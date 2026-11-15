"""The amendments reviewer, round 9, F2 (2026-09-14; a pre-existing defect,
fixed beside 0037 v24.5): `remember`, `dispute`, `confirm`, `record_outcome`
and `correct` — the five paths that default an omitted event date — used the
host's LOCAL calendar date, while ingestion reads a bare date as UTC midnight
(`_event_dt`). On a runtime whose local date runs ahead of UTC — the
reviewer's, at 22:01 UTC — a routine was stored with tomorrow's `valid_from`
and withheld as `not_yet_valid` until UTC midnight. One clock now: the default
is the UTC calendar date the reading uses.

The round-10 reviewer's two follow-ups are both here: the regression drives
`remember()` DIRECTLY (the first version went through a helper that called
`record_procedure()`, whose default was already UTC — an instrument that could
not exhibit the defect), with an explicit-date control beside it; and the
process timezone is restored by putting the ORIGINAL variable back before
`time.tzset()`, so later tests see the variable and the clock agree.

The boundary is exercised, not assumed: the zones fourteen hours ahead of and
twelve hours behind UTC are tried, the test asserts the zone's LOCAL date
differs from the UTC date at the moment of the run (at every hour of the day at
least one of the two does; the other skips, inventoried), and only then
records. Under the old default the stored date was the local one, which fails
on either side of the boundary.
"""

import contextlib
import importlib.util
import json
import os
import pathlib
import time

import pytest

from veracium import Memory, MemoryConfig, _today_utc
from veracium.schema import EvidenceContext, utcnow


def _module(name):
    path = pathlib.Path(__file__).with_name(name)
    spec = importlib.util.spec_from_file_location(name[:-3] + "_base", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = _module("test_0037_procedural.py")
U = base.U
ZONES = ["Etc/GMT-14", "Etc/GMT+12"]          # POSIX signs: Etc/GMT-14 is UTC+14, Etc/GMT+12 is UTC-12
TEXT = "Any tips for keeping a repo tidy? I run the formatter before committing, every time."


def _llm(prompt, *, system=None, role="compile", json_schema=None):
    """A distill answer carrying one routine with its verbatim quote (the
    0037 capture gate admits it); nothing else."""
    if role == "distill":
        return json.dumps({"triples": [{"subject": "user", "relation": "follows_procedure",
                                        "object": "Runs the formatter",
                                        "quote": "I run the formatter before committing, every time"}],
                           "episode": "x", "instructions": []})
    return json.dumps({"triples": [], "episode": "x", "instructions": []})


@contextlib.contextmanager
def _under_zone(zone):
    """Set TZ for the process, and on exit put the ORIGINAL variable back
    BEFORE tzset() (the round-10 reviewer: tzset() before pytest's own restore
    left the clock and the variable disagreeing for every later test)."""
    original = os.environ.get("TZ")
    os.environ["TZ"] = zone
    time.tzset()
    try:
        yield
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        time.tzset()
        assert os.environ.get("TZ") == original


def _boundary_or_skip(zone):
    utc_date = utcnow().date().isoformat()
    local_date = time.strftime("%Y-%m-%d")
    if local_date == utc_date:
        pytest.skip(f"{zone}'s local date equals the UTC date at this hour; the other zone carries the boundary")
    return utc_date, local_date


def _memory(tmp_path, name):
    return Memory(llm=_llm, config=MemoryConfig(db_path=str(tmp_path / name), wiki_recompile_after_writes=0,
                                                 scope_groups={}, require_source_id=False))


@pytest.mark.parametrize("zone", ZONES)
def test_remember_with_no_date_stores_the_utc_date_on_both_sides_of_the_local_boundary(tmp_path, zone):
    """The original public call, directly: `remember()` with NO date under a
    zone whose local date differs from UTC's stores today's UTC date, never a
    future one, and the routine is describable at once — not `not_yet_valid`."""
    with _under_zone(zone):
        utc_date, local_date = _boundary_or_skip(zone)
        assert _today_utc() == utc_date
        mem = _memory(tmp_path, f"remember-{zone.replace('/', '_')}.db")
        mem.remember(U, TEXT, context=EvidenceContext.direct())
        edges = mem.store.edges(U, active_only=False, include_quarantined=True)
        assert len(edges) == 1, [e.id for e in edges]
        edge = edges[0]
        assert edge.valid_from.date().isoformat() == utc_date, (edge.valid_from, local_date, utc_date)
        assert edge.valid_from <= utcnow()
        r = mem.describe_procedures(U)
        assert r.total_describable == 1 and r.descriptions[0].edge_id == edge.id, (r.withheld, local_date, utc_date)
        assert not [w for w in r.withheld if w.outcome == "not_yet_valid"]
        mem.close()


@pytest.mark.parametrize("zone", ZONES)
def test_remember_with_an_explicit_date_is_untouched_by_the_zone(tmp_path, zone):
    """The control: an explicit date is the event's own date whatever the
    zone — today's UTC date lands as today, a past date lands as that day."""
    with _under_zone(zone):
        utc_date, _ = _boundary_or_skip(zone)
        mem = _memory(tmp_path, f"explicit-{zone.replace('/', '_')}.db")
        mem.remember(U, TEXT, date=utc_date, context=EvidenceContext.direct())
        mem.remember("someone-else", TEXT, date="2026-06-01", context=EvidenceContext.direct())
        today = mem.store.edges(U, active_only=False, include_quarantined=True)
        past = mem.store.edges("someone-else", active_only=False, include_quarantined=True)
        assert [e.valid_from.date().isoformat() for e in today] == [utc_date]
        assert [e.valid_from.date().isoformat() for e in past] == ["2026-06-01"]
        assert mem.describe_procedures(U).total_describable == 1
        mem.close()


def test_the_zone_is_restored_before_the_clock_is_reset():
    """Follow-up 2: after the context manager exits, the variable and the
    process clock agree again (the variable put back first, then tzset)."""
    before_env, before_local = os.environ.get("TZ"), time.strftime("%Y-%m-%d %H:%M", time.localtime(0))
    with _under_zone("Etc/GMT-14"):
        assert os.environ.get("TZ") == "Etc/GMT-14" and time.strftime("%H:%M", time.localtime(0)) == "14:00"
    assert os.environ.get("TZ") == before_env
    assert time.strftime("%Y-%m-%d %H:%M", time.localtime(0)) == before_local


def test_every_omitted_date_default_uses_the_utc_clock():
    """No path defaults a date from the local calendar: no `.today()` survives
    in the package, and the five defaulting methods are exactly `remember`,
    `dispute`, `confirm`, `record_outcome` and `correct` (the round-10
    reviewer's list, derived here from the call sites rather than recalled)."""
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "veracium"
    hits = [(p.name, i + 1) for p in src.rglob("*.py")
            for i, line in enumerate(p.read_text().splitlines()) if ".today()" in line]
    assert hits == [], hits
    text = (src / "__init__.py").read_text()
    assert "utcnow().date().isoformat()" in text
    import ast
    tree = ast.parse(text)
    callers = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) == "_today_utc":
                    callers.add(node.name)
    # specs/0031 §4f §3b: the scope gate dates its binding-source PROBE (a never-written episode) by the UTC clock too
    assert callers == {"remember", "dispute", "confirm", "record_outcome", "correct", "_trust_scope_gate"}, callers


