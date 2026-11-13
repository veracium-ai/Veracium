"""specs/0003 §4c-ii v18.7/v18.8, I6d's writers' census: the bind's premise, by property.

The empty body's bind is sound only if every writer of a table a recall reads advances the user's store_version in the
same transaction. The tables are not listed by hand: they are TRACED from the SQL of real recalls on each assembly
path (the legacy projection, the fused construction under a policy, a principal-bearing call), so a new read path
joins the census by itself. Every function under src/veracium that writes one of them is then classified: it bumps
(`_bump`), or every caller of it does, or it is named below with its reason. A writer added later and not classified
fails here by name; a table name computed at run time must be resolved or the census refuses.
"""
import ast
import json
import pathlib
import re

import veracium
from veracium import EvidenceContext, Memory, MemoryConfig
from veracium.scope import Identity

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "veracium"
TABLE_REF = re.compile(r'\b(?:FROM|JOIN)\s+"?([A-Za-z_][A-Za-z0-9_]*)', re.I)
WRITE = re.compile(r'\b(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+"?([A-Za-z_][A-Za-z0-9_]*|\{)',
                   re.I)
# the bound row itself and the counter: publish and discard are bound by the row and its basis, never bump by design
NOT_RECORDS = {"wiki", "write_counter"}
NAMED = {   # (module, function) -> why it may write without its own or its callers' bump
    ("store/migration.py", "_migrate_outcome_chains"): "a schema-migration step (`veracium migrate`, quiesced store)",
    ("store/migration.py", "_data_notice_state"): "a schema-migration step (`veracium migrate`, quiesced store)",
    ("store/sqlite.py", "_write_op"): "consolidation: its outputs are visible only at its counted cutover",
    ("store/sqlite.py", "_claim_inputs"): "consolidation: its outputs are visible only at its counted cutover",
    ("store/sqlite.py", "_abandon"): "consolidation: its outputs are visible only at its counted cutover",
    ("store/sqlite.py", "write_consolidation_output_if_current"): "consolidation: visible only at its counted cutover",
    ("store/sqlite.py", "delete_claimed_inputs_if_current"): "consolidation: visible only at its counted cutover",
    ("store/sqlite.py", "forget_user"): "resets the counter: the stated limit (0003 §4c-ii v18.8; the floor, §10 Q8)",
    ("store/schema_version.py", "_mint_store_identity"): "the store's identity, minted once at create or migrate; "
                                                         "store-level, never a user's record",
}
# a write whose table name is computed at run time, resolved: (module, function) -> the tables it can write
COMPUTED = {
    ("store/sqlite.py", "commit_outcome_import_plan"): "resolved: it bumps in its own transaction",
    ("store/sqlite.py", "forget_user"): "resolved: _ERASE_TABLES, every per-user table (0008 §6g), named above",
}


class _Stub:
    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Berlin",
                                            "volatility": "durable"}], "episode": "The user said Berlin.",
                               "instructions": []})
        return "The user lives in Berlin."


def _traced_tables(tmp_path) -> set:
    m = Memory(llm=_Stub(), config=MemoryConfig(db_path=str(tmp_path / "trace.db"), require_source_id=False,
                                                scope_groups={}))
    m.remember("u", "I live in Berlin.", date="2026-11-12", context=EvidenceContext.direct())
    sql = []
    m.store._conn.set_trace_callback(sql.append)
    lane = veracium.PolicyLane(policy_id="p", policy_version="1", tags_matched=("t",), ranks={})
    for kw in (dict(), dict(policy=lane), dict(principal=Identity(origin=None, source_id="s"))):
        m.recall("u", "where does the user live", semantic=False, **kw)
    m.store._conn.set_trace_callback(None)
    m.close()
    return {t for s in sql if s.lstrip().upper().startswith(("SELECT", "WITH")) for t in TABLE_REF.findall(s)} - \
        {"sqlite_master"}


def _writers(tables: set):
    """(module, function) -> (tables written, writes a computed name, bumps itself, source), over src/veracium."""
    out, sources = {}, {}
    for f in sorted(SRC.rglob("*.py")):
        rel = str(f.relative_to(SRC))
        text = f.read_text()
        for fn in ast.walk(ast.parse(text)):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            src = ast.get_source_segment(text, fn) or ""
            sources[(rel, fn.name)] = src
            written, computed = set(), False
            for node in ast.walk(fn):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    written |= {t for t in WRITE.findall(node.value) if t != "{"}
                elif isinstance(node, ast.JoinedStr):
                    joined = "".join(v.value if isinstance(v, ast.Constant) else "{" for v in node.values)
                    for t in WRITE.findall(joined):
                        computed |= t == "{"
                        if t != "{":
                            written.add(t)
            if written & tables or computed:
                out[(rel, fn.name)] = (written & tables, computed, "._bump(" in src)
    return out, sources


