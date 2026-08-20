---
description: Local pre-market research run — mirrors routines/pre-market.md, reads .env, asks before committing
---

Local mirror of `routines/pre-market.md`. Credentials come from `.env`
(already loaded by the wrapper scripts) — no environment-variable check
needed here.

STEP 1 — Read `memory/TRADING-STRATEGY.md`, tail of `memory/TRADE-LOG.md`,
tail of `memory/RESEARCH-LOG.md` and `memory/REGIME-LOG.md`.

STEP 2 — Pull live state: `bash scripts/alpaca.sh account`, `positions`,
`orders`.

STEP 3 — Research via Perplexity (oil, S&P futures, VIX, today's catalysts,
pre-market earnings, economic calendar, sector momentum, news on held
tickers) — same query list as `routines/pre-market.md` STEP 3. Fall back to
WebSearch and note it if `scripts/perplexity.sh` exits 3.

STEP 4 — `python3 scripts/quant_cli.py regime --qqq [--vix X] [--breadth Y]`

STEP 5 — Pick up to 5 candidates with a real catalyst, run
`python3 scripts/quant_cli.py scan TICKER...`, then `evaluate` the top 2-3
(no order is placed by either).

STEP 6 — Write a dated entry to `memory/RESEARCH-LOG.md` and append to
`memory/REGIME-LOG.md`, matching their existing formats.

STEP 7 — Notify only if urgent: `bash scripts/clickup.sh "<alert>"`.

STEP 8 — Ask the user whether to commit (local runs don't auto-commit). If
yes: `git add memory/RESEARCH-LOG.md memory/REGIME-LOG.md && git commit -m
"pre-market research $(date +%Y-%m-%d)"` (push only if asked).
