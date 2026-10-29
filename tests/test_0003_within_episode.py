"""specs/0003/within-episode (amendment v0.3, research 144bf417; the owner, 2026-10-29: "Contest, retire nothing"):
one episode that names two value groups for a functional (subject, relation) key.

The defect (dev's order-only probe, coordination de53717): `ingest` applied supersession per extracted edge in emission
order, so "I moved and now live in Denver (previously lived in Boston)." emitted as [Denver, Boston] left Boston current.
§4a, the extraction rule, is the fix; §4b, the net tested here, makes the outcome independent of emission order: a
contested key retires nothing, and §4c's refusal rows name every pair of differing value groups. Driven through
`Memory.remember` with a scripted extractor, so every cell runs the shipped ingest.
"""

import itertools
import json
import tempfile

import pytest

from veracium import EvidenceContext, Memory, MemoryConfig

U = "u"
TEXT = "USER: I moved and now live in Denver (previously lived in Boston)."
RULE = ('A value the event says is NO LONGER true ("previously", "used to",\n'
        '  "formerly", "no longer", "moved from", "before that") is history, not a\n'
        '  current fact: do NOT emit it as a triple')


class Scripted:
    """Each distill call emits the next scripted list of `located_at` objects; captures every prompt it is sent."""

    def __init__(self, *scripts):
        self.scripts, self.prompts = list(scripts), []

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            self.prompts.append(prompt)
            objs = self.scripts.pop(0)
            if objs is None:
                return "not json"
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": o,
                                            "volatility": "durable"} for o in objs],
                               "episode": "The user talked about where they live.", "instructions": []})
        return ""


def _run(d, *scripts):
    """One remember() per script, in order; the last one is the episode under test. Returns (memory, its result)."""
    llm = Scripted(*scripts)
    m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    r = None
    for i in range(len(scripts)):
        r = m.remember(U, TEXT if i == len(scripts) - 1 else "USER: I live there.", date=f"2026-10-0{i + 1}",
                       context=EvidenceContext.direct())
    return m, r, llm


def _located(m):
    return [e for e in m.store.edges(U, active_only=False) if e.relation == "located_at"]


def _active(m):
    return sorted(e.object for e in _located(m) if e.active)


def _retired(m):
    return sorted((e.object, e.invalidation_reason) for e in _located(m) if not e.active)


def _rows(m):
    """The refusal rows as (prior object, incoming object, rule_version): ids are fresh per run."""
    obj = {e.id: e.object for e in _located(m)}
    return sorted((obj[p], obj[i], v) for p, i, v in m.store._conn.execute(
        "SELECT prior_edge_id, incoming_edge_id, rule_version FROM supersession_refusals WHERE user_id=?", (U,)))


def _outcome(prior, values):
    with tempfile.TemporaryDirectory() as d:
        m, r, _ = _run(d, *([prior] if prior else []), values)
        return _active(m), _retired(m), _rows(m), r.get("within_episode_contested")


# ---- INV-WE1: order-independence; a refinement is not a contest ---------------------------------------------------

@pytest.mark.parametrize("prior", [None, ["Boston"]], ids=["no-prior", "prior-boston"])
@pytest.mark.parametrize("values", [["Denver", "Boston"], ["Denver", "Boston", "Austin"]], ids=["two", "three"])
def test_every_emission_order_leaves_the_same_active_set_and_row_set(prior, values):
    """Mutant: today's per-edge supersession in emission order (the active set then follows the last value)."""
    outcomes = {tuple(map(str, _outcome(prior, list(p)))) for p in itertools.permutations(values)}
    assert len(outcomes) == 1, outcomes
    active, retired, rows, contested = _outcome(prior, values)
    assert set(values) <= set(active) and retired == [] and contested == 1, (active, retired, contested)
    assert rows and all(v == "within-episode-v1" for _, _, v in rows), rows


@pytest.mark.parametrize("values", [["Denver", "Denver, Colorado"], ["Denver, Colorado", "Denver"]])
def test_a_refinement_of_one_city_is_not_a_contest(values):
    """Mutant: grouping by `_value_key` (which makes "Denver" and "Denver, Colorado" two values)."""
    active, retired, rows, contested = _outcome(["Boston"], values)
    assert contested == 0 and rows == [], (contested, rows)
    assert ("Boston", "superseded") in retired, retired
    assert active and all(a.startswith("Denver") for a in active), active


