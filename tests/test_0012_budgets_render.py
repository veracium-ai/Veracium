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
    """Every item type in the taxonomy: a 500K-char EDGE object, an oversized EPISODE
    summary, and an oversized cached WIKI BODY — each clamped at its cap with the
    recoverability-bearing elision marker, never emitted whole, truncated always set."""
    from veracium.budgets import ELISION_MARKER
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("big", "x" * 500_000))            # 500K-char edge object
    mem.store.add_episode(__import__("veracium.schema", fromlist=["Episode"]).Episode(
        id="bigep", user_id=U, date=NOW.date().isoformat(),
        summary="e" * 200_000,                                  # oversized episode
        provenance=Provenance(source_type=SourceType.STATED,
                              author_of_evidence=EvidenceAuthor.USER,
                              evidence_ref="bigep", observed_at=NOW)))
    r = mem.recall(U, "x", token_budget=900)
    assert r.tokens_estimated <= 900                            # never sails through whole
    assert r.truncated
    assert ELISION_MARKER in r.context                          # the frozen marker
    assert "x" in r.context                                     # clamped, still present
    # oversized WIKI BODY: an identity-fresh cache whose body dwarfs the render share
    from veracium.compile import _ENVELOPE, _policy_digest
    body = "w" * 100_000 + "\n[[veracium-wiki-compile:v1]] +0 facts / +0 episodes not compiled"
    mem.store.set_wiki(U, f"{_ENVELOPE}{_policy_digest(mem.config.relations)}\n{body}",
                       mem.store.store_version(U))
    mem2 = _mem(tmp_path, wiki_recompile_after_writes=10 ** 9)
    r2 = mem.recall(U, "x", token_budget=900)
    assert r2.tokens_estimated <= 900                           # share-clamped body
    assert "not compiled" in r2.context or "wiki" in r2.context.lower()  # framing kept
    assert r2.truncated
    mem.close(); mem2.close()


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
    """I10g on the ACTUAL serialized strings of all three surfaces — including the
    compiler call (system + prompt measured as sent, fixed scaffolding reserved)."""
    mem = _mem(tmp_path)
    for i in range(400):                                        # saturate
        mem.store.add_edge(_edge(f"s{i}", f"saturation fact {i} " + "detail " * 30,
                                 rel=f"topic_{i % 40}", note=f"note {i}",
                                 flag=(i % 3 == 0)))
    for budget in (floor_for("recall"), 400, 900):
        r = mem.recall(U, "saturation detail", token_budget=budget)
        assert est_tokens(r.context) <= budget, f"recall overflow at {budget}"
    ctx, *_ = assemble(mem.store, U, mem.config, now=NOW,
                       token_budget=floor_for("proactive"))
    assert est_tokens(ctx) <= floor_for("proactive")
    from veracium.compile import compile_wiki
    cap = {}
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        cap["t"] = est_tokens(prompt) + est_tokens(system or "")
        return "wiki"
    compile_wiki(mem.store, llm, U, mem.config.relations, wiki_input_budget=8000)
    assert cap["t"] <= 8000, f"compiler serialized {cap['t']} > its 8000 bound"
    compile_wiki(mem.store, llm, U, mem.config.relations,
                 wiki_input_budget=floor_for("wiki"))
    assert cap["t"] <= floor_for("wiki")            # at the floor, too
    mem.close()


