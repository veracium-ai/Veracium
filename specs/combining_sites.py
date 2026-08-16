#!/usr/bin/env python3
"""Generate and verify the COMBINING-SITE manifest for specs/0021 §3.

§3's operation matrix claims to be TOTAL — one row per combining operation.
External F4 is why that claim is not allowed to be prose: v2's matrix rested
on a reach assertion that was simply false about the shipped code, and a
hand-written inventory of "everything that combines records" is exactly what
the next merge path escapes silently. A combining path that escapes the matrix
escapes the scope rule, which is the whole feature.

So the ENUMERATION is mechanical (the AST of the store's SQL, the
`specs/read_surfaces.py` / `specs/audit_manifest.py` pattern) and the VERDICTS
live in `src/veracium/combining.py` — in the CODE, not under specs/, because
0014's `CONSUMPTION_SITES` precedent puts the registry where the writers are.

What is enumerated, and how: every string constant in
`src/veracium/store/sqlite.py` that is an `INSERT` / `UPDATE` / `DELETE`
statement, attributed to its enclosing function. The store owns every SQL
statement in the tree, so "the set of record-mutating code paths" and "the set
of write statements in the store" are the same set.

`--check` then enforces, mechanically:

1. every enumerated write site's enclosing function is REGISTERED (a new write
   path is un-dispositioned and FAILS);
2. every registered site still exists (a stale row FAILS);
3. every `combining=True` site names an operation from §3's matrix and carries
   a scope rule;
4. every operation in §3's matrix marked `combining` is claimed by at least
   one registered site, and every one marked `non-combining` is claimed by
   NONE — so "reinforcement mutates nothing" and "expiry combines nothing"
   are claims this check makes falsifiable in both directions.

  --write   regenerate specs/generated/0021-combining-sites.md
  --check   fail if the code and the registry disagree (0021 W3)
  (none)    print what was found
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
MANIFEST = ROOT / "specs" / "generated" / "0021-combining-sites.md"

#: the module whose SQL is the complete set of record mutations. Every other
#: module reaches persistence THROUGH it, so enumerating it enumerates them.
SOURCES = ("store/sqlite.py",)

_STMT = re.compile(
    r"\b(INSERT\s+(?:OR\s+\w+\s+)?INTO|UPDATE|DELETE\s+FROM)\s+([\w{}]+)",
    re.I | re.S)


def enumerate_write_sites(source: str, module: str) -> dict:
    """`{(module, function): sorted[(verb, table)]}` — every SQL write
    statement in `source`, attributed to its enclosing function.

    Takes SOURCE TEXT so the totality check can be exercised against a
    synthetic module (0021 W3's adversarial half) without touching the tree."""
    tree = ast.parse(source)
    out: dict = {}
    parents: dict = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node

    def enclosing(node):
        cur = parents.get(node)
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return cur.name
            cur = parents.get(cur)
        return "<module>"

    for node in ast.walk(tree):
        text = None
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        elif isinstance(node, ast.JoinedStr):
            text = "".join(v.value if isinstance(v, ast.Constant)
                           and isinstance(v.value, str) else "{}"
                           for v in node.values)
        if not text:
            continue
        hits = _STMT.findall(text)
        if not hits:
            continue
        key = (module, enclosing(node))
        got = out.setdefault(key, set())
        for verb, table in hits:
            got.add((re.sub(r"\s+", " ", verb.upper()), table))
    return {k: sorted(v) for k, v in out.items()}


def sites() -> dict:
    found: dict = {}
    for rel in SOURCES:
        found.update(enumerate_write_sites((SRC / rel).read_text(),
                                           f"src/veracium/{rel}"))
    return found


def problems(found: dict, registry: dict, operations: dict) -> list[str]:
    """The four mechanical rules. Empty means the code and the registry
    agree."""
    bad: list[str] = []
    for key in sorted(set(found) - set(registry)):
        bad.append(
            f"UNREGISTERED write site: {key[0]}:{key[1]} writes "
            f"{found[key]} but appears in NO COMBINING_SITES row. specs/0021 "
            f"§3 claims the operation matrix is TOTAL — register it in "
            f"src/veracium/combining.py and say whether it COMBINES (writes a "
            f"record derived from, or mutates a record because of, MORE THAN "
            f"ONE existing record) and under which scope rule.")
    for key in sorted(set(registry) - set(found)):
        bad.append(
            f"STALE registry row: {key[0]}:{key[1]} — no such write site "
            f"exists any more; remove the row.")
    for key in sorted(set(found) & set(registry)):
        spec = registry[key]
        if not spec.combining:
            if spec.scope_rule:
                bad.append(f"{key[0]}:{key[1]}: combining=False but a scope "
                           f"rule is given — one of the two is wrong.")
            continue
        if not set(spec.operations) <= set(operations):
            bad.append(
                f"{key[0]}:{key[1]}: operations {spec.operations!r} are not all "
                f"rows of the §3 matrix {sorted(operations)}.")
        if not spec.scope_rule:
            bad.append(f"{key[0]}:{key[1]}: a COMBINING site with no scope "
                       f"rule — an omission must not read as a decision.")
    claimed = set()
    for k, s in registry.items():
        if s.combining and k in found:
            claimed.update(s.operations)
    for op, expectation in sorted(operations.items()):
        if expectation == "non-combining":
            if op in claimed:
                bad.append(
                    f"operation {op!r} is declared NON-COMBINING in the §3 "
                    f"matrix, yet a registered combining site claims it — "
                    f"the matrix row and the code disagree.")
        elif op not in claimed:
            bad.append(
                f"operation {op!r} is a §3 matrix row that NO registered "
                f"combining site claims — either the site is missing or the "
                f"row is fiction.")
    return bad


HEADER = """<!-- GENERATED by specs/combining_sites.py — do not hand-edit.
     The registry lives in src/veracium/combining.py.
     Regenerate: python3 specs/combining_sites.py --write
     Verify:     python3 specs/combining_sites.py --check -->

# specs/0021 §3 — combining-site manifest

**{n} record-mutating code paths**, enumerated by **parsing the store's SQL**
rather than by reading the spec's prose matrix. **{c} of them COMBINE**:
they write a record derived from, or mutate a record because of, MORE THAN
ONE existing record — the definition §3 gives the registry.

External F4 is the reason this is mechanical. v2's matrix rested on a reach
assertion that was false about the shipped code, and a hand-written inventory
of merge paths is what the next merge path escapes silently. A combining path
that escapes the matrix escapes the scope rule.
`test_scope_operation_matrix_is_total` (W3) fails when this file, the
registry, and the code disagree — and it is exercised against a synthetic
module carrying a NEW un-registered write, so the gate is known to bite.

**Stated limits.** The enumeration is mechanical; `combining`, the operation
attribution and the scope rule are **reviewed judgement**. It covers the SQL
in `src/veracium/store/sqlite.py`, which is where every persistence path in
the tree terminates; a host writing to the database behind the library is
outside the boundary by construction.

## §3 operations

| operation | expectation |
|---|---|
{ops}

## Sites

| module | function | writes | combines? | operation | scope rule |
|---|---|---|---|---|---|
"""


def render(found: dict, registry: dict, operations: dict) -> str:
    rows = []
    n_comb = 0
    for key in sorted(found):
        spec = registry.get(key)
        writes = " · ".join(f"`{v} {t}`" for v, t in found[key])
        comb = "**yes**" if spec and spec.combining else "no"
        n_comb += 1 if spec and spec.combining else 0
        rows.append(
            f"| `{key[0]}` | `{key[1]}` | {writes} | {comb} | "
            f"{(spec.operation if spec and spec.combining else '—')} | "
            f"{(spec.scope_rule if spec and spec.combining else spec.why if spec else '')} |")
    ops = "\n".join(f"| {op} | {exp} |" for op, exp in sorted(operations.items()))
    return (HEADER.format(n=len(found), c=n_comb, ops=ops)
            + "\n".join(rows) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(ROOT / "src"))
    from veracium.combining import COMBINING_SITES, OPERATIONS

    found = sites()
    bad = problems(found, COMBINING_SITES, OPERATIONS)
    if args.check:
        if bad:
            print("\n".join(bad))
            return 1
        want = render(found, COMBINING_SITES, OPERATIONS)
        if not MANIFEST.exists() or MANIFEST.read_text() != want:
            print("manifest is stale — regenerate with "
                  "`python3 specs/combining_sites.py --write`")
            return 1
        return 0
    if args.write:
        if bad:
            print("\n".join(bad))
            return 1
        MANIFEST.write_text(render(found, COMBINING_SITES, OPERATIONS))
        print(f"wrote {MANIFEST.relative_to(ROOT)}: {len(found)} sites")
        return 0
    for key in sorted(found):
        spec = COMBINING_SITES.get(key)
        print(f"{key[1]:44s} {'COMBINES' if spec and spec.combining else '        '} "
              f"{found[key]}")
    if bad:
        print("\n" + "\n".join(bad))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
