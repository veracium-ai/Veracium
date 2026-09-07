"""specs/0029 v11 §4a — V-LOCK-REFUSAL-FORM: a `database is locked` condition arising in a
transaction `_write_txn` OPENED is refused in ONE form at either lock site — the wrapped,
spec-citing refusal naming which site failed — never bare SQLite text. Postconditions on
refusal: (a) the exception names the lock site; (b) no part of the batch is applied;
(c) `in_transaction` is False and the connection is reusable.

The rule that makes the covered set non-empty BY CONSTRUCTION: `_write_txn` OWNS the commit
of every transaction it opens; no body issues its own. Before v11, all six write bodies
committed themselves, so `_write_txn`'s commit at its else-branch was DEAD on every shipped
path and the measured failure raised from `add_edge`'s own `self._conn.commit()` — the
census node below has TODAY'S CODE (before this commit) as its mutant. The residue — the
`.commit()` sites on paths that do not open through `_write_txn` — is censused, not counted,
and named in the spec; whether 0007 obliges it is the open cross-spec item.

Timing-tolerant: no assertion compares a duration to a constant.
"""
from __future__ import annotations

import ast
import contextlib
import pathlib
import sqlite3
import threading
import time

import pytest

from veracium.schema import Edge, EvidenceAuthor, Provenance
from veracium.store import sqlite as sqlite_mod
from veracium.store.sqlite import SqliteStore

ROOT = pathlib.Path(__file__).resolve().parent.parent
SQLITE_PY = ROOT / "src" / "veracium" / "store" / "sqlite.py"
U = "u-lock"


def _edge(i):
    return Edge(id=f"e-{i}", user_id=U, subject="user", relation="uses_tool", object=f"tool-{i}",
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=f"lock:{i}"))


def _hold_window(store, seconds, out):
    """current_state's window shape: BEGIN under the lock, a read, hold, COMMIT."""
    conn = store._conn
    with store._lock:
        conn.execute("BEGIN")
        out["opened"] = time.perf_counter()
        conn.execute("SELECT count(*) FROM edges WHERE user_id=?", (U,)).fetchone()
        time.sleep(seconds)
        conn.execute("COMMIT")
        out["closed"] = time.perf_counter()


def _commit_time_failure(tmp_path, *, writer_timeout_ms=500, window_s=2.0, write=None):
    """The measured case (0028's transcript, reproduced by the reviewer): a reader window
    outlives the writer's busy_timeout under the default (rollback) journal, so the
    writer's COMMIT — not its BEGIN — meets the lock. Returns (writer, error, window, t)."""
    path = str(tmp_path / "s.db")
    reader = SqliteStore(path); writer = SqliteStore(path, busy_timeout_ms=writer_timeout_ms)
    assert reader._conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    writer.add_edge(_edge("seed"))
    res = {}
    th = threading.Thread(target=_hold_window, args=(reader, window_s, res)); th.start()
    time.sleep(0.2)
    err = None
    try:
        (write or (lambda w: w.add_edge(_edge("during"))))(writer)
    except Exception as e:  # noqa: BLE001 — the exception IS the observation
        err = e
    finished = time.perf_counter()
    th.join(); reader.close()
    return writer, err, res, finished


# ------------------------------------------------------------------ the form
def test_commit_time_lock_refusal_has_the_begin_time_form(tmp_path):
    """(a) the COMMIT-time refusal is the wrapped, spec-citing form naming the site,
    the SAME exception type as the BEGIN-time refusal, SQLite's bare text kept as
    the cause — and it arrives while the window is still open."""
    writer, err, res, finished = _commit_time_failure(tmp_path)
    try:
        assert isinstance(err, sqlite3.OperationalError), err
        msg = str(err)
        assert "COMMIT" in msg and "V-LOCK-REFUSAL-FORM" in msg and "0029" in msg, msg
        assert isinstance(err.__cause__, sqlite3.OperationalError) and "database is locked" in str(err.__cause__)
        assert finished < res["closed"], "the refusal came while the reader's window was still open"
    finally:
        writer.close()


def test_the_store_is_unchanged_and_the_next_write_lands(tmp_path):
    """(b) no part of the batch is applied; (c) the connection is reusable — the
    next write lands and a third connection sees exactly seed + after."""
    writer, err, _, _ = _commit_time_failure(tmp_path)
    try:
        assert err is not None
        assert [e.id for e in writer.edges(U, active_only=False, include_quarantined=True)] == ["e-seed"]
        assert not writer._conn.in_transaction
        writer.add_edge(_edge("after"))
        third = sqlite3.connect(str(tmp_path / "s.db"))
        assert sorted(r[0] for r in third.execute("SELECT id FROM edges")) == ["e-after", "e-seed"]
        third.close()
    finally:
        writer.close()


def test_the_begin_time_refusal_is_unchanged(tmp_path):
    """The CONTROL that the change reached only the other site: a holder with
    RESERVED (BEGIN IMMEDIATE, uncommitted) makes the writer's BEGIN IMMEDIATE
    fail after its busy_timeout — the BEGIN-time form, unchanged."""
    path = str(tmp_path / "s.db")
    holder = SqliteStore(path); writer = SqliteStore(path, busy_timeout_ms=300)
    try:
        holder._conn.execute("BEGIN IMMEDIATE")
        with pytest.raises(sqlite3.OperationalError) as ei:
            writer.add_edge(_edge("x"))
        assert "could not take the write lock" in str(ei.value), str(ei.value)
        assert "COMMIT" not in str(ei.value).split("(")[0]
        assert not writer._conn.in_transaction
    finally:
        with contextlib.suppress(sqlite3.OperationalError):
            holder._conn.execute("ROLLBACK")
        holder.close(); writer.close()


