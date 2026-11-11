#!/usr/bin/env python3
# Mutation-Matrix: tests/test_offline_two_phase.py::test_the_check_refuses_each_broken_run
"""The offline launcher's two-phase split: which files run single-process, and whether the two phases ran the suite.

The owner approved the split (2026-11-08): the single-process run took 110m52s at 0.31.0. Phase 1 runs everything but the
phase-2 files under pytest-xdist. Phase 2 runs the phase-2 files in ONE process: every tests/ file that refuses an xdist
worker, by the gate's own mark, plus the seam-model drivers, which register the executions that gate verifies
(JOINT-TEST-GROUPS.md, G1). This is the rule .github/ci_shard.py and the local two-phase suite use.

    python two_phase.py files <tests dir>
        the phase-2 files, one per line, relative to the tests dir's parent
    python two_phase.py check <collect.txt> <phase1.xml> <phase2.xml> [--merge OUT.xml] [--lines P1 P2] [--tests DIR]
        exit 0 only if the two junits ran exactly the collected node ids, each once, with no failure or error. --merge
        writes one junit with both phases' <testsuite> elements; --lines names each phase's raw pytest output, whose
        summary counts must equal its junit's; --tests makes the split checked (phase 2 ran exactly the phase-2 files).
        The last line printed is the suite's: its counts come from the junits.

A collected id maps to its junit (classname, name) the way pytest's junit writer forms them: the path without `.py`, dots
for slashes, a class joined on, and the name with its parameter brackets kept whole. That mapping is checked to be
one-to-one over the collection before anything is compared, so two ids that share a junit key refuse rather than merge.
"""
from __future__ import annotations

import collections
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

SEAM_MARK = 'PYTEST_XDIST_WORKER") is None'
_SUMMARY = re.compile(r"(\d+) (passed|failed|skipped|errors?|xfailed|xpassed|deselected)")


def test_modules(tests: pathlib.Path) -> list:
    """Every test module, sorted, as `tests/...py`: pytest's default python_files (test_*.py and *_test.py; pyproject sets
    no override), subdirectories included, as ci_shard (research's L5). One enumeration for phase 2 and module skips."""
    return sorted(x.relative_to(tests.parent).as_posix() for x in tests.rglob("*.py")
                  if x.name.startswith("test_") or x.name.endswith("_test.py"))


def phase2_files(tests: pathlib.Path) -> list:
    """The files phase 2 runs, sorted: the mark's carriers and every seam-model driver."""
    out = set()
    for rel in test_modules(tests):
        p = tests.parent / rel
        if p.name.startswith("test_seam_model_") or SEAM_MARK in p.read_text(encoding="utf-8"):
            out.add(rel)
    return sorted(out)


def g1_members(doc_text: str) -> list:
    """G1's members as JOINT-TEST-GROUPS.md names them: every backticked tests/ path on the G1 table's members row."""
    sect = doc_text.split("## G1", 1)[1].split("\n## ", 1)[0]
    row = next((line for line in sect.splitlines() if line.startswith("| members |")), "")
    return sorted(set(re.findall(r"`(tests/[^`]+\.py)`", row)))


# pytest options that take their value as the NEXT argument; a value is never read as a path (research's L4)
VALUED = {"-k", "-m", "-p", "-W", "-o", "-c", "-r", "-n", "--deselect", "--ignore", "--ignore-glob", "--maxfail", "--tb",
          "--durations", "--durations-min", "--rootdir", "--confcutdir", "--override-ini", "--color", "--capture",
          "--import-mode", "--log-level", "--log-file", "--log-file-level", "--log-format", "--log-date-format",
          "--log-cli-level", "--junit-prefix", "--pythonwarnings", "--dist", "--maxprocesses", "--numprocesses", "--tx",
          "--max-worker-restart"}


