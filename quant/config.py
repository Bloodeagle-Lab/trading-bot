"""
Central configuration loader.

Everything downstream (universe, risk, execution, ...) reads settings from
here rather than hard-coding thresholds. Two sources are merged:

  1. config/strategy.yaml   — strategy/risk/validation knobs, safe to commit
  2. .env                   — secrets and environment mode, NEVER committed

Fields left as the string "VALIDATE" in strategy.yaml are placeholders the
PDF spec explicitly says must come from backtesting, not guesswork. Any code
path that would trade on a VALIDATE field must refuse to run live.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
STRATEGY_YAML = ROOT / "config" / "strategy.yaml"


class UnvalidatedParameterError(RuntimeError):
    """Raised when a VALIDATE placeholder is used somewhere that requires a real value."""


def _load_yaml() -> dict[str, Any]:
    with open(STRATEGY_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Config:
    raw: dict[str, Any]
    mode: str                      # "paper" | "live"
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str
    alpaca_data_url: str
    perplexity_api_key: str
    clickup_api_key: str
    clickup_list_id: str

    def get(self, dotted_path: str, default: Any = None) -> Any:
        """Dotted access into the strategy YAML, e.g. cfg.get('risk.max_portfolio_heat_pct')."""
        node: Any = self.raw
        for part in dotted_path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def require_validated(self, dotted_path: str) -> Any:
        """Use for any threshold that gates real risk (sizing, NO-TRADE, ML threshold).
        Raises loudly instead of silently trading on a placeholder."""
        value = self.get(dotted_path)
        if value is None or (isinstance(value, str) and value.strip().upper() == "VALIDATE"):
            raise UnvalidatedParameterError(
                f"config field '{dotted_path}' is still VALIDATE / unset. "
                "Run research/backtest.py + walk_forward.py to pick a real value "
                "before this code path can execute."
            )
        return value

    @property
    def is_live(self) -> bool:
        return self.mode == "live"

    @property
    def effective_max_spread_pct(self) -> float:
        """
        THE single source of truth for the spread/liquidity threshold — live
        mode always uses universe.max_spread_pct (the real one); paper mode
        uses universe.max_spread_pct_paper_only if set, else falls back to
        the same real threshold. Both quant/execution.py's check_quote_quality
        and scripts/quant_cli.py's cmd_evaluate must call THIS, not re-derive
        their own copy — two independent inline copies of this exact
        condition (both effectively hardcoding the live threshold, blind to
        mode) is exactly how the 2026-08-24 bug happened: a correctly
        computed paper-mode liquidity_ok=True got silently overridden by a
        second check elsewhere that never knew the paper override existed.
        """
        if self.is_live:
            return self.get("universe.max_spread_pct", 0.5)
        return self.get("universe.max_spread_pct_paper_only", self.get("universe.max_spread_pct", 0.5))


def load_config(env_file: str | Path | None = None) -> Config:
    load_dotenv(dotenv_path=env_file or (ROOT / ".env"), override=False)
    raw = _load_yaml()
    mode = os.getenv("TRADING_MODE", "paper").strip().lower()
    if mode not in ("paper", "live"):
        raise ValueError(f"TRADING_MODE must be 'paper' or 'live', got {mode!r}")

    cfg = Config(
        raw=raw,
        mode=mode,
        alpaca_api_key=os.getenv("ALPACA_API_KEY", ""),
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
        alpaca_base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets"),
        alpaca_data_url=os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets"),
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY", ""),
        clickup_api_key=os.getenv("CLICKUP_API_KEY", ""),
        clickup_list_id=os.getenv("CLICKUP_LIST_ID", ""),
    )

    if cfg.is_live:
        if not cfg.get("live_mode.require_production_gate", True):
            raise RuntimeError("live_mode.require_production_gate must stay true.")
        if "paper-api" in cfg.alpaca_base_url:
            raise RuntimeError(
                "TRADING_MODE=live but ALPACA_BASE_URL still points at the paper endpoint. Refusing to start."
            )
    return cfg
