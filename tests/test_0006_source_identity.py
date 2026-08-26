"""specs/0006 — Slice A: the source-identity foundation.

Pins the accepted invariants that live entirely in the store/primitive layer:
- I11  the local `store_identity` origin is durable (survives reopen).
- I12  the identity digest is the ONE shared canonical primitive — length-framed,
       domain-separated; `("ab","c")` and `("a","bc")` cannot collide.
- I13  an absent `source_id` yields NO digest — never a `(origin, NULL)` pseudo-source.
Plus the v4→v5 migration: it mints the singleton transactionally, is additive, and does
NOT backfill existing rows; and the provenance fields round-trip through `edges.json`.
"""
import sqlite3
import uuid

import pytest

from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance
from veracium.source_identity import resolve_origin, source_identity_digest
from veracium.store.migration import migrate_store
from veracium.store.schema_version import SCHEMA_V4, SCHEMA_VERSION
from veracium.store.sqlite import SqliteStore

U = "u1"


def _build_v4(path):
    c = sqlite3.connect(path)
    for o in SCHEMA_V4:
        c.execute(o.ddl)
    c.execute("PRAGMA user_version = 4")
    c.commit()
    c.close()


# -- I12: the canonical, shared digest ------------------------------------------------
def test_source_identity_digest_is_canonical_and_shared():
    # length-framing kills the bare-concatenation collision
    assert source_identity_digest("ab", "c") != source_identity_digest("a", "bc")
    # deterministic + shared: the same pair digests identically every call (what lets
    # 0014's write and revoke_source's lookup re-derive one key)
    assert source_identity_digest("o", "s") == source_identity_digest("o", "s")
    # distinct pairs, distinct digests
    assert source_identity_digest("o", "s1") != source_identity_digest("o", "s2")
    assert source_identity_digest("o1", "s") != source_identity_digest("o2", "s")
    # hex sha256
    d = source_identity_digest("o", "s")
    assert len(d) == 64 and int(d, 16) >= 0


# -- I13: absent source_id ⇒ no digest, no pseudo-source -------------------------------
def test_absent_source_id_produces_no_groupable_digest():
    # no source_id ⇒ no identity ⇒ no digest (never (origin, NULL))
    assert source_identity_digest("local", None) is None
    assert source_identity_digest(None, None) is None
    # two unknown-source records under the same resolved origin do NOT collapse into one
    # groupable digest — both are None, which SQL NULL never joins to itself
    a = source_identity_digest(resolve_origin(None, "LOCAL"), None)
    b = source_identity_digest(resolve_origin(None, "LOCAL"), None)
    assert a is None and b is None
    # a present source_id under a resolved origin DOES digest (contrast)
    assert source_identity_digest(resolve_origin(None, "LOCAL"), "mailbox") is not None


def test_digest_requires_a_resolved_origin():
    # a None origin with a present source_id is a programming error — resolve first
    with pytest.raises(ValueError):
        source_identity_digest(None, "mailbox")


def test_resolve_origin_is_the_one_chokepoint():
    local = "LOCAL-ORIGIN"
    assert resolve_origin(None, local) == local          # absent → this store
    assert resolve_origin("FOREIGN", local) == "FOREIGN"  # present (imported) → kept (I2b)


# -- I11: the store_identity singleton is durable -------------------------------------
def test_fresh_store_mints_a_uuid4_origin(tmp_path):
    s = SqliteStore(str(tmp_path / "fresh.db"))
    o = s.local_origin()
    parsed = uuid.UUID(o)                                 # canonical textual encoding
    assert parsed.version == 4                            # UUIDv4 (122 random bits)
    assert str(parsed) == o                               # canonical form, not munged


def test_store_origin_survives_reopen(tmp_path):
    p = str(tmp_path / "durable.db")
    origin = SqliteStore(p).local_origin()
    # reopen a fresh handle on the same path
    assert SqliteStore(p).local_origin() == origin        # I11: durable across reopen


def test_store_identity_is_a_singleton(tmp_path):
    p = str(tmp_path / "singleton.db")
    SqliteStore(p)
    with sqlite3.connect(p) as c:
        assert c.execute("SELECT COUNT(*) FROM store_identity").fetchone()[0] == 1
        # CHECK(id = 1) forbids a second row
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("INSERT INTO store_identity(id, origin) VALUES(2, 'x')")


