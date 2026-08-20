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

---

## 2026-08-20 — Pre-market Research (second run, 20:09 UTC / 16:09 ET)

*Operational note: this run fired **after the 16:00 ET close**, not
pre-market. The intended cron (`routines/README.md`) is 6:00 AM
America/Chicago ≈ 11:00 UTC, and today's first run did fire at 12:12 UTC.
Consequence: every live quote this run pulled is a post-close quote, so
`evaluate`'s entry/stop/target/spread numbers below are unusable — see
Risk Factors. The NO-TRADE decisions are unaffected (they fail on gates
that don't depend on the quote).*

### Account
- Equity: $100,000.00 | Cash: $100,000.00 | Buying power: $400,000 |
  Daytrade count: 0/4 (paper account PA3M8YH661WT)
- Positions: none | Open orders: none

### Market Context
- Regime: STRONG_TREND (confidence 0.39) — see `memory/REGIME-LOG.md`
- WTI ~$85.90 / Brent ~$93.13
- S&P 500 futures: ES ~7,698–7,741 (feeds disagree, roughly flat to
  -0.3%) | VIX 14.89 (-6.0%)
- Today's catalysts: US Treasury expanded long-dated bond buybacks to
  $4B → long yields lower, dollar weaker, broad risk-on in equities,
  gold, crude. Stock-specific: Moderna reported Phase 3 cancer-vaccine
  success, driving a sharp biopharma rally that also lifted Merck.
- Earnings before open: no reliable US schedule for today found in
  sources; week characterized as retail-earnings-heavy.
- Economic calendar: Initial Jobless Claims and Philadelphia Fed
  Manufacturing Index both 8:30 AM ET today. FOMC Minutes released
  yesterday (Aug 19, 2:00 PM ET). July CPI (Aug 12) and PPI (Aug 13)
  already out; NFP was Aug 7. No policy meeting this week.
- Sector momentum YTD: Energy +43.1% (leader), Technology +27.7%,
  Industrials +17.6%; Utilities +3.8%, Consumer Discretionary -0.5%,
  Communication Services -5.1% (laggard). 9 of 11 sectors positive YTD.
  Percent-above-50dma breadth not obtainable from sources — regime run
  with `breadth=null`.

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| MRNA | 0.797 | — | 89.9 tech / 100 cat / 10 liq | evaluated, NO-TRADE |
| MRK | 0.430 | — | 71.5 tech / 100 cat / 10 liq | evaluated, NO-TRADE |
| NVDA | -0.133 | — | — | scanned only; catalyst **falsified** |
| XOM | -0.199 | — | — | scanned only; sector-leader proxy, no ticker catalyst |
| PFE | -0.255 | — | — | scanned only; catalyst **falsified** |

**Catalyst verification note:** a "pre-market movers" source claimed
NVDA +6.2% on data-center revenue and PFE +8.9% on an unexpected FDA
approval. Both were checked with a targeted follow-up query and neither
could be corroborated — NVDA's next scheduled earnings is Aug 26 after
the close, and no Pfizer FDA action for today appears in any source.
Treated as unverified and dropped, not carried into `evaluate`.

### Trade Ideas
None actionable. Both evaluated candidates returned NO-TRADE.

- MRNA — catalyst: Phase 3 cancer-vaccine success. Ensemble 0.797
  (momentum +0.94, trend +0.67, breakout +0.68, RS +0.92, mean-reversion
  -0.76 with RSI 73.7). Entry/stop/target **not usable** — post-close
  ask returned 0.00, so the CLI produced entry $0.00 / stop -$6.63 /
  target $13.26 and a 100% spread.
- MRK — catalyst: biopharma sympathy move on the Moderna read-through.
  Ensemble 0.430. CLI output entry $158.44 / stop $153.48 / target
  $168.36 / R:R 2.0 — also **not usable**, derived from a post-close
  quote with a 10.12% spread (bid 142.40 / ask 158.44).

### NO-TRADE Candidates
- MRNA — reasons: no ML probability available yet (champion model not
  trained) — insufficient evidence; sleeve disagreement
  {momentum 0.94, trend 0.672, breakout 0.676, mean_reversion -0.758,
  relative_strength 0.924}; regime confidence 0.39 below minimum 0.40;
  spread/liquidity failed (spread 100.00% > 0.5% or illiquid).
- MRK — reasons: no ML probability available yet (champion model not
  trained) — insufficient evidence; sleeve disagreement
  {momentum 0.528, trend 0.404, breakout 0.482, mean_reversion -0.704,
  relative_strength 0.277}; regime confidence 0.39 below minimum 0.40;
  spread/liquidity failed (spread 10.12% > 0.5% or illiquid).

### Risk Factors
- **Run fired post-close, so the quote path returns unusable data.**
  Confirmed directly: `alpaca.sh quote MRNA` → ask 0, bid 126.37;
  `alpaca.sh quote MRK` → bid 142.40 / ask 158.44 (10.6% spread). This
  is the same symptom the first run flagged as "possibly stale quotes"
  (MRNA 0.62%, MRVL 6.92%) — it is not a `quant/` bug, it is the
  absence of a two-sided market outside RTH. A run at the intended
  6:00 AM CT slot has the same problem for a different reason
  (pre-market books are thin), so the >0.5% spread gate will likely veto
  most candidates at that hour too. Worth confirming whether the spread
  gate should read a consolidated/last-close quote rather than the live
  NBBO when run outside RTH.
- `models/champion/` is still empty — no ML model trained, so every
  candidate fails the "no ML probability available" gate regardless of
  setup. Correct fail-safe behavior; means the pipeline HOLDs every day
  until a champion is deliberately trained and validated
  (`quant/model.py` `train_challenger` → `research/promotion.py`
  `evaluate_promotion`).
- Regime confidence 0.392 — again just under the 0.40 minimum, identical
  to this morning's 0.39. Second consecutive near-miss; this is now a
  pattern, not a one-off.
- MRNA is technically extended: RSI 73.7, 20d z-score +1.75, realized
  vol 86.3%, 20d return +52%. Even with a champion model, a fresh entry
  here would be chasing.
- Cloud routine git push permission (see `memory/RISK-LOG.md`) —
  re-tested at the end of this run; result recorded there.

### Decision
HOLD — no order placed, no position to manage. Correct outcome: two
NO-TRADE results, zero verified-catalyst candidates that clear the gates,
and a quote environment that could not have sized an order anyway.
