"""
Script de inicio para ejecutar verificaciones del sistema al arrancar la aplicación

Este script realiza varias comprobaciones al inicio de la aplicación:
1. Verifica la conexión a la base de datos
2. Verifica que el modelo de ML esté accesible
3. Registra información del entorno
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def check_database(database_url):
    """
    Verificar conectividad y tablas en la base de datos
    
    Args:
        database_url: URL de conexión a la base de datos
        
    Returns:
        bool: True si la comprobación es exitosa, False en caso contrario
    """
    try:
        logger.info("Verificando conexión a la base de datos...")
        
        # Si la URL comienza con postgres://, convertirla a postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        # Asegurarse de que tenga el driver asyncpg
        if "postgresql://" in database_url and "+asyncpg" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Crear engine para conexión
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"timeout": 5}
        )
        
        # Conectar y ejecutar query simple
        async with engine.connect() as conn:
            # Verificar conectividad
            result = await conn.execute(text("SELECT 1"))
            await result.fetchone()
            logger.info("✅ Conexión a la base de datos establecida correctamente")
            
            # Verificar tablas
            result = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
            )
            tables = [row[0] for row in await result.fetchall()]
            logger.info(f"✅ Tablas encontradas: {', '.join(tables)}")
            
            # Verificar tabla demographics
            if "demographics" in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM demographics"))
                count = (await result.fetchone())[0]
                logger.info(f"✅ Tabla demographics contiene {count} registros")
            else:
                logger.warning("⚠️ Tabla demographics no encontrada")
                
            # Verificar tabla de predicciones
            if "prediction_results" in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM prediction_results"))
                count = (await result.fetchone())[0]
                logger.info(f"✅ Tabla prediction_results contiene {count} registros")
            else:
                logger.warning("⚠️ Tabla prediction_results no encontrada")
                
        return True
    except Exception as e:
        logger.error(f"❌ Error al verificar base de datos: {str(e)}")
        return False

def check_ml_model():
    """
    Verificar que el modelo de ML esté accesible
    
    Returns:
        bool: True si el modelo existe, False en caso contrario
    """
    try:
        logger.info("Verificando acceso al modelo de ML...")
        
        # Ubicaciones posibles del modelo
        model_paths = [
            Path("xgb_model.pkl"),
            Path("./xgb_model.pkl"),
            Path("../xgb_model.pkl"),
            Path("/app/xgb_model.pkl")
        ]
        
        # Variable de entorno con ubicación del modelo
        env_model_path = os.environ.get("MODEL_PATH")
        if env_model_path:
            model_paths.append(Path(env_model_path))
        
        # Verificar si existe en alguna ubicación
        for path in model_paths:
            if path.exists() and path.is_file():
                logger.info(f"✅ Modelo encontrado en: {path}")
                return True
        
        logger.warning("⚠️ No se encontró el modelo de ML en ninguna ubicación")
        logger.warning("⚠️ Se usará un modelo dummy para desarrollo")
        return False
    except Exception as e:
        logger.error(f"❌ Error al verificar modelo ML: {str(e)}")
        return False

def log_environment_info():
    """Registrar información del entorno de ejecución"""
    try:
        logger.info("=== INFORMACIÓN DEL ENTORNO ===")
        logger.info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Entorno: {os.environ.get('APP_ENVIRONMENT', 'development')}")
        logger.info(f"Python versión: {sys.version}")
        logger.info(f"Sistema operativo: {sys.platform}")
        logger.info(f"Directorio de trabajo: {os.getcwd()}")
        logger.info("=" * 30)
    except Exception as e:
        logger.error(f"Error al registrar información del entorno: {str(e)}")

async def run_startup_checks():
    """Ejecutar todas las verificaciones de inicio"""
    try:
        logger.info("Iniciando verificaciones del sistema...")
        
        # Registrar información del entorno
        log_environment_info()
        
        # Verificar base de datos
        database_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:1111@localhost:5432/prometeo_db")
        db_ok = await check_database(database_url)
        
        # Verificar modelo ML
        ml_ok = check_ml_model()
        
        # Resumir estado
        if db_ok and ml_ok:
            logger.info("🚀 Sistema listo para su uso")
        else:
            logger.warning("⚠️ Sistema iniciado con advertencias")
            
        return db_ok and ml_ok
    except Exception as e:
        logger.error(f"❌ Error en verificaciones de inicio: {str(e)}")
        return False 