# -- the v4→v5 migration --------------------------------------------------------------
def test_v4_to_v5_migration_mints_the_singleton_and_does_not_backfill(tmp_path):
    p = str(tmp_path / "v4.db")
    _build_v4(p)
    # an existing edge whose provenance stores NO origin/source_id (a pre-0006 row)
    e = Edge(id="e1", user_id=U, subject="user", relation="works_as", object="acme",
             provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev"))
    before = e.model_dump_json()
    with sqlite3.connect(p) as c:
        c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                  "VALUES(?,?,?,?,?,1,0,?)", (e.id, U, "user", "works_as", "acme", before))
        c.commit()

    assert str(migrate_store(p)) == "migrated"

    with sqlite3.connect(p) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        # the singleton was minted, transactionally, with a valid UUIDv4 origin
        rows = c.execute("SELECT id, origin FROM store_identity").fetchall()
        assert len(rows) == 1 and rows[0][0] == 1
        assert uuid.UUID(rows[0][1]).version == 4
        # NO backfill — the existing edge row's json is byte-unchanged, origin still absent
        after = c.execute("SELECT json FROM edges WHERE id='e1'").fetchone()[0]
        assert after == before
        assert Edge.model_validate_json(after).provenance.origin is None
    # opens cleanly at head, and re-running is idempotent (origin unchanged)
    o1 = SqliteStore(p).local_origin()
    assert str(migrate_store(p)) == "current"
    assert SqliteStore(p).local_origin() == o1            # migration did not re-mint


def test_provenance_carries_origin_and_source_id_through_the_json_blob(tmp_path):
    """The fields need no DDL — they round-trip through edges.json (extra=ignore aside)."""
    prov = Provenance(author_of_evidence=EvidenceAuthor.USER,
                      evidence_ref="ev", source_id="mailbox:primary", origin="STORE-A")
    back = Provenance.model_validate_json(prov.model_dump_json())
    assert back.source_id == "mailbox:primary" and back.origin == "STORE-A"
    # absent by default (a local record); an empty string is rejected (§4 rule 5)
    assert Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev").source_id is None
    with pytest.raises(Exception):
        Provenance(author_of_evidence=EvidenceAuthor.USER,
                   evidence_ref="ev", source_id="")


# ============================ Slice B: ingest + resolve-at-read =======================
import json
import tempfile

from veracium import EvidenceAuthor as _EA, Memory, MemoryConfig


class _FakeComplete:
    """Returns the next scripted extraction JSON, ignoring the prompt."""
    def __init__(self, scripts):
        self._scripts = list(scripts); self.calls = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._scripts[self.calls]; self.calls += 1
        return json.dumps(out)


def _mem(d, scripts):
    return Memory(llm=_FakeComplete(scripts),
                  config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))


def _active(mem, u, relation):
    return [e for e in mem.store.edges(u, active_only=True) if e.relation == relation]


def test_source_id_is_host_supplied_never_extractor_derived(tmp_path):
    # I1: the extractor emits a `source_id` in its triple; the host supplies NONE.
    # The stored provenance source_id is None — the model's value is ignored entirely.
    scripts = [{"triples": [{"subject": "user", "relation": "works_as", "object": "chef",
                             "source_id": "EXTRACTOR-EVIL"}],
                "episode": "noted"}]
    mem = _mem(str(tmp_path), scripts)
    mem.remember("u", "USER: I'm a chef", date="2026-06-01")     # no source_id
    e = _active(mem, "u", "works_as")[0]
    assert e.provenance.source_id is None                        # extractor's value never used


def test_host_source_id_threads_onto_every_record(tmp_path):
    scripts = [{"triples": [{"subject": "user", "relation": "works_as", "object": "chef"}],
                "episode": "User is a chef."}]
    mem = _mem(str(tmp_path), scripts)
    mem.remember("u", "USER: I'm a chef", date="2026-06-01", source_id="mailbox:primary")
    e = _active(mem, "u", "works_as")[0]
    assert e.provenance.source_id == "mailbox:primary"
    eps = mem.store.episodes("u")
    assert eps and all(ep.provenance.source_id == "mailbox:primary" for ep in eps)


