"""specs/0022 — the SELF-EXECUTING vector harness.

Loads `vectors.json`, executes every vector against `reference_revocation.py`,
and reports. Run it directly; exit 0 means every pinned vector agrees with the
reference. 0022 R11 binds any implementation to the same file, which is what
makes "the shipped code agrees with the spec" an artifact rather than a claim
(the `specs/evidence/0020/vector_harness.py` pattern, whose vectors caught two
defects the prose did not).

Vector schema, per kind (every vector: {"name", "kind", "expect", ...}):

- digest:          {"origin": str|null, "source_id": str|null}
                   expect = "none" | {"same_as": {origin, source_id}}
                          | {"differs_from": {...}} | "RevocationError"
- standing:        {"rows": [revocation rows], "query": identity}
                   expect = bool | "RevocationError"
- row_class:       {"row": contribution row}
                   expect = class | "RevocationError" | "RevocationLinkageError"
- basis:           {"rows": [...], "standing": [identity, ...],
                    "retired": [[type, id], ...]?}
                   expect = "sole-basis" | "corroborated"
- recompute:       {"rows": [...], "standing": [...]}
                   expect = {"valid_from","observed_at","confidence"}
                          | "RevocationError"
- sweep:           {"store": {...}, "target": identity,
                    "proposed": {action, at, reason}|null}
                   expect = a SUBSET of the statement, compared field by field
                            (any of: standing, direct, affected, retire,
                             recompute, descendants, counts, graph_walkable,
                             complete, effects, classes, kinds)
                          | "RevocationError" | "RevocationLinkageError"
- preview_agrees:  {"store": {...}, "target": identity, "proposed": {...}}
                   expect = "identical" — runs the sweep TWICE (the preview
                   call and the commit call), applies the commit's effects,
                   and asserts the two statements are equal
- append_only:     {"store": {...}, "target": identity, "proposed": {...}}
                   expect = "append-only" — applies the effects and asserts
                   the input store is untouched, no record disappeared, and
                   `history` only grew
- effect_verbs:    {} ; expect = the closed verb list (no delete, no edit)

Identities in vectors are {"origin": str|null, "source_id": str|null} and are
digested at run time against LOCAL, so no vector hard-codes a hash.
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from reference_revocation import (  # noqa: E402
    BASIS_CORROBORATED, BASIS_SOLE, EFFECT_VERBS, RevocationError,
    RevocationLinkageError, apply_effects, basis, digest_of, recompute,
    row_class, standing_revocations, sweep)

LOCAL = "org-local-9f2c"

_ERRORS = {"RevocationError": RevocationError,
           "RevocationLinkageError": RevocationLinkageError}


def _is_error(expect):
    """`expect` may be a dict, and `dict in dict` raises rather than being
    False — a small thing that would otherwise make every structural vector
    look like a harness crash."""
    return isinstance(expect, str) and expect in _ERRORS


def D(identity):
    """A vector's identity → the digest the store would carry."""
    if identity is None:
        return None
    return digest_of(identity.get("origin"), identity.get("source_id"), LOCAL)


def _sub(value):
    """Substitute {"identity": {...}} markers with digests, recursively, so
    vectors stay JSON-pure and never embed a hash."""
    if isinstance(value, dict):
        if set(value) == {"identity"}:
            return D(value["identity"])
        return {k: _sub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sub(v) for v in value]
    return value


def _keys(pairs):
    return [tuple(p) for p in pairs]


def _expect_error(name, fn):
    want = _ERRORS[name]
    try:
        fn()
    except RevocationLinkageError as e:
        return (None if want is RevocationLinkageError
                else f"RevocationLinkageError where {name} expected: {e}")
    except RevocationError as e:
        # RevocationLinkageError subclasses RevocationError; reaching here
        # means a plain one, so an expectation of the subclass must FAIL.
        return (None if want is RevocationError
                else f"plain RevocationError where {name} expected: {e}")
    return f"expected {name}, none raised"


