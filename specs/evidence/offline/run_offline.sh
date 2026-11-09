#!/usr/bin/env bash
# Self-contained offline test launcher (external round 5's package request,
# corrected at round 6).
#
#   bash specs/evidence/offline/run_offline.sh [pytest arguments...]
#
# Any arguments are passed to pytest unchanged, after the launcher's own. Two a reviewer will want (round 11; see
# README.md beside this script): --basetemp=<a directory OUTSIDE the package tree but on the SAME filesystem> — one
# test hard-links a file of the tree into its tmp_path, which a tmp on another filesystem cannot do — and
# --junitxml=<file>, the same run's machine-readable result.
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

# IMPORT PREFLIGHT (0048 round 1's package note): the reviewer's own CPython build lacked `_ctypes`, and the suite
# found out partway through a long run. Every compiled standard-library module this launcher's own run loaded, traced
# across every process it started (stdlib_extensions.txt, measured, never hand-listed), is imported by the requested
# interpreter FIRST, before anything is built. A missing one refuses with its name; VERACIUM_PREFLIGHT=warn runs anyway.
echo "== preflight: the compiled standard-library modules the suite loads =="
"$PY" "$HERE/stdlib_preflight.py" "$HERE/stdlib_extensions.txt" || exit 2

# NO-ENSUREPIP BOOTSTRAP (impl-review rounds 1+3 standing ask; previously a
# refusal). A qualified interpreter without ensurepip — the reviewer's
# /usr/bin/python3, twice — now gets a HASH-LOCKED NO-PIP environment: venv
# --without-pip, every wheel verified against the lock's sha256 set, then
# unpacked by stdlib zipfile. Same wheels, same hashes, no pip anywhere.
echo "== creating the venv (no network) =="
echo "  interpreter : $(command -v "$PY")"
if "$PY" -c "import ensurepip" 2>/dev/null; then
  "$PY" -m venv "$VENV"
  command -v "$PY" > "$VENV/.created-by"
  "$VENV/bin/pip" install --quiet --no-index \
      --find-links "$HERE" --require-hashes -r "$HERE/requirements-test.lock"
  echo "  installed from $HERE with --require-hashes"
else
  echo "  no ensurepip: hash-locked no-pip bootstrap"
  "$PY" -m venv --without-pip "$VENV"
  command -v "$PY" > "$VENV/.created-by"
  # C4-2: EXACT set verification first — each requirement bound to ITS OWN
  # digest set via wheel METADATA, no duplicates, no absences (the first
  # form accepted a renamed duplicate of another locked wheel standing in
  # for a removed one). Refusal happens BEFORE anything unpacks.
  "$VENV/bin/python" "$HERE/verify_wheelset.py" "$HERE" \
      "$HERE/requirements-test.lock"
  "$VENV/bin/python" - "$HERE" <<'PYB'
import pathlib, sys, sysconfig, zipfile
here = pathlib.Path(sys.argv[1])
site = pathlib.Path(sysconfig.get_paths()["purelib"])
wheels = sorted(here.glob("*.whl"))
for w in wheels:
    with zipfile.ZipFile(w) as z:
        z.extractall(site)
print(f"  unpacked {len(wheels)} exact-set-verified wheels into {site}")
PYB
fi

echo "== qualifying the runtime (specs/0007's predicate, not a version floor) =="
cd "$ROOT"
QUAL_OUT="$(PYTHONPATH=src "$VENV/bin/python" - <<'PYQ' 2>&1 || true
import sqlite3, sys
try:
    from veracium.store.schema_version import runtime_status
    st = runtime_status()                   # 0007 §4g: attested or verified runs; refused does not
except Exception as e:                      # never silenced: the REASON matters
    print(f"UNAVAILABLE\t{sqlite3.sqlite_version}\t{type(e).__name__}: {e}")
    sys.exit(0)
print(f"{'YES' if st.status in ('attested', 'verified') else 'NO'}\t{sqlite3.sqlite_version}\t{st.status}"
      f"{': ' + st.reason if st.reason else ''}")
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
  runtime_status()     : $DETAIL

This is a refusal, not a warning. Running the suite on an unqualified SQLite
build produces a number that LOOKS like a result and is not one — on the build
this launcher previously accepted, the reviewer measured 660 failures.

Set VERACIUM_PYTHON to an interpreter whose SQLite is recorded and reproduces
(specs/0007 defines what that means, and src/veracium/store/evidence/
sqlite_runtimes.json is the recorded set).
MSG
  exit 2
fi

