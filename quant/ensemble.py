"""
Ensemble (PDF section 3): combines the five sleeve scores into one
regime-aware ensemble score, without hiding a broken sleeve behind an
attractive aggregate. Each sleeve's raw score is always retained in the
output so every decision can be audited (section 5).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from quant.strategies import SleeveScore, run_all_sleeves


@dataclass
class EnsembleResult:
    ticker: str
    regime: str
    sleeve_scores: dict[str, float]
    sleeve_explanations: dict[str, str]
    weights_used: dict[str, float]
    ensemble_score: float

    def render(self) -> str:
        lines = [f"Ticker: {self.ticker}", f"Regime: {self.regime}"]
        for name, score in self.sleeve_scores.items():
            label = name.replace("_", " ").title()
            lines.append(f"{label}: {score:+.2f}")
        lines.append(f"Ensemble Score: {self.ensemble_score:+.2f}")
        return "\n".join(lines)


def compute_ensemble(
    ticker: str,
    features_row: pd.Series,
    regime_state: str,
    regime_weights: dict[str, dict[str, float]],
    sleeve_enabled: dict[str, bool] | None = None,
) -> EnsembleResult:
    sleeves: dict[str, SleeveScore] = run_all_sleeves(features_row, sleeve_enabled)
    weights = regime_weights.get(regime_state, {name: 1.0 for name in sleeves})

    weighted_sum = 0.0
    weight_total = 0.0
    for name, sleeve in sleeves.items():
        w = weights.get(name, 0.0)
        weighted_sum += sleeve.score * w
        weight_total += w

    ensemble_score = weighted_sum / weight_total if weight_total > 0 else 0.0

    return EnsembleResult(
        ticker=ticker,
        regime=regime_state,
        sleeve_scores={name: round(s.score, 3) for name, s in sleeves.items()},
        sleeve_explanations={name: s.explanation for name, s in sleeves.items()},
        weights_used={name: weights.get(name, 0.0) for name in sleeves},
        ensemble_score=round(ensemble_score, 3),
    )


@dataclass
class SetupQuality:
    """PDF section 5 — the audit record every candidate produces, independent
    of the final PASS/NO-TRADE decision (that decision belongs to
    quant/no_trade.py, which consumes overall_quality + ml_probability)."""
    ticker: str
    technical: float          # 0..100, derived from ensemble_score
    sector: float              # 0..100, sector trend/breadth/leadership
    catalyst: float            # 0..100, specificity/verifiability of the catalyst
    liquidity: float           # 0..100, spread/volume/halt risk
    risk_quality: float        # 0..100, ATR/gap risk/realistic stop distance
    portfolio_fit: float       # 0..100, correlation/exposure/concentration fit
    ml_probability: float | None

    @property
    def overall_quality(self) -> float:
        """Weighted per PDF section 5's component table. ml_probability is
        reported alongside but intentionally excluded from this composite —
        it is the separate, explicit gate applied in quant/no_trade.py, not
        blended away inside a single opaque number."""
        weights = {
            "technical": 0.25, "sector": 0.15, "catalyst": 0.15,
            "liquidity": 0.15, "risk_quality": 0.15, "portfolio_fit": 0.15,
        }
        total = sum(getattr(self, k) * w for k, w in weights.items())
        return round(total, 1)

    def render(self) -> str:
        lines = [
            "SETUP QUALITY",
            f"Overall quality: {self.overall_quality:.0f}/100",
            f"Technical: {self.technical:.0f}",
            f"Sector: {self.sector:.0f}",
            f"Catalyst: {self.catalyst:.0f}",
            f"Liquidity: {self.liquidity:.0f}",
            f"Risk quality: {self.risk_quality:.0f}",
            f"Portfolio fit: {self.portfolio_fit:.0f}",
        ]
        if self.ml_probability is not None:
            lines.append(f"ML probability: {self.ml_probability:.2f}")
        return "\n".join(lines)


def technical_score_from_ensemble(ensemble_score: float) -> float:
    """Maps the -1..1 ensemble score onto the 0..100 technical component."""
    return round((ensemble_score + 1) / 2 * 100, 1)
