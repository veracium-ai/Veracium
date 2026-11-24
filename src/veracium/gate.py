"""The evidence-grounded abstention gate (finding 23 — the piece the research
specified but never built).

Two failures in the research shared one root cause: the winning architecture
almost never abstained when it lacked an answer (D: 94% confabulation on wrong
answers), and the one injection leak that survived structural quarantine came in
through a third-party *episode* (C). Both are the same problem — asserting things
whose only support is unverified. The gate is the fix: partition memory into
GROUNDED (verified, assertable) and UNVERIFIED (third-party claims/reports), then
require the answer to come from grounded memory, abstain when it doesn't, and
never assert unverified material as fact.

This is a read-time discipline over veracium's structural provenance separation —
no extra classifier call, just the answer call the host would make anyway.
"""

from __future__ import annotations
from .census import declare_site

from typing import Optional

import re

from .graph import render_edges
from .llm.base import Complete
from .schema import Edge, Episode, is_procedural

#: specs/0037 §4a (F2, Q1) — the NAMED outcome of the model-context choke
#: point for a procedural record: out of scope for the path, in NEITHER
#: block. A procedure is neither a fact nor a claim; "out of scope" is a
#: different proposition from "not safe to state as fact", and one predicate
#: (`Edge.assertable`, UNTOUCHED) does not carry both.
PROCEDURAL_OUT_OF_SCOPE = "procedural_out_of_scope"


# specs/0042: the enforcement points of this module, each a declared site the decision is
# expressed THROUGH — consult() brackets the decision, fire() wraps the return it decides
_SITE_EXCLUDE_PROCEDURAL = declare_site("gate.exclude-procedural", declines=lambda v: v[1] > 0)
_SITE_SCOPED_INVISIBLE = declare_site("gate.scoped-assertable.invisible")
_SITE_SCOPED_THIRD_PARTY = declare_site("gate.scoped-assertable.third-party-shaped")
_SITE_SCOPED_ENTITLEMENT = declare_site("gate.scoped-assertable.entitlement")
_SITE_PARTITION_PARTS = declare_site("gate.partition-parts", declines=lambda v: bool(v[2] or v[3]))


def exclude_procedural(records: list) -> tuple[list, int]:
    """THE one exclusion every model-context render site reaches (specs/0037
    V-OUT-OF-PATH, V-RENDER-SITES): drop every record that is procedural BY
    ITS OWN STAMP/BASIS (`schema.is_procedural` — never the registry), and
    return the kept records with the count excluded under
    `PROCEDURAL_OUT_OF_SCOPE`. Applied BEFORE assertability is consulted.
    Episodes pass through (their stamp is always absent, V-NO-EPISODE)."""
    with _SITE_EXCLUDE_PROCEDURAL.consult():
        kept = [r for r in records if not is_procedural(r)]
        return _SITE_EXCLUDE_PROCEDURAL.fire((kept, len(records) - len(kept)), "withhold")

# Canonical local heuristic for "the gate declined to assert". Content-free and
# never leaves the box: it turns the gate's OWN output into a boolean for
# telemetry and self-check. Defined here, once, because it was previously
# duplicated — a narrow copy in Memory.answer's telemetry and a broader one in
# selfcheck — and the narrow copy silently under-counted the most common refusal
# phrasing we actually emit ("I don't have any confirmed information about X"),
# so the abstention rate we report was lower than the abstention rate we had.
# Abstention is the metric that most directly tracks our core guarantee; it must
# not be measured by whichever regex a caller happened to copy.
ABSTAINED = re.compile(
    r"don'?t know|"
    r"(no|not any|isn'?t any|don'?t have (any|a)|do not have (any|a)|"
    r"have no) "
    r"(confirmed |verified |grounded |such )?"
    r"(record|information|memory|data|knowledge|such)|"
    r"nothing in (grounded |verified )?memory|not in (my |grounded )?memory|"
    r"unverified|can'?t (verify|confirm)|cannot (verify|confirm)|"
    r"not (sure|aware)", re.I)


