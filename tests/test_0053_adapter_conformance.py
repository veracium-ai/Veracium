"""specs/0053, the adapter conformance suite: every adapter hands its framework what the library gives.

The oracle (specs/evidence/0053/adapter_conformance/checks.py) is the served MCP surface for schemas and descriptions
and the `*_impl` functions for values, computed in the same run over one fixture store holding every trust class
(fixture.py). The core (`veracium.adapters._surface`) is the green control; the LangChain adapter runs when the
`langchain` extra is installed, and skips by name otherwise. Each check K1-K8 is shown red against its own mutants,
applied to the adapter under test (mutants.py), and a kill counts only when exactly the families its row names go red.
"""
import os
import pathlib
import sys

import pytest

pytest.importorskip("mcp", reason="specs/0053: the oracle reads the served MCP surface, which needs the mcp extra")

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "specs" / "evidence" / "0053"))

from adapter_conformance import canon as K  # noqa: E402
from adapter_conformance import checks as C  # noqa: E402
from adapter_conformance import drivers as D  # noqa: E402
from adapter_conformance import fixture as F  # noqa: E402
from adapter_conformance import mutants as MU  # noqa: E402
from adapter_conformance import planted as PL  # noqa: E402
from adapter_conformance import rows as R  # noqa: E402

from veracium.adapters import _surface  # noqa: E402


def _langchain():
    if "langchain" in os.environ.get("VERACIUM_ADAPTER_ROWS", "").split(","):
        import langchain_core  # noqa: F401  (the CI job that names the row: a missing framework FAILS, never skips)
    pytest.importorskip("langchain_core", reason="specs/0053: the LangChain row needs the langchain extra")
    import importlib.metadata
    name, pinned = R.ROWS["langchain"]["framework"]
    got = importlib.metadata.version(name)
    assert got == pinned, (f"the LangChain row is pinned to {name} {pinned} and {got} is installed: a framework "
                           f"update can change serialisation, so the row moves with a re-run, never silently")
    from veracium.adapters import langchain
    return langchain


def _factory(adapter, surface=None, lc=None):
    if adapter == "core":
        s = surface or _surface
        return lambda mem, b: D.CoreDriver(s, mem, b)
    return lambda mem, b: D.LangChainDriver(lc, mem, b)


@pytest.fixture(scope="module")
def oracle(tmp_path_factory):
    return C.Oracle(str(tmp_path_factory.mktemp("conformance")))


def test_the_oracle_holds_every_trust_class(oracle):
    """§2's anchors, before any adapter: a check whose oracle holds nothing to carry passes every adapter."""
    assert C.anchors(oracle) == []


def test_the_declared_lists_are_the_measured_ones(oracle):
    """§3a: the leaves that vary between two reference runs are the declared id and clock lists, both ways, per clock
    group; the two runs agree under the canonical form (its green control)."""
    assert C.measured_lists(oracle) == []


def test_every_served_parameter_is_exercised(oracle):
    """Research's stage 1, S1-1: every served parameter takes a non-default value in a compared case outside K6 (or is
    refusal-only, with its K6 case), so a mutant rewriting it has somewhere to be seen."""
    assert C.parameter_census(oracle) == []


def test_the_parameter_census_names_an_unexercised_parameter(oracle):
    """The census's negative: drop the cases that pass record_procedure a non-default author, and it names that
    parameter (the gap stage 1 found), and nothing else."""
    import copy
    o = copy.copy(oracle)
    o.doc = dict(oracle.doc, cases=[c for c in oracle.doc["cases"]
                                    if not (c["tool"] == "record_procedure" and "author" in c["args"]
                                            and c["family"] != "K6")])
    assert C.parameter_census(o) == ["record_procedure.author: no compared case outside K6 passes it a non-default value "
                                     "that the reference does not refuse"]


def test_the_parameter_census_does_not_count_a_refused_case(oracle):
    """Research's stage 2, N1: with the one WRITING derived_from case gone, record_procedure.derived_from is passed only
    in a case the reference refuses (attempted_elevation under `none`), and the census names it."""
    import copy
    o = copy.copy(oracle)
    o.doc = dict(oracle.doc, cases=[c for c in oracle.doc["cases"] if c["id"] != "K7-direct-writes-derived"])
    assert C.parameter_census(o) == ["record_procedure.derived_from: no compared case outside K6 passes it a non-default "
                                     "value that the reference does not refuse"]


