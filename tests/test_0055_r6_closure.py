"""specs/0055 round 6: closure of R6-01 at the width of its CLASS (research's stage-1 read, research b77c8c8f,
additions 1-3). The exception boundary's display carriers are a TABLE (`credentials.DISPLAY_CARRIERS`) derived from what
renders an exception, not from the four carriers the review found: each namespace of it equals its renderer's own
fields, measured here, and a dropped row turns that red. Then a fixture token goes through EVERY carrier at the three
formatters (the CLI defect path, `outward_text`, and the two served routes), each with a positive control that the
original object really displays it. One declared reason set, censused both ways; the field names a refusal prints,
censused; groups at depth. R6-02's three witnesses live in test_0055_r5_closure.py, beside the tests they correct (the
reviewer's round-6 file calls those tests by name).
"""
from __future__ import annotations

import ast
import asyncio
import builtins
import importlib.util
import json
import pathlib
import sys
import traceback

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


T = _load("r6c_invariants", "tests/test_0055_invariants.py")

from pydantic import ValidationError                            # noqa: E402
from pydantic_core import PydanticCustomError                   # noqa: E402

from veracium import cli                                        # noqa: E402
from veracium import credentials as C                           # noqa: E402

GH = T.V.GH                                                     # one assembled structural token (the vectors' fixture)
SRC = ROOT / "src" / "veracium"


# ==== the table is the renderers' fields ==============================================================================

def _traceback_fields() -> set:
    """Every field `traceback.TracebackException` keeps, over the exception kinds whose rendering differs."""
    samples = [ValueError("x"), SyntaxError("m", ("f", 1, 2, "t", 1, 3)), ExceptionGroup("g", [ValueError("a")]),
               KeyError("k"), OSError(2, "s", "f"), AttributeError("a", name="n", obj=object()),
               ImportError("i", name="n", path="p")]
    return set().union(*(vars(traceback.TracebackException(type(e), e, None)) for e in samples))


def _pydantic_error_keys() -> set:
    """Every key Pydantic renders for one error, url, context and input included."""
    e = ValidationError.from_exception_data("M", [{"type": "greater_than", "loc": ("a",), "input": 1, "ctx": {"gt": 2}}])
    return set(e.errors(include_url=True, include_context=True, include_input=True)[0])


def _builtin_rendered_attributes() -> set:
    """Probed, not listed: for every built-in exception class (syntax errors and groups are the traceback namespace's),
    each instance attribute beyond `BaseException`'s is set to a sentinel, and the class is counted when the rendering
    then shows it."""
    sentinel, base, found = "SENTINEL-R6", set(dir(BaseException("x"))), set()
    for name in dir(builtins):
        cls = getattr(builtins, name)
        if not (isinstance(cls, type) and issubclass(cls, BaseException)) or issubclass(
                cls, (SyntaxError, BaseExceptionGroup)):
            continue
        exc = None
        for args in (("x",), ()):
            try:
                exc = cls(*args)
                break
            except Exception:                                   # noqa: BLE001 - a constructor wanting more
                continue
        if exc is None:
            try:
                exc = cls.__new__(cls)                          # a bare instance: its fields set one at a time below
            except Exception:                                   # noqa: BLE001
                continue
        for attr in sorted(set(dir(exc)) - base):
            try:
                if callable(getattr(exc, attr)):
                    continue
                setattr(exc, attr, sentinel)
            except Exception:                                   # noqa: BLE001 - read-only or typed
                continue
            try:
                if sentinel in "".join(traceback.format_exception(type(exc), exc, None)):
                    found.add(attr)
            except Exception:                                   # noqa: BLE001 - a type that will not render it
                pass
    return found


#: built-in carriers the one-attribute probe cannot show, each for its stated reason (they render only together with
#: another field, or not as an attribute): rows kept in the table by hand, and named here so a probe that starts
#: finding one moves it out of this list
_BUILTIN_NOT_PROBED = {
    "errno": "OSError prints it only beside strerror",
    "encoding": "UnicodeError: its str() reads it with object/start/end; one alone does not render",
    "start": "as encoding",
    "end": "as encoding",
    "obj": "AttributeError: the suggestion line reads it with name",
    "key_repr": "KeyError: its str() is its argument's repr, not an attribute",
}
_OUTWARD_TEXT_ROWS = {"reason", "field", "allowed", "class_name"}


