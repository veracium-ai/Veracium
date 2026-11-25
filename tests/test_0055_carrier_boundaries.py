"""0055 round 5: the two generated coverage artifacts are current, hold their invariants, and their checks refuse every
tampering (the P1 matrix both scripts point at).

  specs/evidence/0055/carrier_boundaries.py   per CARRIER: planted, and measured at every exit (carrier-boundaries.json)
  specs/evidence/0055/a5_type_census.py       per ARGUMENT: the write boundary's type census (a5-type-census.json)

`--check` is fast (the enumeration from the live code, the digests, the rendered .md); `--write` re-measures. A product
change makes both STALE until they are re-measured: a measured artifact is not current for code it never ran.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CB = _load("_0055_carrier_boundaries", "specs/evidence/0055/carrier_boundaries.py")
A5 = _load("_0055_a5_type_census", "specs/evidence/0055/a5_type_census.py")


def test_the_carrier_table_is_current():
    assert CB.check() == []


def test_the_a5_census_is_current():
    assert A5.check() == []


def test_the_carrier_table_holds_its_invariants():
    """Every planted row is found; every row's remedy leaves nothing (or the row is declared); no row reaches a
    provider, a served result or the CLI. A row the store refused records the refusal it got."""
    doc = json.loads(CB.JSON_OUT.read_text())
    s = doc["summary"]
    assert s["not_found"] == [] and s["remedy_not_gone"] == [] and s["leaks"] == [], s
    for r in doc["rows"]:
        if r["planted"]:
            assert r["finder"] and r["remedy"].endswith("gone"), r["row"]
        else:
            assert r["refused"].startswith("IntegrityError: "), r["row"]
    assert s["planted"] + s["refused_by_the_store"] == s["rows"] == len(CB.enumerate_rows())
    assert [d["row"] for d in doc["declared"]] == [d["row"] for d in CB.declared_rows()]


def test_the_a5_census_holds_its_invariants():
    """No violation; every screened row is refused by type, every other row reaches no further than str."""
    doc = json.loads(A5.JSON_OUT.read_text())
    s = doc["summary"]
    assert s["violations"] == [], s["violations"]
    assert s["refused_by_type"] == s["screened_own"] + s["screened_callee_d3"]
    assert s["no_further_than_str"] == s["unscreened"]
    assert s["screened_callee_d3"] > 0, "D3's callee screen is no longer read: the census lost a class"


def _tamper_json(path: Path, fn):
    doc = json.loads(path.read_text())
    fn(doc)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")


def _first_planted(doc):
    return next(r for r in doc["rows"] if r.get("planted"))


# (id, module, how it tampers, the sentence the check must print)
TAMPERS = [
    ("cb-drop-a-table", "CB", "enum-table", "row set differs from the enumeration"),
    ("cb-drop-a-leaf", "CB", "enum-leaf", "row set differs from the enumeration"),
    ("cb-drop-a-declared-row", "CB", "declared", "declared rows differ"),
    ("cb-a-row-edited", "CB", "row", "the summary is not the rows' summary"),
    ("cb-md-edited", "CB", "md", "the .md is not the JSON's rendering"),
    ("cb-stale", "CB", "digest", "stale"),
    ("a5-drop-a-row", "A5", "enum-row", "rows or screens differ from the code"),
    ("a5-drop-the-callee-screen", "A5", "enum-screen", "rows or screens differ from the code"),
    ("a5-outcome-edited", "A5", "outcome", "an outcome is not its row's measurement"),
    ("a5-md-edited", "A5", "md", "the .md is not the JSON's rendering"),
    ("a5-stale", "A5", "digest", "stale"),
]


@pytest.mark.parametrize("tid,which,how,expect", TAMPERS, ids=[t[0] for t in TAMPERS])
def test_the_check_refuses_each_tampered_artifact(tmp_path, monkeypatch, tid, which, how, expect):
    """Each artifact's check, on a copy, after ONE tampering: the row set (a table or a leaf dropped from the
    enumeration, an A5 row or its callee screen dropped), a declared row, a measured row, an outcome, the .md, the
    product's bytes. The untampered copy passes first, so a refusal is the tampering's."""
    mod = CB if which == "CB" else A5
    j, m = tmp_path / mod.JSON_OUT.name, tmp_path / mod.MD_OUT.name
    j.write_bytes(mod.JSON_OUT.read_bytes())
    m.write_bytes(mod.MD_OUT.read_bytes())
    monkeypatch.setattr(mod, "JSON_OUT", j)
    monkeypatch.setattr(mod, "MD_OUT", m)
    assert mod.check() == [], "the untampered copy must pass"
    if how == "enum-table":
        real = CB.side_columns
        monkeypatch.setattr(CB, "side_columns", lambda store: [tc for tc in real(store) if tc[0] != real(store)[0][0]])
    elif how == "enum-leaf":
        real_leaves = CB.leaf_paths
        monkeypatch.setattr(CB, "leaf_paths", lambda model: real_leaves(model)[1:])
    elif how == "declared":
        _tamper_json(j, lambda d: d["declared"].pop())
    elif how == "row":
        def edit(d):
            r = _first_planted(d)
            r["served"] = dict(r["served"], **{"library recall": "LEAK"})
        _tamper_json(j, edit)
    elif how in ("md",):
        m.write_text(m.read_text() + "\nan edit\n")
    elif how == "digest":
        monkeypatch.setattr(mod, "_src_digest", lambda: "0" * 64)
    elif how == "enum-row":
        real_census = A5.census
        monkeypatch.setattr(A5, "census", lambda C=None: real_census(C)[1:])
    elif how == "enum-screen":
        real_census = A5.census
        monkeypatch.setattr(A5, "census", lambda C=None: [dict(r, screened_by=None if r["screened_by"] == "callee:D3"
                                                                else r["screened_by"]) for r in real_census(C)])
    elif how == "outcome":
        def edit(d):
            d["rows"][0]["outcome"] = "VIOLATION" if d["rows"][0]["outcome"] != "VIOLATION" else "refused by type"
        _tamper_json(j, edit)
    problems = mod.check()
    assert problems and any(expect in p for p in problems), (tid, problems)
