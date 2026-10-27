"""Punto de entrada del contenedor de entrenamiento.

Descarga el dataset curado desde S3, entrena el modelo y ejecuta el health check.

- Con credenciales AWS (``AWS_ACCESS_KEY_ID``): descarga con boto3, sube los
  artefactos a S3 y valida en modo estricto.
- Sin credenciales: descarga por la URL publica del bucket y deja los
  artefactos solo en el contenedor (modo demo local).

Uso:
    python -m scripts.run_pipeline
"""
from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

from ml import health
from ml.train import entrenar

DEFAULT_DATA_KEY = "curated/citibike_trips/citibike_curated.snappy.parquet"
DESTINO = Path("data/datos.parquet")


def _tiene_credenciales() -> bool:
    return bool(os.getenv("AWS_ACCESS_KEY_ID"))


def descargar_datos(destino: Path = DESTINO) -> None:
    bucket = os.environ["S3_BUCKET_NAME"]
    key = os.getenv("S3_DATA_KEY", DEFAULT_DATA_KEY)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if _tiene_credenciales():
        from ml.s3_utils import download_from_s3

        download_from_s3(bucket, key, str(destino))
        return

    region = os.getenv("AWS_REGION", "us-east-1")
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    print(f"  Descargando {url}")
    urllib.request.urlretrieve(url, destino)


def main() -> int:
    descargar_datos()

    con_credenciales = _tiene_credenciales()
    if not con_credenciales:
        # Sin credenciales no se puede escribir en S3: artefactos solo locales.
        os.environ.pop("S3_BUCKET_NAME", None)

    entrenar(str(DESTINO))

    args = ["--json", "--strict"] if con_credenciales else ["--json", "--skip-s3"]
    return health.main(args)


if __name__ == "__main__":
    sys.exit(main())
