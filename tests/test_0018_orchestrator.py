"""The 0018 release-migration orchestrator — the frozen I13–I23 suite.

Operative numerals per the 0019 rider on specs/0018: the preflight passes ONLY
resolved base 7 to minting; bases 1–6 return `unsupported-base` with the
ladder diagnostic; already-current v8 returns `current`; the two `current`
rows carry resulting_version 8.

The exhaustive §4e-domain oracle enumeration (I15's gate-extension obligation)
lives in tests/test_0013_presend_gates.py alongside the other mechanical
gates; here the LITERAL table rows and the carrier laws are asserted
explicitly.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile

import pytest

from veracium.store import release_migration as rm
from veracium.store import schema_version as sv
from veracium.store.schema_version import PackageConsistencyError

HEAD = sv.SCHEMA_VERSION
MINT_BASE = HEAD - 1                # the ordinary one-step migration base

# specs/0001 I13a: v11 is a STAMP-ONLY bump — SCHEMA_V11 is SCHEMA_V10 —
# so "head stamp over the previous version's shape" stopped being a
# mismatch and became, correctly, `current`. A shape-mismatch fixture has
# to use a base whose SHAPE actually differs from head, and pinning that
# to a literal would only defer the same breakage to the next stamp-only
# bump. Derived from the schema table instead, so it follows the shapes.
SHAPE_BASE = max(v for v in sv.SCHEMAS
                 if v < HEAD and sv.SCHEMAS[v] != sv.SCHEMAS[HEAD])

ATT = rm.MigrationAttestation(quiesced=True, backup_ref="backup-1")
_OP = "op-00000000-0000-4000-8000-000000000000"


@pytest.fixture(autouse=True)
def _fast_busy_timeout(monkeypatch):
    monkeypatch.setattr(rm, "_BUSY_TIMEOUT_S", 0.05)


def _store_at(version: int) -> str:
    """A fixture store carrying the SCHEMAS[version] constructor object set,
    stamped `version` (the slice-1 test_0021 pattern)."""
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in sv.SCHEMAS[version]:
        c.execute(o.ddl)
    c.execute(f"PRAGMA user_version = {version}")
    c.commit()
    c.close()
    return p


def _unstamped_v1() -> str:
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    for o in sv.SCHEMA_V1:
        c.execute(o.ddl)
    c.commit()
    c.close()
    return p


def _bytes(p: str) -> bytes:
    with open(p, "rb") as f:
        return f.read()


def _no_audit(p: str) -> bool:
    return not os.path.exists(rm.audit_trail_path(os.path.realpath(p)))


def _valid_facts(outcome: str) -> rm.TerminalFacts:
    """One valid TerminalFacts cell for `outcome` at this release's
    endpoints."""
    special = {
        "migrated": (True, True, "destination", HEAD),
        "current": (False, False, "destination", HEAD),
        "migration-source-missing": (False, False, "missing", None),
    }
    ch, co, st, ver = special.get(outcome, (None, None, "unknown", None))
    if outcome not in special and "unknown" not in \
            rm._OUTCOME_TERMINAL_STATES.get(outcome, {"unknown"}):
        raise AssertionError(f"no generic cell for {outcome}")
    return rm.TerminalFacts(outcome, MINT_BASE, HEAD, ch, co, st, ver)


# ==========================================================================
# I13 — the preflight matrix is TOTAL
# ==========================================================================

@pytest.mark.parametrize("base", [1, 2, 3, 4, 5, 6])
def test_below_v7_base_refuses_with_the_ladder_message(base):
    """Bases 1–6 → `unsupported-base` (returned, never raised), the ladder
    diagnostic, NO authority, ZERO audit rows, bytes+stamp unchanged."""
    p = _store_at(base)
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert r.outcome == "unsupported-base"
    assert (r.store_changed, r.transaction_committed) == (False, False)
    assert r.resulting_state == "source"
    assert r.resulting_version == base
    if base <= 5:
        assert "migrate to v6 on a ≤0.8.x release" in r.diagnostic
        assert "then to v7 on a 0.9.x/0019-era release" in r.diagnostic
        assert "then run this release's migration" in r.diagnostic
    else:
        assert "migrate to v7 on a 0019-era release first" in r.diagnostic
    assert _bytes(p) == before
    assert _no_audit(p)


def test_unstamped_legacy_v1_resolves_without_stamping_and_takes_the_ladder():
    """§4h: a legitimate unstamped store whose shape matches a
    `legacy_base_versions()` entry resolves to that base WITHOUT being
    stamped — and then takes the base-1 ladder cell."""
    p = _unstamped_v1()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert (r.outcome, r.resulting_version) == ("unsupported-base", 1)
    assert _bytes(p) == before                      # never stamped
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == 0


def test_below_v7_open_unchanged():
    """Ordinary OPENING of a below-v7 store is UNCHANGED by 0018 — the
    existing below-head refusal governs it (unstamped legacy →
    `migration-required`; a stamped below-head store refuses exactly as the
    pre-0018 suite pins it, tests/test_schema_v3_migration.py:106); only the
    orchestrator's preflight returns `unsupported-base`."""
    from veracium.store.sqlite import SqliteStore
    p = _unstamped_v1()
    with pytest.raises(sv.StoreVersionError) as ei:
        SqliteStore(p)
    assert ei.value.reason == "migration-required"
    p = _store_at(6)
    before = _bytes(p)
    with pytest.raises((sv.StoreVersionError, PackageConsistencyError)):
        SqliteStore(p)                     # refused, never silently migrated
    assert _bytes(p) == before


