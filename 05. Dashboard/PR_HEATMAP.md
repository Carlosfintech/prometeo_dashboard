# Pull Request: Implementación del componente HeatMap con backend

## Descripción

Este PR implementa la conexión entre el componente HeatMap del frontend y el backend mediante FastAPI, así como mejoras en la visualización del mapa de calor. Se ha asegurado que solo se puedan cruzar variables válidas de los datos y se ha excluido "priority" como opción de eje.

## Cambios realizados

### Backend (FastAPI)

1. Implementación de nuevos endpoints:
   - `/api/v1/metrics/heatmap`: Retorna datos para el mapa de calor basados en los parámetros `x`, `y` y `metric`.
   - `/api/v1/metrics/heatmap/variables`: Retorna las variables disponibles para los ejes del mapa de calor.

2. Validación de parámetros:
   - Se valida que las variables `x` e `y` estén en la lista permitida.
   - Se retorna un error 400 si se intentan usar variables no permitidas.

3. Lógica de negocio:
   - Si `metric=probability`, se calcula el promedio de probabilidad para cada celda.
   - Si `metric=count`, se cuenta el número de clientes en cada celda.

### Frontend (React)

1. Actualización del componente HeatMap:
   - Conexión con el backend mediante React Query.
   - Carga dinámica de variables disponibles para los selectores.
   - Implementación de indicador de umbral (línea roja) para métrica de probabilidad.
   - Tooltip para mostrar oportunidad financiera.

2. Mejoras de UX:
   - Estados de carga y error.
   - Opción para mostrar/ocultar la línea de umbral.
   - Actualización automática al cambiar variables.

## Pruebas

### Backend

Se implementaron pruebas unitarias en `tests/test_heatmap_backend.py` que verifican:
- Respuesta 400 si `x` o `y` no son válidos.
- Estructura correcta del JSON en casos válidos.
- Exclusión de "priority" de las variables disponibles.

### Frontend

Se implementaron pruebas en `src/__tests__/HeatMap.test.tsx` que verifican:
- Renderizado correcto de los datos.
- Visualización de la línea de umbral.
- Manejo de estados de carga y error.

## Cómo probar

1. Iniciar el backend:
   ```bash
   cd backend
   python mock_api.py
   ```

2. Iniciar el frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Acceder a http://localhost:8082 y verificar el componente HeatMap.

4. Probar distintas combinaciones de variables en los ejes X e Y.

5. Alternar entre métricas de "probabilidad" y "conteo".

6. Verificar que la línea de umbral aparece solo con métrica de probabilidad.

## Consideraciones

- Se utilizó el cliente HTTP compartido en `src/lib/api.ts`.
- El componente es responsive y se adapta a diferentes tamaños de pantalla.
- Se ha mantenido la estética y UX consistente con el resto del dashboard.

## Screenshots

_(Sería ideal incluir capturas de pantalla en un PR real)_ 