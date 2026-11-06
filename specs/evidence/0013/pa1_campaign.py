#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0013_pa1_campaign.py::test_pa1_table_check_refuses_each_tampered_table
"""0013-PA1 — the closure evidence of 0013 §4f (v33): every migration step's output is checked AT THE STEP.

Two parts, one table (mutation-table.json, the schema tests/test_closure_mutants.py reads: header "spec" and "cells"
keyed by finding, "digests"; `rows` are the code mutants, each with "finding", "outcome" and "good"; part A's cells
live under their own key, `perturbations`, which that rule does not read).

(A) THE PERTURBATION CELLS. Every write of the six checked steps, on every migration path, perturbed at its execution
    EXACTLY as the step-table instrument (steptable.py, 0007am §4c; its bytes digest-bound here) perturbs it: a data
    step's written value altered, its written row dropped, the statement skipped; the stamp lowered (n-1) or skipped,
    plus one mode this campaign adds beside steptable's, the stamp RAISED (n+1). A cell is KILLED only if ALL hold:
      (i)   the migration refuses with MigrationPostconditionError whose `.step` is EXACTLY that step's name;
      (ii)  POSITION: no write statement of a LATER step was issued before the refusal (the migration connection's
            write count is within the step's own range, and every recorded write is the unperturbed run's own, in
            order) — a check moved to the end would still name its step, so the name alone proves nothing (B3);
      (iii) the store file is unchanged: user_version, the manifest digest and a row digest equal the pre-migration
            values — a refusal that commits would still raise (B3).
    Anything else is recorded with its exact outcome and is NOT killed.

(B) THE CODE MUTANTS, through the shared classifier (specs/evidence/mutation_kinds.py) on the 0041 campaign's protocol:
    CLEAN on an unmutated copy of the tree (kill cells pass, honest cells pass, the module imports); per mutant, every
    edit's anchor occurs EXACTLY ONCE, the module still IMPORTS, its declared HONEST flows still pass, and the kill
    cells (tests/test_0013_pa1_campaign_cells.py, `test_cell_*`) run under pytest with each failing cell classified;
    KILLED iff a qualifying kind and no `other`, and the mutant's NAMED killing cell is among the failures. The file
    is restored byte-identically. CONTROLS: an unrelated TypeError injected into a postcondition must read
    UNCLASSIFIED. Honest flows are DECLARED per mutant: several M121 mutants' only observable is refusing a CORRECT
    legacy row (a false refusal is the defect), so each mutant names the legitimate flows it must not break.

`--check` is FAST and re-runs nothing (digests, definitions, anchors, recounts); `--write` runs both parts.
    $PY specs/evidence/0013/pa1_campaign.py --check
    TMPDIR=/dev/shm $PY specs/evidence/0013/pa1_campaign.py --write
"""
from __future__ import annotations

import ast
import collections
import shlex
import hashlib
import importlib.util
import json
import os
import pathlib
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TABLE = HERE / "mutation-table.json"          # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0013/pa1_campaign.py"
STEPTABLE = "specs/evidence/0013/steptable.py"
KINDS = "specs/evidence/mutation_kinds.py"
MIGRATION = "src/veracium/store/migration.py"
SCHEMA_VERSION_PY = "src/veracium/store/schema_version.py"
CELLS_FILE = "tests/test_0013_pa1_campaign_cells.py"
FINDING = "0013-PA1"


