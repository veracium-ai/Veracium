"""0038 §6b — the evidence set's DISPOSITION is checked against the set it dispositions.

`tests/eval/extraction_speech_act/oracle/SUPERSEDED-CONCLUSIONS.md` carries, in a JSON block, the
withdrawn phrases, the files that must carry a supersession marker, and the files declared exempt
with their reasons. Round 3 (R3-1) found the spec current and the evidence stale; round 4's first
assembly found the evidence current and the DISPOSITION of the evidence stale — a registry row
still phrased as a to-do ("needs the same treatment") after the treatment had been applied in the
same package — and both seal-check legs were green because nothing read the disposition against
the files it describes. `lint_withdrawn.py` selects `specs/*.md` and `tests/test_*.py`; the oracle
set is under neither, so the house gate reads none of its bytes. This file is the check that reads
the JSON and holds it over the set; it lives under `tests/test_*.py` so the house gate reads IT.

Properties:
  markers        the marker set is `lint_withdrawn.MARKERS` IMPORTED plus the file's `markers_extra`
                 — never a retyped copy.
  coverage       every file in the set containing a withdrawn phrase either carries a marker or is
                 in `declared_exempt` with a non-empty reason. Nothing carries a phrase silently.
  state          every `must_carry_a_marker` file carries a marker; every `declared_exempt` file
                 exists; no entry is phrased as a TO-DO ("needs", "to be", "should", "pending") — a
                 to-do goes stale the moment it is done and nothing can tell; a STATE can be compared
                 against the file.
  no to-do keys  no `owned_elsewhere`-shaped key: "true, but checked somewhere else" was where the
                 stale row lived.
  negative       the round-4 first assembly's own pre-fix entry (embedded verbatim from the discarded
                 bytes) fails the same checker — the check has a real failing input.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tests" / "eval" / "extraction_speech_act" / "oracle"
DISPOSITION = ORACLE / "SUPERSEDED-CONCLUSIONS.md"

sys.path.insert(0, str(ROOT / "specs"))
import lint_withdrawn  # noqa: E402  — MARKERS imported, never retyped

TODO_SHAPES = re.compile(r"\b(needs?|to be (done|added|marked|fixed|applied|treated|updated)|should( be)?|pending|TODO|outstanding|not yet)\b", re.I)   # 'to be' alone fires on legitimate states ("known to be superseded") — measured 3 false positives in 6 probes
FORBIDDEN_KEYS = {"owned_elsewhere"}


def load_disposition(text: str) -> dict:
    m = re.search(r"```json\n(.*?)\n```", text, re.S)
    assert m, "the disposition carries its check data in ONE ```json block"
    return json.loads(m.group(1))


def markers(disp: dict) -> tuple:
    return tuple(lint_withdrawn.MARKERS) + tuple(disp.get("markers_extra", []))


def _paragraphs(text: str):
    return re.split(r"\n\s*\n", text)   # lint_withdrawn's paragraph split, the house idea of a block


def _carries_phrase(text: str, phrases) -> list:
    flat = lint_withdrawn._normalise(text).lower()   # the house normaliser, never a third idea of a mention
    return [p for p in phrases if lint_withdrawn._normalise(p).lower() in flat]


def check_disposition(disp: dict, files: dict) -> list:
    """THE CHECKER, shared by the real assertion and its negative control. `files` maps filename
    to text. Returns a list of violation strings (empty == the disposition holds over the set).
    Marker rule, paragraph-granular like lint_withdrawn's exemption: a paragraph carrying a
    withdrawn phrase is covered if it carries a marker itself OR the file's FIRST paragraph (its
    header) carries one — a supersession header governs the record below it, and a record's body
    is not amended (a record amended to agree with a later conclusion is no longer a record)."""
    out = []
    for k in FORBIDDEN_KEYS & set(disp):
        out.append(f"forbidden key {k!r}: an exemption 'checked somewhere else' is checked nowhere")
    phrases = disp["withdrawn_phrases"]
    marks = markers(disp)
    must = disp["must_carry_a_marker"]
    exempt = disp["declared_exempt"]
    for name, state in list(must.items()) + list(exempt.items()):
        if name not in files:
            out.append(f"{name}: named in the disposition but not in the set")
        if not state or not state.strip():
            out.append(f"{name}: an empty reason/state")
        elif TODO_SHAPES.search(state):
            out.append(f"{name}: entry phrased as a TO-DO, not a STATE — {state[:60]!r}")
    governs = disp.get("header_marker_governs_record", {})
    for name, reason in governs.items():
        if name not in files:
            out.append(f"{name}: declared header-governed but not in the set")
        elif not reason or not reason.strip() or TODO_SHAPES.search(reason):
            out.append(f"{name}: header-governance reason empty or phrased as a TO-DO")
    for name, text in files.items():
        if name == DISPOSITION.name or name in exempt:
            continue
        paras = _paragraphs(text)
        header_has_marker = bool(paras) and any(mk in paras[0] for mk in marks)
        # header governance is DECLARED data, never a global property of markers: a file whose first
        # paragraph happens to carry a marker gets no blanket pass unless the disposition names it
        header_marked = header_has_marker and name in governs
        if header_has_marker and name not in governs and _carries_phrase(text, phrases):
            out.append(f"{name}: header carries a marker but the file is not declared in header_marker_governs_record — an exemption nobody declared")
        for para in paras:
            hits = _carries_phrase(para, phrases)
            if hits and not header_marked and not any(mk in para for mk in marks):
                out.append(f"{name}: paragraph carries withdrawn phrase(s) {hits} with no marker in it or in the file's header, and no declared exemption")
        if name in must and not (header_marked or any(any(mk in p for mk in marks) for p in paras)):
            out.append(f"{name}: must carry a marker and carries none of {marks}")
    return out


def _set_files() -> dict:
    return {p.name: p.read_text(encoding="utf-8", errors="replace") for p in ORACLE.iterdir() if p.is_file()}


def test_the_disposition_holds_over_every_file_in_the_set():
    disp = load_disposition(DISPOSITION.read_text(encoding="utf-8"))
    files = _set_files()
    assert DISPOSITION.name in disp["declared_exempt"], "the disposition quotes the phrases it withdraws and must say so"
    violations = check_disposition(disp, files)
    assert not violations, "\n".join(violations)
    # the check held something: the set contains withdrawn phrases somewhere, all covered
    carriers = [n for n, t in files.items() if n != DISPOSITION.name and _carries_phrase(t, disp["withdrawn_phrases"])]
    assert carriers, "no file in the set carries a withdrawn phrase — the disposition dispositions nothing"


def test_markers_are_imported_not_retyped():
    disp = load_disposition(DISPOSITION.read_text(encoding="utf-8"))
    assert "IMPORTED" in disp["markers_from"] and "lint_withdrawn" in disp["markers_from"]
    assert set(lint_withdrawn.MARKERS) <= set(markers(disp))
    assert not (set(lint_withdrawn.MARKERS) & set(disp.get("markers_extra", []))), "an extra marker retypes a house one"


def test_the_registry_marker_state_is_true_of_the_file():
    """The registry row states its marker lines as a STATE; a state is checked by opening the file."""
    disp = load_disposition(DISPOSITION.read_text(encoding="utf-8"))
    assert "verb_registry.py" in disp["must_carry_a_marker"]
    text = (ORACLE / "verb_registry.py").read_text(encoding="utf-8")
    changelog = text.split("# CHANGELOG", 1)[1] if "# CHANGELOG" in text else text
    assert changelog.count("WITHDRAWN") >= 2, "the CHANGELOG's two gate sentences must both be marked"


# ---- the negative control: the round-4 first assembly's pre-fix disposition -------------------
# WITHDRAWN — negative-control fixture, quoted to prove it FAILS. Embedded verbatim in shape from the
# discarded package (sha256 18ad6b69…): the registry sat under `owned_elsewhere` with a to-do sentence,
# and nothing read it against the registry beside it. NO BLANK LINE between this comment and the dict:
# lint_withdrawn exempts at paragraph granularity, so the marker above must share the block with the
# quoted phrase below, or the house gate fires on the fixture that exists to prove the check bites.
PRE_FIX_OWNED_ELSEWHERE = {
    "verb_registry.py": "dev seat: its digest is pinned by the oracle manifest; the v2 CHANGELOG's "
                        "'after the §8 gate PASSED against v1' needs the same treatment",
}


def test_the_round_4_first_assembly_disposition_fails_this_checker():
    disp = load_disposition(DISPOSITION.read_text(encoding="utf-8"))
    files = _set_files()
    stale = json.loads(json.dumps(disp))
    stale["must_carry_a_marker"].pop("verb_registry.py")
    stale["owned_elsewhere"] = dict(PRE_FIX_OWNED_ELSEWHERE)
    violations = check_disposition(stale, files)
    assert any("owned_elsewhere" in v for v in violations), violations
    # and the to-do shape is caught on its own, without the forbidden key
    stale2 = json.loads(json.dumps(disp))
    stale2["must_carry_a_marker"]["verb_registry.py"] = PRE_FIX_OWNED_ELSEWHERE["verb_registry.py"]
    assert any("TO-DO" in v for v in check_disposition(stale2, files)), "a to-do-shaped state was accepted"
    # an unmarked must-carry file is caught (the registry with its markers stripped in memory) — via the
    # must-carry branch, since the registry's gate sentences were REWRITTEN and carry no withdrawn phrase
    files2 = dict(files)
    files2["verb_registry.py"] = files2["verb_registry.py"].replace("WITHDRAWN", "")
    assert any("verb_registry.py" in v and "must carry" in v for v in check_disposition(disp, files2)), "an unmarked must-carry file was accepted"
    # and a TRUE silent carrier is caught via the PHRASE/MARKER branch: plant a withdrawn phrase into a
    # paragraph of a copied file that is neither exempt nor header-governed. This is the only input in the
    # suite that exercises that branch: over the present set every phrase-bearing paragraph is exempt or
    # header-governed, so the rule guards future edits and is exercised here, not by the set.
    victim = next(n for n in files if n.endswith(".py") and n not in disp["declared_exempt"] and n not in disp.get("header_marker_governs_record", {}) and n != "verb_registry.py")
    files3 = dict(files)
    files3[victim] = files3[victim] + "\n\n# a planted live claim: the §8 gate PASSED\n"
    hits = [v for v in check_disposition(disp, files3) if v.startswith(victim) and "carries withdrawn phrase" in v]
    assert hits, f"a planted silent carrier in {victim} was accepted"
    # and a header-marked file NOT declared header-governed is refused: give the victim a marker header
    files4 = dict(files)
    files4[victim] = "SUPERSEDED CONCLUSION: header\n\n" + files3[victim]
    assert any(v.startswith(victim) and "not declared" in v for v in check_disposition(disp, files4)), "an undeclared header exemption was accepted"
