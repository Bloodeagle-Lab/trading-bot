"""
Strategy Engine sleeves (PDF section 3).

Each sleeve is a pure function: one row of features in, a SleeveScore out
(normalized to [-1, 1] plus a human-readable explanation string). Sleeves
know nothing about each other, about regime weighting, or about sizing —
that composition happens in quant/ensemble.py. This separation is what lets
"each sleeve tested independently" (Phase 2 exit criterion) actually happen:
you can unit-test momentum_score() against fixture rows with no dependency
on the rest of the system.

`features_row` is expected to be one row (a pandas Series) produced by
quant.features.compute_features, optionally with relative_strength_* columns
attached for the relative-strength sleeve.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SleeveScore:
    name: str
    score: float          # -1..1, positive = bullish
    explanation: str


def _clip(x: float) -> float:
    return float(np.clip(x, -1.0, 1.0))


def _safe(row: pd.Series, key: str, default: float = 0.0) -> float:
    val = row.get(key, default)
    return default if val is None or (isinstance(val, float) and np.isnan(val)) else float(val)


def momentum_score(row: pd.Series) -> SleeveScore:
    """Persistent relative strength: 20/60-day returns + volume expansion."""
    r20 = _safe(row, "ret_20d")
    r60 = _safe(row, "ret_60d")
    vol_ratio = _safe(row, "volume_ratio", 1.0)
    rs20 = _safe(row, "relative_strength_20")

    raw = 0.4 * np.tanh(r20 * 8) + 0.3 * np.tanh(r60 * 5) + 0.2 * np.tanh(rs20 * 8) \
        + 0.1 * np.tanh((vol_ratio - 1) * 1.5)
    score = _clip(raw)
    explanation = (
        f"20d ret {r20:+.1%}, 60d ret {r60:+.1%}, rel-strength(20d) {rs20:+.1%}, "
        f"volume {vol_ratio:.2f}x avg -> momentum {score:+.2f}"
    )
    return SleeveScore("momentum", score, explanation)


def trend_score(row: pd.Series) -> SleeveScore:
    """Ride established directional moves: MA structure + ADX + vol-adjusted distance."""
    above50 = _safe(row, "price_above_sma50")
    above200 = _safe(row, "price_above_sma200")
    cross = _safe(row, "sma50_above_sma200")
    adx14 = _safe(row, "adx_14")
    atr_pct = _safe(row, "atr_pct", 0.02)
    slope = _safe(row, "sma20_slope_5d")

    structure = 0.4 * (above50 * 2 - 1) + 0.3 * (above200 * 2 - 1) + 0.3 * (cross * 2 - 1)
    trend_strength = np.clip(adx14 / 40, 0, 1)          # ADX>~25-30 = trending
    vol_adjusted_slope = np.tanh((slope / max(atr_pct, 1e-4)) * 0.5)

    raw = 0.5 * structure * trend_strength + 0.5 * vol_adjusted_slope
    score = _clip(raw)
    explanation = (
        f"MA structure {structure:+.2f}, ADX {adx14:.1f} (strength {trend_strength:.2f}), "
        f"vol-adj slope {vol_adjusted_slope:+.2f} -> trend {score:+.2f}"
    )
    return SleeveScore("trend", score, explanation)


def breakout_score(row: pd.Series) -> SleeveScore:
    """Fresh price discovery: proximity to/through range highs with volume confirmation."""
    dist_from_high = _safe(row, "dist_from_high_20_pct")   # <=0, 0 = at/above the 20d high
    new_high = _safe(row, "new_high_break")
    vol_ratio = _safe(row, "volume_ratio", 1.0)
    range_width = _safe(row, "range_width_pct", 0.1)
    atr_pct = _safe(row, "atr_pct", 0.02)

    proximity = np.clip(1 + dist_from_high * 8, 0, 1)     # within ~12.5% of the high scores >0
    confirmation = np.clip((vol_ratio - 1) * 0.8, -0.5, 1.0)
    consolidation_quality = np.clip(1 - range_width * 2, 0, 1)  # tighter base = higher quality
    breakout_bonus = 0.3 if new_high else 0.0

    raw = 0.45 * proximity + 0.3 * confirmation + 0.15 * consolidation_quality + breakout_bonus
    score = _clip(raw)
    explanation = (
        f"dist-from-20d-high {dist_from_high:+.1%}, new_high={bool(new_high)}, "
        f"volume {vol_ratio:.2f}x avg, base width {range_width:.1%}, ATR% {atr_pct:.1%} "
        f"-> breakout {score:+.2f}"
    )
    return SleeveScore("breakout", score, explanation)


def mean_reversion_score(row: pd.Series) -> SleeveScore:
    """Temporary dislocation: distance from mean via z-score/RSI, tightening volatility."""
    z = _safe(row, "zscore_20")
    rsi14 = _safe(row, "rsi_14", 50.0)
    vol20 = _safe(row, "volatility_20")

    # Long the dip: negative z-score and oversold RSI score positive; overbought scores negative.
    z_component = _clip(-z / 2.0)
    rsi_component = _clip((50 - rsi14) / 30.0)
    vol_contraction_bonus = 0.15 if vol20 < 0.15 else 0.0

    raw = 0.55 * z_component + 0.35 * rsi_component + vol_contraction_bonus
    score = _clip(raw)
    explanation = (
        f"z-score(20d) {z:+.2f}, RSI(14) {rsi14:.1f}, realized vol {vol20:.1%} "
        f"-> mean_reversion {score:+.2f}"
    )
    return SleeveScore("mean_reversion", score, explanation)


def relative_strength_score(row: pd.Series) -> SleeveScore:
    """Prefer leaders over peers: sector/market-relative performance."""
    rs20 = _safe(row, "relative_strength_20")
    rs60 = _safe(row, "relative_strength_60")

    raw = 0.6 * np.tanh(rs20 * 6) + 0.4 * np.tanh(rs60 * 4)
    score = _clip(raw)
    explanation = f"RS(20d) {rs20:+.1%} vs benchmark, RS(60d) {rs60:+.1%} -> relative_strength {score:+.2f}"
    return SleeveScore("relative_strength", score, explanation)


SLEEVE_FUNCS = {
    "momentum": momentum_score,
    "trend": trend_score,
    "breakout": breakout_score,
    "mean_reversion": mean_reversion_score,
    "relative_strength": relative_strength_score,
}


def run_all_sleeves(row: pd.Series, enabled: dict[str, bool] | None = None) -> dict[str, SleeveScore]:
    enabled = enabled or {name: True for name in SLEEVE_FUNCS}
    return {name: fn(row) for name, fn in SLEEVE_FUNCS.items() if enabled.get(name, True)}
