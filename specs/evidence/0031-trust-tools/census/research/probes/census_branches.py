"""Research's re-measure of two branches dev's extended census found (0031 trust-tools v0.14.1).

    python census_branches.py SCRATCH_DIR

1. correct() on an OTHER-subject edge (person:alice): CorrectionRefused, and the writes it commits before raising.
2. recall_impl, the lookup's recall, under wiki recompilation OFF (wiki_recompile_after_writes=0) and at the default:
   an empty user with the query "empty", a user with a fact and a query, and a user with a fact and no query.
Every write statement on the store's one connection during the call, by (operation, table). No model is called.
"""
import os
import re
import sys

from veracium import Memory, MemoryConfig
from veracium.mcp_server import recall_impl
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance

SCRATCH = sys.argv[1]
U = "u"
OP = re.compile(r"^\s*(INSERT(?:\s+OR\s+\w+)?|REPLACE|UPDATE(?:\s+OR\s+\w+)?|DELETE)\b(?:\s+INTO|\s+FROM)?\s+[\"`]?(\w+)", re.I)


def mem(name, subject=None, **cfg):
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=os.path.join(SCRATCH, f"{name}.db"),
               scope_groups={}, require_source_id=False, **cfg))
    if subject:
        m.store.add_edge(Edge(id="e1", user_id=U, subject=subject, relation="lives_in", object="Paris",
                              provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev1",
                                                    disclosure=Disclosure.MENTIONABLE)))
    return m


def traced(label, m, fn):
    st = []
    m.store._conn.set_trace_callback(st.append)
    try:
        fn(); out = "ok"
    except Exception as e:
        out = type(e).__name__
    m.store._conn.set_trace_callback(None)
    ops = {}
    for s in st:
        mm = OP.match(s)
        if mm:
            k = f"{re.sub(r'\s+', ' ', mm.group(1).upper())} {mm.group(2)}"; ops[k] = ops.get(k, 0) + 1
    print(f"{label:58} -> {out:18} {dict(sorted(ops.items()))}")
    m.close()


print("default MemoryConfig wiki_recompile_after_writes =", MemoryConfig().wiki_recompile_after_writes)
m = mem("refused", "person:alice", wiki_recompile_after_writes=0)
traced("correct, an OTHER-subject edge (person:alice)", m, lambda: m.correct(U, "e1", "Rome"))
for tag, cfg in (("recompilation 0", {"wiki_recompile_after_writes": 0}), ("default config", {})):
    m = mem(f"empty-{tag}", None, **cfg); traced(f"{tag}: recall_impl, empty user, query 'empty'", m, lambda: recall_impl(m, U, "empty"))
    m = mem(f"fact-q-{tag}", "user", **cfg); traced(f"{tag}: recall_impl, a fact, a query", m, lambda: recall_impl(m, U, "where do I live"))
    m = mem(f"fact-noq-{tag}", "user", **cfg); traced(f"{tag}: recall_impl, a fact, no query", m, lambda: recall_impl(m, U, None))
