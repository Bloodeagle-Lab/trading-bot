from __future__ import annotations

import pandas as pd
import pytest

from quant.regime import CHOPPY, HIGH_VOL, RISK_OFF, STRONG_TREND, TRANSITION, classify_regime


def _row(**kwargs) -> pd.Series:
    base = {
        "price_above_sma50": 1, "price_above_sma200": 1, "sma50_above_sma200": 1,
        "sma20_slope_5d": 0.0, "volatility_20": 0.12,
    }
    base.update(kwargs)
    return pd.Series(base)


def test_strong_trend_with_healthy_breadth():
    row = _row(sma20_slope_5d=0.02)
    result = classify_regime(row, vix_level=15.0, breadth_pct_above_50dma=0.75)
    assert result.state == STRONG_TREND
    assert 0.0 <= result.confidence <= 1.0


def test_risk_off_on_broad_weakness():
    row = _row(price_above_sma50=0, price_above_sma200=0, sma50_above_sma200=0, sma20_slope_5d=-0.03)
    result = classify_regime(row, vix_level=20.0, breadth_pct_above_50dma=0.20)
    assert result.state == RISK_OFF


def test_high_vol_on_extreme_vix():
    row = _row(sma20_slope_5d=0.01, volatility_20=0.10)
    result = classify_regime(row, vix_level=35.0, breadth_pct_above_50dma=0.55)
    assert result.state == HIGH_VOL


def test_choppy_on_weak_ambiguous_trend():
    row = _row(price_above_sma50=1, price_above_sma200=0, sma50_above_sma200=0, sma20_slope_5d=0.0)
    result = classify_regime(row, vix_level=16.0, breadth_pct_above_50dma=0.50)
    assert result.state == CHOPPY


def test_confidence_is_bounded_and_state_is_always_valid():
    row = _row()
    result = classify_regime(row)  # no vix, no breadth -> low data completeness
    assert result.state in (STRONG_TREND, CHOPPY, HIGH_VOL, RISK_OFF, TRANSITION)
    assert 0.0 <= result.confidence <= 1.0


def test_regime_confidence_never_negative_or_above_one_across_grid():
    # sweep a range of synthetic inputs and make sure confidence stays valid
    for slope in (-0.05, -0.01, 0.0, 0.01, 0.05):
        for vix in (None, 12.0, 25.0, 40.0):
            for breadth in (None, 0.1, 0.5, 0.9):
                row = _row(sma20_slope_5d=slope)
                result = classify_regime(row, vix_level=vix, breadth_pct_above_50dma=breadth)
                assert 0.0 <= result.confidence <= 1.0
