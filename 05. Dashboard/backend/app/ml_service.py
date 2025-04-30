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
import os
from typing import Dict, Any, Optional, List, Tuple

from .database import Prediction
from app.features.pipeline_featureengineering_func import generate_features

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constantes
THRESHOLD = 0.5

# Ruta al modelo guardado
model_paths = [
    Path("xgb_model.pkl"),                       # Ruta relativa al directorio principal
    Path("./xgb_model.pkl"),                     # Ruta relativa explícita
    Path("../xgb_model.pkl"),                    # Directorio anterior
    Path("/app/xgb_model.pkl"),                  # Ruta absoluta en contenedor
    Path(os.environ.get("MODEL_PATH", "")),      # Ruta desde variable de entorno
]

# Modelo global - será cargado cuando se importe este módulo
xgb_model = None

# Intentar cargar el modelo desde varias ubicaciones posibles
for model_path in model_paths:
    try:
        if model_path.exists() and model_path.is_file():
            logger.info(f"Cargando modelo desde: {model_path}")
            with open(model_path, 'rb') as f:
                xgb_model = pickle.load(f)
            logger.info(f"Modelo cargado exitosamente desde {model_path}")
            break
    except Exception as e:
        logger.error(f"Error al cargar el modelo desde {model_path}: {str(e)}")

# Si no se pudo cargar el modelo, crear uno dummy para desarrollo
if xgb_model is None:
    logger.warning("No se pudo cargar el modelo real. Usando un modelo dummy para entorno de desarrollo.")
    
    # Clase simple que simula un modelo XGBoost
    class DummyModel:
        def predict_proba(self, X):
            # Generar probabilidades aleatorias para pruebas
            n_samples = len(X) if hasattr(X, '__len__') else 1
            probas = np.random.rand(n_samples, 2)
            # Normalizar para que sumen 1 por fila
            return probas / probas.sum(axis=1, keepdims=True)
    
    xgb_model = DummyModel()
    logger.info("Modelo dummy creado correctamente")

# Verificación final del modelo
if xgb_model:
    logger.info(f"Modelo de ML listo para usar: {type(xgb_model).__name__}")
else:
    logger.error("ERROR CRÍTICO: No se pudo inicializar ningún modelo de ML")

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
        if xgb_model is None:
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
        probabilities = xgb_model.predict_proba(X)[:, 1]
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

def predict_client_probability(features: Dict[str, Any]) -> float:
    """
    Predice la probabilidad de que un cliente sea de alto valor utilizando el modelo XGBoost.
    
    Args:
        features: Diccionario con las características del cliente
        
    Returns:
        float: Probabilidad entre 0 y 1
    """
    try:
        if xgb_model is None:
            logger.error("El modelo no está disponible para predicciones")
            return 0.5  # Valor por defecto si no hay modelo
            
        # Preparar características para el modelo
        # En una aplicación real, aquí habría preprocesamiento y transformación
        X = np.array([[
            features.get('age', 0),
            # Convertir rangos de ingresos a valores numéricos
            {'0-50k': 1, '50k-100k': 2, '100k-150k': 3, '150k+': 4}.get(features.get('income_range', '0-50k'), 1),
            # Convertir perfil de riesgo a valores numéricos
            {'conservative': 1, 'moderate': 2, 'aggressive': 3}.get(features.get('risk_profile', 'moderate'), 2),
            # Otras características necesarias para el modelo
        ]])
        
        # Obtener predicciones
        # En XGBoost, predict_proba devuelve [prob_clase_0, prob_clase_1]
        proba = xgb_model.predict_proba(X)
        
        # Devolver la probabilidad de la clase positiva (clase 1)
        result = float(proba[0, 1])
        logger.info(f"Predicción exitosa: {result:.4f}")
        return result
        
    except Exception as e:
        logger.error(f"Error al hacer predicción: {str(e)}")
        # En caso de error, devolver un valor neutral de probabilidad
        return 0.5

def get_client_priority(probability: float) -> str:
    """Determina la prioridad del cliente basado en su probabilidad"""
    if probability >= 0.7:
        return "high"
    elif probability >= 0.4:
        return "medium"
    else:
        return "low"

def evaluate_model_performance(predictions: List[float], actual: List[bool]) -> Dict[str, float]:
    """
    Evalúa el rendimiento del modelo según predicciones y valores reales
    
    Args:
        predictions: Lista de probabilidades predichas
        actual: Lista de valores reales (True/False)
        
    Returns:
        Dict con métricas de rendimiento (precisión, recall, etc.)
    """
    try:
        # Convertir predicciones a clases binarias según umbral
        pred_classes = [p >= THRESHOLD for p in predictions]
        
        # Calcular métricas básicas
        tp = sum(1 for p, a in zip(pred_classes, actual) if p and a)
        fp = sum(1 for p, a in zip(pred_classes, actual) if p and not a)
        tn = sum(1 for p, a in zip(pred_classes, actual) if not p and not a)
        fn = sum(1 for p, a in zip(pred_classes, actual) if not p and a)
        
        # Calcular métricas derivadas
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }
        
    except Exception as e:
        logger.error(f"Error al evaluar el modelo: {str(e)}")
        return {
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0
        }