# TWO PHASES by default (the owner, 2026-11-08: the one-process run took 110m52s at 0.31.0). Phase 1 runs everything but the
# phase-2 files under pytest-xdist; phase 2 runs those files in ONE process, so JOINT-TEST-GROUPS.md's G1 stays whole.
# two_phase.py names the files and then refuses unless the two phases ran exactly the collected set, each node once.
# VERACIUM_OFFLINE_MODE=single runs the suite as one process, as releases through 0.31.0 did.
MODE="${VERACIUM_OFFLINE_MODE:-two-phase}"
if [ "$MODE" = single ]; then
  echo "== running the suite (one process) =="
  VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src \
      "$VENV/bin/python" -m pytest -q tests -p no:randomly -rs "$@"
  exit $?
fi
[ "$MODE" = two-phase ] || { echo "VERACIUM_OFFLINE_MODE must be two-phase or single, not '$MODE'" >&2; exit 2; }

# The caller's --junitxml and --basetemp are taken out of the arguments: each phase gets its own (a second session
# would overwrite the first's junit and clear its basetemp), and the merged junit is written to the caller's path.
JUNIT=""; BASETEMP=""; ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --junitxml=*) JUNIT="${1#--junitxml=}" ;;
    --junitxml) shift; JUNIT="${1:-}" ;;
    --basetemp=*) BASETEMP="${1#--basetemp=}" ;;
    --basetemp) shift; BASETEMP="${1:-}" ;;
    *) ARGS+=("$1") ;;
  esac
  shift
done
# A path or node id would be added to BOTH phases (pytest does not deduplicate it against `tests`), so two-phase mode refuses
# one; selection options (-k, -m, -x, ...) and their values pass through, to the collection as well as to both phases.
"$VENV/bin/python" "$HERE/two_phase.py" positionals "${ARGS[@]}" || exit 2
WORK="$(mktemp -d "${TMPDIR:-/tmp}/veracium-offline-XXXXXX")"
[ -n "$JUNIT" ] || JUNIT="$WORK/merged.xml"
CORES="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"
W="${VERACIUM_OFFLINE_WORKERS:-8}"; [ "$W" -le "$CORES" ] 2>/dev/null || W="$CORES"
mapfile -t P2 < <("$VENV/bin/python" "$HERE/two_phase.py" files tests)
[ "${#P2[@]}" -gt 0 ] || { echo "two_phase.py found no phase-2 files: the split no longer matches the suite" >&2; exit 2; }
IGN=(); for f in "${P2[@]}"; do IGN+=("--ignore=$f"); done
BT1=(); BT2=(); [ -n "$BASETEMP" ] && BT1=("--basetemp=$BASETEMP/phase1") && BT2=("--basetemp=$BASETEMP/phase2")

T0="$("$VENV/bin/python" -c 'import time; print(time.time())')"
echo "== collecting the suite =="
CRC=0
VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src "$VENV/bin/python" -m pytest --collect-only -q tests -p no:randomly \
    "${ARGS[@]}" > "$WORK/collect.txt" 2>&1 || CRC=$?        # read, not acted on by set -e (research's L3)
[ "$CRC" = 0 ] || [ "$CRC" = 5 ] || { tail -20 "$WORK/collect.txt" >&2; echo "collection failed (exit $CRC)" >&2; exit 1; }
echo "  $(tail -1 "$WORK/collect.txt")"
set +e     # from here each phase's exit is read, not acted on: a red phase still gets the check and its report
echo "== running the suite, phase 1 of 2: all but ${#P2[@]} file(s), $W workers =="
VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src "$VENV/bin/python" -m pytest -q tests -p no:randomly -rs -n "$W" \
    "${IGN[@]}" "${BT1[@]}" --junitxml="$JUNIT.phase1.xml" "${ARGS[@]}" 2>&1 | tee "$WORK/phase1.txt"
RC1=${PIPESTATUS[0]}
echo "== running the suite, phase 2 of 2: ${P2[*]}, one process =="
VERACIUM_FORBID_NETWORK=1 PYTHONPATH=src "$VENV/bin/python" -m pytest -q "${P2[@]}" -p no:randomly -rs \
    "${BT2[@]}" --junitxml="$JUNIT.phase2.xml" "${ARGS[@]}" 2>&1 | tee "$WORK/phase2.txt"
RC2=${PIPESTATUS[0]}
WALL="$("$VENV/bin/python" -c 'import sys, time; print(f"{time.time() - float(sys.argv[1]):.2f}")' "$T0")"
echo "== checking the two phases against the collection (phase 1 exit $RC1, phase 2 exit $RC2; outputs in $WORK) =="
# the check's own line is the transcript's LAST line: the suite line, in pytest's grammar, counted from the two junits
"$VENV/bin/python" "$HERE/two_phase.py" check "$WORK/collect.txt" "$JUNIT.phase1.xml" "$JUNIT.phase2.xml" \
    --merge "$JUNIT" --lines "$WORK/phase1.txt" "$WORK/phase2.txt" --tests tests --rc "$RC1" "$RC2" --wall "$WALL"