def _namespace(table: dict, ns: str) -> set:
    return {k.split(":", 1)[1] for k in table if k.split(":", 1)[0] == ns}


def _table_gaps(table: dict) -> dict:
    """What a renderer prints that the table has no row for, per namespace."""
    return {"traceback": _traceback_fields() - _namespace(table, "traceback"),
            "pydantic.error": _pydantic_error_keys() - _namespace(table, "pydantic.error"),
            "builtin": (_builtin_rendered_attributes() | set(_BUILTIN_NOT_PROBED)) - _namespace(table, "builtin"),
            "pydantic": {"title"} - _namespace(table, "pydantic"),
            "outward_text": _OUTWARD_TEXT_ROWS - _namespace(table, "outward_text")}


def test_the_carrier_table_is_exactly_the_renderers_fields():
    """Data to data, both ways: every field a renderer prints has a row, and every row names such a field (the table
    is the renderers', not a list of carriers someone thought of)."""
    table = C.DISPLAY_CARRIERS
    assert not any(_table_gaps(table).values()), _table_gaps(table)
    assert _namespace(table, "traceback") == _traceback_fields()
    assert _namespace(table, "pydantic.error") == _pydantic_error_keys()
    assert _namespace(table, "pydantic") == {"title"}
    assert _namespace(table, "builtin") == _builtin_rendered_attributes() | set(_BUILTIN_NOT_PROBED)
    assert not (_builtin_rendered_attributes() & set(_BUILTIN_NOT_PROBED))   # a probed field leaves the hand list
    assert _namespace(table, "outward_text") == _OUTWARD_TEXT_ROWS
    assert {k.split(":", 1)[0] for k in table} == {"traceback", "pydantic", "pydantic.error", "builtin", "outward_text"}


@pytest.mark.parametrize("row", ["traceback:exceptions", "traceback:__notes__", "traceback:_str", "pydantic.error:url",
                                 "pydantic.error:type", "builtin:filename", "builtin:path", "pydantic:title",
                                 "outward_text:reason"])
def test_a_dropped_row_turns_the_table_check_red(row):
    """The control: the check above fails when any one renderer-derived row is missing."""
    table = dict(C.DISPLAY_CARRIERS)
    del table[row]
    assert any(_table_gaps(table).values()), row


# ==== a token through every carrier, at the three formatters ==========================================================

def _validation(title="OrdinaryModel", code="fixed_error", loc=("field",), inp="ordinary", msg="ordinary detail",
                ctx=None):
    err = PydanticCustomError(code, msg, ctx) if ctx else PydanticCustomError(code, msg)
    return ValidationError.from_exception_data(title, [{"type": err, "loc": loc, "input": inp}])


class _DisplayGroup(ExceptionGroup):
    """An ordinary display override (the reviewer's): traceback still renders its children."""
    def __str__(self):
        return str(self.args[0])


class _DeriveGroup(ExceptionGroup):
    """A `derive` override that would put the token back into any group built through it."""
    def derive(self, excs):
        return ExceptionGroup(GH, list(excs))


def _noted(exc, note):
    exc.add_note(note)
    return exc


def _caused():
    exc = ValueError("ordinary")
    exc.__cause__ = ValueError(GH)
    return exc


def _contexted():
    try:
        raise ValueError(GH)
    except ValueError:
        try:
            raise ValueError("ordinary")
        except ValueError as exc:
            return exc


def _reasoned(reason):
    exc = ValueError("ordinary detail")
    exc.reason = reason
    return exc


def _suggesting():
    """An AttributeError whose `obj` has an attribute named like the token: the renderer's "Did you mean" line prints
    that name even after `args` is rewritten (its `str()` is then the withheld message alone). The case only a check of
    the RENDERING sees: a `str()`-plus-notes check passes it."""
    import types
    return AttributeError("x", name=GH[:-1] + "Z", obj=types.SimpleNamespace(**{GH: 1}))


def _depth3():
    return ExceptionGroup("one", [ExceptionGroup("two", [ExceptionGroup("three", [ValueError(GH)])]),
                                  _noted(ValueError("ordinary"), GH)])


