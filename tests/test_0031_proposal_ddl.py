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
                               ATTRIBUTE_CLASSES,
                               SRC_ATTRIBUTE_PARTITION,
                               SRC_ATTRIBUTE_TOTAL,
                               SRC_DATA_DUNDERS_IN_DATAFLOW,
                               CAPABILITY_DISCOVERY_FORMS,
                               GETATTR_ALLOWANCES,
                               attribute_census as _attribute_census,
                               connect_census as _connect_census,
                               getattr_census as _getattr_census)


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
    assert any("dynamic acquisition of a protected module" in k
               for k in hits), hits
    hits = _connect_census(
        'import importlib\n'
        'def f(): return importlib.import_module("sqlite3")\n', "x.py")
    assert any("dynamic acquisition of a protected module" in k
               for k in hits), hits
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


def test_string_annotations_apply_the_surface_recursively__controls():
    """Round-9 F1 — THE NINTH RUNG, found where the round-9 attack point #2
    pointed: a STRING annotation deferred the constructor past the census
    (the reviewer evaluated it with get_type_hints into a live connection
    that answered SELECT 1). The positive surface now applies RECURSIVELY
    into parsed string annotations, and strings whose safety cannot be
    established FAIL CLOSED — their full required battery: the exact
    deferred constructor, all three annotation forms, the
    nested-evaluator string, string equivalents of the three legal type
    references, malformed, and dynamically assembled."""
    refused_cases = [
        ("reviewer-deferred-constructor",
         'import sqlite3\n'
         'def f(value: "sqlite3.Connection(\':memory:\')"):\n    pass\n'),
        ("string-return-form",
         'import sqlite3\ndef f() -> "sqlite3.Connection(\'x\')":\n    pass\n'),
        ("string-annassign-form",
         'import sqlite3\nx: "sqlite3.Connection(\'x\')" = None\n'),
        ("string-nested-evaluator",
         'import sqlite3\ndef f(v: "make(sqlite3.Connection)"):\n    pass\n'),
        ("malformed-mentioning-sqlite3",
         'import sqlite3\ndef f(c: "sqlite3.Connection("):\n    pass\n'),
        ("assembled-f-string",
         'import sqlite3\ndef f(c: f"sqlite3.{name}"):\n    pass\n'),
    ]
    for label, src in refused_cases:
        hits = _connect_census(src, "x.py")
        assert any("REFUSED" in k for k in hits), (label, hits)
    legal_cases = [
        ("string-bare", 'import sqlite3\ndef f(c: "sqlite3.Connection"):\n'
         '    pass\n'),
        ("string-subscript",
         'import sqlite3\ndef f(c: "Optional[sqlite3.Connection]"):\n'
         '    pass\n'),
        ("string-union",
         'import sqlite3\ndef f(c: "sqlite3.Connection | None"):\n    pass\n'),
        ("unrelated-string", 'import sqlite3\ndef f(c: "np.ndarray"):\n'
         '    pass\n'),
    ]
    for label, src in legal_cases:
        hits = _connect_census(src, "x.py")
        assert hits == {}, (label, hits)


def test_acquisition_is_classified_by_provenance_not_spelling__controls():
    """Round-10 F1 — THE TENTH RUNG, found where the round-10 attack point
    #2 pointed: the string-annotation recursion was ENTERED on the
    contiguous substring "sqlite3", so the underscore C module acquired
    connections invisibly (the reviewer's three variants, each census-{}
    and runtime-live). The census now classifies by IMPORT PROVENANCE
    against the structured PROTECTED_MODULES table: _sqlite3 refuses in
    EVERY position; protected from-import aliases are tracked so a name
    like C retains the identity of _sqlite3.Connection inside parsed
    strings; EVERY string annotation is parsed regardless of spelling;
    unparseable and assembled strings fail closed with no trigger; and a
    computed dynamic import in a deferred expression refuses because the
    module cannot be ruled out. Their full required battery, plus the
    round-9 exact construction as the regression anchor."""
    refused = [
        ("direct-_sqlite3-Connection",
         "import _sqlite3\ndef f(p):\n    return _sqlite3.Connection(p)\n"),
        ("imported-_sqlite3-alias-called",
         "from _sqlite3 import Connection as C\ndef f(p):\n    return C(p)\n"),
        ("alias-in-param-string",
         "from _sqlite3 import Connection as C\n"
         "def f(v: \"C(':memory:')\"):\n    pass\n"),
        ("alias-in-return-string",
         "from _sqlite3 import Connection as C\n"
         "def f() -> \"C('x')\":\n    pass\n"),
        ("alias-in-annassign-string",
         "from _sqlite3 import Connection as C\nx: \"C('x')\" = None\n"),
        ("composed-module-in-string",
         "def f(v: \"__import__('sql'+'ite3').connect(':memory:')\"):\n"
         "    pass\n"),
        ("alias-passed-to-evaluator-in-string",
         "from _sqlite3 import Connection as C\ndef f(v: \"make(C)\"):\n"
         "    pass\n"),
        ("round-9-exact-regression",
         'import sqlite3\n'
         'def f(value: "sqlite3.Connection(\':memory:\')"):\n    pass\n'),
    ]
    for label, src in refused:
        hits = _connect_census(src, "x.py")
        assert any("REFUSED" in k for k in hits), (label, hits)
    legal = [
        ("unrelated-forward-ref", 'def f(c: "np.ndarray"):\n    pass\n'),
        ("bare-string-ref",
         'import sqlite3\ndef f(c: "sqlite3.Connection"):\n    pass\n'),
        ("subscript-string",
         'import sqlite3\ndef f(c: "Optional[sqlite3.Connection]"):\n'
         '    pass\n'),
        ("union-string",
         'import sqlite3\ndef f(c: "sqlite3.Connection | None"):\n'
         '    pass\n'),
    ]
    for label, src in legal:
        hits = _connect_census(src, "x.py")
        assert hits == {}, (label, hits)


