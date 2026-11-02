"""0048 round 1, R1-01..R1-04 (+ the finite-decay note): reproduce each finding against the SHIPPED code, written at
the round's pin 4ea1ce5 before any fix (pre-seal Phase 0), and re-run at 6c0eab6 (0048 §2c-ii row 12).

    python specs/evidence/0048/pin_repro.py <tree-root>

`veracium` must import from <tree-root>/src (an installed checkout, or PYTHONPATH=<tree-root>/src for an export); the
script asserts it, so a run cannot silently measure another tree. Its stores live in one temporary directory, removed
on exit.

Each case prints REPRODUCED or NOT REPRODUCED with the observed value; exit 1 if any expected reproduction failed.
R1-01..R1-03 concern the proposed design's gaps, so at the pin they reproduce as the SHIPPED behaviour the design
inherits (no factor check, a read outside the write, a prefix of writes before a raise). R1-04 is a census + an
adjacent episode path.

On a tree with 0048 §4 (2026-11-02, made fixed-aware): an `expire()` that REFUSES is recorded, not raised (`run`), so
each case reports NOT REPRODUCED with the refusal named, and R1-02's pause also hooks the §4D store transition
(`expiry_transition`), so the race is attempted on the fixed path rather than skipped. The episode carrier (R1-04,
outside 0048's scope by the owner's Q6 ruling) and the float fixed point still reproduce there."""
# Mutation-Matrix: tests/test_0048_evidence.py::test_pin_repro_reports_a_planted_fix_as_not_reproduced
import ast, os, pathlib, sys, tempfile, types
from datetime import datetime, timedelta, timezone

PIN = pathlib.Path(sys.argv[1]).resolve()
import veracium
assert pathlib.Path(veracium.__file__).resolve().is_relative_to(PIN), veracium.__file__
from veracium import lifecycle
from veracium.schema import Edge, Episode, EvidenceAuthor, ExpiryBehavior, Provenance, Volatility
from veracium.store.sqlite import SqliteStore

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)
OLD = NOW - timedelta(days=4000)
results = []
_TMP = tempfile.TemporaryDirectory()          # every store below lives here; removed at interpreter exit


def report(name, ok, detail):
    results.append(ok)
    label = ("CONTROL HOLDS " if ok else "CONTROL FAILED") if name.startswith("CONTROL") else \
            ("REPRODUCED    " if ok else "NOT REPRODUCED")
    print(f"{label} {name}: {detail}")


def edge(eid, vol, conf):
    return Edge(id=eid, user_id="u", subject="user", relation="works_at", object=f"obj-{eid}", volatility=vol,
                valid_from=OLD, provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref=eid,
                                                      observed_at=OLD, confidence=conf))


def cfg(factor, floor):
    # a duck-typed configuration: expire() reads exactly these three attributes
    return types.SimpleNamespace(volatility_lifetime_days={v: 1 for v in Volatility}, decay_factor=factor,
                                 confidence_floor=floor)


def run(store, config):
    """expire() on a fixed tree refuses a malformed policy at entry: record the refusal's name, never raise it."""
    try:
        lifecycle.expire(store, "u", config, now=NOW)
        return None
    except (ValueError, TypeError, NotImplementedError) as ex:
        return type(ex).__name__


def conf_of(st, eid):
    (e,) = [x for x in st.edges("u", active_only=False) if x.id == eid]
    return e.provenance.confidence, e.active, e.invalidation_reason


# the host activation the design protects (shipped maps 0 of 5): an IN-PLACE edit of the exported, mutable
# `schema.DEFAULT_EXPIRY` (0048 §1, §2c), the one dict both the shipped `expire()` and the §4D store transition read.
# (Until 2026-11-02 this REBOUND `lifecycle.DEFAULT_EXPIRY` to a copy; the §4D transition does not read that name.)
from veracium import schema as _schema
assert lifecycle.DEFAULT_EXPIRY is _schema.DEFAULT_EXPIRY
_schema.DEFAULT_EXPIRY[Volatility.SLOW] = ExpiryBehavior.DECAY


def fresh(*edges):
    d = tempfile.mkdtemp(dir=_TMP.name)
    st = SqliteStore(os.path.join(d, "t.db"))
    for e in edges:
        st.add_edge(e)
    return st, os.path.join(d, "t.db")


# --- R1-01: nothing checks the FACTOR; an in-range product is accepted even when it is an increase -------------
st, _ = fresh(edge("s", Volatility.SLOW, 0.3))
ref = run(st, cfg(2.0, 0.0))
c, active, _ = conf_of(st, "s")
report("R1-01 factor 2.0 on 0.3", active and c > 0.3, f"persisted confidence {c} (was 0.3), active={active}, refused={ref}")
st, _ = fresh(edge("s", Volatility.SLOW, 0.9))
ref = run(st, cfg(0.5, 2.0))
c, active, why = conf_of(st, "s")
report("R1-01 floor 2.0 (the second numeric field)", not active and why == "decayed",
       f"a valid decay 0.9*0.5 invalidated by an out-of-range floor: active={active} reason={why}, refused={ref}")
st, _ = fresh(edge("s", Volatility.SLOW, 0.9))
ref = run(st, cfg(0.5, float("nan")))
c, active, _ = conf_of(st, "s")
report("R1-01 floor NaN", active and ref is None, f"NaN floor completes without refusal: confidence {c}, active={active}, refused={ref}")
st, _ = fresh(edge("s", Volatility.SLOW, 0.9))
ref = run(st, cfg(True, 0.0))
c, active, _ = conf_of(st, "s")
report("R1-01 Boolean factor", active and c == 0.9 and ref is None, f"factor True accepted, confidence {c}, refused={ref}")