def _load_kinds():
    spec = importlib.util.spec_from_file_location("veracium_mutation_kinds", HERE.parent / "mutation_kinds.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


MK = _load_kinds()


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


# ---- the step-table instrument as a library ------------------------------------------------------------------------
# steptable.py is a script (its module body runs the campaign). Its LIBRARY definitions are taken by name from its own
# bytes (never re-typed), so the perturbations here are the instrument's own.
_LIB_NAMES = ("_kind", "_issuer", "Plan", "Proxy", "_short", "_TABLE_RE", "_create_name", "_alter_parts", "ddl_modes",
              "dml_modes", "_rewrite_ddl", "_perturb", "U1", "U2", "_edge_json", "LEGACY_OUTCOME", "POPULATION_NOTES",
              "_generic_row", "_populate", "build_fixture", "paths", "end_state", "_diff", "_Shim")
_LIB = None


def lib() -> dict:
    """steptable's library namespace, bound to the veracium this interpreter imports (asserted under this tree)."""
    global _LIB
    if _LIB is not None:
        return _LIB
    import re
    import traceback
    from datetime import datetime as _RealDT, timezone
    import veracium
    import veracium.store.migration as mig
    import veracium.store.schema_version as sv
    from veracium.schema import Edge, Provenance
    src = os.path.realpath(ROOT / "src")
    assert os.path.realpath(veracium.__file__).startswith(src + os.sep), (veracium.__file__, src)
    tree = ast.parse((ROOT / STEPTABLE).read_text(encoding="utf-8"))
    body, found = [], set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            names = {n.name}
        elif isinstance(n, ast.Assign):
            names = {t.id for t in n.targets if isinstance(t, ast.Name)} | {
                e.id for t in n.targets if isinstance(t, ast.Tuple) for e in t.elts if isinstance(e, ast.Name)}
        else:
            continue
        if names & set(_LIB_NAMES):
            body.append(n); found |= names & set(_LIB_NAMES)
    missing = set(_LIB_NAMES) - found
    assert not missing, f"steptable.py no longer defines {sorted(missing)}"
    ns = {"__name__": "steptable_lib", "os": os, "sys": sys, "re": re, "json": json, "sqlite3": sqlite3,
          "hashlib": hashlib, "traceback": traceback, "sv": sv, "mig": mig, "Edge": Edge, "Provenance": Provenance,
          "_RealDT": _RealDT, "timezone": timezone, "HEAD": sv.SCHEMA_VERSION, "TREE": str(ROOT),
          "SRC": os.path.join(str(ROOT), "src", "veracium") + os.sep}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(ROOT / STEPTABLE), "exec"), ns)
    real_perturb = ns["_perturb"]

    def _perturb(real, sql, params, plan, kind, rec, by):
        """steptable's perturbations, plus the two this campaign adds: the stamp RAISED (n+1), and `jsonset` (a cell's
        added key: an UPDATE's JSON param with the given keys set)."""
        if kind == "STAMP" and plan.mode == "higher":
            n = int(re.search(r"=\s*(\d+)", sql).group(1))
            plan.applied = f"stamp {n + 1}"
            return real.execute(f"PRAGMA user_version = {n + 1}")
        if kind == "DML" and plan.mode == "jsonset" and sql.lstrip().upper().startswith("UPDATE"):
            p = list(params); d = json.loads(p[0], object_pairs_hook=_strict_pairs); d.update(plan.payload); p[0] = json.dumps(d)
            plan.applied = f"UPDATE json set {sorted(plan.payload)}"
            return real.execute(sql, tuple(p))
        return real_perturb(real, sql, params, plan, kind, rec, by)

    ns["_perturb"] = _perturb
    _LIB = ns
    return ns


# ---- the six steps -------------------------------------------------------------------------------------------------
def _steps():
    import veracium.store.migration as mig
    return {mig.STEP_STAMP: lambda w: w["kind"] == "STAMP",
            mig.STEP_IDENTITY: lambda w: ":_mint_store_identity:" in w["by"],
            mig.STEP_EPOCH: lambda w: ":mint_store_epoch:" in w["by"],
            mig.STEP_BASELINE: lambda w: ":append_event:" in w["by"],
            mig.STEP_CHAINS: lambda w: ":_migrate_outcome_chains:" in w["by"],
            mig.STEP_WIKI: lambda w: ":_drop_wiki_cache:" in w["by"],
            # 0008 v7 §2a (v16; T3): the counter's mint and the registry backfill. Until 2026-10-14 neither was mapped,
            # so the first campaign over the v16 step perturbed NEITHER write — found by its own per-step count.
            mig.STEP_ACT_COUNTER: lambda w: ":mint_act_counter:" in w["by"],
            mig.STEP_REGISTRY: lambda w: (w["kind"] == "DML" and ":_data_registry:" in w["by"]
                                          and "INSERT INTO request_registry" in w["sql"]),
            # 0041 §11.6.6 (v16; T4): every redaction row's notice state, derived by the pre-v16 rule
            mig.STEP_NOTICE_STATE: lambda w: (w["kind"] == "DML" and ":_data_notice_state:" in w["by"]
                                              and "UPDATE redactions SET state" in w["sql"]),
            # 0044 §4f / 0018 amendment §4a (v16; T5): the arity era's mint and the two inventories
            mig.STEP_ARITY_ERA: lambda w: ":mint_arity_era:" in w["by"],
            mig.STEP_ARITY_INVENTORY: lambda w: (w["kind"] == "DML" and ":_data_arity_inventory:" in w["by"]
                                                 and "INSERT INTO arity_inventory" in w["sql"]),
            mig.STEP_REFUSAL_INVENTORY: lambda w: (w["kind"] == "DML" and ":_data_refusal_inventory:" in w["by"]
                                                   and "INSERT INTO refusal_inventory" in w["sql"])}


# A step with no DML of its own has no write for THIS campaign to perturb. Named here with its reason, never silently
# absent — every other STEP_* in the migration must appear in the cells. (Research's T3 stage 2 wording: v16-act-columns'
# block DOES write — the ALTER's DEFAULT puts 'local' into every legacy row — but its writes are the six ALTERs, DDL,
# byte-matched against the frozen literal (the step table's class (a) — 1,426 BYTE-MATCH kills at a2dc7b0 as RESEARCH
# measured them, research commit f8c7d01d, not re-derived here), and
# its postcondition is the row check.)
WRITELESS_STEPS = {"v16-act-columns": "its writes are the confirmations ALTERs (DDL, byte-matched, class (a)); its "
                                      "postcondition (B1) checks the legacy rows' v15 columns byte-equal and their act "
                                      "columns ('local', NULL x5) unsynthesized — tests/test_0008_request_registry.py "
                                      "injects its mutants as TEMP triggers",
                  "v16-arity-edges-unchanged": "a check, not a write: after each arity block it compares the edges table "
                                               "and the edge journal with the step's own pin (INV-I24) — "
                                               "tests/test_0044_t5_era.py injects its mutant (an edge rewritten by the "
                                               "step) as a TEMP trigger"}


