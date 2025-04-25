"""
Modelos Pydantic para entrada y salida de la API.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class ClientOut(BaseModel):
    id: int
    name: str
    probability: float
    status: str | None
    age: int
    income: float
    profile: str

    class Config:
        from_attributes = True  # SQLAlchemy ↔︎ Pydantic


class StatusIn(BaseModel):
    new_status: str


class KPISummary(BaseModel):
    clientes_potenciales: int
    conversion_esperada: float


class ProductoBase(BaseModel):
    id: str
    nombre: str
    tipo: str
    descripcion: Optional[str] = None
    
    class Config:
        orm_mode = True


class ClienteProductoBase(BaseModel):
    producto_id: str
    
    class Config:
        orm_mode = True


class ClienteBase(BaseModel):
    id: str
    nombre: str
    probabilidad: float
    estado: str
    edad: int
    ingreso: str
    perfil: str
    prioridad: str
    
    class Config:
        orm_mode = True


class ClienteDetalle(ClienteBase):
    productos: List[ProductoBase] = []
    
    class Config:
        orm_mode = True


class KPIResponse(BaseModel):
    clientes_potenciales: int = Field(..., description="Número de clientes con probabilidad > 0.2389")
    conversion_esperada: float = Field(..., description="Promedio de probabilidades")
    oportunidad_financiera: float = Field(..., description="Total de primas estimadas")
    progreso_contactos: float = Field(..., description="Porcentaje de contactos realizados")