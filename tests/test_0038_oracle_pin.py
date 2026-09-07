"""0038 §6b — the oracle evidence is bound to the spec by ONE digest, data to data, in
the corpus pin's shape (`tests/test_0038_corpus_pin.py`): the manifest is the single pin
and every byte digest lives in the manifest, so a fifteen-file evidence set puts one
token into prose rather than fifteen that would go stale independently.

  spec → manifest   the spec carries ONE column-0 line ``oracle manifest sha256: <hex>``
                    and ``oracle/MANIFEST.json`` hashes to it.
  manifest → spec   the manifest's ``spec_pin.spec_text_sha256_excluding_both_pin_lines``
                    equals the sha256 of the spec text with exactly the two column-0 pin
                    lines removed — this one and the corpus pin's — each line + terminator;
                    the manifest lists the two prefixes as ``excluded_lines`` and this file
                    asserts that list, so the exclusion set is data, not a description.
  manifest ↔ bytes  every listed file is present with the listed digest, and every
                    present file is listed (a present-but-unlisted file is the failure a
                    listed-only check cannot see).
  spec ↔ files      every filename §6b names is a manifest entry (the FILE side: a wrong
                    or stale digest cannot hide behind "matches nothing"), and every
                    16-hex token in the body equal to some file's digest is that file's
                    CURRENT digest — the registry's digest MOVED at publication, so the
                    landed one is asserted by name.
  rulings           the registry's rulings digest, recomputed by the manifest's stated
                    method from the module imported in place, equals the manifest's.
  pseudonym         the set is published on the owner's ruling (2026-09-07): the rater is
                    ``human_1``; no file or filename carries the owner's given name; the
                    human label files carry no per-item timing key; no bytecode rides in.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs" / "0038-extraction-speech-act.md"
ORACLE = ROOT / "tests" / "eval" / "extraction_speech_act" / "oracle"
MANIFEST = ORACLE / "MANIFEST.json"
PREFIX = "oracle manifest sha256: "
CORPUS_PREFIX = "corpus sha256: "   # the OTHER single-line pin on this document
SPEC_PIN_KEY = "spec_text_sha256_excluding_both_pin_lines"   # the KEY says what the VALUE does
EXCLUDED_LINES = [PREFIX, CORPUS_PREFIX]                        # asserted against the manifest's own list
# Two single-line pins on one document are mutually dependent unless one of them excludes
# BOTH lines: the corpus pin (0037's rule, inherited verbatim) excludes only its own line
# and therefore covers the oracle line, so the oracle pin excludes both. Order at landing:
# the oracle line is set first (its pin does not depend on the corpus line), then the corpus
# manifest is re-pinned over the text that now carries the final oracle line.

# The ruling removed a named individual's behavioural trace from a public repo. The
# token is the rater's given name as it appeared in five research-tree files; asserted
# ABSENT, case-insensitive, in content and filenames.
EXCLUDED_NAME = "quentin"
PER_ITEM_TIMING_KEYS = {"seconds", "elapsed", "timing", "duration", "elapsed_s", "time_s"}

GOLDEN_FIXTURE = "alpha\n" + PREFIX + "0" * 64 + "\n\nbeta\n" + CORPUS_PREFIX + "1" * 64 + "\ngamma\n"
GOLDEN_EXPECTED = hashlib.sha256("alpha\n\nbeta\ngamma\n".encode("utf-8")).hexdigest()


def spec_text_sha256_excluding_both_pin_lines(text: str) -> str:
    """Remove exactly one oracle-manifest line and exactly one corpus line (line + terminator)."""
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    assert len(hits) == 1, f"exactly ONE column-0 `{PREFIX}` line is required, found {len(hits)}"
    chits = [i for i, l in enumerate(lines) if l.startswith(CORPUS_PREFIX)]
    assert len(chits) == 1, f"exactly ONE column-0 `{CORPUS_PREFIX}` line is required, found {len(chits)}"
    drop = {hits[0], chits[0]}
    kept = [l for i, l in enumerate(lines) if i not in drop]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def _spec_text() -> str:
    return SPEC.read_text(encoding="utf-8")


def _digest_token() -> str:
    hits = [l for l in _spec_text().split("\n") if l.startswith(PREFIX)]
    assert len(hits) == 1
    return hits[0][len(PREFIX):].strip()


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _present() -> dict[str, Path]:
    return {p.name: p for p in ORACLE.iterdir() if p.is_file() and p.name != "MANIFEST.json"}


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _import_registry(alias: str):
    """Import the registry IN PLACE without writing bytecode into the set being checked
    (the first run of this file failed its own no-bytecode assertion this way)."""
    import sys
    cwd = os.getcwd()
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    os.chdir(ORACLE)
    try:
        spec = importlib.util.spec_from_file_location(alias, ORACLE / "verb_registry.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # the import-time corpus gate runs here
    finally:
        os.chdir(cwd)
        sys.dont_write_bytecode = prev
    return mod


def _body() -> str:
    text = _spec_text()
    return text.split("## 1.", 1)[1] if "## 1." in text else text


# ---- the golden vector (the rule, before the artifact) --------------------------------

def test_the_exclusion_rule_on_the_golden_vector():
    assert spec_text_sha256_excluding_both_pin_lines(GOLDEN_FIXTURE) == GOLDEN_EXPECTED


# ---- spec ↔ manifest, both directions ------------------------------------------------

def test_spec_names_a_bound_manifest_digest():
    token = _digest_token()
    assert len(token) == 64 and all(c in "0123456789abcdef" for c in token), f"not a sha256: {token!r}"
    assert token != "0" * 64, "the placeholder token was never replaced by the manifest's digest"


def test_manifest_hashes_to_the_spec_digest():
    assert _sha256(MANIFEST) == _digest_token()


def test_manifest_pins_the_spec_text_excluding_both_pin_lines():
    man = _manifest()
    assert man["spec_pin"][SPEC_PIN_KEY] == spec_text_sha256_excluding_both_pin_lines(_spec_text())


def test_the_pin_was_computed_by_the_two_line_rule_and_not_the_one_line_rule():
    """The anti-check (research, re-verifying the round-2 pin from the committed bytes): the
    positive check passes under EITHER exclusion rule whenever the corpus line happens not to
    move, so it cannot say which rule ran. Removing the oracle line ALONE must give a
    DIFFERENT digest from the manifest's — proving the two-line rule is the one that ran."""
    man = _manifest()
    lines = _spec_text().split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(PREFIX)]
    assert len(hits) == 1
    oracle_only = hashlib.sha256("\n".join(lines[: hits[0]] + lines[hits[0] + 1:]).encode("utf-8")).hexdigest()
    assert oracle_only != man["spec_pin"][SPEC_PIN_KEY], "the pin equals the ONE-line exclusion: the stated two-line rule did not run"