@pytest.mark.skipif(_sys.version_info < (3, 12),
                    reason="the `type` statement is a SyntaxError below "
                           "3.12 — the census cannot see a position the "
                           "parser refuses to build (availability is a "
                           "parser fact; the 3.12 CI lane executes these)")
def test_type_alias_values_are_annotation_positions__controls():
    """Pre-round-11 red-team (research's pass, the batch rule working):
    the 3.12 `type` statement's VALUE was absent from the annotation-
    position model — a TWO-SIDED finding, the signature of a missing
    position: T1 `type T = "sqlite3.Connection(':memory:')"` sailed
    through silently (the string-bearing position the round-10 entry
    grammar never visited), while T3 `type T = sqlite3.Connection` — the
    LEGITIMATE alias form the exemption exists to permit — false-fired
    as "captured outside annotation position". A position missing from
    the model is under- AND over-protective at once. The fix admits
    TypeAlias values (and 3.12 type-parameter bounds, the next mutant,
    claimed preemptively) into the SAME annotation-position rules:
    exempt as a reference, parsed as a string, refused as a call."""
    refused = [
        ("T1-string-in-alias-value",
         'import sqlite3\ntype T = "sqlite3.Connection(\':memory:\')"\n'),
        ("T2-direct-call-in-alias-value",
         "import sqlite3\ntype T = sqlite3.Connection(':memory:')\n"),
        ("T4-protected-alias-in-alias-string",
         'from sqlite3 import Connection as C\ntype T = "C(\':memory:\')"\n'),
        ("bound-string-on-type-statement",
         'import sqlite3\n'
         'type T[X: "sqlite3.Connection(\':memory:\')"] = int\n'),
        ("bound-string-on-function",
         'import sqlite3\n'
         'def f[X: "sqlite3.Connection(\':memory:\')"](x): pass\n'),
        ("bound-string-on-class",
         'import sqlite3\n'
         'class K[X: "sqlite3.Connection(\':memory:\')"]: pass\n'),
        ("unparseable-alias-string", 'type T = "foo bar("\n'),
        ("underscore-module-in-alias-string",
         'type T = "_sqlite3.Connection"\n'),
    ]
    for label, src in refused:
        hits = _connect_census(src, "x.py")
        assert any("REFUSED" in k for k in hits), (label, hits)
    legal = [
        ("T3-legit-alias-reference",
         "import sqlite3\ntype T = sqlite3.Connection\n"),
        ("subscripted-alias-value",
         "import sqlite3\ntype T = list[sqlite3.Connection]\n"),
        ("union-alias-value",
         "import sqlite3\ntype T = sqlite3.Connection | None\n"),
        ("legit-bound-on-function",
         "import sqlite3\ndef f[X: sqlite3.Connection](x): pass\n"),
        ("unrelated-alias-string", 'type T = "np.ndarray"\n'),
    ]
    for label, src in legal:
        hits = _connect_census(src, "x.py")
        assert hits == {}, (label, hits)


