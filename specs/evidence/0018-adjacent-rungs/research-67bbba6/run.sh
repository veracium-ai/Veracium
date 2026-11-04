#!/usr/bin/env bash
# Re-run of probe_rungs.py at the 0018 adjacent-rungs design package's pin. Usage: run.sh <python 3.14.7>
set -euo pipefail
PIN=67bbba69a8e463267f5533a161c3c6bd7c2991f3
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${1:?python}
(cd / && ! "$PY" -c 'import veracium' 2>/dev/null) || { echo "REFUSE: $PY has its own veracium"; exit 2; }
E=$(mktemp -d /var/tmp/rungs18.XXXX); S=$(mktemp -d /dev/shm/rungs18db.XXXX)
GIT_OPTIONAL_LOCKS=0 git -C "$HOME/Dev/veracium" archive "$PIN" | tar -x -C "$E"
cd "$E"
PYTHONPATH=src "$PY" -c 'import veracium.store.migration as m; assert m.__file__.startswith("'"$E"'/src/"), m.__file__'
PYTHONPATH=src nice -n 19 "$PY" "$HERE/probe_rungs.py" "$S"
echo "scratch (remove by literal path): $E $S" >&2
