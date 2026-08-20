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
