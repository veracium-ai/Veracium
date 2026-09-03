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

#: THE CAPABILITY-DISCOVERY FORMS INVENTORY (renamed at round 12 on the
#: reviewer's feedback — "module-access forms" named the round-11 class;
#: the round-12 class, NAMESPACE MAPPINGS, showed the real subject is
#: every route by which running code can DISCOVER a capability it did
#: not import: module registries, namespace mappings, frames, loaders,
#: and future equivalent carriers). Originally round-11 F1 — the ELEVENTH RUNG:
#: the census recognized only import syntax and two dynamic-import
#: spellings, and `sys.modules["sqlite3"]` — the interpreter's own module
#: registry, a STANDARD alternate access form — obtained the capability
#: uncounted; so did a from-imported `import_module` under any local
#: name, `importlib.reload`, and introspective `vars(sys)` access).
#: The reviewer's feedback taken as asked: the supported forms are
#: EXPLICITLY ENUMERATED here and MECHANICALLY CHECKED — every entry
#: must have a probe in the permanent battery naming it (the causal-
#: coverage move applied to module access), and any machinery form
#: OUTSIDE this enumeration is REJECTED CONSERVATIVELY, so the
#: completeness claim is exactly as wide as this table and no wider.
CAPABILITY_DISCOVERY_FORMS = {
    "static-import": "import M / import M as A / from M import n as A — "
                     "HANDLED by provenance (protected modules refuse; "
                     "aliases tracked)",
    "dunder-import": "__import__(name) — HANDLED: literal unprotected "
                     "name allowed, protected or non-literal refused, "
                     "and an UNCALLED reference to __import__ refuses "
                     "(a captured module-returning capability)",
    "import-module": "importlib.import_module, as an attribute OR "
                     "from-imported under ANY local name — HANDLED: same "
                     "argument rules as __import__; uncalled references "
                     "refuse",
    "sys-modules-registry": "sys.modules (subscript or .get, through any "
                            "alias of sys) — HANDLED: a literal "
                            "unprotected key is allowed, a protected or "
                            "non-literal key refuses, and ANY other use "
                            "of the registry object (aliasing, "
                            "iteration, passing) refuses — the registry "
                            "escaping analysis IS the capability "
                            "escaping analysis",
    "from-sys-modules": "from sys import modules [as X] — REFUSED at the "
                        "import; the bound name is tracked and every use "
                        "refuses",
    "importlib-machinery": "any importlib attribute beyond import_module "
                           "(util, reload, machinery, resources, ...) — "
                           "REFUSED conservatively: unknown machinery "
                           "forms are outside the enumerated claim. "
                           "EXEMPT: importlib.metadata, by what it "
                           "CANNOT do — it reads distribution metadata "
                           "and returns no module (three legitimate src "
                           "uses)",
    "introspective-machinery": "vars(X) / getattr(X, ...) / X.__dict__ "
                               "where X is sys or importlib (or an alias) "
                               "— REFUSED conservatively: an "
                               "introspective read of the interpreter's "
                               "module machinery cannot be ruled out as "
                               "registry access",
    "dynamic-evaluation": "eval(...) / exec(...) — REFUSED "
                          "conservatively: evaluated text can reach any "
                          "machinery form above (src has no use; the "
                          "floor costs nothing)",
    "machinery-modules": "import of pkgutil / runpy / zipimport / ctypes "
                         "/ builtins / inspect / gc / __main__ / pickle / "
                         "marshal / shelve / pydoc / code / codeop / "
                         "unittest / doctest — REFUSED conservatively at "
                         "the import: each can load modules, reach "
                         "frames or namespaces, or unpickle an import "
                         "by spellings of its own (pkgutil.resolve_name, "
                         "runpy.run_module, inspect.currentframe, "
                         "gc.get_objects, pickle.loads, pydoc.locate, "
                         "mock.patch's dotted resolution, ...); src has "
                         "no legitimate use of any (verified rounds "
                         "11-12), and refusing the module wholesale is "
                         "cheaper and stronger than enumerating its "
                         "surface. builtins carries __import__ under its "
                         "own roof; __builtins__ as a bare name refuses "
                         "too",
    "namespace-mappings": "globals() / locals() / vars() with no argument "
                          "— the round-12 route: the current namespace "
                          "mapping carries __builtins__ — HANDLED like "
                          "the module registry: a keyed lookup "
                          "(subscript or .get) with a LITERAL key that "
                          "is provably harmless (not a dunder, not a "
                          "protected or machinery module name) is "
                          "allowed; a dunder or otherwise unsafe literal "
                          "key, a non-literal key, and the mapping "
                          "escaping any keyed lookup (aliased, passed, "
                          "iterated) all refuse; inside a deferred type "
                          "expression the call itself refuses",
    "frame-introspection": "attributes that BY DOCUMENTED SEMANTICS carry "
                           "a namespace, a frame, or a loader, on ANY "
                           "base — f_globals f_locals f_builtins f_back "
                           "tb_frame gi_frame cr_frame ag_frame "
                           "__globals__ __builtins__ __dict__ __loader__ "
                           "__spec__ __subclasses__ — REFUSED "
                           "conservatively, as are sys._getframe and "
                           "sys._current_frames; getattr() with such a "
                           "name as a literal refuses, and getattr() "
                           "with a NON-literal name refuses unless the "
                           "base is `self` or `cls` (an instance or "
                           "class of the enclosing scope, which cannot "
                           "be a module, frame, or mapping — exempt BY "
                           "WHAT IT CANNOT BE; the one src use). "
                           "exc.__traceback__ itself stays allowed (one "
                           "legitimate src formatting use) — the "
                           "discovery step is tb_frame, and that "
                           "refuses. An __mro__ walk and dir() are "
                           "inert by what they cannot do: classes and "
                           "names, not namespaces",
    "captured-primitive": "a discovery PRIMITIVE — getattr, __import__, "
                          "import_module (any local name), eval, exec, "
                          "compile, vars, globals, locals — referenced as "
                          "a bare VALUE rather than as the func of a call "
                          "(passed to functools.partial, aliased, stored, "
                          "handed to map/reduce/a default argument) — "
                          "REFUSED: capturing the primitive IS the "
                          "violation, whoever the courier is, so no "
                          "currying vehicle ever needs a row (round-12, "
                          "research's red-team; the round-6 captured-"
                          "opener lesson generalized). Principle: a "
                          "refused name does not become permitted by "
                          "becoming a value",
    "accessor-constructors": "operator.attrgetter / methodcaller / "
                             "itemgetter (attribute form, or from-"
                             "imported under any local name) — these "
                             "MINT an accessor from a string, so the "
                             "captured-primitive rule cannot see them — "
                             "HANDLED with the getattr name rules: a "
                             "dunder, frame-attribute, unsafe, or "
                             "non-literal argument refuses; a benign "
                             "literal is clean (operator has a large "
                             "legitimate surface, so wholesale refusal "
                             "would be the builtins false-fire shape "
                             "without the zero-cost receipt). itemgetter "
                             "against an ESCAPED mapping needs nothing: "
                             "the escape already refused upstream",
}