#: (case, factory, shown by the original's rendering or only by `outward_text`'s reading of an attribute)
CASES = [
    ("traceback:_str", lambda: ValueError(GH), "render"),
    ("traceback:__notes__", lambda: _noted(ValueError("ordinary"), GH), "render"),
    ("traceback:__cause__", _caused, "render"),
    ("traceback:__context__", _contexted, "render"),
    ("traceback:exceptions", lambda: _DisplayGroup("ordinary", [ValueError(GH)]), "render"),
    ("group:depth-3", _depth3, "render"),
    ("group:base-with-interrupt", lambda: BaseExceptionGroup("g", [KeyboardInterrupt(GH), ValueError("x")]), "render"),
    ("group:child-notes", lambda: ExceptionGroup("g", [_noted(ValueError("x"), GH)]), "render"),
    ("group:child-title", lambda: ExceptionGroup("g", [_validation(title=GH)]), "render"),
    ("group:child-code", lambda: ExceptionGroup("g", [_validation(code=GH)]), "render"),
    ("group:child-context", lambda: ExceptionGroup("g", [_contexted()]), "render"),
    ("group:derive-override", lambda: _DeriveGroup("ordinary", [ValueError(GH)]), "render"),
    ("traceback:text", lambda: SyntaxError("m", ("f", 1, 2, GH, 1, 3)), "render"),
    ("traceback:filename", lambda: SyntaxError("m", (GH, 1, 2, "t", 1, 3)), "render"),
    ("pydantic:title", lambda: _validation(title=GH), "render"),
    ("pydantic.error:type", lambda: _validation(code=GH), "render"),
    ("pydantic.error:loc", lambda: _validation(loc=(GH,)), "render"),
    ("pydantic.error:msg", lambda: _validation(msg=GH), "render"),
    ("pydantic.error:input", lambda: _validation(inp=GH), "render"),
    ("pydantic.error:ctx", lambda: _validation(msg="value {x}", ctx={"x": GH}), "render"),
    ("builtin:filename", lambda: OSError(2, "No such file", GH), "render"),
    ("builtin:filename2", lambda: OSError(2, "No such file", "f", None, GH), "render"),
    ("builtin:strerror", lambda: OSError(2, GH), "render"),
    ("builtin:reason", lambda: UnicodeDecodeError("utf-8", b"x", 0, 1, GH), "render"),
    ("builtin:msg", lambda: ImportError(GH), "render"),
    ("builtin:key_repr", lambda: KeyError(GH), "render"),
    ("builtin:obj", _suggesting, "render"),
    ("outward_text:reason", lambda: _reasoned(GH), "attribute"),
    ("outward_text:field", lambda: C.ArgumentRefused("m", field=GH, reason="not_accepted"), "attribute"),
]
IDS = [c[0] for c in CASES]

#: table rows with no case above, each for its stated reason: no text of their own, outside the contract, or a field
#: a properly constructed instance does not render (the probe sets them on a bare instance; the render check would
#: refuse them anyway)
_NO_CASE = {
    "traceback:__suppress_context__": "a flag", "traceback:_exc_metadata": "no constructible text",
    "traceback:_exc_type": "a type object", "traceback:_have_exc_type": "a flag", "traceback:_is_syntax_error": "a flag",
    "traceback:max_group_width": "a setting", "traceback:max_group_depth": "a setting",
    "traceback:exc_type_qualname": "a program identifier (out of scope)",
    "traceback:exc_type_module": "a program identifier (out of scope)", "traceback:stack": "the program's frames",
    "traceback:lineno": "an int", "traceback:end_lineno": "an int", "traceback:offset": "an int",
    "traceback:end_offset": "an int", "traceback:msg": "a SyntaxError's message (as _str)",
    "pydantic.error:url": "embeds the error type (as type)",
    "builtin:errno": "an int", "builtin:encoding": "a codec name a constructed instance prints from a fixed set",
    "builtin:start": "an int", "builtin:end": "an int",
    "builtin:object": "a constructed instance prints one character of it", "builtin:name": "renders only on a bare "
    "instance", "builtin:path": "renders only on a bare instance", "builtin:name_from": "renders only on a bare instance",
    "outward_text:allowed": "module constants (the census below)", "outward_text:class_name": "a program identifier",
}


def test_every_carrier_row_has_a_case_or_a_stated_reason():
    """The cases cover the table: each row has a token case, or is named with its reason above (and not both)."""
    rows = set(C.DISPLAY_CARRIERS)
    covered = {c[0] for c in CASES} & rows
    assert covered | set(_NO_CASE) == rows, rows ^ (covered | set(_NO_CASE))
    assert not covered & set(_NO_CASE)


def _shown(exc) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


