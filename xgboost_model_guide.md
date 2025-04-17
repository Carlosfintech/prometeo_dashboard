# Guía Completa para Construcción, Evaluación y Ajuste de un Modelo XGBoost

## 1. Resumen del Proceso

Este proyecto cubre de forma integral todas las fases de un pipeline de clasificación usando XGBoost para predecir la contratación de un seguro. El proceso incluyó:

1. **Carga y limpieza de datos.**
2. **Evaluación de tres modelos base:** Logistic Regression, Random Forest y XGBoost.
3. **Selección del mejor modelo** según métricas de validación cruzada.
4. **Búsqueda de hiperparámetros óptimos** para XGBoost usando RandomizedSearchCV.
5. **Entrenamiento del modelo final** con esos hiperparámetros.
6. **Evaluación de la importancia de las características.**
7. **División de los datos** en entrenamiento/test (70/30).
8. **Cálculo del threshold óptimo por F1 score.**
9. **Evaluación en test set** con threshold por defecto (0.5) vs. ajustado.
10. **Validación cruzada con y sin threshold ajustado.**
11. **Guardado del modelo final y del threshold.**

---

## 2. Diagrama del Proceso

1. **Evaluación de modelos base**
2. **Tuning de hiperparámetros para el mejor modelo**
3. **Entrenamiento del modelo final** (X_train)
4. **Evaluación de importancia de características**
5. **Predicción de probabilidades sobre X_test**
6. **Curvas ROC y PR**
7. **Selección del mejor threshold por F1**
8. **Evaluación final en test**
9. **Validación cruzada con y sin threshold**
10. **Guardado de modelo y threshold**

---

## 3. Conceptos Clave

### ⭐ Búsqueda de Hiperparámetros (RandomizedSearchCV)
Permite probar combinaciones aleatorias de hiperparámetros para encontrar las mejores según una métrica (ej. `roc_auc`). Usa validación cruzada interna.

### ⭐ Validación Cruzada (CV)
Divide los datos en `k` folds. Entrena con `k-1` y valida con el restante. Repite `k` veces y promedia resultados. Asegura que el modelo generaliza bien.

### ⭐ Curvas ROC y PR
- **ROC**: mide capacidad de separación entre clases.
- **PR**: mejor para clases desbalanceadas. Evalúa trade-off entre precisión y recall.

### ⭐ Desbalance de Clases
Cuando una clase ocurre mucho más que otra (ej. 80/20). Impacta métricas como Accuracy. Por eso usamos ROC AUC, F1, Precision y Recall.

### ⭐ Threshold (Umbral de Clasificación)
Valor de corte para convertir probabilidades en etiquetas 0 o 1. Por defecto es 0.5, pero puede optimizarse por F1 o Recall para mejorar resultados.

### ⭐ Importancia de Características
Permite interpretar cuáles variables fueron más relevantes para la predicción. Puede evaluarse con `feature_importances_`, SHAP o permutación.

---

## 4. Fases del Proyecto

### ✅ Fase 1: Evaluación de modelos base
```python
evaluate_model(modelo, X, y)
```
Compara Logistic Regression, Random Forest y XGBoost con validación cruzada 5-fold. Se escoge el que tenga mejor `roc_auc`.

### ✅ Fase 2: Tuning de hiperparámetros (XGBoost)
```python
tune_model(modelo, param_grid_xgb, X, y)
```
RandomizedSearchCV busca combinaciones óptimas de `max_depth`, `n_estimators`, `learning_rate`, etc.

### ✅ Fase 3: Entrenamiento del modelo final
```python
tuned_xgb.fit(X_train, y_train)
```
Modelo entrenado con 70% de los datos (`train_test_split`).

### ✅ Fase 4: Evaluación de Importancia de Características
```python
importances = tuned_xgb.feature_importances_
```
Visualiza las variables más relevantes con `matplotlib` o SHAP.

### ✅ Fase 5: Evaluación sobre Test
```python
y_scores = tuned_xgb.predict_proba(X_test)[:, 1]
```
Se generan probabilidades y se grafican curvas ROC y PR.

### ✅ Fase 6: Cálculo del Mejor Threshold
```python
best_threshold = thresholds[np.argmax(f1_scores)]
```
Se busca el punto que maximiza el F1 score en `y_test`.

### ✅ Fase 7: Comparación Threshold 0.5 vs Ajustado
```python
classification_report(y_test, y_pred_thresh)
```
Evalúa el impacto del nuevo umbral sobre la matriz de confusión y métricas.

### ✅ Fase 8: Validación Cruzada con Threshold Ajustado
```python
y_probs_cv = cross_val_predict(..., method='predict_proba')
y_pred_cv_custom = (y_probs_cv >= best_threshold).astype(int)
```
Permite ver el rendimiento general con el nuevo threshold sobre todo el dataset.

---

## 5. Archivos para Producción

### 📂 `xgb_model.pkl`
Contiene el modelo entrenado. Usa `.predict_proba()` por defecto.

### 📂 `xgb_threshold.txt`
Contiene el valor del threshold ajustado (ej. 0.32). Se usa para convertir las probabilidades en 0 o 1.

### 🔧 Cómo usar en producción
```python
modelo = joblib.load("xgb_model.pkl")
thr = float(open("xgb_threshold.txt").read())
prob = modelo.predict_proba(X_new)[:, 1]
pred = (prob >= thr).astype(int)
```

---

## 6. Recomendaciones y Buenas Prácticas

- ✅ **Separar el modelo y el threshold** para mayor flexibilidad.
- ✅ **Usar ROC AUC** en validación cruzada para selección de modelo.
- ✅ **Evaluar F1 y Recall** en test, especialmente si las clases están desbalanceadas.
- ✅ **Visualizar curvas ROC y PR**, no confiar solo en accuracy.
- ✅ **Aplicar el threshold ajustado también en validación cruzada** para entender rendimiento general.
- ✅ **Guardar archivos separados para modelo y umbral**.

---

Esta guía te permite repetir este proceso paso a paso, evaluando modelos de clasificación en contextos reales, mejorando su interpretabilidad, explicabilidad y preparándolos para su uso en producción.
