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

---

## Week ending 2026-08-28

*Second week of live paper trading. One open position (BAC, manual
mechanism test opened 2026-08-24 — see that date's `TRADE-LOG.md` entry;
never scored by the strategy pipeline) carries through the whole week.
Zero strategy-scored trades were placed or closed. The dominant story
this week is not trading performance but a severe recurrence of the
session-branch git-persistence bug — see "What Didn't Work" — which
scattered the week's memory across 10+ unmerged branches; this review's
first task was reconstructing and merging the complete week before any
metric below could be trusted.*

### Stats
| Metric | Value |
|---|---|
| Starting portfolio | $100,000.00 (2026-08-21 EOD) |
| Ending portfolio | $100,014.36 (2026-08-28 EOD snapshot; live `positions` pull at review time showed $100,003.37, an intraday timing difference) |
| Week return | +$14.36 (+0.01%) |
| S&P 500 week | +0.64% (7,674.37 → 7,723.62, FRED/Investing.com, week ending 2026-08-28) |
| Bot vs S&P | -0.63% (relative — flat book sat out a rally; correct-per-rules NO-TRADE, not a losing trade) |
| Trades | 1 (W:0 / L:0 / open:1 — BAC carried in from 2026-08-24, manual mechanism test, not a strategy signal) |
| Win rate | n/a — no closed trades |
| Best trade | n/a — no closed trades (BAC open, +$14.37 / +0.14% unrealized at Friday close) |
| Worst trade | n/a — no closed trades |
| Profit factor | n/a — no closed trades |
| NO-TRADE candidates logged | 29 unique tickers across 9 research-log entries (AYI, SNX, DRI, PDD, XPEV, WGO, CMC ×08-24; BMO, BNS, DKS, VIPS, INTU ×08-25; SJM, WSM, KSS, ANF, DY, BBWI, LI ×08-26; DLTR, BBY, HRL, DG, BURL ×08-27; FRO, CHA, NVDA, BABA, MNSO ×08-28) — several days show duplicate research entries with the same candidates re-logged, a direct symptom of the persistence bug (a later session's fresh clone couldn't see an earlier same-day run's commit, so it redid the research). High count is expected, not a problem: not one candidate all week cleared the validated 0.55 ensemble minimum plus every independent gate — best was AYI at 0.598 on 08-24, blocked by sleeve disagreement. |

### Closed Trades
| Ticker | Entry | Exit | R | P&L | Regime | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | none — zero closed trades this week |

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|---|---|---|---|---|
| BAC | $62.30 | $62.385 (EOD snapshot) | +$14.37 (+0.14%) | 10% trailing GTC, live and confirmed all 5 sessions |

### Regime Performance This Week
| Regime | Trades | Expectancy R | Notes |
|---|---|---|---|
| STRONG_TREND | 0 (BAC's entry regime, 08-24 — bypassed the pipeline, not a regime-gated trade) | n/a | Confidence cleared the 0.40 minimum 08-25 (0.872) and 08-26 (0.68), ending the five-session near-miss streak from last week — first real evidence that streak was a VIX/breadth data-quality issue, not miscalibration. 08-24 was still a near-miss (0.392/0.317). |
| CHOPPY | 0 | n/a | New this week (08-27, 08-28) — both times the explicit `regime` step-4 call disagreed with `scan`'s own internal call on **state**, not just confidence (CHOPPY vs STRONG_TREND), tracing to `scan`'s internal QQQ trend coming back null instead of a real negative print. Confidence cleared 0.40 either way so no decision was mis-gated this week, but 08-27's sleeve weighting silently used the STRONG_TREND weight set on a session step-4 called CHOPPY — flagged in `memory/REGIME-LOG.md`, needs root-causing before it matters on a day the two states would actually disagree on a trade. |

No regime "worked" or "didn't work" in a P&L sense this week — every candidate in every regime failed the ensemble-score/spread/sleeve/catalyst gates before regime confidence or sizing ever became the deciding factor.

### Model / Champion-Challenger
- Champion version in use: **none trained yet** — `models/champion/` is empty, unchanged from last week.
- Challenger candidates evaluated this week: **none** — no `research/promotion.py` run this week; `memory/MODEL-LOG.md`'s only entries remain the four 2026-08-21 RETIRED attempts from last week.

### What Worked
- The NO-TRADE gate chain held for a second straight week: 29 logged
  candidates, zero bad orders reached execution. Several genuine
  near-misses (AYI 0.598, BMO 0.591, SJM 0.487, DLTR/BBY ~0.475) were all
  correctly rejected on an independent gate (spread, sleeve disagreement,
  unverified catalyst, data-quality error) even where ensemble alone
  looked closest yet to tradeable.
- BAC's protective stop stayed live and correct through all 5 sessions
  (`quant_cli.py positions` `flags` empty every day) — the mechanism-test
  position keeps proving the execution/stop path works end-to-end in
  production, not just in theory.
- Regime confidence cleared the 0.40 NO-TRADE minimum on 4 of 5 sessions
  (08-25 through 08-28), breaking last week's five-session near-miss
  streak — first real second-week evidence that the near-miss pattern was
  driven by weekend-stale VIX/null-breadth data, not a fundamental
  regime-engine miscalibration.
- Despite a severe git-branch fragmentation event, no memory was
  permanently lost — every day's research, regime, and trade data was
  eventually recovered (across three separate in-session recovery efforts
  plus this review's final consolidation) rather than silently dropped.

### What Didn't Work
- **The 2026-08-25 "RESOLVED" session-branch persistence fix did not
  hold** — it recurred at least three more times this week (08-26,
  08-27 ×2, 08-28), scattering commits across 10+ never-merged
  `main-xxxxxx` branches (`main-mayo40`, `main-a5zz3r`, `main-x7uq6d`,
  `main-uvj7u8`, `main-uhy3i7`, `main-g63v2n`, `main-gkfsno`,
  `main-kgb03t`, `main-2mxr6t`, plus this session's own `main-llkola`).
  Reconstructing a complete week required this review to `git fetch
  --prune` the full remote, diff every stray branch against `main`, and
  manually merge two divergent recovery chains — a fresh clone that
  skipped this step would have silently graded the week on an incomplete,
  three-day-stale picture (as 08-28's own `daily-summary` run did, before
  this review corrected it). This is now a third distinct "fix"/"reopen"
  cycle on the same root cause in one week — see `memory/RISK-LOG.md`'s
  2026-08-28 entries for the full account and the escalation.
- **A new regime state-disagreement bug** (not just a confidence gap):
  `scan`'s internal regime call and the explicit step-4 `regime` call
  returned different **states** (STRONG_TREND vs CHOPPY) twice this week,
  traced to `scan`'s internal QQQ trend value coming back null instead of
  real. Didn't change a decision this week only because confidence
  cleared 0.40 under both states — a coin flip away from mattering.
- Zero ML edge remains unchanged from last week — no champion model,
  every decision still running on the `require_ml_probability=false`
  ensemble/regime fallback from the 2026-08-21 exception.
- Second straight week with zero strategy-scored trades placed — the bot
  underperformed the S&P 500 by 0.63pp this week purely by holding cash
  through a rally. Correct per the strategy's own filters (nothing
  cleared 0.55 ensemble plus every independent gate), but two quiet weeks
  running means "does the engine find real edges" is still untested, not
  just "do the brakes work."

### Key Lessons
- The persistence bug lives at a layer no session can see or fix from
  inside its own sandboxed clone — every routine's own `git push origin
  main` instruction has been correct the whole time; something in the
  trigger config (or layered on top of it) keeps reassigning a per-run
  branch regardless. A fourth in-session "fix" attempt next week without
  a human checking the routines API/UI directly is expected to reproduce
  the same result — this needs to stop being a routine's job to
  discover and start being a routine's job to merely flag.
- "No stranded branches visible" is not evidence of no stranded branches
  — 08-28's `daily-summary` session concluded routines simply hadn't
  fired, from a `git branch -a` that only reflected its own shallow
  fetch. `git fetch --prune` against the full remote was required to see
  the other 9 branches. Any future persistence-diagnosis session should
  fetch-prune first, not trust a local branch listing.
- Regime state disagreement (not just confidence magnitude) is a more
  dangerous version of the previously-logged null-vs-real breadth/QQQ
  inconsistency — it silently changes which sleeve weights apply. Worth
  root-causing now, while it hasn't yet flipped an actual trade decision,
  rather than after it does.

### Adjustments for Next Week
- None to `memory/TRADING-STRATEGY.md` — nothing here is a trading-rule
  result; this week's evidence is entirely infrastructure (git
  persistence, regime-call state disagreement), which this file
  deliberately doesn't govern. Two non-strategy follow-ups carried
  forward instead: (1) a human needs to check all 5 routines'
  `outcomes[0].git_repository.git_info` config directly via the routines
  API/UI — a third in-session patch attempt is not expected to hold any
  better than the first two; (2) root-cause why `scan`'s internal regime
  call returns a null QQQ trend where the explicit `--qqq` call returns a
  real one, before it lands on a day where the two states disagree on an
  actual trade decision.

### Overall Grade: C+

Trading discipline held for a second week — every one of 29 candidates
was correctly filtered, the one live position's stop never lapsed, and
the regime engine's confidence calibration looks meaningfully better than
last week's five-session near-miss streak. Held down from a B by a
serious, recurring operational failure: the exact persistence bug this
file's own predecessor review flagged for escalation came back three
separate times in five trading days, at one point leaving a full day's
data invisible to the routine that needed it, and was only fully
reconciled by this review's manual archaeology rather than by the fix
that was supposed to have already landed. Zero strategy-driven trades for
a second straight week, against a rallying index, is a legitimate
NO-TRADE outcome under the rules — but it also means the strategy's
actual edge remains as unproven as it was last week.
