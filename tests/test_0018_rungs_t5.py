"""0018 §4j's evidence (T5). I33: every rung from every base, over the release-authored fixtures. I36: a rung's digest names its plan,
and every operation executes exactly its plan, by the two units 0013 §5g.1 keeps apart. The trace needs no product hook: `_apply_forward`
iterates `plan(b, t)`, so a generator in its place sets the active entry as each one is dispatched, and an authorizer on the connection
classifies each write. SQLite's classification, never the statement's text."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import re
import shutil
import sqlite3
import tarfile

import pytest

import veracium.store.migration as mig
import veracium.store.release_migration as rm
import veracium.store.schema_version as sv

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNGS = ROOT / "specs" / "evidence" / "0018" / "rungs"
MANIFEST = json.loads((RUNGS / "manifest.json").read_text())
FIXTURES = [f["fixture"] for f in MANIFEST["fixtures"]]
HEAD = sv.SCHEMA_VERSION
ATTESTATION = rm.MigrationAttestation(quiesced=True, backup_ref="t5")
NOW = datetime.datetime(2026, 11, 6, 12, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture(scope="module")
def stores(tmp_path_factory):
    d = tmp_path_factory.mktemp("fixtures")
    with tarfile.open(RUNGS / "fixtures.tar.xz") as t:
        t.extractall(d, filter="data")
    return d


def _walk(path):
    """The CLI's loop over the real rung, to the head-level `current`. Returns each delegated report."""
    expect, reports = None, []
    for _ in range(HEAD + 1):
        rep = rm.run_release_rung(str(path), host_attestation=ATTESTATION, expect_base=expect)
        if rep.kind == "preflight":
            assert rep.result.outcome == "current", rep
            return reports
        assert rep.kind == "delegated" and rep.result.outcome == "migrated", rep
        reports.append(rep)
        expect = rep.to_version
    raise AssertionError("the walk did not reach head")


def _jump(path):
    """The direct route's outcome, a refusal included, so a direct route that stopped working reads as a wrong outcome."""
    try:
        return str(mig.migrate_store(str(path)))
    except (sv.StoreVersionError, mig.MigrationPostconditionError) as e:
        return f"refused: {e}"