def test_preflight_matrix_total():
    """Every remaining §4e preflight cell, each zero-authority/zero-audit and
    byte-identical — EXCEPT current-with-repair, the one interception that
    commits (external R1-7)."""
    # current, clean → (False, False, destination, 8), byte-identical
    from veracium.store.sqlite import SqliteStore
    p = tempfile.mktemp(suffix=".db")
    SqliteStore(p).close()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("current", False, False, "destination", HEAD)
    assert _bytes(p) == before and _no_audit(p)

    # current with rebuildable drift → (True, True, destination, 8) via the
    # ONE shared opening path (0007's repair-during-opening); the index is back
    key = sorted(sv.rebuildable_keys(HEAD))[0]
    c = sqlite3.connect(p)
    c.execute(f"DROP INDEX {key[1]}")
    c.commit()
    c.close()
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("current", True, True, "destination", HEAD)
    c = sqlite3.connect(p)
    assert c.execute("SELECT COUNT(*) FROM sqlite_master WHERE name=?",
                     (key[1],)).fetchone()[0] == 1
    c.close()
    assert _no_audit(p)

    # missing (nothing at the path) → (F, F, missing, None); nothing created
    p = tempfile.mktemp(suffix=".db")
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("migration-source-missing", False, False,
                            "missing", None)
    assert not os.path.exists(p)

    # a valid, EMPTY, user_version=0 database → the second source-missing form
    # (external R2-3): never created-into, never adopted
    p = tempfile.mktemp(suffix=".db")
    sqlite3.connect(p).close()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("migration-source-missing", False, False,
                            "unaccepted", None)
    assert _bytes(p) == before and _no_audit(p)

    # invalid-store: bytes that are not a SQLite database
    p = tempfile.mktemp(suffix=".db")
    with open(p, "w") as f:
        f.write("this is not a database " * 40)
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("invalid-store", False, False, "unknown", None)
    assert _bytes(p) == before and _no_audit(p)

    # store-unopenable: the path cannot be opened at all (a directory)
    d = tempfile.mkdtemp()
    r = rm.run_release_migration(d, host_attestation=ATT)
    assert tuple(r)[:5] == ("store-unopenable", False, False, "unknown", None)

    # locked: another connection holds the write lock
    p = _store_at(MINT_BASE)
    holder = sqlite3.connect(p)
    holder.execute("BEGIN IMMEDIATE")
    try:
        before = _bytes(p)
        r = rm.run_release_migration(p, host_attestation=ATT)
        assert tuple(r)[:5] == ("locked", False, False, "unknown", None)
    finally:
        holder.close()
    assert _bytes(p) == before and _no_audit(p)

    # unsupported-sqlite: the runtime gate fires before any version decision
    real = sv.runtime_supported
    sv.runtime_supported = lambda: False
    try:
        r = rm.run_release_migration(p, host_attestation=ATT)
    finally:
        sv.runtime_supported = real
    assert tuple(r)[:5] == ("unsupported-sqlite", False, False, "unknown",
                            None)
    assert _no_audit(p)

    # foreign-shape: unstamped, matches no evidenced legacy base
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE weird (x TEXT)")
    c.commit()
    c.close()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("foreign-shape", False, False, "unaccepted", None)
    assert _bytes(p) == before and _no_audit(p)

    # newer: stamped above the head
    p = _store_at(HEAD)
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {HEAD + 1}")
    c.commit()
    c.close()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("newer", False, False, "unaccepted", None)
    assert _bytes(p) == before and _no_audit(p)

    # invalid-version: a negative stamp
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version = -1")
    c.commit()
    c.close()
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("invalid-version", False, False, "unaccepted",
                            None)

    # stamped-shape-mismatch, head-stamped: a HEAD stamp over an older
    # SHAPE (not merely an older version — see SHAPE_BASE above)
    p = _store_at(SHAPE_BASE)
    c = sqlite3.connect(p)
    c.execute(f"PRAGMA user_version = {HEAD}")
    c.commit()
    c.close()
    before = _bytes(p)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("stamped-shape-mismatch", False, False,
                            "unaccepted", None)
    assert _bytes(p) == before and _no_audit(p)

    # stamped-shape-mismatch, below-head-stamped: v3 stamp over a v1 shape
    p = _store_at(1)
    c = sqlite3.connect(p)
    c.execute("PRAGMA user_version = 3")
    c.commit()
    c.close()
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("stamped-shape-mismatch", False, False,
                            "unaccepted", None)

    # invalid-request: a malformed call (path / attestation)
    r = rm.run_release_migration(123, host_attestation=ATT)
    assert tuple(r)[:5] == ("invalid-request", False, False, "unknown", None)
    r = rm.run_release_migration("x\x00y", host_attestation=ATT)
    assert tuple(r)[:5] == ("invalid-request", False, False, "unknown", None)


