"""0018 adjacent-rungs v0.3, R1-02: does every historical table/index constructor meet
the shape 0013 §5f.1 (b1) asserts of the head constructors? Run from a git-archive
export of the pin with PYTHONPATH=src. Prints counts and the (version, kind, name)
pairs whose constructor differs from head's."""
import re
from veracium.store import schema_version as sv

H = sv.SCHEMA_VERSION
bad, n = [], 0
for v in range(1, H + 1):
    for o in sv.SCHEMAS[v]:
        if o.kind not in ("table", "index"):
            bad.append((v, "kind", o.kind, o.name))
            continue
        n += 1
        u = " ".join(o.ddl.upper().split())
        if "IF NOT EXISTS" in u or re.search(r"\bAS\s+SELECT\b", u):
            bad.append((v, o.kind, o.name))
        if o.kind == "table" and not u.startswith("CREATE TABLE"):
            bad.append((v, "not-plain", o.name))
        if o.kind == "index" and not re.match(r"CREATE (UNIQUE )?INDEX ", u):
            bad.append((v, "not-plain-index", o.name))
head = {(o.kind, o.name): o.ddl for o in sv.SCHEMAS[H]}
diff = sorted({(v, o.kind, o.name) for v in range(1, H) for o in sv.SCHEMAS[v]
               if head.get((o.kind, o.name)) not in (None, o.ddl)})
print(f"HEAD {H}")
print(f"table/index constructors over v1..v{H}: {n}")
print(f"constructors outside (b1)'s shape: {len(bad)} {bad}")
print(f"(version, kind, name) whose constructor differs from head: {len(diff)}")
for d in diff:
    print(" ", d)
