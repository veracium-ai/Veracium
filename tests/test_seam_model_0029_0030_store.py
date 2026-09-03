"""Seam model driver — dev's halves (allocation schedule + restriction
derivation + CurrentState), against the REAL store, sweep and projection.

RULE ZERO: every assertion has a negative control proving it CAN fail, and
the controls are themselves asserted (a control that stops discriminating is
a test failure, not a silent green).

Scope note, stated rather than discovered: the TRANSITIVE restriction case
(an edge in `reach` — retired while in neither `direct` nor `affected`) is
exercised by the 0022 sweep vectors (54, shipped); this model proves the
MEMBERSHIP TEST's shape over the heterogeneous retire population, not the
sweep's closure, which is accepted 0022 ground.
"""
from __future__ import annotations

import sys
import types as _types
import uuid
from pathlib import Path

import pytest

SEAM = Path(__file__).resolve().parents[1] / "specs" / "evidence" / "0029-0030" / "seam_model"
sys.path.insert(0, str(SEAM))

from allocation_schedule import (deferred_batch, immediate_batch,  # noqa: E402
                                 run_two_connection_schedule)
from restriction_derivation import (autocommit_variant,  # noqa: E402
                                    control_affected_misses_the_direct_case,
                                    control_bare_id_fails_open,
                                    control_lift_flips_with_no_row_rewrite,
                                    control_token_moves_on_mutation,
                                    current_state, source_restricted)
from current_state_carrier import (CurrentState, RestrictionVerdict,  # noqa: E402
                                   ScopeCell)
from veracium.scope import Identity, validate_policy  # noqa: E402

from veracium import EvidenceAuthor, SqliteStore  # noqa: E402
from veracium.schema import Edge, Provenance  # noqa: E402
from veracium.scope_linkage import identity_digest_of  # noqa: E402
from veracium.store import revocation as rv  # noqa: E402

U = "u"
AT = "2026-08-31T00:00:00Z"


def _edge(obj, *, source="feed-1"):
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject="user",
                relation="located_at", object=obj,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                                      source_id=source))


@pytest.fixture()
def store(tmp_path):
    s = SqliteStore(str(tmp_path / "seam.db"))
    yield s


# ------------------------------------------------------- allocation (F4) --

def test_immediate_schedule_serializes__deferred_is_the_control(tmp_path):
    """The required schedule yields distinct whole batches with ZERO
    allocation refusals; the forbidden DEFERRED schedule reproduces the
    round-3 reviewer's failure (same maxima read, second dies locked)."""
    ok1, ok2 = run_two_connection_schedule(
        str(tmp_path / "imm.db"), immediate_batch, busy_timeout_ms=5000)
    assert ok1.error is None and ok2.error is None, (ok1.error, ok2.error)
    assert ok1.txn != ok2.txn, "two batches shared a txn"
    assert ok1.maxima_read != ok2.maxima_read, \
        "both connections read the same maxima — the lock came too late"
    assert not (set(ok1.seqs) & set(ok2.seqs)), "seq ranges overlap"

    # NEGATIVE CONTROL — the reviewer's reproduction, kept failing forever:
    bad1, bad2 = run_two_connection_schedule(
        str(tmp_path / "def.db"), deferred_batch, busy_timeout_ms=0)
    losers = [r for r in (bad1, bad2) if r.error is not None]
    assert losers and "locked" in losers[0].error, \
        "the DEFERRED schedule no longer fails — control is vacuous"
    assert bad1.maxima_read == bad2.maxima_read, \
        "deferred no longer reads the same maxima — control is vacuous"


# ---------------------------------------------- restriction (F1/F2, X-1) --

def _revoked_superseded_fixture(store):
    """The F2 cell: an INACTIVE superseded edge whose source stands revoked.
    revoke_source SWEEPS but retires only ACTIVE rows (:734), so the edge's
    reason stays `superseded` — the row carries no trace of the restriction."""
    e = _edge("Boston")
    store.add_edge(e)
    store.invalidate_edge(e.id, AT, "superseded")
    d = identity_digest_of(None, "feed-1", store.local_origin())
    rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    return e, d


def test_typed_membership_restricts__bare_id_is_the_control(store):
    e, d = _revoked_superseded_fixture(store)
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.RESTRICTED, "the F2 cell is not restricted"
    # round-4 F4 -> round-5 F2: a VERDICT — never digests (false attribution),
    # never a bare bool (two values cannot carry "could not compute")
    assert isinstance(got, RestrictionVerdict)
    # row untouched: reason is still superseded (history never rewrites)
    import json
    row = store._conn.execute("SELECT json FROM edges WHERE id=?", (e.id,)).fetchone()[0]
    assert json.loads(row)["invalidation_reason"] == "superseded"
    # NEGATIVE CONTROL — round-3 F1's fail-open, permanent:
    assert_control(control_bare_id_fails_open, store, U, e.id,
                   msg="bare-id membership no longer fails open — control "
                       "is vacuous")


def test_direct_case_is_in_retire__affected_misses_it(store):
    """X-1's live demonstration: the simplest F2 shape (own source revoked)
    is caught by `retire` and can be entirely absent from `affected`."""
    e, _ = _revoked_superseded_fixture(store)
    assert source_restricted(store, U, e.id)
    assert_control(control_affected_misses_the_direct_case, store, U, e.id,
                   msg="affected now covers the direct case — retire it as "
                       "a control only with a fixture where it still "
                       "discriminates")


def test_no_standing_case_is_defined_and_calls_no_sweep(store, monkeypatch):
    """The reviewer's named case: no standing restrictions => frozenset(),
    with ZERO sweep calls — asserted by making any call fail."""
    e = _edge("Paris")
    store.add_edge(e)
    import restriction_derivation as rd
    monkeypatch.setattr(rd, "sweep",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("sweep called with no standing set")))
    assert rd.source_restricted(store, U, e.id) is RestrictionVerdict.CLEAR


def test_lift_flips_the_input_without_touching_the_row(store):
    e, _ = _revoked_superseded_fixture(store)
    assert_control(control_lift_flips_with_no_row_rewrite,
                   store, U, e.id, AT,
                   msg="lift no longer flips the input with the row "
                       "untouched")


# ------------------------------------------------ CurrentState (F2, one read)

def test_current_state_is_bound_and_token_moves(store):
    e, d = _revoked_superseded_fixture(store)
    cs = current_state(store, U, e.id)
    assert isinstance(cs, CurrentState)
    assert (cs.user_id, cs.edge_id) == (U, e.id), "carrier identity unbound"
    assert cs.current_raw is not None
    assert cs.source_restricted is RestrictionVerdict.RESTRICTED
    # NEGATIVE CONTROL — the token must move on ANY user mutation; this
    # assertion fails the day a mutator skips the write-counter bump:
    assert_control(control_token_moves_on_mutation,
                   store, U, e.id, lambda: store.add_edge(_edge("Lyon")),
                   msg="a mutation did not advance the read token")


def test_missing_row_is_a_defined_carrier_state(store):
    """Defensive totality: no row -> current_raw is None, restriction still
    computed, identity still bound (absence never grants; 0030 owns the
    classification of this shape)."""
    cs = current_state(store, U, "e-never-existed")
    assert cs.current_raw is None
    assert cs.source_restricted is RestrictionVerdict.CLEAR
    assert (cs.user_id, cs.edge_id) == (U, "e-never-existed")


# --------------------------------------- round-4 F1: the one consistent read

def test_autocommit_straddle_is_real__the_round4_control(store, tmp_path):
    """The reviewer's reproduction, made a permanent negative control: the
    ROUND-3 design (consecutive autocommit reads) returns a MIXED WORLD when
    a second store instance commits between the reads."""
    e = _edge("Boston")
    store.add_edge(e)
    t0 = current_state(store, U, e.id).read_token
    import json
    from veracium import SqliteStore as _S
    other = _S(str(store._path))
    try:
        def between():
            other.invalidate_edge(e.id, AT, "superseded")
        cs = autocommit_variant(store, U, e.id, between=between)
    finally:
        other.close()
    row_state = json.loads(cs.current_raw)
    assert cs.read_token == t0, "token was read before the foreign write"
    assert row_state["invalidated_at"] is not None, \
        "row was read after it — the straddle is no longer reproducible " \
        "and this control is vacuous"