@pytest.mark.parametrize("case,factory,kind", CASES, ids=IDS)
def test_the_original_displays_the_token(case, factory, kind):
    """The positive control for every row below: unwithheld, the object really shows the token (a case that never
    displayed it would pass the withheld check vacuously)."""
    exc = factory()
    if kind == "render":
        assert GH in _shown(exc), case
    else:
        assert GH in (getattr(exc, "reason", None) or "") + (getattr(exc, "field", None) or ""), case


@pytest.mark.parametrize("case,factory,kind", CASES, ids=IDS)
def test_the_cli_defect_path_withholds_every_carrier(monkeypatch, capsys, case, factory, kind):
    """The real `cli.main` defect boundary, the verb replaced by the producer: the raised object shows nothing of the
    token, passes the final check, and is still a crash (never a clean exit)."""
    def fault(args, parser):
        raise factory()
    monkeypatch.setitem(cli._VERBS, "selfcheck", fault)
    if isinstance(factory(), (OSError, C.ArgumentRefused)):            # the CLI's refusal kinds: one line, exit 1
        assert cli.main(["selfcheck"]) == 1                                  # reached: the refusal branch
        err = capsys.readouterr().err
        assert err.strip() and GH not in err, (case, err)
        return
    with pytest.raises(BaseException) as caught:
        cli.main(["selfcheck"])
    out = caught.value
    assert out.__suppress_context__                                        # reached: the defect path raised it
    assert GH not in _shown(out), (case, _shown(out)[-300:])
    assert C._display_safe(out), case


@pytest.mark.parametrize("case,factory,kind", CASES, ids=IDS)
def test_outward_text_names_no_carrier(case, factory, kind):
    text = C.outward_text(factory())
    assert text and GH not in text, (case, text)


@pytest.mark.parametrize("route", ["binding", "mcp"])
@pytest.mark.parametrize("case,factory,kind", [c for c in CASES if issubclass(type(c[1]()), Exception)],
                         ids=[c[0] for c in CASES if issubclass(type(c[1]()), Exception)])
def test_the_served_routes_withhold_every_carrier(tmp_path, monkeypatch, route, case, factory, kind):
    """Both served routes, the tool body replaced by the producer (the reviewer's construction): the call reached the
    producer, the outward formatter answered, and nothing of the token is in what the model would see."""
    from veracium import mcp_server as MCP
    from veracium.adapters._surface import Binding
    m = T._mem(tmp_path)
    reached = []

    def fault(*args, **kwargs):
        reached.append(True)
        raise factory()
    monkeypatch.setattr(m, "maintain", fault)
    try:
        if route == "binding":
            call = lambda: Binding(m, user_id="u", capability="direct").call("maintain", {})   # noqa: E731
        else:
            server = MCP.build_server(m, default_user="u", capability="direct")
            call = lambda: asyncio.run(server.call_tool("maintain", {}))                       # noqa: E731
        with pytest.raises(Exception) as caught:
            call()
        shown = str(caught.value)
    finally:
        m.close()
    assert reached == [True], case                                          # reached: the producer ran
    assert GH not in shown, (case, shown)


# ==== groups at depth (research's addition 3) =========================================================================

def _leaves(exc) -> list:
    if isinstance(exc, BaseExceptionGroup):
        return [x for c in exc.exceptions for x in _leaves(c)]
    return [exc]


@pytest.mark.parametrize("case", ["group:depth-3", "group:base-with-interrupt", "group:derive-override",
                                  "traceback:exceptions", "group:child-title", "group:child-code",
                                  "group:child-notes", "group:child-context"])
def test_a_withheld_group_keeps_its_shape_in_built_in_groups(case):
    """Each group is rebuilt as a BUILT-IN group (never the subclass, its derive or its __str__), every level of it, with
    the same number of leaves of the same kinds; a KeyboardInterrupt child keeps the group a BaseExceptionGroup."""
    orig = dict((c[0], c[1]) for c in CASES)[case]()
    kinds = [type(x).__name__ for x in _leaves(orig)]
    out = C.withheld_defect(orig)
    stack = [out]
    while stack:
        g = stack.pop()
        if isinstance(g, BaseExceptionGroup):
            assert type(g) in (ExceptionGroup, BaseExceptionGroup), type(g)
            stack.extend(g.exceptions)
    assert len(_leaves(out)) == len(kinds)
    assert all(type(a).__name__ in (b, "RuntimeError", "ValidationError") for a, b in zip(_leaves(out), kinds))
    if case == "group:base-with-interrupt":
        assert type(out) is BaseExceptionGroup
    assert GH not in _shown(out)


