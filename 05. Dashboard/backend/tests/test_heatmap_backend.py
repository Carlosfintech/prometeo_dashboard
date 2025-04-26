import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from mock_api import app, VALID_AXES

client = TestClient(app)

def test_get_heatmap_data_valid_parameters():
    """Test que el endpoint devuelve datos correctos con parámetros válidos."""
    response = client.get("/api/v1/metrics/heatmap?x=age&y=income_range&metric=probability")
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura de datos
    assert "x_categories" in data
    assert "y_categories" in data
    assert "values" in data
    assert "threshold" in data
    
    # Verificar que las categorías son arrays
    assert isinstance(data["x_categories"], list)
    assert isinstance(data["y_categories"], list)
    
    # Verificar que values es una matriz (lista de listas)
    assert isinstance(data["values"], list)
    assert len(data["values"]) == len(data["y_categories"])
    assert all(isinstance(row, list) for row in data["values"])
    
    # Verificar que el umbral es un número
    assert isinstance(data["threshold"], (int, float))

def test_get_heatmap_data_structure():
    """Test que la estructura de datos del mapa de calor es correcta."""
    response = client.get("/api/v1/metrics/heatmap?x=age&y=income_range&metric=probability")
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura de datos completa
    assert "x_categories" in data
    assert "y_categories" in data
    assert "values" in data
    
    # Verificar que la matriz de values tiene dimensiones correctas
    assert len(data["values"]) == len(data["y_categories"])
    assert len(data["values"][0]) == len(data["x_categories"])
    
    # Verificar datos en rango correcto
    if "probability" == "probability":
        # Probabilidad debe estar entre 0 y 1
        assert all(0 <= value <= 1 for row in data["values"] for value in row)

def test_get_heatmap_data_invalid_x():
    """Test que el endpoint retorna 400 con parámetro 'x' inválido."""
    response = client.get("/api/v1/metrics/heatmap?x=invalid&y=income_range&metric=probability")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Variable 'x' no válida" in data["detail"]

def test_get_heatmap_data_invalid_y():
    """Test que el endpoint retorna 400 con parámetro 'y' inválido."""
    response = client.get("/api/v1/metrics/heatmap?x=age&y=invalid&metric=probability")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Variable 'y' no válida" in data["detail"]

def test_get_heatmap_data_invalid_metric():
    """Test que el endpoint retorna 400 con parámetro 'metric' inválido."""
    response = client.get("/api/v1/metrics/heatmap?x=age&y=income_range&metric=invalid")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Métrica no válida" in data["detail"]

def test_get_heatmap_variables():
    """Test que el endpoint de variables disponibles funciona correctamente."""
    response = client.get("/api/v1/metrics/heatmap/variables")
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura de datos
    assert "variables" in data
    assert "categories" in data
    
    # Verificar contenido
    assert isinstance(data["variables"], list)
    assert len(data["variables"]) > 0
    assert "priority" not in data["variables"]
    assert isinstance(data["categories"], dict)

def test_priority_not_in_valid_axes():
    """Test que 'priority' no está en la lista de variables válidas del API."""
    assert "priority" not in VALID_AXES
    
    # Verificar que coincide con lo que devuelve la API
    response = client.get("/api/v1/metrics/heatmap/variables")
    data = response.json()
    assert data["variables"] == VALID_AXES 