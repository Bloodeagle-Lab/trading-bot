#!/usr/bin/env python3
"""
CLI bridge between Claude Code (routines/, .claude/commands/) and the
deterministic quant/ decision engine. See CLAUDE.md's layering rule:
Claude never computes a number that determines sizing or order placement —
every subcommand here does that instead, and prints exactly ONE JSON object
to stdout so Claude reads structured data out of the bash tool's output,
never parses prose for numbers.

On a handled error, prints {"error": "..."} to stdout and exits 1. On
success, prints the result object and exits 0. A raw traceback (unhandled
exception) is printed to STDERR, not stdout, so it never gets mistaken for
a JSON result.

Usage: python3 scripts/quant_cli.py <subcommand> [args...]

Read-only / research subcommands (no live orders placed):
  regime                       classify today's market regime from SPY (+ QQQ)
  scan TICKER [TICKER ...]     ensemble-score a list of candidate tickers
  evaluate TICKER              full pipeline: features -> ensemble -> ML
                                probability -> NO-TRADE decision -> position
                                size. Does NOT place an order.
  positions                    positions + unrealized P&L + stop-order presence
  stops-check                  sell-side rule evaluation (close/tighten/hold
                                per position) — read-only, proposes actions
  reconcile                    live-vs-local drift check (also appends to
                                memory/RISK-LOG.md — see quant/reconciliation.py)

Order-placing subcommands (touch the real account, paper by default):
  execute TICKER                market buy + trailing stop, gated
  close TICKER                  market-sell a position, cancel its stop orders
  tighten-stop TICKER           cancel + replace a position's trailing stop

Run `python3 scripts/quant_cli.py <subcommand> --help` for each one's flags.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import traceback
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from quant.config import Config, load_config
from quant.ensemble import SetupQuality, compute_ensemble, technical_score_from_ensemble
from quant.execution import ExecutionGate, OrderRequest
from quant.features import compute_features
from quant.model import predict_with_champion
from quant.no_trade import Candidate, evaluate_no_trade
from quant.reconciliation import reconcile as reconcile_positions
from quant.regime import BREADTH_PROXY_UNIVERSE, classify_regime, compute_breadth
from quant.risk import classify_setup_state, risk_budget_pct, size_position


# ---------------------------------------------------------------------------
# JSON safety — every subcommand's output flows through this before printing.
# ---------------------------------------------------------------------------

def to_jsonable(obj: Any) -> Any:
    """Recursively converts dataclasses / numpy scalars / pandas Timestamps
    into plain JSON-safe Python types. quant/promotion.py had a real bug
    where a numpy bool_ leaked into a field typed `bool` and would have
    broken json.dumps the first time it got serialized — this is the
    blanket guard against that class of bug at the one place (this CLI)
    where everything must actually serialize."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        # NaN/Infinity are not valid JSON tokens — json.dumps emits them
        # anyway (a non-standard extension), producing output most JSON
        # readers, including Claude reading this as structured data, can't
        # parse. `null` is the honest representation of "no value here."
        return None if (f != f or f in (float("inf"), float("-inf"))) else f
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def print_result(result: dict, error: bool = False) -> int:
    print(json.dumps(to_jsonable(result), indent=2, default=str))
    return 1 if error else 0


# ---------------------------------------------------------------------------
# Pure decision logic — no network, unit-tested directly (tests/test_quant_cli.py)
# ---------------------------------------------------------------------------

def validate_tighten_stop(
    new_trail_pct: float, current_trail_pct: float | None, min_distance_pct: float = 3.0,
) -> tuple[bool, str]:
    """Encodes two hard rules from memory/TRADING-STRATEGY.md as one
    deterministic check: never tighten a stop to within min_distance_pct of
    current price, and never move a stop down (a HIGHER trail_percent means
    a stop further from price, i.e. looser — so tightening must only ever
    decrease trail_percent from whatever it currently is)."""
    if new_trail_pct < min_distance_pct:
        return False, f"{new_trail_pct}% is within the {min_distance_pct}% never-tighten-this-close guardrail"
    if current_trail_pct is not None and new_trail_pct > current_trail_pct:
        return False, f"{new_trail_pct}% is looser than current {current_trail_pct}% — never move a stop down"
    return True, "ok"


