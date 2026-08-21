"""The corpus aggregation behind 0024/0025's measured claims — runnable.

External round 3 package feedback asked for the aggregation script plus a
cache manifest/digest supporting the 34.9% measurement. The extraction
cache itself is LOCAL-ONLY (benchmark corpora are never packaged); this
script is what a $0 pass over it consists of, and the manifest block it
prints (entry count + file sha256) pins WHICH cache produced the numbers
in 0025 §2c-ii and 0024 §1.

Run:  $PY specs/evidence/0025/corpus_counts.py --aggregate specs/evidence/0025/corpus_aggregate.json
      (the SHIPPED counts-only aggregate — independent verification of
       every published count without the corpus; or --cache <extractions.jsonl>
       on the measuring host, which emits identical output)

Recorded output for the 2026-08-01 cache, RUN 2026-08-21 on the measuring
host (the reviewer without the corpus verifies the SCRIPT, this manifest,
and that the spec numbers cite this construction):
    entries        52,359
    file sha256    654e336addaf600ca0363fa40933ae92a38d26f23143e5aa0a780f3fbc011df3
    unparseable    6 cache values (counted, skipped)
    triples        183,417
    distinct rels  12,576
    off-vocab      64,030 = 34.9%
    prefers        62,143 = 33.9%
    prefers+uses_tool  88,253 = 48.1%
    near-synonyms  0 under the stated mechanical rule (the earlier ~2.6%
                   was a semantic grouping, unshipped — requalified in
                   0025 §1, round 4 PAIR-R4-1)
    third_party_claim  3,945
      note names user  1,644 = 41.7%  (this script's substring rule)
      subject=='user'  1,606 = 40.7%  (the load-bearing cell)
    Round 4 (PAIR-R4-1): BOTH specs now cite these figures exactly — the
    earlier hand-recorded 183,416/12,575/64,029/1,637=41.5% are retired;
    they differed on a malformed-row boundary and an unshipped phrase set.

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
    ap.add_argument("--cache", help="the local extraction cache (jsonl)")
    ap.add_argument("--aggregate", help="verify from a distributable "
                    "aggregate instead of the local-only cache (round 5 "
                    "package feedback: every published count independently "
                    "recomputable without the corpus)")
    ap.add_argument("--emit-aggregate", metavar="PATH",
                    help="write the distributable counts-only aggregate "
                    "(relation-frequency table + third_party_claim "
                    "sub-counts + the cache manifest) after a --cache run")
    ap.add_argument("--registry", help="file of relation names, one per line "
                                       "(default: shipped DEFAULT_RELATIONS)")
    a = ap.parse_args()
    if bool(a.cache) == bool(a.aggregate):
        ap.error("exactly one of --cache / --aggregate")
    if a.aggregate:
        return report(json.load(open(a.aggregate)), None)

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

    agg = dict(schema=1,
               manifest=dict(entries=entries, sha256=sha.hexdigest(),
                             unparseable=unparseable),
               relation_counts=dict(rel_counter),
               third_party_claim=dict(total=tpc, note_names_user=tpc_note_user,
                                      subject_user=tpc_subject_user))
    if a.emit_aggregate:
        with open(a.emit_aggregate, "w") as fh:
            json.dump(agg, fh, sort_keys=True, indent=1)
        print(f"aggregate written  {a.emit_aggregate}")
    return report(agg, registry)


def report(agg, registry) -> int:
    if registry is None:
        registry = default_relations()
        if not registry:
            return 2
    rel_counter = collections.Counter(agg["relation_counts"])
    entries = agg["manifest"]["entries"]
    unparseable = agg["manifest"]["unparseable"]
    triples = sum(rel_counter.values())
    tpc = agg["third_party_claim"]["total"]
    tpc_note_user = agg["third_party_claim"]["note_names_user"]
    tpc_subject_user = agg["third_party_claim"]["subject_user"]
    offvocab = sum(n for r, n in rel_counter.items() if r not in registry)

    # PAIR-R4-1: every numeric claim the specs retain is computed HERE.
    # near-synonym rule, STATED: canonical(r) = casefold, strip, runs of
    # non-alphanumerics collapsed to "_". A triple is stranded-near-synonym
    # when its relation is off-vocabulary but its canonical form equals a
    # registry member's canonical form ("Prefers", "prefers ", "uses-tool").
    import re
    def canon(r):
        return re.sub(r"[^a-z0-9]+", "_", r.casefold().strip()).strip("_")
    reg_canon = {canon(m) for m in registry}
    near_syn = sum(n for r, n in rel_counter.items()
                   if r not in registry and canon(r) in reg_canon)
    combined = rel_counter.get("prefers", 0) + rel_counter.get("uses_tool", 0)

    print("== cache manifest ==")
    print(f"entries        {entries:,}")
    print(f"file sha256    {agg['manifest']['sha256']}")
    print("== corpus counts ==")
    print(f"unparseable    {unparseable:,} cache values (counted, skipped)")
    print(f"triples        {triples:,}")
    print(f"distinct rels  {len(rel_counter):,}")
    print(f"off-vocab      {offvocab:,}  ({offvocab / triples:.1%})")
    top = rel_counter.most_common(1)[0]
    print(f"top relation   {top[0]}  {top[1]:,}  ({top[1] / triples:.1%})")
    print(f"prefers+uses_tool             {combined:,}  ({combined / triples:.1%})")
    print(f"stranded near-synonyms        {near_syn:,}  ({near_syn / triples:.2%})"
          "  [rule: canonical form matches a member]")
    print(f"third_party_claim            {tpc:,}")
    print(f"  note names the user        {tpc_note_user:,}  "
          f"({tpc_note_user / tpc:.1%})" if tpc else "  (none)")
    print(f"  subject == 'user'          {tpc_subject_user:,}  "
          f"({tpc_subject_user / tpc:.1%})" if tpc else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
