import os
import joblib
import numpy as np
import pandas as pd
import boto3
import tempfile

_modelo = None
_transformers = None


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def _descargar_artefactos():
    bucket = os.getenv("S3_BUCKET_NAME")
    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    if not bucket:
        return None, None

    s3 = _get_s3_client()
    tmp = tempfile.gettempdir()
    modelo_path = os.path.join(tmp, "modelo.pkl")
    trans_path = os.path.join(tmp, "transformers.pkl")

    try:
        s3.download_file(bucket, f"{prefix.rstrip('/')}/modelo.pkl", modelo_path)
        s3.download_file(bucket, f"{prefix.rstrip('/')}/transformers.pkl", trans_path)
        return joblib.load(modelo_path), joblib.load(trans_path)
    except Exception as e:
        print(f"[ml_service] Error descargando modelo de S3: {e}")
        return None, None


def cargar_modelo():
    global _modelo, _transformers
    _modelo, _transformers = _descargar_artefactos()


def predecir(datos):
    global _modelo, _transformers
    if _modelo is None:
        cargar_modelo()
        if _modelo is None:
            return None

    t = _transformers
    df = pd.DataFrame([datos])
    df["start_station_freq"] = np.log1p(
        df["start_station_id"].map(t["station_freq"]).fillna(0)
    )
    for col in ["usertype", "gender"]:
        le = t["label_encoders"][col]
        df[col] = (
            df[col]
            .astype(str)
            .map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        )
    X = df[t["feature_cols"]].astype(float)
    X_s = t["scaler"].transform(X)
    prob = _modelo.predict_proba(X_s)[0, 1]
    pred = int(prob >= 0.65)
    return {
        "probabilidad_largo": round(float(prob), 4),
        "prediccion": pred,
        "etiqueta": "largo" if pred else "corto",
    }


def disponible():
    if _modelo is None:
        cargar_modelo()
    return _modelo is not None
