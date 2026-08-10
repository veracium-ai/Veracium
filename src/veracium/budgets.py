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
MARKER_RESERVE = 16              # the non-truncatable wiki compile-marker line
REPORT_RESERVE = 32              # the per-surface truncation report (bounded-width
#                                  counts keep its worst case ~100 chars ≈ 25 tokens)
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
    # the reserve is PER-SURFACE and matches what the surface actually charges
    # (R-impl2-4): recall/proactive reserve the 32-token truncation REPORT; the wiki
    # reserves the 16-token compile-marker line.
    reserve = MARKER_RESERVE if surface == "wiki" else REPORT_RESERVE
    return (ENVELOPES[surface]
            + max(MIN_ITEM_ALLOWANCE, mandatory_contested_allowance(heading_allowance))
            + reserve)


def validate_budget(surface: str, value: int,
                    heading_allowance: int = GROUP_HEADING_ALLOWANCE) -> int:
    """Reject a below-floor budget LOUDLY, naming the surface, floor and derivation
    (0012 I10e). Applied at config construction AND at every surface build. The
    serialized derivation uses the surface's ACTUAL reserve (R-impl3-3)."""
    fl = floor_for(surface, heading_allowance)
    if value < fl:
        reserve = MARKER_RESERVE if surface == "wiki" else REPORT_RESERVE
        reserve_name = "marker reserve" if surface == "wiki" else "report reserve"
        raise ValueError(
            f"token budget {value} for the {surface!r} surface is below its floor {fl} "
            f"(= envelope {ENVELOPES[surface]} + max(item allowance {MIN_ITEM_ALLOWANCE}, "
            f"mandatory contested allowance "
            f"{mandatory_contested_allowance(heading_allowance)}) + {reserve_name} "
            f"{reserve}); a budget below the floor cannot carry the envelope plus "
            f"one item and the safety framing — raise the budget or omit it")
    return value


def validate_surface_params(surface: str, budget: int, *, item_cap: int = 512,
                            variant_cap: int = 4,
                            heading_allowance: int = GROUP_HEADING_ALLOWANCE) -> None:
    """I10e at surface BUILD (R-impl3-3): every mutable bound a surface call accepts is
    revalidated where it is used, not only at MemoryConfig construction — a direct
    caller cannot smuggle a sub-floor cap past the config."""
    validate_budget(surface, budget, heading_allowance)
    if item_cap < MIN_ITEM_ALLOWANCE:
        raise ValueError(
            f"item_cap {item_cap} is below the minimum item allowance "
            f"{MIN_ITEM_ALLOWANCE} — one framed clamped item must fit")
    if variant_cap < 1:
        raise ValueError("variant_cap must be >= 1")


# --- per-item clamp (framing PLUS content, in-item elision) ------------------------- #
# The FROZEN recoverability-bearing elision marker (0012 §4c(ii)): truncation inside an
# item names where the full record lives — a bare ellipsis tells the model nothing.
ELISION_MARKER = "… [content truncated; full record via introspect()]"


def clamp_item(line: str, cap_tokens: int) -> str:
    if est_tokens(line) <= cap_tokens:
        return line
    keep = max(1, (cap_tokens - est_tokens(ELISION_MARKER)) * 4)
    return line[:keep] + ELISION_MARKER


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


def clamp_edge_line(edge, cap_tokens: int, render_fn) -> str:
    """Clamp an EDGE line by shrinking its CONTENT (object, then note), never its
    framing — the trust/state labels render at the line's END, so a tail clamp would
    sever exactly the safety framing I10c protects. Deterministic: shrink the longer
    content field first, halving, until the framed line fits."""
    line = render_fn([edge])
    if not line or est_tokens(line) <= cap_tokens:
        return line
    e = edge.model_copy(deep=True)
    orig_note, orig_obj = e.note, e.object
    n_keep, o_keep = len(orig_note), len(orig_obj)
    for _ in range(64):
        # cut fractions of the ORIGINAL fields (never re-cut a marker), longer first
        if n_keep > o_keep and n_keep > 8:
            n_keep = max(8, n_keep // 2)
            e.note = orig_note[:n_keep] + ELISION_MARKER
        elif o_keep > 8:
            o_keep = max(8, o_keep // 2)
            e.object = orig_obj[:o_keep] + ELISION_MARKER
        else:
            break
        line = render_fn([e])
        if est_tokens(line) <= cap_tokens:
            return line
    return line
