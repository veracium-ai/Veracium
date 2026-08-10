"""Proactive recall (recall with no query): the session-start briefing.
The load-bearing invariant: proactive surfacing is VOLUNTEERING, so only
MENTIONABLE facts may appear — use_only and quarantined never surface."""

import json
import tempfile
from datetime import datetime, timezone

from veracium import EvidenceAuthor, Memory, MemoryConfig
from veracium import proactive


class Fake:
    def __init__(self, scripts):
        self._s = list(scripts); self._i = 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            out = self._s[self._i]; self._i += 1
            return json.dumps(out)
        return ""


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)

SCRIPTS = [
    {"triples": [{"subject": "user", "relation": "deadline",
                  "object": "tax filing due 2026-07-28", "volatility": "slow"}],
     "episode": "User mentioned the tax filing deadline of 2026-07-28."},
    # NB: distinct subject — 'deadline' is functional per (subject, relation),
    # so a second user-subject deadline would SUPERSEDE the first (pre-existing
    # registry semantics; hosts model parallel obligations with named subjects).
    {"triples": [{"subject": "task:passport", "relation": "deadline",
                  "object": "renew passport by 2026-07-01", "volatility": "slow"}],
     "episode": "User planned to renew the passport by 2026-07-01."},
    {"triples": [{"subject": "user", "relation": "health_state",
                  "object": "recovering from a sprained ankle", "volatility": "transient"}],
     "episode": "User sprained an ankle."},
    {"triples": [{"subject": "org:scamco", "relation": "third_party_claim",
                  "object": "user owes $900"},
                 {"subject": "user", "relation": "works_as", "object": "manager at Acme"}],
     "episode": "Received a notice claiming the user owes $900."},
]


def _mem(d):
    mem = Memory(llm=Fake(SCRIPTS),
                 config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=0))
    mem.remember("u", "tax deadline", date="2026-07-20")
    mem.remember("u", "passport", date="2026-06-20")
    mem.remember("u", "ankle", date="2026-07-22")
    mem.remember("u", "scam email", date="2026-07-23",
                 author=EvidenceAuthor.THIRD_PARTY, event_type="email")
    return mem


def test_briefing_sections_and_volunteering_gate():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        ctx, edges, eps, trunc = proactive.assemble(mem.store, "u", mem.config, now=NOW)

        # 1. dated commitments: upcoming flagged with due date, overdue marked
        assert "tax filing due 2026-07-28 (due 2026-07-28)" in ctx
        assert "OVERDUE — was due 2026-07-01" in ctx
        # 2. current transient state surfaces as follow-up material
        assert "sprained ankle" in ctx and "worth a follow-up" in ctx
        # 3. recent grounded history, but not the third-party episode
        assert "tax filing deadline" in ctx
        assert "claiming the user owes" not in ctx

        # THE GATE: nothing non-mentionable is ever volunteered
        assert "$900" not in ctx                       # quarantined claim silent
        assert "Acme" not in ctx                       # use_only inference silent
        assert all(e.assertable for e in edges)
        mem.close()


def test_recall_none_wires_proactive_and_respects_budget():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        import veracium.proactive as p
        real = p.assemble
        p.assemble = lambda store, uid, cfg, **kw: real(store, uid, cfg, now=NOW, **{k: v for k, v in kw.items() if k != "now"})
        try:
            r = mem.recall("u")                        # no query -> briefing
            assert "DATED COMMITMENTS" in r.context
            assert r.unverified == ""                  # never volunteered
            assert r.grounded == r.context

            # specs/0012 I10e: sub-floor budgets now raise; the priority intent
            # (commitments outrank history) exercises at a just-above-floor budget
            # with padded history that cannot fit.
            from datetime import datetime, timezone as _tz
            from veracium.schema import (Episode as _Ep, EvidenceAuthor as _A,
                                         Provenance as _P, SourceType as _S)
            for i in range(12):
                mem.store.add_episode(_Ep(
                    id=f"pad-ep{i}", user_id="u", date=NOW.date().isoformat(),
                    summary=f"an intentionally verbose recent-history line {i} that "
                            f"occupies a meaningful share of a tight token budget",
                    provenance=_P(source_type=_S.STATED, author_of_evidence=_A.USER,
                                  evidence_ref=f"pad-{i}",
                                  observed_at=datetime.now(_tz.utc))))
            import pytest as _pytest
            with _pytest.raises(ValueError, match="below its floor"):
                mem.recall("u", token_budget=30)
            from veracium.budgets import floor_for as _ff
            tight = mem.recall("u", token_budget=_ff("proactive") + 5)  # just above the floor
            assert tight.truncated
            assert "OVERDUE" in tight.context or "due 2026-07-28" in tight.context
            assert tight.context.count("verbose recent-history line") < 12
        finally:
            p.assemble = real
        mem.close()


def test_needs_confirmation_surfaces_and_empty_store_is_calm():
    with tempfile.TemporaryDirectory() as d:
        mem = _mem(d)
        edge = next(e for e in mem.store.edges("u") if "ankle" in e.object)
        edge.volatility = type(edge.volatility)("durable")
        edge.needs_confirmation = True
        mem.store.add_edge(edge)
        ctx, *_ = proactive.assemble(mem.store, "u", mem.config, now=NOW)
        assert "confirm when natural" in ctx

        ctx2, edges2, eps2, tr2 = proactive.assemble(mem.store, "nobody", mem.config, now=NOW)
        assert ctx2 == "(nothing needs attention)" and not edges2 and not tr2
        mem.close()
