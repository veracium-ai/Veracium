#!/usr/bin/env python3
"""specs/0028 §9 — THE ABSENCE PROOF OVER THE SHIPPED AS-OF CODE, in two forms.

    python3 specs/evidence/0028/check_asof_absence.py            # both forms, the report
    python3 specs/evidence/0028/check_asof_absence.py --static   # the static tree only
    python3 specs/evidence/0028/check_asof_absence.py --json OUT # also write the report

CLAIM PROVED: no path from the shipped as-of entry points reaches
`Edge.valid_now`, `Edge.assertable`, `Episode.valid_now` or
`Episode.assertable` — the predicates that read the process wall clock.

COVERED FRACTION — STATED FIRST, because an artifact titled "no as-of path
reaches valid_now" that silently covered a fraction of the as-of surface
would be R3-1's defect in evidence rather than in prose. `src/veracium`
ships ONLY `asof/` (`classify.py`, `adapter.py`, `carrier.py`). The
resolution 0028 specifies — `facts_valid_at`, `read_window`,
`edges_superseding`, the pointer walk — is UNWRITTEN. This proof covers
`classify_as_of`, `assertable_as_of`, everything they reach, and the two
store reads §5.1 names that exist today (`SqliteStore.current_state`,
`SqliteStore.edges`). It covers nothing of the resolution, and it cannot;
the resolution's own absence proof is owed at implementation (spec §9).

FORM 1 — STATIC, the call tree, method stated. An AST walk over
`src/veracium` from the four roots. FOLLOWED: a call to a bare name bound in
the caller's module by `def` or by `from <src module> import name`; a call
`mod.f(...)` where `mod` is a `src/veracium` module imported by the caller;
a call `self.m(...)` inside a class, resolved to that class's own method;
`ClassName.m(...)` and `ClassName(...)` for classes defined in src. NOT
FOLLOWED, and LISTED in the report by receiver so the boundary is visible:
calls on any other receiver (`view.x()`, `store.x()`, `snap.x()`, a callable
parameter) — dynamic dispatch the static form cannot resolve — and calls into
the standard library or third-party packages. Inside every REACHED function
body, every attribute access `.valid_now` / `.assertable` and every call to a
name so spelled is a HIT. Expected hits: 0.

FORM 2 — BEHAVIOURAL, the recording clock, the stronger of the two. The
pytest plugin `asof_recording_clock.py` wraps the four predicates to count
every access and flag any access made while a `classify_as_of` /
`assertable_as_of` frame (or any frame from `asof/`) is on the stack, then
runs the DERIVED exercised surface under it — every `tests/test_*.py` that
reaches the classifier (imports from `veracium.asof` or names either
function), minus this checker's own matrix, listed as excluded because it
runs this checker. That the derived set is the REACHABLE set is itself
measured: a census of every call to either function in `src/` outside
`asof/classify.py` reads zero, so no shipped path reaches the classifier and
naming it is the only way a test can. The bound is printed: the proof covers
the classifier paths those files exercise; a path exercised nowhere is
outside it. Expected: violations 0, classify calls > 0 (a run that never
classified proves nothing and FAILS here), accesses > 0 outside the branch
(the clock was live — those accesses are the exercised files' own tests of
the wall-clock predicates, not near-violations). It fails whether or not the
static tree found the path, which is why it is the stronger form; the static
form is what makes the result legible.

Exit 0 iff both forms hold. Every number printed is measured in this run.

THE PROOF'S OWN EVIDENCE HANDLING IS GUARDED: the behavioural form reads its
clock's JSON report across a process boundary through a duplicate-refusing
decoder (0026's evidence-boundary rule — a repeated key is refused, never
last-wins), so the proof is not taken on trust at its own seam. The suite's
first run on this file caught a plain json.loads there.


# Mutation-Matrix: tests/test_0028_asof_absence.py::test_static_form_detects_an_injected_predicate_access
# (and its siblings there: a hit reached only THROUGH the tree; a behavioural
#  violation planted by a patched callee; the zero-classification run refused)
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve()
WATCHED_NAMES = frozenset({"valid_now", "assertable"})


def _no_dup_pairs(pairs):
    """0026's evidence-boundary rule: JSON read at an evidence boundary goes
    through a duplicate-refusing decoder (a repeated key is refused, never
    last-wins). The clock's report is such a boundary — it crosses a process."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key in the clock's report: {k!r}")
        out[k] = v
    return out
