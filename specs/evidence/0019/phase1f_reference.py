"""SUPERSEDED HISTORICAL PROVENANCE (0019 R2-2): the window-form phase-1f
predicate whose measurement motivated the OPTION-A class choice. NOT the
candidate; NOT portable (hard-codes research-workspace paths). The
normative reference is reference_predicate.py beside this file.

"""
"""Phase 1e (final gate, from 1d): the four fixes + dev's specifics-only refinement. Still shadow.

Fixes over phase 1b:
  F1 tokenizer: apostrophes stripped (no more 'smoothie / 'why' artifacts)
  F2 stemming: suffix-strip stemmer (ing/ed/es/s/er/ly/ment/tion...) both sides
  F3 dates: ISO-date-shaped anchors are DATE-VALIDATED against the session day
     (plausibility window), never text-matched — resolved dates are the
     distiller's documented job
  F4 relation scoping, dev's refinement: idiom-class relations (data-driven:
     median object length >= 5 tokens) get a SPECIFICS-ONLY check (numeric,
     alphanumeric-identifier, and capitalized proper-noun tokens); value-bearing
     relations get the full stemmed hard-anchor check.
"""
import json, re, sys, glob, collections, random, datetime
from pathlib import Path

HARNESS = Path("/home/ubuntu/Dev/veracium/tests/longmemeval")
sys.path.insert(0, str(HARNESS))
import adapter, run_longmemeval as RL          # noqa: E402
from cache import _sha                          # noqa: E402

DS = Path.home() / "Datasets" / "longmemeval"
OUT = Path(__file__).parent

TEMPLATE = {"named","called","known","also","includes","include",
            "using","information","approximately"}
NUMWORDS = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6",
            "seven":"7","eight":"8","nine":"9","ten":"10","first":"1",
            "second":"2","third":"3","fourth":"4","fifth":"5"}
FORMULA_RELS = {"has_formula","formula","equation","defined_as"}
STOP = set("""a an the of to in on at for from by with and or but as is are was
were be been being it its this that these those i you he she they we my your
his her their our me him them us do does did doing have has had having will
would can could may might should must not no yes about into over under between
through during before after above below up down out off again further then
once here there when where why how all any both each few more most other some
such only own same so than too very s t just don now""".split())

DERIV = [("ation","ate"),("ication","ify"),("tion","te"),("sion","de"),
         ("ance","e"),("ence","e"),("ivity","e"),("ity",""),("ness",""),
         ("ment",""),("age",""),("al",""),("ual",""),("ive","e"),("able","e"),
         ("ible",""),("ous",""),("ful",""),("ic",""),("ist",""),("ism",""),
         ("er",""),("or",""),("ly","")]
SUFFIXES = ["ingly","edly","ings","ing","edly","ed","ies","es","s","er","ers",
            "ly","ment","ments","tion","tions","ness"]

def stems(t: str) -> set[str]:
    """ALL plausible stems (each applicable suffix stripped, with e-restoration
    variants) — 1c's first-match single stem produced artifacts
    (customiz/customize, crea/creat, clo/clos)."""
    out = {t}
    for sfx in SUFFIXES:
        if t.endswith(sfx) and len(t) - len(sfx) >= 3:
            base = t[: len(t) - len(sfx)]
            out.add(base); out.add(base + "e")
            if len(base) >= 4 and base[-1] == base[-2]:
                out.add(base[:-1])          # stopped -> stop
    for sfx, rep in DERIV:
        if t.endswith(sfx) and len(t) - len(sfx) >= 3:
            base = t[: len(t) - len(sfx)]
            out.add(base); out.add(base + rep)
            out.add(base + "e")
    return out

WORD = re.compile(r"[a-z0-9]+")          # F1: apostrophes/punct gone
def toks(s): return WORD.findall(s.lower())

ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
IDENTIFIER = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z0-9]+$")   # s21, 10k, v6
CAPRUN = re.compile(r"\b[A-Z][a-zA-Z0-9]+")

def specifics_tokens(obj_raw: str) -> list[str]:
    """Numeric, alphanumeric-identifier, and proper-noun-run tokens (dev's
    specifics-only class), lowercased; drops sentence-leading capitals only if
    they are common words (heuristic: keep cap-runs longer than 1 word OR
    mid-string capitals OR containing digits)."""
    out = []
    for t in toks(obj_raw):
        if t.isdigit() or IDENTIFIER.match(t):
            out.append(t)
    # capitalized runs from the RAW string, skipping position 0 lead-cap noise
    for m in CAPRUN.finditer(obj_raw):
        if m.start() == 0 and " " not in obj_raw[: m.end()]:
            continue
        out.extend(toks(m.group(0)))
    return list(dict.fromkeys(out))

def date_ok(tok_triplet, session_day: str, window_days=366) -> bool:
    try:
        d = datetime.date(*map(int, tok_triplet))
        s = datetime.date(*map(int, session_day.split("-")))
        return abs((d - s).days) <= window_days
    except ValueError:
        return False

# -- join (same as 1b) --
identities = {}
for f in glob.glob(str(DS / "runs" / "manifest_run_*.json")):
    ei = json.load(open(f)).get("extraction_identity")
    if ei: identities[json.dumps(ei, sort_keys=True)] = 1
ID_HASH = _sha(next(iter(identities)))
cache = {}
for cf in [DS/"cache"/"extractions.jsonl",
           *sorted(glob.glob(str(DS/"variance"/"r*"/"extractions.jsonl")))]:
    for line in open(cf):
        try:
            r = json.loads(line); cache[r["key"]] = r["value"]
        except Exception: pass
