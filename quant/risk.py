"""
Adaptive Risk Engine (PDF section 8).

Position size responds to actual setup risk instead of a blind fixed dollar
amount per ticker. The original guide's fixed caps (max 20% per position,
75-85% target deployment) stay as hard ceilings in config/strategy.yaml;
this module adds the independent per-trade risk budget on top.

The RISK_BUDGET_TABLE ranges below are the PDF's illustrative examples, not
validated recommendations — research/backtest.py + walk_forward.py must
pick the final numbers before this is used against real capital.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from quant.config import Config

# (setup_state) -> (min_pct, max_pct) of equity risked on this trade
RISK_BUDGET_TABLE: dict[str, tuple[float, float]] = {
    "exceptional": (0.0050, 0.0075),
    "normal": (0.0035, 0.0050),
    "uncertain": (0.0015, 0.0035),
    "concentrated": (0.0000, 0.0025),
    "hard_gate_failed": (0.0, 0.0),
}


def classify_setup_state(
    setup_quality: float,
    regime_state: str,
    regime_confidence: float,
    portfolio_concentration_ok: bool,
    hard_gate_failed: bool,
) -> str:
    if hard_gate_failed:
        return "hard_gate_failed"
    if not portfolio_concentration_ok:
        return "concentrated"
    if regime_state in ("HIGH_VOL", "TRANSITION") or regime_confidence < 0.5:
        return "uncertain"
    if setup_quality >= 85 and regime_state == "STRONG_TREND" and regime_confidence >= 0.7:
        return "exceptional"
    return "normal"


def risk_budget_pct(setup_state: str, quality_within_band: float = 0.5) -> float:
    """quality_within_band in [0,1] interpolates within the state's range —
    e.g. a 90/100 setup sits higher in the 'exceptional' band than an 86/100 one."""
    lo, hi = RISK_BUDGET_TABLE[setup_state]
    quality_within_band = max(0.0, min(1.0, quality_within_band))
    return lo + (hi - lo) * quality_within_band


@dataclass
class SizingResult:
    shares: int
    risk_dollars: float
    risk_per_share: float
    risk_budget_pct: float
    capped_by: str        # which constraint bound the final size, for audit


def size_position(
    equity: float,
    risk_budget: float,
    entry_price: float,
    stop_price: float,
    max_position_value: float,
    available_cash: float,
    liquidity_limit_shares: float,
    portfolio_limit_shares: float,
) -> SizingResult:
    """Implements the exact sizing formula from PDF section 8."""
    if entry_price <= 0 or stop_price == entry_price:
        return SizingResult(0, 0.0, 0.0, risk_budget, "invalid entry/stop")

    risk_dollars = equity * risk_budget
    risk_per_share = abs(entry_price - stop_price)
    raw_shares = math.floor(risk_dollars / risk_per_share) if risk_per_share > 0 else 0

    candidates = {
        "risk_budget": raw_shares,
        "max_position_value": math.floor(max_position_value / entry_price),
        "available_cash": math.floor(available_cash / entry_price),
        "liquidity_limit": math.floor(liquidity_limit_shares),
        "portfolio_limit": math.floor(portfolio_limit_shares),
    }
    capped_by = min(candidates, key=candidates.get)
    shares = max(0, candidates[capped_by])

    return SizingResult(
        shares=shares,
        risk_dollars=round(risk_dollars, 2),
        risk_per_share=round(risk_per_share, 4),
        risk_budget_pct=risk_budget,
        capped_by=capped_by,
    )


def portfolio_heat(open_position_risks: list[float], equity: float) -> float:
    """Sum of capital-at-risk across open positions, as a % of equity (section 9)."""
    if equity <= 0:
        return 0.0
    return sum(open_position_risks) / equity


def heat_gate_ok(current_heat_pct: float, cfg: Config) -> bool:
    max_heat = cfg.get("risk.max_portfolio_heat_pct")
    if not isinstance(max_heat, (int, float)):
        # not validated yet -> fail closed, do not silently allow unlimited heat
        return False
    return current_heat_pct <= max_heat
