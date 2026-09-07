#!/usr/bin/env python3
"""Blind human labelling for the 0038 completed-action oracle (§8 gate).

Presents the 66 blinded items one at a time and records one label each.
Resumable: every answer is written to disk immediately, so ^C is safe and
re-running picks up where you stopped.

    python3 label_oracle.py --rater human_1

The rater sees the instruction, the stored episode, and the three-way answer
space. The rater does NOT see the oracle's own label, the baseline flag, or
any other rater's answers -- that is what makes this leg independent.
"""

import argparse
import json
import os
import shutil
import sys
import textwrap
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, "..", "0038-extraction-corpus"))
PACK = os.path.join(CORPUS, "oracle_labelling_pack_BLINDED.json")
PACK_SHA16 = "5e4b76df716ae388"

KEYS = {"1": "performed", "2": "reported", "3": "neither"}


def sha16(path):
    import hashlib

    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def wrap(text, indent="    "):
    width = min(shutil.get_terminal_size((88, 24)).columns - 4, 96)
    return textwrap.fill(text, width=width, initial_indent=indent,
                         subsequent_indent=indent)


def render(item, n, total, prior):
    os.system("clear" if os.name != "nt" else "cls")
    bar_w = 40
    done = int(bar_w * (n - 1) / total)
    print()
    print(f"  0038 oracle -- blind human labelling        item {n} of {total}")
    print(f"  [{'#' * done}{'.' * (bar_w - done)}]  {item['item_id']}")
    print()
    print("  THE INSTRUCTION THAT WAS GIVEN")
    print(wrap(item["the_instruction_that_was_given"]))
    print()
    print("  THE EPISODE THE SYSTEM STORED")
    print(wrap(item["the_episode_the_system_stored"]))
    print()
    print("  " + "-" * 60)
    print()
    print(wrap(item["question"], indent="  "))
    print()
    for i, opt in enumerate(item["answer_space"], start=1):
        print(wrap(f"[{i}]  {opt}", indent="   "))
    print()
    if prior:
        print(f"  (currently recorded: {prior})")
    print("  1/2/3 = label   b = back   s = skip   q = save and quit")
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rater", required=True,
                    help="short rater id, e.g. 'human_1' or 'model-gpt'")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    got = sha16(PACK)
    if got != PACK_SHA16:
        sys.exit(f"REFUSING: pack digest is {got}, expected {PACK_SHA16}.\n"
                 f"The blinded pack has changed since it was sealed.")

    items = json.load(open(PACK))
    out = args.out or os.path.join(HERE, f"oracle_labels_{args.rater}.json")

    state = {"rater": args.rater, "pack_sha16": got, "labels": {}, "timing": {}}
    if os.path.exists(out):
        state.update(json.load(open(out)))
        if state.get("pack_sha16") != got:
            sys.exit("REFUSING: existing labels were made against a different pack.")

    def save():
        tmp = out + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(state, fh, indent=2, sort_keys=True)
        os.replace(tmp, out)

    i = 0
    while i < len(items):
        item = items[i]
        iid = item["item_id"]
        if iid in state["labels"] and "--redo" not in sys.argv:
            i += 1
            continue
        render(item, i + 1, len(items), state["labels"].get(iid))
        t0 = time.time()
        try:
            ans = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            save()
            print("\n\n  saved. re-run the same command to resume.\n")
            return
        if ans == "q":
            save()
            n = len(state["labels"])
            print(f"\n  saved {n}/{len(items)} to {out}")
            print("  re-run the same command to resume.\n")
            return
        if ans == "b":
            i = max(0, i - 1)
            prev = items[i]["item_id"]
            state["labels"].pop(prev, None)
            state["timing"].pop(prev, None)
            save()
            continue
        if ans == "s":
            i += 1
            continue
        if ans in KEYS:
            state["labels"][iid] = KEYS[ans]
            state["timing"][iid] = round(time.time() - t0, 1)
            save()
            i += 1
            continue
        # anything else: re-render the same item

    save()
    n = len(state["labels"])
    secs = sum(state["timing"].values())
    os.system("clear" if os.name != "nt" else "cls")
    print()
    print(f"  DONE -- {n}/{len(items)} labelled in {secs/60:.1f} min")
    print(f"  written to {out}")
    print()
    counts = {}
    for v in state["labels"].values():
        counts[v] = counts.get(v, 0) + 1
    for k in ("performed", "reported", "neither"):
        print(f"    {k:<10} {counts.get(k, 0)}")
    print()
    print("  Nothing has been compared against the oracle key yet.")
    print("  Tell the research session you are done and it will score it.")
    print()


if __name__ == "__main__":
    main()
