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
    # Business metrics
    assert "potential_clients" in data
    assert "expected_conversion" in data
    assert "financial_opportunity" in data
    assert "contact_progress" in data
    
    # Verificar tipos de datos
    assert isinstance(data["total_clients"], int)
    assert isinstance(data["churn_risk_mean"], float)
    assert isinstance(data["contacted"], int)
    assert isinstance(data["at_risk_count"], int)
    # Verify new types
    assert isinstance(data["potential_clients"], int)
    assert isinstance(data["expected_conversion"], int)
    assert isinstance(data["financial_opportunity"], int)
    assert isinstance(data["contact_progress"], int)

def test_probability_distribution():
    """Prueba el endpoint /api/v1/metrics/probability-distribution"""
    response = client.get("/api/v1/metrics/probability-distribution")
    # Verificar código de respuesta
    assert response.status_code == 200
    data = response.json()
    # Verificar estructura básica
    assert "buckets" in data
    assert "threshold" in data
    # Tipos
    assert isinstance(data["buckets"], list)
    assert isinstance(data["threshold"], float)
    # Cada bucket debe tener keys y tipos correctos
    for bucket in data["buckets"]:
        assert "range" in bucket and "no_contacted" in bucket and "contacted" in bucket
        assert isinstance(bucket["range"], str)
        assert isinstance(bucket["no_contacted"], int)
        assert isinstance(bucket["contacted"], int) 