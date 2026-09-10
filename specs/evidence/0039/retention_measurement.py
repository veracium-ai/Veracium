"""specs/0039 §7 — the RETENTION measurement, the figures the spec sends to the
CHANGELOG. §7 states no numbers on purpose: "the figures to quote are the DERIVED
ones — records per window, and events to evict a traceback at a stated degrade rate —
measured at implementation from the record's actual size". This is that measurement,
run against the shipped path (a real `Memory` with a real `Reporter`, the record read
back off the log file), so the CHANGELOG's range is a re-derivation and not a recall.

The window is the reporter's own rotation configuration, read from the shipped
constant rather than restated here.
"""
# Mutation-Matrix: tests/test_0039_degradation_visibility.py::test_the_retention_figures_are_measured_not_recalled
from __future__ import annotations

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from answer_shapes import GOOD, OFF, Stub  # noqa: E402

from veracium import Memory, MemoryConfig  # noqa: E402
from veracium.diagnostics import DiagnosticsConfig, Reporter  # noqa: E402

WINDOW_BYTES = 3_000_000  # maxBytes=1_000_000 with backupCount=2: the active file + 2

_M = lambda triples: json.dumps({"triples": triples})  # noqa: E731

#: The ten records measured — every one of the five degrade KINDS, and for the
#: kinds whose record shape varies by `cause`, every shape the vocabulary allows
#: at a site (§2c). Ordered as the transcript prints them.
CASES = [
    ("member_skipped", _M([GOOD, "junk"]), _M([]), None),
    ("volatility_defaulted", _M([dict(GOOD, volatility="banana")]), _M([]), None),
    ("unparseable/no_json", "prose, not json at all", _M([]), None),
    ("retry_failed/no_json", _M([OFF]), "prose, not json", None),
    ("retry_failed/provider_error", _M([OFF]), None, RuntimeError("provider unavailable")),
    ("primary_failed/shape (string)", json.dumps({"triples": "a string"}), _M([]), None),
    ("primary_failed/shape (null)", json.dumps({"triples": None}), _M([]), None),
    ("primary_failed/shape (number)", json.dumps({"triples": 7}), _M([]), None),
    ("primary_failed/shape (boolean)", json.dumps({"triples": True}), _M([]), None),
    ("primary_failed/no_triples_key", json.dumps({"note": "none"}), _M([]), None),
]


def _error_record(tmp) -> tuple:
    """An ERROR record, for the comparison §7's retention question needs. Until the
    2026-09-10 amendment this came free with three of the rows below: a `null`,
    numeric or boolean `triples` wrote its degrade record and then raised `TypeError`
    from the loop. The wider normalization rule removed that raise, so the error
    record is now produced the way an error record is normally produced -- a provider
    that fails on the FIRST call, which `remember` records with its traceback and
    re-raises."""
    class _Boom(Exception):
        pass
    log = pathlib.Path(tmp) / "err.log"
    rep = Reporter(DiagnosticsConfig(log_path=str(log), report_enabled=False))
    def raiser(*a, **k):
        raise _Boom("provider unavailable")
    mem = Memory(llm=raiser,
                 config=MemoryConfig(db_path=str(pathlib.Path(tmp) / "err.db"),
                                     wiki_recompile_after_writes=0),
                 diagnostics=rep)
    try:
        mem.remember("alice", "I use Vim for editing.")
    except Exception:                                         # noqa: BLE001
        pass
    lines = [l for l in log.read_text().splitlines() if l.strip()]
    assert lines and " degrade=" not in lines[0], lines[:1]
    whole = "\n".join(lines) + "\n"
    return len(whole.encode()), len(lines)


def _one(tmp, name, raw, retry_raw, retry_raises):
    log = pathlib.Path(tmp) / f"{name}.log"
    rep = Reporter(DiagnosticsConfig(log_path=str(log), report_enabled=False))
    mem = Memory(llm=Stub(raw, retry_raw=retry_raw, retry_raises=retry_raises),
                 config=MemoryConfig(db_path=str(pathlib.Path(tmp) / f"{name}.db"),
                                     wiki_recompile_after_writes=0),
                 diagnostics=rep)
    raised = None
    try:
        mem.remember("alice", "I use Vim for editing.")
    except Exception as e:                                    # noqa: BLE001
        raised = type(e).__name__
    lines = [l for l in log.read_text().splitlines() if l.strip()]
    degrade = [l for l in lines if " degrade=" in l]
    error = [l for l in lines if " degrade=" not in l]
    # the handler writes one newline per line; a traceback is ONE record over many lines
    return (len(degrade[0].encode()) + 1 if degrade else None,
            len("\n".join(error).encode()) + 1 if error else None,
            len(error), raised)


def measure() -> dict:
    """Run every case and return the measured table. Pure measurement: no figure
    in this module is written down, all of them are read off the log."""
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (name, raw, retry_raw, retry_raises) in enumerate(CASES):
            d, e, elines, raised = _one(tmp, f"c{i}", raw, retry_raw, retry_raises)
            rows.append({"case": name, "degrade_bytes": d, "error_bytes": e,
                         "error_lines": elines, "raised": raised})
        err_bytes, err_lines = _error_record(tmp)
    sizes = [r["degrade_bytes"] for r in rows]
    return {
        "rows": rows,
        "smallest": min(sizes), "largest": max(sizes),
        "records_at_largest": WINDOW_BYTES // max(sizes),
        "records_at_smallest": WINDOW_BYTES // min(sizes),
        # environment-dependent, deliberately NOT rendered into the transcript
        "error_record_bytes": err_bytes, "error_record_lines": err_lines,
        "window_bytes": WINDOW_BYTES,
    }


def render(m: dict) -> str:
    """The STABLE section, and only it. A degrade record's size is fixed by the
    record's own grammar, so it reproduces anywhere. An ERROR record's size is not
    ours: it carries a traceback, whose length depends on the interpreter's format
    and on the absolute source paths of the checkout it was taken in (measured
    across CI: 7 lines on 3.10, 8 on 3.11, 9 and 12 on longer-path 3.12/3.13 jobs).
    Pinning it would bind this evidence to one machine, so the error record is
    asserted by PROPERTY in the matrix test instead of by byte count here."""
    out = ["# specs/0039 §7 — the retention measurement, run against the shipped path.",
           "# Regenerate with: python specs/evidence/0039/retention_measurement.py",
           "# Bound by tests/test_0039_degradation_visibility.py::"
           "test_the_retention_figures_are_measured_not_recalled, which re-runs this",
           "# measurement and refuses a CHANGELOG figure that is not the measured one.",
           "# Degrade-record sizes only: an error record's size is the interpreter's",
           "# traceback format and the checkout's path lengths, not a fact about",
           "# veracium, so it is asserted as a property (>= 3x a degrade record, a",
           "# multi-line traceback) rather than pinned here.",
           "#"]
    for r in m["rows"]:
        raised = "" if not r["raised"] else f"   (the operation then raised {r['raised']})"
        out.append(f"{r['degrade_bytes']:5d} bytes  {r['case']}{raised}")
    assert not any(r["raised"] for r in m["rows"]), (
        "a row raised: since the 2026-09-10 normalization amendment no provider ANSWER "
        "shape raises out of ingest, and a row that does is a finding, not a render")
    out += [
        "",
        f"degrade record: {m['smallest']}-{m['largest']} bytes over "
        f"{len(m['rows'])} records spanning all five degrade kinds",
        f"window: {m['window_bytes']:,} bytes -> {m['records_at_largest']:,} records at "
        f"the largest size, {m['records_at_smallest']:,} at the smallest",
    ]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print(render(measure()), end="")
