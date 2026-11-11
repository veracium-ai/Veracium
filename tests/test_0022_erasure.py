"""specs/0022 × 0008 §6g — data-subject erasure reaches the revocation ledger (the owner, 2026-10-29: "Erase it").

`source_revocations` was the one per-user table outside `_ERASE_TABLES` (a census of a fresh store at d087f6e: 28
tables, 21 with a `user_id` column, 20 erased). `forget_user` left the user's revoke rows, and the standing state they
derive, so a recreated user id met 0023's guards on a source revoked for the erased one. The census below is the gate
for the class: it is DERIVED from the store's own schema, so a new per-user table that erasure misses fails here
without anyone having named it.
"""

import ast
import pathlib
import re
from datetime import datetime, timezone

from veracium import SqliteStore
from veracium.schema import Episode, EvidenceAuthor, Provenance
from veracium.store import revocation as rv
from veracium.store.revocation_sweep import digest_of
from veracium.store.sqlite import _ERASE_TABLES

U, V = "u", "v"
AT = "2026-08-21T00:00:00Z"
NOW = datetime(2026, 8, 1, tzinfo=timezone.utc)


def _episode(user, eid, source_id):
    return Episode(id=eid, user_id=user, date="2026-08-01", summary=f"from {source_id}",
                   provenance=Provenance(author_of_evidence=EvidenceAuthor.THIRD_PARTY, evidence_ref=eid,
                                         observed_at=NOW, source_id=source_id))


def _revocations(s, user):
    return s._conn.execute("SELECT seq, identity_digest, action, reason, at FROM source_revocations WHERE user_id=?",
                           (user,)).fetchall()


def test_every_per_user_table_is_erased_and_every_erased_table_is_per_user(tmp_path):
    """The census, by PROPERTY: a table is per-user iff it has a `user_id` column. Store-level tables (no such column:
    act_counter, store_identity, the 0044 plan tables, …) are outside by that property, never by a list of names.
    Mutant: drop any table from `_ERASE_TABLES`, or add a per-user table to the schema without it."""
    s = SqliteStore(str(tmp_path / "census.db"))
    tables = [r[0] for r in s._conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
              if not r[0].startswith("sqlite_")]          # SQLite's own internal tables, by exact prefix
    per_user = {t for t in tables if any(c[1] == "user_id" for c in s._conn.execute(f"PRAGMA table_info({t})"))}
    assert per_user, "the census found no per-user table: it is measuring nothing"
    assert per_user - set(_ERASE_TABLES) == set(), (
        f"per-user tables forget_user does not erase: {sorted(per_user - set(_ERASE_TABLES))}")
    assert set(_ERASE_TABLES) - per_user == set(), (
        f"_ERASE_TABLES names tables without a user_id column: {sorted(set(_ERASE_TABLES) - per_user)}")


def test_forget_erases_the_users_revocations_and_no_one_elses(tmp_path):
    s = SqliteStore(str(tmp_path / "f.db"))
    d = digest_of(None, "src:A", s.local_origin())
    for user in (U, V):
        s.add_episode(_episode(user, f"ep-{user}", "src:A"))
        rv.revoke_source(s, user, d, "revoke", "policy", AT)
    v_before = _revocations(s, V)
    assert _revocations(s, U) and v_before, "the fixture revoked nothing"
    s.forget_user(U)
    assert _revocations(s, U) == [], "the erased user's revocation rows survived forget_user"
    assert s.standing_revocations(U) == frozenset(), "a revocation still stands for the erased user"
    assert _revocations(s, V) == v_before, "forget_user touched another user's revocation rows"
    assert d in s.standing_revocations(V)


def test_a_recreated_user_id_starts_with_no_standing_revocation(tmp_path):
    """The behavioural face: after erasure the id is free again (0008 §6g), and nothing erased constrains it. Before
    the fix, a write from the revoked source under the recreated id was still inside the standing set (0023's guards:
    no reinforcement, no supersession, out of consolidation pools)."""
    s = SqliteStore(str(tmp_path / "r.db"))
    d = digest_of(None, "src:A", s.local_origin())
    s.add_episode(_episode(U, "ep-1", "src:A"))
    rv.revoke_source(s, U, d, "revoke", "policy", AT)
    assert d in s.standing_revocations(U)
    s.forget_user(U)
    s.add_episode(_episode(U, "ep-2", "src:A"))
    assert d not in s.standing_revocations(U)
    assert [e.id for e in s.episodes(U)] == ["ep-2"]