def test_base_7_proceeds_through_the_audited_operation():
    """Resolved base 7 ALONE mints and delegates: the store lands at v8, the
    durable trail carries the attempted event AND the append-once terminal
    record, and the result's facts come from the record verbatim."""
    p = _store_at(MINT_BASE)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("migrated", True, True, "destination", HEAD)
    assert "(recorded)" in r.diagnostic
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == HEAD
    apath = rm.audit_trail_path(os.path.realpath(p))
    trail = json.load(open(apath))
    assert len(trail) == 1
    entry = next(iter(trail.values()))
    assert entry["attempted"]["event"] == "migration_attempted"
    assert entry["attempted"]["from_version"] == MINT_BASE
    assert entry["terminal"]["outcome"] == "migrated"
    assert entry["terminal"]["resulting_version"] == HEAD
    # the terminal record read back is a valid, bound TerminalFacts
    op = next(iter(trail))
    rb = rm.read_terminal(op, audit_path=apath)
    assert rb.kind == "record" and rb.facts.outcome == "migrated"


def test_migrated_store_data_survives():
    """The delegated operation MIGRATES (never recreates): a v7 ledger row
    survives the cross with the rider columns NULL."""
    p = _store_at(MINT_BASE)
    c = sqlite3.connect(p)
    c.execute("INSERT INTO contribution_ledger(id,user_id,survivor_type,"
              "survivor_id,site,identity_digest,evidence_ref_digest,payload,"
              "op_key,created_at) VALUES('contrib-1','u1','edge','e-1',"
              "'absorption',NULL,NULL,'{}',NULL,'2026-08-01T00:00:00+00:00')")
    c.commit()
    c.close()
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert r.outcome == "migrated"
    c = sqlite3.connect(p)
    assert c.execute("SELECT contributor_type, contributor_ref FROM "
                     "contribution_ledger WHERE id='contrib-1'"
                     ).fetchone() == (None, None)
    c.close()


# ==========================================================================
# I14 — the mint race closes by the EXACT §4c sequence
# ==========================================================================

def test_mint_race_reclassifies(monkeypatch):
    """EXACTLY three resolves and three mint calls, interleaved resolve→mint,
    re-resolution after failures one and two ONLY, NO resolve after the third
    failure; the third error → `mint-contention` (False, False, unknown,
    None) with the three attempts named — call counts asserted, not
    inferred."""
    p = _store_at(MINT_BASE)
    calls = []

    real_classify = rm._preflight_classify

    def counting_classify(path):
        calls.append("resolve")
        return real_classify(path)

    def failing_mint(path, attestation, *, resolved):
        calls.append("mint")
        raise rm.MintError("source-changed", "forced contention")

    monkeypatch.setattr(rm, "_preflight_classify", counting_classify)
    monkeypatch.setattr(rm, "mint_release_authority", failing_mint)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("mint-contention", False, False, "unknown", None)
    assert "three mint attempts" in r.diagnostic
    assert calls == ["resolve", "mint", "resolve", "mint", "resolve", "mint"]
    assert _no_audit(p)                       # nothing minted, nothing written
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == MINT_BASE


def test_mint_race_first_failure_reclassifies_to_the_now_true_outcome(
        monkeypatch):
    """A re-resolution landing on a non-base-7 cell exits with THAT cell's
    interception outcome: a vanished store → the missing refusal; a migrated
    store → `current`."""
    # vanished
    p = _store_at(MINT_BASE)

    def vanish_then_fail(path, attestation, *, resolved):
        os.remove(p)
        raise rm.MintError("source-missing", "racer deleted it")
    monkeypatch.setattr(rm, "mint_release_authority", vanish_then_fail)
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("migration-source-missing", False, False,
                            "missing", None)

    # migrated by a racer
    p2 = _store_at(MINT_BASE)

    def migrate_then_fail(path, attestation, *, resolved):
        from veracium.store.migration import migrate_store
        migrate_store(p2)
        raise rm.MintError("source-changed", "racer migrated it")
    monkeypatch.setattr(rm, "mint_release_authority", migrate_then_fail)
    r = rm.run_release_migration(p2, host_attestation=ATT)
    assert tuple(r)[:5] == ("current", False, False, "destination", HEAD)


def test_mint_error_reasons_are_closed():
    with pytest.raises(ValueError):
        rm.MintError("bogus-reason")
    for reason in ("source-missing", "source-unaccepted", "source-changed"):
        assert rm.MintError(reason).reason == reason


def test_mint_source_unaccepted_when_observation_matches_but_shape_rejected(
        monkeypatch):
    """§4b's labeling: current observation MATCHES `source_fingerprint` but
    the shape is no longer accepted → `source-unaccepted`."""
    p = _store_at(MINT_BASE)
    canonical = os.path.realpath(p)
    c = sqlite3.connect(p)
    fp = rm.preflight_fingerprint(c)
    c.close()
    ev = rm.PreflightResolution(canonical, MINT_BASE, fp)
    real = sv.accepted_digests
    monkeypatch.setattr(sv, "accepted_digests",
                        lambda v: set() if v == MINT_BASE else real(v))
    with pytest.raises(rm.MintError) as ei:
        rm.mint_release_authority(canonical, ATT, resolved=ev)
    assert ei.value.reason == "source-unaccepted"


