"""specs/0029 §6a / specs/0030 §6a — the shared acceptance corpus, run on
every CI run BY CONSTRUCTION (0029 §7: "a write-only log can rot unread; §6a's
gate reads it on every CI run"). A CORRECTNESS gate, 100%, deterministic, no
model. Research froze the expectations (MANIFEST.json, amendment 1 digest
pinned in the runner); dev owns the runner. Both halves are here: the digest
of the frozen text, and every scenario's checks."""
from __future__ import annotations

import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def _runner():
    spec = importlib.util.spec_from_file_location("corpus_runner_0029", HERE / "corpus_runner.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_acceptance_corpus_manifest_is_the_frozen_text():
    """The manifest on disk is byte-identical to the frozen (amended) text —
    an expectation cannot move without the digest saying so."""
    r = _runner()
    assert r.manifest_ok(), "MANIFEST.json does not match the pinned digest"
    m = r.load_manifest()
    assert [s["id"] for s in m["scenarios"]] == sorted(r.SCENARIOS), "the runner covers every scenario, no more"
    assert m["OPEN_QUESTIONS_FOR_DEV"] == [], "an OPEN question means the bar is not set"


def test_acceptance_corpus_passes_100_percent():
    """Pass criterion (1): every scenario's event sequence AND every named
    reconstruction equal the expected values; (2)–(4) are scenario checks
    S01, S05 and the V-ATOMIC test in tests/test_0029_carrier.py."""
    out = _runner().run_all()
    failed = {sid: [n for n, ok in r["checks"].items() if not ok]
              for group in ("scenarios", "retained")
              for sid, r in out[group].items() if not r["pass"]}
    assert not failed, failed
    # criterion (5): the nine retained scenarios are SCORED, not merely present —
    # the runner's coverage equals the manifest's list, or the gate fails here
    assert out["retained_all_scored"], "a retained scenario is listed but not scored"
    assert out["pass"]
