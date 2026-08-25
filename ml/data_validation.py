"""Validacion del schema y calidad de los datos de entrada.

Antes de entrenar, se verifica que el Parquet contenga las columnas
esperadas y rangos coherentes. Cualquier desviacion lanza
``DataValidationError`` para abortar el pipeline temprano y evitar
entrenar sobre datos corruptos.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

import pandas as pd


class DataValidationError(ValueError):
    """Los datos de entrada no cumplen el contrato esperado."""


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    allowed: tuple | None = None


# Contrato del dataset curado de Citi Bike.
EXPECTED_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec("tripduration", "numeric", min_value=0),
    ColumnSpec("starttime", "datetime"),
    ColumnSpec("start_station_id", "numeric", min_value=0),
    ColumnSpec("usertype", "object", allowed=("Customer", "Subscriber")),
    ColumnSpec("gender", "object", allowed=("Male", "Female", "Unknown")),
    ColumnSpec("birth_year", "numeric", min_value=1900, max_value=2025),
    ColumnSpec("year", "numeric", min_value=2000, max_value=2025),
    ColumnSpec("hour", "numeric", min_value=0, max_value=23),
    ColumnSpec("month", "numeric", min_value=1, max_value=12),
    ColumnSpec("dayofweek", "numeric", min_value=0, max_value=6),
    ColumnSpec("is_weekend", "numeric", min_value=0, max_value=1),
)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise DataValidationError(
                "Validacion de datos fallida:\n" + "\n".join(f"  - {e}" for e in self.errors)
            )


def _is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series)


def _is_datetime(series: pd.Series) -> bool:
    return pd.api.types.is_datetime64_any_dtype(series)


def _is_string_like(series: pd.Series) -> bool:
    return (
        pd.api.types.is_object_dtype(series)
        or pd.api.types.is_string_dtype(series)
    )


def validate_dataframe(df: pd.DataFrame, columns: Iterable[ColumnSpec] = EXPECTED_COLUMNS) -> ValidationResult:
    """Valida ``df`` contra el contrato ``columns``.

    - Columnas requeridas presentes.
    - Tipos compatibles (numeric / datetime / object).
    - Rangos numericos y valores categoricos permitidos.
    - Avisos (no fatales) para nulos o cardinalidad sospechosa.
    """
    result = ValidationResult(valid=True)
    available = set(df.columns)

    for spec in columns:
        if spec.name not in available:
            if spec.required:
                result.errors.append(f"Columna requerida ausente: '{spec.name}'")
                result.valid = False
            continue

        series = df[spec.name]

        # Tipo
        if spec.dtype == "numeric" and not _is_numeric(series):
            result.errors.append(
                f"'{spec.name}' debe ser numerico, es {series.dtype}"
            )
            result.valid = False
        elif spec.dtype == "datetime" and not _is_datetime(series):
            result.errors.append(
                f"'{spec.name}' debe ser datetime, es {series.dtype}"
            )
            result.valid = False
        elif spec.dtype == "object" and not _is_string_like(series):
            result.errors.append(
                f"'{spec.name}' debe ser object/str, es {series.dtype}"
            )
            result.valid = False

        # Nulos
        null_count = int(series.isna().sum())
        if null_count > 0:
            result.warnings.append(
                f"'{spec.name}' contiene {null_count} nulos ({null_count / len(df):.1%})"
            )

        # Rangos
        if spec.min_value is not None and _is_numeric(series):
            mn = float(series.min())
            if mn < spec.min_value:
                result.errors.append(
                    f"'{spec.name}' tiene valor minimo {mn} < {spec.min_value}"
                )
                result.valid = False
        if spec.max_value is not None and _is_numeric(series):
            mx = float(series.max())
            if mx > spec.max_value:
                result.errors.append(
                    f"'{spec.name}' tiene valor maximo {mx} > {spec.max_value}"
                )
                result.valid = False

        # Valores permitidos
        if spec.allowed is not None:
            unique = set(series.dropna().astype(str).unique())
            unexpected = unique - {str(v) for v in spec.allowed}
            if unexpected:
                result.errors.append(
                    f"'{spec.name}' contiene valores no permitidos: {sorted(unexpected)}"
                )
                result.valid = False

    if len(df) == 0:
        result.errors.append("El dataframe esta vacio")
        result.valid = False

    return result
