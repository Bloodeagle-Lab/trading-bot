from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import quant.execution as execution_mod
from quant.execution import ExecutionGate, OrderRequest
from tests.conftest import make_config


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """Every test in this file gets its own state/ dir so nothing touches
    the real repo's state/orders.json."""
    monkeypatch.setattr(execution_mod, "STATE_DIR", tmp_path)
    monkeypatch.setattr(execution_mod, "ORDERS_FILE", tmp_path / "orders.json")
    monkeypatch.setattr(execution_mod, "POSITIONS_FILE", tmp_path / "positions.json")
    return tmp_path


def _gate() -> ExecutionGate:
    return ExecutionGate(make_config())


def _buy_order(**overrides) -> OrderRequest:
    base = dict(ticker="XYZ", side="buy", shares=10, stop_price=45.0)
    base.update(overrides)
    return OrderRequest(**base)


def test_check_symbol_rejects_non_equity():
    result = _gate().check_symbol(_buy_order(), {"asset_class": "option", "tradable": True})
    assert result.passed is False


def test_check_symbol_accepts_tradable_equity():
    result = _gate().check_symbol(_buy_order(), {"asset_class": "us_equity", "tradable": True})
    assert result.passed is True


def test_check_quote_quality_rejects_zero_quote():
    result = _gate().check_quote_quality(_buy_order(), {"bid_price": 0, "ask_price": 0})
    assert result.passed is False


def test_check_quote_quality_rejects_wide_spread():
    result = _gate().check_quote_quality(_buy_order(), {"bid_price": 49.0, "ask_price": 51.0})  # ~4% spread
    assert result.passed is False


def test_check_quote_quality_accepts_tight_spread():
    result = _gate().check_quote_quality(_buy_order(), {"bid_price": 49.95, "ask_price": 50.00})
    assert result.passed is True


def test_check_position_limit_rejects_when_full():
    positions = [{"ticker": f"T{i}"} for i in range(6)]
    result = _gate().check_position_limit(_buy_order(ticker="NEW"), positions)
    assert result.passed is False


def test_check_position_limit_allows_adding_to_existing_position():
    positions = [{"ticker": f"T{i}"} for i in range(6)]
    result = _gate().check_position_limit(_buy_order(ticker="T0"), positions)
    assert result.passed is True


def test_check_weekly_trade_limit_rejects_buy_at_cap():
    result = _gate().check_weekly_trade_limit(_buy_order(), trades_this_week=3)
    assert result.passed is False


def test_check_weekly_trade_limit_ignores_sells():
    result = _gate().check_weekly_trade_limit(_buy_order(side="sell"), trades_this_week=99)
    assert result.passed is True


def test_check_risk_budget_rejects_when_exceeded():
    result = _gate().check_risk_budget(_buy_order(), calculated_risk_dollars=600.0, approved_risk_dollars=500.0)
    assert result.passed is False


def test_check_buying_power_rejects_insufficient_cash():
    result = _gate().check_buying_power(_buy_order(), available_cash=100.0, estimated_cost=500.0)
    assert result.passed is False


def test_check_open_order_conflict_rejects_duplicate():
    open_orders = [{"ticker": "XYZ", "side": "buy", "status": "open"}]
    result = _gate().check_open_order_conflict(_buy_order(), open_orders)
    assert result.passed is False


def test_check_stop_protection_rejects_buy_without_stop():
    result = _gate().check_stop_protection(_buy_order(stop_price=None))
    assert result.passed is False


def test_check_stop_protection_accepts_buy_with_stop():
    result = _gate().check_stop_protection(_buy_order(stop_price=45.0))
    assert result.passed is True


def _full_context(**overrides):
    ctx = dict(
        asset_info={"asset_class": "us_equity", "tradable": True},
        quote={"bid_price": 49.9, "ask_price": 50.0},
        open_positions=[],
        trades_this_week=0,
        calculated_risk_dollars=200.0,
        approved_risk_dollars=500.0,
        available_cash=100_000.0,
        estimated_cost=500.0,
        open_orders=[],
    )
    ctx.update(overrides)
    return ctx


def test_submit_accepted_in_dry_run_mode_and_persists_order():
    gate = _gate()
    order = _buy_order()
    result = gate.submit(order, _full_context())
    assert result.accepted is True
    assert result.status == "simulated"
    assert all(g.passed for g in result.gates)

    persisted = json.loads(execution_mod.ORDERS_FILE.read_text())
    assert len(persisted) == 1
    assert persisted[0]["status"] == "simulated"
    assert persisted[0]["ticker"] == "XYZ"


def test_submit_rejected_when_a_gate_fails_and_persists_rejection():
    gate = _gate()
    order = _buy_order(stop_price=None)  # fails check_stop_protection
    result = gate.submit(order, _full_context())
    assert result.accepted is False
    assert result.rejection_reason is not None
    assert "stop_protection" in result.rejection_reason

    persisted = json.loads(execution_mod.ORDERS_FILE.read_text())
    assert persisted[0]["status"] == "rejected"


