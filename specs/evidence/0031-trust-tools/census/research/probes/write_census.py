"""Research's independent write census of the trust verbs (0031 trust-tools v0.13; the external design review's TT-R1-01/02).

    python write_census.py SCRATCH_DIR          (veracium importable from the source under review)

Each verb runs on its OWN fresh store, seeded alike: one user edge `e1` (evidence_ref `ev1`), a second user edge `e2`,
and one episode `ep1` sharing `ev1` (0041's over-naming join). For each call it reports, MEASURED, not read:
  - every write statement the store connection executed (sqlite3's trace callback: INSERT/UPDATE/DELETE/REPLACE), by
    table and by count;
  - every table's row diff (added, removed, changed), so a write the trace names is tied to its effect;
  - every new or changed episode and edge, with its summary or object and its provenance's source_id and call_path
    (the scope carriers);
  - the returned value's structure (keys, recursively, with value types), the carrier a principal-facing projection
    must scope (TT-R1-02).
The fixture is the product's own (tests/test_0008_ra2_public_registry.py: a Memory with a null model, edges added through
the store). No model is called. Nothing outside SCRATCH_DIR is written.
"""
import json
import os
import re
import sqlite3
import sys

from veracium import Memory, MemoryConfig
from veracium.schema import Disclosure, Edge, Episode, EvidenceAuthor, Provenance

SCRATCH = sys.argv[1] if len(sys.argv) > 1 else "."
U = "census-user"
def _strict_pairs(pairs):
    """A JSON object hook that REFUSES a duplicate key (0026's rule for every evidence decoder)."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key {k!r}")
        out[k] = v
    return out


WRITE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b", re.I)
TABLE = re.compile(r"^\s*(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE(?:\s+OR\s+\w+)?|DELETE\s+FROM)\s+[\"`]?(\w+)", re.I)


def fresh(name):
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(
        db_path=os.path.join(SCRATCH, f"{name}.db"), wiki_recompile_after_writes=0, scope_groups={},
        require_source_id=False))
    for ident, obj in (("e1", "e1-content"), ("e2", "e2-content")):
        m.store.add_edge(Edge(id=ident, user_id=U, subject="user", relation=f"likes_{ident}", object=obj,
                              provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev1",
                                                    disclosure=Disclosure.MENTIONABLE)))
    m.store.add_episode(Episode(id="ep1", user_id=U, date="2026-11-14", summary="ep1 summary",
                                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev1")))
    return m


def snapshot(conn):
    out = {}
    for (t,) in conn.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'"):
        cols = [c[1] for c in conn.execute(f"pragma table_info('{t}')")]
        out[t] = (cols, {tuple(r) for r in conn.execute(f"select * from '{t}'")})
    return out


def shape(v, depth=0):
    if depth > 4:
        return "…"
    if hasattr(v, "model_dump"):                        # a pydantic result (RedactionReceipt): its fields
        return {"<" + type(v).__name__ + ">": shape(v.model_dump(), depth + 1)}
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [shape(v[0], depth + 1)] if v else []
    return type(v).__name__


def carriers(table, cols, row):
    d = dict(zip(cols, row))
    if isinstance(d.get("json"), str):                   # edges and episodes keep the record in a json column
        d = {**json.loads(d["json"], object_pairs_hook=_strict_pairs), **{k: v for k, v in d.items() if k != "json"}}
    prov = d.get("provenance")
    if isinstance(prov, dict):
        prov = json.dumps(prov)
    src = cp = None
    if isinstance(prov, str) and prov.startswith("{"):
        p = json.loads(prov, object_pairs_hook=_strict_pairs)
        src, cp = p.get("source_id"), p.get("call_path")
    text = d.get("summary") or d.get("object") or ""
    return {"id": d.get("id"), "text": str(text)[:90], "source_id": src, "call_path": cp,
            **({"call_path_col": d["call_path"]} if "call_path" in d and table == "confirmations" else {})}


def run(label, call):
    m = fresh(re.sub(r"\W+", "_", label))
    conn = m.store._conn
    before = snapshot(conn)
    stmts = []
    conn.set_trace_callback(lambda s: stmts.append(s) if WRITE.match(s) else None)
    try:
        result = call(m)
        err = None
    except Exception as e:                                # a refusal is reported, not hidden
        result, err = None, f"{e.__class__.__name__}: {str(e)[:160]}"
    conn.set_trace_callback(None)
    after = snapshot(conn)
    by_table = {}
    for s in stmts:
        mt = TABLE.match(s)
        t = mt.group(1) if mt else "?"
        by_table[t] = by_table.get(t, 0) + 1
    diff = {}
    for t, (cols, rows) in after.items():
        old = before.get(t, (cols, set()))[1]
        added, removed = rows - old, old - rows
        if added or removed:
            diff[t] = {"added": len(added), "removed": len(removed),
                       "new_rows": [carriers(t, cols, r) for r in sorted(added, key=str)][:6]
                       if t in ("episodes", "edges", "confirmations") else None}
    print(f"\n=== {label}")
    print("  error:", err)
    print("  write statements by table:", dict(sorted(by_table.items())))
    for t, d in sorted(diff.items()):
        print(f"  row diff {t}: +{d['added']} -{d['removed']}")
        for r in d["new_rows"] or []:
            print(f"      new/changed row: {r}")
    print("  returns:", json.dumps(shape(result), default=str)[:1500])
    m.close()


if __name__ == "__main__":
    print(f"veracium from {__import__('veracium').__file__}")
    run("correct(e1)", lambda m: m.correct(U, "e1", "e1-corrected"))
    run("dispute(e1)", lambda m: m.dispute(U, "e1", reason="no longer true"))
    run("confirm(e1)", lambda m: m.confirm(U, "e1"))
    run("redact(edge e1)", lambda m: m.redact(U, edge_id="e1", reason="subject_request"))
    run("redact(episode ep1)", lambda m: m.redact(U, episode_id="ep1", reason="subject_request"))
    run("forget(user)", lambda m: m.forget(U))
