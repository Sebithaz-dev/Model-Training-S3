"""Tests de la exportacion de metricas a CloudWatch."""
from ml.metrics_export import build_metric_data, publish_model_metrics


def _metricas() -> dict:
    return {
        "roc_auc": 0.65,
        "pr_auc": 0.45,
        "gini": 0.30,
        "accuracy": 0.55,
        "recall": 0.70,
        "precision": 0.35,
        "f1_score": 0.47,
        "train_size": 1000,
        "test_size": 200,
        "features": ["hour"],
    }


def test_build_metric_data_incluye_metricas_numericas():
    data = build_metric_data(_metricas(), gate_passed=True)
    nombres = {d["MetricName"] for d in data}

    assert "roc_auc" in nombres
    assert "f1_score" in nombres
    assert "QualityGatePassed" in nombres
    assert "features" not in nombres
    gate = next(d for d in data if d["MetricName"] == "QualityGatePassed")
    assert gate["Value"] == 1.0


def test_build_metric_data_gate_fallido_publica_cero():
    data = build_metric_data(_metricas(), gate_passed=False)
    gate = next(d for d in data if d["MetricName"] == "QualityGatePassed")

    assert gate["Value"] == 0.0


def test_publish_sin_namespace_no_hace_nada(monkeypatch):
    monkeypatch.delenv("CLOUDWATCH_NAMESPACE", raising=False)

    assert publish_model_metrics(_metricas()) == 0


def test_publish_envia_metricas_al_cliente():
    llamadas = []

    class ClienteFalso:
        def put_metric_data(self, **kwargs):
            llamadas.append(kwargs)

    enviadas = publish_model_metrics(
        _metricas(),
        gate_passed=True,
        namespace="CitiBike/Model",
        client=ClienteFalso(),
    )

    assert enviadas > 0
    assert llamadas[0]["Namespace"] == "CitiBike/Model"
    assert llamadas[0]["MetricData"]


def test_publish_no_rompe_si_cloudwatch_falla(capsys):
    class ClienteRoto:
        def put_metric_data(self, **kwargs):
            raise RuntimeError("sin permisos")

    enviadas = publish_model_metrics(
        _metricas(), namespace="CitiBike/Model", client=ClienteRoto()
    )

    assert enviadas == 0
    assert "No se pudieron publicar" in capsys.readouterr().out
