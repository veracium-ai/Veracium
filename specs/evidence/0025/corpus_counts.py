"""The corpus aggregation behind 0024/0025's measured claims — runnable.

External round 3 package feedback asked for the aggregation script plus a
cache manifest/digest supporting the 34.9% measurement. The extraction
cache itself is LOCAL-ONLY (benchmark corpora are never packaged); this
script is what a $0 pass over it consists of, and the manifest block it
prints (entry count + file sha256) pins WHICH cache produced the numbers
in 0025 §2c-ii and 0024 §1.

Run:  $PY specs/evidence/0025/corpus_counts.py --cache <extractions.jsonl>

Recorded output for the 2026-08-01 cache, RUN 2026-08-21 on the measuring
host (the reviewer without the corpus verifies the SCRIPT, this manifest,
and that the spec numbers cite this construction):
    entries        52,359
    file sha256    654e336addaf600ca0363fa40933ae92a38d26f23143e5aa0a780f3fbc011df3
    unparseable    6 cache values (counted, skipped)
    triples        183,417     (spec tables say 183,416 — the original pass
                                differed by one on a malformed row boundary)
    distinct rels  12,576      (spec: 12,575, same boundary)
    off-vocab      64,030 = 34.9%   (spec: 64,029 = 34.9% — the headline
                                     figure is stable under the delta)
    prefers        62,143 = 33.9%   (exact)
    third_party_claim  3,945        (exact)
      note names user  1,644 = 41.7%  (spec: 1,637 = 41.5% — this script's
                                       substring test is slightly broader
                                       than the original's phrase set; the
                                       structural subject count is the one
                                       the rule uses)
      subject=='user'  1,606 = 40.7%  (exact — the load-bearing number)

Not computed here: the stranded near-synonym mass (2.60%) — that pass
canonicalises relation strings and groups them; 0025 Q2 holds it and its
construction ships with any spec that acts on it.
"""
import argparse, collections, hashlib, json, sys


def default_relations() -> set:
    try:
        from veracium.schema import DEFAULT_RELATIONS
        return set(DEFAULT_RELATIONS)
    except ImportError:
        print("NOTE: veracium not importable; pass --registry with one "
              "relation name per line", file=sys.stderr)
        return set()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--registry", help="file of relation names, one per line "
                                       "(default: shipped DEFAULT_RELATIONS)")
    a = ap.parse_args()

    registry = (set(open(a.registry).read().split())
                if a.registry else default_relations())
    if not registry:
        return 2

    sha = hashlib.sha256()
    entries = 0
    triples = 0
    unparseable = 0
    rel_counter = collections.Counter()
    tpc = tpc_note_user = tpc_subject_user = 0

    with open(a.cache, "rb") as fh:
        for raw in fh:
            sha.update(raw)
            entries += 1
            row = json.loads(raw)
            try:
                value = (json.loads(row["value"])
                         if isinstance(row.get("value"), str)
                         else row.get("value", {}))
            except json.JSONDecodeError:
                unparseable += 1     # malformed extractor output — counted,
                continue             # never silently dropped
            for t in value.get("triples", []) or []:
                if not isinstance(t, dict):
                    continue
                triples += 1
                rel = str(t.get("relation", "")).strip()
                rel_counter[rel] += 1
                if rel == "third_party_claim":
                    tpc += 1
                    if "user" in str(t.get("note", "")).lower():
                        tpc_note_user += 1
                    if str(t.get("subject", "")).strip().casefold() == "user":
                        tpc_subject_user += 1

    offvocab = sum(n for r, n in rel_counter.items() if r not in registry)

    print("== cache manifest ==")
    print(f"entries        {entries:,}")
    print(f"file sha256    {sha.hexdigest()}")
    print("== corpus counts ==")
    print(f"unparseable    {unparseable:,} cache values (counted, skipped)")
    print(f"triples        {triples:,}")
    print(f"distinct rels  {len(rel_counter):,}")
    print(f"off-vocab      {offvocab:,}  ({offvocab / triples:.1%})")
    top = rel_counter.most_common(1)[0]
    print(f"top relation   {top[0]}  {top[1]:,}  ({top[1] / triples:.1%})")
    print(f"third_party_claim            {tpc:,}")
    print(f"  note names the user        {tpc_note_user:,}  "
          f"({tpc_note_user / tpc:.1%})" if tpc else "  (none)")
    print(f"  subject == 'user'          {tpc_subject_user:,}  "
          f"({tpc_subject_user / tpc:.1%})" if tpc else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
