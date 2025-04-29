# Prometeo API Backend

Backend para el Dashboard de Prometeo, proporcionando una API RESTful para análisis y gestión de datos de clientes.

## Tecnologías

- **FastAPI**: Framework moderno para APIs de alto rendimiento
- **PostgreSQL**: Base de datos relacional para almacenamiento persistente
- **Alembic**: Herramienta de migración de base de datos
- **SQLAlchemy**: ORM para interacción con la base de datos
- **Pydantic**: Validación de datos y serialización
- **uvicorn**: Servidor ASGI de alto rendimiento
- **XGBoost**: Biblioteca para modelos de aprendizaje automático

## Endpoints Principales

El backend proporciona los siguientes endpoints principales:

- `/api/v1/metrics/summary`: Resumen de KPIs generales del sistema
- `/api/v1/clients/priority-list`: Lista de clientes prioritarios con paginación
- `/api/v1/clients/{client_id}/status`: Actualización del estado de contacto del cliente
- `/api/v1/metrics/probability-distribution`: Distribución de probabilidades para visualización
- `/api/v1/metrics/heatmap`: Datos para análisis de correlación en formato de mapa de calor
- `/api/v1/metrics/heatmap/variables`: Variables disponibles para el mapa de calor
- `/api/v1/contacts/progress`: Seguimiento del progreso de contactos y proyección

## Estructura del Proyecto

```
backend/
├── app/                    # Código principal de la aplicación
│   ├── api.py              # Definiciones de API y endpoints
│   ├── database.py         # Configuración de conexión a base de datos
│   ├── models.py           # Modelos SQLAlchemy (ORM)
│   └── schemas.py          # Modelos Pydantic para validación
├── alembic/                # Migraciones de base de datos
├── models/                 # Modelos de machine learning
├── mock_api.py             # API mock para desarrollo
├── requirements.txt        # Dependencias de producción
├── requirements-dev.txt    # Dependencias de desarrollo
└── ...
```

## Configuración de Desarrollo

### Requisitos Previos

- Python 3.8+
- PostgreSQL 14+
- Paquetes del sistema: `build-essential`, `libpq-dev` (Linux)

### Variables de Entorno

Cree un archivo `.env` con las siguientes variables:

```
# Configuración de base de datos
POSTGRES_USER=postgres
POSTGRES_PASSWORD=1111
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=prometeo_db
DATABASE_URL=postgresql+asyncpg://postgres:1111@localhost:5432/prometeo_db

# Seguridad
SECRET_KEY=prometeo_secret_key_dev
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Aplicación
APP_NAME="Prometeo Dashboard"
APP_VERSION="1.0.0"
APP_ENVIRONMENT=development
```

### Instalación

Opciones de instalación:

#### Instalación Automática (Recomendada)

```bash
cd "05. Dashboard/backend"
chmod +x check_env.sh
./check_env.sh
```

#### Instalación Manual

```bash
cd "05. Dashboard/backend"
python -m venv venv
source venv/bin/activate  # En Unix/macOS
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo
```

### Iniciar el Servidor

```bash
cd "05. Dashboard/backend"
python mock_api.py
```

El servidor estará disponible en [http://localhost:8001](http://localhost:8001).

La documentación de la API estará disponible en:
- [http://localhost:8001/docs](http://localhost:8001/docs) (Swagger UI)
- [http://localhost:8001/redoc](http://localhost:8001/redoc) (ReDoc)

### Pruebas

Para ejecutar las pruebas:

```bash
cd "05. Dashboard/backend"
pytest
```

## Despliegue

Para desplegar el backend:

1. Construir imagen Docker:

```bash
docker build -f Dockerfile.dev -t prometeo-backend .
```

2. Ejecutar el contenedor:

```bash
docker run -p 8001:8001 --env-file .env prometeo-backend
```

También puede desplegarse en plataformas como Render, Heroku o AWS utilizando la configuración proporcionada. 