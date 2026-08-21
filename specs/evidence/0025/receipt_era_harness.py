"""The cross-era receipt contract through the LIVE product paths — 0025 §4b-v (the consolidated contract).

Round 5 (R5-1) moved this harness onto the shipped schema; round 6 (R6-1)
found it still never REACHED either product comparison site — it fabricated
a version-2 receipt the shipped validators refuse on sight, and its two
"site" functions wrapped the harness's own matrix, never
`apply_supersession()` / `apply_supersession_plan()`. This version drives
the REAL paths:

  1. a real `SqliteStore`, a real supersession, a real committed VERSION-4
     receipt — request_digest under the SHIPPED v1 domain, response carrying
     the exact effect fields (validate_receipt_state passes because the
     PRODUCT wrote the row);
  2. a live lost-response retry through the PUBLIC phase-1 path → REPLAY;
  3. the era BITE on the live path: the same stored row re-digested under
     the v2 domain makes the shipped phase-1 comparison raise "DIFFERENT
     request" — the defect §4b-v exists to fix, demonstrated through the
     shipped topology, not asserted;
  4. the legal SNAPSHOT-LESS receipt state (request_digest NULL, version 4
     — R6-2's cell) retried live: phase 1 branch-3 falls through and the
     STORE-level phase-2 OUTCOME comparison governs — which REFUSES the
     differing post-commit re-plan (the shipped identity-less semantics;
     the domain rule stays out of it, nothing double-applies);
  5. the LIVE store-level phase-2 replay and era bite via same-plan
     resubmission (round 7, R7-2 — the branch the reviewer drove first);
  6. the §4b-v matrix over states READ BACK from real migrated rows,
     including the read-side inconsistency cells.

What this harness cannot do, stated plainly: the v2 comparison logic is
0025's implementation and does not exist in the product yet, so cells that
require it run against the proposed `same_request` applied to REAL rows
the product wrote; reachability of both sites and the bite are proven on
the live code.

Run:  $PY specs/evidence/0025/receipt_era_harness.py
"""
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve()
                       .parents[3] / "src"))
try:
    from veracium.contribution import (REQUEST_DIGEST_DOMAIN,
                                       raw_request_snapshot, request_digest)
    from veracium.graph import apply_supersession
    from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                                 EvidenceAuthor, Provenance, Volatility)
    from veracium.store.base import (ReceiptSchemaBoundaryError,
                                     SupersessionIntegrityError)
    from veracium.store.sqlite import SqliteStore
except ImportError as e:
    print(f"REFUSED: cannot import the shipped construction ({e}). Run "
          f"under an interpreter with the pinned test dependencies — the "
          f"offline launcher's .venv-offline/bin/python — from the "
          f"extraction root.")
    sys.exit(2)

DOMAIN_V1 = REQUEST_DIGEST_DOMAIN
DOMAIN_V2 = b"veracium.supersession-request.v2"
CLOSED_SET = {DOMAIN_V1.decode(), DOMAIN_V2.decode()}
PROPOSED_ALTER = ("ALTER TABLE supersession_operations "
                  "ADD COLUMN request_digest_domain TEXT")

U = "u-era"
NOW = datetime.now(timezone.utc)


def digest_under(domain: bytes, snapshot: dict) -> str:
    body = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(domain + body.encode("utf-8")).hexdigest()


class EraRefusal(Exception):
    """§4b-v fail-closed: a receipt this code cannot interpret."""


def same_request(stored_digest, stored_domain, snapshot):
    """The §4b-v matrix over (request_digest, request_digest_domain, the
    submitted snapshot) — the pre-D2 boundary and the outcome-only path
    are the shipped code's and PRECEDE/FOLLOW this rule (vectors 4-5 show
    them live). Returns True/False for a digest comparison; raises on the
    fail-closed cells; returns None when no request comparison is possible
    (digest or snapshot absent → the shipped outcome comparison governs)."""
    if stored_domain is not None and stored_domain not in CLOSED_SET:
        raise EraRefusal(f"uninterpretable digest domain: {stored_domain!r}")
    if stored_digest is None:
        if stored_domain is not None:
            raise EraRefusal("domain stamped on a digest-less receipt — "
                             "the writer invariant forbids it")
        return None                       # outcome-only comparison governs
    if snapshot is None:
        return None                       # no submitted identity: outcome-only
    if stored_domain is None:             # legacy: BOTH domains
        return stored_digest in (digest_under(DOMAIN_V1, snapshot),
                                 digest_under(DOMAIN_V2, snapshot))
    return stored_digest == digest_under(stored_domain.encode(), snapshot)


# ---- the live fixture ------------------------------------------------------

def _edge(eid, obj, days_ago=1):
    t = NOW - timedelta(days=days_ago)
    return Edge(id=eid, user_id=U, subject="user", relation="works_as",
                object=obj, volatility=Volatility.SLOW, valid_from=t,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      disclosure=Disclosure.MENTIONABLE,
                                      confidence=0.7, observed_at=t))


