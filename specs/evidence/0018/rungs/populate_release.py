"""Run under one release's own source. Writes through that release's own store API whatever routes it has, each attempt
reported; then counts the rows the kernel's data steps read. argv: <db>."""
import datetime as dt, enum, inspect, json, sqlite3, sys, typing, uuid
db = sys.argv[1]
import veracium
from veracium.store.sqlite import SqliteStore
from veracium import schema as S
s = SqliteStore(db)
now = dt.datetime(2024, 1, 2, 3, 4, 5, tzinfo=dt.timezone.utc)
F = lambda m: m.model_fields
def fill(ann):
    a = typing.get_args(ann)[0] if typing.get_args(ann) else ann
    if inspect.isclass(a) and issubclass(a, enum.Enum): return list(a)[0]
    return now if a is dt.datetime else "fixture" if a is str else 0.5 if a is float else 1 if a is int else None
pc = F(S.Edge)["provenance"].annotation
prov = lambda: pc(**{k: fill(f.annotation) for k, f in F(pc).items() if f.is_required()})
def edge(i, **kw):
    e = {"id": i, "user_id": "u1", "subject": "user", "relation": "prefers", "object": "tea" + i, "provenance": prov(), **kw}
    for k, f in F(S.Edge).items():
        if f.is_required() and k not in e: e[k] = fill(f.annotation)
    return S.Edge(**e)
def episode(i, **kw):
    p = {"id": i, "user_id": "u1", **kw}
    if "provenance" in F(S.Episode): p["provenance"] = prov()
    for k, f in F(S.Episode).items():
        if f.is_required() and k not in p: p[k] = fill(f.annotation)
    return S.Episode(**p)
log = {}
def attempt(name, fn):
    try: fn(); log[name] = "ok"
    except Exception as ex: log[name] = f"{type(ex).__name__}: {str(ex)[:90]}"
attempt("edge", lambda: s.add_edge(edge("e1")))
attempt("edge+invalidate", lambda: (s.add_edge(edge("e2")), s.invalidate_edge("e2", now, "lapsed")))
attempt("episode", lambda: s.add_episode(episode("p1")))
attempt("outcome-episode", lambda: s.add_episode(episode("p2", kind="outcome", outcome=list(S.Outcome)[0], edge_id="e1") if "edge_id" in F(S.Episode) else episode("p2", kind="outcome")))
attempt("wiki", lambda: s.set_wiki("u1", "fixture wiki", s.store_version("u1")))
if hasattr(s, "confirm_edge"):
    sig = inspect.signature(s.confirm_edge).parameters
    kw = {"actor": "user", "call_path": list(S.ConfirmationCallPath)[0].value, "correlation_id": str(uuid.UUID(int=7)), "request_digest": "0" * 64, "at": now, "now": now, "confirmed_at": now, "origin": "local"}
    attempt("confirm", lambda: s.confirm_edge("u1", "e1", **{k: v for k, v in kw.items() if k in sig}))
attempt("edge+superseded", lambda: (s.add_edge(edge("e3")), s.invalidate_edge("e3", now, "superseded")))
if hasattr(s, "apply_supersession_plan"):
    def refuse():
        from veracium.authority import scope_fingerprint
        s.add_edge(edge("e4", subject="user", relation="prefers", object="coffee"))
        inc = edge("e5", subject="user", relation="prefers", object="cocoa")
        scope = s.edges("u1", subject="user", relation="prefers", active_only=True, include_quarantined=True)
        d = S.SupersessionRefusalDraft(prior_edge_id="e4", incoming_edge_id="e5", relation="prefers", prior_effective=2, incoming_effective=1)
        s.apply_supersession_plan(S.SupersessionPlan(incoming_edge=inc, insert_incoming=False, operation_id="op-refuse",
                                                     expected_state=scope_fingerprint(scope), refusals=[d]))
    attempt("refusal", refuse)
try: s.close()
except Exception: pass
c = sqlite3.connect(db)
tabs = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
rows = {t: c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("edges", "episodes", "wiki", "confirmations", "supersession_refusals", "supersession_operations", "contribution_ledger", "redactions") if t in tabs}
rows["inactive"] = c.execute("SELECT COUNT(*) FROM edges WHERE active=0").fetchone()[0]
rows["outcome_eps"] = sum(1 for (j,) in c.execute("SELECT json FROM episodes") if json.loads(j).get("kind") == "outcome")
print(json.dumps({"user_version": c.execute("PRAGMA user_version").fetchone()[0], "log": log, "rows": rows}))
