# Landed under specs/evidence/0039/ by dev on 2026-09-10 from research's
# proposals tree (research commit d3fbd990), with research's attribution and
# THREE declared deltas: this header; the `# Mutation-Matrix:` pointer below;
# and the removal of one `sys.path.insert` line that named an absolute local
# path (the package is importable from the venv). Nothing else changed. NOTE the
# consequence: the script now tests whatever `veracium` the interpreter resolves —
# in this repo's venv an editable install of the working tree, in a fresh
# environment possibly a released wheel — so the transcript's pin is asserted
# by the test beside it, not guaranteed by the script. It is
# NOT self-contained: it imports from the product tree, so its transcript
# answers for the pin it was generated against (749e122) and a run at another
# pin answers a different question — which is exactly what the test beside it
# asserts. It was deliberately not built on dev's answer_shapes.py; the
# agreement between the two instruments counts as evidence only because of that.
# Mutation-Matrix: tests/test_0039_answer_shapes.py::test_researchs_independent_instrument_still_prints_its_transcript
"""RESEARCH's independent shape matrix for 0039 v8's red team.

Deliberately NOT dev's answer_shapes.py: the instrument that checks a spec must
not share the assumptions of the seat that wrote it. Two instruments, one table.

Every row is REAL `ingest_event` against a scripted provider, not a simulation
of the loop. The output is the ground truth any "input -> outcome" sentence in
v8 must be checked against.
"""
import json, sys, tempfile, traceback
from veracium.ingest import ingest_event
from veracium import SqliteStore
from veracium.schema import EvidenceAuthor

VALID = {"subject": "user", "relation": "has_diet", "object": "avoids dairy",
         "volatility": "durable"}

class Scripted:
    """First call returns the PRIMARY shape; any later call (the retry) returns
    the RETRY shape. `raw` values are returned verbatim as the provider's text."""
    def __init__(self, primary, retry='{"triples": []}'):
        self.primary, self.retry, self.n = primary, retry, 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        self.n += 1
        return self.primary if self.n == 1 else self.retry

def run(primary, retry='{"triples": []}'):
    with tempfile.TemporaryDirectory() as d:
        store = SqliteStore(f"{d}/m.db")
        try:
            r = ingest_event(store, Scripted(primary, retry), "u",
                             event_text="the deploy succeeded",
                             author=EvidenceAuthor.USER, date="2026-09-09")
            return ("returns", {k: r.get(k) for k in
                                ("facts","unparseable","invalid","retried",
                                 "recovered","residual")})
        except Exception as e:
            return ("raises", f"{type(e).__name__}: {str(e)[:60]}")
        finally:
            try: store.close()
            except Exception: pass

PRIMARY = [
 ("P valid non-empty",      json.dumps({"triples":[VALID]})),
 ("P valid empty",          '{"triples": []}'),
 ("P missing key",          '{"note": "nothing found"}'),
 ("P triples string",       '{"triples": "abc"}'),
 ("P triples dict",         '{"triples": {"a": 1}}'),
 ("P triples null",         '{"triples": null}'),
 ("P triples number",       '{"triples": 5}'),
 ("P triples bool",         '{"triples": true}'),
 ("P bare array of dicts",  json.dumps([VALID])),
 ("P bare array scalars",   '["a", "b"]'),
 ("P top-level number",     '42'),
 ("P top-level string",     '"hello"'),
 ("P prose, no JSON",       'I cannot help with that request.'),
 ("P instructions string",  json.dumps({"triples":[VALID], "instructions":"x"})),
 ("P mixed member types",   json.dumps({"triples":[VALID, "junk", 7, None]})),
 ("P empty dict members",   json.dumps({"triples":[{}, {}]})),
 ("P nested triples",       json.dumps({"triples":{"triples":[VALID]}})),
]
print(f"  {'primary answer shape':24s} {'outcome':52s}")
print(f"  {'-'*24} {'-'*52}")
for label, raw in PRIMARY:
    kind, detail = run(raw)
    print(f"  {label:24s} {kind.upper():7s} {json.dumps(detail) if kind=='returns' else detail}"[:118])

# ---- the RETRY half: a primary with an OFF-VOCABULARY relation forces the retry
OFF = {"subject": "user", "relation": "zzz_not_a_relation", "object": "x",
       "volatility": "durable"}
PRIMARY_OFF = json.dumps({"triples": [OFF]})
RETRY = [
 ("R valid repair",        json.dumps({"triples":[{"subject":"user","relation":"has_diet","object":"x"}]})),
 ("R valid empty",         '{"triples": []}'),
 ("R missing key",         '{"repairs": [1]}'),
 ("R triples string",      '{"triples": "abc"}'),
 ("R triples null",        '{"triples": null}'),
 ("R bare array of dicts", json.dumps([{"subject":"user","relation":"has_diet","object":"x"}])),
 ("R bare array scalars",  '["a","b"]'),
 ("R prose, no JSON",      'I refuse.'),
 ("R top-level number",    '42'),
]
print()
print(f"  {'retry answer shape':24s} {'outcome':52s}")
print(f"  {'-'*24} {'-'*52}")
for label, raw in RETRY:
    kind, detail = run(PRIMARY_OFF, raw)
    print(f"  {label:24s} {kind.upper():7s} {json.dumps(detail) if kind=='returns' else detail}"[:118])
