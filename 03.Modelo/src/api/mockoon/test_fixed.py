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

    # 3) Dataset final con left merges
    df = demog.merge(prod_agg, on='user_id', how='left') \
              .merge(tx_full, on='user_id', how='left')

    # limpieza final
    drop_cols = [
        'fecha_segundo_producto_ts','total_spend','monto_promedio_transaccion',
        'hhi','share_fav','total_transacciones','categoria_favorita','insurance'
    ]
    df.drop(columns=[c for c in drop_cols if c in df], inplace=True)
    for c in ['fecha_primer_producto','fecha_segundo_producto','mes_mas_compras','mes_mayor_monto']:
        if c in df:
            df[f'{c}_ts'] = df[c].astype(int)//10**9
            df.drop(columns=c, inplace=True)
    df['dias_entre_productos']            = df['dias_entre_productos'].fillna(0)
    df['variacion_mensual_promedio']     = df['variacion_mensual_promedio'].fillna(0)
    df['variacion_mensual_promedio_pct'] = df['variacion_mensual_promedio_pct'].fillna(0)

    to_scale = ['age','dias_entre_productos','antiguedad_cliente','numero_productos',
                'recencia_transaccion','variacion_mensual_promedio','variacion_mensual_promedio_pct']
    df[to_scale] = StandardScaler().fit_transform(df[to_scale])

    if 'total_spend_fav' in df:
        df['total_spend_fav'] = np.log1p(df['total_spend_fav'])

    cat_vars = [
        'income_range','risk_profile','occupation','age_range_sturges',
        'primer_producto','segundo_producto','combinacion_productos','categoria_favorita_monto'
    ]
    for c in cat_vars:
        if c in df:
            df[c] = LabelEncoder().fit_transform(df[c].astype(str).fillna('unknown'))
    df.drop(columns=['combinacion_productos'], inplace=True, errors='ignore')

    for cat in ['food','health','shopping','transport','entertainment','other','travel','supermarket']:
        df[f'{cat}_count'] = df.get(f'{cat}_count', 0)
    for b in ['checking_account','savings_account','credit_card','investment','insurance']:
        if b in df:
            df[b] = df[b].fillna(False).astype(int)

    X = df.drop(columns=['user_id','insurance'], errors='ignore').fillna(0)
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
    feats = list(model.feature_names_in_)
    X = X.reindex(columns=feats, fill_value=0)
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