def live_store_with_committed_receipt():
    """A REAL supersession through the public path; the product writes the
    version-4 receipt itself."""
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc = _edge("e-inc", "carpenter")
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert not getattr(counts, "replayed", False)
    return s, inc


def fetch_receipt_row(store, op_id):
    return store._conn.execute(
        "SELECT request_digest, outcome_digest_version, response FROM "
        "supersession_operations WHERE user_id=? AND operation_id=?",
        (U, op_id)).fetchone()


# ---- vectors ---------------------------------------------------------------

def vector_the_product_writes_a_valid_v4_receipt_under_v1():
    s, inc = live_store_with_committed_receipt()
    rd, ver, resp = fetch_receipt_row(s, f"sup-{inc.id}")
    assert ver == 4 and resp is not None
    # the stored digest IS the shipped v1-domain digest of the raw snapshot
    assert rd == request_digest(raw_request_snapshot(inc))
    assert rd == digest_under(DOMAIN_V1, raw_request_snapshot(inc))


def vector_live_phase1_replays_the_legitimate_retry():
    s, inc = live_store_with_committed_receipt()
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)  # the retry
    assert counts.replayed is True          # phase 1, branch 1, LIVE


def vector_the_era_bite_on_the_live_path():
    """The defect §4b-v fixes, demonstrated through the shipped topology:
    the SAME request, digested under the v2 domain, is classified as a
    DIFFERENT request by today's phase-1 comparison."""
    s, inc = live_store_with_committed_receipt()
    v2_digest = digest_under(DOMAIN_V2, raw_request_snapshot(inc))
    s._conn.execute("UPDATE supersession_operations SET request_digest=? "
                    "WHERE user_id=? AND operation_id=?",
                    (v2_digest, U, f"sup-{inc.id}"))
    s._conn.commit()
    try:
        apply_supersession(s, inc, DEFAULT_RELATIONS)
        raise AssertionError("the live path accepted a cross-era digest")
    except SupersessionIntegrityError as e:
        assert "DIFFERENT request" in str(e)   # phase 1, branch 2, LIVE
    # and the proposed rule replays it: legacy NULL domain, dual-domain
    assert same_request(v2_digest, None, raw_request_snapshot(inc)) is True


def vector_snapshotless_receipt_takes_the_outcome_path_live():
    """R6-2's legal cell: (request_digest NULL, version 4, json). A live
    retry passes phase-1 branch 3 (NULL digest is never "different") and
    the STORE-level phase-2 OUTCOME comparison governs — the shipped
    identity-less semantics, which here REFUSES because the post-commit
    re-plan is a different logical operation (exactly the limitation
    request identity exists to remove; 0014 R8-1). The domain rule plays
    no part in this cell, no state is double-applied, and §4b-v states
    this behaviour rather than inventing a kinder one."""
    s, inc = live_store_with_committed_receipt()
    s._conn.execute("UPDATE supersession_operations SET request_digest=NULL "
                    "WHERE user_id=? AND operation_id=?",
                    (U, f"sup-{inc.id}"))
    s._conn.commit()
    before = [e.id for e in s.edges(U, active_only=True,
                                    include_quarantined=True)]
    try:
        apply_supersession(s, inc, DEFAULT_RELATIONS)     # live retry
        raise AssertionError("expected the shipped outcome comparison to "
                             "refuse the differing re-plan")
    except SupersessionIntegrityError as e:
        assert "DIFFERENT logical operation" in str(e)    # phase 2, LIVE
    after = [e.id for e in s.edges(U, active_only=True,
                                   include_quarantined=True)]
    assert before == after                   # refused, never double-applied
    # the proposed matrix stays out of it: digest absent + domain NULL →
    # None (the shipped outcome rule governs, unchanged)
    assert same_request(None, None, raw_request_snapshot(inc)) is None


def vector_live_phase2_replay_and_era_bite():
    """Round 7, R7-2 — the branch the reviewer drove first: the STORE-level
    phase-2 comparison with BOTH digests present. The same plan resubmitted
    directly to apply_supersession_plan() replays under v1; the stored
    digest rewritten under the v2 domain makes the SAME resubmission raise
    DIFFERENT request — the phase-2 era bite, live."""
    from veracium.graph import _build_supersession_plan
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc = _edge("e-inc", "carpenter")
    plan, _ = _build_supersession_plan(s, inc, DEFAULT_RELATIONS,
                                       f"sup-{inc.id}")
    plan.raw_request = raw_request_snapshot(inc)
    r1 = s.apply_supersession_plan(plan)          # commits, writes receipt
    r2 = s.apply_supersession_plan(plan)          # SAME plan: lost-response
    assert getattr(r2, "replayed", False) is True # phase 2 replay, LIVE
    v2_digest = digest_under(DOMAIN_V2, raw_request_snapshot(inc))
    s._conn.execute("UPDATE supersession_operations SET request_digest=? "
                    "WHERE user_id=? AND operation_id=?",
                    (v2_digest, U, f"sup-{inc.id}"))
    s._conn.commit()
    try:
        s.apply_supersession_plan(plan)
        raise AssertionError("phase 2 accepted a cross-era digest")
    except SupersessionIntegrityError as e:
        assert "DIFFERENT request" in str(e)      # phase 2 era bite, LIVE
    # the proposed rule replays it: migrated NULL domain, dual-domain
    assert same_request(v2_digest, None, raw_request_snapshot(inc)) is True


