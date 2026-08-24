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
