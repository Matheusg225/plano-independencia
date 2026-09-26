"""initial tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    prioridade=sa.Enum("ESSENCIAL","ALTA","MEDIA","BAIXA",name="prioridade_item_enum")
    status=sa.Enum("PENDENTE","EM_EXECUCAO","COMPRADO",name="status_item_enum")
    tipo=sa.Enum("DINHEIRO","PIX","DEBITO","CREDITO","BENEFICIO","OUTRO",name="tipo_pagamento_enum")
    op.create_table("categorias_itens",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("nome",sa.String(80),nullable=False,unique=True),sa.Column("ordem",sa.Integer(),server_default="0",nullable=False),sa.Column("ativo",sa.Boolean(),server_default="true",nullable=False))
    op.create_table("formas_pagamento",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("nome",sa.String(80),nullable=False,unique=True),sa.Column("tipo",tipo,nullable=False),sa.Column("ativo",sa.Boolean(),server_default="true",nullable=False))
    op.create_table("itens_casa",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("categoria_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("categorias_itens.id",ondelete="RESTRICT"),nullable=False),sa.Column("nome",sa.String(150),nullable=False),sa.Column("quantidade",sa.Integer(),server_default="1",nullable=False),sa.Column("unidade",sa.String(30),server_default="un.",nullable=False),sa.Column("prioridade",prioridade,nullable=False),sa.Column("status",status,nullable=False),sa.Column("valor_minimo",sa.Numeric(12,2)),sa.Column("valor_estimado",sa.Numeric(12,2)),sa.Column("valor_maximo",sa.Numeric(12,2)),sa.Column("valor_pago",sa.Numeric(12,2)),sa.Column("observacao",sa.Text()),sa.Column("data_compra",sa.Date()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now()),sa.CheckConstraint("quantidade > 0",name="ck_item_quantidade"),sa.CheckConstraint("valor_pago IS NULL OR valor_pago >= 0",name="ck_item_pago"),sa.UniqueConstraint("categoria_id","nome",name="uq_item_categoria_nome"))
    op.create_index("ix_itens_casa_categoria_id","itens_casa",["categoria_id"]); op.create_index("ix_itens_casa_prioridade","itens_casa",["prioridade"]); op.create_index("ix_itens_casa_status","itens_casa",["status"]); op.create_index("ix_item_status_prioridade","itens_casa",["status","prioridade"])
    op.create_table("item_formas_pagamento",sa.Column("item_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("itens_casa.id",ondelete="CASCADE"),primary_key=True),sa.Column("forma_pagamento_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("formas_pagamento.id",ondelete="CASCADE"),primary_key=True),sa.Column("preferencial",sa.Boolean(),server_default="false",nullable=False))
    op.create_table("item_links",sa.Column("id",postgresql.UUID(as_uuid=True),primary_key=True),sa.Column("item_id",postgresql.UUID(as_uuid=True),sa.ForeignKey("itens_casa.id",ondelete="CASCADE"),nullable=False),sa.Column("titulo",sa.String(100),nullable=False),sa.Column("url",sa.Text(),nullable=False),sa.Column("preco",sa.Numeric(12,2)))
    op.create_index("ix_item_links_item_id","item_links",["item_id"])
def downgrade():
    op.drop_table("item_links"); op.drop_table("item_formas_pagamento"); op.drop_table("itens_casa"); op.drop_table("formas_pagamento"); op.drop_table("categorias_itens")
    sa.Enum(name="tipo_pagamento_enum").drop(op.get_bind()); sa.Enum(name="status_item_enum").drop(op.get_bind()); sa.Enum(name="prioridade_item_enum").drop(op.get_bind())
