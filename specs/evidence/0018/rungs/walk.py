"""Research's walk (probes/bfs.py) from POPULATED stores: each row's newest release writes through its own API, every later
release's own migrate_store carries the store, and each state reached then goes to head by the direct route. Reports shapes
reached, route failures, and per origin whether every route's head content agrees. argv: <work> <head src> <python>."""
import itertools, json, os, shutil, subprocess, sys
W, HEAD, PY = sys.argv[1:4]; T = os.path.dirname(os.path.abspath(__file__))
rows = [("v0.4.8",1),("v0.5.0",3),("v0.6.0",4),("v0.9.0",6),("v0.10.0",7),("v0.12.0",8),("v0.13.0",9),("v0.15.0",10),("v0.17.0",11),("v0.19.0",12),("v0.25.0",13),("v0.26.1",14)]
def run(script, args, src):
    e = dict(os.environ, PYTHONPATH=src, PYTHONDONTWRITEBYTECODE="1"); e.pop("PYTHONSAFEPATH", None)
    return subprocess.run([PY, "-P", "-s", f"{T}/{script}"] + args, env=e, capture_output=True, text=True, timeout=180, cwd="/tmp")
last = lambda s: s.strip().splitlines()[-1] if s.strip() else ""
acc = json.loads(last(run("acc.py", [], HEAD).stdout))
def digest(p, v):
    r = run("dig.py", [p, str(v)], HEAD)
    return json.loads(last(r.stdout)) if r.returncode == 0 else {"err": last(r.stderr)[:160]}
os.makedirs(f"{W}/st", exist_ok=True); n = itertools.count(); seen = {}; fails = {}; work = []; pop = {}
for i, (t, v) in enumerate(rows):
    tree = f"{W}/{t}/src"; db = f"{W}/{t}/p.db"
    if os.path.exists(db): os.remove(db)
    r = run("populate_release.py", [db], tree)
    pop[t] = last(r.stdout)[:400] if r.returncode == 0 else "POPULATE FAILED " + last(r.stderr)[:160]
    d = digest(db, v); key = (t, v, d.get("digest"))      # the origin is in the key: a shape another origin reached still walks
    if key not in seen:
        q = f"{W}/st/{next(n)}.db"; shutil.copyfile(db, q); seen[key] = {"route": t, "origin": t, "db": q}; work.append((i, q, d.get("digest"), t, t))
while work:
    i, p, dg, route, origin = work.pop()
    for j in range(i + 1, len(rows)):
        t, v = rows[j]; q = f"{W}/st/{next(n)}.db"; shutil.copyfile(p, q)
        r = run("mig.py", [q], f"{W}/{t}/src")
        if r.returncode != 0:
            fails.setdefault((rows[i][0], t), last(r.stderr)[:140]); os.remove(q); continue
        d = digest(q, v)
        if d.get("uv") != v: fails.setdefault((rows[i][0], t), f"uv {d}"); os.remove(q); continue
        key = (origin, v, d["digest"])
        if key in seen: os.remove(q); continue
        seen[key] = {"route": route + ">" + t, "origin": origin, "db": q}; work.append((j, q, d["digest"], route + ">" + t, origin))
res = {"populate": pop, "states": [], "fails": {f"{a}>{b}": e for (a, b), e in fails.items()}}
for (_o, v, dg), s in sorted(seen.items(), key=lambda kv: (kv[0][1], kv[0][0], str(kv[0][2]))):
    base = json.loads(last(run("content.py", [s["db"]], HEAD).stdout))
    h = s["db"] + ".head"; shutil.copyfile(s["db"], h)
    r = run("head.py", [h], HEAD); hd = last(r.stdout)
    res["states"].append({"v": v, "digest": dg, "accepted": dg in acc[str(v)], "route": s["route"], "origin": s["origin"], "db": s["db"],
                          "rows": {k: x["n"] for k, x in base.items() if x["n"]},
                          "head": hd[:300] if r.returncode == 0 else "HEAD FAILED " + last(r.stderr)[:200],
                          "headcontent": {k: x["d"] for k, x in json.loads(last(run("content.py", [h], HEAD).stdout)).items()} if r.returncode == 0 else None})
res["accepted_at_bases"] = {str(v): len(acc[str(v)]) for _, v in rows}
json.dump(res, open(f"{W}/result.json", "w"), indent=1, default=str)
shapes = {(s["v"], s["digest"]) for s in res["states"] if s["accepted"]}; print("reached accepted", len(shapes), "of", sum(res["accepted_at_bases"].values()), "states", len(res["states"]), "all accepted", all(s["accepted"] for s in res["states"]), "route failures", len(fails))
