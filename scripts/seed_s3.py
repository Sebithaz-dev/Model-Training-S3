"""Crea y puebla el bucket S3 del demo con datos y artefactos.

Uso:
    python -m scripts.seed_s3 \
        --bucket citibike-datalake-seb-<account-id> \
        --region us-east-1 \
        --landing /ruta/citibike_trips.parquet \
        --curated-dir data/curated \
        --artifacts-dir ml/artefactos \
        --public-read

Requiere credenciales AWS con permisos para crear el bucket, configurar su
policy y subir objetos. No contiene credenciales: usa la cadena por defecto de
boto3 (variables de entorno, perfil, rol, etc.).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

S3_DATA_PREFIX = "curated/citibike_trips"
S3_MODEL_PREFIX = "models"
S3_LANDING_PREFIX = "landing"


def _public_policy(bucket: str) -> str:
    return json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket}/*",
                }
            ],
        }
    )


def ensure_bucket(s3, bucket: str, region: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"Bucket existente: {bucket}")
        return
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in {"404", "NoSuchBucket"}:
            raise

    kwargs = {"Bucket": bucket}
    if region != "us-east-1":
        kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
    s3.create_bucket(**kwargs)
    print(f"Bucket creado: {bucket}")


def make_public(s3, bucket: str) -> None:
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )
    s3.put_bucket_policy(Bucket=bucket, Policy=_public_policy(bucket))
    print("Bucket configurado como publico de solo lectura")


def upload(s3, bucket: str, local: Path, key: str, content_type: str) -> None:
    if not local.exists():
        print(f"  [WARN] No existe {local}, se omite")
        return
    s3.upload_file(
        str(local),
        bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    print(f"  {local} -> s3://{bucket}/{key}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea y puebla el bucket S3 del demo")
    parser.add_argument("--bucket", required=True, help="Nombre del bucket")
    parser.add_argument("--region", default="us-east-1", help="Region AWS")
    parser.add_argument("--landing", default=None, help="Parquet raw para la zona landing")
    parser.add_argument("--curated-dir", default="data/curated", help="Directorio del curado")
    parser.add_argument("--artifacts-dir", default="ml/artefactos", help="Directorio de artefactos")
    parser.add_argument(
        "--public-read",
        action="store_true",
        help="Configura el bucket como publico de solo lectura",
    )
    args = parser.parse_args()

    s3 = boto3.client("s3", region_name=args.region)
    ensure_bucket(s3, args.bucket, args.region)

    if args.public_read:
        try:
            make_public(s3, args.bucket)
        except ClientError as exc:
            print(f"[WARN] No se pudo configurar el bucket publico: {exc}")
            print("       El dashboard necesitara credenciales o un bucket publico.")

    curated_dir = Path(args.curated_dir)
    artifacts_dir = Path(args.artifacts_dir)

    print("\nSubiendo datos:")
    if args.landing:
        upload(
            s3,
            args.bucket,
            Path(args.landing),
            f"{S3_LANDING_PREFIX}/citibike_trips.parquet",
            "application/octet-stream",
        )
    upload(
        s3,
        args.bucket,
        curated_dir / "citibike_curated.snappy.parquet",
        f"{S3_DATA_PREFIX}/citibike_curated.snappy.parquet",
        "application/octet-stream",
    )
    upload(
        s3,
        args.bucket,
        curated_dir / "citibike_dashboard_sample.parquet",
        f"{S3_DATA_PREFIX}/citibike_dashboard_sample.parquet",
        "application/octet-stream",
    )

    print("\nSubiendo artefactos:")
    for name, content_type in [
        ("modelo.pkl", "application/octet-stream"),
        ("transformers.pkl", "application/octet-stream"),
        ("metricas.json", "application/json"),
    ]:
        upload(
            s3,
            args.bucket,
            artifacts_dir / name,
            f"{S3_MODEL_PREFIX}/{name}",
            content_type,
        )

    base_url = f"https://{args.bucket}.s3.{args.region}.amazonaws.com"
    print("\nListo. URLs de ejemplo:")
    print(f"  {base_url}/{S3_DATA_PREFIX}/citibike_dashboard_sample.parquet")
    print(f"  {base_url}/{S3_DATA_PREFIX}/citibike_curated.snappy.parquet")
    print(f"  {base_url}/{S3_MODEL_PREFIX}/metricas.json")


if __name__ == "__main__":
    main()