# Each probe names the CAPABILITY_DISCOVERY_FORMS entry it exercises — the
# mechanical check below refuses a form with no probe, and a probe naming
# no form (the causal-coverage move applied to module access).
CAPABILITY_DISCOVERY_PROBES = [
    ("static-import", "protected import refuses",
     "import _sqlite3\n", True),
    ("static-import", "unprotected import clean",
     "import json\n", False),
    ("dunder-import", "protected literal refuses",
     'm = __import__("sqlite3")\n', True),
    ("dunder-import", "captured __import__ refuses",
     "f = __import__\n", True),
    ("dunder-import", "unprotected literal clean (schema.py form)",
     '_re = __import__("re").compile(r"x")\n', False),
    ("import-module", "aliased from-import called refuses",
     'from importlib import import_module as im\nm = im("sqlite3")\n',
     True),
    ("import-module", "bare from-import called refuses",
     'from importlib import import_module\nm = import_module("sqlite3")\n',
     True),
    ("import-module", "captured import_module refuses",
     "import importlib\nf = importlib.import_module\n", True),
    ("import-module", "unprotected literal clean",
     'from importlib import import_module\nm = import_module("json")\n',
     False),
    ("sys-modules-registry", "THE REVIEWER'S FORM: subscript refuses",
     'import sys\nc = sys.modules["sqlite3"].connect(":memory:")\n', True),
    ("sys-modules-registry", ".get refuses",
     'import sys\nc = sys.modules.get("sqlite3")\n', True),
    ("sys-modules-registry", "through a sys alias refuses",
     'import sys as _s\nc = _s.modules["sqlite3"]\n', True),
    ("sys-modules-registry", "non-literal key refuses",
     "import sys\nc = sys.modules[name]\n", True),
    ("sys-modules-registry", "registry aliased out refuses",
     "import sys\nreg = sys.modules\n", True),
    ("sys-modules-registry", "reload-smuggle refuses at the registry",
     'import importlib, sys\n'
     'm = importlib.reload(sys.modules["sqlite3"])\n', True),
    ("sys-modules-registry", "literal unprotected key clean",
     'import sys\nm = sys.modules["json"]\n', False),
    ("sys-modules-registry", "ROUND-14 B1 (research): sys assignment-aliased then the registry refuses AT THE ESCAPE",
     'import sys\nllm = sys\nc = llm.modules["sqlite3"]\n', True),
    ("sys-modules-registry", "sys passed as an argument refuses (escaping attribute access)",
     "import sys\nf(sys)\n", True),
    ("sys-modules-registry", "sys returned refuses",
     "import sys\ndef g():\n    return sys\n", True),
    ("sys-modules-registry", "legitimate dotted uses stay clean: sys.argv, sys.stderr",
     'import sys\nprint(sys.argv, file=sys.stderr)\n', False),
    ("importlib-machinery", "bare importlib escaping refuses",
     "import importlib\nq = importlib\nm = q.import_module('sqlite3')\n", True),
    ("sys-modules-registry", "in a string annotation refuses",
     'import sys\n'
     'def f(v: "sys.modules[\'sqlite3\'].Connection"):\n    pass\n', True),
    ("from-sys-modules", "the import refuses and the name refuses",
     'from sys import modules as reg\nc = reg["sqlite3"]\n', True),
    ("importlib-machinery", "importlib.util refuses",
     'import importlib\ns = importlib.util.find_spec("sqlite3")\n', True),
    ("importlib-machinery", "machinery submodule import refuses",
     "import importlib.util\n", True),
    ("importlib-machinery", "from importlib import util refuses",
     "from importlib import util\n", True),
    ("importlib-machinery", "metadata exempt by what it cannot do",
     'from importlib.metadata import version\nv = version("veracium")\n',
     False),
    ("introspective-machinery", "vars(sys) refuses",
     'import sys\nc = vars(sys)["modules"]["sqlite3"]\n', True),
    ("introspective-machinery", "getattr(sys, ...) refuses",
     'import sys\nm = getattr(sys, "modules")\n', True),
    ("introspective-machinery", "sys.__dict__ refuses",
     "import sys\nd = sys.__dict__\n", True),
    ("introspective-machinery", "ROUND-13: vars on any object refuses (receiver type not establishable)",
     "class A: pass\nd = vars(A())\n", True),
    ("introspective-machinery", "ROUND-15: a plain literal getattr on an unestablished receiver is OBJECT DATAFLOW — clean, exactly like its dotted twin (outside the claim for both forms; the inventory sweep, not the census, polices the table)",
     'x = getattr(record, "lineage", None)\n', False),
    ("introspective-machinery", "a TABLED site (semantic.py: embed.id) is clean at its own file",
     ("semantic.py", 'ident = getattr(embed, "id", None)\n'), False),
    ("introspective-machinery", "ROUND-14 red-team: a tabled receiver NAME rebound to a module refuses (the binding is what the census can establish)",
     ("__init__.py", 'import sys\nllm = sys\nx = getattr(llm, "metering_capability", None)\n'), True),
    ("introspective-machinery", "ROUND-15: an unprotected module bound to the tabled name is MODULE-PLAIN — clean, exactly like `json.metering_capability` dotted",
     ("__init__.py", 'import json\nllm = json\nx = getattr(llm, "metering_capability", None)\n'), False),
    ("introspective-machinery", "getattr on a PROTECTED module refuses (a string-named lookup is never the blessed direct call)",
     'import sqlite3\nf = getattr(sqlite3, "connect", None)\n', True),
    ("dynamic-evaluation", "eval refuses",
     'x = eval("__import__(\'sqlite3\')")\n', True),
    ("dynamic-evaluation", "exec refuses",
     'exec("import sqlite3")\n', True),
    ("dynamic-evaluation", "in a string annotation refuses",
     'def f(v: "eval(x)"):\n    pass\n', True),
    ("machinery-modules", "pkgutil refuses at the import",
     'import pkgutil\nm = pkgutil.resolve_name("sqlite3")\n', True),
    ("machinery-modules", "runpy refuses at the import",
     'import runpy\nrunpy.run_module("sqlite3")\n', True),
    ("machinery-modules", "ctypes refuses at the import",
     'import ctypes\nlib = ctypes.CDLL("libsqlite3.so")\n', True),
    ("machinery-modules", "from-import form refuses",
     "from pkgutil import resolve_name\n", True),
    ("machinery-modules", "builtins.__import__ refuses at the import",
     'import builtins\nm = builtins.__import__("sqlite3")\n', True),
    ("machinery-modules", "bare __builtins__ refuses with no import",
     'm = __builtins__["__import__"]("sqlite3")\n', True),
    ("machinery-modules", "builtins in a string annotation refuses",
     'def f(v: "builtins.__import__(\'sqlite3\')"):\n    pass\n', True),
    ("machinery-modules", "unrelated imports stay clean",
     "import json\nimport os.path\n", False),
    ("machinery-modules", "inspect refuses at the import (frames)",
     "import inspect\ng = inspect.currentframe().f_globals\n", True),
    ("machinery-modules", "pickle refuses at the import (unpickled imports)",
     "import pickle\n", True),
    ("machinery-modules", "__main__ refuses at the import",
     "import __main__\nb = __main__.__builtins__\n", True),
    # ---- round-12 F1: THE TWELFTH RUNG — namespace mappings ----
    ("namespace-mappings", "THE REVIEWER'S ROUTE: globals()['__builtins__']",
     'b = globals()["__builtins__"]\n', True),
    ("namespace-mappings", "reaching __import__ through the mapping",
     'm = globals()["__builtins__"].__import__("sqlite3")\n', True),
    ("namespace-mappings", "locals() mapping refuses",
     'b = locals()["__builtins__"]\n', True),
    ("namespace-mappings", "vars() with no argument refuses",
     'b = vars()["__builtins__"]\n', True),
    ("namespace-mappings", ".get retrieval refuses",
     'b = globals().get("__builtins__")\n', True),
    ("namespace-mappings", "mapping aliased out refuses",
     "g = globals()\n", True),
    ("namespace-mappings", "mapping passed refuses",
     "f(globals())\n", True),
    ("namespace-mappings", "non-literal key refuses",
     "x = globals()[k]\n", True),
    ("namespace-mappings", "dunder literal key refuses (facilities live there)",
     'n = globals()["__name__"]\n', True),
    ("namespace-mappings", "inside a string annotation refuses",
     'def f(v: "globals()[\'__builtins__\']"):\n    pass\n', True),
    ("namespace-mappings", "harmless non-dunder literal key clean",
     'x = globals()["config"]\n', False),
    ("namespace-mappings", "ROUND-13: vars(obj) with an argument refuses — the receiver's type is not establishable",
     "d = vars(A())\n", True),
    ("namespace-mappings", "vars(module) is the module's namespace — refuses",
     'import json\nb = vars(json)["__builtins__"]\n', True),
    # ---- round-12, the class exhausted: frame/loader introspection ----
    ("frame-introspection", "sys._getframe refuses",
     "import sys\ng = sys._getframe().f_globals\n", True),
    ("frame-introspection", "function __globals__ refuses",
     "def f(): pass\ng = f.__globals__\n", True),
    ("frame-introspection", "module __loader__ refuses",
     'import json\nm = json.__loader__.load_module("sqlite3")\n', True),
    ("frame-introspection", "__subclasses__ hunt refuses",
     "cs = object.__subclasses__()\n", True),
    ("frame-introspection", "traceback tb_frame chain refuses at tb_frame",
     "try:\n    pass\nexcept Exception as e:\n"
     "    g = e.__traceback__.tb_frame.f_globals\n", True),
    ("frame-introspection", "getattr with a dunder literal refuses",
     'import json\nl = getattr(json, "__loader__")\n', True),
    ("frame-introspection", "getattr non-literal on a module refuses",
     "import json\nx = getattr(json, name)\n", True),
    ("frame-introspection", "inside a string annotation refuses",
     'def f(v: "f.__globals__"):\n    pass\n', True),
    ("frame-introspection", "exc.__traceback__ formatting clean (the src use)",
     'import traceback\n'
     'tb = "".join(traceback.format_exception(type(exc), exc, '
     'exc.__traceback__))\n', False),
    ("frame-introspection", "ROUND-13: getattr(self, f) REFUSES — `self` is a parameter name, not a checked property",
     "class A:\n    def m(self):\n        for f in self.fields:\n"
     "            if type(getattr(self, f)) is not int: pass\n", True),
    ("frame-introspection", "ROUND-13: getattr(cls, f) refuses too — adjudicated separately, same reason",
     "class A:\n    @classmethod\n    def m(cls, f):\n        return getattr(cls, f)\n", True),
    ("frame-introspection", "ROUND-13: the unbound-method-with-a-module receiver (the reviewer's construction) refuses",
     'import json\nclass A:\n    def m(self, name):\n        return getattr(self, name)\n'
     'x = A.m(json, "__loader__")\n', True),
    ("frame-introspection", "the rewritten legitimate site (literal attribute access) stays clean",
     "class R:\n    def problems(self):\n        p = []\n"
     "        for f, val in ((\"from_version\", self.from_version),\n"
     "                       (\"to_version\", self.to_version)):\n"
     "            if type(val) is not int:\n                p.append(f)\n"
     "        return p\n", False),
    ("frame-introspection", "ROUND-15: the same literal getattr is DATAFLOW at any file — one class for both forms; the table is inventory, not classification",
     'x = getattr(llm, "metering_capability", None)\n', False),
    ("frame-introspection", "the tabled __init__.py site is clean at its own file",
     ("__init__.py", 'x = getattr(llm, "metering_capability", None)\n'), False),
    ("frame-introspection", "an __mro__ walk is inert (classes, not namespaces)",
     "b = type(x).__mro__[-1]\n", False),
    # ---- round-12, research's red-team: the two rules that close the class ----
    ("captured-primitive", "G3: getattr curried by functools.partial refuses",
     "import functools, sys\ng = functools.partial(getattr, sys)\n"
     "m = g('modules')\n", True),
    ("captured-primitive", "globals captured as a value refuses",
     "g = globals\nb = g()['__builtins__']\n", True),
    ("captured-primitive", "eval passed to map refuses",
     "r = list(map(eval, exprs))\n", True),
    ("captured-primitive", "import_module alias stored refuses",
     "from importlib import import_module as im\nf = im\n", True),
    ("captured-primitive", "a primitive as a default argument refuses",
     "def f(g=getattr):\n    return g(o, 'x')\n", True),
    ("captured-primitive", "captured inside a string annotation refuses",
     'def f(v: "partial(getattr, sys)"):\n    pass\n', True),
    ("captured-primitive", "a primitive CALLED under its own rules is clean (a tabled getattr; a harmless mapping key)",
     ("__init__.py", 'x = getattr(llm, "metering_capability", None)\n'
                     'n = globals()["config"]\n'), False),
    ("accessor-constructors", "G1: attrgetter with a dunder refuses",
     'import operator\ng = operator.attrgetter("__globals__")(f)\n', True),
    ("accessor-constructors", "from-imported attrgetter under an alias refuses",
     'from operator import attrgetter as ag\ng = ag("__globals__")(f)\n',
     True),
    ("accessor-constructors", "methodcaller with a dunder refuses",
     'import operator\nm = operator.methodcaller("__subclasses__")\n', True),
    ("accessor-constructors", "itemgetter with a dunder refuses",
     'from operator import itemgetter\ng = itemgetter("__builtins__")\n',
     True),
    ("accessor-constructors", "non-literal argument refuses",
     "import operator\ng = operator.attrgetter(name)\n", True),
    ("accessor-constructors", "inside a string annotation refuses",
     'def f(v: "operator.attrgetter(\'x\')"):\n    pass\n', True),
    ("accessor-constructors", "G2: attrgetter with a benign literal clean",
     'import operator\nk = operator.attrgetter("name")\n', False),
    ("accessor-constructors", "itemgetter with a benign literal clean",
     'from operator import itemgetter\nk = itemgetter("id")\n', False),
    ("accessor-constructors", "itemgetter on an ESCAPED mapping refuses upstream (layering)",
     'import operator\nb = operator.itemgetter("id")(globals())\n', True),
    ("namespace-mappings", "dir() is inert (names, not objects)",
     "names = dir()\n", False),
    ("dynamic-evaluation", "bare compile refuses (FunctionType runs code without exec)",
     'c = compile("import sqlite3", "", "exec")\n', True),
    ("dynamic-evaluation", "needs_recompile is not compile (the src form)",
     "if needs_recompile(store, uid, n): pass\n", False),
]


