"""The cross-era receipt contract, LIVE — specs/0025 §4b-v, implemented.

Through review rounds 3-11 this harness evolved from an abstract matrix to
live-path evidence of the DEFECT (a legitimate cross-era retry classified
as a DIFFERENT request). With 0025 implemented, the same vectors now prove
the FIX: the product stamps the v2 domain on new digest-bearing receipts,
replays legitimate retries across the era boundary at BOTH comparison
sites, refuses the fail-closed cells with the named error, and keeps the
pre-D2 boundary ahead of every domain and digest operation. The deeper
per-surface obligations live in tests/test_0025_receipt_states.py (X13);
this file remains the reviewer-facing, self-contained walk.

Run:  $PY specs/evidence/0025/receipt_era_harness.py
"""
import pathlib
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve()
                       .parents[3] / "src"))
try:
    from veracium.contribution import (CURRENT_DIGEST_DOMAIN,
                                       REQUEST_DIGEST_DOMAIN,
                                       raw_request_snapshot,
                                       request_digest_under)
    from veracium.graph import apply_supersession
    from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                                 EvidenceAuthor, Provenance, Volatility)
    from veracium.store.base import (ReceiptDomainError,
                                     ReceiptSchemaBoundaryError)
    from veracium.store.sqlite import SqliteStore
except ImportError as e:
    print(f"REFUSED: cannot import the shipped construction ({e}). Run "
          f"under an interpreter with the pinned test dependencies — the "
          f"offline launcher's .venv-offline/bin/python — from the "
          f"extraction root.")
    sys.exit(2)

U = "u-era"
NOW = datetime.now(timezone.utc)


def _edge(eid, obj, days_ago=1):
    t = NOW - timedelta(days=days_ago)
    return Edge(id=eid, user_id=U, subject="user", relation="works_as",
                object=obj, volatility=Volatility.SLOW, valid_from=t,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      disclosure=Disclosure.MENTIONABLE,
                                      confidence=0.7, observed_at=t))


def live_store_with_committed_receipt():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc = _edge("e-inc", "carpenter")
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert not getattr(counts, "replayed", False)
    return s, inc


def _set(s, op_id, **cols):
    sets = ", ".join(f"{k}=?" for k in cols)
    s._conn.execute(f"UPDATE supersession_operations SET {sets} "
                    f"WHERE user_id=? AND operation_id=?",
                    (*cols.values(), U, op_id))
    s._conn.commit()


# ---- vectors ---------------------------------------------------------------

def vector_new_receipts_stamp_the_current_domain():
    """§4b-v write rule, live: the product computes the digest under v2 and
    stamps the domain in the same atomic INSERT."""
    s, inc = live_store_with_committed_receipt()
    rd, dom = s._conn.execute(
        "SELECT request_digest, request_digest_domain FROM "
        "supersession_operations WHERE user_id=? AND operation_id=?",
        (U, f"sup-{inc.id}")).fetchone()
    assert rd == request_digest_under(CURRENT_DIGEST_DOMAIN,
                                      raw_request_snapshot(inc))
    assert dom == CURRENT_DIGEST_DOMAIN.decode()


def vector_the_cross_era_retry_replays_live():
    """THE FIX (rounds 3-11's bite, inverted): a migrated receipt — its
    digest under the OLD domain, its domain column NULL — replays a
    legitimate lost-response retry through the live public path. Before
    0025 landed, this exact state raised DIFFERENT request."""
    s, inc = live_store_with_committed_receipt()
    _set(s, f"sup-{inc.id}",
         request_digest=request_digest_under(REQUEST_DIGEST_DOMAIN,
                                             raw_request_snapshot(inc)),
         request_digest_domain=None)               # the migrated population
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert counts.replayed is True


def vector_stamped_receipts_replay_under_their_own_domain():
    s, inc = live_store_with_committed_receipt()
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)   # v2-stamped
    assert counts.replayed is True


def vector_unknown_domains_fail_closed_live():
    """§4b-v: an uninterpretable domain refuses with the NAMED error —
    never replayed, never a new request."""
    s, inc = live_store_with_committed_receipt()
    for bad in ("garbage", "", "veracium.supersession-request.v9"):
        _set(s, f"sup-{inc.id}", request_digest_domain=bad)
        try:
            apply_supersession(s, inc, DEFAULT_RELATIONS)
            raise AssertionError(f"not refused: {bad!r}")
        except ReceiptDomainError:
            pass


def vector_digestless_domain_is_the_writer_invariant_refusal():
    s, inc = live_store_with_committed_receipt()
    _set(s, f"sup-{inc.id}", request_digest=None,
         request_digest_domain=CURRENT_DIGEST_DOMAIN.decode())
    try:
        apply_supersession(s, inc, DEFAULT_RELATIONS)
        raise AssertionError("a digest-less domained receipt was accepted")
    except ReceiptDomainError:
        pass


def vector_pre_d2_precedes_the_domain_logic_live():
    """0016's boundary stays FIRST: a version-3 receipt wearing a poisoned
    domain raises the boundary error, never the domain refusal."""
    s, inc = live_store_with_committed_receipt()
    _set(s, f"sup-{inc.id}", outcome_digest_version=3,
         request_digest_domain="garbage")
    try:
        apply_supersession(s, inc, DEFAULT_RELATIONS)
        raise AssertionError("a pre-D2 receipt was not refused on sight")
    except ReceiptSchemaBoundaryError:
        pass


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors — the implemented §4b-v contract on the "
          f"live paths; per-surface X13 coverage in "
          f"tests/test_0025_receipt_states.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