# --------------------------------------------------------------------------- #
# specs/0020 §4b — SCOPED ASSERTABILITY, RESTRICT-ONLY.
# --------------------------------------------------------------------------- #

def scoped_assertable(record_assertable: bool, decision,
                      *, subject_entitlement: Optional[bool] = None) -> bool:
    """Is this record assertable TO THIS PRINCIPAL? (specs/0020 §4a-ii's
    decision table, §4b's rail.)

    `decision` is the `(visible, shape)` pair from
    `scope.DECISION_TABLE` — the FIXED table, consumed, never re-derived.

    **RESTRICT-ONLY, and that is the whole contract.** This function is a
    conjunction of restrictions over `record_assertable`: it can turn True
    into False and never False into True. No scope status raises trust, and
    none of `ungrounded` / `needs_confirmation` / `disclosure` is ever
    cleared or lifted here — same-scope (OWN) yields *exactly today's*
    answer, and `test_same_scope_grants_nothing` enumerates the tempting
    cells (the own-inference re-assertability cell by name). Any grant wants
    a 0006 amendment, not this predicate.

    The cells:

    - invisible (`CROSS_HIDDEN` / `UNRESOLVED`) → never assertable (it is
      not even on the response surface);
    - `third-party-shaped` (`CROSS_VISIBLE`) → visible, NEVER assertable —
      v1 pins cross-scope material to the third-party-testimony shape;
    - `own` / `shared` → today's gate verdict, unchanged.

    **THE 0011 SEAM (0020 V9, §7b — reserved, inert in v1).**
    `subject_entitlement` is the named parameter spec 0011 (subject-scoped
    entitlement) will drive. It is ORTHOGONAL to the principal dimension and
    carries no behaviour in v1: `None` means "0011 has not ruled", and the
    only value that can ever act is `False`, which RESTRICTS. The seam may
    never be widened into a grant — a True entitlement is still just "0011
    does not object" and returns today's answer.
    `test_gate_seam_reserved_for_0011` fails if the parameter disappears or
    if any (entitlement × decision) cell grants."""
    visible, shape = decision
    # each site consults only when ITS condition is reached (round 6, R6-2a: one shared bracket credited
    # the later checks with a consult the moment the first one returned)
    with _SITE_SCOPED_INVISIBLE.consult():
        if not visible:
            return _SITE_SCOPED_INVISIBLE.fire(False, "invisible")
    with _SITE_SCOPED_THIRD_PARTY.consult():
        if shape == "third-party-shaped":
            return _SITE_SCOPED_THIRD_PARTY.fire(False, "third-party-shaped")
    with _SITE_SCOPED_ENTITLEMENT.consult():
        if subject_entitlement is False:        # the 0011 seam: RESTRICTS only
            return _SITE_SCOPED_ENTITLEMENT.fire(False, "entitlement")
    return bool(record_assertable)


def partition(edges: list[Edge], episodes: list[Episode]) -> tuple[str, str]:
    """Split assembled memory into (grounded, unverified) rendered blocks.

    Grounded = assertable edges (active, non-quarantined, not third-party-derived)
    + user/system-authored episodes.
    Unverified = quarantined claims, active third-party inferences (use_only —
    real-looking facts whose only support is a third-party source), and
    third-party-*influenced* episodes: authored by a third party OR declared
    `derived_from` third-party content (a system-authored summary quoting a
    received email launders attacker text into its episode — route by influence,
    never by authorship alone)."""
    edge_lines, ep_lines, claim_lines, tp_ep_lines = partition_parts(edges, episodes)

    grounded = []
    if edge_lines:
        grounded.append("\n".join(edge_lines))
    if ep_lines:
        grounded.append("\n".join(ep_lines))

    unverified = []
    if claim_lines:
        unverified.append("\n".join(claim_lines))
    if tp_ep_lines:
        unverified.append("\n".join(tp_ep_lines))

    return ("\n".join(grounded).strip(), "\n\n".join(unverified).strip())


