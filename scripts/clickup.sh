#!/usr/bin/env bash
# Notification wrapper. Creates a task in the configured ClickUp list (see
# env.template's "task/notification log" comment — this is the ClickUp v2
# Create Task API, not the Chat API, on purpose).
# Usage: bash scripts/clickup.sh "<markdown message>"
# Graceful fallback: if CLICKUP_API_KEY or CLICKUP_LIST_ID is missing, the
# message is appended to NOTIFICATIONS-FALLBACK.md at the repo root instead
# and the script exits 0 — the agent never crashes on missing notification
# credentials, and the fallback file is committed like any other memory so
# the notification history survives even without ClickUp configured.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"
FALLBACK="$ROOT/NOTIFICATIONS-FALLBACK.md"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ $# -gt 0 ]]; then
  msg="$*"
else
  msg="$(cat)"
fi

if [[ -z "${msg// /}" ]]; then
  echo "usage: bash scripts/clickup.sh \"<message>\"" >&2
  exit 1
fi

stamp="$(date '+%Y-%m-%d %H:%M %Z')"

if [[ -z "${CLICKUP_API_KEY:-}" || -z "${CLICKUP_LIST_ID:-}" ]]; then
  printf "\n---\n## %s (fallback — ClickUp not configured)\n%s\n" "$stamp" "$msg" >> "$FALLBACK"
  echo "[clickup fallback] appended to NOTIFICATIONS-FALLBACK.md"
  echo "$msg"
  exit 0
fi

# Task name = first line, truncated to a reasonable length; full message
# goes in the description so nothing is lost either way.
name="$(printf '%s' "$msg" | head -n1 | cut -c1-100)"

# Pick a working Python interpreter — see scripts/perplexity.sh's comment
# on why `command -v python3` alone isn't a reliable enough check.
PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done
: "${PYTHON_BIN:?no working python3/python interpreter found on PATH}"

payload="$("$PYTHON_BIN" -c "
import json, sys
print(json.dumps({'name': sys.argv[1], 'description': sys.argv[2]}))
" "$name" "$msg")"

curl -fsS -X POST "https://api.clickup.com/api/v2/list/$CLICKUP_LIST_ID/task" \
  -H "Authorization: $CLICKUP_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$payload"
echo
