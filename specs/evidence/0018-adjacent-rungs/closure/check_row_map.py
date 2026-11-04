#!/usr/bin/env python3
"""0018 round-3 closure: the GENERATED map from each model check to the exact normative row it asserts (the reviewer's
archive request; the miss behind R3-01 was a model row left on v0.4.1's table).

Usage: check_row_map.py <model-run.jsonl> <recovery-table.json> [--control]

Reads every `asserts` record the model emits (cell, row, action ids) and joins it to the table extracted from the
candidate. A composite row is read by §7's rules: `P4>U` is U's ids (P4's `newer` reading: `no-rerun-this-build`);
`E1>U` is the resume id for C1/U0 facts, else U's ids, then the disclosure. Prints the map as Markdown, then the rows no
cell asserts (listed, not failed: research N2). Exits 1 if any cell asserts a row the table lacks or ids the table does
not give that row. --control adds v0.4.1's stale expectation (U5 asserting `rerun`) and must exit 1."""
import json
import sys

recs = [json.loads(l) for l in open(sys.argv[1])]
T = json.load(open(sys.argv[2]))["rows"]
asserts = [r["asserts"] for r in recs if "asserts" in r]
if "--control" in sys.argv:
    asserts.append({"cell": "CONTROL: v0.4.1's same-build retry, asserted as U5", "row": "U5", "actions": ["rerun"]})


def want(row):
    base = row.split(">", 1)[-1]
    if base not in T:
        return None
    if row.startswith("P4>"):
        return ["no-rerun-this-build"] if base == "U4" else T[base]["actions"]
    if row.startswith("E1>"):
        return ([T["E1"]["resume"]] if base in ("C1", "U0") else T[base]["actions"]) + [T["E1"]["disclosure"]]
    if row == "E4":
        return None                                           # E4's ids depend on the bound readback: checked below
    return T[row]["actions"]


bad, used = 0, set()
print("| model check | §7 row | ids asserted | the table's ids | agrees |")
print("|---|---|---|---|---|")
for a in asserts:
    row, acts = a["row"], a["actions"]
    w = want(row)
    if row == "E4":
        ok = acts in (["repair-build"], ["repair-build", "stop-inspect-committed"]) and set(acts) <= set(T["E4"]["actions"])
        w = T["E4"]["actions"]
    else:
        ok = w is not None and acts == w
    used.add(row.split(">", 1)[0] if row.startswith("E1>") else row.split(">", 1)[-1] if row.startswith("P4>") else row)
    if row.startswith(("P4>", "E1>")):
        used.add(row.split(">")[0])
    bad += not ok
    print(f"| {a['cell'][:90].replace('|', '/')} | `{row}` | {', '.join(acts) or '—'} | {', '.join(w or []) or '—'} | {'yes' if ok else '**NO**'} |")
unused = [r for r in T if r not in used]
print()
print(f"rows asserted by no cell ({len(unused)} of {len(T)}; listed, not failed): {' '.join(unused) or 'none'}")
print(f"ROWMAP checks={len(asserts)} disagree={bad} rows={len(T)} unexercised={len(unused)}")
sys.exit(1 if bad else 0)
