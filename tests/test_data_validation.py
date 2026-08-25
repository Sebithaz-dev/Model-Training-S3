"""Tests para ml.data_validation."""
import pandas as pd
import pytest

from ml.data_validation import (
    DataValidationError,
    validate_dataframe,
)


def _valid_row(**overrides):
    base = dict(
        tripduration=600,
        starttime=pd.Timestamp("2024-07-15 17:00:00"),
        start_station_id=3160,
        usertype="Subscriber",
        gender="Male",
        birth_year=1990,
        year=2024,
        hour=17,
        month=7,
        dayofweek=0,
        is_weekend=0,
    )
    base.update(overrides)
    return base


def _valid_df(**overrides):
    return pd.DataFrame([_valid_row(**overrides)])


def test_valid_dataframe_passes():
    result = validate_dataframe(_valid_df())
    assert result.valid
    assert result.errors == []


def test_missing_required_column_fails():
    df = _valid_df().drop(columns=["tripduration"])
    result = validate_dataframe(df)
    assert not result.valid
    assert any("tripduration" in e for e in result.errors)


def test_wrong_dtype_fails():
    df = _valid_df()
    df["hour"] = "mañana"
    result = validate_dataframe(df)
    assert not result.valid
    assert any("hour" in e for e in result.errors)


def test_out_of_range_fails():
    df = _valid_df(hour=25)
    result = validate_dataframe(df)
    assert not result.valid
    assert any("hour" in e for e in result.errors)


def test_unallowed_categorical_fails():
    df = _valid_df(usertype="Alien")
    result = validate_dataframe(df)
    assert not result.valid
    assert any("usertype" in e for e in result.errors)


def test_nulls_produce_warning_not_error():
    df = _valid_df()
    df.loc[0, "birth_year"] = pd.NA
    result = validate_dataframe(df)
    assert result.valid
    assert any("birth_year" in w for w in result.warnings)


def test_empty_dataframe_fails():
    result = validate_dataframe(pd.DataFrame())
    assert not result.valid


def test_raise_if_invalid_raises():
    df = _valid_df().drop(columns=["tripduration"])
    result = validate_dataframe(df)
    with pytest.raises(DataValidationError):
        result.raise_if_invalid()


def test_raise_if_invalid_passes_when_valid():
    validate_dataframe(_valid_df()).raise_if_invalid()
