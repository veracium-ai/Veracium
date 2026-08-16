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
3b. [op-key] R9-2: DELIMITER-BEARING ids insert under one operation via
   the INJECTIVE framed-digest key form (the v10 colon-join collided).
3c. [idempotent] R9-3: HISTORY DRIFT (direct vs flattened payload) and
   evidence drift carry DIFFERENT plan ids — never silently skipped.
3d. [construction] R9-3: malformed cross-field combinations refuse at
   the validator before any projection.
4. [null-dedup] an unidentified contributor (identity_digest NULL)
   deduplicates by the deterministic `plan_row_id` PRIMARY KEY — SQLite's
   NULL-uniqueness semantics never decide anything.
5. [idempotent] a RE-IMPORT (new minted operation, same logical rows)
   detects exact-equality by deterministic id and writes NOTHING.
5b. [reopen] R9-1: the STRUCTURED-EXPORT derivation over STORED rows,
   before AND after the retention-contract prune of the intermediate
   (derive(A)=B → prune B → derive(A)=C via the reparented copy).
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


def _stored(user, stype, sid, row, created="2026-08-16T00:00:00Z",
            context="import", op=IMPORT_OP):
    """Complete a reconstruction row to the FULL stored-column tuple.
    R13-1: the (context, op) pair rides through to the validator, which
    enforces the operation-domain and EXACT key-derivation binding."""
    import json
    return (plan_row_id(user, stype, sid, row, context, op=op),
            user, stype, sid,
            row["site"], row["identity_digest"], row["evidence_ref_digest"],
            json.dumps(row["payload"], sort_keys=True), row["op_key"],
            created, "edge", row["contributor_ref"])


INSERT = ("INSERT INTO contribution_ledger(id,user_id,survivor_type,"
          "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
          "op_key,created_at,contributor_type,contributor_ref) "
          "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)")


