"""0011 — standing tests for every campaign mutant that had none.

PROCESS-R6-1: MUTANT-CAMPAIGN.md claimed every fix carried a standing test.
It did not — F1–F4, C1–C4 and the row-unbound withdrawal were verified by
ad-hoc shell plants during the session and never became tests, so neutering
an entire new check left everything green. Every mutant here plants its
attack IN MEMORY (attacked text, fabricated aggregate, patched constant) and
requires the bite; `specs/evidence/0011/mutant_registry.py` carries each
mutation as text hunks, applies them itself, and OBSERVES these tests fail
(PROCESS-R11-1) — no test here claims a kill, and no reporter exists.
"""
from __future__ import annotations

import copy
import importlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "specs" / "evidence" / "0011"
sys.path.insert(0, str(EVID))

import check_round1_fold as CF                                # noqa: E402
import policy_matrix as PM
import mutant_registry as MR                                    # noqa: E402
import subject_census as SC                                   # noqa: E402


SPEC = (ROOT / "specs" / "0011-subject-scoped-entitlement.md").read_text()
AGG = json.loads((EVID / "subject_aggregate.json").read_text())


def _attacked(policy_extra, fence):
    t = SPEC.replace(
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        f"             and {policy_extra}\n"
        "             and self_assertion(incoming)\n    ALLOW    otherwise",
        1)
    return t.replace("## 13. Changes in v7",
                     fence + "\n\n## 13. Changes in v7", 1)


# ---- F1–F4: the fold checker's grammar holes -------------------------------