@pytest.mark.parametrize(
    "form,label,src,refused", CAPABILITY_DISCOVERY_PROBES,
    ids=[f"{f}--{l}".replace(" ", "-") for f, l, _, _ in
         CAPABILITY_DISCOVERY_PROBES])
def test_capability_discovery_form(form, label, src, refused):
    """Round-11 F1 — THE ELEVENTH RUNG: the census recognized only import
    syntax and two dynamic-import spellings, and `sys.modules["sqlite3"]`
    — the interpreter's own registry, a STANDARD alternate access form —
    obtained the capability uncounted (census {}; so did the aliased
    import_module, importlib.reload, and vars(sys)). The closure is
    STRUCTURAL, as the reviewer's feedback asked: CAPABILITY_DISCOVERY_FORMS
    enumerates every supported form with its rule, unknown machinery
    forms are rejected conservatively, and this battery carries one or
    more probes PER FORM — mechanically bound by the inventory test
    below."""
    assert form in CAPABILITY_DISCOVERY_FORMS, f"probe names unknown form {form!r}"
    rel = "x.py"
    if isinstance(src, tuple):
        rel, src = src              # a probe run AS a tabled project site
    hits = _connect_census(src, rel)
    got = any("REFUSED" in k for k in hits)
    assert got == refused, (form, label, hits)


