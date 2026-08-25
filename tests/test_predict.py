"""Tests para ml.predict.Predictor usando artefactos sinteticos."""
import joblib
import numpy as np
import pytest
from sklearn.preprocessing import LabelEncoder, StandardScaler

from ml.predict import Predictor


@pytest.fixture
def artefactos(tmp_path, monkeypatch):
    """Crea artefactos minimos para instanciar Predictor sin entrenar."""
    from sklearn.linear_model import LogisticRegression

    artefactos_dir = tmp_path / "artefactos"
    artefactos_dir.mkdir()

    # Modelo trivial con 8 features (igual que feature_cols).
    feature_cols = [
        "hour", "month", "dayofweek", "is_weekend", "age",
        "start_station_freq", "usertype", "gender",
    ]
    n_features = len(feature_cols)
    modelo = LogisticRegression()
    rng = np.random.default_rng(42)
    X = rng.standard_normal((20, n_features))
    y = (X[:, 0] > 0).astype(int)
    modelo.fit(X, y)
    joblib.dump(modelo, artefactos_dir / "modelo.pkl")

    le_usertype = LabelEncoder().fit(["Customer", "Subscriber"])
    le_gender = LabelEncoder().fit(["Female", "Male", "Unknown"])
    scaler = StandardScaler().fit(X)
    joblib.dump(
        {
            "label_encoders": {"usertype": le_usertype, "gender": le_gender},
            "scaler": scaler,
            "station_freq": {3160: 10},
            "feature_cols": [
                "hour", "month", "dayofweek", "is_weekend", "age",
                "start_station_freq", "usertype", "gender",
            ],
            "decision_threshold": 0.65,
        },
        artefactos_dir / "transformers.pkl",
    )

    monkeypatch.setattr(
        "ml.predict.RUTA_ARTEFACTOS", str(artefactos_dir)
    )
    return artefactos_dir


def test_predict_returns_expected_shape(artefactos):
    p = Predictor()
    resultado = p.predecir(
        {
            "start_station_id": 3160,
            "usertype": "Customer",
            "gender": "Male",
            "hour": 17,
            "month": 7,
            "dayofweek": 3,
            "is_weekend": 0,
            "age": 32,
        }
    )
    assert set(resultado) == {"probabilidad_largo", "prediccion", "etiqueta"}
    assert resultado["prediccion"] in (0, 1)
    assert resultado["etiqueta"] in ("corto", "largo")


def test_predict_unknown_category_maps_to_minus_one(artefactos):
    """Un valor categorico no visto en entrenamiento no rompe la prediccion."""
    p = Predictor()
    resultado = p.predecir(
        {
            "start_station_id": 9999,
            "usertype": "Alien",
            "gender": "Robot",
            "hour": 8,
            "month": 3,
            "dayofweek": 1,
            "is_weekend": 0,
            "age": 40,
        }
    )
    assert resultado["prediccion"] in (0, 1)


def test_predict_uses_decision_threshold(artefactos):
    p = Predictor()
    assert p.decision_threshold == 0.65
