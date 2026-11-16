"""specs/0031 §4f, round 2's TT-R2-02 at the implementation: the trust tools' write census
(specs/evidence/0031-trust-tools/census/write_census_tools.py) is CURRENT. Its committed output, census-tools.txt, is
regenerated here on fresh stores and compared line for line, so every claim the census makes (each refusal gate writes
nothing; find_facts' one conditional wiki row; correct's committed refusal bookkeeping; the erase's store_changed
refusal writing nothing) is re-measured at every commit, never a figure frozen at one."""
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import subprocess

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CENSUS = ROOT / "specs" / "evidence" / "0031-trust-tools" / "census"


def _module():
    spec = importlib.util.spec_from_file_location("veracium_0031_tool_census", CENSUS / "write_census_tools.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_the_tool_census_is_current():
    m = _module()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print(f"write census of the seven trust tools through *_report; {len(m.CASES)} cases, each on a fresh store")
        for name, fn in m.CASES:
            r = fn()
            if isinstance(r[0], tuple):
                print(f"{name}\n    first:  {m.fmt(*r[0])}\n    second: {m.fmt(*r[1])}")
            else:
                print(f"{name}\n    {m.fmt(*r)}")
    committed = (CENSUS / "census-tools.txt").read_text(encoding="utf-8").splitlines()
    assert committed[0] == f"src tree: {_src_tree()}", committed[0]
    assert buf.getvalue().splitlines() == committed[1:]


def _git_tree(path: pathlib.Path) -> str:
    """git's tree object id for a directory, computed from the files (blob ids, 100644/100755 modes, git's entry
    order), skipping __pycache__: the same id `git rev-parse <commit>:<path>` gives for a clean, tracked tree."""
    entries = []
    for ch in path.iterdir():
        if ch.name == "__pycache__":
            continue
        if ch.is_dir():
            entries.append((ch.name + "/", b"40000 " + ch.name.encode() + b"\0" + bytes.fromhex(_git_tree(ch))))
        else:
            data = ch.read_bytes()
            blob = hashlib.sha1(b"blob %d\0" % len(data) + data).digest()
            mode = b"100755" if ch.stat().st_mode & 0o111 else b"100644"
            entries.append((ch.name, mode + b" " + ch.name.encode() + b"\0" + blob))
    body = b"".join(e for _, e in sorted(entries, key=lambda x: x[0].encode()))
    return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()


def _src_tree() -> str:
    """The census header's src tree, DERIVED at test time (research, stage 1: a typed header went stale once): in a git
    checkout, `git rev-parse HEAD:src`; in a git-less export (the offline leg), the same id computed from the files."""
    if (ROOT / ".git").exists():
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD:src"], capture_output=True, text=True,
                              check=True).stdout.strip()
    return _git_tree(ROOT / "src")


def test_the_header_hash_is_gits_tree_id_computed_from_the_files():
    """The git-less derivation agrees with git where both can run (a checkout whose src/ is clean), so the offline
    leg's header check is the same check."""
    if not (ROOT / ".git").exists():
        assert _src_tree() == _git_tree(ROOT / "src")
        return
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "src"], capture_output=True,
                           text=True, check=True).stdout
    assert dirty == "" and _git_tree(ROOT / "src") == _src_tree(), dirty


def test_no_tool_case_raised_and_every_refusal_gate_writes_nothing():
    lines = (CENSUS / "census-tools.txt").read_text(encoding="utf-8").splitlines()
    assert not [ln for ln in lines if "raised:" in ln]
    gate = [i for i, ln in enumerate(lines) if " / gate " in ln]
    assert len(gate) == 29                                  # 7 + 3 + 2 + 5 + 2 + 6 + 4: gates 1 to 7
    for i in gate:
        assert lines[i + 1].strip().startswith("refused:") and lines[i + 1].rstrip().endswith("no writes"), lines[i:i + 2]


