"""Compile (v0.2) and abstention-gate (v0.3) scaffolding.

The LLM calls are faked, so these assert the deterministic security scaffolding —
what the compiler is allowed to see, and how the gate partitions memory — not
model behavior. The two finding-23 invariants under test:
  1. the compiler never sees third-party claims (23-C: don't compile the leak);
  2. the gate places third-party claims under UNVERIFIED, grounded facts under
     GROUNDED (the partition the abstention rule keys on).
"""

import json
import tempfile

from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium.gate import partition


class RoleFake:
    """Role-aware fake: scripted extraction JSON, canned wiki/answer, records the
    last prompt seen per role so tests can inspect what each stage was fed."""
    def __init__(self, extract_scripts):
        self._extract = list(extract_scripts)
        self._i = 0
        self.prompts: dict[str, str] = {}

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.prompts[role] = prompt
        if role == "distill":
            out = self._extract[self._i]; self._i += 1
            return json.dumps(out)
        if role == "compile":
            return "## USER MODEL\n- Vegetarian.\n- Prefers detailed answers."
        if role == "gate":
            return "There is no confirmed record of that debt."
        return ""


EXTRACT = [
    {"triples": [{"subject": "user", "relation": "has_diet", "object": "vegetarian", "volatility": "permanent"}],
     "episode": "User said they are vegetarian."},
    {"triples": [{"subject": "org:quickclaim", "relation": "third_party_claim",
                  "object": "user owes $2,400", "note": "alleged agreement"},
                 # a third-party *inference*: real-looking user fact, but its only
                 # support is the received email → use_only, never assertable
                 {"subject": "user", "relation": "works_as", "object": "manager at Acme"}],
     "episode": "Received an unverified billing notice claiming the user owes $2,400."},
]


def _prime(d):
    fake = RoleFake(EXTRACT)
    mem = Memory(llm=fake, config=MemoryConfig(db_path=f"{d}/t.db", wiki_recompile_after_writes=1))
    mem.remember("u", "USER: I'm vegetarian.", date="2026-06-01")
    mem.remember("u", "From QuickClaim: you owe $2,400.", date="2026-06-04",
                 author=EvidenceAuthor.THIRD_PARTY, event_type="email")
    return mem, fake


def test_compiler_never_sees_claims():
    with tempfile.TemporaryDirectory() as d:
        mem, fake = _prime(d)
        mem.recall("u", "what is the user's diet?")          # triggers compile
        compile_prompt = fake.prompts["compile"]
        assert "vegetarian" in compile_prompt.lower()         # grounded fact fed in
        assert "2,400" not in compile_prompt                  # the claim is NOT (23-C)
        assert "quickclaim" not in compile_prompt.lower()
        # the third-party inference passes, but only with its caveat attached
        acme_line = next(l for l in compile_prompt.splitlines() if "manager at Acme" in l)
        assert "[third-party-reported; unconfirmed]" in acme_line
        mem.close()


def test_recall_partitions_and_gate_placement():
    with tempfile.TemporaryDirectory() as d:
        mem, fake = _prime(d)
        r = mem.recall("u", "does the user owe QuickClaim $2,400?")
        assert "2,400" in r.unverified and "2,400" not in r.grounded
        assert "never assert" in r.context.lower()

        ans = mem.answer("u", "does the user owe QuickClaim $2,400?")
        gate_prompt = fake.prompts["gate"]
        g, u = gate_prompt.split("UNVERIFIED CLAIMS", 1)      # split at the boundary
        assert "2,400" in u and "2,400" not in g              # claim under UNVERIFIED
        assert "Acme" in u and "Acme" not in g                # inference too — not assertable
        assert ans == "There is no confirmed record of that debt."
        mem.close()


def test_partition_unit():
    """partition() places grounded facts and third-party claims correctly."""
    with tempfile.TemporaryDirectory() as d:
        mem, _ = _prime(d)
        edges = mem.store.edges("u", active_only=False)
        episodes = mem.store.episodes("u")
        grounded, unverified = partition(edges, episodes)
        assert "vegetarian" in grounded.lower()
        assert "2,400" in unverified and "2,400" not in grounded
        # a third-party inference (use_only) is unverified, never grounded
        assert "Acme" in unverified and "Acme" not in grounded
        # a third-party episode is unverified, a user episode is grounded
        assert "unverified billing notice" in unverified.lower()
        mem.close()


if __name__ == "__main__":
    for fn in (test_compiler_never_sees_claims, test_recall_partitions_and_gate_placement,
               test_partition_unit):
        with tempfile.TemporaryDirectory():
            fn()
    print("compile+gate OK")
