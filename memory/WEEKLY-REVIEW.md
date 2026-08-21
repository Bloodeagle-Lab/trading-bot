# Weekly Review

Friday-afternoon recaps, appended here by the `weekly-review` routine. If a
rule proves itself for 2+ weeks or fails badly, `memory/TRADING-STRATEGY.md`
is updated in the same commit and the change is called out explicitly in
that week's entry below — never silently.

## Entry format

```
## Week ending YYYY-MM-DD

### Stats
| Metric | Value |
|---|---|
| Starting portfolio | $X |
| Ending portfolio | $X |
| Week return | ±$X (±X%) |
| S&P 500 week | ±X% |
| Bot vs S&P | ±X% |
| Trades | N (W:X / L:Y / open:Z) |
| Win rate | X% |
| Best trade | SYM +X% |
| Worst trade | SYM -X% |
| Profit factor | X.XX |
| NO-TRADE candidates logged | N |

### Closed Trades
| Ticker | Entry | Exit | R | P&L | Regime | Notes |
|---|---|---|---|---|---|---|

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|---|---|---|---|---|

### Regime Performance This Week
| Regime | Trades | Expectancy R | Notes |
|---|---|---|---|

### Model / Champion-Challenger
- Champion version in use: vX (see memory/MODEL-LOG.md)
- Challenger candidates evaluated this week: <none | vY — PROMOTE/RETIRE, see research/promotion.py decision>

### What Worked
- ...

### What Didn't Work
- ...

### Key Lessons
- ...

### Adjustments for Next Week
- <none | specific memory/TRADING-STRATEGY.md change, with the criterion that justified it>

### Overall Grade: X
```

---

## Week ending 2026-08-21

*First week of live paper trading (account created 2026-08-19; first
routine run 2026-08-20). Only two trading days of history exist
(2026-08-20 Thu, 2026-08-21 Fri) — treat all numbers below as a partial,
bootstrap week, not a full Mon-Fri sample.*

### Stats
| Metric | Value |
|---|---|
| Starting portfolio | $100,000.00 |
| Ending portfolio | $100,000.00 |
| Week return | $0 (0.00%) |
| S&P 500 week | -1.9% (FRED weekly series, week ending 2026-08-21) |
| Bot vs S&P | +1.9% (relative — no trades taken, no downside captured) |
| Trades | 0 (W:0 / L:0 / open:0) |
| Win rate | n/a — no closed trades |
| Best trade | n/a |
| Worst trade | n/a |
| Profit factor | n/a |
| NO-TRADE candidates logged | 9 (MRNA, MRVL, MRK ×2, DE, JNJ, BJ, BKE — some evaluated more than once across duplicate runs) |

### Closed Trades
| Ticker | Entry | Exit | R | P&L | Regime | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | none — zero trades placed this week |

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|---|---|---|---|---|
| — | — | — | — | — |

### Regime Performance This Week
| Regime | Trades | Expectancy R | Notes |
|---|---|---|---|
| STRONG_TREND | 0 | n/a | Every classification this week (2026-08-20 ×3, 2026-08-21) called STRONG_TREND, but confidence landed 0.32-0.392 — below the 0.40 minimum every single time, so the regime never actually gated a trade in either direction. Can't yet say whether the regime call itself was right. |

### Model / Champion-Challenger
- Champion version in use: **none trained yet** — `models/champion/` is empty.
- Challenger candidates evaluated this week: **4 attempts, all RETIRED** (see `memory/MODEL-LOG.md`, 2026-08-21):
  - `v1_20260821` (logistic regression, 3yr data) — RETIRED, `model_quality` FAIL (test_auc 0.567, test_brier 0.248 vs 0.139 baseline)
  - `v2_logi_20260821` (logistic regression, 10yr data) — RETIRED, worse than v1 (test_auc 0.532)
  - `v2_grad_20260821` (gradient boosting, 10yr data) — RETIRED, cleared AUC/Brier floors but `top_decile_win_rate` 0.209 vs 0.333 breakeven required
  - Composite-feature and cross-sectional-rank retries (same day) — RETIRED, test_auc 0.548-0.550, top-decile win rate 0.211-0.213, essentially unchanged
  - Net: four structurally different attempts converge on the same negative result — no ML edge found yet in this feature family at this horizon/R:R. `evaluate` continues to return NO-TRADE on "no ML probability" for every candidate, which is correct fail-safe behavior, not a bug.

### What Worked
- The NO-TRADE gate chain did its job end-to-end: every one of the 9
  logged candidates was correctly rejected (no champion model, regime
  confidence below minimum, wide/stale spreads, or setup quality) and zero
  bad orders reached execution.
- The promotion pipeline caught its own false positive: the first
  challenger evaluation would have wrongly promoted a model with no real
  edge, until a fifth `model_quality` criterion was added and a real bug
  in `research/backtest.py` (unenforced position caps, dead dedup set) was
  fixed in the same pass — self-correction before any capital was at risk.
- A quote-path bug (dead/stale quote degrading into a $0.00 entry price
  instead of erroring) was found, and by Friday's run had become a hard
  error instead of silently flowing downstream — verified directly against
  `alpaca.sh quote`.
- The `pre-market` cron timing bug (firing post-close on Thursday) was
  caught, and Friday's run fired genuinely pre-market (7:08 ET) — the fix
  held on its first re-test.
- Zero-trade weeks beat the index this week (0% vs -1.9%) simply by not
  having exposure — a reminder that patience is a real edge, not just a
  rule to tolerate.

### What Didn't Work
- Cloud routine git push was broken (403, no write access) for the very
  first run and lost that run's commit entirely — memory had to be
  reconstructed by hand. Resolved by the second run, but it's a fragile
  dependency worth watching for regressions.
- Regime confidence sat 0.32-0.392 against a 0.40 minimum in **all four**
  classifications this week, always on the same HIGH_VOL (0.55) vs
  STRONG_TREND (0.60) margin — a persistent near-miss, not noise, but only
  one week of evidence so far.
- Four separate ML modeling attempts (two data windows, two algorithms,
  plus two feature-engineering variants) all failed the same
  `top_decile_win_rate` / AUC bar — the current technical-indicator feature
  set has not produced a tradeable edge yet.
- The `pre-market` routine fired multiple times on 2026-08-20 (duplicate
  runs, one of them post-close), producing redundant/unusable log entries
  and unusable quotes for that day's evaluation.

### Key Lessons
- No live trade has been placed yet — the entire pipeline's real-money
  behavior is still unvalidated in production, only in backtest/paper
  gating logic. Every conclusion this week is about the gates working, not
  about strategy performance.
- The regime-confidence near-miss and the ML-edge gap are two independent,
  unrelated NO-TRADE causes (feature quality vs. classification
  calibration) — don't conflate them when deciding what to fix next.
- Infrastructure bugs (git push 403, quote 502 → $0.00, cron timing) are
  being caught fast because every run is logged and reviewed — keep that
  habit as trades start flowing.

### Adjustments for Next Week
- None to `memory/TRADING-STRATEGY.md` — this is the first week of data;
  per this routine's own rule, no change is made on less than 2 weeks of
  evidence. Watching two items for a second data point: (1) whether regime
  confidence keeps landing just under 0.40, and (2) whether cron
  duplicate-firing on 2026-08-20 recurs.

### Overall Grade: B

Infrastructure and risk gates behaved exactly as designed under real
(if quiet) conditions — three separate bugs were caught and fixed without
any capital ever being at risk, and the account is flat while the index
fell 1.9%. Held back from higher only because zero trades and zero
resolved infrastructure issues from a truly clean run means this week
proves the brakes work, not yet that the engine does.
