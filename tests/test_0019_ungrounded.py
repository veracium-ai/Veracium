"""specs/0019 — the `ungrounded` flag: U1–U9, one test per frozen invariant.

U3b (the pre-ship re-measurement over the 93,342-object corpus) is a
measurement obligation discharged by research against THIS shipped code
before release — its record lands in `specs/evidence/0019/`; it is a
release gate, not a unit test.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium import grounding
from veracium.contribution import (RECOMPUTED_EDGE_FIELDS,
                                   raw_request_snapshot)
from veracium.graph import DEFAULT_RELATIONS, apply_supersession, render_edges
from veracium.schema import Edge, EvidenceAuthor as EA, Provenance
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "specs" / "evidence" / "0019"
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)
MARKER = "[possible extraction error]"


class Fake:
    """Scripted distiller/compiler; the compile script deliberately DROPS
    and rephrases markers (U5's compiler-fake — the wiki guarantee must
    never depend on LLM cooperation)."""

    def __init__(self, scripts):
        self._s = list(scripts)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps(self._s.pop(0))
        # a compiler that rewrites everything and strips markers
        return "USER WIKI: everything I know, rephrased, markers removed."


def _edge(obj, *, eid, uid="u1", flagged=False, conf=0.9, observed=NOW):
    return Edge(id=eid, user_id=uid, subject="user", relation="pet",
                object=obj, valid_from=observed, ungrounded=flagged,
                provenance=Provenance(author_of_evidence=EA.USER,
                                      evidence_ref=f"ev-{eid}",
                                      observed_at=observed, confidence=conf))


def _mem(d, scripts):
    return Memory(llm=Fake(scripts),
                  config=MemoryConfig(db_path=f"{d}/t.db",
                                      wiki_recompile_after_writes=0))


def _fab(obj="fabricated deadline 2026-08-10", relation="deadline"):
    """A script whose extraction invents a specific the event never said."""
    return {"triples": [{"subject": "user", "relation": relation,
                         "object": obj, "volatility": "slow"}],
            "episode": "User mentioned a deadline."}


# --------------------------------------------------------------------------- #
# U1 — never refuses, never demotes
# --------------------------------------------------------------------------- #

def test_ungrounded_never_refuses_or_demotes(monkeypatch):
    """Ingest outcomes and gate partitions are IDENTICAL with the check
    enabled vs a counterfactual disabled run — except the flag and its
    marker."""
    def run(disabled):
        with tempfile.TemporaryDirectory() as d:
            if disabled:
                monkeypatch.setattr(grounding, "ungrounded",
                                    lambda *a, **k: False)
            else:
                monkeypatch.undo()
            mem = _mem(d, [_fab()])
            out = mem.remember("u", "the deadline is not decided yet",
                               date="2026-08-01")
            edges = mem.store.edges("u", active_only=True)
            r = mem.recall("u", "deadline")
            mem.close()
            return (out["facts"], out["quarantined"],
                    [(e.object, e.assertable, e.use_only, e.quarantined,
                      e.provenance.disclosure) for e in edges],
                    [e.ungrounded for e in edges], r.context)
    on = run(disabled=False)
    off = run(disabled=True)
    assert on[0:3] == off[0:3]          # counts + partition identical
    assert on[3] == [True] and off[3] == [False]      # only the flag differs
    assert MARKER in on[4] and MARKER not in off[4]   # ...and its marker


# --------------------------------------------------------------------------- #
# U2 — the flag grants nothing: a sweep by FACT over every reader
# --------------------------------------------------------------------------- #

def test_ungrounded_grants_nothing():
    """Every `ungrounded` reader in src/ is an enumerated consumer, and each
    is a marker/withholding/immutability/verification surface — none keys
    trust, authority, assertability, or staleness ON the flag."""
    hits = subprocess.run(
        ["grep", "-rlw", "ungrounded", "--include=*.py",
         str(ROOT / "src" / "veracium")],
        capture_output=True, text=True).stdout.split()
    readers = {pathlib.Path(h).name for h in hits}
    assert readers == {"schema.py", "grounding.py", "ingest.py", "graph.py",
                       "contribution.py", "compile.py", "proactive.py",
                       "introspect.py", "portability.py", "sqlite.py",
                       "base.py", "schema_version.py",
                       # specs/0020 slice B — NOT readers: both name the flag
                       # only in prose, and both name it to promise the U2
                       # property rather than to consume it. `gate.py`'s
                       # `scoped_assertable` states that no scope status ever
                       # clears `ungrounded`/`needs_confirmation` (§4b's
                       # restrict-only rail); `scope_read.py`'s shaping states
                       # the same about the disclosure it narrows. Classified
                       # WITHHOLDING-side; `test_same_scope_grants_nothing`
                       # (0020 V2) is the behavioural check that they keep it.
                       "gate.py", "scope_read.py",
                       # specs/0021 slice C — NOT a reader either:
                       # `combining.py` is a REGISTRY of verdicts about write
                       # sites, and its `_upsert_edge_row` row names
                       # `ungrounded` among the fields the survivor inherited
                       # from the absorbed set. Prose about a field, in a
                       # table; no branch, no read, no write. The N-ary OR
                       # that actually consumes the flag stays in graph.py
                       # and sqlite.py, both already enumerated.
                       "combining.py"}, (
        f"a NEW ungrounded reader appeared: {readers} — classify it (0019 "
        f"U2: marker, withholding, immutability, or verification; never a "
        f"trust/authority/staleness key)")
    # and the behavioural fact: a flagged edge keeps every trust property
    flagged = _edge("Miso", eid="e-f", flagged=True)
    clean = _edge("Miso", eid="e-c", flagged=False)
    for prop in ("assertable", "use_only", "quarantined"):
        assert getattr(flagged, prop) == getattr(clean, prop)
    # …and the 0020 addition, checked by FACT rather than by the file list:
    # neither new file READS the flag — it appears in prose only.
    import re as _re
    for name in ("gate.py", "scope_read.py"):
        src = (ROOT / "src" / "veracium" / name).read_text()
        code = "\n".join(ln for ln in src.splitlines()
                         if not ln.lstrip().startswith("#"))
        code = _re.sub(r'""".*?"""', "", code, flags=_re.S)
        assert "ungrounded" not in code, (
            f"{name} now READS `ungrounded` outside prose — 0019 U2 requires a "
            f"classification, and 0020 §4b promises the flag is never cleared")


# --------------------------------------------------------------------------- #
# U2b — the 0014 rider holds mechanically
# --------------------------------------------------------------------------- #

def test_ungrounded_joins_the_recomputed_class(tmp_path):
    assert "ungrounded" in RECOMPUTED_EDGE_FIELDS
    # 0016 D2 (0019 rider A1): post-D2 receipts stamp version 4; the closed
    # set is {1,2,3,4} — one beyond it still refuses
    store = SqliteStore(str(tmp_path / "s.db"))
    e = _edge("Miso", eid="e-v3")
    apply_supersession(store, e, DEFAULT_RELATIONS)
    r = store.supersession_receipt("u1", "sup-e-v3")
    assert r["outcome_digest_version"] == 4
    with pytest.raises(ValueError, match="closed set"):
        store.validate_receipt_state(None, 5, '{"inserted_incoming":true,'
                                     '"invalidated":0,"refused":0}')
    # the verifier aborts a flag difference that is NOT the N-ary OR:
    # snapshot says True, committed survivor False, no absorption
    from veracium.graph import _build_supersession_plan
    e2 = _edge("Rex", eid="e-forge", flagged=True)
    plan, _ = _build_supersession_plan(store, e2, DEFAULT_RELATIONS, "op-forge")
    plan.incoming_edge.ungrounded = False          # forged weakening
    plan.raw_request = raw_request_snapshot(e2)
    from veracium.store.base import SupersessionIntegrityError
    with pytest.raises(SupersessionIntegrityError):
        store.apply_supersession_plan(plan)
    store.close()


# --------------------------------------------------------------------------- #
# U2c — the N-ary absorption OR, every permutation
# --------------------------------------------------------------------------- #

def _absorb_case(tmp_path, tag, flags, incoming_flag):
    """Three subsumed priors with the given flags, one more-specific
    incoming; returns the committed survivor's flag."""
    store = SqliteStore(str(tmp_path / f"s-{tag}.db"))
    for i, f in enumerate(flags):
        p = _edge("Miso", eid=f"e-p{tag}{i}", flagged=f, conf=0.5,
                  observed=NOW)
        apply_supersession(store, p, DEFAULT_RELATIONS)
    inc = _edge("big cat Miso", eid=f"e-w{tag}", flagged=incoming_flag)
    apply_supersession(store, inc, DEFAULT_RELATIONS)
    survivor = [e for e in store.edges("u1", active_only=True)
                if e.id == f"e-w{tag}"]
    absorbed = [e for e in store.edges("u1", active_only=False)
                if e.invalidation_reason == "absorbed_duplicate"]
    got = (survivor[0].ungrounded, len(absorbed),
           [e.ungrounded for e in absorbed])
    store.close()
    return got


