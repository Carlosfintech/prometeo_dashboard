"""
API mock simple para proporcionar datos de prueba a la UI
"""
import random
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from enum import Enum

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

# Definir las variables válidas para los ejes del mapa de calor
VALID_AXES = ["age", "income_range", "risk_profile", "status"]

# Definir categorías para cada variable
AXIS_CATEGORIES = {
    "age": ["18-25", "26-35", "36-45", "46-55", "56+"],
    "income_range": ["0-50k", "50k-100k", "100k-150k", "150k+"],
    "risk_profile": ["conservative", "moderate", "aggressive"],
    "status": ["pending", "contacted"]
}

# Umbral de probabilidad
PROBABILITY_THRESHOLD = 0.23


@app.get("/api/v1/metrics/summary")
async def get_metrics_summary():
    """Obtiene un resumen de los indicadores clave de rendimiento"""
    total = len(CLIENTS)
    churn_risk_mean = sum(c["probability"] for c in CLIENTS) / total if total else 0
    contacted = sum(1 for c in CLIENTS if c["status"] == "contacted")
    at_risk_count = sum(1 for c in CLIENTS if c["probability"] > 0.23)
    # Business metrics
    potential_clients = at_risk_count
    expected_conversion = int(potential_clients * 0.20)
    financial_opportunity = potential_clients * 1000  # in USD
    contact_progress = sum(1 for c in CLIENTS if c["status"] != "pending")
    
    return {
        "total_clients": total,
        "churn_risk_mean": churn_risk_mean,
        "contacted": contacted,
        "conversion_rate": 0.0,
        "at_risk_count": at_risk_count,
        # New business metrics
        "potential_clients": potential_clients,
        "expected_conversion": expected_conversion,
        "financial_opportunity": financial_opportunity,
        "contact_progress": contact_progress
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


@app.get("/api/v1/metrics/probability-distribution")
async def get_probability_distribution():
    """Obtiene la distribución de probabilidades en buckets de 10% para contactados vs no contactados"""
    # Definir rangos de buckets (0-10, 10-20, ..., 90-100)
    buckets = []
    for i in range(10):
        low = i / 10
        high = (i + 1) / 10
        label = f"{int(low*100)}-{int(high*100)}%"
        no_count = sum(1 for c in CLIENTS if c["probability"] >= low and c["probability"] < high and c["status"] == "pending")
        yes_count = sum(1 for c in CLIENTS if c["probability"] >= low and c["probability"] < high and c["status"] != "pending")
        buckets.append({"range": label, "no_contacted": no_count, "contacted": yes_count})
    # Umbral fijo o dinámico (23.89%)
    threshold = 0.2389
    return {"buckets": buckets, "threshold": threshold}


@app.get("/api/v1/metrics/heatmap")
async def get_heatmap_data(
    x: str = Query(..., description="Variable para el eje X"),
    y: str = Query(..., description="Variable para el eje Y"),
    metric: str = Query("probability", description="Métrica a calcular: 'probability' o 'count'")
):
    """
    Obtiene datos para el mapa de calor cruzando dos variables.
    
    - x: Variable para el eje X (age, income_range, risk_profile, status)
    - y: Variable para el eje Y (age, income_range, risk_profile, status)
    - metric: Métrica a calcular ('probability' o 'count')
    
    Retorna matriz de valores según las categorías de cada variable.
    """
    # Validar que las variables estén en la lista permitida
    if x not in VALID_AXES:
        raise HTTPException(status_code=400, detail=f"Variable 'x' no válida. Opciones: {', '.join(VALID_AXES)}")
    
    if y not in VALID_AXES:
        raise HTTPException(status_code=400, detail=f"Variable 'y' no válida. Opciones: {', '.join(VALID_AXES)}")
        
    if metric not in ["probability", "count"]:
        raise HTTPException(status_code=400, detail="Métrica no válida. Debe ser 'probability' o 'count'")
    
    # Obtener categorías para los ejes
    x_categories = AXIS_CATEGORIES.get(x, [])
    y_categories = AXIS_CATEGORIES.get(y, [])
    
    # Función para convertir una edad numérica a su categoría correspondiente
    def age_to_category(age):
        if 18 <= age <= 25:
            return "18-25"
        elif 26 <= age <= 35:
            return "26-35"
        elif 36 <= age <= 45:
            return "36-45"
        elif 46 <= age <= 55:
            return "46-55"
        else:
            return "56+"
    
    # Inicializar matriz de valores
    values = []
    
    # Para cada categoría en el eje Y
    for y_cat in y_categories:
        row = []
        # Para cada categoría en el eje X
        for x_cat in x_categories:
            # Filtrar clientes que coinciden con ambas categorías
            matching_clients = []
            
            for client in CLIENTS:
                # Obtener los valores reales para comparar, transformando si es necesario
                client_x_value = client.get(x)
                client_y_value = client.get(y)
                
                # Convertir la edad a categoría si es necesario
                if x == "age" and isinstance(client_x_value, int):
                    client_x_value = age_to_category(client_x_value)
                
                if y == "age" and isinstance(client_y_value, int):
                    client_y_value = age_to_category(client_y_value)
                
                # Comparar con las categorías objetivo
                if str(client_x_value) == x_cat and str(client_y_value) == y_cat:
                    matching_clients.append(client)
            
            # Calcular valor según la métrica
            if metric == "probability":
                if matching_clients:
                    avg_probability = sum(c["probability"] for c in matching_clients) / len(matching_clients)
                    row.append(round(avg_probability, 2))
                else:
                    row.append(0)
            else:  # count
                row.append(len(matching_clients))
        
        values.append(row)
    
    # Devolver datos estructurados para el mapa de calor
    return {
        "x_categories": x_categories,
        "y_categories": y_categories,
        "values": values,
        "threshold": PROBABILITY_THRESHOLD
    }


# Endpoint para obtener las variables disponibles para el mapa de calor
@app.get("/api/v1/metrics/heatmap/variables")
async def get_heatmap_variables():
    """Obtiene las variables disponibles para los ejes del mapa de calor"""
    return {
        "variables": VALID_AXES,
        "categories": AXIS_CATEGORIES
    }


if __name__ == "__main__":
    uvicorn.run("mock_api:app", host="0.0.0.0", port=8001, reload=True) 