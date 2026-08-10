"""specs/0012 (accepted v17) — the I10 budget machinery, part 2: rendering-side
invariants (I10a clamps, I10b ordered+reported overflow, I10c framing survival, I10d
no-new-reach, I10f precedence, I10g the serialized bound, I10i contested packing, and
the R11-2 heading clamp / K validation named checks).
"""
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

import veracium
from veracium.budgets import est_tokens, floor_for
from veracium.config import MemoryConfig
from veracium.graph import apply_supersession
from veracium.proactive import assemble
from veracium.schema import (DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor,
                             Provenance, SourceType, Volatility)
from veracium.store.sqlite import SqliteStore

U = "u"
NOW = datetime.now(timezone.utc)


def _edge(eid, obj, *, author=EvidenceAuthor.USER, disc=Disclosure.MENTIONABLE,
          rel="works_as", note="", vol=Volatility.SLOW, flag=False, days=1):
    t = NOW - timedelta(days=days)
    return Edge(id=eid, user_id=U, subject="user", relation=rel, object=obj, note=note,
                volatility=vol, valid_from=t, needs_confirmation=flag,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=author, evidence_ref=f"ev-{eid}",
                                      disclosure=disc, observed_at=t))


def _mem(tmp_path, **cfg):
    return veracium.Memory(llm=lambda p, **k: "## USER MODEL\n- A fact.",
                           config=MemoryConfig(db_path=str(tmp_path / "m.db"), **cfg))


# --- I10a: one oversized item cannot break a budget ------------------------------------
def test_a_single_oversized_item_is_clamped_not_emitted(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("big", "x" * 500_000))            # 500K-char object
    r = mem.recall(U, "x", token_budget=400)
    assert r.tokens_estimated <= 400                            # never sails through whole
    assert r.truncated
    assert "…" in r.context                                     # the elision marker
    # oversized as the FIRST item under a tight budget: still clamped, still present
    assert "x" in r.context
    mem.close()


# --- I10b: overflow is ordered, deterministic, and NEVER silent ------------------------
def test_safety_overflow_is_ordered_and_reported(tmp_path):
    mem = _mem(tmp_path)
    for i in range(6):
        mem.store.add_edge(_edge(f"d{i}", f"grounded detail item number {i} "
                                          f"with verbose content", rel="works_on"))
    mem.store.add_edge(_edge("q1", "the user owes $2,400", disc=Disclosure.QUARANTINED,
                             author=EvidenceAuthor.THIRD_PARTY, rel="finance_claim"))
    for i in range(8):
        mem.store.add_episode(__import__("veracium.schema", fromlist=["Episode"]).Episode(
            id=f"ep{i}", user_id=U, date=(NOW - timedelta(days=i)).date().isoformat(),
            summary=f"a verbose recent episode line number {i} occupying budget",
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=f"ep-{i}", observed_at=NOW)))
    r = mem.recall(U, "grounded detail owes", token_budget=300)
    assert r.truncated
    assert "[budget: dropped" in r.context                      # the report marker
    assert "SAFETY" in r.context                                # safety counted distinctly
    # deterministic: same call, same output
    r2 = mem.recall(U, "grounded detail owes", token_budget=300)
    assert r2.context == r.context
    mem.close()


# --- I10c: framing is never severed from the content it governs ------------------------
def test_clamping_never_severs_the_safety_label(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("stale", "y" * 100_000, flag=True))          # stale-flagged
    mem.store.add_edge(_edge("uo", "z" * 100_000, disc=Disclosure.USE_ONLY,
                             author=EvidenceAuthor.THIRD_PARTY, rel="located_at"))
    mem.store.add_edge(_edge("qc", "w" * 100_000, disc=Disclosure.QUARANTINED,
                             author=EvidenceAuthor.THIRD_PARTY, rel="finance_claim"))
    r = mem.recall(U, "y z w", token_budget=2000)
    assert "possibly stale" in r.context                        # end-positioned label intact
    assert "unconfirmed" in r.context                           # use_only label intact
    assert "never assert as fact" in (r.unverified or r.context)  # quarantine fence intact
    assert r.tokens_estimated <= 2000
    mem.close()