@pytest.mark.parametrize("mode", ["delete", "wal"])
def test_transactional_read_is_one_world__both_journal_modes(store, mode):
    """Round-5 F3: the guaranteed property is ONE WORLD PER WINDOW, and it
    is MODE-NEUTRAL; the MECHANISM is not. A foreign writer forced in
    immediately before the scope decision (the reviewer's point) is
    REFUSED in rollback mode (exclusion) and PROCEEDS in WAL mode while
    the reader keeps its SNAPSHOT — the reviewer executed the WAL half
    against round 5's "writers refused" claim and was right. Both modes
    must carry one world out; each mode's specific mechanism is asserted
    so neither can silently become the other."""
    import json
    mode_now = store._conn.execute(f"PRAGMA journal_mode={mode}").fetchone()[0]
    assert mode in mode_now, f"journal mode not applied: {mode_now}"
    e = _edge("Boston")
    store.add_edge(e)
    from veracium import SqliteStore as _S
    import sqlite3 as _sq
    other = _S(str(store._path), busy_timeout_ms=50)
    attempted = {}
    def interleave():
        try:
            other.invalidate_edge(e.id, AT, "superseded")
            attempted["outcome"] = "succeeded"
        except _sq.OperationalError as ex:
            attempted["outcome"] = f"refused: {ex}"
    try:
        policy = validate_policy({}, cross_scope_visible=False,
                                 local_origin=store.local_origin())
        cs = current_state(store, U, e.id,
                           principal=Identity(origin=None, source_id="mb-a"),
                           policy=policy, _interleave=interleave)
        # THE MODE-NEUTRAL PROPERTY: every carried value is the OLD world.
        row_state = json.loads(cs.current_raw)
        assert row_state["invalidated_at"] is None, "row from another world"
        assert cs.source_restricted is RestrictionVerdict.CLEAR
        assert cs.scope_cell is not None, "scope cell computed in-txn"
        # THE MODE-SPECIFIC MECHANISM:
        if mode == "delete":
            assert "refused" in attempted.get("outcome", ""), \
                f"rollback mode no longer excludes: {attempted}"
            other.invalidate_edge(e.id, AT, "superseded")  # window closed
        else:
            assert attempted.get("outcome") == "succeeded", \
                f"WAL mode no longer admits the writer: {attempted}"
        # AFTER the window: a fresh read sees the new world, token moved.
        cs2 = current_state(store, U, e.id)
        assert json.loads(cs2.current_raw)["invalidated_at"] is not None
        assert cs2.read_token > cs.read_token, "token moved with the world"
    finally:
        other.close()


# ------------------- round-5 F2: the end-to-end matrix, no raise anywhere

def _tamper(store, edge_id):
    """The reviewer's malformed persistence: source_id=[] written at the
    DB level (the store cannot emit it; tamper is the stated honest origin)."""
    import json as _j
    row = store._conn.execute("SELECT json FROM edges WHERE id=?",
                              (edge_id,)).fetchone()[0]
    m = _j.loads(row)
    m["provenance"]["source_id"] = []
    store._conn.execute("UPDATE edges SET json=? WHERE id=?",
                        (_j.dumps(m), edge_id))
    store._conn.commit()


@pytest.mark.parametrize("with_principal", [False, True])
@pytest.mark.parametrize("with_standing", [False, True])
@pytest.mark.parametrize("malformed", ["well_formed", "probe_row", "other_row"])
def test_end_to_end_matrix_never_raises(store, with_principal, with_standing,
                                        malformed):
    """Round-5 F2's required cross: principal x standing x malformation,
    driven through current_state. NO cell may raise; every cell's verdict
    and scope-cell family is pinned. The sharpest cells: a malformed row —
    even an UNRELATED one — with a standing restriction yields
    UNDETERMINABLE (returned, never raised), and a malformed probed row
    with a principal yields the FAIL-CLOSED HIDDEN cell."""
    probe = _edge("Boston")
    store.add_edge(probe)
    other = _edge("Paris", source="feed-2")
    store.add_edge(other)
    if with_standing:
        d = identity_digest_of(None, "feed-1", store.local_origin())
        rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    if malformed == "probe_row":
        _tamper(store, probe.id)
    elif malformed == "other_row":
        _tamper(store, other.id)

    kwargs = {}
    if with_principal:
        kwargs = dict(principal=Identity(origin=None, source_id="mb-a"),
                      policy=validate_policy({}, cross_scope_visible=False,
                                             local_origin=store.local_origin()))
    cs = current_state(store, U, probe.id, **kwargs)   # must never raise

    # the verdict, per cell:
    if not with_standing:
        assert cs.source_restricted is RestrictionVerdict.CLEAR
    elif malformed == "well_formed":
        assert cs.source_restricted is RestrictionVerdict.RESTRICTED, \
            "probe is sourced from the revoked feed-1"
    else:
        assert cs.source_restricted is RestrictionVerdict.UNDETERMINABLE, \
            "a malformed row anywhere makes the projection unbuildable"

    # the scope cell, per cell:
    if not with_principal:
        assert cs.scope_cell is None, "None means NO PRINCIPAL, distinct"
    elif malformed == "probe_row":
        assert cs.scope_cell.fail_closed and not cs.scope_cell.visible, \
            "malformed probed row with a principal -> fail-closed HIDDEN"
        assert cs.scope_cell.principal == (None, "mb-a"), \
            "even the fail-closed cell states who it was computed for"
    else:
        assert cs.scope_cell is not None and not cs.scope_cell.fail_closed
        assert cs.scope_cell.principal == (None, "mb-a"), \
            "the cell is bound to its principal (the C-4 pattern, predictive)"

    # the raw text is verbatim regardless (V-VERBATIM's consumer side):
    assert cs.current_raw is not None


def test_undeterminable_is_returned_not_raised__control(store):
    """Rule zero for the third value: the pre-round-5 design RAISED here.
    The control proves the raise is real (the projection genuinely cannot
    be built) so the catch is load-bearing, not decorative."""
    e = _edge("Boston")
    store.add_edge(e)
    d = identity_digest_of(None, "feed-1", store.local_origin())
    rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    _tamper(store, e.id)
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        from restriction_derivation import project_store as _ps
        _ps(store, U)          # the raw projection DOES raise — the fabric
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


# --------------------- round-6 F1/F3: carried == direct; the decode boundary

def test_carried_decision_equals_direct__every_reachable_row(store):
    """Round-6 F1: the carried cell must EQUAL the direct decision, compared
    per decision-table row reachable in this fixture (own-source visible,
    foreign-source cross). The reviewer's probe — carried says groundable
    where direct refuses — becomes the permanent discriminating test, and
    the type assertion pins the double-wrap shut (shape is a str/None,
    never a tuple)."""
    import sys as _s
    SEAM2 = str(SEAM)
    if SEAM2 not in _s.path:
        _s.path.insert(0, SEAM2)
    from raw_adapter import adapt
    from veracium.scope_read import ScopeView
    e_own = _edge("Boston", source="mb-a")
    e_cross = _edge("Paris", source="other-mailbox")
    store.add_edge(e_own); store.add_edge(e_cross)
    policy = validate_policy({}, cross_scope_visible=True,
                             local_origin=store.local_origin())
    principal = Identity(origin=None, source_id="mb-a")
    for e in (e_own, e_cross):
        cs = current_state(store, U, e.id, principal=principal, policy=policy)
        row = store._conn.execute("SELECT json FROM edges WHERE id=?",
                                  (e.id,)).fetchone()[0]
        adapted = adapt(row, expect_id=e.id, expect_user=U)
        direct = ScopeView(store, U, principal, policy).decision(adapted)
        assert (cs.scope_cell.visible, cs.scope_cell.shape) == direct, \
            f"carried != direct for {e.id}: {cs.scope_cell} vs {direct}"
        assert not isinstance(cs.scope_cell.shape, tuple), \
            "the round-6 double-wrap is back"


