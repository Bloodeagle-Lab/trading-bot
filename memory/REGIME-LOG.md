# Regime Log

Daily regime state, confidence, and the supporting features that produced
them (`quant/regime.py`'s `RegimeResult`), so a bad week can be checked
against "was the regime engine wrong, or was the regime right and the
sleeves/sizing wrong" — the two failure modes need different fixes.

## Entry format (appended by `pre-market`, one per trading day)

```
## YYYY-MM-DD
- State: STRONG_TREND | CHOPPY | HIGH_VOL | RISK_OFF | TRANSITION
- Confidence: 0.XX
- Scores: {STRONG_TREND: 0.XX, CHOPPY: 0.XX, HIGH_VOL: 0.XX, RISK_OFF: 0.XX, TRANSITION: 0.XX}
- Trend (SPY/QQQ): X.XX / X.XX | Volatility (20d): X.XX | VIX: X.X | Breadth (%>50dma): X.XX
- Sleeve weights in effect today (from config/strategy.yaml's regime_weights): {...}
```

---

## 2026-08-20

*Reconstructed locally from the first cloud `pre-market` routine run's
reported summary — see `memory/RESEARCH-LOG.md`'s note on why the
routine's own commit was lost.*

- State: STRONG_TREND
- Confidence: 0.39
- VIX: 15.82 | SPX: ~7,689 (ES -0.28%)
- Full sleeve-score/feature breakdown not captured in the recovered
  summary — this entry is a partial reconstruction, not the routine's
  full original output.

## 2026-08-20 (second run, 20:09 UTC / 16:09 ET — post-close)

- State: STRONG_TREND
- Confidence: 0.392
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.584 / 0.587 | Volatility (20d): 0.1811 | VIX: 14.89 | Breadth (%>50dma): null (not obtainable from research sources)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: second `pre-market` firing of the day (first was 12:12 UTC).
  Same state and effectively the same confidence (0.39) as the morning
  run — confidence remains just below the 0.40 NO-TRADE minimum for the
  second consecutive classification.

## 2026-08-20 (post-close re-run, 16:10 ET)

Second `pre-market` routine firing for the same trading day, this one after
the close — logged separately rather than overwriting the 12:12 ET entry.

- State: STRONG_TREND
- Confidence: 0.39 (with `--vix 15.82` supplied) / 0.32 (scan's own call,
  VIX unsupplied) — both below the 0.40 NO-TRADE minimum
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.584 / 0.587 | Volatility (20d): 0.1811 | VIX: 15.82 | Breadth (%>50dma): not supplied
- Note: HIGH_VOL at 0.55 sitting just under STRONG_TREND's 0.60 is what
  keeps confidence below the minimum. Same pattern as the 12:12 ET run.

## 2026-08-21

- State: STRONG_TREND
- Confidence: 0.392 (with `--vix 15.72`)
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.584 / 0.587 | Volatility (20d): 0.1811 | VIX: 15.72 | Breadth (%>50dma): null (not obtainable from research sources)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: third consecutive near-miss of the 0.40 confidence minimum
  (2026-08-20 x2, now 2026-08-21), always on the same HIGH_VOL-vs-
  STRONG_TREND margin. Genuinely pre-market run this time (7:08 ET) —
  the earlier scheduling problem does not explain this one.

## 2026-08-22

- State: STRONG_TREND
- Confidence: 0.392 (with `--vix 15.4`) / 0.317 (scan's own call, VIX
  unsupplied) — both below the 0.40 NO-TRADE minimum
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.584 / 0.587 | Volatility (20d): 0.1811 | VIX: 15.4 | Breadth (%>50dma): null (not obtainable from research sources)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: fourth consecutive near-miss of the 0.40 confidence minimum
  (2026-08-20 x2, 2026-08-21, now 2026-08-22), always on the same
  HIGH_VOL-vs-STRONG_TREND margin.

## 2026-08-23 (Sunday — non-trading day, routine fired anyway)

- State: STRONG_TREND
- Confidence: 0.392 (with `--vix 15.13`)
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.584 / 0.587 | Volatility (20d): 0.1811 | VIX: 15.13 | Breadth (%>50dma): null
- Note: **fifth consecutive** identical confidence/feature print
  (2026-08-20 x2, 08-21, 08-22, now 08-23) — trend/volatility features
  are now confirmed byte-identical across four separate calendar dates.
  Combined with today being a Sunday, this run's classification should
  not be treated as a fresh read of market state — see
  `memory/RISK-LOG.md` for the stale-data-source finding.

## 2026-08-24

- State: STRONG_TREND
- Confidence: 0.392 (with `--vix 15.13`) / 0.317 (scan's own call, VIX
  unsupplied) — both below the 0.40 NO-TRADE minimum
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.589 / 0.585 | Volatility (20d): 0.1809 | VIX: 15.13 (Friday's close, no fresher print) | Breadth (%>50dma): null (not obtainable from research sources)
- Note: fifth consecutive near-miss of the 0.40 confidence minimum
  (2026-08-20 x2, 2026-08-21, 2026-08-22, now 2026-08-24), always on the
  same HIGH_VOL-vs-STRONG_TREND margin.

## 2026-08-24

- State: STRONG_TREND
- Confidence: 0.392 (with `--vix 16.01`) / 0.317 (scan's own call, VIX
  unsupplied) — both below the 0.40 NO-TRADE minimum
- Scores: {STRONG_TREND: 0.60, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.589 / 0.585 | Volatility (20d): 0.1809 | VIX: 16.01 | Breadth (%>50dma): null (not obtainable from research sources)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: fifth consecutive near-miss of the 0.40 confidence minimum
  (2026-08-20 x2, 2026-08-21, 2026-08-22, now 2026-08-24), always on the
  same HIGH_VOL-vs-STRONG_TREND margin. Run inline from `market-open`
  since no earlier pre-market entry existed for today.

## 2026-08-25

- State: STRONG_TREND
- Confidence: 0.872 (with `--vix 15.8`) / 0.797 (scan's own call, VIX
  unsupplied) — both clear the 0.40 NO-TRADE minimum comfortably, ending
  the five-session near-miss streak (2026-08-20 x2, 2026-08-21,
  2026-08-22, 2026-08-24)
- Scores: {STRONG_TREND: 0.85, CHOPPY: 0.00, HIGH_VOL: 0.00, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.598 / 0.559 | Volatility (20d): 0.1795 | VIX: 15.8 | Breadth (%>50dma): 0.724 (first real, non-null print — prior sessions all returned null)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: HIGH_VOL score dropped to 0.00 (from a steady 0.55 every prior
  session) — that's what pushed STRONG_TREND's confidence past the 0.40
  minimum, not a change in the STRONG_TREND score itself (0.85 today vs.
  0.60 prior, also up). Combined with breadth going from null to a real
  0.724, this looks like better upstream data today rather than a genuine
  regime shift — flag for weekly review to confirm it holds.

## 2026-08-26

- State: STRONG_TREND
- Confidence: 0.68 (with `--vix 15.7 --breadth 0.724`) / 0.605 (scan's own
  call, VIX unsupplied) — both comfortably clear the 0.40 NO-TRADE
  minimum, second session running after the five-session near-miss streak
  broke 2026-08-25
- Scores: {STRONG_TREND: 0.85, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.624 / n/a (QQQ trend not computed in this call) | Volatility (20d): 0.1819 | VIX: 15.7 | Breadth (%>50dma): 0.724 (carried forward from 2026-08-25's print, not independently re-sourced today — flag for weekly review)
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: confidence held near yesterday's level (0.68 vs 0.872 with VIX
  supplied) on the same STRONG_TREND (0.85) / HIGH_VOL (0.55) score split;
  regime read stable, not a fresh shift.

## 2026-08-27

- State: CHOPPY (explicit `--vix 15.2` call) / STRONG_TREND (scan's own
  internal call, VIX unsupplied) — the two calls disagree on state label
- Confidence: 0.745 (explicit `--vix 15.2`) / 0.797 (scan's own call) —
  both comfortably clear the 0.40 NO-TRADE minimum regardless of label
- Scores: {STRONG_TREND: 0.0, CHOPPY: 0.7, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0} (explicit call); scan's own call showed {STRONG_TREND: 0.85, CHOPPY: 0.0, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0}
- Trend (SPY/QQQ): 0.659 / -0.2 (explicit call) | 0.659 / null (scan's
  call) | Volatility (20d): 0.1563 | VIX: 15.2 | Breadth (%>50dma): 0.655
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: first session where the two regime calls disagree on state label
  (CHOPPY vs STRONG_TREND), not just confidence magnitude — driven by
  QQQ trend flipping negative (-0.2) in the explicit call vs null in
  scan's internal call. Confidence cleared 0.40 either way so no decision
  changed today, but flag for weekly review since this is a new pattern,
  not the near-miss-confidence issue from 2026-08-20 through 08-24.

- Confidence: 0.605 (scan's internal call, breadth 0.69) / 0.467 (explicit
  `--vix 15.68 --breadth 0.6` regime call) — both clear the 0.40 NO-TRADE
  minimum
- Scores: {STRONG_TREND: 0.85, CHOPPY: 0.00, HIGH_VOL: 0.55, RISK_OFF: 0.00, TRANSITION: 0.00} (explicit call); scan's own call showed HIGH_VOL 0.55 too but STRONG_TREND 0.85
- Trend (SPY/QQQ): 0.624 / 0.574 (QQQ null on scan's internal call) | Volatility (20d): 0.1819 | VIX: 15.68 | Breadth (%>50dma): 0.6-0.69 depending on call
- Sleeve weights in effect today: {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
- Note: second consecutive session clearing the 0.40 minimum comfortably
  (after 2026-08-25 broke the five-session near-miss streak). HIGH_VOL
  back up to 0.55 from 0.00 yesterday but STRONG_TREND's own score (0.85)
  stayed elevated, so confidence held above threshold either way. Run
  inline from `market-open` (STEPS 1-6 of `pre-market.md`) since no
  earlier `pre-market` entry existed for today.

## 2026-08-27

- State: **CHOPPY** (explicit `regime --qqq --vix 15.4` call) — first
  non-STRONG_TREND read since 2026-08-25 broke the near-miss streak.
  `scan`'s own internal call the same session returned **STRONG_TREND**
  instead (confidence 0.797); see Note below.
- Confidence: 0.745 (explicit call, CHOPPY) / 0.797 (scan's internal call,
  STRONG_TREND) — both clear the 0.40 NO-TRADE minimum regardless of which
  state is used
- Scores: {STRONG_TREND: 0.00, CHOPPY: 0.70, HIGH_VOL: 0.00, RISK_OFF: 0.00, TRANSITION: 0.00} (explicit call); scan's internal call: {STRONG_TREND: 0.85, CHOPPY: 0.00, HIGH_VOL: 0.00, RISK_OFF: 0.00, TRANSITION: 0.00}
- Trend (SPY/QQQ): 0.659 / -0.2 (explicit call, real negative QQQ trend) vs 0.659 / null (scan's internal call, QQQ trend not computed) | Volatility (20d): 0.1563 | VIX: 15.4 (explicit, real print) | Breadth (%>50dma): 0.655 both calls
- Sleeve weights actually applied in today's `scan`/`evaluate` calls:
  {momentum 1.0, trend 1.0, breakout 1.0, mean_reversion 0.0, relative_strength 0.8}
  — the STRONG_TREND weight set, because `scan`/`evaluate` use their own
  internal regime call, not the explicit step-4 call that classified today
  CHOPPY.
- Note: **state-level disagreement, not just a confidence gap** — the
  explicit call and scan's internal call disagree on the regime itself
  (CHOPPY vs STRONG_TREND), tracing to whether QQQ trend comes back null
  (scan) or a real -0.2 (explicit, with `--qqq` passed). Same shape as
  prior sessions' breadth-null-vs-real inconsistency, but here it flips
  the actual state, not just the confidence number, and it means today's
  sleeve weighting silently used STRONG_TREND weights on a session the
  routine's own step-4 classification called CHOPPY. Confidence cleared
  0.40 either way so no trade was blocked by it today, but flag for
  weekly review — root-cause why `--qqq` produces a real trend value on
  the explicit call but null internally in `scan`, before it matters on a
  day where the two states would gate differently.

## 2026-08-28

- State: CHOPPY
- Confidence: 0.745 (explicit `--qqq --vix 14.51` call, breadth
  auto-computed 0.690) — clears the 0.40 NO-TRADE minimum comfortably, but
  the **state** itself flipped from STRONG_TREND (held 08-25, 08-26) to
  CHOPPY
- Scores: {STRONG_TREND: 0.0, CHOPPY: 0.7, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0} (explicit call); `scan`'s own internal call (no `--vix`/`--qqq`) returned STRONG_TREND instead — {STRONG_TREND: 0.85, CHOPPY: 0.0, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0}, confidence 0.797
- Trend (SPY/QQQ): 0.683 / -0.198 (explicit call, real QQQ read) — SPY
  still trending up, QQQ now trending down; this divergence is what
  classified the day as CHOPPY | Volatility (20d): 0.1568 | VIX: 14.51 |
  Breadth (%>50dma): 0.690 (auto-computed from the live proxy universe,
  not independently re-sourced via Perplexity today)
- Sleeve weights: not applicable to the regime call itself; the candidate
  `scan` run used STRONG_TREND's weights {momentum 1.0, trend 1.0,
  breakout 1.0, mean_reversion 0.0, relative_strength 0.8} since its
  internal (no-VIX/QQQ) regime call still read STRONG_TREND
- Note: first CHOPPY classification in this log's history. Driven by a
  genuine QQQ trend reversal (-0.198, first negative QQQ trend print
  logged) rather than a VIX/breadth deterioration — VIX actually fell to
  14.51 from 15.21 the prior close. The explicit and scan-internal calls
  disagreed on **state**, not just confidence magnitude, for the first
  time (prior sessions only diverged on the confidence number) — flag for
  weekly review.

## 2026-08-31

- State: **STRONG_TREND**
- Confidence: 0.872 (explicit `--qqq --vix 15.27` call, breadth
  auto-computed 0.690) — clears the 0.40 NO-TRADE minimum comfortably;
  back to STRONG_TREND after 08-28's one-day CHOPPY read
- Scores: {STRONG_TREND: 0.85, CHOPPY: 0.0, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0} (explicit call); `scan`'s own internal call (no `--vix`/`--qqq`) also returned STRONG_TREND — {STRONG_TREND: 0.85, CHOPPY: 0.0, HIGH_VOL: 0.0, RISK_OFF: 0.0, TRANSITION: 0.0}, confidence 0.797 (no state disagreement today)
- Trend (SPY/QQQ): 0.721 / 0.653 (explicit call) — both trending up, QQQ
  back positive after 08-28's negative print | Volatility (20d): 0.1587 |
  VIX: 15.27 | Breadth (%>50dma): 0.690 (auto-computed from the live proxy
  universe, not independently re-sourced via Perplexity today)
- Sleeve weights: STRONG_TREND weight set applied in today's `scan`/
  `evaluate` calls — {momentum 1.0, trend 1.0, breakout 1.0,
  mean_reversion 0.0, relative_strength 0.8}
- Note: explicit and scan-internal calls agreed on both state and
  confidence direction today (0.872 vs 0.797, both STRONG_TREND) — the
  QQQ-trend-null-on-scan's-internal-call quirk flagged 08-27/08-28 is
  still present (scan's internal `trend_qqq` reads null again today), but
  it no longer matters for state since SPY's trend alone is enough to
  classify STRONG_TREND either way.
