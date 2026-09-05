#!/usr/bin/env python3
"""0029 V-COMPAT — the frozen PRE-FEATURE oracle over the four surfaces V-INERT
names: recall (unscoped and scoped), the context block, EXPORT, and the MCP
tool results. Captured on the 0027 V10 PATTERN (the oracle must predate the
mechanism it judges), from the tree BEFORE any journaling code existed —
main `1fc357f4` (2026-09-05) — and frozen as `pre_feature_capture.json`.

V-COMPAT (specs/0029 §6): "with no consumer, every existing surface
reproduces the frozen pre-feature oracle byte-identically". The 0027 oracle
captures recall projections only; 0029's invariant names export and MCP too,
so this file captures all four (internal co-check, research, 2026-09-05).

DETERMINISTIC: fixed edge ids, fixed timestamps, a scripted extractor and a
scripted answerer (no model, no uuid, no clock). Rerunning REGENERATES the
capture from the live tree — run it only at the pre-feature commit; afterwards
the committed JSON is the frozen truth and `tests/test_0029_carrier.py::
test_no_consumer_behavior_identical` compares the journaling store's four
surfaces against it.

The MCP surface is captured through the `*_impl` functions (the tool bodies,
testable without the SDK) under `capability="direct"` for the user-authored
facts and the default for the third-party one — the Phase A surface as shipped
in 0.19.0.
"""
import json
import pathlib
import sys
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from veracium import Memory, MemoryConfig                                   # noqa: E402
from veracium.schema import Edge, Provenance, EvidenceAuthor, Disclosure    # noqa: E402
from veracium.store.sqlite import SqliteStore                              # noqa: E402
from veracium.portability import export_memory                            # noqa: E402
from veracium import mcp_server as M                                       # noqa: E402

U = "v0029-oracle-user"
T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
HERE = pathlib.Path(__file__).resolve().parent
FROZEN = HERE / "pre_feature_capture.json"


def _edge(i, subject, relation, obj, *, note="", active=True, days=0,
          author=EvidenceAuthor.USER, disclosure=Disclosure.MENTIONABLE,
          reason=None):
    t = T0 + timedelta(days=days)
    e = Edge(id=f"e-0029-{i:03d}", user_id=U, subject=subject, relation=relation,
             object=obj, note=note, valid_from=t,
             provenance=Provenance(author_of_evidence=author, evidence_ref=f"ev-{i:03d}",
                                   observed_at=t, disclosure=disclosure))
    if not active:
        e.invalidated_at = t + timedelta(days=10)
        e.invalidation_reason = reason or "superseded"
    return e


def build_store(path):
    """Fixed ids, fixed instants, every disclosure class, active and retired
    rows, a functional contention, collapse duplicates — the shapes recall,
    export and MCP each render differently."""
    store = SqliteStore(str(path))
    edges = []
    for i, topic in enumerate(["gardening tulips", "chess openings", "marathon training",
                               "sourdough baking", "jazz piano", "kayak rivers"]):
        edges.append(_edge(i, "user", "enjoys", topic, days=i))
    edges.append(_edge(10, "user", "located_at", "Porto", days=3))
    edges.append(_edge(11, "user", "located_at", "Lisbon", days=1, active=False))   # superseded history
    edges.append(_edge(12, "user", "works_as", "carpenter", days=2))
    edges.append(_edge(13, "user", "has_pet", "a cat", note="named Minerva", days=4))
    edges.append(_edge(14, "user", "has_pet", "a cat", days=5))                     # collapse duplicate
    edges.append(_edge(15, "user", "timezone", "pacific", days=5))
    edges.append(_edge(16, "user", "timezone", "eastern", days=6))                  # contention
    edges.append(_edge(20, "org:scam", "third_party_claim", "user owes $500", days=7,
                       author=EvidenceAuthor.THIRD_PARTY, disclosure=Disclosure.QUARANTINED))
    edges.append(_edge(21, "user", "prefers", "window seats", days=8,
                       author=EvidenceAuthor.THIRD_PARTY, disclosure=Disclosure.USE_ONLY))
    edges.append(_edge(22, "user", "deadline", "tax filing", days=9, active=False, reason="lapsed"))
    edges.append(_edge(23, "user", "uses_tool", "vim", days=2, active=False, reason="disputed"))
    for e in edges:
        store.add_edge(e)
    return store


class _Scripted:
    """The scripted extractor/answerer: deterministic text for every call. A
    structured request (a JSON schema) gets an empty extraction; free text gets
    one fixed answer. No path here depends on the prompt's content."""
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        if json_schema is not None:
            return json.dumps({"triples": [], "episode": "scripted"})
        return "scripted answer"


QUERIES = ["marathon training", "where does the user live", "cat", "timezone", ""]


def _no_dup_pairs(pairs):
    """The 0026 evidence-boundary rule: JSON at a boundary is parsed with a
    duplicate-key-REFUSING decoder, never a last-wins one."""
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"duplicate key {k!r} in export header")
        d[k] = v
    return d


def capture(store, tmpdir):
    """The four surfaces, each as JSON-able, deterministic values."""
    mem = Memory(llm=_Scripted(), store=store,
                 config=MemoryConfig(db_path=str(tmpdir / "unused.db"),
                                     wiki_recompile_after_writes=0))
    out = {"recall": {}, "context": {}, "export": None, "mcp": {}, "excluded": None}
    for q in QUERIES:
        r = mem.recall(U, q or None, token_budget=4000)
        out["recall"][q] = {"grounded": r.grounded, "unverified": r.unverified}
        out["context"][q] = r.context
    exp_path = tmpdir / "export.jsonl"
    export_memory(store, U, exp_path)
    # The export is JSON LINES (one record per line); keep the LINES verbatim —
    # byte identity per record is the claim, not structural equality. TWO fields
    # are store/clock identity rather than behaviour and drift between any two
    # captures (measured: exactly `exported_at` and `provenance.origin`, two
    # runs at 1fc357f4): the exporter's wall-clock header stamp and the origin
    # uuid the store mints at create. Both literals are substituted BYTE-WISE
    # (no re-serialisation) and named under "excluded" so the narrowing is
    # visible; the comparison asserts everything else identical.
    lines = exp_path.read_text().splitlines()
    origin = store.local_origin()
    stamp = json.loads(lines[0], object_pairs_hook=_no_dup_pairs)["exported_at"]
    out["export"] = [ln.replace(origin, "<store-origin>").replace(stamp, "<exported-at>")
                     for ln in lines]
    # the exclusion is recorded as a MEASUREMENT (which fields, how many lines
    # each touched), never as the values — the values are what drift
    out["excluded"] = {"fields": ["provenance.origin", "exported_at"],
                       "substitutions": {"provenance.origin": sum(origin in ln for ln in lines),
                                         "exported_at": sum(stamp in ln for ln in lines)},
                       "why": "store identity and export clock — not consumer behaviour"}
    out["mcp"]["recall"] = M.recall_impl(mem, U, "where does the user live")
    out["mcp"]["answer"] = M.answer_impl(mem, U, "where does the user live?")
    out["mcp"]["maintain_keys"] = sorted(M.maintain_impl(mem, U).keys())
    return out


def main():
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp(prefix="oracle-0029-"))
    store = build_store(d / "oracle.db")
    try:
        got = capture(store, d)
    finally:
        store.close()
    FROZEN.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n")
    print(f"captured {FROZEN.name}: recall×{len(got['recall'])}, export keys {sorted(got['export'])[:6]}…, mcp {sorted(got['mcp'])}")


if __name__ == "__main__":
    main()
