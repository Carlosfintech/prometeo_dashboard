import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
import mock_api
from mock_api import app, CONTACT_PROGRESS_CONFIG, CONTACT_DATA

client = TestClient(app)

def test_get_contact_progress_status_code():
    """Test que el endpoint retorna código de estado 200."""
    response = client.get("/api/v1/contacts/progress")
    assert response.status_code == 200

def test_get_contact_progress_json_structure():
    """Test que el endpoint retorna la estructura JSON esperada."""
    response = client.get("/api/v1/contacts/progress")
    data = response.json()
    
    # Verificar que todos los campos requeridos están presentes
    expected_fields = [
        "total_contacted", 
        "total_prioritized", 
        "monthly_target", 
        "contacted_this_month", 
        "days_remaining", 
        "daily_needed", 
        "daily_expected", 
        "difference", 
        "projection_message"
    ]
    
    for field in expected_fields:
        assert field in data
    
    # Verificar tipos de datos
    assert isinstance(data["total_contacted"], int)
    assert isinstance(data["total_prioritized"], int)
    assert isinstance(data["monthly_target"], int)
    assert isinstance(data["contacted_this_month"], int)
    assert isinstance(data["days_remaining"], int)
    assert isinstance(data["daily_needed"], int)
    assert isinstance(data["daily_expected"], int)
    assert isinstance(data["difference"], int)
    assert isinstance(data["projection_message"], str)

def test_get_contact_progress_calculations():
    """Test que los cálculos del progreso de contactos son correctos."""
    response = client.get("/api/v1/contacts/progress")
    data = response.json()
    
    # Verificar que los valores calculados son consistentes con los datos en CONTACT_DATA
    assert data["monthly_target"] == CONTACT_PROGRESS_CONFIG["monthly_target"]
    assert data["contacted_this_month"] == CONTACT_DATA["contacted_this_month"]
    
    # Verificar que los cálculos son correctos
    days_remaining = 14  # Valor hardcodeado en el mock
    current_day = 16     # Valor hardcodeado en el mock
    
    # Calcular directamente los valores esperados
    monthly_target = CONTACT_PROGRESS_CONFIG["monthly_target"]
    contacted_this_month = CONTACT_DATA["contacted_this_month"]
    
    # Calcular ritmo diario necesario usando ceil
    expected_daily_needed = (monthly_target - contacted_this_month) / days_remaining
    if expected_daily_needed > int(expected_daily_needed):
        expected_daily_needed = int(expected_daily_needed) + 1
    else:
        expected_daily_needed = int(expected_daily_needed)
    
    # Calcular ritmo diario esperado usando floor
    expected_daily_expected = int(contacted_this_month / current_day)
    
    # Verificar que los valores calculados coinciden con la respuesta del API
    assert data["daily_needed"] == expected_daily_needed
    assert data["daily_expected"] == expected_daily_expected
    assert data["difference"] == expected_daily_expected - expected_daily_needed

def test_get_contact_progress_projection_message():
    """Test que el mensaje de proyección es coherente con la diferencia calculada."""
    response = client.get("/api/v1/contacts/progress")
    data = response.json()
    
    # El mensaje debe ser coherente con el valor de la diferencia
    if data["difference"] >= 0:
        assert "alcanzarás" in data["projection_message"].lower()
    else:
        assert "no alcanzarás" in data["projection_message"].lower() 