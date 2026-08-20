from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd
import pytest

from scripts.quant_cli import (
    build_parser, compute_stops_check_actions, print_result, to_jsonable, validate_tighten_stop,
)
from tests.conftest import make_config


# ---- to_jsonable ------------------------------------------------------

def test_to_jsonable_converts_numpy_scalars():
    assert to_jsonable(np.bool_(True)) is True
    assert to_jsonable(np.int64(7)) == 7
    assert isinstance(to_jsonable(np.int64(7)), int)
    assert to_jsonable(np.float64(3.5)) == 3.5
    assert isinstance(to_jsonable(np.float64(3.5)), float)


def test_to_jsonable_converts_timestamp():
    ts = pd.Timestamp("2024-01-01")
    out = to_jsonable(ts)
    assert isinstance(out, str)
    assert "2024-01-01" in out


def test_to_jsonable_recurses_into_dataclass():
    @dataclasses.dataclass
    class Inner:
        flag: np.bool_

    @dataclasses.dataclass
    class Outer:
        inner: Inner
        values: list

    obj = Outer(inner=Inner(flag=np.bool_(False)), values=[np.int64(1), np.float64(2.5)])
    out = to_jsonable(obj)
    assert out == {"inner": {"flag": False}, "values": [1, 2.5]}
    assert isinstance(out["inner"]["flag"], bool)


def test_to_jsonable_recurses_into_nested_dict_and_list():
    obj = {"a": [np.bool_(True), {"b": np.int64(3)}]}
    out = to_jsonable(obj)
    assert out == {"a": [True, {"b": 3}]}


def test_to_jsonable_passes_through_plain_types_unchanged():
    assert to_jsonable("x") == "x"
    assert to_jsonable(None) is None
    assert to_jsonable(3.14) == 3.14


# ---- print_result -------------------------------------------------------

def test_print_result_returns_zero_on_success(capsys):
    code = print_result({"ok": True})
    assert code == 0
    out = capsys.readouterr().out
    assert '"ok": true' in out


def test_print_result_returns_one_on_error(capsys):
    code = print_result({"error": "bad"}, error=True)
    assert code == 1
    out = capsys.readouterr().out
    assert '"error": "bad"' in out


def test_print_result_serializes_numpy_leakage_safely(capsys):
    # this is exactly the class of bug found in research/promotion.py —
    # confirm the CLI boundary can't be broken by it even if it recurs
    code = print_result({"passed": np.bool_(False), "n": np.int64(5)})
    assert code == 0
    out = capsys.readouterr().out
    assert '"passed": false' in out
    assert '"n": 5' in out


# ---- validate_tighten_stop ----------------------------------------------

def test_validate_tighten_stop_rejects_within_min_distance():
    ok, reason = validate_tighten_stop(2.0, current_trail_pct=10.0)
    assert ok is False
    assert "guardrail" in reason


def test_validate_tighten_stop_rejects_moving_stop_down():
    ok, reason = validate_tighten_stop(9.0, current_trail_pct=7.0)
    assert ok is False
    assert "never move a stop down" in reason


def test_validate_tighten_stop_allows_legitimate_tighten():
    ok, reason = validate_tighten_stop(5.0, current_trail_pct=7.0)
    assert ok is True


def test_validate_tighten_stop_allows_when_current_unknown():
    ok, reason = validate_tighten_stop(5.0, current_trail_pct=None)
    assert ok is True


def test_validate_tighten_stop_boundary_at_min_distance():
    ok, _ = validate_tighten_stop(3.0, current_trail_pct=None)
    assert ok is True
    ok, _ = validate_tighten_stop(2.999, current_trail_pct=None)
    assert ok is False


# ---- compute_stops_check_actions ----------------------------------------

def test_stops_check_closes_on_hard_loss_cut():
    cfg = make_config()
    positions = [{"ticker": "XYZ", "unrealized_pl_pct": -0.08, "current_trail_pct": 10.0}]
    actions = compute_stops_check_actions(positions, cfg)
    assert actions[0]["action"] == "close"
    assert "hard loss cut" in actions[0]["reason"]


