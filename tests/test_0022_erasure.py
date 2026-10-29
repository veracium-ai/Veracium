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
    tables = [r[0] for r in s._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
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
_LITERAL = re.compile(r"DELETE\s+FROM\s+source_revocations\b", re.I)
_INTERPOLATED = re.compile(r"DELETE\s+FROM\s+\{\w+\}", re.I)


def ledger_delete_routes(files, erase_tables):
    """`files`: {path: source text}. Returns the problems: a literal DELETE of the ledger anywhere; an interpolated
    DELETE outside `forget_user`; a `forget_user` whose interpolated DELETE is not its loop over `_ERASE_TABLES`; the
    ledger absent from `erase_tables`; no erasure route at all."""
    problems, routes = [], []
    for path, text in files.items():
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.get_source_segment(text, node) or ""
            if _LITERAL.search(body):
                problems.append(f"{path}:{node.lineno} `{node.name}` DELETEs source_revocations by name")
            if _INTERPOLATED.search(body):
                if node.name != "forget_user":
                    problems.append(f"{path}:{node.lineno} `{node.name}` has an interpolated DELETE outside forget_user")
                elif "for table in _ERASE_TABLES" not in body:
                    problems.append(f"{path}:{node.lineno} forget_user's interpolated DELETE is not its _ERASE_TABLES loop")
                else:
                    routes.append((path, node.name))
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
    without = tuple(t for t in _ERASE_TABLES if t != "source_revocations")
    assert ledger_delete_routes(base, without) == ["source_revocations is not in _ERASE_TABLES"]
    assert ledger_delete_routes({}, _ERASE_TABLES) == ["no erasure route found: the check is measuring nothing"]
