import argparse
import json
import os
import warnings
from importlib import import_module

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from ml.config import ModelConfig, load_config
from ml.data_validation import validate_dataframe
from ml.features import add_time_features

warnings.filterwarnings("ignore")
RUTA_ARTEFACTOS = os.path.join(os.path.dirname(__file__), "artefactos")


def _resolve_model(cfg: ModelConfig):
    """Instancia el estimador declarado en la config (modulo.Clase)."""
    module_path, _, class_name = cfg.model_class.rpartition(".")
    if not module_path:
        raise ValueError(f"model.class debe ser 'modulo.Clase', recibido: {cfg.model_class}")
    cls = getattr(import_module(module_path), class_name)
    return cls(**cfg.model_params)


def _split_temporal(df: pd.DataFrame, cfg: ModelConfig) -> tuple[pd.DataFrame, ...]:
    df = df.sort_values("starttime").reset_index(drop=True)
    n_total = len(df)
    n_test = int(n_total * cfg.test_size)
    n_val = int(n_total * cfg.validation_size)
    n_train = n_total - n_val - n_test
    if min(n_train, n_val, n_test) <= 0:
        raise ValueError(
            "El dataset es demasiado chico para el split temporal configurado"
        )
    train = df.iloc[:n_train].copy()
    val = df.iloc[n_train : n_train + n_val].copy()
    test = df.iloc[n_train + n_val :].copy()
    return train, val, test


def _split_random(df: pd.DataFrame, cfg: ModelConfig) -> tuple[pd.DataFrame, ...]:
    stratify = df["viaje_largo"] if cfg.stratify else None
    train_val, test = train_test_split(
        df,
        test_size=cfg.test_size,
        random_state=cfg.random_state,
        stratify=stratify,
    )
    val_fraction = cfg.validation_size / (1 - cfg.test_size)
    stratify_train = train_val["viaje_largo"] if cfg.stratify else None
    train, val = train_test_split(
        train_val,
        test_size=val_fraction,
        random_state=cfg.random_state,
        stratify=stratify_train,
    )
    return train.copy(), val.copy(), test.copy()


def _apply_station_freq(
    df: pd.DataFrame, station_freq: dict[int, int]
) -> pd.DataFrame:
    out = df.copy()
    out["start_station_freq"] = np.log1p(
        out["start_station_id"].map(station_freq).fillna(0)
    )
    return out


def _encode_value(value: str, encoder: LabelEncoder) -> int:
    return encoder.transform([value])[0] if value in encoder.classes_ else -1


def _transform_categorical(
    df: pd.DataFrame, encoders: dict[str, LabelEncoder], columns: list[str]
) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        encoder = encoders[col]
        out[col] = out[col].astype(str).map(
            lambda value, enc=encoder: _encode_value(value, enc)
        )
    return out


