"""One arm of T1's differential: migrate one store and report everything observable. argv: <db> [<body>]. With <body>, that file
stands in for veracium.store.migration, so the frozen copy and the live module run the same way. Clock and uuids are fixed."""
import datetime as dt, hashlib, importlib.util, itertools, json, sqlite3, sys, uuid
db = sys.argv[1]
if len(sys.argv) > 2:
    spec = importlib.util.spec_from_file_location("veracium.store.migration", sys.argv[2])
    mod = importlib.util.module_from_spec(spec); sys.modules["veracium.store.migration"] = mod
    import veracium.store
    veracium.store.migration = mod; spec.loader.exec_module(mod)
import veracium.store.migration as M
trace, clocks = [], []
real = sqlite3.connect
def connect(*a, **k):
    c = real(*a, **k); c.set_trace_callback(lambda s: trace.append(" ".join(s.split()))); return c
sqlite3.connect = connect
n = itertools.count(1)
uuid.uuid4 = lambda: uuid.UUID(int=next(n), version=4)
FIXED = dt.datetime(2026, 1, 2, 3, 4, 5, tzinfo=dt.timezone.utc)
def clock():
    clocks.append(1); return FIXED
M._clock = clock
class Fixed(dt.datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED
for name, m in list(sys.modules.items()):           # schema_version reads the wall clock directly, outside `_clock`
    if name.startswith("veracium.") and getattr(m, "datetime", None) is dt.datetime:
        m.datetime = Fixed
outcome = {}
try:
    r = M.migrate_store(db)
    outcome = {k: str(v) for k, v in sorted(vars(r).items())} if hasattr(r, "__dict__") else {"r": str(r)}
except BaseException as e:
    outcome = {"raised": type(e).__name__, "message": str(e)[:400], "vars": {k: str(v)[:200] for k, v in sorted(vars(e).items())}}
c = real(db); state = {}
for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall():
    state[t] = hashlib.sha256("\n".join(sorted(json.dumps(list(r), default=str) for r in c.execute(f'SELECT * FROM "{t}"'))).encode()).hexdigest()
schema = hashlib.sha256("\n".join(sorted(str(r) for r in c.execute("SELECT type, name, sql FROM sqlite_master"))).encode()).hexdigest()
print(json.dumps({"trace": trace, "clocks": len(clocks), "outcome": outcome, "state": state, "schema": schema, "version": c.execute("PRAGMA user_version").fetchone()[0]}))
