from __future__ import annotations

import pandas as pd
import pytest

from quant.portfolio import (
    PortfolioState, Position, concentration_ok, correlated_cluster_risk,
    record_sector_result, rolling_correlation_matrix,
)


def _state(equity=100_000.0, positions=None, sector_fail_streak=None) -> PortfolioState:
    return PortfolioState(positions=positions or [], equity=equity, sector_fail_streak=sector_fail_streak or {})


def test_position_risk_dollars():
    p = Position(ticker="XYZ", sector="Tech", shares=10, entry_price=50.0, stop_price=47.0, market_value=500.0)
    assert p.risk_dollars == pytest.approx(30.0)


def test_sector_exposure_pct_sums_by_sector():
    positions = [
        Position("A", "Tech", 10, 50, 47, 5_000),
        Position("B", "Tech", 5, 100, 95, 5_000),
        Position("C", "Energy", 20, 20, 18, 4_000),
    ]
    state = _state(equity=100_000, positions=positions)
    exposure = state.sector_exposure_pct()
    assert exposure["Tech"] == pytest.approx(0.10)
    assert exposure["Energy"] == pytest.approx(0.04)


def test_total_heat_pct():
    positions = [Position("A", "Tech", 10, 50, 45, 500)]  # risk = (50-45)/share * 10 shares = 50
    state = _state(equity=50_000, positions=positions)
    assert state.total_heat_pct() == pytest.approx(50 / 50_000)


def test_concentration_ok_rejects_when_at_max_positions():
    positions = [Position(f"T{i}", "Tech", 1, 10, 9, 10) for i in range(6)]
    state = _state(positions=positions)
    ok, reasons = concentration_ok(
        state, candidate_ticker="NEW", candidate_sector="Tech", candidate_risk_dollars=10,
        max_position_pct=0.20, max_positions=6, max_correlated_cluster_risk_pct=1.0,
    )
    assert ok is False
    assert any("max_positions" in r for r in reasons)


def test_concentration_ok_allows_adding_to_existing_ticker_at_max():
    positions = [Position(f"T{i}", "Tech", 1, 10, 9, 10) for i in range(6)]
    state = _state(positions=positions)
    ok, reasons = concentration_ok(
        state, candidate_ticker="T0", candidate_sector="Tech", candidate_risk_dollars=10,
        max_position_pct=0.20, max_positions=6, max_correlated_cluster_risk_pct=1.0,
    )
    assert not any("max_positions" in r for r in reasons)


def test_concentration_ok_rejects_sector_after_two_failed_trades():
    state = _state(sector_fail_streak={"Energy": 2})
    ok, reasons = concentration_ok(
        state, candidate_ticker="XOM", candidate_sector="Energy", candidate_risk_dollars=100,
        max_position_pct=0.20, max_positions=6, max_correlated_cluster_risk_pct=1.0,
    )
    assert ok is False
    assert any("2+ consecutive failed trades" in r for r in reasons)


def test_concentration_ok_true_when_nothing_violated():
    state = _state(equity=100_000)
    ok, reasons = concentration_ok(
        state, candidate_ticker="NEW", candidate_sector="Tech", candidate_risk_dollars=100,
        max_position_pct=0.20, max_positions=6, max_correlated_cluster_risk_pct=1.0,
    )
    assert ok is True
    assert reasons == []


def test_correlated_cluster_risk_sums_correlated_positions_only():
    positions = [
        Position("A", "Tech", 1, 10, 9, 10),   # risk = 1
        Position("B", "Tech", 1, 10, 9, 10),   # risk = 1, correlated with candidate
        Position("C", "Energy", 1, 10, 9, 10),  # risk = 1, not correlated
    ]
    state = _state(positions=positions)
    corr = pd.DataFrame(
        [[1.0, 0.9, 0.1], [0.9, 1.0, 0.1], [0.1, 0.1, 1.0]],
        index=["CAND", "A", "C"], columns=["CAND", "A", "C"],
    )
    total = correlated_cluster_risk(state, "CAND", candidate_risk_dollars=5.0, corr_matrix=corr, corr_threshold=0.6)
    # candidate (5) + A (1, corr 0.9 >= 0.6) ; B not in corr_matrix so skipped; C excluded (corr 0.1)
    assert total == pytest.approx(6.0)


def test_correlated_cluster_risk_returns_candidate_only_when_ticker_not_in_matrix():
    state = _state()
    corr = pd.DataFrame([[1.0]], index=["OTHER"], columns=["OTHER"])
    total = correlated_cluster_risk(state, "CAND", candidate_risk_dollars=42.0, corr_matrix=corr)
    assert total == pytest.approx(42.0)


def test_concentration_ok_rejects_on_correlated_cluster_risk():
    positions = [Position("A", "Tech", 100, 10, 9, 1_000)]  # risk = 100
    state = _state(equity=1_000, positions=positions)
    corr = pd.DataFrame([[1.0, 0.9], [0.9, 1.0]], index=["CAND", "A"], columns=["CAND", "A"])
    ok, reasons = concentration_ok(
        state, candidate_ticker="CAND", candidate_sector="Tech", candidate_risk_dollars=200,
        max_position_pct=0.20, max_positions=6, max_correlated_cluster_risk_pct=0.10,
        corr_matrix=corr,
    )
    assert ok is False
    assert any("correlated cluster risk" in r for r in reasons)


def test_rolling_correlation_matrix_shape():
    idx = pd.bdate_range("2024-01-01", periods=100)
    returns = {"A": pd.Series(range(100), index=idx, dtype=float), "B": pd.Series(range(100, 200), index=idx, dtype=float)}
    corr = rolling_correlation_matrix(returns, window=60)
    assert corr.shape == (2, 2)
    assert corr.loc["A", "A"] == pytest.approx(1.0)


def test_record_sector_result_resets_on_win_and_increments_on_loss():
    state = _state()
    record_sector_result(state, "Tech", was_win=False)
    record_sector_result(state, "Tech", was_win=False)
    assert state.sector_fail_streak["Tech"] == 2
    record_sector_result(state, "Tech", was_win=True)
    assert state.sector_fail_streak["Tech"] == 0
