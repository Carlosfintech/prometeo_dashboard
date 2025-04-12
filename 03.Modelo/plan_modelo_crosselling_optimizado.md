# Plan Optimizado de Modelado para Predicción de Contratación de Seguros (12 horas)

## 1. Enfoque y Priorización (30 min)  

- **Objetivo principal**: Desarrollar un modelo predictivo para identificar clientes propensos a contratar un seguro
- **Estrategia**: Optimizar la preparación de datos para maximizar el rendimiento predictivo
- **Entregables mínimos**:
  - Modelo para predecir probabilidad de contratación de seguros
  - Definición de las principales caráteristicas
  - Reporte de resultados

## 2. Análisis y Preparación Exhaustiva de Datos (3 horas) - COMPLETED

### 2.1 Análisis Exploratorio Enfocado - COMPLETED
- Analisis univariado y bivariado
- Análisis de distribución entre clientes con/sin seguros (balance de clases)
- Análisis bivariado especifico entre variables candidatas y la contratación de seguros
- Tiempo estimado: 1 hora

### 2.2 Limpieza y Transformación Óptima - COMPLETED
- Tratamiento de valores atípicos con enfoque en variables financieras
- Imputación selectiva solo para variables altamente predictivas
- Tiempo estimado: 45 min

### 2.3 Ingeniería de Características Selectiva - COMPLETED
- Creación de nuevas variables
  - Crear nuevas variables relacionadas con productos
  - Crear nuevas variables realcionadas con transacciones
  - Hacer un solo dataset
- **Selección sistemática de variables** mediante:
  - **Matriz de correlación con heatmap** para identificar variables predictivas clave y ver la correlación (eliminar colinealidad)
  - Normalización/escalado adecuado según los algoritmos seleccionados
  - One hot encoding y label encoder
- Tiempo estimado: 1.15 horas

## 3. Modelado Predictivo Especializado (4.5 horas) - COMPLETED

### 3.1 Evaluación de Algoritmos Candidatos - COMPLETED
- Implementar versiones básicas de:
  - Gradient Boosting (XGBoost/LightGBM): Ideal para datos tabulares con variables mixtas
  - Random Forest: Robusto contra overfitting con conjuntos de datos pequeños
  - Regresión Logística: Como baseline y para alta interpretabilidad
  - Correr todos los modelos con una función y validación cruzada que mida los parámetros principales AUC, accuracy, f1 score, entre otras.
- Tiempo estimado: 1.5 horas

### 3.2 Implementación y Optimización del Modelo Principal - - COMPLETED
- Seleccionar el mejor algoritmo basado en evaluación preliminar
- Optimización básica de hiperparámetros mediante búsqueda en grid
- Optimización del modelo y análisis de resultado. Iterar el modelo varias veces en caso de no obtener resultados esperados.
- Tiempo estimado: 2 horas

### 3.3 Análisis de Características  - COMPLETED
- Calcular y visualizar importancia de variables
- Generar gráficos SHAP para explicar predicciones individuales
- Identificar perfiles de cliente con alta probabilidad de contratación
- Tiempo estimado: 1 hora

## 4. Implementación en Dashboard (2.5 horas) - PENDIENTE

### 4. 1 Enriquecimiento de datos
- Enriquecer con datos de apis y probar modelo
- Utilizar los datos para el dashboard
- Tiempo estimado: 3 horas

### 4. 2 Dashboards
- Ranking de clientes por probabilidad de contratación de seguro
- Gráficos de importancia de características y filtros por variables
- Agente para hacer recomendaciones basados en data
- Tiempo estimado: 6 horas


## 5. Documentación y Entrega (1.5 horas) 

### 5.1 Reporte
- Métricas de evaluación y su interpretación en contexto de negocio
- Recomendaciones finales respondiendo las preguntas del reto
- Tiempo estimado: 45 min


## 6. Métricas de Éxito para Seguros

- **Técnicas**: 
  - AUC-ROC > 0.75 (considerando el desbalance típico en contratación de seguros)
  - Precision en top-20% > 65% (enfoque en precisión para campañas dirigidas)
  - Recall general > 70% (capturar la mayoría de clientes potenciales)

## 8. Consideraciones Específicas para Seguros

### 8.1 Variables Típicamente Predictivas
- Datos demográficos: edad, riesgo, ocupación.
- Historial financiero: ingresos, gastos, morosidad.
- Productos actuales: créditos, inversiones, ahorro.
- Comportamiento: transacciones pricipales
- Patrones temporales: eventos recientes como cambios en transacciones o productos

### 8.2 Retos Particulares
- Desbalance de clases 
- Estacionalidad en contratación 
- Variables latentes no disponibles (como aversión al riesgo del cliente)

## 9. Consejos para Optimizar el Modelo de Seguros

1. **Equilibrar clases**: Usar técnicas como SMOTE o class_weight para manejar el probable desbalance
2. **Enfocarse en variables de riesgo**: Priorizar variables que indican comportamiento de protección financiera
3. **Validación**: Si es posible, validar con datos más recientes para simular predicción real
4. **Calibrar probabilidades**: Asegurar que las probabilidades predichas reflejen tasas reales de conversión
5. **Segmentar**: Considerar modelos separados para diferentes segmentos si hay suficientes datos

## 10. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Dataset muy desbalanceado | Aplicar técnicas de balanceo |
| Señal predictiva débil | Enfocarse en segmentos específicos donde la señal sea más fuerte |
| Sobreajuste | Validación cruzada rigurosa y metrica roc auc |
| Interpretabilidad insuficiente | Complementar XGBoost/RF con visualizaciones SHAP para explicabilidad 