def test_the_excluded_line_set_is_data_the_manifest_states():
    """The exclusion set is CHECKABLE, not described: the manifest lists the line prefixes it
    removed, and this file's rule removes exactly those. A key or rule text that said "one
    line" over a two-line computation (the first landing's key name) fails here, not in a
    reader's head."""
    man = _manifest()
    assert man["spec_pin"]["excluded_lines"] == EXCLUDED_LINES
    assert set(man["spec_pin"]) >= {SPEC_PIN_KEY, "excluded_lines", "rule", "spec"}
    assert "oracle_manifest_line" not in SPEC_PIN_KEY, "a key naming ONE line over a two-line value is the summary losing its bound"


# ---- manifest ↔ bytes, both directions -----------------------------------------------

def test_every_listed_file_is_present_with_its_digest():
    man = _manifest()
    present = _present()
    assert man["files"], "an empty manifest binds nothing"
    for name, entry in man["files"].items():
        assert name in present, f"listed but missing: {name}"
        h = _sha256(present[name])
        assert h == entry["sha256"], f"{name}: bytes {h[:16]} != manifest {entry['sha16']}"
        assert entry["sha16"] == entry["sha256"][:16]


def test_every_present_file_is_listed():
    man = _manifest()
    unlisted = sorted(set(_present()) - set(man["files"]))
    assert not unlisted, f"present but not in MANIFEST.json: {unlisted}"


def test_no_bytecode_or_cache_rides_in_the_set():
    stray = [str(p.relative_to(ORACLE)) for p in ORACLE.rglob("*")
             if p.is_dir() or p.suffix == ".pyc"]
    assert not stray, f"directories or bytecode under oracle/: {stray}"


