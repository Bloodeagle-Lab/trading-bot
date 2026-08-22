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
