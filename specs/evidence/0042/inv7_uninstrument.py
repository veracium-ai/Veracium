#!/usr/bin/env python3
"""specs/0042 INV-7 — THE UNINSTRUMENTED TWIN, DERIVED FROM HEAD (not exported from an old commit).

The first four-arm transcripts exported the twin from the commit the instrumentation tranches began from
(`84f9515`). That twin was right for exactly as long as src/ changed only by instrumentation; the moment a
later spec touched src the "uninstrumented" arm was also an OLDER product. So the twin is DERIVED: HEAD's src
with the census MEASUREMENTS (every consult and every fire) removed by an AST transform that inverts the
instrumenter's forms and nothing else — and, since round 6 (R6-6), REFUSES everything it has not established is
instrumentation. Since round 14 the DECLARATIONS and census imports are PRESERVED verbatim. The twin's census.py is the
REFERENCE CENSUS (round 16): the census.py of an ACCEPTED commit, `REFERENCE_CENSUS_COMMIT`, tracked beside this file as
reference_census.py and pinned by `REFERENCE_CENSUS_SHA256` — never HEAD's. So the census UNDER TEST is not in the
reference arm (round 15 copied HEAD's, and the round-15 verdict showed a declaration-time defect in it shared by all four
arms), while every declaration still binds a real Site: the reference's Site must equal HEAD's member for member
(`site_drift`), or the transform refuses and T must advance. That no census code takes part in a decision is MEASURED,
outside the twin, by the observer (inv7_observer.py's profile hook), not built into it:

    NAME = declare_site(...)                 ->  PRESERVED            NAME is then a DECLARED name of this module
    from .census import declare_site …      ->  PRESERVED            (declare_site under another name is REFUSED)
    from . import census as _census          ->  PRESERVED
    with NAME.consult(): <body>              ->  <body>               NAME declared; every item of the with a consult
    NAME.consult()                           ->  (removed)            the statement form (round 6, R6-2a)
    raise NAME.fire(EXC, ...)                ->  raise EXC            NAME declared; the value is the first argument
    return NAME.fire(EXPR, ...)              ->  return EXPR
    x = NAME.fire(EXPR, ...)                 ->  x = EXPR
    if _census.enabled(): <block>            ->  if False: <block'>   ONLY the recognised bypass shape at the four hot
                                                                      Edge predicates (a with-consult whose body is
                                                                      [assignment,] return NAME.fire(...)); the block
                                                                      is kept DEAD, not deleted, so the function's
                                                                      return/raise statements keep their number and
                                                                      order — the observer keys exits by ordinal

REFUSED (never guessed): `other.fire(...)` on a name that is not a declared site of the module; `a.b.fire(...)`
(an attribute chain the transform cannot bind); a consult on an undeclared name; a `with` mixing consult and
non-consult items; an enabled-block of any other shape (a side effect inside it would be product behaviour);
`nonlocal`/`global` naming a declared site; and `declare_site` imported under another name. (Rounds 12 and 13 also refused a declared site another module reaches
and the dynamic forms `globals()`, `vars()`, `exec`, `eval`, a `__dict__` or `sys.modules`; those refusals existed
only because the declaration was removed, and round 14, which keeps every declaration bound, withdrew them — each
such route now derives, verifies clean and runs as the source does.) Every statement that is not one of the listed
forms is PRESERVED.

`derive()` writes the twin AND a MANIFEST (`twin_manifest.json`): per module the source sha256 before and after,
the count of every transformation, and per function the number of return/raise statements before and after —
`verify()` asserts the exit counts equal, that no instrumentation survives, and that every non-instrumentation
statement of HEAD is still present in the twin (the transform removes and rewrites only the listed forms).

    python3 specs/evidence/0042/inv7_uninstrument.py <src/veracium> <out/src/veracium>
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import shutil
import symtable
import sys


def _sibling(name):
    """Load a sibling evidence module BY PATH (never `from x import y`: green where the directory happens to be on
    sys.path and red where it is not — the tests/ class)."""
    import importlib.util as _u
    s = _u.spec_from_file_location(f"_0042_{name}", pathlib.Path(__file__).resolve().parent / f"{name}.py")
    m = _u.module_from_spec(s); s.loader.exec_module(m); return m


_scope = _sibling("scope_resolution")

# ---- ROUND 16: THE REFERENCE CENSUS — an ACCEPTED commit's census.py, not HEAD's ----------------------------------------
# The round-15 verdict: the twin carried HEAD's census.py, so a defect in its DECLARATION-time code (which the reference
# arm executes) changed a decision in all four arms at once, and the trace diff could not see it. The owner's decision,
# "(3) Accepted census": the twin carries the census.py of an accepted commit T, pinned by digest. The census under test
# is then NOT shared with the reference, and the separating test (tests/test_0042_inv7.py) shows such a defect reading
# DIVERGENT. Faithfulness still holds by construction — T's Site is a real Site — PROVIDED HEAD's Site has not drifted
# from T's (`site_drift`); if it has, T must advance, which is a specification change.
REFERENCE_CENSUS = pathlib.Path(__file__).resolve().parent / "reference_census.py"
REFERENCE_CENSUS_COMMIT = "5d835e1453d9265acdbb60e3f9732ad7ebeffd2b"      # the round-15 pin: its census.py was reviewed there
REFERENCE_CENSUS_SHA256 = "69beb1bb2f058d97de646638ec103f799c8e8e0e7c11b2abb196a3f41800683f"


def reference_census_bytes() -> bytes:
    """The reference census's bytes, REFUSED unless they are the pinned digest (a changed file is a changed T)."""
    data = REFERENCE_CENSUS.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != REFERENCE_CENSUS_SHA256:
        raise Refused(f"the reference census {REFERENCE_CENSUS.name} is sha256 {got[:16]}…, not the pinned "
                      f"{REFERENCE_CENSUS_SHA256[:16]}… of accepted commit {REFERENCE_CENSUS_COMMIT[:7]}: advancing T is a "
                      f"specification change, not an edit to this file")
    return data


def _site_classdef(text: str):
    cls = [n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == "Site"]
    return cls[0] if len(cls) == 1 else None


def _site_members(text: str) -> dict:
    """A per-member reading of Site's body — the DIAGNOSTIC only, never the verdict (round 17: as a verdict it lost
    statement order and let a later statement shadow an earlier one under the same key)."""
    cls = _site_classdef(text)
    if cls is None:
        return {"<class Site>": "not exactly one module-level class definition named Site"}
    out = {}
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[n.name] = ast.dump(n)
        elif isinstance(n, (ast.Assign, ast.AnnAssign)):
            for tg in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                out[ast.unparse(tg)] = ast.dump(n)
        elif isinstance(n, ast.Expr) and isinstance(getattr(n, "value", None), ast.Constant) and isinstance(n.value.value, str):
            out["<docstring>"] = ast.dump(n)
        else:
            out[f"<statement at line {n.lineno}>"] = ast.dump(n)
    return out


def _definition_drift(head_census: str, reference_census: str) -> list:
    """ROUTE A — Site's DEFINITION as written: the whole ClassDef, compared as one ast.dump. That is ordered, keeps
    duplicate definitions, compares the header by field (decorators, bases and keywords apart) and the docstring by
    position, and carries no line numbers, so a formatting-only change (comments, blank lines) is not drift."""
    h, r = _site_classdef(head_census), _site_classdef(reference_census)
    if h is None or r is None:
        return [f"Site: {'HEAD' if h is None else 'the reference'} census does not define exactly one module-level class Site"]
    if ast.dump(h) == ast.dump(r):
        return []
    out = []
    for field in ("decorator_list", "bases", "keywords"):
        if [ast.dump(x) for x in getattr(h, field)] != [ast.dump(x) for x in getattr(r, field)]:
            out.append(f"Site's class header ({field}) differs from the reference census's")
    hm, rm = _site_members(head_census), _site_members(reference_census)
    out += [f"Site.{k}: in HEAD's census and not in the reference census" for k in sorted(set(hm) - set(rm))]
    out += [f"Site.{k}: in the reference census and not in HEAD's" for k in sorted(set(rm) - set(hm))]
    out += [f"Site.{k}: differs between HEAD's census and the reference census" for k in sorted(set(hm) & set(rm)) if hm[k] != rm[k]]
    if not out:
        # the member map cannot NAME this difference (an order change, or a duplicate a later statement shadows), so it
        # is reported by POSITION: the diagnostic never goes silent while the verdict says drift
        hb, rb = [ast.dump(n) for n in h.body], [ast.dump(n) for n in r.body]
        k = next((i for i in range(min(len(hb), len(rb))) if hb[i] != rb[i]), min(len(hb), len(rb)))
        out.append(f"Site's class body differs from the reference census's at statement {k} "
                   f"({len(hb)} statements in HEAD's, {len(rb)} in the reference's): an order change or a duplicate definition")
    return out


# ROUND 18 — ONE RECURSIVE RULE (the round-17 verdict, and the second seat's stage-1 read of its fix). Rounds 16, 17 and
# the round-17 verdict each found the same shape one level deeper: the class body read as a map; the class's type-level
# fields outside vars(); the FUNCTION objects' own writable fields (__name__, __qualname__, __module__) outside a hand list.
# Each fix derived one level and listed the next. Now ANY object is described by the same rule, recursively, and the only
# things not compared are named below, each by the property that justifies it:
_NAMESPACE_REFS = ("__globals__", "__builtins__")   # the defining module's namespace — census code under test, by design
_CODE_LOCATION = ("co_filename", "co_firstlineno", "co_linetable", "co_lnotab")   # WHERE code was written, not what it does
# The same property for the CLASS: 3.13 stores the line its class statement starts on in vars() as `__firstlineno__`, so
# a comment or a blank line ABOVE Site read as drift on 3.13 alone — an over-refusal in route B and the runtime gate
# from round 18 until round 21, found by CI's 3.13 lane on a census with a coding cookie on line 1. Absent before 3.13,
# so the description is unchanged there.
_CLASS_LOCATION = ("__firstlineno__",)
_CACHE_BIT = 1 << 19      # Py_TPFLAGS_VALID_VERSION_TAG (CPython's Include/object.h): the type's attribute-cache state, set
                          # by a plain lookup on 3.10–3.12 (measured by both seats); IS_ABSTRACT (1 << 20) stays compared
# `__class__` is not read as a field: every object's type is the first component of its description. A BUILT-IN type is
# compared by name: it is the interpreter's own, the same object on both sides.


def _addressless(text: str) -> str:
    """A repr with its memory address removed: two builds of one class give two addresses for the same object (a lock, a
    function's default object), and an address is WHERE, never WHAT — without this the fallback would read the same
    definition as drift, loudly (the second seat's round-17 stage-2 note, N-8). An address printed in any OTHER format
    still reads as drift (over-refusal, loud)."""
    import re
    return re.sub(r" at 0x[0-9a-fA-F]+", " at 0x…", text)


def _data_descriptors(tp: type) -> list:
    import inspect
    names = []
    for k in tp.__mro__:
        for n, d in vars(k).items():
            if n not in names and n != "__class__" and inspect.isdatadescriptor(d):
                names.append(n)
    return names


