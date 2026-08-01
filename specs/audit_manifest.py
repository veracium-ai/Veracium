#!/usr/bin/env python3
"""Generate and verify the store-mutator call-site manifest for specs/0002.

The audit's first two enumerations were done from memory and from a grep keyed
on assignment; both were incomplete. The third was a line-oriented regex scan,
and the third external review showed it could silently reattach verdicts to
different operations. This one parses the AST.

Identity is (file, qualified scope, mutator, fingerprint), where the fingerprint
is derived from WHAT THE CALL IS -- its normalised expression and enclosing
control-flow context -- not from where it sits in a sequence. Moving a call
keeps its verdict; swapping two different calls does not.

  --write   regenerate specs/generated/0002-audit-manifest.md
  --check   fail if the code and the verdicts disagree (CI, spec 0002 N8)
  (none)    list what was found, and what was excluded
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
BASE = SRC / "store" / "base.py"
TESTS = ROOT / "tests"
MANIFEST = ROOT / "specs" / "generated" / "0002-audit-manifest.md"

MUTATOR_PREFIXES = ("add_", "invalidate_", "delete_", "forget_", "set_")
OP_CLASSES = {"write-time", "maintain-time"}
EVIDENCE_VALUES = {"yes", "**no**"}
SPEC_REF = re.compile(r"\b000\d\b")
TEST_REF = re.compile(r"\btest_\w+")


def mutators() -> list[str]:
    """Store methods that write persistent state, from the interface itself."""
    tree = ast.parse(BASE.read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith(MUTATOR_PREFIXES):
                out.add(node.name)
    return sorted(out)


def _fingerprint(call: ast.Call, context: str) -> str:
    """Identity of a call: its normalised expression plus enclosing context.

    Deliberately NOT positional. Two different calls to one mutator in one
    function are distinguished by their arguments and branch; reordering them
    changes nothing, swapping them changes both.
    """
    try:
        expr = ast.unparse(call)
    except Exception:                       # pragma: no cover - very old Python
        expr = f"{getattr(call.func, 'attr', '?')}(...)"
    return hashlib.sha1(f"{context}|{expr}".encode()).hexdigest()[:8]


class _Visitor(ast.NodeVisitor):
    def __init__(self, names: set[str], rel: str):
        self.names, self.rel = names, rel
        self.scope: list[str] = []
        self.ctx: list[str] = []
        self.found: list[tuple] = []

    def _scoped(self, node, label=None):
        self.scope.append(node.name if label is None else label)
        self.generic_visit(node)
        self.scope.pop()

    visit_ClassDef = _scoped
    visit_FunctionDef = _scoped
    visit_AsyncFunctionDef = _scoped

    def _block(self, node):
        """Record WHICH BRANCH, not just the nesting depth.

        `if/else` at the same depth are different operations: in `expire()` the
        decay write and the stale-flag write are both `store.add_edge(e)` inside
        four nested conditionals, and are distinguishable only by branch.
        """
        kind = type(node).__name__
        # The CONDITION is what makes two structurally identical branches
        # different operations: apply_supersession has two `store.add_edge(prior)`
        # calls at the same depth, one guarded by the reinforcement test and one
        # by `_subsumes(...)`. Branch shape alone cannot tell them apart.
        for attr in ("test", "iter"):
            probe = getattr(node, attr, None)
            if probe is not None:
                try:
                    kind += "(" + hashlib.sha1(
                        ast.unparse(probe).encode()).hexdigest()[:4] + ")"
                except Exception:
                    pass
                break
        for field in ("body", "orelse", "finalbody", "handlers"):
            for child in getattr(node, field, []) or []:
                self.ctx.append(f"{kind}.{field}")
                self.visit(child)
                self.ctx.pop()
        # everything that is not a branch body (test, iter, items, ...)
        for field, value in ast.iter_fields(node):
            if field in ("body", "orelse", "finalbody", "handlers"):
                continue
            for child in (value if isinstance(value, list) else [value]):
                if isinstance(child, ast.AST):
                    self.visit(child)

    visit_If = _block
    visit_For = _block
    visit_AsyncFor = _block
    visit_While = _block
    visit_Try = _block
    visit_With = _block

    def visit_Call(self, node):
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in self.names:
            scope = ".".join(self.scope) or "<module>"
            context = ">".join(self.ctx) or "-"
            self.found.append((self.rel, scope, f.attr,
                               _fingerprint(node, context), node.lineno, context))
        self.generic_visit(node)


def call_sites(names: list[str]):
    """(file, scope, mutator, fingerprint, line, context), excluding store impls."""
    out, excluded = [], []
    nameset = set(names)
    for p in sorted(SRC.rglob("*.py")):
        rel = p.relative_to(ROOT).as_posix()
        v = _Visitor(nameset, rel)
        v.visit(ast.parse(p.read_text()))
        # The store implementations ARE the mutators; auditing their internals is
        # a different question from auditing who calls them. Excluded on purpose
        # and REPORTED, because a silent filter is how coverage claims rot.
        (excluded if "/store/" in rel else out).extend(v.found)
    out.sort(key=lambda r: (r[0], r[4]))
    return out, excluded


def _validate(sites) -> list[str]:
    """N8: every site carries a verdict AND a test or an owning spec."""
    from audit_dispositions import DISPOSITIONS
    problems = []
    want = {(r, s, m, fp) for r, s, m, fp, _, _ in sites}
    have = set(DISPOSITIONS)
    for k in sorted(want - have):
        problems.append(f"call site with no disposition: {k}")
    for k in sorted(have - want):
        problems.append(f"disposition for a call site that no longer exists: {k}")

    for k in sorted(want & have):
        v = DISPOSITIONS[k]
        if len(v) != 5:
            problems.append(f"{k}: expected 5 fields, got {len(v)}"); continue
        cls, fields, ev, verdict, test = v
        if cls not in OP_CLASSES:
            problems.append(f"{k}: operation class {cls!r} not in {sorted(OP_CLASSES)}")
        if ev not in EVIDENCE_VALUES:
            problems.append(f"{k}: evidence-bearing {ev!r} not in {sorted(EVIDENCE_VALUES)}")
        if not fields.strip():
            problems.append(f"{k}: no trust fields recorded")
        if not verdict.strip():
            problems.append(f"{k}: no verdict")
        if not test.strip():
            problems.append(f"{k}: no test or owning spec — N8 requires both")
            continue
        moved_or_open = "➡️" in verdict or "🔴" in verdict
        if moved_or_open:
            if not SPEC_REF.search(test) and not SPEC_REF.search(verdict):
                problems.append(f"{k}: moved/open rows must name an owning spec, got {test!r}")
        elif not TEST_REF.search(test):
            problems.append(f"{k}: clean/fixed rows must name a concrete test, got {test!r}")
    return problems


def _missing_tests():
    """Named tests that do not exist in the tree, split by verdict.

    FATAL for clean rows. A site certified clean whose test does not exist is
    an unbacked coverage claim -- which is the exact failure this manifest was
    built to prevent, and 11 of 17 clean rows were in that state when the check
    was added. Advisory for moved/open rows, whose tests land with their spec.
    """
    from audit_dispositions import DISPOSITIONS
    corpus = "\n".join(p.read_text() for p in TESTS.rglob("test_*.py"))
    clean, pending = [], []
    for k, v in DISPOSITIONS.items():
        gone = [n for n in TEST_REF.findall(v[4]) if f"def {n}" not in corpus]
        if not gone:
            continue
        target = pending if ("\u27a1\ufe0f" in v[3] or "\U0001f534" in v[3]) else clean
        target.append((k, gone))
    return clean, pending


def render(sites) -> str:
    from audit_dispositions import DISPOSITIONS
    rows = []
    for rel, scope, mut, fp, ln, ctx in sites:
        cls, fields, ev, verdict, test = DISPOSITIONS.get(
            (rel, scope, mut, fp), ("", "", "", "**NO VERDICT**", ""))
        rows.append(f"| `{rel}:{ln}` | `{scope}()` | `{mut}` | `{fp}` | {cls} | "
                    f"{fields} | {ev} | {verdict} | {test} |")
    open_n = sum(1 for r in rows if "🔴" in r)
    moved = sum(1 for r in rows if "➡️" in r)
    return ("<!-- GENERATED by specs/audit_manifest.py — do not hand-edit.\n"
            "     Verdicts live in specs/audit_dispositions.py.\n"
            "     Regenerate: python3 specs/audit_manifest.py --write\n"
            "     Verify:     python3 specs/audit_manifest.py --check -->\n\n"
            "# specs/0002 — store-mutator call-site manifest\n\n"
            f"**{len(sites)} call sites** across **{len(mutators())} mutators**, "
            "enumerated by **parsing the AST** of every module under "
            "`src/veracium/`, with the mutator set read from the interface in "
            "`store/base.py`. Two earlier enumerations (from memory, then from a "
            "grep keyed on assignment) were incomplete, and a third (a "
            "line-oriented regex scan) could silently reattach a verdict to a "
            "different operation.\n\n"
            f"**{len(sites) - open_n - moved} clean · {open_n} open · {moved} "
            "moved to another spec.** Clean sites are listed because a "
            "findings-only audit cannot demonstrate coverage.\n\n"
            "**Identity is `(file, scope, mutator, fingerprint)`.** The "
            "fingerprint is a hash of the call's normalised expression and its "
            "enclosing control-flow context — **what the call is, not where it "
            "sits**. Moving a call keeps its verdict; swapping two different "
            "calls invalidates both. **Line numbers are informational.**\n\n"
            "**Stated limits** — this establishes coverage of *direct* calls "
            "only. It cannot see aliased or indirect invocation "
            "(`getattr(store, name)(...)`, a bound method passed as a callback), "
            "and it deliberately excludes the store implementations themselves, "
            "which are the mutators rather than callers of them. **The "
            "`evidence-bearing?` column is a reviewed classification, not a "
            "derived fact** — see `0002` §6a.\n\n"
            "| call site | in | mutator | fp | class | trust fields touched | "
            "evidence-bearing? | verdict | test / owning spec |\n"
            "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sites, excluded = call_sites(mutators())

    if a.write:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(render(sites))
        print(f"wrote {MANIFEST.relative_to(ROOT)}: {len(sites)} sites")
        return 0

    if a.check:
        problems = _validate(sites)
        if problems:
            for p in problems:
                print(p, file=sys.stderr)
            print(f"\n{len(problems)} problem(s). Every store mutation must carry "
                  f"an operation class, the trust fields it touches, an "
                  f"evidence-bearing classification, a verdict, and a concrete "
                  f"test (clean rows) or owning spec (moved/open rows). "
                  f"Regenerate with --write after fixing "
                  f"specs/audit_dispositions.py.", file=sys.stderr)
            return 1
        if MANIFEST.exists() and MANIFEST.read_text() != render(sites):
            print("manifest is stale — regenerate with --write", file=sys.stderr)
            return 1
        clean_missing, pending = _missing_tests()
        if clean_missing:
            for k, gone in clean_missing:
                print(f"{k[1]}() {k[2]}: certified CLEAN but names no existing "
                      f"test: {', '.join(gone)}", file=sys.stderr)
            print(f"\n{len(clean_missing)} clean site(s) cite a test that does not "
                  f"exist. A clean verdict backed by an imaginary test is an "
                  f"unbacked coverage claim. Point the row at a real test, or "
                  f"write one.", file=sys.stderr)
            return 1
        if pending:
            print(f"note: {len(pending)} moved/open site(s) name tests that land "
                  f"with their spec — expected.")
        print(f"manifest ok: {len(sites)} call sites, all dispositioned, "
              f"every clean row backed by a test that exists")
        return 0

    print(f"{len(sites)} call sites across {len(mutators())} mutators")
    for rel, scope, mut, fp, ln, ctx in sites:
        print(f"  {rel}:{ln:<5} {scope}()  {mut}  fp={fp}  ctx={ctx}")
    print(f"\n{len(excluded)} call(s) excluded (store implementations — the "
          f"mutators themselves, not callers of them)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
