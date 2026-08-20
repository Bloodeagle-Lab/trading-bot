---
description: Local midday risk-management run — mirrors routines/midday.md, reads .env, asks before committing
---

Local mirror of `routines/midday.md`. Credentials come from `.env`. **This
can close real positions and cancel/replace real stop orders — treat it
with the same care as the cloud routine.**

STEP 1 — Read `memory/TRADING-STRATEGY.md`, tail of `memory/TRADE-LOG.md`,
today's `memory/RESEARCH-LOG.md`.

STEP 2 — `python3 scripts/quant_cli.py stops-check` for the deterministic
close/tighten/hold action list. Don't second-guess it with your own
arithmetic.

STEP 3 — For each `close` action, confirm with the user then:
`python3 scripts/quant_cli.py close TICKER --reason "..."`.

STEP 4 — For each `tighten_stop` action, confirm then:
`python3 scripts/quant_cli.py tighten-stop TICKER --trail-percent N
--current-trail-percent M`.

STEP 5 — Thesis check on remaining positions; close (with confirmation) if
a thesis broke intraday even if `stops-check` said hold. One optional
Perplexity query if something moved sharply with no obvious cause.

STEP 6 — Append actions to `memory/TRADE-LOG.md` / `memory/RISK-LOG.md`.

STEP 7 — Notify only if action was taken.

STEP 8 — Ask the user whether to commit (push only if asked).
