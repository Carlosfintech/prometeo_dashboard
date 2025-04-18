#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test end‑to‑end: descarga datos desde Mockoon, hace feature‑engineering,
predice con el modelo XGBoost y guarda results.csv

Este script realiza las siguientes acciones:
1. Obtiene datos demográficos, productos y transacciones desde una API Mockoon
2. Aplica transformaciones y feature engineering (clonando el pipeline original)
3. Carga un modelo pre-entrenado y predice la probabilidad de contratación de seguro
4. Guarda los resultados en un archivo CSV
5. Opcionalmente publica los resultados a una API

Uso:
    python prometeo_single_test_fixed.py
"""

import pandas as pd
import numpy as np
import requests
import pickle
import gc
import logging
import warnings
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime
import xgboost as xgb
import sys

# ------------------------------------------------------------------
# Configuración global
# ------------------------------------------------------------------
BASE_URL     = "http://localhost:3001"
POST_RESULTS = True
OUTPUT_FILE  = "results.csv"

MODEL_PATH   = Path("/Users/carloslandaverdealquicirez/Documents/Prometeo_reto/Prometeo_project copy/03.Modelo/models/xgb_model.pkl")
THRESH_PATH  = Path("/Users/carloslandaverdealquicirez/Documents/Prometeo_reto/Prometeo_project copy/03.Modelo/models/xgb_threshold.txt")
REFERENCE_DT = pd.Timestamp("2024-01-01")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s ▶  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# Añadir directorio src/features al path de Python para poder importar el módulo
sys.path.append(str(Path(__file__).parent.parent.parent / "features"))
from pipeline_featureengineering_func import generate_features

# --------- 1. Descarga y envío de datos --------------------------
def _get_df(endpoint: str) -> pd.DataFrame:
    """Descarga y parsea un endpoint de Mockoon"""
    r = requests.get(f"{BASE_URL}/{endpoint}")
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    for c in df.columns:
        if c.endswith('_date') or c == 'date':
            df[c] = pd.to_datetime(df[c])
    return df

def _post_results(results: pd.DataFrame) -> None:
    """Envía resultados al endpoint /results"""
    required = ['user_id', 't0', 't0b', 't1', 'timestamp']
    missing = [c for c in required if c not in results.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    logging.info(f"Enviando {len(results)} resultados a la API")
    try:
        resp = requests.post(
            f"{BASE_URL}/results",
            json=results[required].to_dict(orient="records")
        )
        resp.raise_for_status()
        logging.info(f"Resultados enviados correctamente: {resp.status_code}")
    except Exception as e:
        logging.error(f"Error al enviar resultados: {e}")


# --------- 2. Feature‑engineering -----------------------------------------
def transform(demog, prod, tx):
    """
    Función para transformar datos raw en features para el modelo usando el pipeline oficial.
    Calcula las variables target e IDs de usuarios, luego aplica feature engineering y ajusta
    para que coincida exactamente con lo que el modelo necesita.
    """
    logging.info("Aplicando feature engineering con función oficial...")
    
    # Extraer target y user_ids para retornarlos luego
    insurance_users = prod.loc[prod['product_type'] == 'insurance', 'user_id']
    demog['insurance'] = demog['user_id'].isin(insurance_users).astype(int)
    y = demog['insurance'].values
    user_ids = demog['user_id'].values
    
    # Usar la función del pipeline oficial para generar features
    features_df = generate_features(
        demographics_df=demog,
        products_df=prod,
        transactions_df=tx,
        reference_date=REFERENCE_DT,
        output_file=None  # No guardar archivo
    )
    
    # Adaptación para el modelo: obtener las columnas que el modelo espera
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
            
        # Verificar si el modelo tiene el atributo feature_names_in_
        if hasattr(model, 'feature_names_in_'):
            expected_columns = model.feature_names_in_
            logging.info(f"Modelo requiere {len(expected_columns)} columnas específicas")
            
            # Verificar columnas faltantes
            missing_cols = [col for col in expected_columns if col not in features_df.columns]
            if missing_cols:
                logging.warning(f"Faltan {len(missing_cols)} columnas que el modelo espera: {missing_cols[:5]}...")
                
                # Agregar columnas faltantes con valores cero
                for col in missing_cols:
                    features_df[col] = 0
                    
            # Verificar columnas extra que no necesita el modelo
            extra_cols = [col for col in features_df.columns if col not in expected_columns and col != 'user_id']
            if extra_cols:
                logging.info(f"Eliminando {len(extra_cols)} columnas que el modelo no necesita")
            
            # Seleccionar solo las columnas en el orden que el modelo espera
            X = features_df[expected_columns].copy()
            
        else:
            # Si no se puede determinar las columnas exactas, usar todas las columnas excepto user_id
            logging.warning("No se pudieron determinar las columnas exactas del modelo, usando todas")
            X = features_df.drop(columns=['user_id'], errors='ignore')
            
    except Exception as e:
        logging.error(f"Error al preparar datos para el modelo: {e}")
        # En caso de error, usar todas las columnas disponibles excepto user_id
        X = features_df.drop(columns=['user_id'], errors='ignore')
    
    # Guardar un archivo para verificación
    features_df.to_csv("features_verification.csv", index=False)
    logging.info(f"Features generadas: {X.shape[0]} filas, {X.shape[1]} columnas")
    
    return X, y, user_ids


# --------- 3. Carga de modelo y umbral ----------------------------------------
def load_model_and_threshold():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No se encontró el modelo: {MODEL_PATH}")
    if not THRESH_PATH.exists():
        raise FileNotFoundError(f"No se encontró el umbral: {THRESH_PATH}")
    model = pickle.load(open(MODEL_PATH, 'rb'))
    if not isinstance(model, xgb.XGBClassifier):
        raise TypeError(f"Modelo no es XGBClassifier: {type(model)}")
    threshold = float(open(THRESH_PATH).read().strip())
    return model, threshold

def predict(model, threshold, X):
    """Genera predicciones usando el modelo pre-entrenado XGBoost"""
    # Ya no necesitamos reindexar porque hemos creado exactamente las columnas que el modelo espera
    # en la función transform. Solo verificamos que los tipos sean correctos.
    
    # Asegurar que todos los datos son numéricos
    for col in X.columns:
        if X[col].dtype not in ['int64', 'float64', 'bool']:
            logging.warning(f"Convirtiendo columna {col} de tipo {X[col].dtype} a float64")
            X[col] = X[col].astype(float)
            
    # Verificación final de forma de datos
    logging.info(f"Generando predicciones con {X.shape[0]} filas y {X.shape[1]} columnas")

    # Generar probabilidades y etiquetas
    proba = model.predict_proba(X)[:,1]
    return proba, (proba >= threshold).astype(int)


# --------- 4. Orquestador -----------------------------------------------------
def main():
    logging.info("Iniciando proceso end-to-end")

    demog = _get_df('demographics')
    prod  = _get_df('products')
    tx    = _get_df('transactions')
    logging.info(f"Datos obtenidos: {len(demog)} clientes, {len(prod)} productos, {len(tx)} transacciones")

    X, y, users = transform(demog, prod, tx)
    logging.info(f"Feature engineering completado. Dataset shape: {X.shape}")

    model, thr = load_model_and_threshold()
    logging.info(f"Umbral de clasificación: {thr:.4f}")

    t0, t0b = predict(model, thr, X)

    # Ajustar longitudes si hiciera falta
    n = min(len(users), len(t0))
    users, t0, t0b = users[:n], t0[:n], t0b[:n]

    df = pd.DataFrame({
        'user_id':   users,
        't0':        np.round(t0, 4),
        't0b':       t0b,
        't1':        np.zeros(n),
        'timestamp': [datetime.now().isoformat()] * n
    })

    df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"Resultados guardados en {OUTPUT_FILE}")

    # Opcional: envío a la API
    if POST_RESULTS and len(df) > 0:
        _post_results(df)

    print("\nResultados de la predicción:")
    print(df.head())


if __name__ == '__main__':
    main()