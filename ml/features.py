"""Ingenieria de features temporales compartida por entrenamiento e inferencia."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega features ciclicas y flags de horario.

    Las formulas deben coincidir exactamente con las usadas por el dashboard
    (``app/services/ml_service.py``) para evitar skew entre train y serving.
    """
    out = df.copy()
    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["month_sin"] = np.sin(2 * np.pi * (out["month"] - 1) / 12)
    out["month_cos"] = np.cos(2 * np.pi * (out["month"] - 1) / 12)
    out["dayofweek_sin"] = np.sin(2 * np.pi * out["dayofweek"] / 7)
    out["dayofweek_cos"] = np.cos(2 * np.pi * out["dayofweek"] / 7)
    out["is_rush_hour"] = (
        ((out["hour"] >= 7) & (out["hour"] <= 9))
        | ((out["hour"] >= 17) & (out["hour"] <= 19))
    ).astype(int)
    out["is_night"] = ((out["hour"] <= 5) | (out["hour"] >= 22)).astype(int)
    return out
