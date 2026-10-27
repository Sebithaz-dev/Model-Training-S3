"""Genera el dataset curado y el sample del dashboard desde el Parquet raw.

Replica el ETL de AWS Glue y normaliza las columnas que exige el contrato de
``ml/data_validation.py``. Se usa para recrear el demo sin depender de Glue.

Uso:
    python -m scripts.build_curated_dataset \
        --input /ruta/citibike_trips.parquet \
        --output-dir data/curated
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from ml.data_validation import validate_dataframe

GENDER_MAP = {"male": "Male", "female": "Female", "unknown": "Unknown"}

CURATED_COLUMNS = [
    "tripduration",
    "starttime",
    "start_station_id",
    "usertype",
    "gender",
    "birth_year",
    "year",
    "hour",
    "month",
    "dayofweek",
    "is_weekend",
    "age",
]

REQUIRED_RAW_COLUMNS = {
    "tripduration",
    "starttime",
    "start_station_id",
    "usertype",
    "gender",
    "birth_year",
}


def build_curated(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el ETL y devuelve un dataframe listo para entrenar."""
    missing = REQUIRED_RAW_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el raw: {sorted(missing)}")

    curated = df.copy()
    curated["starttime"] = pd.to_datetime(curated["starttime"], errors="coerce")
    curated["gender"] = (
        curated["gender"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(GENDER_MAP)
        .fillna("Unknown")
    )

    curated["year"] = curated["starttime"].dt.year
    curated["hour"] = curated["starttime"].dt.hour
    curated["month"] = curated["starttime"].dt.month
    curated["dayofweek"] = curated["starttime"].dt.dayofweek
    curated["is_weekend"] = curated["dayofweek"].isin([5, 6]).astype(int)
    curated["age"] = curated["year"] - curated["birth_year"]

    curated = curated[
        (curated["tripduration"] > 60)
        & (curated["tripduration"] < 3600)
        & (curated["age"] >= 0)
        & (curated["age"] <= 90)
        & (curated["birth_year"] >= 1900)
        & (curated["birth_year"] <= 2025)
        & curated["starttime"].notna()
    ].copy()

    curated = curated.drop(columns=["end_station_id"], errors="ignore")
    curated = curated[CURATED_COLUMNS]

    result = validate_dataframe(curated)
    result.raise_if_invalid()
    return curated


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el dataset curado de Citi Bike")
    parser.add_argument("--input", required=True, help="Parquet raw de entrada")
    parser.add_argument(
        "--output-dir", default="data/curated", help="Directorio donde guardar los Parquet"
    )
    parser.add_argument(
        "--sample-size", type=int, default=50_000, help="Filas del sample para el dashboard"
    )
    parser.add_argument(
        "--sample-name",
        default="citibike_dashboard_sample.parquet",
        help="Nombre del Parquet del sample",
    )
    parser.add_argument("--seed", type=int, default=42, help="Semilla para el sample")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Leyendo {input_path}")
    raw = pd.read_parquet(input_path)
    print(f"      Shape raw: {raw.shape}")

    print("[2/3] Construyendo dataset curado")
    curated = build_curated(raw)
    print(f"      Shape curado: {curated.shape}")

    curated_path = output_dir / "citibike_curated.snappy.parquet"
    curated.to_parquet(curated_path, index=False, compression="snappy")
    print(f"      Guardado: {curated_path}")

    sample_size = min(args.sample_size, len(curated))
    sample = curated.sample(n=sample_size, random_state=args.seed).reset_index(drop=True)
    sample_path = output_dir / args.sample_name
    sample.to_parquet(sample_path, index=False, compression="snappy")
    print(f"[3/3] Sample dashboard: {sample.shape} -> {sample_path}")


if __name__ == "__main__":
    main()
