"""specs/0019 §7b — the STRICT carrier verification (R3-5, shipped executable).

Runs inside the repo or an extracted review package. Verifies mechanically:
(1) the 0014 rider exists exactly once in §7b with the N-ary transform;
(2) Rider B's fifteen-row table enumerates EXACTLY the outcome labels of
    0018's literal §4e table (label-set equality AND 15 = 15 row counts);
(3) Rider A's receipt-version tetrad {1,2,3,4} and the D2 on-sight rule;
(4) the spec's Spec-Requires line parses (with the repo gate's own regex
    when available) to exactly {0005, 0008, 0014, 0016, 0018}.

Exit 0 with a report on stdout; exit 1 naming the first failure. The seal
runs this and ships its output as `rider_verification_output.txt` beside it.
"""

from __future__ import annotations

import pathlib
import re
import sys


def main() -> int:
    here = pathlib.Path(__file__).resolve()
    root = here.parents[3]                    # <root>/specs/evidence/0019/
    spec = (root / "specs" / "0019-ungrounded-flag.md").read_text()
    src_0018 = (root / "specs" /
                "0018-release-migration-orchestrator.md").read_text()
    report: list[str] = []

    # (1) the 0014 rider, once, N-ary
    n = spec.count("Amended by 0019 (same-commit with 0019's acceptance):")
    if n != 1:
        print(f"FAIL: the 0014 rider appears {n} times (must be exactly 1)")
        return 1
    if "N-ary OR over `{the raw incoming} ∪ {every absorbed contributor}`" \
            not in spec:
        print("FAIL: the 0014 rider's transform is not the N-ary form")
        return 1
    report.append("0014 rider: present exactly once, N-ary transform")

    # (2) Rider B vs the 0018 literal table
    tbl = src_0018[src_0018.index("**Preflight rows**"):
                   src_0018.index("**Delegated rows**")]
    source_labels = re.findall(r"^\| `([a-z-]+)`", tbl, re.M)
    b2 = spec[spec.index("(B2) §4e, THE LITERAL TABLE"):spec.index("(B3) I13")]
    state_words = {"destination", "source", "missing", "unaccepted", "unknown"}
    rider_labels = [l for l in re.findall(r"`([a-z][a-z-]+)`", b2)
                    if l not in state_words and l != "TerminalFacts"]
    if sorted(set(source_labels)) != sorted(set(rider_labels)):
        print(f"FAIL: label sets differ\n  source: {sorted(set(source_labels))}"
              f"\n  rider:  {sorted(set(rider_labels))}")
        return 1
    rows = b2.count("(False, False,") + b2.count("(True, True,")
    if rows != 15 or len(source_labels) != 15:
        print(f"FAIL: row counts differ (source {len(source_labels)}, "
              f"rider {rows}; both must be 15)")
        return 1
    report.append(f"Rider B: 15 rows = 15 rows; "
                  f"{len(set(source_labels))} labels match exactly")

    # (3) Rider A tetrad + the era rule
    for needle in ("1 = legacy", "2 = 0014-era", "3 = 0019-era", "4 = post-D2",
                   "version < 4 refuses UNCONDITIONALLY ON SIGHT"):
        if needle not in spec:
            print(f"FAIL: Rider A missing {needle!r}")
            return 1
    report.append("Rider A: version tetrad {1,2,3,4} + the D2 on-sight rule")

    # (4) Spec-Requires, with the gate's own regex when present
    pattern = r"^Spec-Requires:\s*([0-9, ]+)$"
    gate = root / "specs" / "check_spec_reference.py"
    if gate.is_file():
        m = re.search(r'_REQUIRES = re\.compile\(r"(.+?)", re\.M\)',
                      gate.read_text())
        if m:
            pattern = m.group(1)
    found = re.compile(pattern, re.M).findall(spec)
    deps = {d.strip() for d in found[0].split(",")} if found else set()
    if deps != {"0005", "0008", "0014", "0016", "0018"}:
        print(f"FAIL: Spec-Requires parsed to {sorted(deps)}")
        return 1
    report.append(f"Spec-Requires: {sorted(deps)}")

    print("rider verification: ALL CHECKS PASS")
    for line in report:
        print(" -", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
