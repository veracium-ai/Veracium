# 0044 v1.3 §2c-ii probe (research, 2026-10-11). Run from the repository root: PYTHONPATH=src python <this file>.
from veracium.graph import apply_supersession
from veracium.schema import DEFAULT_RELATIONS as R, Disclosure as D, Edge, EvidenceAuthor as A, Provenance
from veracium.store.sqlite import SqliteStore
from veracium.scope_linkage import identity_digest_of
from veracium.store import revocation as rv
def e(i,o,src): return Edge(id=i,user_id="u",subject="user",relation="measures",object=o,
    provenance=Provenance(author_of_evidence=A.USER,evidence_ref="ev",disclosure=D.MENTIONABLE,source_id=src))
s=SqliteStore(":memory:"); s.add_edge(e("p","weight 78 kg","feed-A")); n=e("i","weight 80 kg","feed-B"); apply_supersession(s,n,R); s.add_edge(n)
rv.revoke_source(s,"u",identity_digest_of(None,"feed-A",s.local_origin()),"revoke","policy","2026-08-21T00:00:00Z")
p=[x for x in s.edges("u",active_only=False,include_quarantined=True) if x.id=="p"][0]
print("after revoking feed-A, the retired prior's reason:", p.invalidation_reason)