# ---- the ledger's one DELETE route (research, 2026-10-29) ---------------------------------------------------------
# tests/support_0022_updater.py finds writers by the table's LITERAL name, so `forget_user`'s interpolated
# `DELETE FROM {table}` over `_ERASE_TABLES` deletes from the ledger unseen by it: 0022 R1's "no UPDATE or DELETE writer"
# would read true with the erasure in place. This check names the erasure route instead of missing it.

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "veracium"
# N1 (shipped-changes round 1), widened by research's stage 2 on 974a6122 (R2S-4, every spelling measured on SQLite): the
# name bare or quoted ("", '', ``, [], and a \" escape inside a Python string), optionally schema-qualified (main./temp.,
# the schema quoted too), with whitespace or SQL comments between the keywords; DROP TABLE as well as DELETE FROM; and an
# interpolation of ANY expression (`{}`, `{0}`, `{t}`, `{self.t}`, `{ts[0]}`, `{t!s}`).
_SEP = r"(?:\s|/\*.*?\*/|--[^\n]*(?:\n|$))+"
_GAP = r"(?:\s|/\*.*?\*/)*"
_OPEN, _CLOSE = r"(?:\\?[\"'`]|\[)?", r"(?:\\?[\"'`]|\])?"
_NAME = rf"(?:{_OPEN}(?:main|temp){_CLOSE}{_GAP}\.{_GAP})?{_OPEN}source_revocations{_CLOSE}(?![\w])"
_LITERAL = re.compile(rf"DELETE{_SEP}FROM{_SEP}{_NAME}", re.I | re.S)
_DROP = re.compile(rf"DROP{_SEP}TABLE(?:{_SEP}IF{_SEP}EXISTS)?{_SEP}{_NAME}", re.I | re.S)
_INTERPOLATED = re.compile(rf"DELETE{_SEP}FROM{_SEP}\{{[^{{}}]*\}}", re.I | re.S)


