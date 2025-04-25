"""
Pruebas de integración para la API FastAPI
"""
import pytest
import httpx
import asyncio
from contextlib import contextmanager
from fastapi.testclient import TestClient

from app.api import app

# Use testclient for synchronous tests
client = TestClient(app)

def test_metrics_summary():
    """Prueba el endpoint /api/v1/metrics/summary"""
    response = client.get("/api/v1/metrics/summary")
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar estructura de la respuesta
    data = response.json()
    assert "total_clients" in data
    assert "churn_risk_mean" in data
    assert "contacted" in data
    assert "at_risk_count" in data
    
    # Verificar tipos de datos
    assert isinstance(data["total_clients"], int)
    assert isinstance(data["churn_risk_mean"], float)
    assert isinstance(data["contacted"], int)
    assert isinstance(data["at_risk_count"], int)


def test_priority_list():
    """Prueba el endpoint /api/v1/clients/priority-list"""
    response = client.get("/api/v1/clients/priority-list?page=1&size=2")
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar estructura de la respuesta
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2  # Verificar tamaño máximo
    
    # Si hay elementos, verificar su estructura
    if data:
        client_data = data[0]
        assert "id" in client_data
        assert "user_id" in client_data
        assert "probability" in client_data
        assert "status" in client_data
        
        # Verificar tipos de datos
        assert isinstance(client_data["id"], int)
        assert isinstance(client_data["user_id"], str)
        assert isinstance(client_data["probability"], float)
        assert isinstance(client_data["status"], str)


def test_update_client_status():
    """Prueba el endpoint PATCH /api/v1/clients/{client_id}/status"""
    # Primero obtener un ID de cliente válido
    response = client.get("/api/v1/clients/priority-list?page=1&size=1")
    assert response.status_code == 200
    
    clients = response.json()
    if not clients:
        pytest.skip("No hay clientes disponibles para la prueba")
    
    client_id = clients[0]["id"]
    
    # Actualizar el estado del cliente
    response = client.patch(
        f"/api/v1/clients/{client_id}/status",
        json={"new_status": "contacted"}
    )
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar la respuesta del endpoint
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert data["status"] == "contacted" 