def test_control_double_wrap_misclassifies(store):
    """Rule zero for F1: reproduce the OLD fill (whole pair into .shape) and
    assert the carried/direct comparison CATCHES it — the discriminating
    test can fail."""
    import sys as _s
    if str(SEAM) not in _s.path:
        _s.path.insert(0, str(SEAM))
    from raw_adapter import adapt
    from veracium.scope_read import ScopeView
    e = _edge("Boston", source="mb-a")
    store.add_edge(e)
    policy = validate_policy({}, cross_scope_visible=True,
                             local_origin=store.local_origin())
    principal = Identity(origin=None, source_id="mb-a")
    row = store._conn.execute("SELECT json FROM edges WHERE id=?",
                              (e.id,)).fetchone()[0]
    adapted = adapt(row, expect_id=e.id, expect_user=U)
    view = ScopeView(store, U, principal, policy)
    direct = view.decision(adapted)
    old_style = ScopeCell(visible=view.visible(adapted),
                          shape=view.decision(adapted),   # THE BUG: whole pair
                          principal=(None, "mb-a"))
    assert (old_style.visible, old_style.shape) != direct, \
        "the double-wrap no longer differs — control is vacuous"


def test_malformed_ledger_payload_yields_undeterminable(store):
    """Round-6 F3: project_store also parses LEDGER payloads (json.loads at
    revocation.py:232) — a malformed one raised JSONDecodeError through the
    ValidationError-only catch. Now: UNDETERMINABLE, returned."""
    e, d = _revoked_superseded_fixture(store)
    store._conn.execute(
        "INSERT INTO contribution_ledger (id, user_id, survivor_type, "
        "survivor_id, site, identity_digest, evidence_ref_digest, payload, "
        "op_key, created_at) VALUES ('cl-bad', ?, 'edge', ?, 'absorb', "
        "NULL, NULL, '}{ not json', NULL, ?)", (U, e.id, AT))
    store._conn.commit()
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


def test_failures_outside_the_interpretation_region_propagate__control(
        store, monkeypatch):
    """Rule zero for the boundary's narrowness, MOVED to the honest edge
    (round-8 F2): the interpretation region (`project_store`) is now TOTAL
    — any Exception inside it is by definition a persisted-data failure —
    so the old injection site (project_store raising RuntimeError) no
    longer discriminates. What must still PROPAGATE is a failure OUTSIDE
    the region: the sweep raising outside its declared RevocationError
    contract is a genuine bug, and catching it would hide that bug behind
    an honest-looking verdict."""
    e, d = _revoked_superseded_fixture(store)
    import restriction_derivation as rd
    def boom(*a, **k):
        raise RuntimeError("a real bug, not a persisted-data failure")
    monkeypatch.setattr(rd, "sweep", boom)
    with pytest.raises(RuntimeError):
        rd.source_restricted(store, U, e.id)


# ------------- round-7 F2: the persisted-data family is wider than decode

def test_invalid_utf8_ledger_payload_yields_undeterminable(store):
    """Round-7: an invalid-UTF-8 ledger payload raises UnicodeDecodeError
    BEFORE json ever runs — a decode family round 6's enumeration missed.
    The raise is proven real first (rule zero), then the boundary returns."""
    import sqlite3 as _sq
    e, d = _revoked_superseded_fixture(store)
    store._conn.execute(
        "INSERT INTO contribution_ledger (id, user_id, survivor_type, "
        "survivor_id, site, identity_digest, evidence_ref_digest, payload, "
        "op_key, created_at) VALUES ('cl-utf8', ?, 'edge', ?, 'absorb', "
        "NULL, NULL, ?, NULL, ?)",
        (U, e.id, _sq.Binary(b"\xff\xfe{ bad"), AT))
    store._conn.commit()
    import pytest as _pt
    from restriction_derivation import project_store as _ps
    with _pt.raises(UnicodeDecodeError):
        _ps(store, U)                       # the raw raise is real
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


def test_corrupt_persisted_revocation_row_yields_undeterminable(store):
    """Round-7: a corrupted PERSISTED revocation row raises RevocationError
    from the SWEEP's own validation — outside project_store entirely, so
    the boundary must cover the sweep call. At this call site every sweep
    input is persisted, so the refusal is store-unreadability."""
    e, d = _revoked_superseded_fixture(store)
    store._conn.execute(
        "UPDATE source_revocations SET at='not-a-time' WHERE user_id=?", (U,))
    store._conn.commit()
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


# ------------- round-8 F2: the enumeration under-counted AGAIN; the region
# is now total, and these two cells are the permanent record of why.

def test_deeply_nested_payload_yields_undeterminable(store):
    """THE REVIEWER'S ROUND-8 PROBE, permanent: a stored ledger payload of
    10,000 nested JSON arrays makes json raise RecursionError — a family
    no round's enumeration had named, which is the point: round 6 listed
    three types, round 7 added two more, round 8 proved the list still
    leaked. The fix stops patching the list (the region is total). NOTE
    the type relationship that makes this cell and the narrowness control
    BOTH true: RecursionError IS a RuntimeError subclass, and the control
    proves RuntimeError propagates — OUTSIDE the region. What changed in
    round 8 is the boundary's definition (a region, not a type list), so
    the same type is caught inside project_store and propagated outside
    it. The discriminator is WHERE, no longer WHAT."""
    import sys as _sys
    e, d = _revoked_superseded_fixture(store)
    depth = 10_000
    assert depth * 4 > _sys.getrecursionlimit()   # the probe stays lethal
    store._conn.execute(
        "INSERT INTO contribution_ledger (id, user_id, survivor_type, "
        "survivor_id, site, identity_digest, evidence_ref_digest, payload, "
        "op_key, created_at) VALUES ('cl-deep', ?, 'edge', ?, 'absorb', "
        "NULL, NULL, ?, NULL, ?)",
        (U, e.id, "[" * depth + "]" * depth, AT))
    store._conn.commit()
    import pytest as _pt
    from restriction_derivation import project_store as _ps
    with _pt.raises(RecursionError):
        _ps(store, U)                       # the raw raise is real
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


def test_blob_digest_revocation_row_yields_undeterminable(store):
    """The class EXHAUSTED past the named finding (checklist item 9: the
    reviewer's next mutant, written now): reading and ORDERING the standing
    set interprets persisted values too. A revocation row whose
    identity_digest holds a BLOB (SQLite TEXT affinity stores a BLOB
    unchanged — 0031's affinity rule, live here) yields a mixed bytes/str
    standing set, and min() over it raises TypeError. Before round 8 that
    read had NO boundary at all and the raise escaped as a crash."""
    import sqlite3 as _sq
    e, d = _revoked_superseded_fixture(store)
    (max_seq,) = store._conn.execute(
        "SELECT COALESCE(MAX(seq), 0) FROM source_revocations "
        "WHERE user_id=?", (U,)).fetchone()
    store._conn.execute(
        "INSERT INTO source_revocations (user_id, seq, identity_digest, "
        "action, at, reason) VALUES (?, ?, ?, 'revoke', ?, 'planted')",
        (U, max_seq + 1, _sq.Binary(b"f" * 64), AT))
    store._conn.commit()
    import pytest as _pt
    from restriction_derivation import standing_revocations as _sr
    standing = _sr(store._conn, U)
    with _pt.raises(TypeError):
        min(standing)                       # the raw raise is real
    got = source_restricted(store, U, e.id)
    assert got is RestrictionVerdict.UNDETERMINABLE


# ------------- round-8 F4: the every-control sweep, made EXHAUSTIVE.
# It lives in THIS file now (the round-7 version lived in the main driver
# and is removed from it): the sweep's home is arbitrary, and the store
# driver is where the modules it newly covers are exercised.

def _seam_modules():
    """Every module in the seam_model DIRECTORY — discovered, not listed.
    Round-8 F4: the round-7 checker named (current_state_carrier,
    raw_adapter) — two of the four model modules — so the reviewer planted
    a control in restriction_derivation and the checker passed. A
    maintained registry can rot the same way; a directory listing cannot
    omit a module the directory contains."""
    import importlib
    return [importlib.import_module(p.stem)
            for p in sorted(SEAM.glob("*.py"))
            if not p.stem.startswith("_")]


from binding_census import (BINDING_CONSTRUCTS, EXECUTED,  # noqa: E402
                            assert_control, impostor_of,
                            census_source as _census_source)


#: THE SESSION-START INVENTORY (round-17 joint F1): captured at IMPORT
#: time — before any test executes — this tuple is the obligation the
#: runtime gate verifies at session end. The reviewer's framing, taken:
#: the beginning of the session defines what must remain present; the
#: end verifies both PRESERVATION and EXECUTION. Without it, the gate's
#: discovery filters (callable, module-match) silently OMITTED a control
#: replaced with a non-callable, a foreign function, or nothing at all —
#: success reported over a reduced set. A change must produce an
#: explicit failure, never remove an obligation.
_EXPECTED_CONTROLS = tuple(sorted(
    (m.__name__, n)
    for m in _seam_modules()
    for n in vars(m)
    if n.startswith("control_")))


