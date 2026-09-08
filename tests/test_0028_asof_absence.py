"""specs/0028 §9 — the mutation matrix for `specs/evidence/0028/check_asof_absence.py`
(the absence proof over the shipped as-of code, two forms). Each test names the
mutant it kills; the positive run comes first so a broken checker cannot pass
its own matrix by failing everything.

The matrix references the artifact by filename (the P1 gate's pointer rule).
"""
from __future__ import annotations

import importlib.util
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "specs" / "evidence" / "0028" / "check_asof_absence.py"
PLUGIN = ROOT / "specs" / "evidence" / "0028" / "asof_recording_clock.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_asof_absence", ARTIFACT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _copy_src(tmp_path):
    dst = tmp_path / "src"
    shutil.copytree(ROOT / "src", dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


# ---------------------------------------------------------------- positive
def test_the_static_form_reaches_the_roots_and_finds_no_predicate_access():
    """The positive static run on the shipped tree: every root resolved, the
    reached set non-trivial, ZERO hits — and the not-followed list is
    non-empty, because a static walker that claims to have followed
    everything is the claim this artifact refuses to make."""
    mod = _load()
    w = mod.static_form(ROOT / "src")
    reached = {q for _, q in w.reached}
    assert {"classify_as_of", "assertable_as_of", "SqliteStore.current_state", "SqliteStore.edges",
            "resolve_as_of", "lookup_successors", "recall_at", "Memory.facts_valid_at",
            "SqliteStore.read_window", "SqliteStore.edges_superseding",
            "_resolve_edge", "_walk", "_absorber", "held_at"} <= reached, sorted(reached)
    assert "adapt" in reached, "the adapter is reached from classify_as_of through the tree"
    assert w.hits == [], w.hits
    assert w.not_followed, "the boundary must be visible: some receivers are not followable statically"


def test_the_behavioural_form_runs_the_shipped_asof_tests_under_the_clock():
    """The positive behavioural run: the whole as-of test surface under the
    recording clock — classifications > 0, accesses > 0 (the clock is live),
    violations == 0."""
    r = subprocess.run([sys.executable, str(ARTIFACT), "--json", str(ROOT / ".asof_absence_matrix.json")],
                       cwd=str(ROOT), capture_output=True, text=True)
    out = ROOT / ".asof_absence_matrix.json"
    try:
        assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-1000:]
        import json
        rep = json.loads(out.read_text())
        c = rep["behavioural"]["counts"]
        assert c["classify_calls"] > 0 and c["accesses"] > 0 and c["violations"] == 0, c
        assert rep["static"]["hits"] == []
        # the exercised surface is DERIVED and names every classifier-reaching
        # test file except this matrix, which is listed as excluded with its reason
        b = rep["behavioural"]
        assert b["exercised_set_derived"] is True
        # DERIVED, compared to the derivation run here (a hand list went stale
        # the day the resolution's own test file joined the surface)
        assert set(b["exercised_files"]) == set(_load().exercised_test_files(ROOT)[0]), b["exercised_files"]
        assert {"tests/test_0030_asof.py", "tests/test_s2_valid_from_predicate.py",
                "tests/test_0028_resolution.py"} <= set(b["exercised_files"]), b["exercised_files"]
        assert "tests/test_0028_asof_absence.py" in b["excluded_files"]
    finally:
        if out.exists():
            out.unlink()


def test_no_shipped_path_reaches_the_classifier_so_the_derived_set_is_the_reachable_set():
    """The completeness argument for the DERIVED exercised set, measured: the
    only calls of classify_as_of/assertable_as_of in src/ are inside the
    `asof/` package (the classifier itself and, since 2026-09-08, the
    resolution — whose entry points are in REACHES_CLASSIFIER), so a test
    reaches the classifier only by naming one of those tokens, and
    files-that-name-them IS files-that-reach-it."""
    assert _load().src_call_sites(ROOT / "src") == []


# ------------------------------------------------------------------ mutants
def test_call_site_census_detects_a_shipped_path_planted_in_gate(tmp_path):
    """MUTANT 0 (the completeness census): a call to classify_as_of planted in
    a COPY of gate.py — the census must report it at its line, because that
    is the case in which the derived set would silently stop being the
    reachable set."""
    src = _copy_src(tmp_path)
    f = src / "veracium" / "gate.py"
    f.write_text(f.read_text() + "\n\ndef _mutant(*a):\n    from .asof import classify_as_of\n    return classify_as_of(*a)\n")
    sites = _load().src_call_sites(src)
    assert len(sites) == 1 and sites[0].startswith("veracium/gate.py:"), sites