@pytest.mark.parametrize("case", ["pydantic:title", "pydantic.error:type", "pydantic.error:loc", "pydantic.error:msg",
                                  "pydantic.error:input", "pydantic.error:ctx"])
def test_a_withheld_validation_error_stays_structured_with_closed_values(case):
    """The structured branch is KEPT (a crash still reads as the validation error it was, as R4-05 accepted), and every
    value it prints is closed: a declared title or the withheld one, closed error types, withheld messages. The final
    check alone would hide a builder that copies an input title or code (it would fall back to a plain RuntimeError);
    this is the assertion that keeps that builder honest."""
    out = C.withheld_defect(dict((c[0], c[1]) for c in CASES)[case]())
    assert isinstance(out, ValidationError), type(out)                     # reached: the rebuilt validation error
    assert out.title in C._declared_titles() | {C.WITHHELD_TITLE}, out.title
    errs = out.errors(include_url=False, include_context=True, include_input=True)
    assert errs and all(e["type"] in C._declared_error_types() and e["msg"] == C.WITHHELD_ERROR_MESSAGE
                        and e.get("input") is None for e in errs), errs
    assert GH not in _shown(out)


def test_a_group_too_deep_to_rebuild_is_replaced_past_the_bound():
    """Past the rebuild depth, the subtree is replaced by one content-free defect (never returned as it is); the
    levels above stay built-in groups, and the whole passes the final check."""
    g = ValueError(GH)
    for _ in range(C._GROUP_DEPTH + 2):
        g = ExceptionGroup("level", [g])
    out = C.withheld_defect(g)
    depth, x = 0, out
    while isinstance(x, BaseExceptionGroup):
        assert type(x) is ExceptionGroup
        depth, x = depth + 1, x.exceptions[0]
    assert depth <= C._GROUP_DEPTH and type(x) is RuntimeError, (depth, type(x))   # reached: the bound cut it
    assert GH not in _shown(out) and C._display_safe(out)


# ==== the final check refuses each unsafe object (research's addition 1: the check, not only the builder) ==============

@pytest.mark.parametrize("make", [
    lambda m: _DisplayGroup(m, [RuntimeError(m.replace("ExceptionGroup", "RuntimeError"))]),   # a subclass group
    lambda m: ExceptionGroup(m, [_noted(RuntimeError(m.replace("ExceptionGroup", "RuntimeError")), "n")]),  # child note
    lambda m: ExceptionGroup(m, [ValueError(GH)]),                                               # an unwithheld child
    lambda m: ExceptionGroup("ordinary", [RuntimeError(m.replace("ExceptionGroup", "RuntimeError"))]),  # its own message
    lambda m: _validation(title=GH, msg=C.WITHHELD_ERROR_MESSAGE, inp=None),                     # an undeclared title
    lambda m: _validation(code=GH, msg=C.WITHHELD_ERROR_MESSAGE, inp=None),                      # a custom code
], ids=["subclass", "child-note", "child-unwithheld", "own-message", "title", "code"])
def test_the_final_check_refuses_each_unsafe_object(make):
    msg = f"ExceptionGroup{C._WITHHELD_SUFFIX}"
    assert not C._display_safe(make(msg))


# ==== one declared reason set; the field names; the allowed lists (research's addition 2) ============================

def _module_trees():
    for f in sorted(SRC.rglob("*.py")):
        yield f, ast.parse(f.read_text(encoding="utf-8"))


def _exception_classes() -> set:
    """Every class src/ defines that derives, through src/'s own classes, from a built-in exception."""
    builtin_exc = {n for n in dir(builtins) if isinstance(getattr(builtins, n), type)
                   and issubclass(getattr(builtins, n), BaseException)}
    bases = {}
    for _, tree in _module_trees():
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef):
                bases[n.name] = {b.id if isinstance(b, ast.Name) else getattr(b, "attr", None) for b in n.bases}
    out, changed = set(), True
    while changed:
        changed = False
        for name, bs in bases.items():
            if name not in out and bs & (builtin_exc | out):
                out.add(name)
                changed = True
    return out


