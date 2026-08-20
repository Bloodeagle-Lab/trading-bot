# Risk Log

Portfolio heat, concentration decisions, rejected/NO-TRADE candidates, and
reconciliation drift — everything the risk and execution gates decided,
whether or not it resulted in an order. A NO-TRADE or a rejected order
belongs here as much as a filled one does; this file is the audit trail for
what did NOT happen, not just what did.

**Note:** the `### Reconciliation — <timestamp>` sections below are
appended automatically by `quant/reconciliation.py`'s `reconcile()` every
time any routine touches orders — do not hand-edit those sections, and
don't be surprised to see them interleaved with the manual entries below.

## Entry format (portfolio heat / sizing decision)

```
## YYYY-MM-DD HH:MM — Portfolio heat snapshot
- Total heat: X.XX% of equity (cap: X.X%)
- Positions: N/6 | Sector exposure: {SECTOR: X.X%, ...}
- Sector fail streaks: {SECTOR: N, ...}
```

## Entry format (rejected candidate — execution gate or NO-TRADE)

```
## YYYY-MM-DD HH:MM — REJECTED TICKER
- Gate: symbol_validation | quote_quality | position_limit | weekly_trade_limit
  | risk_budget | cash_buying_power | open_order_conflict | stop_protection
  | NO-TRADE (quant/no_trade.py)
- Reason: <verbatim gate/reason string>
```

---

No entries yet. Populated automatically (reconciliation) and by
`market-open`/`midday` routines as gates fire.

### Reconciliation — 2026-08-20 12:12:02
No drift — local state matched broker.

## 2026-08-20 — SYSTEMIC: cloud routine persistence blocked

The first cloud `pre-market` routine run completed its full decision
pipeline correctly (regime → scan → evaluate → HOLD), but its final
`git push origin main` step failed:

- `git push` and the GitHub MCP's `push_files` both returned 403
  ("Resource not accessible by integration"). Reads (`git ls-remote`,
  fetch) worked; only writes were denied.
- The session was assigned to a side branch (`claude/trusting-bardeen-j4jj1p`),
  not `main` — but the push failed on that branch too, so this is not
  (only) the "push to main requires the unrestricted-branch-pushes toggle"
  case the original setup guide warns about — it looks like the Claude
  GitHub App simply does not have write (Contents: read and write)
  access to `Bloodeagle-Lab/trading-bot` yet, on any branch.
- Per the session's own guidance (`/root/.ccr/README.md`): 403s are an
  organization/permission denial, not a transient error — retrying
  doesn't help.
- Commit was lost when the ephemeral workspace was reclaimed. Today's
  findings were manually reconstructed into `memory/RESEARCH-LOG.md`,
  `memory/REGIME-LOG.md`, and `memory/TRADE-LOG.md`'s Day 0 baseline from
  the routine's reported chat summary (not from the lost commit itself),
  and pushed via a working local git session instead.

**Every routine's mandatory commit-and-push step will fail identically
until this is fixed.** Action needed (outside this repo): grant the
Claude GitHub App write access to this repo — check
`github.com/settings/installations` → Claude → Configure →
Repository permissions (should be "Contents: Read and write", not
read-only), and/or reconnect GitHub under Claude's own connectors
settings. Do not schedule the other four routines (`market-open`,
`midday`, `daily-summary`, `weekly-review`) until a test `pre-market` run
successfully pushes to `main` on its own.
