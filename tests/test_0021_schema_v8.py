"""SCHEMA v8 — the contribution-ledger typed contributor columns (the 0019
rider as amended by 0020/0021, C1–C4; 0021 §7b, the 0014 amendment clause 3).

The v7→v8 cross is the repo's SECOND ALTER of an existing table, on the 0014 v6
precedent: the fresh constructor and the ALTER path legitimately produce
DIFFERENT stored DDL for the same table, so `MANIFESTS[8]` is a SET (accepted
`0013` §4e), and the ALTER-path expectation is the RECORDED CONSTANT
`ALTER_PATH_V8_SQL` — byte-identical to the recorded evidence
(`specs/evidence/0020/schema_v8_evidence.txt`), which the migration must
byte-match, never define (`0013` §4c).
"""
import hashlib
import os
import pathlib
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from veracium.graph import apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, Edge, EvidenceAuthor,
                             Provenance)
from veracium.store import schema_version as sv
from veracium.store.migration import migrate_store
from veracium.store.schema_version import (ALTER_PATH_V8_SHA256,
                                           ALTER_PATH_V8_SQL, ALTERS_V5_TO_V6,
                                           ALTERS_V7_TO_V8, accepted_digests,
                                           digest, manifest)
from veracium.store.sqlite import SqliteStore

EVIDENCE = (pathlib.Path(__file__).resolve().parents[1]
            / "specs" / "evidence" / "0020" / "schema_v8_evidence.txt")
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _ledger_ddl(objs):
    return [o.ddl for o in objs if o.key == ("table", "contribution_ledger")][0]


def _recorded(marker, terminator):
    """Slice a manifestation text out of the RECORDED evidence file."""
    text = EVIDENCE.read_text()
    start = text.index(marker) + len(marker)
    return text[start:text.index(terminator, start)].strip("\n")


def _fresh(path, version):
    c = sqlite3.connect(path)
    for o in sv.SCHEMAS[version]:
        c.execute(o.ddl)
    c.execute(f"PRAGMA user_version = {version}")
    return c


# -- the recorded manifestations --------------------------------------------

def test_the_recorded_alter_path_literal_matches_its_pinned_sha():
    """C2: the constant IS the recorded-evidence artifact — its sha256 is
    pinned in `schema_v8_evidence.txt`; a drifted constant fails here before
    anything uses it."""
    assert (hashlib.sha256(ALTER_PATH_V8_SQL.encode()).hexdigest()
            == ALTER_PATH_V8_SHA256)


def test_the_declared_texts_byte_match_the_recorded_evidence():
    """Every shipped v8 manifestation equals the RECORDED evidence byte-for-
    byte: the constructor ([1]), the ALTER-path stored DDL ([2]), and the two
    0013-declared migration steps ([4], sha-pinned)."""
    assert _ledger_ddl(sv.SCHEMA_V8) == _recorded(
        "[1] THE LITERAL CONSTRUCTOR (v7 text + rider columns):\n\n",
        "\n\nconstructor_sha256:")
    assert ALTER_PATH_V8_SQL == _recorded(
        "[2] THE MEASURED ALTER-PATH STORED DDL (sqlite_master, "
        "byte-authoritative):\n\n",
        "\n\nalter_path_sha256:")
    text = EVIDENCE.read_text()
    for stmt in ALTERS_V7_TO_V8:
        line = f"step_sha256 {hashlib.sha256(stmt.encode()).hexdigest()}  {stmt}"
        assert line in text


def test_a_new_store_is_born_v8_with_the_recorded_constructor_ddl(tmp_path):
    """A fresh store carries the constructor manifestation natively: the stored
    sqlite_master text equals the recorded [1] text, stamped v8."""
    store = SqliteStore(str(tmp_path / "s.db"))
    stored = store._conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' "
        "AND name='contribution_ledger'").fetchone()[0]
    assert stored == _ledger_ddl(sv.SCHEMA_V8)
    # the HEAD moved to v9 at 0022's acceptance; this test pins v8's CONTENT
    # (the ledger DDL above), not the head — a new store is born at the head
    assert (store._conn.execute("PRAGMA user_version").fetchone()[0]
            == sv.SCHEMA_VERSION)
    store.close()


