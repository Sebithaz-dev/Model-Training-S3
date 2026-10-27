"""Health check del pipeline de entrenamiento.

Valida la configuracion, los artefactos locales y la conexion a S3 desde la
linea de comandos. Se usa en CI para verificar que el pipeline quedo sano
despues de entrenar.

Uso:
    python -m ml.health
    python -m ml.health --json --skip-s3 --skip-artifacts
    python -m ml.health --strict
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib

from ml.config import DEFAULT_CONFIG_PATH, load_config

SERVICE_NAME = "model-training-s3"
VERSION = "0.1.0"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artefactos"
ARTIFACT_FILES = ("modelo.pkl", "transformers.pkl", "metricas.json")


def _result(status: str, detail: str, **extra) -> dict:
    data = {"status": status, "detail": detail}
    data.update(extra)
    return data


def check_config() -> dict:
    config_path = Path(os.getenv("MODEL_CONFIG") or DEFAULT_CONFIG_PATH)
    try:
        cfg = load_config(config_path)
    except Exception as exc:
        return _result("error", f"No se pudo cargar la configuracion: {exc}")

    return _result(
        "ok",
        "Configuracion cargada correctamente",
        path=str(config_path),
        model_class=cfg.model_class,
        features=len(cfg.feature_cols),
    )


def check_artifacts(artifact_dir: Path | None = None) -> dict:
    artifact_dir = artifact_dir or ARTIFACT_DIR
    missing = [name for name in ARTIFACT_FILES if not (artifact_dir / name).exists()]
    if missing:
        return _result(
            "degraded",
            f"Faltan artefactos locales: {', '.join(missing)}",
            directory=str(artifact_dir),
            missing=missing,
        )

    try:
        joblib.load(artifact_dir / "modelo.pkl")
        joblib.load(artifact_dir / "transformers.pkl")
        with (artifact_dir / "metricas.json").open("r", encoding="utf-8") as f:
            metrics = json.load(f)
    except Exception as exc:
        return _result(
            "error",
            f"Artefactos corruptos: {exc}",
            directory=str(artifact_dir),
        )

    return _result(
        "ok",
        "Artefactos cargados correctamente",
        directory=str(artifact_dir),
        metrics_keys=sorted(metrics)[:10],
    )


def check_s3() -> dict:
    bucket = os.getenv("S3_BUCKET_NAME")
    if not bucket:
        return _result("skipped", "S3_BUCKET_NAME no configurado")

    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    region = os.getenv("AWS_REGION", "us-east-1")
    key = f"{prefix.rstrip('/')}/metricas.json"

    try:
        import boto3
        from botocore.config import Config

        s3 = boto3.client(
            "s3",
            region_name=region,
            config=Config(connect_timeout=5, read_timeout=5, retries={"max_attempts": 0}),
        )
        account_id = boto3.client("sts", region_name=region).get_caller_identity()["Account"]
        s3.head_bucket(Bucket=bucket, ExpectedBucketOwner=account_id)
        s3.head_object(Bucket=bucket, Key=key, ExpectedBucketOwner=account_id)
    except Exception as exc:
        return _result(
            "error",
            f"No se pudo verificar S3: {exc}",
            bucket=bucket,
            region=region,
        )

    return _result(
        "ok",
        "Bucket y artefacto metricas.json accesibles",
        bucket=bucket,
        key=key,
        region=region,
    )


def _overall_status(checks: dict) -> str:
    statuses = {check["status"] for check in checks.values()}
    if "error" in statuses:
        return "error"
    if "degraded" in statuses:
        return "degraded"
    return "ok"


def build_report(skip_s3: bool = False, skip_artifacts: bool = False) -> dict:
    checks = {"config": check_config()}
    if skip_artifacts:
        checks["artifacts"] = _result("skipped", "Validacion de artefactos omitida")
    else:
        checks["artifacts"] = check_artifacts()

    if skip_s3:
        checks["s3"] = _result("skipped", "Validacion de S3 omitida")
    else:
        checks["s3"] = check_s3()

    return {
        "status": _overall_status(checks),
        "service": SERVICE_NAME,
        "version": VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


def exit_code_for(report: dict, strict: bool = False) -> int:
    if report["status"] == "error":
        return 1
    if strict and report["status"] == "degraded":
        return 1
    return 0


def print_report(report: dict) -> None:
    print(f"[{report['status'].upper()}] {report['service']} v{report['version']}")
    for name, check in report["checks"].items():
        print(f"  - {name}: {check['status']} ({check['detail']})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Health check del pipeline de entrenamiento")
    parser.add_argument("--json", action="store_true", help="Imprime el reporte en JSON")
    parser.add_argument("--skip-s3", action="store_true", help="Omite la validacion de S3")
    parser.add_argument(
        "--skip-artifacts",
        action="store_true",
        help="Omite la validacion de artefactos locales",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falla ante cualquier estado degradado",
    )
    args = parser.parse_args(argv)

    report = build_report(skip_s3=args.skip_s3, skip_artifacts=args.skip_artifacts)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    return exit_code_for(report, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
