from __future__ import annotations

import pytest

from quant.risk import (
    RISK_BUDGET_TABLE, classify_setup_state, heat_gate_ok, portfolio_heat,
    risk_budget_pct, size_position,
)
from tests.conftest import make_config


def test_classify_setup_state_hard_gate_failed_wins_over_everything():
    state = classify_setup_state(setup_quality=95, regime_state="STRONG_TREND", regime_confidence=0.9,
                                  portfolio_concentration_ok=True, hard_gate_failed=True)
    assert state == "hard_gate_failed"


def test_classify_setup_state_concentrated_when_portfolio_not_ok():
    state = classify_setup_state(setup_quality=95, regime_state="STRONG_TREND", regime_confidence=0.9,
                                  portfolio_concentration_ok=False, hard_gate_failed=False)
    assert state == "concentrated"


def test_classify_setup_state_uncertain_in_high_vol_regime():
    state = classify_setup_state(setup_quality=95, regime_state="HIGH_VOL", regime_confidence=0.9,
                                  portfolio_concentration_ok=True, hard_gate_failed=False)
    assert state == "uncertain"


def test_classify_setup_state_uncertain_on_low_confidence():
    state = classify_setup_state(setup_quality=95, regime_state="STRONG_TREND", regime_confidence=0.3,
                                  portfolio_concentration_ok=True, hard_gate_failed=False)
    assert state == "uncertain"


def test_classify_setup_state_exceptional_requires_all_three_conditions():
    state = classify_setup_state(setup_quality=90, regime_state="STRONG_TREND", regime_confidence=0.8,
                                  portfolio_concentration_ok=True, hard_gate_failed=False)
    assert state == "exceptional"


def test_classify_setup_state_normal_otherwise():
    state = classify_setup_state(setup_quality=70, regime_state="STRONG_TREND", regime_confidence=0.6,
                                  portfolio_concentration_ok=True, hard_gate_failed=False)
    assert state == "normal"


@pytest.mark.parametrize("state", RISK_BUDGET_TABLE.keys())
def test_risk_budget_pct_interpolates_within_band(state):
    lo, hi = RISK_BUDGET_TABLE[state]
    assert risk_budget_pct(state, 0.0) == pytest.approx(lo)
    assert risk_budget_pct(state, 1.0) == pytest.approx(hi)
    mid = risk_budget_pct(state, 0.5)
    assert lo <= mid <= hi


def test_risk_budget_pct_clamps_out_of_range_quality():
    lo, hi = RISK_BUDGET_TABLE["normal"]
    assert risk_budget_pct("normal", -5.0) == pytest.approx(lo)
    assert risk_budget_pct("normal", 5.0) == pytest.approx(hi)


def test_size_position_matches_manual_formula():
    result = size_position(
        equity=100_000, risk_budget=0.005, entry_price=50.0, stop_price=47.0,
        max_position_value=20_000, available_cash=100_000,
        liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    expected_risk_dollars = 100_000 * 0.005
    expected_risk_per_share = 3.0
    expected_shares = int(expected_risk_dollars // expected_risk_per_share)
    assert result.shares == expected_shares
    assert result.risk_dollars == pytest.approx(expected_risk_dollars)
    assert result.capped_by == "risk_budget"


def test_size_position_capped_by_max_position_value():
    result = size_position(
        equity=1_000_000, risk_budget=0.05, entry_price=50.0, stop_price=49.0,
        max_position_value=1_000, available_cash=1_000_000,
        liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    assert result.capped_by == "max_position_value"
    assert result.shares == 20  # 1000 / 50


def test_size_position_capped_by_available_cash():
    result = size_position(
        equity=1_000_000, risk_budget=0.05, entry_price=50.0, stop_price=49.0,
        max_position_value=1_000_000, available_cash=500,
        liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    assert result.capped_by == "available_cash"
    assert result.shares == 10  # 500 / 50


def test_size_position_zero_when_entry_equals_stop():
    result = size_position(
        equity=100_000, risk_budget=0.005, entry_price=50.0, stop_price=50.0,
        max_position_value=20_000, available_cash=100_000,
        liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    assert result.shares == 0
    assert result.capped_by == "invalid entry/stop"


def test_size_position_never_negative():
    result = size_position(
        equity=100_000, risk_budget=0.001, entry_price=50.0, stop_price=48.0,
        max_position_value=20_000, available_cash=0,
        liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    assert result.shares == 0


def test_portfolio_heat_is_sum_of_risk_over_equity():
    assert portfolio_heat([500.0, 300.0], equity=100_000) == pytest.approx(0.008)


def test_portfolio_heat_zero_when_equity_nonpositive():
    assert portfolio_heat([500.0], equity=0) == 0.0


def test_heat_gate_fails_closed_when_not_validated():
    c = make_config({"risk": {"max_portfolio_heat_pct": "VALIDATE"}})
    assert heat_gate_ok(0.01, c) is False


def test_heat_gate_ok_respects_validated_threshold():
    c = make_config({"risk": {"max_portfolio_heat_pct": 3.0}})
    assert heat_gate_ok(2.5, c) is True
    assert heat_gate_ok(3.5, c) is False