# --- R1-02: the read is outside the write; a stale decay overwrites a LOWER committed confidence -----------------
st_a, path = fresh(edge("s", Volatility.SLOW, 0.9))
st_b = SqliteStore(path)                          # a second, real connection to the same file
seen = []


class PausingStore:
    """A's store: on A's first write-back, B completes two whole expiry runs, then A's (stale) write proceeds."""
    def __init__(self, inner):
        self._i = inner; self._fired = False
    def __getattr__(self, n):
        return getattr(self._i, n)
    def _b_runs(self, what):
        if not self._fired:
            self._fired = True
            seen.append(what)
            lifecycle.expire(st_b, "u", cfg(0.5, 0.0), now=NOW); seen.append(("B run 1", conf_of(st_b, "s")[0]))
            lifecycle.expire(st_b, "u", cfg(0.5, 0.0), now=NOW); seen.append(("B run 2", conf_of(st_b, "s")[0]))
    def add_edge(self, e):                        # the shipped path: A's stale write-back
        self._b_runs(("A computed", e.provenance.confidence))
        return self._i.add_edge(e)
    def expiry_transition(self, *a, **k):         # the 0048 §4D path: B runs before A's transition reads its row
        self._b_runs(("A listed", None))
        return self._i.expiry_transition(*a, **k)


lifecycle.expire(PausingStore(st_a), "u", cfg(0.5, 0.0), now=NOW)
final = conf_of(SqliteStore(path), "s")[0]
report("R1-02 two connections", final > seen[-1][1], f"{seen} then A commits; final committed {final}")

# --- R1-03: no unit of refusal; an earlier edge's write survives a later edge's raise ----------------------------
st, path = fresh(edge("a-transient", Volatility.TRANSIENT, 0.9), edge("b-slow", Volatility.SLOW, 0.9))
order = [e.id for e in st.edges("u", active_only=True)]
before = [(e.id, e.active) for e in st.edges("u", active_only=False)]
try:
    lifecycle.expire(st, "u", cfg("not-a-number", 0.0), now=NOW)
    raised = None
except Exception as ex:                            # the malformed factor raises only when the DECAY branch is reached
    raised = type(ex).__name__
after = [(e.id, e.active) for e in SqliteStore(path).edges("u", active_only=False)]
report("R1-03 prefix written before the refusal", raised is not None and after != before,
       f"order {order}; raised {raised}; before {before} after {after}")

# --- R1-04: five confidence-writing model_copy sites, one of them episode provenance ------------------------------
# Each site is named by its ENCLOSING FUNCTION, not its line (2026-10-13: the check named sqlite.py:2454, so an edit
# above that line in an unrelated change read as "not reproduced"); lines are printed for the reader only.
sites, where = [], []
for p in sorted((PIN / "src").rglob("*.py")):
    tree = ast.parse(p.read_text())
    owner = {}
    for c in ast.walk(tree):
        if isinstance(c, ast.ClassDef):
            for f in c.body:
                if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for x in ast.walk(f):
                        owner[id(x)] = f"{c.name}.{f.name}"
    for f in ast.walk(tree):
        if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(f):
                owner.setdefault(id(x), f.name)
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "model_copy"
                and any(k.arg == "update" and isinstance(k.value, ast.Dict)
                        and any(isinstance(x, ast.Constant) and x.value == "confidence" for x in k.value.keys)
                        for k in n.keywords)):
            sites.append(f"{p.relative_to(PIN)}:{n.lineno}")
            where.append(f"{p.relative_to(PIN)}:{owner.get(id(n), '<module>')}")
report("R1-04 census", len(sites) == 5 and "src/veracium/store/sqlite.py:SqliteStore._derive_output_metadata" in where,
       f"{len(sites)} sites {sites} in {sorted(where)}")
st, path = fresh()
bad = Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="x", observed_at=OLD).model_copy(
    update={"confidence": 1.8})
st.add_episode(Episode(id="ep", user_id="u", date="2020-01-01", summary="s", provenance=bad))
try:
    SqliteStore(path).episodes("u"); read = "listed"
except Exception as ex:
    read = type(ex).__name__
report("R1-04 episode carrier", read != "listed", f"add_episode accepted confidence 1.8; listing -> {read}")

# --- the finite-decay note: "finite in real arithmetic" fails in floats ---------------------------------------------
x = 5e-324
report("finite-decay note: a float fixed point", x * 0.9 == x and not (x * 0.9 < x), f"5e-324 * 0.9 == {x * 0.9!r}")

# --- CONTROLS: the same instruments on honest inputs must NOT show the defect ------------------------------------
st, _ = fresh(edge("s", Volatility.SLOW, 0.9))
lifecycle.expire(st, "u", cfg(0.5, 0.0), now=NOW)
c, active, _ = conf_of(st, "s")
report("CONTROL valid factor decays", active and c == 0.45, f"0.9 * 0.5 -> {c}")
st, path = fresh(edge("s", Volatility.SLOW, 0.9))
for _ in range(3):
    lifecycle.expire(st, "u", cfg(0.5, 0.0), now=NOW)
c = conf_of(SqliteStore(path), "s")[0]
report("CONTROL the same three runs, serial", c == 0.1125, f"three serial runs -> {c} (the race left 0.45)")
st, path = fresh(edge("a-transient", Volatility.TRANSIENT, 0.9), edge("b-slow", Volatility.SLOW, 0.9))
lifecycle.expire(st, "u", cfg(0.5, 0.0), now=NOW)
after = sorted((e.id, e.active, e.provenance.confidence) for e in SqliteStore(path).edges("u", active_only=False))
report("CONTROL mixed order, valid config", after == [("a-transient", False, 0.9), ("b-slow", True, 0.45)], f"{after}")

sys.exit(0 if all(results) else 1)
