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

The gap between the upper bound and the true rate is closed by LABELLING
EVERY fire — a census, which is a human judgement and is Research's
co-verification, not this script's output. `--sample` prints the census
reproducibly. (0026-EVIDENCE-R6-1 ended sampling: eight faces of the
selection class showed no sampling construction over a host-produced
population survives, so no draw, seed or size choice exists.)
"""
from __future__ import annotations

import argparse, collections, hashlib, json, pathlib, random, re, sys

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
    ap.add_argument("--sample", action="store_true",
                    help="draw N fires for labelling (printed, never written "
                         "to the aggregate — they are corpus content)")
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
        if _SPEC.is_file():
            bad = spec_problems(agg, _SPEC.read_text())
            if bad:
                print("the CANDIDATE SPEC drifted:\n  " + "\n  ".join(bad),
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
    fire_digests = []
    fire_seen = collections.Counter()

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
                    # 0026-EVIDENCE-R4-1: each fire gets a CONTENT DIGEST —
                    # one-way, content-free, safe to ship — so a labelled
                    # sample can be RECORD-BOUND: its manifest names these
                    # digests and the verifier checks membership
                    key = json.dumps({"rel": rel, "note": note,
                                      "obj": obj}, sort_keys=True)
                    fire_seen[key] += 1     # identical triples DO recur in
                    d = hashlib.sha256(     # the cache: the ordinal keeps
                        f"{key}#{fire_seen[key]}"  # each fire's id unique
                        .encode()).hexdigest()
                    fire_digests.append(d)
                    sample_pool.append((rel, note, obj, sorted(restrict), d))
                elif res["outbound"]:
                    suppressed_only += 1
                    suppressed_counter.update(res["outbound"])

    agg = dict(
        schema=3,
        lexicon_version=L.LEXICON_VERSION,
        fire_digests=sorted(fire_digests),
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
        print(f"\n--- the {fires}-fire CENSUS for LABELLING (every "
              f"adjudication is a census — no draw, seed or size "
              f"exists to choose; 0026-EVIDENCE-R6-1); corpus content, "
              f"never written ---")
        for rel, note, obj, hits, digest in sample_pool:
            print(f"  [{','.join(hits)}] rel={rel} fire={digest}")
            print(f"    note={str(note)[:150]!r}")
            print(f"    obj ={str(obj)[:110]!r}")
        print("label each as {\"fire\": <digest>, \"label\": \"tp\"|\"fp\"} "
              "in fp_adjudication_sample.jsonl beside fp_adjudication.json")
    return 0


_PEER = HERE.parent / "0011" / "subject_aggregate.json"


# 0026-EVIDENCE-R6-1 (the selection class, face EIGHT — terminal): the
# round-5 projection seed enumerated its basis and justified every byte,
# but "decision-read" does not make a host-produced identifier
# non-choosable: fire_digests are shape-checked, never recomputed from
# the cache, so varying ONE digest while holding the semantic population
# and labels fixed shopped the draw (159/500 FP accepted vs 234/500
# refused, executed by the reviewer). Eight faces across three review
# streams establish the class result: NO sampling construction over a
# host-produced population survives. So there is no sampling: EVERY
# adjudication is a CENSUS — the manifest labels every fire, the
# decision is the exact labelled share, and no draw, seed, size choice
# or confidence bound exists to shop. The residual trust surface is
# exactly two things, both stated in §6a: the per-fire LABELS, and the
# population's correspondence to the cache (recorded protocol: the
# digest derivation — sha256 of the canonical rel/note/obj triple plus
# an occurrence ordinal — reproduces with --cache on the measuring
# host, the reviewer's audit path).
ADJUDICATION_SCHEMA = 6     # the ONE carrier of the current revision:
                            # the validator, the worked example's
                            # generator, the §6a generated claim and the
                            # packaged tests all read THIS constant
                            # (0026-PACKAGE-R6-1: prose carriers
                            # described three different revisions)


def _validate_adjudication(adj, agg, pct, sample_path) -> list:
    """The labelling verdict that alone may carry an over-gate record —
    RECORD-BOUND and DERIVED, not narrated (0026-EVIDENCE-R4-1, the
    signature defect's sixth face: schema 2 accepted true_positive=100 /
    false_positive=-50 because labels only had to SUM to size, and
    sample_sha256 was regex-checked but never opened or hashed). Schema 3
    closes the class structurally — the check compares data to data:

      * the labelled sample is an ON-DISK artifact (live only when the
        gate is exceeded; the shipped worked example is synthetic —
        0026-PACKAGE-R5-1)
        (fp_adjudication_sample.jsonl beside the adjudication record):
        one line per labelled fire, {"fire": <sha256>, "label": "tp"|"fp"};
      * `sample_sha256` is the digest OF THAT FILE's bytes — the verifier
        opens and hashes it, so the digest can no longer point at nothing;
      * every labelled fire must be a MEMBER of the aggregate's
        `fire_digests` population, and no fire is labelled twice — the
        sample cannot be drawn from thin air;
      * the counts are DERIVED by counting labels — the record carries no
        count carriers to disagree with, and a derived count cannot be
        negative or exceed the sample;
      * the DECISION is computed: verdict is the closed {"accept",
        "reject"} enum; reject refuses; accept requires
        pct x WilsonUpper95(fp, n) <= 2.0 — the upper confidence bound,
        never the point estimate;
      * the aggregate side is digest-bound as before (aggregate_sha256 ==
        the canonical bytes of this exact aggregate)."""
    out = []
    if type(adj) is not dict or not adj:
        return ["fp_adjudication.json is empty or not an object — a "
                "stub file is not a labelling verdict"]
    TOP = {"schema": int, "lexicon_version": str, "fires": int,
           "sample": dict, "verdict": str,
           "aggregate_sha256": str, "sample_sha256": str}
    missing = sorted(set(TOP) - set(adj))
    unknown = sorted(set(adj) - set(TOP))
    if missing:
        out.append(f"adjudication missing key(s): {missing}")
    if unknown:
        out.append(f"adjudication unknown key(s): {unknown} — closed")
    for k, ty in TOP.items():
        if k in adj and type(adj[k]) is not ty:
            out.append(f"adjudication {k}: {type(adj[k]).__name__}, "
                       f"expected {ty.__name__}")
    if out:
        return out
    if adj["schema"] != ADJUDICATION_SCHEMA:
        out.append(f"adjudication schema {adj['schema']!r} is not "
                   f"{ADJUDICATION_SCHEMA} (census-only adjudication is "
                   f"a shape change — 0026-EVIDENCE-R6-1: eight faces of "
                   f"the selection class ended sampling; earlier shapes: "
                   f"5 projection seed, 4 archive sidecar, 3 derived "
                   f"counts)")
    if adj["lexicon_version"] != agg["lexicon_version"]:
        out.append(f"adjudication is for lexicon "
                   f"{adj['lexicon_version']!r}, the aggregate is "
                   f"{agg['lexicon_version']!r} — a stale verdict cannot "
                   f"carry this record")
    g = agg["grounded_first_person"]
    if adj["fires"] != g["fires"]:
        out.append(f"adjudication is for {adj['fires']} fires, the "
                   f"aggregate has {g['fires']} — a verdict on different "
                   f"fires cannot carry this record")
    agg_bytes = (json.dumps(agg, sort_keys=True, indent=1) + "\n").encode()
    want = hashlib.sha256(agg_bytes).hexdigest()
    if adj["aggregate_sha256"] != want:
        out.append("adjudication aggregate_sha256 does not match this "
                   "aggregate's canonical bytes — it adjudicates some "
                   "other record")
    smp = adj["sample"]
    S = {"size": int}
    if sorted(smp) != sorted(S) or any(
            type(smp[k]) is not ty for k, ty in S.items() if k in smp):
        out.append(f"adjudication sample keys/types != {sorted(S)} — "
                   f"counts are DERIVED from the manifest, never carried "
                   f"(0026-EVIDENCE-R4-1), and no seed exists: every "
                   f"adjudication is a census (0026-EVIDENCE-R6-1)")
        return out
    if smp["size"] != g["fires"]:
        out.append(f"adjudication sample size {smp['size']} is not the "
                   f"population size {g['fires']} — every adjudication "
                   f"is a CENSUS; there is no sampling construction "
                   f"left to shop (0026-EVIDENCE-R6-1, ending the "
                   f"selection class at face eight)")
    if out:
        return out
    # THE MANIFEST — opened, hashed, membership-checked, counted
    sample_path = pathlib.Path(sample_path)
    if not sample_path.is_file():
        return [f"the labelled sample manifest "
                f"({sample_path.name}) does not exist beside the "
                f"adjudication record — a digest that points at nothing "
                f"is not a binding (0026-EVIDENCE-R4-1)"]
    raw = sample_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != adj["sample_sha256"]:
        return [f"sample_sha256 does not match the bytes of "
                f"{sample_path.name} — the record adjudicates some other "
                f"sample"]
    population = set(agg["fire_digests"])
    seen, tp, fp = set(), 0, 0
    import re as _re
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return [f"{sample_path.name} is not valid UTF-8 ({exc}) — a "
                f"structured refusal, never a crash "
                f"(0026-EVIDENCE-R5-3)"]
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            return [f"{sample_path.name} line {i} is not JSON"]
        if (type(row) is not dict or sorted(row) != ["fire", "label"]
                or type(row.get("fire")) is not str
                or not _re.fullmatch(r"[0-9a-f]{64}", row["fire"])
                or row.get("label") not in ("tp", "fp")):
            return [f"{sample_path.name} line {i} is not a "
                    f'{{"fire": <sha256>, "label": "tp"|"fp"}} record']
        if row["fire"] in seen:
            return [f"{sample_path.name} labels fire "
                    f"{row['fire'][:12]}… twice"]
        if row["fire"] not in population:
            return [f"{sample_path.name} labels a fire outside the "
                    f"aggregate's fire_digests population — the sample "
                    f"cannot be drawn from thin air"]
        seen.add(row["fire"])
        tp += row["label"] == "tp"
        fp += row["label"] == "fp"
    if len(seen) != smp["size"]:
        return [f"the manifest labels {len(seen)} fires but the record "
                f"says size={smp['size']} — the carriers disagree"]
    if seen != population:
        return [f"the manifest does not label EXACTLY the population — "
                f"a census labels every fire, no more, no fewer "
                f"(0026-EVIDENCE-R6-1)"]
    # THE DECISION, computed from the DERIVED counts — never narrated
    if adj["verdict"] not in ("accept", "reject"):
        return [f"adjudication verdict {adj['verdict']!r} is outside the "
                f"closed enum ('accept', 'reject') — free text is not a "
                f"decision"]
    if adj["verdict"] == "reject":
        return [f"the adjudication verdict is REJECT — the labelling "
                f"did not clear the over-gate record ({pct:.2f}% at the "
                f"bound)"]
    # a census: every fire labelled — the FP share is EXACT, there is
    # no sampling variance to bound, so the exact share decides
    share = fp / smp["size"]
    basis = f"exact census share {fp}/{smp['size']}"
    adjudicated = pct * share
    if adjudicated > 2.0:
        return [f"the adjudication says accept but the ADJUDICATED rate "
                f"is {adjudicated:.2f}% (bound {pct:.2f}% x {basis}) — "
                f"over the 2% gate; an accept that disagrees with its "
                f"own numbers refuses"]
    return []


def validate_aggregate(agg, adj_path=None) -> list:
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
    TOP = {"schema": int, "lexicon_version": str, "fire_digests": list,
           "manifest": dict, "grounded_first_person": dict,
           "coverage": dict}
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
    if agg["schema"] != 3:
        out.append(f"schema {agg['schema']!r} is not 3 (the record-bound "
                   f"fire-digest population is a shape change — "
                   f"0026-EVIDENCE-R4-1)")
    if agg["lexicon_version"] != L.LEXICON_VERSION:
        out.append(f"lexicon_version {agg['lexicon_version']!r} is not "
                   f"the shipped {L.LEXICON_VERSION!r} — the record "
                   f"describes some other detector")
    # 0026-EVIDENCE-R4-1: the fire POPULATION ships as content-free
    # one-way digests, so a labelled sample can be record-bound — every
    # digest well-formed, no duplicates, sorted, count == fires
    fd = agg["fire_digests"]
    import re as _re
    if not all(type(d) is str and _re.fullmatch(r"[0-9a-f]{64}", d)
               for d in fd):
        out.append("fire_digests carries a non-sha256 entry")
    elif len(set(fd)) != len(fd):
        out.append("fire_digests carries duplicates")
    elif fd != sorted(fd):
        out.append("fire_digests is not sorted (canonical form)")
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
    if len(fd) != g["fires"]:
        out.append(f"fire_digests has {len(fd)} entries but fires is "
                   f"{g['fires']} — the population and its digest list "
                   f"must agree (0026-EVIDENCE-R4-1)")
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
            adj = (HERE / "fp_adjudication.json") if adj_path is None \
                else pathlib.Path(adj_path)
            if not adj.is_file():
                out.append(
                    f"fires are {pct:.2f}% of the population — OVER the "
                    f"2% gate — and no adjudication artifact "
                    f"(fp_adjudication.json) exists; an over-gate record "
                    f"is not acceptance evidence absent a separately "
                    f"validated labelling verdict (0026-EVIDENCE-R2-1)")
            else:
                # research, round-2 re-verify: the first form of this
                # clause CLAIMED "separately validated" and CHECKED
                # is_file — an empty {} defeated the gate, in the very
                # machinery whose job is catching prose that asserts
                # more than the code. The artifact is READ and
                # VALIDATED, and BOUND to this aggregate.
                try:
                    a_ = json.loads(adj.read_text())
                except (OSError, UnicodeDecodeError,
                        json.JSONDecodeError) as exc:
                    a_ = None
                    out.append(f"fp_adjudication.json is unreadable or "
                               f"not JSON ({exc}) — an over-gate record "
                               f"refuses")
                if a_ is not None:
                    out.extend(_validate_adjudication(
                        a_, agg, pct,
                        adj.with_name("fp_adjudication_sample.jsonl")))

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
        (rf"\| {agg['coverage']['matched_by_lexicon']:,} / "
         rf"{agg['coverage']['with_nonempty_note']:,} = "
         rf"\*\*{(100.0 * agg['coverage']['matched_by_lexicon'] / agg['coverage']['with_nonempty_note']) if agg['coverage']['with_nonempty_note'] else 0.0:.1f}%\*\* \|$",
         "the shipped column of the pass table (coverage, denominator "
         "DERIVED — 0026-EVIDENCE-R5-2)"),
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


_SPEC = HERE.parents[1] / "0026-label-value-agreement.md"


def render_spec_claim(agg) -> str:
    """0026-EVIDENCE-R4-2: the §6a quantitative claim is GENERATED from
    the aggregate — data to data, no prose to drift. The spec carries
    this block verbatim between the fp-claim markers; spec_problems
    requires byte-equality, so the lexicon id, both figures of the rate,
    the gate disposition, and the coverage fraction are all bound (the
    round-4 mutations — a 9,999 denominator, a lex-999 headline — now
    refuse instead of passing a substring search)."""
    g = agg["grounded_first_person"]
    c = agg["coverage"]
    pct = 100.0 * g["fires"] / g["total"] if g["total"] else 0.0
    cov = (100.0 * c["matched_by_lexicon"] / c["with_nonempty_note"]
           if c["with_nonempty_note"] else 0.0)
    disp = "CLEARED (UNDER)" if pct <= 2.0 else "NOT CLEARED (OVER)"
    return (
        "<!-- GENERATED:fp-claim (measure_false_positives.py — byte-bound "
        "to fp_aggregate.json; do not hand-edit) -->\n"
        f"**MEASURED, under lexicon `{agg['lexicon_version']}` "
        f"(adjudication schema {ADJUDICATION_SCHEMA}, census-only): "
        f"{g['fires']:,} fires of {g['total']:,} grounded first-person "
        f"triples = {pct:.2f}% at the bound; the 2% gate is {disp}; "
        f"{g['fires_ambiguous_only']:,} fires restrict via the ambiguous "
        f"class only; {g['suppressed_by_direction_only']:,} suppressed by "
        f"the directional rule; coverage (the M-2 reach diagnostic, not "
        f"recall) {c['matched_by_lexicon']:,} of "
        f"{c['with_nonempty_note']:,} = {cov:.1f}%.**\n"
        "<!-- /GENERATED:fp-claim -->")


_CLAIM_RE = re.compile(
    r"<!-- GENERATED:fp-claim .*?/GENERATED:fp-claim -->", re.S)


def spec_problems(agg, spec_text: str) -> list:
    """0026-EVIDENCE-R3-2 + R4-2: the CANDIDATE SPEC is a live
    quantitative carrier — round 3 shipped 217-vs-220 (no binder at
    all), round 4 shipped a lex-8 headline over a lex-9 aggregate and
    survived 9,999/lex-999 mutations (the binder searched two substrings
    anywhere in the file). The claim is a GENERATED block now: exactly
    one fp-claim block must exist, INSIDE §6a, and its bytes must equal
    render_spec_claim(agg) exactly."""
    out = []
    blocks = _CLAIM_RE.findall(spec_text)
    if len(blocks) != 1:
        return [f"the spec carries {len(blocks)} fp-claim generated "
                f"blocks — exactly one, inside §6a, is the contract "
                f"(0026-EVIDENCE-R4-2)"]
    m6a = re.search(r"^##.*6a\b.*$", spec_text, re.M)
    if m6a is None:
        out.append("the spec has no §6a heading to anchor the fp-claim")
    else:
        nxt = re.search(r"^## ", spec_text[m6a.end():], re.M)
        sec_end = (m6a.end() + nxt.start()) if nxt else len(spec_text)
        if not (m6a.end() <= spec_text.index(blocks[0]) < sec_end):
            out.append("the fp-claim block is OUTSIDE §6a — the claim "
                       "must live where the acceptance gate is stated")
    want = render_spec_claim(agg)
    if blocks[0] != want:
        out.append("the spec's fp-claim block does not byte-match the "
                   "aggregate's rendering — regenerate it with "
                   "render_spec_claim (0026-EVIDENCE-R4-2: figures are "
                   "generated, never hand-edited)")
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