def test_every_writer_of_a_table_a_recall_reads_advances_the_counter_or_is_named(tmp_path):
    tables = _traced_tables(tmp_path)
    assert {"edges", "episodes", "redactions"} <= tables, tables          # the trace is not vacuous
    records = tables - NOT_RECORDS
    writers, sources = _writers(records)
    assert writers, "no writer found: the census read nothing"

    def callers(key):
        """Callers of `key` in its own module (a bare or `self.` call) and in any module (`store.<name>(`)."""
        mod, name = key
        local = re.compile(rf"(?:self\.|(?<![.\w])){re.escape(name)}\(")
        remote = re.compile(rf"\bstore\.{re.escape(name)}\(")
        return [k for k, s in sources.items() if k[1] != name and k != key
                and ((k[0] == mod and local.search(s)) or remote.search(s))]

    def advances(key, seen=()):
        if key in writers and writers[key][2] or "._bump(" in sources.get(key, ""):
            return True
        cs = callers(key)
        return bool(cs) and all(c not in seen and advances(c, seen + (key,)) for c in cs)

    unclassified, unresolved = [], []
    for key, (written, computed, _bumps) in sorted(writers.items()):
        if computed and key not in COMPUTED:
            unresolved.append(key)
        if key in NAMED:
            continue
        if not advances(key):
            unclassified.append((key, sorted(written)))
    assert not unresolved, f"a computed table name the census cannot resolve: {unresolved}"
    assert not unclassified, f"writers of a table a recall reads that neither advance the counter nor are named: {unclassified}"
    stale = [k for k in NAMED if k not in writers]
    assert not stale, f"named writers that no longer write a recall table (drop them): {stale}"


def _segments(sql: list) -> list:
    """The trace split into transactions: (statements, ended by) for each BEGIN … COMMIT/ROLLBACK; a write outside
    any BEGIN is its own one-statement transaction (autocommit)."""
    out, cur = [], None
    for st in sql:
        head = st.lstrip().upper()
        if head.startswith("BEGIN"):
            cur = []
        elif head.startswith(("COMMIT", "END")) and cur is not None:
            out.append((cur, "COMMIT")); cur = None
        elif head.startswith("ROLLBACK") and cur is not None:
            out.append((cur, "ROLLBACK")); cur = None
        elif cur is not None:
            cur.append(st)
        elif head.startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
            out.append(([st], "AUTOCOMMIT"))
    return out


def test_every_committed_transaction_that_changes_a_record_advances_the_counter_in_it(tmp_path):
    """The census's other half, by execution: the static census accepts a function that bumps, but the premise is
    'in the SAME transaction'. Each public writer runs under a trace; every committed transaction that writes a table
    a recall reads must write write_counter too. (Found while building this: revocation's bump followed its COMMIT.)
    Erasure is the named exception: it deletes the counter (the stated limit, v18.8)."""
    from veracium import redaction
    records = _traced_tables(tmp_path) - NOT_RECORDS
    m = Memory(llm=_Stub(), config=MemoryConfig(db_path=str(tmp_path / "w.db"), require_source_id=False))
    sql = []
    m.store._conn.set_trace_callback(sql.append)
    m.remember("u", "I live in Berlin.", date="2026-11-12", context=EvidenceContext.direct())
    m.remember("u", "The user lives in Berlin.", date="2026-11-12", author=veracium.EvidenceAuthor.THIRD_PARTY,
               source_id="s1")
    edges = m.store.edges("u")
    m.confirm("u", edges[0].id)
    m.dispute("u", edges[-1].id, reason="no longer current")
    m.remember("u", "I work at Acme.", date="2026-11-13", context=EvidenceContext.direct())
    m.redact("u", edge_id=m.store.edges("u")[-1].id, reason=sorted(redaction.ORIGINATING_REASONS)[0])
    m.remember("u", "The user likes tea.", date="2026-11-13", author=veracium.EvidenceAuthor.THIRD_PARTY,
               source_id="s2")
    m.revoke_source("u", None, "s2", sorted(redaction.SOURCE_REVOCATION_REASONS)[0])
    m.unrevoke_source("u", None, "s2", sorted(redaction.SOURCE_LIFT_REASONS)[0])
    m.maintain("u")
    m.forget("u")
    m.store._conn.set_trace_callback(None)
    m.close()
    pat = re.compile(r'\b(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|UPDATE|DELETE\s+FROM|REPLACE\s+INTO)\s+"?([A-Za-z_][A-Za-z0-9_]*)', re.I)
    bad, erasures, counted = [], 0, 0
    for stmts, end in _segments(sql):
        if end == "ROLLBACK":
            continue
        written = {t for st in stmts for t in pat.findall(st)}
        if not written & records:
            continue
        if any(re.search(r"DELETE\s+FROM\s+write_counter", st, re.I) for st in stmts):
            erasures += 1                                  # forget_user: the named limit
            continue
        if "write_counter" in written:
            counted += 1
        else:
            bad.append((end, sorted(written & records), [st[:90] for st in stmts if pat.search(st)][:4]))
    assert counted >= 8 and erasures == 1, (counted, erasures)          # the scenario reached its writers
    assert not bad, f"a committed transaction changed a record a recall reads without advancing the counter: {bad}"