def step_of(w):
    hits = [s for s, f in _steps().items() if f(w)]
    return hits[0] if hits else None


def _state(path) -> tuple:
    s = lib()["end_state"](path)
    return (s["user_version"], s["schema_sha"], s["data_sha"])


def run_case(path: str, plan=None) -> dict:
    """Migrate the store at `path` through steptable's recording proxy (and `plan`, if any). Returns the outcome, the
    recorded writes, the migration connection's issued-write count, and the store state before and after."""
    import veracium.store.migration as mig
    L = lib()
    pre = _state(path)
    rec, proxies = [], []

    class Shim(L["_Shim"]):
        def connect(self, *a, **kw):
            p = L["Proxy"](sqlite3.connect(*a, **kw), self.rec, self.plan)
            proxies.append(p)
            return p

    mig.sqlite3 = Shim(plan, rec)
    try:
        r = mig.migrate_store(path); exc = None
    except Exception as e:                                       # noqa: BLE001 — the outcome IS the measurement
        r, exc = None, e
    finally:
        mig.sqlite3 = sqlite3
    return {"result": r, "exc": exc, "writes": [w for w in rec if w["kind"] in ("DDL", "DML", "STAMP")],
            "issued": max((object.__getattribute__(p, "_w") for p in proxies), default=0), "pre": pre,
            "post": _state(path)}


def fresh_fixture(path: str, label: str) -> None:
    import veracium.store.release_migration as rm
    L = lib()
    for suffix in ("", "-journal", "-wal", rm._AUDIT_SUFFIX):
        try:
            os.remove(path + suffix)
        except FileNotFoundError:
            pass
    for lab, b, a, stamped in L["paths"]():
        if lab == label:
            L["build_fixture"](path, b, a, stamped=stamped, label=lab)
            _add_a_standing_notice(path)
            _add_arity_rows(path)
            return
    raise KeyError(label)


def _add_a_standing_notice(path: str) -> None:
    """T4 (0041 §11.6.6): the step table's generic row fills every TEXT column, so its one `redactions` row carries an
    event and reads as applied — and v16-notice-state's UPDATE then wrote 0 rows on EVERY fixture (its first campaign:
    96 perturbations, all n/a, found by the per-step count). One STANDING row (no event, a source identity), added here
    rather than in the shared step-table instrument, gives the step a row to write and so a write to perturb. Row data
    only: the manifest is unchanged."""
    conn = sqlite3.connect(path)
    try:
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='redactions'").fetchone():
            conn.execute("INSERT INTO redactions(id, user_id, target_kind, target_id, fields, marker_version, reason, "
                         "store_version_before, store_version_after, event_ref, recorded_at, source_body, source_origin, "
                         "source_user, source_event_ref) VALUES('x-standing','x-user','edge','x-absent','[\"object\"]',1,"
                         "'imported_notice',1,1,NULL,'2026-10-14T00:00:00+00:00','{}','x-origin','x-user','x-user:1')")
            conn.commit()
    finally:
        conn.close()


def _add_arity_rows(path: str) -> None:
    """T5 (0044 §4f): the generic row's relation is no reclassified name and nothing is retired, so the arity
    inventory would write 0 rows on every fixture (T4's lesson, above). One edge retired `superseded` under `measures`,
    and one refusal, give both inventory blocks a row to write. A full `Edge` dump, so every earlier step reads it as
    any legacy row; row data only, the manifest unchanged."""
    from datetime import datetime as _dt, timezone as _tz
    from veracium.schema import Edge, Provenance
    conn = sqlite3.connect(path)
    try:
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='edges'").fetchone():
            e = Edge(id="x-arity", user_id="x-user", subject="user", relation="measures", object="weight 81",
                     invalidated_at=_dt(2050, 1, 1, tzinfo=_tz.utc), invalidation_reason="superseded",
                     provenance=Provenance(author_of_evidence="user", evidence_ref="x-arity"))
            conn.execute("INSERT INTO edges(id,user_id,subject,relation,object,active,quarantined,json) "
                         "VALUES('x-arity','x-user','user','measures','weight 81',0,0,?)", (e.model_dump_json(),))
        if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='supersession_refusals'").fetchone():
            conn.execute("INSERT INTO supersession_refusals VALUES('x-refusal','x-user','x-arity','x-arity','measures',"
                         "3,2,'0003-v1','2026-01-01T00:00:00+00:00')")
        conn.commit()
    finally:
        conn.close()


def step_ranges(writes: list) -> dict:
    """{step: (first index, last index)} over an unperturbed run's writes."""
    out = {}
    for i, w in enumerate(writes):
        s = step_of(w)
        if s:
            lo, hi = out.get(s, (i, i))
            out[s] = (min(lo, i), max(hi, i))
    return out