# ==========================================================================
# I15 — the literal §4e table (the exhaustive oracle is in the presend gates)
# ==========================================================================

def test_migration_result_truth_table():
    MR = rm.MigrationResult
    # every preflight row, all FIFTEEN (unsupported-base parametrized 1–6)
    for base in range(1, 7):
        MR("unsupported-base", False, False, "source", base, "d")
    MR("current", False, False, "destination", HEAD, "d")   # clean
    MR("current", True, True, "destination", HEAD, "d")     # with repair
    MR("migration-source-missing", False, False, "missing", None, "d")
    MR("migration-source-missing", False, False, "unaccepted", None, "d")
    for outcome in ("store-unopenable", "invalid-store", "locked",
                    "unsupported-sqlite", "invalid-request",
                    "mint-contention"):
        MR(outcome, False, False, "unknown", None, "d")
    for outcome in ("foreign-shape", "newer", "invalid-version",
                    "stamped-shape-mismatch"):
        MR(outcome, False, False, "unaccepted", None, "d")
    # the four fixed no-record rows (external R2-9)
    for outcome in sorted(rm._NO_RECORD_OUTCOMES):
        MR(outcome, False, False, "unknown", None, "d")
    # the delegated DEFERENCE law (external R2-2): tri-state effects survive —
    # the reviewer-verified VALID seven-field cells pass verbatim
    MR("internal-error", None, None, "unknown", None, "d")
    MR("migration-failed", None, None, "unknown", None, "d")
    MR("internal-error", True, True, "destination", HEAD, "d")
    MR("migrated", True, True, "destination", HEAD, "d")
    # out-of-table carriers REFUSE
    for bad in [
        ("unsupported-base", False, False, "source", MINT_BASE, "d"),  # the mint base is never
        ("unsupported-base", False, False, "source", None, "d"),
        ("unsupported-base", True, True, "source", 3, "d"),
        ("current", False, False, "destination", MINT_BASE, "d"),  # wrong ver
        ("mint-contention", None, None, "unknown", None, "d"),
        ("migration-audit-unavailable", None, None, "unknown", None, "d"),
        ("migrated", False, False, "destination", HEAD, "d"),    # no-change
        ("migrated", True, True, "source", HEAD, "d"),
        ("locked", False, False, "bogus-state", None, "d"),      # non-vocab
        ("locked", False, False, "source", None, "d"),
        ("package-inconsistent", None, None, "unknown", None, "d"),  # escape,
        ("totally-made-up", False, False, "unknown", None, "d"),  # never a result
        ("current", 1, 1, "destination", HEAD, "d"),             # coerced bool
        ("current", False, False, "destination", True, "d"),     # bool version
    ]:
        with pytest.raises((ValueError, TypeError)):
            rm.MigrationResult(*bad)


# ==========================================================================
# I20 — the two new outcomes are returnable, never terminal
# ==========================================================================

def test_new_outcomes_are_excluded_from_terminal_facts():
    """The reviewer's probe as the regression: `unsupported-base` and
    `mint-contention` REFUSE in TerminalFacts (and hence at terminal
    publication and both loud-escape carriers); the two never-terminal audit
    outcomes are excluded too (the latent-0013-gap closure);
    `package-inconsistent` is INCLUDED; the explicit `TERMINAL_OUTCOMES`
    definition is asserted."""
    for outcome in ("unsupported-base", "mint-contention",
                    "migration-audit-unavailable",
                    "migration-audit-state-unknown"):
        assert rm.TerminalFacts(outcome, MINT_BASE, HEAD, False, False,
                                "unknown", None).problems(), outcome
        assert outcome not in rm.TERMINAL_OUTCOMES
        # terminal publication refuses: the producer validates before writing
        with pytest.raises(ValueError):
            rm._write_terminal(tempfile.mktemp(), _OP,
                               rm.TerminalFacts(outcome, MINT_BASE, HEAD,
                                                False, False, "unknown",
                                                None))
    # the inclusion cell
    assert not rm.TerminalFacts("package-inconsistent", MINT_BASE, HEAD, None,
                                None, "unknown", None).problems()
    assert "package-inconsistent" in rm.TERMINAL_OUTCOMES
    # the explicit definition (0018 §4h, external R2-4)
    assert rm.TERMINAL_OUTCOMES == (
        (rm.OUTCOMES | rm._AUDIT_ONLY_OUTCOMES)
        - {"unsupported-base", "mint-contention",
           "migration-audit-unavailable", "migration-audit-state-unknown"})
    assert {"unsupported-base", "mint-contention"} <= rm.RETURNABLE_OUTCOMES
    assert not ({"unsupported-base", "mint-contention"} & rm.OUTCOMES)


# ==========================================================================
# I22 — the fingerprint has an independent oracle
# ==========================================================================

