"""0018 adjacent rungs, T2: the target. `open_versioned`'s six rows (0007 §4h.1), the kernel at a target below head, and the walk over
every (base, target): a capture is read only after it is written, and only a `read` entry writes one. Still nothing below head in
production: T3's orchestrator is the first caller."""
from __future__ import annotations

import ast
import importlib.util
import inspect
import pathlib
import sqlite3
import sys
import textwrap

import pytest

import veracium.store.migration as M
from veracium.store import schema_version as sv

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEAD = sv.SCHEMA_VERSION
BASES = [b for b in sorted(sv.SCHEMAS) if b < HEAD]
PAIRS = [(b, t) for b in BASES for t in range(b + 1, HEAD + 1)]


def _store(path, version):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("BEGIN")
    sv.create(conn, version)
    conn.execute(f"PRAGMA user_version = {version}")
    conn.execute("COMMIT")
    return conn


def _hook(target):
    def older(conn, path, found, objs, base, runtime=None):
        M._apply_forward(conn, base, target)
    return older


@pytest.mark.parametrize("bad", [True, False, 3.0, "3", type("I", (int,), {})(3)], ids=["True", "False", "a float", "a str", "an int subclass"])
def test_a_target_of_the_wrong_type_refuses_before_the_store_is_touched(bad):
    conn = sqlite3.connect(":memory:")
    with pytest.raises(TypeError):
        sv.open_versioned(conn, ":memory:", migrate_to=bad)
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0


@pytest.mark.parametrize("bad", [0, sv.FIRST_MIGRATABLE, HEAD + 1, -1])
def test_a_target_out_of_range_refuses_before_the_store_is_touched(bad):
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError):
        sv.open_versioned(conn, ":memory:", migrate_to=bad, older=_hook(bad))
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0


def test_a_target_below_head_needs_the_hook():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(ValueError, match="a migration target below head requires the migration hook"):
        sv.open_versioned(conn, ":memory:", migrate_to=HEAD - 1)


def test_the_argument_is_checked_before_the_runtime_gate(monkeypatch):
    def gate():
        raise AssertionError("the runtime gate ran first")
    monkeypatch.setattr(sv, "runtime_status", gate)
    with pytest.raises(ValueError):
        sv.open_versioned(sqlite3.connect(":memory:"), ":memory:", migrate_to=HEAD + 1)


def _sql(conn):
    return sorted(r for r in conn.execute("SELECT type, name, sql FROM sqlite_master"))


@pytest.mark.parametrize("hook", [False, True], ids=["no hook", "with a hook"])
def test_head_as_the_target_is_none_in_every_respect(tmp_path, hook):
    older = _hook(HEAD) if hook else None
    a, b = _store(str(tmp_path / "a.db"), HEAD), _store(str(tmp_path / "b.db"), HEAD)
    ra = sv.open_versioned(a, str(tmp_path / "a.db"), older=older)
    rb = sv.open_versioned(b, str(tmp_path / "b.db"), older=older, migrate_to=HEAD)
    assert ra == rb and _sql(a) == _sql(b)


@pytest.mark.parametrize("t", [t for t in range(2, HEAD + 1)])
def test_one_rung_lands_on_an_accepted_shape_at_its_target(tmp_path, t):
    path = str(tmp_path / "s.db")
    conn = _store(path, t - 1)
    r = sv.open_versioned(conn, path, migrate_to=t, older=_hook(t), allow_adopt=False)
    assert r == "migrated" and r.resulting_version == t
    assert conn.execute("PRAGMA user_version").fetchone()[0] == t
    assert sv.digest(sv.manifest(conn), t) in sv.accepted_digests(t)


