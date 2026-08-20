from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.backtest import Trade
from research.monte_carlo import run_monte_carlo


def _make_trades(n=20, seed=1) -> list[Trade]:
    rng = np.random.default_rng(seed)
    trades = []
    for i in range(n):
        entry = 100.0
        stop = 95.0
        r_multiple = rng.normal(0.3, 1.2)  # mixed wins/losses, slight positive edge
        pnl = r_multiple * 500.0
        trades.append(Trade(
            ticker=f"T{i}",
            entry_date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
            exit_date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=i + 5),
            entry_price=entry, exit_price=entry + r_multiple * (entry - stop), stop_price=stop,
            shares=100, r_multiple=round(r_multiple, 3), pnl_dollars=round(pnl, 2),
            regime_at_entry="STRONG_TREND", ensemble_score=0.6,
            exit_reason="target" if r_multiple > 0 else "stop",
        ))
    return trades


def test_run_monte_carlo_rejects_empty_trades():
    with pytest.raises(ValueError):
        run_monte_carlo([], n_runs=10)


def test_run_monte_carlo_rejects_zero_runs():
    with pytest.raises(ValueError):
        run_monte_carlo(_make_trades(), n_runs=0)


def test_run_monte_carlo_rejects_unknown_method():
    with pytest.raises(ValueError):
        run_monte_carlo(_make_trades(), n_runs=10, method="not_a_method")


def test_shuffle_preserves_total_pnl_across_every_run():
    trades = _make_trades()
    total_pnl = sum(t.pnl_dollars for t in trades)
    result = run_monte_carlo(trades, starting_equity=100_000, n_runs=300, method="shuffle", seed=42)
    expected_ending = 100_000 + total_pnl
    np.testing.assert_allclose(result.ending_equity_dist, expected_ending, rtol=1e-9)
    # path varies even though the destination doesn't -> drawdown distribution has spread
    assert result.max_drawdown_dist.std() > 0


def test_bootstrap_produces_varying_endings():
    trades = _make_trades()
    result = run_monte_carlo(trades, starting_equity=100_000, n_runs=300, method="bootstrap",
                              risk_pct_per_trade=0.01, seed=42)
    assert result.ending_equity_dist.std() > 0
    assert len(result.ending_equity_dist) == 300


def test_block_bootstrap_does_not_crash_with_small_trade_set():
    trades = _make_trades(n=6)
    result = run_monte_carlo(trades, starting_equity=100_000, n_runs=100, method="block_bootstrap",
                              block_size=3, seed=1)
    assert len(result.ending_equity_dist) == 100
    assert np.isfinite(result.ending_equity_dist).all()


def test_block_bootstrap_falls_back_gracefully_when_block_size_exceeds_trade_count():
    trades = _make_trades(n=4)
    result = run_monte_carlo(trades, starting_equity=100_000, n_runs=50, method="block_bootstrap",
                              block_size=100, seed=1)
    assert np.isfinite(result.ending_equity_dist).all()


def test_drawdown_threshold_probabilities_are_monotonic_non_increasing():
    trades = _make_trades(n=40, seed=5)
    result = run_monte_carlo(
        trades, starting_equity=100_000, n_runs=500, method="bootstrap",
        risk_pct_per_trade=0.01, drawdown_thresholds=(0.05, 0.10, 0.20, 0.40), seed=7,
    )
    probs = [result.drawdown_threshold_probabilities[t] for t in sorted(result.drawdown_threshold_probabilities)]
    assert all(0.0 <= p <= 1.0 for p in probs)
    assert all(probs[i] >= probs[i + 1] for i in range(len(probs) - 1))


def test_same_seed_is_reproducible():
    trades = _make_trades()
    r1 = run_monte_carlo(trades, n_runs=200, method="bootstrap", seed=123)
    r2 = run_monte_carlo(trades, n_runs=200, method="bootstrap", seed=123)
    np.testing.assert_array_equal(r1.ending_equity_dist, r2.ending_equity_dist)


def test_percentile_matches_numpy():
    trades = _make_trades()
    result = run_monte_carlo(trades, n_runs=300, method="bootstrap", seed=1)
    assert result.percentile("ending_equity_dist", 50) == pytest.approx(
        float(np.percentile(result.ending_equity_dist, 50))
    )


def test_summary_markdown_contains_method_and_thresholds():
    trades = _make_trades()
    result = run_monte_carlo(trades, n_runs=100, method="shuffle", seed=1, drawdown_thresholds=(0.10, 0.20))
    text = result.summary_markdown()
    assert "shuffle" in text
    assert "10%" in text and "20%" in text