def _reason_census() -> tuple[set, list]:
    """Every reason src/'s exceptions carry: class-level `reason = "..."`, constructor defaults, and each construction's
    reason (keyword, or the first positional for classes whose first parameter is `reason`). An f-string reason built
    from a local helper's literal names (`procedures._opt`) is expanded from that helper's call sites. Returns
    (reasons, anything not resolved to literals)."""
    excs = _exception_classes()
    first_positional = set()
    found, unresolved = set(), []
    for _, tree in _module_trees():
        for n in ast.walk(tree):
            if isinstance(n, ast.ClassDef) and n.name in excs:
                for s in n.body:
                    if (isinstance(s, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "reason" for t in s.targets)
                            and isinstance(s.value, ast.Constant)):
                        found.add(s.value.value)
                    if isinstance(s, ast.FunctionDef) and s.name == "__init__":
                        params = [a.arg for a in s.args.args[1:]]
                        if params[:1] == ["reason"]:
                            first_positional.add(n.name)
                        kw = s.args.kwonlyargs
                        for a, d in zip(kw, s.args.kw_defaults):
                            if a.arg == "reason" and isinstance(d, ast.Constant):
                                found.add(d.value)
    for f, tree in _module_trees():
        nested = {id(h) for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                  for h in x.body if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for fn in [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and id(x) not in nested]:
            helpers = {h.name: h.args.args[0].arg for h in fn.body
                       if isinstance(h, ast.FunctionDef) and h.args.args}       # nested helpers and their first param
            helper_calls = {}
            for c in ast.walk(fn):
                if (isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id in helpers and c.args
                        and isinstance(c.args[0], ast.Constant)):
                    helper_calls.setdefault(helpers[c.func.id], set()).add(c.args[0].value)
            for c in ast.walk(fn):
                if not isinstance(c, ast.Call):
                    continue
                name = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                if name not in excs:
                    continue
                v = next((k.value for k in c.keywords if k.arg == "reason"), None)
                if v is None and name in first_positional and c.args:
                    v = c.args[0]
                if v is None:
                    continue
                if isinstance(v, ast.Constant):
                    found.add(v.value)
                elif (isinstance(v, ast.JoinedStr) and len(v.values) == 2 and isinstance(v.values[1], ast.Constant)
                      and isinstance(v.values[0], ast.FormattedValue) and isinstance(v.values[0].value, ast.Name)
                      and helper_calls.get(v.values[0].value.id)):
                    found.update(f"{h}{v.values[1].value}" for h in helper_calls[v.values[0].value.id])
                else:
                    unresolved.append(f"{f.relative_to(ROOT)}:{c.lineno}")
    for f, tree in _module_trees():                     # the closed vocabularies a constructor enforces
        for s in tree.body:
            if (isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name)
                    and s.targets[0].id in _ENFORCED_VOCABULARIES):
                v = s.value.args[0] if isinstance(s.value, ast.Call) and s.value.args else s.value   # frozenset({...})
                found.update(e.value for e in getattr(v, "elts", []) if isinstance(e, ast.Constant))
    return found, unresolved


#: module-level tuples a constructor refuses any reason outside of (UndoRefused, ReplyRefused, MintError, TrustRefused):
#: every member is a reason the class may carry, raised literally or not
_ENFORCED_VOCABULARIES = {"UNDO_REFUSAL_REASONS", "REPLY_REFUSAL_REASONS", "_MINT_REASONS", "REFUSALS", "REASONS"}


def test_every_reason_the_product_raises_is_declared_and_every_declared_reason_is_raised():
    """Both ways: a new reason fails until it is declared, and a declared reason nothing raises is stale (the trust
    refusals are declared by `trust_tools.REFUSALS`, which TrustRefused enforces at construction)."""
    from veracium import trust_tools
    found, unresolved = _reason_census()
    assert not unresolved, unresolved
    assert found <= C.DECLARED_REASONS, found - C.DECLARED_REASONS
    assert C.DECLARED_REASONS <= found | set(trust_tools.REFUSALS), C.DECLARED_REASONS - found - set(trust_tools.REFUSALS)
    assert set(trust_tools.REFUSALS) <= C.DECLARED_REASONS


