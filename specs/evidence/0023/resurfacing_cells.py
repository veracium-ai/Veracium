"""specs/0023 — the resurfacing probe cells R1-R4 (research's D-extension §5
draft corpus, `paper2/freeze/resurfacing_cells_draft.md`), EXECUTED against
the shipped surface: revoke a source → write → (lift) → what the STORE
ARTIFACT and the RECALL BOUNDARY show.

This is dev's MANIFEST PIN of the registered expectations (2026-09-04): the
observations below are what shipped behaviour produces, recorded as data the
instrument compares against, never taken on report. `resurfacing_cells_pin.json`
beside this file is the frozen output; `tests/test_0023_resurfacing_pin.py`
regenerates it and asserts equality, so the surface cannot drift under the
registered expectations silently. Digests are store-minted per database, so
they are recorded as MATCH booleans, not values.

Probe need the cells do not state (found at the first execution): every
relation a cell writes MUST be in the store's relation vocabulary
(`DEFAULT_RELATIONS`) — an out-of-vocabulary relation is dropped as `invalid`
at ingest and the stripped half of R3 silently vanished from the artifact.

WHAT THE EXACT DISCLOSURES HERE DO AND DO NOT MEAN (research's runner,
2026-09-05): this generator uses a SCRIPTED extractor that always emits an
ordinary relation (`located_at`, `works_as`), so R2/R3's stripped records read
`use_only`. Under a LIVE extractor the same text can be routed to the
`third_party_claim` relation, and the relation leg of `_disclosure_for` then
returns QUARANTINED before either trust leg is consulted (specs/0001/0019).
The cells' INVARIANT is therefore not "use_only" but: `assertable == False`
on every record; disclosure in {use_only, quarantined} — never mentionable,
the value never reaches GROUNDED; no `birth_revocation_digest` (permanently
outside revocation's reach, the honest residual); and the completeness
statement's class-(c) count SEES the stripped records. The pinned JSON
stays exact for THIS generator; the by-name test asserts the invariant.
Ingest configuration, for anyone reproducing the cells: author THIRD_PARTY,
no evidence context (the absent-context floor), `source_id` per cell.
"""
import json, tempfile
from veracium import Memory, MemoryConfig, EvidenceAuthor
from veracium.schema import Disclosure
from veracium.scope_linkage import identity_digest_of
from veracium.store import revocation as rv

U = "u"; AT = "2026-09-04T00:00:00Z"; S = "feed-1"

class Fake:
    def __init__(self, scripts): self._s = list(scripts); self.i = 0
    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self._s[self.i % len(self._s)]; self.i += 1
        return out if isinstance(out, str) else json.dumps(out)

def script(value, relation="located_at"):
    return {"triples": [{"subject": "user", "relation": relation, "object": value,
                         "volatility": "durable"}],
            "episode": f"the feed reported the user is {relation} {value}"}

def mem(d, scripts):
    return Memory(llm=Fake(scripts), config=MemoryConfig(db_path=f"{d}/m.db", wiki_recompile_after_writes=0))

def store_facts(m, rep):
    edges = m.store.edges(U, active_only=False, include_quarantined=True)
    eps = m.store.episodes(U, include_retired=True)
    return {"edges": [{"object": e.object, "disclosure": e.provenance.disclosure.value,
                       "assertable": bool(e.assertable), "active": bool(e.active)} for e in edges],
            "episodes": [{"disclosure": ep.provenance.disclosure.value, "assertable": bool(ep.assertable)} for ep in eps],
            "report": {"facts": rep.get("facts"), "quarantined": rep.get("quarantined"), "quarantined_at_birth": rep.get("quarantined_at_birth"), "birth_revocation_digest_present": rep.get("birth_revocation_digest") is not None}}

def consequence(m, value, query):
    r = m.recall(U, query)
    return {"value_in_grounded": value in r.grounded, "value_in_unverified": value in r.unverified,
            "value_in_context": value in r.context}

def revoke(m, action="revoke"):
    dg = identity_digest_of(None, S, m.store.local_origin())
    st = rv.revoke_source(m.store, U, dg, action, "operator", AT)
    return dg, st

def observe() -> dict:
    out = {"cells": {}}


    # R1 — revoked source, identified rewrite
    d = tempfile.mkdtemp(); m = mem(d, [script("Porto"), "no"])
    dg, _ = revoke(m)
    rep = m.remember(U, "feed says the user moved to Porto", author=EvidenceAuthor.THIRD_PARTY, source_id=S)
    out["cells"]["R1"] = {"values": ["Porto"], "stored": store_facts(m, rep), "digest_matches_source": rep.get("birth_revocation_digest") == dg,
                          "consequence": consequence(m, "Porto", "where does the user live?")}
    m.close()

    # R2 — strip-and-rewrite (no source_id)
    d = tempfile.mkdtemp(); m = mem(d, [script("Lisbon"), "no"])
    dg, _ = revoke(m)
    rep = m.remember(U, "feed says the user moved to Lisbon", author=EvidenceAuthor.THIRD_PARTY)   # source_id ABSENT
    st_dry = rv.revoke_source(m.store, U, dg, "revoke", "operator", AT, dry_run=True)
    out["cells"]["R2"] = {"values": ["Lisbon"], "stored": store_facts(m, rep),
                          "statement": {"counts": st_dry["counts"], "complete": st_dry["complete"], "direct": len(st_dry["direct"])},
                          "consequence": consequence(m, "Lisbon", "where does the user live?")}
    m.close()

    # R3 — hybrid: one identified, one stripped, distinct values
    d = tempfile.mkdtemp(); m = mem(d, [script("Braga", "located_at"), script("carpenter", "works_as"), "no"])
    dg, _ = revoke(m)
    rep_a = m.remember(U, "feed: the user lives in Braga", author=EvidenceAuthor.THIRD_PARTY, source_id=S)
    rep_b = m.remember(U, "feed: the user works as a carpenter", author=EvidenceAuthor.THIRD_PARTY)
    st_dry = rv.revoke_source(m.store, U, dg, "revoke", "operator", AT, dry_run=True)
    out["cells"]["R3"] = {"values": {"identified": "Braga", "stripped": "carpenter"},
                          "stored": store_facts(m, rep_b), "report_identified": {"quarantined_at_birth": rep_a.get("quarantined_at_birth"), "digest_matches_source": rep_a.get("birth_revocation_digest") == dg},
                          "statement": {"counts": st_dry["counts"], "complete": st_dry["complete"], "direct": len(st_dry["direct"])},
                          "consequence": {"Braga": consequence(m, "Braga", "where does the user live and work?"),
                                          "carpenter": consequence(m, "carpenter", "where does the user live and work?")}}
    m.close()

    # R4 — lift boundary
    d = tempfile.mkdtemp(); m = mem(d, [script("Faro"), "no"])
    dg, _ = revoke(m)
    rep = m.remember(U, "feed says the user moved to Faro", author=EvidenceAuthor.THIRD_PARTY, source_id=S)
    _, lift_st = revoke(m, "lift")
    out["cells"]["R4"] = {"values": ["Faro"], "stored_after_lift": store_facts(m, rep), "digest_matches_source": rep.get("birth_revocation_digest") == dg,
                          "consequence_after_lift": consequence(m, "Faro", "where does the user live?")}
    m.close()
    return out


if __name__ == "__main__":
    print(json.dumps(observe(), indent=1, sort_keys=True))
