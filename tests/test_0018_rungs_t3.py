"""0018 adjacent rungs, T3: one rung per call. The twelve rows of §4j.6.4e-ii, `RungReport`'s binding, `expect_base`, the walk from every
base, and the rung's open, which never creates and addresses exactly the file the mint observed."""
from __future__ import annotations

import hashlib
import os
import sqlite3

import pytest

import veracium.store.migration as M
from veracium.store import release_migration as rm
from veracium.store import schema_version as sv

HEAD = sv.SCHEMA_VERSION
ATT = rm.MigrationAttestation(quiesced=True, backup_ref="rungs")
BASES = list(range(1, HEAD))


def _store(path, version, stamp=None):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("BEGIN")
    sv.create(conn, version)
    conn.execute(f"PRAGMA user_version = {version if stamp is None else stamp}")
    conn.execute("COMMIT")
    conn.close()
    return str(path)


def _stamp(path):
    c = sqlite3.connect(path)
    try:
        return c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()


def _authority(path, base):
    """A real authority for `path`, minted while it stood at `base`: the store can then be changed under it."""
    resolved = rm.PreflightResolution(os.path.realpath(path), base, "0" * 64)
    return rm.mint_release_authority(path, ATT, resolved=resolved)


def _facts(result):
    return (result.store_changed, result.transaction_committed, result.resulting_state, result.resulting_version)


@pytest.mark.parametrize("base", BASES)
def test_row_1_a_rung_moves_one_version_and_binds_to_its_minted_endpoints(tmp_path, base):
    p = _store(tmp_path / "s.db", base)
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert (r.kind, r.from_version, r.to_version, r.preflight_base, r.source_stamp) == ("delegated", base, base + 1, base, base)
    assert r.result.outcome == "migrated" and _facts(r.result) == (True, True, "destination", base + 1)
    assert _stamp(p) == base + 1


def test_row_2_an_unstamped_legacy_store_takes_the_first_rung_and_is_stamped_there(tmp_path):
    p = _store(tmp_path / "s.db", 1, stamp=0)
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert (r.kind, r.from_version, r.to_version, r.source_stamp) == ("delegated", 1, 2, 0)
    assert r.result.outcome == "migrated" and _stamp(p) == 2


@pytest.mark.parametrize("base", BASES)
def test_the_walk_from_every_base_reaches_head_one_rung_at_a_time_then_reports_current(tmp_path, base):
    p = _store(tmp_path / "s.db", base)
    for b in range(base, HEAD):
        r = rm.run_release_rung(p, host_attestation=ATT, expect_base=b)
        assert (r.kind, r.from_version, r.to_version, r.result.outcome) == ("delegated", b, b + 1, "migrated")
    done = rm.run_release_rung(p, host_attestation=ATT)
    assert (done.kind, done.result.outcome, done.result.resulting_version) == ("preflight", "current", HEAD)
    c = sqlite3.connect(p)
    assert sv.digest(sv.manifest(c), HEAD) in sv.accepted_digests(HEAD)
    c.close()


def _run_authority(path, authority):
    return rm._delegate(os.path.realpath(path), authority)


RUNGS = (1, 13, 15)        # I38's rungs: the first, a middle one, and the last, where `t` is head and `migrate_to` is `None`'s equal


@pytest.fixture
def attempted(monkeypatch):
    """I38: the kernel's attempted event, which no refused rung may emit."""
    events, real = [], M._mig_event
    monkeypatch.setattr(M, "_mig_event", lambda kind, *a, **k: (events.append(kind), real(kind, *a, **k))[1])
    return events


@pytest.mark.parametrize("b", RUNGS)
def test_row_4_another_operation_reached_the_target_first(tmp_path, b):
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    assert rm.run_release_migration(p, host_attestation=ATT).outcome == "migrated"
    r = _run_authority(p, a)
    assert r.outcome == "current" and _facts(r) == (False, False, "destination", b + 1) and _stamp(p) == b + 1


