from __future__ import annotations

import pandas as pd
import pytest

from research.backtest import Trade
from research.stress_test import (
    apply_execution_failures, apply_slippage, apply_stop_gap_risk,
    regime_breakdown, run_full_stress_suite,
)
from tests.conftest import make_config


def _trades() -> list[Trade]:
    return [
        Trade(
            ticker="A", entry_date=pd.Timestamp("2024-01-01"), exit_date=pd.Timestamp("2024-01-10"),
            entry_price=100.0, exit_price=110.0, stop_price=95.0, shares=10,
            r_multiple=2.0, pnl_dollars=100.0, regime_at_entry="STRONG_TREND", ensemble_score=0.7,
            exit_reason="target",
        ),
        Trade(
            ticker="B", entry_date=pd.Timestamp("2024-01-02"), exit_date=pd.Timestamp("2024-01-11"),
            entry_price=100.0, exit_price=95.0, stop_price=95.0, shares=10,
            r_multiple=-1.0, pnl_dollars=-50.0, regime_at_entry="CHOPPY", ensemble_score=0.5,
            exit_reason="stop",
        ),
        Trade(
            ticker="C", entry_date=pd.Timestamp("2024-01-03"), exit_date=pd.Timestamp("2024-01-12"),
            entry_price=100.0, exit_price=102.0, stop_price=95.0, shares=10,
            r_multiple=0.4, pnl_dollars=20.0, regime_at_entry="STRONG_TREND", ensemble_score=0.6,
            exit_reason="horizon_close",
        ),
    ]


def test_apply_slippage_is_adverse_for_every_trade():
    trades = _trades()
    stressed = apply_slippage(trades, slippage_multiplier=1.5)
    for original, degraded in zip(trades, stressed):
        assert degraded.pnl_dollars < original.pnl_dollars


def test_apply_slippage_zero_multiplier_leaves_trades_unchanged():
    trades = _trades()
    stressed = apply_slippage(trades, slippage_multiplier=0.0)
    for original, degraded in zip(trades, stressed):
        assert degraded.pnl_dollars == pytest.approx(original.pnl_dollars)
        assert degraded.entry_price == pytest.approx(original.entry_price)


def test_apply_slippage_does_not_mutate_input():
    trades = _trades()
    original_pnl = trades[0].pnl_dollars
    apply_slippage(trades, slippage_multiplier=2.0)
    assert trades[0].pnl_dollars == original_pnl


def test_apply_stop_gap_risk_only_touches_stop_exits_when_certain():
    trades = _trades()
    stressed = apply_stop_gap_risk(trades, gap_probability=1.0, gap_severity_r=1.0, seed=1)
    a, b, c = stressed
    assert a.exit_reason == "target" and a.pnl_dollars == pytest.approx(100.0)  # untouched
    assert c.exit_reason == "horizon_close" and c.pnl_dollars == pytest.approx(20.0)  # untouched
    assert b.exit_reason == "stop_gap"
    assert b.pnl_dollars == pytest.approx(-100.0)  # exit gapped down an extra 1R (5 pts) -> (90-100)*10


def test_apply_stop_gap_risk_never_triggers_at_zero_probability():
    trades = _trades()
    stressed = apply_stop_gap_risk(trades, gap_probability=0.0, seed=1)
    for original, unchanged in zip(trades, stressed):
        assert unchanged.exit_reason == original.exit_reason
        assert unchanged.pnl_dollars == pytest.approx(original.pnl_dollars)


def test_apply_execution_failures_drops_all_at_full_rejection():
    assert apply_execution_failures(_trades(), rejection_rate=1.0, seed=1) == []


def test_apply_execution_failures_keeps_all_at_zero_rejection():
    trades = _trades()
    kept = apply_execution_failures(trades, rejection_rate=0.0, seed=1)
    assert len(kept) == len(trades)


def test_regime_breakdown_buckets_by_regime_at_entry():
    breakdown = regime_breakdown(_trades(), starting_equity=100_000)
    assert set(breakdown.keys()) == {"STRONG_TREND", "CHOPPY"}
    assert breakdown["STRONG_TREND"]["n_trades"] == 2
    assert breakdown["CHOPPY"]["n_trades"] == 1


def test_run_full_stress_suite_rejects_empty_trades():
    with pytest.raises(ValueError):
        run_full_stress_suite([], make_config())


def test_run_full_stress_suite_produces_all_expected_scenarios():
    cfg = make_config({"validation": {"stress_slippage_multipliers": [1.25, 1.50, 2.00]}})
    report = run_full_stress_suite(_trades(), cfg, starting_equity=100_000, seed=1)

    assert report.baseline_metrics["n_trades"] == 3
    names = [s.name for s in report.scenarios]
    assert len(names) == 6  # 3 slippage multipliers + gap + execution + combined
    assert sum(n.startswith("slippage_") for n in names) == 3
    assert "overnight_gap_risk" in names
    assert "execution_failures_5pct" in names
    assert "combined_worst_case" in names
    assert set(report.regime_metrics.keys()) == {"STRONG_TREND", "CHOPPY"}

    for scenario in report.scenarios:
        assert scenario.n_trades <= 3
        assert "total_return_pct" in scenario.delta_vs_baseline


def test_stress_report_summary_markdown_lists_scenarios():
    cfg = make_config()
    report = run_full_stress_suite(_trades(), cfg, starting_equity=100_000, seed=1)
    text = report.summary_markdown()
    assert "Stress Test Report" in text
    assert "baseline" in text
    assert "overnight_gap_risk" in text
