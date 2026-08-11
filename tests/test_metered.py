"""veracium.llm.metered — the opt-in host-side usage wrapper."""

from veracium.llm.metered import Metered


def _fake_complete(prompt, *, system=None, role="compile", json_schema=None):
    return f"answer-to:{prompt[:8]}"


def test_metered_passes_through_and_counts_per_role():
    m = Metered(_fake_complete)
    assert m("hello", role="distill").startswith("answer-to:")
    m("world", system="sys", role="distill")
    m("q", role="gate")
    t = m.totals()
    assert t["distill"]["calls"] == 2
    assert t["gate"]["calls"] == 1
    # no counter → character accounting, and NO fabricated token keys
    assert "in_chars" in t["distill"] and "in_tok" not in t["distill"]
    assert t["distill"]["in_chars"] == len("hello") + len("sys" + "world")


def test_metered_with_counter_records_tokens():
    m = Metered(_fake_complete, counter=lambda s: len(s.split()))
    m("two words", role="compile")
    t = m.totals()
    assert t["compile"]["in_tok"] == 2
    assert t["compile"]["out_tok"] >= 1
    assert "in_chars" not in t["compile"]


def test_totals_reset_is_explicit():
    m = Metered(_fake_complete)
    m("x")
    assert m.totals(reset=True)["compile"]["calls"] == 1
    assert m.totals() == {}


def test_metered_works_as_memory_llm_end_to_end(tmp_path):
    """The wrapper satisfies the Complete protocol through real ingest."""
    import json as _json
    from veracium import Memory, MemoryConfig, SqliteStore

    def extractor(prompt, *, system=None, role="compile", json_schema=None):
        if role == "distill":
            return _json.dumps({"triples": [{"subject": "user",
                                             "relation": "has_pet",
                                             "object": "cat Miso"}],
                                "episode": "user has a cat"})
        return "ok"

    m = Metered(extractor)
    db = str(tmp_path / "s.db")
    mem = Memory(llm=m, store=SqliteStore(db), config=MemoryConfig(db_path=db))
    r = mem.remember("u1", "USER: I have a cat named Miso.")
    assert r["facts"] == 1
    assert m.totals()["distill"]["calls"] >= 1
