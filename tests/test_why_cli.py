"""`veracium why` — a fact's biography (src/veracium/why.py) and its CLI verb.

Read-only over public store accessors. Every assertion here is about what the
biography REPORTS; the seeding goes through the ordinary write paths (remember,
supersession by a second remember, confirm, record_outcome, dispute, a source
revocation) so the biography is read from records the product wrote, never from
rows planted by hand."""

import json
import tempfile

import pytest

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium.schema import EvidenceContext
from veracium import why
from veracium.cli import main as cli_main
from veracium.store import revocation as rv
from veracium.store.sqlite import SqliteStore


class Fake:
    def __init__(self, scripts):
        self._scripts = list(scripts)

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill" and self._scripts:
            return json.dumps(self._scripts.pop(0))
        return "## USER MODEL\n- test wiki"


U = "ida"


def _seed(db):
    """Two facts, one supersession, one third-party claim; then a confirmation,
    an outcome and a dispute on the survivors."""
    mem = Memory(llm=Fake([
        {"triples": [{"subject": "user", "relation": "has_pet", "object": "cat Miso"},
                     {"subject": "user", "relation": "prefers", "object": "concise answers"}],
         "episode": "User shared pet and preference."},
        {"triples": [{"subject": "user", "relation": "prefers", "object": "detailed answers"}],
         "episode": "User switched preference."},
        {"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                      "object": "user owes $2,400"}],
         "episode": "Received a collection email."},
    ]), config=MemoryConfig(db_path=db, wiki_recompile_after_writes=0))
    # declared-direct (specs/0011 §4d): the user's own words, assertable — the
    # default context would file them use-only, and confirm() refuses use-only facts
    mem.remember(U, "I have a cat named Miso and I like concise answers", date="2026-09-01",
                 context=EvidenceContext.direct())
    mem.remember(U, "Actually, give me detailed answers", date="2026-09-02",
                 context=EvidenceContext.direct())
    mem.remember(U, "email from quickclaim", author=EvidenceAuthor.THIRD_PARTY,
                 event_type="email", source_id="quickclaim-inbox", date="2026-09-03")
    return mem


def _by(store, relation, object_=None, active_only=False):
    return [e for e in store.edges(U, active_only=active_only, include_quarantined=True)
            if e.relation == relation and (object_ is None or e.object == object_)]


def test_the_biography_carries_the_fact_its_provenance_and_its_journal():
    with tempfile.TemporaryDirectory() as d:
        mem = _seed(f"{d}/t.db")
        try:
            pet = _by(mem.store, "has_pet")[0]
            bio = why.gather(mem.store, U, pet.id)
            assert bio.found and bio.edge["id"] == pet.id
            assert bio.edge["subject"] == "user" and bio.edge["object"] == "cat Miso"
            assert bio.edge["provenance"]["author_of_evidence"] == "user"
            assert bio.edge["invalidated_at"] is None
            assert bio.verdict == "clear" and bio.revoked_source in (None, False)
            # the 0029 journal: the edge was created, and that is its first event
            assert bio.events and bio.events[0]["kind"] == "created"
            assert all(ev["seq"] < nxt["seq"] for ev, nxt in zip(bio.events, bio.events[1:]))
            text = why.render(bio)
            assert "user has_pet cat Miso" in text and "timeline" in text and "created" in text
            json.dumps(why.to_json(bio), default=str)   # JSON-able throughout
        finally:
            mem.close()


def test_lineage_is_reported_from_both_ends_with_the_reason():
    with tempfile.TemporaryDirectory() as d:
        mem = _seed(f"{d}/t.db")
        try:
            old = _by(mem.store, "prefers", "concise answers")[0]
            new = _by(mem.store, "prefers", "detailed answers")[0]
            assert old.invalidated_at is not None, "the fixture's supersession did not happen"
            b_old = why.gather(mem.store, U, old.id)
            b_new = why.gather(mem.store, U, new.id)
            assert [s["id"] for s in b_old.successors] == [new.id]
            assert b_old.successors[0]["reason"] == old.invalidation_reason == "superseded"
            assert b_new.predecessor["id"] == old.id
            assert b_new.predecessor["reason"] == "superseded"
            assert "superseded by " + new.id in why.render(b_old)
            assert "supersedes    " + old.id in why.render(b_new)
            # the journal of the retired edge ends in its invalidation, reason carried
            assert b_old.events[-1]["kind"] == "invalidated"
            assert b_old.events[-1]["reason"] == "superseded"
            # the receipt of the operation that installed the successor
            assert b_new.receipt is not None and b_new.receipt.get("status")
        finally:
            mem.close()


