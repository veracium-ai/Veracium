"""specs/0031 §4b-ii — the proposal carrier's DDL, executed from the SPEC.

Round-2 F6 asked for runnable evidence rather than transcripts; this file is
it. The DDL is EXTRACTED FROM THE SPEC at test time — the spec's own fenced
`CREATE TABLE` blocks are what executes — so a spec edit that breaks the
contract fails here, and the committed evidence can never drift from the
normative text (the propagation discipline, applied to DDL).

Round-2's findings live here as permanent cells: the reviewer's six original
rows (R1-R6), the NULL-blind claim CHECK (C1 — SQL three-valued logic: NULL
never fails a naive CHECK), the non-hex digest (N1), the FK to a nonexistent
proposal (N3), and the resolver attribution (N4). RULE ZERO: the FK cells run
under `PRAGMA foreign_keys=ON` exactly as the store must open connections,
and the pragma-OFF negative control proves the FK is INERT without it — an
unenforced FK is a comment wearing a constraint's clothes.
"""
import re
import sqlite3
from pathlib import Path

import pytest

SPEC = Path(__file__).resolve().parents[1] / "specs" / "0031-agent-facing-trust-surface.md"


def _ddl():
    text = SPEC.read_text()
    blocks = re.findall(r"CREATE TABLE mcp_proposal.*?\n\);", text, re.S)
    assert len(blocks) == 2, (
        f"expected exactly the two pinned tables in the spec, found {len(blocks)}")
    return "\n".join(blocks)


@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")   # the pinned store obligation
    conn.executescript(_ddl())
    yield conn
    conn.close()


BASE = dict(user_id="u", id="p1", kind="correction", proposer="model",
            target_edge_id="e1", target_state_digest="a" * 64,
            correction_payload='{"new":"x"}', claim="error",
            evidence_ref="ev", note=None, created_at="T", expires_at="T2",
            state="open", resolved_at=None, applied_txn=None)
RBASE = dict(user_id="u", proposal_id="p1", seq=1, action="accept", at="T",
             resolver="host-admin", applied_txn=7, reversal_txn=None)


def _insert(conn, table, base, **over):
    row = {**base, **over}
    cols, ph = ",".join(row), ",".join("?" * len(row))
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({ph})",
                 list(row.values()))


PROPOSAL_CELLS = [
    # (cell, overrides, refused?)
    ("R1-kind-confirm", dict(kind="confirm"), True),
    ("R2-proposer-user", dict(proposer="user"), True),
    ("R3-unknown-kind", dict(kind="zzz"), True),
    ("R4-dispute-with-payload",
     dict(kind="dispute", correction_payload='{"x":1}', claim=None), True),
    ("R5-terminal-missing-resolution", dict(state="accepted"), True),
    ("R6-open-with-resolution", dict(resolved_at="T3", applied_txn=7), True),
    ("C1-correction-claim-NULL", dict(claim=None), True),
    ("C2-claim-outside-domain", dict(claim="oops"), True),
    ("C3-dispute-with-claim",
     dict(kind="dispute", correction_payload=None, claim="error"), True),
    # C4: the pad keeps the payload VALID JSON so the length bound is the ONLY
    # refusing conjunct — round-4's json_valid addition would otherwise mask it
    # (the sole-coverage-mutant lesson from round 3, applied preemptively).
    ("C4-oversize-payload",
     dict(correction_payload='{"pad":"' + "x" * 5000 + '"}'), True),
    ("R7-nonjson-payload (round-4 F1)",
     dict(correction_payload="not json at all"), True),
    ("N1-non-hex-digest", dict(target_state_digest="Z" * 64), True),
    ("N2-short-digest", dict(target_state_digest="ab"), True),
    ("N5-BLOB-digest", dict(target_state_digest=b"a" * 64), True),
    # N6 RELABELED (round-4 F3): "seven" is NON-COERCIBLE text, which is the
    # only textual class the DDL can refuse — coercible "7" passes; see the
    # honest-limit cells below.
    ("N6-noncoercible-text-applied-txn",
     dict(state="accepted", resolved_at="T3", applied_txn="seven"), True),
    ("N7-negative-applied-txn",
     dict(state="accepted", resolved_at="T3", applied_txn=-1), True),
    ("P1-valid-correction", dict(), False),
    ("P2-valid-dispute",
     dict(kind="dispute", correction_payload=None, claim=None), False),
    ("P3-valid-accepted",
     dict(state="accepted", resolved_at="T3", applied_txn=7), False),
    ("P4-valid-refused", dict(state="refused", resolved_at="T3"), False),
]


