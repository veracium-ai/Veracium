"""Dev's write census for the 0031 §4f trust TOOLS at the implementation pin: every SQL write each of the seven tools
executes, through its `*_report` (the path the MCP server and both adapters call, call_path and erasure as the server
passes them), on its accepted, REFUSED and CONDITIONAL branches. Each case runs on a fresh store and is traced on
SqliteStore's one connection (set_trace_callback, during the call only). Prints, per case: the outcome (`ok`, the
refusal code, or the exception class) and the (op, table) writes with their counts.

The census at the design pin (dev-census-78a20f4a.txt, census-branches-78a20f4a.txt) traced the HOST VERBS before any
tool existed; it is kept as the record round 2 read. This one traces the tools themselves.

Run from the repo root: PYTHONPATH=src .venv/bin/python specs/evidence/0031-trust-tools/census/write_census_tools.py"""
import collections
import json
import os
import re
import tempfile
from datetime import datetime, timezone

from veracium import EvidenceContext, Memory, MemoryConfig, graph
from veracium import mcp_server as M
from veracium.schema import ConfirmationCallPath, Edge, EvidenceAuthor, Provenance
from veracium.scope import Identity
from veracium.trust_tools import PreviewTokenIssuer

WRITE = re.compile(r"^\s*(INSERT|UPDATE|DELETE|REPLACE)\b(?:\s+OR\s+\w+)?\s+(?:INTO\s+|FROM\s+)?[\"`]?(\w+)", re.I)
U = "u"
A = Identity(None, "src-a")
T0 = datetime(2026, 11, 14, 12, tzinfo=timezone.utc)
MCP = ConfirmationCallPath.MCP_DIRECT


class Stub:
    def __call__(self, prompt, *, role="compile", **kw):
        if role == "distill":
            return json.dumps({"triples": [{"subject": "user", "relation": "located_at", "object": "Berlin",
                                            "volatility": "durable"}], "episode": "The user said Berlin.",
                               "instructions": []})
        return "summary"


def fresh(*, seed=True, scoped=False, default_wiki=False):
    d = tempfile.mkdtemp()
    kw = dict(db_path=os.path.join(d, "v.db"), require_source_id=False)
    if not default_wiki:
        kw["wiki_recompile_after_writes"] = 0
    if scoped:
        kw["scope_groups"] = {"team-a": [A]}
    m = Memory(llm=Stub(), config=MemoryConfig(**kw))
    if seed:
        m.remember(U, "I live in Berlin.", date="2026-11-12", context=EvidenceContext.direct(), source_id="src-a")
    return m


def edge_id(m):
    return next(e.id for e in m.store.edges(U) if e.relation == "located_at")


def episode_id(m):
    return next(e.id for e in m.store.episodes(U))


def other_subject(m):
    m.store.add_edge(Edge(id="e-alice", user_id=U, subject="person:alice", relation="located_at", object="Tokyo",
                          valid_from=T0, provenance=Provenance(author_of_evidence=EvidenceAuthor.USER,
                                                               source_id="src-a", evidence_ref="ev-alice",
                                                               observed_at=T0)))
    return "e-alice"


def traced(m, fn):
    sql = []
    m.store._conn.set_trace_callback(sql.append)
    try:
        try:
            out = fn()
            outcome = "ok" if out.get("ok") is True else f"refused:{out.get('refusal')}"
        except Exception as exc:                                # an internal failure is raised, never a refusal
            outcome = f"raised:{type(exc).__name__}"
    finally:
        m.store._conn.set_trace_callback(None)
    writes = collections.Counter()
    for s in sql:
        w = WRITE.match(s)
        if w:
            writes[(w.group(1).upper(), w.group(2))] += 1
    return outcome, writes


def issuer(m):
    return PreviewTokenIssuer(m.store.local_origin(), U, clock=lambda: int(T0.timestamp()))


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


