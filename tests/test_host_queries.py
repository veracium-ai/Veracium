"""Host/admin query conveniences: list_entities() and edges_since()."""

import json
import sqlite3
import tempfile
from datetime import datetime, timezone

import pytest

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium.store.sqlite import SqliteStore


class Fake:
    def __init__(self):
        self._i = 0
        self.scripts = [
            {"triples": [{"subject": "user", "relation": "uses_tool", "object": "invoices portal",
                          "volatility": "durable"}],
             "episode": "Vendor sent an invoice via the portal."},
            {"triples": [{"subject": "user", "relation": "uses_tool", "object": "wire transfer",
                          "volatility": "durable"}],
             "episode": "Vendor asked to switch to wire transfer."},
            {"triples": [], "episode": "Newsletter received."},
        ]

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            out = self.scripts[self._i]; self._i += 1
            return json.dumps(out)
        return ""


def test_list_entities_counts_per_user():
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",  # 0006 v8: opted out — measures records that exist (rule 8 / I3 / I13), not the ingest requirement
                                                     wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:acme", "wire", date="2026-07-10",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:globex", "newsletter", date="2026-07-05",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        ents = mem.list_entities()
        assert [e["user_id"] for e in ents] == ["vendor:acme", "vendor:globex"]
        acme = ents[0]
        assert acme["edges"] == 2 and acme["episodes"] == 2
        assert ents[1]["edges"] == 0 and ents[1]["episodes"] == 1  # empty triples
        mem.close()



def test_edges_since_means_learned_not_occurred():
    """`edges_since` returns the edges Veracium LEARNED after `since` (its docstring, docs/api.md, docs/recipes.md), not
    the ones whose event happened after it. Event time and learned time are pulled apart: two events dated in 2025 and
    2024 are remembered on a controlled store clock on 2026-07-01 and 2026-07-10. The superseded test above cannot tell
    the two meanings apart, because its event dates and remember dates coincide (0049 §1)."""
    with tempfile.TemporaryDirectory() as d:
        now = {"t": datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)}
        store = SqliteStore(f"{d}/t.db", clock=lambda: now["t"])
        mem = Memory(llm=Fake(), store=store,
                     config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",  # 0006 v8: opted out, as above
                                         wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2025-03-01",            # learned 2026-07-01, happened 2025
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        now["t"] = datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)
        mem.remember("vendor:acme", "wire", date="2024-11-15",               # learned 2026-07-10, happened 2024
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")

        recent = mem.edges_since("vendor:acme", "2026-07-05")
        assert [e.object for e in recent] == ["wire transfer"], [e.object for e in recent]
        assert mem.edges_since("vendor:acme", "2026-07-11") == []
        assert len(mem.edges_since("vendor:acme", "2026-06-01")) == 2
        assert mem.edges_since("vendor:acme", "2026-01-01") != []    # an event-time filter would also return both here
        mem.close()


def test_edges_since_refuses_a_store_without_a_journal():
    """specs/0049 E2: a store that keeps no transaction-time journal cannot say when an edge was learned, so
    `edges_since` REFUSES rather than answer from event time. The base `Store` answers `None` (it keeps none)."""
    from veracium.store.base import Store
    assert Store.first_recorded_at(None, "vendor:acme") is None

    class NoJournal(SqliteStore):
        def first_recorded_at(self, user_id):
            return None

    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), store=NoJournal(f"{d}/t.db"),
                     config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                         wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        with pytest.raises(NotImplementedError, match="transaction-time journal"):
            mem.edges_since("vendor:acme", "2026-06-01")
        mem.close()


def test_edges_since_refuses_an_edge_without_a_journal_event():
    """specs/0049 §4 step 4: an edge the journal has no event for has an unknown learned time; it is refused by
    name, never guessed and never silently dropped."""
    class Forgetful(SqliteStore):
        def first_recorded_at(self, user_id):
            return {}

    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), store=Forgetful(f"{d}/t.db"),
                     config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                         wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        with pytest.raises(ValueError, match="has no journal event"):
            mem.edges_since("vendor:acme", "2026-06-01")
        mem.close()


NAME = "first_recorded_at"


