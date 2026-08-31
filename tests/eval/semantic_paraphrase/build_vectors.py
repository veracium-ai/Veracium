#!/usr/bin/env python3
"""0027 §6a — the SHIPPED pre-computed vectors for the acceptance gate.

Run ONCE, in an environment with sentence-transformers, against the PINNED
model; the emitted `vectors.json` is the committed artifact and the gate
(`tests/eval/test_semantic_recall_gate.py`) needs NO live embedder — the
measurement reproduces byte-for-byte from the shipped vectors (§6a
"Determinism").

The embedded text per target is the spec's §4e embedded-text projection —
"{subject} {relation} {object} {note}" — inlined here because this script
runs WITHOUT veracium installed; the gate spot-welds the inlined form
against `veracium.semantic.embedded_text` at run time, so the two cannot
drift silently.

`--check` re-verifies the committed file's internal shape and digest
WITHOUT the model (no network, no torch).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")
OUT = os.path.join(HERE, "vectors.json")

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def embedded_text(case) -> str:
    # §4e embedded-text projection (gate-verified against veracium.semantic)
    return f"{case['subject']} {case['relation']} {case['object']} {case['note']}"


def check() -> int:
    if not os.path.exists(OUT):
        print("MISSING vectors.json — run build_vectors.py in an environment "
              "with sentence-transformers")
        return 1
    data = json.load(open(OUT, encoding="utf-8"))
    man = json.load(open(MANIFEST, encoding="utf-8"))
    bad = []
    dim = data.get("dim")
    for section in ("targets", "queries"):
        got = data.get(section, {})
        want = ({c["edge_id"] for c in man["cases"]} if section == "targets"
                else {c["id"] for c in man["cases"]})
        if set(got) != want:
            bad.append(f"{section}: keys != the manifest population")
        for k, v in got.items():
            if not (isinstance(v, list) and len(v) == dim
                    and all(isinstance(x, float) for x in v) and any(v)):
                bad.append(f"{section}[{k}]: not a {dim}-float non-zero vector")
                break
    if not isinstance(data.get("embedder_id"), str) or not data["embedder_id"]:
        bad.append("embedder_id missing")
    digest = hashlib.sha256(
        open(OUT, "rb").read()).hexdigest()
    print(f"vectors sha256={digest}")
    for b in bad:
        print(f"PROBLEM: {b}")
    return 1 if bad else 0


def main() -> int:
    if "--check" in sys.argv:
        return check()
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(MODEL)
    # pin the exact snapshot: one embedder_id permanently denotes one
    # behaviour (0027 §4d), so the HF snapshot sha joins the id
    rev = "unknown"
    for base in (os.path.expanduser(
            "~/.cache/huggingface/hub/"
            "models--sentence-transformers--all-MiniLM-L6-v2/snapshots"),):
        if os.path.isdir(base):
            snaps = sorted(os.listdir(base))
            if snaps:
                rev = snaps[0][:12]
    embedder_id = f"all-MiniLM-L6-v2@{rev}"
    man = json.load(open(MANIFEST, encoding="utf-8"))
    cases = man["cases"]
    tgt_texts = [embedded_text(c) for c in cases]
    q_texts = [c["query"] for c in cases]
    tv = m.encode(tgt_texts, normalize_embeddings=False)
    qv = m.encode(q_texts, normalize_embeddings=False)
    dim = int(tv.shape[1])
    data = {
        "note": ("0027 §6a pre-computed vectors — pinned model, committed so "
                 "the acceptance measurement needs no live embedder and "
                 "reproduces byte-for-byte. Regenerating with a different "
                 "model revision is a NEW embedder_id."),
        "model": MODEL,
        "embedder_id": embedder_id,
        "dim": dim,
        "targets": {c["edge_id"]: [float(x) for x in tv[i]]
                    for i, c in enumerate(cases)},
        "queries": {c["id"]: [float(x) for x in qv[i]]
                    for i, c in enumerate(cases)},
    }
    blob = json.dumps(data, indent=1, sort_keys=True) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(blob)
    print(f"wrote {OUT}: {len(cases)} targets + {len(cases)} queries, "
          f"dim {dim}, embedder_id {embedder_id}")
    print(f"sha256={hashlib.sha256(blob.encode()).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
