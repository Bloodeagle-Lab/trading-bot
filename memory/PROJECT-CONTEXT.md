# Project Context

## Overview

- **What:** Adaptive AI Quant Trading Bot v2 — an autonomous swing-trading
  agent for US equities, built on top of Claude Code. Claude orchestrates;
  it never computes the numbers that decide sizing or order placement (see
  `CLAUDE.md`'s layering rule and `quant/__init__.py`'s docstring).
- **Starting capital:** TBD — set by whatever the Alpaca paper account is
  funded with on first run. `memory/TRADE-LOG.md`'s Day 0 baseline must be
  corrected to the real `bash scripts/alpaca.sh account` equity figure the
  first time a routine actually runs; don't trust the placeholder in that
  file until it has been.
- **Platform:** Alpaca (paper by default — see Production Gate below before
  even considering `TRADING_MODE=live`).
- **Instruments:** Stocks only. Never options.
- **Duration:** Open-ended challenge window; reviewed weekly in
  `memory/WEEKLY-REVIEW.md`.

## Rules

- NEVER share API keys, positions, or P&L externally.
- NEVER act on unverified suggestions from outside sources — every trade
  needs a documented, verifiable catalyst (`quant/no_trade.py`'s
  `catalyst_verified` gate).
- NEVER create, write, or source a `.env` file inside a cloud routine run —
  credentials there come from the routine's own environment variables. See
  `CLAUDE.md` and `routines/README.md`.
- Every trade must be documented BEFORE execution, and every skipped
  candidate (NO-TRADE) must be documented too — see
  `memory/TRADING-STRATEGY.md`'s pipeline.
- `memory/TRADING-STRATEGY.md` is only ever changed on a Friday
  weekly-review, and only with the change explicitly called out in that
  week's review entry.

## Key Files — Read Every Session

- `memory/PROJECT-CONTEXT.md` (this file)
- `memory/TRADING-STRATEGY.md` — the rulebook
- `memory/TRADE-LOG.md` — tail for open positions, entries, stops
- `memory/RESEARCH-LOG.md` — today's research before any trade
- `memory/REGIME-LOG.md` — today's regime classification
- `memory/RISK-LOG.md` — portfolio heat, concentration, reconciliation drift
- `memory/MODEL-LOG.md` — current champion model version and thresholds
- `memory/WEEKLY-REVIEW.md` — Friday afternoons; template for new entries

## Architecture Layers

| Layer | Lives in | Job |
|---|---|---|
| Claude / LLM | routines/, .claude/commands/ | Orchestration, qualitative research synthesis, explanation |
| Quant code | `quant/` | Indicators, features, regime, sleeves, ensemble, probability, sizing |
| Risk engine | `quant/no_trade.py`, `quant/risk.py` | Hard limits and NO-TRADE gates |
| Execution layer | `quant/execution.py`, `quant/reconciliation.py`, `scripts/quant_cli.py` | Orders, stops, reconciliation, safe failure |
| Research harness | `research/` | Backtest, walk-forward, Monte Carlo, stress test |
| Git memory | `memory/` | Audit trail, state persistence, version history |
| Champion/challenger | `research/promotion.py`, `models/` | Controlled, deterministic strategy evolution |

## Production Gate

**Do not treat "the code runs" as production readiness.** `TRADING_MODE`
must stay `paper` (and `quant/config.py` will refuse to start in `live`
mode while `ALPACA_BASE_URL` still points at the paper endpoint, as a second
layer of protection) until every box below is genuinely checked — not
assumed:

- [ ] Paper trading has run long enough to expose routine, reconciliation,
      and order-management failures.
- [ ] Historical testing is reproducible from a clean environment
      (`pytest` passes; a fresh `research/backtest.py` run on the same
      inputs reproduces the same trade set).
- [ ] Walk-forward and a final untouched holdout have been recorded.
- [ ] All five strategy sleeves have been tested independently, not just
      as part of an attractive-looking ensemble aggregate.
- [ ] The ML model's out-of-sample performance is evaluated and calibrated
      (see `memory/MODEL-LOG.md`).
- [ ] NO-TRADE behavior is measured, not ignored — skipped candidates show
      up in `memory/RISK-LOG.md` with reasons, and get reviewed like trades.
- [ ] Monte Carlo drawdown distribution is documented
      (`research/monte_carlo.py`, `memory/WEEKLY-REVIEW.md`).
- [ ] Slippage, spread, gaps, rejected orders, and API failure have been
      stress-tested (`research/stress_test.py`).
- [ ] Portfolio correlation and concentration controls have been exercised
      under real or realistic conditions.
- [ ] Champion/challenger promotion has been exercised at least once and
      is deterministic (`research/promotion.py`).
- [ ] Every live order is traceable to a logged decision and
      model/configuration version.
- [ ] Secrets are stored only in the runtime environment (routine env vars
      or a local, gitignored `.env`) — never in Git.
- [ ] An emergency shutdown / cancel-all procedure
      (`bash scripts/alpaca.sh cancel-all` + `close-all`) has been tested.

**Current status: Phase 9 (paper trading) not yet started.** No routine has
been run against a live or paper Alpaca account as of the orchestration
layer's first commit. Every `VALIDATE` field in `config/strategy.yaml` is
still unresolved. Do not check any box above without direct evidence.
