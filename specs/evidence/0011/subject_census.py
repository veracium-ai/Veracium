"""0011 §3b — the SELF-floor census, runnable and digest-bound.

PACKAGE-R1-1 (external round 1): the deciding count was reported in prose —
72,253 predicate passes, 305 candidate aliases, ~30 self-denoting rows,
0.016% — with no artifact that re-derives any of it. The shipped 0025
aggregate supports the corpus SIZE and nothing about subject classification.
This is the pass those numbers consist of.

The extraction cache is LOCAL-ONLY and never ships. What ships is a
counts-only aggregate carrying the cache manifest, plus the distinct-string
CANDIDATE table the hand classification was made from — so a reader
re-derives every figure without the corpus, and can disagree with the
classification by inspecting the same rows the classifier saw.

WHY A CANDIDATE TABLE AND NOT A REGEX VERDICT. The raw regex family counts
305 rows; the spec's claim is ~30. The gap is not a bug in either — the
regex finds subjects MENTIONING the user ("user's mom", "end user", "User
interviews") and most of those correctly denote somebody else. A regex
cannot make that call, so the classification is recorded per distinct
string in `SELF_DENOTING` below and the total is derived FROM the table.
That is the whole point of PACKAGE-R1-1: the judgement is auditable
because the rows it was made over ship beside it.

PRIVACY. Only subjects in the CANDIDATE set are emitted — by construction
these are self-referential strings ("me", "the user", "user's sister"), not
free-text personal data. The full distinct-subject table (12k+ strings) is
NOT emitted.

Run:  $PY specs/evidence/0011/subject_census.py --cache <extractions.jsonl> \\
          --emit-aggregate specs/evidence/0011/subject_aggregate.json
      $PY specs/evidence/0011/subject_census.py \\
          --aggregate specs/evidence/0011/subject_aggregate.json
"""
from __future__ import annotations

import argparse, collections, hashlib, json, pathlib, re, sys

# The SHIPPED predicate, quoted from ingest.py §4a: whole-string casefold
# equality on the canonical subject; odd types fail closed.
def self_predicate(subject) -> bool:
    try:
        return str(subject).strip().casefold() == "user"
    except Exception:
        return False


# CANDIDATE ALIASES — subjects that FAIL the predicate but mention or could
# denote the user. Deliberately OVER-INCLUSIVE: its job is to bound the
# population a human must look at, not to decide anything.
_CANDIDATE = re.compile(
    r"(?:^|[^a-z])users?(?:$|[^a-z])"        # user, users, user's, the user
    r"|^\s*(?:me|i|myself|self)\s*$"          # bare first-person
    r"|^\s*\[?\s*users?\s*\]?\s*$",           # [User], (user)
    re.I)


def is_candidate(subject: str) -> bool:
    return bool(_CANDIDATE.search(subject or ""))


# THE HAND CLASSIFICATION, recorded per distinct string rather than asserted
# as a total. A reader who disagrees edits this set and the number moves.
# Everything NOT listed here is classified OTHER — possessives ("user's
# mom"), work topics ("user interviews", "end user"), and roles.
SELF_DENOTING = frozenset({
    "me", "i", "myself", "self",
    "[user]", "(user)", "user]", "[user",
    "the user", "this user", "current user", "the current user",
    "user themselves", "user himself", "user herself",
})


# NAME MASKING (PACKAGE-R1-1 asked for a PRIVACY-SAFE table). Given names
# appear in a handful of candidate strings — "user's friend David",
# "user|person:Rachel". The classification never depends on the name: those
# rows are OTHER because of "user's friend" and "person:", not because of who
# is named. So the name is masked and nothing auditable is lost. The mask is
# applied at EMIT time; the unmasked table is never written.
_NAME_AFTER = re.compile(
    r"(?i:((?:person|user)\s*:\s*|(?:friend|brother|sister|wife|husband|mom|"
    r"mother|father|dad|parents|colleague|fianc[\u00e9\u00e8]|boyfriend|"
    r"girlfriend|partner|cousin|aunt|uncle|neighbou?r|boss|manager)\s+))"
    # the NAME half stays case-SENSITIVE. With a global re.I this class
    # matched any lowercase word, so "user's brother and his girlfriend"
    # was masked to "brother <name> his girlfriend" — over-masking that
    # corrupts a row the reviewer is meant to audit.
    r"((?:Sir |Dr\.? |Mr\.? |Ms\.? |Mrs\.? )?[A-Z][a-z]+)")


def mask_names(subject: str) -> str:
    return _NAME_AFTER.sub(lambda m: m.group(1) + "<name>", subject)


