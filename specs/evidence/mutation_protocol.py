"""THE mutation-table protocol, with no subject in it (0007 I6, research's stage-1 Q1: one protocol, not two runners).

Factored out of specs/evidence/0013/sa10_mutants.py (INV-SA10, 0007 I2) so that 0007's INV-SA1–SA12 table
(specs/evidence/0007/sa_mutants.py) runs the SAME protocol. A subject supplies only data: its mutants, its controls,
the files it digests, the modules its import probe must load from the copy, and the files its cells live in.

The protocol, on a copy of the tracked tree (TMPDIR=/dev/shm recommended):
  CLEAN    every named cell and every honest probe passes on the unmutated copy, FIRST and again LAST (a campaign whose
           controls fail at either end measured nothing);
  per mutant: every anchor occurs EXACTLY ONCE in its file and the bytes change; the subject's modules still import
           from the copy; its HONEST probes pass (a kill only because the clean path broke is vacuous); its NAMED cells
           run under pytest with a JUnit record, each failing cell classified by specs/evidence/mutation_kinds.py;
           KILLED iff the classifier says so AND every named cell failed AND, where the row declares a REASON, that
           text is in a named cell's failure; the file is restored byte-identically.
  CONTROL  a negative control the classifier must read UNCLASSIFIED, never KILLED; or a NO-OP control (expected
           SURVIVED): an edit that changes the file's bytes and no behaviour, whose named cells must ALL pass, so a
           kill in that file is never merely "the file changed" (a digest-pinning cell would kill every mutant).
`problems()` is FAST and re-runs nothing: definitions, anchors, digests, the named cells' existence, every row good.

A mutant is (id, kind, file, [(anchor, replacement)], named cells, honest nodes, reason or None, what).
A control is (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give).
A cell or node is `<tests/file.py>::<test name>[params]`.
"""
from __future__ import annotations

import ast
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

ROOT = pathlib.Path(__file__).resolve().parents[2]
KINDS = "specs/evidence/mutation_kinds.py"
PROTOCOL = "specs/evidence/mutation_protocol.py"


def _load_kinds():
    spec = importlib.util.spec_from_file_location("veracium_mutation_kinds", ROOT / KINDS)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MK = _load_kinds()


