from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import quant.reconciliation as recon_mod
from quant.reconciliation import reconcile


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(recon_mod, "POSITIONS_FILE", tmp_path / "positions.json")
    monkeypatch.setattr(recon_mod, "ORDERS_FILE", tmp_path / "orders.json")
    monkeypatch.setattr(recon_mod, "RECON_LOG", tmp_path / "RISK-LOG.md")
    return tmp_path


def _write_local(path, positions=None, orders=None):
    if positions is not None:
        (path / "positions.json").write_text(json.dumps(positions), encoding="utf-8")
    if orders is not None:
        (path / "orders.json").write_text(json.dumps(orders), encoding="utf-8")


def _fake_client(live_positions=None, live_orders=None):
    positions = [SimpleNamespace(symbol=p["ticker"], qty=p["shares"], market_value=p["market_value"]) for p in (live_positions or [])]
    orders = [SimpleNamespace(id=o["order_id"], client_order_id=o["client_order_id"], symbol=o["ticker"], side=o["side"], status=o["status"]) for o in (live_orders or [])]
    return SimpleNamespace(get_all_positions=lambda: positions, get_orders=lambda: orders)


def test_reconcile_dry_run_when_no_client_given(isolated_state):
    report = reconcile(trading_client=None)
    assert report.ok is True
    assert any("dry-run" in d for d in report.drift_found)
    assert not (isolated_state / "RISK-LOG.md").exists()


def test_reconcile_no_drift_when_local_matches_live(isolated_state):
    _write_local(isolated_state, positions=[{"ticker": "XYZ", "shares": 10, "market_value": 500}])
    client = _fake_client(live_positions=[{"ticker": "XYZ", "shares": 10, "market_value": 500}])
    report = reconcile(client)
    assert report.ok is True
    assert report.drift_found == []


def test_reconcile_flags_extra_live_position():
    client = _fake_client(live_positions=[{"ticker": "NEW", "shares": 5, "market_value": 250}])
    report = reconcile(client)
    assert report.ok is False
    assert any("NEW" in d and "not tracked locally" in d for d in report.drift_found)


def test_reconcile_flags_stale_local_position(isolated_state):
    _write_local(isolated_state, positions=[{"ticker": "GONE", "shares": 5, "market_value": 250}])
    client = _fake_client(live_positions=[])
    report = reconcile(client)
    assert report.ok is False
    assert any("GONE" in d and "stale" in d for d in report.drift_found)


def test_reconcile_flags_share_count_mismatch(isolated_state):
    _write_local(isolated_state, positions=[{"ticker": "XYZ", "shares": 10, "market_value": 500}])
    client = _fake_client(live_positions=[{"ticker": "XYZ", "shares": 7, "market_value": 350}])
    report = reconcile(client)
    assert report.ok is False
    assert any("share count mismatch" in d for d in report.drift_found)


def test_reconcile_flags_local_order_open_but_not_live(isolated_state):
    _write_local(isolated_state, orders=[{"client_order_id": "abc-123", "ticker": "XYZ", "status": "new"}])
    client = _fake_client()
    report = reconcile(client)
    assert report.ok is False
    assert any("abc-123" in d for d in report.drift_found)


def test_reconcile_overwrites_local_positions_with_live_state(isolated_state):
    _write_local(isolated_state, positions=[{"ticker": "STALE", "shares": 1, "market_value": 1}])
    client = _fake_client(live_positions=[{"ticker": "XYZ", "shares": 10, "market_value": 500}])
    reconcile(client)
    saved = json.loads((isolated_state / "positions.json").read_text())
    assert len(saved) == 1
    assert saved[0]["ticker"] == "XYZ"


def test_reconcile_appends_to_recon_log(isolated_state):
    reconcile(_fake_client(live_positions=[{"ticker": "XYZ", "shares": 1, "market_value": 10}]))
    log_text = (isolated_state / "RISK-LOG.md").read_text(encoding="utf-8")
    assert "Reconciliation" in log_text
    assert "XYZ" in log_text
