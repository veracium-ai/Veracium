"""specs/0042 — the shared scope resolver (round 7, F2 and F4a's shared root).

The instrument under test replaced a HAND-ENUMERATED list of the forms that bind a name with CPython's own scope
analysis. So the matrix here is the binding grammar itself: the two forms the round-7 reviewer found (`:=` and a
`match` capture), the ones research named in advance, and — the half that catches an over-strict resolver — the
forms that must NOT shadow (a comprehension target, a class-body attribute, a nested function's own parameter).
"""
from __future__ import annotations

import ast
import importlib.util
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "specs" / "evidence" / "0042"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m; spec.loader.exec_module(m); return m


sr = _load("scope_resolution_under_test", EVIDENCE / "scope_resolution.py")

# (label, source, does `S` at the marked use resolve to the MODULE binding?)
GRAMMAR = [
    ("a plain outward read",            "S = 1\ndef f(x):\n    return S.fire(x)\n", True),
    ("an ordinary assignment",          "S = 1\ndef f(x):\n    S = x\n    return S.fire(x)\n", False),
    ("an assignment expression",        "S = 1\ndef f(x):\n    if (S := x):\n        return S.fire(x)\n    return 0\n", False),
    ("a match capture",                 "S = 1\ndef f(x):\n    match x:\n        case [S]:\n            return S.fire(1)\n    return 0\n", False),
    ("a parameter",                     "S = 1\ndef f(S):\n    return S.fire(1)\n", False),
    ("a parameter with a default",      "S = 1\ndef f(S=None):\n    return S.fire(1)\n", False),
    ("a for target",                    "S = 1\ndef f(xs):\n    for S in xs:\n        return S.fire(1)\n", False),
    ("a tuple for target",              "S = 1\ndef f(xs):\n    for (a, S) in xs:\n        return S.fire(1)\n", False),
    ("a star for target",               "S = 1\ndef f(xs):\n    for a, *S in xs:\n        return S.fire(1)\n", False),
    ("a with-as target",                "S = 1\ndef f(cm):\n    with cm as S:\n        return S.fire(1)\n", False),
    ("an except-as target",             "S = 1\ndef f():\n    try:\n        pass\n    except Exception as S:\n        return S.fire(1)\n", False),
    ("an augmented assignment",         "S = 1\ndef f(x):\n    S += x\n    return S.fire(1)\n", False),
    ("a deleted name",                  "S = 1\ndef f(x):\n    del S\n    return S.fire(1)\n", False),
    ("an `import x as S`",              "S = 1\ndef f():\n    import os as S\n    return S.fire(1)\n", False),
    ("a `from x import y as S`",        "S = 1\ndef f():\n    from os import path as S\n    return S.fire(1)\n", False),
    ("a name bound on ONE branch",      "S = 1\ndef f(x):\n    if x:\n        S = x\n    return S.fire(1)\n", False),
    ("an ENCLOSING function's binding", "S = 1\ndef outer(o):\n    S = o\n    def inner():\n        return S.fire(1)\n    return inner\n", False),
    ("a nonlocal declaration",          "S = 1\ndef outer(o):\n    S = o\n    def inner():\n        nonlocal S\n        return S.fire(1)\n    return inner\n", False),
    # the half that catches an OVER-STRICT resolver: these must still reach the module binding
    ("a comprehension target",          "S = 1\ndef f(xs):\n    ys = [S for S in xs]\n    return S.fire(1)\n", True),
    ("a generator-expression target",   "S = 1\ndef f(xs):\n    ys = list(S for S in xs)\n    return S.fire(1)\n", True),
    ("a class-body attribute",          "S = 1\ndef f(x):\n    class C:\n        S = 2\n    return S.fire(x)\n", True),
    ("a NESTED function's parameter",   "S = 1\ndef f(x):\n    def g(S):\n        return S\n    return S.fire(x)\n", True),
    ("a `global` read with no assign",  "S = 1\ndef f(x):\n    global S\n    return S.fire(x)\n", True),
]


def _marked_call(resolver):
    """The `S.fire(...)` call this matrix asks about — exactly one per fixture."""
    calls = [n for n in ast.walk(resolver.tree)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "fire"]
    assert len(calls) == 1, calls
    return calls[0]


@pytest.mark.parametrize("label,src,outward", GRAMMAR, ids=[g[0].replace(" ", "-") for g in GRAMMAR])
def test_the_resolver_answers_every_binding_form(label, src, outward):
    """Every form the LANGUAGE has for binding a name, answered by CPython's own scope analysis rather than by an
    enumeration someone maintains. `:=` and the `match` capture are the round-7 reviewer's two; the rest are
    research's announced attack list plus the must-not-shadow half."""
    r = sr.Resolver(src, f"<{label}>")
    assert r.refers_to_module_binding(_marked_call(r), "S") is outward, label


def test_the_matrix_covers_both_answers_and_the_reviewers_two_forms():
    """A matrix of all-True or all-False rows would pass a resolver that answers a constant (the unfailable class)."""
    answers = {g[2] for g in GRAMMAR}
    assert answers == {True, False} and sum(1 for g in GRAMMAR if g[2]) >= 4 and sum(1 for g in GRAMMAR if not g[2]) >= 4
    labels = " ".join(g[0] for g in GRAMMAR)
    assert "assignment expression" in labels and "match capture" in labels


def test_a_constant_answering_resolver_fails_this_matrix():
    """RULE ZERO's negative control, executed: a resolver that always says True, and one that always says False,
    each fail at least one row — so a green matrix is evidence about the resolver and not about the fixtures."""
    for constant in (True, False):
        wrong = [g[0] for g in GRAMMAR if g[2] is not constant]
        assert wrong, f"a resolver answering {constant} constantly would pass every row"


def test_the_module_block_is_the_binding_itself():
    """A use at module level IS the declared binding, not a reference resolving outward to one."""
    r = sr.Resolver("S = 1\nS.fire(1)\n")
    assert r.refers_to_module_binding(_marked_call(r), "S") is True


def test_site_names_are_the_module_level_declare_site_targets():
    r = sr.Resolver("from .census import declare_site\nA = declare_site('a')\nB = declare_site('b')\n"
                    "def f():\n    C = declare_site('c')\n    return C\n")
    assert r.site_names() == {"A", "B"}          # C is not a module-level binding


def test_a_global_rebinding_of_a_site_is_refused_not_resolved():
    """`global S` alone reads the site; `global S` WITH an assignment replaces the module binding for every other
    reader, which no static reading can account for — refused by name, the reviewer's sanctioned alternative."""
    r = sr.Resolver("from .census import declare_site\nS = declare_site('s')\ndef f(o):\n    global S\n    S = o\n")
    with pytest.raises(sr.UnresolvableScope, match="replaces the declared site"):
        r.refuse_site_rebindings(r.site_names())
    clean = sr.Resolver("from .census import declare_site\nS = declare_site('s')\ndef f():\n    global S\n    return S.fire(1)\n")
    clean.refuse_site_rebindings(clean.site_names())          # a read-only global is not refused


def test_two_scopes_on_one_line_are_joined_in_source_order():
    """symtable exposes no column, so same-line blocks are joined in source order. The control that would catch
    that order diverging: two generator expressions on ONE line binding DIFFERENT names (`asof/resolve.py:445` is
    the real instance that made refusing them unusable)."""
    r = sr.Resolver("def f(xs, ys):\n    return list((aaa for aaa in xs)) + list((bbb for bbb in ys))\n")
    gens = sorted((n for n in ast.walk(r.tree) if isinstance(n, ast.GeneratorExp)), key=lambda n: n.col_offset)
    got = [sorted(x for x in r.block_of(g.elt).get_identifiers() if not x.startswith(".")) for g in gens]
    assert got == [["aaa"], ["bbb"]], got


def test_every_product_and_evidence_module_resolves():
    """The resolver refuses what it cannot join, so 'it refuses nothing on the real tree' is a claim to execute:
    a resolver that refused one real module would take the scan with it."""
    refused = []
    for f in sorted((ROOT / "src" / "veracium").rglob("*.py")) + sorted(EVIDENCE.glob("*.py")):
        try:
            r = sr.Resolver(f.read_text(), str(f)); r.refuse_site_rebindings(r.site_names())
        except sr.UnresolvableScope as e:
            refused.append(f"{f}: {e}")
    assert refused == [], refused


