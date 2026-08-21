#!/usr/bin/env python3
"""
One-off research script: fetches historical data, builds a labeled
training dataset, trains a first-pass champion model, and validates the
underlying rule-based sleeve engine via walk-forward + Monte Carlo +
stress test + the champion/challenger promotion criteria.

This is a DELIBERATE, MANUALLY-INVOKED research activity — no routine ever
calls this script. See CLAUDE.md's layering rule and
memory/TRADING-STRATEGY.md's champion/challenger section: model training
and promotion are never automatic.

Usage: python3 scripts/train_champion.py
"""
from __future__ import annotations

import dataclasses
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from quant.config import load_config
from quant.model import label_outcomes, train_challenger
from research.build_training_data import FEATURE_COLUMNS, build_labeled_dataset
from research.monte_carlo import run_monte_carlo
from research.promotion import evaluate_promotion, promote_challenger
from research.stress_test import run_full_stress_suite
from research.walk_forward import run_walk_forward
from scripts.quant_cli import _build_clients, _fetch_daily_bars

# A diversified, liquid large-cap universe across sectors — not a
# scientifically optimal choice, just a reasonable, non-cherry-picked
# first-pass basket so the model sees a range of behavior, not one sector's
# idiosyncrasies.
UNIVERSE = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "META", "AVGO", "CRM", "ORCL",
    "JNJ", "UNH", "PFE", "MRK", "ABBV",
    "JPM", "BAC", "GS", "V", "MA",
    "XOM", "CVX", "COP",
    "WMT", "PG", "KO", "MCD", "HD", "NKE",
    "CAT", "GE",
]
INDEX_SYMBOL = "SPY"
LOOKBACK_TRADING_DAYS = 2500  # ~10 calendar years -- this account's data goes back to
                              # ~2016; spans multiple regimes (2020 crash, 2022 bear,
                              # 2023-24 bull), not just one recent 3-year window.
HORIZON_DAYS = 10
WIN_R, LOSS_R = 2.0, -1.0
STARTING_EQUITY = 100_000.0
STARTING_THRESHOLD = 0.55  # config/strategy.yaml's own suggested starting point
ALGO = "gradient_boosting"  # or "logistic_regression" -- see quant/model.py's ALGOS


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fetch_universe(cfg) -> dict[str, pd.DataFrame]:
    _, data_client = _build_clients(cfg)
    price_data: dict[str, pd.DataFrame] = {}
    log(f"Fetching {INDEX_SYMBOL} ({LOOKBACK_TRADING_DAYS} trading days)...")
    price_data[INDEX_SYMBOL] = _fetch_daily_bars(data_client, INDEX_SYMBOL, LOOKBACK_TRADING_DAYS)
    for ticker in UNIVERSE:
        try:
            price_data[ticker] = _fetch_daily_bars(data_client, ticker, LOOKBACK_TRADING_DAYS)
            log(f"  {ticker}: {len(price_data[ticker])} bars, "
                f"{price_data[ticker].index[0].date()} -> {price_data[ticker].index[-1].date()}")
        except Exception as e:
            log(f"  {ticker}: SKIPPED ({e})")
    return price_data


def main() -> None:
    cfg = load_config()
    price_data = fetch_universe(cfg)
    if len(price_data) < 10:
        log(f"Only {len(price_data)} symbols fetched successfully -- aborting, too few for a meaningful training set.")
        sys.exit(1)

    log("Building labeled dataset (features + forward-looking labels)...")
    dataset = build_labeled_dataset(price_data, INDEX_SYMBOL, horizon_days=HORIZON_DAYS)
    dataset = dataset.sort_values("date").reset_index(drop=True)
    labels = label_outcomes(dataset, win_r=WIN_R, loss_r=LOSS_R, horizon_days=HORIZON_DAYS)
    log(f"Dataset: {len(dataset)} rows, {dataset['ticker'].nunique()} tickers, "
        f"{dataset['date'].min().date()} -> {dataset['date'].max().date()}")
    log(f"Class balance: {labels.mean():.1%} positive (reached +{WIN_R}R before {LOSS_R}R within {HORIZON_DAYS}d)")

    log(f"Training challenger model (time-aware split, {ALGO})...")
    version = f"v2_{ALGO[:4]}_{time.strftime('%Y%m%d')}"
    dataset_with_labels = dataset.copy()
    model = train_challenger(
        dataset_with_labels, feature_columns=FEATURE_COLUMNS,
        train_window=f"{dataset['date'].min().date()}:{dataset['date'].max().date()}",
        validation_window="held-out 20% tail (time-aware split)",
        threshold=STARTING_THRESHOLD, version=version, algo=ALGO,
        win_r=WIN_R, loss_r=LOSS_R, horizon_days=HORIZON_DAYS, test_size=0.2,
    )
    log(f"Model trained: test_auc={model.metadata.test_auc:.3f}, test_brier={model.metadata.test_brier:.3f}, "
        f"n_train={model.metadata.n_train}, n_test={model.metadata.n_test}")

    log("Running walk-forward validation of the rule-based sleeve engine...")
    windows = run_walk_forward(
        price_data, INDEX_SYMBOL, cfg,
        train_months=24, test_months=6, step_months=6,
        min_ensemble_score=STARTING_THRESHOLD, reward_risk=WIN_R, horizon_days=HORIZON_DAYS,
    )
    oos_trades = [t for w in windows for t in w.result.trades]
    log(f"Walk-forward: {len(windows)} windows, {len(oos_trades)} total OOS trades")
    if not oos_trades:
        log("No OOS trades produced by the rule-based engine over this window -- cannot validate promotion. Stopping.")
        sys.exit(1)

    log("Running Monte Carlo simulation on OOS trades...")
    mc = run_monte_carlo(oos_trades, starting_equity=STARTING_EQUITY, n_runs=5000, method="block_bootstrap",
                          risk_pct_per_trade=0.005, seed=42)
    print(mc.summary_markdown())

    log("Running stress test on OOS trades...")
    stress_report = run_full_stress_suite(oos_trades, cfg, starting_equity=STARTING_EQUITY, seed=42)
    print(stress_report.summary_markdown())

    log("Evaluating champion/challenger promotion criteria (bootstrap case -- no existing champion)...")
    decision = evaluate_promotion(oos_trades, champion_trades=None, cfg=cfg, starting_equity=STARTING_EQUITY,
                                   stress_report=stress_report, challenger_model_metadata=model.metadata)
    print(decision.summary_markdown())

    if decision.decision == "PROMOTE":
        log("PROMOTE -- saving challenger and promoting to champion.")
        model.save(version, directory=ROOT / "models" / "challengers")
        promote_challenger(version, retire_archive=True)
        log(f"Champion promoted: {version}")
    else:
        log("RETIRE -- not promoting. Model and walk-forward results are printed above for review.")
        model.save(version, directory=ROOT / "models" / "challengers")
        log(f"Challenger artifacts saved (not promoted): models/challengers/{version}.*")

    print("\n=== SUMMARY (for memory/MODEL-LOG.md) ===")
    print(f"Version: {version}")
    print(f"Dataset: {len(dataset)} rows, {dataset['ticker'].nunique()} tickers, "
          f"{dataset['date'].min().date()} -> {dataset['date'].max().date()}")
    print(f"Model: test_auc={model.metadata.test_auc:.3f}, test_brier={model.metadata.test_brier:.3f}")
    print(f"Walk-forward: {len(windows)} windows, {len(oos_trades)} OOS trades")
    print(f"Promotion decision: {decision.decision}")
    for c in decision.criteria:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name}: {c.detail}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
