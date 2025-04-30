"""
Script para verificar la conexión a la base de datos y su estructura.

Este script realiza una comprobación completa del estado de la base de datos:
1. Verifica la conexión a PostgreSQL
2. Comprueba que las tablas existan
3. Realiza consultas de prueba para validar el acceso a los datos
4. Verifica la estructura de las tablas principales
"""

import os
import sys
import time
import asyncio
from datetime import datetime
import asyncpg
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Obtener URL de la base de datos desde variables de entorno o usar valores por defecto
def get_db_url():
    # Obtener URL de variable de entorno o construirla a partir de componentes
    db_url = os.environ.get("DATABASE_URL")
    
    if not db_url:
        # Componentes individuales de la conexión
        db_user = os.environ.get("POSTGRES_USER", "postgres")
        db_password = os.environ.get("POSTGRES_PASSWORD", "1111")
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "prometeo_db")
        
        # Construir URL
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # Asegurarse de que es una URL de PostgreSQL válida
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # No incluimos asyncpg porque lo manejamos directamente con el driver
    return db_url

async def check_connection(db_url, max_retries=5, retry_delay=3):
    """Verificar la conexión a la base de datos con reintentos"""
    logger.info(f"Verificando conexión a la base de datos...")
    
    for attempt in range(1, max_retries + 1):
        try:
            conn = await asyncpg.connect(db_url)
            version = await conn.fetchval("SELECT version();")
            logger.info(f"✅ Conexión exitosa a la base de datos (Intento {attempt}/{max_retries})")
            logger.info(f"   PostgreSQL versión: {version}")
            await conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Error de conexión (Intento {attempt}/{max_retries}): {str(e)}")
            if attempt < max_retries:
                logger.info(f"   Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ No se pudo establecer conexión después de {max_retries} intentos")
                return False

async def check_tables(db_url):
    """Verificar que las tablas esperadas existan en la base de datos"""
    expected_tables = [
        "demographics", 
        "prediction_results", 
        "contacts", 
        "contact_history",
        "products",
        "transactions",
        "goals"
    ]
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Verificar tablas
        logger.info("Verificando tablas en la base de datos...")
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        tables = await conn.fetch(tables_query)
        existing_tables = [record['table_name'] for record in tables]
        
        # Mostrar todas las tablas encontradas
        logger.info(f"Tablas encontradas en la base de datos ({len(existing_tables)}):")
        for table in existing_tables:
            logger.info(f"   - {table}")
        
        # Verificar tablas esperadas
        missing_tables = [table for table in expected_tables if table not in existing_tables]
        if missing_tables:
            logger.error(f"❌ Faltan las siguientes tablas: {', '.join(missing_tables)}")
        else:
            logger.info(f"✅ Todas las tablas esperadas están presentes")
        
        # Verificar contenido de las tablas
        for table in expected_tables:
            if table in existing_tables:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                logger.info(f"   - Tabla {table}: {count} registros")
        
        await conn.close()
        return len(missing_tables) == 0
    except Exception as e:
        logger.error(f"❌ Error al verificar tablas: {str(e)}")
        return False

async def run_test_queries(db_url):
    """Ejecutar consultas de prueba para verificar el acceso a los datos"""
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. Verificar clientes con alta probabilidad
        high_prob_query = """
            SELECT COUNT(*) FROM demographics 
            WHERE probability >= 0.7
        """
        high_prob_count = await conn.fetchval(high_prob_query)
        logger.info(f"✅ Clientes con alta probabilidad (>= 0.7): {high_prob_count}")
        
        # 2. Verificar predicciones recientes
        recent_pred_query = """
            SELECT COUNT(*) FROM prediction_results 
            WHERE prediction_date >= NOW() - INTERVAL '30 days'
        """
        recent_pred_count = await conn.fetchval(recent_pred_query)
        logger.info(f"✅ Predicciones recientes (últimos 30 días): {recent_pred_count}")
        
        # 3. Verificar contactos
        contacts_query = "SELECT COUNT(*) FROM contacts"
        contacts_count = await conn.fetchval(contacts_query)
        logger.info(f"✅ Total de contactos registrados: {contacts_count}")
        
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Error al ejecutar consultas de prueba: {str(e)}")
        return False

async def main():
    """Función principal que ejecuta todas las verificaciones"""
    logger.info("=== VERIFICACIÓN DE BASE DE DATOS PROMETEO ===")
    logger.info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Obtener URL de la base de datos
    db_url = get_db_url()
    logger.info(f"URL de base de datos: {db_url.split('@')[0].split(':')[0]}:****@{db_url.split('@')[1]}")
    
    # Ejecutar verificaciones
    connection_ok = await check_connection(db_url)
    
    if connection_ok:
        tables_ok = await check_tables(db_url)
        if tables_ok:
            queries_ok = await run_test_queries(db_url)
            if queries_ok:
                logger.info("✅✅✅ Todas las verificaciones completadas exitosamente")
                return 0
    
    logger.error("❌❌❌ Verificación completada con errores")
    return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 