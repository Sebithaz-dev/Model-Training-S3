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


def test_main_text_output(monkeypatch, capsys):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    code = health.main(["--skip-s3", "--skip-artifacts"])
    assert code == 0
    assert "[OK]" in capsys.readouterr().out


def test_main_strict_degraded(monkeypatch, tmp_path):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.setattr(health, "ARTIFACT_DIR", tmp_path)
    code = health.main(["--strict", "--skip-s3"])
    assert code == 1


class _FakeS3:
    def __init__(self):
        self.bucket_kwargs = {}
        self.object_kwargs = {}

    def head_bucket(self, **kwargs):
        self.bucket_kwargs = kwargs

    def head_object(self, **kwargs):
        self.object_kwargs = kwargs


class _FakeSts:
    def get_caller_identity(self):
        return {"Account": "123456789012"}


def test_check_s3_ok(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-test")
    monkeypatch.setenv("S3_MODEL_PREFIX", "models/")
    fake_s3 = _FakeS3()

    def fake_client(service_name, **kwargs):
        return _FakeSts() if service_name == "sts" else fake_s3

    monkeypatch.setattr("boto3.client", fake_client)
    result = health.check_s3()
    assert result["status"] == "ok"
    assert result["bucket"] == "bucket-test"
    assert fake_s3.bucket_kwargs["ExpectedBucketOwner"] == "123456789012"
    assert fake_s3.object_kwargs["Key"] == "models/metricas.json"


def test_check_s3_error(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-test")

    def fake_client(service_name, **kwargs):
        raise RuntimeError("sin credenciales")

    monkeypatch.setattr("boto3.client", fake_client)
    result = health.check_s3()
    assert result["status"] == "error"
    assert "sin credenciales" in result["detail"]


def test_print_report(capsys):
    report = {
        "status": "ok",
        "service": "svc",
        "version": "1",
        "checks": {"config": {"status": "ok", "detail": "ok"}},
    }
    health.print_report(report)
    out = capsys.readouterr().out
    assert "[OK] svc v1" in out
    assert "config: ok" in out
