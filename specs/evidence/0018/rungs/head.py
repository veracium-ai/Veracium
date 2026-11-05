"""Under the branch's own source: migrate one populated store to head by the direct route; report outcome, stamp, rows."""
import json, sqlite3, sys
from veracium.store.migration import migrate_store
from veracium.store import schema_version as sv
db = sys.argv[1]
r = migrate_store(db)
c = sqlite3.connect(db); v = c.execute("PRAGMA user_version").fetchone()[0]
o = sv.manifest(c); d = sv.digest(o, v)
print(json.dumps({"outcome": getattr(r, "outcome", str(r)), "to": v, "accepted": d in sv.accepted_digests(v),
                  "rows": {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("edges", "episodes")}}))
