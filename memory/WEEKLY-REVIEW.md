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

## Week ending 2026-09-04

*Third straight week of live paper trading with zero strategy-scored
trades — BAC (manual mechanism test, opened 2026-08-24, never scored by
the pipeline) is again the only position, carried through the whole week
untouched. This week's two real stories are both infrastructure, not
strategy: (1) the session-branch persistence bug not only recurred an
eighth-plus time but got structurally worse — for the first time, two
same-day sessions (pre-market and market-open, both 09-04) independently
wrote genuinely conflicting content to the same files, requiring this
review to hand-resolve real 3-way merge conflicts rather than just
fast-forward stray branches; and (2) the `--qqq`-null-on-scan/evaluate
regime-visibility bug, flagged as a cosmetic confidence-magnitude quirk
since 08-27, escalated to a full state disagreement (TRANSITION vs
STRONG_TREND, not just a confidence gap) on two separate days this week.
This review's first task, as the last two reviews', was reconstructing
the complete week from four more unmerged stray branches before any
metric below could be trusted.*

### Stats
| Metric | Value |
|---|---|
| Starting portfolio | $100,014.36 (2026-08-28 EOD, prior Friday) |
| Ending portfolio | $100,060.83 (2026-09-04 EOD snapshot; live `positions` pull at review time showed $100,064.21, an intraday timing difference) |
| Week return | +$46.47 (+0.05%) |
| S&P 500 week | +0.19% (7,711.76 → 7,726.14, FRED/Investing.com daily closes, week ending 2026-09-04) |
| Bot vs S&P | -0.14% (relative — flat book underperformed a roughly-flat index; correct-per-rules NO-TRADE, not a losing trade) |
| Trades | 1 (W:0 / L:0 / open:1 — BAC carried in from 2026-08-24, manual mechanism test, not a strategy signal) |
| Win rate | n/a — no closed trades |
| Best trade | n/a — no closed trades (BAC open, +$64.22 / +0.61% unrealized at Friday live pull) |
| Worst trade | n/a — no closed trades |
| Profit factor | n/a — no closed trades |
| NO-TRADE candidates logged | 29 unique tickers across 7 research-log entries (NAT, SAIC, PDD, FRO, NSSC ×08-31; DELL, MDB, MDT, NIO, ASO ×09-01 scheduled; MRVL, PLTR, CVX, XOM, HAL ×09-01 market-open inline; GIII, DRI, BF.A, CMC, OLLI ×09-02; HPE, AVGO, CIEN, TSLA, LULU ×09-03; AYI, WGO, SNX, DRI, CMC ×09-04 pre-market; SNOW, HPE, PLTR ×09-04 market-open). High count is expected, not a problem — but notable this week: **DELL (0.553, 09-01) and SNOW (0.589, 09-04) are the first two candidates in this log's history to clear the validated 0.55 ensemble minimum**, and both were still correctly rejected — DELL on a degraded/stale pre-market quote (data quality, not strategy), SNOW on sleeve disagreement plus spread/liquidity (8.94%, above the 6% paper-mode cap). The gate chain is holding even as candidates get closer. |

### Closed Trades
| Ticker | Entry | Exit | R | P&L | Regime | Notes |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | none — zero closed trades this week |

### Open Positions at Week End
| Ticker | Entry | Close | Unrealized | Stop |
|---|---|---|---|---|
| BAC | $62.30 | $62.66 (EOD snapshot) | +$60.84 (+0.37%*) | 10% trailing GTC, live and confirmed all 5 sessions |

