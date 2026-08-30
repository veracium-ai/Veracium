# The adjudication construction, worked end-to-end (SYNTHETIC)

**Nothing here is a live measurement.** The shipped `fp_aggregate.json`
is UNDER the 2% gate, so no live adjudication exists or can exist — the
validator only consults one for an over-gate record (0026-PACKAGE-R5-1:
an earlier fold said the manifest "ships"; the accurate claim is that
the CONSTRUCTION ships, and the live artifacts materialize if the gate
is ever exceeded). This directory is the inspectable proof that the
construction works end-to-end. `generate_example.py` (in this
directory) regenerates every artifact deterministically — the standing
test runs it into a scratch directory and requires BYTE-IDENTICAL
output to these shipped files, then validates them from disk
(`test_the_worked_adjudication_example_validates_from_disk`;
0026-PACKAGE-R6-1: an earlier README claimed a generator the package
did not ship).

Contents, every value derived (no hand-typed figures):

- `demo_aggregate.json` — a synthetic 120-fire / 4,000-triple
  population (3.0%: over-gate, so the adjudication path is exercised;
  the census labels every fire and the EXACT share decides).
- `fp_adjudication_sample.jsonl` — the census label manifest: one
  `{"fire": <digest>, "label": "tp"|"fp"}` line per fire, 20 labelled
  `fp`.
- `fp_adjudication.json` — the current-schema record (the schema
  number comes from `measure_false_positives.ADJUDICATION_SCHEMA`, the
  one carrier of the revision) binding all of it: aggregate digest,
  manifest digest, the census size, `verdict: accept` — which the
  validator CHECKS (exact census share 20/120 → 3.0% × 0.1667 = 0.5%
  ≤ 2%), never believes. Every adjudication is a CENSUS: no draw, seed
  or size choice exists (0026-EVIDENCE-R6-1 ended sampling at face
  eight of the selection class).

To re-verify by hand:

```
python - <<'PY'
import sys, json, pathlib
sys.path.insert(0, "specs/evidence/0026")
import measure_false_positives as M
D = pathlib.Path("specs/evidence/0026/adjudication_example")
agg = json.loads((D / "demo_aggregate.json").read_text())
print(M.validate_aggregate(agg, adj_path=D / "fp_adjudication.json")
      or "VALID")
PY
```
