"""The spec-number allocation registry's gate (specs/allocation.py).

A number is held by a file in the tree, RESERVED by an arc that has not
drafted it, or free. The registry derives holders from the tree, carries
reservations as data with their provenance, records a known collision as a
dated CONTESTED cell, and refuses any collision that is not so recorded.
Written 2026-09-06 after `specs/0033-…` was drafted, reviewed and merged under
a number reserved two days earlier in a coordination-file paragraph nobody
could check against.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))
import allocation  # noqa: E402

PY = sys.executable


def test_the_allocation_registry_has_no_unrecorded_problems():
    """Duplicates, unrecorded collisions with a live reservation, stale
    contested entries, and reservations without provenance all fail here.
    The known collision (0033) is RECORDED, so it is not a problem the gate
    reports — it is a state the registry names."""
    assert allocation.allocation_problems() == []


def test_the_rendered_table_is_current():
    r = subprocess.run([PY, str(ROOT / "specs" / "allocation.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_holders_are_derived_from_the_tree_not_listed():
    """Every spec file's number appears exactly once, and every number the
    registry reports exists as a file — derived both directions."""
    files = sorted(p.name for p in (ROOT / "specs").glob("[0-9][0-9][0-9][0-9]-*.md"))
    rows = allocation.holders()
    assert sorted(r["file"] for r in rows) == files
    assert len({r["number"] for r in rows}) == len(rows)


def test_an_unrecorded_collision_is_refused__with_its_control(monkeypatch):
    """Rule zero: the gate can fail. Remove the CONTESTED record for a number
    inside a live reservation and the collision is reported; restore it and
    the report clears. A reservation the tree does not touch reports nothing."""
    # plant a collision: a live reservation over the tree's own highest number
    top = max(r["number"] for r in allocation.holders())
    topfile = [r["file"] for r in allocation.holders() if r["number"] == top][0]
    monkeypatch.setattr(allocation, "RESERVATIONS", [dict(allocation.RESERVATIONS[0], range=(top, top))])
    monkeypatch.setattr(allocation, "CONTESTED", {})
    problems = allocation.allocation_problems()
    assert any(top in p and "NOT recorded as contested" in p for p in problems), problems
    monkeypatch.setattr(allocation, "CONTESTED", {top: {"since": "t", "file": f"specs/{topfile}", "how": "", "awaits": ""}})
    assert allocation.allocation_problems() == []
    monkeypatch.undo()
    monkeypatch.setattr(allocation, "RESERVATIONS", [dict(allocation.RESERVATIONS[0], range=("0900", "0910"))])
    monkeypatch.setattr(allocation, "CONTESTED", {})
    assert allocation.allocation_problems() == []


def test_a_stale_contested_entry_is_refused(monkeypatch):
    """A contested entry whose file is gone, or whose reservation was
    released, is itself a defect — the registry must not carry a dead
    disclosure."""
    monkeypatch.setattr(allocation, "CONTESTED", {"0999": {"since": "x", "file": "specs/0999-x.md", "how": "", "awaits": ""}})
    assert any("stale" in p for p in allocation.allocation_problems())
    monkeypatch.undo()
    # a contested entry for a REAL file whose reservation has been released: stale too
    top = max(r["number"] for r in allocation.holders())
    topfile = [r["file"] for r in allocation.holders() if r["number"] == top][0]
    monkeypatch.setattr(allocation, "RESERVATIONS", [dict(allocation.RESERVATIONS[0], range=(top, top), released="2026-09-07 (test)")])
    monkeypatch.setattr(allocation, "CONTESTED", {top: {"since": "t", "file": f"specs/{topfile}", "how": "", "awaits": ""}})
    assert any("inside no live reservation" in p for p in allocation.allocation_problems())


def test_a_reservation_past_review_is_named_for_the_owner(monkeypatch):
    """A reservation is a claim about the future the tree cannot falsify, so it
    carries a review trigger; past it, the registry NAMES it (never releases
    it). Control: before the date, silence; a reservation without a trigger is
    itself a defect."""
    monkeypatch.setattr(allocation, "_today", lambda: "2099-01-01")
    assert any("PAST REVIEW" in p for p in allocation.allocation_problems())
    monkeypatch.setattr(allocation, "_today", lambda: "2026-09-06")
    assert not any("PAST REVIEW" in p for p in allocation.allocation_problems())
    monkeypatch.setattr(allocation, "RESERVATIONS", [dict(allocation.RESERVATIONS[0], review_by=None)])
    assert any("missing review_by" in p for p in allocation.allocation_problems())


def test_next_uncontested_skips_live_reservations():
    """The next number a new spec may take is one above the tree's highest
    (or the highest SPENT number, whichever is higher), stepped past every
    live reservation and every SPENT number — DERIVED here the same way, so
    the expectation is not a hand number that goes stale at the next
    allocation."""
    top = max([r["number"] for r in allocation.holders()] + list(allocation.SPENT))
    n = int(top) + 1
    while (any(x["range"][0] <= f"{n:04d}" <= x["range"][1] for x in allocation.RESERVATIONS if x.get("released") is None)
           or f"{n:04d}" in allocation.SPENT):
        n += 1
    nxt = allocation.next_uncontested()
    assert nxt == f"{n:04d}", nxt
    for x in allocation.RESERVATIONS:
        if x.get("released") is None:
            assert not (x["range"][0] <= nxt <= x["range"][1])


def test_a_spent_number_is_never_handed_out_again__with_its_controls(monkeypatch):
    """A number consumed by a proposal that never entered the tree (0040,
    withdrawn in the research tree on the owner's ruling, 2026-09-08) is
    SPENT: `next_uncontested()` skips it, a tree file taking it is refused as
    a reuse, and an entry without its ruling is refused. Rule zero: with the
    table emptied the same number is handed out — the table is doing the work."""
    top = max(r["number"] for r in allocation.holders())
    nxt = allocation.next_uncontested()
    assert nxt not in allocation.SPENT and nxt > top
    for n in allocation.SPENT:
        assert n not in {r["number"] for r in allocation.holders()}
    assert allocation.allocation_problems() == []
    # the control: without the table, the first free number above the tree is
    # handed out even if it was spent
    monkeypatch.setattr(allocation, "SPENT", {})
    bare = allocation.next_uncontested()
    monkeypatch.undo()
    assert bare <= nxt and (bare in allocation.SPENT or bare == nxt)
    assert "0040" in allocation.SPENT and bare == "0040"
    # a tree file holding a SPENT number is a reuse, refused by name
    monkeypatch.setattr(allocation, "SPENT", {top: dict(next(iter(allocation.SPENT.values())))})
    assert any(f"SPENT {top} is also held by" in p for p in allocation.allocation_problems())
    monkeypatch.undo()
    # an entry without its ruling is refused
    monkeypatch.setattr(allocation, "SPENT", {"0998": {"what": "x", "ruling": "", "record": "r", "spent_on": "2026-09-08"}})
    assert any("SPENT 0998: missing ruling" in p for p in allocation.allocation_problems())
    monkeypatch.undo()
