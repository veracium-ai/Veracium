#!/usr/bin/env python3
"""0018 adjacent rungs, round-3 closure: EXTRACT §7a–7c's recovery tables from the candidate into JSON, never retype them.

Usage: extract_table.py <candidate.md> > recovery-table.json

Per row: its id, its raw input and action cells, the action ids (the backticked tokens of the action cell), and from the
input cell the outcomes it names (backticked tokens) and the state it names ("state `x`"). E1's disclosure id is the
action id in E1's cell that no 7b row uses. The rows must be exactly P0–P4, N1–N4, C1, C2, K, U0–U7, E1–E4, or the
extraction refuses."""
import json
import re
import sys

WANT = "P0 P1 P2 P3 P4 N1 N2 N3 N4 C1 C2 K U0 U1 U2 U3 U4 U5 U6 U7 E1 E2 E3 E4".split()
TOK = re.compile(r"`([a-z][a-z0-9-]*)`")

text = open(sys.argv[1], encoding="utf-8").read()
a = text.index("### 7a."); b = text.index("**What a rerun is promised for:**", a)
rows = {}
for line in text[a:b].splitlines():
    m = re.match(r"^\| (P\d|N\d|C\d|K|U\d|E\d) \|(.*)$", line)
    if not m:
        continue
    cells = [c.strip() for c in m.group(2).split(" | ")]
    inp, act = cells[0], cells[1]
    state = re.search(r"state `([a-z]+)`", inp)
    rows[m.group(1)] = {"input": inp, "action_cell": act, "row_text": line, "actions": TOK.findall(act),
                        "outcomes": [o for o in TOK.findall(inp) if not (state and o == state.group(1))],
                        "state": state.group(1) if state else None}
got = list(rows)
if got != WANT:
    sys.exit(f"REFUSED: the tables' rows are {got}, not {WANT}")
# E1 (v0.5.1): "C1 and U0 facts give `<resume id>`" and "plus the disclosure `<disclosure id>`", read by their phrases
e1 = rows["E1"]["action_cell"]
mr = re.search(r"C1 and U0 facts give `([a-z][a-z0-9-]*)`", e1); md = re.search(r"the disclosure `([a-z][a-z0-9-]*)`", e1)
if not (mr and md):
    sys.exit("REFUSED: E1 must state the resume id for C1 and U0 facts and the disclosure id, by their phrases")
rows["E1"]["resume"], rows["E1"]["disclosure"] = mr.group(1), md.group(1)
for r in WANT:
    if r not in ("P4", "E1") and not rows[r]["actions"]:
        sys.exit(f"REFUSED: row {r} carries no action id")
print(json.dumps({"source": sys.argv[1].rsplit("/", 1)[-1], "rows": rows}, indent=1, sort_keys=True))
