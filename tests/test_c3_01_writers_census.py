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


# The modules the dynamic census runs: existing tests that already build the state each writer needs. Chosen by MEASURED
# reach (research's stage 2 on 35610a8a, B1: one hand-built scenario reached 6 of the 15 bump sites); the reach assertion
# below refuses if a bump site goes unreached, so a module dropped or a writer added fails by name.
CENSUS_MODULES = ("tests/test_lifecycle.py", "tests/test_0047_t10a_reply.py", "tests/test_0009_import_migration.py",
                  "tests/test_0010_consolidation_primitives.py", "tests/test_0044_t6_operation.py",
                  "tests/test_0044_t7_undo.py", "tests/test_0014_ledger.py", "tests/test_0022_revocation_operation.py")
# a writer that may change a recall table without the counter in its transaction, by function (cf. NAMED above)
NAMED_WRITERS = {
    "store/sqlite.py:_write_op", "store/sqlite.py:_claim_inputs", "store/sqlite.py:_abandon",
    "store/sqlite.py:write_consolidation_output_if_current", "store/sqlite.py:delete_claimed_inputs_if_current",
}   # consolidation: its outputs are visible only at its counted cutover (transition_consolidation_if_current bumps)


def _bump_sites() -> set:
    """Every call of the STORE's `_bump` in src/veracium, as 'module:innermost enclosing function' (a nested `plan`
    included): a call inside the store package, or on a receiver named `store` anywhere. (census.py's own `_bump` is the
    decision-site census's counter, another method.)"""
    sites = set()
    for f in sorted(SRC.rglob("*.py")):
        rel = str(f.relative_to(SRC))

        def walk(node, fn):
            for ch in ast.iter_child_nodes(node):
                name = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
                if isinstance(ch, ast.Call) and isinstance(ch.func, ast.Attribute) and ch.func.attr == "_bump" \
                        and fn is not None and (rel.startswith("store/") or (isinstance(ch.func.value, ast.Name)
                                                                             and ch.func.value.id == "store")):
                    sites.add(f"{rel}:{fn}")
                walk(ch, name)
        walk(ast.parse(f.read_text()), None)
    return sites


def test_every_committed_transaction_that_changes_a_record_advances_the_counter_in_it(tmp_path):
    """The census's other half, by execution and with measured reach. Every SqliteStore connection of the census
    modules is traced (specs/evidence/c3-01/census_trace_plugin.py), each statement attributed to the src function
    that issued it: every committed transaction in which a src writer changes a table a recall reads writes
    write_counter in that same transaction, or every such writer is named; erasure (it deletes the counter) is the
    stated limit. Writes no src function issued are the tests' own planted fixtures, not product writers. And every
    `_bump` call site in src was reached, so a writer whose bump moved out of its transaction is SEEN."""
    import os
    import subprocess
    import sys
    records = _traced_tables(tmp_path) - NOT_RECORDS
    out = tmp_path / "census.json"
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(ROOT / "specs" / "evidence" / "c3-01"),
                                                      os.environ.get("PYTHONPATH", "")]),
               C301_CENSUS_OUT=str(out), PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
                        "-p", "no:xdist", "-p", "census_trace_plugin", *CENSUS_MODULES], cwd=str(ROOT), env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
    d = json.loads(out.read_text())
    bad, counted, erasures = [], 0, 0
    for t in d["transactions"]:
        rec = [(tb, w) for tb, w in t["writes"] if tb in records and w]      # src writers of a recall table
        if not rec:
            continue
        if t["deletes_counter"]:
            erasures += 1
        elif any(tb == "write_counter" for tb, _w in t["writes"]):
            counted += 1
        elif not all(w in NAMED_WRITERS for _tb, w in rec):
            bad.append((t["end"], sorted({w for _tb, w in rec if w not in NAMED_WRITERS}), sorted({tb for tb, _ in rec})))
    assert counted > 100, counted                                             # the census reached its writers
    assert not bad, f"a committed transaction changed a recall table without advancing the counter in it: {bad[:5]}"
    unreached = _bump_sites() - set(d["reached"])
    assert not unreached, f"bump call sites no census module reached (add a module that drives them): {sorted(unreached)}"
