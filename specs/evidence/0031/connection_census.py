"""The CONNECTION-ACQUISITION CENSUS — a standalone evidence module (round-7
F1's package feedback, taken, mirroring the joint arc's binding_census move).

The gate's seventh rung, and the ladder's terminal shape: rounds 4-6 taught
the census what a REFERENCE to `sqlite3.connect` is (name -> alias -> dynamic
-> parenthood); round 7 proved the question was wrong one level up — the
census equated CONNECTION ACQUISITION with one function's spelling, and the
reviewer opened working connections through `sqlite3.Connection(path)` (the
constructor, deliberately waved through by the round-6 "non-connect
attributes are harmless" rule) and `sqlite3.dbapi2.connect(path)` (the
submodule re-export). THE SURFACE IS NOW DEFINED POSITIVELY:

  * `sqlite3.connect` — the ONE blessed opener spelling, legal only as a
    direct call (parenthood, rounds 6's rule), counted into the inventory;
  * `sqlite3.Connection` — legal ONLY IN ANNOTATION POSITION (src/veracium
    uses it ten times, all type annotations); as a Call's func it is an
    OPENER and refuses; captured anywhere else it refuses (round 6's
    capture lesson applied at definition);
  * every other attribute of `sqlite3` must be in ALLOWED_ATTRS (exception
    classes, Row/Binary, version constants) or it REFUSES — unknown names
    (dbapi2 included) are refused-until-classified, never waved through;
  * a submodule import (`import sqlite3.dbapi2`, `from sqlite3.dbapi2
    import ...`) REFUSES — a second name for the same surface;
  * the bare-name and dynamic-acquisition rules of rounds 4-6 stand.

The runtime MATRIX (in the driver's tests) derives every opener spelling
from the interpreter itself — every sqlite3 attribute that IS the connect
function or the Connection class, one submodule level down included — and
asserts the census refuses each one except the blessed direct call, so a
future stdlib re-export fails loudly instead of quietly widening the
surface.
"""
import ast

#: Non-opening sqlite3 attributes the codebase may use freely. POSITIVE
#: surface: anything not listed here (and not the two special-cased names
#: above) refuses until a human classifies it into this list or the
#: inventory. Derived from src/veracium's actual usage plus the standard
#: exception hierarchy and constants; a new legitimate attribute is one
#: line here, reviewed.
#: THE PROTECTED IMPORT ORIGINS (round-10 F1's feedback, taken as the
#: reviewer asked: one structured table instead of rules distributed
#: between literal-name checks and annotation recursion). The census
#: classifies acquisition BY PROVENANCE from these modules, never by
#: searching text for a spelling — round 10's lesson: recursion is no
#: fail-closed floor if ENTERING it depends on the forbidden capability
#: keeping one spelling ("_sqlite3" opened connections invisibly).
PROTECTED_MODULES = {
    "sqlite3": "the public module — the blessed opener's home; every use "
               "governed by the positive surface below",
    "_sqlite3": "the underlying C extension — src/veracium has NO legal "
                "use (verified round 10); EVERY reference refuses: import, "
                "from-import, attribute, bare name, and any alias derived "
                "from it, in code and inside parsed string annotations",
}

ALLOWED_ATTRS = frozenset({
    "Error", "Warning", "DatabaseError", "DataError", "IntegrityError",
    "InterfaceError", "InternalError", "NotSupportedError",
    "OperationalError", "ProgrammingError",
    "Row", "Binary",
    "sqlite_version", "sqlite_version_info", "version", "version_info",
    "PARSE_DECLTYPES", "PARSE_COLNAMES",
    "complete_statement", "enable_callback_tracebacks", "register_adapter",
    "register_converter",
})


#: 3.12's `type` statement, absent from older parsers — the census must
#: RECOGNIZE it where the interpreter has it (availability is a parser
#: fact, the round-13 joint lesson) and cannot see it below 3.12, where
#: such sources are a SyntaxError before the census runs.
_TYPE_ALIAS = getattr(ast, "TypeAlias", None)