#: Forms with NO legitimate positive example by construction (round-12's
#: "where applicable"): each is refused wholesale, so a clean probe would
#: have nothing to show. Every other form must carry BOTH directions.
NO_POSITIVE_FORMS = frozenset({"from-sys-modules"})


def test_capability_discovery_inventory_is_mechanically_checked():
    """Every CAPABILITY_DISCOVERY_FORMS entry has at least one probe, every
    form has at least one REFUSING probe, and every form outside
    NO_POSITIVE_FORMS also has at least one CLEAN probe — the reviewer's
    round-12 ask ("both a positive and negative example where
    applicable"), executable: an inventory row without both directions is
    a rule whose boundary has not been shown."""
    probed = {f for f, _, _, _ in CAPABILITY_DISCOVERY_PROBES}
    missing = set(CAPABILITY_DISCOVERY_FORMS) - probed
    assert not missing, f"inventory forms with NO probe: {sorted(missing)}"
    assert probed <= set(CAPABILITY_DISCOVERY_FORMS), (
        f"probes naming no inventory form: "
        f"{sorted(probed - set(CAPABILITY_DISCOVERY_FORMS))}")
    refusing = {f for f, _, _, r in CAPABILITY_DISCOVERY_PROBES if r}
    never_refuted = set(CAPABILITY_DISCOVERY_FORMS) - refusing
    assert not never_refuted, (
        f"inventory forms with no refusing probe: {sorted(never_refuted)}")
    clean = {f for f, _, _, r in CAPABILITY_DISCOVERY_PROBES if not r}
    no_positive = set(CAPABILITY_DISCOVERY_FORMS) - clean - NO_POSITIVE_FORMS
    assert not no_positive, (
        f"inventory forms with no CLEAN probe and not declared "
        f"NO_POSITIVE: {sorted(no_positive)}")
    assert NO_POSITIVE_FORMS <= set(CAPABILITY_DISCOVERY_FORMS)

