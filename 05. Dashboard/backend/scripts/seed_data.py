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
import asyncio, argparse, logging, os, pandas as pd, requests
from io import StringIO
from pathlib import Path
from sqlalchemy import insert
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

async def upsert_table(session, model, df, keys):
    await session.execute(
        insert(model).values(df.to_dict("records"))
        .on_conflict_do_update(index_elements=keys,
                               set_={c: getattr(insert(model).excluded, c)
                                     for c in df.columns if c not in keys})
    )

async def main(from_api: bool):
    if from_api:
        demog = csv_api("/demographics")
        prod  = csv_api("/products")
        tx    = csv_api("/transactions")
    else:
        demog = csv_local("demographics.csv")
        prod  = csv_local("products.csv")
        tx    = csv_local("transactions.csv")

    async with SessionLocal() as ses:
        await upsert_table(ses, Demographic, demog, ["user_id"])
        await upsert_table(ses, Product,      prod,  ["user_id", "product_type"])
        await upsert_table(ses, Transaction,  tx,    ["transaction_id"])
        await ses.commit()
        logging.info("✓ Tablas crudas pobladas")

        # ---------- Predicción ----------
        await write_batch(ses, demog[["user_id"]])
        logging.info("✓ Predicciones guardadas en prediction_results")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--from-api", action="store_true",
                   help="Usar Mockoon en vez de CSV locales")
    args = p.parse_args()
    asyncio.run(main(args.from_api))