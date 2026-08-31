#!/usr/bin/env python3
"""0027 §6a acceptance manifest — FROZEN evaluation population (v2, round-5).

Authored by research, BEFORE implementation (R3-6 / round-4 finding 1). Round-5
finding R5-2 rework:
  * PARAPHRASE cases now use ENTITY subjects (not "user"). Shipped lexical recall
    admits a user-subject edge even at ZERO overlap (base = 1 + 2*overlap), which
    made the old cases trivially recall@10 = 1.0. An entity-subject edge enters
    lexical scoring ONLY on overlap>0 (base = 3*overlap), so a zero-overlap
    paraphrase query genuinely misses it lexically — the recovery is then a real
    measurement of the semantic lane.
  * The FIXTURE-CONSTRUCTION PROTOCOL is pinned (spec §6a): each case runs in an
    ISOLATED store = the target edge + a fixed distractor set; fixed observed_at /
    valid_from / insertion order / budget / empty wiki / no higher-priority
    classes. See §6a; the per-case params ride the manifest `fixture` block.
  * Preregistered NON-BLIND (Quentin-approved 2026-08-30): accept cases are in
    plaintext + digest; the tuning PROCEDURE is frozen in §6a (only
    semantic_min_cosine is tunable, on the `tune` split, before any accept run).

Deterministic: re-running reproduces manifest.json byte-for-byte.
Portable: writes beside THIS file (no absolute paths). `--check` verifies the
committed manifest matches without writing.

Expected answers are CONTENT KEYS ("subject|relation|object"), resolved to the
ingested edge id at run time. SYNTHETIC fixtures — review case quality before use.
"""
import json, hashlib, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "manifest.json")

# Fixed fixture parameters (pinned so the harness cannot determine the result
# after freezing — R5-2 point 2). Times are fixed ISO instants; the isolated
# store holds the target + DISTRACTORS unrelated (entity) edges.
FIXTURE = {
    "store": "isolated-per-case",
    "distractors": 19,                 # target + 19 = 20 edges; recall@10 non-trivial
    "distractor_source": "the other cases' target edges (deterministic, per §6a)",
    # R7-1: ONE timestamp for all 20 edges left lexical ranks TIE-BROKEN BY
    # NOTHING before fusion — `_lexical_scored` sorts (score, -observed_at),
    # `edges()` has no contractual order, and the post-fusion edge_id
    # tie-break cannot repair ranks assigned before it (the reviewer measured
    # top-10 identity changes in 40/100 cases under reversed insertion).
    # Every edge in a fixture store now gets a DISTINCT fixed instant by
    # POSITION: insertion position k (target k=0, then the 19 distractor_ids
    # in listed order k=1..19) has observed_at = valid_from = base + k
    # seconds. Same calendar day (the _cover coverage term sees one day, as
    # before); total order within every store; reversal-invariant by
    # construction, asserted by the gate.
    "observed_at": "2026-01-01T00:00:00Z + position seconds (see timestamp_rule)",
    "valid_from": "2026-01-01T00:00:00Z + position seconds (see timestamp_rule)",
    "timestamp_rule": "edge at insertion position k gets "
                      "2026-01-01T00:00:0{k}Z semantics: base "
                      "2026-01-01T00:00:00Z plus k seconds, k=0 the target, "
                      "k=1..19 the distractor_ids in listed order — distinct "
                      "within every store, one calendar day",
    "insertion_order": "target first, then the 19 distractor_ids in listed order",
    "token_budget": 4000,
    "wiki": "empty",
    "higher_priority_classes": "none (no commitments/contested/episodes)",
    "max_subgraph_edges": 40,
    "principal": None,
    "embedder": "all-MiniLM-L6-v2 (pinned; vectors shipped at implementation)",
    # R6-2: the backend is part of the frozen topology. SqliteStore's edges()
    # has no ORDER BY — determinism rests on the fused-order edge_id tiebreak,
    # which is why every target's edge_id is FROZEN below (e-{case_id}), never
    # runtime-resolved.
    "backend": "SqliteStore",
    "determinism": "edges() has no ORDER BY; final-order ties break on frozen "
                   "edge_id (spec §4a Stage 2)",
}

