#!/usr/bin/env python3
"""0018 adjacent rungs, the implementation's repository copy (I33 (iii)): the GENERATED census of head-bound references in
the forward step's reach. Derived from the reviewed specs/evidence/0018-adjacent-rungs/dev-model/head_bound_census.py,
whose bytes stay as reviewed; the differences are research's stage-1 finding on the plan (a call-following census goes
blind on a table): the reach follows a store function or class merely REFERENCED, not only one called, and it reads
MODULE-LEVEL VALUES like function bodies: reaching a module-level name visits every expression bound to it (`=`, `:`,
`+=`, through imports), so a table split into named sub-tuples, extended, aliased or kept in its own module stays in
reach, and a class attribute resolves to its member. The table name is a root, so a table nothing yet reads is read.

Usage:
  head_bound_census.py <tree-root> --json             print the set, one JSON object per reference
  head_bound_census.py <tree-root> --check <expected>  compare with a committed expectation; exit 1 on any difference

THE SET (0018 amendment v0.4.1 §2a): every reference to the store's head version, `SCHEMA_VERSION` as defined in
`veracium.store.schema_version`, inside the forward step's REACH, by AST:
  - the root `_apply_forward` (src/veracium/store/migration.py), its whole body, nested functions included;
  - the module-level name `FORWARD_ENTRIES`, if bound or imported in that module, and every module-level name reached:
    each is visited through every expression bound to it, a string equal to a function of its module counting as a
    reference. `--json` prints the callables so reached from the table as `table_roots`; a cell compares them with the
    runtime table once a table exists (owed at T1: no table exists at this commit);
  - every module-level function it calls or references, transitively, resolved by name within src/veracium/store/ (a direct name, a
    `from .m import f [as g]` import, or `m.f` where `m` is bound to a store module);
  - for every CLASS it calls (constructs, which includes every `raise X(...)`), that class's `__init__`, and the
    `__init__` of each of its bases defined within src/veracium/store/; and what those call, transitively.
A reference is a Name bound to the store's SCHEMA_VERSION, in any of the forms that bind one: the direct import
`from .schema_version import SCHEMA_VERSION`, an import-as (`... import SCHEMA_VERSION as X`), a module-level alias
(`X = SCHEMA_VERSION`, followed through chains), or an Attribute `m.SCHEMA_VERSION` where `m` is bound to the defining
module (`from . import schema_version as m`, `import veracium.store.schema_version as m`). Same-named constants of
OTHER modules (diagnostics.SCHEMA_VERSION, telemetry.SCHEMA_VERSION) are not references.

NAMED RESIDUAL: a lookup built at run time (`getattr(mod, "SCHEMA_" + "VERSION")`, `globals()[name]`, an import by a
computed string) is out of reach of an AST census. The rung's own `older` hook is outside the reach by construction
(v0.4.1 §2a); its events' (b, t) are held by the model's A2 cells and I38, not by this census.

Each reference is reported with: module, function (qualified, nested defs dotted), line, kind
(guard | error-argument | error-default | other), and the call path from the root. `--check` compares the set of
(module, function, line, kind) with the expectation file and names every difference."""
# Mutation-Matrix: tests/test_0018_adjacent_rungs_evidence.py::test_the_repository_census_sees_a_table_and_refuses_each_plant
from __future__ import annotations

import ast
import json
import pathlib
import sys

PKG = "veracium.store"
DEFINER = "veracium.store.schema_version"
ROOT = ("veracium.store.migration", "_apply_forward")
TABLE = "FORWARD_ENTRIES"


def modname(tree_root: pathlib.Path, path: pathlib.Path) -> str:
    rel = path.relative_to(tree_root / "src").with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_from(module: str, level: int, target: str | None, is_pkg: bool = False) -> str:
    if level == 0:
        return target or ""
    base = module.split(".")
    pkg = base if is_pkg else base[:-1]              # a module's package (a package's __init__ is its own)
    pkg = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg
    return ".".join(pkg + ([target] if target else []))


