"""
API FastAPI para el dashboard de predicción de seguros
"""
from typing import List
from datetime import datetime
import logging

from fastapi import FastAPI, Depends, HTTPException, Query, Path, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db, Client, Prediction, Contact
from .schemas import ClientOut, StatusIn, KPISummary, ClienteDetalle
from .ml_service import THRESHOLD

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Prometeo API",
    description="API para el dashboard de predicción de seguros",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prometeo-dashboard.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint raíz para mensaje de bienvenida
@app.get("/")
async def root():
    """Endpoint raíz que muestra un mensaje de bienvenida"""
    return {"message": "🚀 API Prometeo funcionando correctamente"}

# Router versionado
api_v1 = APIRouter(prefix="/api/v1")


@api_v1.get("/metrics/summary", response_model=KPISummary)
async def get_metrics_summary(db: AsyncSession = Depends(get_db)):
    """Obtiene un resumen de los indicadores clave de rendimiento"""
    try:
        # Consultar total de clientes
        query = select(func.count()).select_from(Client)
        result = await db.execute(query)
        total_clients = result.scalar() or 0
        
        # Consultar promedio de probabilidad (riesgo de abandono)
        query = select(func.avg(Client.probability)).select_from(Client)
        result = await db.execute(query)
        churn_risk_mean = result.scalar() or 0.0
        
        # Consultar total de contactos
        query = select(func.count(Contact.id)).select_from(Contact)
        result = await db.execute(query)
        contacted = result.scalar() or 0
        
        # Calcular clientes en riesgo (probability >= THRESHOLD)
        query = select(func.count()).select_from(Client).where(Client.probability >= THRESHOLD)
        result = await db.execute(query)
        at_risk_count = result.scalar() or 0
        
        # Calcular tasa de conversión (si se tiene información)
        conversion_rate = 0.0  # Valor por defecto
        
        return KPISummary(
            total_clients=total_clients,
            churn_risk_mean=float(churn_risk_mean),
            contacted=contacted,
            at_risk_count=at_risk_count,
            conversion_rate=conversion_rate
        )
    
    except Exception as e:
        logger.error(f"Error al obtener métricas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la solicitud"
        )


@api_v1.get("/clients/priority-list")
async def get_priority_list(
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene la lista de clientes ordenados por probabilidad de abandono"""
    try:
        # Calcular offset para paginación
        offset = (page - 1) * size
        
        # Consultar clientes ordenados por probabilidad descendente
        query = (
            select(Client)
            .order_by(desc(Client.probability))
            .offset(offset)
        .limit(size)
    )
        
        result = await db.execute(query)
        clients = result.scalars().all()
        
        if not clients:
            return []
        
        # Retornar una lista de diccionarios en lugar de modelos Pydantic
        client_list = []
        for client in clients:
            # Determinar la prioridad basada en la probabilidad
            if client.probability is None:
                priority = "low"
                prob_value = 0.0
            else:
                prob_value = float(client.probability)
                if prob_value > 0.7:
                    priority = "high"
                elif prob_value > 0.4:
                    priority = "medium"
                else:
                    priority = "low"
            
            # Crear un diccionario con los datos del cliente
            client_dict = {
                "id": client.id,
                "user_id": client.user_id,
                "probability": prob_value,
                "status": client.status or "pending",
                "age": client.age,
                "risk_profile": client.risk_profile,
                "income_range": client.income_range,
                "priority": priority
            }
            client_list.append(client_dict)
        
        return client_list
    
    except Exception as e:
        logger.error(f"Error al obtener lista de prioridad: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )


@api_v1.patch("/clients/{client_id}/status")
async def update_client_status(
    status_data: StatusIn,
    client_id: int = Path(..., description="ID del cliente"),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza el estado de un cliente."""
    try:
        # Verificar existencia del cliente
        query = select(Client).where(Client.id == client_id)
        result = await db.execute(query)
        client = result.scalars().first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {client_id} no encontrado"
            )
        # Actualizar estado y fecha
        client.status = status_data.new_status
        client.last_contact_date = datetime.now()
        # Registrar contacto si corresponde
        if status_data.new_status == "contacted":
            contact = Contact(
                client_id=client.id,
                channel="app",
                contacted_at=datetime.now(),
                notes="Actualización de estado vía API"
            )
            db.add(contact)
        # Confirmar cambios en la base de datos
        await db.commit()
        # Retornar respuesta sencilla
        return {
            "id": client.id,
            "user_id": client.user_id,
            "status": client.status,
            "success": True
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al actualizar estado del cliente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la solicitud: {str(e)}"
        )


# Incluir router versionado
app.include_router(api_v1)