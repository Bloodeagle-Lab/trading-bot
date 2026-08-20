"""
Stress testing (PDF section 12, second half).

Where research/monte_carlo.py asks "how sensitive is this strategy to path
variation", this module asks "how much of the edge survives worse-than-
backtest conditions". Each scenario perturbs a validated trade set along one
axis the PDF calls out explicitly, then re-derives full metrics so the delta
against baseline is visible line-by-line rather than buried in one aggregate
number. A strategy that only clears its bar under perfect fills and one
favorable regime is not production-ready (PDF section 12's closing line).

Scenarios implemented, each mapped to a PDF bullet:
  - apply_slippage           -> "model worse slippage and wider spreads"
  - apply_stop_gap_risk       -> "test overnight gaps through stops"
  - apply_execution_failures  -> "test delayed fills, missing quotes,
                                   rejected orders and API outages"
  - regime_breakdown          -> "test regime transitions where a strategy
                                   that worked in one environment becomes
                                   ineffective"

All scenario functions take a `trades: list[Trade]` and return a new,
independent `list[Trade]` — the input is never mutated, so the same baseline
trade set can be stressed along multiple axes (including combined) without
re-running the backtest.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from quant.config import Config
from research.backtest import Trade, compute_metrics


@dataclass
class StressScenario:
    name: str
    n_trades: int
    metrics: dict[str, float]
    delta_vs_baseline: dict[str, float]     # metric -> (scenario - baseline), numeric metrics only


@dataclass
class StressTestReport:
    baseline_metrics: dict[str, float]
    scenarios: list[StressScenario] = field(default_factory=list)
    regime_metrics: dict[str, dict[str, float]] = field(default_factory=dict)

    def summary_markdown(self) -> str:
        lines = ["**Stress Test Report**", "", "Baseline vs stressed scenarios:", ""]
        headline = ["total_return_pct", "max_drawdown_pct", "sharpe", "win_rate_pct", "expectancy_r", "n_trades"]
        header = ["Scenario"] + headline
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        base_row = ["baseline"] + [
            (f"{self.baseline_metrics.get(m, 0):.2f}" if m != "n_trades" else str(self.baseline_metrics.get("n_trades", 0)))
            for m in headline
        ]
        lines.append("| " + " | ".join(base_row) + " |")
        for s in self.scenarios:
            row = [s.name] + [
                (f"{s.metrics.get(m, 0):.2f}" if m != "n_trades" else str(s.n_trades))
                for m in headline
            ]
            lines.append("| " + " | ".join(row) + " |")
        if self.regime_metrics:
            lines += ["", "**By regime at entry:**", ""]
            lines.append("| Regime | n | Total return % | Max DD % | Win rate % | Expectancy R |")
            lines.append("|---|---|---|---|---|---|")
            for regime, m in self.regime_metrics.items():
                lines.append(
                    f"| {regime} | {m.get('n_trades', 0)} | {m.get('total_return_pct', 0):.2f} | "
                    f"{m.get('max_drawdown_pct', 0):.2f} | {m.get('win_rate_pct', 0):.1f} | "
                    f"{m.get('expectancy_r', 0):.3f} |"
                )
        return "\n".join(lines)


def _equity_curve_from_trades(trades: list[Trade], starting_equity: float) -> pd.Series:
    """Builds a date-indexed equity curve by walking exit dates in
    chronological order and applying each trade's pnl_dollars. Same
    single-strategy-thread simplification research/backtest.py's own
    equity_curve makes — concurrent-position margin/cash interaction is not
    modeled here, only the sequence of realized P&L."""
    if not trades:
        now = pd.Timestamp.now()
        return pd.Series([starting_equity], index=pd.DatetimeIndex([now]))
    ordered = sorted(trades, key=lambda t: t.exit_date)
    equity = starting_equity
    idx, vals = [], []
    for t in ordered:
        equity += t.pnl_dollars
        idx.append(t.exit_date)
        vals.append(equity)
    return pd.Series(vals, index=pd.DatetimeIndex(idx))


def _metrics_for(trades: list[Trade], starting_equity: float) -> dict[str, float]:
    curve = _equity_curve_from_trades(trades, starting_equity)
    return compute_metrics(trades, curve, starting_equity, pd.DataFrame())


def apply_slippage(trades: list[Trade], slippage_multiplier: float, base_slippage_bps: float = 5.0) -> list[Trade]:
    """Degrades every entry AND exit fill by base_slippage_bps *
    slippage_multiplier, adverse both ways (buy higher, sell lower) — the
    long-only assumption research/backtest.py already makes (stop_price is
    always below entry_price there). slippage_multiplier=1.0 reproduces a
    small baseline cost; use the validated
    validation.stress_slippage_multipliers from config/strategy.yaml
    (1.25 / 1.50 / 2.00) to see how much edge survives worse execution.
    """
    slip_frac = base_slippage_bps * slippage_multiplier / 10_000
    stressed = []
    for t in trades:
        entry = t.entry_price * (1 + slip_frac)
        exit_ = t.exit_price * (1 - slip_frac)
        risk_per_share = t.entry_price - t.stop_price
        pnl = (exit_ - entry) * t.shares
        r_new = (exit_ - entry) / risk_per_share if risk_per_share else t.r_multiple
        stressed.append(replace(
            t, entry_price=round(entry, 4), exit_price=round(exit_, 4),
            pnl_dollars=round(pnl, 2), r_multiple=round(r_new, 3),
        ))
    return stressed


def apply_stop_gap_risk(
    trades: list[Trade], gap_probability: float = 0.05, gap_severity_r: float = 1.0, seed: int | None = None,
) -> list[Trade]:
    """Overnight gaps can blow straight through a stop order — the original
    guide's own Alpaca gotcha ("trailing stops only work during market
    hours; overnight gaps can blow right through them"). For each trade that
    exited via a stop, with probability gap_probability the fill is modeled
    as landing gap_severity_r additional R below the intended stop price
    instead of exactly at it. Trades that exited via target/horizon_close
    are untouched — the stop was never in play."""
    rng = np.random.default_rng(seed)
    stressed = []
    for t in trades:
        if t.exit_reason != "stop" or rng.random() >= gap_probability:
            stressed.append(t)
            continue
        risk_per_share = t.entry_price - t.stop_price
        gapped_exit = t.exit_price - gap_severity_r * risk_per_share
        pnl = (gapped_exit - t.entry_price) * t.shares
        r_new = (gapped_exit - t.entry_price) / risk_per_share if risk_per_share else t.r_multiple
        stressed.append(replace(
            t, exit_price=round(gapped_exit, 4), pnl_dollars=round(pnl, 2),
            r_multiple=round(r_new, 3), exit_reason="stop_gap",
        ))
    return stressed


def apply_execution_failures(trades: list[Trade], rejection_rate: float = 0.05, seed: int | None = None) -> list[Trade]:
    """Models rejected orders / API outages / stale quotes at entry time:
    with probability rejection_rate, an otherwise-valid signal never got
    filled at all. The trade is DROPPED entirely (not degraded) — a rejected
    entry order produces no position and no P&L, good or bad."""
    rng = np.random.default_rng(seed)
    return [t for t in trades if rng.random() >= rejection_rate]


def regime_breakdown(trades: list[Trade], starting_equity: float) -> dict[str, dict[str, float]]:
    """Buckets trades by regime_at_entry and computes metrics per bucket, so
    a strategy that only works in STRONG_TREND — and quietly loses money
    everywhere else — is visible rather than hidden inside the aggregate
    (PDF: "test regime transitions where a strategy that worked in one
    environment becomes ineffective")."""
    buckets: dict[str, list[Trade]] = defaultdict(list)
    for t in trades:
        buckets[t.regime_at_entry].append(t)
    return {regime: _metrics_for(group, starting_equity) for regime, group in buckets.items()}


def _make_scenario(name: str, stressed_trades: list[Trade], starting_equity: float, baseline: dict[str, float]) -> StressScenario:
    metrics = _metrics_for(stressed_trades, starting_equity)
    delta = {
        k: round(v - baseline[k], 3)
        for k, v in metrics.items()
        if isinstance(v, (int, float)) and isinstance(baseline.get(k), (int, float))
    }
    return StressScenario(name=name, n_trades=len(stressed_trades), metrics=metrics, delta_vs_baseline=delta)


def run_full_stress_suite(
    trades: list[Trade],
    cfg: Config,
    starting_equity: float = 100_000.0,
    seed: int | None = None,
) -> StressTestReport:
    """Runs every scenario above plus a combined worst-case (all three
    execution-quality stresses applied together) and a regime breakdown,
    and returns everything alongside the unstressed baseline for
    side-by-side comparison. Consumes the same OOS trade set walk-forward
    testing produced — do not feed this a single in-sample backtest run."""
    if not trades:
        raise ValueError("run_full_stress_suite requires at least one trade")

    baseline_metrics = _metrics_for(trades, starting_equity)
    scenarios: list[StressScenario] = []

    multipliers = cfg.get("validation.stress_slippage_multipliers", [1.25, 1.50, 2.00])
    for m in multipliers:
        stressed = apply_slippage(trades, slippage_multiplier=m)
        scenarios.append(_make_scenario(f"slippage_{m}x", stressed, starting_equity, baseline_metrics))

    gapped = apply_stop_gap_risk(trades, seed=seed)
    scenarios.append(_make_scenario("overnight_gap_risk", gapped, starting_equity, baseline_metrics))

    failed = apply_execution_failures(trades, seed=seed)
    scenarios.append(_make_scenario("execution_failures_5pct", failed, starting_equity, baseline_metrics))

    worst_multiplier = max(multipliers) if multipliers else 1.5
    combined = apply_execution_failures(
        apply_stop_gap_risk(apply_slippage(trades, slippage_multiplier=worst_multiplier), seed=seed),
        seed=seed,
    )
    scenarios.append(_make_scenario("combined_worst_case", combined, starting_equity, baseline_metrics))

    return StressTestReport(
        baseline_metrics=baseline_metrics,
        scenarios=scenarios,
        regime_metrics=regime_breakdown(trades, starting_equity),
    )