def _invoked_identities():
    """The identity census over BOTH drivers; shadow violations fail here.
    The protected-module set is DERIVED from the seam_model directory (no
    hardcoded registry to rot — the round-7 lesson, held)."""
    here = Path(__file__).resolve().parent
    protected_mods = {m.__name__ for m in _seam_modules()}
    credited = set()
    for f in ("test_seam_model_0029_0030.py",
              "test_seam_model_0029_0030_store.py"):
        c, viol = _census_source((here / f).read_text(), protected_mods)
        assert not viol, f"{f}: {viol}"
        credited.update(c)
    return credited


def _unasserted_controls(modules, credited):
    import inspect
    return [f"{m.__name__}.{n}" for m in modules
            for n, o in sorted(vars(m).items())
            if n.startswith("control_") and inspect.isfunction(o)
            and o.__module__ == m.__name__
            and (m.__name__, n) not in credited]


def test_every_control_in_the_seam_model_is_asserted():
    """THE CLASS, closed a FOURTH level up (round-7 F4 -> round-8 F4 ->
    round-9 F2 -> round-10 F3). Round 7 scanned two of four modules; round
    8 discovered every module but grepped TEXT; round 9 required a Call
    node but matched terminal NAMES, so any callee spelled `control_x`
    credited the seam control; round 10 requires IDENTITY — the call must
    resolve through the driver's imports to THAT module's function, and
    rebinding a control to another name is a census violation outright."""
    missing = _unasserted_controls(_seam_modules(), _invoked_identities())
    assert not missing, f"control(s) defined but INVOKED by nothing: {missing}"


# The round-9 F2 decoy, deliberately mentioned here and NEVER invoked:
# control_mentioned_never_invoked. Under the round-8 text grep this comment
# alone would have satisfied the census; the negatives below prove the
# identity census is fooled by neither mention nor name-collision.

def test_the_control_sweep_can_fail__control():
    """Rule zero for the sweep, PERMANENT, at the round-10 semantics: a
    synthetic module's control whose name is PRESENT in this file's text
    (the decoy comment above) but never invoked through an import of that
    module must be FLAGGED."""
    import types
    name = "control_mentioned_never_invoked"
    mod = types.ModuleType("synthetic_seam_module")
    def planted():
        return True
    planted.__name__ = name
    planted.__qualname__ = name
    planted.__module__ = mod.__name__
    setattr(mod, name, planted)
    here_text = Path(__file__).read_text()
    assert name in here_text, "the decoy mention vanished — restore the comment"
    missing = _unasserted_controls([mod], _invoked_identities())
    assert missing == [f"{mod.__name__}.{name}"], \
        "a mentioned-but-never-invoked control was not flagged — the census " \
        "has regressed"


def test_same_name_foreign_call_does_not_credit__control():
    """THE REVIEWER'S ROUND-10 CONSTRUCTION, permanent: a call to an
    UNRELATED function that happens to be spelled like a control must not
    credit the seam control. The round-9 census failed exactly this (a
    terminal-name set has no notion of WHOSE control_x was called); the
    identity census resolves through imports, and a local def or foreign
    import is not an import of the seam module."""
    src = (
        "from other_module import control_x\n"
        "def control_y():\n"
        "    return True\n"
        "control_x()\n"          # foreign module's control_x — not ours
        "control_y()\n"          # local def — bound to no module
    )
    credited, violations = _census_source(src)
    assert violations == []
    assert ("other_module", "control_x") in credited
    assert not any(m == "seam_module" for m, _ in credited), \
        "a same-name foreign call credited the seam module — the census " \
        "has regressed to terminal names"


def test_alias_rebinding_is_a_census_violation__control():
    """The other half of the reviewer's round-10 finding: alias or dispatch
    invocation of the GENUINE control is invisible to any static census —
    so the grammar is CONSTRAINED instead (the 0031 inventory sweep's
    move): rebinding an imported control to another name is a VIOLATION
    the census returns and the driver census asserts empty. Both rebind
    shapes covered: the from-import binding and the module-attribute."""
    src1 = ("from restriction_derivation import control_bare_id_fails_open\n"
            "f = control_bare_id_fails_open\n"
            "f()\n")
    _, viol1 = _census_source(src1)
    assert viol1 and "rebound" in viol1[0]
    src2 = ("import restriction_derivation as rd\n"
            "g = rd.control_token_moves_on_mutation\n")
    _, viol2 = _census_source(src2)
    assert viol2 and "rebound" in viol2[0]
    # and a NON-control rebinding is not a violation (the constraint is
    # scoped to what the census must see, not a style rule):
    src3 = ("from restriction_derivation import current_state\n"
            "cs = current_state\n")
    _, viol3 = _census_source(src3)
    assert viol3 == []


# ------------- round-8 F1: the pair rule, end-to-end through the REAL producer

def test_producer_cell_replayed_without_its_view_is_refused(store):
    """The pair rule (round-8 F1) exercised with a REAL producer cell, not a
    hand-built one: current_state with a principal emits a scope cell; that
    exact cell replayed through bind with NO view is IDENTITY_UNBOUND —
    principal-bearing or not, because a viewless cell is the same influence
    channel (visible/shape at steps 2/10) minus attribution. The bare
    producer output (no principal => no cell) still binds viewless, which
    is the rule's other half: the producer and the rule agree, so the
    refusal costs no legitimate path anything."""
    from current_state_carrier import (BOUND, IDENTITY_UNBOUND, Envelope,
                                       RawEdgeState, bind)
    e = _edge("Boston")
    store.add_edge(e)
    kwargs = dict(principal=Identity(origin=None, source_id="mb-a"),
                  policy=validate_policy({}, cross_scope_visible=False,
                                         local_origin=store.local_origin()))
    with_cell = current_state(store, U, e.id, **kwargs)
    assert with_cell.scope_cell is not None, "producer emitted no cell"
    bare = current_state(store, U, e.id)
    assert bare.scope_cell is None, "the producer's no-principal path " \
        "emitted a cell — the pair rule's cost claim just became false"
    env = Envelope(U, e.id)
    snap = RawEdgeState(e.id, U, with_cell.current_raw)
    assert bind(env, snap, with_cell, None) == IDENTITY_UNBOUND, \
        "a viewless producer cell bound — the pair rule is not enforced"
    # The round-8 HALF, discriminating against the round-7 rule (which this
    # exact shape slipped past): the SAME producer cell with its principal
    # stripped — round 8's argument made literal, the same influence channel
    # minus attribution — must be refused just as firmly.
    pc = with_cell.scope_cell
    stripped = CurrentState(U, e.id, with_cell.current_raw,
                            with_cell.source_restricted, with_cell.read_token,
                            ScopeCell(pc.visible, pc.shape, pc.fail_closed,
                                      None))
    assert bind(env, snap, stripped, None) == IDENTITY_UNBOUND, \
        "the producer cell minus attribution bound viewless — the round-7 " \
        "permissiveness is back"
    assert bind(env, snap, bare, None) == BOUND, \
        "a bare viewless record no longer binds — the rule over-narrowed"


# ------------- round-9 F1: persisted-value totality, one layer deeper — the
# ledger payload's SIDES. The wrapper was validated (round 7); the fields
# _fold consumes were not, and the reviewer's {"base":{},"contributor":{}}
# reached base["valid_from"] as a KeyError.

def _absorption_tamper_fixture(store, payload_obj, *, revoke_first):
    """A survivor with TWO absorption ledger rows — one contributor's source
    revoked, one standing (the reviewer's construction: recompute runs with
    live sides). `revoke_first` sequences the corruption BEFORE or AFTER the
    revocation, because the two orders fail at DIFFERENT shipped surfaces."""
    import json as _j
    surv = _edge("Boston")
    store.add_edge(surv)
    d_revoked = identity_digest_of(None, "feed-2", store.local_origin())
    if revoke_first:
        rv.revoke_source(store, U, d_revoked, "revoke", "seam-model", AT)
    payload = _j.dumps(payload_obj)
    for i, dg in enumerate((d_revoked,
                            identity_digest_of(None, "feed-3",
                                               store.local_origin()))):
        store._conn.execute(
            "INSERT INTO contribution_ledger (id, user_id, survivor_type, "
            "survivor_id, site, identity_digest, evidence_ref_digest, "
            "payload, op_key, created_at, contributor_type, contributor_ref) "
            "VALUES (?, ?, 'edge', ?, 'absorption', ?, NULL, ?, NULL, ?, "
            "'edge', ?)",
            (f"cl-r9-{i}", U, surv.id, dg, payload, AT, f"c-{i}"))
    store._conn.commit()
    if not revoke_first:
        return surv, d_revoked
    return surv, d_revoked