def test_the_runtime_gate_never_sees_the_target(tmp_path, monkeypatch):
    """Dev's model F1: patched so the target reached it, every below-head rung refused `unsupported-sqlite`. The gate reads the build."""
    seen = []
    real = sv.attestation_revision

    def revision(*a, **k):
        seen.append((a, k))
        return real(*a, **k)
    monkeypatch.setattr(sv, "attestation_revision", revision)
    path = str(tmp_path / "s.db")
    conn = _store(path, HEAD - 2)
    assert sv.open_versioned(conn, path, migrate_to=HEAD - 1, older=_hook(HEAD - 1), allow_adopt=False).resulting_version == HEAD - 1
    assert all(HEAD - 1 not in a and HEAD - 1 not in k.values() for a, k in seen), seen


def test_a_target_that_is_no_version_refuses_as_an_unsupported_base():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(sv.StoreVersionError, match="no migration path from base 1 to head 99"):
        M._apply_forward(conn, 1, 99)


def test_a_postcondition_names_the_rung_s_target(tmp_path):
    run = M._Forward(4, 9)
    with pytest.raises(M.MigrationPostconditionError) as ei:
        M._refuse_unless(run, M.STEP_WIKI, ["planted"])
    assert ei.value.expected == 9 and ei.value.found == 4


def test_a_capture_mistyped_fails_where_it_is_written():
    with pytest.raises(AttributeError):
        M._Forward(1, 2).episode_before = {}


def test_an_unknown_kind_refuses_in_the_dispatcher_as_well_as_the_gate(monkeypatch):
    monkeypatch.setattr(M, "plan", lambda b, t: [M.ForwardEntry(0, t, "sideways", None)])
    with pytest.raises(sv.StoreVersionError, match="unknown kind"):
        M._apply_forward(sqlite3.connect(":memory:"), 1, 2)


def test_sa10_s_text_classes_bind_the_target_and_not_the_head():
    """(b1) and (b2) move to `SCHEMAS[t]` (0018 §2a; I39): a head-only constructor is no class of a lower rung's."""
    spec = importlib.util.spec_from_file_location("veracium_sa10_gate_t2", ROOT / "specs/evidence/0013/sa10_gate.py")
    g = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = g
    spec.loader.exec_module(g)
    head = g.text_classes()
    low = g.text_classes(8)
    assert head == g.text_classes(HEAD)
    assert low[1] == {o.ddl for o in sv.SCHEMAS[8] if o.key[0] in ("table", "index")} and low[1] != head[1]
    only_head = {o.ddl for o in sv.SCHEMAS[HEAD] if o.key[0] == "table"} - {o.ddl for o in sv.SCHEMAS[8]}
    assert only_head and not (only_head & low[1])


# ---- the walk: captures move between entries now, so what a local guaranteed is checked ----------------------------------------

def _run_attributes(fn):
    """(attributes of `run` the function reads, attributes it stores), by its own AST and any helper called with `run`."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    reads, writes = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "run":
            (writes if isinstance(n.ctx, ast.Store) else reads).add(n.attr)
        if isinstance(n, ast.Call) and any(isinstance(a, ast.Name) and a.id == "run" for a in n.args):
            helper = getattr(M, getattr(n.func, "id", ""), None)
            if inspect.isfunction(helper) and helper is not M._refuse_unless:
                r, w = _run_attributes(helper)
                reads |= r
                writes |= w
    return reads, writes


@pytest.mark.parametrize("base, target", PAIRS)
def test_every_capture_is_written_before_it_is_read_at_every_base_and_target(base, target):
    have = {"base", "target", "conf_before", "red_before"}
    for e in M.plan(base, target):
        if e.kind == "clock":
            have |= {"now", "now_iso"}
        elif e.kind in ("read", "data", "check"):
            reads, writes = _run_attributes(e.step)
            assert reads <= have, (e.step.__name__, reads - have)
            have |= writes


def test_only_a_read_entry_stores_on_the_run():
    """A `before` capture used to be a local, so no step could overwrite the value its own check compares (research, 11f9329c)."""
    for e in M.FORWARD_ENTRIES:
        if e.kind in ("data", "check"):
            assert _run_attributes(e.step)[1] == set(), e.step.__name__