def test_same_line_blocks_of_DIFFERENT_kinds_resolve_to_their_own_owners():
    """Research's stage-1 BLOCKING 2. The same-line join is by (line, symtable's block name) and consumes each
    key's list in source order; the control shipped with it was two GENEXPRS, both arms the same kind. If AST
    traversal order and symtable's child order ever diverged, the plausible cause is a PER-KIND difference in how
    each side enumerates, and a same-kind pair cannot see it. So: mixed kinds on one line, each binding a
    different name, plus a NESTED same-kind pair where one block is inside the other rather than beside it —
    the two shapes where an order assumption would break differently."""
    mixed = sr.Resolver("def f(xs):\n    return (lambda aaa: aaa)(1), list(bbb for bbb in xs)\n")
    lam = [n for n in ast.walk(mixed.tree) if isinstance(n, ast.Lambda)][0]
    gen = [n for n in ast.walk(mixed.tree) if isinstance(n, ast.GeneratorExp)][0]
    assert sorted(x for x in mixed.block_of(lam.body).get_identifiers() if not x.startswith(".")) == ["aaa"]
    assert sorted(x for x in mixed.block_of(gen.elt).get_identifiers() if not x.startswith(".")) == ["bbb"]
    nested = sr.Resolver("def f(xs):\n    return list(ooo for ooo in (iii for iii in xs))\n")
    gens = [n for n in ast.walk(nested.tree) if isinstance(n, ast.GeneratorExp)]
    # ROUND 12, S2b-1: this compared the two owners as a SET — `{ooo, iii}` — and a SWAP produces the identical set,
    # so it passed while the resolver handed each genexp the other's table, on every version, from the day it was
    # written. The property is a MAPPING, and the assertion is now per element.
    for g in gens:
        own = g.generators[0].target.id
        held = {x for x in nested.block_of(g.elt).get_identifiers() if not x.startswith(".")}
        assert own in held and not (held & ({"ooo", "iii"} - {own})), \
            f"the genexp binding {own!r} resolves inside a block holding {sorted(held)}"
    # and the property the join exists for, across kinds: a site read in the lambda is the module's, a site
    # REBOUND as the lambda's parameter is not
    r = sr.Resolver("S = 1\ndef f(xs):\n    return (lambda q: S.fire(q)), list(S for S in xs)\n")
    inner = [n for n in ast.walk(r.tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "fire"][0]
    assert r.refers_to_module_binding(inner, "S") is True
    r2 = sr.Resolver("S = 1\ndef f(xs):\n    return (lambda S: S.fire(1)), 2\n")
    inner2 = [n for n in ast.walk(r2.tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "fire"][0]
    assert r2.refers_to_module_binding(inner2, "S") is False


# (label, source, does `S` at the single `S.fire(...)` resolve to the MODULE binding?)
COMPREHENSIONS = [
    ("module-level listcomp rebinding S",      "S = 1\nxs = [S.fire(1) for S in (1,2)]\n", False),
    ("module-level genexpr rebinding S",       "S = 1\nxs = list(S.fire(1) for S in (1,2))\n", False),
    ("listcomp in a function rebinding S",     "S = 1\ndef f(xs):\n    return [S.fire(1) for S in xs]\n", False),
    ("dictcomp rebinding S (its value)",       "S = 1\nxs = {1: S.fire(1) for S in (1,)}\n", False),
    ("setcomp rebinding S",                    "S = 1\ndef f(xs):\n    return {S.fire(1) for S in xs}\n", False),
    ("a nested comprehension's INNER target",  "S = 1\nxs = [[S.fire(1) for S in row] for row in (1,)]\n", False),
    ("a nested comprehension's OUTER target",  "S = 1\nxs = [[S.fire(1) for q in row] for S in (1,)]\n", False),
    ("a genexpr nested in a listcomp",         "S = 1\nxs = [list(S.fire(1) for S in row) for row in (1,)]\n", False),
    ("a SECOND generator's iterable",          "S = 1\nxs = [q for S in (1,) for q in S.fire((2,))]\n", False),
    ("an `if` clause of the comprehension",    "S = 1\nxs = [q for S in (1,) if S.fire(q)]\n", False),
    # the must-NOT-shadow half: the first iterable is the enclosing scope's, and an unrebound name is the module's
    ("the FIRST iterable (enclosing scope)",   "S = 1\nxs = [q for S in S.fire((1,2))]\n", True),
    ("a listcomp that does NOT rebind S",      "S = 1\nxs = [S.fire(q) for q in (1,2)]\n", True),
    ("a function listcomp not rebinding S",    "S = 1\ndef f(xs):\n    return [S.fire(q) for q in xs]\n", True),
    ("nested, neither rebinding S",            "S = 1\nxs = [[S.fire(1) for q in row] for row in (1,)]\n", True),
]


@pytest.mark.parametrize("label,src,outward", COMPREHENSIONS, ids=[c[0].replace(" ", "-") for c in COMPREHENSIONS])
def test_a_comprehension_target_shadows_on_every_interpreter(label, src, outward):
    """Research's stage-2 BLOCKING, and the reason it is worth a matrix of its own: the answer used to DEPEND ON
    THE INTERPRETER. PEP 709 inlines list/set/dict comprehensions from 3.12, so they have a symtable block on
    3.10 and 3.11 and none on 3.12+. With the block, symtable answers; without it the nodes are owned by the
    enclosing block, and at module level `refers_to_module_binding` short-circuits to True — so a `.fire()` on a
    name the comprehension REBINDS read as the module's site on 3.12 and not on 3.10. Both consumers take that at
    face value: the scan computes `bound` from it and the transform decides WHAT TO REWRITE from it.

    PEP 709 removed the BLOCK, not the SCOPING, and the interpreter says so itself — the control below runs it.
    CI runs 3.10, 3.11, 3.12 and 3.13, so this matrix asserting the SAME answers on all four is the cross-version
    control: on two of them it exercises the symtable path and on two the inlined path."""
    r = sr.Resolver(src, f"<{label}>")
    assert r.refers_to_module_binding(_marked_call(r), "S") is outward, label


def test_the_interpreter_itself_agrees_that_a_comprehension_target_does_not_leak():
    """The premise the matrix above rests on, EXECUTED rather than cited — on whichever interpreter is running."""
    S = "the module binding"
    seen = [S for S in ("a", "b")]                                  # noqa: F841 — the point is the rebinding
    assert seen == ["a", "b"] and S == "the module binding"
    import symtable as _st
    inlined = [c.get_name() for c in _st.symtable("[x for x in y]", "<p>", "exec").get_children()] == []
    assert inlined is (sys.version_info >= (3, 12)), (sys.version_info[:2], inlined)


def test_the_comprehension_matrix_exercises_both_answers_and_both_regimes():
    """A matrix of all-False rows would pass a resolver that answers False inside any comprehension — which would
    break the first iterable and every unrebound read. Both halves are present and counted."""
    answers = {c[2] for c in COMPREHENSIONS}
    assert answers == {True, False}
    assert sum(1 for c in COMPREHENSIONS if not c[2]) >= 8 and sum(1 for c in COMPREHENSIONS if c[2]) >= 4
    kinds = " ".join(c[0] for c in COMPREHENSIONS)
    for kind in ("listcomp", "genexpr", "dictcomp", "setcomp", "nested", "FIRST iterable"):
        assert kind in kinds, kind


def test_a_module_level_rebinding_of_a_site_is_refused_including_a_walrus_in_a_comprehension():
    """Research's stage-2 held probe, answered before the pin rather than after it. PEP 572 binds a walrus in the
    ENCLOSING scope ON PURPOSE, so at module level `[(S := q) for q in ...]` genuinely reassigns the site's name —
    and every static reading still says "S is the module binding", which is TRUE OF THE NAME and false of the
    object. The refusal used to cover only `global S` with an assignment inside a function; it now covers any
    module-level rebinding, which is the property that was actually meant."""
    decl = "from .census import declare_site\nS = declare_site('t')\n"
    # The expected message is named per row, because the WALRUS row is answered by a different reading on each
    # side of PEP 709: on 3.12+ the comprehension is inlined and its store is in the module's own code object
    # (rule A counts two); on 3.10/3.11 it is a separate code object that binds the ENCLOSING scope, which the
    # interpreter's module-level reading cannot see at all, and symtable answers it instead (rule C).
    inlined = sys.version_info >= (3, 12)
    for label, src, expected in [
        ("a walrus inside a comprehension", decl + "xs = [(S := q) for q in (1, 2)]\n",
         "bound 2 times in the module's own code" if inlined
         else "assigns the MODULE-level name"),
        ("a plain second assignment",       decl + "S = object()\n", "bound 2 times"),
        ("a module-level for target",       decl + "for S in (1, 2):\n    pass\n", "bound 2 times"),
        ("a module-level with-as",          decl + "import contextlib\nwith contextlib.nullcontext() as S:\n    pass\n",
         "bound 2 times"),
    ]:
        r = sr.Resolver(src, f"<{label}>")
        with pytest.raises(sr.UnresolvableScope, match=expected):
            r.refuse_site_rebindings(r.site_names())
    # the controls: a comprehension's own TARGET is comprehension-local and binds nothing at module level, and a
    # function-local name of the same spelling is a shadow, not a rebinding — neither may be refused
    for label, src in {
        "a comprehension's for target":    decl + "xs = [S for S in (1, 2)]\n",
        "a function-local shadow":         decl + "def f():\n    S = object()\n    return S\n",
        "a nested function's parameter":   decl + "def f(S):\n    return S\n",
        "the declaration alone":           decl,
    }.items():
        r = sr.Resolver(src, f"<{label}>")
        r.refuse_site_rebindings(r.site_names())
    # and the runtime confirms the premise the refusal rests on
    ns = {"declare_site": lambda i: f"<site {i}>"}
    exec("S = declare_site('t')\nxs = [(S := q) for q in (1, 2)]\n", ns)
    assert ns["S"] == 2, "PEP 572 binds the walrus in the enclosing scope; the site object is replaced"


# (label, the listcomp form, the genexpr form, the expected answer) — the SAME question in both spellings
REGIME_PAIRS = [
    ("the first iterable",        "S = 1\nxs = [q for S in S.fire((1,2))]\n",          "S = 1\nxs = list(q for S in S.fire((1,2)))\n", True),
    ("the element, rebound",      "S = 1\nxs = [S.fire(1) for S in (1,2)]\n",          "S = 1\nxs = list(S.fire(1) for S in (1,2))\n", False),
    ("a second iterable",         "S = 1\nxs = [q for S in (1,) for q in S.fire((2,))]\n", "S = 1\nxs = list(q for S in (1,) for q in S.fire((2,)))\n", False),
    ("an `if` clause",            "S = 1\nxs = [q for S in (1,) if S.fire(q)]\n",      "S = 1\nxs = list(q for S in (1,) if S.fire(q))\n", False),
    ("the element, NOT rebound",  "S = 1\nxs = [S.fire(q) for q in (1,)]\n",           "S = 1\nxs = list(S.fire(q) for q in (1,))\n", True),
    ("inside a function",         "S = 1\ndef f():\n    return [q for S in S.fire((1,))]\n", "S = 1\ndef f():\n    return list(q for S in S.fire((1,)))\n", True),
]


@pytest.mark.parametrize("label,listcomp,genexpr,outward", REGIME_PAIRS, ids=[p[0].replace(" ", "-") for p in REGIME_PAIRS])
def test_both_scope_regimes_agree_and_a_genexpr_proves_the_other_one_locally(label, listcomp, genexpr, outward):
    """THE TECHNIQUE, and it is the reusable part: a GENERATOR EXPRESSION keeps its own symtable block on EVERY
    version, so on 3.12 it exercises exactly the branch a LIST COMPREHENSION takes on 3.10 and 3.11. Pairing the
    two spellings of one question therefore tests BOTH regimes on ONE interpreter — a local cross-version control,
    where the version matrix alone can only be checked by CI.

    It is not hypothetical: the first version of this fix handled the first-iterable rule on the inlined path
    only, every local test passed, and CI's 3.10 and 3.11 jobs went red on precisely the row below that asserts
    it. The pair would have caught it here."""
    got = [sr.Resolver(src, f"<{label}>") for src in (listcomp, genexpr)]
    answers = [r.refers_to_module_binding(_marked_call(r), "S") for r in got]
    assert answers == [outward, outward], (label, answers)


def test_the_regime_pairs_really_do_take_different_paths():
    """The control for the technique itself: if a genexpr and a listcomp were handled identically on this
    interpreter, the pairs above would prove nothing. On 3.12 the listcomp has NO block and the genexpr has one;
    before 3.12 both have one, and the pairs still assert the shared rules."""
    import symtable as _st
    lc = [c.get_name() for c in _st.symtable("[x for x in y]", "<p>", "exec").get_children()]
    ge = [c.get_name() for c in _st.symtable("(x for x in y)", "<p>", "exec").get_children()]
    assert ge == ["genexpr"], ge
    if sys.version_info >= (3, 12):
        assert lc == [], lc                      # inlined: the pairs exercise two DIFFERENT paths here
    else:
        assert lc == ["listcomp"], lc            # both blocked: the pairs still assert the same answers


def test_the_site_question_refuses_until_the_rebinding_guarantee_is_established():
    """Research's stage-1 note on the stage-2 fix, made a MECHANISM rather than a docstring sentence. There are
    two questions here and they are not the same one: `refers_to_module_binding` answers whether the NAME
    resolves to the module binding, and both consumers need whether the receiver IS THE DECLARED SITE OBJECT.
    They coincide only while the module name is bound exactly once, which `refuse_site_rebindings` establishes —
    in a different function. A guarantee held in the CALL ORDER is one a later caller or a refactor can drop
    with nothing failing, because every existing test happens to run both. So the site question refuses until
    the guarantee exists, and the name question stays available under its honest name."""
    src = "from .census import declare_site\nS = declare_site('t')\nr = S.fire(1)\n"
    r = sr.Resolver(src)
    call = _marked_call(r)
    assert r.refers_to_module_binding(call, "S") is True          # the NAME question: answerable immediately
    with pytest.raises(sr.UnresolvableScope, match="before `refuse_site_rebindings`"):
        r.refers_to_declared_site(call, "S")                      # the SITE question: refused until established
    r.refuse_site_rebindings(r.site_names())
    assert r.refers_to_declared_site(call, "S") is True           # and answerable after
    # a name the guarantee was never asked about stays refused, even once OTHERS are cleared
    with pytest.raises(sr.UnresolvableScope, match="before `refuse_site_rebindings`"):
        r.refers_to_declared_site(call, "some_other_name")
    # AND BOTH CONSUMERS ASK THE SITE QUESTION, NOT THE NAME ONE — checked BY PROPERTY, not by banning the
    # name question's spelling. This was `assert "refers_to_module_binding(" not in text`, a blanket ban on the
    # API anywhere in either module, and round 9 made it refuse CORRECT work: `_is_census_alias` asks whether a
    # name is the MODULE-LEVEL CENSUS IMPORT, which is genuinely the name question — the census alias is not a
    # site, so `refers_to_declared_site` (which requires membership in `declared` and the rebinding guarantee)
    # is the wrong question for it. A gate narrower than its subject either refuses correct work loudly or
    # accepts wrong work silently; this one refused loudly, which is the cheap direction, and the fix is to
    # state the real rule rather than to add an exemption for a string.
    #
    # THE REAL RULE: a function that decides something about A DECLARED SITE (it consults `self.declared`) must
    # reach the resolver through `refers_to_declared_site`. A function that asks the name question must not be
    # deciding about a site — so it must not consult `self.declared`.
    # ROUND 9, SECOND FORM. The first form of this property check was defeated three ways by research's
    # stage-2 mutants, and the worst one let the ROUND-7 DEFECT ITSELF walk back in:
    #
    #   1. `def _m6(self, node, name): return name in self.declared` — decides site-hood by MEMBERSHIP and
    #      calls no resolver at all. The first form's second assertion was GUARDED by "…and it calls one of
    #      the two resolver methods", so a function that asks NO question and decides anyway never entered
    #      the `if`. That is precisely what round 7's F4a was. The guard is gone: consulting `declared` now
    #      obliges a function to ask the site question OR to use the membership only to REFUSE.
    #   2. `f = self.resolver.refers_to_module_binding` then `f(node, name)` — bound to a local, the call's
    #      func is an `ast.Name`, so collecting `ast.Call` attrs missed it. Attribute READS are collected now.
    #   3. a module- or class-level `lambda` — the walk took FunctionDef/AsyncFunctionDef only.
    #
    # WHAT THIS GATE CANNOT SEE, STATED SO THE ATTACK LIST IS NOT MISTAKEN FOR THE SPECIFICATION. It is a
    # STATIC reading, so it cannot distinguish a pure attribute read from a side-effecting @property:
    #
    #     if any(n in self.declared and self.bump for n in node.names):   # `bump` is a property that mutates
    #         raise Refused(...)                                          # and returns falsy
    #     return node                                                     # -> affirms by fall-through
    #
    # MEASURED, not assumed: the getter executes once per element (three, for three names) while the guard
    # never fires, and this gate reads no method call and exempts it. It is NOT closed, deliberately. Banning
    # attribute reads in the guard's test would ban `self.declared`, which is what the guard is FOR, and no
    # static check of any shape can tell a pure read from a side-effecting one without executing the code. The
    # instrument has reached the boundary of its own class; the honest move is to name the boundary rather than
    # to keep appending shapes until the list reads as a definition. The threat model is a future developer
    # reintroducing round 7's F4a by accident, and nobody writes a side-effecting property into a refusal guard
    # by accident. (Research found this one and recommended leaving it; the reasoning above is theirs.)
    #
    # THE EXEMPTION IS A PROPERTY, NOT A NAME LIST. `visit_Global` and `visit_Nonlocal` legitimately consult
    # `declared` and call no resolver: they REFUSE on a hit, which is the fail-closed direction, and a wrong
    # answer there over-refuses loudly. That is checkable — every `if` whose test reads `self.declared` has a
    # body that is exactly a `raise` — so it is checked, rather than the functions being named.
    def _declared_reads(node):
        """`self.declared` READ, in a Load context. `__init__`'s `self.declared = declared` is a WRITE and
        is not a consultation — counting it made the gate accuse the constructor of deciding site-hood."""
        return [n for n in ast.walk(node)
                if isinstance(n, ast.Attribute) and n.attr == "declared" and isinstance(n.ctx, ast.Load)]

    for mod in ("installed_sites.py", "inv7_uninstrument.py"):
        text = (EVIDENCE / mod).read_text()
        assert "refers_to_declared_site(" in text, mod
        tree = ast.parse(text)
        units = [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))]
        checked = 0
        for fn in units:
            where = f"{mod}:{getattr(fn, 'name', '<lambda>')}:{fn.lineno}"
            # every attribute this unit READS or CALLS — a method bound to a local is still named here
            names = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
            reads = _declared_reads(fn)
            if not reads:
                continue
            checked += 1
            # THE FAIL-CLOSED EXEMPTION, AND ITS FIRST FORM WAS DEFEATED. That form was "every read of
            # `declared` sits in the test of an `if` whose body is exactly a raise", and research inverted the
            # guard clause straight through it:
            #
            #     def visit_Evil(self, node):
            #         if not any(n in self.declared for n in node.names):
            #             raise Refused(...)          # membership FALSE -> refuse
            #         self.sites += 1                 # membership TRUE  -> act on it
            #         return None
            #
            # Every read is inside a raise-guard, so it was exempt — and it decides the site question BY
            # FALL-THROUGH. F4a with a `not` in front of it, and a guard clause is ordinary Python.
            #
            # The invariant is NOT about the shape of one `if`. It is that CONSULTING `declared` CAN ONLY EVER
            # REFUSE, NEVER AFFIRM — this function refuses, or it leaves the tree alone. So the whole body is
            # checked: every statement that is not a raise-guard must be a bare `return <parameter>`.
            # `visit_Global` and `visit_Nonlocal` are refuse-or-passthrough and satisfy it; `visit_Evil` does
            # not. Disqualifying `ast.Not` inside the test was considered and REJECTED — that is a narrow
            # matcher, and `if all(n not in self.declared ...)` walks past it, which is the same defect as the
            # packaging gate that matched one spelling.
            params = {a.arg for a in list(getattr(fn.args, "posonlyargs", [])) + fn.args.args
                      + fn.args.kwonlyargs} if hasattr(fn, "args") else set()
            guards, other = [], []
            for stmt in (fn.body if isinstance(fn.body, list) else [fn.body]):
                # A REFUSAL GUARD'S TEST MAY NOT CALL A METHOD. My own attack battery left one survivor:
                #     if any(n in self.declared and self._bump() for n in node.names): raise Refused(...)
                # which refuses only when `_bump()` is truthy, so on the falsy path it has ACTED on membership
                # and returned the node — affirming through a side effect in the test. Banning method calls in
                # the guard's test closes the construct rather than the one spelling: `any(...)`/`all(...)`
                # are `ast.Name` calls and stay legal, `self.anything()` does not.
                calls_a_method = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                                     for c in ast.walk(stmt.test)) if isinstance(stmt, ast.If) else False
                if isinstance(stmt, ast.If) and len(stmt.body) == 1 and isinstance(stmt.body[0], ast.Raise) \
                        and not stmt.orelse and not calls_a_method:
                    guards.append(stmt)
                else:
                    other.append(stmt)
            refusing = [r for g in guards for r in _declared_reads(g.test)]
            passthrough = all(isinstance(s, ast.Return) and isinstance(s.value, ast.Name)
                              and s.value.id in params for s in other)
            only_refuses = ({id(n) for n in reads} == {id(n) for n in refusing}) and bool(guards) and passthrough
            assert "refers_to_declared_site" in names or only_refuses, (
                f"{where} consults `declared` without asking the SITE question, and does not use the "
                f"membership solely to refuse. That is round 7's F4a exactly: membership is not a scope "
                f"answer, and deciding on it silently rewrites or accepts what it should have resolved")
            assert "refers_to_module_binding" not in names or "refers_to_declared_site" in names, (
                f"{where} consults `declared` AND reaches the NAME question — the site question answered by "
                f"the wrong one, which is what this gate exists to refuse")
        # THE VACANCY CHECK, WITH ITS EXPECTATION DERIVED RATHER THAN ASSUMED. A first form asserted every
        # module has a unit consulting `declared`, and `installed_sites.py` REFUSED it correctly: that module
        # is not class-based — it holds a LOCAL `declared` list and asks `r.refers_to_declared_site(...)`
        # directly, so there is no `self.declared` to consult. The expectation therefore comes from the
        # source: a module that mentions `self.declared` must have at least one unit examined here, and one
        # that does not is covered by the `refers_to_declared_site(` assertion above. Deriving it means
        # a module that GAINS the attribute is covered without anyone remembering to add it.
        if "self.declared" in text:
            assert checked, (
                f"{mod} mentions `self.declared` but this gate examined no unit that reads it — the gate has "
                f"gone blind to the module it is for")


