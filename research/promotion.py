"""
Champion / Challenger Framework (PDF section 13).

Do not let the agent rewrite its live strategy whenever a weekly result is
poor. This module is the deterministic gate between "a challenger model
tested well" and "the challenger is now live": it evaluates a fixed set of
promotion criteria (PDF: "minimum out-of-sample sample size, no unacceptable
drawdown increase, stable performance across regimes, and no material
degradation under execution stress") and returns an auditable PROMOTE/RETIRE
decision with a reason attached to every criterion. The LLM may propose a
challenger and read this decision, but it never gets to override it — the
mechanism itself has no discretionary step.

Depends on quant/ (deterministic core) and research/backtest.py +
stress_test.py (validation harness), never the reverse — consistent with the
rest of this codebase's layering: quant/ knows nothing about research/ or
promotion, research/ knows nothing about live execution.
"""
from __future__ import annotations

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import quant.model as model_mod
from quant.config import Config
from research.backtest import Trade, compute_metrics
from research.stress_test import StressTestReport, _equity_curve_from_trades, regime_breakdown, run_full_stress_suite


@dataclass
class PromotionCriteria:
    min_out_of_sample_trades: int
    max_drawdown_increase_pct: float
    min_regime_trades_for_stability_check: int = 5
    min_regime_expectancy_r: float = 0.0
    max_stress_expectancy_drop_r: float = 0.5

    @classmethod
    def from_config(cls, cfg: Config) -> "PromotionCriteria":
        """Pulls the two criteria the PDF's starter config.yaml already has
        dedicated fields for; the regime-stability and stress-resilience
        floors don't have their own VALIDATE-gated config keys yet, so they
        keep their (documented, overridable) defaults here instead of
        silently trusting an unset value."""
        return cls(
            min_out_of_sample_trades=cfg.require_validated("validation.min_out_of_sample_trades"),
            max_drawdown_increase_pct=cfg.require_validated("validation.max_drawdown_increase_pct"),
        )


@dataclass
class CriterionResult:
    name: str
    passed: bool
    detail: str


@dataclass
class PromotionDecision:
    decision: str        # "PROMOTE" | "RETIRE"
    criteria: list[CriterionResult] = field(default_factory=list)
    challenger_metrics: dict = field(default_factory=dict)
    champion_metrics: dict | None = None

    def summary_markdown(self) -> str:
        lines = [f"**Champion/Challenger decision: {self.decision}**", ""]
        for c in self.criteria:
            mark = "PASS" if c.passed else "FAIL"
            lines.append(f"- [{mark}] {c.name}: {c.detail}")
        return "\n".join(lines)


