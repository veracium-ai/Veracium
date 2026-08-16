#!/usr/bin/env python3
"""Generate and verify the PUBLIC READ-SURFACE manifest for specs/0020 §4f.

The §4f inventory was written by hand. A hand-written inventory of read
surfaces is exactly what a newly added read path escapes silently — and a
read path that escapes the inventory escapes the principal boundary, which
is the whole feature. So the ENUMERATION is mechanical (the AST of the
public surface, the `specs/audit_manifest.py` pattern) and the VERDICTS
live in `specs/read_surface_dispositions.py`.

What is enumerated, and how:

- every PUBLIC method of `class Memory` in `src/veracium/__init__.py`
  (name not starting with `_`), parsed from the AST;
- every PUBLIC `*_impl` function in `src/veracium/mcp_server.py` — the MCP
  tool implementations, which are the same values over MCP.

For each surface the parser records whether the signature carries a
`principal` parameter. `--check` then enforces, mechanically:

1. the enumerated set and the dispositioned set are EQUAL (a new public
   surface is un-dispositioned and FAILS; a deleted one is stale and FAILS);
2. `principal="threaded"` iff the parsed signature HAS a `principal`
   parameter — in BOTH directions, so a row can neither claim a threading
   the code does not do nor hide one it does;
3. every `returns_records=True` surface is either principal-threaded or
   carries a disposition naming it an operator surface — an omission
   cannot masquerade as a decision.

  --write   regenerate specs/generated/0020-read-surfaces.md
  --check   fail if the code and the dispositions disagree (0020 V12)
  (none)    print what was found
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
MANIFEST = ROOT / "specs" / "generated" / "0020-read-surfaces.md"

#: (module file, how to enumerate). The MEMORY class is the library surface;
#: mcp_server's `*_impl` functions are the MCP surface (§4f row 5).
SOURCES = (("__init__.py", "Memory"), ("mcp_server.py", None))

#: a disposition may only ever say one of these about the principal
PRINCIPAL_STATES = ("threaded", "none")

#: the word that must name an operator decision, so an omission cannot pass
#: as one (rule 3)
OPERATOR_MARKER = "UNSCOPED"


def _params(fn: ast.FunctionDef) -> list[str]:
    a = fn.args
    return [p.arg for p in (list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs))]


def enumerate_surfaces(source: str, module: str,
                       class_name: str | None) -> dict[str, dict]:
    """The mechanical enumeration, over SOURCE TEXT (so the totality check
    can be exercised against a synthetic module — 0020 V12's adversarial
    half — without touching the tree)."""
    tree = ast.parse(source)
    out: dict[str, dict] = {}

    def _add(fn, qual):
        out[qual] = {
            "module": module,
            "lineno": fn.lineno,
            "has_principal": "principal" in _params(fn),
            "returns": (ast.unparse(fn.returns) if fn.returns is not None
                        else ""),
        }

    for node in tree.body:
        if class_name is not None:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for sub in node.body:
                    if (isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and not sub.name.startswith("_")):
                        _add(sub, f"{class_name}.{sub.name}")
        elif (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
              and not node.name.startswith("_")
              and node.name.endswith("_impl")):
            _add(node, f"{module}.{node.name}")
    return out


def surfaces() -> dict[str, dict]:
    found: dict[str, dict] = {}
    for filename, class_name in SOURCES:
        module = filename[:-3]
        found.update(enumerate_surfaces((SRC / filename).read_text(),
                                        module, class_name))
    return found


def problems(found: dict[str, dict], dispositions: dict[str, dict]) -> list[str]:
    """The three mechanical rules. Returns a list of human-readable
    failures; empty means the code and the verdicts agree."""
    bad: list[str] = []
    for name in sorted(set(found) - set(dispositions)):
        bad.append(
            f"UN-DISPOSITIONED read surface: {name} — a new public surface "
            f"appeared with no 0020 §4f ruling. Give it one in "
            f"specs/read_surface_dispositions.py (is it scoped, or an "
            f"operator surface by decision?).")
    for name in sorted(set(dispositions) - set(found)):
        bad.append(
            f"STALE disposition: {name} — no such public surface exists any "
            f"more; remove the row.")
    for name in sorted(set(found) & set(dispositions)):
        d, f = dispositions[name], found[name]
        if d.get("principal") not in PRINCIPAL_STATES:
            bad.append(f"{name}: principal must be one of {PRINCIPAL_STATES}")
            continue
        threaded = d["principal"] == "threaded"
        if threaded and not f["has_principal"]:
            bad.append(
                f"{name}: dispositioned `principal=threaded` but the signature "
                f"has NO `principal` parameter — the row claims a threading "
                f"the code does not do.")
        if not threaded and f["has_principal"]:
            bad.append(
                f"{name}: the signature HAS a `principal` parameter but the "
                f"row says `none` — either thread it into the visibility "
                f"relation and say so, or remove the parameter.")
        if d.get("returns_records") and not threaded \
                and OPERATOR_MARKER not in d.get("disposition", ""):
            bad.append(
                f"{name}: returns RECORDS, takes no principal, and its "
                f"disposition does not name it {OPERATOR_MARKER} by decision "
                f"— an omission must not read as a decision (§2's operator "
                f"row).")
    return bad


HEADER = """<!-- GENERATED by specs/read_surfaces.py — do not hand-edit.
     Verdicts live in specs/read_surface_dispositions.py.
     Regenerate: python3 specs/read_surfaces.py --write
     Verify:     python3 specs/read_surfaces.py --check -->