def test_reviewers_empty_sides_payload_yields_undeterminable(store):
    """THE ROUND-9 PROBE, permanent (order B — revocation stands, then the
    ledger rots): {"base":{},"contributor":{}} is VALID JSON and a valid
    wrapper, and pre-fix it escaped source_restricted as
    KeyError('valid_from') from _fold. The raw refusal is proven real first
    (rule zero), then the boundary returns UNDETERMINABLE."""
    surv, d = _absorption_tamper_fixture(
        store, {"base": {}, "contributor": {}}, revoke_first=True)
    from restriction_derivation import _build_projection
    from veracium.store.revocation_sweep import RevocationError as _RE
    from veracium.store.revocation_sweep import sweep as _sweep
    with pytest.raises(_RE):
        _sweep(_build_projection(store, U), d)   # the raw refusal is real
    assert source_restricted(store, U, surv.id) \
        is RestrictionVerdict.UNDETERMINABLE


def test_corrupt_ledger_refuses_revocation_with_a_typed_error(store):
    """Order A — the ledger rots BEFORE the revocation: pre-fix,
    revoke_source ITSELF crashed with KeyError (the sweep runs inside the
    revocation transaction), which is worse than the verdict's framing.
    Post-fix the shipped verb refuses with its DECLARED RevocationError and
    R19 rolls back: no revocation row lands."""
    from veracium.store.revocation_sweep import RevocationError as _RE
    surv, d = _absorption_tamper_fixture(
        store, {"base": {}, "contributor": {}}, revoke_first=False)
    with pytest.raises(_RE):
        rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    from restriction_derivation import standing_revocations as _sr
    assert not _sr(store._conn, U), \
        "the refused revocation left a standing row — R19 did not roll back"


_GOOD_SIDE = {"valid_from": "2026-01-01T00:00:00Z",
              "observed_at": "2026-01-02T00:00:00Z",
              "confidence": 0.5, "disclosure": "mentionable"}

# Round-10 F1 widened the matrix past types into DOMAINS: the round-9 fix
# validated that confidence was a number and stopped one recursion short of
# validating it was a PROBABILITY — the reviewer's 2.0 survived a revoke+lift
# and the stored edge failed its own model. Domain variants apply per field:
# confidence gains range/NaN/inf; the datetimes gain the unparseable string
# (the SAME laundering one field over — Edge.valid_from is datetime-typed).
# Round-11 F1 widened the datetime variants past parseability into the
# CANONICAL WRITER FORM: parseable non-canonical forms (the reviewer's
# offset pair, naive, date-only, padded precision) folded lexicographically
# to chronologically WRONG values — both implementations agreeing on the
# wrong answer. All refuse now; the fold compares parsed instants.
_DT_VARIANTS = ("not-a-datetime", "offset", "naive", "date-only",
                "padded-precision")
_DOMAIN_VARIANTS = {
    "confidence": ("above-domain", "below-domain", "nan", "infinity"),
    "valid_from": _DT_VARIANTS,
    "observed_at": _DT_VARIANTS,
}
_DOMAIN_VALUES = {"above-domain": 2.0, "below-domain": -0.5,
                  "nan": float("nan"), "infinity": float("inf"),
                  "not-a-datetime": "not-a-date",
                  "offset": "2025-12-31T23:30:00-01:00",
                  "naive": "2026-01-01T00:00:00",
                  "date-only": "2026-01-01",
                  "padded-precision": "2026-01-01T00:00:00.000000Z"}
SIDE_MUTANTS = [
    (side, field, variant)
    for side in ("base", "contributor")
    for field in ("valid_from", "observed_at", "confidence")
    for variant in (("absent", "wrong-type") + _DOMAIN_VARIANTS[field])
]


@pytest.mark.parametrize(
    "side,field,variant", SIDE_MUTANTS,
    ids=[f"{s}-{f}-{v}" for s, f, v in SIDE_MUTANTS])
def test_every_consumed_side_field_is_validated(store, side, field, variant):
    """The reviewer's NEXT mutant, written now (checklist item 9): the fix
    must hold for every field _fold consumes, on BOTH sides, in BOTH failure
    shapes — absent (KeyError pre-fix) and wrong-typed (TypeError from
    min()/max() one mutant over, which the round-9 finding did not name and
    the shipped writer's scalar-only validation would not catch). 12 cells;
    each returns UNDETERMINABLE, nothing escapes."""
    good = dict(_GOOD_SIDE)
    bad = dict(_GOOD_SIDE)
    if variant == "absent":
        del bad[field]
    elif variant == "wrong-type":
        bad[field] = 3 if field != "confidence" else "high"
    else:
        bad[field] = _DOMAIN_VALUES[variant]
    payload = {"base": good, "contributor": good}
    payload[side] = bad
    surv, d = _absorption_tamper_fixture(store, payload, revoke_first=True)
    assert source_restricted(store, U, surv.id) \
        is RestrictionVerdict.UNDETERMINABLE


# ------------- round-9 F3: presence precedes equality, with REAL material

def test_principal_less_pair_from_producer_material_is_refused(store):
    """Round-9 F3, end-to-end shape: v20's rule checked EQUALITY and both-None
    satisfied `!=` while naming no principal at all — the only hole left
    (half-None was already refused as mismatch). The producer cannot emit a
    principal-less cell (both ScopeCell sites carry a real (origin,
    source_id) tuple) and production's ScopeView RAISES on a non-groupable
    principal (scope_read.py:307), so this refusal costs no legitimate path
    — but the model's constructors stay DELIBERATELY wide so this test can
    build the illegal shape and prove rule 0 refuses it at the one site a
    direct constructor cannot route around."""
    from current_state_carrier import (BOUND, IDENTITY_UNBOUND, Envelope,
                                       RawEdgeState, View, bind)
    e = _edge("Boston")
    store.add_edge(e)
    kwargs = dict(principal=Identity(origin=None, source_id="mb-a"),
                  policy=validate_policy({}, cross_scope_visible=False,
                                         local_origin=store.local_origin()))
    with_cell = current_state(store, U, e.id, **kwargs)
    pc = with_cell.scope_cell
    assert pc.principal is not None, \
        "the producer emitted a principal-less cell — the cost claim broke"
    stripped = CurrentState(U, e.id, with_cell.current_raw,
                            with_cell.source_restricted, with_cell.read_token,
                            ScopeCell(pc.visible, pc.shape, pc.fail_closed,
                                      None))
    env = Envelope(U, e.id)
    snap = RawEdgeState(e.id, U, with_cell.current_raw)
    assert bind(env, snap, stripped, View(U, principal=None)) \
        == IDENTITY_UNBOUND, \
        "a present pair naming NO principal bound — presence must precede " \
        "equality"
    assert bind(env, snap, with_cell,
                View(U, principal=pc.principal)) == BOUND, \
        "the legitimate paired case no longer binds — the rule over-narrowed"


# ------------- round-10 F1: the reviewer's revoke/lift laundering, refused