def compute_stops_check_actions(positions: list[dict], cfg: Config) -> list[dict]:
    """Pure, network-free sell-side rule evaluation (memory/TRADING-STRATEGY.md
    "Sell-Side Rules"). Each position dict needs: ticker, unrealized_pl_pct
    (a fraction, e.g. -0.08 for -8%), and current_trail_pct (None if no
    trailing stop is currently on file). cmd_stops_check() is the thin live
    wrapper that fetches these from Alpaca and calls this function."""
    hard_loss_cut = cfg.get("stops.hard_loss_cut_pct", 7) / 100
    trail1_pct = cfg.get("stops.winner_trail_1_pct", 7)
    trail1_trigger = cfg.get("stops.winner_trail_1_trigger_gain_pct", 15) / 100
    trail2_pct = cfg.get("stops.winner_trail_2_pct", 5)
    trail2_trigger = cfg.get("stops.winner_trail_2_trigger_gain_pct", 20) / 100

    actions = []
    for pos in positions:
        ticker = pos["ticker"]
        pl_pct = pos["unrealized_pl_pct"]
        current_trail = pos.get("current_trail_pct")

        if pl_pct <= -hard_loss_cut:
            actions.append({
                "ticker": ticker, "action": "close", "current_trail_pct": current_trail,
                "reason": f"unrealized {pl_pct:.1%} <= hard loss cut -{hard_loss_cut:.0%}",
            })
            continue

        target_trail = trail2_pct if pl_pct >= trail2_trigger else (trail1_pct if pl_pct >= trail1_trigger else None)
        if target_trail is None:
            actions.append({
                "ticker": ticker, "action": "hold", "current_trail_pct": current_trail,
                "reason": f"unrealized {pl_pct:.1%}, no rule triggered",
            })
            continue

        ok, reason = validate_tighten_stop(target_trail, current_trail)
        if ok:
            actions.append({
                "ticker": ticker, "action": "tighten_stop", "new_trail_pct": target_trail,
                "current_trail_pct": current_trail,
                "reason": f"unrealized {pl_pct:.1%} crossed the tighten trigger",
            })
        else:
            actions.append({
                "ticker": ticker, "action": "hold", "current_trail_pct": current_trail,
                "reason": f"target tighten to {target_trail}% skipped: {reason}",
            })
    return actions


# ---------------------------------------------------------------------------
# Live-data helpers — untested here (no network in this environment); keep
# these thin so the untested surface area stays as small as possible.
# ---------------------------------------------------------------------------

def _build_clients(cfg: Config):
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.trading.client import TradingClient

    trading_client = TradingClient(cfg.alpaca_api_key, cfg.alpaca_secret_key, paper=not cfg.is_live)
    data_client = StockHistoricalDataClient(cfg.alpaca_api_key, cfg.alpaca_secret_key)
    return trading_client, data_client


def _fetch_daily_bars(data_client, symbol: str, lookback_days: int = 300) -> pd.DataFrame:
    from datetime import datetime, timedelta

    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    # `limit` alone, with no `start`, only returns the single latest bar —
    # Alpaca's historical bars endpoint needs an explicit date range to
    # actually page back through history. 1.6x + a 10-day buffer covers
    # lookback_days TRADING days worth of calendar days (weekends/holidays).
    start = datetime.now() - timedelta(days=int(lookback_days * 1.6) + 10)
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day, start=start, limit=lookback_days)
    bars = data_client.get_stock_bars(req).df
    if bars.empty:
        raise ValueError(f"no bar data returned for {symbol}")
    if isinstance(bars.index, pd.MultiIndex):
        bars = bars.xs(symbol, level=0)
    bars.index = pd.DatetimeIndex(bars.index).tz_localize(None)
    return bars[["open", "high", "low", "close", "volume"]].sort_index()


def _resolve_breadth(data_client, override: float | None) -> float | None:
    """
    An explicit --breadth always wins (lets a caller override with a real
    published statistic, or force None for testing). Otherwise, computes a
    real breadth read from BREADTH_PROXY_UNIVERSE — found in production
    that this was NEVER being supplied at all (regime.py's compute_breadth
    docstring has the full story), which silently capped regime confidence
    well below the 0.40 minimum for five straight sessions regardless of
    how strong the actual trend was. A failed fetch degrades to None (no
    breadth data) rather than crashing the whole command — breadth is an
    enhancement to regime confidence, not a hard dependency of it.
    """
    if override is not None:
        return override
    price_data: dict[str, pd.DataFrame] = {}
    for ticker in BREADTH_PROXY_UNIVERSE:
        try:
            price_data[ticker] = _fetch_daily_bars(data_client, ticker, lookback_days=60)
        except Exception:
            continue  # one bad ticker shouldn't sink the whole breadth read
    return compute_breadth(price_data)


