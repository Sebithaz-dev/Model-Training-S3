"""Tests para ml.health."""
import json

import joblib
from sklearn.linear_model import LogisticRegression

from ml import health


def test_check_config_ok():
    result = health.check_config()
    assert result["status"] == "ok"
    assert result["model_class"] == "sklearn.linear_model.LogisticRegression"


def test_check_artifacts_missing(tmp_path):
    result = health.check_artifacts(tmp_path)
    assert result["status"] == "degraded"
    assert set(result["missing"]) == set(health.ARTIFACT_FILES)
    assert health.exit_code_for({"status": "degraded"}) == 0
    assert health.exit_code_for({"status": "degraded"}, strict=True) == 1


def test_check_artifacts_ok(tmp_path):
    joblib.dump(LogisticRegression(), tmp_path / "modelo.pkl")
    joblib.dump({"scaler": None}, tmp_path / "transformers.pkl")
    (tmp_path / "metricas.json").write_text(
        json.dumps({"accuracy": 0.9}), encoding="utf-8"
    )

    result = health.check_artifacts(tmp_path)
    assert result["status"] == "ok"
    assert result["metrics_keys"] == ["accuracy"]


def test_check_artifacts_corrupt(tmp_path):
    (tmp_path / "modelo.pkl").write_text("no es un pickle", encoding="utf-8")
    (tmp_path / "transformers.pkl").write_text("no es un pickle", encoding="utf-8")
    (tmp_path / "metricas.json").write_text("{}", encoding="utf-8")

    result = health.check_artifacts(tmp_path)
    assert result["status"] == "error"
    assert health.exit_code_for({"status": "error"}) == 1


def test_check_s3_skipped_without_bucket(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    result = health.check_s3()
    assert result["status"] == "skipped"


def test_build_report_skips_checks(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    report = health.build_report(skip_s3=True, skip_artifacts=True)
    assert report["service"] == health.SERVICE_NAME
    assert report["checks"]["config"]["status"] == "ok"
    assert report["checks"]["artifacts"]["status"] == "skipped"
    assert report["checks"]["s3"]["status"] == "skipped"
    assert report["status"] == "ok"


def test_main_json_output(monkeypatch, capsys):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    code = health.main(["--json", "--skip-s3", "--skip-artifacts"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
