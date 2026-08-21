# Model Log

Every trained model (champion or challenger) and every champion/challenger
promotion decision, so any live prediction can be traced back to a specific
model version, training window, feature version, and threshold — PDF
section 6's requirement that "model version, training window, feature
version, threshold, and test results" travel with every prediction.

## Entry format (new model trained — `quant/model.py`'s `train_challenger`)

```
## YYYY-MM-DD — Trained challenger vX
- Algo: logistic_regression | gradient_boosting
- Feature version: X.X.X | Feature columns: [...]
- Train window: YYYY-MM-DD:YYYY-MM-DD | Validation window: YYYY-MM-DD:YYYY-MM-DD
- Threshold: 0.XX | Test AUC: 0.XX | Test Brier: 0.XX
- n_train: N | n_test: N
```

## Entry format (promotion decision — `research/promotion.py`'s `evaluate_promotion`)

```
## YYYY-MM-DD — Promotion evaluation: challenger vX vs champion vY
<paste PromotionDecision.summary_markdown() verbatim>

Action taken: PROMOTED to champion | RETIRED (challenger discarded)
```

---

## 2026-08-21 — Trained challenger v1_20260821

- Algo: logistic_regression
- Feature version: 1.0.0 | Feature columns: 22 technical/momentum/mean-reversion
  features from `research/build_training_data.py` (new this session — no
  prior tool built the feature+label dataset `quant/model.py` needs;
  `research/backtest.py` only records realized rule-based trades, not
  every day's setup)
- Universe: 28 liquid large-caps across sectors + SPY (`scripts/train_champion.py`)
- Train window: 2024-02-14:2026-04-10 (time-aware tail split, 20% held out)
- Threshold (starting point): 0.55
- Test AUC: 0.567 | Test Brier: 0.248 | train_positive_rate: 0.169
  (naive-baseline Brier = 0.169 × 0.831 = 0.139 — **this model's Brier score
  is worse than just always predicting the base rate.** AUC 0.567 is barely
  above random (0.5). This model has essentially no real predictive value
  on this dataset.)
- n_train: 12,528 | n_test: 3,132

## 2026-08-21 — Promotion evaluation: challenger v1_20260821 vs champion (none — bootstrap)

**First run (before this session's fixes) — decision: PROMOTE (incorrectly)**

The first evaluation passed all four criteria that existed at the time
(sample size, drawdown, regime stability, stress resilience) and promoted
this model despite its weak AUC/Brier above — because **none of those four
criteria evaluate the ML model itself**, only the rule-based sleeve
engine's realized trades. Caught by inspection, not by the promotion
mechanism, which is exactly the gap a deterministic gate is supposed to
close. Two fixes applied as a result:

1. Added a fifth `model_quality` criterion to `research/promotion.py`'s
   `evaluate_promotion()` — checks `test_auc` against a floor and
   `test_brier` against the naive constant-baseline Brier score
   (`positive_rate × (1 - positive_rate)`), computed from a new
   `ModelMetadata.train_positive_rate` field.
2. Found and fixed a real bug in `research/backtest.py` along the way: its
   `open_tickers` de-duplication set was declared but never populated — a
   complete no-op that let the backtest re-enter the same ticker with
   overlapping holding periods, and it never enforced
   `portfolio.max_positions`/`max_new_trades_per_week` at all. First run
   produced 544 "OOS trades" with -18% baseline drawdown; after the fix,
   the same data produces 87 trades with a -3.6% baseline drawdown — the
   544-trade number was never representative of what the live,
   cap-constrained strategy could actually do.

**Second run (after both fixes) — decision: RETIRE (correct)**

```
- [PASS] min_out_of_sample_trades: 87 OOS trades (need >= 30)
- [PASS] max_drawdown_increase: no existing champion to compare against — skipped (bootstrap case)
- [PASS] regime_stability: no regime with >=5 trades shows negative expectancy
- [PASS] stress_resilience: expectancy drops 0.093R under combined worst-case stress (allowed up to 0.500R)
- [FAIL] model_quality: test_auc=0.567 (need >= 0.550), test_brier=0.248 vs naive-baseline=0.139 (need <= 0.139)
```

Action taken: **RETIRED** (challenger discarded, not promoted).
`models/champion/` remains empty. Every live `evaluate` continues to
return `ml_probability: None` and NO-TRADE on "no champion model trained
yet" — correct, safe behavior. Challenger artifacts kept at
`models/challengers/v1_20260821.*` for reference, not deleted.

**Note on the rule-based engine itself** (separate from the ML model): with
the backtest fix applied, the underlying sleeve/ensemble/regime engine's
own OOS numbers look reasonably sound on this first pass — Monte Carlo
median return +2.2% (block-bootstrap, 5,000 runs), P(max drawdown > 15%)
= 0.1%, expectancy only drops 0.093R under combined worst-case stress. The
rule engine passed every criterion that actually tested it. The gap is
specifically the ML layer, which needs a real model-improvement pass
(more/better features, more data, trying gradient_boosting, addressing the
16.9% class imbalance) before another training attempt — not something to
retry today expecting a different result from the same approach.
