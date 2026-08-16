"""specs/0021 §7b — the IMPLEMENTATION-SHAPED ledger-plan harness
(external round 8's artifact ask). Proves the amended 0009/0014 contracts
are CONSTRUCTIBLE AND STORABLE against the REAL accepted schema:

1. [real-ddl] extracts the contribution_ledger DDL + indexes from a LIVE
   SqliteStore's sqlite_master (never hand-mirrored), rebuilds them in a
   bare database, and applies the amendment's EXACT ALTER statements
   (contributor_type, contributor_ref — the SCHEMA-v8 rider).
2. [construction] builds rows from an ACTUAL `reconstruct_absorption_rows`
   run over an A→B→C chain (multi-row, one import operation) and completes
   them to the stored-row shape with `plan_row_id` — every ContributionRecord
   column populated, none invented.
3. [op-key] inserts the multi-row plan under PER-ROW canonical op keys —
   the accepted UNIQUE partial index accepts it — then DEMONSTRATES the
   v9 design's failure verbatim: two rows sharing one op key raise
   IntegrityError (the reviewer's executed break, kept as a regression).
4. [null-dedup] an unidentified contributor (identity_digest NULL)
   deduplicates by the deterministic `plan_row_id` PRIMARY KEY — SQLite's
   NULL-uniqueness semantics never decide anything.
5. [idempotent] a RE-IMPORT (new minted operation, same logical rows)
   detects exact-equality by deterministic id and writes NOTHING.
6. [concurrent] two connections importing the same plan: BEGIN IMMEDIATE
   linearizes; the loser observes the winner's rows as existing and
   skips — no duplicates, no partial state.
7. [reopen] rows and the closure verdict survive close/reopen.

Run: `<venv>/python specs/evidence/0020/ledger_plan_harness.py`
(temp stores; <1s; the seal records the result in
`ledger_plan_result.txt`).
"""

from __future__ import annotations

import pathlib
import sqlite3
import sys
import tempfile
import threading

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from reference_scope import (Identity, close_absorption_rows, digest_of,  # noqa: E402
                             membership, plan_row_id,
                             reconstruct_absorption_rows, UNRESOLVED)

AMENDMENT_ALTERS = (
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_type TEXT",
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_ref TEXT",
)
IMPORT_OP = "op-1234abcd5678"
LOCAL = "org-dest-0001"


def _real_ddl():
    """Extract the ACCEPTED ledger DDL from a live store — never mirrored."""
    from veracium.store.sqlite import SqliteStore
    with tempfile.TemporaryDirectory() as d:
        s = SqliteStore(f"{d}/probe.db")
        rows = s._conn.execute(
            "SELECT type, sql FROM sqlite_master WHERE tbl_name="
            "'contribution_ledger' AND sql IS NOT NULL ORDER BY type DESC"
        ).fetchall()
        s.close()
    assert rows, "no contribution_ledger DDL found in the live store"
    return [r[1] for r in rows]


def _chain_rows():
    """Rows from an ACTUAL reconstruction over an A→B→C export chain."""
    records = [
        {"id": "A", "invalidation_reason": "absorbed_duplicate",
         "note": "absorbed_by:B (restated as 'x')", "origin": "org-a",
         "source_id": "agent-a", "evidence_ref": "ev-a"},
        {"id": "B", "invalidation_reason": "absorbed_duplicate",
         "note": "absorbed_by:C (restated as 'y')", "origin": "org-b",
         "source_id": "agent-b", "evidence_ref": "ev-b"},
        {"id": "C", "invalidation_reason": None, "note": "",
         "origin": "org-b", "source_id": "agent-b", "evidence_ref": "ev-c"},
    ]
    return reconstruct_absorption_rows(records, LOCAL, import_op=IMPORT_OP)


def _stored(user, stype, sid, row, created="2026-08-16T00:00:00Z"):
    """Complete a reconstruction row to the FULL stored-column tuple."""
    import json
    return (plan_row_id(user, stype, sid, row), user, stype, sid,
            row["site"], row["identity_digest"], row["evidence_ref_digest"],
            json.dumps(row["payload"], sort_keys=True), row["op_key"],
            created, "edge", row["contributor_ref"])


