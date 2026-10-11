# 0044 v1.3 §2c-ii probe (research, 2026-10-11). Run from the repository root: PYTHONPATH=src python <this file>.
from datetime import datetime, timezone, timedelta
from veracium.graph import apply_supersession
from veracium.schema import DEFAULT_RELATIONS, Disclosure, Edge, EvidenceAuthor, Provenance
from veracium.store.sqlite import SqliteStore
from veracium.asof.resolve import resolve_as_of
def e(i,o): return Edge(id=i,user_id="u",subject="user",relation="prefers",object=o,
    provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,evidence_ref="ev",disclosure=Disclosure.MENTIONABLE))
def run(reinstate):
    s=SqliteStore(":memory:"); s.add_edge(e("p","oat milk")); n=e("i","window seats"); apply_supersession(s,n,DEFAULT_RELATIONS); s.add_edge(n)
    t=[x for x in s.edges("u",active_only=False) if x.id=="p"][0].invalidated_at
    if reinstate:
        with s._write_txn(): s._reinstate_edge_row("p")
    for label,T in (("now",datetime.now(timezone.utc)),("in retired window",t+timedelta(microseconds=1))):
        a=resolve_as_of(s,"u",T)
        print(("reinstated" if reinstate else "control   "), label.ljust(18), sorted((f.edge.object, f.resolution.outcome, f.resolution.tag) for f in a.facts))
run(False); run(True)
