"""T1's proof: every fixture migrated by two bodies, compared on the full statement trace, SELECTs included, the end state, the
schema, the verdict, and the clock reads. argv: <python> <src> <left body or -> <right body or -> <work>. Exit 1 on any difference."""
import io, json, lzma, os, shutil, subprocess, sys, tarfile
from pathlib import Path
PY, SRC, L, Rt, W = sys.argv[1:6]; H = Path(__file__).resolve().parent; W = Path(W); W.mkdir()
t = tarfile.open(fileobj=io.BytesIO(lzma.decompress((H / "fixtures.tar.xz").read_bytes()))); t.extractall(W, filter="data")
def arm(db, body):
    e = dict(os.environ, PYTHONPATH=SRC, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([PY, "-P", "-s", str(H / "t1_arm.py"), str(db)] + ([] if body == "-" else [str(Path(body).resolve())]), env=e, capture_output=True, text=True, timeout=180, cwd="/tmp")
    if p.returncode: return {"crashed": p.stderr[-300:]}
    return json.loads(p.stdout.strip().splitlines()[-1])
bad, total = [], 0
for f in sorted(W.glob("*.db")):
    a, b = f.with_suffix(".a"), f.with_suffix(".b"); shutil.copyfile(f, a); shutil.copyfile(f, b)
    x, y = arm(a, L), arm(b, Rt); total += 1
    keys = [k for k in sorted(set(x) | set(y)) if x.get(k) != y.get(k)]
    if keys:
        i = next((i for i, (p, q) in enumerate(zip(x.get("trace", []), y.get("trace", []))) if p != q), None)
        bad.append({"fixture": f.name, "differs": keys, "first": i, "left": (x.get("trace") or [None] * (i or 1))[i or 0] if i is not None else None, "right": (y.get("trace") or [None] * (i or 1))[i or 0] if i is not None else None, "crash": x.get("crashed") or y.get("crashed")})
    a.unlink(); b.unlink()
print(json.dumps({"fixtures": total, "differing": len(bad), "first": bad[:3]}, indent=1)[:1800])
sys.exit(1 if bad or not total else 0)
