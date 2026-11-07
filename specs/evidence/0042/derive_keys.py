"""Derive the plan's keys from the artifacts, for a given tree:
  1. ENFORCEMENT keys from the instrumented SOURCE — every return/raise whose value is `VAR.fire(...)`
     with VAR bound by `VAR = declare_site("id")`, kept only when the statement is an inventory
     candidate; plus, in the same function, a candidate `return NAME` where NAME is the Name a fire
     statement returns (the census-off branch of a bypassed predicate) — bound to the same id.
  2. OVERRIDE (per-line NOT reasons) re-keyed by (module, qualname, kind, ordinal) from the PLAN-TIME
     inventory (the literal was never rewritten, so one hop is exact) to the target inventory.
Un-instrumented enforcement ids keep their keys. Lives beside the review it maintains
(specs/evidence/0042): inventory_at_plan.json is the plan-time inventory and override_at_plan.py the
never-rewritten OVERRIDE literal. Usage:
  derive_keys.py <src/veracium> <target OUTPUT.json> <semantic_review.py> <out.py> [<previous reviewed_points.json>]"""
import ast, pathlib, re, sys, json, collections, importlib.util


def _strict_pairs(pairs):
    """0026's evidence-boundary rule: a duplicate key is a REFUSAL, never last-wins."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out
root, inv_path, plan_in, plan_out = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
S = pathlib.Path(__file__).resolve().parent
inv = json.load(open(inv_path), object_pairs_hook=_strict_pairs)["sites"]; inv_key = {(x["module"], x["line"]): x for x in inv}
found = collections.defaultdict(list); skipped = []
for p in sorted(root.rglob("*.py")):
    module = str(p.relative_to(root)); tree = ast.parse(p.read_text())
    var_id = {n.targets[0].id: n.value.args[0].value for n in tree.body
              if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
              and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", getattr(n.value.func, "attr", "")) == "declare_site"}
    if not var_id: continue
    fn_of = {}
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn):
                if isinstance(n, (ast.Return, ast.Raise)): fn_of.setdefault(n, fn)
    by_fn_names = collections.defaultdict(dict)       # fn -> {Name returned through fire: id}
    for n, fn in fn_of.items():
        v = n.value if isinstance(n, ast.Return) else n.exc
        if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "fire" and isinstance(v.func.value, ast.Name) and v.func.value.id in var_id:
            sid = var_id[v.func.value.id]
            if (module, n.lineno) in inv_key: found[sid].append((module, n.lineno))
            else: skipped.append((module, n.lineno, sid))
            if v.args and isinstance(v.args[0], ast.Name): by_fn_names[fn][v.args[0].id] = sid
    # round 7 (INV-7 R6-5): the four hot Edge predicates carry ONE return statement for every arm, so the
    # fire is an ASSIGNMENT — `q = SITE.fire(q)` — and the decision statement is the `return q` after it;
    # a Name assigned through fire maps to the id exactly as a Name returned through fire does
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(fn):
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                    v = n.value
                    if isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute) and v.func.attr == "fire" \
                            and isinstance(v.func.value, ast.Name) and v.func.value.id in var_id:
                        by_fn_names[fn][n.targets[0].id] = var_id[v.func.value.id]
    for n, fn in fn_of.items():
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Name) and n.value.id in by_fn_names.get(fn, {}) and (module, n.lineno) in inv_key:
            found[by_fn_names[fn][n.value.id]].append((module, n.lineno))
s = open(plan_in).read()
for sid in found:
    s = re.sub(r'^e\("[^"]+",\s*\d+,\s*"' + re.escape(sid) + r'",[^\n]*\n', "", s, flags=re.M)
    s = re.sub(r'^for ln in \([\d, ]+\):\n    e\("[^"]+", ln, "' + re.escape(sid) + r'",[^\n]*\n', "", s, flags=re.M)
s = re.sub(r"^# ---- DERIVED from the instrumented source.*\n", "", s, flags=re.M)
spec = importlib.util.spec_from_file_location("plan", plan_in); plan = importlib.util.module_from_spec(spec); spec.loader.exec_module(plan)
meta = {}
for (m, l), (sid, sp, inv_, label) in plan.E.items(): meta.setdefault(sid, (sp, inv_, label))
lines = ["", "# ---- DERIVED from the instrumented source (derive_keys.py): every fire()-wrapped candidate ----"]
for sid in sorted(found):
    sp, inv_, label = meta[sid]
    for m, l in sorted(set(found[sid])): lines.append(f'e("{m}", {l}, "{sid}", "{sp}", "{inv_}", "{label}")')
s = s.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
# OVERRIDE: one exact hop from the plan-time inventory to the target
old_inv = json.load(open(S / "inventory_at_plan.json"), object_pairs_hook=_strict_pairs)["sites"]
def oi(sites):
    d = {}
    for x in sorted(sites, key=lambda x: (x["module"], x["line"])): d.setdefault((x["module"], x["qualname"], x["kind"]), []).append(x["line"])
    return d
O, N = oi(old_inv), oi(inv); oldkey = {(x["module"], x["line"]): x for x in old_inv}
ov_src = open(S / "override_at_plan.py").read()
# When a group GAINED candidates since plan time (a new refusal inside a function that carries OVERRIDE
# lines — 0041 tranche 1, commit_outcome_import_plan 8 -> 9 RAISEs), the ordinal hop is ambiguous. The
# previous generation's reviewed_points.json (5th arg; the committed one) carries every candidate's
# STATEMENT text at its stable key, so an override line is re-keyed by TEXT within its group instead:
# plan-time line -> (group, ordinal) -> the statement the last generation recorded -> the one current
# line in the group carrying that statement. Asserted unique, or refused.
prev_rp = json.load(open(sys.argv[5]), object_pairs_hook=_strict_pairs) if len(sys.argv) > 5 else None
# the carry below needs the reviewed points; without them, an input holding entries the plan-time literal lacks REFUSES
# here, before any re-key (the plan-time hop's own refusal fires first on a moved group, and named the wrong remedy)
if prev_rp is None:
    _n_plan = len(next(ast.literal_eval(n.value) for n in ast.parse(ov_src).body
                       if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "OVERRIDE"))
    assert len(plan.OVERRIDE) == _n_plan, (len(plan.OVERRIDE), _n_plan, "the input review carries OVERRIDE entries "
                                           "the plan-time literal lacks; pass the previous reviewed_points.json to "
                                           "carry them")
src_lines = {}
def stmt_at(module, line):
    if module not in src_lines: src_lines[module] = (root / module).read_text().split("\n")
    return src_lines[module][line - 1].strip()
def sub_ov(m):
    mod, ln = m.group(1), int(m.group(2)); o = oldkey[(mod, ln)]; g = (o["module"], o["qualname"], o["kind"])
    nl = N[g]
    if len(nl) == len(O[g]):
        return f'("{mod}", {nl[O[g].index(ln)]})'
    # 0041 tranche 5 (2026-09-20): a STRUCTURAL attribute the inventory records (`bare` — a bare `raise`
    # re-raising after a rollback) identifies a statement across generations without any text: when exactly
    # one current candidate in the group shares the plan-time entry's attributes, that is the hop. The text
    # path below fails on this function since tranche 4b — every refusal in it opens with the same line, and
    # the previous generation's ordinal no longer names the plan-time statement.
    attrs = {k: v for k, v in o.items() if k not in ("line",)}
    same = [x["line"] for x in inv if all(x.get(k) == v for k, v in attrs.items()) and x.get("bare") is True]
    if attrs.get("bare") is True and len(same) == 1:
        return f'("{mod}", {same[0]})'
    assert prev_rp is not None, (g, O[g], nl, "the group's candidate count changed; pass the previous reviewed_points.json to re-key by text")
    key = f"{g[0]}:{g[1]}:{g[2]}:{O[g].index(ln) + 1}"
    prev = [r for r in prev_rp.values() if r["key"] == key]
    assert len(prev) == 1, (key, len(prev))
    matches = [l for l in nl if stmt_at(mod, l) == prev[0]["statement"]]
    assert len(matches) == 1, (key, prev[0]["statement"][:60], matches)
    return f'("{mod}", {matches[0]})'
ov_new = re.sub(r'\("([^"]+)",\s*(\d+)\)', sub_ov, ov_src.split("\n", 1)[1])
# 2026-10-24 (R-II round 3, NEXT-ROUND): an OVERRIDE entry added AFTER plan time lives only in the input review, so
# rebuilding from override_at_plan.py alone dropped it — four at RII-R2-01 (schema.py 659 and 686/1438 among them),
# re-added by hand each generation. Every INPUT entry is now re-keyed to the target through the previous generation's
# reviewed_points.json (its stable key; its statement text where the group's count moved), and one the plan-time hop
# does not produce is CARRIED with its comment. A carried key the hop produces under ANOTHER class refuses.
ov_plan = next(ast.literal_eval(n.value) for n in ast.parse(ov_new).body
               if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "OVERRIDE")
if prev_rp is not None:
    prev_rows = list(prev_rp.values())
    prev_at = {(r["key"].split(":", 1)[0], r["line"]): r for r in prev_rows}
    prev_n = collections.Counter(tuple([r["key"].split(":", 1)[0]] + r["key"].split(":", 1)[1].rsplit(":", 2)[:2])
                                 for r in prev_rows)
    in_ov = re.search(r"^OVERRIDE = \{.*?^\}\n", s, flags=re.M | re.S).group(0)
    note = {(m.group(1), int(m.group(2))): m.group(3) for m in
            re.finditer(r'\("([^"]+)",\s*(\d+)\):\s*"[^"]+",\s*(#[^\n]*)$', in_ov, flags=re.M)}
    carried = []
    for (mod, ln), cls in sorted(plan.OVERRIDE.items()):
        r = prev_at.get((mod, ln))
        assert r is not None, (mod, ln, "an input OVERRIDE line the previous reviewed_points.json does not record")
        q, k, o = r["key"].split(":", 1)[1].rsplit(":", 2)
        nl = N.get((mod, q, k), [])
        if len(nl) == prev_n[(mod, q, k)]:
            cur = nl[int(o) - 1]
        else:
            hits = [l for l in nl if stmt_at(mod, l) == r["statement"]]
            if len(hits) > 1:
                # 2026-11-07 (0018 round 5): the group gained a candidate, and the entry's text occurs more than once in it
                # (two bare `raise` lines in run_release_rung). The entry is the same OCCURRENCE of that text, counted in line
                # order, provided the number of same-text statements in the group did not change; otherwise this refuses.
                same_prev = sorted(x["line"] for x in prev_rows if x["key"].split(":", 1)[0] == mod
                                   and tuple(x["key"].split(":", 1)[1].rsplit(":", 2)[:2]) == (q, k)
                                   and x["statement"] == r["statement"])
                assert len(same_prev) == len(hits), (r["key"], r["statement"][:60], hits, same_prev)
                hits = [hits[same_prev.index(ln)]]
            assert len(hits) == 1, (r["key"], r["statement"][:60], hits)
            cur = hits[0]
        if (mod, cur) in ov_plan:
            assert ov_plan[(mod, cur)] == cls, (r["key"], ov_plan[(mod, cur)], cls, "the input reclassifies a plan-time entry")
            continue
        carried.append(f'    ("{mod}", {cur}): "{cls}",   ' + note.get((mod, ln), f"# carried: {r['key']}"))
    if carried:
        ov_new = re.sub(r"^\}\n", "\n".join(carried) + "\n}\n", ov_new, count=1, flags=re.M)
    print(f"carried {len(carried)} OVERRIDE entr(y/ies) added after plan time")
s = re.sub(r"^OVERRIDE = \{.*?^\}\n", lambda _m: ov_new, s, flags=re.M | re.S)
open(plan_out, "w").write(s)
spec = importlib.util.spec_from_file_location("plan2", plan_out); p2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p2)
unres = [k for k in p2.E if k not in inv_key]; ov_unres = [k for k in p2.OVERRIDE if k not in inv_key]
print(f"derived {len(found)} ids over {sum(len(set(v)) for v in found.values())} candidates (skipped {len(skipped)} non-candidate fire statements) | entries {len(p2.E)} ids {len({v[0] for v in p2.E.values()})} | unresolved E {unres} | OVERRIDE keys {len(p2.OVERRIDE)} unresolved {ov_unres}")