def test_out_of_domain_confidence_refuses_revoke_and_lift(store):
    """THE ROUND-10 PROBE, permanent, at the REAL store: confidence 2.0 in a
    contributor side survived the round-9 TYPE check, rode a revoke and a
    LIFT into a committed recompute effect, and the stored edge then failed
    its own Edge.model_validate — the sweep laundering an out-of-domain
    persisted value into a live record. Both operations must now REFUSE
    with the declared error and roll back completely.

    Revoke half: the corrupt side is present before any revocation —
    revoke_source refuses, R19 rolls back, no standing row lands.
    Lift half: the revocation stands FIRST (good payload), the ledger then
    rots to 2.0 — the lift refuses and the source STAYS revoked (a refused
    lift must not half-lift)."""
    import json as _j
    from veracium.store.revocation_sweep import RevocationError as _RE
    from restriction_derivation import standing_revocations as _sr
    GOOD = dict(_GOOD_SIDE)
    EVIL = dict(_GOOD_SIDE, confidence=2.0)

    # -- revoke half
    surv, d = _absorption_tamper_fixture(
        store, {"base": GOOD, "contributor": EVIL}, revoke_first=False)
    with pytest.raises(_RE):
        rv.revoke_source(store, U, d, "revoke", "seam-model", AT)
    assert not _sr(store._conn, U), "refused revoke left a standing row"

    # -- lift half: make the store clean again, revoke on GOOD payload,
    # then rot the ledger and attempt the lift
    store._conn.execute("DELETE FROM contribution_ledger WHERE user_id=?",
                        (U,))
    store._conn.commit()
    surv2, d2 = _absorption_tamper_fixture(
        store, {"base": GOOD, "contributor": GOOD}, revoke_first=True)
    assert _sr(store._conn, U), "fixture failed to establish the revocation"
    store._conn.execute(
        "UPDATE contribution_ledger SET payload=? WHERE user_id=?",
        (_j.dumps({"base": GOOD, "contributor": EVIL}), U))
    store._conn.commit()
    with pytest.raises(_RE):
        rv.revoke_source(store, U, d2, "lift", "seam-model", AT)
    assert _sr(store._conn, U), \
        "the refused lift removed the standing revocation — a half-lift"
    # and the survivor's stored edge still validates (nothing was committed)
    row = store._conn.execute("SELECT json FROM edges WHERE id=?",
                              (surv2.id,)).fetchone()[0]
    Edge.model_validate_json(row)


SHADOW_PROBES = [
    # (case, source, needs_protected_module)
    ("reviewer-def-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "def control_bare_id_fails_open():\n"
        "    return True\n"
        "control_bare_id_fails_open()\n"), False),
    ("reviewer-module-reassignment", (
        "import restriction_derivation as rd\n"
        "rd = replacement_object\n"
        "rd.control_token_moves_on_mutation()\n"), True),
    ("class-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "class control_bare_id_fails_open: pass\n"), False),
    ("parameter-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "def f(control_bare_id_fails_open):\n"
        "    return control_bare_id_fails_open()\n"), False),
    ("for-target-shadow", (
        "import restriction_derivation as rd\n"
        "for rd in items:\n"
        "    pass\n"), True),
    ("with-as-shadow", (
        "import restriction_derivation as rd\n"
        "with open('x') as rd:\n"
        "    pass\n"), True),
    ("except-as-shadow", (
        "import restriction_derivation as rd\n"
        "try:\n    pass\n"
        "except Exception as rd:\n    pass\n"), True),
    ("walrus-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "if (control_bare_id_fails_open := other()):\n"
        "    pass\n"), False),
    ("plain-assignment-over-imported-name", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "control_bare_id_fails_open = lambda: True\n"), False),
    ("unpack-shadow", (
        "import restriction_derivation as rd\n"
        "rd, other = things\n"), True),
    ("conflicting-reimport", (
        "import restriction_derivation as rd\n"
        "import somewhere_else as rd\n"), True),
    # round-12 F1: the reviewer's two probes VERBATIM, then the rest of the
    # family the closure named (nested patterns reached by walk), then the
    # async/annotated forms the inventory-coverage test demands probes for.
    ("reviewer-lambda-parameter (round-12)", (
        "import restriction_derivation as rd\n"
        "invoke = lambda rd: rd.control_token_moves_on_mutation()\n"
        "invoke(replacement_object)\n"), True),
    ("reviewer-match-capture (round-12)", (
        "import restriction_derivation as rd\n"
        "match replacement_object:\n"
        "    case rd:\n"
        "        rd.control_token_moves_on_mutation()\n"), True),
    ("match-star-capture", (
        "import restriction_derivation as rd\n"
        "match x:\n"
        "    case [first, *rd]:\n        pass\n"), True),
    ("match-mapping-rest-capture", (
        "import restriction_derivation as rd\n"
        "match x:\n"
        "    case {'k': 1, **rd}:\n        pass\n"), True),
    ("match-nested-class-and-or-pattern", (
        "import restriction_derivation as rd\n"
        "match x:\n"
        "    case Point(x=rd) | [rd]:\n        pass\n"), True),
    ("async-def-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "async def control_bare_id_fails_open():\n    pass\n"), False),
    ("annotated-assignment-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "control_bare_id_fails_open: int = 1\n"), False),
    ("augmented-assignment-shadow", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "control_bare_id_fails_open += 1\n"), False),
    ("async-for-target-shadow", (
        "import restriction_derivation as rd\n"
        "async def f():\n"
        "    async for rd in xs:\n        pass\n"), True),
    ("comprehension-target-shadow", (
        "import restriction_derivation as rd\n"
        "ys = [1 for rd in xs]\n"), True),
    ("async-with-target-shadow", (
        "import restriction_derivation as rd\n"
        "async def f():\n"
        "    async with y as rd:\n        pass\n"), True),
    # round-13: ImportFrom as the CAUSAL conflicting re-import (the reviewer's
    # causality point — an initial from-import satisfied appears-somewhere
    # coverage while a different node supplied every probe's violation).
    ("conflicting-refrom-import", (
        "from restriction_derivation import control_bare_id_fails_open\n"
        "from elsewhere import other as control_bare_id_fails_open\n"), False),
]

import sys as _s
if _s.version_info >= (3, 12):
    # round-13 joint F1: the reviewer's two TypeAlias probes VERBATIM. The
    # construct is UNAVAILABLE below 3.12 (a parser fact), never excluded.
    SHADOW_PROBES.extend([
        ("reviewer-typealias-module-shadow (round-13)", (
            "import restriction_derivation as rd\n"
            "type rd = int\n"
            "rd.control_token_moves_on_mutation()\n"), True),
        ("reviewer-typealias-control-shadow (round-13)", (
            "from restriction_derivation import "
            "control_token_moves_on_mutation\n"
            "type control_token_moves_on_mutation = int\n"
            "control_token_moves_on_mutation()\n"), False),
    ])


@pytest.mark.parametrize("case,src,needs_mod", SHADOW_PROBES,
                         ids=[p[0] for p in SHADOW_PROBES])
def test_shadowing_is_a_census_violation__controls(case, src, needs_mod):
    """Round-11 F2's permanent negatives — the reviewer's two probes
    VERBATIM first, then their full binding-construct list: the round-10
    census remembered import bindings and never applied later name binding,
    so a def-shadow or module reassignment left it crediting the ORIGINAL
    control while runtime invoked a replacement. Scope-aware resolution is
    a compiler's job; the constrained grammar refuses EVERY shadow of a
    protected binding instead, and each construct here must VIOLATE."""
    mods = {"restriction_derivation"} if needs_mod else None
    _, violations = _census_source(src, mods)
    assert violations, f"{case}: shadow accepted silently — the census " \
                       f"has regressed to import-time-only binding"


def test_same_module_local_reimport_is_not_a_violation__control():
    """The constraint's scope, asserted: a function-local re-import of the
    SAME module under the SAME alias binds the same identity (the drivers'
    own standing pattern) and must NOT violate — the grammar refuses
    shadows, not style."""
    src = ("import restriction_derivation as rd\n"
           "def f():\n"
           "    import restriction_derivation as rd\n"
           "    return rd.control_bare_id_fails_open\n")
    _, violations = _census_source(src, {"restriction_derivation"})
    assert violations == [], violations


def test_the_binding_inventory_is_covered_causally():
    """Round-13 joint F1's coverage upgrade (the reviewer taking the
    round-13 README's own attack point #1): appears-somewhere coverage let
    an initial import satisfy ImportFrom while a different node supplied
    every probe's actual violation. Coverage is now CAUSAL — every handled
    construct must have a probe whose returned violation NAMES that
    construct as the shadowing source (the census brackets the AST class
    in each violation). A construct the running interpreter cannot parse
    (TypeAlias below 3.12) is UNAVAILABLE — skipped with its reason —
    never semantically excluded."""
    import ast as _ast
    for name in BINDING_CONSTRUCTS["handled"]:
        if getattr(_ast, name, None) is None:
            continue                    # unavailable on this interpreter
        tag = f"[{name}]"
        causal = False
        for _, src, needs in SHADOW_PROBES:
            try:
                mods = {"restriction_derivation"} if needs else None
                _, viol = _census_source(src, mods)
            except SyntaxError:
                continue
            if any(tag in v for v in viol):
                causal = True
                break
        assert causal, \
            f"{name}: no probe's violation names it as the shadowing " \
            f"source — coverage regressed to appears-somewhere"