def _independent_fingerprint(path: str) -> str:
    """A separately-written encoder: its own identity-equivalent (string-keyed
    typed objects straight off sqlite_master/table_xinfo) and its own
    length-framing."""
    c = sqlite3.connect(path)
    ident = {}
    for typ, name, tbl, sql in c.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT GLOB 'sqlite_*' ORDER BY type, name").fetchall():
        entry = {"type": typ, "table": tbl, "sql": sql}
        if typ == "table":
            entry["columns"] = [
                [row[1], (row[2] or "").upper(), int(row[3]),
                 None if row[4] is None else str(row[4]), int(row[5]),
                 int(row[6])]
                for row in c.execute("SELECT * FROM pragma_table_xinfo(?)",
                                     (name,))]
        ident[f"{typ}:{name}"] = entry
    uv = c.execute("PRAGMA user_version").fetchone()[0]
    c.close()
    h = hashlib.sha256()
    for seg in ("0018-preflight-fingerprint-v1", str(uv),
                json.dumps(ident, sort_keys=True, separators=(",", ":"))):
        raw = seg.encode("utf-8")
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)
    return h.hexdigest()


def test_preflight_fingerprint_oracle():
    """The independent encoder reproduces the §4b fingerprint byte-for-byte on
    fixture stores incl. a generated-column store (the `table_xinfo` cell) and
    a quoted-literal DDL store (0007's byte-exactness case); the raw
    `manifest()` serialization failure (tuple keys) is the named negative."""
    fixtures = []
    p = _store_at(MINT_BASE)
    fixtures.append(p)
    # a generated-column store
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE g (a INTEGER, b INTEGER GENERATED ALWAYS AS "
              "(a * 2) VIRTUAL)")
    c.execute("PRAGMA user_version = 3")
    c.commit()
    c.close()
    fixtures.append(p)
    # a quoted-literal DDL store (two spaces inside the literal)
    p = tempfile.mktemp(suffix=".db")
    c = sqlite3.connect(p)
    c.execute("CREATE TABLE q (x TEXT CHECK(x <> 'a  b'))")
    c.commit()
    c.close()
    fixtures.append(p)
    for p in fixtures:
        c = sqlite3.connect(p)
        got = rm.preflight_fingerprint(c)
        c.close()
        assert got == _independent_fingerprint(p), p
        assert rm._DIGEST_RE.fullmatch(got)
    # the named negative case (external R3-1): raw manifest() has TUPLE keys
    c = sqlite3.connect(fixtures[0])
    with pytest.raises(TypeError):
        json.dumps(sv.manifest(c), sort_keys=True)
    c.close()


# ==========================================================================
# I16 — the attestation contract is exact
# ==========================================================================

def test_attestation_contract():
    p = _store_at(MINT_BASE)
    # absent → TypeError (required keyword)
    with pytest.raises(TypeError):
        rm.run_release_migration(p)
    # coerced quiesced: 1 and truthy objects refuse (`is True`)
    with pytest.raises(ValueError):
        rm.MigrationAttestation(quiesced=1, backup_ref="b1")

    class Truthy:
        def __bool__(self):
            return True
    with pytest.raises(ValueError):
        rm.MigrationAttestation(quiesced=Truthy(), backup_ref="b1")
    # grammar-violating backup_ref, incl. embedded space / empty / whitespace
    for bad in ("", " ", "a b", "x" * 129, "-leading", "tab\tx"):
        with pytest.raises(ValueError):
            rm.MigrationAttestation(quiesced=True, backup_ref=bad)
    # unknown extra fields refused (immutable, exact)
    with pytest.raises(TypeError):
        rm.MigrationAttestation(quiesced=True, backup_ref="b1", extra=1)

    # duck-typed carrier refused at admission, never copied
    class Duck:
        quiesced = True
        backup_ref = "b1"
    r = rm.run_release_migration(p, host_attestation=Duck())
    assert r.outcome == "invalid-request"

    # a HOSTILE SUBCLASS (attribute interception) refused by exact-type
    # admission BEFORE any attribute is read (the 0013 authority-regression
    # pattern, R14-4)
    class Hostile(rm.MigrationAttestation):
        def __getattribute__(self, name):
            if name in ("quiesced", "backup_ref"):
                raise RuntimeError("hostile getter boom")
            return object.__getattribute__(self, name)
    r = rm.run_release_migration(
        p, host_attestation=Hostile(quiesced=True, backup_ref="b1"))
    assert r.outcome == "invalid-request"
    with pytest.raises(TypeError):
        rm.mint_release_authority(
            p, Hostile(quiesced=True, backup_ref="b1"),
            resolved=rm.PreflightResolution(os.path.realpath(p), MINT_BASE,
                                            "0" * 64))
    # the store was never touched by any of the refusals
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == MINT_BASE
    assert _no_audit(p)


# ==========================================================================
# I18 — the resolution evidence is reason-labeling only
# ==========================================================================

