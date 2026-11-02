"""0048 §2c-ii rows 5, 7, 8, 11 and 12: the four evidence scripts the draft cites, run on this tree in every suite run.

The rows state what the code did at 0048's pin (the defects 0048 v3 answers). With 0048 §4 implemented they are
INVERTED, case by case (2026-11-02, research, on dev's implementation draft): rows 5, 11 and 12 and pin_repro assert the
FIXED behaviour on this tree, while the spec rows keep the pin's measurement as history, which the scripts still
reproduce on a pre-§4 tree (each script states both outputs). Row 8 pins the pin's census as history and the live
census as exactly that history minus the one site §4B removes; the live census as a gate is dev's N4c cell. The census (row 8) is a checker, so its refusals are
driven one by one on planted copies of src/ (P1's mutation matrix); `pin_repro.py` exits 1 when a reproduction stops
reproducing, so its matrix plants the fix and watches it say so. Every script runs as a subprocess with `veracium`
imported from the tree under test and its temporary files under the test's own directory.

What holds a NEW writer is two instruments, and neither alone. The census resolves the forms it is written for and
misses others (round 2's stage 2: twenty, then eleven more against its widened form), so it pins row 8's counts on this
tree and is no regression pin by itself. The token tripwire (`tripwire_0048.py`) resolves nothing: it counts every
token an unvalidated confidence write or an edge json write must contain, and a hand-classified snapshot of its hits
fails on any new one. Together they hold every planted attack. The residual is a write with none of the tripwire's
tokens: a field name built from parts that reaches the store through none of its names (a memory-level route such as
ctypes, a C extension), a SQL write verb built from parts, or SQL read from outside src/veracium/*.py; the residual
control is planted and silent in both. Durable protection is 0048 §4C's validating serialiser at the store, which does not care how a value was made.
"""
from __future__ import annotations

import collections
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "specs" / "evidence" / "0048"
SPEC = ROOT / "specs" / "0048-decay-never-raises-confidence.md"


def _run(tmp_path, script, *args, tree=ROOT):
    env = {**os.environ, "PYTHONPATH": str(tree / "src"), "TMPDIR": str(tmp_path)}
    return subprocess.run([sys.executable, str(EV / script), *map(str, args)], cwd=tree, env=env,
                          capture_output=True, text=True, timeout=300)


def _row(n):
    """The §2c-ii table row numbered `n`, as text."""
    (line,) = [ln for ln in SPEC.read_text().splitlines() if re.match(rf"\| {n} \|", ln)]
    return line


# --- row 8: the census -----------------------------------------------------------------------------------------------

def _census_sites(out):
    conf = re.search(r"of them write `confidence`: (\d+)\n((?:  \S+:\d+ .*\n)*)", out)
    edges = re.search(r"edge json writers in store/sqlite\.py: (\d+)", out)
    unresolved = re.search(r"UNRESOLVED: (\d+)", out)
    files = sorted(re.sub(r"^src/veracium/", "", ln.split()[0].rsplit(":", 1)[0]) for ln in conf.group(2).splitlines())
    return int(conf.group(1)), files, int(edges.group(1)), int(unresolved.group(1))


