#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test end‑to‑end: descarga datos desde Mockoon, hace feature‑engineering,
predice con el modelo XGBoost y guarda results.csv
"""

import pandas as pd, numpy as np, requests, pickle, gc, logging, warnings
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
import sys, os, json

# Agregar el directorio src al path para importar módulos de features
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.features.pipeline_featureengineering_func import generate_features

# --------- CONFIG ------------------------------------------------------------
BASE_URL     = "http://localhost:3002"     # Mockoon (puerto 3002 según mockoon_config_new.json)
# Definir la ruta base del proyecto
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
# Definir la ruta explícita a los modelos
MODELS_DIR   = BASE_DIR / "models"
MODEL_PATH   = MODELS_DIR / "xgb_model.pkl"
THRESH_PATH  = MODELS_DIR / "xgb_threshold.txt"

REFERENCE_DT = pd.Timestamp("2024-01-01")
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s ▶  %(message)s")

# Lista de características reales que espera el modelo (obtenidas del mensaje de error)
EXPECTED_FEATURES = [
    'age', 'income_range', 'risk_profile', 'occupation', 'age_range_sturges',
    'primer_producto', 'segundo_producto', 'dias_entre_productos', 'antiguedad_cliente',
    'checking_account', 'savings_account', 'credit_card', 'investment', 'numero_productos',
    'entertainment_count', 'food_count', 'health_count', 'shopping_count', 'supermarket_count',
    'transport_count', 'travel_count', 'transacciones_promedio_mensual',
    'variacion_mensual_promedio', 'variacion_mensual_promedio_pct', 'n_meses_activos',
    'recencia_transaccion', 'categoria_favorita_monto', 'total_spend_fav',
    'fecha_primer_producto_ts', 'mes_mas_compras_ts', 'mes_mayor_monto_ts'
]

# --------- 1. Descarga tablas -------------------------------------------------
def _get_df(endpoint: str) -> pd.DataFrame:
    r = requests.get(f"{BASE_URL}/{endpoint}")
    r.raise_for_status()
    return pd.DataFrame(r.json())

def fetch_tables():
    logging.info("Descargando CSV desde Mockoon …")
    demog = _get_df("demographics")
    prod  = _get_df("products")
    tx    = _get_df("transactions")
    return demog, prod, tx

# --------- 2. Feature‑engineering  -------------------------------------------
def transform(demographics: pd.DataFrame,
              products: pd.DataFrame,
              transactions: pd.DataFrame):
    """
    Utiliza la función generate_features del módulo pipeline_featureengineering_func
    para procesar los datos y generar características para el modelo.
    
    Returns:
    --------
    tuple: (X, y, ids)
        X: DataFrame con features procesadas
        y: Series con variable objetivo (placeholder, siempre 0)
        ids: Series con los IDs de usuarios
    """
    # Usar la función generate_features pasándole los DataFrames directamente
    df = generate_features(
        demographics_df=demographics,
        products_df=products,
        transactions_df=transactions,
        reference_date=REFERENCE_DT,
        output_file=None  # No guardar archivo
    )
    
    # Extraer user_id antes de eliminar la columna para el modelo
    ids = df["user_id"].copy()
    
    # Eliminar columna de ID para pasar al modelo
    y = pd.Series(0, index=df.index)  # Placeholder para la variable objetivo
    
    # Eliminar explícitamente la columna 'insurance' si existe
    if "insurance" in df.columns:
        logging.info("Eliminando columna 'insurance' (variable objetivo)")
        df = df.drop(columns=["insurance"])
    
    # Verificar si hay columnas que no deberían ir al modelo y eliminarlas
    if "user_id" in df.columns:
        X = df.drop(columns=["user_id"])
    else:
        X = df
    
    # Agregar columna transacciones_promedio_mensual si no existe
    if 'transacciones_promedio_mensual' not in X.columns:
        if 'total_transacciones' in X.columns and 'n_meses_activos' in X.columns:
            X['transacciones_promedio_mensual'] = X['total_transacciones'] / X['n_meses_activos'].replace(0, 1)
        else:
            X['transacciones_promedio_mensual'] = 0
    
    # Verificar si hay características faltantes o extras
    missing_features = [feat for feat in EXPECTED_FEATURES if feat not in X.columns]
    extra_features = [feat for feat in X.columns if feat not in EXPECTED_FEATURES]
    
    logging.info(f"Características faltantes: {missing_features}")
    logging.info(f"Características extra: {extra_features}")
    
    # Añadir características faltantes con valores predeterminados
    for feat in missing_features:
        if "count" in feat:
            X[feat] = 0
        elif "ts" in feat:
            X[feat] = 0
        else:
            X[feat] = 0
    
    # Eliminar características extra
    if extra_features:
        X = X.drop(columns=extra_features)
    
    # Reordenar columnas para que coincidan con el orden esperado por el modelo
    X = X[EXPECTED_FEATURES]
    
    logging.info(f"Dataset preparado para modelo: {X.shape[0]} filas, {X.shape[1]} columnas")
    logging.info(f"Verificación final de columnas: {all(X.columns == EXPECTED_FEATURES)}")
    
    return X, y, ids

# --------- 3. Predicción ------------------------------------------------------
def load_model_and_threshold():
    logging.info(f"Cargando modelo desde: {MODEL_PATH}")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    threshold = float(THRESH_PATH.read_text().strip())
    logging.info(f"Modelo y umbral cargados   (threshold={threshold:.4f})")
    return model, threshold

def predict(model, threshold, X):
    # 1) Comprobar que X tenga todas las columnas esperadas
    expected = set(model.feature_names_in_)
    got      = set(X.columns)
    missing_feats = expected - got
    extra_feats   = got - expected
    if missing_feats:
        logging.warning(f"Faltan estas features en el DataFrame: {missing_feats}")
    if extra_feats:
        logging.warning(f"Estas features extra están en el DataFrame: {extra_feats}")

    # 2) Reindex para alinear con el modelo
    X = X.reindex(columns=list(model.feature_names_in_), fill_value=0)

    # 3) Generar probabilidades y etiquetas
    proba = model.predict_proba(X)[:,1]
    return proba, (proba >= threshold).astype(int)

# --------- 4. Envío de resultados a la API ------------------------------------
def send_results(results_df):
    """
    Envía los resultados de las predicciones al endpoint /results de la API Mockoon.
    
    Args:
        results_df: DataFrame con los resultados de las predicciones
    
    Returns:
        response: Respuesta de la API
    """
    # Convertir el DataFrame a formato JSON
    results_json = results_df.to_json(orient='records')
    
    # Configurar los headers para la petición POST
    headers = {
        'Content-Type': 'application/json'
    }
    
    # Enviar la petición POST a la API
    logging.info(f"Enviando resultados a {BASE_URL}/results")
    
    try:
        response = requests.post(
            f"{BASE_URL}/results",
            data=results_json,
            headers=headers
        )
        response.raise_for_status()
        logging.info(f"Resultados enviados correctamente: {response.status_code}")
        logging.info(f"Respuesta: {response.text}")
        return response
    except Exception as e:
        logging.error(f"Error al enviar resultados: {e}")
        raise

# --------- 5. Orquestador -----------------------------------------------------
def main():
    demog, prod, tx = fetch_tables()
    X, y, ids       = transform(demog, prod, tx)
    model, thr      = load_model_and_threshold()
    
    try:
        t0, t0b = predict(model, thr, X)
        
        # DataFrame con resultados
        out = pd.DataFrame({"user_id": ids,
                            "t0":  t0.round(4),
                            "t0b": t0b,
                            "t1":  0})        # placeholder
        
        # Guardar resultados en CSV
        out.to_csv("results.csv", index=False)
        logging.info(f"results.csv guardado  ({len(out)} filas)")
        print(out.head())                     # muestra un vistazo rápido
        
        # Enviar resultados a la API
        response = send_results(out)
        logging.info("Proceso completo: datos descargados, procesados, predicciones realizadas y enviadas a la API")
        
    except Exception as e:
        logging.error(f"Error en la predicción: {e}")
        # Si falla con la validación de características, intentar sin validación
        logging.info("Intentando realizar predicción sin validación de características...")
        
        # Imprimir las columnas del DataFrame para depuración
        logging.info(f"Columnas en X: {list(X.columns)}")
        
        # Guardar los datos en caso de error para análisis
        X.to_csv("error_features.csv")
        logging.info("Características guardadas en error_features.csv para análisis")
        
        raise e

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s ▶  %(message)s")
    # Depuración
    print(f"Directorio de trabajo actual: {Path.cwd()}")
    print(f"Directorio base: {BASE_DIR}")
    print(f"Directorio de modelos: {MODELS_DIR}")
    print(f"Archivo de modelo: {MODEL_PATH}")
    
    # Verificar si el archivo existe
    if os.path.exists(MODEL_PATH):
        print(f"El archivo del modelo existe: {MODEL_PATH}")
    else:
        print(f"⚠️ El archivo del modelo NO existe: {MODEL_PATH}")
        # Buscar el archivo en el directorio 03.Modelo
        alt_path = BASE_DIR / "03.Modelo" / "models" / "xgb_model.pkl"
        if os.path.exists(alt_path):
            print(f"✅ Encontrado en: {alt_path}")
            MODEL_PATH = alt_path
            THRESH_PATH = BASE_DIR / "03.Modelo" / "models" / "xgb_threshold.txt"
    
    main()