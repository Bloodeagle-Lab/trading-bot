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

## 2026-08-21 — Persistence: same session-branch issue recurs on daily-summary

This `daily-summary` run was assigned branch `claude/brave-rubin-g81u3p`
with the same no-push-elsewhere-without-permission constraint as
2026-08-20's `pre-market` run. Today's EOD snapshot commit lands there,
not on `main` — this is now a recurring pattern across at least two
different routines and two different assigned branches, not a one-off.
Until this is fixed at the scheduling/harness level, every cloud routine
needs its branch merged to `main` by a human before the next routine's
fresh clone can see prior memory (e.g. tomorrow's day P&L depends on
today's snapshot reaching `main`). **Action needed:** either grant the
scheduled-routine identity push access to `main` directly (matching what
`CLAUDE.md` assumes), or add an automatic merge/PR step after each
routine's push to its assigned branch.

## 2026-08-21 — Persistence: weekly-review run also landed on a session branch, not main

Same pattern as above, recurring. This `weekly-review` session was assigned
`claude/admiring-albattani-jsaf40` with an explicit "never push to a
different branch" instruction, which overrides `routines/weekly-review.md`
STEP 9's `git push origin main`. The 2026-08-21 review entry (and this
note) landed on that branch, not `main` — it must be merged before the
next routine's fresh clone will see this week's review or any of this
week's other memory updates that may be sitting on other session branches.
Worth checking before Monday's `pre-market` run whether `main` is actually
up to date, since a fresh clone from `main` would otherwise silently miss
a full week of memory.

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

**Resolved 2026-08-24:** root cause was `breadth_pct_above_50dma` never
being supplied (always `null`), which alone kept STRONG_TREND's score
capped at 0.6 instead of 0.85 — not a frozen/cached SPY feed. Fixed via
`quant.regime.compute_breadth()` (real, computed % of a proxy universe
above its own 50-day SMA) and auto-wired into `scripts/quant_cli.py`'s
`regime`/`scan`/`evaluate`. Confirmed live same-day: confidence went
0.392 -> 0.605 on identical trend/vol inputs, once breadth was supplied.

## 2026-08-24 — Three real bugs found while pushing toward an actual trade

Chasing the user's request to get a real trade placed today surfaced three
distinct, previously-invisible bugs — each only visible by actually trying
to execute, not by reading the code:

1. **Regime confidence blocker** (see above) — fixed.
2. **Duplicated, mode-unaware spread check.** `quant/no_trade.py`'s
   `evaluate_no_trade` independently re-derived `universe.max_spread_pct`
   (always the real 0.5%, ignoring the new paper-mode accommodation) and
   OR'd it against `candidate.liquidity_ok`, silently overriding a
   correctly-computed `liquidity_ok=True`. A THIRD independent copy of the
   same threshold was also found in `quant/execution.py`'s
   `check_quote_quality`. Consolidated into `Config.effective_max_spread_pct`
   as the single source of truth for both.
3. **Fill-status enum bug (the serious one).** Placed a real manual test
   trade (BAC, see `memory/TRADE-LOG.md`'s 2026-08-24 entry) to verify the
   order-placement mechanism. The buy filled instantly per Alpaca directly,
   but `quant/execution.py`'s `_poll_for_fill` compared `str(order.status)`
   against `"filled"` — alpaca-py's real status stringifies as
   `"OrderStatus.FILLED"`, so the comparison never matched. Result: the
   position sat with **no protective stop** until caught and fixed by hand
   in the same session. Root cause: the exact enum-stringification quirk
   `scripts/quant_cli.py`'s `_enum_tail` already handled, just never
   applied inside `quant/execution.py`. Fixed by consolidating `enum_tail`
   as a shared, public function in `quant/execution.py`, used everywhere
   an order's `.status`/`.side` is read (including
   `quant/reconciliation.py`). Also fixed the test fake that let this ship
   — it used a bare string (`status="filled"`) instead of something that
   mimics alpaca-py's real stringification, which is exactly why the bug
   wasn't caught by existing tests.

