---
description: Local weekly-review run — mirrors routines/weekly-review.md, reads .env, asks before committing
---

Local mirror of `routines/weekly-review.md`. Credentials come from `.env`.

STEP 1 — Read this week's `memory/TRADE-LOG.md`, `memory/RESEARCH-LOG.md`,
`memory/REGIME-LOG.md` entries, `memory/WEEKLY-REVIEW.md`'s template, and
`memory/TRADING-STRATEGY.md`.

STEP 2 — `python3 scripts/quant_cli.py positions` for week-end state.

STEP 3 — Compute week return, S&P 500 week return (via
`scripts/perplexity.sh`), W/L/open counts, win rate, best/worst trade,
profit factor, NO-TRADE candidates logged this week.

STEP 4 — Regime performance breakdown for the week.

STEP 5 — Note the current champion model version from `memory/MODEL-LOG.md`
and any challenger evaluation this week. Do not train or promote a model
from this command — that's a deliberate offline research step.

STEP 6 — Append a full review section to `memory/WEEKLY-REVIEW.md`: stats,
closed trades, open positions, regime performance, what worked/didn't,
lessons, adjustments, letter grade.

STEP 7 — Only with real evidence (a rule proven 2+ weeks or failed badly),
propose a `memory/TRADING-STRATEGY.md` change — **ask the user before
applying it**; don't silently rewrite the rulebook even locally. Never
touch `config/strategy.yaml`'s `VALIDATE` fields here.

STEP 8 — Send one ClickUp message with headline numbers.

STEP 9 — Ask the user whether to commit (push only if asked).
