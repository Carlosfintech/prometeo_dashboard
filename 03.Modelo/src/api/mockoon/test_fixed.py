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
    logging.info("Aplicando feature engineering...")
    # Target + user_ids
    insurance_users = prod.loc[prod['product_type'] == 'insurance', 'user_id']
    demog['insurance'] = demog['user_id'].isin(insurance_users).astype(int)
    y = demog['insurance'].values
    user_ids = demog['user_id'].values

    # 2a) DEMOGRAPHICS – age_range_sturges
    breaks = np.linspace(18, 70, 9)
    labels = ["18–24","25–31","32–38","39–45","46–52","53–59","60–66","67–70"]
    demog['age_range_sturges'] = pd.cut(
        demog['age'], bins=breaks, labels=labels,
        right=True, include_lowest=True
    ).astype('category')

    # 2b) PRODUCTS – flags, fechas y métricas
    prod['product_type'] = prod['product_type'].replace('investment_account','investment')
    flag_cols = ['checking_account','savings_account','credit_card','insurance','investment']

    pv = prod.pivot_table(
        index='user_id', columns='product_type',
        values='contract_date', aggfunc='count', fill_value=0
    )
    for f in flag_cols:
        pv[f] = (pv.get(f, 0) > 0)
    pv = pv[flag_cols].reset_index().astype({f: 'bool' for f in flag_cols})

    ps = prod.sort_values(['user_id','contract_date'])
    first = ps.groupby('user_id').first().reset_index().rename(
        columns={'product_type':'primer_producto','contract_date':'fecha_primer_producto'}
    )
    sec_rows = []
    for uid, g in ps.groupby('user_id'):
        if len(g) >= 2:
            sec = g.iloc[1].rename({'product_type':'segundo_producto','contract_date':'fecha_segundo_producto'})
            sec_rows.append(sec)
    if sec_rows:
        sec = pd.DataFrame(sec_rows)[['user_id','segundo_producto','fecha_segundo_producto']]
    else:
        sec = pd.DataFrame(columns=['user_id','segundo_producto','fecha_segundo_producto'])

    prod_agg = first.merge(sec, on='user_id', how='left') \
                    .merge(pv,   on='user_id', how='left')
    prod_agg['fecha_segundo_producto'] = prod_agg['fecha_segundo_producto'].fillna(pd.Timestamp('1900-01-01'))
    prod_agg['dias_entre_productos'] = (
        (prod_agg['fecha_segundo_producto'] - prod_agg['fecha_primer_producto'])
    ).dt.days.fillna(0).astype(int)
    prod_agg['antiguedad_cliente'] = (
        REFERENCE_DT - prod_agg['fecha_primer_producto']
    ).dt.days.astype(int)
    prod_agg['numero_productos'] = prod_agg[flag_cols].sum(axis=1).astype(int)

    def combo(r):
        act = [c for c in flag_cols if r[c]]
        if not act: return 'sin_productos'
        if len(act) == 1: return act[0]
        if len(act) == 2: return ' + '.join(sorted(act))
        return 'multi_producto'

    prod_agg['combinacion_productos'] = prod_agg.apply(combo, axis=1).astype('category')

    # 2c) TRANSACTIONS – estadísticas por usuario
    cat_counts = tx.pivot_table(
        index='user_id', columns='merchant_category',
        values='transaction_id', aggfunc='count', fill_value=0
    ).add_suffix('_count').reset_index()
    tx_basic = tx.groupby('user_id').agg(
        total_transacciones        = ('transaction_id','count'),
        monto_promedio_transaccion  = ('amount','mean'),
        total_spend                 = ('amount','sum'),
        n_meses_activos             = ('date', lambda s: s.dt.to_period('M').nunique()),
        recencia_transaccion        = ('date', lambda s: (REFERENCE_DT - s.max()).days)
    ).reset_index()

    cnt_cols = [c for c in cat_counts.columns if c.endswith('_count')]
    idx = cat_counts[cnt_cols].values.argmax(axis=1)
    names = [c.replace('_count','') for c in cnt_cols]
    cat_counts['categoria_favorita'] = [names[i] for i in idx]

    sp_by_cat = tx.pivot_table(
        index='user_id', columns='merchant_category',
        values='amount', aggfunc='sum', fill_value=0
    )
    fav_idx = sp_by_cat.values.argmax(axis=1)
    sp_fav = np.take_along_axis(sp_by_cat.values, fav_idx[:,None], axis=1).squeeze()

    tx_money = pd.DataFrame({
        'user_id': sp_by_cat.index,
        'categoria_favorita_monto': [sp_by_cat.columns[i] for i in fav_idx],
        'total_spend_fav'         : sp_fav
    })
    hhi = ((sp_by_cat.div(sp_by_cat.sum(axis=1), axis=0))**2).sum(axis=1)
    tx_money['hhi'] = hhi.values

    month = tx.copy()
    month['mes'] = month['date'].dt.to_period('M').dt.to_timestamp()
    ma = month.groupby(['user_id','mes']).agg(
        monto_mes         = ('amount','sum'),
        transacciones_mes = ('transaction_id','count')
    ).reset_index()
    best_t = ma.loc[ma.groupby('user_id').transacciones_mes.idxmax()][['user_id','mes']].rename(columns={'mes':'mes_mas_compras'})
    best_a = ma.loc[ma.groupby('user_id').monto_mes.idxmax()][['user_id','mes']].rename(columns={'mes':'mes_mayor_monto'})
    diffs = ma.sort_values(['user_id','mes']).groupby('user_id')['monto_mes'].diff().fillna(0)
    pct   = ma.sort_values(['user_id','mes']).groupby('user_id')['monto_mes'].pct_change().fillna(0)
    diffs_df = pd.DataFrame({
        'user_id': ma.user_id.unique(),
        'variacion_mensual_promedio'     : diffs.groupby(ma.user_id).mean().values,
        'variacion_mensual_promedio_pct' : pct.groupby(ma.user_id).mean().values
    })

    tx_full = tx_basic.merge(cat_counts, on='user_id', how='left') \
                     .merge(tx_money,  on='user_id', how='left') \
                     .merge(best_t,    on='user_id', how='left') \
                     .merge(best_a,    on='user_id', how='left') \
                     .merge(diffs_df,  on='user_id', how='left')
    tx_full['share_fav'] = tx_full['total_spend_fav'] / tx_full['total_spend']
    del month, ma, diffs, pct; gc.collect()

    # 5) Dataset final con left merges
    df = demog.merge(prod_agg, on='user_id', how='left') \
              .merge(tx_full,  on='user_id', how='left')
    
    # Eliminar irrelevantes
    drop_cols = ['fecha_segundo_producto_ts','total_spend','monto_promedio_transaccion',
                 'hhi','share_fav','total_transacciones','categoria_favorita','insurance']
    df.drop(columns=[c for c in drop_cols if c in df], inplace=True)
    
    # Fechas → ts - asegurarnos que los nombres sean exactamente como los espera el modelo
    for c in ['fecha_primer_producto','fecha_segundo_producto','mes_mas_compras','mes_mayor_monto']:
        if c in df:
            df[f'{c}_ts'] = df[c].astype(int)//10**9
            df.drop(columns=c, inplace=True)
    
    # Manejar duplicados en columnas después del merge
    for col in df.columns:
        if '.x' in col or '.y' in col:
            # Eliminar sufijo para columnas con .x o renombrar adecuadamente
            base_col = col.split('.')[0]
            if base_col + '.x' in df.columns and base_col + '.y' in df.columns:
                # Mantener la versión .x y eliminar la .y
                df[base_col] = df[base_col + '.x']
                df.drop(columns=[base_col + '.x', base_col + '.y'], inplace=True)
            elif base_col + '.x' in df.columns:
                df[base_col] = df[base_col + '.x']
                df.drop(columns=[base_col + '.x'], inplace=True)
            elif base_col + '.y' in df.columns:
                df[base_col] = df[base_col + '.y']
                df.drop(columns=[base_col + '.y'], inplace=True)
    
    # Crear columna "transacciones_promedio_mensual" si no existe
    if 'transacciones_promedio_mensual' not in df.columns and 'n_meses_activos' in df.columns and 'total_transacciones' in df.columns:
        df['transacciones_promedio_mensual'] = df['total_transacciones'] / df['n_meses_activos'].replace(0, 1)
    
    # Verificación final de columnas esperadas según Pipeline_test2.csv
    expected_columns = [
        'user_id', 'age', 'income_range', 'risk_profile', 'occupation', 'age_range_sturges',
        'primer_producto', 'segundo_producto', 'checking_account', 'credit_card', 'insurance',
        'investment', 'savings_account', 'dias_entre_productos', 'antiguedad_cliente',
        'numero_productos', 'n_meses_activos', 'recencia_transaccion', 'entertainment_count',
        'food_count', 'health_count', 'shopping_count', 'supermarket_count', 'transport_count',
        'travel_count', 'categoria_favorita_monto', 'total_spend_fav', 'variacion_mensual_promedio',
        'variacion_mensual_promedio_pct', 'fecha_primer_producto_ts', 'fecha_segundo_producto_ts',
        'mes_mas_compras_ts', 'mes_mayor_monto_ts'
    ]
    
    # Verificar y corregir columnas faltantes
    for col in expected_columns:
        if col not in df.columns:
            logging.warning(f"Columna esperada {col} no existe - añadiendo con valor cero o valores por defecto")
            df[col] = 0
            
            # Manejo específico para columnas categóricas
            if col in ['primer_producto', 'segundo_producto', 'age_range_sturges', 'categoria_favorita_monto']:
                df[col] = df[col].astype(str)
    
    # Rellenar valores nulos en columnas booleanas
    bool_cols = ['checking_account', 'credit_card', 'insurance', 'investment', 'savings_account']
    for b in bool_cols:
        if b in df.columns:
            df[b] = df[b].fillna(False).astype(int)
    
    # Rellenar valores nulos en columnas numéricas
    for col in ['dias_entre_productos', 'variacion_mensual_promedio', 'variacion_mensual_promedio_pct']:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    # Convertir columnas categóricas a numéricas para XGBoost
    cat_cols = ['income_range', 'risk_profile', 'occupation', 'age_range_sturges', 
               'primer_producto', 'segundo_producto', 'categoria_favorita_monto']
    
    for col in cat_cols:
        if col in df.columns:
            if df[col].dtype == 'category':
                df[col] = df[col].astype(str)
            df[col] = df[col].fillna('unknown')
            # Usamos un simple mapeo numérico para las categorías
            unique_values = df[col].unique()
            value_map = {val: i for i, val in enumerate(unique_values)}
            df[col] = df[col].map(value_map).astype(int)
            logging.info(f"Columna categórica {col} convertida a tipo numérico.")
    
    # Agregar columnas específicas con sufijo .x requeridas por el modelo
    # Estas son columnas que el modelo espera debido a cómo fue entrenado
    needed_x_columns = [
        'mes_mas_compras.x_ts', 
        'variacion_mensual_promedio.x', 
        'mes_mayor_monto.x_ts', 
        'transacciones_promedio_mensual.x', 
        'variacion_mensual_promedio_pct.x'
    ]
    
    for col in needed_x_columns:
        base_col = col.split('.x')[0]
        if col not in df.columns and base_col in df.columns:
            df[col] = df[base_col]
            logging.info(f"Creada columna {col} usando valores de {base_col}")
        elif col not in df.columns:
            df[col] = 0
            logging.info(f"Creada columna {col} con valores cero")
    
    # Extraer solo las columnas que sabemos que el modelo espera
    # Obtenemos la lista exacta de columnas desde el modelo pre-entrenado
    try:
        with open(MODEL_PATH, 'rb') as f:
            temp_model = pickle.load(f)
        model_columns = temp_model.feature_names_in_
        
        # Crear las columnas faltantes que el modelo espera
        for col in model_columns:
            if col not in df.columns:
                logging.warning(f"Columna requerida por el modelo {col} no existe - creando con ceros")
                df[col] = 0
                
        # X final - solo incluir las columnas que el modelo espera en el mismo orden
        X = df[model_columns].copy()
        logging.info(f"Dataset ajustado para coincidir exactamente con las {len(model_columns)} columnas que el modelo espera")
    except Exception as e:
        logging.error(f"Error al obtener las columnas del modelo: {e}. Usando todas las columnas disponibles.")
        X = df.copy()
    
    # Guardar el DataFrame final para verificación
    X_with_ids = X.copy()
    X_with_ids.to_csv("model_input_verification.csv", index=False)
    logging.info(f"DataFrame para verificación guardado en model_input_verification.csv con shape {X.shape}")
    
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