#!/bin/bash

# Configuración de la base de datos
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/prometeo_db

# Iniciar el servidor de desarrollo
uvicorn app.api:app --reload --port 8000 