"""Opt-in robustness tier (needs a live model; see tests/robustness/).

Skipped by default. To run against the committed fixture corpus:

    VERACIUM_ROBUSTNESS=1 pytest tests/test_robustness.py

Set VERACIUM_ROBUSTNESS_CORPUS=/path/to/lmsys.jsonl to run against a locally
exported lmsys-chat-1m (gated; never committed — see tests/robustness/adapter.py).
Uses the Anthropic reference provider (set ANTHROPIC_API_KEY) unless you wire
another via run() directly.
"""

import os
import tempfile

import pytest


@pytest.mark.skipif(not os.environ.get("VERACIUM_ROBUSTNESS"),
                    reason="set VERACIUM_ROBUSTNESS=1 to run the live robustness tier")
def test_robustness_invariants():
    from veracium import Memory, MemoryConfig
    from veracium.llm.anthropic import AnthropicComplete
    from tests.robustness.run_robustness import run
    from tests.robustness.adapter import FIXTURES

    def factory():
        d = tempfile.mkdtemp(prefix="veracium-robust-")
        return Memory(llm=AnthropicComplete(),
                      config=MemoryConfig(db_path=f"{d}/robust.db",
                                          wiki_recompile_after_writes=0))

    corpus = os.environ.get("VERACIUM_ROBUSTNESS_CORPUS", FIXTURES)
    card = run(factory, corpus, n=int(os.environ.get("VERACIUM_ROBUSTNESS_N", "50")))
    assert card["passed"], f"hard invariant violated: {card['hard']} / {card['offenders']}"