def C(cid, subj, rel, obj, note, query, split, label, disclosure=None):
    # R6-2: the target's edge id is FROZEN (e-{case id}) — ids are the final
    # fused-order tiebreak, so they must be fixed, not runtime-resolved.
    row = {"id": cid, "edge_id": f"e-{cid}",
           "subject": subj, "relation": rel, "object": obj,
           "note": note, "query": query,
           "expected_key": f"{subj}|{rel}|{obj}", "split": split, "label": label}
    if disclosure is not None:
        row["disclosure"] = disclosure
    return row

cases = []

# ---- 40 TUNE: ENTITY-subject paraphrase, ~zero shipped-token overlap ----
# (subject, relation, object, note, query)
tune = [
    ("kyoto","known_for","ancient temples","toured in april","which city did i explore for its old shrines"),
    ("miso","species","cat","tabby, adopted 2021","what kind of creature is my furry companion"),
    ("acme robotics","headquartered","boston","my employer","where is the firm that pays my salary based"),
    ("green curry","cuisine","thai","my favorite dish","what style of cooking is the meal i love most"),
    ("penicillin","triggers","allergic reaction","severe for me","which drug should a clinic never give me"),
    ("portland","is","my birthplace","grew up there","where did i spend my childhood"),
    ("el capitan","activity","rock climbing","weekend passion","what sport do i pursue on granite walls"),
    ("model 3","manufacturer","tesla","my blue car","what brand of vehicle sits in my driveway"),
    ("jordan","relation","my spouse","wed in 2019","who did i marry"),
    ("mit","conferred","my masters degree","computer science","where did i earn my graduate diploma"),
    ("foundation","author","isaac asimov","my favorite series","who wrote the sci-fi saga i adore"),
    ("steinway","instrument","grand piano","ten years playing","what do i perform music on at home"),
    ("open offices","reaction","i dislike them","prefer quiet","what workspace setup annoys me"),
    ("castilian","is","the spanish tongue","i speak it","which iberian language can i converse in"),
    ("boston marathon","goal","i want to run it","training begun","what long-distance race do i aspire to finish"),
    ("the times","format","daily newspaper","i subscribe","what publication do i pay to read each morning"),
    ("dr patel","specialty","cardiology","treats me","who is the physician for my heart"),
    ("riverside fitness","type","gym","member since jan","where do i go to lift weights"),
    ("oat latte","drink","coffee","no sugar, my usual","what beverage do i order at the cafe"),
    ("sam","relation","my child","age seven","who is my kid"),
    ("pixel 8","device","smartphone","my android","which handset do i carry daily"),
    ("golden state warriors","sport","basketball","my team","which hoops club do i cheer for"),
    ("tofu stir fry","diet","vegetarian","no meat for me","what eating pattern do i follow"),
    ("first national","institution","bank","my accounts","where do i keep my savings"),
    ("atlas migration","context","work project","q3 deadline","what am i building at the office"),
    ("alex","role","my mentor","career guide","who advises me on my profession"),
    ("tall ladders","phobia","fear of heights","i avoid them","what am i frightened of"),
    ("monstera","kind","houseplant","on my balcony","what greenery do i tend at home"),
    ("bicycle","means","my commute","thirty minutes","how do i travel to work"),
    ("autumn","preference","favorite season","love the foliage","which part of the year do i like best"),
    ("blue note","genre","jazz","my focus playlist","what music helps me concentrate"),
    ("hostels","style","backpacking","trains and dorms","how do i prefer to travel abroad"),
    ("loud chewing","irritant","pet peeve","in meetings","what minor habit bothers me"),
    ("humane society","cause","animal shelter","i volunteer saturdays","where do i give my time"),
    ("dawn","habit","early riser","up at five thirty","when do i wake in the morning"),
    ("tonkotsu ramen","role","comfort food","on rainy days","what do i eat to cheer myself up"),
    ("patagonia","desire","dream destination","for the glaciers","where would i most love to journey"),
    ("walnut desk","craft","woodworking","i built it","what handiwork am i skilled at"),
    ("ocean conservancy","support","charity","monthly donor","what cause do i fund each month"),
    ("sourdough","hobby","bread baking","weekend ritual","what do i make from flour on days off"),
]
for i,(s,r,o,n,q) in enumerate(tune, 1):
    cases.append(C(f"tune-{i:02d}", s,r,o,n,q,"tune","paraphrase"))

