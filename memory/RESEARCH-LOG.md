# Research Log

One dated entry per trading day, written by the `pre-market` routine (and
occasionally an intraday addendum from `midday`). Read today's entry before
`market-open` places anything — never trade without documented research.

## Entry format

```
## YYYY-MM-DD — Pre-market Research

### Account
- Equity: $X | Cash: $X | Buying power: $X | Daytrade count: N/4

### Market Context
- Regime: STATE (confidence X.XX) — see memory/REGIME-LOG.md for the full record
- WTI / Brent:
- S&P 500 futures / VIX:
- Today's catalysts:
- Earnings before open:
- Economic calendar:
- Sector momentum:

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|

### Trade Ideas
1. TICKER — catalyst, entry $X, stop $X, target $X, R:R X:1, ensemble X.XX, ML prob X.XX
2. ...

### NO-TRADE Candidates
- TICKER — reason: <no_trade.py's reasons list, verbatim>

### Risk Factors
- ...

### Decision
TRADE or HOLD (default HOLD — patience beats activity; a NO-TRADE day is a
valid, measured outcome, not a gap in this log)
```

### Afternoon addendum format (midday, only when something moved sharply)

```
### YYYY-MM-DD — Midday Addendum
- TICKER moved X% intraday, no obvious pre-market cause — researched via
  scripts/perplexity.sh: <finding, with citation>
```

---

## 2026-08-20 — Pre-market Research

*Reconstructed locally from the first cloud `pre-market` routine run's
reported summary — the routine's own commit was stranded on an ephemeral
session branch and lost to a Claude GitHub App write-permission issue
before it could push. See `memory/RISK-LOG.md`.*

### Account
- Equity: $100,000 | Cash: $100,000 | Buying power: not captured in the
  recovered summary | Daytrade count: 0/4 (paper account PA3M8YH661WT,
  first live run)

### Market Context
- Regime: STRONG_TREND (confidence 0.39) — see `memory/REGIME-LOG.md`
- VIX: 15.82
- S&P 500 futures: ES -0.28%, SPX ~7,689
- WTI ~$85-88, Brent ~$92.8

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| MRNA | 0.797 | — | — | evaluated, NO-TRADE |
| DE | 0.665 | — | — | scanned only |
| MRVL | 0.586 | — | — | evaluated, NO-TRADE |
| MRK | 0.430 | — | — | evaluated, NO-TRADE |
| WMT | -0.07 | — | — | scanned only |

### Trade Ideas
None — all three evaluated candidates (MRNA, MRVL, MRK) returned NO-TRADE.

### NO-TRADE Candidates
- MRNA — no ML probability (no champion model trained), sleeve
  disagreement, regime confidence 0.39 < 0.40 minimum, plus a 0.62%
  quoted spread that looked like it may be a stale quote rather than real
  illiquidity (worth re-checking the quote path)
- MRVL — same three shared reasons, plus a 6.92% quoted spread (likely
  stale/off quote, not real illiquidity for a stock this liquid)
- MRK — same three shared reasons (no ML probability, sleeve
  disagreement, regime confidence below minimum)

### Risk Factors
- `models/champion/` is empty — no ML model has been trained yet, so
  every candidate fails the "no ML probability available" NO-TRADE gate
  regardless of setup quality. This is expected, correct, fail-safe
  behavior, not a bug — but it means the pipeline will HOLD every day
  until a champion model is deliberately trained and validated
  (`quant/model.py`'s `train_challenger` + `research/promotion.py`'s
  `evaluate_promotion`), which has not happened yet.
- Regime confidence (0.39) is very close to but below the 0.40 minimum —
  worth watching whether this is a recurring near-miss.
- Cloud routine git push is currently broken entirely (see
  `memory/RISK-LOG.md`) — every routine's persistence step will fail
  until the Claude GitHub App is granted write access.

### Decision
HOLD — no order placed. Correct outcome given the NO-TRADE results above.