def judge(res: dict, step: str, baseline_writes: list) -> dict:
    """The three kill conditions for a perturbation of `step` (see the module docstring)."""
    import veracium.store.migration as mig
    e = res["exc"]
    named = isinstance(e, mig.MigrationPostconditionError) and e.step == step
    last = step_ranges(baseline_writes)[step][1]
    sqls = [w["sql"] for w in baseline_writes[:res["issued"]]]
    it = iter(sqls)
    in_order = all(any(w["sql"] == s for s in it) for w in res["writes"])
    position = res["issued"] <= last + 1 and in_order
    unchanged = res["pre"] == res["post"]
    outcome = ("migrated" if e is None else
               f"{type(e).__name__}" + (f"[{getattr(e, 'step', '')}]" if hasattr(e, "step") else
                                        f"[{getattr(e, 'reason', '')}]" if hasattr(e, "reason") else ""))
    return {"outcome": outcome, "refused_at_step": named, "position": position, "unchanged": unchanged,
            "issued": res["issued"], "step_last_write": last, "killed": named and position and unchanged}


# ---- (A) the perturbation cells ------------------------------------------------------------------------------------
def campaign_a(work: str) -> list:
    L = lib()
    path = os.path.join(work, "a.db")
    rows = []
    for label, _b, _a, _st in L["paths"]():
        fresh_fixture(path, label)
        base = run_case(path)
        assert base["exc"] is None, f"{label}: the unperturbed ladder did not migrate: {base['exc']!r}"
        writes = base["writes"]
        for k, w in enumerate(writes):
            step = step_of(w)
            if step is None:
                continue
            modes = ["alter", "skip", "higher"] if w["kind"] == "STAMP" else L["dml_modes"](w["sql"])
            for mode in modes:
                fresh_fixture(path, label)
                plan = L["Plan"](k=k, mode=mode, expect=w["sql"])
                res = run_case(path, plan)
                row = {"path": label, "k": k, "step": step, "mode": mode, "applied": str(plan.applied)[:100]}
                if plan.anchor_ok is not True:
                    row.update(outcome=f"ANCHOR (anchor_ok={plan.anchor_ok})", killed=False)
                elif plan.applied is None or str(plan.applied).startswith("n/a"):
                    row.update(outcome=f"N/A ({plan.applied})", killed=None)
                elif mode == "skip" and w["kind"] == "DML" and w.get("rows") == 0 and res["exc"] is None:
                    # an EQUIVALENT perturbation: the unperturbed write changed 0 rows (the recorder's measured
                    # total_changes delta), so skipping it removes nothing — e.g. v16's registry backfill on a base-1
                    # store, which has no confirmation to copy. Whole-store equality is NOT the test: two UNPERTURBED
                    # runs of one fixture already differ (the clock and minted UUIDs in episodes, store_identity,
                    # edge_event, store_epoch — measured 2026-10-14), so it would refuse every equivalent.
                    row.update(outcome="N/A (equivalent: the write changed 0 rows)", killed=None)
                else:
                    row.update(judge(res, step, writes))
                rows.append(row)
    return rows


# ---- (B) the code mutants ------------------------------------------------------------------------------------------
_CELLS_REL = CELLS_FILE
H_PRESENT = f"{_CELLS_REL}::test_honest_a_legacy_row_with_a_present_observed_at_migrates"
H_ABSENT = f"{_CELLS_REL}::test_honest_a_legacy_row_lacking_observed_at_migrates"
BOTH = (H_PRESENT, H_ABSENT)
C = lambda name: f"{_CELLS_REL}::{name}"                                     # noqa: E731

_ID_LINE = '    _refuse_unless(run.base, STEP_IDENTITY, _identity_problems(run.identity_pre, run.identity_post))\n'
_STAMP_REFUSE = ('    _refuse_unless(run.base, STEP_STAMP, [f"user_version reads {run.stamped}, not {SCHEMA_VERSION}"]\n'
                 '                   if run.stamped != SCHEMA_VERSION else [])\n')
_LAST_ENTRY = '    ForwardEntry(0, 16, "check", _check_refusal_inventory_edges),\n)\n'