# ROUND 19 — IDENTITY, NOT NAMES (the round-18 verdict; the second seat's stage-1 read). The round-18 rule matched scalars
# and containers by isinstance() and described a type in `builtins` by NAME, so `class tuple(tuple)` overriding
# __contains__, rebound as Site.__slots__, read as the built-in tuple on both routes and at runtime. A name is a CLAIM —
# __module__ and __qualname__ are writable on any class Python code creates. What Python code CANNOT fake is
# Py_TPFLAGS_IMMUTABLETYPE (1 << 8, 3.10+): set on every type Python code cannot create (the built-ins, and C types such
# as _thread.lock and re.Pattern, heap types included), and an immutable type's __module__ and __qualname__ cannot be
# written. So a type is described BY NAME only if it is immutable; every other type is described by this same rule.
_IMMUTABLE_TYPE = 1 << 8
_SCALARS = frozenset({"str", "bytes", "int", "float", "complex", "bool", "NoneType", "ellipsis"})
_SEQUENCES = frozenset({"tuple", "list"})
_SETS = frozenset({"set", "frozenset"})
_MAPPINGS = frozenset({"dict", "mappingproxy"})


def _immutable(tp: type) -> bool:
    return bool(type.__dict__["__flags__"].__get__(tp) & _IMMUTABLE_TYPE)


def _builtin(tp: type, names: frozenset) -> bool:
    """IS `tp` the built-in of that name — by the immutable flag (unforgeable) and the name it then cannot fake."""
    return _immutable(tp) and tp.__module__ == "builtins" and tp.__qualname__ in names


def _base_content(obj, tp: type, seen: dict):
    """An instance of a MUTABLE subclass of a built-in scalar or container: its content read through the IMMUTABLE BASE's
    own methods (tuple.__iter__, dict.items, str.__repr__), never the subclass's, which may override them."""
    for b in tp.__mro__[1:]:
        if _builtin(b, _SEQUENCES):
            return (b.__qualname__, tuple(_normalise(x, seen) for x in b.__iter__(obj)))
        if _builtin(b, _SETS):
            return (b.__qualname__, tuple(sorted(repr(_normalise(x, seen)) for x in b.__iter__(obj))))
        if _builtin(b, _MAPPINGS):
            return (b.__qualname__, tuple((repr(_normalise(k, seen)), _normalise(v, seen)) for k, v in b.items(obj)))
        if _builtin(b, _SCALARS):
            return (b.__qualname__, b.__repr__(obj))
    return None


def _normalise(obj, seen: dict) -> tuple:
    """ANY object by what it IS: a built-in scalar or container — by the immutable flag, never isinstance — by value or
    element-wise; a code object by every non-callable co_* field except its location; a CLASS by module and qualname only
    if it is immutable, else by this same rule; anything else by its TYPE's identity (by name if immutable, described
    in full if not), EVERY data descriptor along its type's MRO (read-only included — a read-only field can hold
    writable state), each normalised recursively, and — for a mutable subclass of a built-in — its content read through
    the base's own methods. A leaf with no data descriptors keeps its address-free repr. An object met again is
    recorded by the position at which it was first described, so equal structures stay equal and cycles end."""
    tp = type(obj)
    if _builtin(tp, _SCALARS):
        return (tp.__qualname__, repr(obj))
    if id(obj) in seen:
        return ("<ref>", seen[id(obj)])
    seen[id(obj)] = len(seen)
    if issubclass(tp, type) and _immutable(obj):
        return ("immutable-type", obj.__module__, obj.__qualname__)
    if _builtin(tp, _SEQUENCES):
        return (tp.__qualname__, tuple(_normalise(x, seen) for x in obj))
    if _builtin(tp, _SETS):
        return (tp.__qualname__, tuple(sorted(repr(_normalise(x, seen)) for x in obj)))
    if _builtin(tp, _MAPPINGS):
        return (tp.__qualname__, tuple((repr(_normalise(k, seen)), _normalise(v, seen)) for k, v in obj.items()))
    if _builtin(tp, frozenset({"code"})):
        fields = [f for f in dir(obj) if f.startswith("co_") and f not in _CODE_LOCATION and not callable(getattr(obj, f))]
        return ("code", tuple((f, _normalise(getattr(obj, f), seen)) for f in fields))
    identity = ("immutable-type", tp.__module__, tp.__qualname__) if _immutable(tp) else ("class", _normalise(tp, seen))
    fields = []
    for n in _data_descriptors(tp):
        if n in _NAMESPACE_REFS:
            continue
        try:
            v = getattr(obj, n)
        except AttributeError:
            fields.append((n, ("<unset>",)))
            continue
        if n == "__flags__" and isinstance(v, int):
            v = v & ~_CACHE_BIT
        fields.append((n, _normalise(v, seen)))
    content = None if _immutable(tp) else _base_content(obj, tp, seen)
    if not fields and content is None:
        return (identity, _addressless(repr(obj)))
    return (identity, tuple(fields), content)


def _normal_code(co) -> tuple:
    """A code object by the recursive rule's code branch (kept by name for its callers and cells)."""
    return _normalise(co, {})[1]


def _normal_value(v, seen=None) -> tuple:
    """A value in vars(Site), by the recursive rule. `seen` carries the Site class itself, so a reference back to it (a
    slot's __objclass__) is recorded by position rather than describing the class again inside its own member."""
    return _normalise(v, {} if seen is None else seen)


def _realized_site(text: str, name: str):
    """T's or HEAD's census EXECUTED in its own fresh module namespace, inside the transform process — never inside an
    arm — and its Site returned. Module-level code in census.py builds only its own state (locks, an empty registry)."""
    import types
    mod = types.ModuleType(name)
    exec(compile(text, f"<{name}>", "exec"), mod.__dict__)
    return mod.__dict__.get("Site")


def _type_level_fields(meta: type) -> list:
    """The fields a class carries ON THE TYPE OBJECT rather than in its vars(): every data descriptor its METACLASS (and
    the metaclass's MRO) defines — for `type`, __name__, __qualname__, __module__, __doc__, __mro__, __bases__, __base__,
    the size and flag fields and the rest. DERIVED from the metaclass, never listed (round 17, the second seat's pre-seal
    read: `Site.__qualname__ = …` after the class changed repr(type(S)) with vars(Site) equal)."""
    import inspect
    names = []
    for k in meta.__mro__:
        for n, v in vars(k).items():
            if inspect.isdatadescriptor(v) and n not in names and n != "__dict__":
                names.append(n)
    return names


def _type_level_value(cls, name):
    try:
        v = getattr(cls, name)
    except AttributeError:
        return ("<unset>",)
    if name in ("__mro__", "__bases__"):
        # a class reference by an identity it cannot fake: an immutable class by module and qualname; a mutable one is
        # marked as such here and described in full in its own `base.` entry
        return tuple((c.__module__, c.__qualname__) if _immutable(c) else ("mutable class", c.__qualname__) for c in v)
    if name == "__base__":
        return (v.__module__, v.__qualname__) if isinstance(v, type) and _immutable(v) else ("mutable class", getattr(v, "__qualname__", repr(v)))
    if name == "__flags__":
        # the attribute-cache bit masked (_CACHE_BIT above); found by dev building round 18's cells, 2026-09-25
        return ("int", v & ~_CACHE_BIT)
    return _normalise(v, {id(cls): 0})


def site_description(cls) -> list:
    """Route B's reading of ONE built Site class, as ordered (key, normalised value) entries — the ONE definition both
    route B (two descriptions compared, at transform time) and the observer's runtime gate (one description digested in
    each arm, round 18's N-6) read, so the two cannot disagree about what "the same class" means: its MRO by name, the
    names of vars(Site) in order, each vars value normalised (functions by code, defaults, keyword defaults, annotations,
    doc, attributes and closure; slots by name; anything else by type and address-free repr), every TYPE-LEVEL field its
    metaclass defines (derived, not listed; the attribute-cache bit masked), and the metaclass. vars() is read FIRST:
    reading __annotations__ on 3.10+ inserts one into vars."""
    v = {k: x for k, x in vars(cls).items() if k not in _CLASS_LOCATION}
    out = [("mro", tuple(c.__name__ for c in cls.__mro__)), ("vars.order", tuple(v))]
    out += [(f"vars.{k}", _normal_value(x, {id(cls): 0})) for k, x in v.items()]
    # every NON-built-in base, described by the same rule (a base's content is inherited behaviour; route A does not see
    # a base class defined outside Site's own ClassDef)
    out += [(f"base.{i}", _normalise(b, {id(cls): 0})) for i, b in enumerate(cls.__mro__[1:], 1) if not _immutable(b)]
    out += [(f"type.{n}", _type_level_value(cls, n)) for n in _type_level_fields(type(cls))]
    meta = type(cls)
    out.append(("metaclass", (meta.__module__, meta.__qualname__) if _immutable(meta) else _normalise(meta, {id(cls): 0})))
    return out


def site_description_digest(desc: list) -> dict:
    """A description as its digest and per-entry sha16s, so a runtime disagreement NAMES the entry that differs."""
    entries = [[k, hashlib.sha256(repr(val).encode()).hexdigest()[:16]] for k, val in desc]
    return {"digest": hashlib.sha256(repr(entries).encode()).hexdigest(), "entries": entries}


_ISOLATED_CHILD = """
import builtins, importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("_inv7_uninstrument_isolated", sys.argv[1])
un = importlib.util.module_from_spec(spec); spec.loader.exec_module(un)
response, dumps, open_, exit_ = sys.argv[2], json.dumps, open, os._exit     # bound BEFORE the census runs
census = sys.stdin.buffer.read().decode("utf-8")   # bytes: never the locale's encoding
bdict = vars(builtins); saved = dict(bdict)          # a census may rebind a built-in; the DESCRIBER must not see it
site = un._realized_site(census, "_inv7_head_census")
bdict.clear(); bdict.update(saved)                   # bound names only: `vars` itself is a built-in
body = (dumps([[k, repr(v)] for k, v in un.site_description(site)]) if isinstance(site, type)
        else dumps("the census does not build a class named Site"))
with open_(response, "w", encoding="ascii") as f:
    f.write(body); f.flush()
exit_(0)                                             # neither the census's atexit hooks nor its threads outlive this
"""

# The child's wall-clock budget; a module constant so a test can lower it (a census whose import never ends).
_ISOLATION_TIMEOUT = 300


