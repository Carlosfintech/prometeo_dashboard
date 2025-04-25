"""
Semilla inicial de datos.
Ejecuta:  python -m scripts.seed_data

Nota: Para que este script funcione, primero debes hacer:
pip install -e "03.Modelo/src"   # hace importable src.features directamente
"""
import asyncio, pandas as pd
from pathlib import Path
from app.database import SessionLocal
from app.database import Client, Prediction          # modelos ya existentes
from app.ml_service import predict, write_batch      # usa generate_features internamente

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_clients.csv"

async def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} no existe")
    
    print(f"Leyendo datos desde: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    async with SessionLocal() as session:
        # ---- 1. insertar / actualizar clientes ----
        for row in df.itertuples():
            session.merge(
                Client(id=int(row.user_id),
                       name=row.name,
                       age=int(row.age),
                       income=float(row.income),
                       profile=row.profile)
            )
        await session.commit()
        print(f"✓ {len(df)} clientes insertados")

        # ---- 2. generar y guardar predicciones ----
        await write_batch(session, df[["user_id", "age", "income", "profile"]])
        print(f"✓ {len(df)} predicciones generadas")

if __name__ == "__main__":
    asyncio.run(main()) 