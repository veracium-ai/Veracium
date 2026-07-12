"""Dataset adapter: conversations (jsonl) -> ingestable events + sampling manifest.

Input is one conversation per line: {"conversation_id": str, "language": str,
"conversation": [{"role": "user"|"assistant", "content": str}, ...]} — the shape
of lmsys-chat-1m records. The gated LMSYS dataset is never committed or fetched
here; export it locally, e.g.:

    from datasets import load_dataset  # after accepting the license on HF
    ds = load_dataset("lmsys/lmsys-chat-1m", split="train")
    with open("lmsys.jsonl", "w") as f:
        for r in ds:
            f.write(json.dumps({"conversation_id": r["conversation_id"],
                                "language": r["language"],
                                "conversation": r["conversation"]}) + "\n")

and pass that path. `fixtures/messy.jsonl` (committed, hand-crafted, no real
PII) lets the harness run without it.

Mapping (proposal §4): one synthetic user_id per conversation; user turns become
USER/"chat" events; a seeded fraction is replayed as THIRD_PARTY/"email" instead
(injection replay); assistant turns are not ingested. Edge cases — empty turns,
huge turns (truncated at a recorded cap), non-English — are kept: they are the
stressors.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from veracium.diagnostics import redact
from veracium.schema import EvidenceAuthor

FIXTURES = Path(__file__).with_name("fixtures") / "messy.jsonl"


def snippet(text: str, cap: int = 120) -> str:
    """Redacted, truncated excerpt — the only form of corpus text a report may
    contain (mirrors veracium's content-free telemetry posture)."""
    s = redact(text.replace("\n", " "))
    return s[:cap] + ("…" if len(s) > cap else "")


def iter_conversations(path, *, n: int = 200, seed: int = 0,
                       inject_frac: float = 0.15, truncate_chars: int = 16000):
    """Load, sample, and map the corpus. Returns (convos, manifest) where convos
    is a list of (user_id, [ {text, author, event_type} ]) and the manifest
    records exactly what ran — coverage is explicit, never silently truncated."""
    path = Path(path)
    records = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    rng = random.Random(seed)
    if len(records) > n:
        records = rng.sample(records, n)

    truncations = 0
    convos = []
    for i, rec in enumerate(records):
        uid = f"robust:{rec.get('conversation_id', i)}"
        turns = []
        for t in rec.get("conversation", []):
            if t.get("role") != "user":
                continue
            text = str(t.get("content", ""))
            if truncate_chars and len(text) > truncate_chars:
                text = text[:truncate_chars]
                truncations += 1
            if rng.random() < inject_frac:
                turns.append({"text": text, "author": EvidenceAuthor.THIRD_PARTY,
                              "event_type": "email"})
            else:
                turns.append({"text": text, "author": EvidenceAuthor.USER,
                              "event_type": "chat"})
        convos.append((uid, turns))

    manifest = {"source": str(path), "n_conversations": len(convos),
                "n_user_turns": sum(len(t) for _, t in convos),
                "seed": seed, "inject_frac": inject_frac,
                "truncate_chars": truncate_chars, "truncated_turns": truncations}
    return convos, manifest