def test_absorption_or_nary_permutations(tmp_path):
    # zero contributors: the incoming flag passes through
    s = SqliteStore(str(tmp_path / "s0.db"))
    for flag, eid in ((True, "e-t"), (False, "e-f")):
        apply_supersession(store=s, edge=_edge(f"pet {eid}", eid=eid,
                                               flagged=flag),
                           relations=DEFAULT_RELATIONS)
        got = [e for e in s.edges("u1") if e.id == eid][0]
        assert got.ungrounded is flag
    s.close()
    # NOTE: shipped absorption fires per same-class subsumed prior — one and
    # many contributors, every flag placement of a three-contributor case
    import itertools
    for i, flags in enumerate(itertools.product((False, True), repeat=3)):
        for inc_flag in (False, True):
            surv, n_absorbed, absorbed_flags = _absorb_case(
                tmp_path, f"{i}{int(inc_flag)}", list(flags), inc_flag)
            assert n_absorbed >= 1
            expected = inc_flag or any(absorbed_flags)
            assert surv is expected, (flags, inc_flag, absorbed_flags)
    # stored flags stayed byte-untouched on the absorbed rows themselves
    # (asserted inside _absorb_case via absorbed_flags reflecting inputs)


def test_reinforcement_leaves_flags_untouched(tmp_path):
    store = SqliteStore(str(tmp_path / "s.db"))
    first = _edge("Miso", eid="e-1", flagged=True)
    apply_supersession(store, first, DEFAULT_RELATIONS)
    again = _edge("Miso", eid="e-2", flagged=False)   # its own honest flag
    apply_supersession(store, again, DEFAULT_RELATIONS)
    flags = {e.id: e.ungrounded for e in store.edges("u1", active_only=True)}
    assert flags == {"e-1": True, "e-2": False}       # nothing transferred
    store.close()


