# Mutation-Matrix: tests/test_0042_retired_overrides.py::test_each_forged_retirement_refuses_by_name
"""specs/0042 (the derived keys): the RETIRED plan-time OVERRIDE entries. `override_at_plan.py` is the never-rewritten
plan-time literal, and derive_keys re-keys each of its per-line NOT reasons in one hop to the current inventory. When
a code change REMOVES the statement an override decided about, its (module, qualname, kind) group is gone and the hop
has nowhere to land: derive_keys refuses. A vanished overridden statement is what a reviewer should SEE, so it is never
dropped silently: it is retired HERE, by a declared entry, and every entry is checked:

  - its plan-time key names an override in the literal, under the class the entry says it retires;
  - the statement the previous generation recorded for its group is the text the entry quotes, in the generation that
    retires it, and NOTHING in every later one (a retirement cannot be keyed onto the wrong line now, and a statement
    reappearing in the group later makes it stale, below);
  - its group has NO candidate in the current inventory (a retirement whose statement still exists is stale);
  - each replacement it names is a site FIRED INSIDE THE RETIRED STATEMENT'S OWN FUNCTION in the current tree (the
    decision moved to declared sites there, not anywhere; research's stage 2, SF2), or the entry says "none" with a
    reason.

derive_keys drops exactly the retired entries and still refuses any other vanished group. override_at_plan.py stays
byte-identical."""
from __future__ import annotations

RETIRED_OVERRIDES = {
    # specs/0049 v2.2 (0049-R1-01): edges_since's `return [e for e in self.store.edges(...) if ...]` (a filter by a
    # non-policy criterion: control-flow) became a loop whose two refusals are declared sites (E2, E2b)
    ("__init__.py", 1750): {
        "class": "control-flow",
        "group": ("__init__.py", "Memory.edges_since", "FILTER_RETURN"),
        "statement": "return [e for e in self.store.edges(user_id, active_only=False,",
        "replaced_by": ("memory.edges-since.no-journal", "memory.edges-since.no-journal-event"),
        "reason": "specs/0049: the learned-time filter now refuses instead of guessing; both refusals are declared sites",
    },
}


class RetirementRefused(ValueError):
    """A retirement that does not hold: named by its plan key and the property that failed."""


def check(retired: dict, plan_override: dict, plan_inventory: list, target_inventory: list,
          previous_reviewed: dict, fired_in: dict) -> set:
    """Validate every retirement; returns the set of plan keys to drop from the hop. REFUSES on the first entry that
    fails, by name. `plan_override` is override_at_plan.py's OVERRIDE; the inventories are lists of
    {module, qualname, kind, line}; `previous_reviewed` is the committed reviewed_points.json; `fired_in` maps each
    declared site id to the {(module, qualname)} its fire statements sit in, in the current tree."""
    target_groups = {(x["module"], x["qualname"], x["kind"]) for x in target_inventory}
    plan_at = {(x["module"], x["line"]): (x["module"], x["qualname"], x["kind"]) for x in plan_inventory}
    by_key = {}
    for row in previous_reviewed.values():
        by_key.setdefault(row["key"].rsplit(":", 1)[0], []).append(row)
    out = set()
    for key, entry in sorted(retired.items()):
        name = f"retired override {key[0]}:{key[1]}"
        if key not in plan_override:
            raise RetirementRefused(f"{name}: no such entry in override_at_plan.py")
        if plan_override[key] != entry["class"]:
            raise RetirementRefused(f"{name}: the literal says {plan_override[key]!r}, the retirement {entry['class']!r}")
        if plan_at.get(key) != tuple(entry["group"]):
            raise RetirementRefused(f"{name}: the plan-time inventory places {plan_at.get(key)} there, not {entry['group']}")
        if tuple(entry["group"]) in target_groups:
            raise RetirementRefused(f"{name}: STALE, its group {entry['group']} still has a candidate in the tree")
        # the RETIRING generation's previous reviewed points record the vanished statement, and it must be the quoted
        # text; every LATER generation records nothing for the group (it is gone, and the stale check above refuses
        # the moment any candidate reappears in it), so a retirement cannot slide onto a different statement
        recorded = [r["statement"] for r in by_key.get(":".join(entry["group"]), [])]
        if recorded not in ([entry["statement"]], []):
            raise RetirementRefused(f"{name}: the previous generation recorded {recorded!r} for the group, "
                                    f"not the quoted statement {entry['statement']!r}")
        repl = entry["replaced_by"]
        if repl == "none":
            if not entry.get("reason"):
                raise RetirementRefused(f"{name}: replaced by none, with no reason")
        else:
            where = tuple(entry["group"][:2])
            missing = [s for s in repl if s not in fired_in]
            if not repl or missing:
                raise RetirementRefused(f"{name}: replacement site(s) not declared in the tree: {missing or repl!r}")
            elsewhere = [s for s in repl if where not in fired_in[s]]
            if elsewhere:
                raise RetirementRefused(f"{name}: replacement site(s) {elsewhere!r} are not fired in "
                                        f"{where[0]}:{where[1]}, the retired statement's function")
        out.add(key)
    return out
