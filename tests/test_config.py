from __future__ import annotations

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
