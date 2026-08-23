"""specs/0001 v7 candidate harness (round-3 standing ask; version kept
current per R5-5 — this line is a version carrier).

Runnable, self-contained, offline. Each vector MEASURES the shipped
behaviour the v5 contracts are written against, and states beside it the
candidate delta acceptance would authorise. Nothing here monkeypatches the
enum: vectors that need `ASSISTANT` to exist use the disclosure class it
will occupy (`use_only`) through the shipped third-party route, which
exercises the SAME guard/ladder/ranker paths — the stand-in is named at
each site. Round-3's findings were executed collisions between the v4 text
and these behaviours; this harness makes each one a one-command check.

Run:  $PY specs/evidence/0001/candidate_harness.py
"""
import pathlib
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))
try:
    from veracium.graph import apply_supersession, subgraph_for_query
    from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge,
                                 EvidenceAuthor, Provenance, Volatility)
    from veracium.store.sqlite import SqliteStore
except ImportError as e:
    print(f"REFUSED: cannot import the shipped construction ({e}). Run "
          f"under the pinned interpreter from the extraction root.")
    sys.exit(2)

U = "u-0001"
NOW = datetime.now(timezone.utc)


def _edge(obj, *, author=EvidenceAuthor.USER, derived=None, rel="works_as",
          days_ago=1, disclosure=None):
    t = NOW - timedelta(days=days_ago)
    prov = Provenance(author_of_evidence=author, derived_from=derived,
                      evidence_ref=f"ev-{uuid.uuid4().hex[:6]}",
                      confidence=0.7, observed_at=t,
                      **({"disclosure": disclosure} if disclosure else {}))
    return Edge(id=f"e-{uuid.uuid4().hex[:8]}", user_id=U, subject="user",
                relation=rel, object=obj, volatility=Volatility.SLOW,
                valid_from=t, provenance=prov)


def _use_only_edge(obj, **kw):
    """The `use_only` stand-in for a candidate assistant edge: authored
    USER, derived THIRD_PARTY, disclosure USE_ONLY — the class ASSISTANT
    will occupy, exercising the same guards. Disclosure is set explicitly
    because this harness constructs Provenance directly (ingest's
    `_disclosure_for` is bypassed; its routing has its own vectors)."""
    return _edge(obj, author=EvidenceAuthor.USER,
                 derived=EvidenceAuthor.THIRD_PARTY,
                 disclosure=Disclosure.USE_ONLY, **kw)


def vector_confirm_edge_refuses_non_assertable():
    """R3-1: 0008's `confirm_edge` refuses EVERY non-assertable edge — the
    contract v4's promotion cell collided with. Candidate delta: none;
    v5's affirmation path is new USER evidence, 0008 unamended."""
    s = SqliteStore(":memory:")
    e = _use_only_edge("carpenter")
    s.add_edge(e)
    try:
        s.confirm_edge(U, e.id, actor="user", call_path="harness",
                       correlation_id="c-0001", request_digest=None,
                       confirmed_at="2026-08-23T00:00:00Z")
        raise AssertionError("confirm_edge accepted a use_only edge")
    except ValueError as err:
        assert "not assertable" in str(err)


def vector_affirmation_makes_the_fact_assertable():
    """R3-1: the v5 affirmation contract, BOTH shapes, measured. Same
    value: the user edge becomes the ASSERTABLE carrier and the use_only
    prior persists un-asserted (nothing to supersede — the value did not
    change; R4-2: the two records RENDER IN SEPARATE PARTITIONS, measured
    below). Different value: the
    ladder retires the prior. ASSISTANT slots in at rung 1; the same
    paths hold."""
    # shape 1: same value — assertable via the user edge, prior persists
    s = SqliteStore(":memory:")
    prior = _use_only_edge("carpenter")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    affirmation = _edge("carpenter")            # plain USER evidence
    apply_supersession(s, affirmation, DEFAULT_RELATIONS)
    by_id = {e.id: e for e in s.edges(U)}
    assert by_id[affirmation.id].assertable, "the affirmed fact must ground"
    assert not by_id[prior.id].assertable, "the prior must stay un-asserted"
    # R4-2, the RENDERED result (the reviewer measured what storage-state
    # assertions had stood in for): collapse groups by (subject, relation,
    # disclosure, author, derived_from), so the two records surface in
    # SEPARATE trust partitions — 0012's envelope isolation, preserved.
    from veracium.graph import collapse_for_render
    surfaced, _info = collapse_for_render(list(by_id.values()))
    assert len(surfaced) == 2, "cross-class records must NOT collapse"
    # R5-3: the REAL surface — collapse alone neither partitions nor
    # renders. gate.partition_parts is what recall's renderer consumes:
    # the user record must appear ONLY in the grounded edge lines, the
    # assistant-class record ONLY in the unverified block, origin marker
    # present, no cross-partition leakage.
    from veracium.gate import partition_parts
    edge_lines, ep_lines, claim_lines, tp_ep_lines = partition_parts(
        surfaced, [])
    grounded = "\n".join(edge_lines)
    unverified = "\n".join(claim_lines)
    assert "carpenter" in grounded, "the affirmed user fact must ground"
    assert "carpenter" in unverified, (
        "the assistant-class record must surface in the unverified block")
    assert "third-party-reported" in unverified, (
        "the origin marker must be present on the unverified record")
    assert "third-party-reported" not in grounded, (
        "no origin marker may leak into the grounded block")
    assert not any(l in edge_lines for l in claim_lines), (
        "no line may appear in both partitions")
    # shape 2: different value — the ladder retires the prior
    s2 = SqliteStore(":memory:")
    prior2 = _use_only_edge("carpenter")
    apply_supersession(s2, prior2, DEFAULT_RELATIONS)
    correction = _edge("plumber")               # user CORRECTS the claim
    apply_supersession(s2, correction, DEFAULT_RELATIONS)
    retired = next(e for e in s2.edges(U, active_only=False)
                   if e.id == prior2.id)
    assert not retired.active, "a differing user value must retire the prior"