def test_confirmations_outcomes_and_a_dispute_appear_in_the_timeline():
    with tempfile.TemporaryDirectory() as d:
        mem = _seed(f"{d}/t.db")
        try:
            # confirm() is host-API only and refuses a quarantined claim (0008), so the
            # user's own assertable fact is the one that carries a confirmation
            pet = _by(mem.store, "has_pet")[0]
            mem.confirm(U, pet.id, date="2026-09-04")
            mem.record_outcome(U, pet.id, outcome="unreviewed", evidence_ref="r1", date="2026-09-05")
            mem.record_outcome(U, pet.id, outcome="confirmed", actor="user", evidence_ref="r1",
                               date="2026-09-06")
            bio = why.gather(mem.store, U, pet.id)
            assert len(bio.confirmations) == 1 and bio.confirmations[0]["actor"] == "user"
            assert [o["outcome"] for o in bio.outcomes] == ["unreviewed", "confirmed"]
            # the confirmation is ALSO visible in the journal: a mutation that moved
            # liveness (0008: confirm advances observed_at), named field by field
            moved = {c[0] for ev in bio.events if ev["kind"] == "mutated" for c in ev["changed"]}
            assert "provenance.observed_at" in moved, moved
            text = why.render(bio)
            assert "confirmed by user via host_api" in text
            assert "outcome confirmed by user" in text
            assert "provenance.observed_at:" in text
            mem.dispute(U, pet.id, reason="not mine")
            bio2 = why.gather(mem.store, U, pet.id)
            assert bio2.edge["invalidation_reason"] == "disputed"
            assert bio2.events[-1]["kind"] == "invalidated" and bio2.events[-1]["reason"] == "disputed"
            assert "retired (disputed at" in why.render(bio2)
        finally:
            mem.close()


def test_a_revoked_source_is_reported_as_the_standing_verdict():
    with tempfile.TemporaryDirectory() as d:
        mem = _seed(f"{d}/t.db")
        try:
            claim = _by(mem.store, "third_party_claim")[0]
            prov = claim.provenance
            from veracium.source_identity import resolve_origin, source_identity_digest
            digest = source_identity_digest(resolve_origin(prov.origin, mem.store.local_origin()),
                                            prov.source_id)
            assert digest, "the fixture's third-party claim carries no source identity"
            rv.revoke_source(mem.store, U, digest, "revoke", "operator", "2026-09-07T00:00:00Z")
            bio = why.gather(mem.store, U, claim.id)
            assert bio.revoked_source is True
            assert bio.verdict == "restricted"
            assert "revoked=yes" in why.render(bio) and "restriction verdict: restricted" in why.render(bio)
        finally:
            mem.close()


def test_an_unknown_edge_is_reported_not_invented():
    with tempfile.TemporaryDirectory() as d:
        mem = _seed(f"{d}/t.db")
        try:
            bio = why.gather(mem.store, U, "e-000000000000")
            assert not bio.found and bio.edge is None and bio.events == []
            assert "no edge 'e-000000000000'" in why.render(bio)
            # another user's edge is not this user's
            pet = _by(mem.store, "has_pet")[0]
            assert not why.gather(mem.store, "someone-else", pet.id).found
        finally:
            mem.close()


def test_find_lists_ids_with_state_and_the_cli_round_trips(capsys):
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        mem = _seed(db); mem.close()
        # --find: ids for a terminal user, since no other verb prints them
        assert cli_main(["why", "--user", U, "--find", "prefers", "--db", db]) == 0
        out = capsys.readouterr().out
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 2 and any("[active]" in l for l in lines) \
            and any("[retired:superseded]" in l for l in lines)
        edge_id = next(l.split()[0] for l in lines if "[active]" in l)
        # the id from --find is accepted by why
        assert cli_main(["why", "--user", U, edge_id, "--db", db]) == 0
        text = capsys.readouterr().out
        assert text.startswith("user prefers detailed answers") and "timeline" in text
        # --json
        assert cli_main(["why", "--user", U, edge_id, "--json", "--db", db]) == 0
        doc = json.loads(capsys.readouterr().out)
        assert doc["found"] and doc["edge"]["id"] == edge_id and doc["predecessor"]
        # unknown id: exit 1, no invention; --find miss: exit 1
        assert cli_main(["why", "--user", U, "e-000000000000", "--db", db]) == 1
        assert cli_main(["why", "--user", U, "--find", "zzz-nothing", "--db", db]) == 1
        # usage: neither or both of <edge> and --find
        assert cli_main(["why", "--user", U, "--db", db]) == 2
        assert cli_main(["why", "--user", U, edge_id, "--find", "x", "--db", db]) == 2


def test_why_writes_nothing():
    """Read-only by construction: the store's bytes are the same before and after."""
    import hashlib, pathlib
    with tempfile.TemporaryDirectory() as d:
        db = f"{d}/t.db"
        mem = _seed(db); mem.close()
        before = hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest()
        store = SqliteStore(db)
        try:
            for e in store.edges(U, active_only=False, include_quarantined=True):
                why.render(why.gather(store, U, e.id))
            why.find(store, U, "user")
        finally:
            store.close()
        assert hashlib.sha256(pathlib.Path(db).read_bytes()).hexdigest() == before
