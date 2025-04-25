#!/bin/bash

# Script para verificar el entorno Python y las dependencias
# Este script comprueba que el entorno virtual exista y que todas las dependencias estén instaladas

echo "🔍 Verificando entorno Python..."

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado o no está en el PATH."
    echo "   Por favor instala Python 3.8 o superior."
    exit 1
fi

# Mostrar versión de Python
PYTHON_VERSION=$(python3 --version)
echo "✅ ${PYTHON_VERSION} encontrado"

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️ Entorno virtual no encontrado, creando uno nuevo..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error al crear el entorno virtual. Verifica tu instalación de Python."
        exit 1
    fi
    echo "✅ Entorno virtual creado correctamente"
else
    echo "✅ Entorno virtual existente encontrado"
fi

# Activar el entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Error al activar el entorno virtual."
    exit 1
fi

# Verificar si pip está disponible
if ! command -v pip &> /dev/null; then
    echo "❌ Error: pip no está disponible en el entorno virtual."
    exit 1
fi

# Actualizar pip
echo "🔄 Actualizando pip..."
pip install --upgrade pip > /dev/null
echo "✅ pip actualizado"

# Instalar dependencias
echo "🔄 Instalando dependencias principales..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Error al instalar las dependencias principales."
    exit 1
fi
echo "✅ Dependencias principales instaladas"

echo "🔄 Instalando dependencias de desarrollo..."
pip install -r requirements-dev.txt
if [ $? -ne 0 ]; then
    echo "❌ Error al instalar las dependencias de desarrollo."
    exit 1
fi
echo "✅ Dependencias de desarrollo instaladas"

echo "📊 Resumen de paquetes instalados:"
pip list | grep -E "fastapi|uvicorn|sqlalchemy|asyncpg|psycopg2|pydantic|alembic"

echo "🎉 Entorno configurado correctamente. Puedes iniciar el servidor con ./start_dev.sh" 