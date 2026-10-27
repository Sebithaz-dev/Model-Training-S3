"""Carga la configuracion del modelo desde config/model.yaml.

Centraliza todos los hiperparametros y umbrales que antes estaban
hardcodeados en ``train.py``. La ruta del archivo es configurable via
la variable de entorno ``MODEL_CONFIG`` para permitir overrides en CI
o experimentos sin tocar el repo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "model.yaml"


@dataclass(frozen=True)
class ModelConfig:
    trip_long_threshold_seconds: int
    decision_threshold: float
    tune_threshold: bool
    threshold_metric: str
    split_strategy: str
    test_size: float
    validation_size: float
    random_state: int
    stratify: bool
    model_class: str
    model_params: dict
    numeric_features: list[str]
    categorical_features: list[str]
    age_min: int
    age_max: int

    @property
    def feature_cols(self) -> list[str]:
        return [*self.numeric_features, *self.categorical_features]


def load_config(path: str | os.PathLike | None = None) -> ModelConfig:
    """Carga y valida la configuracion desde YAML.

    El path por defecto es ``config/model.yaml`` del repo, pero puede
    sobreescribirse con el argumento ``path`` o la variable de entorno
    ``MODEL_CONFIG``.
    """
    config_path = Path(path or os.getenv("MODEL_CONFIG") or DEFAULT_CONFIG_PATH)
    if not config_path.exists():
        raise FileNotFoundError(f"Archivo de configuracion no encontrado: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    target = data["target"]
    split = data["split"]
    model = data["model"]
    features = data["features"]
    outliers = data["outliers"]

    cfg = ModelConfig(
        trip_long_threshold_seconds=int(target["trip_long_threshold_seconds"]),
        decision_threshold=float(target["decision_threshold"]),
        tune_threshold=bool(target.get("tune_threshold", True)),
        threshold_metric=str(target.get("threshold_metric", "f1")),
        split_strategy=str(split.get("strategy", "temporal")),
        test_size=float(split["test_size"]),
        validation_size=float(split.get("validation_size", 0.1)),
        random_state=int(split["random_state"]),
        stratify=bool(split["stratify"]),
        model_class=str(model["class"]),
        model_params=dict(model["params"]),
        numeric_features=list(features["numeric"]),
        categorical_features=list(features["categorical"]),
        age_min=int(outliers["age_min"]),
        age_max=int(outliers["age_max"]),
    )
    _validate_config(cfg)
    return cfg


def _validate_config(cfg: ModelConfig) -> None:
    if not 0 <= cfg.decision_threshold <= 1:
        raise ValueError("target.decision_threshold debe estar entre 0 y 1")
    if cfg.threshold_metric not in {"f1", "recall", "precision"}:
        raise ValueError(
            "target.threshold_metric debe ser f1, recall o precision"
        )
    if cfg.split_strategy not in {"temporal", "random"}:
        raise ValueError("split.strategy debe ser temporal o random")
    if not 0 < cfg.test_size < 1:
        raise ValueError("split.test_size debe estar entre 0 y 1")
    if not 0 < cfg.validation_size < 1:
        raise ValueError("split.validation_size debe estar entre 0 y 1")
    if cfg.test_size + cfg.validation_size >= 1:
        raise ValueError("test_size + validation_size debe ser menor que 1")