def _local_calendar_calls(tree):
    """`<x>.today()` (date.today, datetime.today) and an argument-less `datetime.now()`: each reads the LOCAL calendar."""
    import ast
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "today" and not node.args and not node.keywords:
                out.append(node.lineno)
            elif node.func.attr == "now" and not node.args and not node.keywords:
                out.append(node.lineno)
    return out


def test_no_test_fixture_takes_its_date_from_the_local_calendar():
    """The package's guard above covers src/ only, and a fixture in tests/ did exactly this: the round-10 readers'
    `TODAY = date.today()` dated an episode by the LOCAL calendar while `Episode.valid_now` compares the UTC date, so the
    control failed wherever the local date was ahead of UTC (0048 round 1, R1-05, reproduced under Australia/Brisbane).
    Every test module is parsed; a local-calendar call anywhere in tests/ is refused."""
    import ast
    tests = pathlib.Path(__file__).resolve().parent
    hits = [(p.name, ln) for p in sorted(tests.rglob("*.py")) for ln in _local_calendar_calls(ast.parse(p.read_text()))]
    assert hits == [], hits


def test_the_round10_readers_fixture_dates_by_utc_on_both_sides_of_the_date_line():
    """R1-05's boundary regression: the fixture module is imported afresh in a zone AHEAD of UTC (Etc/GMT-14) and one
    BEHIND it (Etc/GMT+12). At any instant the local date differs from the UTC date in at least one of them, so a fixture
    reading the local calendar fails here whatever the hour; the one reading UTC passes in both."""
    import importlib.util
    from datetime import datetime, timezone
    path = pathlib.Path(__file__).resolve().parent / "test_0041_round10_readers.py"
    differs = []
    for zone in ("Etc/GMT-14", "Etc/GMT+12"):
        with _under_zone(zone):
            import datetime as _dt
            differs.append(_dt.date.fromtimestamp(time.time()).isoformat() != datetime.now(timezone.utc).date().isoformat())
            spec = importlib.util.spec_from_file_location(f"r10_readers_{zone.replace('/', '_').replace('-', 'm').replace('+', 'p')}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert mod.TODAY == datetime.now(timezone.utc).date().isoformat(), (zone, mod.TODAY)
    assert any(differs), "neither zone's local date differed from UTC — the regression would have no teeth"