@pytest.mark.parametrize("cell,over,refused",
                         PROPOSAL_CELLS, ids=[c[0] for c in PROPOSAL_CELLS])
def test_proposal_cell(db, cell, over, refused):
    if refused:
        with pytest.raises(sqlite3.IntegrityError):
            _insert(db, "mcp_proposal", BASE, **over)
    else:
        _insert(db, "mcp_proposal", BASE, **over)


RESOLUTION_CELLS = [
    ("N3-fk-nonexistent-proposal", dict(proposal_id="p-missing"), True),
    ("N4-resolver-empty", dict(resolver=""), True),
    ("N8-BLOB-resolver", dict(resolver=b"host-admin"), True),
    ("N9-negative-seq", dict(seq=-3), True),
    ("N10-noncoercible-text-reversal-txn",
     dict(action="reverse", applied_txn=None, reversal_txn="nine"), True),
    ("N11-negative-reversal-txn",
     dict(action="reverse", applied_txn=None, reversal_txn=-9), True),
    ("accept-valid", dict(), False),
    ("accept-without-txn", dict(applied_txn=None), True),
    ("reverse-valid", dict(action="reverse", applied_txn=None, reversal_txn=9),
     False),
    ("refuse-valid", dict(action="refuse", applied_txn=None), False),
]


@pytest.mark.parametrize("cell,over,refused",
                         RESOLUTION_CELLS, ids=[c[0] for c in RESOLUTION_CELLS])
def test_resolution_cell(db, cell, over, refused):
    _insert(db, "mcp_proposal", BASE)          # the referenced proposal
    if refused:
        with pytest.raises(sqlite3.IntegrityError):
            _insert(db, "mcp_proposal_resolution", RBASE, **over)
    else:
        _insert(db, "mcp_proposal_resolution", RBASE, **over)


def test_fk_is_inert_without_the_pragma__control():
    """V-FK-ENFORCED's negative control: the SAME DDL on a connection opened
    WITHOUT the pragma ACCEPTS a resolution for a nonexistent proposal — so
    the pragma is load-bearing, and a store that forgets it ships the
    round-1 comments-not-constraints defect in a new costume."""
    conn = sqlite3.connect(":memory:")       # no PRAGMA — the wrong opening
    conn.executescript(_ddl())
    _insert(conn, "mcp_proposal_resolution", RBASE, proposal_id="p-missing")
    conn.close()  # accepted: the control proves the pragma discriminates


def test_fk_holds_under_the_pinned_store_opening_sequence(tmp_path):
    """Round-3 F6's path fix: the prior FK evidence enabled the pragma on a
    raw connection and so proved the WRONG claim — TODAY's `SqliteStore`
    opens with `PRAGMA foreign_keys = 0`, which is exactly WHY 0031 pins
    the cross-spec obligation (0007's connection open gains the pragma at
    Phase B implementation, as a rider). This test mirrors the PINNED
    OPENING SEQUENCE the spec obligates — file-backed, busy_timeout, then
    the pragma, in order — so it is evidence for the path the store must
    take, not for a path no store takes."""
    conn = sqlite3.connect(str(tmp_path / "store.db"),
                           check_same_thread=False)
    conn.execute("PRAGMA busy_timeout = 5000")   # 0007's opening, mirrored
    conn.execute("PRAGMA foreign_keys = ON")     # the 0031 rider's addition
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.executescript(_ddl())
    with pytest.raises(sqlite3.IntegrityError):
        _insert(conn, "mcp_proposal_resolution", RBASE,
                proposal_id="p-missing")
    conn.close()