ROOTS = (("veracium/asof/classify.py", None, "classify_as_of"),
         ("veracium/asof/classify.py", None, "assertable_as_of"),
         ("veracium/store/sqlite.py", "SqliteStore", "current_state"),
         ("veracium/store/sqlite.py", "SqliteStore", "edges"))


def repo_root(start=HERE):
    for p in [start] + list(start.parents):
        if (p / "src" / "veracium" / "__init__.py").exists():
            return p
    raise SystemExit("could not find src/veracium above " + str(start))


# ---------------------------------------------------------------- static form
class _Module:
    def __init__(self, path, pkg_root):
        self.path = path
        self.rel = str(path.relative_to(pkg_root.parent))   # veracium/x/y.py
        self.tree = ast.parse(path.read_text())
        self.funcs = {}       # name -> FunctionDef (module level)
        self.classes = {}     # name -> ClassDef
        self.methods = {}     # (class, name) -> FunctionDef
        self.imports = {}     # local name -> (module rel, remote name or None)
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.funcs[node.name] = node
            elif isinstance(node, ast.ClassDef):
                self.classes[node.name] = node
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.methods[(node.name, sub.name)] = sub
        self.pkg_root = pkg_root
        self._resolve_imports(pkg_root, self.tree.body, self.imports)

    def local_imports(self, fn):
        """Imports INSIDE a function body (`from .x import y` at call time —
        `SqliteStore.current_state` binds `derive_current_state` this way).
        The first run of this walker listed that call as an unbound name and
        did not follow it: a function-local import is a followed edge."""
        found = {}
        nodes = [n for n in ast.walk(fn) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self._resolve_imports(self.pkg_root, nodes, found)
        return found

    def _resolve_imports(self, pkg_root, nodes, into):
        pkg_dir = self.path.parent
        for node in nodes:
            if isinstance(node, ast.ImportFrom):
                base = pkg_dir
                for _ in range(max(node.level - 1, 0)):
                    base = base.parent
                if node.level == 0:
                    if not (node.module or "").startswith("veracium"):
                        continue
                    target = pkg_root.parent / pathlib.Path(*node.module.split("."))
                else:
                    target = base / pathlib.Path(*(node.module or "").split(".")) if node.module else base
                for alias in node.names:
                    local = alias.asname or alias.name
                    if (target / (alias.name + ".py")).exists():          # from .pkg import module
                        into[local] = (str((target / (alias.name + ".py")).relative_to(pkg_root.parent)), None)
                    elif (target.with_suffix(".py")).exists():            # from .module import name
                        into[local] = (str(target.with_suffix(".py").relative_to(pkg_root.parent)), alias.name)
                    elif (target / "__init__.py").exists():               # from .pkg import name
                        into[local] = (str((target / "__init__.py").relative_to(pkg_root.parent)), alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("veracium"):
                        p = pkg_root.parent / pathlib.Path(*alias.name.split("."))
                        p = p.with_suffix(".py") if p.with_suffix(".py").exists() else p / "__init__.py"
                        if p.exists():
                            into[alias.asname or alias.name] = (str(p.relative_to(pkg_root.parent)), None)


class StaticWalker:
    def __init__(self, src_dir):
        self.pkg_root = src_dir / "veracium"
        self.modules = {}
        for py in sorted(self.pkg_root.rglob("*.py")):
            m = _Module(py, self.pkg_root)
            self.modules[m.rel] = m
        self.reached = []          # (module rel, qualname)
        self.not_followed = {}     # receiver text -> count
        self.hits = []             # (module rel, qualname, lineno, kind, text)
        self._seen = set()

    def _find_def(self, rel, cls, name):
        m = self.modules.get(rel)
        if m is None:
            return None
        if cls is not None:
            fn = m.methods.get((cls, name))
            return (rel, cls, fn) if fn is not None else None
        fn = m.funcs.get(name)
        if fn is not None:
            return (rel, None, fn)
        if name in m.imports:                       # re-exported name
            tgt_rel, remote = m.imports[name]
            return self._find_def(tgt_rel, None, remote or name)
        if name in m.classes:                       # ClassName(...) -> __init__ if defined
            fn = m.methods.get((name, "__init__"))
            return (rel, name, fn) if fn is not None else None
        return None

    def _resolve_call(self, m, cls, call, imports, nested):
        f = call.func
        if isinstance(f, ast.Name):
            if f.id in nested:
                return None, None           # a nested def: its body is inside the scanned body
            if f.id in m.funcs or f.id in m.classes:
                return self._find_def(m.rel, None, f.id), None
            if f.id in imports:
                tgt_rel, remote = imports[f.id]
                if remote is None:
                    return None, f"{f.id}(...) [imported module called]"
                return self._find_def(tgt_rel, None, remote), None
            return None, f"{f.id}(...) [builtin/unbound name]"
        if isinstance(f, ast.Attribute):
            recv = f.value
            if isinstance(recv, ast.Name):
                if recv.id == "self" and cls is not None:
                    d = self._find_def(m.rel, cls, f.attr)
                    return (d, None) if d else (None, f"self.{f.attr} [no such method on {cls}]")
                if recv.id in imports and imports[recv.id][1] is None:
                    d = self._find_def(imports[recv.id][0], None, f.attr)
                    return (d, None) if d else (None, f"{recv.id}.{f.attr} [not found in module]")
                if recv.id in m.classes:
                    d = self._find_def(m.rel, recv.id, f.attr)
                    return (d, None) if d else (None, f"{recv.id}.{f.attr}")
                if recv.id in imports and imports[recv.id][1] is not None:
                    tgt_rel, remote = imports[recv.id]
                    d = self._find_def(tgt_rel, remote, f.attr)
                    return (d, None) if d else (None, f"{recv.id}.{f.attr} [imported name; no src method of that name]")
                return None, f"{recv.id}.{f.attr}(...)"
            return None, f"<{type(recv).__name__}>.{f.attr}(...)"
        return None, f"<{type(f).__name__}>(...)"

    def walk(self, rel, cls, name):
        d = self._find_def(rel, cls, name)
        if d is None:
            raise SystemExit(f"root not found: {rel} {cls} {name}")
        self._visit(*d)

    def _visit(self, rel, cls, fn):
        key = (rel, cls, fn.name, fn.lineno)
        if key in self._seen:
            return
        self._seen.add(key)
        qual = f"{cls}.{fn.name}" if cls else fn.name
        self.reached.append((rel, qual))
        m = self.modules[rel]
        imports = dict(m.imports)
        imports.update(m.local_imports(fn))          # function-local imports are followed edges
        nested = {n.name for n in ast.walk(fn) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn}
        for node in ast.walk(fn):
            if isinstance(node, ast.Attribute) and node.attr in WATCHED_NAMES:
                self.hits.append((rel, qual, node.lineno, "attribute", ast.unparse(node)))
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name) and f.id in WATCHED_NAMES:
                    self.hits.append((rel, qual, node.lineno, "call", ast.unparse(node)))
                target, why = self._resolve_call(m, cls, node, imports, nested)
                if target is not None:
                    self._visit(*target)
                elif why:
                    self.not_followed[why] = self.not_followed.get(why, 0) + 1


def static_form(src_dir):
    w = StaticWalker(src_dir)
    for rel, cls, name in ROOTS:
        w.walk(rel, cls, name)
    return w


# ----------------------------------------------------------- behavioural form
# The ONE test deselected under the clock, with its reason printed in the report:
# `test_current_path_oracle_identical_post0027` reads the SOURCE of
# `Edge.assertable`'s getter (inspect.getsource) to assert the shipped
# predicate text — under the recording clock the getter IS the wrapper, so the
# observer replaces the thing that test inspects. It classifies nothing
# through the wrapped predicate; deselecting it removes no classification
# from the run (the classify_calls count is printed either way).
DESELECTED_UNDER_CLOCK = ("test_current_path_oracle_identical_post0027",)


# The behavioural form's EXERCISED SURFACE is DERIVED, never hand-listed: every
# test file under tests/ that reaches the classifier (imports from
# veracium.asof or names classify_as_of / assertable_as_of), minus this
# checker's own matrix, which RUNS this checker (recursion), listed as excluded
# with that reason. Research's bound on the first run: "the clock ran ONE file;
# a path through classify_as_of exercised only elsewhere is outside the proof"
# — the static form listed what it did not follow, so this form lists what it
# did not exercise, and derives what it did.
REACHES_CLASSIFIER = ("classify_as_of", "assertable_as_of", "veracium.asof", "from veracium.asof")
EXCLUDED_FROM_CLOCK = {"tests/test_0028_asof_absence.py": "this checker's own matrix — it runs this checker; recursion"}


def exercised_test_files(root):
    hits = []
    for py in sorted((root / "tests").glob("test_*.py")):
        text = py.read_text()
        if any(tok in text for tok in REACHES_CLASSIFIER):
            hits.append(str(py.relative_to(root)))
    return [h for h in hits if h not in EXCLUDED_FROM_CLOCK], {h: EXCLUDED_FROM_CLOCK[h] for h in hits if h in EXCLUDED_FROM_CLOCK}


def src_call_sites(src_dir):
    """Every CALL of classify_as_of / assertable_as_of in src/veracium outside
    asof/classify.py itself, by AST (a Name or Attribute callee so spelled).
    Why it is measured here: the derived exercised set is files that MENTION
    the classifier, and the residual hole in that derivation would be a test
    reaching the classifier INDIRECTLY through a shipped API that calls it
    without the test naming it. If this census is ZERO, no shipped path
    reaches the classifier, naming it is the only way a test can, and the
    derived set is the REACHABLE set — complete, not merely careful."""
    sites = []
    for py in sorted((src_dir / "veracium").rglob("*.py")):
        rel = str(py.relative_to(src_dir))
        if rel.endswith("asof/classify.py"):
            continue
        for node in ast.walk(ast.parse(py.read_text())):
            if isinstance(node, ast.Call):
                f = node.func
                name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                if name in ("classify_as_of", "assertable_as_of"):
                    sites.append(f"{rel}:{node.lineno}")
    return sites


def _test_carrying(root, test_paths, test_name):
    for tp in test_paths:
        if f"def {test_name}(" in (root / tp).read_text():
            return tp
    return None


def behavioural_form(root, test_paths, extra_args=()):
    import tempfile
    fd, name = tempfile.mkstemp(prefix="asof_clock_report.", suffix=".json")
    os.close(fd)
    report = pathlib.Path(name)
    report.unlink()                      # the plugin writes it at session end
    env = dict(os.environ)
    env["PYTHONPATH"] = str(HERE.parent) + os.pathsep + env.get("PYTHONPATH", "")
    env["ASOF_CLOCK_REPORT"] = str(report)
    desel = []
    for tname in DESELECTED_UNDER_CLOCK:
        tp = _test_carrying(root, test_paths, tname)
        if tp:
            desel += ["--deselect", f"{tp}::{tname}"]
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
           "-p", "asof_recording_clock", *[str(root / tp) for tp in test_paths], *desel, *extra_args]
    r = subprocess.run(cmd, cwd=str(root), env=env, capture_output=True, text=True)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    counts = (json.loads(report.read_text(), object_pairs_hook=_no_dup_pairs)
              if report.exists() else None)
    if report.exists():
        report.unlink()
    return r.returncode, tail, counts