def ledger_delete_routes(files, erase_tables):
    """`files`: {path: source text}. Returns the problems: a literal DELETE or DROP of the ledger anywhere in a file's
    text, in a function or at module level; an interpolated DELETE outside `forget_user`; a `forget_user` whose
    interpolated DELETE is not its loop over `_ERASE_TABLES`; the ledger absent from `erase_tables`; no erasure route.

    THE GRAMMAR IT READS (N1, widened at R2S-4: what "anywhere" means, stated): the text of every .py file under
    src/veracium, searched in any case for `DELETE FROM <name>` and `DROP TABLE [IF EXISTS] <name>`, the words separated
    by whitespace or SQL comments (/* */, --), where <name> is source_revocations bare or quoted with "", '', `` or []
    (a \" escape inside a Python string included), optionally prefixed main. or temp., that schema quoted the same way;
    and for `DELETE FROM {<any expression>}` (an f-string or .format field, empty included). It does NOT read: SQL
    assembled from pieces (`"DELETE FROM " + t`, `" ".join(...)`), a table name passed through `%` formatting, a DELETE
    whose name is a bound variable SQLite cannot take (it refuses parameters for names), SQL in non-.py files or read
    from disk, `executescript` of text built elsewhere, a trigger body created at run time, or a statement SQLite
    reaches through a view, an ATTACHed database or a rename. It is a source census over those spellings, not an
    analysis of every SQL a process could run."""
    problems, routes = [], []
    for path, text in files.items():
        funcs = [n for n in ast.walk(ast.parse(text)) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        def owner(line):
            inside = [f for f in funcs if f.lineno <= line <= f.end_lineno]
            return min(inside, key=lambda f: f.end_lineno - f.lineno) if inside else None

        for m in _LITERAL.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            f = owner(line)
            problems.append(f"{path}:{line} `{f.name if f else '<module>'}` DELETEs source_revocations by name")
        for m in _DROP.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            f = owner(line)
            problems.append(f"{path}:{line} `{f.name if f else '<module>'}` DROPs source_revocations by name")
        for m in _INTERPOLATED.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            f = owner(line)
            if f is None or f.name != "forget_user":
                problems.append(f"{path}:{line} `{f.name if f else '<module>'}` has an interpolated DELETE outside "
                                f"forget_user")
            elif "for table in _ERASE_TABLES" not in (ast.get_source_segment(text, f) or ""):
                problems.append(f"{path}:{line} forget_user's interpolated DELETE is not its _ERASE_TABLES loop")
            else:
                routes.append((path, f.name))
    if "source_revocations" not in erase_tables:
        problems.append("source_revocations is not in _ERASE_TABLES")
    if not routes:
        problems.append("no erasure route found: the check is measuring nothing")
    return problems


def test_the_ledgers_only_delete_route_is_forget_users_erase_loop():
    files = {str(p.relative_to(SRC)): p.read_text() for p in sorted(SRC.rglob("*.py"))}
    assert ledger_delete_routes(files, _ERASE_TABLES) == []


def test_the_delete_route_check_refuses_each_planted_defect():
    """Controls, on the check's own input: the real tree passes; each planted defect is named."""
    real = (SRC / "store" / "sqlite.py").read_text()
    base = {"store/sqlite.py": real}
    assert ledger_delete_routes(base, _ERASE_TABLES) == []
    elsewhere = {**base, "x.py": "def purge(c):\n    c.execute('DELETE FROM source_revocations WHERE user_id=?')\n"}
    assert any("`purge` DELETEs source_revocations by name" in p for p in ledger_delete_routes(elsewhere, _ERASE_TABLES))
    rogue = {**base, "y.py": "def sweep(c, t):\n    c.execute(f'DELETE FROM {t} WHERE 1')\n"}
    assert any("`sweep` has an interpolated DELETE outside forget_user" in p
               for p in ledger_delete_routes(rogue, _ERASE_TABLES))
    # N1's controls (the reviewer's two spellings, erasure-probe.json, and their siblings): each was read as clean
    for name, src in {
        "quoted": "def purge(c):\n    c.execute('DELETE FROM \"source_revocations\" WHERE user_id=?')\n",
        "backtick": "def purge(c):\n    c.execute('DELETE FROM `source_revocations` WHERE 1')\n",
        "bracket": "def purge(c):\n    c.execute('DELETE FROM [source_revocations] WHERE 1')\n",
        "schema": "def purge(c):\n    c.execute('delete from main . source_revocations where 1')\n",
    }.items():
        assert any("`purge` DELETEs source_revocations by name" in p
                   for p in ledger_delete_routes({**base, "q.py": src}, _ERASE_TABLES)), name
    module = {**base, "m.py": "connection.execute('DELETE FROM source_revocations WHERE user_id=?', ('u',))\n"}
    assert any("m.py:1 `<module>` DELETEs source_revocations by name" in p
               for p in ledger_delete_routes(module, _ERASE_TABLES))
    module_f = {**base, "n.py": "for t in TABLES:\n    connection.execute(f'DELETE FROM {t}')\n"}
    assert any("n.py:2 `<module>` has an interpolated DELETE outside forget_user" in p
               for p in ledger_delete_routes(module_f, _ERASE_TABLES))
    # R2S-4 (research's stage 2, each measured on SQLite as deleting the rows or dropping the table): each is named
    for name, src in {
        "escaped double quote": 'def purge(c):\n    c.execute("DELETE FROM \\"source_revocations\\"")\n',
        "single-quoted identifier": "def purge(c):\n    c.execute(\"DELETE FROM 'source_revocations'\")\n",
        "quoted schema": "def purge(c):\n    c.execute('DELETE FROM \"main\".\"source_revocations\"')\n",
        "comment between the keywords": "def purge(c):\n    c.execute('DELETE /* x */ FROM source_revocations')\n",
    }.items():
        assert any("`purge` DELETEs source_revocations by name" in p
                   for p in ledger_delete_routes({**base, "q.py": src}, _ERASE_TABLES)), name
    drop = {**base, "d.py": "def purge(c):\n    c.execute('DROP TABLE IF EXISTS source_revocations')\n"}
    assert any("`purge` DROPs source_revocations by name" in p for p in ledger_delete_routes(drop, _ERASE_TABLES))
    for name, src in {
        ".format with {}": "def sweep(c, t):\n    c.execute('DELETE FROM {} WHERE 1'.format(t))\n",
        "f-string attribute": "def sweep(self, c):\n    c.execute(f'DELETE FROM {self.table} WHERE 1')\n",
        "f-string subscript": "def sweep(c, ts):\n    c.execute(f'DELETE FROM {ts[0]} WHERE 1')\n",
        "f-string conversion": "def sweep(c, t):\n    c.execute(f'DELETE FROM {t!s} WHERE 1')\n",
    }.items():
        assert any("`sweep` has an interpolated DELETE outside forget_user" in p
                   for p in ledger_delete_routes({**base, "s.py": src}, _ERASE_TABLES)), name
    near = {**base, "r.py": "def keep(c):\n    c.execute('DELETE FROM source_revocations_archive WHERE 1')\n"}
    assert ledger_delete_routes(near, _ERASE_TABLES) == [], "a different table whose name starts the same is not it"
    without = tuple(t for t in _ERASE_TABLES if t != "source_revocations")
    assert ledger_delete_routes(base, without) == ["source_revocations is not in _ERASE_TABLES"]
    assert ledger_delete_routes({}, _ERASE_TABLES) == ["no erasure route found: the check is measuring nothing"]