def test_todays_store_lacks_the_pragma__the_obligation_is_real():
    """The honest fact the obligation rests on, asserted so it cannot rot
    silently: the SHIPPED store opens with foreign_keys = 0. The day the
    Phase B rider lands in 0007's open sequence, this test FAILS — which
    is the desired signal to flip it into the positive assertion and
    retire the obligation as discharged."""
    import tempfile
    from veracium import SqliteStore
    with tempfile.TemporaryDirectory() as td:
        s = SqliteStore(td + "/t.db")
        assert s._conn.execute("PRAGMA foreign_keys").fetchone()[0] == 0


def test_null_claim_would_pass_a_naive_check__control():
    """C1's mechanism, kept executable: NULL IN (...) is NULL, and a CHECK
    refuses only FALSE — proven on a minimal naive table so the spec's
    IS-NOT-NULL clause is demonstrably load-bearing."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""CREATE TABLE naive (
        kind TEXT NOT NULL,
        claim TEXT CHECK ((kind = 'dispute' AND claim IS NULL) OR
                          (kind = 'correction' AND claim IN ('error','change'))))""")
    conn.execute("INSERT INTO naive VALUES ('correction', NULL)")  # accepted!
    conn.close()


# ---------- round-4 F3: coercion — the DDL's HONEST LIMIT, kept executable

def test_coercible_text_txn_is_ddl_invisible__honest_limit(db):
    """The reviewer's probe, permanent: affinity conversion runs BEFORE every
    CHECK, so textual "7" bound to the INTEGER applied_txn column arrives at
    typeof() already an integer and is ACCEPTED. No DDL — STRICT included
    (executed, both seats) — can see the caller's binding type; that is the
    STORE schedules' pinned validation preamble (§4c-i). This cell asserts
    the coercion HAPPENS, so the store obligation's necessity stays
    executable — and it is designed to expire: if SQLite ever stops
    coercing, this fails and the narrowed DDL claim can be re-widened."""
    _insert(db, "mcp_proposal", BASE,
            state="accepted", resolved_at="T3", applied_txn="7")
    v, t = db.execute("SELECT applied_txn, typeof(applied_txn) "
                      "FROM mcp_proposal").fetchone()
    assert (v, t) == (7, "integer"), (v, t)


def test_numeric_resolver_coerces_to_text__honest_limit(db):
    """The other direction of the same limit: numeric 7 bound to the TEXT
    resolver column stores as '7' and satisfies every CHECK. Same owner:
    the schedules' binding-type preamble, not the DDL."""
    _insert(db, "mcp_proposal", BASE)
    _insert(db, "mcp_proposal_resolution", RBASE, resolver=7)
    v, t = db.execute("SELECT resolver, typeof(resolver) "
                      "FROM mcp_proposal_resolution").fetchone()
    assert (v, t) == ("7", "text"), (v, t)


def test_ddl_accepts_what_the_store_parse_must_refuse__honest_limit(db):
    """Round-4 F1's ownership split, executable: json_valid refuses raw text
    (R7) but ACCEPTS `{}` (fails field requiredness) and a duplicate-key
    object (SQLite's parser is last-wins) — the payload FIELD contract's
    owner is the store parse at both sites (§4b-ii), and this cell is the
    DDL's honest limit asserted so the ownership row stays load-bearing."""
    _insert(db, "mcp_proposal", BASE, id="p-empty", correction_payload="{}")
    _insert(db, "mcp_proposal", BASE, id="p-dup",
            correction_payload='{"object":"a","object":"b"}')


# ---------- round-4 F2: V-RESOLUTION-LEDGER — the gate, extracted and fired

def _gate_selects():
    """The gate SQL comes FROM THE SPEC's fenced block (extract-at-test-time,
    the same discipline as _ddl): the audit that runs is the audit the spec
    promises, and neither can drift from the other."""
    text = SPEC.read_text()
    m = re.findall(r"```sql\n(-- V-RESOLUTION-LEDGER.*?)```", text, re.S)
    assert len(m) == 1, f"expected exactly one fenced gate block, found {len(m)}"
    # Comment lines label the clauses (and mention SELECT in prose), so strip
    # them BEFORE splitting — the statements are what remains between ';'s.
    sql_only = "\n".join(l for l in m[0].splitlines()
                         if not l.strip().startswith("--"))
    selects = [s.strip() for s in sql_only.split(";") if s.strip()]
    assert len(selects) == 7, ("expected the seven audit SELECTs "
        f"(round-5 F1 added the state/action grammar), found {len(selects)}")
    return selects


