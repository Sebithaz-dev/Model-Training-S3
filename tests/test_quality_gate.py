"""Tests del quality gate del modelo (config, evaluacion y CLI)."""
import json

import pytest

from ml.quality_gate import (
    DEFAULT_GATE_PATH,
    GateResult,
    QualityGateError,
    enforce,
    evaluate,
    load_gate,
    main,
)


def _metricas_validas() -> dict:
    return {
        "roc_auc": 0.65,
        "pr_auc": 0.45,
        "f1_score": 0.47,
        "recall": 0.70,
        "precision": 0.35,
        "accuracy": 0.55,
        "test_size": 5000,
    }


def test_load_gate_por_defecto():
    gate = load_gate(DEFAULT_GATE_PATH)

    assert gate.enabled is True
    assert gate.min_test_size > 0
    assert "roc_auc" in gate.thresholds


def test_evaluate_aprueba_metricas_del_baseline():
    resultado = evaluate(_metricas_validas(), load_gate())

    assert resultado.passed is True
    assert resultado.failures == []
    assert {c["metric"] for c in resultado.checks} >= {"roc_auc", "f1_score", "test_size"}


def test_evaluate_falla_por_metrica_bajo_umbral():
    metricas = _metricas_validas() | {"roc_auc": 0.10}

    resultado = evaluate(metricas, load_gate())

    assert resultado.passed is False
    assert any(f.startswith("roc_auc>=") for f in resultado.failures)


def test_evaluate_falla_si_falta_metrica():
    metricas = _metricas_validas()
    metricas.pop("f1_score")

    resultado = evaluate(metricas, load_gate())

    assert resultado.passed is False
    assert any(f.startswith("f1_score>=") for f in resultado.failures)


def test_evaluate_falla_por_test_size_insuficiente():
    metricas = _metricas_validas() | {"test_size": 5}

    resultado = evaluate(metricas, load_gate())

    assert resultado.passed is False
    assert any("test_size" in f for f in resultado.failures)


def test_enforce_lanza_error_con_regresion():
    metricas = _metricas_validas() | {"pr_auc": 0.01}

    with pytest.raises(QualityGateError, match="pr_auc"):
        enforce(metricas)


def test_enforce_gate_deshabilitado_no_evalua(tmp_path):
    gate_path = tmp_path / "gate.yaml"
    gate_path.write_text("enabled: false\nthresholds:\n  roc_auc: 0.99\n", encoding="utf-8")

    resultado = enforce({"roc_auc": 0.1}, gate_path)

    assert resultado.passed is True


def test_gate_result_to_dict():
    resultado = GateResult(passed=False, checks=[{"check": "x", "passed": False}])

    assert resultado.to_dict()["passed"] is False
    assert resultado.to_dict()["failures"] == ["x"]


def _escribir_metricas(tmp_path, metricas: dict):
    path = tmp_path / "metricas.json"
    path.write_text(json.dumps(metricas), encoding="utf-8")
    return path


def test_cli_exit_0_si_pasa(tmp_path, capsys):
    path = _escribir_metricas(tmp_path, _metricas_validas())

    assert main(["--metrics", str(path)]) == 0
    assert "GATE: PASS" in capsys.readouterr().out


def test_cli_exit_1_si_falla(tmp_path, capsys):
    path = _escribir_metricas(tmp_path, _metricas_validas() | {"roc_auc": 0.01})

    assert main(["--metrics", str(path), "--json"]) == 1
    assert '"passed": false' in capsys.readouterr().out
