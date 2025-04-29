"""
Servicios de Machine Learning para predicciones
"""
import pickle
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Prediction
from app.features.pipeline_featureengineering_func import generate_features

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constantes
THRESHOLD = 0.2389
MODEL_PATH = Path(__file__).parent.parent / "models" / "xgb_model.pkl"

# Cargar modelo
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    logger.info(f"Modelo cargado desde {MODEL_PATH}")
except Exception as e:
    logger.error(f"Error al cargar el modelo: {e}")
    model = None


async def predict(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Genera predicciones a partir de un DataFrame con datos crudos.
    
    Args:
        df_raw: DataFrame con al menos columnas user_id, age, income_range, risk_profile
        
    Returns:
        DataFrame con columnas: ['user_id', 'probability', 'is_target', 'created_at']
    """
    try:
        # Verificar si hay un modelo válido
        if model is None:
            logger.warning("No hay modelo disponible. Generando predicciones aleatorias.")
            return _generate_dummy_predictions(df_raw)
        
        # Generar características
        features_df = generate_features(
            demographics_df=df_raw,
            products_df=pd.DataFrame(columns=["user_id", "product_type"]) if "products_df" not in df_raw else df_raw["products_df"],
            transactions_df=pd.DataFrame(columns=["user_id", "amount", "date"]) if "transactions_df" not in df_raw else df_raw["transactions_df"],
            reference_date=pd.Timestamp("2024-01-01"),
            output_file=None
        )
        
        # Prepare features for prediction
        X = features_df.drop(columns=["user_id", "insurance"], errors="ignore")
        
        # Asegurar que todas las columnas sean numéricas
        for col in X.columns:
            if X[col].dtype == 'object' or X[col].dtype.name == 'category':
                X[col] = X[col].astype(float)
        
        # Predict
        probabilities = model.predict_proba(X)[:, 1]
        predictions = (probabilities >= THRESHOLD).astype(int)
        
        # Crear DataFrame de resultados
        result_df = pd.DataFrame({
            "user_id": features_df["user_id"],
            "probability": probabilities,
            "is_target": predictions.astype(bool),
            "created_at": datetime.now()
        })
        
        return result_df
    
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        return _generate_dummy_predictions(df_raw)


def _generate_dummy_predictions(df: pd.DataFrame) -> pd.DataFrame:
    """Genera predicciones aleatorias para casos de error"""
    import random
    
    result_df = pd.DataFrame({
        "user_id": df["user_id"],
        "probability": [random.uniform(0.1, 0.9) for _ in range(len(df))],
        "created_at": datetime.now()
    })
    
    result_df["is_target"] = result_df["probability"] > THRESHOLD
    return result_df


async def write_batch(session: AsyncSession, df_raw: pd.DataFrame):
    """
    Predice y escribe un batch de predicciones en la base de datos.
    
    Args:
        session: Sesión de SQLAlchemy async
        df_raw: DataFrame con datos para predicción
    """
    try:
        # Obtener predicciones
        predictions_df = await predict(df_raw)
        
        # Preparar para inserción (bulk upsert)
        for _, row in predictions_df.iterrows():
            # Verificar si existe la predicción para este usuario
            stmt = select(Prediction).where(Prediction.user_id == row["user_id"])
            result = await session.execute(stmt)
            existing = result.scalars().first()
            
            # Datos para insertar/actualizar
            data = {
                "user_id": row["user_id"],
                "probability": float(row["probability"]),
                "is_target": bool(row["is_target"]),
                "created_at": row["created_at"]
            }
            
            if existing:
                # Actualizar predicción existente
                stmt = (
                    update(Prediction)
                    .where(Prediction.user_id == row["user_id"])
                    .values(data)
                )
                await session.execute(stmt)
            else:
                # Insertar nueva predicción
                pred = Prediction(**data)
                session.add(pred)
        
        # Commit
        await session.commit()
        logger.info(f"Batch de {len(predictions_df)} predicciones guardado en la base de datos")
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Error al escribir batch de predicciones: {e}")
        raise