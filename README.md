# Adaptive AI Quant Trading Bot v2

An autonomous, cloud-scheduled swing-trading agent for US equities, built
on Claude Code. Claude orchestrates research and workflow; a deterministic
Python engine (`quant/`) owns every number that touches sizing or order
placement. See `CLAUDE.md` for the agent's operating rules and
`memory/PROJECT-CONTEXT.md` for the full architecture.

**Status: pre-launch.** No routine has run against a live or paper Alpaca
account yet. Every threshold marked `VALIDATE` in `config/strategy.yaml`
is unresolved until backtesting produces evidence for it — see the
Production Gate in `memory/PROJECT-CONTEXT.md` before enabling
`TRADING_MODE=live`.

## Repository layout

```
trading-bot/
├── CLAUDE.md              # agent rulebook, auto-loaded every session
├── config/strategy.yaml   # every tunable threshold (VALIDATE-gated)
├── env.template           # copy to .env for local runs — never commit .env
├── .claude/commands/      # local slash commands (/portfolio, /trade, ...)
├── routines/              # cloud routine prompts — the production path
├── scripts/               # the only way to touch Alpaca/Perplexity/ClickUp
│   ├── alpaca.sh / perplexity.sh / clickup.sh   # thin bash API wrappers
│   └── quant_cli.py       # bridges routines to the quant/ decision engine
├── quant/                 # deterministic core: features, regime, sleeves,
│                           # ensemble, ML model, NO-TRADE, risk, execution
├── research/               # backtest, walk-forward, Monte Carlo, stress
│                           # test, champion/challenger promotion
├── models/                # champion/challenger model artifacts + metadata
├── memory/                 # git-committed durable state — the bot's only
│                           # memory between runs
├── state/                 # local, gitignored scratch cache (reconciled
│                           # from live Alpaca state every run)
└── tests/                 # pytest suite for quant/ and research/
```

## Local setup

1. **Python 3.11+** and a virtualenv:
   ```
   python -m venv .venv
   .venv/Scripts/activate      # Windows; use .venv/bin/activate on macOS/Linux
   pip install -r requirements.txt
   ```
2. Copy `env.template` to `.env` and fill in real credentials. `.env` is
   gitignored — it is never committed, and a cloud routine run must never
   create one (see `CLAUDE.md`).
3. Run the test suite:
   ```
   pytest
   ```
   All tests are self-contained (synthetic data, no network calls, no real
   credentials needed) and should pass before you trust anything else here.
4. Open the repo in Claude Code and try `/portfolio` — a read-only Alpaca
   account/positions/orders snapshot. If it prints cleanly, your `.env` is
   wired correctly.

## Cloud routines (the production path)

Five scheduled workflows fire on a cron, each an ephemeral cloud container:
clone `main`, read memory, pull live state, do the work, write memory,
**commit and push before exiting**. If it's not in `main`, it didn't
happen — that's the entire memory model.

One-time prerequisites (see `routines/README.md` for the full walkthrough):

1. Install the Claude GitHub App on this repo (least privilege — this repo
   only), or run `/web-setup` to sync a `gh` CLI token.
2. On each routine's environment, enable **"Allow unrestricted branch
   pushes"** — without it, `git push origin main` silently fails with a
   proxy error. This is the most common first-run break.
3. Set the environment variables listed in `CLAUDE.md`'s "Environment
   Variables" section on each routine directly — **not** in a `.env` file.
4. Paste each `routines/*.md` prompt verbatim into its routine's prompt
   field. Do not paraphrase — the environment-variable check and the
   commit/push steps are load-bearing.
5. Hit "Run now" on each new routine and read the logs before trusting the
   schedule. Verify the relevant `memory/*.md` file was actually committed
   and pushed.

Cron schedule (`America/Chicago`, adjust to your timezone):

| Routine | Schedule | When |
|---|---|---|
| `pre-market` | `0 6 * * 1-5` | 6:00 AM weekdays |
| `market-open` | `30 8 * * 1-5` | 8:30 AM weekdays (market open) |
| `midday` | `0 12 * * 1-5` | Noon weekdays |
| `daily-summary` | `0 15 * * 1-5` | 3:00 PM weekdays (market close) |
| `weekly-review` | `0 16 * * 5` | 4:00 PM Fridays only |

## Safety notes

- Paper trading (`TRADING_MODE=paper`, the default) until every box in
  `memory/PROJECT-CONTEXT.md`'s Production Gate is checked with actual
  evidence, not assumed.
- `quant/config.py` refuses to start in `live` mode while `ALPACA_BASE_URL`
  still points at the paper endpoint, as a second layer of protection
  beyond the `TRADING_MODE` switch itself.
- Read every commit the agent makes for at least the first week of paper
  trading — this is not a "set it and forget it" system on day one.
