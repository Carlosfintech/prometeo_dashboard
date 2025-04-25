#!/bin/bash

# Configuración de la base de datos
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/prometeo

# Iniciar el servidor de desarrollo
uvicorn app.api:app --reload --port 8000 