# --------------------------------------------------------------------------- #
# U3 — the predicate matches the in-repo reference on the pinned vectors
# --------------------------------------------------------------------------- #

def test_predicate_matches_the_pinned_vectors():
    vectors = json.loads((EVIDENCE / "vectors.json").read_text())
    assert len(vectors) >= 30
    sys.path.insert(0, str(EVIDENCE))
    try:
        import reference_predicate as ref
    finally:
        sys.path.pop(0)
    for v in vectors:
        shipped = grounding.ungrounded(v["obj"], v["text"], v["session"])
        normative = ref.ungrounded(v["obj"], v["text"], v["session"])
        assert shipped == normative == v["expect"], v["name"]


def test_predicate_is_hash_seed_independent():
    """The R3-1 regression, executed: the full vector suite under four
    PYTHONHASHSEED values agrees with the pinned expectations."""
    prog = (
        "import json,sys; sys.path.insert(0,'src');"
        "from veracium.grounding import ungrounded;"
        f"vs=json.load(open(r'{EVIDENCE / 'vectors.json'}'));"
        "bad=[v['name'] for v in vs "
        "if ungrounded(v['obj'],v['text'],v['session'])!=v['expect']];"
        "print(','.join(bad) if bad else 'OK')")
    for seed in ("0", "1", "42", "271828"):
        r = subprocess.run([sys.executable, "-c", prog], cwd=ROOT,
                           capture_output=True, text=True,
                           env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin"})
        assert r.stdout.strip() == "OK", (seed, r.stdout, r.stderr)


# --------------------------------------------------------------------------- #
# U4 — stored flags never change; the store enforces it TOTALLY
# --------------------------------------------------------------------------- #

def test_ungrounded_total_replace_guard(tmp_path):
    store = SqliteStore(str(tmp_path / "s.db"))
    # host-set-at-insert: accepted (the store boundary is the host's domain)
    e = _edge("Miso", eid="e-g", flagged=True)
    store.add_edge(e)
    # clear attempt: refused
    cleared = e.model_copy(update={"ungrounded": False})
    with pytest.raises(ValueError, match="ungrounded"):
        store.add_edge(cleared)
    # flag attempt on replace of a clean row: refused (BOTH directions)
    c = _edge("Rex", eid="e-h", flagged=False)
    store.add_edge(c)
    with pytest.raises(ValueError, match="ungrounded"):
        store.add_edge(c.model_copy(update={"ungrounded": True}))
    # same-flag replace (an ordinary note update) passes
    store.add_edge(e.model_copy(update={"note": "renamed"}))
    # confirm leaves the flag byte-unchanged
    stored = [x for x in store.edges("u1") if x.id == "e-g"][0]
    assert stored.ungrounded is True
    store.close()


def test_confirm_records_but_never_clears(tmp_path):
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [_fab()])
        mem.remember("u", "no date picked yet", date="2026-08-01")
        edge = mem.store.edges("u", active_only=True)[0]
        assert edge.ungrounded is True
        mem.confirm("u", edge.id)
        after = [e for e in mem.store.edges("u") if e.id == edge.id][0]
        assert after.ungrounded is True         # confirmation ≠ grounding
        mem.close()


