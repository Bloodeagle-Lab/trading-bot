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

No entries yet. `models/champion/` is empty — every live decision currently
runs with `ml_probability: None` ("no champion model trained yet — treat as
insufficient evidence"), which `quant/no_trade.py` handles explicitly and
safely, not as a coin flip. Training the first champion is a Phase 9/10
activity, not something a daily routine does automatically.
