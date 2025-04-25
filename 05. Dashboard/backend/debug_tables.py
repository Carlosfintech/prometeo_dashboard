"""
Script para depurar las tablas de la base de datos
"""
import asyncio
from sqlalchemy import text, inspect
from app.database import engine, Client, Base

async def main():
    # Consultar datos de la tabla demographics
    async with engine.connect() as conn:
        # Usar SQLAlchemy 2.0 para consultas
        result = await conn.execute(text('SELECT * FROM demographics LIMIT 5'))
        
        # Imprimir el resultado
        print("Datos en la tabla demographics:")
        for row in result:
            # Convertir a diccionario de manera segura
            row_dict = {}
            for column, value in row._mapping.items():
                row_dict[column] = value
            print(row_dict)
        
        # Verificar la estructura de la tabla
        result = await conn.execute(text('''
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'demographics'
        '''))
        
        print("\nEstructura de la tabla demographics:")
        for row in result:
            row_dict = {}
            for column, value in row._mapping.items():
                row_dict[column] = value
            print(row_dict)

if __name__ == "__main__":
    asyncio.run(main()) 