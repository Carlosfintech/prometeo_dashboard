"""
Seed en modo simulación:
  • Consume directamente desde Mockoon API en localhost:3002
  • Simula la inserción/actualización en la base de datos
  • Simula la ejecución del pipeline ML
"""
import logging, pandas as pd, requests, re
from datetime import datetime 
from io import StringIO
from pathlib import Path
import sys, os

# ---------- Configuración ----------
BASE_URL = "http://localhost:3002"          # Mockoon
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s ▶ %(levelname)s | %(message)s")

def _get_mock_csv(endpoint: str) -> pd.DataFrame:
    """
    Obtiene datos en formato CSV desde un endpoint de Mockoon y los convierte a DataFrame.
    """
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    
    if response.status_code == 200:
        logging.info(f"✅ {endpoint} cargado correctamente")
        return pd.read_csv(StringIO(response.text))
    else:
        logging.error(f"❌ Error al cargar {endpoint}: {response.status_code}")
        return pd.DataFrame()

def load_sources():
    """
    Descarga todas las tablas necesarias desde la API Mockoon
    """
    logging.info("⤵ Descargando CSV desde Mockoon …")
    demo = _get_mock_csv("/demographics")
    prod = _get_mock_csv("/products")
    tx = _get_mock_csv("/transactions")
    
    # Verificar que se obtuvieron datos
    if demo.empty or prod.empty or tx.empty:
        logging.warning("⚠️ Uno o más DataFrames están vacíos después de la descarga")
        return None, None, None
    
    # Mostrar un vistazo de los datos descargados
    logging.info(f"Demographics: {len(demo)} registros")
    logging.info(f"Products: {len(prod)} registros")
    logging.info(f"Transactions: {len(tx)} registros")
    
    return demo, prod, tx

def parse_income(income_str):
    """
    Parsea diferentes formatos de ingresos a un valor numérico
    """
    try:
        # Eliminar cualquier símbolo de moneda, comas, etc.
        income_str = str(income_str).replace('$', '').replace(',', '')
        
        # Verificar si es un rango (3000-5000)
        if '-' in income_str:
            return float(income_str.split('-')[0].strip())
        
        # Verificar si tiene 'k' (30k)
        if 'k' in income_str.lower():
            return float(income_str.lower().replace('k', '')) * 1000
            
        # Si no, convertir directamente
        return float(income_str)
    except Exception as e:
        logging.warning(f"⚠️ Error al convertir ingreso '{income_str}': {e}")
        return 3000.0  # Valor predeterminado en caso de error

def simulate_ml_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simula la ejecución del modelo ML para generar predicciones
    """
    import numpy as np
    
    # Generar predicciones aleatorias
    n_samples = len(df)
    probabilities = np.random.random(n_samples) * 0.9 + 0.05  # Entre 0.05 y 0.95
    
    # Crear dataframe de salida
    predictions = pd.DataFrame({
        'user_id': df['user_id'],
        'probability': probabilities,
        'pred_bin': (probabilities >= 0.5).astype(int),
        'created_at': datetime.now()
    })
    
    return predictions

def main():
    # Cargar datos desde Mockoon
    demo, prod, tx = load_sources()
    
    if demo is None or prod is None or tx is None:
        logging.error("❌ Error al cargar datos. Abortando.")
        return

    # Simulación: Procesamiento de demographics
    logging.info("✓ SIMULANDO inserción en base de datos...")
    
    # Simulación: Procesamiento de productos
    logging.info("✓ SIMULANDO inserción de productos...")
    
    # Simulación: Procesamiento de transacciones
    logging.info("✓ SIMULANDO inserción de transacciones...")
    
    # Simulación: Generación de características
    logging.info("✓ SIMULANDO generación de características...")
    
    # Simulación: Generación de predicciones
    logging.info("Generando predicciones simuladas...")
    predictions = simulate_ml_model(demo)
    logging.info(f"✓ Se generaron {len(predictions)} predicciones")
    
    # Mostrar algunas predicciones
    logging.info("Muestra de predicciones generadas:")
    print(predictions.head(5))
    
    # Guardar predicciones en CSV
    output_path = Path("predictions_sim.csv")
    predictions.to_csv(output_path, index=False)
    logging.info(f"✓ Predicciones guardadas en {output_path}")
    
    logging.info("✓ Proceso de seed simulado completado exitosamente")

if __name__ == "__main__":
    main() 