#!/usr/bin/env bash
# UserPromptSubmit hook: remember what the user typed, in a detached background
# process so LLM extraction (~seconds) never blocks the conversation.
# stdin: the hook's JSON payload; .prompt is the user's message.
set -euo pipefail

DB="${VERACIUM_DB:-$HOME/.veracium/claude-code.db}"
USER_ID="${VERACIUM_USER:-$USER}"

PROMPT="$(jq -r '.prompt // empty' 2>/dev/null || true)"
# Skip empties and bare slash-commands — command names are noise, not memories.
if [ -z "$PROMPT" ] || [[ "$PROMPT" == /* && "$PROMPT" != *" "* ]]; then
  exit 0
fi

mkdir -p "$(dirname "$DB")"
printf '%s' "$PROMPT" | nohup veracium remember --user "$USER_ID" --db "$DB" - \
  >/dev/null 2>&1 &
