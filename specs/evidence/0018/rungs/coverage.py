"""Run the head migration on every fixture with each statement logged; print which writes changed a row. argv: <python> <head src> <this directory> <work>."""
import json, os, shutil, subprocess, sys, collections, ast, pathlib
PY, HEAD, T, W = sys.argv[1:5]; r = json.load(open(f"{W}/result.json"))
agg = {}; who = collections.defaultdict(set)
for s in r["states"]:
    q = s["db"] + ".cov"; shutil.copyfile(s["db"], q)
    e = dict(os.environ, PYTHONPATH=HEAD, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([PY, "-P", "-s", f"{T}/cov.py", q], env=e, capture_output=True, text=True, timeout=180, cwd="/tmp")
    if p.returncode: print("FAILED", s["route"], p.stderr[-200:]); continue
    for k, (sql, n, ch) in json.loads(p.stdout.strip().splitlines()[-1]).items():
        a = agg.setdefault(k, [sql, 0, 0]); a[1] += n; a[2] += ch
        if ch > 0: who[k].add(s["origin"])
W = ("UPDATE", "INSERT", "DELETE", "REPLACE")
wr = {k: v for k, v in agg.items() if v[0].upper().startswith(W)}
print("write statements run:", len(wr), "| changed a row:", sum(1 for v in wr.values() if v[2] > 0))
for k, v in sorted(wr.items(), key=lambda kv: (kv[0].split(":")[0], int(kv[0].split(":")[1]))):
    print(("  SAW " if v[2] else "  ZERO"), k, f"runs={v[1]} rows={v[2]}", v[0][:70])