def test_local_records_never_carry_an_origin_and_resolve_to_the_singleton(tmp_path):
    scripts = [{"triples": [{"subject": "user", "relation": "works_as", "object": "chef"}],
                "episode": "noted"}]
    mem = _mem(str(tmp_path), scripts)
    mem.remember("u", "USER: I'm a chef", date="2026-06-01", source_id="mailbox")
    e = _active(mem, "u", "works_as")[0]
    assert e.provenance.origin is None                           # I2a: no local origin, ever
    # it resolves to THIS store's singleton at the one chokepoint
    assert resolve_origin(e.provenance.origin, mem.store.local_origin()) == mem.store.local_origin()


def test_origin_is_not_a_local_entry_point_parameter(tmp_path):
    # I2a structurally: there is no way for a local caller to name an origin
    scripts = [{"triples": [], "episode": "noted"}]
    mem = _mem(str(tmp_path), scripts)
    with pytest.raises(TypeError):
        mem.remember("u", "x", date="2026-06-01", origin="FORGE-ANOTHER-STORE")


def test_source_id_changes_no_decision(tmp_path):
    """I5/I4 — (origin, source_id) groups but never grants: differing source_ids do NOT
    alter supersession, disclosure, or third-party routing, and never clear staleness."""
    scripts = [
        {"triples": [{"subject": "user", "relation": "prefers", "object": "concise", "volatility": "slow"}],
         "episode": "prefers concise"},
        {"triples": [{"subject": "user", "relation": "prefers", "object": "detailed", "volatility": "slow"}],
         "episode": "prefers detailed"},
        # a third-party email — disclosure/routing must be identical with or without source_id
        {"triples": [{"subject": "org:x", "relation": "third_party_claim", "object": "you owe $9"}],
         "episode": "billing claim"},
    ]
    mem = _mem(str(tmp_path), scripts)
    mem.remember("u", "USER: concise please", date="2026-06-01", source_id="mailbox:A")
    mem.remember("u", "USER: detailed now", date="2026-06-02", source_id="mailbox:B")
    pref = _active(mem, "u", "prefers")
    # functional supersession is unaffected by the differing source_id — exactly one active
    assert len(pref) == 1 and pref[0].object == "detailed"
    # third-party content stays quarantined/use-only regardless of source_id (routing ignores it)
    mem.remember("u", "From X: you owe $9", date="2026-06-03",
                 author=_EA.THIRD_PARTY, event_type="email", source_id="mailbox:C")
    tp = [e for e in mem.store.edges("u", active_only=True) if e.subject == "org:x"]
    assert tp and tp[0].provenance.third_party_influenced
    assert tp[0].provenance.disclosure.value in ("quarantined", "use_only")


# ============================ Slice C: portability ===================================
from veracium.portability import FORMAT_VERSION, export_memory, import_memory


def _mem_at(db, scripts):
    return Memory(llm=_FakeComplete(scripts),
                  config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))


