"""Tests para ml.features."""
import numpy as np
import pandas as pd
import pytest

from ml.features import add_time_features


def test_add_time_features_crea_columnas_y_flags():
    df = pd.DataFrame(
        {
            "hour": [0, 8, 17, 22],
            "month": [1, 7, 12, 6],
            "dayofweek": [0, 3, 5, 6],
        }
    )

    out = add_time_features(df)

    assert {
        "hour_sin",
        "hour_cos",
        "month_sin",
        "month_cos",
        "dayofweek_sin",
        "dayofweek_cos",
        "is_rush_hour",
        "is_night",
    } <= set(out.columns)
    assert out.loc[0, "hour_sin"] == pytest.approx(0.0)
    assert out.loc[0, "hour_cos"] == pytest.approx(1.0)
    assert out.loc[0, "is_night"] == 1
    assert out.loc[0, "is_rush_hour"] == 0
    assert out.loc[1, "is_rush_hour"] == 1
    assert out.loc[2, "is_rush_hour"] == 1
    assert out.loc[3, "is_night"] == 1
    assert out.loc[0, "month_sin"] == pytest.approx(0.0)
    assert out.loc[0, "month_cos"] == pytest.approx(1.0)
    assert out.loc[0, "dayofweek_sin"] == pytest.approx(0.0)
    assert out.loc[0, "dayofweek_cos"] == pytest.approx(1.0)


def test_add_time_features_no_muta_el_dataframe_original():
    df = pd.DataFrame({"hour": [8], "month": [7], "dayofweek": [3]})
    add_time_features(df)
    assert "hour_sin" not in df.columns


def test_add_time_features_rangos_ciclicos():
    df = pd.DataFrame(
        {
            "hour": list(range(24)),
            "month": [1] * 24,
            "dayofweek": [0] * 24,
        }
    )
    out = add_time_features(df)
    assert np.all(out["hour_sin"].between(-1, 1))
    assert np.all(out["hour_cos"].between(-1, 1))
    assert out["is_rush_hour"].isin([0, 1]).all()
    assert out["is_night"].isin([0, 1]).all()
