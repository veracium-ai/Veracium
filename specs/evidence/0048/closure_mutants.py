#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0048_closure_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0048's CODE closures, at its implementation-acceptance fold (external rounds 1-6): each finding killed by its cells.

tests/test_closure_mutants.py's rule: a code finding raised on or after its date closes only with a mutant that the closure
row's cited cells kill, in a table declaring spec 0048 and that finding. One table per finding, at
specs/evidence/0048/closure/<id>/mutation-table.json, each run by the shared protocol on a copy of the tracked tree.

The product findings reuse specs/evidence/0048/implementation_mutants.py's rows BY ID, so a closure is proven by the edit that
table already kills, its superseded implementation first where the table holds one. R2-01, R5-01 and R5-02 were closed in the
N4f gate itself, so their mutants edit tests/test_0048_decay_bounds.py: the reverted rule, as the round's gate mutants did. A
NO-OP control per mutated file. R1-04 (a text fix) and R1-05 (a test fixture) touch no non-test .py and have no table.

    $PY specs/evidence/0048/closure_mutants.py --check [ID ...]     # fast: every table current, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0048/closure_mutants.py --write [ID ...]
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

SELF = "specs/evidence/0048/closure_mutants.py"
TABLES = HERE / "closure"
IMPL = "specs/evidence/0048/implementation_mutants.py"
CFG = "src/veracium/config.py"
LC = "src/veracium/lifecycle.py"
SQ = "src/veracium/store/sqlite.py"
T = "tests/test_0048_decay_bounds.py"
COMMON = ("specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)
ANCHOR = {CFG: "def validate_decay_bound(", LC: "def expire(", SQ: "def _validated_edge_json(", T: "def _digest(node) -> str:"}

SOURCES = {}


def _source(rel):
    """The implementation table's runner, loaded once; its mutants are reused BY ID, so their definition digests are its own."""
    if rel not in SOURCES:
        spec = importlib.util.spec_from_file_location("veracium_closure_src_" + pathlib.Path(rel).stem, ROOT / rel)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        SOURCES[rel] = m
    return SOURCES[rel]


def _rows(ids):
    by_id = {r[0]: r for r in _source(IMPL).MUTANTS}
    missing = [i for i in ids if i not in by_id]
    assert not missing, f"{IMPL} has no mutant {missing}"
    return [by_id[i] for i in ids]


C = lambda name: f"{T}::{name}"                                                         # noqa: E731
_FORM = lambda n: C(f"test_the_gate_refuses_each_unresolved_form[{n}]")                 # noqa: E731
_R5 = lambda n: C(f"test_the_gate_refuses_each_round_5_form_for_its_reason[{n}]")       # noqa: E731
_RECV = lambda n: C(f"test_each_receiver_form_has_its_stated_static_and_runtime_outcome[{n}]")   # noqa: E731
_HONEST = [C("test_a_closure_over_a_methods_self_is_the_method_s")]
_HELD = '''            bad.append(f"{at(n)}: `.{n.attr}` held, passed or returned, not called ({q.get(id(n), '<module>')})")\n'''
_HELD_SRC = '''                bad.append(f"{at(n)}: `.{n.attr}` held, passed or returned, not called")\n'''
_CALLEE = '''    f = call.func\n    name = getattr(f, "id", None) or getattr(f, "attr", None)\n'''
_PREPARE = '''_PREPARE = "EXPLAIN QUERY PLAN "\n'''

GATE = {
    "0048-R2-01": [("R2-01-an-alias-of-execute-passes", "gate", T,
                    [(_HELD, "            pass\n"), (_HELD_SRC, "                pass\n")],
                    [_R5("(b) the reviewer's alias of execute, with constructed SQL")], _HONEST, None,
                    "an execute-family attribute held in a name is let through: R2-01's alias of `connection.execute`")],
    "0048-R5-01": [("R5-01-the-self-exemption-restored", "gate", T,
                    [(_CALLEE, '    f = call.func\n    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and '
                               'f.value.id == "self":\n        return None\n    name = getattr(f, "id", None) or getattr(f, "attr", None)\n')],
                    [_RECV("P12 method-shaped, no such member"), _RECV("P13 method-shaped, its own _rows member")], _HONEST, None,
                    "THE SUPERSEDED IMPLEMENTATION: a receiver spelled `self` is exempted without resolving what it denotes")],
    "0048-R5-02": [("R5-02-the-classifier-runs-the-statement", "gate", T, [(_PREPARE, '_PREPARE = ""\n')],
                    [C("test_a_statement_that_binds_exactly_is_compiled_and_not_run")], _HONEST, None,
                    "THE SUPERSEDED IMPLEMENTATION: the statement prepared bare, so one that binds exactly runs"),
                   ("R5-02-plain-explain", "gate", T, [(_PREPARE, '_PREPARE = "EXPLAIN "\n')],
                    [C("test_a_string_sqlite_refuses_bare_stays_unresolved[QUERY PLAN SELECT 1]")], _HONEST, None,
                    "plain EXPLAIN: a string SQLite refuses bare becomes grammatical")],
}

# finding: (the commit that fixed it, [mutants], [mutated files], the runner whose import probe it takes). The first mutant is
# the superseded implementation where the source table names one.
FINDINGS = {
    "0048-R1-01": ("19a95585", _rows(["N4g-entry-validation-removed", "N4d-floor-unvalidated-at-entry"]), (LC,), IMPL),
    "0048-R1-02": ("19a95585", _rows(["N4h-decided-from-the-listing", "N4h-conditional-on-the-row-as-read"]), (LC, SQ), IMPL),
    "0048-R1-03": ("19a95585", _rows(["N4d-validation-inside-the-decay-branch", "N4-write-refusal-swallowed"]), (LC,), IMPL),
    "0048-R2-01": ("8c71f85d", GATE["0048-R2-01"], (T,), None),
    "0048-R2-02": ("19a95585", _rows(["N4i-retained-decay-counted", "N4i-below-the-floor-the-decayed-value-stored",
                                      "N4i-floor-comparison-inclusive"]), (LC, SQ), IMPL),
    "0048-R3-01": ("1860fec0", _rows(["R3-01-two-observations", "R3-01-validate-the-capture-return-a-fresh-dump"]), (SQ,), IMPL),
    "0048-R3-02": ("1860fec0", _rows(["N4f-a-writer-bypasses-the-helper", "N4f-the-helpers-return-ignored"]), (SQ,), IMPL),
    "0048-R3-03": ("1860fec0", _rows(["R3-03-float-first"]), (CFG,), IMPL),
    "0048-R4-01": ("0c7ad4aa", _rows(["R4-01-the-runtime-layout-check-removed", "R4-01-a-layout-entry-moved"]), (SQ,), IMPL),
    "0048-R4-02": ("0c7ad4aa", _rows(["R4-02-the-value-rendered-unbounded"]), (CFG,), IMPL),
    "0048-R5-01": ("ed4d98c9", GATE["0048-R5-01"], (T,), None),
    "0048-R5-02": ("ed4d98c9", GATE["0048-R5-02"], (T,), None),
}


def _noop(fid, rel, mutants):
    anchor = ANCHOR[rel]
    return (f"NOOP-{fid}-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted({c for m in mutants if m[2] == rel for c in m[4]}),
            f"a comment before {anchor.strip()!r}: the bytes change, the behaviour does not", "SURVIVED")


def subject(fid: str) -> "_protocol.Subject":
    _fix, mutants, files, src = FINDINGS[fid]
    cells = sorted({n.split("::")[0] for m in mutants for n in (*m[4], *m[5])})
    source = _source(src).SUBJECT_P if src else None
    mutated = sorted({m[2] for m in mutants})
    return _protocol.Subject(
        spec="0048", finding=fid, table=TABLES / fid / "mutation-table.json",
        digested=tuple(dict.fromkeys((*mutated, *cells, *((src,) if src else ()), *COMMON))), mutants=mutants,
        controls=[_noop(fid, rel, mutants) for rel in mutated],
        import_modules=source.import_modules if source else (),
        import_specs=source.import_specs if source else (),
        cells_files=tuple(cells), kinds=tuple(sorted({m[1] for m in mutants})))


SUBJECTS = {fid: subject(fid) for fid in FINDINGS}
canonical = _protocol.canonical
render = _protocol.render


def problems(root: pathlib.Path = ROOT) -> list:
    out = []
    for fid, s in SUBJECTS.items():
        out += [f"{fid}: {p}" for p in s.problems(root=root)]
    found = sorted(p.parent.name for p in TABLES.glob("*/mutation-table.json"))
    if found != sorted(SUBJECTS):
        out.append(f"the tables on disk {found} are not one per finding {sorted(SUBJECTS)}")
    return out


def main(argv=None) -> int:
    argv = sys.argv if argv is None else argv
    ids = [a for a in argv[1:] if not a.startswith("--")] or list(SUBJECTS)
    unknown = sorted(set(ids) - set(SUBJECTS))
    if unknown:
        print(f"unknown finding(s): {unknown}")
        return 2
    if "--write" in argv or "--try" in argv:
        TABLES.mkdir(exist_ok=True)
        rc = 0
        for fid in ids:
            (TABLES / fid).mkdir(exist_ok=True)
            print(f"== {fid}", flush=True)
            mode = "--write" if "--write" in argv else "--try"
            rest = [] if mode == "--write" else [m[0] for m in SUBJECTS[fid].mutants] + [k[0] for k in SUBJECTS[fid].controls]
            rc |= SUBJECTS[fid].main([argv[0], mode, *rest])
        return rc
    bad = problems()
    for b in bad:
        print(f"STALE: {b}")
    if not bad:
        print(f"{len(SUBJECTS)} closure tables current, every row good")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
