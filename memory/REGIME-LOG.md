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