def _latest_quote(data_client, symbol: str) -> dict:
    from alpaca.data.requests import StockLatestQuoteRequest

    req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
    quote = data_client.get_stock_latest_quote(req)[symbol]
    bid = float(quote.bid_price or 0)
    ask = float(quote.ask_price or 0)
    if bid <= 0 or ask <= 0:
        # A degraded/empty quote (e.g. an outage behind a 200, or a stale
        # response after-hours) must not silently become entry_price=0.0 /
        # a negative stop_price downstream in cmd_evaluate — found via a
        # live run where a bad quote (bid=ask=0) produced stop_price=-8.49
        # and only accidentally got caught by the liquidity gate rather
        # than being rejected at the source.
        raise ValueError(f"no usable quote for {symbol} (bid={bid}, ask={ask}) — market data may be degraded or stale")
    return {"bid_price": bid, "ask_price": ask}


def _enum_tail(value) -> str:
    """alpaca-py enums stringify as 'OrderSide.SELL' — this extracts 'sell'."""
    return str(value).lower().split(".")[-1]


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_regime(cfg: Config, args: argparse.Namespace) -> dict:
    _, data_client = _build_clients(cfg)
    spy_bars = _fetch_daily_bars(data_client, "SPY")
    spy_row = compute_features(spy_bars).iloc[-1]
    qqq_row = None
    if args.qqq:
        qqq_row = compute_features(_fetch_daily_bars(data_client, "QQQ")).iloc[-1]
    breadth = _resolve_breadth(data_client, args.breadth)
    result = classify_regime(spy_row, qqq_row, vix_level=args.vix, breadth_pct_above_50dma=breadth)
    return dataclasses.asdict(result)


def cmd_scan(cfg: Config, args: argparse.Namespace) -> dict:
    _, data_client = _build_clients(cfg)
    spy_bars = _fetch_daily_bars(data_client, "SPY")
    spy_row = compute_features(spy_bars).iloc[-1]
    breadth = _resolve_breadth(data_client, args.breadth)
    regime = classify_regime(spy_row, vix_level=args.vix, breadth_pct_above_50dma=breadth)

    regime_weights = cfg.get("strategy.regime_weights", {})
    sleeve_enabled = cfg.get("strategy.sleeves", {})

    candidates = []
    for ticker in args.tickers:
        try:
            bars = _fetch_daily_bars(data_client, ticker)
            row = compute_features(bars, benchmark_close=spy_bars["close"]).iloc[-1]
            ensemble = compute_ensemble(ticker, row, regime.state, regime_weights, sleeve_enabled)
            candidates.append({
                "ticker": ticker,
                "ensemble_score": ensemble.ensemble_score,
                "sleeve_scores": ensemble.sleeve_scores,
                "explanations": ensemble.sleeve_explanations,
                "close": float(bars["close"].iloc[-1]),
            })
        except Exception as e:  # a bad ticker shouldn't kill the whole scan
            candidates.append({"ticker": ticker, "error": str(e)})

    candidates.sort(key=lambda c: c.get("ensemble_score", float("-inf")), reverse=True)
    return {"regime": dataclasses.asdict(regime), "candidates": candidates}


