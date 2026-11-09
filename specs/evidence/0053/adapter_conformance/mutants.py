# Mutation-Matrix: tests/test_0053_adapter_conformance.py::test_a_mutant_whose_site_moved_is_refused
"""specs/0053 §4: the mutant row, applied to the adapter UNDER TEST, never only to a reference.

Each mutant names its site: one or more (file, anchor, replacement) edits to a copy of `veracium/adapters/`. The gate
refuses a mutant whose anchor does not occur exactly once, or whose edit leaves the file unchanged (`DoesNotApply`): a
moved site is a refusal, never a silent pass. The mutated copy is imported as its own package, so the drivers run the
mutated adapter in process, and a kill is counted only when the families that went red are EXACTLY the families its
row names (`expect`): every one of them collected, run and failed, and no other.

The canonicaliser's own mutants (§3a, §4) edit a copy of `canon.py`, or (C4) the declared lists, and must be caught by
the planted pairs or by the measured-list check.
"""
from __future__ import annotations

import importlib
import importlib.util
import itertools
import os
import shutil
import sys
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
ADAPTERS = os.path.join(ROOT, "src", "veracium", "adapters")
CANON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canon.py")

S, L = "_surface.py", "langchain.py"
BOTH, LC = ("core", "langchain"), ("langchain",)

_REC_END = '                                    principal=self._principal)\n        if name == "answer":'
_ANS = '            return _mcp.answer_impl(mem, user, a["query"], principal=self._principal)'
_REM_OPEN = '            return _mcp.remember_impl('
_REM_CLOSE = '                                      capability=self._capability)\n        if name == "recall":'
_LAST = '        raise ValueError(f"unknown tool {name!r}")   # unreachable while TOOLS and the branches agree\n'
_SPECS = 'json.loads(json.dumps(t.parameters))) for t in _registered(mem))'


class DoesNotApply(AssertionError):
    pass


@dataclass(frozen=True)
class Mutant:
    id: str
    expect: frozenset
    adapters: tuple
    edits: tuple
    what: str


def _m(id, expect, adapters, edits, what):
    return Mutant(id, frozenset(expect), adapters, tuple(edits), what)


