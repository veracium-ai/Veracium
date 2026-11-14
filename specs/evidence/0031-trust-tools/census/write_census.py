"""Dev's independent write census for the 0031 trust verbs at the pinned source: every SQL write each verb executes,
traced on a real store, plus the provenance (source_id, call_path) of every row the verb adds to edges or episodes, and
the keys of what the verb returns. Run from the repo root with the repo's venv: PYTHONPATH=src python write_census.py"""
import json, os, re, sqlite3, tempfile, collections
from veracium import Memory, MemoryConfig, EvidenceContext

class Stub:
    def __init__(self, fact): self.fact = fact
    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            rel, obj = self.fact
            return json.dumps({"triples": [{"subject": "user", "relation": rel, "object": obj, "volatility": "durable"}],
                               "episode": f"The user said {obj}.", "instructions": []})
        return "summary"

def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


WRITE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b(?:\s+OR\s+\w+)?\s+(?:INTO\s+|FROM\s+)?[\"`]?(\w+)", re.I)

def seeded():
    d = tempfile.mkdtemp(); db = os.path.join(d, "v.db")
    m = Memory(llm=Stub(("located_at", "Berlin")), config=MemoryConfig(db_path=db, require_source_id=False))
    m.remember("u", "I live in Berlin.", date="2026-11-12", context=EvidenceContext.direct(), source_id="src-a")
    m.llm = Stub(("works_at", "Acme"))
    m.remember("u", "I work at Acme.", date="2026-11-12", context=EvidenceContext.direct(), source_id="src-a")
    return m, db

def rows(db, table):
    c = sqlite3.connect(db)
    try: return {r[0]: r for r in c.execute(f"select * from {table}")}
    finally: c.close()

def census(name, call):
    m, db = seeded()
    e1 = next(e.id for e in m.store.edges("u") if e.relation == "located_at")
    ep = sorted(rows(db, "episodes"))[0]
    before = {t: set(rows(db, t)) for t in ("edges", "episodes")}
    stmts = []
    conns = {id(m.store._conn): m.store._conn}
    for c in conns.values(): c.set_trace_callback(stmts.append)
    try: out = call(m, e1, ep)
    except Exception as ex: out = f"RAISED {type(ex).__name__}: {ex}"
    for c in conns.values(): c.set_trace_callback(None)
    writes = collections.Counter()
    for s in stmts:
        mm = WRITE.match(s)
        if mm: writes[(mm.group(1).upper(), mm.group(2))] += 1
    added = {}
    for t in ("edges", "episodes"):
        after = rows(db, t); new = set(after) - before[t]
        for k in sorted(new):
            j = json.loads(after[k][-1], object_pairs_hook=_strict_pairs); prov = j.get("provenance") or {}
            added[f"{t}:{k}"] = {"author": prov.get("author_of_evidence"), "source_id": prov.get("source_id"),
                                 "call_path": prov.get("call_path"), "summary": (j.get("summary") or j.get("object") or "")[:60]}
    keys = sorted(out) if isinstance(out, dict) else (sorted(vars(out)) if hasattr(out, "__dict__") else str(out)[:120])
    print(f"=== {name}"); print("  writes:", dict(sorted(writes.items())))
    for k, v in added.items(): print("  added:", k, v)
    print("  returns:", keys)
    m.close()

census("correct", lambda m, e, ep: m.correct("u", e, "Paris"))
census("dispute", lambda m, e, ep: m.dispute("u", e, reason="not true"))
census("confirm", lambda m, e, ep: m.confirm("u", e))
census("redact edge", lambda m, e, ep: m.redact("u", edge_id=e, reason="subject_request"))
census("redact episode", lambda m, e, ep: m.redact("u", episode_id=ep, reason="subject_request"))
census("forget", lambda m, e, ep: m.forget("u"))