def _run_one(v):
    kind, expect = v["kind"], v["expect"]

    if kind == "digest":
        if _is_error(expect):
            return _expect_error(expect, lambda: D(v))
        got = D(v)
        if expect == "none":
            return None if got is None else f"expected None, got {got!r}"
        if "same_as" in expect:
            return (None if got == D(expect["same_as"])
                    else "digests differ where they must match")
        return (None if got != D(expect["differs_from"])
                else "digests COLLIDE where they must differ")

    if kind == "standing":
        rows = _sub(v["rows"])
        if _is_error(expect):
            return _expect_error(expect,
                                 lambda: standing_revocations(rows, "u1"))
        got = D(v["query"]) in standing_revocations(rows, "u1")
        return None if got is expect else f"standing={got}, expected {expect}"

    if kind == "row_class":
        row = _sub(v["row"])
        if _is_error(expect):
            return _expect_error(expect, lambda: row_class(row))
        got = row_class(row)
        return None if got == expect else f"got {got}, expected {expect}"

    if kind == "basis":
        rows = _sub(v["rows"])
        standing = frozenset(D(i) for i in v["standing"])
        retired = frozenset(tuple(k) for k in v.get("retired", ()))
        got = basis(rows, standing, retired)
        want = {"sole-basis": BASIS_SOLE,
                "corroborated": BASIS_CORROBORATED}[expect]
        return None if got == want else f"got {got}, expected {want}"

    if kind == "recompute":
        rows = _sub(v["rows"])
        standing = frozenset(D(i) for i in v["standing"])
        if _is_error(expect):
            return _expect_error(expect, lambda: recompute(rows, standing))
        got = recompute(rows, standing)
        return None if got == expect else f"got {got!r}, expected {expect!r}"

    if kind in ("sweep", "preview_agrees", "append_only"):
        store = _sub(v["store"])
        target = D(v["target"])
        proposed = _sub(v.get("proposed"))
        if _is_error(expect):
            return _expect_error(
                expect, lambda: sweep(store, target, proposed=proposed))

        if kind == "sweep":
            got = sweep(store, target, proposed=proposed)
            for field, want in expect.items():
                if field in ("direct", "affected", "retire", "recompute",
                             "descendants"):
                    want = _keys(want)
                if got[field] != want:
                    return f"{field}: got {got[field]!r}, expected {want!r}"
            return None

        if kind == "preview_agrees":
            # THE Q3 RULING, EXECUTED: the preview and the commit are one
            # computation. Run it as a preview, run it again as the commit's
            # own planning call, and require byte-equality of the statement.
            before = copy.deepcopy(store)
            preview = sweep(store, target, proposed=proposed)
            if store != before:
                return "the PREVIEW mutated the store"
            committed = sweep(store, target, proposed=proposed)
            if preview != committed:
                return "preview and commit statements DIVERGE"
            after = apply_effects(store, committed)
            # and the second call's plan, replanned against the SAME inputs,
            # is still the same statement — the planner is a pure function
            again = sweep(store, target, proposed=proposed)
            if again != preview:
                return "the planner is not a pure function of its inputs"
            if len(after["records"]) != len(store["records"]):
                return "applying the plan changed the record count"
            return None

        # append_only
        before = copy.deepcopy(store)
        stmt = sweep(store, target, proposed=proposed)
        after = apply_effects(store, stmt)
        if store != before:
            return "apply_effects MUTATED its input store"
        if len(after["records"]) != len(store["records"]):
            return "a record disappeared — supersede-never-erase violated"
        old_hist = list(store.get("history", ()))
        if after["history"][:len(old_hist)] != old_hist:
            return "history is not append-only"
        if len(after["history"]) != len(old_hist) + len(stmt["effects"]):
            return "an effect left no superseded value in history"
        for rec in after["records"]:
            if rec["active"] and rec.get("retired_reason") is not None:
                return "an active record kept a retirement reason"
        return None

    if kind == "effect_verbs":
        got = sorted(EFFECT_VERBS)
        if got != sorted(expect):
            return f"verb vocabulary drifted: {got}"
        banned = {"delete", "erase", "edit", "update", "purge"}
        if banned & EFFECT_VERBS:
            return "the effect vocabulary contains an ERASING verb (C3)"
        return None

    return f"unknown vector kind {kind!r}"


def run(vectors_path=None):
    vectors = json.loads((vectors_path or HERE / "vectors.json").read_text())
    failures = []
    seen = set()
    for v in vectors:
        if v["name"] in seen:
            failures.append((v["name"], "DUPLICATE vector name"))
        seen.add(v["name"])
        try:
            why = _run_one(v)
        except AssertionError as e:                      # pragma: no cover
            why = f"assertion: {e}"
        except (RevocationError, KeyError, TypeError) as e:
            why = f"unexpected {type(e).__name__}: {e}"
        if why is not None:
            failures.append((v["name"], why))
    return len(vectors), failures


if __name__ == "__main__":
    total, failed = run()
    for name, why in failed:
        print(f"FAIL {name}: {why}")
    if failed:
        sys.exit(1)
    print(f"vector harness: {total}/{total} pass against "
          f"reference_revocation.py")