# ---------------------------------------------------------------------------------------------------------------
# Round 8e — research's stage-2 finding: SIX module-level binding spellings were accepted, because the refusal's
# only reading was an AST walk over `ast.Name` in a `Store` context and none of the six is one. The matrix below
# is the binding grammar of a MODULE SCOPE, both halves, and it is the negative space of the `GRAMMAR` table
# above: there the question was "which binding does this name see", here it is "is the declared site still the
# object this name denotes". Every row is a module whose first two lines declare a site called `S`.
# ---------------------------------------------------------------------------------------------------------------
DECL = "from .census import declare_site\nS = declare_site('t')\n"

# (label, the source after the declaration, must the refusal fire?)
REBINDING_MATRIX = [
    # --- the six research found. None is an `ast.Name` in a `Store` context; all six replace or remove the site.
    ("import os as S",                   "import os as S\n", True),
    ("from os import path as S",         "from os import path as S\n", True),
    ("except Exception as S",            "try:\n    pass\nexcept Exception as S:\n    pass\n", True),
    ("del S",                            "del S\n", True),
    ("def S()",                          "def S():\n    pass\n", True),
    ("class S",                          "class S:\n    pass\n", True),
    # --- their neighbours in the same grammar, none of them named by anyone
    ("async def S()",                    "async def S():\n    pass\n", True),
    ("import os as S inside a try",      "try:\n    import os as S\nexcept ImportError:\n    pass\n", True),
    ("a match capture",                  "match 1:\n    case S:\n        pass\n", True),
    ("a match as-pattern",               "match 1:\n    case int() as S:\n        pass\n", True),
    # --- the forms the AST walk already saw, which must keep being refused
    ("a plain second assignment",        "S = object()\n", True),
    ("an augmented assignment",          "S += 1\n", True),
    ("an annotated assignment",          "S: int = 1\n", True),
    ("a module-level for target",        "for S in (1, 2):\n    pass\n", True),
    ("a module-level with-as",           "import contextlib\nwith contextlib.nullcontext() as S:\n    pass\n", True),
    ("tuple unpacking",                  "(S, y) = (1, 2)\n", True),
    ("starred unpacking",                "[*S, y] = (1, 2, 3)\n", True),
    ("a module-level walrus",            "if (S := 1):\n    pass\n", True),
    # --- bound from INSIDE a nested code object, at the module scope: the half rule A cannot see
    ("a walrus in a listcomp",           "xs = [q for q in (1, 2) if (S := q)]\n", True),
    ("a walrus in a genexpr",            "xs = list(q for q in (1, 2) if (S := q))\n", True),
    ("`global S` assigned in a function", "def f():\n    global S\n    S = 1\n", True),
    ("`global S` deleted in a function",  "def f():\n    global S\n    del S\n", True),
    ("`global S` in a class body",        "class K:\n    global S\n    S = 1\n", True),
    ("`global S` two scopes down",        "def outer():\n    def inner():\n        global S\n        S = 1\n"
                                          "    return inner\n", True),
    # --- ROUND 8'S FINDING. symtable reports these two `is_imported` and NOT `is_assigned`, so rule C's old
    # --- predicate pair never fired and the site was replaced in silence. They are the ONLY two rows on which
    # --- the superseded pair and the shipped reading disagree, which
    # --- `test_the_superseded_predicate_pair_misses_exactly_the_nested_imports` asserts in both directions.
    ("a nested `import x as S` under `global`",
                                         "def f():\n    global S\n    import os as S\n", True),
    ("a nested `from x import y as S` under `global`",
                                         "def f():\n    global S\n    from os import path as S\n", True),
    # --- the other half: an over-strict refusal is a refusal of CORRECT code, and it is the half a matrix of
    # --- all-True rows would never catch. None of these replaces the site object.
    ("the declaration alone",            "", False),
    ("a listcomp target",                "xs = [S for S in (1, 2)]\n", False),
    ("a genexpr target",                 "xs = list(S for S in (1, 2))\n", False),
    ("a setcomp target",                 "a = {S for S in (1, 2)}\n", False),
    ("a dictcomp target",                "b = {S: S for S in (1, 2)}\n", False),
    ("a nested comprehension target",    "b = [[S for S in r] for r in ((1,),)]\n", False),
    ("a function-local shadow",          "def f():\n    S = 1\n    return S\n", False),
    ("a function parameter",             "def f(S=None):\n    return S\n", False),
    ("a lambda parameter",               "f = lambda S: S\n", False),
    ("a class-body attribute",           "class K:\n    S = 1\n", False),
    ("except-as inside a function",      "def f():\n    try:\n        pass\n    except Exception as S:\n"
                                         "        pass\n", False),
    ("a for target inside a function",   "def f():\n    for S in (1, 2):\n        pass\n", False),
    ("`global S` READ in a function",    "def f():\n    global S\n    return S\n", False),
    ("an ordinary module-level use",     "with S.consult():\n    pass\n", False),
    ("an ordinary use in a function",    "def f():\n    with S.consult():\n        return 1\n", False),
    # --- research's Q2: counting binding OPERATIONS cannot tell "bound twice in sequence" from "bound once in
    # --- two mutually exclusive branches". All three below count more than one and are REFUSED, and the
    # --- decision is recorded here rather than inherited from the counting: a static reading cannot tell a
    # --- dead branch from a live one unless the condition is a literal the compiler folds, and a site declared
    # --- ONCE and UNCONDITIONALLY is the premise of the scan this refusal protects. The `TYPE_CHECKING` row is
    # --- the sharpest — that branch never executes, so the refusal is false IN FACT — and the trade is taken
    # --- knowingly: it needs a site name to collide with a type-checking alias, and no module in the tree
    # --- does that. `if False:` sits two rows below it, ACCEPTED, because the compiler folds it away; the two
    # --- are adjacent so the asymmetry explains itself where a reader meets it.
    ("a try/except import fallback",     "try:\n    import os as S\nexcept ImportError:\n    import sys as S\n",
     True),
    ("a site declared in both branches", "flag = True\nif flag:\n    S = declare_site('a')\nelse:\n"
                                         "    S = declare_site('b')\n", True),
    ("an `if TYPE_CHECKING` import",     "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
                                         "    import os as S\n", True),
    ("a dead `if False` branch",         "if False:\n    S = 1\n", False),
    ("a bare annotation",                "S: int\n", False),
]


def _refusal(module, src):
    """The refusal message for one matrix row, or None if the row was accepted."""
    r = module.Resolver(DECL + src, "<matrix>")
    try:
        r.refuse_site_rebindings(r.site_names())
        return None
    except module.UnresolvableScope as e:
        return str(e)


def test_every_module_level_binding_form_is_refused_and_no_shadow_is():
    """The whole matrix at once, reporting EVERY disagreement rather than the first — a row-per-run matrix hides
    how much of the grammar a regression takes with it. Both halves are asserted because an always-refusing
    resolver would pass the first half and refuse the entire product tree."""
    wrong = []
    for label, src, must_refuse in REBINDING_MATRIX:
        got = _refusal(sr, src)
        if (got is not None) != must_refuse:
            wrong.append(f"{label}: expected {'a refusal' if must_refuse else 'acceptance'}, got {got!r}")
    assert not wrong, "\n".join(wrong)


def test_the_rebinding_matrix_covers_both_answers_and_the_six_forms_by_name():
    """The table's own shape, so a row silently deleted from either half is visible."""
    assert len(REBINDING_MATRIX) == 46
    assert len({row[0] for row in REBINDING_MATRIX}) == 46, "labels are the ids; they must be distinct"
    refused = [row for row in REBINDING_MATRIX if row[2]]
    assert len(refused) == 29 and len(REBINDING_MATRIX) - len(refused) == 17
    labels = " ".join(row[0] for row in REBINDING_MATRIX)
    for form in ("import os as S", "from os import path as S", "except Exception as S", "del S", "def S()",
                 "class S", "a walrus in a genexpr", "`global S` READ in a function", "a listcomp target",
                 "an `if TYPE_CHECKING` import", "a dead `if False` branch", "a bare annotation"):
        assert form in labels, form


def test_the_interpreter_confirms_each_spelling_really_does_replace_the_site():
    """The premise under the first half, EXECUTED. A refusal of a form that does not actually replace the object
    would be a refusal of correct code, so the six are run and the name is read afterwards: in every case `S` is
    no longer the site the declaration returned. This is the 'true of the name, false of the object' distinction
    the whole refusal exists to keep, and nothing here is derived from reading the grammar."""
    site = object()
    for label, src, expect_gone in [
        ("import os as S",           "import os as S\n", True),
        ("from os import path as S", "from os import path as S\n", True),
        ("except Exception as S",    "try:\n    raise ValueError()\nexcept Exception as S:\n    pass\n", True),
        ("del S",                    "del S\n", True),
        ("def S()",                  "def S():\n    pass\n", True),
        ("class S",                  "class S:\n    pass\n", True),
        ("a walrus in a genexpr",    "xs = list(q for q in (1, 2) if (S := q))\n", True),
        ("`global S` in a function", "def f():\n    global S\n    S = 1\nf()\n", True),
        ("a listcomp target",        "xs = [S for S in (1, 2)]\n", False),
        ("a function-local shadow",  "def f():\n    S = 1\n    return S\nf()\n", False),
    ]:
        ns = {"declare_site": lambda i: site}
        exec("S = declare_site('t')\n" + src, ns)
        still = ns.get("S", None) is site
        assert still is (not expect_gone), f"{label}: after execution S is {'still' if still else 'no longer'} the site"


def _mutant(old, new):
    """The resolver with one rule disabled, loaded as its own module. A rule that no row depends on is a rule
    that can be deleted without anyone noticing, which is the dead-check taxonomy's UNFAILABLE entry."""
    src = (EVIDENCE / "scope_resolution.py").read_text()
    assert src.count(old) == 1, f"the mutant's anchor {old!r} matched {src.count(old)} times"
    path = pathlib.Path(__import__("tempfile").mkdtemp()) / "scope_resolution_mutant.py"
    path.write_text(src.replace(old, new))
    return _load(f"scope_resolution_mutant_{abs(hash(old))}", path)


RULE_A = ("            if len(executed) > 1:", "            if False:")
RULE_C = ("            if nested:", "            if False:")


def test_both_readings_are_load_bearing_and_neither_over_refuses():
    """Disable one rule in the SOURCE and the matrix must redden — the reviewer's next move, made first. Two
    readings remain, both of them the language's own, and each owns part of the grammar:

      A  the module's own COMPILED CODE OBJECT binds the name more than once. Total over syntax by
         construction. Sole catcher of every rebinding performed by this scope, whatever its spelling.
      C  a NESTED CODE OBJECT binds the name with STORE_GLOBAL or DELETE_GLOBAL. The interpreter's reading
         again, so it is total over syntax for the same reason A is. Sole catcher of `global` from a
         function, a class body or two scopes down, of a nested import targeting the module name, and — on
         3.10/3.11 only — of a comprehension's walrus, which binds the enclosing scope with no `global`
         statement in the source. From 3.12 PEP 709 inlines a LIST comprehension into the module, so that row
         changes hands to rule A while the GENERATOR-expression spelling stays with C on every version; the
         two spellings sit adjacent in the matrix and `test_every_refused_row_names_the_rule_that_caught_it`
         is what would notice a row moving.

    A third reading — refuse when the two disagree — was written here and deleted; the paragraph in
    `scope_resolution.py` says why, and `test_no_reading_of_this_module_is_a_hand_enumeration` keeps the walk
    it cross-checked from coming back. Each mutant is also asked whether it refuses CORRECT code, because a
    mutant that reddens the acceptance half proves nothing about the rule it disabled."""
    for rule, (old, new_), sole in [("A", RULE_A, "a plain second assignment"),
                                    ("C", RULE_C, "`global S` assigned in a function")]:
        mutant = _mutant(old, new_)
        survivors = [row[0] for row in REBINDING_MATRIX if row[2] and _refusal(mutant, row[1]) is None]
        assert sole in survivors, (rule, sole, survivors)
        wrongly = [row[0] for row in REBINDING_MATRIX if not row[2] and _refusal(mutant, row[1]) is not None]
        assert not wrongly, f"rule {rule}'s mutant refuses correct code, so the redness is not the rule's: {wrongly}"


