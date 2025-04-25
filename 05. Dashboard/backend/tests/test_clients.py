"""
Pruebas del endpoint de clientes usando mocks
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.api import app
from app.database import Client

# Cliente sincrónico para pruebas
client = TestClient(app)

def test_priority_list_mocked():
    """Prueba el endpoint /api/v1/clients/priority-list con datos simulados"""
    # Crear datos simulados
    mock_clients = [
        MagicMock(
            id=1,
            user_id="user1",
            probability=0.75,
            status="pending"
        ),
        MagicMock(
            id=2,
            user_id="user2",
            probability=0.65,
            status="contacted"
        )
    ]
    
    # Mockear la función de base de datos para evitar conexiones reales
    with patch('app.api.get_priority_list') as mock_get_priority:
        # Configurar el mock para devolver nuestros datos simulados
        mock_db = MagicMock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_all = MagicMock(return_value=mock_clients)
        
        mock_db.execute.return_value = mock_execute
        mock_execute.scalars.return_value = mock_scalars
        mock_scalars.all.return_value = mock_clients
        
        # Hacer el patch de la ejecución real del endpoint
        with patch('app.api.select'), patch('app.api.desc'), patch('sqlalchemy.ext.asyncio.AsyncSession'):
            with patch('app.api.get_db', return_value=mock_db):
                # Realizar la solicitud
                response = client.get("/api/v1/clients/priority-list?page=1&size=2")
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar estructura de la respuesta
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # Verificar tamaño
    
    # Verificar datos en la respuesta
    client_data = data[0]
    assert client_data["id"] == 1
    assert client_data["user_id"] == "user1"
    assert client_data["probability"] == 0.75
    assert client_data["status"] == "pending"
    
    client_data2 = data[1]
    assert client_data2["id"] == 2
    assert client_data2["user_id"] == "user2"
    assert client_data2["probability"] == 0.65
    assert client_data2["status"] == "contacted"


def test_update_client_status_mocked():
    """Prueba el endpoint /api/v1/clients/{client_id}/status con datos simulados"""
    # Crear un cliente simulado
    mock_client = MagicMock(
        id=1,
        user_id="user1",
        status="pending"
    )
    
    # Mockear la función de base de datos
    with patch('app.api.update_client_status') as mock_update:
        mock_db = MagicMock()
        mock_execute = MagicMock()
        mock_scalars = MagicMock()
        mock_first = MagicMock(return_value=mock_client)
        
        mock_db.execute.return_value = mock_execute
        mock_execute.scalars.return_value = mock_scalars
        mock_scalars.first.return_value = mock_client
        
        # Mockear la selección y ejecución
        with patch('app.api.select'), patch('sqlalchemy.ext.asyncio.AsyncSession'):
            with patch('app.api.get_db', return_value=mock_db):
                # Realizar la solicitud
                response = client.patch(
                    "/api/v1/clients/1/status",
                    json={"new_status": "contacted"}
                )
    
    # Verificar código de respuesta
    assert response.status_code == 200
    
    # Verificar la respuesta
    data = response.json()
    assert "success" in data
    assert data["success"] is True 