# --- I10i: one contention group cannot break a budget (packing) ------------------------
def test_one_oversized_contention_group_is_bounded(tmp_path):
    """I10i with GROUNDED members: SYSTEM/mentionable challengers against a USER prior
    produce refusals whose exposed members are ALL assertable, so the group line packs
    real grounded values — the mandatory member renders content-clamped, the emitted
    count reduces below K, and the withheld count reports the remainder."""
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("prior", "grounded user value " + "verbose " * 40, days=9))
    for i in range(20):                          # 20 grounded same-class challengers
        apply_supersession(mem.store,
                           _edge(f"ch{i}", f"challenger value {i} " + "verbose " * 40,
                                 author=EvidenceAuthor.SYSTEM,
                                 disc=Disclosure.MENTIONABLE, days=8 - (i % 5)),
                           mem.config.relations)
    r = mem.recall(U, "challenger value verbose", token_budget=420)
    assert r.tokens_estimated <= 420                            # the packed store case
    assert "grounded user value" in r.context                   # the mandatory member
    assert "CONTESTED" in r.context

    # the DIRECT wide-group case (the reviewer's method — 0003 supersedes equal-authority
    # challengers, so a wide GROUNDED group must be constructed at the renderer boundary):
    # 300 grounded members through the packer under a tight line budget.
    from veracium.schema import ContestedGroup
    wide = ContestedGroup(subject="user", relation="works_as",
                          exposed=[_edge(f"m{i}", f"member value {i} " + "pad " * 10,
                                         author=EvidenceAuthor.USER, days=i % 30)
                                   for i in range(300)],
                          linkage=[])
    block, spent, truncated = mem._render_contested([wide], 420, mem._est_tokens)
    assert mem._est_tokens(block) <= 420                        # one group NEVER breaks it
    import re as _re
    m = _re.search(r"\(\+(\d+) more contending values withheld\)", block)
    assert m and int(m.group(1)) >= 294                         # the withheld count
    shown = block.count("member value")
    assert 1 <= shown <= mem.config.contested_members_per_line  # dynamic, bounded by K
    assert truncated                                            # withholding SIGNALS (I10i)
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


# --- I10 (the headline check): hard-bounded against variant floods ---------------------
def test_read_surfaces_are_hard_bounded_against_variant_floods(tmp_path):
    """The accepted I10 check, verbatim: 25 distinct-note variants (suppression-evading
    by construction) — every surface stays within its token bound, the warning and the
    commitment are retained, and the report marker is present and deterministic."""
    mem = _mem(tmp_path)
    due = (NOW + timedelta(days=3)).date().isoformat()
    mem.store.add_edge(_edge("commit", f"file the annual report by {due}",
                             rel="deadline", days=2))
    mem.store.add_edge(_edge("warn", "membership status uncertain", rel="member_of",
                             flag=True, days=400))
    for i in range(25):                                     # the flood: distinct notes
        mem.store.add_edge(_edge(f"v{i}", "senior engineer acme", rel="works_as",
                                 note=f"restated in meeting {i}", days=25 - i))
    r1 = mem.recall(U, "engineer report membership", token_budget=400)
    assert est_tokens(r1.context) <= 400                    # recall bounded
    assert "file the annual report" in r1.context           # commitment retained
    assert "possibly stale" in r1.context                   # warning retained
    assert r1.truncated and "[budget:" in r1.context        # marker present
    r2 = mem.recall(U, "engineer report membership", token_budget=400)
    assert r2.context == r1.context                         # deterministic
    ctx, *_ = assemble(mem.store, U, mem.config, now=NOW, token_budget=400)
    assert est_tokens(ctx) <= 400                           # proactive bounded
    from veracium.compile import compile_wiki
    cap = {}
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        cap["t"] = est_tokens(prompt) + est_tokens(system or "")
        return "wiki"
    compile_wiki(mem.store, llm, U, mem.config.relations,
                 wiki_input_budget=mem.config.wiki_input_budget_tokens)
    assert cap["t"] <= mem.config.wiki_input_budget_tokens  # compiler bounded (I10g)
    mem.close()


# --- I10h (the named check): the query-matched claim flag survives overflow ------------
def test_query_matched_claim_flag_survives_overflow(tmp_path):
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("claim", "the user owes $2,400 to a collector",
                             disc=Disclosure.QUARANTINED,
                             author=EvidenceAuthor.THIRD_PARTY, rel="finance_claim"))
    for i in range(30):                                     # overflow pressure
        mem.store.add_edge(_edge(f"p{i}", f"project workstream {i} " + "detail " * 20,
                                 rel=f"topic_{i}"))
    for i in range(10):
        mem.store.add_episode(__import__("veracium.schema", fromlist=["Episode"]).Episode(
            id=f"ep{i}", user_id=U, date=(NOW - timedelta(days=i)).date().isoformat(),
            summary=f"verbose episode {i} " + "history " * 20,
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=f"ep-{i}", observed_at=NOW)))
    r = mem.recall(U, "owes collector money", token_budget=400)
    assert "$2,400" in r.unverified                         # the fenced flag SURVIVES
    assert "never assert" in r.context                      # fenced, not grounded
    assert r.truncated                                      # under real overflow
    assert est_tokens(r.context) <= 400
    mem.close()


# =============================================================================
# impl round 2 — the six cells the reviewer showed the named tests missed
# =============================================================================