def _references(sources: dict) -> list:
    """specs/0049 E4a: EVERY static reference to `first_recorded_at` in the package, by its enclosing
    function's qualified name, from the parsed source (never a spelling match): an attribute access in any form (a
    call, an alias, a partial, a lambda, a class-level `SqliteStore.first_recorded_at`), a bare name, a constant
    string anywhere (`getattr(x, "first_recorded_at")`, `operator.attrgetter`), and a definition of the name (an
    override). LIMITS, stated: a COMPUTED name (`getattr(x, "first_" + s)`) is invisible to a parser, and a reader that
    re-queries edge_event's recorded_at WITHOUT this method is 0029's V-INERT inventory's subject, not this one's."""
    import ast
    out = []
    for rel, text in sorted(sources.items()):
        tree = ast.parse(text)

        def walk(node, scope):
            for child in ast.iter_child_nodes(node):
                inner = scope
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    inner = f"{scope}.{child.name}" if scope else child.name
                    if child.name == NAME and not isinstance(child, ast.ClassDef):
                        out.append((rel, inner, "def"))
                if isinstance(child, ast.Attribute) and child.attr == NAME:
                    out.append((rel, scope or "<module>", "attribute"))
                elif isinstance(child, ast.Name) and child.id == NAME:
                    out.append((rel, scope or "<module>", "name"))
                elif isinstance(child, ast.Constant) and child.value == NAME:
                    out.append((rel, scope or "<module>", "string"))
                walk(child, inner)
        walk(tree, "")
    return sorted(set(out))


def _package_sources():
    """EVERY module of the package, the store included (research's stage 2, SF1: a store method under another name
    that returns the timestamps is a second reader as surely as one outside the store)."""
    from pathlib import Path
    import veracium
    src = Path(veracium.__file__).parent
    return {str(py.relative_to(src)): py.read_text() for py in src.rglob("*.py")}


# the one sanctioned shape: the two definitions (the base Store's default, SqliteStore's query) and ONE reader
ALLOWED = [("__init__.py", "Memory.edges_since", "attribute"),
           ("store/base.py", "Store.first_recorded_at", "def"),
           ("store/sqlite.py", "SqliteStore.first_recorded_at", "def")]