# ---- gate 1: the capability, every tool under `none` --------------------------------------------------------------
for tool in ("find_facts", "correct_fact", "dispute_fact", "confirm_fact", "forget_fact",
             "forget_everything_preview", "forget_everything_confirm"):
    def _none(tool=tool):
        m = fresh()
        calls = {
            "find_facts": lambda: M.find_facts_report(m, U, "Berlin", capability="none"),
            "correct_fact": lambda: M.correct_fact_report(m, U, edge_id(m), "Paris", capability="none", call_path=MCP),
            "dispute_fact": lambda: M.dispute_fact_report(m, U, edge_id(m), "no", capability="none", call_path=MCP),
            "confirm_fact": lambda: M.confirm_fact_report(m, U, edge_id(m), capability="none", call_path=MCP),
            "forget_fact": lambda: M.forget_fact_report(m, U, edge_id(m), capability="none"),
            "forget_everything_preview": lambda: M.forget_everything_preview_report(m, U, capability="none",
                                                                                   issuer=issuer(m)),
            "forget_everything_confirm": lambda: M.forget_everything_confirm_report(m, U, "tt1.x.y", capability="none",
                                                                                   issuer=issuer(m)),
        }
        return traced(m, calls[tool])
    case(f"{tool} / gate 1 capability none")(_none)

# ---- gate 2: the erasure switch, the three forget tools ------------------------------------------------------------
for tool in ("forget_fact", "forget_everything_preview", "forget_everything_confirm"):
    def _off(tool=tool):
        m = fresh()
        calls = {
            "forget_fact": lambda: M.forget_fact_report(m, U, edge_id(m), capability="direct", erasure="off"),
            "forget_everything_preview": lambda: M.forget_everything_preview_report(m, U, capability="direct",
                                                                                   erasure="off", issuer=issuer(m)),
            "forget_everything_confirm": lambda: M.forget_everything_confirm_report(m, U, "tt1.x.y", capability="direct",
                                                                                   erasure="off", issuer=issuer(m)),
        }
        return traced(m, calls[tool])
    case(f"{tool} / gate 2 erasure off")(_off)

# ---- gate 3: a principal on the whole-user erase --------------------------------------------------------------------
case("forget_everything_preview / gate 3 principal")(lambda: (lambda m: traced(m, lambda: M.forget_everything_preview_report(
    m, U, capability="direct", principal=A, issuer=issuer(m))))(fresh(scoped=True)))
case("forget_everything_confirm / gate 3 principal")(lambda: (lambda m: traced(m, lambda: M.forget_everything_confirm_report(
    m, U, "tt1.x.y", capability="direct", principal=A, issuer=issuer(m))))(fresh(scoped=True)))

# ---- gate 4: input validation ---------------------------------------------------------------------------------------
case("forget_fact / gate 4 both ids")(lambda: (lambda m: traced(m, lambda: M.forget_fact_report(
    m, U, edge_id(m), episode_id(m), capability="direct")))(fresh()))
case("dispute_fact / gate 4 reason over 1024 code points")(lambda: (lambda m: traced(m, lambda: M.dispute_fact_report(
    m, U, edge_id(m), "é" * 1025, capability="direct", call_path=MCP)))(fresh()))
case("forget_everything_confirm / gate 4 malformed token")(lambda: (lambda m: traced(m, lambda: M.forget_everything_confirm_report(
    m, U, "tt1.x.y", capability="direct", issuer=issuer(m))))(fresh()))

# ---- gate 5: scope configuration under a principal ------------------------------------------------------------------
case("correct_fact / gate 5 scope unconfigured")(lambda: (lambda m: traced(m, lambda: M.correct_fact_report(
    m, U, edge_id(m), "Paris", capability="direct", principal=A, call_path=MCP)))(fresh()))
case("find_facts / gate 5 principal ungroupable")(lambda: (lambda m: traced(m, lambda: M.find_facts_report(
    m, U, "Berlin", capability="direct", principal=Identity(None, None))))(fresh(scoped=True)))

# ---- gate 7: not found in scope -------------------------------------------------------------------------------------
for tool in ("correct_fact", "dispute_fact", "confirm_fact", "forget_fact"):
    def _missing(tool=tool):
        m = fresh()
        calls = {
            "correct_fact": lambda: M.correct_fact_report(m, U, "e-none", "Paris", capability="direct", call_path=MCP),
            "dispute_fact": lambda: M.dispute_fact_report(m, U, "e-none", "no", capability="direct", call_path=MCP),
            "confirm_fact": lambda: M.confirm_fact_report(m, U, "e-none", capability="direct", call_path=MCP),
            "forget_fact": lambda: M.forget_fact_report(m, U, "e-none", capability="direct"),
        }
        return traced(m, calls[tool])
    case(f"{tool} / gate 7 unknown id, no principal")(_missing)

