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
from .graph import subgraph_for_query
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
                 derived_from: Optional[EvidenceAuthor] = None) -> dict:
        """Ingest one interaction event into `user_id`'s memory.

        `author` is the trust-critical input: use EvidenceAuthor.THIRD_PARTY for
        received email / external documents so their claims are quarantined.

        Authorship is per-event; if the event's *content* embeds material a
        lower-trust party influenced — a system-authored summary quoting a
        received email's subject or body — declare it with `derived_from`
        (e.g. `author=SYSTEM, derived_from=THIRD_PARTY`). Trust is capped at
        the minimum of the two: nothing extracted from such an event is ever
        assertable, closing the system-event laundering bypass."""
        from datetime import date as _date
        date = date or _date.today().isoformat()
        t0 = time.perf_counter()
        try:
            r = ingest_event(self.store, self.llm, user_id, event_text=event_text,
                             author=author, date=date, event_type=event_type,
                             evidence_ref=evidence_ref, derived_from=derived_from,
                             relations=self.config.relations)
        except Exception as e:
            self._on_error("remember", e, user_id)
            raise
        self._record("ingest", {"facts": r["facts"], "quarantined": r["quarantined"],
                                "episodes": 1 if r["episode"] else 0,
                                "unparseable": 1 if r.get("unparseable") else 0,
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

        `token_budget` caps the rendered context (heuristic: chars/4 — veracium
        is tokenizer-agnostic, so treat it as approximate, not exact). Selection
        priority when trimming: query-matched facts first, then unverified-claim
        flags (a host reasoning near a claim should see it flagged), then the
        wiki, then recent episodes. Best-effort minimum of one item; check
        `Recall.truncated` / `Recall.tokens_estimated`.

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
        wiki = _compile.ensure_wiki(self.store, self.llm, user_id,
                                    self.config.wiki_recompile_after_writes,
                                    self.config.relations)
        edges = subgraph_for_query(self.store, user_id, query,
                                   max_edges=self.config.max_subgraph_edges,
                                   coverage_share=self.config.subgraph_coverage_share,
                                   relations=self.config.relations)
        # outcome events are structured records, not narrative — they'd crowd
        # out interaction history for high-volume consumers; their signal
        # reaches recall as counters rendered on the edges themselves
        episodes = [e for e in self.store.episodes(user_id)
                    if e.kind != "outcome"][-self.config.max_recent_episodes:]

        truncated = False
        if token_budget is None:
            detail_grounded, unverified = _gate.partition(edges, episodes)
        else:
            wiki, detail_grounded, unverified, truncated = self._fit_to_budget(
                wiki, edges, episodes, token_budget)

        grounded_parts = []
        if wiki:
            grounded_parts.append(wiki)
        if detail_grounded:
            grounded_parts.append("## RELEVANT DETAIL\n" + detail_grounded)
        grounded = "\n\n".join(grounded_parts).strip() or "(no memory yet for this user)"

        context = grounded
        if unverified:
            context += ("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n"
                        + unverified)
        # specs/0003 §4c-ii: the structured contested surface + the de-duplicated
        # Recall.edges union. The exposed higher-authority grounded prior is included
        # even if the query did not select it (the I6a guarantee, budget-independent).
        contested, exposed_extra = self._build_contested(user_id, edges)
        seen = {e.id for e in edges}
        for e in exposed_extra:
            if e.id not in seen:
                edges.append(e)
                seen.add(e.id)

        self._record("recall", {"wiki_used": bool(wiki), "subgraph_edges": len(edges),
                                "grounded_items": sum(1 for e in edges if not e.quarantined),
                                "unverified_items": sum(1 for e in edges if e.quarantined),
                                "trimmed": 1 if truncated else 0}, user_id)
        return Recall(context=context, grounded=grounded, unverified=unverified,
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated,
                      contested=contested)

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
        for r in refusals:
            prior, inc = active.get(r.prior_edge_id), active.get(r.incoming_edge_id)
            rel = relations.get(r.relation)
            if (prior is not None and inc is not None and rel and rel.functional
                    and _value_key(prior.object) != _value_key(inc.object)):
                groups.setdefault((prior.subject, r.relation), set()).update(
                    [prior.id, inc.id])
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
            result.append(ContestedGroup(subject=subject, relation=relation,
                                         exposed=exposed, linkage=linkage))
            exposed_all.extend(exposed)
        return result, exposed_all

    def _fit_to_budget(self, wiki: Optional[str], edges, episodes,
                       budget: int) -> tuple[Optional[str], str, str, bool]:
        """Greedy selection under the token budget, in priority order:

        1. query-matched assertable detail (edge lines, already relevance-sorted);
        2. unverified-claim/report lines — safety context: if the host is about
           to reason near a claim, the never-assert flag must survive trimming;
        3. the wiki (curated breadth), all-or-nothing — it is pre-budgeted at
           compile time and loses its meaning cut mid-sentence;
        4. recent episodes, newest first (rendered chronologically).

        Sections stop at the first line that doesn't fit (lines are
        relevance/recency-sorted — skipping a long important line to admit a
        short unimportant one would invert the ranking). Best-effort minimum:
        the single top item is always included even if it alone overflows."""
        est = self._est_tokens
        edge_lines, ep_lines, claim_lines, tp_ep_lines = _gate.partition_parts(
            edges, episodes)
        unv_lines = claim_lines + tp_ep_lines
        headers = est("## RELEVANT DETAIL\n") \
            + est("\n\n## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n")
        remaining = budget - headers
        truncated = False

        sel_edges: list[str] = []
        for line in edge_lines:
            cost = est(line)
            if cost > remaining and sel_edges:
                truncated = True
                break
            sel_edges.append(line)      # first item is best-effort unconditional
            remaining -= cost

        sel_unv: list[str] = []
        for line in unv_lines:
            cost = est(line)
            if cost > remaining:
                truncated = True
                break
            sel_unv.append(line)
            remaining -= cost

        if wiki and est(wiki) <= remaining:
            remaining -= est(wiki)
        else:
            truncated = truncated or bool(wiki)
            wiki = None

        sel_eps: list[str] = []
        n_grounded_eps = len(ep_lines)
        for line in reversed(ep_lines):          # newest first under budget
            cost = est(line)
            if cost > remaining:
                truncated = True
                break
            sel_eps.append(line)
            remaining -= cost
        sel_eps.reverse()                        # render chronologically
        truncated = truncated or len(sel_eps) < n_grounded_eps \
            or len(sel_edges) < len(edge_lines) or len(sel_unv) < len(unv_lines)

        detail = "\n".join(sel_edges + sel_eps).strip()
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
        counts; mode="categories" adds the facts themselves grouped by
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

    def import_memory(self, path, *, user_id: Optional[str] = None) -> dict:
        """Load a Veracium JSONL export into this store. Idempotent (existing
        ids are skipped, never overwritten); `user_id` remaps the records.
        Trust note: import only from sources you trust as much as the database
        file itself — provenance in the file is data."""
        from . import portability
        r = portability.import_memory(self.store, path, user_id=user_id)
        self._record("import", {"edges": r["edges"], "episodes": r["episodes"],
                                "skipped": r["skipped"]}, r["user_id"])
        return r

    def close(self) -> None:
        self.store.close()