# ------------------------------------------------------------------ the census agrees with the obligation matrix
# Round 2's verdict (TT-R2-02, §5): "the corrected matrix must agree with exercised SQL branches". The test above
# compares the census with its own regeneration, which cannot see a census that measures the WRONG call: at a643588d the
# other-subject case ran its fixture inside the trace, and the census charged the fixture's INSERT edges and INSERT
# edge_event to a refused correction for which the matrix declares four tables. This compares the two DATA carriers:
# every (op, table) the committed census charges to a case against the matrix's declared writes for that case's branch.
#   - a table the census charges must be declared for the branch, with that op (INSERT/UPDATE/DELETE family);
#   - a write the matrix declares UNCONDITIONAL for the branch ("always"; every row of writes_on_correction_refused,
#     whose branch is its condition) must be charged; a conditional one ("only when ...", find_facts' query-path row)
#     is not required per case, and its conditions are held by the census lines themselves;
#   - a count the matrix states, "(n)", is the count charged;
#   - a denied branch (gates 1-7, and the confirm's store_changed refusal) charges nothing, and the matrix says so.
MATRIX = CENSUS.parent / "obligation-matrix.json"
_CALL = re.compile(r"^    (?:(first|second): +)?(\S+) +(no writes|.+)$")
_W = re.compile(r"^(INSERT|UPDATE|DELETE|REPLACE) (\w+) x(\d+)$")


def _parse(lines):
    """census-tools.txt (without its header line) -> [(case, outcome, {(op, table): n})], one entry per traced call."""
    out, case = [], None
    for ln in lines:
        if not ln.startswith("    "):
            case = ln
            continue
        m = _CALL.match(ln)
        assert m and case, ln
        writes = {}
        if m.group(3) != "no writes":
            for part in m.group(3).split(", "):
                w = _W.match(part)
                assert w, part
                writes[(w.group(1), w.group(2))] = int(w.group(3))
        out.append((case, m.group(2), writes))
    return out


def _branch(case):
    """A case's matrix branch, from its name: None for a denied branch; else (tool, key). Refuses an unknown tool."""
    tool, rest = case.split(" / ", 1)
    if rest.startswith("gate ") or rest.startswith("CONDITIONAL store changed since the preview"):
        return None
    key = ("writes_on_correction_refused" if "correction_refused" in rest else
           "writes_edge_target" if rest.startswith("accepted (edge)") else
           "writes_episode_target" if rest.startswith("accepted (episode)") else "writes")
    return tool, key


def _family(op):
    return {w for w in ("INSERT", "UPDATE", "DELETE") if w in op.upper()}


def disagreements(calls, matrix):
    tools, bad, seen = matrix["tools"], [], set()
    if matrix["denied_branch_writes"]["gates_1_to_7"] != []:
        bad.append("the matrix's gates_1_to_7 declares writes")
    refused = {w.split(" ")[0] for w in matrix["denied_branch_writes"]["CorrectionRefused"]["writes"]}
    if refused != {w["table"] for w in tools["correct_fact"]["writes_on_correction_refused"]}:
        bad.append("the matrix's two CorrectionRefused carriers name different tables")
    charged_by_branch = {}
    for case, outcome, writes in calls:
        b = _branch(case)
        # D (research): the branch is routed by the case's NAME, so its outcome is checked against the branch
        want = ("refused:" if b is None else "refused:correction_refused" if b[1] == "writes_on_correction_refused"
                else "ok")
        if not (outcome.startswith(want) if b is None else outcome == want):
            bad.append(f"{case}: outcome {outcome}, but its branch {b or 'denied'} wants {want}")
        if b is None:
            if writes:
                bad.append(f"{case}: a denied branch charged {sorted(writes)}")
            continue
        if b[0] not in tools or not isinstance(tools[b[0]].get(b[1]), list):
            bad.append(f"{case}: no matrix branch {b}")
            continue
        seen.add(b)
        declared = tools[b[0]][b[1]]
        fam = {}
        for d in declared:
            fam.setdefault(d["table"], set()).update(_family(d["op"]))
        for (op, table), n in sorted(writes.items()):
            if op == "REPLACE":
                op = "INSERT"
            if op not in fam.get(table, set()):
                bad.append(f"{case}: charges {op} {table}, which {b[0]}.{b[1]} does not declare")
        charged = {(("INSERT" if op == "REPLACE" else op), t) for (op, t) in writes}
        charged_by_branch.setdefault(b, set()).update(charged)
        for d in declared:
            unconditional = d.get("condition") == "always" or b[1] == "writes_on_correction_refused"
            # A (research): every op of an unconditional row, not only its table ("INSERT and UPDATE" edge_event)
            missing = sorted(op for op in _family(d["op"]) if (op, d["table"]) not in charged)
            if unconditional and missing:
                bad.append(f"{case}: {b[0]}.{b[1]} declares {d['op']} {d['table']} unconditionally; the census "
                           f"charges no {' or '.join(missing)} {d['table']}")
            stated = re.search(r"\((\d+)\)", d["op"])
            if stated:
                got = sum(n for (op, t), n in writes.items() if t == d["table"] and op in _family(d["op"]))
                if got != int(stated.group(1)):
                    bad.append(f"{case}: {b[0]}.{b[1]} states {d['op']} {d['table']}; the census charges {got}")
    branches = {(t, k) for t, T in tools.items() for k, v in T.items() if k.startswith("writes") and isinstance(v, list)}
    if seen != branches:
        bad.append(f"matrix branches no case exercises: {sorted(branches - seen)}")
    # B (research): a CONDITIONAL row is not required per case, but some case of its branch must exercise it (TT-R2-02:
    # the matrix agrees with EXERCISED branches)
    for b in sorted(seen):
        for d in tools[b[0]][b[1]]:
            unconditional = d.get("condition") == "always" or b[1] == "writes_on_correction_refused"
            if not unconditional and not any((op, d["table"]) in charged_by_branch[b] for op in _family(d["op"])):
                bad.append(f"{b[0]}.{b[1]}: the conditional {d['op']} {d['table']} is charged by no case of its branch")
    return bad


