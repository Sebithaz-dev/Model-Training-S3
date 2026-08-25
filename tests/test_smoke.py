"""Smoke tests basicos de importabilidad de los modulos del paquete."""


def test_import_train():
    import ml.train  # noqa: F401
    assert hasattr(ml.train, "entrenar")


def test_import_predict():
    import ml.predict  # noqa: F401
    assert hasattr(ml.predict, "Predictor")


def test_import_s3_utils():
    import ml.s3_utils  # noqa: F401
    assert hasattr(ml.s3_utils, "upload_artifacts")
