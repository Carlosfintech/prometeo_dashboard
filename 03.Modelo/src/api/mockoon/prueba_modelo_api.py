#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test end‑to‑end: descarga datos desde Mockoon, hace feature‑engineering,
predice con el modelo XGBoost y guarda results.csv
"""

import pandas as pd, numpy as np, requests, pickle, gc, logging, warnings, json
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
import sys, os
from io import StringIO  # Añadido para StringIO

# Agregar el directorio src al path para importar módulos de features
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src.features.pipeline_featureengineering_func import generate_features, run_pipeline

# --------- CONFIG ------------------------------------------------------------
BASE_URL = "http://localhost:3002"  # Mockoon (puerto 3002 según mockoon_config_new.json)
# Definir la ruta base del proyecto
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
# Definir la ruta explícita a los modelos
MODELS_DIR = BASE_DIR / "03.Modelo" / "models"
MODEL_PATH = MODELS_DIR / "xgb_model.pkl"
THRESH_PATH = MODELS_DIR / "xgb_threshold.txt"
REFERENCE_DT = pd.Timestamp("2024-01-01")
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s ▶  %(message)s")

# --------- 1. Descarga tablas -------------------------------------------------
# Función para cargar CSV desde Mockoon (basada en prueba_api.py)
def get_mock_csv(endpoint):
    """
    Obtiene datos en formato CSV desde un endpoint de Mockoon y los convierte a DataFrame.
    
    Args:
        endpoint (str): Ruta del endpoint, por ejemplo "/demographics"
        
    Returns:
        pandas.DataFrame: DataFrame con los datos obtenidos
    """
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    
    if response.status_code == 200:
        logging.info(f"✅ {endpoint} cargado correctamente")
        return pd.read_csv(StringIO(response.text))
    else:
        logging.error(f"❌ Error al cargar {endpoint}: {response.status_code}")
        return pd.DataFrame()

def fetch_tables():
    """
    Descarga todas las tablas necesarias desde la API Mockoon
    
    Returns:
        tuple: (demog, prod, tx) - DataFrames con datos demográficos, productos y transacciones
    """
    logging.info("Descargando CSV desde Mockoon …")
    demog = get_mock_csv("/demographics")
    prod = get_mock_csv("/products")
    tx = get_mock_csv("/transactions")
    
    # Verificar que se obtuvieron datos
    if demog.empty or prod.empty or tx.empty:
        logging.warning("⚠️ Uno o más DataFrames están vacíos después de la descarga")
    
    # Mostrar un vistazo de los datos descargados
    print("\n🔍 Datos demográficos")
    print(demog.head())

    print("\n🔍 Productos contratados")
    print(prod.head())

    print("\n🔍 Transacciones")
    print(tx.head())
    
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
        df = df.drop(columns=["insurance"])
        logging.info("Columna 'insurance' eliminada explícitamente para predicción")
    
    # Verificar si hay columnas que no deberían ir al modelo y eliminarlas
    if "user_id" in df.columns:
        X = df.drop(columns=["user_id"])
    else:
        X = df
    
    logging.info(f"Dataset preparado para modelo: {X.shape[0]} filas, {X.shape[1]} columnas")
    
    return X, y, ids

# --------- 3. Predicción ------------------------------------------------------
def load_model_and_threshold():
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

# --------- 4. POST resultados -------------------------------------------------
def post_results(results_df):
    """
    Envía los resultados al endpoint /results de Mockoon via POST
    
    Args:
        results_df (pandas.DataFrame): DataFrame con los resultados
        
    Returns:
        bool: True si el envío fue exitoso, False en caso contrario
    """
    url = f"{BASE_URL}/results"
    
    # Convertir DataFrame a formato JSON
    results_json = results_df.to_json(orient='records')
    
    # Configurar headers
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        # Realizar la petición POST
        response = requests.post(url, data=results_json, headers=headers)
        
        # Verificar respuesta
        if response.status_code == 200:
            logging.info(f"✅ Resultados enviados correctamente a {url}")
            logging.info(f"Respuesta: {response.json()}")
            return True
        else:
            logging.error(f"❌ Error al enviar resultados: {response.status_code}")
            logging.error(f"Respuesta: {response.text}")
            return False
    
    except Exception as e:
        logging.error(f"❌ Excepción al enviar resultados: {str(e)}")
        return False

# --------- 5. Orquestador -----------------------------------------------------
def main():
    """
    Función principal que orquesta el flujo de trabajo.
    """
    # Verificar rutas de modelo
    global MODEL_PATH, THRESH_PATH
    
    if not os.path.exists(MODEL_PATH):
        logging.warning(f"⚠️ Archivo de modelo no encontrado en: {MODEL_PATH}")
        alt_path = BASE_DIR / "models" / "xgb_model.pkl"
        if os.path.exists(alt_path):
            logging.info(f"✅ Modelo encontrado en ruta alternativa: {alt_path}")
            MODEL_PATH = alt_path
            THRESH_PATH = BASE_DIR / "models" / "xgb_threshold.txt"
    
    # Obtener datos desde Mockoon
    demog, prod, tx = fetch_tables()
    
    # Aplicar el pipeline de feature engineering
    X, y, ids = transform(demog, prod, tx)
    
    try:
        # Cargar modelo y hacer predicciones
        model, thr = load_model_and_threshold()
        t0, t0b = predict(model, thr, X)
        
        # Crear DataFrame con resultados
        out = pd.DataFrame({
            "user_id": ids,
            "t0": t0.round(4),  # Probabilidad
            "t0b": t0b,         # Etiqueta binaria (0/1)
            "t1": 0             # Placeholder para futuras predicciones
        })
        
        # Guardar resultados en CSV
        out.to_csv("results.csv", index=False)
        logging.info(f"results.csv guardado ({len(out)} filas)")
        print(out.head())  # muestra un vistazo rápido
        
        # Enviar resultados a la API Mockoon
        post_success = post_results(out)
        if post_success:
            logging.info("Proceso completado con éxito.")
        else:
            logging.warning("El proceso se completó pero hubo problemas al enviar los resultados.")
    
    except Exception as e:
        logging.error(f"Error en la predicción: {e}")
        # Guardar datos para depuración
        X.to_csv("error_features.csv")
        logging.info("Características guardadas en error_features.csv para análisis")
        raise e

if __name__ == "__main__":
    main()