INSERT = ("INSERT INTO contribution_ledger(id,user_id,survivor_type,"
          "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
          "op_key,created_at,contributor_type,contributor_ref) "
          "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)")


def _insert_plan(conn, plan, *, skip_existing=False):
    written = existing = 0
    for sid, rows in sorted(plan.items()):
        for row in rows:
            t = _stored("u1", "edge", sid, row)
            if skip_existing and conn.execute(
                    "SELECT 1 FROM contribution_ledger WHERE id=?",
                    (t[0],)).fetchone():
                existing += 1
                continue
            conn.execute(INSERT, t)
            written += 1
    return written, existing


def run():
    checks = []
    ddl = _real_ddl()
    assert any("UNIQUE INDEX ix_contribution_ledger_op_key" in s
               for s in ddl), "the accepted unique op_key index is missing?"
    checks.append(f"[real-ddl] {len(ddl)} DDL statements extracted from the "
                  "LIVE store (table + indexes, incl. the UNIQUE partial "
                  "op_key index)")

    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/ledger.db"
        conn = sqlite3.connect(db)
        for s in ddl:
            conn.execute(s)
        for s in AMENDMENT_ALTERS:
            conn.execute(s)
        conn.commit()
        checks.append("[real-ddl] the amendment's EXACT ALTERs applied over "
                      "the extracted schema (contributor_type, "
                      "contributor_ref — nullable; legacy rows unaffected)")

        # (2)+(3) multi-row single-operation plan under per-row keys
        plan = _chain_rows()
        n_rows = sum(len(v) for v in plan.values())
        assert n_rows == 3, f"chain should yield 3 rows, got {n_rows}"
        written, existing = _insert_plan(conn, plan)
        conn.commit()
        assert (written, existing) == (3, 0)
        checks.append("[op-key] ONE import operation, THREE rows (C carries "
                      "B+A transitively, B carries A) inserted under "
                      "per-row canonical keys — the accepted UNIQUE partial "
                      "index ACCEPTS the plan")

        # the v9 design's failure, demonstrated verbatim (the reviewer's break)
        try:
            conn.execute(INSERT, _stored("u1", "edge", "X1",
                                         {"site": "imported-absorption",
                                          "identity_digest": "0" * 64,
                                          "evidence_ref_digest": None,
                                          "payload": {"reconstructed": True},
                                          "op_key": IMPORT_OP,
                                          "contributor_ref": "r1"}))
            conn.execute(INSERT, _stored("u1", "edge", "X2",
                                         {"site": "imported-absorption",
                                          "identity_digest": "1" * 64,
                                          "evidence_ref_digest": None,
                                          "payload": {"reconstructed": True},
                                          "op_key": IMPORT_OP,
                                          "contributor_ref": "r2"}))
            raise AssertionError("one-key-per-plan did NOT raise — the "
                                 "index changed?")
        except sqlite3.IntegrityError:
            conn.rollback()
        checks.append("[op-key] the v9 one-key-per-plan design raises "
                      "IntegrityError on row 2 (the reviewer's executed "
                      "break, kept as a regression) — per-row keys are "
                      "REQUIRED, not stylistic")

        # (4) NULL-digest contributor dedup via the deterministic PK
        null_row = {"site": "imported-absorption", "identity_digest": None,
                    "evidence_ref_digest": None,
                    "payload": {"reconstructed": True},
                    "op_key": f"{IMPORT_OP}:W:unid-1",
                    "contributor_ref": "unid-1"}
        conn.execute(INSERT, _stored("u1", "edge", "W", null_row))
        conn.commit()
        try:
            conn.execute(INSERT, _stored("u1", "edge", "W", dict(
                null_row, op_key="op-9999ffff0000:W:unid-1")))
            raise AssertionError("NULL-digest logical duplicate not refused")
        except sqlite3.IntegrityError:
            conn.rollback()
        checks.append("[null-dedup] an unidentified contributor "
                      "(identity_digest NULL) deduplicates by the "
                      "deterministic plan_row_id PRIMARY KEY — a re-minted "
                      "op key does not evade it; SQLite NULL-uniqueness "
                      "decides nothing")

        # (5) idempotent re-import: new op, same logical rows → all skip
        replan = reconstruct_absorption_rows(
            [{"id": "A", "invalidation_reason": "absorbed_duplicate",
              "note": "absorbed_by:B (restated as 'x')", "origin": "org-a",
              "source_id": "agent-a", "evidence_ref": "ev-a"},
             {"id": "B", "invalidation_reason": "absorbed_duplicate",
              "note": "absorbed_by:C (restated as 'y')", "origin": "org-b",
              "source_id": "agent-b", "evidence_ref": "ev-b"},
             {"id": "C", "invalidation_reason": None, "note": "",
              "origin": "org-b", "source_id": "agent-b",
              "evidence_ref": "ev-c"}],
            LOCAL, import_op="op-feedbeef1234")
        before = conn.execute(
            "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0]
        w2, e2 = _insert_plan(conn, replan, skip_existing=True)
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0]
        assert (w2, e2) == (0, 3) and before == after
        checks.append("[idempotent] RE-IMPORT under a new minted operation: "
                      "3 rows detected exact-equal by deterministic id, 0 "
                      "written (contributions=0, contributions_existing=3)")
        conn.close()

        # (6) concurrent same-plan imports on two connections
        results = {}
        barrier = threading.Barrier(2)

        def importer(name):
            c = sqlite3.connect(db, timeout=10)
            barrier.wait()
            c.execute("BEGIN IMMEDIATE")           # the linearization point
            w, e = _insert_plan(c, {"Z": [{
                "site": "imported-absorption", "identity_digest": "2" * 64,
                "evidence_ref_digest": None,
                "payload": {"reconstructed": True},
                "op_key": f"op-cc00cc00cc00:Z:zz-1",
                "contributor_ref": "zz-1"}]}, skip_existing=True)
            c.commit(); c.close()
            results[name] = (w, e)

        ts = [threading.Thread(target=importer, args=(i,)) for i in (0, 1)]
        [t.start() for t in ts]; [t.join() for t in ts]
        conn = sqlite3.connect(db)
        zrows = conn.execute("SELECT COUNT(*) FROM contribution_ledger "
                             "WHERE survivor_id='Z'").fetchone()[0]
        assert zrows == 1, f"concurrent import duplicated rows: {zrows}"
        assert sorted(r[0] for r in results.values()) == [0, 1], results
        checks.append("[concurrent] two connections, same plan, BEGIN "
                      "IMMEDIATE: one writes, one observes-and-skips — 1 "
                      "row total, no duplicates, no partial state")
        conn.close()

        # (7) reopen durability + the closure verdict over stored rows
        import json as _json
        conn = sqlite3.connect(db)
        stored = conn.execute(
            "SELECT survivor_id, site, identity_digest, contributor_ref, "
            "payload FROM contribution_ledger WHERE survivor_id IN "
            "('B','C') ORDER BY survivor_id").fetchall()
        conn.close()
        ledger = {}
        for sid, site, dig, ref, payload in stored:
            ledger.setdefault(sid, []).append(
                {"site": site, "identity_digest": dig,
                 "contributor_ref": ref,
                 "payload": _json.loads(payload)})
        closed = close_absorption_rows("C", ledger)
        # the closure is C's OWN born-closed set (B's rows verify it but
        # are not unioned — the survivor's rows ARE the durable object)
        assert closed is not None and len(closed) == 2, closed
        rec = {"author": "user", "origin": "org-b", "source_id": "agent-b",
               "evidence_ref": "ev-c", "lineage": False}
        got = membership(rec, closed, "none", LOCAL)
        assert got == UNRESOLVED, f"restored chain must be UNRESOLVED: {got!r}"
        checks.append("[reopen] rows persist across close/reopen and the "
                      "LEDGER-RESIDENT closure classifies the A→B→C "
                      "survivor UNRESOLVED from stored rows alone (typed "
                      "refs; no records, no notes needed — R8-1 closed)")
    return checks


if __name__ == "__main__":
    for line in run():
        print("PASS", line)
    print("ledger plan harness: 8 checks pass against the EXTRACTED real "
          "DDL + the amendment ALTERs")