def _described_in_isolation(census_text: str):
    """ROUTE B's reading of the Site a census builds, made in a FRESH interpreter (`python -I`, no user site, no
    PYTHONPATH) and returned as data — [(entry, repr of its normalised value)], or a string saying why it could not be
    made. The transform process never executes census code: a census that rebinds a built-in (`import builtins;
    builtins.tuple = …`) changes only the child (round 19, the second seat's stage-1 read: a __builtins__ copy does not
    isolate, because `import builtins` returns the real module), and inside the child the builtins module is restored
    after the census runs, so the describer reads with the real built-ins. The child never writes bytecode (`-B`,
    always): `-I` drops every PYTHON* variable, PYTHONDONTWRITEBYTECODE and PYTHONPYCACHEPREFIX among them, and a child
    does not inherit `-B`, so without it a transform run with bytecode off, or with its caches redirected, wrote caches
    into the evidence directory it was loaded from (found by the round-19 stage's untouched-tree check; passing on only
    the caller's `-B` missed the redirected caller, the second seat's stage-1 read). The description does not depend on
    the child's hash seed.
    THE RESPONSE TRAVELS ON A CHANNEL THE CHILD OWNS (round 20, the round-19 verdict's F1): a file at an absolute path in
    a temporary directory outside the evidence tree, removed afterwards — never stdout, which the census shares, so
    a census that prints is not a census that cannot be described. The census keeps its stdout and stderr; they are
    read only to name a failure. The child ends with os._exit(0) once the response is written and closed, so a
    census's atexit hooks and non-daemon threads cannot append to it, change its exit or hold it open; a complete,
    well-formed response is authoritative and the exit code is diagnostic only. No response, a malformed one, one
    of the wrong shape and a child that outruns its budget are each a NAMED failure, which derive() refuses and
    verify() reports as "could not be described" — never a bare exception. THE BOUNDARY IS BYTES (round 21, the
    round-20 verdict's F1): the census text goes in as UTF-8 bytes and the census's own stdout and stderr come back as
    bytes, decoded only to name a failure (invalid UTF-8 backslash-escaped), so neither a census that prints arbitrary
    bytes nor a non-UTF-8 locale can turn a valid description into a UnicodeDecodeError. The census can read the response path
    from argv; within the accepted scope (below) it does not attack the measurement.
    INV-7's ACCEPTED SCOPE (the round-19 verdict accepted it; before then it was an unstated assumption), not a gap of
    this route: describing an object needs the object, and the
    object needs the process that ran the census, so census code can reach the describer — a census that patches it
    forges its own description in four lines, even with no import statement (the second seat's probe, round 19). The
    same holds for the N-6 runtime gate and for the INV-7 trace itself: every arm runs census code in the process that
    records it, and a census can rewrite its own arm's trace (executed round 19: four appended lines took a healthy arm
    from 519 records to 0, its pytest still green). The measurement assumes census code CHANGES BEHAVIOUR and does not
    ATTACK THE MEASUREMENT; route A, which reads only the ClassDef, is the one reading outside that assumption."""
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory(prefix="inv7_route_b_") as d:
        response = pathlib.Path(d).resolve() / "description.json"
        try:
            r = subprocess.run([sys.executable, "-I", "-B", "-c", _ISOLATED_CHILD, str(pathlib.Path(__file__).resolve()),
                                str(response)], input=census_text.encode("utf-8"), capture_output=True,
                               timeout=_ISOLATION_TIMEOUT)
        except subprocess.TimeoutExpired:
            return f"the isolated interpreter did not finish within {_ISOLATION_TIMEOUT}s"
        try:
            body = response.read_text(encoding="ascii") if response.exists() else None
        except (OSError, UnicodeDecodeError) as e:
            body, unreadable = None, f"{type(e).__name__}: {e}"
        else:
            unreadable = None
    def shown(b: bytes) -> str:                        # decoded only to NAME a failure, never on success
        return b.decode("utf-8", errors="backslashreplace").strip()[-200:]
    context = f"exit {r.returncode}; stderr: {shown(r.stderr)!r}; stdout: {shown(r.stdout)!r}"
    if body is None:
        return f"the isolated interpreter wrote no description ({unreadable or context})"
    try:
        out = json.loads(body, object_pairs_hook=_strict_pairs)       # 0026's evidence-boundary rule: never plain
    except ValueError as e:
        return f"the isolated interpreter's description is malformed ({e}; {context})"
    if isinstance(out, str):
        return out
    if not (isinstance(out, list) and all(isinstance(e, list) and len(e) == 2 and all(isinstance(x, str) for x in e)
                                          for e in out)):
        return f"the isolated interpreter's description has the wrong shape ({context})"
    return [tuple(e) for e in out]


def _realized_drift(head_census: str, reference_census: str) -> list:
    """ROUTE B — the Site CLASS each census BUILDS, read by `site_description` and compared entry by entry. It sees what
    route A cannot: a module-level statement after the class (`Site.__doc__ = …`, `Site.fire.__defaults__ = …`,
    `setattr(Site, …)`, `Site.__qualname__ = …`), and a module-level name read at class creation whose VALUE differs."""
    h, r = _described_in_isolation(head_census), _described_in_isolation(reference_census)
    for label, d in (("HEAD's", h), ("the reference", r)):
        if isinstance(d, str):
            raise SiteUndescribed(f"{label} census could not be described in an isolated interpreter — this is not "
                                  f"drift, and T does not advance: {d}")
    hd, rd = dict(h), dict(r)
    out = []
    for k in list(rd) + [k for k in hd if k not in rd]:
        if hd.get(k, "<absent>") == rd.get(k, "<absent>"):
            continue
        if k == "mro":
            out.append("Site's realized MRO differs from the reference census's")
        elif k == "vars.order":
            out.append("Site's realized attributes differ in their names or order from the reference census's")
        elif k == "metaclass":
            out.append("Site's realized metaclass differs from the reference census's")
        elif k.startswith("vars."):
            name = k[len("vars."):]
            where = "in HEAD's census and not in the reference census" if k not in rd else (
                "in the reference census and not in HEAD's" if k not in hd else "differs between HEAD's census and the reference census")
            out.append(f"Site.{name} (realized): {where}")
        else:
            out.append(f"Site.{k[len('type.'):]} (realized, on the type): differs between HEAD's census and the reference census")
    return out


def site_drift(head_census: str, reference_census: str) -> list:
    """Every way HEAD's Site differs from the reference census's Site, read TWO independent ways (round 17, the round-16
    verdict and the second seat's stage-1 read): ROUTE A compares Site's DEFINITION as written — the whole class, ordered,
    duplicates kept — and ROUTE B compares the Site class each census BUILDS when executed. Drift is the UNION: either
    route seeing a difference means Site's definition is not T's, and T must advance. Formatting-only changes are not
    drift on either route. A change ELSEWHERE in HEAD's census — a module-level helper a method calls — is NOT drift: it
    is census code under test, which the reference arm does not carry, so the trace diff sees any decision it changes;
    and a Site method that runs in the reference arm is counted by the census-entry hook. Both routes are read under ONE
    interpreter (ast.dump fields and code layout differ across versions). Empty means Site is T's; anything else means T
    must advance. A census that cannot be DESCRIBED (it crashes, exits, or never finishes on import) is not drift and is
    never reported as drift: route B raises SiteUndescribed, which derive() refuses and verify() reports as what it is
    (round 20, the second seat's stage-2 read of the round-19 verdict's F1 contract — "a contextual failure")."""
    return _definition_drift(head_census, reference_census) + _realized_drift(head_census, reference_census)


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins. Every JSON read in this layer
    goes through it — the round-8 suite caught the manifest read added for F4 arriving as a plain `json.loads`."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


class Refused(Exception):
    pass


# ROUND 21 (the round-20 verdict's F1, and the second seat's stage-1b read): every text boundary is one of these, and
# the gate in tests/test_0042_inv7.py refuses a decode, an encode or a text read/write anywhere else in this module.
# A Python SOURCE is read in the encoding it DECLARES — a PEP 263 coding cookie on line 1 or 2, or a UTF-8 BOM, else
# UTF-8 — because a census, or a product module, is any valid Python, and valid Python declares its own encoding. Line
# endings are kept, so an ordinary file's twin bytes do not move. Everything else this module reads or writes (the
# manifest) is UTF-8.
# ROUND 22 (the round-21 verdict): round 21 found the cookie with tokenize.detect_encoding and called that "the
# interpreter's rule". It is not: detect_encoding decodes lines 1-2 as UTF-8 BEFORE looking for a cookie, and raises on a
# header comment the interpreter's own tokenizer, which scans those lines as BYTES, accepts (a latin-1 comment above a
# latin-1 cookie; text after a cookie; an invalid byte in a line-1 comment — measured on 3.10, 3.12 and 3.13). The
# cookie is now found at the byte level, as PEP 263 states it — and because that is a second implementation of the
# interpreter's rule too, it is never trusted alone: _source_text checks every reading against the interpreter's.
_COOKIE = re.compile(rb"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")
_BLANK_OR_COMMENT = re.compile(rb"^[ \t\f]*(?:[#\r\n]|$)")
_BOM = b"\xef\xbb\xbf"


# ROUND 23 (the round-22 verdict): the interpreter does not look a cookie's name up as written. Its tokenizer first
# passes it through get_normal_name (tokenize._get_normal_name is the stdlib's copy), which folds every spelling of
# UTF-8 and Latin-1 — `utf-8-unix`, `iso-latin-1`, `LATIN_1-x` — onto one name; round 22's byte-level reader dropped
# that step with detect_encoding and refused 52 of 5,825 names the interpreter runs (measured on 3.10–3.13).
def _normal_name(name: str) -> str:
    """The interpreter's own normalisation of a cookie's name, step for step: the first 12 characters, lower-cased,
    `_` read as `-`; then UTF-8 and Latin-1, and either followed by `-` and anything, are named canonically. One step
    per line, so each can be mutated alone."""
    s = name[:12]
    s = s.lower()
    s = s.replace("_", "-")
    if s == "utf-8" or \
            s.startswith("utf-8-"):
        return "utf-8"
    if s in ("latin-1", "iso-8859-1", "iso-latin-1") or \
            s.startswith(("latin-1-", "iso-8859-1-", "iso-latin-1-")):
        return "iso-8859-1"
    return name                                        # the name AS WRITTEN, not the folded one: the interpreter's too


def _source_encoding(data: bytes) -> str:
    """The encoding a source declares: a coding cookie on line 1, or on line 2 when line 1 is blank or a comment, its
    name normalised as the interpreter normalises it; a UTF-8 BOM (which admits no other declaration — compared, as the
    interpreter compares it, by the normalised name); else UTF-8. Scanned as BYTES, never decoded to find the cookie.
    An encoding Python's codecs do not know raises LookupError, which the caller names."""
    import codecs
    bom = data.startswith(_BOM)
    for i, line in enumerate((data[len(_BOM):] if bom else data).splitlines(keepends=True)[:2]):
        m = _COOKIE.match(line)
        if m:
            name = _normal_name(m.group(1).decode("ascii"))
            codecs.lookup(name)
            if bom and name != "utf-8":
                raise SyntaxError(f"encoding problem: {name} with BOM")
            return "utf-8-sig" if bom else name
        if i == 0 and not _BLANK_OR_COMMENT.match(line):
            break
    return "utf-8-sig" if bom else "utf-8"


class SourceUnreadable(Refused):
    """A file the transform must read as Python source, and cannot: EITHER it is not Python the interpreter accepts
    (an unknown coding cookie, bytes invalid in the declared encoding outside a comment, a syntax error), OR the
    interpreter accepts it and the transform's reading disagrees with the interpreter's — a failure of the transform,
    said so in the message, never passed off as the source's. A refusal of its own and never drift: T does not
    advance for it."""


