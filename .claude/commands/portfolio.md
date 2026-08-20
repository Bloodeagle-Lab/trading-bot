---
description: Read-only snapshot of account, positions, open orders, and stops
---

Print a clean ad-hoc portfolio snapshot. No state changes, no orders, no
file writes.

1. Run:
   ```
   python3 scripts/quant_cli.py positions
   ```
2. Format the output as a single concise summary:
   ```
   Portfolio — <today's date>
   Equity: $X | Cash: $X | Buying power: $X | Daytrade count: N/4

   Positions:
     SYM | Sh | Entry -> Current | Unrealized P&L | Stop
   ```
3. If the result's `flags` list is non-empty, print every flag verbatim
   right after the positions table — a position with no protective stop
   order is the one thing that must never be silently skipped.

No other commentary. If `scripts/quant_cli.py` returns an `{"error": ...}`
object (e.g. missing/invalid credentials in `.env`), print that error
plainly and stop — do not retry or guess a workaround.