def test_receiver_names_do_not_determine_runtime_type__control():
    """Round-13 F1 — THE THIRTEENTH RUNG, the reviewer taking attack point
    #3 exactly: the round-12 exemption for `getattr(self, name)` rested
    on `self` "not being able to be a module" — a NAMING CONVENTION. This
    test EXECUTES the reviewer's argument: an unbound method invoked with
    a module as its receiver reaches the module's loader through the very
    call the exemption blessed. Receiver names do not determine runtime
    type; a checked property does. The census now refuses non-literal
    getattr regardless of receiver name (asserted here too), and the one
    legitimate project usage was rewritten to literal access — so the
    exemption was deleted, not replaced."""
    import json

    class Holder:
        def peek(self, name):
            return getattr(self, name)

    loader = Holder.peek(json, "__loader__")      # `self` IS a module here
    assert loader is json.__loader__, "the naming convention held nothing"
    hits = _connect_census(
        "class Holder:\n    def peek(self, name):\n"
        "        return getattr(self, name)\n", "x.py")
    assert any("not a checked propert" in k or "parameter names" in k
               for k in hits), hits


def test_the_legitimate_project_site_is_literal_and_clean__control():
    """The positive half the reviewer asked for: the EXACT project usage
    the round-12 exemption existed to preserve (release_migration's
    from_version/to_version int check) now reads its two fields by
    literal attribute access — the idiom the same function already used
    two lines above for store_changed/transaction_committed — and the
    census over the shipped file is clean of any non-literal getattr."""
    src_file = (SPEC.parents[1] / "src" / "veracium" / "store"
                / "release_migration.py")
    text = src_file.read_text()
    assert 'getattr(self, f)' not in text, "the dynamic idiom is back"
    assert '("from_version", self.from_version)' in text
    hits = _connect_census(text, "store/release_migration.py")
    assert not any("REFUSED" in k for k in hits), hits


def test_sibling_exemptions_rest_on_documented_semantics__controls():
    """Round-13's lesson applied to its siblings BEFORE the reviewer has
    to: the remaining by-what-they-cannot-be exemptions (__closure__,
    __mro__, dir(), __traceback__ short of tb_frame) are each pinned to
    an EXECUTED language property, never a naming convention.

    (a) __closure__: a cell holds whatever the enclosing scope bound — a
        module included (executed) — but a closure over a PROTECTED
        module needs `m = sqlite3`, which the bare-name rule refuses at
        the binding site; the cell reaches nothing its scope could not.
    (b) __mro__: the only namespace path from a class is through
        __globals__/__dict__/__subclasses__, each refused.
    (c) dir(): strings only (executed).
    (d) __traceback__: its public attributes are EXACTLY tb_frame,
        tb_lasti, tb_lineno, tb_next (enumerated from the runtime
        object) — two ints, a traceback-or-None, and tb_frame, the one
        object-typed attribute, which refuses."""
    import json

    def outer():
        m = json

        def inner():
            return m
        return inner
    assert outer().__closure__[0].cell_contents is json     # (a) executed
    clean = _connect_census(
        "import json\ndef outer():\n    m = json\n    def inner():\n"
        "        return m\n    return inner\n"
        "x = outer().__closure__[0].cell_contents\n", "x.py")
    assert not any("REFUSED" in k for k in clean), clean
    upstream = _connect_census(
        "import sqlite3\ndef outer():\n    m = sqlite3\n"
        "    def inner():\n        return m\n    return inner\n", "x.py")
    assert any("bare sqlite3 module reference" in k for k in upstream), \
        upstream                                             # (a) refused upstream
    for src in ("import json\ng = type(json).__mro__[0].__init__.__globals__\n",
                "import json\nd = type(json).__mro__[-1].__dict__\n",
                "cs = type(x).__mro__[-1].__subclasses__()\n"):
        assert any("REFUSED" in k for k in _connect_census(src, "x.py")), src  # (b)
    assert all(isinstance(n, str) for n in dir(json))        # (c) executed
    try:
        raise ValueError("probe")
    except ValueError as e:
        tb = e.__traceback__
    public = sorted(a for a in dir(tb) if not a.startswith("_"))
    assert public == ["tb_frame", "tb_lasti", "tb_lineno", "tb_next"], public
    assert isinstance(tb.tb_lasti, int) and isinstance(tb.tb_lineno, int)
    assert tb.tb_next is None or type(tb.tb_next) is type(tb)   # (d) enumerated
    assert any("REFUSED" in k for k in _connect_census(
        "try:\n    pass\nexcept Exception as e:\n"
        "    f = e.__traceback__.tb_next.tb_frame\n", "x.py"))


