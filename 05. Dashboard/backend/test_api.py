#!/usr/bin/env python3
"""
Script para probar la conectividad con la API en Render
"""
import requests
import sys

def test_api(url):
    """Prueba la conectividad con la API"""
    print(f"Probando conexión a: {url}")
    
    # Probar endpoint raíz
    try:
        response = requests.get(url, timeout=10)
        print(f"Respuesta (raíz): {response.status_code}")
        print(f"Contenido: {response.text}")
    except Exception as e:
        print(f"Error al conectar a la raíz: {e}")
    
    # Probar endpoint de métricas
    try:
        metrics_url = f"{url}/api/v1/metrics/summary"
        print(f"\nProbando endpoint: {metrics_url}")
        response = requests.get(metrics_url, timeout=10)
        print(f"Respuesta (métricas): {response.status_code}")
        print(f"Contenido: {response.text[:200]}...")  # Mostrar solo los primeros 200 caracteres
    except Exception as e:
        print(f"Error al conectar a métricas: {e}")

if __name__ == "__main__":
    api_url = "https://prometeo-dashboard-api.onrender.com"
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    
    test_api(api_url)
    print("\nPrueba completada.") 