def test_resolution_is_reason_labeling_only():
    """I18's two-condition expectation VERBATIM: with a VALID store +
    attestation, mint SUCCEEDS identically under forged evidence (an authority
    IS granted — forgery must not deny either); with a FAILING store, mint
    fails identically and at most the `MintError` reason label differs."""
    p = _store_at(MINT_BASE)
    canonical = os.path.realpath(p)
    c = sqlite3.connect(p)
    fp = rm.preflight_fingerprint(c)
    c.close()
    genuine = rm.PreflightResolution(canonical, MINT_BASE, fp)
    forged = rm.PreflightResolution(canonical, MINT_BASE, "ab" * 32)

    a_genuine = rm.mint_release_authority(canonical, ATT, resolved=genuine)
    a_forged = rm.mint_release_authority(canonical, ATT, resolved=forged)
    for a in (a_genuine, a_forged):
        assert type(a) is rm.MigrationAuthority
        assert (a.from_version, a.to_version) == (MINT_BASE, HEAD)
        assert a.store_path == canonical
        assert a.backup_ref == "backup-1"
    # identical success facts; only the operation identity differs
    assert a_genuine._replace(operation_id="x", issued_at="t",
                              expires_at="t") == \
        a_forged._replace(operation_id="x", issued_at="t", expires_at="t")

    # failing store: both fail; at most the reason label differs
    os.remove(p)
    reasons = {}
    for name, ev in (("genuine", genuine), ("forged", forged)):
        with pytest.raises(rm.MintError) as ei:
            rm.mint_release_authority(canonical, ATT, resolved=ev)
        reasons[name] = ei.value.reason
    assert reasons["genuine"] == reasons["forged"] == "source-missing"


def test_resolution_recursive_exactness():
    """Closure obligation 2: the `PreflightResolution` boundary EXACT-TYPES
    every scalar BEFORE any comparison — `resolved_base=True` refuses,
    hostile `str` subclasses refuse before their methods can run."""
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution("/s", True, "0" * 64)      # bool is an int subclass

    class HostileStr(str):
        def __eq__(self, o):
            raise RuntimeError("hostile __eq__")

        def __ne__(self, o):
            raise RuntimeError("hostile __ne__")

        def __hash__(self):
            raise RuntimeError("hostile __hash__")

        def __len__(self):
            raise RuntimeError("hostile __len__")
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution(HostileStr("/s"), 7, "0" * 64)
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution("/s", 7, HostileStr("0" * 64))
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution("", 7, "0" * 64)           # empty path
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution("/s", HEAD, "0" * 64)      # outside 1..MINT_BASE
    with pytest.raises((TypeError, ValueError)):
        rm.PreflightResolution("/s", 7, "0" * 63)         # malformed digest
    # wrong type at the mint boundary → refused
    p = _store_at(MINT_BASE)
    with pytest.raises(TypeError):
        rm.mint_release_authority(p, ATT, resolved={"canonical_path": p})

    class HostileRes(rm.PreflightResolution):
        pass
    with pytest.raises(TypeError):
        rm.mint_release_authority(
            p, ATT,
            resolved=HostileRes(os.path.realpath(p), MINT_BASE, "0" * 64))


# ==========================================================================
# I23 — ReadbackResult is a closed constructed carrier
# ==========================================================================