def test_proactive_clamp_signals_and_keeps_due_framing(tmp_path):
    """R-impl2-1: a 500K-char due item through PUBLIC proactive recall — the clamp is a
    truncation EVENT (truncated=True), and at the floor the recomposed clamp keeps the
    end-positioned (due …) framing while the content shrinks."""
    mem = _mem(tmp_path)
    due = (NOW + timedelta(days=2)).date().isoformat()
    mem.store.add_edge(_edge("huge-due", ("x" * 500_000) + f" due {due}",
                             rel="deadline", days=1))
    r = mem.recall(U)                                       # public, default budget
    assert r.truncated                                      # the clamp SIGNALS
    assert est_tokens(r.context) <= mem.config.proactive_default_budget_tokens
    tight_ctx, *_ = assemble(mem.store, U, mem.config, now=NOW,
                             token_budget=floor_for("proactive"))
    assert est_tokens(tight_ctx) <= floor_for("proactive")
    assert f"due {due}" in tight_ctx                        # framing NEVER severed (I10c)
    assert "xxxx" in tight_ctx                              # content present, clamped
    mem.close()


def test_the_frozen_recall_and_proactive_orders(tmp_path):
    """R-impl2-2: wiki (within share) outranks plain grounded facts; episodes outrank
    the remaining unverified partition and variants; proactive history admits NEWEST
    first and renders chronologically."""
    mem = _mem(tmp_path)
    mem.store.add_edge(_edge("plain", "a plain grounded fact " + "pad " * 300,
                             rel="topic_a"))
    r = mem.recall(U, "unrelated query", token_budget=floor_for("recall") + 20)
    # at just-above-floor: the wiki (small, within share) admits FIRST; the plain fact
    # follows only as the clamped best-effort remainder — order, not absence, is frozen
    assert "USER MODEL" in r.context                        # the wiki admitted
    assert r.context.find("USER MODEL") < r.context.find("a plain grounded fact") \
        or "a plain grounded fact" not in r.context         # wiki BEFORE plain (frozen)
    assert est_tokens(r.context) <= floor_for("recall") + 20
    assert r.truncated
    # proactive: OLD vs NEW oversized episodes at the floor — NEW is selected
    Episode = __import__("veracium.schema", fromlist=["Episode"]).Episode
    s2 = SqliteStore(str(tmp_path / "h.db"))
    for tag, days in (("OLD", 3), ("NEW", 0)):
        s2.add_episode(Episode(
            id=f"ep-{tag}", user_id=U, date=(NOW - timedelta(days=days)).date().isoformat(),
            summary=f"{tag} " + "verbose history " * 30,
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=tag, observed_at=NOW - timedelta(days=days))))
    ctx, *_ = assemble(s2, U, MemoryConfig(db_path=":memory:"), now=NOW,
                       token_budget=floor_for("proactive"))
    assert "NEW" in ctx and "OLD" not in ctx                # newest admits first
    mem.close()


def test_compiler_groups_by_envelope_and_orders_deterministically(tmp_path):
    """R-impl2-3: USER and SYSTEM members of the SAME value are distinct envelope
    groups (each owed a survivor even at variant_cap=1); group iteration is sorted,
    not insertion-ordered; the cap applies to variants BEYOND the survivor."""
    from veracium.compile import compile_wiki
    for order in (("a", "b"), ("b", "a")):                  # both insertion orders
        s = SqliteStore(":memory:")
        for tag in order:
            s.add_edge(_edge(f"e-{tag}", f"value {tag} " + "pad " * 150,
                             rel=f"rel_{tag}"))
        cap = {}
        def llm(prompt, *, system=None, role="compile", json_schema=None):
            cap["p"] = prompt; return "wiki"
        compile_wiki(s, llm, U, DEFAULT_RELATIONS,
                     wiki_input_budget=floor_for("wiki"))   # items budget fits ONE ~158-token line
        # BITING (R-impl3-2 fixed the -1-find hole): at this budget exactly ONE
        # ~150-token survivor fits after the scaffold; sorted group order means
        # "value a" is selected under BOTH insertion orders — "value b" never is.
        assert "value a" in cap["p"], f"order {order}: the sorted-first group missing"
        assert "value b" not in cap["p"], f"order {order}: insertion order leaked"
    # envelope split at variant_cap=1: USER + SYSTEM same value -> BOTH lines compile
    s3 = SqliteStore(":memory:")
    s3.add_edge(_edge("u-same", "SAME value", author=EvidenceAuthor.USER))
    s3.add_edge(_edge("s-same", "SAME value", author=EvidenceAuthor.SYSTEM))
    cap3 = {}
    def llm3(prompt, *, system=None, role="compile", json_schema=None):
        cap3["p"] = prompt; return "wiki"
    compile_wiki(s3, llm3, U, DEFAULT_RELATIONS, variant_cap=1)
    assert cap3["p"].count("SAME value") == 2               # one survivor per envelope


