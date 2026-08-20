"""
Market-Regime Engine (PDF section 4).

Classifies the current market environment from index trend, volatility and
(optionally) breadth, and outputs BOTH a categorical state and a confidence
value. Regime confidence is an input to risk sizing (quant/risk.py) and to
the NO-TRADE filter (quant/no_trade.py) — it is never used to override a
hard risk gate.

This is a first-version, transparent rule engine on purpose (per the PDF:
"a simple first version can use SPY/QQQ trend, volatility, breadth, and
sector dispersion"). Swap in something fancier later behind the same
`classify_regime` signature.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

STRONG_TREND = "STRONG_TREND"
CHOPPY = "CHOPPY"
HIGH_VOL = "HIGH_VOL"
RISK_OFF = "RISK_OFF"
TRANSITION = "TRANSITION"

VALID_STATES = (STRONG_TREND, CHOPPY, HIGH_VOL, RISK_OFF, TRANSITION)


@dataclass
class RegimeResult:
    state: str
    confidence: float                 # 0..1
    scores: dict[str, float] = field(default_factory=dict)   # per-state raw score, for audit
    features: dict[str, Any] = field(default_factory=dict)   # supporting numbers, for REGIME-LOG.md


def _trend_strength(index_features_row: pd.Series) -> float:
    """+1 = strong healthy uptrend structure, -1 = strong downtrend, 0 = no structure."""
    score = 0.0
    score += 0.4 if index_features_row.get("price_above_sma50") else -0.4
    score += 0.3 if index_features_row.get("sma50_above_sma200") else -0.3
    slope = index_features_row.get("sma20_slope_5d", 0.0) or 0.0
    score += float(np.clip(slope * 20, -0.3, 0.3))
    return float(np.clip(score, -1.0, 1.0))


def classify_regime(
    spy_features_row: pd.Series,
    qqq_features_row: pd.Series | None = None,
    vix_level: float | None = None,
    vix_high_threshold: float = 25.0,
    vix_extreme_threshold: float = 32.0,
    breadth_pct_above_50dma: float | None = None,
) -> RegimeResult:
    """
    Parameters
    ----------
    spy_features_row / qqq_features_row : one row from quant.features.compute_features
        for SPY / QQQ (most recent date).
    vix_level : latest VIX close, if available.
    breadth_pct_above_50dma : fraction (0..1) of the universe above its 50dma, if available.
    """
    trend_spy = _trend_strength(spy_features_row)
    trend_qqq = _trend_strength(qqq_features_row) if qqq_features_row is not None else trend_spy
    trend = (trend_spy + trend_qqq) / 2

    vol_20 = float(spy_features_row.get("volatility_20", 0.0) or 0.0)
    # crude realized-vol regime bands (annualized); refine with historical percentiles later
    vol_elevated = vol_20 > 0.18
    vol_extreme = vol_20 > 0.28
    if vix_level is not None:
        vol_elevated = vol_elevated or vix_level >= vix_high_threshold
        vol_extreme = vol_extreme or vix_level >= vix_extreme_threshold

    breadth_bad = breadth_pct_above_50dma is not None and breadth_pct_above_50dma < 0.35
    breadth_good = breadth_pct_above_50dma is not None and breadth_pct_above_50dma > 0.60

    scores = {
        STRONG_TREND: 0.0,
        CHOPPY: 0.0,
        HIGH_VOL: 0.0,
        RISK_OFF: 0.0,
        TRANSITION: 0.0,
    }

    # Risk-off: broad weakness + deteriorating breadth, dominates other signals
    if trend < -0.3 and (breadth_bad or breadth_pct_above_50dma is None):
        scores[RISK_OFF] = 0.9 if breadth_bad else 0.6

    # High volatility regime — quality bar goes up regardless of direction
    if vol_extreme:
        scores[HIGH_VOL] = 0.9
    elif vol_elevated:
        scores[HIGH_VOL] = 0.55

    # Strong trend — clean directional structure, controlled volatility, healthy breadth
    if trend > 0.5 and not vol_extreme and not breadth_bad:
        scores[STRONG_TREND] = 0.85 if breadth_good else 0.6

    # Choppy / range — weak trend signal, no volatility spike
    if abs(trend) < 0.25 and not vol_elevated:
        scores[CHOPPY] = 0.7

    # Transition — trend and breadth disagree, or trend sign is ambiguous under rising vol
    disagreement = (trend > 0.15 and breadth_bad) or (trend < -0.15 and breadth_good)
    if disagreement or (0.25 <= abs(trend) <= 0.5 and vol_elevated):
        scores[TRANSITION] = max(scores[TRANSITION], 0.6)

    # Pick the highest-scoring state; default to TRANSITION if nothing fired (ambiguous data)
    best_state = max(scores, key=scores.get)
    best_score = scores[best_state]
    if best_score == 0.0:
        best_state, best_score = TRANSITION, 0.3

    # Confidence: how much the winning state clears the runner-up, plus data completeness
    ordered = sorted(scores.values(), reverse=True)
    margin = ordered[0] - (ordered[1] if len(ordered) > 1 else 0.0)
    data_completeness = sum(x is not None for x in (vix_level, breadth_pct_above_50dma)) / 2
    confidence = float(np.clip(0.5 * best_score + 0.35 * margin + 0.15 * data_completeness, 0.0, 1.0))

    return RegimeResult(
        state=best_state,
        confidence=round(confidence, 3),
        scores={k: round(v, 3) for k, v in scores.items()},
        features={
            "trend_spy": round(trend_spy, 3),
            "trend_qqq": round(trend_qqq, 3) if qqq_features_row is not None else None,
            "volatility_20": round(vol_20, 4),
            "vix_level": vix_level,
            "breadth_pct_above_50dma": breadth_pct_above_50dma,
        },
    )