# (id, the invariant it attacks, [(anchor, replacement), ...] in migration.py, honest nodes, the NAMED killing cell,
#  what it reintroduces)
MUTANTS = [
    ("M121-string-compare", "M121",
     [("                want = _typed(f, raw[k])\n", "                want, got = raw[k], new.get(k)\n")],
     BOTH, C("test_cell_a_legacy_row_in_isoformat_plus0000_form_migrates"),
     "present keys compared as strings: a '+00:00' legacy value re-serialised as 'Z' falsely refuses"),
    ("M121-added-key-any-value", "M121",
     [("                want = _typed(f, f.default)\n", "                want = got\n")],
     BOTH, C("test_cell_an_added_key_with_a_non_default_value_refuses_at_the_chain_step"),
     "a key the dump added is accepted whatever its value"),
    ("M121-undeclared-raw-key-tolerated", "M121",
     [("        if k not in fields and (path + (k,)) not in RETIRED_EPISODE_KEYS:\n", "        if False:\n")],
     BOTH, C("test_cell_an_undeclared_raw_key_refuses_at_the_chain_step"),
     "a raw key no model declares is dropped silently, outside the retired set (0016 D2)"),
    ("M121-raw-read-through-the-model", "M121",
     [("        _compare_converted(old, new, Episode, (), now, out)\n",
       "        _compare_converted(json.loads(Episode.model_validate_json(blob).model_dump_json()), new, Episode, (), now,"
       " out)\n")],
     (H_PRESENT,), C("test_cell_an_undeclared_raw_key_refuses_at_the_chain_step"),
     "the legacy row read through the model: its dropped keys and refilled defaults pass vacuously"),
    ("M121-clock-per-row", "M121",
     [('            prov["observed_at"] = now.isoformat()             # the ONE stated clock read, never a per-row '
       'default\n', '            prov["observed_at"] = _clock().isoformat()\n')],
     (H_PRESENT,), C("test_cell_a_missing_observed_at_is_filled_from_the_one_clock_read"),
     "the clock re-read per row: the fill is not the recorded value"),
    ("M121-present-observed-at-overwritten", "M121",
     [('        if isinstance(prov, dict) and "observed_at" not in prov:\n', "        if isinstance(prov, dict):\n")],
     (H_ABSENT,), C("test_cell_a_present_observed_at_is_kept"),
     "a present observed_at overwritten with the migration's clock"),
    ("M123-own-variable", "M123",
     [('    run.stamped = conn.execute("PRAGMA user_version").fetchone()[0]\n', "    run.stamped = SCHEMA_VERSION\n")],
     BOTH, C("test_cell_a_perturbed_stamp_refuses_at_the_stamp"),
     "the stamp postcondition reads the value the step meant to write, not the database"),
    ("M123-identity-checked-only-at-the-end", "M123",
     [('    ForwardEntry(0, 5, "read", _read_identity_post),\n    ForwardEntry(0, 5, "check", _check_identity),\n', ""),
      (_LAST_ENTRY, '    ForwardEntry(0, 16, "check", _check_refusal_inventory_edges),\n'
                    '    ForwardEntry(0, 5, "read", _read_identity_post),\n    ForwardEntry(0, 5, "check", _check_identity),\n)\n')],
     BOTH, C("test_cell_a_perturbed_store_identity_refuses_at_its_step"),
     "the identity postcondition run once, at the end: it still names its step, after later steps wrote"),
    ("M123-failure-commits", "M123",
     [(_STAMP_REFUSE, "    if run.stamped != SCHEMA_VERSION:\n"
                      '        conn.execute("COMMIT"); conn.execute("BEGIN IMMEDIATE")\n' + _STAMP_REFUSE)],
     BOTH, C("test_cell_a_perturbed_stamp_refuses_at_the_stamp"),
     "a failed postcondition commits the migration's writes before refusing"),
    ("M123-step-misclassifies-a-row", "M123",
     [('        if raw.get("kind", kind_default) != "outcome":        # classified from the RAW row (0013 §4f), never a load\n',
       '        if raw.get("kind", kind_default) != "outcome" or outcome_rows:\n')],
     BOTH, C("test_cell_two_legacy_outcome_rows_both_convert"),
     "research stage-2 F1: the step converts only the first legacy outcome row; a postcondition that took its outcome set "
     "from the step would find nothing to check"),
    ("M123-unparseable-converted-row", "M123",
     [("                     (converted.model_dump_json(), eid))\n", "                     (converted.model_dump_json()[:-1], eid))\n")],
     (f"{_CELLS_REL}::test_honest_a_store_above_v3_migrates",), C("test_cell_a_legacy_row_in_isoformat_plus0000_form_migrates"),
     "research stage-2 F2: the step writes a row that is not JSON; the postcondition must refuse, never raise"),
    ("del-chains", "M121", [("    _check_outcome_chains(conn, run.base, run.episodes_before, run.now)\n", "    pass\n")],
     BOTH, C("test_cell_a_perturbed_outcome_chain_refuses_at_its_step"), "the chain step's postcondition removed"),
    ("del-wiki", "M122",
     [('    _refuse_unless(run.base, STEP_WIKI, [f"wiki holds {left} row(s) after the drop"] if left else [])\n',
       "    pass\n")],
     BOTH, C("test_cell_a_skipped_wiki_drop_refuses_at_its_step"), "the wiki step's postcondition removed"),
    ("del-identity", "M118", [(_ID_LINE, "    pass\n")],
     BOTH, C("test_cell_a_perturbed_store_identity_refuses_at_its_step"), "the identity step's postcondition removed"),
    ("del-baseline", "M120",
     [("    _refuse_unless(run.base, STEP_BASELINE, _baseline_problems(conn, run.baseline_edges, {r[0] for r in run.events_before}, "
       "run.now))\n", "    pass\n")],
     BOTH, C("test_cell_a_perturbed_baseline_event_refuses_at_its_step"), "the baseline step's postcondition removed"),
    ("del-epoch", "M119",
     [('    _refuse_unless(run.base, STEP_EPOCH, _epoch_problems(run.epoch_pre, run.epoch_post, run.now))\n', "    pass\n")],
     BOTH, C("test_cell_a_skipped_store_epoch_refuses_at_its_step"), "the epoch step's postcondition removed"),
    ("del-stamp", "M117", [(_STAMP_REFUSE, "    pass\n")],
     BOTH, C("test_cell_a_perturbed_stamp_refuses_at_the_stamp"), "the stamp's postcondition removed"),
]