#: The discovery primitives (round-12): each is a door when CALLED under
#: its own rules, and a captured door when referenced as a value.
DISCOVERY_PRIMITIVES = frozenset({
    "getattr", "__import__", "eval", "exec", "compile",
    "vars", "globals", "locals",
})

#: Attributes whose documented semantics carry a namespace, a frame, or a
#: loader (round-12): reaching one is the discovery step, whatever the
#: base. __closure__ is deliberately absent — cells hold arbitrary objects,
#: not a namespace — and __traceback__ is absent because the traceback is
#: not the frame: tb_frame is, and it is here.
FRAME_ATTRS = frozenset({
    "f_globals", "f_locals", "f_builtins", "f_back", "tb_frame", "gi_frame",
    "cr_frame", "ag_frame", "__globals__", "__builtins__", "__dict__",
    "__loader__", "__spec__", "__subclasses__",
})

#: The no-argument namespace-mapping calls (round-12).
NAMESPACE_CALLS = frozenset({"globals", "locals", "vars"})

#: The machinery-modules class (round-11, the class exhausted rather than
#: the named form fixed): stdlib modules that can produce modules or the
#: raw capability by spellings of their own. Refused at the import, like
#: _sqlite3 — no per-attribute surface to lag.
MACHINERY_MODULES = frozenset({"pkgutil", "runpy", "zipimport", "ctypes",
                               "builtins", "inspect", "gc", "__main__",
                               "pickle", "marshal", "shelve", "pydoc",
                               "code", "codeop", "unittest", "doctest"})


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


