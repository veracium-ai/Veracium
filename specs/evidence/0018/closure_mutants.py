#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0018_closure_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0018's CODE closures for the adjacent-rungs arc, at its implementation-acceptance fold (external round 6, 2026-11-08).

tests/test_closure_mutants.py's rule: a code finding raised on or after its date closes only with a mutant that the closure row's
cited cells kill, in a table declaring spec 0018 and that finding. There is one table per finding, at
specs/evidence/0018/closure/<id>/mutation-table.json, each run by the shared protocol on a copy of the tracked tree.

Every finding reuses specs/evidence/0018/rungs/implementation_mutants.py's rows BY ID. A closure is proven by the edit that table
already kills: the regression of the fix the finding asked for. Rounds 1 to 3 were design rounds, and their findings were
implemented in a042d9c2 (T1), 5dca1cce (T2), 10708086 (T3 to T6) and b1782a7a (I38's rows). Rounds 4 and 5 were implementation
rounds, closed in 9a502e59, 96a8fa69, 7eb00c3a, e75382cd, 793dd08e and 6daf8a02. Each mutated file has a NO-OP control.

No table, by property: R1-07 was closed by narrowing the claim in the spec text (ba71c886), and C5-02 in the round-6 package's
stage, outside the tree. C5-01 was closed by the v9.1 text (214f37b6), and its closure row cites the E1 cells, which the
implementation table's R4-01 rows already kill. E4-01 is a retained, disclosed limitation, not a raised finding: it was never fixed.

    $PY specs/evidence/0018/closure_mutants.py --check [ID ...]     # fast: every table current, every row good
    TMPDIR=/dev/shm $PY specs/evidence/0018/closure_mutants.py --write [ID ...]
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

SELF = "specs/evidence/0018/closure_mutants.py"
TABLES = HERE / "closure"
IMPL = "specs/evidence/0018/rungs/implementation_mutants.py"
COMMON = ("specs/evidence/mutation_protocol.py", _protocol.KINDS, SELF)

SOURCES = {}


def _source(rel=IMPL):
    """The implementation table's runner, loaded once; its mutants are reused BY ID, so their definition digests are its own."""
    if rel not in SOURCES:
        spec = importlib.util.spec_from_file_location("veracium_0018_closure_src_" + pathlib.Path(rel).stem, ROOT / rel)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        SOURCES[rel] = m
    return SOURCES[rel]


def _rows(ids):
    by_id = {r[0]: r for r in _source().MUTANTS}
    missing = [i for i in ids if i not in by_id]
    assert not missing, f"{IMPL} has no mutant {missing}"
    return [by_id[i] for i in ids]


P = "0018-AR-"
# finding: (the commit(s) that fixed it, the implementation rows that revert it). The design findings' rows are the mutants of the
# invariant each finding amended; the implementation findings' rows are the ones their own round wrote.
FINDINGS = {
    P + "R1-01": ("10708086", ["I13-the-preflight-writes-the-store", "I13-forged-evidence-carried-into-the-authority"]),
    P + "R1-02": ("10708086 b1782a7a", ["I39-every-historical-constructor-admitted", "I36-a-data-entry-issues-ddl",
                                        "I33-the-stamp-written-as-head"]),
    P + "R1-03": ("10708086", ["I34-checked-after-the-mint", "I34-a-loop-without-the-expectation", "I38-binding-on-migrate_to"]),
    P + "R1-04": ("10708086 b1782a7a", ["I38-a-target-store-judged-at-head", "I38-the-target-branch-not-validated",
                                        "I34-count-printed-rungs"]),
    P + "R1-05": ("10708086", ["I35-same-build-retry", "I35-rerun-because-a-version-is-known", "I35-rerun-repairs-a-missing-record"]),
    P + "R1-06": ("a042d9c2", ["I36-helper-carried-check-dropped", "I36-nested-check-deleted", "I36-two-data-steps-swapped"]),
    P + "R2-01": ("10708086", ["I34-count-only-the-migrated-branch", "I34-count-a-committed-error-twice",
                               "I34-continue-past-a-committed-error"]),
    P + "R2-02": ("a042d9c2", ["I36-direct-as-adjacent-plans", "I36-two-rungs-data-steps-swapped", "I36-a-field-joined-by-a-separator"]),
    P + "R2-03": ("a042d9c2", ["I33-the-v6-refusal-reports-head", "I33-the-v8-refusal-reports-head", "I33-the-v10-refusal-reports-head"]),
    P + "E2-01": ("10708086", ["I38-path-unencoded", "I38-operational-error-is-missing"]),
    P + "E2-02": ("10708086", ["I38-a-rung-opens-to-create"]),
    P + "R3-01": ("10708086", ["I35-the-superseded-blanket-retry", "I35-a-conditional-claims-a-cause",
                               "I35-unknown-prints-the-previous-version"]),
    P + "R3-02": ("10708086", ["I35-audit-write-weaker"]),
    P + "R3-03": ("10708086", ["I34-count-a-readback-before-it-is-bound"]),
    P + "R4-01": ("9a502e59 96a8fa69", ["I35-a-landed-attempted-rename-read-as-unwritten", "I35-append-once-read-as-unwritten",
                                        "I35-a-published-terminal-record-reported-unpublished",
                                        "I35-an-unread-terminal-record-reported-unpublished",
                                        "I35-a-present-terminal-record-reported-unpublished", "I35-the-n2-id-not-printed",
                                        "I35-every-e1-disclosure-says-unpublished"]),
    P + "R4-02": ("9a502e59", ["I15-ordinary-readback-binds-the-outcome-only"]),
    P + "R4-03": ("9a502e59", ["I19-a-mint-escape-becomes-internal-error"]),
    P + "R4-04": ("9a502e59", ["I36-a-check-dispatched-twice", "I36-a-check-never-dispatched", "I36-the-clock-read-twice"]),
    P + "R5-01": ("e75382cd", ["I35-an-unresolved-attempted-write-read-as-absence", "I35-the-load-inside-the-proving-window",
                               "I35-an-unresolved-terminal-write-reported-unpublished", "I35-absence-by-os-path-exists"]),
    P + "R5-02": ("e75382cd 793dd08e 6daf8a02", ["I36-an-off-plan-entry-called", "I36-an-off-plan-entry-nested",
                                                 "I36-an-off-plan-entry-in-a-thread", "I36-an-off-plan-entry-in-a-low-level-thread",
                                                 "I36-a-thread-before-the-first-entry", "I36-a-thread-after-the-last-entry",
                                                 "I36-a-dispatcher-read-helper"]),
}


def _noop(fid, rel, mutants):
    anchor = _source()._NOOP[rel]
    return (f"NOOP-{fid}-{pathlib.Path(rel).stem}", rel, [(anchor, "# no-op control: a comment, no behaviour\n" + anchor)],
            sorted({c for m in mutants if m[2] == rel for c in m[4]}),
            f"a comment before {anchor.strip()!r}: the bytes change, the behaviour does not", "SURVIVED")


def subject(fid: str) -> "_protocol.Subject":
    _fix, ids = FINDINGS[fid]
    mutants = _rows(ids)
    cells = sorted({n.split("::")[0] for m in mutants for n in (*m[4], *m[5])})
    source = _source().SUBJECT_P
    mutated = sorted({m[2] for m in mutants})
    data = [d for d in source.digested if not d.endswith(".py") and d != _protocol.KINDS]        # the fixtures and vectors the cells read
    return _protocol.Subject(
        spec="0018", finding=fid, table=TABLES / fid / "mutation-table.json",
        digested=tuple(dict.fromkeys((*mutated, *cells, *data, IMPL, *COMMON))), mutants=mutants,
        controls=[_noop(fid, rel, mutants) for rel in mutated],
        import_modules=source.import_modules, import_specs=source.import_specs,
        cells_files=tuple(cells), kinds=tuple(sorted({m[1] for m in mutants})))


SUBJECTS = {fid: subject(fid) for fid in FINDINGS}
canonical = _protocol.canonical
render = _protocol.render


def cited(fid: str) -> list:
    """The cells a closure row must cite, exactly: the table header's."""
    return SUBJECTS[fid].named_cells()


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
