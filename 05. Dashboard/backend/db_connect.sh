#!/bin/bash

# Script para probar la conexión a la base de datos PostgreSQL
# Sin necesidad de ingresar contraseña manualmente

# Configurar la variable de entorno con la cadena de conexión
export DB_USER="postgres"
export DB_PASS="1111"
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="prometeo_db"
export DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "🔧 Configuración:"
echo "   DATABASE_URL: ${DATABASE_URL}"

# Verificar si el entorno virtual está activado (para funcionalidad futura con Python)
if [[ -z "${VIRTUAL_ENV}" && -f "venv/bin/activate" ]]; then
    echo "ℹ️ Activando entorno virtual..."
    source venv/bin/activate
fi

# Función para probar la conexión a la base de datos
function test_connection() {
    echo "🔍 Comprobando conexión con PostgreSQL..."
    echo "   Intentando conectar a: ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    
    # Intentar conexión con PSQL
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1 as connection_test;" > /dev/null 2>&1
    
    return $?
}

# Ejecutar prueba de conexión
test_connection

# Mostrar mensaje si la conexión fue exitosa
if [ $? -eq 0 ]; then
    echo "✅ Prueba de conexión exitosa"
    echo "📊 Listado de tablas disponibles:"
    PGPASSWORD=1111 psql -h localhost -p 5432 -U postgres -d prometeo_db -c "\dt"
else
    echo "❌ Error en la prueba de conexión"
fi