def _type_param_positions(node):
    """3.12 type-parameter bounds (and 3.13 defaults) are LAZILY
    evaluated annotation-like expressions — string-bearing positions the
    round-10 rules must visit, claimed here before a reviewer plants
    `type T[X: "sqlite3.Connection(':memory:')"] = int`."""
    for tp in getattr(node, "type_params", None) or []:
        for attr in ("bound", "default_value"):
            sub = getattr(tp, attr, None)
            if sub is not None:
                yield sub


def _annotation_nodes(tree):
    """Every node inside an annotation subtree — the positions where
    `sqlite3.Connection` names a TYPE rather than acquires a connection.

    The TypeAlias VALUE is one of these positions (the pre-round-11
    red-team seam, two-sided): `type T = sqlite3.Connection` is exactly
    the non-executing type reference the exemption exists to permit, and
    its string form defers evaluation the same way an annotation string
    does — so it is exempt as a reference, parsed as a string, and
    refused as a call, by the SAME rules, not a parallel set."""
    ann_roots = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            for arg in (a.posonlyargs + a.args + a.kwonlyargs
                        + ([a.vararg] if a.vararg else [])
                        + ([a.kwarg] if a.kwarg else [])):
                if arg.annotation is not None:
                    ann_roots.append(arg.annotation)
            if node.returns is not None:
                ann_roots.append(node.returns)
            ann_roots.extend(_type_param_positions(node))
        elif isinstance(node, ast.ClassDef):
            ann_roots.extend(_type_param_positions(node))
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            ann_roots.append(node.annotation)
        elif _TYPE_ALIAS is not None and isinstance(node, _TYPE_ALIAS):
            ann_roots.append(node.value)
            ann_roots.extend(_type_param_positions(node))
    ids = set()
    for root in ann_roots:
        for n in ast.walk(root):
            ids.add(id(n))
    return ids, ann_roots


