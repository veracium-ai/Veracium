"""specs/0014 Slice A — schema v6: the ledger DDL, the three receipt ALTERs, and
the `MANIFESTS[6]` set with the independently authored ALTER-path manifest.

The v5→v6 cross is the repo's FIRST ALTER of an existing table. Accepted `0013`
§4e makes the version accept a SET of manifests (constructor + ALTER path);
§4c forbids the migration from defining its own destination — the ALTER-path
expectation is the REVIEWED CONSTANT `ALTER_PATH_V6_SQL` (0014 §4b, authored on
the qualified 3.45.1 and authorized by the 0014 acceptance review), and the
migration must byte-match it.
"""
import hashlib
import os
import sqlite3
import tempfile

from veracium.store import schema_version as sv
from veracium.store.migration import migrate_store
from veracium.store.schema_version import (ALTER_PATH_V6_SHA256,
                                           ALTER_PATH_V6_SQL, ALTERS_V5_TO_V6,
                                           accepted_digests, digest, manifest)


def _fresh(path, version):
    c = sqlite3.connect(path)
    for o in sv.SCHEMAS[version]:
        c.execute(o.ddl)
    c.execute(f"PRAGMA user_version = {version}")
    return c


def test_the_reviewed_alter_path_literal_matches_its_pinned_sha():
    """0014 §4b: the constant IS the authorization artifact — its sha256 is
    pinned in the spec; a drifted constant fails here before anything uses it."""
    assert (hashlib.sha256(ALTER_PATH_V6_SQL.encode()).hexdigest()
            == ALTER_PATH_V6_SHA256)


def test_the_alter_path_reproduces_the_reviewed_literal():
    """The three frozen ALTERs over v5's constructor table produce EXACTLY the
    reviewed stored DDL on the qualified runtime — the migration matches the
    pre-declared expectation; the expectation never moves (0013 §4c)."""
    c = sqlite3.connect(":memory:")
    for o in sv.SCHEMA_V5:
        c.execute(o.ddl)
    for stmt in ALTERS_V5_TO_V6:
        c.execute(stmt)
    stored = c.execute("SELECT sql FROM sqlite_master "
                       "WHERE name='supersession_operations'").fetchone()[0]
    assert stored == ALTER_PATH_V6_SQL


def test_manifests_v6_is_a_set_with_the_reviewed_path():
    """0013 §4e: v6 accepts TWO manifests — the fresh constructor and the
    reviewed ALTER path — and they are genuinely different digests (the exact
    reason MANIFESTS is a set)."""
    accepted = accepted_digests(6)
    assert len(accepted) >= 2
    ctor = sqlite3.connect(":memory:")
    for o in sv.SCHEMA_V6:
        ctor.execute(o.ddl)
    ctor_digest = digest(manifest(ctor), 6)
    alt = sqlite3.connect(":memory:")
    for o in sv.SCHEMA_V5:
        alt.execute(o.ddl)
    # the real v5->v6 path: the additive diff (ledger + indexes) PLUS the ALTERs
    v5_keys = {o.key for o in sv.SCHEMA_V5}
    for o in sv.SCHEMA_V6:
        if o.key not in v5_keys:
            alt.execute(o.ddl)
    for stmt in ALTERS_V5_TO_V6:
        alt.execute(stmt)
    alt_digest = digest(manifest(alt), 6)
    assert ctor_digest in accepted
    assert alt_digest in accepted
    assert ctor_digest != alt_digest


def test_v5_to_v6_migrates_a_nonempty_receipt_table():
    """0014 R10-3, the named migration test: a v5 store WITH existing receipt
    rows migrates; every pre-existing row reads (request_digest NULL, response
    NULL, outcome_digest_version 1 — the DEFAULT IS the stamp); a post-migration
    write can stamp 2; the final stored DDL byte-matches the PRE-DECLARED
    reviewed expectation; and the result's digest is in the accepted set."""
    d = tempfile.mkdtemp()
    path = os.path.join(d, "s.db")
    c = _fresh(path, 5)
    c.execute("INSERT INTO supersession_operations VALUES "
              "('u1','op1','digestA','committed')")
    c.execute("INSERT INTO supersession_operations VALUES "
              "('u1','op2','digestB','committed')")
    c.commit()
    c.close()

    migrate_store(path)

    c = sqlite3.connect(path)
    assert c.execute("PRAGMA user_version").fetchone()[0] == sv.SCHEMA_VERSION == 8  # 0021 rider: v8 head
    rows = c.execute(
        "SELECT operation_id, request_digest, response, outcome_digest_version "
        "FROM supersession_operations ORDER BY operation_id").fetchall()
    assert rows == [("op1", None, None, 1), ("op2", None, None, 1)]
    stored = c.execute("SELECT sql FROM sqlite_master "
                       "WHERE name='supersession_operations'").fetchone()[0]
    assert stored == ALTER_PATH_V6_SQL
    assert c.execute("SELECT name FROM sqlite_master "
                     "WHERE name='contribution_ledger'").fetchone()
    # v8 head: the v5 base lands (receipts ALTER-path × ledger constructor) —
    # an accepted v8 manifest; the v6 accepted-set membership moved with the head
    assert digest(manifest(c), 8) in accepted_digests(8)
    # a post-upgrade write stamps 2 EXPLICITLY (never relying on the default)
    c.execute("INSERT INTO supersession_operations "
              "(user_id, operation_id, logical_request_digest, status, "
              " request_digest, response, outcome_digest_version) "
              "VALUES ('u1','op3','digestC','committed', 'rd', '{}', 2)")
    assert c.execute("SELECT outcome_digest_version FROM supersession_operations "
                     "WHERE operation_id='op3'").fetchone()[0] == 2


def test_deep_migration_v1_to_v6_lands_accepted():
    """The whole chain: a v1 store crosses every data step (outcome re-rooting,
    wiki drop, identity minting) AND the v6 ALTERs in one migrate_store call,
    landing on an accepted manifest."""
    d = tempfile.mkdtemp()
    path = os.path.join(d, "s.db")
    c = _fresh(path, 1)
    c.commit()
    c.close()
    migrate_store(path)
    c = sqlite3.connect(path)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 8  # 0021 rider: head is v8
    # base 1 lacks BOTH altered tables, so the additive diff creates each in its
    # v8 CONSTRUCTOR form — the constructor manifest
    assert digest(manifest(c), 8) in accepted_digests(8)
    cols = [r[1] for r in c.execute("PRAGMA table_info(supersession_operations)")]
    assert cols[-3:] == ["request_digest", "response", "outcome_digest_version"]