def _source_text(data: bytes, label: str = "<source>") -> str:
    """A source's TEXT for analysis. The BYTES are first parsed exactly as the interpreter parses a file (its cookie,
    a BOM, its tokenizer), so what is accepted here is what Python would run, and anything else is a NAMED refusal.
    Valid Python may still hold bytes invalid in its declared encoding, but only inside a COMMENT (the tokenizer does
    not decode comment bytes; measured on 3.10–3.13, round 21, the second seat's stage-1c read); so the text is
    decoded with errors="replace", which can change nothing but a comment's characters — which neither route reads
    and no twin executes. (errors="surrogateescape" round-trips, but ast.parse and compile of a str re-encode it as
    UTF-8 and reject the surrogate: measured on the same four interpreters.)
    THE INTERPRETER IS THE ORACLE, per file (round 22): the text is parsed too, and its syntax tree — positions included
    — must equal the one the interpreter built from the bytes. A wrong decoding changes a literal or a column, so any
    disagreement between _source_encoding and the interpreter's own tokenizer is a NAMED refusal, never a misreading."""
    try:
        from_bytes = ast.parse(data, filename=label)
    except (SyntaxError, ValueError) as e:
        raise SourceUnreadable(f"{label} could not be read as Python source — this is not drift, and T does not "
                               f"advance: {type(e).__name__}: {e}") from None
    # THE REFUSAL DIRECTION (round 23): from here the interpreter HAS accepted the bytes, so any failure below is the
    # transform's, and is named as a disagreement with the interpreter — never as a source that is not Python.
    try:
        encoding = _source_encoding(data)
        text = data.decode(encoding, errors="replace")
        from_text = ast.parse(text, filename=label)
    except (SyntaxError, LookupError, ValueError) as e:
        raise SourceUnreadable(f"{label}: the interpreter accepts this source and the transform cannot read it — its "
                               f"reading disagrees with the interpreter's; this is not drift, and T does not advance: "
                               f"{type(e).__name__}: {e}") from None
    if ast.dump(from_bytes, include_attributes=True) != ast.dump(from_text, include_attributes=True):
        raise SourceUnreadable(f"{label}: the transform's reading of this source (as {encoding}) disagrees with the "
                               f"interpreter's — this is not drift, and T does not advance")
    return text


def _read_source(path: pathlib.Path) -> str:
    return _source_text(path.read_bytes(), str(path))


def _write_source(path: pathlib.Path, text: str) -> bytes:
    """Writes transformed source in the encoding the TEXT ITSELF declares — a PEP 263 cookie in its first two lines,
    else UTF-8 — so the twin always declares what it is. Not the original's encoding: the transform may drop comments,
    and a cp1252 file whose cookie is gone would be written as cp1252 bytes read back as UTF-8 (measured, round 21).
    Returns the bytes written: the manifest's `sha256_after` is of those, never of a re-encoding of the text."""
    data = text.encode(_source_encoding(text.encode("utf-8")))
    path.write_bytes(data)
    return data


def _read_data(path: pathlib.Path) -> str:
    return path.read_bytes().decode("utf-8")


def _write_data(path: pathlib.Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


class SiteUndescribed(Refused):
    """Route B could not describe a census's Site — a crash, an exit or an unfinished import in the isolated child,
    or a response that is absent or malformed. A refusal of its own, because it is NOT drift: T must not advance for it."""


def _receiver(call: ast.Call):
    """The receiver NAME of `NAME.method(...)`, or None for any other callee shape."""
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f.value.id
    return None


def _is_consult_call(c) -> bool:
    """`<NAME>.consult()` — the one reading of a consult CALL. ROUND 12 (research's R4a): the with-item form and the
    bare-statement form each spelled this test out, identically, in two places; now both ask this."""
    return isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "consult" and not c.args


def _is_consult_item(item: ast.withitem) -> bool:
    return _is_consult_call(item.context_expr)


def _is_fire_call(node) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "fire"


def _is_enabled_call(node) -> bool:
    """`<Name>.enabled()` — the one reading of a census CONSULT. ROUND 12 (research's R4a): `visit_If` (which
    rewrites it) and the unresolved-bypass detector (which reports what was not rewritten) each spelled this test
    out, identically. Two readings of one question, identical today, are the shape every round of this arc found
    disagreeing one round later."""
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "enabled" \
        and isinstance(node.func.value, ast.Name)


def exits_per_function(tree: ast.AST) -> dict:
    """{qualname: number of return/raise statements in the function's OWN body (nested scopes excluded)}."""
    out = {}
    def walk(node, qual):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = ".".join(qual + [child.name]); n = 0
                def count(n_):
                    nonlocal n
                    for c in ast.iter_child_nodes(n_):
                        if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                            continue
                        if isinstance(c, (ast.Return, ast.Raise)):
                            n += 1
                        count(c)
                count(child); out[q] = n
                walk(child, qual + [child.name])
            elif isinstance(child, ast.ClassDef):
                walk(child, qual + [child.name])
            else:
                walk(child, qual)
    walk(tree, [])
    return out


class Uninstrument(ast.NodeTransformer):
    def __init__(self, declared: set[str], census_aliases: set[str], resolver=None):
        self.declared = declared; self.census_aliases = census_aliases
        # ROUND 7, F4a (F2's shared root): "is this NAME the declared site?" is a SCOPE question, and the transform
        # answered it by membership in `declared` alone. A function PARAMETER shadowing a module-level site name
        # therefore had its own ordinary method call rewritten, changing what the twin computes. The question now
        # goes to the same resolver the binding scan uses — CPython's own scope analysis.
        self.resolver = resolver
        self.sites = 0; self.fires = 0; self.consults = 0; self.consult_stmts = 0; self.bypasses = 0; self.imports = 0

    def _is_site(self, name, node) -> bool:
        """`name`, used at `node`, is the module-level declared site — not a local, a parameter, or an enclosing
        function's binding. With no resolver the transform REFUSES rather than falling back to membership, because
        the fallback IS the defect."""
        if name not in self.declared:
            return False
        if self.resolver is None:
            raise Refused(f"line {getattr(node, 'lineno', '?')}: no scope resolver was supplied, so {name!r} cannot "
                          f"be established as the declared site rather than a local of the same name")
        return self.resolver.refers_to_declared_site(node, name)

    def _is_census_alias(self, name, node) -> bool:
        """`name`, used at `node`, is the MODULE-level census import — not a parameter, a local, or an
        enclosing function's binding that happens to be spelled the same.

        ROUND 9, F3: THE TWIN OF `_is_site`, AND IT DID NOT EXIST. Round 7's F4a established that "is this NAME
        the declared site?" is a SCOPE question and routed it to the resolver — at the site call sites. The
        CENSUS-ALIAS question sat four methods away still answered by `name in self.census_aliases`, pure
        spelling, and that one REWRITES rather than refusing: an ordinary function taking a parameter named
        `_census` and branching on `_census.enabled()` had its branch turned into `if False:`, so the twin
        computed a different answer from the source (measured: original True, derived False) while `verify()`
        reported no problems. A fix applied at one of a question's two sites is the round's recurring shape.

        Fail direction matters here and it is why this one was the dangerous one: `visit_Global`/`visit_Nonlocal`
        also test membership, but they REFUSE on a hit, so a wrong answer over-refuses and is loud.

        WHAT THIS ESTABLISHES, IN THE MECHANISM'S OWN WORDS, AND WHAT IT DOES NOT. It establishes that the
        name resolves to a MODULE-LEVEL binding, that the binding is made by an import spelled
        `from . import census` (level 1, no module), and — via `module_binding_count` at the call in
        `uninstrument_source` — that the name is bound EXACTLY ONCE, so the import was not later replaced.
        IT DOES NOT ESTABLISH THAT THE BINDING DENOTES THIS PROJECT'S CENSUS MODULE, and no static reading
        can, which is the round-9 verdict's distinction between module scope and the identity of the object
        bound there. Research demonstrated the limit executably: two BYTE-IDENTICAL files,

            from . import census as _census
            def ordinary(): return _census.enabled()

        one under `real/sub/` and one under `fake/sub/`, bind different objects and return True and False.
        A static check cannot separate them BECAUSE THEY ARE THE SAME FILE — `.census` resolves against
        whichever package the module sits in. Three rounds of increasingly specific syntax (membership ->
        spelling -> scope) have a fourth rung that syntax cannot reach.

        SO IDENTITY IS CHECKED WHERE IT IS CHECKABLE: AT RUNTIME, in the behaviour regressions, which
        already execute both modules and can therefore assert that the object bound to the alias IS the
        census module the instrumentation uses. That assertion is
        `test_r9_the_alias_identity_is_established_at_runtime_because_it_cannot_be_established_statically`."""
        if name not in self.census_aliases:
            return False
        if self.resolver is None:
            raise Refused(f"line {getattr(node, 'lineno', '?')}: no scope resolver was supplied, so {name!r} "
                          f"cannot be established as the census module rather than a local of the same name")
        return self.resolver.refers_to_module_binding(node, name)

    # module-level: count the declarations (PRESERVED) and refuse the census imports the twin could not answer
    def visit_Module(self, node):
        # ROUND 14, the round-13 verdict's F1 — NOTHING IS REMOVED. Every declaration `NAME = declare_site(...)` and every
        # census import stays in the twin VERBATIM, and census.py is a real census (round 15 the source's; round 16 the
        # REFERENCE census's), so a declaration binds a real Site. The twin removed every declaration from its first derivation, and rounds
        # 12 and 13 chased, one spelling at a time, every route by which another piece of code could still reach the
        # name it bound — an import, a star, `__all__`, an attribute, `getattr`, `import_module`, `sys.modules`,
        # `globals()` — and the round-13 verdict found five more (`pkgutil`, `runpy`, `importlib.util`, `__globals__`,
        # `inspect`). A name that is never unbound cannot be reached and
        # found missing, however the route is spelled. What stays refused here is what the transform must RECOGNISE:
        # a declaration made through an alias of `declare_site`.
        # The declarations are COUNTED where they are recognised (`bound_declarations`, which `declared_names` also
        # reads), not here: round 14's docstring sweep found this loop counting by the callee's SPELLING while
        # recognition asks the BINDING (round 13's B3), and a membership test on `declared` here is round 7's F4a form.
        for stmt in node.body:
            if is_census_surface_import(stmt):
                for a in stmt.names:
                    if is_instrumentation_name(a.name) and a.asname and a.asname != a.name:
                        raise Refused(f"line {stmt.lineno}: `{a.name}` is imported under another name "
                                      f"({a.asname!r}); a site declaration is recognised by that name, so a "
                                      f"declaration made through this alias could not be recognised")
        self.generic_visit(node)
        return node

    def visit_Global(self, node):
        if any(n in self.declared for n in node.names):
            raise Refused(f"line {node.lineno}: `global` names a declared site — not resolved by guess")
        return node

    def visit_Nonlocal(self, node):
        if any(n in self.declared for n in node.names):
            raise Refused(f"line {node.lineno}: `nonlocal` names a declared site — not resolved by guess")
        return node

    def visit_With(self, node):
        self.generic_visit(node)
        consults = [_is_consult_item(i) for i in node.items]
        if all(consults):
            for i in node.items:
                r = _receiver(i.context_expr)
                if not self._is_site(r, node):
                    raise Refused(f"line {node.lineno}: consult() on {r!r}, which is not this module's declared site "
                                  f"at this point (a local, a parameter, or an enclosing binding of the same name)")
            self.consults += 1
            return node.body                       # spliced into the parent's statement list
        if any(consults):
            raise Refused(f"line {node.lineno}: a consult() item beside a non-consult item — an unrecognised form")
        return node

    def visit_Expr(self, node):
        self.generic_visit(node)
        v = node.value
        if _is_consult_call(v):
            r = _receiver(v)
            if not self._is_site(r, node):
                raise Refused(f"line {node.lineno}: consult() statement on {r!r}, which is not this module's declared "
                              f"site at this point (a local, a parameter, or an enclosing binding of the same name)")
            self.consult_stmts += 1
            return None                            # the statement form: removed
        return node

    def visit_If(self, node):
        self.generic_visit(node)
        t = node.test
        if _is_enabled_call(t) and self._is_census_alias(t.func.value.id, t.func.value):
            # the ONLY recognised shapes for the body (after the with was spliced by generic_visit above):
            # one or two statements, each a simple assignment to ONE Name, the last of them allowed to be a
            # `return <expr>` — the four hot Edge predicates, in their round-6 form (`q = …; return fire(q)`,
            # no else) and their round-7 form (`q = …; q = fire(q)` under an `else:` that computes the same
            # Name, ONE return after both: the exit statement is then the same in every arm, INV-7 R6-5).
            # The else branch is product code and is left exactly as written: with the test made False it
            # is the path every twin takes, which is the census-disabled path by construction.
            body = node.body

            def simple_assign(s):
                return isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name)
            ok = 1 <= len(body) <= 2 and all(simple_assign(s) for s in body[:-1]) and \
                 (simple_assign(body[-1]) or isinstance(body[-1], ast.Return))
            if not ok:
                raise Refused(f"line {node.lineno}: a census-enabled block whose body is not the recognised bypass shape "
                              f"([assignment,] assignment|return) — a side effect or another statement in it would be product behaviour")
            if node.orelse and not all(simple_assign(s) for s in node.orelse):
                raise Refused(f"line {node.lineno}: a census-enabled bypass whose else branch is not simple assignments — unrecognised")
            self.bypasses += 1
            node.test = ast.Constant(value=False)  # kept DEAD: a return statement in the body keeps its ordinal
            return node
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if _is_fire_call(node):
            r = _receiver(node)
            if r is None:
                raise Refused(f"line {node.lineno}: fire() reached through an attribute chain the transform cannot bind")
            if not self._is_site(r, node):
                raise Refused(f"line {node.lineno}: fire() on {r!r}, which is not this module's declared site at this "
                              f"point (a local, a parameter, or an enclosing binding of the same name)")
            if not node.args:
                raise Refused(f"line {node.lineno}: fire() with no decision argument")
            self.fires += 1
            return node.args[0]
        return node

    def generic_visit(self, node):
        # statement lists may receive lists from visit_With (splicing) — flatten them
        for field, old in ast.iter_fields(node):
            if isinstance(old, list):
                new = []
                for item in old:
                    if isinstance(item, ast.AST):
                        r = self.visit(item)
                        if r is None:
                            continue
                        if isinstance(r, list):
                            new.extend(r)
                        else:
                            new.append(r)
                    else:
                        new.append(item)
                old[:] = new
            elif isinstance(old, ast.AST):
                r = self.visit(old)
                if r is None:
                    delattr(node, field)
                else:
                    setattr(node, field, r)
        return node


