#!/usr/bin/env python3
"""specs/0031 §4f, INV-TT5 and INV-TT23 (TT-R3-04 D): the controlled LEGACY BYTES a host call with every new keyword
absent must reproduce. One generator, run under two builds: the released wheel immediately before §4f (v0.32.1, whose
output is the committed baseline `legacy/v0.32.1.json`) and the tree under test (the test compares the two).

Each case is a fresh store with one planted USER edge, then ONE host verb with today's arguments only: `correct`,
`dispute`, `confirm`. Ids and clocks are controlled (a counter for `uuid4`, one held instant for every veracium
module's `datetime`), so two runs of one build are identical. Recorded per case: the verb's return value, every row
of every table (sqlite `iterdump`), and the bytes of `export_memory`. The return value is kept as its canonical JSON
text (sorted keys), never re-parsed.

    python legacy_bytes.py --emit            # this build's bytes, JSON on stdout (the import path picks the build)

The baseline was made by installing the PyPI wheel `veracium==0.32.1` into a fresh venv and running this file with
that venv's interpreter and no PYTHONPATH; the wheel's name and sha256 are recorded inside the baseline.
"""
from __future__ import annotations

import datetime as _dt
import importlib.metadata
import itertools
import json
import pathlib
import sys
import tempfile
import uuid

HELD = _dt.datetime(2026, 11, 1, 12, 0, 0, tzinfo=_dt.timezone.utc)
U = "u"
CASES = ("correct", "dispute", "confirm")


class _AnyDatetime(type):
    """isinstance(x, _Held) holds for every real datetime, so a module whose `datetime` name is held still accepts
    the datetimes it parses (freezegun's construction)."""
    def __instancecheck__(cls, obj):
        return isinstance(obj, _dt.datetime)


class _Held(_dt.datetime, metaclass=_AnyDatetime):
    @classmethod
    def now(cls, tz=None):
        return HELD if tz is not None else HELD.replace(tzinfo=None)

    @classmethod
    def utcnow(cls):
        return HELD.replace(tzinfo=None)


def _control():
    """Hold every clock and id source the verbs read. Returns the undo list."""
    import importlib
    import pkgutil
    import veracium
    for info in pkgutil.walk_packages(veracium.__path__, "veracium."):   # load every module first: a lazily imported
        try:                                                              # one would read the real clock
            importlib.import_module(info.name)
        except ImportError:                                               # an optional extra this build lacks
            pass
    undo = []
    counter = itertools.count(1)
    fake = lambda: uuid.UUID(int=next(counter))           # noqa: E731
    undo.append((uuid, "uuid4", uuid.uuid4))
    uuid.uuid4 = fake
    for name, mod in list(sys.modules.items()):
        if not (name == "veracium" or name.startswith("veracium.")) or mod is None:
            continue
        if getattr(mod, "datetime", None) is _dt.datetime:
            undo.append((mod, "datetime", _dt.datetime))
            mod.datetime = _Held
        if getattr(mod, "uuid4", None) is not None and getattr(mod, "uuid4") is undo[0][2]:
            undo.append((mod, "uuid4", undo[0][2]))
            mod.uuid4 = fake
    return undo


def run_case(case: str, kw: dict | None = None) -> dict:
    from veracium import Memory, MemoryConfig
    from veracium.schema import Edge, EvidenceAuthor, Provenance
    kw = kw or {}
    with tempfile.TemporaryDirectory() as d:
        undo = _control()
        try:
            m = Memory(llm=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no model call")),
                       config=MemoryConfig(db_path=str(pathlib.Path(d) / "v.db"), require_source_id=False,
                                           wiki_recompile_after_writes=0))
            m.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="likes", object="tea",
                                  valid_from=HELD, provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                                         evidence_ref="ev-e-1", observed_at=HELD)))
            ret = {"correct": lambda: m.correct(U, "e-1", "coffee", date="2026-11-01", **kw),
                   "dispute": lambda: m.dispute(U, "e-1", reason="not so", **kw),
                   "confirm": lambda: m.confirm(U, "e-1", date="2026-11-01", **kw)}[case]()
            rows = list(m.store._conn.iterdump())
            out = pathlib.Path(d) / "export.jsonl"
            m.export_memory(U, out)
            export = out.read_text(encoding="utf-8")
            m.close()
        finally:
            for obj, attr, val in reversed(undo):
                setattr(obj, attr, val)
    return {"return": json.dumps(ret, default=str, sort_keys=True), "rows": rows, "export": export}   # canonical text


def emit() -> dict:
    return {"veracium": importlib.metadata.version("veracium"), "cases": {c: run_case(c) for c in CASES}}


if __name__ == "__main__":
    if "--emit" in sys.argv:
        json.dump(emit(), sys.stdout, indent=1, sort_keys=True)
        sys.stdout.write("\n")
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