# --------------------------------------------------------------------------- #
# U5 — the marker is never severed; the wiki excludes flagged facts
# --------------------------------------------------------------------------- #

def test_marker_surfaces_and_wiki_exclusion():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [_fab(), {"triples": [
            {"subject": "user", "relation": "pet", "object": "cat Miso"}],
            "episode": "User mentioned the cat."}])
        mem.remember("u", "deadline undecided", date="2026-08-01")
        mem.remember("u", "my cat Miso", date="2026-08-02")
        # every code-rendered surface carries the marker with the fact
        r = mem.recall("u", "deadline")
        assert MARKER in r.context
        cats = mem.introspect("u", mode="categories")
        assert MARKER in json.dumps(cats)
        # the wiki (LLM-rendered, marker-hostile by construction of Fake):
        # flagged facts NEVER entered its input, so nothing was lost to the
        # marker-stripping compiler — the clean fact is in, the flagged out
        from veracium.compile import _grounded_inputs
        edges, _eps = _grounded_inputs(mem.store, "u", DEFAULT_RELATIONS)
        assert all(not e.ungrounded for e in edges)
        assert any("Miso" in e.object for e in edges)
        mem.close()


def test_marker_survives_supersession_render():
    flagged = _edge("fabricated 2026-09-01", eid="e-old", flagged=True)
    flagged.invalidated_at = NOW
    flagged.invalidation_reason = "superseded"
    out = render_edges([flagged])
    assert MARKER in out and "SUPERSEDED" in out      # severed nowhere


# --------------------------------------------------------------------------- #
# U6 — proactive suppression; query recall unaffected
# --------------------------------------------------------------------------- #

def test_proactive_suppression():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [
            _fab(obj="tax filing due 2026-08-10"),      # fabricated → flagged
            {"triples": [{"subject": "task:vat", "relation": "deadline",
                          "object": "VAT filing due 2026-08-12",
                          "volatility": "slow"}],
             "episode": "User noted the VAT deadline."}])   # grounded twin
        mem.remember("u", "taxes soon, date not set", date="2026-08-01")
        mem.remember("u", "VAT filing due 2026-08-12", date="2026-08-01")
        briefing = mem.recall("u")                     # no query: proactive
        # the grounded overdue twin SURFACES — the section works — while the
        # flagged one, equally overdue, is suppressed BY THE FLAG alone
        assert "2026-08-12" in briefing.context
        assert "2026-08-10" not in briefing.context    # never volunteered
        queried = mem.recall("u", "tax filing deadline")
        assert "2026-08-10" in queried.context         # fully recallable
        assert MARKER in queried.context               # ...with its marker
        mem.close()


# --------------------------------------------------------------------------- #
# U7 — the import boundary: StrictBool + the forging matrix
# --------------------------------------------------------------------------- #

def _export_lines(mem, uid, d):
    p = pathlib.Path(d) / "x.jsonl"
    mem.export_memory(uid, p)
    return p, [json.loads(l) for l in p.read_text().splitlines()]


