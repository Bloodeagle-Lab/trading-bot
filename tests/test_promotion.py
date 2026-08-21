from __future__ import annotations

import json

import pandas as pd
import pytest

import quant.model as model_mod
from quant.model import ModelMetadata
from research.backtest import Trade
from research.promotion import PromotionCriteria, evaluate_promotion, promote_challenger
from research.stress_test import StressTestReport
from tests.conftest import make_config


def _model_metadata(test_auc=0.65, test_brier=0.15, train_positive_rate=0.30) -> ModelMetadata:
    return ModelMetadata(
        version="v1", algo="logistic_regression", feature_version="1.0.0", feature_columns=["f1"],
        train_window="2020:2021", validation_window="2022", threshold=0.55,
        test_auc=test_auc, test_brier=test_brier, train_positive_rate=train_positive_rate,
        n_train=100, n_test=25, created_ts=0.0,
    )


def _trade(i, r_multiple, regime="STRONG_TREND", exit_reason="target"):
    entry, stop = 100.0, 95.0
    exit_price = entry + r_multiple * (entry - stop)
    return Trade(
        ticker=f"T{i}", entry_date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
        exit_date=pd.Timestamp("2024-01-01") + pd.Timedelta(days=i + 3),
        entry_price=entry, exit_price=exit_price, stop_price=stop, shares=10,
        r_multiple=r_multiple, pnl_dollars=round(r_multiple * (entry - stop) * 10, 2),
        regime_at_entry=regime, ensemble_score=0.6, exit_reason=exit_reason,
    )


def _winning_trades(n=40, regime="STRONG_TREND"):
    # 2 wins for every 1 loss -> net positive expectancy
    return [_trade(i, 1.5 if i % 3 else -1.0, regime=regime, exit_reason="target" if i % 3 else "stop") for i in range(n)]


# ---- evaluate_promotion --------------------------------------------------

def test_evaluate_promotion_rejects_empty_challenger():
    with pytest.raises(ValueError):
        evaluate_promotion([], None, make_config())


def test_bootstrap_case_skips_drawdown_criterion_when_no_champion():
    trades = _winning_trades(40)
    cfg = make_config()
    decision = evaluate_promotion(trades, None, cfg)
    dd_result = next(c for c in decision.criteria if c.name == "max_drawdown_increase")
    assert dd_result.passed is True
    assert "bootstrap" in dd_result.detail
    assert decision.champion_metrics is None


def test_min_out_of_sample_trades_fails_with_too_few_trades():
    trades = _winning_trades(5)
    criteria = PromotionCriteria(min_out_of_sample_trades=30, max_drawdown_increase_pct=100.0,
                                  min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=100.0)
    decision = evaluate_promotion(trades, None, make_config(), criteria=criteria)
    sample_result = next(c for c in decision.criteria if c.name == "min_out_of_sample_trades")
    assert sample_result.passed is False
    assert decision.decision == "RETIRE"


def test_min_out_of_sample_trades_passes_with_enough_trades():
    trades = _winning_trades(40)
    criteria = PromotionCriteria(min_out_of_sample_trades=30, max_drawdown_increase_pct=100.0,
                                  min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=100.0)
    decision = evaluate_promotion(trades, None, make_config(), criteria=criteria)
    sample_result = next(c for c in decision.criteria if c.name == "min_out_of_sample_trades")
    assert sample_result.passed is True


def test_regime_stability_fails_when_one_regime_is_consistently_losing():
    good = _winning_trades(20, regime="STRONG_TREND")
    bad = [_trade(100 + i, -1.0, regime="CHOPPY", exit_reason="stop") for i in range(10)]
    criteria = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                  min_regime_trades_for_stability_check=5, max_stress_expectancy_drop_r=1000.0)
    decision = evaluate_promotion(good + bad, None, make_config(), criteria=criteria)
    regime_result = next(c for c in decision.criteria if c.name == "regime_stability")
    assert regime_result.passed is False
    assert "CHOPPY" in regime_result.detail
    assert decision.decision == "RETIRE"