def test_a_read_that_writes_is_named_by_the_anchors(tmp_path, monkeypatch):
    """Research's stage 2, N2: I12 shown red. recall_impl is planted to write (remember_impl first) and the anchors
    name every recall case's reference store as written; the unplanted oracle's anchors are clean (the first cell)."""
    real = C.M.recall_impl

    def writing_recall(mem, user_id, *a, **kw):
        C.M.remember_impl(mem, user_id, "USER: a planted write. #fx-W1", date="2026-07-09", source_id=F.CHAT)
        return real(mem, user_id, *a, **kw)
    monkeypatch.setattr(C.M, "recall_impl", writing_recall)
    o = C.Oracle(str(tmp_path))
    found = [x for x in C.anchors(o) if "the reference read wrote the store" in x]
    recalls = [c["id"] for c in o.doc["cases"] if c["tool"] == "recall"]
    assert sorted(x.split("VACUOUS: ")[1].split(":")[0] for x in found) == sorted(recalls), found


@pytest.mark.parametrize("adapter", ["core", "langchain"])
def test_a_raise_of_another_type_reaches_the_model_as_a_tool_error(oracle, monkeypatch, adapter):
    """Research's stage 2, N3, the witness for S1-4: a library raise that is not a ValueError reaches the model as the
    tool-error result with its message, on each row, as FastMCP reports it; it never escapes into the agent loop."""
    lc = _langchain() if adapter == "langchain" else None

    def planted(*a, **kw):
        raise RuntimeError("a planted RuntimeError from the library")
    monkeypatch.setattr(C.M, "answer_impl", planted)
    mem = F.open_memory(oracle.fresh(f"raise-{adapter}"))
    try:
        drv = _factory(adapter, lc=lc)(mem, C.binding(oracle.doc, "none"))
        got = drv.decode(drv.call("answer", {"query": "what is the user's diet?"}))
    finally:
        mem.close()
    assert got == ("error", "a planted RuntimeError from the library"), got


def test_the_registration_is_read_under_the_hosts_capability(oracle, caplog):
    """Research's stage 1, S1-3: the server an adapter builds to read the served surface logs the capability the host
    bound, never the default (0031 I3's operator line)."""
    import logging
    mem = F.open_memory(oracle.fresh("caplog"))
    try:
        with caplog.at_level(logging.INFO, logger="veracium.mcp"):
            _surface.Binding(mem, user_id="u1", capability="direct")
    finally:
        mem.close()
    lines = [r.getMessage() for r in caplog.records if r.name == "veracium.mcp"]
    assert lines and all("'direct'" in m for m in lines) and not any("'none'" in m for m in lines), lines


def test_the_oracle_imports_no_adapter_code():
    """0053 v0.3 I10 (§10 Q4): the oracle side (checks, canon, fixture, planted) imports nothing from veracium.adapters,
    so the oracle never reuses the code under test; the scan's anchor proves it parsed what it names."""
    assert C.oracle_import_problems() == []


@pytest.mark.parametrize("src,want", [
    ("from veracium.adapters._surface import Binding\n", "from veracium.adapters._surface import Binding"),
    ("import veracium.adapters._surface as x\n", "import veracium.adapters._surface"),
    ("from veracium import adapters\n", "from veracium import adapters"),
    ("import veracium\nveracium.adapters\n", "veracium.adapters read as an attribute"),
    ("import veracium\nimport importlib\nimportlib.import_module('veracium.adapters.langchain')\n",
     "import_module('veracium.adapters.langchain')"),
    ("import veracium\n__import__('veracium.adapters')\n", "__import__('veracium.adapters')"),
    ("", "parsed to nothing"),
    ("import json\n", "ANCHOR: no `veracium` import"),
])
def test_the_import_scan_refuses_each_form(tmp_path, src, want):
    """The I10 scan's negatives: each import form, an empty module, and a scan with no veracium import at all."""
    f = tmp_path / "planted_oracle.py"
    f.write_text(src)
    found = C.oracle_import_problems([str(f)])
    assert any(want in x for x in found), found


def test_the_canonicaliser_judges_its_planted_pairs(tmp_path):
    assert PL.misjudged(K, str(tmp_path)) == []


@pytest.mark.parametrize("cid", [m[0] for m in MU.CANON_MUTANTS])
def test_the_canonicaliser_catches_each_of_its_mutants(cid, tmp_path):
    """canon.py under each §4 canonicaliser mutant misjudges at least one planted pair."""
    edits = dict((m[0], m[1]) for m in MU.CANON_MUTANTS)[cid]
    mutated = MU.load_canon(edits, str(tmp_path))
    assert PL.misjudged(mutated, str(tmp_path / "pairs")), f"canon.py mutant {cid} judged every planted pair right"