def test_the_deleted_third_reading_would_refuse_correct_code():
    """The deletion, kept honest. Round 8e first ADDED a rule that refused when the interpreter's reading and an
    AST walk disagreed about where a name is bound, and demoted it to a tripwire when its own mutant showed it
    caught nothing the other two did. Running two rows research proposed as must-accept showed what it actually
    fires on: a dead branch the compiler folds away, and a bare annotation whose target carries a `Store`
    context and binds nothing. Both are correct code. This test rebuilds that rule and asserts it refuses them,
    so the reason for the deletion is a RESULT and not a remark in a docstring.

    THE LIMIT, STATED SO A LATER READER DOES NOT OVERREAD IT (research's note): the rule is DELETED, so this
    asserts a property of a REBUILD written here, not of any code that ever shipped. It cannot be bound to what
    D was, because what D was is only in the history. What it can do — and does, below — is show that the two
    rows are refused by the rebuilt reading ALONE: disabling either surviving rule leaves them accepted, so the
    refusal being demonstrated is the rebuilt one's and not a side effect of A or C."""
    src = (EVIDENCE / "scope_resolution.py").read_text()
    anchor = "            if len(executed) > 1:"
    assert src.count(anchor) == 1
    restored = src.replace(anchor, """            walked = []

            def _walk(node, out):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                        continue
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store) and child.id == n:
                        out.append(child.lineno)
                    _walk(child, out)
            _walk(self.tree, walked)
            if sorted(set(walked)) != executed_lines:
                raise UnresolvableScope(f"site {n!r}: the two readings disagree")
            if len(executed) > 1:""")
    tmp = pathlib.Path(__import__("tempfile").mkdtemp()) / "with_d.py"
    tmp.write_text(restored)
    with_d = _load("scope_resolution_with_deleted_rule", tmp)
    for label in ("a dead `if False` branch", "a bare annotation"):
        body = next(row[1] for row in REBINDING_MATRIX if row[0] == label)
        assert _refusal(sr, body) is None, f"{label} must be accepted by the shipped resolver"
        message = _refusal(with_d, body)
        assert message is not None and "readings disagree" in message, \
            f"the deleted rule no longer refuses {label}, so the stated reason for deleting it has gone stale"
        # and the refusal is the rebuilt reading's alone: neither surviving rule refuses these rows either way
        for rule, pair in (("A", RULE_A), ("C", RULE_C)):
            assert _refusal(_mutant(*pair), body) is None, (
                f"{label} is refused with rule {rule} disabled, so the rebuilt rule is not what refuses it and "
                f"this test is measuring something else")


_AST_CONSULTATION_PROBE = r"""
# Counts every consultation of the AST during `refuse_site_rebindings`, for the shipped resolver and for two
# mutants that reinstate an enumeration. The counters are installed BEFORE any of the three modules is imported,
# so a module-level `from ast import walk as _w` binds to a counter too — which a sabotage-after-import control
# would miss. Runs as a SUBPROCESS: it monkeypatches the stdlib `ast` module, and doing that in the session would
# be fixture state living outside the thing under test, which is this round's other recurring defect.
import ast, importlib.util, pathlib, sys, tempfile

CALLS = {"n": 0}
REAL_STORE = ast.Store

class _StoreMeta(type):
    def __instancecheck__(cls, obj):
        CALLS["n"] += 1
        return isinstance(obj, REAL_STORE)

for _name in ("walk", "iter_child_nodes", "iter_fields", "dump"):
    def _wrapper(*a, _real=getattr(ast, _name), **k):
        CALLS["n"] += 1
        return _real(*a, **k)
    setattr(ast, _name, _wrapper)
ast.Store = _StoreMeta("Store", (), {})

def load(name, text):
    d = pathlib.Path(tempfile.mkdtemp()); f = d / (name + ".py"); f.write_text(text)
    sp = importlib.util.spec_from_file_location(name, f); m = importlib.util.module_from_spec(sp)
    sys.modules[name] = m; sp.loader.exec_module(m); return m

SRC = pathlib.Path(sys.argv[1]).read_text()
ANCHOR = "        declared_here = self.site_names()"
assert SRC.count(ANCHOR) == 1, "the probe's anchor moved; the mutants are not being injected"
ALIASED = SRC.replace(ANCHOR, "        from ast import walk as _w, Store as _St\n"
                              "        _back = [n.lineno for n in _w(self.tree)\n"
                              "                 if n.__class__.__name__ == 'Name' and isinstance(n.ctx, _St)]\n" + ANCHOR)
TOPLEVEL = SRC.replace("import symtable\n", "import symtable\nfrom ast import walk as _topwalk\n", 1) \
              .replace(ANCHOR, "        _back = [n for n in _topwalk(self.tree)]\n" + ANCHOR)

DECL = "from .census import declare_site\nS = declare_site('t')\n"
ROWS = [("import os as S\n", True), ("del S\n", True), ("S = object()\n", True),
        ("def f():\n    global S\n    S = 1\n", True), ("xs = [S for S in (1, 2)]\n", False),
        ("if False:\n    S = 1\n", False), ("S: int\n", False), ("", False)]

for tag, text in (("SHIPPED", SRC), ("ALIASED", ALIASED), ("MODULE_ALIAS", TOPLEVEL)):
    m = load(tag.lower() + "_probe", text)
    built = [(m.Resolver(DECL + b, "<c>"), must) for b, must in ROWS]   # __init__ legitimately walks the AST
    CALLS["n"] = 0
    got = []
    for r, must in built:
        try:
            r.refuse_site_rebindings(r.site_names()); got.append(False)
        except m.UnresolvableScope:
            got.append(True)
    ok = got == [must for _, must in built]
    print(tag + "\t" + str(CALLS["n"]) + "\t" + str(ok))
"""


