"""
Seed completo usando la API Mockoon:
  • Consume directamente desde Mockoon API en localhost:3002
  • Inserta/actualiza los datos en las tablas adecuadas
  • Ejecuta el pipeline ML y guarda predicciones
"""
import asyncio, argparse, logging, os, sys, pandas as pd, requests, re
from datetime import datetime
from io import StringIO
from pathlib import Path
from app.database import SessionLocal
from app.models import Client, Prediction
from app.ml_service import write_batch

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
    
    # Verificar que se obtuvieron datos
    if demo.empty:
        logging.warning("⚠️ No se pudieron cargar los datos demográficos")
        return None
    
    logging.info(f"Demographics: {len(demo)} registros")
    return demo

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

# ---------------- main ----------------
async def main():
    # Cargar datos desde Mockoon
    demo = load_sources()
    
    if demo is None:
        logging.error("❌ Error al cargar datos. Abortando.")
        return

    async with SessionLocal() as ses:
        # Insertar datos demográficos
        for r in demo.itertuples():
            try:
                # Convertir el ingreso
                income = parse_income(r.income_range)
                
                # Crear o actualizar el cliente
                client = Client(
                    id=r.user_id,
                    name=f"Cliente {r.user_id}",
                    age=r.age,
                    income=income,
                    profile=r.risk_profile
                )
                await ses.merge(client)
                
            except Exception as e:
                logging.error(f"Error al procesar cliente {r.user_id}: {e}")
        
        await ses.commit()
        logging.info("✓ Datos demográficos insertados")
        
        # ---------- Predicciones ----------
        logging.info("Generando predicciones...")
        await write_batch(ses, demo[["user_id"]])
        logging.info("✓ Predicciones generadas y guardadas")
        
        logging.info("✓ Proceso de seed completado exitosamente")

if __name__ == "__main__":
    asyncio.run(main())