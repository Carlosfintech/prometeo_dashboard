"""
Seed definitivo:
  • Opción 1 (por defecto): lee los CSV reales de 05.Dashboard/backend/data/raw
  • Opción 2: --from-api descarga CSV desde Mockoon (localhost:3002)
  • Inserta/actualiza Demographic, Product, Transaction
  • Actualiza las tablas utilizando SQLAlchemy sincrónico
Ejemplos:
    python -m scripts.seed_data              # CSV locales
    python -m scripts.seed_data --from-api   # Mockoon

IMPORTANTE: Antes de ejecutar este script, generar el modelo dummy:
    python backend/models/create_dummy_model.py
    python -m backend.scripts.seed_data
"""
import sys
from pathlib import Path

# Asegura que 'backend' esté en sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import argparse, logging, os, pandas as pd, requests, re
from io import StringIO
from datetime import datetime, date
import sqlalchemy
from sqlalchemy import create_engine, inspect, Table, MetaData, insert, select, text
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, Client, Prediction, Contact, Product, Transaction, Goal
from features.pipeline_featureengineering_func import generate_features
import pickle

# Alias para mantener compatibilidad con scripts
Demographic = Client

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
BASE_URL = "http://localhost:3002"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s ▶ %(levelname)s | %(message)s")

# Obtener la URL de la base de datos desde las variables de entorno (versión sincrónica)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:1111@localhost:5432/prometeo_db")
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")

# Crear motor sincrónico
engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Acceder directamente a las tablas
metadata = MetaData()
demographics_table = Table('demographics', metadata, autoload_with=engine)
products_table = Table('products', metadata, autoload_with=engine)
transactions_table = Table('transactions', metadata, autoload_with=engine)
prediction_results_table = Table('prediction_results', metadata, autoload_with=engine)

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

def seed_demographics(conn, df):
    """Inserta datos demográficos mapeados correctamente para la estructura real de la tabla"""
    for r in df.itertuples():
        user_id = r.user_id
        
        # Verificar si el usuario ya existe
        exists = conn.execute(
            select(demographics_table.c.id).where(demographics_table.c.user_id == user_id)
        ).scalar_one_or_none()
        
        # Datos para insertar/actualizar
        data = {
            'user_id': user_id,
            'age': r.age,
            'income_range': r.income_range,
            'risk_profile': r.risk_profile,
            'occupation': r.occupation if hasattr(r, 'occupation') else 'Professional',
            'profile_category': 'standard',
            'segment': 'potential',
            'acquisition_date': date.today(),
            'last_contact_date': None,
            'status': 'pending',
            'priority': 'medium',
            'probability': 0.5  # Valor por defecto, se actualizará luego
        }
        
        # Si el usuario existe, actualizar
        if exists:
            conn.execute(
                demographics_table.update().where(demographics_table.c.user_id == user_id).values(data)
            )
        # Si no existe, insertar
        else:
            conn.execute(demographics_table.insert().values(data))