# ---- INV-WE2 / WE3: a contested key retires nothing; a single value behaves as today -----------------------------

@pytest.mark.parametrize("values", [["Denver", "Boston"], ["Boston", "Denver"]])
def test_a_contested_key_retires_no_prior_and_no_own_edge(values):
    """Mutant: priors retired by the first new value before the group is checked."""
    active, retired, _, contested = _outcome(["Boston"], values)
    assert retired == [] and contested == 1, retired
    assert active.count("Boston") == 2 and "Denver" in active, active        # the prior, and its reinforcement


def test_a_shorter_value_of_its_own_group_is_not_absorbed_in_a_contested_key():
    """"Denver" beside "Denver, Colorado" AND "Denver, Texas" is subsumed by two anchors, so it is its own value group
    (value_groups' ambiguous cell). Absorption would retire it; in a contested key only a SAME-group prior is
    absorbed. Mutant: the absorption guard removed."""
    active, retired, _, contested = _outcome(None, ["Denver", "Denver, Colorado", "Denver, Texas"])
    assert contested == 1 and retired == [], (contested, retired)
    assert sorted(active) == ["Denver", "Denver, Colorado", "Denver, Texas"], active


def test_a_single_value_episode_supersedes_as_today():
    """Mutant: the group check applied to every key (no supersession at all)."""
    active, retired, rows, contested = _outcome(["Boston"], ["Denver"])
    assert active == ["Denver"] and retired == [("Boston", "superseded")] and rows == [] and contested == 0


def test_a_key_already_holding_both_values_still_records_its_contest():
    """§4c's 'at least one row per contested key' when every edge of the episode REINFORCES (no retire would have
    happened today either): the rows are owed by the contest, not by a withheld retire. Counted for the LAST episode
    only: the second episode, itself contested, legitimately wrote rows. Mutant: reinforcement's rows omitted."""
    with tempfile.TemporaryDirectory() as d:
        llm = Scripted(["Austin"], ["Boston", "Austin"], ["Austin", "Boston"])
        m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
        for i in range(2):
            m.remember(U, "USER: I live there.", date=f"2026-10-0{i + 1}", context=EvidenceContext.direct())
        before = _rows(m)
        r = m.remember(U, TEXT, date="2026-10-03", context=EvidenceContext.direct())
        added = [x for x in _rows(m) if x not in before or _rows(m).count(x) > before.count(x)]
        assert r.get("within_episode_contested") == 1, r
        assert [x for x in added if x[2] == "within-episode-v1"], (before, _rows(m))



