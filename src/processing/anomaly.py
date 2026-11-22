from pathlib import Path
import joblib
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model location: project‑root/models/model.pkl
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "model.pkl"

def _load_model():
    """Load the IsolationForest model; raise a clear error if missing."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. Run src/processing/train_model.py to generate it."
        )
    logger.info(f"Loading model from {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

# Cache the model so it is loaded only once per process
_model = None
def _get_model():
    global _model
    if _model is None:
        _model = _load_model()
    return _model

def predict(features: np.ndarray) -> tuple[bool, float]:
    """
    Run anomaly detection on the given feature(s).

    Parameters
    ----------
    features : np.ndarray
        Input feature array. Expected shape (n_samples, n_features). A single reading
        may be supplied as a 1‑D array; it will be reshaped to 2‑D.

    Returns
    -------
    is_anomaly : bool
        True if the reading is classified as an anomaly.
    score : float
        Continuous anomaly score; higher values mean more anomalous.
    """
    model = _get_model()
    # Ensure 2‑D shape expected by scikit‑learn
    features = np.atleast_2d(features)
    # Predict anomaly label (‑1 = anomaly, 1 = normal)
    is_anomaly = bool(model.predict(features)[0] == -1)
    # Use decision_function for a continuous score (higher = more anomalous)
    score = -model.decision_function(features)[0]
    return is_anomaly, float(score)