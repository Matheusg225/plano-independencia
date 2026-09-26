from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, HttpUrl
from app.models.models import PrioridadeItem, StatusItem
class LinkIn(BaseModel):
    titulo:str="Produto"; url:HttpUrl; preco:Decimal|None=None
class ItemIn(BaseModel):
    nome:str; categoria:str; quantidade:int=1; unidade:str="un."; prioridade:PrioridadeItem=PrioridadeItem.MEDIA; status:StatusItem=StatusItem.PENDENTE
    valor_minimo:Decimal|None=None; valor_estimado:Decimal|None=None; valor_maximo:Decimal|None=None; valor_pago:Decimal|None=None
    observacao:str|None=None; data_compra:date|None=None; links:list[LinkIn]=[]; forma_pagamento:str|None=None
class ItemUpdate(BaseModel):
    nome:str|None=None; categoria:str|None=None; quantidade:int|None=None; unidade:str|None=None; prioridade:PrioridadeItem|None=None; status:StatusItem|None=None
    valor_minimo:Decimal|None=None; valor_estimado:Decimal|None=None; valor_maximo:Decimal|None=None; valor_pago:Decimal|None=None
    observacao:str|None=None; data_compra:date|None=None; links:list[LinkIn]|None=None; forma_pagamento:str|None=None

class ItemOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; nome:str; categoria:str; quantidade:int; unidade:str; prioridade:str; status:str
    valor_minimo:Decimal|None; valor_estimado:Decimal|None; valor_maximo:Decimal|None; valor_pago:Decimal|None; observacao:str|None
    links:list[dict]; forma_pagamento:str|None=None