def seed_products(conn, df):
    """Inserta productos mapeados correctamente según la estructura real de la tabla"""
    for r in df.itertuples():
        product_id = r.Index + 1
        user_id = r.user_id
        
        # Verificar si el producto ya existe
        exists = conn.execute(
            select(products_table.c.id).where(
                products_table.c.id == product_id, 
                products_table.c.user_id == user_id
            )
        ).scalar_one_or_none()
        
        # Datos para insertar/actualizar
        data = {
            'user_id': user_id,
            'product_type': r.product_type,
            'contract_date': pd.to_datetime(r.contract_date) if hasattr(r, 'contract_date') else date.today(),
            'status': 'active',
            'product_value': 1000.0,  # Valor por defecto
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Si el producto existe, actualizar
        if exists:
            conn.execute(
                products_table.update().where(products_table.c.id == product_id).values(data)
            )
        # Si no existe, insertar
        else:
            conn.execute(products_table.insert().values(data))

def seed_transactions(conn, df):
    """Inserta transacciones mapeadas correctamente según la estructura real de la tabla"""
    for idx, r in enumerate(df.itertuples()):
        # Usar un ID numérico secuencial en lugar del UUID
        tx_id = idx + 1
        user_id = r.user_id
        
        # Datos para insertar/actualizar basados en la estructura real de la tabla
        data = {
            'user_id': user_id,
            'transaction_date': pd.to_datetime(r.date).date() if hasattr(r, 'date') else date.today(),
            'amount': r.amount,
            'transaction_type': 'payment',  # Valor por defecto
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Verificar si ya existe un registro con este ID
        exists = conn.execute(
            select(transactions_table.c.id).where(transactions_table.c.id == tx_id)
        ).scalar_one_or_none()
        
        if exists:
            # Actualizar transacción existente
            conn.execute(
                transactions_table.update().where(transactions_table.c.id == tx_id).values(data)
            )
        else:
            # Insertar nueva transacción
            # Permitir que la secuencia genere el ID automáticamente
            conn.execute(transactions_table.insert().values(data))

def add_predictions(conn, demog, prod, tx):
    # 1. Generar features reales
    feats = generate_features(
        demographics_df=demog,
        products_df=prod,
        transactions_df=tx,
        reference_date=pd.Timestamp("2024-01-01"),
        output_file=None
    )
    # 2. Cargar modelo y umbral
    model_path = ROOT / "models" / "xgb_model.pkl"
    thresh_path = ROOT / "models" / "xgb_threshold.txt"
    model = pickle.load(open(model_path, "rb"))
    threshold = float(Path(thresh_path).read_text().strip())
    # 3. Predecir
    # Eliminar columnas que no son características
    X = feats.drop(columns=["user_id", "insurance", "pred_bin"], errors="ignore")
    
    # Convertir todas las columnas a tipo numérico
    for col in X.columns:
        if X[col].dtype == 'object' or X[col].dtype.name == 'category':
            X[col] = X[col].astype(float)
    
    proba = model.predict_proba(X)[:,1]
    pred_bin = (proba >= threshold).astype(int)
    
    # 4. Insertar o actualizar predicciones
    for uid, p, b in zip(feats["user_id"], proba, pred_bin):
        uid_str = str(uid)  # casteo a texto para evitar mismatch de tipos
        exists = conn.execute(
            select(prediction_results_table.c.user_id)
            .where(prediction_results_table.c.user_id == uid_str)
        ).scalar_one_or_none()
        row = {
          "user_id": uid_str,
          "probability": float(p),
          "is_target": bool(b),
          "created_at": datetime.now()
        }
        if exists:
            conn.execute(
                prediction_results_table.update()
                .where(prediction_results_table.c.user_id == uid_str)
                .values(row)
            )
        else:
            conn.execute(prediction_results_table.insert().values(row))

def main(from_api: bool):
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

    # Usar la conexión directa para todas las operaciones
    with engine.connect() as conn:
        # conn.execution_options(isolation_level="AUTOCOMMIT")  # Comentado según instrucciones
        
        logging.info("Insertando demographics...")
        seed_demographics(conn, demog)
        
        logging.info("Insertando products...")
        seed_products(conn, prod)
        
        logging.info("Insertando transactions...")
        seed_transactions(conn, tx)
        
        # ---------- Predicción ----------
        logging.info("Generando predicciones con el pipeline ML real...")
        try:
            add_predictions(conn, demog, prod, tx)
        except Exception as e:
            logging.error(f"Error al generar predicciones: {e}")
            
            # En caso de error, generar predicciones aleatorias como fallback
            logging.info("Generando predicciones aleatorias como fallback...")
            import random
            for r in demog.itertuples():
                user_id = r.user_id
                uid_str = str(user_id)
                probability = random.uniform(0.1, 0.9)
                is_target = probability > 0.5
                exists = conn.execute(
                    select(prediction_results_table.c.user_id)
                    .where(prediction_results_table.c.user_id == uid_str)
                ).scalar_one_or_none()
                row = {
                    "user_id": uid_str,
                    "probability": probability,
                    "is_target": is_target,
                    "created_at": datetime.now()
                }
                if exists:
                    conn.execute(
                        prediction_results_table.update()
                        .where(prediction_results_table.c.user_id == uid_str)
                        .values(row)
                    )
                else:
                    conn.execute(prediction_results_table.insert().values(row))
        
        conn.execute(text("COMMIT"))
        
    logging.info("✓ Datos guardados en la base de datos")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from-api", action="store_true",
                   help="Usar Mockoon en vez de CSV locales")
    args = p.parse_args()
    main(args.from_api)