def _lines(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def _write_lines(p, header, recs):
    with open(p, "w") as f:
        f.write(json.dumps(header) + "\n")
        for r in recs:
            f.write(json.dumps(r) + "\n")


_SCRIPT = [{"triples": [{"subject": "user", "relation": "works_as", "object": "chef"}],
            "episode": "User is a chef."}]


def test_export_materialises_and_import_roundtrips_source_id_and_origin(tmp_path):
    # I6: export round-trips source_id AND the RESOLVED origin
    src = _mem_at(str(tmp_path / "src.db"), _SCRIPT)
    src.remember("u", "x", date="2026-01-01", source_id="mailbox:primary")
    src_origin = src.store.local_origin()
    exp = str(tmp_path / "e.jsonl")
    export_memory(src.store, "u", exp)
    # every exported record carries the materialised (resolved) origin
    for rec in _lines(exp)[1:]:
        assert rec["provenance"]["origin"] == src_origin
    assert _lines(exp)[0]["version"] == FORMAT_VERSION == 9   # 0014 4->5; 0019 5->6; 0016 D2 6->7; 0025 7->8; 0001 8->9
    dst = SqliteStore(str(tmp_path / "dst.db"))
    import_memory(dst, exp)
    e = [x for x in dst.edges("u", active_only=True) if x.relation == "works_as"][0]
    assert e.provenance.source_id == "mailbox:primary"
    assert e.provenance.origin == src_origin        # foreign to dst, preserved (I2b)


def test_local_source_survives_a_roundtrip_into_the_same_store(tmp_path):
    # I9: export→re-import into the SAME store groups as one and digests identically
    src = _mem_at(str(tmp_path / "src.db"), _SCRIPT)
    src.remember("u", "x", date="2026-01-01", source_id="mailbox")
    e0 = [x for x in src.store.edges("u", active_only=True) if x.relation == "works_as"][0]
    local = src.store.local_origin()
    d0 = source_identity_digest(resolve_origin(e0.provenance.origin, local), "mailbox")
    exp = str(tmp_path / "e.jsonl")
    export_memory(src.store, "u", exp)
    # specs/0005 §7b: the I9 round-trip property lives on the RESTORE path —
    # the default import caps trust, so an own-store re-import refuses there.
    import_memory(src.store, exp, restore=True)      # re-import into itself — idempotent
    works = [x for x in src.store.edges("u", active_only=True) if x.relation == "works_as"]
    assert len(works) == 1                           # one source, not split by the round-trip
    e1 = works[0]
    assert e1.provenance.origin is None              # de-materialised: a local record came home
    d1 = source_identity_digest(resolve_origin(e1.provenance.origin, local), "mailbox")
    assert d1 == d0                                  # digests identically (I9)


def test_a_v4_import_missing_origin_is_rejected(tmp_path):
    # I14: a current-format record with no origin is malformed → reject, never localise
    src = _mem_at(str(tmp_path / "src.db"), _SCRIPT)
    src.remember("u", "x", date="2026-01-01", source_id="mailbox")
    exp = str(tmp_path / "e.jsonl")
    export_memory(src.store, "u", exp)
    ls = _lines(exp)
    for rec in ls[1:]:
        rec["provenance"].pop("origin", None)        # hand-strip the materialised origin
    _write_lines(exp, ls[0], ls[1:])
    dst = SqliteStore(str(tmp_path / "dst.db"))
    with pytest.raises(ValueError, match="origin"):
        import_memory(dst, exp)


def test_a_foreign_origin_is_preserved_not_localised(tmp_path):
    # I2b: an imported foreign origin stays foreign, does NOT acquire the destination's
    src = _mem_at(str(tmp_path / "src.db"), _SCRIPT)
    src.remember("u", "x", date="2026-01-01", source_id="mailbox")
    exp = str(tmp_path / "e.jsonl")
    export_memory(src.store, "u", exp)
    ls = _lines(exp)
    for rec in ls[1:]:
        rec["provenance"]["origin"] = "FOREIGN-STORE-A"   # pretend it came from store A
    _write_lines(exp, ls[0], ls[1:])
    dst = SqliteStore(str(tmp_path / "dst.db"))
    import_memory(dst, exp)
    e = [x for x in dst.edges("u", active_only=True) if x.relation == "works_as"][0]
    assert e.provenance.origin == "FOREIGN-STORE-A"       # not dst's singleton
    assert e.provenance.origin != dst.local_origin()


def test_a_pre_v4_envelope_carrying_source_id_is_stripped(tmp_path):
    # I10: a field NEWER than the declared FORMAT_VERSION is stripped, not trusted
    src = _mem_at(str(tmp_path / "src.db"), _SCRIPT)
    src.remember("u", "x", date="2026-01-01", source_id="mailbox")
    exp = str(tmp_path / "e.jsonl")
    export_memory(src.store, "u", exp)
    ls = _lines(exp)
    ls[0]["version"] = 3                                   # relabel as an OLD envelope
    for rec in ls[1:]:
        rec["provenance"]["source_id"] = "SMUGGLED"        # hand-add the new fields
        rec["provenance"]["origin"] = "SMUGGLED-ORIGIN"
    _write_lines(exp, ls[0], ls[1:])
    dst = SqliteStore(str(tmp_path / "dst.db"))
    import_memory(dst, exp)
    e = [x for x in dst.edges("u", active_only=True) if x.relation == "works_as"][0]
    assert e.provenance.source_id is None and e.provenance.origin is None   # both stripped


def test_honest_exports_with_equal_source_ids_under_different_origins_do_not_collide():
    # I8: same source_id, different origin ⇒ different identity (no accidental collision)
    assert source_identity_digest("STORE-A", "mailbox:primary") != \
        source_identity_digest("STORE-B", "mailbox:primary")
