"""specs/0025 §4b-v — X13: the receipt-state contract, PER SURFACE.

Five tests, one per surface, each table-driven over that surface's
REACHABLE cells with the unreachable cells named (§4b-v's reachability
table; round 8 R8-2 made the invariant executable this way). The pre-D2
precedence cells use the EXPLODING-DIGEST SENTINEL: a counting hook on the
shipped digest constructions that fails the test if any digest is computed
before the boundary refuses.
"""
from datetime import datetime, timedelta, timezone

import pytest

import veracium.contribution as contribution
from veracium.contribution import (ACCEPTED_DIGEST_DOMAINS,
                                   CURRENT_DIGEST_DOMAIN,
                                   REQUEST_DIGEST_DOMAIN,
                                   raw_request_snapshot,
                                   receipt_request_matches,
                                   request_digest_under)
from veracium.graph import _build_supersession_plan, apply_supersession
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                             EvidenceAuthor, Provenance, Volatility)
from veracium.store.base import (ReceiptDomainError,
                                 ReceiptSchemaBoundaryError,
                                 SupersessionIntegrityError)
from veracium.store.migration import migrate_store
from veracium.store.sqlite import SqliteStore

U = "u-x13"
NOW = datetime.now(timezone.utc)
V1 = REQUEST_DIGEST_DOMAIN.decode()
V2 = CURRENT_DIGEST_DOMAIN.decode()


def _edge(eid, obj, days_ago=1):
    t = NOW - timedelta(days=days_ago)
    return Edge(id=eid, user_id=U, subject="user", relation="works_as",
                object=obj, volatility=Volatility.SLOW, valid_from=t,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{eid}",
                                      disclosure=Disclosure.MENTIONABLE,
                                      confidence=0.7, observed_at=t))


def _committed_store():
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc = _edge("e-inc", "carpenter")
    counts = apply_supersession(s, inc, DEFAULT_RELATIONS)
    assert not getattr(counts, "replayed", False)
    return s, inc


def _row(s, op_id):
    return s._conn.execute(
        "SELECT request_digest, request_digest_domain, outcome_digest_version "
        "FROM supersession_operations WHERE user_id=? AND operation_id=?",
        (U, op_id)).fetchone()


def _set(s, op_id, **cols):
    sets = ", ".join(f"{k}=?" for k in cols)
    s._conn.execute(f"UPDATE supersession_operations SET {sets} "
                    f"WHERE user_id=? AND operation_id=?",
                    (*cols.values(), U, op_id))
    s._conn.commit()


class ExplodingDigest:
    """The sentinel: counts (and forbids) digest computation."""

    def __enter__(self):
        self.calls = []
        self._real = (contribution.request_digest,
                      contribution.request_digest_under)
        def boom(*a, **k):
            self.calls.append(1)
            raise AssertionError("digest computed inside a pre-D2 case")
        contribution.request_digest = boom
        contribution.request_digest_under = boom
        return self

    def __exit__(self, *exc):
        (contribution.request_digest,
         contribution.request_digest_under) = self._real
        return False


# ---- WRITE (new receipts; migrated/pre-D2 states named-unreachable) --------

def test_receipt_write_states():
    # digest-bearing new receipt: stamps the CURRENT domain atomically
    s, inc = _committed_store()
    rd, dom, ver = _row(s, f"sup-{inc.id}")
    assert rd == request_digest_under(CURRENT_DIGEST_DOMAIN,
                                      raw_request_snapshot(inc))
    assert dom == V2 and ver == 4
    # digest-less new receipt (plan without raw_request): NULL/NULL —
    # the writer invariant, NEW WRITES ONLY
    s2 = SqliteStore(":memory:")
    s2.add_edge(_edge("e-prior", "chef", days_ago=200))
    inc2 = _edge("e-inc2", "plumber")
    plan, _ = _build_supersession_plan(s2, inc2, DEFAULT_RELATIONS,
                                       f"sup-{inc2.id}")
    plan.raw_request = None
    s2.apply_supersession_plan(plan)
    rd, dom, _ = _row(s2, f"sup-{inc2.id}")
    assert rd is None and dom is None
    # named-unreachable at this surface: migrated states (digest + NULL
    # domain) and pre-D2 versions — no new write produces either
    assert dom != V1


# ---- READ (validate + domain read; the snapshot axis has no input) ---------

def test_receipt_read_states():
    s, inc = _committed_store()
    op = f"sup-{inc.id}"
    # a valid v2-stamped row reads back whole
    r = s.supersession_receipt(U, op)
    assert r["request_digest_domain"] == V2
    # pre-D2 precedence at the READ-adjacent comparison: version 3 + a
    # poisoned domain refuses at the BOUNDARY with zero digest computation
    _set(s, op, outcome_digest_version=3, request_digest_domain="garbage")
    with ExplodingDigest() as sentinel:
        with pytest.raises(ReceiptSchemaBoundaryError):
            apply_supersession(s, _edge("e-inc", "carpenter"),
                               DEFAULT_RELATIONS)
    assert sentinel.calls == []
    # the read-side inconsistency: digest NULL + domain non-NULL refuses
    _set(s, op, outcome_digest_version=4, request_digest=None,
         request_digest_domain=V2)
    with pytest.raises(ReceiptDomainError):
        apply_supersession(s, _edge("e-inc", "carpenter"), DEFAULT_RELATIONS)


# ---- PHASE 1 (public; snapshot-absent named-unreachable) --------------------

