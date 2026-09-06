"""0037 §6a — the acceptance corpus is bound to the spec by digest, in both
directions, data to data.

Round 2 of 0037's external review found the corpus "frozen" in prose while
absent from the package. This test is the binding:

  spec → corpus : the spec carries ONE column-0 line ``corpus sha256: <hex>``
                  and the file at the spec's stated path hashes to it.
  corpus → spec : the manifest records
                  ``spec_text_sha256_excluding_the_corpus_digest_line`` — the
                  sha256 of the spec text with EXACTLY the lines beginning at
                  column 0 with ``corpus sha256: `` removed (line + terminator,
                  nothing else), asserted to be exactly one such line. Binding
                  the digest into that line therefore does not move the pin;
                  any other edit to the spec does.

The exclusion rule is research's, recorded in the manifest with two reference
implementations (python: split on "\\n", assert one hit, drop it, join; shell:
``grep -c`` == 1 && ``grep -v``), verified to agree byte for byte. This test
mirrors the python form exactly. A regex with ``\\s*`` was rejected because
``\\s`` matches a newline and ate the blank line after the digest line — a pin
sensitive to spacing the spec never claimed was load-bearing.

Failure modes this refuses: the unbound placeholder token; a missing corpus
file; a corpus/spec digest mismatch; zero or two digest lines (the second
would appear at acceptance if the digest is copied into ``## Review closure``
as another column-0 line — the two reference impls diverge exactly there, so
the rule asserts one line and fails loudly instead); a manifest whose
recorded spec digest does not match the spec it claims to pin.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs" / "0037-procedural-basis.md"
CORPUS = ROOT / "tests" / "eval" / "procedural_describe" / "MANIFEST.json"
PREFIX = "corpus sha256: "
UNBOUND = "CORPUS-DIGEST-NOT-YET-BOUND"
SPEC_PIN_KEY = "spec_text_sha256_excluding_the_corpus_digest_line"


def _spec_lines() -> list[str]:
    return SPEC.read_text(encoding="utf-8").split("\n")


def _digest_lines() -> list[str]:
    return [l for l in _spec_lines() if l.startswith(PREFIX)]


def _spec_digest_token() -> str:
    hits = _digest_lines()
    assert len(hits) == 1, (
        f"the spec must carry exactly ONE column-0 `{PREFIX}` line, found {len(hits)}; "
        "a second one (e.g. copied into ## Review closure at acceptance) makes the two "
        "reference exclusion rules diverge, so this fails loudly instead")
    return hits[0][len(PREFIX):].strip()


def _spec_text_sha256_excluding_the_line() -> str:
    """Research's python reference form, mirrored exactly: split on "\\n",
    assert exactly one hit, drop it, join, sha256."""
    lines = _spec_lines()
    hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    assert len(hits) == 1
    kept = lines[: hits[0]] + lines[hits[0] + 1:]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def test_spec_names_a_bound_corpus_digest():
    token = _spec_digest_token()
    assert token != UNBOUND, (
        "the spec's corpus digest is the placeholder token: the corpus is not bound "
        "(§6a: a spec whose corpus is unbound cannot pass the suite)")
    assert len(token) == 64 and all(c in "0123456789abcdef" for c in token), f"not a sha256: {token!r}"


def test_corpus_file_hashes_to_the_spec_digest():
    token = _spec_digest_token()
    assert CORPUS.is_file(), f"{CORPUS.relative_to(ROOT)} is absent — the corpus is named but not in the tree"
    actual = hashlib.sha256(CORPUS.read_bytes()).hexdigest()
    assert actual == token, (
        f"corpus digest mismatch: file {actual[:16]}… vs spec {token[:16]}… — a corpus amendment "
        "and its spec line move together, in one commit")


def test_manifest_pins_this_spec_text_by_the_exclusion_rule():
    """The other direction: the manifest's recorded spec digest equals the sha256
    of THIS spec's text with exactly the one column-0 digest line removed."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    recorded = (manifest.get("spec_pin") or {}).get(SPEC_PIN_KEY)
    assert isinstance(recorded, str) and len(recorded) == 64, (
        f"manifest lacks a bound {SPEC_PIN_KEY} (found {recorded!r})")
    computed = _spec_text_sha256_excluding_the_line()
    assert computed == recorded, (
        f"the manifest pins a different spec text: recorded {recorded[:16]}… vs computed "
        f"{computed[:16]}… — an edit to the spec beyond the digest line needs research to re-pin")


def test_the_exclusion_rule_removes_exactly_the_line_and_nothing_else():
    """Negative controls on the rule itself: binding the digest line does not
    move the exclusion hash; eating the following blank line would."""
    lines = _spec_lines()
    i = [k for k, l in enumerate(lines) if l.startswith(PREFIX)][0]
    rebound = lines[:i] + [PREFIX + "0" * 64] + lines[i + 1:]
    kept_a = "\n".join(lines[:i] + lines[i + 1:])
    kept_b = "\n".join(rebound[:i] + rebound[i + 1:])
    assert kept_a == kept_b, "rebinding the digest line must not change the excluded text"
    # the rejected rule: also removing the blank line that follows (if any) changes the hash
    if i + 1 < len(lines) and lines[i + 1] == "":
        greedy = "\n".join(lines[:i] + lines[i + 2:])
        assert hashlib.sha256(greedy.encode()).hexdigest() != hashlib.sha256(kept_a.encode()).hexdigest()
    # the column-0 anchor: the prose mention of the line mid-sentence must not count
    assert sum(1 for l in lines if PREFIX in l) > sum(1 for l in lines if l.startswith(PREFIX)), (
        "the anchor's control expects the spec to mention the line in prose as well as carry it")
