"""0012 v18.2 (research's stage-2 note N3 on f25ff044, pre-existing since 0.4.0): a CONFIRM WHEN NATURAL line and a
"worth a follow-up" line (CURRENT CONTEXT or RESTATED VARIANTS) name a subject other than `user`, as a DATED
COMMITMENTS line does (S1-4). Before, `works_on: project alpha (since …)` for a `person:sam` fact read as the user's own.

Each such line is composed by one function of its cap (`_framed_line`, v18.1 NEW 1's structure), at composition and on
the first-item path: the whole line held to the cap, the subject clamped at item_cap_tokens // 8, the object taking what
the rest leaves, the framing (and its restatement count) at the end, one clamped item; the receipt carries the subject
as rendered (TT-R3-02), for the line returned. A subject-`user` line is byte-identical to before.
"""
import re
from datetime import datetime, timedelta, timezone

import pytest

from veracium.config import MemoryConfig
from veracium.proactive import assemble
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance, Volatility
from veracium.store.sqlite import SqliteStore
from veracium.trust_tools import RenderReceipt

U = "u"
NOW = datetime.now(timezone.utc)


def _e(eid, obj, subject="person:sam", rel="works_on", note="", vol=Volatility.TRANSIENT, flag=False, days=1):
    t = NOW - timedelta(days=days)
    return Edge(id=eid, user_id=U, subject=subject, relation=rel, object=obj, note=note, volatility=vol,
                valid_from=t, needs_confirmation=flag,
                provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev-" + eid,
                                      disclosure=Disclosure.MENTIONABLE, observed_at=t))


def _brief(edges, budget=1200, cap=512):
    s = SqliteStore(":memory:")
    for e in edges:
        s.add_edge(e)
    rc = RenderReceipt()
    cfg = MemoryConfig(db_path=":memory:", item_cap_tokens=cap)
    ctx, *_rest = assemble(s, U, cfg, now=NOW, token_budget=budget, receipt=rc)
    return ctx, {u["id"]: u for u in rc.units}, cfg


def _section(ctx, header):
    m = re.search(rf"^{re.escape(header)}\n((?:.+\n?)+?)(?:\n|$)", ctx, re.M)
    return m.group(1).splitlines() if m else []


def _one(lines):
    """The one line a cell judges, asserted (a missing line fails by assertion, never by unpacking)."""
    assert len(lines) == 1, lines
    return lines[0]


def _unit(units, eid):
    assert eid in units, sorted(units)
    return units[eid]


def _clamped(ctx):
    found = re.findall(r"/ (\d+) clamped\]", ctx)
    return int(found[0]) if found else 0


def _est(s):                                           # the assembler's own estimate (est_tokens via budgets)
    from veracium.budgets import est_tokens
    return est_tokens(s)


TIERS = {
    "confirm": ("## CONFIRM WHEN NATURAL", lambda **k: [_e("x", "the old boat", rel="owns", vol=Volatility.SLOW,
                                                            flag=True, days=200, **k)],
                " — confirm when natural (unrefreshed since "),
    "current": ("## CURRENT CONTEXT", lambda **k: [_e("x", "project alpha", **k)], " (since "),
    "variants": ("## RESTATED VARIANTS",
                 lambda **k: [_e("y", "project alpha beta", note="NEWER", days=1, **k),
                              _e("x", "project alpha", note="OLDER", days=3, **k)], " (since "),
}


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_each_tier_names_a_non_user_subject_and_the_receipt_carries_it(tier):
    """The line reads `<relation>: person:sam — <object>` before its framing, and the unit for that line carries the
    subject as rendered. Mutants: the line without its subject; the subject rendered but not registered."""
    header, edges, framing = TIERS[tier]
    ctx, units, _ = _brief(edges())
    line = _one([ln for ln in _section(ctx, header) if "project alpha" in ln and "beta" not in ln
              or "old boat" in ln])
    assert re.match(r"^\w+: person:sam — ", line) and framing in line, line
    assert units.get("x", {}).get("subject") == "person:sam", units.get("x", {})


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_a_subject_user_line_is_byte_identical(tier):
    """The same edges with subject `user` render exactly the pre-v18.2 form: no subject, no unit subject."""
    header, edges, _ = TIERS[tier]
    ctx, units, _cfg = _brief(edges(subject="user"))
    lines = _section(ctx, header)
    e = [x for x in edges(subject="user") if x.id == "x"][0]
    if tier == "confirm":
        want = (f"{e.relation}: {e.object} — confirm when natural "
                f"(unrefreshed since {e.provenance.observed_at.date()})")
    else:
        want = f"{e.relation}: {e.object} (since {e.valid_from.date()} — worth a follow-up)"
    assert want in lines, (want, lines)
    assert "subject" not in _unit(units, "x")


