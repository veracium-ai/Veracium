#!/usr/bin/env python3
"""Score a blind human labelling run against the 0038 oracle key (§8 gate).

    python3 score_oracle.py --rater human_1

Emits the confusion matrix, Cohen's kappa, the disagreement classes, and the
drift diagnostics. Everything printed is derived from the three pinned files;
nothing is hand-maintained.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, "..", "0038-extraction-corpus"))

PINS = {
    "oracle_labelling_pack_BLINDED.json": "5e4b76df716ae388",
    "oracle_labelling_KEY.json": "b081fa87206ae203",
}

# Surface classes over the STORED EPISODE. Ordered: first match wins.
CLASSES = [
    ("decided to",                 r"\bdecided to\b"),
    ("gave an instruction",        r"\bgave an instruction\b|\bwas instructed\b|\binstructed to\b"),
    ("asked for / requested",      r"\basked for\b|\brequested\b"),
    ("set an obligation",          r"\bset a recurring obligation\b"),
    ("wants / prefers / plans",    r"\bwants?\b|\bprefers?\b|\bintends?\b|\bplans? to\b"),
    ("bare past-tense verb",       r""),
]


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def classify(episode):
    for name, pat in CLASSES:
        if not pat or re.search(pat, episode):
            return name
    return "bare past-tense verb"


def kappa(pairs):
    """pairs: list of (human_bool, oracle_bool)."""
    n = len(pairs)
    if not n:
        return float("nan"), 0.0
    agree = sum(h == o for h, o in pairs)
    pa = agree / n
    ph = sum(h for h, _ in pairs) / n
    po = sum(o for _, o in pairs) / n
    pe = ph * po + (1 - ph) * (1 - po)
    k = float("nan") if pe == 1 else (pa - pe) / (1 - pe)
    return k, pa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater", required=True)
    args = ap.parse_args()

    for name, want in PINS.items():
        got = sha16(os.path.join(CORPUS, name))
        if got != want:
            sys.exit(f"REFUSING: {name} is {got}, expected {want}")

    key = json.load(open(os.path.join(CORPUS, "oracle_labelling_KEY.json")))
    pack = json.load(open(os.path.join(CORPUS, "oracle_labelling_pack_BLINDED.json")))
    lab_path = os.path.join(HERE, f"oracle_labels_{args.rater}.json")
    state = json.load(open(lab_path))
    hum, tim = state["labels"], state["timing"]

    if state.get("pack_sha16") != PINS["oracle_labelling_pack_BLINDED.json"]:
        sys.exit("REFUSING: labels were made against a different pack.")

    pos = {i["item_id"]: n + 1 for n, i in enumerate(pack)}
    epi = {i["item_id"]: i["the_episode_the_system_stored"] for i in pack}
    ins = {i["item_id"]: i["the_instruction_that_was_given"] for i in pack}

    ids = [i for i in key if i in hum]
    missing = [i for i in key if i not in hum]

    print(f"# 0038 oracle §8 — human leg, rater '{args.rater}'\n")
    print(f"pack  {PINS['oracle_labelling_pack_BLINDED.json']}   "
          f"key {PINS['oracle_labelling_KEY.json']}   "
          f"labels {sha16(lab_path)}")
    print(f"labelled {len(ids)}/{len(key)}"
          + (f"  MISSING: {missing}" if missing else ""))
    used = collections.Counter(hum[i] for i in ids)
    print("rater used: " + ", ".join(f"{k}={v}" for k, v in sorted(used.items())))
    unused = {"performed", "reported", "neither"} - set(used)
    if unused:
        print(f"ANSWER OPTIONS NEVER USED: {sorted(unused)}")
    print()

    pairs = [(hum[i] == "performed", key[i]["regex_said_performed"]) for i in ids]
    cm = collections.Counter(pairs)
    k, pa = kappa(pairs)
    print("## human vs oracle\n")
    print(f"{'':<20}{'oracle: performed':<20}oracle: reported")
    print(f"{'human: performed':<20}{cm[(True,True)]:<20}{cm[(True,False)]}")
    print(f"{'human: reported':<20}{cm[(False,True)]:<20}{cm[(False,False)]}")
    print(f"\n  raw agreement  {sum(h==o for h,o in pairs)}/{len(pairs)} = {pa*100:.1f}%")
    print(f"  Cohen's kappa  {k:.3f}")
    print()

    print("## by surface class of the stored episode\n")
    g = collections.defaultdict(list)
    for i in ids:
        g[classify(epi[i])].append(i)
    print(f"{'class':<26}{'n':>3}{'h=perf':>8}{'o=perf':>8}{'disagree':>10}")
    print("-" * 55)
    for c, v in sorted(g.items(), key=lambda x: -len(x[1])):
        dh = sum(hum[i] == "performed" for i in v)
        do = sum(key[i]["regex_said_performed"] for i in v)
        dis = sum((hum[i] == "performed") != key[i]["regex_said_performed"] for i in v)
        print(f"{c:<26}{len(v):>3}{dh:>8}{do:>8}{dis:>10}")
    print()

    print("## drift diagnostic — intra-rater consistency by position\n")
    half = len(pack) // 2
    for lo, hi, nm in ((1, half, f"items 1-{half}"), (half + 1, len(pack), f"items {half+1}-{len(pack)}")):
        sel = [i for i in ids if lo <= pos[i] <= hi]
        ag = sum((hum[i] == "performed") == key[i]["regex_said_performed"] for i in sel)
        ts = sorted(tim[i] for i in sel if i in tim)
        med = ts[len(ts) // 2] if ts else float("nan")
        print(f"  {nm:<14} agreement {ag}/{len(sel)} = {ag/len(sel)*100:5.1f}%   median {med:.1f}s")
    print()

    # Perfect positional separation is only evidence of drift if it is unlikely
    # by chance. With a of one label and b of the other, exactly 2 of the
    # C(a+b, a) orderings separate, so p = 2 / C(a+b, a). A 1-vs-3 split
    # separates half the time and means nothing; report the p-value and let it
    # say so rather than trusting the pattern.
    from math import comb
    for c, v in sorted(g.items(), key=lambda x: -len(x[1])):
        p = sorted(pos[i] for i in v if hum[i] == "performed")
        r = sorted(pos[i] for i in v if hum[i] == "reported")
        if not (p and r):
            continue
        if not (max(p) < min(r) or max(r) < min(p)):
            continue
        pv = 2 / comb(len(p) + len(r), len(p))
        verdict = "DRIFT" if pv < 0.01 else "not significant — expected at this split"
        print(f"  perfect positional separation in class '{c}' "
              f"({len(p)} vs {len(r)}), p = {pv:.5f}  [{verdict}]")
        print(f"      performed at {p}")
        print(f"      reported  at {r}")
        if pv < 0.01:
            print(f"      The rater's policy on this class changed once, mid-run, and did")
            print(f"      not change back. Agreement over the whole run averages two")
            print(f"      different policies and is not a single measurement.")
        print()

    print("## disagreements\n")
    d = [i for i in ids if (hum[i] == "performed") != key[i]["regex_said_performed"]]
    for i in sorted(d, key=lambda x: pos[x]):
        o = "performed" if key[i]["regex_said_performed"] else "reported"
        print(f"  pos {pos[i]:>2}  {i}  human={hum[i]:<10} oracle={o:<10} {tim.get(i)}s")
        print(f"        instr : {ins[i]}")
        print(f"        stored: {epi[i]}")
    print(f"\n  {len(d)} disagreements, "
          f"{sum(1 for i in d if pos[i] <= half)} in the first half, "
          f"{sum(1 for i in d if pos[i] > half)} in the second.")


if __name__ == "__main__":
    main()