def test_the_alter_path_reproduces_the_recorded_literal():
    """The two frozen ALTERs over v7's constructor table produce EXACTLY the
    recorded stored DDL on the qualified runtime (0013 §4c: the migration
    matches the pre-declared expectation; the expectation never moves)."""
    c = sqlite3.connect(":memory:")
    c.execute(_ledger_ddl(sv.SCHEMA_V7))
    for stmt in ALTERS_V7_TO_V8:
        c.execute(stmt)
    stored = c.execute("SELECT sql FROM sqlite_master "
                       "WHERE name='contribution_ledger'").fetchone()[0]
    assert stored == ALTER_PATH_V8_SQL
    assert stored != _ledger_ddl(sv.SCHEMA_V8)   # genuinely dual manifestations


# -- the v7→v8 migration ----------------------------------------------------

def test_a_v7_store_migrates_onto_the_recorded_alter_path():
    """A v7-shaped store (the full SCHEMAS[7] object set, stamped 7) crosses to
    v8 via migrate_store: the two declared ALTERs run, the stored ledger DDL
    byte-matches the recorded expectation, and the result is an accepted v8
    manifest. A pre-existing (legacy) ledger row survives and reads back with
    contributor_type/contributor_ref NULL — never backfilled."""
    d = tempfile.mkdtemp()
    path = os.path.join(d, "s.db")
    c = _fresh(path, 7)
    c.execute("INSERT INTO store_identity(id, origin) VALUES(1, "
              "'00000000-0000-4000-8000-000000000000')")
    c.execute("INSERT INTO contribution_ledger(id,user_id,survivor_type,"
              "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
              "op_key,created_at) VALUES('contrib-legacy1','u1','edge','e-w',"
              "'absorption',NULL,NULL,'{\"base\":{},\"contributor\":{}}',NULL,"
              "'2026-08-01T00:00:00+00:00')")
    c.commit()
    c.close()

    migrate_store(path)

    c = sqlite3.connect(path)
    from veracium.store.schema_version import SCHEMA_VERSION
    assert c.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    stored = c.execute("SELECT sql FROM sqlite_master "
                       "WHERE name='contribution_ledger'").fetchone()[0]
    assert stored == ALTER_PATH_V8_SQL      # the v8 CONTENT pin — unchanged
    assert digest(manifest(c), SCHEMA_VERSION) in accepted_digests(SCHEMA_VERSION)
    assert c.execute(
        "SELECT contributor_type, contributor_ref FROM contribution_ledger "
        "WHERE id='contrib-legacy1'").fetchone() == (None, None)
    c.close()

    # the migrated store OPENS, and the legacy row reads back None/None through
    # the record surface — with its accepted payload intact
    store = SqliteStore(path)
    recs = store.contributions("u1", "edge", "e-w")
    assert len(recs) == 1
    r = recs[0]
    assert r.contributor_type is None and r.contributor_ref is None
    assert set(r.payload) == {"base", "contributor"}
    store.close()


def test_manifests_v8_accepts_every_reachable_shape():
    """The full reachable matrix of the two ALTERed tables' forms — not only
    the named cell (0013 §4e; both divergences persist at v8):
      ctor×ctor (fresh, or a ≤v3 base), ALTERv6×ctor (a v4/v5 base),
      ctor×ALTERv8 (a born-≥v6 base), ALTERv6×ALTERv8 (a ≤v5→v6/v7→v8
      history). Each digest is in the accepted set, and all four differ."""
    digests = []

    def _shape(build):
        c = sqlite3.connect(":memory:")
        build(c)
        d = digest(manifest(c), 8)
        c.close()
        return d

    def _ctor(c):
        for o in sv.SCHEMA_V8:
            c.execute(o.ddl)

    def _from_v5(c):                       # migrate_store's v4/v5-base path
        v5_keys = {o.key for o in sv.SCHEMA_V5}
        for o in sv.SCHEMA_V5:
            c.execute(o.ddl)
        for o in sv.SCHEMA_V8:
            if o.key not in v5_keys:
                c.execute(o.ddl)           # ledger arrives in v8 ctor form
        for stmt in ALTERS_V5_TO_V6:
            c.execute(stmt)

    def _from_v7(c):                       # a store BORN ≥v6, migrated on
        for o in sv.SCHEMA_V7:
            c.execute(o.ddl)
        for stmt in ALTERS_V7_TO_V8:
            c.execute(stmt)

    def _double(c):                        # ≤v5 → v6/v7 (old build) → v8 (now)
        v5_keys = {o.key for o in sv.SCHEMA_V5}
        for o in sv.SCHEMA_V5:
            c.execute(o.ddl)
        for o in sv.SCHEMA_V6:
            if o.key not in v5_keys:
                c.execute(o.ddl)           # ledger arrives in v6 ctor form
        for stmt in ALTERS_V5_TO_V6:
            c.execute(stmt)
        for stmt in ALTERS_V7_TO_V8:
            c.execute(stmt)

    for build in (_ctor, _from_v5, _from_v7, _double):
        d = _shape(build)
        assert d in accepted_digests(8), build.__name__
        digests.append(d)
    assert len(set(digests)) == 4          # genuinely four accepted shapes