def test_identical_literal_names_differ_by_receiver__control():
    """Round-14 F1 — THE FOURTEENTH RUNG, the reviewer's argument
    EXECUTED: the same literal attribute name is ordinary data on one
    receiver and a module facility on another, because a receiver can
    determine attribute results dynamically. The census cannot know
    which it faces from the name; it now allows a literal getattr ONLY
    at a site tabled with its receiver's provenance and its result's
    consumption, and refuses everywhere else."""
    import json

    class Plain:
        lineage = ["a", "b"]

    class Hostile:
        def __getattr__(self, name):
            return json                       # any name -> a module

    assert getattr(Plain(), "lineage", None) == ["a", "b"]
    assert getattr(Hostile(), "lineage", None) is json     # same name, a facility
    # ROUND-15: the census classifies BOTH forms of this access as object
    # DATAFLOW — outside its claim under either syntax — and the
    # GETATTR_ALLOWANCES sweep (not the census) inventories the getattr
    # form: at x.py the site is UNTABLED, at scope_read.py it is tabled.
    both = _attribute_census('x = getattr(record, "lineage", None)\n'
                             'y = record.lineage\n', "x.py")
    assert {c for _, _, _, c in both} == {"dataflow"}, both
    assert ("x.py", "record", "lineage") in _getattr_census(
        'x = getattr(record, "lineage", None)\n', "x.py")["__untabled__"]
    assert _getattr_census('x = getattr(record, "lineage", None)\n',
                           "scope_read.py")["__untabled__"] == ()


def test_getattr_allowances_sweep_both_directions():
    """The positive half the reviewer asked for, over EVERY retained
    project use: each GETATTR_ALLOWANCES row is observed in the shipped
    src file with exactly its tabled count (a row nobody uses is a stale
    allowance), every literal getattr the census allows is tabled (an
    untabled site would already have refused — asserted by running the
    full census over each file), and the table's files all exist. Counts
    are compared so a duplicated probe fails until the table says why."""
    import collections
    root = SPEC.parents[1] / "src" / "veracium"
    observed = collections.Counter()
    for py in sorted(root.rglob("*.py")):
        rel = str(py.relative_to(root))
        text = py.read_text()
        seen = _getattr_census(text, rel)
        assert seen.pop("__untabled__") == (), (
            f"UNTABLED literal getattr in {rel} — inventory it in "
            f"GETATTR_ALLOWANCES with its category and consumption")
        for key, n in seen.items():
            observed[key] += n
        hits = _connect_census(text, rel)
        assert not any("REFUSED" in k for k in hits), (rel, hits)
    expected = {k: v[0] for k, v in GETATTR_ALLOWANCES.items()}
    assert dict(observed) == expected, (
        f"getattr allowances drifted from src:\n  observed: {dict(observed)}"
        f"\n  tabled:   {expected}")
    for (rel, _, _), (count, category, consumption) in GETATTR_ALLOWANCES.items():
        assert (root / rel).exists(), rel
        assert count >= 1 and category and consumption


# ---------- round-15 F1: ONE semantic rule for both attribute-access forms

PAIRED_ACCESSES = [
    # (label, preamble, receiver expr, attr, expected class for BOTH forms)
    ("plain receiver, plain name -> object dataflow",
     "", "record", "lineage", "dataflow"),
    ("call receiver (a hostile instance), plain name -> object dataflow",
     "", "Hostile()", "lineage", "dataflow"),
    ("attribute receiver, plain name -> object dataflow",
     "", "self.store", "local_origin", "dataflow"),
    ("dunder name on any receiver -> refused",
     "", "record", "__dict__", "refused"),
    ("frame attribute on any receiver -> refused",
     "", "f", "__globals__", "refused"),
    ("unprotected module, plain name -> module-plain",
     "import json\n", "json", "dumps", "module-plain"),
    ("module rebound through assignment, plain name -> module-plain",
     "import json\nllm = json\n", "llm", "metering_capability",
     "module-plain"),
    ("unprotected module, dunder name -> refused",
     "import json\n", "json", "__loader__", "refused"),
    ("protected module -> module-protected",
     "import sqlite3\n", "sqlite3", "connect", "module-protected"),
    ("machinery module -> module-machinery",
     "import sys\n", "sys", "modules", "module-machinery"),
]


@pytest.mark.parametrize("label,pre,recv,attr,expected", PAIRED_ACCESSES,
                         ids=[p[0] for p in PAIRED_ACCESSES])