def connect_census(source, rel):
    """The census over one source text. Returns {key: count}: inventory
    counts for blessed direct `sqlite3.connect(...)` calls under `rel`,
    and `[REFUSED: ...]` keys for every violation of the positive surface."""
    out = {}

    def bump(key):
        out[key] = out.get(key, 0) + 1

    tree = ast.parse(source)
    ann_ids, ann_roots = _annotation_nodes(tree)
    parent = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parent[c] = n
    # Aliases bound (by from-import) to PROTECTED-module objects: tracked so
    # parsed string annotations resolve them back to their provenance
    # (round-10 requirement 3/5 — an alias such as C retains the identity of
    # _sqlite3.Connection even though the import that minted it refused).
    protected_aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module \
                and (node.module.split(".")[0] in PROTECTED_MODULES):
            root = node.module.split(".")[0]
            for alias in node.names:
                protected_aliases[alias.asname or alias.name] = (
                    node.module, alias.name)
            bump(rel + f" [REFUSED: from-import of protected module "
                       f"{node.module!r}]")
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root == "_sqlite3":
                    bump(rel + " [REFUSED: import of _sqlite3 — the "
                               "underlying C extension has no legal use "
                               "(round-10: it opens connections without "
                               "the public spelling)]")
                elif alias.name == "sqlite3" and alias.asname:
                    bump(rel + " [REFUSED: aliased sqlite3]")
                elif alias.name.startswith("sqlite3."):
                    bump(rel + " [REFUSED: sqlite3 submodule import — a "
                               "second name for the connection surface]")
        if isinstance(node, ast.Call):
            fn = node.func
            is_dunder = isinstance(fn, ast.Name) and fn.id == "__import__"
            is_implib = (isinstance(fn, ast.Attribute)
                         and fn.attr == "import_module")
            if is_dunder or is_implib:
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and (
                        arg.value == "sqlite3"
                        or (isinstance(arg.value, str)
                            and arg.value.startswith("sqlite3."))):
                    bump(rel + " [REFUSED: dynamic acquisition of sqlite3]")
                elif not (isinstance(arg, ast.Constant)
                          and isinstance(arg.value, str)):
                    bump(rel + " [REFUSED: non-literal dynamic import — "
                               "cannot be ruled out as sqlite3]")
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "sqlite3"):
            par = parent.get(node)
            if node.attr == "connect":
                if not (isinstance(par, ast.Call) and par.func is node):
                    bump(rel + " [REFUSED: sqlite3.connect referenced "
                               "without being called — captured/passed/"
                               "assigned indirection defeats the inventory]")
            elif node.attr == "Connection":
                # ROUND-8 F1 — the eighth rung, found where attack point #4
                # invited: the round-7 exemption tested syntactic LOCATION
                # (anywhere beneath an annotation root) instead of
                # type-reference STRUCTURE, and annotations are ordinary
                # expressions evaluated at def time — the reviewer's
                # `def f(value: sqlite3.Connection(":memory:")):` opened a
                # REAL connection that lived in f.__annotations__. The
                # reviewer's safer formulation, taken exactly: opening
                # CALLS are processed BEFORE any annotation exemption, and
                # the exemption then admits only non-executing
                # type-reference structure — a Connection that is any part
                # of a Call inside an annotation (its func, OR an argument
                # handed to an evaluating callee: the next mutant over,
                # refused before it is planted) is not a type reference.
                if isinstance(par, ast.Call) and par.func is node:
                    bump(rel + " [REFUSED: sqlite3.Connection constructed "
                               "directly — the constructor is an opener "
                               "(round-7: it makes usable connections; "
                               "round-8: annotation ancestry exempts "
                               "nothing that CALLS) and only the blessed "
                               "opener acquires]")
                elif id(node) in ann_ids:
                    if isinstance(par, ast.Call):
                        bump(rel + " [REFUSED: sqlite3.Connection passed "
                                   "into a call inside an annotation — an "
                                   "evaluating callee can open with it; a "
                                   "type reference is never a call "
                                   "participant]")
                    else:
                        pass                 # a non-executing TYPE reference
                else:
                    bump(rel + " [REFUSED: sqlite3.Connection captured "
                               "outside annotation position]")
            elif node.attr not in ALLOWED_ATTRS:
                bump(rel + f" [REFUSED: unclassified sqlite3 attribute "
                           f"{node.attr!r} — the surface is positive; "
                           f"classify it or it refuses]")
        elif isinstance(node, ast.Name) and node.id == "_sqlite3" \
                and isinstance(node.ctx, ast.Load):
            bump(rel + " [REFUSED: reference to _sqlite3 — the underlying "
                       "C extension has no legal use in any position]")
        elif isinstance(node, ast.Name) and node.id == "sqlite3" \
                and isinstance(node.ctx, ast.Load):
            par = parent.get(node)
            if not (isinstance(par, ast.Attribute) and par.value is node):
                bump(rel + " [REFUSED: bare sqlite3 module reference — the "
                           "module escaping any attribute access cannot be "
                           "classified]")
        if (isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "sqlite3"
                and node.attr == "connect"
                and isinstance(parent.get(node), ast.Call)
                and parent[node].func is node):
            bump(rel)
    # ROUND-9 F1 — THE NINTH RUNG, found where the round-9 attack point #2
    # pointed: a STRING annotation defers execution past this census
    # (`def f(value: "sqlite3.Connection(':memory:')")` looked inert here
    # and get_type_hints evaluated it into a live connection). The contract
    # says NON-EXECUTING; a string whose structure cannot be established is
    # not provably non-executing, so (the reviewer's option 1 + fail-closed):
    # every string in annotation position that MENTIONS sqlite3 is PARSED
    # as an expression and the same positive-surface rules apply
    # recursively — Connection legal only outside any Call, connect never a
    # type, unknown attributes refused, bare module refused — and a string
    # that cannot be parsed, or is dynamically ASSEMBLED (f-string,
    # concatenation) with any fragment mentioning sqlite3, FAILS CLOSED:
    # safety that cannot be established is not exempted. Strings that never
    # mention sqlite3 are outside this surface and stay untouched.
    def _string_annotation_rules(expr_tree):
        eparent = {}
        for n in ast.walk(expr_tree):
            for c in ast.iter_child_nodes(n):
                eparent[c] = n
        for n in ast.walk(expr_tree):
            if (isinstance(n, ast.Attribute)
                    and isinstance(n.value, ast.Name)
                    and n.value.id in PROTECTED_MODULES):
                mod = n.value.id
                par = eparent.get(n)
                if mod == "_sqlite3":
                    bump(rel + " [REFUSED: string annotation referencing "
                               "_sqlite3 — no legal use in any position]")
                elif n.attr == "Connection":
                    if isinstance(par, ast.Call):
                        bump(rel + " [REFUSED: string annotation whose "
                                   "parsed structure makes sqlite3."
                                   "Connection a call participant — the "
                                   "deferred constructor executes when the "
                                   "annotation is resolved (round-9)]")
                elif n.attr == "connect":
                    bump(rel + " [REFUSED: string annotation referencing "
                               "sqlite3.connect — an opener is never a "
                               "type]")
                elif n.attr not in ALLOWED_ATTRS:
                    bump(rel + f" [REFUSED: string annotation with "
                               f"unclassified sqlite3 attribute "
                               f"{n.attr!r}]")
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                # ROUND-10 requirement 5: names inside parsed strings
                # resolve against PROTECTED import bindings — an alias
                # such as C retains the identity of _sqlite3.Connection,
                # so its use in a deferred expression refuses by
                # PROVENANCE, whatever it is spelled.
                if n.id in protected_aliases:
                    src_mod, src_name = protected_aliases[n.id]
                    bump(rel + f" [REFUSED: string annotation using "
                               f"{n.id!r}, an alias of "
                               f"{src_mod}.{src_name} — protected "
                               f"provenance, not a type reference]")
                elif n.id in PROTECTED_MODULES and n.id == "_sqlite3":
                    bump(rel + " [REFUSED: string annotation referencing "
                               "_sqlite3 — no legal use in any position]")
                elif n.id == "sqlite3":
                    par = eparent.get(n)
                    if not (isinstance(par, ast.Attribute)
                            and par.value is n):
                        bump(rel + " [REFUSED: string annotation with a "
                                   "bare sqlite3 module reference]")
            if isinstance(n, ast.Call):
                fn = n.func
                is_dunder = isinstance(fn, ast.Name) and fn.id == "__import__"
                is_implib = (isinstance(fn, ast.Attribute)
                             and fn.attr == "import_module")
                if is_dunder or is_implib:
                    arg = n.args[0] if n.args else None
                    if isinstance(arg, ast.Constant) \
                            and isinstance(arg.value, str) \
                            and arg.value.split(".")[0] in PROTECTED_MODULES:
                        bump(rel + " [REFUSED: string annotation "
                                   "dynamically importing a protected "
                                   "module]")
                    elif not (isinstance(arg, ast.Constant)
                              and isinstance(arg.value, str)):
                        # ROUND-10 requirement 6: a COMPUTED module name in
                        # a deferred expression ('sql'+'ite3') cannot be
                        # statically ruled out as SQLite — fail closed.
                        bump(rel + " [REFUSED: computed dynamic import "
                                   "inside a string annotation — the "
                                   "module cannot be ruled out as SQLite; "
                                   "failing closed]")

    # ROUND-10 F1: EVERY string in annotation position is parsed —
    # entering the recursion no longer depends on the forbidden capability
    # keeping one spelling (the round-10 lesson; "_sqlite3"-through-alias
    # acquired invisibly under the substring trigger). A string that
    # cannot parse cannot have its inertness established and FAILS
    # CLOSED, whatever it mentions; a parseable string referencing
    # nothing protected is inert and untouched.
    for root in ann_roots:
        for n in ast.walk(root):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                try:
                    sub = ast.parse(n.value, mode="eval")
                except SyntaxError:
                    bump(rel + " [REFUSED: unparseable string annotation "
                               "— inertness cannot be established, "
                               "failing closed (round-10: refusal no "
                               "longer requires a spelling)]")
                    continue
                _string_annotation_rules(sub)
            elif isinstance(n, (ast.JoinedStr, ast.BinOp)):
                frags = [c.value for c in ast.walk(n)
                         if isinstance(c, ast.Constant)
                         and isinstance(c.value, str)]
                if frags:
                    bump(rel + " [REFUSED: dynamically assembled string "
                               "annotation — the assembled text cannot be "
                               "statically established as inert, failing "
                               "closed (round-10: no spelling trigger)]")
    return out
