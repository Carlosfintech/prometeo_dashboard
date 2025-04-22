# Prueba End-to-End del Modelo Prometeo

Este directorio contiene herramientas para probar el modelo Prometeo mediante una API simulada con Mockoon.

## Script Principal: `prueba_modelo_api.py`

El script `prueba_modelo_api.py` implementa un flujo completo end-to-end que:

1. Descarga datos desde endpoints Mockoon
2. Procesa los datos mediante feature engineering
3. Realiza predicciones con el modelo XGBoost
4. Envía los resultados de vuelta a la API

## Requisitos

- Python 3.8+
- Mockoon instalado y configurado con `mockoon_config_new.json`
- Dependencias Python: pandas, numpy, scikit-learn, xgboost, requests

## Configuración

El script utiliza las siguientes configuraciones:

```python
BASE_URL = "http://localhost:3002"  # Puerto de Mockoon
# Rutas a los archivos del modelo
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "03.Modelo" / "models"
MODEL_PATH = MODELS_DIR / "xgb_model.pkl"
THRESH_PATH = MODELS_DIR / "xgb_threshold.txt"
```

## Cómo Ejecutar

1. Inicia Mockoon con la configuración del archivo `mockoon_config_new.json` en el puerto 3002
2. Ejecuta el script:

```bash
python prueba_modelo_api.py
```

## Estructura del Script

El script está organizado en 5 secciones principales:

1. **Descarga de tablas** - Obtiene datos demográficos, productos y transacciones del API mock
2. **Feature Engineering** - Procesa los datos utilizando la función `generate_features`
3. **Predicción** - Carga el modelo XGBoost y realiza predicciones
4. **POST resultados** - Envía los resultados al endpoint /results
5. **Orquestador** - Coordina todo el flujo de trabajo

## Flujo de Datos

```
[API Mockoon]───► [Feature Engineering]───► [Modelo XGBoost]───► [Resultados]───► [API Mockoon]
   │                                                               │
   │                                                               │
   └───────────────────────► [Archivo CSV] ◄────────────────────────
```

## Resultados

El script genera:

- Un archivo `results.csv` con predicciones para cada usuario
- Cada registro contiene:
  - `user_id`: Identificador del usuario
  - `t0`: Probabilidad de contratación de seguro (0-1)
  - `t0b`: Predicción binaria (0 o 1)
  - `t1`: Campo placeholder para futuras predicciones

## Manejo de Errores

El script incluye manejo robusto de errores:
- Verifica la existencia del modelo en múltiples ubicaciones
- Valida que los datos descargados no estén vacíos
- Comprueba la alineación de características entre el modelo y los datos
- Guarda datos de depuración (`error_features.csv`) en caso de error

## Otros Archivos en el Directorio

- `mockoon_config_new.json`: Configuración para Mockoon
- `prueba_api.py`: Script simple para probar la conexión con la API
- `results.csv`: Resultados de ejecuciones previas

## Depuración

Si encuentras problemas:
1. Verifica que Mockoon esté ejecutándose en el puerto 3002
2. Confirma que los archivos del modelo existan en la ruta esperada
3. Revisa los logs de error que se muestran en la consola 