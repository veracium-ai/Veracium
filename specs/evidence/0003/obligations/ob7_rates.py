#!/usr/bin/env python3
"""0003/obligations INV-OB7 (0003 §4c-v.8): the extractor's measured rates under §4c-v.6a, at the pinned extractor.

An acceptance measurement of a model, not a proof. Each probe runs n=3 through `Memory.remember` with the reference
provider (`veracium.llm.anthropic.AnthropicComplete`, its default distill model), a fresh store per trial, and reports
per probe, never pooled (research S1-3):

- `subject_not_user`: every `deadline` triple names the obligation, not `user`;
- `iso_object`: the object is the ISO date the event means (P1–P3) — P3 is the RIGHT-YEAR probe ("January 5" said
  on 2025-12-20 is 2026-01-05; an event date may not be in the future);
- `no_fabrication` (P4, P5): the date has no stated day, or is relative and outside the calendar, so an ISO object is
  the FAILURE;
- `both_active` (P1): the two obligations coexist after the second statement;
- `no_phantom` (P6, research S1-5): a PAST stated date ("I had my dentist appointment on October 12", said on
  2026-10-20) never becomes a commitment after the event's day (the rule's "next such date" would make it 2027-10-12).

`--superseded-year-wording` measures the rule's FIRST year clause ("written with the year the event means"), patched
into `veracium.prompts.EXTRACT_PROMPT` for this process only, and writes `ob7-rates-superseded-wording.json`: the
wording change's evidence (research S1-6). The first run under that wording was overwritten by the second; that file
is a later, labelled re-measurement, not the first run.

    PYTHONPATH=src $PY specs/evidence/0003/obligations/ob7_rates.py [--superseded-year-wording]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "ob7-rates.json"
OUT_SUPERSEDED = HERE / "ob7-rates-superseded-wording.json"
STATED = ('; a stated date\n  with no year ("November 12") is the next such date on or after the day the\n'
          '  event occurred, unless the event says which year.')
SUPERSEDED = (', a stated date\n  ("November 12") written with the year the event means.')
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
N = 3

PROBES = [
    ("P1-two-appointments", [("2026-10-29", "USER: I have a dentist appointment on November 12."),
                             ("2026-10-29", "USER: I have a haircut appointment on November 20.")],
     {"iso": ["2026-11-12", "2026-11-20"], "both_active": True}),
    ("P2-stated-date", [("2026-11-01", "USER: My lease renewal is due November 30.")], {"iso": ["2026-11-30"]}),
    ("P3-right-year", [("2025-12-20", "USER: I have a dentist appointment on January 5.")], {"iso": ["2026-01-05"]}),
    ("P4-no-stated-day", [("2026-10-20", "USER: I need to renew my passport sometime in November.")],
     {"no_fabrication": True}),
    ("P5-relative-outside-calendar", [("2026-11-01", "USER: My tax filing is due in three weeks.")],
     {"no_fabrication": True}),
    ("P6-past-stated-date", [("2026-10-20", "USER: I had my dentist appointment on October 12.")],
     {"no_phantom_after": "2026-10-20"}),
]


def trial(texts):
    from veracium import EvidenceContext, Memory, MemoryConfig
    from veracium.llm.anthropic import AnthropicComplete
    with tempfile.TemporaryDirectory() as d:
        m = Memory(llm=AnthropicComplete(), config=MemoryConfig(require_source_id=False, db_path=f"{d}/t.db",
                                                                 wiki_recompile_after_writes=0))
        for day, text in texts:
            m.remember("u", text, date=day, context=EvidenceContext.direct())
        es = [e for e in m.store.edges("u", active_only=False, include_quarantined=True) if e.relation == "deadline"]
        m.close()
        return [{"subject": e.subject, "object": e.object, "active": e.active} for e in es]


def score(expect, edges):
    s = {"deadline_triples": len(edges),
         "subject_not_user": bool(edges) and all(e["subject"] != "user" for e in edges)}
    if "iso" in expect:
        s["iso_object"] = sorted(e["object"] for e in edges) == sorted(expect["iso"])
    if expect.get("both_active"):
        s["both_active"] = sum(1 for e in edges if e["active"]) == 2
    if expect.get("no_fabrication"):
        s["no_fabrication"] = not any(ISO.match(e["object"]) for e in edges)
    if expect.get("no_phantom_after"):
        s["subject_not_user"] = all(e["subject"] != "user" for e in edges)      # no triple at all is not a failure
        s["no_phantom"] = not any(ISO.match(e["object"]) and e["object"] > expect["no_phantom_after"] for e in edges)
    return s


def main() -> int:
    from veracium import prompts
    from veracium.llm.anthropic import DEFAULT_MODELS
    superseded = "--superseded-year-wording" in sys.argv
    assert prompts.EXTRACT_PROMPT.count(STATED) == 1, "the stated year clause is not in the prompt this tree sends"
    if superseded:
        prompts.EXTRACT_PROMPT = prompts.EXTRACT_PROMPT.replace(STATED, SUPERSEDED)
    out = OUT_SUPERSEDED if superseded else OUT
    rows = []
    for pid, texts, expect in PROBES:
        trials = []
        for _ in range(N):
            edges = trial(texts)
            trials.append({"edges": edges, "score": score(expect, edges)})
        keys = [k for k in trials[0]["score"] if k != "deadline_triples"]
        rates = {k: f"{sum(1 for t in trials if t['score'][k])}/{N}" for k in keys}
        rows.append({"probe": pid, "texts": texts, "expect": expect, "rates": rates, "trials": trials})
        print(pid, rates)
    out.write_text(json.dumps({"invariant": "INV-OB7", "spec": "0003 §4c-v", "n": N,
                               "extractor_pin": f"{DEFAULT_MODELS.get('distill')} (veracium.llm.anthropic."
                                                f"DEFAULT_MODELS['distill'], the reference provider's distill default)",
                               "year_clause": "superseded: written with the year the event means" if superseded
                               else "stated: the next such date on or after the day the event occurred",
                               "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                               "probes": rows}, indent=2) + "\n")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