def _content(path):
    """Every table's rows, sorted, with the uuid a migration mints as `store_identity.origin` read out of them: two operations mint two."""
    c = sqlite3.connect(path)
    try:
        origins = [r[0] for r in c.execute("SELECT origin FROM store_identity")] if c.execute(
            "SELECT 1 FROM sqlite_master WHERE name='store_identity'").fetchone() else []
        out = {}
        for (name,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT GLOB 'sqlite_*' ORDER BY name").fetchall():
            rows = []
            for row in c.execute(f'SELECT * FROM "{name}"').fetchall():
                text = repr(row)
                for o in origins:
                    text = text.replace(o, "<origin>")
                rows.append(text)
            out[name] = sorted(rows)
        return out
    finally:
        c.close()


@pytest.mark.parametrize("name", FIXTURES)
def test_every_rung_from_every_base(stores, tmp_path, monkeypatch, name):
    """I33 (ii): walked to head a rung at a time, each rung landing on a shape accepted at its target, and the rows equal the direct
    jump of the same fixture in every column. The clock is held, so a clock value is compared too: `test_each_rung_reads_its_own_clock`
    has the unheld case."""
    monkeypatch.setattr(mig, "_clock", lambda: NOW)
    walked, direct = tmp_path / "walked.db", tmp_path / "direct.db"
    shutil.copyfile(stores / name, walked)
    shutil.copyfile(stores / name, direct)
    base = next(f["base"] for f in MANIFEST["fixtures"] if f["fixture"] == name)
    reports = _walk(walked)
    assert [(r.from_version, r.to_version) for r in reports] == [(b, b + 1) for b in range(base, HEAD)]
    assert _jump(direct) == "migrated"
    a, b = _content(walked), _content(direct)
    assert sorted(a) == sorted(b)
    assert {t: (a[t], b[t]) for t in a if a[t] != b[t]} == {}


def _ticking_walk(path, monkeypatch):
    """A walk under a clock that moves on every read. Returns {target: that rung's reads, isoformat}."""
    reads = []

    def tick():
        reads.append(NOW + datetime.timedelta(hours=len(reads) + 1))
        return reads[-1]
    monkeypatch.setattr(mig, "_clock", tick)
    expect, per_rung = None, {}
    for _ in range(HEAD + 1):
        before = len(reads)
        rep = rm.run_release_rung(str(path), host_attestation=ATTESTATION, expect_base=expect)
        if rep.kind == "preflight":
            return per_rung
        assert rep.result.outcome == "migrated", rep
        per_rung[rep.to_version] = [r.isoformat() for r in reads[before:]]
        expect = rep.to_version
    raise AssertionError("the walk did not reach head")


CLOCK_FIXTURE = next(f["fixture"] for f in MANIFEST["fixtures"] if f["base"] <= 12 and f["rows"].get("confirmations") and f["rows"].get("edges"))


@pytest.mark.parametrize("column, query, rung", [
    ("store_epoch.started_at", "SELECT started_at FROM store_epoch", 13),
    ("edge_event.recorded_at", "SELECT recorded_at FROM edge_event", 13),
    ("request_registry.written_at", "SELECT written_at FROM request_registry", 16),
    ("arity_era.effective_at", "SELECT effective_at FROM arity_era", 16),
], ids=["started_at", "recorded_at", "written_at", "effective_at"])
def test_each_declared_clock_value_is_its_own_rung_s_read(stores, tmp_path, monkeypatch, column, query, rung):
    """§4j.10: each per-rung clock value comes from its own rung's clock read, column by column: equality with that rung's read, so a
    walk that reused one read for every rung fails here. Each rung reads once."""
    p = tmp_path / "s.db"
    shutil.copyfile(stores / CLOCK_FIXTURE, p)
    per_rung = _ticking_walk(p, monkeypatch)
    assert all(len(v) == 1 for v in per_rung.values()), per_rung
    c = sqlite3.connect(p)
    values = {r[0] for r in c.execute(query).fetchall()}
    c.close()
    assert values == set(per_rung[rung]), (column, values, per_rung[rung])


def test_the_v3_observed_at_fill_is_rung_three_s_read(tmp_path, monkeypatch):
    """The v2→v3 fill, which no release-authored fixture reaches: every outcome episode a release wrote already carries `observed_at`.
    So this legacy row is hand-made, as the README says, and the value it receives is rung 3's read."""
    p = tmp_path / "s.db"
    _store_at(p, 2)
    c = sqlite3.connect(p)
    ep = {"id": "ep", "user_id": "u", "date": "2026-01-01", "summary": "s", "kind": "outcome", "edge_id": "e", "outcome": "concurred",
          "provenance": {"author_of_evidence": "user", "evidence_ref": "r", "source_type": "user_stated"}}
    c.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)", ("ep", "u", "2026-01-01", json.dumps(ep)))
    c.commit()
    c.close()
    per_rung = _ticking_walk(p, monkeypatch)
    c = sqlite3.connect(p)
    got = json.loads(c.execute("SELECT json FROM episodes WHERE id='ep'").fetchone()[0])["provenance"]["observed_at"]
    c.close()
    assert len(per_rung[3]) == 1 and mig._same_instant(got, datetime.datetime.fromisoformat(per_rung[3][0])), (got, per_rung[3])


# ---- I36 ---------------------------------------------------------------------------------------------------------------
class _Trace:
    """Unit 1: the entries dispatched, in order. Unit 2: each write, with the entry active when SQLite prepared it."""

    def __init__(self, monkeypatch):
        self.entries, self.writes, self.executed, self.active, self.inside = [], [], [], None, False
        real_plan, real_apply = mig.plan, mig._apply_forward

        def dispatched(b, t):
            for e in real_plan(b, t):
                self.active = e
                self.entries.append(e)
                yield e
            self.active = None

        def plan(b, t):                            # the mint's digest reads the plan too: only the dispatcher's read is a trace
            return dispatched(b, t) if self.inside else real_plan(b, t)

        def apply_forward(conn, base, target=HEAD):
            conn.set_authorizer(self._authorize)     # once per PREPARE, so it classifies a statement
            conn.set_trace_callback(lambda sql: self.executed.append((self.active, sql)))   # once per RUN, so it counts one
            self.inside = True
            try:
                return real_apply(conn, base, target)
            finally:
                self.inside = False
                conn.set_authorizer(None)
                conn.set_trace_callback(None)
        monkeypatch.setattr(mig, "plan", plan)
        monkeypatch.setattr(mig, "_apply_forward", apply_forward)
        self.real_plan = real_plan

    def _authorize(self, code, a, b, db, trigger):
        if self.inside:
            self.writes.append((self.active, code, a, b))
        return sqlite3.SQLITE_OK