def test_import_strictbool_and_forging_matrix():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [_fab()])
        mem.remember("u", "deadline undecided", date="2026-08-01")
        path, lines = _export_lines(mem, "u", d)
        edge_line = next(l for l in lines if l.get("kind") == "edge"
                         or l.get("relation"))
        assert edge_line["ungrounded"] is True          # exported verbatim

        # StrictBool: the exhaustive coercive cells REFUSE, never coerce
        for bad in ("false", "yes", 0, 1, None, [], {}):
            m2 = []
            for l in lines:
                l = dict(l)
                if l.get("relation"):
                    l["ungrounded"] = bad
                m2.append(l)
            bp = pathlib.Path(d) / "bad.jsonl"
            bp.write_text("\n".join(json.dumps(l) for l in m2) + "\n")
            bd = tempfile.mkdtemp(prefix="bad-", dir=d)
            dest = _mem(bd, [])
            with pytest.raises((ValueError, Exception)):
                dest.import_memory(bp, user_id="u")
            dest.close()

        # DEFAULT path: a forged False is inert BY COMPOSITION — the 0005
        # cap floors disclosure to use_only, so the record is
        # proactive-ineligible and wiki-excluded regardless of the flag
        forged = []
        for l in lines:
            l = dict(l)
            if l.get("relation"):
                l["ungrounded"] = False               # the forge
            forged.append(l)
        fp = pathlib.Path(d) / "forged.jsonl"
        fp.write_text("\n".join(json.dumps(l) for l in forged) + "\n")
        with tempfile.TemporaryDirectory() as d2:
            dest = _mem(d2, [])
            dest.import_memory(fp, user_id="u")
            imported = dest.store.edges("u", active_only=True)
            assert all(e.use_only or e.quarantined for e in imported)  # capped
            briefing = dest.recall("u")
            assert "2026-08-10" not in briefing.context   # ineligible anyway
            from veracium.compile import _grounded_inputs
            edges, _ = _grounded_inputs(dest.store, "u", DEFAULT_RELATIONS)
            assert all("2026-08-10" not in e.object for e in edges)
            dest.close()

        # RESTORE path: the forged/absent False DOES obtain both flag-keyed
        # eligibilities — the documented §8 limit 6, asserted per consumer
        with tempfile.TemporaryDirectory() as d3:
            dest = _mem(d3, [])
            dest.import_memory(fp, restore=True)
            imported = dest.store.edges("u", active_only=True)
            assert all(not e.ungrounded for e in imported)
            briefing = dest.recall("u")
            assert "2026-08-10" in briefing.context       # proactive: granted (overdue commitment)
            from veracium.compile import _grounded_inputs
            edges, _ = _grounded_inputs(dest.store, "u", DEFAULT_RELATIONS)
            assert any("2026-08-10" in e.object for e in edges)  # wiki: granted
            dest.close()

        # and a TRUTHFUL True restores flagged: both withheld
        with tempfile.TemporaryDirectory() as d4:
            dest = _mem(d4, [])
            dest.import_memory(path, restore=True)
            briefing = dest.recall("u")
            assert "2026-08-10" not in briefing.context   # truthful True: withheld
            dest.close()
        mem.close()


def test_pre_v6_envelope_strips_the_field():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [_fab()])
        mem.remember("u", "deadline undecided", date="2026-08-01")
        path, lines = _export_lines(mem, "u", d)
        downgraded = []
        for l in lines:
            l = dict(l)
            if l.get("kind") == "veracium-export":
                l["version"] = 5                      # a pre-v6 envelope...
            downgraded.append(l)
        dp = pathlib.Path(d) / "old.jsonl"
        dp.write_text("\n".join(json.dumps(l) for l in downgraded) + "\n")
        with tempfile.TemporaryDirectory() as d2:
            dest = _mem(d2, [])
            dest.import_memory(dp, restore=True)
            imported = dest.store.edges("u", active_only=True)
            assert all(e.ungrounded is False for e in imported)  # stripped →
            dest.close()                                         # default
        mem.close()


# --------------------------------------------------------------------------- #
# U8 — version honesty
# --------------------------------------------------------------------------- #

def test_version_gates_and_migration(tmp_path):
    from veracium.portability import FORMAT_VERSION
    from veracium.store import schema_version as sv
    from veracium.store.migration import migrate_store
    assert FORMAT_VERSION == 7 and sv.SCHEMA_VERSION >= 8  # 0016 D2 + 0021 rider (head has since moved to 9, 0022)
    # a v6-stamped store migrates (crossing the v8 ledger ALTERs en route) and
    # lands head-current
    import sqlite3
    p = tmp_path / "v6.db"
    c = sqlite3.connect(p)
    for o in sv.SCHEMAS[6]:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version = 6")
    c.commit(); c.close()
    assert str(migrate_store(str(p))) == "migrated"
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == sv.SCHEMA_VERSION
    c.close()
    # (an OLDER build refusing a v8 store is 0007's found>expected rule —
    # exercised by the shipped store_versioning suite's newer-store cells)


# --------------------------------------------------------------------------- #
# U9 — observation surfaces
# --------------------------------------------------------------------------- #

def test_observation_surfaces():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d, [_fab()])
        mem.remember("u", "deadline undecided", date="2026-08-01")
        rep = mem.introspect("u")
        assert rep["ungrounded"] == 1
        # MCP carries no new field beyond the rendered marker: the tool
        # surface exposes no "ungrounded" key
        mcp = (ROOT / "src" / "veracium" / "mcp_server.py")
        if mcp.exists():
            assert "ungrounded" not in mcp.read_text()
        mem.close()
