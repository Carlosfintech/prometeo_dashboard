#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Feature engineering optimizado y "future‑proof" para el proyecto Prometeo.
Genera ../data/processed/Pipeline_test1.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder
import logging
import gc      # Para gestión de memoria
from functools import partial
import warnings

# Suprimir advertencias que no son críticas
warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# ------------------------------------------------------------------
# Configuración de registro
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ------------------------------------------------------------------
# Parámetros globales
# ------------------------------------------------------------------
DATA_RAW   = Path("../data/raw")
DATA_PROD  = Path("../data/processed")
DATA_PROD.mkdir(exist_ok=True, parents=True)

REFERENCE_DATE = pd.Timestamp("2024-01-01")

# ------------------------------------------------------------------
# 1. Carga de datos - con tipos optimizados
# ------------------------------------------------------------------
def read_with_dtypes(filepath, date_cols=None, cat_cols=None):
    """Lee CSV con tipos de datos optimizados."""
    dtypes = {}
    parse_dates = date_cols if date_cols else []
    
    if cat_cols:
        for col in cat_cols:
            dtypes[col] = 'category'
            
    return pd.read_csv(filepath, dtype=dtypes, parse_dates=parse_dates)

# Definir tipos para cada dataset
transactions = read_with_dtypes(
    DATA_RAW / "transactions.csv",
    date_cols=["date"],
    cat_cols=["merchant_category"]
)

demographics = read_with_dtypes(
    DATA_RAW / "demographics.csv", 
    cat_cols=["income_range", "risk_profile", "occupation"]
)

products = read_with_dtypes(
    DATA_RAW / "products.csv",
    date_cols=["contract_date"],
    cat_cols=["product_type"]
)

logging.info("Archivos cargados con tipos optimizados")

# ------------------------------------------------------------------
# 2. DEMOGRAPHICS – age_range_sturges
# ------------------------------------------------------------------
# Vectorizado sin usar apply
breaks = np.linspace(18, 70, 9)
labels = ["18–24", "25–31", "32–38", "39–45",
          "46–52", "53–59", "60–66", "67–70"]

demographics["age_range_sturges"] = pd.cut(
    demographics["age"],
    bins=breaks,
    labels=labels,
    right=True,
    include_lowest=True
)
demographics["age_range_sturges"] = demographics["age_range_sturges"].astype('category')

# ------------------------------------------------------------------
# 3. PRODUCTS – flags, fechas y métricas
# ------------------------------------------------------------------
# Más eficiente que crear una copia completa
products["product_type"] = products["product_type"].replace("investment_account", "investment")

# Crea flags de producto de manera vectorizada
flag_cols = ["checking_account", "savings_account", "credit_card", 
             "insurance", "investment"]

# Preprocesamiento más eficiente de productos
prod_pivoted = products.pivot_table(
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
prod_sorted = products.sort_values(["user_id", "contract_date"])
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
    (REFERENCE_DATE - prod_agg["fecha_primer_producto"]).dt.days.astype('int32')
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

del prod_sorted, first_products, second_products, prod_pivoted, prod_with_rank
gc.collect()  # Liberar memoria

# ------------------------------------------------------------------
# 4. TRANSACTIONS – estadísticas por usuario
# ------------------------------------------------------------------
# Conteos por categoría usando pivot_table (más eficiente)
cat_counts = transactions.pivot_table(
    index="user_id",
    columns="merchant_category",
    values="transaction_id",
    aggfunc="count",
    fill_value=0
).add_suffix("_count").reset_index()

# Calcular estadísticas básicas (vectorizado)
tx_basic = (
    transactions.groupby("user_id")
      .agg(
          total_transacciones        = ("transaction_id", "count"),
          monto_promedio_transaccion = ("amount", "mean"),
          total_spend                = ("amount", "sum"),
          n_meses_activos            = ("date", lambda s: s.dt.to_period("M").nunique()),
          recencia_transaccion       = ("date", lambda s: (REFERENCE_DATE - s.max()).days)
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
sp_by_cat = transactions.pivot_table(
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
tx_month = transactions.copy()
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

del tx_month, month_agg, user_max_tx, user_max_amt, month_diffs, month_pcts
gc.collect()  # Liberar memoria

logging.info("Transacciones agregadas de forma optimizada")

# ------------------------------------------------------------------
# 5. DATASET FINAL y transformaciones
# ------------------------------------------------------------------
df = (demographics
      .merge(prod_agg, on="user_id", how="left")
      .merge(tx_full,  on="user_id", how="left"))

# Variables a descartar (incluye user_id y fecha_segundo_producto_ts)
drop_cols = [
    "fecha_segundo_producto_ts",
    "total_spend", "monto_promedio_transaccion", "monto_promedio_mensual",
    "hhi", "share_fav", "total_transacciones", "categoria_favorita"
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
scaler = StandardScaler()
to_scale = [
    "age", "dias_entre_productos", "antiguedad_cliente",
    "numero_productos", "recencia_transaccion",
    "variacion_mensual_promedio", "variacion_mensual_promedio_pct"
]
present = [c for c in to_scale if c in df.columns]
# Usar un subset en lugar de crear copias
if present:
    df[present] = scaler.fit_transform(df[present])

# Log1p (vectorizado)
if "total_spend_fav" in df.columns:
    df["total_spend_fav"] = np.log1p(df["total_spend_fav"])

# Label encoding (vectorizado) - CON CAMBIO PARA MANEJAR CATEGORICAL
cat_vars = [
    "income_range", "risk_profile", "occupation", "age_range_sturges",
    "primer_producto", "segundo_producto", "combinacion_productos",
    "categoria_favorita_monto"
]

for c in cat_vars:
    if c in df.columns:
        # Primero convertir a string para evitar problemas con tipo 'category'
        if df[c].dtype.name == 'category':
            df[c] = df[c].astype(str)
            
        # Manejar valores nulos
        if df[c].isna().any():
            df[c] = df[c].fillna('unknown')
            
        le = LabelEncoder()
        df[c] = le.fit_transform(df[c].astype(str))

df.drop(columns=["combinacion_productos"], errors="ignore", inplace=True)

# ------------------------------------------------------------------
# 6. Guardar
# ------------------------------------------------------------------
outfile = DATA_PROD / "Pipeline_test2.csv"
df.to_csv(outfile, index=False)
logging.info(f"Dataset final guardado: {outfile}  ({df.shape[0]} filas, {df.shape[1]} columnas)")