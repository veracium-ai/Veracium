"""0026 §6a — the acceptance measurement, runnable.

§6a pre-commits: if the lexicon's false-positive rate exceeds 2% OF GROUNDED
FIRST-PERSON TRIPLES, the lexicon narrows before v1 ships. This script is
what that pass consists of. The extraction cache is LOCAL-ONLY and never
ships; the counts-only aggregate does.

WHAT CANNOT BE DECIDED HERE, AND IS NOT PRETENDED OTHERWISE. "Genuinely own"
is a property of the CONTENT, and the detector is the thing on trial — using
it to decide which of its own fires are false is the self-assertion failure
this project has a name for. So this script reports what can be counted
mechanically and bounds the rest:

  * FIRES  — grounded first-person triples where the detector matches. Every
    fire is a CANDIDATE false positive, so this rate is the UPPER BOUND: the
    true rate cannot exceed it, and equals it only if no fire is a real relay.
  * SUPPRESSED — first-person-outbound constructions the directional rule
    withheld. This is the population the rule saves, counted rather than
    asserted, and it is the direct evidence for §3a's directional cells.
  * COVERAGE (M-2's denominator) — over third_party_claim notes, the share
    the lexicon matches, so §8's claim ships with its measured denominator
    instead of an implied whole.

The gap between the upper bound and the true rate is closed by LABELLING a
random sample of fires, which is a human judgement and is Research's
co-verification, not this script's output. `--sample N --seed S` draws that
sample reproducibly.
"""
from __future__ import annotations

import argparse, collections, hashlib, json, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "src"))

import relay_lexicon as L                                   # noqa: E402


def default_relations() -> set:
    from veracium.schema import DEFAULT_RELATIONS
    return set(DEFAULT_RELATIONS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--emit-aggregate", metavar="PATH")
    ap.add_argument("--sample", type=int, default=0,
                    help="draw N fires for labelling (printed, never written "
                         "to the aggregate — they are corpus content)")
    ap.add_argument("--seed", type=int, default=20260826)
    a = ap.parse_args()

    registry = default_relations()
    sha = hashlib.sha256()
    entries = unparseable = 0
    grounded_first_person = 0
    fires = 0
    suppressed_only = 0
    marker_counter = collections.Counter()
    suppressed_counter = collections.Counter()
    tpc_notes = tpc_notes_nonempty = tpc_matched = 0
    sample_pool = []

    with open(a.cache, "rb") as fh:
        for raw in fh:
            sha.update(raw); entries += 1
            row = json.loads(raw)
            try:
                value = (json.loads(row["value"])
                         if isinstance(row.get("value"), str)
                         else row.get("value", {}))
            except json.JSONDecodeError:
                unparseable += 1
                continue
            for t in value.get("triples", []) or []:
                if not isinstance(t, dict):
                    continue
                rel = str(t.get("relation", "")).strip()
                note = t.get("note")
                obj = t.get("object")
                subj_is_user = (str(t.get("subject", "")).strip().casefold()
                                == "user")

                if rel == "third_party_claim":
                    tpc_notes += 1
                    if isinstance(note, str) and note.strip():
                        tpc_notes_nonempty += 1
                        if L.relay_markers(note, None):
                            tpc_matched += 1
                    continue

                # GROUNDED FIRST-PERSON: an in-registry relation whose subject
                # is the user — the population §6a's 2% is a share OF.
                if rel not in registry or not subj_is_user:
                    continue
                grounded_first_person += 1
                res = L.scan(note, obj)
                if res["inbound"]:
                    fires += 1
                    marker_counter.update(res["inbound"])
                    sample_pool.append((rel, note, obj, sorted(res["inbound"])))
                elif res["outbound"]:
                    suppressed_only += 1
                    suppressed_counter.update(res["outbound"])

    agg = dict(
        schema=1,
        lexicon_version=L.LEXICON_VERSION,
        manifest=dict(entries=entries, sha256=sha.hexdigest(),
                      unparseable=unparseable),
        grounded_first_person=dict(
            total=grounded_first_person,
            fires=fires,
            suppressed_by_direction_only=suppressed_only,
            markers=dict(marker_counter),
            suppressed_markers=dict(suppressed_counter)),
        coverage=dict(third_party_claim_triples=tpc_notes,
                      with_nonempty_note=tpc_notes_nonempty,
                      matched_by_lexicon=tpc_matched),
    )
    if a.emit_aggregate:
        pathlib.Path(a.emit_aggregate).write_text(
            json.dumps(agg, sort_keys=True, indent=1) + "\n")
        print(f"aggregate written  {a.emit_aggregate}")
    report(agg)

    if a.sample and sample_pool:
        rng = random.Random(a.seed)
        print(f"\n--- {min(a.sample, len(sample_pool))} fires sampled for "
              f"LABELLING (seed {a.seed}); corpus content, never written ---")
        for rel, note, obj, hits in rng.sample(
                sample_pool, min(a.sample, len(sample_pool))):
            print(f"  [{','.join(hits)}] rel={rel}")
            print(f"    note={str(note)[:150]!r}")
            print(f"    obj ={str(obj)[:110]!r}")
    return 0


def report(agg) -> None:
    g = agg["grounded_first_person"]; c = agg["coverage"]
    tot, fires = g["total"], g["fires"]
    pct = (100.0 * fires / tot) if tot else 0.0
    print(f"lexicon        {agg['lexicon_version']}")
    print(f"cache          {agg['manifest']['entries']:,} entries, "
          f"sha {agg['manifest']['sha256'][:16]}…, "
          f"{agg['manifest']['unparseable']} unparseable")
    print(f"grounded 1P    {tot:,} triples (in-registry relation, subject=user)")
    print(f"  FIRES        {fires:,} = {pct:.2f}%   <-- UPPER BOUND on the "
          f"false-positive rate")
    print(f"  gate         2% of grounded first-person triples "
          f"({'UNDER at the bound' if pct <= 2 else 'OVER at the bound — '
             'labelling decides'})")
    print(f"  suppressed   {g['suppressed_by_direction_only']:,} outbound-only "
          f"(saved by the directional rule)")
    top = sorted(g["markers"].items(), key=lambda kv: -kv[1])[:8]
    print(f"  top markers  {top}")
    sup = sorted(g["suppressed_markers"].items(), key=lambda kv: -kv[1])[:6]
    print(f"  suppressed by {sup}")
    denom = c["with_nonempty_note"]
    cov = (100.0 * c["matched_by_lexicon"] / denom) if denom else 0.0
    print(f"coverage (M-2) {c['matched_by_lexicon']:,} of {denom:,} "
          f"third_party_claim notes = {cov:.1f}%  "
          f"(of {c['third_party_claim_triples']:,} tpc triples)")


if __name__ == "__main__":
    raise SystemExit(main())
