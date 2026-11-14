"""Dev's EXTENDED write census for the 0031 trust verbs (round 2's TT-R2-02: the happy-path censuses missed two branches):
every SQL write each verb executes on its happy, DENIED and CONDITIONAL branches, traced on SqliteStore's one connection
(set_trace_callback, during the call only), each case on a fresh store. Prints, per case: the outcome (returned or
raised), and the (op, table) writes. Run from the repo root: PYTHONPATH=src .venv/bin/python write_census_branches.py"""
import json, os, re, sqlite3, tempfile, collections, datetime
from veracium import Memory, MemoryConfig, EvidenceContext
from veracium.schema import Edge, Provenance, EvidenceAuthor
from veracium import mcp_server

WRITE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b(?:\s+OR\s+\w+)?\s+(?:INTO\s+|FROM\s+)?[\"`]?(\w+)", re.I)


class Stub:
    def __init__(self, fact): self.fact = fact

    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            rel, obj = self.fact
            return json.dumps({"triples": [{"subject": "user", "relation": rel, "object": obj, "volatility": "durable"}],
                               "episode": f"The user said {obj}.", "instructions": []})
        return "summary"


def fresh(seed=True):
    d = tempfile.mkdtemp(); db = os.path.join(d, "v.db")
    m = Memory(llm=Stub(("located_at", "Berlin")), config=MemoryConfig(db_path=db, require_source_id=False))
    if seed:
        m.remember("u", "I live in Berlin.", date="2026-11-12", context=EvidenceContext.direct(), source_id="src-a")
    return m


def edge_of(m, rel="located_at"):
    return next(e for e in m.store.edges("u") if e.relation == rel)


def add_raw_edge(m, **kw):
    """An edge written directly, for the shapes remember() does not produce (another subject, quarantined)."""
    e = Edge(id=kw.pop("id"), user_id="u", subject=kw.pop("subject", "user"), relation=kw.pop("relation"),
             object=kw.pop("object"), provenance=Provenance(author_of_evidence=kw.pop("author", EvidenceAuthor.USER),
                                                           evidence_ref="census", source_id=kw.pop("source_id", None)), **kw)
    m.store.add_edge(e)
    return e


def redacted_id(m):
    """The edge's id captured BEFORE its redaction (the store's listing omits a redacted edge afterwards)."""
    e = E(m); m.redact("u", edge_id=e, reason="subject_request"); return e


def third_party_id(m):
    """A third-party fact ingested the real way (use_only, not assertable): the store's own shape, never hand-built."""
    m.llm = Stub(("likes", "tea"))
    m.remember("u", "Email: the user likes tea.", date="2026-11-12", author=EvidenceAuthor.THIRD_PARTY)
    return next(x.id for x in m.store.edges("u") if x.object == "tea")   # stored as relation "unclassified"


def run(name, setup, call):
    m = fresh(seed=setup != "empty")
    try:
        target = setup(m) if callable(setup) else None
    except Exception as ex:
        print(f"=== {name}\n  SETUP FAILED: {type(ex).__name__}: {ex}"); m.close(); return
    stmts = []
    m.store._conn.set_trace_callback(stmts.append)
    try:
        out = call(m, target); outcome = "returned " + (",".join(sorted(out)) if isinstance(out, dict) else type(out).__name__)
    except Exception as ex:
        outcome = f"raised {type(ex).__name__}: {str(ex)[:90]}"
    m.store._conn.set_trace_callback(None)
    w = collections.Counter()
    for s in stmts:
        mm = WRITE.match(s)
        if mm: w[f"{mm.group(1).upper()} {mm.group(2)}"] += 1
    print(f"=== {name}\n  outcome: {outcome}\n  writes: {dict(sorted(w.items())) or 'NONE'}")
    m.close()


E = lambda m: edge_of(m).id
# correct
run("correct: happy", E, lambda m, e: m.correct("u", e, "Paris"))
run("correct: OTHER subject (person:alice) -> CorrectionRefused",
    lambda m: add_raw_edge(m, id="e-alice", subject="person:alice", relation="located_at", object="Rome").id,
    lambda m, e: m.correct("u", e, "Oslo"))
run("correct: unknown id", E, lambda m, e: m.correct("u", "e-nope", "Paris"))
run("correct: a redacted (attested) target", redacted_id,
    lambda m, e: m.correct("u", e, "Paris"))
# dispute
run("dispute: happy", E, lambda m, e: m.dispute("u", e, reason="no"))
run("dispute: unknown id", E, lambda m, e: m.dispute("u", "e-nope"))
run("dispute: a redacted (attested) target", redacted_id,
    lambda m, e: m.dispute("u", e))
# confirm
run("confirm: happy (observed_at earlier than the confirmation)", E, lambda m, e: m.confirm("u", e))
run("confirm: a third-party (use_only, not assertable) target, ingested the real way", third_party_id,
    lambda m, e: m.confirm("u", e))
run("confirm: unknown id", E, lambda m, e: m.confirm("u", "e-nope"))
# redact
run("redact: edge, first", E, lambda m, e: m.redact("u", edge_id=e, reason="subject_request"))
run("redact: edge, REPEAT", redacted_id,
    lambda m, e: m.redact("u", edge_id=e, reason="subject_request"))
run("redact: unknown id", E, lambda m, e: m.redact("u", edge_id="e-nope", reason="subject_request"))
run("redact: bad reason", E, lambda m, e: m.redact("u", edge_id=e, reason="not-a-reason"))
# forget
run("forget: a user with data", E, lambda m, e: m.forget("u"))
run("forget: an EMPTY user", "empty", lambda m, e: m.forget("u"))
# the lookup's base: recall_impl exactly as the MCP tool calls it
run("recall_impl: an EMPTY user, query 'empty' (round 2's witness)", "empty",
    lambda m, e: {"ctx": mcp_server.recall_impl(m, "u", "empty")})
run("recall_impl: a user with a fact, query", E, lambda m, e: {"ctx": mcp_server.recall_impl(m, "u", "where do I live")})
run("recall_impl: a user with a fact, no query (proactive)", E, lambda m, e: {"ctx": mcp_server.recall_impl(m, "u", None)})
