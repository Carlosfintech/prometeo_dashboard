"""
Script para verificar los datos insertados en la base de datos
"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:1111@localhost:5432/prometeo_db')

with engine.connect() as conn:
    # Verificar predicciones
    print("\nPredicciones:")
    result = conn.execute(text('SELECT * FROM prediction_results LIMIT 5'))
    rows = result.fetchall()
    for row in rows:
        print(row)
        
    # Verificar clientes
    print("\nClientes:")
    result = conn.execute(text('SELECT * FROM demographics LIMIT 5'))
    rows = result.fetchall()
    for row in rows:
        print(row)
        
    # Contar todos los registros
    print("\nConteo de registros:")
    result = conn.execute(text('''
    SELECT 
        (SELECT COUNT(*) FROM demographics) as demographics_count,
        (SELECT COUNT(*) FROM products) as products_count,
        (SELECT COUNT(*) FROM transactions) as transactions_count,
        (SELECT COUNT(*) FROM prediction_results) as predictions_count
    '''))
    counts = result.fetchone()
    print(f"Demografía: {counts[0]}, Productos: {counts[1]}, Transacciones: {counts[2]}, Predicciones: {counts[3]}") 