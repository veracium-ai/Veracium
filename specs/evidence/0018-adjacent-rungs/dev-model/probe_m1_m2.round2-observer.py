"""M1/M2 at the pin: a store swapped between the mint and the delegated transaction.
Run from the pin's tree/ with PYTHONPATH=src and a new work dir. Process-local wrapper on
migration.migrate_store only (the swap point); no product file is edited."""
import json, os, pathlib, sqlite3, sys
from veracium.store import migration as m
from veracium.store import release_migration as rm
from veracium.store import schema_version as sv
ROOT = pathlib.Path(sys.argv[1]).resolve(); ROOT.mkdir(parents=True, exist_ok=False)
ATT = rm.MigrationAttestation(quiesced=True, backup_ref="dev-m12")
H = sv.SCHEMA_VERSION
def make(path, v, stamped=True):
    c = sqlite3.connect(path, isolation_level=None); c.execute("BEGIN"); sv.create(c, v)
    if stamped: c.execute(f"PRAGMA user_version={v}")
    c.execute("COMMIT"); c.close()
def stamp(path):
    c = sqlite3.connect(path); v = c.execute("PRAGMA user_version").fetchone()[0]
    n = c.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]; c.close(); return v, n
def run(case, swap):
    p = str(ROOT / f"{case}.db"); make(p, H - 1)
    orig = m.migrate_store; seen = {}
    def wrapped(path, **kw):
        swap(path); seen["swapped_to"] = stamp(path); return orig(path, **kw)
    m.migrate_store = wrapped
    try:
        try:
            r = rm.run_release_migration(p, host_attestation=ATT); res = {"result": list(r)}
        except Exception as e:
            res = {"escape": type(e).__name__, "msg": str(e)[:300]}
    finally:
        m.migrate_store = orig
    audit = json.load(open(rm.audit_trail_path(p))) if os.path.exists(rm.audit_trail_path(p)) else {}
    (op, entry), = audit.items() if len(audit) == 1 else ((None, audit),)
    att = entry.get("attempted", {}) if op else {}
    print(json.dumps({"case": case, **seen, **res, "after": stamp(p),
        "attempted": {k: att.get(k) for k in ("from_version", "to_version")} if att else None,
        "terminal": entry.get("terminal") if op else None,
        "readback": rm.read_terminal(op, audit_path=rm.audit_trail_path(p)).kind if op else None},
        sort_keys=True, default=str))
def to_v13(path):
    s = path + ".swap"; make(s, 13); os.replace(s, path)
def to_empty(path):
    s = path + ".swap"; sqlite3.connect(s).close(); os.replace(s, path)
def control(path):
    pass
print(json.dumps({"runtime": sv.runtime_status().status, "head": H, "mint_base": rm._MINT_BASE}))
run("control-no-swap", control)
run("M1-swap-to-v13", to_v13)
run("M2-swap-to-empty", to_empty)
def to_absent(path):
    os.remove(path)
run("M3-swap-to-absent", to_absent)
