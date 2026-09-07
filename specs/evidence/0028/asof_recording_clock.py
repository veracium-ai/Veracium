"""specs/0028 §9 — the RECORDING CLOCK, a pytest plugin (the behavioural form of
the absence proof over `classify_as_of` as shipped).

Installs, for the whole pytest session it is loaded into, wrappers on the four
wall-clock-reading predicates — `Edge.valid_now`, `Edge.assertable`,
`Episode.valid_now`, `Episode.assertable` (schema.py) — that count every
access and, for each access, walk the Python call stack looking for a frame
whose code object is `classify_as_of` or `assertable_as_of`, or whose file
lives under `src/veracium/asof/`. An access WITH such a frame on the stack is
a VIOLATION: the as-of branch reached a predicate that reads the process
clock. An access without one is ordinary product behaviour and is counted
only so the report can show the clock was live (a wrapper that never fires
proves nothing about anything).

A profile hook counts calls to `classify_as_of`'s code object on the thread
that runs the tests, so the report also states HOW MANY classifications the
run exercised — the proof is vacuous at zero and must fail there. The counts
are written as JSON to the path in `ASOF_CLOCK_REPORT` at session end.

Load with `-p asof_recording_clock` from a PYTHONPATH containing this
directory. `check_asof_absence.py` does exactly that over
`tests/test_0030_asof.py`, the shipped as-of test surface — every rule path
of the classifier has a test there, so the run exercises each return.

COVERED FRACTION (say it here because the JSON will be read alone): this
watches the SHIPPED as-of code. The resolution 0028 specifies —
`facts_valid_at`, `read_window`, `edges_superseding` — is unwritten, and no
frame of it can appear on any stack. Its own proof is owed at implementation.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import threading

WATCHED = (("Edge", "valid_now"), ("Edge", "assertable"),
           ("Episode", "valid_now"), ("Episode", "assertable"))
_COUNTS = {"accesses": 0, "violations": 0, "classify_calls": 0,
           "by_predicate": {}, "violation_sites": []}
_ASOF_CODES = set()
_ASOF_DIR = None
_LOCK = threading.Lock()


def _stack_has_asof_frame():
    f = sys._getframe(2)
    while f is not None:
        if f.f_code in _ASOF_CODES:
            return f.f_code.co_name
        fn = f.f_code.co_filename
        if _ASOF_DIR and fn.startswith(_ASOF_DIR):
            return f"{pathlib.Path(fn).name}:{f.f_code.co_name}"
        f = f.f_back
    return None


def _wrap(cls, name):
    original = cls.__dict__[name]          # the property object itself
    assert isinstance(original, property), (cls, name)
    key = f"{cls.__name__}.{name}"

    def getter(self):
        with _LOCK:
            _COUNTS["accesses"] += 1
            _COUNTS["by_predicate"][key] = _COUNTS["by_predicate"].get(key, 0) + 1
            site = _stack_has_asof_frame()
            if site is not None:
                _COUNTS["violations"] += 1
                _COUNTS["violation_sites"].append({"predicate": key, "asof_frame": site})
        return original.fget(self)
    setattr(cls, name, property(getter, original.fset, original.fdel, original.__doc__))
    return original


def _profile(frame, event, arg):
    if event == "call" and frame.f_code in _CLASSIFY_CODES:
        with _LOCK:
            _COUNTS["classify_calls"] += 1


_CLASSIFY_CODES = set()
_ORIGINALS = []


def pytest_configure(config):
    global _ASOF_DIR
    from veracium import schema
    from veracium.asof import classify
    _ASOF_DIR = str(pathlib.Path(classify.__file__).resolve().parent) + os.sep
    _ASOF_CODES.update({classify.classify_as_of.__code__, classify.assertable_as_of.__code__})
    _CLASSIFY_CODES.add(classify.classify_as_of.__code__)
    for cname, pname in WATCHED:
        _ORIGINALS.append((getattr(schema, cname), pname, _wrap(getattr(schema, cname), pname)))
    sys.setprofile(_profile)
    threading.setprofile(_profile)


def pytest_unconfigure(config):
    sys.setprofile(None)
    threading.setprofile(None)
    for cls, name, original in _ORIGINALS:
        setattr(cls, name, original)
    out = os.environ.get("ASOF_CLOCK_REPORT")
    if out:
        pathlib.Path(out).write_text(json.dumps(_COUNTS, indent=1))