def test_the_binding_inventory_is_covered_and_current():
    """Round-12 F1's mechanical-reviewability ask, executable: the census's
    BINDING_CONSTRUCTS table is the inventory of Python's name-introducing
    constructs; every HANDLED entry must appear in at least one probe of the
    battery above (all of which must VIOLATE — the battery test's contract),
    every ast.Match* class must be inventoried so a future pattern kind
    fails loudly instead of slipping the family a third time, and nothing
    is both handled and excluded. The "every binding construct" claim is
    now a table plus two assertions, not a sentence."""
    import ast as _ast
    handled = set(BINDING_CONSTRUCTS["handled"])
    excluded = set(BINDING_CONSTRUCTS["excluded"])
    assert not (handled & excluded)
    match_classes = {n for n in dir(_ast)
                     if n.startswith("Match") and n != "Match"
                     and isinstance(getattr(_ast, n), type)}
    assert match_classes <= handled | excluded, \
        f"uninventoried pattern kinds: {match_classes - (handled | excluded)}"
    for name in handled:
        cls = getattr(_ast, name, None)
        if cls is None:
            # UNAVAILABLE on this interpreter (TypeAlias below 3.12) — a
            # parser fact, not an exclusion; the 3.12+ CI lanes execute the
            # construct's probes. (Round-13's own CI red: this assert used
            # to REQUIRE availability, which the 3.10/3.11 lanes correctly
            # refused the day TypeAlias joined handled.)
            continue
        def _parses(src):
            try:
                return _ast.parse(src)
            except SyntaxError:
                return _ast.parse("pass")
        assert any(
            any(isinstance(n, cls) for n in _ast.walk(_parses(src)))
            for _, src, _ in SHADOW_PROBES), \
            f"{name} has no probe in the shadow battery"


# ------------- round-14 F1: the RUNTIME execution gate — the census ladder's
# static side closed at its ceiling (the reviewer's `if False:` call credited
# as "actually called"), so the execution claim now rides runtime evidence.

def test_every_control_was_executed_and_asserted():
    """THE RUNTIME GATE (round-14 joint F1): every discovered control_*
    callable must have EXECUTED in this test session with its result
    ASSERTED — recorded by `assert_control` at the moment the assertion
    passed, keyed by callable identity. The static census is RESCOPED to
    source hygiene; AST call identity credits dead branches (`if False:`,
    TYPE_CHECKING, uncalled functions) and can never carry this claim.

    Ordering: a conftest hook anchors this test LAST after pytest-randomly
    shuffles, so every control-invoking test has run. Scope: a partial run
    that invokes some controls but not others FAILS here by design — an
    unexecuted control is unexecuted, and the gate refuses to guess why;
    the prescribed surfaces (both drivers; the full suite; CI) always
    execute everything.

    THE OBLIGATION IS SESSION-START, THE VERIFICATION SESSION-END
    (round-17 joint F1): `_EXPECTED_CONTROLS`, captured at import before
    any test executes, defines what must remain present; this gate then
    validates all four clauses per obligation — present, an ordinary
    function, of its own module, and the PRESENT identity executed. Fresh
    re-resolution alone was not enough: a control replaced with a
    non-callable, a foreign function, or nothing at all fell out of the
    discovery FILTERS before validation, and the gate reported success
    over a reduced set. A change fails explicitly; it never removes an
    obligation. Additions join the obligation under the same clauses.

    TRUST BOUNDARY, stated beside the topology contract (round-17
    ruling): this gate is evidence tooling within a COOPERATING process;
    it is not a defense against arbitrary mutation by its own process —
    code that rebinds the gate's inventory or registry is inside the
    boundary the topology statement already draws."""
    import os
    assert os.environ.get("PYTEST_XDIST_WORKER") is None, (
        "UNSUPPORTED TOPOLOGY: the runtime registry is in-process session "
        "state and this is an xdist worker — registrars and the gate can "
        "land in different processes, so no single process holds complete "
        "evidence. Aggregate execution identities across processes before "
        "applying the gate, or run the seam surface single-process "
        "(round-15 adjudication: detect and fail explicitly, never skip)")
    # FRESH re-resolution at gate time (round-15's also-consider, taken):
    # later module-level reassignment cannot silently change what
    # "discovered control" means — the gate compares the objects the
    # modules hold NOW against the objects that actually ran.
    # ROUND-17 joint F1: validate EVERY session-start obligation before
    # any filter — the four clauses, in the reviewer's order. Discovery
    # filters silently omitted a changed control (non-callable, foreign
    # module, removed); the inventory turns each omission into a named
    # failure. A same-module replacement passes ONLY if the newly present
    # function itself was executed (clause 4 on the PRESENT identity).
    mods = {m.__name__: m for m in _seam_modules()}
    _MISSING = object()
    problems = []
    present = []
    for mod_name, attr in _EXPECTED_CONTROLS:
        m = mods.get(mod_name)
        obj = vars(m).get(attr, _MISSING) if m is not None else _MISSING
        if obj is _MISSING:
            problems.append(f"{mod_name}.{attr}: attribute REMOVED — an "
                            f"obligation cannot be deleted")
        elif not isinstance(obj, _types.FunctionType):
            problems.append(f"{mod_name}.{attr}: replaced with a "
                            f"non-function ({type(obj).__name__})")
        elif getattr(obj, "__module__", None) != mod_name:
            problems.append(f"{mod_name}.{attr}: replaced with a function "
                            f"from module {getattr(obj, '__module__', None)!r}")
        else:
            present.append(obj)
    assert not problems, (
        "session-start control obligations violated (round-17 joint F1 — "
        "a change fails explicitly, it never removes an obligation): "
        + "; ".join(problems))
    # ADDITIONS: control-named attributes not in the inventory join the
    # obligation (they must be ordinary same-module functions — the
    # round-16 door — and must have executed like any control).
    expected = set(_EXPECTED_CONTROLS)
    added = [(mn, n, vars(m)[n]) for mn, m in mods.items()
             for n in vars(m)
             if n.startswith("control_") and (mn, n) not in expected]
    nonfunctions = [(mn, n, type(f).__name__) for mn, n, f in added
                    if not isinstance(f, _types.FunctionType)
                    or getattr(f, "__module__", None) != mn]
    assert not nonfunctions, (
        f"added control_* object(s) that are not ordinary functions of "
        f"their own module: {nonfunctions} — arbitrary callables can "
        f"define __eq__/__hash__, so only types.FunctionType is admitted "
        f"to the identity contract (round-16 joint F1); rewrite the "
        f"control as a def or rename it")
    discovered = present + [f for _, _, f in added]
    # The selection convenience sits AFTER the structural clauses (1-3 and
    # the additions door), which need no registry: a direct call with an
    # empty registry must still fail loudly on a planted non-function —
    # placing this skip first made that outcome ORDER-DEPENDENT under
    # pytest-randomly (caught at the round-18 gating run: 2479/9 on one
    # seed vs 2480/8 deterministic — the found-in-fix class).
    if not EXECUTED:
        pytest.skip("no control executions recorded — the control-invoking "
                    "tests were not selected in this session; run the full "
                    "seam surface to enforce the runtime gate (the skip is "
                    "a selection convenience, NEVER positive evidence — "
                    "round-15 adjudication)")
    # ROUND-16 joint F1, the comparison half: membership is an id() lookup
    # against a registry that RETAINS its references (a held reference pins
    # the id for the session, so no reuse), never set membership — sets
    # compare by __eq__/__hash__, and the reviewer's two distinct
    # equal-comparing instances satisfied each other's entry.
    unexecuted = [f for f in discovered if id(f) not in EXECUTED]
    assert not unexecuted, (
        f"control(s) discovered but NEVER EXECUTED-AND-ASSERTED this "
        f"session (by OBJECT identity — metadata cannot satisfy this): "
        f"{sorted(f'{f.__module__}.{f.__name__}' for f in unexecuted)} "
        f"— a syntactic reference is not runtime evidence (round-14), and "
        f"a copied name is not the callable (round-15)")