def _audit(conn):
    return [i for i, s in enumerate(_gate_selects(), 1)
            if conn.execute(s.rstrip(";")).fetchall()]


def _fresh_history(builder):
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_ddl())
    builder(conn)
    return conn


def _p(conn, **over):
    _insert(conn, "mcp_proposal", BASE, **over)


def _r(conn, **over):
    _insert(conn, "mcp_proposal_resolution", RBASE, **over)


GATE_HISTORIES = [
    # (case, builder, clauses that MUST fire — [] means the clean pass)
    ("clean-multi-proposal", lambda c: (
        _p(c, id="p1", state="accepted", resolved_at="T3", applied_txn=7),
        _p(c, id="p2", state="refused", resolved_at="T3"),
        _p(c, id="p3"),
        _r(c, proposal_id="p1", seq=1),
        _r(c, proposal_id="p1", seq=2, action="reverse",
           applied_txn=None, reversal_txn=9),
        _r(c, proposal_id="p2", seq=1, action="refuse", applied_txn=None)), []),
    ("accepted-without-accept-row", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),), [1, 7]),
    ("two-accept-rows", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),
        _r(c, seq=1), _r(c, seq=2)), [1, 7]),
    ("mismatched-applied-txn", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),
        _r(c, seq=1, applied_txn=8)), [2]),
    ("accept-row-on-refused", lambda c: (
        _p(c, state="refused", resolved_at="T3"),
        _r(c, seq=1)), [3, 7]),
    ("reverse-without-prior-accept", lambda c: (
        _p(c, state="refused", resolved_at="T3"),
        _r(c, seq=1, action="reverse", applied_txn=None, reversal_txn=9)), [4, 7]),
    ("double-reversal", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),
        _r(c, seq=1),
        _r(c, seq=2, action="reverse", applied_txn=None, reversal_txn=9),
        _r(c, seq=3, action="reverse", applied_txn=None, reversal_txn=10)), [5, 7]),
    ("seq-gap", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),
        _r(c, seq=1),
        _r(c, seq=3, action="reverse", applied_txn=None, reversal_txn=9)), [6]),
    # round-5 F1: the grammar cases — histories legal under all six original
    # clauses (each a true negative; their conjunction was not totality) and
    # illegal under the state/action grammar. The reviewer's four, plus the
    # shapes the pre-validation added — including refused-with-zero-rows,
    # the case the clause's own FIRST DRAFT passed silently (the NULL trap
    # inside the audit that exists because of the NULL trap; COALESCE is
    # the fix and this cell is its regression).
    ("accept-then-refuse (reviewer)", lambda c: (
        _p(c, state="accepted", resolved_at="T3", applied_txn=7),
        _r(c, seq=1),
        _r(c, seq=2, action="refuse", applied_txn=None)), [7]),
    ("refuse-then-expire (reviewer)", lambda c: (
        _p(c, state="refused", resolved_at="T3"),
        _r(c, seq=1, action="refuse", applied_txn=None),
        _r(c, seq=2, action="expire", applied_txn=None)), [7]),
    ("duplicate-refuse (reviewer)", lambda c: (
        _p(c, state="refused", resolved_at="T3"),
        _r(c, seq=1, action="refuse", applied_txn=None),
        _r(c, seq=2, action="refuse", applied_txn=None)), [7]),
    ("rows-on-open (reviewer)", lambda c: (
        _p(c),
        _r(c, seq=1, action="refuse", applied_txn=None)), [7]),
    ("expired-with-refuse-row", lambda c: (
        _p(c, state="expired", resolved_at="T3"),
        _r(c, seq=1, action="refuse", applied_txn=None)), [7]),
    ("refused-no-rows (the NULL-trap cell)", lambda c: (
        _p(c, state="refused", resolved_at="T3"),), [7]),
]


