# Script de Seed Data - Documentación

## Resumen

Este script permite poblar la base de datos con datos reales consumidos desde Mockoon, ejecutando el pipeline de machine learning para generar características y almacenar predicciones.

## Requisitos para la ejecución

1. Mockoon ejecutándose en http://localhost:3002 con los endpoints:
   - `/demographics` - Datos demográficos de clientes
   - `/products` - Productos contratados por clientes
   - `/transactions` - Transacciones de clientes

2. Base de datos PostgreSQL configurada correctamente (revisar `.env`)

3. Módulo `src.features` disponible en el PYTHONPATH

## Problemas detectados y soluciones

### 1. Error de conexión a la base de datos

Si experimentas el error "password authentication failed for user postgres", verifica:

- El archivo `.env` con las credenciales correctas
- Que la base de datos esté en ejecución
- Que las credenciales configuradas tengan permisos de escritura

Ejemplo de variables de entorno necesarias:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_contraseña_correcta
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=prometeo_db
DATABASE_URL=postgresql+asyncpg://postgres:tu_contraseña_correcta@localhost:5432/prometeo_db
```

### 2. Error con los campos requeridos por `generate_features`

La función `generate_features` espera recibir un DataFrame con determinadas columnas, pero al llamar `write_batch` solo estamos pasando 'user_id'. 

**Solución**: Modificar `ml_service.py` para que busque automáticamente los datos completos del cliente a partir del user_id, o bien asegurarse de pasar todas las columnas requeridas desde el script de seed.

### 3. Versiones del modelo en el pipeline

Para corregir posibles inconsistencias entre los modelos y las características, asegúrate de que:

1. El modelo cargado corresponde a las características generadas
2. Las columnas esperadas por el modelo existen en el DataFrame generado
3. Los nombres de las columnas son consistentes

## Ejecución

Para ejecutar el script con el PYTHONPATH correcto:

```bash
export PYTHONPATH=$PYTHONPATH:/ruta/a/03.Modelo && python -m scripts.seed_data
```

## Flujo de datos

1. Obtención de datos desde Mockoon API
2. Inserción/actualización en la base de datos
3. Generación de características mediante `generate_features`
4. Predicción con el modelo ML
5. Almacenamiento de resultados en la tabla de predicciones 