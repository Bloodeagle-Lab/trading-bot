"""
NO-TRADE Filter (PDF section 7).

An explicit model for "insufficient edge" so the optimizer can't treat
activity as success. Every candidate passes through here before sizing.
A NO-TRADE decision is logged with its reason and is a valid, measured
outcome (memory/RISK-LOG.md), not a silent skip.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from quant.config import Config, UnvalidatedParameterError


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
    require_ml = cfg.get("no_trade.require_ml_probability", True)  # fail-safe default; only
                                                                    # config/strategy.yaml flips this,
                                                                    # never a hardcoded assumption here

    if candidate.ml_probability is None:
        if require_ml:
            reasons.append("no ML probability available yet (champion model not trained) — insufficient evidence")
        else:
            # Rule-engine-only fallback (no_trade.require_ml_probability: false
            # — a deliberate, evidenced decision, see memory/TRADING-STRATEGY.md
            # and memory/MODEL-LOG.md's 2026-08-21 entries). Compensates for the
            # missing ML confirmation layer by requiring the candidate clear
            # the SAME minimum_ensemble_score that was actually walk-forward /
            # Monte-Carlo / stress-tested — not a new, unvalidated number
            # invented just to unblock trading. Every other gate below
            # (catalyst verification, regime confidence, liquidity, portfolio
            # concentration, reward:risk) still applies unchanged.
            try:
                min_ensemble = cfg.require_validated("strategy.minimum_ensemble_score")
            except UnvalidatedParameterError:
                reasons.append(
                    "no_trade.require_ml_probability=false but strategy.minimum_ensemble_score is "
                    "still VALIDATE/unset — cannot run the rule-engine-only fallback without it"
                )
            else:
                if candidate.ensemble_score < min_ensemble:
                    reasons.append(
                        f"no ML confirmation available (require_ml_probability=false); ensemble score "
                        f"{candidate.ensemble_score:.2f} below the validated minimum {min_ensemble:.2f}"
                    )
    elif isinstance(prob_threshold, (int, float)) and candidate.ml_probability < prob_threshold:
        reasons.append(
            f"model probability {candidate.ml_probability} below validated threshold {prob_threshold}"
        )

    if _sleeve_disagreement(candidate.sleeve_scores):
        reasons.append(f"sleeve disagreement: {candidate.sleeve_scores}")

    min_conf = cfg.get("no_trade.min_regime_confidence", 0.4)
    if candidate.regime_confidence < min_conf:
        reasons.append(f"regime confidence {candidate.regime_confidence:.2f} below minimum {min_conf:.2f}")

    min_quality = cfg.get("no_trade.min_setup_quality", 60)
    if candidate.setup_quality < min_quality:
        reasons.append(f"setup quality {candidate.setup_quality:.0f} below minimum {min_quality}")

    # Trust candidate.liquidity_ok as the single source of truth for the
    # spread/illiquidity check — it exists on Candidate specifically so the
    # caller (which knows the live-vs-paper spread threshold; see
    # scripts/quant_cli.py's _resolve_max_spread_pct) decides this once.
    # This function used to ALSO re-derive its own threshold via
    # cfg.get("universe.max_spread_pct", 0.5) and OR it in — always the
    # real 0.5% regardless of mode, so it silently overrode the caller's
    # correct paper-mode decision and kept rejecting candidates that had
    # already legitimately passed. Found 2026-08-24 testing AYI: liquidity_ok
    # was True (5.94% under the paper-mode 6.0% allowance) but this function
    # still failed it citing "> 0.5%".
    if not candidate.liquidity_ok:
        reasons.append(f"spread/liquidity failed (spread {candidate.spread_pct:.2f}%, illiquid or too wide)")

    if not candidate.portfolio_concentration_ok:
        reasons.append("portfolio concentration too high for this ticker/sector/correlation cluster")

    if cfg.get("no_trade.require_catalyst_verification", True) and not candidate.catalyst_verified:
        reasons.append("catalyst could not be verified against a specific, current, verifiable source")

    min_rr = cfg.get("strategy.reward_risk_minimum", 2.0)
    # 1e-9 epsilon: entry/stop/target are rounded decimals (e.g. 148.30,
    # 141.67) that aren't exactly representable in binary floating point,
    # so a genuinely-at-target 2.0 R:R setup can compute as 1.9999999999999998
    # and get spuriously rejected by a strict `<` here -- observed live on a
    # real candidate. This tolerance absorbs float noise, not real shortfall.
    if candidate.reward_risk_ratio < min_rr - 1e-9:
        reasons.append(f"reward/risk {candidate.reward_risk_ratio:.2f} below minimum {min_rr:.2f}")

    if candidate.market_risk_off_gate_active and not candidate.risk_off_exception_validated:
        reasons.append("market-wide risk-off gate active and no separately validated exception exists")

    if reasons:
        return NoTradeResult(decision="NO-TRADE", reasons=reasons)
    return NoTradeResult(decision="PASS", reasons=["all gates passed"])
