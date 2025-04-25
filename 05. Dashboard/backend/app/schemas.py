"""
Esquemas Pydantic para entrada/salida de la API
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, validator


class ClientBase(BaseModel):
    """Esquema base para clientes"""
    user_id: str
    age: int
    risk_profile: str
    probability: float


class ClientOut(BaseModel):
    """Esquema de salida para clientes"""
    id: int
    user_id: str
    probability: Optional[float] = 0.0
    status: Optional[str] = "pending"
    
    class Config:
        orm_mode = True
        from_attributes = True


class ClienteDetalle(ClientOut):
    """Esquema detallado de cliente para endpoint priority-list"""
    age: Optional[int] = None
    risk_profile: Optional[str] = None
    income_range: Optional[str] = None
    occupation: Optional[str] = None
    segment: Optional[str] = None
    acquisition_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    
    class Config:
        orm_mode = True
        from_attributes = True


class StatusIn(BaseModel):
    """Esquema para actualizar el estado de un cliente"""
    new_status: str
    
    @validator('new_status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'contacted', 'interested', 'not_interested', 'converted', 'lost']
        if v not in valid_statuses:
            raise ValueError(f'status must be one of {valid_statuses}')
        return v


class KPISummary(BaseModel):
    """Esquema para el resumen de KPIs"""
    total_clients: int
    churn_risk_mean: float
    contacted: int
    conversion_rate: Optional[float] = 0.0
    at_risk_count: Optional[int] = 0


class PredictionCreate(BaseModel):
    """Esquema para crear una predicción"""
    user_id: str
    probability: float
    is_target: bool
    
    class Config:
        orm_mode = True
        from_attributes = True


class PredictionOut(PredictionCreate):
    """Esquema de salida para predicciones"""
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


class ContactCreate(BaseModel):
    """Esquema para crear un contacto"""
    client_id: int
    channel: str
    notes: Optional[str] = None
    outcome: Optional[str] = None
    
    class Config:
        orm_mode = True
        from_attributes = True


class ContactOut(ContactCreate):
    """Esquema de salida para contactos"""
    id: int
    contacted_at: datetime
    created_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True