def test_readback_result_contract(tmp_path):
    TF = rm.TerminalFacts
    good = TF("migrated", MINT_BASE, HEAD, True, True, "destination", HEAD)
    ok = rm.ReadbackResult("record", good, ())
    assert (ok.kind, ok.facts, ok.problems) == ("record", good, ())
    rm.ReadbackResult("absent", None, ())
    rm.ReadbackResult("malformed", None, ("boom",))

    # every cross-field-law violation refuses
    bad_facts = TF("migrated", MINT_BASE, HEAD, False, False, "source",
                   MINT_BASE)                      # invalid facts (no-change migrated)
    for args in [
        ("record", None, ()),                      # record without facts
        ("record", good, ("p",)),                  # record with problems
        ("record", bad_facts, ()),                 # invalid facts
        ("absent", good, ()),                      # absent with facts
        ("absent", None, ("p",)),                  # absent with problems
        ("malformed", good, ("p",)),               # malformed with facts
        ("malformed", None, ()),                   # malformed without problems
        ("bogus", None, ()),                       # unknown kind
    ]:
        with pytest.raises((ValueError, TypeError)):
            rm.ReadbackResult(*args)
    # a list-typed problems, a mutable member, and an uncapped flood refuse
    with pytest.raises((ValueError, TypeError)):
        rm.ReadbackResult("malformed", None, ["boom"])
    with pytest.raises((ValueError, TypeError)):
        rm.ReadbackResult("malformed", None, (["mutable"],))
    with pytest.raises((ValueError, TypeError)):
        rm.ReadbackResult("malformed", None, tuple(f"p{i}" for i in range(40)))
    with pytest.raises((ValueError, TypeError)):
        rm.ReadbackResult("malformed", None, ("x" * 501,))

    # a hostile SUBCLASS OF TerminalFacts as facts: exact-type + the UNBOUND
    # problems() call — the reviewer's dynamic-validator probe
    class FakeTF(rm.TerminalFacts):
        def problems(self):
            return []
    with pytest.raises((ValueError, TypeError)):
        rm.ReadbackResult(
            "record",
            FakeTF("migrated", MINT_BASE, HEAD, False, False, "source",
                   MINT_BASE),
            ())

    # the malformed row's TOTAL construction: a durable row failing validation
    # yields ≥1 capped problem entry
    apath = str(tmp_path / "trail.json")
    with open(apath, "w") as f:
        json.dump({_OP: {"terminal": {
            "outcome": "migrated", "from_version": MINT_BASE,
            "to_version": HEAD, "store_changed": False,
            "transaction_committed": False, "resulting_state": "source",
            "resulting_version": MINT_BASE}}}, f)
    rb = rm.read_terminal(_OP, audit_path=apath)
    assert rb.kind == "malformed" and len(rb.problems) >= 1
    assert all(len(e) <= 500 for e in rb.problems)

    # unparsable trail → malformed(read-failed: <class>)
    with open(apath, "w") as f:
        f.write("{not json")
    rb = rm.read_terminal(_OP, audit_path=apath)
    assert rb.kind == "malformed" and rb.problems[0].startswith("read-failed:")

    # a FORCED read failure (an unopenable trail: a directory) maps to
    # malformed(read-failed: …), never a raise (closure obligation 3)
    d = str(tmp_path / "dir-trail")
    os.mkdir(d)
    rb = rm.read_terminal(_OP, audit_path=d)
    assert rb.kind == "malformed" and rb.problems[0].startswith("read-failed:")

    # no trail at all → absent; present trail, unknown operation → absent
    rb = rm.read_terminal(_OP, audit_path=str(tmp_path / "nope.json"))
    assert rb.kind == "absent" and rb.facts is None and rb.problems == ()

    # exact-type admission at the routing consumer: a hostile ReadbackResult
    # subclass is refused (surfaced as the loud read error)
    class HostileRB(rm.ReadbackResult):
        pass
    orig = rm.read_terminal
    rm.read_terminal = lambda op, *, audit_path: HostileRB("absent", None, ())
    try:
        with pytest.raises(rm.MigrationAuditReadError):
            rm._route_delegated(_OP, "migrated", apath, "d")
    finally:
        rm.read_terminal = orig


# ==========================================================================
# I21 — the delegated routing is total
# ==========================================================================

def test_delegated_routing_total(monkeypatch, tmp_path):
    apath = str(tmp_path / "trail.json")

    def with_readback(rb):
        monkeypatch.setattr(rm, "read_terminal",
                            lambda op, *, audit_path: rb)

    for outcome in sorted(rm.OUTCOMES):
        # record-present, bound → facts verbatim (where a terminal cell exists)
        if outcome in rm.TERMINAL_OUTCOMES:
            facts = _valid_facts(outcome)
            with_readback(rm.ReadbackResult("record", facts, ()))
            r = rm._route_delegated(_OP, outcome, apath, "d")
            assert tuple(r)[:5] == (outcome, facts.store_changed,
                                    facts.transaction_committed,
                                    facts.resulting_state,
                                    facts.resulting_version)
            # a VALID record whose outcome DIFFERS from the kernel return →
            # mismatched (external R2-5), never a fact source
            other = "migrated" if outcome != "migrated" else "current"
            with_readback(rm.ReadbackResult("record", _valid_facts(other), ()))
            with pytest.raises(rm.MigrationAuditReadError) as ei:
                rm._route_delegated(_OP, outcome, apath, "d")
            assert ei.value.failure == "mismatched"
        # record-absent × the four no-record outcomes → the fixed rows, NO error
        with_readback(rm.ReadbackResult("absent", None, ()))
        if outcome in rm._NO_RECORD_OUTCOMES:
            r = rm._route_delegated(_OP, outcome, apath, "d")
            assert tuple(r)[:5] == (outcome, False, False, "unknown", None)
            if outcome == "migration-audit-state-unknown":
                assert "MAY be consumed" in r.diagnostic     # retry-unsafe
        else:
            with pytest.raises(rm.MigrationAuditReadError) as ei:
                rm._route_delegated(_OP, outcome, apath, "d")
            assert ei.value.failure == "missing"
        # malformed × ANY outcome → MigrationAuditReadError(malformed)
        with_readback(rm.ReadbackResult("malformed", None, ("boom",)))
        with pytest.raises(rm.MigrationAuditReadError) as ei:
            rm._route_delegated(_OP, outcome, apath, "d")
        assert ei.value.failure == "malformed"


