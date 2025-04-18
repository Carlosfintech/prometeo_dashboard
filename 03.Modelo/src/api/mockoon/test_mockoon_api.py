#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar que la API de Mockoon esté funcionando correctamente.
Este script prueba la conectividad a todos los endpoints configurados.
"""

import requests
import json
import sys
from pprint import pprint

BASE_URL = "http://localhost:3001"

def test_endpoint(endpoint, method="GET", data=None):
    """Prueba un endpoint específico de la API"""
    url = f"{BASE_URL}/{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data or {})
        else:
            raise ValueError(f"Método no soportado: {method}")
            
        print(f"Endpoint: {endpoint} ({method}) - Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"Error: No se pudo conectar a {url}")
        print("¿Está ejecutándose Mockoon en el puerto 3001?")
        return None
    except Exception as e:
        print(f"Error inesperado al probar {endpoint}: {str(e)}")
        return None

def main():
    """Prueba todos los endpoints disponibles"""
    print("=== Probando API de Mockoon ===")
    
    # Probar endpoint de demografía
    print("\n== Datos demográficos ==")
    demo_data = test_endpoint("demographics")
    if demo_data:
        print(f"Registros demográficos obtenidos: {len(demo_data)}")
        print("Primer registro:")
        pprint(demo_data[0])
    
    # Probar endpoint de productos
    print("\n== Datos de productos ==")
    prod_data = test_endpoint("products")
    if prod_data:
        print(f"Registros de productos obtenidos: {len(prod_data)}")
        print("Primer registro:")
        pprint(prod_data[0])
    
    # Probar endpoint de transacciones
    print("\n== Datos de transacciones ==")
    tx_data = test_endpoint("transactions")
    if tx_data:
        print(f"Registros de transacciones obtenidos: {len(tx_data)}")
        print("Primer registro:")
        pprint(tx_data[0])
    
    # Probar endpoint de resultados
    print("\n== Envío de resultados ==")
    test_result = {
        "user_id": 1001,
        "t0": 0.3456,
        "t0b": 1,
        "t1": 0,
        "timestamp": "2023-06-17T10:30:45.123456"
    }
    result_resp = test_endpoint("results", method="POST", data=[test_result])
    if result_resp:
        print("Respuesta del servidor:")
        pprint(result_resp)
    
    print("\n=== Prueba de API completada ===")
    
    # Verificar si todas las pruebas fueron exitosas
    all_success = all([
        demo_data is not None,
        prod_data is not None,
        tx_data is not None,
        result_resp is not None
    ])
    
    if all_success:
        print("✓ Todos los endpoints funcionan correctamente.")
        return 0
    else:
        print("✗ Al menos un endpoint no funciona correctamente.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 