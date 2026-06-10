import os
import json
import joblib
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")
RUTA_ARTEFACTOS = os.path.join(os.path.dirname(__file__), "artefactos")


class Predictor:
    def __init__(self):
        self._cargar()

    def _cargar(self):
        modelo_path = os.path.join(RUTA_ARTEFACTOS, "modelo.pkl")
        transformers_path = os.path.join(RUTA_ARTEFACTOS, "transformers.pkl")

        if not os.path.exists(modelo_path):
            raise FileNotFoundError(
                "Modelo no encontrado. Ejecuta primero: python -m ml.train --input ruta/datos.parquet"
            )

        self.modelo = joblib.load(modelo_path)
        t = joblib.load(transformers_path)
        self.label_encoders = t["label_encoders"]
        self.scaler = t["scaler"]
        self.station_freq = t["station_freq"]
        self.feature_cols = t["feature_cols"]

    def predecir(self, datos):
        df = pd.DataFrame([datos])
        df["start_station_freq"] = np.log1p(
            df["start_station_id"].map(self.station_freq).fillna(0)
        )
        for col in ["usertype", "gender"]:
            le = self.label_encoders[col]
            df[col] = (
                df[col]
                .astype(str)
                .map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
            )
        X = df[self.feature_cols].astype(float)
        X_s = self.scaler.transform(X)
        prob = self.modelo.predict_proba(X_s)[0, 1]
        pred = int(prob >= 0.65)
        return {
            "probabilidad_largo": round(float(prob), 4),
            "prediccion": pred,
            "etiqueta": "largo" if pred else "corto",
        }


INPUT_SCHEMA = {
    "start_station_id": "int  -  ID de estacion de inicio",
    "usertype": "str   -  'Customer' | 'Subscriber'",
    "gender": "str     -  'Male' | 'Female' | 'Unknown'",
    "hour": "int       -  Hora del dia (0-23)",
    "month": "int      -  Mes (1-12)",
    "dayofweek": "int  -  Dia semana (0=lunes, 6=domingo)",
    "is_weekend": "int -  1 si fin de semana, 0 si no",
    "age": "int        -  Edad del usuario (0-90)",
}

SALIDA_SCHEMA = {
    "probabilidad_largo": "float - Probabilidad de viaje largo (0.0 - 1.0)",
    "prediccion": "int - 1 si viaje largo, 0 si corto",
    "etiqueta": "str - 'largo' | 'corto'",
}


def main():
    predictor = Predictor()

    ejemplo_1 = {
        "start_station_id": 3160,
        "usertype": "Customer",
        "gender": "Male",
        "hour": 17,
        "month": 7,
        "dayofweek": 3,
        "is_weekend": 0,
        "age": 32,
    }
    ejemplo_2 = {
        "start_station_id": 3160,
        "usertype": "Subscriber",
        "gender": "Male",
        "hour": 8,
        "month": 7,
        "dayofweek": 3,
        "is_weekend": 0,
        "age": 32,
    }

    print("\nEjemplo 1 (Customer, 5pm):")
    print(json.dumps(predictor.predecir(ejemplo_1), indent=2))
    print("\nEjemplo 2 (Subscriber, 8am):")
    print(json.dumps(predictor.predecir(ejemplo_2), indent=2))


if __name__ == "__main__":
    main()
