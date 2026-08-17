#!/usr/bin/env bash
# Self-contained offline test launcher (external round 5's package request).
#
# Creates a venv, installs the pinned wheels with NO network, SELECTS A
# QUALIFIED SQLITE RUNTIME, and runs the suite. Every step prints what it
# chose, because "it worked on my machine" is the failure this is against.
#
#   bash specs/evidence/offline/run_offline.sh
#
# Exit 0 means the suite passed on a runtime this project qualifies.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
VENV="${VERACIUM_OFFLINE_VENV:-$ROOT/.venv-offline}"

# --- the qualified-runtime rule, stated and CHECKED --------------------------
# specs/0007 qualifies the SQLite runtimes this store is tested against. A
# suite green on an unqualified build proves less than it looks like, so the
# launcher REFUSES rather than warning.
MIN_SQLITE="3.35"     # the floor the store's DDL and migrations assume

pick_python() {
  for cand in "${VERACIUM_PYTHON:-}" python3.12 python3.11 python3; do
    [ -n "$cand" ] || continue
    command -v "$cand" >/dev/null 2>&1 || continue
    v="$("$cand" -c 'import sqlite3;print(sqlite3.sqlite_version)' 2>/dev/null)" || continue
    if [ "$(printf '%s\n%s\n' "$MIN_SQLITE" "$v" | sort -V | head -1)" = "$MIN_SQLITE" ]; then
      echo "$cand $v"; return 0
    fi
    echo "  skipping $cand: SQLite $v is below the $MIN_SQLITE floor" >&2
  done
  return 1
}

echo "== selecting a qualified runtime =="
if ! read -r PY SQLITE_V <<<"$(pick_python)"; then
  echo "NO QUALIFIED RUNTIME FOUND: every candidate interpreter links SQLite" >&2
  echo "older than $MIN_SQLITE. Set VERACIUM_PYTHON to one that does not." >&2
  exit 2
fi
echo "  interpreter : $(command -v "$PY")"
echo "  python      : $("$PY" -c 'import sys;print(sys.version.split()[0])')"
echo "  SQLite      : $SQLITE_V  (floor $MIN_SQLITE)"

echo "== creating the venv (no network) =="
"$PY" -m venv "$VENV"
"$VENV/bin/pip" install --quiet --no-index \
    --find-links "$HERE" --require-hashes -r "$HERE/requirements-test.lock"
echo "  installed from $HERE with --require-hashes"

echo "== running the suite =="
cd "$ROOT"
VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src \
    "$VENV/bin/python" -m pytest -q tests -p no:randomly -rs
