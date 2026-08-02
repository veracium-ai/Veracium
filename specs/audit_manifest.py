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
from collections import Counter
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
BASE = SRC / "store" / "base.py"
TESTS = ROOT / "tests"
MANIFEST = ROOT / "specs" / "generated" / "0002-audit-manifest.md"

OP_CLASSES = {"write-time", "maintain-time"}
EVIDENCE_VALUES = {"act", "observation", "none", "transfer"}
SPEC_REF = re.compile(r"\b\d{4}\b")   # spec numbers are four digits; 000\d stopped at 0009
TEST_REF = re.compile(r"\btest_\w+")


def mutators() -> list[str]:
    """Store methods that write persistent state, read from the `@store_mutator`
    marker on the interface.

    This used to match a remembered list of name prefixes (`add_`, `invalidate_`,
    `delete_`, `forget_`, `set_`), which repeats the audit's original failure one
    level up: the interface was scanned, but *which methods mutate* was still
    recalled rather than declared. Spec 0010 needs `claim_episode_batch`, which
    no prefix covers -- it would have written persistent trust state while being
    invisible to this manifest.

    Parsed rather than imported, so the manifest can be checked from a source
    tree without installing the package.
    """
    tree = ast.parse(BASE.read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                nm = dec.id if isinstance(dec, ast.Name) else getattr(dec, "attr", None)
                if nm == "store_mutator":
                    out.add(node.name)
    if not out:
        raise SystemExit(
            "no @store_mutator methods found in store/base.py. The manifest "
            "cannot enumerate call sites for an empty mutator set, and failing "
            "closed beats certifying zero sites as covered.")
    return sorted(out)


def _fingerprint(call: ast.Call, context: str) -> str:
    """The canonical record of a call: normalised expression + enclosing context.

    Deliberately NOT positional -- two different calls to one mutator in one
    function are distinguished by their arguments and branch, so reordering
    changes nothing and swapping changes both.

    Returned in FULL, not hashed. An abbreviated digest is a collision risk with
    no compensating benefit, and the fourth external review was right that
    nothing checked for one. `call_sites` hashes it for display only, after
    appending a disambiguator for syntactically identical siblings.

    Narrow claim, since v4 overstated it: this follows the call's SYNTAX and its
    selected branch. It does not prove that upstream dataflow still makes the
    operation mean the same thing.
    """
    try:
        expr = ast.unparse(call)
    except Exception:                       # pragma: no cover - very old Python
        expr = f"{getattr(call.func, 'attr', '?')}(...)"
    return f"{context}|{expr}"


def _expr(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:                       # pragma: no cover
        return type(node).__name__


class _Visitor(ast.NodeVisitor):
    """Walks every module, recording each mutator call with its full scope and
    control-flow context.

    The context carries the COMPLETE normalised discriminator of each enclosing
    arm -- the `if` test, the `for` target and iterable, the `except` type and
    position, the `match` pattern and guard -- not a truncated hash of it. v5
    used four hex characters of SHA-1, and the reviewer found a real collision:
    `x == 119` and `x == 125` both hash to `4bd2`, so two different branches
    shared a context and the tie-break fell back to source order, which is the
    failure the fingerprint replaced ordinals to prevent.
    """

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

    def _arm(self, label: str, children):
        for child in children or []:
            self.ctx.append(label)
            self.visit(child)
            self.ctx.pop()

    def _others(self, node, skip):
        for field, value in ast.iter_fields(node):
            if field in skip:
                continue
            for child in (value if isinstance(value, list) else [value]):
                if isinstance(child, ast.AST):
                    self.visit(child)

    def visit_If(self, node):
        t = _expr(node.test)
        self._arm(f"if({t})", node.body)
        self._arm(f"else-of-if({t})", node.orelse)
        self._others(node, {"body", "orelse"})

    def visit_While(self, node):
        t = _expr(node.test)
        self._arm(f"while({t})", node.body)
        self._arm(f"else-of-while({t})", node.orelse)
        self._others(node, {"body", "orelse"})

    def _loop(self, node, kw):
        d = f"{_expr(node.target)} in {_expr(node.iter)}"
        self._arm(f"{kw}({d})", node.body)
        self._arm(f"else-of-{kw}({d})", node.orelse)
        self._others(node, {"body", "orelse"})

    def visit_For(self, node):
        self._loop(node, "for")

    def visit_AsyncFor(self, node):
        self._loop(node, "async-for")

    def visit_Try(self, node):
        self._arm("try", node.body)
        for i, h in enumerate(node.handlers):
            # handler TYPE and position: `except A` and `except B` are different
            # operations, and v5 gave every handler the same context
            self._arm(f"except[{i}]({_expr(h.type) if h.type else 'bare'})", h.body)
        self._arm("else-of-try", node.orelse)
        self._arm("finally", node.finalbody)
        self._others(node, {"body", "handlers", "orelse", "finalbody"})

    visit_TryStar = visit_Try

    def _with(self, node, kw):
        d = ", ".join(_expr(it.context_expr) for it in node.items)
        self._arm(f"{kw}({d})", node.body)
        self._others(node, {"body"})

    def visit_With(self, node):
        self._with(node, "with")

    def visit_AsyncWith(self, node):
        self._with(node, "async-with")

    def visit_Match(self, node):
        subj = _expr(node.subject)
        for i, case in enumerate(node.cases):
            guard = f" if {_expr(case.guard)}" if case.guard else ""
            self._arm(f"match({subj})case[{i}]({_expr(case.pattern)}{guard})",
                      case.body)
        self._others(node, {"cases"})

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

    # Two calls that are identical in expression AND in every enclosing arm are
    # genuinely indistinguishable to this tool. v5 broke the tie with a source-
    # order `#n`, which silently reattached verdicts when the two were swapped.
    # There is no correct automatic answer, so it FAILS and asks for a label --
    # `store.add_edge(e)  # audit: decay-write` -- which is a deliberate human
    # act rather than a guess. No site in the tree needs one today.
    from collections import Counter
    counts = Counter((r, s, m, fp) for r, s, m, fp, _, _ in out)
    ambiguous = {k: n for k, n in counts.items() if n > 1}
    if ambiguous:
        lines = "\n".join(f"  {k[0]} {k[1]}() {k[2]} x{n}" for k, n in ambiguous.items())
        raise SystemExit(
            f"indistinguishable call sites -- identical expression and identical "
            f"enclosing arms:\n{lines}\n"
            f"Add `# audit: <label>` to each so they can be told apart. Source "
            f"order is not an identity: swapping two such calls would silently "
            f"move their verdicts.")
    final = []
    for rel, scope, mut, canon, ln, ctx in out:
        final.append((rel, scope, mut,
                      hashlib.sha256(canon.encode()).hexdigest()[:12], ln, ctx))
    ids = [(r, s, m, fp) for r, s, m, fp, _, _ in final]
    if len(set(ids)) != len(ids):
        dupes = {k for k in ids if ids.count(k) > 1}
        raise SystemExit(f"identity collision after disambiguation: {dupes}. "
                         f"The manifest cannot certify a site it cannot name.")
    return final, excluded


def _validate(sites) -> list[str]:
    """N8: every site carries a verdict AND a test or an owning spec."""
    from audit_dispositions import DISPOSITIONS
    problems = []
    ids = [(r, s, m, fp) for r, s, m, fp, _, _ in sites]
    if len(set(ids)) != len(ids):
        problems.append("duplicate call-site identities — cardinality lost")
    want, have = set(ids), set(DISPOSITIONS)
    for k in sorted(want - have):
        problems.append(f"call site with no disposition: {k}")
    for k in sorted(have - want):
        problems.append(f"disposition for a call site that no longer exists: {k}")

    from audit_dispositions import STATES
    for k in sorted(want & have):
        st = STATES.get(k)
        if st is None:
            problems.append(f"{k}: no declared state — add one to STATES")
        elif st not in VALID_STATES:
            problems.append(f"{k}: state {st!r} not in {sorted(VALID_STATES)}")
        v = DISPOSITIONS[k]
        if len(v) != 5:
            problems.append(f"{k}: expected 5 fields, got {len(v)}"); continue
        cls, fields, ev, verdict, test = v
        if cls not in OP_CLASSES:
            problems.append(f"{k}: operation class {cls!r} not in {sorted(OP_CLASSES)}")
        if ev not in EVIDENCE_VALUES:
            problems.append(f"{k}: evidence class {ev!r} not in {sorted(EVIDENCE_VALUES)}")
        if not fields.strip():
            problems.append(f"{k}: no trust fields recorded")
        if not verdict.strip():
            problems.append(f"{k}: no verdict")
        if not test.strip():
            problems.append(f"{k}: no test or owning spec — N8 requires both")
            continue
        # State semantics are enforced, not just spelling. v5 declared the
        # vocabulary and then assigned three sites `open` while they were owned
        # by 0008/0009/0010 -- a definition nothing checked is a comment.
        # "External" means another spec -- 0002 naming itself is not delegation.
        external = any(m not in ("0002",) for m in SPEC_REF.findall(verdict + test))
        if st == "open" and external:
            problems.append(f"{k}: state `open` means owned by 0002, but the "
                            f"verdict names another spec — use `open_moved`")
        if st in ("moved", "open_moved") and not external:
            problems.append(f"{k}: state `{st}` requires an owning spec, and "
                            f"none is named")
        if st == "moved" and "🔴" in verdict:
            problems.append(f"{k}: state `moved` means the defect is not open "
                            f"here; the verdict says otherwise — use `open_moved`")
        if st in ("open", "moved", "open_moved"):
            if not SPEC_REF.search(test) and not SPEC_REF.search(verdict):
                problems.append(f"{k}: moved/open rows must name an owning spec, got {test!r}")
        elif not TEST_REF.search(test):
            problems.append(f"{k}: clean/fixed rows must name a concrete test, got {test!r}")
    return problems


VALID_STATES = {"clean", "fixed", "open", "moved", "open_moved"}


def _collected_tests() -> set[str]:
    """Tests pytest actually COLLECTS, via `--collect-only`.

    Three attempts at this claim, each narrower than it sounded. v4 asked
    whether `f"def {name}"` appeared in the concatenated files, so `test_foo`
    was satisfied by `def test_foobar`. v5 parsed exact function names from the
    AST, which fixed that and still accepted a function nested inside another,
    one under `if False`, or a method on a class pytest never collects.

    Collection is the real predicate, so ask the collector. Falls back to the
    AST scan when pytest is unavailable, and SAYS SO rather than silently
    weakening the guarantee.
    """
    import subprocess
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "--no-header", "-p", "no:cacheprovider", str(TESTS)],
        capture_output=True, text=True, cwd=ROOT)
    if r.returncode == 0 and r.stdout.strip():
        names = set()
        for line in r.stdout.splitlines():
            if "::" in line:
                names.add(line.rsplit("::", 1)[-1].split("[")[0].strip())
        if names:
            return names
    print("note: pytest --collect-only unavailable; falling back to an AST scan, "
          "which cannot see collection", file=sys.stderr)
    names = set()
    for f in TESTS.rglob("test_*.py"):
        for node in ast.walk(ast.parse(f.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


def _missing_tests():
    """Named tests that do not exist in the tree, split by verdict.

    FATAL for clean rows. A site certified clean whose test does not exist is
    an unbacked coverage claim -- which is the exact failure this manifest was
    built to prevent, and 11 of 17 clean rows were in that state when the check
    was added. Advisory for moved/open rows, whose tests land with their spec.
    """
    from audit_dispositions import DISPOSITIONS, STATES
    collected = _collected_tests()
    clean, pending = [], []
    for k, v in DISPOSITIONS.items():
        gone = [n for n in TEST_REF.findall(v[4]) if n not in collected]
        if not gone:
            continue
        state = STATES.get(k, "clean")
        target = pending if state in ("open", "moved", "open_moved") else clean
        target.append((k, gone))
    return clean, pending


def render(sites) -> str:
    from audit_dispositions import DISPOSITIONS, STATES
    rows = []
    canon = {}
    for rel, scope, mut, fp, ln, ctx in sites:
        canon[fp] = ctx
    for rel, scope, mut, fp, ln, ctx in sites:
        cls, fields, ev, verdict, test = DISPOSITIONS.get(
            (rel, scope, mut, fp), ("", "", "", "**NO VERDICT**", ""))
        rows.append(f"| `{rel}:{ln}` | `{scope}()` | `{mut}` | `{fp}` | "
                    f"`{STATES.get((rel, scope, mut, fp), '?')}` | {cls} | "
                    f"{fields} | {ev} | {verdict} | {test} |")
    tally = Counter(STATES.values())
    unaffected = tally["clean"] + tally["fixed"]
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
            f"**{tally['clean']} clean · {tally['fixed']} fixed · "
            f"{tally['open']} open · {tally['moved']} moved · "
            f"{tally['open_moved']} open and moved** "
            f"— {unaffected} of {len(sites)} sites are unaffected. **States are "
            "declared in `audit_dispositions.py`, not inferred from the rendered "
            "table**: deriving them by searching rows for emoji double-counted "
            "every row whose verdict and test column disagreed, and shipped two "
            "different totals in one review package. Clean sites are listed "
            "because a findings-only audit cannot demonstrate coverage.\n\n"
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
            "`evidence` column is a reviewed classification, not a "
            "derived fact** — see `0002` §6a.\n\n"
            "**Full canonical context per site** is listed after the table, so "
            "the digest can be recomputed rather than trusted.\n\n"
            "| call site | in | mutator | fp | state | class | trust fields touched | "
            "evidence | verdict | test / owning spec |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            "## Canonical context\n\n"
            "The identity hashed into each `fp`. Full discriminators, never a "
            "truncated hash: v5 used four hex characters of the branch condition "
            "and `x == 119` / `x == 125` collided.\n\n```\n"
            + "\n".join(f"{fp}  {ctx}" for fp, ctx in sorted(canon.items()))
            + "\n```\n")


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
                  f"evidence classification, a verdict, and a concrete "
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
