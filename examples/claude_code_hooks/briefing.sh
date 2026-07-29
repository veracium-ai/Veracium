#!/usr/bin/env bash
# SessionStart hook: print the proactive briefing; Claude Code injects stdout
# as session context. Store-only — no provider, no tokens, no network.
set -euo pipefail

DB="${VERACIUM_DB:-$HOME/.veracium/claude-code.db}"
USER_ID="${VERACIUM_USER:-$USER}"

mkdir -p "$(dirname "$DB")"
BRIEFING="$(veracium recall --user "$USER_ID" --db "$DB" 2>/dev/null || true)"
if [ -n "$BRIEFING" ]; then
  echo "## Veracium memory briefing for $USER_ID"
  echo "$BRIEFING"
fi
