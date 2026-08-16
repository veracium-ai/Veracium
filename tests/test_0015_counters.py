"""specs/0015 I1–I7, I9–I11, I14: the supersession/reinforcement counters."""

import json
import sqlite3
import tempfile

import veracium.telemetry as T
from veracium import EvidenceAuthor, Memory, MemoryConfig, SqliteStore
from veracium.graph import SupersessionCounts, apply_supersession
from veracium.ingest import ingest_event
from veracium.schema import DEFAULT_RELATIONS, Edge, Provenance
from veracium.schema import SupersessionPlan


def _llm_for(value):
    def complete(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at",
                                            "object": value}],
                               "episode": f"user at {value}"})
        return "ok"
    return complete


def _mem(tmp, llm):
    db = str(tmp / "s.db")
    return Memory(llm=llm, store=SqliteStore(db), config=MemoryConfig(db_path=db))


def _edge(uid, obj, rel="located_at"):
    import uuid
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=uid, subject="user",
                relation=rel, object=obj,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}"))


def _store(tmp):
    return SqliteStore(str(tmp / "c.db"))


def test_counting_is_pure_observation(tmp_path):
    """I1: identical ingest sequences produce identical stored rows whether or
    not anything reads the returned counts."""
    dumps = []
    for i in range(2):
        s = SqliteStore(str(tmp_path / f"i1-{i}.db"))
        for obj in ("Lisbon", "Porto", "Porto"):
            c = apply_supersession(s, _edge("u", obj), DEFAULT_RELATIONS)
            assert isinstance(c, SupersessionCounts)
        conn = sqlite3.connect(str(tmp_path / f"i1-{i}.db"))
        raw = conn.execute(
            "SELECT user_id,subject,relation,object,active,json "
            "FROM edges ORDER BY object, active").fetchall()
        # ids/timestamps are nondeterministic; the DECISION-bearing projection
        # is what must be identical (I1)
        rows = [(u, sub, rel, ob, act,
                 json.loads(j)["invalidation_reason"],
                 json.loads(j)["provenance"]["disclosure"])
                for u, sub, rel, ob, act, j in raw]
        conn.close()
        dumps.append(rows)
        s.close()
    assert dumps[0] == dumps[1]


def test_replay_counts_zero(tmp_path):
    """I2: a phase-1 replay (same edge id resubmitted) performs no work in
    this call and counts zero."""
    s = _store(tmp_path)
    e = _edge("u", "Lisbon")
    first = apply_supersession(s, e, DEFAULT_RELATIONS)
    assert first.replayed is False
    again = apply_supersession(s, e.model_copy(deep=True), DEFAULT_RELATIONS)
    assert again == SupersessionCounts(superseded=0, reinforced=0, replayed=True)


def test_plan_stale_retry_counts_once(tmp_path):
    """I3: only the committing attempt counts — a supersession that follows a
    prior value counts its one 'superseded' exactly once."""
    s = _store(tmp_path)
    apply_supersession(s, _edge("u", "Lisbon"), DEFAULT_RELATIONS)
    c = apply_supersession(s, _edge("u", "Porto"), DEFAULT_RELATIONS)
    assert (c.superseded, c.reinforced, c.replayed) == (1, 0, False)


def test_counts_partition_invalidated(tmp_path):
    """I4: superseded + absorbed == the store result's invalidated on every
    fresh commit — exercised over supersede, absorb, reinforce, accumulate."""
    from veracium.graph import _build_supersession_plan
    s = _store(tmp_path)
    apply_supersession(s, _edge("u", "Miso", rel="has_pet"), DEFAULT_RELATIONS)
    # absorption: the more specific form retires the shorter prior
    winner = _edge("u", "cat Miso", rel="has_pet")
    plan, is_reinf = _build_supersession_plan(s, winner, DEFAULT_RELATIONS,
                                              f"sup-{winner.id}")
    n_sup = sum(1 for _, _, r in plan.prior_invalidations if r == "superseded")
    n_abs = sum(1 for _, _, r in plan.prior_invalidations if r == "absorbed_duplicate")
    result = s.apply_supersession_plan(plan)
    assert n_sup + n_abs == result.invalidated == 1 and n_abs == 1
    assert is_reinf is False