def test_the_refusal_decides_what_binds_without_walking_the_ast(tmp_path):
    """THE PROPERTY, MEASURED — replacing a text check that a rename defeated.

    THE NAME IS A CLAIM, SO IT SAYS WHAT IS MEASURED. This test was first called
    `test_the_refusal_never_consults_the_ast`, which is FALSE of the shipped code and was caught by reading the
    name against the function rather than by any failure. The refusal DOES reach the AST, through
    `site_names()`, which walks `self.tree.body` and asks `isinstance(n, ast.Assign)` — and the counter reports
    zero for it, correctly, because that is not a walk over binding forms. What is measured, and all that is
    measured, is that the refusal decides WHAT BINDS without walking the AST. `site_names()` answers a
    different question — which module-level names are `NAME = declare_site(...)` targets — and structurally
    cannot answer a binding one: it looks only at top-level `Assign` statements and would miss every form the
    six spellings are made of, which is exactly why it is safe here and was not safe as a binding reading.

    THE EXCLUDED SURFACE, NAMED. The counter wraps `ast`'s walking callables and `ast.Store`, so it catches any
    ALIAS of them, at module level or inside the function, which is what defeated the text check. It would NOT
    catch a hand-rolled recursion over `node._fields` that calls no `ast` function at all. That is the
    irreducible limit of this instrument and it is stated rather than left to be discovered — though it is
    worth noting the enumeration this round removed was not of that shape: it used `ast.iter_child_nodes` and
    `ast.Name`/`ast.Store`, and so does every reinstatement a reader would naturally write.

    THIS TEST AND `test_the_refusals_only_reach_into_the_ast_is_the_declaration_lookup` ARE A PAIR. DO NOT
    DELETE EITHER AS REDUNDANT TO THE OTHER — they look independent and only together do they bound the
    surface (research's reading). This one catches AST USE; that one catches AST use THAT MATTERS. A
    hand-rolled `_fields` recursion escapes this counter, but the moment it makes the reading sensitive to HOW
    a name is rebound, the 46-row invariance test fails. What is left over is a walk that touches the AST and
    changes no answer, which is inert by definition — a far smaller residue than "the counter has a limit".

    Round 8e first gated this by refusing the strings `ast.Store`, `ast.walk` and `ast.iter_child_nodes` inside
    the refusal's source. Research defeated it in one line: `from ast import walk as _w, Store as _St` contains
    none of them, reinstates the whole enumeration, and the test passes. A text check for names is a narrow
    matcher, inside the test written to prevent narrow matchers — the finding's own class, one level up again.

    So the claim is measured instead. Every AST-walking callable is wrapped in a counter and `ast.Store` is
    replaced by a class whose instance checks count, BEFORE the resolver is imported; then a Resolver is built
    (its `__init__` legitimately walks the AST to index scopes, so the count is taken after), and the refusal is
    called. The shipped code must consult the AST ZERO times. Two mutants that reinstate a walk — one aliasing
    inside the function, one aliasing at module level, which a patch-after-import control could not see — must
    both be caught, and both must still return the right verdicts, so the redness is the property and not a
    broken mutant.

    TWO PROPERTIES OF THIS TEST THAT MUST SURVIVE ANY SIMPLIFICATION (research's note). Both mutants return
    CORRECT verdicts, so what goes red is the property and not a broken mutant. And the probe runs in a
    SUBPROCESS, because it monkeypatches the stdlib `ast` module and doing that in the session would be fixture
    state living outside the thing under test — this round's other recurring class, which would have leaked into
    every test that parses anything, under a shuffle, with no way to tell where it came from.
    """
    probe = tmp_path / "ast_consultation_probe.py"
    probe.write_text(_AST_CONSULTATION_PROBE)
    run = subprocess.run([sys.executable, str(probe), str(EVIDENCE / "scope_resolution.py")],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr[-2000:]
    rows = {}
    for line in run.stdout.strip().splitlines():
        tag, count, verdicts_ok = line.split("\t")
        rows[tag] = (int(count), verdicts_ok == "True")
    assert set(rows) == {"SHIPPED", "ALIASED", "MODULE_ALIAS"}, rows
    for tag, (_, verdicts_ok) in rows.items():
        assert verdicts_ok, f"{tag} returns wrong verdicts, so its count says nothing about the refusal"
    assert rows["SHIPPED"][0] == 0, (
        f"the refusal consulted the AST {rows['SHIPPED'][0]} times — it is supposed to decide from the compiled "
        f"code object and symtable alone, and an AST walk here is the enumeration round 8 removed")
    for tag in ("ALIASED", "MODULE_ALIAS"):
        assert rows[tag][0] > 0, f"the {tag} mutant reinstates an AST walk and this control did not see it"


def test_the_refusals_only_reach_into_the_ast_is_the_declaration_lookup():
    """The other half of the name above: not "it never touches the AST" but "the one place it does cannot
    answer a binding question". `site_names` reads only TOP-LEVEL `Assign` statements whose value is a call to
    `declare_site` — so it sees declarations and is blind to every rebinding form, which is what makes it the
    wrong instrument for the question and the right one for its own.

    Asserted by RUNNING it against the matrix's own rows rather than by reading it: for every row, the set of
    site names it reports is the same whether the module rebinds the name six ways or not at all. A reading
    that changed with the rebinding would be a reading of bindings.

    PAIRED WITH `test_the_refusal_decides_what_binds_without_walking_the_ast`, AND NEITHER IS REDUNDANT. That
    one wraps `ast`'s callables and so catches any ALIAS of them, but not a hand-rolled recursion over
    `node._fields` that calls no `ast` function. This one does not care HOW the AST is reached: it asserts the
    ANSWER does not move with the rebinding, so a hand-rolled walk that changes the reading fails here even
    though the counter stays at zero. Between them the only surviving case is a walk that touches the AST and
    changes nothing, which is inert. Deleting either one reopens a real gap."""
    baseline = sr.Resolver(DECL, "<decl>").site_names()
    assert baseline == {"S"}, baseline
    for label, body, _ in REBINDING_MATRIX:
        got = sr.Resolver(DECL + body, f"<{label}>").site_names()
        assert got == baseline, (
            f"{label}: site_names reports {got}, not {baseline} — it has started responding to how the name is "
            f"REBOUND, which would make it a binding reading and put an enumeration back in the refusal's path")


def test_the_binding_count_matches_a_hand_count_on_modules_small_enough_to_count():
    """Research's third target: confirming the four opcode names against `dis.opmap` catches a RENAME and not an
    ADDITION. A new binding opcode in a future CPython would leave all four valid and the count SHORT, silently —
    the enumeration moved down a layer rather than vanishing, to a layer that changes rarely and fails loudly on
    rename, but a hand list all the same. So the reading is also checked against modules whose module-level
    bindings of one name can be counted by eye. A new opcode shows up here as a count that stopped matching.

    The last three rows are the other half: a binding that is NOT this scope's must not be counted."""
    for label, body, expected in [
        ("one plain assignment",             "S = 1\n", 1),
        ("two plain assignments",            "S = 1\nS = 2\n", 2),
        ("an assignment and a del",          "S = 1\ndel S\n", 2),
        ("assignment, import-as, del",       "S = 1\nimport os as S\ndel S\n", 3),
        ("three, one shadowed in a function", "S = 1\nS = 2\nS = 3\ndef f():\n    S = 4\n    return S\n", 3),
        ("one, plus a comprehension target", "S = 1\nxs = [S for S in (1, 2)]\n", 1),
        ("one, plus a class-body attribute", "S = 1\nclass K:\n    S = 2\n", 1),
    ]:
        got = sr.Resolver(body, f"<{label}>")._module_binding_ops("S")
        assert len(got) == expected, f"{label}: hand-counted {expected}, the reading found {len(got)} ({got})"


def test_the_interpreters_reading_is_read_at_the_right_lines():
    """`_module_binding_ops` reports LINES, and CPython has spelled an instruction's line three ways across the
    versions CI runs (3.10 `starts_line`, 3.11+ `positions.lineno`, 3.13 `line_number`). A version that adds a
    fourth would silently report line 0 for everything and every refusal message would lose its location, while
    the verdicts above stayed green — so the lines are asserted, not just the counts."""
    r = sr.Resolver(DECL + "import os as S\n", "<lines>")
    ops = r._module_binding_ops("S")
    assert [line for _, line in ops] == [2, 3], ops
    assert all(op in sr._MODULE_BINDING_OPS for op, _ in ops), ops
    assert "lines 2, 3" in (_refusal(sr, "import os as S\n") or ""), "the message must carry the lines"


def test_rule_A_is_the_interpreters_reading_and_not_a_second_node_list():
    """What makes rule A total is that it reads the compiled module, so a form nobody enumerated is counted like
    any other. The proof is that it is right about a form this test file never lists: the `__all__`-style
    conditional import below binds `S` twice with no `ast.Name` store in sight on either line."""
    src = "import sys\nif sys.platform:\n    import os as S\nelse:\n    from os import path as S\n"
    r = sr.Resolver(DECL + src, "<unlisted>")
    assert [line for _, line in r._module_binding_ops("S")] == [2, 5, 7], "the interpreter sees both branches"
    assert "bound 3 times" in (_refusal(sr, src) or "")
    # the condition is deliberately not a constant: `if 1:` is folded away and the `else` branch is never
    # compiled, so a folded example would have understated the interpreter's reading and passed for a wrong reason
    folded = sr.Resolver(DECL + "if 1:\n    import os as S\nelse:\n    from os import path as S\n", "<folded>")
    assert len(folded._module_binding_ops("S")) == 2, "the dead branch really is absent from the code object"


def test_the_opcode_names_are_confirmed_against_this_interpreters_table():
    """A check that reads opcodes BY NAME weakens silently if a name moves: every count falls to zero, every
    module is accepted, and nothing is red. The names are therefore confirmed against `dis.opmap` at import.
    The control is a copy of the module with one name misspelled, which must refuse to import at all."""
    import dis as _dis
    assert all(op in _dis.opmap for op in sr._MODULE_BINDING_OPS), sr._MODULE_BINDING_OPS
    broken = (EVIDENCE / "scope_resolution.py").read_text().replace('"DELETE_GLOBAL")', '"DELETE_GLOBAL_")', 1)
    path = pathlib.Path(__import__("tempfile").mkdtemp()) / "renamed_opcode.py"
    path.write_text(broken)
    with pytest.raises(RuntimeError, match="dis.opmap"):
        _load("scope_resolution_renamed_opcode", path)


def test_source_that_parses_but_does_not_compile_is_refused_not_raised_through():
    """`ast.parse` accepts text the compiler rejects, so `__init__` can succeed where the interpreter's reading
    cannot be taken at all. That is a refusal in this module's own vocabulary, not a bare SyntaxError escaping
    from the middle of a scan."""
    import ast as _ast
    assert _ast.parse("return 1"), "the premise: this parses"
    with pytest.raises(SyntaxError):
        compile("return 1", "<p>", "exec")
    r = sr.Resolver(DECL + "return 1\n", "<uncompilable>")
    with pytest.raises(sr.UnresolvableScope, match="parses but does not compile"):
        r.refuse_site_rebindings(r.site_names())


def test_a_reading_that_finds_nothing_is_a_broken_reading_not_a_clean_module():
    """The failure mode of the guard above, one level in: if the interpreter's reading ever returns EMPTY for a
    name this module declares at module level, the reading is broken and every rebinding would be accepted in
    silence. An empty reading is a refusal, and the control is the same module read normally."""
    r = sr.Resolver(DECL + "S = object()\n", "<blinded>")
    assert r.site_names() == {"S"}
    with pytest.raises(sr.UnresolvableScope, match="bound 2 times"):
        r.refuse_site_rebindings(r.site_names())
    r._module_binding_ops = lambda name: []                      # the reading goes blind
    with pytest.raises(sr.UnresolvableScope, match="the reading is broken"):
        r.refuse_site_rebindings(r.site_names())


def test_a_refusal_never_claims_a_global_statement_the_module_does_not_contain():
    """CI found this on 3.10 and 3.11, and it was a FALSE SENTENCE IN A REFUSAL, not a stale expectation.

    Rule C chose its wording with `is_declared_global()`, on the assumption that the flag means the source said
    `global`. It does not: for a WALRUS inside a comprehension, `symtable` synthesises the flag, and the refusal
    told the reader `` `global S` with an assignment `` about a module containing no `global` anywhere. A
    refusal is read by someone deciding what to change; sending them to look for a statement that is not there
    is worse than saying less. The message now names both spellings and claims neither.

    The assertion is version-independent by construction — on 3.12 the row is answered by rule A, whose message
    also contains no such claim — so this test does not encode which rule answers it."""
    body = "xs = [(S := q) for q in (1, 2)]\n"
    source = DECL + body
    assert "global" not in source, "the premise: this module contains no `global` statement"
    message = _refusal(sr, body)
    assert message is not None, "a walrus in a comprehension rebinds the site and must be refused"
    assert "`global S` with an assignment" not in message, (
        f"the refusal claims a `global` statement this module does not contain: {message}")
    # and the fact that caused it, recorded where it will be re-measured rather than remembered
    import symtable as _st
    blocks = [c for c in _st.symtable(source, "<w>", "exec").get_children() if c.get_name() == "listcomp"]
    if blocks:                                    # 3.10/3.11 only; from 3.12 PEP 709 inlines it away
        sym = blocks[0].lookup("S")
        assert sym.is_declared_global(), (
            "symtable no longer synthesises declared-global for a comprehension walrus on this interpreter — "
            "the premise of this test has moved, and rule C's docstring says the two predicates agree")


def _old_predicate_pair_fires(src: str, names) -> bool:
    """RULE C AS IT READ BEFORE ROUND 9, kept here as the negative control its replacement must beat.

    `sym.is_global() and sym.is_assigned()` — the hand-picked predicate pair round 8's reviewer defeated with
    a nested `import os as S` under `global S`, which symtable reports `is_imported` and NOT `is_assigned`.
    Keeping the superseded implementation is the only way the REASON for the change stays a result: a
    docstring saying "the old reading missed the imports" is a claim, and this makes it an assertion."""
    import symtable as _st
    table = _st.symtable(src, "<old-pair>", "exec")
    fired = []

    def walk(block):
        if block.get_type() != "module":
            for n in names:
                try:
                    sym = block.lookup(n)
                except KeyError:
                    continue
                if sym.is_global() and sym.is_assigned():
                    fired.append(block.get_name())
        for child in block.get_children():
            walk(child)

    walk(table)
    return bool(fired)


def test_the_superseded_predicate_pair_misses_exactly_the_nested_imports():
    """THE CHANGE IS EXACTLY AS WIDE AS IT WAS SAID TO BE — asserted in BOTH directions, because "the new rule
    catches more" is half a claim and the dangerous half is the other one.

      - the old pair ACCEPTS the two nested-import rows that the shipped rule REFUSES (the round-8 finding); and
      - on every OTHER row of the matrix the two readings agree, so replacing the predicate with the
        interpreter's reading did not quietly start refusing something else.

    This replaced `test_the_two_global_predicates_agree_over_the_whole_matrix`, which compared `is_global()`
    against `is_declared_global()`. That test became MOOT rather than failing: rule C asks neither predicate
    now, so the mutant it built had no anchor. A test whose subject has been deleted must be replaced by one
    about the successor, never merely repaired until it passes."""
    expected_misses = {"a nested `import x as S` under `global`", "a nested `from x import y as S` under `global`"}
    assert expected_misses <= {row[0] for row in REBINDING_MATRIX}, "the reviewer's two rows left the matrix"
    disagreements = set()
    for label, body, _expect in REBINDING_MATRIX:
        src = DECL + body
        r = sr.Resolver(src, f"<{label}>")
        names = r.site_names()
        new_fires = any(r._nested_global_bindings(n) for n in names)
        if new_fires != _old_predicate_pair_fires(src, names):
            disagreements.add(label)
    assert disagreements == expected_misses, (
        f"the two readings of rule C now differ on {sorted(disagreements)}, not on exactly the two nested "
        f"imports. If that is intended, this is the test that has to say so.")


# Which rule is expected to catch each REFUSED row. Derived once by disabling each rule in turn and recorded
# here so that a row CHANGING HANDS is a test failure rather than a silent re-attribution.
RULE_OWNER = {
    # rule A — the module's own code object binds the name more than once
    "import os as S": "A", "from os import path as S": "A", "except Exception as S": "A", "del S": "A",
    "def S()": "A", "class S": "A", "async def S()": "A", "import os as S inside a try": "A",
    "a match capture": "A", "a match as-pattern": "A", "a plain second assignment": "A",
    "an augmented assignment": "A", "an annotated assignment": "A", "a module-level for target": "A",
    "a module-level with-as": "A", "tuple unpacking": "A", "starred unpacking": "A",
    "a module-level walrus": "A", "a try/except import fallback": "A",
    "a site declared in both branches": "A", "an `if TYPE_CHECKING` import": "A",
    # rule C — a NESTED code object binds the module name with STORE_GLOBAL/DELETE_GLOBAL
    "a walrus in a genexpr": "C", "`global S` assigned in a function": "C",
    "`global S` deleted in a function": "C", "`global S` in a class body": "C",
    "`global S` two scopes down": "C", "a nested `import x as S` under `global`": "C",
    "a nested `from x import y as S` under `global`": "C",
    # THE ONE ROW THAT CHANGES HANDS, and the reason this table exists. PEP 709 inlines a LIST comprehension
    # from 3.12, so its walrus becomes an ordinary module-level binding and rule A counts it; before 3.12 the
    # comprehension has its own code object and rule C reads the store. The GENERATOR-expression spelling
    # above keeps its own code object on every version and stays with C — the two sit adjacent on purpose, so
    # one interpreter exercises both regimes.
    "a walrus in a listcomp": "A" if sys.version_info >= (3, 12) else "C",
}


def test_every_refused_row_names_the_rule_that_caught_it():
    """A ROW THAT CHANGES HANDS BETWEEN THE RULES IS INVISIBLE TO A MATRIX THAT ONLY ASSERTS "REFUSED".

    Research's stage-1 recommendation for round 9, and it is the gate that would have caught its own example:
    the listcomp walrus is refused on all four interpreters, so the matrix is green on all four — GREEN FOR A
    DIFFERENT REASON on each side of 3.12. Asserting only the refusal cannot see that, so it also cannot see a
    future version moving a row the other way, or a change to rule A quietly taking over a row that was rule
    C's evidence.

    The owner is DERIVED by disabling each rule in turn, never read off the source, and the declared table's
    keys must equal the refused rows exactly — so adding a refused row without deciding which rule owns it
    fails here rather than passing unnoticed."""
    refused = {row[0] for row in REBINDING_MATRIX if row[2]}
    assert set(RULE_OWNER) == refused, (
        f"declared owners and refused rows differ — only in RULE_OWNER: {sorted(set(RULE_OWNER) - refused)}; "
        f"only in the matrix: {sorted(refused - set(RULE_OWNER))}")
    without_a, without_c = _mutant(*RULE_A), _mutant(*RULE_C)
    wrong = []
    for label, body, must_refuse in REBINDING_MATRIX:
        if not must_refuse:
            continue
        a_off = _refusal(without_a, body) is not None      # still refused with A disabled -> C reaches it
        c_off = _refusal(without_c, body) is not None      # still refused with C disabled -> A reaches it
        got = "A+C" if (a_off and c_off) else ("C" if a_off else ("A" if c_off else "NEITHER"))
        if got != RULE_OWNER[label]:
            wrong.append(f"{label}: declared {RULE_OWNER[label]}, derived {got}")
    assert not wrong, "rows changed hands between the rules:\n  " + "\n  ".join(wrong)



# ------------------------------------------------------------------------------------------------------------------
# ROUND 12, research's STAGE-2 S2-1 — THE RESOLVER PLACED EVERY DEFINITION-TIME POSITION IN THE INNER SCOPE.
# ------------------------------------------------------------------------------------------------------------------

# Every position Python evaluates in the ENCLOSING scope when a def, lambda or class statement runs. `__X__` is filled
# with the name under test. Research's stage-2 read named seven; enumerating the grammar found TWELVE, and all twelve
# were wrong at d61fd62 (plus a nested composition). ONE LIST, shared by the inv7 tests, which load it from here by
# path — two copies of a position list would be the hand-kept pair this whole round removed.
DEFINITION_TIME_POSITIONS = [
    ("default",                     "def f(x=__X__):\n    return x\n"),
    ("kw-only-default",             "def f(*, x=__X__):\n    return x\n"),
    ("positional-only-default",     "def f(x=__X__, /):\n    return x\n"),
    ("function-decorator-arg",      "@deco(__X__)\ndef f():\n    return 1\n"),
    ("arg-annotation",              "def f(x: __X__ = 1):\n    return x\n"),
    ("star-args-annotation",        "def f(*a: __X__):\n    return a\n"),
    ("star-star-kwargs-annotation", "def f(**k: __X__):\n    return k\n"),
    ("return-annotation",           "def f() -> __X__:\n    return 1\n"),
    ("lambda-default",              "g = lambda x=__X__: x\n"),
    ("class-base",                  "class K(__X__):\n    pass\n"),
    ("class-keyword",               "class K(metaclass=__X__):\n    pass\n"),
    ("class-decorator-arg",         "@deco(__X__)\nclass K:\n    pass\n"),
    ("nested-function-default",     "def outer():\n    def inner(x=__X__):\n        return x\n    return inner\n"),
    # A SCOPE NESTED INSIDE A DEFAULT. The fix's own docstring claims each node is visited EXACTLY ONCE, because
    # re-assigning a default after the fact would visit its lambda or comprehension twice and consume two
    # symbol-table blocks. A claim with no test is a docstring: these are the test.
    ("lambda-inside-a-default",     "def f(x=lambda: __X__):\n    return x\n"),
    ("comprehension-inside-a-default", "def f(x=[v for v in [__X__]]):\n    return x\n"),
]
_S21_HEAD = "from . import census as _census\nS = _census.declare_site('s')\n\ndef deco(v):\n    return lambda fn: fn\n\n"


@pytest.mark.parametrize("cell,body,want", [
    ("control-function-body", "def f():\n    return S\n", [True]),
    ("control-a-parameter-named-S-shadows-it", "def f(S=1):\n    return S\n", [False]),
    # THE ACCEPTANCE HALF, and the one a careless fix breaks: the default is the ENCLOSING scope's even when the
    # body binds the same name, and the body's own `S` stays local.
    ("default-is-enclosing-while-the-body-binds-S", "def f(x=S):\n    S = 2\n    return S + x\n", [True, False]),
    # ROUND 12 STAGE 2b, research's S2b-2 (mutant DM8 survived): a definition-time part inside an INLINED comprehension
    # must keep the comprehension's own shadowing. The default names the comprehension TARGET, never the site — and
    # dropping the shadow set is equivalent on 3.10/3.11 (a real block) and wrong on 3.12/3.13 (inlined).
    ("lambda-default-naming-its-comprehension-target", "x = [(lambda y=S: y) for S in range(3)]\n", [False]),
] + [(pos, body.replace("__X__", "S"), None) for pos, body in DEFINITION_TIME_POSITIONS],
    ids=lambda v: v if isinstance(v, str) and "\n" not in v else "")
def test_r12_s2_1_definition_time_positions_resolve_in_the_enclosing_scope(cell, body, want):
    """RESEARCH'S STAGE-2 S2-1, measured before this was written: `refers_to_declared_site` returned True in a
    function BODY and False in a default, a decorator, an annotation and a class keyword. Python evaluates all of
    those in the ENCLOSING scope, when the `def`/`lambda`/`class` statement runs — the resolver sent every child of
    the statement to the inner block. The comprehension handler beside it already made exactly this distinction for
    its first iterable; definitions never got it.

    Two consumers took the answer at face value: round 12's R2 refusal (a site loaded as a value), which MISSED all
    of these, and round 11's unresolved-bypass detector, which went SILENT — `def f(q, on=_census.enabled())` left a
    live census call in the twin with nothing reported. Loads are compared in SOURCE ORDER."""
    r = sr.Resolver(_S21_HEAD + body, f"<{cell}>"); r.refuse_site_rebindings({"S"})
    loads = sorted((n for n in ast.walk(r.tree) if isinstance(n, ast.Name) and n.id == "S" and isinstance(n.ctx, ast.Load)),
                   key=lambda n: (n.lineno, n.col_offset))
    assert loads, f"{cell}: the fixture loads no `S` at all, so it tests nothing"
    got = [r.refers_to_declared_site(n, "S") for n in loads]
    expected = want if want is not None else [True] * len(loads)
    assert got == expected, f"{cell}: the resolver says {got}, Python evaluates these as {expected}"



# ------------------------------------------------------------------------------------------------------------------
# ROUND 12 STAGE 2b, research's S2b-1 — SAME-LINE NESTED SCOPES IN DIFFERENT ROLES GOT EACH OTHER'S TABLES.
# ------------------------------------------------------------------------------------------------------------------

# One key, `(line, kind)`, names every lambda (or comprehension) on a line, and the resolver drains its queue of
# symbol-table blocks in its OWN visiting order. symtable FILLS it in the interpreter's order: it evaluates a
# statement's header — decorators, defaults, annotations, return, bases, keywords, a comprehension's first iterable —
# in the ENCLOSING scope before the statement's own block exists, and groups the header by ROLE. Research measured
# the in-header order: positional defaults, kw-only defaults, annotations (posonly, args, *args, **kwargs, kw-only),
# return. `iter_fields` groups by FIELD. Where the two disagree, each scope is handed the other's table.
#
# Remedy (b), on Quentin's word: REFUSE rather than guess the order, which is the resolver's own principle. A
# collision is refused when one key spans two or more ROLES and at least one is a header role. "Self + body" and
# "one role twice" are left alone: their orders provably agree and ordinary code uses them.
SAME_LINE_ROLE_COLLISIONS = [
    ("positional-default-vs-kw-only-default",  "def f(q, a=lambda: 1, *, k=lambda: 2):\n    return q\n"),
    ("annotation-vs-default",                  "def f(q: (lambda: 1) = lambda: 2):\n    return q\n"),
    ("kwargs-annotation-vs-kw-only-annotation", "def f(*, k: (lambda: 1), **kw: (lambda: 2)):\n    return k\n"),
    # BASE vs KEYWORD. (A first draft put both lambdas in `keywords` — `**{...}` is a keyword too, arg=None — which
    # is "one role twice", the case the rule ACCEPTS; the cell would have asserted the wrong expectation.)
    ("class-base-vs-class-keyword",            "class K((lambda: dict)(), m=(lambda: 2)):\n    pass\n"),
]
SAME_LINE_ROLE_ACCEPTED = [
    ("two-lambdas-in-one-role-positional-defaults", "def f(a=lambda: 1, b=lambda: 2):\n    return a\n"),
    ("two-lambdas-both-in-a-body",                  "def f():\n    return (lambda: 1), (lambda: 2)\n"),
    ("self-and-body-same-kind",                     "g = lambda: (lambda: 1)\n"),
    ("comprehension-with-a-same-kind-scope-in-its-element", "x = [[p for p in range(2)] for q in range(3)]\n"),
]


@pytest.mark.parametrize("cell,body", SAME_LINE_ROLE_COLLISIONS, ids=[c for c, _ in SAME_LINE_ROLE_COLLISIONS])
def test_r12_s2b_1_same_line_scopes_across_roles_are_refused_not_guessed(cell, body):
    """RESEARCH'S S2b-1, and it was SILENT. With one of the two scopes binding the census alias as its own parameter
    and the other reading it, the read resolved to the parameter: a live census call stayed in the twin with nothing
    reported. Research measured three in-header pairs; the same mechanism gave dev three more, all confirmed silent —
    return annotation vs body, a lambda inside a lambda's own default, and a genexp nested in a genexp's FIRST
    ITERABLE. The last is in round 8's comprehension handler, not in round 12's code: the class, not the cell."""
    with pytest.raises(sr.UnresolvableScope, match="different roles"):
        sr.Resolver("from . import census as _census\n" + body, f"<{cell}>")


@pytest.mark.parametrize("cell,body", SAME_LINE_ROLE_ACCEPTED, ids=[c for c, _ in SAME_LINE_ROLE_ACCEPTED])
def test_r12_s2b_1_same_line_scopes_whose_orders_agree_are_not_refused(cell, body):
    """THE ACCEPTANCE HALF. A refusal that fires on ordinary code is the narrow-gate defect in the other direction:
    two lambdas in ONE role, two in a BODY, a scope and a same-kind scope in its own body — in each, symtable's order
    and the resolver's agree, and research's control (two same-line genexps in a body) already stood on that."""
    sr.Resolver("from . import census as _census\n" + body, f"<{cell}>")



# THE SHAPES FIXED BY ORDER, NOT REFUSAL. A header part against the statement's OWN block or its BODY: the language
# defines the order (the header runs in the enclosing scope before the block exists, the body inside it after), so the
# resolver now takes them in that order. Each scope binds a DISTINCT name, and the assertion is per element — a swap
# is exactly what a set comparison cannot see (see the corrected nested-genexp assertion above).
SAME_LINE_ORDERED = [
    ("return-annotation-vs-body",              "def f() -> (lambda rrr: rrr): return (lambda bbb: bbb)(1)\n"),
    ("lambda-inside-a-lambda-default",         "g = lambda ooo=(lambda iii: iii): ooo\n"),
    ("genexp-in-a-genexp-first-iterable",      "x = list(ooo for ooo in (iii for iii in range(3)))\n"),
    ("listcomp-in-a-listcomp-first-iterable",  "x = [ooo for ooo in [iii for iii in range(3)]]\n"),
]


def _own_names(n):
    if isinstance(n, ast.Lambda):
        return {a.arg for a in n.args.posonlyargs + n.args.args + n.args.kwonlyargs}
    return {x.id for g in n.generators for x in ast.walk(g.target) if isinstance(x, ast.Name)}


@pytest.mark.parametrize("cell,body", SAME_LINE_ORDERED, ids=[c for c, _ in SAME_LINE_ORDERED])
def test_r12_s2b_1_a_header_part_beside_its_own_block_gets_its_own_table(cell, body):
    """RESEARCH'S S2b-1, the part fixed by ORDER on Quentin's word. The resolver took a statement's own block from the
    queue BEFORE the blocks nested in its header, which the interpreter creates first — so a lambda in a lambda's
    default, a return annotation beside a same-line body lambda, and a genexp in a genexp's first iterable each got
    the other's table. Dev confirmed all three silent; the genexp shape is live in asof/resolve.py:445. Refusing them
    would have refused real product code, and the language defines this order, so it is not a guess.

    On 3.12+ an inlined listcomp has no block of its own and resolves in the enclosing one, where no swap is possible;
    the stronger half of the assertion (no OTHER scope's names) applies wherever a scope has a block to swap."""
    r = sr.Resolver(body, f"<{cell}>")
    scopes = [n for n in ast.walk(r.tree) if isinstance(n, (ast.Lambda, ast.ListComp, ast.GeneratorExp))]
    assert len(scopes) == 2, f"{cell}: the fixture should hold exactly two same-line scopes"
    for n in scopes:
        inside = n.body if isinstance(n, ast.Lambda) else n.elt
        block = r.block_of(inside)
        held = {x for x in block.get_identifiers() if not x.startswith(".")}
        own = _own_names(n)
        assert own <= held, f"{cell}: the scope binding {sorted(own)} resolves inside a block holding {sorted(held)}"
        if block.get_type() != "module":
            others = set().union(*(_own_names(m) for m in scopes if m is not n))
            assert not (held & others), f"{cell}: the scope binding {sorted(own)} got a table holding {sorted(held & others)}"



# ------------------------------------------------------------------------------------------------------------------
# ROUND 12 STAGE 2c, research's S2c-2 — CPython 3.13's SYMTABLE DISAGREES WITH ITS OWN COMPILER.
# ------------------------------------------------------------------------------------------------------------------

def test_r12_s2c_2_an_inlinable_comprehension_in_a_first_iterable_is_refused_on_3_12_plus():
    """RESEARCH'S S2c-2, measured by executing it. `lambda p0: [u5 for t4 in {0 for t5 in [0] for u5 in [1]}]` RETURNS
    ['MODULE'] on 3.10, 3.11 and 3.13 — the name is the module's — while 3.13's symtable says `u5` is LOCAL to the
    lambda. This resolver's premise is that symtable IS the interpreter's analysis, and on this shape, on this version,
    it is not; through the transform a census read there stayed live in the twin with unresolved=0. On 3.12.3 the
    source ITSELF raises UnboundLocalError (a CPython inlining bug on that version).

    REFUSED ON 3.12+, on Quentin's word — the resolver cannot answer where its source of truth is wrong, and refusing
    is its principle. NOT refused on 3.10/3.11, where symtable and the compiler agree and the answer is right: the
    refusal is loud where it fires and the answer correct where it does not, so this is not round 8's SILENT
    version divergence. Only inside a function or class block: at module level `block_of` answers module outright."""
    shape = "def f(q):\n    return [q for t in {0 for u in range(1)}]\n"
    if sys.version_info >= (3, 12):
        with pytest.raises(sr.UnresolvableScope, match="symtable"):
            sr.Resolver(shape, "<s2c2>")
    else:
        sr.Resolver(shape, "<s2c2>")                                   # 3.10/3.11: symtable is right, and resolves


@pytest.mark.parametrize("cell,body", [
    ("the-same-shape-at-module-level", "x = [0 for t in {0 for u in range(1)}]\n"),
    ("a-genexp-not-inlinable-in-a-first-iterable-the-resolve-py-445-shape",
     "def f(r):\n    return list(o for o in (i for i in r))\n"),
    ("an-inlinable-comprehension-in-a-LATER-iterable", "def f(r):\n    return [0 for t in r for u in [v for v in r]]\n"),
], ids=lambda v: v if "\n" not in v else "")
def test_r12_s2c_2_the_refusal_does_not_reach_shapes_symtable_answers_rightly(cell, body):
    """THE ACCEPTANCE HALF: the refusal is the one shape research measured wrong — an INLINABLE comprehension in a
    comprehension's FIRST iterable, inside a function — and none of its neighbours. asof/resolve.py:445 is a genexp in a
    genexp's first iterable; a refusal reaching it would refuse real product code on 3.12+."""
    sr.Resolver(body, f"<{cell}>")


# ------------------------------------------------------------------------------------------------------------------
# ROUND 13 — THE ROUND-12 VERDICT'S F1 (research's S2c-1): THE ORDER INSIDE A COMPREHENSION.
# ------------------------------------------------------------------------------------------------------------------

# Two same-line lambdas in the positions CPython's symtable orders differently from a field walk: it visits the
# outermost ifs, then each later generator as TARGET, ITER, IFS, then a dict comprehension's VALUE, then the ELEMENT or
# KEY last. Each lambda binds a parameter no other scope names, so a swap is visible per element. Every cell is given
# in a listcomp (inlined on 3.12+, its own block below) AND a genexp (a block on every version).
_R13_ORDER_BODIES = [
    ("element-vs-if",               "[(lambda eee: eee)(0) for x in [1] if (lambda fff: fff)(1)]"),
    ("element-vs-later-iterable",   "[(lambda eee: eee)(0) for x in [1] for y in (lambda fff: [fff])(1)]"),
    ("element-vs-later-if",         "[(lambda eee: eee)(0) for x in [1] for y in [2] if (lambda fff: fff)(1)]"),
    ("later-target-vs-element",     "[(lambda eee: eee)(0) for x in [[0]] for x[(lambda fff: fff)(0)] in [1]]"),
    ("later-target-vs-later-iter",  "[0 for x in [[0]] for x[(lambda eee: eee)(0)] in (lambda fff: [fff])(1)]"),
    ("dict-key-vs-value",           "{(lambda eee: eee)(0): (lambda fff: fff)(1) for x in [1]}"),
    ("dict-key-vs-if",              "{(lambda eee: eee)(0): 0 for x in [1] if (lambda fff: fff)(1)}"),
]
R13_COMPREHENSION_ORDER = [(c, f"def f():\n    return {b}\n") for c, b in _R13_ORDER_BODIES] + [
    (c + "/genexp", f"def f():\n    return list({b[1:-1]} )\n") for c, b in _R13_ORDER_BODIES if b.startswith("[")]


@pytest.mark.parametrize("cell,body", R13_COMPREHENSION_ORDER, ids=[c for c, _ in R13_COMPREHENSION_ORDER])
def test_r13_f1_every_scope_inside_a_comprehension_gets_its_own_table(cell, body):
    """THE ROUND-12 VERDICT'S F1: "the disclosed scope-order gap changes a measured decision from [True] to [False]
    while verify() reports clean". The comprehension handler walked elt/key/value BEFORE the generators, while CPython
    creates their nested blocks in the opposite order, so two same-line lambdas split across those positions were
    handed each other's tables. Asserted PER ELEMENT — a set comparison is blind to exactly this swap (round 12's
    lesson) — on every version CI runs."""
    r = sr.Resolver(body, f"<{cell}>")
    lambdas = [n for n in ast.walk(r.tree) if isinstance(n, ast.Lambda)]
    assert len(lambdas) == 2, f"{cell}: the fixture should hold exactly two lambdas"
    names = [_own_names(n) for n in lambdas]
    for n, own, other in ((lambdas[0], names[0], names[1]), (lambdas[1], names[1], names[0])):
        held = {x for x in r.block_of(n.body).get_identifiers() if not x.startswith(".")}
        assert own <= held and not (held & other), \
            f"{cell}: the lambda binding {sorted(own)} resolves inside a block holding {sorted(held)}"


# ROUND 13 — THE JOIN CHECK (research's P2', stage-1 read of round 13). The order fix above closes the cells; this
# closes the CLASS: a same-line group of blocks is safe only if every block's fingerprint is identical or every node
# is fitted by exactly one block — its own. Anything else would rest on an order alone, and is REFUSED.
_R13_NEW_ORDER = '''        for i, gen in enumerate(child.generators):
            self._comp_local[id(gen)] = body_shadow
            self._owner[id(gen)] = body_block
            self._assign_child(gen.target, body_block, body_shadow)
            if i:
                self._assign_child(gen.iter, body_block, body_shadow)
            for cond in gen.ifs:
                self._assign_child(cond, body_block, body_shadow)
        for field in ("value", "elt", "key"):
            sub = getattr(child, field, None)
            if sub is not None:
                self._assign_child(sub, body_block, body_shadow)'''
_R13_OLD_ORDER = '''        for field in ("elt", "key", "value"):
            sub = getattr(child, field, None)
            if sub is not None:
                self._assign_child(sub, body_block, body_shadow)
        for i, gen in enumerate(child.generators):
            self._comp_local[id(gen)] = body_shadow
            self._owner[id(gen)] = body_block
            if i:
                self._assign_child(gen.iter, body_block, body_shadow)
            self._assign_child(gen.target, body_block, body_shadow)
            for cond in gen.ifs:
                self._assign_child(cond, body_block, body_shadow)'''


def _r13_verdict(mod, cell, body):
    try:
        r = mod.Resolver(body, f"<{cell}>")
    except mod.UnresolvableScope as e:
        assert "join check" in str(e), f"{cell}: refused, but not by the join check: {e}"
        return "refused"
    lambdas = [n for n in ast.walk(r.tree) if isinstance(n, ast.Lambda)]
    right = all(_own_names(n) <= set(r.block_of(n.body).get_identifiers()) for n in lambdas)
    return "right" if right else "SILENT-WRONG"


def test_r13_the_join_check_turns_the_old_orders_silent_answers_into_refusals():
    """THE SUPERSEDED ORDER IS THE MUTANT. With round 12's comprehension order restored and the join check REMOVED,
    every order cell resolves silently wrong — which proves the cells can see the defect. With the old order and the
    check KEPT, every one is refused. So a future construct ordered wrongly fails loudly rather than resolving."""
    no_check = _mutant(_R13_NEW_ORDER + "\n", _R13_OLD_ORDER + "\n")
    src = (EVIDENCE / "scope_resolution.py").read_text().replace(_R13_NEW_ORDER, _R13_OLD_ORDER)
    assert src.count("        self._check_join()\n") == 1
    path = pathlib.Path(__import__("tempfile").mkdtemp()) / "scope_resolution_old_order_unchecked.py"
    path.write_text(src.replace("        self._check_join()\n", ""))
    unchecked = _load("scope_resolution_r13_old_order_unchecked", path)
    silent = {c: _r13_verdict(unchecked, c, b) for c, b in R13_COMPREHENSION_ORDER}
    assert set(silent.values()) == {"SILENT-WRONG"}, f"the cells cannot all see the old order: {silent}"
    loud = {c: _r13_verdict(no_check, c, b) for c, b in R13_COMPREHENSION_ORDER}
    assert set(loud.values()) == {"refused"}, f"the join check let an old-order answer through: {loud}"


def test_r13_the_join_check_refuses_research_s_blind_case_and_accepts_interchangeable_scopes():
    """RESEARCH'S R1: two PARAMETER-LESS lambdas on one line, one binding `_census` by walrus, the other reading it —
    a parameter-equality check passes ([] == []) and the twin kept a live census call with unresolved=0. Refused.
    The control: two lambdas whose tables are IDENTICAL cannot be mis-paired to any effect, and are resolved."""
    blind = "from . import census as _census\nG = ((lambda: (_census := 1)) for x in range(3) if (lambda: _census.enabled())())\n"
    with pytest.raises(sr.UnresolvableScope, match="join check"):
        sr.Resolver(blind, "<r1>")
    sr.Resolver("G = ((lambda: 0) for x in range(3) if (lambda: 0)())\n", "<control>")


def test_r13_the_join_check_refuses_nothing_in_the_product_or_the_evidence():
    """The check's cost, measured rather than assumed: dev's first form (a SUBSET test for comprehensions) refused
    inv7_uninstrument.py:499, where two same-line genexps are told apart only by one target. Equality — research's
    rule — refuses none of the product and evidence modules, on every version CI runs."""
    mods = sorted(list((ROOT / "src" / "veracium").rglob("*.py")) + list(EVIDENCE.glob("*.py")))
    refused = []
    for p in mods:
        try:
            sr.Resolver(p.read_text(), str(p))
        except sr.UnresolvableScope as e:
            refused.append(f"{p.relative_to(ROOT)}: {e}")
    assert len(mods) > 60 and not refused, "\n".join(refused)


# ROUND 13 — THE PAIRING ORACLE AS A STANDING GATE (research's (h) and stage-1 R3). Random one-line programs dense with
# same-line nested scopes, judged against CPython's BYTECODE. It tests the class every silent defect of rounds 12 and 13
# belonged to, rather than one more hand-built cell of it.
_ORACLE_N, _ORACLE_SEED = 400, 13


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the pairing oracle reads instruction POSITIONS, which 3.10 does "
                    "not record — on 3.10 this gate SKIPS, visibly, and never passes (research's R3(iii))")