# (id, [(anchor, replacement)], what it injects, the outcome the classifier must give it)
CONTROLS = [
    ("CTRL-unrelated-TypeError",
     [("def _identity_problems(pre: list, post: list) -> list:\n",
       "def _identity_problems(pre: list, post: list) -> list:\n"
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n')],
     "an UNRELATED TypeError inside the identity postcondition: every migration crossing v5 fails for no reason a "
     "postcondition names", "UNCLASSIFIED"),
]


def cells() -> dict:
    """finding -> its closure cells, read from specs/closure_findings.py (the `::` nodes its closure row's evidence
    runs, in order), as the 0041 campaign's cells() does — never a hand list."""
    spec = importlib.util.spec_from_file_location("pa1_cf", ROOT / "specs" / "closure_findings.py")
    cf = importlib.util.module_from_spec(spec); spec.loader.exec_module(cf)
    return {r[3]: [t for t in shlex.split(r[-1]) if "::" in t]
            for r in cf.CLOSURES if r[0] == "0013" and r[3] == FINDING}


def kill_cells() -> list:
    """The closure row's cited cells; raises if the row does not exist yet."""
    c = cells()
    if FINDING not in c or not c[FINDING]:
        raise SystemExit(f"no closure cells for {FINDING} in specs/closure_findings.py")
    return c[FINDING]


def file_cells() -> list:
    """Every `test_cell_*` in the cells file, in definition order: the row must cite exactly these."""
    tree = ast.parse((ROOT / CELLS_FILE).read_text(encoding="utf-8"))
    return [f"{CELLS_FILE}::{n.name}" for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name.startswith("test_cell_")]


def honest_nodes() -> list:
    return sorted({n for m in MUTANTS for n in m[3]})


def definition_sha(m) -> str:
    return hashlib.sha256(json.dumps(list(m), ensure_ascii=True).encode()).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _digests(root: pathlib.Path) -> dict:
    files = (MIGRATION, SCHEMA_VERSION_PY, STEPTABLE, KINDS, CELLS_FILE, SELF)
    return {f: _sha(root / f) for f in files}


def _snapshot(dst: pathlib.Path):
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                       capture_output=True, check=True)
    for f in filter(None, r.stdout.decode().split("\0")):
        src = ROOT / f
        if src.is_file():
            (dst / f).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst / f)


def _env(root):
    return {**os.environ, "PYTHONPATH": str(root / "src"), "PYTHONDONTWRITEBYTECODE": "1"}


def _imports(root) -> str:
    code = ("import importlib, pathlib, sys\nm = importlib.import_module('veracium.store.migration')\n"
            "assert pathlib.Path(m.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve()), m.__file__\n")
    r = subprocess.run([sys.executable, "-B", "-c", code, str(root / "src")], cwd=root, env=_env(root),
                       capture_output=True, text=True)
    return "ok" if r.returncode == 0 else "error: " + (r.stderr.strip().splitlines() or ["?"])[-1][:200]


def _pytest(root, nodes) -> dict:
    with tempfile.TemporaryDirectory() as d:
        xml = pathlib.Path(d) / "j.xml"
        r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:randomly", "-p", "no:cacheprovider",
                            f"--junitxml={xml}", *nodes], cwd=root, env=_env(root), capture_output=True, text=True)
        failed, errored, passed, kinds = [], [], 0, {}
        if xml.exists():
            for tc in ET.parse(xml).iter("testcase"):
                node = f"{tc.get('file') or tc.get('classname', '').replace('.', '/') + '.py'}::{tc.get('name')}"
                f = tc.find("failure")
                if f is not None:
                    failed.append(node); kinds[node] = MK.failure_kind(f.get("message") or "")
                elif tc.find("error") is not None:
                    errored.append(node)
                elif tc.find("skipped") is None:
                    passed += 1
        summary = (r.stdout.strip().splitlines() or [""])[-1][:160]
    return {"exit": r.returncode, "passed": passed, "failed": sorted(failed), "errored": sorted(errored),
            "kinds": dict(sorted(kinds.items())), "summary": summary}


def _apply(root, edits) -> tuple:
    target = root / MIGRATION
    original = target.read_bytes()
    text = original.decode()
    counts = [text.count(a) for a, _ in edits]
    if counts != [1] * len(edits):
        return original, counts, False
    for a, r in edits:
        text = text.replace(a, r)
    target.write_text(text)
    return original, counts, True


def run_one(root: pathlib.Path, m, cells) -> dict:
    mid, inv, edits, honest, killer, what = m
    row = {"id": mid, "finding": FINDING, "attacks": inv, "what": what, "killing_cell": killer,
           "honest_nodes": list(honest),
           "definition_sha256": definition_sha(m)}
    original, counts, ok = _apply(root, edits)
    row["anchor_counts"] = counts
    if not ok:
        return {**row, "outcome": "ANCHOR", "good": False}
    try:
        row["import"] = _imports(root)
        h = _pytest(root, list(honest))
        row["honest"] = ("pass" if h["exit"] == 0 and h["passed"] == len(honest) and not h["failed"] and not h["errored"]
                         else f"fail: {len(h['failed'])} failed, {len(h['errored'])} errored of {len(honest)}")
        c = _pytest(root, cells)
    finally:
        (root / MIGRATION).write_bytes(original)
    assert _sha(root / MIGRATION) == hashlib.sha256(original).hexdigest()
    row.update(MK.classify(c["kinds"], c["failed"], c["errored"]))
    row.update({"cells": len(cells), "pytest": c["summary"], "killer_failed": killer in c["failed"]})
    row["good"] = (row["import"] == "ok" and row["honest"] == "pass" and row["outcome"] == "KILLED"
                   and row["killer_failed"])
    return row


