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
    """The negative control: skip one declining execution and the trace diverges at a named record."""
    victim = sorted(leg.DECLINES)[len(leg.DECLINES) // 2]
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
# R7 pulled into this batch on Quentin's word). Every cell below was written BEFORE the fix and run against the
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


# ---- round 15: the twin keeps a REAL census.py (Quentin's decision, 2026-09-24): round 15 the SOURCE'S verbatim; round 16
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
    hn, rn = dict(un._normal_code(h.__code__)), dict(un._normal_code(r.__code__))
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
            "__module__", "__name__", "__qualname__"} | ({"__type_params__"} if sys.version_info >= (3, 12) else set())
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


_R19_SHIPPED_FLAGS = '[sys.executable, "-I", "-B", "-c",'
# the two superseded forms, each the mutant of one caller: `-I` alone (the round-19 fix as first committed to the
# working tree), and the caller's `-B` passed on conditionally (the first fix, which the second seat's stage-1 read
# showed misses a caller whose caches are redirected)
_R19_BARE = '[sys.executable, "-I", "-c",'
_R19_CONDITIONAL = '[sys.executable, "-I", *(["-B"] if sys.flags.dont_write_bytecode else []), "-c",'


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
    # on the transport itself (a bare JSONDecodeError), not on this round's budget constant
    monkeypatch.setattr(un, "_ISOLATION_TIMEOUT", 8, raising=False)
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
    # and the one decode of a SOURCE carries an error handler: valid Python may hold bytes invalid in its declared
    # encoding inside a comment (the second seat's stage-1c read), and a strict decode would crash on it
    tree = ast.parse(source)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_source_text")
    decodes = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "decode"]
    if not (decodes and all(any(k.arg == "errors" for k in c.keywords) for c in decodes)):
        found.append(("module", fn.lineno, "_source_text decodes without an error handler"))
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
    # the second seat's stage-1c read: a byte invalid in the declared encoding is VALID PYTHON inside a comment (the
    # tokenizer does not decode comment bytes; it imports and runs on 3.10-3.13), and an unknown cookie is not Python
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
    ("a source decoded as UTF-8, whatever it declares", '        text = data.decode(encoding, errors="replace")',
     '        text = data.decode("utf-8", errors="replace")', _R21_CP1252),
    ("the twin written in the ORIGINAL's encoding", '    data = text.encode(_source_encoding(text.encode("utf-8")))',
     '    data = text.encode("cp1252")', _R21_CP1252),
    ("a source decoded strictly (no error handler)", '        text = data.decode(encoding, errors="replace")',
     "        text = data.decode(encoding)", "census: a trailing comment holding an invalid UTF-8 byte"),
    ("an unreadable source raising bare", '        raise SourceUnreadable(f"{label} could not be read as Python source',
     '        raise\n        raise SourceUnreadable(f"{label} could not be read as Python source',
     "census: an unknown coding cookie (not Python: a named refusal)"),
    # round 22 made the bytes-parse also the interpreter's side of the guard, so the V3 form is now "parse the decoded
    # text in its place": no BYTE-level validation at all
    ("the bytes-parse removed (stage 2's V3)", "        from_bytes = ast.parse(data, filename=label)\n",
     '        from_bytes = ast.parse(data.decode(_source_encoding(data), errors="replace"), filename=label)\n',
     "census: an invalid byte in a string literal (not Python: a named refusal)"),
], ids=["decode as utf-8", "write in the original's encoding", "strict decoding", "bare on an unknown cookie",
        "bytes-parse removed"])
def test_r21_each_superseded_source_rule_fails_a_cell(mutant, anchor, replacement, killer, tmp_path):
    text = (EVIDENCE / "inv7_uninstrument.py").read_text(encoding="utf-8")
    assert text.count(anchor) == 1, (mutant, "the anchor moved")
    ev = tmp_path / "evidence"
    shutil.copytree(EVIDENCE, ev, ignore=shutil.ignore_patterns("__pycache__"))
    (ev / "inv7_uninstrument.py").write_text(text.replace(anchor, replacement), encoding="utf-8")
    mut = _load("inv7_uninstrument_r21srcmut", ev / "inv7_uninstrument.py")
    _, kind, make, expect = {c[0]: c for c in _R21_SOURCE_CELLS}[killer]
    src, out = _r21_source_cell(mut, tmp_path, kind, make)
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
    """The verdict's class through derive() and verify(); a product twin RUNS as its source does."""
    un = _load("inv7_uninstrument_r22cells", EVIDENCE / "inv7_uninstrument.py")
    kind = "census" if cell.startswith("census") else "product"
    src, out = _r21_source_cell(un, tmp_path, kind, make)
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
    data = b"# -*- coding: latin-1 -*-\n" + "S = 'caf\u00e9'\n".encode("latin-1")
    assert "caf\u00e9" in un._source_text(data, "m.py")
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
    data = b"# -*- coding: latin-1 -*-\n" + "S = 'caf\u00e9'\n".encode("latin-1")
    assert "caf\u00e9" not in mut._source_text(data, "m.py"), "the mutant refused the wrong UTF-8 reading — not killed"


_R22_MUTANTS = [
    ("round 21's detect_encoding", "def _source_encoding(data: bytes) -> str:\n",
     "def _source_encoding(data: bytes) -> str:\n    import io, tokenize\n    return tokenize.detect_encoding(io.BytesIO(data).readline)[0]\n\n\ndef _unused_(data: bytes) -> str:\n"),
    ("line 2 examined after a line of code", "        if i == 0 and not _BLANK_OR_COMMENT.match(line):\n            break\n", ""),
    ("the interpreter guard removed", "    if ast.dump(from_bytes, include_attributes=True) != ast.dump(from_text, include_attributes=True):\n",
     "    if False:\n"),
]


@pytest.mark.parametrize("mutant,anchor,replacement", _R22_MUTANTS, ids=[m[0] for m in _R22_MUTANTS])
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








