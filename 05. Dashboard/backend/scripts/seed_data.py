"""
Seed definitivo:
  • Opción 1 (por defecto): lee los CSV reales de 05.Dashboard/backend/data/raw
  • Opción 2: --from-api descarga CSV desde Mockoon (localhost:3002)
  • Inserta/actualiza Demographic, Product, Transaction
  • Llama generate_features() y write_batch() => prediction_results
Ejemplos:
    python -m scripts.seed_data              # CSV locales
    python -m scripts.seed_data --from-api   # Mockoon
"""
import asyncio, argparse, logging, os, pandas as pd, requests, re
from io import StringIO
from pathlib import Path
from datetime import datetime
from app.database import SessionLocal, Demographic, Product, Transaction
from app.ml_service import write_batch   # usa generate_features auténtico

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
BASE_URL = "http://localhost:3002"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s ▶ %(levelname)s | %(message)s")

def csv_local(name: str) -> pd.DataFrame:
    f = DATA_DIR / name
    if not f.exists():
        raise FileNotFoundError(f"CSV no hallado: {f}")
    return pd.read_csv(f)

def csv_api(endpoint: str) -> pd.DataFrame:
    r = requests.get(f"{BASE_URL}{endpoint}")
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))

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

async def seed_demographics(session, df):
    """Inserta datos demográficos mapeados correctamente"""
    for r in df.itertuples():
        # Mapear campos del CSV a los campos del modelo
        demo = Demographic(
            id=int(r.user_id.replace('user_', '')),  # Convertir 'user_001' a 1
            name=f"Cliente {r.user_id}",
            age=r.age,
            income=parse_income(r.income_range),
            profile=r.risk_profile
        )
        await session.merge(demo)

async def seed_products(session, df):
    """Inserta productos mapeados correctamente"""
    for r in df.itertuples():
        prod = Product(
            id=r.Index + 1,  # Usar índice como ID
            name=r.product_type,
            description=f"Producto {r.product_type}",
            type=r.product_type
        )
        await session.merge(prod)

async def seed_transactions(session, df):
    """Inserta transacciones mapeadas correctamente"""
    for r in df.itertuples():
        tx = Transaction(
            id=r.transaction_id if hasattr(r, 'transaction_id') else r.Index + 1,
            user_id=int(r.user_id.replace('user_', '')),
            product_id=1,  # Producto por defecto
            amount=r.amount,
            date=pd.to_datetime(r.date) if hasattr(r, 'date') else datetime.now()
        )
        await session.merge(tx)

async def main(from_api: bool):
    if from_api:
        logging.info("Obteniendo datos desde Mockoon API...")
        demog = csv_api("/demographics")
        prod  = csv_api("/products")
        tx    = csv_api("/transactions")
    else:
        logging.info("Leyendo datos desde archivos CSV locales...")
        demog = csv_local("demographics.csv")
        prod  = csv_local("products.csv")
        tx    = csv_local("transactions.csv")
    
    logging.info(f"Procesando {len(demog)} demographic records, {len(prod)} products, {len(tx)} transactions")

    async with SessionLocal() as ses:
        logging.info("Insertando demographics...")
        await seed_demographics(ses, demog)
        
        logging.info("Insertando products...")
        await seed_products(ses, prod)
        
        logging.info("Insertando transactions...")
        await seed_transactions(ses, tx)
        
        await ses.commit()
        logging.info("✓ Tablas crudas pobladas")

        # ---------- Predicción ----------
        logging.info("Generando predicciones...")
        # Convertir los user_id a enteros para el modelo
        user_ids = pd.DataFrame({
            'user_id': [int(uid.replace('user_', '')) for uid in demog['user_id']]
        })
        await write_batch(ses, user_ids)
        logging.info("✓ Predicciones guardadas en prediction_results")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from-api", action="store_true",
                   help="Usar Mockoon en vez de CSV locales")
    args = p.parse_args()
    asyncio.run(main(args.from_api))