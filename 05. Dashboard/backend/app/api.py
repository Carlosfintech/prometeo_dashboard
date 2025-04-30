"""
API FastAPI para el dashboard de predicción de seguros
"""
from typing import List
from datetime import datetime
import logging
import os
import numpy as np
from sqlalchemy import select, update, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import FastAPI, Depends, HTTPException, Query, Path, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# Obtener el entorno de la aplicación
app_environment = os.environ.get("APP_ENVIRONMENT", "development")
logger.info(f"Aplicación iniciada en entorno: {app_environment}")

# Configurar CORS con los dominios permitidos
if app_environment == "production":
    # En producción, permitir solo dominios específicos
    allowed_origins = [
        "https://prometeo-dashboard.vercel.app",
        "https://prometeo-dashboard-mdqdqqc4y-carlosfintechs-projects.vercel.app",
        # Añadir cualquier dominio de Vercel donde se despliegue el frontend
        "https://*.vercel.app",  # Permitir cualquier subdominio de vercel.app
    ]
    logger.info(f"CORS configurado para dominios de producción: {allowed_origins}")
else:
    # En desarrollo, permitir cualquier origen (más flexible)
    allowed_origins = ["*"]
    logger.info("CORS configurado para permitir cualquier origen (entorno de desarrollo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Mantener en False para evitar problemas con '*' y credentials
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware adicional para asegurar que se envíen los encabezados CORS
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    # Si estamos en desarrollo o la solicitud es de un origen permitido,
    # añadir encabezados CORS explícitamente
    if app_environment == "development" or any(origin in request.headers.get("origin", "") for origin in allowed_origins if "*" not in origin):
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    else:
        # En otros casos, usar el comodín
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

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


@api_v1.get("/metrics/probability-distribution", response_model=List[dict])
async def get_probability_distribution(db: AsyncSession = Depends(get_db)):
    """
    Obtener la distribución de probabilidades de clientes
    
    Returns:
        List[dict]: Lista con la distribución de probabilidades
    """
    try:
        # Definir los rangos para la distribución
        ranges = [
            {"min": 0.0, "max": 0.2, "label": "0-20%"},
            {"min": 0.2, "max": 0.4, "label": "20-40%"},
            {"min": 0.4, "max": 0.6, "label": "40-60%"},
            {"min": 0.6, "max": 0.8, "label": "60-80%"},
            {"min": 0.8, "max": 1.0, "label": "80-100%"}
        ]
        
        # Consulta para obtener todas las probabilidades
        query = select(Client.probability)
        result = await db.execute(query)
        probabilities = [float(row[0]) for row in result.fetchall()]
        
        # Calcular la distribución
        distribution = []
        for r in ranges:
            count = len([p for p in probabilities if r["min"] <= p < r["max"]])
            distribution.append({
                "range": r["label"],
                "count": count,
                "percentage": round(count / len(probabilities) * 100, 2) if probabilities else 0
            })
            
        return distribution
    except Exception as e:
        logger.error(f"Error al obtener distribución de probabilidades: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar la distribución de probabilidades: {str(e)}"
        )


@api_v1.get("/metrics/heatmap/variables")
async def get_heatmap_variables():
    """
    Obtener las variables disponibles para el mapa de calor
    
    Returns:
        List[dict]: Lista de variables disponibles
    """
    # Definir variables disponibles para el mapa de calor
    variables = [
        {"id": "age", "name": "Edad", "type": "numeric"},
        {"id": "income_range", "name": "Rango de Ingresos", "type": "categorical"},
        {"id": "risk_profile", "name": "Perfil de Riesgo", "type": "categorical"},
        {"id": "occupation", "name": "Ocupación", "type": "categorical"},
        {"id": "segment", "name": "Segmento", "type": "categorical"},
        {"id": "probability", "name": "Probabilidad", "type": "numeric"}
    ]
    
    return variables


@api_v1.get("/metrics/heatmap")
async def get_heatmap_data(
    x_var: str = Query(..., description="Variable para el eje X"),
    y_var: str = Query(..., description="Variable para el eje Y"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener datos para el mapa de calor según variables seleccionadas
    
    Args:
        x_var: Variable para el eje X
        y_var: Variable para el eje Y
        
    Returns:
        dict: Datos para el mapa de calor
    """
    try:
        # Validar variables
        valid_vars = ["age", "income_range", "risk_profile", "occupation", "segment", "probability"]
        if x_var not in valid_vars or y_var not in valid_vars:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Variables no válidas. Debe ser una de: {', '.join(valid_vars)}"
            )
        
        # Consulta para obtener datos según las variables seleccionadas
        query = select(getattr(Client, x_var), getattr(Client, y_var), func.count(Client.id))
        query = query.group_by(getattr(Client, x_var), getattr(Client, y_var))
        result = await db.execute(query)
        
        # Procesar resultados
        heatmap_data = []
        for row in result.fetchall():
            x_value = str(row[0]) if row[0] is not None else "N/A"
            y_value = str(row[1]) if row[1] is not None else "N/A"
            count = row[2]
            
            heatmap_data.append({
                "x": x_value,
                "y": y_value,
                "value": count
            })
        
        # Obtener valores únicos para ejes X e Y
        x_values = sorted(list(set(d["x"] for d in heatmap_data)))
        y_values = sorted(list(set(d["y"] for d in heatmap_data)))
        
        return {
            "data": heatmap_data,
            "xAxis": x_values,
            "yAxis": y_values
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar datos de mapa de calor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar datos del mapa de calor: {str(e)}"
        )


@api_v1.get("/contacts/progress")
async def get_contacts_progress(
    start_date: str = Query(None, description="Fecha de inicio (YYYY-MM-DD)"),
    end_date: str = Query(None, description="Fecha de fin (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener el progreso de contactos a lo largo del tiempo
    
    Args:
        start_date: Fecha de inicio para filtrar
        end_date: Fecha de fin para filtrar
        
    Returns:
        dict: Datos de progreso de contactos
    """
    try:
        # Construir query base
        query = select(
            func.date_trunc('day', Contact.contacted_at).label('date'),
            Contact.outcome,
            func.count().label('count')
        )
        
        # Aplicar filtros de fecha si están presentes
        if start_date:
            query = query.where(Contact.contacted_at >= start_date)
        if end_date:
            query = query.where(Contact.contacted_at <= end_date)
            
        # Agrupar por fecha y resultado
        query = query.group_by(
            text('date'),
            Contact.outcome
        ).order_by(text('date'))
        
        # Ejecutar consulta
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Preparar datos de series temporales
        dates = sorted(list(set(str(row.date.date()) for row in rows if row.date)))
        
        # Categorías de resultados
        outcomes = ["success", "pending", "not_interested", "unreachable", "other"]
        
        # Preparar estructura de datos
        series_data = {outcome: [0] * len(dates) for outcome in outcomes}
        
        # Llenar datos
        for row in rows:
            if row.date:
                date_str = str(row.date.date())
                date_idx = dates.index(date_str)
                outcome = row.outcome if row.outcome in outcomes else "other"
                series_data[outcome][date_idx] = row.count
        
        # Formatear para la respuesta
        series = [
            {
                "name": outcome.replace("_", " ").title(),
                "data": series_data[outcome]
            }
            for outcome in outcomes
        ]
        
        return {
            "categories": dates,
            "series": series
        }
    except Exception as e:
        logger.error(f"Error al obtener progreso de contactos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar datos de progreso de contactos: {str(e)}"
        )

# Incluir router versionado
app.include_router(api_v1)