def test_r13_the_pairing_oracle_finds_no_silent_answer_and_its_control_does():
    """Five assertions, and the last four are what make the first mean anything:
      * the resolver gives NO silent wrong answer (a wrong answer with nothing refused);
      * the POSITIVE CONTROL — this tree's resolver with round 12's comprehension order restored and the join check
        removed, built from the source text in-process — DOES give silent answers on the same programs, so the gate
        can fail (research's R3(ii));
      * the tied-signature programs are REACHED, counted from the PROGRAM (`is_tied`: equal signatures, different
        fingerprints) and never from the resolver's outcome — research's stage-2 B1: the first form counted join-check
        refusals, every one of which at these settings was an over-refusal of an UNTIED program, so turning the tied
        generators off left it met. Measured: 33/47/33 tied programs on 3.12/3.11/3.13 before round 19 made annotations
        roles, 41/50/41 after, and 0 with the tied generators off (measured before round 19, not re-measured since);
      * most programs are judged rather than refused, and many reads are checked — an oracle refusing everything, or
        judging nothing, would pass the first assertion vacuously;
      * the reads with no instruction position stay a small share (3.13's return annotations)."""
    po = _load("pairing_oracle_under_test", EVIDENCE / "pairing_oracle.py")
    got = po.run(_ORACLE_N, _ORACLE_SEED, sr)
    control = po.run(_ORACLE_N, _ORACLE_SEED, po.positive_control_resolver())
    assert got["SILENT"] == 0, f"the resolver gave {got['SILENT']} silent wrong answers: {dict(got)}"
    assert control["SILENT"] >= 10, f"the positive control is no longer a mutant the programs reach: {dict(control)}"
    assert got["TIED programs"] >= 20, f"the tied-signature programs are not reached: {dict(got)}"
    assert got["TIED programs SILENT"] == 0, f"a tied program was answered silently wrong: {dict(got)}"
    assert got["OK"] >= 0.6 * _ORACLE_N and got["reads checked"] >= 5000, f"the oracle judges too little: {dict(got)}"
    assert got["reads unmapped"] <= 0.05 * got["reads checked"], f"too many reads unjudged: {dict(got)}"
    # ROUND 19 (N5, the second seat's stage-1 read): ANNOTATIONS ARE ROLES the gate judges — a parameter's, a
    # keyword-only parameter's and the return's, on a module-level function AND on a method in a class body. The
    # NUMERATOR is measured per role (a role whose reads are never judged would pass the gate silently): each must
    # judge some reads on this interpreter, from the SAME run as the assertions above.
    roles = [f"{w} {r} annotation" for w in ("function", "method") for r in ("parameter", "keyword-only", "return")]
    judged = {role: got[(role, "judged")] for role in roles}
    assert all(n > 0 for n in judged.values()), judged
    # ...and the NAMED control: under `from __future__ import annotations` an annotation holds no load, so every read
    # in one must read "no instruction" — never judged, and so never "wrong".
    import collections
    import random
    fut = collections.Counter(); rng = random.Random(_ORACLE_SEED)
    for _ in range(60):
        src, _discarded, rl = po.program_with_roles(rng, future=True)
        fut[po.judge(sr, src, rl, fut)[0]] += 1
    assert fut["SILENT"] == 0, dict(fut)
    assert all(fut[(role, "judged")] == 0 for role in roles), {k: v for k, v in fut.items() if isinstance(k, tuple)}
    assert sum(fut[(role, "no instruction")] for role in roles) > 0, "the future control reached no annotation read"