def run_control(root: pathlib.Path, ctl, cells) -> dict:
    cid, edits, what, expected = ctl
    row = {"id": cid, "what": what, "expected": expected}
    original, counts, ok = _apply(root, edits)
    row["anchor_counts"] = counts
    if not ok:
        return {**row, "outcome": "ANCHOR", "good": False}
    try:
        row["import"] = _imports(root)
        c = _pytest(root, cells)
    finally:
        (root / MIGRATION).write_bytes(original)
    row.update(MK.classify(c["kinds"], c["failed"], c["errored"]))
    row["good"] = row["import"] == "ok" and row["outcome"] == expected and bool(row["cells_failed"])
    return row


def campaign() -> dict:
    t0 = time.time()
    cells = kill_cells()
    with tempfile.TemporaryDirectory() as w:
        a_rows = campaign_a(w)
    t_a = time.time() - t0
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _snapshot(root)
        clean_imports = _imports(root)
        clean_cells = _pytest(root, cells)
        clean_honest = _pytest(root, honest_nodes())
        if (clean_imports != "ok" or clean_cells["failed"] or clean_cells["errored"] or clean_cells["exit"] != 0
                or clean_honest["exit"] != 0 or clean_honest["failed"]):
            raise SystemExit(f"CLEAN failed — no mutant is meaningful on a tree whose controls fail: "
                             f"{clean_imports} {clean_cells} {clean_honest}")
        rows = [run_one(root, m, cells) for m in MUTANTS]
        controls = [run_control(root, k, cells) for k in CONTROLS]
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.split("\n")
    per_step = collections.defaultdict(collections.Counter)
    for r in a_rows:
        per_step[r["step"]]["killed" if r["killed"] else "n/a" if r["killed"] is None else "NOT killed"] += 1
    body = {
        "header": {"spec": "0013", "finding": FINDING, "commit": head,
                   "tracked_changes": sorted(l[3:] for l in dirty if l.strip()),
                   "python": platform.python_version(), "platform": platform.platform(), "sqlite": sqlite3.sqlite_version,
                   "digests": _digests(ROOT), "definitions": {m[0]: definition_sha(m) for m in MUTANTS},
                   "control_definitions": {k[0]: definition_sha(k) for k in CONTROLS},
                   "cells": {FINDING: cells}, "honest_nodes": honest_nodes(),
                   "clean": {"cells_passed": clean_cells["passed"], "honest_passed": clean_honest["passed"]}},
        "perturbations": a_rows,
        "rows": rows,
        "controls": controls,
        "summary": {"perturbations": len(a_rows), "perturbations_killed": sum(r["killed"] is True for r in a_rows),
                    "perturbations_not_applicable": sum(r["killed"] is None for r in a_rows),
                    "per_step": {s: dict(c) for s, c in sorted(per_step.items())},
                    "rows": len(rows), "killed": sum(r.get("outcome") == "KILLED" for r in rows),
                    "good": sum(r["good"] for r in rows),
                    "cell_kinds": dict(sorted(collections.Counter(
                        k for r in rows for k in r.get("cell_kinds", {}).values()).items())),
                    "controls": len(controls), "controls_good": sum(k["good"] for k in controls),
                    "seconds": {"part_a": round(t_a), "total": round(time.time() - t0)}},
    }
    return {**body, "body_sha256": hashlib.sha256(canonical(body)).hexdigest()}


def render(table: dict) -> str:
    return json.dumps(table, indent=1, sort_keys=True, ensure_ascii=True) + "\n"


