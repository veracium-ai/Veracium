"""The BINDING CENSUS — a reusable evidence module (round-12 joint F1's
package feedback, taken): adversarial probes import this directly instead of
loading it out of a test driver.

The census's rung history, one gate taught six times what "reference" means:
round 9 required a Call node (terminal names); round 10 required IDENTITY
through imports; round 11 refused SHADOWING across the ordinary binding
constructs; round 12 found the family incomplete — Lambda parameters and
structural-pattern captures (`case rd:` REBINDS rd) both credited the
original while runtime invoked a replacement. The closure here adds those
and, per the reviewer's ask, makes "every binding construct" MECHANICALLY
REVIEWABLE: `BINDING_CONSTRUCTS` below is the inventory, every HANDLED
entry must have a probe in the driver's battery (asserted there), and every
`ast.Match*` class must appear in the inventory (asserted there), so a new
Python binding form fails loudly instead of slipping the family again.
"""
import ast

#: The name-introducing constructs of the Python grammar this census either
#: HANDLES (refuses when they shadow a protected binding) or EXCLUDES with
#: the reason a reader can check. Mechanical review = diff this table
#: against the language reference's binding list.
BINDING_CONSTRUCTS = {
    "handled": (
        "FunctionDef", "AsyncFunctionDef", "ClassDef", "Lambda",
        "Assign", "AnnAssign", "AugAssign", "NamedExpr",
        "For", "AsyncFor", "comprehension", "With", "AsyncWith",
        "ExceptHandler", "Import", "ImportFrom",
        "MatchAs", "MatchStar", "MatchMapping",
    ),
    "excluded": {
        "Global": "a declaration, not a binding — the paired Assign is caught",
        "Nonlocal": "a declaration, not a binding — the paired Assign is caught",
        "arg": "handled via its owning FunctionDef/AsyncFunctionDef/Lambda",
        "withitem": "handled via its owning With/AsyncWith",
        "alias": "handled via its owning Import/ImportFrom",
        "TypeAlias": "3.12+ type statement — binds a TYPE name; a protected "
                     "name shadowed by a type alias would still be refused "
                     "by mechanical review of this table on the day one "
                     "appears in a driver (none exists; CI floor is 3.10)",
        "MatchValue": "matches a value, binds nothing",
        "MatchSingleton": "matches a constant, binds nothing",
        "MatchSequence": "binds only via nested MatchAs/MatchStar (walked)",
        "MatchClass": "binds only via nested patterns (walked)",
        "MatchOr": "binds only via nested patterns (walked)",
    },
}


