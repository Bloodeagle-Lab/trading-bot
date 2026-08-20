"""Shared fixtures for the quant/ and research/ unit tests.

Kept deliberately dependency-light: everything here is synthetic, in-memory
data — no network calls, no real Alpaca/Perplexity/ClickUp credentials, and
no reliance on config/strategy.yaml's VALIDATE placeholders. Tests that need
a specific config value build their own minimal Config via `make_config`
rather than loading the real strategy.yaml, so they stay stable if the repo's
own strategy config changes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quant.config import Config


def make_config(overrides: dict | None = None) -> Config:
    """Builds a Config with sane, fully-validated (non-VALIDATE) defaults so
    gated code paths (require_validated, heat_gate_ok, etc.) can be exercised
    without touching the real strategy.yaml or an .env file."""
    raw = {
        "universe": {"max_spread_pct": 0.5, "min_avg_dollar_volume": 5_000_000},
        "portfolio": {"max_positions": 6, "max_position_pct": 0.20, "max_new_trades_per_week": 3},
        "strategy": {
            "reward_risk_minimum": 2.0,
            "sleeves": {"momentum": True, "trend": True, "breakout": True, "mean_reversion": True, "relative_strength": True},
            "regime_weights": {
                "STRONG_TREND": {"momentum": 1.0, "trend": 1.0, "breakout": 1.0, "mean_reversion": 0.0, "relative_strength": 0.8},
                "CHOPPY": {"momentum": 0.2, "trend": 0.2, "breakout": 0.3, "mean_reversion": 1.0, "relative_strength": 0.5},
            },
        },
        "risk": {"max_risk_per_trade_pct": 0.5, "max_portfolio_heat_pct": 3.0},
        "no_trade": {"probability_threshold": 0.55, "min_regime_confidence": 0.4, "min_setup_quality": 60, "require_catalyst_verification": True},
        "validation": {
            "stress_slippage_multipliers": [1.25, 1.50, 2.00],
            "min_out_of_sample_trades": 30,
            "max_drawdown_increase_pct": 5.0,
        },
        "live_mode": {"default": "paper", "require_production_gate": True},
    }
    if overrides:
        for section, values in overrides.items():
            raw.setdefault(section, {})
            if isinstance(values, dict):
                raw[section].update(values)
            else:
                raw[section] = values
    return Config(
        raw=raw, mode="paper",
        alpaca_api_key="test", alpaca_secret_key="test",
        alpaca_base_url="https://paper-api.alpaca.markets",
        alpaca_data_url="https://data.alpaca.markets",
        perplexity_api_key="", clickup_api_key="", clickup_list_id="",
    )


@pytest.fixture
def cfg() -> Config:
    return make_config()


def make_ohlcv(n: int = 260, start_price: float = 100.0, drift: float = 0.0005, vol: float = 0.015, seed: int = 7) -> pd.DataFrame:
    """A synthetic, deterministic OHLCV series: geometric random walk with
    configurable drift/volatility, enough bars (default 260) to warm up a
    200-day SMA. Not real market data — only used to exercise the math."""
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    close = start_price * np.cumprod(1 + rets)
    high = close * (1 + np.abs(rng.normal(0, vol / 3, n)))
    low = close * (1 - np.abs(rng.normal(0, vol / 3, n)))
    open_ = np.roll(close, 1)
    open_[0] = start_price
    volume = rng.integers(500_000, 2_000_000, n).astype(float)
    idx = pd.bdate_range("2023-01-02", periods=n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=idx)


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    return make_ohlcv()