# ---- 20 ACCEPT: held-out ENTITY-subject paraphrase (recovery criterion) ----
acc_para = [
    ("kinkaku-ji","location","kyoto","golden temple i saw","which shrine did i visit on my japan trip"),
    ("ollie","species","dog","golden retriever","what animal is my four-legged friend"),
    ("northwind labs","industry","biotech","where i work","what sector is my company in"),
    ("injera","cuisine","ethiopian","i seek it out","what food tradition do i love hunting for"),
    ("shrimp","triggers","allergy","gives me hives","what seafood makes me break out"),
    ("tucson","climate","desert","my hometown","what kind of landscape did i grow up in"),
    ("wheel throwing","art","pottery","evening class","what clay craft do i study after work"),
    ("outback","maker","subaru","my camping car","what vehicle do i take on trips"),
    ("scripps","awarded","phd","marine biology","where did i complete my doctorate"),
    ("wolf hall","genre","historical fiction","tudor era","what type of novel is on my shelf"),
    ("yo-yo ma","instrument","cello","i play in an ensemble","what do i bow in the orchestra"),
    ("putonghua","language","mandarin","hsk 4","which chinese dialect can i speak"),
    ("dinghy","goal","learn to sail","lessons booked","what water skill am i taking up"),
    ("dr okafor","field","dermatology","my skin doctor","who cares for my complexion"),
    ("cortado","drink","espresso","extra hot","what small coffee is my regular"),
    ("anfield","club","liverpool","i support them","which english side do i follow"),
    ("salmon","diet","pescatarian","fish only","what are my food limits"),
    ("light rail","commute","train","two stops","how do i get to the office each day"),
    ("brush lettering","craft","calligraphy","wedding invites","what elegant handwriting can i do"),
    ("reykjavik","desire","iceland trip","for the auroras","where do i dream of vacationing for the lights"),
]
for i,(s,r,o,n,q) in enumerate(acc_para, 1):
    cases.append(C(f"acc-para-{i:02d}", s,r,o,n,q,"accept","paraphrase"))

# ---- 20 ACCEPT: exact-match (non-regression control; HIGH-overlap query) ----
# subject=user is DELIBERATE here: this control tests that a high-overlap exact
# match is not DISPLACED once semantic is on, not paraphrase recovery.
acc_exact = [
    ("user","favorite_color","blue","",  "favorite color blue"),
    ("user","birthday","june 12","",     "birthday june 12"),
    ("user","shoe_size","ten","",        "shoe size ten"),
    ("user","blood_type","o negative","","blood type o negative"),
    ("user","office","building 4","",    "office building 4"),
    ("user","manager","priya","",        "manager priya"),
    ("user","laptop","macbook pro","",   "laptop macbook pro"),
    ("user","timezone","pacific","",     "timezone pacific"),
    ("user","desk","seat 22","",         "desk seat 22"),
    ("user","badge","id 7788","",        "badge id 7788"),
    ("user","parking","spot b12","",     "parking spot b12"),
    ("user","extension","x4501","",      "extension x4501"),
    ("user","tshirt_size","large","",    "tshirt size large"),
    ("user","favorite_number","seven","","favorite number seven"),
    ("user","email_client","thunderbird","","email client thunderbird"),
    ("user","keyboard","dvorak","",      "keyboard dvorak"),
    ("user","monitor","dell u2720","",   "monitor dell u2720"),
    ("user","standing_desk","yes","",    "standing desk yes"),
    ("user","lunch_time","noon","",      "lunch time noon"),
    ("user","favorite_sport","tennis","","favorite sport tennis"),
]
for i,(s,r,o,n,q) in enumerate(acc_exact, 1):
    cases.append(C(f"acc-exact-{i:02d}", s,r,o,n,q,"accept","exact"))

