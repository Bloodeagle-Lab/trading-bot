"""
Monte Carlo simulation (PDF section 12, first half).

After a validated trade set exists (from research/backtest.py or
research/walk_forward.py), this module runs thousands of randomized
trade-sequence simulations. The goal is not to predict the future — it is
to understand how sensitive the strategy is to path variation: the same set
of trade outcomes, arriving in a different order or a differently-sampled
mix, can produce a much worse drawdown than the one lucky path the backtest
happened to walk.

Three resampling methods, matching the PDF's three explicit bullets:

  - "shuffle"         — randomize the ORDER of the existing trades, exact
                         outcome distribution preserved. Ending equity is
                         therefore identical across runs (same trades, same
                         sum); only the PATH — and so max drawdown — varies.
                         This isolates path/sequencing risk specifically.
  - "bootstrap"        — sample trade outcomes WITH REPLACEMENT, converted to
                         R-multiples and compounded at a chosen
                         risk_pct_per_trade. This lets ending equity and
                         drawdown both vary, and (via `n_runs` far exceeding
                         `len(trades)`) probes outcomes the observed history
                         never happened to produce.
  - "block_bootstrap"  — bootstrap in contiguous blocks of the original
                         chronological order instead of single trades, so a
                         real losing streak stays a streak instead of being
                         broken up by independent resampling. This is the
                         PDF's "test clustered losses, not only random
                         independent losses."

Why R-multiples, not raw dollar P&L, drive bootstrap/block_bootstrap:
this system sizes each trade with an adaptive risk budget (quant/risk.py),
so a trade's pnl_dollars is entangled with the equity and setup quality at
the moment it was taken. Reusing those dollar amounts under a different
resampled order or a longer synthetic history would silently misrepresent
compounding. Normalizing to R and re-compounding at a single configured
risk_pct_per_trade removes that entanglement — it is a deliberate
simplification, not an oversight, and the risk_pct_per_trade parameter
should be set from the validated risk budget (see RISK_BUDGET_TABLE in
quant/risk.py), not left at the default.

The "shuffle" method sidesteps this issue entirely by reusing the exact
recorded dollar P&L in a different order, which is why it's the right tool
for path/drawdown-only questions and the wrong tool for extrapolating
beyond the observed trade count.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from research.backtest import Trade

MonteCarloMethod = Literal["shuffle", "bootstrap", "block_bootstrap"]


@dataclass
class MonteCarloResult:
    method: MonteCarloMethod
    n_runs: int
    n_trades: int
    starting_equity: float
    ending_equity_dist: np.ndarray
    max_drawdown_dist: np.ndarray          # negative fractions, e.g. -0.23
    total_return_dist: np.ndarray
    drawdown_threshold_probabilities: dict[float, float]   # {0.10: 0.42, ...}

    def percentile(self, field_name: str, q: float) -> float:
        """q in [0, 100]. field_name one of ending_equity_dist,
        max_drawdown_dist, total_return_dist."""
        return float(np.percentile(getattr(self, field_name), q))

    def summary_markdown(self) -> str:
        p = self.percentile
        lines = [
            f"**Monte Carlo — {self.method}** ({self.n_runs:,} runs, {self.n_trades} trades, "
            f"starting equity ${self.starting_equity:,.0f})",
            "",
            "| Metric | P5 | P25 | Median | P75 | P95 |",
            "|---|---|---|---|---|---|",
            (
                "| Ending equity | "
                f"${p('ending_equity_dist', 5):,.0f} | ${p('ending_equity_dist', 25):,.0f} | "
                f"${p('ending_equity_dist', 50):,.0f} | ${p('ending_equity_dist', 75):,.0f} | "
                f"${p('ending_equity_dist', 95):,.0f} |"
            ),
            (
                "| Total return | "
                f"{p('total_return_dist', 5):+.1%} | {p('total_return_dist', 25):+.1%} | "
                f"{p('total_return_dist', 50):+.1%} | {p('total_return_dist', 75):+.1%} | "
                f"{p('total_return_dist', 95):+.1%} |"
            ),
            (
                "| Max drawdown | "
                f"{p('max_drawdown_dist', 5):.1%} | {p('max_drawdown_dist', 25):.1%} | "
                f"{p('max_drawdown_dist', 50):.1%} | {p('max_drawdown_dist', 75):.1%} | "
                f"{p('max_drawdown_dist', 95):.1%} |"
            ),
            "",
            "P(max drawdown exceeds threshold):",
        ]
        for thr, prob in sorted(self.drawdown_threshold_probabilities.items()):
            lines.append(f"- {thr:.0%}: {prob:.1%}")
        return "\n".join(lines)


def _max_drawdown(equity_curve: np.ndarray) -> float:
    running_max = np.maximum.accumulate(equity_curve)
    dd = equity_curve / running_max - 1
    return float(dd.min())


def _shuffle_run(trade_pnls: np.ndarray, starting_equity: float, rng: np.random.Generator) -> tuple[float, float, float]:
    order = rng.permutation(len(trade_pnls))
    curve = np.concatenate(([starting_equity], starting_equity + np.cumsum(trade_pnls[order])))
    ending = float(curve[-1])
    return ending, _max_drawdown(curve), ending / starting_equity - 1


def _bootstrap_run(
    r_multiples: np.ndarray,
    starting_equity: float,
    risk_pct_per_trade: float,
    n_trades: int,
    rng: np.random.Generator,
    block_size: int | None = None,
) -> tuple[float, float, float]:
    if block_size and block_size > 1 and len(r_multiples) > block_size:
        n_blocks = int(np.ceil(n_trades / block_size))
        max_start = len(r_multiples) - block_size
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        sampled = np.concatenate([r_multiples[s:s + block_size] for s in starts])[:n_trades]
    else:
        sampled = rng.choice(r_multiples, size=n_trades, replace=True)

    equity_mult = np.cumprod(1 + sampled * risk_pct_per_trade)
    curve = starting_equity * np.concatenate(([1.0], equity_mult))
    ending = float(curve[-1])
    return ending, _max_drawdown(curve), ending / starting_equity - 1


def run_monte_carlo(
    trades: list[Trade],
    starting_equity: float = 100_000.0,
    n_runs: int = 10_000,
    method: MonteCarloMethod = "bootstrap",
    risk_pct_per_trade: float = 0.005,
    block_size: int = 5,
    drawdown_thresholds: tuple[float, ...] = (0.10, 0.15, 0.20, 0.25, 0.30),
    seed: int | None = None,
) -> MonteCarloResult:
    """
    trades: a completed, validated trade set — typically the OOS trades from
    research/walk_forward.py, not a single in-sample backtest (see PDF
    section 11: "use out-of-sample and walk-forward results as the primary
    evidence").
    risk_pct_per_trade: only used by "bootstrap"/"block_bootstrap" — the
    per-trade risk budget (as a fraction of equity) to compound R-multiples
    at. Pull this from the validated risk.max_risk_per_trade_pct once it is
    no longer VALIDATE, not from the RISK_BUDGET_TABLE defaults blindly.
    block_size: only used by "block_bootstrap" — length of each contiguous
    chunk sampled from the original chronological trade order.
    """
    if not trades:
        raise ValueError("run_monte_carlo requires at least one trade — nothing to resample")
    if n_runs < 1:
        raise ValueError("n_runs must be >= 1")

    rng = np.random.default_rng(seed)
    n_trades = len(trades)

    endings = np.empty(n_runs)
    drawdowns = np.empty(n_runs)
    returns = np.empty(n_runs)

    if method == "shuffle":
        pnls = np.array([t.pnl_dollars for t in trades])
        for i in range(n_runs):
            endings[i], drawdowns[i], returns[i] = _shuffle_run(pnls, starting_equity, rng)
    elif method in ("bootstrap", "block_bootstrap"):
        r_mults = np.array([t.r_multiple for t in trades])
        bs = block_size if method == "block_bootstrap" else None
        for i in range(n_runs):
            endings[i], drawdowns[i], returns[i] = _bootstrap_run(
                r_mults, starting_equity, risk_pct_per_trade, n_trades, rng, block_size=bs
            )
    else:
        raise ValueError(f"unknown method {method!r}, choose shuffle | bootstrap | block_bootstrap")

    threshold_probs = {thr: float(np.mean(drawdowns <= -abs(thr))) for thr in drawdown_thresholds}

    return MonteCarloResult(
        method=method,
        n_runs=n_runs,
        n_trades=n_trades,
        starting_equity=starting_equity,
        ending_equity_dist=endings,
        max_drawdown_dist=drawdowns,
        total_return_dist=returns,
        drawdown_threshold_probabilities=threshold_probs,
    )