# --- I10d: proactive gives contested material NO NEW REACH -----------------------------
def test_proactive_grants_contested_no_new_reach(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    # a durable, unflagged, undated, non-transient contested pair (functional contention)
    s.add_edge(_edge("p1", "CFO at Acme", vol=Volatility.DURABLE, days=5))
    apply_supersession(s, _edge("p2", "janitor", author=EvidenceAuthor.THIRD_PARTY,
                                disc=Disclosure.QUARANTINED, vol=Volatility.DURABLE),
                       DEFAULT_RELATIONS)
    ctx, edges, _eps, _tr = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert "CFO at Acme" not in ctx                             # no contested tier exists
    assert "janitor" not in ctx                                 # fenced never volunteered
    # the same grounded fact, when FLAGGED, appears via the ordinary WARNING tier
    flagged = next(e for e in s.edges(U, active_only=True) if e.id == "p1")
    flagged.needs_confirmation = True
    s.add_edge(flagged)
    ctx2, *_ = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert "CFO at Acme" in ctx2 and "confirm when natural" in ctx2


# --- I10f: overlapping classifications take the highest class --------------------------
def test_overlapping_classifications_take_the_highest_class(tmp_path):
    s = SqliteStore(str(tmp_path / "s.db"))
    due = (NOW + timedelta(days=2)).date().isoformat()
    s.add_edge(_edge("both", f"file the report by {due}", note=f"due {due}",
                     flag=True, days=300))                      # flagged AND dated
    ctx, *_ = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW)
    assert ctx.count("file the report") == 1                    # renders ONCE
    assert "confirm when natural" in ctx                        # ...in the WARNING tier
    assert "DATED COMMITMENTS" not in ctx                       # not demoted to commitment

    # the R8-2 case: an UNRELATED flagged warning vs a query-matched quarantined claim
    # under a one-item budget — the claim flag wins AND renders fenced
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("warn", "unrelated legacy system fact " * 40, flag=True,
                             rel="works_on", days=400))
    mem.store.add_edge(_edge("claim", "the user owes $2,400",
                             disc=Disclosure.QUARANTINED,
                             author=EvidenceAuthor.THIRD_PARTY, rel="finance_claim"))
    r = mem.recall(U, "owes money debts", token_budget=floor_for("recall") + 30)
    assert "$2,400" in (r.unverified or "")                     # the claim survives, fenced
    assert "legacy system" not in r.context                     # the unrelated warning waits
    mem.close()


# --- I10g: the serialized text never exceeds its bound ---------------------------------
def test_the_serialized_prompt_never_exceeds_its_bound(tmp_path):
    mem = _mem(tmp_path)
    for i in range(40):                                         # saturate
        mem.store.add_edge(_edge(f"s{i}", f"saturation fact {i} " + "detail " * 30,
                                 rel="works_on", note=f"note {i}", flag=(i % 3 == 0)))
    for budget in (floor_for("recall"), 400, 900):
        r = mem.recall(U, "saturation detail", token_budget=budget)
        assert est_tokens(r.context) <= budget, f"recall overflow at {budget}"
    ctx, *_ = assemble(mem.store, U, mem.config, now=NOW,
                       token_budget=floor_for("proactive"))
    assert est_tokens(ctx) <= floor_for("proactive")
    mem.close()


# --- I10i: one contention group cannot break a budget (packing) ------------------------
def test_one_oversized_contention_group_is_bounded(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("prior", "grounded value " + "verbose " * 40))
    for i in range(20):                                         # a large n-way contention
        apply_supersession(mem.store,
                           _edge(f"ch{i}", f"challenger value {i} " + "verbose " * 40,
                                 author=EvidenceAuthor.THIRD_PARTY,
                                 disc=Disclosure.QUARANTINED),
                           mem.config.relations)
    r = mem.recall(U, "value", token_budget=400)
    assert r.tokens_estimated <= 400                            # the group is PACKED
    assert "grounded value" in r.context                        # the mandatory member renders
    assert r.truncated
    mem.close()


# --- R11-2/R12-2: the named heading-clamp check ----------------------------------------
def test_oversized_subject_and_relation_are_heading_clamped(tmp_path):
    mem = _mem(tmp_path)
    big_subject = "s" * 10_000
    mem.store.add_edge(Edge(
        id="hs", user_id=U, subject=big_subject, relation="works_as",
        object="grounded", provenance=Provenance(
            source_type=SourceType.STATED, author_of_evidence=EvidenceAuthor.USER,
            evidence_ref="ev-hs", disclosure=Disclosure.MENTIONABLE)))
    apply_supersession(mem.store, Edge(
        id="hc", user_id=U, subject=big_subject, relation="works_as",
        object="challenger", provenance=Provenance(
            source_type=SourceType.STATED, author_of_evidence=EvidenceAuthor.THIRD_PARTY,
            evidence_ref="ev-hc", disclosure=Disclosure.QUARANTINED)),
        mem.config.relations)
    r = mem.recall(U, "grounded challenger works", token_budget=600)
    assert r.tokens_estimated <= 600                            # the heading clamped (48)
    assert "CONTESTED" in r.context or "grounded" in r.context  # the group still renders
    mem.close()
