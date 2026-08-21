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
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from quant.features import compute_features
from quant.regime import classify_regime

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

FEATURE_COLUMNS = NUMERIC_FEATURE_COLUMNS + RELATIVE_STRENGTH_COLUMNS


def build_labeled_dataset(
    price_data: dict[str, pd.DataFrame],
    index_symbol: str,
    horizon_days: int = 10,
    stop_atr_multiple: float = 1.5,
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
    index itself is a benchmark, not a trade candidate.
    """
    index_df = price_data[index_symbol]
    index_features = compute_features(index_df)

    rows: list[dict] = []
    for ticker, df in price_data.items():
        if ticker == index_symbol:
            continue
        feats = compute_features(df, benchmark_close=index_df["close"])
        candidate_dates = feats.dropna(subset=["sma_200", "atr_14"]).index

        for date in candidate_dates:
            row = feats.loc[date]
            if row[NUMERIC_FEATURE_COLUMNS].isna().any():
                continue

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

            if date not in index_features.index:
                continue
            regime = classify_regime(index_features.loc[date])

            record = {c: float(row[c]) for c in NUMERIC_FEATURE_COLUMNS}
            for c in RELATIVE_STRENGTH_COLUMNS:
                record[c] = float(row[c]) if c in row.index and not pd.isna(row[c]) else 0.0
            record.update({
                "ticker": ticker, "date": date, "regime_state": regime.state,
                "entry_price": entry_price, "stop_price": stop_price,
                "max_high_in_horizon": max_high, "min_low_in_horizon": min_low,
            })
            rows.append(record)

    return pd.DataFrame(rows)
