#!/usr/bin/env bash
# Self-contained offline test launcher (external round 5's package request,
# corrected at round 6).
#
#   bash specs/evidence/offline/run_offline.sh
#
# Creates a venv, installs the pinned wheels with NO network, then asks the
# REPOSITORY whether this runtime is qualified — and REFUSES if it is not.
# Exit 0 means the suite passed on a runtime specs/0007 qualifies.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
VENV="${VERACIUM_OFFLINE_VENV:-$ROOT/.venv-offline}"
PY="${VERACIUM_PYTHON:-python3}"

# --- WHY THE ORDER IS VENV-FIRST ---------------------------------------------
# EXTERNAL ROUND 6, R6-4: v1 of this launcher invented its own rule — "SQLite
# >= 3.35" — and called anything above that floor qualified. Accepted spec 0007
# defines qualification as a COMPLETE RECORDED RUNTIME whose identity matches
# this process and whose recorded constructor manifestations REPRODUCE, and the
# repository already implements it: `runtime_supported()`. The reviewer
# measured v1 selecting SQLite 3.53.1, declaring it qualified, and producing
# 660 FAILED / 951 passed / 31 errors — while `runtime_supported()` returned
# False for that runtime. A launcher whose job is to refuse unqualified builds
# certified one instead.
#
# The predicate lives INSIDE the package and needs its dependencies, so it
# cannot be asked before the venv exists. v2 of this fix tried to ask first,
# rejected every candidate because `import veracium` failed with no pydantic,
# and hid the reason behind `2>/dev/null`. So: build the venv, THEN qualify,
# and never silence the answer.

# ROUND-21 PACKAGE NOTE (the reviewer's non-blocking recommendation): rerunning
# into an EXISTING venv reused its original interpreter while this script
# printed the newly requested one — `python -m venv` over an existing directory
# keeps the interpreter it was created with, so the qualification diagnostics
# described an interpreter that was not the one being qualified. An existing
# venv is REFUSED rather than reused; the marker file names what created it so
# the refusal can say so.
if [ -e "$VENV" ]; then
  echo "REFUSED: $VENV already exists." >&2
  if [ -f "$VENV/.created-by" ]; then
    echo "  created by: $(cat "$VENV/.created-by")" >&2
  fi
  echo "  Reusing it would qualify ITS interpreter while printing the one you" >&2
  echo "  just requested. Remove it, or set VERACIUM_OFFLINE_VENV to a fresh path." >&2
  exit 2
fi

echo "== creating the venv (no network) =="
echo "  interpreter : $(command -v "$PY")"
"$PY" -m venv "$VENV"
command -v "$PY" > "$VENV/.created-by"
"$VENV/bin/pip" install --quiet --no-index \
    --find-links "$HERE" --require-hashes -r "$HERE/requirements-test.lock"
echo "  installed from $HERE with --require-hashes"

echo "== qualifying the runtime (specs/0007's predicate, not a version floor) =="
cd "$ROOT"
QUAL_OUT="$(PYTHONPATH=src "$VENV/bin/python" - <<'PYQ' 2>&1 || true
import sqlite3, sys
try:
    from veracium.store.schema_version import runtime_supported
    ok = runtime_supported()
except Exception as e:                      # never silenced: the REASON matters
    print(f"UNAVAILABLE\t{sqlite3.sqlite_version}\t{type(e).__name__}: {e}")
    sys.exit(0)
print(f"{'YES' if ok is True else 'NO'}\t{sqlite3.sqlite_version}\t{ok!r}")
PYQ
)"
QUAL="$(printf '%s' "$QUAL_OUT" | cut -f1)"
SQLITE_V="$(printf '%s' "$QUAL_OUT" | cut -f2)"
DETAIL="$(printf '%s' "$QUAL_OUT" | cut -f3-)"
echo "  SQLite      : ${SQLITE_V:-unknown}"
echo "  qualified   : $QUAL  ($DETAIL)"

if [ "$QUAL" != "YES" ]; then
  cat >&2 <<MSG

REFUSING TO RUN: this runtime is NOT qualified.

  SQLite               : ${SQLITE_V:-unknown}
  runtime_supported()  : $DETAIL

This is a refusal, not a warning. Running the suite on an unqualified SQLite
build produces a number that LOOKS like a result and is not one — on the build
this launcher previously accepted, the reviewer measured 660 failures.

Set VERACIUM_PYTHON to an interpreter whose SQLite is recorded and reproduces
(specs/0007 defines what that means, and src/veracium/store/evidence/
sqlite_runtimes.json is the recorded set).
MSG
  exit 2
fi

echo "== running the suite =="
VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src \
    "$VENV/bin/python" -m pytest -q tests -p no:randomly -rs
