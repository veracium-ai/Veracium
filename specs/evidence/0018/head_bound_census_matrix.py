#!/usr/bin/env python3
"""The repository census's adversarial matrix (0018 adjacent rungs; derived from dev-model/head_bound_census_matrix.py, with
the table plants research's stage-1 read asked for).

Usage: head_bound_census_matrix.py <tree-root> <expected.json> <scratch-dir>

Each case copies <tree-root>/src into <scratch-dir>/<case>/src, plants ONE change (on an existing line or at end of
file, so no other line moves), and runs `head_bound_census.py <copy> --check <expected.json>`. A PLANT must be refused
(exit 1, naming its own reference); a CONTROL must pass (exit 0): an honest copy, a reference in a function outside the
reach, and a same-named constant of another module. Every anchor is asserted to occur exactly once before it is
edited. Prints one line per case; exits 1 if any case is not as expected."""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
tree, expected, scratch = (pathlib.Path(a).resolve() for a in sys.argv[1:4])
scratch.mkdir(parents=True, exist_ok=False)
MIG, SV, EE = "veracium/store/migration.py", "veracium/store/schema_version.py", "veracium/store/edge_events.py"
BASE_KEYS = "        run = _Forward(base, target)\n"
PENDING = "        pending: dict = {}\n"
L63 = 'def _apply_forward(conn: sqlite3.Connection, base: int, target: int = SCHEMA_VERSION) -> None:\n'
NEXT_SEQ = '    serialized (the PK is a backstop only, §4a)."""\n'


def on_line(anchor, tail):
    """append `; tail` to the anchor line (no line moves)"""
    return (anchor, anchor.rstrip("\n") + "; " + tail + "\n")


