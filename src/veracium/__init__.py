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
from .ingest import ingest_event
from .llm.base import Complete, Embed
from .schema import Edge, Episode, EvidenceAuthor
from .store.base import Store
from .store.sqlite import SqliteStore

__all__ = ["Memory", "MemoryConfig", "Recall", "Store", "SqliteStore",
           "Complete", "Embed", "EvidenceAuthor"]


@dataclass
class Recall:
    """The result of a recall.

    `context` is a ready-to-inject block (grounded memory + a fenced never-assert
    section). For hosts that want the abstention gate, `grounded` and `unverified`
    are the two partitions the gate operates on (see `Memory.answer`)."""
    context: str
    grounded: str
    unverified: str
    edges: list[Edge]
    episodes: list[Episode]


class Memory:
    def __init__(self, *, llm: Complete, store: Optional[Store] = None,
                 embed: Optional[Embed] = None, config: Optional[MemoryConfig] = None,
                 telemetry=None, diagnostics=None):
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

    def _record(self, event: str, fields: dict) -> None:
        if self.telemetry is not None:
            try:
                self.telemetry.record(event, fields)
            except Exception:
                pass  # telemetry must never break memory

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
                                "ms": int((time.perf_counter() - t0) * 1000)})
        return r

    # -- read --------------------------------------------------------------
    def recall(self, user_id: str, query: str) -> Recall:
        """Assemble grounded memory context for answering `query`.

        Combines the LLM-curated wiki (the grounded, verified working view,
        recompiled after N writes) with a per-query entity-matched subgraph for
        detail — the layered design that won both horizons. Memory is partitioned
        into grounded (assertable) and unverified (third-party claims/reports),
        so the host can apply the abstention gate via `answer()` or its own prompt.
        """
        try:
            return self._recall(user_id, query)
        except Exception as e:
            self._on_error("recall", e, user_id)
            raise

    def _recall(self, user_id: str, query: str) -> Recall:
        wiki = _compile.ensure_wiki(self.store, self.llm, user_id,
                                    self.config.wiki_recompile_after_writes)
        edges = subgraph_for_query(self.store, user_id, query,
                                   max_edges=self.config.max_subgraph_edges)
        episodes = self.store.episodes(user_id)[-self.config.max_recent_episodes:]

        detail_grounded, unverified = _gate.partition(edges, episodes)
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
                                "unverified_items": sum(1 for e in edges if e.quarantined)})
        return Recall(context=context, grounded=grounded, unverified=unverified,
                      edges=edges, episodes=episodes)

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
                                "ms": int((time.perf_counter() - t0) * 1000)})
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
                                  "consolidated_out": co.get("into", 0)})
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

    def close(self) -> None:
        self.store.close()
