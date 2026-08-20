"""
Walk-forward testing (PDF section 11).

Rolls a train/validation window forward through history, re-evaluating on
each out-of-sample slice, instead of trusting one lucky in-sample backtest.
This is what the PDF means by "use out-of-sample and walk-forward results
as the primary evidence."
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant.config import Config
from research.backtest import BacktestResult, run_backtest


@dataclass
class WalkForwardWindow:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    result: BacktestResult


def generate_windows(
    start: pd.Timestamp, end: pd.Timestamp,
    train_months: int = 24, test_months: int = 6, step_months: int = 6,
) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
    windows = []
    cursor = start
    while True:
        train_start = cursor
        train_end = train_start + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        if test_end > end:
            break
        windows.append((train_start, train_end, train_end, test_end))
        cursor = cursor + pd.DateOffset(months=step_months)
    return windows


def run_walk_forward(
    price_data: dict[str, pd.DataFrame],
    index_symbol: str,
    cfg: Config,
    train_months: int = 24,
    test_months: int = 6,
    step_months: int = 6,
    **backtest_kwargs,
) -> list[WalkForwardWindow]:
    """Note: this backtest engine does not itself re-fit anything on the
    train slice (the rule-based sleeves have no trainable parameters, and
    quant/model.py's ML model is trained separately — point it at the same
    train_start/train_end via quant.model.ProbabilityModel.fit before running
    each test slice if you're validating the ML layer, not just the sleeves).
    Here, each window's TEST slice is what gets backtested and reported."""
    index_df = price_data[index_symbol]
    start, end = index_df.index.min(), index_df.index.max()
    windows = generate_windows(start, end, train_months, test_months, step_months)

    results = []
    for train_start, train_end, test_start, test_end in windows:
        test_slice = {
            t: df.loc[(df.index >= train_start) & (df.index <= test_end)]  # keep pre-history for indicator warm-up
            for t, df in price_data.items()
        }
        result = run_backtest(test_slice, index_symbol, cfg, **backtest_kwargs)
        # keep only trades whose entry actually falls in the OOS test window
        result.trades = [t for t in result.trades if test_start <= t.entry_date <= test_end]
        results.append(WalkForwardWindow(train_start, train_end, test_start, test_end, result))
    return results


def summarize_walk_forward(windows: list[WalkForwardWindow]) -> pd.DataFrame:
    rows = []
    for w in windows:
        row = {"test_start": w.test_start.date(), "test_end": w.test_end.date(), **w.result.metrics}
        rows.append(row)
    return pd.DataFrame(rows)