# ---- 20 ACCEPT: trust-labelled (classification-entry control) ----
acc_trust = [
    ("colleague","recommends","dentist dr lee","relayed by user","who did a coworker suggest for teeth","USE_ONLY"),
    ("neighbor","claims","road closes friday","hearsay","what did a neighbor say about the street","QUARANTINED"),
    ("user","prescribed","medication x","by dr patel","what medicine was i given","MENTIONABLE"),
    ("friend","mentioned","new sushi place","third-party","which restaurant did a friend bring up","USE_ONLY"),
    ("article","states","market fell","unverified source","what did the news item assert about markets","QUARANTINED"),
    ("user","confirmed","meeting monday","","when is my confirmed meeting","MENTIONABLE"),
    ("vendor","promises","delivery tuesday","supplier claim","what did the vendor commit to","USE_ONLY"),
    ("forum post","alleges","app has bug","anonymous","what did a forum post allege","QUARANTINED"),
    ("user","owns","house on elm st","deed","what property do i own","MENTIONABLE"),
    ("relative","says","reunion in july","relayed","what did a relative say about the gathering","USE_ONLY"),
    ("ad","claims","product cures cold","marketing","what did an advertisement claim","QUARANTINED"),
    ("user","booked","flight to denver","confirmation 88","what trip did i book","MENTIONABLE"),
    ("coworker","reports","server down","relayed","what did a coworker report about the server","USE_ONLY"),
    ("rumor","suggests","layoffs coming","unverified","what does the rumor suggest","QUARANTINED"),
    ("user","paid","rent this month","receipt","what did i pay recently","MENTIONABLE"),
    ("acquaintance","recommends","tax advisor","hearsay","who did an acquaintance recommend for taxes","USE_ONLY"),
    ("blog","asserts","diet works","no evidence","what did a blog assert about the diet","QUARANTINED"),
    ("user","scheduled","dentist friday","","what appointment did i schedule","MENTIONABLE"),
    ("stranger","claims","found my wallet","unverified","what did a stranger claim","QUARANTINED"),
    ("partner","noted","anniversary dinner","relayed plan","what did my partner note about dinner","USE_ONLY"),
]
for i,(s,r,o,n,q,d) in enumerate(acc_trust, 1):
    cases.append(C(f"acc-trust-{i:02d}", s,r,o,n,q,"accept","trust",disclosure=d))

# R6-2: EXPLICIT per-case distractor ids — "19 other cases' targets" named
# exactly, not described. Pools are SPLIT- AND LABEL-PURE: a tune case draws
# only from the other tune targets (tuning never depends on accept content —
# the tune-only-pool requirement), and each accept label draws from its own
# 20-case pool (so a paraphrase fixture carries no disclosure-bearing
# distractors). One deterministic rule for every pool: the next 19 targets of
# the same (split, label) in manifest order, wrapping cyclically.
_pools = {}
for c in cases:
    _pools.setdefault((c["split"], c["label"]), []).append(c)
for _pool in _pools.values():
    _ids = [c["edge_id"] for c in _pool]
    _n = len(_ids)
    assert _n >= 20, f"pool too small for 19 distractors: {_n}"
    for _idx, c in enumerate(_pool):
        c["distractor_ids"] = [_ids[(_idx + j) % _n] for j in range(1, 20)]

manifest = {
    "manifest_version": "2.2",
    "spec": "0027-semantic-hybrid-recall",
    "authored": "2026-08-30",
    "authored_by": "research",
    "amended": "2026-08-31 (R6-2 deterministic topology: frozen edge_ids, "
               "explicit split/label-pure distractor_ids, backend named; "
               "R7-1: distinct per-position timestamps — lexical ranks are "
               "tie-free BEFORE fusion, applied before any re-tune or "
               "accept rerun)",
    "amended_by": "dev",
    "blinding": "preregistered non-blind (Quentin-approved 2026-08-30); tuning "
                "procedure frozen in spec §6a",
    "note": ("FROZEN evaluation population, committed before implementation. "
             "PARAPHRASE cases use ENTITY subjects so lexical does not trivially "
             "admit them (R5-2). Expected answers are content keys resolved to "
             "edge_id at run time. Synthetic fixtures — review before use."),
    "fixture": FIXTURE,
    "counts": {"tune": 40, "accept": 60,
               "accept_breakdown": {"paraphrase": 20, "exact": 20, "trust": 20}},
    "cases": cases,
}
blob = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()

if "--check" in sys.argv:
    if not os.path.exists(OUT):
        print("MISSING manifest.json"); sys.exit(1)
    cur = open(OUT, encoding="utf-8").read()
    cur_digest = hashlib.sha256(cur.encode("utf-8")).hexdigest()
    ok = (cur == blob)
    print(f"committed sha256={cur_digest}")
    print(f"regenerated sha256={digest}")
    print("MATCH" if ok else "DRIFT — regenerate")
    sys.exit(0 if ok else 1)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(blob)
print(f"wrote {OUT}")
print(f"cases={len(cases)} (tune={sum(1 for c in cases if c['split']=='tune')}, "
      f"accept={sum(1 for c in cases if c['split']=='accept')})")
print(f"sha256={digest}")