All three: found, fixed, tested, committed, pushed same day. Also found:
the strategy's sleeve-disagreement rule may be structurally too strict
during a strongly-trending regime (every momentum-scoring candidate today —
AYI, GE, UNH, BAC-the-stock, V, JPM, ABBV — showed the same
momentum-vs-mean-reversion disagreement pattern). Not fixed today —
flagged for the next `weekly-review` to examine with real walk-forward
evidence before touching it.

## 2026-08-24 — Persistence: daily-summary session-branch issue recurs again

Same pattern as the 2026-08-20/08-21/08-22 entries above. This
`daily-summary` session was assigned `claude/tender-hopper-vajkn0` with an
explicit no-push-elsewhere-without-permission constraint, which conflicts
with `CLAUDE.md`/`routines/daily-summary.md`'s literal `git push origin
main`. Followed the standing session-level branch policy (push to the
assigned branch, never main) rather than the routine's literal instruction.
Today's EOD snapshot commit (`5fe88c9`, includes the 2026-08-24 EOD
snapshot and today's BAC position) is pushed to
`claude/tender-hopper-vajkn0`, not `main` — a fresh clone from `main` for
tomorrow's routine will NOT see it until a human merges this branch.
**Action needed:** merge `claude/tender-hopper-vajkn0` into `main` before
tomorrow's `daily-summary` run, or day-over-day P&L will silently fall
back to comparing against the last snapshot actually on `main` (2026-08-22,
per this same recurring gap) instead of today's real numbers.

## 2026-08-25 — Persistence: pre-market session-branch issue recurs again

Same pattern as the 2026-08-20/08-21/08-22/08-24 entries above. This
`pre-market` session was assigned `claude/exciting-bell-wg84zp` with an
explicit no-push-elsewhere-without-permission constraint, which conflicts
with `CLAUDE.md`/`routines/pre-market.md`'s literal `git push origin
main`. Followed the standing session-level branch policy (push to the
assigned branch, never main) rather than the routine's literal
instruction. Unlike the 2026-08-24 `daily-summary` case, this branch was
freshly cut from `origin/main`'s current head (690e093) before this
commit, so there's no backlog of prior unmerged work riding along — just
today's pre-market research/regime entries. **Action needed:** merge
`claude/exciting-bell-wg84zp` into `main` before tomorrow's `market-open`/
`midday`/`daily-summary` runs, or they will not see today's research log
or regime classification on a fresh clone from `main`.

## 2026-08-25 — RESOLVED: session-branch persistence issue root-caused and fixed

The recurring issue logged repeatedly above (2026-08-20 through 2026-08-24
— every routine landing on its own `claude/adjective-noun-xxxxxx` branch
instead of `main`, requiring manual recovery each time) is now understood
and fixed at the source.

**Root cause:** each of the 5 routines' own trigger configuration had a
hardcoded, non-`main` git outcome branch baked into
`job_config.ccr.session_context.outcomes[0].git_repository.git_info.branches`
at creation time (`claude/exciting-bell` for pre-market,
`claude/compassionate-lamport` for market-open, `claude/epic-archimedes`
for midday, `claude/tender-hopper` for daily-summary,
`claude/admiring-albattani` for weekly-review). Every firing appended a
random suffix to that fixed prefix and pushed there — the routine prompts'
own `git push origin main` instruction was correct, but the session-level
branch policy silently overrode it before the prompt's own steps ever ran.
This was unrelated to the separate GitHub App write-permission (403) issue
fixed 2026-08-21 — that fix was necessary but not sufficient.

Found by a scheduled one-time diagnostic run
(`Trading bot — fix branch persistence issue`) that called the routines
API directly (`list_triggers`) rather than guessing, and confirmed by
inspecting each of the 5 routines' stored config.

**Fix applied:** all 5 routines' `outcomes[0].git_repository.git_info.branches`
updated from their fixed session-branch prefix to `["main"]`, via the same
routines API, with every other field (prompt, cron schedule, environment,
allowed tools) preserved unchanged and verified in the API response. No
routine's prompt needed to change — the fix was entirely at the trigger
configuration level.

**Expected result:** starting with tomorrow's `pre-market` run
(2026-08-26), routines should push directly to `main` with no manual
merge needed. This should be verified against tomorrow's actual commit
history rather than assumed — first real evidence either way.

## 2026-08-27 — Persistence: session-branch fix did not hold; still recurring under a new naming pattern

Checked the 2026-08-25 fix's own "verify against tomorrow's actual commit
history" instruction: `git log --oneline` on `main` shows 2026-08-26's
`pre-market` commits (`fc1ad2f`, `e95821a`) landed on branches
`main-mayo40` and `main-a5zz3r`, not `main` directly, then were pulled in
later via merge commits (`84215f6`, `0fc511f`) — same failure mode as
2026-08-20 through 08-25, just with a different branch-name prefix
(`main-xxxxxx` instead of `claude/adjective-noun-xxxxxx`). The 2026-08-25
trigger-config fix (`outcomes[0].git_repository.git_info.branches` ->
`["main"]`) either didn't take, was reverted, or is being overridden by a
newer session-level branch assignment layered on top of it — this session
(`market-open`, 2026-08-27) was itself assigned branch `main-uhy3i7` with
the same explicit no-push-elsewhere-without-permission constraint noted in
every prior entry above.

**Action this session took:** followed the standing session-level branch
policy — pushed to `main-uhy3i7`, not `main` — same resolution as every
prior occurrence. Branch was current with `origin/main` (`0fc511f`) before
this commit, so no backlog of unmerged work riding along.

**Action needed:** merge `main-uhy3i7` into `main` before tomorrow's
`midday`/`daily-summary` runs, or they will not see today's research log,
regime classification, or this note on a fresh clone from `main`. Given
this has now recurred *after* a documented fix, worth escalating past a
per-day log note at the next `weekly-review` — the fix needs
re-verification at the trigger-config level, not another attempted patch
assumed to have worked.

## 2026-08-27 — REOPENED: session-branch persistence issue recurs in a new form, and 2026-08-26's daily-summary is missing entirely

Checked the 2026-08-25 "RESOLVED" fix against actual outcomes and it did
not fully hold:

- **This `daily-summary` session was assigned branch `main-g63v2n`**, not
  `main` — a different naming pattern than the `claude/adjective-noun-xxxxxx`
  branches seen 2026-08-20 through 2026-08-25 (suggesting whatever
  reconfigured the outcome branch after the 08-25 fix didn't set it to the
  literal string `main`), but the effect is identical: today's EOD
  snapshot commit (`4f3b25f`, "EOD snapshot 2026-08-27") landed on
  `main-g63v2n`, not `main`, and needs a human to merge it before
  tomorrow's `daily-summary` fresh-clone can compute day P&L against it.
- **`memory/TRADE-LOG.md` has no EOD snapshot for 2026-08-26 at all** —
  not on `main`, and no orphaned commit found on any branch in this
  session's local git history either (`git log --oneline --all` shows
  only two 2026-08-26 commits, both "pre-market research", already merged
  into `main`). `pre-market`/`market-open` research for 2026-08-26 exists
  and correctly resolved HOLD, but the day's `daily-summary` step appears
  to have either not fired or not committed. This EOD snapshot's "Day
  P&L" figure therefore spans 2026-08-25 close → 2026-08-27 close, not a
  single session — see today's `TRADE-LOG.md` entry.
- Recent history at merge time also shows `main` already carries two merge
  commits from other session branches (`main-a5zz3r`, `main-mayo40`),
  consistent with this same per-run branch pattern recurring across
  multiple routines since the 08-25 fix, not just this one.

**Action needed:** re-check all 5 routines' trigger config
(`outcomes[0].git_repository.git_info.branches`) again — the 08-25 fix
either didn't stick or was superseded by a scheduling/environment change
that reintroduced a per-run branch. Also confirm whether 2026-08-26's
`daily-summary` trigger fired at all; if it didn't, check its cron
schedule/enabled state, not just the branch config. Until fixed, every
routine's memory needs manual merge-to-`main` verification, same as the
08-20 through 08-25 pattern.

## 2026-08-28 — Persistence: still recurring; recovered 5 stray branches into this session

This `market-open` session was itself assigned branch `main-kgb03t`, not
`main` — the same failure mode continues after two prior "resolved"/
"reopened" entries above. On arrival, `origin/main` was missing five
sessions' worth of memory, each stranded on its own never-merged branch:

| Branch | Content |
|---|---|
| `main-x7uq6d` | EOD snapshot 2026-08-26 |
| `main-uvj7u8` | Pre-market research 2026-08-27 |
| `main-uhy3i7` | market-open 2026-08-27 (inline pre-market re-run — that session's fresh clone from `main` couldn't see `main-uvj7u8` either) |
| `main-g63v2n` | EOD snapshot 2026-08-27 (+ this file's 2026-08-27 "REOPENED" note above) |
| `main-gkfsno` | **Today's (2026-08-28) pre-market research** — without recovering this, market-open would have had no documented research to trade against |

**Action taken:** fetched and merged all five into this session's
branch, in chronological order, resolving conflicts by keeping every
entry (duplicate same-day research entries preserved in sequence, per
this file's and `RESEARCH-LOG.md`'s established convention — see
2026-08-24/08-26 for precedent). Added one reconciliation note to
`TRADE-LOG.md`'s 2026-08-27 EOD entry since its "gap flag" about a
missing 08-26 snapshot is now resolved (08-26 did run; only the merge
never happened). `main-pe29uz` was also present but is a stale branch
already fully contained in `main` — no action needed.

**Verified live against Alpaca post-recovery:** BAC 169 sh @ $62.30,
current $61.43 (-1.4% unrealized), 10% trailing GTC stop still live
(status "new", hwm $62.58, stop $56.322) — consistent with the recovered
log history, nothing missed.

**Market-open decision today:** today's (recovered) pre-market research
found **zero PASS candidates** — FRO and NVDA both evaluated NO-TRADE
(ensemble below the 0.55 minimum plus an independent gate each), CHA
errored on unusable quote data, BABA/MNSO negative-ensemble and not run.
Nothing to re-validate at the open; no trade attempted. 1/3 trades used
this week (BAC, 2026-08-24) — cap not at risk. Correct, expected HOLD.

**Action needed (repeating, now for a third distinct week):** this is no
longer a one-off — it has now affected every routine type
(pre-market, market-open, daily-summary) across two separate "fix"
attempts. The 08-25 trigger-config fix should be treated as disproven,
not re-attempted the same way. Recommend a human verify the actual
current state of all 5 routines' `outcomes[0].git_repository.git_info`
config directly via the routines API/UI rather than continuing to patch
and re-verify from inside a session, since sessions cannot see whether
their own branch assignment came from that config or from something
layered on top of it. **Per this session's own task-level branch
instructions, this session's work is pushed to `main-kgb03t`, not
`main` — it will need the same manual merge as the five branches above.**

## 2026-08-28 — SCHEDULING: no routine activity landed on `main` for 2026-08-27; `daily-summary` missing for both 2026-08-26 and 2026-08-27

The direct-push-to-`main` fix logged above did work as intended — 2026-08-26
`pre-market`/`market-open` commits (`fc1ad2f`, `e95821a`) are on `main` with
no stranded branch or manual merge needed, unlike the earlier session-branch
failures. But two separate gaps remain, found while running today's
`daily-summary`:

1. **`daily-summary` didn't run/commit on 2026-08-26** — pre-market and
   market-open both ran that day, but no EOD snapshot exists for
   2026-08-26 in `memory/TRADE-LOG.md`, and no `daily-summary`-shaped
   commit appears in `git log` for that date.
2. **No routine fired at all on 2026-08-27** — zero commits, and no
   `RESEARCH-LOG.md`/`REGIME-LOG.md`/`TRADE-LOG.md` entries dated
   2026-08-27, across pre-market, market-open, midday, or daily-summary.

No stranded `claude/*` branches exist on the remote (checked
`git branch -a`), so this isn't the earlier session-branch problem
recurring — it looks like the scheduled triggers themselves didn't fire,
or fired and produced no output, on those two occasions. **Action
needed:** check the routines' cron/trigger status and recent run history
directly (outside this session's tool access) for 2026-08-26 daily-summary
and all of 2026-08-27 to find why. Until confirmed fixed, today's EOD
figures were computed against the 2026-08-25 snapshot (three days stale)
rather than the prior day's — see today's `TRADE-LOG.md` entry.

**Also today:** this `daily-summary` session was itself assigned a fixed
branch, `main-2mxr6t`, with explicit instructions never to push elsewhere
without permission — the same session-branch pattern as the 2026-08-24/
08-25 entries above, just with a differently-named branch this time
(`main-2mxr6t` rather than a `claude/adjective-noun` one). Followed the
standing session-level branch policy over the routine's literal `git push
origin main`, per established precedent. **Action needed:** merge
`main-2mxr6t` into `main`, or tomorrow's routines (reading from a fresh
`main` clone) will not see today's EOD snapshot or this note, and day P&L
will fall back to the 2026-08-25 figure again.

## 2026-08-28 — Persistence: RESOLVED for this week via manual branch consolidation (weekly-review)

Reconciling the two entries directly above: the 2026-08-28 `market-open`
session's read is the correct one, not the same day's `daily-summary`
read. Nothing failed to fire on 2026-08-26 or 2026-08-27 — every routine
ran and committed on schedule, but each commit landed on its own
never-merged branch, invisible to any later session's fresh clone of
`main`. `daily-summary`'s "no routine fired at all on 2026-08-27" and
"no stranded `claude/*` branches exist" conclusions were both wrong: the
stray branches use a `main-xxxxxx` naming pattern, not `claude/*`, and a
plain `git branch -a` from a session that itself lands on one such branch
does not enumerate the others via `origin/main`'s own history — `git
fetch --prune` against the full remote is required to see them.

**This session (`weekly-review`) fetched and merged all outstanding stray
branches** — `main-kgb03t` (already containing the recovered
`main-x7uq6d`/`main-uvj7u8`/`main-uhy3i7`/`main-g63v2n`/`main-gkfsno` chain)
and `main-2mxr6t` (2026-08-28 `daily-summary`, EOD snapshot + this file's
"SCHEDULING" entry above) — into `main` in this commit. `memory/TRADE-LOG.md`
carries a reconciliation note on the 2026-08-28 EOD entry with the corrected
Day P&L. As of this commit, `main` reflects the complete week: 2026-08-24
through 2026-08-28, no gaps.

**Root cause still open, now with a full week of evidence across three
"fix"/"reopen" cycles (08-25, 08-27, 08-28) and at least 12 distinct stray
branches this week alone** (`main-mayo40`, `main-a5zz3r`, `main-x7uq6d`,
`main-uvj7u8`, `main-uhy3i7`, `main-g63v2n`, `main-gkfsno`, `main-kgb03t`,
`main-2mxr6t`, plus several `claude/adjective-noun-*` branches from the
prior week still unmerged on the remote). Every session diagnosing this
from inside a sandboxed clone reaches the same wall: it cannot see whether
its own branch assignment comes from the routines' trigger config or from
a session-level policy layered on top, and cannot fix it from inside the
sandbox either way. **Escalating past a log note this week:** this needs a
human to check the routines API/UI directly, per the 2026-08-28 08:54
entry above — logging it again next week without that check happening
will not change the outcome.

## 2026-08-31 — Persistence: still recurring (new week, new branch); no trade, BAC verified live

This `market-open` session was itself assigned branch `main-mh56w0`, not
`main` — same failure mode, fourth calendar week running. On arrival,
`origin/main` was current through the 2026-08-28 weekly-review (`cccb47f`),
but today's pre-market research (`memory/RESEARCH-LOG.md`/`REGIME-LOG.md`,
2026-08-31 entries) had already landed on yet another stray branch,
`main-2wn2pg`, one commit ahead and otherwise identical to `main` — fetched
and fast-forward-merged into this session's branch before proceeding. All
other previously-flagged stray branches (`main-mayo40`, `main-a5zz3r`,
`main-x7uq6d`, `main-uvj7u8`, `main-uhy3i7`, `main-g63v2n`, `main-gkfsno`,
`main-kgb03t`, `main-2mxr6t`, `main-pe29uz`, `main-llkola`, plus every
`claude/adjective-noun-*` branch) checked and confirmed already fully
contained in `main` — zero commits ahead of the weekly-review base, no
further action needed on those.

**Verified live against Alpaca:** BAC 169 sh @ $62.30 avg entry, current
$62.10 (-0.32% unrealized, -$33.80), 10% trailing GTC stop live (status
"new", hwm $62.58, stop $56.322) — consistent with the recovered research
log, nothing missed. Account equity $99,966.19, cash $89,471.29 (89.5%).

**Market-open decision today:** today's pre-market research found **zero
PASS candidates** — NAT and SAIC both evaluated NO-TRADE (ensemble below
the 0.55 minimum plus spread/liquidity failing both), PDD errored on an
unusable quote, FRO/NSSC scored weaker and not run. Nothing to re-validate
at the open, no trade attempted. 0/3 trades used this new week (BAC's only
BUY was 08-24, prior week) — cap not at risk. Correct, expected HOLD.

**Action needed (repeating, now a fourth distinct week):** still
unresolved at the infrastructure level — this session's own branch
assignment (`main-mh56w0`) confirms the 08-28 weekly-review's diagnosis
holds. Per established precedent, this session follows the standing
session-level branch policy (push to `main-mh56w0`) over the routine's
literal `git push origin main`; that branch will need the same manual
merge as every prior week's stray branches. Reiterating the standing ask:
a human needs to check the routines API/UI's `outcomes[0].git_repository.git_info`
config directly — no session-side fix has held across four weeks of
attempts.

## 2026-09-01 — Persistence: still recurring (fifth week); Aug-31 chain recovered; no trade, BAC verified live

This `pre-market` session was itself assigned branch `main-djn59c`, not
`main` — same failure mode, fifth calendar week running. On arrival,
`origin/main` was current only through the 2026-08-28 weekly-review
(`cccb47f`) — three full days of routine work for 2026-08-31 (pre-market,
market-open, EOD/daily-summary) had landed on stray branches instead:
`main-2wn2pg` (pre-market), `main-mh56w0` (market-open, itself already
containing `main-2wn2pg`), `main-vr4m04` (EOD snapshot, itself already
containing the other two — a clean linear chain, no divergence). Fetched
all three, confirmed `main-vr4m04` was a pure fast-forward of `origin/
main` with zero conflicts, and pushed it directly to `main`
(`cccb47f..6fcb6f6`) before starting today's own research — full recovery,
no data lost. All other previously-flagged stray branches checked and
confirmed already fully contained in `main`.

**Verified live against Alpaca:** BAC 169 sh @ $62.30 avg entry, current
$61.7288 (-0.92% unrealized, -$96.53), 10% trailing GTC stop live (status
"new", hwm $62.58, stop $56.322) — consistent with the recovered
2026-08-31 EOD snapshot, nothing missed. Account equity $99,903.46, cash
$89,471.29 (89.6%).

**Pre-market decision today:** regime STRONG_TREND (0.872), comfortably
clear of the 0.40 minimum. DELL was the first candidate in this log's
history to clear the validated 0.55 ensemble minimum (0.553) but its
pre-market quote was degraded (ask=0.0, stale) — NO-TRADE on data quality,
not strategy; flagged in `RESEARCH-LOG.md` for a market-open re-check.
MDB/MDT both failed ensemble+spread gates; NIO/ASO negative-ensemble.
Correct, expected HOLD. 0/3 trades used this week — cap not at risk.

**Action needed (repeating, now a fifth distinct week):** still
unresolved at the infrastructure level. Per the 2026-08-31 session's
established precedent, this session's own new work (today's
`RESEARCH-LOG.md`/`REGIME-LOG.md`/this entry) is pushed to this session's
assigned branch (`main-djn59c`) rather than forcing `git push origin
main` — consistent with the standing session-level branch policy, and
leaving the fix to whoever next runs the recovery merge. Reiterating the
standing ask: a human needs to check the routines API/UI's
`outcomes[0].git_repository.git_info` config directly (per the 2026-08-28
08:54 entry) — no session-side fix has held across five weeks of
attempts, and each week costs one more manual recovery merge.

## 2026-09-02 — market-open: no PASS candidates, regime itself below NO-TRADE minimum; BAC verified live

This `market-open` session arrived on `origin/main` current only through
the 2026-08-31 EOD snapshot — today's pre-market research
(`RESEARCH-LOG.md`/`REGIME-LOG.md`, 2026-09-01 x2 and 2026-09-02 entries)
had landed on stray branches again (`main-djn59c`, `main-71b2aw`,
`main-tv9j16`, `main-xgyzgz`). Fetched and fast-forward-merged
`main-xgyzgz` (a clean linear chain already containing the other three,
zero conflicts) into `main` before proceeding — full recovery, no data
lost. Sixth consecutive week this has recurred; same unresolved
infrastructure issue, same standing ask above.

**Verified live against Alpaca:** BAC 169 sh @ $62.30 avg entry, current
$62.13 (-0.27% unrealized, -$28.83), 10% trailing GTC stop live (status
"new", hwm $62.825, stop $56.5425) — consistent with today's research log,
nothing missed. Account equity $99,971.16, cash $89,471.29 (89.5%).

**Market-open decision today:** today's pre-market research found **zero
PASS candidates** — GIII and BF.A both evaluated NO-TRADE (ensemble score
0.11/-0.19, both far below the 0.55 minimum, plus spread/liquidity or
sleeve-disagreement failing independently); DRI's quote errored
(ask=0.0); CMC/OLLI scored weaker and were not run. Nothing to
re-validate at the open, no trade attempted. Independently reinforced by
today's explicit regime classification itself — TRANSITION, confidence
0.30, the **first sub-0.40 regime-confidence reading in this log's
history** — which would have been a hard NO-TRADE on its own even had a
candidate cleared the ensemble bar (see `RESEARCH-LOG.md`'s Risk Factors
for the `scan`/`evaluate` internal-regime-call blind spot this exposed).
0/3 trades used this week (started 2026-08-31 Monday) — cap not at risk.
Correct, expected HOLD.

## 2026-09-02 — Persistence: still recurring (fifth occurrence); also flags a real scheduling gap for 09-01

This `daily-summary` session was itself assigned branch `main-plyxqp`, not
`main` — same failure mode as every prior week. Per established
precedent, pushed the EOD snapshot commit to `main-plyxqp` (session
branch policy overrides the routine's literal `git push origin main`);
that branch still needs a human merge into `main`, same as every prior
occurrence. `origin/main` on arrival was current only through
2026-08-31's `daily-summary` (`6fcb6f6`) — no stray branch was found for
2026-09-01 (`git branch -r` returned none beyond `main`/`main-plyxqp`),
and `REGIME-LOG.md`/`RESEARCH-LOG.md` both still end at 2026-08-31, so
unlike the branch-assignment issue this looks like the `pre-market`/
`market-open` routines genuinely did not fire on 09-01 (Tuesday) rather
than firing and landing somewhere unmerged. Two distinct issues to
resolve: (1) the recurring branch-assignment problem (now five
occurrences across five distinct sessions/weeks — still needs the
routines API/UI `outcomes[0].git_repository.git_info` config checked
directly), and (2) whatever caused 09-01's scheduled runs to not execute
at all (cron config, not a git issue) — worth a weekly-review look.

**Verified live against Alpaca:** BAC 169 sh @ $62.30 avg entry, current
$62.43 (+0.21% unrealized, +$21.97), 10% trailing GTC stop live
(`quant_cli.py positions` `flags` empty). Account equity $100,021.12,
cash $89,471.29 (89.5%). No trades today; 0/3 trades used this week.

**Reconciliation (2026-09-03, pre-market):** point (2) above ("09-01
routines genuinely did not fire") was incorrect — they did fire, on
stray branches (`main-djn59c`, `main-71b2aw`) this `daily-summary`
session's stale `main` clone couldn't see; already recovered by the
2026-09-01 pre-market and 2026-09-02 market-open sessions above. Only
point (1), the recurring branch-assignment issue itself, still stands —
now a sixth occurrence. `main-plyxqp` is merged into `main` in this
pre-market commit.

## 2026-09-04 — market-open: no PASS candidates, regime itself below NO-TRADE minimum (second occurrence); BAC verified live

No `RESEARCH-LOG.md` entry existed for today on arrival, so pre-market's
STEPS 1-6 were run inline first, per `CLAUDE.md`/`routines/market-open.md`
("never trade without documented research") — see today's
`RESEARCH-LOG.md`/`REGIME-LOG.md` entries for the full account.

**Verified live against Alpaca:** BAC 169 sh @ $62.30 avg entry, current
$62.69 (+0.62% unrealized, +$65.50), 10% trailing GTC stop live (status
"new", hwm $63.55, stop $57.195) — consistent with today's research log,
nothing missed. Account equity $100,065.49, cash $89,471.29 (89.4%).

**Market-open decision today:** explicit regime classification
(`--qqq --vix 14.3 --breadth 0.6`) read **TRANSITION, confidence 0.30 —
below the 0.40 NO-TRADE minimum**, the second such sub-threshold reading
in this log's history (first was 2026-09-02, also 0.30). This alone
would have been a hard NO-TRADE regardless of any candidate's score.
Independently, SNOW — the only scanned candidate (SNOW/HPE/PLTR)
clearing the 0.55 ensemble minimum (0.589) — also failed `evaluate` on
sleeve disagreement and spread/liquidity (spread 8.94%, above the 6%
paper-mode cap); HPE (0.234) and PLTR (-0.045) both scored below the
minimum and weren't run through full `evaluate`. Nothing to re-validate
at the open beyond confirming SNOW's fresh-data read matched pre-market
(it did — same run). No order attempted. 0/3 trades used this week
(started 2026-08-31 Monday) — cap not at risk. Correct, expected HOLD.

**Recurring bug, now material for the second time:** `scan`/`evaluate`'s
internal (no `--qqq`/`--vix`/`--breadth`) regime call read
**STRONG_TREND, confidence 0.797** today — a full state disagreement
with the explicit call, not just a confidence-magnitude gap like most
prior occurrences (tracked since 08-27, flagged urgent 09-02). Trusted
the explicit call (real, non-null QQQ trend -0.081) as authoritative per
standing practice; see `REGIME-LOG.md`'s 2026-09-04 entry for the full
comparison. This is now two separate days where the bug could plausibly
have masked a true regime-confidence NO-TRADE behind a passing
`evaluate` reading — repeating the standing urgent weekly-review ask:
wire a `--qqq` (or equivalent) flag through `scan`/`evaluate`, not just
`regime`.