@pytest.mark.parametrize("b, found", [(13, 11), (13, 12), (15, 13), (15, 14)],
                         ids=["middle two behind", "middle one behind", "last two behind", "last one behind"])
def test_row_7a_a_store_below_the_source_refuses_and_nothing_is_written(tmp_path, attempted, b, found):
    """Rung 1 has no store below its source. The last rung's cells are the ones a binding put on `migrate_to` would miss."""
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    _store(p, found)
    r = _run_authority(p, a)
    assert r.outcome == "migration-source-missing" and _facts(r) == (False, False, "unaccepted", None)
    assert f"observed v{found}" in r.diagnostic and _stamp(p) == found and "migration_attempted" not in attempted


@pytest.mark.parametrize("b, found", [(1, 3), (1, HEAD), (13, 15), (13, HEAD)], ids=["first above", "first at head", "middle above", "middle at head"])
def test_row_7b_a_store_above_the_target_is_newer_and_is_never_stepped_back(tmp_path, attempted, b, found):
    """The last rung's target is head, so nothing is above it: a store at it is row 4."""
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    _store(p, found)
    r = _run_authority(p, a)
    assert r.outcome == "newer" and _facts(r) == (False, False, "unaccepted", None)
    assert f"v{found} is newer than this rung's target v{b + 1}" in r.diagnostic and "install" not in r.diagnostic
    assert _stamp(p) == found and "migration_attempted" not in attempted


@pytest.mark.parametrize("b", [13, 15])
def test_row_8a_an_unstamped_store_resolving_elsewhere_refuses(tmp_path, attempted, b):
    """An unstamped store resolves to v1, so at rung 1 it is the source, not row 8a."""
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    _store(p, 1, stamp=0)
    r = _run_authority(p, a)
    assert r.outcome == "migration-source-missing" and _facts(r) == (False, False, "unaccepted", None) and _stamp(p) == 0
    assert "migration_attempted" not in attempted


@pytest.mark.parametrize("b", RUNGS)
def test_row_9_an_unstamped_foreign_store_refuses(tmp_path, b):
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE foreign_thing (x)")
    c.close()
    r = _run_authority(p, a)
    assert r.outcome == "foreign-shape" and _facts(r) == (False, False, "unaccepted", None)


@pytest.mark.parametrize("b", RUNGS)
def test_row_10_an_empty_replacement_is_never_created_into(tmp_path, attempted, b):
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    sqlite3.connect(p).close()
    r = _run_authority(p, a)
    assert r.outcome == "migration-source-missing" and _facts(r) == (False, False, "unaccepted", None)
    c = sqlite3.connect(p)
    assert c.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 0
    c.close()
    assert "migration_attempted" not in attempted


@pytest.mark.parametrize("b", RUNGS)
def test_row_11a_nothing_at_the_path_is_refused_and_nothing_appears(tmp_path, attempted, b):
    p = _store(tmp_path / "s.db", b)
    a = _authority(p, b)
    os.remove(p)
    r = _run_authority(p, a)
    assert r.outcome == "migration-source-missing" and _facts(r) == (False, False, "missing", None)
    assert not os.path.exists(p) and "migration_attempted" not in attempted


def test_row_11b_an_existing_path_that_will_not_open_is_unopenable(tmp_path):
    p = _store(tmp_path / "s.db", 5)
    a = _authority(p, 5)
    os.remove(p)
    os.mkdir(p)
    r = _run_authority(p, a)
    assert r.outcome == "store-unopenable" and r.resulting_state == "unknown"


def test_row_12_a_postcondition_failure_rolls_back_to_the_original_stamp(tmp_path, monkeypatch):
    p = _store(tmp_path / "s.db", 2)
    monkeypatch.setattr(M, "_check_outcome_chains", lambda conn, run, before, now: M._refuse_unless(run, M.STEP_CHAINS, ["planted"]))
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert r.result.outcome == "unsupported-migration" and _facts(r.result) == (False, False, "unknown", None) and _stamp(p) == 2