def _strict_pairs(pairs):
    """Duplicate-key refusal (the name 0026's evidence-boundary gate knows as strict)."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


def definition_sha(m) -> str:
    return hashlib.sha256(json.dumps(list(m), ensure_ascii=True).encode()).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def render(table: dict) -> str:
    return json.dumps(table, indent=1, sort_keys=True, ensure_ascii=True) + "\n"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def junit_node(classname: str, name: str) -> str:
    """`tests.test_x[.Class]` + `name` → `tests/test_x.py[::Class]::name`."""
    parts = (classname or "").split(".")
    mod = next((i for i, p in enumerate(parts) if p.startswith("test_")), len(parts) - 1)
    return "::".join(["/".join(parts[:mod + 1]) + ".py", *parts[mod + 1:], name or ""])


def _noop_fired(row) -> bool:
    """A NO-OP control fired iff EVERY named cell ran and passed, and none failed or errored."""
    named = set(row.get("named_cells") or [])
    return (bool(named) and named <= set(row.get("cells_passed") or [])
            and not row.get("cells_failed") and not row.get("cells_errored"))


class Subject:
    def __init__(self, *, spec, finding, table, digested, mutants, controls, import_modules, import_specs,
                 cells_files, kinds):
        self.spec, self.finding, self.table = spec, finding, pathlib.Path(table)
        self.digested, self.mutants, self.controls = tuple(digested), list(mutants), list(controls)
        self.import_modules, self.import_specs = tuple(import_modules), tuple(import_specs)
        self.cells_files, self.kinds = tuple(cells_files), tuple(kinds)

    # ---- the definitions ---------------------------------------------------------------------------------------------
    def named_cells(self) -> list:
        return sorted({n for m in self.mutants for n in m[4]} | {n for k in self.controls for n in k[3]})

    def honest_nodes(self) -> list:
        return sorted({n for m in self.mutants for n in m[5]})

    def digests(self, root: pathlib.Path) -> dict:
        return {f: sha(root / f) for f in self.digested}

    # ---- the copy -------------------------------------------------------------------------------------------------------
    @staticmethod
    def snapshot(dst: pathlib.Path):
        r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           capture_output=True, check=True)
        for f in filter(None, r.stdout.decode().split("\0")):
            src = ROOT / f
            if src.is_file():
                (dst / f).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst / f)

    @staticmethod
    def env(root):
        return {**os.environ, "PYTHONPATH": str(root / "src"), "PYTHONDONTWRITEBYTECODE": "1"}

    def imports(self, root) -> str:
        code = ("import importlib, importlib.util, pathlib, sys\nroot = pathlib.Path(sys.argv[1]).resolve()\n"
                f"for name in {self.import_modules!r}:\n"
                "    m = importlib.import_module(name)\n"
                "    assert pathlib.Path(m.__file__).resolve().is_relative_to(root / 'src'), m.__file__\n"
                f"for rel in {self.import_specs!r}:\n"
                "    s = importlib.util.spec_from_file_location(pathlib.Path(rel).stem, root / rel)\n"
                "    s.loader.exec_module(importlib.util.module_from_spec(s))\n")
        r = subprocess.run([sys.executable, "-B", "-c", code, str(root)], cwd=root, env=self.env(root),
                           capture_output=True, text=True)
        return "ok" if r.returncode == 0 else "error: " + (r.stderr.strip().splitlines() or ["?"])[-1][:200]

    def pytest(self, root, nodes) -> dict:
        with tempfile.TemporaryDirectory() as d:
            xml = pathlib.Path(d) / "j.xml"
            r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:randomly", "-p",
                                "no:cacheprovider", f"--junitxml={xml}", *nodes], cwd=root, env=self.env(root),
                               capture_output=True, text=True)
            failed, errored, passed, kinds, texts = [], [], [], {}, {}
            if xml.exists():
                for tc in ET.parse(xml).iter("testcase"):
                    node = junit_node(tc.get("classname"), tc.get("name"))
                    f = tc.find("failure")
                    if f is not None:
                        failed.append(node)
                        kinds[node] = MK.failure_kind(f.get("message") or "")
                        texts[node] = (f.get("message") or "") + "\n" + (f.text or "")
                    elif tc.find("error") is not None:
                        errored.append(node)
                    elif tc.find("skipped") is None:
                        passed.append(node)
            summary = (r.stdout.strip().splitlines() or [""])[-1][:160]
        return {"exit": r.returncode, "passed": sorted(passed), "failed": sorted(failed), "errored": sorted(errored),
                "kinds": dict(sorted(kinds.items())), "texts": texts, "summary": summary}

    @staticmethod
    def apply(root, rel, edits) -> tuple:
        target = root / rel
        original = target.read_bytes()
        text = original.decode()
        counts = [text.count(a) for a, _ in edits]
        if counts != [1] * len(edits):
            return original, counts, False
        for a, r in edits:
            text = text.replace(a, r)
        if text.encode() == original:
            return original, counts, False
        target.write_text(text)
        return original, counts, True

    def clean(self, root, nodes) -> dict:
        imp = self.imports(root)
        run = self.pytest(root, nodes)
        ok = (imp == "ok" and run["exit"] == 0 and not run["failed"] and not run["errored"]
              and run["passed"] == sorted(nodes))
        return {"import": imp, "passed": len(run["passed"]), "of": len(nodes), "ok": ok,
                "failed": run["failed"], "errored": run["errored"], "summary": run["summary"]}

    # ---- one row -----------------------------------------------------------------------------------------------------------
    def run_one(self, root: pathlib.Path, m) -> dict:
        mid, kind, rel, edits, cells, honest, reason, what = m
        row = {"id": mid, "finding": self.finding, "kind": kind, "file": rel, "what": what, "named_cells": list(cells),
               "honest_nodes": list(honest), "reason": reason, "definition_sha256": definition_sha(m)}
        original, counts, ok = self.apply(root, rel, edits)
        row["anchor_counts"] = counts
        if not ok:
            return {**row, "outcome": "ANCHOR", "good": False}
        try:
            row["import"] = self.imports(root)
            h = self.pytest(root, list(honest)) if honest else None
            row["honest"] = ("n/a" if h is None else "pass" if h["exit"] == 0 and h["passed"] == sorted(honest)
                             else f"fail: {len(h['failed'])} failed, {len(h['errored'])} errored of {len(honest)}")
            c = self.pytest(root, list(cells))
        finally:
            (root / rel).write_bytes(original)
        assert sha(root / rel) == hashlib.sha256(original).hexdigest()
        row.update(MK.classify(c["kinds"], c["failed"], c["errored"]))
        row["named_failed"] = all(n in c["failed"] for n in cells)
        row["reason_seen"] = None if reason is None else any(reason in c["texts"].get(n, "") for n in cells)
        row["pytest"] = c["summary"]
        row["good"] = (row["import"] == "ok" and row["honest"] in ("pass", "n/a") and row["outcome"] == "KILLED"
                       and row["named_failed"] and row["reason_seen"] in (None, True))
        return row

    def run_control(self, root: pathlib.Path, ctl) -> dict:
        cid, rel, edits, cells, what, expected = ctl
        row = {"id": cid, "file": rel, "what": what, "expected": expected, "named_cells": list(cells),
               "definition_sha256": definition_sha(ctl)}
        original, counts, ok = self.apply(root, rel, edits)
        row["anchor_counts"] = counts
        if not ok:
            return {**row, "outcome": "ANCHOR", "good": False}
        try:
            row["import"] = self.imports(root)
            c = self.pytest(root, list(cells))
        finally:
            (root / rel).write_bytes(original)
        row.update(MK.classify(c["kinds"], c["failed"], c["errored"]))
        # a negative control must fail a cell (for no reason a row names); a NO-OP control must PASS every named cell —
        # "none failed" alone is vacuous when the selection collected nothing (a renamed cell, a typo'd node: research)
        row["cells_passed"] = sorted(c["passed"])
        fired = (_noop_fired(row) if expected == "SURVIVED" else bool(row["cells_failed"]))
        row["good"] = row["import"] == "ok" and row["outcome"] == expected and fired
        return row

    # ---- the campaign and its table ---------------------------------------------------------------------------------------
    def campaign(self) -> dict:
        t0 = time.time()
        nodes = sorted(set(self.named_cells()) | set(self.honest_nodes()))
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            self.snapshot(root)
            digests = self.digests(root)               # the bytes measured, never the live tree's at write time
            first = self.clean(root, nodes)
            if not first["ok"]:
                raise SystemExit(f"CLEAN (first) failed — no mutant is meaningful on a tree whose cells fail: {first}")
            rows = []
            for m in self.mutants:
                rows.append(self.run_one(root, m))
                r = rows[-1]
                print(f"  {r['id']:42s} {r.get('outcome', ''):12s} good={r['good']} import={r.get('import')} "
                      f"honest={r.get('honest')} named_failed={r.get('named_failed')} reason={r.get('reason_seen')} "
                      f"kinds={sorted(set(r.get('cell_kinds', {}).values()))}", flush=True)
            controls = [self.run_control(root, k) for k in self.controls]
            last = self.clean(root, nodes)
            if not last["ok"]:
                raise SystemExit(f"CLEAN (last) failed — the copy changed under the campaign: {last}")
        head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True).stdout.split("\n")
        body = {
            "header": {"spec": self.spec, "finding": self.finding, "commit": head,
                       "tracked_changes": sorted(ln[3:] for ln in dirty if ln.strip()),
                       "python": platform.python_version(), "platform": platform.platform(),
                       "sqlite": sqlite3.sqlite_version, "digests": digests,
                       "definitions": {m[0]: definition_sha(m) for m in self.mutants},
                       "control_definitions": {k[0]: definition_sha(k) for k in self.controls},
                       "cells": {self.finding: self.named_cells()}, "honest_nodes": self.honest_nodes(),
                       "clean": {"first": {k: v for k, v in first.items() if k in ("passed", "of", "ok")},
                                 "last": {k: v for k, v in last.items() if k in ("passed", "of", "ok")}}},
            "rows": rows,
            "controls": controls,
            "summary": {"rows": len(rows), "by_kind": {k: sum(r["kind"] == k for r in rows) for k in self.kinds},
                        "killed": sum(r.get("outcome") == "KILLED" for r in rows),
                        "good": sum(r["good"] for r in rows),
                        "controls": len(controls), "controls_good": sum(k["good"] for k in controls),
                        "seconds": round(time.time() - t0)},
        }
        return {**body, "body_sha256": hashlib.sha256(canonical(body)).hexdigest()}

    def defined_tests(self, root: pathlib.Path = ROOT) -> set:
        """{`file::name`} of every top-level test function in the subject's cells files."""
        out = set()
        for f in self.cells_files:
            tree = ast.parse((root / f).read_text(encoding="utf-8"))
            out |= {f"{f}::{n.name}" for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name.startswith("test_")}
        return out

    def problems(self, path=None, root: pathlib.Path = ROOT) -> list:
        path = self.table if path is None else pathlib.Path(path)
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
        if h.get("spec") != self.spec or h.get("finding") != self.finding:
            out.append(f"the table declares {h.get('spec')!r}/{h.get('finding')!r}, not {self.spec}/{self.finding}")
        if h.get("definitions") != {m[0]: definition_sha(m) for m in self.mutants}:
            out.append("the mutant definitions differ from the runner's — run --write")
        if h.get("control_definitions") != {k[0]: definition_sha(k) for k in self.controls}:
            out.append("the control definitions differ from the runner's — run --write")
        if h.get("cells") != {self.finding: self.named_cells()} or h.get("honest_nodes") != self.honest_nodes():
            out.append("the named cells or honest probes differ from the runner's — run --write")
        clean = h.get("clean", {})
        if not (clean.get("first", {}).get("ok") is True and clean.get("last", {}).get("ok") is True):
            out.append(f"the clean runs are not both green: {clean}")
        live = self.digests(root)
        stale = sorted(f for f in set(live) | set(h.get("digests", {})) if live.get(f) != h.get("digests", {}).get(f))
        if stale:
            out.append(f"stale: {stale} — run --write")
        for m in self.mutants + [(k[0], None, k[1], k[2]) for k in self.controls]:
            text = (root / m[2]).read_text(encoding="utf-8")
            for a, _r in m[3]:
                if text.count(a) != 1:
                    out.append(f"{m[0]}: an anchor occurs {text.count(a)} time(s) in {m[2]}")
        tests = self.defined_tests(root)
        for n in sorted(set(self.named_cells()) | set(self.honest_nodes())):
            f, name = n.split("::")[0], n.split("::")[-1].split("[")[0]
            if f"{f}::{name}" not in tests:
                out.append(f"{n} is not a test in {f}")
        rows = t.get("rows", [])
        if [r.get("id") for r in rows] != [m[0] for m in self.mutants]:
            out.append("the rows are not one per mutant, in order")
        for r in rows:
            recount = MK.classify(r.get("cell_kinds") or {}, r.get("cells_failed") or [], r.get("cells_errored") or [])
            named = all(n in (r.get("cells_failed") or []) for n in r.get("named_cells") or ["<none>"])
            if not (r.get("outcome") == "KILLED" == recount["outcome"] and r.get("kill_kind") == recount["kill_kind"]
                    and r.get("import") == "ok" and r.get("honest") in ("pass", "n/a") and r.get("good") is True
                    and named and r.get("named_failed") is True and r.get("reason_seen") in (None, True)
                    and (r.get("reason") is None) == (r.get("reason_seen") is None) and not r.get("cells_errored")):
                out.append(f"{r.get('id')}: not a good row (outcome {r.get('outcome')}, recounted {recount['outcome']}, "
                           f"import {r.get('import')}, honest {r.get('honest')}, every named cell failed {named}, "
                           f"reason seen {r.get('reason_seen')})")
        ctls = t.get("controls", [])
        if [k.get("id") for k in ctls] != [k[0] for k in self.controls]:
            out.append("the controls are not one per CONTROLS entry, in order")
        for k in ctls:
            recount = MK.classify(k.get("cell_kinds") or {}, k.get("cells_failed") or [], k.get("cells_errored") or [])
            noop_ok = k.get("expected") != "SURVIVED" or _noop_fired(k)
            if not (k.get("good") is True and noop_ok
                    and k.get("outcome") == k.get("expected") == recount["outcome"] != "KILLED"):
                out.append(f"{k.get('id')}: the classifier's negative control is not good (outcome {k.get('outcome')}, "
                           f"recounted {recount['outcome']}, expected {k.get('expected')})")
        return out

    def main(self, argv=None) -> int:
        argv = sys.argv if argv is None else argv
        if "--try" in argv:                     # a development aid: the named mutants on a copy, nothing written
            ids = argv[argv.index("--try") + 1:]
            with tempfile.TemporaryDirectory() as d:
                root = pathlib.Path(d)
                self.snapshot(root)
                for m in [m for m in self.mutants if m[0] in ids] + [k for k in self.controls if k[0] in ids]:
                    r = self.run_one(root, m) if len(m) == 8 else self.run_control(root, m)
                    print(json.dumps({k: r.get(k) for k in ("id", "outcome", "good", "import", "honest",
                                                            "named_failed", "reason_seen", "cell_kinds", "pytest")}),
                          flush=True)
            return 0
        if "--write" in argv:
            t = self.campaign()
            self.table.parent.mkdir(exist_ok=True)
            self.table.write_text(render(t), encoding="utf-8")
            print(f"wrote {self.table.relative_to(ROOT)}: {json.dumps(t['summary'])} (body_sha256 {t['body_sha256']})")
            for k in t["controls"]:
                print(f"  {k['id']:42s} {k.get('outcome', ''):12s} good={k['good']}")
            bad = self.problems()
            for b in bad:
                print(f"PROBLEM: {b}")
            return 0 if not bad else 1
        bad = self.problems()
        for b in bad:
            print(f"STALE: {b}")
        if not bad:
            t = json.loads(self.table.read_text(encoding="utf-8"), object_pairs_hook=_strict_pairs)
            print(f"{self.table.relative_to(ROOT)} current: {json.dumps(t['summary'])} (body_sha256 {t['body_sha256']})")
        return 1 if bad else 0
