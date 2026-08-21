"""
Training-data construction for quant/model.py's ProbabilityModel (PDF
section 6).

`quant/model.py`'s `label_outcomes()` and `train_challenger()` need a
DataFrame with feature columns AND entry_price/stop_price/
max_high_in_horizon/min_low_in_horizon per row — this module builds
exactly that from raw OHLCV history, independent of
`research/backtest.py`'s realized-trade simulation (which only records the
rule-based ensemble's ACTUAL entries, gated on `min_ensemble_score`). The
ML model is deliberately trained on a broader set of daily setups than the
ensemble ever actually traded, so it learns to discriminate good setups
from bad ones rather than only ever seeing days the rule engine already
liked — a model trained only on already-filtered "good" days can't learn
what makes a setup bad.

Feature set (see memory/MODEL-LOG.md for the history behind each addition):
  - raw technical indicators (returns, MA structure, ATR, RSI, ADX, ...)
  - relative strength vs the benchmark (SPY)
  - the sleeve/ensemble/regime composite signals quant/strategies.py,
    quant/ensemble.py and quant/regime.py already compute — added
    2026-08-21 after raw indicators alone found no edge across three
    attempts; this alone barely moved the needle (sleeve scores are
    themselves just recombinations of the same raw indicators, not
    independent information)
  - cross-sectional peer rank — where a ticker's 20d return / ensemble
    score ranks among the OTHER tickers in the universe on the SAME date,
    not just vs SPY. Captures sector/market rotation (leaders vs laggards
    on a given day) that a single fixed benchmark comparison can't.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant.ensemble import EnsembleResult, compute_ensemble
from quant.features import compute_features
from quant.regime import VALID_STATES, RegimeResult, classify_regime
from quant.strategies import SLEEVE_FUNCS, SleeveScore, run_all_sleeves

# Numeric, always-present feature columns from quant/features.compute_features()
# that are safe to feed a model directly (feature_version is metadata, not
# a feature; sma_20/50/200 and range_high/low_20 are raw price levels that
# don't generalize across tickers — their DERIVED ratios/flags do, and are
# what's listed here instead).
NUMERIC_FEATURE_COLUMNS = [
    "ret_1d", "ret_5d", "ret_20d", "ret_60d",
    "price_above_sma20", "price_above_sma50", "price_above_sma200",
    "sma20_slope_5d", "sma50_above_sma200",
    "atr_pct", "rsi_14", "adx_14", "zscore_20", "volatility_20", "gap_pct",
    "volume_ratio", "dollar_volume_20",
    "dist_from_high_20_pct", "new_high_break", "range_width_pct",
]
# Only present when a benchmark_close is passed to compute_features().
RELATIVE_STRENGTH_COLUMNS = ["relative_strength_20", "relative_strength_60"]

# The system's own composite signals — not raw indicators, but what the
# sleeve/ensemble/regime engines already conclude from them.
SLEEVE_SCORE_COLUMNS = [f"sleeve_{name}" for name in SLEEVE_FUNCS]
ENSEMBLE_COLUMNS = ["ensemble_score", "regime_confidence"]
REGIME_ONEHOT_COLUMNS = [f"regime_{state}" for state in VALID_STATES]

# Percentile rank (0..1) among the universe on the SAME date — 1.0 = today's
# strongest name, 0.0 = today's weakest, 0.5 = right in the middle.
CROSS_SECTIONAL_COLUMNS = ["cross_sectional_rank_ret20", "cross_sectional_rank_ensemble"]

FEATURE_COLUMNS = (
    NUMERIC_FEATURE_COLUMNS + RELATIVE_STRENGTH_COLUMNS
    + SLEEVE_SCORE_COLUMNS + ENSEMBLE_COLUMNS + REGIME_ONEHOT_COLUMNS
    + CROSS_SECTIONAL_COLUMNS
)


def _percentile_rank(values_by_ticker: dict[str, float], ticker: str) -> float:
    """Fraction of peers this ticker beats on this date, in [0, 1]. 0.5 when
    the ticker or enough peers aren't available (neutral, not a guess)."""
    if ticker not in values_by_ticker or len(values_by_ticker) < 2:
        return 0.5
    v = values_by_ticker[ticker]
    values = list(values_by_ticker.values())
    below = sum(1 for x in values if x < v)
    return below / (len(values) - 1)


