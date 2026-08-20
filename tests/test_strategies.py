from __future__ import annotations

import pandas as pd
import pytest

from quant.strategies import (
    SLEEVE_FUNCS, breakout_score, mean_reversion_score, momentum_score,
    run_all_sleeves, trend_score,
)


def test_momentum_score_positive_for_strong_uptrend():
    row = pd.Series({"ret_20d": 0.15, "ret_60d": 0.30, "volume_ratio": 1.5, "relative_strength_20": 0.08})
    result = momentum_score(row)
    assert result.score > 0
    assert -1.0 <= result.score <= 1.0
    assert "momentum" == result.name


def test_momentum_score_negative_for_strong_downtrend():
    row = pd.Series({"ret_20d": -0.15, "ret_60d": -0.30, "volume_ratio": 0.6, "relative_strength_20": -0.08})
    assert momentum_score(row).score < 0


def test_momentum_score_handles_missing_fields_via_defaults():
    row = pd.Series({})
    result = momentum_score(row)
    assert result.score == pytest.approx(0.0, abs=1e-6)


def test_trend_score_bounded():
    row = pd.Series({
        "price_above_sma50": 1, "price_above_sma200": 1, "sma50_above_sma200": 1,
        "adx_14": 35, "atr_pct": 0.02, "sma20_slope_5d": 0.01,
    })
    result = trend_score(row)
    assert -1.0 <= result.score <= 1.0
    assert result.score > 0


def test_breakout_score_higher_near_new_high_with_volume():
    near_high = pd.Series({"dist_from_high_20_pct": -0.01, "new_high_break": 1, "volume_ratio": 2.0, "range_width_pct": 0.05, "atr_pct": 0.02})
    far_from_high = pd.Series({"dist_from_high_20_pct": -0.30, "new_high_break": 0, "volume_ratio": 0.8, "range_width_pct": 0.05, "atr_pct": 0.02})
    assert breakout_score(near_high).score > breakout_score(far_from_high).score


def test_mean_reversion_score_favors_oversold_dip():
    oversold = pd.Series({"zscore_20": -2.0, "rsi_14": 20.0, "volatility_20": 0.10})
    overbought = pd.Series({"zscore_20": 2.0, "rsi_14": 80.0, "volatility_20": 0.10})
    assert mean_reversion_score(oversold).score > 0
    assert mean_reversion_score(overbought).score < 0


def test_run_all_sleeves_returns_every_sleeve_by_default():
    row = pd.Series({})
    out = run_all_sleeves(row)
    assert set(out.keys()) == set(SLEEVE_FUNCS.keys())


def test_run_all_sleeves_respects_enabled_flags():
    row = pd.Series({})
    out = run_all_sleeves(row, enabled={"momentum": True, "trend": False, "breakout": False, "mean_reversion": False, "relative_strength": False})
    assert set(out.keys()) == {"momentum"}
