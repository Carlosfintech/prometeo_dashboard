# Prometeo Dashboard

Dashboard interactivo para análisis y gestión de clientes con predicciones de probabilidad.

## Estructura del Proyecto

El dashboard está compuesto por dos partes principales:

- **Frontend**: Aplicación React con TypeScript, Vite y TailwindCSS
- **Backend**: API RESTful en FastAPI que proporciona datos para la visualización

## Frontend

El frontend está construido con React, TypeScript y Vite, utilizando TailwindCSS y shadcn/ui para los componentes de interfaz de usuario.

### Principales Componentes

- **HeatMap**: Visualiza correlaciones entre variables como edad, rango de ingresos y perfil de riesgo
- **PriorityClientsTable**: Tabla de clientes prioritarios con opciones de gestión de estado
- **KPICards**: Tarjetas de indicadores clave de rendimiento
- **ContactProgress**: Seguimiento del progreso de contacto con clientes prioritarios
- **ProbabilityDistribution**: Distribución de probabilidades en categorías
- **AIAssistant**: Asistente de inteligencia artificial para análisis

### Estructura de Archivos

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/      # Componentes específicos del dashboard
│   │   └── ui/             # Componentes de UI reutilizables
│   ├── hooks/              # Custom hooks
│   ├── lib/                # Utilidades y configuración
│   ├── pages/              # Rutas/páginas
│   └── ...
└── ...
```

## Backend

El backend es una API construida con FastAPI que proporciona datos para el dashboard.

### Principales Endpoints

- `/api/v1/metrics/summary`: Resumen de KPIs generales
- `/api/v1/clients/priority-list`: Lista de clientes prioritarios
- `/api/v1/metrics/probability-distribution`: Distribución de probabilidades
- `/api/v1/metrics/heatmap`: Datos para el mapa de calor
- `/api/v1/contacts/progress`: Progreso de contactos con clientes

### Estructura de Archivos

```
backend/
├── app/                    # Código principal
├── models/                 # Modelos de ML
├── alembic/                # Migraciones de base de datos
├── mock_api.py             # API mock para desarrollo
└── ...
```

## Configuración de Desarrollo

### Variables de Entorno

El proyecto utiliza el siguiente archivo `.env` en la raíz:

```
VITE_PORT=9000
VITE_API_BASE_URL=http://localhost:8001
VITE_USE_PROXY=true
```

### Iniciar el Desarrollo

1. Iniciar el backend:

```bash
cd 05.\ Dashboard/backend
python mock_api.py
```

2. Iniciar el frontend:

```bash
cd 05.\ Dashboard/frontend
npm install
npm run dev
```

3. Acceder al dashboard en: http://localhost:9000

## Despliegue

Para desplegar la aplicación, consulte las instrucciones específicas en los READMEs del frontend y backend. 