# Trade Log

Every trade (entry + exit) and every EOD snapshot, appended here in
chronological order. Never edit or delete a past entry — this is an
append-only audit trail. `memory/PROJECT-CONTEXT.md`'s "Key Files" note:
tail this file for currently-open positions, their entries, and their
stops before doing anything else.

## Entry format (market-open / ad-hoc trade)

```
### YYYY-MM-DD — BUY TICKER
- Shares: N @ $entry (order id: ...)
- Stop: $stop (10% trailing GTC, order id: ...) [or: fixed stop — trailing
  rejected, reason: ...] [or: PDT-blocked, queued for tomorrow AM]
- Target: $target (R:R X:1)
- Catalyst: <from today's RESEARCH-LOG.md>
- Regime at entry: STATE (confidence X.XX)
- Ensemble score: X.XX | ML probability: X.XX
- Risk budget: X.XX% of equity ($X risked)
```

## Entry format (close / stop tightened)

```
### YYYY-MM-DD — SELL TICKER
- Shares: N @ $exit (order id: ...)
- Realized P&L: ±$X (±X.X%, X.XR)
- Reason: <-7% stop hit | thesis broken: ... | sector exit: 2 failed trades in SECTOR>
```

## Entry format (EOD snapshot, appended every daily-summary run)

```
### YYYY-MM-DD — EOD Snapshot (Day N, Weekday)
**Portfolio:** $X | **Cash:** $X (X%) | **Day P&L:** ±$X (±X%) | **Phase P&L:** ±$X (±X%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|

**Notes:** one-paragraph plain-English summary.
```

---

## Day 0 — EOD Snapshot (real baseline, first live pre-market run)

**Portfolio:** $100,000.00 | **Cash:** $100,000.00 (100%) | **Day P&L:** $0 | **Phase P&L:** $0

Real baseline as of 2026-08-20, replacing the pre-launch $10,000
placeholder — confirmed via `bash scripts/alpaca.sh account` against paper
account PA3M8YH661WT. No positions, no open orders. This is the actual
figure every later day-over-day and phase P&L calculation in this file is
measured against.

*Note: this entry was reconstructed locally from the first cloud
`pre-market` routine run's reported summary, not committed by the routine
itself — that run's commit was stranded on an ephemeral session branch and
lost when the workspace was reclaimed, because the Claude GitHub App does
not yet have write access to this repo (`git push` returned 403). See
`memory/RISK-LOG.md` for that finding. This does not happen for local
runs or for this recovery commit, both of which use working git
credentials.*

## 2026-08-21 — EOD Snapshot (Day 1, Friday)

---

### 2026-08-22 — EOD Snapshot (Day 2, Saturday)