MUTANTS = (
    _m("never-assert-header-stripped", {"K3"}, BOTH,
       [(S, _REC_END, _REC_END.replace(
           "principal=self._principal)",
           r'principal=self._principal).replace("## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)\n", "")'))],
       "the never-assert header stripped from recall's text (the ruling's 'a mutant that drops a label')"),
    _m("claim-front-label-removed", {"K3"}, BOTH,
       [(S, _REC_END, _REC_END.replace(
           "principal=self._principal)",
           'principal=self._principal).replace("[UNVERIFIED third-party claim, never assert as fact] ", "", 1)'))],
       "one claim line's front label removed"),
    _m("own-budget-trim", {"K3", "K6"}, BOTH,       # K6: a below-floor budget no longer reaches the library's raise
       [(S, 'token_budget=a["token_budget"],', "token_budget=None,"),
        (S, _REC_END, _REC_END.replace("principal=self._principal)",
                                       'principal=self._principal)[: (a["token_budget"] or 10 ** 9) * 4]'))],
       "the adapter trims to its own budget instead of passing token_budget"),
    _m("procedural-in-recall", {"K3"}, BOTH,
       [(S, _REC_END, _REC_END.replace(
           "principal=self._principal)",
           'principal=self._principal) + "".join("\\n" + d["summary"] for d in '
           '_mcp.describe_procedures_impl(mem, user, None)["descriptions"])'))],
       "a procedural record surfaced in recall's context"),
    _m("abstention-replaced", {"K4"}, BOTH,
       [(S, _ANS, '            return (lambda s: "Most likely yes, going by your history." if "know" in s else s)('
                  '_mcp.answer_impl(mem, user, a["query"], principal=self._principal))')],
       "the abstention replaced by a fallback answer"),
    _m("procedure-answered", {"K4"}, BOTH,
       [(S, _ANS, _ANS + ' + "".join(" " + d["attribution"] for d in '
                         '_mcp.describe_procedures_impl(mem, user, a["query"])["descriptions"])')],
       "a procedural question answered with the procedure's text (B1: the gate never sees P)"),
    _m("third-party-forwarded-as-user", {"K5"}, BOTH,
       [(S, 'author=a["author"], event_type=a["event_type"],',
         'author=("user" if a["author"] == "third_party" else a["author"]), event_type=a["event_type"],')],
       "author forwarded as 'user' when the model passed 'third_party'"),
    _m("derived-from-dropped", {"K5"}, BOTH,
       [(S, 'date=a["date"], derived_from=a["derived_from"], source_id=self._source_id,',
         'date=a["date"], derived_from=None, source_id=self._source_id,')],
       "derived_from dropped (seen after canonicalisation)"),
    _m("date-dropped", {"K5"}, BOTH,
       [(S, 'date=a["date"], derived_from=a["derived_from"], source_id=self._source_id,',
         'date=None, derived_from=a["derived_from"], source_id=self._source_id,')],
       "remember's model-supplied date dropped: an input, compared as stored in the dated group"),
    _m("operator-counter-left", {"K5"}, BOTH,
       [(S, _REM_OPEN, '            return (lambda r: {**r, "provenance_raises_discarded": 0} if "facts" in r else r)'
                       '(_mcp.remember_impl('),
        (S, _REM_CLOSE, _REM_CLOSE.replace("capability=self._capability)", "capability=self._capability))"))],
       "one operator counter left in remember's result"),
    _m("refusal-returned-as-success", {"K6"}, BOTH,
       [(S, _REM_OPEN, '            return (lambda r: {"ok": True} if r.get("ok") is False else r)(_mcp.remember_impl('),
        (S, _REM_CLOSE, _REM_CLOSE.replace("capability=self._capability)", "capability=self._capability))"))],
       "a serialized refusal returned as {'ok': true}"),
    _m("capability-from-argument", {"K1", "K7"}, BOTH,
       [(S, _SPECS, '_with_arg(t.name, "record_procedure", "capability", json.loads(json.dumps(t.parameters)))) '
                    'for t in _registered(mem))'),
        (S, '                                              capability=self._capability)',
         '                                              capability=args.get("capability", self._capability))'),
        (S, _LAST, _LAST + '\n\ndef _with_arg(tool, only, arg, p):\n    if only in (tool, "*"):\n'
                           '        p["properties"][arg] = {"anyOf": [{"type": "string"}, {"type": "null"}], '
                           '"default": None, "title": arg}\n    return p\n')],
       "the capability read from a tool argument"),
    _m("user-id-parameter", {"K1", "K8"}, BOTH,
       [(S, _SPECS, '_with_arg(t.name, "*", "user_id", json.loads(json.dumps(t.parameters)))) '
                    'for t in _registered(mem))'),
        (S, "        mem, user = self._mem, self._user", '        mem, user = self._mem, args.get("user_id") or self._user'),
        (S, _LAST, _LAST + '\n\ndef _with_arg(tool, only, arg, p):\n    if only in (tool, "*"):\n'
                           '        p["properties"][arg] = {"anyOf": [{"type": "string"}, {"type": "null"}], '
                           '"default": None, "title": arg}\n    return p\n')],
       "a user_id parameter added, and honoured"),
    _m("principal-not-passed", {"K8"}, BOTH,
       [(S, _REC_END, _REC_END.replace("principal=self._principal)", "principal=None)")),
        (S, _ANS, _ANS.replace("principal=self._principal)", "principal=None)")),
        (S, 'a["query"], principal=self._principal)\n        raise', 'a["query"], principal=None)\n        raise')],
       "the host principal not passed through"),
    _m("description-shortened-core", {"K2"}, BOTH,
       [(S, "ToolSpec(t.name, t.description, ", "ToolSpec(t.name, t.description[:1024], ")],
       "a description shortened (the shared core)"),
    # the LangChain adapter's own seams
    _m("description-shortened-langchain", {"K2"}, LC,
       [(L, "description=spec.description,", "description=spec.description[:1024],")],
       "a description shortened in the LangChain tool"),
    _m("schema-rewritten-langchain", {"K1"}, LC,
       [(L, "args_schema=spec.parameters,",
         'args_schema={**spec.parameters, "properties": {k: {"type": "string"} '
         'for k in spec.parameters["properties"]}},')],
       "the LangChain tool's schema rewritten (every parameter a plain string)"),
    _m("raise-swallowed-langchain", {"K6"}, LC,
       [(L, "            raise ToolException(str(exc)) from exc", '            return {"ok": True}')],
       "a library raise swallowed into a success (B2)"),
    _m("tool-error-unhandled-langchain", {"K6"}, LC,
       [(L, "handle_tool_error=True)", "handle_tool_error=False)")],
       "a refusal raised through the framework as an exception"),
)