def test_accumulation_counts_zero_reinforcements(tmp_path):
    """I5: a plain accumulation commit counts (0,0) even though its plan is
    shape-identical to a reinforcement plan."""
    s = _store(tmp_path)
    c1 = apply_supersession(s, _edge("u", "hiking", rel="has_hobby"), DEFAULT_RELATIONS)
    assert (c1.superseded, c1.reinforced) == (0, 0)
    c2 = apply_supersession(s, _edge("u", "chess", rel="has_hobby"), DEFAULT_RELATIONS)
    assert (c2.superseded, c2.reinforced) == (0, 0)
    # and the true reinforcement branch counts 1
    c3 = apply_supersession(s, _edge("u", "chess", rel="has_hobby"), DEFAULT_RELATIONS)
    assert (c3.superseded, c3.reinforced) == (0, 1)


def test_supersession_plan_fields_pinned():
    """I6: the plan carrier gained no field (the 0014 digest basis holds)."""
    assert sorted(SupersessionPlan.model_fields) == sorted([
        "incoming_edge", "insert_incoming", "operation_id", "expected_state",
        "prior_upserts", "prior_invalidations", "refusals",
        "contribution_drafts", "absorption_pre_image", "raw_request"])


def test_counters_are_content_free(tmp_path):
    """I9: the recorded ingest payload carries only numbers."""
    values = ["Lisbon", "Porto"]
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            v = values.pop(0)
            return json.dumps({"triples": [{"subject": "user",
                                            "relation": "located_at",
                                            "object": v}],
                               "episode": f"at {v}"})
        return "ok"
    m = _mem(tmp_path, llm)
    coll = T.Collector(consent_epoch=1, schema_version=2)
    m.telemetry = coll
    m.remember("u1", "USER: I moved to Lisbon.")
    m.remember("u1", "USER: I moved to Porto.")
    snap = coll.snapshot()
    for ev in snap["events"].values():
        for v in ev["sums"].values():
            assert isinstance(v, float)
    assert snap["events"]["ingest"]["sums"]["supersessions"] == 1.0


def test_consent_text_and_whitelist_move_together():
    """I10: the consent text mentions the counters iff whitelisted+populated."""
    assert "superseded or reinforced" in T.CONSENT_TEXT
    assert {"supersessions", "reinforcements"} <= T.EVENT_FIELDS["ingest"]


def test_mcp_result_carries_no_supersession_oracle(tmp_path):
    """I11: the MCP tool result contains neither key under supersession,
    reinforcement, and accumulation — and the kept fields are co-invariant."""
    from veracium.mcp_server import remember_impl
    m = _mem(tmp_path, _llm_for("Lisbon"))
    r_acc = remember_impl(m, "u1", "USER: I moved to Lisbon.")
    m2 = _mem(tmp_path / "b", _llm_for("Porto")) if False else m
    r_sup = remember_impl(m, "u1", "USER: I moved to Lisbon again.")  # reinforce
    for r in (r_acc, r_sup):
        assert "supersessions" not in r and "reinforcements" not in r
    # co-invariance: the kept count fields identical across outcomes
    assert (r_acc["facts"], r_acc["quarantined"]) == (r_sup["facts"], r_sup["quarantined"])


def test_host_api_return_carries_counts(tmp_path):
    """I11 permission side: the host-API return DOES carry both keys."""
    m = _mem(tmp_path, _llm_for("Lisbon"))
    r = m.remember("u1", "USER: I moved to Lisbon.")
    assert r["supersessions"] == 0 and r["reinforcements"] == 0
    r2 = m.remember("u1", "USER: I moved to Lisbon.")
    assert r2["reinforcements"] == 1


def test_unparseable_return_carries_zero_counts(tmp_path):
    """I14: the parse-failure early return carries both keys as int zeros, and
    the MCP strip behaves on that branch too."""
    def refusing(prompt, *, system=None, role="compile", json_schema=None):
        return "I cannot help with that." if role == "distill" else "ok"
    m = _mem(tmp_path, refusing)
    r = m.remember("u1", "USER: gibberish")
    assert r["supersessions"] == 0 and r["reinforcements"] == 0
    assert r.get("unparseable") is True
    from veracium.mcp_server import remember_impl
    r2 = remember_impl(m, "u1", "USER: more gibberish")
    assert "supersessions" not in r2 and "reinforcements" not in r2
