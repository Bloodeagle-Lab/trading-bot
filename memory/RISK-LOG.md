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

## 2026-08-20 20:1x UTC — RESOLVED: cloud routine push to `main` now works

Re-tested during the second cloud `pre-market` run of the day. The
routine's own mandatory persistence step succeeded on its own:

- `git push origin HEAD:main` → `6ab5b35..d9446a7  HEAD -> main`, exit 0.
- No 403, no permission error. Writes to `main` are now allowed for the
  cloud session's git credentials.

This supersedes the "SYSTEMIC: cloud routine persistence blocked" entry
above. The precondition that entry set — *"do not schedule the other four
routines until a test `pre-market` run successfully pushes to `main` on
its own"* — **is now satisfied**. `market-open`, `midday`,
`daily-summary`, and `weekly-review` can be scheduled.

Unrelated open item from this run: the routine fired at 20:09 UTC
(16:09 ET, post-close) rather than the intended 6:00 AM America/Chicago
slot, so every quote it pulled was post-close and unusable for sizing.
See `memory/RESEARCH-LOG.md`'s Risk Factors for detail. Check the cron's
configured timezone before relying on the schedule.

## 2026-08-20 16:10 — Portfolio heat snapshot
- Total heat: 0.00% of equity — no open positions
- Positions: 0/6 | Sector exposure: {}
- Sector fail streaks: {}

## 2026-08-20 16:10 — REJECTED DE
- Gate: NO-TRADE (quant/no_trade.py)
- Reason: no ML probability available yet (champion model not trained) — insufficient evidence; sleeve disagreement: {'momentum': 0.705, 'trend': 0.582, 'breakout': 0.9, 'mean_reversion': -0.748, 'relative_strength': 0.424}; regime confidence 0.32 below minimum 0.40; spread/liquidity failed (spread 11.08% > 0.5% or illiquid)

## 2026-08-20 16:10 — REJECTED JNJ
- Gate: NO-TRADE (quant/no_trade.py)
- Reason: no ML probability available yet (champion model not trained) — insufficient evidence; sleeve disagreement: {'momentum': 0.543, 'trend': 0.535, 'breakout': 0.45, 'mean_reversion': -0.669, 'relative_strength': 0.29}; regime confidence 0.32 below minimum 0.40; spread/liquidity failed (spread 100.00% > 0.5% or illiquid)

## 2026-08-20 16:10 — REJECTED MRK
- Gate: NO-TRADE (quant/no_trade.py)
- Reason: no ML probability available yet (champion model not trained) — insufficient evidence; sleeve disagreement: {'momentum': 0.528, 'trend': 0.404, 'breakout': 0.482, 'mean_reversion': -0.704, 'relative_strength': 0.277}; regime confidence 0.32 below minimum 0.40; spread/liquidity failed (spread 10.12% > 0.5% or illiquid)

## 2026-08-20 — BUG: quote-fetch failure degrades to a $0.00 entry price

`bash scripts/alpaca.sh quote JNJ` returned HTTP 502 during the post-close
`pre-market` run. `scripts/quant_cli.py evaluate JNJ` did **not** surface
that failure. It returned:

- `entry_price: 0.0`, `stop_price: -8.49`, `target_price: 16.98`,
  `spread_pct: 100.0`, `setup_quality.risk_quality: 50.0`

The NO-TRADE filter rejected the candidate (on the 100% spread among other
reasons), so nothing reached sizing or execution — the fail-safe held. But
the failure mode is wrong: a dead quote endpoint should raise, not
manufacture a zero price and a negative stop and let them flow downstream.
`quant/risk.py` sizes as `shares = risk_dollars / risk_per_share`; a $0.00
entry with a negative stop produces a risk-per-share that is meaningless,
and the only thing standing between that and an order today was a gate
that happened to fire for other reasons too.

**Action needed before `market-open` runs unattended:** make the quote path
treat a non-200 response as a hard error that aborts the evaluation, rather
than returning a zero/None price that downstream code treats as a number.

