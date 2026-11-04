"""0048 round 2: a small runnable contract harness for §4 (A-D), with §6's planned mechanism mutants run against it.

    python contract_harness_0048.py <tree-root>

<tree-root>/src/veracium must exist: the harness imports `veracium.schema` (Edge, Provenance, EvidenceAuthor,
Volatility, ExpiryBehavior, DEFAULT_EXPIRY) for the model; N4i's baseline arm also imports `veracium.lifecycle` and
`veracium.store.sqlite`. Stdlib sqlite3 plus pydantic. No other argument is taken; a missing or wrong one is refused
(exit 2). About 40 s.

WHAT THIS IS. A MODEL of the design under review, not the implementation, in the shape of the round-1 reviewer's
isolated model. Every name in the MODEL section (`check_bound`, `ModelConfig`, `ModelStore`, `serialise_edge`,
`_write_edge_row`, `_DeferredJournal`, `expire`, `transition`, `confirm`, `redact`, ...) is THE MODEL'S OWN; none is a
name the implementation must use.
- A  `check_bound`, one validator, used by `ModelConfig` construction (`__post_init__`), by its `__setattr__` on the
     two fields (validate, then set), and by `expire()`'s entry. Construction and assignment are separate call sites
     here so that §6's "construction check removed" and "assignment check removed" are separate mutants. An `int` is
     compared exactly, before any conversion to float (v4.2, R3-03).
- B  `expire()` reads the three policy values once and validates the pair at entry, before any read of the store;
     the decayed stamp is built by `Provenance.model_validate` (defence in depth).
- C  (v4.2) `serialise_edge` serialises the edge ONCE, re-validates those captured bytes and returns them (R3-01).
     ONE write method, `ModelStore._write_edge_row`, makes every write of the edges table's `json` column: it calls
     the helper once, binds the captured bytes at the json position and journals the same bytes, at once or, for the
     redaction (`redact`), through a single-use `_DeferredJournal` (R3-02, (a′)). No writer holds the json string.
     The N4f gate checks this file's MODEL section by §4C's closed grammar, refusal over inventory: the write method
     and its deferred journal frozen by digest; the helper, the method, the journal writer and the deferred journal
     bound once and never shadowed; every json-writing SQL literal, classified by SQLite's own authorizer, in a closed
     set and used only as the write method's SQL; every non-literal SQL site on a closed allow-list; the one dynamic
     table's domain frozen; a test-time authorizer refusing an edges write prepared outside the write method. It still
     fails CLOSED by the connection's receiver (R2-01).
- D  one transition per due edge, decided from the row read INSIDE `BEGIN IMMEDIATE` (the only form from v3.3).
     The store keeps a journal (with the bytes it journaled) and counters, so N4d's snapshot covers more than the
     edges table. DECAY keeps the shipped result (R2-02, v4): `decayed` counts decay-triggered invalidations only, and
     below the floor the row as read is retired with its stored confidence unchanged. N4i checks the model against a
     fixed table AND against the tree's own `expire()` on a real store.
N4h's schedule is §6's: A paused after its listing, B commits, A resumes; the serial control runs B, then A.

WHAT A KILL MEANS HERE. Each §6 mechanism mutant is applied to the MODEL section as exact-once text replacements, and
the §6 cell named as its killer is run on the mutated model. KILLED means that cell fails there BY ITS OWN REFUSAL
and, where a case is required, that case is among the failures. Where an instance names more than one cell (the
(v4.2) write-method row: "and the deferred journal's cells"), EVERY named cell must refuse with its own required case.
This shows each cell CAN fire against the design. It is not the implementation's mutation result, which the round-1
verdict asks for "When implementation is ready".

H-01 (found by this harness, 2026-10-12; closed in v3.3). v3.2's §4D permitted "an equivalent form", a write
conditional on the whole row as read. When that write loses a race, a transition still due on the committed row is
dropped and not counted, which matches no serial order: on N4h's decay case B commits 0.225, A leaves 0.225, and the
serial control gives 0.1125. v3.3 removes the permission and adds the mutant row "a conditional write on the row as
read in place of the in-transaction read"; its MUTANT line below prints those three values.

ROUND 2'S VERDICT (2026-10-12, design ACCEPTED; folded in v4). R2-01: this file's first gate visited only attribute
calls named `execute`/`executescript` and skipped every other call, so `executemany`, an alias of `execute`,
`getattr(conn, "execute")` and `conn.cursor().executemany` each passed it while storing confidence 1.8 (the reviewer
found two, research two more). The gate now refuses any reference to the connection it does not resolve, and nine
forms are mutants of one §6 row. R2-02: the model counted every decay and stored the decayed value below the floor;
the shipped `expire()` does neither (proposals/evidence-0048/r2-verdict/r2_02_matrix.py in the research tree: 7 of 13
branches differed, all from those two mechanisms). The model now keeps the shipped meaning, and N4i holds it.

ROUND 3'S VERDICT (2026-11-03, the implementation returned for amendment; folded in v4.2, this file's round-4
update). R3-01: the helper validated one observation of a mutable edge and returned another. R3-02: the gate read a
json binding by its spelling, so an annotated rebinding, a loop target, unpacking, a named expression or a lambda
shadowing the helper each stored 1.8, and `WITH … UPDATE edges` and `UPDATE main.edges` were not classified as edges
writes. R3-03: an integer bound was converted to float before its comparison (`10**400` raised OverflowError). The
model now carries the v4.2 write site, and each new §6 row is run here. One instance goes beyond §6's list: a
trigger whose body writes edges. SQLite reports a trigger body's writes only when a statement that fires it is
prepared, never when the CREATE TRIGGER literal is, and the firing statement may be the write method's own journal
insert, so neither the literal classification nor a frame-based tripwire sees it. The model's gate refuses any
trigger or view defined in a literal, and its tripwire records any edges write a trigger makes, whatever the frame.

ROUND 4'S VERDICT (2026-11-04, the implementation returned for amendment of R4-01; this file's round-5 update; v4.3's
text is queued). R4-01 found four forms the closed grammar admitted, and asked that the contract-model gate carry the
same obligations "where relevant". Research's stage 1 found all four relevant here, statically
(proposals/evidence-0048-r5-stage1/ in the research tree):
  (a) the json slot's layout: each write-method call's `before`/`after` are tuple displays whose lengths put the
      captured bytes at the json position SQLite itself reads (derived by execution against the model's tables, with
      a moved-json control);
  (b) every connection route: beyond R2-01's receiver rule, a cursor's `.connection` and its own `.execute` (each the
      RESULT of an admitted call), and any execute-family attribute not called directly, are refused; `create_function`
      and `set_authorizer` are connection forms the rule does not resolve;
  (c) a literal SQLite cannot prepare is UNRESOLVED and refused at every SQL argument position: the classifier
      compiles each statement as `EXPLAIN <statement>` and never runs it, so honest transaction control prepares;
  (d) each non-literal allow-list entry binds its function's body, the module and class definitions that function
      reads, and the parameters its expression reads (each reviewed).
Four connection forms and six write-method forms are new mutant instances, refused by the static gate's own reason
with the write method unchanged; two new controls pass (a savepoint pair; a docstring edit outside any listed site).
Harness r6 (2026-11-04, research's read of dev's package-wide fix for S2-01) adds the accessor constructors, whose
attribute is a string (`attrgetter`, `methodcaller`, `getattr_static`, by name, attribute and import), and five more
connection forms; `blobopen` and a connection read through a parameter were already refused, and are now mutants.
Harness r7 (2026-11-04, research's recheck of 8c71f85d, R-01, and dev's class) refuses a route around the store's own
schema, statically and in the tripwire (`_route`): unqualified names resolve to temp first, so a TEMP table named edges
takes the store's reads and writes with the file untouched. Seven write-method forms are new. The rule refuses any TEMP
table in the model, so the harmless control is an ordinary literal instead.

§6 MUTANT ROWS OUTSIDE THIS MODEL (the complement, stated): the two N4c rows,
  "a copy site writing `confidence` removed from the declared table" and
  "a writer of a form the census does not see, its trigger tokens left unclassified".
They are held by the census and the tripwire (specs/evidence/0048/census_0048.py, tripwire_0048.py, and
tests/test_0048_evidence.py) over the tree, not over a model. Every other §6 mutant row is run here, a row that names
several forms once per form: R3-01's three helper bodies (3); "**for each of the declared edge writers:**" once per
model edge writer, add_edge, confirm, transition and redact (4); "**for each connection form the gate does not
resolve:**" (18); "a writer calls the helper, or the journal writer, itself" (2); R3-02's reviewer forms (7); the
(v4.2) write method's own forms (36: the trigger, round 4's six R4-01 forms and R-01's seven among them). So the MUTANT
lines number the rows run plus 2 + 3 + 17 + 1 + 6 + 35 = 64.

OUTPUT GRAMMAR (dev's test asserts on it; do not reword without telling dev):
  CONTROL <PASS|FAIL> | `<cell>`[ on a harmless variant: <variant>][ | <failing cases>]
  MUTANT <KILLED|SURVIVED|CRASHED> | <§6 mutant cell text, verbatim> | <§6 killing cell text, verbatim> | <instance> | <detail>
  TALLY: mutants <k>/<n> killed; controls <c>/<m> pass
KILLED means every named cell failed by its OWN refusal (and each required case is among its failures); an exception
that is not the cell's refusal is CRASHED, never KILLED (H-02). A CONTROL that crashes is a FAIL. Exit 0 only when
k == n, c == m and nothing crashed; 1 otherwise; 2 on a usage or harness error (a mutant anchor not matching exactly
once).
"""
# Mutation-Matrix: tests/test_0048_evidence.py::test_contract_harness_0048_counts_only_a_refusal_as_a_kill
import ast
import functools
import hashlib
import itertools
import math
import pathlib
import random
import re
import sys
import tempfile
import threading
import types

if __name__ == "__main__":                            # the MODEL section below imports the tree's schema
    if len(sys.argv) != 2 or not (pathlib.Path(sys.argv[1]) / "src" / "veracium" / "schema.py").is_file():
        print("usage: contract_harness_0048.py <tree-root>   (<tree-root>/src/veracium/schema.py must exist)",
              file=sys.stderr)
        sys.exit(2)
    sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / "src"))

# ======================================= MODEL BEGIN =======================================
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone

from veracium.schema import DEFAULT_EXPIRY, Edge, EvidenceAuthor, ExpiryBehavior, Provenance, Volatility

EXPIRY = dict(DEFAULT_EXPIRY)            # cells map SLOW -> DECAY on this copy, as §6's "DECAY mapped for the test"
BOUNDED = ("decay_factor", "confidence_floor")
MARK_TABLES = ("redacted",)              # the one dynamic table's domain, frozen by the gate


def check_bound(name, x):
    """A: a real number (int or float, never bool), 0 <= x <= 1 inclusive, a float also finite; an int is compared
    exactly, before any conversion to float (v4.2, R3-03); else ValueError naming both."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError(f"{name} must be a real number, not {x!r}")
    if isinstance(x, int):
        ok = 0 <= x <= 1
    else:
        ok = math.isfinite(x) and 0.0 <= x <= 1.0
    if not ok:
        raise ValueError(f"{name} must lie in [0, 1], not {x!r}")


class ModelConfig:
    def __init__(self, decay_factor=0.5, confidence_floor=0.3, volatility_lifetime_days=None):
        object.__setattr__(self, "_built", False)
        self.decay_factor = decay_factor
        self.confidence_floor = confidence_floor
        self.volatility_lifetime_days = volatility_lifetime_days or {
            Volatility.PERMANENT: None, Volatility.DURABLE: 730, Volatility.SLOW: 120,
            Volatility.TRANSIENT: 7, Volatility.EPHEMERAL: 1}
        self.__post_init__()

    def __post_init__(self):
        for name in BOUNDED:
            check_bound(name, getattr(self, name))
        object.__setattr__(self, "_built", True)

    def __setattr__(self, name, value):
        if name in BOUNDED and self._built:
            check_bound(name, value)
        object.__setattr__(self, name, value)


def serialise_edge(e):
    """C (v4.2, R3-01): ONE observation. The edge is serialised once, those captured bytes are re-validated (an
    instance is not revalidation: its nested model may be unvalidated), and the same bytes are returned."""
    captured = e.model_dump_json()
    Edge.model_validate_json(captured)
    return captured


DDL = """
CREATE TABLE edges (rowid INTEGER PRIMARY KEY, id TEXT NOT NULL, user_id TEXT NOT NULL, json TEXT NOT NULL,
                    UNIQUE (id, user_id));