# ---------------------------------------------------- the construction rule
def _in_body_commits(src: str):
    tree = ast.parse(src); hits = []
    for w in [n for n in ast.walk(tree) if isinstance(n, ast.With)
              and any(isinstance(i.context_expr, ast.Call) and getattr(i.context_expr.func, "attr", "") == "_write_txn" for i in n.items)]:
        hits += [n.lineno for n in ast.walk(w) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "commit"]
    return hits


def test_no_write_txn_body_issues_its_own_commit():
    """`_write_txn` OWNS the commit of every transaction it opens: an AST walk over
    every `with … self._write_txn()` block finds ZERO `.commit()` calls inside. The
    MUTANT is the code that shipped before this commit — six bodies committing
    themselves, which left `_write_txn`'s commit dead on every path. The residue is
    censused and printed: every `.commit()` on paths that do not open through
    `_write_txn` (named in the spec; 0007's obligation over it is the open item)."""
    src = SQLITE_PY.read_text()
    assert _in_body_commits(src) == [], _in_body_commits(src)
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_write_txn")
    own = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "commit"]
    assert len(own) == 1, "exactly one commit is _write_txn's own"
    assert "V-LOCK-REFUSAL-FORM" in ast.get_source_segment(src, fn)
    sites = [i + 1 for i, l in enumerate(src.splitlines()) if "self._write_txn()" in l and "def " not in l]
    here = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "commit") - 1
    elsewhere = sum(1 for p in (ROOT / "src" / "veracium").rglob("*.py") if p != SQLITE_PY
                    for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "commit")
    print(f"\ncovered: _write_txn's own commit, reached from {len(sites)} call site(s) at {sites}; residue: {here} in sqlite.py + {elsewhere} elsewhere = {here + elsewhere}")
    # the mutant, on a COPY of the source: one in-body commit reintroduced is detected
    mutant = src.replace("            self._upsert_edge_row(edge)\n            self._bump(edge.user_id)\n",
                         "            self._upsert_edge_row(edge)\n            self._bump(edge.user_id)\n            self._conn.commit()\n", 1)
    assert mutant != src and len(_in_body_commits(mutant)) == 1, "the census must see a reintroduced in-body commit"


def test_a_failed_commit_never_returns_import_counts(tmp_path):
    """A `__exit__` that raises discards a pending return: `commit_outcome_import_plan`
    computes its counts before the commit, and if the COMMIT is refused the caller
    receives the refusal, never counts for a write that did not land. Pinned by
    driving the smallest write path (add_edge) through the measured failure and
    asserting no value came back — the property is `_write_txn`'s, shared by every
    body."""
    captured = {}
    def write(w):
        captured["ret"] = w.add_edge(_edge("during"))
    writer, err, _, _ = _commit_time_failure(tmp_path, write=write)
    try:
        assert isinstance(err, sqlite3.OperationalError) and "COMMIT" in str(err)
        assert "ret" not in captured, "a refused commit must not hand the caller a return value"
    finally:
        writer.close()


# ------------------------------------------------------------------ mutants
def _old_write_txn_factory(swallow: bool):
    """The pre-v11 shape: `_write_txn` with the commit UNWRAPPED (mutant 1), or a
    wrapper that SWALLOWS the commit-time lock (mutant 2). Both are planted on the
    class so the real measured failure exercises them."""
    @contextlib.contextmanager
    def _wt(self):
        with self._journal_scope():
            if self._conn.in_transaction:
                yield; return
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield
            except BaseException:
                if self._conn.in_transaction: self._conn.rollback()
                raise
            else:
                if self._conn.in_transaction:
                    if swallow:
                        try: self._conn.commit()
                        except sqlite3.OperationalError:
                            self._conn.rollback()      # swallowed: the caller hears nothing
                    else:
                        self._conn.commit()             # unwrapped: the bare text surfaces
    return _wt


def test_mutant_a_wrapper_at_begin_alone_shows_the_bare_text(tmp_path, monkeypatch):
    """MUTANT 1 — wrap the BEGIN only (the pre-v11 form of `_write_txn`): the
    measured failure surfaces as SQLite's bare text with no cause, which the form
    test refuses."""
    monkeypatch.setattr(sqlite_mod.SqliteStore, "_write_txn", _old_write_txn_factory(swallow=False))
    writer, err, _, _ = _commit_time_failure(tmp_path)
    try:
        assert isinstance(err, sqlite3.OperationalError)
        assert str(err) == "database is locked" and err.__cause__ is None, str(err)
    finally:
        writer.close()


def test_mutant_a_wrapper_that_swallows_is_refused_by_the_postconditions(tmp_path, monkeypatch):
    """MUTANT 2 — a wrapper that catches the commit-time lock and returns quietly:
    the caller hears nothing and the write is silently absent — the outcome
    postcondition (a) exists to refuse (no exception names a site)."""
    monkeypatch.setattr(sqlite_mod.SqliteStore, "_write_txn", _old_write_txn_factory(swallow=True))
    writer, err, _, _ = _commit_time_failure(tmp_path)
    try:
        assert err is None, "the mutant swallows — nothing is raised"
        assert [e.id for e in writer.edges(U, active_only=False, include_quarantined=True)] == ["e-seed"], "and the write is silently absent"
    finally:
        writer.close()
