"""Run the head migration with every migration-module statement logged by line, with the rows it changed. argv: <db>."""
import json, os, sqlite3, sys
real = sqlite3.connect; log = {}
class C(sqlite3.Connection):
    def execute(self, sql, *a):
        f = sys._getframe(1); cur = super().execute(sql, *a)
        if os.path.basename(f.f_code.co_filename) in ("migration.py", "data_migration.py", "schema_version.py"):
            k = f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno}"; e = log.setdefault(k, [" ".join(str(sql).split())[:90], 0, 0])
            e[1] += 1; e[2] += max(cur.rowcount, 0)
        return cur
def connect(*a, **k):
    k.setdefault("factory", C); return real(*a, **k)
sqlite3.connect = connect
from veracium.store.migration import migrate_store
migrate_store(sys.argv[1])
print(json.dumps(log))
