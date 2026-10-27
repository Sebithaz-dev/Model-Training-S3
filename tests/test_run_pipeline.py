"""Tests para scripts.run_pipeline (entrypoint del contenedor)."""
from pathlib import Path

from scripts import run_pipeline


def test_descarga_publica_sin_credenciales(monkeypatch, tmp_path):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("S3_DATA_KEY", "curated/datos.parquet")
    llamadas = []
    monkeypatch.setattr(
        run_pipeline.urllib.request,
        "urlretrieve",
        lambda url, destino: llamadas.append((url, Path(destino))),
    )

    destino = tmp_path / "data" / "datos.parquet"
    run_pipeline.descargar_datos(destino)

    assert llamadas == [
        ("https://bucket-demo.s3.us-east-1.amazonaws.com/curated/datos.parquet", destino)
    ]
    assert destino.parent.exists()


def test_descarga_con_credenciales_usa_boto3(monkeypatch, tmp_path):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    monkeypatch.delenv("S3_DATA_KEY", raising=False)
    llamadas = []
    monkeypatch.setattr(
        "ml.s3_utils.download_from_s3",
        lambda bucket, key, local: llamadas.append((bucket, key, local)),
    )

    destino = tmp_path / "datos.parquet"
    run_pipeline.descargar_datos(destino)

    assert llamadas == [("bucket-demo", run_pipeline.DEFAULT_DATA_KEY, str(destino))]


def test_main_sin_credenciales_no_sube_a_s3(monkeypatch):
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    eventos = {}
    monkeypatch.setattr(run_pipeline, "descargar_datos", lambda: None)

    def fake_entrenar(ruta):
        eventos["bucket_al_entrenar"] = run_pipeline.os.getenv("S3_BUCKET_NAME")

    monkeypatch.setattr(run_pipeline, "entrenar", fake_entrenar)
    monkeypatch.setattr(run_pipeline.health, "main", lambda args: eventos.setdefault("args", args) and 0)

    assert run_pipeline.main() == 0
    assert eventos["bucket_al_entrenar"] is None
    assert eventos["args"] == ["--json", "--skip-s3"]


def test_main_con_credenciales_valida_estricto(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    eventos = {}
    monkeypatch.setattr(run_pipeline, "descargar_datos", lambda: None)
    monkeypatch.setattr(run_pipeline, "entrenar", lambda ruta: None)
    monkeypatch.setattr(run_pipeline.health, "main", lambda args: eventos.setdefault("args", args) and 0)

    assert run_pipeline.main() == 0
    assert eventos["args"] == ["--json", "--strict"]
