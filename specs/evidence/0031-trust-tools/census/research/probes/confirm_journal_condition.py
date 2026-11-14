"""When does confirm write an edge_event? (research, 0031 trust-tools v0.13 census)

    python confirm_journal_condition.py SCRATCH_DIR

One edge with NO source, confirmed date-less (so its instant is today 00:00 UTC, before the edge's observed_at), at
confidence 0.9 and at 0.5. The journal choke point writes an event iff the edge's stored bytes change, so the 0.9 case
(nothing changes) writes none and the 0.5 case (confidence raised to 0.9) writes one. No model is called.
"""
import os
import re
import sys

from veracium import Memory, MemoryConfig
from veracium.schema import Disclosure, Edge, EvidenceAuthor, Provenance

SCRATCH = sys.argv[1]
U = "census-user"


def run(label, conf):
    m = Memory(llm=lambda *a, **k: "", config=MemoryConfig(db_path=os.path.join(SCRATCH, f"{label}.db"),
               wiki_recompile_after_writes=0, scope_groups={}, require_source_id=False))
    m.store.add_edge(Edge(id="e1", user_id=U, subject="user", relation="likes", object="x",
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev1",
                                                confidence=conf, disclosure=Disclosure.MENTIONABLE)))
    st = []
    m.store._conn.set_trace_callback(lambda s: st.append(s) if re.match(r"\s*INSERT\s+INTO\s+edge_event", s, re.I) else None)
    m.confirm(U, "e1")
    m.store._conn.set_trace_callback(None)
    print(f"{label:34} confidence {conf} src None: edge_event inserts during confirm = {len(st)}")
    m.close()


run("conf09_nosrc", 0.9)
run("conf05_nosrc", 0.5)
