"""Publica las metricas del modelo en Amazon CloudWatch.

El pipeline de CI/CD y las tareas de entrenamiento llaman a este modulo
cuando existe la variable ``CLOUDWATCH_NAMESPACE`` (por ejemplo
``CitiBike/Model``). Sin esa variable el modulo no hace nada, asi que los
tests y las corridas locales no necesitan AWS.

Las metricas quedan disponibles para el dashboard de Grafana/CloudWatch de
la EP3 (IE3): ROC-AUC, F1, estado del quality gate, tamano de test, etc.
"""
from __future__ import annotations

import os

DEFAULT_NAMESPACE = "CitiBike/Model"

# Metricas numericas de metricas.json que se publican en CloudWatch.
_MODEL_METRICS = (
    "roc_auc",
    "pr_auc",
    "gini",
    "accuracy",
    "recall",
    "precision",
    "f1_score",
    "test_size",
    "train_size",
)


def build_metric_data(metrics: dict, gate_passed: bool | None = None) -> list[dict]:
    """Construye la lista de MetricData para ``put_metric_data``."""
    data: list[dict] = []
    for name in _MODEL_METRICS:
        value = metrics.get(name)
        if isinstance(value, (int, float)):
            data.append(
                {
                    "MetricName": name,
                    "Value": float(value),
                    "Unit": "Count" if name.endswith("_size") else "None",
                }
            )

    if gate_passed is not None:
        data.append(
            {
                "MetricName": "QualityGatePassed",
                "Value": 1.0 if gate_passed else 0.0,
                "Unit": "None",
            }
        )
    return data


def publish_model_metrics(
    metrics: dict,
    gate_passed: bool | None = None,
    namespace: str | None = None,
    region: str | None = None,
    client=None,
) -> int:
    """Publica las metricas en CloudWatch y devuelve cuantas se enviaron.

    Es *best effort*: no levanta excepciones si CloudWatch no esta
    disponible, porque la observabilidad nunca debe impedir el despliegue.
    Devuelve 0 cuando no hay namespace configurado.
    """
    namespace = namespace or os.getenv("CLOUDWATCH_NAMESPACE")
    if not namespace:
        return 0

    data = build_metric_data(metrics, gate_passed)
    if not data:
        return 0

    try:
        if client is None:
            import boto3

            client = boto3.client(
                "cloudwatch",
                region_name=region or os.getenv("AWS_REGION", "us-east-1"),
            )
        client.put_metric_data(Namespace=namespace, MetricData=data)
    except Exception as exc:  # noqa: BLE001 - no debe romper el pipeline
        print(f"[cloudwatch] No se pudieron publicar metricas: {exc}")
        return 0

    print(f"[cloudwatch] {len(data)} metricas publicadas en {namespace}")
    return len(data)