def _elegir_umbral(
    y_true: np.ndarray, y_prob: np.ndarray, metric: str = "f1"
) -> float:
    if metric not in {"f1", "recall", "precision"}:
        raise ValueError("metric debe ser f1, recall o precision")

    best_threshold = 0.5
    best_score = -1.0
    for threshold in np.linspace(0.01, 0.99, 99):
        y_pred = (y_prob >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        score = {"f1": f1, "recall": recall, "precision": precision}[metric]
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return best_threshold


def entrenar(ruta_parquet, config: ModelConfig | None = None):
    cfg = config or load_config()
    os.makedirs(RUTA_ARTEFACTOS, exist_ok=True)

    print(f"[1/8] Cargando datos desde: {ruta_parquet}")
    df = pd.read_parquet(ruta_parquet)
    print(f"      Shape: {df.shape}")

    print("[2/8] Validando schema y calidad de datos")
    validacion = validate_dataframe(df)
    for warning in validacion.warnings:
        print(f"      [WARN] {warning}")
    validacion.raise_if_invalid()
    print("      Schema OK")

    umbral_s = cfg.trip_long_threshold_seconds
    print(f"[3/8] Creando variable objetivo (viaje_largo > {umbral_s}s)")
    df["viaje_largo"] = (df["tripduration"] > umbral_s).astype(int)
    print(f"      Proporcion viajes largos: {df['viaje_largo'].mean():.3f}")

    print("[4/8] Ingenieria de features")
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
    df = df.dropna(subset=["starttime"]).copy()
    df["hour"] = df["starttime"].dt.hour
    df["month"] = df["starttime"].dt.month
    df["dayofweek"] = df["starttime"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["age"] = df["year"] - df["birth_year"]
    df = df[(df["age"] >= cfg.age_min) & (df["age"] <= cfg.age_max)].copy()
    df = add_time_features(df)

    print(f"[5/8] Split {cfg.split_strategy} (train/val/test)")
    if cfg.split_strategy == "temporal":
        train, val, test = _split_temporal(df, cfg)
    else:
        train, val, test = _split_random(df, cfg)
    print(f"      Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")

    station_freq = train["start_station_id"].value_counts().to_dict()
    train = _apply_station_freq(train, station_freq)
    val = _apply_station_freq(val, station_freq)
    test = _apply_station_freq(test, station_freq)

    print("[6/8] Codificando variables categoricas")
    label_encoders = {}
    for col in cfg.categorical_features:
        encoder = LabelEncoder()
        train[col] = encoder.fit_transform(train[col].astype(str))
        label_encoders[col] = encoder
        print(f"      {col}: {list(encoder.classes_)}")
    val = _transform_categorical(val, label_encoders, cfg.categorical_features)
    test = _transform_categorical(test, label_encoders, cfg.categorical_features)

    feature_cols = cfg.feature_cols
    X_train = train[feature_cols].astype(float)
    X_val = val[feature_cols].astype(float)
    X_test = test[feature_cols].astype(float)
    y_train = train["viaje_largo"].values
    y_val = val["viaje_largo"].values
    y_test = test["viaje_largo"].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    print(f"[7/8] Entrenando {cfg.model_class}")
    modelo = _resolve_model(cfg)
    modelo.fit(X_train_s, y_train)

    y_val_prob = modelo.predict_proba(X_val_s)[:, 1]
    if cfg.tune_threshold:
        decision_threshold = _elegir_umbral(
            y_val, y_val_prob, metric=cfg.threshold_metric
        )
        print(
            f"      Umbral optimizado ({cfg.threshold_metric}): "
            f"{decision_threshold:.4f}"
        )
    else:
        decision_threshold = cfg.decision_threshold
        print(f"      Umbral fijo: {decision_threshold:.4f}")

    decision_threshold = round(decision_threshold, 4)
    y_prob = modelo.predict_proba(X_test_s)[:, 1]
    y_pred = (y_prob >= decision_threshold).astype(int)
    print("\n      Classification Report:")
    separador = chr(10) + "      "
    print(
        "      "
        + classification_report(
            y_test,
            y_pred,
            labels=[0, 1],
            target_names=["corto", "largo"],
            zero_division=0,
        )
        .rstrip()
        .replace(chr(10), separador)
    )
    roc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    print(f"      ROC-AUC: {roc:.4f}")
    print(f"      PR-AUC: {pr_auc:.4f}")
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    print(f"      Confusion Matrix:\n      {cm}")

    print(f"[8/8] Guardando artefactos en {RUTA_ARTEFACTOS}/")
    joblib.dump(modelo, os.path.join(RUTA_ARTEFACTOS, "modelo.pkl"))
    joblib.dump(
        {
            "label_encoders": label_encoders,
            "scaler": scaler,
            "station_freq": station_freq,
            "feature_cols": feature_cols,
            "decision_threshold": decision_threshold,
            "threshold_metric": cfg.threshold_metric if cfg.tune_threshold else "fixed",
            "split_strategy": cfg.split_strategy,
        },
        os.path.join(RUTA_ARTEFACTOS, "transformers.pkl"),
    )

    tn, fp, fn, tp = cm.ravel()
    report = classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["corto", "largo"],
        output_dict=True,
        zero_division=0,
    )
    metricas = {
        "roc_auc": round(roc, 4),
        "pr_auc": round(pr_auc, 4),
        "gini": round(2 * roc - 1, 4),
        "accuracy": round(report["accuracy"], 4),
        "recall": round(report["largo"]["recall"], 4),
        "precision": round(report["largo"]["precision"], 4),
        "f1_score": round(report["largo"]["f1-score"], 4),
        "matriz_confusion": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "umbral_largo_segundos": umbral_s,
        "umbral_decision": round(decision_threshold, 4),
        "threshold_metric": cfg.threshold_metric if cfg.tune_threshold else "fixed",
        "split_strategy": cfg.split_strategy,
        "proporcion_largos": round(y_test.mean(), 3),
        "train_size": len(train),
        "validation_size": len(val),
        "test_size": len(test),
        "features": feature_cols,
        "modelo": cfg.model_class,
        "model_params": cfg.model_params,
    }
    with open(os.path.join(RUTA_ARTEFACTOS, "metricas.json"), "w") as f:
        json.dump(metricas, f, indent=2)

    print("\n[OK] Entrenamiento completado localmente.")

    bucket = os.getenv("S3_BUCKET_NAME")
    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    if bucket:
        from ml.s3_utils import upload_artifacts
        print(f"\nSubiendo artefactos a s3://{bucket}/{prefix}")
        upload_artifacts(RUTA_ARTEFACTOS, bucket, prefix)
    else:
        print("\n[S3] S3_BUCKET_NAME no configurado, artefactos solo locales.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar clasificador Citibike")
    parser.add_argument("--input", required=True, help="Ruta al archivo .parquet")
    parser.add_argument(
        "--config",
        default=None,
        help="Ruta al archivo YAML de configuracion (default: config/model.yaml o $MODEL_CONFIG)",
    )
    args = parser.parse_args()
    entrenar(args.input, load_config(args.config) if args.config else None)
