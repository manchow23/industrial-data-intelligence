import numpy as np
import pytest
from src.processing.train_model import main as train_main
import src.processing.anomaly as anomaly

# Ensure the model exists before tests run
train_main()

def test_normal_reading():
    # Input: np.array([51.0])
    features = np.array([51.0])
    is_anomaly, score = anomaly.predict(features)
    assert is_anomaly is False

def test_anomalous_reading():
    # Input: np.array([100.0])
    features = np.array([100.0])
    is_anomaly, score = anomaly.predict(features)
    assert is_anomaly is True

def test_score_monotonicity():
    # Compare scores for np.array([51.0]) and np.array([120.0])
    normal_features = np.array([51.0])
    extreme_features = np.array([120.0])
    _, score_normal = anomaly.predict(normal_features)
    _, score_extreme = anomaly.predict(extreme_features)
    assert score_extreme > score_normal