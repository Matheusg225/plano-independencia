from __future__ import annotations

import argparse
import re
import sys
import unicodedata
import zipfile
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.models.models import (
    CategoriaItem,
    FormaPagamento,
    ItemCasa,
    ItemFormaPagamento,
    ItemLink,
    PrioridadeItem,
    StatusItem,
    TipoPagamento,
)

STATUS_MAP = {
    "comprar": StatusItem.PENDENTE,
    "pendente": StatusItem.PENDENTE,
    "em execucao": StatusItem.EM_EXECUCAO,
    "feito": StatusItem.COMPRADO,
    "comprado": StatusItem.COMPRADO,
}

PRIORIDADE_MAP = {
    "essencial": PrioridadeItem.ESSENCIAL,
    "alta": PrioridadeItem.ALTA,
    "media": PrioridadeItem.MEDIA,
    "baixa": PrioridadeItem.BAIXA,
}


def norm(value: object) -> str:
    text = "" if value is None else str(value).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).lower()


def parse_money(value: object):
    """Retorna (minimo, estimado, maximo). Faixa vira min/max; valor unico vira estimado."""
    if value is None:
        return None, None, None
    text = str(value).strip()
    if not text or norm(text) in {"r$", "rs"}:
        return None, None, None
    numbers = re.findall(r"\d[\d.]*?(?:,\d{1,2})?(?=\D|$)", text)
    parsed = []
    for raw in numbers:
        cleaned = raw.replace(".", "").replace(",", ".")
        try:
            parsed.append(Decimal(cleaned))
        except Exception:
            pass
    if len(parsed) >= 2:
        lo, hi = min(parsed[0], parsed[1]), max(parsed[0], parsed[1])
        return lo, None, hi
    if len(parsed) == 1:
        return None, parsed[0], None
    return None, None, None


def parse_quantity(value: object):
    text = "" if value is None else str(value).strip()
    match = re.search(r"\d+", text)
    qty = int(match.group()) if match else 1
    unit = "kit" if "kit" in norm(text) else "un."
    return max(qty, 1), unit


