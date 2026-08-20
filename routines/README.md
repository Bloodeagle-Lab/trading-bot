# Cloud Routines

Five scheduled Claude Code cloud routines fire on a cron, one per workflow
below. Each firing is an **ephemeral container**: clone `main`, read
memory, pull live state, do the work, write memory, **commit and push
before exiting**. The container is then destroyed. If a run's changes
aren't in `main` when it exits, they never happened — that is the entire
memory model this bot runs on.

## One-time setup (do this once, before creating any routine)

1. **Install the Claude GitHub App** on this repo specifically (least
   privilege — don't grant it access to unrelated repos), or run
   `/web-setup` inside Claude Code to sync a `gh` CLI token with the same
   effect. This is what lets a cloud container clone and push to this repo.
2. **Enable "Allow unrestricted branch pushes"** in each routine's
   environment settings. Without this toggle, `git push origin main`
   silently fails with a proxy error — this is the single most common
   first-run break.
3. **Set environment variables on the routine itself — never in a `.env`
   file.** Each routine below lists exactly which ones it needs. A `.env`
   committed to the repo would leak secrets; one created at runtime is
   either a leak (if pushed) or wasted work (if not) — every prompt below
   has an explicit "do not create a `.env` file" instruction to prevent an
   agent from "helpfully" working around a missing variable that way.

## Creating a routine

1. In Claude Code cloud: Routines → New Routine.
2. Name it (e.g. "Trading bot pre-market").
3. Select this repository (requires the GitHub App from step 1) and branch
   `main`.
4. Add the environment variables the specific routine needs (see below).
5. Toggle on "Allow unrestricted branch pushes" (step 2 above).
6. Set the cron schedule and timezone from the table below.
7. Paste the routine's prompt from `routines/<name>.md` **verbatim** — copy
   everything in the file. Do not paraphrase; the environment-variable
   check and the commit/push steps are load-bearing, and a paraphrased
   prompt is the most common way an agent "helpfully" creates a `.env` file
   it shouldn't.
8. Save, then click **"Run now"** once and read the logs before trusting
   the schedule. Verify the relevant `memory/*.md` file was actually
   committed and pushed to `main` — check `git log origin/main`.

## Cron schedule (`America/Chicago` — adjust to your timezone)

| Routine | Cron | When |
|---|---|---|
| `pre-market` | `0 6 * * 1-5` | 6:00 AM weekdays |
| `market-open` | `30 8 * * 1-5` | 8:30 AM weekdays (market open) |
| `midday` | `0 12 * * 1-5` | Noon weekdays |
| `daily-summary` | `0 15 * * 1-5` | 3:00 PM weekdays (market close) |
| `weekly-review` | `0 16 * * 5` | 4:00 PM Fridays only |

## Environment variables per routine

| Variable | pre-market | market-open | midday | daily-summary | weekly-review |
|---|---|---|---|---|---|
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `ALPACA_BASE_URL` / `ALPACA_DATA_URL` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `TRADING_MODE` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `PERPLEXITY_API_KEY` (+ optional `PERPLEXITY_MODEL`) | ✓ | | optional | | ✓ |
| `CLICKUP_API_KEY` / `CLICKUP_LIST_ID` | ✓ | ✓ | ✓ | ✓ | ✓ |

`ALPACA_BASE_URL` defaults to the **paper** endpoint if unset
(`https://paper-api.alpaca.markets`) — see `memory/PROJECT-CONTEXT.md`'s
Production Gate before ever pointing this at the live endpoint.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Repository not accessible" / clone fails | GitHub App not installed | Install it, grant access to this repo |
| `git push` fails with a proxy/permission error | "Allow unrestricted branch pushes" is off | Enable it in the routine's environment |
| `ALPACA_API_KEY not set in environment` | Env var missing from routine config | Add it on the routine, not in `.env` |
| Agent creates a `.env` file anyway | Prompt was paraphrased | Re-paste the routine's `.md` file exactly |
| Yesterday's trades missing from today's run | Previous run didn't commit+push | Check `git log origin/main`; re-verify the routine's final commit step |
| Push fails "fetch first" / non-fast-forward | Another run pushed in between | The prompt handles this with `git pull --rebase`. If it loops, there's a real merge conflict — investigate manually |
| ClickUp notification didn't arrive | `CLICKUP_API_KEY`/`CLICKUP_LIST_ID` missing | `scripts/clickup.sh` silently falls back to `NOTIFICATIONS-FALLBACK.md` — check there, then add the missing vars |
| Perplexity calls didn't happen | `PERPLEXITY_API_KEY` missing | `scripts/perplexity.sh` exits 3; the agent falls back to WebSearch and notes it |
| `scripts/quant_cli.py` errors with "You must supply a method of authentication" | Alpaca credentials missing/wrong | Check `ALPACA_API_KEY`/`ALPACA_SECRET_KEY` on the routine |
| Alpaca rejects a stop with a PDT error | Same-day stop on a same-day buy | `scripts/quant_cli.py execute`'s fallback ladder (trailing → fixed → queue for tomorrow) handles this automatically — check the `stop_status` field in its output |
