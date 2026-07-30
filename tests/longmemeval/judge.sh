#!/usr/bin/env bash
# Run the OFFICIAL LongMemEval judge, unmodified, over a hypothesis file.
#
#   tests/longmemeval/judge.sh <hypotheses.jsonl> [data.json]
#
# Deliberately a thin wrapper: the scoring code is theirs, run as-is, so no
# prompt or aggregation drift can creep in from our side. What we add is only
# provenance — the repo commit and judge model are echoed for the run record.
#
# Requires: OPENAI_API_KEY, and the official repo cloned next to the dataset
# (see OFFICIAL_DIR). Judge model is the repo's own pin: gpt-4o -> gpt-4o-2024-08-06.
set -euo pipefail

HYP="${1:?usage: judge.sh <hypotheses.jsonl> [data.json]}"
DATA="${2:-$HOME/Datasets/longmemeval/longmemeval_s_cleaned.json}"
OFFICIAL_DIR="${OFFICIAL_DIR:-$HOME/Datasets/longmemeval/official}"
PY="${PY:-$HOME/Dev/veracium/.venv/bin/python}"

[ -n "${OPENAI_API_KEY:-}" ] || { echo "judge.sh needs OPENAI_API_KEY" >&2; exit 2; }
[ -d "$OFFICIAL_DIR" ] || { echo "official repo not found at $OFFICIAL_DIR" >&2; exit 2; }

COMMIT="$(git -C "$OFFICIAL_DIR" rev-parse HEAD)"
echo "[judge] official repo   : $OFFICIAL_DIR @ $COMMIT"
echo "[judge] judge model     : gpt-4o (repo pin -> gpt-4o-2024-08-06)"
echo "[judge] hypotheses      : $HYP"
echo "[judge] reference data  : $DATA"

cd "$OFFICIAL_DIR/src/evaluation"
"$PY" evaluate_qa.py gpt-4o "$HYP" "$DATA" | tail -3
echo
echo "[judge] per-type metrics:"
"$PY" print_qa_metrics.py "${HYP}.eval-results-gpt-4o" "$DATA"
