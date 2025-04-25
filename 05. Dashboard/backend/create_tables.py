"""
Script para crear todas las tablas en la base de datos
"""
from app.database import Base, engine
import asyncio

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tablas creadas correctamente")

if __name__ == "__main__":
    asyncio.run(init_db()) 