"""specs/0027 §4a Stage 2 — the I6 reserve's relevance set, pinned; and the policy
lane's invariant (a policy contributes to `fused_score` only, never to `rel_ext`).

The ordered implementation (research, 2026-09-12, on the owner's word "add a
distinct policy lane parameter that feeds fused_score but not rel_ext"): PIN what
exists first — `rel_ext = relevant_ids | sm_rank` had no test at all — then the
negative control, SEEN TO FAIL against the `sm`-overloading route before the
parameter that satisfies it exists. The two tests are the deliverable as a PAIR:
the control alone could pass by breaking the semantic lane.

The fixture is the unit seam the existing 0027 tests use: `scored` /
`relevant_ids` / `by_id` built directly, so the reserve is exercised with
`max_edges` smaller than the candidate set. The reserve is OBSERVED from the
output: with every candidate assertable and lexically relevant, the first
⌈max_edges/4⌉ positions are the reserve in fused order (V1's own assertion in
test_0027_semantic_recall.py); a candidate that is NOT in `rel_ext` can never
occupy one of them, whatever its fused rank."""

import importlib.util
import pathlib

import pytest

from veracium.graph import RRF_K, fused_subgraph


def _base_module():
    """The 0027 test module's fixture helpers (`_edge`, `U`), loaded by PATH: the
    tests directory is not a package, and `import tests.…` resolved only when
    the invocation happened to put the repo root on sys.path — CI's did not
    (five red jobs at ca4674d, ModuleNotFoundError: No module named 'tests')."""
    path = pathlib.Path(__file__).with_name("test_0027_semantic_recall.py")
    spec = importlib.util.spec_from_file_location("test_0027_semantic_recall_base", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = _base_module()
U = base.U
_edge = base._edge


def _lexical_fixture(n=12, max_edges=8):
    """n lexically relevant, assertable edges, in a fixed lexical order; the
    reserve holds ⌈max_edges/4⌉ = 2 of them."""
    edges = [_edge(f"x{i:02d}", "user", "likes", f"boat topic{i}", days=i) for i in range(n)]
    scored = [(10 - i * 0.1, 1, e) for i, e in enumerate(edges)]      # (score, overlap>0, edge)
    relevant = {e.id for e in edges}
    by_id = {e.id: e for e in edges}
    return edges, scored, relevant, by_id, max_edges


def _reserve_size(max_edges):
    return -(-max_edges // 4)


# ------------------------------------------------ step 1: pin what exists ----
def test_the_reserve_reads_the_extended_relevance_set_semantic_yes_non_entry_no():
    """CHARACTERISATION (0027 §4a Stage 2, the R2-3 ruling): a semantic-lane entry
    that is not lexically relevant IS reserve-eligible — `rel_ext` extends
    `relevant_ids` by `sm_rank` — and a candidate in neither set is not, however
    high its fused rank. Both halves observed from the output, not the internals."""
    edges, scored, relevant, by_id, max_edges = _lexical_fixture()
    # a semantic-only arrival: assertable, NOT in scored/relevant, in `sm` at rank 1
    sem = _edge("sem", "user", "enjoys", "harbor walks", days=30)
    by_id["sem"] = sem
    out, meta = fused_subgraph(scored, relevant, by_id, [("sem", 0.9)], max_edges=max_edges)
    got = [e.id for e in out]
    assert meta["sem"]["route"] == "semantic" and meta["sem"]["fused_rank"] == 1
    # rank 1 in the semantic lane alone ties lexical rank 1 (both 1/61); the
    # tiebreak is recency and `sem` (day 30) is the newest, so it leads — and
    # it holds a RESERVE slot, which is the claim
    assert got[: _reserve_size(max_edges)] == ["sem", "x00"], got
    # the SAME candidate NOT in the semantic lane but with the SAME fused rank is
    # not eligible: give it lexical rank 1 with overlap 0 (the eligibility floor —
    # a user-subject edge present only via the floor, route "lexical", overlap 0)
    floor = _edge("flr", "user", "enjoys", "hill walks", days=30)
    scored2 = [(99.0, 0, floor)] + scored          # top lexical rank, but overlap 0
    by_id2 = {**by_id, "flr": floor}
    del by_id2["sem"]
    out2, meta2 = fused_subgraph(scored2, relevant, by_id2, [], max_edges=max_edges)
    got2 = [e.id for e in out2]
    assert meta2["flr"]["fused_rank"] == 1 and meta2["flr"]["route"] == "lexical"
    assert "flr" not in got2[: _reserve_size(max_edges)], (
        "a candidate outside rel_ext took a reserve slot: " + str(got2))
    assert got2[: _reserve_size(max_edges)] == ["x00", "x01"], got2


# ------------------------------------------- step 2: the negative control ----
def _apply_policy_via_sm(scored, relevant, by_id, policy, *, max_edges):
    """THE ROUTE ANYONE WOULD REACH FOR — and the hazard: express the policy as a
    semantic-lane list. It ranks the target exactly as the policy lane would
    (research measured it), and it ALSO puts the target in `rel_ext`."""
    sm = sorted(policy, key=policy.get)
    return fused_subgraph(scored, relevant, by_id, [(eid, 0.0) for eid in sm], max_edges=max_edges)


def _apply_policy_via_parameter(scored, relevant, by_id, policy, *, max_edges):
    """The approved design: a distinct parameter that feeds fused_score only."""
    return fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges, policy_rank=policy)


def _policy_target_is_not_reserve_eligible(apply):
    """The invariant, as a function of the route, asserted as the PROPERTY the
    mechanism exists to produce rather than as membership of an internal set
    (research's re-measurement, 2026-09-12): a policy-ranked candidate that is
    neither lexically relevant nor a semantic entry cannot occupy any of the
    ⌈max_edges/4⌉ reserve slots, so at policy rank 1 it lands at EXACTLY the
    first position after the reserve — reserve_n + 1. Through the `sm` route it
    lands at position 1, inside protected evidence. A position assertion
    survives any refactor of how `rel_ext` is computed."""
    edges, scored, relevant, by_id, max_edges = _lexical_fixture()
    target = _edge("pol", "user", "enjoys", "harbor walks", days=30)
    # present via the floor at the BOTTOM of the lexical lane (overlap 0, not
    # relevant, lexical rank 13): without a policy it is outside the budget, so
    # everything observed below is the policy's doing — research's census found
    # the other exception class, a target already returned, and this rules it out
    scored = scored + [(0.0, 0, target)]
    by_id["pol"] = target
    base, _ = fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges)
    assert "pol" not in [e.id for e in base], "fixture drift: the target must not be returned without a policy"
    out, meta = apply(scored, relevant, by_id, {"pol": 1}, max_edges=max_edges)
    got = [e.id for e in out]
    # PRECONDITION, asserted rather than assumed (research's census, 2026-09-12:
    # 51 of 57 exceptions to the position rule were recalls that did not
    # truncate — when stage3 fits the budget the reserve is never computed and a
    # promoted record correctly sits at position 1; the rule is conditional on
    # truncation, and a fixture that shrinks below the budget would pass here
    # for the wrong reason)
    assert len(scored) > max_edges and len(got) == max_edges, (
        f"fixture no longer truncates ({len(scored)} candidates, budget {max_edges}): the reserve is not exercised")
    assert "pol" in meta, "the policy must rank the target into the selection"
    position = got.index("pol") + 1
    assert position > _reserve_size(max_edges), (
        f"a POLICY-ranked candidate took a protected-reserve slot (position {position}): {got}")
    assert position == _reserve_size(max_edges) + 1, (
        f"the policy target should land at the first slot after the reserve, not {position}: {got}")
    return got, meta