def test_a_provenance_leaf_declared_as_an_id_is_refused(oracle):
    """§4's fourth canonicaliser mutant: a provenance leaf added to the declared id list is refused by the measured
    lists (it never varies), so it cannot rename a dropped field out of sight."""
    ids, clocks = C.DECLARED["dated"]
    bad = dict(C.DECLARED, dated=(ids | {("edges", "json", ("$", "provenance", "author_of_evidence"))}, clocks))
    found = C.measured_lists(oracle, bad)
    assert any("author_of_evidence" in f and "never varies" in f for f in found), found


def test_the_core_conforms(oracle):
    """The green control: the framework-free core passes every family."""
    assert C.run_families(oracle, _factory("core"), "core") == {f: [] for f in C.FAMILIES}


def test_the_langchain_adapter_conforms(oracle):
    lc = _langchain()
    assert C.run_families(oracle, _factory("langchain", lc=lc), "langchain") == {f: [] for f in C.FAMILIES}


def test_the_langchain_decoder_is_lossless(oracle):
    _langchain()
    assert C.check_decoder(oracle, D.LangChainDriver) == []


_ROW = [(m, a) for m in MU.MUTANTS for a in m.adapters]


@pytest.mark.parametrize("mutant,adapter", _ROW, ids=[f"{m.id}-{a}" for m, a in _ROW])
def test_the_mutant_row_kills_exactly_its_families(oracle, tmp_path, mutant, adapter):
    """mutants.py applied to the adapter under test; checks.py's families must go red EXACTLY as the row names."""
    if adapter == "langchain":
        _langchain()
    surface, lc = MU.materialise(mutant, str(tmp_path), with_langchain=adapter == "langchain")
    res = C.run_families(oracle, _factory(adapter, surface, lc), f"{mutant.id}-{adapter}")
    red = MU.red_families(res)
    assert red == mutant.expect, (f"{mutant.id} on {adapter}: red {sorted(red)}, the row names {sorted(mutant.expect)}"
                                  f"; failures: { {f: v[:2] for f, v in res.items() if v} }")


def test_a_mutant_whose_site_moved_is_refused(tmp_path):
    """mutants.py refuses an edit whose anchor is absent or repeated, and one that leaves the file unchanged: only a
    mutant that really changed the adapter can count (§4, harness's point 1)."""
    anchor = "handle_tool_error=True)"
    for n, (edits, what) in enumerate([
            ([(MU.L, "handle_tool_error=Maybe)", "x")], "occurs 0 times"),
            ([(MU.S, "return _mcp.", "return  _mcp.")], "times, not once"),
            ([(MU.L, anchor, anchor)], "unchanged")]):
        with pytest.raises(MU.DoesNotApply, match=what):
            MU.apply_edits(MU.ADAPTERS, str(tmp_path / f"m{n}"), edits)


def test_the_surface_refuses_a_registration_it_cannot_answer(tmp_path, oracle):
    """A served tool the core has no binding for (or a binding for a tool not served) is refused at construction,
    never dropped or answered by nothing."""
    dst = str(tmp_path / "pkg")
    MU.apply_edits(MU.ADAPTERS, dst, [(MU.S, '"describe_procedures")\n', '"describe_procedures", "forget")\n')])
    surface, _ = MU.load_package(dst, with_langchain=False)
    mem = F.open_memory(oracle.fresh("registration"))
    try:
        with pytest.raises(RuntimeError, match="is refused"):
            surface.served_tools(mem)
    finally:
        mem.close()


def test_the_host_bindings_refuse_a_malformed_value(oracle):
    mem = F.open_memory(oracle.fresh("bindings"))
    try:
        with pytest.raises(ValueError):
            _surface.Binding(mem, user_id="u1", capability="trusted")       # outside the closed set (0031 §4a)
        with pytest.raises(ValueError):
            _surface.Binding(mem, user_id="")
    finally:
        mem.close()


def test_the_scripted_model_refuses_an_ambiguous_or_unknown_marker():
    llm = F.ScriptedComplete()
    with pytest.raises(AssertionError, match="2 markers"):
        llm("event #fx-G and #fx-S1", role="distill")
    with pytest.raises(AssertionError, match="no extraction"):
        llm("event #fx-NOPE", role="distill")


def test_each_adapter_row_runs_its_mutants():
    """§5: every adapter has a row, every mutant names only adapters with rows, and every row runs at least one mutant
    per family K1-K8 (a family with no mutant on an adapter would be a check never shown red there)."""
    assert set(R.ROWS) == {"core", "langchain"}
    for adapter in R.ROWS:
        names = set()
        for m in MU.MUTANTS:
            assert set(m.adapters) <= set(R.ROWS), m.id
            if adapter in m.adapters:
                names |= m.expect
        assert names == set(C.FAMILIES), (adapter, sorted(set(C.FAMILIES) - names))
    assert os.path.basename(MU.CANON) == "canon.py"
