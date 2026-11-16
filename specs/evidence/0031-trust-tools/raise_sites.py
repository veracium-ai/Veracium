#!/usr/bin/env python3
"""specs/0031 §4f, TT-R3-03's stated bound (v23.3, §4f.5 4a step 8): the refusal-class raise sites the trust tools'
library calls REACH, each classified by hand as an intended REFUSAL or an internal INVARIANT. Evidence, not a gate: the
phase rule needs no classification (a refusal is decided by whether anything committed in the call), and this table
lets an origin rule be added later without measuring again.

Two steps, both recorded in the output's header:
  1. REACH, measured: the 0031 cell files run under a sys.monitoring plugin that records every src/veracium function
     entered INSIDE `mcp_server._trust_call` (the corpus bound: the functions those tests reach, no others).
  2. SITES, by AST: every `raise` in a reached function whose exception is a refusal class (`ValueError`, `TypeError`,
     `ScopeError`, `TrustRefused`), written directly or through a decision site (`raise SITE.fire(ValueError(...))`).

    python raise_sites.py --measure > raise-sites.tsv      # needs the mcp extra; runs pytest once

Every site's classification is keyed by (file, function, decision site), or by the first string constant of the
exception for a raise with no decision site; a site with no key prints UNCLASSIFIED and the run exits 1.
"""
from __future__ import annotations

import ast
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "src" / "veracium"
CELL_FILES = ("tests/test_0031_trust_tools_library.py", "tests/test_0031_render_receipt.py",
              "tests/test_0031_trust_tools_erase.py", "tests/test_0031_trust_tools_mcp.py",
              "tests/test_0031_trust_tools_surfaces.py")
CLASSES = {"ValueError", "TypeError", "ScopeError", "TrustRefused"}

PLUGIN = '''
import os, sys
def pytest_configure(config):
    from veracium import mcp_server as M
    orig, inside, seen = M._trust_call, [0], set()
    mon = sys.monitoring; TOOL = 4
    mon.use_tool_id(TOOL, "tt-reach")
    def on_start(code, off):
        if "/src/veracium/" not in code.co_filename:
            return mon.DISABLE
        if inside[0]:
            seen.add((code.co_filename.split("/src/veracium/")[-1], code.co_qualname))
    mon.register_callback(TOOL, mon.events.PY_START, on_start)
    mon.set_events(TOOL, mon.events.PY_START)
    def wrapped(mem, fn):
        inside[0] += 1
        try:
            return orig(mem, fn)
        finally:
            inside[0] -= 1
    M._trust_call = wrapped
    def dump():
        with open(os.environ["REACH_OUT"], "w") as fh:
            for f, q in sorted(seen):
                fh.write(f"{f}\\t{q}\\n")
    config.add_cleanup(dump)
'''

