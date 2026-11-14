"""Research's census of each verb's (operation, table) pairs: the op type behind the obligation matrix (0031 trust-tools).

    python census_ops.py SCRATCH_DIR          (veracium importable from the source under review)

The fixture is write_census.py's (the product's own test fixture: a null model, edges added through the store). Each
verb runs on its own fresh store; every write statement on the store's one connection during the call is classified by
its leading verb (INSERT, INSERT OR REPLACE, UPDATE, DELETE) and table. No model is called; no JSON is decoded here.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_census as W  # noqa: E402

W.SCRATCH = sys.argv[1]
OP = re.compile(r"^\s*(INSERT(?:\s+OR\s+\w+)?|REPLACE|UPDATE(?:\s+OR\s+\w+)?|DELETE)\b(?:\s+INTO|\s+FROM)?\s+[\"`]?(\w+)", re.I)
U = W.U
for label, call in [("correct", lambda m: m.correct(U, "e1", "x2")), ("dispute", lambda m: m.dispute(U, "e1", reason="r")),
                    ("confirm", lambda m: m.confirm(U, "e1")),
                    ("redact-edge", lambda m: m.redact(U, edge_id="e1", reason="subject_request")),
                    ("redact-episode", lambda m: m.redact(U, episode_id="ep1", reason="subject_request"))]:
    m = W.fresh(f"ops-{label}"); st = []
    m.store._conn.set_trace_callback(st.append)
    call(m)
    m.store._conn.set_trace_callback(None)
    ops = {}
    for s in st:
        mm = OP.match(s)
        if mm:
            k = (re.sub(r"\s+", " ", mm.group(1).upper()), mm.group(2)); ops[k] = ops.get(k, 0) + 1
    print(label, sorted(ops.items()))
    m.close()
