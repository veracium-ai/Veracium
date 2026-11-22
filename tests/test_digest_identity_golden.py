"""Golden values for the digests the store uses as IDENTITY.

The order census (2026-09-19) found four functions that canonicalise by sorting.
Reversing their sort key changed what the digest names and no test failed. In this
codebase those digests are identity:
  - `authority.scope_fingerprint` is the CAS token for `apply_supersession_plan`;
  - `SqliteStore._logical_request_digest` decides replay versus integrity conflict
    for a retried `operation_id`;
  - `scope_linkage.plan_row_id`, over `canonical_payload`, is import idempotence:
    "plan_row_id set equality" is its one definition;
  - `agreement.derive_record` fixes the stored `AgreementRecord.markers` order.
A refactor, a tidied sort or an iteration-order change could silently re-key them:
the CAS token would read every plan as stale, committed receipts would stop
replaying, re-imports would duplicate.

Each test pins the BYTES for a fixed input, with the input given in two orders where
the function promises order-independence. The fixtures are fully specified: every
timestamp is fixed, and no default_factory runs. A golden value that moves is a
change to stored identity. Moving it needs a migration story, not a new constant.

The constants were computed by running the functions at the commit that added this
file. They were never typed by hand.
"""
from datetime import datetime, timezone

from veracium.agreement import derive_record
from veracium.authority import scope_fingerprint
from veracium.schema import (Disclosure, Edge, EvidenceAuthor, Provenance,
                             SupersessionPlan, SupersessionRefusalDraft)
from veracium.scope_linkage import SITE_ATTRIBUTION, canonical_payload, plan_row_id
from veracium.store.sqlite import SqliteStore

T0 = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
T1 = datetime(2026, 2, 3, 4, 5, 6, tzinfo=timezone.utc)
U = "u-golden"


def _edge(eid, obj, author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE, df=None, active=True):
    return Edge(id=eid, user_id=U, subject="user", relation="works_as", object=obj,
                valid_from=T0, invalidated_at=None if active else T1,
                provenance=Provenance(author_of_evidence=author, evidence_ref="ev-golden",
                                      disclosure=disc, derived_from=df, observed_at=T0))


def _scope():
    return [_edge("e-alpha", "teacher"),
            _edge("e-beta", "engineer", author=EvidenceAuthor.ASSISTANT,
                  disc=Disclosure.QUARANTINED),
            _edge("e-gamma", "nurse", active=False)]


SCOPE_FINGERPRINT = "54a366d636da4474be4b5710fe815f663fa0b5ded0622fcc0d401713b985bce2"


def test_scope_fingerprint_bytes_are_pinned():
    edges = _scope()
    assert scope_fingerprint(edges) == SCOPE_FINGERPRINT
    assert scope_fingerprint(list(reversed(edges))) == SCOPE_FINGERPRINT
    assert scope_fingerprint([edges[1], edges[2], edges[0]]) == SCOPE_FINGERPRINT


def _plan(order, operation_id="op-golden-1", expected_state="state-one"):
    incoming = _edge("e-incoming", "architect")
    upserts = [_edge("e-up-1", "teacher", active=False), _edge("e-up-2", "nurse", active=False)]
    invalidations = [("e-up-1", T1, "superseded"), ("e-up-2", T1, "superseded")]
    refusals = [SupersessionRefusalDraft(prior_edge_id=p, incoming_edge_id="e-incoming",
                                         relation="works_as", prior_effective=3,
                                         incoming_effective=2)
                for p in ("e-held-1", "e-held-2")]
    if order == "reversed":
        upserts, invalidations, refusals = upserts[::-1], invalidations[::-1], refusals[::-1]
    return SupersessionPlan(incoming_edge=incoming, insert_incoming=True,
                            operation_id=operation_id, expected_state=expected_state,
                            prior_upserts=upserts, prior_invalidations=invalidations,
                            refusals=refusals)


LOGICAL_REQUEST_DIGEST = "952a07e1da264aa31ebd1ece7125d1a271d9032bfbea41b40e84ec479ad4156d"


def test_logical_request_digest_bytes_are_pinned():
    assert SqliteStore._logical_request_digest(_plan("forward")) == LOGICAL_REQUEST_DIGEST
    assert SqliteStore._logical_request_digest(_plan("reversed")) == LOGICAL_REQUEST_DIGEST
    # Its documented exclusions: the lookup key and the CAS state it assumed.
    assert SqliteStore._logical_request_digest(
        _plan("forward", operation_id="op-golden-2", expected_state="state-two")) == LOGICAL_REQUEST_DIGEST


PAYLOAD = {"zeta": 1, "alpha": {"mu": [3, 1], "beta": None}, "reconstructed": True}
CANONICAL_PAYLOAD = '{"alpha":{"beta":null,"mu":[3,1]},"reconstructed":true,"zeta":1}'
_ROW = {"site": SITE_ATTRIBUTION,
        "identity_digest": "0" * 64,
        "evidence_ref_digest": None,
        "contributor_ref": "A",
        "contributor_type": "edge"}
ROW_PAYLOAD = {"reconstructed": True, "flattened": True}
PLAN_ROW_ID = "3a9764edd8d40ab1d6b44bb386623761092d30345ee1611212fa1c9e715f863a"


def _row(payload, op):
    from veracium.scope_linkage import row_op_key
    row = dict(_ROW, payload=payload)
    row["op_key"] = row_op_key(op, row["site"], "C", row["contributor_ref"])
    return row


def test_canonical_payload_and_plan_row_id_bytes_are_pinned():
    assert canonical_payload(PAYLOAD) == CANONICAL_PAYLOAD
    reordered = {"reconstructed": True, "alpha": {"beta": None, "mu": [3, 1]}, "zeta": 1}
    assert canonical_payload(reordered) == CANONICAL_PAYLOAD
    # plan_row_id validates the payload against its site's closed shapes, so it takes
    # the one legal two-key shape, given in both key orders. The op key is operational
    # (re-minted per import), so two ops give one id.
    a = plan_row_id(U, "edge", "C", _row(ROW_PAYLOAD, "op-aaaaaaaaaaaa"), "import", op="op-aaaaaaaaaaaa")
    b = plan_row_id(U, "edge", "C", _row(dict(reversed(list(ROW_PAYLOAD.items()))), "op-bbbbbbbbbbbb"),
                    "import", op="op-bbbbbbbbbbbb")
    assert a == b == PLAN_ROW_ID


DERIVED_MARKERS = ['according to', 'reported', 'said']


def test_derive_record_marker_order_is_pinned():
    note = "my boss said, according to my mother, they reported it"
    rec = derive_record(note, "x", Disclosure.MENTIONABLE)
    assert rec is not None and rec.direction == "inbound"
    assert rec.markers == DERIVED_MARKERS


USER_SOURCE_MARKERS = ['said', 'told']


def test_derive_record_user_source_marker_order_is_pinned():
    # The second branch: an outbound (user-as-source) reading on a record the extractor
    # demoted to quarantine. Its markers are sorted separately from the inbound branch.
    from veracium.schema import QUARANTINE_RELATION
    rec = derive_record('I said so and I told them', "x", Disclosure.QUARANTINED, relation=QUARANTINE_RELATION)
    assert rec is not None and rec.direction == "user_source"
    assert rec.markers == USER_SOURCE_MARKERS
