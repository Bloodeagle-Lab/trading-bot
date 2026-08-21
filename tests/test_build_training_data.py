from __future__ import annotations

import pandas as pd
import pytest

from research.build_training_data import FEATURE_COLUMNS, build_labeled_dataset
from tests.conftest import make_ohlcv


def test_build_labeled_dataset_produces_expected_columns():
    price_data = {
        "SPY": make_ohlcv(n=280, seed=1),
        "AAA": make_ohlcv(n=280, seed=2),
    }
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)

    assert len(df) > 0
    for col in FEATURE_COLUMNS:
        assert col in df.columns
    for col in ("ticker", "date", "regime_state", "entry_price", "stop_price",
                "max_high_in_horizon", "min_low_in_horizon"):
        assert col in df.columns
    assert (df["ticker"] == "AAA").all()  # SPY (the index) never becomes a row itself


def test_build_labeled_dataset_skips_rows_without_enough_warmup():
    # Only ~60 bars -> nowhere near the 200-day SMA warmup -> zero rows,
    # not a crash on NaN features.
    price_data = {"SPY": make_ohlcv(n=60, seed=1), "AAA": make_ohlcv(n=60, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) == 0


def test_build_labeled_dataset_skips_rows_without_enough_forward_horizon():
    # Enough warmup, but essentially no room left for a 10-day forward label
    # window -> the last ~10 rows must be excluded, not silently truncated.
    price_data = {"SPY": make_ohlcv(n=205, seed=1), "AAA": make_ohlcv(n=205, seed=2)}
    df_short_horizon = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=1)
    df_long_horizon = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=20)
    assert len(df_short_horizon) > len(df_long_horizon)


def test_build_labeled_dataset_stop_price_below_entry_by_atr_multiple():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10, stop_atr_multiple=2.0)
    assert len(df) > 0
    assert (df["stop_price"] < df["entry_price"]).all()


def test_build_labeled_dataset_no_nans_in_feature_columns():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    assert not df[FEATURE_COLUMNS].isna().any().any()


def test_build_labeled_dataset_regime_state_is_valid():
    from quant.regime import VALID_STATES
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    assert df["regime_state"].isin(VALID_STATES).all()


def test_build_labeled_dataset_handles_multiple_tickers():
    price_data = {
        "SPY": make_ohlcv(n=280, seed=1),
        "AAA": make_ohlcv(n=280, seed=2),
        "BBB": make_ohlcv(n=280, seed=3),
    }
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert set(df["ticker"].unique()) == {"AAA", "BBB"}


def test_build_labeled_dataset_max_high_and_min_low_bracket_entry_reasonably():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    # the forward high must be >= forward low, always
    assert (df["max_high_in_horizon"] >= df["min_low_in_horizon"]).all()