@pytest.mark.parametrize("name", ["a?b.db", "a#b.db", "a%41b.db", "a b.db"], ids=["question", "hash", "percent", "space"])
def test_the_rung_addresses_exactly_the_file_the_mint_observed(tmp_path, name):
    """E2-01: `?`, `#`, `%` and spaces must not address a sibling."""
    p = _store(tmp_path / name, 5)
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert r.result.outcome == "migrated" and _stamp(p) == 6
    assert sorted(f for f in os.listdir(tmp_path) if not f.endswith(rm._AUDIT_SUFFIX)) == [name]


def test_a_non_utf8_name_is_addressed_by_its_bytes(tmp_path):
    raw = os.fsencode(str(tmp_path)) + b"/s\xff.db"
    p = os.fsdecode(raw)
    _store(p, 5)
    assert rm.run_release_rung(p, host_attestation=ATT).result.outcome == "migrated"


def test_a_mismatched_expectation_stops_before_any_authority_is_used(tmp_path):
    p = _store(tmp_path / "s.db", 5)
    r = rm.run_release_rung(p, host_attestation=ATT, expect_base=4)
    assert (r.kind, r.result, r.preflight_base, r.expected_base) == ("unexpected-base", None, 5, 4) and _stamp(p) == 5


def test_a_report_binds_the_record_to_the_minted_endpoints_not_to_the_result_s_version():
    result = rm.MigrationResult("migrated", True, True, "destination", 14, "d")
    op = "op-00000000-0000-4000-8000-000000000000"
    assert rm.RungReport("delegated", result, 13, 13, op, 13, 14, None).to_version == 14
    with pytest.raises(ValueError):
        rm.RungReport("delegated", result, 14, 14, op, 14, 15, None)


def test_a_lawful_lower_rung_result_is_in_the_domain_and_an_unlawful_one_is_not():
    assert rm.MigrationResult("migrated", True, True, "destination", 14, "d").resulting_version == 14
    with pytest.raises(ValueError):
        rm.MigrationResult("migrated", True, True, "destination", 1, "d")


def test_the_digest_is_the_rung_s_own_preimage():
    for b in BASES:
        assert rm._declared_migration_digest(b, b + 1) == hashlib.sha256(M.plan_preimage(b, b + 1)).hexdigest()
    assert len({rm._declared_migration_digest(b, b + 1) for b in BASES}) == len(BASES)


def test_an_escape_after_the_mint_carries_the_rung_and_one_before_it_carries_none(tmp_path, monkeypatch):
    p = _store(tmp_path / "s.db", 5)

    def boom(*a, **k):
        raise sv.PackageConsistencyError("forced")
    monkeypatch.setattr(rm, "_run_rung", boom)
    with pytest.raises(sv.PackageConsistencyError) as ei:
        rm.run_release_rung(p, host_attestation=ATT)
    op, frm, to = ei.value.rung_context
    assert (frm, to) == (5, 6) and op.startswith("op-")
    monkeypatch.undo()
    monkeypatch.setattr(rm, "_preflight_classify", boom)
    with pytest.raises(sv.PackageConsistencyError) as ei:
        rm.run_release_rung(p, host_attestation=ATT)
    assert ei.value.rung_context is None


def test_feeds_is_what_each_check_really_reads():
    """Declared, and compared with the derivation, so it cannot drift: a read feeds a check iff the check, or a function it calls
    with the run, reads what the read writes. A byte check's stored text has its own name, so five reads derive one check each."""
    import ast
    import inspect
    import textwrap

    def attrs(fn):
        t = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        r, w = set(), set()
        for n in ast.walk(t):
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "run":
                (w if isinstance(n.ctx, ast.Store) else r).add(n.attr)
            if isinstance(n, ast.Call) and any(isinstance(a, ast.Name) and a.id == "run" for a in n.args):
                h = getattr(M, getattr(n.func, "id", ""), None)
                if inspect.isfunction(h) and h is not M._refuse_unless:
                    a, b = attrs(h)
                    r |= a
                    w |= b
        return r - {"base", "target"}, w
    checks = []
    for e in M.FORWARD_ENTRIES:
        if e.kind == "check" and e.step not in checks:
            checks.append(e.step)
    checks.append(M._check_stamp)
    reads = [e for e in M.plan(1, HEAD) + [e for e in M.FORWARD_ENTRIES if e.kind == "read"] if e.kind == "read"]
    for e in reads:
        written = attrs(e.step)[1]
        assert list(e.fields) == [c for c in checks if attrs(c)[0] & written], e.step.__name__


