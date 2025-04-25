"""
Pruebas del endpoint de métricas
"""
import pytest
from fastapi.testclient import TestClient

from app.api import app

# Cliente sincrónico para pruebas
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