def census_source(source, protected_modules=None):
    """IDENTITY census over one source text (round-10 F3, the gate's FOURTH
    rung: mention -> module-discovery -> call-by-name -> call-by-IDENTITY).
    The round-9 census recorded terminal NAMES, so a call to any unrelated
    function spelled `control_x` credited the seam control, while alias or
    dispatch invocation of the genuine callable was invisible.

    This census resolves each call through the file's IMPORTS:
    - `from M import c [as y]` binds y (or c) to identity (M, c); a Name
      call through that binding credits (M, c) — aliased from-imports
      resolve, because the identity is declared at the import.
    - `import M [as m]` + `m.c()` credits (M, c).
    - A call through a name bound any other way (a local def, a foreign
      import, a bare attribute) credits NOTHING for the seam modules.

    And the GRAMMAR IS CONSTRAINED (the 0031 inventory sweep's move) where
    identity cannot be traced: an assignment that rebinds an imported
    control to another name is a VIOLATION, returned for the caller to
    fail on — controls are invoked through their imported bindings, so
    dispatch tables and aliases cannot silently hide an invocation from
    the census.

    FIFTH RUNG (round-11 F2): the round-10 census remembered import bindings
    and never applied LATER name binding — a `def` shadowing an imported
    control, or a reassigned module alias, left the census crediting the
    ORIGINAL while runtime invoked a replacement (the reviewer's two probes,
    verbatim in the negatives below). Scope-aware resolution is a compiler's
    job, so the CONSTRAINED-GRAMMAR arm is completed instead: the census
    derives a PROTECTED set — every local name bound to an imported
    control_* and every module alias of a protected (seam) module — and
    REFUSES every binding construct that shadows one: def/class, plain,
    annotated, augmented and unpacked assignment, walrus, for/comprehension
    targets, with-as, except-as, function parameters, and re-imports.

    Returns (credited, violations): credited = {(module, func)} identities
    actually called; violations = [description]."""
    import ast
    tree = ast.parse(source)
    from_bindings = {}   # local name -> (module, original_name)
    mod_bindings = {}    # local name -> module
    for node in ast.walk(tree):
        # FIRST binding wins (round-11: a conflicting later import must not
        # silently DEPROTECT the name by overwriting its map entry — the
        # last-wins draft of this loop did exactly that, caught by the
        # conflicting-reimport probe before it shipped).
        if isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                from_bindings.setdefault(a.asname or a.name,
                                         (node.module, a.name))
        elif isinstance(node, ast.Import):
            for a in node.names:
                mod_bindings.setdefault(a.asname or a.name, a.name)
    protected = {n for n, (_, orig) in from_bindings.items()
                 if orig.startswith("control_")}
    protected |= {n for n, mod in mod_bindings.items()
                  if mod in (protected_modules or ())}

    def _target_names(t):
        if isinstance(t, ast.Name):
            yield t.id
        elif isinstance(t, (ast.Tuple, ast.List)):
            for e in t.elts:
                yield from _target_names(e)
        elif isinstance(t, ast.Starred):
            yield from _target_names(t.value)

    credited, violations = set(), []

    def _shadow(name, what):
        if name in protected:
            violations.append(
                f"protected binding {name!r} shadowed by {what} — the census "
                f"resolves calls through import bindings, so any later "
                f"rebinding makes it credit a callable that is not the one "
                f"invoked (round-11 F2)")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in from_bindings:
                credited.add(from_bindings[fn.id])
            elif (isinstance(fn, ast.Attribute)
                  and isinstance(fn.value, ast.Name)
                  and fn.value.id in mod_bindings):
                credited.add((mod_bindings[fn.value.id], fn.attr))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.Lambda)):
            # Lambda joined round 12: `invoke = lambda rd: rd.control_x()`
            # rebinds rd for the body — the reviewer's probe credited the
            # original while runtime invoked a replacement. Same parameter
            # treatment as a def, per the closure's exact ask.
            if not isinstance(node, ast.Lambda):
                _shadow(node.name, "a def")
            a = node.args
            for arg in (a.posonlyargs + a.args + a.kwonlyargs
                        + ([a.vararg] if a.vararg else [])
                        + ([a.kwarg] if a.kwarg else [])):
                _shadow(arg.arg, "a function or lambda parameter")
        elif isinstance(node, ast.MatchAs):
            # Structural patterns joined round 12: `case rd:` REBINDS rd
            # before the case body runs (the reviewer's second probe).
            # ast.walk reaches every NESTED pattern (sequence/class/or), so
            # MatchAs/MatchStar/MatchMapping-rest anywhere in a pattern tree
            # land here.
            if node.name:
                _shadow(node.name, "a match capture")
        elif isinstance(node, ast.MatchStar):
            if node.name:
                _shadow(node.name, "a match star capture")
        elif isinstance(node, ast.MatchMapping):
            if node.rest:
                _shadow(node.rest, "a match mapping rest capture")
        elif isinstance(node, ast.ClassDef):
            _shadow(node.name, "a class def")
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                for n in _target_names(t):
                    _shadow(n, "an assignment")
            src = node.value
            rebind = None
            if isinstance(src, ast.Name) and src.id in from_bindings:
                rebind = from_bindings[src.id]
            elif (isinstance(src, ast.Attribute)
                  and isinstance(src.value, ast.Name)
                  and src.value.id in mod_bindings):
                rebind = (mod_bindings[src.value.id], src.attr)
            if rebind and rebind[1].startswith("control_"):
                violations.append(
                    f"control {rebind[0]}.{rebind[1]} rebound to another "
                    f"name — controls are invoked through their imported "
                    f"bindings so the identity census can see them")
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            for n in _target_names(node.target):
                _shadow(n, "an annotated/augmented assignment")
        elif isinstance(node, ast.NamedExpr):
            for n in _target_names(node.target):
                _shadow(n, "a walrus assignment")
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for n in _target_names(node.target):
                _shadow(n, "a for target")
        elif isinstance(node, ast.comprehension):
            for n in _target_names(node.target):
                _shadow(n, "a comprehension target")
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars is not None:
                    for n in _target_names(item.optional_vars):
                        _shadow(n, "a with-as target")
        elif isinstance(node, ast.ExceptHandler):
            if node.name:
                _shadow(node.name, "an except-as name")
    # a later import rebinding a protected name to a DIFFERENT target is a
    # shadow; re-importing the SAME module under the same alias (a common
    # function-local pattern in these drivers) binds the same identity and
    # is legitimate.
    first = {}
    for node in ast.walk(tree):
        pairs = []
        if isinstance(node, ast.ImportFrom) and node.module:
            pairs = [(a.asname or a.name, ("from", node.module, a.name))
                     for a in node.names]
        elif isinstance(node, ast.Import):
            pairs = [(a.asname or a.name, ("mod", a.name)) for a in node.names]
        for n, ident in pairs:
            if n in protected and n in first and first[n] != ident:
                _shadow(n, "a conflicting re-import")
            first.setdefault(n, ident)
    return credited, violations


# The driver imports census_source; probes import it from here directly.