R, I = "refusal", "invariant"
# (file, function qualname, decision site) -> (class, why); a raise with no decision site is keyed by its first string
# constant, or by "*" for every such raise in the function. REFUSAL: the answer to the caller's input or to the target
# record's state, raised before the verb writes. INVARIANT: a value the verb or the host built itself is wrong.
_HOST = "a parameter the trust tools never supply; reached only through a host call or a fixture"
_STORE = "a write the verb constructed itself breaks a store invariant (its own pre-checks refuse first)"
_SCOPE = "the scope boundary's refusal (§4a step 8 names ScopeError)"
CLASSIFICATION: dict = {
    ("__init__.py", "Memory._trust_scope_gate", "_SITE_TRUST_SCOPE_GATE"): (R, "§4a gates 5-7, before any write"),
    ("__init__.py", "Memory.forget_everything_preview", "_SITE_TRUST_ERASE_PREVIEW"): (R, "gate 3, before any write"),
    ("__init__.py", "Memory.forget_everything_preview", "_SITE_TRUST_ERASE_PREVIEW_CONTEXT"):
        (R, "an issuer for another store or user, before any write"),
    ("__init__.py", "Memory.forget_everything_confirm", "_SITE_TRUST_ERASE_CONFIRM"): (R, "gate 3, before any write"),
    ("__init__.py", "Memory._find_edge", "_SITE_EDGE_UNKNOWN_TARGET"):
        (R, "an unknown target, before dispute's and correct's writes; reached AFTER confirm's commit by its readback "
            "(round 3's interleaving), where the phase rule makes it an internal failure"),
    ("__init__.py", "Memory.confirm", "_SITE_CONFIRM_UNKNOWN_TARGET"): (R, "an unknown target, before any write"),
    ("__init__.py", "Memory.correct", "_SITE_CORRECT_INACTIVE"): (R, "an inactive target, before any write"),
    ("__init__.py", "Memory.dispute", "_SITE_DISPUTE_INACTIVE"): (R, "an inactive target, before any write"),
    ("__init__.py", "Memory._refuse_attested", "_SITE_FEEDBACK_ATTESTED"): (R, "a redacted target, before any write"),
    ("__init__.py", "Memory.recall", "*"): (I, _HOST),
    ("__init__.py", "Memory.recall", "_SITE_ASOF_ON_PROACTIVE"): (I, _HOST),
    ("__init__.py", "Memory.recall", "_SITE_RECALL_RECEIPT_AS_OF"): (I, _HOST),
    ("__init__.py", "Memory._recall", "*"): (I, _HOST),
    ("__init__.py", "Memory._recall", "_SITE_POLICY_WITH_ASOF"): (I, _HOST),
    ("adapters/_surface.py", "Binding.__init__", "*"): (I, "the host's binding construction"),
    ("adapters/_surface.py", "Binding.call", "*"): (R, "the caller named a tool the binding does not serve"),
    ("budgets.py", "validate_budget", "*"): (I, _HOST),
    ("budgets.py", "validate_surface_params", "*"): (I, "the deployment's configuration"),
    ("proactive.py", "assemble", "*"): (I, "the deployment's configuration"),
    ("graph.py", "plan_correction", "_SITE_CORRECTION_IDENTITY"): (R, "the corrected value, before any write"),
    ("graph.py", "plan_correction", "_SITE_CORRECTION_PRIOR_INACTIVE"): (R, "an inactive target, before any write"),
    ("ingest.py", "_event_dt", "*"): (I, _HOST),
    ("schema.py", "Edge._grounding_axis_is_well_formed", "*"): (I, _STORE),
    ("schema.py", "Provenance._producer_only_on_procedural", "*"): (I, _STORE),
    ("schema.py", "as_utc_required", "*"): (I, _STORE),
    ("scope.py", "Identity.__post_init__", "*"): (R, _SCOPE + ": a malformed principal"),
    ("scope.py", "classify", "_SITE_CLASSIFY_NO_POLICY"): (R, _SCOPE),
    ("scope.py", "classify", "_SITE_CLASSIFY_UNGROUPABLE"): (R, _SCOPE),
    ("scope.py", "classify", "_SITE_CLASSIFY_EVIDENCE"): (I, "a stored membership value outside its closed form"),
    ("scope.py", "_revalidate", "_SITE_REVALIDATE"): (I, "the policy object diverges from the validated one"),
    ("scope.py", "membership", "_SITE_MEMBERSHIP_ABANDONED"): (I, "a ledger state outside its closed set"),
    ("scope.py", "membership", "_SITE_MEMBERSHIP_UNKNOWN_STATE"): (I, "a ledger state outside its closed set"),
    ("scope.py", "resolve", "*"): (I, "the store's own identity"),
    ("scope.py", "validate_filters", "_SITE_FILTERS_BAD_VALUE"): (R, _SCOPE + ": a filter the caller supplied"),
    ("scope.py", "validate_filters", "_SITE_FILTERS_NOT_MAPPING"): (R, _SCOPE + ": a filter the caller supplied"),
    ("scope.py", "validate_filters", "_SITE_FILTERS_UNKNOWN_FIELD"): (R, _SCOPE + ": a filter the caller supplied"),
    ("scope_read.py", "ScopeView.__init__", "_SITE_VIEW_NO_POLICY"): (R, _SCOPE),
    ("scope_read.py", "ScopeView.__init__", "_SITE_VIEW_PRINCIPAL_NOT_IDENTITY"): (R, _SCOPE),
    ("scope_read.py", "ScopeView.__init__", "_SITE_VIEW_UNGROUPABLE"): (R, _SCOPE),
    ("source_identity.py", "source_identity_digest", "*"): (I, "an origin the store resolves itself"),
    ("store/sqlite.py", "SqliteStore._confirm_replay", "_SITE_CONFIRM_REQUEST_DIGEST"):
        (R, "a repeated request identity with different content (INV-TT18's source conflict), before any write"),
    ("store/sqlite.py", "SqliteStore._confirm_replay", "_SITE_REGISTRY_RESULT_MISSING"): (I, "the request registry"),
    ("store/sqlite.py", "SqliteStore._registry_held", "_SITE_REGISTRY_VERB_HELD"):
        (R, "a host-supplied correlation id held by another verb; a tool supplies none"),
    ("store/sqlite.py", "SqliteStore.confirm_edge", "_SITE_CONFIRM_NOT_ASSERTABLE"): (R, "the target's state"),
    ("store/sqlite.py", "SqliteStore.confirm_edge", "_SITE_CONFIRM_ACTIVE_CHALLENGE"): (R, "the target's state"),
    ("store/sqlite.py", "SqliteStore.confirm_edge", "_SITE_CONFIRM_SOURCE_REDACTED"): (R, "the target's state"),
    ("store/sqlite.py", "SqliteStore.confirm_edge", "_SITE_CONFIRM_CORRELATION"):
        (R, "a host-supplied correlation id conflict; a tool supplies none"),
    ("store/sqlite.py", "SqliteStore.forget_user", "_SITE_TRUST_STORE_CHANGED"):
        (R, "the token's key sets no longer match; the erase transaction writes nothing"),
    ("store/sqlite.py", "SqliteStore.redact", "_SITE_REDACT_BOTH_OR_NEITHER"): (R, "gate 4's input, before any write"),
    ("store/sqlite.py", "SqliteStore.redact", "_SITE_REDACT_REASON"): (R, "the reason, before any write"),
    ("store/sqlite.py", "SqliteStore.redact", "_SITE_REDACT_TARGET"): (R, "an unknown target, before any write"),
    ("store/sqlite.py", "SqliteStore._redact_in_txn", "_SITE_REDACT_CLAIMED"): (R, "the target's state (0041)"),
    ("store/sqlite.py", "SqliteStore._redact_in_txn", "_SITE_REDACT_DISPOSITION"): (R, "the target's state (0041)"),
    ("store/sqlite.py", "SqliteStore._redact_in_txn", "_SITE_REDACT_NOTHING"): (R, "the target's state (0041)"),
    ("store/sqlite.py", "SqliteStore._refuse_redacted_reason", "_SITE_REDACTED_REASON"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore._journal_edge_write", "*"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore._journal_edge_write", "_SITE_JOURNAL_REASON"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore._journal_edge_write", "_SITE_JOURNAL_REDACTION_REASON"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore._journal_edge_write", "_SITE_JOURNAL_REINSTATEMENT_REASON"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore._write_edge_row", "*"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore.validate_receipt_state", "*"): (I, _STORE),
    ("store/sqlite.py", "SqliteStore.apply_supersession_plan", "_SITE_SUPERSESSION_PLAN"): (I, _STORE),
    ("trust_tools.py", "PreviewTokenIssuer.__init__", "*"): (I, "the host's issuer construction"),
    ("trust_tools.py", "PreviewTokenIssuer.now", "*"): (I, "the host's issuer clock"),
    ("trust_tools.py", "PreviewTokenIssuer.verify", "_SITE_TOKEN_VERIFY"): (R, "the caller's token, before any write"),
    ("trust_tools.py", "parse_token", "_SITE_TOKEN_PARSE"): (R, "the caller's token, before any write"),
    ("trust_tools.py", "parse_token", "*"): (R, "the caller's token, before any write (mapped to preview_unknown)"),
    ("trust_tools.py", "_b64url_strict", "*"): (R, "the caller's token, before any write (mapped to preview_unknown)"),
    ("trust_tools.py", "_no_dup_object", "*"): (R, "the caller's token, before any write (mapped to preview_unknown)"),
    ("trust_tools.py", "TrustRefused.__init__", "*"): (I, "a refusal reason outside the closed set"),
}
for _site in ("_SITE_UPSERT_ATTESTED", "_SITE_UPSERT_IMMUTABLE", "_SITE_UPSERT_INVALIDATION_REASON", "_SITE_UPSERT_MARKER",
              "_SITE_UPSERT_RELATION_ONLY_QUARANTINE"):
    CLASSIFICATION[("store/sqlite.py", "SqliteStore._upsert_edge_row", _site)] = (I, _STORE)
