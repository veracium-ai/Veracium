"""U3B — the 0019 round-4 obligation: re-measure the SHIPPED predicate
(veracium.grounding.ungrounded @ 19765e1) over the same 93,342-object corpus
(the cache-reconstruction join), with a fresh flag-sample for classification.
The acceptance-pinned numbers are these."""
import json, re, sys, glob, random, hashlib
from pathlib import Path
HARNESS = Path("/home/ubuntu/Dev/veracium/tests/longmemeval")
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, "/home/ubuntu/Dev/veracium/src")
import adapter, run_longmemeval as RL          # noqa: E402
from cache import _sha                          # noqa: E402
from veracium.grounding import ungrounded       # THE SHIPPED PREDICATE

DS = Path.home() / "Datasets" / "longmemeval"
identities = {}
for f in glob.glob(str(DS / "runs" / "manifest_run_*.json")):
    ei = json.load(open(f)).get("extraction_identity")
    if ei: identities[json.dumps(ei, sort_keys=True)] = 1
ID_HASH = _sha(next(iter(identities)))
cache = {}; cache_sha = hashlib.sha256()
for cf in sorted([str(DS/"cache"/"extractions.jsonl"),
                  *glob.glob(str(DS/"variance"/"r*"/"extractions.jsonl"))]):
    data = open(cf, "rb").read(); cache_sha.update(data)
    for line in data.decode().splitlines():
        try:
            r = json.loads(line); cache[r["key"]] = r["value"]
        except Exception: pass
items, _e, _m = adapter.load(strict=False)
WINDOW = RL.CONTEXT_POLICY["window_turns"]
objects = flags = 0
hits = set(); samples = []
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
                    hits.add(k); val = cache[k]; break
            if val is None: continue
            try:
                data = json.loads(val)
                if isinstance(data, list): data = {"triples": data}
            except ValueError: continue
            for t in (data.get("triples") or []) if isinstance(data, dict) else []:
                if not (isinstance(t, dict) and t.get("subject")
                        and t.get("relation") and t.get("object")): continue
                obj = str(t["object"]).strip()
                if obj.lower() in ("true","false","yes","no"): continue
                objects += 1
                if ungrounded(obj, text, session.iso_day):
                    flags += 1
                    if len(samples) < 400:
                        samples.append({"object": obj, "relation": t.get("relation"),
                                        "evt_tail": text[-300:]})
print(f"objects: {objects}")
print(f"FLAGS (shipped predicate): {flags} ({100*flags/max(objects,1):.2f}%)")
random.seed(20260815); random.shuffle(samples)
json.dump(samples[:30], open("u3b_flag_sample.json","w"), indent=1)
json.dump({"objects": objects, "flags": flags,
           "flag_rate": round(flags/max(objects,1), 5),
           "corpus_sha256": cache_sha.hexdigest(),
           "code_identity": "src/veracium/grounding.py @ 19765e1"},
          open("u3b_measurement.json","w"), indent=1)
print("sample -> u3b_flag_sample.json; record -> u3b_measurement.json")
