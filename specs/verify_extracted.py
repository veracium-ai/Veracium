#!/usr/bin/env python3
"""The extraction verifiers, as NAMED SCRIPTS rather than inline `-c` programs.

External round 11, R11-1. The registry's two verifier entries were
`python -c "<program>"`, and the binding regression checked that the program
CONTAINED the strings `verify_collected` and `COLLECTED`. The reviewer
substituted:

    python -c "pass # verify_collected COLLECTED"

kept the label, and both the binding test and `verify_archive()` accepted the
archive. Substring inspection of a source string is not a binding to
behaviour — it is a binding to spelling, which is what round 10's finding said
about labels one level up.

Named scripts fix the shape: the registry pins a complete argv ending in a
FILE, that file's behaviour is fixed by its own source, and the adversarial
test corrupts the packaged carrier and requires the extraction to refuse.

Each verb reads the carriers as they exist IN THE EXTRACTION and exits
non-zero with a reason.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def _carriers():
    collected = ROOT / "COLLECTED.txt"
    rs = ROOT / "COLLECTED_pytest_rs.txt"
    for p in (collected, rs):
        if not p.exists():
            print(f"{p.name} is not in the extraction", file=sys.stderr)
            raise SystemExit(2)
    return collected.read_text(), rs.read_text()


def verify_collected_carrier() -> int:
    sys.path.insert(0, str(HERE))
    from skip_inventory import verify_collected
    collected, rs = _carriers()
    try:
        verify_collected(collected, rs)
    except Exception as e:                       # noqa: BLE001 — the reason matters
        print(f"verify_collected FAILED: {e}", file=sys.stderr)
        return 1
    print("verify_collected: PASS")
    return 0


def reconcile_carrier() -> int:
    sys.path.insert(0, str(HERE))
    from skip_inventory import reconcile
    _collected, rs = _carriers()
    problems = reconcile(rs)
    if problems:
        print("reconcile FAILED:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print("reconcile: PASS")
    return 0


def header_carrier() -> int:
    """C-plus (COLLECTED_HEADER_DESIGN §5): the record conforms to the
    code-owned policy registry, the template is digest-bound, COLLECTED.txt
    is byte-identical to the recomputed whole-file construction, and every
    field's required witness holds against the carriers IN THE EXTRACTION."""
    sys.path.insert(0, str(HERE))
    import hashlib
    import json

    import collected_record as CR
    import collected_render as CX

    rec_path = ROOT / CR.RECORD_CARRIER
    if not rec_path.exists():
        print(f"{CR.RECORD_CARRIER} is not in the extraction", file=sys.stderr)
        raise SystemExit(2)
    try:
        record = json.loads(rec_path.read_text())
    except ValueError as e:
        print(f"the record does not parse: {e}", file=sys.stderr)
        return 1

    problems = CR.validate_record(record)
    if not problems:
        texts = {}
        for which in ("header", "manifest"):
            tpl_rel = record["templates"][which]["path"]
            tpl_path = (ROOT / tpl_rel).resolve()
            if ROOT.resolve() not in tpl_path.parents:
                problems.append(f"the {which} template path {tpl_rel!r} "
                                f"escapes the extraction")
            elif not tpl_path.exists():
                problems.append(f"the named {which} template {tpl_rel!r} is "
                                f"not in the extraction")
            else:
                tpl_bytes = tpl_path.read_bytes()
                if hashlib.sha256(tpl_bytes).hexdigest() \
                        != record["templates"][which]["sha256"]:
                    problems.append(f"the {which} template {tpl_rel!r} does "
                                    f"not match the record's digest")
                else:
                    texts[which] = tpl_bytes.decode()
        if not problems:
            collected, rs = _carriers()
            problems += CX.whole_file_problems(
                collected, record, texts["header"], rs)
            # F2: the manifest is the SAME kind of carrier — one whole-file
            # equation, no bytes unowned
            man_path = ROOT / "PACKAGE_MANIFEST.txt"
            if not man_path.exists():
                problems.append("PACKAGE_MANIFEST.txt is not in the "
                                "extraction")
            else:
                problems += CX.manifest_problems(
                    man_path.read_text(), record, texts["manifest"])
            problems += CR.witness_problems(record, ROOT)
    if problems:
        print("header verification FAILED:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    print("header: PASS (record conforms; COLLECTED.txt AND "
          "PACKAGE_MANIFEST.txt recompute byte-for-byte; witnesses hold)")
    return 0


VERBS = {
    "collected": verify_collected_carrier,
    "reconcile": reconcile_carrier,
    "header": header_carrier,
}


def main(argv) -> int:
    if len(argv) != 2 or argv[1] not in VERBS:
        print(f"usage: verify_extracted.py {{{'|'.join(VERBS)}}}", file=sys.stderr)
        return 2
    return VERBS[argv[1]]()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
