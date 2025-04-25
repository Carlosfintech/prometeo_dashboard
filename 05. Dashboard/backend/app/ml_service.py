"""
Carga pipeline + modelo XGBoost y ofrece utilidades para predicción batch.
"""
from datetime import datetime
import os, sys
import pickle, pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from .database import Prediction
import numpy as np
from typing import Dict, Any, List

# Ensure pipeline code is importable
PIPELINE_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../03.Modelo/src"))
if PIPELINE_SRC not in sys.path:
    sys.path.insert(0, PIPELINE_SRC)
from features.pipeline_featureengineering_func import run_pipeline

THRESHOLD = "(COLOCAR AQUI EL ARCHIVO DE THRESHOLD)"
MODEL_PATH = "xgb_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

async def predict(df_raw: pd.DataFrame) -> pd.DataFrame:
    x = run_pipeline(df_raw)
    probs = model.predict_proba(x)[:, 1]
    out = df_raw[["user_id"]].copy()
    out["probability"] = probs
    out["pred_bin"] = (probs >= THRESHOLD).astype(int)
    out["created_at"] = datetime.utcnow()
    return out


async def write_batch(session: AsyncSession, df_raw: pd.DataFrame):
    preds_df = await predict(df_raw)
    # upsert en bloque
    for row in preds_df.to_dict(orient="records"):
        await session.merge(Prediction(**row))
    await session.commit()

def load_model():
    """
    Simula la carga de un modelo de ML
    En un caso real, cargaríamos un modelo desde un archivo
    """
    # Simular modelo cargado (podría ser un modelo de scikit-learn, tensorflow, etc.)
    return {
        "name": "customer_conversion_model",
        "version": "1.0.0",
        "type": "random_forest",
    }

def predict_conversion_probability(client_data: Dict[str, Any]) -> float:
    """
    Predice la probabilidad de conversión de un cliente
    
    Args:
        client_data: Diccionario con los datos del cliente
            Debe incluir al menos: edad, ingreso, perfil
            
    Returns:
        Probabilidad de conversión (0.0 - 1.0)
    """
    # En un caso real, haríamos preprocesamiento y usaríamos un modelo
    # Aquí simplemente asignamos probabilidades basadas en reglas simples
    
    # Extraer características relevantes
    age = client_data.get("edad", 0)
    income = _parse_income(client_data.get("ingreso", "0"))
    profile = client_data.get("perfil", "").lower()
    
    # Base de probabilidad
    prob = 0.5
    
    # Ajustes por edad
    if 30 <= age <= 55:
        prob += 0.1
    elif age > 55:
        prob += 0.05
    else:
        prob -= 0.05
        
    # Ajustes por ingreso
    if income >= 4000:
        prob += 0.15
    elif income >= 3000:
        prob += 0.1
    elif income >= 2000:
        prob += 0.05
        
    # Ajustes por perfil
    if profile == "agresivo":
        prob += 0.1
    elif profile == "moderado":
        prob += 0.05
    
    # Añadir aleatoriedad para variar los resultados
    prob += np.random.normal(0, 0.05)
    
    # Limitar la probabilidad al rango [0.1, 0.95]
    return max(0.1, min(0.95, prob))

def batch_predict(clients_data: List[Dict[str, Any]]) -> List[float]:
    """
    Realiza predicciones para múltiples clientes
    
    Args:
        clients_data: Lista de diccionarios con datos de clientes
            
    Returns:
        Lista de probabilidades de conversión
    """
    return [predict_conversion_probability(client) for client in clients_data]

def _parse_income(income_str: str) -> float:
    """
    Convierte un string de ingreso (ej: "$3,500") a un valor numérico
    """
    try:
        # Eliminar el símbolo de moneda y comas
        clean_income = income_str.replace("$", "").replace(",", "")
        return float(clean_income)
    except (ValueError, AttributeError):
        return 0.0