# THE CENSUS PREDICATES — ONE DEFINITION EACH, AND EVERY CONSUMER ROUTES THROUGH THEM.
#
# ROUND 11, research's stage-1 enumeration: SIX units in this module decided "is this the census?" on THREE
# different readings, kept in step by hand, and every round found two of them disagreeing. Round 10's verdict
# was two instances at once — alias RECOGNITION narrowed while import REMOVAL was not, and rule A applied to
# the alias while rule C was not. Research then found a third and a fourth: a removal branch that checks
# `module` and never `level`, so `from .. import census` is UNRECOGNISED and REMOVED ANYWAY (the same
# NameError as the reviewer's finding 2, reached through the disagreement rather than through either answer);
# and a recogniser and a detector that both require `ast.If`, so a census consult in any other statement shape
# is invisible to BOTH.
#
# The remedy is not a fifth patch. It is that the predicates below are the only definitions, every consumer
# calls one of them, and `test_every_census_decision_routes_through_one_predicate` enumerates the consumers
# and fails the day one appears on a reading of its own. (This comment used to say "these TWO functions"
# and was wrong at five: a count describing a set that grows is a count that goes stale, so it names none.)
#
# ROUND 12 (research's stage-1 R4a): THE GATE'S BANNED SET IS DERIVED FROM THE STRING CONSTANTS INSIDE THESE
# PREDICATES, not written as the one literal "census". Round 11's gate banned that one word, so the same
# decision made with OTHER vocabulary was invisible to it — and research measured three such pairs, two of
# which had ALREADY drifted: the instrumentation tokens (a three-tuple here, a four-tuple in verify()) and
# the census FILE (top level here, any depth in verify()). Every recognition word now lives in exactly one
# predicate, so adding a word to a predicate bans it everywhere else without editing the gate.

def is_census_module_file(rel) -> bool:
    """The census module's OWN file, which the twin replaces with the REFERENCE census (round 16; round 15 copied it
    verbatim, rounds 7–14 replaced it with a stub).

    ROUND 11: a THIRD reading, found by the enumeration gate on its first run and NOT by the hand enumeration
    that preceded it — research's walk classified `derive` as "mention only, decides nothing", and it decides
    twice. Neither decision was wrong, which is exactly why a manual reading passed over them: the gate looks
    for units deciding on a reading of their own, not for units getting it wrong."""
    return str(rel) == "census.py"


def may_skip_uninstrumenting(text: str) -> bool:
    """A module that cannot be instrumented, skipped without parsing it.

    THE SAFETY ARGUMENT, STATED BECAUSE THE FALSE NEGATIVE IS THE DANGEROUS ONE: skipping a module that DOES
    use the census would leave instrumentation in the twin. Every route into the census carries one of these
    three tokens in the source text — the census import contains `census`, a declaration contains
    `declare_site`, a measured decision contains `.fire(`. A module containing none of them has no route in.
    This is a performance guard, not an identity decision, and it is named here so it cannot drift into one.

    ROUND 12: THE TOKENS ARE ASKED OF THEIR OWNER. This spelled out `.fire(` and `declare_site` itself, and its
    safety rested on "every route in carries one of THESE tokens" — so a fourth instrumentation token added to
    `instrumentation_tokens_in` would have been unknown here, a module carrying only it SKIPPED, and its
    instrumentation left live in the twin. Two predicates can both be definitions and still be a hand-kept pair;
    the derived gate cannot see that, because both are allowed to hold the word. Measured before the change: zero
    modules in src/veracium change their skip decision (the form adds `.consult()`, which no module carries alone)."""
    return "census" not in text and not instrumentation_tokens_in(text)