for _site in ("_SITE_ADD_EPISODE", "_SITE_ADD_EPISODE_OWNER", "_SITE_EPISODE_ATTESTED", "_SITE_EPISODE_KIND",
              "_SITE_EPISODE_MARKER", "_SITE_EPISODE_RETIRED_REASON"):
    CLASSIFICATION[("store/sqlite.py", "SqliteStore.add_episode", _site)] = (I, _STORE)


def classify(rel, q, site, text):
    if site != "-":
        return CLASSIFICATION.get((rel, q, site), ("UNCLASSIFIED", ""))
    return CLASSIFICATION.get((rel, q, text), CLASSIFICATION.get((rel, q, "*"), ("UNCLASSIFIED", "")))


def reach() -> set:
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "tt_reach_plugin.py").write_text(PLUGIN)
        out = pathlib.Path(d) / "reach.tsv"
        env = {**os.environ, "REACH_OUT": str(out), "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": os.pathsep.join([d, str(ROOT / "src")])}
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
                            "-p", "tt_reach_plugin", *CELL_FILES], cwd=ROOT, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"the reach run failed:\n{r.stdout[-2000:]}")
        summary = r.stdout.strip().splitlines()[-1]
        return {tuple(ln.split("\t")) for ln in out.read_text().splitlines()}, summary


