"""H1–H4 hard-invariant checkers + Phase-0 soft accumulators (proposal §5–§6).

Hard gates (any count > 0 fails the tier — these are veracium's stated,
content-independent guarantees):

  H1 internal_crashes — remember/answer/maintain never raise from veracium's own
     code. Provider/transport failures (timeouts, CLI errors) raise through by
     design (the documented diagnostics re-raise contract) and are tracked as a
     soft crash-rate instead: a flaky model is not a veracium defect.
  H2 cross_user_leaks — no edge/episode returned for user A carries another user_id.
  H3 injection_leaks — a THIRD_PARTY ingest never yields an *assertable*
     user-subject edge (Edge.assertable is the enforced surface as of 0.1.3:
     claims are quarantined, inferences are use_only; both are non-assertable).
  H4 malformed_edges — every new edge has non-empty subject/relation/object and
     provenance matching the author actually passed.

Reports carry only redacted snippets (adapter.snippet) — never raw corpus text.
"""

from __future__ import annotations

import traceback
from pathlib import Path

from veracium.schema import DEFAULT_RELATIONS

from adapter import snippet

_MAX_OFFENDERS = 5  # redacted examples kept per gate


def _percentiles(ms: list[float]) -> dict:
    if not ms:
        return {}
    s = sorted(ms)
    pick = lambda q: s[min(len(s) - 1, int(q * len(s)))]
    return {"n": len(s), "p50": round(pick(0.50), 1),
            "p95": round(pick(0.95), 1), "p99": round(pick(0.99), 1)}


class Accumulators:
    def __init__(self, provider_files: tuple[str, ...] = ()):
        # files of the LLM callable; a crash whose traceback passes through one
        # of them escaped the provider, not veracium (see H1 above)
        self._provider_files = tuple(str(f) for f in provider_files if f)
        self.internal_crashes: list[dict] = []
        self.provider_crashes: list[dict] = []
        self.cross_user_leaks = 0
        self.injection_leaks: list[dict] = []
        self.malformed: list[dict] = []
        self.relation_drift: dict[str, int] = {}
        self.latency: dict[str, list[float]] = {"remember": [], "answer": [], "maintain": []}
        self.turns = self.substantive = self.empty_substantive = 0
        self.total_facts = self.total_quarantined = 0

    # -- H1 -------------------------------------------------------------------
    def crash(self, op: str, exc: BaseException, text: str) -> None:
        files = []
        tb = exc.__traceback__
        while tb is not None:
            files.append(tb.tb_frame.f_code.co_filename)
            tb = tb.tb_next
        is_provider = any(f in self._provider_files for f in files)
        rec = {"op": op, "error": f"{type(exc).__name__}: {snippet(str(exc))}",
               "input": snippet(text),
               "raised_from": Path(files[-1]).name if files else "?"}
        if is_provider:
            self.provider_crashes.append(rec)
        else:
            rec["traceback"] = "".join(traceback.format_exception(exc))[-2000:]
            self.internal_crashes.append(rec)  # unknown origin fails loud

    # -- H3/H4 + S2, per new edge ----------------------------------------------
    def check_edges(self, new_edges, turn) -> None:
        for e in new_edges:
            if not (e.subject.strip() and e.relation.strip() and e.object.strip()) \
                    or e.provenance.author_of_evidence != turn["author"]:
                self.malformed.append({"edge": f"{e.subject!r} {e.relation!r} {snippet(e.object)!r}",
                                       "author": e.provenance.author_of_evidence.value})
            if e.relation not in DEFAULT_RELATIONS:
                self.relation_drift[e.relation] = self.relation_drift.get(e.relation, 0) + 1
            if turn["author"].value == "third_party" and e.assertable and e.subject == "user":
                self.injection_leaks.append({"edge": f"{e.relation}: {snippet(e.object)}",
                                             "input": snippet(turn["text"])})

    # -- S1 ---------------------------------------------------------------------
    def yield_stat(self, turn, result: dict) -> None:
        self.turns += 1
        self.total_facts += result.get("facts", 0)
        self.total_quarantined += result.get("quarantined", 0)
        if len(turn["text"].strip()) >= 20:
            self.substantive += 1
            if not (result.get("facts") or result.get("quarantined")
                    or result.get("episode")):
                self.empty_substantive += 1

    # -- H2 ----------------------------------------------------------------------
    def check_isolation(self, store, user_ids) -> None:
        for uid in user_ids:
            for e in store.edges(uid, active_only=False, include_quarantined=True):
                if e.user_id != uid:
                    self.cross_user_leaks += 1
            for ep in store.episodes(uid):
                if ep.user_id != uid:
                    self.cross_user_leaks += 1

    # -- report --------------------------------------------------------------------
    def scorecard(self, manifest: dict) -> dict:
        hard = {"internal_crashes": len(self.internal_crashes),
                "cross_user_leaks": self.cross_user_leaks,
                "injection_leaks": len(self.injection_leaks),
                "malformed_edges": len(self.malformed)}
        return {
            "passed": not any(hard.values()),
            "hard": hard,
            "offenders": {"internal_crashes": self.internal_crashes[:_MAX_OFFENDERS],
                          "injection_leaks": self.injection_leaks[:_MAX_OFFENDERS],
                          "malformed_edges": self.malformed[:_MAX_OFFENDERS]},
            "soft": {
                "provider_crashes": {"n": len(self.provider_crashes),
                                     "examples": self.provider_crashes[:_MAX_OFFENDERS]},
                "yield": {"turns": self.turns, "substantive": self.substantive,
                          "empty_rate_substantive": round(
                              self.empty_substantive / self.substantive, 3)
                              if self.substantive else None,
                          "facts": self.total_facts,
                          "quarantined": self.total_quarantined},
                "relation_drift": self.relation_drift,
                "latency_ms": {op: _percentiles(v) for op, v in self.latency.items() if v},
            },
            "manifest": manifest,
        }