def test_surface_build_revalidates_bounds(tmp_path):
    """R-impl2-4: compile_wiki/ensure_wiki reject a below-floor bound at surface build."""
    from veracium.compile import compile_wiki, ensure_wiki
    s = SqliteStore(":memory:")
    s.add_edge(_edge("e1", "chef"))
    with pytest.raises(ValueError, match="below its floor"):
        compile_wiki(s, lambda p, **k: "w", U, DEFAULT_RELATIONS, wiki_input_budget=1)
    with pytest.raises(ValueError, match="below its floor"):
        ensure_wiki(s, lambda p, **k: "w", U, recompile_after=1, wiki_input_budget=1)


def test_report_counts_are_bounded_width(tmp_path):
    """R-impl2-5: a 1,020-edge overflow renders the frozen '999+', never a raw count."""
    mem = _mem(tmp_path, max_subgraph_edges=1100)
    for i in range(1020):
        mem.store.add_edge(_edge(f"n{i}", f"numbered fact {i} with padding text",
                                 rel=f"t{i}"))
    r = mem.recall(U, "numbered", token_budget=floor_for("recall") + 10)
    assert "999+" in r.context                              # bounded-width (R9-2)
    assert r.truncated
    mem.close()


def test_two_oversized_mandatory_members_both_emit(tmp_path):
    """R-impl2-6: a direct group whose TWO DISTINCT mandatory members are each 500K
    chars, at the floor — BOTH emit content-clamped; neither is withheld."""
    from veracium.schema import ContestedGroup
    mem = _mem(tmp_path)
    g = ContestedGroup(subject="user", relation="works_as",
                       exposed=[_edge("m-hi", "H" * 500_000,
                                      author=EvidenceAuthor.USER, days=2),
                                _edge("m-prior", "P" * 500_000,
                                      author=EvidenceAuthor.SYSTEM, days=1)],
                       linkage=[], prior_edge_ids=["m-prior"])
    block, spent, truncated = mem._render_contested([g], floor_for("recall"),
                                                    mem._est_tokens)
    assert mem._est_tokens(block) <= floor_for("recall")
    assert "HHH" in block and "PPP" in block                # BOTH mandatory members
    assert "withheld" not in block                          # neither withheld
    assert truncated                                        # the clamping SIGNALS
    mem.close()


def test_aliased_mandatory_roles_leave_challengers_optional(tmp_path):
    """R-impl3-5: in a REAL refusal group the USER prior is both highest-authority and
    the grounded prior — the mandatory roles ALIAS to one member; an oversized SYSTEM
    challenger is OPTIONAL and is withheld (with the marker) rather than promoted."""
    from veracium.schema import ContestedGroup
    mem = _mem(tmp_path)
    g = ContestedGroup(subject="user", relation="works_as",
                       exposed=[_edge("u-prior", "U" * 500_000,
                                      author=EvidenceAuthor.USER, days=2),
                                _edge("s-chal", "S" * 500_000,
                                      author=EvidenceAuthor.SYSTEM, days=1)],
                       linkage=[], prior_edge_ids=["u-prior"])   # roles ALIAS
    block, _spent, truncated = mem._render_contested([g], floor_for("recall"),
                                                     mem._est_tokens)
    assert mem._est_tokens(block) <= floor_for("recall")
    assert "UUU" in block                                    # the aliased mandatory
    assert "SSS" not in block                                # the challenger: optional,
    assert "+1 more contending values withheld" in block     # withheld WITH the marker
    assert truncated
    mem.close()


# =============================================================================
# impl round 3 — the reviewer's concrete reproductions, pinned
# =============================================================================

