"""
Execution & Order Safety (PDF section 10).

This is the ONE place allowed to talk to the broker for order placement.
Claude/the LLM layer may decide a candidate is eligible; it must never
construct or send an order directly — it calls into this module, which runs
every gate below and hard-rejects anything that fails, before touching
Alpaca. Every gate failure is a reason string, logged to
memory/RISK-LOG.md / memory/TRADE-LOG.md by the calling routine.

Uses the alpaca-py TradingClient/StockHistoricalDataClient directly (the
PDF's "use Alpaca wrappers rather than direct API calls" — this class *is*
that wrapper; nothing else in the codebase should import alpaca-py).
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quant.config import Config, ROOT


def enum_tail(value: Any) -> str:
    """alpaca-py enums stringify as 'OrderStatus.FILLED', 'OrderSide.SELL'
    etc. — this extracts the lowercase tail ('filled', 'sell'). Public (no
    leading underscore) because both this module's own fill-status checks
    and scripts/quant_cli.py's order-filtering need the exact same
    extraction; a second inline copy of `str(x).lower().split(".")[-1]` is
    how a real bug shipped (see _poll_for_fill's docstring, 2026-08-24)."""
    return str(value).lower().split(".")[-1]

STATE_DIR = ROOT / "state"
ORDERS_FILE = STATE_DIR / "orders.json"
POSITIONS_FILE = STATE_DIR / "positions.json"


@dataclass
class OrderRequest:
    ticker: str
    side: str            # "buy" | "sell"
    shares: int
    order_type: str = "limit"
    limit_price: float | None = None
    stop_price: float | None = None       # protective stop, submitted as a bracket/OCO leg
    take_profit_price: float | None = None
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reason: str = ""      # points back at the logged decision (setup quality, ensemble score, etc.)


@dataclass
class GateResult:
    passed: bool
    gate: str
    detail: str = ""


@dataclass
class ExecutionResult:
    accepted: bool
    gates: list[GateResult]
    order_id: str | None = None
    status: str | None = None
    rejection_reason: str | None = None


@dataclass
class EntryWithStopResult:
    """Return type for submit_entry_with_trailing_stop — distinct from
    ExecutionResult because a new entry is two orders (buy + protective
    stop), not one, and the stop leg has its own fallback ladder that needs
    to be visible to the caller, not collapsed into a single status."""
    accepted: bool
    gates: list[GateResult]
    rejection_reason: str | None = None
    buy_order_id: str | None = None
    buy_status: str | None = None
    filled_qty: float = 0.0
    fill_price: float = 0.0
    stop_status: str | None = None    # "trailing" | "fixed" | "queue_for_tomorrow" | "simulated" | "buy_not_filled_yet"
    stop_order_id: str | None = None
    reason: str | None = None


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class ExecutionGate:
    """Runs the deterministic gate chain from PDF section 10. Each `check_*`
    method returns a GateResult; run_gates() short-circuits on the first
    hard failure so the rejection reason is unambiguous."""

    def __init__(self, cfg: Config, trading_client=None):
        self.cfg = cfg
        # trading_client is an alpaca.trading.client.TradingClient, injected so
        # this module stays unit-testable without hitting the network.
        self.client = trading_client

    def check_symbol(self, order: OrderRequest, asset_info: dict) -> GateResult:
        ok = asset_info.get("asset_class") == "us_equity" and asset_info.get("tradable", False)
        return GateResult(ok, "symbol_validation", str(asset_info))

    def check_quote_quality(self, order: OrderRequest, quote: dict) -> GateResult:
        bid, ask = quote.get("bid_price", 0), quote.get("ask_price", 0)
        if bid <= 0 or ask <= 0:
            return GateResult(False, "quote_quality", "stale/zero quote")
        spread_pct = (ask - bid) / ask * 100
        max_spread = self.cfg.effective_max_spread_pct
        if spread_pct > max_spread:
            return GateResult(False, "quote_quality", f"spread {spread_pct:.2f}% > {max_spread}%")
        return GateResult(True, "quote_quality", f"spread {spread_pct:.2f}%")

    def check_position_limit(self, order: OrderRequest, open_positions: list[dict]) -> GateResult:
        max_positions = self.cfg.get("portfolio.max_positions", 6)
        tickers = {p["ticker"] for p in open_positions}
        if order.ticker not in tickers and len(tickers) >= max_positions:
            return GateResult(False, "position_limit", f"already at max_positions={max_positions}")
        return GateResult(True, "position_limit")

    def check_weekly_trade_limit(self, order: OrderRequest, trades_this_week: int) -> GateResult:
        cap = self.cfg.get("portfolio.max_new_trades_per_week", 3)
        if order.side == "buy" and trades_this_week >= cap:
            return GateResult(False, "weekly_trade_limit", f"{trades_this_week} >= cap {cap}")
        return GateResult(True, "weekly_trade_limit")

    def check_risk_budget(self, order: OrderRequest, calculated_risk_dollars: float, approved_risk_dollars: float) -> GateResult:
        if calculated_risk_dollars > approved_risk_dollars + 1e-6:
            return GateResult(
                False, "risk_budget",
                f"order risk ${calculated_risk_dollars:.2f} exceeds approved ${approved_risk_dollars:.2f}",
            )
        return GateResult(True, "risk_budget")

    def check_buying_power(self, order: OrderRequest, available_cash: float, estimated_cost: float) -> GateResult:
        if estimated_cost > available_cash:
            return GateResult(False, "cash_buying_power", f"cost ${estimated_cost:.2f} > cash ${available_cash:.2f}")
        return GateResult(True, "cash_buying_power")

    def check_open_order_conflict(self, order: OrderRequest, open_orders: list[dict]) -> GateResult:
        for o in open_orders:
            if o.get("ticker") == order.ticker and o.get("side") == order.side and o.get("status") in ("open", "new", "accepted"):
                return GateResult(False, "open_order_conflict", f"existing {o.get('side')} order on {order.ticker}")
        return GateResult(True, "open_order_conflict")

    def check_stop_protection(self, order: OrderRequest) -> GateResult:
        if order.side == "buy" and (order.stop_price is None or order.stop_price <= 0):
            return GateResult(False, "stop_protection", "buy order missing a protective stop")
        return GateResult(True, "stop_protection")

    def run_gates(self, order: OrderRequest, context: dict[str, Any]) -> list[GateResult]:
        """`context` carries everything the gates need: asset_info, quote,
        open_positions, trades_this_week, calculated_risk_dollars,
        approved_risk_dollars, available_cash, estimated_cost, open_orders."""
        checks = [
            self.check_symbol(order, context["asset_info"]),
            self.check_quote_quality(order, context["quote"]),
            self.check_position_limit(order, context["open_positions"]),
            self.check_weekly_trade_limit(order, context["trades_this_week"]),
            self.check_risk_budget(order, context["calculated_risk_dollars"], context["approved_risk_dollars"]),
            self.check_buying_power(order, context["available_cash"], context["estimated_cost"]),
            self.check_open_order_conflict(order, context["open_orders"]),
            self.check_stop_protection(order),
        ]
        return checks

    def submit(self, order: OrderRequest, context: dict[str, Any]) -> ExecutionResult:
        gates = self.run_gates(order, context)
        failed = [g for g in gates if not g.passed]
        if failed:
            reason = "; ".join(f"{g.gate}: {g.detail}" for g in failed)
            self._persist_order(order, status="rejected", reason=reason)
            return ExecutionResult(accepted=False, gates=gates, rejection_reason=reason)

        if self.client is None:
            # dry-run / backtest mode — no live client wired up
            self._persist_order(order, status="simulated")
            return ExecutionResult(accepted=True, gates=gates, order_id=order.client_order_id, status="simulated")

        # Live/paper submission via alpaca-py. Bracket order: entry + stop-loss (+ optional take-profit).
        from alpaca.trading.requests import LimitOrderRequest, StopLossRequest, TakeProfitRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass

        side = OrderSide.BUY if order.side == "buy" else OrderSide.SELL
        req = LimitOrderRequest(
            symbol=order.ticker,
            qty=order.shares,
            side=side,
            time_in_force=TimeInForce.DAY,
            limit_price=order.limit_price,
            order_class=OrderClass.BRACKET if order.stop_price else OrderClass.SIMPLE,
            stop_loss=StopLossRequest(stop_price=order.stop_price) if order.stop_price else None,
            take_profit=TakeProfitRequest(limit_price=order.take_profit_price) if order.take_profit_price else None,
            client_order_id=order.client_order_id,
        )
        result = self.client.submit_order(req)
        self._persist_order(order, status=enum_tail(result.status), order_id=str(result.id))
        return ExecutionResult(accepted=True, gates=gates, order_id=str(result.id), status=enum_tail(result.status))

    def submit_entry_with_trailing_stop(
        self,
        order: OrderRequest,
        context: dict[str, Any],
        trailing_stop_pct: float,
        fill_poll_attempts: int = 10,
        fill_poll_interval_s: float = 1.0,
    ) -> EntryWithStopResult:
        """
        The live counterpart to submit() for NEW positions specifically.
        The strategy's hard rule is a REAL trailing stop GTC order on every
        position (config/strategy.yaml's stops.* — tightened later to 7%/5%
        as a position gains, which only makes sense against a trailing
        stop, not a fixed one) — so this deliberately does NOT reuse
        submit()'s single bracket-order path. It is the two-step flow
        documented in CLAUDE.md and memory/TRADING-STRATEGY.md, with the
        original guide's PDT fallback ladder:

          1. market buy (day TIF), poll for fill
          2. trailing_stop GTC sell for the filled quantity
             -> on rejection (commonly a same-day-buy PDT restriction),
                fall back to a FIXED stop GTC sell at the same initial %
                distance below the actual fill price
             -> if that also fails, report stop_status="queue_for_tomorrow"
                rather than silently leaving a naked, unprotected position

        order.stop_price is ignored here — a trailing stop has no fixed
        price yet — pass trailing_stop_pct instead. The gate chain still
        runs first and still hard-rejects exactly as submit() does; this
        method adds no new way to bypass a failed gate.
        """
        gates = self.run_gates(order, context)
        failed = [g for g in gates if not g.passed]
        if failed:
            reason = "; ".join(f"{g.gate}: {g.detail}" for g in failed)
            self._persist_order(order, status="rejected", reason=reason)
            return EntryWithStopResult(accepted=False, gates=gates, rejection_reason=reason)

        if self.client is None:
            # dry-run / backtest mode — no live client wired up
            self._persist_order(order, status="simulated")
            return EntryWithStopResult(
                accepted=True, gates=gates, buy_order_id=order.client_order_id,
                buy_status="simulated", stop_status="simulated",
            )

        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        buy_req = MarketOrderRequest(
            symbol=order.ticker, qty=order.shares, side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY, client_order_id=order.client_order_id,
        )
        buy_result = self.client.submit_order(buy_req)
        buy_order_id = str(buy_result.id)
        self._persist_order(order, status=enum_tail(buy_result.status), order_id=buy_order_id)

        filled_qty, fill_price, buy_status = self._poll_for_fill(
            buy_order_id, fill_poll_attempts, fill_poll_interval_s,
        )
        if filled_qty <= 0:
            return EntryWithStopResult(
                accepted=True, gates=gates, buy_order_id=buy_order_id, buy_status=buy_status,
                stop_status="buy_not_filled_yet",
                reason="buy order not filled within the poll window — reconcile next run before placing a stop",
            )

        stop_status, stop_order_id, stop_detail = self._place_protective_stop(
            order.ticker, filled_qty, fill_price, trailing_stop_pct,
        )

        return EntryWithStopResult(
            accepted=True, gates=gates, buy_order_id=buy_order_id, buy_status=buy_status,
            filled_qty=filled_qty, fill_price=fill_price,
            stop_status=stop_status, stop_order_id=stop_order_id, reason=stop_detail,
        )

    def _poll_for_fill(self, order_id: str, attempts: int, interval_s: float) -> tuple[float, float, str]:
        """
        BUG (found 2026-08-24, real live order): this used to compare
        str(o.status) directly against "filled"/"partially_filled"/etc.
        alpaca-py's status is an enum that stringifies as "OrderStatus.FILLED",
        not "filled" — the comparison never matched, so this ALWAYS fell
        through to "not filled yet" and skipped placing the protective stop,
        even on an order that filled instantly. A real BAC buy filled
        (confirmed via the broker directly: filled_qty="169",
        filled_avg_price="62.3") while this method still reported
        filled_qty=0.0 and left the position with no stop until a human
        caught it manually. Now uses enum_tail() to extract the real value,
        the same fix already applied to every enum comparison in
        scripts/quant_cli.py.
        """
        status = "unknown"
        for _ in range(attempts):
            o = self.client.get_order_by_id(order_id)
            status = enum_tail(o.status)
            if status in ("filled", "partially_filled"):
                return float(o.filled_qty or 0), float(o.filled_avg_price or 0), status
            if status in ("canceled", "rejected", "expired"):
                return 0.0, 0.0, status
            time.sleep(interval_s)
        return 0.0, 0.0, status

    def _place_protective_stop(
        self, ticker: str, qty: float, fill_price: float, trailing_stop_pct: float,
    ) -> tuple[str, str | None, str]:
        from alpaca.trading.requests import StopOrderRequest, TrailingStopOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce

        try:
            req = TrailingStopOrderRequest(
                symbol=ticker, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.GTC,
                trail_percent=str(trailing_stop_pct),
            )
            result = self.client.submit_order(req)
            return "trailing", str(result.id), f"{trailing_stop_pct}% trailing stop placed"
        except Exception as trailing_error:
            fixed_stop_price = round(fill_price * (1 - trailing_stop_pct / 100), 2)
            try:
                req = StopOrderRequest(
                    symbol=ticker, qty=qty, side=OrderSide.SELL, time_in_force=TimeInForce.GTC,
                    stop_price=fixed_stop_price,
                )
                result = self.client.submit_order(req)
                return "fixed", str(result.id), (
                    f"trailing stop rejected ({trailing_error}); fell back to fixed stop at ${fixed_stop_price}"
                )
            except Exception as fixed_error:
                return "queue_for_tomorrow", None, (
                    f"trailing stop rejected ({trailing_error}); fixed stop also rejected ({fixed_error}) — "
                    "queue for tomorrow morning, log in TRADE-LOG.md"
                )

    @staticmethod
    def _persist_order(order: OrderRequest, status: str, order_id: str | None = None, reason: str | None = None) -> None:
        orders = _load_json(ORDERS_FILE, [])
        orders.append({
            "client_order_id": order.client_order_id,
            "order_id": order_id,
            "ticker": order.ticker,
            "side": order.side,
            "shares": order.shares,
            "status": status,
            "reason": reason or order.reason,
            "ts": time.time(),
        })
        _save_json(ORDERS_FILE, orders)
