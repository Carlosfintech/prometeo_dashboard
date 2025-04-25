"""
Tests con base de datos simulada
"""
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

# Creamos una aplicación minimalista para testing
app_test = FastAPI()

# Modelos simplificados para testing
class ClientOut(BaseModel):
    id: int
    user_id: str
    probability: float
    status: str

class StatusIn(BaseModel):
    new_status: str

# Datos simulados
mock_clients = [
    {"id": 1, "user_id": "user1", "probability": 0.75, "status": "pending"},
    {"id": 2, "user_id": "user2", "probability": 0.65, "status": "contacted"}
]

# Endpoints simulados
@app_test.get("/api/v1/clients/priority-list", response_model=List[ClientOut])
async def get_priority_list_mock():
    """Endpoint simulado para pruebas"""
    return mock_clients

@app_test.patch("/api/v1/clients/{client_id}/status")
async def update_status_mock(client_id: int, status_data: StatusIn):
    """Endpoint simulado para actualizar estado"""
    # Simulamos que actualizamos el cliente
    for client in mock_clients:
        if client["id"] == client_id:
            client["status"] = status_data.new_status
            return {
                "id": client["id"],
                "user_id": client["user_id"],
                "status": client["status"],
                "success": True
            }
    
    # Si no encontramos el cliente
    return {"success": False}

# Cliente de prueba
client = TestClient(app_test)

# Pruebas
def test_priority_list_simple():
    """Prueba el endpoint simulado de lista de prioridad"""
    response = client.get("/api/v1/clients/priority-list")
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar estructura y datos
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    
    assert data[0]["id"] == 1
    assert data[0]["user_id"] == "user1"
    assert data[0]["probability"] == 0.75
    assert data[0]["status"] == "pending"

def test_update_status_simple():
    """Prueba el endpoint simulado de actualización de estado"""
    response = client.patch(
        "/api/v1/clients/1/status",
        json={"new_status": "contacted"}
    )
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar respuesta
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "contacted"
    
    # Verificar que el estado se actualizó en los datos simulados
    assert mock_clients[0]["status"] == "contacted" 