def test_package_escape_propagates_on_both_routes(monkeypatch):
    """External R3-5: PRE-MINT — no readback attempted, no route attributes;
    POST-MINT — the escape-path readback runs and the record is accepted as a
    fact source ONLY when valid AND bound to `package-inconsistent`."""
    # pre-mint: the escape fires during the preflight
    p = _store_at(MINT_BASE)

    def boom(path):
        raise PackageConsistencyError("pre-mint break")
    monkeypatch.setattr(rm, "_preflight_classify", boom)
    with pytest.raises(PackageConsistencyError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    assert not hasattr(ei.value, "readback_route")
    monkeypatch.undo()

    # post-mint: the kernel escapes after the authority was minted
    import veracium.store.migration as mig

    def kernel_boom(path, **kw):
        raise PackageConsistencyError("post-mint break")
    monkeypatch.setattr(mig, "migrate_store", kernel_boom)
    with pytest.raises(PackageConsistencyError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    e = ei.value
    assert e.readback_route == "recorded"
    assert e.recorded_facts.outcome == "package-inconsistent"
    assert not rm.TerminalFacts.problems(e.recorded_facts)
    monkeypatch.undo()

    # post-mint with the terminal write failing → unavailable (readback:
    # missing); the escape STILL propagates unchanged
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(mig, "migrate_store", kernel_boom)
    monkeypatch.setattr(rm, "_write_terminal",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(PackageConsistencyError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    assert ei.value.readback_route == "missing"
    assert ei.value.recorded_facts is None
    monkeypatch.undo()

    # post-mint with a bound record carrying ANOTHER outcome → mismatched
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(mig, "migrate_store", kernel_boom)
    monkeypatch.setattr(
        rm, "read_terminal",
        lambda op, *, audit_path: rm.ReadbackResult(
            "record", _valid_facts("migrated"), ()))
    with pytest.raises(PackageConsistencyError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    assert ei.value.readback_route == "mismatched"


# ==========================================================================
# I17 — audit failures are loud end-to-end
# ==========================================================================

def test_audit_read_error_is_loud(monkeypatch):
    """A missing record under a record-guaranteed outcome, and a malformed
    record under ANY outcome, raise `MigrationAuditReadError` with the derived
    state labeled derived-from-outcome."""
    # missing under a record-guaranteed outcome (the terminal write silently
    # dropped): the migration COMMITTED and the readback finds nothing
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(rm, "_write_terminal", lambda *a, **k: None)
    with pytest.raises(rm.MigrationAuditReadError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    e = ei.value
    assert (e.failure, e.outcome) == ("missing", "migrated")
    assert e.derived_resulting_state == "destination"     # the singleton map
    assert "derived-from-outcome" in str(e)
    monkeypatch.undo()

    # malformed record under any outcome
    p = _store_at(MINT_BASE)

    def corrupt_terminal(apath, op, facts):
        data = {}
        data[op] = {"terminal": {"outcome": facts.outcome,
                                 "from_version": "seven",
                                 "to_version": HEAD, "store_changed": True,
                                 "transaction_committed": True,
                                 "resulting_state": "destination",
                                 "resulting_version": HEAD}}
        with open(apath, "w") as f:
            json.dump(data, f)
    monkeypatch.setattr(rm, "_write_terminal", corrupt_terminal)
    with pytest.raises(rm.MigrationAuditReadError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    assert ei.value.failure == "malformed"


def test_audit_write_error_is_loud(monkeypatch):
    """A terminal-record write failure AFTER the operation ran raises
    `MigrationAuditWriteError` carrying the SAME validated facts the record
    would have — never `migration-failed`, never a silent success."""
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(rm, "_write_terminal",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(rm.MigrationAuditWriteError) as ei:
        rm.run_release_migration(p, host_attestation=ATT)
    e = ei.value
    assert e.facts.outcome == "migrated"
    assert (e.store_changed, e.committed) == (True, True)
    assert e.resulting_state == "destination"
    assert e.resulting_version == HEAD
    assert e.audit_committed is False
    # the store IS migrated — the escape reports it, never hides it
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == HEAD


def test_attempted_write_failure_is_the_no_record_row(monkeypatch):
    """The attempted-record write failing INSIDE the kernel transaction aborts
    it: `migration-audit-unavailable` (False, False, unknown, None), the store
    NOT migrated, no terminal error."""
    p = _store_at(MINT_BASE)
    monkeypatch.setattr(rm, "_write_attempted",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")))
    r = rm.run_release_migration(p, host_attestation=ATT)
    assert tuple(r)[:5] == ("migration-audit-unavailable", False, False,
                            "unknown", None)
    assert sqlite3.connect(p).execute(
        "PRAGMA user_version").fetchone()[0] == MINT_BASE


def test_read_error_carrier_validates():
    e = rm.MigrationAuditReadError(_OP, "missing", "migrated")
    assert e.derived_resulting_state == "destination"
    e = rm.MigrationAuditReadError(_OP, "malformed", "locked")
    assert e.derived_resulting_state == "unknown"
    e = rm.MigrationAuditReadError(_OP, "mismatched", "migration-failed")
    assert e.derived_resulting_state == "unknown"          # non-singleton set
    for bad in [("nope", "missing", "migrated"),
                (_OP, "bogus", "migrated"),
                (_OP, "missing", "not-an-outcome")]:
        with pytest.raises(ValueError):
            rm.MigrationAuditReadError(*bad)


def test_terminal_sidecar_is_append_once(tmp_path):
    apath = str(tmp_path / "trail.json")
    facts = _valid_facts("migrated")
    rm._write_terminal(apath, _OP, facts)
    with pytest.raises(RuntimeError):
        rm._write_terminal(apath, _OP, facts)
    rb = rm.read_terminal(_OP, audit_path=apath)
    assert rb.kind == "record" and rb.facts == facts
