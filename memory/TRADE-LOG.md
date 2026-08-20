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