CREATE TABLE journal (seq INTEGER PRIMARY KEY, op TEXT NOT NULL, target TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE counters (name TEXT PRIMARY KEY, n INTEGER NOT NULL);
CREATE TABLE redacted (user_id TEXT NOT NULL, target TEXT NOT NULL);
"""


class _DeferredJournal:
    """C (v4.2, R3-02): the one edge journal emitted LATER than its row write, the redaction's. Built only by
    `ModelStore._write_edge_row(..., defer=True)` over the bytes that call bound, and used only as `with ... as NAME:`.
    `emit(op)` journals those bytes, once. Leaving the block normally without having emitted raises, inside the write
    transaction, so the writer's rollback runs; an exception leaving the block is not suppressed; `emit` outside the
    block, or twice, refuses."""

    def __init__(self, store, target, captured):
        self._store, self._target, self._captured, self._state = store, target, captured, "built"

    def __enter__(self):
        if self._state != "built":
            raise RuntimeError("the deferred journal was entered twice")
        self._state = "open"
        return self

    def emit(self, op):
        if self._state != "open":
            raise RuntimeError(f"the deferred journal emitted outside its block, or twice (state {self._state})")
        self._state = "emitted"
        self._store._journal_edge(op, self._target, self._captured)

    def __exit__(self, exc_type, exc, tb):
        state, self._state = self._state, "closed"
        if exc_type is None and state != "emitted":
            raise RuntimeError("the edge row was written and its journal never emitted")
        return False


class ModelStore:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False, timeout=10)
        if not self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='edges'").fetchone():
            self.conn.executescript(DDL)

    def _journal_edge(self, op, target, captured):
        """The edge journal writer: called only by the write method and its deferred journal."""
        self.conn.execute("INSERT INTO journal (op, target, json) VALUES (?, ?, ?)", (op, target, captured))
        self.conn.execute("INSERT INTO counters (name, n) VALUES (?, 1) ON CONFLICT(name) DO UPDATE SET n = n + 1",
                          (op,))

    def _write_edge_row(self, sql, before, e, after, *, target, op=None, defer=False):
        """C (v4.2, R3-02): THE write of the edges table's json column. The helper's bytes are captured ONCE, bound at
        the json position and journaled, now or (the redaction alone) through a deferred journal."""
        if defer and op is not None:
            raise TypeError("a deferred journal takes its op at emit(), not at the write")
        captured = serialise_edge(e)
        n = self.conn.execute(sql, (*before, captured, *after)).rowcount
        if defer:
            return _DeferredJournal(self, target, captured)
        if n:
            self._journal_edge(op, target, captured)
        return n

    def _begin(self):
        self.conn.execute("BEGIN IMMEDIATE")

    def _end(self, ok):
        if ok:
            self.conn.execute("COMMIT")
        else:
            self.conn.execute("ROLLBACK")

    def add_edge(self, e):
        self._begin()
        try:
            self._write_edge_row("INSERT INTO edges (id, user_id, json) VALUES (?, ?, ?) "
                                 "ON CONFLICT(id, user_id) DO UPDATE SET json = excluded.json",
                                 (e.id, e.user_id), e, (), target=e.id, op="add")
        except BaseException:
            self._end(False)
            raise
        self._end(True)

    def read(self, eid, user_id):
        r = self.conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (eid, user_id)).fetchone()
        return None if r is None else r[0]

    def _redacted(self, eid, user_id):
        return self.conn.execute("SELECT 1 FROM redacted WHERE user_id=? AND target=?", (user_id, eid)).fetchone()

    def _mark(self, table, user_id, target):
        """The one dynamic-table write: its table is drawn from MARK_TABLES, a frozen domain."""
        if table not in MARK_TABLES:
            raise ValueError(f"{table!r} is not a mark table")
        self.conn.execute(f"INSERT INTO {table} (user_id, target) VALUES (?, ?)", (user_id, target))

    def due_candidates(self, user_id, lifetimes, now):
        out = []
        for eid, raw in self.conn.execute("SELECT id, json FROM edges WHERE user_id=? ORDER BY rowid", (user_id,)):
            e = Edge.model_validate_json(raw)
            if e.invalidated_at is None and not self._redacted(eid, user_id) and _due(e, lifetimes, now):
                out.append((eid, raw))
        return out

    def confirm(self, eid, user_id, now):
        """The overlapping operation of N4h (B): the 0008 shape, max(c, 0.9), observed now, unflagged."""
        self._begin()
        try:
            e = Edge.model_validate_json(self.read(eid, user_id))
            e.provenance = Provenance.model_validate({**e.provenance.model_dump(), "observed_at": now,
                                                      "confidence": max(e.provenance.confidence, 0.9)})
            e.needs_confirmation = False
            self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, (eid, user_id),
                                 target=eid, op="confirm")
        except BaseException:
            self._end(False)
            raise
        self._end(True)

    def redact(self, eid, user_id):
        """The deferred writer (the redaction's shape): the tombstoned row is written, a side-table write follows,
        and the journal is emitted last, inside the same transaction."""
        self._begin()
        try:
            e = Edge.model_validate_json(self.read(eid, user_id))
            e.object = "[redacted]"
            with self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, (eid, user_id),
                                      target=eid, defer=True) as pending:
                self._mark("redacted", user_id, eid)
                pending.emit("redacted")
        except BaseException:
            self._end(False)
            raise
        self._end(True)

    def transition(self, eid, user_id, policy, now, listed_raw):
        """D: one store transition per edge, decided from the row read INSIDE the write transaction. Returns the
        counter it moved, or None (no write, not counted). `listed_raw` is the listing's copy of the row; the
        transition does not decide from it (§6's mutants do)."""
        self._begin()
        try:
            raw = self.read(eid, user_id)
            e = _decide_on(raw, eid, user_id, policy, now, self)
            if e is None:
                self._end(True)
                return None
            new, counter = e
            n = self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), new, (eid, user_id),
                                     target=eid, op=counter)
        except BaseException:
            self._end(False)
            raise
        self._end(True)
        return counter if n else None


def _due(e, lifetimes, now):
    lifetime = lifetimes.get(e.volatility)
    return lifetime is not None and (now - e.provenance.observed_at).days > lifetime


def _decide_on(raw, eid, user_id, policy, now, store):
    """D steps 1-3 on the row as read: absent, inactive, redacted or not due -> None; else (new edge, counter)."""
    factor, floor, lifetimes = policy
    if raw is None or store._redacted(eid, user_id):
        return None
    e = Edge.model_validate_json(raw)
    if e.invalidated_at is not None or not _due(e, lifetimes, now):
        return None
    behaviour = EXPIRY[e.volatility]
    if behaviour == ExpiryBehavior.LAPSE:
        return _invalidated(e, now, "lapsed"), "lapsed"
    if behaviour == ExpiryBehavior.DECAY:
        # R2-02: the shipped meaning. Strictly below the floor, the row AS READ is retired, its stored confidence
        # unchanged, and counted; otherwise the decayed edge is written, and a retained decay is not counted.
        if e.provenance.confidence * factor < floor:
            return _invalidated(e, now, "decayed"), "decayed"
        e.provenance = Provenance.model_validate({**e.provenance.model_dump(),
                                                  "confidence": e.provenance.confidence * factor})
        return e, "decayed_kept"
    if e.needs_confirmation:
        return None
    e.needs_confirmation = True
    return e, "flagged_for_confirmation"


def _invalidated(e, now, reason):
    e.invalidated_at = now
    e.invalidation_reason = reason
    return e


def expire(store, user_id, config, *, now):
    """B: the policy is read ONCE and validated at entry, before the store is read; then one transition per edge."""
    factor, floor = config.decay_factor, config.confidence_floor
    lifetimes = dict(config.volatility_lifetime_days)
    check_bound("decay_factor", factor)
    check_bound("confidence_floor", floor)
    policy = (factor, floor, lifetimes)
    counts = {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}
    for eid, listed_raw in store.due_candidates(user_id, lifetimes, now):
        moved = store.transition(eid, user_id, policy, now, listed_raw)
        if moved is not None and moved != "decayed_kept":     # R2-02: `decayed` counts decay invalidations only
            counts[moved] += 1
    return counts
# ======================================== MODEL END ========================================

HERE = pathlib.Path(__file__)
U = "u1"
NOW = datetime(2026, 10, 12, tzinfo=timezone.utc)
OLD = datetime(2024, 1, 1, tzinfo=timezone.utc)
NEAR_ABOVE_1 = math.nextafter(1.0, 2.0)
NEAR_BELOW_0 = math.nextafter(0.0, -1.0)
BIG = 10 ** 400                                   # R3-03: an int no float can hold
REJECTED = (2.0, -1.0, float("nan"), float("inf"), float("-inf"), True, "0.5", NEAR_ABOVE_1, NEAR_BELOW_0, BIG, -BIG)


def _lab(v):
    """A case label: the two R3-03 integers by name, every other value by repr."""
    if type(v) is int and abs(v) == BIG:
        return "-10**400" if v < 0 else "10**400"
    return repr(v)


#: exceptions that mean the MODEL is broken (a mutant's text drifted), never that a cell detected a defect: a cell that
#: catches broadly re-raises these, so run_cell reports them as CRASHED (H-02's class, one level down)
BREAKAGE = (NameError, AttributeError, ImportError, SyntaxError)


def _strict_pairs(pairs):
    """The strict decoder (the evidence-boundary rule, tests/test_0026_relay_lexicon.py): refuse a duplicate key."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


class CellFailure(Exception):
    def __init__(self, cases):
        super().__init__("; ".join(cases))
        self.cases = cases


def model_source():
    s = HERE.read_text()
    a = s.index("# " + "=" * 39 + " MODEL BEGIN")
    b = s.index("# " + "=" * 40 + " MODEL END")
    return s[a:b]


def load(src):
    mod = types.ModuleType("model_0048")
    exec(compile(src, "<model_0048>", "exec"), mod.__dict__)
    return mod


def edge(m, eid, vol, conf, observed=OLD):
    return m.Edge(id=eid, user_id=U, subject="user", relation="works_on", object=eid, volatility=vol,
                  provenance=m.Provenance(author_of_evidence=m.EvidenceAuthor.USER, evidence_ref="ev", confidence=conf,
                                          observed_at=observed))


class Fixture:
    def __init__(self, m):
        self.m = m
        self.dir = tempfile.TemporaryDirectory()
        self.n = 0

    def store(self, name=None):
        self.n += 1
        return self.m.ModelStore(str(pathlib.Path(self.dir.name) / f"{name or self.n}.db"))

    def path(self, name):
        return str(pathlib.Path(self.dir.name) / f"{name}.db")


def snapshot(store):
    return "\n".join(store.conn.iterdump())


def decay_mapped(m):
    m.EXPIRY[m.Volatility.SLOW] = m.ExpiryBehavior.DECAY


def unmapped(m):
    m.EXPIRY.clear()
    m.EXPIRY.update(m.DEFAULT_EXPIRY)


def duck(factor=0.5, floor=0.3):
    """A duck-typed config: no validation of its own, so only B stands between it and the store."""
    from veracium.schema import Volatility as V
    return types.SimpleNamespace(decay_factor=factor, confidence_floor=floor, volatility_lifetime_days={
        V.PERMANENT: None, V.DURABLE: 730, V.SLOW: 120, V.TRANSIENT: 7, V.EPHEMERAL: 1})


def _refusal(fn, field):
    """None when fn raises a ValueError naming `field`; else why not (any other exception type is a failure, never a
    pass: R3-03's OverflowError is the case)."""
    try:
        fn()
    except ValueError as ex:
        return None if field in str(ex) else "a ValueError not naming the field"
    except BREAKAGE:
        raise
    except Exception as ex:
        return type(ex).__name__
    return "no ValueError"


def _refused(fn, kind=RuntimeError):
    """True when fn raises `kind`; False when it returns or raises anything else (BREAKAGE re-raised)."""
    try:
        fn()
    except kind:
        return True
    except BREAKAGE:
        raise
    except Exception:
        return False
    return False


# ------------------------------------------------ the §6 cells, over the model ------------------------------------------------
# Each cell is `model_<§6 test name>`, never the §6 name itself: specs/citation_debt.py resolves an accepted spec's
# cited `test_*` names to `^def test_...(` anywhere under specs/evidence/, so a model cell carrying the name would
# make the implementation's owed test read as written (found at the v4 fold, 2026-10-12). Output lines print the
# §6 name. The four deferred-journal cells carry the names of the implementation's cells for "the deferred journal's
# cells" (§6 names them only as a group).

def model_test_no_maintenance_op_raises_confidence(m, fx):
    decay_mapped(m)
    rng = random.Random(48)
    bad = []
    moved = {"lapsed": 0, "decayed": 0, "flagged_for_confirmation": 0}
    for trial in range(40):
        s = fx.store()
        vols = list(m.Volatility)
        for i in range(6):
            s.add_edge(edge(m, f"e{i}", rng.choice(vols), rng.choice((0.0, 0.3, 0.5, 0.9, 1.0, rng.random())),
                            NOW - timedelta(days=rng.choice((0, 2, 30, 200, 1000)))))
        cfg = m.ModelConfig(decay_factor=rng.choice((0.0, 0.5, 0.9, 1.0, 1, 0)), confidence_floor=rng.choice((0.0, 0.3, 1.0)))
        for run in range(rng.randint(1, 4)):
            before = {i: m.Edge.model_validate_json(s.read(f"e{i}", U)).provenance.confidence for i in range(6)}
            for key, v in m.expire(s, U, cfg, now=NOW + timedelta(days=run)).items():
                moved[key] += v
            for i in range(6):
                c = m.Edge.model_validate_json(s.read(f"e{i}", U)).provenance.confidence
                if not (c <= before[i] and 0.0 <= c <= 1.0):
                    bad.append(f"trial {trial} run {run} e{i}: {before[i]} -> {c}")
    if not all(moved.values()):                 # non-vacuity: every behaviour was exercised
        bad.append(f"a behaviour never ran: {moved}")
    if bad:
        raise CellFailure(bad[:3])


_DUCK = {"decay_factor": "factor", "confidence_floor": "floor"}


def model_test_config_bounds_are_validated(m, fx):
    """N4b: every rejected value, both fields, at construction, assignment and expire() entry (v4.2 adds ±10**400 and
    the last two arms), raises ValueError naming the field."""
    bad = []
    for f in m.BOUNDED:
        for v in REJECTED:
            for arm, fn in (("construction", lambda: m.ModelConfig(**{f: v})),
                            ("assignment", lambda: setattr(m.ModelConfig(), f, v)),
                            ("expire() entry", lambda: m.expire(fx.store(), U, duck(**{_DUCK[f]: v}), now=NOW))):
                why = _refusal(fn, f)
                if why:
                    bad.append(f"{f}={_lab(v)} at {arm}: {why}")
    if bad:
        raise CellFailure(bad)


def model_test_boundary_configs_are_still_valid(m, fx):
    bad = []
    for f in m.BOUNDED:
        for v in (0.0, 1.0, 0, 1):
            try:
                m.ModelConfig(**{f: v})
                c = m.ModelConfig()
                setattr(c, f, v)
                if getattr(c, f) != v:
                    bad.append(f"{f}={v!r} assign")
            except ValueError:
                bad.append(f"{f}={v!r}")
    if bad:
        raise CellFailure(bad)


def model_test_config_bounds_hold_on_assignment(m, fx):
    bad = []
    for f in m.BOUNDED:
        for v in REJECTED:
            c = m.ModelConfig()
            old = getattr(c, f)
            why = _refusal(lambda: setattr(c, f, v), f)
            if why:
                bad.append(f"{f}={_lab(v)} accepted ({why})")
            elif not (getattr(c, f) == old):
                bad.append(f"{f}={_lab(v)} old value lost")
    if bad:
        raise CellFailure(bad)


def model_test_decay_config_refusal_writes_nothing(m, fx):
    decay_mapped(m)
    bad = []
    configs = [("factor", v, duck(factor=v)) for v in (2.0, -1.0, float("nan"), True, "0.5")] + \
              [("floor", v, duck(floor=v)) for v in (2.0, -0.5, float("nan"))]
    for kind, v, cfg in configs:
        for empty in (False, True):
            s = fx.store()
            if not empty:                       # the TRANSIENT edge is listed first; SLOW is mapped to DECAY
                s.add_edge(edge(m, "t", m.Volatility.TRANSIENT, 0.9))
                s.add_edge(edge(m, "s", m.Volatility.SLOW, 0.9))
            before = snapshot(s)
            label = f"{kind} {v!r}{' (empty store)' if empty else ''}"
            try:
                m.expire(s, U, cfg, now=NOW)
                bad.append(f"{label}: no ValueError")
            except ValueError:
                pass
            except BREAKAGE:
                raise
            except Exception as ex:                 # e.g. the shipped TypeError for "0.5": a real N4d failure
                bad.append(f"{label}: {type(ex).__name__}")
            if snapshot(s) != before:
                bad.append(f"{label}: store changed")
    if bad:
        raise CellFailure(bad)


def model_test_a_later_failure_keeps_the_processed_prefix(m, fx):
    decay_mapped(m)
    s = fx.store()
    s.add_edge(edge(m, "t", m.Volatility.TRANSIENT, 0.9))
    s.add_edge(edge(m, "s", m.Volatility.SLOW, 0.9))
    real = s._journal_edge

    def failing(op, target, captured):
        if target == "s" and op != "add":
            raise RuntimeError("injected store failure")
        real(op, target, captured)
    s._journal_edge = failing
    bad = []
    try:
        m.expire(s, U, m.ModelConfig(), now=NOW)
        bad.append("the injected failure did not propagate")
    except RuntimeError:
        pass
    if m.Edge.model_validate_json(s.read("t", U)).invalidated_at is None:
        bad.append("the first edge's transition was not committed")
    if m.Edge.model_validate_json(s.read("s", U)).provenance.confidence != 0.9:
        bad.append("the second edge's transition was committed")
    if bad:
        raise CellFailure(bad)


def model_test_valid_decay_never_raises(m, fx):
    decay_mapped(m)
    bad = []
    for f, fl in itertools.product((0.0, 0.25, 0.5, 1.0, 0, 1), (0.0, 0.3, 1.0, 0, 1)):
        s = fx.store()
        for i, c in enumerate((0.0, 0.3, 0.9, 1.0)):
            s.add_edge(edge(m, f"e{i}", m.Volatility.SLOW, c))
        try:
            m.expire(s, U, m.ModelConfig(decay_factor=f, confidence_floor=fl), now=NOW)
            for i in range(4):
                m.Edge.model_validate_json(s.read(f"e{i}", U))
        except BREAKAGE:
            raise
        except Exception as ex:
            bad.append(f"f={f!r} floor={fl!r}: {type(ex).__name__}")
    if bad:
        raise CellFailure(bad)


# --- N4f: §4C's closed grammar over the MODEL section (v4.2), refusal over inventory --------------------------------------

HELPER, WRITE, DEFERRED, JOURNAL = "serialise_edge", "_write_edge_row", "_DeferredJournal", "_journal_edge"
#: the closed set of json-writing SQL literals (normalised), each usable only as the write method's SQL argument
WRITES = frozenset({
    "insert into edges (id, user_id, json) values (?, ?, ?) on conflict(id, user_id) do update set json = "
    "excluded.json",
    "update edges set json=? where id=? and user_id=?",
})
#: the two frozen bodies, by sha256 of ast.dump(node, include_attributes=False); an edit refuses until re-reviewed
FROZEN = {
    "ModelStore._write_edge_row": "6e4568d12ba7fef2eaea0dcd7dee4085441aab121d310033104978d8e0714c14",
    "_DeferredJournal": "aaf132fd3db92be7669bcbce89c3aa4aeedca6f47ff7195d9c27dee5874d4295",
}
#: every NON-literal SQL argument of an execute/executemany/executescript, keyed (qualname, sha256 of its ast.dump) ->
#: (occurrences, the containing function's digest, the module-level and store-class binders of every name and `self.`
#: attribute that function reads, by digest, and the parameters the expression reads). v4.2 round 5 (R4-01 (d)): a
#: changed assignment reaching a listed site, in its function or in a definition the function reads, refuses until
#: the entry is re-reviewed. The parameters, each reviewed: `__init__` reads none (DDL is a module literal, which step
#: 5 classifies statement by statement); `_write_edge_row`'s `sql` is the closed write path (every call site's `sql`
#: is a literal of WRITES, steps 4 and 5, and the method is frozen); `_mark`'s `table` is the frozen domain (every call
#: site passes a constant of MARK_TABLES, step 4, and MARK_TABLES is frozen, step 3).
NONLITERAL = {
    ('ModelStore.__init__', 'fc28ecdb9fe43ac94546fd33b959a19c4978ae60199c85a2b29802685d1ed10b'):
        (1, '1957659e8c4aba526d84676d482c8542af2597d5b2b63384c40aedefd93c399b',
         (('module DDL', '3c9f387f007ef7999ad5820f7c0e48e2b1318d82f31d05b4a959634e904298da'), ('module sqlite3', '4e97bcd5f1455d88cb504c337bc7b8a2632804c7832b2fe01592f1fc4d604744'), ),
         ()),
    ('ModelStore._mark', 'cade917bcb4632729072d16e0e895f0224ce8bc835d19d10814b273ac8e06854'):
        (1, 'bbd467a181041eeb14917c0f824ceb429d2ae37cea660eab65ebb363cf5ea2ce',
         (('module MARK_TABLES', '3ed8aba4622a3be7f8eb77664f6dc62e4aeaa0f82e900a2290e6f92668e86d15'), ),
         ('table',)),
    ('ModelStore._write_edge_row', '33f41f90a9a4e29967595c068ca002673821bcb52a03d702ab8f50612eae4c23'):
        (1, '6e4568d12ba7fef2eaea0dcd7dee4085441aab121d310033104978d8e0714c14',
         (('class _journal_edge', '9d1ff172ec2668e68751d2e35c0cf29b847939cbf6a453d2aa22815b367df085'), ('module _DeferredJournal', 'e963b0cac49c6a8591d1e05f3b9893cc9b929ecffbc4a1885f713a5d29cd3230'), ('module serialise_edge', '304cb6acea513e462d8911acf4a7b554764aaa2733ebe1e89cf2b1b9dbafbcf9'), ),
         ('sql',)),
}
MARK_DOMAIN = ("redacted",)
CONN_CALLS = ("execute", "executescript")         # the only connection methods the gate resolves
DYNAMIC = ("getattr", "setattr", "delattr", "vars", "eval", "exec", "compile", "__import__", "globals", "locals")
#: the accessor constructors: an attribute reached by a STRING, so no attribute node names it (research's read of dev's
#: package-wide fix for S2-01, 2026-11-04: `operator.attrgetter("conn.execute")(self)` passed every rule of harness r5)
ACCESSORS = ("attrgetter", "methodcaller", "getattr_static")


def _sql(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        a, b = _sql(node.left), _sql(node.right)
        return None if a is None or b is None else a + b
    return None


def _digest(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def _is_self_conn(n):
    return isinstance(n, ast.Attribute) and n.attr == "conn" and isinstance(n.value, ast.Name) and n.value.id == "self"


def _parents(tree):
    return {ch: node for node in ast.walk(tree) for ch in ast.iter_child_nodes(node)}


def _qualname(node, parent):
    names = []
    while node in parent:
        node = parent[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            names.append(getattr(node, "name", "<lambda>"))
    return ".".join(reversed(names)) or "<module>"


def _unresolved(tree):
    """R2-01: fail CLOSED by the connection's RECEIVER, not by a method name. Every reference to the store's connection
    is one the gate resolves (a direct call `self.conn.execute(...)` / `self.conn.executescript(...)`, or the one
    assignment in `ModelStore.__init__`); `sqlite3` is used only for that connection; no dynamic attribute access
    outside `ModelConfig`. Anything else (an alias, `executemany`, a cursor, `getattr`, the unbound method, the
    connection passed as an argument, `__dict__`, a second connection) is refused, never skipped."""
    parent = _parents(tree)

    def enclosing(node, kind):
        while node in parent:
            node = parent[node]
            if isinstance(node, kind):
                return node
        return None

    def in_store_init(node):
        fn, cls = enclosing(node, ast.FunctionDef), enclosing(node, ast.ClassDef)
        return fn is not None and fn.name == "__init__" and cls is not None and cls.name == "ModelStore"

    bad = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        cls = enclosing(node, ast.ClassDef)
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            bad.append(f"line {line}: sqlite3 used other than for the store's one connection (from-import)")
        elif isinstance(node, ast.Name) and node.id == "sqlite3":
            p = parent.get(node)
            call = parent.get(p)
            ok = (isinstance(p, ast.Attribute) and p.attr == "connect" and isinstance(call, ast.Call)
                  and call.func is p and isinstance(parent.get(call), ast.Assign)
                  and any(_is_self_conn(t) for t in parent[call].targets) and in_store_init(node))
            if not ok:
                bad.append(f"line {line}: sqlite3 used other than for the store's one connection")
        elif isinstance(node, ast.Attribute) and node.attr == "conn":
            p = parent.get(node)
            if not _is_self_conn(node):
                bad.append(f"line {line}: the connection reached through something other than `self`")
            elif isinstance(p, ast.Assign) and node in p.targets:
                if not in_store_init(node):
                    bad.append(f"line {line}: the connection rebound outside ModelStore.__init__")
            elif not (isinstance(p, ast.Attribute) and p.attr in CONN_CALLS and isinstance(parent.get(p), ast.Call)
                      and parent[p].func is p):
                bad.append(f"line {line}: the connection is reached in a form the gate does not resolve")
        # v4.2 round 5 (R4-01 (b); research's stage 1, B1): a cursor carries the connection (`.connection`) and its own
        # `.execute`, so the RESULT of an admitted direct call is a second route to the connection. The model uses
        # neither attribute, and an execute-family attribute is only ever the callee of a direct call.
        if isinstance(node, ast.Attribute) and node.attr in ("connection", "cursor"):
            bad.append(f"line {line}: a cursor or its connection reached (`.{node.attr}`), a route the gate does not "
                       f"resolve")
        if isinstance(node, ast.Attribute) and node.attr in ("execute", "executemany", "executescript"):
            p = parent.get(node)
            if not (isinstance(p, ast.Call) and p.func is node):
                bad.append(f"line {line}: `.{node.attr}` held, passed or returned rather than called directly")
        if (isinstance(node, ast.Name) and node.id in ACCESSORS) or (isinstance(node, ast.Attribute) and node.attr in ACCESSORS) \
                or (isinstance(node, ast.alias) and node.name.rsplit(".", 1)[-1] in ACCESSORS):
            bad.append(f"line {line}: an accessor constructor (`{getattr(node, 'id', None) or getattr(node, 'attr', None) or node.name}`), "
                       f"an attribute reached by a string")
        if cls is not None and cls.name == "ModelConfig":
            continue
        if isinstance(node, ast.Name) and node.id in DYNAMIC:
            bad.append(f"line {line}: dynamic access (`{node.id}`) outside ModelConfig")
        elif isinstance(node, ast.Attribute) and node.attr in ("__dict__", "__setattr__", "__getattribute__"):
            bad.append(f"line {line}: dynamic access (`{node.attr}`) outside ModelConfig")
    return bad


def _statements(sql):
    """Split a literal into SQLite statements by sqlite3.complete_statement (a trigger's BEGIN … END stays whole)."""
    out, buf = [], ""
    for ch in sql:
        buf += ch
        if ch == ";" and sqlite3.complete_statement(buf):
            out.append(buf)
            buf = ""
    if buf.strip():
        out.append(buf)
    return out


#: CPython's sqlite3 text for the one expected error, a statement's parameters left unbound (pinned; N is a number)
_BINDINGS = re.compile(r"Incorrect number of bindings supplied\. The current statement uses (\d+), and there are 0 "
                       r"supplied\.")


def _scratch(ddl):
    c = sqlite3.connect(":memory:", isolation_level=None)
    for st in _statements(ddl):
        if st.strip().upper().startswith("CREATE TABLE"):
            c.execute(st)
    return c


@functools.lru_cache(maxsize=None)
def _classify(sql, ddl):
    """SQLite's own reading of a literal, statement by statement, against a scratch copy of the model's tables:
    ("edges", ...) for an INSERT on edges or an UPDATE of edges.json in any database, ("trigger", ...) for a trigger or
    view defined (its body is reported only when a statement that fires it is prepared), ("unresolved", ...) when
    SQLite cannot prepare a statement. v4.2 round 5 (R4-01 (c)): each statement is COMPILED as `EXPLAIN <statement>`
    under the authorizer and never executed, so every error is a failure to prepare (a missing function, table or
    collation; a syntax error), and a failure to prepare is UNRESOLVED, never an empty classification. The one
    expected error, unbound parameters, is answered by compiling again with that many NULLs."""
    c = _scratch(ddl)
    found = set()

    def auth(action, a1, a2, db, trig):
        if (action == sqlite3.SQLITE_INSERT and a1 == "edges") or \
                (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json"):
            found.add("edges")
        if action in (sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
                      sqlite3.SQLITE_CREATE_VIEW, sqlite3.SQLITE_CREATE_TEMP_VIEW):
            found.add("trigger")
        if _route(action, a1, a2, db):
            found.add("schema-route")
        return sqlite3.SQLITE_OK
    c.set_authorizer(auth)
    for st in _statements(sql):
        try:
            try:
                c.execute("EXPLAIN " + st)
            except sqlite3.ProgrammingError as ex:
                m = _BINDINGS.fullmatch(str(ex))
                if m is None:
                    raise
                c.execute("EXPLAIN " + st, (None,) * int(m.group(1)))
        except sqlite3.DatabaseError:                    # ProgrammingError included: it subclasses DatabaseError
            found.add("unresolved")
    c.close()
    return frozenset(found)


def _route(action, a1, a2, db):
    """A route around the store's own schema, by what SQLite's authorizer reports (research's recheck of 8c71f85d, R-01, and
    dev's class): any action in a database other than main (`db` is None for most actions, and None is not another
    database; unqualified names resolve to temp first, so a TEMP table named edges takes the store's reads and writes
    with the file untouched), ATTACH or DETACH, ALTER on another database (it names the database in its first argument),
    and any PRAGMA: the model uses none, and `pragma_*` table functions report as PRAGMA too."""
    return (db is not None and db != "main") or action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH, sqlite3.SQLITE_PRAGMA) \
        or (action == sqlite3.SQLITE_ALTER_TABLE and a1 != "main")


#: the derivation's own control: json moved to the second placeholder must read as position 1 of 3
LAYOUT_CONTROL = ("UPDATE edges SET user_id=?, json=? WHERE id=?", (3, 1))


@functools.lru_cache(maxsize=None)
def _json_layout(sql, ddl):
    """(n, json_index) of a json-writing literal, by SQLite's own reading (v4.2 round 5, R4-01 (a); research's stage
    1, B4): in a scratch store of the model's tables holding one seeded row, bind valid JSON at position k and the
    seed's id everywhere else, and read whether it landed in edges.json; over every k. None unless exactly one does."""
    c = _scratch(ddl)
    c.execute("INSERT INTO edges (id, user_id, json) VALUES ('S0', 'S0', '{}')")
    try:
        c.execute("EXPLAIN " + sql)
        n = 0
    except sqlite3.ProgrammingError as ex:
        m = _BINDINGS.fullmatch(str(ex))
        n = int(m.group(1)) if m else 0
    except sqlite3.DatabaseError:
        n = 0
    hits = []
    for k in range(n):
        vals = ["S0"] * n
        vals[k] = '{"probe": %d}' % k
        c.execute("SAVEPOINT p")
        try:
            c.execute(sql, vals)
            if c.execute("SELECT count(*) FROM edges WHERE json=?", (vals[k],)).fetchone()[0]:
                hits.append(k)
        except sqlite3.DatabaseError:
            pass
        c.execute("ROLLBACK TO p")
        c.execute("RELEASE p")
    c.close()
    return (n, hits[0]) if n and len(hits) == 1 else None


def _defs(body):
    """name -> sha256 over the ast.dump of every top-level statement in `body` that binds it"""
    out = {}
    for st in body:
        names = []
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = [st.name]
        elif isinstance(st, ast.Assign):
            names = [x.id for tg in st.targets for x in ast.walk(tg) if isinstance(x, ast.Name)]
        elif isinstance(st, (ast.AnnAssign, ast.AugAssign)) and isinstance(st.target, ast.Name):
            names = [st.target.id]
        elif isinstance(st, (ast.Import, ast.ImportFrom)):
            names = [a.asname or a.name.split(".")[0] for a in st.names]
        for x in names:
            out.setdefault(x, []).append(_digest(st))
    return {k: hashlib.sha256("".join(v).encode()).hexdigest() for k, v in out.items()}


def _binding(fn, expr, mdefs, cdefs):
    """What a listed non-literal SQL site's value depends on (v4.2 round 5, R4-01 (d); research's stage 1, B3): its
    containing function's body (every local assignment); the module-level and store-class binders of every name and
    `self.` attribute the function reads; and the function's parameters the expression reads, directly or through the
    function's own assignments. -> (function digest, ((dependency, digest), ...), (parameter, ...))"""
    a = fn.args
    params = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs} | {x.arg for x in (a.vararg, a.kwarg) if x}
    local = {x.id for x in ast.walk(fn) if isinstance(x, ast.Name) and isinstance(x.ctx, (ast.Store, ast.Del))}
    deps = {}
    for x in ast.walk(fn):
        if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load) and x.id not in local | params and x.id in mdefs:
            deps[f"module {x.id}"] = mdefs[x.id]
        elif (isinstance(x, ast.Attribute) and isinstance(x.value, ast.Name) and x.value.id == "self"
              and x.attr in cdefs):
            deps[f"class {x.attr}"] = cdefs[x.attr]
    reach = {x.id for x in ast.walk(expr) if isinstance(x, ast.Name)}
    while True:                                          # the function's own assignments feeding the expression
        more = set()
        for st in ast.walk(fn):
            if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and st.value is not None:
                tgs = st.targets if isinstance(st, ast.Assign) else [st.target]
                if any(isinstance(y, ast.Name) and y.id in reach for tg in tgs for y in ast.walk(tg)):
                    more |= {y.id for y in ast.walk(st.value) if isinstance(y, ast.Name)}
        if more <= reach:
            break
        reach |= more
    return _digest(fn), tuple(sorted(deps.items())), tuple(sorted(reach & params - {"self"}))


def _closed_grammar(tree, ddl):
    """§4C's closed grammar over the MODEL section (v4.2): the static layer of N4f."""
    parent = _parents(tree)
    bad = []
    mod_defs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    store = mod_defs.get("ModelStore")
    if _json_layout(LAYOUT_CONTROL[0], ddl) != LAYOUT_CONTROL[1]:
        bad.append(f"the json-layout derivation failed its control ({LAYOUT_CONTROL[0]!r} did not read as "
                   f"{LAYOUT_CONTROL[1]})")
    # 1. the two frozen bodies
    bodies = {"_DeferredJournal": mod_defs.get(DEFERRED),
              "ModelStore._write_edge_row": next((n for n in (store.body if store else ()) if
                                                  isinstance(n, ast.FunctionDef) and n.name == WRITE), None)}
    for q, node in bodies.items():
        if node is None or _digest(node) != FROZEN[q]:
            bad.append(f"`{q}` is not its frozen body (an edit refuses until the digest is re-reviewed)")
    # 2. the names are what they say: one binder each, never an attribute, never subclassed, never declared global
    binders = {n: [] for n in (HELPER, WRITE, DEFERRED, JOURNAL, "MARK_TABLES")}
    for node in ast.walk(tree):
        found = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found = [node.name]
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            found = [node.id]
        elif isinstance(node, ast.arg):
            found = [node.arg]
        elif isinstance(node, ast.alias):
            found = [node.asname or node.name.split(".")[0]]
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            found = [node.name]
        elif isinstance(node, ast.MatchMapping) and node.rest:
            found = [node.rest]
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for x in node.names:
                if x in binders:
                    bad.append(f"line {node.lineno}: `{x}` declared {type(node).__name__.lower()}")
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, (ast.Store, ast.Del)) and node.attr in binders:
            bad.append(f"line {node.lineno}: `{node.attr}` assigned as an attribute (an instance or class shadow)")
        for x in found:
            if x in binders:
                binders[x].append(node)
        if isinstance(node, ast.ClassDef) and any(isinstance(b, ast.Name) and b.id in ("ModelStore", DEFERRED)
                                                  for b in node.bases):
            bad.append(f"line {node.lineno}: a subclass of the store or the deferred journal (`{node.name}`)")
    want = {HELPER: (tree, ast.FunctionDef), DEFERRED: (tree, ast.ClassDef), WRITE: (store, ast.FunctionDef),
            JOURNAL: (store, ast.FunctionDef), "MARK_TABLES": (tree, ast.Name)}
    for x, nodes in binders.items():
        home, kind = want[x]
        ok = len(nodes) == 1 and isinstance(nodes[0], kind) and (
            parent.get(nodes[0]) is home if kind is not ast.Name else
            isinstance(parent.get(nodes[0]), ast.Assign) and parent.get(parent[nodes[0]]) is home)
        if not ok:
            bad.append(f"`{x}` bound {len(nodes)} time(s), or not by its one definition (a shadow, a same-named "
                       f"function or a rebinding)")
    # 3. the dynamic table's domain is frozen, and every call draws from it by a constant
    for node in binders["MARK_TABLES"]:
        a = parent.get(node)
        try:
            val = ast.literal_eval(a.value) if isinstance(a, ast.Assign) else None
        except ValueError:
            val = None
        if val != MARK_DOMAIN:
            bad.append(f"the dynamic table domain `MARK_TABLES` is not its frozen value {MARK_DOMAIN}")
    # 4. the call-site grammar
    refs = {HELPER: [], DEFERRED: [], JOURNAL: [], WRITE: [], "_mark": []}
    defer_sites = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in (HELPER, DEFERRED):
            refs[node.id].append(node)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and node.attr in (JOURNAL, WRITE, "_mark"):
            refs[node.attr].append(node)
    for x, homes in ((HELPER, ["ModelStore._write_edge_row"]), (DEFERRED, ["ModelStore._write_edge_row"]),
                     (JOURNAL, ["ModelStore._write_edge_row", "_DeferredJournal.emit"])):
        where = sorted(_qualname(n, parent) for n in refs[x])
        if where != sorted(homes):
            bad.append(f"`{x}` referenced outside the write method{' and the deferred journal' if x == JOURNAL else ''},"
                       f" or more than once there ({where})")
    for n in refs["_mark"]:
        call = parent.get(n)
        if not (isinstance(call, ast.Call) and call.func is n and call.args and isinstance(call.args[0], ast.Constant)
                and call.args[0].value in MARK_DOMAIN):
            bad.append(f"line {n.lineno}: a dynamic table argument outside its frozen domain")
    for n in refs[WRITE]:
        call = parent.get(n)
        line = n.lineno
        if not (isinstance(call, ast.Call) and call.func is n and isinstance(n.value, ast.Name) and n.value.id == "self"
                and _qualname(n, parent).startswith("ModelStore.")):
            bad.append(f"line {line}: the write method reached other than by a direct `self.{WRITE}(...)` call")
            continue
        if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
            bad.append(f"line {line}: a `*` or `**` argument reaching the write method")
        if len(call.args) != 4 or _sql(call.args[0]) is None:
            bad.append(f"line {line}: the write method's SQL is not its first of four positional arguments, a literal")
        else:
            # v4.2 round 5 (R4-01 (a)): the captured bytes go to `(*before, captured, *after)`[len(before)], so the
            # json slot is the captured one only when `before` is exactly as long as SQLite's json index
            lay, b, a = _json_layout(_sql(call.args[0]), ddl), call.args[1], call.args[3]
            if lay is None:
                bad.append(f"line {line}: the write method's SQL has no single json position by SQLite's reading")
            elif not (isinstance(b, ast.Tuple) and isinstance(a, ast.Tuple)) or any(
                    isinstance(x, ast.Starred) for x in b.elts + a.elts):
                bad.append(f"line {line}: the write method's `before` and `after` are not tuple displays without `*`, "
                           f"so the json slot's layout cannot be read")
            elif len(b.elts) != lay[1] or len(b.elts) + 1 + len(a.elts) != lay[0]:
                bad.append(f"line {line}: the json slot's layout: `before` has {len(b.elts)} and `after` "
                           f"{len(a.elts)} element(s), where SQLite reads {lay[0]} parameters with json at {lay[1]}")
        for k in call.keywords:
            if k.arg == "defer":
                defer_sites.append(call)
                w = parent.get(call)
                if not (isinstance(k.value, ast.Constant) and k.value.value is True):
                    bad.append(f"line {line}: a non-constant `defer` (only `defer=True`, at one site)")
                elif not (isinstance(w, ast.withitem) and w.context_expr is call and isinstance(w.optional_vars, ast.Name)):
                    bad.append(f"line {line}: `defer=True` not used as `with ... as NAME:`")
    if len(defer_sites) > 1:
        bad.append(f"a second `defer` site ({len(defer_sites)} sites; the redaction's is the one)")
    # 5. SQL, by SQLite's reading of every literal (docstrings and bare string statements aside: they reach nothing)
    for node in ast.walk(tree):
        p = parent.get(node)
        if _sql(node) is None or isinstance(p, ast.Expr) or (isinstance(p, ast.BinOp) and _sql(p) is not None):
            continue
        kinds = _classify(_sql(node), ddl)
        norm = " ".join(_sql(node).lower().split())
        if "trigger" in kinds:
            bad.append(f"line {node.lineno}: a trigger or view defined in a literal ({norm[:50]!r}): SQLite reports its "
                       f"body's writes only when a statement firing it is prepared")
        if "schema-route" in kinds:
            bad.append(f"line {node.lineno}: a route around the store's own schema (another database, ATTACH or a PRAGMA)"
                       f" ({norm[:50]!r})")
        at_sql = (isinstance(p, ast.Call) and p.args and p.args[0] is node and isinstance(p.func, ast.Attribute)
                  and p.func.attr in ("execute", "executemany", "executescript", WRITE))
        if "unresolved" in kinds and at_sql:            # v4.2 round 5 (R4-01 (c)); a string elsewhere is prose
            bad.append(f"line {node.lineno}: an SQL literal SQLite cannot prepare, at an SQL argument position: "
                       f"unresolved, not classified ({norm[:60]!r})")
        if "edges" in kinds:
            at_write = (isinstance(p, ast.Call) and p.args and p.args[0] is node and isinstance(p.func, ast.Attribute)
                        and p.func.attr == WRITE)
            if not at_write:
                bad.append(f"line {node.lineno}: an edges-writing SQL literal outside the write method ({norm[:60]!r})")
            elif norm not in WRITES:
                bad.append(f"line {node.lineno}: an edges-writing SQL literal not in the closed set ({norm[:60]!r})")
    # 6. every non-literal SQL site is on the closed allow-list, by its function and its expression, counted, and bound
    # (v4.2 round 5, R4-01 (d)) to what determines its value: a changed assignment reaching it refuses until re-review
    mdefs, cdefs = _defs(tree.body), _defs(store.body if store else [])
    seen = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                node.func.attr in ("execute", "executemany", "executescript"):
            arg = node.args[0] if node.args else None
            if arg is None or _sql(arg) is None:
                key = (_qualname(node, parent), _digest(arg) if arg is not None else "none")
                seen[key] = seen.get(key, 0) + 1
                if key not in NONLITERAL:
                    bad.append(f"line {node.lineno}: an execute whose SQL is not a literal and not on the non-literal "
                               f"allow-list ({key[0]})")
                    continue
                fn = node
                while fn in parent and not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    fn = parent[fn]
                got = _binding(fn, arg, mdefs, cdefs) if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) else None
                if got != NONLITERAL[key][1:]:
                    bad.append(f"line {node.lineno}: a listed non-literal SQL site whose function, a definition it "
                               f"reads or a parameter it reads changed ({key[0]}): re-review it")
    for key, want in NONLITERAL.items():
        if seen.get(key, 0) != want[0]:
            bad.append(f"the non-literal site {key[0]} occurs {seen.get(key, 0)} time(s); the reviewed list says {want[0]}")
    return bad


def _runtime_arm(m, fx):
    """The test-time tripwire: an authorizer on the store's connection records every edges INSERT or edges.json UPDATE
    prepared from a stack without the write method's code object, every such write made by a trigger whatever the
    frame, and every trigger or view created, over a workload that runs every model writer."""
    hits = []
    code = m.ModelStore._write_edge_row.__code__

    def auth(action, a1, a2, db, trig):
        if action in (sqlite3.SQLITE_CREATE_TRIGGER, sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
                      sqlite3.SQLITE_CREATE_VIEW, sqlite3.SQLITE_CREATE_TEMP_VIEW):
            hits.append(f"tripwire: a trigger or view created on the store's connection (`{a1}`)")
        elif _route(action, a1, a2, db):
            hits.append(f"tripwire: a route around the store's own schema on its connection ({action}, `{a1}`, `{db}`)")
        elif ((action == sqlite3.SQLITE_INSERT and a1 == "edges") or
                (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json")) and trig is not None:
            # a trigger's write: the firing statement may be the write method's own journal insert, so its frame
            # proves nothing (dev took the same rule into the implementation's tripwire, 2026-11-03)
            hits.append(f"tripwire: an edges write made by trigger `{trig}`")
        elif (action == sqlite3.SQLITE_INSERT and a1 == "edges") or \
                (action == sqlite3.SQLITE_UPDATE and a1 == "edges" and a2 == "json"):
            f = sys._getframe(1)
            while f is not None and f.f_code is not code:
                f = f.f_back
            if f is None:
                hits.append(f"tripwire: an edges write prepared outside the write method (from "
                            f"`{sys._getframe(1).f_code.co_name}`)")
        return sqlite3.SQLITE_OK
    s = fx.store("runtime-arm")
    # statement caching OFF on the tripwire's connection: SQLite consults the authorizer when a statement is PREPARED,
    # and sqlite3 reuses a cached statement by its text without re-preparing it, so a bypass using the same SQL text
    # the write method already prepared on that connection would never be seen (found building this arm, 2026-11-03:
    # the transition and redaction bypasses survived the tripwire with the default cache of 128)
    s.conn.close()
    s.conn = sqlite3.connect(fx.path("runtime-arm"), isolation_level=None, check_same_thread=False, timeout=10,
                             cached_statements=0)
    s.conn.set_authorizer(auth)
    try:
        s.add_edge(edge(m, "a", m.Volatility.SLOW, 0.6))
        s.add_edge(edge(m, "t", m.Volatility.TRANSIENT, 0.6))
        s.confirm("a", U, NOW)
        m.expire(s, U, m.ModelConfig(), now=NOW)
        s.redact("a", U)
    except BREAKAGE:
        raise
    except Exception as ex:
        return hits + [f"runtime arm: the workload raised {type(ex).__name__}: {str(ex)[:80]}"]
    ops = {r[0] for r in s.conn.execute("SELECT op FROM journal")}
    if not {"add", "confirm", "lapsed", "redacted"} <= ops:
        hits.append(f"runtime arm: a model writer never ran (journal ops {sorted(ops)})")
    return sorted(set(hits))


def model_test_every_edge_write_goes_through_the_validating_serialiser(m, fx, src=None):
    tree = ast.parse(src)
    bad = _unresolved(tree) + _closed_grammar(tree, m.DDL) + _runtime_arm(m, fx)
    if bad:
        raise CellFailure(bad)


def model_test_the_store_refuses_an_out_of_bound_edge(m, fx):
    s = fx.store()
    s.add_edge(edge(m, "ok", m.Volatility.SLOW, 0.5))
    before = snapshot(s)
    p = m.Provenance.model_construct(author_of_evidence=m.EvidenceAuthor.USER, evidence_ref="ev", confidence=1.8, observed_at=OLD)
    e = m.Edge(id="bad", user_id=U, subject="user", relation="works_on", object="x", provenance=p)
    bad = []
    try:
        s.add_edge(e)
        bad.append("an edge carrying confidence 1.8 was accepted")
    except ValueError:
        pass
    if snapshot(s) != before:
        bad.append("the table changed")
    if bad:
        raise CellFailure(bad)


def model_test_the_store_binds_the_bytes_it_validated(m, fx):
    """N4f (v4.2, R3-01), the reviewer's schedule: validation succeeds, then a second thread replaces the edge's
    provenance with an unvalidated 1.8, and the writer commits; the stored row and every read carry 0.8. And an edge
    already carrying 1.8 is refused (so a capture never validated fails here too)."""
    bad = []
    s = fx.store()
    pre = edge(m, "pre", m.Volatility.SLOW, 0.5)
    pre.provenance = m.Provenance.model_construct(**{**dict(pre.provenance), "confidence": 1.8})
    try:
        s.add_edge(pre)
        bad.append("an edge already carrying 1.8 was accepted")
    except ValueError:
        pass
    e = edge(m, "race", m.Volatility.SLOW, 0.8)
    fired = []

    def swap():                                  # the second thread
        e.provenance = e.provenance.model_copy(update={"confidence": 1.8})

    def after(result):
        if not fired:
            fired.append(1)
            t = threading.Thread(target=swap)
            t.start()
            t.join()
        return result
    cls = m.Edge
    saved = {k: cls.__dict__[k] for k in ("model_validate_json", "model_validate") if k in cls.__dict__}
    real_json, real_obj = cls.model_validate_json.__func__, cls.model_validate.__func__
    cls.model_validate_json = classmethod(lambda c, *a, **k: after(real_json(c, *a, **k)))
    cls.model_validate = classmethod(lambda c, *a, **k: after(real_obj(c, *a, **k)))
    try:
        s.add_edge(e)
    except ValueError as ex:
        bad.append(f"the write refused ({type(ex).__name__})")
    finally:
        for k in ("model_validate_json", "model_validate"):
            if k in saved:
                setattr(cls, k, saved[k])
            else:
                delattr(cls, k)
    if not fired:
        bad.append("the helper never validated (the schedule did not happen)")
    raw = s.read("race", U)
    if raw is not None:
        stored = json.loads(raw, object_pairs_hook=_strict_pairs)["provenance"]["confidence"]
        if stored != 0.8:
            bad.append(f"stored {stored}, the helper validated 0.8")
        try:
            m.Edge.model_validate_json(raw)
        except ValueError:
            bad.append("the stored row does not read back")
    if bad:
        raise CellFailure(bad)


UPD = "UPDATE edges SET json=? WHERE id=? AND user_id=?"


def _deferred(m, fx):
    """A store holding edge "d" at 0.5, and a CHANGED copy (0.6) to write, so a rolled-back write and a committed one
    differ on disk."""
    s = fx.store()
    s.add_edge(edge(m, "d", m.Volatility.SLOW, 0.5))
    e = m.Edge.model_validate_json(s.read("d", U))
    e.provenance = m.Provenance.model_validate({**e.provenance.model_dump(), "confidence": 0.6})
    return s, e


def _in_txn(s, body):
    """body inside the store's write transaction, as a writer runs it: any exception rolls back and is re-raised."""
    s._begin()
    try:
        r = body()
    except BaseException:
        s._end(False)
        raise
    s._end(True)
    return r


def _journaled(s, eid, op):
    return s.conn.execute("SELECT json FROM journal WHERE target=? AND op=?", (eid, op)).fetchall()


def model_test_a_deferred_journal_left_unemitted_rolls_the_write_back(m, fx):
    """Leaving the block without emit, by fall-through or an early return, raises inside the transaction: the row
    write is rolled back with it."""
    bad = []
    s, e = _deferred(m, fx)
    before = snapshot(s)

    def fall_through():
        with s._write_edge_row(UPD, (), e, ("d", U), target="d", defer=True):
            pass

    def early_return():
        with s._write_edge_row(UPD, (), e, ("d", U), target="d", defer=True):
            return "left early"
    for name, body in (("fall-through", fall_through), ("early return", early_return)):
        if not _refused(lambda: _in_txn(s, body)):
            bad.append(f"{name}: no refusal")
        if snapshot(s) != before:
            bad.append(f"{name}: store changed (a row committed without its journal)")
            before = snapshot(s)
    if bad:
        raise CellFailure(bad)


def model_test_a_deferred_journal_emits_once_and_only_inside_its_block(m, fx):
    bad = []
    s, e = _deferred(m, fx)
    out = {}

    def body():
        with s._write_edge_row(UPD, (), e, ("d", U), target="d", defer=True) as p:
            p.emit("redacted")
            out["second"] = _refused(lambda: p.emit("redacted"))
        out["p"] = p
    try:
        _in_txn(s, body)
    except BREAKAGE:
        raise
    except Exception as ex:
        bad.append(f"the honest block raised {type(ex).__name__}")
    if "p" in out:
        if not out["second"]:
            bad.append("a second emit inside the block was accepted")
        if not _refused(lambda: out["p"].emit("redacted")):
            bad.append("an emit after the block was accepted")
        rows = _journaled(s, "d", "redacted")
        if rows != [(s.read("d", U),)]:
            bad.append(f"the journal holds {len(rows)} redacted row(s); want the stored bytes once")
    if not _refused(lambda: s._write_edge_row(UPD, (), e, ("d", U), target="d", op="redacted", defer=True), TypeError):
        bad.append("a deferred write accepted its op at the write")
    if bad:
        raise CellFailure(bad)


def model_test_a_deferred_journal_never_swallows_an_exception(m, fx):
    """An exception leaving the block is neither emitted for nor suppressed, so the writer's rollback runs."""
    bad = []
    s, e = _deferred(m, fx)
    before = snapshot(s)

    def body():
        with s._write_edge_row(UPD, (), e, ("d", U), target="d", defer=True):
            raise sqlite3.OperationalError("a side-table write failed")
    try:
        _in_txn(s, body)
        bad.append("the exception was swallowed (the block's failure did not propagate)")
    except sqlite3.OperationalError:
        pass
    if snapshot(s) != before:
        bad.append("store changed: a row committed without its journal")
    if bad:
        raise CellFailure(bad)


def model_test_the_redaction_journals_the_bytes_it_stored(m, fx):
    """The deferred writer end to end: the tombstoned row, its side-table mark, and ONE `redacted` journal row holding
    the stored bytes."""
    s = fx.store()
    s.add_edge(edge(m, "r", m.Volatility.SLOW, 0.5))
    try:
        s.redact("r", U)
    except BREAKAGE:
        raise
    except Exception as ex:
        raise CellFailure([f"the redaction raised {type(ex).__name__}: {ex}"])
    bad = []
    stored = s.read("r", U)
    if json.loads(stored, object_pairs_hook=_strict_pairs)["object"] != "[redacted]":
        bad.append("the row was not tombstoned")
    if not s._redacted("r", U):
        bad.append("the side-table mark is missing")
    rows = _journaled(s, "r", "redacted")
    if rows != [(stored,)]:
        bad.append(f"the journal holds {len(rows)} redacted row(s); want the stored bytes once")
    if bad:
        raise CellFailure(bad)


def model_test_factor_is_validated_whatever_the_confidence(m, fx):
    decay_mapped(m)
    bad = []
    for c, f in itertools.product((0.0, 0.3, 0.9), (2.0, NEAR_ABOVE_1, -1.0, float("nan"), True)):
        s = fx.store()
        s.add_edge(edge(m, "s", m.Volatility.SLOW, c))
        before = snapshot(s)
        listed = []
        real = s.due_candidates
        s.due_candidates = lambda *a, **k: listed.append(1) or real(*a, **k)
        label = f"{c} × {f!r}"
        try:
            m.expire(s, U, duck(factor=f), now=NOW)
            bad.append(label)
        except ValueError:
            if listed or snapshot(s) != before:
                bad.append(label)
    if bad:
        raise CellFailure(bad)


def _row(s):
    d = json.loads(s.read("e-1", U), object_pairs_hook=_strict_pairs)
    return {"confidence": round(d["provenance"]["confidence"], 9), "observed": d["provenance"]["observed_at"],
            "needs_confirmation": d["needs_confirmation"], "invalidated": d["invalidated_at"] is not None}


N4H_CASES = (  # name, volatility, observed, confidence, B's operations (on B's store)
    ("confirm", "slow", OLD, 0.6, ("confirm",)),
    ("confirm95", "slow", OLD, 0.95, ("confirm",)),
    ("lapse", "transient", NOW - timedelta(days=60), 0.6, ("confirm",)),
    ("decay", "slow", OLD, 0.9, ("expire", "expire")),
)


def model_test_expiry_is_decided_from_the_current_row(m, fx):
    bad = []
    for name, vol, observed, conf, b_ops in N4H_CASES:
        if name == "decay":
            decay_mapped(m)
        cfg = m.ModelConfig(decay_factor=0.5, confidence_floor=0.0)

        def b_run(B):
            for op in b_ops:
                B.confirm("e-1", U, NOW) if op == "confirm" else m.expire(B, U, cfg, now=NOW)
        # the serial control: B commits, THEN A runs
        S = fx.m.ModelStore(fx.path(f"{name}-serial"))
        S.add_edge(edge(m, "e-1", m.Volatility(vol), conf, observed))
        b_run(S)
        m.expire(S, U, cfg, now=NOW)
        serial = _row(S)
        # the overlap: A paused after its listing, B commits, A resumes
        A = fx.m.ModelStore(fx.path(name))
        B = fx.m.ModelStore(fx.path(name))
        A.add_edge(edge(m, "e-1", m.Volatility(vol), conf, observed))
        listed, go, out = threading.Event(), threading.Event(), {}
        real = A.due_candidates

        def paused(*a, **k):
            r = real(*a, **k)
            listed.set()
            go.wait(10)
            return r
        A.due_candidates = paused
        def a_run():
            try:
                out["A"] = m.expire(A, U, cfg, now=NOW)
            except BaseException as ex:            # surfaced below: a thread's exception is otherwise lost
                out["exc"] = ex
        t = threading.Thread(target=a_run)
        t.start()
        if not listed.wait(10):
            bad.append(f"{name}: A never reached its listing (the overlap did not happen)")
        b_run(B)
        committed = _row(B)
        go.set()
        t.join(10)
        if isinstance(out.get("exc"), BREAKAGE):
            raise out["exc"]
        if t.is_alive() or "A" not in out:
            bad.append(f"{name}: A did not complete")
        after = _row(B)
        if after != serial:
            bad.append(f"{name}: B committed {committed}, A left {after}, serial gives {serial}")
        unmapped(m)
    # the legacy-bytes control: valid, non-canonical json (keys reordered) is processed, not skipped
    s = fx.store("legacy")
    s.add_edge(edge(m, "e-1", m.Volatility.SLOW, 0.6))
    canon = json.loads(s.read("e-1", U), object_pairs_hook=_strict_pairs)
    s.conn.execute("UPDATE edges SET json=? WHERE id=?", (json.dumps(dict(reversed(list(canon.items())))), "e-1"))
    m.expire(s, U, m.ModelConfig(), now=NOW)
    if not json.loads(s.read("e-1", U), object_pairs_hook=_strict_pairs)["needs_confirmation"]:
        bad.append("legacy-bytes control: the row was skipped")
    if bad:
        raise CellFailure(bad)


N4I_CASES = (  # name, confidence, flagged, factor, floor -> the shipped result: (decayed, active, confidence, flagged)
    ("retained", 0.9, False, 0.5, 0.3, (0, True, 0.45, False)),
    ("below the floor", 0.9, False, 0.5, 0.5, (1, False, 0.9, False)),
    ("exactly at the floor", 0.6, False, 0.5, 0.3, (0, True, 0.3, False)),
    ("factor 1.0", 0.9, False, 1.0, 0.3, (0, True, 0.9, False)),
    ("factor 0, floor 0", 0.9, False, 0.0, 0.0, (0, True, 0.0, False)),
    ("factor 0, floor 0.3", 0.9, False, 0.0, 0.3, (1, False, 0.9, False)),
    ("already flagged, retained", 0.9, True, 0.5, 0.3, (0, True, 0.45, True)),
)


def _n4i_result(counts, e):
    return (counts["decayed"], e.invalidated_at is None, round(e.provenance.confidence, 9), e.needs_confirmation)


def model_test_decay_keeps_the_shipped_result(m, fx):
    """N4i (R2-02): SLOW mapped to DECAY, one due edge per case. The model's returned `decayed` count and stored
    edge equal the shipped result table; and the table is the tree's: its own `expire()` on a real store gives it too
    (the baseline arm, so the table cannot drift from what the tree does)."""
    from veracium import lifecycle
    from veracium.schema import DEFAULT_EXPIRY
    from veracium.store.sqlite import SqliteStore
    bad = []
    for name, c, flagged, f, fl, want in N4I_CASES:
        e0 = edge(m, "e", m.Volatility.SLOW, c)
        e0.needs_confirmation = flagged
        decay_mapped(m)
        s = fx.store()
        s.add_edge(e0)
        got = _n4i_result(m.expire(s, U, m.ModelConfig(decay_factor=f, confidence_floor=fl), now=NOW),
                          m.Edge.model_validate_json(s.read("e", U)))
        unmapped(m)
        if got != want:
            bad.append(f"{name}: model {got}, shipped {want}")
        saved = DEFAULT_EXPIRY[m.Volatility.SLOW]
        DEFAULT_EXPIRY[m.Volatility.SLOW] = m.ExpiryBehavior.DECAY      # as a host maps it (§2c row 4)
        try:
            st = SqliteStore(fx.path(f"n4i-{name}"))
            st.add_edge(e0)
            bc = lifecycle.expire(st, U, duck(factor=f, floor=fl), now=NOW)
            base = _n4i_result(bc, [x for x in st.edges(U, active_only=False) if x.id == "e"][0])
        finally:
            DEFAULT_EXPIRY[m.Volatility.SLOW] = saved
        if base != want:
            bad.append(f"{name}: the tree's own expire() gives {base}, the table says {want} (the table is stale)")
    if bad:
        raise CellFailure(bad)


CELLS = [model_test_no_maintenance_op_raises_confidence, model_test_config_bounds_are_validated,
         model_test_boundary_configs_are_still_valid, model_test_config_bounds_hold_on_assignment,
         model_test_decay_config_refusal_writes_nothing, model_test_a_later_failure_keeps_the_processed_prefix,
         model_test_valid_decay_never_raises, model_test_every_edge_write_goes_through_the_validating_serialiser,
         model_test_the_store_refuses_an_out_of_bound_edge, model_test_the_store_binds_the_bytes_it_validated,
         model_test_a_deferred_journal_left_unemitted_rolls_the_write_back,
         model_test_a_deferred_journal_emits_once_and_only_inside_its_block,
         model_test_a_deferred_journal_never_swallows_an_exception, model_test_the_redaction_journals_the_bytes_it_stored,
         model_test_factor_is_validated_whatever_the_confidence, model_test_expiry_is_decided_from_the_current_row,
         model_test_decay_keeps_the_shipped_result]

# ------------------------------------------------ §6's mutants ------------------------------------------------
# (§6 mutant cell, §6 killing cell, instance, required failing case(s) or None,
#  [(old, new), ...] exact-once replacements in the MODEL section[, [(cell, required case(s)), ...] when the instance
#  names its cells: every one must refuse])
ENTRY = ('    check_bound("decay_factor", factor)\n    check_bound("confidence_floor", floor)\n', "")
TXN_READ = "            raw = self.read(eid, user_id)\n            e = _decide_on"
FROM_LISTING = (TXN_READ, "            raw = listed_raw\n            e = _decide_on")
TXN_WRITE = ('            n = self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), new, (eid, user_id),\n'
             '                                     target=eid, op=counter)\n')
FLOAT_BRANCH = "        ok = math.isfinite(x) and 0.0 <= x <= 1.0\n"
HELPER_BODY = "    captured = e.model_dump_json()\n    Edge.model_validate_json(captured)\n    return captured\n"
MUTANTS = [
    ("construction check removed", "`test_config_bounds_are_validated`", "-", None,
     [("        for name in BOUNDED:\n            check_bound(name, getattr(self, name))\n", "")]),
    ("assignment check removed", "`test_config_bounds_hold_on_assignment`", "-", None,
     [("        if name in BOUNDED and self._built:\n            check_bound(name, value)\n", "")]),
    ("assignment sets before validating", "`test_config_bounds_hold_on_assignment`", "-", "old value lost",
     [("        if name in BOUNDED and self._built:\n            check_bound(name, value)\n"
       "        object.__setattr__(self, name, value)\n",
       "        object.__setattr__(self, name, value)\n"
       "        if name in BOUNDED and self._built:\n            check_bound(name, value)\n")]),
    ("exclusive bound (`0 < x < 1`)", "`test_boundary_configs_are_still_valid`", "-", None,
     [(FLOAT_BRANCH, "        ok = math.isfinite(x) and 0.0 < x < 1.0\n")]),
    ("NaN-blind comparison (`x < 0 or x > 1`)", "`test_config_bounds_are_validated`", "-", "nan",
     [(FLOAT_BRANCH, "        ok = not (x < 0.0 or x > 1.0)\n")]),
    ("`bool` accepted (no explicit refusal)", "`test_config_bounds_are_validated`", "-", "True",
     [("    if isinstance(x, bool) or not isinstance(x, (int, float)):\n",
       "    if not isinstance(x, (int, float)):\n")]),
    ("**(v4.2, R3-03)** the bound check converts an integer to float before comparing it",
     "`test_config_bounds_are_validated` (±10**400)", "-", "10**400",
     [("    if isinstance(x, int):\n        ok = 0 <= x <= 1\n    else:\n" + FLOAT_BRANCH,
       "    x = float(x)\n" + FLOAT_BRANCH.replace("        ", "    ", 1))]),
    ("the entry validation removed, B and C intact", "`test_factor_is_validated_whatever_the_confidence` (`0.3 × 2.0`)",
     "-", "0.3 × 2.0", [ENTRY]),
    ("the floor left unvalidated at entry", "`test_decay_config_refusal_writes_nothing` (floor 2.0)", "-",
     "floor 2.0", [('    check_bound("confidence_floor", floor)\n    policy', "    policy")]),
    ("the entry validation moved back inside the DECAY branch",
     "`test_decay_config_refusal_writes_nothing` (the TRANSIENT edge is lapsed first)", "-",
     "factor 2.0: store changed",
     [ENTRY, ("    if behaviour == ExpiryBehavior.DECAY:\n",
              "    if behaviour == ExpiryBehavior.DECAY:\n"
              '        check_bound("decay_factor", factor)\n        check_bound("confidence_floor", floor)\n')]),
    ("decay write back to unvalidated `model_copy`, entry check also removed",
     "`test_decay_config_refusal_writes_nothing`", "-", None,
     [ENTRY, ('        e.provenance = Provenance.model_validate({**e.provenance.model_dump(),\n'
              '                                                  "confidence": e.provenance.confidence * factor})\n',
              '        e.provenance = e.provenance.model_copy(update={"confidence": e.provenance.confidence * factor})\n')]),
    ("the store helper serialises without validating", "`test_the_store_refuses_an_out_of_bound_edge`", "-", None,
     [("    captured = e.model_dump_json()\n    Edge.model_validate_json(captured)\n    return captured\n", "    return e.model_dump_json()\n")]),
    ("the helper accepts an instance without revalidating nested data",
     "`test_the_store_refuses_an_out_of_bound_edge`", "-", None,
     [(HELPER_BODY, "    return Edge.model_validate(e).model_dump_json()\n")]),
]
R3_01 = ("**(v4.2, R3-01)** the helper validates one observation and returns another (v4.1's two-observation body); "
         "validates the capture and returns a fresh dump; returns the capture unvalidated")
for inst, need, body in (
        ("v4.1's two-observation body", "stored 1.8",
         "    Edge.model_validate(e.model_dump())\n    return e.model_dump_json()\n"),
        ("validates the capture, returns a fresh dump", "stored 1.8",
         "    captured = e.model_dump_json()\n    Edge.model_validate_json(captured)\n    return e.model_dump_json()\n"),
        ("returns the capture unvalidated", "already carrying 1.8 was accepted",
         "    captured = e.model_dump_json()\n    return captured\n")):
    MUTANTS.append((R3_01, "`test_the_store_binds_the_bytes_it_validated`", inst, need, [(HELPER_BODY, body)]))

GATE = "`test_every_edge_write_goes_through_the_validating_serialiser`"
OUTSIDE = "an edges-writing SQL literal outside the write method"
TRIP = "tripwire: an edges write prepared outside"
_I = "            "
ADD_WRITE = (f'{_I}self._write_edge_row("INSERT INTO edges (id, user_id, json) VALUES (?, ?, ?) "\n'
             '                                 "ON CONFLICT(id, user_id) DO UPDATE SET json = excluded.json",\n'
             '                                 (e.id, e.user_id), e, (), target=e.id, op="add")\n')
CONFIRM_WRITE = (f'{_I}self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, (eid, user_id),\n'
                 '                                 target=eid, op="confirm")\n')
REDACT_WRITE = (f'{_I}with self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, (eid, user_id),\n'
                '                                      target=eid, defer=True) as pending:\n'
                '                self._mark("redacted", user_id, eid)\n'
                '                pending.emit("redacted")\n')
_SQL = '"INSERT INTO edges (id, user_id, json) VALUES (?, ?, ?) ON CONFLICT(id, user_id) DO UPDATE SET json = excluded.json"'
_P = "(e.id, e.user_id, e.model_dump_json())"
_JOIN = ('"".join(["INSERT INTO ed", "ges (id, user_id, json) VALUES (?, ?, ?) ON CONFLICT(id, user_id) DO UPDATE SET '
         'json = excluded.json"])')
BYPASS = "**for each of the declared edge writers:** that writer bypasses the write method"
for inst, old, new in (
        ("add_edge", ADD_WRITE, f"{_I}self.conn.execute({_SQL}, {_P})\n"),
        ("confirm", CONFIRM_WRITE, f'{_I}self.conn.execute("UPDATE edges SET json=? WHERE id=? AND user_id=?", '
                                   f'(e.model_dump_json(), eid, user_id))\n'),
        ("transition", TXN_WRITE, f'{_I}n = self.conn.execute("UPDATE edges SET json=? WHERE id=? AND user_id=?", '
                                  f'(new.model_dump_json(), eid, user_id)).rowcount\n'),
        ("redact", REDACT_WRITE, f'{_I}self.conn.execute("UPDATE edges SET json=? WHERE id=? AND user_id=?", '
                                 f'(e.model_dump_json(), eid, user_id))\n{_I}self._mark("redacted", user_id, eid)\n')):
    MUTANTS.append((BYPASS, GATE, inst, (OUTSIDE, TRIP), [(old, new)]))
FORMS = "**for each connection form the gate does not resolve:** a writer reaches the connection that way"
for inst, need, new in (
        ("executemany", "does not resolve", f"{_I}self.conn.executemany({_SQL}, [{_P}])\n"),
        ("a bound execute alias", "does not resolve", f"{_I}_x = self.conn.execute\n{_I}_x({_SQL}, {_P})\n"),
        ("getattr(conn, 'execute')", "dynamic access", f"{_I}getattr(self.conn, 'execute')({_SQL}, {_P})\n"),
        ("cursor().executemany", "does not resolve", f"{_I}self.conn.cursor().executemany({_SQL}, [{_P}])\n"),
        ("SQL held in a variable", "not a literal", f"{_I}_q = {_SQL}\n{_I}self.conn.execute(_q, {_P})\n"),
        ("parameters held in a variable", OUTSIDE, f"{_I}_p = {_P}\n{_I}self.conn.execute({_SQL}, _p)\n"),
        ("the unbound sqlite3.Connection.execute", "sqlite3 used",
         f"{_I}sqlite3.Connection.execute(self.conn, {_SQL}, {_P})\n"),
        ("a second connection", "sqlite3 used", f"{_I}sqlite3.connect(':memory:').execute({_SQL}, {_P})\n"),
        ("the instance __dict__", "dynamic access", f"{_I}self.__dict__['conn'].execute({_SQL}, {_P})\n"),
        # v4.2 round 5 (R4-01 (b); research's stage 1, B1, B2): a cursor's connection, a cursor's own execute, each
        # called with SQL the literal rule cannot fold; and the two connection methods that change what SQL means or
        # who sees it
        ("a cursor's `.connection`, its execute held in a name (SQL by join)", "a cursor or its connection reached",
         f"{_I}_x = self.conn.execute('SELECT 1').connection.execute\n{_I}_x({_JOIN}, {_P})\n"),
        ("a cursor's own execute held in a name (SQL by join)", "held, passed or returned",
         f"{_I}_x = self.conn.execute('SELECT 1').execute\n{_I}_x({_JOIN}, {_P})\n"),
        ("create_function on the connection", "does not resolve",
         f"{_I}self.conn.create_function('rj', 1, str)\n" + ADD_WRITE),
        ("set_authorizer on the connection (the tripwire removed)", "does not resolve",
         f"{_I}self.conn.set_authorizer(None)\n" + ADD_WRITE),
        # research's read of dev's package-wide fix for S2-01: routes with no execute attribute node, and a column written
        # with no SQL statement at all (SQLite's authorizer receives no callback for a blob write)
        ("operator.attrgetter('conn.execute')(self) (SQL by join)", "an accessor constructor",
         f"{_I}import operator\n{_I}operator.attrgetter('conn.execute')(self)({_JOIN}, {_P})\n"),
        ("attrgetter imported under another name (SQL by join)", "an accessor constructor",
         f"{_I}from operator import attrgetter as ag\n{_I}ag('conn.execute')(self)({_JOIN}, {_P})\n"),
        ("operator.methodcaller('execute', ...) over an attrgetter of the connection", "an accessor constructor",
         f"{_I}import operator\n{_I}operator.methodcaller('execute', {_JOIN}, {_P})(operator.attrgetter('conn')(self))\n"),
        ("blobopen on the connection (a column written with no SQL statement)", "does not resolve",
         ADD_WRITE + f"{_I}self.conn.blobopen('edges', 'json', 1).close()\n"),
        ("the store's connection read through a parameter, not `self`", "something other than `self`",
         ADD_WRITE + f"{_I}(lambda store: store.conn)(self).execute({_JOIN}, {_P})\n")):
    MUTANTS.append((FORMS, GATE, inst, need, [(ADD_WRITE, new)]))
ITSELF = "a writer calls the helper, or the journal writer, itself"
MUTANTS += [
    (ITSELF, GATE, "the helper (add_edge, its return ignored)", "`serialise_edge` referenced",
     [(ADD_WRITE, f"{_I}serialise_edge(e)\n" + ADD_WRITE)]),
    (ITSELF, GATE, "the journal writer (confirm journals a second time)", "`_journal_edge` referenced",
     [(CONFIRM_WRITE, CONFIRM_WRITE + f'{_I}self._journal_edge("confirm", eid, e.model_dump_json())\n')]),
]
R3_02 = ("**(v4.2, R3-02) for each form the round-3 reviewer found:** an edge dump bound outside the write method by "
         "annotated rebinding, a loop target, unpacking, a named expression, or with the helper shadowed by a lambda; "
         "`WITH … UPDATE edges`; `UPDATE main.edges`")
_J = f'{_I}self.conn.execute("UPDATE edges SET json=? WHERE id=? AND user_id=?", (j, eid, user_id))\n'
for inst, need, old, new in (
        ("annotated rebinding", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f"{_I}j = serialise_edge(e)\n{_I}j: str = j.replace('0.9', '1.8')\n" + _J),
        ("a loop target", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f"{_I}j = serialise_edge(e)\n{_I}for j in (j.replace('0.9', '1.8'),):\n{_I}    pass\n" + _J),
        ("unpacking", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f"{_I}j = serialise_edge(e)\n{_I}j, _ = j.replace('0.9', '1.8'), None\n" + _J),
        ("a named expression", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f"{_I}j = serialise_edge(e)\n{_I}(j := j.replace('0.9', '1.8'))\n" + _J),
        ("the helper shadowed by a lambda (module scope, every writer unchanged)", "`serialise_edge` bound 2 time(s)",
         "\n\nDDL = ", "\n\nserialise_edge = lambda obj: obj.model_dump_json()\nDDL = "),
        ("`WITH … UPDATE edges`", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f'{_I}self.conn.execute("WITH unused AS (SELECT 1) UPDATE edges SET json=? WHERE id=? AND user_id=?", '
         f'(e.model_dump_json(), eid, user_id))\n'),
        ("`UPDATE main.edges`", (OUTSIDE, TRIP), CONFIRM_WRITE,
         f'{_I}self.conn.execute("UPDATE main.edges SET json=? WHERE id=? AND user_id=?", '
         f'(e.model_dump_json(), eid, user_id))\n')):
    MUTANTS.append((R3_02, GATE, inst, need, [(old, new)]))
OWN = ("**(v4.2) the write method's own forms:** an edit to the write method or its deferred journal; a second helper "
       "call in it; a journal of other bytes; the deferred journal not emitted, emitted twice or after its scope, or "
       "swallowing an exception; a non-constant or second `defer`; a name shadowed by an instance or class attribute, "
       "a subclass or a same-named function; an f-string or `executescript` edges write; a non-literal SQL site "
       "unlisted; a dynamic table's domain gaining `edges`")
OWN_KILL = GATE + " and the deferred journal's cells"
G, FZ = "test_every_edge_write_goes_through_the_validating_serialiser", "is not its frozen body"
DJ_UNEMITTED = "test_a_deferred_journal_left_unemitted_rolls_the_write_back"
DJ_ONCE = "test_a_deferred_journal_emits_once_and_only_inside_its_block"
DJ_SWALLOW = "test_a_deferred_journal_never_swallows_an_exception"
DJ_REDACT = "test_the_redaction_journals_the_bytes_it_stored"
JOURNAL_NOW = "            self._journal_edge(op, target, captured)\n"
EMIT_GUARD = '        if self._state != "open":\n'
EXIT_GUARD = ('        if exc_type is None and state != "emitted":\n'
              '            raise RuntimeError("the edge row was written and its journal never emitted")\n')
REDACT_EMIT = '                self._mark("redacted", user_id, eid)\n                pending.emit("redacted")\n'
for inst, reps, plan in (
        ("an edit to the write method (its SQL whitespace normalised)",
         [("        captured = serialise_edge(e)\n", '        sql = " ".join(sql.split())\n        captured = serialise_edge(e)\n')],
         [(G, FZ)]),
        ("an edit to the deferred journal (a message reworded)",
         [('"the deferred journal was entered twice"', '"entered twice"')], [(G, FZ)]),
        ("a second helper call in it", [(JOURNAL_NOW, "            self._journal_edge(op, target, serialise_edge(e))\n")],
         [(G, (FZ, "`serialise_edge` referenced"))]),
        ("a journal of other bytes", [(JOURNAL_NOW, "            self._journal_edge(op, target, e.model_dump_json())\n")],
         [(G, FZ)]),
        ("the deferred journal not emitted (the redaction)", [(REDACT_EMIT, '                self._mark("redacted", user_id, eid)\n')],
         [(DJ_REDACT, "the redaction raised RuntimeError")]),
        ("the deferred journal not emitted (the journal accepts it)", [(EXIT_GUARD, "")],
         [(G, FZ), (DJ_UNEMITTED, "no refusal")]),
        ("the deferred journal emitted twice (the redaction)",
         [(REDACT_EMIT, REDACT_EMIT + '                pending.emit("redacted")\n')],
         [(DJ_REDACT, "the redaction raised RuntimeError")]),
        ("the deferred journal emitted twice (the journal accepts it)",
         [(EMIT_GUARD, '        if self._state not in ("open", "emitted"):\n')],
         [(G, FZ), (DJ_ONCE, "a second emit inside the block was accepted")]),
        ("the deferred journal emitted after its scope (the redaction)",
         [(REDACT_EMIT, '                self._mark("redacted", user_id, eid)\n            pending.emit("redacted")\n')],
         [(DJ_REDACT, "the redaction raised RuntimeError")]),
        ("the deferred journal emitted after its scope (the journal accepts it)",
         [(EMIT_GUARD, '        if self._state not in ("open", "closed"):\n')],
         [(G, FZ), (DJ_ONCE, "an emit after the block was accepted")]),
        ("the deferred journal swallowing an exception",
         [(EXIT_GUARD + "        return False\n", EXIT_GUARD + "        return True\n")],
         [(G, FZ), (DJ_SWALLOW, "the exception was swallowed")]),
        ("a non-constant `defer`", [("                                      target=eid, defer=True) as pending:\n",
                                     "                                      target=eid, defer=bool(eid)) as pending:\n")],
         [(G, "a non-constant `defer`")]),
        ("a second `defer` site (confirm deferred too)",
         [(CONFIRM_WRITE, f'{_I}with self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, '
                          f'(eid, user_id),\n{_I}                          target=eid, defer=True) as p:\n'
                          f'{_I}    p.emit("confirm")\n')],
         [(G, "a second `defer` site")]),
        ("`**kwargs` reaching it (confirm)",
         [(CONFIRM_WRITE, f'{_I}self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=?", (), e, '
                          f'(eid, user_id),\n{_I}                     **{{"target": eid, "op": "confirm"}})\n')],
         [(G, "a `*` or `**` argument")]),
        ("a name shadowed by an instance attribute (the journal writer)",
         [("            self.conn.executescript(DDL)\n",
           "            self.conn.executescript(DDL)\n        self._journal_edge = lambda op, target, captured: None\n")],
         [(G, "`_journal_edge` assigned as an attribute")]),
        ("a name shadowed by a class attribute (the journal writer)",
         [("    def _begin(self):\n", "    _journal_edge = lambda self, op, target, captured: None\n\n    def _begin(self):\n")],
         [(G, "`_journal_edge` bound 2 time(s)")]),
        ("a subclass overriding the write method",
         [("\n\ndef _due(e, lifetimes, now):\n",
           "\n\nclass _QuickStore(ModelStore):\n    def _write_edge_row(self, sql, before, e, after, **k):\n"
           "        return self.conn.execute(sql, (*before, e.model_dump_json(), *after)).rowcount\n"
           "\n\ndef _due(e, lifetimes, now):\n")],
         [(G, "a subclass of the store")]),
        ("a same-named function (the helper)",
         [("\n\nDDL = ", "\n\ndef serialise_edge(e):\n    return e.model_dump_json()\n\n\nDDL = ")],
         [(G, "`serialise_edge` bound 2 time(s)")]),
        ("an f-string edges write (confirm)",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute(f"UPDATE edges SET json=? WHERE id=\'{{eid}}\'", (e.model_dump_json(),))\n')],
         [(G, ("not a literal", TRIP))]),
        ("an `executescript` edges write (confirm)",
         [(CONFIRM_WRITE, CONFIRM_WRITE + f'{_I}self.conn.executescript("UPDATE edges SET json = json_set(json, '
                                          f"'$.provenance.confidence', 1.8) WHERE id = 'a';\")\n")],
         [(G, (OUTSIDE, TRIP))]),
        ("a non-literal SQL site unlisted (a read whose WHERE is a name)",
         [('        r = self.conn.execute("SELECT json FROM edges WHERE id=? AND user_id=?", (eid, user_id)).fetchone()\n',
           '        where = "id=? AND user_id=?"\n'
           '        r = self.conn.execute("SELECT json FROM edges WHERE " + where, (eid, user_id)).fetchone()\n')],
         [(G, "not a literal")]),
        ("a dynamic table's domain gaining `edges`",
         [('MARK_TABLES = ("redacted",)', 'MARK_TABLES = ("redacted", "edges")')],
         [(G, "is not its frozen value")]),
        ("(beyond §6's list) a trigger whose body writes edges, fired by the write method's own journal insert",
         [("CREATE TABLE redacted (user_id TEXT NOT NULL, target TEXT NOT NULL);\n",
           "CREATE TABLE redacted (user_id TEXT NOT NULL, target TEXT NOT NULL);\n"
           "CREATE TRIGGER lift AFTER INSERT ON journal BEGIN UPDATE edges SET json = json_set(json, "
           "'$.provenance.confidence', 1.8) WHERE id = NEW.target; END;\n")],
         [(G, ("a trigger or view defined in a literal", "an edges write made by trigger"))]),
        # v4.2 round 5: round 4's R4-01, beyond v4.2's list (v4.3's row text is queued); each is refused by the static
        # gate's own reason, the write method unchanged
        ("(beyond §6's list; R4-01 (a)) the json slot re-laid: `before` one short, the unchecked dump in `after`",
         [(ADD_WRITE, f'{_I}self._write_edge_row("INSERT INTO edges (id, user_id, json) VALUES (?, ?, ?) "\n'
                      '                                 "ON CONFLICT(id, user_id) DO UPDATE SET json = excluded.json",\n'
                      '                                 (e.id,), e, (e.model_dump_json().replace("0.8", "1.8"),), '
                      'target=e.id, op="add")\n')],
         [(G, "the json slot's layout")]),
        ("(beyond §6's list; R4-01 (a)) `before` held in a name",
         [(ADD_WRITE, f'{_I}_b = (e.id, e.user_id)\n'
                      f'{_I}self._write_edge_row("INSERT INTO edges (id, user_id, json) VALUES (?, ?, ?) "\n'
                      '                                 "ON CONFLICT(id, user_id) DO UPDATE SET json = excluded.json",\n'
                      '                                 _b, e, (), target=e.id, op="add")\n')],
         [(G, "not tuple displays")]),
        ("(beyond §6's list; R4-01 (c)) an edges write SQLite cannot prepare in the classifier (a table made at run time)",
         [(CONFIRM_WRITE, CONFIRM_WRITE + f'{_I}self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS scratch (j)")\n'
                          f'{_I}self.conn.execute("INSERT INTO scratch VALUES (?)", (e.model_dump_json(),))\n'
                          f'{_I}self.conn.execute("UPDATE edges SET json=(SELECT j FROM scratch) WHERE id=? AND '
                          f'user_id=?", (eid, user_id))\n')],
         [(G, "SQLite cannot prepare")]),
        ("(beyond §6's list; R4-01 (c)) an edges write through a function the classifier lacks",
         [(CONFIRM_WRITE, CONFIRM_WRITE + f'{_I}self.conn.execute("UPDATE edges SET json=rj(json) WHERE id=? AND '
                          f'user_id=?", (eid, user_id))\n')],
         [(G, "SQLite cannot prepare")]),
        ("(beyond §6's list; R4-01 (d)) a changed assignment reaching a listed site (`_mark`'s table)",
         [('        self.conn.execute(f"INSERT INTO {table} (user_id, target) VALUES (?, ?)", (user_id, target))\n',
           '        table = "edges (id, json) VALUES (?, ?) --"\n'
           '        self.conn.execute(f"INSERT INTO {table} (user_id, target) VALUES (?, ?)", (user_id, target))\n')],
         [(G, "a listed non-literal SQL site whose function")]),
        ("(beyond §6's list; R4-01 (d)) a changed definition a listed site reads (`DDL` gains a table)",
         [("CREATE TABLE redacted (user_id TEXT NOT NULL, target TEXT NOT NULL);\n",
           "CREATE TABLE redacted (user_id TEXT NOT NULL, target TEXT NOT NULL);\nCREATE TABLE extra (x TEXT);\n")],
         [(G, "a listed non-literal SQL site whose function")]),
        # research's recheck of 8c71f85d, R-01: unqualified names resolve to temp first, so a TEMP table named edges takes
        # the store's reads and writes; the file is untouched, so no teardown over the file sees it
        ("(beyond §6's list; R-01) `CREATE TEMP TABLE edges`, shadowing the store",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS edges AS SELECT * FROM main.edges")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        ("(beyond §6's list; R-01) `CREATE TEMPORARY TABLE edges`",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("CREATE TEMPORARY TABLE IF NOT EXISTS edges (id TEXT, user_id TEXT, json TEXT)")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        ("(beyond §6's list; R-01) `CREATE TABLE temp.edges`",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("CREATE TABLE IF NOT EXISTS temp.edges (id TEXT, user_id TEXT, json TEXT)")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        ("(beyond §6's list; R-01's class) a TEMP table shadowing the journal",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS journal (seq INTEGER PRIMARY KEY, op TEXT NOT NULL, '
                          f'target TEXT NOT NULL, json TEXT NOT NULL)")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        ("(beyond §6's list; R-01's class) ATTACH",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("ATTACH \':memory:\' AS other")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        ("(beyond §6's list; R-01's class) PRAGMA writable_schema",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("PRAGMA writable_schema=ON")\n' + CONFIRM_WRITE)],
         [(G, ("a route around the store's own schema", "tripwire: a route around"))]),
        # no rule of its own: with writable_schema off, which the PRAGMA rule keeps, SQLite refuses to prepare it
        ("(beyond §6's list; R-01's class) a schema table written directly",
         [(CONFIRM_WRITE, f'{_I}self.conn.execute("UPDATE sqlite_master SET sql=sql WHERE 0")\n' + CONFIRM_WRITE)],
         [(G, "SQLite cannot prepare")])):
    MUTANTS.append((OWN, OWN_KILL, inst, None, reps, plan))
MUTANTS += [
    ("the transition decides from the listing (read outside the transaction)",
     "`test_expiry_is_decided_from_the_current_row` (all four cases)", "-",
     ("confirm:", "confirm95:", "lapse:", "decay:"), [FROM_LISTING]),
    # the two conditional-write rows: decided from the listing's row (the only read a lost race can make stale under
    # N4h's schedule), written conditionally on the fields, or on the read model re-serialised
    ("a write conditional on (confidence, active) as read",
     "`test_expiry_is_decided_from_the_current_row` (`confirm95`)", "-", "confirm95:",
     [FROM_LISTING,
      (TXN_WRITE,
       '            n = self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=? AND '
       "json_extract(json, '$.provenance.confidence')=? AND json_extract(json, '$.invalidated_at') IS NULL\", (), new,\n"
       "                                     (eid, user_id, json.loads(raw)['provenance']['confidence']), target=eid, "
       "op=counter)\n")]),
    ("a conditional write binding the read model re-serialised",
     "`test_expiry_is_decided_from_the_current_row` (legacy-bytes control)", "-", "legacy-bytes control",
     [(TXN_WRITE,
       '            n = self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=? AND json=?", (), new,\n'
       "                                     (eid, user_id, serialise_edge(Edge.model_validate_json(raw))), target=eid, "
       "op=counter)\n")]),
    # v3.3 (H-01): §4D's former "equivalent form", decided from the listing's row and written conditionally on the
    # raw json listed with it; a lost race drops a transition still due on the committed row
    ("a conditional write on the row as read in place of the in-transaction read",
     "`test_expiry_is_decided_from_the_current_row` (`decay`)", "-", "decay:",
     [FROM_LISTING,
      (TXN_WRITE,
       '            n = self._write_edge_row("UPDATE edges SET json=? WHERE id=? AND user_id=? AND json=?", (), new,\n'
       "                                     (eid, user_id, raw), target=eid, op=counter)\n")]),
    # v4 (R2-02): the model's pre-verdict decay semantics, each a departure from the shipped result
    ("a retained decay counted as `decayed`", "`test_decay_keeps_the_shipped_result` (`retained`)", "-", "retained:",
     [('        if moved is not None and moved != "decayed_kept":     # R2-02: `decayed` counts decay invalidations only\n'
       "            counts[moved] += 1\n",
       "        if moved is not None:\n"
       '            counts["decayed" if moved == "decayed_kept" else moved] += 1\n')]),
    ("below the floor, the decayed confidence stored", "`test_decay_keeps_the_shipped_result` (`below the floor`)",
     "-", "below the floor:",
     [('        if e.provenance.confidence * factor < floor:\n'
       '            return _invalidated(e, now, "decayed"), "decayed"\n'
       '        e.provenance = Provenance.model_validate({**e.provenance.model_dump(),\n'
       '                                                  "confidence": e.provenance.confidence * factor})\n',
       '        e.provenance = Provenance.model_validate({**e.provenance.model_dump(),\n'
       '                                                  "confidence": e.provenance.confidence * factor})\n'
       '        if e.provenance.confidence < floor:\n'
       '            return _invalidated(e, now, "decayed"), "decayed"\n')]),
    ("the floor comparison inclusive (`<=`)", "`test_decay_keeps_the_shipped_result` (`exactly at the floor`)", "-",
     "exactly at the floor:",
     [("        if e.provenance.confidence * factor < floor:\n", "        if e.provenance.confidence * factor <= floor:\n")]),
]

#: harmless variants the gate must PASS (§4C's controls): the honest tree is CELLS' own control
_READ = "    def read(self, eid, user_id):\n"
GATE_CONTROLS = [
    ("a new non-edges literal write",
     [(_READ, '    def note(self, op):\n        self.conn.execute("INSERT INTO counters (name, n) VALUES (?, 0) '
              'ON CONFLICT(name) DO NOTHING", (op,))\n\n' + _READ)]),
    ("a new SELECT on edges",
     [(_READ, '    def count(self, user_id):\n        return self.conn.execute("SELECT count(*) FROM edges WHERE '
              'user_id=?", (user_id,)).fetchone()[0]\n\n' + _READ)]),
    ("a WITH-led read of edges",
     [(_READ, '    def count(self, user_id):\n        return self.conn.execute("WITH x AS (SELECT json FROM edges WHERE '
              'user_id=?) SELECT count(*) FROM x", (user_id,)).fetchone()[0]\n\n' + _READ)]),
    # v4.2 round 5: transaction control, which a classifier that RAN statements would read as an error (COMMIT with
    # none open), and an edit in a function no listed non-literal site reads
    ("a savepoint pair (transaction-control literals)",
     [(_READ, '    def _savepoint(self):\n        self.conn.execute("SAVEPOINT s")\n        self.conn.execute("RELEASE s")'
              '\n\n' + _READ)]),
    ("a schema read through `sqlite_master`, in main (no route: it reads the store's own schema)",
     [(_READ, '    def _tables(self):\n        return self.conn.execute("SELECT name FROM sqlite_master").fetchall()\n\n' + _READ)]),
    ("a docstring edit in a function no listed site reads (confirm)",
     [('"""The overlapping operation of N4h (B): the 0008 shape, max(c, 0.9), observed now, unflagged."""',
       '"""The overlapping operation of N4h (B): the 0008 shape — max(c, 0.9), observed now, unflagged."""')]),
]


def run_cell(cell, m, src):
    """-> (outcome, cases): "passed"; "refused", the cell's own CellFailure with its failing cases; or "crashed", any
    other exception. Only a refusal can kill a mutant: a mutant whose text breaks the model (a NameError, a drifted
    signature) crashes, and a crash is not the cell detecting the defect (H-02, dev, 2026-10-12; the 0045 r2 class)."""
    fx = Fixture(m)
    try:
        if cell is model_test_every_edge_write_goes_through_the_validating_serialiser:
            cell(m, fx, src=src)
        else:
            cell(m, fx)
        return "passed", []
    except CellFailure as f:
        return "refused", f.cases
    except Exception as ex:
        return "crashed", [f"{type(ex).__name__}: {str(ex).splitlines()[0][:120] if str(ex) else ''}"]
    finally:
        unmapped(m)
        fx.dir.cleanup()


def _apply(src, row, inst, reps):
    for old, new in reps:
        if src.count(old) != 1:
            print(f"HARNESS ERROR: {row!r} [{inst}]: an anchor occurs {src.count(old)} times", file=sys.stderr)
            sys.exit(2)
        src = src.replace(old, new)
    return src


def main():
    src0 = model_source()
    by_name = {c.__name__.removeprefix("model_"): c for c in CELLS}
    k = n = c = mm = crashed = 0
    m = load(src0)
    for cell in CELLS:
        outcome, fails = run_cell(cell, m, src0)
        mm += 1
        c += outcome == "passed"
        print(f"CONTROL {'PASS' if outcome == 'passed' else 'FAIL'} | `{cell.__name__.removeprefix('model_')}`"
              + ("" if outcome == "passed" else f" | {outcome}: {' '.join('; '.join(fails).split())[:400]}"))
    gate = model_test_every_edge_write_goes_through_the_validating_serialiser
    for label, reps in GATE_CONTROLS:
        src = _apply(src0, "control", label, reps)
        outcome, fails = run_cell(gate, load(src), src)
        mm += 1
        c += outcome == "passed"
        print(f"CONTROL {'PASS' if outcome == 'passed' else 'FAIL'} | `{gate.__name__.removeprefix('model_')}` on a "
              f"harmless variant: {label}" + ("" if outcome == "passed" else f" | {outcome}: {' '.join('; '.join(fails).split())[:400]}"))
    for row, killer, inst, need, reps, *named in MUTANTS:
        src = _apply(src0, row, inst, reps)
        plan = named[0] if named else [(re.match(r"`(\w+)`", killer).group(1), need)]
        outs = []
        for name, nd in plan:
            outcome, fails = run_cell(by_name[name], load(src), src)
            needs = (nd,) if isinstance(nd, str) else (nd or ())
            outs.append((name, outcome, fails, outcome == "refused" and all(any(x in f for f in fails) for x in needs)))
        killed = all(o[3] for o in outs)
        verdict = "KILLED" if killed else "CRASHED" if any(o[1] == "crashed" for o in outs) else "SURVIVED"
        n += 1
        k += killed
        crashed += any(o[1] == "crashed" for o in outs)
        detail = " ".join((f"[{nm}] " if named else "") + ("; ".join(fl) if fl else "cell passed")
                          for nm, _, fl, _ in outs)
        print(f"MUTANT {verdict} | {row} | {killer} | {inst} | {' '.join(detail.split())[:600]}")
    print(f"TALLY: mutants {k}/{n} killed; controls {c}/{mm} pass")
    sys.exit(0 if (k == n and c == mm and not crashed) else 1)


if __name__ == "__main__":
    main()
