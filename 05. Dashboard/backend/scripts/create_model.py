"""
Script para crear un modelo XGBoost simple y un archivo de umbral
para propósitos de prueba del script seed_data.py
"""
import xgboost as xgb
import pickle
import numpy as np
from pathlib import Path

def create_dummy_model():
    # Crear un modelo XGBoost básico
    model = xgb.XGBClassifier(
        n_estimators=10,
        max_depth=3,
        learning_rate=0.1,
        objective='binary:logistic'
    )
    
    # Entrenarlo con datos ficticios
    n_samples = 100
    n_features = 11  # El número de características que espera nuestro modelo
    X = np.random.rand(n_samples, n_features)
    y = np.random.randint(0, 2, size=n_samples)
    
    # Entrenar el modelo
    model.fit(X, y)
    
    # Crear directorio models si no existe
    models_dir = Path(__file__).parent.parent / "models"
    models_dir.mkdir(exist_ok=True)
    
    # Guardar el modelo
    model_path = models_dir / "xgb_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    
    # Guardar un umbral (0.5 es el estándar)
    threshold_path = models_dir / "xgb_threshold.txt"
    with open(threshold_path, "w") as f:
        f.write("0.5")
    
    print(f"Modelo guardado en: {model_path}")
    print(f"Umbral guardado en: {threshold_path}")

if __name__ == "__main__":
    create_dummy_model() 