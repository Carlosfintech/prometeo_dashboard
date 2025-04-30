"""
Aplicación principal FastAPI
"""
import logging
import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .database import get_db
from .api import app as api_app, api_v1
from .startup import run_startup_checks

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Prometeo API",
    description="API para el dashboard de predicción de seguros",
    version="1.0.0"
)

# Configurar CORS
app_environment = os.environ.get("APP_ENVIRONMENT", "development")
logger.info(f"Aplicación iniciada en entorno: {app_environment}")

# Configurar orígenes permitidos según el entorno
if app_environment == "production":
    # En producción, permitir solo dominios específicos
    allowed_origins = [
        "https://prometeo-dashboard.vercel.app",
        "https://prometeo-dashboard-mdqdqqc4y-carlosfintechs-projects.vercel.app",
        "https://*.vercel.app",  # Permitir cualquier subdominio de vercel.app
    ]
    logger.info(f"CORS configurado para dominios de producción: {allowed_origins}")
else:
    # En desarrollo, permitir cualquier origen (más flexible)
    allowed_origins = ["*"]
    logger.info("CORS configurado para permitir cualquier origen (entorno de desarrollo)")

# Añadir middleware CORS
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

# Middleware para manejar excepciones globales
@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Error no manejado: {str(e)}")
        
        # Preparar respuesta de error
        return JSONResponse(
            status_code=500,
            content={"message": "Error interno del servidor", "detail": str(e)}
        )

# Montar la aplicación de API
app.mount("/api/v1", api_v1)

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz para verificar que la API está funcionando"""
    return {"message": "🚀 API Prometeo funcionando correctamente", "version": "1.0.0"}

# Endpoint de salud para verificar estado del sistema
@app.get("/health")
async def health():
    """Endpoint de verificación de salud del sistema"""
    try:
        # Realizar verificaciones básicas
        # 1. Verificar que la aplicación esté respondiendo
        # 2. Verificar que se pueda obtener la sesión de base de datos
        db_generator = get_db()
        db = await anext(db_generator)
        await db.execute("SELECT 1")
        await db.close()
        
        return {
            "status": "healthy",
            "environment": app_environment,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Error en verificación de salud: {str(e)}")
        return JSONResponse(
            status_code=503,  # Service Unavailable
            content={
                "status": "unhealthy",
                "environment": app_environment,
                "database": "disconnected",
                "error": str(e)
            }
        )

# Función para ejecutar verificaciones al inicio
@app.on_event("startup")
async def startup_event():
    """Ejecutar verificaciones al inicio de la aplicación"""
    logger.info("Iniciando aplicación...")
    
    # Ejecutar verificaciones de inicio
    await run_startup_checks()
    
    logger.info("Aplicación iniciada y lista para recibir peticiones")

# Función para limpiar recursos al cerrar
@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar la aplicación"""
    logger.info("Cerrando aplicación...")
    
    # Cerrar conexiones y liberar recursos
    # Aquí podrían ir limpiezas adicionales
    
    logger.info("Aplicación cerrada correctamente")

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    # Configuración del servidor Uvicorn
    port = int(os.environ.get("PORT", 8000))
    
    # Iniciar servidor
    logger.info(f"Iniciando servidor en puerto {port}...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=app_environment == "development"
    ) 