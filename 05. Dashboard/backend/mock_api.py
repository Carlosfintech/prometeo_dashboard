"""
API mock simple para proporcionar datos de prueba a la UI
"""
import random
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any

# Crear aplicación FastAPI
app = FastAPI(
    title="Prometeo API (MOCK)",
    description="API Mock para el dashboard de predicción de seguros",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Datos de prueba
CLIENTS = [
    {
        "id": i,
        "user_id": f"user_{i:03d}",
        "probability": round(random.random(), 2),
        "status": "pending",
        "age": random.randint(18, 70),
        "income_range": random.choice(["0-50k", "50k-100k", "100k-150k", "150k+"]),
        "risk_profile": random.choice(["conservative", "moderate", "aggressive"]),
        "priority": random.choice(["low", "medium", "high"])
    }
    for i in range(1, 101)
]

# Ordenar por probabilidad (riesgo) descendente
CLIENTS.sort(key=lambda x: x["probability"], reverse=True)


@app.get("/api/v1/metrics/summary")
async def get_metrics_summary():
    """Obtiene un resumen de los indicadores clave de rendimiento"""
    total = len(CLIENTS)
    churn_risk_mean = sum(c["probability"] for c in CLIENTS) / total
    contacted = sum(1 for c in CLIENTS if c["status"] == "contacted")
    at_risk = sum(1 for c in CLIENTS if c["probability"] > 0.23)
    
    return {
        "total_clients": total,
        "churn_risk_mean": churn_risk_mean,
        "contacted": contacted,
        "conversion_rate": 0.0,
        "at_risk_count": at_risk
    }


@app.get("/api/v1/clients/priority-list")
async def get_priority_list(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """Obtiene la lista de clientes ordenados por probabilidad de abandono"""
    start = (page - 1) * size
    end = start + size
    return CLIENTS[start:end]


@app.patch("/api/v1/clients/{client_id}/status")
async def update_client_status(client_id: int, status_data: Dict[str, str]):
    """Actualiza el estado de un cliente"""
    # Buscar cliente por ID
    for client in CLIENTS:
        if client["id"] == client_id:
            client["status"] = status_data.get("status", "pending")
            return {
                "id": client["id"],
                "user_id": client["user_id"],
                "status": client["status"],
                "success": True
            }
    
    return {"success": False, "message": "Cliente no encontrado"}


if __name__ == "__main__":
    uvicorn.run("mock_api:app", host="0.0.0.0", port=8001, reload=True) 