CASES = [
    # (label, expect, {file: [(old, new), ...]}, eof {file: text}, the token the refusal must name)
    ("honest", "PASS", {}, {}, None),
    ("PLANT a seventh error carrying the head (constructed in _apply_forward)", "REFUSE",
     {MIG: [on_line(BASE_KEYS, '_plant = StoreVersionError("", base, SCHEMA_VERSION, "plant")')]}, {}, "_apply_forward"),
    ("PLANT a module-level alias, used in _apply_forward", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _HEAD_ALIAS")]}, {MIG: "_HEAD_ALIAS = SCHEMA_VERSION\n"}, "_apply_forward"),
    ("PLANT an alias of an alias, used in _apply_forward", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _HEAD_ALIAS2")]}, {MIG: "_HEAD_ALIAS1 = SCHEMA_VERSION\n_HEAD_ALIAS2 = _HEAD_ALIAS1\n"},
     "_apply_forward"),
    ("PLANT an import-as alias, used in _apply_forward", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _HV")]}, {MIG: "from .schema_version import SCHEMA_VERSION as _HV\n"}, "_apply_forward"),
    ("PLANT a module alias's attribute, used in _apply_forward", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _svmod.SCHEMA_VERSION")]}, {MIG: "from . import schema_version as _svmod\n"},
     "_apply_forward"),
    ("PLANT a reference in a newly called helper", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _plant_helper()")]}, {MIG: "def _plant_helper():\n    return SCHEMA_VERSION\n"},
     "_plant_helper"),
    ("PLANT a reference in a reached helper of ANOTHER store module (edge_events.next_seq)", "REFUSE",
     {EE: [on_line(NEXT_SEQ, "_plant = _SVX")]}, {EE: "from .schema_version import SCHEMA_VERSION as _SVX\n"}, "next_seq"),
    ("PLANT a reference in a raised error's base __init__ (StoreVersionError, schema_version.py)", "REFUSE",
     {}, {}, "StoreVersionError.__init__"),            # filled below: needs the __init__'s first body line
    ("PLANT the one listed reference deleted (the target's default replaced by a literal)", "REFUSE",
     {MIG: [(L63, L63.replace("SCHEMA_VERSION", "16"))]}, {}, "_apply_forward"),
    ("PLANT a step named only in FORWARD_ENTRIES (research's stage-1 finding)", "REFUSE",
     {}, {MIG: "def _step_plant(conn):\n    return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = (('p', _step_plant),)\n"}, "_step_plant"),
    ("PLANT a step the table names by a STRING", "REFUSE",
     {}, {MIG: "def _step_str(conn):\n    return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = (('p', '_step_str'),)\n"}, "_step_str"),
    ("PLANT a helper a dispatched step calls", "REFUSE",
     {}, {MIG: "def _deep():\n    return SCHEMA_VERSION\n\n\ndef _step_d(conn):\n    return _deep()\n\n\nFORWARD_ENTRIES = (('p', _step_d),)\n"}, "_deep"),
    ("PLANT a function referenced, not called, in _apply_forward", "REFUSE",
     {MIG: [on_line(BASE_KEYS, "_plant = _held")]}, {MIG: "def _held():\n    return SCHEMA_VERSION\n"}, "_held"),
    ('PLANT (research) keyword field of an entry constructor', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\nclass Entry:\n    def __init__(self, kind, fn=None):\n        self.fn = fn\n\n\nFORWARD_ENTRIES = (Entry('p', fn=_step_x),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) functools.partial in the table', "REFUSE", {}, {'veracium/store/migration.py': "import functools\ndef _step_x(conn):\n    return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = (('p', functools.partial(_step_x)),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) default argument in a step', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn, head=SCHEMA_VERSION):\n    return head\n\n\nFORWARD_ENTRIES = (('p', _step_x),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) table assembled from a named sub-tuple', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n_V16_ENTRIES = (('p', _step_x),)\nFORWARD_ENTRIES = _V16_ENTRIES\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) table concatenated from two sub-tuples', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n_A = ()\n_B = (('p', _step_x),)\nFORWARD_ENTRIES = _A + _B\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) table built by a function', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\ndef _build():\n    return (('p', _step_x),)\n\n\nFORWARD_ENTRIES = _build()\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) table extended with +=', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = ()\nFORWARD_ENTRIES += (('p', _step_x),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) the head value in the table itself', "REFUSE", {}, {'veracium/store/migration.py': "FORWARD_ENTRIES = (('stamp', SCHEMA_VERSION),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) a lambda in the table reading the head', "REFUSE", {}, {'veracium/store/migration.py': "FORWARD_ENTRIES = (('p', lambda conn: SCHEMA_VERSION),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) a module-level alias of a step', "REFUSE", {}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n_alias = _step_x\nFORWARD_ENTRIES = (('p', _alias),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) a staticmethod as a step', "REFUSE", {}, {'veracium/store/migration.py': "class _Steps:\n    @staticmethod\n    def run(conn):\n        return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = (('p', _Steps.run),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) the table in its own store module', "REFUSE", {}, {'veracium/store/forward_table.py': "from .schema_version import SCHEMA_VERSION\n\n\ndef _step_x(conn):\n    return SCHEMA_VERSION\n\n\nFORWARD_ENTRIES = (('p', _step_x),)\n", 'veracium/store/migration.py': 'from .forward_table import FORWARD_ENTRIES\n'}, "CENSUS DIFFERS"),
    ('PLANT (research) the table under another name, read in _apply_forward', "REFUSE", {MIG: [on_line(BASE_KEYS, '_plant = _TABLE')]}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n_TABLE = (('p', _step_x),)\n"}, "CENSUS DIFFERS"),
    ('PLANT (research) a dict of steps read in _apply_forward', "REFUSE", {MIG: [on_line(BASE_KEYS, '_plant = _STEPS')]}, {'veracium/store/migration.py': "def _step_x(conn):\n    return SCHEMA_VERSION\n\n\n_STEPS = {'x': _step_x}\n"}, "CENSUS DIFFERS"),
    ("CONTROL a reference in a function OUTSIDE the reach (migrate_store)", "PASS",
     {MIG: [on_line(PENDING, "_plant = SCHEMA_VERSION")]}, {}, None),
    ("CONTROL a table naming a function with no reference", "PASS",
     {}, {MIG: "def _step_clean(conn):\n    return None\n\n\nFORWARD_ENTRIES = (('p', _step_clean),)\n"}, None),
    ("CONTROL a same-named constant of another module (diagnostics.SCHEMA_VERSION) in _apply_forward", "PASS",
     {MIG: [on_line(BASE_KEYS, "_plant = _DIAG_SV")]}, {MIG: "from ..diagnostics import SCHEMA_VERSION as _DIAG_SV\n"}, None),
]

# StoreVersionError.__init__'s first statement line, read from the tree (anchored, asserted once)
svsrc = (tree / "src" / SV).read_text()
import ast
cls = next(n for n in ast.parse(svsrc).body if isinstance(n, ast.ClassDef) and n.name == "StoreVersionError")
init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
lines = svsrc.splitlines(keepends=True)
cands = [s for s in init.body if isinstance(s, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and s.end_lineno == s.lineno
         and svsrc.count(lines[s.lineno - 1]) == 1]
assert cands, "StoreVersionError.__init__ has no unique one-line assignment to plant on"
first = lines[cands[0].lineno - 1]
CASES[8] = (CASES[8][0], "REFUSE", {SV: [on_line(first, "_plant = SCHEMA_VERSION")]}, {}, "StoreVersionError.__init__")

bad = 0
for i, (label, expect, edits, eof, token) in enumerate(CASES):
    d = scratch / f"case{i:02d}"
    shutil.copytree(tree / "src", d / "src")
    for f, pairs in edits.items():
        p = d / "src" / f; t = p.read_text()
        for old, new in pairs:
            assert t.count(old) == 1, f"{label}: anchor occurs {t.count(old)} times in {f}"
            t = t.replace(old, new)
        assert t != p.read_text(), f"{label}: the edit changed nothing"
        p.write_text(t)
    for f, text in eof.items():
        p = d / "src" / f; p.write_text((p.read_text() if p.exists() else "") + text)
    r = subprocess.run([sys.executable, "-I", str(HERE / "head_bound_census.py"), str(d), "--check", str(expected)],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if expect == "PASS":
        ok = r.returncode == 0 and out.startswith("CENSUS EQUAL")
    else:
        ok = r.returncode == 1 and "CENSUS DIFFERS" in out and token in out
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} {label}: expected {expect}, exit {r.returncode}: {out.splitlines()[0] if out else r.stderr.strip()[-150:]}")
print(f"CENSUS MATRIX: {len(CASES)} cases, {bad} not as expected")
sys.exit(1 if bad else 0)
