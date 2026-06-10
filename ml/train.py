import os
import json
import joblib
import warnings
import argparse
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

warnings.filterwarnings("ignore")
RUTA_ARTEFACTOS = os.path.join(os.path.dirname(__file__), "artefactos")


def entrenar(ruta_parquet):
    os.makedirs(RUTA_ARTEFACTOS, exist_ok=True)

    print(f"[1/6] Cargando datos desde: {ruta_parquet}")
    df = pd.read_parquet(ruta_parquet)
    print(f"      Shape: {df.shape}")

    print("[2/6] Creando variable objetivo (viaje_largo > 15min = 900s)")
    df["viaje_largo"] = (df["tripduration"] > 900).astype(int)
    print(f"      Proporcion viajes largos: {df['viaje_largo'].mean():.3f}")

    print("[3/6] Ingenieria de features")
    df["starttime"] = pd.to_datetime(df["starttime"], errors="coerce")
    df["hour"] = df["starttime"].dt.hour
    df["month"] = df["starttime"].dt.month
    df["dayofweek"] = df["starttime"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["age"] = df["year"] - df["birth_year"]
    df = df[(df["age"] >= 0) & (df["age"] <= 90)].copy()

    station_freq = df["start_station_id"].value_counts().to_dict()
    df["start_station_freq"] = np.log1p(
        df["start_station_id"].map(station_freq).fillna(0)
    )

    print("[4/6] Codificando variables categoricas")
    label_encoders = {}
    for col in ["usertype", "gender"]:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
        print(f"      {col}: {list(le.classes_)}")

    feature_cols = [
        "hour", "month", "dayofweek", "is_weekend", "age",
        "start_station_freq", "usertype", "gender"
    ]
    X = df[feature_cols].astype(float)
    y = df["viaje_largo"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"      Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    print("[5/6] Entrenando Logistic Regression")
    modelo = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    modelo.fit(X_train, y_train)

    y_prob = modelo.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.65).astype(int)
    print(f"\n      Classification Report:")
    separador = chr(10) + "      "
    print(
        "      "
        + classification_report(y_test, y_pred, target_names=["corto", "largo"])
        .rstrip()
        .replace(chr(10), separador)
    )
    roc = roc_auc_score(y_test, y_prob)
    print(f"      ROC-AUC: {roc:.4f}")
    print(f"      Confusion Matrix:\n      {confusion_matrix(y_test, y_pred)}")

    print(f"[6/6] Guardando artefactos en {RUTA_ARTEFACTOS}/")
    joblib.dump(modelo, os.path.join(RUTA_ARTEFACTOS, "modelo.pkl"))
    joblib.dump(
        {
            "label_encoders": label_encoders,
            "scaler": scaler,
            "station_freq": station_freq,
            "feature_cols": feature_cols,
        },
        os.path.join(RUTA_ARTEFACTOS, "transformers.pkl"),
    )

    metricas = {
        "roc_auc": round(roc, 4),
        "umbral_largo_segundos": 900,
        "features": feature_cols,
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
    args = parser.parse_args()
    entrenar(args.input)
