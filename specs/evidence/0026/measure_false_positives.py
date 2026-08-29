#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0026_relay_lexicon.py::test_fp_aggregate_validator_matrix
"""0026 §6a — the acceptance measurement, runnable AND verifiable.

0026-EVIDENCE-R1-1: the first aggregate was write-only — no checker read
it, its figures could be edited freely, and the archive could not
establish the reported rate. This script now has TWO modes (exactly one
of --cache / --aggregate): --cache measures (the cache is LOCAL-ONLY and
never ships) and --aggregate VERIFIES the shipped counts-only record — a
closed typed schema, and the cache manifest cross-checked against the
0025/0011 subject aggregate, which was derived from the same cache by a
different script and ships beside this one, so a fabricated manifest has
to agree with an artifact the fabricator does not control. Whole-corpus
figures (fires, suppressed, coverage) are RECORDED ONLY: they reproduce
with --cache on the measuring host, not from the archive alone, and are
labelled so.

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
    ap.add_argument("--cache")
    ap.add_argument("--aggregate", metavar="PATH",
                    help="VERIFY a shipped aggregate instead of measuring")
    ap.add_argument("--emit-aggregate", metavar="PATH")
    ap.add_argument("--sample", type=int, default=0,
                    help="draw N fires for labelling (printed, never written "
                         "to the aggregate — they are corpus content)")
    ap.add_argument("--seed", type=int, default=20260826)
    a = ap.parse_args()
    if bool(a.cache) == bool(a.aggregate):
        ap.error("exactly one of --cache / --aggregate")
    if a.aggregate:
        agg = json.loads(pathlib.Path(a.aggregate).read_text())
        bad = validate_aggregate(agg)
        if bad:
            print("fp aggregate REFUSED:\n  " + "\n  ".join(bad),
                  file=sys.stderr)
            return 1
        doc = HERE / "FP-MEASUREMENT.md"
        if doc.is_file():
            bad = doc_problems(agg, doc.read_text())
            if bad:
                print("fp measurement DOC drifted:\n  " + "\n  ".join(bad),
                      file=sys.stderr)
                return 1
        report(agg)
        print("aggregate VALID: closed schema, manifest cross-checked "
              "against the 0011/0025 subject aggregate; corpus-dependent "
              "figures are RECORDED ONLY (reproduce with --cache)")
        return 0

    registry = default_relations()
    sha = hashlib.sha256()
    entries = unparseable = 0
    grounded_first_person = 0
    fires = 0
    suppressed_only = 0
    fires_ambiguous_only = 0
    marker_counter = collections.Counter()
    ambiguous_counter = collections.Counter()
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
                restrict = res["inbound"] | res["ambiguous"]
                if restrict:
                    fires += 1
                    if not res["inbound"]:
                        fires_ambiguous_only += 1
                    marker_counter.update(res["inbound"])
                    ambiguous_counter.update(res["ambiguous"])
                    sample_pool.append((rel, note, obj, sorted(restrict)))
                elif res["outbound"]:
                    suppressed_only += 1
                    suppressed_counter.update(res["outbound"])

    agg = dict(
        schema=2,
        lexicon_version=L.LEXICON_VERSION,
        manifest=dict(entries=entries, sha256=sha.hexdigest(),
                      unparseable=unparseable),
        grounded_first_person=dict(
            total=grounded_first_person,
            fires=fires,
            fires_ambiguous_only=fires_ambiguous_only,
            suppressed_by_direction_only=suppressed_only,
            markers=dict(marker_counter),
            ambiguous_markers=dict(ambiguous_counter),
            suppressed_markers=dict(suppressed_counter)),
        coverage=dict(third_party_claim_triples=tpc_notes,
                      with_nonempty_note=tpc_notes_nonempty,
                      matched_by_lexicon=tpc_matched),
    )
    bad = validate_aggregate(agg)
    if bad:
        print("the freshly measured aggregate FAILS its own validator:\n  "
              + "\n  ".join(bad), file=sys.stderr)
        return 1
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


_PEER = HERE.parent / "0011" / "subject_aggregate.json"


def validate_aggregate(agg) -> list:
    """0026-EVIDENCE-R1-1: a CLOSED typed schema, and the cache manifest
    cross-checked against the 0011/0025 subject aggregate — same cache,
    different script, ships beside this one. A fabricated manifest has to
    agree with an artifact the fabricator does not control. Figures that
    only the cache can reproduce are RECORDED ONLY and are not pretended
    verifiable here — but they must be internally consistent (fires
    cannot exceed the population; the ambiguous-only split cannot exceed
    fires; coverage numerators cannot exceed their denominators; the
    lexicon version must be THIS lexicon's, or the record is about some
    other detector)."""
    out = []
    if type(agg) is not dict:
        return ["aggregate is not an object"]
    TOP = {"schema": int, "lexicon_version": str, "manifest": dict,
           "grounded_first_person": dict, "coverage": dict}
    missing = sorted(set(TOP) - set(agg))
    unknown = sorted(set(agg) - set(TOP))
    if missing:
        out.append(f"missing key(s): {missing}")
    if unknown:
        out.append(f"unknown key(s): {unknown} — the schema is CLOSED")
    for k, ty in TOP.items():
        if k in agg and type(agg[k]) is not ty:
            out.append(f"{k}: {type(agg[k]).__name__}, expected "
                       f"{ty.__name__}")
    if out:
        return out
    if agg["schema"] != 2:
        out.append(f"schema {agg['schema']!r} is not 2 (the ambiguity "
                   f"split is a shape change)")
    if agg["lexicon_version"] != L.LEXICON_VERSION:
        out.append(f"lexicon_version {agg['lexicon_version']!r} is not "
                   f"the shipped {L.LEXICON_VERSION!r} — the record "
                   f"describes some other detector")
    MAN = {"entries": int, "sha256": str, "unparseable": int}
    man = agg["manifest"]
    if sorted(man) != sorted(MAN) or any(
            type(man[k]) is not ty for k, ty in MAN.items()
            if k in man):
        out.append(f"manifest keys/types != {sorted(MAN)}")
        return out
    G = {"total": int, "fires": int, "fires_ambiguous_only": int,
         "suppressed_by_direction_only": int, "markers": dict,
         "ambiguous_markers": dict, "suppressed_markers": dict}
    g = agg["grounded_first_person"]
    if sorted(g) != sorted(G) or any(
            type(g[k]) is not ty for k, ty in G.items() if k in g):
        out.append(f"grounded_first_person keys/types != {sorted(G)}")
        return out
    # privacy AND correctness in one rule (the census C3 lesson): marker
    # keys must be MEMBERS of the shipped closed lexicon — an arbitrary
    # string key could carry corpus content into the shipped record, and
    # a marker outside the lexicon cannot have fired at all
    lexicon_members = (set(L._VERBS) | set(L._PHRASES) | {"per"})
    for name in ("markers", "ambiguous_markers", "suppressed_markers"):
        for k, v in g[name].items():
            if type(k) is not str or type(v) is not int or v < 1:
                out.append(f"{name}[{k!r}] = {v!r} is not a positive count")
            elif k not in lexicon_members:
                out.append(f"{name} key {k!r} is not a member of the "
                           f"shipped lexicon — a foreign key could carry "
                           f"corpus content, and a marker outside the "
                           f"lexicon cannot have fired")
    C = {"third_party_claim_triples": int, "with_nonempty_note": int,
         "matched_by_lexicon": int}
    c = agg["coverage"]
    if sorted(c) != sorted(C) or any(
            type(c[k]) is not ty for k, ty in C.items() if k in c):
        out.append(f"coverage keys/types != {sorted(C)}")
        return out
    # internal consistency — RECORDED-ONLY figures still cannot contradict
    # themselves
    if not (0 <= g["fires"] <= g["total"]):
        out.append(f"fires {g['fires']} outside [0, total {g['total']}]")
    if not (0 <= g["fires_ambiguous_only"] <= g["fires"]):
        out.append("fires_ambiguous_only exceeds fires")
    if not (0 <= c["matched_by_lexicon"] <= c["with_nonempty_note"]
            <= c["third_party_claim_triples"]):
        out.append("coverage numerators exceed their denominators")
    # markers cannot restrict more triples than fired: every fired triple
    # carries >=1 marker, so any single marker's count <= fires
    for name in ("markers", "ambiguous_markers"):
        for k, v in g[name].items():
            if v > g["fires"]:
                out.append(f"{name}[{k!r}]={v} exceeds fires {g['fires']}")
    # 0026-EVIDENCE-R2-1: the validator validated SHAPE while the GATE
    # was carried elsewhere — fires=2,000 (2.92%, over the 2% bar)
    # verified as "aggregate VALID". The gate is part of validity now: an
    # over-gate record refuses UNLESS a separately validated adjudication
    # artifact exists (the §6a pre-commitment path: labelling decides),
    # because an over-bar aggregate is not acceptance evidence on its own.
    if g["total"] > 0:
        pct = 100.0 * g["fires"] / g["total"]
        if pct > 2.0:
            adj = HERE / "fp_adjudication.json"
            if not adj.is_file():
                out.append(
                    f"fires are {pct:.2f}% of the population — OVER the "
                    f"2% gate — and no adjudication artifact "
                    f"(fp_adjudication.json) exists; an over-gate record "
                    f"is not acceptance evidence absent a separately "
                    f"validated labelling verdict (0026-EVIDENCE-R2-1)")

    # the cross-artifact anchor: the 0011/0025 subject aggregate was
    # derived from the SAME cache by a different script
    peer_path = _PEER.resolve()
    if not peer_path.is_file():
        out.append(f"{peer_path.name} is absent — the manifest cross-check "
                   f"cannot run, and an uncrossed aggregate is the defect "
                   f"this validator exists for")
        return out
    peer = json.loads(peer_path.read_text())
    pm = peer.get("manifest", {})
    for k in ("entries", "sha256", "unparseable"):
        if man.get(k) != pm.get(k):
            out.append(f"manifest.{k} = {man.get(k)!r} disagrees with the "
                       f"0011/0025 subject aggregate's {pm.get(k)!r} — "
                       f"the two scripts read the same cache")
    return out


def doc_problems(agg, doc_text: str) -> list:
    """0026-EVIDENCE-R2-1: FP-MEASUREMENT.md carried stale figures beside
    the current result, because nothing compared the prose to the
    artifact — the 0011 check_census_figures class. The doc's SHIPPED
    claims are bound here: headline fires/percent/lexicon, and the
    shipped column of the pass table."""
    import re as _re
    g = agg["grounded_first_person"]
    pct = 100.0 * g["fires"] / g["total"] if g["total"] else 0.0
    out = []
    facts = (
        (rf"gate is CLEARED\. {pct:.2f}% \({g['fires']:,} of "
         rf"{g['total']:,}\)",
         "the headline result line"),
        (rf"under {_re.escape(agg['lexicon_version'].replace('0026-', ''))} ",
         "the headline lexicon version"),
        (rf"\| {g['fires']:,} = \*\*{pct:.2f}%\*\* \|$",
         "the shipped column of the pass table (fires)"),
        (rf"\| \*\*{g['suppressed_by_direction_only']:,}\*\* \|$",
         "the shipped column of the pass table (suppressed)"),
        (rf"\| {agg['coverage']['matched_by_lexicon']:,} / 3,898 = ",
         "the shipped column of the pass table (coverage)"),
        (rf"matches \*\*{agg['coverage']['matched_by_lexicon']:,} of ",
         "the coverage prose figure"),
    )
    for pat, what in facts:
        if not _re.search(pat, doc_text, _re.M):
            out.append(f"FP-MEASUREMENT.md no longer states {what} in the "
                       f"bound form matching the aggregate "
                       f"({agg['lexicon_version']}, {g['fires']:,} = "
                       f"{pct:.2f}%) — the prose has drifted from its "
                       f"artifact")
    return out


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
    verdict = ("UNDER at the bound" if pct <= 2
               else "OVER at the bound — labelling decides")
    print(f"  gate         2% of grounded first-person triples ({verdict})")
    print(f"  ambiguous    {g.get('fires_ambiguous_only', 0):,} of the "
          f"fires restrict via the AMBIGUOUS class only (counted, "
          f"conservative)")
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
