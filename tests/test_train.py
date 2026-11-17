"""Tests para el pipeline de entrenamiento."""
import json
from dataclasses import replace

import joblib
import numpy as np
import pandas as pd
import pytest

from ml import train
from ml.config import load_config


def _dataset(n: int = 120) -> pd.DataFrame:
    starttime = pd.date_range("2018-01-01", periods=n, freq="h")
    pares = np.arange(n) % 2 == 0
    return pd.DataFrame(
        {
            "tripduration": np.where(pares, 600, 1200),
            "starttime": starttime,
            "start_station_id": np.arange(n) % 3 + 1,
            "usertype": np.where(pares, "Subscriber", "Customer"),
            "gender": np.where(pares, "Male", "Female"),
            "birth_year": np.where(pares, 1980, 1990),
            "year": 2018,
            "hour": starttime.hour,
            "month": starttime.month,
            "dayofweek": starttime.dayofweek,
            "is_weekend": starttime.dayofweek.isin([5, 6]).astype(int),
            "viaje_largo": (~pares).astype(int),
        }
    )


def _config():
    base = load_config()
    return replace(
        base,
        model_params={
            "class_weight": "balanced",
            "max_iter": 10,
            "learning_rate": 0.1,
            "max_leaf_nodes": 5,
            "min_samples_leaf": 2,
            "early_stopping": False,
            "random_state": 42,
        },
    )


def test_split_temporal_respeta_orden_y_tamanos():
    df = _dataset(100)
    config = load_config()

    train_df, val_df, test_df = train._split_temporal(df, config)

    assert (len(train_df), len(val_df), len(test_df)) == (70, 10, 20)
    assert train_df["starttime"].max() < val_df["starttime"].min()
    assert val_df["starttime"].max() < test_df["starttime"].min()


def test_split_random_respeta_tamanos():
    df = _dataset(100)
    config = replace(load_config(), split_strategy="random")

    train_df, val_df, test_df = train._split_random(df, config)

    assert (len(train_df), len(val_df), len(test_df)) == (70, 10, 20)
    assert set(train_df.index).isdisjoint(val_df.index)
    assert set(train_df.index).isdisjoint(test_df.index)


def test_elegir_umbral_por_metrica():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])

    umbral_f1 = train._elegir_umbral(y_true, y_prob, "f1")
    umbral_recall = train._elegir_umbral(y_true, y_prob, "recall")
    umbral_precision = train._elegir_umbral(y_true, y_prob, "precision")

    assert 0.3 < umbral_f1 < 0.7
    assert umbral_recall <= 0.1
    assert 0.3 < umbral_precision <= 0.4


def test_elegir_umbral_metrica_invalida():
    with pytest.raises(ValueError, match="metric"):
        train._elegir_umbral(
            np.array([0, 1]), np.array([0.2, 0.8]), "accuracy"
        )


def test_entrenar_genera_artefactos(tmp_path, monkeypatch):
    dataset_path = tmp_path / "datos.parquet"
    _dataset().to_parquet(dataset_path, index=False)
    artefactos_dir = tmp_path / "artefactos"
    monkeypatch.setattr(train, "RUTA_ARTEFACTOS", str(artefactos_dir))
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    train.entrenar(dataset_path, _config())

    for nombre in ("modelo.pkl", "transformers.pkl", "metricas.json"):
        assert (artefactos_dir / nombre).exists()

    with (artefactos_dir / "metricas.json").open(encoding="utf-8") as f:
        metricas = json.load(f)
    transformers = joblib.load(artefactos_dir / "transformers.pkl")
    modelo = joblib.load(artefactos_dir / "modelo.pkl")

    assert hasattr(modelo, "predict_proba")
    assert metricas["split_strategy"] == "temporal"
    assert metricas["train_size"] == 84
    assert metricas["validation_size"] == 12
    assert metricas["test_size"] == 24
    assert metricas["modelo"] == "sklearn.ensemble.HistGradientBoostingClassifier"
    assert "pr_auc" in metricas
    assert "hour_sin" in metricas["features"]
    assert 0 <= metricas["umbral_decision"] <= 1
    assert transformers["decision_threshold"] == metricas["umbral_decision"]
    assert transformers["feature_cols"] == metricas["features"]


def _gate_yaml(tmp_path, roc_min: float) -> str:
    gate = tmp_path / "gate.yaml"
    gate.write_text(
        "enabled: true\n"
        "min_test_size: 0\n"
        "thresholds:\n"
        f"  roc_auc: {roc_min}\n",
        encoding="utf-8",
    )
    return str(gate)


def test_entrenar_con_gate_aprobado_sube_artefactos(tmp_path, monkeypatch):
    dataset_path = tmp_path / "datos.parquet"
    _dataset().to_parquet(dataset_path, index=False)
    monkeypatch.setattr(train, "RUTA_ARTEFACTOS", str(tmp_path / "artefactos"))
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    monkeypatch.delenv("CLOUDWATCH_NAMESPACE", raising=False)
    subidas = []
    monkeypatch.setattr(
        "ml.s3_utils.upload_artifacts",
        lambda local, bucket, prefix: subidas.append((local, bucket, prefix)),
    )

    train.entrenar(
        dataset_path,
        _config(),
        quality_gate=True,
        quality_gate_path=_gate_yaml(tmp_path, roc_min=0.0),
    )

    assert len(subidas) == 1


def test_entrenar_con_gate_fallido_no_sube_artefactos(tmp_path, monkeypatch):
    from ml.quality_gate import QualityGateError

    dataset_path = tmp_path / "datos.parquet"
    _dataset().to_parquet(dataset_path, index=False)
    monkeypatch.setattr(train, "RUTA_ARTEFACTOS", str(tmp_path / "artefactos"))
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    monkeypatch.delenv("CLOUDWATCH_NAMESPACE", raising=False)
    subidas = []
    monkeypatch.setattr(
        "ml.s3_utils.upload_artifacts",
        lambda local, bucket, prefix: subidas.append((local, bucket, prefix)),
    )

    with pytest.raises(QualityGateError):
        train.entrenar(
            dataset_path,
            _config(),
            quality_gate=True,
            quality_gate_path=_gate_yaml(tmp_path, roc_min=1.1),
        )

    assert subidas == []
    # El artefacto local si queda, para poder inspeccionar el fallo.
    assert (tmp_path / "artefactos" / "metricas.json").exists()