class Module:
    def __init__(self, name: str, path: pathlib.Path):
        self.name, self.path = name, path
        self.tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.funcs = {n.name: n for n in self.tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.classes = {n.name: n for n in self.tree.body if isinstance(n, ast.ClassDef)}
        self.bindings: dict[str, list] = {}              # module-level name -> every expression bound to it
        self.members: dict[str, dict] = {}               # class -> attribute -> its def, or its value expression

        def module_level(stmts):
            for s in stmts:
                targets = s.targets if isinstance(s, ast.Assign) else [s.target] if isinstance(s, (ast.AnnAssign, ast.AugAssign)) else []
                value = getattr(s, "value", None)
                for tg in targets:
                    for x in ast.walk(tg):
                        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store) and value is not None:
                            self.bindings.setdefault(x.id, []).append(value)
                if isinstance(s, (ast.If, ast.Try, ast.With)):      # a conditional definition is still module-level
                    for f in ("body", "orelse", "finalbody"):
                        module_level(getattr(s, f, []) or [])
                    for h in getattr(s, "handlers", []) or []:
                        module_level(h.body)
        module_level(self.tree.body)
        for c in self.classes.values():
            mem = self.members.setdefault(c.name, {})
            for s in c.body:
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mem[s.name] = s
                elif isinstance(s, ast.Assign) and s.value is not None:
                    for tg in s.targets:
                        if isinstance(tg, ast.Name):
                            mem[tg.id] = s.value
        self.imported: dict[str, tuple[str, str]] = {}   # local name -> (module, attr)
        self.modalias: dict[str, str] = {}               # local name -> module
        for n in ast.walk(self.tree):
            if isinstance(n, ast.ImportFrom):
                src = resolve_from(self.name, n.level, n.module, path.name == "__init__.py")
                for a in n.names:
                    local = a.asname or a.name
                    # `from . import schema_version as m` binds a MODULE
                    self.imported[local] = (src, a.name)
                    self.modalias.setdefault(local, f"{src}.{a.name}")
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.asname:
                        self.modalias[a.asname] = a.name
        self.sv_names: set[str] = set()                  # local names bound to the store's SCHEMA_VERSION
        self.sv_modules: set[str] = {k for k, v in self.modalias.items() if v == DEFINER}


def load(tree_root: pathlib.Path) -> dict[str, Module]:
    mods = {}
    for p in sorted((tree_root / "src/veracium/store").rglob("*.py")):
        m = Module(modname(tree_root, p), p)
        mods[m.name] = m
    # names bound to the store's SCHEMA_VERSION, per module: the definer's own name, imports of it (any spelling),
    # then module-level aliases, followed to a fixed point (an alias of an alias)
    for m in mods.values():
        if m.name == DEFINER:
            m.sv_names.add("SCHEMA_VERSION")
        for local, (src, attr) in m.imported.items():
            if src == DEFINER and attr == "SCHEMA_VERSION":
                m.sv_names.add(local)
    changed = True
    while changed:
        changed = False
        for m in mods.values():
            for n in m.tree.body:
                if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and is_ref(m, n.value):
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    for tg in targets:
                        if isinstance(tg, ast.Name) and tg.id not in m.sv_names:
                            m.sv_names.add(tg.id); changed = True
            for local, (src, attr) in m.imported.items():     # an import of another module's alias
                if src in mods and attr in mods[src].sv_names and local not in m.sv_names:
                    m.sv_names.add(local); changed = True
    return mods


