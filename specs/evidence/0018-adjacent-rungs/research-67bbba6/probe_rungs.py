"""0018 option B (adjacent rungs), by execution: from every base 1..HEAD-1, walk the store ONE schema version at a time
and ask at every rung whether the result is a shape that version accepts (`sv.digest(manifest, t) in
sv.accepted_digests(t)`), and whether the rung's own postconditions hold. For contrast, migrate the same base DIRECTLY
to head (today's `_apply_forward`) and ask the same.

The rung is today's kernel with its head moved: `migration.SCHEMA_VERSION` is set to t and `_apply_forward(conn, t-1)`
runs, so the additive diff targets SCHEMAS[t], every data/ALTER block guarded `base < k <= SCHEMA_VERSION` fires only
for k == t, and the stamp is t. The patch lives in this process only. Stores are built by `sv.create(conn, b)` (the
registry's constructor set, plus the identity singleton where it applies) and stamped b: EMPTY stores, so this measures
SHAPE acceptance and the postconditions on empty data, not data steps over populated rows.
Usage (an export's root on sys.path via PYTHONPATH=src): python probe_rungs.py <scratch dir>. Prints one line per
(base, rung) and a summary."""
import sqlite3
import sys
import pathlib

from veracium.store import migration as M
from veracium.store import schema_version as sv

scratch = pathlib.Path(sys.argv[1])
HEAD = sv.SCHEMA_VERSION


def build(path, b):
    c = sqlite3.connect(path, isolation_level=None)   # explicit BEGIN/COMMIT only
    c.execute("BEGIN")
    sv.create(c, b)
    c.execute(f"PRAGMA user_version = {b}")
    c.commit()
    return c


def step(c, frm, to):
    """One kernel application inside one transaction; returns (ok, accepted, note)."""
    saved = M.SCHEMA_VERSION
    M.SCHEMA_VERSION = to
    try:
        c.execute("BEGIN IMMEDIATE")
        try:
            M._apply_forward(c, frm)
        except Exception as exc:  # noqa: BLE001 - recorded, the probe's output
            c.execute("ROLLBACK")
            return False, None, f"{type(exc).__name__}: {str(exc)[:160]}"
        objs = sv.manifest(c)
        accepted = sv.digest(objs, to) in sv.accepted_digests(to)
        c.execute("COMMIT")
        return True, accepted, ""
    finally:
        M.SCHEMA_VERSION = saved


bad = []
for b in range(1, HEAD):
    c = build(scratch / f"rungs-from-{b}.db", b)
    for t in range(b + 1, HEAD + 1):
        ok, acc, note = step(c, t - 1, t)
        mark = "ok" if ok and acc else ("NOT-ACCEPTED" if ok else "REFUSED")
        print(f"base {b:2d} rung v{t-1:2d}->v{t:2d}: {mark} {note}")
        if mark != "ok":
            bad.append((b, t, mark, note))
            break
    c.close()
    d = build(scratch / f"direct-from-{b}.db", b)
    ok, acc, note = step(d, b, HEAD)
    print(f"base {b:2d} DIRECT v{b:2d}->v{HEAD}: {'ok' if ok and acc else ('NOT-ACCEPTED' if ok else 'REFUSED')} {note}")
    d.close()
print(f"SUMMARY head v{HEAD}: {len(bad)} base(s) whose rung walk stopped: {bad}")
# CONTROLS: the acceptance predicate can say no. (1) a store one rung short, judged as the next version; (2) a fully
# walked store with one foreign table added, judged at head; (3) a walked store with a column added to `edges`.
c = build(scratch / "control-short.db", HEAD - 1)
print("CONTROL v%d store judged as v%d accepted: %s (expect False)"
      % (HEAD - 1, HEAD, sv.digest(sv.manifest(c), HEAD) in sv.accepted_digests(HEAD)))
c.close()
c = build(scratch / "control-extra.db", 1)
for t_ in range(2, HEAD + 1):
    assert step(c, t_ - 1, t_)[:2] == (True, True)
print("CONTROL walked v1->v%d store accepted before tampering: %s (expect True)"
      % (HEAD, sv.digest(sv.manifest(c), HEAD) in sv.accepted_digests(HEAD)))
c.execute("CREATE TABLE probe_foreign(x)")
print("CONTROL the same store + a foreign table accepted: %s (expect False)"
      % (sv.digest(sv.manifest(c), HEAD) in sv.accepted_digests(HEAD)))
c.execute("DROP TABLE probe_foreign")
c.execute("ALTER TABLE edges ADD COLUMN probe_x TEXT")   # a changed TABLE (indexes are rebuildable: 0007 repairs them)
print("CONTROL the same store with a column added to edges accepted: %s (expect False)"
      % (sv.digest(sv.manifest(c), HEAD) in sv.accepted_digests(HEAD)))
c.close()
