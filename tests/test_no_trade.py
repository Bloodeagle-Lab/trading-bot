from __future__ import annotations

import pytest

from quant.no_trade import Candidate, evaluate_no_trade
from tests.conftest import make_config


def _good_candidate(**overrides) -> Candidate:
    base = dict(
        ticker="XYZ", ensemble_score=0.7, ml_probability=0.65,
        regime_state="STRONG_TREND", regime_confidence=0.8, setup_quality=85,
        sleeve_scores={"momentum": 0.6, "trend": 0.5, "breakout": 0.4, "mean_reversion": 0.1, "relative_strength": 0.5},
        spread_pct=0.1, liquidity_ok=True, portfolio_concentration_ok=True,
        catalyst_verified=True, reward_risk_ratio=2.5, market_risk_off_gate_active=False,
    )
    base.update(overrides)
    return Candidate(**base)


def test_all_gates_pass_returns_pass():
    result = evaluate_no_trade(_good_candidate(), make_config())
    assert result.decision == "PASS"


def test_ml_probability_below_threshold_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(ml_probability=0.30), make_config())
    assert result.decision == "NO-TRADE"
    assert any("probability" in r for r in result.reasons)


def test_missing_ml_probability_treated_as_insufficient_evidence():
    c = make_config({"no_trade": {"probability_threshold": "VALIDATE"}})
    result = evaluate_no_trade(_good_candidate(ml_probability=None), c)
    assert result.decision == "NO-TRADE"
    assert any("no ML probability" in r for r in result.reasons)


def test_sleeve_disagreement_triggers_no_trade():
    scores = {"momentum": 0.6, "trend": 0.5, "breakout": -0.6, "mean_reversion": 0.1, "relative_strength": 0.5}
    result = evaluate_no_trade(_good_candidate(sleeve_scores=scores), make_config())
    assert result.decision == "NO-TRADE"
    assert any("disagreement" in r for r in result.reasons)


def test_low_regime_confidence_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(regime_confidence=0.1), make_config())
    assert result.decision == "NO-TRADE"
    assert any("regime confidence" in r for r in result.reasons)


def test_low_setup_quality_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(setup_quality=30), make_config())
    assert result.decision == "NO-TRADE"
    assert any("setup quality" in r for r in result.reasons)


def test_wide_spread_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(spread_pct=0.9), make_config())
    assert result.decision == "NO-TRADE"
    assert any("spread" in r for r in result.reasons)


def test_illiquid_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(liquidity_ok=False), make_config())
    assert result.decision == "NO-TRADE"


def test_portfolio_concentration_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(portfolio_concentration_ok=False), make_config())
    assert result.decision == "NO-TRADE"
    assert any("concentration" in r for r in result.reasons)


def test_unverified_catalyst_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(catalyst_verified=False), make_config())
    assert result.decision == "NO-TRADE"
    assert any("catalyst" in r for r in result.reasons)


def test_insufficient_reward_risk_triggers_no_trade():
    result = evaluate_no_trade(_good_candidate(reward_risk_ratio=1.0), make_config())
    assert result.decision == "NO-TRADE"
    assert any("reward/risk" in r for r in result.reasons)


def test_reward_risk_exactly_at_minimum_passes_despite_float_noise():
    # Regression: observed live on a real candidate (MRNA, 2026-08-21) --
    # (161.56 - 148.3) / (148.3 - 141.67) computes to 1.9999999999999998 in
    # IEEE754 double precision, not exactly 2.0, and was spuriously
    # rejected by a strict `<` comparison against a 2.0 minimum.
    computed = (161.56 - 148.3) / (148.3 - 141.67)
    assert computed < 2.0  # confirms the float-noise premise this test guards against
    result = evaluate_no_trade(_good_candidate(reward_risk_ratio=computed), make_config())
    assert result.decision == "PASS"


def test_no_ml_fallback_passes_when_ensemble_score_clears_validated_minimum():
    c = make_config({"no_trade": {"require_ml_probability": False}, "strategy": {"minimum_ensemble_score": 0.55}})
    result = evaluate_no_trade(_good_candidate(ml_probability=None, ensemble_score=0.70), c)
    assert result.decision == "PASS"


def test_no_ml_fallback_fails_when_ensemble_score_below_validated_minimum():
    c = make_config({"no_trade": {"require_ml_probability": False}, "strategy": {"minimum_ensemble_score": 0.55}})
    result = evaluate_no_trade(_good_candidate(ml_probability=None, ensemble_score=0.40), c)
    assert result.decision == "NO-TRADE"
    assert any("ensemble score" in r for r in result.reasons)


def test_no_ml_fallback_fails_closed_when_minimum_ensemble_score_still_validate():
    c = make_config({"no_trade": {"require_ml_probability": False}, "strategy": {"minimum_ensemble_score": "VALIDATE"}})
    result = evaluate_no_trade(_good_candidate(ml_probability=None, ensemble_score=0.99), c)
    assert result.decision == "NO-TRADE"
    assert any("VALIDATE/unset" in r for r in result.reasons)


def test_no_ml_fallback_still_requires_catalyst_verification():
    c = make_config({"no_trade": {"require_ml_probability": False}, "strategy": {"minimum_ensemble_score": 0.55}})
    result = evaluate_no_trade(
        _good_candidate(ml_probability=None, ensemble_score=0.90, catalyst_verified=False), c,
    )
    assert result.decision == "NO-TRADE"
    assert any("catalyst" in r for r in result.reasons)


def test_require_ml_probability_false_does_not_override_an_active_model_saying_no():
    # require_ml_probability=false only changes behavior when ml_probability
    # IS None -- if a champion model exists and actively says no, that's a
    # stronger signal than "no model yet" and must still block.
    c = make_config({"no_trade": {"require_ml_probability": False, "probability_threshold": 0.55}})
    result = evaluate_no_trade(_good_candidate(ml_probability=0.20), c)
    assert result.decision == "NO-TRADE"
    assert any("probability" in r for r in result.reasons)


def test_risk_off_gate_blocks_unless_exception_validated():
    blocked = evaluate_no_trade(_good_candidate(market_risk_off_gate_active=True), make_config())
    assert blocked.decision == "NO-TRADE"

    allowed = evaluate_no_trade(
        _good_candidate(market_risk_off_gate_active=True, risk_off_exception_validated=True), make_config()
    )
    assert allowed.decision == "PASS"