# specs/0020 §4f — public read-surface manifest

**{n} public surfaces** — every public method of `Memory` plus every public
`*_impl` in `mcp_server` — enumerated by **parsing the AST**, not by reading
the spec's prose inventory. **{records} of them return record objects.**

The §4f inventory is a claim about COMPLETENESS, and completeness written by
hand is the thing that silently rots: a read path added next quarter would
join no table and cross no boundary. `test_read_surface_manifest_is_total`
(0020 V12) fails when this file and the code disagree.

**Three rules are enforced mechanically**, beyond the enumeration itself:
the dispositioned set must EQUAL the enumerated set; `principal: threaded`
must agree with the parsed signature IN BOTH DIRECTIONS (a row cannot claim
a threading the code does not do, nor hide one it does); and a surface that
returns records without a principal must be dispositioned **UNSCOPED** in
words — so an omission cannot pass itself off as a decision.

**Stated limits.** The enumeration is mechanical; `returns_records`, the
carrier column and the disposition text are **reviewed judgement**. This
covers the LIBRARY's public surface: a host reaching around it into
`Store` (or into `veracium.proactive` / `veracium.graph` directly) is
outside the boundary by construction — those are not public read surfaces,
and 0020's claim is about the surfaces named here.

| surface | records? | principal | carriers | disposition |
|---|---|---|---|---|
"""


def render(found: dict[str, dict], dispositions: dict[str, dict]) -> str:
    rows = []
    n_records = 0
    for name in sorted(found):
        d = dispositions.get(name, {})
        rec = "**yes**" if d.get("returns_records") else "no"
        n_records += 1 if d.get("returns_records") else 0
        pr = ("`principal=` **threaded**" if d.get("principal") == "threaded"
              else "none")
        rows.append(f"| `{name}` | {rec} | {pr} | {d.get('carriers', '')} | "
                    f"{d.get('disposition', '')} |")
    return (HEADER.format(n=len(found), records=n_records) + "\n".join(rows)
            + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    sys.path.insert(0, str(ROOT / "specs"))
    from read_surface_dispositions import DISPOSITIONS

    found = surfaces()
    bad = problems(found, DISPOSITIONS)
    if args.check:
        if bad:
            print("\n".join(bad))
            return 1
        want = render(found, DISPOSITIONS)
        if not MANIFEST.exists() or MANIFEST.read_text() != want:
            print("manifest is stale — regenerate with "
                  "`python3 specs/read_surfaces.py --write`")
            return 1
        return 0
    if args.write:
        if bad:
            print("\n".join(bad))
            return 1
        MANIFEST.write_text(render(found, DISPOSITIONS))
        print(f"wrote {MANIFEST.relative_to(ROOT)}: {len(found)} surfaces")
        return 0
    for name in sorted(found):
        f = found[name]
        print(f"{name:34s} principal={f['has_principal']!s:5s} "
              f"-> {f['returns'] or '(unannotated)'}")
    if bad:
        print("\n" + "\n".join(bad))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
