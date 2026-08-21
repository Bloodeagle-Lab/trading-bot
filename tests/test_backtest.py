from __future__ import annotations

import pandas as pd

from research.backtest import run_backtest
from tests.conftest import make_config, make_ohlcv


def _price_data(n_tickers: int = 8, n: int = 280) -> dict[str, pd.DataFrame]:
    data = {"SPY": make_ohlcv(n=n, seed=1)}
    for i in range(n_tickers):
        data[f"T{i}"] = make_ohlcv(n=n, seed=100 + i, drift=0.001)
    return data


def test_run_backtest_never_exceeds_max_positions():
    cfg = make_config({"portfolio": {"max_positions": 2, "max_new_trades_per_week": 100, "max_position_pct": 0.20}})
    price_data = _price_data()
    # min_ensemble_score effectively disabled so every candidate "signals" —
    # isolates the portfolio-cap enforcement as the binding constraint.
    result = run_backtest(price_data, "SPY", cfg, min_ensemble_score=-10.0)

    assert len(result.trades) > 0
    for check_date in {t.entry_date for t in result.trades}:
        concurrently_open = sum(1 for t in result.trades if t.entry_date <= check_date <= t.exit_date)
        assert concurrently_open <= 2, f"exceeded max_positions on {check_date}: {concurrently_open} open"


def test_run_backtest_never_exceeds_weekly_trade_cap():
    cfg = make_config({"portfolio": {"max_positions": 100, "max_new_trades_per_week": 1, "max_position_pct": 0.20}})
    price_data = _price_data()
    result = run_backtest(price_data, "SPY", cfg, min_ensemble_score=-10.0)

    assert len(result.trades) > 0
    weeks = {}
    for t in result.trades:
        wk = t.entry_date.isocalendar()[:2]
        weeks[wk] = weeks.get(wk, 0) + 1
    assert all(count <= 1 for count in weeks.values()), f"a week exceeded the cap: {weeks}"


def test_run_backtest_never_double_enters_the_same_ticker_while_open():
    cfg = make_config({"portfolio": {"max_positions": 100, "max_new_trades_per_week": 100, "max_position_pct": 0.20}})
    price_data = _price_data()
    result = run_backtest(price_data, "SPY", cfg, min_ensemble_score=-10.0)

    by_ticker: dict[str, list] = {}
    for t in result.trades:
        by_ticker.setdefault(t.ticker, []).append(t)

    for ticker, trades in by_ticker.items():
        trades_sorted = sorted(trades, key=lambda t: t.entry_date)
        for a, b in zip(trades_sorted, trades_sorted[1:]):
            assert b.entry_date > a.exit_date, (
                f"{ticker} re-entered on {b.entry_date} while a prior trade was still open "
                f"(entry {a.entry_date} -> exit {a.exit_date})"
            )


def test_run_backtest_respects_generous_caps_and_still_trades():
    # Sanity check: with caps effectively unlimited, the fix shouldn't have
    # accidentally made the backtest unable to trade at all.
    cfg = make_config({"portfolio": {"max_positions": 6, "max_new_trades_per_week": 3, "max_position_pct": 0.20}})
    price_data = _price_data()
    result = run_backtest(price_data, "SPY", cfg, min_ensemble_score=-10.0)
    assert len(result.trades) > 0
