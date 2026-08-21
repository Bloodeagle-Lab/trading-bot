from __future__ import annotations

import pandas as pd
import pytest

from research.build_training_data import FEATURE_COLUMNS, _percentile_rank, build_labeled_dataset
from tests.conftest import make_ohlcv


# ---- _percentile_rank -----------------------------------------------------

def test_percentile_rank_orders_correctly():
    values = {"A": 0.10, "B": 0.05, "C": 0.20, "D": -0.10}
    assert _percentile_rank(values, "C") == pytest.approx(1.0)   # highest -> beats everyone
    assert _percentile_rank(values, "D") == pytest.approx(0.0)   # lowest -> beats no one
    assert _percentile_rank(values, "A") == pytest.approx(2 / 3)  # beats B, D (not C)


def test_percentile_rank_neutral_when_ticker_missing():
    assert _percentile_rank({"A": 0.1, "B": 0.2}, "C") == 0.5


def test_percentile_rank_neutral_when_fewer_than_two_peers():
    assert _percentile_rank({"A": 0.1}, "A") == 0.5
    assert _percentile_rank({}, "A") == 0.5


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


def test_build_labeled_dataset_includes_sleeve_and_ensemble_columns():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    for col in ("sleeve_momentum", "sleeve_trend", "sleeve_breakout",
                "sleeve_mean_reversion", "sleeve_relative_strength",
                "ensemble_score", "regime_confidence"):
        assert col in df.columns
    assert df["sleeve_momentum"].between(-1.0, 1.0).all()
    assert df["ensemble_score"].between(-1.0, 1.0).all()
    assert df["regime_confidence"].between(0.0, 1.0).all()


def test_build_labeled_dataset_regime_onehot_matches_regime_state():
    from quant.regime import VALID_STATES
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    onehot_cols = [f"regime_{s}" for s in VALID_STATES]
    for col in onehot_cols:
        assert col in df.columns
    # exactly one regime column is 1.0 per row, matching regime_state
    assert (df[onehot_cols].sum(axis=1) == 1.0).all()
    for state in VALID_STATES:
        matching = df[df["regime_state"] == state]
        if len(matching):
            assert (matching[f"regime_{state}"] == 1.0).all()


def test_build_labeled_dataset_ensemble_respects_regime_weights():
    # weighting everything to zero except one sleeve should make
    # ensemble_score track that sleeve's own score exactly
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    weights = {state: {"momentum": 1.0, "trend": 0.0, "breakout": 0.0, "mean_reversion": 0.0, "relative_strength": 0.0}
               for state in ("STRONG_TREND", "CHOPPY", "HIGH_VOL", "RISK_OFF", "TRANSITION")}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10, regime_weights=weights)
    assert len(df) > 0
    # compute_ensemble rounds to 3dp; sleeve_momentum here is unrounded
    assert (df["ensemble_score"] - df["sleeve_momentum"]).abs().max() < 1e-3


def test_build_labeled_dataset_cross_sectional_columns_present_and_bounded():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2), "BBB": make_ohlcv(n=280, seed=3)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    for col in ("cross_sectional_rank_ret20", "cross_sectional_rank_ensemble"):
        assert col in df.columns
        assert df[col].between(0.0, 1.0).all()


def test_build_labeled_dataset_cross_sectional_rank_differentiates_tickers_on_same_date():
    # Three tickers with clearly different momentum -> their cross-sectional
    # ranks on any shared date should NOT all collapse to the neutral 0.5.
    price_data = {
        "SPY": make_ohlcv(n=280, seed=1, drift=0.0),
        "STRONG": make_ohlcv(n=280, seed=2, drift=0.004),
        "WEAK": make_ohlcv(n=280, seed=3, drift=-0.004),
        "MID": make_ohlcv(n=280, seed=4, drift=0.0),
    }
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    ranks = df.groupby("ticker")["cross_sectional_rank_ret20"].mean()
    assert ranks["STRONG"] > ranks["MID"] > ranks["WEAK"]


def test_build_labeled_dataset_max_high_and_min_low_bracket_entry_reasonably():
    price_data = {"SPY": make_ohlcv(n=280, seed=1), "AAA": make_ohlcv(n=280, seed=2)}
    df = build_labeled_dataset(price_data, index_symbol="SPY", horizon_days=10)
    assert len(df) > 0
    # the forward high must be >= forward low, always
    assert (df["max_high_in_horizon"] >= df["min_low_in_horizon"]).all()