items, _e, _m = adapter.load(strict=False)
WINDOW = RL.CONTEXT_POLICY["window_turns"]

# pass 1: per-relation median object length -> idiom classification
rel_lens = collections.defaultdict(list)
triples_by_key = {}
hits = set()
for item in items:
    for session in item.sessions:
        for i, turn in enumerate(session.turns):
            text = RL.serialize(session, i, window=WINDOW)
            seen = set(); val = None
            for arm in ["A","B","C","D"]:
                author,_d,etype = RL.author_for(turn.role, arm)
                kw = (author.value, etype, session.iso_day)
                if kw in seen: continue
                seen.add(kw)
                k = _sha(ID_HASH, text, *kw)
                if k in cache and k not in hits:
                    hits.add(k); val = (k, cache[k], text, session.iso_day); break
            if val is None: continue
            k, raw, text, day = val
            try:
                data = json.loads(raw)
                if isinstance(data, list): data = {"triples": data}
            except ValueError: continue
            ts = [t for t in (data.get("triples") or [])
                  if isinstance(t, dict) and t.get("subject")
                  and t.get("relation") and t.get("object")]
            triples_by_key[k] = (text, day, ts)
            for t in ts:
                rel_lens[str(t["relation"]).strip()].append(
                    len(toks(str(t["object"]))))

def median(xs): xs = sorted(xs); return xs[len(xs)//2]
IDIOM = {r for r, ls in rel_lens.items() if len(ls) >= 20 and median(ls) >= 5}
print(f"relations: {len(rel_lens)}; idiom-class (median len >= 5, n >= 20): "
      f"{len(IDIOM)}")
print("top idiom relations:",
      sorted(IDIOM, key=lambda r: -len(rel_lens[r]))[:8])

# pass 2: the fixed predicate
objects = flags = 0
flags_by_mode = collections.Counter()
objs_by_mode = collections.Counter()
samples = []
for k, (text, day, ts) in triples_by_key.items():
    t_toks = toks(text)
    t_stems = set()
    for x in t_toks:
        t_stems |= stems(x)
    t_capruns = {tuple(toks(m.group(0))) for m in
                 __import__("re").finditer(r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+", text)}
    t_initialisms = {"".join(w[0] for w in run) for run in t_capruns}
    for t in ts:
        rel = str(t["relation"]).strip()
        obj = str(t["object"]).strip()
        if obj.lower() in ("true","false","yes","no"): continue
        if rel in FORMULA_RELS: continue   # notation, not testimony
        mode = "specifics"
        if mode == "full":
            cand = [x for x in toks(obj)
                    if x not in STOP and (any(c.isdigit() for c in x) or len(x) >= 5)]
        else:
            cand = specifics_tokens(obj)
        # F3: pull ISO dates out for date-validation
        date_matches = ISO_DATE.findall(obj)
        date_parts = {p for trip in date_matches for p in trip} | \
                     {f"{t2}" for trip in date_matches for t2 in trip}
        bad_dates = [f"{y}-{mo}-{d}" for (y, mo, d) in date_matches
                     if not date_ok((y, mo, d), day)]
        cand = [x for x in cand if x not in date_parts]
        if not cand and not date_matches: continue
        objects += 1; objs_by_mode[mode] += 1
        obj_capruns = [tuple(toks(m.group(0))) for m in
                       __import__("re").finditer(r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+", obj)]
        obj_initialism_words = set()
        for run in obj_capruns:
            initials = "".join(w[0] for w in run)
            if initials in t_stems:
                obj_initialism_words.update(run)
        def grounded(x):
            if x in obj_initialism_words: return True        # expansion of a text acronym
            if x in t_stems: return True
            if stems(x) & t_stems: return True
            if x in TEMPLATE: return True
            if NUMWORDS.get(x) in t_stems: return True       # "first" vs 1
            if x in NUMWORDS.values() and any(w for w,d in NUMWORDS.items()
                                              if d == x and w in t_stems): return True
            if x in t_initialisms: return True               # WHO / UN / SDG
            # compound splitting: object token contained inside a longer text
            # token or spanning two adjacent text tokens ("sql","server" vs
            # "sqlserver"; "sqlserver" vs "sql server")
            if len(x) >= 4 and any(x in tt for tt in t_toks if len(tt) > len(x)):
                return True
            if len(x) >= 6 and any(x == t_toks[i] + t_toks[i+1]
                                   for i in range(len(t_toks) - 1)): return True
            # reverse initialism: x is a word of an object cap-run whose
            # INITIALS appear as a text token (World Health Organization ~ WHO)
            return False
        missing = [x for x in cand if not grounded(x)]
        if missing or bad_dates:
            flags += 1; flags_by_mode[mode] += 1
            if len(samples) < 400:
                samples.append({"mode": mode, "relation": rel, "object": obj,
                                "missing": missing, "bad_dates": bad_dates,
                                "evt_tail": text[-350:]})

print(f"\nobjects with checkable anchors: {objects} "
      f"(full: {objs_by_mode['full']}, specifics: {objs_by_mode['specifics']})")
print(f"FLAGS: {flags} ({100*flags/max(objects,1):.2f}%)")
for m in ("full","specifics"):
    print(f"  {m}: {flags_by_mode[m]}/{objs_by_mode[m]} "
          f"({100*flags_by_mode[m]/max(objs_by_mode[m],1):.2f}%)")
random.seed(11); random.shuffle(samples)
json.dump(samples[:200], open(OUT/"phase1f_flag_samples.json","w"), indent=1)
print(f"samples -> phase1f_flag_samples.json ({min(len(samples),150)})")