def is_ref(m: Module, node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in m.sv_names
    if isinstance(node, ast.Attribute) and node.attr == "SCHEMA_VERSION" and isinstance(node.value, ast.Name):
        return node.value.id in m.sv_modules
    return False


def kind_of(parents: list, node: ast.AST, in_error_init: bool) -> str:
    if in_error_init:
        return "error-default"
    for p in reversed(parents):
        if isinstance(p, ast.If) and any(x is node for x in ast.walk(p.test)):
            return "guard"
        if isinstance(p, ast.Call):
            callee = ast.unparse(p.func)
            if callee.endswith(("Error", "Exception")):
                return "error-argument"
        if isinstance(p, ast.stmt):
            break
    return "other"


def census(tree_root: pathlib.Path) -> list[dict]:
    mods = load(tree_root)

    def resolve_call(m: Module, func: ast.AST):
        """-> ('func'|'class'|'bind', module, name) | ('member', module, class, attribute) | None, within the store
        package. A name is looked up as a function, a class, then a module-level binding."""
        def in_module(src, name):
            mm = mods[src]
            kind = "func" if name in mm.funcs else "class" if name in mm.classes else "bind" if name in mm.bindings else None
            return (kind, src, name) if kind else None
        if isinstance(func, ast.Name):
            r = in_module(m.name, func.id)
            if r:
                return r
            if func.id in m.imported:
                src, attr = m.imported[func.id]
                if src in mods:
                    return in_module(src, attr)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in m.modalias and m.modalias[func.value.id] in mods:
                r = in_module(m.modalias[func.value.id], func.attr)
                if r:
                    return r
            owner = resolve_call(m, func.value)
            if owner and owner[0] == "class" and func.attr in mods[owner[1]].members.get(owner[2], {}):
                return ("member", owner[1], owner[2], func.attr)
        return None

    def class_inits(modn: str, cname: str, seen: set):
        """yield (module, class, __init__ node) for the class and its in-package bases"""
        if (modn, cname) in seen:
            return
        seen.add((modn, cname))
        m = mods[modn]; c = m.classes[cname]
        init = next((x for x in c.body if isinstance(x, ast.FunctionDef) and x.name == "__init__"), None)
        if init is not None:
            yield modn, f"{cname}.__init__", init
        for b in c.bases:
            r = resolve_call(m, b)
            if r and r[0] == "class":
                yield from class_inits(r[1], r[2], seen)

    out, seen_fn, seen_cls = [], set(), set()
    census.via_table = []
    work = [(ROOT[0], ROOT[1], mods[ROOT[0]].funcs[ROOT[1]], (f"{ROOT[0]}:{ROOT[1]}",), False)]

    def follow(m, node, path):
        take(resolve_call(m, node), path)
        # a name bound here AND imported: a later import rebinds it, so neither is assumed to win and both are followed
        if isinstance(node, ast.Name) and node.id in m.imported and m.imported[node.id][0] in mods:
            src, attr = m.imported[node.id]
            take(resolve_call(mods[src], ast.Name(id=attr, ctx=ast.Load())), path)

    def take(r, path):
        if not r:
            return
        if r[0] == "func":
            fm, fn = r[1], r[2]
            work.append((fm, fn, mods[fm].funcs[fn], path + (f"{fm}:{fn}",), False))
        elif r[0] == "class" and (r[1], r[2]) not in seen_cls:
            seen_cls.add((r[1], r[2]))
            for im, iq, inode in class_inits(r[1], r[2], set()):
                work.append((im, iq, inode, path + (f"{im}:{iq}",), True))
        elif r[0] == "bind":
            q = f"<module>.{r[2]}"
            work.append((r[1], q, ast.Tuple(elts=list(mods[r[1]].bindings[r[2]]), ctx=ast.Load()), path + (f"{r[1]}:{q}",), False))
        elif r[0] == "member":
            q = f"{r[2]}.{r[3]}"
            work.append((r[1], q, mods[r[1]].members[r[2]][r[3]], path + (f"{r[1]}:{q}",), False))

    follow(mods[ROOT[0]], ast.Name(id=TABLE, ctx=ast.Load()), (f"{ROOT[0]}:{TABLE}",))

    while work:
        modn, qual, node, path, is_err_init = work.pop()
        if (modn, qual) in seen_fn:
            continue
        seen_fn.add((modn, qual))
        if path and path[0].endswith(f":{TABLE}") and not qual.startswith("<module>."):
            census.via_table.append(f"{modn}:{qual}")
        m = mods[modn]

        def visit(n, parents, fqual):
            for child in ast.iter_child_nodes(n):
                cq = fqual
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cq = f"{fqual}.{child.name}"        # a nested def is part of its enclosing body, named dotted
                if is_ref(m, child):
                    out.append({"module": modn, "function": cq, "line": child.lineno,
                                "kind": kind_of(parents + [n], child, is_err_init), "via": " -> ".join(path)})
                # a store function, class or module-level value REFERENCED, called or not: `step = f`, `(f, g)`, a default
                if isinstance(child, (ast.Name, ast.Attribute)) and isinstance(child.ctx, ast.Load):
                    follow(m, child, path)
                # inside a module-level value, a string naming a function of its module is a reference to it
                if (qual.startswith("<module>.") and isinstance(child, ast.Constant) and isinstance(child.value, str)
                        and child.value in m.funcs):
                    follow(m, ast.Name(id=child.value, ctx=ast.Load()), path)
                visit(child, parents + [n], cq)

        visit(node, [], qual)
    out.sort(key=lambda r: (r["module"], r["line"], r["function"]))
    census.reached = sorted(f"{a}:{b}" for a, b in seen_fn)
    # what the table reaches: the callables whose path to them runs through the table's own name
    census.table_roots = sorted({r for r in census.via_table})
    return out


def key(r):
    return (r["module"], r["function"], r["line"], r["kind"])


def main(argv):
    if len(argv) < 3 or argv[2] not in ("--json", "--check") or (argv[2] == "--check" and len(argv) != 4):
        print(__doc__.split("\n\n")[1]); return 2
    rows = census(pathlib.Path(argv[1]))
    if argv[2] == "--json":
        print(json.dumps({"root": f"{ROOT[0]}:{ROOT[1]}", "definer": DEFINER, "count": len(rows), "references": rows,
                          "table_roots": census.table_roots, "reached": census.reached},
                         indent=1))
        return 0
    want = json.loads(pathlib.Path(argv[3]).read_text())["references"]
    got_k, want_k = {key(r) for r in rows}, {key(r) for r in want}
    extra, missing = sorted(got_k - want_k), sorted(want_k - got_k)
    for e in extra:
        print("NEW (not in the expectation):", e)
    for e in missing:
        print("MISSING (expected, not found):", e)
    if extra or missing:
        print(f"CENSUS DIFFERS: {len(rows)} found, {len(want)} expected, {len(extra)} new, {len(missing)} missing")
        return 1
    print(f"CENSUS EQUAL: {len(rows)} references in the forward step's reach, as expected")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
