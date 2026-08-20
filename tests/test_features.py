from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant.features import (
    atr, compute_features, gap_pct, ma_structure, rsi, sma, zscore,
)
from tests.conftest import make_ohlcv


def test_sma_matches_manual_rolling_mean():
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = sma(close, 3)
    assert out.iloc[2] == pytest.approx(2.0)
    assert out.iloc[4] == pytest.approx(4.0)
    assert np.isnan(out.iloc[1])


def test_rsi_is_bounded_and_high_for_mostly_up_trend():
    # A strictly monotonic series has zero losses, which makes rs = gain/0 ->
    # NaN -> the function's documented neutral fillna(50), not "near 100" —
    # that's the correct edge-case behavior, not what this test is after.
    # Adding rare, tiny pullbacks keeps avg_loss nonzero so RSI reads high
    # without hitting that divide-by-zero fallback.
    increments = np.ones(80)
    increments[::7] = -0.5   # a real down day roughly one week in seven
    close = pd.Series(1 + np.cumsum(increments))
    out = rsi(close, 14)
    assert out.dropna().between(0, 100).all()
    assert out.iloc[-1] > 80


def test_rsi_neutral_when_no_data():
    close = pd.Series([100.0] * 5)
    out = rsi(close, 14)
    # not enough periods for a real read -> fillna(50) neutral default
    assert (out == 50).all()


def test_atr_nonnegative_and_warms_up():
    df = make_ohlcv(n=60)
    out = atr(df, 14)
    assert out.dropna().ge(0).all()
    assert out.iloc[:13].isna().all()  # min_periods=14 -> first 13 are NaN


def test_ma_structure_flags_match_price_vs_sma():
    df = make_ohlcv(n=260)
    out = ma_structure(df["close"])
    valid = out.dropna(subset=["sma_20"])
    expected = (df["close"].loc[valid.index] > valid["sma_20"]).astype(int)
    pd.testing.assert_series_equal(valid["price_above_sma20"], expected, check_names=False)


def test_gap_pct_zero_when_open_equals_prev_close():
    df = pd.DataFrame({
        "open": [10.0, 10.0, 11.0],
        "high": [10.5, 10.5, 11.5],
        "low": [9.5, 9.5, 10.5],
        "close": [10.0, 10.0, 11.0],
        "volume": [1000, 1000, 1000],
    })
    out = gap_pct(df)
    assert out.iloc[1] == pytest.approx(0.0)
    assert out.iloc[2] == pytest.approx(0.1)  # (11-10)/10


def test_zscore_zero_at_the_rolling_mean():
    close = pd.Series([100.0] * 19 + [100.0])
    out = zscore(close, 20)
    # constant series -> std is 0 -> NaN (division guarded, not a crash)
    assert np.isnan(out.iloc[-1]) or out.iloc[-1] == 0


def test_compute_features_requires_ohlcv_columns():
    bad = pd.DataFrame({"close": [1, 2, 3]})
    with pytest.raises(ValueError):
        compute_features(bad)


def test_compute_features_attaches_relative_strength_only_with_benchmark():
    df = make_ohlcv(n=100)
    bench = make_ohlcv(n=100, seed=99)["close"]
    without = compute_features(df)
    with_bench = compute_features(df, benchmark_close=bench)
    assert "relative_strength_20" not in without.columns
    assert "relative_strength_20" in with_bench.columns
    assert (with_bench["feature_version"] == "1.0.0").all()