def test_the_census_states_what_row_8_says(tmp_path):
    """Row 8 is the pin's census, kept as history: five confidence writers in the files it names (the decay site in
    lifecycle.py among them) and seven edge json writers. On this tree the census must give exactly that history
    MINUS the one site 0048 §4B removes (the decay stamp is now built by `Provenance.model_validate`): four writers, in
    the named files less lifecycle.py, the same seven edge writers, nothing unresolved. Files and counts, not line
    numbers. Any other moved writer fails here; a writer of a form the census does not resolve is the tripwire's
    (test_every_tripwire_hit_on_this_tree_is_classified). The live census as a gate is dev's N4c cell."""
    r = _run(tmp_path, "census_0048.py", ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    n_conf, files, n_edge, n_unres = _census_sites(r.stdout)
    row = _row(8)
    named = sorted(m.rsplit(":", 1)[0] for m in re.findall(r"`((?:store/)?[a-z_]+\.py:\d+)`", row)
                   if not m.startswith("scope_read.py"))
    assert "**five**" in row and "Edge `json` writers at L" in row and len(named) == 5, named
    assert "lifecycle.py" in named, named                       # the history names the site §4B removes
    assert (n_conf, n_edge, n_unres) == (len(named) - 1, 7, 0), r.stdout
    rest = list(named)
    rest.remove("lifecycle.py")
    assert files == rest, (files, named)
    assert len(re.search(r"Edge `json` writers at (L[\d, ]+)", row).group(1).split(",")) == n_edge


# The planted forms, one table for both instruments: research's stage-2 matrix (its two controls and twenty forms the
# census was not written for, research 22685e22), dev's six (the forms the census WAS written for), dev's eleven from
# the next-mutant campaign against the widened census, research's pickle round trip, the residual the tripwire names,
# research's write through a table selector the tree already binds (planted inside its function), and seven harmless
# forms. Generated from research's two scripts by `ast.literal_eval`, not retyped (both at research 71c9ed9d). name: (file under src/veracium, code appended, a snippet that runs the form on a
# real Provenance `p` and leaves the result in `q`, or None).
_FORMS = {
    'CONTROL model_copy literal': ('_mut.py', "def f(p):\n    return p.model_copy(update={'confidence': 2.0})\n",
        "q = p.model_copy(update={'confidence': 2.0})"),
    'CONTROL edge UPDATE': ('store/sqlite.py', "_M = 'UPDATE edges SET json=? WHERE id=?'\n",
        None),
    'pydantic .copy(update=)': ('_mut.py', "def f(p):\n    return p.copy(update={'confidence': 2.0})\n",
        "q = p.copy(update={'confidence': 2.0})"),
    'copy.replace': ('_mut.py', 'import copy\ndef f(p):\n    return copy.replace(p, confidence=2.0)\n',
        'import copy; q = copy.replace(p, confidence=2.0)'),
    'model_copy(**kw)': ('_mut.py', "def f(p):\n    kw = {'update': {'confidence': 2.0}}\n    return p.model_copy(**kw)\n",
        "kw = {'update': {'confidence': 2.0}}; q = p.model_copy(**kw)"),
    'parameter rebound in a branch': ('_mut.py', "def f(p, u=None):\n    if u is None:\n        u = {'disclosure': p.disclosure}\n    return p.model_copy(update=u)\n",
        "def f(p, u=None):\n    if u is None:\n        u = {'disclosure': p.disclosure}\n    return p.model_copy(update=u)\nq = f(p, {'confidence': 2.0})"),
    'alias mutated': ('_mut.py', "def f(p):\n    u = {'disclosure': p.disclosure}\n    v = u\n    v['confidence'] = 2.0\n    return p.model_copy(update=u)\n",
        "u = {'disclosure': p.disclosure}; v = u; v['confidence'] = 2.0; q = p.model_copy(update=u)"),
    'dict.update(u, ...)': ('_mut.py', "def f(p):\n    u = {'disclosure': p.disclosure}\n    dict.update(u, confidence=2.0)\n    return p.model_copy(update=u)\n",
        "u = {'disclosure': p.disclosure}; dict.update(u, confidence=2.0); q = p.model_copy(update=u)"),
    'module-constant key': ('_mut.py', "K = 'confidence'\ndef f(p):\n    return p.model_copy(update={K: 2.0})\n",
        "K = 'confidence'; q = p.model_copy(update={K: 2.0})"),
    "getattr(p, 'model_copy')": ('_mut.py', "def f(p):\n    return getattr(p, 'model_copy')(update={'confidence': 2.0})\n",
        "q = getattr(p, 'model_copy')(update={'confidence': 2.0})"),
    'object.__setattr__': ('_mut.py', "def f(p):\n    object.__setattr__(p, 'confidence', 2.0)\n    return p\n",
        "object.__setattr__(p, 'confidence', 2.0); q = p"),
    '__dict__ write': ('_mut.py', "def f(p):\n    p.__dict__['confidence'] = 2.0\n    return p\n",
        "p.__dict__['confidence'] = 2.0; q = p"),
    'edge UPDATE over two lines': ('store/sqlite.py', "_M = '''UPDATE edges\n   SET json=? WHERE id=?'''\n",
        None),
    'edge update in lower case': ('store/sqlite.py', "_M = 'update edges set json=? where id=?'\n",
        None),
    'edge REPLACE INTO': ('store/sqlite.py', "_M = 'REPLACE INTO edges(id,user_id,json) VALUES(?,?,?)'\n",
        None),
    'edge UPDATE OR IGNORE': ('store/sqlite.py', "_M = 'UPDATE OR IGNORE edges SET json=? WHERE id=?'\n",
        None),
    'edge quoted table': ('store/sqlite.py', '_M = \'UPDATE "edges" SET json=? WHERE id=?\'\n',
        None),
    'edge SQL joined by +': ('store/sqlite.py', "_M = 'UPDATE edges ' + 'SET json=? WHERE id=?'\n",
        None),
    'edge writer in another module': ('store/_mut.py', "_M = 'UPDATE edges SET json=? WHERE id=?'\n",
        None),
    'edge schema-qualified': ('store/sqlite.py', "_M = 'UPDATE main.edges SET json=? WHERE id=?'\n",
        None),
    'from copy import replace': ('_mut.py', 'from copy import replace as r\ndef f(p):\n    return r(p, confidence=2.0)\n',
        'from copy import replace as r; q = r(p, confidence=2.0)'),
    'dynamic setattr': ('_mut.py', 'def f(p, k):\n    object.__setattr__(p, k, 2.0)\n    return p\n',
        "k = 'confidence'; object.__setattr__(p, k, 2.0); q = p"),
    'DEV update built by dict()': ('_mut.py', 'def f(p):\n    return p.model_copy(update=dict(confidence=1.0))\n',
        None),
    'DEV local dict writing confidence': ('_mut.py', "def f(p):\n    u = {'confidence': 1.0}\n    return p.model_copy(update=u)\n",
        None),
    'DEV local dict .update()': ('_mut.py', "def f(p):\n    u = {'disclosure': 1}\n    u.update(confidence=1.0)\n    return p.model_copy(update=u)\n",
        None),
    'DEV model_construct': ('_mut.py', 'def f(P):\n    return P.model_construct(confidence=2.0)\n',
        None),
    'DEV key three lines below': ('_mut.py', "def f(p):\n    return p.model_copy(update={\n        'a': 1,\n        'b': 2,\n        'confidence': 0.5})\n",
        None),
    'DEV new edge json writer': ('store/sqlite.py', "_MUT_SQL = 'UPDATE edges SET json=? WHERE user_id=?'\n",
        None),
    'HARMLESS other-field setattr': ('_mut.py', "def f(p):\n    object.__setattr__(p, 'kind', 1)\n    return p\n",
        None),
    'HARMLESS literal getattr': ('_mut.py', "def f(p):\n    return getattr(p, 'model_dump')()\n",
        None),
    'HARMLESS str/datetime replace': ('_mut.py', "def f(s, d):\n    return s.replace('a', 'b'), d.replace(year=2000)\n",
        None),
    'HARMLESS dict tested then used': ('_mut.py', "def f(p):\n    u = {}\n    if p:\n        u['disclosure'] = 1\n    if not u or len(u) == 0:\n        return p\n    return p.model_copy(update=u)\n",
        None),
    'HARMLESS edges read': ('store/sqlite.py', "_M = 'SELECT json FROM edges WHERE id=?'\n",
        None),
    'HARMLESS episodes write': ('store/sqlite.py', "_M = 'UPDATE episodes SET json=? WHERE id=?'\n",
        None),
    'HARMLESS edges_fts write': ('store/sqlite.py', "_M = 'INSERT INTO edges_fts(rowid, json) VALUES(?,?)'\n",
        None),
    'DEV2 vars(p)[...] store': ('_mut.py', "def f(p):\n    vars(p)['confidence'] = 2.0\n    return p\n",
        "vars(p)['confidence'] = 2.0; q = p"),
    'DEV2 __dict__.update': ('_mut.py', 'def f(p):\n    p.__dict__.update(confidence=2.0)\n    return p\n',
        'p.__dict__.update(confidence=2.0); q = p'),
    'DEV2 __dict__ alias |=': ('_mut.py', "def f(p):\n    d = p.__dict__\n    d |= {'confidence': 2.0}\n    return p\n",
        "d = p.__dict__; d |= {'confidence': 2.0}; q = p"),
    'DEV2 deprecated construct': ('_mut.py', 'def f(P):\n    return P.construct(confidence=2.0)\n',
        "q = type(p).construct(author_of_evidence=p.author_of_evidence, evidence_ref='r', confidence=2.0)"),
    'DEV2 bound-method alias': ('_mut.py', "def f(p):\n    m = p.model_copy\n    return m(update={'confidence': 2.0})\n",
        "m = p.model_copy; q = m(update={'confidence': 2.0})"),
    'DEV2 functools.partial': ('_mut.py', "import functools\ndef f(p):\n    return functools.partial(p.model_copy, update={'confidence': 2.0})()\n",
        "import functools; q = functools.partial(p.model_copy, update={'confidence': 2.0})()"),
    'DEV2 SQL %-formatted table': ('store/sqlite.py', "_M = 'UPDATE %s SET json=? WHERE id=?' % 'edges'\n",
        None),
    'DEV2 SQL f-string table name': ('store/sqlite.py', "_T = 'edges'\n_M = f'UPDATE {_T} SET json=? WHERE id=?'\n",
        None),
    "DEV2 SQL ' '.join": ('store/sqlite.py', "_M = ' '.join(['UPDATE edges', 'SET json=? WHERE id=?'])\n",
        None),
    'DEV2 SQL comment in statement': ('store/sqlite.py', "_M = 'UPDATE /* x */ edges SET json=? WHERE id=?'\n",
        None),
    'DEV2 SQL table alias': ('store/sqlite.py', "_M = 'UPDATE edges AS e SET json=? WHERE e.id=?'\n",
        None),
    'R2b pickle round trip': ('_mut.py', "import pickle, struct\ndef f(p):\n    b = pickle.dumps(p)\n    return pickle.loads(b.replace(struct.pack('>d', 0.5), struct.pack('>d', 2.0)))\n",
        "import pickle, struct; b = pickle.dumps(p); q = pickle.loads(b.replace(struct.pack('>d', 0.5), struct.pack('>d', 2.0)))"),
    'RESIDUAL verb built from parts': ('store/sqlite.py', "_M = 'UP' + 'DATE ed' + 'ges SET json=? WHERE id=?'\n",
        None),
    # the census's resolution BY PROPERTY (2026-11-02, dev's MemoryConfig.__setattr__): resolved only in a base-less,
    # keyword-less class's own `__setattr__` (no decorator but the stdlib dataclass), receiver `self`, never
    # rebound, the class subclassed nowhere in src
    'PROP setattr in a BaseModel subclass': ('_mut.py', "from pydantic import BaseModel\nclass _PropM(BaseModel):\n    x: float = 0.0\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP base-less class subclassed in src': ('_mut.py', "class _PropM:\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\nclass _PropN(_PropM):\n    pass\n",
        None),
    'PROP base-less class subclassed by type()': ('_mut.py', "class _PropM:\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n_PropN = type('_PropN', (_PropM,), {})\n",
        None),
    'PROP a metaclass keyword': ('_mut.py', "class _PropM(metaclass=type):\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP outside its own __setattr__': ('_mut.py', "class _PropM:\n    def put(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP receiver not self': ('_mut.py', "class _PropM:\n    def __setattr__(self, name, value):\n        object.__setattr__(value, name, 2.0)\n",
        None),
    'PROP self rebound': ('_mut.py', "class _PropM:\n    def __setattr__(self, name, value):\n        self = value\n        object.__setattr__(self, name, 2.0)\n",
        None),
    # its DECORATORS (dev, 2026-11-02): only the stdlib dataclass, matched by its IMPORT, keeps a class plain
    'PROP pydantic.dataclasses decorator': ('_mut.py', "import pydantic.dataclasses\n@pydantic.dataclasses.dataclass\nclass _PropM:\n    x: float = 0.0\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP dataclass imported from pydantic': ('_mut.py', "from pydantic.dataclasses import dataclass\n@dataclass\nclass _PropM:\n    x: float = 0.0\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP dataclass imported from both': ('_mut.py', "from dataclasses import dataclass\nfrom pydantic.dataclasses import dataclass\n@dataclass\nclass _PropM:\n    x: float = 0.0\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'PROP an unknown decorator': ('_mut.py', "def _deco(c):\n    return c\n@_deco\nclass _PropM:\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'HARMLESS stdlib dataclass(frozen=False)': ('_mut.py', "from dataclasses import dataclass\n@dataclass(frozen=False)\nclass _PropM:\n    x: float = 0.0\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
    'HARMLESS own __setattr__ of a plain class': ('_mut.py', "class _PropM:\n    def __setattr__(self, name, value):\n        object.__setattr__(self, name, value)\n",
        None),
}
# planted INSIDE an existing function: name: (file, anchor line that must occur exactly once, code put before it)
_INSERTS = {
    'R2b UPDATE through an existing selector': ('store/sqlite.py',
        '        row = self._conn.execute(f"SELECT json FROM {table} WHERE id=? AND user_id=?", (target_id, user_id)).fetchone()\n',
        '        self._conn.execute(f"UPDATE {table} SET json=? WHERE id=?", ("{}", target_id))\n'),
}

_CENSUS_IS_NOT_WRITTEN_FOR = ("DEV2 ", "R2b ", "RESIDUAL ", "HARMLESS ")
_TRIPWIRE_SILENT = {"RESIDUAL verb built from parts", "HARMLESS str/datetime replace"}
_DEV_SIX = {  # dev's six, with the exact census result each must give
    "DEV update built by dict()": "unresolved", "DEV local dict writing confidence": "unresolved",
    "DEV local dict .update()": "unresolved", "DEV model_construct": "unresolved",
    "DEV key three lines below": "six writers", "DEV new edge json writer": "eight edge writers"}
_REACH = """
import sys
from veracium.schema import Provenance, EvidenceAuthor
p = Provenance(author_of_evidence=list(EvidenceAuthor)[0], evidence_ref="r", confidence=0.5)
try:
{body}
except Exception as ex:
    print("REFUSED", type(ex).__name__); sys.exit(0)
print("WROTE", q.confidence)
"""


@pytest.fixture(scope="module")
def planted(tmp_path_factory):
    """Every form planted on its own copy of src/, both instruments run on it, and every Python form executed on a
    real Provenance. The unmutated copy is run first and must give the honest results, so a planted case cannot pass by
    the copy being broken."""
    td = tmp_path_factory.mktemp("planted")

    def instruments(tree):
        c = _run(td, "census_0048.py", tree)
        t = _run(td, "tripwire_0048.py", tree)
        assert t.returncode == 0, t.stderr
        return c, json.loads(t.stdout)
    base = td / "base"
    shutil.copytree(ROOT / "src" / "veracium", base / "src" / "veracium", ignore=shutil.ignore_patterns("__pycache__"))
    c0, t0 = instruments(base)
    honest = _census_sites(c0.stdout)
    assert c0.returncode == 0 and honest[3] == 0 and honest[2] == 7, c0.stdout   # relative: (5, 7) at the pin, (4, 7) after §4B
    out = {}
    plants = [(n, rel, code, reach, None) for n, (rel, code, reach) in _FORMS.items()] + \
             [(n, rel, code, None, anchor) for n, (rel, anchor, code) in _INSERTS.items()]
    for i, (name, rel, code, reach, anchor) in enumerate(plants):
        tree = td / f"m{i}"
        shutil.copytree(base, tree)
        target = tree / "src" / "veracium" / rel
        if anchor is None:
            target.write_text((target.read_text() if target.exists() else "") + "\n" + code)
        else:
            old = target.read_text()
            assert old.count(anchor) == 1, f"{name}: the anchor occurs {old.count(anchor)} times -- re-anchor it"
            target.write_text(old.replace(anchor, code + anchor))
        c, tw = instruments(tree)
        cells = {(f, h) for f in set(tw) | set(t0) for h in set(tw.get(f, {})) | set(t0.get(f, {}))}
        fires = sorted(f"{f}:{h}" for f, h in cells if tw.get(f, {}).get(h, 0) != t0.get(f, {}).get(h, 0))
        wrote = None
        if reach is not None:
            body = "\n".join("    " + ln for ln in (reach.splitlines() if "\n" in reach else reach.split("; ")))
            r = subprocess.run([sys.executable, "-c", _REACH.format(body=body)], capture_output=True, text=True,
                               env={**os.environ, "PYTHONPATH": str(ROOT / "src")}, timeout=120)
            wrote = r.stdout.strip() or r.stderr.strip()
        out[name] = (c, _census_sites(c.stdout) if c.returncode in (0, 1) else None, fires, wrote)
    return c0, out


def test_census_0048_refuses_each_planted_defect(planted):
    """census_0048.py's mutation matrix, over the forms it is written to resolve: research's two controls and twenty
    stage-2 forms (each exits 1 as UNRESOLVED or moves a count), and dev's six with the exact result each gives. The
    census's boundary is pinned too, so it cannot move unseen: it stays silent on the seven harmless forms (no
    over-refusal) and on the forms it was not written for, which tripwire_0048.py holds (the next test)."""
    c0, out = planted
    honest = _census_sites(c0.stdout)
    for name, (c, sites, _, _) in out.items():
        n_conf, _, n_edge, n_unres = sites
        noticed = c.returncode == 1 or (n_conf, n_edge, n_unres) != (honest[0], honest[2], honest[3])
        if name.startswith(_CENSUS_IS_NOT_WRITTEN_FOR):
            assert c.returncode == 0 and not noticed, (name, c.stdout)
        elif name in _DEV_SIX:
            assert {"unresolved": c.returncode == 1 and n_unres >= 1,
                    "six writers": c.returncode == 0 and n_conf == honest[0] + 1,      # one more than the honest tree
                    "eight edge writers": c.returncode == 0 and n_edge == honest[2] + 1}[_DEV_SIX[name]], (name, c.stdout)
        else:
            assert noticed, (name, c.stdout)


def test_tripwire_0048_fires_on_every_planted_attack(planted):
    """tripwire_0048.py's mutation matrix. Every attack form (41: the census's own, the twenty it was not written for,
    dev's eleven, the pickle round trip, a write through a table selector the tree already binds) moves a (file,
    trigger) count, and every one that is Python really stores 2.0 when run, so none is a straw man. The residual the
    tripwire's docstring names (a SQL write verb built from parts) is silent in BOTH instruments: the residual is
    stated, and it is accurate. The harmless split is pinned (six fire, the tripwire's cost by design; one is
    silent)."""
    _, out = planted
    for name, (c, _, fires, wrote) in out.items():
        if name in _TRIPWIRE_SILENT:
            assert not fires, (name, fires)
        else:
            assert fires, (name, "tripwire_0048.py is silent")
        if name.startswith("RESIDUAL"):
            assert c.returncode == 0, (name, c.stdout)
        if wrote is not None:
            assert wrote == "WROTE 2.0", (name, wrote)
    attacks = [n for n in out if not n.startswith(("HARMLESS", "RESIDUAL", "PROP"))]
    assert len(attacks) == 41 and sum(out[n][3] is not None for n in attacks) == 20, (len(attacks),)
    assert sum(n.startswith("HARMLESS") for n in out) == 9 and sum(n.startswith("RESIDUAL") for n in out) == 1
    assert sum(n.startswith("PROP") for n in out) == 11


# --- the tripwire's snapshot -------------------------------------------------------------------------------------------

def test_every_tripwire_hit_on_this_tree_is_classified(tmp_path):
    """tripwire_0048.py's hits on this tree equal, as a multiset of (file, trigger, line text), the rows of
    tripwire_0048_classified.tsv, and every row carries a class from its header's closed list. A line that moves still
    matches; a new hit, or an edit to a hit's line, fails here until someone classifies it."""
    r = _run(tmp_path, "tripwire_0048.py", ROOT, "--sites")
    assert r.returncode == 0, r.stderr
    live = collections.Counter()
    for ln in r.stdout.splitlines():
        loc, trig, *text = ln.split(" ", 2)
        live[(loc.rsplit(":", 1)[0], trig, text[0] if text else "")] += 1
    table = (EV / "tripwire_0048_classified.tsv").read_text().splitlines()
    classes = set(re.findall(r"^#   ([a-z-]+) ", "\n".join(table), re.M))
    assert len(classes) == 14, classes                     # validated-write added with 0048 §4B (2026-11-02)
    rows = [ln.split("\t") for ln in table if ln and not ln.startswith("#")]
    assert all(len(row) == 4 and row[0] in classes for row in rows), [row for row in rows if row[0] not in classes]
    snap = collections.Counter((f, t, x) for _, f, t, x in rows)
    assert snap == live, {"unclassified": live - snap, "classified but gone": snap - live}


# --- rows 5 and 7: reach_rows ----------------------------------------------------------------------------------------

def test_reach_row_5_the_out_of_range_write_breaks_the_users_read(tmp_path):
    """INVERTED (0048 §4): row 5 records the pin, where factor 2.0 and NaN were written and the user's read then
    failed. On this tree both refuse at expire()'s entry, nothing is written, and the read returns the untouched 0.9;
    the valid factor still decays to 0.45 (the row's honest control, unchanged). The row keeps its history."""
    r = _run(tmp_path, "reach_rows.py", ROOT, 5)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = r.stdout.splitlines()
    assert lines[:2] == ["factor 2.0: expire -> ValueError; read ok, confidence 0.9",
                         "factor nan: expire -> ValueError; read ok, confidence 0.9"], r.stdout
    assert lines[2].startswith("factor 0.5: expire -> {") and lines[2].endswith("read ok, confidence 0.45"), r.stdout
    for phrase in ("Input should be less than or equal to 1", "Input should be a valid number", "0.45"):
        assert phrase in _row(5), phrase                            # the history stays in the spec
    assert "Input should be" not in r.stdout


def test_reach_row_7_one_bounded_field_frozen_without_assignment_validation(tmp_path):
    r = _run(tmp_path, "reach_rows.py", ROOT, 7)
    assert r.returncode == 0, r.stdout + r.stderr
    for span in re.findall(r"`([^`]+)`", _row(7).split("|")[4]):
        assert span in r.stdout, (span, r.stdout)


# --- row 11: the lost update -----------------------------------------------------------------------------------------

def test_row_11_the_shipped_expire_loses_an_overlapping_update(tmp_path):
    """INVERTED (0048 §4D): at the pin all four overlapping cases lost B's committed state (row 11's history). On this
    tree confirm, confirm95 and lapse keep it, and decay ends exactly where the serial order (B, then A) ends: B's
    0.225 decayed once more to 0.1125, the H-01 value. The probe judges each overlap against its own serial run, so a
    stale write still prints LOST-UPDATE; the printed serial controls are kept, kept and CHANGED (A decays B's result)."""
    r = _run(tmp_path, "probe_expire_lost_update.py", tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    verdicts = dict(re.findall(r"^(\w+)\s+B committed .*\n.*\s(LOST-UPDATE|kept|serial)$", r.stdout, re.M))
    assert verdicts == {"confirm": "kept", "confirm95": "kept", "lapse": "kept", "decay": "serial"}, r.stdout
    (decay,) = re.findall(r"^decay\s+B committed .*'confidence': ([\d.]+).*\n.*-> .*'confidence': ([\d.]+)", r.stdout, re.M)
    assert decay == ("0.225", "0.1125"), decay
    serial = dict(re.findall(r"^(\w+)\s+SERIAL B .*\n.*\s(kept|CHANGED)$", r.stdout, re.M))
    assert serial == {"confirm": "kept", "lapse": "kept", "decay": "CHANGED"}, r.stdout
    assert "LOST-UPDATE" in _row(11)                                # the history stays in the spec


# --- row 12: the round-1 reproductions -------------------------------------------------------------------------------

_FIXED = {  # pin_repro's case -> its label on a tree with 0048 §4 (at the pin: every case REPRODUCED)
    "R1-01 factor 2.0 on 0.3": "NOT REPRODUCED", "R1-01 floor 2.0 (the second numeric field)": "NOT REPRODUCED",
    "R1-01 floor NaN": "NOT REPRODUCED", "R1-01 Boolean factor": "NOT REPRODUCED",
    "R1-02 two connections": "NOT REPRODUCED", "R1-03 prefix written before the refusal": "NOT REPRODUCED",
    "R1-04 census": "NOT REPRODUCED",
    "R1-04 episode carrier": "REPRODUCED",                     # episodes are outside 0048 (the owner's Q6 ruling)
    "finite-decay note: a float fixed point": "REPRODUCED",    # arithmetic: 5e-324 * 0.9 == 5e-324
    "CONTROL valid factor decays": "CONTROL HOLDS", "CONTROL the same three runs, serial": "CONTROL HOLDS",
    "CONTROL mixed order, valid config": "CONTROL HOLDS"}


def _labels(out):
    """{case name: label}; a case name may itself hold a colon, so names are matched against _FIXED's."""
    return {next((k for k in _FIXED if ln[15:].startswith(k + ": ")), ln[15:]): ln[:14].strip()
            for ln in out.splitlines()}


def test_row_12_the_round_1_reproductions_hold_and_their_controls_hold(tmp_path):
    """INVERTED (0048 §4), case by case: the four R1-01 cases refuse at entry, R1-02's race ends at the serial value,
    R1-03 writes nothing before its refusal, and R1-04's census has lost the decay site; the episode carrier and the
    float fixed point still reproduce, and the three controls hold. pin_repro exits 1 because reproductions failed,
    which is the fix. (At the pin: nine REPRODUCED, three controls, exit 0: row 12's history.)"""
    r = _run(tmp_path, "pin_repro.py", ROOT)
    assert r.returncode == 1, r.stdout + r.stderr
    assert _labels(r.stdout) == _FIXED, r.stdout
    assert "refused=ValueError" in r.stdout.splitlines()[0], r.stdout
    assert not (tmp_path / "leftover").exists() and not any(p.name.startswith("tmp") for p in tmp_path.iterdir())


def test_pin_repro_reports_a_planted_fix_as_not_reproduced(tmp_path):
    """pin_repro's mutation matrix, inverted with the fix: on this tree it reports the fix (row 12's test), so the
    instrument must also see the DEFECT when it is planted back. On a copy of src/ whose expire() no longer validates
    its policy at entry (0048 §6's mutant "the entry validation removed, B and C intact"), exactly the five cases that
    entry validation answers flip to REPRODUCED: the four R1-01 cases (a factor 2.0 on 0.3 persists 0.6, which C's
    bound check accepts) and R1-03 (the TRANSIENT edge is lapsed before the bad factor raises). Every other line, the
    race, the census and the controls, is unchanged. (At the pin this matrix clamped the factor and watched the factor
    case flip the other way.)"""
    tree = tmp_path / "mutant"
    shutil.copytree(ROOT / "src" / "veracium", tree / "src" / "veracium")
    lc = tree / "src" / "veracium" / "lifecycle.py"
    t = lc.read_text()
    for a, b in (('validate_decay_bound("decay_factor", config.decay_factor)', 'config.decay_factor'),
                 ('validate_decay_bound("confidence_floor", config.confidence_floor)', 'config.confidence_floor')):
        assert t.count(a) == 1, "the mutant's anchor moved: re-anchor this test"
        t = t.replace(a, b)
    lc.write_text(t)
    honest = _labels(_run(tmp_path, "pin_repro.py", ROOT).stdout)
    r = _run(tmp_path, "pin_repro.py", tree, tree=tree)
    mutant = _labels(r.stdout)
    assert honest == _FIXED and mutant.keys() == honest.keys(), r.stdout + r.stderr
    flipped = sorted(k for k in honest if honest[k] != mutant[k])
    assert flipped == sorted(["R1-01 factor 2.0 on 0.3", "R1-01 floor 2.0 (the second numeric field)",
                              "R1-01 floor NaN", "R1-01 Boolean factor", "R1-03 prefix written before the refusal"]), \
        (flipped, r.stdout)
    assert all(mutant[k] == "REPRODUCED" for k in flipped), r.stdout


# --- the contract harness (round 1's request: a small runnable model of §4) ---------------------------------------------

def _harness(tmp_path, harness=EV / "contract_harness_0048.py"):
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "TMPDIR": str(tmp_path)}
    return subprocess.run([sys.executable, str(harness), str(ROOT)], cwd=ROOT, env=env, capture_output=True,
                          text=True, timeout=600)


def _s6_mutant_rows():
    """§6's mutant table as (mutant, killing cell) pairs, the two N4c rows aside: those are held by the census and the
    tripwire over the tree, and the harness's docstring states that complement."""
    s6 = SPEC.read_text()
    s6 = s6[s6.index("\n## 6."):s6.index("\n## 7.")]
    cells = lambda ln: [x.strip() for x in re.split(r"(?<!\\)\|", ln)[1:-1]]
    lines = [ln for ln in s6.splitlines() if ln.startswith("|")]
    (h,) = [k for k, ln in enumerate(lines) if [x.lower() for x in cells(ln)] == ["mutant", "reintroduces", "killed by"]]
    rows = []
    for ln in lines[h + 2:]:
        c = cells(ln)
        if len(c) != 3:
            break
        rows.append(c)
    return {(m, k) for m, why, k in rows if not why.startswith("N4c")}, len(rows)


def test_contract_harness_0048_counts_only_a_refusal_as_a_kill(tmp_path):
    """contract_harness_0048.py's mutation matrix. On the tree it runs exactly §6's mutant rows (by row text and killing
    cell, both ways; the per-writer bypass row once per model writer, so two more MUTANT lines than rows), kills every
    one and passes every control. Then three planted copies of the harness: a mutation that changes nothing must
    SURVIVE; a mutation that only crashes the model must read CRASHED, never KILLED (a crash is not the cell's refusal);
    a model line moved under a mutant's anchor must stop the run as a HARNESS ERROR. Each exits non-zero."""
    want, n_rows = _s6_mutant_rows()
    r = _harness(tmp_path)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr
    mutants = [ln.split(" | ") for ln in r.stdout.splitlines() if ln.startswith("MUTANT ")]
    assert {(m[1], m[2]) for m in mutants} == want, {(m[1], m[2]) for m in mutants} ^ want
    n = len(want) + 2 + 8          # the per-writer bypass row x3 (+2); the unresolved-connection-form row x9 (+8), R2-01
    assert len(mutants) == n and all(m[0] == "MUTANT KILLED" for m in mutants), [m[:3] for m in mutants]
    tally = re.findall(r"^TALLY: mutants (\d+)/(\d+) killed; controls (\d+)/(\d+) pass$", r.stdout, re.M)
    assert tally and tally[0][0] == tally[0][1] == str(n) and tally[0][2] == tally[0][3] and int(tally[0][3]) > 0, tally
    assert n_rows == len(want) + 2, "the N4c complement is no longer exactly two rows: restate the harness's docstring"

    src = (EV / "contract_harness_0048.py").read_text()
    anchor = '"    return Edge.model_validate(e.model_dump()).model_dump_json()\\n", "    return e.model_dump_json()\\n"'
    assert src.count(anchor) == 1, "the mutator's anchor moved: re-anchor this test"
    planted = {
        "no-op": src.replace(anchor, anchor.split(", ")[0] + ", " + anchor.split(", ")[0]),
        "crash": src.replace(anchor, anchor.split(", ")[0] + ", \"    raise RuntimeError('a crash, not a refusal')\\n\""),
    }
    model_line = "    return Edge.model_validate(e.model_dump()).model_dump_json()\n"
    assert src.count(model_line) == 1, "the model line moved: re-anchor this test"
    planted["drift"] = src.replace(model_line, "    return Edge.model_validate(e.model_dump()).model_dump_json()  # moved\n")
    out = {}
    for name, text in planted.items():
        f = tmp_path / f"harness_{name}.py"
        f.write_text(text)
        out[name] = _harness(tmp_path, f)
    line = lambda r: [ln for ln in r.stdout.splitlines() if "| the store helper serialises without validating |" in ln]
    assert out["no-op"].returncode == 1 and line(out["no-op"])[0].startswith("MUTANT SURVIVED"), out["no-op"].stdout[-800:]
    assert out["crash"].returncode == 1 and line(out["crash"])[0].startswith("MUTANT CRASHED"), out["crash"].stdout[-800:]
    assert out["drift"].returncode == 2 and "HARNESS ERROR" in out["drift"].stderr, out["drift"].stdout[-400:] + out["drift"].stderr
