"""specs/0012 I10 — the budget-machinery primitives.

I10 governs the RENDERED, MODEL-FACING text of the three surfaces (query recall, the wiki
compiler input, proactive assembly) in ESTIMATED tokens under the frozen `chars/4`
estimator. Budgets are hard; floors are envelope-derived and validated loudly at every
source; the compile-drop marker's serialization is FROZEN and versioned through the wiki
cache identity. Structured carriers (`Recall.edges` etc.) are deliberately out of scope
(0012 §8).
"""
from __future__ import annotations

import re
from typing import Optional

# --- the frozen estimator ----------------------------------------------------------- #
def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# --- floor derivation (0012 §4c(i), R11-2/R12-2) ------------------------------------ #
MIN_ITEM_ALLOWANCE = 64          # one framed, clamped item
MARKER_RESERVE = 16              # the non-truncatable truncation/wiki marker
WITHHELD_MARKER_RESERVE = 16     # "… +N more contending values withheld"
MEMBER_FRAMING_COST = 32         # a contested member's framing (author tag, punctuation)
MIN_MEMBER_CONTENT = 32          # the minimum clamped content per mandatory member
GROUP_HEADING_ALLOWANCE = 48     # default sub-cap for a heading's clamped subject+relation

# Measured envelope costs (estimated tokens of each surface's constant scaffolding).
# test_0012_budgets.py measures the real scaffolding and asserts these COVER it — the
# constants may exceed the measurement (headroom) but never undershoot it.
ENVELOPES = {"recall": 48, "wiki": 300, "proactive": 32}


def mandatory_contested_allowance(heading_allowance: int = GROUP_HEADING_ALLOWANCE) -> int:
    """0012 §4c: heading + withheld marker + 2 × (framing + min content) — 2 being the
    MAXIMUM mandatory cardinality (highest-effective-authority member + grounded prior,
    which MAY alias at runtime; aliasing frees budget but never lowers the floor)."""
    return (heading_allowance + WITHHELD_MARKER_RESERVE
            + 2 * (MEMBER_FRAMING_COST + MIN_MEMBER_CONTENT))


def floor_for(surface: str, heading_allowance: int = GROUP_HEADING_ALLOWANCE) -> int:
    return (ENVELOPES[surface]
            + max(MIN_ITEM_ALLOWANCE, mandatory_contested_allowance(heading_allowance))
            + MARKER_RESERVE)


def validate_budget(surface: str, value: int,
                    heading_allowance: int = GROUP_HEADING_ALLOWANCE) -> int:
    """Reject a below-floor budget LOUDLY, naming the surface, floor and derivation
    (0012 I10e). Applied at config construction AND at every surface build."""
    fl = floor_for(surface, heading_allowance)
    if value < fl:
        raise ValueError(
            f"token budget {value} for the {surface!r} surface is below its floor {fl} "
            f"(= envelope {ENVELOPES[surface]} + max(item allowance {MIN_ITEM_ALLOWANCE}, "
            f"mandatory contested allowance "
            f"{mandatory_contested_allowance(heading_allowance)}) + marker reserve "
            f"{MARKER_RESERVE}); a budget below the floor cannot carry the envelope plus "
            f"one item and the safety framing — raise the budget or omit it")
    return value


# --- per-item clamp (framing PLUS content, in-item elision) ------------------------- #
def clamp_item(line: str, cap_tokens: int) -> str:
    if est_tokens(line) <= cap_tokens:
        return line
    return line[: max(1, cap_tokens * 4 - 2)] + "…"


# --- the compile-drop marker (0012 §4c(iv), FROZEN grammar R10-3/R12-1) ------------- #
MARKER_GRAMMAR_VERSION = "v1"
MARKER_PREFIX = "[[veracium-wiki-compile:"
ESCAPED_PREFIX = "[[veracium-wiki-compile-escaped:"
_MARKER_RE = re.compile(
    r"^\[\[veracium-wiki-compile:v1\]\] "
    r"\+(\d{1,3}|999\+) facts / \+(\d{1,3}|999\+) episodes not compiled$")


def bounded_count(n: int) -> str:
    """Exact to 999, then the literal '999+' — fixed width, never grows with the store."""
    return str(n) if n <= 999 else "999+"


def sanitize_llm_body(text: str) -> str:
    """The byte rewrite: every occurrence of the literal marker prefix in LLM output
    becomes the -escaped: form (inert to the parser), BEFORE the authoritative line is
    appended. Code-owned marker lines are appended after this runs, never before."""
    return text.replace(MARKER_PREFIX, ESCAPED_PREFIX)


def append_compile_marker(body: str, facts_dropped: int, episodes_dropped: int) -> str:
    """Newline-normalize, then append the ALWAYS-present authoritative final line —
    including the zero case."""
    normalized = "\n".join(ln.rstrip() for ln in body.rstrip().splitlines())
    line = (f"[[veracium-wiki-compile:{MARKER_GRAMMAR_VERSION}]] "
            f"+{bounded_count(facts_dropped)} facts / "
            f"+{bounded_count(episodes_dropped)} episodes not compiled")
    return (normalized + "\n" + line) if normalized else line


def parse_compile_marker(body: Optional[str]) -> dict:
    """The frozen R11-5 schema: {"status": "ok"|"absent"|"legacy"|"malformed",
    "facts_dropped": int|"999+"|None, "episodes_dropped": int|"999+"|None,
    "marker_line": str|None}. `absent` = no cache; `legacy` = no sentinel anywhere
    (pre-v12); `malformed` = a sentinel present but the final line grammar-invalid.
    Drop fields and marker_line are None unless status is "ok"."""
    none = {"facts_dropped": None, "episodes_dropped": None, "marker_line": None}
    if body is None:
        return {"status": "absent", **none}
    lines = body.rstrip().splitlines()
    final = lines[-1] if lines else ""
    m = _MARKER_RE.match(final)
    if m:
        def _c(tok: str):
            return tok if tok == "999+" else int(tok)
        return {"status": "ok", "facts_dropped": _c(m.group(1)),
                "episodes_dropped": _c(m.group(2)), "marker_line": final}
    if MARKER_PREFIX in body:
        return {"status": "malformed", **none}
    return {"status": "legacy", **none}


# --- the provider-free stale-cache notice (0012 I10l) ------------------------------- #
STALE_WIKI_NOTICE = "[wiki omitted: cache is stale; recompilation requires an LLM provider]"
