"""0037 §6a — the acceptance corpus is bound to the spec by digest, in both
directions, data to data.

Round 2 of 0037's external review found the corpus "frozen" in prose while
absent from the package. This test is the binding:

  spec → corpus : the spec carries ONE column-0 line ``corpus sha256: <hex>``
                  and the file at the spec's stated path hashes to it.
  corpus → spec : the manifest records
                  ``spec_pin.spec_text_sha256_excluding_the_corpus_digest_line``
                  — the sha256 of the spec text with EXACTLY the lines beginning
                  at column 0 with ``corpus sha256: `` removed (line + terminator,
                  nothing else), asserted to be exactly one such line. Binding
                  the digest into that line therefore does not move the pin; any
                  other edit to the spec does.

WHICH rule binds is enforced by a GOLDEN VECTOR, not by self-consistency:
research's mutation test showed that installing the REJECTED greedy rule,
re-pinning the manifest to what it produces, and rebinding the line passed
every self-consistency check — a wrong rule pinned to itself is consistent.
The fixture below has an expected digest computed from the rule as written
(the line removed, the blank line after it KEPT), independent of the spec's
content, and it exercises the real function. The greedy rule (a regex whose
``\\s*`` crosses the line boundary and eats the following blank line) fails it.

The rule is research's, recorded in the manifest with two reference
implementations (python: split on "\\n", assert one hit, drop it, join; shell:
``grep -c '^corpus sha256: '`` == 1 && ``grep -v`` | sha256sum), verified to agree
byte for byte; this file mirrors the python form.

Failure modes this refuses: the unbound placeholder token; a missing corpus
file; a corpus/spec digest mismatch; zero or two digest lines (a second would
appear at acceptance if the digest is copied into ``## Review closure`` as
another column-0 line — the two reference forms diverge exactly there, so the
rule asserts one line and fails loudly instead); a manifest whose recorded spec
digest does not match the spec it claims to pin; and an implementation of the
exclusion rule that is not the bound one.
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

# The golden vector: expected digest computed from the rule AS WRITTEN, not from
# the implementation under test. The blank line after the digest line is KEPT.
GOLDEN_FIXTURE = "alpha\n" + PREFIX + "0" * 64 + "\n\nbeta\n"
GOLDEN_EXPECTED = hashlib.sha256("alpha\n\nbeta\n".encode("utf-8")).hexdigest()


def spec_text_sha256_excluding_the_line(text: str) -> str:
    """Research's python reference form, mirrored exactly: split on "\\n",
    assert exactly one column-0 hit, drop that line, join, sha256."""
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    assert len(hits) == 1, (
        f"exactly ONE column-0 `{PREFIX}` line is required, found {len(hits)}; a second one "
        "(e.g. copied into ## Review closure at acceptance) makes the two reference exclusion "
        "rules diverge, so this fails loudly instead")
    kept = lines[: hits[0]] + lines[hits[0] + 1:]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def _spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


def _spec_digest_token() -> str:
    hits = [l for l in _spec_text().split("\n") if l.startswith(PREFIX)]
    assert len(hits) == 1, f"the spec must carry exactly ONE column-0 `{PREFIX}` line, found {len(hits)}"
    return hits[0][len(PREFIX):].strip()


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
        f"manifest lacks a bound spec_pin.{SPEC_PIN_KEY} (found {recorded!r})")
    computed = spec_text_sha256_excluding_the_line(_spec_text())
    assert computed == recorded, (
        f"the manifest pins a different spec text: recorded {recorded[:16]}… vs computed "
        f"{computed[:16]}… — an edit to the spec beyond the digest line needs research to re-pin")


def test_the_exclusion_rule_is_the_bound_one_golden_vector():
    """WHICH rule: the real function on a fixture whose expected digest was
    computed from the rule as written. A self-consistent wrong rule (pinned to
    itself) passes every other test here; only this one names the rule."""
    assert spec_text_sha256_excluding_the_line(GOLDEN_FIXTURE) == GOLDEN_EXPECTED


def test_the_rejected_greedy_rule_fails_the_golden_vector():
    """Negative control on the golden vector, always run (never skipped): the
    rejected rule — remove the line AND the blank line after it — must NOT
    produce the expected digest, or the vector could not tell the rules apart."""
    greedy = hashlib.sha256("alpha\nbeta\n".encode("utf-8")).hexdigest()
    assert greedy != GOLDEN_EXPECTED
    # and the real function must not be that rule on any input with a following blank line
    assert spec_text_sha256_excluding_the_line(GOLDEN_FIXTURE) != greedy


def test_every_corpus_row_is_in_the_declared_domain():
    """Round 3, finding 1: the first corpus amendment wrote the STRING
    "declarative" into 486 cells, a value the proposed field
    `record_kind: Optional[Literal["procedural"]] = None` cannot hold, and the
    binding tests passed because they compare digests. This validates every row
    against the declared domain — today by value, at implementation by
    constructing a `Provenance` from the row — so a string-only generator fails
    here instead of in front of the reviewer. The four-state table is asserted
    on the same rows: an unstamped row with a basis is the named conflict, a
    stamped row without one is `basis_unknown`."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    cells = manifest.get("cells")
    assert isinstance(cells, list) and cells, "the manifest carries no cells"
    bad = []
    for i, cell in enumerate(cells):
        rk, basis = cell.get("record_kind"), cell.get("basis")
        if rk not in (None, "procedural"):
            bad.append((i, "record_kind", rk))
        if basis not in (None, "stated", "observed"):
            bad.append((i, "basis", basis))
    assert not bad, f"{len(bad)} corpus value(s) outside the declared field domain, e.g. {bad[:3]}"
    # the four-state table, on the rows that carry an expected outcome for the pair
    for cell in cells:
        rk, basis, expected = cell.get("record_kind"), cell.get("basis"), cell.get("kind_state")
        if expected is None:
            continue
        state = ("declarative" if rk is None and basis is None
                 else "procedural" if rk == "procedural" and basis is not None
                 else "basis_unknown" if rk == "procedural" and basis is None
                 else "kind_conflict")
        assert state == expected, f"cell {cell.get('id')}: rule says {state}, corpus says {expected}"


def test_the_column_zero_anchor_has_a_prose_mention_to_ignore():
    """The anchor's control: §6a mentions the line's form in prose mid-sentence;
    the anchored rule must count only the column-0 line. If someone tidies the
    prose mention away, the anchor becomes untested and this says so."""
    lines = _spec_text().split("\n")
    mentions = sum(1 for l in lines if PREFIX in l)
    anchored = sum(1 for l in lines if l.startswith(PREFIX))
    assert anchored == 1
    assert mentions > anchored, "the anchor's control expects a prose mention of the line that must not count"