class _FakeBrokerClient:
    """Stands in for alpaca.trading.client.TradingClient. submit_order()
    branches on the real alpaca-py request class it receives so tests
    exercise the actual request objects submit_entry_with_trailing_stop
    constructs, not a re-implementation of them."""

    def __init__(self, fill_after=1, fill_qty=10.0, fill_price=50.0,
                 trailing_stop_raises=False, fixed_stop_raises=False):
        self.fill_after = fill_after
        self.fill_qty = fill_qty
        self.fill_price = fill_price
        self.trailing_stop_raises = trailing_stop_raises
        self.fixed_stop_raises = fixed_stop_raises
        self.poll_count = 0
        self.submitted = []

    def submit_order(self, req):
        self.submitted.append(req)
        cls_name = type(req).__name__
        if cls_name == "MarketOrderRequest":
            return SimpleNamespace(id="buy-1", status="new")
        if cls_name == "TrailingStopOrderRequest":
            if self.trailing_stop_raises:
                raise RuntimeError("trailing stop rejected (simulated PDT restriction)")
            return SimpleNamespace(id="stop-trailing-1", status="accepted")
        if cls_name == "StopOrderRequest":
            if self.fixed_stop_raises:
                raise RuntimeError("fixed stop rejected too (simulated)")
            return SimpleNamespace(id="stop-fixed-1", status="accepted")
        raise AssertionError(f"unexpected order type submitted: {cls_name}")

    def get_order_by_id(self, order_id):
        self.poll_count += 1
        if self.poll_count >= self.fill_after:
            return SimpleNamespace(id=order_id, status="filled", filled_qty=self.fill_qty, filled_avg_price=self.fill_price)
        return SimpleNamespace(id=order_id, status="new", filled_qty=0, filled_avg_price=None)


def test_submit_entry_with_trailing_stop_rejects_on_failed_gate():
    gate = ExecutionGate(make_config(), trading_client=_FakeBrokerClient())
    order = _buy_order(stop_price=None)  # fails check_stop_protection
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10)
    assert result.accepted is False
    assert "stop_protection" in result.rejection_reason


def test_submit_entry_with_trailing_stop_dry_run_when_no_client():
    gate = ExecutionGate(make_config())  # no trading_client -> dry run
    order = _buy_order()
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10)
    assert result.accepted is True
    assert result.buy_status == "simulated"
    assert result.stop_status == "simulated"


def test_submit_entry_with_trailing_stop_happy_path_places_trailing_stop():
    client = _FakeBrokerClient(fill_after=1, fill_qty=10.0, fill_price=50.0)
    gate = ExecutionGate(make_config(), trading_client=client)
    order = _buy_order(shares=10)
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10, fill_poll_interval_s=0)

    assert result.accepted is True
    assert result.buy_order_id == "buy-1"
    assert result.filled_qty == 10.0
    assert result.fill_price == 50.0
    assert result.stop_status == "trailing"
    assert result.stop_order_id == "stop-trailing-1"


def test_submit_entry_with_trailing_stop_falls_back_to_fixed_stop_on_pdt_rejection():
    client = _FakeBrokerClient(fill_after=1, fill_qty=10.0, fill_price=50.0, trailing_stop_raises=True)
    gate = ExecutionGate(make_config(), trading_client=client)
    order = _buy_order(shares=10)
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10, fill_poll_interval_s=0)

    assert result.stop_status == "fixed"
    assert result.stop_order_id == "stop-fixed-1"
    assert "fell back to fixed stop" in result.reason


def test_submit_entry_with_trailing_stop_queues_for_tomorrow_when_both_stops_fail():
    client = _FakeBrokerClient(fill_after=1, trailing_stop_raises=True, fixed_stop_raises=True)
    gate = ExecutionGate(make_config(), trading_client=client)
    order = _buy_order(shares=10)
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10, fill_poll_interval_s=0)

    assert result.stop_status == "queue_for_tomorrow"
    assert result.stop_order_id is None
    assert "queue for tomorrow" in result.reason


def test_submit_entry_with_trailing_stop_reports_unfilled_buy_without_placing_a_stop():
    client = _FakeBrokerClient(fill_after=999)  # never fills within the poll window
    gate = ExecutionGate(make_config(), trading_client=client)
    order = _buy_order(shares=10)
    result = gate.submit_entry_with_trailing_stop(order, _full_context(), trailing_stop_pct=10,
                                                    fill_poll_attempts=2, fill_poll_interval_s=0)

    assert result.accepted is True
    assert result.stop_status == "buy_not_filled_yet"
    assert result.stop_order_id is None
    # no stop-order request should ever have been submitted for an unfilled buy
    assert all(type(r).__name__ != "TrailingStopOrderRequest" for r in client.submitted)
    assert all(type(r).__name__ != "StopOrderRequest" for r in client.submitted)


def test_run_gates_short_circuit_still_returns_all_checks():
    gate = _gate()
    order = _buy_order(stop_price=None)
    gates = gate.run_gates(order, _full_context())
    # run_gates itself does NOT short-circuit (submit() does the reasoning);
    # every check should still have run so the audit trail is complete.
    assert len(gates) == 8
    names = {g.gate for g in gates}
    assert "stop_protection" in names