def _in_recognised_bypass(tree, call) -> bool:
    """Is this `<alias>.enabled()` call the TEST of an `if`, the one shape `visit_If` rewrites?

    Anything else — an assignment, a `while`, a ternary, a boolean operand — is a census consult the
    transform leaves in place, which the twin then carries live. The detector reports those rather than
    refusing them: preserving ordinary behaviour cannot over-refuse, and the manifest naming them is what
    makes the silence into a signal."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.test is call:
            return True
    return False


def census_names_in_import(stmt) -> list:
    """The `census` aliases a sibling `from . import ...` binds — [] if it is not one.

    ONE DERIVATION for both the whole-statement removal and the partial strip. Round 11's first form asked
    `any(...)` in the predicate and had no partial branch at all, so a multi-name import was all-or-nothing
    and the answer was ALL."""
    if not (isinstance(stmt, ast.ImportFrom) and stmt.level == 1 and stmt.module is None):
        return []
    return [a for a in stmt.names if a.name == "census"]


def is_census_surface_import(stmt) -> bool:
    """`from .census import declare_site, ...` — the instrumentation SURFACE, not the module object.

    `stmt.module` is checked EXACTLY, not by `endswith`: `from .not_really_census import x` is not this, and
    neither is `from totally_unrelated.census import x`. (Research's next-round item, taken now because it
    costs one comparison and this is the round that is supposed to stop hand-kept predicates.)

    BOTH SPELLINGS THE TREE ACTUALLY USES ARE ACCEPTED, and the first form of this predicate accepted only
    one. It required a RELATIVE import, and the suite caught it immediately: the tree carries
    `from .census import declare_site` (19) and `from ..census import declare_site` (9, in the store/ and
    asof/ subpackages), while the fixtures carry the ABSOLUTE `from veracium.census import declare_site`.
    Narrowing to the relative form left the emitted module still carrying `declare_site`, which the token
    check then refused. `endswith` was too wide; level>=1 alone was too narrow; the exact module name in
    either spelling is the property that is actually meant."""
    if not isinstance(stmt, ast.ImportFrom):
        return False
    if stmt.level >= 1:
        return stmt.module == "census"            # from .census / from ..census import <surface>
    return stmt.module == "veracium.census"        # from veracium.census import <surface>


def is_instrumentation_name(name: str) -> bool:
    """The one name on the census SURFACE that is instrumentation rather than a harness read.

    ROUND 12 (the verdict's F1): a surface import is decided per NAME. ROUND 14: nothing is stripped — `declare_site`
    is kept, and it must be imported under its own name (an alias is refused, since a declaration is recognised by
    this name). ROUND 15: the twin's census is the source's own module, so every other surface name resolves as it does
    in the source; the round-12 refusal of a name the stub did not answer had nothing left to refuse and is gone."""
    return name == "declare_site"


def is_site_declaration(call) -> bool:
    """`declare_site(...)` or `<alias>.declare_site(...)` — a site DECLARATION, recognised by the callee's name.
    ROUND 12 (research's R4a): `visit_Module` and `declared_names` each spelled this test out; now both ask it."""
    f = call.func
    return is_instrumentation_name(getattr(f, "id", getattr(f, "attr", "")))


def instrumentation_tokens_in(text: str) -> list:
    """Every instrumentation TOKEN still present in `text`. ROUND 12 (research's R1): ONE definition for the
    transform's own emitted-module refusal AND for verify(), which kept a second tuple with a FOURTH token
    (`from .census import`). The two had drifted, and the fix for F1 would have made them contradict — a
    correct twin keeping `from .census import enabled` refused by verify() on its first run."""
    # ROUND 14: `declare_site` is no longer a token that must not survive — every declaration stays in the twin (bound,
    # since round 16, to the REFERENCE census). What must not survive is a MEASUREMENT: a consult or a fire.
    return [tok for tok in (".consult()", ".fire(") if tok in text]


def lost_bindings(src_text: str, twin_text: str) -> set:
    """Names the SOURCE binds at module level that the TWIN still reads and binds nowhere — a NameError waiting.

    THE CHECK OF A DIFFERENT KIND (the verdict's F1, its E half). verify() compares the twin against RE-DERIVING
    the transform, so a transform defect reproduces identically and reads clean; this does not re-derive anything.
    It is a DIFFERENTIAL over every module-level binding, not only imports (research's stage-1 R2: a declared site
    is ASSIGNMENT-bound, and an import-scoped check missed it). A differential rather than an absolute "unbound
    read" check, because both sides are read by one interpreter: CPython 3.12+ inlines comprehensions (PEP 709),
    so a comprehension variable appears as a module-level binding AND read there and on 3.10/3.11 does not — an
    absolute check would false-positive on half the regimes, while the difference cancels it on all four.

    NO BUILTIN EXCLUSION (round 12, research's stage-2 S2-2). This subtracted `dir(builtins)`, on the reasoning that
    a builtin name cannot be a lost binding. It is the ONE case that can be SILENT: a lost binding can only carry a
    builtin's name if the source SHADOWED that builtin, and losing the shadow raises no NameError — the name quietly
    resolves to the builtin. Measured: a site named `id`, read in a default, gave a twin passing the builtin `id`
    function where the source passed the site, with verify() CLEAN. The subtraction was never what kept ordinary
    builtin reads out; the differential is, because it only reports names the SOURCE bound.

    WHAT THIS DOES NOT READ, AND WHAT DOES (round 13 — round 12 listed these as limits, and the round-12 verdict
    returned a disclosed silent limit as blocking, so each now has an owner): a name bound DYNAMICALLY
    (`globals()[...]`, `exec`) is invisible to a static reading; this reads ONE module at a time, so a binding lost
    ACROSS modules is read by `lost_cross_module_references` in verify(). ROUND 14: the transform removes no binding
    — every declaration stays bound (since round 16 to the REFERENCE census) — so neither limit can be reached through a declared site, and
    the round-13 refusals of dynamic forms and of cross-module reach were withdrawn; this reading remains verify()'s
    check against a transform that DOES lose a binding (the mutant in tests/test_0042_inv7.py). A changed
    VALUE with no lost name — the round-12 verdict's F1 — is the scope resolver's pairing, which its join check now
    refuses rather than guesses; the pairing oracle over random programs is the class-level instrument."""

    def bound(text):
        top = symtable.symtable(text, "<twin-check>", "exec")
        return {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported()}

    def reads(text):
        top = symtable.symtable(text, "<twin-check>", "exec")
        out = {s.get_name() for s in top.get_symbols() if s.is_referenced()}

        def walk(tab):
            for child in tab.get_children():
                out.update(s.get_name() for s in child.get_symbols() if s.is_global() and s.is_referenced())
                walk(child)
        walk(top)
        return out

    return (bound(src_text) - bound(twin_text)) & reads(twin_text)


def _module_file(root: pathlib.Path, dotted: str):
    """The file for `<package>.<a>.<b>` under `root` (the package directory), or None: a module or a package."""
    parts = dotted.split(".")[1:]
    base = root.joinpath(*parts) if parts else root
    for cand in (base.with_suffix(".py") if parts else None, base / "__init__.py"):
        if cand is not None and cand.is_file():
            return cand
    return None


def _dotted_of(root: pathlib.Path, path: pathlib.Path, pkg: str | None = None) -> str:
    rel = path.relative_to(root).with_suffix("")
    parts = [pkg or root.name, *rel.parts]
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def _exported(path: pathlib.Path) -> set:
    """What `from <module> import *` binds: a literal `__all__` if the module has one, else its public names."""
    tree = ast.parse(_read_source(path))
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets) and stmt.value is not None:
                try:
                    return set(ast.literal_eval(stmt.value))
                except ValueError:
                    return set()
    return {n for n in _module_bindings(path) if not n.startswith("_")}


def _module_bindings(path: pathlib.Path) -> set:
    """Module-level names a module binds, by the interpreter's own scope analysis."""
    top = symtable.symtable(_read_source(path), str(path), "exec")
    return {s.get_name() for s in top.get_symbols() if s.is_assigned() or s.is_imported()}


def cross_module_references(root: pathlib.Path, pkg: str | None = None) -> list:
    """Every reference, anywhere in the package at `root`, from one module to a NAME in another: `from X import N`
    (relative or absolute), `from X import *` (through X's `__all__` or public names), and an ATTRIBUTE read through
    a module object — bound by `from . import a`, `import pkg.a as m`, or `import pkg.a` and read as `pkg.a.N`.
    Returned as (importer, line, target module file, name, form). ROUND 13, the round-12 verdict's F2 and research's
    stage-1 R2: removing a declared site broke a sibling's import with verify() clean, and the attribute route
    (`from . import a` … `a.S`) broke at call time the same way.

    ALSO a literal `getattr(<package module>, "S")` and `import_module("<package module>")` — inline or bound to a name,
    recognised by its binding — which are the same static reference (round 13, research's pre-seal P1).

    ROUND 14 — WHAT THIS IS FOR NOW. Rounds 12 and 13 used these references to REFUSE a declared site that another
    module reached, because the twin removed the declaration; the round-13 verdict found five more routes (`pkgutil`,
    `runpy`, `importlib.util`, `__globals__`, `inspect`) and the list could not close. Round 14 keeps every declaration
    bound, so nothing here is refused. This remains as `verify()`'s cross-module DIFFERENTIAL — a reference the twin
    still makes that resolved in the source and does not in the twin — and it can still fire: a transform that
    deleted a declaration is the mutant that shows it (tests/test_0042_inv7.py)."""
    root = pathlib.Path(root); pkg = pkg or root.name       # a twin's directory may be named apart from its package
    files = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
    refs = []
    for path in files:
        tree = ast.parse(_read_source(path))
        here = _dotted_of(root, path, pkg)
        package = here if path.name == "__init__.py" else here.rsplit(".", 1)[0]
        modules = {}                                      # local name -> dotted module it is bound to
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package.split(".")
                    base = base[:len(base) - (node.level - 1)] if node.level > 1 else base
                    target = ".".join(base + ([node.module] if node.module else []))
                else:
                    target = node.module or ""
                if target != pkg and not target.startswith(pkg + "."):
                    continue
                tfile = _module_file(root, target)
                for a in node.names:
                    if a.name == "*":
                        if tfile is not None:
                            refs += [(path, node.lineno, tfile, n, "star") for n in sorted(_exported(tfile))]
                    elif _module_file(root, f"{target}.{a.name}") is not None:
                        modules[a.asname or a.name] = f"{target}.{a.name}"          # a submodule, bound as a name
                    elif tfile is not None:
                        refs.append((path, node.lineno, tfile, a.name, "from-import"))
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == pkg or a.name.startswith(pkg + "."):
                        if a.asname:
                            modules[a.asname] = a.name
                        else:
                            modules[pkg] = pkg                                     # `import pkg.a` binds `pkg`
        # BINDINGS, NOT SPELLINGS (research's input to P1, after B2): what `import_module` is called in THIS module is
        # read from its imports, so `from importlib import import_module as im` is seen.
        im_names, importlib_names = {"__import__"}, set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and not node.level and node.module == "importlib":
                for a in node.names:
                    if a.name == "import_module":
                        im_names.add(a.asname or a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == "importlib":
                        importlib_names.add(a.asname or a.name)

        def is_import_module(call):
            f = call.func
            return (isinstance(f, ast.Name) and f.id in im_names) or \
                (isinstance(f, ast.Attribute) and f.attr == "import_module" and isinstance(f.value, ast.Name)
                 and f.value.id in importlib_names)

        def literal(node):
            return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None

        def in_pkg(dotted):
            return dotted is not None and (dotted == pkg or dotted.startswith(pkg + "."))

        for node in ast.walk(tree):                   # `m = import_module("pkg.a")` binds a module like an import
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and is_import_module(node.value) \
                    and node.value.args and in_pkg(literal(node.value.args[0])):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        modules[t.id] = literal(node.value.args[0])

        def module_of(expr):
            """The package module an expression evaluates to, or None."""
            if isinstance(expr, ast.Name) and isinstance(expr.ctx, ast.Load):
                return modules.get(expr.id)
            if isinstance(expr, ast.Call) and is_import_module(expr) and expr.args \
                    and not (isinstance(expr.func, ast.Name) and expr.func.id == "__import__"):
                d = literal(expr.args[0])
                return d if in_pkg(d) else None
            if isinstance(expr, ast.Attribute) and isinstance(expr.ctx, ast.Load):
                base = module_of(expr.value)
                if base is not None and _module_file(root, f"{base}.{expr.attr}") is not None:
                    return f"{base}.{expr.attr}"
            return None

        def add(dotted, name, line, form):
            # NO SELF-EXEMPTION (round 13, research's pre-seal D1): a module referring to its OWN module object — `import
            # pkg.b as me`, `from . import b as me`, `import_module('pkg.b')` inside b — reaches its own site the same way
            # a sibling would. Exempting `tfile == path` made those silent. (Round 14: the twin removes no declaration, so
            # these references are verify()'s differential against a transform that does — the mutant that shows it.)
            tfile = _module_file(root, dotted)
            if tfile is not None:
                refs.append((path, line, tfile, name, form))

        parent = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent[id(child)] = node

        def is_plain_getattr(call):
            return isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "getattr" \
                and "getattr" not in modules and len(call.args) >= 2

        for node in ast.walk(tree):
            dotted = module_of(node) if isinstance(node, (ast.Name, ast.Call, ast.Attribute)) else None
            if dotted is not None:
                up = parent.get(id(node))
                # A package module read as `m.<static, non-dunder attribute>`, or through the plain builtin
                # `getattr(m, "<literal>")`, is a static reference. (Round 13 also listed every OTHER use as an escape
                # and every dynamic acquisition, for derive() to refuse; round 14 keeps every name bound, so those
                # refusals are gone and nothing consumes such rows.)
                if isinstance(up, ast.Attribute) and up.value is node and not up.attr.startswith("__"):
                    if module_of(up) is None:
                        add(dotted, up.attr, up.lineno, "attribute")
                elif is_plain_getattr(up) and up.args[0] is node and literal(up.args[1]) is not None:
                    add(dotted, literal(up.args[1]), up.lineno, "getattr")
    return refs


def _resolves(root: pathlib.Path, tfile: pathlib.Path, name: str) -> bool:
    return name in _module_bindings(tfile) or _module_file(root, f"{_dotted_of(root, tfile)}.{name}") is not None


def lost_cross_module_references(src: pathlib.Path, out: pathlib.Path) -> list:
    """The references the TWIN still makes that do not resolve in the twin and DID resolve in the source: an
    ImportError, an AttributeError at import (a star over a stale `__all__`), or an AttributeError at call time.
    verify()'s cross-module reading. It is a DIFFERENTIAL over the twin's own references — a reference only the SOURCE
    makes is not the twin's and is not reported (since round 14 the transform removes no reference to a binding: it
    removes consults and unwraps fires) — and it asks nothing about which names are sites, so it does not share the
    transform's site recognition."""
    lost = []
    for path, line, tfile, name, form in cross_module_references(out, pkg=src.name):
        if tfile is None or name is None:
            continue
        if _resolves(out, tfile, name):
            continue
        src_target = src / tfile.relative_to(out)
        if src_target.is_file() and _resolves(src, src_target, name):
            lost.append(f"{path.relative_to(out)}:{line}: {form} of {name!r} from {tfile.relative_to(out)} — bound "
                        f"there in the source and not in the twin: the twin fails where the source ran")
    return lost


def bound_declarations(tree: ast.Module) -> list:
    """Every module-level `NAME = declare_site(...)` statement that DECLARES A SITE — recognised by its census BINDING
    (below). The ONE recognition: `declared_names` takes its names from it and the transform its site COUNT, so the
    count cannot drift from what is recognised (round 14: it had counted by the callee's spelling)."""
    return [stmt for stmt in tree.body if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
            and isinstance(stmt.targets[0], ast.Name) and isinstance(stmt.value, ast.Call)
            and _is_bound_declaration(tree, stmt.value)]


def _is_bound_declaration(tree: ast.Module, call) -> bool:
    surface = {a.asname or a.name for st in tree.body if is_census_surface_import(st) for a in st.names
               if is_instrumentation_name(a.name)}
    census_bound = {a.asname or a.name for st in tree.body for a in census_names_in_import(st)}
    f = call.func
    if isinstance(f, ast.Name):
        return f.id in surface and is_site_declaration(call)
    return isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in census_bound \
        and is_site_declaration(call)


def declared_names(tree: ast.Module) -> tuple[set[str], set[str]]:
    """(the module-level names bound by `NAME = declare_site(...)`, the aliases the census module is imported as)."""
    declared, aliases = {stmt.targets[0].id for stmt in bound_declarations(tree)}, set()
    # ROUND 13 (research's stage-2 B3): a declaration is recognised by its BINDING, not its spelling. This accepted
    # ANY callee named `declare_site`, so `N = mock.MagicMock().declare_site('a')` — an object from outside the
    # package — was removed from the twin as a site, with verify() CLEAN: the source's `N.fire(4)` returned a
    # MagicMock, the twin's returned 4. Only `declare_site` bound by a census surface import, or `<census
    # alias>.declare_site`, declares a site. Any other spelling is ordinary code: ROUND 14 keeps it in the twin as
    # written (the token check no longer names `declare_site`), and a `fire()`/`consult()` on the name it binds is
    # refused, because that name is not a declared site. All 162 real declarations are one of the two.
    for stmt in tree.body:
        # ROUND 10, research's stage-1 B1. This tested `any(a.name == "census")` and NEVER LOOKED AT
        # `stmt.module` OR `stmt.level`, so six of seven spellings were collected — including
        # `from totally_unrelated import census`, `from conftest import census`, `from .vendor.fakes import
        # census` and `from .. import census`. A fix that said "the one binding must be the census import"
        # while asking THIS would have moved from spelling-of-the-alias to SPELLING-OF-THE-IMPORTED-NAME:
        # the same rung, one level up, which is the stop-one-rung-short this round was returned for.
        #
        # Only the SIBLING form is collected: `from . import census` — level 1, no module. That is the form
        # the tree uses (schema.py, where all four bypasses are; __init__.py's is function-local and
        # correctly not module-level). `from .. import census` is a DIFFERENT package's census and is no
        # longer collected. Measured before narrowing: zero modules in src/veracium use any other spelling,
        # so this over-refuses nothing that exists.
        for a in census_names_in_import(stmt):
            # ROUND 12: `a.name`, not the literal — identical for every alias `census_names_in_import` returns
            # (it returns only `a.name == "census"`), and a second copy of the word here is what the
            # derived gate now refuses.
            aliases.add(a.asname or a.name)
    return declared, aliases


def _statement_keys(tree: ast.AST) -> list:
    """Every non-instrumentation statement, as (qualname, kind, unparsed text) — the material the transform must PRESERVE."""
    keys = []
    def walk(node, qual):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                keys.append((".".join(qual), type(child).__name__, child.name)); walk(child, qual + [child.name]); continue
            if isinstance(child, ast.stmt):
                keys.append((".".join(qual), type(child).__name__, None))
            walk(child, qual)
    walk(tree, [])
    return keys


def uninstrument_source(text: str, filename: str = "<twin>") -> tuple[str, dict]:
    resolver = _scope.Resolver(text, filename)          # ROUND 7, F4a: the transform's scope question, resolved
    tree = resolver.tree
    declared, aliases = declared_names(tree)
    resolver.refuse_site_rebindings(declared)
    exits_before = exits_per_function(tree)
    # ROUND 12, research's stage-1 R2: A DECLARED SITE LOADED AS A VALUE. The transform removes `S = declare_site(...)`
    # and rewrites every `S.fire(x)` / `S.consult()`, so any OTHER load of `S` — an argument, a container element, an
    # attribute read — is left pointing at a name the twin no longer binds. Measured: `register(S)` raised NameError
    # at call time and `REGISTRY = [S]` at import, both with verify() CLEAN, because the name is ASSIGNMENT-bound and
    # an import-scoped check could not see it. It was refused here, where the resolver could still say which loads
    # were the site; `lost_bindings` in verify() was the second, independent reading of the same fact.
    # ROUND 14: round 12's R2 ("a declared site loaded outside fire()/consult()") and round 13's dynamic-namespace
    # refusal are GONE — both existed because the declaration was removed; with the name kept bound (to a stand-in in
    # round 14, to a real census since round 15 — the source's, then (round 16) the REFERENCE census), a site loaded as a
    # value, or reached through `globals()`,
    # is correct code (research's stage-1 read).
    census_aliases = aliases
    # AND THE BINDING MUST NOT HAVE MOVED. `from . import census as _census` followed by `_census = On()`
    # imports the census and then replaces it; the name still resolves to module scope, so the scope
    # question answers YES about a binding that no longer denotes the census. Rule A's reading answers the
    # one part of this a static check can: was the name bound more than once?
    # ROUND 10'S VERDICT, FINDING 1: THIS ASKED RULE A ONLY. The SITE question has always been answered by
    # TWO readings — the module's own code object (rule A) and the NESTED code objects (rule C) — and round 10
    # gave the census alias the first and not the second. `_nested_global_bindings` was in the same file, made
    # public in the same round, unused. So a nested `global _census; _census = On()`, a nested import, and a
    # generator-expression walrus all replaced the alias invisibly: ordinary() returned 101 in the source and
    # 1 in the twin, with verify() clean. Not a missing case — an existing mechanism applied to one half of
    # the question it was built for.
    for a in sorted(census_aliases):
        here = resolver.module_binding_count(a)                 # rule A: this scope's own bindings
        nested = resolver.nested_global_bindings(a)             # rule C: what nested scopes bind here
        if here != 1 or nested:
            where = f"{here} time(s) at module level" + (f" and from nested scope(s) {', '.join(sorted({n for n, _ in nested}))}" if nested else "")
            raise Refused(f"the census alias {a!r} is bound {where}, so the import does not establish what the "
                          f"name denotes where the bypass reads it. BOTH readings are asked, the module's own "
                          f"code object and the nested code objects, because a nested `global {a}` assignment, "
                          f"a nested import and a comprehension walrus all replace the binding without the "
                          f"module-level count moving")
    # ROUND 10, research's stage-2 F-S2-2: `bypasses: 0` HAD TWO MEANINGS AND THEY PRINTED IDENTICALLY —
    # a module with genuinely no census bypass, and a module WITH one whose alias could not be established,
    # whose twin therefore RETAINS a live `<name>.enabled()` call. In that region the twin is not an
    # uninstrumented reference at all, and its own manifest called it clean. That is the zero-versus-N/A
    # shape: "none present" and "present but not recognisable" are different facts and only the first is a
    # result. Four shapes reach it, all measured — a try/except import, an `if TYPE_CHECKING:` import, an
    # import under a runtime block, and no census import at all — because `declared_names` reads `tree.body`
    # and the bound-exactly-once refusal only fires on an ESTABLISHED alias, so the gap sits BEFORE both.
    #
    # The module is NOT refused: preserving ordinary behaviour cannot over-refuse, and refusing here would
    # reject an idiom no module in the tree uses. What changes is that the manifest stops reporting it clean.
    # Counted on the ORIGINAL tree, where the resolver can still answer about these nodes.
    # ROUND 11, research's stage-1 B2 — THEIR OWN ROUND-10 FINDING, FIXED AT ONE OF ITS TWO SITES, AND THE
    # SITE THEY DID NOT SPECIFY IS THE ONE I IMPLEMENTED. They asked for "does any surviving `<name>.enabled()`
    # call sit on a module-level name I could not establish" — SHAPE-AGNOSTIC. I wrote it on `ast.If` tests,
    # and the recogniser is on `ast.If` too, so a census consult in ANY other statement form was invisible to
    # BOTH. Measured with a perfectly ESTABLISHED alias: `on = _census.enabled()`, `while _census.enabled():`
    # and a ternary all gave bypasses=0, unresolved=0, and a twin that KEEPS the live call.
    #
    # So `bypasses: 0, unresolved: 0` had THREE meanings, not the two round 10 fixed: no bypass; a bypass on
    # an unestablished alias (reported); and a bypass in an unrecognised STATEMENT SHAPE (silent). This walks
    # every `<Name>.enabled()` call wherever it stands, and reports the ones the transform did not rewrite.
    unresolved = []
    for node in ast.walk(tree):
        if _is_enabled_call(node):
            nm = node.func.value.id
            if not resolver.refers_to_module_binding(node.func.value, nm):
                continue                                   # a local or a parameter of the same name: not ours
            if nm not in census_aliases:
                unresolved.append(f"{nm}.enabled() at line {node.lineno} (name not an established census alias)")
            elif not _in_recognised_bypass(tree, node):
                unresolved.append(f"{nm}.enabled() at line {node.lineno} (established alias, statement shape "
                                  f"the transform does not rewrite)")
    t = Uninstrument(declared, census_aliases, resolver)
    t.sites = len(bound_declarations(tree))              # counted where recognised (see `bound_declarations`)
    tree = t.visit(tree); ast.fix_missing_locations(tree)
    # a module that still USES the census surface after the instrumentation is gone (the opt-in switch,
    # `_census.enable(True)` in the package module) keeps its import: the twin's stub census answers it
    # ROUND 9, F3 (found by sweeping F3's class rather than fixing the cell the reviewer named): this read
    # `n.id in ("_census", "census")` — a hand-written literal sitting two lines below `census_aliases`, which
    # is DERIVED from this module's own imports. A module importing the census as anything else kept its
    # surface use and lost its import, so the twin died with `NameError`. Latent, not live: the tree's only
    # alias today is `_census`. Same shape as `_NESTED_BINDING_OPS` nearly reusing the wider tuple and as the
    # packaging README hand-listing filenames the stage derives — a literal next to the derivation that
    # should have produced it.
    out = ast.unparse(tree) + "\n"
    exits_after = exits_per_function(ast.parse(out))
    if exits_after != exits_before:
        diff = {k: (exits_before.get(k), exits_after.get(k)) for k in set(exits_before) | set(exits_after) if exits_before.get(k) != exits_after.get(k)}
        raise Refused(f"the transform changed a function's exit count — the observer keys exits by ordinal: {diff}")
    stats = {"sites": t.sites, "fires": t.fires, "consults": t.consults, "consult_statements": t.consult_stmts,
             "bypasses": t.bypasses, "imports": t.imports, "exits": exits_after,
             # the COUNT sums into the manifest totals; the DETAIL stays per module, under a key the
             # totals loop does not know, so a reviewer sees both the headline and which call it was.
             "unresolved_bypass_candidates": len(unresolved), "unresolved_bypass_detail": unresolved}
    # no INSTRUMENTATION may survive in the emitted module (a stub-answered surface read may)
    for token in instrumentation_tokens_in(out):         # ROUND 12, R1: ONE definition, shared with verify()
        raise Refused(f"the emitted module still carries {token!r}")
    return out, stats




def derive(src: pathlib.Path, out: pathlib.Path) -> dict:
    """Copy src/veracium to out, un-instrumenting every module; census.py is replaced by the REFERENCE census (round
    16), refused unless its digest is the pinned one and its Site equals HEAD's member for member. Writes the
    MANIFEST beside the twin (out/../twin_manifest.json): source hashes before and after, every count, the
    permitted transformations by name."""
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("__pycache__"))
    totals = {"sites": 0, "fires": 0, "consults": 0, "consult_statements": 0, "bypasses": 0, "unresolved_bypass_candidates": 0, "imports": 0, "modules_changed": 0}
    manifest = {"permitted_transformations": [
                    "NAME = declare_site(...) PRESERVED (round 14), bound to the REFERENCE census's Site (round 16)",
                    "census imports PRESERVED (round 14)",
                    "census.py -> the REFERENCE census: accepted commit's census.py, pinned by digest, its Site equal to HEAD's (round 16)",
                    "with NAME.consult(): body -> body (NAME declared)", "NAME.consult() statement removed (NAME declared)",
                    "NAME.fire(X, ...) -> X (NAME declared; raise/return/assign)",
                    "if <census>.enabled(): [assign,] return NAME.fire(...) -> if False: [assign,] return X (kept dead; exit ordinals preserved)",
                    "if <census>.enabled(): [assign,] NAME2 = NAME.fire(NAME2) else: <assignments> -> if False: ... else: <assignments> (round 7: the four hot Edge predicates' one-return form; the else branch is product code, untouched)"],
                "refused_forms": ["fire()/consult() on an undeclared name", "fire() through an attribute chain", "fire() with no decision argument",
                                  "a with mixing consult and non-consult items", "an enabled block of any other shape",
                                  "a census-enabled bypass whose else branch is not simple assignments", "nonlocal/global naming a declared site",
                                  "a transform that changes a function's exit count", "an emitted module still carrying a measurement (a consult or a fire)",
                                  "declare_site imported under another name"],
                "modules": {}}
    for p in sorted(out.rglob("*.py")):
        rel = str(p.relative_to(out)); before = p.read_bytes()
        if is_census_module_file(rel):
            ref = reference_census_bytes()
            try:
                drift = site_drift(_source_text(before, rel), _source_text(ref, "the reference census"))
            except SiteUndescribed as e:
                raise SiteUndescribed(f"{rel}: {e}") from e
            if drift:
                raise Refused(f"{rel}: HEAD's Site has drifted from the reference census's (accepted commit "
                              f"{REFERENCE_CENSUS_COMMIT[:7]}) — T must advance: " + "; ".join(drift))
            p.write_bytes(ref)
            manifest["modules"][rel] = {"sha256_before": hashlib.sha256(before).hexdigest(), "sha256_after": hashlib.sha256(ref).hexdigest(),
                                        "reference": REFERENCE_CENSUS_COMMIT}
            continue
        text = _source_text(before, rel)
        if may_skip_uninstrumenting(text):
            manifest["modules"][rel] = {"sha256_before": hashlib.sha256(before).hexdigest(), "sha256_after": hashlib.sha256(before).hexdigest(), "unchanged": True}
            continue
        try:
            new, stats = uninstrument_source(text)
        except (Refused, _scope.UnresolvableScope) as e:
            # ROUND 13 (research's S2-6): an UnresolvableScope escaped here WITHOUT the module path, because only
            # Refused was wrapped — a refusal naming a line and not the file it is in. Each keeps its own type.
            raise type(e)(f"{rel}: {e}") from None
        after = _write_source(p, new)
        # ROUND 10: summed BY PROPERTY, not by an exclusion list. This read `if k != "exits"`, so every
        # new stat had to be remembered in two places — and adding one that is not a number KeyErrors here,
        # which is how the unresolved-bypass detail first landed. A numeric stat now sums automatically and
        # a non-numeric one is carried per module without anyone maintaining a name list.
        for k, v in stats.items():
            if isinstance(v, int):
                totals[k] = totals.get(k, 0) + v
        totals["modules_changed"] += 1
        manifest["modules"][rel] = {"sha256_before": hashlib.sha256(before).hexdigest(), "sha256_after": hashlib.sha256(after).hexdigest(), **stats}
    manifest["totals"] = totals
    _write_data(out.parent / "twin_manifest.json", json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return totals


def verify(out: pathlib.Path, src: pathlib.Path | None = None, manifest: pathlib.Path | None = None) -> list[str]:
    """Does the twin at `out` differ from `src` BY THE INSTRUMENTATION AND NOTHING ELSE? Round 7, F4: the previous
    version answered only half the question and answered that half loosely. It checked that no instrumentation
    TOKEN survived, and — only when a source was passed, which the harness never did — compared a MULTISET of
    (qualname, node kind) for a few kinds. So it verified clean after `return False` became `return True` (same
    kind, same qualname), clean after a module was DELETED from the copy (it iterates the copy, so a missing file
    is simply not visited), and it never looked at the manifest it ships beside. Four readings now, and the source
    is REQUIRED — a verification that silently checks less when an argument is omitted is the round's other finding:

      1. FILE SET — the twin's modules equal the source's, both directions. A deletion or an addition is named.
      2. TOKENS — no instrumentation token (`instrumentation_tokens_in`, the ONE definition the transform's own
         refusal uses) survives an emitted module. ROUND 12: this clause used to add a fourth token, "census
         import", and it was TRUE only because every surface import was dropped whole; once a harness name the
         census answers is kept (the verdict's F1), a correct twin carries `from .census import enabled` — research's
         R1 measured verify() refusing exactly that. ROUND 14: `declare_site` is no longer a token — every declaration
         survives by design — and the tokens are the MEASUREMENTS, `.consult()` and `.fire(`.
      3. STRUCTURE — the twin's AST equals the AST of RE-DERIVING the transform from the source, compared with
         `ast.dump` including every expression and its ORDER. This is data against data: the permitted changes are
         whatever the transform does, so nothing has to enumerate them a second time and drift from the first.
      3b. ROUND 12 — TWO CHECKS OF A DIFFERENT KIND, because 3 re-derives with the SAME transform and so cannot see
         a defect IN it (round 9 learned this about F3 and answered one case; the round-11 verdict's F1 was the
         general form): every emitted module must COMPILE — `ast.parse` accepts a `from __future__` import that is
         no longer first, `compile()` does not — and `lost_bindings` finds any name the source binds at module
         level that the twin reads and binds nowhere. Neither re-derives anything, so neither inherits the defect.
      4. MANIFEST — every module's `sha256_before` matches the source file and `sha256_after` the emitted one, and
         the manifest's module set equals the file set. A manifest is looked for beside the twin unless one is given.
    """
    problems = []
    if src is None:
        return ["verify(out) was called WITHOUT a source: preservation cannot be established from the twin alone "
                "(round 7, F4 — the harness used to call it this way and got a token check silently standing in "
                "for a preservation check). Pass the source tree."]
    twin_files = {p.relative_to(out) for p in out.rglob("*.py")}
    src_files = {p.relative_to(src) for p in src.rglob("*.py") if "__pycache__" not in p.parts}
    for missing in sorted(src_files - twin_files):
        problems.append(f"{missing}: present in the source and MISSING from the twin")
    for extra in sorted(twin_files - src_files):
        problems.append(f"{extra}: present in the twin and absent from the source")
    for rel in sorted(twin_files & src_files):
        p_out = out / rel; text = _read_source(p_out)
        if is_census_module_file(rel):                   # ROUND 12, R4: the transform's own reading, not a second one
            if hashlib.sha256(p_out.read_bytes()).hexdigest() != REFERENCE_CENSUS_SHA256:
                problems.append(f"{rel}: the census module is not the reference census (round 16: accepted commit "
                                f"{REFERENCE_CENSUS_COMMIT[:7]}'s census.py, sha256 {REFERENCE_CENSUS_SHA256[:16]}…)")
            try:
                problems += [f"{rel}: {d} — T must advance" for d in site_drift(_read_source(src / rel), _read_source(p_out))]
            except SiteUndescribed as e:
                problems.append(f"{rel}: {e}")
            continue
        for token in instrumentation_tokens_in(text):   # ROUND 12, R1: the transform's definition, not a drifted copy
            problems.append(f"{rel}: {token!r} survives")
        try:
            compile(text, str(rel), "exec", dont_inherit=True)
        except SyntaxError as e:
            problems.append(f"{rel}: the twin does not COMPILE ({e.msg}, line {e.lineno}) — `ast.parse` accepts text "
                            f"`compile()` refuses, such as a `from __future__` import that is no longer first")
            continue
        lost = lost_bindings(_read_source(src / rel), text)
        if lost:
            problems.append(f"{rel}: LOST BINDING(S) {sorted(lost)} — bound at module level in the source, still read "
                            f"by the twin, bound nowhere in it: the twin raises NameError where the source ran")
        try:
            redone, _ = uninstrument_source(_read_source(src / rel), str(src / rel))
        except Refused as e:
            problems.append(f"{rel}: re-deriving the transform from the source REFUSES ({e})")
            continue
        try:
            if ast.dump(ast.parse(text)) != ast.dump(ast.parse(redone)):
                problems.append(f"{rel}: the twin's program structure differs from re-deriving the transform from "
                                f"the source — the difference is NOT one of the permitted instrumentation changes")
        except SyntaxError as e:
            problems.append(f"{rel}: the twin does not parse ({e})")
    # ROUND 13, the round-12 verdict's F2 — a CROSS-MODULE reading. Every check above reads one module at a time, so a
    # sibling's `from .a import S` breaking with ImportError read clean. A differential over the twin's own references.
    problems += lost_cross_module_references(src, out)
    man_path = manifest if manifest is not None else out.parent / "twin_manifest.json"
    if not man_path.exists():
        problems.append(f"no twin manifest at {man_path} — the derivation's own record of what it rewrote is missing")
    else:
        man = json.loads(_read_data(man_path), object_pairs_hook=_strict_pairs)
        mods = man.get("modules") or {}
        if set(mods) != {str(r) for r in twin_files}:
            only_man = sorted(set(mods) - {str(r) for r in twin_files}); only_twin = sorted({str(r) for r in twin_files} - set(mods))
            problems.append(f"the manifest's module set differs from the twin's files (manifest only: {only_man[:4]}; twin only: {only_twin[:4]})")
        for rel, rec in sorted(mods.items()):
            p_out = out / rel; p_src = src / rel
            if p_out.exists() and hashlib.sha256(p_out.read_bytes()).hexdigest() != rec.get("sha256_after"):
                problems.append(f"{rel}: the emitted file's sha256 does not match the manifest's `sha256_after`")
            if p_src.exists() and hashlib.sha256(p_src.read_bytes()).hexdigest() != rec.get("sha256_before"):
                problems.append(f"{rel}: the SOURCE file's sha256 does not match the manifest's `sha256_before` — "
                                f"the manifest describes a different source than the one verified against")
    return problems


if __name__ == "__main__":
    src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    totals = derive(src, out)
    problems = verify(out, src)
    print("twin derived:", totals)
    print("verify:", "clean" if not problems else problems)
    sys.exit(0 if not problems else 1)
