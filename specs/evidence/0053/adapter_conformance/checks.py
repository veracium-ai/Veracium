# Mutation-Matrix: tests/test_0053_adapter_conformance.py::test_the_mutant_row_kills_exactly_its_families
"""specs/0053 §2-§4: the oracle, the anchors, the checks K1-K8, the measured lists and the canonicaliser's planted
pairs.

THE ORACLE is written here, independently of every adapter: the served surface (`build_server`'s registered tools,
listed through FastMCP's public `list_tools`) for K1/K2, and for values the `*_impl` functions called directly, with
the arguments validated by the served tool's own argument model (as an MCP call is). Each oracle call runs in its own
fresh copy of the fixture store and is computed once per run; every driver, mutated or not, is compared with it.

A driver factory is `factory(mem, binding) -> driver` (drivers.py). `run_families(factory)` returns
{family: [failure, ...]} over every case; an empty list is a pass.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import anyio

from veracium import mcp_server as M
from veracium.gate import ABSTAINED

from . import canon as K
from .canon import _strict_pairs
from . import fixture as F

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES = ("K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8")
NEVER_ASSERT = "## UNVERIFIED THIRD-PARTY CLAIMS (never assert as fact)"
Q_LABEL = "[UNVERIFIED third-party claim, never assert as fact] org:quickclaim claims:"
P_TEXT = "Weekly review on Sunday evenings"

#: §3a's declared lists, per clock group: MEASURED by `measured_lists` (both ways), never chosen. A dated write takes
#: its event time from the call's `date`, so the event-time leaves are inputs, compared as stored; an undated write
#: takes them from the wall clock, so in that group they are clocks.
_IDS = {
    ("edge_event", "edge_id", ()), ("edge_event", "state", ("$", "id")),
    ("edge_event", "state", ("$", "provenance", "evidence_ref")), ("edge_event", "state", ("$", "src")),
    ("edges", "id", ()), ("edges", "json", ("$", "id")), ("edges", "json", ("$", "provenance", "evidence_ref")),
    ("edges", "json", ("$", "src")),
    ("episodes", "id", ()), ("episodes", "json", ("$", "id")), ("episodes", "json", ("$", "provenance", "evidence_ref")),
    ("supersession_operations", "operation_id", ()), ("supersession_operations", "request_digest", ()),
    ("supersession_operations", "logical_request_digest", ()),
}
_EVENT_TIME = {
    ("edge_event", "state", ("$", "provenance", "observed_at")), ("edge_event", "state", ("$", "valid_from")),
    ("edges", "json", ("$", "provenance", "observed_at")), ("edges", "json", ("$", "valid_from")),
}
#: maintain (0053 v0.3 Q5): expiry flags and one consolidated pool. Its own ids (the operation, its owner, the ledger
#: rows, the new episode) and clocks (the lease, the ledger time, the events' recorded_at), measured from twin runs
_MAINTAIN_IDS = {
    ("consolidation_ops", "operation_id", ()), ("consolidation_ops", "owner", ()),
    ("contribution_ledger", "id", ()), ("contribution_ledger", "op_key", ()), ("contribution_ledger", "survivor_id", ()),
    ("episodes", "id", ()), ("episodes", "json", ("$", "id")), ("episodes", "json", ("$", "operation_id")),
    ("episodes", "json", ("$", "provenance", "evidence_ref")),
}
_MAINTAIN_CLOCKS = {("edge_event", "recorded_at", ()), ("consolidation_ops", "lease_expires_at", ()),
                    ("contribution_ledger", "created_at", ())}
DECLARED = {
    "dated": (frozenset(_IDS), frozenset({("edge_event", "recorded_at", ())})),
    "undated": (frozenset(_IDS), frozenset({("edge_event", "recorded_at", ())} | _EVENT_TIME)),
    "maintain": (frozenset(_MAINTAIN_IDS), frozenset(_MAINTAIN_CLOCKS)),
}


def load_cases(path=None):
    with open(path or os.path.join(HERE, "cases.json")) as fh:
        doc = json.load(fh, object_pairs_hook=_strict_pairs)
    q = doc["queries"]

    def resolve(v):
        return q[v[1:]] if isinstance(v, str) and v.startswith("@") else v
    for c in doc["cases"]:
        c["args"] = {k: resolve(v) for k, v in c["args"].items()}
    return doc


def binding(doc, name) -> dict:
    b = dict(doc["bindings"][name])
    if b.get("principal") == "PRINCIPAL":
        b["principal"] = F.PRINCIPAL
    return b


def _json_form(v):
    """The value as the served surface hands it over: JSON. A value that is not JSON is refused, by name."""
    try:
        return json.loads(json.dumps(v, ensure_ascii=False), object_pairs_hook=_strict_pairs)
    except (TypeError, ValueError) as exc:
        raise AssertionError(f"a reference value is not JSON-serialisable: {v!r:.200}") from exc


@dataclass
class Ref:
    case: dict
    outcome: tuple
    store: str
    prompts: list = field(default_factory=list)


class Oracle:
    def __init__(self, workdir: str):
        self.workdir = workdir
        self.template = F.build_template(os.path.join(workdir, "template"))
        self.doc = load_cases()
        mem = F.open_memory(F.fresh_copy(self.template, os.path.join(workdir, "served"), "served"))
        server = M.build_server(mem)
        self.listing = [{"name": t.name, "description": t.description, "parameters": t.inputSchema}
                        for t in anyio.run(server.list_tools)]
        self._meta = {t.name: t.fn_metadata for t in server._tool_manager.list_tools()}
        mem.close()
        self._n = 0
        self.refs = {c["id"]: self.run(c) for c in self.doc["cases"]}

    def fresh(self, tag: str) -> str:
        self._n += 1
        return F.fresh_copy(self.template, os.path.join(self.workdir, "runs"), f"{tag}-{self._n}")

    def call(self, mem, b: dict, tool: str, args: dict):
        meta = self._meta[tool]
        try:
            a = meta.arg_model.model_validate(meta.pre_parse_json(dict(args))).model_dump_one_level()
        except Exception as exc:                 # as FastMCP: any error while answering is the served error result
            return ("error", str(exc))
        user, cap, sid, pr = b["user_id"], b.get("capability"), b.get("source_id"), b.get("principal")
        try:
            if tool == "remember":
                v = M.remember_impl(mem, user, a["text"], author=a["author"], event_type=a["event_type"],
                                    date=a["date"], derived_from=a["derived_from"], source_id=sid, capability=cap)
            elif tool == "recall":
                v = M.recall_impl(mem, user, a["query"], token_budget=a["token_budget"], principal=pr)
            elif tool == "answer":
                v = M.answer_impl(mem, user, a["query"], principal=pr)
            elif tool == "maintain":
                v = M.maintain_impl(mem, user)
            elif tool == "record_procedure":
                v = M.record_procedure_impl(mem, user, a["summary"], a["basis"], author=a["author"],
                                            derived_from=a["derived_from"], relation=a["relation"], note=a["note"],
                                            date=a["date"], source_id=sid, capability=cap)
            elif tool == "describe_procedures":
                v = M.describe_procedures_impl(mem, user, a["query"], principal=pr)
            else:
                raise AssertionError(f"the oracle has no call for {tool!r}")
        except AssertionError:
            raise
        except Exception as exc:
            return ("error", str(exc))
        return ("ok", _json_form(v))

    def run(self, case: dict, tag="ref") -> Ref:
        path = self.fresh(f"{tag}-{case['id']}")
        llm = F.ScriptedComplete()
        mem = F.open_memory(path, llm)
        try:
            out = self.call(mem, binding(self.doc, case["binding"]), case["tool"], case["args"])
        finally:
            mem.close()
        return Ref(case, out, path, llm.prompts)


# --------------------------------------------------------------------------- anchors (§2)

def anchors(o: Oracle) -> list[str]:
    """Each class visible in the oracle, or the suite is VACUOUS. Read before any adapter runs."""
    r = {k: v.outcome for k, v in o.refs.items()}
    bad = []

    def need(cond, what):
        if not cond:
            bad.append(f"VACUOUS: {what}")
    text = lambda k: r[k][1] if r[k][0] == "ok" and isinstance(r[k][1], str) else ""
    need(NEVER_ASSERT in text("K3-Q") and Q_LABEL in text("K3-Q"), "Q: the reference recall lacks the never-assert "
         "header or the labelled QuickClaim line")
    need("has_diet: vegetarian" in text("K3-all"), "G: the grounded fact is not in the reference recall")
    need("works_as: manager at Acme" in text("K3-all") and "engineer at Acme" in text("K3-all"),
         "S: the superseded fact's current value or its history is missing")
    unverified = text("K3-all").split(NEVER_ASSERT)[-1] if NEVER_ASSERT in text("K3-all") else ""
    need("prefers: window seats" in unverified, "D: the derived record is not on the never-assert side")
    need("CONTESTED" in text("K3-all"), "C: the contention is not rendered")
    need("parrot" not in text("K3-all").lower(), "R: the revoked source's record reaches recall")
    need("[budget: dropped" in text("K3-T"), "T: the budget did not truncate")
    need(P_TEXT not in text("K3-P") and P_TEXT not in text("K3-all"), "P (recall): the procedure is in recall's text")
    gate_inputs = [p for role, p in o.refs["K4-P"].prompts if role == "gate"]
    need(gate_inputs and not any(P_TEXT in p for p in gate_inputs),
         "P (answer): the procedure's summary reached the gate's input, or the gate was never called")
    d = r["K3-describe-all"]
    need(d[0] == "ok" and P_TEXT in json.dumps(d[1]), "P: describe_procedures does not hold the procedure (the anchor "
         "would hold of an empty store)")
    need(bool(ABSTAINED.search(text("K4-A"))) and text("K4-A") == F.ABSTENTION, "A: the reference answer does not "
         "abstain")
    need(text("K4-G") != F.ABSTENTION, "G (answer): the grounded question abstains")
    need("vegan" in text("K8-u2-recall") and "vegetarian" not in text("K8-u2-recall"),
         "K8: the second user's recall does not differ from the first's")
    need("cello" in text("K8-u2-recall") and "cello" not in text("K8-principal-recall"),
         "K8: the principal's scope hides nothing in recall")
    need(text("K8-principal-answer") != text("K8-u2-answer"), "K8: the principal changes nothing in answer")
    # §2: the fixture configures no policy and no sinks, so a read leaves the store as it was (research's S1-5: the
    # claim had no check). Every read case's reference store equals the template under the canonical comparison
    reads = K.Canon(*DECLARED["dated"])
    for c in o.doc["cases"]:
        if c["tool"] in ("recall", "answer", "describe_procedures"):
            d = reads.differences(o.template, o.refs[c["id"]].store)
            need(not d, f"{c['id']}: the reference read wrote the store ({d[:1]})")
    need(NEVER_ASSERT not in text("K8-u2-recall"), "K8: the second user's store holds third-party content, so a "
         "never-assert mutant would reach K8's cases as well as K3's")
    return bad


# --------------------------------------------------------------------------- I10: the oracle reuses no adapter code

#: the oracle side of the suite: the modules that compute or judge what the adapters must equal
ORACLE_MODULES = ("checks.py", "canon.py", "fixture.py", "planted.py")
_ADAPTERS = "veracium.adapters"


def _names_adapters(module) -> bool:
    return module == _ADAPTERS or (module or "").startswith(_ADAPTERS + ".")


def oracle_import_problems(paths=None) -> list[str]:
    """0053 v0.3 I10 (§10 Q4): no oracle-side module imports `veracium.adapters`, in any form: `import
    veracium.adapters[...]` (aliased or not), `from veracium.adapters[...] import ...`, `from veracium import adapters`, an
    attribute read `veracium.adapters` on the package, or a string naming it handed to `importlib.import_module` or
    `__import__`. Its anchor: every named module was parsed, holds statements, and the set holds at least one `veracium`
    import (checks.py imports veracium.mcp_server), so a scan that parsed nothing cannot read as clean."""
    import ast
    paths = [os.path.join(HERE, m) for m in ORACLE_MODULES] if paths is None else list(paths)
    bad, veracium_imports = [], 0
    for path in paths:
        name = os.path.basename(path)
        try:
            tree = ast.parse(open(path).read())
        except (OSError, SyntaxError) as exc:
            bad.append(f"{name}: not parsed ({exc})")
            continue
        if not tree.body:
            bad.append(f"{name}: parsed to nothing")
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    veracium_imports += a.name.split(".")[0] == "veracium"
                    if _names_adapters(a.name):
                        bad.append(f"{name}:{n.lineno}: import {a.name}")
            elif isinstance(n, ast.ImportFrom) and not n.level:
                veracium_imports += (n.module or "").split(".")[0] == "veracium"
                if _names_adapters(n.module) or (n.module == "veracium" and any(a.name == "adapters" for a in n.names)):
                    bad.append(f"{name}:{n.lineno}: from {n.module} import {', '.join(a.name for a in n.names)}")
            elif (isinstance(n, ast.Attribute) and n.attr == "adapters" and isinstance(n.value, ast.Name)
                  and n.value.id == "veracium"):
                bad.append(f"{name}:{n.lineno}: veracium.adapters read as an attribute")
            elif isinstance(n, ast.Call):
                f = n.func
                fname = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None
                if fname in ("import_module", "__import__"):
                    for arg in n.args[:1]:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and _names_adapters(arg.value):
                            bad.append(f"{name}:{n.lineno}: {fname}({arg.value!r})")
    if paths and not veracium_imports:
        bad.append("ANCHOR: no `veracium` import found in any scanned module (checks.py imports veracium.mcp_server): "
                   "the scan read nothing it could have refused")
    return bad


def oracle_runtime_imports(extra=()) -> list[str]:
    """0053 §10 Q8 (research's L1), I10 at run time: import the oracle modules (and any `extra` file) alone, in a fresh
    interpreter, and name every veracium.adapters module left in sys.modules. The static scan reads import forms; this
    reads what was loaded, so a computed string, an alias read or a transitive import is caught too. Its anchor: the
    run must have loaded veracium.mcp_server, or it imported nothing it could have refused."""
    import subprocess
    import sys
    code = ("import importlib.util, sys\n"
            f"sys.path.insert(0, {os.path.dirname(HERE)!r})\n"
            "import " + ", ".join(f"adapter_conformance.{m[:-3]}" for m in ORACLE_MODULES) + "\n"
            "for i, f in enumerate(sys.argv[1:]):\n"
            "    spec = importlib.util.spec_from_file_location(f'planted_{i}', f)\n"
            "    spec.loader.exec_module(importlib.util.module_from_spec(spec))\n"
            "print('LOADED', ' '.join(sorted(m for m in sys.modules if m.split('.')[0] == 'veracium')))\n")
    r = subprocess.run([sys.executable, "-c", code, *extra], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        return [f"the import run failed (exit {r.returncode}): {r.stderr.strip()[-300:]}"]
    line = next((ln for ln in r.stdout.splitlines() if ln.startswith("LOADED")), None)
    if line is None:
        return ["the import run printed no LOADED line"]
    loaded = line.split()[1:]
    bad = [f"{m} is loaded by the oracle modules" for m in loaded if _names_adapters(m)]
    if "veracium.mcp_server" not in loaded:
        bad.append("ANCHOR: the oracle modules did not load veracium.mcp_server, so the run imported nothing it could "
                   "have refused")
    return bad


# --------------------------------------------------------------------------- the parameter census

#: a served parameter whose every non-default value is a REFUSAL (its closed set has one member), with the K6 case that
#: carries one: no compared case can pass it a valid non-default value
REFUSAL_ONLY = {("record_procedure", "relation"): "K6-procedure-relation-not-procedural"}
_ABSENT = object()


def parameter_census(o: Oracle) -> list[str]:
    """Research's stage 1, S1-1: every served parameter takes a non-default value in at least one compared case outside
    K6 whose reference does not refuse it (stage 2, N1), so a mutant that rewrites it has a case to be seen in (record_procedure's author had none, and a mutant
    forwarding it as "user" passed every family). A refusal-only parameter needs its K6 case instead."""
    bad = []
    for t in o.listing:
        for p, schema in t["parameters"].get("properties", {}).items():
            default = schema.get("default", _ABSENT)
            hits = [c["id"] for c in o.doc["cases"] if c["tool"] == t["name"] and p in c["args"]
                    and (default is _ABSENT or c["args"][p] != default)]
            key = (t["name"], p)
            if key in REFUSAL_ONLY:
                case = REFUSAL_ONLY[key]
                if key == ("record_procedure", "relation") and _procedural_relations() != {default}:
                    bad.append(f"record_procedure.relation is refusal-only only while the procedural relations are its "
                               f"default alone; they are {sorted(_procedural_relations())}")
                if case not in hits or o.refs[case].case["family"] != "K6" or not _refused(o.refs[case].outcome):
                    bad.append(f"{t['name']}.{p}: declared refusal-only, and {case} does not carry its refusal")
            elif not [h for h in hits if o.refs[h].case["family"] != "K6" and not _refused(o.refs[h].outcome)]:
                # research's stage 2, N1: a case whose reference REFUSES carries the value nowhere a rewrite could be
                # seen (record_procedure's derived_from under `none` is attempted_elevation), so it does not count
                bad.append(f"{t['name']}.{p}: no compared case outside K6 passes it a non-default value that the "
                           f"reference does not refuse")
    for key in REFUSAL_ONLY:
        if key[0] not in {t["name"] for t in o.listing}:
            bad.append(f"REFUSAL_ONLY names {key}, which is not served")
    return bad


def _procedural_relations() -> set:
    from veracium.schema import DEFAULT_RELATIONS
    return {name for name, r in DEFAULT_RELATIONS.items() if r.relation_kind == "procedural"}


def _refused(outcome) -> bool:
    return outcome[0] == "error" or (isinstance(outcome[1], dict) and outcome[1].get("ok") is False)


# --------------------------------------------------------------------------- measured lists (§3a)

def measured_lists(o: Oracle, declared=None) -> list[str]:
    """For every write case, the reference twice in two fresh stores. The leaves that vary must equal the declared
    lists of the case's group, both ways; the two runs give equal canonical forms and no clock reversal (the
    canonicaliser's green control); a declared id never parses as a timestamp."""
    declared = DECLARED if declared is None else declared
    bad, seen = [], {}
    for c in o.doc["cases"]:
        g = c.get("clock_group")
        if g is None:
            continue
        a, b = o.run(c, "twinA"), o.run(c, "twinB")
        seen.setdefault(g, set()).update(K.varying(a.store, b.store))
        ids, clocks = declared[g]
        diff = K.Canon(ids, clocks).differences(a.store, b.store)
        if diff:
            bad.append(f"{c['id']}: the two reference runs differ under the canonical form: {diff[:2]}")
    for g, (ids, clocks) in declared.items():
        got = seen.get(g, set())
        for p in sorted(got - ids - clocks):
            bad.append(f"group {g}: {p} varies between the reference runs and is not declared")
        for p in sorted((ids | clocks) - got):
            bad.append(f"group {g}: {p} is declared and never varies (a dropped field there would go unseen)")
    for c in o.doc["cases"]:
        if c.get("clock_group") is None:
            continue
        ids = declared[c["clock_group"]][0]
        for t, n, col, path, v in K.leaves(o.refs[c["id"]].store):
            if K.pattern(t, col, path) in ids and isinstance(v, str) and _is_timestamp(v):
                bad.append(f"{c['id']}: declared id {K.pattern(t, col, path)} holds a timestamp {v!r}: a clock "
                           f"renamed as an id loses its order")
    return list(dict.fromkeys(bad))


def _is_timestamp(v: str) -> bool:
    try:
        K._clock(v, "")
    except AssertionError:
        return False
    return True


# --------------------------------------------------------------------------- the families

def _canon_value(v, idmap):
    if isinstance(v, dict):
        return {k: _canon_value(x, idmap) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return type(v)(_canon_value(x, idmap) for x in v)
    return idmap.get(v, v) if K._scalar(v) else v


def _idmap(canon: K.Canon, store: str) -> dict:
    ls = K.leaves(store)
    m = {}
    for t, n, c, path, v in ls:
        if K.pattern(t, c, path) in canon.ids and K._scalar(v):
            m.setdefault(v, f"<id:{len(m)}>")
    return m


def _same_schema(served: dict, got: dict) -> list[str]:
    out = []
    sp, gp = served.get("properties", {}), (got or {}).get("properties", {})
    for extra in sorted(set(gp) - set(sp)):
        out.append(f"parameter {extra!r} is offered and the served schema has no such parameter")
    for missing in sorted(set(sp) - set(gp)):
        out.append(f"parameter {missing!r} is served and not offered")
    if sorted(served.get("required", [])) != sorted((got or {}).get("required", [])):
        out.append(f"required {served.get('required', [])} != {(got or {}).get('required', [])}")
    for k in sorted(set(sp) & set(gp)):
        strip = lambda d: {a: b for a, b in d.items() if a != "title"}
        if strip(sp[k]) != strip(gp[k]):
            out.append(f"parameter {k!r}: {gp[k]} != served {sp[k]}")
    return out


def run_families(o: Oracle, factory, tag="drv") -> dict:
    res = {f: [] for f in FAMILIES}
    # K1/K2: the surface, over one store with the default binding
    path = o.fresh(f"{tag}-surface")
    mem = F.open_memory(path)
    try:
        drv = factory(mem, binding(o.doc, "none"))
        offered = drv.tools()
        converted = drv.converted()
    finally:
        mem.close()
    served = {t["name"]: t for t in o.listing}
    for view, tools in (("offered", offered), ("converted", converted)):
        if tools is None:
            continue
        names = [t["name"] for t in tools]
        if sorted(names) != sorted(served) or len(set(names)) != len(names):
            res["K1"].append(f"{view}: tools {names} != served {sorted(served)}")
        for t in tools:
            s = served.get(t["name"])
            if s is None:
                continue
            exact = view == "offered"
            if exact and t["parameters"] != s["parameters"]:
                res["K1"].append(f"{view} {t['name']}: the schema is not the served schema byte for byte: "
                                 + "; ".join(_same_schema(s["parameters"], t["parameters"]) or ["(same keys)"]))
            elif not exact:
                res["K1"].extend(f"{view} {t['name']}: {m}" for m in _same_schema(s["parameters"], t["parameters"]))
            if t["description"] != s["description"]:
                cap = len(t["description"])
                if s["description"].startswith(t["description"]):
                    res["K2"].append(f"{view} {t['name']}: the description is capped at {cap} of "
                                     f"{len(s['description'])} characters (provider path: {view}; source: measured "
                                     f"through the framework's offline conversion)")
                else:
                    res["K2"].append(f"{view} {t['name']}: the description is not the served description")
    # K3-K8: the values, one fresh store per case
    for c in o.doc["cases"]:
        ref = o.refs[c["id"]]
        path = o.fresh(f"{tag}-{c['id']}")
        mem = F.open_memory(path)
        try:
            drv = factory(mem, binding(o.doc, c["binding"]))
            try:
                got = drv.decode(drv.call(c["tool"], c["args"]))
            except Exception as exc:                 # a framework exception is a K6 defect wherever it happens
                got = ("exception", f"{type(exc).__name__}: {exc}")
        finally:
            mem.close()
        fam = c["family"]
        if got[0] == "exception":
            res["K6"].append(f"{c['id']}: the call raised through the framework ({got[1][:160]})")
            continue
        if fam == "K8" and c.get("clock_group"):
            # a K8 case that WRITES (remember, maintain: it carries a clock group) compares the property K8 names: the
            # other users' records are untouched, and the bound user gained the reference's rows. The content is K5's
            res["K8"].extend(f"{c['id']}: {m}" for m in
                             _identity_writes(ref.store, path, binding(o.doc, c["binding"])["user_id"]))
            continue
        g = c.get("clock_group", "dated")
        canon = K.Canon(*DECLARED[g])
        if fam in ("K5", "K7"):
            exp_v = _canon_value(ref.outcome, _idmap(canon, ref.store))
            got_v = _canon_value(got, _idmap(canon, path))
        else:
            exp_v, got_v = ref.outcome, got
        if got_v != exp_v:
            res[fam].append(f"{c['id']}: {_short(got_v)} != reference {_short(exp_v)}")
        diff = canon.differences(ref.store, path)
        if diff:
            res[fam].append(f"{c['id']}: the store differs from the reference store: {diff[:2]}")
    return res


def _owned_rows(store: str):
    """{owner: [row leaves]}, a row's owner its `user_id` column or JSON leaf (None when it has neither)."""
    rows: dict = {}
    for t, n, c, path, v in K.leaves(store):
        rows.setdefault((t, n), []).append((c, path, v))
    out: dict = {}
    for (t, n), cells in rows.items():
        owners = {v for c, path, v in cells if (c == "user_id" and path == ()) or path == ("$", "user_id")}
        owner = owners.pop() if len(owners) == 1 else (None if not owners else "<several>")
        out.setdefault(owner, []).append((t, cells))
    return out


def _identity_writes(ref_store: str, store: str, user: str) -> list[str]:
    a, b = _owned_rows(ref_store), _owned_rows(store)
    bad = []
    for owner in sorted(set(a) | set(b), key=str):
        if owner in (user, None):
            if len(a.get(owner, [])) != len(b.get(owner, [])):
                bad.append(f"{owner!r} holds {len(b.get(owner, []))} rows, the reference {len(a.get(owner, []))}")
        elif a.get(owner) != b.get(owner):
            bad.append(f"another user's records ({owner!r}) differ from the reference: a write crossed users")
    return bad


def _short(v) -> str:
    return repr(v)[:220]


def check_decoder(o: Oracle, driver_cls) -> list[str]:
    """§3: the declared decoder is total and lossless over every reference value of the run."""
    bad = []
    for k, ref in o.refs.items():
        try:
            back = driver_cls.decode(None, driver_cls.encode(ref.outcome))
        except Exception as exc:
            bad.append(f"{k}: the decoder raised on a reference value ({type(exc).__name__}: {exc})")
            continue
        if back != ref.outcome:
            bad.append(f"{k}: the decoder is lossy: {_short(ref.outcome)} -> {_short(back)}")
    return bad
