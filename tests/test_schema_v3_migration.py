"""SCHEMA_VERSION 2→3 migration — the shared foundation for specs/0009 + 0010.

v3 is a purely additive migration: it adds the `consolidation_ops` table
(specs/0010 §4a) and carries specs/0009's new Episode fields in the existing
`episodes.json` blob (no episode-table ALTER). A v1 OR v2 store migrates forward
in one `migrate_store()` call; an older build opening a v3 store REFUSES (0007).
Co-implemented under one bump per 0009 §9a / 0010 §9.
"""
import sqlite3

import pytest

from veracium.schema import Episode, Provenance, EvidenceAuthor
from veracium.schema import _SourceType as SourceType  # specs/0016 D1: internal tests bind the private name
from veracium.store.migration import migrate_store
from veracium.store.schema_version import (SCHEMA_V1, SCHEMA_V2, SCHEMA_VERSION,
                                           PackageConsistencyError,
                                           StoreVersionError)
from veracium.store.sqlite import SqliteStore


def _build_at(path, schema_objs):
    """Create a store at an older schema shape (unstamped, user_version 0), the
    way a legacy store on disk looks before migration."""
    c = sqlite3.connect(path)
    for o in schema_objs:
        c.execute(o.ddl)
    c.commit()
    c.close()


def test_fresh_store_is_head_with_consolidation_ops(tmp_path):
    # A fresh store is built at HEAD (>= 3, since v3 added consolidation_ops); the
    # exact head advances as later specs add versions (0003 took it to v4), so this
    # asserts head-relative rather than pinning a number.
    p = str(tmp_path / "fresh.db")
    SqliteStore(p)
    with sqlite3.connect(p) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION >= 3
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "consolidation_ops" in tables


@pytest.mark.parametrize("base_objs,base,stamp", [(SCHEMA_V1, 1, 0), (SCHEMA_V2, 2, 2)])
def test_migrate_forward_to_v3_is_additive(tmp_path, base_objs, base, stamp):
    """A v1 (unstamped legacy) or v2 (stamped below-head) store migrates to v3 in
    one call; the migration only ADDS `consolidation_ops` (and, for a v1 base,
    `confirmations`) — it stamps user_version=3 and touches no existing row."""
    p = str(tmp_path / f"legacy_v{base}.db")
    _build_at(p, base_objs)
    if stamp:
        with sqlite3.connect(p) as c:
            c.execute(f"PRAGMA user_version = {stamp}"); c.commit()
    result = migrate_store(p)
    assert str(result) == "migrated"
    with sqlite3.connect(p) as c:
        # migrate_store brings a below-head store all the way to HEAD in one call, so
        # a v1/v2 base now crosses v3 AND v4; assert head-relative and confirm every
        # additive table along the way landed.
        assert c.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        tables = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "consolidation_ops" in tables
    assert "confirmations" in tables   # v1→head also picks up v2's table
    assert "supersession_refusals" in tables and "supersession_operations" in tables
    # A second migrate is a no-op (already current), not a re-migration.
    assert str(migrate_store(p)) == "current"
    # And it opens cleanly through the ordinary Store path now.
    SqliteStore(p)


def test_new_episode_fields_round_trip_through_json(tmp_path):
    """0009's seq/supersedes_episode/judgment_time_known and 0010's
    claimed_by/operation_id/lineage/date_start/date_end serialise into the
    episode JSON blob and read back — no schema column needed."""
    from veracium.schema import Outcome, OutcomeJudgmentDraft
    p = str(tmp_path / "rt.db")
    s = SqliteStore(p)
    # 0009 outcome fields: minted by the sanctioned writer (H14 forbids add_episode
    # for kind=="outcome"), then read back through the JSON blob.
    ep = s.append_outcome_if_head(
        "u", "e1", "run-1", None,
        OutcomeJudgmentDraft(author=EvidenceAuthor.USER, event_timestamp="2026-01-01",
                             outcome=Outcome.CONFIRMED, summary="s"))
    got = {e.id: e for e in s.episodes("u")}[ep.id]
    assert got.seq == 1 and got.judgment_time_known is True
    assert got.supersedes_episode is None and got.kind == "outcome"
    # 0010 consolidation fields ride the same JSON blob (no schema column). They are
    # store-minted by the fenced primitives (add_episode refuses them — X18), so the
    # "carried by the blob" property is a pure-model round-trip.
    cep = Episode(
        id="epc-1", user_id="u", date="2026-01-01", summary="c",
        provenance=Provenance(source_type=SourceType.INFERRED,
                              author_of_evidence=EvidenceAuthor.SYSTEM,
                              evidence_ref="op-1"),
        operation_id="op-1", lineage=["hist:ep-a", "hist:ep-b"],
        date_start="2026-01-01", date_end="2026-01-02")
    got2 = Episode.model_validate_json(cep.model_dump_json())
    assert got2.lineage == ["hist:ep-a", "hist:ep-b"]
    assert got2.operation_id == "op-1"
    assert got2.date_start == "2026-01-01" and got2.date_end == "2026-01-02"


def test_a_below_head_store_refuses_ordinary_open(tmp_path):
    """0007/0013 §5b: ordinary opening of a stamped below-head store REFUSES
    (migration is offline and explicit — `migrate_store`, not ordinary open)."""
    p = str(tmp_path / "v2only.db")
    _build_at(p, SCHEMA_V2)
    with sqlite3.connect(p) as c:
        c.execute("PRAGMA user_version = 2")
        c.commit()
    with pytest.raises((StoreVersionError, PackageConsistencyError)):
        SqliteStore(p)