_DML = (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE)
_DDL = {sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE,
        sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_VIEW}


def _system(table):
    return table is not None and table.startswith("sqlite_")


def _attribution_problems(trace):
    """0013 §5g.1 unit 2, as SQLite's authorizer classifies each statement. What an ALTER or a CREATE does to `sqlite_master` belongs to it."""
    bad = []
    per = {}
    for entry, code, a, b in trace.writes:
        is_ddl = code in _DDL and not _system(a)          # an `sqlite_autoindex_*` is part of its CREATE TABLE
        is_dml = code in _DML and not _system(a)
        is_stamp = code == sqlite3.SQLITE_PRAGMA and a == "user_version" and b is not None
        if not (is_ddl or is_dml or is_stamp):
            continue
        if entry is None:
            bad.append(f"a write with no active entry: {code} {a} {b}")
            continue
        per.setdefault(id(entry), [entry, []])[1].append((code, a, b))
        kind = entry.kind
        if (kind == "add" and code not in (sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX)) \
                or (kind == "alter" and code != sqlite3.SQLITE_ALTER_TABLE) or (kind == "data" and not is_dml) \
                or kind in ("read", "check", "clock") or (kind == "stamp" and not is_stamp):
            bad.append(f"a {kind} entry issued {code} {a} {b}")
    for entry, seen in per.values():
        if entry.kind in ("add", "alter", "stamp") and len(seen) != 1:
            bad.append(f"a {entry.kind} entry issued {len(seen)} writes: {seen}")
        if entry.kind == "add" and seen[0][1] != entry.step.key[1]:
            bad.append(f"an add of {entry.step.key[1]} wrote {seen[0][1]}")
        if entry.kind == "alter" and f"ALTER TABLE {seen[0][2]} " not in entry.step:
            bad.append(f"an alter of another table: {seen[0]} under {entry.step}")
        if entry.kind == "stamp" and str(seen[0][2]) != str(entry.step):
            bad.append(f"a stamp of {seen[0][2]} under {entry.step}")
    return bad


def _store_at(path, version):
    c = sqlite3.connect(path)
    for o in sv.SCHEMAS[version]:
        c.execute(o.ddl)
    c.execute(f"PRAGMA user_version = {version}")
    c.commit()
    c.close()


def _same_plan(trace, b, t):
    return [(e.kind, e.step) for e in trace.entries] == [(e.kind, e.step) for e in trace.real_plan(b, t)]


@pytest.mark.parametrize("name", FIXTURES[::7])
def test_a_rung_executes_exactly_its_plan_and_every_write_is_its_entry_s(stores, tmp_path, monkeypatch, name):
    """Units 1 and 2 on release-authored fixtures, one rung at a time, every base from the fixture's up."""
    p = tmp_path / "s.db"
    shutil.copyfile(stores / name, p)
    base = next(f["base"] for f in MANIFEST["fixtures"] if f["fixture"] == name)
    trace = _Trace(monkeypatch)
    for b in range(base, HEAD):
        trace.entries.clear()
        trace.writes.clear()
        rep = rm.run_release_rung(str(p), host_attestation=ATTESTATION, expect_base=b)
        assert rep.result.outcome == "migrated", rep
        assert _same_plan(trace, b, b + 1), b
        assert _attribution_problems(trace) == []


@pytest.mark.parametrize("base", [1, 13])
def test_the_direct_route_executes_its_own_plan_with_one_clock_and_one_stamp(tmp_path, monkeypatch, base):
    """I36 (iv): `migrate_store` keeps its contract: the destination constructors, one clock read, one stamp. It is not the concatenation
    of the adjacent plans, which would read the clock and stamp once per rung."""
    p = tmp_path / "s.db"
    _store_at(p, base)
    trace = _Trace(monkeypatch)
    reads, clock = [], mig._clock
    monkeypatch.setattr(mig, "_clock", lambda: (reads.append(1), clock())[1])
    assert str(mig.migrate_store(str(p))) == "migrated"
    assert _same_plan(trace, base, HEAD) and len(reads) == 1          # a dispatch the plan does not hold reads the clock again
    kinds = [e.kind for e in trace.entries]
    assert kinds.count("clock") == 1 and kinds.count("stamp") == 1 and _attribution_problems(trace) == []