# ---- the original preserved (round 1's closure checks on the unstamped first rung; v9's "original-preservation checks") ------
def _legacy(path):
    """An unstamped v1 store holding a row, so a rollback has data to keep."""
    p = _store(path, 1, stamp=0)
    c = sqlite3.connect(p)
    c.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) VALUES('e','u','s','r','o',1,0,'{}')")
    c.commit()
    c.close()
    return p


def _bytes(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _dump(path):
    c = sqlite3.connect(path)
    try:
        return list(c.iterdump())
    finally:
        c.close()


def test_before_delegation_an_unstamped_store_keeps_its_bytes_and_stamp(tmp_path):
    """Resolving and minting read the store and never write it: a rung stopped at the expectation leaves the file byte for byte."""
    p = _legacy(tmp_path / "s.db")
    before = _bytes(p)
    r = rm.run_release_rung(p, host_attestation=ATT, expect_base=7)
    assert r.kind == "unexpected-base" and r.preflight_base == 1 and _stamp(p) == 0 and _bytes(p) == before
    _authority(p, 1)
    assert _stamp(p) == 0 and _bytes(p) == before


def test_a_first_rung_that_fails_restores_the_original_stamp_and_data(tmp_path, monkeypatch):
    """Rollback leaves the ORIGINAL raw stamp: 0 on an unstamped store, not `t-1`, with every row as it was."""
    p = _legacy(tmp_path / "s.db")
    before = _dump(p)
    monkeypatch.setattr(M, "_check_stamp", lambda conn, run: M._refuse_unless(run, M.STEP_STAMP, ["planted"]))
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert r.result.outcome == "unsupported-migration" and _facts(r.result)[:2] == (False, False)
    assert _stamp(p) == 0 and _dump(p) == before


def test_an_invalid_unstamped_shape_refuses_at_the_preflight_and_is_untouched(tmp_path):
    p = str(tmp_path / "s.db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE foreign_thing (x)")
    c.close()
    before = _bytes(p)
    r = rm.run_release_rung(p, host_attestation=ATT)
    assert r.kind == "preflight" and r.result.outcome == "foreign-shape" and _stamp(p) == 0 and _bytes(p) == before


@pytest.mark.parametrize("b, stamp", [(1, 0), (13, None)], ids=["unstamped first rung", "stamped middle rung"])
def test_forged_resolution_evidence_cannot_alter_a_rung(tmp_path, b, stamp):
    """Under both real-store conditions: on a good store a forged resolution mints the same endpoints from the store's own observation,
    and on a failing one it refuses for the same reason as the genuine evidence."""
    p = _store(tmp_path / "s.db", b, stamp=stamp)
    canonical = os.path.realpath(p)
    genuine, forged = rm.PreflightResolution(canonical, b, "0" * 64), rm.PreflightResolution(canonical, b, "ab" * 32)
    a, f = (rm.mint_release_authority(p, ATT, resolved=x) for x in (genuine, forged))
    assert (a.from_version, a.to_version, a.source_digest) == (f.from_version, f.to_version, f.source_digest) == (b, b + 1, a.source_digest)
    os.remove(p)
    reasons = []
    for x in (genuine, forged):
        with pytest.raises(rm.MintError) as e:
            rm.mint_release_authority(p, ATT, resolved=x)
        reasons.append(e.value.reason)
    assert reasons[0] == reasons[1], reasons