def test_regime_stability_ignores_small_sample_regimes():
    good = _winning_trades(20, regime="STRONG_TREND")
    tiny_bad = [_trade(100 + i, -1.0, regime="CHOPPY", exit_reason="stop") for i in range(2)]  # below stability floor
    criteria = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                  min_regime_trades_for_stability_check=5, max_stress_expectancy_drop_r=1000.0)
    decision = evaluate_promotion(good + tiny_bad, None, make_config(), criteria=criteria)
    regime_result = next(c for c in decision.criteria if c.name == "regime_stability")
    assert regime_result.passed is True


def test_max_drawdown_increase_fails_when_challenger_much_worse_than_champion():
    champion = _winning_trades(40)
    challenger = _winning_trades(38) + [_trade(900, -8.0, exit_reason="stop"), _trade(901, -8.0, exit_reason="stop")]
    criteria = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=0.05,
                                  min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    decision = evaluate_promotion(challenger, champion, make_config(), criteria=criteria)
    dd_result = next(c for c in decision.criteria if c.name == "max_drawdown_increase")
    assert dd_result.passed is False
    assert decision.decision == "RETIRE"


def test_stress_resilience_fails_when_no_matching_scenario_present():
    trades = _winning_trades(20)
    criteria = PromotionCriteria(min_out_of_sample_trades=5, max_drawdown_increase_pct=1000.0,
                                  min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    fake_report = StressTestReport(baseline_metrics={}, scenarios=[], regime_metrics={})
    decision = evaluate_promotion(trades, None, make_config(), stress_report=fake_report, criteria=criteria)
    stress_result = next(c for c in decision.criteria if c.name == "stress_resilience")
    assert stress_result.passed is False
    assert "no combined_worst_case" in stress_result.detail


def test_all_criteria_pass_yields_promote_decision():
    trades = _winning_trades(40)
    lenient = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                 min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    decision = evaluate_promotion(trades, None, make_config(), criteria=lenient)
    assert decision.decision == "PROMOTE"
    assert all(c.passed for c in decision.criteria)


def test_any_failing_criterion_forces_retire_even_if_others_pass():
    trades = _winning_trades(40)
    strict = PromotionCriteria(min_out_of_sample_trades=10_000, max_drawdown_increase_pct=1000.0,
                                min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    decision = evaluate_promotion(trades, None, make_config(), criteria=strict)
    assert decision.decision == "RETIRE"


def test_summary_markdown_lists_every_criterion():
    trades = _winning_trades(40)
    decision = evaluate_promotion(trades, None, make_config())
    text = decision.summary_markdown()
    for name in ("min_out_of_sample_trades", "max_drawdown_increase", "regime_stability", "stress_resilience"):
        assert name in text


# ---- model_quality criterion ----------------------------------------------

def test_model_quality_skipped_and_passes_when_metadata_omitted():
    trades = _winning_trades(40)
    decision = evaluate_promotion(trades, None, make_config())
    quality = next(c for c in decision.criteria if c.name == "model_quality")
    assert quality.passed is True
    assert "SKIPPED" in quality.detail


def test_model_quality_passes_for_a_genuinely_good_model():
    trades = _winning_trades(40)
    lenient = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                 min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    good_model = _model_metadata(test_auc=0.70, test_brier=0.10, train_positive_rate=0.30)  # baseline brier = 0.21
    decision = evaluate_promotion(trades, None, make_config(), criteria=lenient, challenger_model_metadata=good_model)
    quality = next(c for c in decision.criteria if c.name == "model_quality")
    assert quality.passed is True
    assert decision.decision == "PROMOTE"


def test_model_quality_fails_on_weak_auc():
    trades = _winning_trades(40)
    lenient = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                 min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    weak_model = _model_metadata(test_auc=0.51, test_brier=0.10, train_positive_rate=0.30)
    decision = evaluate_promotion(trades, None, make_config(), criteria=lenient, challenger_model_metadata=weak_model)
    quality = next(c for c in decision.criteria if c.name == "model_quality")
    assert quality.passed is False
    assert decision.decision == "RETIRE"


def test_model_quality_fails_when_brier_worse_than_naive_baseline():
    # This is the exact real-world case that motivated the criterion:
    # positive_rate=0.169 -> naive baseline brier = 0.169*0.831 = 0.1404;
    # a model scoring 0.248 is WORSE than just guessing the base rate.
    trades = _winning_trades(40)
    lenient = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                 min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    bad_model = _model_metadata(test_auc=0.567, test_brier=0.248, train_positive_rate=0.169)
    decision = evaluate_promotion(trades, None, make_config(), criteria=lenient, challenger_model_metadata=bad_model)
    quality = next(c for c in decision.criteria if c.name == "model_quality")
    assert quality.passed is False
    assert decision.decision == "RETIRE"


def test_model_quality_handles_nan_auc_safely():
    trades = _winning_trades(40)
    lenient = PromotionCriteria(min_out_of_sample_trades=10, max_drawdown_increase_pct=1000.0,
                                 min_regime_trades_for_stability_check=1000, max_stress_expectancy_drop_r=1000.0)
    nan_model = _model_metadata(test_auc=float("nan"), test_brier=0.10, train_positive_rate=0.30)
    decision = evaluate_promotion(trades, None, make_config(), criteria=lenient, challenger_model_metadata=nan_model)
    quality = next(c for c in decision.criteria if c.name == "model_quality")
    assert quality.passed is False  # NaN AUC must never silently pass


# ---- promote_challenger ---------------------------------------------------

@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    champion, challengers, metadata = tmp_path / "champion", tmp_path / "challengers", tmp_path / "metadata"
    monkeypatch.setattr(model_mod, "CHAMPION_DIR", champion)
    monkeypatch.setattr(model_mod, "CHALLENGERS_DIR", challengers)
    monkeypatch.setattr(model_mod, "METADATA_DIR", metadata)
    challengers.mkdir(parents=True)
    metadata.mkdir(parents=True)
    return {"champion": champion, "challengers": challengers, "metadata": metadata}


def _fake_challenger_artifacts(dirs, name="challenger_v1"):
    (dirs["challengers"] / f"{name}.joblib").write_bytes(b"fake-model-bytes")
    (dirs["challengers"] / f"{name}.features.json").write_text(json.dumps(["f1", "f2"]))
    (dirs["metadata"] / f"{name}.json").write_text(json.dumps({"version": name}))


def test_promote_challenger_raises_if_artifacts_missing(isolated_dirs):
    with pytest.raises(FileNotFoundError):
        promote_challenger("nonexistent")


def test_promote_challenger_copies_artifacts_into_champion_slot(isolated_dirs):
    _fake_challenger_artifacts(isolated_dirs, "challenger_v1")
    promote_challenger("challenger_v1", retire_archive=False)

    assert (isolated_dirs["champion"] / "champion.joblib").read_bytes() == b"fake-model-bytes"
    assert json.loads((isolated_dirs["champion"] / "champion.features.json").read_text()) == ["f1", "f2"]
    assert json.loads((isolated_dirs["metadata"] / "champion.json").read_text())["version"] == "challenger_v1"


def test_promote_challenger_archives_previous_champion_when_present(isolated_dirs):
    (isolated_dirs["metadata"] / "champion.json").write_text(json.dumps({"version": "old_champion"}))
    _fake_challenger_artifacts(isolated_dirs, "challenger_v2")

    promote_challenger("challenger_v2", retire_archive=True)

    archived = list(isolated_dirs["metadata"].glob("champion_retired_*.json"))
    assert len(archived) == 1
    assert json.loads(archived[0].read_text())["version"] == "old_champion"
    assert json.loads((isolated_dirs["metadata"] / "champion.json").read_text())["version"] == "challenger_v2"


def test_promote_challenger_without_archive_flag_does_not_create_archive(isolated_dirs):
    (isolated_dirs["metadata"] / "champion.json").write_text(json.dumps({"version": "old_champion"}))
    _fake_challenger_artifacts(isolated_dirs, "challenger_v3")

    promote_challenger("challenger_v3", retire_archive=False)

    archived = list(isolated_dirs["metadata"].glob("champion_retired_*.json"))
    assert archived == []