def test_r13_s2d_1_the_s2c_2_refusal_walks_deep_into_the_first_iterable():
    """RESEARCH'S S2d-1: the S2c-2 refusal's DEEP walk is necessary and nothing pinned it (mutant FM4, a shallow walk,
    survived the suite). THE KILLING CELL IS NOT THE ONE FIRST PROPOSED, and the reason is measured: in
    `[u for t in list(v for v in {0 for u in [1]})]` the inner GENEXP's own first iterable is the inlinable setcomp, so
    the refusal fires one level down even under the shallow mutant — at this code both refuse it (3.12 and 3.13). The
    shape the deep walk alone reaches is an inlinable comprehension inside a CALL or a TUPLE in the first iterable,
    where no inner comprehension's own check fires. In a CLASS body `u = 'M'; class C: x = [u for t in
    list({0 for u in [1]})]` runs to ['M'] on 3.12 AND 3.13 while the unrefused resolver answers local: the deep walk
    refuses it, the shallow mutant resolves it wrong. (In a 3.12 FUNCTION body the interpreter itself raises
    UnboundLocalError — it also reads local there — which is research's W1b cell.)"""
    killing = "u = 'M'\nclass C:\n    x = [u for t in list({0 for u in [1]})]\n"
    research = "u = 'M'\ndef f():\n    return [u for t in list(v for v in {0 for u in [1]})]\n"
    shallow = _mutant("any(isinstance(n, _INLINABLE) for n in ast.walk(child.generators[0].iter))",
                      "isinstance(child.generators[0].iter, _INLINABLE)")
    if sys.version_info >= (3, 12):
        for body in (killing, research):
            with pytest.raises(sr.UnresolvableScope, match="S2c-2"):
                sr.Resolver(body, "<s2d1>")
        shallow.Resolver(killing, "<s2d1-shallow>")          # the mutant does NOT refuse the killing cell
    else:
        for body in (killing, research):
            sr.Resolver(body, "<s2d1>")

# ---- round 19 (N4): the comprehension signature is CPython's inlining rule, checked against symtable ------------------
# 3.12's symtable merges an inlined comprehension's name into the enclosing block ONLY IF THE BLOCK DOES NOT ALREADY HOLD
# IT (inline_comprehension, in the analysis pass). The first form merged every inlined target, so a genexp whose inner
# dictcomp's first iterable reads one of the dictcomp's own targets read a local symtable does not have, and a same-line
# pair was refused though the resolver would answer it rightly — ~4.5% of the oracle's programs on 3.12 and 3.13.
_R19_COMP_NAME = {ast.GeneratorExp: "genexpr", ast.ListComp: "listcomp", ast.SetComp: "setcomp", ast.DictComp: "dictcomp"}


def _r19_signature_disagreements(src: str, label: str) -> tuple:
    """For every comprehension block symtable reports, keyed by (line, block name): the multiset of its non-parameter
    locals against the multiset of the resolver's signatures for the AST nodes of that kind on that line. -> (the SET
    of disagreements, blocks compared, keys whose node and block counts differ)."""
    import collections
    import symtable
    blocks = collections.defaultdict(list)

    def walk(b):
        for c in b.get_children():
            if c.get_name() in _R19_COMP_NAME.values():
                blocks[(c.get_lineno(), c.get_name())].append(
                    tuple(sorted(s.get_name() for s in c.get_symbols() if s.is_local() and not s.is_parameter())))
            walk(c)
    walk(symtable.symtable(src, label, "exec"))
    nodes = collections.defaultdict(list)
    tree = ast.parse(src)
    # round 20: compared in the symbol table's (mangled) spelling; a module without the map (the round-19 pin) is
    # compared as it was, so a round-20 cell fails there on the defect rather than on a missing name
    private = sr._private_map(tree) if hasattr(sr, "_private_map") else None
    for n in ast.walk(tree):
        if type(n) in _R19_COMP_NAME:
            nodes[(n.lineno, _R19_COMP_NAME[type(n)])].append(n)
    bad, compared, ambiguous = set(), 0, 0
    for key, bl in blocks.items():
        ns = nodes.get(key, [])
        if len(ns) != len(bl):
            ambiguous += 1
            continue
        compared += len(bl)
        got = sorted(tuple(sorted(sr.Resolver._comprehension_signature(n, private.get(id(n))) if private is not None
                                  else sr.Resolver._comprehension_signature(n))) for n in ns)
        if got != sorted(bl):
            bad.add((label, key, tuple(sorted(bl)), tuple(got)))
    return bad, compared, ambiguous