# ---- accepted and conditional branches ------------------------------------------------------------------------------
case("find_facts / accepted, user with facts, recompilation 0")(lambda: (lambda m: traced(m, lambda: M.find_facts_report(
    m, U, "Berlin", capability="direct")))(fresh()))


def _find_empty():
    m = fresh(seed=False, default_wiki=True)
    first = traced(m, lambda: M.find_facts_report(m, U, "empty", capability="direct"))
    second = traced(m, lambda: M.find_facts_report(m, U, "empty", capability="direct"))
    return first, second


case("find_facts / CONDITIONAL empty user, default config: first lookup | second lookup")(_find_empty)
case("find_facts / CONDITIONAL user with facts, default config (recompilation on)")(lambda: (lambda m: traced(
    m, lambda: M.find_facts_report(m, U, "Berlin", capability="direct")))(fresh(default_wiki=True)))
case("find_facts / CONDITIONAL no query (the proactive path), default config")(lambda: (lambda m: traced(
    m, lambda: M.find_facts_report(m, U, None, capability="direct")))(fresh(default_wiki=True)))
case("correct_fact / accepted")(lambda: (lambda m: traced(m, lambda: M.correct_fact_report(
    m, U, edge_id(m), "Paris", capability="direct", call_path=MCP)))(fresh()))
case("correct_fact / CONDITIONAL other-subject target: correction_refused, committed bookkeeping")(
    lambda: (lambda m: traced(m, lambda: M.correct_fact_report(m, U, other_subject(m), "Osaka", capability="direct",
                                                               call_path=MCP)))(fresh()))
case("dispute_fact / accepted")(lambda: (lambda m: traced(m, lambda: M.dispute_fact_report(
    m, U, edge_id(m), "that's wrong", capability="direct", call_path=MCP)))(fresh()))
case("confirm_fact / accepted")(lambda: (lambda m: traced(m, lambda: M.confirm_fact_report(
    m, U, edge_id(m), capability="direct", call_path=MCP)))(fresh()))
case("forget_fact / accepted (edge)")(lambda: (lambda m: traced(m, lambda: M.forget_fact_report(
    m, U, edge_id(m), capability="direct")))(fresh()))
case("forget_fact / accepted (episode)")(lambda: (lambda m: traced(m, lambda: M.forget_fact_report(
    m, U, episode_id=episode_id(m), capability="direct")))(fresh()))
case("forget_everything_preview / accepted")(lambda: (lambda m: traced(m, lambda: M.forget_everything_preview_report(
    m, U, capability="direct", issuer=issuer(m))))(fresh()))


def _confirm(changed):
    m = fresh()
    iss = issuer(m)
    tok = M.forget_everything_preview_report(m, U, capability="direct", issuer=iss)["preview_token"]
    if changed:
        m.remember(U, "I also like tea.", date="2026-11-13", context=EvidenceContext.direct(), source_id="src-a")
    return traced(m, lambda: M.forget_everything_confirm_report(m, U, tok, capability="direct", issuer=iss))


case("forget_everything_confirm / accepted")(lambda: _confirm(False))
case("forget_everything_confirm / CONDITIONAL store changed since the preview")(lambda: _confirm(True))


def fmt(outcome, writes):
    w = ", ".join(f"{op} {t} x{n}" for (op, t), n in sorted(writes.items())) or "no writes"
    return f"{outcome:32s} {w}"


if __name__ == "__main__":
    print(f"write census of the seven trust tools through *_report; {len(CASES)} cases, each on a fresh store")
    for name, fn in CASES:
        r = fn()
        if isinstance(r[0], tuple):
            print(f"{name}\n    first:  {fmt(*r[0])}\n    second: {fmt(*r[1])}")
        else:
            print(f"{name}\n    {fmt(*r)}")