def positionals(args: list) -> list:
    """The arguments pytest would read as paths or node ids: every argument that is neither an option nor the value of an
    option in VALUED. Two-phase mode refuses them, because each would be run by both phases."""
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-"):
            skip = a in VALUED
        else:
            out.append(a)
    return out


def junit_key(nodeid: str) -> tuple:
    base, br, rest = nodeid.partition("[")
    parts = base.split("::")
    path = parts[0][:-3] if parts[0].endswith(".py") else parts[0]
    return ".".join([path.replace("/", "."), *parts[1:-1]]), parts[-1] + br + rest


def collected(collect_text: str) -> list:
    """The node ids of a `--collect-only -q` output: its first block, up to the first blank line, each an id."""
    lines = collect_text.splitlines()
    block = lines[:lines.index("")] if "" in lines else lines
    if not block or block == [""]:
        raise ValueError("the selection collected no tests, so nothing ran; an empty run is refused, never counted as a pass")
    bad = [line for line in block if "::" not in line]
    if bad:
        raise ValueError(f"the collect output's first block is not a node-id list ({len(block)} lines, {len(bad)} without ::)")
    # pytest prints "N tests collected" whole, and "N/M tests collected (K deselected)" under -k or -m (research's L1)
    tail = [m for m in (re.match(r"^(\d+)(?:/(\d+))? tests? collected(?: \((\d+) deselected\))?", line) for line in lines) if m]
    if not tail or int(tail[-1].group(1)) != len(block):
        raise ValueError(f"the collect summary {[t.group(0) for t in tail[-1:]]} does not count its {len(block)} listed ids")
    n, total, desel = (int(x) if x is not None else None for x in tail[-1].groups())
    if (total is None) != (desel is None) or (total is not None and total - n != desel):
        raise ValueError(f"the collect summary {tail[-1].group(0)!r} does not add up: {total} collected less {desel} "
                         f"deselected is not the {n} listed")
    return block


def cases(xml_bytes: bytes) -> tuple:
    keys, kinds = collections.Counter(), collections.Counter()
    for tc in ET.fromstring(xml_bytes).iter("testcase"):
        keys[(tc.get("classname"), tc.get("name"))] += 1
        sk = tc.find("skipped")
        kind = ("failed" if tc.find("failure") is not None else "error" if tc.find("error") is not None
                else ("xfailed" if sk.get("type") == "pytest.xfail" else "skipped") if sk is not None else "passed")
        kinds[kind] += 1
    return keys, kinds


def module_skips(xml_bytes: bytes) -> list:
    """The modules skipped at COLLECTION (a module-level `importorskip` or `skip`): pytest's junit writes each as ONE testcase
    with an EMPTY classname, the module's dotted path as its name, and a <skipped> child only; `--collect-only` lists none
    of its nodes. Found at the shipped-changes round-2 pin: on a host without the `mcp` extra, 0053's adapter suite skips
    whole, and the comparison read that one entry as a node that ran uncollected, refusing a green run.

    `check` accounts for such an entry only when its module is one of the run's own test modules (`test_modules`) and none
    of that module's nodes was collected; with no module set given it accounts for none (fail closed). A second
    cross-check, the module skips equal to those the collection itself reports, needs `-rs` on the collection command:
    `--collect-only -q` alone prints no skip (pytest 9.2.0), and `-rs` prints one "SKIPPED [1] tests/<file>.py:<line>"
    line per module skipped at collection."""
    return [tc.get("name") for tc in ET.fromstring(xml_bytes).iter("testcase")
            if not tc.get("classname") and [c.tag for c in tc] == ["skipped"]]


def summary_counts(output: str) -> dict:
    lines = [line for line in output.splitlines() if re.search(r"\b(passed|failed|error|errors|no tests ran)\b", line)]
    got = {k: int(n) for n, k in _SUMMARY.findall(lines[-1] if lines else "")}
    if "error" in got:
        got["errors"] = got.pop("error")
    return got


