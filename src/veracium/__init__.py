"""veracium — a provenance-aware memory plug-in for agentic systems.

    from veracium import Memory
    from veracium.llm.anthropic import AnthropicComplete

    mem = Memory(llm=AnthropicComplete())          # or any Complete callable
    mem.remember("alice", "USER: I'm vegetarian and have a dog named Ollie.")
    ctx = mem.recall("alice", "what should I keep in mind for lunch?")
    print(ctx.context)   # grounded, provenance-flagged memory for your prompt

Design (validated in the `agent-memory` research repo): a typed graph + dated
episodes are the store of record; recall assembles an entity-matched subgraph
(and, when enabled, an LLM-curated wiki) with third-party claims structurally
quarantined. Memory is per-user; one user's memory never reaches another's.
"""

from __future__ import annotations

import hashlib
import re
import time
from uuid import uuid4
from dataclasses import dataclass, field
from typing import Optional

from . import compile as _compile
from . import gate as _gate
from . import lifecycle as _lifecycle
from .config import MemoryConfig

# Local-only abstention heuristic: computed on the answer text to emit a
# content-free boolean for telemetry. The text itself never leaves. Imported
# from gate rather than restated — the previous local copy was narrower than
# selfcheck's and under-counted abstentions.
from .gate import ABSTAINED as _ABSTAINED  # noqa: E402
from .graph import subgraph_for_query, render_edges
from .ingest import _event_dt, ingest_event
from .llm.base import Complete, Embed
from .authority import edge_effective as _edge_effective
from .graph import _value_key as _value_key
from .schema import (CONFIRMATION_RULE_VERSION, ConfirmationActor,
                     ConfirmationCallPath, ContestedGroup, ContestedLinkage, Edge,
                     Episode, EvidenceAuthor, OutcomeJudgmentDraft, Provenance,
                     SourceType, utcnow, validate_correlation_id)
from .store.base import HEAD_MOVED, Store
from .store.sqlite import SqliteStore

__all__ = ["Memory", "MemoryConfig", "Recall", "Store", "SqliteStore",
           "Complete", "Embed", "EvidenceAuthor"]


@dataclass
class Recall:
    """The result of a recall.

    `context` is a ready-to-inject block (grounded memory + a fenced never-assert
    section). For hosts that want the abstention gate, `grounded` and `unverified`
    are the two partitions the gate operates on (see `Memory.answer`).

    When recall ran with a `token_budget`, `tokens_estimated` is the heuristic
    size of `context` (chars/4 — veracium is tokenizer-agnostic by design) and
    `truncated` says whether anything was left out to fit. `edges`/`episodes`
    always carry the full retrieved units regardless of budget — the budget
    shapes the rendered context, not the raw material."""
    context: str
    grounded: str
    unverified: str
    edges: list[Edge]
    episodes: list[Episode]
    tokens_estimated: int = 0
    truncated: bool = False
    # specs/0003 §4c-ii: the structured contested-facts surface. One entry per LIVE refusal
    # contention, carrying full Edges for exposed members and content-free linkage for the
    # unseen fenced cross-partition challenger. Appended, defaulted — no existing constructor
    # call breaks. `edges` becomes the de-duplicated union of query-selected edges and the
    # exposed preservation members.
    contested: list["ContestedGroup"] = field(default_factory=list)