def test_receipt_phase1_states():
    cells = [
        # (stored domain, digest-under, expect)
        (None, V1, "replay"),          # migrated: dual-domain matches v1
        (None, V2, "replay"),          # migrated: dual-domain matches v2
        (V2,   V2, "replay"),          # stamped: its own domain
        (V1,   V2, "different"),       # stamped v1, digest under v2: mismatch
        ("garbage", V2, "domain-error"),
        ("", V2, "domain-error"),
    ]
    for dom, under, expect in cells:
        s, inc = _committed_store()
        op = f"sup-{inc.id}"
        snap = raw_request_snapshot(inc)
        _set(s, op, request_digest=request_digest_under(
                 {"v1": REQUEST_DIGEST_DOMAIN,
                  "v2": CURRENT_DIGEST_DOMAIN}["v1" if under == V1 else "v2"],
                 snap),
             request_digest_domain=dom)
        retry = lambda: apply_supersession(s, inc, DEFAULT_RELATIONS)
        if expect == "replay":
            assert retry().replayed is True, (dom, under)
        elif expect == "different":
            with pytest.raises(SupersessionIntegrityError):
                retry()
        else:
            with pytest.raises(ReceiptDomainError):
                retry()
    # pre-D2 precedence × domain states, sentinel-proven
    for dom in (None, V2, "garbage"):
        s, inc = _committed_store()
        _set(s, f"sup-{inc.id}", outcome_digest_version=3,
             request_digest_domain=dom)
        with ExplodingDigest() as sentinel:
            with pytest.raises(ReceiptSchemaBoundaryError):
                apply_supersession(s, inc, DEFAULT_RELATIONS)
        assert sentinel.calls == [], dom


# ---- PHASE 2 (store; the full product incl. snapshot-absent) ---------------

def test_receipt_phase2_states():
    def plan_for(s, inc, with_snapshot=True):
        plan, _ = _build_supersession_plan(s, inc, DEFAULT_RELATIONS,
                                           f"sup-{inc.id}")
        plan.raw_request = raw_request_snapshot(inc) if with_snapshot else None
        return plan

    # same-plan resubmission replays across every valid domain state
    for dom_setup in ("stamped-v2", "migrated-null"):
        s, inc = _committed_store()
        op = f"sup-{inc.id}"
        if dom_setup == "migrated-null":
            # simulate a migrated row: keep the digest, clear the domain,
            # re-digest under v1 (the migrated population's real state)
            _set(s, op, request_digest=request_digest_under(
                     REQUEST_DIGEST_DOMAIN, raw_request_snapshot(inc)),
                 request_digest_domain=None)
        r = s.apply_supersession_plan(plan_for(s, inc))
        assert getattr(r, "replayed", False) is True, dom_setup
    # a truly different request refuses
    s, inc = _committed_store()
    other = _edge("e-inc", "plumber")
    with pytest.raises(SupersessionIntegrityError):
        s.apply_supersession_plan(plan_for(s, other))
    # snapshot-absent: the shipped outcome comparison governs (identity-less
    # semantics — a differing post-commit re-plan legitimately refuses)
    s, inc = _committed_store()
    with pytest.raises(SupersessionIntegrityError) as ei:
        s.apply_supersession_plan(plan_for(s, inc, with_snapshot=False))
    assert "DIFFERENT logical operation" in str(ei.value)
    # fail-closed cells at the store site
    s, inc = _committed_store()
    _set(s, f"sup-{inc.id}", request_digest_domain="garbage")
    with pytest.raises(ReceiptDomainError):
        s.apply_supersession_plan(plan_for(s, inc))
    # pre-D2 precedence × poisoned domain, sentinel-proven
    s, inc = _committed_store()
    plan = plan_for(s, inc)
    _set(s, f"sup-{inc.id}", outcome_digest_version=3,
         request_digest_domain="garbage")
    with ExplodingDigest() as sentinel:
        with pytest.raises(ReceiptSchemaBoundaryError):
            s.apply_supersession_plan(plan)
    assert sentinel.calls == []


# ---- MIGRATION (produces NULL domains; never fabricates) -------------------

def test_receipt_migration_states(tmp_path):
    import sqlite3
    from veracium.store.schema_version import SCHEMA_V6, SCHEMA_VERSION
    db = tmp_path / "legacy.db"
    conn = sqlite3.connect(db)
    # a faithful CONSTRUCTOR-form v6 store (the accepted v6 manifest); the
    # ALTER-path base variant's v10 result is separately byte-verified
    # against its frozen literal by the migration itself.
    for o in SCHEMA_V6:
        conn.execute(o.ddl)
    conn.execute("PRAGMA user_version = 6")
    # a digest-bearing v6-era receipt and a digest-less one
    conn.execute("INSERT INTO supersession_operations VALUES (?,?,?,?,?,?,?)",
                 (U, "op-digest", "lrd-1", "applied", "some-v1-digest",
                  '{"superseded":1,"reinforced":0,"replayed":false}', 4))
    conn.execute("INSERT INTO supersession_operations VALUES (?,?,?,?,?,?,?)",
                 (U, "op-bare", "lrd-2", "applied", None,
                  '{"superseded":1,"reinforced":0,"replayed":false}', 4))
    conn.commit(); conn.close()
    migrate_store(str(db))
    conn = sqlite3.connect(db)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    rows = dict(conn.execute(
        "SELECT operation_id, request_digest_domain "
        "FROM supersession_operations").fetchall())
    # the migration NEVER fabricates a domain — both forms stay NULL
    assert rows == {"op-digest": None, "op-bare": None}