def is_url(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    try:
        p = urlparse(text)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def read_xlsx_rows(path: Path, sheet_name: str):
    """Leitor XLSX mínimo usando apenas a biblioteca padrão (sem openpyxl)."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "p": "http://schemas.openxmlformats.org/package/2006/relationships"}
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iterfind(".//m:t", ns)))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        target = None
        for sh in wb.findall("m:sheets/m:sheet", ns):
            if sh.attrib.get("name") == sheet_name:
                target = rel_map[sh.attrib[f"{{{ns['r']}}}id"]]
                break
        if target is None:
            raise ValueError(f"Aba '{sheet_name}' não encontrada")
        sheet_path = "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
        root = ET.fromstring(z.read(sheet_path))

        rows = []
        for row in root.findall(".//m:sheetData/m:row", ns):
            values = {}
            for c in row.findall("m:c", ns):
                ref = c.attrib.get("r", "A1")
                col = re.match(r"[A-Z]+", ref).group()
                typ = c.attrib.get("t")
                v = c.find("m:v", ns)
                inline = c.find("m:is", ns)
                val = None
                if typ == "s" and v is not None:
                    val = shared[int(v.text)]
                elif typ == "inlineStr" and inline is not None:
                    val = "".join(t.text or "" for t in inline.iterfind(".//m:t", ns))
                elif v is not None:
                    val = v.text
                values[col] = val
            rows.append(values)
        return rows


def get_or_create_category(db, name: str):
    obj = db.scalar(select(CategoriaItem).where(CategoriaItem.nome == name))
    if not obj:
        obj = CategoriaItem(nome=name)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_food_benefit(db):
    name = "Alimentação"
    obj = db.scalar(select(FormaPagamento).where(FormaPagamento.nome == name))
    if not obj:
        obj = FormaPagamento(nome=name, tipo=TipoPagamento.BENEFICIO)
        db.add(obj)
        db.flush()
    return obj


def main():
    parser = argparse.ArgumentParser(description="Importa a planilha 'Coisa para comprar.xlsx' para o Plano de Independência.")
    parser.add_argument("xlsx", type=Path, help="Caminho do arquivo .xlsx")
    parser.add_argument("--sheet", default="Folha2", help="Nome da aba (padrão: Folha2)")
    parser.add_argument("--dry-run", action="store_true", help="Valida e mostra o que faria, sem gravar no banco")
    parser.add_argument("--update-only", action="store_true", help="Atualiza somente itens existentes; não cria categorias, itens ou registros para itens ausentes")
    args = parser.parse_args()

    if not args.xlsx.exists():
        print(f"ERRO: arquivo não encontrado: {args.xlsx}", file=sys.stderr)
        return 2

    rows = read_xlsx_rows(args.xlsx, args.sheet)
    if not rows:
        print("ERRO: planilha vazia", file=sys.stderr)
        return 2

    created = updated = skipped = 0
    db = SessionLocal()
    try:
        for n, row in enumerate(rows[1:], start=2):
            categoria = (row.get("A") or "").strip()
            nome = (row.get("B") or "").strip()
            if not categoria or not nome:
                continue

            quantidade, unidade = parse_quantity(row.get("C"))
            prioridade_txt = norm(row.get("D"))
            status_txt = norm(row.get("E"))
            minimo, estimado, maximo = parse_money(row.get("F"))
            link_or_payment = (row.get("G") or "").strip()

            prioridade = PRIORIDADE_MAP.get(prioridade_txt, PrioridadeItem.MEDIA)
            status = STATUS_MAP.get(status_txt)
            if status is None:
                print(f"Linha {n}: status desconhecido '{row.get('E')}', ignorada")
                skipped += 1
                continue

            if args.update_only:
                # Não cria categoria em --update-only. Se categoria ou item não existirem, ignora a linha.
                cat = db.scalar(select(CategoriaItem).where(CategoriaItem.nome == categoria))
                if cat is None:
                    print(f"IGNORAR: {categoria} / {nome} | categoria inexistente (--update-only)")
                    skipped += 1
                    continue
            else:
                cat = get_or_create_category(db, categoria)

            item = db.scalar(
                select(ItemCasa)
                .options(selectinload(ItemCasa.links), selectinload(ItemCasa.formas_pagamento))
                .where(ItemCasa.categoria_id == cat.id, ItemCasa.nome == nome)
            )
            if item is None:
                if args.update_only:
                    print(f"IGNORAR: {categoria} / {nome} | item inexistente (--update-only)")
                    skipped += 1
                    continue
                item = ItemCasa(categoria_id=cat.id, nome=nome)
                db.add(item)
                db.flush()
                created += 1
                action = "CRIAR"
            else:
                updated += 1
                action = "ATUALIZAR"

            item.quantidade = quantidade
            item.unidade = unidade
            item.prioridade = prioridade
            item.status = status
            item.valor_minimo = minimo
            item.valor_estimado = estimado
            item.valor_maximo = maximo

            # A coluna G mistura URL de produto e a indicação "Alimentação".
            if is_url(link_or_payment):
                existing = {x.url for x in item.links}
                if link_or_payment not in existing:
                    db.add(ItemLink(item_id=item.id, titulo="Produto", url=link_or_payment))
            elif norm(link_or_payment) == "alimentacao":
                fp = get_or_create_food_benefit(db)
                if not any(x.forma_pagamento_id == fp.id for x in item.formas_pagamento):
                    db.add(ItemFormaPagamento(item_id=item.id, forma_pagamento_id=fp.id, preferencial=True))

            print(f"{action}: {categoria} / {nome} | {status.value} | min={minimo} est={estimado} max={maximo}")

        if args.dry_run:
            db.rollback()
            print(f"\nDRY-RUN: {created} criariam, {updated} atualizariam, {skipped} ignorados. Nada gravado.")
        else:
            db.commit()
            print(f"\nOK: {created} criados, {updated} atualizados, {skipped} ignorados.")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
