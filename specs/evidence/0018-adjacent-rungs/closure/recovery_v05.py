"""0018 adjacent rungs, round-3 closure (R3-01, R3-02, R3-03): ONE executable recovery classifier for the amendment's §7.

A pure function of STRUCTURED inputs only; it is never given a diagnostic. Its rows and action ids come from the table
EXTRACTED from the candidate (extract_table.py -> recovery-table JSON), never retyped here: the code decides WHICH row,
by the rules §7 states, and returns that row's extracted ids.

    classify(route, outcome=None, facts=None, t=None, ctx=None, readback=None) -> Decision(row, actions, counted)

route: "preflight" | "unexpected-base" | "delegated" | "write-error" | "read-error" | "package-pre-mint" |
       "package-post-mint".  facts: (changed, committed, state, version) or None.  ctx: the minted (from, to) for the
       post-mint escape; readback: the pin's ReadbackResult for it."""
from __future__ import annotations

import json
import pathlib
from typing import NamedTuple, Optional

TABLE: dict = {}
NO_RECORD = ("migration-audit-unavailable", "migration-audit-state-unknown", "migration-quiescence-required",
             "migration-evidence-missing")


class Decision(NamedTuple):
    row: str
    actions: tuple
    counted: bool


def load(path):
    TABLE.clear()
    TABLE.update(json.loads(pathlib.Path(path).read_text())["rows"])
    # P4's two preflight readings are stated in its own cell: refuse a table that no longer says them
    p4 = TABLE["P4"]["row_text"]                 # its readings are stated in the operator column
    for tok in ("`newer`", "`no-rerun-this-build`", "`migration-source-missing`", "`unaccepted`", "`no-rerun-not-a-source`"):
        assert tok in p4, f"P4's cell no longer states {tok}; the classifier's preflight readings must follow the text"
    return TABLE


def ids(row):
    return tuple(TABLE[row]["actions"])


def klass(ch, co):
    return {(True, True): "committed", (False, False): "unchanged", (None, None): "unknown"}.get((ch, co))


def u_row(outcome, state, version, t):
    """7b's unchanged rows: U0, then the first of U1..U6 whose input names the outcome (and its state, when the row
    names one); every other outcome is U7, the fallback (including any outcome a later head adds)."""
    if outcome == "current" and state == "destination" and version == t:
        return "U0"
    for r in ("U1", "U2", "U3", "U4", "U5", "U6"):
        row = TABLE[r]
        if outcome in row["outcomes"] and (row["state"] is None or row["state"] == state):
            return r
    return "U7"


def record_row(outcome, facts, t):
    """7b: by the facts' CLASS (changed, committed); state and version are printed data."""
    ch, co, state, version = facts
    k = klass(ch, co)
    if k == "committed":
        return "C1" if (outcome in TABLE["C1"]["outcomes"] and version == t) else "C2"
    if k == "unknown":
        return "K"
    if k == "unchanged":
        return u_row(outcome, state, version, t)
    raise ValueError(f"facts of no class: {facts!r} (problems() admits none)")


def bound(readback, ctx) -> bool:
    """0018 §4f(7), the pin's own rule (release_migration._package_escape_post_mint: a record, outcome
    package-inconsistent), plus v0.5's 'at the minted endpoints' for a rung: checked BEFORE any counting."""
    return (readback is not None and getattr(readback, "kind", None) == "record" and readback.facts is not None
            and readback.facts.outcome == "package-inconsistent"
            and (readback.facts.from_version, readback.facts.to_version) == tuple(ctx))


def classify(route, outcome=None, facts=None, t=None, ctx=None, readback=None) -> Decision:
    if route == "preflight":
        if outcome == "current":
            return Decision("P0", ids("P0"), False)
        if outcome == "mint-contention":
            return Decision("P1", ids("P1"), False)
        if outcome == "invalid-request":
            return Decision("P2", ids("P2"), False)
        state = facts[2] if facts else None
        # P4: the U row the outcome and state select, read as an observation made just now (no conditional)
        if outcome == "newer":
            return Decision("P4>U4", ("no-rerun-this-build",), False)
        if outcome == "migration-source-missing" and state == "unaccepted":
            return Decision("P4>U1", ids("U1"), False)
        r = u_row(outcome, state, None, None)
        return Decision(f"P4>{r}", ids(r), False)
    if route == "unexpected-base":
        return Decision("P3", ids("P3"), False)
    if route == "delegated":
        if outcome in NO_RECORD:
            r = next(n for n in ("N1", "N2", "N3", "N4") if outcome in TABLE[n]["outcomes"])
            return Decision(r, ids(r), False)
        r = record_row(outcome, facts, t)
        return Decision(r, ids(r), r in ("C1", "C2"))
    if route == "write-error":
        # E1: the 7b action of the CARRIED facts, exactly as if they were the record, plus the disclosure
        r = record_row(outcome, facts, t)
        store = (TABLE["E1"]["resume"],) if r in ("C1", "U0") else ids(r)   # an escape never continues
        return Decision(f"E1>{r}", store + (TABLE["E1"]["disclosure"],), r in ("C1", "C2"))
    if route == "read-error":
        return Decision("E2", ids("E2"), False)
    if route == "package-pre-mint":
        return Decision("E3", ids("E3"), False)
    if route == "package-post-mint":
        if bound(readback, ctx):
            f = readback.facts
            committed = klass(f.store_changed, f.transaction_committed) == "committed"
            return Decision("E4", ("repair-build",) + (("stop-inspect-committed",) if committed else ()), committed)
        return Decision("E4", ("repair-build",), False)            # unbound: unavailable, no id, nothing counted
    raise ValueError(f"route {route!r}")
