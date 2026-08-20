"""
Failure Recovery / Reconciliation (PDF section 10).

Every routine that can touch orders MUST call reconcile() first, before any
new trade is considered. This closes the gap where a run dies after an
order was sent but before local state was updated — the next run trusts
Alpaca's live state over its own local cache, logs any drift, and only then
proceeds.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from quant.config import ROOT

STATE_DIR = ROOT / "state"
POSITIONS_FILE = STATE_DIR / "positions.json"
ORDERS_FILE = STATE_DIR / "orders.json"
RECON_LOG = ROOT / "memory" / "RISK-LOG.md"


@dataclass
class ReconciliationReport:
    ok: bool
    drift_found: list[str] = field(default_factory=list)
    live_positions: list[dict] = field(default_factory=list)
    live_open_orders: list[dict] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def reconcile(trading_client) -> ReconciliationReport:
    """
    trading_client: alpaca.trading.client.TradingClient, or None to run in a
    local-only dry mode (used by tests / backtest harness — always drift-free).
    """
    local_positions = {p["ticker"]: p for p in _load_json(POSITIONS_FILE, [])}
    local_orders = {o["client_order_id"]: o for o in _load_json(ORDERS_FILE, [])}

    if trading_client is None:
        return ReconciliationReport(ok=True, drift_found=["dry-run: no broker client, skipped live check"])

    live_positions_raw = trading_client.get_all_positions()
    live_positions = [
        {"ticker": p.symbol, "shares": float(p.qty), "market_value": float(p.market_value)}
        for p in live_positions_raw
    ]
    live_orders_raw = trading_client.get_orders()
    live_open_orders = [
        {"order_id": str(o.id), "client_order_id": o.client_order_id, "ticker": o.symbol,
         "side": str(o.side), "status": str(o.status)}
        for o in live_orders_raw
    ]

    drift: list[str] = []
    live_tickers = {p["ticker"] for p in live_positions}
    local_tickers = set(local_positions)

    for extra in live_tickers - local_tickers:
        drift.append(f"live position {extra} not tracked locally — adopting live state")
    for missing in local_tickers - live_tickers:
        drift.append(f"local position {missing} not found live — local record is stale, removing")

    for t in live_tickers & local_tickers:
        if abs(local_positions[t]["shares"] - next(p["shares"] for p in live_positions if p["ticker"] == t)) > 1e-6:
            drift.append(f"share count mismatch on {t}: local={local_positions[t]['shares']} live differs")

    live_client_ids = {o["client_order_id"] for o in live_open_orders if o["client_order_id"]}
    for oid, order in local_orders.items():
        if order.get("status") in ("new", "accepted", "pending_new") and oid not in live_client_ids:
            drift.append(f"local order {oid} ({order['ticker']}) marked open locally but not open live")

    # Live state wins. Overwrite local cache.
    _save_json(POSITIONS_FILE, live_positions)

    report = ReconciliationReport(
        ok=len(drift) == 0,
        drift_found=drift,
        live_positions=live_positions,
        live_open_orders=live_open_orders,
    )
    _append_recon_log(report)
    return report


def _append_recon_log(report: ReconciliationReport) -> None:
    RECON_LOG.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"\n### Reconciliation — {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}"]
    if report.drift_found:
        lines.append("Drift found:")
        lines.extend(f"- {d}" for d in report.drift_found)
    else:
        lines.append("No drift — local state matched broker.")
    with open(RECON_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