def vector_cross_class_absorption_stays_blocked():
    """R3-3 cell 1: mentionable USER evidence does NOT absorb a use_only
    prior — both persist (the 0.4.1 equal-disclosure-class guard). v4
    claimed the absorption; the reviewer measured both records active on
    a NON-functional relation, where supersession cannot mask it."""
    s = SqliteStore(":memory:")
    prior = _use_only_edge("likes hiking", rel="has_hobby")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    inc = _edge("likes hiking in the alps", rel="has_hobby")
    apply_supersession(s, inc, DEFAULT_RELATIONS)
    active_ids = {e.id for e in s.edges(U) if e.active}
    assert {prior.id, inc.id} <= active_ids, (
        "cross-class absorption happened — the 0.4.1 guard moved")


def vector_same_class_restatement_persists_untouched():
    """R3-3 cell 2: a same-class restatement PERSISTS and the prior is
    byte-unchanged (0012's persist-and-collapse; no store-side merge).
    This is I10a's shipped ground."""
    s = SqliteStore(":memory:")
    prior = _use_only_edge("likes hiking", rel="has_hobby")
    apply_supersession(s, prior, DEFAULT_RELATIONS)
    before = next(e for e in s.edges(U) if e.id == prior.id
                  ).model_dump_json()
    restatement = _use_only_edge("likes hiking", rel="has_hobby")
    apply_supersession(s, restatement, DEFAULT_RELATIONS)
    after = next(e for e in s.edges(U, active_only=False)
                 if e.id == prior.id).model_dump_json()
    assert after == before, "the prior moved — 0012 persists untouched"


def vector_old_reader_refuses_a_newer_store_at_open():
    """R3-2: 0007's guard fires ONLY when a newer store is stamped — the
    reason v5 bumps SCHEMA_VERSION 10→11. Measured: a store stamped one
    version ahead refuses AT OPEN, before any edge validates."""
    import tempfile
    from veracium.store import schema_version as sv
    with tempfile.TemporaryDirectory() as td:
        db = str(pathlib.Path(td) / "future.db")
        s = SqliteStore(db)
        s.add_edge(_edge("carpenter"))
        s._conn.execute(f"PRAGMA user_version = {sv.SCHEMA_VERSION + 1}")
        s._conn.commit()
        s.close()
        try:
            SqliteStore(db)
            raise AssertionError("an old reader opened a newer store")
        except Exception as err:                 # noqa: BLE001
            # R4-4: EXACT — the shipped refusal, not merely "some exception
            # that is not ValidationError"
            assert type(err).__name__ == "StoreVersionError", type(err)
            assert getattr(err, "reason", None) == "newer", (
                f"expected reason='newer', got {getattr(err, 'reason', None)!r}")


def vector_the_1000_edge_selection_today():
    """R3-4: the 1,000+1 fixture, measured. The reviewer's enum-patched
    run returned `selected=40 user_selected=[]`; this stand-in fixture
    may rank differently (the printed line reports what THIS tree does).
    Either way the point stands: today the outcome is RANKING-INCIDENTAL,
    and the I6 reserve rule (min(count_assertable, ceil(40/4)) slots)
    makes the user edge's selection GUARANTEED. The I6 test asserts the
    guarantee; this vector records the pre-rule ground."""
    s = SqliteStore(":memory:")
    user_edge = _edge("the user's own fact", rel="works_as", days_ago=400)
    s.add_edge(user_edge)
    for i in range(1000):
        s.add_edge(_use_only_edge(f"assistant fact {i}",
                                  rel="works_as", days_ago=1))
    # R5-2: coverage_share is pinned to the SHIPPED MemoryConfig default
    # (0.0) — the function default of 0.25 masked the reviewer's measured
    # failure in the earlier form of this vector.
    picked = subgraph_for_query(s, U, "works fact", max_edges=40,
                                coverage_share=0.0,
                                relations=DEFAULT_RELATIONS)
    ids = {e.id for e in picked}
    assert len(ids) <= 40
    print(f"    (today: user edge selected = {user_edge.id in ids} — "
          f"the I6 rule requires True at implementation)")


def main() -> int:
    vectors = [v for n, v in sorted(globals().items())
               if n.startswith("vector_")]
    for v in vectors:
        v()
        print(f"ok  {v.__name__}")
    print(f"{len(vectors)} vectors — the shipped contracts the CURRENT candidate is "
          f"written against; candidate deltas stated per vector")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
