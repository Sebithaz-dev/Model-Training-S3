"""Quality gate del modelo entrenado.

Evalua las metricas de ``ml/artefactos/metricas.json`` contra los umbrales
declarados en ``config/quality_gate.yaml``. El objetivo es bloquear la
publicacion de un modelo degradado en S3 (IE6 de la EP3).

Uso como CLI (exit code 1 si el gate falla):

    python -m ml.quality_gate --metrics ml/artefactos/metricas.json
    python -m ml.quality_gate --metrics metricas.json --json

Uso como libreria:

    from ml.quality_gate import enforce
    enforce(metricas)  # lanza QualityGateError si no cumple
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_GATE_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "quality_gate.yaml"
)


class QualityGateError(RuntimeError):
    """El modelo no cumple los umbrales minimos de calidad."""


@dataclass(frozen=True)
class QualityGate:
    enabled: bool
    thresholds: dict[str, float]
    min_test_size: int


@dataclass
class GateResult:
    passed: bool
    checks: list[dict] = field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        return [c["check"] for c in self.checks if not c["passed"]]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "failures": self.failures,
            "checks": self.checks,
        }


def load_gate(path: str | os.PathLike | None = None) -> QualityGate:
    """Carga y valida la configuracion del gate desde YAML."""
    gate_path = Path(path or os.getenv("QUALITY_GATE_CONFIG") or DEFAULT_GATE_PATH)
    if not gate_path.exists():
        raise FileNotFoundError(f"Quality gate no encontrado: {gate_path}")

    with gate_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    raw_thresholds = data.get("thresholds") or {}
    thresholds = {str(k): float(v) for k, v in raw_thresholds.items()}
    if not thresholds:
        raise ValueError("quality_gate.yaml debe declarar al menos un threshold")

    min_test_size = int(data.get("min_test_size", 0))
    if min_test_size < 0:
        raise ValueError("min_test_size no puede ser negativo")

    return QualityGate(
        enabled=bool(data.get("enabled", True)),
        thresholds=thresholds,
        min_test_size=min_test_size,
    )


def evaluate(metrics: dict, gate: QualityGate) -> GateResult:
    """Compara las metricas contra los umbrales del gate."""
    checks: list[dict] = []

    for name, minimo in gate.thresholds.items():
        valor = metrics.get(name)
        passed = isinstance(valor, (int, float)) and float(valor) >= minimo
        checks.append(
            {
                "check": f"{name}>={minimo}",
                "metric": name,
                "value": valor,
                "threshold": minimo,
                "passed": bool(passed),
                "detail": (
                    f"{name}={valor} cumple el minimo {minimo}"
                    if passed
                    else f"{name}={valor} no alcanza el minimo {minimo}"
                ),
            }
        )

    if gate.min_test_size:
        test_size = metrics.get("test_size")
        passed = isinstance(test_size, (int, float)) and int(test_size) >= gate.min_test_size
        checks.append(
            {
                "check": f"test_size>={gate.min_test_size}",
                "metric": "test_size",
                "value": test_size,
                "threshold": gate.min_test_size,
                "passed": bool(passed),
                "detail": (
                    f"test_size={test_size} es suficiente"
                    if passed
                    else f"test_size={test_size} es menor que {gate.min_test_size}"
                ),
            }
        )

    return GateResult(passed=all(c["passed"] for c in checks), checks=checks)


def enforce(
    metrics: dict,
    path: str | os.PathLike | None = None,
) -> GateResult:
    """Evalua el gate y lanza ``QualityGateError`` si no se cumple.

    Si el gate esta deshabilitado en la config, devuelve un resultado
    aprobado sin evaluar umbrales (util para experimentos locales).
    """
    gate = load_gate(path)
    if not gate.enabled:
        return GateResult(
            passed=True,
            checks=[{"check": "gate_enabled", "passed": True, "detail": "gate deshabilitado"}],
        )

    resultado = evaluate(metrics, gate)
    if not resultado.passed:
        detalle = "; ".join(resultado.failures)
        raise QualityGateError(f"Quality gate fallido: {detalle}")
    return resultado


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evalua el quality gate del modelo")
    parser.add_argument(
        "--metrics",
        type=argparse.FileType("r", encoding="utf-8"),
        default="ml/artefactos/metricas.json",
        help="Ruta a metricas.json (default: ml/artefactos/metricas.json)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Ruta al YAML del gate (default: config/quality_gate.yaml o $QUALITY_GATE_CONFIG)",
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv)

    with args.metrics as metrics_file:
        metrics = json.load(metrics_file)

    gate = load_gate(args.config)
    resultado = evaluate(metrics, gate) if gate.enabled else GateResult(passed=True)

    if args.json:
        print(json.dumps(resultado.to_dict(), indent=2, ensure_ascii=False))
    else:
        for check in resultado.checks:
            estado = "OK  " if check["passed"] else "FAIL"
            print(f"[{estado}] {check['detail']}")
        print("GATE: PASS" if resultado.passed else "GATE: FAIL")

    return 0 if resultado.passed else 1


if __name__ == "__main__":
    sys.exit(main())
