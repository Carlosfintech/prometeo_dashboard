#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Feature Engineering para el proyecto Prometeo.
Este script procesa los datasets de transacciones, demografía y productos
para generar variables derivadas para el modelo predictivo.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import os

# Fecha de referencia (equivalente a Sys.Date() en el código R)
REFERENCE_DATE = pd.Timestamp('2024-01-01')

def load_data():
    """Carga los datasets desde los archivos CSV."""
    # Encontrar la ruta absoluta del directorio actual del script
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Construir la ruta a los archivos de datos (retrocediendo un nivel desde notebooks)
    base_path = current_dir.parent / 'data' / 'raw'
    
    print(f"Buscando datos en: {base_path}")
    
    transactions = pd.read_csv(base_path / 'transactions.csv')
    demographics = pd.read_csv(base_path / 'demographics.csv')
    products = pd.read_csv(base_path / 'products.csv')
    
    # Convertir fechas a formato datetime
    transactions['date'] = pd.to_datetime(transactions['date'])
    products['contract_date'] = pd.to_datetime(products['contract_date'])
    
    return transactions, demographics, products

def prepare_demographics(demographics):
    """Prepara el dataset de demografía, incluyendo la variable age_range_sturges."""
    # Crear cortes con base en Sturges (8 segmentos)
    breaks = np.linspace(18, 70, 9)  # 9 puntos de corte para 8 segmentos
    labels = ["18–24", "25–31", "32–38", "39–45", "46–52", "53–59", "60–66", "67–70"]
    
    # Crear variable de rango de edad usando cut (equivalente a cut en R)
    demographics['age_range_sturges'] = pd.cut(
        demographics['age'], 
        bins=breaks, 
        labels=labels, 
        right=True, 
        include_lowest=True
    )
    
    return demographics

def prepare_products(products):
    """Prepara el dataset de productos, generando variables de conteo y fechas."""
    # Cambiar investment_account a investment
    products_mod = products.copy()
    products_mod['product_type'] = products_mod['product_type'].replace('investment_account', 'investment')
    
    # Crear variables binarias para cada producto
    products_wide = pd.pivot_table(
        products_mod,
        index='user_id',
        columns='product_type',
        values='contract_date',
        aggfunc='count',
        fill_value=0
    ).reset_index()
    
    # Convertir a indicadores binarios (0/1)
    product_types = ['checking_account', 'savings_account', 'credit_card', 'insurance', 'investment']
    for col in product_types:
        if col not in products_wide.columns:
            products_wide[col] = 0
        products_wide[col] = (products_wide[col] > 0).astype(int)
    
    # Extraer fechas de primer/segundo producto
    product_dates = (
        products_mod
        .sort_values(['user_id', 'contract_date'])
        .groupby('user_id')
        .apply(lambda x: pd.Series({
            'primer_producto': x['product_type'].iloc[0],
            'fecha_primer_producto': x['contract_date'].iloc[0],
            'segundo_producto': x['product_type'].iloc[1] if len(x) >= 2 else np.nan,
            'fecha_segundo_producto': x['contract_date'].iloc[1] if len(x) >= 2 else pd.NaT,
        }))
        .reset_index()
    )
    
    # Calcular días entre productos y antigüedad del cliente
    product_dates['dias_entre_productos'] = (
        product_dates['fecha_segundo_producto'] - product_dates['fecha_primer_producto']
    ).dt.days
    
    product_dates['antiguedad_cliente'] = (
        REFERENCE_DATE - product_dates['fecha_primer_producto']
    ).dt.days
    
    # Join de products_wide y product_dates
    products_final = (
        product_dates
        .merge(products_wide, on='user_id', how='left')
    )
    
    # Calcular número de productos
    products_final['numero_productos'] = products_final[product_types].sum(axis=1)
    
    # Generar combinación de productos
    # Vamos a hacerlo de forma más eficiente que en R
    def get_product_combination(row):
        products = []
        for product in product_types:
            if row[product] == 1:
                products.append(product)
        
        if not products:
            return "sin_productos"
        
        return " + ".join(products)
    
    products_final['combinacion_productos'] = products_final.apply(get_product_combination, axis=1)
    
    # Reemplazar con las combinaciones específicas según el patrón del código R
    combinations_mapping = {
        'checking_account': 'checking_account',
        'savings_account': 'savings_account',
        'savings_account + credit_card': 'credit_card + savings_account',
        'savings_account + insurance': 'insurance + savings_account',
        'checking_account + insurance': 'checking_account + insurance',
        'checking_account + credit_card': 'checking_account + credit_card',
        'checking_account + investment': 'checking_account + investment',
        'savings_account + investment': 'investment + savings_account'
    }
    
    # Aplicar el mapeo y dejar OTRA_COMBINACION para el resto
    products_final['combinacion_productos'] = products_final['combinacion_productos'].map(
        lambda x: combinations_mapping.get(x, 'OTRA_COMBINACION')
    )
    
    return products_final