# ------------------------------------------------------------------- report
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true", help="the static tree only")
    ap.add_argument("--json", help="write the machine-readable report here")
    ap.add_argument("--src", help="walk THIS src dir instead of the repo's (the matrix uses it)")
    ap.add_argument("--test-path", action="append", default=None,
                    help="override the DERIVED exercised set (the matrix uses it); repeatable")
    ap.add_argument("--pytest-arg", action="append", default=[])
    a = ap.parse_args(argv)
    root = repo_root()
    src_dir = pathlib.Path(a.src).resolve() if a.src else root / "src"
    out = {"covered": "classify_as_of, assertable_as_of and everything they reach; "
                      "SqliteStore.current_state and SqliteStore.edges (the §5.1 reads that exist). "
                      "NOT the resolution (facts_valid_at, read_window, edges_superseding): unwritten; "
                      "its proof is owed at implementation."}
    print("ABSENCE PROOF over the SHIPPED as-of code — predicates watched:",
          ", ".join(sorted(WATCHED_NAMES)))
    print("covered fraction:", out["covered"])
    w = static_form(src_dir)
    out["static"] = {"reached": [f"{r}:{q}" for r, q in w.reached],
                     "not_followed": w.not_followed,
                     "hits": [{"module": r, "function": q, "line": ln, "kind": k, "text": t}
                              for r, q, ln, k, t in w.hits]}
    print(f"\nSTATIC — reached {len(w.reached)} function(s) from {len(ROOTS)} root(s):")
    for r, q in w.reached:
        print(f"  {r}:{q}")
    print(f"STATIC — not followed (dynamic receivers / non-src callees), {sum(w.not_followed.values())} call(s) over {len(w.not_followed)} form(s):")
    for why, n in sorted(w.not_followed.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {why}")
    print(f"STATIC — hits on {'/'.join(sorted(WATCHED_NAMES))} in reached bodies: {len(w.hits)}")
    for h in out["static"]["hits"]:
        print(f"  HIT {h['module']}:{h['function']}:{h['line']} {h['kind']} {h['text']}")
    ok = len(w.hits) == 0
    if not a.static:
        if a.test_path:
            test_paths, excluded = list(a.test_path), {}
            derived = False
        else:
            test_paths, excluded = exercised_test_files(root)
            derived = True
        rc, tail, counts = behavioural_form(root, test_paths, a.pytest_arg)
        out["behavioural"] = {"pytest_exit": rc, "pytest_tail": tail, "counts": counts,
                              "exercised_files": test_paths, "exercised_set_derived": derived,
                              "excluded_files": excluded,
                              "deselected_under_clock": list(DESELECTED_UNDER_CLOCK)}
        sites = src_call_sites(src_dir)
        out["behavioural"]["src_call_sites_outside_classify"] = sites
        print(f"\nBEHAVIOURAL — exercised test files ({'DERIVED: every tests/test_*.py that reaches the classifier' if derived else 'OVERRIDDEN on the command line'}): {', '.join(test_paths)}")
        for f, why in excluded.items():
            print(f"BEHAVIOURAL — excluded from the clock: {f} — {why}")
        print(f"BEHAVIOURAL — src call sites of the classifier outside asof/classify.py: {len(sites)}"
              + (f" {sites}" if sites else "")
              + (" — no shipped path reaches the classifier, so naming it is the only way a test can: the derived set is the REACHABLE set"
                 if not sites else " — a shipped path reaches the classifier; a test could exercise it WITHOUT naming it, so the derived set is NOT the reachable set"))
        print("BEHAVIOURAL — bound: the proof covers the classifier paths THESE files exercise; a path exercised nowhere is outside it")
        print(f"BEHAVIOURAL — pytest under the recording clock: exit {rc}; {tail}")
        print(f"BEHAVIOURAL — deselected under the clock ({len(DESELECTED_UNDER_CLOCK)}): "
              f"{', '.join(DESELECTED_UNDER_CLOCK)} — it inspects the SOURCE of the wrapped getter; "
              f"it classifies nothing, so no classification leaves the run")
        if counts is None:
            print("BEHAVIOURAL — NO REPORT WRITTEN (the plugin did not run): FAIL")
            ok = False
        else:
            print(f"BEHAVIOURAL — classify_as_of calls: {counts['classify_calls']}; predicate accesses: "
                  f"{counts['accesses']} {counts['by_predicate']}; VIOLATIONS (access with an as-of frame on the stack): {counts['violations']}")
            print("BEHAVIOURAL — the accesses above with no as-of frame are the exercised files' OWN tests of the wall-clock "
                  "predicates (the S2 valid_from predicate tests touch the very predicates the as-of branch must not use); "
                  "they are not near-violations, they are the instrument proving it is live")
            for v in counts["violation_sites"][:10]:
                print(f"  VIOLATION {v['predicate']} under {v['asof_frame']}")
            if counts["classify_calls"] == 0:
                print("BEHAVIOURAL — zero classifications exercised: the run proves nothing: FAIL")
                ok = False
            if counts["accesses"] == 0:
                print("BEHAVIOURAL — the clock never fired at all: wrapper not live: FAIL")
                ok = False
            if counts["violations"] != 0 or rc != 0:
                ok = False
    out["ok"] = ok
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1))
    print("\nABSENCE PROOF:", "OK — no as-of path reaches the wall-clock predicates (covered fraction as stated)" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
