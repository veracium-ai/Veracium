"""specs/0021 §7b — the SCHEMA_V8 dual-manifestation evidence GENERATOR
(external round 10's artifact ask: the literal constructor and the
MEASURED ALTER-path stored DDL, produced NOW, never promised).

Emits, deterministically:
1. the LITERAL SCHEMA_V8 `contribution_ledger` CONSTRUCTOR — the accepted
   v7 constructor text (read from the SHIPPED `SCHEMA_V7` tuple, never
   retyped) with the two rider columns appended after `created_at`;
2. the MEASURED ALTER-path stored DDL — a real SQLite database is built
   from the v7 constructor, the rider's two ALTER statements run, and
   sqlite_master's stored text is read back (byte-authoritative; SQLite's
   ALTER-append layout differs from the constructor bytes — the 0014
   supersession_operations precedent);
3. a PARITY proof: PRAGMA table_info over both manifestations yields the
   IDENTICAL (name, type, notnull, pk) column sequence;
4. the sha-pinned 0013 STEP EVIDENCE: the sha256 of each ALTER statement
   (the D2 migration's declared steps) and of both manifestation texts.

The seal records this output as `schema_v8_evidence.txt`; the 0019 rider
(0021 §7b) cites the recorded shas. At the acceptance flip the same
generation runs on the QUALIFIED runtime and enters
`specs/schema_evidence.py`'s generated evidence (C2 of the rider).

Run: `<venv>/python specs/evidence/0020/schema_v8_evidence.py`
"""

from __future__ import annotations

import hashlib
import pathlib
import sqlite3
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))

RIDER_ALTERS = (
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_type TEXT",
    "ALTER TABLE contribution_ledger ADD COLUMN contributor_ref TEXT",
)


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    from veracium.store.schema_version import SCHEMA_V7
    v7 = [o for o in SCHEMA_V7
          if o.kind == "table" and o.name == "contribution_ledger"]
    assert len(v7) == 1, "expected exactly one v7 contribution_ledger table"
    v7_sql = v7[0].ddl
    assert v7_sql.rstrip().endswith(")"), "unexpected v7 constructor shape"
    # (1) the literal v8 CONSTRUCTOR: the v7 text with the rider columns
    # appended after created_at (the table has no table-level constraints,
    # so the append point is the closing paren)
    v8_constructor = (v7_sql.rstrip()[:-1].rstrip()
                      + ",\n    contributor_type TEXT,"
                      + " contributor_ref TEXT\n)")

    # (2) the MEASURED ALTER-path stored DDL
    conn = sqlite3.connect(":memory:")
    conn.execute(v7_sql)
    for stmt in RIDER_ALTERS:
        conn.execute(stmt)
    measured = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND "
        "name='contribution_ledger'").fetchone()[0]

    # (3) PARITY: both manifestations yield identical logical columns
    conn2 = sqlite3.connect(":memory:")
    conn2.execute(v8_constructor)
    cols_alter = conn.execute(
        "PRAGMA table_info(contribution_ledger)").fetchall()
    cols_ctor = conn2.execute(
        "PRAGMA table_info(contribution_ledger)").fetchall()
    proj = [tuple(c[1:4]) + (c[5],) for c in cols_alter]
    proj2 = [tuple(c[1:4]) + (c[5],) for c in cols_ctor]
    assert proj == proj2, ("MANIFESTATION PARITY FAILED:\n"
                           f"alter: {proj}\nctor:  {proj2}")
    conn.close(); conn2.close()

    print("SCHEMA_V8 contribution_ledger — dual-manifestation evidence")
    print("=" * 64)
    print("\n[1] THE LITERAL CONSTRUCTOR (v7 text + rider columns):\n")
    print(v8_constructor)
    print(f"\nconstructor_sha256: {_sha(v8_constructor)}")
    print("\n[2] THE MEASURED ALTER-PATH STORED DDL (sqlite_master,"
          " byte-authoritative):\n")
    print(measured)
    print(f"\nalter_path_sha256: {_sha(measured)}")
    print("\n[3] PARITY: PRAGMA table_info identical over both"
          f" manifestations ({len(proj)} columns:"
          f" {[c[0] for c in proj]})")
    print("\n[4] THE 0013-DECLARED MIGRATION STEPS, sha-pinned:")
    for stmt in RIDER_ALTERS:
        print(f"  step_sha256 {_sha(stmt)}  {stmt}")
    print(f"\nsqlite_runtime: {sqlite3.sqlite_version}")
    print("schema v8 evidence: BOTH manifestations generated + parity"
          " proven")
    return 0


if __name__ == "__main__":
    sys.exit(main())