def test_compiler_incomparable_values_each_get_a_survivor(tmp_path):
    """R-impl3-2: cat Miso / dog Miso / bird Pico — three incomparable same-envelope
    values are three I8 groups; each compiles a survivor at variant_cap=1, +0 dropped."""
    from veracium.compile import compile_wiki
    s = SqliteStore(":memory:")
    for i, obj in enumerate(("cat Miso", "dog Miso", "bird Pico")):
        s.add_edge(_edge(f"pet{i}", obj, rel="has_pet"))
    cap = {}
    def llm(prompt, *, system=None, role="compile", json_schema=None):
        cap["p"] = prompt; return "wiki"
    body_marker = compile_wiki(s, llm, U, DEFAULT_RELATIONS, variant_cap=1)
    for obj in ("cat Miso", "dog Miso", "bird Pico"):
        assert obj in cap["p"], f"{obj} lost its survivor slot"
    assert "+0 facts" in body_marker                        # nothing dropped


def test_proactive_order_ties_and_directions(tmp_path):
    """R-impl3-1: (a) recent history admits newest under BOTH input orders; (b) a
    same-due-date tie selects the NEWER observed_at; (c) variants admit last —
    both group survivors before any variant."""
    Episode = __import__("veracium.schema", fromlist=["Episode"]).Episode
    cfg = MemoryConfig(db_path=":memory:")
    for order in (("OLD", "NEW"), ("NEW", "OLD")):          # (a) both input orders
        s = SqliteStore(":memory:")
        for tag in order:
            days = 3 if tag == "OLD" else 0
            s.add_episode(Episode(
                id=f"ep-{tag}", user_id=U,
                date=(NOW - timedelta(days=days)).date().isoformat(),
                summary=f"{tag} " + "verbose history " * 30,
                provenance=Provenance(source_type=SourceType.STATED,
                                      author_of_evidence=EvidenceAuthor.USER,
                                      evidence_ref=tag,
                                      observed_at=NOW - timedelta(days=days))))
        ctx, *_ = assemble(s, U, cfg, now=NOW, token_budget=floor_for("proactive"))
        assert "NEW" in ctx and "OLD" not in ctx, f"input order {order} leaked"
    # (b) same due date, oversized pair: the NEWER observed_at wins the tie
    due = (NOW + timedelta(days=2)).date().isoformat()
    s2 = SqliteStore(":memory:")
    for tag, days in (("OLDER", 30), ("NEWER", 1)):
        s2.add_edge(_edge(f"c-{tag}", f"{tag} commitment due {due} " + "pad " * 200,
                          rel=f"deadline_{tag}", days=days))
    ctx2, *_ = assemble(s2, U, cfg, now=NOW, token_budget=floor_for("proactive"))
    assert "NEWER" in ctx2 and "OLDER" not in ctx2          # observed_at DESC on ties
    # (c) variants last: A-survivor, A-variant, B-survivor at a two-item budget
    s3 = SqliteStore(":memory:")
    # a GENUINE variant: the same value token-dropped within _subsumes' bound (one
    # unique anchor), carrying a distinct note so the collapse surfaces it — the
    # reviewer's correction: incomparable values are independent survivors, never
    # variants (R-impl4-1).
    base = "A survivor value " + "pad " * 150
    s3.add_edge(_edge("a-surv", base, rel="topic",
                      vol=Volatility.TRANSIENT, days=2))
    s3.add_edge(_edge("a-var", base.rsplit("pad", 2)[0].strip(), rel="topic",
                      note="restated in standup", vol=Volatility.TRANSIENT, days=1))
    s3.add_edge(_edge("b-surv", "B survivor value " + "pad " * 150, rel="other_topic",
                      vol=Volatility.TRANSIENT, days=1))
    ctx3, *_ = assemble(s3, U, cfg, now=NOW, token_budget=400)
    assert "A survivor" in ctx3 and "B survivor" in ctx3    # both survivors first
    assert "restated in standup" not in ctx3                # the true variant waited


# =============================================================================
# impl round 4 — the reviewer's reproductions, pinned
# =============================================================================

