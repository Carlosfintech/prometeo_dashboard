import xgboost as xgb
import pickle
import numpy as np
from pathlib import Path

def create_dummy_model():
    # Crear un modelo XGBoost básico
    model = xgb.XGBClassifier(
        n_estimators=10, max_depth=3,
        learning_rate=0.1, objective='binary:logistic'
    )
    
    # El número de características debe coincidir con las generadas por el pipeline
    n_features = 28  # Actualizado para coincidir con el número de características generadas
    X = np.random.rand(100, n_features)
    y = np.random.randint(0, 2, size=100)
    
    # Entrenar el modelo
    model.fit(X, y)

    models_dir = Path(__file__).parent
    models_dir.mkdir(exist_ok=True)

    # Guardar el modelo
    model_path = models_dir / "xgb_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
        
    # Guardar el umbral
    (models_dir / "xgb_threshold.txt").write_text("0.5")
    
    print(f"Modelo dummy creado con {n_features} características")

if __name__ == "__main__":
    create_dummy_model() 