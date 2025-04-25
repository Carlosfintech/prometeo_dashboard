#!/bin/bash

# Script para iniciar el servidor de desarrollo de Prometeo API
# Este script verifica la conexión a la base de datos antes de iniciar el servidor

# Configuración de la base de datos
export DB_USER="postgres"
export DB_PASS="1111"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="prometeo_db"
export DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "🔧 Configuración:"
echo "   DATABASE_URL: ${DATABASE_URL}"

echo "🔍 Verificando conexión a PostgreSQL..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1 as connection_test;" > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Error: No se pudo conectar a la base de datos. Verifica que PostgreSQL esté activo."
    echo "   Prueba con: ./db_connect.sh para diagnosticar el problema."
    exit 1
fi

echo "✅ Conexión a la base de datos exitosa"

# Verificar si el entorno virtual está activado
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "ℹ️ Activando entorno virtual..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo "❌ Error: No se encontró el entorno virtual. Crea uno con:"
        echo "   python -m venv venv"
        echo "   e instala las dependencias con:"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

echo "🚀 Iniciando servidor de desarrollo en http://localhost:8000"
echo "   Presiona Ctrl+C para detener el servidor"

# Iniciar el servidor de desarrollo
python -m uvicorn app.api:app --reload --port 8000

# Nota: Si tienes problemas de conexión, prueba con:
# /Library/PostgreSQL/17/bin/psql -U postgres -d prometeo_db
# para asegurarte que puedes conectarte directamente 