# -- the typed contributor link on native absorption rows --------------------

def _edge(uid, obj, *, conf=0.9, observed=NOW, source_id=None, eid=None):
    return Edge(
        id=eid or f"e-{obj.replace(' ', '-')}", user_id=uid, subject="user",
        relation="pet", object=obj, valid_from=observed,
        provenance=Provenance(
            author_of_evidence=EvidenceAuthor.USER,
            evidence_ref="ev-1", observed_at=observed, confidence=conf,
            source_id=source_id))


def test_native_absorption_rows_carry_the_typed_contributor_link(tmp_path):
    """0021 §7b (the 0014 amendment, clause 3): every NEW native absorption row
    persists contributor_type='edge' and contributor_ref=<the absorbed prior's
    id> from the fields the shipped ContributionDraft already carries — while
    the accepted {base, contributor} payload and the op-key idiom stay
    UNTOUCHED (the native site is NOT amended)."""
    store = SqliteStore(str(tmp_path / "s.db"))
    prior = _edge("u1", "Miso", conf=0.8, observed=NOW - timedelta(days=3),
                  source_id="src-A", eid="e-prior")
    apply_supersession(store, prior, DEFAULT_RELATIONS)
    winner = _edge("u1", "cat Miso", conf=0.9, source_id="src-A", eid="e-winner")
    apply_supersession(store, winner, DEFAULT_RELATIONS)

    recs = store.contributions("u1", "edge", "e-winner")
    assert len(recs) == 1
    r = recs[0]
    assert r.contributor_type == "edge"
    assert r.contributor_ref == "e-prior"
    assert set(r.payload) == {"base", "contributor"}   # the accepted schema
    assert r.op_key is None                # absorption rides 0003's receipt
    # the stored row agrees with the record surface (no reader-side default)
    raw = store._conn.execute(
        "SELECT contributor_type, contributor_ref FROM contribution_ledger "
        "WHERE survivor_id='e-winner'").fetchone()
    assert raw == ("edge", "e-prior")
    store.close()


def test_consolidation_rows_stay_null_on_the_contributor_columns(tmp_path):
    """The typed link is scoped to the draft-carried sites (0021 §7b clause 3
    names the plan/absorption rows); a consolidation row's contributor is
    already bound by its op_key + identity digest, and its R3-3 field-for-field
    replay verification must keep matching pre-v8 rows — so the columns stay
    NULL there, by construction. Driven through the REAL 0010 machinery to the
    OUTPUTS_DURABLE cutover."""
    from veracium.schema import (ConsolidationOutputDraft, ConsolidationState,
                                 Episode)
    store = SqliteStore(str(tmp_path / "s.db"))
    for i in range(2):
        store.add_episode(Episode(
            id=f"ep-{i}", user_id="u1", date=f"2026-07-0{i+1}",
            summary=f"day {i}", provenance=Provenance(
                author_of_evidence=EvidenceAuthor.USER,
                evidence_ref=f"ev-{i}", observed_at=NOW,
                confidence=0.9, source_id=f"src-{i}")))
    op = store.create_or_takeover_consolidation("u1", ["ep-0", "ep-1"],
                                                "w1", 60)
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.GENERATING)
    assert store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w1",
        ConsolidationOutputDraft(summary="the week", date_start="2026-07-01",
                                 date_end="2026-07-02"))
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w1", ConsolidationState.OUTPUTS_DURABLE)
    outs = [ep for _, ep in store._episodes_for_operation("u1", op.operation_id)
            if ep.lineage]
    assert len(outs) == 1
    recs = store.contributions("u1", "episode", outs[0].id)
    assert len(recs) == 2
    for r in recs:
        assert r.contributor_type is None and r.contributor_ref is None
        assert set(r.payload) == {"input", "output_index"}   # untouched
    store.close()