def _first_str(node) -> str:
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            return n.value[:48]
        if isinstance(n, ast.JoinedStr):
            return "".join(v.value for v in n.values if isinstance(v, ast.Constant))[:48]
    return ""


def _raised(exc):
    """(class, site) of a raise's exception, or None when it is not a refusal class constructed here."""
    if not isinstance(exc, ast.Call):
        return None
    f = exc.func
    if isinstance(f, ast.Attribute) and f.attr == "fire" and isinstance(f.value, ast.Name) and exc.args:
        inner = _raised(exc.args[0])
        return None if inner is None else (inner[0], f.value.id, inner[2])
    name = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
    return (name, "-", _first_str(exc)) if name in CLASSES else None


def sites(reached: set) -> list:
    rows = []
    for rel in sorted({f for f, _ in reached}):
        tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))

        def visit(node, prefix):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    q = f"{prefix}{child.name}"
                    if isinstance(child, ast.ClassDef):
                        visit(child, q + ".")
                        continue
                    if (rel, q) in reached:
                        for n in _own_nodes(child):
                            if isinstance(n, ast.Raise) and n.exc is not None:
                                got = _raised(n.exc)
                                if got:
                                    rows.append((rel, q, n.lineno, *got))
                    visit(child, q + ".<locals>.")
        visit(tree, "")
    return rows


def _own_nodes(fn):
    """The function's own nodes: nested defs and classes are their own functions (reached or not)."""
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        n = stack.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            stack.extend(ast.iter_child_nodes(n))


def main() -> int:
    reached, summary = reach()
    rows = sorted(sites(reached))
    print(f"# reach: {len(reached)} src/veracium functions entered inside mcp_server._trust_call while pytest ran "
          f"{' '.join(CELL_FILES)} ({summary}); sites: {len(rows)} refusal-class raises in those functions")
    print("# file\tfunction\tline\tclass\tdecision site\tfirst string\tclassification\twhy")
    counts = {R: 0, I: 0, "UNCLASSIFIED": 0}
    for rel, q, line, cls, site, text in rows:
        verdict, why = classify(rel, q, site, text)
        counts[verdict] += 1
        print(f"{rel}\t{q}\t{line}\t{cls}\t{site}\t{text!r}\t{verdict}\t{why}")
    print(f"# {counts[R]} refusal, {counts[I]} invariant, {counts['UNCLASSIFIED']} unclassified")
    return 1 if counts["UNCLASSIFIED"] else 0


if __name__ == "__main__":
    if "--measure" in sys.argv:
        sys.exit(main())
    print(__doc__)
    sys.exit(2)
