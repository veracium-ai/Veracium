"""One store's rows, table by table, every column, as a digest per table and a count. argv: <db>."""
import hashlib, json, sqlite3, sys
c = sqlite3.connect(sys.argv[1])
out = {}
for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
    cols = [r[1] for r in c.execute(f'PRAGMA table_info("{t}")')]
    rows = sorted(json.dumps(list(r), default=str) for r in c.execute(f'SELECT * FROM "{t}"'))
    out[t] = {"n": len(rows), "d": hashlib.sha256("\n".join(rows).encode()).hexdigest()[:16], "cols": cols}
print(json.dumps(out))