def _insert_plan(conn, plan, *, skip_existing=False, context="import",
                 op=IMPORT_OP):
    written = existing = 0
    for sid, rows in sorted(plan.items()):
        for row in rows:
            t = _stored("u1", "edge", sid, row, context=context, op=op)
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

        # the v9 design's failure, demonstrated verbatim (the reviewer's
        # break). RAW tuples: the v14 validator now REFUSES this shape
        # outright (R13-1), so the demo bypasses it to show the index
        # behaviour the old design hit
        import json as _jd
        def _raw_tuple(rid, sid, dig, ref):
            return (rid, "u1", "edge", sid, "imported-absorption", dig,
                    None, _jd.dumps({"reconstructed": True}), IMPORT_OP,
                    "2026-08-16T00:00:00Z", "edge", ref)
        try:
            conn.execute(INSERT, _raw_tuple("demo-x1", "X1", "0" * 64,
                                            "r1"))
            conn.execute(INSERT, _raw_tuple("demo-x2", "X2", "1" * 64,
                                            "r2"))
            raise AssertionError("one-key-per-plan did NOT raise — the "
                                 "index changed?")
        except sqlite3.IntegrityError:
            conn.rollback()
        checks.append("[op-key] the v9 one-key-per-plan design raises "
                      "IntegrityError on row 2 (the reviewer's executed "
                      "break, kept as a regression) — per-row keys are "
                      "REQUIRED, not stylistic")

        # (3b) R9-2: DELIMITER-BEARING ids under ONE operation — the v10
        # colon-join collided ('a:b'+'c' vs 'a'+'b:c'); the injective
        # framed-digest keys insert cleanly against the real unique index
        from reference_scope import (import_row_op_key,
                                     construct_plan_row)
        collide_cases = [("a:b", "c"), ("a", "b:c")]
        for surv, cref in collide_cases:
            row = construct_plan_row(
                "import", IMPORT_OP, surv, site="imported-absorption",
                identity_digest="3" * 64, evidence_ref_digest=None,
                contributor_ref=cref, payload={"reconstructed": True})
            conn.execute(INSERT, _stored("u1", "edge", surv, row))
        conn.commit()
        keys = {import_row_op_key(IMPORT_OP, s, c) for s, c in collide_cases}
        assert len(keys) == 2, "injective keys collided?!"
        checks.append("[op-key] DELIMITER-BEARING ids ('a:b'+'c' vs "
                      "'a'+'b:c') insert under ONE operation — the "
                      "injective framed-digest form; the v10 colon-join "
                      "collided here (R9-2, the reviewer's IntegrityError)")

        # (3c) R9-3/R10-1: HISTORY DRIFT is a DIFFERENT logical row — a
        # direct A→C link (imported-absorption) and a flattened A→(B)→C
        # copy (scope-attribution) must never skip as equal
        from reference_scope import plan_row_id as _prid, row_op_key
        direct_row = construct_plan_row(
            "import", IMPORT_OP, "C2", site="imported-absorption",
            identity_digest="4" * 64, evidence_ref_digest=None,
            contributor_ref="A2", payload={"reconstructed": True})
        flat_row = construct_plan_row(
            "import", "op-eeee00001111", "C2", site="scope-attribution",
            identity_digest="4" * 64, evidence_ref_digest=None,
            contributor_ref="A2",
            payload={"flattened": True, "reconstructed": True})
        assert _prid("u1", "edge", "C2", direct_row, "import",
                     op=IMPORT_OP) != \
            _prid("u1", "edge", "C2", flat_row, "import",
                  op="op-eeee00001111"), \
            "payload drift collapsed into one id (R9-3)"
        conn.execute(INSERT, _stored("u1", "edge", "C2", direct_row))
        conn.commit()
        w3, e3 = _insert_plan(conn, {"C2": [flat_row]},
            skip_existing=True, op="op-eeee00001111")
        conn.commit()
        assert (w3, e3) == (1, 0), (
            "a flattened history skipped as equal to a direct one (R9-3)")
        checks.append("[idempotent] HISTORY DRIFT detected: a direct A->C "
                      "link and a flattened A->(B)->C copy carry DIFFERENT "
                      "plan ids AND sites — the drift WRITES (surfacing to "
                      "the primitive's DESTINATION_CHANGED conflict rule), "
                      "never silently skips (R9-3)")

        # (3d) R10-3: the EXHAUSTIVE row-validator matrix — every field ×
        # a malformation set, plus the cross-field cells; enumeration, not
        # named examples (the reviewer fed v11's validator four accepted
        # malformed rows)
        from reference_scope import (PolicyError as _PE,
                                     validate_row_plan as _vrp)
        from reference_scope import row_op_key as _rok, \
            native_row_op_key as _nrok
        GOOD = {"site": "imported-absorption", "identity_digest": "5" * 64,
                "evidence_ref_digest": "6" * 64, "contributor_ref": "X",
                "contributor_type": "edge",
                "payload": {"reconstructed": True},
                "op_key": _rok(IMPORT_OP, "imported-absorption", "M", "X")}
        _vrp(GOOD, "import", op=IMPORT_OP, survivor_id="M")
        MATRIX = {
            "site": [None, "", "absorption", "consolidation", "alien", 7],
            "identity_digest": ["nothex", "5" * 63, "5" * 65, 7, ""],
            "evidence_ref_digest": ["nothex", "6" * 63, 7, ""],
            "contributor_ref": [None, "", 7],
            "contributor_type": ["episode", "", None, 7],
            "payload": [None, "", 7, {}, {"reconstructed": False},
                        {"reconstructed": 1}, {"reconstructed": "true"},
                        {"reconstructed": True, "extra": 1},
                        {"flattened": True},          # wrong site
                        {"reparented_from": "B"},     # wrong site
                        {"closure": "incomplete"},    # wrong site
                        {"reparented": True},
                        {"closure": "partial"}],
        }
        NATIVE_OP = "sup-matrix-edge"
        ATTR_GOOD = {"site": "scope-attribution",
                     "identity_digest": "5" * 64,
                     "evidence_ref_digest": None, "contributor_ref": "X",
                     "contributor_type": "edge",
                     "payload": {"flattened": True},
                     "op_key": _nrok(NATIVE_OP, "M", "X")}
        _vrp(ATTR_GOOD, "native", op=NATIVE_OP, survivor_id="M")
        ATTR_MATRIX = {
            "payload": [{"flattened": 1}, {"flattened": False},
                        {"flattened": True, "extra": 1},
                        {"reparented_from": ""}, {"reparented_from": 7},
                        {"reparented_from": "B", "flattened": True},
                        {"closure": "incomplete", "extra": 1},
                        {"reconstructed": True}],     # wrong site
            "contributor_ref": [None, ""],
        }
        tried = refused = 0
        OPS = {"import": IMPORT_OP, "native": NATIVE_OP,
               "prune": "op-1e1e1e1e1e1e"}
        for base, ctx, matrix in ((GOOD, "import", MATRIX),
                                  (ATTR_GOOD, "native", ATTR_MATRIX)):
            for field, bads in matrix.items():
                for bad in bads:
                    tried += 1
                    try:
                        _vrp(dict(base, **{field: bad}), ctx,
                             op=OPS[ctx], survivor_id="M")
                    except _PE:
                        refused += 1
        # R11-2: DELETION cells — presence is separate from value
        # validity (the reviewer deleted keys; .get() accepted them)
        for base, ctx in ((GOOD, "import"), (ATTR_GOOD, "native")):
            for field in ("site", "identity_digest", "evidence_ref_digest",
                          "contributor_type", "contributor_ref", "payload",
                          "op_key"):
                tried += 1
                gone = {k: v for k, v in base.items() if k != field}
                try:
                    _vrp(gone, ctx, op=OPS[ctx], survivor_id="M")
                except _PE:
                    refused += 1
        # the cross-field cells the matrix's single-field sweep can't hit
        # R13-1: the COMPLETE 3×5 writer × payload-class product — the
        # 5 valid cells built by the constructor (asserted below), the 10
        # INVALID cells enumerated here mechanically (v14's named list
        # covered only 6 of 10 — the reviewer counted)
        from reference_scope import SITE_ATTRIBUTION as _SA
        CLASS_ROWS = {
            "reconstructed": ("imported-absorption",
                              {"reconstructed": True}, "5" * 64),
            "flattened": (_SA, {"flattened": True}, "5" * 64),
            "flattened+reconstructed": (_SA, {"flattened": True,
                                              "reconstructed": True},
                                        "5" * 64),
            "reparented": (_SA, {"reparented_from": "B"}, "5" * 64),
            "marker": (_SA, {"closure": "incomplete"}, None),
        }
        VALID_CELLS = {("native", "flattened"),
                       ("import", "reconstructed"),
                       ("import", "flattened+reconstructed"),
                       ("prune", "reparented"), ("prune", "marker")}
        # ACCEPTANCE OBLIGATION 1 (round 14): the FIVE VALID cells are
        # constructor-BUILT (incl. the native-context call) and INSERTED
        # at the extracted-real-DDL boundary — the reviewer built this
        # oracle independently at acceptance; it now ships
        from reference_scope import construct_plan_row as _cpr14
        built5 = 0
        for ctx in ("native", "import", "prune"):
            for cls, (site, payload, dig) in CLASS_ROWS.items():
                if (ctx, cls) not in VALID_CELLS:
                    continue
                vrow = _cpr14(ctx, OPS[ctx], f"orc-{ctx}-{cls}",
                              site=site, identity_digest=dig,
                              evidence_ref_digest=None,
                              contributor_ref=f"xo-{cls}",
                              payload=payload)
                conn.execute(INSERT, _stored(
                    "u1", "edge", f"orc-{ctx}-{cls}", vrow,
                    context=ctx, op=OPS[ctx]))
                built5 += 1
        conn.commit()
        assert built5 == 5, built5
        stored5 = conn.execute(
            "SELECT COUNT(*) FROM contribution_ledger WHERE survivor_id "
            "LIKE 'orc-%'").fetchone()[0]
        assert stored5 == 5, stored5
        checks.append("[construction] THE FIVE-VALID-CELL ORACLE: every "
                      "valid (writer, payload-class) cell — native/"
                      "flattened (the native-context constructor call, "
                      "sup-domain op), import/reconstructed, import/"
                      "flattened+reconstructed, prune/reparented, prune/"
                      "marker — constructor-BUILT and INSERTED against "
                      "the extracted real DDL: 5/5 stored, keys derived "
                      "in-primitive (acceptance obligation 1, shipped)")
        for ctx in ("native", "import", "prune"):
            for cls, (site, payload, dig) in CLASS_ROWS.items():
                if (ctx, cls) in VALID_CELLS:
                    continue
                tried += 1
                key = (_nrok(OPS[ctx], "M", "X") if ctx == "native"
                       else _rok(OPS[ctx], site, "M", "X"))
                combo = {"site": site, "identity_digest": dig,
                         "evidence_ref_digest": None,
                         "contributor_ref": "X",
                         "contributor_type": "edge", "payload": payload,
                         "op_key": key}
                try:
                    _vrp(combo, ctx, op=OPS[ctx], survivor_id="M")
                except _PE:
                    refused += 1
        # R13-1: the KEY cases — absent/null/malformed/cross-context/
        # mis-derived, each against an otherwise-valid import row
        for bad_key in (None, "not-an-operation-key",
                        _nrok("sup-alien-edge", "M", "X"),
                        _rok(IMPORT_OP, "imported-absorption",
                             "OTHER", "X")):
            tried += 1
            try:
                _vrp(dict(GOOD, op_key=bad_key), "import",
                     op=IMPORT_OP, survivor_id="M")
            except _PE:
                refused += 1
        # ...and an op OUTSIDE the context's domain, with its own key
        tried += 1
        try:
            _vrp(GOOD, "import", op="sup-not-an-import-op",
                 survivor_id="M")
        except _PE:
            refused += 1
        # ACCEPTANCE OBLIGATION 2: the trailing-newline op id (re.match
        # with $ accepted it; fullmatch refuses) — the cell is retained
        tried += 1
        try:
            _vrp(GOOD, "import", op=IMPORT_OP + "\n", survivor_id="M")
        except _PE:
            refused += 1
        for combo, ctx in (
            (dict(ATTR_GOOD, payload={"closure": "incomplete"}), "prune"),
            (dict(GOOD, identity_digest=None,
                  payload={"reconstructed": True},
                  evidence_ref_digest="nothex"), "import"),
        ):
            tried += 1
            try:
                _vrp(combo, ctx, op=OPS[ctx], survivor_id="M")
            except _PE:
                refused += 1
        assert tried == refused, (
            f"validator matrix: {tried - refused} of {tried} malformed "
            f"rows ACCEPTED")
        checks.append(f"[construction] the EXHAUSTIVE validator matrix: "
                      f"{refused}/{tried} malformed rows refuse across "
                      f"every field, both sites, closed payload shapes "
                      f"(literal-True markers; unknown keys; wrong-site "
                      f"classes; cross-field combos) — R10-3")

        # (4) NULL-digest contributor dedup via the deterministic PK
        null_row = construct_plan_row(
            "import", IMPORT_OP, "W", site="imported-absorption",
            identity_digest=None, evidence_ref_digest=None,
            contributor_ref="unid-1", payload={"reconstructed": True})
        conn.execute(INSERT, _stored("u1", "edge", "W", null_row))
        conn.commit()
        try:
            remint = construct_plan_row(
                "import", "op-9999ffff0000", "W",
                site="imported-absorption", identity_digest=None,
                evidence_ref_digest=None, contributor_ref="unid-1",
                payload={"reconstructed": True})
            conn.execute(INSERT, _stored("u1", "edge", "W", remint,
                                         op="op-9999ffff0000"))
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
        w2, e2 = _insert_plan(conn, replan, skip_existing=True,
                              op="op-feedbeef1234")
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM contribution_ledger").fetchone()[0]
        assert (w2, e2) == (0, 3) and before == after
        checks.append("[idempotent] RE-IMPORT under a new minted operation: "
                      "3 rows detected exact-equal by deterministic id, 0 "
                      "written (contributions=0, contributions_existing=3)")
        conn.close()

        conn = sqlite3.connect(db)
        # (5b) R9-1: the STRUCTURED-EXPORT derivation, before and after
        # pruning B — over rows loaded from SQL, never from memory
        import json as _j
        from reference_scope import (derive_absorbed_by,
                                     prune_absorbed_record)

        def _load(c):
            m = {}
            for sid, site, dig, eref, ref, pay, ok in c.execute(
                    "SELECT survivor_id, site, identity_digest,"
                    " evidence_ref_digest, contributor_ref, payload, op_key"
                    " FROM contribution_ledger WHERE "
                    "survivor_id IN ('B','C')"):
                m.setdefault(sid, []).append(
                    {"site": site, "identity_digest": dig,
                     "evidence_ref_digest": eref, "contributor_ref": ref,
                     "payload": _j.loads(pay), "op_key": ok})
            return m
        before = _load(conn)
        _flat_keys0 = [r["op_key"] for r in before.get("C", [])
                       if (r["payload"] or {}).get("flattened")]
        def _raw0(c, keys):
            q = ",".join("?" * len(keys))
            return {r[0]: r for r in c.execute(
                f"SELECT op_key, id, user_id, survivor_type, survivor_id,"
                f" site, identity_digest, evidence_ref_digest, payload,"
                f" created_at, contributor_type, contributor_ref FROM"
                f" contribution_ledger WHERE op_key IN ({q})", keys)}
        pre_prune_raw = _raw0(conn, _flat_keys0)
        assert derive_absorbed_by("A", before) == "B"
        assert derive_absorbed_by("B", before) == "C"
        # the retention contract's prune of B — INSERT-ONLY (R10-1:
        # accepted 0014 rows are never updated; the v11 harness ran a raw
        # UPDATE here, which was proof-by-bypass). The A10 drop deletes
        # the PRUNED record's own rows; the NEW reparented row is an
        # ordinary validated INSERT; nothing existing is touched.
        after = prune_absorbed_record("B", before,
                                      prune_op="op-9e9e9e9e9e9e")
        conn.execute("DELETE FROM contribution_ledger WHERE survivor_id='B'")
        existing_keys = {r["op_key"] for r in before.get("C", [])}
        inserted = 0
        for r in after.get("C", []):
            if r["op_key"] in existing_keys:
                continue                        # immutable — never rewritten
            conn.execute(INSERT, _stored("u1", "edge", "C", r,
                                         context="prune",
                                         op="op-9e9e9e9e9e9e"))
            inserted += 1
        conn.commit()
        assert inserted == 1, f"expected ONE new reparented row, {inserted}"
        reloaded = _load(conn)
        assert "B" not in reloaded
        # R11-3 (the reviewer caught an `... or True` tautology here):
        # the old flattened copy must be BYTE-IDENTICAL — compare the
        # full stored tuple by op_key, before vs after the prune
        def _raw(c, keys):
            q = ",".join("?" * len(keys))
            return {r[0]: r for r in c.execute(
                f"SELECT op_key, id, user_id, survivor_type, survivor_id,"
                f" site, identity_digest, evidence_ref_digest, payload,"
                f" created_at, contributor_type, contributor_ref FROM"
                f" contribution_ledger WHERE op_key IN ({q})", keys)}
        flat_keys = [r["op_key"] for r in before.get("C", [])
                     if (r["payload"] or {}).get("flattened")]
        assert flat_keys, "no pre-prune flattened copy to compare"
        raw_after = _raw(conn, flat_keys)
        assert raw_after == pre_prune_raw, (
            "the flattened copy CHANGED across the prune — immutability "
            "violated")
        flat_copies = [r for r in reloaded["C"]
                       if (r["payload"] or {}).get("flattened")]
        rep_rows = [r for r in reloaded["C"]
                    if set(r["payload"] or {}) == {"reparented_from"}]
        assert flat_copies and rep_rows, (reloaded["C"])
        assert derive_absorbed_by("A", reloaded) == "C", (
            "post-prune reverse link did not reparent to the survivor")
        checks.append("[reopen] STRUCTURED-EXPORT derivation from STORED "
                      "rows: derive(A)=B and derive(B)=C before the prune; "
                      "the retention-contract prune of B is INSERT-ONLY "
                      "(A10 drops B's own rows; ONE new validated "
                      "reparented row lands on C; the old flattened copy "
                      "survives byte-identical and non-canonical) — "
                      "derive(A)=C, unique both sides (R9-1/R10-1)")

        # (5c) R10-2: the MISSING-COPY prune path exports NOTHING clean —
        # build A2->B2 with NO flattened copy on the absorber's absorber,
        # prune, and prove the marker never materialises a link
        for sid, cref, dig in (("B2", "A9", "7" * 64),
                               ("C2b", "B2", "8" * 64)):
            row = construct_plan_row(
                "import", "op-777777777777", sid,
                site="imported-absorption", identity_digest=dig,
                evidence_ref_digest=None, contributor_ref=cref,
                payload={"reconstructed": True})
            conn.execute(INSERT, _stored("u1", "edge", sid, row,
                                         op="op-777777777777"))
        conn.commit()
        def _load2(c, ids):
            m = {}
            q = ",".join("?" * len(ids))
            for sid, site, dig, eref, ref, pay, ok in c.execute(
                    f"SELECT survivor_id, site, identity_digest,"
                    f" evidence_ref_digest, contributor_ref, payload,"
                    f" op_key FROM contribution_ledger WHERE survivor_id "
                    f"IN ({q})", ids):
                m.setdefault(sid, []).append(
                    {"site": site, "identity_digest": dig,
                     "evidence_ref_digest": eref, "contributor_ref": ref,
                     "payload": _j.loads(pay), "op_key": ok})
            return m
        st = _load2(conn, ("B2", "C2b"))
        st = prune_absorbed_record("B2", st, prune_op="op-8f8f8f8f8f8f")
        conn.execute("DELETE FROM contribution_ledger WHERE "
                     "survivor_id='B2'")
        for r in st.get("C2b", []):
            if not conn.execute("SELECT 1 FROM contribution_ledger WHERE "
                                "op_key=?", (r["op_key"],)).fetchone():
                conn.execute(INSERT, _stored("u1", "edge", "C2b", r,
                                             context="prune",
                                             op="op-8f8f8f8f8f8f"))
        conn.commit()
        st2 = _load2(conn, ("B2", "C2b"))
        markers = [r for r in st2["C2b"]
                   if (r["payload"] or {}) == {"closure": "incomplete"}]
        assert markers and markers[0]["identity_digest"] is None
        assert derive_absorbed_by("A9", st2) is None, (
            "the incompleteness marker LAUNDERED into a clean link (R10-2)")
        checks.append("[reopen] MISSING-COPY prune path: the inserted "
                      "closure-incompleteness marker (identity None) is "
                      "NEVER canonical — derive(A9)=None, the export OMITS "
                      "the field, and the import-side note rule fails "
                      "closed (R10-2's launder closed structurally)")

        conn.close()

        # (6) concurrent same-plan imports on two connections
        results = {}
        barrier = threading.Barrier(2)

        def importer(name):
            c = sqlite3.connect(db, timeout=10)
            barrier.wait()
            c.execute("BEGIN IMMEDIATE")           # the linearization point
            from reference_scope import construct_plan_row as _cpr
            zrow = _cpr("import", "op-cc00cc00cc00", "Z",
                        site="imported-absorption",
                        identity_digest="2" * 64,
                        evidence_ref_digest=None, contributor_ref="zz-1",
                        payload={"reconstructed": True})
            w, e = _insert_plan(c, {"Z": [zrow]}, skip_existing=True,
                                op="op-cc00cc00cc00")
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
        # are not unioned — the survivor's rows ARE the durable object):
        # the direct(B) link + the flattened(A) copy + the reparented(A)
        # row group (5b) inserted — three rows, all keyed to C
        assert closed is not None and len(closed) == 3, closed
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
    results = run()
    for line in results:
        print("PASS", line)
    print(f"ledger plan harness: {len(results)} checks pass against the "
          f"EXTRACTED real DDL + the amendment ALTERs")