def test_a_ladder_refusal_in_a_contested_key_keeps_its_own_row_and_gets_no_second():
    """A THIRD-PARTY episode naming two values over the user's own prior: the author ladder refuses that pair itself,
    so its row stands under the ladder's rule_version and no within-episode row is added for it (INV-WE4). Mutant:
    the ladder's pairs not excluded (every named pair also drafted within-episode)."""
    from veracium import EvidenceAuthor
    with tempfile.TemporaryDirectory() as d:
        llm = Scripted(["Boston"], ["Denver", "Boston"])
        m = Memory(llm=llm, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
        m.remember(U, "USER: I live there.", date="2026-10-01", context=EvidenceContext.direct())
        r = m.remember(U, "Forwarded: the user lives in Denver, not Boston.", date="2026-10-02",
                       author=EvidenceAuthor.THIRD_PARTY)
        assert r.get("within_episode_contested") == 1, r
        user_prior = next(e for e in _located(m) if e.provenance.author_of_evidence == EvidenceAuthor.USER)
        rows = m.store._conn.execute("SELECT incoming_edge_id, rule_version FROM supersession_refusals "
                                     "WHERE user_id=? AND prior_edge_id=?", (U, user_prior.id)).fetchall()
        incoming = {e.id: e.object for e in _located(m)}
        for_denver = [v for i, v in rows if incoming[i] == "Denver"]
        assert for_denver == ["supersession-authority-v2"], rows


def test_one_grouping_decides_the_contest_with_the_priors():
    """A prior "Denver, Colorado" joins the episode's "Denver" and "Colorado" into ONE group, so the key is not
    contested (INV-WE9). Mutant: the contest decided over the episode's edges alone."""
    active, retired, rows, contested = _outcome(["Denver, Colorado"], ["Denver", "Colorado"])
    assert contested == 0 and rows == [] and retired == [], (contested, rows, retired)

# ---- INV-WE4: the row and the counter -------------------------------------------------------------------------------

def test_the_counter_is_present_and_zero_on_every_uncontested_path():
    """Read from `ingest_event`'s OWN result (beneath remember's re-export, which would raise first on an absent key).
    Mutant: the counter absent rather than 0 (an absent key is not a zero, 0025 §4c)."""
    from veracium import EvidenceAuthor
    from veracium.ingest import ingest_event
    for script, unparseable in ((["Denver"], False), (None, True)):
        with tempfile.TemporaryDirectory() as d:
            m = Memory(llm=None, config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db"))
            r = ingest_event(m.store, Scripted(script), U, event_text=TEXT, author=EvidenceAuthor.USER,
                             date="2026-10-01", context=EvidenceContext.direct(), relations=m.config.relations)
            assert bool(r.get("unparseable")) is unparseable, r
            assert "within_episode_contested" in r and r["within_episode_contested"] == 0, r


def test_the_counter_is_operator_only_over_mcp():
    from veracium import mcp_server
    assert "within_episode_contested" in mcp_server._OPERATOR_ONLY


# ---- INV-WE5: the rule is in the prompt the extractor RECEIVES ------------------------------------------------------

def test_the_extraction_rule_reaches_the_extractor():
    """Read from the prompt actually sent (a capturing completer). Mutant: the rule written to a constant not sent."""
    with tempfile.TemporaryDirectory() as d:
        _, _, llm = _run(d, ["Denver"])
        assert llm.prompts and RULE in llm.prompts[0], llm.prompts[0][-1200:]
        assert '"since 2019", "for ten years"): emit it as usual.' in llm.prompts[0]


# ---- the refusal draft's new field: digest compatibility and the closed set ----------------------------------------

def test_a_ladder_refusal_serializes_exactly_as_before_the_field():
    """The logical digest binds each refusal's dump: an absent rule_version must not appear, or every receipt with a
    refusal committed before the change would read as a DIFFERENT request on a lost-response retry."""
    from veracium.schema import SupersessionRefusalDraft
    d = SupersessionRefusalDraft(prior_edge_id="p", incoming_edge_id="i", relation="located_at",
                                 prior_effective=3, incoming_effective=1)
    assert json.loads(d.model_dump_json()) == {"prior_edge_id": "p", "incoming_edge_id": "i", "relation": "located_at",
                                                "prior_effective": 3, "incoming_effective": 1}
    w = d.model_copy(update={"rule_version": "within-episode-v1"})
    assert json.loads(w.model_dump_json()).get("rule_version") == "within-episode-v1"



def test_the_drafts_closed_type_is_the_authority_modules_closed_set():
    """Two carriers of one closed set: the draft's Literal type and authority.DRAFTED_RULE_VERSIONS. A value added to
    one and not the other fails here, and the model itself refuses a value outside its type."""
    import typing
    from veracium import authority
    from veracium.schema import SupersessionRefusalDraft
    lit = [a for a in typing.get_args(SupersessionRefusalDraft.model_fields["rule_version"].annotation) if a is not type(None)]
    assert typing.get_args(lit[0]) == authority.DRAFTED_RULE_VERSIONS == (authority.WITHIN_EPISODE_RULE_VERSION,)
    with pytest.raises(ValueError):
        SupersessionRefusalDraft(prior_edge_id="p", incoming_edge_id="i", relation="r", prior_effective=1,
                                 incoming_effective=1, rule_version="made-up")

def test_the_store_refuses_a_rule_version_outside_the_closed_set():
    from veracium.graph import _build_supersession_plan
    from veracium.schema import Edge, EvidenceAuthor, Provenance
    with tempfile.TemporaryDirectory() as d:
        m, _, _ = _run(d, ["Boston"])
        prior = next(e for e in _located(m) if e.active)
        inc = Edge(id="e-new", user_id=U, subject="user", relation="located_at", object="Denver",
                   provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="x"))
        plan, _ = _build_supersession_plan(m.store, inc, m.config.relations, "sup-e-new", within_episode=(prior,))
        assert [r.rule_version for r in plan.refusals] == ["within-episode-v1"] and not plan.prior_invalidations
        plan.refusals[0] = plan.refusals[0].model_copy(update={"rule_version": "made-up"})
        with pytest.raises(ValueError, match="rule_version"):
            m.store.apply_supersession_plan(plan)
        assert m.store._conn.execute("SELECT COUNT(*) FROM supersession_refusals").fetchone()[0] == 0