def test_journal_timestamps_reach_only_edges_since_and_carry_no_content():
    """specs/0049 E4a, the amendment to 0029 V-INERT: across the WHOLE package, `first_recorded_at` is defined twice
    (the base Store's default, SqliteStore's query) and referenced ONLY by `Memory.edges_since`, as one attribute
    access, over EVERY static reference form (the parser inventory above; round 1's R1-02 named two forms a grep could
    not see, and research's stage 2 a store method handing the map on). Its value is `{edge_id: recorded_at}`, every value a
    tz-aware ISO timestamp, never a journal `state` (JSON), reason or kind, for exactly the user's edges."""
    assert _references(_package_sources()) == ALLOWED
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                                     wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        mem.remember("vendor:globex", "wire", date="2026-07-02",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        first = mem.store.first_recorded_at("vendor:acme")
        assert first and all(isinstance(k, str) and isinstance(v, str) for k, v in first.items())
        for v in first.values():                 # a timestamp, not a payload: the journal `state` is JSON
            assert datetime.fromisoformat(v).tzinfo is not None, v
        assert set(first) == {e.id for e in mem.store.edges("vendor:acme", active_only=False,
                                                              include_quarantined=True)}
        assert not set(first) & set(mem.store.first_recorded_at("vendor:globex"))      # two users, two maps
        mem.close()


# E4a's negative controls: each form a second reader could take, planted in a copy of __init__.py's source, must
# appear in the inventory (round 1's two survivors first, then the rest of the class, research's stage 1 included)
_PLANTED = {
    "a space before the call (R1-02)": "def _peek(self, u):\n    return self.store.first_recorded_at (u)\n",
    "an attribute alias (R1-02)": "def _peek(self, u):\n    read = self.store.first_recorded_at\n    return read(u)\n",
    "getattr with a constant string": "def _peek(self, u):\n    return getattr(self.store, 'first_recorded_at')(u)\n",
    "a class-level reference": "def _peek(self, u):\n    return SqliteStore.first_recorded_at(self.store, u)\n",
    "functools.partial": "def _peek(self, u):\n    import functools\n    return functools.partial(self.store.first_recorded_at, u)()\n",
    "a lambda wrapper": "_peek = lambda self, u: self.store.first_recorded_at(u)\n",
    "operator.attrgetter": "def _peek(self, u):\n    import operator\n    return operator.attrgetter('first_recorded_at')(self.store)(u)\n",
    "a module-level helper": "def _helper(store, u):\n    return store.first_recorded_at(u)\n",
    "an override outside the store": "class Peek:\n    def first_recorded_at(self, u):\n        return {}\n",
}
# research's stage-2 S5, planted IN the store: a method under another name handing the timestamps on
_PLANTED_STORE = "    def learned_map(self, user_id):\n        return self.first_recorded_at(user_id)\n"


@pytest.mark.parametrize("form", sorted(_PLANTED))
def test_the_reference_inventory_sees_every_static_form(form):
    sources = _package_sources()
    base = _references(sources)
    sources["__init__.py"] = sources["__init__.py"] + "\n\n" + _PLANTED[form]
    assert _references(sources) != base, form


def test_the_inventory_sees_a_store_method_handing_the_timestamps_on():
    """Research's stage-2 S5: a SqliteStore method under another name returning first_recorded_at is a second
    reader; the package-wide inventory sees it (SqliteStore.learned_map)."""
    sources = _package_sources()
    text = sources["store/sqlite.py"]
    anchor = "    def first_recorded_at(self, user_id: str) -> dict:\n"
    assert text.count(anchor) == 1
    sources["store/sqlite.py"] = text.replace(anchor, _PLANTED_STORE + "\n" + anchor)
    assert ("store/sqlite.py", "SqliteStore.learned_map", "attribute") in _references(sources)
    assert _references(sources) != ALLOWED


def test_the_inventory_limit_is_a_computed_name():
    """The stated limit, as a cell: a name computed at run time is NOT seen (the inventory claims static references
    only, constant-string getattr included)."""
    sources = _package_sources()
    base = _references(sources)
    sources["__init__.py"] += "\n\ndef _peek(self, u):\n    return getattr(self.store, 'first_' + 'recorded_at')(u)\n"
    assert _references(sources) == base


EDGE_EVENT_READABLE = {"user_id", "edge_id", "seq", "recorded_at"}


def _authorize(conn, seen, denied):
    def auth(action, arg1, arg2, dbname, source):
        if action == sqlite3.SQLITE_READ and arg1 == "edge_event":
            seen.add(arg2)
            if arg2 not in EDGE_EVENT_READABLE:
                denied.append(arg2)
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    conn.set_authorizer(auth)


def test_edges_since_loads_no_journal_payload_column():
    """specs/0049 E4b, 'no payload LOADED' (distinct from E4a's 'none returned'): a SQLite authorizer on the store's
    own connection, installed for the whole call, refuses any read of an `edge_event` column outside {user_id,
    edge_id, seq, recorded_at} (the filter, the order and the two returned columns). POSITIVE CONTROL: it SAW
    recorded_at read, so it was on the connection the query ran on. Mutant: a payload column selected and discarded."""
    with tempfile.TemporaryDirectory() as d:
        mem = Memory(llm=Fake(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                                     wiki_recompile_after_writes=0))
        mem.remember("vendor:acme", "invoice", date="2026-07-01",
                     author=EvidenceAuthor.THIRD_PARTY, event_type="email")
        seen, denied = set(), []
        _authorize(mem.store._conn, seen, denied)
        try:
            try:
                mem.edges_since("vendor:acme", "2020-01-01")
                raised = None
            except sqlite3.DatabaseError as exc:
                raised = str(exc)
        finally:
            mem.store._conn.set_authorizer(None)
        assert denied == [] and raised is None, (denied, raised)
        assert "recorded_at" in seen and seen <= EDGE_EVENT_READABLE, seen
        mem.close()


@pytest.mark.parametrize("query", [
    "SELECT * FROM edge_event WHERE user_id=?",
    "SELECT e.edge_id, e.recorded_at, e.state FROM edge_event e WHERE e.user_id=?",
    "SELECT edge_id, recorded_at FROM edge_event WHERE user_id=? AND kind IN ('created')",
    "SELECT edge_id, (SELECT state FROM edge_event x WHERE x.seq = edge_event.seq) FROM edge_event WHERE user_id=?",
    "WITH j AS (SELECT edge_id, reason FROM edge_event WHERE user_id=?) SELECT edge_id FROM j",
    "SELECT ev.edge_id FROM edge_event ev JOIN edges ed ON ed.id = ev.edge_id WHERE ev.user_id=? AND ev.txn > 0",
])
def test_the_authorizer_refuses_every_query_shape_that_loads_a_payload_column(query):
    """E4b's controls: SELECT *, a qualified column, a filter on a payload column, a subquery, a CTE and a JOIN each
    reach a column outside the allowlist, and each is refused, so the authorizer cannot pass vacuously."""
    with tempfile.TemporaryDirectory() as d:
        store = SqliteStore(f"{d}/t.db")
        seen, denied = set(), []
        _authorize(store._conn, seen, denied)
        try:
            with pytest.raises(sqlite3.DatabaseError, match="prohibited|not authorized"):
                store._conn.execute(query, ("u",)).fetchall()
        finally:
            store._conn.set_authorizer(None)
        assert denied, query
