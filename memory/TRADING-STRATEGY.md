# Trading Strategy

The rulebook. Every workflow (routines/*.md and .claude/commands/*.md) reads
this file first, before touching Alpaca. It is a human-readable mirror of
`config/strategy.yaml` plus the hard rules that exist independent of any
tunable number — **the agent must never violate these**, and must never
silently rewrite this file. It only changes on a Friday weekly-review, and
only when a rule has proven itself for 2+ weeks or failed badly, with the
change called out explicitly in that week's `WEEKLY-REVIEW.md` entry.

## Mission

Beat the S&P 500 over the challenge window, trading stocks only, with
discipline enforced programmatically — not left to interpretation. This is
the "Adaptive AI Quant Trading Bot v2" design: an ensemble of five strategy
sleeves, a market-regime engine, an ML probability layer, and an explicit
NO-TRADE filter sit between "the LLM read some research" and "an order got
placed." See `memory/PROJECT-CONTEXT.md` for the full architecture and the
Production Gate that must be satisfied before real capital goes live.

## Hard Rules (non-negotiable, no config override)

- **NO OPTIONS. Ever.** Stocks only.
- Maximum 5-6 open positions at a time.
- Maximum 20% of equity per position.
- Maximum 3 new trades per week.
- Target 75-85% of capital deployed.
- Every new position gets a **real 10% trailing stop GTC order on Alpaca.
  Never mental, never a bracket fixed-stop substitute.**
- Cut any losing position at **-7% from entry**, manually, immediately.
  No hoping, no averaging down.
- Tighten the trailing stop to **7% when a position is up +15%**, to
  **5% when up +20%**.
- **Never** tighten a stop to within 3% of current price. **Never** move a
  stop down.
- Exit an entire sector after **2 consecutive failed trades** in that
  sector (`quant/portfolio.py`'s `sector_fail_streak`, enforced by
  `concentration_ok`).
- Follow sector momentum. Don't force a thesis against a rolling-over
  sector.
- **Patience beats activity.** A week — or a day — with zero trades is a
  valid, measured outcome, not a failure. NO-TRADE decisions are logged
  and reviewed exactly like trades are.
- A trade **must not** be placed unless every buy-side gate check passes.
  Any failure is logged with its reason; the candidate is skipped, not
  overridden.

## The v2 Decision Pipeline (what actually gates an order)

No routine, and no human reading a chat message, decides position size or
whether an order is "close enough" to pass a rule. Every buy candidate runs
through this exact pipeline, in this order, all deterministic code in
`quant/` — see `CLAUDE.md` for the layering rule this enforces:

1. **Regime** (`quant/regime.py`) — classify today's market state
   (STRONG_TREND / CHOPPY / HIGH_VOL / RISK_OFF / TRANSITION) with a
   confidence score.
2. **Sleeves + Ensemble** (`quant/strategies.py`, `quant/ensemble.py`) —
   five independently-scored sleeves (momentum, trend, breakout,
   mean-reversion, relative-strength), combined with regime-aware weights
   from `config/strategy.yaml`'s `strategy.regime_weights`.
3. **ML probability** (`quant/model.py`) — the trained champion model's
   estimate of P(reach +2R before -1R within N days). `None` (not 0.5) if
   no champion has been trained yet.

   **2026-08-21 — deliberate, evidenced exception:** four separate training
   attempts (different data sizes, algorithms, and feature sets — raw
   technical indicators, then the system's own sleeve/ensemble/regime
   signals, then cross-sectional peer rank) all found no tradeable edge;
   see `memory/MODEL-LOG.md` for the full record. Rather than block all
   trading indefinitely with no path forward,
   `no_trade.require_ml_probability` is set to `false` in
   `config/strategy.yaml`: when no ML probability exists, the pipeline
   falls back to the rule-based ensemble/regime engine alone, gated on the
   VALIDATED `strategy.minimum_ensemble_score` (0.55 — backed by real
   walk-forward/Monte-Carlo/stress-test evidence, not a guess) instead of
   hard-blocking. Every other gate below still applies unchanged — this
   removes exactly one confirmation layer, not the whole filter. **Flip
   `require_ml_probability` back to `true`** once a model actually passes
   `research/promotion.py`'s criteria.
4. **NO-TRADE filter** (`quant/no_trade.py`) — the explicit abstention gate.
   Any one of: probability below threshold, sleeve disagreement, low regime
   confidence, low setup quality, wide spread/illiquid, portfolio
   concentration too high, unverified catalyst, insufficient reward:risk,
   or an active risk-off gate → **NO-TRADE**, reason logged.
5. **Adaptive risk sizing** (`quant/risk.py`) — position size is a function
   of setup quality and stop distance (`risk_dollars = equity *
   risk_budget; shares = risk_dollars / risk_per_share`, capped by the
   fixed ceilings above), not a flat dollar amount per ticker.
6. **Execution gate** (`quant/execution.py`) — the last, hard, unbypassable
   check chain (symbol validity, quote quality, position/weekly-trade
   limits, risk budget, cash, open-order conflicts, stop protection) before
   any order reaches Alpaca.

Fields marked `VALIDATE` in `config/strategy.yaml` **must not be trusted**
until `research/backtest.py`, `walk_forward.py`, `monte_carlo.py`, and
`stress_test.py` have produced out-of-sample evidence — `quant/config.py`'s
`require_validated()` raises loudly rather than silently trading on a
placeholder.

## Entry Checklist (documented before every placed order)

- What is the specific, verifiable catalyst today?
- Is the sector in momentum?
- What is the stop level (volatility/structure-based, 7-10% below entry)?
- What is the target (minimum 2:1 risk/reward, `strategy.reward_risk_minimum`)?
- What did the ensemble score, the regime, and the ML probability say?

## Sell-Side Rules (evaluated at midday and opportunistically)

- Unrealized loss ≤ -7% → close immediately, no exceptions.
- Thesis broken (catalyst invalidated, sector rolling over, adverse news)
  → close, even if not yet at -7%.
- Up ≥ +20% → tighten trailing stop to 5%.
- Up ≥ +15% → tighten trailing stop to 7%.
- Sector has 2 consecutive failed trades → exit all positions in that
  sector.

## Champion/Challenger (`research/promotion.py`)

The live ML model ("champion") is never overwritten automatically. A new
model ("challenger") is only promoted after `evaluate_promotion()` returns
`PROMOTE` against four fixed, auditable criteria: minimum out-of-sample
trade count, no unacceptable drawdown increase vs. the champion, stable
performance across regimes, and no material degradation under stress
testing. See `memory/MODEL-LOG.md` for the history of every promotion
decision, promoted or not.
