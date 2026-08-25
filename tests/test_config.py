"""Tests para ml.config."""
import pytest

from ml.config import ModelConfig, load_config


def test_load_default_config():
    cfg = load_config()
    assert isinstance(cfg, ModelConfig)
    assert cfg.trip_long_threshold_seconds == 900
    assert cfg.decision_threshold == 0.65
    assert cfg.test_size == 0.2
    assert cfg.random_state == 42
    assert cfg.model_class == "sklearn.linear_model.LogisticRegression"
    assert cfg.model_params["class_weight"] == "balanced"


def test_feature_cols_combines_numeric_and_categorical():
    cfg = load_config()
    assert cfg.feature_cols == [*cfg.numeric_features, *cfg.categorical_features]
    assert "usertype" in cfg.feature_cols
    assert "hour" in cfg.feature_cols


def test_missing_config_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "no_existe.yaml")


def test_custom_config_override(tmp_path):
    cfg_file = tmp_path / "custom.yaml"
    cfg_file.write_text(
        """
target:
  trip_long_threshold_seconds: 600
  decision_threshold: 0.5
split:
  test_size: 0.3
  random_state: 7
  stratify: false
model:
  class: sklearn.linear_model.LogisticRegression
  params:
    max_iter: 500
features:
  numeric: [hour, age]
  categorical: [usertype]
outliers:
  age_min: 18
  age_max: 70
""",
        encoding="utf-8",
    )
    cfg = load_config(cfg_file)
    assert cfg.trip_long_threshold_seconds == 600
    assert cfg.decision_threshold == 0.5
    assert cfg.test_size == 0.3
    assert cfg.random_state == 7
    assert cfg.stratify is False
    assert cfg.age_min == 18
    assert cfg.feature_cols == ["hour", "age", "usertype"]
