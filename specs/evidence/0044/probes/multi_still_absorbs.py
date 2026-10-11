# 0044 v1.3 §2c-ii probe (research, 2026-10-11). Run from the repository root: PYTHONPATH=src python <this file>.
from veracium.graph import apply_supersession
from veracium.schema import DEFAULT_RELATIONS, Disclosure as D, Edge, EvidenceAuthor as A, Provenance
from veracium.store.sqlite import SqliteStore
R={k:(v.model_copy(update={"functional":False}) if k=="measures" else v) for k,v in DEFAULT_RELATIONS.items()}
def e(i,o): return Edge(id=i,user_id="u",subject="user",relation="measures",object=o,
    provenance=Provenance(author_of_evidence=A.USER,evidence_ref="ev",disclosure=D.MENTIONABLE))
s=SqliteStore(":memory:"); s.add_edge(e("p","80")); n=e("i","weight 80"); apply_supersession(s,n,R); s.add_edge(n)
print({x.object: x.invalidation_reason for x in s.edges("u",active_only=False,include_quarantined=True)})
