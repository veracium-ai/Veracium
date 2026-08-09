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

from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance, SourceType
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
             provenance=Provenance(source_type=SourceType.STATED,
                                   author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev"))
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
    prov = Provenance(source_type=SourceType.STATED, author_of_evidence=EvidenceAuthor.USER,
                      evidence_ref="ev", source_id="mailbox:primary", origin="STORE-A")
    back = Provenance.model_validate_json(prov.model_dump_json())
    assert back.source_id == "mailbox:primary" and back.origin == "STORE-A"
    # absent by default (a local record); an empty string is rejected (§4 rule 5)
    assert Provenance(source_type=SourceType.STATED,
                      author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev").source_id is None
    with pytest.raises(Exception):
        Provenance(source_type=SourceType.STATED, author_of_evidence=EvidenceAuthor.USER,
                   evidence_ref="ev", source_id="")