def classify(subject: str) -> str:
    return "SELF" if subject.strip().casefold() in SELF_DENOTING else "OTHER"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache")
    ap.add_argument("--aggregate")
    ap.add_argument("--emit-aggregate", metavar="PATH")
    a = ap.parse_args()
    if bool(a.cache) == bool(a.aggregate):
        ap.error("exactly one of --cache / --aggregate")
    if a.aggregate:
        agg = json.loads(pathlib.Path(a.aggregate).read_text())
        problems = validate_aggregate(agg)
        if problems:
            print("aggregate REFUSED:\n  " + "\n  ".join(problems),
                  file=sys.stderr)
            return 1
        return report(agg)

    sha = hashlib.sha256()
    entries = unparseable = triples = passes = 0
    tpc_total = tpc_passes = 0
    candidates = collections.Counter()
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
                triples += 1
                subj = t.get("subject", "")
                hit = self_predicate(subj)
                if hit:
                    passes += 1
                elif is_candidate(str(subj)):
                    candidates[str(subj).strip()] += 1
                # the ONE subpopulation 0025 measured independently: the
                # predicate restricted to third_party_claim. Cross-checking
                # it proves 0011's predicate IS 0025's, on real rows,
                # without needing the corpus.
                if str(t.get("relation", "")).strip() == "third_party_claim":
                    tpc_total += 1
                    if hit:
                        tpc_passes += 1

    agg = dict(
        schema=1,
        manifest=dict(entries=entries, sha256=sha.hexdigest(),
                      unparseable=unparseable),
        triples=triples,
        predicate_passes=passes,
        candidate_table=_masked_table(candidates),
        third_party_claim=dict(total=tpc_total, predicate_passes=tpc_passes),
    )
    if a.emit_aggregate:
        pathlib.Path(a.emit_aggregate).write_text(
            json.dumps(agg, sort_keys=True, indent=1) + "\n")
        print(f"aggregate written  {a.emit_aggregate}")
    return report(agg)


def _masked_table(counter) -> dict:
    """Distinct candidate strings, names masked, counts SUMMED where masking
    collapses two rows into one — so the row total is preserved."""
    out: dict = {}
    for s, n in counter.items():
        out[mask_names(s)] = out.get(mask_names(s), 0) + n
    return {s: out[s] for s in sorted(out)}


# The 0025 aggregate ships in this same archive and was derived from the
# SAME cache by a different script. It is the independent side of every
# cross-check below.
_PEER = (pathlib.Path(__file__).resolve().parents[1]
         / "0025" / "corpus_aggregate.json")