def test_the_sm_route_grants_reserve_eligibility_the_hazard_is_real():
    """STEP 2, SEEN TO FAIL: the control run against the `sm`-overloading route
    must FAIL — the policy target takes a reserve slot. Pinned as the executed
    evidence that the hazard is real; a control never seen to fail is an
    assertion. (This test asserts the FAILURE of the invariant on the wrong
    route, so it stays green after the parameter lands.)"""
    with pytest.raises(AssertionError, match=r"took a protected-reserve slot \(position 1\)"):
        _policy_target_is_not_reserve_eligible(_apply_policy_via_sm)


def test_a_policy_lane_entry_does_not_gain_reserve_eligibility():
    """THE NEGATIVE CONTROL for the approved parameter: `policy_rank` feeds
    `fused_score` only — never `rel_ext`, never Stage 3 membership. Fails until
    step 4 lands (TypeError: no such parameter), then passes; the pair with the
    characterisation test above is the deliverable."""
    got, meta = _policy_target_is_not_reserve_eligible(_apply_policy_via_parameter)
    # the policy DID rank it: lexical rank 13 (1/73) plus policy rank 1 (1/61)
    # outscores every single-lane candidate, so it is FIRST in fused order — yet
    # it sits at reserve_n + 1 in the OUTPUT, because the reserve is taken from
    # rel_ext and it is not in it
    assert meta["pol"]["fused_rank"] == 1, meta["pol"]