def test_r19_the_comprehension_signature_equals_symtable_over_the_corpus():
    """The DIRECT acceptance (the second seat's round-19 stage-1 read, BLOCKING): the signature is a second
    implementation of symtable's rule, so ANY disagreement is a defect — over the pairing oracle's corpus (seed 13, 400
    programs) and every product and evidence module. The SET of disagreements must be empty; the count compared must
    be large, and no key may be skipped as ambiguous (a skipped key would be an unchecked one)."""
    import random
    po = _load("pairing_oracle_r19", EVIDENCE / "pairing_oracle.py")
    rng = random.Random(_ORACLE_SEED)
    sources = [(f"oracle#{i}", po.program(rng)[0]) for i in range(_ORACLE_N)]
    sources += [(str(p.relative_to(ROOT)), p.read_text())
                for p in sorted(list((ROOT / "src" / "veracium").rglob("*.py")) + list(EVIDENCE.glob("*.py")))]
    bad, compared, ambiguous = set(), 0, 0
    for label, src in sources:
        b, c, a = _r19_signature_disagreements(src, label)
        bad |= b; compared += c; ambiguous += a
    assert bad == set(), sorted(bad)[:5]
    assert ambiguous == 0 and compared >= 400, (compared, ambiguous)


def test_r19_n4_the_reproduction_resolves_on_every_version():
    """The over-refusal, as found: on 3.12 and 3.13 the first genexp's block holds `v` from its dictcomp's first
    iterable, as a global, and the old signature counted `v` as a merged local — the same-line pair was refused. The
    signature now equals symtable's locals, and the pair resolves; on 3.11 (no inlining) it always did."""
    src = "def f(a, b):\n    return (x for x in a if {k: v for k, v in [(v, 1)]}), (y for y in b)\n"
    assert _r19_signature_disagreements(src, "<n4>")[0] == set()
    sr.Resolver(src, "<n4>")


def test_r19_a_name_the_block_also_reads_is_not_merged():
    """The rule's other half, measured against symtable rather than predicted (dev's stage-1 plan predicted the
    opposite): the block reading `k` ANYWHERE — here after the inner comprehension — already holds it when inlining
    runs, so the listcomp's `k` is NOT merged as a local of the genexp."""
    src = "def f(a, b):\n    return (x for x in a if [k for k in b] and k)\n"
    assert _r19_signature_disagreements(src, "<k>")[0] == set()
    node = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.GeneratorExp))
    assert "k" not in sr.Resolver._comprehension_signature(node)


# ---- round 20: the ROUND-19 VERDICT'S F2 — names the COMPILER puts in a block, and names it SPELLS differently ---------
# A `super` load makes symtable add `__class__` to the block (no ast.Name for it), so `[__class__ for __class__ in b]`
# beside it is NOT merged; and inside a class every `__x` is `_Class__x` in the symbol table. The signature missed both,
# and the join check refused valid same-line pairs (loud over-refusals, never a silent wrong pairing). The reviewer's
# seven cells, the second seat's stage-1 cells (super in a function nested in a method, and in a lambda; mangling), and
# a generated corpus over the dimensions; each program must compile, match symtable, and RESOLVE.
_R20_G = "(x for x in a if {inner} and {outer}), (y for y in b)"


def _r20_fn(body):
    return "def f(a, b):\n    return " + body + "\n"


def _r20_meth(body, cls="C"):
    return f"class {cls}:\n    def m(self, a, b):\n        return " + body + "\n"


_R20_CELLS = [
    ("ordinary inner target, with super", _r20_fn(_R20_G.format(inner="[k for k in b]", outer="super"))),
    ("inner target __class__, without super", _r20_fn(_R20_G.format(inner="[__class__ for __class__ in b]", outer="a"))),
    ("inner target __class__, with a bare super (the verdict's witness)",
     _r20_fn(_R20_G.format(inner="[__class__ for __class__ in b]", outer="super"))),
    ("an explicit outer __class__ read as well",
     _r20_fn(_R20_G.format(inner="[__class__ for __class__ in b]", outer="super and __class__"))),
    ("the same generators on separate lines",
     "def f(a, b):\n    g = (x for x in a if [__class__ for __class__ in b] and super)\n    return g, (y for y in b)\n"),
    ("a method with a bare super", _r20_meth(_R20_G.format(inner="[__class__ for __class__ in b]", outer="super"))),
    ("a method calling super(C, self)",
     _r20_meth(_R20_G.format(inner="[__class__ for __class__ in b]", outer="super(C, self)"))),
    ("super in a function nested in a method",
     "class C:\n    def m(self, a, b):\n        def h():\n            return "
     + _R20_G.format(inner="[__class__ for __class__ in b]", outer="super") + "\n        return h\n"),
    ("super inside a lambda inside the generator (the lambda's block holds __class__, not the generator's)",
     _r20_fn(_R20_G.format(inner="[__class__ for __class__ in b]", outer="(lambda: super)"))),
    ("a class-private inner target in a method (spelled _C__p)", _r20_meth(_R20_G.format(inner="[__p for __p in b]", outer="a"))),
    ("a class-private outer read and inner target", _r20_meth(_R20_G.format(inner="[__p for __p in b]", outer="__p"))),
    ("a class named with underscores only: no mangling", _r20_meth(_R20_G.format(inner="[__p for __p in b]", outer="a"), cls="__")),
    ("same-line list comprehensions with a class-private target (the non-inlined path)",
     "class C:\n    def m(self, a, b):\n        return [__p for __p in a], [y for y in b]\n"),
    ("same-line lambdas with a class-private parameter",
     "class C:\n    def m(self):\n        return (lambda __p: __p), (lambda q: q)\n"),
    # the second seat's round-20 stage 2 (U5, U3), each reachable and each killing a mutant that survived the rest:
    ("super STORED as a target adds no __class__ (only a LOAD does)",
     "def f(a, b):\n    return (x for super in a if [__class__ for __class__ in b]), (y for y in b)\n"),
    ("a class decorator inside a method is mangled by the ENCLOSING class",
     "def dec(*a):\n    return lambda c: c\nclass C:\n    def m(self, a, b):\n"
     "        @dec((__p for __p in a), (__q for __q in b))\n        class D:\n            pass\n        return D\n"),
    ("a class's bases inside a method are mangled by the ENCLOSING class",
     "class C:\n    def m(self, a, b):\n        class D(*[(__p for __p in a), (__q for __q in b)] and [object]):\n"
     "            pass\n        return D\n"),
    ("a class's keywords inside a method are mangled by the ENCLOSING class",
     "class M(type):\n    def __new__(m, n, b, d, **k):\n        return super().__new__(m, n, b, d)\nclass C:\n"
     "    def m(self, a, b):\n        class D(metaclass=M, g=((__p for __p in a), (__q for __q in b))):\n"
     "            pass\n        return D\n"),
]


@pytest.mark.parametrize("cell,src", _R20_CELLS, ids=[c[0] for c in _R20_CELLS])
def test_r20_f2_compiler_names_and_mangling_match_symtable_and_resolve(cell, src):
    compile(src, "<r20>", "exec")
    assert _r19_signature_disagreements(src, "<r20>")[0] == set(), cell
    sr.Resolver(src, "<r20>")


def _r20_corpus():
    """The dimensions, crossed: the enclosing context x the inner comprehension's kind x its target x the outer read x
    the layout. Every program compiles; none depends on running zero-argument super."""
    contexts = {"function": _r20_fn, "method": _r20_meth, "method of a class named _C_": lambda b: _r20_meth(b, cls="_C_"),
                "function nested in a method": lambda b: (
                    "class C:\n    def m(self, a, b):\n        def h():\n            return " + b + "\n        return h\n")}
    kinds = {"list": "[{t} for {t} in b]", "set": "{{{t} for {t} in b}}", "dict": "{{{t}: 1 for {t} in b}}"}
    targets = ["k", "__class__", "__p", "__p__"]
    outers = ["a", "super", "super(C, self)", "__class__", "__p", "(lambda: super)"]
    out = []
    for cname, ctx in contexts.items():
        for kname, kind in kinds.items():
            for t in targets:
                for o in outers:
                    inner = kind.format(t=t)
                    one = ctx(f"(x for x in a if {inner} and {o}), (y for y in b)")
                    out.append((f"{cname}/{kname}/{t}/{o}/one line", one))
                    two = one.replace("), (y for y in b)", "),\\\n            (y for y in b)")
                    out.append((f"{cname}/{kname}/{t}/{o}/two lines", two))
    return out


def test_r20_f2_the_generated_corpus_equals_symtable_and_resolves():
    """Over every cross of the dimensions: the signature equals symtable's non-parameter locals for every comprehension
    block (no key skipped), and the resolver accepts every program — each same-line pair has distinct signatures, so a
    refusal here could only be the over-refusal this round fixes."""
    corpus = _r20_corpus()
    bad, compared, ambiguous, refused = set(), 0, 0, []
    for label, src in corpus:
        compile(src, label, "exec")
        b, c, a = _r19_signature_disagreements(src, label)
        bad |= b; compared += c; ambiguous += a
        try:
            sr.Resolver(src, label)
        except sr.UnresolvableScope as e:
            refused.append((label, str(e)[:80]))
    assert bad == set(), sorted(bad)[:5]
    assert refused == [], refused[:5]
    assert ambiguous == 0 and compared >= len(corpus), (compared, ambiguous, len(corpus))


@pytest.mark.parametrize("mutant", ["super adds nothing (the round-19 walk)", "no mangling (the round-19 spelling)"])
def test_r20_f2_each_superseded_rule_fails_the_corpus(mutant, monkeypatch):
    """Each half of the fix is load-bearing: with it removed, the corpus and cells above find a disagreement or a
    refusal on 3.12+ (on 3.10 and 3.11 nothing is inlined, so only the mangling half is visible there)."""
    if mutant.startswith("super"):
        if sys.version_info < (3, 12):
            pytest.skip("no comprehension is inlined before 3.12, so a held __class__ decides nothing there")
        monkeypatch.setattr(sr, "_IMPLICIT_IN_COMPREHENSION", {})
    else:
        monkeypatch.setattr(sr, "_mangle", lambda private, name: name)
    hits = 0
    for label, src in _r20_corpus() + _R20_CELLS:
        try:
            hits += bool(_r19_signature_disagreements(src, label)[0])
            sr.Resolver(src, label)
        except sr.UnresolvableScope:
            hits += 1
    assert hits > 0, mutant


def test_r20_f2_route_two_finds_no_implicit_name_route_one_lacks():
    """The second seat's route 2 (stage-1 read of round 20): over every stdlib module, a symbol whose name is never a
    NAME token in its module is compiler-introduced or mangled; every such name must be in route 1
    (_IMPLICIT_NAMES_ALL_BLOCKS, read from Python/symtable.c) or a mangled spelling of a token. Route 2 must also SEE
    `__class__` (the stdlib's functions read super), or the check has no teeth. ITS BLIND SPOT, named: no stdlib module
    triggers `__classdict__`, which only route 1 carries. THE STDLIB DIFFERS BY HOST: CI's carries Lib/test, a
    Debian build does not, and the first form passed here and failed on CI (c6b2620) on CPython's own non-ASCII
    identifier tests; R20_ROUTE_TWO_STDLIB points the census at any Lib/ (a CPython source tree's) to run it in full."""
    if sys.version_info < (3, 12):
        pytest.skip("before 3.12 tokenize returns an f-string as ONE token, so every name read inside one looks "
                    "compiler-introduced (measured: len, abs, repr on 3.10/3.11); the census is exact from 3.12 (PEP 701)")
    import collections
    import io
    import os
    import symtable
    import sysconfig
    import tokenize
    import unicodedata
    import warnings
    lib = pathlib.Path(os.environ.get("R20_ROUTE_TWO_STDLIB") or sysconfig.get_paths()["stdlib"])
    found = collections.Counter(); files = 0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for f in sorted(lib.rglob("*.py")):
            if "site-packages" in f.parts:
                continue
            try:
                src = f.read_text(encoding="utf-8")
                table = symtable.symtable(src, str(f), "exec")
                # NFKC, as the compiler normalises every identifier (PEP 3131): `µ` is `μ` in the symbol table, and
                # CPython's own Lib/test spells `Unicode` in mathematical fraktur (CI's full stdlib, not this box's)
                toks = {unicodedata.normalize("NFKC", t.string)
                        for t in tokenize.generate_tokens(io.StringIO(src).readline) if t.type == tokenize.NAME}
            except (SyntaxError, UnicodeDecodeError, ValueError, tokenize.TokenError):
                continue
            files += 1
            stack = [table]
            while stack:
                b = stack.pop(); stack.extend(b.get_children())
                for s in b.get_symbols():
                    n = s.get_name()
                    if n in toks:
                        continue
                    tail = "__" + n.split("__", 1)[1] if n.startswith("_") and "__" in n[1:] else None
                    found["<mangled>" if tail in toks else n] += 1
    assert files >= 300, files
    unknown = {n for n in found if n != "<mangled>"} - sr._IMPLICIT_NAMES_ALL_BLOCKS
    assert unknown == set(), (sorted(unknown), dict(found))
    assert found["__class__"] > 0, dict(found)


# The second seat's round-20 stage-2 survivors, as source substitutions at anchors that must match once: each mutant
# must REFUSE its killing cell above, which the shipped resolver answers (the cell's own test).
_R20_STAGE2_MUTANTS = [
    ("U5: super adds __class__ even when stored",
     "                if isinstance(x.ctx, ast.Load) and x.id in _IMPLICIT_IN_COMPREHENSION:",
     "                if x.id in _IMPLICIT_IN_COMPREHENSION:",
     "super STORED as a target adds no __class__ (only a LOAD does)"),
    ("U3: a class header mangled by the class's own name",
     "            for c in [*node.decorator_list, *node.bases, *node.keywords]:\n                visit(c, private)",
     "            for c in [*node.decorator_list, *node.bases, *node.keywords]:\n                visit(c, node.name)",
     "a class decorator inside a method is mangled by the ENCLOSING class"),
]


@pytest.mark.parametrize("mutant,anchor,replacement,killer", _R20_STAGE2_MUTANTS, ids=[m[0] for m in _R20_STAGE2_MUTANTS])
def test_r20_f2_the_stage_two_survivors_are_killed(mutant, anchor, replacement, killer, tmp_path):
    if mutant.startswith("U5") and sys.version_info < (3, 12):
        pytest.skip("no comprehension is inlined before 3.12, so a held __class__ decides nothing there")
    text = (EVIDENCE / "scope_resolution.py").read_text()
    assert text.count(anchor) == 1, (mutant, "the anchor moved")
    path = tmp_path / "scope_resolution_mutant.py"
    path.write_text(text.replace(anchor, replacement))
    mut = _load("scope_resolution_r20_stage2", path)
    src = dict(_R20_CELLS)[killer]
    sr.Resolver(src, "<shipped>")
    with pytest.raises(mut.UnresolvableScope):
        mut.Resolver(src, "<mutant>")
