"""
Configuración y modelos de base de datos utilizando SQLAlchemy 2.0 async
"""
import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.future import select

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# URL de la base de datos desde variables de entorno
# En Render, DATABASE_URL se configura automáticamente para PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")

# Si DATABASE_URL empieza con postgres://, cambiarlo a postgresql://
# (esto es necesario para SQLAlchemy con esquema asyncpg)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
# Si DATABASE_URL no tiene asyncpg, agregarlo
if DATABASE_URL and "postgresql://" in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# URL de la base de datos por defecto para desarrollo
if not DATABASE_URL:
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_password = os.environ.get("POSTGRES_PASSWORD", "1111")
    db_host = os.environ.get("POSTGRES_HOST", "localhost")
    db_port = os.environ.get("POSTGRES_PORT", "5432")
    db_name = os.environ.get("POSTGRES_DB", "prometeo_db")
    
    DATABASE_URL = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

logger.info(f"Conectando a la base de datos: {DATABASE_URL.split('@')[0].split(':')[0]}:****@{DATABASE_URL.split('@')[1]}")

# Configuración de engine con parámetros de conexión optimizados
engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    pool_size=5,               # Tamaño inicial del pool de conexiones
    max_overflow=10,           # Conexiones adicionales permitidas
    pool_timeout=30,           # Tiempo máximo de espera para obtener una conexión (segundos)
    pool_recycle=1800,         # Reciclar conexiones después de 30 minutos
    pool_pre_ping=True,        # Verificar conexiones antes de usarlas
    connect_args={
        "timeout": 30,         # Timeout de conexión
        "command_timeout": 30  # Timeout de comandos
    }
)

# Evento para monitorear errores de conexión
@event.listens_for(engine.sync_engine, "engine_connect")
def ping_connection(connection, branch):
    if branch:
        # "branch" se refiere a una sub-conexión de un Connection a nivel de Engine
        return

    # Ping la base de datos
    try:
        connection.scalar("SELECT 1")
    except:
        # Conexión es inválida, será cerrada y reemplazada
        logger.warning("Conexión a la base de datos inválida; será reciclada")
        connection.close()
        raise

# Configuración más robusta de la sesión con retry
SessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False,            # No hacer flush automáticamente para mejor control
    autocommit=False            # No hacer commit automáticamente para mejor control de transacciones
)

# Base declarativa para los modelos
Base = declarative_base()

# Modelos
class Client(Base):
    __tablename__ = "demographics"  # Nombre real en la base de datos
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True, nullable=False, index=True)
    age = Column(Integer)
    income_range = Column(String)
    risk_profile = Column(String)
    occupation = Column(String)
    profile_category = Column(String)
    segment = Column(String)
    acquisition_date = Column(DateTime)
    last_contact_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    priority = Column(String, default="medium")
    probability = Column(Float, default=0.5)
    opportunity_value = Column(Float, default=1000.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    
    # Relaciones
    predictions = relationship("Prediction", back_populates="client", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Client(id={self.id}, user_id='{self.user_id}', probability={self.probability:.2f})>"

class Prediction(Base):
    __tablename__ = "prediction_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("demographics.user_id"))
    probability = Column(Float)
    is_target = Column(Boolean)
    features = Column(String, nullable=True)
    prediction_date = Column(DateTime, nullable=True)
    actual_conversion = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    
    # Relaciones
    client = relationship("Client", back_populates="predictions")
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, user_id='{self.user_id}', probability={self.probability:.2f})>"

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("demographics.id"))
    contacted_at = Column(DateTime, default=datetime.now)
    channel = Column(String)
    notes = Column(String, nullable=True)
    outcome = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relaciones
    client = relationship("Client", back_populates="contacts")
    
    def __repr__(self):
        return f"<Contact(id={self.id}, client_id={self.client_id}, channel='{self.channel}')>"

# Función para obtener una sesión de base de datos con reintentos
async def get_db(max_retries=3, retry_delay=1):
    """Obtener una sesión de base de datos con manejo de reintentos"""
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            # Si no es el primer intento, esperar antes de reintentar
            if attempt > 0:
                await asyncio.sleep(retry_delay)
                logger.warning(f"Reintentando conexión a la base de datos (intento {attempt+1}/{max_retries})")
            
            # Iniciar sesión
            db = SessionLocal()
            # Verificar conexión con una consulta simple
            await db.execute(select(1))
            # Si llegamos aquí, la conexión es buena
            try:
                yield db
            finally:
                await db.close()
            return  # Salir después de yield exitoso
            
        except Exception as e:
            attempt += 1
            last_error = e
            logger.error(f"Error de conexión a la base de datos: {str(e)}")
            # Si estamos usando una sesión, asegurarse de cerrarla
            try:
                await db.close()
            except:
                pass
    
    # Si llegamos aquí, todos los intentos fallaron
    logger.critical(f"No se pudo establecer conexión a la base de datos después de {max_retries} intentos.")
    logger.critical(f"Último error: {str(last_error)}")
    raise last_error