@pytest.mark.parametrize("case,builder,expect",
                         GATE_HISTORIES, ids=[h[0] for h in GATE_HISTORIES])
def test_resolution_ledger_gate(case, builder, expect):
    """Round-4 F2: the gate §4b cited for two rounds EXISTED NOWHERE — the
    phantom-citation class in our own spec. Now it is fenced SQL in §6a,
    extracted here at test time, and FIRED: a legal multi-proposal history
    returns zero rows from every SELECT, and each violation history — legal
    per-row, illegal per-table, which is exactly what a row CHECK cannot see
    — trips exactly its clause. A gate that has never fired is a comment
    (rule zero, applied to the gate itself)."""
    conn = _fresh_history(builder)
    fired = _audit(conn)
    # EXACT equality, not membership: each history was built to violate one
    # clause and satisfy the rest, so a second clause firing means either the
    # history or a clause drifted — both worth failing on.
    assert fired == expect, \
        f"{case}: expected clauses {expect} to fire, got {fired}"
    conn.close()


# ---------- round-4 F4: the connection-path inventory-completeness sweep

import sys as _sys
_sys.path.insert(0, str(SPEC.parents[1] / "specs" / "evidence" / "0031"))
from connection_census import (ALLOWED_ATTRS,  # noqa: E402
                               connect_census as _connect_census)


def test_connection_path_inventory_is_complete():
    """The sweep §4b-ii names (labeled as a SWEEP, not behavior evidence):
    every `sqlite3.connect` call site under src/veracium must be accounted
    for by the spec's inventory table — per-file site COUNTS are compared,
    so a new site (new file, or an extra call in a known file) fails until
    the inventory and the factory obligation cover it, while line-number
    drift from unrelated edits does not false-fail. The classifier
    criterion in the spec (:memory: => scratch; anything else => file-backed,
    owed the factory, no third class) tells the person who lands here what
    to do with the new site."""
    import collections
    root = SPEC.parents[1] / "src" / "veracium"
    live = collections.Counter()
    for py in sorted(root.rglob("*.py")):
        rel = str(py.relative_to(root))
        for key, n in _connect_census(py.read_text(), rel).items():
            live[key] += n
    spec_text = SPEC.read_text()
    expected = {}
    for line in spec_text.splitlines():
        mrow = re.match(r"\| `store/([a-z_]+\.py):\d+", line)
        if mrow:
            # every `:NNN` on the row is one cited call site in that file
            expected[f"store/{mrow.group(1)}"] = len(re.findall(r":\d+", line))
    assert expected, "the spec's inventory table was not found"
    assert dict(live) == expected, (
        f"connection sites drifted from the spec inventory:\n"
        f"  live: {dict(live)}\n  spec: {expected}\n"
        f"Classify the new site by the criterion in §4b-ii and update the "
        f"inventory (and the factory obligation) in the same commit.")


def test_dynamic_sqlite_acquisition_is_refused__controls():
    """Round-5 F2's permanent negatives, run through the REAL census on
    synthetic sources — so "the check was hardened" is carried by a test
    containing the evading construction, never by a README sentence. The
    FIRST cell is the exact original mutant, verbatim."""
    hits = _connect_census(
        'def f(p): return __import__("sqlite3").connect(p)\n', "x.py")
    assert any("dynamic acquisition of sqlite3" in k for k in hits), hits
    hits = _connect_census(
        'import importlib\n'
        'def f(): return importlib.import_module("sqlite3")\n', "x.py")
    assert any("dynamic acquisition of sqlite3" in k for k in hits), hits
    hits = _connect_census(
        'import importlib\n'
        'def f(name): return importlib.import_module(name)\n', "x.py")
    assert any("non-literal dynamic import" in k for k in hits), hits
    # scoped: a literal, unrelated dynamic import is NOT refused (the shipped
    # __import__("re") at schema.py:85 must keep passing)
    hits = _connect_census('_re = __import__("re")\n', "x.py")
    assert hits == {}, hits