# ---------------------------------------- the invariant's other two edges ----
def test_a_policy_id_outside_both_lanes_gets_no_membership_and_a_bad_rank_is_refused():
    """Bullets 1 and 3 of the Stage 2 amendment: a policy id that is neither a
    lexical candidate nor a semantic entry gets no term and NO membership — it
    does not appear in the output or in `meta`, whatever its rank — and a
    malformed rank (0, negative, non-int, bool) is a programming error, refused
    rather than skipped."""
    edges, scored, relevant, by_id, max_edges = _lexical_fixture()
    ghost = _edge("ghost", "user", "enjoys", "harbor walks", days=30)
    by_id["ghost"] = ghost                     # known to the store, in neither lane
    out, meta = fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges, policy_rank={"ghost": 1})
    assert "ghost" not in meta and "ghost" not in [e.id for e in out]
    # and with the policy naming nothing real, the output equals the no-policy output (V10's shape)
    out0, meta0 = fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges)
    assert [e.id for e in out] == [e.id for e in out0] and meta == meta0
    for bad in (0, -1, 1.5, True, "1"):
        with pytest.raises(ValueError, match="must be an int >= 1"):
            fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges, policy_rank={"x00": bad})


def test_the_policy_lane_is_inert_when_absent_and_bounded_per_lane():
    """Bullets 4 and 5: `policy_rank=None` and `{}` are byte-identical to the
    two-lane construction (V10's guard, here on the unit seam), and a lane's
    contribution is at most 1/(RRF_K + 1) — three lanes at rank 1 give
    exactly 3/61, the per-lane bound the spec states."""
    edges, scored, relevant, by_id, max_edges = _lexical_fixture()
    base_out, base_meta = fused_subgraph(scored, relevant, by_id, [("x03", 0.9)], max_edges=max_edges)
    for absent in (None, {}):
        out, meta = fused_subgraph(scored, relevant, by_id, [("x03", 0.9)], max_edges=max_edges, policy_rank=absent)
        assert [e.id for e in out] == [e.id for e in base_out] and meta == base_meta
    # x00 is lexical rank 1; make it semantic rank 1 and policy rank 1: three lanes
    out, meta = fused_subgraph(scored, relevant, by_id, [("x00", 0.9)], max_edges=max_edges, policy_rank={"x00": 1})
    assert abs(meta["x00"]["fused_score"] - 3.0 / (RRF_K + 1)) < 1e-12
    assert meta["x00"]["route"] == "both"      # route names the two membership lanes only


def test_a_policy_promotion_displaces_only_the_record_at_the_budget_boundary():
    """The marginal-record property (research's census: 1,309 of 1,309
    displacing configurations displaced exactly the last record kept): under
    truncation, promoting one record that was not already returned removes
    exactly the previous last record and nothing else — every other member and
    its relative order survive. The policy makes the recall drop record 40
    instead of 41; it never reaches into the middle."""
    edges, scored, relevant, by_id, max_edges = _lexical_fixture()
    target = _edge("pol", "user", "enjoys", "harbor walks", days=30)
    scored = scored + [(0.0, 0, target)]             # bottom of the lexical lane, not returned today
    by_id["pol"] = target
    base, _ = fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges)
    base_ids = [e.id for e in base]
    assert len(base_ids) == max_edges and "pol" not in base_ids, base_ids   # truncates; target not returned
    out, _ = fused_subgraph(scored, relevant, by_id, [], max_edges=max_edges, policy_rank={"pol": 1})
    got = [e.id for e in out]
    displaced = [i for i in base_ids if i not in got]
    assert displaced == [base_ids[-1]], f"displaced {displaced}, expected only the boundary record {base_ids[-1]!r}"
    kept = [i for i in got if i != "pol"]
    assert kept == base_ids[:-1], "a surviving record moved relative to the others"