def validate_aggregate(agg) -> list:
    """EVIDENCE-R2-1: aggregate mode TRUSTED its input.

    The reviewer supplied a one-entry aggregate with an all-zero digest and
    this script printed the claimed measurement and exited 0. A verifier
    that accepts a fabrication verifies nothing — 0001's R12-1 in a second
    place, which is where that lesson should have arrived before this
    artifact shipped.

    So: a CLOSED typed schema (missing AND unknown keys refused), and every
    figure the aggregate asserts about the cache cross-checked against the
    0025 aggregate, which was derived from the same cache by a different
    script and ships beside this one. A fabricated manifest now has to
    agree with an artifact the fabricator does not control.
    """
    out = []
    TOP = {"schema": int, "manifest": dict, "triples": int,
           "predicate_passes": int, "candidate_table": dict,
           "third_party_claim": dict}
    missing = sorted(set(TOP) - set(agg))
    unknown = sorted(set(agg) - set(TOP))
    if missing:
        out.append(f"missing key(s): {missing}")
    if unknown:
        out.append(f"unknown key(s): {unknown} — the schema is CLOSED")
    for k, ty in TOP.items():
        if k in agg and type(agg[k]) is not ty:
            out.append(f"{k}: {type(agg[k]).__name__}, expected {ty.__name__}")
    if out:
        return out

    MAN = {"entries": int, "sha256": str, "unparseable": int}
    man = agg["manifest"]
    if sorted(man) != sorted(MAN):
        out.append(f"manifest keys {sorted(man)} != {sorted(MAN)}")
    else:
        for k, ty in MAN.items():
            if type(man[k]) is not ty:
                out.append(f"manifest.{k}: expected {ty.__name__}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(man.get("sha256", ""))):
        out.append("manifest.sha256 is not a sha256 digest")
    for s, n in agg["candidate_table"].items():
        if type(s) is not str or type(n) is not int or n < 1:
            out.append(f"candidate_table[{s!r}] = {n!r} is not a positive "
                       f"count")
            break
        # C3 (own campaign): the validator accepted an aggregate carrying an
        # UNMASKED name — the mask ran at emit time only, so a hand-edited
        # or fabricated aggregate could ship a given name. The same pattern
        # that masks at emit refuses at validate.
        if _NAME_AFTER.search(s):
            out.append(f"candidate_table key {s!r} carries an unmasked "
                       f"name-shaped segment — the table is privacy-safe by "
                       f"contract, masked at emit AND refused here")
            break
    if out:
        return out

    # --- the independent side -------------------------------------------
    if not _PEER.exists():
        out.append(f"{_PEER.name} is absent — the cross-check cannot run, "
                   f"and an uncrossed aggregate is the defect this "
                   f"function exists for")
        return out
    peer = json.loads(_PEER.read_text())
    pm = peer["manifest"]
    if man["sha256"] != pm["sha256"]:
        out.append(f"cache sha256 {man['sha256'][:16]}… does not match the "
                   f"0025 aggregate's {pm['sha256'][:16]}… — these figures "
                   f"were not derived from the same cache")
    if man["entries"] != pm["entries"]:
        out.append(f"manifest.entries {man['entries']:,} != 0025's "
                   f"{pm['entries']:,}")
    if man["unparseable"] != pm["unparseable"]:
        out.append(f"manifest.unparseable {man['unparseable']} != 0025's "
                   f"{pm['unparseable']}")
    # the triple total DERIVED independently, from 0025's relation counts
    derived = sum(peer["relation_counts"].values())
    if agg["triples"] != derived:
        out.append(f"triples {agg['triples']:,} != {derived:,} derived by "
                   f"summing 0025's relation_counts — the total is not "
                   f"taken on trust")
    if not 0 <= agg["predicate_passes"] <= agg["triples"]:
        out.append("predicate_passes is not within [0, triples]")
    # EVIDENCE-R3-1: `schema` was typed but never VALUED — 999 passed.
    if agg["schema"] != 1:
        out.append(f"schema {agg['schema']} is not 1 — this validator "
                   f"knows one version and must not read another")
    # ...and the predicate itself is cross-checked on the one subpopulation
    # 0025 measured independently. This does not bind the full count, but it
    # proves 0011's predicate IS 0025's on 1,600+ real rows.
    tpc = agg["third_party_claim"]
    if sorted(tpc) != ["predicate_passes", "total"]:
        out.append(f"third_party_claim keys {sorted(tpc)} unexpected")
    elif tpc["total"] != peer["third_party_claim"]["total"]:
        out.append(f"third_party_claim total {tpc['total']:,} != 0025's "
                   f"{peer['third_party_claim']['total']:,}")
    elif tpc["predicate_passes"] != peer["third_party_claim"]["subject_user"]:
        out.append(f"the subject predicate passes {tpc['predicate_passes']:,} "
                   f"of third_party_claim; 0025's independently-derived "
                   f"subject_user is {peer['third_party_claim']['subject_user']:,} "
                   f"— the two scripts do not agree on the same predicate")
    return out


def report(agg) -> int:
    triples = agg["triples"]; passes = agg["predicate_passes"]
    table = agg["candidate_table"]
    cand_rows = sum(table.values())
    self_rows = sum(n for s, n in table.items() if classify(s) == "SELF")
    pct = lambda n: (100.0 * n / triples) if triples else 0.0
    print(f"cache            {agg['manifest']['entries']:,} entries, "
          f"sha {agg['manifest']['sha256'][:16]}…, "
          f"{agg['manifest']['unparseable']} unparseable")
    print(f"triples          {triples:,}")
    print(f"predicate passes {passes:,} = {pct(passes):.1f}%   "
          f"(subject.strip().casefold() == 'user')")
    print(f"candidate rows   {cand_rows:,} = {pct(cand_rows):.3f}%  "
          f"over {len(table):,} distinct strings — the population a HUMAN "
          f"had to judge, not a verdict")
    print(f"  classified SELF  {self_rows:,} = {pct(self_rows):.3f}%  "
          f"({sum(1 for s in table if classify(s) == 'SELF')} distinct "
          f"strings in SELF_DENOTING)")
    print(f"  classified OTHER {cand_rows - self_rows:,} — possessives, "
          f"work topics, roles")
    tpc = agg.get("third_party_claim", {})
    print()
    print("  PROVENANCE OF EACH FIGURE (EVIDENCE-R3-1 — what the archive can "
          "check, and what it cannot):")
    print(f"    cross-checked vs 0025   cache manifest, entries, unparseable, "
          f"triples ({triples:,})")
    print(f"    cross-checked vs 0025   the PREDICATE itself on the "
          f"third_party_claim subset: {tpc.get('predicate_passes', 0):,} of "
          f"{tpc.get('total', 0):,} — two scripts, same answer")
    print(f"    derived from the table  candidate rows ({cand_rows:,}), "
          f"classified SELF ({self_rows:,}) — recomputable here")
    print(f"    RECORDED ONLY           predicate_passes over the WHOLE "
          f"corpus ({passes:,}), and the candidate table's COMPLETENESS. "
          f"0025 carries no whole-corpus subject data, so these reproduce "
          f"with --cache on the measuring host and NOT from the archive "
          f"alone.")
    top = sorted(table.items(), key=lambda kv: -kv[1])[:8]
    print(f"  heaviest candidates {[(s, n, classify(s)) for s, n in top]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
