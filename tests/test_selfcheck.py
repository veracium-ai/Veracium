"""Self-check runner: end-to-end on a deterministic provider, and its content-free
telemetry wiring."""

import json

import pytest

from veracium import Memory, MemoryConfig
from veracium import selfcheck, telemetry as T


class Provider:
    """A cooperative, deterministic Complete: extracts the expected triples and
    answers the gate the way a correct model would. Lets us exercise the runner's
    scoring offline without a live model."""

    def __call__(self, prompt, *, system=None, role="", json_schema=None):
        low = prompt.lower()
        if role == "distill":
            return json.dumps(self._extract(low))
        if role == "compile":
            return "Working memory: employment and pet on file."
        # gate — branch on the question line, not the boilerplate
        q = low.split("question:", 1)[-1]
        if "car" in q:
            return "I don't know — there's no record of a car."
        if "owe" in q:
            return ("I have no confirmed record of any debt. There was an unverified "
                    "third-party claim, which was never confirmed.")
        if "work" in q:
            return "You currently work at Globex."
        return "I don't know."

    def _extract(self, low):
        if "globex" in low:
            return {"triples": [{"subject": "user", "relation": "works_as",
                                 "object": "Globex", "volatility": "slow"}],
                    "episode": "changed jobs to Globex"}
        if "acme" in low:
            return {"triples": [{"subject": "user", "relation": "works_as",
                                 "object": "Acme Corp", "volatility": "slow"}],
                    "episode": "works as an analyst at Acme Corp"}
        if "owe" in low or "4,200" in low:
            return {"triples": [{"subject": "person:sender", "relation": "third_party_claim",
                                 "object": "claims the user owes $4,200", "volatility": "transient"}],
                    "episode": "received a payment-demand email"}
        if "cat" in low:
            return {"triples": [{"subject": "user", "relation": "has_pet",
                                 "object": "cat named Mittens", "volatility": "durable"}],
                    "episode": "has a cat named Mittens"}
        return {"triples": [], "episode": "introduced themselves"}


def test_abstention_detector_accepts_natural_phrasings():
    # The gate abstains in its own words; the detector must recognize the common
    # shapes, not just "I don't know". (A live run abstained with "I don't have
    # any confirmed record of ..." and was scored 0 — this pins the fix.)
    abstained = [
        "I don't know.",
        "I don't have any confirmed record of your favorite color in memory.",
        "There's no record of you owning or driving a car.",
        "There is no verified information about that.",
        "Nothing in grounded memory supports an answer.",
        "That isn't any confirmed knowledge I hold.",
        "I can't verify that from memory.",
    ]
    answered = [
        "You drive a blue Honda Civic.",
        "Your favorite color is green (since 2026-05-02).",
        "You currently work at Globex.",
    ]
    for s in abstained:
        assert selfcheck._ABSTAINED.search(s), f"should count as abstention: {s!r}"
    for s in answered:
        assert not selfcheck._ABSTAINED.search(s), f"should NOT count as abstention: {s!r}"


def test_run_scores_all_three_checks_on_a_correct_provider():
    r = selfcheck.run(Provider())
    assert r["total_n"] == 4
    assert r["supersession_ok"] == 2          # current value + retained history
    assert r["injection_asserts"] == 0        # the scam never asserted
    assert r["abstention_ok"] == 1            # unknown → declined
    assert r["total_ok"] == 4 and r["passed"] is True
    assert r["errors"] == []


def test_result_is_content_free_through_the_collector():
    # A collector only keeps the whitelisted scalar keys; detail/errors/strings drop.
    r = selfcheck.run(Provider())
    c = T.Collector()
    c.record("selfcheck", r)
    snap = c.snapshot()["events"]["selfcheck"]["sums"]
    assert snap["total_ok"] == 4.0 and snap["total_n"] == 4.0
    assert snap["injection_asserts"] == 0.0
    flat = json.dumps(c.snapshot())
    for leak in ("Globex", "Acme", "4,200", "Mittens", "detail", "passed", "errors"):
        assert leak not in flat


def test_memory_self_check_emits_selfcheck_event(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    coll = T.Collector()
    mem = Memory(llm=Provider(), telemetry=coll,
                 config=MemoryConfig(db_path=str(tmp_path / "unused.db")))
    result = mem.self_check()
    mem.close()
    assert result["total_n"] == 4
    snap = coll.snapshot()["events"]["selfcheck"]["sums"]
    assert snap["total_n"] == 4.0
    # the caller's own store was never used by the check
    assert "detail" not in json.dumps(coll.snapshot())


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
