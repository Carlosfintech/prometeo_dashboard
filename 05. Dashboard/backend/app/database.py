"""
Configura SQLAlchemy async + modelos ORM.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/prometeo")

# Crear el motor de base de datos asíncrono
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

# Crear una fábrica de sesiones asíncronas
async_session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_db():
    """
    Obtener una sesión de base de datos asíncrona.
    Para usar como dependencia en FastAPI.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()