#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test end‑to‑end: descarga datos desde Mockoon, hace feature‑engineering,
predice con el modelo XGBoost y guarda results.csv

Este script realiza las siguientes acciones:
1. Obtiene datos demográficos, productos y transacciones desde una API Mockoon
2. Aplica transformaciones y feature engineering
3. Carga un modelo pre-entrenado y predice la probabilidad de contratación de seguro
4. Guarda los resultados en un archivo CSV
5. Opcionalmente publica los resultados a una API

Uso:
    python prometeo_single_test.py
"""

import pandas as pd
import numpy as np
import requests
import pickle
import gc
import logging
import warnings
import json
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime
import xgboost as xgb

# ------------------------------------------------------------------
# Configuración global
# ------------------------------------------------------------------
BASE_URL = "http://localhost:3001"
POST_RESULTS = True
OUTPUT_FILE = "results.csv"

# Rutas de modelo y umbral
MODEL_PATH = Path("../../../../03.Modelo/models/xgb_model.pkl")
THRESH_PATH = Path("../../../../03.Modelo/models/xgb_threshold.txt")
ENCODERS_PATH = Path("../../../../03.Modelo/models/label_encoders.pkl")

# Fecha de referencia (debe coincidir con pipeline_featureengineering.py)
REFERENCE_DT = pd.Timestamp("2024-01-01")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s ▶  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# --------- 1. Funciones para obtener y procesar datos --------------------------
def _get_df(endpoint: str) -> pd.DataFrame:
    """Obtiene datos de un endpoint de la API y los convierte a DataFrame"""
    try:
        logging.info(f"Obteniendo datos desde {endpoint}...")
        r = requests.get(f"{BASE_URL}/{endpoint}")
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data)
        
        # Procesar fechas automáticamente
        for col in df.columns:
            if col.endswith('_date') or col == 'date':
                df[col] = pd.to_datetime(df[col])
                
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener datos de {endpoint}: {str(e)}")
        raise

def _post_results(results: pd.DataFrame) -> None:
    """
    Envía los resultados a la API.
    
    Args:
        results: DataFrame con las columnas user_id, t0, t0b, t1, timestamp
    """
    if not POST_RESULTS:
        logging.info("POST_RESULTS está desactivado. No se enviarán resultados.")
        return
        
    try:
        # Verificar columnas requeridas
        required_cols = ['user_id', 't0', 't0b', 't1', 'timestamp']
        missing_cols = set(required_cols) - set(results.columns)
        if missing_cols:
            raise ValueError(f"Faltan columnas requeridas: {missing_cols}")
        
        # Verificar tipos de datos
        if not results['t0'].between(0, 1).all():
            raise ValueError("Columna t0 debe estar entre 0 y 1")
        if not results['t0b'].isin([0, 1]).all():
            raise ValueError("Columna t0b debe ser 0 o 1")
        if not results['t1'].isin([0, 1]).all():
            raise ValueError("Columna t1 debe ser 0 o 1")
            
        # Preparar payload
        payload = results[required_cols].to_dict(orient='records')
        
        # Enviar resultados
        logging.info(f"\nEnviando {len(payload)} resultados a {BASE_URL}/results")
        r = requests.post(f"{BASE_URL}/results", json=payload)
        r.raise_for_status()
        
        # Verificar respuesta
        if r.status_code == 200:
            logging.info("Resultados enviados exitosamente")
            response = r.json()
            if 'processed' in response:
                logging.info(f"Registros procesados: {response['processed']}")
        else:
            logging.warning(f"Respuesta inesperada: {r.status_code}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al enviar resultados: {str(e)}")
        if hasattr(e.response, 'text'):
            logging.error(f"Respuesta del servidor: {e.response.text}")
        raise
    except ValueError as e:
        logging.error(f"Error en la validación de datos: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        raise

def fetch_tables():
    """Obtiene los datos desde la API de Mockoon"""
    logging.info("Descargando datos desde Mockoon...")
    
    # Definir estructura esperada de los datos
    required_columns = {
        'demographics': {
            'columns': ['user_id', 'age', 'income_range', 'risk_profile', 'occupation'],
            'dtypes': {
                'user_id': 'object',
                'age': 'int64',
                'income_range': 'object',
                'risk_profile': 'object',
                'occupation': 'object'
            }
        },
        'products': {
            'columns': ['user_id', 'product_type', 'contract_date'],
            'dtypes': {
                'user_id': 'object',
                'product_type': 'object',
                'contract_date': 'datetime64[ns]'
            }
        },
        'transactions': {
            'columns': ['transaction_id', 'user_id', 'date', 'amount', 'merchant_category'],
            'dtypes': {
                'transaction_id': 'object',
                'user_id': 'object',
                'date': 'datetime64[ns]',
                'amount': 'float64',
                'merchant_category': 'object'
            }
        }
    }

    try:
        # Obtener datos demográficos
        logging.info("Obteniendo datos desde demographics...")
        r = requests.get(f"{BASE_URL}/demographics")
        r.raise_for_status()
        demog = pd.DataFrame(r.json())
        
        # Verificar y convertir tipos de datos
        for col, dtype in required_columns['demographics']['dtypes'].items():
            if col not in demog.columns:
                raise ValueError(f"Columna {col} no encontrada en demographics")
            if dtype == 'datetime64[ns]':
                demog[col] = pd.to_datetime(demog[col])
            else:
                demog[col] = demog[col].astype(dtype)

        # Obtener datos de productos
        logging.info("Obteniendo datos desde products...")
        r = requests.get(f"{BASE_URL}/products")
        r.raise_for_status()
        prod = pd.DataFrame(r.json())
        
        # Verificar y convertir tipos de datos
        for col, dtype in required_columns['products']['dtypes'].items():
            if col not in prod.columns:
                raise ValueError(f"Columna {col} no encontrada en products")
            if dtype == 'datetime64[ns]':
                prod[col] = pd.to_datetime(prod[col])
            else:
                prod[col] = prod[col].astype(dtype)

        # Obtener datos de transacciones
        logging.info("Obteniendo datos desde transactions...")
        r = requests.get(f"{BASE_URL}/transactions")
        r.raise_for_status()
        tx = pd.DataFrame(r.json())
        
        # Verificar y convertir tipos de datos
        for col, dtype in required_columns['transactions']['dtypes'].items():
            if col not in tx.columns:
                raise ValueError(f"Columna {col} no encontrada en transactions")
            if dtype == 'datetime64[ns]':
                tx[col] = pd.to_datetime(tx[col])
            else:
                tx[col] = tx[col].astype(dtype)

        # Verificar integridad referencial
        all_users = set(demog['user_id'])
        prod_users = set(prod['user_id'])
        tx_users = set(tx['user_id'])
        
        if not prod_users.issubset(all_users):
            missing = prod_users - all_users
            raise ValueError(f"Usuarios en products no encontrados en demographics: {missing}")
        
        if not tx_users.issubset(all_users):
            missing = tx_users - all_users
            raise ValueError(f"Usuarios en transactions no encontrados en demographics: {missing}")

        # Crear columna insurance basada en productos
        insurance_users = prod[prod['product_type'] == 'insurance']['user_id'].unique()
        demog['insurance'] = demog['user_id'].isin(insurance_users)

        logging.info(f"Datos obtenidos: {len(demog)} clientes, {len(prod)} productos, {len(tx)} transacciones")
        
        # Verificar valores válidos
        logging.info("Verificando rangos de valores...")
        if demog['age'].min() < 18 or demog['age'].max() > 100:
            raise ValueError(f"Edades fuera de rango: min={demog['age'].min()}, max={demog['age'].max()}")
        
        if tx['amount'].min() < 0:
            raise ValueError(f"Montos negativos encontrados: min={tx['amount'].min()}")
        
        return demog, prod, tx

    except requests.exceptions.RequestException as e:
        logging.error(f"Error al obtener datos de la API: {str(e)}")
        raise
    except ValueError as e:
        logging.error(f"Error en la validación de datos: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Error inesperado: {str(e)}")
        raise

# --------- 2. Feature‑engineering  -------------------------------------------
def transform(demog, prod, tx):
    """
    Performs complete feature engineering following pipeline_featureengineering.py exactly
    """
    logging.info("Aplicando feature engineering...")
    
    # Save target and user_ids before any transformations
    y = demog['insurance'].values
    user_ids = demog['user_id'].values

    # Añadir income_range_num
    demog['income_range_num'] = (
        demog['income_range'].str.extract(r'(\d+)').astype(float)
    )
    
    # ------------------------------------------------------------------
    # 2. DEMOGRAPHICS – age_range_sturges
    # ------------------------------------------------------------------
    breaks = np.linspace(18, 70, 9)
    labels = ["18–24", "25–31", "32–38", "39–45",
              "46–52", "53–59", "60–66", "67–70"]

    demog["age_range_sturges"] = pd.cut(
        demog["age"],
        bins=breaks,
        labels=labels,
        right=True,
        include_lowest=True
    )
    demog["age_range_sturges"] = demog["age_range_sturges"].astype('category')

    # ------------------------------------------------------------------
    # 3. PRODUCTS – flags, fechas y métricas
    # ------------------------------------------------------------------
    # Más eficiente que crear una copia completa
    prod["product_type"] = prod["product_type"].replace("investment_account", "investment")

    # Crea flags de producto de manera vectorizada
    flag_cols = ["checking_account", "savings_account", "credit_card", 
                 "insurance", "investment"]

    # Preprocesamiento más eficiente de productos
    prod_pivoted = prod.pivot_table(
        index="user_id", 
        columns="product_type", 
        values="contract_date", 
        aggfunc="count",
        fill_value=0
    )

    # Convertir a indicadores binarios de manera más eficiente
    for col in flag_cols:
        if col in prod_pivoted.columns:
            prod_pivoted[col] = (prod_pivoted[col] > 0).astype(bool)
        else:
            prod_pivoted[col] = False

    prod_pivoted.reset_index(inplace=True)

    # Obtener primer y segundo producto de forma más eficiente
    prod_sorted = prod.sort_values(["user_id", "contract_date"])
    first_products = prod_sorted.groupby("user_id").first().reset_index()
    first_products.rename(columns={
        "product_type": "primer_producto", 
        "contract_date": "fecha_primer_producto"
    }, inplace=True)

    # Obtener el segundo producto de forma más eficiente
    prod_with_rank = prod_sorted.assign(
        rank=prod_sorted.groupby("user_id").cumcount() + 1
    )
    second_products = prod_with_rank[prod_with_rank["rank"] == 2].drop(columns=["rank"])
    second_products.rename(columns={
        "product_type": "segundo_producto", 
        "contract_date": "fecha_segundo_producto"
    }, inplace=True)

    # Combinar todo
    prod_agg = first_products[["user_id", "primer_producto", "fecha_primer_producto"]].merge(
        second_products[["user_id", "segundo_producto", "fecha_segundo_producto"]], 
        on="user_id", how="left"
    )

    # Combinar con los flags
    prod_agg = prod_agg.merge(prod_pivoted, on="user_id", how="left")

    # Procesar fechas y calcular métricas
    prod_agg["fecha_segundo_producto"] = prod_agg["fecha_segundo_producto"].fillna(
        pd.Timestamp("1900-01-01")
    )

    # Vectorizado sin apply
    prod_agg["dias_entre_productos"] = (
        (prod_agg["fecha_segundo_producto"] - prod_agg["fecha_primer_producto"])
        .dt.days.fillna(0).astype('int32')
    )
    prod_agg["antiguedad_cliente"] = (
        (REFERENCE_DT - prod_agg["fecha_primer_producto"]).dt.days.astype('int32')
    )
    prod_agg["numero_productos"] = prod_agg[flag_cols].sum(axis=1).astype('int8')

    # Combinación de productos
    def _combo(row):
        activos = [c for c in flag_cols if row[c]]
        
        # Sin productos
        if not activos:
            return "sin_productos"
        
        # Un solo producto
        if len(activos) == 1:
            return activos[0]
        
        # Para dos productos, ordenamos para consistencia
        if len(activos) == 2:
            return " + ".join(sorted(activos))
        
        # Si hay más de 2 productos (caso no esperado), usar "multi_producto"
        return "multi_producto"

    # Usar procesamiento normal para esta operación
    prod_agg["combinacion_productos"] = prod_agg.apply(_combo, axis=1)

    # Mapeo completo para todas las combinaciones de dos productos
    mapeo_completo = {
        # Combinaciones con checking_account
        "checking_account + credit_card": "checking_account + credit_card",
        "checking_account + insurance": "checking_account + insurance",
        "checking_account + investment": "checking_account + investment",
        "checking_account + savings_account": "checking_account + savings_account",
        
        # Combinaciones con credit_card
        "credit_card + insurance": "credit_card + insurance",
        "credit_card + investment": "credit_card + investment",
        "credit_card + savings_account": "credit_card + savings_account",
        
        # Combinaciones con insurance
        "insurance + investment": "insurance + investment",
        "insurance + savings_account": "insurance + savings_account",
        
        # Combinación de investment y savings_account
        "investment + savings_account": "investment + savings_account"
    }

    # Aplicar mapeo a las combinaciones de dos productos
    def aplicar_mapeo_completo(x):
        # Si es una combinación de dos productos, aplicar el mapeo
        if "+" in x:
            return mapeo_completo.get(x, x)
        # Caso contrario, mantener el valor original
        return x

    prod_agg["combinacion_productos"] = prod_agg["combinacion_productos"].map(aplicar_mapeo_completo)
    prod_agg["combinacion_productos"] = prod_agg["combinacion_productos"].astype('category')

    # Liberar memoria
    del prod_sorted, first_products, second_products, prod_pivoted, prod_with_rank
    gc.collect() 

    # ------------------------------------------------------------------
    # 4. TRANSACTIONS – estadísticas por usuario
    # ------------------------------------------------------------------
    # Conteos por categoría usando pivot_table (más eficiente)
    cat_counts = tx.pivot_table(
        index="user_id",
        columns="merchant_category",
        values="transaction_id",
        aggfunc="count",
        fill_value=0
    ).add_suffix("_count").reset_index()

    # Calcular estadísticas básicas (vectorizado)
    tx_basic = (
        tx.groupby("user_id")
          .agg(
              total_transacciones        = ("transaction_id", "count"),
              monto_promedio_transaccion = ("amount", "mean"),
              total_spend                = ("amount", "sum"),
              n_meses_activos            = ("date", lambda s: s.dt.to_period("M").nunique()),
              recencia_transaccion       = ("date", lambda s: (REFERENCE_DT - s.max()).days)
          )
          .reset_index()
    )

    # Obtener categoría favorita de forma más eficiente
    cnt_cols = [c for c in cat_counts.columns if c.endswith("_count")]
    # Usar argmax() en lugar de idxmax() para mayor velocidad
    cat_counts["categoria_favorita"] = cat_counts[cnt_cols].values.argmax(axis=1)
    # Mapear índices a nombres de categorías
    cat_names = [c.replace("_count", "") for c in cnt_cols]
    cat_counts["categoria_favorita"] = cat_counts["categoria_favorita"].apply(
        lambda idx: cat_names[idx]
    )

    # Análisis de gastos por categoría vectorizado
    sp_by_cat = tx.pivot_table(
        index="user_id", 
        columns="merchant_category", 
        values="amount", 
        aggfunc="sum",
        fill_value=0
    )

    # Estas operaciones son más rápidas que usar idxmax con series
    fav_idx = sp_by_cat.values.argmax(axis=1)
    sp_fav = np.take_along_axis(sp_by_cat.values, fav_idx[:, np.newaxis], axis=1).squeeze()

    # Crear DataFrame con los resultados
    tx_money = pd.DataFrame({
        "user_id": sp_by_cat.index,
        "categoria_favorita_monto": [sp_by_cat.columns[i] for i in fav_idx],
        "total_spend_fav": sp_fav
    })

    # Calcular HHI de forma vectorizada
    row_sums = sp_by_cat.sum(axis=1)
    hhi = ((sp_by_cat.div(row_sums, axis=0))**2).sum(axis=1)
    tx_money["hhi"] = hhi.values

    # Análisis temporal por mes
    tx_month = tx.copy()
    tx_month["mes"] = tx_month["date"].dt.to_period("M").dt.to_timestamp()

    # Agrupación por mes (vectorizado)
    month_agg = tx_month.groupby(["user_id", "mes"]).agg(
        monto_mes=("amount", "sum"),
        transacciones_mes=("transaction_id", "count")
    ).reset_index()

    # Encontrar meses con más transacciones y mayor monto
    user_max_tx = month_agg.loc[month_agg.groupby("user_id")["transacciones_mes"].idxmax()]
    m_best = user_max_tx[["user_id", "mes"]].rename(columns={"mes": "mes_mas_compras"})

    user_max_amt = month_agg.loc[month_agg.groupby("user_id")["monto_mes"].idxmax()]
    m_best_amt = user_max_amt[["user_id", "mes"]].rename(columns={"mes": "mes_mayor_monto"})

    # Calcular diferencias entre meses
    month_agg = month_agg.sort_values(["user_id", "mes"])
    month_diffs = month_agg.groupby("user_id")["monto_mes"].diff().fillna(0)
    month_pcts = month_agg.groupby("user_id")["monto_mes"].pct_change().fillna(0)

    diffs = pd.DataFrame({
        "user_id": month_agg["user_id"].unique(),
        "variacion_mensual_promedio": month_diffs.groupby(month_agg["user_id"]).mean().values,
        "variacion_mensual_promedio_pct": month_pcts.groupby(month_agg["user_id"]).mean().values
    })

    # Combinar todos los resultados
    tx_full = (tx_basic
        .merge(cat_counts, on="user_id", how="left")
        .merge(tx_money,   on="user_id", how="left")
        .merge(m_best,     on="user_id", how="left")
        .merge(m_best_amt, on="user_id", how="left")
        .merge(diffs,      on="user_id", how="left")
    )

    tx_full["share_fav"] = tx_full["total_spend_fav"] / tx_full["total_spend"]
    tx_full["categoria_favorita_monto"] = tx_full["categoria_favorita_monto"].astype('category')

    # Liberar memoria
    del tx_month, month_agg, user_max_tx, user_max_amt, month_diffs, month_pcts
    gc.collect()

    # ------------------------------------------------------------------
    # 5. DATASET FINAL y transformaciones
    # ------------------------------------------------------------------
    df = (demog
          .merge(prod_agg, on="user_id", how="left")
          .merge(tx_full,  on="user_id", how="left"))

    # Variables a descartar (incluye user_id y fecha_segundo_producto_ts)
    drop_cols = [
        "fecha_segundo_producto_ts",
        "total_spend", "monto_promedio_transaccion", "monto_promedio_mensual",
        "hhi", "share_fav", "total_transacciones", "categoria_favorita",
        "insurance"  # Aseguramos que insurance se elimine si existe
    ]
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Fechas -> timestamp (vectorizado)
    date_cols = ["fecha_primer_producto", "fecha_segundo_producto",
                 "mes_mas_compras", "mes_mayor_monto"]
    for c in date_cols:
        if c in df.columns:
            df[f"{c}_ts"] = df[c].astype('int64') // 10**9  # Más eficiente que convertir a int
            df.drop(columns=c, inplace=True)

    # Imputaciones vectorizadas
    df["dias_entre_productos"] = df["dias_entre_productos"].fillna(0)
    df["variacion_mensual_promedio"] = df["variacion_mensual_promedio"].fillna(0)
    df["variacion_mensual_promedio_pct"] = df["variacion_mensual_promedio_pct"].fillna(0)

    # Escalado
    SCALER_PATH = Path("../../../../03.Modelo/models/std_scaler.pkl")
    try:
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
            logging.info("Scaler cargado desde archivo")
    except (FileNotFoundError, IOError):
        logging.warning(f"No se pudo cargar el scaler desde {SCALER_PATH}. Creando uno nuevo")
        scaler = StandardScaler()
        
    to_scale = [
        "age", "income_range_num", "dias_entre_productos", "antiguedad_cliente",
        "numero_productos", "recencia_transaccion",
        "variacion_mensual_promedio", "variacion_mensual_promedio_pct"
    ]
    present = [c for c in to_scale if c in df.columns]
    if present:
        # Usar transform si el scaler ya está entrenado, o fit_transform si es nuevo
        if hasattr(scaler, 'mean_') and scaler.mean_ is not None:
            df[present] = scaler.transform(df[present])
        else:
            df[present] = scaler.fit_transform(df[present])

    # Log1p (vectorizado)
    if "total_spend_fav" in df.columns:
        df["total_spend_fav"] = np.log1p(df["total_spend_fav"])

    # Label encoding (vectorizado)
    cat_vars = [
        "income_range", "risk_profile", "occupation", "age_range_sturges",
        "primer_producto", "segundo_producto", "combinacion_productos",
        "categoria_favorita_monto"
    ]

    # Cargar encoders entrenados
    try:
        with open(ENCODERS_PATH, "rb") as f:
            encoders = pickle.load(f)
            logging.info("Encoders cargados desde archivo")
    except (FileNotFoundError, IOError):
        logging.warning(f"No se pudo cargar los encoders desde {ENCODERS_PATH}. Usando LabelEncoder básico")
        encoders = {}

    for c in cat_vars:
        if c in df.columns:
            df[c] = df[c].astype(str).fillna("unknown")
            if c in encoders:
                df[c] = encoders[c].transform(df[c])
            else:
                logging.warning(f"Encoder para {c} no encontrado. Usando nuevo LabelEncoder")
                le = LabelEncoder()
                df[c] = le.fit_transform(df[c])

    df.drop(columns=["combinacion_productos"], errors="ignore", inplace=True)

    # Before final transformations, ensure all category counts exist
    required_categories = ['food', 'health', 'shopping', 'transport', 'entertainment', 'other', 'travel', 'supermarket']
    for cat in required_categories:
        count_col = f"{cat}_count"
        if count_col not in df.columns:
            df[count_col] = 0
    
    # Convert boolean columns to int, handling NaN values first
    bool_columns = ['checking_account', 'savings_account', 'credit_card', 'investment', 'insurance']
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].fillna(False)  # Fill NaN with False
            df[col] = df[col].astype(int)    # Convert to int
    
    # Drop unnecessary columns and return
    cols_to_drop = ['user_id', 'insurance'] + [c for c in date_cols if c in df.columns]
    X = df.drop(columns=cols_to_drop, errors='ignore')
    
    # Fill NaN values with 0 for numeric columns
    X = X.fillna(0)
    
    # Ensure all numeric columns are float
    for col in X.columns:
        if X[col].dtype != bool:  # Skip boolean columns
            X[col] = X[col].astype(float)
    
    logging.info(f"Feature engineering completado. Shape del dataset: {X.shape}")
    return X, y, user_ids

# --------- 3. Predicción ------------------------------------------------------
def load_model_and_threshold():
    """Carga el modelo XGBoost y el umbral desde los archivos"""
    try:
        # Verificar que los archivos existen
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"No se encontró el archivo del modelo: {MODEL_PATH}")
        if not THRESH_PATH.exists():
            raise FileNotFoundError(f"No se encontró el archivo del umbral: {THRESH_PATH}")
        
        # Cargar modelo
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        # Verificar que es un modelo XGBoost
        if not isinstance(model, xgb.XGBClassifier):
            raise TypeError(f"El modelo no es un XGBClassifier: {type(model)}")
        
        # Cargar umbral
        with open(THRESH_PATH, 'r') as f:
            threshold = float(f.read().strip())
        
        # Verificar umbral válido
        if not 0 <= threshold <= 1:
            raise ValueError(f"Umbral fuera de rango [0,1]: {threshold}")
        
        # Logging de información del modelo
        logging.info("\nInformación del modelo:")
        logging.info(f"- Tipo: {type(model).__name__}")
        logging.info(f"- Número de características: {len(model.feature_names_in_)}")
        logging.info(f"- Umbral de clasificación: {threshold:.4f}")
        
        return model, threshold
        
    except Exception as e:
        logging.error(f"Error al cargar el modelo o umbral: {str(e)}")
        raise

def predict(model, threshold, X):
    """Genera predicciones usando el modelo pre-entrenado"""
    logging.info(f"Generando predicciones para {X.shape[0]} registros...")
    try:
        # Verificar que X tenga las características necesarias
        expected_features = model.feature_names_in_
        current_features = set(X.columns)
        
        # Logging detallado de características
        logging.info("Verificación de características:")
        logging.info(f"- Características esperadas: {len(expected_features)}")
        logging.info(f"- Características actuales: {len(current_features)}")
        
        missing_features = set(expected_features) - current_features
        extra_features = current_features - set(expected_features)
        
        if missing_features:
            logging.warning(f"Creando características faltantes: {missing_features}")
            for feature in missing_features:
                X[feature] = 0
        
        if extra_features:
            logging.warning(f"Eliminando características extra: {extra_features}")
            X = X[expected_features]
        
        # Verificar tipos de datos
        for col in X.columns:
            if X[col].dtype not in ['int64', 'float64', 'bool']:
                logging.warning(f"Convirtiendo {col} de {X[col].dtype} a float64")
                X[col] = X[col].astype(float)
        
        # Generar predicciones
        proba = model.predict_proba(X)[:, 1]
        preds = (proba >= threshold).astype(int)
        
        # Logging detallado de resultados
        pos_count = sum(preds)
        logging.info("\nResultados de predicción:")
        logging.info(f"- Total registros: {len(preds)}")
        logging.info(f"- Predicciones positivas: {pos_count} ({pos_count/len(preds)*100:.1f}%)")
        logging.info(f"- Rango de probabilidades: [{proba.min():.4f}, {proba.max():.4f}]")
        logging.info(f"- Umbral usado: {threshold}")
        
        # Distribución de probabilidades
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        hist = np.histogram(proba, bins=bins)[0]
        for i in range(len(bins)-1):
            count = hist[i]
            pct = count/len(proba)*100
            logging.info(f"  {bins[i]:.1f}-{bins[i+1]:.1f}: {count} registros ({pct:.1f}%)")
        
        return proba, preds
        
    except Exception as e:
        logging.error(f"Error al generar predicciones: {str(e)}")
        logging.error(f"Shape de X: {X.shape}")
        logging.error(f"Columnas en X: {list(X.columns)}")
        logging.error(f"Tipos de datos: {X.dtypes.to_dict()}")
        raise

# --------- 4. Orquestador -----------------------------------------------------
def main():
    """Función principal que ejecuta todo el proceso end-to-end"""
    try:
        # 1. Obtener datos
        demog, prod, tx = fetch_tables()
        
        # 2. Transformar datos
        logging.info("Aplicando feature engineering...")
        df, y, user_ids = transform(demog, prod, tx)
        
        # Verificación de datos antes de predicción
        logging.info(f"Verificación de datos:")
        logging.info(f"- Shape de X: {df.shape}")
        logging.info(f"- Columnas numéricas: {df.select_dtypes(['int64', 'float64']).columns.tolist()}")
        logging.info(f"- Columnas categóricas: {df.select_dtypes(['object', 'category']).columns.tolist()}")
        logging.info(f"- Valores faltantes: {df.isnull().sum().sum()}")
        
        # 3. Cargar modelo y generar predicciones
        model, thr = load_model_and_threshold()
        t0, t0b = predict(model, thr, df)
        
        # 4. Generar resultados con join final
        timestamp = datetime.now().isoformat()
        results = pd.DataFrame({
            "user_id": user_ids,
            "t0": t0.round(4),        # Probabilidad predicha (continua)
            "t0b": t0b,               # Predicción binaria basada en umbral
            "t1": 0,                  # Placeholder para resultado real futuro
            "timestamp": timestamp    # Marca temporal
        })
        
        # Agregar información demográfica relevante
        results = results.merge(
            demog[['user_id', 'age', 'income_range', 'risk_profile']],
            on='user_id',
            how='left'
        )
        
        # Verificación de resultados
        logging.info("\nVerificación de resultados:")
        logging.info(f"- Total registros: {len(results)}")
        logging.info(f"- Predicciones positivas (t0b=1): {sum(results['t0b'])} ({sum(results['t0b'])/len(results)*100:.1f}%)")
        logging.info(f"- Rango de probabilidades: [{results['t0'].min():.3f}, {results['t0'].max():.3f}]")
        
        # Distribución por perfil de riesgo
        logging.info("\nDistribución por perfil de riesgo:")
        risk_dist = results.groupby('risk_profile')['t0b'].agg(['count', 'mean'])
        for idx, row in risk_dist.iterrows():
            pct_pos = row['mean'] * 100
            logging.info(f"- {idx}: {row['count']} clientes, {pct_pos:.1f}% positivos")
        
        # 5. Guardar resultados
        results_to_save = results[['user_id', 't0', 't0b', 't1', 'timestamp']]
        results_to_save.to_csv(OUTPUT_FILE, index=False)
        logging.info(f"\n{OUTPUT_FILE} guardado ({len(results)} filas)")
        
        # 6. Mostrar resultados y enviar a API
        print("\nResultados de la predicción:")
        print(results[['user_id', 't0', 't0b', 'risk_profile']].head())
        
        if POST_RESULTS:
            _post_results(results_to_save)
            
        return results
            
    except Exception as e:
        logging.error(f"Error en el proceso end-to-end: {str(e)}")
        logging.error("Detalles del error:", exc_info=True)
        raise

if __name__ == "__main__":
    main()
