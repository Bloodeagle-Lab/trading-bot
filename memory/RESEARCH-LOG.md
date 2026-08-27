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

## 2026-08-20 — Pre-market Research (post-close re-run, 16:10 ET)

*Timing note: this scheduled `pre-market` cloud routine fired at 16:10 ET —
**after** Thursday's close, not before the open. The 12:12 ET entry above is
the same trading day's first run. All quotes below are closing-auction
prints (timestamped exactly 20:00:00Z), not pre-market quotes. Nothing here
was actionable for today's session; it is logged for the audit trail and as
evidence the routine's cron schedule is wrong. See "Risk Factors."*

### Account
- Equity: $100,000.00 | Cash: $100,000.00 | Buying power: $400,000
  (4x intraday) | Daytrade count: 0 (paper account PA3M8YH661WT)
- Positions: none. Open orders: none.

### Market Context
- Regime: STRONG_TREND (confidence 0.39 with VIX supplied; 0.32 on the
  scan's own unsupplied-VIX call) — see `memory/REGIME-LOG.md`
- WTI: ~$86.2-86.6 (+2.4-2.6% on the day) | Brent: ~$93.0 (+1.6%)
  — supply-constraint bid, no diplomatic resolution priced in
- VIX: 15.82 intraday (14.89 prior close) | S&P 500: ~7,708
- Today's catalysts: Treasury said it will more than double buybacks of
  10y/20y/30y debt — yields fell Wednesday, then rebounded Thursday and
  pressured equities, erasing most of the prior day's rally. Higher oil and
  weak Walmart results added to the drag.
- Earnings before open: Walmart (slowest quarterly sales growth in 6+
  years, -6%), Deere (DE), Alibaba (BABA), Advance Auto Parts (AAP)
- Economic calendar: 8:30 ET initial + continuing jobless claims,
  Philadelphia Fed manufacturing survey; 10:00 ET Conference Board Leading
  Index; weekly EIA natural gas inventories
- Sector momentum (YTD): Energy +43.1% (leader), Technology +27.7%,
  Industrials +17.6%, Communication Services -5.1% (laggard)
- Held-ticker news: n/a — no open positions

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

| DE | 0.665 | — (no champion) | 83.2 tech / 70 sector | Earnings today; new 20d high, +16.9% 20d |
| JNJ | 0.463 | — (no champion) | 73.2 tech / 55 sector | Earnings beat, +5.1% pre-market |
| MRK | 0.430 | — (no champion) | 71.5 tech / 55 sector | +13% on Phase 3 cancer-vaccine data with MRNA |
| NVDA | -0.133 | — | — | Data-center strength, but -10.8% 20d, RS -9.3% |
| XOM | -0.199 | — | — | Oil +2.5%, but RS(60d) -28.8% — sector strong, stock is not |
| PFE | -0.255 | — | — | FDA approval, +8.9% pre-market; MA structure -1.00 |
| BABA | -0.620 | — | — | Earnings; -23.5% 20d, RSI 19.8 — falling knife |

### Trade Ideas
None. All three top-scoring candidates returned NO-TRADE from
`scripts/quant_cli.py evaluate`. No order was placed or staged.

### NO-TRADE Candidates
- **DE** — entry $664.65, stop $637.52, target $718.91 (R:R 2.0). Reasons,
  verbatim: no ML probability available yet (champion model not trained) —
  insufficient evidence; sleeve disagreement (mean_reversion -0.748 against
  breakout +0.90); regime confidence 0.32 below minimum 0.40;
  spread/liquidity failed (spread 11.08% > 0.5%).
- **JNJ** — entry $0.00 (!), stop -$8.49, target $16.98. Reasons, verbatim:
  no ML probability available yet; sleeve disagreement; regime confidence
  0.32 below minimum 0.40; spread/liquidity failed (spread 100.00%). The
  zero entry price is a quote-path failure, not a market fact — see Risk
  Factors.
- **MRK** — entry $158.44, stop $153.48, target $168.36 (R:R 2.0). Reasons,
  verbatim: no ML probability available yet; sleeve disagreement; regime
  confidence 0.32 below minimum 0.40; spread/liquidity failed (spread
  10.12% > 0.5%).

### Risk Factors
- **The routine fired post-close.** A `pre-market` run at 16:10 ET cannot
  inform an open it has already missed. Until the cron schedule is moved to
  a genuine pre-market slot (~07:00-09:00 ET), this routine produces
  after-the-fact commentary, and `market-open` would have no same-morning
  research to act on. This is the single most important item in this entry.
- **Quote path returns garbage instead of failing on an API error.**
  `bash scripts/alpaca.sh quote JNJ` returned HTTP 502; `evaluate JNJ` did
  not surface that error — it produced `entry_price 0.0`, `stop_price
  -8.49`, `spread_pct 100.0` and carried on. The NO-TRADE gate caught it
  (correct fail-safe), but a $0.00 entry reaching `quant/risk.py` sizing
  would divide risk dollars by a nonsense risk-per-share. A failed quote
  fetch should raise, not degrade into a zero price. Worth a fix in the
  quote path before `market-open` ever runs unattended.
- **Wide spreads here are closing-auction artifacts, not illiquidity.**
  Every quote came back stamped 20:00:00Z (16:00:00 ET) — DE ask $664.65
  against bid $591.04, MRK ask $158.44 against bid $142.40. This is the
  same "stale quote" pattern flagged in the 12:12 ET entry, and it is a
  consequence of the timing problem above, not a property of these names.
  The spread gate firing on it is correct behavior on bad input.
- **No champion ML model exists** (`models/champion/` empty), so every
  candidate fails the ML-evidence gate regardless of setup. The pipeline
  will HOLD every single day until a champion is deliberately trained and
  promoted (`quant/model.py` `train_challenger` → `research/promotion.py`
  `evaluate_promotion`). Expected, fail-safe, and unchanged from this
  morning — but it means these daily NO-TRADE results carry no information
  about the candidates themselves yet.
- **Regime confidence 0.32-0.39 is a persistent near-miss** of the 0.40
  minimum — second run in a row. Both runs classify STRONG_TREND on trend
  features (SPY +0.584, QQQ +0.587) while HIGH_VOL scores 0.55 against
  STRONG_TREND's 0.60, which is what holds confidence down. Worth reviewing
  at Friday's weekly review whether that is the engine being appropriately
  humble or a miscalibration.
- Sector-vs-stock divergence: Energy leads YTD (+43.1%) and oil rallied
  2.5% today, but XOM's own relative strength is -28.8% over 60d. Do not
  read the sector's YTD number as a catalyst for the megacaps in it.

### Decision
**HOLD** — no order placed, none staged. Correct and expected outcome: all
three evaluated candidates returned NO-TRADE on gates that are working as
designed, and this run happened after the close in any case.

## 2026-08-21 — Pre-market Research

Run fired 11:08 UTC / 7:08 ET — genuinely pre-market for the first time,
inside the intended 07:00-09:00 ET window flagged in `memory/RISK-LOG.md`'s
2026-08-20 scheduling note. Noting the fix; no further action needed on
that item unless it regresses.

### Account
- Equity: $100,000 | Cash: $100,000 (100%) | Buying power: $400,000 |
  Daytrade count: 0/4
- Positions: none | Open orders: none

### Market Context
- Regime: STRONG_TREND (confidence 0.392) — see `memory/REGIME-LOG.md`
- WTI / Brent: ~$86.50 / ~$93.60 (both down slightly on the day, per
  Oilprice.com)
- S&P 500 futures / VIX: ES roughly flat-to-down (~7,690-7,730 range
  depending on feed, down ~0.3% on the clearest quote); VIX ~15.7
  (up modestly, ~+5-6% on the day, still a low-vol print)
- Today's catalysts: light U.S. macro calendar — S&P Global flash
  Manufacturing/Services PMI at 9:45 ET is the main scheduled item; BLS
  State Employment and Unemployment (July) at 10:00 ET; semiconductor
  (SMH) and energy (XLE) flagged as the relative-strength leaders this
  week; no Fed appearance or CPI/PPI today
- Earnings before open: BJ (BJ's Wholesale), UI (Ubiquiti), BKE (Buckle),
  BEKE (KE Holdings) — the four calendar-confirmed pre-open reports
- Economic calendar: no CPI/PPI/FOMC/jobs report today — CPI (Aug 12),
  PPI (Aug 13), and FOMC minutes (Aug 19) already out; next jobs report is
  Sept 4
- Sector momentum: Energy still the clear YTD leader (+37-45% depending on
  source), Technology +27.5%, Materials +16.5%; Financials and
  Communication Services lagging/negative
- Held-ticker news: n/a — no open positions

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| BJ | -0.057 | — (no champion) | n/a — quote error | Earnings today; weak breakout/mean-rev only, RS(60d) -24.9% |
| BKE | -0.254 | — (no champion) | 57 (37.3 tech / 40 sector / 100 cat / 10 liq) | Earnings today; evaluated, NO-TRADE |
| UI | -0.353 | — | — | Earnings today; scanned only, RS(60d) -50.4%, 60d ret -36.5% |
| BEKE | -0.437 | — | — | Earnings today; scanned only, RS(60d) -15.8%, weakest of the four |

### Trade Ideas
None. All four earnings-day candidates scored negative ensemble (no
bullish setup regardless of catalyst) — none warranted a constructive
thesis. Ran `evaluate` on the top two anyway per the pipeline:

- **BJ** — `evaluate` raised a hard error: "no usable quote for BJ
  (bid=85.77, ask=0.0) — market data may be degraded or stale." This is
  the correct behavior for the quote-path bug flagged in
  `memory/RISK-LOG.md` on 2026-08-20 (a dead/one-sided quote used to
  degrade into a $0.00 entry price and slip past unnoticed) — worth
  confirming as a fix, not just a NO-TRADE input. No entry/stop/target
  produced; nothing reached sizing.
- **BKE** — entry $48.55 / stop $46.25 / target $53.15 (R:R 2.0), NO-TRADE.

### NO-TRADE Candidates
- **BJ** — quote path errored (ask=0.0) before reaching the NO-TRADE gate;
  treated as unusable, not evaluated further.
- **BKE** — reasons, verbatim: no ML probability available yet (champion
  model not trained) — insufficient evidence; sleeve disagreement
  {momentum -0.335, trend -0.584, breakout 0.273, mean_reversion 0.667,
  relative_strength -0.398}; regime confidence 0.32 below minimum 0.40;
  setup quality 57 below minimum 60; spread/liquidity failed (spread
  25.56% > 0.5%).
- UI, BEKE — not run through `evaluate`; ensemble scores (-0.353, -0.437)
  and negative 60d relative strength made them clearly weaker than BJ/BKE,
  no need to spend an evaluate call confirming a NO-TRADE on a worse setup.

### Risk Factors
- **Regime confidence 0.39 (with VIX) / 0.32 (scan's own call) is now a
  third consecutive near-miss** of the 0.40 minimum (2026-08-20 morning
  0.39, 2026-08-20 post-close 0.32/0.39, today 0.392/0.317). HIGH_VOL
  scoring 0.55 against STRONG_TREND's 0.60 is consistently what holds
  confidence down. This is a pattern now, not noise — flag for Friday's
  weekly review regardless of which Friday lands next.
- **No champion ML model exists** (`models/champion/` empty) — every
  candidate fails the ML-evidence gate regardless of setup. Expected,
  fail-safe, unchanged from prior runs.
- All four earnings names today are in structural downtrends (MA
  structure -0.40 to -1.00, negative 60d relative strength) — earnings
  reports alone are not a long catalyst here; would need a clean
  post-earnings reaction to reconsider, not pre-positioning.
- Quote-path bug from 2026-08-20 (dead quote degrading to $0.00 entry)
  appears to now raise a hard error instead (see BJ above) — good, but
  only directly observed for one ticker in one direction (ask=0.0); not
  a full regression test.

### Decision
**HOLD** — no order placed, none staged. All four earnings-day candidates
carry negative ensemble scores (no bullish setup), the one evaluated
survivor (BKE) is NO-TRADE on multiple gates, and BJ's quote path errored
outright. Correct, expected outcome.

## 2026-08-22 — Pre-market Research

### Account
- Equity: $100,000 | Cash: $100,000 (100%) | Buying power: $400,000 |
  Daytrade count: 0/4
- Positions: none | Open orders: none

### Market Context
- Regime: STRONG_TREND (confidence 0.392 with VIX / 0.317 scan's own call) — see `memory/REGIME-LOG.md`
- WTI / Brent: ~$86.6-87.1 / ~$94.0-94.4, both modestly higher on the day
- S&P 500 futures / VIX: ES ~7,691-7,695 (+0.3-0.4%); VIX ~15.4, down
  ~4-5% on the day — low-vol, mildly risk-on tape
- Today's catalysts: two FDA PDUFA decisions dated today — Capricor
  Therapeutics (CAPR) for Deramiocel in Duchenne muscular dystrophy, and
  Savara (SVRA) for Molbreevi in aPAP; broader market narrative remains
  cooling-inflation + AI/chip earnings strength + Treasury long-bond
  buyback support; weekly jobless claims also due today
- Earnings before open: BJ (BJ's Wholesale), UI (Ubiquiti) — same two
  names flagged BMO yesterday; some calendars show no reports at all
  today, so treat as low-confidence
- Economic calendar: no CPI/PPI/FOMC/jobs report today — initial jobless
  claims only; next CPI Sept, next jobs report Sept 4
- Sector momentum: Energy still YTD leader (+44.6%), Technology +27.5%,
  Materials +16.5%, Utilities +3.9%; Communication Services worst
  (-5.4%), Consumer Discretionary also negative (-1.9%); breadth broad
  (9/11 sectors positive YTD)
- Held-ticker news: n/a — no open positions

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| SVRA | 0.528 | — (no champion) | 76.4 tech / 50 sector / 100 cat / 10 liq | FDA PDUFA today; only positive-score candidate |
| BJ | -0.057 | — | — | Earnings today (disputed); quote errored on evaluate |
| CAPR | -0.325 | — | — | FDA PDUFA today; already down 25% (60d) into the decision |
| UI | -0.353 | — | — | Earnings today (disputed); weakest scan, not evaluated |

### Trade Ideas
None. Ran `evaluate` on the top three by ensemble score:

- **SVRA** — entry $6.32 / stop $5.91 / target $7.14 (R:R 2.0), NO-TRADE.
- **BJ** — `evaluate` raised a hard error: "no usable quote for BJ
  (bid=91.76, ask=0.0) — market data may be degraded or stale." Same
  quote-path failure mode as 2026-08-20/08-21 (ask=0.0), same correct
  fail-safe (raises instead of degrading to a $0 entry). No entry/stop/
  target produced.
- **CAPR** — `evaluate` raised the identical error: "no usable quote for
  CAPR (bid=5.34, ask=0.0)." Second ticker today hitting the same
  ask=0.0 failure.

### NO-TRADE Candidates
- **SVRA** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.53 below the validated
  minimum 0.55; sleeve disagreement (mean_reversion -0.768 against
  momentum +0.705, breakout +0.468, trend +0.462, relative_strength
  +0.463); regime confidence 0.32 below minimum 0.40; spread/liquidity
  failed (spread 25.16% > 0.5%).
- BJ, CAPR — not evaluated past the quote error; no NO-TRADE reasons
  available since the pipeline never reached the gate chain.
- UI — not run through `evaluate`; ensemble score -0.353 and negative 60d
  relative strength (-50.4%) made it clearly the weakest of the four, no
  need to spend an evaluate call confirming a NO-TRADE on a worse setup.

### Risk Factors
- **Regime confidence 0.392/0.317 is now a fourth consecutive near-miss**
  of the 0.40 minimum (2026-08-20 x2, 2026-08-21, now 2026-08-22), always
  on the same HIGH_VOL (0.55) vs. STRONG_TREND (0.60) margin. This is a
  structural pattern, not day-to-day noise — still flagged for the next
  weekly review.
- **Quote-path `ask=0.0` failure recurred on two more tickers today**
  (BJ, CAPR), on top of BJ itself yesterday and JNJ on 2026-08-20. Same
  symbol (BJ) has now hit this exact failure two days running. The
  NO-TRADE/hard-error fail-safe is working correctly each time, but a
  bug that reproduces on the same name across days points at something
  specific to Alpaca's quote feed for these tickers (or a systemic issue
  the routine keeps encountering at this time of day) rather than random
  staleness — worth a direct look at `scripts/alpaca.sh quote BJ` outside
  the pipeline before it recurs a third time.
- **CAPR's PDUFA catalyst is real but the setup is deteriorating into the
  decision**: 60d relative strength -38.9%, 20d momentum -15.6%, RSI 36.4
  — this reads as the market already pricing in a negative/uncertain
  outcome, not a case for a pre-decision long regardless of what the
  pipeline's gates say. No options available under this strategy in any
  case, so no way to structure defined-risk exposure to the binary event.
- **SVRA is the closest thing to a live idea** (ensemble 0.528, only
  candidate above 0) but the sleeve disagreement is real and directly
  event-driven — RSI 71.8 / z-score +1.87 (already extended) heading into
  a binary FDA readout is not the same setup the momentum/trend sleeves
  are scoring. The 25% spread here also looks like it could be
  event-driven wide-quoting ahead of the PDUFA date, not a liquidity
  defect — worth re-scanning after the decision lands, not chasing pre-event.
- **No champion ML model exists** (`models/champion/` empty) — every
  candidate fails the ML-evidence gate regardless of setup. Expected,
  fail-safe, unchanged from prior runs.

### Decision
**HOLD** — no order placed, none staged. Only positive-score candidate
(SVRA) is NO-TRADE on multiple gates and sits on an event-driven extended
setup into a binary FDA catalyst; the other three candidates are either
negative-ensemble or blocked by a recurring quote-path error. Correct,
expected outcome.

## 2026-08-23 — Pre-market Research

**Note: today is Sunday — markets closed, not a trading day.** Routine
fired anyway (scheduling issue, see `memory/RISK-LOG.md`). Research
completed for the record; no scan/evaluate run — see Decision.

## 2026-08-24 — Pre-market Research

### Account
- Equity: $100,000 | Cash: $100,000 (100%) | Buying power: $400,000 |
  Daytrade count: 0/4
- Positions: none | Open orders: none

### Market Context
- Regime: STRONG_TREND (confidence 0.392) — see `memory/REGIME-LOG.md` for
  the full record
- WTI / Brent: ~$87.06 / ~$94.39 (last settle, Friday 8/21; no weekend
  trading)
- S&P 500 futures / VIX: ES ~7,691.25 (Friday settle, +0.38%); VIX 15.13
  (Friday close, -5.5% on the day) — both stale weekend snapshots, not
  live quotes
- Today's catalysts: none scheduled — it's Sunday. Broader narrative
  heading into next week: rising 10-year yield (4.736%) as a headwind for
  growth/tech, Nvidia earnings and PCE/Jackson Hole flagged as next week's
  catalysts (week of 8/24-8/28). One low-quality source
  (interactivecrypto.com) claimed a same-day TSLA "close" on Sunday 8/23 —
  factually impossible since markets don't trade Sundays; discarded as
  unreliable, not used as a candidate.
- Earnings before open: none — multiple calendars (TradingView, Nasdaq,
  Markets Insider, Tickzen) confirm zero reports scheduled for 8/23
  (Sunday); next reports are Monday 8/24 (GRRR, AVXL, RR, and ~22 others).
- Economic calendar: no CPI/PPI/FOMC/jobs data today. CPI (8/12), PPI
  (8/13) already out; next jobs report Fri 9/4; next PPI 9/10. No
  legitimate scheduled release found for Sunday 8/23 despite one FRED
  listing noise ("FOMC Press Release" 7pm CT) that does not match any
  known FOMC meeting date — disregarded as calendar-source noise.
- Sector momentum: Energy still YTD leader (+44.3%), Technology +27.6%,
  Materials +19.0%; Communication Services worst (-4.8%), Consumer
  Discretionary also negative (-0.8%); breadth 9/11 sectors positive YTD —
  materially unchanged from 8/22.
- Held-ticker news: n/a — no open positions

### Candidate Scan (scripts/quant_cli.py scan)
Not run. No earnings, no scheduled catalysts, and no legitimate same-day
news exists for a Sunday — nothing meets the "specific, verifiable
catalyst" bar STEP 5 requires. Running `scan`/`evaluate` against Monday's
names using weekend-stale quotes would test nothing and risks reproducing
the ask=0.0 degraded-quote bug on data that isn't even live. Deferred to
Monday's `pre-market` run, which will have real quotes and real earnings
names (GRRR, AVXL, RR, +22 others).

### Trade Ideas
None.

### NO-TRADE Candidates
None evaluated — no candidates met the catalyst bar (see above).

### Risk Factors
- **Routine fired on a non-trading day (Sunday).** This is a new
  scheduling-bug data point beyond the 2026-08-20 post-close-firing issue
  already logged in `memory/RISK-LOG.md` — that one was a wrong *time*,
  this one is a wrong *day* entirely. Flagged there in detail; needs a
  cron-config look before Monday if not already fixed.
- **`quant/regime.py`'s feature inputs are byte-identical across four
  separate calendar days** (`trend_spy` 0.584, `trend_qqq` 0.587,
  `volatility_20` 0.1811 — unchanged 2026-08-20 through 2026-08-23,
  including today). Confidence has also landed on exactly 0.392 (with VIX
  supplied) every single time. This is very unlikely to be real market
  behavior four days running and reads as a stale/cached data source
  feeding the regime engine rather than a live SPY/QQQ pull — flagged in
  `memory/RISK-LOG.md` as a new, separate finding; worth checking the
  regime engine's data source directly before trusting Monday's
  classification for sizing.
- No champion ML model exists (`models/champion/` empty) — unchanged,
  expected.

### Decision
**HOLD** — no research-driven candidates today; not a trading day. Logged
per `CLAUDE.md`'s instruction to record every routine firing, expected or
not.

- Regime: STRONG_TREND (confidence 0.392 with VIX / 0.317 scan's own call) — see `memory/REGIME-LOG.md`
- WTI / Brent: ~$84-87 / ~$87-93, both down on the day — Iran sanctions
  headlines cutting both ways (geopolitical premium vs. profit-taking
  after last week's rally); wide dispersion across feeds today
- S&P 500 futures / VIX: ES ~7,680-7,700, roughly flat (-0.05% to
  +0.11% depending on feed); VIX ~15.13 (Friday's close, no fresher
  print available) — low-vol, flattish tape
- Today's catalysts: no major single-name US catalyst; broader narrative
  is a Nvidia-earnings-anticipation setup (reports later this week) plus
  Jackson Hole positioning and elevated Treasury yields pressuring risk
  assets; Chicago Fed National Activity Index due today (minor)
- Earnings before open: PDD Holdings, XPeng (XPEV) headline the list;
  also DRI, TD SYNNEX (SNX), Acuity Brands (AYI), Commercial Metals,
  Winnebago, Nano-X Imaging per broader calendars — some disagreement
  across sources on the full set
- Economic calendar: no CPI/PPI/FOMC/jobs release today; next CPI Sept
  11, next PPI Sept 10, next jobs report Sept 4; Core PCE later this week
- Sector momentum: Energy still YTD leader (+44.3%), Technology +27.6%,
  Materials +19.0%, Industrials +16.8%; Communication Services worst
  (-4.8%), Consumer Discretionary also negative (-0.8%)

## 2026-08-24 — Pre-market Research (run inline from market-open — no earlier pre-market entry existed)

### Account
- Equity: $100,000 | Cash: $100,000 (100%) | Buying power: $400,000 |
  Daytrade count: 0/4 (endpoint doesn't return the field; no trades executed
  yet this account, assumed 0)
- Positions: none | Open orders: none

### Market Context
- Regime: STRONG_TREND (confidence 0.392 with VIX / 0.317 scan's own call) — see `memory/REGIME-LOG.md`
- WTI / Brent: ~$85.4-85.6 / ~$92.9-93.1, both down ~1.5-2% on the day on
  reports of tougher new US sanctions on Iran
- S&P 500 futures / VIX: ES ~7,679-7,689 (-0.1 to -0.3%); VIX ~15.9-16.0,
  roughly flat — low-vol, mixed-to-mildly-risk-off tape
- Today's catalysts: Nvidia earnings (this week's AI-trade bellwether, not
  confirmed before today's open), Jackson Hole Fed symposium, Chicago Fed
  National Activity Index + weekly jobless claims at 12:30pm ET; Australia
  CPI / BoJ rate-hike expectations for Asia/FX
- Earnings before open: DRI (Darden), SNX (TD Synnex), AYI (Acuity
  Brands), CMC (Commercial Metals), WGO (Winnebago), NNOX (Nano-X); PDD,
  XPEV also flagged pre-market on a second calendar
- Economic calendar: no CPI/PPI/FOMC today; Chicago Fed National Activity
  Index + weekly jobless claims at 12:30pm ET; next PPI Sept 10
- Sector momentum: Energy still YTD leader (+44.3%), Technology +27.6%,
  Materials +19.0%, Industrials +16.8%; Communication Services worst
  (-4.8%), Consumer Discretionary also negative (-0.8%); breadth broad
  (9/11 sectors positive YTD)
- Held-ticker news: n/a — no open positions

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| AYI | 0.598 | — (no champion) | 79.9 tech / 16.8 sector / 100 cat / 10 liq | Earnings today; only candidate above 0.55 minimum |
| SNX | 0.184 | — | 59.2 tech / 27.6 sector / 100 cat / 10 liq | Earnings today; below ensemble minimum |
| DRI | 0.164 | — | 58.2 tech / -0.8 sector / 100 cat / 10 liq | Earnings today; weak sector (Consumer Discretionary) |
| PDD | -0.266 | — | — | Earnings today; negative ensemble, not evaluated |
| XPEV | -0.558 | — | — | Earnings today; weakest scan (-24% 20d ret), not evaluated |

| AYI | 0.598 | — (no champion) | 79.9 tech / 65 sector / 100 cat / 10 liq | Earnings today; only candidate above 0.55 min |
| WGO | 0.204 | — | 60.2 tech / 30 sector / 100 cat / 10 liq | Earnings today; weak sector (Discretionary) |
| SNX | 0.184 | — | 59.2 tech / 80 sector / 100 cat / 10 liq | Earnings today; strong sector, weak technicals |
| DRI | 0.164 | — | not evaluated | Earnings today; below scan threshold, not run |
| CMC | -0.327 | — | not evaluated | Earnings today; negative ensemble, not run |

### Trade Ideas
None. Ran `evaluate` on the top three by ensemble score:

- **AYI** — entry $383.94 / stop $360.20 / target $431.42 (R:R 2.0),
  NO-TRADE.
- **SNX** — entry $278.38 / stop $262.44 / target $310.26 (R:R 2.0),
  NO-TRADE.
- **DRI** — entry $245.99 / stop $236.88 / target $264.21 (R:R 2.0),
  NO-TRADE.

### NO-TRADE Candidates
- **AYI** — reasons, verbatim: sleeve disagreement {momentum 0.835,
  trend 0.401, breakout 0.401, mean_reversion -0.672, relative_strength
  0.795}; regime confidence 0.32 below minimum 0.40; spread/liquidity
  failed (spread 22.37% > 0.5%).
- **SNX** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.18 below the validated
  minimum 0.55; regime confidence 0.32 below minimum 0.40; spread/
  liquidity failed (spread 16.81% > 0.5%).
- **DRI** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.16 below the validated
  minimum 0.55; regime confidence 0.32 below minimum 0.40; setup quality
  57 below minimum 60; spread/liquidity failed (spread 16.20% > 0.5%).
- PDD, XPEV — not run through `evaluate`; both negative ensemble scores
  (-0.27, -0.56) driven by negative momentum/trend/relative-strength made
  them clearly weaker than AYI/SNX/DRI, no need to spend an evaluate call
  confirming a NO-TRADE on a worse setup.

### Risk Factors
- **Regime confidence 0.392/0.317 is now a fifth consecutive near-miss**
  of the 0.40 minimum (2026-08-20 x2, 2026-08-21, 2026-08-22, now
  2026-08-24), always on the same HIGH_VOL (0.55) vs. STRONG_TREND (0.60)
  margin. This is now a five-session pattern, not noise — flag again for
  the next weekly review; worth asking whether the HIGH_VOL/STRONG_TREND
  weighting itself needs revisiting rather than continuing to log it as a
  near-miss each day.
- **Large nonzero spreads (16-22%) failed the liquidity gate on all three
  evaluated tickers today**, without the hard ask=0.0 error seen on
  2026-08-20/21/22 (BJ, CAPR, JNJ). Different failure shape (a wide-but-
  present two-sided quote vs. a dead one-sided quote) but the same net
  effect — every candidate blocked on spread/liquidity regardless of
  setup quality. Five sessions running with a quote-data quality issue in
  some form; still worth the direct `scripts/alpaca.sh quote` look
  flagged on 2026-08-22, not yet done.
- **AYI is the strongest setup seen in the last several sessions**
  (ensemble 0.598, technical score 79.9, real earnings catalyst) but is
  blocked purely on regime confidence and the spread gate, not on the
  setup itself — worth re-scanning post-earnings if the spread normalizes
  and regime confidence clears 0.40.

- **AYI** — entry $383.94 / stop $360.20 / target $431.42 (R:R 2.0), NO-TRADE.
- **SNX** — entry $278.38 / stop $262.44 / target $310.26 (R:R 2.0), NO-TRADE.
- **WGO** — entry $36.77 / stop $34.46 / target $41.39 (R:R 2.0), NO-TRADE.

### NO-TRADE Candidates
- **AYI** — reasons, verbatim: sleeve disagreement (mean_reversion -0.672
  against momentum +0.835, trend +0.401, breakout +0.401, relative_strength
  +0.795); regime confidence 0.39 below minimum 0.40; spread/liquidity
  failed (spread 22.37% > 0.5%).
- **SNX** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.18 below the validated
  minimum 0.55; regime confidence 0.39 below minimum 0.40; spread/liquidity
  failed (spread 16.81% > 0.5%).
- **WGO** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.20 below the validated
  minimum 0.55; sleeve disagreement (momentum +0.274, trend +0.024,
  breakout +0.436, mean_reversion -0.487, relative_strength +0.054); regime
  confidence 0.39 below minimum 0.40; spread/liquidity failed (spread
  28.94% > 0.5%).
- DRI, CMC — not evaluated past the scan; DRI's 0.164 ensemble and CMC's
  negative -0.327 ensemble made both clearly weaker than the top three,
  no need to spend an evaluate call confirming a NO-TRADE on a worse setup.

### Risk Factors
- **Regime confidence 0.392 is now a fifth consecutive near-miss** of the
  0.40 minimum (2026-08-20 x2, 2026-08-21, 2026-08-22, now 2026-08-24 —
  no research/routine ran 2026-08-23, a Sunday), always on the same
  HIGH_VOL (0.55) vs. STRONG_TREND (0.60) margin. Structural pattern,
  flagged again for weekly review.
- **All three evaluated candidates failed on spread/liquidity (16.8-28.9%
  spreads)** — this is a genuinely pre-market run (quotes pulled before
  the open), so wide spreads here are expected market microstructure, not
  the ask=0.0 quote-path bug seen on BJ/CAPR/JNJ in prior logs. Worth
  re-checking AYI (the only ensemble-PASS candidate) once the market
  opens and real liquidity is present, though STEP 2 of `market-open`
  already re-validates with fresh data before any order would fire.
- **AYI's setup is the closest to tradeable** (ensemble 0.598, only
  candidate above the 0.55 minimum) but real earnings-day gap risk (20d
  return already +18%, RSI 69.2, z-score +1.63 — extended into the print)
  plus the regime-confidence and spread gates both failing independently
  means this is correctly NO-TRADE, not a borderline call to argue with.
- **No champion ML model exists** (`models/champion/` empty) — every
  candidate fails the ML-evidence gate regardless of setup. Expected,
  fail-safe, unchanged from prior runs.

### Decision
**HOLD** — no order placed, none staged. Best-scoring candidate (AYI) is
NO-TRADE on regime confidence and spread/liquidity despite a strong
technical setup; SNX and DRI fail the ensemble-score minimum outright;
PDD and XPEV are negative-ensemble. Correct, expected outcome.

**HOLD** — no order placed, none staged. AYI is the only candidate above
the ensemble minimum but fails on regime confidence and spread/liquidity;
SNX and WGO fail ensemble score outright; DRI and CMC weaker still.
Correct, expected outcome.

## 2026-08-25 — Pre-market Research

### Account
- Equity: $100,032.64 | Cash: $89,471.29 (89.5%) | Buying power: $387,456.94 |
  Daytrade count: 0/4 (endpoint doesn't return the field; assumed 0)
- Positions: BAC 169 @ $62.30, current $62.4932 (+0.31% intraday, +$32.65
  unrealized) — manual mechanism-test position, see 2026-08-24 `TRADE-LOG.md`
  entry. Trailing 10% GTC stop confirmed live (hwm $62.55, stop $56.295,
  status "new").
- Open orders: 1 (the BAC protective trailing stop above)

### Market Context
- Regime: STRONG_TREND (confidence 0.872 with `--vix 15.8`) — see
  `memory/REGIME-LOG.md`
- WTI / Brent: ~$85.2-85.4 / ~$92.3-92.5, both up modestly intraday after
  yesterday's ~2% drop on Iran-sanctions/diplomacy headlines
- S&P 500 futures / VIX: ES ~7,662-7,689, mixed-to-mildly-negative
  (-0.1% to -0.4% depending on feed); VIX ~15.8, up modestly off Friday's
  15.13 close — still a low-vol tape
- Today's catalysts: light on major macro; Nvidia earnings tomorrow
  (8/26) is the market's next real directional catalyst, along with
  CrowdStrike/Salesforce/Synopsys/Okta/HP; Fed Barkin speech today
- Earnings before open: DKS (Dick's Sporting Goods), BNS (Bank of Nova
  Scotia), BMO (Bank of Montreal), VIPS (Vipshop), BZ (Kanzhun), EH
  (EHang), GFI (Gold Fields), SLQT (SelectQuote), CTRN (Citi Trends) —
  13 companies before the open total; INTU (Intuit) reports after close
  today (not a pre-market mover)
- Economic calendar: no CPI/PPI/FOMC today (CPI Aug 12, PPI Aug 13, FOMC
  minutes Aug 19 already out; next jobs report Sept 4); today's prints:
  ADP Weekly Employment Change, Richmond Fed Manufacturing Index, New
  Home Sales, Consumer Confidence, S&P/Case-Shiller Home Price Index
- Sector momentum: Energy still YTD leader (+44.3%), Technology +27.6%,
  Materials +19.0%, Industrials +16.8%, Health Care +13.8%, Real Estate
  +13.4%, Consumer Staples +12.1%, Financials +5.9%, Utilities +1.5%;
  Consumer Discretionary -0.8% and Communication Services -4.8% both
  negative
- Held-ticker news (BAC): trading near 52-week high (~$62.3-62.5, +1%
  type moves); SEC subpoenaed BAC and other large banks in the
  "Situational Awareness" trading probe (regulatory headline risk, stock
  unaffected so far); WSJ reports BAC plans $250B AI/energy
  infrastructure deployment; dividend raised 14% to $0.32; Jio Credit
  stake deal (~$1.9B); lost head of investment banking (early Aug). No
  thesis to break (mechanism-test position, no catalyst thesis to begin
  with) and no move near -7% — nothing urgent.

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| BMO | 0.591 | — (no champion) | 79.5 tech / 5.9 sector / 100 cat / 10 liq | Earnings today; only candidate above 0.55 minimum |
| BNS | 0.587 | — | not evaluated — quote error | Earnings today; close 2nd by ensemble, evaluate crashed on bad quote |
| DKS | 0.374 | — | not evaluated | Earnings today; below ensemble minimum, weak sector (Consumer Discretionary) |
| VIPS | -0.251 | — | — | Earnings today; negative ensemble, not evaluated |
| INTU | -0.461 | — | — | Earnings after close today; negative ensemble, not evaluated |

### Trade Ideas
None. Ran `evaluate` on the top two by ensemble score:

- **BMO** — entry $196.65 / stop $192.09 / target $205.77 (R:R 2.0),
  NO-TRADE.
- **BNS** — `evaluate` raised a hard error: "no usable quote for BNS
  (bid=73.79, ask=0.0) — market data may be degraded or stale." No
  entry/stop/target produced; nothing reached sizing.

### NO-TRADE Candidates
- **BMO** — reasons, verbatim: sleeve disagreement {momentum 0.607,
  trend 0.754, breakout 0.506, mean_reversion -0.253, relative_strength
  0.474}; spread/liquidity failed (spread 25.59%, illiquid or too wide).
- **BNS** — quote path errored (ask=0.0) before reaching the NO-TRADE
  gate; treated as unusable, not evaluated further. Confirmed directly
  via `scripts/alpaca.sh quote BNS`: `{"ap":0,"as":0,"bp":73.79,"bs":100}`
  — a real bid, dead ask, condition code "R".
- DKS, VIPS, INTU — not run through `evaluate`; DKS's 0.374 ensemble is
  below the 0.55 minimum and sits in a negative-momentum sector; VIPS
  (-0.251) and INTU (-0.461) both carry negative ensemble scores driven
  by negative momentum/trend/relative-strength — all three clearly
  weaker than BMO/BNS, no need to spend an evaluate call confirming a
  NO-TRADE on a worse setup.

### Risk Factors
- **Regime confidence jumped sharply today — 0.872 (with VIX) / 0.797
  (scan's own call)** — the first session since the 2026-08-20 baseline
  to clear the 0.40 NO-TRADE minimum by a wide margin, breaking the
  five-consecutive-near-miss streak logged 2026-08-20 through 2026-08-24.
  Breadth (%>50dma) also returned a real number for the first time
  (0.724) instead of `null` — looks like the earlier "stale/missing
  breadth data" flag from prior risk-log entries has resolved on its
  own; worth confirming at the next weekly review rather than assuming
  it's permanent.
- **BNS's quote error (ask=0.0) is the same recurring one-sided-quote
  data-quality issue** seen on BJ (2026-08-21), CAPR/JNJ (2026-08-22),
  and now BNS today — five tickers across four separate sessions.
  `evaluate`'s hard-fail-rather-than-silently-trade behavior is correct
  and safe, but the underlying data-quality issue itself is still not
  root-caused. Flagging again for the next weekly review as a pattern
  that has now recurred enough times to warrant an actual investigation,
  not another "worth checking" note.
- **BMO's 25.59% spread blocked an otherwise-decent setup** (ensemble
  0.591, technical score 79.5, real earnings catalyst, sector momentum
  now positive at 5.9) purely on liquidity/spread — genuinely pre-market
  timing (quotes pulled before the open), consistent with the same
  microstructure pattern noted on prior sessions, not a bug.
- **No champion ML model exists** — every candidate fails the
  ML-evidence gate regardless of setup. Expected, fail-safe, unchanged.

### Decision
**HOLD** — no order placed, none staged. BMO is the only candidate above
the ensemble minimum but fails on sleeve disagreement and spread/
liquidity; BNS's quote path errored outright; DKS, VIPS, INTU all weaker
or negative-ensemble. Correct, expected outcome.

## 2026-08-26 — Pre-market Research

### Account
- Equity: $100,041.34 | Cash: $89,471.29 (89.4%) | Buying power: $387,481.31 |
  Daytrade count: 0/4 (endpoint doesn't return the field; assumed 0)
- Positions: BAC 169 @ $62.30, current $62.5447 (+0.39% intraday, +$41.35
  unrealized) — manual mechanism-test position, see 2026-08-24 `TRADE-LOG.md`
  entry. Trailing 10% GTC stop confirmed live (hwm $62.575, stop $56.3175,
  status "new").
- Open orders: 1 (the BAC protective trailing stop above)

### Market Context
- Regime: STRONG_TREND (confidence 0.68 with `--vix 15.7 --breadth 0.724`)
  — see `memory/REGIME-LOG.md`
- WTI / Brent: ~$80.3-82.4 / ~$86.3-89.5, both down ~2-3% intraday as US
  sanctions/diplomacy rollout on Iran (Strait of Hormuz) deflated the
  supply-risk premium, plus a bearish US inventory build
- S&P 500 futures / VIX: ES ~7,670-7,700 (mixed, roughly flat to +0.2-0.4%
  depending on feed/contract); VIX ~15.5-15.9, still a low-vol tape
- Today's catalysts: **Nvidia earnings after the close** — the market's
  single biggest catalyst this month (AI capex/demand read-through,
  ~7.3% S&P weight); also reporting after close: Salesforce, CrowdStrike,
  Synopsys, Okta, HP; July Core PCE / GDP second estimate / durable goods
  at 8:30am ET (Fed-cut-expectations relevant, no CPI/PPI/FOMC/jobs today)
- Earnings before open: KSS (Kohl's), WSM (Williams-Sonoma), ANF
  (Abercrombie), DY (Dycom Industries), SJM (Smucker), BBWI (Bath & Body
  Works), LI (Li Auto), plus several smaller/foreign names — 27 companies
  total before the open
- Economic calendar: no CPI/PPI/FOMC/jobs today (CPI Aug 12, PPI Aug 13,
  FOMC minutes Aug 19, next jobs report Sept 4); today's prints: Core PCE
  Price Index, Q2 GDP second estimate, Personal Income & Spending,
  Durable Goods, Capital Goods Orders, MBA Mortgage Applications
- Sector momentum (YTD): Energy +43.1% (leader), Technology +25.4%,

## 2026-08-26 — Pre-market Research (run inline from market-open — no earlier pre-market entry existed)

### Account
- Equity: $100,001.68 | Cash: $89,471.29 (89.5%) | Buying power: $387,370.25 |
  Daytrade count: 0/4 (endpoint doesn't return the field; assumed 0)
- Positions: BAC 169 @ $62.30, current $62.34 (+0.06% intraday, +$6.76
  unrealized) — manual mechanism-test position, see 2026-08-24
  `TRADE-LOG.md` entry. Trailing 10% GTC stop confirmed live (hwm $62.58,
  stop $56.322, status "new").
- Open orders: 1 (the BAC protective trailing stop above)

### Market Context
- Regime: STRONG_TREND (confidence 0.605 scan-internal / 0.467 with
  explicit `--vix 15.68 --breadth 0.6`) — see `memory/REGIME-LOG.md`
- S&P 500 futures / VIX: ES ~7,687-7,688 (-0.05 to -0.07%), roughly flat;
  VIX ~15.68-15.71 (spot), VIX futures ~17.2-17.25 — low-vol tape
- Today's catalysts: Nvidia earnings after the close (the week's biggest
  single catalyst) plus July PCE/Core PCE inflation data, durable goods
  orders, and Q2 GDP (second reading) all at 8:30 ET; CrowdStrike also
  reports after the bell; Fed Jackson Hole symposium (Warsh speech) later
  this week
- Earnings before open: Kohl's (KSS), Abercrombie & Fitch (ANF), Dycom
  (DY), Williams-Sonoma (WSM), Li Auto (LI), JM Smucker (SJM), Bath & Body
  Works (BBWI)
- Economic calendar: PCE/Core PCE, durable goods orders, Q2 GDP (2nd
  reading), MBA mortgage applications, personal income & spending — all
  8:30 ET; no CPI/PPI/FOMC decision today (CPI Aug 12, PPI Aug 13, FOMC
  minutes Aug 19 already out; next jobs report Sept 4)
- Sector momentum YTD: Energy still leader (+43.1%), Technology +25.4%,
  Materials +19.1%, Industrials +16.0%, Real Estate +14.1%, Consumer
  Staples +14.0%, Health Care +13.8%, Financials +7.2%, Utilities +2.6%;
  Consumer Discretionary -0.5% and Communication Services -4.0% both
  negative
- Held-ticker news (BAC): trading flat-to-slightly-up (~$62.4-62.5, +0.1-
  0.3% type moves); SEC subpoena/Situational Awareness probe story is
  now several days old and hasn't moved the stock; WSJ's $250B AI/energy
  infrastructure deployment and Jio Credit stake stories both already
  known. No thesis to break (mechanism-test position, no catalyst thesis
  to begin with) and no move near -7% — nothing urgent.

- Held-ticker news (BAC): no fresh catalyst-moving news — mixed-to-neutral
  flow (dividend hike and $250B AI/infrastructure financing push already
  known from 2026-08-25, some commentary on higher employee-benefit costs
  and AI-linked credit risk). Price flat near $62.4, well inside normal
  range. No thesis to break (mechanism-test position, no catalyst thesis
  to begin with) and nowhere near -7%; nothing urgent.

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| SJM | 0.487 | — (no champion) | 74.4 tech / 14.0 sector / 100 cat / 10 liq | Earnings today; top-scoring but below 0.55 minimum |
| WSM | 0.444 | — | 72.2 tech / 0.0 sector / 100 cat / 10 liq | Earnings today; 2nd by ensemble, negative-momentum sector |
| KSS | 0.337 | — | not evaluated | Earnings today (reported ~7am); below ensemble minimum |
| ANF | 0.263 | — | not evaluated | Earnings today; below ensemble minimum, negative-momentum sector |
| DY | -0.148 | — | not evaluated | Earnings today; negative ensemble, not evaluated |

| SJM | 0.487 | — (no champion) | 74.4 tech / 14.0 sector / 100 cat / 10 liq | Earnings today; top-scoring candidate |
| BBWI | 0.484 | — | 74.2 tech / -0.5 sector / 100 cat / 90 liq | Earnings today; close 2nd by ensemble |
| WSM | 0.444 | — | not evaluated | Earnings today; below top two, not run |
| KSS | 0.337 | — | not evaluated | Earnings today; below ensemble minimum, not run |
| ANF | 0.263 | — | not evaluated | Earnings today; below ensemble minimum, not run |
| DY | -0.148 | — | — | Earnings today; negative ensemble, not evaluated |
| LI | -0.544 | — | — | Earnings today; weakest scan, not evaluated |

### Trade Ideas
None. Ran `evaluate` on the top two by ensemble score:

- **SJM** — entry $133.46 / stop $128.66 / target $143.06 (R:R 2.0),
  NO-TRADE.
- **WSM** — entry $272.05 / stop $260.87 / target $294.41 (R:R 2.0),

- **SJM** — entry $138.59 / stop $133.79 / target $148.19 (R:R 2.0),
  NO-TRADE.
- **BBWI** — entry $17.68 / stop $15.96 / target $21.12 (R:R 2.0),
  NO-TRADE.

### NO-TRADE Candidates
- **SJM** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.49 below the validated
  minimum 0.55; spread/liquidity failed (spread 21.11%, illiquid or too
  wide).
- **WSM** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.44 below the validated
  minimum 0.55; spread/liquidity failed (spread 37.14%, illiquid or too
  wide).
- KSS, ANF, DY — not run through `evaluate`; KSS (0.337) and ANF (0.263)
  are both below the 0.55 ensemble minimum and sit in the
  negative-momentum Consumer Discretionary sector; DY (-0.148) carries a
  negative ensemble score driven by negative momentum/relative-strength —
  all three clearly weaker than SJM/WSM, no need to spend an evaluate
  call confirming a NO-TRADE on a worse setup.

### Risk Factors
- **Nvidia reports after today's close** — the month's single biggest
  market catalyst (~7.3% S&P weight, AI capex/demand read-through); no
  position here is exposed to that print directly (BAC is unrelated), but
  a large post-close move could move tomorrow's regime/sector-momentum
  reads materially. Nothing actionable pre-market today.
- **Both evaluated candidates failed on spread/liquidity** (21.1% SJM,
  37.1% WSM) on top of failing the ensemble-score minimum — genuinely
  pre-market timing (quotes pulled before the open), consistent with the
  same microstructure pattern noted on prior sessions, not a bug.
- **Today's earnings slate skews toward the negative-momentum Consumer
  Discretionary sector** (KSS, WSM, ANF, BBWI all report there) — sector
  momentum correctly penalized WSM's setup quality (sector score 0) even
  though its technicals (72.2) were solid; this is the filter working as
  designed, not a missed opportunity.
- **Breadth (0.724) was carried forward from yesterday's real print**,
  not independently re-sourced today (not part of today's Perplexity
  research queries) — flag for weekly review if this becomes a recurring
  shortcut rather than a one-off.

  minimum 0.55; spread/liquidity failed (spread 10.20%, illiquid or too
  wide).
- **BBWI** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.48 below the validated
  minimum 0.55; sleeve disagreement {momentum 0.777, trend 0.343,
  breakout 0.162, mean_reversion -0.304, relative_strength 0.694}.
- WSM, KSS, ANF, DY, LI — not run through `evaluate`; all scored below
  SJM/BBWI (WSM 0.444 down to LI -0.544), no need to spend an evaluate
  call confirming a NO-TRADE on a weaker setup.

### Risk Factors
- **Regime confidence held comfortably above the 0.40 minimum for a
  second consecutive session** (0.605/0.467 today vs. 0.872/0.797 on
  2026-08-25), after the five-session near-miss streak 2026-08-20 through
  2026-08-24. Worth continuing to watch at the next weekly review rather
  than treating two clean sessions as proof the earlier pattern is fully
  resolved.
- **Nvidia earnings after today's close is the market's real catalyst
  today** — none of today's pre-market earnings names (retail/consumer
  cluster) carry that kind of market-wide weight; today's own candidates
  are ordinary earnings-day setups, not systemically important.
- **Both evaluated candidates fail on the validated 0.55 ensemble-score
  minimum outright** (SJM 0.49, BBWI 0.48) — SJM additionally fails on a
  10.20% spread (genuinely pre-market timing) and BBWI on sleeve
  disagreement (mean_reversion -0.30 against four positive sleeves led by
  momentum +0.78). Neither is a borderline call.
- **No champion ML model exists** (`models/champion/` empty) — every
  candidate fails the ML-evidence gate regardless of setup. Expected,
  fail-safe, unchanged from prior runs.

### Decision
**HOLD** — no order placed, none staged. SJM and WSM are the only
candidates above zero and closest to tradeable but both fail the
ensemble-score minimum and spread/liquidity gates; KSS, ANF, DY all
weaker or negative-ensemble. Correct, expected outcome.

**HOLD** — no order placed, none staged. SJM and BBWI are the only
candidates above 0 ensemble but both fail the validated 0.55 minimum plus
an independent gate each (spread, sleeve disagreement); WSM/KSS/ANF all
below minimum, DY/LI negative-ensemble. Correct, expected outcome.

## 2026-08-27 — Pre-market Research (run inline from market-open — no earlier pre-market entry existed)

### Account
- Equity: $99,935.77 | Cash: $89,471.29 (89.5%) | Buying power: $387,185.70
  | Daytrade count: 0/4 (endpoint doesn't return the field; assumed 0)
- Positions: BAC 169 @ $62.30, current $61.92 (-0.61% intraday, -$64.22
  unrealized) — manual mechanism-test position, see 2026-08-24
  `TRADE-LOG.md` entry. Trailing 10% GTC stop confirmed live (hwm $62.58,
  stop $56.322, status "new").
- Open orders: 1 (the BAC protective trailing stop above)
- Trades this week (Mon 08/24-today): 1/3 (BAC, mechanism test, not a
  strategy signal)

### Market Context
- Regime: CHOPPY (confidence 0.745 with explicit `--vix 15.2`) / scan's
  own internal call showed STRONG_TREND (confidence 0.797, VIX
  unsupplied) — see `memory/REGIME-LOG.md` for the full score split
- WTI / Brent: ~$81.7-82.6 / ~$87.4-88.5, both modestly lower on the day
- S&P 500 futures / VIX: ES ~7,726 (+0.47-0.5%), Nasdaq futures +1.0-1.1%
  — Nvidia's post-close beat (shares +4%) is driving the premarket rally;
  VIX ~15.1-15.5, low-vol tape
- Today's catalysts: Nvidia follow-through (reported after yesterday's
  close, +4% premarket) is the dominant theme; Jackson Hole Symposium
  underway through 08/29 (Fed policy signals in focus); weekly initial
  jobless claims at 8:30am ET
- Earnings before open: Dollar General (DG), Darden Restaurants (DRI), TD
  SYNNEX (SNX), Acuity Brands (AYI), Commercial Metals (CMC), Winnebago
  (WGO), Best Buy (BBY), Dollar Tree (DLTR), Hormel (HRL), Build-A-Bear
  (BBW), Burlington (BURL), HealthEquity (HQY), Malibu Boats (MBUU),
  several Canadian banks (CM, RY, TD) and smaller/foreign names
- Economic calendar: weekly initial jobless claims 8:30am ET; no
  CPI/PPI/FOMC decision today (next CPI Sept 11, next PPI Sept 10)
- Sector momentum YTD: Energy +43.1% (leader), Technology +25.4%,
  Materials +19.1%, Industrials +16.0%, Real Estate +14.1%, Consumer
  Staples +14.0%, Health Care +13.8%, Financials +7.2%, Utilities +2.6%;
  Consumer Discretionary -0.5% and Communication Services -4.0% both
  negative
- Held-ticker news (BAC): no fresh catalyst-moving news — dividend hike
  (+14% to $0.32/sh) and Jio Credit JV both already known; regulatory
  headlines (Situational Awareness trade subpoenas, an insider-trading
  case involving a former banker) are noise, not new and not
  thesis-relevant (mechanism-test position, no catalyst thesis to begin
  with). Price -0.61% intraday, nowhere near -7%; nothing urgent.

### Candidate Scan (scripts/quant_cli.py scan)
| Ticker | Ensemble | ML Prob | Setup Quality | Notes |
|---|---|---|---|---|
| DLTR | 0.476 | — (no champion) | not evaluated | Earnings today; top by ensemble, but quote unusable (bid $122.61 / ask $0.00 — degraded data) |
| BBY | 0.474 | — | 73.7 tech / -0.5 sector / 100 cat / 10 liq | Earnings today; 2nd by ensemble |
| HRL | 0.291 | — | not evaluated | Earnings today; below ensemble minimum, not run |
| DG | 0.236 | — | not evaluated | Earnings today; below ensemble minimum, not run |
| BURL | -0.05 | — | not evaluated | Earnings today; negative ensemble, not evaluated |

### Trade Ideas
None. Ran `evaluate` on the top two by ensemble score:

- **DLTR** — could not evaluate: `_latest_quote` raised "no usable quote
  for DLTR (bid=122.61, ask=0.0) — market data may be degraded or
  stale," same pre-market microstructure pattern noted on prior sessions
  (see Risk Factors). No sizing possible; treated as NO-TRADE by
  necessity, not a scored rejection.
- **BBY** — entry $78.72 / stop $72.50 / target $91.16 (R:R 2.0),
  NO-TRADE.

### NO-TRADE Candidates
- **DLTR** — quote data unusable (bid $122.61 / ask $0.00); could not be
  scored. Ensemble (0.476) was itself already below the 0.55 validated
  minimum, so this would very likely have been NO-TRADE on ensemble
  score alone even with a clean quote.
- **BBY** — reasons, verbatim: no ML confirmation available
  (require_ml_probability=false); ensemble score 0.47 below the validated
  minimum 0.55; sleeve disagreement {momentum 0.639, trend 0.273,
  breakout 0.517, mean_reversion -0.551, relative_strength 0.465};
  spread/liquidity failed (spread 10.93%, illiquid or too wide).
- HRL, DG, BURL — not run through `evaluate`; HRL's own quote (bid $22.02
  / ask $25.38, ~14% spread) shows the same stale/degraded pre-market
  pattern as DLTR/BBY. All three score below BBY (HRL 0.291 down to BURL
  -0.05), no need to spend an evaluate call confirming a NO-TRADE on a
  weaker setup.

### Risk Factors
- **Quote data quality degraded across today's whole candidate set** —
  DLTR (bid/ask $122.61/$0.00), BBY (spread 10.93%), HRL (spread ~14%)
  all show stale or broken quotes, same pre-market-timing microstructure
  pattern flagged in prior sessions' logs. This blocked DLTR from being
  scored at all today, not just failed on spread — worth flagging at
  weekly review if this keeps recurring on the exact top candidate.
- **Nvidia's post-close beat is today's real market catalyst** (shares
  +4%, futures broadly higher) — no position here is exposed to it
  directly (BAC unrelated), and none of today's pre-market earnings names
  carry that kind of market-wide weight.
- **Today's earnings slate again skews toward the negative-momentum
  Consumer Discretionary sector** (BBY, DG, BURL, DLTR all report there;
  HRL is the lone Consumer Staples name) — consistent with the same
  sector pattern noted on 2026-08-25/08-26.
- **No champion ML model exists** (`models/champion/` empty) — every
  candidate fails the ML-evidence gate regardless of setup. Expected,
  fail-safe, unchanged from prior runs.
- **Regime call disagreement**: explicit `--vix 15.2` call returned CHOPPY
  (0.745 confidence, HIGH_VOL/CHOPPY split), while `scan`'s own internal
  call (no VIX supplied) returned STRONG_TREND (0.797). Both clear the
  0.40 NO-TRADE minimum so this didn't change any decision today, but the
  state label itself flipped between calls — flag for weekly review.

### Decision
**HOLD** — no order placed, none staged. DLTR (top by ensemble) couldn't
be scored on unusable quote data; BBY (2nd) fails the validated 0.55
ensemble minimum plus sleeve disagreement plus a 10.93% spread; HRL/DG/
BURL all weaker or negative-ensemble. Correct, expected outcome.
