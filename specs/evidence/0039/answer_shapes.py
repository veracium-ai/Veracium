"""specs/0039 §2c-ii — the answer matrix's "today" column, MEASURED, not read.

Drives every provider answer shape the matrix names through the real
`ingest_event` with a scripted provider and prints the observable outcome:
the result's counters, or the exception class that escaped. The printed
transcript (`answer_shapes_transcript.txt` beside this file) is the "first
extraction, today" and "retry, today" columns of §2c-ii, and
tests/test_0039_answer_shapes.py asserts the script still prints it — so the
execution is KEPT, not repeated by hand, and a change in shipped behaviour
moves the transcript before it moves the spec.

Why this exists: v4 of the spec wrote "a non-list `triples` raises
AttributeError" from reading the loop; the round-1 reviewer ran it and three
of ten cells were silent. A sentence of the form input → outcome is produced
by running the input, and the run is committed.

# Mutation-Matrix: tests/test_0039_answer_shapes.py::test_the_answer_shape_transcript_is_the_scripts_output
"""
from __future__ import annotations

import json
import sys

from veracium.ingest import ingest_event
from veracium.schema import EvidenceAuthor, EvidenceContext
from veracium.store.sqlite import SqliteStore


class Stub:
    """A scripted provider: one answer for the first extraction, one for the retry."""

    def __init__(self, main_raw, retry_raw=None, retry_raises=None):
        self.main_raw, self.retry_raw, self.retry_raises = main_raw, retry_raw, retry_raises
        self.calls = []

    def __call__(self, prompt, **kw):
        self.calls.append(kw.get("role"))
        if kw.get("role") == "distill-retry":
            if self.retry_raises:
                raise self.retry_raises
            return self.retry_raw
        return self.main_raw


class MainRaises(Stub):
    def __call__(self, prompt, **kw):
        self.calls.append(kw.get("role"))
        if kw.get("role") != "distill-retry":
            raise RuntimeError("provider down")
        return self.retry_raw


def run(llm) -> str:
    s = SqliteStore(":memory:")
    try:
        r = ingest_event(s, llm, "u", event_text="I use Vim for editing.", author=EvidenceAuthor.USER,
                         date="2026-09-01", context=EvidenceContext.direct())
        return (f"RESULT facts={r['facts']} unparseable={r.get('unparseable', False)} "
                f"retried={r.get('retried')} recovered={r.get('recovered')} residual={r.get('residual')} calls={llm.calls}")
    except Exception as e:  # the outcome IS the escaping class; this is a measurement, not a handler
        return f"RAISES {type(e).__name__}: {str(e)[:60]!r} calls={llm.calls}"


GOOD = {"subject": "user", "relation": "uses_tool", "object": "Vim", "volatility": "durable"}
OFF = {"subject": "user", "relation": "no_such_relation", "object": "Vim", "volatility": "durable"}

PRIMARY = [
    ("valid non-empty list", json.dumps({"triples": [GOOD]})),
    ("valid empty list", json.dumps({"triples": []})),
    ("missing key", json.dumps({"note": "none"})),
    ("string", json.dumps({"triples": "user uses Vim"})),
    ("dictionary", json.dumps({"triples": {"subject": "user"}})),
    ("nested dictionary", json.dumps({"triples": {"triples": [GOOD]}})),
    ("null", json.dumps({"triples": None})),
    ("number", json.dumps({"triples": 3})),
    ("boolean", json.dumps({"triples": True})),
    ("bare array of dicts", json.dumps([GOOD])),
    ("bare array of scalars", json.dumps(["triples", 1])),
    ("list with malformed members", json.dumps({"triples": [GOOD, "junk", 7, None]})),
    ("list of empty dicts", json.dumps({"triples": [{}, {}]})),
    ("non-object top-level: string", json.dumps("hello")),
    ("non-object top-level: number", "42"),
    ("prose", "I cannot help with that."),
    ("instructions wrong type", json.dumps({"triples": [GOOD], "instructions": "x"})),
]
RETRY = [
    ("raising", None, RuntimeError("boom")),
    ("prose", "cannot", None),
    ("bare array of dicts", json.dumps([GOOD]), None),
    ("bare array of scalars", json.dumps(["triples"]), None),
    ("triples not a list (string)", json.dumps({"triples": "x"}), None),
    ("triples not a list (dict)", json.dumps({"triples": {}}), None),
    ("triples null", json.dumps({"triples": None}), None),
    ("triples number", json.dumps({"triples": 3}), None),
    ("no triples key", json.dumps({"repairs": [GOOD]}), None),
    ("triples empty list", json.dumps({"triples": []}), None),
    ("list of dicts (recovery)", json.dumps({"triples": [GOOD]}), None),
    ("list with malformed members", json.dumps({"triples": [GOOD, "junk", 7, None]}), None),
    ("non-object top-level: number", "42", None),
    ("instructions as a string", json.dumps({"triples": [GOOD], "instructions": "x"}), None),
    ("instructions as a list", json.dumps({"triples": [GOOD], "instructions": ["do x"]}), None),
]


def transcript() -> str:
    out = ["=== PRIMARY answer shapes (the retry answer fixed to a valid empty object) ==="]
    for name, raw in PRIMARY:
        out.append(f"  {name:32} -> {run(Stub(raw, retry_raw=json.dumps({'triples': []})))}")
    out.append("  primary call raises              -> " + run(MainRaises("", retry_raw=json.dumps({"triples": []}))))
    out.append("=== RETRY answer shapes (the primary carries ONE off-vocabulary triple to trigger the retry) ===")
    main = json.dumps({"triples": [OFF]})
    for name, raw, exc in RETRY:
        out.append(f"  {name:32} -> {run(Stub(main, retry_raw=raw, retry_raises=exc))}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.stdout.write(transcript())
