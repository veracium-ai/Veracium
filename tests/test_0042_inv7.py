"""specs/0042 INV-7 — OBSERVATION-ONLY, as a FOUR-ARM decision-trace diff (tranche 6b, 2026-09-19).

The frozen invariant: capture the decision trace with counters HEALTHY, FORCED TO ERROR and on an
UNINSTRUMENTED tree, and assert the traces byte-identical; the bypass at the four hot predicates
(tranche 2b) adds a fourth arm — instrumented but BYPASSED, the shipped default. The trace comes from
an instrument that is not the census (`specs/evidence/0042/inv7_observer.py`: every declared
enforcement function wrapped from outside, one content-free record per exit), because "two arms that
share the instrument cannot detect the instrument".

Three legs here:
  1. THE MINIATURE, in-process: the runtime leg's declining executions (tests/test_0042_sites.py —
     one per declared id) replayed under healthy, failing and off with the observer installed; the
     three observer traces are one byte string. The uninstrumented arm cannot run in-process (it is a
     different src tree), so:
  2. THE PINNED TRANSCRIPT: `specs/evidence/0042/inv7_transcript.txt` is the harness's four-arm run
     over the named suites, pinned to the commit it ran against; the pin must be an ancestor of HEAD
     with src/ unchanged since, and the transcript must read IDENTICAL with the exclusions it names
     equal to the ones the declaration derives today.
  3. THE MATRIX: the harness's comparison fails on each mutant (a changed record, a shorter arm, a
     census sequence the observer did not see, an id outside the declaration, a measured counter in
     the failing arm).
"""
from __future__ import annotations

import ast
import collections
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "specs" / "evidence" / "0042"
TRANSCRIPT = EVIDENCE / "inv7_transcript.txt"


def _load(name, path):
    """By path (tests/ is not a package) and REGISTERED in sys.modules: the observer rebinds from-import
    bindings by sweeping sys.modules, so a module it cannot see would call around it."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m


observer = _load("inv7_observer", EVIDENCE / "inv7_observer.py")
harness = _load("inv7_harness", EVIDENCE / "inv7_harness.py")
declaration = _load("inv7_declaration", EVIDENCE / "declaration.py")
ID_TO_SYMBOL = {row[0]: row[3] for row in declaration.DECLARATION}


def _nested_symbols():
    """The declared symbols an outside instrument cannot reach: nested inside a function."""
    out = set()
    for sym in {row[3] for row in declaration.DECLARATION}:
        parts = sym.split(":")[1].split(".")
        if len(parts) > 1 and not parts[0][0].isupper():
            out.add(sym)
    return out


# ---- leg 1: the miniature -------------------------------------------------------------------------

# loaded at COLLECTION, like the leg itself: its SITES snapshot reads the registry at import, and the census
# tests' autouse fixture clears the registry once tests RUN — a fixture-time load would snapshot nothing
LEG = _load("inv7_sites_leg", ROOT / "tests" / "test_0042_sites.py")


def _observer_names():
    """Every upper-case module-level name of the observer, DERIVED from the module (with or without the underscore)."""
    import re
    return {n for n in vars(observer) if re.fullmatch(r"_?[A-Z][A-Z0-9_]*", n)}


@pytest.fixture(autouse=True)
def _observer_state_restored():
    """Snapshot before each test and restore after it EVERYTHING the observer classifies as mutable state
    (`observer._STATE` — containers in place, scalars by assignment), and assert everything it classifies as a
    constant (`observer._CONSTANTS`) UNCHANGED at teardown — a mutable thing misfiled as a constant fails by name on
    the first test that mutates it. Research, round 7: three leaks of this class in one round — restore-what-you-touch
    is a per-test discipline over fourteen things, and the fifteenth, or the first forgotten one, comes back as a
    wrong symbol index that is silent, order-dependent, and reads as a real divergence. The classification's
    COMPLETENESS is asserted by `test_every_upper_case_name_of_the_observer_is_classified`, a test rather than this
    fixture, so that on a tree whose observer predates the classification (the RED/GREEN transcript runs these tests
    against the round-6 pin) the other tests fail at THEIR assertion, not at this fixture's setup; there the fixture
    restores every derived container and nothing else."""
    import copy
    state = set(getattr(observer, "_STATE", ())) or {n for n in _observer_names() if isinstance(getattr(observer, n), (list, dict, set, bytearray))}
    consts = set(getattr(observer, "_CONSTANTS", {}))
    snapshot = {n: copy.copy(getattr(observer, n)) for n in state}
    constants = {n: copy.copy(getattr(observer, n)) for n in consts}
    yield
    changed = sorted(n for n in consts if getattr(observer, n) != constants[n])
    assert changed == [], (changed, "a name classified as a constant was changed by this test — reclassify it as state")
    for n in state:
        v, s = getattr(observer, n), snapshot[n]
        if isinstance(v, (dict, set)):
            v.clear(); v.update(s)
        elif isinstance(v, (list, bytearray)):
            v[:] = s
        else:
            setattr(observer, n, s)


def test_every_upper_case_name_of_the_observer_is_classified():
    """The classification is COMPLETE and DISJOINT: every upper-case module-level name of the observer, derived from
    the module, is in `_STATE` (restored around every test) or in `_CONSTANTS` (asserted unchanged), never neither,
    never both; a new container OR scalar flag must be classified before this passes (research, round 7: a filter
    over containers alone would not see a scalar flag, and a name in neither list is invisible to both)."""
    derived = _observer_names()
    state, consts = set(observer._STATE), set(observer._CONSTANTS)
    assert not (state & consts), sorted(state & consts)
    assert derived == state | consts, (sorted(derived - (state | consts)), sorted((state | consts) - derived))
    assert all(isinstance(r, str) and r for r in observer._CONSTANTS.values())
    assert "DECL_PATH" in state                     # the one scalar install() reassigns is state, not a constant


@pytest.fixture(scope="module")
def leg():
    """The runtime leg's tables (tests/ is not a package; loaded by path at collection)."""
    return LEG


def _replay(arm, leg, skip=()):
    from veracium import census
    observer.install(str(EVIDENCE / "declaration.py"))
    observer.reset_records()
    orig_bump = census.Site._bump
    # counters are read from the leg's SITES snapshot (the Site objects captured at its import), never from
    # census.counters(): the census tests' autouse fixture CLEARS the registry, so under a shuffled order the
    # registry is empty here while the module-level sites keep counting (the sites leg's own rule)
    def _counters():
        return {sid: site.counters() for sid, site in leg.SITES.items()}
    before = _counters()
    census.trace_reset()
    try:
        if arm in ("healthy", "failing"):
            census.enable(True); census.trace(True)
            if arm == "failing":
                def boom(self, field):
                    raise census.CensusError("INV-7 forced counter failure")
                census.Site._bump = boom
        else:
            census.enable(False)
        for sid in sorted(leg.DECLINES):
            if sid in skip:
                continue
            entry = leg.DECLINES[sid]
            with pytest.MonkeyPatch.context() as mp:
                if isinstance(entry, leg.TwoPhase):
                    entry.run(entry.setup(mp))
                else:
                    entry(mp)
        for sid in sorted(leg.SURFACE_DRIVEN):
            leg.SURFACE_DRIVEN[sid]()
        after = _counters()
        deltas = {sid: {k: after[sid][k] - before[sid][k] for k in ("consulted", "fired", "errors")} for sid in after}
        return {"bytes": observer.records(), "decoded": observer.decoded(),
                "census_trace": census.trace_snapshot(), "counters": deltas}
    finally:
        census.Site._bump = orig_bump
        census.enable(False); census.trace(False); census.trace_reset()
        observer.uninstall()


@pytest.fixture(scope="module")
def arms(leg):
    return {arm: _replay(arm, leg) for arm in ("healthy", "failing", "off")}


def test_the_three_in_process_arms_produce_one_observer_trace(arms, leg):
    h, f, o = arms["healthy"], arms["failing"], arms["off"]
    assert h["bytes"] and h["bytes"] == f["bytes"] == o["bytes"], \
        {"healthy/failing": harness.first_divergence(h["bytes"], f["bytes"]),
         "healthy/off": harness.first_divergence(h["bytes"], o["bytes"])}
    # the replay REACHES the declared functions: every id the leg declines maps to a symbol the
    # observer recorded, except the nested ones it cannot wrap (named, derived)
    observed = {s for s, _, _ in h["decoded"]}
    expected = {ID_TO_SYMBOL[sid] for sid in list(leg.DECLINES) + list(leg.SURFACE_DRIVEN)} - _nested_symbols()
    assert expected <= observed, sorted(expected - observed)


def test_the_census_sees_a_subsequence_of_what_the_observer_sees(arms):
    for arm in ("healthy", "failing"):
        obs = [s for s, _, _ in arms[arm]["decoded"]]
        nested = _nested_symbols()
        needle = [ID_TO_SYMBOL[rec[1]] for rec in arms[arm]["census_trace"]
                  if rec[1] in ID_TO_SYMBOL and ID_TO_SYMBOL[rec[1]] not in nested]
        assert needle, arm
        assert harness.subsequence_match(needle, obs) == len(needle), arm


def test_the_failing_arm_is_unmeasured_everywhere_and_the_off_arm_counts_nothing(arms, leg):
    c = arms["failing"]["counters"]
    touched = {sid for sid, v in c.items() if v["errors"] or v["consulted"] or v["fired"]}
    assert touched == set(leg.DECLINES) | set(leg.SURFACE_DRIVEN), (sorted(touched ^ (set(leg.DECLINES) | set(leg.SURFACE_DRIVEN))))
    assert all(c[sid]["errors"] > 0 and c[sid]["consulted"] == 0 and c[sid]["fired"] == 0 for sid in touched)
    assert all(v == {"consulted": 0, "fired": 0, "errors": 0} for v in arms["off"]["counters"].values())
    # and the healthy arm measured every one of them
    hc = arms["healthy"]["counters"]
    assert all(hc[sid]["consulted"] >= 1 and hc[sid]["fired"] >= 1 and hc[sid]["errors"] == 0 for sid in touched)


def test_the_comparison_can_fail_a_replay_that_took_a_different_path(arms, leg):
    """The negative control: skip one declining execution and the trace diverges at a named record.

    The victim is chosen among the ids the observer can SEE: an id declared on a nested symbol is excluded from the
    wrapping by design (`observer._EXCLUDED`, "nested inside a function"), so its execution leaves no record and
    skipping it cannot change the trace. A positional pick over every id landed on one (`scope.closure.walk`) when two
    ids were added in 0041 round 10 — the control read as unfailable for a reason that had nothing to do with the
    comparison. The pick is now over the observable ids, and the victim's visibility is asserted, not assumed."""
    observer.install(str(EVIDENCE / "declaration.py"))
    try:
        hidden = {sym for sym, _why in observer._EXCLUDED}
    finally:
        observer.uninstall()
    symbol_of = {row[0]: row[3] for row in declaration.DECLARATION}
    observable = sorted(i for i in leg.DECLINES if symbol_of[i] not in hidden)
    assert len(observable) < len(leg.DECLINES), "the exclusion this pick guards against no longer exists — re-read it"
    victim = observable[len(observable) // 2]
    assert symbol_of[victim] not in hidden
    # the positive side: an UNSKIPPED replay after this test's own install/uninstall reproduces the arm, so a
    # difference below is the skip's and never an artefact of re-indexing
    assert _replay("healthy", leg)["bytes"] == arms["healthy"]["bytes"]
    other = _replay("healthy", leg, skip=(victim,))
    assert other["bytes"] != arms["healthy"]["bytes"]
    i = harness.first_divergence(other["bytes"], arms["healthy"]["bytes"])     # a BYTE index; records are 3 bytes
    assert i is not None and 0 <= i // observer.RECORD_WIDTH <= len(other["decoded"])


# ---- leg 2: the pinned four-arm transcript ------------------------------------------------------------

def _pin(text):
    m = re.search(r"^# generated \S+ against veracium @ ([0-9a-f]{7,40})$", text, re.M)
    assert m, "no pin line"
    return m.group(1)


def test_the_pinned_transcript_is_this_tree_and_reads_identical_across_four_arms():
    text = TRANSCRIPT.read_text()
    pin = _pin(text)
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode != 0:
        pytest.skip("no repository here: the transcript's pin cannot be checked against history")
    present = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{pin}^{{commit}}"], capture_output=True)
    assert present.returncode == 0, f"pin {pin[:7]} is not a commit here"
    anc = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", pin, "HEAD"], capture_output=True, text=True)
    if anc.returncode == 128:
        pytest.skip("shallow repository: the pin's ancestry cannot be checked")
    assert anc.returncode == 0, f"pin {pin[:7]} is not an ancestor of HEAD"
    moved = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", pin, "HEAD", "--", "src/"], capture_output=True, text=True).stdout.split()
    assert moved == [], f"src/ changed since the transcript's pin: {moved} — re-run the harness and re-pin"
    assert re.search(r"^VERDICT: observer traces IDENTICAL across 4 arms", text, re.M), "the transcript does not read IDENTICAL over four arms"
    rows = re.findall(r"^(healthy|failing|off|uninstrumented)\s+(\d+)\s+([0-9a-f]{64})\s+(.*)$", text, re.M)
    assert [r[0] for r in rows] == ["healthy", "failing", "off", "uninstrumented"]
    assert all(int(r[1]) > 0 for r in rows)
    # the verdict is PER TEST (a whole-trace digest also carries the non-reproducible tests' bytes, which is
    # why the arms' digests may differ while every compared test agrees): each arm compared with none differing
    per_arm = re.findall(r"^  (healthy|failing|off): (\d+) tests compared, (\d+) differing, (\d+) not in both$", text, re.M)
    assert [a for a, *_ in per_arm] == ["healthy", "failing", "off"], per_arm
    assert all(int(c) > 0 and d == "0" and n == "0" for _, c, d, n in per_arm), per_arm
    assert len({c for _, c, *_ in per_arm}) == 1                     # the same compared set in every arm
    # and the census arms' cross-checks read as the invariant requires
    assert re.search(r'^  healthy: \{.*"any_errors": false.*"subsequence_holds": true', text, re.M)
    assert re.search(r'^  failing: \{.*"all_unmeasured": true.*"subsequence_holds": true', text, re.M)
    assert re.search(r'^  off: \{"census_enabled": false, "registry_size": (\d+)\}', text, re.M).group(1) == str(len(declaration.DECLARED_IDS))
    # the reference arm's checks: census off, and (since round 15 the twin carries a real census; round 16 the REFERENCE one) a registry holding the
    # declaration's ids, equal to the off arm's as sets — its census-entry count is asserted with the derivation below;
    # parsed as JSON rather than matched as a key-order-dependent prefix
    _u = json.loads(re.search(r"^  uninstrumented: (\{.*\})$", text, re.M).group(1))
    assert _u.get("census_enabled") is False and _u.get("registry_size") == len(declaration.DECLARED_IDS) and _u.get("registry_equals_off") is True, _u
    # the tests the run could not compare are NAMED (a reader sees the boundary of the claim), each a node id
    # round 7c: the exclusions are the STANDING list (by name, with a cause) plus any NEWLY non-reproducible test —
    # the verdict line counts both apart, the two headings list them, and a NEW one is a finding the harness's exit
    # refuses, so a committed transcript carries none
    over = re.search(r"over (\d+) tests \(reference: uninstrumented; excluded by the STANDING list: (\d+); NEWLY non-reproducible this run: (\d+);", text); assert over, "the verdict line does not count the standing and the new exclusions apart"
    assert int(over.group(1)) > 0 and int(over.group(3)) == 0, over.groups()

    def listed(heading):
        m = re.search(r"^" + heading + r".*$", text, re.M); assert m, f"the transcript does not state {heading}"
        tail = []
        for line in text[m.end():].splitlines()[1:]:      # the indented lines under the heading, and nothing after
            if not line.startswith("  "):
                break
            tail.append(line.strip())
        return [l for l in tail if l and l != "(none)" and not l.startswith("cause:")]
    standing = listed("EXCLUDED BY THE STANDING LIST"); newly = listed("NEWLY NON-REPRODUCIBLE THIS RUN")
    assert len(standing) == int(over.group(2)) and all("::" in s for s in standing), standing
    assert newly == [], newly
    # every standing exclusion the transcript names is on the list the tree carries, with its cause printed
    real = harness.load_standing_exclusions()
    for s in standing:
        node = s.split("  [")[0]
        assert node in real, (node, "excluded but not on inv7_exclusions.STANDING")
        assert real[node][:60] in text, node
    excluded_tests = standing
    # the exclusions the transcript names are exactly the nested symbols the declaration derives today
    excluded = set(re.findall(r"^  (\S+\.py:\S+): nested inside a function", text, re.M))
    assert excluded == _nested_symbols(), (sorted(excluded ^ _nested_symbols()))
    # the suites the transcript ran are the committed NAMED suites, derived by the reach measurement from the
    # spec's sentence plus a greedy cover — and the reach table's own list is that file
    named = json.loads((EVIDENCE / "inv7_named_suites.json").read_text())
    suites_line = re.search(r"^suites: (.*)$", text, re.M).group(1).split()
    assert suites_line == named, (suites_line[:3], named[:3])
    reach_text = (EVIDENCE / "inv7_reach_table.txt").read_text()
    listed = re.findall(r"^  (tests/\S+)$", reach_text.split("NAMED SUITES", 1)[1], re.M)
    assert listed == named
    assert all(f in named for f in harness.SPEC_NAMED_SUITES if f in reach_text), "a spec-named suite the reach measured is missing from the named set"
    # the src commits between the twin and the pin are LISTED (a reader sees what the twin lacks); the claim
    # that matters is asserted elsewhere: the uninstrumented arm registered zero sites. (A first version asserted
    # every listed commit was an 0042 tranche — true until the next spec touched src; a census of the moment
    # mistaken for a rule.)
    # the twin is DERIVED from HEAD by un-instrumenting it (2026-09-19; an exported old commit is a different product
    # as soon as src/ moves for any other reason): the transcript states the derivation, and — since round 14 — the
    # number of declarations PRESERVED (round 15 bound to the source's own census; since round 16 to the REFERENCE census,
    # whose commit and digest the line prints from the transform's constants) equals the declaration's ids
    m = re.search(r"^twin \(uninstrumented\): derived from HEAD ([0-9a-f]{40}) by inv7_uninstrument\.py$", text, re.M)
    assert m, "the transcript's twin is not the derived one"
    assert m.group(1) == pin
    d = re.search(r"^twin derivation: (\d+) declare_site preserved, bound to the REFERENCE census \(accepted commit ([0-9a-f]{7})'s census\.py, sha256 ([0-9a-f]{16})\.\.\.\), (\d+) fire\(\) unwrapped, (\d+) consult blocks spliced, (\d+) census-enabled bypass blocks removed", text, re.M)
    assert d, "the transcript does not state the derivation"
    un = _load("inv7_uninstrument_r16t", EVIDENCE / "inv7_uninstrument.py")
    assert (d.group(2), d.group(3)) == (un.REFERENCE_CENSUS_COMMIT[:7], un.REFERENCE_CENSUS_SHA256[:16]), d.groups()[1:3]
    assert int(d.group(1)) == len(declaration.DECLARED_IDS), (d.group(1), len(declaration.DECLARED_IDS))
    assert int(d.group(4)) > 0 and int(d.group(5)) > 0 and int(d.group(6)) == 4       # the four hot-predicate bypasses
    # ROUND 15: "uninstrumented", MEASURED — the reference arm's printed checks carry 0 entries into census code during
    # the run, a disabled census, and a registry equal to the off arm's as sets (research's stage-1 conditions)
    u = re.search(r"^  uninstrumented: (\{.*\})$", text, re.M)
    assert u, "the transcript does not print the reference arm's checks"
    uc = json.loads(u.group(1))
    assert uc.get("census_code_entries") == 0 and uc.get("census_enabled") is False and uc.get("registry_equals_off") is True, uc
    # and the gates and the exit are PRINTED (research's N-1): every one true, the exit 0, read from the transcript itself
    g = re.search(r"^GATES \((\d+), (\d+) true; [^)]*\): (\{.*\})$", text, re.M)
    assert g and g.group(1) == g.group(2) and all(json.loads(g.group(3)).values()), g and g.group(0)[:200]
    # the gate NAME SET, not only their values (research's pre-commit note): a per-arm gate exists only when its arm ran,
    # so a run missing the off arm would otherwise pass by omitting uninstrumented:registry_equals_off
    assert {"uninstrumented:census_disabled", "uninstrumented:registry_equals_off", "uninstrumented:no_census_code_in_decisions",
            "uninstrumented:site_realized_equal",
            "off:census_disabled", "healthy:subsequence", "failing:all_unmeasured", "identical"} <= set(json.loads(g.group(3))), sorted(json.loads(g.group(3)))
    # ROUND 18 (N-6): the printed check — every run (the four arms and their four controls) imported the same Site
    sr = json.loads(re.search(r"^  site_realized: (\{.*\})$", text, re.M).group(1))
    assert sr["equal"] is True and sr["missing"] == [] and sr["distinct_digests"] == 1 and sr["runs"] == 8, sr
    assert re.search(r"^HARNESS EXIT: 0$", text, re.M)


# ---- leg 3: the harness's mutation matrix ------------------------------------------------------------

def _fabricate(tmp_path, arm, records, symbols=("m.py:f", "m.py:g"), labels=("None", "ValueError"), census=None, counters=None, enabled=False, boundaries=None, registry_size=2):
    d = tmp_path / arm; d.mkdir()
    recs = [(r[0], 0, r[1]) if len(r) == 2 else tuple(r) for r in records]       # (symbol, exit ordinal, label)
    raw = bytes(b for r in recs for b in r)
    (d / "observer_trace.bin").write_bytes(raw)
    bounds = boundaries if boundaries is not None else [[0, "t.py::a"], [2, "t.py::b"]]
    (d / "test_boundaries.jsonl").write_text("".join(json.dumps(b) + "\n" for b in bounds))
    summary = {"symbols": list(symbols), "labels": list(labels), "records": len(recs), "record_width": 3, "census_enabled": enabled,
               "census_registry_size": registry_size, "veracium_file": "x", "pytest_exit": 0,
               # ROUND 15: every arm records its registry's ids (the reference arm's must equal the off arm's, as sets), and
               # the reference arm records its entries into census code (0 required; None elsewhere: no hook runs there)
               "census_registry_ids": ["a.id", "b.id"],
               "census_code_entries": 0 if arm.startswith("uninstrumented") else None,
               # ROUND 18 (N-6): every run records the digest of the Site it imported; fabricated arms import the same one
               "site_realized": {"digest": "fabricated", "entries": [["mro", "fabricated"]]}}
    if census is not None:
        (d / "census_trace.jsonl").write_text("".join(json.dumps(r) + "\n" for r in census))
        summary["census_counters"] = counters or {}
    return summary


def test_the_harness_comparison_fails_on_each_mutant(tmp_path):
    """The matrix for specs/evidence/0042/inv7_harness.py (its `# Mutation-Matrix:` pointer names this test):
    the comparison is loaded here, from the file, and driven on fabricated arms."""
    harness = _load("inv7_harness_matrix", EVIDENCE / "inv7_harness.py")
    ids = {"a.id": "m.py:f", "b.id": "m.py:g"}
    good = [(0, 0), (1, 1), (0, 1)]
    healthy_census = [(1, "a.id", "None"), (2, "b.id", "ValueError")]
    ok_counters = {"a.id": {"consulted": 1, "fired": 1, "errors": 0}, "b.id": {"consulted": 1, "fired": 1, "errors": 0}}
    failing_counters = {"a.id": {"consulted": 0, "fired": 0, "errors": 2}, "b.id": {"consulted": 0, "fired": 0, "errors": 2}}
    S = {"healthy": _fabricate(tmp_path, "healthy", good, census=healthy_census, counters=ok_counters, enabled=True),
         "failing": _fabricate(tmp_path, "failing", good, census=healthy_census, counters=failing_counters, enabled=True),
         "off": _fabricate(tmp_path, "off", good), "uninstrumented": _fabricate(tmp_path, "uninstrumented", good)}
    arms = ["healthy", "failing", "off", "uninstrumented"]
    verdict, checks = harness.compare(tmp_path, arms, S, ids)
    assert verdict["identical"] and verdict["divergences"] == {}
    assert checks["healthy"]["subsequence_holds"] and checks["failing"]["all_unmeasured"]
    # mutant 1: one record changed in one arm → divergent, decoded at the record
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes([0, 0, 0, 1, 0, 0, 0, 0, 1]))
    v, _ = harness.compare(tmp_path, arms, S, ids)
    assert not v["identical"] and v["divergences"]["off"]["first_index"] == 1
    assert v["divergences"]["off"]["this"] == ("m.py:g", 0, "None") and v["divergences"]["off"]["reference"] == ("m.py:g", 0, "ValueError")
    # mutant 2: an arm cut short → divergent at the shorter length
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes([0, 0, 0, 1, 0, 1]))
    v, _ = harness.compare(tmp_path, arms, S, ids)
    assert not v["identical"] and v["divergences"]["off"]["first_index"] == 2 and v["divergences"]["off"]["lengths"] == [2, 3]
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes(b for s, l in good for b in (s, 0, l)))
    # mutant 3: the census claims a fired sequence the observer never saw → the subsequence check fails
    (tmp_path / "healthy" / "census_trace.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [(1, "b.id", "x"), (2, "b.id", "x"), (3, "b.id", "x")]))
    _, c = harness.compare(tmp_path, arms, S, ids)
    assert not c["healthy"]["subsequence_holds"]
    # mutant 4: a census id outside the declaration is LISTED, never silently dropped
    (tmp_path / "healthy" / "census_trace.jsonl").write_text(json.dumps((1, "phantom.id", "x")) + "\n")
    _, c = harness.compare(tmp_path, arms, S, ids)
    assert c["healthy"]["census_ids_not_in_declaration"] == ["phantom.id"]
    # mutant 5: a counter that MEASURED in the failing arm → not UNMEASURED everywhere
    S["failing"]["census_counters"] = {"a.id": {"consulted": 1, "fired": 0, "errors": 1}, "b.id": {"consulted": 0, "fired": 0, "errors": 2}}
    _, c = harness.compare(tmp_path, arms, S, ids)
    assert not c["failing"]["all_unmeasured"]
    # mutant 6: a compared test whose segment differs → DIVERGENT, and the TEST is named
    S["failing"]["census_counters"] = failing_counters
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes([0, 0, 0, 1, 0, 1, 1, 0, 1]))     # test b's segment changed
    v, _ = harness.compare(tmp_path, arms, S, ids)
    assert not v["identical"] and v["per_test"]["off"]["differing"] == ["t.py::b"]
    assert v["divergences"]["off"]["owning_test"] == "t.py::b" and v["divergences"]["off"]["first_index"] == 2
    # mutant 7: the control run shows test b is NOT reproducible → b is excluded by name and the verdict holds on a
    # ROUND 9, F2: this line used to DISCARD the fabricated control's summary, and the test passed anyway —
    # because `compare()` substituted the main arm's summary for an absent control's. So this fixture was
    # depending on the very defect round 9 removes, and it is the ONLY one of the three controls in this file
    # that did: the other two (`S["healthy-control"] = _fabricate(...)`, lines below) already kept theirs.
    # A real capture always has the control's own summary — the round-8 reviewer confirmed all eight were
    # present in the supplied one — so keeping it here is what the fixture always should have done.
    S["uninstrumented-control"] = _fabricate(tmp_path, "uninstrumented-control", [(0, 0, 0), (1, 0, 1), (1, 0, 0)])
    v, c = harness.compare(tmp_path, arms, S, ids, standing={})
    assert v["identical"] and v["control"]["non_reproducible"] == ["t.py::b"] and v["per_test"]["off"]["compared"] == 1
    # round 7 (research): b is NEWLY non-reproducible — excluded from the comparison, and a FINDING the exit refuses
    assert v["control"]["newly_non_reproducible"] == ["t.py::b"] and v["control"]["standing_excluded"] == []
    assert harness.final_status(v, c, S, arms) == 1 and v["gates"]["no_new_non_reproducible"] is False
    # … on the STANDING list by name with its cause, the same disagreement is an expected exclusion and the exit holds
    v, c = harness.compare(tmp_path, arms, S, ids, standing={"t.py::b": "fabricated: a known wall-clock dependence"})
    assert v["control"]["standing_excluded"] == ["t.py::b"] and v["control"]["newly_non_reproducible"] == [] and v["control"]["standing_causes"]["t.py::b"].startswith("fabricated")
    harness.final_status(v, c, S, arms); assert v["gates"]["no_new_non_reproducible"] is True     # (other gates carry earlier mutants' state)
    # a standing entry that names a test NOT in this run is neither excluded nor an error (it is listed as absent)
    v, _ = harness.compare(tmp_path, arms, S, ids, standing={"t.py::b": "x", "t.py::absent": "y"})
    assert v["control"]["standing_excluded"] == ["t.py::b"]
    # the real list loads and names its cause for every entry
    real = harness.load_standing_exclusions(); assert real and all(isinstance(k, str) and "::" in k and len(v_) > 40 for k, v_ in real.items())
    # … but a differing segment in test a still fails, control or no control
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes([1, 0, 1, 1, 0, 1, 1, 0, 0]))
    v, _ = harness.compare(tmp_path, arms, S, ids)
    assert not v["identical"] and v["per_test"]["off"]["differing"] == ["t.py::a"]
    (tmp_path / "off" / "observer_trace.bin").write_bytes(bytes(b for s, l in good for b in (s, 0, l)))
    # a test present in one arm only is a divergence too
    _fabricate(tmp_path, "extra", good, boundaries=[[0, "t.py::a"], [2, "t.py::z"]])
    v, _ = harness.compare(tmp_path, arms + ["extra"], {**S, "extra": S["off"]}, ids)
    assert not v["identical"] and v["per_test"]["extra"]["tests_not_in_both"] == ["t.py::b", "t.py::z"]
    # the pure helpers, at their edges
    assert harness.first_divergence(b"", b"") is None and harness.first_divergence(b"\x00\x00", b"") == 0
    assert harness.subsequence_match([], ["x"]) == 0 and harness.subsequence_match(["x", "y"], ["x", "z", "y"]) == 2
    assert harness.subsequence_match(["y", "x"], ["x", "y"]) == 1


# ---- round 6 (2026-09-20), cells C and E ---------------------------------------------------------------------------

def test_r6_5_i_identical_bytes_with_different_dictionaries_are_different_traces(tmp_path):
    """R6-5(i): the comparison compared encoded bytes without their symbol and label tables — identical bytes whose
    label meant False in one arm and True in another read identical=True. Now the comparison is over the DECODED
    records and the transcript carries a dictionary-independent canonical digest per arm."""
    ids = {"a.id": "m.py:f"}
    good = [(0, 0), (0, 1)]
    S = {"uninstrumented": _fabricate(tmp_path, "uninstrumented", good, symbols=("m.py:f",), labels=("False", "True")),
         "healthy": _fabricate(tmp_path, "healthy", good, symbols=("m.py:f",), labels=("True", "False"), census=[], counters={}, enabled=True)}
    v, _ = harness.compare(tmp_path, ["uninstrumented", "healthy"], S, ids)
    assert not v["identical"] and v["per_test"]["healthy"]["differing"] == ["t.py::a"]     # both records sit in test a
    assert v["divergences"]["healthy"]["this"] == ("m.py:f", 0, "True") and v["divergences"]["healthy"]["reference"] == ("m.py:f", 0, "False")
    assert v["canonical_digest"]["healthy"] != v["canonical_digest"]["uninstrumented"]
    # the control: the same bytes with the SAME dictionaries are one trace, and their canonical digests agree
    S["healthy"] = _fabricate(tmp_path / "again", "healthy", good, symbols=("m.py:f",), labels=("False", "True"), census=[], counters={}, enabled=True) if (tmp_path / "again").mkdir() is None else None
    import shutil; shutil.copytree(tmp_path / "again" / "healthy", tmp_path / "healthy", dirs_exist_ok=True)
    v, _ = harness.compare(tmp_path, ["uninstrumented", "healthy"], S, ids)
    assert v["identical"] and v["canonical_digest"]["healthy"] == v["canonical_digest"]["uninstrumented"]


def test_r6_5_iii_the_harness_exit_requires_every_arm_and_every_cross_check(tmp_path):
    """R6-5(iii), EXECUTED against the real harness on the sealed package: a one-test suite that failed only in the
    twin gave exit 0. `final_status` is now the exit: identical AND every arm's pytest exit 0 AND every cross-check."""
    ids = {"a.id": "m.py:f", "b.id": "m.py:g"}
    good = [(0, 0), (1, 1), (0, 1)]
    census = [(1, "a.id", "None"), (2, "b.id", "ValueError")]
    ok = {"a.id": {"consulted": 1, "fired": 1, "errors": 0}, "b.id": {"consulted": 1, "fired": 1, "errors": 0}}
    fail = {"a.id": {"consulted": 0, "fired": 0, "errors": 2}, "b.id": {"consulted": 0, "fired": 0, "errors": 2}}
    S = {"healthy": _fabricate(tmp_path, "healthy", good, census=census, counters=ok, enabled=True),
         "failing": _fabricate(tmp_path, "failing", good, census=census, counters=fail, enabled=True),
         "off": _fabricate(tmp_path, "off", good), "uninstrumented": _fabricate(tmp_path, "uninstrumented", good, registry_size=0)}
    arms = ["healthy", "failing", "off", "uninstrumented"]
    v, c = harness.compare(tmp_path, arms, S, ids)
    assert harness.final_status(v, c, S, arms) == 0 and all(v["gates"].values()), v["gates"]
    # gate 1: an arm whose pytest did not exit 0 — the reproduction's case
    S["uninstrumented"]["pytest_exit"] = 1
    assert harness.final_status(v, c, S, arms) == 1 and v["gates"]["pytest_exit:uninstrumented"] is False
    S["uninstrumented"]["pytest_exit"] = 0
    # gate 2: a cross-check that does not hold (the failing arm measured something)
    c2 = json.loads(json.dumps(c)); c2["failing"]["all_unmeasured"] = False
    assert harness.final_status(v, c2, S, arms) == 1
    # gate 3: the census saw an id outside the declaration
    c3 = json.loads(json.dumps(c)); c3["healthy"]["census_ids_not_in_declaration"] = ["phantom.id"]
    assert harness.final_status(v, c3, S, arms) == 1
    # gate 4 (round 15): the twin's registry is NOT the off arm's (or could not be compared)
    for bad in (False, None):
        c4 = json.loads(json.dumps(c)); c4["uninstrumented"]["registry_equals_off"] = bad
        assert harness.final_status(v, c4, S, arms) == 1 and v["gates"]["uninstrumented:registry_equals_off"] is False, bad
    # gate 4b (round 15): census code ran in the reference arm — once is enough — or the count is MISSING (None: the
    # hook could not be shown alive, or no observer read it). Both fail; 0 passes.
    for bad in (1, None):
        c4b = json.loads(json.dumps(c)); c4b["uninstrumented"]["census_code_entries"] = bad
        assert harness.final_status(v, c4b, S, arms) == 1 and v["gates"]["uninstrumented:no_census_code_in_decisions"] is False, bad
    # gate 4c: the reference arm's census was ENABLED
    c4c = json.loads(json.dumps(c)); c4c["uninstrumented"]["census_enabled"] = True
    assert harness.final_status(v, c4c, S, arms) == 1 and v["gates"]["uninstrumented:census_disabled"] is False
    assert harness.final_status(v, c, S, arms) == 0
    # gate 5 (round 7, research): a control pair disagreeing on a test NOT on the standing list is a finding → exit 1;
    # the same test on the standing list by name → excluded, exit 0
    S["healthy-control"] = _fabricate(tmp_path, "healthy-control", [(0, 0), (1, 1), (1, 0)], census=census, counters=ok, enabled=True)
    v5, c5 = harness.compare(tmp_path, arms, S, ids, standing={})
    assert v5["control"]["newly_non_reproducible"] == ["t.py::b"] and harness.final_status(v5, c5, S, arms) == 1 and v5["gates"]["no_new_non_reproducible"] is False
    v6, c6 = harness.compare(tmp_path, arms, S, ids, standing={"t.py::b": "fabricated cause"})
    assert v6["control"]["standing_excluded"] == ["t.py::b"] and harness.final_status(v6, c6, S, arms) == 0


_SCAN_CACHE: dict = {}


def _scan_rows(src, module):
    """The binding scan's rows for one module, scanned ONCE per session (it reads the whole tree)."""
    if not _SCAN_CACHE:
        inst = _load("installed_sites_for_inv7", EVIDENCE / "installed_sites.py")
        for r in inst.scan(src):
            _SCAN_CACHE.setdefault(r["module"], []).append(r)
    return _SCAN_CACHE.get(module, [])


def _sites_per_exit(tree, qual: str, sites: set[str]):
    """{exit-statement ordinal: the declared sites whose decision leaves the function THROUGH that statement} for
    the function `qual`, or None if it is absent.

    ROUND 7, F3b. The previous guard COUNTED a function's fire-carrying exits and compared the count to its number
    of sites — a necessary condition standing in for a sufficient one, and the reviewer built the fixture that
    separates them: two sites sharing ONE return, plus a second return repeating only one of them, gives two exits
    for two sites and passes while the two sites still collide on one ordinal. What the observer actually needs is
    the ASSOCIATION: its record is (symbol, exit ordinal, label), so two sites reaching the SAME exit statement of
    the SAME function produce records that cannot be told apart.

    Two forms are followed: a fire INSIDE the exit statement (`return S.fire(x)`, `raise S.fire(e)`), and the
    round-7 one-return form, where the fire is an assignment (`q = S.fire(q)`) and the value leaves through a later
    `return q` — one hop, by name, within the same body. A fire whose value reaches an exit by any other route is
    NOT followed and is reported under the ordinal `None`, so it is visible rather than silently attributed."""
    import ast, collections
    target = [None]

    def find(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = ".".join(stack + [child.name])
                if q == qual and not isinstance(child, ast.ClassDef):
                    target[0] = child
                find(child, stack + [child.name])
            else:
                find(child, stack)
    find(tree, [])
    fn = target[0]
    if fn is None:
        return None

    def own(node):
        """This body's nodes: nested scopes bind their own exits."""
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            yield c
            yield from own(c)

    def fired_in(node):
        return {c.func.value.id for c in ast.walk(node)
                if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "fire"
                and isinstance(c.func.value, ast.Name) and c.func.value.id in sites}

    exits = [c for c in own(fn) if isinstance(c, (ast.Return, ast.Raise))]
    by_name = {}                                     # NAME assigned a fire's value -> the sites in that assignment
    for c in own(fn):
        if isinstance(c, ast.Assign) and len(c.targets) == 1 and isinstance(c.targets[0], ast.Name):
            s = fired_in(c.value)
            if s:
                by_name.setdefault(c.targets[0].id, set()).update(s)
    out = collections.defaultdict(set)
    attributed = set()
    for ordinal, c in enumerate(exits):
        value = c.value if isinstance(c, ast.Return) else c.exc
        direct = fired_in(c)
        out[ordinal] |= direct; attributed |= direct
        if isinstance(value, ast.Name) and value.id in by_name:
            out[ordinal] |= by_name[value.id]; attributed |= by_name[value.id]
    unrouted = set().union(*by_name.values()) if by_name else set()
    unrouted |= {s for c in own(fn) for s in fired_in(c)}
    unrouted -= attributed
    if unrouted:
        out[None] = unrouted
    return dict(out)


def test_r6_5_ii_every_declared_site_has_its_own_exit_statement_so_exit_keyed_records_separate_them():
    """R6-5(ii), as ROUND 7 makes it exact: an exit-keyed record separates two sites of one function only if no
    EXIT STATEMENT carries more than one of them. Asserted over the declaration at HEAD by the site-to-exit
    ASSOCIATION, not by a count of exits (F3b): a function whose two sites share a return collides on one ordinal
    however many other exits it has."""
    import collections
    by_symbol = collections.defaultdict(set)
    name_of = {}
    for row in declaration.DECLARATION:
        by_symbol[row[3]].add(row[0])
    src = ROOT / "src" / "veracium"
    collisions, unrouted, missing = [], [], []
    for sym, ids in by_symbol.items():
        if len(ids) < 2:
            continue
        module, qual = sym.split(":")
        text = (src / module).read_text()
        names = {r["name"] for r in _scan_rows(src, module) if r["id"] in ids and r["name"]}
        assoc = _sites_per_exit(ast.parse(text), qual, names)
        assert assoc is not None, sym
        for ordinal, at in sorted(assoc.items(), key=lambda kv: (kv[0] is None, kv[0])):
            if ordinal is None:
                unrouted.append((sym, sorted(at)))
            elif len(at) > 1:
                collisions.append((sym, ordinal, sorted(at)))
        seen = set().union(*assoc.values()) if assoc else set()
        if names - seen:
            missing.append((sym, sorted(names - seen)))
    multi = sum(1 for v in by_symbol.values() if len(v) > 1)
    assert multi >= 1                                        # the figure is real (31 multi-site symbols at round 7)
    assert collisions == [], collisions                      # no exit statement carries two sites
    assert unrouted == [], unrouted                          # every fire's value reaches an exit by a followed route
    assert missing == [], missing                            # and every site of a multi-site function has an exit


def test_r6_5_ii_control_the_reviewers_fixture_collides_and_a_count_cannot_see_it():
    """The RED for the guard above, and it is the reviewer's own fixture (F3b): two sites sharing ONE return, plus
    a second return repeating just one of them. The old COUNT is satisfied — two fire-carrying exits for two sites
    — and the ASSOCIATION shows the collision. The one-return form, where the fire is an assignment feeding a
    later `return`, is attributed to that return and must NOT read as a collision."""
    collide = ast.parse("class C:\n    def f(self, x):\n        if x:\n            return A.fire(B.fire(x))\n        return A.fire(x)\n")
    assoc = _sites_per_exit(collide, "C.f", {"A", "B"})
    assert assoc == {0: {"A", "B"}, 1: {"A"}}, assoc
    assert sum(1 for v in assoc.values() if v) == 2                      # the OLD count: two exits, two sites, satisfied
    assert [o for o, at in assoc.items() if len(at) > 1] == [0]          # the association: they collide at exit 0
    split = ast.parse("class C:\n    def f(self, x):\n        if x:\n            return A.fire(x)\n        return B.fire(x)\n")
    assert _sites_per_exit(split, "C.f", {"A", "B"}) == {0: {"A"}, 1: {"B"}}
    one_return = ast.parse("class C:\n    def f(self, x):\n        if E:\n            q = A.fire(x)\n        else:\n            q = x\n        return q\n")
    assert _sites_per_exit(one_return, "C.f", {"A"}) == {0: {"A"}}       # the round-7 hot-predicate shape
    assert _sites_per_exit(collide, "C.absent", {"A"}) is None


def test_a_propagated_exception_is_never_attributed_to_a_walked_return_statement():
    """Research's mutant 1 (round 7): `try: return "A"` / `finally: boom()` reaches the return statement and exits by
    the callee's raise. The exception path must record EXIT_PROPAGATED (253) — the exception event's line is not a
    raise statement of this function — never the return's ordinal (the statement-line fallback is the RETURN path's
    witness only). Controls: a plain return (its ordinal), a raise statement (its ordinal), a propagated raise with no
    return walked (253)."""
    def boom():
        raise ValueError("callee")

    def plain(x):
        return x

    def raiser(x):
        raise KeyError(x)

    def control(x):
        y = boom()                                                 # the callee raises on a NON-exit line
        return y

    def on_the_return(x):
        return boom()                                              # the callee raises while the return statement executes

    def mutant(x):
        try:
            return "A"
        finally:
            boom()
    observer.reset_records(); observer._SYMBOLS[:] = ["t:plain", "t:raiser", "t:control", "t:on_the_return", "t:mutant"]
    observer._SYM_INDEX.clear(); observer._SYM_INDEX.update({s: i for i, s in enumerate(observer._SYMBOLS)})
    w = {i: observer._wrap_callable(fn, i) for i, fn in enumerate((plain, raiser, control, on_the_return, mutant))}
    w[0](1)
    for i in (1, 2, 3, 4):
        with pytest.raises((KeyError, ValueError)):
            w[i](1)
    recs = observer.decoded()
    assert recs[0] == ("t:plain", 0, "value")
    assert recs[1] == ("t:raiser", 0, "KeyError")
    assert recs[2] == ("t:control", observer.EXIT_PROPAGATED, "ValueError")
    # a raise DURING the return statement's own evaluation is attributed to that statement (the exception event's
    # line is the return line, which is in the exit map) — the label says it was a raise; stated, not hidden
    assert recs[3] == ("t:on_the_return", 0, "ValueError")
    assert recs[4] == ("t:mutant", observer.EXIT_PROPAGATED, "ValueError"), recs[4]      # the mutant: was (…, 0, …)
    observer.reset_records(); observer._SYMBOLS.clear(); observer._SYM_INDEX.clear()     # leave the tables as found


def test_r6_6_the_twin_transform_refuses_what_it_has_not_established_is_instrumentation_and_keeps_exits():
    """R6-6: the three round-6 cases (an unrelated `other.fire`, an unbound attribute chain, a side effect inside an
    enabled block) each REFUSE by name; an undeclared consult refuses; the recognised bypass is kept DEAD with its
    return statement in place (exit ordinals preserved) rather than deleted; the derived twin of THIS tree verifies
    clean and its manifest reports equal exit counts per function."""
    un = _load("inv7_uninstrument_r6", EVIDENCE / "inv7_uninstrument.py")
    refused = {
        "unrelated other.fire": "from .census import declare_site\nS = declare_site('x')\ndef f(other, x):\n    return other.fire(False)\n",
        "unbound attribute chain": "from .census import declare_site\nS = declare_site('x')\ndef g(a):\n    return a.b.c.fire(1)\n",
        "side effect inside an enabled block": "from . import census as _census\nfrom .census import declare_site\nS = declare_site('x')\ndef h(q):\n    if _census.enabled():\n        audit_log(q)\n        return q\n    return q\n",
        "consult on an undeclared name": "from .census import declare_site\nS = declare_site('x')\ndef k(o):\n    with o.consult():\n        return S.fire(o)\n",
        "a with mixing consult and another item": "from .census import declare_site\nS = declare_site('x')\ndef w(lock):\n    with S.consult(), lock:\n        return S.fire(None)\n",
    }
    for name, code in refused.items():
        with pytest.raises(un.Refused):
            un.uninstrument_source(code)
    # research's mutation campaign over the transform's refusals (round 7): neutering each `raise Refused` in turn found
    # three that no test drove — `global` naming a site (its `nonlocal` twin WAS driven), the consult STATEMENT on an
    # undeclared name (the `with` form was), and a bypass whose else branch does work — plus the no-argument fire.
    # Each is pinned to ITS OWN message, so another branch catching the input first would not pass for it.
    pinned = {
        "`global` names a declared site": "from .census import declare_site\nS = declare_site('x')\ndef f():\n    global S\n    return S.fire(1)\n",
        "consult\\(\\) statement on 'o', which is not this module's declared site": "from .census import declare_site\nS = declare_site('x')\ndef f(o):\n    o.consult()\n    return S.fire(1)\n",
        "else branch is not simple assignments": "from . import census as _census\nfrom .census import declare_site\nS = declare_site('x')\n"
                                                 "def h(self, q):\n    if _census.enabled():\n        with S.consult():\n            q = S.fire(q)\n    else:\n        audit(self)\n    return q\n",
        "fire\\(\\) with no decision argument": "from .census import declare_site\nS = declare_site('x')\ndef n():\n    return S.fire()\n",
    }
    for message, code in pinned.items():
        with pytest.raises(un.Refused, match=message):
            un.uninstrument_source(code)
    out, st = un.uninstrument_source("from . import census as _census\nfrom .census import declare_site\nS = declare_site('x')\n"
                                     "def p(self):\n    if _census.enabled():\n        with S.consult():\n            q = self.v()\n            return S.fire(q)\n    q = self.v()\n    return q\n")
    assert "if False:" in out and out.count("return q") == 2 and st["exits"] == {"p": 2} and st["bypasses"] == 1
    out2, st2 = un.uninstrument_source("from .census import declare_site\nS = declare_site('x')\ndef s(x):\n    S.consult()\n    if x:\n        raise S.fire(ValueError('no'))\n    return x\n")
    assert "consult" not in out2 and st2["consult_statements"] == 1 and st2["exits"] == {"s": 2}
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out_dir = pathlib.Path(d) / "src" / "veracium"
        totals = un.derive(ROOT / "src" / "veracium", out_dir)
        assert un.verify(out_dir, ROOT / "src" / "veracium") == []
        manifest = json.loads((out_dir.parent / "twin_manifest.json").read_text())
        assert manifest["totals"] == totals and totals["sites"] == len(declaration.DECLARATION)
        assert all("sha256_before" in m and "sha256_after" in m for m in manifest["modules"].values())
        changed = [m for m in manifest["modules"].values() if "exits" in m]
        assert changed and all(isinstance(m["exits"], dict) for m in changed)


def test_a_test_boundary_is_a_record_index_at_the_declared_width(tmp_path):
    """Round 7, found re-running the harness: the boundary side file was written as `len(bytes) // 2` after the
    records became three bytes, so every per-test segment was cut at 1.5x its true index — the per-test
    comparison compared misaligned windows and read a real divergence's owning test wrong. The boundary is a
    RECORD index: k records recorded, then a test starts, then its boundary is k, and the harness's owning_test
    maps record k to it and record k-1 to the test before."""
    observer.reset_records(); observer._BOUNDARIES.clear()
    observer._SYMBOLS[:] = ["m.py:f"]; observer._SYM_INDEX.clear(); observer._SYM_INDEX["m.py:f"] = 0
    observer.pytest_runtest_logstart("t.py::a", None)
    for _ in range(5):
        observer._record(0, 0, "None")
    observer.pytest_runtest_logstart("t.py::b", None)
    observer._record(0, 1, "None")
    assert observer._BOUNDARIES == [(0, "t.py::a"), (5, "t.py::b")], observer._BOUNDARIES
    assert len(observer.records()) == 6 * observer.RECORD_WIDTH
    (tmp_path / "test_boundaries.jsonl").write_text("".join(json.dumps(list(b)) + "\n" for b in observer._BOUNDARIES))
    assert harness.owning_test(tmp_path, 4) == "t.py::a" and harness.owning_test(tmp_path, 5) == "t.py::b"
    # the mutant: the old divisor puts b's boundary at 7 — past the end of a's five and one of b's records
    assert (5 * observer.RECORD_WIDTH) // 2 != 5
    observer.reset_records(); observer._BOUNDARIES.clear(); observer._SYMBOLS.clear(); observer._SYM_INDEX.clear()


def test_install_starts_from_an_empty_symbol_table_whatever_a_previous_test_left():
    """The floor lane, round 7 (found by CI after the push): a unit test left one entry in the observer's symbol
    table; under pytest-randomly it ran before the in-process arms, the first arm's install appended the declared
    symbols after it, and every record of that arm read one symbol index higher than the other two arms'. A
    symbol's index is its rank among the declared symbols — the same from a dirty table as from a clean one."""
    observer._SYMBOLS[:] = ["left.py:behind"]; observer._SYM_INDEX.clear(); observer._SYM_INDEX["left.py:behind"] = 0
    observer.install(str(EVIDENCE / "declaration.py"))
    try:
        dirty = list(observer._SYMBOLS)
    finally:
        observer.uninstall()
    observer.install(str(EVIDENCE / "declaration.py"))
    try:
        clean = list(observer._SYMBOLS)
    finally:
        observer.uninstall()
    assert dirty == clean and "left.py:behind" not in dirty and dirty[0] == sorted(dirty)[0]
    assert observer._SYMBOLS == [] and observer._SYM_INDEX == {}          # uninstall leaves the tables empty


# ---- round 7: the verdict's cases, each as its own regression ---------------------------------------------------

def test_r7_f3a_a_control_run_that_failed_fails_the_exit(tmp_path):
    """F3a: `final_status` gated each ARM's pytest exit and not the CONTROL runs, so the reviewer set the supplied
    `healthy-control` to exit 1 and still got status 0. A failed control is exactly the run whose "these tests
    agree with themselves" claim is void, and the exclusions it feeds are then derived from a broken run."""
    ids = {"a.id": "m.py:f"}; good = [(0, 0, 0)]
    ok = {"a.id": {"consulted": 1, "fired": 1, "errors": 0}}; bad = {"a.id": {"consulted": 0, "fired": 0, "errors": 2}}
    cen = [(1, "a.id", "None")]
    S = {"healthy": _fabricate(tmp_path, "healthy", good, census=cen, counters=ok, enabled=True),
         "failing": _fabricate(tmp_path, "failing", good, census=cen, counters=bad, enabled=True),
         "off": _fabricate(tmp_path, "off", good),
         "uninstrumented": _fabricate(tmp_path, "uninstrumented", good, registry_size=0)}
    arms = ["healthy", "failing", "off", "uninstrumented"]
    S["healthy-control"] = _fabricate(tmp_path, "healthy-control", good, census=cen, counters=ok, enabled=True)
    v, c = harness.compare(tmp_path, arms, S, ids, standing={})
    assert harness.final_status(v, c, S, arms) == 0 and v["gates"]["pytest_exit:healthy-control"] is True
    S["healthy-control"]["pytest_exit"] = 1                       # the reviewer's mutation
    assert harness.final_status(v, c, S, arms) == 1 and v["gates"]["pytest_exit:healthy-control"] is False
    assert {g for g in v["gates"] if g.startswith("pytest_exit:")} == {"pytest_exit:" + a for a in arms} | {"pytest_exit:healthy-control"}


def test_r7_f3c_the_serialised_verdict_carries_the_gates_both_readmes_promise(tmp_path, monkeypatch):
    """F3c: `verdict.json` was written BEFORE `final_status` added `gates`, so every shipped verdict lacked what
    the bundle README and `inv7-run/README.txt` both say it carries — a false claim in two carriers, passed by
    both seats' checks because each asserted the file's PRESENCE and DIGEST, never its keys. The order is fixed and
    `main()` now asserts the serialised object carries them; this reads the file, which is what the reviewer did."""
    import json as _json
    src = (EVIDENCE / "inv7_harness.py").read_text()
    assert src.index("status = final_status(") < src.index('(out / "verdict.json").write_text'), "gates must be computed first"
    assert 'assert set(written["verdict"].get("gates")' in src, "main() must assert the serialised verdict kept them"
    # and the property itself, on a fabricated run: whatever final_status decided is what round-trips through JSON
    ids = {"a.id": "m.py:f"}; good = [(0, 0, 0)]
    ok = {"a.id": {"consulted": 1, "fired": 1, "errors": 0}}; bad = {"a.id": {"consulted": 0, "fired": 0, "errors": 2}}
    cen = [(1, "a.id", "None")]
    S = {"healthy": _fabricate(tmp_path, "healthy", good, census=cen, counters=ok, enabled=True),
         "failing": _fabricate(tmp_path, "failing", good, census=cen, counters=bad, enabled=True),
         "off": _fabricate(tmp_path, "off", good),
         "uninstrumented": _fabricate(tmp_path, "uninstrumented", good, registry_size=0)}
    arms = ["healthy", "failing", "off", "uninstrumented"]
    v, c = harness.compare(tmp_path, arms, S, ids, standing={})
    harness.final_status(v, c, S, arms)
    round_tripped = _json.loads(_json.dumps({"verdict": v, "checks": c}))
    assert set(round_tripped["verdict"]["gates"]) == set(v["gates"]) and v["gates"], v.get("gates")


def _twin_fixture(tmp_path, body="from .census import declare_site\nS = declare_site('t')\n\ndef f(x):\n    with S.consult():\n        return S.fire(False)\n"):
    src = tmp_path / "src_tree" / "veracium"; src.mkdir(parents=True)
    # the REAL census (round 16): the twin's census is the reference census, and derive() refuses a census whose Site has
    # drifted from the reference's — a toy census with no Site at all is that, so this fixture carries the real one
    (src / "__init__.py").write_text(""); (src / "census.py").write_text((ROOT / "src" / "veracium" / "census.py").read_text())
    (src / "m.py").write_text(body)
    out = tmp_path / "twin" / "src" / "veracium"
    un = _load("inv7_uninstrument_r7", EVIDENCE / "inv7_uninstrument.py")
    un.derive(src, out)
    return un, src, out


def test_r7_f4_the_verifier_establishes_preservation(tmp_path):
    """F4: three reviewer reproductions and four more. The old verifier compared a MULTISET of (qualname, node
    kind) for a few kinds, and only when a source was passed — which the harness never did. So a flipped return
    verified clean (same kind, same qualname), a DELETED module verified clean (it iterates the copy, so a missing
    file is never visited), and the manifest it ships beside was never read. Every case is driven here, with the
    clean twin as the control that would catch an over-strict verifier."""
    import json as _json
    un, src, out = _twin_fixture(tmp_path)
    assert un.verify(out, src) == []                                             # the control: a clean twin
    only = un.verify(out)
    assert len(only) == 1 and "WITHOUT a source" in only[0]                      # F4d: the harness's old call
    flipped = tmp_path / "f"; flipped.mkdir()
    un2, src2, out2 = _twin_fixture(flipped)
    (out2 / "m.py").write_text((out2 / "m.py").read_text().replace("return False", "return True"))
    assert any("program structure differs" in p for p in un2.verify(out2, src2)), un2.verify(out2, src2)   # F4b
    deleted = tmp_path / "d"; deleted.mkdir()
    un3, src3, out3 = _twin_fixture(deleted)
    (out3 / "m.py").unlink()
    assert any("MISSING from the twin" in p for p in un3.verify(out3, src3))                                # F4c
    added = tmp_path / "a"; added.mkdir()
    un4, src4, out4 = _twin_fixture(added)
    (out4 / "extra.py").write_text("x = 1\n")
    assert any("absent from the source" in p for p in un4.verify(out4, src4))
    tampered = tmp_path / "t"; tampered.mkdir()
    un5, src5, out5 = _twin_fixture(tampered)
    man_path = out5.parent / "twin_manifest.json"; man = _json.loads(man_path.read_text())
    man["modules"]["m.py"]["sha256_after"] = "0" * 64; man_path.write_text(_json.dumps(man))
    assert any("does not match the manifest's `sha256_after`" in p for p in un5.verify(out5, src5))
    missing_man = tmp_path / "mm"; missing_man.mkdir()
    un6, src6, out6 = _twin_fixture(missing_man)
    (out6.parent / "twin_manifest.json").unlink()
    assert any("no twin manifest" in p for p in un6.verify(out6, src6))
    untransformed = tmp_path / "u"; untransformed.mkdir()
    un7, src7, out7 = _twin_fixture(untransformed)
    (out7 / "m.py").write_text((src7 / "m.py").read_text())
    assert any("survives" in p for p in un7.verify(out7, src7))


def test_r7_f4a_a_parameter_shadowing_a_site_name_keeps_its_own_call(tmp_path):
    """F4a, the shared root with F2: the transform asked "is this name declared?" by MEMBERSHIP, so a function
    PARAMETER of the same name had its ordinary method call rewritten and the twin computed something else. The
    question is a SCOPE question and goes to the same resolver the binding scan uses; an unestablished receiver is
    REFUSED by name rather than rewritten."""
    un = _load("inv7_uninstrument_r7a", EVIDENCE / "inv7_uninstrument.py")
    shadow = "from .census import declare_site\nS = declare_site('t.shadow')\n\ndef f(S):\n    S.consult()\n    return len(S)\n"
    with pytest.raises(un.Refused, match="not this module's declared site"):
        un.uninstrument_source(shadow)
    fire_shadow = "from .census import declare_site\nS = declare_site('t.shadow')\n\ndef f(S, x):\n    return S.fire(x)\n"
    with pytest.raises(un.Refused, match="not this module's declared site"):
        un.uninstrument_source(fire_shadow)
    # the control: the same shapes on the real module-level site still transform
    plain = "from .census import declare_site\nS = declare_site('t')\n\ndef f(x):\n    with S.consult():\n        return S.fire(False)\n"
    out, stats = un.uninstrument_source(plain)
    assert "consult" not in out and stats["fires"] == 1 and out.strip().endswith("return False")


def test_r8_f2_a_control_without_its_own_summary_is_refused_not_substituted(tmp_path):
    """ROUND 8, F2 — THE WHOLE MATRIX, BECAUSE THE REVIEWER NAMED ONE OF THE TWO CELLS THAT WERE WRONG.

    The control set had TWO derivations. `compare()` chose controls by DIRECTORY and substituted the main
    arm's summary for an absent one (`summaries.get(arm + "-control", summaries[arm])`); `final_status()`
    gated whichever controls it found among the SUMMARY KEYS. Deleting `summaries["healthy-control"]` while
    leaving its directory made the two disagree: the control was still compared — decoded through the WRONG
    arm's dictionaries — and its exit gate disappeared, so a control run that FAILED produced exit 0.

    That is precisely the defect round 7's F3a fix closed, restored by another route, because that fix moved
    the gate's source from `arms` to the summary keys: both are sets of what happens to be AVAILABLE, and
    neither is the set actually USED.

    All eight cells of {directory} x {summary} x {control exit} are asserted. The reviewer's cell is
    (present, absent, exit 1); the other wrong one is (present, absent, exit 0), which is wrong for a second
    reason he did not need — there the control is not merely ungated but decoded with the wrong tables."""
    import itertools
    h = _load("inv7_harness_r8f2", EVIDENCE / "inv7_harness.py")
    good = [(0, 0, 0), (1, 0, 1)]
    seen = {}
    for has_dir, has_sum, cexit in itertools.product([True, False], [True, False], [0, 1]):
        out = tmp_path / f"cell{int(has_dir)}{int(has_sum)}{cexit}"
        out.mkdir()
        S = {"healthy": _fabricate(out, "healthy", good, census=[], counters={}, enabled=True)}
        if has_dir:
            ctl = _fabricate(out, "healthy-control", good, census=[], counters={}, enabled=True)
        else:
            ctl = dict(S["healthy"])            # a control that RAN but whose directory is not here
        ctl["pytest_exit"] = cexit
        if has_sum:
            S["healthy-control"] = ctl
        verdict, checks = h.compare(out, ["healthy"], S, {}, standing={})
        status = h.final_status(verdict, checks, S, ["healthy"])
        seen[(has_dir, has_sum, cexit)] = ("healthy" in verdict["control"]["arms"], status)

    # THE TWO CELLS THAT WERE WRONG: a control directory with no summary of its own is never compared, and
    # never passes the exit — whatever its exit code was.
    for cexit in (0, 1):
        used, status = seen[(True, False, cexit)]
        assert not used, f"(dir, no summary, exit {cexit}): the control was compared with another arm's dictionaries"
        assert status == 1, f"(dir, no summary, exit {cexit}): a control we cannot decode passed the exit"

    # THE POSITIVE CONTROLS, so a harness that simply refused everything could not satisfy the assertions
    # above: a complete, passing control still passes, and a complete, FAILING one still fails.
    assert seen[(True, True, 0)] == (True, 0), "a complete, passing control no longer passes"
    assert seen[(True, True, 1)] == (True, 1), "a complete, FAILING control no longer fails the exit"
    # and a summary with no directory is not 'used', but its run still happened, so its exit still counts
    assert seen[(False, True, 0)][1] == 0 and seen[(False, True, 1)][1] == 1


def test_r8_f2_the_fix_changes_nothing_for_a_COMPLETE_capture(tmp_path):
    """THE QUESTION A REVIEWER ASKS NEXT: did tightening the control rule change what the SHIPPED transcript
    means? The pinned four-arm transcript was produced by the harness as it stood at the round-8 pin, and
    `test_the_pinned_transcript_is_this_tree_and_reads_identical_across_four_arms` binds it to `src/`, which
    round 9 does not touch. That is an argument about provenance; this is the measurement.

    The old harness is loaded FROM GIT at the round-8 pin and run beside the current one over complete
    captures — every arm present, every control present, which is what a real capture is (the round-8
    reviewer confirmed all eight summaries were in the supplied one). The verdict and the exit must agree
    exactly. If they do, the fix is confined to INCOMPLETE evidence, which is what it was said to be, and the
    shipped transcript needs no re-run.

    Skipped rather than faked where git is absent: the packaged copy has no history to load the old harness
    from, and a comparison against a rebuild-from-memory would be a claim about my own reconstruction."""
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
                      capture_output=True).returncode != 0:
        pytest.skip("no repository here: the pin's harness cannot be loaded to compare against")
    pin = _pin(TRANSCRIPT.read_text())
    old_src = subprocess.run(["git", "-C", str(ROOT), "show", f"{pin}:specs/evidence/0042/inv7_harness.py"],
                             capture_output=True, text=True)
    if old_src.returncode != 0:
        pytest.skip(f"the harness at pin {pin[:7]} is not retrievable here")
    old_path = tmp_path / "old_harness.py"
    old_path.write_text(old_src.stdout)
    old = _load("inv7_harness_at_pin", old_path)
    new = _load("inv7_harness_now", EVIDENCE / "inv7_harness.py")

    good = [(0, 0, 0), (1, 0, 1)]
    scenarios = [("both controls pass", 0, 0), ("the control FAILED", 0, 1), ("the arm itself failed", 1, 0)]
    for label, arm_exit, ctl_exit in scenarios:
        out = tmp_path / label.replace(" ", "_")
        out.mkdir()
        S = {"healthy": _fabricate(out, "healthy", good, census=[], counters={}, enabled=True)}
        S["healthy"]["pytest_exit"] = arm_exit
        S["healthy-control"] = _fabricate(out, "healthy-control", good, census=[], counters={}, enabled=True)
        S["healthy-control"]["pytest_exit"] = ctl_exit
        v_old, c_old = old.compare(out, ["healthy"], dict(S), {}, standing={})
        v_new, c_new = new.compare(out, ["healthy"], dict(S), {}, standing={})
        s_old = old.final_status(v_old, c_old, dict(S), ["healthy"])
        s_new = new.final_status(v_new, c_new, dict(S), ["healthy"])
        assert s_old == s_new, f"{label}: exit moved {s_old} -> {s_new} on a COMPLETE capture"
        assert v_old["identical"] == v_new["identical"] and v_old["per_test"] == v_new["per_test"], label
        assert v_old["control"]["arms"] == v_new["control"]["arms"], label
        assert v_old["control"]["non_reproducible"] == v_new["control"]["non_reproducible"], label
        # the gate SET may grow (round 9 adds one); no gate that existed may change its answer
        for name, value in v_old["gates"].items():
            assert v_new["gates"][name] == value, f"{label}: gate {name} moved {value} -> {v_new['gates'][name]}"


def _execute_twin_and_source(source: str, twin: str):
    """Execute BOTH modules against the same stub census and return them. The relative census import is
    stripped and the stub injected, so the two run under identical conditions and any difference is the
    transform's."""
    import types
    stub = types.SimpleNamespace(
        declare_site=lambda i: types.SimpleNamespace(fire=lambda q: q, consult=lambda: None),
        enabled=lambda: True, enable=lambda v: None)
    mods = []
    for i, text in enumerate((source, twin)):
        m = types.ModuleType(f"inv7_behaviour_{i}")
        m.__dict__["_census"] = stub
        exec(compile(text.replace("from . import census as _census\n", ""), f"<b{i}>", "exec"), m.__dict__)
        mods.append(m)
    return mods


def test_r8_f3_an_ordinary_shadowed_census_alias_keeps_its_behaviour():
    """ROUND 8, F3 — AND IT IS A BEHAVIOUR CHECK ON PURPOSE, WHICH IS THE POINT.

    Round 7's F4a made "is this name the declared SITE?" a scope question and routed it to the resolver. The
    CENSUS-ALIAS question sat four methods away still answered by spelling (`t.func.value.id in
    self.census_aliases`), and unlike the membership tests in `visit_Global`/`visit_Nonlocal` — which REFUSE,
    and so fail loudly — this one REWRITES. An ordinary function whose PARAMETER is named `_census` and which
    branches on that object's `enabled()` had its branch turned into `if False:`. Measured at the pin: the
    source returned 101 and the twin returned 1, while `verify(copy, source)` reported NO PROBLEMS.

    WHY THIS EXECUTES BOTH MODULES INSTEAD OF COMPARING TREES, in the reviewer's words: `verify()`'s structure
    check re-derives the twin with the SAME transform, so a transform defect reproduces identically and the
    comparison is clean. A cross-check built from the primary's own logic cannot catch the primary's bugs. The
    only check that can is one of a DIFFERENT KIND, so this one runs the code."""
    un = _load("inv7_uninstrument_r8f3", EVIDENCE / "inv7_uninstrument.py")
    src = ("from . import census as _census\n"
           "S = _census.declare_site('s')\n"
           "\n"
           "def hot(q):\n"
           "    if _census.enabled():\n"
           "        q = q + 1\n"
           "        return S.fire(q)\n"
           "    return q\n"
           "\n"
           "def ordinary(_census, q):\n"
           "    if _census.enabled():\n"
           "        r = q + 100\n"
           "        return r\n"
           "    return q\n")
    twin, stats = un.uninstrument_source(src, "<shadow-alias>")
    # THE POSITIVE CONTROL, FIRST: the genuine bypass must still be rewritten, or this test passes by doing
    # nothing at all — a transform that stopped transforming would satisfy the behaviour assertion trivially.
    assert stats["bypasses"] == 1 and stats["fires"] == 1 and "if False:" in twin, \
        "the genuine census bypass was not rewritten, so the shadowed-alias assertion below proves nothing"
    source_mod, twin_mod = _execute_twin_and_source(src, twin)
    flag = type("Flag", (), {"enabled": lambda self: True})()
    assert source_mod.ordinary(flag, 1) == 101, "the fixture's own control: the source returns 101"
    assert twin_mod.ordinary(flag, 1) == 101, \
        "the twin's ordinary() diverges from the source's — an ordinary shadowed `_census` was rewritten"


def test_r9_a_census_alias_whose_binding_was_replaced_is_refused_not_rewritten():
    """ROUND 9's FINDING, case (a): module SCOPE established, object IDENTITY not.

    Round 8 made the census-alias question a SCOPE question. A genuine `from . import census as _census`
    FOLLOWED BY `_census = On()` still resolves to module scope — and no longer denotes the census. The
    transform rewrote the condition anyway, so an ordinary function returned 101 in the source and 1 in the
    twin while `verify()` reported no problems.

    The static reading answers the one part of identity it can: rule A's own count, made public as
    `module_binding_count`. A name bound TWICE at module level had its import replaced, and the transform
    refuses rather than rewriting a condition whose subject it cannot establish."""
    un = _load("inv7_uninstrument_r9a", EVIDENCE / "inv7_uninstrument.py")
    src = ("from . import census as _census\n"
           "S = _census.declare_site('s')\n\n"
           "class On:\n    def enabled(self):\n        return True\n\n"
           "_census = On()\n\n"
           "def hot(q):\n    if _census.enabled():\n        q = q + 1\n        return S.fire(q)\n    return q\n")
    # the message now reports BOTH readings, so it says "time(s)"; matched on the stable clause rather
    # than the count, because a test pinning an exact refusal string is a carrier that breaks whenever
    # the message legitimately gains information — which is what happened here.
    with pytest.raises(un.Refused, match="does not establish what the"):
        un.uninstrument_source(src, "<replaced-alias>")
    # THE POSITIVE CONTROL: the same module WITHOUT the reassignment still transforms, or this test would
    # pass against a transform that refused everything.
    ok = ("from . import census as _census\n"
          "S = _census.declare_site('s')\n\n"
          "def hot(q):\n    if _census.enabled():\n        q = q + 1\n        return S.fire(q)\n    return q\n")
    twin, stats = un.uninstrument_source(ok, "<intact-alias>")
    assert stats["bypasses"] == 1 and "if False:" in twin, "the genuine bypass stopped being rewritten"


def test_r9_a_module_with_no_census_import_keeps_its_own_behaviour():
    """ROUND 9's FINDING, case (b): the GUESSED-ALIAS FALLBACK.

    `aliases or {"_census", "census"}` treated those two spellings as the census in a module that imports no
    census at all, so an ordinary object bound to `_census` had its condition rewritten. The verdict allows
    "preserve ordinary behavior OR explicitly refuse"; preserving is the half that cannot over-refuse, and
    removing the fallback preserves. Measured before removal: the real tree's twin derives byte-identically,
    because every bypass is in a module that derives its alias properly.

    This EXECUTES both modules rather than comparing trees, because `verify()` re-derives with the same
    transform and so reproduces a transform defect identically."""
    un = _load("inv7_uninstrument_r9b", EVIDENCE / "inv7_uninstrument.py")
    src = ("from veracium.census import declare_site\n"
           "S = declare_site('s')\n\n"
           "class On:\n    def enabled(self):\n        return True\n\n"
           "_census = On()\n\n"
           "def hot(q):\n    if _census.enabled():\n        q = q + 1\n        return S.fire(q)\n    return q\n\n"
           "def ordinary(q):\n    if _census.enabled():\n        return q + 100\n    return q\n")
    twin, stats = un.uninstrument_source(src, "<no-census-import>")
    assert stats["bypasses"] == 0, "a module with no census import had a condition rewritten"
    import types
    def run(text, tag):
        m = types.ModuleType(tag)
        m.__dict__["declare_site"] = lambda i: types.SimpleNamespace(fire=lambda q: q, consult=lambda: None)
        exec(compile(text.replace("from veracium.census import declare_site\n", ""), tag, "exec"), m.__dict__)
        return m
    assert run(src, "src_b").ordinary(1) == run(twin, "twin_b").ordinary(1) == 101, \
        "the twin's ordinary() diverges: an object that is not the census had its condition rewritten"


def test_every_census_decision_routes_through_one_predicate():
    """THE ROUND-11 GATE, AND IT IS THE ONLY VERSION OF THIS THAT STOPS.

    Research's stage-1 enumeration found SIX units in `inv7_uninstrument.py` deciding "is this the census?"
    on THREE different readings, kept in step by hand — and EVERY round of this arc has found two of them
    disagreeing. Round 10's verdict was two instances at once (alias RECOGNITION narrowed while import
    REMOVAL was not; rule A applied to the alias while rule C was not), and research then found a third and a
    fourth. A fifth patch would have bought one more round.

    So the rule is structural: **any unit that tests the literal `"census"` must route through one of the two
    predicates.** The predicates are the only definitions; everything else asks them. This FAILS the day a
    seventh consumer appears on a reading of its own, which is the failure mode four rounds of hand-keeping
    could not produce on demand.

    Derived from the module's AST, never from a list maintained here — the same shape as
    `test_every_refused_row_names_the_rule_that_caught_it`: derive the set, assert the declared set equals it."""
    src = (EVIDENCE / "inv7_uninstrument.py").read_text()
    tree = ast.parse(src)
    # FOUR predicates, not the two this gate was written with: it found `derive` deciding on a reading of
    # its own — which file IS the census, and which modules can be skipped unparsed — on its first run,
    # after a hand enumeration had classified that function as "mention only, decides nothing".
    # FIVE predicates. The fifth, `census_names_in_import`, was added while fixing research's stage-2
    # multi-name-import finding — and THIS GATE CAUGHT IT THE MOMENT IT EXISTED, along with `declared_names`
    # which calls it. That is the gate doing the job it was written for, one round early: a new consumer of
    # the census literal cannot appear without either becoming a predicate or routing through one.
    # ROUND 14: `is_census_module_import` is GONE — it decided whether a whole import statement could be DELETED, and
    # the twin now keeps every census import, so nothing asks it (the "never called" half of this gate said so).
    PREDICATES = {"is_census_surface_import", "census_names_in_import",
                  "is_census_module_file", "may_skip_uninstrumenting",
                  # ROUND 12 (research's R4a): every word the transform RECOGNISES instrumentation by now has one home
                  "is_instrumentation_name", "instrumentation_tokens_in",
                  "_is_fire_call", "_is_consult_call", "_is_enabled_call"}
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert PREDICATES <= defined, f"a predicate this gate names does not exist: {sorted(PREDICATES - defined)}"

    # ROUND 11 STAGE 2 asked "which units hold the CONSTANT", not "which units test it by a SHAPE" — a shape list
    # could not see round 8's own `n.id in ("_census", "census")`. That half stands.
    #
    # ROUND 12 — THE ROUND-11 VERDICT'S F2: THE GATE WAS NAMED PER DECISION AND CHECKED PER UNIT. Its rule was "a unit
    # holding the constant must BE a predicate or CALL one", so ANY unit calling a predicate was waived wholesale,
    # whatever else it decided. Measured at the pin: round 10's too-wide `endswith("census")` re-introduced inside
    # visit_Module PASSED, because visit_Module calls a predicate — and visit_Module ALREADY held a live second
    # reading, `a.name != "census"`, the partial-import strip at the heart of the same verdict's F1. The waiver is
    # DELETED: the vocabulary may appear ONLY inside the predicates.
    #
    # AND THE VOCABULARY IS DERIVED, NOT WRITTEN (research's R4a). Banning the one word "census" closed one spelling
    # of the class. Research measured three more pairs of units making one decision with other words — the
    # instrumentation tokens and the census FILE had ALREADY drifted, site-declaration recognition was identical
    # today. So the banned set is every string constant held inside a predicate: add a word to a predicate and it
    # is banned everywhere else, with no edit here. What pins that the derivation has not SHRUNK is behavioural, not
    # a floor written here: `test_r12_f2_the_gate_refuses_a_second_reading_wherever_it_stands` appends a unit
    # holding each vocabulary class and asserts it is refused.
    #
    # NAMED BOUNDARY: this file only. Round 13 dealt with the two readings OUTSIDE it that round 12 queued:
    # `inv7_harness.export_twin` now asks `is_census_module_file`; and site-declaration recognition — the transform's,
    # `scope_resolution.Resolver.site_names`, and `installed_sites.scan` — is PINNED, not unified, by
    # `test_r13_the_three_site_readers_answer_as_pinned` (they disagree on four shapes the tree does not use, each
    # loudly). Widening THIS gate to the evidence directory was measured and not done: 7 units hold the vocabulary,
    # and `"enabled"` as a report field and `"fire"` in the inventory are other concepts under the same word. A unit
    # deciding without ever writing the constant (a name built by concatenation) is out of reach of any static check.
    def string_constants(fn):
        """The string constants a unit HOLDS — its own docstring excluded, because prose ABOUT the vocabulary is not
        a decision made WITH it (the must-not-fire half of the round-12 battery)."""
        first = fn.body[0] if fn.body else None
        doc = first.value if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
            and isinstance(first.value.value, str) else None
        return {n.value for n in ast.walk(fn)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not doc}

    units = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    banned = set()
    for fn in units:
        if fn.name in PREDICATES:
            banned |= string_constants(fn)
    assert banned, "the predicates hold no string constant at all, so the derived vocabulary is EMPTY and this gate " \
                   "would pass anything — the unfailable class"

    offenders = []
    for fn in units:
        if fn.name in PREDICATES:
            continue
        held = string_constants(fn) & banned
        if held:
            offenders.append(f"{fn.name}:{fn.lineno} holds {sorted(held)}")
    assert not offenders, (
        "these units make a census or instrumentation decision with a word of the predicates' vocabulary instead of "
        f"asking the predicate that owns it — a second reading, kept in step by hand: {offenders}")

    # NEITHER PREDICATE MAY BE DEAD: a definition nothing calls cannot keep anything in step, and a gate
    # that passes because both are unused would be the unfailable class.
    for pred in sorted(PREDICATES):
        callers = [fn.name for fn in ast.walk(tree)
                   if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == pred
                           for n in ast.walk(fn))]
        assert callers, f"{pred} is defined and never called: it keeps nothing in step"


def test_r11_the_four_census_identity_findings(tmp_path):
    """ROUND 10'S TWO VERDICT FINDINGS AND THE TWO RESEARCH FOUND, one test because they are one defect:
    a decision about the census answered at one of its sites.

    1. NESTED CODE REPLACES THE ALIAS (verdict). `module_binding_count` is RULE A — the module's own code
       object. A nested `global _census; _census = On()`, a nested import, and a generator-expression walrus
       all replace the binding without moving that count. The SITE question has always asked BOTH readings;
       the alias was given one. Measured at the pin: ordinary() 101 in the source, 1 in the twin, verify clean.
    2. UNRELATED `census` IMPORTS DELETED (verdict). Recognition was narrowed to `from . import census`;
       removal still stripped any name spelled `census` from any import, so an ordinary module lost its import
       and the twin raised NameError.
    3. `from .. import census` — UNRECOGNISED AND REMOVED ANYWAY (research). The removal branch checked
       `module` and never `level`. The two halves of one decision gave opposite answers about one statement.
    4. AN ESTABLISHED ALIAS IN AN UNRECOGNISED STATEMENT SHAPE (research). Recogniser and detector both
       required `ast.If`, so `on = _census.enabled()`, `while ...` and a ternary were invisible to both."""
    un = _load("inv7_uninstrument_r11", EVIDENCE / "inv7_uninstrument.py")
    HEAD = ("from . import census as _census\nS = _census.declare_site('s')\n\n"
            "class On:\n    def enabled(self):\n        return True\n\n")
    TAIL = ("\ndef ordinary(q):\n    if _census.enabled():\n        return q + 100\n    return q\n")

    # (1) all three nested shapes must now be REFUSED, not silently rewritten
    for label, mid in [("global assignment", "def swap():\n    global _census\n    _census = On()\n"),
                       ("nested import",     "def swap():\n    global _census\n    import os as _census\n"),
                       ("genexp walrus",     "xs = list((_census := On()) for _ in (1,))\n")]:
        with pytest.raises(un.Refused, match="does not establish what the"):
            un.uninstrument_source(HEAD + mid + TAIL, f"<{label}>")

    # (2) and (3): an import that is NOT this project's census survives untouched
    for label, spell, use in [("unrelated module", "from totally_unrelated import census", "census.value()"),
                              ("test fixture",     "from conftest import census as c",     "c.value()"),
                              ("wrong level",      "from .. import census as up",          "up.value()")]:
        src = ("from . import census as _census\n" + spell + "\nS = _census.declare_site('s')\n\n"
               f"def ordinary():\n    return {use}\n")
        twin, _ = un.uninstrument_source(src, f"<{label}>")
        assert spell in twin, f"{label}: an import that is not the census module was deleted"

    # (4) an ESTABLISHED alias in a shape the transform does not rewrite is REPORTED, not silent
    est = "from . import census as _census\nS = _census.declare_site('s')\n\n"
    for label, body in [("assignment", "def f(q):\n    on = _census.enabled()\n    return S.fire(q)\n"),
                        ("while",      "def f(q):\n    while _census.enabled():\n        return S.fire(q)\n    return q\n"),
                        ("ternary",    "def f(q):\n    return S.fire(q) if _census.enabled() else q\n")]:
        twin, stats = un.uninstrument_source(est + body, f"<{label}>")
        assert stats["bypasses"] == 0 and stats["unresolved_bypass_candidates"] == 1, \
            f"{label}: a live census consult the transform did not rewrite is reported as clean"
        assert "statement shape" in stats["unresolved_bypass_detail"][0], \
            f"{label}: the report does not say WHY it went unrewritten"

    # THE POSITIVE CONTROLS, so none of the above can pass by the transform doing nothing:
    ok = est + "def f(q):\n    if _census.enabled():\n        q = q + 1\n        return S.fire(q)\n    return q\n"
    twin, stats = un.uninstrument_source(ok, "<control>")
    assert stats["bypasses"] == 1 and stats["unresolved_bypass_candidates"] == 0 and "if False:" in twin, \
        "the genuine bypass stopped being rewritten"
    plain = est + "def f(q):\n    return S.fire(q)\n"
    _, stats = un.uninstrument_source(plain, "<no-bypass>")
    assert stats["bypasses"] == 0 and stats["unresolved_bypass_candidates"] == 0, \
        "a module with no census consult at all is no longer distinguishable from one that has an unread it"


def test_r10_bypasses_zero_distinguishes_none_present_from_not_recognisable():
    """RESEARCH'S STAGE-2 FINDING: `bypasses: 0` MEANT TWO THINGS AND THEY PRINTED IDENTICALLY.

    A module with genuinely no census bypass and a module WITH one whose alias could not be established both
    reported `bypasses: 0`. In the second the twin RETAINS a live `<name>.enabled()` call — in that region it
    is not an uninstrumented reference at all — and its own manifest called it clean. "None present" and
    "present but not recognisable" are different facts and only the first is a result; this is the
    zero-versus-N/A shape this project has paid for before.

    The module is NOT refused. Preserving ordinary behaviour cannot over-refuse, and refusing would reject an
    idiom no module in the tree uses. What changed is that the manifest stops reporting it clean.

    All four shapes that reach it are exercised, because the gap sits BEFORE both mechanisms: `declared_names`
    reads `tree.body`, so a block-level import establishes no alias, and the bound-exactly-once refusal only
    fires on an ESTABLISHED alias — so neither fires and the transform proceeds."""
    un = _load("inv7_uninstrument_r10", EVIDENCE / "inv7_uninstrument.py")
    body = ("S = declare_site('s')\n\ndef hot(q):\n    if _census.enabled():\n        q = q + 1\n"
            "        return S.fire(q)\n    return q\n")
    head = "from veracium.census import declare_site\n"
    unestablished = {
        "conditional import": head + "try:\n    from . import census as _census\nexcept ImportError:\n    _census = None\n" + body,
        "if TYPE_CHECKING":   head + "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from . import census as _census\n" + body,
        "runtime block":      head + "import sys\nif sys.version_info >= (3, 9):\n    from . import census as _census\n" + body,
        "no census import":   head + body,
    }
    for label, src in unestablished.items():
        twin, stats = un.uninstrument_source(src, f"<{label}>")
        assert stats["bypasses"] == 0, label
        assert stats["unresolved_bypass_candidates"] == 1, (
            f"{label}: the twin keeps a live census call and the manifest still reports it clean")
        assert stats["unresolved_bypass_detail"], f"{label}: the count is reported without naming the call"
        assert "_census.enabled()" in twin, f"{label}: fixture no longer reproduces the condition it tests"

    # THE OTHER MEANING OF ZERO, which must stay distinguishable: a module with genuinely no bypass.
    none_present = head + "S = declare_site('s')\n\ndef hot(q):\n    return S.fire(q)\n"
    twin, stats = un.uninstrument_source(none_present, "<none-present>")
    assert stats["bypasses"] == 0 and stats["unresolved_bypass_candidates"] == 0, \
        "a module with no bypass at all is no longer distinguishable from one the transform could not read"
    # AND THE POSITIVE CONTROL: an establishable alias is still rewritten and reported as a bypass.
    ok = ("from . import census as _census\nS = _census.declare_site('s')\n\ndef hot(q):\n"
          "    if _census.enabled():\n        q = q + 1\n        return S.fire(q)\n    return q\n")
    twin, stats = un.uninstrument_source(ok, "<establishable>")
    assert stats["bypasses"] == 1 and stats["unresolved_bypass_candidates"] == 0 and "if False:" in twin, \
        "the genuine bypass stopped being rewritten, so the assertions above prove nothing"


def test_r9_the_alias_identity_is_established_at_runtime_because_it_cannot_be_established_statically():
    """THE FOURTH RUNG, CLOSED WHERE IT IS CLOSEABLE.

    Three rounds climbed membership -> spelling -> scope, one rung per round. The fourth — does the alias
    DENOTE this project's census module? — is not statically reachable, and research demonstrated it
    executably: two BYTE-IDENTICAL files under different packages bind different objects and return True
    and False. A static reading cannot separate them because they ARE the same file.

    So the claim is not made statically. It is made here, at runtime, where `sys.modules` exists and
    identity is an `is` comparison — and the behaviour regressions already pay for the execution. This test
    asserts the instrumented tree's own alias resolves to the census module the instrumentation uses, which
    is the assertion the AST cannot make."""
    import veracium, veracium.census, veracium.schema
    assert veracium.schema._census is veracium.census, \
        "schema.py's `_census` is not the census module the instrumentation uses — the alias the transform " \
        "rewrites conditions on does not denote what the static check assumes"
    # and the NEGATIVE control: identity is a real discriminator here, not a tautology
    assert veracium.schema._census is not veracium, "the identity assertion would pass against any module"


def test_r8_f3_the_census_import_is_restored_for_a_derived_alias():
    """The SECOND member of F3's class, found by sweeping the module's other spelling-based tests rather than
    by the reviewer. `still_used` read a hand-written `("_census", "census")` sitting two lines below the
    DERIVED `census_aliases`, so a module importing the census under any other name kept its surface use,
    lost its import, and produced a twin that died at import with `NameError`. Latent rather than live: the
    tree's only alias today is `_census`, which is why nothing caught it.

    A KNOWN AND BENIGN IMPRECISION, STATED SO IT IS NOT MISTAKEN FOR AN OVERSIGHT: `still_used` walks the
    TRANSFORMED tree, whose nodes the resolver cannot answer about, so it remains a spelling test. A parameter
    named like the alias therefore makes it restore an import the module does not need. That direction is
    safe — the twin's census is the stub, which answers the surface — whereas the direction fixed here,
    failing to restore a NEEDED import, breaks the twin outright."""
    un = _load("inv7_uninstrument_r8f3b", EVIDENCE / "inv7_uninstrument.py")
    src = ("from . import census as c\n"
           "S = c.declare_site('s')\n"
           "\n"
           "def on():\n"
           "    c.enable(True)\n"
           "\n"
           "def hot(q):\n"
           "    if c.enabled():\n"
           "        q = q + 1\n"
           "        return S.fire(q)\n"
           "    return q\n")
    twin, stats = un.uninstrument_source(src, "<third-alias>")
    assert stats["bypasses"] == 1, "the bypass was not rewritten, so this fixture is not exercising the transform"
    assert "import census as c" in twin, \
        "the census import was not restored for a module whose alias is neither `_census` nor `census`"


# ------------------------------------------------------------------------------------------------------------------
# ROUND 12 — the round-11 verdict's two findings, and research's stage-1 read of the fix (R1-R4 blocking; R4a and
# R7 pulled into this batch on the owner's word). Every cell below was written BEFORE the fix and run against the
# pin: each defect cell FAILED there and each control PASSED, which is what makes the controls controls.
# ------------------------------------------------------------------------------------------------------------------

_R12_CENSUS_SRC = ROOT / "src" / "veracium" / "census.py"

# (cell, module text, expected). expected is ("works", the value f() returns in the SOURCE) or ("refuses", a
# substring of the refusal). THREE AXES, not one cell (research's R7): the import's SHAPE, whether the census is
# still LIVE after the instrumentation is gone, and the MODULE CONTEXT a restored import has to be placed into.
_R12_CELLS = [
    ("control-module-full-census-used-after",
     "from . import census\nS = census.declare_site('s')\n\ndef f():\n    census.enable(True)\n    return census.enabled()\n",
     ("works", True)),
    ("F1-module-mixed-census-used-after",
     "from . import census, other\nS = census.declare_site('s')\n\ndef f():\n    census.enable(True)\n    return other.X\n",
     ("works", 7)),
    ("control-module-mixed-census-not-used-after",
     "from . import census, other\nS = census.declare_site('s')\n\ndef f():\n    return other.X\n",
     ("works", 7)),
    ("control-surface-pure-declare-site-the-real-tree-shape",
     "from .census import declare_site\nS = declare_site('s')\n\ndef f():\n    return 1\n",
     ("works", 1)),
    ("F1-surface-mixed-extra-name-live",
     "from .census import declare_site, enabled\nS = declare_site('s')\n\ndef f():\n    return enabled()\n",
     ("works", False)),
    ("F1-surface-no-declare-site-name-live",
     "from .census import enabled\n\ndef f():\n    return enabled()\n",
     ("works", False)),
    # the census's Site class, imported by name: works (round 14 through a stand-in named Site; round 15, the real one)
    ("surface-name-site",
     "from .census import declare_site, Site\nS = declare_site('s')\n\ndef f():\n    return isinstance(S, Site)\n",
     ("works", True)),
    # round 15: the twin's census IS the source's, so a real-census name the stand-in never answered now WORKS — the
    # refusal of a name "the STUB does not define" had nothing left to refuse and is gone
    ("surface-name-a-real-census-name",
     "from .census import declare_site, CensusError\nS = declare_site('s')\n\ndef f():\n    return issubclass(CensusError, Exception)\n",
     ("works", True)),
    ("boundary-declare-site-imported-under-another-name",
     "from .census import declare_site as ds\nS = ds('s')\n\ndef f():\n    return 1\n",
     ("refuses", "under another name")),
    ("R2-site-passed-as-a-value",
     "from . import census as _census\nS = _census.declare_site('s')\n\ndef f():\n    return register(S) is S\n\n"
     "def register(s):\n    return s\n",
     ("works", True)),                    # round 14: the name stays bound — R2's refusal is gone
    ("R2-site-in-a-module-level-registry",
     "from . import census as _census\nS = _census.declare_site('s')\nREGISTRY = [S]\n\ndef f():\n    return 1\n",
     ("works", 1)),
    ("R3-restored-import-with-a-docstring",
     '"""Doc."""\nfrom . import census\nS = census.declare_site(\'s\')\n\ndef f():\n    census.enable(True)\n'
     '    return census.enabled()\n',
     ("works", True)),
    ("R3-restored-import-with-a-docstring-and-future",
     '"""Doc."""\nfrom __future__ import annotations\nfrom . import census\nS = census.declare_site(\'s\')\n\n'
     'def f():\n    census.enable(True)\n    return census.enabled()\n',
     ("works", True)),
    # ROUND 12 STAGE 2, research's S2-4 — survivors of their mutant campaign, each a real behaviour NO test pinned:
    # M4b matched receivers by NAME rather than identity and survived, because both R2 cells above load the site
    # ONLY as a value. A site that is fired AND loaded as a value is the row that tells identity from name.
    ("S2-4-site-fired-AND-loaded-as-a-value",
     "from . import census as _census\nS = _census.declare_site('s')\n\ndef f(q=None):\n    return S.fire(len([S]))\n",
     ("works", 1)),
    # M10 dropped `.consult()` from the instrumentation tokens and survived: that token is the ONLY guard against a
    # consult in EXPRESSION position, which the transform does not rewrite, and no test contained one.
    ("S2-4-consult-in-expression-position",
     "from . import census as _census\nS = _census.declare_site('s')\n\ndef f():\n    x = S.consult()\n    return x\n",
     ("refuses", ".consult()")),
]


@pytest.mark.parametrize("cell,text,expected", _R12_CELLS, ids=[c[0] for c in _R12_CELLS])
def test_r12_f1_every_census_import_shape_keeps_its_bindings_or_refuses(cell, text, expected, tmp_path, monkeypatch):
    """ROUND 11'S F1 — "Mixed and surface imports can lose live bindings, causing NameError while verify() reports
    clean" — AS A MATRIX, because round 11 fixed the ONE cell the previous verdict named (the partial module
    import) and never enumerated the rest. Reproduced at the pin: THREE broken cells where the finding names two
    (the third is a surface import with no `declare_site` at all), each NameError with verify() CLEAN.

    Research's stage-1 read added the other axes, each measured before it was written down: a declared site LOADED
    as a value (R2 — the name is assignment-bound, not import-bound, so an import-scoped check misses it), and a
    restored import placed ahead of the docstring and `from __future__` (R3 — __doc__ silently lost, or a
    SyntaxError that `ast.parse` accepts and `compile()` refuses; ONE appended line from live on schema.py).

    A `works` cell must derive, verify CLEAN, import, compute what the source computes, and keep its docstring.
    A `refuses` cell must be refused with the boundary named — never a twin that dies at import."""
    un = _load("inv7_uninstrument_r12_matrix", EVIDENCE / "inv7_uninstrument.py")
    kind, want = expected
    if kind == "refuses":
        with pytest.raises(un.Refused, match=re.escape(want)):
            un.uninstrument_source(text, f"<{cell}>")
        return
    slug = re.sub(r"\W", "_", cell)
    src = tmp_path / f"r12src_{slug}"; src.mkdir()
    (src / "__init__.py").write_text(""); (src / "other.py").write_text("X = 7\n")
    (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "mod.py").write_text(text)
    twin = f"r12twin_{slug}"; out = tmp_path / twin
    un.derive(src, out)
    problems = un.verify(out, src)
    assert problems == [], f"{cell}: verify() is not clean on this derivation: {problems}"
    monkeypatch.syspath_prepend(str(tmp_path))
    try:
        mod = importlib.import_module(f"{twin}.mod")
        got, doc = mod.f(), mod.__doc__
    finally:
        for k in [k for k in sys.modules if k == twin or k.startswith(twin + ".")]:
            del sys.modules[k]
    assert got == want, f"{cell}: the twin computes {got!r} where the source computes {want!r}"
    assert doc == ast.get_docstring(ast.parse(text)), f"{cell}: the twin's docstring is {doc!r}"


def test_r12_r4_one_reading_of_which_file_is_the_census(tmp_path):
    """RESEARCH'S STAGE-1 R4: "is this file the census module?" was decided THREE ways — `is_census_module_file`
    (top level only), verify() (`rel.name`, ANY depth) and the harness (legacy branch, outside the gate's file). So
    a subpackage `census.py` was uninstrumented normally by derive() and then flagged by verify() as "not the twin
    STUB": loud, latent, and two readings of one question. verify() now asks the predicate."""
    un = _load("inv7_uninstrument_r12_r4", EVIDENCE / "inv7_uninstrument.py")
    src = tmp_path / "r12src_subcensus"; (src / "sub").mkdir(parents=True)
    (src / "__init__.py").write_text(""); (src / "sub" / "__init__.py").write_text("")
    (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "sub" / "census.py").write_text("X = 1\n")          # an ordinary module that is merely NAMED census.py
    (src / "mod.py").write_text("from .census import declare_site\nS = declare_site('s')\n\ndef f():\n    return 1\n")
    out = tmp_path / "r12twin_subcensus"; un.derive(src, out)
    assert (out / "sub" / "census.py").read_text() == "X = 1\n", "derive() treated the subpackage file as the census"
    assert un.verify(out, src) == [], "verify() and derive() still disagree about which file is the census"


def _r14_deleting_visit_module(is_declaration):
    """THE MUTANT: round 13's transform — the declaration REMOVED. Round 14 keeps every name bound, which is exactly
    what makes the checks below unable to fire on the real transform; this puts back the behaviour they exist for."""
    def visit_Module(self, node):
        node.body = [st for st in node.body
                     if not (isinstance(st, ast.Assign) and isinstance(st.value, ast.Call) and is_declaration(st.value))]
        self.generic_visit(node)
        return node
    return visit_Module


def _r14_future_breaking_visit_module(is_declaration):
    """THE MUTANT: a transform that emits a statement ahead of `from __future__` — `ast.parse` accepts it, `compile()`
    does not (round 12's R3 shape)."""
    def visit_Module(self, node):
        node.body.insert(0, ast.Expr(ast.Constant(0)))
        self.generic_visit(node)
        return node
    return visit_Module


@pytest.mark.parametrize("mutant,cell,sibling,reported", [
    (_r14_deleting_visit_module, "from . import census\nS = census.declare_site('s')\nREG = [S]\n\n"
     "def f():\n    return REG[0] is S\n", None, "LOST BINDING"),
    (_r14_deleting_visit_module, "from . import census\nS = census.declare_site('s')\n\ndef f():\n    return 1\n",
     "from .mod import S\n\ndef g():\n    return S is not None\n", "bound there in the source and not in the twin"),
    (_r14_future_breaking_visit_module, '"""Doc."""\nfrom __future__ import annotations\nfrom . import census\n'
     "S = census.declare_site('s')\n\ndef f():\n    return census.enabled()\n", None, "does not COMPILE"),
], ids=["lost-binding", "lost-cross-module-reference", "does-not-compile"])
def test_r12_verify_catches_a_transform_defect_it_did_not_write(mutant, cell, sibling, reported, tmp_path, monkeypatch):
    """THE E HALF OF round 11's F1: verify() re-derives the twin with the SAME transform and compares, so a transform
    defect reproduces identically and reads clean. Its checks of a DIFFERENT KIND — every emitted module COMPILES
    (round 12), no module-level name the source binds is read by the twin and bound nowhere (`lost_bindings`, round
    12), no cross-module reference the twin makes fails to resolve (`lost_cross_module_references`, round 13) — must
    catch the transform's OWN defects.

    ROUND 14 (research's stage-1 B3): the real transform now REMOVES NOTHING, so on it the lost-binding and
    cross-module checks cannot fire at all — a check that cannot fail is kept only if it is SHOWN to fail on the
    defect it exists for. Each cell patches the transform with a mutant — round 13's own declaration removal, or a
    statement emitted ahead of `from __future__` — so the transform AND verify()'s re-derivation both run it, which
    is exactly the situation the structure comparison cannot see; the named check must report it."""
    un = _load("inv7_uninstrument_r14_verify", EVIDENCE / "inv7_uninstrument.py")
    monkeypatch.setattr(un.Uninstrument, "visit_Module", mutant(un.is_site_declaration))
    src = tmp_path / "r14src_mut"; src.mkdir()
    (src / "__init__.py").write_text(""); (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "mod.py").write_text(cell)
    if sibling:
        (src / "sib.py").write_text(sibling)
    out = tmp_path / "r14twin_mut"
    un.derive(src, out)
    problems = un.verify(out, src)
    assert any(reported in p for p in problems), f"the twin is broken and verify() does not report {reported!r}: {problems}"


def test_r12_f2_the_gate_refuses_a_second_reading_wherever_it_stands(tmp_path, monkeypatch):
    """ROUND 11'S F2 — "The enumeration gate permits independent decisions inside functions that call a predicate."
    The gate is NAMED per decision and CHECKED per unit: any unit calling a predicate was waived wholesale. Measured
    at the pin: a mutant re-introducing round 10's too-wide `endswith("census")` inside visit_Module PASSED, because
    visit_Module calls a predicate; the same decision in a unit that calls none was caught.

    AND RESEARCH'S R4a: banning the one literal "census" closes one spelling of the class, not the class. Their
    measurement found the same decision made twice with OTHER vocabulary — the instrumentation tokens (R1, already
    drifted), the census file (R4, already drifted), site-declaration recognition (identical today). So the banned
    set is DERIVED from the constants inside the predicates, and every mutant below uses a different word of it.

    Runs the REAL gate, against mutated copies of the evidence directory. Both halves are asserted: the mutants
    must be refused, AND a docstring that merely MENTIONS the vocabulary must not be — a gate that refuses prose
    would be the narrow-gate defect in the other direction."""
    real = (EVIDENCE / "inv7_uninstrument.py").read_text()
    anchor = "            if is_census_surface_import(stmt):\n"
    assert real.count(anchor) == 1, "the visit_Module anchor this mutant rewrites has moved"
    CASES = [
        ("unmutated", real, True),
        ("F2: round 10's endswith() re-introduced INSIDE visit_Module, which calls predicates",
         real.replace(anchor, "            if is_census_surface_import(stmt) or (isinstance(stmt, ast.ImportFrom) "
                              "and (stmt.module or '').endswith(\"census\")):\n"), False),
        ("R4a: a census-FILE reading of its own", real + "\n\ndef _m_file(rel):\n    return rel.name == \"census.py\"\n", False),
        ("R4a: a site-DECLARATION reading of its own",
         real + "\n\ndef _m_decl(call):\n    return getattr(call.func, \"id\", \"\") == \"declare_site\"\n", False),
        ("R4a: an instrumentation-TOKEN reading of its own (R1's class)",
         real + "\n\ndef _m_tokens(text):\n    return \".fire(\" in text\n", False),
        ("control: the literal in a unit that calls no predicate",
         real + "\n\ndef _m_plain(stmt):\n    return stmt.module == \"census\"\n", False),
        ("must NOT fire: a docstring that only MENTIONS the vocabulary",
         real + "\n\ndef _m_prose(x):\n    \"\"\"census, census.py, declare_site and .fire( are named here in prose.\"\"\"\n"
                "    return x\n", True),
    ]
    gate = globals()["test_every_census_decision_routes_through_one_predicate"]
    wrong = []
    for label, text, should_pass in CASES:
        d = tmp_path / re.sub(r"\W", "_", label)[:60]; d.mkdir()
        for q in EVIDENCE.glob("*.py"):
            (d / q.name).write_text(q.read_text())
        (d / "inv7_uninstrument.py").write_text(text)
        monkeypatch.setitem(globals(), "EVIDENCE", d)
        try:
            gate(); passed = True
        except AssertionError:
            passed = False
        if passed != should_pass:
            wrong.append(f"{label}: gate {'PASSED' if passed else 'REFUSED'}, should have "
                         f"{'passed' if should_pass else 'refused'}")
    assert not wrong, "the enumeration gate misjudged:\n  " + "\n  ".join(wrong)



# ------------------------------------------------------------------------------------------------------------------
# ROUND 12 STAGE 2 — research's S2-1 (the resolver misplaced every definition-time position), S2-2 (lost_bindings'
# builtin subtraction hid the one silent case) and S2-4 (survivors). The positions are LOADED from the scope file.
# ------------------------------------------------------------------------------------------------------------------

_SCOPE_TESTS = _load("t0042_scope_positions", ROOT / "tests" / "test_0042_scope_resolution.py")




@pytest.mark.parametrize("pos,body", _SCOPE_TESTS.DEFINITION_TIME_POSITIONS,
                         ids=[p for p, _ in _SCOPE_TESTS.DEFINITION_TIME_POSITIONS])
def test_r14_a_site_loaded_at_a_definition_time_position_keeps_its_declaration(pos, body):
    """Round 12's S2-1 made R2 refuse a declared site LOADED at every definition-time position, because the twin
    removed the declaration and kept the load. ROUND 14 removes nothing: the load is correct code, the declaration is
    PRESERVED, and the transform derives it (R2 is gone — research's stage-1 read)."""
    un = _load("inv7_uninstrument_r14_s21", EVIDENCE / "inv7_uninstrument.py")
    out, stats = un.uninstrument_source(_SCOPE_TESTS._S21_HEAD + body.replace("__X__", "S"), f"<{pos}>")
    assert "S = _census.declare_site('s')" in out and stats["sites"] == 1, out


@pytest.mark.parametrize("pos,body", _SCOPE_TESTS.DEFINITION_TIME_POSITIONS,
                         ids=[p for p, _ in _SCOPE_TESTS.DEFINITION_TIME_POSITIONS])
def test_r12_s2_1_a_census_consult_at_a_definition_time_position_is_reported_not_silent(pos, body):
    """THE SILENT ONE. Round 11 made the unresolved-bypass detector shape-agnostic: every `<alias>.enabled()` the
    transform does not rewrite is REPORTED, so a twin carrying a live census call cannot call itself clean. It asks
    the resolver whether the name is the module's alias — and at a definition-time position the resolver said no, so
    the detector filed it as "a local of the same name: not ours". Measured: `def f(q, on=_census.enabled())` left
    the live call in the twin with unresolved=0 and verify() CLEAN, while the same read in a function BODY was
    reported. Round 11's own claim — "walks every call wherever it stands" — was false for header positions."""
    un = _load("inv7_uninstrument_r12_s21b", EVIDENCE / "inv7_uninstrument.py")
    out, stats = un.uninstrument_source(_SCOPE_TESTS._S21_HEAD + body.replace("__X__", "_census.enabled()"), f"<{pos}>")
    assert "_census.enabled()" in out, f"{pos}: the fixture no longer leaves a live consult, so it tests nothing"
    assert stats["unresolved_bypass_candidates"] >= 1, (
        f"{pos}: the twin keeps a live `_census.enabled()` and the manifest reports it CLEAN (unresolved=0)")


@pytest.mark.parametrize("pos,body", _SCOPE_TESTS.LAZY_POSITIONS, ids=[p for p, _ in _SCOPE_TESTS.LAZY_POSITIONS])
def test_py314_a_census_consult_in_a_lazy_position_is_refused_not_transformed(pos, body):
    """The 3.14 floor (the second seat's B3, item 4): `_census.enabled()` in an annotation, a type alias, a type
    variable's bound or a generic class's base runs apart from the decision beside it — the transform refuses the
    module by name rather than rewriting it or reporting it clean."""
    un = _load("inv7_uninstrument_py314_lazy", EVIDENCE / "inv7_uninstrument.py")
    with pytest.raises(Exception, match="runs apart from the decision beside it"):
        un.uninstrument_source(_SCOPE_TESTS._S21_HEAD + body.replace("__X__", "_census.enabled()"), f"<{pos}>")


def test_r12_s2_2_lost_bindings_does_not_hide_a_lost_builtin_shadow():
    """RESEARCH'S S2-2. `lost_bindings` subtracted `dir(builtins)`, reasoning that a builtin name cannot be a lost
    binding. It is the ONE case that can be SILENT: a lost binding can only be a builtin's name if the source SHADOWED
    that builtin, and losing the shadow raises no NameError — the name resolves to the builtin instead. Measured end
    to end: a site named `id`, read in a default, gave a twin passing the builtin `id` function where the source
    passed the site, with verify() CLEAN (the same site named `S` was reported).

    BOTH HALVES: the shadow must be reported, AND an ordinary builtin read the source never bound must not be — the
    subtraction was never what kept `len` out, the differential is (it only reports names the SOURCE bound)."""
    un = _load("inv7_uninstrument_r12_s22", EVIDENCE / "inv7_uninstrument.py")
    src = "from . import census as _census\nid = _census.declare_site('s')\n\ndef f(x=id):\n    return len([x])\n"
    twin = "\ndef f(x=id):\n    return len([x])\n"
    lost = un.lost_bindings(src, twin)
    assert "id" in lost, f"the source's `id` is gone from the twin and still read there, and it was not reported: {lost}"
    assert "len" not in lost, "an ordinary builtin read the source never bound was reported as lost"


def test_r12_s2_4_a_module_carrying_only_a_consult_is_parsed_not_skipped():
    """RESEARCH'S S2-4, survivor M9: `may_skip_uninstrumenting` spelled out its own tokens, and a mutant restoring
    that SURVIVED because no test held a module whose only route into the census is `.consult()`. Such a module was
    skipped unparsed before round 12 and must be parsed now: the skip heuristic asks the owner of the token list."""
    un = _load("inv7_uninstrument_r12_s24", EVIDENCE / "inv7_uninstrument.py")
    assert un.may_skip_uninstrumenting("x = 1\n"), "control: a module with no route into the census may be skipped"
    assert not un.may_skip_uninstrumenting("def f(site):\n    with site.consult():\n        return 1\n"), \
        "a module whose only census token is `.consult()` was skipped unparsed"



# ------------------------------------------------------------------------------------------------------------------
# ROUND 12 STAGE 2b — the SILENT end of research's S2b-1, and S2b-2.
# ------------------------------------------------------------------------------------------------------------------

_S2B1_REFUSED = [   # two or more HEADER roles on one key — the order is subtle, so refused (remedy (b))
    ("positional-default-reads-kw-only-binds", "def f(q, a=lambda: _census.enabled(), *, k=lambda _census: _census):\n    return q\n"),
    ("annotation-binds-default-reads",         "def f(q: (lambda _census: _census) = lambda: _census.enabled()):\n    return q\n"),
]
_S2B1_ORDERED = [   # a header part against the statement's own block or body — the order is defined, so fixed
    ("return-annotation-binds-body-reads",     "def f() -> (lambda _census: _census): return (lambda: _census.enabled())()\n"),
    ("lambda-default-binds-outer-reads",       "g = lambda a=(lambda _census: _census): _census.enabled()\n"),
    ("genexp-target-binds-first-iterable-reads",
     "def f(r):\n    return list(_census for _census in (_census.enabled() for q in r))\n"),
]
_S2B1_HEAD = "from . import census as _census\nS = _census.declare_site('s')\n\n"


@pytest.mark.parametrize("cell,body", _S2B1_REFUSED, ids=[c for c, _ in _S2B1_REFUSED])
def test_r12_s2b_1_a_swapped_table_is_refused_not_silently_derived(cell, body):
    """THE PROPERTY THE FINDING IS ABOUT, for the collisions refused. Each fixture puts a census read and a scope
    binding `_census` as its own parameter in two different HEADER roles on one line. At 40f5839 the read resolved to
    the parameter and the twin kept a live `_census.enabled()` with unresolved=0 and verify() clean. Now the resolver
    refuses to guess which table is which, and the refusal reaches the caller instead of a clean-looking twin."""
    un = _load("inv7_uninstrument_r12_s2b1", EVIDENCE / "inv7_uninstrument.py")
    with pytest.raises(un._scope.UnresolvableScope, match="different roles"):
        un.uninstrument_source(_S2B1_HEAD + body, f"<{cell}>")


@pytest.mark.parametrize("cell,body", _S2B1_ORDERED, ids=[c for c, _ in _S2B1_ORDERED])
def test_r12_s2b_1_a_swapped_table_is_now_resolved_and_reported(cell, body):
    """THE SAME PROPERTY, for the collisions fixed by ORDER. At 40f5839 the census read resolved to the other scope's
    parameter and went unreported. Now each scope gets its own table, the read is the module's alias, and the live
    call the twin keeps is REPORTED — the detector's whole job, which round 11 made shape-agnostic."""
    un = _load("inv7_uninstrument_r12_s2b1o", EVIDENCE / "inv7_uninstrument.py")
    out, stats = un.uninstrument_source(_S2B1_HEAD + body, f"<{cell}>")
    assert "_census.enabled()" in out, f"{cell}: the fixture no longer leaves a live consult, so it tests nothing"
    assert stats["unresolved_bypass_candidates"] >= 1, f"{cell}: a live census call in the twin, reported CLEAN"


def test_r12_s2b_2_a_default_naming_a_comprehension_target_is_not_the_site():
    """RESEARCH'S S2b-2 (mutant DM8): a definition-time part inside an INLINED comprehension must keep the
    comprehension's shadowing. `[(lambda y=S: y) for S in range(3)]` reads the comprehension's TARGET, not the declared
    site, so it must not be refused as a site loaded outside fire()/consult(). DM8 dropped the shadow set and was
    equivalent on 3.10/3.11 and wrong on 3.12/3.13 — this is the cell CI's 3.12/3.13 jobs kill it on."""
    un = _load("inv7_uninstrument_r12_s2b2", EVIDENCE / "inv7_uninstrument.py")
    un.uninstrument_source("from . import census as _census\nS = _census.declare_site('s')\n\n"
                           "x = [(lambda y=S: y) for S in range(3)]\n", "<s2b2>")



def test_r12_s2c_2_the_silent_route_is_refused_on_3_12_plus_and_reported_below():
    """RESEARCH'S S2c-2, END TO END. On 3.13 a census read in an inlinable comprehension placed in another
    comprehension's first iterable stayed LIVE in the twin with unresolved=0, because 3.13's symtable calls the
    comprehension variable local where the compiler resolves it to the module. On 3.12+ the resolver now refuses the
    shape, so the refusal reaches the caller instead of a clean-looking twin; on 3.10/3.11 symtable is right, the read
    resolves to the module's alias, and the live call is REPORTED."""
    un = _load("inv7_uninstrument_r12_s2c2", EVIDENCE / "inv7_uninstrument.py")
    src = ("from . import census as _census\nS = _census.declare_site('s')\n\n"
           "def f(q):\n    return [_census.enabled() for t in {0 for _census in range(1)}] and S.fire(q)\n")
    if sys.version_info >= (3, 12):
        with pytest.raises(un._scope.UnresolvableScope, match="symtable"):
            un.uninstrument_source(src, "<s2c2>")
    else:
        out, stats = un.uninstrument_source(src, "<s2c2>")
        assert "_census.enabled()" in out and stats["unresolved_bypass_candidates"] >= 1, \
            "on 3.10/3.11 the read resolves to the module's alias, and the live call must be reported"


# ROUND 13 — THE ROUND-12 VERDICT'S F1, END TO END. The resolver cells live in the scope file
# (test_r13_f1_every_scope_inside_a_comprehension_gets_its_own_table); this is the verdict's own statement, through
# derive() and the manifest: a census read handed the wrong table stayed LIVE in the twin with verify() clean AND
# `unresolved_bypass_candidates == 0`. One scope binds `_census` as its own parameter; the other reads the module's.
_R13_F1_SHAPES = [
    ("element-binds/if-reads",     "    return [(lambda _census: 0)(0) for x in [1] if (lambda: _census.enabled())()]\n"),
    ("element-binds/later-iter",   "    return [(lambda _census: 0)(0) for x in [1] for y in (lambda: [_census.enabled()])()]\n"),
    ("key-binds/value-reads",      "    return list({(lambda _census: 0)(0): (lambda: _census.enabled())() for x in [1]}.values())\n"),
    ("element-binds/later-target", "    return [(lambda _census: 0)(0) for x in [[0]] for x[(lambda: _census.enabled())()] in [1]]\n"),
]


@pytest.mark.parametrize("cell,line", _R13_F1_SHAPES, ids=[c for c, _ in _R13_F1_SHAPES])
def test_r13_f1_a_census_read_the_twin_keeps_is_reported_not_silent(cell, line, tmp_path):
    """"The disclosed scope-order gap changes a measured decision from [True] to [False] while verify() reports clean
    and the manifest records zero unresolved candidates." Reproduced at the round-12 pin on 3.10–3.13: the twin kept a
    live `_census.enabled()`, so its result depended on the census (the dict shape: [False] off, [True] on), and
    nothing said so. The read is still one the transform cannot rewrite in place; what must hold is that it is
    REPORTED, with its line, and never counted as zero."""
    un = _load("inv7_uninstrument_r13_f1", EVIDENCE / "inv7_uninstrument.py")
    slug = re.sub(r"\W", "_", cell)
    src = tmp_path / f"r13src_{slug}"; src.mkdir()
    (src / "__init__.py").write_text("")
    (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "mod.py").write_text("from . import census as _census\nS = _census.declare_site('s')\n\n\ndef f():\n" + line)
    out = tmp_path / f"r13twin_{slug}"
    un.derive(src, out)
    totals = json.loads((out.parent / "twin_manifest.json").read_text())["totals"]
    assert totals["unresolved_bypass_candidates"] == 1, \
        f"{cell}: a live census read in the twin is counted as {totals['unresolved_bypass_candidates']} unresolved"


# A two-module package whose `a` declares a site — the shape every cross-module cell below is built in.
_R13_A = "from . import census as _census\nS = _census.declare_site('a.s')\n\n\ndef g(v):\n    return S.fire(v)\n"


def _r13_pkg(tmp_path, slug, b_text, a_extra):
    src = tmp_path / slug / "vpkg"; src.mkdir(parents=True)
    (src / "__init__.py").write_text("")
    (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "a.py").write_text(_R13_A + a_extra)
    (src / "b.py").write_text(b_text)
    return src


def _r13_run_b(root):
    code = f"import sys; sys.path.insert(0, {str(root)!r}); import vpkg.b as b; print(b.f())"
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)




def test_r13_f2_a_sibling_using_only_ordinary_names_is_neither_refused_nor_reported(tmp_path):
    """The acceptance half: a sibling importing a FUNCTION from a site-declaring module, by name and as an attribute."""
    un = _load("inv7_uninstrument_r13_f2_ok", EVIDENCE / "inv7_uninstrument.py")
    for slug, b_text in (("by_name", "from .a import g\n\n\ndef f():\n    return g(True)\n"),
                         ("by_attribute", "from . import a\n\n\ndef f():\n    return a.g(True)\n")):
        src = _r13_pkg(tmp_path, slug, b_text, "")
        out = tmp_path / slug / "twin" / "vpkg"
        un.derive(src, out)
        assert un.verify(out, src) == [], f"{slug}: {un.verify(out, src)}"
        assert _r13_run_b(out.parent).stdout.strip() == "True"








# ROUND 13 — THREE READERS OF "WHICH NAMES ARE SITES", PINNED RATHER THAN UNIFIED. The transform (`declared_names`),
# the scope resolver (`Resolver.site_names`) and the binding scan (`installed_sites.scan`) each recognise a site
# declaration. Round 12's gate is scoped to the transform's file and named the other two as its boundary. Measured at
# round 13 over eleven declaration shapes: they AGREE on the three the tree uses and DISAGREE on four others — and every
# disagreement is LOUD end to end (derive refuses, or the evidence run's reconciliation refuses a registered id the scan
# does not show). ROUND 13 STAGE 2 (research's B3): "other object attr" WAS the silent one — an object from outside the
# package with a `declare_site` method was removed from the twin as a site, verify() clean; the transform now
# recognises a declaration only by its census BINDING, and the other two readers still say ['S'], each loudly caught.
# ROUND 14 CHANGED THE MECHANISM, NOT THE CLAIM: the token check no longer names `declare_site`, so the twin half is now
# that an unrecognised declaration is PRESERVED verbatim (it cannot corrupt the twin) and a fire()/consult() on it is
# refused (test_r13_b3_a_declare_site_method_on_an_outside_object_is_not_a_site); the scan half is
# `check_registry_against_scan`, which refuses a scanned site in a loaded module that did not register
# (test_r14_an_outside_declare_site_is_preserved_uncounted_and_the_scan_side_refuses). Unifying them into one definition is a refactor across four modules; this pins the whole matrix so a
# drift in ANY reader fails here, with the shape named, instead of surfacing as a disagreement a round later.
_R13_READER_SHAPES = {
    #  shape                  source                                                             site_names / declared_names / scan names
    "bare call":           ("from .census import declare_site\nS = declare_site('a')\n",              (["S"], ["S"], ["S"])),
    "alias attribute":     ("from . import census as _census\nS = _census.declare_site('a')\n",       (["S"], ["S"], ["S"])),
    "other object attr":   ("x = None\nS = x.declare_site('a')\n",                                    (["S"], [], ["S"])),
    "annotated":           ("from .census import declare_site\nS: object = declare_site('a')\n",      ([], [], [])),
    "tuple target":        ("from .census import declare_site\nS, T = declare_site('a'), 1\n",       ([], [], [])),
    "chained target":      ("from .census import declare_site\nS = T = declare_site('a')\n",         ([], [], [])),
    "inside a function":   ("from .census import declare_site\ndef f():\n    S = declare_site('a')\n", ([], [], ["S"])),
    "inside if":           ("from .census import declare_site\nif True:\n    S = declare_site('a')\n", ([], [], ["S"])),
    "non-literal id":      ("from .census import declare_site\nS = declare_site(NAME)\n",            (["S"], ["S"], [])),
    "keyword id":          ("from .census import declare_site\nS = declare_site(site_id='a')\n",     (["S"], ["S"], [])),
    "aliased import":      ("from .census import declare_site as ds\nS = ds('a')\n",                 ([], [], [])),
}


@pytest.mark.parametrize("shape", sorted(_R13_READER_SHAPES), ids=sorted(_R13_READER_SHAPES))
def test_r13_the_three_site_readers_answer_as_pinned(shape, tmp_path):
    un = _load("inv7_uninstrument_r13_readers", EVIDENCE / "inv7_uninstrument.py")
    sr_ = _load("scope_resolution_r13_readers", EVIDENCE / "scope_resolution.py")
    inst = _load("installed_sites_r13_readers", EVIDENCE / "installed_sites.py")
    src, want = _R13_READER_SHAPES[shape]
    (tmp_path / "m.py").write_text(src)
    got = (sorted(sr_.Resolver(src, "<r>").site_names()), sorted(un.declared_names(ast.parse(src))[0]),
           sorted({r["name"] for r in inst.scan(tmp_path) if r["name"]}))
    assert got == want, f"{shape}: (site_names, declared_names, scan) = {got}, pinned {want}"


def test_r14_an_outside_declare_site_is_preserved_uncounted_and_the_scan_side_refuses(tmp_path):
    """The "other object attr" shape end to end, after round 14 took `declare_site` out of the token check (found by
    round 14's docstring sweep, research's stage-2 addendum). The TWIN half: a `declare_site` on an object outside the
    package is ordinary code — preserved verbatim, and NOT counted as a site (the count asks the binding, like
    recognition; it counted the callee's spelling, which inflated the manifest's "declare_site preserved" figure).
    The SCAN half: the scan reads it as a site, and the registry check refuses it, loudly, because nothing registered."""
    un = _load("inv7_uninstrument_r14_outside", EVIDENCE / "inv7_uninstrument.py")
    inst = _load("installed_sites_r14_outside", EVIDENCE / "installed_sites.py")
    text = "x = None\nS = x.declare_site('a')\n\n\ndef f():\n    return S\n"
    out, stats = un.uninstrument_source(text, "<outside>")
    assert "S = x.declare_site('a')" in out and stats["sites"] == 0, (stats["sites"], out)
    # the counted half, beside it: a census declaration IS a site
    _, real = un.uninstrument_source("from .census import declare_site\nS = declare_site('a')\n", "<census>")
    assert real["sites"] == 1
    (tmp_path / "m.py").write_text(text)
    scanned = inst.scan(tmp_path)
    assert [(r["id"], r["name"]) for r in scanned] == [("a", "S")]
    refusals, _ = inst.check_registry_against_scan(scanned, {}, {r["module"] for r in scanned})
    assert len(refusals) == 1 and "did not register" in refusals[0], refusals


def test_r13_s2_6_an_unresolvable_scope_in_derive_names_its_module(tmp_path, monkeypatch):
    """RESEARCH'S S2-6: derive() wrapped only `Refused`, so an `UnresolvableScope` escaped naming a line and not the
    module. It now names the module and keeps its type (a caller catching UnresolvableScope still catches it).
    REWRITTEN (queued since round 13, the second seat's round-18 stage-1 read): the first form held a program only the
    join check's CURRENT refusal set cannot resolve, so the test was coupled to that set — at the round-12 pin nothing was
    raised at all, and a join check that learned to resolve the shape would have turned it vacuous. The refusal is now
    made by the resolver the transform calls, replaced for ONE module, so the test asserts the wrapping alone."""
    un = _load("inv7_uninstrument_r13_s26", EVIDENCE / "inv7_uninstrument.py")
    marker = "# r18: this module's scope is unresolvable"
    real = un._scope.Resolver

    class Unresolvable(real):
        def __init__(self, text, *a, **k):
            if marker in text:
                raise un._scope.UnresolvableScope("line 2: a scope the resolver refuses (injected)")
            super().__init__(text, *a, **k)

    monkeypatch.setattr(un._scope, "Resolver", Unresolvable)
    src = tmp_path / "vpkg"; src.mkdir()
    (src / "__init__.py").write_text(""); (src / "census.py").write_text(_R12_CENSUS_SRC.read_text())
    (src / "deep").mkdir(); (src / "deep" / "__init__.py").write_text("")
    (src / "deep" / "m.py").write_text("from .. import census as _census\n" + marker + "\nX = _census.enabled()\n")
    with pytest.raises(un._scope.UnresolvableScope) as caught:
        un.derive(src, tmp_path / "twin" / "vpkg")
    assert str(caught.value).startswith(str(pathlib.Path("deep") / "m.py") + ": "), str(caught.value)
    assert "(injected)" in str(caught.value), "the refusal is not the injected one: the test would be asserting something else"


def test_r13_b3_a_declare_site_method_on_an_outside_object_is_not_a_site(tmp_path):
    """RESEARCH'S STAGE-2 B3 — dev's own named attack, confirmed silent: `x = mock.MagicMock(); N =
    x.declare_site('a')` was removed from the twin as a site, verify() CLEAN; the source's `N.fire(4)` returned a
    MagicMock and the twin's returned 4. A declaration is now recognised only through a census binding, so this module
    keeps its call and is refused — loudly — rather than rewritten."""
    un = _load("inv7_uninstrument_r13_b3", EVIDENCE / "inv7_uninstrument.py")
    src = ("from unittest import mock\nx = mock.MagicMock()\nN = x.declare_site('a')\n\n\n"
           "def probe():\n    return type(N.fire(4)).__name__\n")
    assert un.declared_names(ast.parse(src))[0] == set()
    with pytest.raises(un.Refused):
        un.uninstrument_source(src, "<b3>")








# ROUND 14 — THE ROUND-13 VERDICT'S F1: "Site-reachability gaps still produce broken twins with clean verification."
# The twin removed every declaration from its first derivation, and rounds 12 and 13 REFUSED, one spelling at a time,
# every route by which code could still reach the name; the verdict found five more (pkgutil, runpy, importlib.util, __globals__, inspect). Round 14
# keeps every declared name bound to an inert stand-in, so no route can find it missing. Every route rounds 12 and 13
# refused, and every route the verdict found, is a cell here, and must DERIVE, VERIFY CLEAN, and give the same
# answer in the twin as in the source (the source runs the real census, default off; the twin the STUB).
_R14_SELF = "from . import census as _census\nS = _census.declare_site('b.s')\n\n\ndef g(v):\n    return S.fire(v)\n\n\n"
_R14_ROUTES = [
    # round 13's cross-module refusals (F2, R2 of its stage-1, N3)
    ("from-import",                  "from .a import S\n\n\ndef f():\n    return S is not None\n", {}),
    ("absolute from-import",         "from vpkg.a import S\n\n\ndef f():\n    return S is not None\n", {}),
    ("star import over __all__",     "from .a import *\n\n\ndef f():\n    return S is not None and g(True)\n", {"a+": "__all__ = ['S', 'g']\n"}),
    ("attribute via from . import a", "from . import a\n\n\ndef f():\n    return a.S is not None\n", {}),
    ("attribute via import as",      "import vpkg.a as m\n\n\ndef f():\n    return m.S is not None\n", {}),
    ("attribute via dotted chain",   "import vpkg.a\n\n\ndef f():\n    return vpkg.a.S is not None\n", {}),
    ("a literal __all__, no importer", "from .a import g\n\n\ndef f():\n    return g(True)\n", {"a+": "__all__ = ['S', 'g']\n"}),
    # round 13's P1 and the six bypasses sent before its commit
    ("getattr, literal",             "from . import a\n\n\ndef f():\n    return getattr(a, 'S') is not None\n", {}),
    ("getattr, non-literal",         "from . import a\nNAME = 'S'\n\n\ndef f():\n    return getattr(a, NAME) is not None\n", {}),
    ("getattr aliased",              "from . import a\n_ga = getattr\n\n\ndef f():\n    return _ga(a, 'S') is not None\n", {}),
    ("import_module, literal",       "import importlib\n\n\ndef f():\n    return importlib.import_module('vpkg.a').S is not None\n", {}),
    ("import_module aliased",        "from importlib import import_module as im\n\n\ndef f():\n    return im('vpkg.a').S is not None\n", {}),
    ("import_module, non-literal",   "import importlib\nM = 'vpkg.a'\n\n\ndef f():\n    return importlib.import_module(M).S is not None\n", {}),
    ("__import__",                   "def f():\n    return __import__('vpkg.a', fromlist=['S']).S is not None\n", {}),
    ("sys.modules",                  "import sys\nimport vpkg.a\n\n\ndef f():\n    return sys.modules['vpkg.a'].S is not None\n", {}),
    ("vars of the module",           "from . import a\n\n\ndef f():\n    return vars(a)['S'] is not None\n", {}),
    ("the module's __dict__",        "from . import a\n\n\ndef f():\n    return a.__dict__['S'] is not None\n", {}),
    ("operator.attrgetter",          "import operator\nfrom . import a\n\n\ndef f():\n    return operator.attrgetter('S')(a) is not None\n", {}),
    # round 13's closure refinement and D1
    ("a module carrying a site",     "from . import c\n\n\ndef h(m):\n    return getattr(m.a, 'S')\n\n\ndef f():\n    return h(c) is not None\n", {"c.py": "from . import a\n"}),
    ("a package object",             "import vpkg\nimport vpkg.a\n\n\ndef h(m):\n    return m.a.S\n\n\ndef f():\n    return h(vpkg) is not None\n", {}),
    ("self: import pkg.b as me",     "import vpkg.b as me\n" + _R14_SELF + "def f():\n    return getattr(me, 'S') is not None\n", {}),
    ("self: from . import b as me",  "from . import b as me\n" + _R14_SELF + "def f():\n    return me.S is not None\n", {}),
    ("self: import_module",          "import importlib\n" + _R14_SELF + "def f():\n    return importlib.import_module('vpkg.b').S is not None\n", {}),
    # round 13's namespace refusal (B2), in the site's own module
    ("globals()",                    _R14_SELF + "def f():\n    return globals()['S'] is S\n", {}),
    ("globals by another name",      "_gl = globals\n" + _R14_SELF + "def f():\n    return _gl()['S'] is not None\n", {}),
    ("vars()",                       _R14_SELF + "V = vars()\n\n\ndef f():\n    return V['S'] is not None\n", {}),
    ("eval",                         _R14_SELF + "def f():\n    return eval('S') is not None\n", {}),
    ("exec",                         _R14_SELF + "def f():\n    ns = {}\n    exec('X = S', globals(), ns)\n    return ns['X'] is S\n", {}),
    ("sys by another name",          "import sys as _s\n" + _R14_SELF + "def f():\n    return _s.modules[__name__].S is not None\n", {}),
    # round 12's R2 — a declared site loaded as a value
    ("the site passed as a value",   _R14_SELF + "def f():\n    return register(S) is S\n\n\ndef register(s):\n    return s\n", {}),
    ("the site in a module registry", _R14_SELF + "REGISTRY = [S]\n\n\ndef f():\n    return REGISTRY[0] is S\n", {}),
    # the round-13 verdict's F1: five routes the round-13 refusals did not name
    ("pkgutil.resolve_name",         "import pkgutil\n\n\ndef f():\n    return pkgutil.resolve_name('vpkg.a:S') is not None\n", {}),
    ("runpy.run_module",             "import runpy\n\n\ndef f():\n    return runpy.run_module('vpkg.a')['S'] is not None\n", {}),
    ("importlib.util loading",       "import importlib.util\n\n\ndef f():\n    sp = importlib.util.find_spec('vpkg.a'); m = importlib.util.module_from_spec(sp)\n    sp.loader.exec_module(m)\n    return m.S is not None\n", {}),
    ("a function's __globals__",     "from .a import g\n\n\ndef f():\n    return g.__globals__['S'] is not None\n", {}),
    ("inspect.getmodule",            "import inspect\nfrom .a import g\n\n\ndef f():\n    return inspect.getmodule(g).S is not None\n", {}),
]


@pytest.mark.parametrize("cell,b_text,extra", _R14_ROUTES, ids=[c for c, _, _ in _R14_ROUTES])
def test_r14_f1_no_route_to_a_declared_site_breaks_the_twin(cell, b_text, extra, tmp_path):
    """THE ROUND-13 VERDICT'S F1, closed by construction rather than by one more refusal: the twin keeps every
    declaration, bound to the STUB's inert stand-in, so however a route is spelled it finds a name that is there."""
    un = _load("inv7_uninstrument_r14_f1", EVIDENCE / "inv7_uninstrument.py")
    slug = re.sub(r"\W", "_", cell)
    src = _r13_closure_pkg(tmp_path, slug, b_text, {k: v for k, v in extra.items() if k != "a+"})
    if "a+" in extra:
        (src / "a.py").write_text((src / "a.py").read_text() + extra["a+"])
    out = tmp_path / slug / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == [], f"{cell}: {un.verify(out, src)}"
    ran_src, ran_twin = _r13_run_b(src.parent), _r13_run_b(out.parent)
    assert ran_src.returncode == 0, f"{cell}: the SOURCE does not run: {ran_src.stderr[-300:]}"
    assert (ran_twin.returncode, ran_twin.stdout) == (0, ran_src.stdout), \
        f"{cell}: source printed {ran_src.stdout!r}, the twin {ran_twin.stdout!r} {ran_twin.stderr[-300:]}"


def test_r14_a_fire_the_transform_cannot_bind_is_still_refused():
    """What round 14 KEEPS refusing (research's stage-1 read): a `fire()` whose receiver is not this module's declared
    site by name — reached through `globals()`, another module, or any expression — is a MEASUREMENT the transform
    cannot unwrap, and a live measurement in the twin is refused, not left to run."""
    un = _load("inv7_uninstrument_r14_fire", EVIDENCE / "inv7_uninstrument.py")
    for body in ("def f():\n    return globals()['S'].fire(1)\n", "from .a import S as T\n\n\ndef f():\n    return T.fire(1)\n"):
        with pytest.raises(un.Refused):
            un.uninstrument_source(_R14_SELF + body, "<fire>")


# ---- round 15: the twin keeps a REAL census.py (the owner's decision, 2026-09-24): round 15 the SOURCE'S verbatim; round 16
# the REFERENCE census, an accepted commit's (tests below) — these round-15 tests hold under both --------------------------
# The round-14 verdict: "The new stand-in can still change an instrumented decision from True to False while
# verification is clean and its use counter stays at zero." Reproduced at 8074e6b through the stand-in's CLASS — its
# counting overrides of object's dunders. The stand-in is gone: a declaration binds the source's own Site, so a question
# about the class or an instance answers as the census-off arm's does BY CONSTRUCTION, and "no census code takes part in
# a decision" is MEASURED outside the twin (inv7_observer.py's hook; research's stage-1 conditions B1–B3).

_R15_SHAPES = [
    # the verdict's class, reproduced eight ways at 8074e6b (source True, twin False, verify clean, 0 uses) ...
    "type(S).__hash__ is object.__hash__", "type(S).__eq__ is object.__eq__", "type(S).__repr__ is object.__repr__",
    "type(S).__getattribute__ is object.__getattribute__", "'__eq__' not in vars(type(S))",
    "not hasattr(type(S), '__bool__')", "S.__class__.__hash__ is object.__hash__",
    "sorted(vars(type(S))) == sorted(vars(_census.Site))",
    # ... the two controls of that reproduction, and the identity the class now carries
    "object.__getattribute__(S, 'fired') == 0", "type(S).counters(S) == {'consulted': 0, 'fired': 0, 'errors': 0}",
    "type(S) is _census.Site", "repr(S).startswith('<vpkg.census.Site object at ')",
]


@pytest.mark.parametrize("shape", _R15_SHAPES, ids=range(len(_R15_SHAPES)))
def test_r15_every_question_about_a_site_answers_alike_in_source_and_twin(shape, tmp_path):
    """The round-14 verdict's class, end to end: derive, verify CLEAN, run source and twin — the same answer, which is
    the source's True. Under round 14's stand-in the first eight read False in the twin."""
    un = _load("inv7_uninstrument_r15_shapes", EVIDENCE / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "shape", _R14_SELF + f"def f():\n    return {shape}\n", "")
    out = tmp_path / "shape" / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == []
    ran_src, ran_twin = _r13_run_b(src.parent), _r13_run_b(out.parent)
    assert ran_src.stdout == "True\n", ran_src.stdout + ran_src.stderr
    # the message carries what the twin ANSWERED as well as its stderr, which is empty when it simply answers False (the
    # class-shapes row printed a blank failure line in round 15)
    assert (ran_twin.returncode, ran_twin.stdout) == (0, "True\n"), (shape, ran_twin.returncode, ran_twin.stdout, ran_twin.stderr[-300:])


def test_r16_the_twin_census_is_the_reference_census_and_verify_refuses_any_other(tmp_path, monkeypatch):
    """Round 16 (the owner's "(3) Accepted census"): the twin's census.py is the REFERENCE census — an accepted commit's
    census.py, tracked as specs/evidence/0042/reference_census.py and pinned by digest — not HEAD's. (It equals HEAD's
    today, byte for byte: census.py has not changed since round 8, so the protection is PROSPECTIVE and the separating
    test below is what demonstrates it.) A declaration binds that module's Site and is the object its registry holds;
    re-declaring an id — a reload — is refused in BOTH. The controls: a twin whose census differs by one byte at the
    same length is refused by verify(); a reference file that is not the pinned digest is refused by derive()."""
    un = _load("inv7_uninstrument_r16_identity", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_bytes()
    assert hashlib.sha256(ref).hexdigest() == un.REFERENCE_CENSUS_SHA256
    src = _r13_pkg(tmp_path, "ident", _R14_SELF + "def f():\n    return 1\n", "")
    out = tmp_path / "ident" / "twin" / "vpkg"
    un.derive(src, out)
    assert (out / "census.py").read_bytes() == ref
    assert un.verify(out, src) == []
    code = ("import sys, importlib; sys.path.insert(0, {root!r}); import vpkg.b as b, vpkg.census as c\n"
            "print(type(b.S) is c.Site, c._REGISTRY['b.s'] is b.S)\n"
            "try:\n    importlib.reload(b); print('reload accepted')\nexcept c.CensusError: print('reload refused')\n")
    for root in (src.parent, out.parent):
        r = subprocess.run([sys.executable, "-c", code.format(root=str(root))], capture_output=True, text=True)
        assert r.stdout.split("\n")[:2] == ["True True", "reload refused"], (root, r.stdout, r.stderr[-300:])
    # one byte FLIPPED at the same length in the TWIN's census: refused by verify()
    data = bytearray((out / "census.py").read_bytes()); i = data.index(b"census") + 1; data[i] ^= 0x20
    assert len(data) == len(ref) and bytes(data) != ref
    (out / "census.py").write_bytes(bytes(data))
    assert any("not the reference census" in p for p in un.verify(out, src)), un.verify(out, src)
    # and a reference FILE that is not the pinned digest: refused by derive() — advancing T is a spec change
    fake = tmp_path / "reference_census.py"; fake.write_bytes(bytes(data))
    monkeypatch.setattr(un, "REFERENCE_CENSUS", fake)
    with pytest.raises(un.Refused, match="advancing T is a specification change"):
        un.derive(src, tmp_path / "ident" / "twin2" / "vpkg")

_R15_OFF_FORMS = {
    "with consult": lambda s: s.consult().__enter__(), "consult statement": lambda s: s.consult(),
    "fire True": lambda s: s.fire(True), "fire False": lambda s: s.fire(False), "fire None": lambda s: s.fire(None),
    "fire labelled": lambda s: s.fire(ValueError("x"), "lbl"), "fire declined=True": lambda s: s.fire(7, declined=True),
    "fire declined=False": lambda s: s.fire(None, declined=False), "declined": lambda s: s.declined(None),
}


def test_r15_b3_with_the_census_off_consult_and_fire_leave_every_slot_unchanged():
    """Research's stage-1 B3 — THE PREMISE of "uncounted = faithful". A read that runs no census Python code (a slot, `is`,
    `id`, `type`, object's dunders) is uncounted by the hook, and it answers as the source's only because the twin's
    Sites are real Sites in the OFF state and, in that state, consult and fire leave EVERY slot as it was. The slots are
    DERIVED from `Site.__slots__`; each form runs on a fresh Site and the whole slot state is compared before and after
    (the lock and the failures dict by identity, the rest by value)."""
    import veracium.census as C
    assert C.enabled() is False
    for label, form in _R15_OFF_FORMS.items():
        s = C.Site("r15.b3", None)
        before = {n: getattr(s, n) for n in C.Site.__slots__}
        form(s)
        after = {n: getattr(s, n) for n in C.Site.__slots__}
        for n in C.Site.__slots__:
            same = after[n] is before[n] if n in ("_lock", "failures", "_declines") else after[n] == before[n]
            assert same, (label, n, before[n], after[n])
        assert s.failures == {}, (label, s.failures)


_R15_CHAIN_CELLS = [
    # (cell, test module text, the entries predicate, the gate's expected value)
    ("declaration only", "import importlib\n\n\ndef test_it():\n    m = importlib.import_module(MOD)\n    assert getattr(m, NAME) is not None\n",
     lambda n: n == 0, True),
    ("product code enables the census", "from veracium import Memory\nfrom veracium.config import MemoryConfig\n\n\ndef test_it(tmp_path):\n"
     "    m = Memory(llm=lambda *a, **k: '', config=MemoryConfig(db_path=str(tmp_path / 'b.db'), census_enabled=True)); m.close()\n",
     lambda n: n is not None and n >= 1, False),
    ("a Site method through the class", "import importlib\n\n\ndef test_it():\n    m = importlib.import_module(MOD)\n    S = getattr(m, NAME)\n"
     "    assert type(S).counters(S) is not None\n", lambda n: n is not None and n >= 1, False),
    ("a declaration from a TEST module body", "from veracium import census as _c\n\nT = _c.declare_site('r15.test-module-body')\n\n\n"
     "def test_it():\n    assert T is not None\n", lambda n: n is not None and n >= 1, False),
    ("an exec'd declaration", "def test_it():\n    exec(\"from veracium import census as c\\nc.declare_site('r15.exec')\", {})\n",
     lambda n: n is not None and n >= 1, False),
    ("the hook cleared mid-run", "import sys\n\n\ndef test_it():\n    sys.setprofile(None)\n", lambda n: n is None, False),
    # research's pre-seal read, three survivors killed: the liveness check must see the hook REPLACED, not only cleared
    # (N-1); a census call from a WORKER THREAD must count (N-2: threading.setprofile); and a PRODUCT module body calling
    # a census function other than declare_site must count — the exclusion is the declaration's code object, not any
    # call from a product module body (N-3; the fixture writes that module into the twin)
    ("the hook replaced by another profiler", "import sys\n\n\ndef test_it():\n    sys.setprofile(lambda *a: None)\n", lambda n: n is None, False),
    ("census code from a worker thread", "import importlib, threading\n\n\ndef test_it():\n    m = importlib.import_module(MOD)\n    S = getattr(m, NAME)\n"
     "    t = threading.Thread(target=lambda: type(S).counters(S)); t.start(); t.join()\n", lambda n: n is not None and n >= 1, False),
    ("a product module body calling enabled()", "import importlib\n\n\ndef test_it():\n    importlib.import_module('veracium.r15_probe_body')\n",
     lambda n: n is not None and n >= 1, False),
]


@pytest.fixture(scope="module")
def r15_twin(tmp_path_factory):
    """The REAL tree's twin, derived once for the chain cells, and a throwaway repo whose `.venv/bin/python` is THIS
    interpreter (run_arm runs `<repo>/.venv/bin/python`; CI and a packaged copy have no .venv)."""
    un = _load("inv7_uninstrument_r15_chain", EVIDENCE / "inv7_uninstrument.py")
    base = tmp_path_factory.mktemp("r15chain")
    twin = base / "twin"
    un.derive(ROOT / "src" / "veracium", twin / "veracium")
    site = None
    for p in sorted((twin / "veracium").rglob("*.py")):
        m = re.search(r"^(\w+) = (?:\w+\.)?declare_site\(", p.read_text(), re.M)
        if m and not un.is_census_module_file(str(p.relative_to(twin / "veracium"))):
            # a package's __init__ is imported by the PACKAGE's name: importing `veracium.__init__` executes the body a
            # second time, and the real census rightly refuses the duplicate declarations (round 14's stand-in did not,
            # which hid this in its harness cell)
            site = (".".join(("veracium",) + p.relative_to(twin / "veracium").with_suffix("").parts).removesuffix(".__init__"), m.group(1)); break
    assert site is not None
    # a PRODUCT module (under the twin's root) whose body calls a census function that is not declare_site (N-3)
    (twin / "veracium" / "r15_probe_body.py").write_text("from . import census as _census\n\n_census.enabled()\n")
    repo = base / "repo"; (repo / ".venv" / "bin").mkdir(parents=True)
    shim = repo / ".venv" / "bin" / "python"; shim.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n"); shim.chmod(0o755)
    return base, twin, repo, site


@pytest.mark.parametrize("cell,text,entries_ok,gate", _R15_CHAIN_CELLS, ids=[c[0] for c in _R15_CHAIN_CELLS])
def test_r15_the_reference_arm_s_census_count_fails_through_the_real_chain(cell, text, entries_ok, gate, r15_twin):
    """Research's stage-1 conditions 2, 3 and B1–B2, through the REAL chain — the real tree's twin, the observer inside
    a pytest run, run_arm's summary, compare's checks, final_status's gate. Declarations from product module bodies and
    the observer's own reads are excluded (the acceptance cell reads 0, gate TRUE); census code reached any other way
    counts — product code enabling the census, a Site method through the class, a declaration from a TEST module body
    or from exec'd text (the exclusion needs the product root, not only a module body) — and a hook cleared mid-run
    reports None, never a 0 that measured nothing."""
    harness = _load("inv7_harness_r15_chain", EVIDENCE / "inv7_harness.py")
    base, twin, repo, (mod, name) = r15_twin
    slug = re.sub(r"\W", "_", cell)
    t = base / slug / f"test_r15_{slug}.py"; t.parent.mkdir()
    t.write_text(f"MOD = {mod!r}\nNAME = {name!r}\n" + text)
    out = base / slug / "out"
    s = harness.run_arm(repo, "uninstrumented", [str(t)], out, EVIDENCE / "declaration.py", twin_src=str(twin))
    assert s["pytest_exit"] == 0, (cell, s.get("pytest_result_line"), (out / "uninstrumented" / "pytest_stdout.txt").read_text()[-600:])
    assert pathlib.Path(s["veracium_file"]).is_relative_to(twin), s["veracium_file"]
    v, c = harness.compare(out, ["uninstrumented"], {"uninstrumented": s}, ID_TO_SYMBOL)
    harness.final_status(v, c, {"uninstrumented": s}, ["uninstrumented"])
    n = s["census_code_entries"]
    assert entries_ok(n), (cell, n, s.get("census_code_entry_detail"))
    assert v["gates"]["uninstrumented:no_census_code_in_decisions"] is gate, (cell, n, v["gates"])


_R15_REGISTRY_CELLS = [
    # (cell, what the reference arm's test does to the registry — no census code runs, so only the registry gate moves, gate)
    ("registries equal", "", True),
    ("the reference registry lacks an id", "        del _c._REGISTRY[sorted(_c._REGISTRY)[0]]\n", False),
    ("the reference registry has an extra id", "        _c._REGISTRY['r15.extra-id'] = object()\n", False),
]


@pytest.mark.parametrize("cell,mutate,gate", _R15_REGISTRY_CELLS, ids=[c[0] for c in _R15_REGISTRY_CELLS])
def test_r15_the_registry_gate_fails_through_the_real_chain(cell, mutate, gate, r15_twin):
    """Research's pre-seal B-1: no cell ever turned `uninstrumented:registry_equals_off` FALSE, so a comparison weakened
    to a subset survived. Both arms run through the REAL chain (the off arm on the source, the reference arm on the twin);
    the reference arm's test alters the registry WITHOUT running census code (a dict edit), so the count gate stays true
    and only the registry gate can move — an id missing, or an extra one, each turns it false; equal registries pass."""
    harness = _load("inv7_harness_r15_registry", EVIDENCE / "inv7_harness.py")
    base, twin, repo, (mod, name) = r15_twin
    slug = "reg_" + re.sub(r"\W", "_", cell)
    t = base / slug / f"test_r15_{slug}.py"; t.parent.mkdir()
    t.write_text(f"import importlib, os\nfrom veracium import census as _c\n\n\ndef test_it():\n    importlib.import_module({mod!r})\n"
                 f"    if os.environ.get('INV7_ARM') == 'uninstrumented':\n" + (mutate or "        pass\n"))
    out = base / slug / "out"
    S = {"off": harness.run_arm(repo, "off", [str(t)], out, EVIDENCE / "declaration.py"),
         "uninstrumented": harness.run_arm(repo, "uninstrumented", [str(t)], out, EVIDENCE / "declaration.py", twin_src=str(twin))}
    for arm, s in S.items():
        assert s["pytest_exit"] == 0, (cell, arm, s.get("pytest_result_line"), (out / arm / "pytest_stdout.txt").read_text()[-600:])
    assert pathlib.Path(S["uninstrumented"]["veracium_file"]).is_relative_to(twin) and not pathlib.Path(S["off"]["veracium_file"]).is_relative_to(twin)
    arms = ["off", "uninstrumented"]
    v, c = harness.compare(out, arms, S, ID_TO_SYMBOL)
    harness.final_status(v, c, S, arms)
    assert v["gates"]["uninstrumented:no_census_code_in_decisions"] is True, (cell, S["uninstrumented"].get("census_code_entry_detail"))
    assert v["gates"]["uninstrumented:registry_equals_off"] is gate, (cell, len(S["off"]["census_registry_ids"]), len(S["uninstrumented"]["census_registry_ids"]))


_R16_DRIFT = [
    # (cell, (old, new) in HEAD's census.py, drift expected) — HEAD's Site against the reference's, both directions
    ("a method body changed", ('        with self._lock:\n            return dict(self.failures)', '        with self._lock:\n            return dict(self.failures) or {}'), True),
    ("a member added to HEAD", ('    def failure_kinds(self) -> dict:', '    def extra(self):\n        return 1\n\n    def failure_kinds(self) -> dict:'), True),
    ("a member removed from HEAD", ('    def __enter__(self):\n        return self                           # the count happened in consult(); the bracket only scopes the body\n\n', ''), True),
    ("__slots__ changed", ('"_declines", "failures")', '"_declines", "failures", "extra")'), True),
    ("a base class added", ('class Site:', 'class Site(object):'), True),
    # the second seat's round-16 pre-seal mutants M10, M3 and M4 each survived the cells above (N-1 to N-3)
    ("a signature and default changed", ('    def failure_kinds(self) -> dict:', '    def failure_kinds(self, detail=False) -> dict:'), True),
    ("a decorator added", ('    def failure_kinds(self) -> dict:', '    @staticmethod\n    def failure_kinds(self) -> dict:'), True),
    ("a class-body statement added", ('    __slots__ = ("site_id",', '    if True:\n        pass\n    __slots__ = ("site_id",'), True),
    ("the class docstring changed", ('    """One enforcement point\'s counters.', '    """One enforcement point\'s counters (changed).'), True),
    ("formatting only (a comment and blank lines)", ('    def failure_kinds(self) -> dict:', '    # a comment\n\n    def failure_kinds(self) -> dict:'), False),
]


@pytest.mark.parametrize("cell,edit,drift", _R16_DRIFT, ids=[c[0] for c in _R16_DRIFT])
def test_r16_a_drifted_site_is_refused_and_t_must_advance(cell, edit, drift, tmp_path):
    """Research's stage-1 condition 3: HEAD's Site and the reference census's Site compared MEMBER BY MEMBER, by source
    (the AST of each member), in BOTH directions. A change to Site's OWN definition — a body, a signature or default, a
    decorator, a member added or removed, the slots, a class-body statement, the docstring, the class header — is drift:
    derive() refuses it and verify() reports it, "T must advance"; a formatting-only change is not drift. (A change to a
    census helper OUTSIDE Site is not drift — it is census code under test, outside the reference arm — see site_drift.)
    Today HEAD's Site equals the reference's, so the real tree reads no drift."""
    un = _load("inv7_uninstrument_r16_drift", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    assert un.site_drift(_R12_CENSUS_SRC.read_text(), ref) == []
    old, new = edit
    assert ref.count(old) == 1, (cell, ref.count(old))
    head = ref.replace(old, new)
    found = un.site_drift(head, ref)
    assert bool(found) is drift, (cell, found)
    src = _r13_pkg(tmp_path, "drift", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(head)
    out = tmp_path / "drift" / "twin" / "vpkg"
    if drift:
        with pytest.raises(un.Refused, match="T must advance"):
            un.derive(src, out)
    else:
        un.derive(src, out)
        assert un.verify(out, src) == []


# ---- round 17: the drift check read TWO ways -----------------------------------------------------------------------
# The round-16 verdict: the drift check modelled Site's class body (an ORDERED sequence in which a name can repeat) as a
# MAP, so a docstring moved below `__slots__`, or changed with T's text re-added later, read no drift while the source and
# the reference answered `Site.__doc__` differently. The second seat's stage-1 read: whole-ClassDef equality is necessary
# and NOT sufficient — a module-level statement after the class (`Site.__doc__ = …`) changes the class Site names with the
# ClassDef equal. So drift is read two ways, and each cell names the route(s) that must see it: A, the DEFINITION as
# written (the whole ClassDef); B, the class each census BUILDS when executed. A mutant removing either route fails a cell.
_R17_DOC_SLOTS = re.compile(r'(class Site:\n)(    """One enforcement point.*?"""\n)(    __slots__ = \(.*?\)\n)', re.S)
_R17_ENTER_EXIT = ("    def __enter__(self):\n        return self                           # the count happened in consult(); the bracket only scopes the body\n\n"
                   "    def __exit__(self, exc_type, exc, tb):\n        return False                          # never swallows the decision's raise\n")
_R17_AFTER = "\ndef _label_of(decision) -> str:"


def _r17_after(line):
    return lambda s: s.replace(_R17_AFTER, "\n" + line + "\n\n" + _R17_AFTER, 1)


def _r17_sub(pattern, fn):
    def edit(s):
        assert len(pattern.findall(s)) == 1, "the cell's anchor must match exactly once"
        return pattern.sub(fn, s, count=1)
    return edit


def _r17_swap_enter_exit(s):
    a, b = _R17_ENTER_EXIT.split("\n\n")
    assert s.count(_R17_ENTER_EXIT) == 1
    return s.replace(_R17_ENTER_EXIT, b + "\n" + a + "\n")


_R17_BASE_X = ("class _X:\n    def __new__(cls, *a):\n        return a[0] if a and isinstance(a[0], type) else super().__new__(cls)\n\n\n")
_R17_CELLS = [
    # (cell, prepare BOTH sides (None: T as is), HEAD's edit, the route(s) that must see it)
    ("the verdict's first: the docstring moved below __slots__", None,
     _r17_sub(_R17_DOC_SLOTS, lambda m: m.group(1) + m.group(3) + m.group(2)), "AB"),
    ("the verdict's second: the docstring changed and T's text re-added later", None,
     _r17_sub(_R17_DOC_SLOTS, lambda m: m.group(1) + '    """A DIFFERENT docstring."""\n' + m.group(3) + m.group(2)), "AB"),
    ("a duplicate method BEFORE the original (the original wins: behaviour-neutral, still drift)", None,
     lambda s: s.replace("    def failure_kinds(self) -> dict:", "    def failure_kinds(self) -> dict:\n        return {}\n\n    def failure_kinds(self) -> dict:", 1), "A"),
    ("two methods swapped (behaviour-neutral order, still drift)", None, _r17_swap_enter_exit, "AB"),
    ("post-class: Site.__doc__ assigned", None, _r17_after("Site.__doc__ = 'changed after the class'"), "B"),
    ("post-class: Site.fire's defaults replaced", None, _r17_after("Site.fire.__defaults__ = ('changed',)"), "B"),
    ("post-class: setattr(Site, 'extra', 1)", None, _r17_after("setattr(Site, 'extra', 1)"), "B"),
    ("post-class: Site.fire rebound", None, _r17_after("Site.fire = Site.__enter__"), "B"),
    # the second seat's round-17 pre-seal read: fields on the TYPE object, not in vars(Site)
    ("post-class: Site.__qualname__ assigned", None, _r17_after("Site.__qualname__ = 'NotSite'"), "B"),
    ("post-class: Site.__name__ assigned", None, _r17_after("Site.__name__ = 'NotSite'"), "B"),
    ("a module-level name read at class creation, with a different VALUE",
     lambda s: s.replace("class Site:", "_SLOT_EXTRA = ()\n\n\nclass Site:", 1).replace('"_declines", "failures")', '"_declines", "failures") + _SLOT_EXTRA', 1),
     lambda s: s.replace("_SLOT_EXTRA = ()", "_SLOT_EXTRA = ('extra',)", 1), "B"),
    ("a base class X in T, a decorator X in HEAD (the header compared by field, not as one string)",
     lambda s: s.replace("class Site:", _R17_BASE_X + "class Site(_X):", 1),
     lambda s: s.replace("class Site(_X):", "@_X\nclass Site:", 1), "AB"),
]


@pytest.mark.parametrize("cell,prepare,edit,routes", _R17_CELLS, ids=[c[0] for c in _R17_CELLS])
def test_r17_site_drift_reads_the_definition_and_the_realized_class(cell, prepare, edit, routes, tmp_path):
    """Each cell's change is drift, seen by EXACTLY the route(s) it names; the union is site_drift. A cell that edits
    T's census alone also runs derive (which must refuse, "T must advance"); a cell that must prepare BOTH sides (T has
    no base class or module-level slot name to vary) reads site_drift on the pair, since T is pinned."""
    un = _load("inv7_uninstrument_r17", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    base = prepare(ref) if prepare else ref
    assert base != ref or prepare is None
    head = edit(base)
    assert head != base, (cell, "the edit changed nothing")
    assert un.site_drift(base, base) == [], (cell, "the prepared reference drifts from itself")
    # the VERDICT first, through the name the round-16 pin also has, so at that pin the cell fails on the defect itself
    # (site_drift reads [] for the change) and not on a name round 17 introduced
    found = un.site_drift(head, base)
    assert found, (cell, "site_drift read NO drift for a change to Site's definition")
    if prepare is None:
        src = _r13_pkg(tmp_path, "r17", _R14_SELF + "def f():\n    return 1\n", "")
        (src / "census.py").write_text(head)
        with pytest.raises(un.Refused, match="T must advance"):
            un.derive(src, tmp_path / "r17" / "twin" / "vpkg")
    a, b = un._definition_drift(head, base), un._realized_drift(head, base)
    assert (bool(a), bool(b)) == ("A" in routes, "B" in routes), (cell, a, b)
    assert found == a + b


def test_r17_formatting_is_not_drift_on_either_route():
    """The acceptance half: comments and blank lines inside and after Site are not drift (site_drift is the union of the
    two routes, so an empty union is an empty route each)."""
    un = _load("inv7_uninstrument_r17f", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    head = ref.replace("    def failure_kinds(self) -> dict:", "    # a comment\n\n    def failure_kinds(self) -> dict:", 1)
    head = head.replace(_R17_AFTER, "\n# a comment after the class\n" + _R17_AFTER, 1)
    assert head != ref
    assert un.site_drift(head, ref) == []


# ---- round 18 (queued after round 17's pre-seal reads; worked while the round-17 verdict is out) ------------------------
# N-7: a cell for each of the second seat's route-B stage-2 survivors that a change can reach — a method differing ONLY in
# a constant (BM1), a closure differing ONLY in its value (BM2), an attribute set on a method (BM3); and the class header's
# `keywords` field, which the comparison covered and no cell varied. (BM4 — type-level values compared by type only — has
# no cell: every writable type-level field is also visible in vars(Site) or the MRO, measured; see the second seat's note.)
_R18_EXIT_CONST = "Site.__exit__.__code__ = Site.__exit__.__code__.replace(co_consts=tuple(True if c is False else c for c in Site.__exit__.__code__.co_consts))"
_R18_MAKER = "def _r18_make(v):\n    def extra(self):\n        return v\n    return extra\n\n\nSite.extra = _r18_make(1)"
_R18_CELLS = [
    ("a method differing ONLY in a constant", None, _r17_after(_R18_EXIT_CONST), "B"),
    ("a method differing ONLY in its closure's value", _r17_after(_R18_MAKER),
     lambda s: s.replace("Site.extra = _r18_make(1)", "Site.extra = _r18_make(2)", 1), "B"),
    ("an attribute set on a method", None, _r17_after("Site.fire.marker = 1"), "B"),
    ("the class header's keywords field (metaclass=type: the same class built, a different definition)", None,
     lambda s: s.replace("class Site:", "class Site(metaclass=type):", 1), "A"),
]


@pytest.mark.parametrize("cell,prepare,edit,routes", _R18_CELLS, ids=[c[0] for c in _R18_CELLS])
def test_r18_route_b_sees_constants_closures_and_method_attributes(cell, prepare, edit, routes, tmp_path):
    """The same shape as the round-17 cells: the verdict first, through site_drift; then exactly the named route(s)."""
    test_r17_site_drift_reads_the_definition_and_the_realized_class(cell, prepare, edit, routes, tmp_path)


def test_r18_the_constant_cell_changes_only_a_constant():
    """The cell's premise, pinned: the edited __exit__ differs from T's in co_consts and in nothing else route B reads."""
    un = _load("inv7_uninstrument_r18c", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    h, r = un._realized_site(_r17_after(_R18_EXIT_CONST)(ref), "_x").__exit__, un._realized_site(ref, "_x").__exit__
    normal_code = lambda co: un._normalise(co, {})[1]          # the code branch of the recursive rule (was un._normal_code)
    hn, rn = dict(normal_code(h.__code__)), dict(normal_code(r.__code__))
    assert [k for k in rn if hn[k] != rn[k]] == ["co_consts"], [k for k in rn if hn[k] != rn[k]]


def test_r18_an_address_is_not_drift():
    """N-8, the acceptance half: the SAME definition built twice holds objects at different addresses (a lock here); that
    is where, not what, and must not read as drift on either route."""
    un = _load("inv7_uninstrument_r18a", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    both = _r17_after("Site._probe_lock = threading.Lock()\nSite.fire.marker = threading.Lock()")(ref)
    assert "at 0x" in repr(un._realized_site(both, "_x")._probe_lock)          # the premise: the repr carries an address
    assert un.site_drift(both, both) == []


_R18_NEUTRAL = [
    # (cell, a behaviour-neutral line after the class) — each sets the type's attribute-cache bit (1 << 19) on 3.10–3.12,
    # measured by both seats; none is drift (round 17's check read each as drift, through __flags__)
    ("a bare lookup", "Site.fire"),
    ("an instance created and used", "_r18_probe = Site('r18.probe')\n_r18_probe.site_id"),
    ("hasattr of a missing name", "hasattr(Site, 'no_such_member')"),
]


@pytest.mark.parametrize("cell,line", _R18_NEUTRAL, ids=[c[0] for c in _R18_NEUTRAL])
def test_r18_a_behaviour_neutral_use_after_the_class_is_not_drift(cell, line):
    """The acceptance half of the __flags__ comparison: EXACTLY the attribute-cache bit is masked."""
    un = _load("inv7_uninstrument_r18l", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    assert un.site_drift(_r17_after(line)(ref), ref) == [], cell


def test_r18_the_abstract_flag_is_not_masked():
    """...and ONLY that bit: `Site.__abstractmethods__ = …` sets IS_ABSTRACT (1 << 20), which is semantic — Site can no
    longer be instantiated — and must read as drift, on route B, with the __flags__ field among what it reports."""
    un = _load("inv7_uninstrument_r18ab", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    head = _r17_after("Site.__abstractmethods__ = frozenset({'fire'})")(ref)
    b = un._realized_drift(head, ref)
    assert any(x.startswith("Site.__flags__ ") for x in b), b
    assert un._definition_drift(head, ref) == []


def test_r18_a_census_entry_with_no_python_caller_is_counted(monkeypatch):
    """`back is None` — a census entry reached with no Python caller (from C, or a thread's first frame) — was DROPPED
    by the census-entry hook, so it read as no entry at all. It is counted now; the gate requires 0."""
    obs = _load("inv7_observer_r18", EVIDENCE / "inv7_observer.py")
    monkeypatch.setattr(obs, "_CENSUS_ENTRIES", {})
    monkeypatch.setattr(obs, "_kind_of", lambda filename: "census")
    code = compile("def consult(): pass", "census.py", "exec").co_consts[0]
    frame = type("F", (), {"f_code": code, "f_back": None})()
    obs._census_profile(frame, "call", None)
    assert obs._CENSUS_ENTRIES == {("consult", "<no Python caller>", "<no Python caller>"): 1}


# ---- round 18: the ROUND-17 VERDICT — function-object metadata, and one recursive rule ---------------------------------
# The verdict: route B's function normaliser omitted the function objects' own writable fields. Its witness pairs each
# change with `Site.__doc__ = Site.__doc__`, a type setattr that CLEARS the attribute-cache bit, so no incidental __flags__
# difference can catch it. Every value is now described by ONE recursive rule (every data descriptor, read-only included,
# normalised recursively; exclusions named by property), so a staticmethod's inner function and a closure's cells are
# covered without a case of their own.
_R18_RESET = "\nSite.__doc__ = Site.__doc__"
_R18_STATIC = ("    def failure_kinds(self) -> dict:", "    @staticmethod\n    def _probe():\n        return 1\n\n    def failure_kinds(self) -> dict:")
_R18_V17_CELLS = [
    ("the verdict's witness: Site.fire.__name__", None, _r17_after('Site.fire.__name__ = "changed"' + _R18_RESET), "B"),
    ("the verdict's witness: Site.fire.__qualname__", None, _r17_after('Site.fire.__qualname__ = "changed"' + _R18_RESET), "B"),
    ("the verdict's witness: Site.fire.__module__", None, _r17_after('Site.fire.__module__ = "changed"' + _R18_RESET), "B"),
    ("a function's __type_params__ (its descriptor on 3.12+, its __dict__ before)", None,
     _r17_after("import typing as _typing\nSite.fire.__type_params__ = (_typing.TypeVar('T'),)" + _R18_RESET), "B"),
    ("a staticmethod's inner function renamed through its read-only __func__",
     lambda s: s.replace(*_R18_STATIC, 1),
     _r17_after('Site.__dict__["_probe"].__func__.__name__ = "renamed"' + _R18_RESET), "B"),
    ("a closure cell's contents changed after the class", _r17_after(_R18_MAKER),
     _r17_after("Site.extra.__closure__[0].cell_contents = 2" + _R18_RESET), "B"),
    # N-9 (the second seat's round-18 stage 2, RM4): a back-reference is recorded by the POSITION of the object it
    # repeats, and that position is load-bearing only when one object recurs INSIDE one value — each attribute is
    # described separately, so two swapped attributes are told apart by content alone. Here a container repeats an
    # alias, and the repeat points back to a DIFFERENT earlier object; positionless references read the two alike.
    ("a repeated alias pointing back to a different object", _r17_after("Site._aliases = (Site.fire, Site.consult, Site.fire)"),
     lambda s: s.replace("(Site.fire, Site.consult, Site.fire)", "(Site.fire, Site.consult, Site.consult)", 1), "B"),
]


@pytest.mark.parametrize("cell,prepare,edit,routes", _R18_V17_CELLS, ids=[c[0] for c in _R18_V17_CELLS])
def test_r18_function_metadata_is_compared_by_one_recursive_rule(cell, prepare, edit, routes, tmp_path):
    """The round-17 verdict's class, each cell asserting the verdict first (site_drift, which the round-17 pin has)."""
    test_r17_site_drift_reads_the_definition_and_the_realized_class(cell, prepare, edit, routes, tmp_path)


def test_r18_a_census_helper_outside_site_is_not_drift():
    """The acceptance half of the NAMESPACE exclusion: a change to a module-level census helper a Site method calls is
    census code UNDER TEST — the reference arm does not carry it, so the trace diff sees any decision it changes — and
    must not read as Site drift, though every Site method's __globals__ holds the changed helper."""
    un = _load("inv7_uninstrument_r18h", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    head = ref.replace('    return "decision"\n', '    return "a decision"\n', 1)
    assert head != ref
    assert un.site_drift(head, ref) == []


def test_r18_the_function_fields_compared_are_derived_per_interpreter():
    """The fields the rule reads off a function, DERIVED from the function type (every data descriptor along its MRO, minus
    the named namespace references): pinned per interpreter, so a Python that adds a field shows here, not silently."""
    import types
    un = _load("inv7_uninstrument_r18f", EVIDENCE / "inv7_uninstrument.py")
    got = set(un._data_descriptors(types.FunctionType)) - set(un._NAMESPACE_REFS)
    want = {"__annotations__", "__closure__", "__code__", "__defaults__", "__dict__", "__doc__", "__kwdefaults__",
            "__module__", "__name__", "__qualname__"} | ({"__type_params__"} if sys.version_info >= (3, 12) else set()) \
        | ({"__annotate__"} if sys.version_info >= (3, 14) else set())     # PEP 649: lazy annotations (B1)
    assert got == want, (sys.version_info[:2], sorted(got ^ want))


# ---- round 19: the ROUND-18 VERDICT — identity, not names --------------------------------------------------------------
# The verdict: `class tuple(tuple)` overriding __contains__, rebound as Site.__slots__ and the name deleted, read as the
# built-in tuple on both routes, in derive(), verify() and the runtime gate. The normaliser trusted CLAIMS — isinstance(),
# `__module__ == "builtins"`, a qualname — and every one can be made by Python code. A type is now described by name only
# when Py_TPFLAGS_IMMUTABLETYPE is set (Python code cannot create such a type, nor write its name); every other type is
# described in full, and a subclass's content is read through the immutable base's own methods.
_R19_WITNESS = ("class tuple(tuple):\n    def __contains__(self, item):\n        return False\n"
                "Site.__slots__ = tuple(Site.__slots__)\ndel tuple")
_R19_SPOOF = _R19_WITNESS.replace("class tuple(tuple):\n", "class tuple(tuple):\n    __module__ = 'builtins'\n    __qualname__ = 'tuple'\n", 1)
_R19_CELLS = [
    ("the verdict's witness: a tuple subclass named tuple as Site.__slots__", None, _r17_after(_R19_WITNESS), "B"),
    ("the spoof: the subclass also claims module builtins and qualname tuple", None, _r17_after(_R19_SPOOF), "B"),
    ("a str subclass NAMED str with an overriding __eq__, where T holds a real str", _r17_after("Site.label = 'x'"),
     lambda s: s.replace("Site.label = 'x'", "class str(str):\n    def __eq__(self, o):\n        return True\n    __hash__ = str.__hash__\nSite.label = str('x')\ndel str", 1), "B"),
    ("an int subclass NAMED int, where T holds a real int", _r17_after("Site.limit = 3"),
     lambda s: s.replace("Site.limit = 3", "class int(int):\n    pass\nSite.limit = int(3)\ndel int", 1), "B"),
    ("a dict subclass NAMED dict overriding get, where T holds a real dict", _r17_after("Site.table = {'a': 1}"),
     lambda s: s.replace("Site.table = {'a': 1}", "class dict(dict):\n    def get(self, k, d=None):\n        return 0\nSite.table = dict({'a': 1})\ndel dict", 1), "B"),
]


@pytest.mark.parametrize("cell,prepare,edit,routes", _R19_CELLS, ids=[c[0] for c in _R19_CELLS])
def test_r19_a_subclass_is_never_read_as_the_builtin_it_names(cell, prepare, edit, routes, tmp_path):
    """The round-18 verdict's class, each cell asserting the verdict first (site_drift, which the round-18 pin has)."""
    test_r17_site_drift_reads_the_definition_and_the_realized_class(cell, prepare, edit, routes, tmp_path)


def test_r19_an_equal_real_builtin_is_not_drift():
    """The acceptance half: Site.__slots__ rebound to an EQUAL real tuple is the same class — not drift."""
    un = _load("inv7_uninstrument_r19a", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    assert un.site_drift(_r17_after("Site.__slots__ = tuple(Site.__slots__)")(ref), ref) == []


def test_r19_the_immutable_criterion_per_interpreter():
    """The one property the rule trusts, pinned on this interpreter: set on the built-ins route B meets and on C types
    (heap ones included), CLEAR on every class Python code makes — the spoof, a plain class, a metaclass-built one — and
    an immutable type's name cannot be written."""
    import re as _re
    import threading
    import types
    un = _load("inv7_uninstrument_r19i", EVIDENCE / "inv7_uninstrument.py")

    class _Spoof(tuple):
        __module__ = "builtins"; __qualname__ = "tuple"

    class _Meta(type):
        pass
    for tp in (tuple, list, dict, str, int, type, object, types.FunctionType, types.CellType, types.MappingProxyType,
               types.CodeType, type(threading.Lock()), _re.Pattern):
        assert un._immutable(tp), tp
    for tp in (_Spoof, type("_Plain", (), {}), _Meta("_Built", (), {})):
        assert not un._immutable(tp), tp
    with pytest.raises(TypeError):
        tuple.__qualname__ = "not tuple"


def test_r19_the_runtime_gate_reads_the_witness_and_the_spoof_as_different():
    """The runtime gate digests site_description in each arm; the verdict says it accepted the witness. Read the way the
    observer reads it — the Site each census builds, described and digested — the witness and the spoof now differ from
    T's."""
    un = _load("inv7_uninstrument_r19g", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    digest = lambda text: un.site_description_digest(un.site_description(un._realized_site(text, "_x")))["digest"]
    for body in (_R19_WITNESS, _R19_SPOOF):
        assert digest(_r17_after(body)(ref)) != digest(ref), body[:40]


def test_r19_a_census_rebinding_a_builtin_cannot_reach_the_transform(tmp_path):
    """The second seat's stage-1 read: route B used to exec each census INSIDE the transform, so `import builtins;
    builtins.tuple = …` in HEAD's census rebound the transform's own built-ins (a __builtins__ copy does not isolate —
    `import builtins` returns the real module). It now runs in an isolated interpreter: the transform's built-ins are
    untouched, and derive() and verify() behave exactly as without the line."""
    import builtins
    un = _load("inv7_uninstrument_r19b", EVIDENCE / "inv7_uninstrument.py")
    real = builtins.tuple
    ref = un.REFERENCE_CENSUS.read_text()
    polluting = _r17_after("import builtins as _b\n_b.tuple = list")(ref)
    try:
        assert un.site_drift(polluting, ref) == []
        assert builtins.tuple is real, "the census rebound the TRANSFORM's built-ins"
        for tag, census_text in (("clean", ref), ("polluting", polluting)):
            src = _r13_pkg(tmp_path, tag, _R14_SELF + "def f():\n    return 1\n", "")
            (src / "census.py").write_text(census_text)
            out = tmp_path / tag / "twin" / "vpkg"
            un.derive(src, out)
            assert un.verify(out, src) == [], tag
            assert builtins.tuple is real, tag
    finally:
        builtins.tuple = real


_R19_SHIPPED_FLAGS = '_ROUTE_B_FLAGS = ("-P", "-s", "-B")'   # round 33: `-I` became `-P -s` under `_isolated_env`; then one constant
# the two superseded forms, each the mutant of one caller: `-I` alone (the round-19 fix as first committed to the
# working tree), and the caller's `-B` passed on conditionally (the first fix, which the second seat's stage-1 read
# showed misses a caller whose caches are redirected)
_R19_BARE = '_ROUTE_B_FLAGS = ("-P", "-s")'
_R19_CONDITIONAL = '_ROUTE_B_FLAGS = ("-P", "-s", *(["-B"] if sys.flags.dont_write_bytecode else []))'


@pytest.mark.parametrize("caller,form,expect_written", [
    ("-B", "shipped", False), ("-B", "bare -I", True),
    ("PYTHONPYCACHEPREFIX", "shipped", False), ("PYTHONPYCACHEPREFIX", "conditional -B", True)])
def test_r19_the_isolated_child_never_writes_bytecode(caller, form, expect_written, tmp_path):
    """Found by the round-19 stage's untouched-tree check: `-I` drops every PYTHON* variable — PYTHONDONTWRITEBYTECODE
    and PYTHONPYCACHEPREFIX among them — and a child does not inherit `-B`, so route B's child wrote caches into the
    evidence directory of a transform run with bytecode OFF, or with its caches REDIRECTED. The child now never writes
    bytecode. Each cell runs one caller over a fresh copy of the evidence directory. For each caller the shipped module
    writes nothing there, and the superseded form that caller defeats DOES write — so neither half is vacuous, and the
    prefix caller separates the shipped form from the conditional one (the second seat's stage-1 read)."""
    probe = ("import importlib.util, sys\n"
             "s = importlib.util.spec_from_file_location('u', sys.argv[1]); m = importlib.util.module_from_spec(s)\n"
             "sys.modules['u'] = m; s.loader.exec_module(m)\n"
             "ref = m.REFERENCE_CENSUS.read_text(); assert m.site_drift(ref, ref) == []\n")
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")}
    argv = [sys.executable]
    if caller == "-B":
        argv.append("-B")
    else:
        env["PYTHONPYCACHEPREFIX"] = str(tmp_path / "prefix")      # the caller's OWN caches go there, not beside the code
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    if form != "shipped":
        text = (ev / "inv7_uninstrument.py").read_text()
        assert text.count(_R19_SHIPPED_FLAGS) == 1, "the mutant's anchor moved"
        (ev / "inv7_uninstrument.py").write_text(
            text.replace(_R19_SHIPPED_FLAGS, _R19_BARE if form == "bare -I" else _R19_CONDITIONAL))
    r = subprocess.run(argv + ["-c", probe, str(ev / "inv7_uninstrument.py")],
                       capture_output=True, text=True, env=env, timeout=300)
    assert r.returncode == 0, (caller, form, r.stderr[-500:])
    written = sorted(str(q.relative_to(ev)) for q in ev.rglob("*.pyc"))
    assert bool(written) is expect_written, (caller, form, written)


# ---- round 20: the ROUND-19 VERDICT'S F1 — census output across the isolated child's boundary ------------------------
# Round 19 returned the child's description on stdout, which the census shares, so `print("census initialized")` made
# derive() and verify() raise a bare JSONDecodeError. The response now travels in a file the child owns, and the child
# ends with os._exit(0) once it is written. Each cell is a suffix appended to the reference census, run through derive()
# AND verify(): "accept" means no census problem at all; "refuse" means a NAMED failure ("could not be described"), never
# a bare exception; "drift" means the named drift survives the output. The exit-path cells are the second seat's round-20
# stage-1 read, each executed there at the round-19 pin.
_R20_REAL_DRIFT = '\nSite.fire.__name__ = "changed"\nSite.__doc__ = Site.__doc__\n'
_R20_F1_CELLS = [
    ("no suffix", "", "accept"),
    ("print()", "\nprint()\n", "accept"),
    ("a banner on stdout", '\nprint("census initialized")\n', "accept"),
    ('print("null")', '\nprint("null")\n', "accept"),
    ("sys.stdout.write without a newline", '\nimport sys as _s\n_s.stdout.write("census initialized")\n', "accept"),
    ("stdout text that looks like the response", "\nprint('[[\"mro\", \"x\"]]')\n", "accept"),
    ("a banner on stderr", '\nimport sys as _s\n_s.stderr.write("census initialized\\n")\n', "accept"),
    ("sys.stdout closed", "\nimport sys as _s\n_s.stdout.close()\n", "accept"),
    ("file descriptor 1 closed", "\nimport os as _o\n_o.close(1)\n", "accept"),
    ("an atexit hook that prints", "\nimport atexit as _a\n_a.register(print, 'bye')\n", "accept"),
    ("an atexit hook that exits 3", "\nimport atexit as _a, os as _o\n_a.register(_o._exit, 3)\n", "accept"),
    ("a non-daemon thread still running", "\nimport threading as _t, time as _tm\n_t.Thread(target=_tm.sleep, args=(600,)).start()\n", "accept"),
    ("a daemon thread still running", "\nimport threading as _t, time as _tm\n_t.Thread(target=_tm.sleep, args=(600,), daemon=True).start()\n", "accept"),
    ("the working directory changed", "\nimport os as _o\n_o.chdir('/')\n", "accept"),
    ("os._exit(0) during import", "\nimport os as _o\n_o._exit(0)\n", "refuse"),
    ("sys.exit(3) during import", "\nimport sys as _s\n_s.exit(3)\n", "refuse"),
    ("an exception during import", "\nraise RuntimeError('census failed')\n", "refuse"),
    ("real drift, silent", _R20_REAL_DRIFT, "drift"),
    ("real drift with a banner on stdout", _R20_REAL_DRIFT + 'print("census initialized")\n', "drift"),
]


@pytest.mark.parametrize("cell,suffix,expect", _R20_F1_CELLS, ids=[c[0] for c in _R20_F1_CELLS])
def test_r20_census_output_never_reaches_the_isolated_child_s_response(cell, suffix, expect, tmp_path, monkeypatch):
    """The verdict's matrix and the second seat's exit paths, through derive() and through an independently invoked
    verify() over a valid twin whose manifest carries the edited census's source hash (the reviewer's own setup, so a
    problem here is never a manifest mismatch)."""
    un = _load("inv7_uninstrument_r20f1", EVIDENCE / "inv7_uninstrument.py")
    # raising=False: the matrix reaches the defect through names the round-19 pin also has, so there every cell fails
    # on the transport itself (a bare JSONDecodeError), not on this round's budget constant.
    # 60 s, not the 8 s of the never-ends cell below: every cell here FINISHES, so the budget only caps a regression
    # that hangs. Measured under the two-phase suite's -n 8 phase (five runs, 2026-11-14..16): a whole cell, four
    # children included, took at most 3.44 s. The external reviewer's full concurrent offline run (0031 round 3)
    # took one child past 8 s, and the same selections passed alone; 60 s is about 17x the worst cell measured here.
    monkeypatch.setattr(un, "_ISOLATION_TIMEOUT", 60, raising=False)
    ref = un.REFERENCE_CENSUS.read_text()
    head = ref + suffix
    # derive() over the edited census
    src = _r13_pkg(tmp_path, "derive", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(head)
    out = tmp_path / "derive" / "twin" / "vpkg"
    if expect == "accept":
        un.derive(src, out)
    else:
        with pytest.raises(un.Refused, match="could not be described" if expect == "refuse" else r"Site\.fire \(realized\)") as e:
            un.derive(src, out)
        assert "JSONDecodeError" not in str(e.value), (cell, str(e.value)[:300])
        if expect == "refuse":        # the second seat's stage-2 read: a census that cannot be described has not DRIFTED
            assert "T must advance" not in str(e.value) and "drifted" not in str(e.value), (cell, str(e.value)[:300])
    # verify() over a clean twin, the source census then edited and its hash carried into the manifest
    src = _r13_pkg(tmp_path, "verify", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(ref)
    out = tmp_path / "verify" / "twin" / "vpkg"
    un.derive(src, out)
    (src / "census.py").write_text(head)
    man_path = out.parent / "twin_manifest.json"
    man = json.loads(man_path.read_text())
    man["modules"]["census.py"]["sha256_before"] = hashlib.sha256(head.encode()).hexdigest()
    man_path.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    problems = [p for p in un.verify(out, src) if p.startswith("census.py")]
    if expect == "accept":
        assert problems == [], (cell, problems)
    elif expect == "refuse":
        assert problems and all("could not be described" in p and "T must advance" not in p for p in problems), (cell, problems)
    else:
        assert any("Site.fire (realized)" in p and "T must advance" in p for p in problems), (cell, problems)


def test_r20_a_census_whose_import_never_ends_is_a_named_failure(tmp_path, monkeypatch):
    """The second seat's stage-1 cell: a census whose import never finishes. The child's budget (lowered here) ends it,
    and derive() refuses by name — never a bare TimeoutExpired. A cell of its own because it needs the budget constant
    this round introduced (the round-19 pin hard-coded 300s)."""
    un = _load("inv7_uninstrument_r20f1t", EVIDENCE / "inv7_uninstrument.py")
    monkeypatch.setattr(un, "_ISOLATION_TIMEOUT", 8)
    ref = un.REFERENCE_CENSUS.read_text()
    src = _r13_pkg(tmp_path, "slow", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(ref + "\nwhile True:\n    pass\n")
    with pytest.raises(un.Refused, match="did not finish within 8s"):
        un.derive(src, tmp_path / "slow" / "twin" / "vpkg")


def test_r20_an_undescribable_census_is_never_reported_as_drift(tmp_path):
    """The second seat's stage-2 read of c6b2620: a census that crashes on import was refused as "HEAD's Site has
    drifted … — T must advance", which is false twice over — Site did not drift, and advancing T is a specification
    change nobody should make for a crash. Route B's could-not-describe is a refusal of its own on EITHER side, never
    a drift entry; and the wrapping it replaced is the mutant, which must misreport the crash."""
    un = _load("inv7_uninstrument_r20u", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text()
    crash = "\nraise RuntimeError('census failed')\n"
    for head, reference, who in ((ref + crash, ref, "HEAD's census"), (ref, ref + crash, "the reference census")):
        with pytest.raises(un.Refused, match=f"{who} could not be described") as e:
            un.site_drift(head, reference)
        assert "T must advance" not in str(e.value) and "not drift" in str(e.value), str(e.value)[:300]
    text = (EVIDENCE / "inv7_uninstrument.py").read_text()
    shipped = ('            raise SiteUndescribed(f"{label} census could not be described in an isolated interpreter — this is not "\n'
               '                                  f"drift, and T does not advance: {d}")')
    assert text.count(shipped) == 1, "the mutant's anchor moved"
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(
        shipped, '            return [f"Site: {label} census could not be described in an isolated interpreter — {d}"]'))
    mut = _load("inv7_uninstrument_r20u_mut", ev / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "mut", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(ref + crash)
    with pytest.raises(mut.Refused) as e:
        mut.derive(src, tmp_path / "mut" / "twin" / "vpkg")
    assert "T must advance" in str(e.value), "the superseded wrapping no longer misreports a crash — the mutant is not killed"


# The superseded forms, each substituted at an anchor that must match once, and the cell that kills it.
_R20_F1_MUTANTS = [
    ("the response on stdout (round 19's transport)",
     [('with open_(response, "w", encoding="ascii") as f:\n    f.write(body); f.flush()\n', "sys.stdout.write(body); sys.stdout.flush()\n"),
      ('body = response.read_text(encoding="ascii") if response.exists() else None', "body = r.stdout")],
     '\nprint("census initialized")\n'),
    ("no final os._exit", [("exit_(0)                                             #", "pass                                                 #")],
     "\nimport threading as _t, time as _tm\n_t.Thread(target=_tm.sleep, args=(600,)).start()\n"),
    ("the timeout left uncaught", [("        except subprocess.TimeoutExpired:\n", "        except ZeroDivisionError:\n")],
     "\nwhile True:\n    pass\n"),
]


@pytest.mark.parametrize("mutant,subs,killer", _R20_F1_MUTANTS, ids=[m[0] for m in _R20_F1_MUTANTS])
def test_r20_each_superseded_transport_fails_its_cell(mutant, subs, killer, tmp_path):
    """Each mutant must MISREAD its killing cell — a spurious refusal or a bare exception where the shipped module reads
    no drift — or the matrix above is not the thing that holds the fix in place."""
    text = (EVIDENCE / "inv7_uninstrument.py").read_text()
    for a, b in subs:
        assert text.count(a) == 1, (mutant, "the anchor moved", a[:60])
        text = text.replace(a, b)
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text)
    mut = _load("inv7_uninstrument_r20f1_mut", ev / "inv7_uninstrument.py")
    mut._ISOLATION_TIMEOUT = 8
    ref = mut.REFERENCE_CENSUS.read_text()
    try:
        found = mut.site_drift(ref + killer, ref)
    except Exception as e:                                       # a bare exception is the defect's own symptom
        found = [f"raised {type(e).__name__}"]
    assert found, (mutant, "the mutant read the killing cell as no drift — it is not killed")


# ---- round 20: the ROUND-19 VERDICT'S F2, end to end — a valid helper beside a measured decision must DERIVE -----------
# The verdict put `(x for x in a if [__class__ for __class__ in b] and super), (y for y in b)` in a temporary product
# module beside an ordinary site and the shipped derive() raised UnresolvableScope. The signature cells live in
# tests/test_0042_scope_resolution.py; these are the derivation controls: each helper derives, and the twin verifies.
_R20_F2_HELPERS = [
    ("the verdict's witness", "def h(a, b):\n    return (x for x in a if [__class__ for __class__ in b] and super), (y for y in b)\n"),
    ("a method calling super(C, self)",
     "class C:\n    def m(self, a, b):\n        return (x for x in a if [__class__ for __class__ in b] and super(C, self)), (y for y in b)\n"),
    ("a class-private inner target", "class C:\n    def m(self, a, b):\n        return (x for x in a if [__p for __p in b]), (y for y in b)\n"),
    ("same-line lambdas with a class-private parameter", "class C:\n    def m(self):\n        return (lambda __p: __p), (lambda q: q)\n"),
]


@pytest.mark.parametrize("cell,helper", _R20_F2_HELPERS, ids=[c[0] for c in _R20_F2_HELPERS])
def test_r20_a_valid_helper_beside_a_measured_decision_derives(cell, helper, tmp_path):
    un = _load("inv7_uninstrument_r20f2", EVIDENCE / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "f2", _R14_SELF + "def f():\n    return 1\n\n\n" + helper, "")
    (src / "census.py").write_text(un.REFERENCE_CENSUS.read_text())
    out = tmp_path / "f2" / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == [], cell


# ---- round 21: the ROUND-20 VERDICT'S F1 — the isolated child's boundary is BYTES, and the transform reads UTF-8 --------
# Round 20 moved the description to a file the child owns, but the parent still captured the census's stdout and stderr
# with text=True, so a census writing bytes that are not UTF-8 made derive() and verify() raise UnicodeDecodeError
# although the description was valid; and the census text went in, and verify() read files, in the LOCALE's encoding.
_R21_BAD = "\nimport sys as _s\n_s.{stream}.buffer.write(b'\\xff\\xfe census\\n'); _s.{stream}.flush()\n"
_R21_F1_CELLS = [
    ("invalid UTF-8 on stdout", _R21_BAD.format(stream="stdout"), "accept"),
    ("invalid UTF-8 on stderr", _R21_BAD.format(stream="stderr"), "accept"),
    ("invalid UTF-8 on both", _R21_BAD.format(stream="stdout") + _R21_BAD.format(stream="stderr"), "accept"),
    ("valid non-ASCII on stdout", "\nprint('census µ é 中')\n", "accept"),
    ("a non-ASCII comment in the census", "\n# census µ é 中\n", "accept"),
    ("real drift with invalid UTF-8 on stdout", _R20_REAL_DRIFT + _R21_BAD.format(stream="stdout"), "drift"),
    # on stdout, so the escaped bytes survive in the failure's detail (stderr's tail is the traceback, kept to 200 chars)
    ("a crash after invalid UTF-8 on stdout", _R21_BAD.format(stream="stdout") + "raise RuntimeError('census failed')\n", "refuse"),
]


def _r21_verify_problems(un, tmp_path, head):
    """verify() over a clean twin, the source census then edited and its hash carried into the manifest."""
    ref = un.REFERENCE_CENSUS.read_text(encoding="utf-8")
    src = _r13_pkg(tmp_path, "verify", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(ref, encoding="utf-8")
    out = tmp_path / "verify" / "twin" / "vpkg"
    un.derive(src, out)
    (src / "census.py").write_text(head, encoding="utf-8")
    man_path = out.parent / "twin_manifest.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["modules"]["census.py"]["sha256_before"] = hashlib.sha256(head.encode("utf-8")).hexdigest()
    man_path.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return [p for p in un.verify(out, src) if p.startswith("census.py")]


@pytest.mark.parametrize("cell,suffix,expect", _R21_F1_CELLS, ids=[c[0] for c in _R21_F1_CELLS])
def test_r21_census_bytes_never_break_the_isolated_boundary(cell, suffix, expect, tmp_path):
    """The verdict's F1 and its class, through derive() AND verify(): whatever bytes the census writes, a valid
    description is authoritative; a failure is named, its bytes backslash-escaped; real drift keeps its name."""
    un = _load("inv7_uninstrument_r21f1", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text(encoding="utf-8")
    head = ref + suffix
    src = _r13_pkg(tmp_path, "derive", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(head, encoding="utf-8")
    out = tmp_path / "derive" / "twin" / "vpkg"
    if expect == "accept":
        un.derive(src, out)
    else:
        with pytest.raises(un.Refused) as e:
            un.derive(src, out)
        msg = str(e.value)
        assert "UnicodeDecodeError" not in msg, (cell, msg[:300])
        if expect == "refuse":
            assert "could not be described" in msg and "T must advance" not in msg and "\\xff" in msg, (cell, msg[:400])
        else:
            assert "Site.fire (realized)" in msg and "T must advance" in msg, (cell, msg[:300])
    problems = _r21_verify_problems(un, tmp_path, head)
    if expect == "accept":
        assert problems == [], (cell, problems)
    elif expect == "refuse":
        assert problems and all("could not be described" in p and "T must advance" not in p for p in problems), (cell, problems)
    else:
        assert any("Site.fire (realized)" in p and "T must advance" in p for p in problems), (cell, problems)


# The locale cell: derive() and verify() in a child whose locale encoding is NOT UTF-8, over a census holding non-ASCII
# (the reference census's own em dash, and a comment). The child FIRST asserts its encoding is not UTF-8 and fails
# loudly otherwise — PEP 538 coerces LANG=C and LC_CTYPE=C to UTF-8, so a cell that merely set them would pass vacuously
# (the second seat's measurement); LC_ALL=C with UTF-8 mode off gives ASCII.
_R21_LOCALE_CHILD = r"""
import importlib.util, locale, pathlib, sys
enc = locale.getpreferredencoding(False)
if enc.replace("-", "").lower() in ("utf8",):
    print(f"LOCALE CELL VACUOUS: the child's encoding is {enc}, not a non-UTF-8 one"); sys.exit(3)
s = importlib.util.spec_from_file_location("un", sys.argv[1]); un = importlib.util.module_from_spec(s)
sys.modules["un"] = un; s.loader.exec_module(un)
src, out = pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
un.derive(src, out)
problems = un.verify(out, src)
print(f"encoding {enc}; verify {problems!r}")
sys.exit(0 if problems == [] else 4)
"""
_R21_LOCALE_MUTANTS = [
    ("shipped", None, None),
    ("the census text sent in the locale's encoding", 'input=census_text.encode("utf-8")',
     'input=census_text.encode(__import__("locale").getpreferredencoding(False))'),
    ("verify reading the census in the locale's encoding",
     "site_drift(_read_source(src / rel), _read_source(p_out))",
     "site_drift((src / rel).read_text(), p_out.read_text())"),
]


@pytest.mark.parametrize("form,anchor,replacement", _R21_LOCALE_MUTANTS, ids=[m[0] for m in _R21_LOCALE_MUTANTS])
def test_r21_derive_and_verify_hold_under_a_non_utf8_locale(form, anchor, replacement, tmp_path):
    module = EVIDENCE / "inv7_uninstrument.py"
    if anchor is not None:
        ev = tmp_path / "evidence"
        shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
        text = (ev / "inv7_uninstrument.py").read_text(encoding="utf-8")
        assert text.count(anchor) == 1, (form, "the mutant's anchor moved")
        (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, replacement), encoding="utf-8")
        module = ev / "inv7_uninstrument.py"
    un = _load("inv7_uninstrument_r21loc", EVIDENCE / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "loc", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_text(un.REFERENCE_CENSUS.read_text(encoding="utf-8") + "\n# census µ é\n", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("LC_", "LANG", "PYTHONUTF8", "PYTHONIOENCODING"))}
    env["LC_ALL"] = "C"
    r = subprocess.run([sys.executable, "-X", "utf8=0", "-B", "-c", _R21_LOCALE_CHILD, str(module), str(src),
                        str(tmp_path / "loc" / "twin" / "vpkg")], capture_output=True, env=env, timeout=600)
    shown = (r.stdout + r.stderr).decode("utf-8", errors="backslashreplace")
    assert r.returncode != 3, shown[-400:]                    # the cell itself must be non-vacuous, never skipped
    if anchor is None:
        assert r.returncode == 0, shown[-800:]
    else:
        assert r.returncode != 0, (form, "the mutant held under a non-UTF-8 locale — it is not killed", shown[-400:])


def test_r21_decoding_the_census_output_on_success_fails_the_byte_cells(tmp_path):
    """The round-20 capture's behaviour as a mutant: the census's output decoded (strictly) on every run. It must
    fail the invalid-stdout cell that the shipped boundary accepts."""
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    anchor = '    context = f"exit {r.returncode}; stderr: {shown(r.stderr)!r}; stdout: {shown(r.stdout)!r}"'
    assert text.count(anchor) == 1, "the mutant's anchor moved"
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(
        text.replace(anchor, '    r.stdout.decode("utf-8"); r.stderr.decode("utf-8")\n' + anchor), encoding="utf-8")
    mut = _load("inv7_uninstrument_r21dec", ev / "inv7_uninstrument.py")
    ref = mut.REFERENCE_CENSUS.read_text(encoding="utf-8")
    with pytest.raises(UnicodeDecodeError):
        mut.site_drift(ref + _R21_BAD.format(stream="stdout"), ref)


def _r21_text_io_violations(source: str) -> list:
    """Every call that reads or writes TEXT in the locale's encoding: read_text/write_text without encoding=, open()
    in text mode without encoding=, a subprocess run with text=True (or universal_newlines=True), and a read or write
    on sys.stdin/stdout/stderr themselves rather than their .buffer. Returns [(line, description)]."""
    out = []
    for n in ast.walk(ast.parse(source)):
        if not isinstance(n, ast.Call):
            continue
        kw = {k.arg for k in n.keywords}
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in ("read_text", "write_text") and "encoding" not in kw:
            out.append((n.lineno, f"{name}() without encoding="))
        elif name in ("open", "open_") and "encoding" not in kw:
            mode = n.args[1].value if len(n.args) > 1 and isinstance(n.args[1], ast.Constant) else next(
                (k.value.value for k in n.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)), "r")
            if "b" not in str(mode):
                out.append((n.lineno, f"{name}() in text mode without encoding="))
        elif name in ("run", "Popen", "check_output", "check_call") and any(
                k.arg in ("text", "universal_newlines") and isinstance(k.value, ast.Constant) and k.value.value
                for k in n.keywords):
            out.append((n.lineno, f"subprocess {name}(text=True)"))
        elif name in ("read", "readline", "write") and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Attribute) \
                and isinstance(f.value.value, ast.Name) and f.value.value.id == "sys" and f.value.attr in ("stdin", "stdout", "stderr"):
            out.append((n.lineno, f"sys.{f.value.attr}.{name}() on the text stream"))
    return out


# The functions whose ROLE is a text boundary; the gate refuses a decode, an encode or a text read/write anywhere else in
# the transform (the second seat's stage-1b read: a source read spelled `read_text(encoding="utf-8")` assumes an encoding
# the source declares for itself, and a gate that only asks for SOME encoding blesses it).
_R21_BOUNDARY_FUNCTIONS = {"_source_encoding", "_source_text", "_read_source", "_write_source", "_read_data", "_write_data",
                           "_described_in_isolation",
                           # round 31: the backed-field probe child's channel, route B's rules — bytes in and out, its
                           # ASCII JSON answer decoded strictly, stderr decoded only to NAME a failure
                           "_prime_in_child",
                           # encodes its OWN repr to hash it: an in-memory digest, never I/O, and str.encode() is UTF-8
                           # whatever the locale
                           "site_description_digest"}


def _r21_boundary_violations(source: str) -> list:
    """Every decode/encode/read_text/write_text/open() call OUTSIDE a boundary function, by the innermost enclosing
    def — plus the locale-default forms anywhere (_r21_text_io_violations)."""
    tree = ast.parse(source)
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    def owners(line):
        return {f.name for f in funcs if f.lineno <= line <= f.end_lineno}
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in ("decode", "encode", "read_text", "write_text", "open") and not owners(n.lineno) & _R21_BOUNDARY_FUNCTIONS:
            out.append((n.lineno, f"{name}() outside a text-boundary function ({sorted(owners(n.lineno)) or ['<module>']})"))
    return out


def test_r21_the_transform_reads_and_writes_text_only_at_its_boundaries():
    """The class guard (round-21 stage 1 and 1b), derived from the AST rather than a hand list — two hand counts of
    these calls were short in one exchange. SCOPE, stated: inv7_uninstrument.py (the transform: derive and verify),
    including the isolated child's source, which the module carries as a string and runs. Two rules: nothing reads or
    writes text in the locale's encoding, and nothing decodes, encodes or reads/writes text OUTSIDE the named boundary
    functions — so a Python source is decoded only by `_source_text` (its own declared encoding) and never by an
    assumed one. OUTSIDE THE SCOPE, named: the INV-7 harness and observer and the other evidence modules read and write
    in the locale's encoding (queued)."""
    un = _load("inv7_uninstrument_r21ast", EVIDENCE / "inv7_uninstrument.py")
    source = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    found = [("module", *v) for v in _r21_text_io_violations(source) + _r21_boundary_violations(source)]
    child = [v for v in _r21_text_io_violations(un._ISOLATED_CHILD)]
    child += [(ln, why) for ln, why in _r21_boundary_violations(un._ISOLATED_CHILD)
              if not (why.startswith("decode()") and 'sys.stdin.buffer.read().decode("utf-8")' in un._ISOLATED_CHILD.splitlines()[ln - 1])
              and not why.startswith("open()")]                       # the child's one decode is OUR utf-8 transport
    found += [("_ISOLATED_CHILD", *v) for v in child]
    # and the one decode of a SOURCE is STRICT (the 3.14 floor, B2): round 21 required an error handler because 3.10-3.13
    # ran a byte invalid in its declared encoding inside a comment; 3.14's tokenizer refuses that byte, so after the
    # bytes-parse accepts a source nothing is left for a handler to repair, and a handler could only hide a disagreement
    tree = ast.parse(source)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_source_text")
    decodes = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "decode"]
    if not (decodes and not any(any(k.arg == "errors" for k in c.keywords) for c in decodes)):
        found.append(("module", fn.lineno, "_source_text decodes with an error handler, or not at all"))
    assert found == [], found


def test_r21_the_boundary_gate_flags_a_utf8_assuming_source_read():
    """The gate's own mutant: the form the second seat showed it blessing — a source read in verify() spelled
    read_text(encoding="utf-8") — must be flagged."""
    source = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    anchor = "site_drift(_read_source(src / rel), _read_source(p_out))"
    assert source.count(anchor) == 1, "the mutant's anchor moved"
    mutated = source.replace(anchor, 'site_drift((src / rel).read_text(encoding="utf-8"), p_out.read_text(encoding="utf-8"))')
    flagged = [v for v in _r21_boundary_violations(mutated) if "read_text" in v[1]]
    assert len(flagged) == 2, flagged


# A Python SOURCE declares its own encoding (PEP 263, a BOM). Each cell writes a census or a product module in a declared
# encoding and runs derive() and verify(); a product module's twin must also RUN as its source does.
_R21_COOKIE = "# -*- coding: {enc} -*-\n"
_R21_SOURCE_CELLS = [
    ("census: the reference, UTF-8 BOM", "census", lambda ref: b"\xef\xbb\xbf" + ref, "accept"),
    ("census: the reference re-encoded gb18030, with its cookie", "census",
     lambda ref: _R21_COOKIE.format(enc="gb18030").encode() + ref.decode("utf-8").encode("gb18030"), "accept"),
    ("census: a utf-8 cookie line", "census", lambda ref: _R21_COOKIE.format(enc="utf-8").encode() + ref, "accept"),
    ("census: a latin-1 cookie over UTF-8 bytes (the census's strings REALLY change: drift)", "census",
     lambda ref: _R21_COOKIE.format(enc="latin-1").encode() + ref + "\n# café\n".encode("latin-1"), "drift"),
    ("product: latin-1 cookie, a latin-1 string", "product",
     lambda _: _R21_COOKIE.format(enc="latin-1").encode() + (_R14_SELF + "def f():\n    return 'café'\n").encode("latin-1"), "accept"),
    ("product: cp1252 cookie, a cp1252 string (the cookie is lost in the twin)", "product",
     lambda _: _R21_COOKIE.format(enc="cp1252").encode() + (_R14_SELF + "def f():\n    return '— café'\n").encode("cp1252"), "accept"),
    ("product: UTF-8 BOM, a non-ASCII string", "product",
     lambda _: b"\xef\xbb\xbf" + (_R14_SELF + "def f():\n    return 'µ 中'\n").encode("utf-8"), "accept"),
    # the second seat's stage-1c read: a byte invalid in the declared encoding was VALID PYTHON inside a comment on
    # 3.10-3.13, and 3.14's tokenizer REFUSES it (B2): each cell's expectation below is therefore re-derived from the
    # running interpreter (_r21_expect), never assumed; an unknown cookie is not Python on any version
    ("census: a trailing comment holding an invalid UTF-8 byte", "census", lambda ref: ref + b"\n# \xff comment\n", "accept"),
    ("census: a utf-8 cookie and a comment holding an invalid byte", "census",
     lambda ref: _R21_COOKIE.format(enc="utf-8").encode() + ref + b"\n# \xff\n", "accept"),
    ("census: an invalid comment byte and REAL drift", "census",
     lambda ref: ref + b"\n# \xff\n" + _R20_REAL_DRIFT.encode(), "drift"),
    ("census: an unknown coding cookie (not Python: a named refusal)", "census",
     lambda ref: _R21_COOKIE.format(enc="nonexistent").encode() + ref, "refuse"),
    ("product: a comment holding an invalid UTF-8 byte", "product",
     lambda _: (_R14_SELF + "def f():\n    return 'x'\n").encode() + b"# \xff\n", "accept"),
    # the second seat's round-21 stage 2 (V3): the bytes-parse is what makes "a bad byte can only be in a comment" true;
    # outside one, the source is not Python, and a census Python cannot compile must not be silently transformed
    ("census: an invalid byte in a string literal (not Python: a named refusal)", "census",
     lambda ref: ref + b"\nX_EXTRA = '\xff'\n", "refuse"),
    ("product: an invalid byte in a string literal (not Python: a named refusal)", "product",
     lambda _: (_R14_SELF + "def f():\n    return 'x'\n").encode() + b"S2 = '\xff'\n", "refuse"),
]


def _r21_expect(expect, make, un):
    """The cell's stated expectation, unless the RUNNING interpreter refuses the bytes the cell writes — then a named
    refusal, whatever the cell says (3.14 refuses an invalid byte in a comment, which 3.10-3.13 accepted: B2)."""
    data = make(un.REFERENCE_CENSUS.read_bytes())
    try:
        compile(data, "<r21-expect>", "exec", dont_inherit=True)
    except (SyntaxError, ValueError):
        return "refuse"
    return expect


def _r21_source_cell(un, tmp_path, kind, make):
    ref = un.REFERENCE_CENSUS.read_bytes()
    src = _r13_pkg(tmp_path, "enc", _R14_SELF + "def f():\n    return 1\n", "")
    (src / "census.py").write_bytes(make(ref) if kind == "census" else ref)
    if kind == "product":
        (src / "b.py").write_bytes(make(ref))
    return src, tmp_path / "enc" / "twin" / "vpkg"


@pytest.mark.parametrize("cell,kind,make,expect", _R21_SOURCE_CELLS, ids=[c[0] for c in _R21_SOURCE_CELLS])
def test_r21_a_source_is_read_in_the_encoding_it_declares(cell, kind, make, expect, tmp_path):
    un = _load("inv7_uninstrument_r21src", EVIDENCE / "inv7_uninstrument.py")
    src, out = _r21_source_cell(un, tmp_path, kind, make)
    expect = _r21_expect(expect, make, un)
    if expect == "drift":
        with pytest.raises(un.Refused, match="T must advance"):
            un.derive(src, out)
        return
    if expect == "refuse":
        with pytest.raises(un.Refused, match="could not be read as Python source") as e:
            un.derive(src, out)
        assert "T must advance" not in str(e.value) and "not drift" in str(e.value), str(e.value)[:300]
        return
    _r21_holds(un, src, out, kind, cell)


def _r21_holds(un, src, out, kind, cell):
    """derive() and verify() clean, every twin file compiles, and a product twin RUNS as its source does."""
    un.derive(src, out)
    assert un.verify(out, src) == [], cell
    for p in out.rglob("*.py"):
        compile(p.read_bytes(), str(p), "exec")                      # the twin declares what it is
    if kind == "product":
        runs = [subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(root)!r}); import vpkg.b as b; "
                                "print(ascii(b.f()))"], capture_output=True, text=True, encoding="utf-8") for root in (src.parent, out.parent)]
        assert [r.returncode for r in runs] == [0, 0], [r.stderr[-300:] for r in runs]
        assert runs[0].stdout == runs[1].stdout, (cell, runs[0].stdout, runs[1].stdout)


_R21_CP1252 = "product: cp1252 cookie, a cp1252 string (the cookie is lost in the twin)"


@pytest.mark.parametrize("mutant,anchor,replacement,killer", [
    ("a source decoded as UTF-8, whatever it declares", '        text = data.decode(encoding)',
     '        text = data.decode("utf-8", errors="replace")', _R21_CP1252),
    ("the twin written in the ORIGINAL's encoding", '    data = text.encode(_source_encoding(text.encode("utf-8")))',
     '    data = text.encode("cp1252")', _R21_CP1252),
    # RETIRED at the 3.14 floor: "a source decoded strictly (no error handler)" was round 21's mutant of the lenient
    # decode. Strict decoding IS the rule now (B2), and its converse — errors="replace" — is EQUIVALENT on 3.14: the
    # bytes-parse refuses every source holding a byte invalid in its declared encoding before the decode is reached.
    ("an unreadable source raising bare", '        raise SourceUnreadable(f"{label} could not be read as Python source',
     '        raise\n        raise SourceUnreadable(f"{label} could not be read as Python source',
     "census: an unknown coding cookie (not Python: a named refusal)"),
    # round 22 made the bytes-parse also the interpreter's side of the guard, so the V3 form is now "parse the decoded
    # text in its place": no BYTE-level validation at all
    ("the bytes-parse removed (stage 2's V3)", "        from_bytes = ast.parse(data, filename=label)\n",
     '        from_bytes = ast.parse(data.decode(_source_encoding(data), errors="replace"), filename=label)\n',
     "census: an invalid byte in a string literal (not Python: a named refusal)"),
], ids=["decode as utf-8", "write in the original's encoding", "bare on an unknown cookie", "bytes-parse removed"])
def test_r21_each_superseded_source_rule_fails_a_cell(mutant, anchor, replacement, killer, tmp_path):
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    assert text.count(anchor) == 1, (mutant, "the anchor moved")
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, replacement), encoding="utf-8")
    mut = _load("inv7_uninstrument_r21srcmut", ev / "inv7_uninstrument.py")
    _, kind, make, expect = {c[0]: c for c in _R21_SOURCE_CELLS}[killer]
    src, out = _r21_source_cell(mut, tmp_path, kind, make)
    expect = _r21_expect(expect, make, mut)
    try:
        if expect == "refuse":
            with pytest.raises(mut.Refused, match="could not be read as Python source"):
                mut.derive(src, out)
        else:
            _r21_holds(mut, src, out, kind, killer)
    except BaseException as e:                                   # the cell no longer holds under the mutant: killed
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        return
    pytest.fail(f"{mutant}: the killing cell still holds — the mutant is not killed")


# ---- round 21: a line ABOVE Site is not drift on any version (CI's 3.13 lane, on the first round-21 commit) ---------
# 3.13 stores the class statement's first line in vars() as __firstlineno__, which route B and the runtime gate read, so
# a comment or blank line above Site refused on 3.13 alone — from round 18 to round 21, unseen because no cell shifted
# the lines ABOVE the class (the formatting cell added them inside and after it).
_R21_ABOVE = [("a comment above everything", lambda r: "# a comment\n" + r),
              ("blank lines above everything", lambda r: "\n\n\n" + r),
              ("a comment right above class Site", lambda r: r.replace("class Site", "# a comment\nclass Site", 1))]


@pytest.mark.parametrize("cell,edit", _R21_ABOVE, ids=[c[0] for c in _R21_ABOVE])
def test_r21_a_line_above_site_is_not_drift_on_any_version(cell, edit):
    un = _load("inv7_uninstrument_r21above", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text(encoding="utf-8")
    head = edit(ref)
    assert head != ref and head.count("class Site") == ref.count("class Site"), cell
    assert un.site_drift(head, ref) == [], cell


def test_r21_the_class_location_exclusion_is_load_bearing_on_313(tmp_path):
    """The exclusion's mutant: without it, a comment above Site is drift — on 3.13 and later, where the field exists."""
    if sys.version_info < (3, 13):
        pytest.skip("__firstlineno__ is stored in a class's vars() from 3.13; before it the exclusion excludes nothing")
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    anchor = '_CLASS_LOCATION = ("__firstlineno__",)'
    assert text.count(anchor) == 1, "the mutant's anchor moved"
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, "_CLASS_LOCATION = ()"), encoding="utf-8")
    mut = _load("inv7_uninstrument_r21abovemut", ev / "inv7_uninstrument.py")
    ref = mut.REFERENCE_CENSUS.read_text(encoding="utf-8")
    assert mut.site_drift("# a comment\n" + ref, ref), "the mutant read a line shift as no drift on 3.13 — not killed"


# ---- round 22: the ROUND-21 VERDICT — a source's ENCODING HEADER, read as the interpreter reads it --------------------
# Round 21 found the coding cookie with tokenize.detect_encoding and called it "the interpreter's rule"; it decodes lines
# 1-2 as UTF-8 first, and refused valid Python whose header comments hold bytes in the declared encoding (or an invalid
# byte), which CPython's own tokenizer accepts. The cookie is now found at the byte level AND every reading is checked
# against the interpreter's: the syntax tree of our text must equal the one parsed from the bytes. The oracle for the
# corpus below is the interpreter itself — compile(bytes) — never our reading of PEP 263.
_R22_LITERALS = {"utf-8": "中 é", "latin-1": "café", "cp1252": "— café", "gb18030": "中 é"}


def _r22_corpus():
    """Programs crossing: line 1 (absent, blank, a shebang, an ASCII comment, a comment in the declared encoding, a
    comment holding an invalid UTF-8 byte, a line of CODE) x the cookie's form (none, emacs, vim, emacs with mode, plain
    `coding=` with trailing non-ASCII) x the declared encoding x the BODY's encoding (the declared one, or UTF-8 whatever
    the cookie says) x a BOM. The body holds a non-ASCII string literal."""
    out = []
    forms = {"none": None, "emacs": "# -*- coding: {e} -*-", "vim": "# vim: set fileencoding={e} :",
             "emacs+mode": "# -*- mode: python; coding: {e} -*-", "coding= + text": "# coding={e} é"}
    for enc, lit in _R22_LITERALS.items():
        for l1 in ("absent", "blank", "shebang", "ascii comment", "comment in enc", "invalid-utf8 comment", "code"):
            for form, cookie in forms.items():
                for body_enc in (enc, "utf-8"):
                    for bom in (False, True):
                        def enc_line(s, e):
                            try:
                                return s.encode(e)
                            except UnicodeEncodeError:
                                return None
                        head = []
                        if l1 != "absent":
                            head.append({"blank": b"\n", "shebang": b"#!/usr/bin/env python\n", "ascii comment": b"# a comment\n",
                                         "comment in enc": enc_line("# é comment\n", enc), "invalid-utf8 comment": b"# \xff comment\n",
                                         "code": b"x0 = 0\n"}[l1])
                        if cookie is not None:
                            head.append(enc_line(cookie.format(e=enc) + "\n", enc))
                        body = enc_line(f"S = {lit!r}\n", body_enc)
                        if None in head or body is None:
                            continue
                        data = (b"\xef\xbb\xbf" if bom else b"") + b"".join(head) + body
                        out.append((f"{enc}/{l1}/{form}/body {body_enc}/{'BOM' if bom else 'no BOM'}", data))
    return out


def _r22_interpreter(data):
    """The oracle: does CPython compile these bytes, and if so, what is S?"""
    try:
        code = compile(data, "<r22>", "exec", dont_inherit=True)
    except (SyntaxError, ValueError):
        return False, None
    ns = {}
    exec(code, ns)
    return True, ns["S"]


def _r22_disagreements(un):
    bad = []
    for label, data in _r22_corpus():
        ok, value = _r22_interpreter(data)
        try:
            text = un._source_text(data, label)
            ours_ok, ours = True, None
            ns = {}
            exec(compile(text, "<r22-text>", "exec", dont_inherit=True), ns)
            ours = ns["S"]
        except un.Refused:
            ours_ok = False
        if ok != ours_ok or (ok and value != ours):
            bad.append((label, ok, ours_ok))
    return bad


def test_r22_the_source_reader_agrees_with_the_interpreter_over_the_header_corpus():
    """For every program: we accept exactly what CPython compiles, and read its literal as CPython does."""
    un = _load("inv7_uninstrument_r22", EVIDENCE / "inv7_uninstrument.py")
    corpus = _r22_corpus()
    accepted = sum(_r22_interpreter(d)[0] for _, d in corpus)
    assert len(corpus) >= 500 and accepted >= 100 and len(corpus) - accepted >= 100, (len(corpus), accepted)
    bad = _r22_disagreements(un)
    assert bad == [], bad[:8]


_R22_PRODUCT = _R14_SELF + "def f():\n    return {lit!r}\n"
_R22_CELLS = [
    ("product: a latin-1 comment on line 1, a latin-1 cookie on line 2",
     lambda _: "# café\n".encode("latin-1") + b"# -*- coding: latin-1 -*-\n" + _R22_PRODUCT.format(lit="café").encode("latin-1")),
    ("product: a shebang, then a cookie followed by latin-1 text",
     lambda _: b"#!/usr/bin/env python\n" + "# -*- coding: latin-1 -*- café\n".encode("latin-1") + _R22_PRODUCT.format(lit="café").encode("latin-1")),
    ("product: a cp1252 comment above a cp1252 cookie",
     lambda _: "# — café\n".encode("cp1252") + b"# coding: cp1252\n" + _R22_PRODUCT.format(lit="—").encode("cp1252")),
    ("product: an invalid UTF-8 byte in a line-1 comment",
     lambda _: b"# \xff\n" + _R22_PRODUCT.format(lit="é").encode("utf-8")),
    ("census: the reference, a gb18030 comment above its gb18030 cookie",
     lambda ref: "# 中文\n".encode("gb18030") + b"# coding: gb18030\n" + ref.decode("utf-8").encode("gb18030")),
    ("census: the reference, an invalid UTF-8 byte in a line-1 comment", lambda ref: b"# \xff\n" + ref),
]


@pytest.mark.parametrize("cell,make", _R22_CELLS, ids=[c[0] for c in _R22_CELLS])
def test_r22_a_header_the_interpreter_accepts_derives_and_verifies(cell, make, tmp_path):
    """The verdict's class through derive() and verify(); a product twin RUNS as its source does. A header the RUNNING
    interpreter refuses (3.14 refuses an invalid byte in a line-1 comment, which 3.10-3.13 ran: B2) is a named refusal."""
    un = _load("inv7_uninstrument_r22cells", EVIDENCE / "inv7_uninstrument.py")
    kind = "census" if cell.startswith("census") else "product"
    src, out = _r21_source_cell(un, tmp_path, kind, make)
    if _r21_expect("accept", make, un) == "refuse":
        with pytest.raises(un.SourceUnreadable, match="could not be read as Python source"):
            un.derive(src, out)
        return
    _r21_holds(un, src, out, kind, cell)


def test_r22_the_interpreter_guard_fires_on_a_wrong_reading(monkeypatch):
    """The guard's control (the second seat's stage-1 addition): force a WRONG encoding on a UTF-8 source holding a
    non-ASCII literal, and the reading must be refused by name — the guard shown to fire, not only to pass."""
    un = _load("inv7_uninstrument_r22guard", EVIDENCE / "inv7_uninstrument.py")
    data = "S = 'café'\n".encode("utf-8")
    assert un._source_text(data, "m.py") == "S = 'café'\n"
    monkeypatch.setattr(un, "_source_encoding", lambda d: "latin-1")
    with pytest.raises(un.SourceUnreadable, match="disagrees with the interpreter"):
        un._source_text(data, "m.py")


def test_r22_the_interpreter_guard_fires_on_a_wrong_utf8_reading(monkeypatch):
    """The mirror of the control above (the second seat's round-22 stage 2, W6): a source wrongly read as UTF-8 — what
    a MISSED cookie produces, since UTF-8 is the fallback — must be refused by name too. A latin-1-declared source
    holding a non-ASCII literal, with _source_encoding forced to "utf-8"."""
    un = _load("inv7_uninstrument_r22guard8", EVIDENCE / "inv7_uninstrument.py")
    # latin-1 "Ã©" is the bytes C3 A9, which are ALSO valid UTF-8 ("é"): under the strict decode (the 3.14 floor) a
    # wrong UTF-8 reading of plain latin-1 fails at the decode before the guard; these bytes reach the guard
    data = b"# -*- coding: latin-1 -*-\n" + "S = 'caf\u00c3\u00a9'\n".encode("latin-1")
    assert "caf\u00c3\u00a9" in un._source_text(data, "m.py")
    monkeypatch.setattr(un, "_source_encoding", lambda d: "utf-8")
    with pytest.raises(un.SourceUnreadable, match="disagrees with the interpreter"):
        un._source_text(data, "m.py")


def test_r22_the_guard_skipped_for_utf8_readings_fails_the_mirror_cell(tmp_path, monkeypatch):
    """W6 as a mutant, anchored on a line OTHER than the guard's (the second seat's note: two mutant tests anchored on
    one line mask each other in a campaign): return before the guard whenever the reading is UTF-8."""
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    anchor = "        from_text = ast.parse(text, filename=label)\n"
    assert text.count(anchor) == 1, "the mutant's anchor moved"
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(
        text.replace(anchor, anchor + '        if encoding.startswith("utf-8"):\n            return text\n'), encoding="utf-8")
    mut = _load("inv7_uninstrument_r22w6", ev / "inv7_uninstrument.py")
    monkeypatch.setattr(mut, "_source_encoding", lambda d: "utf-8")
    # latin-1 "Ã©" is the bytes C3 A9, which are ALSO valid UTF-8 ("é"): under the strict decode (the 3.14 floor) a
    # wrong UTF-8 reading of plain latin-1 fails at the decode before the guard; these bytes reach the guard
    data = b"# -*- coding: latin-1 -*-\n" + "S = 'caf\u00c3\u00a9'\n".encode("latin-1")
    assert "caf\u00c3\u00a9" not in mut._source_text(data, "m.py"), "the mutant refused the wrong UTF-8 reading — not killed"


_R22_MUTANTS = [
    ("round 21's detect_encoding", "def _source_encoding(data: bytes) -> str:\n",
     "def _source_encoding(data: bytes) -> str:\n    import io, tokenize\n    return tokenize.detect_encoding(io.BytesIO(data).readline)[0]\n\n\ndef _unused_(data: bytes) -> str:\n"),
    ("line 2 examined after a line of code", "        if i == 0 and not _BLANK_OR_COMMENT.match(line):\n            break\n", ""),
    ("the interpreter guard removed", "    if ast.dump(from_bytes, include_attributes=True) != ast.dump(from_text, include_attributes=True):\n",
     "    if False:\n"),
]


# "round 21's detect_encoding" is RETIRED as a mutant at the 3.14 floor, with its measured reason: on 3.14.7 it agrees
# with the interpreter on all 560 programs of the header corpus (3.12.3: 466, disagreeing on 94), because 3.14's C
# tokenizer now refuses the non-UTF-8 header bytes the pure-Python one refused. It stays the round-23 set control's
# reader (_R22_MUTANTS[0]), where it still separates: it must agree on the folded names.
_R22_MUTANTS_AT_THE_FLOOR = [m for m in _R22_MUTANTS if m[0] != "round 21's detect_encoding"]


@pytest.mark.parametrize("mutant,anchor,replacement", _R22_MUTANTS_AT_THE_FLOOR, ids=[m[0] for m in _R22_MUTANTS_AT_THE_FLOOR])
def test_r22_each_superseded_reading_fails(mutant, anchor, replacement, tmp_path, monkeypatch):
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    assert text.count(anchor) == 1, (mutant, "the anchor moved")
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, replacement), encoding="utf-8")
    mut = _load("inv7_uninstrument_r22mut", ev / "inv7_uninstrument.py")
    if mutant == "the interpreter guard removed":             # killed by the guard's control: a wrong reading passes
        monkeypatch.setattr(mut, "_source_encoding", lambda d: "latin-1")
        assert mut._source_text("S = 'café'\n".encode("utf-8"), "m.py") != "S = 'café'\n"
        return
    assert _r22_disagreements(mut), (mutant, "the mutant agrees with the interpreter over the corpus — it is not killed")


def test_r22_the_transform_never_uses_tokenize_detect_encoding():
    """The superseded rule may not come back (the second seat's stage-1 addition, c)."""
    tree = ast.parse((EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8"))
    found = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr == "detect_encoding"]
    found += [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "detect_encoding"]
    assert found == [], found


# ---- round 23 (the round-22 verdict): a cookie's NAME is read as the interpreter normalises it -----------------------
# Round 22's byte-level reader looked a cookie's name up as written; the interpreter first folds every spelling of UTF-8
# and Latin-1 onto one name (`utf-8-unix`, `iso-latin-1`), so valid sources were refused. Round 22's corpus varied the
# header's STRUCTURE over a hand list of four canonical names; the NAME is a grammar of its own. Its domain is DERIVED
# here from both halves of the rule: every name the codecs know (encodings.aliases), and every spelling of the
# families the tokenizer folds. The interpreter judges each, with and without a BOM, in BOTH directions.
_R23_TAILS = ("", "-x", "-unix", "_dos", ".y", "x", "-something-very-long-tail")
_R23_BOUNDARY_ACCEPTED = ("ISO-LATIN-1-UNIX", "UTF-8-UNIX-LONGNAME", "Iso_Latin_1_Dos", "iso-latin-1-",
                          "LATIN-1-SOMETHING-VERY-LONG", "iso-8859-1_mac", "Utf-8-Emacs", "UTF_8", "utf8")
_R23_BOUNDARY_REFUSED = ("iso-latin-1x", "utf-8x")


def _r23_names():
    import encodings.aliases
    names = set(_R23_BOUNDARY_ACCEPTED) | set(_R23_BOUNDARY_REFUSED)
    for b in set(encodings.aliases.aliases) | set(encodings.aliases.aliases.values()):     # what the codecs know
        for v in (b, b.replace("_", "-"), b.upper(), b.replace("_", "-").upper()):
            names.update(v + tail for tail in _R23_TAILS[:5])
    for fam in ("utf-8", "latin-1", "iso-8859-1", "iso-latin-1"):                          # what the tokenizer folds
        for sep in ("-", "_"):
            base = fam.replace("-", sep)
            for tail in _R23_TAILS:
                for v in (base + tail, (base + tail).upper(), (base + tail).title(), base.upper() + tail.swapcase()):
                    names.add(v)
    return sorted(names)


def _r23_program(name, bom):
    """A cookie naming `name`, and a literal in whatever the interpreter will read it as (ASCII when that is unknown)."""
    import codecs, tokenize
    try:
        codec = "utf-8" if bom else codecs.lookup(tokenize._get_normal_name(name)).name
        body = "S = 'café'\n".encode(codec)
    except (LookupError, UnicodeError, TypeError):
        body = b"S = 'abc'\n"
    return (b"\xef\xbb\xbf" if bom else b"") + f"# -*- coding: {name} -*-\n".encode("ascii") + body


def _r23_cells(un):
    """(name, bom) -> (interpreter accepts, we accept, the two read S alike)."""
    out = {}
    for name in _r23_names():
        for bom in (False, True):
            data = _r23_program(name, bom)
            ok, value = _r22_interpreter(data)
            try:
                ns = {}
                exec(compile(un._source_text(data, name), "<r23-text>", "exec", dont_inherit=True), ns)
                ours_ok, same = True, ok and ns["S"] == value
            except un.Refused:
                ours_ok, same = False, False
            out[(name, bom)] = (ok, ours_ok, same)
    return out


def _r23_disagreements(un):
    return sorted(k for k, (ok, ours, same) in _r23_cells(un).items() if ok != ours or (ok and not same))


def test_r23_the_source_reader_agrees_with_the_interpreter_over_every_cookie_name():
    """Accept exactly what CPython compiles, in both directions, reading the literal as CPython does — over every name
    the codecs know and every spelling the tokenizer folds, each with and without a BOM. Every cell is populated."""
    un = _load("inv7_uninstrument_r23", EVIDENCE / "inv7_uninstrument.py")
    cells = _r23_cells(un)
    grid = collections.Counter((ok, bom) for (_, bom), (ok, _, _) in cells.items())
    assert min(grid.get((ok, bom), 0) for ok in (True, False) for bom in (True, False)) >= 20, grid
    assert _r23_disagreements(un) == []
    for name in _R23_BOUNDARY_ACCEPTED:
        assert cells[(name, False)][:2] == (True, True), name
    for name in _R23_BOUNDARY_REFUSED:
        assert cells[(name, False)][:2] == (False, False), name
    assert cells[("utf8", True)][:2] == (False, False)                  # a BOM is compared by the NORMAL name


def test_r23_the_normaliser_is_the_interpreters_over_the_name_domain():
    """Secondary to the interpreter (which judges above): the mirror equals the stdlib's copy of the C rule, name by name."""
    import tokenize
    un = _load("inv7_uninstrument_r23norm", EVIDENCE / "inv7_uninstrument.py")
    assert [n for n in _r23_names() if un._normal_name(n) != tokenize._get_normal_name(n)] == []


def _r23_mutant(tmp_path, anchor, replacement, tag):
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    assert text.count(anchor) == 1, (tag, "the anchor moved")
    ev = tmp_path / tag
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, replacement), encoding="utf-8")
    return _load(f"inv7_uninstrument_r23_{tag}", ev / "inv7_uninstrument.py")


# round 22's reader, as it was: the name looked up as written, and a BOM compared by the codec's name
_R23_ROUND_22 = ('            name = _normal_name(m.group(1).decode("ascii"))\n            codecs.lookup(name)\n'
                 '            if bom and name != "utf-8":\n',
                 '            name = m.group(1).decode("ascii")\n            codecs.lookup(name)\n'
                 '            if bom and codecs.lookup(name).name != "utf-8":\n')


def test_r23_the_controls_are_sets_round_22_fails_exactly_the_folded_names_round_21_passes_them(tmp_path):
    """Round 22's reader (the normaliser removed) must fail on EXACTLY the names the interpreter accepts and the codecs
    do not know as written — the verdict's class, by name, derived — and round 21's detect_encoding must pass them."""
    import codecs
    def unknown(n):
        try:
            codecs.lookup(n)
            return False
        except LookupError:
            return True
    un = _load("inv7_uninstrument_r23ctl", EVIDENCE / "inv7_uninstrument.py")
    cells = _r23_cells(un)
    expected = sorted(k for k, (ok, _, _) in cells.items() if ok and unknown(k[0]))
    assert ("iso-latin-1", False) in expected and ("utf-8-unix", False) in expected, "the verdict's witnesses"
    r22 = _r23_mutant(tmp_path, *_R23_ROUND_22, "r22")
    assert _r23_disagreements(r22) == expected
    r21 = _r23_mutant(tmp_path, *_R22_MUTANTS[0][1:], "r21")
    assert [k for k in _r23_disagreements(r21) if k in set(expected)] == []


_R23_MUTANTS = [
    ("no lower-casing", "    s = s.lower()\n", ""),
    ("no _ read as -", '    s = s.replace("_", "-")\n', ""),
    ("no utf-8- prefix", '            s.startswith("utf-8-"):\n', "            False:\n"),
    ("no latin-1 prefixes", '            s.startswith(("latin-1-", "iso-8859-1-", "iso-latin-1-")):\n', "            False:\n"),
    ("the folded name returned", "    return name                                        #", "    return s  #"),
]


@pytest.mark.parametrize("mutant,anchor,replacement", _R23_MUTANTS, ids=[m[0] for m in _R23_MUTANTS])
def test_r23_each_step_of_the_normaliser_is_load_bearing(mutant, anchor, replacement, tmp_path):
    mut = _r23_mutant(tmp_path, anchor, replacement, "m")
    assert _r23_disagreements(mut), (mutant, "the mutant agrees with the interpreter over every name — not killed")


def _r23_bom_disagreements(un):
    """The BOM rule at its OWN site: behind _source_text the interpreter refuses a bad BOM first and masks it. For
    every name with a BOM, _source_encoding refuses exactly when the interpreter does."""
    bad = []
    for name in _r23_names():
        data = _r23_program(name, True)
        try:
            un._source_encoding(data)
            ours = True
        except (SyntaxError, LookupError):
            ours = False
        if ours != _r22_interpreter(data)[0]:
            bad.append(name)
    return bad


def test_r23_a_bom_is_compared_by_the_normal_name_at_its_own_site(tmp_path):
    un = _load("inv7_uninstrument_r23bom", EVIDENCE / "inv7_uninstrument.py")
    assert _r23_bom_disagreements(un) == []
    mut = _r23_mutant(tmp_path, '            if bom and name != "utf-8":\n',
                      '            if bom and codecs.lookup(name).name != "utf-8":\n', "bom")
    assert "utf8" in _r23_bom_disagreements(mut), "a BOM compared by the codec's name is not killed"


def test_r23_the_twelve_character_cut_is_an_equivalent_mutant(tmp_path):
    """Shown by running, not asserted: every exact name the rule matches is shorter than 12 characters and the longest
    prefix it matches (`iso-latin-1-`) is exactly 12, so reading the whole name changes no verdict over the domain."""
    mut = _r23_mutant(tmp_path, "    s = name[:12]\n", "    s = name\n", "cut")
    assert _r23_disagreements(mut) == []


def test_r23_a_refusal_after_the_interpreter_accepts_is_named_a_disagreement(monkeypatch):
    """The refusal direction (the verdict's second gap): once the interpreter has accepted the bytes, a failure of the
    transform's reading says so — never that the source is not Python. And a source the interpreter refuses keeps
    its own refusal, without the disagreement's words."""
    un = _load("inv7_uninstrument_r23dir", EVIDENCE / "inv7_uninstrument.py")
    with pytest.raises(un.SourceUnreadable, match="could not be read as Python source") as e:
        un._source_text(b"# coding: no-such-codec\nS = 1\n", "m.py")
    assert "interpreter accepts" not in str(e.value)
    def lookup_fails(data):
        raise LookupError("unknown encoding: forced")
    monkeypatch.setattr(un, "_source_encoding", lookup_fails)
    with pytest.raises(un.SourceUnreadable, match="the interpreter accepts this source and the transform cannot read it"):
        un._source_text(b"S = 1\n", "m.py")

# ---- Python 3.14 (the floor from 2026-09-27), B1: annotations are LAZY, and a describer must never run them ----------
# PEP 649: defining a class runs no annotation code, and READING __annotations__ calls __annotate__ — census code — so
# route B's describer executed the census in the reference arm (seven census entries, through _normalise). On a class,
# reading __annotations__ or __annotate__ also WRITES into vars(), and ANY code in the process can do that read.
_B1_CENSUS = """
CALLS = []
def side(x):
    CALLS.append(x)
    return x
class Base:
    base_kind: side("base class annotation")
class Site(Base):
    kind: side("class annotation")
    def fire(self, decision: side("parameter annotation")) -> side("return annotation"):
        return decision
"""
_B1_BARE = """
CALLS = []
class Site:
    def fire(self, decision):
        return decision
"""


def _b1_site(un, text, name):
    import types
    mod = types.ModuleType(name)
    # dont_inherit: this file's `from __future__ import annotations` would otherwise make every annotation a STRING, and
    # a string annotation runs nothing — the cells below could not fail (found by their own mutants, 2026-09-27)
    exec(compile(text, f"<{name}>", "exec", dont_inherit=True), mod.__dict__)
    if "side(" in text:
        # THE ACCEPTANCE HALF (the second seat's N1): the case this cell is named for must really be present — lazy,
        # unevaluated annotations — or the cell fails BY NAME rather than passing because nothing could run
        # the SHAPE, read from the annotate function's code and never by calling it: the lazy shape's names `side`;
        # the future-import shape's returns constant strings and names nothing (the second seat's precision)
        assert mod.Site.fire.__annotate__ is not None and callable(vars(mod.Site).get("__annotate_func__")) \
            and "side" in mod.Site.fire.__annotate__.__code__.co_names, \
            "the census compiled without lazy annotations: this cell cannot run the case it is named for"
        assert mod.CALLS == [], mod.CALLS
    return mod


def test_py314_describing_a_site_runs_no_annotation_code():
    """Annotations with side effects, on a method AND on the class: describing the class — and digesting it, as the
    observer does — runs none of them, on every interpreter (on <3.14 they ran once, at definition, which is before)."""
    un = _load("inv7_uninstrument_b1a", EVIDENCE / "inv7_uninstrument.py")
    mod = _b1_site(un, _B1_CENSUS, "b1a")
    before = list(mod.CALLS)
    un.site_description_digest(un.site_description(mod.Site))
    assert mod.CALLS == before, mod.CALLS


_B1_FUTURE = """from __future__ import annotations
class Site:
    kind: int
    def fire(self, decision: str) -> bool:
        return decision
"""


def test_py314_describing_a_future_import_site_runs_none_of_its_code():
    """THE REAL CENSUS'S SHAPE (the second seat's precision, 2026-09-27): census.py stringifies its annotations, and on
    3.14 its functions STILL carry a compiler-generated __annotate__ that returns those strings — calling it is a call
    into code compiled from census.py, and it is what the observer counted (7 entries through _normalise). Measured
    here by a profile hook counting calls into code compiled from the census's own filename while the class is
    described: zero. The shape is asserted from the annotate function's code — constant strings, no names."""
    import types as _types
    un = _load("inv7_uninstrument_b1f", EVIDENCE / "inv7_uninstrument.py")
    mod = _types.ModuleType("b1f")
    exec(compile(_B1_FUTURE, "<b1f-census>", "exec", dont_inherit=True), mod.__dict__)
    ann = mod.Site.fire.__annotate__
    assert ann is not None and ann.__code__.co_names == () and "str" in ann.__code__.co_consts, \
        "not the future-import shape: this cell cannot run the case it is named for"
    entered = []

    def hook(frame, event, arg):
        if event == "call" and frame.f_code.co_filename == "<b1f-census>":
            entered.append(frame.f_code.co_name)
    sys.setprofile(hook)
    try:
        un.site_description_digest(un.site_description(mod.Site))
    finally:
        sys.setprofile(None)
    assert entered == [], entered


def test_py314_describing_a_site_leaves_its_vars_unchanged():
    """The describer must not WRITE into what it describes: vars() has the same keys and values before and after one
    description, for a class with annotations, for one without (on 3.14 a read of an unannotated class's __annotate__
    alone inserts __annotate_func__), and for the mutable BASE route B describes beside Site."""
    un = _load("inv7_uninstrument_b1b", EVIDENCE / "inv7_uninstrument.py")
    for text in (_B1_CENSUS, _B1_BARE):
        mod = _b1_site(un, text, "b1b")
        classes = [c for c in mod.Site.__mro__ if c is not object]
        before = [dict(vars(c)) for c in classes]
        un.site_description(mod.Site)
        after = [dict(vars(c)) for c in classes]
        assert after == before, [sorted(set(a) ^ set(b)) for a, b in zip(after, before)]


def test_py314_another_reader_of_the_annotations_is_not_drift():
    """The second seat's cell: describe, read __annotations__ from OUTSIDE the describer (as typing.get_type_hints or the
    product would), describe again — the digests are equal, for a class with annotations and one without. Without the
    by-value normalisation of the keys that read creates, who read the class first would split the arms' digests."""
    un = _load("inv7_uninstrument_b1c", EVIDENCE / "inv7_uninstrument.py")
    for text in (_B1_CENSUS, _B1_BARE):
        mod = _b1_site(un, text, "b1c")
        first = un.site_description_digest(un.site_description(mod.Site))["digest"]
        mod.Site.__annotations__                                          # someone else's read
        mod.Site.fire.__annotations__
        assert un.site_description_digest(un.site_description(mod.Site))["digest"] == first, text[:40]


def test_py314_an_assigned_class_annotation_is_drift():
    """The second seat's round-24 stage 2, F1: on 3.14 `Site.__annotations__ = {...}` stores the value in
    `__annotations_cache__` ALONE and removes `__annotate_func__`, so the cache IS the annotations there. Two classes
    that differ only in what was ASSIGNED — to a bare class, or one value against another — must describe differently;
    the control (an annotated class against the same class assigned) stays different too."""
    import types as _types
    un = _load("inv7_uninstrument_f1", EVIDENCE / "inv7_uninstrument.py")

    def site(src, assign=None):
        m = _types.ModuleType("f1")
        exec(compile(src, "<f1>", "exec", dont_inherit=True), m.__dict__)
        if assign is not None:
            m.Site.__annotations__ = assign
        return un.site_description_digest(un.site_description(m.Site))["digest"]
    bare, annotated = "class Site:\n    def fire(self): pass\n", "class Site:\n    x: int\n    def fire(self): pass\n"
    assert site(bare) != site(bare, {"x": str}), "an annotation assigned to a bare class reads as no drift"
    assert site(bare, {"x": str}) != site(bare, {"x": bytes}), "two assigned annotations read as no drift"
    assert site(annotated) != site(annotated, {"x": str}), "the control: an assignment over declared annotations"


def test_py314_a_census_dict_carrying_an_annotation_key_is_still_compared():
    """The normalisation is scoped to CLASS NAMESPACES (the second seat's N2): an ordinary census dict that happens to
    carry `__annotations_cache__`, `__annotate_func__` None or `__annotations__` {} is data, and a change in it reads."""
    un = _load("inv7_uninstrument_b1d", EVIDENCE / "inv7_uninstrument.py")
    for key, a, b in (("__annotations_cache__", {"x": 1}, {"x": 2}), ("__annotate_func__", None, 0),
                      ("__annotations__", {}, {"y": 1})):
        assert un._normalise({key: a}, {}) != un._normalise({key: b}, {}), key
    # each READ-CREATED FORM against the empty mapping: in a class namespace they are the same, in census data they are
    # not — and only this comparison drops BOTH sides under an unscoped normalisation (the scoping mutant survived the
    # pairs above once F1 made the cache conditional)
    for form in ({"__annotations_cache__": {}}, {"__annotate_func__": None}, {"__annotations__": {}},
                 {"__annotate_func__": _R27_ANNOTATE, "__annotations_cache__": {"x": 1}}):
        # round 27: this was `len`, an incidental callable; a module-level builtin is refused now (its __self__ is the
        # builtins module, which fail-closed refuses), so a Python function stands in — the cell's subject is unchanged
        assert un._normalise(form, {}) != un._normalise({k: v for k, v in form.items() if k == "__annotate_func__" and v is _R27_ANNOTATE}, {}), form


def _R27_ANNOTATE():
    """A plain callable standing in as an annotate function (round 27: `len` is refused as a held builtin)."""


_B1_MUTANTS = [
    ("a function's lazy annotations read", "        if n == \"__annotations__\" and lazy:\n",
     "        if False:\n", test_py314_describing_a_site_runs_no_annotation_code),
    ("a function's lazy annotations read (the future-import shape)", "        if n == \"__annotations__\" and lazy:\n",
     "        if False:\n", test_py314_describing_a_future_import_site_runs_none_of_its_code),
    ("a class's annotation attributes read", "        if is_class and n in _LAZY_ANNOTATION:\n",
     "        if False:\n", test_py314_describing_a_site_leaves_its_vars_unchanged),
    ("the type-level annotation fields read",
     'if _is_data_descriptor(v) and n not in names and n != "__dict__" and n not in _LAZY_ANNOTATION:',
     'if _is_data_descriptor(v) and n not in names and n != "__dict__":',
     test_py314_describing_a_site_leaves_its_vars_unchanged),
    ("the read-created keys not normalised", '    return (k == "__annotate_func__" and x is None) or (k == "__annotations__" and type(x) is dict and not x)\n',
     "    return False\n", test_py314_another_reader_of_the_annotations_is_not_drift),
    ("the derived cache not dropped", '        return (type(x) is dict and not x) or callable(namespace.get("__annotate_func__"))\n',
     "        return False\n", test_py314_another_reader_of_the_annotations_is_not_drift),
    ("the cache dropped unconditionally (F1)", '        return (type(x) is dict and not x) or callable(namespace.get("__annotate_func__"))\n',
     "        return True\n", test_py314_an_assigned_class_annotation_is_drift),
    ("the normalisation applied to every mapping", "        ns = any(_read_created(k, v, obj) for k, v in obj.items()) and _is_class_namespace(obj)\n",
     "        ns = True\n", test_py314_a_census_dict_carrying_an_annotation_key_is_still_compared),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell", _B1_MUTANTS, ids=[m[0] for m in _B1_MUTANTS])
def test_py314_each_annotation_rule_is_load_bearing(mutant, anchor, replacement, cell, tmp_path, monkeypatch):
    mut = _r23_mutant(tmp_path, anchor, replacement, "b1m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    # round 28's guard stops census code before its first line and REFUSES the Site: without the rule the Site is either
    # described by running its code (the cell's assertion) or refused (the guard) — never described without running it
    try:
        cell()
    except AssertionError:
        pass
    except mut.SiteUndescribed as e:
        assert "would run code the describer did not write" in str(e), f"{mutant}: refused, but not by the guard: {e}"
    else:
        pytest.fail(f"{mutant}: the cell passed")

# ---- round 18, N-6: the Site each arm IMPORTED, compared at runtime --------------------------------------------------
# site_drift reads both censuses in the TRANSFORM's process, so a change to Site made after the class and CONDITIONAL on
# the arm's runtime state (its environment, what it imports) is seen by neither route. The observer now digests route B's
# description of the Site each run imported — right after `import veracium.census`, BEFORE the arm's own intervention —
# and the gate uninstrumented:site_realized_equal requires every run's digest (arms and controls) equal.
_R18_COND = ('\nif os.environ.get("INV7_ARM") == "healthy":\n    Site.__doc__ = "changed only in the healthy arm"\n')


def test_r18_site_realized_check_is_equal_missing_or_names_the_first_difference():
    harness = _load("inv7_harness_r18c", EVIDENCE / "inv7_harness.py")
    d = lambda digest, entries: {"site_realized": {"digest": digest, "entries": entries}}
    same = {"uninstrumented": d("aa", [["mro", "1"], ["vars.x", "2"]]), "healthy": d("aa", [["mro", "1"], ["vars.x", "2"]])}
    assert harness.site_realized_check(same) == {"runs": 2, "missing": [], "distinct_digests": 1, "equal": True, "first_difference": None}
    miss = dict(same, off={"site_realized": None})
    assert harness.site_realized_check(miss)["equal"] is False and harness.site_realized_check(miss)["missing"] == ["off"]
    diff = dict(same, healthy=d("bb", [["mro", "1"], ["vars.x", "3"]]))
    got = harness.site_realized_check(diff)
    assert got["equal"] is False and got["first_difference"] == {"run": "healthy", "entry": "vars.x"}, got


def test_r18_final_status_gates_on_the_site_realized_check():
    """The gate is WIRED: final_status names it, and it follows checks["site_realized"]["equal"]."""
    harness = _load("inv7_harness_r18g", EVIDENCE / "inv7_harness.py")
    for equal in (True, False):
        v = {"identical": True, "control": {}}
        checks = {"uninstrumented": {"census_enabled": False, "census_code_entries": 0}, "site_realized": {"equal": equal}}
        harness.final_status(v, checks, {"uninstrumented": {"pytest_exit": 0}}, ["uninstrumented"])
        assert v["gates"]["uninstrumented:site_realized_equal"] is equal, v["gates"]


def test_r18_the_failing_arm_changes_site_so_the_digest_is_taken_at_import():
    """The NEGATIVE control for WHERE the digest is taken: the failing arm replaces Site._bump by construction, so a
    session-end digest would differ in that arm on every run — the gate would be false on the unmutated tree."""
    un = _load("inv7_uninstrument_r18n", EVIDENCE / "inv7_uninstrument.py")
    S = un._realized_site(un.REFERENCE_CENSUS.read_text(), "_x")
    before = un.site_description_digest(un.site_description(S))["digest"]

    def boom(self, field):
        raise RuntimeError("INV-7 forced counter failure")
    S._bump = boom                                          # exactly what inv7_observer._arm_setup does in the failing arm
    assert un.site_description_digest(un.site_description(S))["digest"] != before


@pytest.fixture(scope="module")
def r18_trees(tmp_path_factory):
    """The source as is, and with a post-class change to Site CONDITIONAL on the arm's environment; a shim repo."""
    base = tmp_path_factory.mktemp("r18n6")
    trees = {}
    for tag, cond in (("head", False), ("cond", True)):
        d = base / f"src-{tag}" / "veracium"
        shutil.copytree(ROOT / "src" / "veracium", d, ignore=shutil.ignore_patterns("__pycache__"))
        if cond:
            c = d / "census.py"; c.write_text(c.read_text() + _R18_COND)
        trees[tag] = d.parent
    repo = base / "repo"; (repo / ".venv" / "bin").mkdir(parents=True)
    shim = repo / ".venv" / "bin" / "python"; shim.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n"); shim.chmod(0o755)
    return base, trees, repo


@pytest.mark.parametrize("tag,equal", [("head", True), ("cond", False)], ids=["unconditional: every run imports T's Site", "conditional on the arm's environment: the gate is FALSE"])
def test_r18_the_runtime_gate_sees_a_change_the_transform_cannot(tag, equal, r18_trees, monkeypatch):
    """Through the REAL chain (derive, run_arm with the observer, site_realized_check): the conditional change is NOT
    drift at transform time — site_drift reads [] and derive succeeds — and the runtime gate is FALSE, naming the entry;
    with no such change the gate is TRUE."""
    un = _load("inv7_uninstrument_r18r", EVIDENCE / "inv7_uninstrument.py")
    harness = _load("inv7_harness_r18r", EVIDENCE / "inv7_harness.py")
    base, trees, repo = r18_trees
    src = trees[tag]
    assert un.site_drift((src / "veracium" / "census.py").read_text(), un.REFERENCE_CENSUS.read_text()) == []
    twin = base / f"twin-{tag}"
    un.derive(src / "veracium", twin / "veracium")
    out = base / f"cell-{tag}"
    S = {}
    # the unconditional cell also runs the FAILING arm, whose own intervention replaces Site._bump: its digest must still
    # equal the reference's, which holds only because the digest is taken at IMPORT (a session-end digest would differ)
    for arm in (("uninstrumented", "healthy", "failing") if equal else ("uninstrumented", "healthy")):
        monkeypatch.setenv("PYTHONPATH", str(src))
        S[arm] = harness.run_arm(repo, arm, [str(ROOT / _R16_SEP_SUITE)], out, EVIDENCE / "declaration.py",
                                 twin_src=(str(twin) if arm == "uninstrumented" else None))
    got = harness.site_realized_check(S)
    assert got["missing"] == [] and got["equal"] is equal, got
    if not equal:
        assert got["first_difference"] == {"run": "healthy", "entry": "vars.__doc__"}, got


# THE SEPARATING TEST (research's stage-1 condition 1, run first in scratch before any code): the reviewer's class of
# defect — census DECLARATION-time code that changes a later decision — against the round-15 construction and the round-16
# one. The mutant: declare_site, when declaring 'authority.permitted', raises third-party authority in the declaring
# module's `_RUNGS` (a dict defined above the declarations, read by effective() inside the declared decision permitted()).
_R16_MUT_ANCHOR = "    with _REGISTRY_LOCK:\n        if site_id in _REGISTRY:\n            raise CensusError(f\"duplicate enforcement-point id {site_id!r}\")\n"
_R16_MUT = _R16_MUT_ANCHOR + ("        if site_id == \"authority.permitted\":\n"
                              "            import sys as _sys; _sys._getframe(1).f_globals[\"_RUNGS\"][\"third_party\"] = 3\n")
_R16_SEP_SUITE = "tests/test_0011_entitlement.py"
_R16_SEP_CELLS = [
    # (cell, arms mutated?, the twin's census: "reference" | "head", expected verdict)
    ("round-15 construction, mutated: the defect is SHARED", True, "head", "IDENTICAL"),
    ("reference census, mutated: the defect SEPARATES", True, "reference", "DIVERGENT"),
    ("reference census, unmutated: the control", False, "reference", "IDENTICAL"),
    ("round-15 construction, unmutated: the baseline", False, "head", "IDENTICAL"),
]


@pytest.fixture(scope="module")
def r16_trees(tmp_path_factory):
    """The source tree twice (as is, and with the declaration-time mutant in census.py) and a shim repo whose
    .venv/bin/python is THIS interpreter, for the separating test."""
    base = tmp_path_factory.mktemp("r16sep")
    trees = {}
    for tag, mutated in (("head", False), ("mut", True)):
        d = base / f"src-{tag}" / "veracium"
        shutil.copytree(ROOT / "src" / "veracium", d, ignore=shutil.ignore_patterns("__pycache__"))
        if mutated:
            c = d / "census.py"; t = c.read_text(); assert t.count(_R16_MUT_ANCHOR) == 1; c.write_text(t.replace(_R16_MUT_ANCHOR, _R16_MUT))
        trees[tag] = d.parent
    repo = base / "repo"; (repo / ".venv" / "bin").mkdir(parents=True)
    shim = repo / ".venv" / "bin" / "python"; shim.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n"); shim.chmod(0o755)
    return base, trees, repo


def _r16_arm(harness, repo, arm, src_root, out, monkeypatch, twin=None, name=None):
    monkeypatch.setenv("PYTHONPATH", str(src_root))
    return harness.run_arm(repo, arm, [str(ROOT / _R16_SEP_SUITE)], out, EVIDENCE / "declaration.py", twin_src=(str(twin) if twin else None), out_name=name)


def test_r16_the_mutant_changes_a_decision_at_all(r16_trees, monkeypatch):
    """The separating test's NUMERATOR: the census-OFF arm on the mutated source against the census-OFF arm on the
    source as is — the mutant must change a decision, or nothing the separating cells say means anything."""
    harness = _load("inv7_harness_r16_num", EVIDENCE / "inv7_harness.py")
    base, trees, repo = r16_trees
    out = base / "numerator"
    s = {n: _r16_arm(harness, repo, "off", trees[tag], out, monkeypatch, name=n) for n, tag in (("off", "head"), ("off-mut", "mut"))}
    for n, v in s.items():
        assert pathlib.Path(v["veracium_file"]).is_relative_to(trees["mut" if n == "off-mut" else "head"]), (n, v["veracium_file"])
    a, b = (harness.segments(out / n, s[n]) for n in ("off", "off-mut"))
    assert sorted(t for t in set(a) | set(b) if a.get(t) != b.get(t)), "the mutant changed no decision: the separating test would be vacuous"


@pytest.mark.parametrize("cell,mutated,twin_census,verdict", _R16_SEP_CELLS, ids=[c[0] for c in _R16_SEP_CELLS])
def test_r16_the_reference_census_separates_a_declaration_time_defect(cell, mutated, twin_census, verdict, r16_trees, monkeypatch):
    """The round-15 verdict's class, through the REAL harness pieces (derive, run_arm with the observer, compare): a defect
    in the census's declaration-time code, present in the three instrumented arms, reads IDENTICAL when the reference arm
    carries the same census (round 15's construction — the verdict) and DIVERGENT when it carries the REFERENCE census
    (round 16's); with no defect both read IDENTICAL. The reference arm's census-entry count is 0 in every cell."""
    un = _load("inv7_uninstrument_r16_sep", EVIDENCE / "inv7_uninstrument.py")
    harness = _load("inv7_harness_r16_sep", EVIDENCE / "inv7_harness.py")
    base, trees, repo = r16_trees
    src = trees["mut" if mutated else "head"]
    slug = re.sub(r"\W", "_", cell)[:40]
    twin = base / f"twin-{slug}"
    un.derive(src / "veracium", twin / "veracium") if not mutated or twin_census == "reference" else None
    if mutated and twin_census == "head":
        # round 15's construction: the twin carries the census UNDER TEST verbatim (here, the mutated one)
        un.derive(trees["head"] / "veracium", twin / "veracium")
        (twin / "veracium" / "census.py").write_bytes((src / "veracium" / "census.py").read_bytes())
    elif twin_census == "head":
        (twin / "veracium" / "census.py").write_bytes((src / "veracium" / "census.py").read_bytes())
    out = base / f"cell-{slug}"
    arms = ["healthy", "failing", "off", "uninstrumented"]
    S = {a: _r16_arm(harness, repo, a, src, out, monkeypatch, twin=(twin if a == "uninstrumented" else None)) for a in arms}
    for a in arms:
        assert pathlib.Path(S[a]["veracium_file"]).is_relative_to(twin if a == "uninstrumented" else src), (a, S[a]["veracium_file"])
    v, _ = harness.compare(out, arms, S, ID_TO_SYMBOL)
    # the VERDICT is asserted BEFORE the twin's census identity, deliberately: at the round-15 pin the "reference" cells
    # derive with round 15's transform (HEAD's census verbatim), so the mutated one reads IDENTICAL with 0 census entries
    # — the reviewer's finding, failing on its own assertion — where an identity check first would fail on a name the
    # pin does not have (REFERENCE_CENSUS) and demonstrate nothing
    got = "IDENTICAL" if v["identical"] else "DIVERGENT"
    # the message names the verdict it READ, so a RED at an earlier pin prints what it saw (N-4: it printed the empty set)
    assert got == verdict, (cell, f"read {got}, expected {verdict}", v["divergences"])
    assert S["uninstrumented"]["census_code_entries"] == 0, (cell, S["uninstrumented"].get("census_code_entry_detail"))
    want_census = (src / "veracium" / "census.py").read_bytes() if twin_census == "head" else un.REFERENCE_CENSUS.read_bytes()
    assert (twin / "veracium" / "census.py").read_bytes() == want_census


def test_r16_run_arm_hands_the_child_an_absolute_import_path(tmp_path, monkeypatch):
    """The round-15 verdict's second finding: the reviewer ran the extracted package with a RELATIVE import path, and the
    child run_arm starts (cwd = the repo) could not import it — three tests failed. run_arm now makes every inherited
    entry absolute against the parent's cwd. Captured at the subprocess boundary; the pre-fix form is the mutant."""
    harness = _load("inv7_harness_r16_path", EVIDENCE / "inv7_harness.py")
    seen = {}
    def fake_run(cmd, cwd=None, env=None, capture_output=None, text=None):
        seen["pp"] = env["PYTHONPATH"]; out = pathlib.Path(env["INV7_OUT"]); out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text("{}")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(["src", "lib/extra"]))
    harness.run_arm(tmp_path / "repo", "off", ["t.py"], tmp_path / "out", EVIDENCE / "declaration.py")
    parts = seen["pp"].split(os.pathsep)
    assert all(os.path.isabs(p) for p in parts), parts
    assert str(tmp_path / "src") in parts and str(tmp_path / "lib" / "extra") in parts, parts


def test_r13_p1_import_module_of_the_standard_library_is_not_refused(tmp_path):
    """The acceptance half, measured on the real tree: its one `import_module` call names the standard library."""
    un = _load("inv7_uninstrument_r13_p1_ok", EVIDENCE / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "stdlib", "import importlib\n\n\ndef f():\n    return importlib.import_module('re') is not None\n", "")
    out = tmp_path / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == []


def _r13_closure_pkg(tmp_path, slug, b_text, extra):
    src = _r13_pkg(tmp_path, slug, b_text, "")
    for name, text in extra.items():
        (src / name).write_text(text)
    return src










# ---- round 25: the round-24 verdict's R24-1 — an annotation whose text is DATA is kept as written -------------------
def _r25_mutant(tmp_path, filename, anchor, replacement, tag):
    """The evidence directory copied with ONE file mutated, and inv7_uninstrument loaded from the copy — it loads its
    siblings (scope_resolution) by its own path, so a mutant in either file reaches the transform and verify()."""
    ev = tmp_path / tag
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    text = (ev / filename).read_text(encoding="utf-8")
    assert text.count(anchor) == 1, (tag, filename, "the anchor moved")
    (ev / filename).write_text(text.replace(anchor, replacement), encoding="utf-8")
    return _load(f"inv7_uninstrument_r25_{tag}", ev / "inv7_uninstrument.py")


_R25_ANN = "S.fire(123)"
# every annotation POSITION the grammar has; the regime is the second axis. The expected outcome is NOT listed here: it
# is DERIVED from the compiler (`_r25_executable`), so a position whose evaluation 3.14 changes moves its own cell
_R25_POSITIONS = [
    ("def parameter",            f"def f(x: {_R25_ANN}):\n    pass\n"),
    ("def return",               f"def f() -> {_R25_ANN}:\n    pass\n"),
    ("def positional-only",      f"def f(x: {_R25_ANN}, /):\n    pass\n"),
    ("def keyword-only",         f"def f(*, k: {_R25_ANN}):\n    pass\n"),
    ("def *args",                f"def f(*a: {_R25_ANN}):\n    pass\n"),
    ("def **kwargs",             f"def f(**k: {_R25_ANN}):\n    pass\n"),
    ("async def parameter",      f"async def f(x: {_R25_ANN}):\n    pass\n"),
    ("method parameter",         f"class C:\n    def m(self, x: {_R25_ANN}):\n        pass\n"),
    ("nested def parameter",     f"def outer():\n    def inner(x: {_R25_ANN}):\n        pass\n    return inner\n"),
    ("generic def parameter",    f"def f[T](x: {_R25_ANN}):\n    pass\n"),
    ("module variable",          f"x: {_R25_ANN}\n"),
    ("module variable with value", f"x: {_R25_ANN} = 1\n"),
    ("module parenthesised target", f"(x): {_R25_ANN} = 1\n"),
    ("module attribute target",  f"class O:\n    pass\no = O()\no.a: {_R25_ANN} = 1\n"),
    ("module subscript target",  f"d = {{}}\nd['k']: {_R25_ANN} = 1\n"),
    ("class variable",           f"class C:\n    y: {_R25_ANN}\n"),
    ("class attribute target",   f"class C:\n    o = None\n    o.a: {_R25_ANN} = 1\n"),
    ("class variable in a function", f"def f():\n    class K:\n        y: {_R25_ANN}\n    return K\n"),
    ("function-local variable",  f"def f():\n    z: {_R25_ANN} = 1\n    return z\n"),
    ("function-local attribute target", f"def f(o):\n    o.a: {_R25_ANN} = 1\n"),
]
_R25_REGIMES = [("lazy", ""), ("future import", "from __future__ import annotations\n")]
_R25_HEAD = "from . import census as _census\nS = _census.declare_site('m.s')\n\n"


def _r25_executable(prologue, body) -> bool:
    """Can the annotation's call EVER run? The compiler's answer: does any code object compiled from the module load the
    call's argument 123 as a value (a stringified annotation holds it inside a string constant; an annotation that is
    never evaluated is compiled away)."""
    import dis
    todo, hit = [compile(prologue + "S = None\n" + body, "<r25>", "exec", dont_inherit=True)], False
    while todo:
        co = todo.pop()
        hit = hit or any(i.opname in ("LOAD_SMALL_INT", "LOAD_CONST") and i.argval == 123 for i in dis.get_instructions(co))
        todo += [c for c in co.co_consts if hasattr(c, "co_code")]
    return hit


_R25_MATRIX = [(f"{pos} / {regime}", prologue, body) for pos, body in _R25_POSITIONS for regime, prologue in _R25_REGIMES]


@pytest.mark.parametrize("cell,prologue,body", _R25_MATRIX, ids=[c[0] for c in _R25_MATRIX])
def test_r25_every_annotation_position_by_regime_is_preserved_or_refused_as_the_compiler_evaluates_it(cell, prologue, body):
    """The verdict's R24-1, as a MATRIX (research's stage 1): every annotation position × {lazy, future import}. An
    annotation whose call can run is REFUSED (the census use would run apart from its decision); one that can never run
    is DATA and is kept byte-for-byte — never rewritten (the round-24 defect: `S.fire(123)` became `123`) and never
    refused. Which is which comes from the compiler, not from a list."""
    un = _load("inv7_uninstrument_r25_matrix", EVIDENCE / "inv7_uninstrument.py")
    src = prologue + _R25_HEAD + body
    if _r25_executable(prologue, body):
        with pytest.raises(Exception, match="runs apart from the decision beside it"):
            un.uninstrument_source(src, f"<{cell}>")
        return
    out, stats = un.uninstrument_source(src, f"<{cell}>")
    # the TEXT first — what the round-24 verdict saw — so the cell fails on the rewrite itself wherever there is one
    assert [l for l in body.splitlines() if _R25_ANN in l] == [l for l in out.splitlines() if _R25_ANN in l], (cell, out)
    assert un.annotations_in_order(out) == un.annotations_in_order(src), (cell, out)
    assert stats["preserved_annotation_census_calls"] == [f"{_R25_ANN} at line {src.count(chr(10), 0, src.index(_R25_ANN)) + 1}"], (cell, stats)


_R25_VERDICT_CASES = [
    ("a function's annotation", "def f(x: S.fire(123)):\n    pass\n", "def f(x: S.fire(123)):"),
    ("a module variable's annotation", "x: S.fire(123)\n", "x: S.fire(123)"),
]


@pytest.mark.parametrize("case,body,line", _R25_VERDICT_CASES, ids=[c[0] for c in _R25_VERDICT_CASES])
def test_r25_the_verdicts_two_cases_keep_their_annotation_text(case, body, line):
    """The round-24 verdict's R24-1, exactly as it was found: under `from __future__ import annotations` the transform
    turned `def f(x: S.fire(123))` into `def f(x: 123)` and `x: S.fire(123)` into `x: 123`. Each is kept as written."""
    un = _load("inv7_uninstrument_r25_verdict", EVIDENCE / "inv7_uninstrument.py")
    out, _stats = un.uninstrument_source("from __future__ import annotations\n" + _R25_HEAD + body, f"<{case}>")
    assert line in out.splitlines(), f"{case}: the annotation was rewritten — {[l for l in out.splitlines() if '123' in l]}"


def test_r25_the_matrix_holds_both_outcomes_in_the_lazy_regime_and_only_data_under_the_future_import():
    """The acceptance half of the matrix, COUNTED: a matrix whose derivation read every cell one way would pass the cells
    above vacuously. On 3.14 the lazy regime refuses the def, method, module and class annotations and keeps the local and
    non-simple-target ones; the future import makes every one data."""
    got = {(regime, _r25_executable(prologue, body)) for pos, body in _R25_POSITIONS for regime, prologue in _R25_REGIMES}
    assert got == {("lazy", True), ("lazy", False), ("future import", False)}, got
    kept = sorted(pos for pos, body in _R25_POSITIONS if not _r25_executable("", body))
    assert kept == sorted(["module parenthesised target", "module attribute target", "module subscript target",
                           "class attribute target", "function-local variable", "function-local attribute target"]), kept


_R25_B_FUTURE = ("from __future__ import annotations\n" + _R14_SELF +
                 "def f(x: S.fire(123)) -> S.consult():\n    return x\n\n\nV: S.fire(7) = 1\n\n\n"
                 "def h():\n    z: S.fire(9) = 1\n    return z\n")
_R25_READ = ("import json, sys; sys.path.insert(0, sys.argv[1]); import vpkg.b as b\n"
             "fired = []\n"
             "class Rec:\n"
             "    def fire(self, *a):\n        fired.append(a)\n        return a[0]\n"
             "    def consult(self):\n        fired.append('consult')\n"
             "b.S = Rec()\n"
             "print(json.dumps({'f': b.f.__annotations__, 'module': b.__annotations__, 'h': b.h(), 'fired': fired}))\n")


def test_r25_the_reviewers_cases_end_to_end_the_twin_reads_the_sources_annotations(tmp_path):
    """The verdict's two cases, a function's and a module variable's, and the function-local one (research's stage 1:
    "ship a cell showing the local annotation's census call stays in the twin text and never runs"): derive, verify()
    clean, and the SOURCE and the TWIN each imported in a child — `f.__annotations__` and the module's `__annotations__`
    read identically (the strings as written), and calling `h` runs no census call in either."""
    read = _r25_e2e(_load("inv7_uninstrument_r25_e2e", EVIDENCE / "inv7_uninstrument.py"), tmp_path, _R25_B_FUTURE)
    assert read["twin"] == {"f": {"x": "S.fire(123)", "return": "S.consult()"}, "module": {"V": "S.fire(7)"}, "h": 1, "fired": []}, read


def _r25_e2e(un, tmp_path, b_text):
    src = _r13_pkg(tmp_path, "e2e", b_text, "")
    out = tmp_path / "e2e" / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == [], un.verify(out, src)
    twin_b = (out / "b.py").read_text(encoding="utf-8")
    assert "def f(x: S.fire(123))" in twin_b and "V: S.fire(7) = 1" in twin_b and "z: S.fire(9) = 1" in twin_b, twin_b
    read = {}
    for arm, root in (("source", src.parent), ("twin", out.parent)):
        r = subprocess.run([sys.executable, "-c", _R25_READ, str(root)], capture_output=True, text=True)
        assert r.returncode == 0, (arm, r.stderr[-800:])
        read[arm] = json.loads(r.stdout)
    assert read["source"] == read["twin"], read
    return read


_R25_R24_TRANSFORM = ("    future = _future_annotations(tree)\n    roots = {}\n", "    future = False\n    roots = {}\n")


def test_r25_rewriting_under_the_future_import_is_caught_by_verifys_independent_check(tmp_path):
    """THE ROUND-24 TRANSFORM IS THE MUTANT (the classifier blind to the future import): it rewrites `S.fire(123)` to
    `123` inside the annotation, and because verify()'s structure check RE-DERIVES with the same transform, only an
    independent reading can see it — the annotation comparison, which never asks the classifier. The end-to-end cell
    fails under it too."""
    mut = _r25_mutant(tmp_path, "scope_resolution.py", *_R25_R24_TRANSFORM, "r24transform")
    # the reviewer's shape: a FIRE in the annotation, which the round-24 transform rewrote silently (a consult there it
    # left, and the token check refused the module — loud, so not the case this mutant is for)
    fire_only = _R25_B_FUTURE.replace(" -> S.consult():", ":")
    src = _r13_pkg(tmp_path, "mut", fire_only, "")
    out = tmp_path / "mut" / "twin" / "vpkg"
    mut.derive(src, out)
    assert "def f(x: 123)" in (out / "b.py").read_text(encoding="utf-8"), "the mutant no longer rewrites: it tests nothing"
    problems = mut.verify(out, src)
    assert any("b.py: the twin's ANNOTATIONS differ" in p for p in problems), problems
    assert not any("program structure differs" in p for p in problems), "the re-derivation saw it: the check is not the one tested"
    with pytest.raises(AssertionError):
        _r25_e2e(mut, tmp_path / "e2e-under-mutant", fire_only)
    _r25_e2e(_load("inv7_uninstrument_r25_e2e_fire", EVIDENCE / "inv7_uninstrument.py"), tmp_path / "e2e-shipped", fire_only)


def test_r25_verify_names_a_dropped_or_rewritten_annotation_the_classifier_would_exempt(tmp_path):
    """verify()'s annotation check over a HAND-EDITED twin (no transform involved), both directions: an annotation
    rewritten, and one dropped — each named; the clean twin is not."""
    un = _load("inv7_uninstrument_r25_verify", EVIDENCE / "inv7_uninstrument.py")
    src = _r13_pkg(tmp_path, "v", _R25_B_FUTURE, "")
    out = tmp_path / "v" / "twin" / "vpkg"
    un.derive(src, out)
    assert un.verify(out, src) == []
    man_path = out.parent / "twin_manifest.json"
    for edit in (("def f(x: S.fire(123))", "def f(x: 123)"), ("def f(x: S.fire(123)) -> S.consult():", "def f(x: S.fire(123)):")):
        good = (out / "b.py").read_text(encoding="utf-8")
        assert good.count(edit[0]) == 1, edit
        (out / "b.py").write_text(good.replace(edit[0], edit[1]), encoding="utf-8")
        man = json.loads(man_path.read_text(encoding="utf-8")); old_after = man["modules"]["b.py"]["sha256_after"]
        man["modules"]["b.py"]["sha256_after"] = hashlib.sha256((out / "b.py").read_bytes()).hexdigest()
        man_path.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        assert any("b.py: the twin's ANNOTATIONS differ" in p for p in un.verify(out, src)), edit
        (out / "b.py").write_text(good, encoding="utf-8")
        man["modules"]["b.py"]["sha256_after"] = old_after
        man_path.write_text(json.dumps(man, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    assert un.verify(out, src) == []


def test_r25_the_token_check_exempts_data_annotations_and_nothing_else():
    """`instrumentation_tokens_in` — ONE definition, the transform's refusal and verify()'s — skips exactly the
    annotations the shared classifier calls data: the same call in a lazy annotation, in a default, in a body, or in a
    string constant is still found; text that does not parse is searched whole."""
    un = _load("inv7_uninstrument_r25_tokens", EVIDENCE / "inv7_uninstrument.py")
    fut = "from __future__ import annotations\n"
    assert un.instrumentation_tokens_in(fut + "def f(x: S.fire(1)): pass\n") == []
    assert un.instrumentation_tokens_in("def f():\n    z: S.fire(1) = 1\n") == []
    for text in ("def f(x: S.fire(1)): pass\n", fut + "def f(x=S.fire(1)): pass\n", fut + "def f():\n    return S.fire(1)\n",
                 fut + "X = 'S.fire(1)'\n", fut + "def f(x: S.fire(1)):\n    return S.fire(2)\n", "def f(:\n    S.fire(1)\n"):
        assert un.instrumentation_tokens_in(text) == [".fire("], text


# ---- round 25: the round-24 verdict's R24-2 — lazy type metadata is described, never evaluated -----------------------
# The reviewer's eleven cases: nine AFFECTED forms and the two annotation controls. Each is (label, the Site's source,
# a path to the object holding the lazy value or None for a control, the evaluator's name).
_R25_SIDE = "CALLS = []\ndef side(label):\n    CALLS.append(label)\n    return int\n"
_R25_LAZY = [
    ("method TypeVar bound", "class Site:\n    def fire[T: side('X')](self, value):\n        return value\n",
     lambda m: m.Site.fire.__type_params__[0], "evaluate_bound"),
    ("method TypeVar constraints", "class Site:\n    def fire[T: (side('X'), side('Y'))](self, value):\n        return value\n",
     lambda m: m.Site.fire.__type_params__[0], "evaluate_constraints"),
    ("method TypeVar default", "class Site:\n    def fire[T = side('X')](self, value):\n        return value\n",
     lambda m: m.Site.fire.__type_params__[0], "evaluate_default"),
    ("method ParamSpec default", "class Site:\n    def fire[**P = side('X')](self, value):\n        return value\n",
     lambda m: m.Site.fire.__type_params__[0], "evaluate_default"),
    ("method TypeVarTuple default", "class Site:\n    def fire[*Ts = side('X')](self, value):\n        return value\n",
     lambda m: m.Site.fire.__type_params__[0], "evaluate_default"),
    ("generic class bound", "class Site[T: side('X')]:\n    def fire(self, value):\n        return value\n",
     lambda m: m.Site.__type_params__[0], "evaluate_bound"),
    ("generic class default", "class Site[T = side('X')]:\n    def fire(self, value):\n        return value\n",
     lambda m: m.Site.__type_params__[0], "evaluate_default"),
    ("class-held alias", "class Site:\n    type Value = side('X')\n    def fire(self, value):\n        return value\n",
     lambda m: m.Site.Value, "evaluate_value"),
    ("class-held generic alias", "class Site:\n    type Value[V] = side('X')\n    def fire(self, value):\n        return value\n",
     lambda m: m.Site.Value, "evaluate_value"),
    # beyond the reviewer's nine: the alias's OWN type parameter, reached only by recursing into __type_params__
    ("class-held alias's type-parameter bound", "class Site:\n    type Value[V: side('X')] = int\n    def fire(self, value):\n        return value\n",
     lambda m: m.Site.Value.__type_params__[0], "evaluate_bound"),
]
_R25_CONTROLS = [
    ("annotation control", "class Site:\n    def fire(self, value: side('X')) -> side('Y'):\n        return value\n", None, None),
    ("future-import annotation control", "from __future__ import annotations\nclass Site:\n    def fire(self, value: side('X')):\n        return value\n", None, None),
]


def _r25_site(label, body):
    import types
    mod = types.ModuleType("r25site")
    head, body = (body.split("\n", 1)[0] + "\n", body.split("\n", 1)[1]) if body.startswith("from __future__") else ("", body)
    exec(compile(head + _R25_SIDE + body, f"<r25:{label}>", "exec", dont_inherit=True), mod.__dict__)
    return mod


def _r25_describe_counting(un, mod, label):
    """(the digest, code objects ENTERED from the case's own source while describing) — through site_description AND
    the runtime caller, the observer's `_site_realized` (the digest the arms compare)."""
    entered = []

    def hook(frame, event, arg):
        if event == "call" and frame.f_code.co_filename == f"<r25:{label}>":
            entered.append(frame.f_code.co_name)
    sys.setprofile(hook)
    try:
        digest = un.site_description_digest(un.site_description(mod.Site))["digest"]
        realized = observer._site_realized(mod.Site)["digest"]
    finally:
        sys.setprofile(None)
    return digest, realized, entered


@pytest.mark.parametrize("label,body,holder,evaluator", _R25_LAZY + _R25_CONTROLS, ids=[c[0] for c in _R25_LAZY + _R25_CONTROLS])
def test_r25_describing_lazy_type_metadata_runs_no_census_code(label, body, holder, evaluator):
    import types
    """The verdict's R24-2: describing a Site whose type parameters or class-held aliases carry LAZY values enters no
    code compiled from the census's source and runs none of its side effects — through the describer AND the observer's
    runtime digest. The case must really be lazy (the evaluator present and a FUNCTION, the value unevaluated), or the
    cell fails by name; the lazy value is described as such, and the two routes agree."""
    un = _load("inv7_uninstrument_r25_lazy", EVIDENCE / "inv7_uninstrument.py")
    mod = _r25_site(label, body)
    if holder is not None:
        # round 26: the LAZY shape is a compiler-generated FUNCTION, not merely a callable (round 25 read the two as one,
        # and a constant evaluator around an eager value is callable too — the round-25 verdict's R25-1)
        assert isinstance(getattr(holder(mod), evaluator), types.FunctionType), \
            f"{label}: not the lazy shape — this cell cannot run its case"
    assert mod.CALLS == [], mod.CALLS
    digest, realized, entered = _r25_describe_counting(un, mod, label)
    assert mod.CALLS == [] and entered == [], (label, mod.CALLS, entered)
    assert digest == realized, label
    if holder is not None:
        assert f"<lazy: described by {evaluator}>" in repr(un.site_description(mod.Site)), label


@pytest.mark.parametrize("label,body,holder,evaluator", _R25_LAZY, ids=[c[0] for c in _R25_LAZY])
def test_r25_a_changed_lazy_definition_still_describes_differently(label, body, holder, evaluator):
    """The verdict's other half: "simply excluding every type-parameter/alias object would create another undetected-drift
    gap". Two Sites differing ONLY in the lazy expression (`side('X')` against `side('Z')`) describe differently —
    the evaluator is described by its code — and describing either still runs nothing."""
    un = _load("inv7_uninstrument_r25_changed", EVIDENCE / "inv7_uninstrument.py")
    a, b = _r25_site(label, body), _r25_site(label, body.replace("side('X')", "side('Z')"))
    da, _, ea = _r25_describe_counting(un, a, label)
    db, _, eb = _r25_describe_counting(un, b, label)
    assert da != db, f"{label}: a changed lazy definition reads as no drift"
    assert a.CALLS == b.CALLS == [] and ea == eb == [], (label, a.CALLS, b.CALLS)


def test_r25_a_bare_type_parameter_is_read_eagerly_not_marked_lazy():
    """The acceptance half (research's stage 1: so "lazy" is not concluded from the TYPE alone): a bare `[V]` carries no
    evaluator — its evaluate_* read None — and its __bound__/__constraints__/__default__ are READ and described as values."""
    import typing
    un = _load("inv7_uninstrument_r25_bare", EVIDENCE / "inv7_uninstrument.py")
    mod = _r25_site("bare", "class Site:\n    def fire[V](self, value):\n        return value\n")
    v = mod.Site.fire.__type_params__[0]
    assert (v.evaluate_bound, v.evaluate_constraints, v.evaluate_default) == (None, None, None)
    assert v.__bound__ is None and v.__constraints__ == () and v.__default__ is typing.NoDefault
    desc = repr(un._normalise(v, {}))
    assert "<lazy:" not in desc and "'__bound__'" in desc and "'__default__'" in desc, desc


def test_r25_the_evaluator_pairing_is_derived_and_exists_on_this_interpreter():
    """The pairing `evaluate_<x>` → `__<x>__` is DERIVED from the descriptor names, never listed — so the rule would
    silently cover nothing if CPython renamed them. Asserted to EXIST: on 3.14, each PEP 695 type carries the pairs the
    rule relies on."""
    import typing
    un = _load("inv7_uninstrument_r25_pairs", EVIDENCE / "inv7_uninstrument.py")
    want = {typing.TypeVar: {"__bound__", "__constraints__", "__default__"}, typing.ParamSpec: {"__default__"},
            typing.TypeVarTuple: {"__default__"}, typing.TypeAliasType: {"__value__"}}
    for tp, values in want.items():
        d = un._data_descriptors(tp)
        assert values <= {"__" + n[len("evaluate_"):] + "__" for n in d if n.startswith("evaluate_")} <= set(d), (tp, sorted(d))


_R25_READ_MUTANT = ("        if n in lazy_values:\n", "        if False:\n")


def test_r25_the_lazy_value_rule_is_load_bearing(tmp_path, monkeypatch):
    """THE READ MUTANT: the lazy value read like any other descriptor — every affected cell must then fail."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", *_R25_READ_MUTANT, "readlazy")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    for label, body, holder, evaluator in _R25_LAZY:
        try:   # run (the cell's assertion), or refused by round 28's guard — by the guard's own message, nothing else
            test_r25_describing_lazy_type_metadata_runs_no_census_code(label, body, holder, evaluator)
        except AssertionError:
            continue
        except mut.SiteUndescribed as e:
            assert "would run code the describer did not write" in str(e), (label, str(e))
            continue
        pytest.fail(f"{label}: the cell passed under the read mutant")


# ---- round 25, found by the R24-2 cells: a WRAPPER's annotations, and objects made during a description ---------------
_R25_WRAPPERS = ("class Site:\n    @classmethod\n    def c(cls, x: side('cm')):\n        pass\n"
                 "    @staticmethod\n    def s(x):\n        pass\n    def fire(self, value):\n        return value\n")


def test_r25_describing_a_wrapper_writes_nothing_runs_nothing_and_is_stable():
    """On 3.14 READING a classmethod's or staticmethod's `__annotate__` stores it in the wrapper's own `__dict__`, and
    reading `__annotations__` stores the evaluated dict — calling the wrapped `__annotate__`. Describing a Site holding
    an annotated classmethod and a bare staticmethod, and a generic Site (whose Generic[T] base reaches typing's own
    classmethods), writes nothing into either wrapper, runs no census code, and describes the same three times."""
    un = _load("inv7_uninstrument_r25_wrap", EVIDENCE / "inv7_uninstrument.py")
    mod = _r25_site("wrappers", _R25_WRAPPERS)
    before = {k: dict(vars(vars(mod.Site)[k])) for k in ("c", "s")}
    descs = [un.site_description(mod.Site) for _ in range(3)]
    assert {k: dict(vars(vars(mod.Site)[k])) for k in ("c", "s")} == before, "the describer wrote into a wrapper"
    assert mod.CALLS == [] and descs[0] == descs[1] == descs[2]
    generic = _r25_site("generic", "class Site[T]:\n    def fire(self, value):\n        return value\n")
    assert len({repr(un.site_description(generic.Site)) for _ in range(3)}) == 1, "a generic Site describes unstably"


def test_r25_another_reader_of_a_wrapper_is_not_drift_and_an_assignment_is():
    """Who read a wrapper's annotations first is not drift — a bare one, and an annotated one read (which evaluates it)
    from outside; an ASSIGNED `__annotations__` or `__annotate__` on a wrapper is."""
    un = _load("inv7_uninstrument_r25_wrapread", EVIDENCE / "inv7_uninstrument.py")

    def digest(prepare=None):
        m = _r25_site("wrappers", _R25_WRAPPERS)
        if prepare:
            prepare(m)
        return un.site_description_digest(un.site_description(m.Site))["digest"]
    base = digest()
    assert digest(lambda m: (vars(m.Site)["s"].__annotations__, vars(m.Site)["s"].__annotate__)) == base
    assert digest(lambda m: vars(m.Site)["c"].__annotations__) == base
    assert digest(lambda m: setattr(vars(m.Site)["s"], "__annotations__", {"z": str})) != base
    assert digest(lambda m: setattr(vars(m.Site)["c"], "__annotations__", {"z": str})) != base
    assert digest(lambda m: setattr(vars(m.Site)["c"], "__annotate__", None)) != base


def test_r25_every_described_object_is_held_until_the_description_ends():
    """The id-reuse mechanism, asserted rather than hoped for: `seen` holds each object it gave a position, so no
    address freed during the description can be read back as a `<ref>` (allocation-dependent otherwise — a cell relying
    on reuse to happen would be flaky, so the property is asserted on the mechanism itself)."""
    un = _load("inv7_uninstrument_r25_held", EVIDENCE / "inv7_uninstrument.py")
    mod = _r25_site("held", _R25_WRAPPERS)
    seen = {}
    un._normalise(mod.Site, seen)
    assert seen and all(type(v) is tuple and id(v[1]) == k for k, v in seen.items()), \
        [k for k, v in seen.items() if type(v) is not tuple][:3]


_R25_WRAPPER_MUTANTS = [
    ("the wrapper read like any object", "    wrapper = not is_class and _WRAPPER <= set(descriptors)\n",
     "    wrapper = False\n", test_r25_describing_a_wrapper_writes_nothing_runs_nothing_and_is_stable),
    ("the read-created wrapper keys kept", "        if k == \"__annotations__\" and any(r is x for r in gc.get_referents(func)):\n",
     "        if False:\n", test_r25_another_reader_of_a_wrapper_is_not_drift_and_an_assignment_is),
    ("the wrapper's annotation keys dropped unconditionally",
     "        if k == \"__annotations__\" and any(r is x for r in gc.get_referents(func)):\n",
     "        if k == \"__annotations__\":\n", test_r25_another_reader_of_a_wrapper_is_not_drift_and_an_assignment_is),
    ("the wrapper's __annotate__ dropped unconditionally",
     "        if k == \"__annotate__\" and x is _read(func, type(func), \"__annotate__\", None):\n",
     "        if k == \"__annotate__\":\n", test_r25_another_reader_of_a_wrapper_is_not_drift_and_an_assignment_is),
    ("a described object not held", "    seen[id(obj)] = (len(seen), obj)\n", "    seen[id(obj)] = len(seen)\n",
     test_r25_every_described_object_is_held_until_the_description_ends),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell", _R25_WRAPPER_MUTANTS, ids=[m[0] for m in _R25_WRAPPER_MUTANTS])
def test_r25_each_wrapper_rule_is_load_bearing(mutant, anchor, replacement, cell, tmp_path, monkeypatch):
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "wrapm")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    with pytest.raises(AssertionError):
        cell()


_R25_CLASSIFIER_MUTANTS = [
    ("every def annotation kept, whatever the regime", "                if future:\n                    for x in a.posonlyargs",
     "                if True:\n                    for x in a.posonlyargs"),
    ("every variable annotation kept, whatever the regime",
     "                if isinstance(child, ast.AnnAssign) and (future or scope == \"function\" or not child.simple):",
     "                if isinstance(child, ast.AnnAssign):"),
    ("the function-local rule removed",
     "                if isinstance(child, ast.AnnAssign) and (future or scope == \"function\" or not child.simple):",
     "                if isinstance(child, ast.AnnAssign) and (future or not child.simple):"),
    ("the non-simple-target rule removed",
     "                if isinstance(child, ast.AnnAssign) and (future or scope == \"function\" or not child.simple):",
     "                if isinstance(child, ast.AnnAssign) and (future or scope == \"function\"):"),
    ("the future-import regime ignored", *_R25_R24_TRANSFORM),
]


@pytest.mark.parametrize("mutant,anchor,replacement", _R25_CLASSIFIER_MUTANTS, ids=[m[0] for m in _R25_CLASSIFIER_MUTANTS])
def test_r25_each_regime_rule_is_load_bearing(mutant, anchor, replacement, tmp_path, monkeypatch):
    """Each rule of the shared classifier, removed or widened, fails at least one cell of the position × regime matrix."""
    mut = _r25_mutant(tmp_path, "scope_resolution.py", anchor, replacement, "regimem")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    failed = []
    for cell, prologue, body in _R25_MATRIX:
        try:
            test_r25_every_annotation_position_by_regime_is_preserved_or_refused_as_the_compiler_evaluates_it(cell, prologue, body)
        except (AssertionError, pytest.fail.Exception, Exception) as e:
            failed.append((cell, type(e).__name__))
    assert failed, f"{mutant}: every matrix cell still passes"


# ---- round 26: the round-25 verdict's R25-1 — an EAGER value behind the constant evaluator is read and compared -------
# The constructor regime: `typing.TypeVar('T', bound=X)` and its five siblings hold X ALREADY SUPPLIED, behind CPython's
# `_typing._ConstEvaluator`. Round 25 took any callable evaluator for a lazy one and dropped the value, so a held class or
# function changed with the Site's behaviour and no drift read, in all six forms. (label, constructor, how fire uses it)
_R26_FORMS = [
    ("TypeVar bound",        "typing.TypeVar('T', bound=Held)",       "self.param.__bound__"),
    ("TypeVar constraints",  "typing.TypeVar('T', Held, int)",        "self.param.__constraints__[0]"),
    ("TypeVar default",      "typing.TypeVar('T', default=Held)",     "self.param.__default__"),
    ("ParamSpec default",    "typing.ParamSpec('P', default=Held)",   "self.param.__default__"),
    ("TypeVarTuple default", "typing.TypeVarTuple('Ts', default=Held)", "self.param.__default__"),
    ("TypeAliasType value",  "typing.TypeAliasType('A', Held)",       "self.param.__value__"),
]
# the held object: a mutable CLASS, and a FUNCTION, each under the same name in both censuses, with different contents
_R26_HELD = [
    ("a class", "class Held:\n    def decision(self):\n        return {v}\n", "().decision()"),
    ("a function", "def Held():\n    return {v}\n", "()"),
]
_R26_EAGER = [(f"{form} holding {what}", ctor, use, held, call)
              for form, ctor, use in _R26_FORMS for what, held, call in _R26_HELD]


def _r26_census(ctor, use, held, call, v):
    return ("import typing\n\n" + held.format(v=v) +
            f"\nclass Site:\n    param = {ctor}\n\n    def fire(self, value):\n        return {use}{call}\n")


@pytest.mark.parametrize("cell,ctor,use,held,call", _R26_EAGER, ids=[c[0] for c in _R26_EAGER])
def test_r26_a_changed_eager_value_behind_the_constant_evaluator_is_drift(cell, ctor, use, held, call):
    """The verdict's R25-1 fixture, both held kinds: the two censuses differ ONLY inside the held object; the Site source is
    identical; its behaviour changes. Route B must describe them differently and site_drift must report it. The regime is
    asserted FIRST from the interpreter alone — an evaluator that is present and not a function, so the cell cannot pass on
    a lazy case — and the describer's own name for it LAST: at the round-25 pin, which has no such name, the cell must
    fail on the undetected drift the verdict found, not on a missing attribute (the round-25 lesson, applied here)."""
    import types
    un = _load("inv7_uninstrument_r26_eager", EVIDENCE / "inv7_uninstrument.py")
    before, after = _r26_census(ctor, use, held, call, 1), _r26_census(ctor, use, held, call, 2)
    sb, sa = un._realized_site(before, "review_census"), un._realized_site(after, "review_census")
    ev = next(getattr(sb.param, n) for n in dir(type(sb.param)) if n.startswith("evaluate_") and getattr(sb.param, n) is not None)
    assert not issubclass(type(ev), types.FunctionType), (cell, "a lazy case: this cell cannot run the regime it is named for", type(ev))
    assert (sb().fire(0), sa().fire(0)) == (1, 2), cell
    db = un.site_description_digest(un.site_description(sb))["digest"]
    da = un.site_description_digest(un.site_description(sa))["digest"]
    assert db != da, f"{cell}: a changed held value reads as no drift"
    assert any("Site.param (realized)" in d for d in un.site_drift(after, before)), cell
    assert type(ev) is un._CONST_EVALUATOR, (cell, type(ev))


@pytest.mark.parametrize("cell,ctor,use,held,call", _R26_EAGER[::2], ids=[c[0] for c in _R26_EAGER[::2]])
def test_r26_reading_an_eager_value_runs_no_census_code(cell, ctor, use, held, call):
    """The zero-evaluation control on the EAGER side, for a held class and function with NO display code of their own:
    describing reads the supplied value and enters no code compiled from the census's source. (Round 26 claimed more than
    this — "reading an eager value runs no census code" — and the round-26 verdict showed a held class's metaclass __repr__
    running during description; that case is round 27's, `test_r27_describing_runs_no_held_display_code`.)"""
    un = _load("inv7_uninstrument_r26_zero", EVIDENCE / "inv7_uninstrument.py")
    mod = _r25_site(cell, _r26_census(ctor, use, held, call, 1))
    _digest, _realized, entered = _r25_describe_counting(un, mod, cell)
    assert entered == [], (cell, entered)


def test_r26_the_constructor_regimes_evaluator_holds_the_supplied_value():
    """The REGIME FACT the rule relies on, asserted HERE and never in the describer (which calls no evaluator): in the
    constructor regime the evaluator is the constant evaluator and, called with the VALUE format, returns the very object
    supplied; in the syntax regime it is a function. If a later interpreter changes either, this fails by name."""
    import types, typing
    un = _load("inv7_uninstrument_r26_regime", EVIDENCE / "inv7_uninstrument.py")

    class Held:
        pass
    for obj, n in ((typing.TypeVar("T", bound=Held), "evaluate_bound"), (typing.TypeVar("T", Held, int), "evaluate_constraints"),
                   (typing.TypeVar("T", default=Held), "evaluate_default"), (typing.ParamSpec("P", default=Held), "evaluate_default"),
                   (typing.TypeVarTuple("Ts", default=Held), "evaluate_default"), (typing.TypeAliasType("A", Held), "evaluate_value")):
        ev = getattr(obj, n)
        assert type(ev) is un._CONST_EVALUATOR, (obj, n, type(ev))
        assert ev(1) is getattr(obj, "__" + n[len("evaluate_"):] + "__"), (obj, n)
    lazy = _r25_site("regime", "class Site:\n    def fire[T: side('X')](self, value):\n        return value\n")
    assert isinstance(lazy.Site.fire.__type_params__[0].evaluate_bound, types.FunctionType)


class _R26OtherEvaluator:
    """A type pairing `evaluate_bound` with `__bound__` whose evaluator is NEITHER a function NOR the constant evaluator —
    held in C slots, which the description reads (round 28: a property serving it is never called; its own cell)."""
    __slots__ = ("evaluate_bound", "__bound__")

    def __init__(self):
        self.evaluate_bound = __import__("functools").partial(int)
        self.__bound__ = int


def test_r26_any_other_evaluator_is_refused_by_name_never_read_as_lazy_or_eager():
    """D3, the totality the verdict asks for: a supported form that cannot be described faithfully is REFUSED, naming the
    object, the field and the evaluator's type — never dropped as lazy, never read as eager."""
    un = _load("inv7_uninstrument_r26_other", EVIDENCE / "inv7_uninstrument.py")

    class Site:
        param = _R26OtherEvaluator()

        def fire(self, value):
            return value
    with pytest.raises(un.SiteUndescribed, match=r"_R26OtherEvaluator\.__bound__: its evaluator `evaluate_bound` is a functools\.partial"):
        un.site_description(Site)


def test_r26_the_constant_evaluator_type_refuses_an_interpreter_where_it_would_be_ambiguous(monkeypatch):
    """The import-time assertion (the second seat's addition): if the derived constant-evaluator type were a function, or
    carried data descriptors, the rule could not tell the regimes apart — it must refuse, not pick a branch."""
    import typing
    un = _load("inv7_uninstrument_r26_assert", EVIDENCE / "inv7_uninstrument.py")

    class FunctionEvaluator:
        def __init__(self, *a, **k):
            self.evaluate_bound = lambda fmt: int
    class DescriptorEvaluator:
        def __init__(self, *a, **k):
            class Ev:
                held = property(lambda self: int)
            self.evaluate_bound = Ev()
    for fake in (FunctionEvaluator, DescriptorEvaluator):
        monkeypatch.setattr(typing, "TypeVar", fake)
        with pytest.raises(RuntimeError, match="does not hold here"):
            un._const_evaluator_type()


_R26_MUTANTS = [
    ("round 25's rule: any callable evaluator is lazy",
     "            if ev is None or type(ev) is _CONST_EVALUATOR:\n                continue\n            if issubclass(type(ev), types.FunctionType):\n",
     "            if ev is None:\n                continue\n            if callable(ev):\n",
     "value"),
    ("the constant-evaluator branch dropped",
     "            if ev is None or type(ev) is _CONST_EVALUATOR:\n", "            if ev is None:\n", "eager"),
    ("the function test widened to callable",
     "            if issubclass(type(ev), types.FunctionType):\n", "            if callable(ev):\n", "other"),
    ("the refusal branch dropped (another evaluator falls through to lazy)",
     "            raise SiteUndescribed(f\"{_qualname(type(obj))}.{value}: its evaluator `{n}` is a \"",
     "            out[value] = n\n            continue\n            raise SiteUndescribed(f\"{_qualname(type(obj))}.{value}: its evaluator `{n}` is a \"",
     "other"),
]


@pytest.mark.parametrize("mutant,anchor,replacement,kind", _R26_MUTANTS, ids=[m[0] for m in _R26_MUTANTS])
def test_r26_each_evaluator_rule_is_load_bearing(mutant, anchor, replacement, kind, tmp_path, monkeypatch):
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "evalm")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    if kind == "other":
        with pytest.raises(BaseException):
            test_r26_any_other_evaluator_is_refused_by_name_never_read_as_lazy_or_eager()
        return
    if kind == "value":
        # round 27: the constant evaluator's own description now carries the held value (E1), so round 25's rule no longer
        # hides a CHANGE — drift reads through the evaluator — but it still marks the value lazy, which this cell refuses
        with pytest.raises(BaseException):
            test_r27_an_eager_value_is_described_as_a_value_not_marked_lazy()
        return
    failed = 0
    for cell in _R26_EAGER:
        try:
            test_r26_a_changed_eager_value_behind_the_constant_evaluator_is_drift(*cell)
        except BaseException:
            failed += 1
    assert failed == len(_R26_EAGER), f"{mutant}: {len(_R26_EAGER) - failed} eager cell(s) still pass"


# ---- round 27: the round-26 verdict's R26-1 — a leaf is described without executing its display code -----------------
# The describer's leaf fallback was repr(obj). CPython's constant evaluator formats the value it holds with %R, so a held
# class's metaclass __repr__ ran census code during description — a decision 0 -> 1 through the describer AND the observer.
_R27_DISPLAY = ("import typing\n\nCALLS = []\n\nclass Display(type):\n    def __repr__(cls):\n        CALLS.append('display')\n"
                "        return 'Bound'\n\nclass Bound(metaclass=Display):\n    pass\n\nclass Site:\n    param = {ctor}\n\n"
                "    def fire(self, value):\n        return len(CALLS)\n")
_R27_FORMS = [(f, c.replace("Held", "Bound")) for f, c, _u in _R26_FORMS] + [("direct control", "Bound")]
_R27_CELLS = [(f"{form} through {route}", ctor, route) for form, ctor in _R27_FORMS for route in ("site_description", "_site_realized")]


@pytest.mark.parametrize("cell,ctor,route", _R27_CELLS, ids=[c[0] for c in _R27_CELLS])
def test_r27_describing_runs_no_held_display_code(cell, ctor, route):
    """The verdict's fixture, every form, BOTH callers of the describer: the held class's display method is never entered
    and the decision it feeds is unchanged. The cell fails on the display call itself, so at the round-26 pin it fails on
    the finding, not on anything round 27 added."""
    import types as _types
    un = _load("inv7_uninstrument_r27_display", EVIDENCE / "inv7_uninstrument.py")
    mod = _types.ModuleType("review_census")
    exec(compile(_R27_DISPLAY.format(ctor=ctor), "<review_census>", "exec", dont_inherit=True), mod.__dict__)
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, cell
    if route == "site_description":
        un.site_description(mod.Site)
    else:
        observer._site_realized(mod.Site)
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, f"{cell}: describing ran the held class's display code {mod.CALLS}"


def test_r27_an_eager_value_is_described_as_a_value_not_marked_lazy():
    """Round 26's rule, asserted where it is visible: in the constructor regime the supplied value is DESCRIBED — its field
    carries the value, never the lazy marker — for all six forms."""
    import typing
    un = _load("inv7_uninstrument_r27_value", EVIDENCE / "inv7_uninstrument.py")

    class Held:
        pass
    for obj, field in ((typing.TypeVar("T", bound=Held), "__bound__"), (typing.TypeVar("T", Held, int), "__constraints__"),
                       (typing.TypeVar("T", default=Held), "__default__"), (typing.ParamSpec("P", default=Held), "__default__"),
                       (typing.TypeVarTuple("Ts", default=Held), "__default__"), (typing.TypeAliasType("A", Held), "__value__")):
        fields = dict(un._normalise(obj, {})[1])
        assert field in fields and "<lazy:" not in repr(fields[field]), (type(obj).__name__, field, fields.get(field))


def test_r27_an_unpaired_constant_evaluator_keeps_its_value_visible_and_runs_nothing():
    """The verdict: "including where an evaluator is reached outside an established value/evaluator pair". A Site holding
    the evaluator ALONE: a changed held class still describes differently, and a held display method is never entered."""
    import types as _types
    un = _load("inv7_uninstrument_r27_unpaired", EVIDENCE / "inv7_uninstrument.py")

    def site(v):
        src = ("import typing\nCALLS = []\nclass Display(type):\n    def __repr__(cls):\n        CALLS.append('display')\n"
               "        return 'H'\nclass Held(metaclass=Display):\n    def decision(self):\n        return " + str(v) + "\n"
               "class Site:\n    ev = typing.TypeVar('T', bound=Held).evaluate_bound\n")
        m = _types.ModuleType("unpaired")
        exec(compile(src, "<unpaired>", "exec", dont_inherit=True), m.__dict__)
        return m
    a, b = site(1), site(2)
    da, db = (un.site_description_digest(un.site_description(m.Site))["digest"] for m in (a, b))
    assert da != db, "a changed class behind an unpaired evaluator reads as no drift"
    assert a.CALLS == b.CALLS == [], (a.CALLS, b.CALLS)


def test_r27_a_stateless_slotted_instance_is_described_by_its_type_never_its_repr():
    """A Python class with __slots__ = () and no C base: no data descriptor, no state; its own __repr__ is never called."""
    un = _load("inv7_uninstrument_r27_slotted", EVIDENCE / "inv7_uninstrument.py")

    class Slotted:
        __slots__ = ()

        def __repr__(self):
            raise AssertionError("the describer ran the leaf's own __repr__")
    assert repr(un._normalise(Slotted(), {})) == repr(un._normalise(Slotted(), {}))


def test_r27_a_python_subclass_of_a_stateful_c_type_is_read_by_its_c_repr_or_refused():
    """The second seat's pair: `class S(itertools.count): __slots__ = ()` — S(5) and S(7) behave differently, and gc sees
    the same referents for both ([S, 1]: the counter is a C integer, not a Python object). They must describe differently,
    through count's own C repr; with a Python __repr__ the only description would execute it, so it is refused."""
    import itertools
    un = _load("inv7_uninstrument_r27_cbase", EVIDENCE / "inv7_uninstrument.py")

    class S(itertools.count):
        __slots__ = ()

    class SR(itertools.count):
        __slots__ = ()

        def __repr__(self):
            raise AssertionError("the describer ran a Python __repr__")
    assert repr(un._normalise(S(5), {})) != repr(un._normalise(S(7), {})), "hidden C state read as no drift"
    with pytest.raises(un.SiteUndescribed, match="derives from a C type that can hold state no referent shows"):
        un._normalise(SR(5), {})


def test_r27_an_interpreter_type_holding_a_non_scalar_is_refused_and_a_scalar_one_is_read():
    """E2 and E4: an immutable type with no field is read by its repr only when everything it holds is a built-in scalar —
    a lock's state still reads (locked against unlocked differ) — and refused when it holds anything else (a count whose
    step is a Fraction, whose repr the count's repr would call)."""
    import _thread, fractions, itertools
    un = _load("inv7_uninstrument_r27_leafrule", EVIDENCE / "inv7_uninstrument.py")
    free, held = _thread.allocate_lock(), _thread.allocate_lock()
    held.acquire()
    try:
        assert repr(un._normalise(free, {})) != repr(un._normalise(held, {})), "a lock's state no longer reads"
    finally:
        held.release()
    with pytest.raises(un.SiteUndescribed, match="non-scalar referent"):
        un._normalise(itertools.count(0, fractions.Fraction(1, 2)), {})


def test_r27_only_a_c_types_own_repr_slot_is_trusted_on_a_c_based_leaf():
    """What (b) trusts, all four ways it could be fooled: a Python function, a C callable that calls back into Python
    (functools.partial, operator.methodcaller) and ANOTHER type's repr slot are each refused; count's own slot, even
    assigned explicitly in the Python class, is read — it is C code formatting C state."""
    import functools, itertools, operator
    un = _load("inv7_uninstrument_r27_slot", EVIDENCE / "inv7_uninstrument.py")
    calls = []

    def py(self):
        calls.append("python")
        return "x"
    # a Python function or another type's slot reaches the leaf's repr test; a partial or a methodcaller is itself C state
    # the description is not shown to read, and is refused while the CLASS holding it is described (round 27, fail-closed)
    for label, rep_, expect in (("a Python function", py, "not its C base own repr slot"),
                                ("functools.partial of a Python function", functools.partial(py), "a C type holding instance storage"),
                                ("operator.methodcaller", operator.methodcaller("bit_length"), "a C type holding instance storage"),
                                ("another type's slot", list.__repr__, "not its C base own repr slot"),
                                ("object's slot, which prints a constant", object.__repr__, "not its C base own repr slot")):
        C = type("C", (itertools.count,), {"__slots__": (), "__repr__": rep_})
        with pytest.raises(un.SiteUndescribed, match=expect):
            un._normalise(C(5), {})
    assert calls == [], calls
    Own = type("Own", (itertools.count,), {"__slots__": (), "__repr__": itertools.count.__repr__})
    assert repr(un._normalise(Own(5), {})) != repr(un._normalise(Own(7), {}))


def test_r27_state_a_c_base_holds_and_no_field_exposes_is_refused_never_read_as_equal():
    """The second seat's stage-2 probe: a C base that ADDS instance storage and exposes none of it — `_random.Random`, the
    Mersenne-Twister state — was invisible at every pin back to the accepted round 23: random.Random(5) and
    random.Random(7) described EQUAL while they behaved differently. Now refused by name, as a field-bearing object
    (random.Random) and as a leaf (a slotted subclass, whose only C repr is object's, which prints a constant)."""
    import _random, random
    un = _load("inv7_uninstrument_r27_opaque", EVIDENCE / "inv7_uninstrument.py")

    class R(_random.Random):
        __slots__ = ()
    assert random.Random(5).random() != random.Random(7).random() and R(5).random() != R(7).random()
    with pytest.raises(un.SiteUndescribed, match="derives from _random.Random, a C type holding instance storage"):
        un._normalise(random.Random(5), {})
    with pytest.raises(un.SiteUndescribed, match="derives from _random.Random, a C type holding instance storage no field exposes"):
        un._normalise(R(5), {})


def test_r27_a_site_holding_hidden_c_state_is_refused_through_site_drift():
    """The probe's own shape, end to end: two censuses whose Site definitions are IDENTICAL and differ only in a seed their
    Site's generator holds — site_drift refuses (loudly, SiteUndescribed) rather than reporting no drift."""
    un = _load("inv7_uninstrument_r27_opaque_drift", EVIDENCE / "inv7_uninstrument.py")

    def census(seed):
        return ("import random\n\nclass Site:\n    def fire(self, value):\n        return self._rng.random()\n\n"
                f"SEED = {seed}\nSite._rng = random.Random(SEED)\n")
    with pytest.raises(un.SiteUndescribed):
        un.site_drift(census(7), census(5))


def test_r27_a_reader_types_state_change_is_drift_and_no_override_is_called():
    """Each reader: two instances that differ ONLY in their C state describe differently, and a Python subclass overriding
    the method the reader could have called is never called — the reader goes through the BASE type's own C method."""
    import array, collections, io
    un = _load("inv7_uninstrument_r27_readers", EVIDENCE / "inv7_uninstrument.py")
    d = lambda o: repr(un._normalise(o, {}))
    calls = []

    def spy(name):
        def f(self, *a, **k):
            calls.append(name)
            raise AssertionError(f"the describer called an override: {name}")
        return f
    Dq = type("Dq", (collections.deque,), {"__iter__": spy("deque.__iter__")})
    Dd = type("Dd", (collections.defaultdict,), {"items": spy("defaultdict.items"), "__iter__": spy("defaultdict.__iter__")})
    Ar = type("Ar", (array.array,), {"tolist": spy("array.tolist")})
    Si = type("Si", (io.StringIO,), {"getvalue": spy("StringIO.getvalue"), "tell": spy("StringIO.tell")})
    Bi = type("Bi", (io.BytesIO,), {"getvalue": spy("BytesIO.getvalue"), "tell": spy("BytesIO.tell")})
    pairs = [
        ("deque", collections.deque([1, 2]), collections.deque([1, 3])),
        ("deque subclass", Dq([1, 2]), Dq([1, 3])),
        ("defaultdict", collections.defaultdict(int, {"a": 1}), collections.defaultdict(int, {"a": 2})),
        ("defaultdict subclass", Dd(int, {"a": 1}), Dd(int, {"a": 2})),
        ("array", array.array("i", [1]), array.array("i", [2])),
        ("array subclass", Ar("i", [1]), Ar("i", [2])),
        ("StringIO content", io.StringIO("x"), io.StringIO("y")),
        ("StringIO subclass", Si("x"), Si("y")),
        ("BytesIO content", io.BytesIO(b"x"), io.BytesIO(b"y")),
        ("BytesIO subclass", Bi(b"x"), Bi(b"y")),
    ]
    moved = io.StringIO("xy")
    moved.seek(1)
    pairs.append(("StringIO position", io.StringIO("xy"), moved))
    for label, a, b in pairs:
        assert d(a) != d(b), f"{label}: a change of state reads as no drift"
    assert calls == [], calls


def test_r27_a_module_is_refused_before_it_is_touched():
    """Fail-closed decides from the TYPE before any read, so a refused object is never touched: a module reached by the
    description is refused, and its namespace is the same before and after (reading its annotations WRITES into it —
    round 25's A5, which this closes)."""
    import types as _types
    un = _load("inv7_uninstrument_r27_module", EVIDENCE / "inv7_uninstrument.py")
    m = _types.ModuleType("held")
    exec("x = 1\n", m.__dict__)
    before = dict(vars(m))

    class Site:
        mod = m

        def fire(self, value):
            return value
    with pytest.raises(un.SiteUndescribed, match="derives from builtins.module"):
        un.site_description(Site)
    assert dict(vars(m)) == before, sorted(set(vars(m)) ^ set(before))


def test_r27_a_held_module_level_builtin_is_refused_by_name():
    """The decided consequence (the second seat's stage-2 mark): a module-level builtin's __self__ IS its module, so a Site
    holding `len` is refused by name — loudly — rather than described through a module it cannot read."""
    un = _load("inv7_uninstrument_r27_len", EVIDENCE / "inv7_uninstrument.py")

    class Site:
        size = len

        def fire(self, value):
            return value
    with pytest.raises(un.SiteUndescribed, match="derives from builtins.module"):
        un.site_description(Site)


def test_r27_the_real_site_describes_with_zero_refusals():
    """Completeness of the allowlist for what the product needs: the reference census's Site and HEAD's describe without a
    refusal, and site_drift between them reports none — fail-closed refuses nothing the real Site holds."""
    un = _load("inv7_uninstrument_r27_real", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text(encoding="utf-8")
    head = (ROOT / "src" / "veracium" / "census.py").read_text(encoding="utf-8")
    for label, text in (("reference", ref), ("head", head)):
        un.site_description(un._realized_site(text, "real_" + label))
    assert un.site_drift(head, ref) == []


def test_r27_getsets_do_not_count_as_exposure_a_hash_is_refused():
    """The negative control: a sha256 hash exposes three getsets (name, digest_size, block_size) — 24 bytes by count, more
    than its +16 of hash state — and none of them is the state. It is refused, never read as equal."""
    import hashlib
    un = _load("inv7_uninstrument_r27_hash", EVIDENCE / "inv7_uninstrument.py")
    a, b = hashlib.sha256(b"x"), hashlib.sha256(b"y")
    assert a.digest() != b.digest()
    with pytest.raises(un.SiteUndescribed, match="a C type holding instance storage"):
        un._normalise(a, {})


_R27_MUTANTS = [
    ("the constant evaluator read through repr (E1 dropped)",
     "    if tp is _CONST_EVALUATOR:\n        if len(refs) != 1:",
     "    if False:\n        if len(refs) != 1:",
     test_r27_describing_runs_no_held_display_code),
    ("any immutable leaf read through repr (E2's scalar test dropped)",
     "        if all(_builtin(type(r), _SCALARS) for r in refs) and _repr_reads(tp, hidden):\n",
     "        if True:\n",   # round 32 retarget: the branch's return now also passes the referents through the map
     test_r27_an_interpreter_type_holding_a_non_scalar_is_refused_and_a_scalar_one_is_read),
    ("a Python-type leaf read through its repr (E3)",
     "    if not hidden and not [b for b in _mro(tp) if b is not object and _immutable(b)]:\n        return (identity, (\"referents\", tuple(_normalise(r, seen) for r in refs)))",
     "    if not hidden and not [b for b in _mro(tp) if b is not object and _immutable(b)]:\n        return (identity, _addressless(repr(obj)))",
     test_r27_a_stateless_slotted_instance_is_described_by_its_type_never_its_repr),
    ("any C callable trusted as the repr slot",
     "    c_slot = issubclass(type(found), types.WrapperDescriptorType) and getattr(found, \"__objclass__\", None) in _mro(tp) \\\n        and _repr_reads(tp, hidden)\n",
     "    c_slot = callable(found)\n",
     test_r27_only_a_c_types_own_repr_slot_is_trusted_on_a_c_based_leaf),
    ("no C base found stateful (the hidden-state rule dropped)",
     "        if _TYPE_BASICSIZE.__get__(b) - _TYPE_BASICSIZE.__get__(base) > _exposed(b):\n            out.append(b)\n",
     "        pass\n",
     test_r27_state_a_c_base_holds_and_no_field_exposes_is_refused_never_read_as_equal),
    ("any C repr slot trusted to show a stateful base's state",
     "    return owner is not None and issubclass(type(owner), type) and issubclass(owner, hidden[0])\n",
     "    return True\n",
     test_r27_only_a_c_types_own_repr_slot_is_trusted_on_a_c_based_leaf),
    ("getsets credited as exposure",
     "            + (8 if type(own.get(\"__weakref__\")) is types.GetSetDescriptorType else 0))\n",
     "            + (8 if type(own.get(\"__weakref__\")) is types.GetSetDescriptorType else 0)\n            + 8 * sum(type(x).__name__ == \"getset_descriptor\" for x in own.values()))\n",
     test_r27_getsets_do_not_count_as_exposure_a_hash_is_refused),
    ("the fail-closed check dropped (a refused object read first)",
     "        if hidden:\n            raise SiteUndescribed(f\"a {_module(tp)}.{_qualname(tp)} derives from {_module(hidden[0])}.{_qualname(hidden[0])}, \"\n                                  f\"a C type holding instance storage that neither its fields nor any reader",
     "        if False:\n            raise SiteUndescribed(f\"a {_module(tp)}.{_qualname(tp)} derives from {_module(hidden[0])}.{_qualname(hidden[0])}, \"\n                                  f\"a C type holding instance storage that neither its fields nor any reader",
     test_r27_a_module_is_refused_before_it_is_touched),
    ("a reader calls the object's own method",
     "        collections.deque: lambda obj, seen: items(collections.deque.__iter__(obj), seen),\n",
     "        collections.deque: lambda obj, seen: items(iter(obj), seen),\n",
     test_r27_a_reader_types_state_change_is_drift_and_no_override_is_called),
    ("a C-based leaf read by referents alone (the second seat's E3)",
     "    if not hidden and not [b for b in _mro(tp) if b is not object and _immutable(b)]:\n",
     "    if True:\n",
     test_r27_a_python_subclass_of_a_stateful_c_type_is_read_by_its_c_repr_or_refused),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell", _R27_MUTANTS, ids=[m[0] for m in _R27_MUTANTS])
def test_r27_each_leaf_rule_is_load_bearing(mutant, anchor, replacement, cell, tmp_path, monkeypatch):
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "leafm")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    if cell is test_r27_describing_runs_no_held_display_code:
        # the OBSERVER route loads its own inv7_uninstrument from the evidence directory, never the mutated copy, so a
        # mutant of the describer reaches the site_description cells alone: all six forms there must fail
        failed = []
        for c in _R27_CELLS:
            if c[0].startswith("direct control") or c[2] != "site_description":
                continue
            try:
                cell(*c)
            except BaseException:
                failed.append(c[0])
        assert len(failed) == len(_R27_FORMS) - 1, f"{mutant}: only {failed} failed"
        return
    with pytest.raises(BaseException):
        cell()


# ---------------------------------------------------------------------------------------------------------------------
# ROUND 28 — the round-27 verdict's two findings, widened by the second seat's stage-1 read to ONE property: THE DESCRIBER
# PERFORMS NO ATTRIBUTE LOOKUP ON WHAT IT DESCRIBES. R27-1: `getattr(v, "__qualname__", repr(v))` evaluated its default
# first, so a base's metaclass __repr__ ran during description. R27-2: a reader exempted its type's C state while reading
# content only — a StringIO's newline setting and an outstanding buffer export read as no drift.

_R28_DISPLAY_BASE = ("import typing\n\nCALLS = []\n\nclass Display(type):\n    def __repr__(cls):\n        CALLS.append('display')\n"
                     "        return 'Base'\n\nclass Base(metaclass=Display):\n    pass\n\n{body}")
_R28_PLAIN_BASE = "import typing\n\nCALLS = []\n\nclass Base:\n    pass\n\n{body}"
_R28_INHERITED = [
    # the verdict's fixture: Site itself derives from the display base
    ("Site derives from it", "class Site(Base):\n    def fire(self, value):\n        return len(CALLS)\n"),
    # the verdict's "held-class and unpaired-evaluator controls", now with the display on the held class's BASE
    ("a held class derives from it", "class Held(Base):\n    pass\n\nclass Site:\n    held = Held\n"
                                     "    def fire(self, value):\n        return len(CALLS)\n"),
    ("a TypeVar bound to a class deriving from it", "class Held(Base):\n    pass\n\nclass Site:\n"
                                                    "    param = typing.TypeVar('T', bound=Held)\n"
                                                    "    def fire(self, value):\n        return len(CALLS)\n"),
    ("an unpaired evaluator of such a class", "class Held(Base):\n    pass\n\nclass Site:\n"
                                              "    ev = typing.TypeVar('T', bound=Held).evaluate_bound\n"
                                              "    def fire(self, value):\n        return len(CALLS)\n"),
]
_R28_INHERITED_CELLS = [(f"{base}-base: {form} through {route}", base, body, route)
                        for form, body in _R28_INHERITED for base in ("display", "plain")
                        for route in ("site_description", "_site_realized")]


def _r28_module(src):
    import types as _types
    m = _types.ModuleType("review_census")
    exec(compile(src, "<review_census>", "exec", dont_inherit=True), m.__dict__)
    return m


@pytest.mark.parametrize("cell,base,body,route", _R28_INHERITED_CELLS, ids=[c[0] for c in _R28_INHERITED_CELLS])
def test_r28_describing_an_inherited_base_runs_no_display_code(cell, base, body, route):
    """R27-1, every place a display base can sit, BOTH callers: the base's metaclass __repr__ is never entered and the
    decision that counts its calls stays 0. The plain base is the control. Fails at the round-27 pin on the display call."""
    un = _load("inv7_uninstrument_r28_inherited", EVIDENCE / "inv7_uninstrument.py")
    mod = _r28_module((_R28_DISPLAY_BASE if base == "display" else _R28_PLAIN_BASE).format(body=body))
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, cell
    (un.site_description if route == "site_description" else observer._site_realized)(mod.Site)
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, f"{cell}: describing ran display code {mod.CALLS}"


def test_r28_a_mutable_base_is_still_described_in_full():
    """The verdict: "preserve the recursive description of mutable bases; do not omit their behavior to avoid the call".
    Two display bases differing only in a method describe differently — through the describer and through site_drift."""
    un = _load("inv7_uninstrument_r28_base_drift", EVIDENCE / "inv7_uninstrument.py")

    def census(v):
        return ("CALLS = []\n\nclass Display(type):\n    def __repr__(cls):\n        CALLS.append('display')\n        return 'Base'\n\n"
                f"class Base(metaclass=Display):\n    def decision(self):\n        return {v}\n\n"
                "class Site(Base):\n    def fire(self, value):\n        return self.decision()\n")
    a, b = _r28_module(census(1)), _r28_module(census(2))
    assert un.site_description(a.Site) != un.site_description(b.Site)
    assert a.CALLS == [] and b.CALLS == []
    assert un.site_drift(census(2), census(1)) != []
    assert un.site_drift(census(1), census(1)) == []


# Every way an ATTRIBUTE LOOKUP could hand control to census code, each counting its calls. The second seat's stage-1 read
# measured these at the round-27 pin: the instance-class __getattribute__ 1 call, Site's metaclass __getattribute__ 23,
# a held class's metaclass __getattribute__ 18, both callers. The `__class__` property and a slotted class with its own
# __getattribute__ were examined and entered 0 times there; they are kept as rows so a regression is seen.
_R28_LOOKUP = [
    ("a property on a held instance",
     "class P:\n    @property\n    def v(self):\n        CALLS.append('property')\n        return 1\n\n"
     "class Site:\n    held = P()\n"),
    ("a property on Site's metaclass",
     "class M(type):\n    @property\n    def v(cls):\n        CALLS.append('meta property')\n        return 1\n\n"
     "class Site(metaclass=M):\n    pass\n"),
    ("__getattribute__ on a held instance's class",
     "class H:\n    __slots__ = ('a',)\n    def __getattribute__(self, n):\n        CALLS.append(n)\n"
     "        return object.__getattribute__(self, n)\n\nh = H()\nh.a = 1\n\nclass Site:\n    held = h\n"),
    ("__getattribute__ on Site's metaclass",
     "class M(type):\n    def __getattribute__(cls, n):\n        CALLS.append(n)\n        return type.__getattribute__(cls, n)\n\n"
     "class Site(metaclass=M):\n    pass\n"),
    ("__getattribute__ on a held class's metaclass",
     "class M(type):\n    def __getattribute__(cls, n):\n        CALLS.append(n)\n        return type.__getattribute__(cls, n)\n\n"
     "class Held(metaclass=M):\n    pass\n\nclass Site:\n    held = Held\n"),
    ("a __class__ property on a held instance",
     "class W:\n    @property\n    def __class__(self):\n        CALLS.append('__class__')\n        return W\n\n"
     "class Site:\n    held = W()\n"),
    ("__getattribute__ on a held instance's slotted class, reached as a referrer",
     "class G:\n    __slots__ = ('d',)\n    def __getattribute__(self, n):\n        CALLS.append(n)\n"
     "        return object.__getattribute__(self, n)\n\nclass Site:\n    pass\n\ng = G()\ng.d = Site.__dict__\n"),
]
_R28_LOOKUP_CELLS = [(f"{row} through {route}", src, route) for row, src in _R28_LOOKUP
                     for route in ("site_description", "_site_realized")]


@pytest.mark.parametrize("cell,src,route", _R28_LOOKUP_CELLS, ids=[c[0] for c in _R28_LOOKUP_CELLS])
def test_r28_describing_performs_no_attribute_lookup_on_what_it_describes(cell, src, route):
    """The widened property (the second seat's N1): no getattr, no `x.attr`, no getattr default, on the described object
    or its class — a property is recorded and never called, and no __getattribute__ is entered, through either caller."""
    un = _load("inv7_uninstrument_r28_lookup", EVIDENCE / "inv7_uninstrument.py")
    mod = _r28_module("CALLS = []\n\n" + src)
    mod.CALLS.clear()
    (un.site_description if route == "site_description" else observer._site_realized)(mod.Site)
    assert mod.CALLS == [], f"{cell}: describing entered census code {mod.CALLS}"


def test_r28_a_property_never_called_is_still_described_by_its_code():
    """Recording a Python descriptor rather than calling it must not hide it: a changed getter — on a held instance's
    class and on Site's metaclass — describes differently."""
    un = _load("inv7_uninstrument_r28_property_drift", EVIDENCE / "inv7_uninstrument.py")
    for label, src in (("held instance", "class P:\n    @property\n    def v(self):\n        return {v}\n\nclass Site:\n    held = P()\n"),
                       ("metaclass", "class M(type):\n    @property\n    def v(cls):\n        return {v}\n\nclass Site(metaclass=M):\n    pass\n")):
        a, b = (un.site_description(_r28_module(src.format(v=v)).Site) for v in (1, 2))
        assert a != b, f"{label}: a changed property getter reads as no drift"


def test_r28_an_evaluator_served_by_a_property_is_refused_and_never_called():
    """_lazy_values reads an evaluator through `_read`: served by a Python property, it is never called to find out which
    regime it is — refused, naming the field."""
    un = _load("inv7_uninstrument_r28_evaluator_property", EVIDENCE / "inv7_uninstrument.py")
    calls = []

    class Served:
        evaluate_bound = property(lambda self: calls.append("evaluate_bound") or __import__("functools").partial(int))
        __bound__ = property(lambda self: calls.append("__bound__") or int)

    class Site:
        param = Served()

        def fire(self, value):
            return value
    with pytest.raises(un.SiteUndescribed, match=r"Served\.__bound__: its evaluator `evaluate_bound` is served by a Python descriptor"):
        un.site_description(Site)
    assert calls == [], calls


# R27-2: each pair holds EQUAL content and differs in configuration or export state; the view is retained by an ordinary
# module variable, as the verdict's fixtures do. The decision each pair feeds differs.
_R28_READER_PAIRS = [
    ("stringio_newline",
     "import io\n\nclass Site:\n    def fire(self, value):\n        self.s.seek(0)\n        self.s.write('x\\n')\n"
     "        return self.s.getvalue()\n\nSite.s = io.StringIO('seed', newline={arg})\n", "'\\n'", "'\\r\\n'"),
    ("bytesio_export",
     "import io\n\nclass Site:\n    def fire(self, value):\n        try:\n            return self.b.truncate(1)\n"
     "        except BufferError:\n            return 'BufferError'\n\nSite.b = io.BytesIO(b'xy')\nVIEW = {arg}\n",
     "None", "Site.b.getbuffer()"),
    ("array_export",
     "import array\n\nclass Site:\n    def fire(self, value):\n        try:\n            self.a.append(3)\n            return 'ok'\n"
     "        except BufferError:\n            return 'BufferError'\n\nSite.a = array.array('i', [1, 2])\nVIEW = {arg}\n",
     "None", "memoryview(Site.a)"),
    ("array_pickle_buffer_export",
     "import array, pickle\n\nclass Site:\n    def fire(self, value):\n        try:\n            self.a.append(3)\n            return 'ok'\n"
     "        except BufferError:\n            return 'BufferError'\n\nSite.a = array.array('i', [1, 2])\nVIEW = {arg}\n",
     "None", "pickle.PickleBuffer(Site.a)"),
    # the second seat's N2: universal-newline mode, the same text, a different seen-newline record — must STAY drift
    ("stringio_universal_newline",
     "import io\n\nclass Site:\n    def fire(self, value):\n        return self.s.newlines\n\n"
     "Site.s = io.StringIO(newline=None)\nSite.s.write({arg})\nSite.s.seek(0)\n", "'x\\n'", "'x\\r\\n'"),
]
_R28_READER_CELLS = [(f"{label} through {route}", label, src, a, b, route) for label, src, a, b in _R28_READER_PAIRS
                     for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,label,src,a,b,route", _R28_READER_CELLS, ids=[c[0] for c in _R28_READER_CELLS])
def test_r28_equal_content_with_different_configuration_or_export_is_drift(cell, label, src, a, b, route):
    """R27-2, every pair through all three routes: the description, the observer's digest and complete site_drift. The
    decision is asserted to differ first, so a pair that stopped demonstrating anything fails as a fixture."""
    un = _load("inv7_uninstrument_r28_readers", EVIDENCE / "inv7_uninstrument.py")
    ma, mb = _r28_module(src.format(arg=a)), _r28_module(src.format(arg=b))
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    ma, mb = _r28_module(src.format(arg=a)), _r28_module(src.format(arg=b))
    if route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(src.format(arg=b), src.format(arg=a)) != [], f"{cell}: site_drift returns []"
        assert un.site_drift(src.format(arg=a), src.format(arg=a)) == [], (cell, "a census drifts from itself")


def _r28_channels(obj):
    """THE ORACLE (the second seat's F5): every state channel a reader type has, read a SEPARATE way from the describer —
    here by ordinary attribute access, which is safe on the exact standard-library types the corpus holds. Its channels
    are the pickle state the type itself says reconstructs it, every C getset and member along its MRO (derived, never
    listed), and — for a type that exports its buffer — whether a resize would raise BufferError, found by trying one on
    the real object and undoing it."""
    import array, io, types as _types
    tp = type(obj)
    out = {}
    try:
        red = obj.__reduce_ex__(4)
        out["pickle"] = repr(tuple(list(x) if hasattr(x, "__next__") else x for x in red))
    except Exception as e:
        out["pickle"] = type(e).__name__
    for k in tp.__mro__:
        for n, d in vars(k).items():
            if isinstance(d, (_types.GetSetDescriptorType, _types.MemberDescriptorType)) and n not in ("__dict__", "__weakref__"):
                try:
                    out[f"{k.__name__}.{n}"] = repr(getattr(obj, n))
                except Exception as e:
                    out[f"{k.__name__}.{n}"] = type(e).__name__
    if tp is array.array:
        try:
            obj.append(obj[0] if len(obj) else 0)
            obj.pop()
            out["export"] = False
        except BufferError:
            out["export"] = True
    if tp is io.BytesIO:
        try:
            out["export"] = False if obj.truncate(None) is not None else None
        except BufferError:
            out["export"] = True
        except ValueError:
            out["export"] = "closed"
    return out


# channels that CANNOT vary within an exact reader type — each with the value every corpus instance must show (asserted,
# so a declared constant that starts varying fails) and why. Nothing is exempted by the shape of its name.
_R28_CONSTANT_CHANNELS = {
    **{(n, "object.__class__"): (f"<class '{m}.{n}'>", "the corpus holds exact types only; the type itself is described")
       for n, m in (("deque", "collections"), ("defaultdict", "collections"), ("array", "array"), ("StringIO", "_io"),
                    ("BytesIO", "_io"))},
    ("StringIO", "_TextIOBase.encoding"): ("None", "_io._TextIOBase's getter returns None: a StringIO holds text, not bytes"),
    ("StringIO", "_TextIOBase.errors"): ("None", "_io._TextIOBase's getter returns None, as for encoding"),
}


def _r28_reader_corpus():
    """Instances of every reader type, varying each channel the oracle names — built fresh per call, the exports held by the
    returned list so they stay outstanding."""
    import array, collections, io, pickle
    keep = []

    def exported_bytesio(v):
        b = io.BytesIO(v)
        keep.append(b.getbuffer())
        return b

    def exported_array(tc, v, how):
        a = array.array(tc, v)
        keep.append(memoryview(a) if how == "memoryview" else pickle.PickleBuffer(a) if how == "pickle" else memoryview(a)[1:])
        return a

    def closed(cls, *a):
        s = cls(*a)
        s.close()
        return s

    def at(s, pos):
        s.seek(pos)
        return s

    def universal(text):
        s = io.StringIO(newline=None)
        s.write(text)
        s.seek(0)
        return s
    corpus = {
        collections.deque: [collections.deque([1, 2]), collections.deque([1, 3]), collections.deque([1, 2], maxlen=2),
                            collections.deque([1, 2], maxlen=5), collections.deque()],
        collections.defaultdict: [collections.defaultdict(int, {"a": 1}), collections.defaultdict(list, {"a": 1}),
                                  collections.defaultdict(int, {"a": 2}), collections.defaultdict(None, {"a": 1})],
        array.array: [array.array("i", [1, 2]), array.array("i", [1, 3]), array.array("l", [1, 2]),
                      exported_array("i", [1, 2], "memoryview"), exported_array("i", [1, 2], "pickle"),
                      exported_array("i", [1, 2], "slice")],
        io.StringIO: [io.StringIO("seed"), io.StringIO("seef"), at(io.StringIO("seed"), 2), io.StringIO("seed", newline="\n"),
                      io.StringIO("seed", newline="\r\n"), io.StringIO("seed", newline=""), io.StringIO("seed", newline="\r"),
                      universal("x\n"), universal("x\r\n"), universal("x\r"), closed(io.StringIO, "seed")],
        io.BytesIO: [io.BytesIO(b"xy"), io.BytesIO(b"xz"), at(io.BytesIO(b"xy"), 1), exported_bytesio(b"xy"),
                     closed(io.BytesIO, b"xy")],
    }
    return corpus, keep


def test_r28_every_reader_state_channel_is_drift():
    """Data to data, not a hand list of cases: for every reader type, any two corpus instances the ORACLE tells apart on
    ANY channel must describe differently. And every channel the oracle derives must actually VARY somewhere in the
    corpus — a getset added to a type on a future interpreter, or a channel nobody exercised, fails here rather than
    passing as covered."""
    import itertools
    un = _load("inv7_uninstrument_r28_oracle", EVIDENCE / "inv7_uninstrument.py")
    corpus, keep = _r28_reader_corpus()
    assert set(corpus) == set(un._READERS), ("the corpus must cover every reader, and only readers", set(un._READERS) ^ set(corpus))
    unvaried, silent, used = [], [], set()
    for tp, objs in corpus.items():
        descs = [repr(un._normalise(o, {})) for o in objs]
        chans = [_r28_channels(o) for o in objs]
        for ch in chans[0]:
            values = {c.get(ch) for c in chans}
            declared = _R28_CONSTANT_CHANNELS.get((tp.__name__, ch))
            if declared is not None:
                used.add((tp.__name__, ch))
                assert values == {declared[0]}, (tp.__name__, ch, "declared constant, observed", values)
            elif len(values) < 2:
                unvaried.append(f"{tp.__name__}: {ch}")
        for (i, a), (j, b) in itertools.combinations(enumerate(chans), 2):
            if a != b and descs[i] == descs[j]:
                silent.append(f"{tp.__name__} #{i} vs #{j}: {[k for k in a if a.get(k) != b.get(k)]}")
    assert not silent, f"instances whose state differs on a channel read as no drift: {silent}"
    assert not unvaried, f"channels the corpus never varies (extend the corpus): {unvaried}"
    assert used == set(_R28_CONSTANT_CHANNELS), ("a declared constant channel no reader type has", set(_R28_CONSTANT_CHANNELS) - used)
    del keep


_R28_GUARDED = ("CALLS = []\n\nclass Getter:\n    def __call__(self, obj):\n        return 1\n    @property\n"
                "    def __isabstractmethod__(self):\n        CALLS.append('__isabstractmethod__')\n        return False\n\n"
                "class Site:\n    value = property(Getter())\n    def fire(self, value):\n        return len(CALLS)\n")


@pytest.mark.parametrize("route", ["site_description", "_site_realized"])
def test_r28_a_c_getter_that_would_run_census_code_is_refused_before_it_runs(route):
    """What no list of C getters can promise, the guard enforces: property's `__isabstractmethod__` getset looks the flag up
    on its fget — here a Python property on a callable. The describer performs no lookup itself; the C getter does. The
    Site is REFUSED, and the census code never ran (its first line was never reached), through both callers."""
    un = _load("inv7_uninstrument_r28_guard", EVIDENCE / "inv7_uninstrument.py")
    mod = _r28_module(_R28_GUARDED)
    assert mod.Site().fire(0) == 0
    # the observer loads its own copy of the describer, so its SiteUndescribed is another class of the same name
    refusal = un.SiteUndescribed if route == "site_description" else Exception
    with pytest.raises(refusal, match="would run code the describer did not write"):
        (un.site_description if route == "site_description" else observer._site_realized)(mod.Site)
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, mod.CALLS


def test_r28_a_description_the_guard_did_not_watch_to_the_end_is_refused(monkeypatch):
    """The guard proves it was alive: a description during which the tracer was unset — by a swallowed refusal, or by
    census code replacing it — is refused, not returned."""
    import sys as _sys
    un = _load("inv7_uninstrument_r28_alive", EVIDENCE / "inv7_uninstrument.py")
    real = un._site_description

    def unset(cls):
        _sys.settrace(None)
        return real(cls)
    monkeypatch.setattr(un, "_site_description", unset)

    class Site:
        def fire(self, value):
            return value
    with pytest.raises(un.SiteUndescribed, match="the guard was unset"):
        un.site_description(Site)


def test_r28_unrelated_garbage_cannot_land_inside_the_guarded_window():
    """Collection is paused for the window: cyclic garbage whose __del__ is Python code, with the collector made to run on
    every allocation, neither refuses the description nor runs inside it. Described twice, equal both times."""
    import gc
    un = _load("inv7_uninstrument_r28_gc", EVIDENCE / "inv7_uninstrument.py")
    ran = []

    class Cyclic:
        def __del__(self):
            ran.append(1)

    class Site:
        held = (1, "a", (2, 3))

        def fire(self, value):
            return value
    old = gc.get_threshold()
    try:
        gc.set_threshold(1)
        for _ in range(50):
            c = Cyclic()
            c.self = c
            del c
        first = un.site_description(Site)
        for _ in range(50):
            c = Cyclic()
            c.self = c
            del c
        second = un.site_description(Site)
    finally:
        gc.set_threshold(*old)
        gc.collect()
    assert first == second


_R28_TWO_ENTRIES = ("CALLS = []\n\nclass Getter:\n    def __call__(self, obj):\n        return 1\n    @property\n"
                    "    def __isabstractmethod__(self):\n        CALLS.append('__isabstractmethod__')\n        return False\n\n"
                    "class Site:\n    a = property(Getter())\n    b = property(Getter())\n"
                    "    def fire(self, value):\n        return len(CALLS)\n")


@pytest.mark.parametrize("route", ["site_description", "_site_realized"])
def test_r28_a_second_entry_after_a_refusal_is_stopped_too(route):
    """The refusal must not be catchable by the describer's own handlers (the second seat's stage-2 B3). Two properties,
    each of whose C `__isabstractmethod__` getter would call census code: if the first refusal were an Exception, the
    field loop's `except Exception` would record it as a raising getter, CPython would unset the tracer that raised, and
    the SECOND entry would run unwatched. As a BaseException it ends the description at the first. Both callers."""
    un = _load("inv7_uninstrument_r28_two_entries", EVIDENCE / "inv7_uninstrument.py")
    mod = _r28_module(_R28_TWO_ENTRIES)
    refusal = un.SiteUndescribed if route == "site_description" else Exception
    with pytest.raises(refusal, match="would run code the describer did not write"):
        (un.site_description if route == "site_description" else observer._site_realized)(mod.Site)
    assert mod.CALLS == [] and mod.Site().fire(0) == 0, f"census code ran after a refusal: {mod.CALLS}"


def test_r28_collection_is_paused_inside_the_guarded_window():
    """Observed, not hoped for (the second seat's stage-2 B1: the garbage cell's kill depended on the heap earlier tests
    left). A probe compiled under the DESCRIBER's own filename — so the guard lets it run — is reached from inside the
    window through a property's C `__isabstractmethod__` getter and records gc.isenabled() there: False inside, and
    collection is on again after."""
    import gc
    un = _load("inv7_uninstrument_r28_gc_probe", EVIDENCE / "inv7_uninstrument.py")
    seen = []
    ns = {"SEEN": seen, "gc": gc}
    src = ("class Probe:\n    def __call__(self, obj):\n        return 1\n    @property\n    def __isabstractmethod__(self):\n"
           "        SEEN.append(gc.isenabled())\n        return False\n")
    exec(compile(src, un._site_description.__code__.co_filename, "exec", dont_inherit=True), ns)

    class Site:
        value = property(ns["Probe"]())

        def fire(self, value):
            return value
    assert gc.isenabled(), "the test itself must start with collection on"
    un.site_description(Site)
    assert seen == [False], f"collection inside the window: {seen}"
    assert gc.isenabled(), "collection was not resumed"


def _r28_cell(fn, *args):
    return lambda: fn(*args)


_R28_MUTANTS = [
    ("R27-1: the getattr default restored",
     "        return (_module(v), _qualname(v)) if _immutable(v) else (\"mutable class\", _qualname(v))",
     "        return (v.__module__, v.__qualname__) if _immutable(v) else (\"mutable class\", getattr(v, \"__qualname__\", repr(v)))",
     _r28_cell(test_r28_describing_an_inherited_base_runs_no_display_code, "m", "display", _R28_INHERITED[0][1], "site_description"), "refused"),
    ("a C field read through getattr",
     "            return d.__get__(obj, tp)\n", "            return getattr(obj, name)\n",
     _r28_cell(test_r28_describing_performs_no_attribute_lookup_on_what_it_describes, "m", _R28_LOOKUP[2][1], "site_description"), "refused"),
    ("a Python descriptor called",
     "        return default\n    return _PYTHON_DESCRIPTOR     # a Python descriptor, or any other value a class stores under the name — None included\n", "        return default\n    return getattr(obj, name)\n",
     _r28_cell(test_r28_describing_performs_no_attribute_lookup_on_what_it_describes, "m", _R28_LOOKUP[0][1], "site_description"), "refused"),
    ("a class named through its metaclass",
     "    return _TYPE_QUALNAME.__get__(tp)\n", "    return tp.__qualname__\n",
     _r28_cell(test_r28_describing_performs_no_attribute_lookup_on_what_it_describes, "m", _R28_LOOKUP[3][1], "site_description"), "refused"),
    ("a descriptor's qualname read through its getter",
     "    return _qualname(target) + \".\" + name\n", "    return _read(obj, tp, \"__qualname__\")\n",
     _r28_cell(test_r28_describing_performs_no_attribute_lookup_on_what_it_describes, "m", _R28_LOOKUP[3][1], "site_description"), "refused"),
    ("the data-descriptor test through inspect",
     "    return _has_static(tp, \"__set__\") or _has_static(tp, \"__delete__\")\n",
     "    import inspect\n    return inspect.isdatadescriptor(d)\n",
     _r28_cell(test_r28_describing_performs_no_attribute_lookup_on_what_it_describes, "m", _R28_LOOKUP[4][1], "site_description"), "refused"),
    ("the guard never installed",
     "    sys.settrace(guard)\n", "    pass\n",
     _r28_cell(test_r28_a_c_getter_that_would_run_census_code_is_refused_before_it_runs, "site_description"), (AssertionError, "__isabstractmethod__")),
    ("the guard's liveness not checked",
     "        alive = sys.gettrace() is guard\n", "        alive = True\n",
     None, (pytest.fail.Exception, "DID NOT RAISE")),
    ("the refusal catchable as an Exception (the second seat's S3)",
     "class _ForeignFrame(BaseException):\n", "class _ForeignFrame(Exception):\n",
     _r28_cell(test_r28_a_second_entry_after_a_refusal_is_stopped_too, "site_description"), (AssertionError, "census code ran after a refusal")),
    ("collection not paused",
     "    gc.disable()\n    sys.settrace(guard)\n", "    sys.settrace(guard)\n",
     test_r28_collection_is_paused_inside_the_guarded_window, (AssertionError, "collection inside the window")),
    ("StringIO's newline not read",
     "        io.StringIO: stream(io.StringIO, lambda obj, seen: (\"newline\", _normalise(io.StringIO.__getstate__(obj)[1], seen))),\n",
     "        io.StringIO: stream(io.StringIO),\n",
     _r28_cell(test_r28_equal_content_with_different_configuration_or_export_is_drift, "m", *_R28_READER_PAIRS[0][:4], "site_description"), (AssertionError, "reads as no drift")),
    ("the export bit dropped",
     "        return (\"exported\", any(type(r) in by for r in gc.get_referrers(obj)))\n", "        return (\"exported\", False)\n",
     _r28_cell(test_r28_equal_content_with_different_configuration_or_export_is_drift, "m", *_R28_READER_PAIRS[2][:4], "site_description"), (AssertionError, "reads as no drift")),
    ("PickleBuffer not counted as an exporter",
     "(managed[0], pickle.PickleBuffer)", "(managed[0],)",
     _r28_cell(test_r28_equal_content_with_different_configuration_or_export_is_drift, "m", *_R28_READER_PAIRS[3][:4], "site_description"), (AssertionError, "reads as no drift")),
    ("the export bit dropped (the oracle alone)",
     "        return (\"exported\", any(type(r) in by for r in gc.get_referrers(obj)))\n", "        return (\"exported\", False)\n",
     test_r28_every_reader_state_channel_is_drift, (AssertionError, "read as no drift")),
    ("StringIO's newline not read (the oracle alone)",
     "        io.StringIO: stream(io.StringIO, lambda obj, seen: (\"newline\", _normalise(io.StringIO.__getstate__(obj)[1], seen))),\n",
     "        io.StringIO: stream(io.StringIO),\n",
     test_r28_every_reader_state_channel_is_drift, (AssertionError, "read as no drift")),
    ("a raising getter escapes as a crash",
     "        except Exception as e:\n            # ROUND 28: a C getter that RAISES", "        except ZeroDivisionError as e:\n            # ROUND 28: a C getter that RAISES",
     test_r28_every_reader_state_channel_is_drift, (ValueError, "closed file")),
]


_R28_GUARD_REFUSAL = "would run code the describer did not write"


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R28_MUTANTS, ids=[m[0] for m in _R28_MUTANTS])
def test_r28_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each mutant must fail its cell THE WAY IT IS NAMED FOR (the second seat's stage-2 B2): a refusal by the guard
    carrying the guard's own message, or the cell's own assertion — never any exception, which an import error in the
    mutated module would also satisfy."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "r28m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    if cell is None:   # the liveness check: a monkeypatch cell needs the mutated module's own attribute
        cell = lambda: test_r28_a_description_the_guard_did_not_watch_to_the_end_is_refused(monkeypatch)
    exc, pattern = (mut.SiteUndescribed, _R28_GUARD_REFUSAL) if expected == "refused" else expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


# ---------------------------------------------------------------------------------------------------------------------
# ROUND 29 — the round-28 verdict's R28-1: a subclass SHADOWING the descriptor that exposes instance storage hid that
# storage. The fields are read by the name the MRO resolves; a base's slot, a `__dict__`, or a C getset whose name a
# subclass reuses was never read. Widened by the second seat's stage 1: a duplicate slot (N-a) and a reader type's C getset
# (N-b). Every form, both callers and site_drift: changed description, or the named refusal — never a fixture call.

_R29_HEAD = "CALLS = []\n\n"
_R29_FORMS = [
    # (label, source, value a, value b, expected: "drift" or "refused")
    ("V1 base slot shadowed by a property",
     "class Base:\n    __slots__ = ('value',)\n\nclass Held(Base):\n    __slots__ = ()\n    @property\n    def value(self):\n"
     "        CALLS.append('property')\n        return Base.value.__get__(self)\n\nclass Site:\n    held = Held()\n"
     "    def fire(self, value):\n        return Base.value.__get__(self.held)\n\nBase.value.__set__(Site.held, {v})\n",
     "1", "2", "drift"),
    ("V2 instance dict shadowed by a property",
     "class Held:\n    @property\n    def __dict__(self):\n        CALLS.append('property')\n        return {{}}\n\n"
     "class Site:\n    held = Held()\n    def fire(self, value):\n        return self.held.value\n\n"
     "object.__setattr__(Site.held, 'value', {v})\n",
     "1", "2", "refused"),
    ("V3 base slot shadowed by a class attribute",
     "class Base:\n    __slots__ = ('value',)\n\nclass Held(Base):\n    __slots__ = ()\n    value = 0\n\nclass Site:\n"
     "    held = Held()\n    def fire(self, value):\n        return Base.value.__get__(self.held)\n\n"
     "Base.value.__set__(Site.held, {v})\n",
     "1", "2", "drift"),
    ("N-a a slot declared again by the subclass",
     "class Base:\n    __slots__ = ('value',)\n\nclass Held(Base):\n    __slots__ = ('value',)\n\nclass Site:\n    held = Held()\n"
     "    def fire(self, value):\n        return Base.value.__get__(self.held)\n\nBase.value.__set__(Site.held, {v})\n",
     "1", "2", "drift"),
    ("N-b a reader's C getset shadowed by a property",
     "import io\n\nclass Held(io.StringIO):\n    @property\n    def newlines(self):\n        CALLS.append('property')\n"
     "        return None\n\nclass Site:\n    held = Held(newline=None)\n    def fire(self, value):\n"
     "        return io.StringIO.newlines.__get__(self.held)\n\nSite.held.write({v})\nSite.held.seek(0)\n",
     "'x\\n'", "'x\\r\\n'", "drift"),
]
_R29_CONTROLS = [
    ("control: an unshadowed slot",
     "class Held:\n    __slots__ = ('value',)\n\nclass Site:\n    held = Held()\n    def fire(self, value):\n"
     "        return self.held.value\n\nSite.held.value = {v}\n", "1", "2", "drift"),
    ("control: an unshadowed dict",
     "class Held:\n    pass\n\nclass Site:\n    held = Held()\n    def fire(self, value):\n        return self.held.value\n\n"
     "Site.held.value = {v}\n", "1", "2", "drift"),
]
_R29_CELLS = [(f"{label} through {route}", label, src, a, b, want, route)
              for label, src, a, b, want in _R29_FORMS + _R29_CONTROLS
              for route in ("site_description", "_site_realized", "site_drift")]
# matched on the message's TAIL: route B's child reports stderr truncated from the front
_R29_REFUSAL = "carries the getset that exposes the dictionary"


@pytest.mark.parametrize("cell,label,src,a,b,want,route", _R29_CELLS, ids=[c[0] for c in _R29_CELLS])
def test_r29_shadowed_storage_is_read_through_its_owner_or_refused(cell, label, src, a, b, want, route):
    """R28-1 and the second seat's two further forms, through all three routes: two censuses whose Site definitions are
    identical and whose held object differs only in storage a subclass shadows must describe differently — or, where no
    C accessor reaches the storage at all (V2), be REFUSED by name. The decision is asserted to differ first, and no
    fixture code runs in either case."""
    un = _load("inv7_uninstrument_r29_shadow", EVIDENCE / "inv7_uninstrument.py")
    ma, mb = _r28_module(_R29_HEAD + src.format(v=a)), _r28_module(_R29_HEAD + src.format(v=b))
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    ma.CALLS.clear(); mb.CALLS.clear()
    sa, sb = _R29_HEAD + src.format(v=a), _R29_HEAD + src.format(v=b)
    if want == "refused":
        refusal = un.SiteUndescribed if route != "_site_realized" else Exception
        with pytest.raises(refusal, match=_R29_REFUSAL):
            if route == "site_description":
                un.site_description(ma.Site)
            elif route == "_site_realized":
                observer._site_realized(ma.Site)
            else:
                un.site_drift(sb, sa)
    elif route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(sb, sa) != [], f"{cell}: site_drift returns []"
        assert un.site_drift(sa, sa) == [], (cell, "a census drifts from itself")
    assert ma.CALLS == [] and mb.CALLS == [], f"{cell}: describing ran fixture code {ma.CALLS + mb.CALLS}"


def test_r29_an_unshadowed_object_describes_exactly_as_before():
    """The shadowed-storage entries are added ONLY where a name resolves to something other than the descriptor that owns
    the storage: an object with nothing shadowed carries no `storage.` entry, so the real Site's description — and the
    carried INV-7 run's digest — cannot move."""
    un = _load("inv7_uninstrument_r29_unshadowed", EVIDENCE / "inv7_uninstrument.py")
    for label, src, a, _b, _w in _R29_CONTROLS:
        d = repr(un.site_description(_r28_module(_R29_HEAD + src.format(v=a)).Site))
        assert "storage." not in d, (label, "an unshadowed object gained a storage entry")
    shadowed = repr(un.site_description(_r28_module(_R29_HEAD + _R29_FORMS[0][1].format(v="1")).Site))
    assert "storage." in shadowed and "Base.value" in shadowed, "the shadowed slot is not keyed by its owner"


_R29_MANAGED = [
    ("TypeVar", "typing.TypeVar('T')"),
    ("TypeVar with a bound", "typing.TypeVar('T', bound=int)"),
    ("TypeVarTuple", "typing.TypeVarTuple('Ts')"),
    ("ParamSpec", "typing.ParamSpec('P')"),
]
_R29_MANAGED_SRC = ("import typing\n\nCALLS = []\n\nclass Site:\n    held = {ctor}\n    def fire(self, value):\n"
                    "        return getattr(self.held, 'extra', None)\n\n{setup}")
_R29_MANAGED_CELLS = [(f"{label} with an attribute through {route}", ctor, route) for label, ctor in _R29_MANAGED
                      for route in ("site_description", "_site_realized", "site_drift")]
_R29_MANAGED_REFUSAL = "no accessor exposes that dictionary"


@pytest.mark.parametrize("cell,ctor,route", _R29_MANAGED_CELLS, ids=[c[0] for c in _R29_MANAGED_CELLS])
def test_r29_a_typing_objects_hidden_dict_contents_are_refused(cell, ctor, route):
    """Inside R28-1, found building its fix (the second seat's stage-1 mark B): TypeVar, TypeVarTuple and ParamSpec carry a
    managed dict that no descriptor exposes — `T.extra = 1` against `= 2` described EQUAL at the round-28 pin. The dict's
    values are visible to the collector, its keys are not, so contents beyond what the fields read are REFUSED by name,
    through all three routes."""
    un = _load("inv7_uninstrument_r29_managed", EVIDENCE / "inv7_uninstrument.py")
    sa = _R29_MANAGED_SRC.format(ctor=ctor, setup="Site.held.extra = 1\n")
    sb = _R29_MANAGED_SRC.format(ctor=ctor, setup="Site.held.extra = 2\n")
    ma, mb = _r28_module(sa), _r28_module(sb)
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    refusal = un.SiteUndescribed if route != "_site_realized" else Exception
    with pytest.raises(refusal, match=_R29_MANAGED_REFUSAL):
        if route == "site_description":
            un.site_description(ma.Site)
        elif route == "_site_realized":
            observer._site_realized(ma.Site)
        else:
            un.site_drift(sb, sa)


@pytest.mark.parametrize("label,ctor", _R29_MANAGED, ids=[m[0] for m in _R29_MANAGED])
def test_r29_a_typing_object_without_extra_attributes_is_still_described(label, ctor):
    """The acceptance half: the dict these types always carry (`__module__`, stored at construction) is accounted for, so
    an object with nothing more describes — stably, and a changed module still reads as drift."""
    un = _load("inv7_uninstrument_r29_managed_ok", EVIDENCE / "inv7_uninstrument.py")
    src = _R29_MANAGED_SRC.format(ctor=ctor, setup="")
    d1 = un.site_description(_r28_module(src).Site)
    d2 = un.site_description(_r28_module(src).Site)
    assert d1 == d2, (label, "an unchanged object describes differently")
    assert un.site_drift(src, src) == []


_R29_RESIDUE = [
    # (label, constructor, setup a, setup b, expected) — the second seat's stage-2 rows B4 and B5
    ("an extra None against none", "typing.TypeVar('T')", "Site.held.extra = None\n", "", "refused"),
    ("an extra () against none", "typing.TypeVar('T')", "Site.held.extra = ()\n", "", "refused"),
    ("a ParamSpec's extra None against none", "typing.ParamSpec('P')", "Site.held.extra = None\n", "", "refused"),
    ("__module__ changed", "typing.TypeVar('T')", "Site.held.__module__ = 'm1'\n", "Site.held.__module__ = 'm2'\n", "drift"),
]
_R29_RESIDUE_SRC = ("import typing\n\nCALLS = []\n\nclass Site:\n    held = {ctor}\n    def fire(self, value):\n"
                    "        return repr((getattr(self.held, 'extra', 'absent'), self.held.__module__))\n\n{setup}")
_R29_RESIDUE_CELLS = [(f"{label} through {route}", ctor, sa, sb, want, route) for label, ctor, sa, sb, want in _R29_RESIDUE
                      for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,ctor,sa,sb,want,route", _R29_RESIDUE_CELLS, ids=[c[0] for c in _R29_RESIDUE_CELLS])
def test_r29_a_made_up_value_absorbs_nothing_and_the_module_is_described(cell, ctor, sa, sb, want, route):
    """The residue rule's own gaps (the second seat's stage 2): a getter makes up None or () for an absent C field, and
    pooled, such a value absorbed an extra attribute holding None or () — described EQUAL. Only a field that STORES its
    value pools it (derived per type from a canonical instance). And `__module__`, the instance dict's one known entry,
    was counted but never described: a changed module read as no drift. Both through all three routes."""
    un = _load("inv7_uninstrument_r29_residue", EVIDENCE / "inv7_uninstrument.py")
    src_a, src_b = _R29_RESIDUE_SRC.format(ctor=ctor, setup=sa), _R29_RESIDUE_SRC.format(ctor=ctor, setup=sb)
    ma, mb = _r28_module(src_a), _r28_module(src_b)
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    if want == "refused":
        refusal = un.SiteUndescribed if route != "_site_realized" else Exception
        with pytest.raises(refusal, match=_R29_MANAGED_REFUSAL):
            if route == "site_description":
                un.site_description(ma.Site)
            elif route == "_site_realized":
                observer._site_realized(ma.Site)
            else:
                un.site_drift(src_a, src_b)
    elif route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(src_b, src_a) != [], f"{cell}: site_drift returns []"


@pytest.mark.parametrize("label,ctor", [("TypeVar(default=None)", "typing.TypeVar('T', default=None)"),
                                        ("ParamSpec(default=None)", "typing.ParamSpec('P', default=None)")],
                         ids=["TypeVar(default=None)", "ParamSpec(default=None)"])
def test_r29_a_stored_none_is_accounted_for_not_refused(label, ctor):
    """The acceptance half of B4, measured: `default=None` STORES None in a C field (a referent), so its read stays in
    the pool — an object with nothing extra is described, not over-refused."""
    un = _load("inv7_uninstrument_r29_stored_none", EVIDENCE / "inv7_uninstrument.py")
    src = _R29_RESIDUE_SRC.format(ctor=ctor, setup="")
    assert un.site_description(_r28_module(src).Site) == un.site_description(_r28_module(src).Site)


_R29_BY_LABEL = {label: (src, a, b, want) for label, src, a, b, want in _R29_FORMS}


def _r29_cell(label, route="site_description"):
    src, a, b, want = _R29_BY_LABEL[label]
    return lambda: test_r29_shadowed_storage_is_read_through_its_owner_or_refused("m", label, src, a, b, want, route)


_R29_MUTANTS = [
    ("storage read by name only (round 28's code)",
     "    fields += _shadowed_storage(obj, tp, is_class or wrapper, seen)\n", "",
     _r29_cell("V1 base slot shadowed by a property"), (AssertionError, "reads as no drift")),
    ("storage read by name only — the class-attribute form",
     "    fields += _shadowed_storage(obj, tp, is_class or wrapper, seen)\n", "",
     _r29_cell("V3 base slot shadowed by a class attribute"), (AssertionError, "reads as no drift")),
    ("storage read by name only — the duplicate slot",
     "    fields += _shadowed_storage(obj, tp, is_class or wrapper, seen)\n", "",
     _r29_cell("N-a a slot declared again by the subclass"), (AssertionError, "reads as no drift")),
    ("getsets excluded from the shadowed-storage read (the second seat's N-b)",
     "        for n, d in _owned(k):\n            if n == \"__weakref__\"",
     "        for n, d in [x for x in _owned(k) if type(x[1]) is not __import__(\"types\").GetSetDescriptorType]:\n            if n == \"__weakref__\"",
     _r29_cell("N-b a reader's C getset shadowed by a property"), (AssertionError, "reads as no drift")),
    ("the unreachable-dict refusal dropped",
     "    if not is_class and _dict_unreachable(tp):\n", "    if False:\n",
     _r29_cell("V2 instance dict shadowed by a property"), (pytest.fail.Exception, "DID NOT RAISE")),
    ("the managed-dict residue check dropped (the second seat's mark B)",
     "    if _managed_dict_unexposed(tp):\n        # ROUND 29 (the second seat's stage-2 B5)", "    if False:\n        # ROUND 29 (the second seat's stage-2 B5)",
     lambda: test_r29_a_typing_objects_hidden_dict_contents_are_refused("m", "typing.TypeVar('T')", "site_description"),
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("__module__ not accounted for (an empty TypeVar over-refused)",
     "        pool.append(module)\n", "        pass\n",
     lambda: test_r29_a_typing_object_without_extra_attributes_is_still_described("m", "typing.TypeVar('T')"),
     (Exception, "no accessor exposes that dictionary")),
    ("getter-made values pooled (the second seat's B4)",
     "    pool = [v for n, v in read if n in backed and not (n in fab and (v is None or (type(v) is tuple and not v)))]\n",
     "    pool = [v for n, v in read if n in backed]\n",
     lambda: test_r30_in_a_fresh_interpreter_a_made_up_value_absorbs_no_stored_one("m", "None"),
     (AssertionError, "a made-up value absorbed an extra attribute holding the same value")),
    ("__module__ counted but not described (the second seat's B5)",
     "        fields.append((\"__module__ (instance dict)\", _normalise(_refuse_unread_managed_dict(obj, tp, read), seen)))\n",
     "        _refuse_unread_managed_dict(obj, tp, read)\n",
     lambda: test_r29_a_made_up_value_absorbs_nothing_and_the_module_is_described(
         "m", "typing.TypeVar('T')", "Site.held.__module__ = 'm1'\n", "Site.held.__module__ = 'm2'\n", "drift", "site_description"),
     (AssertionError, "reads as no drift")),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R29_MUTANTS, ids=[m[0] for m in _R29_MUTANTS])
def test_r29_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each round-29 rule fails its own cell FOR THE REASON IT IS NAMED FOR (round 28's B2 discipline)."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "r29m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    exc, pattern = expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


# ---------------------------------------------------------------------------------------------------------------------
# ROUND 30 — the round-29 verdict's R29-1 (an explicit `__dict__ = None` read as an absent name, bypassing the
# unreachable-dictionary refusal) and R29-2 (the residue check dropped EVERY referent that is the object's own type).
# Both are round 29's own new state: a sentinel ambiguity in `_static`, and a filter wider than the one structural fact.

_R30_NONE_DICT = [
    # (label, class body, setup a, setup b) — two held objects whose dictionary no accessor reaches
    ("__dict__ = None, a key changed (the leaf form)", "    __dict__ = None\n",
     "Site.held.alpha = 1\n", "Site.held.beta = 1\n"),
    ("__dict__ = None beside a property, a value changed (the field form)",
     "    __dict__ = None\n    @property\n    def marker(self):\n        CALLS.append('marker')\n        return 0\n",
     "object.__setattr__(Site.held, 'value', 1)\n", "object.__setattr__(Site.held, 'value', 2)\n"),
    ("__dict__ = 0", "    __dict__ = 0\n", "Site.held.alpha = 1\n", "Site.held.beta = 1\n"),
]
_R30_NONE_SRC = ("CALLS = []\n\ndef _has(o, n):\n    try:\n        object.__getattribute__(o, n)\n        return True\n"
                 "    except AttributeError:\n        return False\n\nclass Held:\n{body}\nclass Site:\n    held = Held()\n"
                 "    def fire(self, value):\n        names = tuple(n for n in ('alpha', 'beta') if _has(self.held, n))\n"
                 "        return names + ((object.__getattribute__(self.held, 'value'),) if _has(self.held, 'value') else ())\n\n"
                 "{setup}")
_R30_NONE_CELLS = [(f"{label} through {route}", body, sa, sb, route) for label, body, sa, sb in _R30_NONE_DICT
                   for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,body,sa,sb,route", _R30_NONE_CELLS, ids=[c[0] for c in _R30_NONE_CELLS])
def test_r30_a_dictionary_no_accessor_reaches_is_refused_whatever_its_name_holds(cell, body, sa, sb, route):
    """R29-1: the refusal is decided from STORAGE and OWNED accessors, never the name — `None`, `0` and a property in the
    `__dict__` name all refuse the same way, through all three routes, running no fixture code."""
    un = _load("inv7_uninstrument_r30_none", EVIDENCE / "inv7_uninstrument.py")
    src_a, src_b = _R30_NONE_SRC.format(body=body, setup=sa), _R30_NONE_SRC.format(body=body, setup=sb)
    ma, mb = _r28_module(src_a), _r28_module(src_b)
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    ma.CALLS.clear()
    refusal = un.SiteUndescribed if route != "_site_realized" else Exception
    with pytest.raises(refusal, match=_R29_REFUSAL):
        if route == "site_description":
            un.site_description(ma.Site)
        elif route == "_site_realized":
            observer._site_realized(ma.Site)
        else:
            un.site_drift(src_b, src_a)
    assert ma.CALLS == [], ma.CALLS


def test_r30_a_dictionary_under_an_inherited_accessor_is_read_not_refused():
    """The control: `__dict__ = None` on a subclass whose BASE owns the real accessor — the dictionary is read through the
    base's getset, and a change in it is drift."""
    un = _load("inv7_uninstrument_r30_inherited", EVIDENCE / "inv7_uninstrument.py")
    src = ("CALLS = []\n\nclass Base:\n    pass\n\nclass Held(Base):\n    __dict__ = None\n\nclass Site:\n    held = Held()\n"
           "    def fire(self, value):\n        return Base.__dict__['__dict__'].__get__(self.held).get('value')\n\n"
           "Base.__dict__['__dict__'].__get__(Site.held)['value'] = {v}\n")
    a, b = src.format(v=1), src.format(v=2)
    assert un.site_description(_r28_module(a).Site) != un.site_description(_r28_module(b).Site)
    assert un.site_drift(b, a) != [] and un.site_drift(a, a) == []


def test_r30_the_leaf_refuses_an_object_with_an_instance_dictionary():
    """The belt (the second seat's stage-1 mark 1): the leaf fallback reads VALUES, never keys, so it refuses any object
    carrying instance-dictionary storage rather than describe it by its referents."""
    un = _load("inv7_uninstrument_r30_belt", EVIDENCE / "inv7_uninstrument.py")

    class Held:
        pass
    h = Held()
    h.alpha = 1
    with pytest.raises(un.SiteUndescribed, match="reached the leaf fallback"):
        un._leaf(h, Held, ("class",), {})


def test_r30_absent_is_not_a_stored_none():
    """The sentinel (R29-1's cause): a name no class defines and a name a class STORES None under are different answers."""
    un = _load("inv7_uninstrument_r30_sentinel", EVIDENCE / "inv7_uninstrument.py")

    class Stored:
        __dict__ = None
    assert un._static(Stored, "__dict__") is None
    assert un._static(Stored, "no_such_name") is un._ABSENT, "an absent name read as a stored None"


_R30_OWN_TYPE = [("TypeVar", "typing.TypeVar('T')"), ("TypeVarTuple", "typing.TypeVarTuple('Ts')"),
                 ("ParamSpec", "typing.ParamSpec('P')")]
_R30_OWN_SRC = ("import typing\n\nCALLS = []\n\nclass Site:\n    held = {ctor}\n    def fire(self, value):\n"
                "        return hasattr(self.held, 'alpha')\n\n{setup}")
_R30_OWN_CELLS = [(f"{label} through {route}", ctor, route) for label, ctor in _R30_OWN_TYPE
                  for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,ctor,route", _R30_OWN_CELLS, ids=[c[0] for c in _R30_OWN_CELLS])
def test_r30_an_attribute_holding_the_objects_own_type_is_refused(cell, ctor, route):
    """R29-2: the structural reference to the object's own type is consumed ONCE — its derived count — and a further
    occurrence (an attribute holding the type) is an ordinary value the description did not read, so it is refused."""
    un = _load("inv7_uninstrument_r30_own", EVIDENCE / "inv7_uninstrument.py")
    sa = _R30_OWN_SRC.format(ctor=ctor, setup="")
    sb = _R30_OWN_SRC.format(ctor=ctor, setup="Site.held.alpha = type(Site.held)\n")
    ma, mb = _r28_module(sa), _r28_module(sb)
    assert ma.Site().fire(0) != mb.Site().fire(0), (cell, "the pair does not change the decision")
    refusal = un.SiteUndescribed if route != "_site_realized" else Exception
    with pytest.raises(refusal, match=_R29_MANAGED_REFUSAL):
        if route == "site_description":
            un.site_description(mb.Site)
        elif route == "_site_realized":
            observer._site_realized(mb.Site)
        else:
            un.site_drift(sb, sa)


def test_r30_a_field_holding_the_objects_own_type_is_described_not_refused():
    """The verdict's acceptance half: a LEGITIMATE field holding the type — `TypeVar(bound=TypeVar)` — is a value the
    description read, so it accounts for the second occurrence; the object is described, stably, and a changed bound is
    drift."""
    un = _load("inv7_uninstrument_r30_field", EVIDENCE / "inv7_uninstrument.py")
    src = "import typing\n\nclass Site:\n    held = typing.TypeVar('T', bound={b})\n"
    own, other = src.format(b="typing.TypeVar"), src.format(b="int")
    d1, d2 = un.site_description(_r28_module(own).Site), un.site_description(_r28_module(own).Site)
    assert d1 == d2
    assert un.site_drift(other, own) != []


def test_r30_a_leaf_holding_its_own_type_is_described():
    """The leaf is the third site that filtered EVERY own-type referent (the second seat's stage-1 widening). The constant
    evaluator's traverse visits only the value it holds — its MEASURED structural count is 0, although it is a heap type
    — so an evaluator whose value is its own class is described, and differs from one holding `int`."""
    import typing
    un = _load("inv7_uninstrument_r30_leaf", EVIDENCE / "inv7_uninstrument.py")
    ce = un._CONST_EVALUATOR
    assert un._CONST_EVALUATOR_STRUCTURAL == 0

    def site(bound):
        class Site:
            ev = typing.TypeVar("T", bound=bound).evaluate_bound
        return Site
    assert un.site_description(site(ce)) != un.site_description(site(int))


_R30_FRESH_PROBE = r"""
import gc, importlib.util, sys, types
spec = importlib.util.spec_from_file_location("un_fresh", sys.argv[1]); un = importlib.util.module_from_spec(spec)
sys.modules["un_fresh"] = un; spec.loader.exec_module(un)
m = types.ModuleType("review_census"); exec(compile(sys.argv[2], "<review_census>", "exec"), m.__dict__)
held = m.Site.held
print("own-type-referents", sum(1 for r in gc.get_referents(held) if r is type(held)))
try:
    un.site_description(m.Site)
    print("described")
except un.SiteUndescribed:
    print("refused")
"""


@pytest.mark.parametrize("label,ctor", _R30_OWN_TYPE, ids=[m[0] for m in _R30_OWN_TYPE])
def test_r30_in_a_fresh_interpreter_both_own_type_occurrences_are_seen_and_refused(label, ctor):
    """R29-2 with its PRECONDITION asserted. The collector reports a managed dictionary as its VALUES only while the
    object's keys follow the order its type's shared keys expect; an earlier object of the same type that took other
    attribute names in another order makes CPython MATERIALISE this one's dictionary, and the collector then reports one
    dict instead — refused either way, but the multiplicity rule is no longer what refuses it (found running the 0042
    files in definition order: the rule's own mutant survived there and died alone). So the cell runs in a FRESH
    interpreter and first asserts that both occurrences of the type are visible, then that the object is refused."""
    un = _load("inv7_uninstrument_r30_fresh", EVIDENCE / "inv7_uninstrument.py")
    src = _R30_OWN_SRC.format(ctor=ctor, setup="Site.held.alpha = type(Site.held)\n")
    out = subprocess.run([sys.executable, "-I", "-c", _R30_FRESH_PROBE, un.__file__, src], capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    lines = out.stdout.split()
    assert out.returncode == 0 and "own-type-referents" in lines, (label, out.stderr[-400:])
    assert lines[lines.index("own-type-referents") + 1] == "2", (label, "the fresh interpreter did not show both occurrences", lines)
    assert lines[-1] == "refused", f"{label}: an attribute holding the object's own type reads as no drift in a fresh interpreter"


_R30_FRESH_MADE_UP_PROBE = r"""
import gc, importlib.util, sys, types
spec = importlib.util.spec_from_file_location("un_fresh", sys.argv[1]); un = importlib.util.module_from_spec(spec)
sys.modules["un_fresh"] = un; spec.loader.exec_module(un)
m = types.ModuleType("review_census"); exec(compile(sys.argv[2], "<review_census>", "exec"), m.__dict__)
held = m.Site.held
refs = gc.get_referents(held)
print("dict-referents", sum(1 for r in refs if type(r) is dict), "stored-value-referents", sum(1 for r in refs if r is m.EXTRA))
try:
    un.site_description(m.Site)
    print("described")
except un.SiteUndescribed:
    print("refused")
"""


@pytest.mark.parametrize("label,value", [("None", "None"), ("()", "()")], ids=["None", "()"])
def test_r30_in_a_fresh_interpreter_a_made_up_value_absorbs_no_stored_one(label, value):
    """Round 29's B4 with its PRECONDITION asserted (found on CI's floor lane, whose shuffle drew the materialised mode):
    a getter's made-up `None` or `()` must not absorb an EXTRA attribute holding the same value. That is only the
    residue rule's decision while the collector reports the dictionary as its VALUES — materialised, the object is
    refused by the one dict referent instead, and the rule's mutant survives — so the cell runs in a FRESH interpreter
    and first asserts values mode: no dict referent, and the stored value visible once."""
    un = _load("inv7_uninstrument_r30_fresh_made_up", EVIDENCE / "inv7_uninstrument.py")
    src = f"import typing\nEXTRA = {value}\n\nclass Site:\n    held = typing.TypeVar('T')\n\nSite.held.extra = EXTRA\n"
    out = subprocess.run([sys.executable, "-I", "-c", _R30_FRESH_MADE_UP_PROBE, un.__file__, src], capture_output=True,
                         text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    words = out.stdout.split()
    assert out.returncode == 0 and "dict-referents" in words, (label, out.stderr[-400:])
    assert words[words.index("dict-referents") + 1] == "0", (label, "the fresh interpreter materialised the dictionary", words)
    assert words[words.index("stored-value-referents") + 1] == "1", (label, "the stored value is not a referent", words)
    assert words[-1] == "refused", f"{label}: a made-up value absorbed an extra attribute holding the same value"


def _r30_cell(fn, *args):
    return lambda: fn(*args)


_R30_MUTANTS = [
    ("the dictionary refusal decided by the name again (R29-1)",
     "    return (_has_instance_dict(tp)\n            and not any(",
     "    return (_has_instance_dict(tp) and _static(tp, \"__dict__\") not in (None, _ABSENT)\n            and not any(",
     _r30_cell(test_r30_a_dictionary_no_accessor_reaches_is_refused_whatever_its_name_holds, "m",
               _R30_NONE_DICT[1][1], _R30_NONE_DICT[1][2], _R30_NONE_DICT[1][3], "site_description"),
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("the leaf belt dropped",
     "    if _has_instance_dict(tp):\n        raise SiteUndescribed(f\"a {_module(tp)}.{_qualname(tp)} carries an instance dictionary and reached",
     "    if False:\n        raise SiteUndescribed(f\"a {_module(tp)}.{_qualname(tp)} carries an instance dictionary and reached",
     test_r30_the_leaf_refuses_an_object_with_an_instance_dictionary, (pytest.fail.Exception, "DID NOT RAISE")),
    ("_static without its sentinel",
     "            return d[name]\n    return _ABSENT\n", "            return d[name]\n    return None\n",
     test_r30_absent_is_not_a_stored_none, (AssertionError, "an absent name read as a stored None")),
    ("every occurrence of the type filtered (R29-2)",
     "        if r is tp and left:\n", "        if r is tp:\n",
     _r30_cell(test_r30_in_a_fresh_interpreter_both_own_type_occurrences_are_seen_and_refused, "m", "typing.TypeVar('T')"),
     (AssertionError, "reads as no drift in a fresh interpreter")),
    ("no structural reference consumed (an empty instance over-refused)",
     "    left = _structural_count(tp)\n", "    left = 0\n",
     _r30_cell(test_r29_a_typing_object_without_extra_attributes_is_still_described, "m", "typing.TypeVar('T')"),
     (Exception, "no accessor exposes that dictionary")),
    ("the constant evaluator's count taken from the heap flag",
     "        return _CONST_EVALUATOR_STRUCTURAL\n", "        return 1\n",
     test_r30_a_leaf_holding_its_own_type_is_described, (Exception, "holding 0 referents")),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R30_MUTANTS, ids=[m[0] for m in _R30_MUTANTS])
def test_r30_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each round-30 rule fails its own cell FOR THE REASON IT IS NAMED FOR."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "r30m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    exc, pattern = expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


# ROUND 31 — the round-30 verdict's R30-1 and R30-2.
# R30-1: TypeVar's and ParamSpec's variance flags are C ints; their reads are the `True`/`False` singletons, stored
# nowhere, and pooled they absorbed a hidden attribute holding the same singleton. Only a field PROVEN to return a stored
# object is credited — the differential probe `_derive_backed`, primed at import. The cells run in a FRESH interpreter
# and assert values mode first (round 30's lesson: the residue rule decides only while the collector reports values).
_R31_FRESH_PROBE = r"""
import gc, importlib.util, json, sys, types
def mod(src):
    m = types.ModuleType("review_census"); exec(compile(src, "<review_census>", "exec", dont_inherit=True), m.__dict__); return m
# EVERY fixture is built BEFORE the describer is imported: the describer's import-time priming builds typing objects,
# and that history can switch LATER typing objects into materialised mode (measured, round 31) — an object built first
# keeps values mode, so the cell judges the residue rule, not the mode
a, b = sys.argv[3], sys.argv[4]
ma1, mb1, ma, mb = mod(a), mod(b), mod(a), mod(b)
def load(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m
    s.loader.exec_module(m); return m
un = load("un_fresh", sys.argv[1]); ob = load("ob_fresh", sys.argv[2])
if len(sys.argv) > 5 and sys.argv[5] == "unprime":
    import typing
    un._BACKED.pop(typing.TypeVar)
out = {"decisions": [repr(ma1.Site().fire(0)), repr(mb1.Site().fire(0))],
       "dict_referents": sum(1 for r in gc.get_referents(mb.Site.held) if type(r) is dict)}
def route(f):
    # the observer executes its OWN copy of the describer, so its refusal is another module's SiteUndescribed
    try:
        return f()
    except Exception as e:
        if type(e).__name__ != "SiteUndescribed":
            raise
        return "REFUSED"
da, db = route(lambda: un.site_description(ma.Site)), route(lambda: un.site_description(mb.Site))
out["site_description"] = "REFUSED" if "REFUSED" in (da, db) else ("DIFFER" if da != db else "EQUAL")
ra = route(lambda: ob._site_realized(ma.Site)["digest"]); rb = route(lambda: ob._site_realized(mb.Site)["digest"])
out["_site_realized"] = "REFUSED" if "REFUSED" in (ra, rb) else ("DIFFER" if ra != rb else "EQUAL")
try:
    d = un.site_drift(b, a)
    out["site_drift"] = "DRIFT" if d else "[]"
except un.SiteUndescribed:
    out["site_drift"] = "REFUSED"
print("R31", json.dumps(out))
"""
_R31_HELD = "import typing\n\nclass Site:\n    held = typing.{ctor}\n\n    def fire(self, value):\n        return {decision}\n"


def _r31_fresh(src_a, src_b, unprime=False):
    un = _load("inv7_uninstrument_r31_fresh", EVIDENCE / "inv7_uninstrument.py")
    out = subprocess.run([sys.executable, "-I", "-c", _R31_FRESH_PROBE, un.__file__, str(EVIDENCE / "inv7_observer.py"),
                          src_a, src_b] + (["unprime"] if unprime else []),
                         capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    line = next((ln for ln in out.stdout.splitlines() if ln.startswith("R31 ")), None)
    assert out.returncode == 0 and line, out.stderr[-600:]
    return json.loads(line[4:])


# the verdict's matrix: constructor x variance flag x hidden value x multiplicity. Every hidden value equals a flag's read.
_R31_SYNTH = [
    ("TypeVar, flags false, one False", 'TypeVar("T")', ["alpha = False"]),
    ("TypeVar, flags false, two False", 'TypeVar("T")', ["alpha = False", "beta = False"]),
    ("TypeVar, flags false, three False", 'TypeVar("T")', ["alpha = False", "beta = False", "gamma = False"]),
    ("TypeVar covariant, one True", 'TypeVar("T", covariant=True)', ["alpha = True"]),
    ("TypeVar contravariant, one True", 'TypeVar("T", contravariant=True)', ["alpha = True"]),
    ("TypeVar infer_variance, one True", 'TypeVar("T", infer_variance=True)', ["alpha = True"]),
    ("ParamSpec, flags false, one False", 'ParamSpec("P")', ["alpha = False"]),
    ("ParamSpec, flags false, three False", 'ParamSpec("P")', ["alpha = False", "beta = False", "gamma = False"]),
    ("ParamSpec covariant, one True", 'ParamSpec("P", covariant=True)', ["alpha = True"]),
    ("ParamSpec infer_variance, one True", 'ParamSpec("P", infer_variance=True)', ["alpha = True"]),
    # a STORED False beside a hidden one: the default is credited once, the hidden one is left over
    ("TypeVar default=False, one False", 'TypeVar("T", default=False)', ["alpha = False"]),
]


@pytest.mark.parametrize("label,ctor,setup", _R31_SYNTH, ids=[m[0] for m in _R31_SYNTH])
def test_r31_a_synthesized_boolean_read_absorbs_no_hidden_value(label, ctor, setup):
    """R30-1 through all three routes, in a fresh interpreter, values mode asserted first: a hidden attribute holding the
    Boolean a variance flag returns changes the decision, and is REFUSED, never absorbed by the flag's read."""
    a = _R31_HELD.format(ctor=ctor, decision='hasattr(self.held, "alpha")')
    b = a + "".join(f"Site.held.{s}\n" for s in setup)
    got = _r31_fresh(a, b)
    assert got["decisions"][0] != got["decisions"][1], (label, "the pair does not change the decision")
    assert got["dict_referents"] == 0, (label, "the fresh interpreter materialised the dictionary", got)
    for route in ("site_description", "_site_realized", "site_drift"):
        assert got[route] == "REFUSED", f"{label}: {route} reads {got[route]} — a synthesized read absorbed a hidden value"


_R31_STORED = [
    ("TypeVar default False/True", 'TypeVar("T", default={v})', "self.held.__default__", "False", "True"),
    ("ParamSpec default False/True", 'ParamSpec("P", default={v})', "self.held.__default__", "False", "True"),
    ("TypeVarTuple default False/True", 'TypeVarTuple("Ts", default={v})', "self.held.__default__", "False", "True"),
    ("TypeVar bound int/str", 'TypeVar("T", bound={v})', "self.held.__bound__", "int", "str"),
    ("TypeVar constraints", 'TypeVar("T", int, {v})', "self.held.__constraints__", "str", "bytes"),
]


@pytest.mark.parametrize("label,ctor,decision,va,vb", _R31_STORED, ids=[m[0] for m in _R31_STORED])
def test_r31_a_stored_default_bound_or_constraint_is_described_not_refused(label, ctor, decision, va, vb):
    """The ACCEPTANCE half: a field that STORES its value — a Boolean default, a bound, constraints — is credited, so the
    object is described and a change is drift on all three routes. Dropping every Boolean, or crediting nothing the
    guard could not prove, would refuse these."""
    a = _R31_HELD.format(ctor=ctor.format(v=va), decision=decision)
    b = _R31_HELD.format(ctor=ctor.format(v=vb), decision=decision)
    got = _r31_fresh(a, b)
    assert got["decisions"][0] != got["decisions"][1], (label, "the pair does not change the decision")
    for route in ("site_description", "_site_realized", "site_drift"):
        assert got[route] in ("DIFFER", "DRIFT"), f"{label}: {route} reads {got[route]} — a stored value is refused"


def test_r31_backed_fields_are_derived_and_primed_at_import():
    """The derivation's output on this interpreter, and its candidates found by the residue rule's own property over the
    loaded classes: the variance flags are backed nowhere; bound, constraints, default and name are, and each lazy
    evaluator (a PEP 695 type parameter stores the function its syntax compiles)."""
    import typing
    un = _load("inv7_uninstrument_r31_backed", EVIDENCE / "inv7_uninstrument.py")
    assert set(un._BACKED) == {tp for tp in un._loaded_types() if un._managed_dict_unexposed(tp)}
    assert un._BACKED[typing.TypeVar] == {"__name__", "__bound__", "__constraints__", "__default__",
                                          "evaluate_bound", "evaluate_constraints", "evaluate_default"}
    assert un._BACKED[typing.ParamSpec] == {"__name__", "__bound__", "__default__", "evaluate_default"}
    assert un._BACKED[typing.TypeVarTuple] == {"__name__", "__default__", "evaluate_default"}


def test_r31_the_sentinel_condition_rejects_a_coincident_singleton():
    """The derivation is DIFFERENTIAL, never membership: on a build that stores `False` as its default (the second seat's
    witness), every variance read is that same `False`, among the referents by coincidence. The probe credits a field
    only if it returns the build's own sentinel — so the flags stay unbacked even on that build."""
    import typing
    un = _load("inv7_uninstrument_r31_sentinel", EVIDENCE / "inv7_uninstrument.py")
    coincident = ((("_",), {"default": False}),)
    probe = typing.TypeVar("_", default=False)
    assert any(r is False for r in un._referents_but_type(probe, typing.TypeVar)), "the coincidence build stores no False"
    got = un._derive_backed(typing.TypeVar, coincident)
    assert not ({"__covariant__", "__contravariant__", "__infer_variance__"} & got), \
        f"a coincident stored singleton credited a synthesized field: {sorted(got)}"


_R31_IMPORT_PROBE = r"""
import gc, importlib.util, sys, typing
s = importlib.util.spec_from_file_location("un_fresh", sys.argv[1]); un = importlib.util.module_from_spec(s)
sys.modules["un_fresh"] = un; s.loader.exec_module(un)
assert un._BACKED, "nothing primed"
T = typing.TypeVar("T"); T.alpha = False; T.beta = False
print("dict-referents", sum(1 for r in gc.get_referents(T) if type(r) is dict))
"""


def test_r31_importing_the_describer_leaves_the_process_as_it_found_it():
    """The priming's BUILDS run in a child of the same executable: built in the described process they switched a LATER
    TypeVar with two attributes into materialised mode (measured, round 31, through a mechanism no single build
    reproduced). After the import, in a fresh interpreter, such an object still reports its dictionary as values."""
    un = _load("inv7_uninstrument_r31_import", EVIDENCE / "inv7_uninstrument.py")
    out = subprocess.run([sys.executable, "-I", "-c", _R31_IMPORT_PROBE, un.__file__], capture_output=True, text=True,
                         env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    words = out.stdout.split()
    assert out.returncode == 0 and "dict-referents" in words, out.stderr[-400:]
    assert words[words.index("dict-referents") + 1] == "0", \
        "the describer's import changed how the collector sees a later object (its dictionary is materialised)"


def test_r31_an_unprimed_type_credits_nothing_and_is_refused():
    """The FALLBACK: a type the import did not prime credits no field, so even an empty instance is refused — loud,
    never a silent credit. The primed control, in the same fresh interpreter recipe, is described."""
    src = _R31_HELD.format(ctor='TypeVar("T")', decision="1")
    assert _r31_fresh(src, src)["site_description"] == "EQUAL", "an empty primed TypeVar is not described"
    assert _r31_fresh(src, src, unprime=True)["site_description"] == "REFUSED", \
        "an unprimed type credited its fields — the fallback is not fail-closed"


# R30-2: ONE reference map across the whole description, recording identity only where identity is state.
# Each row: label, source, the post-definition line that makes two roots share one object, and a CONTENT expression that
# must be EQUAL in both sources — the pair must differ by sharing ALONE. Round 31's first method-default row set
# `__defaults__` from (None,) to a list: a content change any describer sees, so its three cells passed at the round-30
# pin and proved nothing about sharing (found by the red/green transcript's per-cell states); the precondition refuses it.
_R31_SHARED = [
    ("shared lists, compared by identity",
     "class Site:\n    left = []\n    right = []\n\n    def fire(self, value):\n        return self.left is self.right\n",
     "Site.right = Site.left\n", "(Site.left, Site.right)"),
    ("shared lists, mutated through one",
     "class Site:\n    left = []\n    right = []\n\n    def fire(self, value):\n        self.left.append(value)\n"
     "        return len(self.right)\n", "Site.right = Site.left\n", "(Site.left, Site.right)"),
    ("shared dictionaries",
     "class Site:\n    left = {}\n    right = {}\n\n    def fire(self, value):\n        return self.left is self.right\n",
     "Site.right = Site.left\n", "(Site.left, Site.right)"),
    ("a method default shared with a field",
     "class Site:\n    shared = []\n\n    def fire(self, value, box=[]):\n        return self.shared is box\n",
     "Site.shared = Site.fire.__defaults__[0]\n", "(Site.shared, Site.fire.__defaults__)"),
    # the second seat's stage-2 cross-ROOT cases (research probe r30v_probe.py): the one map spans the roots, not only
    # the members — a base's attribute, a method's closure cell, a metaclass's attribute
    ("a member shared with a base's attribute",
     "class Base:\n    shared = []\n\nclass Site(Base):\n    left = []\n\n    def fire(self, value):\n"
     "        return self.left is Base.shared\n", "Site.left = Base.shared\n", "(Site.left, Base.shared)"),
    ("a member shared with a method's closure cell",
     "def make():\n    box = []\n\n    def fire(self, value):\n        return box is self.left\n    return fire, box\n\n"
     "_f, _box = make()\n\nclass Site:\n    left = []\n    fire = _f\n", "Site.left = _box\n", "(Site.left, _box)"),
    ("a member shared with a metaclass's attribute",
     "class M(type):\n    cfg = []\n\nclass Site(metaclass=M):\n    left = []\n\n    def fire(self, value):\n"
     "        return self.left is M.cfg\n", "Site.left = M.cfg\n", "(Site.left, M.cfg)"),
]
_R31_SHARED_CELLS = [(f"{label} through {route}", label, src, setup, content, route)
                     for label, src, setup, content in _R31_SHARED
                     for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,label,src,setup,content,route", _R31_SHARED_CELLS, ids=[c[0] for c in _R31_SHARED_CELLS])
def test_r31_sharing_between_members_is_drift(cell, label, src, setup, content, route):
    """R30-2 through all three routes: the class statement is identical and a post-definition assignment makes two
    members share one object; the decision changes, and so must the description. The decisions are taken on objects
    built apart from the ones described, and again after description, so no mutation precedes the measurement."""
    un = _load("inv7_uninstrument_r31_shared", EVIDENCE / "inv7_uninstrument.py")
    a, b = src, src + setup
    first = (_r28_module(a).Site().fire(0), _r28_module(b).Site().fire(0))
    assert first[0] != first[1], (cell, "the pair does not change the decision")
    ca, cb = (eval(content, _r28_module(s).__dict__) for s in (a, b))
    assert ca == cb, (cell, "the pair differs in CONTENT, not only in sharing — any describer would see it", ca, cb)
    ma, mb = _r28_module(a), _r28_module(b)
    if route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(b, a) != [], f"{cell}: site_drift returns []"
    assert (ma.Site().fire(0), mb.Site().fire(0)) == first, (cell, "the description changed a decision")


def test_r31_sharing_controls():
    """The ACCEPTANCE halves: sharing inside ONE member was already seen and still is; two graphs built apart with the
    same sharing describe EQUAL; a content change is drift; and a VALUE is never state — a constant-folded `(1, 2)` both
    members share now describes DIFFERENTLY from an equal tuple built apart — round 31 asserted EQUAL here, the premise
    the round-31 verdict found wrong (R31-1): `a is b` tells them apart, so the sharing is state."""
    un = _load("inv7_uninstrument_r31_controls", EVIDENCE / "inv7_uninstrument.py")
    d = lambda s: un.site_description(_r28_module(s).Site)
    inner = "class Site:\n    both = [[], []]\n"
    assert d(inner) != d(inner + "Site.both[1] = Site.both[0]\n"), "sharing inside one member is no longer seen"
    graph = "class Site:\n    left = []\n    right = left\n"
    assert d(graph) == d(graph), "two equally shared graphs built apart describe differently"
    assert d("class Site:\n    left = [1]\n") != d("class Site:\n    left = [2]\n"), "a content change is not drift"
    folded = "class Site:\n    a = (1, 2)\n    b = (1, 2)\n\n    def fire(self, value):\n        return self.a is self.b\n"
    m, apart = _r28_module(folded), _r28_module(folded + "Site.b = tuple([1, 2])\n")
    assert m.Site.a is m.Site.b, "the precondition: the class body shares the folded constant"
    assert (m.Site().fire(0), apart.Site().fire(0)) == (True, False), "the pair does not change the decision"
    assert d(folded) != d(folded + "Site.b = tuple([1, 2])\n"), "a folded tuple's sharing reads as no drift"


def _r31_shared_cell(name):
    """A sharing cell by its NAME, never by position (a row inserted above would move a bare index silently)."""
    return next(c for c in _R31_SHARED_CELLS if c[0] == name)


_R31_MUTANTS = [
    ("the variance flags credited again (R30-1)",
     "    pool = [v for n, v in read if n in backed and not (n in fab",
     "    pool = [v for n, v in read if not (n in fab",
     _r30_cell(test_r31_a_synthesized_boolean_read_absorbs_no_hidden_value, *_R31_SYNTH[0]),
     (AssertionError, "a synthesized read absorbed a hidden value")),
    ("priming by plain membership",
     "            if ours(v) and any(v is r for r in refs):\n",
     "            if any(v is r for r in refs):\n",
     test_r31_the_sentinel_condition_rejects_a_coincident_singleton,
     (AssertionError, "a coincident stored singleton credited a synthesized field")),
    ("the priming dropped",
     "_BACKED = _prime_in_child([tp for tp in _loaded_types() if _managed_dict_unexposed(tp)])\n",
     "_BACKED = {}\n",
     _r30_cell(test_r31_a_stored_default_bound_or_constraint_is_described_not_refused, *_R31_STORED[3]),
     (AssertionError, "a stored value is refused")),
    ("the probe builds run in the described process",
     "_BACKED = _prime_in_child([tp for tp in _loaded_types() if _managed_dict_unexposed(tp)])\n",
     "_BACKED = {tp: _derive_backed(tp) for tp in _loaded_types() if _managed_dict_unexposed(tp)}\n",
     test_r31_importing_the_describer_leaves_the_process_as_it_found_it,
     (AssertionError, "the describer's import changed how the collector sees a later object")),
    ("a fresh map per member again (R30-2)",
     "    out += [(f\"vars.{k}\", _normal_value(x, seen)) for k, x in v.items()]\n",
     "    out += [(f\"vars.{k}\", _normal_value(x, {id(cls): 0})) for k, x in v.items()]\n",
     _r30_cell(test_r31_sharing_between_members_is_drift, *_r31_shared_cell("shared lists, compared by identity through site_description")),
     (AssertionError, "reads as no drift")),
    ("a fresh map for the bases",
     "    out += [(f\"base.{i}\", _normalise(b, seen)) for i, b in enumerate(_mro(cls)[1:], 1) if not _immutable(b)]\n",
     "    out += [(f\"base.{i}\", _normalise(b, {id(cls): 0})) for i, b in enumerate(_mro(cls)[1:], 1) if not _immutable(b)]\n",
     _r30_cell(test_r31_sharing_between_members_is_drift, *_r31_shared_cell("a member shared with a base's attribute through site_description")),
     (AssertionError, "reads as no drift")),
    # a metaclass is described through BOTH the type-level field `type.__class__` (object's getset, so every class has
    # it) and the `metaclass` entry, and each on the shared map is enough to show the sharing: a fresh map on either
    # alone survived (found writing this row, both ways round). The two are a load-bearing PAIR — neither is a
    # duplicate to be tidied away — so the mutant breaks both
    ("a fresh map for the metaclass's two roots (type.__class__ and the metaclass entry)",
     "    out += [(f\"type.{n}\", _type_level_value(cls, n, seen)) for n in _type_level_fields(type(cls))]\n"
     "    meta = type(cls)\n"
     "    out.append((\"metaclass\", (_module(meta), _qualname(meta)) if _immutable(meta) else _normalise(meta, seen)))\n",
     "    out += [(f\"type.{n}\", _type_level_value(cls, n, {id(cls): 0})) for n in _type_level_fields(type(cls))]\n"
     "    meta = type(cls)\n"
     "    out.append((\"metaclass\", (_module(meta), _qualname(meta)) if _immutable(meta) else _normalise(meta, {id(cls): 0})))\n",
     _r30_cell(test_r31_sharing_between_members_is_drift, *_r31_shared_cell("a member shared with a metaclass's attribute through site_description")),
     (AssertionError, "reads as no drift")),
    # round 31's sixth row mutated `_VALUE_CONTAINERS`, the value exemption the round-31 verdict found wrong (R31-1);
    # round 32 deleted the exemption, and its mutants are round 32's (`test_r32_each_rule_is_load_bearing`)
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R31_MUTANTS, ids=[m[0] for m in _R31_MUTANTS])
def test_r31_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each round-31 rule fails its own cell FOR THE REASON IT IS NAMED FOR."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "r31m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    exc, pattern = expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


# ROUND 32 — the round-31 verdict's R31-1: the value exemption erased observable sharing. Every object is recorded now,
# scalars included, and a set's elements are registered in an order their descriptions decide.
# Each row: label, source, the post-definition line that makes two references one object, and a CONTENT expression that
# must be EQUAL in both sources (the pair differs by identity alone). The decision is `is`, so it changes in every row.
_R32_SHARING = [
    ("runtime tuples within one member",
     "class Site:\n    pair = [tuple([1, 2]), tuple([1, 2])]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    ("runtime frozensets within one member",
     "class Site:\n    pair = [frozenset([1, 2]), frozenset([1, 2])]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    ("code objects within one member",
     "class Site:\n    pair = [compile('1', 'ordinary-held-code.py', 'eval'), compile('1', 'ordinary-held-code.py', 'eval')]\n\n"
     "    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "[eval(c) for c in Site.pair]"),
    ("runtime tuples in two members",
     "class Site:\n    a = tuple([1, 2])\n    b = tuple([1, 2])\n\n    def fire(self, value):\n        return self.a is self.b\n",
     "Site.b = Site.a\n", "(Site.a, Site.b)"),
    ("runtime frozensets in two members",
     "class Site:\n    a = frozenset([1, 2])\n    b = frozenset([1, 2])\n\n    def fire(self, value):\n        return self.a is self.b\n",
     "Site.b = Site.a\n", "(Site.a, Site.b)"),
    ("code objects in two members",
     "class Site:\n    a = compile('1', 'ordinary-held-code.py', 'eval')\n    b = compile('1', 'ordinary-held-code.py', 'eval')\n\n"
     "    def fire(self, value):\n        return self.a is self.b\n",
     "Site.b = Site.a\n", "(eval(Site.a), eval(Site.b))"),
    ("tuple wrappers around one mutable child",
     "_child = []\n\nclass Site:\n    pair = [tuple([_child]), tuple([_child])]\n\n    def fire(self, value):\n"
     "        return self.pair[0] is self.pair[1]\n", "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    # the SCALAR siblings (dev's extension of the class, stage 1): round 18's scalar exemption rested on the same premise
    ("runtime ints within one member",
     "class Site:\n    pair = [int('1' * 25), int('1' * 25)]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    ("runtime strings within one member",
     "class Site:\n    pair = [''.join(['ab', 'c']), ''.join(['ab', 'c'])]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    ("runtime bytes within one member",
     "class Site:\n    pair = [bytes([97, 98]), bytes([97, 98])]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
    ("runtime floats within one member",
     "class Site:\n    pair = [float('1.5'), float('1.5')]\n\n    def fire(self, value):\n        return self.pair[0] is self.pair[1]\n",
     "Site.pair[1] = Site.pair[0]\n", "Site.pair"),
]
_R32_SHARING_CELLS = [(f"{label} through {route}", src, setup, content, route) for label, src, setup, content in _R32_SHARING
                      for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,src,setup,content,route", _R32_SHARING_CELLS, ids=[c[0] for c in _R32_SHARING_CELLS])
def test_r32_sharing_of_an_immutable_object_is_drift(cell, src, setup, content, route):
    """R31-1 and its scalar siblings through all three routes: two equal objects built apart against one object held
    twice — equal contents, an identical class statement, a decision that turns on `is`."""
    un = _load("inv7_uninstrument_r32_sharing", EVIDENCE / "inv7_uninstrument.py")
    a, b = src, src + setup
    first = (_r28_module(a).Site().fire(0), _r28_module(b).Site().fire(0))
    assert first == (False, True), (cell, "the pair does not change the decision", first)
    ca, cb = (eval(content, _r28_module(s).__dict__) for s in (a, b))
    assert ca == cb, (cell, "the pair differs in CONTENT, not only in identity", ca, cb)
    ma, mb = _r28_module(a), _r28_module(b)
    if route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(b, a) != [], f"{cell}: site_drift returns []"
    assert (ma.Site().fire(0), mb.Site().fire(0)) == first, (cell, "the description changed a decision")


# the CANONICAL controls (the second seat's K1/K2): a small int, `()` and an interned name are ONE object whichever way
# the source reaches them, so "sharing" them changes nothing — equal on every route, although every object is recorded
_R32_CANONICAL = [
    ("a small int in two members", "class Site:\n    a = 5\n    b = int('5')\n\n    def fire(self, value):\n        return self.a is self.b\n"),
    ("the empty tuple in two members", "class Site:\n    a = ()\n    b = tuple([])\n\n    def fire(self, value):\n        return self.a is self.b\n"),
    ("an interned name in two members", "class Site:\n    a = 'name'\n    b = 'name'\n\n    def fire(self, value):\n        return self.a is self.b\n"),
]


@pytest.mark.parametrize("label,src", _R32_CANONICAL, ids=[c[0] for c in _R32_CANONICAL])
def test_r32_a_canonical_object_reads_the_same_shared_or_not(label, src):
    un = _load("inv7_uninstrument_r32_canonical", EVIDENCE / "inv7_uninstrument.py")
    b = src + "Site.b = Site.a\n"
    assert _r28_module(src).Site().fire(0) is True and _r28_module(b).Site().fire(0) is True, (label, "not canonical here")
    assert un.site_description(_r28_module(src).Site) == un.site_description(_r28_module(b).Site), f"{label}: false drift"
    assert observer._site_realized(_r28_module(src).Site)["digest"] == observer._site_realized(_r28_module(b).Site)["digest"]
    assert un.site_drift(b, src) == [], f"{label}: site_drift reports a canonical object's 'sharing'"


# THE SET'S REGISTRATION ORDER (the second seat's M2). K instances hash by address, so their set's iteration order follows
# the order they were ALLOCATED, outside the class; the Site is otherwise identical.
_R32_K = ("class K:\n    def __init__(self, name, box=None):\n        self.name = name\n        self.box = box\n\n"
          "    def __hash__(self):\n        return 1\n\n")   # one colliding hash: a set iterates in INSERTION order


# ROUND 33 — the round-32 verdict's R32-1: round 32 SORTED a set's elements, so an order that only insertion decided,
# which `next(iter(s))` observes, read as no drift. A set is now described by its WHOLE TABLE — slots in iteration order,
# and (the second seat's stage 2a) the mask, fill, used count, pop finger and dummies — where its slots follow values
# (every element value-hashed by exact type), and REFUSED where they cannot.
_R33_ORDER_TAIL = "\nclass Site:\n    s = _s\n    t = _x\n\n    def fire(self, value):\n        return next(iter(self.s)) is self.t\n"
_R33_REFUSED = [
    # the verdict's four shapes: K's hash is a Python method (census code), so its order is not a function of values
    ("the verdict's exact frozenset", _R32_K + "_x, _y = K('x'), K('y')\n", "_s = frozenset([_x, _y])\n", "_s = frozenset([_y, _x])\n"),
    ("the verdict's exact set", _R32_K + "_x, _y = K('x'), K('y')\n", "_s = set([_x, _y])\n", "_s = set([_y, _x])\n"),
    ("the verdict's frozenset subclass", _R32_K + "class FS(frozenset):\n    pass\n\n_x, _y = K('x'), K('y')\n",
     "_s = FS([_x, _y])\n", "_s = FS([_y, _x])\n"),
    ("the verdict's set subclass", _R32_K + "class SS(set):\n    pass\n\n_x, _y = K('x'), K('y')\n",
     "_s = SS([_x, _y])\n", "_s = SS([_y, _x])\n"),
    # the second seat's B4: default-hash instances (address-ordered), Ellipsis (identity-hashed); strings are described
    # (their order follows the seed, pinned in every cross-process comparison — test_r33_a_set_of_colliding_strings_...)
    ("default-hash instances", "class D:\n    pass\n\n_x, _y = D(), D()\n", "_s = frozenset([_x, _y])\n", "_s = frozenset([_y, _x])\n"),
    ("Ellipsis beside an int", "_x, _y = ..., 1\n", "_s = frozenset([_x, _y])\n", "_s = frozenset([_y, _x])\n"),
]
_R33_REFUSED_CELLS = [(f"{label} through {route}", head, a, b, route) for label, head, a, b in _R33_REFUSED
                      for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,head,a,b,route", _R33_REFUSED_CELLS, ids=[c[0] for c in _R33_REFUSED_CELLS])
def test_r33_a_set_whose_slots_are_not_its_values_is_refused(cell, head, a, b, route):
    """R32-1 through all three routes: a set of two or more elements whose iteration order an address, the hash seed or
    a census-defined hash decides is REFUSED — never described in a sorted order that erases what `next(iter(s))` sees."""
    un = _load("inv7_uninstrument_r33_refused", EVIDENCE / "inv7_uninstrument.py")
    sa, sb = head + a + _R33_ORDER_TAIL, head + b + _R33_ORDER_TAIL
    ma = _r28_module(sa)
    assert len(ma.Site.s) == 2, (cell, "the fixture's set does not hold two elements")
    with pytest.raises(Exception, match="refused") as got:
        if route == "site_description":
            un.site_description(ma.Site)
        elif route == "_site_realized":
            observer._site_realized(ma.Site)
        else:
            un.site_drift(sb, sa)
    assert type(got.value).__name__ == "SiteUndescribed", (cell, type(got.value))


_R33_VALUE_ORDER = "_s = {ctor}([{a}, {b}])\n\nclass Site:\n    s = _s\n\n    def fire(self, value):\n        return next(iter(self.s)) == 8\n"
_R33_DESCRIBED = [
    ("ints 8/16 against 16/8", "", "frozenset"),
    ("ints in a frozenset subclass", "class FS(frozenset):\n    pass\n\n", "FS"),
    ("ints in a set", "", "set"),
]
_R33_DESCRIBED_CELLS = [(f"{label} through {route}", head, ctor, route) for label, head, ctor in _R33_DESCRIBED
                        for route in ("site_description", "_site_realized", "site_drift")]


@pytest.mark.parametrize("cell,head,ctor,route", _R33_DESCRIBED_CELLS, ids=[c[0] for c in _R33_DESCRIBED_CELLS])
def test_r33_a_set_of_value_hashed_elements_is_described_by_its_table(cell, head, ctor, route):
    """The POSITIVE half (the second seat's B2): a set of ints — value-hashed, so their order is a function of the values
    and the insertion history — is described in ITERATION order, so two insertion orders that `next(iter(s))` tells apart
    are drift through all three routes; the same source is not."""
    un = _load("inv7_uninstrument_r33_described", EVIDENCE / "inv7_uninstrument.py")
    sa = head + _R33_VALUE_ORDER.format(ctor=ctor, a=8, b=16)
    sb = head + _R33_VALUE_ORDER.format(ctor=ctor, a=16, b=8)
    ma, mb = _r28_module(sa), _r28_module(sb)
    assert list(ma.Site.s) != list(mb.Site.s), (cell, "the fixture did not produce two iteration orders")
    assert (ma.Site().fire(0), mb.Site().fire(0)) == (True, False), (cell, "the pair does not change the decision")
    if route == "site_description":
        assert un.site_description(ma.Site) != un.site_description(mb.Site), f"{cell}: reads as no drift"
        assert un.site_description(ma.Site) == un.site_description(_r28_module(sa).Site), (cell, "the same source differs")
    elif route == "_site_realized":
        assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"], f"{cell}: equal digests"
    else:
        assert un.site_drift(sb, sa) != [], f"{cell}: site_drift returns []"
        for _ in range(3):
            assert un.site_drift(sa, sa) == [], (cell, "site_drift between identical sources")


def test_r33_a_set_of_address_hashed_elements_is_refused():
    """The successor of round 32's `..._are_registered_in_an_order_their_descriptions_decide`: instances with the
    default hash iterate by ADDRESS, which one description cannot hold across processes — refused."""
    un = _load("inv7_uninstrument_r33_address", EVIDENCE / "inv7_uninstrument.py")
    src = "class D:\n    pass\n\nclass Site:\n    s = frozenset([D(), D()])\n"
    with pytest.raises(un.SiteUndescribed, match="does not follow its value alone"):
        un.site_description(_r28_module(src).Site)


def test_r33_a_set_subclass_is_described_by_its_table():
    """The successor of round 32's set-subclass ordering cell: `_base_content`'s set-subclass branch describes a subclass
    of ints in ITERATION order too — two insertion orders differ."""
    un = _load("inv7_uninstrument_r33_subclass", EVIDENCE / "inv7_uninstrument.py")
    head = "class FS(frozenset):\n    pass\n\n"
    ma = _r28_module(head + _R33_VALUE_ORDER.format(ctor="FS", a=8, b=16))
    mb = _r28_module(head + _R33_VALUE_ORDER.format(ctor="FS", a=16, b=8))
    assert list(ma.Site.s) != list(mb.Site.s), "the fixture did not produce two iteration orders"
    assert un.site_description(ma.Site) != un.site_description(mb.Site), "a set subclass's iteration order was erased"


def _r33_colliding_strings():
    """Two runtime strings that share a slot in a two-element set's table UNDER THIS PROCESS'S SEED, so their iteration
    order follows insertion (without a collision it follows the hashes alone) — found by measurement, and asserted."""
    for i in range(2, 4000):
        a, b = "".join(["s", "1"]), "".join(["s", str(i)])
        if (hash(a) & 7) == (hash(b) & 7) and list(frozenset([a, b])) != list(frozenset([b, a])):
            return "s1", f"s{i}"
    raise AssertionError("no colliding pair found")


_R33_STRINGS = ("_s = frozenset([''.join(['s', '{a}']), ''.join(['s', '{b}'])])\n\nclass Site:\n    s = _s\n\n"
                "    def fire(self, value):\n        return next(iter(self.s)) == 's{a}'\n")


def test_r33_a_set_of_colliding_strings_is_described_by_its_table():
    """R32-1 for strings, in one process (one seed): two insertion orders of a colliding pair iterate differently, and
    `next(iter(s))` sees it, so the description and the observer's digest differ; the same source does not."""
    un = _load("inv7_uninstrument_r33_strings", EVIDENCE / "inv7_uninstrument.py")
    a, b = _r33_colliding_strings()
    src_ab = _R33_STRINGS.format(a=a[1:], b=b[1:])
    src_ba = src_ab.replace(f"[''.join(['s', '{a[1:]}']), ''.join(['s', '{b[1:]}'])]", f"[''.join(['s', '{b[1:]}']), ''.join(['s', '{a[1:]}'])]")
    assert src_ab != src_ba
    ma, mb = _r28_module(src_ab), _r28_module(src_ba)
    assert list(ma.Site.s) != list(mb.Site.s), "the precondition: the two insertion orders iterate differently"
    # WHICH order decides True follows this process's seed (it failed one suite run hard-coded as (True, False)); the
    # property is that the two decisions DIFFER
    assert ma.Site().fire(0) != mb.Site().fire(0), "the pair does not change the decision"
    assert un.site_description(ma.Site) != un.site_description(mb.Site), "a string set's iteration order was erased"
    assert observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"]
    assert un.site_description(ma.Site) == un.site_description(_r28_module(src_ab).Site), "the same source differs"


_R33_SEED0_PAIR = (
    "for i in range(2, 4000):\n"
    "    a, b = ''.join(['s', '1']), ''.join(['s', str(i)])\n"
    "    if (hash(a) & 7) == (hash(b) & 7) and list(frozenset([a, b])) != list(frozenset([b, a])):\n"
    "        print(i); break\n")


def test_r33_route_b_describes_colliding_strings_in_seed_zero_order():
    """Through route B, whose children run under PYTHONHASHSEED=0 and assert it: a pair colliding UNDER SEED 0, in two
    insertion orders, is drift; the same source through two children, three times, is not."""
    un = _load("inv7_uninstrument_r33_routeb", EVIDENCE / "inv7_uninstrument.py")
    out = subprocess.run([sys.executable, "-c", _R33_SEED0_PAIR], capture_output=True, text=True,
                         env={**os.environ, "PYTHONHASHSEED": "0"})
    i = out.stdout.strip()
    assert out.returncode == 0 and i.isdigit(), out.stderr[-300:]
    src_ab = _R33_STRINGS.format(a="1", b=i)
    src_ba = src_ab.replace(f"[''.join(['s', '1']), ''.join(['s', '{i}'])]", f"[''.join(['s', '{i}']), ''.join(['s', '1'])]")
    assert src_ab != src_ba
    assert un.site_drift(src_ba, src_ab) != [], "route B erased a string set's seed-0 iteration order"
    for _ in range(3):
        assert un.site_drift(src_ab, src_ab) == [], "route B finds drift between identical sources"


def test_r33_route_b_refuses_a_child_that_is_not_isolated():
    """The second seat's B-b: route B's child asserts its own isolation — no script directory or user site on the path,
    no PYTHON* variable but the pinned seed, hash randomization off — before it describes. Run as `-I` (which ignores
    PYTHONHASHSEED), the child refuses and says which condition failed."""
    import tempfile
    un = _load("inv7_uninstrument_r33_isolation", EVIDENCE / "inv7_uninstrument.py")
    with tempfile.TemporaryDirectory() as d:
        resp = pathlib.Path(d) / "r.json"
        subprocess.run([sys.executable, "-I", "-B", "-c", un._ISOLATED_CHILD, str(pathlib.Path(un.__file__).resolve()),
                        str(resp)], input=b"class Site:\n    pass\n", capture_output=True, timeout=120)
        body = json.loads(resp.read_text(encoding="ascii"))
    assert isinstance(body, str) and "not isolated" in body and "hash_randomization == 0" in body, body


_R33_ARM_PROBE = (
    "import importlib.util, sys\n"
    "s = importlib.util.spec_from_file_location('inv7_observer_probe', sys.argv[1]); o = importlib.util.module_from_spec(s)\n"
    "sys.modules['inv7_observer_probe'] = o; s.loader.exec_module(o)\n"
    "o._arm_setup()\nprint('SET UP')\n")


def test_r33_an_arm_refuses_an_unpinned_seed():
    """The INV-7 arms compare Sites across processes AND sources (the uninstrumented pair imports the twin's), so an arm
    asserts its own pinned seed before it describes: unpinned, `_arm_setup` refuses; under seed 0 it sets up."""
    un = _load("inv7_uninstrument_r33_arm", EVIDENCE / "inv7_uninstrument.py")
    obs = pathlib.Path(un.__file__).resolve().parent / "inv7_observer.py"
    base = {k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}
    base.update({"INV7_ARM": "off", "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"})
    unpinned = subprocess.run([sys.executable, "-c", _R33_ARM_PROBE, str(obs)], capture_output=True, text=True, env=base)
    assert unpinned.returncode != 0 and "not pinned to 0" in unpinned.stderr, \
        ("an unpinned arm was set up", unpinned.stdout[-200:], unpinned.stderr[-300:])
    pinned = subprocess.run([sys.executable, "-c", _R33_ARM_PROBE, str(obs)], capture_output=True, text=True,
                            env={**base, "PYTHONHASHSEED": "0"})
    assert pinned.returncode == 0 and "SET UP" in pinned.stdout, pinned.stderr[-300:]


def test_r33_a_set_holding_nan_is_refused():
    """The second seat's B1: NaN hashes by IDENTITY, so a set holding NaN — even inside a tuple — is refused."""
    un = _load("inv7_uninstrument_r33_nan", EVIDENCE / "inv7_uninstrument.py")
    for s in ("frozenset([float('nan'), float('nan')])", "frozenset([(1, float('nan')), (2, 3)])"):
        with pytest.raises(un.SiteUndescribed, match="does not follow its value alone"):
            un.site_description(_r28_module(f"class Site:\n    s = {s}\n").Site)


def test_r33_an_int_subclass_with_its_own_hash_is_refused():
    """The second seat's B3: the type test is EXACT — an int subclass may define `__hash__`, census code."""
    un = _load("inv7_uninstrument_r33_intsub", EVIDENCE / "inv7_uninstrument.py")
    src = "class I(int):\n    def __hash__(self):\n        return 1\n\nclass Site:\n    s = frozenset([I(1), I(2)])\n"
    with pytest.raises(un.SiteUndescribed, match="does not follow its value alone"):
        un.site_description(_r28_module(src).Site)


def test_r33_a_set_of_one_address_hashed_element_is_refused():
    """The second seat's stage-2a R3: ONE element's slot is its hash masked by the table, and a default hash is an
    address, so a set of one instance is refused too (round 33 had described it, as a set with a single order)."""
    un = _load("inv7_uninstrument_r33_one", EVIDENCE / "inv7_uninstrument.py")
    with pytest.raises(un.SiteUndescribed, match="does not follow its value alone"):
        un.site_description(_r28_module("class D:\n    pass\n\nclass Site:\n    s = frozenset([D()])\n").Site)


def test_r33_an_empty_set_and_a_set_of_one_value_are_described():
    """The ACCEPTANCE half of the refusal: an empty set, and a set of one value-hashed element, are described."""
    un = _load("inv7_uninstrument_r33_one_ok", EVIDENCE / "inv7_uninstrument.py")
    un.site_description(_r28_module("class Site:\n    s = set()\n    f = frozenset()\n    t = {'x'}\n    u = frozenset([1])\n").Site)



# ROUND 33, the second seat's stage 2a (on the R32-1 fix 4580f33f): a set's TABLE is state beyond its elements and their
# iteration order. Each pair holds equal elements in EQUAL iteration order (asserted) and differs in the table alone.
_R33_TABLE = [
    # (label, the pair's two constructions of _s, the decision, whether the pair must differ)
    ("W1 a set popped and refilled", "_s = {0, 1, 2, 3}\n", "_s = {0, 1, 2, 3}\n_s.pop()\n_s.add(0)\n",
     "        return self.s.pop()\n", True),
    ("W2 an emptied set that once held forty", "_s = set()\n",
     "_s = set(range(40))\nfor _x in range(40):\n    _s.discard(_x)\n",
     "        self.s.add(16)\n        self.s.add(8)\n        return next(iter(self.s))\n", True),
    ("W3 a frozenset's layout", "_s = frozenset([16, 14, 38])\n", "_s = frozenset([16, 38, 14])\n",
     "        t = set(self.s)\n        t.add(0)\n        return list(t)[1]\n", True),
    # dev's, for the mask alone: the same five slots, fill, used and finger, in a table of 32 (grown by adds) against 16
    # (made by one merge) — the next two adds land in another order
    ("W4 a table grown by adds against one made by merge", "_s = set([0, 1, 2, 3, 4])\n", "_s = set({0, 1, 2, 3, 4})\n",
     "        self.s.add(21)\n        self.s.add(16)\n        return list(self.s)[5]\n", True),
    # the second seat's stage 2b, for the dummies alone: equal mask, fill, used, finger and live slot, dummies at (0, 6)
    # against (1, 2) under seed-free int hashes — one add lands before the live element in one and after it in the other
    ("W5 dummies at other slots", "_s = set()\nfor _x in (4, 14, 32):\n    _s.add(_x)\n_s.discard(14)\n_s.discard(32)\n",
     "_s = set()\nfor _x in (57, 4, 58):\n    _s.add(_x)\n_s.discard(57)\n_s.discard(58)\n",
     "        self.s.add(38)\n        return next(iter(self.s))\n", True),
    ("K1 two equal fresh sets", "_s = {0, 1, 2, 3}\n", "_s = {0, 1, 2, 3}\n", "        return self.s.pop()\n", False),
]
_R33_TABLE_CELLS = [(f"{label} through {route}", a, b, decide, differ, route)
                    for label, a, b, decide, differ in _R33_TABLE for route in ("site_description", "_site_realized", "site_drift")]


def _r33_table_source(pre, decide):
    return pre + "\nclass Site:\n    s = _s\n\n    def fire(self, value):\n" + decide


@pytest.mark.parametrize("cell,a,b,decide,differ,route", _R33_TABLE_CELLS, ids=[c[0] for c in _R33_TABLE_CELLS])
def test_r33_a_sets_table_is_state(cell, a, b, decide, differ, route):
    """The second seat's W1–W3 and K1 through all three routes: equal elements in equal iteration order, and a table
    that differs — the slot `pop()` resumes from, a grown table kept after its elements were discarded, a frozenset's
    slots (which `set(fs)` copies) — changes the decision and is drift; two equal fresh sets decide alike and are not."""
    un = _load("inv7_uninstrument_r33_table", EVIDENCE / "inv7_uninstrument.py")
    sa, sb = _r33_table_source(a, decide), _r33_table_source(b, decide)
    ma, mb = _r28_module(sa), _r28_module(sb)
    assert list(ma.Site.s) == list(mb.Site.s), (cell, "the precondition: equal iteration order")
    assert set(ma.Site.s) == set(mb.Site.s), (cell, "the precondition: equal elements")
    decisions = (_r28_module(sa).Site().fire(0), _r28_module(sb).Site().fire(0))   # fresh modules: fire mutates the set
    assert (decisions[0] != decisions[1]) == differ, (cell, "the pair's decisions", decisions)
    if route == "site_description":
        got = un.site_description(ma.Site) != un.site_description(mb.Site)
    elif route == "_site_realized":
        got = observer._site_realized(ma.Site)["digest"] != observer._site_realized(mb.Site)["digest"]
    else:
        got = un.site_drift(sb, sa) != []
    assert got == differ, f"{cell}: " + ("reads as no drift" if differ else "equal sets read as drift")



_R33_DICT_HISTORIES = [
    "_d = {}\n",
    "_d = {i: i for i in range(40)}\nfor _i in range(40):\n    del _d[_i]\n",
    "_d = {0: 0, 1: 1}\ndel _d[0]\n_d.popitem()\n",
    "_d = {i: i for i in range(40)}\n_d.clear()\n",
]
_R33_DICT_DECIDE = ("\nclass Site:\n    d = _d\n\n    def fire(self, value):\n        d, out = self.d, [list(self.d)]\n"
                    "        d['c'] = 3\n        d[16] = 0\n        d[8] = 0\n        out.append(list(d))\n"
                    "        out.append(d.popitem())\n        d['z'] = 0\n        out.append(list(d))\n"
                    "        del d['a']\n        d['a'] = 9\n        out.append(list(d.items()))\n        return out\n")


def test_r33_a_dicts_table_history_is_not_order_state():
    """The second seat's N3, measured and asserted: a dict's table (grown and emptied, popped, cleared) changes NO order
    a decision sees — iteration, adds after it, popitem, delete-and-reinsert all follow insertion order, which the
    description holds — so equal insertion histories of the live keys decide alike AND describe alike. Only
    `sys.getsizeof` tells them apart: the allocation surface, named, not described (like `id()`)."""
    un = _load("inv7_uninstrument_r33_dict", EVIDENCE / "inv7_uninstrument.py")
    srcs = [h + "_d['a'] = 1\n_d['b'] = 2\n" + _R33_DICT_DECIDE for h in _R33_DICT_HISTORIES]
    decisions = [_r28_module(s).Site().fire(0) for s in srcs]
    assert all(d == decisions[0] for d in decisions), ("a dict's table history changed a decision", decisions)
    assert len({sys.getsizeof(_r28_module(s).Site.d) for s in srcs}) > 1, "the precondition: the tables differ"
    descs = [un.site_description(_r28_module(s).Site) for s in srcs]
    assert all(d == descs[0] for d in descs), "equal dicts with different table histories read as drift"

def test_r33_a_frozensets_slots_are_what_differs():
    """W3's REASON, at slot level: the two frozensets iterate alike, and their slots differ — the description names the
    slot each element holds, which iteration order alone does not."""
    un = _load("inv7_uninstrument_r33_slots", EVIDENCE / "inv7_uninstrument.py")
    a, b = frozenset([16, 14, 38]), frozenset([16, 38, 14])
    assert list(a) == list(b), "the precondition: equal iteration order"
    sa, sb = un._set_table(a, list(a))[4], un._set_table(b, list(b))[4]
    ids = {id(x): x for x in a}
    assert [ids[k] for _, k in sa] == [ids[k] for _, k in sb] == list(a), "slots in slot order are the iteration order"
    assert [i for i, _ in sa] != [i for i, _ in sb], "the two frozensets' slots do not differ"
    da = un._set_elements(a, frozenset, {})
    db = un._set_elements(b, frozenset, {})
    assert da != db and da[:4] == db[:4], ("the description differs by the slots alone", da, db)



def test_r33_a_sets_dummies_are_what_differs():
    """W5's REASON, field by field: the two sets agree in mask, fill, used, finger and every live slot, and differ in
    where their dummies sit — the one table field no other witness isolates (W1 the finger, W3 the live slots, W4 the
    mask)."""
    un = _load("inv7_uninstrument_r33_dummies", EVIDENCE / "inv7_uninstrument.py")
    row = next(r for r in _R33_TABLE if r[0].startswith("W5"))
    a, b = (_r28_module(_r33_table_source(pre, row[3])).Site.s for pre in row[1:3])
    ta, tb = un._set_table(a, list(a)), un._set_table(b, list(b))
    assert ta[:4] == tb[:4], ("the precondition: equal fill, used, mask and finger", ta[:4], tb[:4])
    live = lambda tab: [i for i, k in tab[4] if k != un._SET_DUMMY]
    dead = lambda tab: [i for i, k in tab[4] if k == un._SET_DUMMY]
    assert live(ta) == live(tb), "the precondition: equal live slots"
    assert dead(ta) and dead(tb) and dead(ta) != dead(tb), ("the dummies' slots do not differ", dead(ta), dead(tb))
    assert un._set_elements(a, set, {}) != un._set_elements(b, set, {}), "the dummies' slots were not described"


def test_r33_a_dummy_read_as_empty_is_refused():
    """The second seat's stage-2b C3: a dummy slot misread as EMPTY leaves the live keys and the used count right, and
    only the occupied-slot count against fill catches it — so the reader refuses rather than describe a table with a
    slot missing."""
    un = _load("inv7_uninstrument_r33_lostdummy", EVIDENCE / "inv7_uninstrument.py")
    s = {4, 14, 32}
    s.discard(14)
    real = un._set_keys

    def lossy(table, mask):
        keys = list(real(table, mask))
        keys[next(i for i, k in enumerate(keys) if k == un._SET_DUMMY)] = 0
        return tuple(keys)
    with pytest.MonkeyPatch.context() as monkeypatch:   # a context, not the fixture: the mutant table calls this cell
        monkeypatch.setattr(un, "_set_keys", lossy)
        with pytest.raises(un.SiteUndescribed, match="did not read consistently"):
            un._set_table(s, list(s))

def test_r33_a_dummy_left_by_an_address_hashed_element_is_described():
    """The named residual: an EMPTY set whose dummies were left by discarding default-hash instances holds no element to
    refuse; its dummies' slots are recorded as they are (so the description is faithful in one process). Their slots
    follow those instances' addresses, so across processes the description may vary — reported by the 8-run gate as
    instability, never as silence (measured stable over 12 processes on 3.14.7; not asserted)."""
    un = _load("inv7_uninstrument_r33_dummy", EVIDENCE / "inv7_uninstrument.py")
    src = ("class D:\n    pass\n\n_s = set()\n_xs = [D() for _ in range(3)]\nfor _x in _xs:\n    _s.add(_x)\n"
           "for _x in _xs:\n    _s.discard(_x)\n\nclass Site:\n    s = _s\n")
    site = _r28_module(src).Site
    got = un._set_elements(site.s, set, {})
    assert got[2] == ("used", 0) and got[4] and all(v == "<dummy>" for _, v in got[4]), got
    assert un.site_description(site) != un.site_description(_r28_module("class Site:\n    s = set()\n").Site), \
        "the dummies were not described"


def test_r33_a_table_that_changes_while_read_is_refused():
    """The second seat's N1 (a torn read): a census thread mutating the set between the reader's two reads. The reader
    reads header and slots twice; a change between them refuses."""
    un = _load("inv7_uninstrument_r33_torn", EVIDENCE / "inv7_uninstrument.py")
    real, calls = un._set_header, []

    def moving(obj):
        calls.append(obj)
        h = real(obj)
        return h if len(calls) == 1 else (h[0], h[1], h[2], h[3], h[4] + 1)
    with pytest.MonkeyPatch.context() as monkeypatch:   # a context, not the fixture: the mutant table calls this cell
        monkeypatch.setattr(un, "_set_header", moving)
        with pytest.raises(un.SiteUndescribed, match="did not read consistently"):
            un._set_table({1, 2}, [1, 2])


def test_r33_an_unproven_reader_refuses_every_set(monkeypatch):
    """Fail-closed: when the import-time check did not prove the layout, a set is refused and the check's reason named."""
    un = _load("inv7_uninstrument_r33_unproven", EVIDENCE / "inv7_uninstrument.py")
    monkeypatch.setattr(un, "_SET_DUMMY", None)
    monkeypatch.setattr(un, "_SET_READER_BROKEN", "a stand-in reason")
    with pytest.raises(un.SiteUndescribed, match="not proven on this interpreter \\(a stand-in reason\\)"):
        un.site_description(_r28_module("class Site:\n    s = set()\n").Site)


# each field the reader trusts, set to a WRONG offset that still lies inside the set object: the check must refuse and
# name THAT field (so dropping any one check fails its own row, not a neighbour's)
_R33_WRONG_OFFSETS = [
    ("_SET_FILL", 40, "fill/used: a fresh"),          # the table pointer
    ("_SET_FILL", 24, "fill/used: three discards"),   # fill read as used: equal in a fresh set, told apart by discards
    ("_SET_USED", 16, "fill/used: three discards"),
    ("_SET_FINGER", 48, "finger: a fresh"),            # the hash field, -1 in a set
    ("_SET_FINGER", 192, "finger: one pop"),           # the weakref list, 0 in a fresh set and after a pop
    # the type pointer: static, readable memory, so with the table test dropped the keys test refuses by name (a wrong
    # offset that reads as an unmapped address — the hash field, -1 — would crash the reader, not fail it)
    ("_SET_TABLE", 8, "table: a fresh"),
    ("_SET_SMALL", 72, "table: a fresh"),
    ("_SET_MASK", 56, "mask: the mask"),               # the finger, 0 in a fresh set
    ("_SET_ENTRY", 8, "keys: a fresh"),
]


@pytest.mark.parametrize("field,offset,reason", _R33_WRONG_OFFSETS, ids=[r[0] for r in _R33_WRONG_OFFSETS])
def test_r33_the_set_reader_check_refuses_a_wrong_layout(field, offset, reason):
    """The second seat's R2: every field is proven against an independent observable, and a wrong offset for any one of
    them leaves the reader unproven, with that field named."""
    un = _load("inv7_uninstrument_r33_layout", EVIDENCE / "inv7_uninstrument.py")
    assert un._set_reader_check()[1] is None, "the precondition: the true layout is proven"
    with pytest.MonkeyPatch.context() as monkeypatch:   # a context, not the fixture: the mutant table calls this cell
        monkeypatch.setattr(un, field, offset)
        dummy, why = un._set_reader_check()
    assert dummy is None and why is not None and why.startswith(reason), (field, why)


@pytest.mark.parametrize("build,patch", [
    ("a debug build", lambda m, un: m.setattr(sys, "gettotalrefcount", lambda: 0, raising=False)),
    ("a free-threaded build", lambda m, un: m.setattr(__import__("sysconfig"), "get_config_var",
                                                      lambda n: 1 if n == "Py_GIL_DISABLED" else None)),
    ("pointers are not 64-bit", lambda m, un: m.setattr(un.ctypes, "sizeof", lambda _t: 4)),
])
def test_r33_the_set_reader_check_refuses_an_unsupported_build(build, patch, monkeypatch):
    """The layout is trusted only on the builds it was measured for; any other is refused before a read."""
    un = _load("inv7_uninstrument_r33_build", EVIDENCE / "inv7_uninstrument.py")
    patch(monkeypatch, un)
    assert un._set_reader_check() == (None, build)


def test_r33_the_set_reader_runs_under_the_guard():
    """The second seat's R1: the reads go through ctypes' C-level accessors only, so describing W1–W3 under the round-28
    guard enters no foreign frame (a Python-level ctypes helper would be refused: `_R33_MUTANTS`)."""
    un = _load("inv7_uninstrument_r33_guard", EVIDENCE / "inv7_uninstrument.py")
    for label, a, b, decide, _ in _R33_TABLE[:3]:
        for pre in (a, b):
            un.site_description(_r28_module(_r33_table_source(pre, decide)).Site)

def test_r32_which_set_element_is_shared_is_still_drift():
    """`t` is the set's own element, or an equal object built apart (round 33: large ints, value-hashed, so the set is
    described and the identity of the shared element is recorded)."""
    un = _load("inv7_uninstrument_r32_setwhich", EVIDENCE / "inv7_uninstrument.py")
    head = "_x, _y = int('1' * 25), int('2' * 25)\n"
    tail = "class Site:\n    s = frozenset([_x, _y])\n    t = @T@\n\n    def fire(self, value):\n        return any(e is self.t for e in self.s)\n"
    inside, apart = head + tail.replace("@T@", "_x"), head + tail.replace("@T@", "int('1' * 25)")
    assert (_r28_module(inside).Site().fire(0), _r28_module(apart).Site().fire(0)) == (True, False)
    assert un.site_description(_r28_module(inside).Site) != un.site_description(_r28_module(apart).Site), \
        "which element is shared reads as no drift"


def test_r32_a_set_whose_elements_cannot_be_told_apart_is_refused():
    """Two instances with equal state: their order follows their (census-defined, here colliding) hash and insertion,
    not their values — refused (round 33's rule; round 32 refused it as a tie)."""
    un = _load("inv7_uninstrument_r32_settie", EVIDENCE / "inv7_uninstrument.py")
    src = _R32_K + "class Site:\n    s = frozenset({K('x'), K('x')})\n"
    with pytest.raises(un.SiteUndescribed, match="does not follow its value alone"):
        un.site_description(_r28_module(src).Site)


def test_r32_a_leafs_scalar_referents_go_through_the_map():
    """The last value path outside the map (the second seat's mark 2): a C object described by its own repr — here
    itertools.count — also passes its scalar referents through the map, so one runtime int held as start and step
    differs from two equal ones. Measured on 3.14: `count` does not pickle, and `next()` returns the stored START but
    then a fresh sum, never the step, so whether start and step are one object is not shown by `count`'s own API —
    recorded anyway, an over-detection that cannot be a false silence. This cell reaches the immutable-type branch;
    the C-repr-SLOT branch takes the same rule and NO cell reaches it — subclasses of itertools.count and
    itertools.repeat holding runtime ints are refused before it (the second seat's stage 2, measured)."""
    import itertools
    un = _load("inv7_uninstrument_r32_leaf", EVIDENCE / "inv7_uninstrument.py")

    def site(shared):
        x = int("1" * 25)
        y = x if shared else int("1" * 25)

        class Site:
            c = itertools.count(x, y)
        return Site
    assert un.site_description(site(True)) != un.site_description(site(False)), "a leaf's referents bypassed the map"


def test_r32_a_set_whose_elements_differ_only_by_a_back_reference_is_described():
    """A set whose elements are equal except that one holds an object met earlier (a back-reference) is described
    (round 33: value-hashed tuples of large ints; the set is described in iteration order)."""
    un = _load("inv7_uninstrument_r32_backref", EVIDENCE / "inv7_uninstrument.py")
    src = ("_first = int('9' * 25)\n_other = int('9' * 25)\n"
           "class Site:\n    first = _first\n    s = frozenset([(1, _first), (2, _other)])\n")
    un.site_description(_r28_module(src).Site)


def _r32_cell(name):
    return next(c for c in _R32_SHARING_CELLS if c[0] == name)


_R32_MUTANTS = [
    ("the per-type exemption restored (round 31's rule)",
     "    if id(obj) in seen:\n        ref = seen[id(obj)]\n",
     "    if _builtin(tp, frozenset({\"tuple\", \"frozenset\"})):\n        return (_qualname(tp), tuple(_normalise(x, seen) for x in obj))\n"
     "    if id(obj) in seen:\n        ref = seen[id(obj)]\n",
     _r30_cell(test_r32_sharing_of_an_immutable_object_is_drift, *_r32_cell("runtime tuples within one member through site_description")),
     (AssertionError, "reads as no drift")),
    ("scalars exempted again (round 18's rule)",
     "    if id(obj) in seen:\n        ref = seen[id(obj)]\n",
     "    if _builtin(tp, _SCALARS):\n        return (_qualname(tp), repr(obj))\n    if id(obj) in seen:\n        ref = seen[id(obj)]\n",
     _r30_cell(test_r32_sharing_of_an_immutable_object_is_drift, *_r32_cell("runtime ints within one member through site_description")),
     (AssertionError, "reads as no drift")),
    ("a leaf's scalar referents outside the map",
     "            return (identity, _addressless(repr(obj)), tuple(_normalise(r, seen) for r in refs))\n",
     "            return (identity, _addressless(repr(obj)))\n",
     test_r32_a_leafs_scalar_referents_go_through_the_map,
     (AssertionError, "a leaf's referents bypassed the map")),

    # round 32's five set-order rows mutated the sorted registration, its provisional copies and its tie refusal —
    # removed with the mechanism in round 33 (R32-1); round 33's rows are in `_R33_MUTANTS`
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R32_MUTANTS, ids=[m[0] for m in _R32_MUTANTS])
def test_r32_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each round-32 rule fails its own cell FOR THE REASON IT IS NAMED FOR."""
    mut = _r25_mutant(tmp_path, "inv7_uninstrument.py", anchor, replacement, "r32m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    exc, pattern = expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


# ONE DEFINITION OF ROUTE B'S LAUNCH, tested in both directions (the second seat's stage 2 on the receipt): the receipt
# follows the constant, and route B itself reads it.
def test_receipt_follows_route_bs_flags_when_they_change():
    """Route B's flags without -B: the receipt's route-B child reports bytecode writable, and the acceptance condition
    reads false — the receipt audits the launch route B actually makes."""
    rec = _load("reader_seed_receipt_flags_cell", EVIDENCE / "reader_seed_receipt.py")
    un = _load("inv7_uninstrument_flags_cell", EVIDENCE / "inv7_uninstrument.py")
    with pytest.MonkeyPatch.context() as m:
        m.setattr(un, "_ROUTE_B_FLAGS", ("-P", "-s"))
        r = rec.receipt(un)
    assert r["route_b_child"]["ran"] and r["route_b_child"]["dont_write_bytecode"] is False, r["route_b_child"]
    assert rec.accepted(r) is False


def test_receipt_refuses_a_route_b_environment_that_leaks_a_variable():
    """Route B's environment leaking a PYTHON* variable: the receipt records it and the acceptance condition reads
    false — recorded is not enough, the receipt requires PYTHONHASHSEED alone."""
    rec = _load("reader_seed_receipt_env_cell", EVIDENCE / "reader_seed_receipt.py")
    un = _load("inv7_uninstrument_env_cell", EVIDENCE / "inv7_uninstrument.py")
    real = un._isolated_env
    with pytest.MonkeyPatch.context() as m:
        m.setattr(un, "_isolated_env", lambda: {**real(), "PYTHONWARNINGS": "ignore"})
        r = rec.receipt(un)
    assert r["route_b_child"]["python_env"] == ["PYTHONHASHSEED", "PYTHONWARNINGS"], r["route_b_child"]
    assert rec.accepted(r) is False


def test_route_b_reads_its_flags_from_the_one_definition():
    """The other direction: route B's launch READS `_ROUTE_B_FLAGS`. Without -s, route B's own child refuses and names the
    condition (no_user_site); route B re-inlining its own literals would launch with -s regardless and describe — the
    mutant in `_R33_MUTANTS` that fails this cell."""
    un = _load("inv7_uninstrument_routeb_flags", EVIDENCE / "inv7_uninstrument.py")
    ref = un.REFERENCE_CENSUS.read_text(encoding="utf-8")
    assert un.site_drift(ref, ref) == [], "the precondition: route B describes the reference census under its flags"
    with pytest.MonkeyPatch.context() as m:
        m.setattr(un, "_ROUTE_B_FLAGS", ("-P", "-B"))
        with pytest.raises(un.SiteUndescribed, match="not isolated as it must be: no_user_site"):
            un.site_drift(ref, ref)


def _r33_cell(table, name, fn):
    return _r30_cell(fn, *next(c for c in table if c[0] == name))


_R33_MUTANTS = [
    ("the elements sorted again (round 32's rule)",
     "    fill, used, mask, finger, slots = _set_table(obj, items)\n",
     # round 32's rule in full: registered AND emitted in the order of each element's provisional description (sorting
     # only the emitted reprs is not round 32's rule — registration positions still follow iteration order)
     "    return tuple(repr(_normalise(x, seen)) for x in sorted(items, key=lambda x: repr(_normalise(x, dict(seen)))))\n",
     _r33_cell(_R33_DESCRIBED_CELLS, "ints 8/16 against 16/8 through site_description",
               test_r33_a_set_of_value_hashed_elements_is_described_by_its_table),
     (AssertionError, "reads as no drift")),
    ("the refusal dropped",
     "    if not all(_value_hashed(x) for x in items):\n",
     "    if False:\n",
     _r33_cell(_R33_REFUSED_CELLS, "the verdict's exact frozenset through site_description",
               test_r33_a_set_whose_slots_are_not_its_values_is_refused),
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("the NaN test dropped (the second seat's B1)",
     "        return not (tp is float and x != x)\n",
     "        return True\n",
     test_r33_a_set_holding_nan_is_refused,
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("a subclass admitted (isinstance for the exact type; the second seat's B3)",
     "    if _builtin(tp, _VALUE_HASHED_SCALARS):\n",
     "    if isinstance(x, int) or _builtin(tp, _VALUE_HASHED_SCALARS):\n",
     test_r33_an_int_subclass_with_its_own_hash_is_refused,
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("route B's child isolation check dropped (the second seat's B-b)",
     "if _bad:\n", "if False:\n",
     test_r33_route_b_refuses_a_child_that_is_not_isolated,
     (AssertionError, "'mro'")),   # the child then DESCRIBES: its response is the description, which starts with mro
    ("the table read as its order alone (round 33's first rule)",
     "    return ((\"mask\", mask), (\"fill\", fill), (\"used\", used), (\"finger\", finger),\n"
     "            tuple((i, \"<dummy>\" if k == _SET_DUMMY else repr(_normalise(by_id[k], seen))) for i, k in slots))\n",
     "    return tuple(repr(_normalise(by_id[k], seen)) for i, k in slots if k != _SET_DUMMY)\n",
     _r33_cell(_R33_TABLE_CELLS, "W3 a frozenset's layout through site_description", test_r33_a_sets_table_is_state),
     (AssertionError, "reads as no drift")),
    ("the dummies' slots dropped (the second seat's stage-2b C1)",
     "            tuple((i, \"<dummy>\" if k == _SET_DUMMY else repr(_normalise(by_id[k], seen))) for i, k in slots))\n",
     "            tuple((i, repr(_normalise(by_id[k], seen))) for i, k in slots if k != _SET_DUMMY))\n",
     _r33_cell(_R33_TABLE_CELLS, "W5 dummies at other slots through site_description", test_r33_a_sets_table_is_state),
     (AssertionError, "reads as no drift")),
    ("the occupied-slot count against fill dropped (the second seat's stage-2b C3)",
     "            or {k for _, k in slots if k != _SET_DUMMY} != live or len(slots) != fill):\n",
     "            or {k for _, k in slots if k != _SET_DUMMY} != live):\n",
     test_r33_a_dummy_read_as_empty_is_refused,
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("the finger dropped",
     "(\"finger\", finger),\n", "\n",
     _r33_cell(_R33_TABLE_CELLS, "W1 a set popped and refilled through site_description", test_r33_a_sets_table_is_state),
     (AssertionError, "reads as no drift")),
    ("the mask dropped",
     "    return ((\"mask\", mask), (\"fill\", fill)", "    return ((\"fill\", fill)",
     _r33_cell(_R33_TABLE_CELLS, "W4 a table grown by adds against one made by merge through site_description", test_r33_a_sets_table_is_state),
     (AssertionError, "reads as no drift")),
    ("the reader through a Python-level ctypes helper (the second seat's R1)",
     "    return tuple(ptr(table + _SET_ENTRY * i).value or 0 for i in range(mask + 1))\n",
     "    return tuple(int.from_bytes(ctypes.string_at(table + _SET_ENTRY * i, 8), 'little') for i in range(mask + 1))\n",
     test_r33_the_set_reader_runs_under_the_guard,
     (Exception, "would run code the describer did not write")),
    ("the reader's check forced to pass",
     "_SET_DUMMY, _SET_READER_BROKEN = _set_reader_check()\n",
     "_SET_DUMMY, _SET_READER_BROKEN = _set_reader_check()\n_set_reader_check = lambda: (_SET_DUMMY, None)\n",
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *_R33_WRONG_OFFSETS[0]),
     (AssertionError, "_SET_FILL")),
    ("the torn-read re-read dropped (the second seat's N1)",
     "    if (_set_header(obj) != first or _set_keys(table, mask) != keys or used != len(items)\n",
     "    if (used != len(items)\n",
     test_r33_a_table_that_changes_while_read_is_refused,
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("the reader check's fresh fill/used test dropped",
     '        if (fill, used) != (n, n):\n', '        if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'a fresh' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's fresh finger test dropped",
     '        if finger != 0:\n', '        if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'finger: a fresh' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's table pointer test dropped",
     '        if (table == id(s) + _SET_SMALL) != (n <= 4):\n', '        if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'table' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's mask test dropped",
     '        if set.__sizeof__(s) != set.__basicsize__ + (0 if n <= 4 else (mask + 1) * _SET_ENTRY) or (n <= 4) != (mask == 7):\n', '        if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'mask' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's keys test dropped",
     '        if sorted(k for k in _set_keys(table, mask) if k) != sorted(id(x) for x in s):\n', '        if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'keys' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's discard fill/used test dropped",
     '    if (fill, used) != (10, 7):\n', '    if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'three discards' in r[2])),
     (AssertionError, "_SET_")),
    ("the reader check's pop finger test dropped",
     '    if s.pop() != 0 or _set_header(s)[4] != 1:\n', '    if False:\n',
     _r30_cell(test_r33_the_set_reader_check_refuses_a_wrong_layout, *next(r for r in _R33_WRONG_OFFSETS if 'one pop' in r[2])),
     (AssertionError, "_SET_")),
    ("route B's launch with its flags re-inlined (the second seat's stage 2 on the receipt)",
     '            r = subprocess.run([sys.executable, *_ROUTE_B_FLAGS, "-c", _ISOLATED_CHILD, str(pathlib.Path(__file__).resolve()),\n',
     '            r = subprocess.run([sys.executable, "-P", "-s", "-B", "-c", _ISOLATED_CHILD, str(pathlib.Path(__file__).resolve()),\n',
     test_route_b_reads_its_flags_from_the_one_definition,
     (pytest.fail.Exception, "DID NOT RAISE")),
    ("the arm's seed assertion dropped",
     "    _assert_seed_pinned()\n    import veracium\n", "    import veracium\n",
     test_r33_an_arm_refuses_an_unpinned_seed,
     (AssertionError, "an unpinned arm was set up")),
]


@pytest.mark.parametrize("mutant,anchor,replacement,cell,expected", _R33_MUTANTS, ids=[m[0] for m in _R33_MUTANTS])
def test_r33_each_rule_is_load_bearing(mutant, anchor, replacement, cell, expected, tmp_path, monkeypatch):
    """Each round-33 rule fails its own cell FOR THE REASON IT IS NAMED FOR."""
    # the file to mutate is the ONE evidence file whose text holds the anchor exactly once (by property, never by the
    # row's name): the arm's seed assertion lives in the observer, every other round-33 rule in the describer
    holders = [f for f in ("inv7_uninstrument.py", "inv7_observer.py")
               if (EVIDENCE / f).read_text(encoding="utf-8").count(anchor) == 1]
    assert len(holders) == 1, (mutant, holders)
    mut = _r25_mutant(tmp_path, holders[0], anchor, replacement, "r33m")
    monkeypatch.setattr(sys.modules[__name__], "_load", lambda *_a, **_k: mut)
    exc, pattern = expected
    with pytest.raises(exc, match=re.escape(pattern)):
        cell()


_R32_REAL_SEED_PROBE = r"""
import hashlib, importlib.util, sys
sys.path.insert(0, sys.argv[2])
s = importlib.util.spec_from_file_location("un_real_seed", sys.argv[1]); un = importlib.util.module_from_spec(s)
sys.modules["un_real_seed"] = un; s.loader.exec_module(un)
from veracium.census import Site
print("SEEDPROBE", hash("a"))
print("DIGEST", un.site_description_digest(un.site_description(Site))["digest"])   # site_realized's own definition
"""


def test_r32_the_real_site_describes_the_same_under_every_hash_seed():
    """The INV-7 run cannot show this: its harness pins PYTHONHASHSEED=0 for every arm, while route B's `-I` children each
    draw a random seed (the second seat's stage-2 mark). The REAL census's Site, described under six distinct hash seeds
    — asserted distinct by each process's own hash("a") — reads identically; and route B's own path, its isolated child,
    finds no drift between the census and itself, three times."""
    un = _load("inv7_uninstrument_r32_realseed", EVIDENCE / "inv7_uninstrument.py")
    src = pathlib.Path(un.__file__).resolve().parents[3] / "src"
    probes, digests = set(), set()
    for seed in range(1, 7):
        out = subprocess.run([sys.executable, "-c", _R32_REAL_SEED_PROBE, un.__file__, str(src)], capture_output=True,
                             text=True, env={**os.environ, "PYTHONHASHSEED": str(seed), "PYTHONDONTWRITEBYTECODE": "1"})
        assert out.returncode == 0, out.stderr[-400:]
        lines = dict(line.split(" ", 1) for line in out.stdout.splitlines() if " " in line)
        probes.add(lines["SEEDPROBE"]); digests.add(lines["DIGEST"])
    assert len(probes) == 6, ("the six processes did not run under six hash seeds", probes)
    assert len(digests) == 1, ("the real Site's description followed the hash seed", len(digests))
    census = (src / "veracium" / "census.py").read_text(encoding="utf-8")
    for _ in range(3):
        assert un.site_drift(census, census) == [], "route B finds drift between the real census and itself"


# THE READER/SEED RECEIPT (the round-33 verdict's suggestion, on the owner's word): what the trusted channel rests on,
# reported by the interpreter it rests on. Both halves are cells (the second seat's mark 4): a receipt that could only
# print "proven" would be a control that cannot fail.
def _receipt_run(env):
    out = subprocess.run([sys.executable, str(EVIDENCE / "reader_seed_receipt.py")], capture_output=True, text=True,
                         env=env, timeout=600)
    return out.returncode, json.loads(out.stdout), out.stderr


def test_receipt_reports_a_pinned_seed_and_a_proven_reader_in_both_processes():
    """Under PYTHONHASHSEED=0, as an arm runs: the seed reads pinned and the reader proven, at import and fresh, in this
    process AND in route B's child, launched as route B launches it; the receipt says it is a proxy for the arm."""
    env = {**{k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}, "PYTHONHASHSEED": "0",
           "PYTHONDONTWRITEBYTECODE": "1"}
    rc, r, err = _receipt_run(env)
    assert rc == 0, (r, err[-300:])
    assert "proxy for the arm" in r["process"], r["process"]
    assert r["seed"] == {**r["seed"], "hash_randomization": 0, "PYTHONHASHSEED": "0", "pinned_to_zero": True}
    sr = r["set_reader"]
    assert (sr["proven_at_import"], sr["proven_fresh"], sr["agree"], sr["reason_at_import"], sr["reason_fresh"]) == \
        (True, True, True, None, None), sr
    b = r["route_b_child"]
    assert b["ran"] and b["safe_path"] and b["no_user_site"] and b["hash_randomization"] == 0, b
    assert b["python_env"] == ["PYTHONHASHSEED"] and b["proven_at_import"] and b["proven_fresh"], b
    assert len(r["identity"]["executable_sha256"]) == 64 and r["identity"]["sys_version"] == sys.version, r["identity"]


def test_receipt_reports_an_unpinned_seed_and_refuses():
    """Without PYTHONHASHSEED the seed is random: the receipt says so and exits 1 — the condition the INV-7 result was
    accepted under does not hold, and the receipt records it rather than staying silent."""
    env = {**{k: v for k, v in os.environ.items() if k != "PYTHONHASHSEED"}, "PYTHONDONTWRITEBYTECODE": "1"}
    rc, r, err = _receipt_run(env)
    assert rc == 1, (r, err[-300:])
    assert r["seed"]["pinned_to_zero"] is False and r["seed"]["hash_randomization"] == 1 and r["seed"]["PYTHONHASHSEED"] is None


@pytest.mark.parametrize("how", ["a wrong offset found fresh", "unproven at import"])
def test_receipt_reports_an_unproven_reader_with_its_reason(how):
    """The reader's check FAILING: the receipt reports unproven with the check's own reason, and the acceptance
    condition reads false — never a crash, never "proven"."""
    rec = _load("reader_seed_receipt_cell", EVIDENCE / "reader_seed_receipt.py")
    un = _load("inv7_uninstrument_receipt_cell", EVIDENCE / "inv7_uninstrument.py")
    with pytest.MonkeyPatch.context() as m:
        if how == "a wrong offset found fresh":
            m.setattr(un, "_SET_FILL", 40)
            r = rec.receipt(un, route_b=False)
            sr = r["set_reader"]
            assert sr["proven_fresh"] is False and sr["reason_fresh"].startswith("fill/used: a fresh"), sr
            assert sr["agree"] is False, sr
        else:
            m.setattr(un, "_SET_DUMMY", None)
            m.setattr(un, "_SET_READER_BROKEN", "a stand-in reason")
            r = rec.receipt(un, route_b=False)
            sr = r["set_reader"]
            assert sr["proven_at_import"] is False and sr["reason_at_import"] == "a stand-in reason", sr
    assert rec.accepted(r) is False, r


def test_receipt_acceptance_fails_on_a_route_b_child_that_did_not_hold():
    """The acceptance condition reads route B's child too: a child that did not run, or ran unisolated, fails it."""
    rec = _load("reader_seed_receipt_child_cell", EVIDENCE / "reader_seed_receipt.py")
    good = {"seed": {"pinned_to_zero": True},
            "set_reader": {"proven_at_import": True, "proven_fresh": True, "agree": True},
            "route_b_child": {"ran": True, "safe_path": True, "no_user_site": True, "dont_write_bytecode": True,
                              "hash_randomization": 0, "python_env": ["PYTHONHASHSEED"],
                              "proven_at_import": True, "proven_fresh": True, "agree": True}}
    assert rec.accepted(good) is True
    for field, bad in [("ran", False), ("safe_path", False), ("no_user_site", False), ("dont_write_bytecode", False),
                       ("hash_randomization", 1), ("python_env", ["PYTHONHASHSEED", "PYTHONWARNINGS"]),
                       ("proven_fresh", False)]:
        r = json.loads(json.dumps(good)); r["route_b_child"][field] = bad
        assert rec.accepted(r) is False, (field, bad)

