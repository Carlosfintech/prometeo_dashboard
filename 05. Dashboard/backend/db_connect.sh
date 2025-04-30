#!/bin/bash

# Script para verificar y establecer conexión a la base de datos PostgreSQL
# Este script verifica la conexión a PostgreSQL y ejecuta los comandos necesarios para su configuración

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Carga de variables de entorno desde archivo .env
if [ -f .env ]; then
    echo -e "${BLUE}Cargando variables de entorno desde .env${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Archivo .env no encontrado, usando valores por defecto${NC}"
fi

# Configuración de la base de datos
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-1111}
DB_HOST=${POSTGRES_HOST:-localhost}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-prometeo_db}

# Si DATABASE_URL está definido, extraer valores
if [ ! -z "$DATABASE_URL" ]; then
    echo -e "${BLUE}Usando DATABASE_URL para la conexión${NC}"
    # Extraer valores de DATABASE_URL si tiene formato postgresql://user:pass@host:port/dbname
    if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASSWORD="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        echo -e "${BLUE}DATABASE_URL parseado correctamente${NC}"
    else
        echo -e "${YELLOW}No se pudo parsear DATABASE_URL, usando valores por defecto${NC}"
    fi
fi

# Función para verificar instalación de PostgreSQL
check_postgres_installed() {
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}PostgreSQL no está instalado o no está en el PATH${NC}"
        echo -e "${YELLOW}Por favor, instala PostgreSQL o asegúrate de que esté en el PATH${NC}"
        return 1
    fi
    echo -e "${GREEN}PostgreSQL está instalado${NC}"
    return 0
}

# Función para verificar si el servicio PostgreSQL está en ejecución
check_postgres_running() {
    # Intentar ejecutar un comando simple para verificar conexión
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "SELECT 1;" postgres &> /dev/null; then
        echo -e "${GREEN}Servicio PostgreSQL está en ejecución${NC}"
        return 0
    else
        echo -e "${RED}No se puede conectar al servicio PostgreSQL${NC}"
        echo -e "${YELLOW}Verifica que el servicio PostgreSQL esté en ejecución:${NC}"
        echo -e "  - Mac/Linux: sudo service postgresql start"
        echo -e "  - Windows: inicia el servicio desde el Panel de Control"
        return 1
    fi
}

# Función para verificar si la base de datos existe
check_database_exists() {
    # Verificar si la base de datos existe
    if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        echo -e "${GREEN}Base de datos '$DB_NAME' existe${NC}"
        return 0
    else
        echo -e "${YELLOW}Base de datos '$DB_NAME' no existe${NC}"
        return 1
    fi
}

# Función para crear la base de datos si no existe
create_database() {
    echo -e "${BLUE}Creando base de datos '$DB_NAME'...${NC}"
    PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Base de datos '$DB_NAME' creada exitosamente${NC}"
        return 0
    else
        echo -e "${RED}Error al crear la base de datos '$DB_NAME'${NC}"
        return 1
    fi
}

# Función para verificar tablas en la base de datos
check_tables() {
    echo -e "${BLUE}Verificando tablas en la base de datos...${NC}"
    TABLES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';" -t | wc -l)
    
    if [ $TABLES -gt 0 ]; then
        echo -e "${GREEN}La base de datos tiene $TABLES tablas${NC}"
        return 0
    else
        echo -e "${YELLOW}La base de datos no tiene tablas${NC}"
        return 1
    fi
}

# Función para ejecutar scripts SQL
run_sql_script() {
    SCRIPT=$1
    echo -e "${BLUE}Ejecutando script SQL: $SCRIPT${NC}"
    
    if [ -f "$SCRIPT" ]; then
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$SCRIPT"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Script SQL ejecutado exitosamente${NC}"
            return 0
        else
            echo -e "${RED}Error al ejecutar script SQL${NC}"
            return 1
        fi
    else
        echo -e "${RED}Archivo SQL no encontrado: $SCRIPT${NC}"
        return 1
    fi
}

# Verificar instalación y servicio
echo -e "${BLUE}=== Verificación de PostgreSQL ===${NC}"
if ! check_postgres_installed; then
    exit 1
fi

if ! check_postgres_running; then
    exit 1
fi

# Verificar/crear base de datos
echo -e "${BLUE}=== Configuración de Base de Datos ===${NC}"
if ! check_database_exists; then
    if ! create_database; then
        exit 1
    fi
fi

# Verificar tablas
check_tables

# Mostrar información de conexión
echo -e "${BLUE}=== Información de Conexión ===${NC}"
echo -e "Host: ${YELLOW}$DB_HOST${NC}"
echo -e "Puerto: ${YELLOW}$DB_PORT${NC}"
echo -e "Usuario: ${YELLOW}$DB_USER${NC}"
echo -e "Base de datos: ${YELLOW}$DB_NAME${NC}"
echo -e "URL de conexión: ${YELLOW}postgresql://$DB_USER:******@$DB_HOST:$DB_PORT/$DB_NAME${NC}"

# Opciones adicionales
echo -e "${BLUE}=== Opciones de Administración ===${NC}"
echo -e "1. Conectar a psql (cliente interactivo)"
echo -e "2. Ejecutar script SQL de inicialización"
echo -e "3. Verificar contenido de tablas"
echo -e "4. Salir"
echo -e -n "${YELLOW}Selecciona una opción (1-4):${NC} "
read OPTION

case $OPTION in
    1)
        echo -e "${BLUE}Conectando a psql...${NC}"
        PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
        ;;
    2)
        echo -e "${BLUE}Selecciona un script SQL para ejecutar:${NC}"
        echo -e "1. Schema inicial (create_tables.sql)"
        echo -e "2. Datos de muestra (sample_data.sql)"
        echo -e -n "${YELLOW}Selecciona una opción (1-2):${NC} "
        read SQL_OPTION
        
        case $SQL_OPTION in
            1) run_sql_script "scripts/create_tables.sql" ;;
            2) run_sql_script "scripts/sample_data.sql" ;;
            *) echo -e "${RED}Opción inválida${NC}" ;;
        esac
        ;;
    3)
        echo -e "${BLUE}Verificando contenido de tablas...${NC}"
        for TABLE in demographics prediction_results contacts products transactions goals
        do
            COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM $TABLE;" -t 2>/dev/null || echo "Tabla no existe")
            echo -e "Tabla ${YELLOW}$TABLE${NC}: ${GREEN}$COUNT${NC} registros"
        done
        ;;
    4)
        echo -e "${GREEN}Saliendo${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        ;;
esac

echo -e "${GREEN}Proceso completado${NC}"
