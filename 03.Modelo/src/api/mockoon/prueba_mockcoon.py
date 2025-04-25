import pandas as pd
import requests
from io import StringIO

# Dirección base del Mock API (ajusta si cambiaste el puerto)
BASE_URL = "http://localhost:3002"

# Función para cargar CSV desde Mockoon
def get_mock_csv(endpoint):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url)
    
    if response.status_code == 200:
        print(f"✅ {endpoint} cargado correctamente")
        return pd.read_csv(StringIO(response.text))
    else:
        print(f"❌ Error al cargar {endpoint}: {response.status_code}")
        return pd.DataFrame()

# Cargar los 3 datasets
df_demographics = get_mock_csv("/demographics")
df_products     = get_mock_csv("/products")
df_transactions = get_mock_csv("/transactions")

# Verificar contenido
print("\n🔍 Datos demográficos")
print(df_demographics.head())

print("\n🔍 Productos contratados")
print(df_products.head())

print("\n🔍 Transacciones")
print(df_transactions.head())

# Aquí podrías guardarlos si lo necesitas
# df_demographics.to_csv("demographics_mock.csv", index=False)
# df_products.to_csv("products_mock.csv", index=False)
# df_transactions.to_csv("transactions_mock.csv", index=False)