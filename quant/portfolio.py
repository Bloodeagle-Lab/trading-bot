"""
Portfolio & Correlation Controls (PDF section 9).

Five different tickers can still be one concentrated bet — this module
tracks sector exposure, factor exposure and rolling pairwise correlations
so quant/no_trade.py and quant/risk.py can see the whole book, not just the
candidate in front of them. Correlation/heat spikes are risk-sizing and
new-entry controls here, NOT an automatic exit-everything trigger, per the
PDF's explicit instruction not to invent a separate emergency rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Position:
    ticker: str
    sector: str
    shares: int
    entry_price: float
    stop_price: float
    market_value: float

    @property
    def risk_dollars(self) -> float:
        return abs(self.entry_price - self.stop_price) * self.shares


@dataclass
class PortfolioState:
    positions: list[Position] = field(default_factory=list)
    equity: float = 0.0
    sector_fail_streak: dict[str, int] = field(default_factory=dict)   # consecutive losing trades per sector

    def sector_exposure_pct(self) -> dict[str, float]:
        if self.equity <= 0:
            return {}
        totals: dict[str, float] = {}
        for p in self.positions:
            totals[p.sector] = totals.get(p.sector, 0.0) + p.market_value
        return {sector: value / self.equity for sector, value in totals.items()}

    def position_count(self) -> int:
        return len(self.positions)

    def total_heat_dollars(self) -> float:
        return sum(p.risk_dollars for p in self.positions)

    def total_heat_pct(self) -> float:
        return 0.0 if self.equity <= 0 else self.total_heat_dollars() / self.equity


def rolling_correlation_matrix(returns_by_ticker: dict[str, pd.Series], window: int = 60) -> pd.DataFrame:
    """returns_by_ticker: {ticker: daily-return Series, aligned index}. Returns the
    most recent `window`-day pairwise correlation matrix."""
    df = pd.DataFrame(returns_by_ticker).dropna(how="all")
    recent = df.tail(window)
    return recent.corr()


def correlated_cluster_risk(
    state: PortfolioState,
    candidate_ticker: str,
    candidate_risk_dollars: float,
    corr_matrix: pd.DataFrame,
    corr_threshold: float = 0.6,
) -> float:
    """Sum of risk-dollars (existing positions + candidate) across everything
    correlated above `corr_threshold` with the candidate — the "five tickers,
    one bet" check. Returns the cluster's total risk in dollars."""
    if candidate_ticker not in corr_matrix.columns:
        return candidate_risk_dollars
    cluster_risk = candidate_risk_dollars
    for p in state.positions:
        if p.ticker == candidate_ticker or p.ticker not in corr_matrix.columns:
            continue
        corr = corr_matrix.loc[candidate_ticker, p.ticker]
        if pd.notna(corr) and abs(corr) >= corr_threshold:
            cluster_risk += p.risk_dollars
    return cluster_risk


def concentration_ok(
    state: PortfolioState,
    candidate_ticker: str,
    candidate_sector: str,
    candidate_risk_dollars: float,
    max_position_pct: float,
    max_positions: int,
    max_correlated_cluster_risk_pct: float,
    corr_matrix: pd.DataFrame | None = None,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if state.position_count() >= max_positions and candidate_ticker not in {p.ticker for p in state.positions}:
        reasons.append(f"already at max_positions ({max_positions})")

    sector_exposure = state.sector_exposure_pct()
    projected_sector_pct = sector_exposure.get(candidate_sector, 0.0) + (
        candidate_risk_dollars / state.equity if state.equity else 0.0
    )
    if projected_sector_pct > max_position_pct * 2:   # sector cap = 2x single-position cap, adjustable
        reasons.append(f"sector '{candidate_sector}' exposure would reach {projected_sector_pct:.1%}")

    if state.sector_fail_streak.get(candidate_sector, 0) >= 2:
        reasons.append(f"sector '{candidate_sector}' has 2+ consecutive failed trades — sector paused")

    if corr_matrix is not None and state.equity > 0:
        cluster_risk = correlated_cluster_risk(state, candidate_ticker, candidate_risk_dollars, corr_matrix)
        cluster_pct = cluster_risk / state.equity
        if cluster_pct > max_correlated_cluster_risk_pct:
            reasons.append(
                f"correlated cluster risk would reach {cluster_pct:.2%} > {max_correlated_cluster_risk_pct:.2%}"
            )

    return (len(reasons) == 0, reasons)


def record_sector_result(state: PortfolioState, sector: str, was_win: bool) -> None:
    """Call this from the daily-summary / trade-close workflow to maintain the
    2-consecutive-failed-trades sector pause (original guide behavior, kept
    quantitative per PDF section 9)."""
    if was_win:
        state.sector_fail_streak[sector] = 0
    else:
        state.sector_fail_streak[sector] = state.sector_fail_streak.get(sector, 0) + 1
