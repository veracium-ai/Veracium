#!/usr/bin/env python3
"""0024 conflation baseline runner. Run with the LIVE tree's venv:
  /home/ubuntu/Dev/veracium/.venv/bin/python run_baseline.py
Measures current main (pre-0024-fix); the post-fix re-run uses the SAME
frozen probes and pairs probe-for-probe. Store-level classification
first (classify from artifacts), answer classification second.
"""
import json, os, re, subprocess, sys, tempfile, time

sys.path.insert(0, "/home/ubuntu/Dev/veracium/src")
HERE = os.path.dirname(os.path.abspath(__file__))

COMMIT = subprocess.run(["git", "-C", "/home/ubuntu/Dev/veracium",
                         "rev-parse", "--short", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
DIRTY_SRC = subprocess.run(["git", "-C", "/home/ubuntu/Dev/veracium",
                            "status", "--porcelain", "--", "src/", "tests/"],
                           capture_output=True, text=True).stdout.strip()

MODEL = "gpt-4.1-2025-04-14"


def mk_llm():
    from openai import OpenAI
    client = OpenAI()

    def complete(prompt, *, system=None, role="compile", json_schema=None):
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        for attempt in range(6):
            try:
                r = client.chat.completions.create(
                    model=MODEL, temperature=0.0, max_tokens=1024,
                    messages=msgs, timeout=120)
                return r.choices[0].message.content or ""
            except Exception as e:
                if attempt == 5:
                    raise
                time.sleep(10 * (2 ** attempt)
                           if "429" in str(e) or "rate" in str(e).lower()
                           else 3)
    return complete


HEDGE = re.compile(r"unverified|not confirmed|no confirmed|claim|reported|"
                   r"according to|says|said|don'?t know|no record|"
                   r"not in (my |the )?(memory|record)", re.I)


def classify_answer(ans, value_key):
    has_value = value_key.lower() in ans.lower()
    if has_value and not HEDGE.search(ans):
        return "asserted"
    if has_value:
        return "hedged"
    return "absent"


def main():
    from veracium import Memory, MemoryConfig, EvidenceAuthor
    llm = mk_llm()
    probes = [json.loads(l) for l in open(os.path.join(HERE, "probes.jsonl"))]
    out_path = os.path.join(HERE, "baseline_main_records.jsonl")
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)["probe_id"] for l in open(out_path)}

    with open(out_path, "a") as out:
        for p in probes:
            if p["probe_id"] in done:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                mem = Memory(llm=llm, config=MemoryConfig(
                    db_path=f"{tmp}/store.db"))
                uid = "bl"
                try:
                    author = (EvidenceAuthor.USER if p["author"] == "user"
                              else EvidenceAuthor.THIRD_PARTY)
                    mem.remember(uid, p["text"], author=author)
                    edges = [{
                        "relation": e.relation,
                        "original_relation": e.original_relation,
                        "disclosure": e.provenance.disclosure.value,
                        "note": e.note,
                    } for e in mem.store.edges(uid, active_only=False)]
                    eps = [{
                        "disclosure": ep.provenance.disclosure.value,
                        "assertable": bool(ep.assertable),
                    } for ep in mem.store.episodes(uid, include_retired=True)]
                    ans = mem.answer(uid, p["query"])
                    ans = ans if isinstance(ans, str) else str(ans)
                    rec = {"probe_id": p["probe_id"], "cell": p["cell"],
                           "edges": edges, "episodes": eps,
                           "answer": ans,
                           "answer_class": classify_answer(ans, p["value_key"]),
                           "commit": COMMIT}
                finally:
                    mem.close()
            out.write(json.dumps(rec, sort_keys=True) + "\n")
            out.flush()
            print(p["probe_id"], rec["answer_class"],
                  [f'{e["relation"]}:{e["disclosure"]}' for e in rec["edges"]])

    # summarize
    recs = [json.loads(l) for l in open(out_path)]
    summary = {"commit": COMMIT, "src_dirty": bool(DIRTY_SRC), "model": MODEL,
               "cells": {}}
    for cell in "ABCD":
        cr = [r for r in recs if r["cell"] == cell]
        tpc = [r for r in cr if any(e["relation"] == "third_party_claim"
                                    for e in r["edges"])]
        tpc_q = [r for r in tpc
                 if all(e["disclosure"] == "quarantined"
                        for e in r["edges"]
                        if e["relation"] == "third_party_claim")]
        summary["cells"][cell] = {
            "n": len(cr),
            "third_party_claim_probes": len(tpc),
            "tpc_all_quarantined": len(tpc_q),
            "grounded_probes": sum(
                1 for r in cr
                if any(e["disclosure"] == "mentionable" for e in r["edges"])),
            "answers": {k: sum(1 for r in cr if r["answer_class"] == k)
                        for k in ("asserted", "hedged", "absent")},
        }
    with open(os.path.join(HERE, "baseline_main_summary.json"), "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
