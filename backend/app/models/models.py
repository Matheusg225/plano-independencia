import enum, uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
class PrioridadeItem(str,enum.Enum): ESSENCIAL="ESSENCIAL"; ALTA="ALTA"; MEDIA="MEDIA"; BAIXA="BAIXA"
class StatusItem(str,enum.Enum): PENDENTE="PENDENTE"; EM_EXECUCAO="EM_EXECUCAO"; COMPRADO="COMPRADO"
class TipoPagamento(str,enum.Enum): DINHEIRO="DINHEIRO"; PIX="PIX"; DEBITO="DEBITO"; CREDITO="CREDITO"; BENEFICIO="BENEFICIO"; OUTRO="OUTRO"
class CategoriaItem(Base):
    __tablename__="categorias_itens"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    nome:Mapped[str]=mapped_column(String(80),unique=True,nullable=False)
    ordem:Mapped[int]=mapped_column(Integer,default=0,server_default="0")
    ativo:Mapped[bool]=mapped_column(Boolean,default=True,server_default="true")
    itens:Mapped[list["ItemCasa"]]=relationship(back_populates="categoria")
class FormaPagamento(Base):
    __tablename__="formas_pagamento"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    nome:Mapped[str]=mapped_column(String(80),unique=True,nullable=False)
    tipo:Mapped[TipoPagamento]=mapped_column(Enum(TipoPagamento,name="tipo_pagamento_enum"),nullable=False)
    ativo:Mapped[bool]=mapped_column(Boolean,default=True,server_default="true")
    itens_associados:Mapped[list["ItemFormaPagamento"]]=relationship(back_populates="forma_pagamento",cascade="all, delete-orphan")
class ItemCasa(Base):
    __tablename__="itens_casa"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    categoria_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("categorias_itens.id",ondelete="RESTRICT"),nullable=False,index=True)
    nome:Mapped[str]=mapped_column(String(150),nullable=False)
    quantidade:Mapped[int]=mapped_column(Integer,default=1,server_default="1")
    unidade:Mapped[str]=mapped_column(String(30),default="un.",server_default="un.")
    prioridade:Mapped[PrioridadeItem]=mapped_column(Enum(PrioridadeItem,name="prioridade_item_enum"),default=PrioridadeItem.MEDIA,nullable=False,index=True)
    status:Mapped[StatusItem]=mapped_column(Enum(StatusItem,name="status_item_enum"),default=StatusItem.PENDENTE,nullable=False,index=True)
    valor_minimo:Mapped[Decimal|None]=mapped_column(Numeric(12,2))
    valor_estimado:Mapped[Decimal|None]=mapped_column(Numeric(12,2))
    valor_maximo:Mapped[Decimal|None]=mapped_column(Numeric(12,2))
    valor_pago:Mapped[Decimal|None]=mapped_column(Numeric(12,2))
    observacao:Mapped[str|None]=mapped_column(Text)
    data_compra:Mapped[date|None]=mapped_column(Date)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    categoria:Mapped[CategoriaItem]=relationship(back_populates="itens")
    formas_pagamento:Mapped[list["ItemFormaPagamento"]]=relationship(back_populates="item",cascade="all, delete-orphan")
    links:Mapped[list["ItemLink"]]=relationship(back_populates="item",cascade="all, delete-orphan")
    __table_args__=(CheckConstraint("quantidade > 0",name="ck_item_quantidade"),CheckConstraint("valor_pago IS NULL OR valor_pago >= 0",name="ck_item_pago"),UniqueConstraint("categoria_id","nome",name="uq_item_categoria_nome"),Index("ix_item_status_prioridade","status","prioridade"))
class ItemFormaPagamento(Base):
    __tablename__="item_formas_pagamento"
    item_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("itens_casa.id",ondelete="CASCADE"),primary_key=True)
    forma_pagamento_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("formas_pagamento.id",ondelete="CASCADE"),primary_key=True)
    preferencial:Mapped[bool]=mapped_column(Boolean,default=False,server_default="false")
    item:Mapped[ItemCasa]=relationship(back_populates="formas_pagamento")
    forma_pagamento:Mapped[FormaPagamento]=relationship(back_populates="itens_associados")
class ItemLink(Base):
    __tablename__="item_links"
    id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    item_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("itens_casa.id",ondelete="CASCADE"),nullable=False,index=True)
    titulo:Mapped[str]=mapped_column(String(100),default="Produto")
    url:Mapped[str]=mapped_column(Text,nullable=False)
    preco:Mapped[Decimal|None]=mapped_column(Numeric(12,2))
    item:Mapped[ItemCasa]=relationship(back_populates="links")