def test_surrogate_text_raises_through_the_driver__mechanism(db):
    """Round-5 F3's mechanism, kept executable per externally-supplied
    string class: a lone surrogate passes isinstance(str) and RAISES
    UnicodeEncodeError from the sqlite3 driver at binding — before any
    CHECK can run, which is why the DDL structurally cannot own this and
    the schedules' preamble must (the spec's ownership row): the accepted
    text domain is str-that-encodes-as-valid-UTF-8, validated BEFORE
    binding with a typed refusal. isinstance names the TYPE; UTF-8 names
    the DOMAIN — the type-vs-domain recursion, in text this time."""
    for cls, over in [
        ("id", dict(id="\ud800")),
        ("target_edge_id", dict(target_edge_id="\udfff")),
        ("evidence_ref", dict(evidence_ref="\ud800")),
        ("note", dict(note="ok\udc00")),
        ("payload", dict(correction_payload='{"o":"\ud800"}')),
        ("created_at", dict(created_at="\ud800")),
    ]:
        assert isinstance(list(over.values())[0], str)   # passes the TYPE
        with pytest.raises(UnicodeEncodeError):
            _insert(db, "mcp_proposal", BASE, **over)    # fails the DOMAIN
    # resolver, on the resolution table
    _insert(db, "mcp_proposal", BASE)
    with pytest.raises(UnicodeEncodeError):
        _insert(db, "mcp_proposal_resolution", RBASE, resolver="\ud800")


def test_captured_connect_reference_is_refused__controls():
    """Round-6 F1's permanent negatives — the reviewer's EXACT construction
    first, verbatim: the round-5 census recognized sqlite3.connect only as
    the called expression, so the connect function escaping into a variable
    opened an unclassified persistent connection (same completeness class
    as round 5, ordinary spelling — the reviewer planted it under
    src/veracium and the inventory test passed). Conservative closure by
    parenthood: any non-call reference to sqlite3.connect refuses, and a
    bare sqlite3 name escaping attribute access refuses (getattr and
    module-passing, the next spellings over, refused before planting)."""
    hits = _connect_census(
        "import sqlite3\n"
        "def open_store(path):\n"
        "    opener = sqlite3.connect\n"
        "    return opener(path)\n", "x.py")
    assert any("referenced without being called" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3\n"
        "def f(path):\n"
        "    return getattr(sqlite3, 'connect')(path)\n", "x.py")
    assert any("bare sqlite3 module reference" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3\n"
        "def f(opener_factory):\n"
        "    return opener_factory(sqlite3)\n", "x.py")
    assert any("bare sqlite3 module reference" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3\n"
        "def f(path):\n"
        "    return sqlite3.connect(path)\n", "x.py")
    assert hits == {"x.py": 1}, hits          # the direct call still counts
    hits = _connect_census(
        "import sqlite3\n"
        "def f(e):\n"
        "    return isinstance(e, sqlite3.IntegrityError)\n", "x.py")
    assert hits == {}, hits                   # non-connect attributes legal


def test_connection_constructors_and_submodules_refuse__controls():
    """Round-7 F1's permanent negatives, the reviewer's two EXECUTED bypasses
    verbatim first: the constructor makes usable connections and the
    round-6 rule waved it through as a harmless non-connect attribute; the
    dbapi2 submodule re-exports the whole surface under a second name. The
    surface is now POSITIVE: connect (direct call only), Connection
    (annotation position only), ALLOWED_ATTRS, nothing else."""
    hits = _connect_census(
        "import sqlite3\n"
        "def open_store(path):\n"
        "    return sqlite3.Connection(path)\n", "x.py")
    assert any("constructed directly" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3.dbapi2\n"
        "def open_store(path):\n"
        "    return sqlite3.dbapi2.connect(path)\n", "x.py")
    assert any("submodule import" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3\n"
        "opener = sqlite3.Connection\n", "x.py")
    assert any("captured outside annotation" in k for k in hits), hits
    hits = _connect_census(
        "import sqlite3\n"
        "x = sqlite3.mystery_attr\n", "x.py")
    assert any("unclassified sqlite3 attribute" in k for k in hits), hits
    # POSITIVE CONTROLS — the reviewer's named legitimate uses stay legal:
    hits = _connect_census(
        "import sqlite3\n"
        "def f(conn: sqlite3.Connection) -> sqlite3.Connection:\n"
        "    row = sqlite3.Row\n"
        "    try:\n        pass\n"
        "    except sqlite3.IntegrityError:\n        pass\n"
        "    return conn\n", "x.py")
    assert hits == {}, hits
    hits = _connect_census(
        "import sqlite3\nsqlite3.connect(':memory:')\n", "x.py")
    assert hits == {"x.py": 1}, hits


