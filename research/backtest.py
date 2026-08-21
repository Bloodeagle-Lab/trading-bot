"""
Backtest engine (PDF section 11).

Simplifications made explicit up front, so nobody mistakes this for a
production-fidelity simulator:
  - entries fill at next bar's open; exits check each subsequent bar's
    high/low against target/stop (target-and-stop-in-same-bar defaults to
    a loss, matching quant/model.py's label_outcomes conservatism)
  - no partial fills, no intrabar order queueing
  - universe passed in must already be survivorship-aware (point-in-time
    membership) — this module does not fetch or curate history itself

Use this for sleeve/ensemble research and to generate the trade set that
research/walk_forward.py, research/monte_carlo.py and research/stress_test.py
consume. Do not tune thresholds by staring at the aggregate metrics here
until they look good — that is exactly the overfitting path the PDF warns
against; use walk-forward + a final untouched holdout as the real evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from quant.config import Config
from quant.ensemble import compute_ensemble, technical_score_from_ensemble
from quant.features import compute_features
from quant.regime import classify_regime
from quant.risk import classify_setup_state, risk_budget_pct, size_position


@dataclass
class Trade:
    ticker: str
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    stop_price: float
    shares: int
    r_multiple: float
    pnl_dollars: float
    regime_at_entry: str
    ensemble_score: float
    exit_reason: str        # "target" | "stop" | "horizon_close"


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    metrics: dict[str, float]


def _simulate_exit(
    future_bars: pd.DataFrame, entry_price: float, stop_price: float,
    reward_risk: float, horizon_days: int,
) -> tuple[pd.Timestamp, float, str]:
    r = abs(entry_price - stop_price)
    target = entry_price + reward_risk * r if entry_price > stop_price else entry_price - reward_risk * r
    is_long = entry_price > stop_price

    window = future_bars.head(horizon_days)
    for date, bar in window.iterrows():
        hit_target = bar["high"] >= target if is_long else bar["low"] <= target
        hit_stop = bar["low"] <= stop_price if is_long else bar["high"] >= stop_price
        if hit_target and hit_stop:
            return date, stop_price, "stop"          # conservative: ambiguous same-bar -> stop
        if hit_target:
            return date, target, "target"
        if hit_stop:
            return date, stop_price, "stop"

    if window.empty:
        return future_bars.index[-1] if len(future_bars) else pd.Timestamp.now(), entry_price, "horizon_close"
    last_date = window.index[-1]
    return last_date, float(window.iloc[-1]["close"]), "horizon_close"


def run_backtest(
    price_data: dict[str, pd.DataFrame],
    index_symbol: str,
    cfg: Config,
    starting_equity: float = 100_000.0,
    min_ensemble_score: float = 0.55,
    reward_risk: float = 2.0,
    horizon_days: int = 10,
    stop_atr_multiple: float = 1.5,
) -> BacktestResult:
    """
    price_data: {ticker: OHLCV DataFrame indexed by date}, must include index_symbol
    (e.g. "SPY") for regime classification. All frames should share a trading
    calendar; missing dates are forward-filled by the caller before this runs.
    """
    index_df = price_data[index_symbol]
    index_features = compute_features(index_df)

    features_by_ticker = {
        t: compute_features(df, benchmark_close=index_df["close"])
        for t, df in price_data.items() if t != index_symbol
    }

    all_dates = sorted(index_features.dropna(subset=["sma_200"]).index)
    equity = starting_equity
    equity_curve = {}
    trades: list[Trade] = []

    regime_weights = cfg.get("strategy.regime_weights", {})
    sleeve_enabled = cfg.get("strategy.sleeves", {})
    max_positions = cfg.get("portfolio.max_positions", 6)
    max_new_trades_per_week = cfg.get("portfolio.max_new_trades_per_week", 3)

    for date in all_dates:
        regime = classify_regime(index_features.loc[date])

        # Portfolio-level caps, mirroring quant/execution.py's live gates —
        # without these the backtest can (and did) simulate far more
        # concurrent positions and weekly entries than the live strategy is
        # ever allowed to hold, making its trade count and returns
        # unrepresentative of what actually gets traded.
        open_count = sum(1 for t in trades if t.entry_date <= date <= t.exit_date)
        week_key = date.isocalendar()[:2]
        week_count = sum(1 for t in trades if t.entry_date.isocalendar()[:2] == week_key)
        open_ticker_set = {t.ticker for t in trades if t.entry_date <= date <= t.exit_date}

        for ticker, feats in features_by_ticker.items():
            if open_count >= max_positions:
                break  # no capacity for any more entries today, any ticker
            if week_count >= max_new_trades_per_week:
                break  # weekly cap already hit — no more entries this week
            if ticker in open_ticker_set or date not in feats.index:
                continue
            row = feats.loc[date]
            if row.isna().get("atr_14", True):
                continue

            ensemble = compute_ensemble(ticker, row, regime.state, regime_weights, sleeve_enabled)
            if ensemble.ensemble_score < min_ensemble_score:
                continue

            future_idx = feats.index[feats.index > date]
            if len(future_idx) == 0:
                continue
            entry_date = future_idx[0]
            entry_price = float(price_data[ticker].loc[entry_date, "open"])
            atr = float(row["atr_14"]) if not np.isnan(row["atr_14"]) else entry_price * 0.02
            stop_price = entry_price - stop_atr_multiple * atr

            setup_state = classify_setup_state(
                setup_quality=technical_score_from_ensemble(ensemble.ensemble_score),
                regime_state=regime.state, regime_confidence=regime.confidence,
                portfolio_concentration_ok=True, hard_gate_failed=False,
            )
            budget = risk_budget_pct(setup_state, quality_within_band=0.5)
            sizing = size_position(
                equity=equity, risk_budget=budget, entry_price=entry_price, stop_price=stop_price,
                max_position_value=equity * cfg.get("portfolio.max_position_pct", 0.20),
                available_cash=equity, liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
            )
            if sizing.shares <= 0:
                continue

            future_bars = price_data[ticker].loc[price_data[ticker].index > entry_date]
            exit_date, exit_price, reason = _simulate_exit(
                future_bars, entry_price, stop_price, reward_risk, horizon_days
            )
            pnl = (exit_price - entry_price) * sizing.shares
            r_multiple = (exit_price - entry_price) / (entry_price - stop_price) if entry_price != stop_price else 0.0

            equity += pnl
            trades.append(Trade(
                ticker=ticker, entry_date=entry_date, exit_date=exit_date,
                entry_price=entry_price, exit_price=exit_price, stop_price=stop_price,
                shares=sizing.shares, r_multiple=round(r_multiple, 3), pnl_dollars=round(pnl, 2),
                regime_at_entry=regime.state, ensemble_score=ensemble.ensemble_score, exit_reason=reason,
            ))
            open_count += 1
            week_count += 1
            open_ticker_set.add(ticker)

        equity_curve[date] = equity

    curve = pd.Series(equity_curve).sort_index()
    metrics = compute_metrics(trades, curve, starting_equity, index_df)
    return BacktestResult(trades=trades, equity_curve=curve, metrics=metrics)


def compute_metrics(trades: list[Trade], equity_curve: pd.Series, starting_equity: float, benchmark_df: pd.DataFrame) -> dict[str, float]:
    if equity_curve.empty:
        return {"error": "no data"}

    total_return = equity_curve.iloc[-1] / starting_equity - 1
    days = (equity_curve.index[-1] - equity_curve.index[0]).days or 1
    cagr = (1 + total_return) ** (365 / days) - 1

    daily_rets = equity_curve.pct_change().dropna()
    sharpe = (daily_rets.mean() / daily_rets.std() * np.sqrt(252)) if daily_rets.std() > 0 else 0.0
    downside = daily_rets[daily_rets < 0]
    sortino = (daily_rets.mean() / downside.std() * np.sqrt(252)) if len(downside) and downside.std() > 0 else 0.0

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    max_dd = drawdown.min()

    wins = [t for t in trades if t.pnl_dollars > 0]
    losses = [t for t in trades if t.pnl_dollars <= 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    gross_profit = sum(t.pnl_dollars for t in wins)
    gross_loss = abs(sum(t.pnl_dollars for t in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    expectancy_r = np.mean([t.r_multiple for t in trades]) if trades else 0.0

    bench_return = benchmark_df["close"].iloc[-1] / benchmark_df["close"].iloc[0] - 1 if len(benchmark_df) else None

    return {
        "total_return_pct": round(total_return * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "win_rate_pct": round(win_rate * 100, 1),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else None,
        "expectancy_r": round(expectancy_r, 3),
        "avg_win_dollars": round(np.mean([t.pnl_dollars for t in wins]), 2) if wins else 0.0,
        "avg_loss_dollars": round(np.mean([t.pnl_dollars for t in losses]), 2) if losses else 0.0,
        "n_trades": len(trades),
        "benchmark_return_pct": round(bench_return * 100, 2) if bench_return is not None else None,
    }