def _module(classname: str) -> str:
    """The module a junit classname belongs to, as `tests/test_x.py`: the classname up to its first capitalised segment."""
    parts = (classname or "").split(".")
    keep = [x for x in parts if not x[:1].isupper()] if parts else []
    return "/".join(keep) + ".py"


def check(collect_text: str, p1: bytes, p2: bytes, lines=None, phase2=None, rcs=None, modules=None) -> tuple:
    """(problems, totals). Every refusal is a problem string; totals are the suite's counts from the two junits. `phase2`, the
    phase-2 files, makes the split itself checked: phase 2 ran exactly those files' nodes and phase 1 none of them."""
    problems = []
    (k1, n1), (k2, n2) = cases(p1), cases(p2)          # counted first: a refused run's line still says what ran (L2)
    try:
        ids = collected(collect_text)
    except ValueError as e:
        return [str(e)], n1 + n2
    want = collections.Counter(junit_key(n) for n in ids)
    if sum(want.values()) != len(set(want)):
        problems.append(f"{sum(want.values()) - len(set(want))} collected ids share a junit key: the comparison would merge them")
    ran = k1 + k2
    twice = sorted(k for k, n in ran.items() if n > 1)
    if twice:
        problems.append(f"{len(twice)} node(s) ran more than once (in both phases, or twice in one): {twice[:3]}")
    missing, extra = want - ran, ran - want
    # a module skipped at collection is accounted for, not "uncollected", only when none of its nodes was collected
    have = {n.split("::")[0] for n in ids}
    for name in module_skips(p1) + module_skips(p2):
        path = name.replace(".", "/") + ".py"
        if path in have:
            problems.append(f"{path} is reported skipped at collection, yet {sum(1 for n in ids if n.split('::')[0] == path)} "
                            f"of its node(s) were collected")
        elif modules is not None and path in set(modules):
            extra.pop(("", name), None)
    if missing:
        problems.append(f"{sum(missing.values())} collected node(s) ran in neither phase: {sorted(missing)[:3]}")
    if extra:
        problems.append(f"{sum(extra.values())} node(s) ran that were not collected: {sorted(extra)[:3]}")
    if phase2 is not None:
        p2set = set(phase2)
        in1 = sorted({_module(c) for c, _n in k1} & p2set)
        out2 = sorted({_module(c) for c, _n in k2} - p2set)
        if in1:
            problems.append(f"phase 1 ran a phase-2 file under workers, splitting its joint group: {in1}")
        if out2:
            problems.append(f"phase 2 ran file(s) outside the phase-2 set: {out2}")
    if rcs is not None:
        p2set = set(phase2 or ())
        sizes = (sum(1 for n in ids if n.split("::")[0] not in p2set), sum(1 for n in ids if n.split("::")[0] in p2set))
        for label, rc, size in (("phase 1", rcs[0], sizes[0]), ("phase 2", rcs[1], sizes[1])):
            if rc == 5 and size:
                problems.append(f"{label} exited 5 (no tests ran) while the collection gives it {size} node(s)")
            elif rc not in (0, 5):
                problems.append(f"{label} exited {rc}")
    for label, n in (("phase 1", n1), ("phase 2", n2)):
        if n["failed"] or n["error"]:
            problems.append(f"{label}: {n['failed']} failed, {n['error']} errors")
    if lines is not None:
        for label, text, n in (("phase 1", lines[0], n1), ("phase 2", lines[1], n2)):
            got = summary_counts(text)
            got["passed"] = got.get("passed", 0) + got.get("xpassed", 0)        # a non-strict xpass is a passed testcase
            mine = {"passed": n["passed"], "skipped": n["skipped"], "failed": n["failed"], "errors": n["error"],
                    "xfailed": n["xfailed"]}
            if any(got.get(k, 0) != v for k, v in mine.items()):
                problems.append(f"{label}: its pytest summary {got} disagrees with its junit {mine}")
    return problems, n1 + n2


