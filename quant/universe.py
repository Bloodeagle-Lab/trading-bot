"""
Universe selection (PDF section 19 / Phase 1).

Filters the tradable US-equity universe down to names worth scoring:
minimum average dollar volume, no halts, no abnormal spreads. Live universe
building queries Alpaca directly; backtests should instead build a
point-in-time, survivorship-aware universe from stored historical data
(current index membership as of each date, not today's membership applied
retroactively) — that plumbing lives in research/backtest.py since it needs
a historical membership dataset the live path doesn't.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant.config import Config


@dataclass
class UniverseFilterStats:
    total_assets: int
    after_tradable: int
    after_dollar_volume: int
    after_spread: int
    final: list[str]


def build_live_universe(trading_client, data_client, cfg: Config) -> UniverseFilterStats:
    """
    trading_client: alpaca.trading.client.TradingClient
    data_client: alpaca.data.historical.StockHistoricalDataClient
    """
    from alpaca.trading.requests import GetAssetsRequest
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    assets = trading_client.get_all_assets(
        GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE)
    )
    total = len(assets)

    tradable = [a for a in assets if a.tradable and not getattr(a, "shortable", True) is None]
    if cfg.get("universe.exclude_halted", True):
        tradable = [a for a in tradable if getattr(a, "status", "active") == "active"]
    after_tradable = len(tradable)

    symbols = [a.symbol for a in tradable]
    min_dollar_vol = cfg.get("universe.min_avg_dollar_volume", 5_000_000)

    # Batch bar requests for 20-day average dollar volume
    kept: list[str] = []
    batch_size = 200
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        req = StockBarsRequest(symbol_or_symbols=batch, timeframe=TimeFrame.Day, limit=20)
        bars = data_client.get_stock_bars(req).df
        if bars.empty:
            continue
        dollar_vol = (bars["close"] * bars["volume"]).groupby(level=0).mean()
        kept.extend(dollar_vol[dollar_vol >= min_dollar_vol].index.tolist())
    after_dollar_volume = len(kept)

    # Spread filter needs a live quote per symbol — done lazily by the caller
    # (quant/execution.py's quote_quality gate) rather than here, to avoid
    # burning a quote call on every universe symbol every run.
    final = sorted(set(kept))

    return UniverseFilterStats(
        total_assets=total,
        after_tradable=after_tradable,
        after_dollar_volume=after_dollar_volume,
        after_spread=after_dollar_volume,  # spread applied downstream, see docstring
        final=final,
    )