def cmd_evaluate(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, data_client = _build_clients(cfg)
    spy_bars = _fetch_daily_bars(data_client, "SPY")
    spy_row = compute_features(spy_bars).iloc[-1]
    breadth = _resolve_breadth(data_client, args.breadth)
    regime = classify_regime(spy_row, vix_level=args.vix, breadth_pct_above_50dma=breadth)

    bars = _fetch_daily_bars(data_client, args.ticker)
    row = compute_features(bars, benchmark_close=spy_bars["close"]).iloc[-1]

    regime_weights = cfg.get("strategy.regime_weights", {})
    sleeve_enabled = cfg.get("strategy.sleeves", {})
    ensemble = compute_ensemble(args.ticker, row, regime.state, regime_weights, sleeve_enabled)
    technical = technical_score_from_ensemble(ensemble.ensemble_score)

    ml = predict_with_champion(row)

    quote = _latest_quote(data_client, args.ticker)
    spread_pct = (quote["ask_price"] - quote["bid_price"]) / quote["ask_price"] * 100 if quote["ask_price"] else 100.0
    max_spread_pct = cfg.effective_max_spread_pct
    liquidity_ok = quote["ask_price"] > 0 and quote["bid_price"] > 0 and spread_pct <= max_spread_pct

    entry_price = args.entry_price if args.entry_price is not None else quote["ask_price"]
    atr_raw = row.get("atr_14")
    atr = float(atr_raw) if atr_raw is not None and not pd.isna(atr_raw) else entry_price * 0.02
    stop_price = args.stop_price if args.stop_price is not None else round(entry_price - 1.5 * atr, 2)
    reward_risk_min = cfg.get("strategy.reward_risk_minimum", 2.0)
    target_price = args.target_price if args.target_price is not None else round(
        entry_price + reward_risk_min * (entry_price - stop_price), 2,
    )
    reward_risk_ratio = (target_price - entry_price) / (entry_price - stop_price) if entry_price != stop_price else 0.0

    setup_quality = SetupQuality(
        ticker=args.ticker,
        technical=technical,
        sector=args.sector_momentum_score,
        catalyst=100.0 if args.catalyst_verified else 0.0,
        liquidity=90.0 if liquidity_ok else 10.0,
        risk_quality=max(0.0, min(100.0, 100.0 - (atr / entry_price * 100 * 3))) if entry_price else 50.0,
        portfolio_fit=80.0 if args.portfolio_concentration_ok else 20.0,
        ml_probability=ml.get("ml_probability"),
    )

    candidate = Candidate(
        ticker=args.ticker,
        ensemble_score=ensemble.ensemble_score,
        ml_probability=ml.get("ml_probability"),
        regime_state=regime.state,
        regime_confidence=regime.confidence,
        setup_quality=setup_quality.overall_quality,
        sleeve_scores=ensemble.sleeve_scores,
        spread_pct=spread_pct,
        liquidity_ok=liquidity_ok,
        portfolio_concentration_ok=args.portfolio_concentration_ok,
        catalyst_verified=args.catalyst_verified,
        reward_risk_ratio=reward_risk_ratio,
        market_risk_off_gate_active=(regime.state == "RISK_OFF"),
        risk_off_exception_validated=args.risk_off_exception_validated,
    )
    no_trade_result = evaluate_no_trade(candidate, cfg)

    decision: dict[str, Any] = {
        "ticker": args.ticker,
        "regime": dataclasses.asdict(regime),
        "ensemble": dataclasses.asdict(ensemble),
        "setup_quality": dataclasses.asdict(setup_quality),
        "ml_probability": ml,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "reward_risk_ratio": round(reward_risk_ratio, 3),
        "spread_pct": round(spread_pct, 3),
        "max_spread_pct_applied": max_spread_pct,
        "spread_limit_is_paper_mode_override": not cfg.is_live,
        "no_trade": dataclasses.asdict(no_trade_result),
        "sizing": None,
    }

    if no_trade_result.decision != "PASS":
        return decision

    account = trading_client.get_account()
    equity, cash = float(account.equity), float(account.cash)

    setup_state = classify_setup_state(
        setup_quality=setup_quality.overall_quality,
        regime_state=regime.state,
        regime_confidence=regime.confidence,
        portfolio_concentration_ok=args.portfolio_concentration_ok,
        hard_gate_failed=False,   # already enforced by evaluate_no_trade above
    )
    quality_within_band = min(1.0, max(0.0, (setup_quality.overall_quality - 60) / 40))
    budget = risk_budget_pct(setup_state, quality_within_band=quality_within_band)
    sizing = size_position(
        equity=equity, risk_budget=budget, entry_price=entry_price, stop_price=stop_price,
        max_position_value=equity * cfg.get("portfolio.max_position_pct", 0.20),
        available_cash=cash, liquidity_limit_shares=1_000_000, portfolio_limit_shares=1_000_000,
    )
    decision["setup_state"] = setup_state
    decision["risk_budget_pct"] = round(budget, 5)
    decision["sizing"] = dataclasses.asdict(sizing)
    return decision


def cmd_execute(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, data_client = _build_clients(cfg)
    gate = ExecutionGate(cfg, trading_client=trading_client)

    quote = _latest_quote(data_client, args.ticker)
    asset = trading_client.get_asset(args.ticker)
    asset_class = asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class)
    asset_info = {"asset_class": asset_class, "tradable": bool(asset.tradable)}

    open_positions = [{"ticker": p.symbol} for p in trading_client.get_all_positions()]
    open_orders = [
        {"ticker": o.symbol, "side": _enum_tail(o.side), "status": _enum_tail(o.status)}
        for o in trading_client.get_orders()
    ]

    account = trading_client.get_account()
    cash = float(account.cash)

    order = OrderRequest(
        ticker=args.ticker, side="buy", shares=args.shares,
        stop_price=args.stop_price, reason=args.reason,
    )
    context = {
        "asset_info": asset_info,
        "quote": quote,
        "open_positions": open_positions,
        "trades_this_week": args.trades_this_week,
        "calculated_risk_dollars": abs(args.entry_price - args.stop_price) * args.shares,
        "approved_risk_dollars": args.approved_risk_dollars,
        "available_cash": cash,
        "estimated_cost": args.entry_price * args.shares,
        "open_orders": open_orders,
    }

    trailing_pct = args.trailing_stop_pct if args.trailing_stop_pct is not None else cfg.get(
        "stops.original_reference_trailing_stop_pct", 10,
    )
    result = gate.submit_entry_with_trailing_stop(order, context, trailing_stop_pct=trailing_pct)
    return dataclasses.asdict(result)


def cmd_close(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, _ = _build_clients(cfg)
    cancelled = []
    for o in trading_client.get_orders():
        if o.symbol == args.ticker:
            trading_client.cancel_order_by_id(o.id)
            cancelled.append(str(o.id))
    close_result = trading_client.close_position(args.ticker)
    return {
        "ticker": args.ticker,
        "reason": args.reason,
        "cancelled_orders": cancelled,
        "close_order_id": str(getattr(close_result, "id", close_result)),
    }


def cmd_tighten_stop(cfg: Config, args: argparse.Namespace) -> dict:
    ok, reason = validate_tighten_stop(args.trail_percent, args.current_trail_percent)
    if not ok:
        return {"error": f"refusing to tighten {args.ticker}: {reason}"}

    trading_client, _ = _build_clients(cfg)
    position = trading_client.get_open_position(args.ticker)
    qty = float(position.qty)

    cancelled = []
    for o in trading_client.get_orders():
        if o.symbol == args.ticker and _enum_tail(o.side) == "sell":
            trading_client.cancel_order_by_id(o.id)
            cancelled.append(str(o.id))

    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import TrailingStopOrderRequest

    req = TrailingStopOrderRequest(
        symbol=args.ticker, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.GTC,
        trail_percent=str(args.trail_percent),
    )
    result = trading_client.submit_order(req)
    return {
        "ticker": args.ticker, "cancelled_orders": cancelled,
        "new_stop_order_id": str(result.id), "trail_percent": args.trail_percent,
    }


def cmd_reconcile(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, _ = _build_clients(cfg)
    report = reconcile_positions(trading_client)
    return dataclasses.asdict(report)


def cmd_positions(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, _ = _build_clients(cfg)
    account = trading_client.get_account()
    positions_raw = trading_client.get_all_positions()
    orders_raw = trading_client.get_orders()

    stops_by_ticker: dict[str, list[dict]] = {}
    for o in orders_raw:
        if _enum_tail(o.side) != "sell":
            continue
        otype = _enum_tail(getattr(o, "order_type", getattr(o, "type", "")))
        if otype in ("trailing_stop", "stop", "stop_limit"):
            stops_by_ticker.setdefault(o.symbol, []).append({"order_id": str(o.id), "type": otype})

    positions, flags = [], []
    for p in positions_raw:
        ticker = p.symbol
        if ticker not in stops_by_ticker:
            flags.append(f"{ticker}: NO PROTECTIVE STOP ORDER FOUND")
        positions.append({
            "ticker": ticker,
            "shares": float(p.qty),
            "entry_price": float(p.avg_entry_price),
            "current_price": float(p.current_price),
            "unrealized_pl_pct": round(float(p.unrealized_plpc) * 100, 2),
            "unrealized_pl_dollars": float(p.unrealized_pl),
            "stops": stops_by_ticker.get(ticker, []),
        })

    return {
        "equity": float(account.equity),
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "daytrade_count": int(account.daytrade_count or 0),
        "positions": positions,
        "flags": flags,
    }


def cmd_stops_check(cfg: Config, args: argparse.Namespace) -> dict:
    trading_client, _ = _build_clients(cfg)
    positions_raw = trading_client.get_all_positions()
    orders_raw = trading_client.get_orders()

    trail_by_ticker: dict[str, float] = {}
    for o in orders_raw:
        if _enum_tail(o.side) == "sell" and _enum_tail(getattr(o, "order_type", "")) == "trailing_stop":
            trail_pct = getattr(o, "trail_percent", None)
            if trail_pct is not None:
                trail_by_ticker[o.symbol] = float(trail_pct)

    positions = [
        {
            "ticker": p.symbol,
            "unrealized_pl_pct": float(p.unrealized_plpc),
            "current_trail_pct": trail_by_ticker.get(p.symbol),
        }
        for p in positions_raw
    ]
    return {"actions": compute_stops_check_actions(positions, cfg)}


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quant_cli.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("regime", help="classify today's market regime")
    p.add_argument("--qqq", action="store_true")
    p.add_argument("--vix", type=float, default=None)
    p.add_argument("--breadth", type=float, default=None,
                    help="fraction 0-1 of universe above 50dma; auto-computed from a live proxy "
                         "universe if omitted (see quant/regime.py's BREADTH_PROXY_UNIVERSE) — "
                         "pass this only to override with a real published statistic")

    p = sub.add_parser("scan", help="ensemble-score candidate tickers")
    p.add_argument("tickers", nargs="+")
    p.add_argument("--vix", type=float, default=None)
    p.add_argument("--breadth", type=float, default=None)

    p = sub.add_parser("evaluate", help="full pipeline: score, NO-TRADE gate, and size a candidate")
    p.add_argument("ticker")
    p.add_argument("--entry-price", type=float, default=None, help="defaults to the live ask")
    p.add_argument("--stop-price", type=float, default=None, help="defaults to entry - 1.5x ATR(14)")
    p.add_argument("--target-price", type=float, default=None, help="defaults to entry + reward_risk_minimum x R")
    p.add_argument("--catalyst-verified", action="store_true")
    p.add_argument("--portfolio-concentration-ok", action="store_true")
    p.add_argument("--risk-off-exception-validated", action="store_true")
    p.add_argument("--sector-momentum-score", type=float, default=50.0, help="0-100, from research, default neutral")
    p.add_argument("--vix", type=float, default=None)
    p.add_argument("--breadth", type=float, default=None)

    p = sub.add_parser("execute", help="place a market buy + trailing stop (REAL ORDER)")
    p.add_argument("ticker")
    p.add_argument("--shares", type=int, required=True)
    p.add_argument("--entry-price", type=float, required=True)
    p.add_argument("--stop-price", type=float, required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--trades-this-week", type=int, required=True, help="count from this week's memory/TRADE-LOG.md entries")
    p.add_argument("--approved-risk-dollars", type=float, required=True, help="from the prior `evaluate` call's sizing.risk_dollars")
    p.add_argument("--trailing-stop-pct", type=float, default=None, help="defaults to stops.original_reference_trailing_stop_pct")

    p = sub.add_parser("close", help="market-sell an entire position and cancel its orders (REAL ORDER)")
    p.add_argument("ticker")
    p.add_argument("--reason", required=True)

    p = sub.add_parser("tighten-stop", help="cancel + replace a position's trailing stop (REAL ORDER)")
    p.add_argument("ticker")
    p.add_argument("--trail-percent", type=float, required=True)
    p.add_argument("--current-trail-percent", type=float, default=None, help="omit if unknown; the 3% guardrail still applies")

    sub.add_parser("reconcile", help="live-vs-local drift check; appends to memory/RISK-LOG.md")
    sub.add_parser("positions", help="read-only positions + unrealized P&L + stop presence")
    sub.add_parser("stops-check", help="propose close/tighten/hold actions per open position")

    return parser


COMMANDS = {
    "regime": cmd_regime,
    "scan": cmd_scan,
    "evaluate": cmd_evaluate,
    "execute": cmd_execute,
    "close": cmd_close,
    "tighten-stop": cmd_tighten_stop,
    "reconcile": cmd_reconcile,
    "positions": cmd_positions,
    "stops-check": cmd_stops_check,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = load_config()
    except Exception as e:
        return print_result({"error": f"config load failed: {e}"}, error=True)

    handler = COMMANDS[args.command]
    try:
        result = handler(cfg, args)
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        return print_result({"error": f"{type(e).__name__}: {e}"}, error=True)

    return print_result(result, error=bool(result.get("error")))


if __name__ == "__main__":
    sys.exit(main())