def _committed():
    lines = (CENSUS / "census-tools.txt").read_text(encoding="utf-8").splitlines()
    return lines[2:]                                        # the src-tree header and the title line


def test_every_case_writes_exactly_what_the_matrix_declares_for_its_branch():
    calls = _parse(_committed())
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    # every case is mapped: 45 cases, 46 traced calls (find_facts' empty user traces two); 30 denied (29 gates and the
    # store_changed confirm), 16 on the nine write branches the matrix declares (preview's is the empty one), three of
    # them gate 6's own-source controls
    cases = {c for c, _, _ in calls}
    assert (len(cases), len(calls)) == (len(_module().CASES), 46) == (45, 46)
    assert sum(_branch(c) is None for c in cases) == 30
    assert disagreements(calls, matrix) == []


def _mutated(name):
    """The agreement check's mutants: each is a census or a matrix the check must refuse, by name."""
    calls = _parse(_committed())
    matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
    if name == "the fixture inside the trace (a643588d's census line)":
        calls = [(c, o, {**w, ("INSERT", "edges"): 1, ("INSERT", "edge_event"): 1,
                         ("INSERT", "write_counter"): w[("INSERT", "write_counter")] + 1})
                 if "other-subject" in c else (c, o, w) for c, o, w in calls]
    elif name == "the matrix loses a table (wiki from the refused correction)":
        b = matrix["tools"]["correct_fact"]["writes_on_correction_refused"]
        b[:] = [d for d in b if d["table"] != "wiki"]
    elif name == "the matrix gains an unconditional table (dispute redactions)":
        matrix["tools"]["dispute_fact"]["writes"].append({"table": "redactions", "op": "INSERT", "condition": "always"})
    elif name == "a stated count the census does not charge (forget's replies, 3)":
        for d in matrix["tools"]["forget_fact"]["writes_edge_target"]:
            if d["table"] == "replies":
                d["op"] = "UPDATE (3)"
    elif name == "a gate that writes":
        calls = [(c, o, {("UPDATE", "edges"): 1}) if c.startswith("forget_fact / gate 4 neither id") else (c, o, w)
                 for c, o, w in calls]
    elif name == "an unmapped tool":
        calls = calls + [("summon_fact / accepted", "ok", {("INSERT", "edges"): 1})]
    elif name == "a branch no case exercises (the episode target)":
        calls = [x for x in calls if not x[0].startswith("forget_fact / accepted (episode)")]
    elif name == "an unconditional row loses one of its ops (forget's UPDATE edge_event)":
        calls = [(c, o, {k: v for k, v in w.items() if k != ("UPDATE", "edge_event")})
                 if c.startswith("forget_fact / accepted (edge)") else (c, o, w) for c, o, w in calls]
    elif name == "no case charges a conditional row (forget's source_revocations)":
        calls = [(c, o, {k: v for k, v in w.items() if k[1] != "source_revocations"})
                 if c.startswith("forget_fact / accepted") else (c, o, w) for c, o, w in calls]
    elif name == "the matrix gains a conditional row no case exercises (dispute policy_receipt)":
        matrix["tools"]["dispute_fact"]["writes"].append({"table": "policy_receipt", "op": "INSERT",
                                                          "condition": "only when a policy lane is passed"})
    elif name == "an accepted case refused with the same writes":
        calls = [(c, "refused:not_found_in_scope" if c.startswith("dispute_fact / accepted") else o, w)
                 for c, o, w in calls]
    return calls, matrix


