import argparse
import json
import os
import warnings
from importlib import import_module

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from ml.config import ModelConfig, load_config
from ml.data_validation import validate_dataframe

warnings.filterwarnings("ignore")
RUTA_ARTEFACTOS = os.path.join(os.path.dirname(__file__), "artefactos")


def _resolve_model(cfg: ModelConfig):
    """Instancia el estimador declarado en la config (modulo.Clase)."""
    module_path, _, class_name = cfg.model_class.rpartition(".")
    if not module_path:
        raise ValueError(f"model.class debe ser 'modulo.Clase', recibido: {cfg.model_class}")
    cls = getattr(import_module(module_path), class_name)
    return cls(**cfg.model_params)


def entrenar(ruta_parquet, config: ModelConfig | None = None):
    cfg = config or load_config()
    os.makedirs(RUTA_ARTEFACTOS, exist_ok=True)

    print(f"[1/7] Cargando datos desde: {ruta_parquet}")
    df = pd.read_parquet(ruta_parquet)
    print(f"      Shape: {df.shape}")

    print("[2/7] Validando schema y calidad de datos")
    validacion = validate_dataframe(df)
    for w in validacion.warnings:
        print(f"      [WARN] {w}")
    validacion.raise_if_invalid()
    print("      Schema OK")

    umbral_s = cfg.trip_long_threshold_seconds
    print(f"[3/7] Creando variable objetivo (viaje_largo > {umbral_s}s)")
    df["viaje_largo"] = (df["tripduration"] > umbral_s).astype(int)
    print(f"      Proporcion viajes largos: {df['viaje_largo'].mean():.3f}")

    print("[4/7] Ingenieria de features")
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
    df["hour"] = df["starttime"].dt.hour
    df["month"] = df["starttime"].dt.month
    df["dayofweek"] = df["starttime"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["age"] = df["year"] - df["birth_year"]
    df = df[(df["age"] >= cfg.age_min) & (df["age"] <= cfg.age_max)].copy()

    station_freq = df["start_station_id"].value_counts().to_dict()
    df["start_station_freq"] = np.log1p(
        df["start_station_id"].map(station_freq).fillna(0)
    )

    print("[5/7] Codificando variables categoricas")
    label_encoders = {}
    for col in cfg.categorical_features:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"      {col}: {list(le.classes_)}")

    feature_cols = cfg.feature_cols
    X = df[feature_cols].astype(float)
    y = df["viaje_largo"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    stratify = y if cfg.stratify else None
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=cfg.test_size, random_state=cfg.random_state, stratify=stratify
    )
    print(f"      Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    print(f"[6/7] Entrenando {cfg.model_class}")
    modelo = _resolve_model(cfg)
    modelo.fit(X_train, y_train)

    y_prob = modelo.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= cfg.decision_threshold).astype(int)
    print("\n      Classification Report:")
    separador = chr(10) + "      "
    print(
        "      "
        + classification_report(y_test, y_pred, target_names=["corto", "largo"])
        .rstrip()
        .replace(chr(10), separador)
    )
    roc = roc_auc_score(y_test, y_prob)
    print(f"      ROC-AUC: {roc:.4f}")
    cm = confusion_matrix(y_test, y_pred)
    print(f"      Confusion Matrix:\n      {cm}")

    print(f"[7/7] Guardando artefactos en {RUTA_ARTEFACTOS}/")
    joblib.dump(modelo, os.path.join(RUTA_ARTEFACTOS, "modelo.pkl"))
    joblib.dump(
        {
            "label_encoders": label_encoders,
            "scaler": scaler,
            "station_freq": station_freq,
            "feature_cols": feature_cols,
            "decision_threshold": cfg.decision_threshold,
        },
        os.path.join(RUTA_ARTEFACTOS, "transformers.pkl"),
    )

    tn, fp, fn, tp = cm.ravel()
    report = classification_report(y_test, y_pred, target_names=["corto", "largo"], output_dict=True)
    metricas = {
        "roc_auc": round(roc, 4),
        "gini": round(2 * roc - 1, 4),
        "accuracy": round(report["accuracy"], 4),
        "recall": round(report["largo"]["recall"], 4),
        "precision": round(report["largo"]["precision"], 4),
        "f1_score": round(report["largo"]["f1-score"], 4),
        "matriz_confusion": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "umbral_largo_segundos": umbral_s,
        "umbral_decision": cfg.decision_threshold,
        "proporcion_largos": round(y.mean(), 3),
        "train_size": X_train.shape[0],
        "test_size": X_test.shape[0],
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
        print('\n[S3] S3_BUCKET_NAME no configurado, artefactos solo locales.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenar clasificador Citibike")
    parser.add_argument("--input", required=True, help="Ruta al archivo .parquet")
    parser.add_argument(
        "--config", default=None,
        help="Ruta al archivo YAML de configuracion (default: config/model.yaml o $MODEL_CONFIG)",
    )
    args = parser.parse_args()
    entrenar(args.input, load_config(args.config) if args.config else None)
