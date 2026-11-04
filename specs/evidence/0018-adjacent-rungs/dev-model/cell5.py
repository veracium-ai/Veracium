import json, pathlib, sqlite3, sys, inspect
from veracium.store import schema_version as sv
from veracium.store import migration as m
ROOT = pathlib.Path(sys.argv[1]).resolve(); ROOT.mkdir(parents=True, exist_ok=False)
print(json.dumps({"open_versioned_sig": str(inspect.signature(sv.open_versioned))}))
for case, stamped in (("unstamped-v1", False), ("stamped-v1", True)):
    p = str(ROOT / f"{case}.db")
    c = sqlite3.connect(p, isolation_level=None); c.execute("BEGIN"); sv.create(c, 1)
    if stamped: c.execute("PRAGMA user_version=1")
    c.execute("COMMIT"); c.close()
    calls = []
    def older(c, spath, found, objs, base, *, runtime):
        calls.append({"found": found, "base": base})
        raise RuntimeError("cell5: hook reached; refusing so nothing is written")
    conn = sqlite3.connect(p)
    try:
        r = sv.open_versioned(conn, p, older=older); out = {"result": str(r)}
    except Exception as e:
        out = {"escape": type(e).__name__, "reason": getattr(e, "reason", None), "msg": str(e)[:200]}
    conn.close()
    c = sqlite3.connect(p); st = c.execute("PRAGMA user_version").fetchone()[0]; c.close()
    print(json.dumps({"case": case, "hook_calls": calls, **out, "stamp_after": st}))