def prepare_transactions(transactions):
    """Prepara el dataset de transacciones, generando conteos y agregaciones."""
    # Conteo de transacciones por usuario por categoría
    category_counts = (
        transactions
        .groupby('user_id')['merchant_category']
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )
    
    # Renombrar columnas para seguir el patrón del código R
    category_counts.columns = [
        'user_id' if col == 'user_id' else f'{col}_count' 
        for col in category_counts.columns
    ]
    
    # Calcular estadísticas adicionales por usuario
    transactions_agg = (
        transactions
        .groupby('user_id')
        .agg(
            total_transacciones=('transaction_id', 'count'),
            monto_promedio_transaccion=('amount', 'mean')
        )
        .reset_index()
    )
    
    # Unir con los conteos de categorías
    transactions_agg = transactions_agg.merge(category_counts, on='user_id', how='left')
    
    # Determinar la categoría favorita basada en conteos
    category_cols = [col for col in transactions_agg.columns if col.endswith('_count')]
    
    def get_favorite_category(row):
        categories = {col.replace('_count', ''): row[col] for col in category_cols}
        max_count = max(categories.values())
        # En caso de empate, concatenar con "+"
        fav_categories = [cat for cat, count in categories.items() if count == max_count]
        return " + ".join(fav_categories)
    
    transactions_agg['categoria_favorita'] = transactions_agg.apply(get_favorite_category, axis=1)
    
    # Análisis temporal (mensual)
    transactions_monthly = (
        transactions
        .assign(mes=transactions['date'].dt.to_period('M').dt.to_timestamp())
        .groupby(['user_id', 'mes'])
        .agg(
            monto_mes=('amount', 'sum'),
            transacciones_mes=('transaction_id', 'count')
        )
        .reset_index()
    )
    
    # Identificar mes con más compras y mayor gasto
    transactions_monthly_agg = (
        transactions_monthly
        .sort_values(['user_id', 'mes'])
        .groupby('user_id')
        .apply(lambda x: pd.Series({
            'mes_mas_compras': x.loc[x['transacciones_mes'].idxmax(), 'mes'] if not x.empty else pd.NaT,
            'mes_mayor_monto': x.loc[x['monto_mes'].idxmax(), 'mes'] if not x.empty else pd.NaT,
            'monto_promedio_mensual': x['monto_mes'].mean(),
            'transacciones_promedio_mensual': x['transacciones_mes'].mean()
        }))
        .reset_index()
    )
    
    # Calcular variaciones de un mes al siguiente
    transactions_trend = (
        transactions_monthly
        .sort_values(['user_id', 'mes'])
        .groupby('user_id')
        .apply(lambda x: pd.Series({
            'variacion_mensual_promedio': np.nanmean(
                x['monto_mes'].diff().dropna().values
            ) if len(x) > 1 else np.nan,
            'variacion_mensual_promedio_pct': np.nanmean(
                (x['monto_mes'] / x['monto_mes'].shift(1) - 1).dropna().values
            ) if len(x) > 1 else np.nan
        }))
        .reset_index()
    )
    
    # Calcular métricas adicionales
    user_agg = (
        transactions
        .groupby('user_id')
        .agg(
            total_spend=('amount', 'sum'),
            n_meses_activos=('date', lambda x: x.dt.to_period('M').nunique()),
            recencia_transaccion=('date', lambda x: (REFERENCE_DATE - x.max()).days)
        )
        .reset_index()
    )
    
    # Categoría favorita por monto
    cat_monto = (
        transactions
        .groupby(['user_id', 'merchant_category'])
        .agg(total_spend_cat=('amount', 'sum'))
        .reset_index()
    )
    
    # Encuentrar categoría con mayor monto
    cat_max = (
        cat_monto
        .groupby('user_id')
        .agg(max_spend_cat=('total_spend_cat', 'max'))
        .reset_index()
    )
    
    # Determinar categoría favorita por monto
    cat_fav = (
        cat_monto
        .merge(cat_max, on='user_id')
        .query('total_spend_cat == max_spend_cat')
        .groupby('user_id')
        .apply(lambda x: pd.Series({
            'categoria_favorita_monto': ' + '.join(x['merchant_category']),
            'total_spend_fav': x['total_spend_cat'].sum()
        }))
        .reset_index()
    )
    
    # Calcular share de la categoría favorita
    cat_fav = (
        cat_fav
        .merge(user_agg[['user_id', 'total_spend']], on='user_id')
        .assign(share_fav=lambda x: x['total_spend_fav'] / x['total_spend'])
    )
    
    # Calcular HHI (Herfindahl-Hirschman Index)
    cat_hhi = (
        cat_monto
        .groupby('user_id')
        .apply(lambda x: pd.Series({
            'hhi': np.sum((x['total_spend_cat'] / x['total_spend_cat'].sum()) ** 2)
        }))
        .reset_index()
    )
    
    # Unir todas las agregaciones de transacciones
    transactions_final = (
        transactions_agg
        .merge(transactions_monthly_agg, on='user_id', how='left')
        .merge(transactions_trend, on='user_id', how='left')
        .merge(user_agg, on='user_id', how='left')
        .merge(cat_fav[['user_id', 'categoria_favorita_monto', 'total_spend_fav', 'share_fav']], 
               on='user_id', how='left')
        .merge(cat_hhi, on='user_id', how='left')
    )
    
    return transactions_final

def create_final_dataset():
    """Crea el dataset final uniendo todos los datasets procesados."""
    # Cargar datos
    transactions, demographics, products = load_data()
    
    # Preparar cada dataset
    demographics_processed = prepare_demographics(demographics)
    products_final = prepare_products(products)
    transactions_final = prepare_transactions(transactions)
    
    # Unir todos los datasets
    df_final = (
        demographics_processed
        .merge(products_final, on='user_id', how='left')
        .merge(transactions_final, on='user_id', how='left')
    )
    
    # Obtener ruta del directorio actual y construir la ruta de salida
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    output_path = current_dir.parent / 'data' / 'processed' / 'data_final.csv'
    
    # Asegurar que el directorio de salida existe
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Guardando dataset final en: {output_path}")
    df_final.to_csv(output_path, index=False)
    
    return df_final

if __name__ == "__main__":
    df_final = create_final_dataset()
    print(f"Dataset final creado con {len(df_final)} filas y {len(df_final.columns)} columnas.") 