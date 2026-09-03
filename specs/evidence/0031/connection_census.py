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


def _annotation_nodes(tree):
    """Every node inside an annotation subtree — the positions where
    `sqlite3.Connection` names a TYPE rather than acquires a connection."""
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
        elif isinstance(node, ast.AnnAssign) and node.annotation is not None:
            ann_roots.append(node.annotation)
    ids = set()
    for root in ann_roots:
        for n in ast.walk(root):
            ids.add(id(n))
    return ids


def connect_census(source, rel):
    """The census over one source text. Returns {key: count}: inventory
    counts for blessed direct `sqlite3.connect(...)` calls under `rel`,
    and `[REFUSED: ...]` keys for every violation of the positive surface."""
    out = {}

    def bump(key):
        out[key] = out.get(key, 0) + 1

    tree = ast.parse(source)
    ann_ids = _annotation_nodes(tree)
    parent = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parent[c] = n
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module \
                and (node.module == "sqlite3"
                     or node.module.startswith("sqlite3.")):
            bump(rel + " [REFUSED: from-import of sqlite3 or a submodule]")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "sqlite3" and alias.asname:
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
                if id(node) in ann_ids:
                    pass                     # a TYPE annotation, not an opener
                elif isinstance(par, ast.Call) and par.func is node:
                    bump(rel + " [REFUSED: sqlite3.Connection constructed "
                               "directly — the constructor is an opener "
                               "(round-7: it makes usable connections) and "
                               "only the blessed opener acquires]")
                else:
                    bump(rel + " [REFUSED: sqlite3.Connection captured "
                               "outside annotation position]")
            elif node.attr not in ALLOWED_ATTRS:
                bump(rel + f" [REFUSED: unclassified sqlite3 attribute "
                           f"{node.attr!r} — the surface is positive; "
                           f"classify it or it refuses]")
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
    return out
