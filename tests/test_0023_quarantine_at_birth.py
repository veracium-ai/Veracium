"""specs/0023 §4a — quarantine-at-birth (Slice C4).

A standing-revoked source's writes land QUARANTINED — every edge of the
event and the episode itself, one verdict per event — and a later lift does
NOT revisit the floor (Q2, ratified). No host-configurable refusal exists
(Q1, resolved, both names)."""

import json
import uuid

import pytest

from veracium import EvidenceAuthor, SqliteStore
from veracium.ingest import ingest_event
from veracium.schema import DEFAULT_RELATIONS, Disclosure
from veracium.scope_linkage import identity_digest_of
from veracium.store import revocation as rv

U = "u"
AT = "2026-08-21T00:00:00Z"


def _llm(prompt, *, system=None, role="distill", json_schema=None):
    return json.dumps({"triples": [{"subject": "user", "relation": "located_at",
                                    "object": "Porto"}],
                       "episode": "the feed reported the user moved to Porto"})


def _ingest(store, source_id):
    return ingest_event(store, _llm, U,
                        event_text="feed says user moved to Porto",
                        author=EvidenceAuthor.THIRD_PARTY,
                        date="2026-08-21", source_id=source_id,
                        relations=DEFAULT_RELATIONS)


def test_revoked_source_ingest_is_quarantined_at_birth(   # N1's canonical name
tmp_path):
    s = SqliteStore(str(tmp_path / "q.db"))
    digest = identity_digest_of(None, "feed-1", s.local_origin())
    rv.revoke_source(s, U, digest, "revoke", "operator", AT)

    _ingest(s, "feed-1")
    edges = s.edges(U, active_only=False)
    assert edges and all(
        e.provenance.disclosure == Disclosure.QUARANTINED for e in edges), (
        "a standing-revoked source's edges must land QUARANTINED at birth")
    eps = s.episodes(U, include_retired=True)
    assert eps and eps[0].provenance.disclosure == Disclosure.QUARANTINED
    assert not eps[0].assertable, (
        "the quarantined-at-birth episode reached the assertable set")


def test_an_unrevoked_source_is_untouched(tmp_path):
    """The floor applies to the revoked source ONLY — the negative control,
    without which the positive test could pass by quarantining everything."""
    s = SqliteStore(str(tmp_path / "q.db"))
    digest = identity_digest_of(None, "feed-1", s.local_origin())
    rv.revoke_source(s, U, digest, "revoke", "operator", AT)
    _ingest(s, "feed-2")                       # a DIFFERENT source
    eps = s.episodes(U, include_retired=True)
    # third-party influence still caps at USE_ONLY — but never QUARANTINED
    assert eps[0].provenance.disclosure == Disclosure.USE_ONLY


def test_lift_does_not_rewrite_existing_disclosure(      # N13's canonical name
tmp_path):
    """Q2, ratified on the two-floors argument: the persisted disclosure is
    the MINIMUM of every floor that applied, the record does not carry which
    floor bound it, and re-deriving would relax another mechanism's floor as
    a side effect."""
    s = SqliteStore(str(tmp_path / "q.db"))
    digest = identity_digest_of(None, "feed-1", s.local_origin())
    rv.revoke_source(s, U, digest, "revoke", "operator", AT)
    _ingest(s, "feed-1")
    rv.revoke_source(s, U, digest, "lift", "operator", AT)
    eps = s.episodes(U, include_retired=True)
    assert eps[0].provenance.disclosure == Disclosure.QUARANTINED, (
        "a lift revisited the birth floor — Q2 says it must not")


def test_no_refusal_mode_exists():
    """Q1, resolved with both names: no host-configurable refusal. The
    ingest surface accepts no such parameter — asserted structurally so a
    config flag cannot arrive without failing this test."""
    import inspect
    params = inspect.signature(ingest_event).parameters
    for name in params:
        assert "refus" not in name and "reject" not in name, (
            f"ingest_event grew a {name!r} parameter — Q1 resolved NO host "
            f"choice, and §3b refuses per-process acceptance settings")


def test_q4_audit_facts_carry_digest_and_count():
    """0023 Q4, RESOLVED 2026-08-22 (the spec-table audit found the
    pre-release question shipped unresolved and its carrier missing): the
    ingest result carries the content-free identity digest and the count on
    the revoked path, None/0 otherwise — the AuditLog is the consumer,
    telemetry's whitelist drops both, the MCP surface strips both."""
    import json
    from veracium.ingest import ingest_event
    from veracium.schema import EvidenceAuthor
    from veracium.scope_linkage import identity_digest_of
    from veracium.store.revocation import revoke_source
    from veracium.store.sqlite import SqliteStore

    class Stub:
        def __call__(self, prompt, **kw):
            if kw.get("role") == "distill-retry":
                return json.dumps({"triples": []})
            return json.dumps({"triples": [{"subject": "user",
                                            "relation": "works_on",
                                            "object": "x"}],
                               "episode": "e"})

    s = SqliteStore(":memory:")
    # the EXACT derivation ingest uses (ingest.py: identity_digest_of over
    # the store's local origin + the host source_id)
    digest = identity_digest_of(None, "mail:spoofed@example.com",
                                s.local_origin())
    revoke_source(s, "u", digest, "revoke", "compromised",
                  "2026-08-22T00:00:00Z")
    r = ingest_event(s, Stub(), "u", event_text="t",
                     author=EvidenceAuthor.THIRD_PARTY, date="2026-08-22",
                     source_id="mail:spoofed@example.com")
    assert r["quarantined_at_birth"] >= 1
    assert r["birth_revocation_digest"] == digest
    # the clean path carries the keys with their honest zeros
    r2 = ingest_event(s, Stub(), "u2", event_text="t",
                      author=EvidenceAuthor.USER, date="2026-08-22")
    assert r2["quarantined_at_birth"] == 0
    assert r2["birth_revocation_digest"] is None
    # telemetry's whitelist does NOT admit either key
    from veracium.telemetry import EVENT_FIELDS
    assert "birth_revocation_digest" not in EVENT_FIELDS["ingest"]
    assert "quarantined_at_birth" not in EVENT_FIELDS["ingest"]