def test_no_exception_reason_is_assigned_outside_its_constructor():
    """`.reason` is set only by a class attribute or by `self.reason = reason` in `__init__`: an assignment anywhere
    else would carry a reason the census above cannot see."""
    bad = []
    for f, tree in _module_trees():
        for fn in [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for s in ast.walk(fn):
                if not isinstance(s, ast.Assign):
                    continue
                for t in s.targets:
                    pairs = (list(zip(t.elts, s.value.elts)) if isinstance(t, ast.Tuple) and isinstance(s.value, ast.Tuple)
                             else [(e, None) for e in t.elts] if isinstance(t, ast.Tuple) else [(t, s.value)])
                    for tgt, val in pairs:
                        if isinstance(tgt, ast.Attribute) and tgt.attr == "reason":
                            if not (fn.name == "__init__" and isinstance(tgt.value, ast.Name) and tgt.value.id == "self"
                                    and isinstance(val, ast.Name) and val.id == "reason"):
                                bad.append(f"{f.relative_to(ROOT)}:{s.lineno}")
    assert not bad, bad


def test_every_refusal_field_is_a_declared_name():
    """`ArgumentRefused.field` prints only as a declared name (`_declared_argument_names`). Every field src/ raises is a
    literal at its site, or a loop variable over literal (name, value) pairs; each is declared, and `ARGUMENT_NAMES`
    holds no name nothing raises."""
    names, unresolved = set(), []
    for f, tree in _module_trees():
        for fn in [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            pairs = {e.elts[0].value for e in ast.walk(fn) if isinstance(e, ast.Tuple) and len(e.elts) == 2
                     and isinstance(e.elts[0], ast.Constant) and isinstance(e.elts[0].value, str)}
            for c in ast.walk(fn):
                if not (isinstance(c, ast.Call) and getattr(c.func, "attr", getattr(c.func, "id", None))
                        in ("ArgumentRefused", "ArgumentTypeRefused")):
                    continue
                v = next((k.value for k in c.keywords if k.arg == "field"), None)
                if isinstance(v, ast.Constant):
                    names.add(v.value)
                elif isinstance(v, ast.Name) and pairs:
                    names.update(pairs)
                elif isinstance(v, ast.Name) and fn.name == "_cred_ingress":
                    pass                                    # its (name, value) pairs come from its callers: read below
                else:
                    unresolved.append(f"{f.relative_to(ROOT)}:{c.lineno}")
    # the ingress screen's pairs are built by its CALLERS: every literal first element passed to `_cred_ingress`
    for f, tree in _module_trees():
        for c in ast.walk(tree):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", None) == "_cred_ingress":
                for kw in c.keywords:
                    for el in getattr(kw.value, "elts", []):
                        if isinstance(el, ast.Tuple) and el.elts and isinstance(el.elts[0], ast.Constant):
                            names.add(el.elts[0].value)
    assert not unresolved, unresolved
    declared = C._declared_argument_names()
    assert names <= declared, names - declared
    assert C.ARGUMENT_NAMES <= names and not (C.ARGUMENT_NAMES & C._declared_field_names()), C.ARGUMENT_NAMES


def test_every_allowed_list_is_built_from_module_constants():
    """`ArgumentRefused.allowed` is printed as the closed vocabulary; every raise builds it from a module-level name,
    never from a parameter or a local."""
    bad = []
    for f, tree in _module_trees():
        module_names = {t.id for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign))
                        for t in (s.targets if isinstance(s, ast.Assign) else [s.target]) if isinstance(t, ast.Name)}
        for c in ast.walk(tree):
            if isinstance(c, ast.Call) and getattr(c.func, "attr", getattr(c.func, "id", None)) == "ArgumentRefused":
                v = next((k.value for k in c.keywords if k.arg == "allowed"), None)
                if v is None:
                    continue
                used = {n.id for n in ast.walk(v) if isinstance(n, ast.Name)} - {"sorted", "list", "tuple"}
                if not used or not used <= module_names:
                    bad.append(f"{f.relative_to(ROOT)}:{c.lineno}")
    assert not bad, bad


# ==== the served helper's locator label (the reviewer's bounded observation) ==========================================

def test_a_served_locator_label_never_names_a_shaped_key():
    """`served_result` labels a shaped value under an `*_id` key by its ordinal and that key: the key is the MASKED one,
    so a shaped key ending in `_id` over a shaped value copies nothing (the reviewer's helper-level observation)."""
    from veracium import mcp_server as MCP
    out = MCP.served_result({f"x_{GH}_id": GH, "edge_id": GH, "nested": {f"{GH}_id": GH}})
    assert GH not in json.dumps(out), out
    assert "record 1 of this report (edge_id)" in json.dumps(out)           # reached: the ordinal label still works