def test_stops_check_hold_when_loss_not_yet_at_cut():
    cfg = make_config()
    positions = [{"ticker": "XYZ", "unrealized_pl_pct": -0.03, "current_trail_pct": 10.0}]
    actions = compute_stops_check_actions(positions, cfg)
    assert actions[0]["action"] == "hold"


def test_stops_check_tightens_at_15_percent_trigger():
    cfg = make_config({"stops": {
        "hard_loss_cut_pct": 7, "winner_trail_1_pct": 7, "winner_trail_1_trigger_gain_pct": 15,
        "winner_trail_2_pct": 5, "winner_trail_2_trigger_gain_pct": 20,
    }})
    positions = [{"ticker": "XYZ", "unrealized_pl_pct": 0.16, "current_trail_pct": 10.0}]
    actions = compute_stops_check_actions(positions, cfg)
    assert actions[0]["action"] == "tighten_stop"
    assert actions[0]["new_trail_pct"] == 7


def test_stops_check_tightens_at_20_percent_trigger_takes_precedence():
    cfg = make_config({"stops": {
        "hard_loss_cut_pct": 7, "winner_trail_1_pct": 7, "winner_trail_1_trigger_gain_pct": 15,
        "winner_trail_2_pct": 5, "winner_trail_2_trigger_gain_pct": 20,
    }})
    positions = [{"ticker": "XYZ", "unrealized_pl_pct": 0.25, "current_trail_pct": 10.0}]
    actions = compute_stops_check_actions(positions, cfg)
    assert actions[0]["action"] == "tighten_stop"
    assert actions[0]["new_trail_pct"] == 5


def test_stops_check_holds_when_tighten_would_move_stop_down():
    cfg = make_config({"stops": {
        "hard_loss_cut_pct": 7, "winner_trail_1_pct": 7, "winner_trail_1_trigger_gain_pct": 15,
        "winner_trail_2_pct": 5, "winner_trail_2_trigger_gain_pct": 20,
    }})
    # already tightened to 5% (from a prior +20% run); a fresh +16% read
    # would compute target 7%, which is LOOSER than the current 5% -> hold
    positions = [{"ticker": "XYZ", "unrealized_pl_pct": 0.16, "current_trail_pct": 5.0}]
    actions = compute_stops_check_actions(positions, cfg)
    assert actions[0]["action"] == "hold"
    assert "skipped" in actions[0]["reason"]


def test_stops_check_handles_multiple_positions_independently():
    cfg = make_config()
    positions = [
        {"ticker": "A", "unrealized_pl_pct": -0.09, "current_trail_pct": 10.0},
        {"ticker": "B", "unrealized_pl_pct": 0.01, "current_trail_pct": 10.0},
    ]
    actions = compute_stops_check_actions(positions, cfg)
    by_ticker = {a["ticker"]: a for a in actions}
    assert by_ticker["A"]["action"] == "close"
    assert by_ticker["B"]["action"] == "hold"


# ---- argparse wiring ------------------------------------------------------

def test_build_parser_exposes_every_documented_subcommand():
    parser = build_parser()
    sub_action = next(a for a in parser._actions if a.dest == "command")
    assert set(sub_action.choices.keys()) == {
        "regime", "scan", "evaluate", "execute", "close", "tighten-stop", "reconcile", "positions", "stops-check",
    }


def test_execute_requires_all_safety_critical_flags():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["execute", "XYZ", "--shares", "10"])  # missing entry/stop/reason/etc.


def test_execute_parses_with_all_required_flags():
    parser = build_parser()
    args = parser.parse_args([
        "execute", "XYZ", "--shares", "10", "--entry-price", "50", "--stop-price", "47",
        "--reason", "test", "--trades-this-week", "1", "--approved-risk-dollars", "30",
    ])
    assert args.ticker == "XYZ"
    assert args.shares == 10
    assert args.trailing_stop_pct is None  # falls back to config default in cmd_execute


def test_tighten_stop_requires_trail_percent():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["tighten-stop", "XYZ"])


def test_scan_requires_at_least_one_ticker():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scan"])