def merge(p1: bytes, p2: bytes) -> bytes:
    root = ET.Element("testsuites")
    for raw in (p1, p2):
        r = ET.fromstring(raw)
        for s in ([r] if r.tag == "testsuite" else list(r.iter("testsuite"))):
            root.append(s)                                  # verbatim: phase 1's testsuite(s), then phase 2's
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def suite_line(t, wall=None) -> str:
    """pytest's count grammar: only the kinds present, in pytest's order and words, from the junits."""
    parts = [f"{t[k]} {w}" for k, w in (("failed", "failed"), ("passed", "passed"), ("skipped", "skipped"),
                                          ("xfailed", "xfailed"), ("xpassed", "xpassed")) if t.get(k)]
    if t.get("error"):
        parts.append(f"{t['error']} error" + ("s" if t["error"] > 1 else ""))
    head = ", ".join(parts) if parts else "no tests ran"
    return head + (f" in {wall:.2f}s" if wall is not None else "")


def _last_line(text: str) -> str:
    lines = [line.strip(" =") for line in text.splitlines() if re.search(r"\b(passed|failed|deselected|no tests ran)\b", line)]
    return lines[-1] if lines else "(no summary)"


def main(argv) -> int:
    if argv[:1] == ["positionals"]:
        bad = positionals(argv[1:])
        if bad:
            print(f"two-phase mode takes no path or node id ({bad}): pass -k, or set VERACIUM_OFFLINE_MODE=single",
                  file=sys.stderr)
            return 2
        return 0
    if len(argv) >= 2 and argv[0] == "files":
        tests = pathlib.Path(argv[1])
        mine = phase2_files(tests)
        g1 = g1_members((pathlib.Path(__file__).resolve().parent / "JOINT-TEST-GROUPS.md").read_text(encoding="utf-8"))
        if not mine or mine != g1:
            print(f"REFUSED: the phase-2 rule finds {mine}, and JOINT-TEST-GROUPS.md's G1 names {g1}: they must be equal "
                  f"and non-empty, or a narrowed matcher shrinks the one-process phase silently", file=sys.stderr)
            return 1
        print("\n".join(mine))
        return 0
    if len(argv) >= 4 and argv[0] == "check":
        collect_path, a, b = (pathlib.Path(x) for x in argv[1:4])
        rest = argv[4:]
        out = pathlib.Path(rest[rest.index("--merge") + 1]) if "--merge" in rest else None
        texts = None
        if "--lines" in rest:
            i = rest.index("--lines")
            texts = [pathlib.Path(rest[i + 1]).read_text(encoding="utf-8", errors="replace"),
                     pathlib.Path(rest[i + 2]).read_text(encoding="utf-8", errors="replace")]
        p2files = phase2_files(pathlib.Path(rest[rest.index("--tests") + 1])) if "--tests" in rest else None
        rcs = (int(rest[rest.index("--rc") + 1]), int(rest[rest.index("--rc") + 2])) if "--rc" in rest else None
        wall = float(rest[rest.index("--wall") + 1]) if "--wall" in rest else None
        p1, p2 = a.read_bytes(), b.read_bytes()
        mods = test_modules(pathlib.Path(rest[rest.index("--tests") + 1])) if "--tests" in rest else None
        problems, t = check(collect_path.read_text(encoding="utf-8"), p1, p2, texts, p2files, rcs, mods)
        if out is not None:
            out.write_bytes(merge(p1, p2))
        for p in problems:
            print(f"TWO-PHASE REFUSED: {p}")
        phases = f"phase 1 {_last_line(texts[0])}; phase 2 {_last_line(texts[1])}" if texts else "phase lines not given"
        tail = f" (the launcher's wall time; two phases, counted from their junits: {phases})" if wall is not None else \
            f" (two phases, counted from their junits: {phases})"
        print(suite_line(t, wall) + tail)
        return 1 if problems else 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