#: The row as the draft names it, and why a mutant is absent from an adapter's row (§5: the row records it).
NOT_APPLICABLE = {
    "grounded-unverified-merged": "neither adapter offers a structured form: recall reaches the framework as the "
                                  "library's text alone",
}

_counter = itertools.count()


def apply_edits(src_dir: str, dst_dir: str, edits) -> None:
    shutil.copytree(src_dir, dst_dir, ignore=shutil.ignore_patterns("__pycache__"))
    for fname, anchor, repl in edits:
        path = os.path.join(dst_dir, fname)
        with open(path) as fh:
            text = fh.read()
        n = text.count(anchor)
        if n != 1:
            raise DoesNotApply(f"{fname}: the anchor occurs {n} times, not once: {anchor[:80]!r}")
        new = text.replace(anchor, repl)
        if new == text:
            raise DoesNotApply(f"{fname}: the edit leaves the file unchanged: {anchor[:80]!r}")
        with open(path, "w") as fh:
            fh.write(new)


def load_package(pkg_dir: str, *, with_langchain: bool):
    """Import a copy of veracium/adapters as a sibling subpackage of `veracium` (`veracium.adapters_m<N>_<pid>`), so
    its relative `from .. import mcp_server` reaches the library; return (surface, langchain-or-None)."""
    import veracium
    name = f"veracium.adapters_m{next(_counter)}_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(name, os.path.join(pkg_dir, "__init__.py"),
                                                  submodule_search_locations=[pkg_dir])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True                # a fresh directory per mutant, and no bytecode written beside it
    try:
        spec.loader.exec_module(mod)
        surface = importlib.import_module(name + "._surface")
        lc = importlib.import_module(name + ".langchain") if with_langchain else None
    finally:
        sys.dont_write_bytecode = old
    if os.path.dirname(os.path.abspath(surface.__file__)) != os.path.abspath(pkg_dir):
        raise AssertionError(f"the mutated package imported {surface.__file__}, not its own copy")
    return surface, lc


def materialise(mutant: Mutant, workdir: str, *, with_langchain: bool):
    dst = os.path.join(workdir, f"mut-{mutant.id}-{next(_counter)}")
    apply_edits(ADAPTERS, dst, mutant.edits)
    return load_package(dst, with_langchain=with_langchain)


def red_families(result: dict) -> frozenset:
    return frozenset(f for f, v in result.items() if v)


# --------------------------------------------------------------------------- the canonicaliser's mutants

CANON_MUTANTS = (
    ("ids-renamed-per-table",
     [("canon.py", '                idmap.setdefault(v, f"<id:{len(idmap)}>")',
       '                idmap.setdefault((t, v), f"<id:{t}:{sum(1 for k in idmap if k[0] == t)}>")'),
      ("canon.py", "            if _scalar(v) and v in idmap:\n                return idmap[v]",
       "            if _scalar(v) and (_T[0], v) in idmap:\n                return idmap[(_T[0], v)]"),
      ("canon.py", "        canon, clocks = [], {}\n        for t, n, c, path, v in ls:\n",
       "        canon, clocks = [], {}\n        for t, n, c, path, v in ls:\n            _T[0] = t\n"),
      ("canon.py", "_MIN_ID = 8", "_T = [None]\n_MIN_ID = 8"),
      ("canon.py", "        subs = sorted((k for k in idmap if isinstance(k, str) and len(k) >= _MIN_ID), key=len, "
                   "reverse=True)", "        subs = []")],
     "renaming ids per table instead of one store-wide map"),
    ("clocks-dropped",
     [("canon.py", "    places = [p for p in ka if ka[p] is not None and kb.get(p) is not None]",
       "    places = []")],
     "dropping clock columns instead of comparing their order"),
    ("tie-read-as-difference",
     [("canon.py", "            if sa * sb < 0:", "            if sa != sb:")],
     "reading a tie as a difference"),
)


def load_canon(edits, workdir: str):
    dst = os.path.join(workdir, f"canon-{next(_counter)}")
    os.makedirs(dst)
    shutil.copyfile(CANON, os.path.join(dst, "canon.py"))
    for fname, anchor, repl in edits:
        path = os.path.join(dst, fname)
        text = open(path).read()
        n = text.count(anchor)
        if n != 1:
            raise DoesNotApply(f"{fname}: the anchor occurs {n} times, not once: {anchor[:80]!r}")
        open(path, "w").write(text.replace(anchor, repl))
    name = f"canon_m{next(_counter)}_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(name, os.path.join(dst, "canon.py"))
    mod = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod
