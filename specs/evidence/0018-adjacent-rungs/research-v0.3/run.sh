#!/usr/bin/env bash
# 0018 adjacent-rungs v0.3 tables draft: re-run both probes at the pin. Usage: run.sh <python 3.14.7 with pydantic>
set -euo pipefail
PIN=67bbba69a8e463267f5533a161c3c6bd7c2991f3
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${1:?python}
(cd / && ! "$PY" -c 'import veracium' 2>/dev/null) || { echo "REFUSE: $PY has its own veracium"; exit 2; }
E=$(mktemp -d /var/tmp/r18v3ev.XXXX)
GIT_OPTIONAL_LOCKS=0 git -C "$HOME/Dev/veracium" archive "$PIN" | tar -x -C "$E"
cd "$E"
export PYTHONPATH="$E/src"
"$PY" -P -s -c 'import veracium.store.migration as m, sys; assert m.__file__.startswith(sys.argv[1] + "/src/"), m.__file__' "$E"
nice -n 19 "$PY" -P -s "$HERE/probe_constructors.py" > "$HERE/probe-constructors-67bbba6.out"
nice -n 19 "$PY" -P -s "$HERE/check_a2_facts.py" > "$HERE/check-a2-facts-67bbba6.out"
echo "scratch (remove by literal path): $E" >&2