## 2026-08-20 — SCHEDULING: `pre-market` routine is firing post-close

This run started at 16:10 ET — 6h40m after the open it is named for, and
10 minutes after the close. Consequences observed in this run:

- Every quote returned is the 16:00:00 ET closing-auction cross
  (all timestamped 20:00:00Z), with auction-width bid/ask spreads: DE
  $591.04 / $664.65, MRK $142.40 / $158.44. The spread gate correctly
  rejected all three candidates, but it was rejecting bad input, not
  judging the names.
- The "pre-market" research it produced describes a session that already
  finished.
- `market-open` (if scheduled) would find no same-morning research entry.

**Action needed:** move the `pre-market` cron trigger to roughly 07:00-09:00
ET on trading days. Until then this routine cannot do the job it exists to
do, and its NO-TRADE results should not be read as evidence about the
candidates.

## 2026-08-20 — Persistence: this run's memory is on a session branch, not main

`CLAUDE.md` requires each routine to push memory to `main`. This session was
assigned the branch `claude/sharp-rubin-ng4nj9` and instructed not to push
anywhere else, so this run's memory commit lands there. It must be merged to
`main` for the next routine's fresh clone to see it. Related to, but
distinct from, the GitHub App write-403 finding above.

## 2026-08-23 — SCHEDULING: `pre-market` routine fired on a Sunday (non-trading day)

The cron trigger fired today, 2026-08-23, which is a Sunday — markets are
closed, no earnings, no economic releases, no live quotes. This is a
different failure mode than the 2026-08-20 post-close-timing issue already
logged above (wrong hour on a real trading day): this is the routine
running on a day the market isn't even open at all.

Consequences this run:
- All price/index data pulled (WTI, Brent, ES futures, VIX) was Friday
  8/21's stale settle, not live.
- No candidate scan/evaluate was run — no legitimate catalyst exists for a
  Sunday, and testing the pipeline against Monday's names using
  weekend-stale quotes would produce meaningless output and risked
  reproducing the known ask=0.0 degraded-quote bug on data that was never
  live to begin with. See `memory/RESEARCH-LOG.md`'s 2026-08-23 entry.

**Action needed:** verify the cron schedule excludes Saturday/Sunday
entirely (weekday-only trigger), not just the correct hour on trading
days. If `market-open` or `midday` fire on a weekend with this
misconfiguration, they must NOT be allowed to reach the execution gate —
worth confirming both wrappers/CLI treat a closed market as a hard stop
independent of the cron schedule, not just relying on the schedule being
right.

## 2026-08-23 — DATA QUALITY: regime engine's SPY/QQQ features frozen across 4+ days

`python3 scripts/quant_cli.py regime --qqq --vix X` has returned
byte-identical `trend_spy` (0.584), `trend_qqq` (0.587), and
`volatility_20` (0.1811) on every `pre-market` run since 2026-08-20 (four
distinct calendar dates: 08-20 x2, 08-21, 08-22, 08-23), producing the same
0.392 confidence every time VIX is supplied in the same ~15-16 range.
`breadth_pct_above_50dma` has also returned `null` every single run.

This is very unlikely to reflect real market behavior across four separate
days (SPY/QQQ trend and 20-day realized vol do not stay static day to day
even in a genuinely quiet tape) and reads as `quant/regime.py` (or
whatever data source feeds it) pulling from a stale/cached snapshot rather
than a live SPY/QQQ series. Today's run (a Sunday) can't distinguish "no
new bar exists yet" from "the feed is stuck," but the pattern already
spanned three real trading days before today.

**Action needed:** check `quant/regime.py`'s SPY/QQQ data source directly
(not just the CLI's JSON output) to confirm it's pulling a fresh daily bar
before the confidence score from any future `regime`/`scan`/`evaluate` call
is trusted for real sizing. If it's genuinely stuck, every NO-TRADE
decision citing "regime confidence below minimum" since 2026-08-20 was
correct by coincidence (frozen inputs happen to sit under the 0.40 bar),
not because the gate evaluated real data.