def test_dead_branch_credits_static_but_not_runtime__control():
    """THE REVIEWER'S ROUND-14 CONSTRUCTION, permanent, as the two gates'
    discriminating pair: the STATIC hygiene census CREDITS a call under
    `if False:` (asserted — that is its ceiling, stated), while the RUNTIME
    registry records nothing for it (asserted — that is why the execution
    claim lives there). One probe, both verdicts, the division of labor
    executable."""
    import types
    name = "control_dead_branch_probe"
    mod = types.ModuleType("synthetic_dead_module")
    def planted():
        return True
    planted.__name__ = name
    planted.__qualname__ = name
    planted.__module__ = mod.__name__
    setattr(mod, name, planted)
    src = ("import synthetic_dead_module as sdm\n"
           "if False:\n"
           f"    sdm.{name}()\n")
    credited, violations = _census_source(src, {"synthetic_dead_module"})
    assert ("synthetic_dead_module", name) in credited, \
        "the static census stopped crediting the dead call — its ceiling " \
        "claim in the runtime gate's docstring is now stale; update both"
    assert violations == []
    assert id(planted) not in EXECUTED, \
        "the runtime registry recorded a call that never ran"


def test_metadata_impostor_cannot_satisfy_the_registry__control():
    """THE REVIEWER'S ROUND-15 CONSTRUCTION, permanent, all four parts: a
    discovered real control; a DISTINCT callable wearing its copied
    module/name/qualname metadata (via the reusable `impostor_of` probe —
    their feedback, so identity tests need no seam drivers); execution and
    successful assertion of ONLY the impostor; and a gate-view that still
    identifies the real control as unexecuted. Under the round-14 metadata
    key the impostor SATISFIED the real control's entry (asserted below as
    the contrast — the metadata copy is real); under object identity it
    never can: a copied name is not the callable."""
    from restriction_derivation import control_bare_id_fails_open as real
    imp = impostor_of(real)
    assert imp is not real
    assert (imp.__module__, imp.__name__) == (real.__module__, real.__name__), \
        "the impostor's metadata copy failed — the contrast is gone"
    before = set(EXECUTED)                        # snapshot of id keys
    try:
        assert_control(imp)                       # only the impostor runs
        assert id(imp) in EXECUTED, \
            "the impostor's own execution must record"
        # the REAL control gains nothing from the impostor's run:
        assert (id(real) in EXECUTED) == (id(real) in before), \
            "a metadata twin satisfied the real control's registry entry — " \
            "the registry has regressed to descriptive names (round-15)"
    finally:
        EXECUTED.pop(id(imp), None)               # probe hygiene: the
        # impostor is not a discovered control; leaving it recorded would
        # be harmless to the gate but untidy in the registry


class _EqualCallable:
    """THE REVIEWER'S ROUND-16 CONSTRUCTION: distinct instances that
    compare and hash EQUAL — legal Python, and exactly what set membership
    cannot tell apart. Kept as a class (not a fixture) so the probe below
    reads as the reviewer wrote it."""
    def __call__(self, *a, **k):
        return True
    def __eq__(self, other):
        return isinstance(other, _EqualCallable)
    def __hash__(self):
        return 0xC0FFEE


def test_equal_comparing_callables_cannot_satisfy_each_other__control():
    """THE REVIEWER'S ROUND-16 CONSTRUCTION, permanent, both halves of the
    closure asserted:

    THE DOOR (the definitional half): `assert_control` REFUSES a callable
    instance outright — a control IS an ordinary function
    (types.FunctionType, enforced), because anything else can define
    __eq__/__hash__ and equality is not identity.

    THE COMPARISON (the identity half): even placed directly into the
    registry mechanics — the reviewer's move, done first, bypassing the
    door — recording one of two distinct equal-comparing instances leaves
    the other reported as unexecuted, because membership is an id()
    lookup against retained references, with no path through
    user-definable equality. The CONTRAST is asserted too: a set of the
    same registry values still reports the twin present, which is exactly
    the round-16 finding and why the registry is not a set."""
    a, b = _EqualCallable(), _EqualCallable()
    assert a is not b and a == b and hash(a) == hash(b), \
        "the construction lost its premise — distinct but equal-comparing"

    with pytest.raises(AssertionError, match="ordinary function"):
        assert_control(a)                     # the door refuses, loudly
    assert id(a) not in EXECUTED, "a refused callable must not record"

    before = set(EXECUTED)
    try:
        EXECUTED[id(a)] = a                   # the reviewer's bypass
        assert id(b) not in EXECUTED, (
            "an equal-comparing twin satisfied the identity registry — "
            "membership has regressed to equality (round-16 joint F1)")
        # the contrast: equality-based membership WOULD be satisfied,
        # which is the reproduced finding and the reason for the id keys
        assert b in set(EXECUTED.values()), \
            "the contrast is gone — the twins no longer compare equal"
    finally:
        for k in set(EXECUTED) - before:
            EXECUTED.pop(k, None)             # probe hygiene


def test_changed_controls_fail_explicitly_not_silently__controls(
        monkeypatch):
    """THE REVIEWER'S ROUND-17 CONSTRUCTION, permanent, all four cases —
    run against the REAL gate over a controlled one-module inventory (a
    synthetic module + a monkeypatched session-start inventory, so each
    case exercises the gate's own clauses end-to-end, mid-session,
    without depending on the rest of the surface having run):

      1. replacement with a non-callable value    -> explicit failure
      2. replacement with a foreign-module function -> explicit failure
      3. removal of the attribute                 -> explicit failure
      4. replacement with a NEW valid same-module function:
           unexecuted -> explicit failure;
           executed-and-asserted -> the gate ACCEPTS it (the reviewer's
           "unless the newly present function itself was executed").

    Before round 17 the discovery filters silently OMITTED cases 1-3 —
    the gate reported success over a reduced set; the session-start
    inventory turns every change into a named failure: a change never
    removes an obligation."""
    import types as _t
    fake = _t.ModuleType("fake_seam_mod")

    def control_probe():
        return True
    control_probe.__module__ = "fake_seam_mod"
    fake.control_probe = control_probe
    monkeypatch.setattr(sys.modules[__name__], "_EXPECTED_CONTROLS",
                        (("fake_seam_mod", "control_probe"),))
    monkeypatch.setattr(sys.modules[__name__], "_seam_modules",
                        lambda: [fake])
    keys_before = set(EXECUTED)
    try:
        assert_control(control_probe)             # the obligation ran

        fake.control_probe = 42                   # case 1: non-callable
        with pytest.raises(AssertionError, match="non-function"):
            test_every_control_was_executed_and_asserted()

        import json                               # case 2: foreign module
        fake.control_probe = json.dumps
        with pytest.raises(AssertionError,
                           match="function from module 'json'"):
            test_every_control_was_executed_and_asserted()

        del fake.control_probe                    # case 3: removed
        with pytest.raises(AssertionError, match="REMOVED"):
            test_every_control_was_executed_and_asserted()

        def _fresh():                             # case 4: valid same-module
            return True
        _fresh.__module__ = "fake_seam_mod"
        _fresh.__name__ = "control_probe"
        fake.control_probe = _fresh
        with pytest.raises(AssertionError,
                           match="NEVER EXECUTED-AND-ASSERTED"):
            test_every_control_was_executed_and_asserted()  # unexecuted
        assert_control(_fresh)                    # ...but executed is
        test_every_control_was_executed_and_asserted()      # permitted

        fake.control_probe = control_probe        # the honest baseline
        test_every_control_was_executed_and_asserted()
    finally:
        for k in set(EXECUTED) - keys_before:
            EXECUTED.pop(k, None)                 # probe hygiene


def test_nonfunction_control_fails_the_gate_loudly__control(monkeypatch):
    """The next mutant, claimed before it can be offered (round-16's
    definitional ask, enforced at DISCOVERY too): a callable instance
    named control_* planted in a seam module makes the runtime gate fail
    LOUDLY at its type check — never silently narrowed out of discovery
    (which would under-protect: an unexecuted control invisible to the
    gate), and never admitted to the identity contract."""
    import restriction_derivation as rd
    planted = _EqualCallable()
    monkeypatch.setattr(rd, "control_planted_instance", planted,
                        raising=False)
    monkeypatch.setattr(
        _EqualCallable, "__module__", rd.__name__, raising=False)
    with pytest.raises(AssertionError, match="not ordinary functions"):
        test_every_control_was_executed_and_asserted()
