---
description: Manual trade helper with full rule validation. Usage — /trade SYMBOL entry_price stop_price "catalyst reason"
---

Execute a manual trade with the exact same gate chain the automated
routines use — never construct an order from your own arithmetic here.

Args: `SYMBOL entry_price stop_price "reason"`. If any are missing, ask for
them — especially the reason, since `scripts/quant_cli.py evaluate` treats
`--catalyst-verified` as a hard gate and you should only pass it if there
really is a specific, verifiable catalyst.

1. Ask the user to confirm: is there a real catalyst, and are you
   comfortable with current portfolio concentration for this sector? Only
   pass `--catalyst-verified` / `--portfolio-concentration-ok` if genuinely
   true — this command will not talk you out of a NO-TRADE result, and it
   shouldn't.
2. Score and gate-check (does NOT place an order):
   ```
   python3 scripts/quant_cli.py evaluate SYMBOL --entry-price P --stop-price P \
     [--catalyst-verified] [--portfolio-concentration-ok] --sector-momentum-score N
   ```
3. Print the full result: regime, ensemble score, ML probability,
   `no_trade.decision` + reasons, and (if PASS) the proposed `sizing`.
4. If `no_trade.decision != "PASS"`, stop here — that is the answer. Do not
   override it.
5. If PASS, show the exact order that would be placed (shares, entry, stop,
   trailing stop %, risk dollars) and ask **"execute? (y/n)"**. Wait for
   confirmation — never place the order without it.
6. On "y": count this week's BUY entries in `memory/TRADE-LOG.md` for
   `--trades-this-week`, then:
   ```
   python3 scripts/quant_cli.py execute SYMBOL --shares <sizing.shares> \
     --entry-price P --stop-price P --reason "<catalyst>" \
     --trades-this-week N --approved-risk-dollars <sizing.risk_dollars>
   ```
7. Print the result. Append it to `memory/TRADE-LOG.md` in the file's
   existing format.
8. Send a notification: `bash scripts/clickup.sh "<trade summary>"`.
9. Ask the user whether to commit — local runs don't auto-commit. If yes:
   ```
   git add memory/TRADE-LOG.md
   git commit -m "manual trade SYMBOL $(date +%Y-%m-%d)"
   ```
   (push only if the user asks to.)
