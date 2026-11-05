import sys,sqlite3,json
import veracium.store.schema_version as sv
db=sys.argv[1]; c=sqlite3.connect(db); v=c.execute("PRAGMA user_version").fetchone()[0]; o=sv.manifest(c)
base=int(sys.argv[2]); print(json.dumps({"uv":v,"digest":sv.digest(o,base),"accepted":sv.digest(o,base) in sv.accepted_digests(base)}))
