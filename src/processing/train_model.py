import os
from pathlib import Path
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

def main():
    # Determine project root (two levels up from this file)
    project_root = Path(__file__).resolve().parents[2]
    models_dir = project_root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)  # create models/ if missing
    model_path = models_dir / "model.pkl"

    # Generate synthetic sensor readings: normal values + clear outliers
    np.random.seed(42)
    normal = np.random.normal(loc=50, scale=5, size=(1000, 1))   # normal sensor readings
    outliers = np.random.uniform(80, 120, size=(100, 1))          # clear outliers
    data = np.vstack([normal, outliers])

    # Train Isolation Forest (10% contamination)
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(data)

    # Persist the trained model
    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    main()