def _harmless_literal_key(key):
    """A LITERAL mapping key that is provably harmless (round-12): a str
    that is not a dunder (the builtins facility and every loader live
    under dunder names) and names no protected or machinery module."""
    return (isinstance(key, ast.Constant) and isinstance(key.value, str)
            and not key.value.startswith("__")
            and key.value.split(".")[0] not in PROTECTED_MODULES
            and key.value.split(".")[0] not in MACHINERY_MODULES)


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
    # ROUND-11 F1 pre-pass: the names through which the interpreter's
    # module machinery is reachable in THIS source. Collected before the
    # rules run so an alias never outruns its rule.
    sys_names = {"sys"}
    importlib_names = {"importlib"}
    module_returning_fns = {"__import__"}
    registry_names = set()          # locals bound by `from sys import modules`
    getter_names = set()            # locals bound to operator.attrgetter/methodcaller
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in MACHINERY_MODULES:
                    bump(rel + f" [REFUSED: import of machinery module "
                               f"{alias.name!r} — can load modules or the "
                               f"raw capability by its own spellings; "
                               f"outside the enumerated forms "
                               f"(round-11)]")
                elif alias.name == "sys" and alias.asname:
                    sys_names.add(alias.asname)
                elif alias.name == "importlib" and alias.asname:
                    importlib_names.add(alias.asname)
                elif alias.name.split(".")[0] == "importlib" \
                        and alias.name != "importlib" \
                        and alias.name != "importlib.metadata":
                    bump(rel + f" [REFUSED: import of importlib machinery "
                               f"submodule {alias.name!r} — outside the "
                               f"enumerated capability-discovery forms "
                               f"(round-11); importlib.metadata is the "
                               f"one exempt leaf]")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in MACHINERY_MODULES:
                bump(rel + f" [REFUSED: from-import of machinery module "
                           f"{node.module!r} — outside the enumerated "
                           f"forms (round-11)]")
            elif node.module == "sys":
                for alias in node.names:
                    if alias.name == "modules":
                        registry_names.add(alias.asname or alias.name)
                        bump(rel + " [REFUSED: from sys import modules — "
                                   "the module registry bound to a local "
                                   "name (round-11: the registry escaping "
                                   "analysis is the capability escaping "
                                   "analysis)]")
            elif node.module == "operator":
                for alias in node.names:
                    if alias.name in ("attrgetter", "methodcaller",
                                      "itemgetter"):
                        getter_names.add(alias.asname or alias.name)
            elif node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        module_returning_fns.add(alias.asname or alias.name)
                    elif alias.name == "metadata":
                        pass          # exempt by what it cannot do
                    else:
                        bump(rel + f" [REFUSED: from importlib import "
                                   f"{alias.name} — machinery beyond "
                                   f"import_module is outside the "
                                   f"enumerated forms (round-11)]")
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
            # ROUND-11: a module-returning capability is the capability,
            # whatever its local spelling — __import__ AND import_module
            # from-imported under any name (the eleventh rung's aliased
            # form) get the same argument rules.
            is_modfn = (isinstance(fn, ast.Name)
                        and fn.id in module_returning_fns)
            is_implib = (isinstance(fn, ast.Attribute)
                         and fn.attr == "import_module")
            if is_modfn or is_implib:
                arg = node.args[0] if node.args else None
                if isinstance(arg, ast.Constant) and isinstance(
                        arg.value, str) and (
                        arg.value.split(".")[0] in PROTECTED_MODULES):
                    bump(rel + " [REFUSED: dynamic acquisition of a "
                               "protected module]")
                elif not (isinstance(arg, ast.Constant)
                          and isinstance(arg.value, str)):
                    bump(rel + " [REFUSED: non-literal dynamic import — "
                               "cannot be ruled out as a protected "
                               "module]")
            elif (isinstance(fn, ast.Name)
                    and fn.id in ("eval", "exec", "compile")):
                bump(rel + " [REFUSED: dynamic evaluation — evaluated or "
                           "compiled text can reach any capability-"
                           "discovery form; outside the enumerated claim "
                           "(round-11; compile added round-12: "
                           "FunctionType(code, globals) runs it without "
                           "exec)]")
            elif (isinstance(fn, ast.Name) and fn.id in ("vars", "getattr")
                    and node.args
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id in (sys_names | importlib_names)):
                bump(rel + " [REFUSED: introspective access to interpreter "
                           "module machinery — cannot be ruled out as "
                           "registry access (round-11)]")
            elif (isinstance(fn, ast.Name) and fn.id in NAMESPACE_CALLS
                    and not node.args):
                # ROUND-12 F1 — THE TWELFTH RUNG: the current namespace
                # mapping carries __builtins__; the registry rules apply.
                par = parent.get(node)
                gpar = parent.get(par) if par is not None else None
                keyed, key = False, None
                if isinstance(par, ast.Subscript) and par.value is node:
                    keyed, key = True, par.slice
                elif (isinstance(par, ast.Attribute) and par.value is node
                      and par.attr == "get" and isinstance(gpar, ast.Call)
                      and gpar.func is par):
                    keyed, key = True, (gpar.args[0] if gpar.args else None)
                if keyed:
                    if not _harmless_literal_key(key):
                        bump(rel + f" [REFUSED: {fn.id}() namespace "
                                   f"mapping keyed by a dunder, unsafe, "
                                   f"or non-literal key — the mapping "
                                   f"carries __builtins__ (round-12, the "
                                   f"twelfth rung)]")
                else:
                    bump(rel + f" [REFUSED: {fn.id}() namespace mapping "
                               f"escaping a keyed lookup — aliased, "
                               f"passed, or iterated, the mapping IS the "
                               f"capability escaping analysis "
                               f"(round-12)]")
            elif ((isinstance(fn, ast.Name) and fn.id in getter_names
                   and node.args)
                  or (isinstance(fn, ast.Attribute)
                      and fn.attr in ("attrgetter", "methodcaller",
                                      "itemgetter")
                      and isinstance(fn.value, ast.Name)
                      and fn.value.id == "operator" and node.args)):
                # ROUND-12 ACCESSOR-CONSTRUCTOR RULE (research's red-team,
                # the row's shape theirs): these MINT an accessor from a
                # string — getattr's name rules, with no base to exempt.
                name_arg = node.args[0]
                if not (isinstance(name_arg, ast.Constant)
                        and isinstance(name_arg.value, str)) \
                        or name_arg.value.startswith("__") \
                        or name_arg.value.split(".")[0] in FRAME_ATTRS \
                        or any(part in FRAME_ATTRS or part.startswith("__")
                               for part in name_arg.value.split(".")):
                    bump(rel + " [REFUSED: operator accessor constructor "
                               "(attrgetter/methodcaller/itemgetter) with "
                               "a dunder, frame-attribute, or non-literal "
                               "name — an accessor minted from a string "
                               "(round-12)]")
            elif (isinstance(fn, ast.Name) and fn.id == "getattr"
                    and len(node.args) >= 2):
                name_arg = node.args[1]
                base = node.args[0]
                if isinstance(name_arg, ast.Constant) \
                        and isinstance(name_arg.value, str):
                    if name_arg.value.startswith("__") \
                            or name_arg.value in FRAME_ATTRS:
                        bump(rel + f" [REFUSED: getattr with the dunder/"
                                   f"frame name {name_arg.value!r} — a "
                                   f"spelling of attribute-based "
                                   f"discovery (round-12)]")
                elif not (isinstance(base, ast.Name)
                          and base.id in ("self", "cls")):
                    bump(rel + " [REFUSED: getattr with a non-literal "
                               "name on a base that could be a module, "
                               "frame, or mapping — safety cannot be "
                               "established (round-12; self/cls exempt "
                               "by what they cannot be)]")
        # ROUND-12 CAPTURED-PRIMITIVE RULE (research's red-team; the
        # round-6 captured-opener lesson generalized): a discovery
        # primitive referenced as a bare VALUE — not the func of a call —
        # refuses, whoever the courier is (partial, map, reduce, aliasing,
        # a default argument). A refused name does not become permitted
        # by becoming a value.
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                and node.id in (DISCOVERY_PRIMITIVES | module_returning_fns):
            par = parent.get(node)
            if not (isinstance(par, ast.Call) and par.func is node):
                bump(rel + f" [REFUSED: discovery primitive {node.id!r} "
                           f"referenced as a value without being called "
                           f"— a captured capability; the courier is "
                           f"irrelevant (round-12)]")
        # ROUND-11: __builtins__ is the same door with no import at all.
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                and node.id == "__builtins__":
            bump(rel + " [REFUSED: __builtins__ reference — carries "
                       "__import__ with no import statement; outside the "
                       "enumerated forms (round-11)]")
        # ROUND-11: uses of a name bound by `from sys import modules`.
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                and node.id in registry_names:
            bump(rel + f" [REFUSED: use of {node.id!r}, a binding of the "
                       f"module registry (round-11)]")
        # ROUND-12: attributes that carry a namespace/frame/loader refuse
        # on ANY base — the discovery step is the attribute, whatever holds
        # it (a function's __globals__, a traceback's tb_frame, a
        # generator's gi_frame, a module's __dict__/__loader__, a class's
        # __subclasses__).
        if isinstance(node, ast.Attribute) and node.attr in FRAME_ATTRS:
            bump(rel + f" [REFUSED: .{node.attr} — an attribute that "
                       f"carries a namespace, frame, or loader by its "
                       f"documented semantics; reaching it is the "
                       f"capability-discovery step (round-12)]")
        # ROUND-11: the sys.modules REGISTRY and the machinery floor.
        if isinstance(node, ast.Attribute) \
                and isinstance(node.value, ast.Name):
            base = node.value.id
            if base in sys_names:
                if node.attr in ("_getframe", "_current_frames"):
                    bump(rel + f" [REFUSED: sys.{node.attr} — frame "
                               f"access reaches every namespace mapping "
                               f"(round-12)]")
                elif node.attr == "modules":
                    par = parent.get(node)
                    gpar = parent.get(par) if par is not None else None
                    key = None
                    keyed = False
                    if isinstance(par, ast.Subscript) and par.value is node:
                        keyed = True
                        key = par.slice
                    elif (isinstance(par, ast.Attribute)
                          and par.value is node and par.attr == "get"
                          and isinstance(gpar, ast.Call)
                          and gpar.func is par):
                        keyed = True
                        key = gpar.args[0] if gpar.args else None
                    if keyed:
                        if isinstance(key, ast.Constant) and isinstance(
                                key.value, str) and (
                                key.value.split(".")[0]
                                not in PROTECTED_MODULES):
                            pass      # a literal, provably unprotected key
                        else:
                            bump(rel + " [REFUSED: sys.modules access "
                                       "with a protected or non-literal "
                                       "key — the interpreter's registry "
                                       "is a standard module-access form "
                                       "(round-11, the eleventh rung)]")
                    else:
                        bump(rel + " [REFUSED: sys.modules used outside "
                                   "a keyed lookup — the registry "
                                   "escaping analysis is the capability "
                                   "escaping analysis (round-11)]")
                elif node.attr == "__dict__":
                    bump(rel + " [REFUSED: introspective access to "
                               "interpreter module machinery — cannot be "
                               "ruled out as registry access (round-11)]")
            elif base in importlib_names:
                par = parent.get(node)
                if node.attr == "import_module":
                    if not (isinstance(par, ast.Call)
                            and par.func is node):
                        bump(rel + " [REFUSED: importlib.import_module "
                                   "referenced without being called — a "
                                   "captured module-returning capability "
                                   "(round-11)]")
                elif node.attr == "metadata":
                    pass              # exempt by what it cannot do
                elif node.attr == "__dict__":
                    bump(rel + " [REFUSED: introspective access to "
                               "interpreter module machinery — cannot be "
                               "ruled out as registry access (round-11)]")
                else:
                    bump(rel + f" [REFUSED: importlib.{node.attr} — "
                               f"machinery beyond import_module is "
                               f"outside the enumerated module-access "
                               f"forms; rejected conservatively "
                               f"(round-11)]")
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
            if (isinstance(n, ast.Attribute)
                    and isinstance(n.value, ast.Name)
                    and n.value.id in sys_names
                    and n.attr in ("modules", "__dict__")):
                # ROUND-11, one level down (the rungs-9/10 lesson — the
                # surface applies recursively): the registry reached from
                # inside a deferred expression is the registry.
                bump(rel + " [REFUSED: string annotation reaching the "
                           "interpreter module registry (round-11)]")
            elif (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                    and n.id in ("builtins", "__builtins__")):
                bump(rel + " [REFUSED: string annotation reaching "
                           "builtins — carries __import__; deferred use "
                           "of the door (round-11)]")
            elif (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                    and n.id in (module_returning_fns - {"__import__"})
                    | registry_names):
                bump(rel + f" [REFUSED: string annotation using "
                           f"{n.id!r}, a module-returning or registry "
                           f"binding — deferred use of the capability "
                           f"(round-11)]")
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) \
                    and n.id in (DISCOVERY_PRIMITIVES | module_returning_fns):
                par_ = eparent.get(n)
                if not (isinstance(par_, ast.Call) and par_.func is n):
                    bump(rel + f" [REFUSED: discovery primitive {n.id!r} "
                               f"captured as a value inside a string "
                               f"annotation (round-12)]")
            if isinstance(n, ast.Attribute) and n.attr in FRAME_ATTRS:
                bump(rel + f" [REFUSED: .{n.attr} inside a string "
                           f"annotation — a namespace/frame/loader "
                           f"attribute in a deferred expression "
                           f"(round-12)]")
            if isinstance(n, ast.Call):
                fn = n.func
                is_dunder = isinstance(fn, ast.Name) and fn.id == "__import__"
                is_implib = (isinstance(fn, ast.Attribute)
                             and fn.attr == "import_module")
                if isinstance(fn, ast.Name) \
                        and fn.id in ("eval", "exec", "compile"):
                    bump(rel + " [REFUSED: dynamic evaluation inside a "
                               "string annotation (round-11)]")
                if isinstance(fn, ast.Name) and fn.id in NAMESPACE_CALLS \
                        and not n.args:
                    bump(rel + " [REFUSED: namespace mapping reached "
                               "inside a string annotation — deferred "
                               "use of the mapping (round-12)]")
                if isinstance(fn, ast.Name) and fn.id == "getattr":
                    bump(rel + " [REFUSED: getattr inside a string "
                               "annotation — attribute discovery in a "
                               "deferred expression (round-12)]")
                if (isinstance(fn, ast.Name) and fn.id in getter_names) or (
                        isinstance(fn, ast.Attribute)
                        and fn.attr in ("attrgetter", "methodcaller",
                                        "itemgetter")):
                    bump(rel + " [REFUSED: accessor constructor inside a "
                               "string annotation (round-12)]")
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