def test_every_runtime_opener_spelling_is_refused__matrix():
    """The reviewer's matrix ask, DERIVED FROM THE RUNTIME rather than
    enumerated: every attribute of the running sqlite3 module (one
    submodule level included) whose value IS the connect function or the
    Connection class is an opener spelling; each must refuse through the
    census except the one blessed direct call. A future stdlib re-export
    fails this test loudly instead of quietly widening the surface."""
    import sqlite3 as _sq
    import types
    spellings = []
    for name in dir(_sq):
        val = getattr(_sq, name)
        if val is _sq.connect or val is _sq.Connection:
            spellings.append((f"sqlite3.{name}",
                              f"import sqlite3\nx = sqlite3.{name}(p)\n"))
        elif isinstance(val, types.ModuleType) and not name.startswith("_"):
            for sub in dir(val):
                sval = getattr(val, sub, None)
                if sval is _sq.connect or sval is _sq.Connection:
                    spellings.append(
                        (f"sqlite3.{name}.{sub}",
                         f"import sqlite3.{name}\n"
                         f"x = sqlite3.{name}.{sub}(p)\n"))
    assert len(spellings) >= 4, \
        f"the runtime matrix collapsed — expected connect/Connection x " \
        f"top-level/dbapi2 at least, found {spellings}"
    for spelling, src in spellings:
        hits = _connect_census(src, "x.py")
        if spelling == "sqlite3.connect":
            assert hits == {"x.py": 1}, (spelling, hits)   # the blessed call
        else:
            assert any("REFUSED" in k for k in hits), \
                f"opener spelling {spelling} passed the census silently"


def test_evaluated_annotation_acquisition_is_refused__controls():
    """Round-8 F1 — THE EIGHTH RUNG, found exactly where attack point #4
    invited: the round-7 exemption tested annotation LOCATION, not
    type-reference STRUCTURE, and annotations are ordinary expressions
    evaluated at def time — the reviewer's probe opened a REAL connection
    that lived in f.__annotations__. Calls are now processed BEFORE the
    exemption (their safer formulation, taken exactly), and the exemption
    admits only non-executing type-reference structure. The battery: the
    reviewer's construction verbatim, the return-annotation and
    annotated-assignment variants they asked for, and the NEXT mutant —
    Connection passed as an ARGUMENT to an evaluating callee inside an
    annotation — refused before anyone plants it. Positive controls: the
    bare, subscripted, and union type references stay legal."""
    for label, src in [
        ("reviewer-param", 'import sqlite3\n'
         'def f(value: sqlite3.Connection(":memory:")):\n    pass\n'),
        ("return-annotation", 'import sqlite3\n'
         'def f() -> sqlite3.Connection("x"):\n    pass\n'),
        ("annassign", 'import sqlite3\nx: sqlite3.Connection("x") = None\n'),
        ("passed-to-callee", 'import sqlite3\n'
         'def f(v: make(sqlite3.Connection)):\n    pass\n'),
    ]:
        hits = _connect_census(src, "x.py")
        assert any("REFUSED" in k for k in hits), (label, hits)
    for label, src in [
        ("bare", 'import sqlite3\n'
         'def f(c: sqlite3.Connection) -> sqlite3.Connection:\n    pass\n'),
        ("subscript", 'import sqlite3\nfrom typing import Optional\n'
         'def f(c: Optional[sqlite3.Connection]):\n    pass\n'),
        ("union", 'import sqlite3\ndef f(c: sqlite3.Connection | None):\n'
         '    pass\n'),
    ]:
        hits = _connect_census(src, "x.py")
        assert hits == {}, (label, hits)