def test_static_form_detects_an_injected_predicate_access(tmp_path):
    """MUTANT 1 (static, at the root): `snap.valid_now` inserted into
    classify_as_of's body in a COPY of src. The walker must report exactly
    that hit, in that function, at that line. This is the test the artifact's
    `# Mutation-Matrix:` pointer names, so the binding is asserted here: the
    module under test is specs/evidence/0028/check_asof_absence.py."""
    assert ARTIFACT.name == "check_asof_absence.py" and ARTIFACT.exists()
    src = _copy_src(tmp_path)
    f = src / "veracium" / "asof" / "classify.py"
    t = f.read_text()
    anchor = "    reason = snap.invalidation_reason\n"
    assert t.count(anchor) == 1
    f.write_text(t.replace(anchor, anchor + "    _mutant = snap.valid_now\n"))
    w = _load().static_form(src)
    assert [(h[1], h[3], h[4]) for h in w.hits] == [("classify_as_of", "attribute", "snap.valid_now")], w.hits


def test_static_form_detects_a_hit_reached_only_through_the_tree(tmp_path):
    """MUTANT 2 (static, through a followed edge): the access is planted in
    `adapter.adapt`, which classify_as_of reaches by `from .adapter import
    adapt`. A walker that looked only at the root bodies would miss it."""
    src = _copy_src(tmp_path)
    f = src / "veracium" / "asof" / "adapter.py"
    t = f.read_text()
    assert "def adapt(" in t
    body_start = t.index("def adapt(")
    colon = t.index(":\n", body_start) + 2
    f.write_text(t[:colon] + "    _mutant = expect_id.assertable if False else None\n" + t[colon:])
    w = _load().static_form(src)
    assert any(h[1] == "adapt" and h[3] == "attribute" and "assertable" in h[4] for h in w.hits), w.hits


def test_behavioural_form_detects_a_violation_planted_in_a_callee(tmp_path):
    """MUTANT 3 (behavioural): a callee of classify_as_of is patched to touch
    `Edge.valid_now` — the static tree of the SHIPPED files is clean, so only
    the recording clock can see it. Run the artifact's behavioural form with
    a conftest that installs the patch; violations must be > 0 and the
    proof must FAIL."""
    tdir = tmp_path / "t"
    tdir.mkdir()
    (tdir / "conftest.py").write_text(
        "import pytest\n"
        "from veracium.asof import classify as _c\n"
        "from veracium.schema import Edge, EvidenceAuthor, Provenance\n"
        "_orig = _c.adapt\n"
        "def _bad(*a, **k):\n"
        "    e = Edge(id='m', user_id='u', subject='user', relation='located_at', object='x',\n"
        "             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref='m'))\n"
        "    _ = e.valid_now\n"
        "    return _orig(*a, **k)\n"
        "_c.adapt = _bad\n")
    shutil.copy(ROOT / "tests" / "test_0030_asof.py", tdir / "test_0030_asof.py")
    r = subprocess.run([sys.executable, str(ARTIFACT), "--test-path", str(tdir / "test_0030_asof.py"),
                        "--json", str(tmp_path / "rep.json")], cwd=str(ROOT), capture_output=True, text=True)
    import json
    rep = json.loads((tmp_path / "rep.json").read_text())
    c = rep["behavioural"]["counts"]
    assert c["violations"] > 0, (c, r.stdout[-1500:])
    assert any(v["asof_frame"] == "classify_as_of" for v in c["violation_sites"])
    assert r.returncode == 1 and rep["ok"] is False


def test_behavioural_form_refuses_a_run_that_classified_nothing(tmp_path):
    """MUTANT 4 (vacuity): a test selection that never calls classify_as_of
    — the recording clock reports zero classifications and the proof FAILS
    rather than passing on silence."""
    tdir = tmp_path / "t"
    tdir.mkdir()
    (tdir / "test_nothing.py").write_text("def test_nothing():\n    assert True\n")
    r = subprocess.run([sys.executable, str(ARTIFACT), "--test-path", str(tdir / "test_nothing.py"),
                        "--json", str(tmp_path / "rep.json")], cwd=str(ROOT), capture_output=True, text=True)
    import json
    rep = json.loads((tmp_path / "rep.json").read_text())
    assert rep["behavioural"]["counts"]["classify_calls"] == 0
    assert r.returncode == 1 and rep["ok"] is False
    assert "zero classifications" in r.stdout