AGREEMENT_MUTANTS = {
    "the fixture inside the trace (a643588d's census line)": "charges INSERT edges",
    "the matrix loses a table (wiki from the refused correction)": "charges DELETE wiki",
    "the matrix gains an unconditional table (dispute redactions)": "declares INSERT redactions unconditionally",
    "a stated count the census does not charge (forget's replies, 3)": "states UPDATE (3) replies; the census charges 2",
    "a gate that writes": "a denied branch charged",
    "an unmapped tool": "no matrix branch",
    "a branch no case exercises (the episode target)": "matrix branches no case exercises",
    "an unconditional row loses one of its ops (forget's UPDATE edge_event)": "the census charges no UPDATE edge_event",
    "no case charges a conditional row (forget's source_revocations)":
        "the conditional UPDATE source_revocations is charged by no case of its branch",
    "the matrix gains a conditional row no case exercises (dispute policy_receipt)":
        "the conditional INSERT policy_receipt is charged by no case of its branch",
    "an accepted case refused with the same writes": "outcome refused:not_found_in_scope, but its branch",
}


@pytest.mark.parametrize("name", sorted(AGREEMENT_MUTANTS))
def test_the_agreement_check_refuses_each_mutant_by_name(name):
    bad = disagreements(*_mutated(name))
    assert any(AGREEMENT_MUTANTS[name] in b for b in bad), bad


# ------------------------------------------------------------------ TT-R3-03: the phase rule over the census corpus
def test_no_refusal_class_leaves_a_call_after_a_writing_commit_across_the_census(monkeypatch):
    """v23.3's INV-TT11 check, "no refusal site reached after a writing commit in the call", over this census's 45 cases
    (the corpus bound: every gate, accepted write, committed refusal and conditional write the census charges). Every
    refusal-class exception (ValueError, TypeError, ScopeError, TrustRefused; CorrectionRefused apart, the committed
    refusal) that leaves a tool's library call does so while the call's commit cell is EMPTY, so the phase rule turns
    none of today's refusals into an internal failure. Read at the moment the exception leaves, from the cell the
    connection itself fills. Gates 1 to 5 refuse before any library call, so the calls this reads are the ones that
    reach the catch. Non-vacuous: the corpus reaches refusals and writing commits, both counted. Mutant: a
    refusal-class raise after a commit (the confirm-then-readback shape) in a census case."""
    from veracium import graph
    from veracium import mcp_server as M
    from veracium.scope_linkage import ScopeError
    from veracium.store import sqlite as S
    real, events, current = M._trust_call, [], [None]

    def commits():
        bound = S._TRUST_COMMITS.get()
        return None if bound is None else len(bound[1])

    def spy(mem, fn):
        def inner():
            try:
                out = fn()
            except graph.CorrectionRefused:
                events.append((current[0], "correction_refused", commits()))
                raise
            except (ScopeError, ValueError, TypeError) as exc:
                events.append((current[0], f"refusal {type(exc).__name__}", commits()))
                raise
            events.append((current[0], "returned", commits()))
            return out
        return real(mem, inner)

    monkeypatch.setattr(M, "_trust_call", spy)
    m = _module()
    for name, fn in m.CASES:
        current[0] = name
        fn()
    refusals = [e for e in events if e[1].startswith("refusal")]
    after = [e for e in refusals if e[2] != 0]
    assert after == [], after
    assert len(m.CASES) == 45 and len(refusals) >= 5, (len(m.CASES), len(refusals))
    assert any(e[1] == "returned" and e[2] for e in events), "no case committed a write: the check would be vacuous"