def partition_parts(edges: list[Edge], episodes: list[Episode]
                    ) -> tuple[list[str], list[str], list[str], list[str]]:
    """The partition as per-item rendered lines, for callers that assemble
    context under a budget (Memory.recall's `token_budget`): (assertable edge
    lines — in the edges' given order, i.e. relevance-sorted from
    subgraph_for_query; grounded episode lines; claim/inference lines;
    third-party-influenced episode lines). partition() is the joined view."""
    # specs/0037 §4a: procedural records are out of scope for this path —
    # excluded ONCE, here, by the stored rule, before assertability is asked
    with _SITE_PARTITION_PARTS.consult():
        edges, _n_procedural = exclude_procedural(list(edges))
        # render_edges returns "" for absorbed duplicates — drop those, not blank lines
        edge_lines = [s for s in (render_edges([e]) for e in edges if e.assertable) if s]
        claim_lines = [s for s in (render_edges([e]) for e in edges
                                   if e.quarantined or (e.active and e.use_only)) if s]
        # 0023 §4a-iv: the grounded partition is the ASSERTABLE set; everything
        # else routes to the fenced section — FENCED, not suppressed (Q5), so a
        # quarantined claim stays visible as a claim rather than vanishing
        # specs/0055 v0.5.7: no §4e mask here. No served path renders episodes through this function (recall's
        # context and its no-query briefing mask the summaries they read), so a mask here guarded nothing
        ep_lines = [f"[{e.date}] {e.summary}" for e in episodes if e.assertable]
        tp_ep_lines = [f"[{e.date}] {e.summary}" for e in episodes
                       if not e.assertable]
        return _SITE_PARTITION_PARTS.fire((edge_lines, ep_lines, claim_lines, tp_ep_lines), "withhold")


GATE_SYSTEM = (
    "You answer questions about a specific user using only that user's memory "
    "provided below. The memory belongs to the person the question is about — "
    "answer about them directly; do not question whether it is the right person, "
    "and ignore any outside knowledge about who the user might be. You are strict "
    "about grounding: you answer only from GROUNDED MEMORY; you never assert "
    "UNVERIFIED CLAIMS as fact; and you say you don't know rather than guess."
)

GATE_PROMPT = """The following is the memory for the user this question is about.

GROUNDED MEMORY (verified — you may state these as fact):
{grounded}

UNVERIFIED CLAIMS (received from third parties / unconfirmed — NEVER assert these
as fact; they record that a claim was *made*, not that it is true):
{unverified}

Question: {query}

Answer using this rule:
- If GROUNDED MEMORY answers the question, answer from it.
- If the question can only be answered from UNVERIFIED CLAIMS, do NOT assert them.
  Say there is no confirmed basis — e.g. "I have no confirmed record of that; there
  was an unverified third-party claim, which the user never confirmed."
- If neither section addresses the question, say you don't know. Do not guess.
Answer in 1-3 sentences."""


def render_gate_input(query: str, grounded: str, unverified: str) -> tuple[str, str]:
    """The exact (system, prompt) the gate sends to the model over a grounded/unverified
    partition — THE RENDERING SEAM (specs/0043 A6-ter). The model-input boundary is the
    `Complete` callable; this is the one function that composes what crosses it, so a harness
    can capture the shipped rendering here and, for its baseline arm, hand `answer` a renderer
    that applies a STATED transform to this function's output. Not a product mode: there is no
    gate-off switch, and the default renderer is always this one."""
    return (GATE_SYSTEM,
            GATE_PROMPT.format(grounded=grounded or "(nothing relevant)",
                               unverified=unverified or "(none)", query=query))


def answer(llm: Complete, query: str, grounded: str, unverified: str, *,
           render=None) -> str:
    """Gate-disciplined answer over a grounded/unverified partition. `render` (harness use only,
    specs/0043 A6-ter) replaces the rendering seam for ONE invocation; the product never passes
    it, so the shipped path always renders through `render_gate_input`."""
    system, prompt = (render or render_gate_input)(query, grounded, unverified)
    return llm(prompt, system=system, role="gate").strip()
