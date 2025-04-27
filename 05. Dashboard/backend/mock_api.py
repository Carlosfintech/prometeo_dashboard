"""
API mock simple para proporcionar datos de prueba a la UI
"""
import random
import uvicorn
import math
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from enum import Enum
import os

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

# Configuración para el componente ContactProgress - Ahora es un dict para poder modificarlo
CONTACT_PROGRESS_CONFIG = {
    "monthly_target": 100  # Meta mensual inicial
}

# Datos de prueba para el componente ContactProgress
CONTACT_DATA = {
    "contacted_this_month": 123  # Número de clientes contactados este mes
}


@app.get("/api/v1/metrics/summary")
async def get_metrics_summary():
    """Obtiene un resumen de los indicadores clave de rendimiento"""
    total = len(CLIENTS)
    # Consistent calculation: use >= threshold
    potential_clients = sum(1 for c in CLIENTS if c["probability"] >= PROBABILITY_THRESHOLD)
    contacted = sum(1 for c in CLIENTS if c["status"] != "pending")
    churn_risk_mean = sum(c["probability"] for c in CLIENTS) / total if total else 0
    expected_conversion = int(potential_clients * 0.20) # Example conversion rate
    financial_opportunity = potential_clients * 1000  # Example value per client

    return {
        "total_clients": total,
        "churn_risk_mean": round(churn_risk_mean, 2),
        "contacted": contacted,
        "conversion_rate": 0.0, # Placeholder
        "at_risk_count": potential_clients, # Use consistent term/calculation
        "potential_clients": potential_clients,
        "expected_conversion": expected_conversion,
        "financial_opportunity": financial_opportunity,
        "contact_progress": contacted # Renamed for clarity?
    }


@app.put("/api/v1/contacts/config")
async def update_contact_config(config_update: Dict[str, Any]):
    """Simula la actualización de la configuración de contactos (ej. meta mensual)."""
    global CONTACT_PROGRESS_CONFIG
    new_target = config_update.get("monthly_target")
    if new_target is not None and isinstance(new_target, int) and new_target > 0:
        CONTACT_PROGRESS_CONFIG["monthly_target"] = new_target
        print(f"Updated monthly target to: {new_target}")
        return {"success": True, "monthly_target": new_target}
    else:
        raise HTTPException(status_code=400, detail="Invalid monthly_target value provided.")


@app.get("/api/v1/contacts/progress")
async def get_contact_progress():
    """
    Obtiene información sobre el progreso de contactos. Usa el umbral consistente.
    """
    # Clientes prioritarios/potenciales (probabilidad >= umbral)
    total_prioritized = sum(1 for c in CLIENTS if c["probability"] >= PROBABILITY_THRESHOLD)
    
    # Clientes contactados (status no es 'pending')
    total_contacted = sum(1 for c in CLIENTS if c["status"] != "pending")
    
    # Asumimos contactados este mes = total contactados (para el mock)
    contacted_this_month = total_contacted

    # Obtener meta mensual actual
    monthly_target = CONTACT_PROGRESS_CONFIG["monthly_target"]
    
    # Cálculos de fecha
    now = datetime.now()
    current_day = now.day
    year = now.year
    month = now.month
    if month == 12:
        last_day_dt = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day_dt = datetime(year, month + 1, 1) - timedelta(days=1)
    last_day_of_month = last_day_dt.day
    days_remaining = max(1, last_day_of_month - current_day)
    
    # Calculamos los contactos restantes para la meta mensual
    remaining_contacts = max(0, monthly_target - contacted_this_month)
    
    # Cálculos de ritmo
    daily_needed = math.ceil(remaining_contacts / days_remaining) if days_remaining > 0 else 0
    days_passed = max(1, current_day)
    daily_expected = math.floor(contacted_this_month / days_passed)
    difference = daily_expected - daily_needed
    
    # Mensaje de proyección
    if contacted_this_month >= monthly_target:
        projection_message = f"¡Meta mensual de {monthly_target} contactos alcanzada!"
    elif difference >= 0:
        projection_message = f"Ritmo actual ({daily_expected}/día) suficiente para alcanzar la meta."
    else:
        projection_message = f"Ritmo actual ({daily_expected}/día) insuficiente. Necesitas {daily_needed}/día."

    return {
        "total_contacted": total_contacted,
        "total_prioritized": total_prioritized,
        "monthly_target": monthly_target,
        "contacted_this_month": contacted_this_month,
        "days_remaining": days_remaining,
        "daily_needed": daily_needed,
        "daily_expected": daily_expected,
        "difference": difference,
        "remaining_contacts": remaining_contacts,
        "projection_message": projection_message
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
    """Actualiza el estado de un cliente sin restricciones de valor."""
    print(f"Received status update request for client {client_id}: {status_data}")
    
    client_found = False
    for client in CLIENTS:
        if client["id"] == client_id:
            # Acepta cualquier valor de estado sin validación
            new_status = status_data.get("status")
            if new_status is not None:
                # Guardar el estado tal cual viene del frontend
                client["status"] = new_status
                client_found = True
                print(f"Updated client {client_id} status to: {new_status}")
                break
            else:
                raise HTTPException(status_code=400, detail="Status field is required")

    if not client_found:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return {
        "id": client_id,
        "status": client["status"],
        "success": True
    }


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
    port = 8001
    # Ensure clean start
    os.system(f"lsof -i :{port} -t | xargs kill -9 2>/dev/null || true") 
    uvicorn.run("mock_api:app", host="0.0.0.0", port=port, reload=True) 