**Portfolio:** $100,000.00 | **Cash:** $100,000.00 (100%) | **Day P&L:** $0.00 (0.00%) | **Phase P&L:** $0.00 (0.00%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| (none) | | | | | | |

**Notes:** No open positions and no trades today — regime confidence
(0.392) stayed below the 0.40 minimum for a third straight run (per
`REGIME-LOG.md`), and the day's earnings-driven candidates were either
negative-ensemble or failed the evaluate gates (per `RESEARCH-LOG.md`),
so no order was placed. Equity flat at the $100,000 baseline, zero day
and phase P&L. Zero trades this week against the cap of 3. No stop-flag
issues (`positions` returned an empty `flags` list). *Persistence flag:
this session was assigned working branch `claude/brave-rubin-g81u3p`
with an explicit no-push-elsewhere-without-permission constraint, the
same failure mode already logged in `memory/RISK-LOG.md` for
2026-08-20 — this commit is pushed there, not to `main`, and needs a
human to merge it before tomorrow's `daily-summary` run can find
today's snapshot for day-over-day P&L.*

| — | — | — | — | — | — | — |

**Notes:** Market closed (Saturday) — `quant_cli.py positions` returns the
Friday close carried forward: equity flat at $100,000.00, no open
positions, no flags. Zero trades since Day 0 baseline (2026-08-20); regime
has missed the 0.40 NO-TRADE confidence minimum four sessions running
(2026-08-20 x2, 08-21, 08-22), always on the same HIGH_VOL-vs-STRONG_TREND
margin, so the pipeline has correctly stayed in NO-TRADE the whole phase.
This is the first EOD snapshot committed by the `daily-summary` routine
itself — prior days have no logged snapshot (no committed daily-summary
run found in history), so day-over-day P&L here is measured against the
Day 0 baseline rather than a prior daily-summary entry. Trades this week:
0/3.

### 2026-08-23 — EOD Snapshot (Day 3, Sunday)

**Portfolio:** $100,000.00 | **Cash:** $100,000.00 (100%) | **Day P&L:** $0 (0.0%) | **Phase P&L:** $0 (0.0%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|

**Notes:** No open positions, no trades today, no flags from
`quant_cli.py positions`. Equity unchanged from the Day 0 baseline —
today falls on a weekend (market closed since Friday's close), so this
snapshot reflects the account's flat holding state rather than fresh
market action. Pipeline continues to correctly NO-TRADE (regime
confidence has missed the 0.40 minimum four sessions running per
`memory/REGIME-LOG.md`, and no champion ML model exists yet). Zero
trades this week against the cap of 3.

### 2026-08-24 — BUY BAC — MANUAL MECHANISM TEST, NOT A STRATEGY SIGNAL

- Shares: 169 @ $62.30 (buy order id: 3e1dcfc2-4114-4b8d-8fc1-242ec62ae878)
- Stop: 10% trailing GTC, ~$56.06 initial (stop order id:
  85214135-e5a1-4df2-abc4-1cd4cd946e68) — placed manually via direct
  TradingClient call after the automated stop-placement path failed (see
  below), not by `execute`'s own `_place_protective_stop`.
- Target: none set — not a scored setup, no thesis to size a target against.
- Catalyst: **none — BAC was never scored by `evaluate`/`no_trade`.** Called
  `scripts/quant_cli.py execute` directly, deliberately bypassing the
  strategy-scoring gates (sleeve/ensemble/regime/ML), at the user's explicit
  request specifically to verify the order-placement mechanism works
  end-to-end, after today's actual top-scored candidate (AYI, ensemble
  0.598) was correctly blocked by real sleeve disagreement (extended
  technicals ahead of earnings — a legitimate NO-TRADE, not a bug). BAC was
  picked only for a genuinely tight spread (0.02%), to isolate the
  execution mechanism from today's separate data-quality findings.
- Regime at entry: STRONG_TREND (confidence 0.605 — post-fix, see
  `memory/REGIME-LOG.md`)
- Ensemble score: not computed (bypassed) | ML probability: not computed
  (no champion model)
- Risk budget: 0.3% of equity ($300 risked), sized via `quant.risk.size_position`
  the same way a real trade would be

**Bug found and fixed in the process:** `execute`'s automated stop-placement
never ran. The buy filled instantly (confirmed directly against Alpaca:
`filled_qty="169"`, `filled_avg_price="62.3"`), but
`quant/execution.py`'s `_poll_for_fill` compared `str(order.status)`
against `"filled"` — alpaca-py's real status stringifies as
`"OrderStatus.FILLED"`, so the comparison never matched, `filled_qty`
came back 0.0, and the position sat with **no protective stop** until
caught and fixed by hand within the same session (same enum-stringification
bug `scripts/quant_cli.py`'s `_enum_tail` already had a fix for, just not
applied inside `quant/execution.py`). Full fix, consolidated `enum_tail`
utility, and a realistic-enum test fake (the old bare-string fake is
exactly what let this ship) — see `memory/RISK-LOG.md` and the
2026-08-24 commits.

**Resolved (user, 2026-08-24):** leave it open. No manual close — it
follows the normal sell-side rules from here (`memory/TRADING-STRATEGY.md`:
-7% hard cut, tighten to 7%/5% trailing at +15%/+20%, thesis-break check)
via `midday`/`stops-check` like any other position, even though it has no
catalyst-driven thesis to break. `daily-summary`/`weekly-review` should
treat it as a normal open position, not exclude it as a "test."

### 2026-08-24 — EOD Snapshot (Day 4, Monday)

**Portfolio:** $100,032.96 | **Cash:** $89,471.30 (89.5%) | **Day P&L:** $32.96 (0.03%) | **Phase P&L:** $32.96 (0.03%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $62.495 | +0.31% | +$32.96 | trailing 10% |

**Notes:** One trade today — BAC, a manual mechanism test (not a
strategy signal; see entry above), filled at $62.30 with a 10% trailing
GTC stop now confirmed live (`quant_cli.py positions` `flags` empty, no
missing-stop issue). Day P&L computed against the 2026-08-23 EOD snapshot
($100,000.00); phase P&L against the Day 0 real baseline (also
$100,000.00, so the two figures match today). 1/3 trades used this week.
No new strategy-scored trades today — regime/scan/evaluate weren't run
as part of this EOD step; see `RESEARCH-LOG.md`/`REGIME-LOG.md` for
today's pre-market and market-open findings.

### 2026-08-25 — EOD Snapshot (Day 5, Tuesday)

**Portfolio:** $100,017.74 | **Cash:** $89,471.29 (89.5%) | **Day P&L:** -$15.22 (-0.02%) | **Phase P&L:** $17.74 (0.02%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $62.405 | -0.14% | +$17.75 | trailing 10% |

**Notes:** No new trades today; BAC (manual mechanism-test position from
2026-08-24) remains the only open position, still carrying its live 10%
trailing GTC stop (`quant_cli.py positions` `flags` empty). Day P&L
computed against the 2026-08-24 EOD snapshot ($100,032.96); phase P&L
against the Day 0 baseline ($100,000.00). Regime cleared the 0.40
NO-TRADE confidence minimum today for the first time in five sessions
(0.872, per `REGIME-LOG.md`), but the day's candidate scan still
resolved to HOLD — BMO failed on spread/liquidity, BNS's quote path
errored, and the rest scored weaker or negative (see `RESEARCH-LOG.md`).
No champion ML model exists yet, so every candidate still fails the
ML-evidence gate regardless of setup. 1/3 trades used this week (BAC,
2026-08-24).

### 2026-08-26 — EOD Snapshot (Day 6, Wednesday)

**Portfolio:** $100,018.58 | **Cash:** $89,471.29 (89.5%) | **Day P&L:** $0.84 (0.00%) | **Phase P&L:** $18.58 (0.02%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $62.41 | +0.18% | +$18.59 | trailing 10% |

**Notes:** No new trades today; BAC (manual mechanism-test position from
2026-08-24) remains the only open position, still carrying its live 10%
trailing GTC stop (`quant_cli.py positions` `flags` empty, no missing-stop
issue). Day P&L computed against the 2026-08-25 EOD snapshot
($100,017.74); phase P&L against the Day 0 baseline ($100,000.00).
Pre-market scan (SJM, BBWI) both failed the validated 0.55 ensemble-score
minimum outright, plus independent gates each (SJM: 10.20% spread; BBWI:
sleeve disagreement) — correctly resolved HOLD, no order placed or
staged. No champion ML model exists yet, so every candidate still fails
the ML-evidence gate regardless of setup. 1/3 trades used this week
(BAC, 2026-08-24), well under the cap of 3.

### 2026-08-27 — EOD Snapshot (Day 7, Thursday)

**Portfolio:** $99,846.20 | **Cash:** $89,471.29 (89.6%) | **Day P&L:** -$171.54 (-0.17%) | **Phase P&L:** -$153.80 (-0.15%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $61.39 | -1.63% | -$153.79 | trailing 10% |

**Notes:** No new trades today or on 2026-08-26; BAC (manual
mechanism-test position, 2026-08-24) remains the only open position,
stop live and confirmed (`quant_cli.py positions` `flags` empty). **Gap
flag:** no EOD snapshot exists in this file for 2026-08-26 — pre-market
and market-open both ran that day and correctly resolved to HOLD (see
`RESEARCH-LOG.md`/`REGIME-LOG.md`), but no `daily-summary` commit landed
on `main`, so "Day P&L" above actually spans two trading sessions
(2026-08-25 close → 2026-08-27 close), not one. Worth a weekly-review
check on whether that day's `daily-summary` ran at all. Phase P&L
computed against the Day 0 baseline ($100,000.00). 1/3 trades used this
week (BAC, 2026-08-24) — cap not at risk.

**Reconciliation (2026-08-28, market-open):** the 2026-08-26 EOD snapshot
above ("Gap flag") was not actually missing — it landed on stray branch
`main-x7uq6d` and is now recovered into this file (see the 2026-08-26
entry above). It did run and did commit; only the merge to `main` never
happened, same root cause as this file's other stray-branch recoveries.
Recomputed against the recovered 2026-08-26 close ($100,018.58), this
entry's real one-session Day P&L is -$172.38, not the -$171.54 stated
above (which was computed against 2026-08-25's close because 08-26 wasn't
visible yet) — a $0.84 difference, immaterial, left uncorrected above to
preserve the routine's actual output as run.

### 2026-08-28 — EOD Snapshot (Day 8, Friday)

**Portfolio:** $100,014.36 | **Cash:** $89,471.29 (89.5%) | **Day P&L:** -$3.38 (-0.00%) | **Phase P&L:** $14.36 (0.01%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $62.385 | +0.14% | +$14.37 | trailing 10% |

**Notes:** No trades today; BAC (manual mechanism-test position from
2026-08-24) remains the only open position, live 10% trailing GTC stop
confirmed (`quant_cli.py positions` `flags` empty). **Continuity gap:**
no `daily-summary` EOD snapshot was committed for 2026-08-26 or
2026-08-27, and no routine activity of any kind (pre-market/market-open/
midday/daily-summary) landed on `main` for 2026-08-27 — see
`memory/RISK-LOG.md` for the flagged gap. Day P&L above is therefore
computed against the last real snapshot, 2026-08-25 ($100,017.74), three
calendar days stale rather than one; phase P&L is against the Day 0 real
baseline ($100,000.00) and is unaffected. Regime/scan/evaluate weren't
run as part of this EOD step. 1/3 trades used this week (BAC, 2026-08-24),
unchanged.

**Reconciliation (2026-08-28, weekly-review):** the "continuity gap" flagged
above was a stray-branch problem, not a missed run — 2026-08-26's EOD
snapshot, 2026-08-27's pre-market/market-open/EOD, and 2026-08-28's own
pre-market/market-open all did run and commit, but each landed on a
different unmerged branch (`main-x7uq6d`, `main-uvj7u8`, `main-uhy3i7`,
`main-g63v2n`, `main-kgb03t`) that this daily-summary session's fresh
clone of `main` couldn't see; `market-open`'s 2026-08-28 run (`main-kgb03t`)
had already recovered all but this entry before this one ran in parallel
from an older base — see `memory/RISK-LOG.md` for the full account and
this file's 2026-08-27 entry for the same pattern one day earlier. All
branches are now merged into `main` in this weekly-review commit. Recomputed
against the recovered 2026-08-27 close ($99,846.20), this entry's real
one-session Day P&L is **+$168.16 (+0.17%)**, not the -$3.38 stated above
(which was computed against the stale 2026-08-25 close because 08-26/08-27
weren't visible yet) — left uncorrected above to preserve the routine's
actual output as run. Phase P&L ($14.36, vs the real Day 0 baseline) is
unaffected either way.

### 2026-08-31 — EOD Snapshot (Day 11, Monday)

**Portfolio:** $99,964.50 | **Cash:** $89,471.29 (89.5%) | **Day P&L:** -$49.86 (-0.05%) | **Phase P&L:** -$35.50 (-0.04%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $62.09 | -0.47% | -$35.49 | trailing 10% |

**Notes:** No trades today — pre-market found zero PASS candidates (NAT
and SAIC both NO-TRADE on ensemble-score/spread-liquidity failures, PDD
errored on an unusable quote, FRO/NSSC scored weaker and weren't run);
market-open correctly confirmed HOLD, nothing to re-validate. BAC
(manual mechanism-test position, 2026-08-24) remains the only open
position, live 10% trailing GTC stop confirmed (`quant_cli.py positions`
`flags` empty, no missing-stop issue). First trading day of a new week —
0/3 trades used, cap not at risk. Regime is STRONG_TREND, confidence
0.872, comfortably clear of the 0.40 NO-TRADE minimum. Day P&L computed
against the 2026-08-28 EOD snapshot ($100,014.36, last trading day —
market closed the weekend of 08-29/08-30); phase P&L against the Day 0
real baseline ($100,000.00). **Persistence note (recurring, fourth
week):** both today's pre-market and market-open runs landed on stray
branches (`main-2wn2pg`, `main-mh56w0`) instead of `main` — same
still-unresolved routine branch-assignment issue tracked in
`memory/RISK-LOG.md` since 2026-08-20. Recovered and merged into this
daily-summary's branch before this snapshot; see `RISK-LOG.md`'s
2026-08-31 entry for the full account.

### 2026-09-01 — EOD Snapshot (Day 12, Tuesday)

**Portfolio:** $99,939.15 | **Cash:** $89,471.29 (89.5%) | **Day P&L:** -$25.35 (-0.03%) | **Phase P&L:** -$60.85 (-0.06%)

| Ticker | Shares | Entry | Close | Day Chg | Unrealized P&L | Stop |
|---|---|---|---|---|---|---|
| BAC | 169 | $62.30 | $61.94 | -0.24% | -$60.84 | trailing 10% |

**Notes:** No trades today — two independent pre-market research runs
both landed on the same HOLD decision (see below). BAC (manual
mechanism-test position, 2026-08-24) remains the only open position, live
10% trailing GTC stop confirmed (`quant_cli.py positions` `flags` empty).
0/3 trades used this week (started 2026-08-31 Monday) — cap not at risk.
Regime is STRONG_TREND, confidence 0.872, comfortably clear of the 0.40
NO-TRADE minimum. Day P&L computed against the 2026-08-31 EOD snapshot
($99,964.50); phase P&L against the Day 0 real baseline ($100,000.00).
**Persistence note (recurring, fifth week):** this session's own branch
started stale — `origin/main` was current only through 2026-08-31's EOD —
because today's scheduled pre-market (11:37 UTC) and market-open's inline
re-run of pre-market (13:51 UTC, market-open couldn't see the 11:37 run
either, same stale-`main` cause) both landed on separate stray branches
(`main-djn59c`, `main-71b2aw`) instead of `main`. Recovered and merged
both into this daily-summary's branch before this snapshot — one real
conflict (both sessions appended a `## 2026-09-01` section to the same
spot in `REGIME-LOG.md`/`RESEARCH-LOG.md`), resolved by keeping both
entries under distinguishing timestamped headers rather than discarding
either. Both independently scored DELL/MDB/MDT and MRVL/PLTR/CVX/XOM/HAL
respectively and reached the same HOLD; see `RESEARCH-LOG.md` and
`RISK-LOG.md` for the full account. Still unresolved at the
infrastructure level — same standing ask as prior weeks.
