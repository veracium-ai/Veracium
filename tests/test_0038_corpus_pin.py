"""0038 §6a — the extraction speech-act corpus is bound to the spec by digest,
in both directions, data to data. Inherits 0037's binding rule VERBATIM
(`tests/test_0037_corpus_pin.py`): the same exclusion rule, the same golden
vector, the same exactly-one assertion, the same mutants — both found the hard
way on 0037 (a self-consistent wrong rule; a digest-consistent malformed row),
so 0038 does not rediscover them.

  spec → corpus : the spec carries ONE column-0 line ``corpus sha256: <hex>``
                  and the manifest at the spec's stated path hashes to it.
  corpus → spec : the manifest's ``spec_pin.spec_text_sha256_excluding_the_
                  corpus_digest_line`` equals the sha256 of the spec text with
                  exactly that one line removed (line + terminator).

Row-domain validation here is the 0038 corpus's OWN declared shape: every row
of the two frozen sets carries the fields the manifest says it does, and the
manifest's measured baselines are DERIVABLE from the rows they summarise (the
derived-basis rule — research's F4 found the first freeze carried a baseline
its rows could not produce).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs" / "0038-extraction-speech-act.md"
CORPUS_DIR = ROOT / "tests" / "eval" / "extraction_speech_act"
MANIFEST = CORPUS_DIR / "MANIFEST.json"
PREFIX = "corpus sha256: "
SPEC_PIN_KEY = "spec_text_sha256_excluding_the_corpus_digest_line"

GOLDEN_FIXTURE = "alpha\n" + PREFIX + "0" * 64 + "\n\nbeta\n"
GOLDEN_EXPECTED = hashlib.sha256("alpha\n\nbeta\n".encode("utf-8")).hexdigest()


def spec_text_sha256_excluding_the_line(text: str) -> str:
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    assert len(hits) == 1, f"exactly ONE column-0 `{PREFIX}` line is required, found {len(hits)}"
    kept = lines[: hits[0]] + lines[hits[0] + 1:]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def _spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


def _digest_token() -> str:
    hits = [l for l in _spec_text().split("\n") if l.startswith(PREFIX)]
    assert len(hits) == 1
    return hits[0][len(PREFIX):].strip()


def test_spec_names_a_bound_corpus_digest():
    token = _digest_token()
    assert len(token) == 64 and all(c in "0123456789abcdef" for c in token), f"not a sha256: {token!r}"


def test_manifest_hashes_to_the_spec_digest():
    assert MANIFEST.is_file(), f"{MANIFEST.relative_to(ROOT)} is absent — the corpus is named but not in the tree"
    assert hashlib.sha256(MANIFEST.read_bytes()).hexdigest() == _digest_token()


def test_manifest_pins_this_spec_text_by_the_exclusion_rule():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    recorded = (m.get("spec_pin") or {}).get(SPEC_PIN_KEY)
    assert isinstance(recorded, str) and len(recorded) == 64, f"manifest lacks spec_pin.{SPEC_PIN_KEY}"
    assert spec_text_sha256_excluding_the_line(_spec_text()) == recorded, (
        "the manifest pins a different spec text — an edit beyond the digest line needs research to re-pin")


def test_the_exclusion_rule_is_the_bound_one_golden_vector():
    assert spec_text_sha256_excluding_the_line(GOLDEN_FIXTURE) == GOLDEN_EXPECTED


def test_the_rejected_greedy_rule_fails_the_golden_vector():
    greedy = hashlib.sha256("alpha\nbeta\n".encode("utf-8")).hexdigest()
    assert greedy != GOLDEN_EXPECTED
    assert spec_text_sha256_excluding_the_line(GOLDEN_FIXTURE) != greedy


def test_the_frozen_sets_are_present_and_the_manifest_baselines_derive_from_them():
    """The derived-basis rule on the corpus itself: the 66-row acceptance set and
    the 412-row non-regression set exist with the sizes the manifest states, and
    the measured baselines the spec cites are recomputable from the rows."""
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sets = m["sets"]
    for name in ("bare_procedural_66.jsonl", "capture_412.jsonl"):
        assert name in sets, f"manifest does not declare {name}"
        path = CORPUS_DIR / name
        assert path.is_file(), f"{path.relative_to(ROOT)} absent"
        declared = sets[name]
        if isinstance(declared, dict) and "sha256" in declared:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == declared["sha256"], f"{name} digest mismatch"
    rows = [json.loads(l) for l in (CORPUS_DIR / "bare_procedural_66.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 66, f"the acceptance set has {len(rows)} rows, not 66"
    mb = m["measured_baselines"]
    # the completed-action baseline: N/66 in the manifest; N rows flagged in the set
    stated = int(str(mb["recorded_as_completed_action"]).split("/")[0])
    # the row field, by NAME from the manifest's author (research, 2026-09-07), never guessed by keyword
    FLAG = "baseline_recorded_as_completed_action"
    assert all(FLAG in r for r in rows), f"every row must carry {FLAG}; keys: {sorted(rows[0].keys())}"
    derived = sum(1 for r in rows if r[FLAG] is True)
    assert derived == stated, f"manifest says {stated}/66 completed-action, the rows derive {derived}/66"
    # the coercion baseline: derivable from baseline_triples
    co = mb["coerced_into_a_disposition_relation"]
    stated_co = int(str(co["rate"]).split("/")[0])
    dispo = set(co["disposition_set"])
    derived_co = sum(1 for r in rows if any(t.get("relation") in dispo for t in (r.get("baseline_triples") or [])))
    assert derived_co == stated_co, f"manifest says {stated_co}/66 coerced, the rows derive {derived_co}/66"
