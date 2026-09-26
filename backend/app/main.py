from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import CategoriaItem, FormaPagamento, TipoPagamento
from app.api.items import router as items_router
app=FastAPI(title=settings.APP_NAME)
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(items_router,prefix="/api")
@app.on_event("startup")
def seed():
    with SessionLocal() as db:
        if not db.scalar(select(CategoriaItem.id).limit(1)):
            db.add_all([CategoriaItem(nome=n,ordem=i) for i,n in enumerate(["Cozinha","Sala","Quarto","Banheiro","Lavanderia","Geral"])])
            db.add_all([FormaPagamento(nome="Dinheiro / PIX",tipo=TipoPagamento.DINHEIRO),FormaPagamento(nome="Cartão alimentação",tipo=TipoPagamento.BENEFICIO),FormaPagamento(nome="Cartão de crédito",tipo=TipoPagamento.CREDITO)])
            db.commit()
@app.get("/health")
def health(): return {"status":"ok"}