class Memory:
    def __init__(self, *, llm: Complete, store: Optional[Store] = None,
                 embed: Optional[Embed] = None, config: Optional[MemoryConfig] = None,
                 telemetry=None, diagnostics=None, audit=None):
        self.config = config or MemoryConfig()
        self.store = store or SqliteStore(self.config.db_path)
        self.llm = llm
        self.embed = embed
        # Optional content-free telemetry sink (a telemetry.Collector). None = off.
        # The library never creates one implicitly; entry points wire a consented
        # collector. See veracium.telemetry.
        self.telemetry = telemetry
        # Optional error-reporting sink (a diagnostics.Reporter). None = off. Logs
        # genuine errors locally and, only with consent, offers to send that log.
        # See veracium.diagnostics; sending is a separate, more careful channel than
        # telemetry because a log can contain memory content.
        self.diagnostics = diagnostics
        # Optional operation audit sink (an audit.AuditLog). None = off. One
        # content-free line per operation: who called what, when, which user.
        # See veracium.audit.
        self.audit = audit

    def _record(self, event: str, fields: dict,
                user_id: Optional[str] = None) -> None:
        if self.telemetry is not None:
            try:
                self.telemetry.record(event, fields)
            except Exception:
                pass  # telemetry must never break memory
        if self.audit is not None and user_id is not None:
            try:
                self.audit.record(event, user_id, fields)
            except Exception:
                pass  # auditing must never break memory, even a broken sink

    def _on_error(self, where: str, exc: BaseException, user_id: Optional[str] = None) -> None:
        """Hand a genuine error to the diagnostics reporter (log locally; send only
        with consent). Best-effort — never masks or delays the real exception, which
        the caller re-raises."""
        if self.diagnostics is None:
            return
        try:
            uh = hashlib.sha256(user_id.encode()).hexdigest()[:12] if user_id else None
            self.diagnostics.record_error(where, exc, {"user_hash": uh})
        except Exception:
            pass

    # -- write -------------------------------------------------------------
    def remember(self, user_id: str, event_text: str, *,
                 author: EvidenceAuthor = EvidenceAuthor.USER,
                 date: Optional[str] = None, event_type: str = "chat",
                 evidence_ref: Optional[str] = None,
                 derived_from: Optional[EvidenceAuthor] = None,
                 source_id: Optional[str] = None) -> dict:
        """Ingest one interaction event into `user_id`'s memory.

        `author` is the trust-critical input: use EvidenceAuthor.THIRD_PARTY for
        received email / external documents so their claims are quarantined.

        Authorship is per-event; if the event's *content* embeds material a
        lower-trust party influenced — a system-authored summary quoting a
        received email's subject or body — declare it with `derived_from`
        (e.g. `author=SYSTEM, derived_from=THIRD_PARTY`). Trust is capped at
        the minimum of the two: nothing extracted from such an event is ever
        assertable, closing the system-event laundering bypass.

        `source_id` (specs/0006) optionally records WHICH source produced this
        event — an opaque, host-chosen id (a mailbox, a connector instance). It
        is DIAGNOSTIC: it groups records for inspection/dedup/attribution but
        grants no trust and changes no answer (I5). It is host-supplied only,
        never model-derived (I1)."""
        from datetime import date as _date
        date = date or _date.today().isoformat()
        t0 = time.perf_counter()
        try:
            r = ingest_event(self.store, self.llm, user_id, event_text=event_text,
                             author=author, date=date, event_type=event_type,
                             evidence_ref=evidence_ref, derived_from=derived_from,
                             source_id=source_id, relations=self.config.relations)
        except Exception as e:
            self._on_error("remember", e, user_id)
            raise
        self._record("ingest", {"facts": r["facts"], "quarantined": r["quarantined"],
                                "episodes": 1 if r["episode"] else 0,
                                "unparseable": 1 if r.get("unparseable") else 0,
                                "supersessions": r["supersessions"],
                                "reinforcements": r["reinforcements"],
                                "ms": int((time.perf_counter() - t0) * 1000)}, user_id)
        return r

    # -- read --------------------------------------------------------------
    def recall(self, user_id: str, query: Optional[str] = None, *,
               token_budget: Optional[int] = None) -> Recall:
        """Assemble grounded memory context for answering `query`.

        Combines the LLM-curated wiki (the grounded, verified working view,
        recompiled after N writes) with a per-query entity-matched subgraph for
        detail — the layered design that won both horizons. Memory is partitioned
        into grounded (assertable) and unverified (third-party claims/reports),
        so the host can apply the abstention gate via `answer()` or its own prompt.

        `token_budget` caps the rendered context in ESTIMATED tokens (chars/4 —
        veracium is tokenizer-agnostic; approximate, not exact). Omitted, the
        validated config default applies (`query_context_budget_tokens`, 4,000)
        — recall is never unbounded; a budget below the envelope-derived floor
        raises `ValueError` (specs/0012 I10e — the old sub-floor best-effort
        rendering is withdrawn). Selection under pressure follows the FROZEN
        0012 §4c(iv) order: contested first, then query-relevant flagged
        warnings, query-matched claim flags, other flagged warnings
        (most-overdue first), dated commitments (nearest first), the wiki
        within its render share, relevance-ranked grounded edges, episodes
        (newest first), the remaining unverified partition, and variants last.
        Truncation is reported in-context (bounded-width counts) and via
        `Recall.truncated`.

        **No query → proactive mode**: a session-start briefing ("what should
        I know before starting?") — dated commitments coming due or overdue,
        possibly-stale facts to confirm when natural, current transient state
        worth a follow-up, recent history. Proactive surfacing is
        *volunteering*, so disclosure gates it: only MENTIONABLE facts appear;
        `use_only` material and quarantined claims never surface unprompted
        (`Recall.unverified` is always empty in this mode). LLM-free and
        deterministic; see `veracium.proactive`.
        """
        if token_budget is not None and token_budget <= 0:
            raise ValueError("token_budget must be a positive number of tokens")
        try:
            if query is None:
                return self._proactive(user_id, token_budget)
            return self._recall(user_id, query, token_budget)
        except Exception as e:
            self._on_error("recall", e, user_id)
            raise

    def _proactive(self, user_id: str, token_budget: Optional[int]) -> Recall:
        from . import proactive
        # specs/0012 I10: proactive is ALWAYS budgeted — the config default (1,200)
        # applies when the caller omits token_budget.
        if token_budget is None:
            token_budget = self.config.proactive_default_budget_tokens
        context, edges, episodes, truncated = proactive.assemble(
            self.store, user_id, self.config,
            token_budget=token_budget, est=self._est_tokens)
        self._record("recall", {"wiki_used": False, "subgraph_edges": len(edges),
                                "grounded_items": len(edges), "unverified_items": 0,
                                "proactive": 1, "trimmed": 1 if truncated else 0},
                     user_id)
        return Recall(context=context, grounded=context, unverified="",
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated)

    @staticmethod
    def _est_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def _recall(self, user_id: str, query: str,
                token_budget: Optional[int] = None) -> Recall:
        # specs/0003 §4c-ii/§4e: the host relation registry flows to BOTH the compiler
        # (so a contested functional group is excluded from the one-value wiki, and the
        # cache binds the registry/policy digest) AND subgraph_for_query (so a functional
        # contention is authority-ordered). A custom registry must reach both, not one.
        # specs/0012 I10: query recall is ALWAYS budgeted — a caller that omits
        # token_budget gets the validated config default (4,000), never unbounded.
        if token_budget is None:
            token_budget = self.config.query_context_budget_tokens
        # I10e at SURFACE BUILD (R-impl4-3): a config mutated after construction
        # cannot smuggle a sub-floor bound past __post_init__ — every mutable
        # recall bound revalidates here, the wiki layer enabled or not.
        from .budgets import MIN_ITEM_ALLOWANCE, validate_budget
        validate_budget("recall", token_budget,
                        self.config.group_heading_allowance_tokens)
        if self.config.item_cap_tokens < MIN_ITEM_ALLOWANCE:
            raise ValueError(
                f"item_cap_tokens {self.config.item_cap_tokens} is below the minimum "
                f"item allowance {MIN_ITEM_ALLOWANCE} (I10e, recall surface build)")
        if not (0 < self.config.wiki_render_share <= 1):
            raise ValueError("wiki_render_share must be in (0, 1]")
        from .budgets import MARKER_RESERVE
        if int(token_budget * self.config.wiki_render_share) < \
                MIN_ITEM_ALLOWANCE + MARKER_RESERVE:
            raise ValueError(
                f"wiki_render_share {self.config.wiki_render_share} of token budget "
                f"{token_budget} leaves "
                f"{int(token_budget * self.config.wiki_render_share)} tokens for the "
                f"wiki slot — below one clamped item + the marker reserve "
                f"({MIN_ITEM_ALLOWANCE + MARKER_RESERVE}) (I10e, recall surface build)")
        if self.config.contested_members_per_line < 2:
            raise ValueError("contested_members_per_line < 2 (I10e, surface build)")
        if self.config.group_heading_allowance_tokens < 16:
            raise ValueError("group_heading_allowance_tokens < 16 (I10e, surface build)")
        wiki = _compile.ensure_wiki(self.store, self.llm, user_id,
                                    self.config.wiki_recompile_after_writes,
                                    self.config.relations,
                                    wiki_input_budget=self.config.wiki_input_budget_tokens,
                                    variant_cap=self.config.wiki_variant_cap,
                                    item_cap=self.config.item_cap_tokens)
        edges = subgraph_for_query(self.store, user_id, query,
                                   max_edges=self.config.max_subgraph_edges,
                                   coverage_share=self.config.subgraph_coverage_share,
                                   relations=self.config.relations)
        # outcome events are structured records, not narrative — they'd crowd
        # out interaction history for high-volume consumers; their signal
        # reaches recall as counters rendered on the edges themselves
        episodes = [e for e in self.store.episodes(user_id)
                    if e.kind != "outcome"][-self.config.max_recent_episodes:]

        # specs/0003 §4c-ii: the structured contested surface + the de-duplicated
        # Recall.edges union, computed BEFORE rendering so the exposed members render in a
        # deterministic HIGH-priority CONTESTED block rather than the ordinary detail. The
        # exposed higher-authority grounded prior is present even if the query did not
        # select it (the I6a guarantee).
        contested, exposed_extra = self._build_contested(user_id, edges)
        seen = {e.id for e in edges}
        for e in exposed_extra:
            if e.id not in seen:
                edges.append(e)
                seen.add(e.id)
        # Only the GROUNDED (assertable) exposed members move into the grounded CONTESTED
        # block. A fenced exposed member (e.g. a query-selected quarantined challenger — a
        # full member in the STRUCTURED carrier) must stay on the unverified side of the
        # gate, so it is left in detail_edges to route through the unverified channel
        # (partition-preserving, §4c-ii).
        contested_ids = {e.id for g in contested for e in g.exposed if e.assertable}
        detail_edges = [e for e in edges if e.id not in contested_ids]

        # the contested surface gets FIRST claim on the budget — HIGH priority, ahead
        # of ordinary query detail — so a refusal never demotes the prior below where it
        # stood before it (the finite-budget form of I6a). It IS budget-gated, not an
        # unbounded surface (round-8 blocker 2); truncation is deterministic and flagged.
        # specs/0012 I10: recall is ALWAYS budgeted (the config default applies when the
        # caller omits token_budget) — the old unbudgeted branch is gone.
        contested_block, spent, c_trunc = self._render_contested(
            contested, token_budget, self._est_tokens)
        wiki, detail_grounded, unverified, d_trunc = self._fit_to_budget(
            wiki, detail_edges, episodes, max(0, token_budget - spent), query)
        truncated = c_trunc or d_trunc

        grounded_parts = []
        if wiki:
            grounded_parts.append(wiki)
        if contested_block:
            grounded_parts.append(contested_block)
        if detail_grounded:
            grounded_parts.append("## RELEVANT DETAIL\n" + detail_grounded)
        grounded = "\n\n".join(grounded_parts).strip() or "(no memory yet for this user)"

        context = grounded
        if unverified:
            context += ("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n"
                        + unverified)
        self._record("recall", {"wiki_used": bool(wiki), "subgraph_edges": len(edges),
                                "grounded_items": sum(1 for e in edges if not e.quarantined),
                                "unverified_items": sum(1 for e in edges if e.quarantined),
                                "trimmed": 1 if truncated else 0}, user_id)
        return Recall(context=context, grounded=grounded, unverified=unverified,
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated,
                      contested=contested)

    def _contested_line(self, g: "ContestedGroup",
                        line_budget: Optional[int] = None):
        """One deterministic line for a contested group, budget-aware PACKED per
        specs/0012 §4c (I10i): the heading's subject/relation render CONTENT-CLAMPED
        under the group-heading allowance; the withheld marker is reserved FIRST; the
        MANDATORY member — the highest-effective-authority grounded member, which IS the
        preserved grounded prior here (the roles may alias; `0003` orders exposed higher
        authority first) — is emitted with content clamped to the remaining budget;
        further members are admitted only while they fit WHOLE, the emitted count
        reducing dynamically below `contested_members_per_line`; the withheld count
        reflects everything not emitted. A fenced member is NOT shown here — it stays in
        the unverified channel (partition-preserving, §4c-ii). Returns None if the group
        has no assertable member."""
        from .budgets import (MEMBER_FRAMING_COST, MIN_MEMBER_CONTENT,
                              WITHHELD_MARKER_RESERVE, clamp_item, est_tokens)
        grounded = [e for e in g.exposed if e.assertable]
        if not grounded:
            return None, False
        k_cap = self.config.contested_members_per_line
        head = clamp_item(f"{g.subject} {g.relation}",
                          self.config.group_heading_allowance_tokens)
        tail = " — CONTESTED (no single current value)"

        def _member(e, content_cap):
            return (f"{clamp_item(e.object, content_cap)} "
                    f"[{e.provenance.author_of_evidence.value}]")

        squeezed = False
        if line_budget is None:
            members = [_member(e, self.config.item_cap_tokens) for e in grounded[:k_cap]]
            withheld = len(grounded) - len(members)
        else:
            remaining = (line_budget - est_tokens(f"- {head}: {tail}")
                         - WITHHELD_MARKER_RESERVE)
            # the mandatory member, content-clamped to what remains (never dropped)
            # the mandatory ROLES (R-impl3-5): the highest-effective-authority member
            # (grounded[0], authority-sorted) AND the preserved grounded PRIOR —
            # resolved via the group's prior_edge_ids carrier. The roles MAY ALIAS
            # (a USER prior against SYSTEM challengers): then the mandatory set is
            # ONE member and every challenger is optional (fit-whole or withheld).
            prior_ids = set(g.prior_edge_ids or ())
            mandatory = [grounded[0]]
            if prior_ids and grounded[0].id not in prior_ids:
                prior_member = next((m for m in grounded[1:] if m.id in prior_ids), None)
                if prior_member is not None:
                    mandatory.append(prior_member)
            members = []
            for i, m in enumerate(mandatory):
                share = max(1, len(mandatory) - i)
                m_cap = max(MIN_MEMBER_CONTENT,
                            min(self.config.item_cap_tokens,
                                (remaining // share) - MEMBER_FRAMING_COST))
                rendered = _member(m, m_cap)
                squeezed = squeezed or est_tokens(m.object) > m_cap
                members.append(rendered)
                remaining -= est_tokens(rendered)
            for e in grounded[len(mandatory):]:
                if len(members) >= k_cap:
                    break
                cand = _member(e, self.config.item_cap_tokens)
                if est_tokens(cand) > remaining:           # admit only while it fits WHOLE
                    continue
                members.append(cand)
                remaining -= est_tokens(cand)
            withheld = len(grounded) - len(members)
        squeezed = squeezed or withheld > 0                # I10i: EVERY cause signals
        vals = " / ".join(members)
        wh = f" (+{withheld} more contending values withheld)" if withheld > 0 else ""
        return f"- {head}: {vals}{wh}{tail}", squeezed

    def _render_contested(self, contested, budget=None, est=None):
        """Render the deterministic CONTESTED FUNCTIONAL FACTS block from the grounded
        exposed members (specs/0003 §4c-ii). Returns (block, tokens_spent, truncated). With
        a budget, group lines are admitted highest-priority-first with a best-effort minimum
        (the first line is unconditional — the higher-authority prior is never dropped),
        and the rest are budget-gated so the surface is bounded, not unbounded."""
        if not contested:
            return "", 0, False
        heading = "## CONTESTED FUNCTIONAL FACTS (no single current value; do not assert one)"
        if budget is None or est is None:
            results = [self._contested_line(g) for g in contested]
            lines = [ln for ln, _sq in results if ln]
            if not lines:
                return "", 0, False
            # I10i: within-group withholding signals truncation even unbudgeted
            any_sq = any(sq for ln, sq in results if ln)
            return heading + "\n" + "\n".join(lines), 0, any_sq
        remaining = budget - est(heading + "\n")
        sel, truncated = [], False
        for g in contested:
            # I10i: each group line is PACKED within what remains — one group can
            # never break the budget (the first line is best-effort unconditional)
            line, squeezed = self._contested_line(
                g, line_budget=remaining if sel else max(remaining, 1))
            if line is None:
                continue
            truncated = truncated or squeezed             # EVERY cause signals (I10i)
            cost = est(line)
            if cost > remaining and sel:
                truncated = True
                break
            sel.append(line)
            remaining -= cost
        if not sel:
            return "", 0, False
        block = heading + "\n" + "\n".join(sel)
        return block, est(block), truncated

    def _build_contested(self, user_id: str, query_edges: list):
        """Build the structured contested surface for the LIVE refusal contentions of a
        user (specs/0003 §4c-ii). Returns (contested_groups, exposed_edges). A member is
        EXPOSED (full Edge) iff it is grounded/assertable — the preserved higher-authority
        prior AND every same-partition grounded member I6 deterministically renders, even
        one the query did not select (round-11) — OR the query already selected it. The
        unseen fenced CROSS-partition challenger (use_only/quarantined, not selected) is
        content-free linkage only: no query-independent reach on any surface (round-10 A)."""
        try:
            refusals = self.store.refusals(user_id)
        except NotImplementedError:
            return [], []
        if not refusals:
            return [], []
        relations = self.config.relations
        active = {e.id: e for e in self.store.edges(user_id, active_only=True,
                                                    include_quarantined=True)}
        selected = {e.id for e in query_edges}
        groups: dict = {}
        group_priors: dict = {}
        for r in refusals:
            prior, inc = active.get(r.prior_edge_id), active.get(r.incoming_edge_id)
            rel = relations.get(r.relation)
            if (prior is not None and inc is not None and rel and rel.functional
                    and _value_key(prior.object) != _value_key(inc.object)):
                groups.setdefault((prior.subject, r.relation), set()).update(
                    [prior.id, inc.id])
                group_priors.setdefault((prior.subject, r.relation), set()).add(prior.id)
        result, exposed_all = [], []
        for (subject, relation), member_ids in sorted(groups.items()):
            members = [active[mid] for mid in member_ids]
            exposed, linkage = [], []
            for m in members:
                if m.assertable or m.id in selected:
                    exposed.append(m)
                else:
                    linkage.append(ContestedLinkage(
                        edge_id=m.id, partition="unverified",
                        authority=_edge_effective(m)))
            exposed.sort(key=lambda e: (-_edge_effective(e), e.id))
            linkage.sort(key=lambda x: (-x.authority, x.edge_id))
            result.append(ContestedGroup(
                subject=subject, relation=relation, exposed=exposed, linkage=linkage,
                prior_edge_ids=sorted(group_priors.get((subject, relation), ()))))
            exposed_all.extend(exposed)
        return result, exposed_all

    def _fit_to_budget(self, wiki: Optional[str], edges, episodes,
                       budget: int, query: str = "") -> tuple[Optional[str], str, str, bool]:
        """Greedy selection under the token budget in the specs/0012 I10f precedence
        (mirroring the surface order; the contested block was already charged upstream):

        1. query-RELEVANT flagged assertable detail (warnings, most-overdue first);
        2. claim/inference flag lines — safety context, BEFORE the wiki (I10h);
        3. remaining assertable detail (query-relevant first, then unrelated flagged,
           then the rest in relevance order);
        4. the wiki, under its render SHARE of the budget, body clamped with the
           compile marker line kept intact (the framing is never severed);
        5. grounded episodes, newest-first admission, rendered chronologically.

        Every item is clamped at the item cap (framing + content, I10a); the
        truncation report marker is charged from the reserve BEFORE selection and
        reports dropped counts per class, SAFETY distinctly (I10b); class decides
        priority, the gate decides presentation — classification never moves an
        item across the partition (I10f)."""
        from .budgets import REPORT_RESERVE, clamp_item
        est = self._est_tokens
        cap = self.config.item_cap_tokens
        qtok = set(re.findall(r"[a-z0-9]+", (query or "").lower()))

        def _rel(e) -> bool:
            etok = set(re.findall(r"[a-z0-9]+",
                                   f"{e.subject} {e.relation} {e.object} {e.note}".lower()))
            return bool(qtok & etok)

        assertable = [e for e in edges if e.assertable]
        flagged_rel = [e for e in assertable if e.needs_confirmation and _rel(e)]
        flagged_rel.sort(key=lambda e: (e.provenance.observed_at, e.id))   # most overdue
        flagged_unrel = [e for e in assertable if e.needs_confirmation and not _rel(e)]
        flagged_unrel.sort(key=lambda e: (e.provenance.observed_at, e.id))
        rest = [e for e in assertable if not e.needs_confirmation]         # relevance order
        # I10f: the full taxonomy — COMMITMENTS (dated, nearest first) rank above plain
        # context; VARIANTS (a further member of a (subject, relation) group already
        # represented) rank LAST, below the wiki. Variancy never demotes the first
        # representative.
        _date_re = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
        commitments = [e for e in rest if _date_re.search(e.object + " " + e.note)]
        commitments.sort(key=lambda e: (_date_re.search(e.object + " " + e.note).group(0),
                                        e.id))                             # nearest first
        commit_ids = {e.id for e in commitments}
        plain, variants, _seen_groups = [], [], set()
        for e in rest:
            if e.id in commit_ids:
                continue
            g = (e.subject, e.relation)
            (variants if g in _seen_groups else plain).append(e)
            _seen_groups.add(g)

        from .budgets import clamp_edge_line

        claim_edges = [e for e in edges if e.quarantined or (e.active and e.use_only)]
        # I10h protects the QUERY-MATCHED claim flag above the wiki; an unmatched claim
        # renders fenced but admits after the wiki (it outranks only variants).
        claims_matched = [e for e in claim_edges if _rel(e)]
        claims_unmatched = [e for e in claim_edges if not _rel(e)]
        # claim lines carry their never-assert label at the FRONT; content still
        # clamps first so the label+content pair stays within the cap (I10c)
        def _claim_lines(es):
            return [ln for ln in
                    (clamp_edge_line(e, cap, render_edges) for e in es) if ln]
        ep_lines = [clamp_item(f"[{e.date}] {e.summary}", cap) for e in episodes
                    if not e.provenance.third_party_influenced]
        tp_ep_lines = [clamp_item(f"[{e.date}] {e.summary}", cap) for e in episodes
                       if e.provenance.third_party_influenced]

        headers = est("## RELEVANT DETAIL\n") \
            + est("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n")
        remaining = budget - headers - REPORT_RESERVE          # I10b: report reserved first

        n_clamped = 0

        def _admit_edges(es, sel, best_effort_first=False):
            # I10a: the best-effort FIRST item is clamped TO FIT the remaining budget
            # (content-first, so its safety framing survives) — an oversized item is
            # clamped, never emitted whole and never silently dropped; a clamp is a
            # truncation EVENT and is counted, never silent
            dropped = 0
            nonlocal remaining, n_clamped
            for k, e in enumerate(es):
                raw = render_edges([e])
                line = clamp_edge_line(e, cap, render_edges)
                if not line:
                    continue
                if est(raw) > cap:
                    n_clamped += 1
                cost = est(line) + 1                       # +1: the join newline
                if cost > remaining:
                    if best_effort_first and k == 0 and not sel and remaining >= 16:
                        line = clamp_edge_line(e, remaining - 1, render_edges)
                        cost = est(line) + 1
                        if cost <= remaining:
                            n_clamped += 1                 # clamp-to-fit SIGNALS (I10a)
                            sel.append(line)
                            remaining -= cost
                            continue
                    dropped += 1
                    continue
                sel.append(line)
                remaining -= cost
            return dropped

        def _admit(lines, sel):
            dropped = 0
            nonlocal remaining
            for line in lines:
                cost = est(line) + 1                       # +1: the join newline
                if cost > remaining:
                    dropped += 1
                    continue
                sel.append(line)
                remaining -= cost
            return dropped

        # the FROZEN §4c(iv) recall order: contested (upstream) → query-relevant flagged
        # → query-matched claim flags → other flagged → commitments → the WIKI within its
        # share → relevance-ranked grounded edges → episodes (newest) → the remaining
        # unverified partition → variants LAST.
        sel_edges: list[str] = []
        d_flag_rel = _admit_edges(flagged_rel, sel_edges, best_effort_first=True)
        sel_unv: list[str] = []
        d_safety = _admit(_claim_lines(claims_matched) + tp_ep_lines, sel_unv)
        d_flag_unrel = _admit_edges(flagged_unrel, sel_edges)
        d_commit = _admit_edges(commitments, sel_edges)

        wiki_dropped = False
        if wiki:
            share_cap = int(budget * self.config.wiki_render_share)
            allowance = min(remaining, share_cap)
            if est(wiki) <= allowance:
                remaining -= est(wiki)
            else:
                marker_ln = wiki.splitlines()[-1] if wiki.splitlines() else ""
                keep_marker = marker_ln.startswith("[[veracium-wiki-compile:")
                body_allow = allowance - (est(marker_ln) if keep_marker else 0)
                if body_allow >= 16:                       # clamp the BODY, keep the marker
                    body = "\n".join(wiki.splitlines()[:-1]) if keep_marker else wiki
                    clamped = clamp_item(body, body_allow)
                    wiki = clamped + ("\n" + marker_ln if keep_marker else "")
                    remaining -= est(wiki)
                    wiki_dropped = True                    # counted as clamped in the report
                else:
                    wiki, wiki_dropped = None, True

        d_plain = _admit_edges(plain, sel_edges,           # grounded edges AFTER the wiki
                               best_effort_first=not sel_edges)
        sel_eps: list[str] = []
        d_eps = 0
        for line in reversed(ep_lines):                    # episodes: newest first
            cost = est(line) + 1                           # +1: the join newline
            if cost > remaining:
                d_eps += 1
                continue
            sel_eps.append(line)
            remaining -= cost
        sel_eps.reverse()                                  # render chronologically
        d_safety += _admit(_claim_lines(claims_unmatched), sel_unv)   # remaining partition
        d_variants = _admit_edges(variants, sel_edges)                # variants LAST

        d_detail = d_flag_rel + d_flag_unrel + d_commit + d_plain + d_variants
        truncated = bool(d_detail or d_safety or wiki_dropped or d_eps or n_clamped)
        detail = "\n".join(sel_edges + sel_eps).strip()
        if truncated:                                      # the I10b report, per class,
            from .budgets import bounded_count as _bc      # counts BOUNDED-WIDTH (R9-2)
            detail = (detail + ("\n" if detail else "")
                      + f"[budget: dropped {_bc(d_detail)} detail / {_bc(d_safety)} SAFETY / "
                        f"{_bc(n_clamped)} clamped / "
                        f"wiki {'clamped-or-dropped' if wiki_dropped else 'kept'} / "
                        f"{_bc(d_eps)} episodes]")
        unverified = "\n".join(sel_unv).strip()
        return wiki, detail, unverified, truncated

    def answer(self, user_id: str, query: str) -> str:
        """Recall + the evidence-grounded abstention gate → a direct answer.

        The convenience path for hosts that want veracium to answer: it answers only
        from grounded memory, refuses to assert unverified third-party claims, and
        abstains ("I don't know") rather than confabulate when memory lacks the
        answer — the finding-23 fix for both confabulation and the episodic
        injection leak."""
        r = self.recall(user_id, query)   # already error-guarded
        t0 = time.perf_counter()
        try:
            ans = _gate.answer(self.llm, query, r.grounded, r.unverified)
        except Exception as e:
            self._on_error("answer", e, user_id)
            raise
        self._record("answer", {"abstained": bool(_ABSTAINED.search(ans)),
                                "ms": int((time.perf_counter() - t0) * 1000)}, user_id)
        return ans

    # -- maintenance -------------------------------------------------------
    def maintain(self, user_id: str, *, consolidate: bool = True) -> dict:
        """Run lifecycle maintenance for `user_id` — the "overnight" job.

        Applies volatility-driven expiry (transient facts lapse, durable facts
        get flagged possibly-stale, never silently dropped) and, if enabled,
        consolidates cold episodes into denser records (preserving first failures,
        fixes, illnesses, and dated commitments). Idempotent; call on a schedule."""
        try:
            report = {"expiry": _lifecycle.expire(self.store, user_id, self.config)}
            if consolidate:
                report["consolidation"] = _lifecycle.consolidate(
                    self.store, self.llm, user_id, self.config)
        except Exception as e:
            self._on_error("maintain", e, user_id)
            raise
        ex, co = report["expiry"], report.get("consolidation", {})
        self._record("maintain", {"lapsed": ex["lapsed"], "decayed": ex["decayed"],
                                  "flagged": ex["flagged_for_confirmation"],
                                  "consolidated_in": co.get("consolidated", 0),
                                  "consolidated_out": co.get("into", 0)}, user_id)
        return report

    # -- self-check --------------------------------------------------------
    def self_check(self, *, record: bool = True) -> dict:
        """Run veracium's load-bearing guarantees (supersession, injection defense,
        abstention) against a fresh throwaway store and return content-free
        pass/fail counters. Uses this Memory's own `llm`; never touches this
        Memory's store. When telemetry is wired and `record` is True, the counters
        are emitted as a content-free `selfcheck` event (see veracium.selfcheck)."""
        from . import selfcheck as _sc
        result = _sc.run(self.llm, relations=self.config.relations)
        if record:
            self._record("selfcheck", result)  # non-scalar keys are dropped by the collector
        return result

    # -- telemetry (opt-in, content-free; see veracium.telemetry) ------------
    def flush_telemetry(self) -> bool:
        """If telemetry is enabled and due, POST the anonymous aggregate. Safe to
        call often (e.g. after each request or on a timer) — it no-ops until the
        interval elapses and never raises. Returns True if a send happened."""
        if self.telemetry is None:
            return False
        from . import telemetry as _t
        return _t.flush_if_due(_t.TelemetryConfig.load(), self.telemetry)

    def telemetry_preview(self) -> Optional[dict]:
        """Exactly what a flush would send right now, or None if telemetry is off."""
        if self.telemetry is None:
            return None
        from . import telemetry as _t
        return _t.preview(_t.TelemetryConfig.load(), self.telemetry)

    # -- diagnostics / error reporting (opt-in; see veracium.diagnostics) -----
    def report_error(self, *, interactive: Optional[bool] = None) -> bool:
        """Send the captured local error log for diagnosis, subject to consent
        (advance permission, or an interactive yes). No-ops if diagnostics is off,
        nothing was captured, or no endpoint is configured; never raises. A host
        that caught an veracium error can call this to offer to report it."""
        if self.diagnostics is None or not self.diagnostics.has_pending():
            return False
        return self.diagnostics.send(interactive=interactive)

    def diagnostics_preview(self) -> Optional[dict]:
        """Exactly what a report would send (redacted if enabled) — the log content
        that would leave the machine — or None if diagnostics is off."""
        if self.diagnostics is None:
            return None
        return self.diagnostics.preview()

    # -- host queries ----------------------------------------------------------
    def list_entities(self) -> list[dict]:
        """Distinct ids that have accumulated memory, with edge/episode counts.
        For hosts deciding what to recall proactively or auditing coverage.
        Host/admin surface — not exposed over MCP by design (cross-user
        enumeration is not an agent tool)."""
        return self.store.list_users()

    def introspect(self, user_id: str, *, mode: str = "summary") -> dict:
        """The formatted transparency view: "what do you know about me, and
        where did it come from?" — counts by relation / evidence author /
        disclosure tier, lifecycle state, retired history by reason, episode
        counts, and `wiki_compile_record` (specs/0012: the cached wiki's
        authoritative compile-drop marker, parsed + verbatim — status
        ok/absent/legacy/malformed; counts int or "999+"; the cached record
        only, never a current-store hypothetical);
        mode="categories" adds the facts themselves grouped by
        relation, rendered with their provenance markers. LLM-free and
        store-only; the complete raw dump remains `export_memory()`, erasure
        remains `forget()`. CLI: `veracium introspect --user X`."""
        from . import introspect as _introspect
        try:
            out = _introspect.report(self.store, user_id, mode=mode)
        except Exception as e:
            self._on_error("introspect", e, user_id)
            raise
        self._record("introspect", {"facts": out["facts"],
                                    "claims": out["unverified_claims"],
                                    "episodes": sum(out["episodes"].values())},
                     user_id)
        return out

    def edges_since(self, user_id: str, since) -> list[Edge]:
        """Edges *learned* after `since` (ISO date/datetime string, or a
        datetime) — filtered on `provenance.observed_at`, i.e. when veracium
        recorded the fact, not `valid_from` (when it became true). Includes
        superseded and quarantined edges so change-detection sees everything;
        filter on `.active` / `.assertable` / provenance as needed."""
        from datetime import datetime, timezone
        if isinstance(since, str):
            since = datetime.fromisoformat(since)
        if since.tzinfo is None:
            since = since.replace(tzinfo=timezone.utc)
        return [e for e in self.store.edges(user_id, active_only=False,
                                            include_quarantined=True)
                if e.provenance.observed_at > since]

    # -- user feedback verbs -------------------------------------------------
    def _find_edge(self, user_id: str, edge_id: str) -> Edge:
        for e in self.store.edges(user_id, active_only=False, include_quarantined=True):
            if e.id == edge_id:
                return e
        raise ValueError(f"no edge {edge_id!r} for user {user_id!r}")

    def dispute(self, user_id: str, edge_id: str, *, reason: str = "",
                actor: str = "user") -> dict:
        """The user challenges a remembered fact. Non-destructive: the edge is
        invalidated (reason 'disputed') — out of every assertable surface
        immediately, retained as queryable history — and the dispute itself is
        recorded as a system episode carrying the actor and reason. If the fact
        was actually right, it re-enters the normal way: new evidence via
        `remember()`. Not exposed over MCP (an agent-callable suppress verb is
        a prompt-injection target); hosts wire it to a real user action."""
        edge = self._find_edge(user_id, edge_id)
        if not edge.active:
            raise ValueError(f"edge {edge_id!r} is not active (already "
                             f"{edge.invalidation_reason or 'invalidated'})")
        from datetime import date as _date
        today = _date.today().isoformat()
        self.store.invalidate_edge(edge_id, utcnow(), "disputed")
        note = f" — {reason}" if reason else ""
        self.store.add_episode(Episode(
            id=f"ep-{uuid4().hex[:12]}", user_id=user_id, date=today,
            summary=f"({actor}) disputed the remembered fact "
                    f"'{edge.relation}: {edge.object}'{note}",
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=f"dispute:{edge_id}")))
        self._record("feedback", {"disputed": 1, "confirmed": 0}, user_id)
        return {"disputed": edge_id, "relation": edge.relation}

    def confirm(self, user_id: str, edge_id: str, *,
                date: Optional[str] = None,
                actor: ConfirmationActor = ConfirmationActor.USER,
                call_path: ConfirmationCallPath = ConfirmationCallPath.HOST_API,
                correlation_id: Optional[str] = None) -> dict:
        """The user explicitly validates a remembered fact (specs/0008). This is the
        ONLY path that clears `needs_confirmation`; reinforcement no longer does. In
        one atomic store operation it clears the flag, advances liveness
        (`observed_at`) and confidence, writes the confirmation episode, and records
        the mandatory confirmation.

        Only assertable facts can be confirmed: elevating a quarantined claim or a
        third-party inference by 'confirmation' would be a laundering vector — if
        the user affirms a claim, that affirmation is new user-authored evidence and
        belongs in `remember()`.

        `actor` and `call_path` are closed enums (audit metadata; they grant
        nothing — authority is the protected call path, not the label). `confirm()`
        is HOST API only, never model-reachable. `correlation_id` (opaque, ≤64
        chars) gives replay protection across an unknown commit outcome; omitted, one
        is generated and there is none to retry against. The return is a mapping:
        `{confirmed, valid_from, confirmed_at, correlation_id, replayed}`."""
        # Closed-enum + charset validation BEFORE any mutation (§6c/C9). A string is
        # accepted only if it names an enum member — a free-form label is rejected,
        # not stored (C2a).
        actor = ConfirmationActor(actor)
        call_path = ConfirmationCallPath(call_path)
        correlation_id = (validate_correlation_id(correlation_id)
                          if correlation_id is not None
                          else f"auto-{uuid4().hex}")
        self._find_edge(user_id, edge_id)              # ValueError if absent
        # The canonical request identity is the CALLER's inputs — never the derived
        # instant — so two date-less retries are the SAME request (§6c). `OMITTED`
        # is a value; `rule_version` guards against a rule change colliding digests.
        caller_date = date if date is not None else "OMITTED"
        request_digest = hashlib.sha256("\x1f".join(
            [user_id, edge_id, call_path.value, actor.value,
             CONFIRMATION_RULE_VERSION, caller_date]).encode()).hexdigest()
        from datetime import date as _date
        when = _event_dt(date or _date.today().isoformat())
        conf = self.store.confirm_edge(
            user_id, edge_id, actor=actor, call_path=call_path,
            correlation_id=correlation_id, request_digest=request_digest,
            confirmed_at=when)
        if not conf.replayed:
            self._record("feedback", {"disputed": 0, "confirmed": 1}, user_id)
        # `valid_from` is first-known and immutable, so reading it back is stable on
        # replay; `confirmed_at` comes from the RECORD (the stored instant on replay,
        # never a fresh one). M2 (0.4.5): the return names the confirmation instant
        # and the edge's first-known separately, each meaning what it says.
        edge = self._find_edge(user_id, edge_id)
        return {"confirmed": edge_id,
                "valid_from": edge.valid_from.date().isoformat(),
                "confirmed_at": conf.confirmed_at.date().isoformat(),
                "correlation_id": conf.correlation_id,
                "replayed": conf.replayed}

    # -- outcome tracking (engine-written; never MCP) ------------------------
    _OUTCOME_ACTORS = {"user": EvidenceAuthor.USER, "system": EvidenceAuthor.SYSTEM}

    def record_outcome(self, user_id: str, edge_id: str, *, outcome,
                       evidence_ref: str, actor: str = "system",
                       corrected_value: Optional[str] = None,
                       date: Optional[str] = None,
                       context_ref: Optional[str] = None) -> dict:
        """Record that a conclusion built on `edge_id` was used / judged.

        Writes (or upgrades) a `kind="outcome"` episode — the source of truth —
        and maintains the edge's derived counters. The upgrade path is keyed by
        (`edge_id`, `evidence_ref`): a use recorded UNREVIEWED is upgraded in
        place when a judgment arrives for the same use.

        DELIBERATELY NEVER supersedes the fact (the platform's edge-blind
        clarification): one run's evidence_ref touches every fact it consulted,
        so upgrading a *use* to `corrected` must not invalidate supporting
        facts — `corrected_value` here is recorded as the decision's true value
        only. Fact-level correction is the explicit `correct()` verb.
        `challenged` sets the existing needs-confirmation flag; nothing else
        touches gate placement — counters are information, not gating."""
        from .schema import Outcome
        outcome = Outcome(outcome)
        author = self._OUTCOME_ACTORS.get(actor)
        if author is None:
            raise ValueError(f"actor must be 'user' or 'system', not {actor!r}")
        if outcome in (Outcome.CONFIRMED, Outcome.CORRECTED) and actor != "user":
            raise ValueError(f"{outcome.value} is a human judgment (actor='user')")
        if outcome in (Outcome.CHALLENGED, Outcome.CONCURRED) and actor != "system":
            raise ValueError(f"{outcome.value} is a system judgment (actor='system')")
        edge = self._find_edge(user_id, edge_id)
        from datetime import date as _date
        date = _event_dt(date or _date.today().isoformat()).date().isoformat()

        # specs/0009: NEVER mutate a prior judgment — append a new chain link.
        # The head is the max-`seq` outcome episode for (edge_id, evidence_ref);
        # `append_outcome_if_head` CAS-appends and retries if the head moved. The
        # `[prior judgment was …]` note is rebuilt against the WINNING head, and
        # `upgraded` reflects the successful attempt (H11, round-5 Correction A).
        val = f" (true value: {corrected_value})" if corrected_value else ""
        while True:
            head = self._outcome_head(user_id, edge_id, evidence_ref)
            summary = (f"({actor}) {outcome.value}: use of "
                       f"'{edge.relation}: {edge.object}'{val}")
            if head is not None:
                was = head.provenance.author_of_evidence
                if was != author:
                    summary += f" [prior judgment was {was.value}-authored]"
            draft = OutcomeJudgmentDraft(
                author=author, event_timestamp=date, outcome=outcome,
                summary=summary, context_ref=context_ref)
            appended = self.store.append_outcome_if_head(
                user_id, edge_id, evidence_ref,
                head.id if head is not None else None, draft)
            if appended is not HEAD_MOVED:
                break                                    # committed
        upgraded = head is not None                      # revised an existing chain

        # Counters are DERIVED from chain heads (H6), recomputed rather than
        # mutated in place — the denormalisation the M4 defect was.
        times_used, counts = self._edge_outcome_aggregates(user_id, edge_id)
        edge.times_used = times_used
        edge.outcome_counts = counts
        # last_outcome / last_outcome_at are DEPRECATED (Option A) — best-effort,
        # no cross-chain guarantee.
        edge.last_outcome = outcome
        edge.last_outcome_at = _event_dt(date)
        if outcome is Outcome.CHALLENGED:
            edge.needs_confirmation = True   # "confirm before relying" — existing surface
        self.store.add_edge(edge)
        self._record("outcome", {"new": 0 if upgraded else 1,
                                 "upgraded": 1 if upgraded else 0}, user_id)
        return {"edge_id": edge_id, "outcome": outcome.value, "upgraded": upgraded,
                "times_used": times_used}

    def _outcome_head(self, user_id: str, edge_id: str, evidence_ref: str):
        """The head (max-`seq`) of the `(edge_id, evidence_ref)` outcome chain, or
        None — derived, never materialised (specs/0009 H-Q2)."""
        head = None
        for ep in self.store.episodes(user_id):
            if (ep.kind == "outcome" and ep.edge_id == edge_id
                    and ep.provenance.evidence_ref == evidence_ref):
                if head is None or (ep.seq or 0) > (head.seq or 0):
                    head = ep
        return head

    def _edge_outcome_aggregates(self, user_id: str, edge_id: str):
        """`(times_used, outcome_counts)` for an edge, DERIVED from chain heads
        (specs/0009 H6): one chain per `(edge_id, evidence_ref)` use, its head the
        max-`seq` link. `times_used` = distinct chains; `outcome_counts` = the head
        outcome of each chain. A five-judgment chain about one use is still one use."""
        heads: dict = {}
        for ep in self.store.episodes(user_id):
            if ep.kind == "outcome" and ep.edge_id == edge_id:
                key = ep.provenance.evidence_ref
                cur = heads.get(key)
                if cur is None or (ep.seq or 0) > (cur.seq or 0):
                    heads[key] = ep
        counts: dict = {}
        for ep in heads.values():
            if ep.outcome is not None:
                counts[ep.outcome.value] = counts.get(ep.outcome.value, 0) + 1
        return len(heads), counts

    def correct(self, user_id: str, edge_id: str, corrected_value: str, *,
                actor: str = "user", evidence_ref: Optional[str] = None,
                date: Optional[str] = None) -> dict:
        """Explicit FACT-level correction: the remembered value itself was wrong.
        Supersedes the edge with `invalidation_reason="corrected"` (distinguishable
        at recall from natural change) and records the corrected value as a new
        user-authored assertable edge. This — and only this — invalidates a fact;
        `record_outcome(outcome="corrected")` judges a *decision* and never
        touches the facts it consulted. Not an MCP tool."""
        edge = self._find_edge(user_id, edge_id)
        if not edge.active:
            raise ValueError(f"edge {edge_id!r} is not active (already "
                             f"{edge.invalidation_reason or 'invalidated'})")
        from datetime import date as _date
        date = date or _date.today().isoformat()
        when = _event_dt(date)
        date = when.date().isoformat()          # normalise once, as confirm()
        self.store.invalidate_edge(edge_id, when, "corrected")
        new = Edge(
            id=f"e-{uuid4().hex[:12]}", user_id=user_id, subject=edge.subject,
            relation=edge.relation, object=corrected_value, note=edge.note,
            volatility=edge.volatility, supersedes=edge_id, valid_from=when,
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=evidence_ref or f"correct:{edge_id}",
                                  observed_at=when))
        self.store.add_edge(new)
        self.store.add_episode(Episode(
            id=f"ep-{uuid4().hex[:12]}", user_id=user_id, date=date,
            summary=(f"({actor}) corrected '{edge.relation}: {edge.object}' "
                     f"to '{corrected_value}'"),
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=evidence_ref or f"correct:{edge_id}",
                                  observed_at=when)))
        self._record("feedback", {"disputed": 0, "confirmed": 0, "corrected": 1}, user_id)
        return {"corrected": edge_id, "replacement": new.id}

    # -- compliance erasure --------------------------------------------------
    def forget(self, user_id: str) -> dict:
        """Irreversibly erase everything stored for `user_id`: all edges
        (superseded history and quarantined claims included), all episodes,
        the wiki cache, and counters. Returns {"edges": n, "episodes": n}.

        This is the data-subject right ("right to be forgotten"), deliberately
        distinct from lifecycle: `maintain()` never deletes, `forget()` never
        preserves. There is no undo — export first (`export_memory`) if a
        recoverable copy is wanted. Confirmation is the host's responsibility."""
        r = self.store.forget_user(user_id)
        self._record("forget", {"edges": r["edges"], "episodes": r["episodes"]}, user_id)
        return r

    # -- portability (see veracium.portability for the format) --------------
    def export_memory(self, user_id: str, path) -> dict:
        """Write `user_id`'s complete memory to `path` as portable JSONL —
        full provenance/disclosure/history included, nothing summarized.
        The inverse of `import_memory`; see `docs/api.md` and the trust note
        in `veracium.portability`."""
        from . import portability
        r = portability.export_memory(self.store, user_id, path)
        self._record("export", {"edges": r["edges"], "episodes": r["episodes"]}, user_id)
        return r

    def import_memory(self, path, *, user_id: Optional[str] = None,
                      restore: bool = False) -> dict:
        """Load a Veracium JSONL export into this store. Idempotent (existing
        ids are skipped, never overwritten); `user_id` remaps the records.

        Trust note (specs/0005): the DEFAULT import caps every record's trust
        — nothing imported is assertable or grounded as this user's own
        testimony, whatever the file claims. ``restore=True`` (mutually
        exclusive with ``user_id``) preserves the file's trust fields exactly
        and is the operator's assertion that the file is this store's own
        history; use it only on files you exported yourself or have
        independently verified. The returned dict carries ``capped``; the
        audit record deliberately keeps its shipped field set (§7a)."""
        from . import portability
        r = portability.import_memory(self.store, path, user_id=user_id,
                                      restore=restore)
        self._record("import", {"edges": r["edges"], "episodes": r["episodes"],
                                "skipped": r["skipped"]}, r["user_id"])
        return r

    def close(self) -> None:
        self.store.close()
