from __future__ import annotations

import dataclasses

import pytest

from quant.config import Config, UnvalidatedParameterError
from tests.conftest import make_config


def test_get_dotted_path_returns_nested_value():
    c = make_config()
    assert c.get("portfolio.max_positions") == 6


def test_get_dotted_path_missing_returns_default():
    c = make_config()
    assert c.get("does.not.exist", "fallback") == "fallback"


def test_require_validated_raises_on_validate_placeholder():
    c = make_config({"strategy": {"minimum_ensemble_score": "VALIDATE"}})
    with pytest.raises(UnvalidatedParameterError):
        c.require_validated("strategy.minimum_ensemble_score")


def test_require_validated_raises_on_missing_field():
    c = make_config()
    with pytest.raises(UnvalidatedParameterError):
        c.require_validated("strategy.minimum_ensemble_score")


def test_require_validated_passes_through_real_value():
    c = make_config({"strategy": {"minimum_ensemble_score": 0.55}})
    assert c.require_validated("strategy.minimum_ensemble_score") == 0.55


def test_is_live_reflects_mode():
    live = Config(
        raw={}, mode="live",
        alpaca_api_key="k", alpaca_secret_key="s",
        alpaca_base_url="https://api.alpaca.markets", alpaca_data_url="https://data.alpaca.markets",
        perplexity_api_key="", clickup_api_key="", clickup_list_id="",
    )
    paper = make_config()
    assert live.is_live is True
    assert paper.is_live is False


# ---- effective_max_spread_pct ----------------------------------------------
# The single source of truth shared by quant/execution.py's check_quote_quality
# and scripts/quant_cli.py's cmd_evaluate — see quant/config.py's docstring
# for the 2026-08-24 bug this consolidation fixed (two independent inline
# copies of this exact condition drifted out of sync).

def test_effective_max_spread_pct_uses_real_threshold_in_live_mode():
    cfg = dataclasses.replace(
        make_config({"universe": {"max_spread_pct": 0.5, "max_spread_pct_paper_only": 6.0}}),
        mode="live",
    )
    assert cfg.effective_max_spread_pct == 0.5


def test_effective_max_spread_pct_uses_paper_override_in_paper_mode():
    cfg = make_config({"universe": {"max_spread_pct": 0.5, "max_spread_pct_paper_only": 6.0}})
    assert cfg.mode == "paper"
    assert cfg.effective_max_spread_pct == 6.0


def test_effective_max_spread_pct_falls_back_to_real_threshold_if_paper_override_unset():
    cfg = make_config({"universe": {"max_spread_pct": 0.5}})
    assert cfg.effective_max_spread_pct == 0.5


def test_effective_max_spread_pct_live_mode_ignores_paper_override_even_if_looser():
    # the critical safety property: switching to live must NEVER silently
    # inherit the loosened paper-mode spread allowance
    cfg = dataclasses.replace(
        make_config({"universe": {"max_spread_pct": 0.5, "max_spread_pct_paper_only": 50.0}}),
        mode="live",
    )
    assert cfg.effective_max_spread_pct == 0.5
