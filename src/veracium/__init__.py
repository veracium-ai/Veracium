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
from dataclasses import dataclass
from typing import Optional

from . import compile as _compile
from . import gate as _gate
from . import lifecycle as _lifecycle
from .config import MemoryConfig

# Local-only abstention heuristic: computed on the answer text to emit a content-
# free boolean for telemetry. The text itself never leaves.
_ABSTAINED = re.compile(r"don'?t know|no (confirmed|record|information|such)|"
                        r"unverified|can'?t (verify|confirm)|not (sure|aware)", re.I)
from .graph import subgraph_for_query
from .ingest import _event_dt, ingest_event
from .llm.base import Complete, Embed
from .schema import Edge, Episode, EvidenceAuthor, Provenance, SourceType, utcnow
from .store.base import Store
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
    def recall(self, user_id: str, query: str, *,
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
        """
        if token_budget is not None and token_budget <= 0:
            raise ValueError("token_budget must be a positive number of tokens")
        try:
            return self._recall(user_id, query, token_budget)
        except Exception as e:
            self._on_error("recall", e, user_id)
            raise

    @staticmethod
    def _est_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    def _recall(self, user_id: str, query: str,
                token_budget: Optional[int] = None) -> Recall:
        wiki = _compile.ensure_wiki(self.store, self.llm, user_id,
                                    self.config.wiki_recompile_after_writes)
        edges = subgraph_for_query(self.store, user_id, query,
                                   max_edges=self.config.max_subgraph_edges)
        episodes = self.store.episodes(user_id)[-self.config.max_recent_episodes:]

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
        self._record("recall", {"wiki_used": bool(wiki), "subgraph_edges": len(edges),
                                "grounded_items": sum(1 for e in edges if not e.quarantined),
                                "unverified_items": sum(1 for e in edges if e.quarantined),
                                "trimmed": 1 if truncated else 0}, user_id)
        return Recall(context=context, grounded=grounded, unverified=unverified,
                      edges=edges, episodes=episodes,
                      tokens_estimated=self._est_tokens(context), truncated=truncated)

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

    def confirm(self, user_id: str, edge_id: str, *, actor: str = "user",
                date: Optional[str] = None) -> dict:
        """The user explicitly validates a remembered fact: refreshes its
        validity (so it won't lapse or sit flagged possibly-stale) and records
        the confirmation as an episode with the actor. Equivalent to the
        reinforcement a re-statement triggers, minus the extraction round-trip.

        Only assertable facts can be confirmed: elevating a quarantined claim
        or third-party inference by 'confirmation' would be a laundering
        vector — if the user affirms a claim, that affirmation is new
        user-authored evidence and belongs in `remember()`."""
        edge = self._find_edge(user_id, edge_id)
        if not edge.assertable:
            raise ValueError(
                f"edge {edge_id!r} is not assertable (quarantined/use_only/"
                f"inactive) — a user affirming a claim is new evidence: "
                f"ingest it via remember(author=USER) instead")
        from datetime import date as _date
        date = date or _date.today().isoformat()
        edge.valid_from = _event_dt(date)
        edge.needs_confirmation = False
        edge.provenance.confidence = max(edge.provenance.confidence, 0.9)
        self.store.add_edge(edge)
        self.store.add_episode(Episode(
            id=f"ep-{uuid4().hex[:12]}", user_id=user_id, date=date,
            summary=f"({actor}) confirmed '{edge.relation}: {edge.object}' still holds",
            provenance=Provenance(source_type=SourceType.STATED,
                                  author_of_evidence=EvidenceAuthor.USER,
                                  evidence_ref=f"confirm:{edge_id}")))
        self._record("feedback", {"disputed": 0, "confirmed": 1}, user_id)
        return {"confirmed": edge_id, "valid_from": date}

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
