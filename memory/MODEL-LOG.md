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
specifically the ML layer.

## 2026-08-21 — Trained challengers v2 (10 years of data, two algorithms)

Two more attempts same day, same session, after extending
`scripts/train_champion.py`'s lookback from 750 to 2,500 trading days
(this account's data goes back to 2016 — ~10 years were available, not
just 3) and widening walk-forward to the originally-intended 24mo
train / 6mo test windows (15 windows, 543 OOS trades, vs. 2 windows/87
trades on the smaller dataset).

**v2_logi_20260821 (logistic_regression, 66,410 rows, 29 tickers,
2016-10-17:2025-11-24):** test_auc=0.532, test_brier=0.248 — more data
made it *worse*, not better. RETIRED, `model_quality` FAIL on both AUC and
Brier.

**v2_grad_20260821 (gradient_boosting, same dataset):** test_auc=0.556,
test_brier=0.139 — technically clears both the AUC floor (0.550) and the
Brier-vs-baseline check (0.142). **This is the run that exposed a real gap
in the two criteria added after the first attempt**: AUC/Brier only ask
"better than random" and "better than guessing the average" — neither
asks whether the model is good enough to make money at *this specific
strategy's* economics. Manual decile analysis on the held-out test set
showed the model's own best bucket (top 10% most-confident predictions)
had only a **20.8-20.9% realized win rate**, far short of the **33.3%**
breakeven this strategy's 2:1 reward:risk ratio requires. Every other
decile was worse. No probability threshold on this model corresponds to a
profitable edge.

**Fix applied**: added a fifth sub-check to `model_quality` —
`ModelMetadata` now records `win_r`, `loss_r`, and `top_decile_win_rate`
(the empirical win rate of the test set's most-confident 10%), and
`evaluate_promotion()` requires `top_decile_win_rate >= |loss_r| / (win_r
+ |loss_r|)` (+ optional `PromotionCriteria.min_edge_margin` for extra
slack). Re-ran v2_grad_20260821 through the corrected criteria:

```
- [PASS] min_out_of_sample_trades: 543 OOS trades (need >= 30)
- [PASS] max_drawdown_increase: no existing champion to compare against — skipped (bootstrap case)
- [PASS] regime_stability: no regime with >=5 trades shows negative expectancy
- [PASS] stress_resilience: expectancy drops 0.092R under combined worst-case stress (allowed up to 0.500R)
- [FAIL] model_quality: test_auc=0.557, test_brier=0.139, top_decile_win_rate=0.209 vs breakeven=0.333 (need >= 0.333)
```

Action taken: **RETIRED**, both v2 attempts. `models/champion/` remains
empty. Artifacts kept at `models/challengers/v2_logi_20260821.*` and
`v2_grad_20260821.*` for reference.

**Where this leaves things**: three attempts (v1, v2 logistic, v2 gradient
boosting), across 3 years and 10 years of data, two algorithms — none
found a probability bucket that clears this strategy's real breakeven win
rate. More data and a different off-the-shelf algorithm did NOT fix it.
That points toward the 22-feature technical/momentum/mean-reversion
feature set itself not containing enough signal for a 10-day, 2:1-R:R
prediction target, not toward "try the same approach again." A real next
attempt would need either materially different features (catalyst/news
signal, sector-relative or options-flow data — not just more of the same
technical indicators) or a reconsideration of the prediction target
(shorter/longer horizon, different R:R) — both real research work, not a
same-day retry. This is a legitimate, informative negative result, not a
failure to find something that was there to find.

## 2026-08-21 — Two more feature-engineering attempts, same day

Continued the same session after the v2 attempts above, on the theory that
raw technical indicators alone might be missing signal the system's own
richer composite calculations already capture.

**Attempt 3 — added sleeve/ensemble/regime features.** Extended
`research/build_training_data.py` to feed the model the five sleeve scores
(`quant/strategies.py`), the regime-weighted `ensemble_score`
(`quant/ensemble.py`), `regime_confidence`, and one-hot regime state
(`quant/regime.py`) — signals the system already computes but had never
been given to the model, only raw indicators. Result: test_auc=0.550,
top_decile_win_rate=0.211. Essentially unchanged. Makes sense in
hindsight — sleeve scores are deterministic recombinations of the same
raw indicators already in the feature set, not independent information.

**Attempt 4 — added cross-sectional peer rank.** Added
`cross_sectional_rank_ret20` / `cross_sectional_rank_ensemble`: each
ticker's percentile rank against the OTHER 28 tickers in the universe on
the SAME date, not just vs. SPY — meant to capture rotation/leadership
effects a single fixed benchmark comparison can't see. Result:
test_auc=0.548, top_decile_win_rate=0.213. Still unchanged.

**Stopping here for today, deliberately.** Four attempts — 2 data sizes ×
2 algorithms, plus composite features, plus cross-sectional rank — all
converge on the same result: AUC hovering 0.53-0.57, top-decile win rate
20-21%, never within reach of the 33.3% breakeven this strategy's 2:1 R:R
requires. Continuing to try more variations of the same
price/volume-derived feature family today would risk fishing for a result
that clears the bar by chance rather than genuine signal — exactly the
overfitting `research/backtest.py`'s own docstring warns against
("optimizing dozens of thresholds until the backtest looks attractive ...
a direct path to overfitting"). Four consistent negative results across
meaningfully different attempts is itself the finding: standard technical
indicators on large-cap liquid names, at this horizon and R:R, don't
appear to carry a tradeable edge with the methods tried so far. Real next
steps need a genuinely different data source (news/catalyst NLP,
fundamentals, options flow) or a fundamentally different prediction setup
— not another same-session retry.