*EOD Day-Chg figure is vs. the stale 09-02 close (09-03's snapshot wasn't
visible to that session before this review's recovery merge); the live
Friday pull shows +0.61% / +$64.22 against true entry.

### Regime Performance This Week
| Regime | Trades | Expectancy R | Notes |
|---|---|---|---|
| STRONG_TREND | 0 (BAC's entry regime, 08-24, predates this week and bypassed the pipeline) | n/a | 4 of 7 sessions (08-31, 09-01 ×2, 09-03), confidence 0.66-0.872, comfortably clear of the 0.40 minimum. Closest-ever candidates (DELL 0.553, HPE 0.37) still surfaced under this regime — no candidate cleared every independent gate. |
| TRANSITION (sub-0.40, NO-TRADE-by-regime) | 0 | n/a | **New and escalating**: 3 of 7 sessions (09-02, 09-04 pre-market, 09-04 market-open — 2 of 5 trading days), confidence 0.30 each time, all below the 0.40 minimum. First-ever occurrence was 09-02 (this log's history); this week alone repeated it twice more. `scan`/`evaluate`'s internal regime call couldn't see any of the three (still reads STRONG_TREND 0.797-0.85), meaning the pipeline ran on the wrong sleeve-weight set on 2 of 5 trading days this week. Didn't flip an actual decision only because no candidate cleared the 0.55 ensemble minimum on either NO-TRADE-by-regime day — a coincidence, not a safeguard. |

Can't yet separate "regime engine right, sizing/sleeves wrong" from
"regime engine wrong" — no candidate on any TRANSITION day got far enough
into the pipeline to test sizing. What's newly testable: 09-04's
TRANSITION read coincided with a genuinely calm tape (VIX at a multi-week
low ~14.2-14.3, market near highs after Thursday's 627-pt Dow rally) purely
because QQQ's trend flipped negative against a positive SPY — worth
watching whether this SPY/QQQ-divergence pattern is a real early-warning
signal (a rotation out of tech) or the regime engine being oversensitive
to a single input; three negative-QQQ prints since 08-28 (08-28, 09-02,
09-04) is now a pattern, not a one-off.

### Model / Champion-Challenger
- Champion version in use: **none trained yet** — `models/champion/` is empty, unchanged since 2026-08-21.
- Challenger candidates evaluated this week: **none** — no `research/promotion.py` run this week; `memory/MODEL-LOG.md`'s entries remain the four 2026-08-21 RETIRED attempts.

### What Worked
- The NO-TRADE gate chain held for a third straight week under real
  pressure: 29 logged candidates, and for the first time two of them
  (DELL 0.553, SNOW 0.589) cleared the validated 0.55 ensemble minimum
  outright — both were still correctly stopped by an independent gate
  (data quality, sleeve disagreement/spread) rather than the ensemble
  score alone waving them through. This is the system's first real test
  of "what happens when a candidate gets close" and it held.
- BAC's protective stop stayed live and correct through all 5 sessions
  (`quant_cli.py positions` `flags` empty every day) for a third
  consecutive week — the mechanism-test position keeps proving the
  execution/stop path end-to-end.
- Despite a materially worse persistence incident this week (see below),
  no memory was permanently lost — all four newly-discovered stray
  branches (`main-qtxeug` 09-03 EOD, `main-fzz3ks` 09-04 pre-market,
  `main-jxv1et` 09-04 market-open, `main-oo16eh` 09-04 EOD) were
  recovered and merged, including a real 3-file conflict, with nothing
  discarded.
- Regime confidence correctly identified two distinct real risk events
  this week (09-02's Iran-strike oil spike, and a genuine — if more
  ambiguous — SPY/QQQ divergence on 09-04) rather than a data artifact;
  both readings were internally consistent with the day's actual market
  action.

### What Didn't Work
- **The persistence bug got structurally worse, not just longer-running.**
  Every prior week's stray-branch recoveries were pure fast-forwards —
  no session had actually created conflicting content before. This week,
  `main-fzz3ks` (pre-market) and `main-jxv1et` (market-open) both
  appended different, non-identical "2026-09-04" sections to the same
  spot in `REGIME-LOG.md` and `RESEARCH-LOG.md` from the same stale base,
  and `main-qtxeug`/`main-oo16eh` did the same in `TRADE-LOG.md`,
  requiring this review to hand-merge real conflicts rather than just
  `git merge --ff`. Same still-unresolved root cause flagged since
  2026-08-20 (routines API/UI `outcomes[0].git_repository.git_info`) —
  now well past a "third in-session fix attempt won't hold" prediction
  and squarely a "will cause a real, non-recoverable divergence
  eventually" risk if a future week's conflicting entries are ever
  substantively different (e.g. two different trade decisions) rather
  than two research sessions reaching the same HOLD.
- **The `--qqq`/regime-visibility bug escalated from cosmetic to
  material, twice.** 09-02 and 09-04 both saw `scan`/`evaluate`'s
  internal regime call disagree with the explicit call on *state*
  (STRONG_TREND vs TRANSITION), not just confidence magnitude — meaning
  the pipeline used the wrong sleeve-weight set on 2 of 5 trading days
  this week. Neither day happened to have a candidate clear the ensemble
  bar, so no bad trade resulted, but "didn't matter yet" is now true for
  three consecutive weeks running (08-27/08-28, 09-02, 09-04) on a bug
  that's getting more consequential each time it recurs, not less.
- Third straight week with zero strategy-scored trades — the bot
  underperformed the S&P 500 by 0.14pp this week. Unlike the prior two
  quiet weeks, this week did produce two candidates that cleared the
  ensemble minimum (DELL, SNOW), which is genuine evidence the scoring
  engine can find something — but both were still blocked before
  execution, so "does the engine convert a real edge into a filled trade"
  remains untested after three weeks.
- Two sessions this week (09-04 pre-market and market-open) each
  independently believed they were the *first* pre-market run of the day
  because neither could see the other's stray branch — a direct
  consequence of the persistence bug, not a new failure mode, but worth
  naming: it means "no earlier entry existed" claims in this log cannot
  be trusted at face value without a fetch-prune check first.

### Key Lessons
- A recurring bug that has caused no P&L damage yet is not the same as a
  bug with no consequence — this week is the first time both standing
  infrastructure issues (persistence, regime-visibility) came within one
  coincidence (no candidate clearing the ensemble bar on the affected
  days) of actually mattering. Two "it didn't matter this time" weeks in
  a row is exactly the setup for a week where it does.
- The persistence bug's failure mode has changed shape: fast-forward
  recovery (safe, mechanical) has become 3-way conflict recovery
  (requires judgment about which content to keep). That's a meaningfully
  higher-stakes ask of whichever session next discovers it, and argues
  for escalating this past "flag it again" toward "a human should treat
  this as a standing production incident," not routine noise.
- SPY/QQQ trend divergence (three negative QQQ prints since 08-28) may be
  a real, recurring signal rather than noise — worth tracking explicitly
  rather than re-discovering it as a surprise each time regime confidence
  drops.

### Adjustments for Next Week
- None to `memory/TRADING-STRATEGY.md` — nothing this week is a
  trading-rule result; both real findings are infrastructure (git
  persistence, regime-call state disagreement), which this file
  deliberately doesn't govern. Non-strategy follow-ups carried forward,
  with the first two now overdue for direct human attention rather than
  another routine-level flag: (1) a human needs to check all 5 routines'
  `outcomes[0].git_repository.git_info` config directly via the routines
  API/UI — now an eighth-plus occurrence with a real conflict this week,
  not just a missed fast-forward; (2) wire a `--qqq` (or equivalent
  real-trend) input through to `scan`'s and `evaluate`'s internal
  `regime` call, not just the standalone `regime` subcommand's `--vix`/
  `--breadth` flags — this is a `quant_cli.py` code change, not
  something fixable from within a routine, and has now caused a full
  state disagreement (not just confidence) on 2 of the last 3 weeks;
  (3) new this week — keep watching the SPY/QQQ divergence pattern (3
  negative QQQ prints since 08-28) as a possible real signal rather than
  noise.

### Overall Grade: C

One notch down from last week's C+, not because trading discipline
slipped — it didn't: every one of 29 candidates was correctly filtered,
including the two closest calls this log has ever seen (DELL, SNOW), and
BAC's stop never lapsed across a third straight week. The downgrade is
because both standing operational risks flagged in the last two reviews
got worse in a way that matters, not just longer in duration: the
persistence bug produced its first real multi-file merge conflict instead
of a clean fast-forward, and the regime-visibility bug caused a full
state disagreement (not just a confidence gap) on two separate days,
either of which could plausibly have masked a bad trade decision if a
candidate had cleared the ensemble bar on the wrong day — it simply
didn't happen to this week. Zero strategy-driven trades for a third
straight week is a legitimate, rules-correct NO-TRADE outcome, and two
candidates finally clearing the ensemble minimum (a first) is real
evidence the engine can find something — but the operational risk
underneath the strategy is now large enough that it, not the strategy
itself, is this review's central finding.