def vector_phase2_pre_d2_precedes_all_domain_logic():
    """Round 9, R9-1: accepted 0016 requires the pre-D2 boundary at BOTH
    phases, BEFORE any domain validation or digest computation. A version-3
    receipt with a POISONED domain value must raise the boundary error —
    never the domain refusal, never a digest comparison — at the live
    store-level path."""
    from veracium.graph import _build_supersession_plan
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc = _edge("e-inc", "carpenter")
    plan, _ = _build_supersession_plan(s, inc, DEFAULT_RELATIONS,
                                       f"sup-{inc.id}")
    plan.raw_request = raw_request_snapshot(inc)
    s.apply_supersession_plan(plan)
    s._conn.execute(PROPOSED_ALTER)
    # a pre-D2 receipt wearing a poisoned domain: the boundary must win
    s._conn.execute("UPDATE supersession_operations SET "
                    "outcome_digest_version=3, request_digest_domain=? "
                    "WHERE user_id=? AND operation_id=?",
                    ("garbage-domain", U, f"sup-{inc.id}"))
    s._conn.commit()
    try:
        s.apply_supersession_plan(plan)
        raise AssertionError("a pre-D2 receipt was not refused on sight")
    except ReceiptSchemaBoundaryError:
        pass          # the boundary, not EraRefusal, not a digest compare
    # and the same precedence at the public phase-1 path
    try:
        apply_supersession(s, inc, DEFAULT_RELATIONS)
        raise AssertionError("phase 1 accepted a pre-D2 receipt")
    except ReceiptSchemaBoundaryError:
        pass


def vector_the_product_matrix_on_real_migrated_rows():
    """§4b-v over the REAL migrated table: stored digest × submitted
    snapshot × domain, including the writer invariant's fail-closed cells."""
    s, inc = live_store_with_committed_receipt()
    s._conn.execute(PROPOSED_ALTER)
    snap = raw_request_snapshot(inc)
    op = f"sup-{inc.id}"

    def row_state(op_id):
        # R7-2: the matrix consumes states READ BACK from the row, never
        # literals passed around the store
        return s._conn.execute(
            "SELECT request_digest, request_digest_domain FROM "
            "supersession_operations WHERE user_id=? AND operation_id=?",
            (U, op_id)).fetchone()

    def set_state(op_id, digest, domain):
        s._conn.execute("UPDATE supersession_operations SET "
                        "request_digest=?, request_digest_domain=? "
                        "WHERE user_id=? AND operation_id=?",
                        (digest, domain, U, op_id))
        s._conn.commit()

    # digest present, domain NULL (post-migration legacy) → dual-domain
    rd, dom = row_state(op)
    assert dom is None
    assert same_request(rd, dom, snap) is True
    assert same_request(rd, dom, dict(snap, id="other")) is False
    # digest present, valid v2 domain → that domain only
    set_state(op, digest_under(DOMAIN_V2, snap), DOMAIN_V2.decode())
    rd, dom = row_state(op)
    assert same_request(rd, dom, snap) is True
    set_state(op, digest_under(DOMAIN_V1, snap), DOMAIN_V2.decode())
    rd, dom = row_state(op)
    assert same_request(rd, dom, snap) is False
    # digest present, snapshot ABSENT → outcome-only; unknown domains refuse
    set_state(op, digest_under(DOMAIN_V1, snap), DOMAIN_V1.decode())
    rd, dom = row_state(op)
    assert same_request(rd, dom, None) is None
    for bad in ("v2", "", "veracium.supersession-request.v9"):
        set_state(op, digest_under(DOMAIN_V1, snap), bad)
        rd, dom = row_state(op)
        try:
            same_request(rd, dom, None)
            raise AssertionError(f"not refused: {bad!r}")
        except EraRefusal:
            pass
    # digest ABSENT: domain NULL → outcome-only; domain present → refuse
    set_state(op, None, None)
    rd, dom = row_state(op)
    assert same_request(rd, dom, snap) is None
    for bad_dom in (DOMAIN_V2.decode(), "garbage"):
        set_state(op, None, bad_dom)
        rd, dom = row_state(op)
        try:
            same_request(rd, dom, snap)
            raise AssertionError(f"not refused: digest-less + {bad_dom!r}")
        except EraRefusal:
            pass


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors: live phase-1 and phase-2 replay+bite, "
          f"pre-D2 precedence over a poisoned domain at both phases, "
          f"snapshot-less outcome-refusal, the §4b-v matrix over "
          f"row-read states")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
