"""INV-SA1–SA12's mutation table (0007 §4g.8, 0013 §5f.4; 0007 I6): specs/evidence/0007/sa_mutants.py.

The table is current and every row good; the spec's mutant PHRASES equal the table's carriers (research's I6 Q2: a
missing mutant fails by name, not by review); and the table check refuses each tampered table, including a carrier
that names a matrix row that does not exist.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name="veracium_sa_mutants"):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "specs" / "evidence" / "0007" / "sa_mutants.py")
        m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m)
    return sys.modules[name]


sm = _load()


def test_the_mutation_table_is_current_and_every_row_good():
    assert sm.problems() == []


def test_every_spec_mutant_phrase_has_exactly_one_carrier():
    """The complement check: the phrases §4g.8 and 0013 §5f.4 name EQUAL the carriers' keys, and each carrier
    resolves. Read from the spec's bytes and the matrices' ASTs, never from a list typed beside them."""
    ph = sm.phrases()
    # the invariant set is DERIVED from the two specs' own INV-SA rows (0007 §4g.8 and 0013 §5f.4), never typed: a
    # hand range read INV-SA13 (0007 v24.1) as an extra phrase set
    rows = set()
    for spec in ("0007-store-schema-versioning.md", "0013-store-migrations.md"):
        rows |= set(re.findall(r"^\| \*\*(INV-SA\d+)\*\*", (ROOT / "specs" / spec).read_text(), re.M))
    assert len(ph) >= 45 and {k[0] for k in ph} == rows, (sorted({k[0] for k in ph}), sorted(rows))
    assert sm.carrier_problems() == []


def test_a_phrase_without_a_carrier_or_a_carrier_without_a_phrase_fails_by_name(monkeypatch):
    first = sorted(sm.CARRIERS)[0]
    monkeypatch.setattr(sm, "CARRIERS", {k: v for k, v in sm.CARRIERS.items() if k != first})
    assert any(f"{first[0]} phrase {first[1]} has no carrier" in p for p in sm.carrier_problems())
    monkeypatch.setattr(sm, "CARRIERS", {**sm.CARRIERS, ("INV-SA1", 99): ("mutant", sm.MUTANTS[0][0])})
    assert any("carrier 99 has no phrase" in p for p in sm.carrier_problems())


def test_a_citation_of_a_row_that_does_not_exist_fails(monkeypatch):
    k = next(k for k, c in sorted(sm.CARRIERS.items()) if c[0] == "cite")
    ref = sm.CARRIERS[k][1].rsplit("::", 1)[0]
    monkeypatch.setattr(sm, "CARRIERS", {**sm.CARRIERS, k: ("cite", f"{ref}::a row nobody wrote")})
    assert any("has no row 'a row nobody wrote'" in p for p in sm.carrier_problems())


def _base():
    t = json.loads(sm.TABLE.read_text(encoding="utf-8"))
    t["header"]["digests"] = sm._digests(ROOT)
    return t


def _write(tmp_path, t, redigest=True):
    if redigest:
        t["body_sha256"] = hashlib.sha256(sm.canonical({k: v for k, v in t.items() if k != "body_sha256"})).hexdigest()
    p = tmp_path / "mutation-table.json"
    p.write_text(sm.render(t), encoding="utf-8")
    return p


TAMPERS = {
    "edited after writing": (lambda t: t["rows"][0].__setitem__("what", "edited"), False,
                             "does not match its own body digest"),
    "a row not killed": (lambda t: t["rows"][0].update(outcome="SURVIVED"), True, "not a good row"),
    "a missing row": (lambda t: t["rows"].pop(), True, "the rows are not one per mutant"),
    "a stale digest": (lambda t: t["header"]["digests"].__setitem__(sm.SV, "0" * 64), True, "stale: "),
    "a changed definition": (lambda t: t["header"]["definitions"].__setitem__(sm.MUTANTS[0][0], "0" * 64), True,
                             "the mutant definitions differ"),
    "a red clean run": (lambda t: t["header"]["clean"]["last"].__setitem__("ok", False), True,
                        "the clean runs are not both green"),
    "a classifier control that killed": (lambda t: t["controls"][0].update(outcome="KILLED"), True,
                                         "negative control is not good"),
    "another spec": (lambda t: t["header"].__setitem__("spec", "0013"), True, "not 0007/INV-SA1-SA12"),
}


def test_the_table_check_refuses_each_tampered_table(tmp_path):
    check = _load().problems                                  # the artifact this matrix binds (P1): sa_mutants.py
    (tmp_path / "control").mkdir()
    assert check(_write(tmp_path / "control", _base())) == []           # the untampered copy passes
    for name, (tamper, redigest, want) in TAMPERS.items():
        t = copy.deepcopy(_base())
        tamper(t)
        d = tmp_path / name.replace(" ", "-")
        d.mkdir()
        probs = check(_write(d, t, redigest))
        assert any(want in p for p in probs), (name, probs)
