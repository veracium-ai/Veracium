"""Write fixtures.tar.xz and manifest.json from a walk's result and a coverage run. The tar is deterministic: names sorted,
mtime 0, owner 0. argv: <work> <coverage output> <out dir>."""
import hashlib, io, json, lzma, sqlite3, sys, tarfile
from pathlib import Path
W, COV, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
r = json.loads((W / "result.json").read_text())
entries, blobs = [], {}
for s in r["states"]:
    name = f"v{s['v']:02d}-{s['digest'][:12]}.db"
    b = Path(s["db"]).read_bytes(); blobs[name] = b
    entries.append({"fixture": name, "base": s["v"], "digest": s["digest"], "accepted": s["accepted"], "origin": s["origin"], "route": s["route"],
                    "rows": s["rows"], "sha256": hashlib.sha256(b).hexdigest(), "head": json.loads(s["head"])})
cov = []
for line in COV.read_text().splitlines():
    p = line.split(None, 4)
    if p and p[0] in ("SAW", "ZERO"):
        cov.append({"seen": p[0] == "SAW", "runs": p[2], "rows": p[3], "statement": p[4]})
manifest = {"generator": {"python": sys.version.split()[0], "sqlite": sqlite3.sqlite_version},
            "fixtures": sorted(entries, key=lambda e: e["fixture"]), "coverage": cov,
            "not_seen": {"UPDATE redactions": "no released base holds `redactions`, so no release-authored fixture can carry a row: "
                         "v16-notice-state and the redactions ALTERs stay on PA1's synthetic row, a limit of release-authored"}}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w") as t:
    for n in sorted(blobs):
        i = tarfile.TarInfo(n); i.size = len(blobs[n]); i.mtime = 0; i.uid = i.gid = 0; i.uname = i.gname = ""
        t.addfile(i, io.BytesIO(blobs[n]))
(OUT / "fixtures.tar.xz").write_bytes(lzma.compress(buf.getvalue(), preset=9))
print(len(entries), "fixtures,", sum(e["accepted"] for e in entries), "accepted,", sum(c["seen"] for c in cov), "of", len(cov), "write statements saw a row")