def build_labeled_dataset(
    price_data: dict[str, pd.DataFrame],
    index_symbol: str,
    horizon_days: int = 10,
    stop_atr_multiple: float = 1.5,
    regime_weights: dict[str, dict[str, float]] | None = None,
    sleeve_enabled: dict[str, bool] | None = None,
) -> pd.DataFrame:
    """
    Walks every (ticker, date) pair with enough trailing history for a
    stable feature read (past the SMA-200/ATR-14 warmup) and enough
    leading history for a full horizon_days label window, and returns one
    row per pair with every column in FEATURE_COLUMNS, plus
    entry_price/stop_price/max_high_in_horizon/min_low_in_horizon
    (consumed directly by quant/model.py's label_outcomes()) and
    ticker/date/regime_state for later regime-bucketed analysis.

    price_data must include index_symbol (e.g. "SPY") for relative-strength
    features and regime classification; only OTHER tickers get rows — the
    index itself is a benchmark, not a trade candidate. Cross-sectional
    features need the FULL universe passed in one call — running this
    ticker-by-ticker would silently degrade every cross_sectional_rank_*
    column to the neutral 0.5 default.

    regime_weights/sleeve_enabled: passed straight through to
    quant.ensemble.compute_ensemble — pass config/strategy.yaml's
    strategy.regime_weights / strategy.sleeves so ensemble_score reflects
    the same regime-aware weighting the live system actually uses.
    """
    index_df = price_data[index_symbol]
    index_features = compute_features(index_df)
    regime_weights = regime_weights or {}
    sleeve_enabled = sleeve_enabled or {}

    # Regime is identical across all tickers on a given date — compute it
    # once per date instead of once per (ticker, date) pair.
    regime_cache: dict[pd.Timestamp, RegimeResult] = {
        date: classify_regime(index_features.loc[date])
        for date in index_features.dropna(subset=["sma_200"]).index
    }

    # Pass 1: compute features/sleeves/ensemble once per (ticker, date) —
    # reused in pass 2 so nothing is computed twice — and simultaneously
    # build the cross-sectional (date -> {ticker: value}) tables the
    # percentile-rank features need.
    ticker_feats: dict[str, pd.DataFrame] = {}
    per_row_extra: dict[tuple[str, pd.Timestamp], tuple[dict[str, SleeveScore], EnsembleResult, RegimeResult]] = {}
    cross_ret20: dict[pd.Timestamp, dict[str, float]] = {}
    cross_ensemble: dict[pd.Timestamp, dict[str, float]] = {}

    for ticker, df in price_data.items():
        if ticker == index_symbol:
            continue
        feats = compute_features(df, benchmark_close=index_df["close"])
        ticker_feats[ticker] = feats
        for date in feats.dropna(subset=["sma_200", "atr_14"]).index:
            regime = regime_cache.get(date)
            if regime is None:
                continue
            row = feats.loc[date]
            if row[NUMERIC_FEATURE_COLUMNS].isna().any():
                continue

            sleeves = run_all_sleeves(row, sleeve_enabled)
            ensemble = compute_ensemble(ticker, row, regime.state, regime_weights, sleeve_enabled)
            per_row_extra[(ticker, date)] = (sleeves, ensemble, regime)

            cross_ensemble.setdefault(date, {})[ticker] = ensemble.ensemble_score
            ret20 = row.get("ret_20d")
            if ret20 is not None and not pd.isna(ret20):
                cross_ret20.setdefault(date, {})[ticker] = float(ret20)

    rows: list[dict] = []
    for ticker, feats in ticker_feats.items():
        df = price_data[ticker]
        for date in feats.dropna(subset=["sma_200", "atr_14"]).index:
            extra = per_row_extra.get((ticker, date))
            if extra is None:
                continue
            row = feats.loc[date]

            future_idx = df.index[df.index > date]
            if len(future_idx) < horizon_days + 1:
                continue  # not enough forward data for a full label window

            entry_date = future_idx[0]
            entry_price = float(df.loc[entry_date, "open"])
            atr = float(row["atr_14"])
            if atr <= 0 or np.isnan(atr) or entry_price <= 0:
                continue
            stop_price = entry_price - stop_atr_multiple * atr

            window = df.loc[future_idx[:horizon_days]]
            max_high = float(window["high"].max())
            min_low = float(window["low"].min())

            record = {c: float(row[c]) for c in NUMERIC_FEATURE_COLUMNS}
            for c in RELATIVE_STRENGTH_COLUMNS:
                record[c] = float(row[c]) if c in row.index and not pd.isna(row[c]) else 0.0

            sleeves, ensemble, regime = extra
            for name, sleeve in sleeves.items():
                record[f"sleeve_{name}"] = sleeve.score
            record["ensemble_score"] = ensemble.ensemble_score
            record["regime_confidence"] = regime.confidence
            for state in VALID_STATES:
                record[f"regime_{state}"] = 1.0 if regime.state == state else 0.0

            record["cross_sectional_rank_ret20"] = _percentile_rank(cross_ret20.get(date, {}), ticker)
            record["cross_sectional_rank_ensemble"] = _percentile_rank(cross_ensemble.get(date, {}), ticker)

            record.update({
                "ticker": ticker, "date": date, "regime_state": regime.state,
                "entry_price": entry_price, "stop_price": stop_price,
                "max_high_in_horizon": max_high, "min_low_in_horizon": min_low,
            })
            rows.append(record)

    return pd.DataFrame(rows)