def test_indented_helper_definition_is_followed():
    t = _attacked("sourced(prior)",
                  "```\n    sourced(e) := e.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F1 regressed"


def test_parenless_binding_is_followed():
    t = _attacked("srcflag",
                  "```\nsrcflag := prior.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F2 regressed"


def test_info_string_fence_is_scanned():
    t = _attacked("sourced(prior)",
                  "```text\nsourced(e) := e.provenance.source_id is not None\n```")
    assert any("source_id" in b for b in CF.check_r1_1(t)), "F3 regressed"


def test_extra_table_row_is_refused():
    t = SPEC.replace("| `user` | `user` | 3 | **REFUSE** | ALLOW |",
                     "| `user` | `user` | 3 | **REFUSE** | ALLOW |\n"
                     "| `user` | `user` | 3 | **ALLOW** | ALLOW |", 1)
    assert CF.check_decision_table(t), "F4 regressed"
    assert not CF.check_decision_table(SPEC), "pristine control"


# ---- the reviewer's round-5 carrier attack ---------------------------------

def test_rider_promise_in_the_row_is_refused():
    # rebuild the row carrying the old promise
    i = SPEC.index("| USER (sole authority: self-assertion) |")
    j = SPEC.index("\n", i)
    t = SPEC[:i] + SPEC[i:j].split("|")[0] + \
        "| USER (sole authority: self-assertion) | **OTHER** | any | " \
        "retires | **REFUSED** | narrow by ruling, with the measurement " \
        "rider |" + SPEC[j:]
    assert any("measurement rider" in b for b in CF.check_carriers(t)), (
        "the row-bound rider check regressed (CARRIER-R5-1)")


# ---- C1–C4: the census figure bindings -------------------------------------

def test_inflated_aggregate_figure_is_refused():
    m = copy.deepcopy(AGG)
    m["predicate_passes"] = 99_999
    assert any("drifted from its artifact" in b
               for b in CF.check_census_figures(SPEC, agg=m)), "C1 regressed"


def test_gutted_candidate_table_is_refused():
    m = copy.deepcopy(AGG)
    m["candidate_table"] = {"me": 31}
    assert CF.check_census_figures(SPEC, agg=m), "C2 regressed"


def test_unmasked_name_in_aggregate_is_refused():
    # the artifact under attack, named in the body (P1's binding):
    assert (EVID / "subject_census.py").exists()
    m = copy.deepcopy(AGG)
    m["candidate_table"] = dict(AGG["candidate_table"])
    m["candidate_table"]["user's friend David"] = 3
    assert any("unmasked" in b for b in SC.validate_aggregate(m)), (
        "C3 regressed — subject_census accepts an unmasked name")
    assert not SC.validate_aggregate(AGG), "pristine control"


def test_spec_figure_drift_is_refused():
    t = SPEC.replace("| predicate passes | **72,253 = 39.4%**",
                     "| predicate passes | **72,254 = 39.4%**", 1)
    assert t != SPEC, "the drift failed to apply"
    assert CF.check_census_figures(t, agg=AGG), "C4 regressed"
    assert not CF.check_census_figures(SPEC, agg=AGG), "pristine control"


# ---- R6-1 and the neutered-check hole --------------------------------------

def test_narrowed_enum_dimension_is_refused(monkeypatch):
    """EVIDENCE-R6-1: removing THIRD_PARTY from DERIVED shrank the claimed
    domain 1,440 → 1,152 with exit 0 — both sides read the constants. The
    enum axes are pinned to the enum itself now."""
    monkeypatch.setattr(PM, "DERIVED",
                        [None] + [a for a in PM.A
                                  if a is not PM.A.THIRD_PARTY])
    assert any("DERIVED" in b for b in PM.problems()), "R6-1 regressed"
    monkeypatch.undo()
    monkeypatch.setattr(PM, "AUTHORS",
                        [a for a in PM.A if a is not PM.A.SYSTEM])
    assert any("AUTHORS" in b for b in PM.problems()), (
        "the AUTHORS axis can still self-narrow")


def test_every_fold_check_is_reached(monkeypatch):
    """PROCESS-R6-1: deleting `check_census_figures` from main()'s sum left
    every test green — nothing proved the aggregation REACHES each check.
    The R14-1 sentinel, per check function."""
    checks = [n for n in dir(CF)
              if n.startswith("check_") and callable(getattr(CF, n))]
    assert len(checks) >= 6, checks
    for name in checks:
        class _Reached(Exception):
            pass

        def _sentinel(*a, _r=_Reached, **k):
            raise _r()

        monkeypatch.setattr(CF, name, _sentinel)
        try:
            CF.main()
        except _Reached:
            pass
        except SystemExit:
            raise AssertionError(
                f"main() finished without invoking {name} — a neutered "
                f"check is invisible (PROCESS-R6-1)")
        else:
            raise AssertionError(
                f"main() returned without invoking {name}")
        monkeypatch.undo()


# ---- PROCESS-R7-1 → R11-1: the ledger itself -------------------------------
#
# History, because each block below closes a specific round: R7-1 a
# fictitious entry rode a passing node; R8-1 a global id-bag hid a node
# swap, bool coerced to int, and /etc/passwd validated; R9-1 the grammar
# was open and the join self-asserted; R10-1 the in-artifact reporter
# conspired with a swapped on-disk registry; R11-1 the round-10 regression
# never executed (exit 4 looked like the defense) and the id half of every
# kill was still a test-side claim. Schema 4 ends the claim protocol:
# mutations live in the registry as hunks, the runner applies them and
# OBSERVES the mapped node fail. These tests exercise that machinery.


def test_registry_structural_validity_is_enforced():
    E = MR.ENTRIES
    dup = E + (E[0],)
    assert any("duplicate" in b for b in MR.validate_entries(dup))
    hunk = ("specs/evidence/0011/policy_matrix.py", "SOURCES", "X")
    ghost = E + (("G1", "dev", "x", E[0][3], "problems",
                  (("does_not_exist.py", "a", "b"),)),)
    assert any("OUTSIDE the closed mutable set" in b
               for b in MR.validate_entries(ghost))
    empty = E + (("G2", "dev", "x", E[0][3], "problems", ()),)
    assert any("no hunks" in b for b in MR.validate_entries(empty))
    noop = E + (("G3", "dev", "x", E[0][3], "problems",
                 ((hunk[0], "SOURCES", "SOURCES"),)),)
    assert any("identical" in b for b in MR.validate_entries(noop))
    multi = E + (("G4", "dev", "x", E[0][3], "problems",
                  ((hunk[0], "REFUSE", "X"),)),)   # occurs many times
    assert any("exactly once" in b for b in MR.validate_entries(multi))
    optioned = E + (("G5", "dev", "x",
                     "tests/test_0011_policy_matrix.py::t --pdb",
                     "problems", (hunk,)),)
    assert any("pytest node id" in b for b in MR.validate_entries(optioned))
    assert not MR.validate_entries(E), "pristine control"


def test_the_mutable_artifact_set_is_inclusion_defined():
    """Research F-B residual: 'not tests/, not the registry' was a
    DENY-LIST — the polarity this arc exists to refuse. It silently
    admitted a future conftest.py (judge-side infrastructure pytest will
    load) and any off-path src function (a genuine kill of an unrelated
    defense, inflating the depth metric). The campaign is entitled to
    mutate exactly MUTABLE_ARTIFACTS; everything else refuses by
    membership, including files that exist and functions that are real."""
    assert MR.MUTABLE_ARTIFACTS == frozenset({
        "specs/evidence/0011/policy_matrix.py",
        "specs/evidence/0011/check_round1_fold.py",
        "specs/evidence/0011/subject_census.py",
        "specs/evidence/0011/check_contention_rule.py"}), (
        "widening the mutable set is a REVIEWED edit — update this test "
        "with the review that authorizes it")
    for art in ("tests/test_0011_policy_matrix.py",       # the judge
                "specs/evidence/0011/mutant_registry.py",  # the runner
                "conftest.py",                             # future judge infra
                "src/veracium/authority.py"):              # off-path, real
        g = MR.ENTRIES + (("J1", "dev", "x", MR.ENTRIES[0][3],
                           "problems", ((art, "import", "IMPORT"),)),)
        assert any("OUTSIDE the closed mutable set" in b
                   for b in MR.validate_entries(g)), art
    # research (round-11 pass, forward note): the allowlist is hand-
    # maintained and must track what ENTRIES actually target — set
    # equality BOTH ways, so a fifth legitimate artifact with a stale
    # allowlist, and an allowlist member no entry mutates any more, each
    # fail with the other named (the bundle-digest closure shape).
    targeted = {h[0] for e in MR.ENTRIES for h in e[5]}
    assert targeted == MR.MUTABLE_ARTIFACTS, (
        f"entries target {sorted(targeted)} but MUTABLE_ARTIFACTS is "
        f"{sorted(MR.MUTABLE_ARTIFACTS)} — grow or shrink the allowlist "
        f"WITH the entries, as a reviewed edit")


def test_artifact_outside_the_package_is_refused():
    """PROCESS-R8-1(3): `/etc/passwd` validated, because pathlib discards
    the left operand when the right is absolute. Hunk paths must be
    relative, contained, and regular files."""
    for art in ("/etc/passwd", "../../../etc/passwd", "specs/archives"):
        g = MR.ENTRIES + (("X1", "dev", "x", MR.ENTRIES[0][3],
                           "problems", ((art, "a", "b"),)),)
        assert any("X1" in b for b in MR.validate_entries(g)), art


def test_missing_observations_fail_coverage():
    """PROCESS-R7-1's fictitious entry, in observed-kill terms: an entry
    the runner never saw die has no kill in the verified block, and
    coverage names it — the record cannot claim completeness by riding
    another entry's node."""
    v = dict(clean={e[3]: 1 for e in MR.ENTRIES},
             kills=[dict(id=e[0], exit=1, failed=1) for e in MR.ENTRIES],
             leave_one_out=[dict(id=e[0], dropped=n, exit=0)
                            for e in MR.ENTRIES if len(e[5]) > 1
                            for n in range(len(e[5]))])
    assert not MR.coverage_problems(MR.ENTRIES, v), "pristine control"
    bogus = MR.ENTRIES + (("BOGUS", "dev", "rides a passing node",
                           MR.ENTRIES[0][3], MR.ENTRIES[0][4],
                           MR.ENTRIES[0][5]),)
    assert any("BOGUS" in b for b in MR.coverage_problems(bogus, v))
    thin = dict(v, leave_one_out=v["leave_one_out"][1:])
    assert any("leave-one-out" in b
               for b in MR.coverage_problems(MR.ENTRIES, thin))


def test_a_dead_subprocess_is_an_error_not_a_defense(tmp_path):
    """PROCESS-R11-1 itself: the round-10 regression's copied module
    derived ROOT from /tmp, pytest exited 4 with nothing collected, and
    the empty kill list produced the expected binding mismatch — the test
    passed while executing nothing. The runner now refuses a run that
    never happened, at both phases."""
    # clean phase: a node that cannot run yields NO baseline, loudly
    e = ("D1", "dev", "x", "tests/test_0011_policy_matrix.py::no_such_test",
         MR.ENTRIES[0][4], MR.ENTRIES[0][5])
    verified, problems = MR.execute((e,), root=MR.ROOT)
    assert verified["clean"] == {} and verified["kills"] == []
    assert any("no baseline" in p for p in problems), problems
    # and a rootless tree is the same refusal, not an empty success
    verified, problems = MR.execute((MR.ENTRIES[0],), root=tmp_path)
    assert verified["kills"] == []
    assert any("no baseline" in p for p in problems), problems


def test_a_swapped_on_disk_registry_survives_and_is_refused(tmp_path):
    """The round-10/11 coordinated attack, standing, with nothing left to
    coordinate: swap the NODES of R4A and F1 in an on-disk copy of the
    registry and drive the REAL execution at the REAL root. The runner
    applies R4A's policy-matrix mutation and runs F1's fold-checker test,
    which passes — an observed SURVIVAL on both entries. No reporter
    exists to echo the swapped declaration back (round 10's conspiracy),
    and the mechanism is asserted positively: clean baselines exist, so
    exit-4 vacuity (round 11's fail-open regression) cannot pass this."""
    import importlib.util
    src = (EVID / "mutant_registry.py").read_text()
    n1 = 'f"{T1}::test_a_variance_planted_in_the_emission_is_caught"'
    n2 = 'f"{T2}::test_indented_helper_definition_is_followed"'
    assert src.count(n1) == 1 and src.count(n2) == 1
    swapped = src.replace(n1, "@@TMP@@").replace(n2, n1).replace("@@TMP@@", n2)
    mod_path = tmp_path / "mutant_registry_swapped.py"
    mod_path.write_text(swapped)
    spec = importlib.util.spec_from_file_location("mr_swapped", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sub = tuple(e for e in mod.ENTRIES if e[0] in ("R4A", "F1"))
    assert {e[0] for e in sub} == {"R4A", "F1"}
    # the REAL root, not the module's own tmp-derived one (PROCESS-R11-1)
    verified, problems = mod.execute(sub, root=MR.ROOT)
    # mechanism first: the run genuinely happened
    assert len(verified["clean"]) == 2 and all(
        n >= 1 for n in verified["clean"].values()), verified["clean"]
    # and the swap is refused by OBSERVATION: both entries survive
    survived = {p.split(":")[0] for p in problems if "SURVIVED" in p}
    assert survived == {"R4A", "F1"}, (survived, problems)
    assert verified["kills"] == [], verified["kills"]
    assert mod.coverage_problems(sub, verified), "coverage must also refuse"


def test_no_kill_claim_protocol_remains():
    """The reporter is not hardened, it is GONE — a regression reintroducing
    any kill-claim channel (a reporter function, the kill-log env var, or
    pytest-side attribution) is this test's failure."""
    for path in (EVID / "mutant_registry.py",
                 ROOT / "tests" / "test_0011_policy_matrix.py",
                 ROOT / "tests" / "test_0011_mutant_registry.py"):
        src = path.read_text()
        # needles assembled so this test's own source cannot satisfy them
        for needle in ("def record" + "_kill", "VERACIUM_MUTANT" + "_KILL_LOG",
                       "PYTEST_CURRENT" + "_TEST"):
            assert needle not in src, (path.name, needle)


class _CheckResult:
    def __init__(self, code, err):
        self.returncode, self.stderr = code, err


def _run_main_against(record_text):
    """EVIDENCE-M10-1: corrupt operands are exercised through the INTERNAL
    helper on a copy — the command entry point is pinned to RECORD and
    takes no selector, environmental or otherwise."""
    import io
    import contextlib
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json",
                                     delete=False) as fh:
        fh.write(record_text)
        path = pathlib.Path(fh.name)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            code = MR.run_check(path)
    finally:
        path.unlink()
    return _CheckResult(code, err.getvalue())


def test_corrupt_records_are_refused_by_main_itself():
    """EVIDENCE-R9-1: removing the refusal branches left every in-memory
    test green — the checks were exercised as functions, never as the
    behavior main() actually runs. These invoke the check against each
    corrupt record and require refusal. Grammar refusals happen BEFORE
    recomputation, so all of these are fast."""
    raw = (EVID / "mutant_results.json").read_text()

    # duplicate key: json.loads would keep the LAST value silently
    r = _run_main_against('{\n "schema": false,' + raw[1:])
    assert r.returncode == 1 and "duplicate JSON key" in r.stderr

    # ungoverned found_by, REGENERATED so totals carry the alien partition
    rec2 = json.loads(raw)
    rec2["entries"][6]["found_by"] = "banana"
    r = _run_main_against(json.dumps(rec2, indent=1, sort_keys=True) + "\n")
    assert r.returncode == 1 and "governed partition" in r.stderr

    # bool-for-int on schema; a claimed kill that is not a REAL failure
    # (exit 0, or failed 0); a minimality witness that did not pass; an
    # alien totals key
    for mutate, needle in (
            (lambda d: d.__setitem__("schema", True), "not 4"),
            (lambda d: d["verified"]["kills"][0].__setitem__("exit", 0),
             "observed"),
            (lambda d: d["verified"]["kills"][0].__setitem__("failed", 0),
             "observed"),
            (lambda d: d["verified"]["leave_one_out"][0].__setitem__(
                "exit", 1), "leave the node PASSING"),
            (lambda d: d["totals"].__setitem__("banana", 1),
             "closed set")):
        d = json.loads(raw)
        mutate(d)
        r = _run_main_against(json.dumps(d, indent=1, sort_keys=True) + "\n")
        assert r.returncode == 1, needle
        assert needle in r.stderr, (needle, r.stderr[:300])


def test_type_coerced_kill_exit_is_refused():
    """PROCESS-R8-1(2): True == 1 under dict equality, so a bool smuggled
    into the kill's exit field would claim the exact int. The grammar pins
    exact int types and the byte comparison distinguishes true from 1."""
    raw = (EVID / "mutant_results.json").read_text()
    d = json.loads(raw)
    d["verified"]["kills"][0]["exit"] = True
    assert d["verified"]["kills"][0]["exit"] == 1, "coercion premise"
    assert MR.validate_record(d), "bool-for-int passed the grammar"
    r = _run_main_against(json.dumps(d, indent=1, sort_keys=True) + "\n")
    assert r.returncode == 1


def test_non_canonical_bytes_are_refused_by_main():
    """Same CONTENT, different whitespace: a parse-normalise round trip
    would bless it; the raw-bytes comparison must not."""
    raw = (EVID / "mutant_results.json").read_text()
    r = _run_main_against(json.dumps(json.loads(raw), sort_keys=True) + "\n")
    assert r.returncode == 1
    # refused BEFORE any recomputation (EVIDENCE-M10-1's ordering fix):
    # canonical form is a property of the bytes themselves
    assert "canonical serialisation of their own content" in r.stderr


def test_the_shipped_record_recomputes_and_diverges_on_tamper():
    """The record was once WRITE-ONLY. build_record over the shipped
    verified block must reproduce the shipped record exactly, and any
    tamper diverges."""
    shipped = json.loads((EVID / "mutant_results.json").read_text())
    rebuilt = MR.build_record(MR.ENTRIES, shipped["verified"])
    assert rebuilt == shipped, "the shipped record does not recompute"
    tampered = copy.deepcopy(shipped)
    tampered["totals"]["all"] = 99
    assert tampered != rebuilt
    tampered2 = copy.deepcopy(shipped)
    tampered2["entries"][0]["mutation"] = "something else"
    assert tampered2 != rebuilt
    tampered3 = copy.deepcopy(shipped)
    tampered3["entries"][0]["hunks"][0]["new"] = "something else"
    assert tampered3 != rebuilt


def test_the_real_entry_point_passes_on_the_shipped_tree():
    """The control: the REAL command, no operand, no selector — the pinned
    path over the shipped record and a full observed campaign. This is the
    expensive test (the campaign is ~45 isolated pytest runs) and the only
    one that pays for it."""
    import subprocess
    import sys as _sys
    r = subprocess.run([_sys.executable, str(EVID / "mutant_registry.py")],
                       capture_output=True, text=True, cwd=ROOT,
                       timeout=1200)
    assert r.returncode == 0, (r.stdout + r.stderr)[-500:]
    assert "runner-observed" in r.stdout
    assert "VERACIUM_MUTANT_RECORD" not in (
        EVID / "mutant_registry.py").read_text(), (
        "the environment selector is back (EVIDENCE-M10-1)")


def test_the_live_tree_is_never_mutated_and_campaigns_isolate():
    """The campaign runs in a private snapshot (research F-E generalized):
    the first design patched the live tree with verified restores, and one
    afternoon supplied three failure modes — interleaved concurrent
    campaigns froze a mutation into the fold checker, a killed campaign
    left a frozen hunk, and the closure gate's concurrent ledger commands
    read artifacts mid-mutation. Here two campaigns run CONCURRENTLY and
    both observe their kill, while the live artifact stays byte-identical
    throughout."""
    import concurrent.futures
    art = ROOT / "specs" / "evidence" / "0011" / "policy_matrix.py"
    before = art.read_bytes()
    e = next(e for e in MR.ENTRIES if e[0] == "R5A")
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        futs = [pool.submit(MR.execute, (e,), MR.ROOT) for _ in range(2)]
        results = [f.result() for f in futs]
    assert art.read_bytes() == before, "the live tree was mutated"
    for verified, problems in results:
        assert problems == [], problems
        assert [k["id"] for k in verified["kills"]] == ["R5A"], verified


def test_a_hunk_outside_its_defense_is_refused():
    """Research F-B (the proxy-kill): an observed failure proves the test
    NOTICED the hunk, not that the hunk touched the defense — a hunk
    mutating a fixture, helper or constant on the node's execution path
    is a guaranteed kill measuring nothing. Every hunk must fall inside
    the source span of the top-level function or constant the entry
    names as its defense."""
    pm = "specs/evidence/0011/policy_matrix.py"
    # `make_edge` is on every node's execution path but is NOT the defense
    outside = MR.ENTRIES + (("P1", "dev", "x", MR.ENTRIES[0][3], "problems",
                             ((pm, 'relation="works_as"', 'relation="x"'),)),)
    assert any("OUTSIDE the source span" in b
               for b in MR.validate_entries(outside))
    ghostname = MR.ENTRIES + (("P2", "dev", "x", MR.ENTRIES[0][3],
                               "no_such_function",
                               ((pm, "emitted_keys.count(k) > 1",
                                 "emitted_keys.count(k) > 3"),)),)
    assert any("names no top-level function" in b
               for b in MR.validate_entries(ghostname))
    assert not MR.validate_entries(MR.ENTRIES), "pristine control"


def test_a_duplicate_mutation_is_refused_at_the_real_boundary(tmp_path,
                                                              monkeypatch):
    """PROCESS-R12-1: R5A duplicated under a fresh DUPR5A id — unique-ids
    passed, --write produced 22 entries, --check exited 0, and the totals
    reported a dev mutant that was a second label for a reviewer's. The
    mutant's identity carrier moved to the hunk bundle in schema 4 and
    uniqueness stayed on the ids. This drives the DUP registry through the
    REAL boundaries on disk (the R11 lesson: not an in-memory analog):
    run_check refuses BEFORE any campaign spends a subprocess, and --write
    refuses without writing."""
    import importlib.util
    src = (EVID / "mutant_registry.py").read_text()
    needle = "ENTRIES = ("
    assert src.count(needle) == 1
    dup_entry = (
        '    ("DUPR5A", "dev",\n'
        '     "a second label for R5A\'s mutation",\n'
        '     f"{T1}::test_a_duplicate_hiding_a_missing_cell_is_caught",\n'
        '     "problems",\n'
        '     ((PM, "emitted_keys.count(k) > 1",'
        ' "emitted_keys.count(k) > 2"),)),\n')
    dupped = src.replace(needle, needle + "\n" + dup_entry, 1)
    # pin the copied module to the REAL root: since PROCESS-R14-1 the
    # guard (and therefore identity) is deliberately file-dependent, so
    # a tmp-derived ROOT would refuse on missing files instead of on the
    # duplicate — the R11 lesson, applied here a second time
    root_line = "ROOT = pathlib.Path(__file__).resolve().parents[3]"
    assert dupped.count(root_line) == 1
    dupped = dupped.replace(root_line,
                            f"ROOT = pathlib.Path({str(MR.ROOT)!r})")
    mod_path = tmp_path / "mutant_registry_dup.py"
    mod_path.write_text(dupped)
    spec = importlib.util.spec_from_file_location("mr_dup", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert len(mod.ENTRIES) == 22
    assert any("duplicate mutation" in b and "DUPR5A" in b
               for b in mod.validate_entries())
    # --check boundary: refuses at validation, BEFORE any campaign run
    import io
    import contextlib
    import time
    err = io.StringIO()
    t0 = time.monotonic()
    with contextlib.redirect_stderr(err):
        code = mod.run_check(MR.RECORD)
    assert code == 1 and "duplicate mutation" in err.getvalue()
    assert time.monotonic() - t0 < 5, (
        "the duplicate refusal must precede the campaign, not follow it")
    # --write boundary: refuses and writes NOTHING
    monkeypatch.setattr(mod.sys, "argv", ["mutant_registry.py", "--write"])
    err2 = io.StringIO()
    with contextlib.redirect_stderr(err2):
        code = mod.main()
    assert code == 1 and "duplicate mutation" in err2.getvalue()
    assert not mod.RECORD.exists(), (
        "--write on a duplicate-carrying registry wrote a record")


def test_mutation_identity_is_the_resulting_transformation():
    """PROCESS-R12-1/R13-1, faces two through four: identity is the
    sha256 of the artifact bytes the bundle PRODUCES, so every
    representation-slide collapses — window (three exactly-once
    old-texts of one edit), partitioning (C2's two hunks merged into one
    wider hunk), order — while genuinely different transformations stay
    distinct. The whitespace-folded screen refuses the cheapest
    semantically-equivalent variant for human review."""
    pm = "specs/evidence/0011/policy_matrix.py"
    slices = [("emitted_keys.count(k) > 1", "emitted_keys.count(k) > 2"),
              ("keys.count(k) > 1", "keys.count(k) > 2"),
              ("count(k) > 1", "count(k) > 2")]
    ids = {MR.mutation_identity(((pm, o, n),)) for o, n in slices}
    assert len(ids) == 1, ids
    assert MR.mutation_identity(((pm, "count(k) > 1",
                                  "count(k) >= 2"),)) not in ids
    m3 = next(e for e in MR.ENTRIES if e[0] == "M3")
    assert MR.mutation_identity(m3[5]) == MR.mutation_identity(
        tuple(reversed(m3[5])))
    c2 = next(e for e in MR.ENTRIES if e[0] == "C2")
    assert MR.mutation_identity(c2[5]) == MR.mutation_identity(
        (_merged_c2_hunk(),))
    r5a = next(e for e in MR.ENTRIES if e[0] == "R5A")
    ws = MR.ENTRIES + (("WSV", "dev", "x", r5a[3], r5a[4],
                        ((pm, "emitted_keys.count(k) > 1",
                          "emitted_keys.count(k) >  2"),)),)
    assert any("whitespace of the mutated result" in b
               for b in MR.validate_entries(ws))
    # the record-side carrier enforces the same closure (both carriers)
    shipped = json.loads((EVID / "mutant_results.json").read_text())
    d = json.loads(json.dumps(shipped))
    d["entries"].append(dict(d["entries"][2], id="DUPX"))
    assert any("same normalized hunk bundle" in b
               for b in MR.validate_record(d))
    assert not MR.validate_record(shipped), "pristine control"


def _merged_c2_hunk():
    """C2's two edits as ONE wider hunk spanning both sites — the
    round-13 partitioning attack, byte-identical in effect."""
    c2 = next(e for e in MR.ENTRIES if e[0] == "C2")
    art = c2[5][0][0]
    src = (ROOT / art).read_text()
    i = src.index('"candidate rows"')
    j = src.index('distinct"),') + len('distinct"),')
    old_b = src[i:j]
    new_b = old_b
    for _a, o, n in c2[5]:
        assert o in new_b
        new_b = new_b.replace(o, n, 1)
    return (art, old_b, new_b)


def test_partitioned_duplicates_are_refused_at_the_real_boundary(tmp_path):
    """PROCESS-R13-1 at the real boundary: (a) DUPC2 as the merged
    single hunk beside the original C2; (b) the constant-cardinality
    replacement — C1 removed, the merged duplicate kept — 21 entries,
    finder totals unchanged, one mutant gone and another counted twice.
    Both refuse at --check fast (before any campaign subprocess) and at
    --write without writing."""
    import importlib.util
    import io
    import contextlib
    import time
    src = (EVID / "mutant_registry.py").read_text()
    # pin the copied module to the REAL root — its own derivation would
    # point at tmp_path and every identity would degrade (the R11
    # fail-open lesson, applied to this test itself)
    root_line = "ROOT = pathlib.Path(__file__).resolve().parents[3]"
    assert src.count(root_line) == 1
    src = src.replace(root_line,
                      f"ROOT = pathlib.Path({str(MR.ROOT)!r})")
    entry = ("DUPC2", "dev", "merged single-hunk relabel of C2",
             next(e for e in MR.ENTRIES if e[0] == "C2")[3],
             "check_census_figures", (_merged_c2_hunk(),))
    needle = "ENTRIES = ("
    dupped = src.replace(needle, needle + "\n    " + repr(entry) + ",", 1)
    ci = dupped.index('    ("C1", "dev",')
    cj = dupped.index('    ("C2", "dev",')
    card = dupped[:ci] + dupped[cj:]
    for name, text, n_expected in (("dup", dupped, 22), ("card", card, 21)):
        mod_path = tmp_path / f"mutant_registry_{name}.py"
        mod_path.write_text(text)
        spec = importlib.util.spec_from_file_location(f"mr_{name}", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert len(mod.ENTRIES) == n_expected, name
        err = io.StringIO()
        t0 = time.monotonic()
        with contextlib.redirect_stderr(err):
            code = mod.run_check(MR.RECORD)
        assert code == 1 and "duplicate mutation" in err.getvalue(), (
            name, err.getvalue()[:300])
        assert time.monotonic() - t0 < 5, (
            f"{name}: the refusal must precede the campaign")
        mod.sys.argv = ["mutant_registry.py", "--write"]
        err2 = io.StringIO()
        with contextlib.redirect_stderr(err2):
            code = mod.main()
        assert code == 1 and "duplicate mutation" in err2.getvalue(), name
        assert not mod.RECORD.exists(), (
            f"{name}: --write on a duplicate-carrying registry wrote")


def test_digested_bytes_are_executed_bytes_even_for_dependent_hunks(
        tmp_path, monkeypatch):
    """Research, round-13 pre-seal: 'the bytes the bundle produces' is
    well-defined only if identity and execution share one apply path.
    This proves it BEHAVIORALLY on an ORDER-DEPENDENT bundle (the second
    hunk's old text exists only after the first applies): the identity's
    digest equals the sha256 of the file bytes the campaign's own
    _Restorer leaves behind — same function, same order, by
    construction — while the reversed bundle degrades instead of
    silently digesting something that would never run."""
    import hashlib
    art_dir = tmp_path / "specs" / "evidence" / "0011"
    art_dir.mkdir(parents=True)
    art = "specs/evidence/0011/fake_artifact.py"
    (tmp_path / art).write_text("alpha = 1\nbeta = 2\n")
    dependent = ((art, "alpha = 1", "alpha = 1  # W1"),
                 (art, "1  # W1\nbeta", "1  # W1\nbeta_renamed"))
    monkeypatch.setattr(MR, "ROOT", tmp_path)
    ident = MR.mutation_identity(dependent)
    assert len(ident) == 1 and ident[0][1] is not None, ident
    rest = MR._Restorer(tmp_path)
    assert rest.apply(dependent) == []
    executed = (tmp_path / art).read_text()
    assert hashlib.sha256(executed.encode()).hexdigest() == ident[0][1], (
        "identity digested bytes the campaign did not execute")
    assert rest.restore() == []
    # the reversed bundle cannot apply from pristine: it degrades loudly
    rev = tuple(reversed(dependent))
    assert MR.mutation_identity(rev)[0][1] is None, (
        "an unappliable order digested as if it ran")


def test_out_of_tree_paths_refuse_before_any_read(tmp_path):
    """PROCESS-R14-1: both carriers computed mutation identity BEFORE
    validating paths — a record hunk naming /etc/passwd validated clean,
    and /bin/sh was READ and crashed the checker with an uncaught decode
    error (ROOT / '/etc/passwd' IS '/etc/passwd', the R8-1(3) footgun
    reachable through the new code path). Now ONE shared guard runs
    first in both carriers, membership as a pure string check, so an
    out-of-set path is refused with NO filesystem access. The no-read
    witness is /bin/sh itself: reading it raises UnicodeDecodeError, so
    a clean named refusal without a traceback proves the read never
    happened. Driven through the REAL entry point for the record
    carrier, with a latency bound proving no campaign ran."""
    import time
    raw = (EVID / "mutant_results.json").read_text()
    for art in ("/etc/passwd", "../../../etc/passwd", "/bin/sh"):
        # entries carrier: named refusal, no exception
        g = MR.ENTRIES + (("Z1", "dev", "x", MR.ENTRIES[0][3], "problems",
                           ((art, "a", "b"),)),)
        bad = MR.validate_entries(g)
        assert any("Z1" in b and "OUTSIDE the closed mutable set" in b
                   for b in bad), (art, bad[:2])
        # record carrier at the REAL boundary
        d = json.loads(raw)
        d["entries"][0]["hunks"][0]["artifact"] = art
        t0 = time.monotonic()
        r = _run_main_against(json.dumps(d, indent=1, sort_keys=True)
                              + "\n")
        assert r.returncode == 1, art
        assert "OUTSIDE the closed mutable set" in r.stderr, (art,
                                                             r.stderr[:200])
        assert "Traceback" not in r.stderr, (
            f"{art}: the checker crashed instead of refusing — the "
            f"target was read")
        assert time.monotonic() - t0 < 5, (
            f"{art}: the refusal must precede the campaign")
    # identity itself is defensive: degrades without reading or raising
    assert MR._identity((("/bin/sh", "a", "b"),), fold_ws=False)[0][1] \
        is None


def test_a_symlink_in_the_campaign_tree_refuses_before_any_copy(tmp_path):
    """PROCESS-R14-1's snapshot half (research): copytree with
    symlinks=False DEREFERENCES, so a committed symlink anywhere under
    the copied dirs is a read of its target — escaping the tree if the
    target does — and the artifact guard never sees it, because the
    snapshot copies the whole tree. The pre-scan refuses on the FIRST
    symlink, before any copy: the target here is /bin/sh, whose
    dereference-copy would land binary bytes in the snapshot, so a named
    refusal that mentions the link and produces no snapshot proves
    nothing was read through it."""
    tree = tmp_path / "specs" / "evidence" / "0011"
    tree.mkdir(parents=True)
    (tmp_path / "specs" / "evidence" / "0011" / "real.py").write_text(
        "x = 1\n")
    (tree / "innocuous.py").symlink_to("/bin/sh")
    verified, problems = MR.execute((MR.ENTRIES[0],), root=tmp_path)
    assert verified == dict(clean={}, kills=[], leave_one_out=[])
    assert any("symlink in the campaign tree" in p and "innocuous.py" in p
               for p in problems), problems
    assert any("before any copy" in p for p in problems), problems
    # the DIRECTORY form (research): os.walk(followlinks=False) surfaces
    # a symlinked subdir in dirnames and never descends it, while
    # copytree(symlinks=False) DESCENDS and reads the external target —
    # so a filenames-only scan would pass what the copy then reads. The
    # scan checks dirnames too, and checks BEFORE pruning, even for a
    # link named like a pruned dir.
    (tree / "innocuous.py").unlink()
    (tree / "linkdir").symlink_to("/etc")
    verified, problems = MR.execute((MR.ENTRIES[0],), root=tmp_path)
    assert verified["kills"] == []
    assert any("symlink in the campaign tree" in p and "linkdir" in p
               for p in problems), problems
    (tree / "linkdir").unlink()
    (tree / "archives").symlink_to("/etc")     # named like a pruned dir
    verified, problems = MR.execute((MR.ENTRIES[0],), root=tmp_path)
    assert any("symlink in the campaign tree" in p and "archives" in p
               for p in problems), problems
