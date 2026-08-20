"""
NO-TRADE Filter (PDF section 7).

An explicit model for "insufficient edge" so the optimizer can't treat
activity as success. Every candidate passes through here before sizing.
A NO-TRADE decision is logged with its reason and is a valid, measured
outcome (memory/RISK-LOG.md), not a silent skip.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from quant.config import Config


@dataclass
class NoTradeResult:
    decision: str                 # "PASS" | "NO-TRADE"
    reasons: list[str] = field(default_factory=list)
    reduced_risk: bool = False    # True if allowed to proceed but at reduced size


@dataclass
class Candidate:
    ticker: str
    ensemble_score: float
    ml_probability: float | None
    regime_state: str
    regime_confidence: float
    setup_quality: float           # 0..100 overall quality score
    sleeve_scores: dict[str, float]
    spread_pct: float
    liquidity_ok: bool
    portfolio_concentration_ok: bool
    catalyst_verified: bool
    reward_risk_ratio: float
    market_risk_off_gate_active: bool
    risk_off_exception_validated: bool = False


def _sleeve_disagreement(sleeve_scores: dict[str, float]) -> bool:
    """Disagreement = meaningful sleeves point in opposite directions, not
    just "not all sleeves agree" — a disabled/near-zero sleeve doesn't count."""
    signed = [s for s in sleeve_scores.values() if abs(s) > 0.15]
    if len(signed) < 2:
        return False
    return any(s > 0 for s in signed) and any(s < 0 for s in signed)


def evaluate_no_trade(candidate: Candidate, cfg: Config) -> NoTradeResult:
    reasons: list[str] = []

    prob_threshold = cfg.get("no_trade.probability_threshold")
    if isinstance(prob_threshold, (int, float)):
        if candidate.ml_probability is None or candidate.ml_probability < prob_threshold:
            reasons.append(
                f"model probability {candidate.ml_probability} below validated threshold {prob_threshold}"
            )
    elif candidate.ml_probability is None:
        reasons.append("no ML probability available yet (champion model not trained) — insufficient evidence")

    if _sleeve_disagreement(candidate.sleeve_scores):
        reasons.append(f"sleeve disagreement: {candidate.sleeve_scores}")

    min_conf = cfg.get("no_trade.min_regime_confidence", 0.4)
    if candidate.regime_confidence < min_conf:
        reasons.append(f"regime confidence {candidate.regime_confidence:.2f} below minimum {min_conf:.2f}")

    min_quality = cfg.get("no_trade.min_setup_quality", 60)
    if candidate.setup_quality < min_quality:
        reasons.append(f"setup quality {candidate.setup_quality:.0f} below minimum {min_quality}")

    max_spread = cfg.get("universe.max_spread_pct", 0.5)
    if candidate.spread_pct > max_spread or not candidate.liquidity_ok:
        reasons.append(f"spread/liquidity failed (spread {candidate.spread_pct:.2f}% > {max_spread}% or illiquid)")

    if not candidate.portfolio_concentration_ok:
        reasons.append("portfolio concentration too high for this ticker/sector/correlation cluster")

    if cfg.get("no_trade.require_catalyst_verification", True) and not candidate.catalyst_verified:
        reasons.append("catalyst could not be verified against a specific, current, verifiable source")

    min_rr = cfg.get("strategy.reward_risk_minimum", 2.0)
    if candidate.reward_risk_ratio < min_rr:
        reasons.append(f"reward/risk {candidate.reward_risk_ratio:.2f} below minimum {min_rr:.2f}")

    if candidate.market_risk_off_gate_active and not candidate.risk_off_exception_validated:
        reasons.append("market-wide risk-off gate active and no separately validated exception exists")

    if reasons:
        return NoTradeResult(decision="NO-TRADE", reasons=reasons)
    return NoTradeResult(decision="PASS", reasons=["all gates passed"])
