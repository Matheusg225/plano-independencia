from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db
from app.models.models import CategoriaItem, FormaPagamento, ItemCasa, ItemFormaPagamento, ItemLink, TipoPagamento
from app.schemas.items import ItemIn, ItemUpdate
router=APIRouter(prefix="/items",tags=["items"])
def serialize(i):
    return {"id":str(i.id),"nome":i.nome,"categoria":i.categoria.nome,"quantidade":i.quantidade,"unidade":i.unidade,"prioridade":i.prioridade.value,"status":i.status.value,"valor_minimo":i.valor_minimo,"valor_estimado":i.valor_estimado,"valor_maximo":i.valor_maximo,"valor_pago":i.valor_pago,"observacao":i.observacao,"links":[{"id":str(x.id),"titulo":x.titulo,"url":x.url,"preco":x.preco} for x in i.links],"forma_pagamento":next((x.forma_pagamento.nome for x in i.formas_pagamento if x.preferencial),None)}
def query(): return select(ItemCasa).options(selectinload(ItemCasa.categoria),selectinload(ItemCasa.links),selectinload(ItemCasa.formas_pagamento).selectinload(ItemFormaPagamento.forma_pagamento)).order_by(ItemCasa.created_at.desc())
@router.get("")
def list_items(db:Session=Depends(get_db)): return [serialize(i) for i in db.scalars(query()).unique().all()]
@router.post("",status_code=201)
def create_item(data:ItemIn,db:Session=Depends(get_db)):
    cat=db.scalar(select(CategoriaItem).where(CategoriaItem.nome==data.categoria))
    if not cat: cat=CategoriaItem(nome=data.categoria); db.add(cat); db.flush()
    item=ItemCasa(categoria_id=cat.id,nome=data.nome,quantidade=data.quantidade,unidade=data.unidade,prioridade=data.prioridade,status=data.status,valor_minimo=data.valor_minimo,valor_estimado=data.valor_estimado,valor_maximo=data.valor_maximo,valor_pago=data.valor_pago,observacao=data.observacao,data_compra=data.data_compra)
    db.add(item); db.flush()
    for l in data.links: db.add(ItemLink(item_id=item.id,titulo=l.titulo,url=str(l.url),preco=l.preco))
    if data.forma_pagamento:
        fp=db.scalar(select(FormaPagamento).where(FormaPagamento.nome==data.forma_pagamento))
        if not fp: fp=FormaPagamento(nome=data.forma_pagamento,tipo=TipoPagamento.BENEFICIO if "aliment" in data.forma_pagamento.lower() else TipoPagamento.OUTRO); db.add(fp); db.flush()
        db.add(ItemFormaPagamento(item_id=item.id,forma_pagamento_id=fp.id,preferencial=True))
    db.commit(); return serialize(db.scalar(query().where(ItemCasa.id==item.id)))
@router.patch("/{item_id}")
def update_item(item_id:str,data:ItemUpdate,db:Session=Depends(get_db)):
    item=db.get(ItemCasa,item_id)
    if not item: raise HTTPException(404,"Item não encontrado")
    changes=data.model_dump(exclude_unset=True)
    if "categoria" in changes:
        categoria_nome=changes.pop("categoria")
        if categoria_nome:
            cat=db.scalar(select(CategoriaItem).where(CategoriaItem.nome==categoria_nome))
            if not cat:
                cat=CategoriaItem(nome=categoria_nome); db.add(cat); db.flush()
            item.categoria_id=cat.id
    if "links" in changes:
        links=changes.pop("links") or []
        item.links.clear(); db.flush()
        for link in links:
            db.add(ItemLink(item_id=item.id,titulo=link.titulo,url=str(link.url),preco=link.preco))
    if "forma_pagamento" in changes:
        forma_nome=changes.pop("forma_pagamento")
        item.formas_pagamento.clear(); db.flush()
        if forma_nome:
            fp=db.scalar(select(FormaPagamento).where(FormaPagamento.nome==forma_nome))
            if not fp:
                fp=FormaPagamento(nome=forma_nome,tipo=TipoPagamento.BENEFICIO if "aliment" in forma_nome.lower() else TipoPagamento.OUTRO)
                db.add(fp); db.flush()
            db.add(ItemFormaPagamento(item_id=item.id,forma_pagamento_id=fp.id,preferencial=True))
    for key,value in changes.items(): setattr(item,key,value)
    db.commit()
    return serialize(db.scalar(query().where(ItemCasa.id==item.id)))
@router.delete("/{item_id}",status_code=204)
def delete_item(item_id:str,db:Session=Depends(get_db)):
    item=db.get(ItemCasa,item_id)
    if not item: raise HTTPException(404,"Item não encontrado")
    db.delete(item); db.commit()
