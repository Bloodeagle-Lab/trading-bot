---
description: Local daily-summary run — mirrors routines/daily-summary.md, reads .env, asks before committing
---

Local mirror of `routines/daily-summary.md`. Credentials come from `.env`.

STEP 1 — Find yesterday's closing equity from the most recent EOD snapshot
in `memory/TRADE-LOG.md`. Count today's trades and this week's running
count.

STEP 2 — `python3 scripts/quant_cli.py positions` for today's final state
and stop-presence flags.

STEP 3 — Compute day P&L and phase-to-date P&L ($ and %), list today's
trades.

STEP 4 — Append a dated EOD snapshot to `memory/TRADE-LOG.md`, matching the
file's existing format.

STEP 5 — Send one ClickUp message, always, under 15 lines. Call out any
stop-presence flags explicitly.

STEP 6 — Ask the user whether to commit (this one matters even locally —
tomorrow's day P&L depends on today's snapshot existing somewhere). Push
only if asked.