def test_both_attribute_forms_share_one_classification(label, pre, recv,
                                                        attr, expected):
    """Round-15 F1 — THE FIFTEENTH RUNG: the round-14 boundary between
    `getattr(obj, "a")` and `obj.a` was SYNTACTIC — both forms perform
    receiver-dependent resolution and Python enforces no distinction —
    so ONE classifier now decides both. The reviewer's required paired
    test: the same receiver and attribute through both forms receive the
    same class. The only mechanically justified difference (a non-literal
    getattr name, which dotted syntax cannot express) is tested below."""
    src = pre + f"a = getattr({recv}, {attr!r}, None)\nb = {recv}.{attr}\n"
    rows = _attribute_census(src, "x.py")
    got = {form: cls for form, r, a, cls in rows if r == recv and a == attr}
    assert set(got) == {"getattr", "dotted"}, rows
    assert got["getattr"] == got["dotted"] == expected, (label, got)
    assert expected in ATTRIBUTE_CLASSES


def test_the_one_justified_difference_is_the_non_literal_name__control():
    """The single asymmetry the classifier keeps, and why it is
    mechanical: a getattr name can be COMPUTED, which dotted syntax
    cannot express — so a non-literal name refuses (round 13) while no
    dotted access can reach that class. Asserted on the reader."""
    rows = _attribute_census("x = getattr(obj, name)\n", "x.py")
    assert rows == [("getattr", "obj", "<non-literal>", "refused")], rows
    assert not any(a == "<non-literal>" for f, _, a, _ in
                   _attribute_census("y = obj.name\n", "x.py") if f == "dotted")


def test_shared_attribute_inventory_over_src():
    """THE SHARED SEMANTIC INVENTORY (the reviewer's round-15 feedback),
    swept over the shipped source: every attribute access in
    src/veracium, both forms, falls in exactly one of the five classes;
    NO access in src is 'refused' (an untabled dunder/frame access would
    be); the module-governed classes are the ones the census's rules
    reach; and the DATAFLOW count — the bulk of an ordinary program — is
    reported as the size of what the completeness claim explicitly does
    NOT cover under either syntax. The claim is as wide as the module-
    governed classes and no wider, and it never says dotted syntax proves
    a known type."""
    import collections
    root = SPEC.parents[1] / "src" / "veracium"
    counts = collections.Counter()
    dunders = 0
    for py in sorted(root.rglob("*.py")):
        rel = str(py.relative_to(root))
        for form, recv, attr, cls in _attribute_census(py.read_text(), rel):
            assert cls in ATTRIBUTE_CLASSES, (rel, form, recv, attr, cls)
            counts[(form, cls)] += 1
            if form == "dotted" and cls == "dataflow" and attr.startswith("__"):
                dunders += 1
    assert counts[("dotted", "refused")] == 0, dict(counts)
    assert counts[("getattr", "refused")] == 0, dict(counts)
    assert counts[("getattr", "dataflow")] == sum(
        v[0] for v in GETATTR_ALLOWANCES.values()), (
        "every literal-getattr site in src is dataflow and inventoried")
    # ROUND-16 pre-dispatch refusal: the partition is asserted by EQUALITY
    # against the one constants row the spec quotes — "> 1000" certified an
    # ordinary program, not the figure we print, and the printed figure
    # went stale when the membership rule moved 96 data-dunders into
    # dataflow. A drift in either direction fails here.
    measured = {f"{form}/{cls}": n for (form, cls), n in counts.items()}
    assert measured == SRC_ATTRIBUTE_PARTITION, (
        f"the src attribute partition drifted from the quoted row:\n"
        f"  measured: {measured}\n  quoted:   {SRC_ATTRIBUTE_PARTITION}\n"
        f"Regenerate the row from the measurement and update every carrier "
        f"that quotes it (spec, README) in the same commit.")
    assert sum(counts.values()) == SRC_ATTRIBUTE_TOTAL
    assert dunders == SRC_DATA_DUNDERS_IN_DATAFLOW, dunders


def test_spec_quotes_the_measured_partition_exactly():
    """The spec's narrated figures for the shared attribute inventory are
    BOUND to the constants row the sweep asserts: every value in
    SRC_ATTRIBUTE_PARTITION (and the total, and the data-dunder count)
    appears in the spec's text, and the superseded figure appears only as
    a narrated correction. A figure quoted in prose but absent from the
    row — or a row value absent from the prose — fails here, so a
    re-measurement must reach every carrier in the same commit."""
    text = SPEC.read_text()
    for key, n in SRC_ATTRIBUTE_PARTITION.items():
        assert f"{n:,}" in text or str(n) in text, (key, n)
    # the spec narrates the DOTTED total (the figure measured before the
    # rule was designed); it is derived here from the row, never retyped
    dotted_total = sum(n for k, n in SRC_ATTRIBUTE_PARTITION.items()
                       if k.startswith("dotted/"))
    assert f"{dotted_total:,}" in text, dotted_total
    assert dotted_total + SRC_ATTRIBUTE_PARTITION["getattr/dataflow"] \
        == SRC_ATTRIBUTE_TOTAL
    assert str(SRC_DATA_DUNDERS_IN_DATAFLOW) in text
    # the stale figure survives only where it is being corrected
    for i, line in enumerate(text.splitlines(), 1):
        if "4,487" in line or "4487" in line:
            assert any(w in line.lower() for w in
                       ("supersed", "stale", "correct", "was ")), (i, line[:120])
