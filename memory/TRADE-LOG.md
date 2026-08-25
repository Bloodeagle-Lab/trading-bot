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
