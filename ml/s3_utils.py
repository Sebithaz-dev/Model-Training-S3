import os
import boto3


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )


def download_from_s3(bucket, key, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3 = _get_s3_client()
    s3.download_file(bucket, key, local_path)
    print(f"  Descargado s3://{bucket}/{key} -> {local_path}")


def upload_to_s3(local_path, bucket, key):
    s3 = _get_s3_client()
    s3.upload_file(local_path, bucket, key)
    print(f"  Subido {local_path} -> s3://{bucket}/{key}")


def upload_artifacts(local_dir, bucket, prefix):
    for fname in ["modelo.pkl", "transformers.pkl", "metricas.json"]:
        local = os.path.join(local_dir, fname)
        if os.path.exists(local):
            upload_to_s3(local, bucket, f"{prefix.rstrip('/')}/{fname}")


def download_artifacts(bucket, prefix, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for fname in ["modelo.pkl", "transformers.pkl", "metricas.json"]:
        download_from_s3(
            bucket, f"{prefix.rstrip('/')}/{fname}",
            os.path.join(local_dir, fname)
        )
