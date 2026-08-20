---
description: Local market-open execution run — mirrors routines/market-open.md, reads .env, asks before committing
---

Local mirror of `routines/market-open.md`. Credentials come from `.env` —
no environment-variable check needed here. **This still places real orders
against whatever account `.env` points at (paper by default) — treat it
with the same care as the cloud routine.**

STEP 1 — Read `memory/TRADING-STRATEGY.md` and today's
`memory/RESEARCH-LOG.md` entry (run `/pre-market` first if it's missing —
never trade without documented research). Count this week's BUY entries in
`memory/TRADE-LOG.md`.

STEP 2 — Re-validate each planned trade with fresh data:
`python3 scripts/quant_cli.py evaluate TICKER --entry-price P --stop-price P
--catalyst-verified --portfolio-concentration-ok --sector-momentum-score N`.

STEP 3 — For each `no_trade.decision == "PASS"` candidate, confirm with the
user before placing anything (unlike the cloud routine, ask **"execute
TICKER? (y/n)"** here), then:
`python3 scripts/quant_cli.py execute TICKER --shares N --entry-price P
--stop-price P --reason "..." --trades-this-week N --approved-risk-dollars X`.
Read `stop_status` — `queue_for_tomorrow` means no stop is on the position
yet; flag this loudly.

STEP 4 — Append every attempt to `memory/TRADE-LOG.md`.

STEP 5 — Notify only if a trade fired: `bash scripts/clickup.sh "<summary>"`.

STEP 6 — Ask the user whether to commit. If yes: `git add
memory/TRADE-LOG.md memory/RISK-LOG.md && git commit -m "market-open
$(date +%Y-%m-%d)"` (push only if asked).
