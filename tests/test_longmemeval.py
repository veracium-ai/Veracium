"""LongMemEval adapter tests — the leak firewall, loader invariants, cache
identity, and serialization. Runs offline on synthetic fixtures: no dataset,
no provider. (The real corpus lives outside the repo; see
tests/longmemeval/adapter.py.)
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "longmemeval"))

from adapter import (LoaderError, Turn, load, stratified_pilot,  # noqa: E402
                     to_iso)
from cache import CacheLock, CachedComplete, SCHEMA_VERSION  # noqa: E402
from run_longmemeval import (CONTEXT_POLICY, author_for, isolated,  # noqa: E402
                             question_with_date, serialize)

from veracium.schema import EvidenceAuthor  # noqa: E402

ORACLE_MARKERS = ("has_answer", "answer_session_ids", "question_type",
                  "GOLDANSWERLEAK", "single-session-user")


def _instance(qid="q1", qtype="single-session-user", n_sessions=2, when=("2023/05/20 (Sat) 02:21",
                                                                        "2023/05/21 (Sun) 09:00")):
    """A benchmark-shaped instance with conspicuous oracle annotations."""
    sessions = []
    for s in range(n_sessions):
        sessions.append([
            {"role": "user", "content": f"session {s} user turn"},
            {"role": "assistant", "content": f"session {s} assistant turn",
             "has_answer": True},
        ])
    return {
        "question_id": qid, "question_type": qtype,
        "question": "what did I say?", "answer": "GOLDANSWERLEAK",
        "question_date": "2023/05/30 (Tue) 23:40",
        "haystack_session_ids": [f"s{i}" for i in range(n_sessions)],
        "haystack_dates": list(when[:n_sessions]),
        "haystack_sessions": sessions,
        "answer_session_ids": ["s1"],
    }


def _write(instances) -> str:
    d = tempfile.mkdtemp(prefix="lme-")
    p = Path(d) / "data.json"
    p.write_text(json.dumps(instances))
    return str(p)


# -- the firewall (spec §2) ---------------------------------------------------

def test_model_facing_structure_carries_no_oracle_annotation():
    items, evals, _ = load(_write([_instance()]))
    blob = json.dumps([[[t.role, t.content, t.index] for t in s.turns]
                       for s in items[0].sessions] + [items[0].question,
                                                      items[0].question_date])
    for marker in ORACLE_MARKERS:
        assert marker not in blob, f"{marker!r} reached the model-facing structure"
    # the eval half still has everything the report needs
    ev = evals["q1"]
    assert ev.answer == "GOLDANSWERLEAK"
    assert ev.evidence_turns == (("s0", 1), ("s1", 1))
    assert ev.answer_session_ids == ("s1",)
    assert ev.question_type == "single-session-user"


def test_serialized_event_text_never_leaks_oracle_fields():
    """Whatever reaches the extractor is built only from role/content."""
    items, _, _ = load(_write([_instance()]))
    session = items[0].sessions[0]
    for i in range(len(session.turns)):
        for text in (serialize(session, i, window=CONTEXT_POLICY["window_turns"]),
                     isolated(session, i)):
            for marker in ORACLE_MARKERS:
                assert marker not in text
    # nor into the answer prompt
    prompt = question_with_date(items[0])
    assert "GOLDANSWERLEAK" not in prompt and "has_answer" not in prompt
    assert items[0].question_date in prompt  # official convention: date is shown


def test_turn_type_cannot_carry_annotations():
    """Turn is frozen with exactly three fields — a leak is a TypeError."""
    with pytest.raises(TypeError):
        Turn(role="user", content="x", index=0, has_answer=True)


# -- loader invariants (spec §5, §10) -----------------------------------------

def test_sessions_are_date_sorted_official_order():
    inst = _instance(when=("2023/05/25 (Thu) 10:00", "2023/05/21 (Sun) 09:00"))
    items, _, _ = load(_write([inst]))
    stamps = [s.stamp for s in items[0].sessions]
    assert stamps == sorted(stamps)
    assert items[0].sessions[0].session_id == "s1"  # later date moved after


def test_session_after_question_date_is_rejected():
    inst = _instance(when=("2023/06/30 (Fri) 10:00", "2023/05/21 (Sun) 09:00"))
    with pytest.raises(LoaderError, match="dated after the question"):
        load(_write([inst]))


def test_misaligned_haystack_rejected_but_repeated_ids_are_kept():
    bad = _instance()
    bad["haystack_dates"] = bad["haystack_dates"][:1]
    with pytest.raises(LoaderError, match="misaligned"):
        load(_write([bad]))

    # a repeated session id is real benchmark data (13/500): keep both dated
    # occurrences, disambiguated, and surface the quirk in the manifest
    dup = _instance()
    dup["haystack_session_ids"] = ["s0", "s0"]
    items, _, manifest = load(_write([dup]))
    assert len(items[0].sessions) == 2
    assert [s.ref for s in items[0].sessions] == ["s0", "s0~1"]
    assert items[0].repeated_session_ids == ("s0",)
    assert manifest["instances_with_repeated_session_ids"] == 1


def test_non_strict_mode_collects_rejections_instead_of_aborting():
    bad = _instance(qid="bad")
    bad["haystack_dates"] = []
    bad["haystack_sessions"] = []
    bad["haystack_session_ids"] = []
    items, _, manifest = load(_write([_instance(qid="ok"), bad]), strict=False)
    # empty haystack aligns (0==0==0) so it loads; use a genuinely broken one
    assert manifest["instances"] + manifest["rejected"] == 2


def test_timestamp_parsing():
    assert to_iso("2023/05/20 (Sat) 02:21") == "2023-05-20T02:21:00"
    with pytest.raises(ValueError):
        to_iso("May 20, 2023")


def test_stratified_pilot_guarantees_minimums():
    instances = []
    for t in ("single-session-user", "single-session-assistant",
              "single-session-preference", "temporal-reasoning",
              "knowledge-update", "multi-session"):
        for k in range(8):
            instances.append(_instance(qid=f"{t}-{k}", qtype=t))
    for k in range(10):  # abstention items
        instances.append(_instance(qid=f"abs-{k}_abs", qtype="multi-session"))
    items, evals, _ = load(_write(instances))
    picked = stratified_pilot(items, evals, per_type=6, min_abs=8, seed=0)
    by_type = {}
    n_abs = 0
    for it in picked:
        ev = evals[it.question_id]
        if ev.is_abstention:
            n_abs += 1
        else:
            by_type[ev.question_type] = by_type.get(ev.question_type, 0) + 1
    assert n_abs >= 8
    assert all(c >= 6 for c in by_type.values()), by_type
    assert len(by_type) == 6


# -- ingestion shape ----------------------------------------------------------

def test_context_window_marks_context_and_current_turn():
    items, _, _ = load(_write([_instance()]))
    session = items[0].sessions[0]
    text = serialize(session, 1, window=4)
    assert "[CONTEXT" in text and "[CURRENT TURN" in text
    # the current turn appears after the current-turn marker, context before it
    head, tail = text.split("[CURRENT TURN", 1)
    assert "session 0 user turn" in head       # prior turn = context
    assert "session 0 assistant turn" in tail  # current turn = evidence
    assert isolated(session, 1) == "assistant: session 0 assistant turn"


def test_trust_arms_map_authorship():
    assert author_for("user", "C") == (EvidenceAuthor.USER, None, "chat")
    a, d, et = author_for("assistant", "T")
    assert (a, d, et) == (EvidenceAuthor.SYSTEM, None, "assistant_chat")
    a, d, et = author_for("assistant", "C")
    assert (a, d) == (EvidenceAuthor.SYSTEM, EvidenceAuthor.THIRD_PARTY)
    assert et == "assistant_chat"


# -- cache identity + durability (spec §4, §11) ------------------------------

class _Counting:
    def __init__(self, out="{}"):
        self.out, self.calls = out, 0

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.calls += 1
        return self.out


def _cache(tmp, inner, **identity_overrides):
    identity = {"extractor_model": "fake", "extract_prompt_sha": "abc",
                "serializer_version": 2, "parser_version": 1, "schema": "triples-v1"}
    identity.update(identity_overrides)
    return CachedComplete(inner, path=Path(tmp) / "c.jsonl", identity=identity)


def test_cache_hit_serves_stored_extraction_once():
    with tempfile.TemporaryDirectory() as tmp:
        inner = _Counting('{"triples": []}')
        c = _cache(tmp, inner)
        k = c.key_for("turn text", author="user", event_type="chat", date="2023-05-20T02:21:00")
        c.bind(k)
        assert c("p", role="distill") == '{"triples": []}'
        c.bind(k)
        c("p", role="distill")
        assert inner.calls == 1 and c.stats == {"hits": 1, "misses": 1, "writes": 1,
                                               "incompatible": 0}
        # non-distill roles are never cached
        c.bind(k)
        c("p", role="gate")
        assert inner.calls == 2


def test_cache_key_changes_with_every_identity_component():
    with tempfile.TemporaryDirectory() as tmp:
        base = _cache(tmp, _Counting())
        k = base.key_for("t", author="user", event_type="chat", date="d")
        assert base.key_for("t2", author="user", event_type="chat", date="d") != k
        assert base.key_for("t", author="system", event_type="chat", date="d") != k
        assert base.key_for("t", author="user", event_type="email", date="d") != k
        assert base.key_for("t", author="user", event_type="chat", date="d2") != k
        for field, value in (("extract_prompt_sha", "zzz"), ("serializer_version", 99),
                             ("parser_version", 2), ("schema", "triples-v2"),
                             ("extractor_model", "other")):
            other = _cache(tmp, _Counting(), **{field: value})
            assert other.key_for("t", author="user", event_type="chat", date="d") != k, field


def test_cache_survives_partial_line_and_rejects_old_schema():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "c.jsonl"
        good = {"schema": SCHEMA_VERSION, "key": "k1", "value": "v1"}
        old = {"schema": SCHEMA_VERSION - 1, "key": "k2", "value": "stale"}
        path.write_text(json.dumps(good) + "\n" + json.dumps(old) + "\n"
                        + '{"schema": 1, "key": "k3", "val')  # truncated tail
        identity = {"extractor_model": "fake"}
        c = CachedComplete(_Counting(), path=path, identity=identity)
        assert c.unique_keys == 1              # only the good entry loaded
        assert c.stats["incompatible"] == 1    # old-schema entry rejected, not replayed


def test_cache_lock_excludes_a_second_run():
    with tempfile.TemporaryDirectory() as tmp:
        lock = Path(tmp) / "lock"
        with CacheLock(lock):
            assert lock.exists()
            with pytest.raises(RuntimeError, match="locked"):
                with CacheLock(lock):
                    pass
        assert not lock.exists()


def test_same_day_later_clock_time_is_history_not_a_violation():
    """Benchmark semantics are day-level: 1475 sessions in the real S file sit
    on the question's own day at a later clock time. Those are history; only a
    later DAY is a structural violation."""
    inst = _instance(when=("2023/05/30 (Tue) 23:59", "2023/05/21 (Sun) 09:00"))
    items, _, manifest = load(_write([inst]))   # question_date is 05/30 23:40
    assert len(items[0].sessions) == 2
    assert items[0].same_day_later_sessions == 1
    assert manifest["same_day_later_sessions"] == 1


def test_stale_lock_from_a_dead_run_is_cleared():
    """A killed run never runs __exit__. The next run must distinguish a dead
    holder (clear it) from a live one (refuse) rather than making the operator
    guess."""
    with tempfile.TemporaryDirectory() as tmp:
        lock = Path(tmp) / "lock"
        lock.write_text("999999")          # a pid that cannot be running
        with CacheLock(lock):
            assert lock.read_text().strip() == str(__import__("os").getpid())
        assert not lock.exists()

        lock.write_text(str(__import__("os").getpid()))   # a live holder: refuse
        with pytest.raises(RuntimeError, match="LIVE run"):
            with CacheLock(lock):
                pass


# -- provider rate limiting ---------------------------------------------------

def _bare_provider(limits):
    """A MeteredOpenAI with only its pacing state — no client, no API key."""
    import collections
    import threading
    from providers import MeteredOpenAI
    p = MeteredOpenAI.__new__(MeteredOpenAI)
    p._limits = dict(limits)
    p._windows = {}
    p._in_window = {}
    p._pace_lock = threading.Lock()
    p._pace_waits = 0
    return p


def test_token_bucket_admits_by_estimated_tokens_not_call_count():
    """Average-cadence pacing let a burst of long turns punch through the TPM
    limit (a 3.2k-token call 429ing while the cadence thought it was fine).
    Admission is by estimated tokens against a trailing-60s budget."""
    import threading
    p = _bare_provider({"m": 10_000})                 # budget = 8500 at 0.85

    p._pace("m", 8_000)
    assert p._in_window["m"] == 8_000

    t = threading.Thread(target=p._pace, args=("m", 8_000), daemon=True)
    t.start()
    t.join(timeout=1.0)
    assert t.is_alive(), "second oversized call should be waiting on the budget"
    assert p._pace_waits > 0

    before = p._in_window["m"]
    p._penalize("m", 1_000)      # a 429 charges the window with nothing served
    assert p._in_window["m"] == before + 1_000


def test_budgets_are_per_model():
    """Measured limits differ ~7x (extractor 200k vs answer model 30k), so one
    shared pool would 429 the tight model while the wide one looks fine."""
    import threading
    p = _bare_provider({"wide": 200_000, "tight": 30_000})
    p._pace("tight", 25_000)                  # 25k of a 25.5k budget
    t = threading.Thread(target=p._pace, args=("tight", 5_000), daemon=True)
    t.start()
    t.join(timeout=0.5)
    assert t.is_alive(), "tight model should be throttled"
    # the wide model is unaffected by the tight model's saturation
    p._pace("wide", 100_000)
    assert p._in_window["wide"] == 100_000


def test_provider_reported_limit_is_adopted():
    """A tier change should need no code edit: the next response's
    x-ratelimit-limit-tokens header widens (or narrows) the budget."""
    p = _bare_provider({"m": 30_000})
    p._learn_limit("m", {"x-ratelimit-limit-tokens": "2000000"})
    assert p._limits["m"] == 2_000_000
    p._learn_limit("m", {})                       # missing header: keep current
    assert p._limits["m"] == 2_000_000
    p._learn_limit("m", {"x-ratelimit-limit-tokens": "nonsense"})
    assert p._limits["m"] == 2_000_000


def test_cache_identity_ignores_throughput_state():
    """Regression: rate-limit state leaked into `decoding`, which feeds the
    cache identity — so every pacing tweak silently invalidated the whole
    cache and re-paid for thousands of extractions. Sampling params belong in
    the identity; throughput never does."""
    from providers import MeteredOpenAI
    p = MeteredOpenAI.__new__(MeteredOpenAI)
    import collections, threading
    p.temperature, p.max_tokens = 0.0, 4096
    p._limits, p._windows, p._in_window = {"m": 200_000}, {}, {}
    p._pace_lock, p._pace_waits, p.rate_limited = threading.Lock(), 0, 0

    before = dict(p.decoding)
    p._learn_limit("m", {"x-ratelimit-limit-tokens": "2000000"})  # tier change
    p._pace_waits += 17                                          # throughput churn
    assert p.decoding == before, "throughput state must not reach the identity"
    assert "tpm_limits" in p.throughput      # still reported, just not in the key


def test_cache_records_key_parts_for_migration():
    """Entries carry their key components so a future benign identity change can
    be re-keyed instead of re-extracted."""
    with tempfile.TemporaryDirectory() as tmp:
        c = _cache(tmp, _Counting('{"triples": []}'))
        kw = dict(author="user", event_type="chat", date="2023-05-20")
        c.bind(c.key_for("some turn", **kw), c.parts_for("some turn", **kw))
        c("p", role="distill")
        rec = json.loads(Path(tmp, "c.jsonl").read_text().splitlines()[0])
        assert set(rec["parts"]) == {"text_sha", "author", "event_type", "date",
                                     "identity"}
        assert rec["parts"]["date"] == "2023-05-20"


def test_quota_exhaustion_is_terminal_not_retried():
    """The SDK reports insufficient_quota as a RateLimitError. Retrying it burns
    every worker's retry budget and turns one billing problem into a full set of
    empty hypotheses that looks like a completed run."""
    from providers import MeteredOpenAI, QuotaExhausted
    import collections, threading

    calls = []

    class _Raw:
        def create(self, **kw):
            calls.append(kw)
            raise RuntimeError("Error code: 429 - {'error': {'message': 'You "
                               "exceeded your current quota', 'type': "
                               "'insufficient_quota'}}")

    class _Completions:
        with_raw_response = _Raw()

    p = MeteredOpenAI.__new__(MeteredOpenAI)
    p.models = {"distill": "m", "compile": "m", "gate": "m"}
    p.max_retries, p.max_tokens, p.temperature = 8, 16, 0.0
    p._limits, p._windows, p._in_window = {"m": 200_000}, {}, {}
    p._pace_lock, p._pace_waits = threading.Lock(), 0
    p._lock, p.usage, p.retries, p.failures, p.rate_limited = (
        threading.Lock(), {}, 0, 0, 0)
    p.error_classes = {}
    p._client = type("C", (), {"chat": type("H", (), {"completions": _Completions()})()})()

    with pytest.raises(QuotaExhausted, match="quota exhausted"):
        p("prompt", role="distill")
    assert len(calls) == 1, "must not retry a terminal quota failure"


# -- variance protocol --------------------------------------------------------

def test_variance_aggregation_detects_extractor_noise():
    """Three realizations that differ in extraction and answers must show
    imperfect agreement and a nonzero official-score range; identical ones must
    show perfect agreement. This is the number that says how much of a score is
    extractor noise rather than memory quality."""
    from variance import aggregate
    with tempfile.TemporaryDirectory() as tmp:
        def write(name, rows):
            p = Path(tmp) / name
            p.write_text("\n".join(json.dumps(r) for r in rows))
            return p

        # q1 identical everywhere; q2 differs in both extraction and label
        r1 = write("r1.jsonl", [
            {"question_id": "q1", "hypothesis": "blue", "edge_sig": ["aa", "bb"],
             "autoeval_label": {"label": True}},
            {"question_id": "q2", "hypothesis": "cats", "edge_sig": ["cc", "dd"],
             "autoeval_label": {"label": True}}])
        r2 = write("r2.jsonl", [
            {"question_id": "q1", "hypothesis": "blue", "edge_sig": ["aa", "bb"],
             "autoeval_label": {"label": True}},
            {"question_id": "q2", "hypothesis": "dogs", "edge_sig": ["cc", "ee"],
             "autoeval_label": {"label": False}}])
        r3 = write("r3.jsonl", [
            {"question_id": "q1", "hypothesis": "blue", "edge_sig": ["aa", "bb"],
             "autoeval_label": {"label": True}},
            {"question_id": "q2", "hypothesis": "dogs", "edge_sig": ["cc", "ee"],
             "autoeval_label": {"label": False}}])

        out = aggregate([r1, r2, r3])
        assert out["realizations"] == 3 and out["questions"] == 2
        assert out["per_question"]["q1"]["edge_jaccard"] == 1.0
        assert out["per_question"]["q1"]["answers_identical"] is True
        assert out["per_question"]["q2"]["edge_jaccard"] < 1.0
        assert out["per_question"]["q2"]["judged_agree"] is False
        assert out["questions_flipping_label"] == ["q2"]
        assert out["official_scores"] == [1.0, 0.5, 0.5]
        assert out["official_score_range"] == 0.5
        assert out["identical_answer_rate"] == 0.5


def test_spend_is_ledgered_during_the_run_not_only_at_the_end():
    """Cost used to be written only into a completed run's record, so every
    killed run spent real money that appeared in no report — under-reporting
    actual spend by ~2x. Usage must reach the ledger while the run is alive."""
    from providers import MeteredOpenAI
    import collections, threading

    with tempfile.TemporaryDirectory() as tmp:
        ledger = Path(tmp) / "spend.jsonl"
        p = MeteredOpenAI.__new__(MeteredOpenAI)
        p._lock, p.usage = threading.Lock(), {}
        p._ledger, p._label, p._calls_since_flush = ledger, "unit-test", 0
        p.rate_limited, p._pace_waits = 0, 0

        class _U:
            prompt_tokens, completion_tokens = 1_000_000, 500_000
        p._meter("distill", "gpt-4.1-mini-2025-04-14", type("R", (), {"usage": _U})())

        p.flush_spend("mid-run")          # what a killed run would still leave
        rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
        assert rows and rows[-1]["reason"] == "mid-run"
        assert rows[-1]["label"] == "unit-test"
        # 1M in @ $0.40 + 0.5M out @ $1.60 = $1.20
        assert abs(rows[-1]["usd"] - 1.20) < 0.01


# -- extraction-strictness experiment ----------------------------------------

def test_strictness_bar_filters_only_distill_output():
    """The over-extraction test filters cached extraction output so strictness
    is a replay, not a re-extraction. It must drop off-registry relations and
    essay-length objects — and leave compile/gate calls completely alone."""
    from strictness import StrictExtraction

    payload = json.dumps({"triples": [
        {"subject": "user", "relation": "has_pet", "object": "cat Miso"},
        {"subject": "user", "relation": "includes", "object": "invented relation"},
        {"subject": "user", "relation": "prefers", "object": "x" * 200},
    ], "episode": "e"})

    class Inner:
        stats = {"hits": 0, "misses": 0}
        def __call__(self, p, *, system=None, role="compile", json_schema=None):
            return payload

    kept = lambda bar, role="distill": json.loads(
        StrictExtraction(Inner(), bar=bar)(  "p", role=role))["triples"]
    assert len(kept("none")) == 3
    assert [t["relation"] for t in kept("registry")] == ["has_pet", "prefers"]
    assert [t["relation"] for t in kept("registry+len")] == ["has_pet"]
    # curation must never touch the answer path
    assert len(kept("registry+len", role="gate")) == 3


def test_strictness_bar_survives_unparseable_output():
    """Extraction sometimes returns junk; that is veracium's tolerant-parser
    problem, and the experiment must not convert it into a crash."""
    from strictness import StrictExtraction

    class Junk:
        stats = {"hits": 0, "misses": 0}
        def __call__(self, p, *, system=None, role="compile", json_schema=None):
            return "not json at all"

    assert StrictExtraction(Junk(), bar="registry")("p", role="distill") == "not json at all"