@pytest.mark.parametrize("rows", [0, 1, 2])
def test_a_data_entry_issues_zero_or_more_writes_on_a_v2_fixture(tmp_path, monkeypatch, rows):
    """I36 (iii): an empty store cannot exercise a data write, so `UPDATE episodes` is counted at 0, 1 and 2 legacy outcome rows."""
    p = tmp_path / "s.db"
    _store_at(p, 2)
    c = sqlite3.connect(p)
    for i in range(rows):
        ep = {"id": f"ep{i}", "user_id": "u", "date": "2026-01-01", "summary": "s", "kind": "outcome", "edge_id": f"e{i}", "outcome": "concurred",
              "provenance": {"author_of_evidence": "user", "evidence_ref": f"r{i}", "source_type": "user_stated"}}
        c.execute("INSERT INTO episodes(id,user_id,date,json) VALUES(?,?,?,?)", (f"ep{i}", "u", "2026-01-01", json.dumps(ep)))
    c.commit()
    c.close()
    trace = _Trace(monkeypatch)
    rep = rm.run_release_rung(str(p), host_attestation=ATTESTATION)
    assert rep.result.outcome == "migrated", rep
    data = [sql for entry, sql in trace.executed if entry is not None and entry.kind == "data" and sql.startswith("UPDATE episodes")]
    assert len(data) == rows and _attribution_problems(trace) == []


def test_a_refused_operation_s_trace_is_a_prefix_ending_at_the_refusing_entry(tmp_path, monkeypatch):
    """Unit 1, refused: the trace stops at the entry that refused, and the transaction rolls back."""
    p = tmp_path / "s.db"
    _store_at(p, 13)
    trace = _Trace(monkeypatch)
    monkeypatch.setattr(mig, "_check_stamp", lambda conn, run: mig._refuse_unless(run, mig.STEP_STAMP, ["injected"]))
    rep = rm.run_release_rung(str(p), host_attestation=ATTESTATION)
    assert rep.result.outcome == "unsupported-migration", rep
    want = [(e.kind, e.step) for e in trace.real_plan(13, 14)]
    got = [(e.kind, e.step) for e in trace.entries]
    assert got == want[:len(got)] and got[-1][0] == "check" and len(got) == len(want)
    c = sqlite3.connect(p)
    assert c.execute("PRAGMA user_version").fetchone()[0] == 13
    c.close()


def test_each_rung_s_digest_is_its_vector():
    """I36 (i): the preimages are frozen by the vector file, so a change to a plan, a constructor or the grammar moves a digest here."""
    vectors = json.loads((RUNGS / "digest_vectors.json").read_text())
    assert sorted(vectors["rungs"], key=int) == [str(b) for b in range(1, HEAD)]
    for b, v in vectors["rungs"].items():
        b = int(b)
        pre = mig.plan_preimage(b, b + 1)
        assert pre.hex() == v["preimage"], b
        assert hashlib.sha256(pre).hexdigest() == v["digest"] == rm._declared_migration_digest(b, b + 1), b
        assert [[e.kind, *map(str, mig.preimage_fields(e))] for e in mig.plan(b, b + 1)] == v["entries"], b


def test_the_direct_plans_keep_their_order():
    """A guard keeps steps of two different rungs out of every rung's plan, so only a direct plan orders them: `plan(1, HEAD)` runs v3's
    data step before v4's, and no rung's digest says so."""
    vectors = json.loads((RUNGS / "digest_vectors.json").read_text())
    assert vectors["direct"], vectors.keys()
    for b, want in vectors["direct"].items():
        assert [[e.kind, *map(str, mig.preimage_fields(e))] for e in mig.plan(int(b), HEAD)] == want, b


@pytest.mark.parametrize("name, t", [("ALTER_PATH_V6_SQL", 6), ("ALTER_PATH_V8_SQL", 8), ("ALTER_PATH_V10_FROM_CONSTRUCTOR_SQL", 10),
                                     ("ALTER_PATH_V16_CONFIRMATIONS_SQL", 16), ("ALTER_PATH_V16_REDACTIONS_SQL", 16)])
def test_a_mismatched_alter_output_reports_the_rung_s_target(tmp_path, monkeypatch, name, t):
    """I33 (iii): each frozen ALTER-output expectation, mismatched, reports the rung's target and never the head."""
    p = tmp_path / "s.db"
    _store_at(p, t - 1)
    monkeypatch.setattr(mig if hasattr(mig, name) else sv, name, "not the frozen text")
    c = sqlite3.connect(p)
    with pytest.raises(sv.StoreVersionError) as e:
        c.execute("BEGIN")
        mig._apply_forward(c, t - 1, t)
    c.close()
    assert e.value.expected == t, str(e.value)