# ---- spec ↔ files (the FILE side and the TOKEN side) ---------------------------------

def test_every_filename_the_spec_names_is_a_manifest_entry():
    man = _manifest()
    body = _body()
    named = {n for n in re.findall(r"`([A-Za-z0-9_§\-\.]+\.(?:py|md|json|txt))`", body)}
    # only names that are oracle files are held here; other backticked filenames belong to
    # other bindings (the corpus manifest, source files)
    oracle_like = {n for n in named if n in _present() or n.startswith(("oracle_", "verb_registry", "VERB_REGISTRY", "RUBRIC", "model_pass_0038", "score_oracle", "label_oracle", "0038-oracle-"))}
    assert oracle_like, "the spec body names no oracle file — the file side has nothing to hold"
    missing = sorted(n for n in oracle_like if n not in man["files"])
    assert not missing, f"the spec names oracle files that are not in the landed set: {missing}"


def test_every_digest_token_naming_a_landed_file_is_its_current_digest():
    man = _manifest()
    current = {e["sha16"]: name for name, e in man["files"].items()}
    tokens = set(re.findall(r"\b[0-9a-f]{16}\b", _body()))
    resolved = {t: current[t] for t in tokens if t in current}
    assert resolved, "the spec body cites no landed file by digest"
    registry_sha16 = man["files"]["verb_registry.py"]["sha16"]
    assert registry_sha16 in tokens, (
        f"the spec body does not cite the landed registry by its digest {registry_sha16} — "
        "the one file whose digest MOVED at publication must be cited by the landed bytes")


# ---- the rulings ----------------------------------------------------------------------

def test_the_rulings_digest_matches_the_manifest_by_its_stated_method():
    man = _manifest()
    mod = _import_registry("vr_pin")
    canon = json.dumps(mod.VERB_REGISTRY, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert hashlib.sha256(canon.encode("utf-8")).hexdigest() == man["rulings_sha256"]
    assert len(mod.VERB_REGISTRY) == man["registry_entries"]
    assert mod.CORPUS_SHA16 == man["corpus_sha16"]


# ---- the pseudonymisation ruling -------------------------------------------------------

def test_no_oracle_file_or_filename_carries_the_owners_name():
    present = _present()
    hits = [n for n, p in present.items()
            if EXCLUDED_NAME in p.read_text(encoding="utf-8", errors="replace").lower()]
    assert not hits, f"the ruling is violated in: {hits}"
    assert not [n for n in present if EXCLUDED_NAME in n.lower()], "a filename carries the name"
    assert EXCLUDED_NAME not in MANIFEST.read_text(encoding="utf-8").lower()


def test_human_label_files_carry_aggregated_timing_only():
    seen = 0
    for name, p in _present().items():
        if not (name.startswith("oracle_labels") and name.endswith(".json")):
            continue
        seen += 1
        data = json.loads(p.read_text(encoding="utf-8"))
        labels = data.get("labels", data)
        items = labels.values() if isinstance(labels, dict) else labels
        for item in items:
            if isinstance(item, dict):
                leaked = PER_ITEM_TIMING_KEYS & set(item)
                assert not leaked, f"{name}: per-item timing key {leaked} survives aggregation"
    assert seen >= 2, "both human label runs are expected in the set"


# ---- rule zero: the negative controls -------------------------------------------------

def test_the_negative_controls_fail():
    man = _manifest()
    # golden vector: a second digest line is refused
    try:
        spec_text_sha256_excluding_both_pin_lines(GOLDEN_FIXTURE + PREFIX + "1" * 64 + "\n")
    except AssertionError:
        pass
    else:
        raise AssertionError("two digest lines were accepted")
    # manifest ↔ bytes: an edited byte moves the digest
    name, entry = next(iter(man["files"].items()))
    assert hashlib.sha256(_present()[name].read_bytes() + b"\n").hexdigest() != entry["sha256"]
    # token side: the pre-publication registry digest must NOT resolve to a landed file
    assert "197e0976272eed3d" not in {e["sha16"] for e in man["files"].values()}
    # spec → manifest: a changed manifest byte breaks the pin
    assert hashlib.sha256(MANIFEST.read_bytes() + b" ").hexdigest() != _digest_token()
