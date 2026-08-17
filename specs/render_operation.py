#!/usr/bin/env python3
"""Generate 0022 §4e-i's construction block FROM the executable that runs it.

External round 5, R5-2 found the spec claiming its code block was "quoted
verbatim" from `store_concurrency_harness.revocation_operation` when the two
differed by test hooks, helper names and return shape. I withdrew the claim.

Withdrawing it was honest and insufficient: the reason the claim was worth
making is that a spec printing a construction the evidence does not run is
exactly the R3-1 defect, and prose cannot prevent it twice. R5-2 named the
honest form — "generating this block from the source" — so this does that.

NOTHING IS STRIPPED. The first draft of this generator removed the test hooks
to keep the block tidy, which recreates the finding one level down: a spec
showing a signature the executable does not have. The block is the source's
own text, hooks included, and the sentence above it says what they are.

`--check` fails when the spec and the source disagree, which is the property
"verbatim" was asserting without establishing.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "specs" / "evidence" / "0022" / "store_concurrency_harness.py"
SPEC = ROOT / "specs" / "0022-source-revocation.md"
BEGIN = "<!-- GENERATED:r19-operation -->"
END = "<!-- /GENERATED:r19-operation -->"

# NO STRIPPING. The first draft of this generator removed the `_gate`/`_fault`
# parameters to keep the spec's block tidy — and that RECREATES THE FINDING:
# a spec showing a function whose signature differs from the executable's, with
# a docstring still referencing parameters the reader cannot see. "Verbatim"
# becomes true by SHOWING THE SOURCE, not by tidying it and asserting the
# resemblance. The two hooks are named in the sentence above the block; they
# are `None` in every non-test call, which the docstring already says.


def render() -> str:
    tree = ast.parse(SOURCE.read_text())
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == "revocation_operation")
    body = ast.get_source_segment(SOURCE.read_text(), fn)
    return (f"{BEGIN}\n"
            f"*GENERATED from `specs/evidence/0022/store_concurrency_harness.py` "
            f"by `specs/render_operation.py` — BYTE-FOR-BYTE, nothing "
            f"stripped or reformatted, because the finding this closes (R5-2) "
            f"was a spec block that differed from the executable it claimed to "
            f"quote. `_gate` and `_fault` are TEST HOOKS, `None` in every "
            f"non-test call; they appear here because they appear in the code, "
            f"and hiding them would reintroduce exactly the divergence.*\n\n"
            f"```python\n{body}\n```\n{END}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = SPEC.read_text()
    block = render()
    if BEGIN not in text:
        print(f"{SPEC.name} carries no {BEGIN} marker", file=sys.stderr)
        return 1
    new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, text, flags=re.S)
    if a.write:
        SPEC.write_text(new)
        print("R19 operation block written")
        return 0
    if new != text:
        print("the R19 operation block in 0022 §4e-i DISAGREES with the "
              "executable it claims to show — run "
              "`python3 specs/render_operation.py --write`", file=sys.stderr)
        return 1
    print("the R19 operation block matches its source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