def test_the_restatement_tail_is_kept_after_the_subject():
    """A flagged group's restatement count stays at the end of a subject line, inside the line the cap holds."""
    ctx, units, _ = _brief([_e("x", "the old boat", rel="owns", vol=Volatility.SLOW, flag=True, days=200),
                            _e("x2", "the old boat", rel="owns", note="again", vol=Volatility.SLOW, flag=True,
                               days=150)])
    line = _one([ln for ln in _section(ctx, "## CONFIRM WHEN NATURAL") if "old boat" in ln])
    assert line.startswith("owns: person:sam — the old boat — confirm when natural"), line
    assert line.endswith(" restatements need confirmation)"), line


def test_an_object_that_is_a_substring_of_its_subject():
    """The subject is placed by the composer, never found by searching the line: an object equal to part of the
    subject leaves both intact, and the receipt's place check (admit) holds."""
    ctx, units, _ = _brief([_e("x", "alice", subject="person:alice")])
    line = _one([ln for ln in _section(ctx, "## CURRENT CONTEXT") if "alice" in ln])
    assert line.startswith("works_on: person:alice — alice (since "), line
    assert units.get("x", {}).get("subject") == "person:alice"


@pytest.mark.parametrize("tier", ["confirm", "current", "variants"])
def test_the_whole_line_is_held_to_the_item_cap_at_new1_sizes(tier):
    """v18.1 NEW 1's sizes (a 420-character subject, a 3,000-character object): the line is within item_cap_tokens,
    its framing intact at the end, the subject clamped and still the unit's subject as rendered. ONE clamped item per
    edge (the variants case has two edges, its survivor in CURRENT clamped too)."""
    sub, obj = "person:" + "s" * 413, "o" * 3000
    header, _edges, framing = TIERS[tier]
    edges = ([_e("x", obj, subject=sub, rel="owns", vol=Volatility.SLOW, flag=True, days=200)] if tier == "confirm"
             else [_e("x", obj, subject=sub)] if tier == "current"
             else [_e("y", obj + " extra", subject=sub, note="NEWER", days=1),
                   _e("x", obj, subject=sub, note="OLDER", days=3)])
    ctx, units, cfg = _brief(edges, budget=4000)
    line = _one([ln for ln in _section(ctx, header) if "ooo" in ln and units.get("x", {}).get("text") == ln])
    assert _est(line) <= cfg.item_cap_tokens, (_est(line), cfg.item_cap_tokens)
    assert framing in line and (line.endswith("— worth a follow-up)") if tier == "current" else
                                line.endswith(")")), line[-80:]
    seg = units.get("x", {}).get("subject")
    assert isinstance(seg, str), units.get("x")
    assert seg != sub and sub.startswith(seg.split("…")[0]) and seg in line, seg      # clamped, as rendered
    assert _clamped(ctx) == (2 if tier == "variants" else 1), ctx


@pytest.mark.parametrize("tier", ["confirm", "current"])
def test_the_first_item_recomposition_keeps_the_subject_in_the_line_and_the_receipt(tier):
    """On the first-item path (the only line, over the remaining budget) the line is RECOMPOSED by its own composer
    at that budget: the subject and the framing stay, and the receipt's unit carries the subject for the line as
    ADMITTED. Before, a replace inside the line made a new key that the receipt missed (N3's own defect, on this
    path), and could land inside the subject. VARIANTS is not a case: it renders last and its group's survivor sits in
    CURRENT before it, so a variant line is never the first item."""
    obj = "o" * 3000
    header, _edges, framing = TIERS[tier]
    edges = ([_e("x", obj, rel="owns", vol=Volatility.SLOW, flag=True, days=200)] if tier == "confirm"
             else [_e("x", obj)])
    full, *_ = _brief(edges, budget=4000)
    from veracium.budgets import floor_for
    ctx, units, _cfg = _brief(edges, budget=floor_for("proactive"))
    line = _one([ln for ln in _section(ctx, header) if "ooo" in ln])
    assert line not in full, "the budget did not force the first-item path"
    assert re.match(r"^\w+: person:sam — o+", line) and framing in line, line
    assert units.get("x", {}).get("subject") == "person:sam" and units.get("x", {}).get("text") == line
