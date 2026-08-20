from __future__ import annotations

import pandas as pd
import pytest

from quant.ensemble import SetupQuality, compute_ensemble, technical_score_from_ensemble


def test_ensemble_score_isolates_single_weighted_sleeve():
    row = pd.Series({"ret_20d": 0.10, "ret_60d": 0.20, "volume_ratio": 1.2, "relative_strength_20": 0.05})
    weights = {"TEST_REGIME": {"momentum": 1.0, "trend": 0.0, "breakout": 0.0, "mean_reversion": 0.0, "relative_strength": 0.0}}
    result = compute_ensemble("XYZ", row, "TEST_REGIME", weights)
    assert result.ensemble_score == pytest.approx(result.sleeve_scores["momentum"], abs=1e-3)


def test_ensemble_defaults_to_equal_weights_for_unknown_regime():
    row = pd.Series({})
    result = compute_ensemble("XYZ", row, "UNKNOWN_REGIME", regime_weights={})
    # every sleeve must still be represented with weight 1.0 when the regime
    # isn't in the table (equal-weighted fallback), so the ensemble score is
    # exactly the plain average of the per-sleeve scores on this row (not
    # necessarily 0 — several sleeves have nonzero defaults on an empty row,
    # e.g. breakout treats a missing dist-from-high as "at the high").
    assert set(result.weights_used.keys()) == set(result.sleeve_scores.keys())
    assert all(w == 1.0 for w in result.weights_used.values())
    expected = sum(result.sleeve_scores.values()) / len(result.sleeve_scores)
    assert result.ensemble_score == pytest.approx(expected, abs=1e-3)


def test_ensemble_respects_disabled_sleeves():
    row = pd.Series({})
    result = compute_ensemble(
        "XYZ", row, "R", regime_weights={},
        sleeve_enabled={"momentum": True, "trend": False, "breakout": False, "mean_reversion": False, "relative_strength": False},
    )
    assert set(result.sleeve_scores.keys()) == {"momentum"}


def test_ensemble_render_includes_ticker_and_score():
    row = pd.Series({})
    result = compute_ensemble("ABC", row, "R", regime_weights={})
    text = result.render()
    assert "Ticker: ABC" in text
    assert "Ensemble Score:" in text


@pytest.mark.parametrize("ensemble_score,expected", [(-1.0, 0.0), (0.0, 50.0), (1.0, 100.0)])
def test_technical_score_from_ensemble_mapping(ensemble_score, expected):
    assert technical_score_from_ensemble(ensemble_score) == pytest.approx(expected)


def test_setup_quality_overall_quality_is_weighted_average():
    sq = SetupQuality(
        ticker="XYZ", technical=80, sector=80, catalyst=80,
        liquidity=80, risk_quality=80, portfolio_fit=80, ml_probability=0.6,
    )
    assert sq.overall_quality == pytest.approx(80.0)


def test_setup_quality_render_includes_ml_probability_when_present():
    sq = SetupQuality(ticker="X", technical=1, sector=1, catalyst=1, liquidity=1, risk_quality=1, portfolio_fit=1, ml_probability=0.42)
    assert "ML probability: 0.42" in sq.render()


def test_setup_quality_render_omits_ml_probability_when_none():
    sq = SetupQuality(ticker="X", technical=1, sector=1, catalyst=1, liquidity=1, risk_quality=1, portfolio_fit=1, ml_probability=None)
    assert "ML probability" not in sq.render()