def problems(path: pathlib.Path = TABLE) -> list[str]:
    if not path.exists():
        return [f"{path.name} does not exist — run --write"]
    try:
        t = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
    except ValueError as e:
        return [f"{path.name} is not JSON, or carries a duplicate key: {e}"]
    out = []
    body = {k: v for k, v in t.items() if k != "body_sha256"}
    if hashlib.sha256(canonical(body)).hexdigest() != t.get("body_sha256"):
        out.append("the table does not match its own body digest (edited after writing)")
    h = t.get("header", {})
    if h.get("spec") != "0013" or h.get("finding") != FINDING:
        out.append(f"the table declares {h.get('spec')!r}/{h.get('finding')!r}, not 0013/{FINDING}")
    if h.get("definitions") != {m[0]: definition_sha(m) for m in MUTANTS}:
        out.append("the mutant definitions differ from the runner's — run --write")
    if h.get("control_definitions") != {k[0]: definition_sha(k) for k in CONTROLS}:
        out.append("the control definitions differ from the runner's — run --write")
    cited = cells()
    if h.get("cells") != cited:
        out.append("the closure cells differ from what specs/closure_findings.py cites now — run --write")
    if cited.get(FINDING) and sorted(cited[FINDING]) != sorted(file_cells()):
        out.append(f"the closure row's cited cells are not exactly the cells file's test_cell_* functions")
    if h.get("honest_nodes") != honest_nodes():
        out.append("the honest nodes differ from the runner's — run --write")
    live = _digests(ROOT)
    stale = sorted(f for f in set(live) | set(h.get("digests", {})) if live.get(f) != h.get("digests", {}).get(f))
    if stale:
        out.append(f"stale: {stale} — run --write")
    text = (ROOT / MIGRATION).read_text()
    for m in list(MUTANTS) + [(k[0], None, k[1]) for k in CONTROLS]:
        for a, _r in m[2]:
            if text.count(a) != 1:
                out.append(f"{m[0]}: an anchor occurs {text.count(a)} time(s) in {MIGRATION}")
    defined = {n.split("::")[1] for n in file_cells()} | {n.split("::")[1] for n in honest_nodes()}
    for m in MUTANTS:
        if m[4].split("::")[1] not in defined:
            out.append(f"{m[0]}: its killing cell {m[4]} is not a test in {CELLS_FILE}")
    rows = t.get("rows", [])
    if [r.get("id") for r in rows] != [m[0] for m in MUTANTS]:
        out.append("the rows are not one per mutant, in order")
    for r in rows:
        if r.get("finding") != FINDING:
            out.append(f"{r.get('id')}: its finding is {r.get('finding')!r}, not {FINDING}")
        recount = MK.classify(r.get("cell_kinds") or {}, r.get("cells_failed") or [], r.get("cells_errored") or [])
        if not (r.get("outcome") == "KILLED" == recount["outcome"] and r.get("kill_kind") == recount["kill_kind"]
                and r.get("import") == "ok" and r.get("honest") == "pass" and r.get("good") is True
                and r.get("killing_cell") in (r.get("cells_failed") or []) and r.get("killer_failed") is True
                and not r.get("cells_errored")):
            out.append(f"{r.get('id')}: not a good row (outcome {r.get('outcome')}, recounted from its cell kinds "
                       f"{recount['outcome']}, import {r.get('import')}, honest {r.get('honest')}, named killing cell "
                       f"{'failed' if r.get('killing_cell') in (r.get('cells_failed') or []) else 'did NOT fail'})")
    ctls = t.get("controls", [])
    if [k.get("id") for k in ctls] != [k[0] for k in CONTROLS]:
        out.append("the controls are not one per CONTROLS entry, in order")
    for k in ctls:
        recount = MK.classify(k.get("cell_kinds") or {}, k.get("cells_failed") or [], k.get("cells_errored") or [])
        if not (k.get("good") is True and k.get("outcome") == k.get("expected") == recount["outcome"] != "KILLED"):
            out.append(f"{k.get('id')}: the classifier's negative control is not good (outcome {k.get('outcome')}, "
                       f"recounted {recount['outcome']}, expected {k.get('expected')})")
    pert = t.get("perturbations", [])
    if not pert:
        out.append("no perturbation cells")
    for r in pert:
        if r.get("killed") is None:
            continue
        if not (r.get("killed") is True and r.get("refused_at_step") is True and r.get("position") is True
                and r.get("unchanged") is True):
            out.append(f"perturbation {r.get('path')} W{r.get('k')} {r.get('step')} {r.get('mode')}: not killed "
                       f"(outcome {r.get('outcome')}, named {r.get('refused_at_step')}, position {r.get('position')}, "
                       f"unchanged {r.get('unchanged')})")
    steps = {r.get("step") for r in pert}
    import veracium.store.migration as mig
    want_steps = {v for k, v in vars(mig).items() if k.startswith("STEP_") and isinstance(v, str)} - set(WRITELESS_STEPS)
    if steps != want_steps:
        out.append(f"the perturbation cells cover steps {sorted(steps)}, not every writing step {sorted(want_steps)}")
    return out


def main() -> int:
    if "--write" in sys.argv:
        t = campaign()
        TABLE.write_text(render(t), encoding="utf-8")
        print(f"wrote {TABLE.relative_to(ROOT)}: {json.dumps(t['summary'])} (body_sha256 {t['body_sha256']})")
        for r in t["rows"]:
            print(f"  {r['id']:40s} {r.get('outcome', ''):12s} import={r.get('import')} honest={r.get('honest')} "
                  f"killer_failed={r.get('killer_failed')} kinds={sorted(set(r.get('cell_kinds', {}).values()))}")
        for k in t["controls"]:
            print(f"  {k['id']:40s} {k.get('outcome', ''):12s} good={k['good']}")
        bad = problems()
        for b in bad:
            print(f"PROBLEM: {b}")
        return 0 if not bad else 1
    bad = problems()
    for b in bad:
        print(f"STALE: {b}")
    if not bad:
        t = json.loads(TABLE.read_text(), object_pairs_hook=_strict_pairs)
        print(f"mutation-table.json current: {json.dumps(t['summary'])} (body_sha256 {t['body_sha256']})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