def test_variancy_never_demotes_a_flagged_member(tmp_path):
    """R-impl4-1: a flagged same-group member is a WARNING, never a final-tier
    variant — it survives the floor while the ordinary survivor competes normally.
    And incomparable same-envelope values are independent proactive survivors."""
    cfg = MemoryConfig(db_path=":memory:")
    s = SqliteStore(":memory:")
    base = "current project state " + "pad " * 150
    s.add_edge(_edge("base", base, rel="works_on", vol=Volatility.TRANSIENT, days=1))
    s.add_edge(_edge("flagged", base.rsplit("pad", 2)[0].strip(), rel="works_on",
                     note="needs another look", vol=Volatility.TRANSIENT,
                     flag=True, days=300))                  # same group, FLAGGED
    ctx, edges, _eps, _tr = assemble(s, U, cfg, now=NOW,
                                     token_budget=floor_for("proactive"))
    assert "confirm when natural" in ctx                    # the warning SURVIVES
    assert any(e.id == "flagged" for e in edges)
    # incomparable values: three independent survivors, no RESTATED VARIANTS section
    s2 = SqliteStore(":memory:")
    for i, obj in enumerate(("cat Miso", "dog Miso", "bird Pico")):
        s2.add_edge(_edge(f"pet{i}", obj, rel="has_pet", vol=Volatility.TRANSIENT))
    ctx2, *_ = assemble(s2, U, cfg, now=NOW, token_budget=1200)
    assert "RESTATED VARIANTS" not in ctx2
    for obj in ("cat Miso", "dog Miso", "bird Pico"):
        assert obj in ctx2


def test_episode_id_tie_is_lexicographic_ascending(tmp_path):
    """R-impl4-1: with otherwise-identical episodes a and z, the final id tie is
    ASCENDING — a is selected."""
    Episode = __import__("veracium.schema", fromlist=["Episode"]).Episode
    s = SqliteStore(":memory:")
    for eid in ("z-ep", "a-ep"):
        s.add_episode(Episode(
            id=eid, user_id=U, date=NOW.date().isoformat(),
            summary=f"[{eid}] " + "identical verbose history " * 30,
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=eid, observed_at=NOW)))
    ctx, *_ = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW,
                       token_budget=floor_for("proactive"))
    assert "[a-ep]" in ctx and "[z-ep]" not in ctx


def test_compiler_survivor_is_order_invariant(tmp_path):
    """R-impl4-2: same-value same-envelope members with distinct notes — the I8j
    survivor (note-bearing → specificity → freshest → id) compiles under BOTH
    insertion orders; input permutation never changes the selection."""
    from veracium.compile import compile_wiki
    expected = None
    for order in (("older", "newer"), ("newer", "older")):
        s = SqliteStore(":memory:")
        for tag in order:
            days = 30 if tag == "older" else 1
            s.add_edge(_edge(f"e-{tag}", "the project codename " + "pad " * 100,
                             rel="works_on", note=f"{tag.upper()}-NOTE", days=days))
        cap = {}
        def llm(prompt, *, system=None, role="compile", json_schema=None):
            cap["p"] = prompt; return "wiki"
        compile_wiki(s, llm, U, DEFAULT_RELATIONS,
                     wiki_input_budget=floor_for("wiki"))   # one line fits
        got = "NEWER-NOTE" if "NEWER-NOTE" in cap["p"] else "OLDER-NOTE"
        expected = expected or got
        assert got == expected, f"insertion order {order} changed the survivor"
    assert expected == "NEWER-NOTE"                         # freshest among note-bearers


def test_public_recall_rejects_a_mutated_sub_floor_cap(tmp_path):
    """R-impl4-3: mutating the dataclass AFTER construction cannot smuggle a
    sub-floor item cap past validation — the public recall path revalidates at
    surface build, wiki layer enabled or not."""
    mem = _mem(tmp_path, wiki_recompile_after_writes=0)     # wiki layer DISABLED
    mem.store.add_edge(_edge("e1", "chef"))
    mem.config.item_cap_tokens = 1                          # post-construction mutation
    with pytest.raises(ValueError, match="minimum"):
        mem.recall(U, "chef")
    mem.close()


def test_proactive_clamp_count_is_per_item(tmp_path):
    """R-impl4-4: one oversized due item clamped at composition AND recomposed at
    admission reports EXACTLY '1 clamped' — stages are not items."""
    s = SqliteStore(":memory:")
    due = (NOW + timedelta(days=2)).date().isoformat()
    s.add_edge(_edge("huge", ("x" * 500_000) + f" due {due}", rel="deadline", days=1))
    ctx, *_ = assemble(s, U, MemoryConfig(db_path=":memory:"), now=NOW,
                       token_budget=floor_for("proactive"))
    assert "1 clamped]" in ctx                              # exactly one ITEM