def evaluate_promotion(
    challenger_trades: list[Trade],
    champion_trades: list[Trade] | None,
    cfg: Config,
    starting_equity: float = 100_000.0,
    stress_report: StressTestReport | None = None,
    criteria: PromotionCriteria | None = None,
) -> PromotionDecision:
    """
    Deterministic promote/retire decision. challenger_trades /
    champion_trades must both be genuine out-of-sample trade sets (e.g. from
    research/walk_forward.py) — feeding this a single in-sample backtest
    defeats the entire point of a promotion gate.

    champion_trades may be None ONLY for the very first model (bootstrap
    case): a from-scratch challenger has no live baseline to be compared
    against, so the drawdown-increase criterion is explicitly SKIPPED (and
    reported as such) rather than silently passed on an empty comparison.

    stress_report: pass a pre-computed StressTestReport to avoid re-running
    the stress suite when the caller already has one; otherwise it's
    computed here from challenger_trades.

    criteria: override the criteria pulled from config/strategy.yaml (e.g.
    to apply a stricter regime-stability or stress-resilience floor than the
    defaults, which don't have their own YAML fields yet). Defaults to
    PromotionCriteria.from_config(cfg).
    """
    if not challenger_trades:
        raise ValueError("evaluate_promotion requires at least one challenger trade")

    criteria = criteria or PromotionCriteria.from_config(cfg)
    results: list[CriterionResult] = []

    challenger_metrics = compute_metrics(
        challenger_trades, _equity_curve_from_trades(challenger_trades, starting_equity), starting_equity, pd.DataFrame(),
    )
    champion_metrics = None
    if champion_trades:
        champion_metrics = compute_metrics(
            champion_trades, _equity_curve_from_trades(champion_trades, starting_equity), starting_equity, pd.DataFrame(),
        )

    # 1. Minimum out-of-sample sample size
    n = challenger_metrics["n_trades"]
    ok = bool(n >= criteria.min_out_of_sample_trades)
    results.append(CriterionResult(
        "min_out_of_sample_trades", ok,
        f"{n} OOS trades (need >= {criteria.min_out_of_sample_trades})",
    ))

    # 2. No unacceptable drawdown increase vs the live champion
    if champion_metrics is not None:
        challenger_dd = abs(challenger_metrics["max_drawdown_pct"])
        champion_dd = abs(champion_metrics["max_drawdown_pct"])
        increase = challenger_dd - champion_dd
        ok = bool(increase <= criteria.max_drawdown_increase_pct)
        results.append(CriterionResult(
            "max_drawdown_increase", ok,
            f"challenger DD {challenger_dd:.2f}% vs champion {champion_dd:.2f}% "
            f"({increase:+.2f}pp, allowed up to +{criteria.max_drawdown_increase_pct:.2f}pp)",
        ))
    else:
        results.append(CriterionResult(
            "max_drawdown_increase", True, "no existing champion to compare against — skipped (bootstrap case)",
        ))

    # 3. Stable performance across regimes — not just an attractive aggregate
    regime_metrics = regime_breakdown(challenger_trades, starting_equity)
    unstable = sorted(
        regime for regime, m in regime_metrics.items()
        if m["n_trades"] >= criteria.min_regime_trades_for_stability_check
        and m["expectancy_r"] < criteria.min_regime_expectancy_r
    )
    ok = not unstable
    detail = (
        f"no regime with >={criteria.min_regime_trades_for_stability_check} trades shows negative expectancy"
        if ok else f"negative expectancy with sufficient sample size in: {', '.join(unstable)}"
    )
    results.append(CriterionResult("regime_stability", ok, detail))

    # 4. No material degradation under execution stress
    report = stress_report or run_full_stress_suite(challenger_trades, cfg, starting_equity)
    worst = next((s for s in report.scenarios if s.name == "combined_worst_case"), None)
    if worst is not None:
        drop = challenger_metrics["expectancy_r"] - worst.metrics.get("expectancy_r", challenger_metrics["expectancy_r"])
        ok = bool(drop <= criteria.max_stress_expectancy_drop_r)
        results.append(CriterionResult(
            "stress_resilience", ok,
            f"expectancy drops {drop:.3f}R under combined worst-case stress "
            f"(allowed up to {criteria.max_stress_expectancy_drop_r:.3f}R)",
        ))
    else:
        results.append(CriterionResult("stress_resilience", False, "no combined_worst_case stress scenario found"))

    decision = "PROMOTE" if all(r.passed for r in results) else "RETIRE"
    return PromotionDecision(
        decision=decision, criteria=results,
        challenger_metrics=challenger_metrics, champion_metrics=champion_metrics,
    )


def promote_challenger(name: str, retire_archive: bool = True) -> None:
    """
    Executes an ALREADY-AUDITED PROMOTE decision by copying a challenger's
    model artifacts into the champion slot. This function does not
    re-evaluate criteria itself — call it only after evaluate_promotion()
    returned decision == "PROMOTE", so the deterministic-decision and
    file-mutation concerns stay separate and the caller's audit trail (e.g.
    a memory/MODEL-LOG.md entry citing the PromotionDecision) is what
    actually authorized this, not this function's own judgment.

    Reads quant.model's CHAMPION_DIR/CHALLENGERS_DIR/METADATA_DIR
    dynamically at call time (not as bound defaults), so monkeypatching
    those module attributes in tests works as expected.
    """
    challengers_dir = model_mod.CHALLENGERS_DIR
    champion_dir = model_mod.CHAMPION_DIR
    metadata_dir = model_mod.METADATA_DIR
    champion_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    challenger_joblib = challengers_dir / f"{name}.joblib"
    challenger_features = challengers_dir / f"{name}.features.json"
    challenger_meta = metadata_dir / f"{name}.json"
    for p in (challenger_joblib, challenger_features, challenger_meta):
        if not p.exists():
            raise FileNotFoundError(f"promote_challenger: missing challenger artifact {p}")

    if retire_archive:
        old_champion_meta = metadata_dir / "champion.json"
        if old_champion_meta.exists():
            ts = time.strftime("%Y%m%dT%H%M%S")
            shutil.copy(old_champion_meta, metadata_dir / f"champion_retired_{ts}.json")

    shutil.copy(challenger_joblib, champion_dir / "champion.joblib")
    shutil.copy(challenger_features, champion_dir / "champion.features.json")
    shutil.copy(challenger_meta, metadata_dir / "champion.json")
