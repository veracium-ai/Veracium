"""0048 round 2: expire() decides on a read taken OUTSIDE its write, for all three behaviours (R1-02's class).

    PYTHONPATH=<export>/src python probe_expire_lost_update.py <scratch-dir>

Two real SQLite connections (two `Memory` objects on one file). A runs `expire()` and pauses after its read, before any
write; B commits an operation; A resumes. The pause is deterministic (events), not a timing race.

  confirm   SLOW -> CONFIRM (the SHIPPED table)      B confirm()s; A's stale CONFIRM write reverts it
  confirm95 as confirm, confidence 0.95: B changes neither confidence nor activity, and A still reverts it
  lapse     TRANSIENT -> LAPSE (the SHIPPED table)   B confirm()s; A lapses the fact B just confirmed
  decay     SLOW -> DECAY (mapped for the probe)     the round-1 reviewer's schedule: 0.9 -> B 0.45 -> B 0.225 -> A 0.45

Each case prints the committed row before A resumes and after, with a verdict: `kept` when B's committed state stands;
`serial` when A changed it to exactly what the SERIAL order (B, then A) gives, which is the only correct change (the
decay case after 0048 §4D: B's 0.225 decays to 0.1125); `LOST-UPDATE` otherwise, A's write undoing B's committed state.
Each overlapping case computes its own serial result on a separate file to judge by. The printed SERIAL controls run
B, then A, with no overlap: `kept` for confirm and lapse (nothing is due), `CHANGED` for decay (A decays B's result).
Exit 0 always: this is evidence, not a gate. At the 0048 pin every overlapping case prints `LOST-UPDATE`; with §4D,
confirm, confirm95 and lapse print `kept` and decay prints `serial` (2026-11-02, the verdict made fixed-aware).
"""
import datetime as dt
import json
import pathlib
import sys
import threading

from veracium import Disclosure, Edge, EvidenceAuthor, Memory, MemoryConfig, Provenance
from veracium import schema as S
from veracium.lifecycle import expire

U = "u1"
DIR = pathlib.Path(sys.argv[1])


def _quiet(prompt, *, system=None, role="compile", json_schema=None):
    return json.dumps({"triples": [], "episode": "we talked", "instructions": []})


def _mem(db, **cfg):
    return Memory(llm=_quiet, config=MemoryConfig(db_path=str(db), wiki_recompile_after_writes=0, scope_groups={},
                                                  require_source_id=False, **cfg))


def _row(m):
    e = next(x for x in m.store.edges(U, active_only=False, include_quarantined=True) if x.id == "e-1")
    return {"needs_confirmation": e.needs_confirmation, "confidence": round(e.provenance.confidence, 6),
            "observed": e.provenance.observed_at.date().isoformat(), "invalidated": e.invalidated_at is not None}


def case(name, volatility, observed, conf, b_ops, cfg=None, serial=False, quiet=False):
    db = DIR / f"{name}.db"
    for p in DIR.glob(f"{name}.db*"):
        p.unlink()
    A, B = _mem(db, **(cfg or {})), _mem(db, **(cfg or {}))
    A.store.add_edge(Edge(id="e-1", user_id=U, subject="user", relation="works_on", object="Atlas",
                          volatility=volatility,
                          provenance=Provenance(author_of_evidence=EvidenceAuthor.USER, evidence_ref="ev",
                                                disclosure=Disclosure.MENTIONABLE, confidence=conf,
                                                observed_at=observed)))
    if serial:                                   # the honest control: B commits, THEN A runs, no overlap
        for op in b_ops:
            op(B)
        before = _row(B)
        r = expire(A.store, U, A.config)
        after = _row(B)
        if not quiet:
            print(f"{name:8} SERIAL B {before}\n{'':8} then A {r} -> {after}  {'kept' if after == before else 'CHANGED'}")
        return after
    read, go, out = threading.Event(), threading.Event(), {}
    real = A.store.edges

    def paused(*a, **k):
        r = list(real(*a, **k))
        read.set()
        go.wait(10)
        return r

    A.store.edges = paused
    t = threading.Thread(target=lambda: out.setdefault("A", expire(A.store, U, A.config)))
    t.start()
    read.wait(10)
    for op in b_ops:
        op(B)
    before = _row(B)
    go.set()
    t.join(10)
    A.store.edges = real
    after = _row(B)
    ser = case(name + "-serial", volatility, observed, conf, b_ops, cfg=cfg, serial=True, quiet=True)
    verdict = "kept" if after == before else "serial" if after == ser else "LOST-UPDATE"
    print(f"{name:8} B committed {before}\n{'':8} A {out.get('A')} -> {after}  {verdict}")


now = dt.datetime.now(dt.timezone.utc)
case("confirm", S.Volatility.SLOW, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 0.6,
     [lambda B: B.confirm(U, "e-1")])
# confirm() on an edge already at >= 0.9 changes NEITHER confidence NOR activity (max(c, 0.9) = c): a conditional
# write predicated on (confidence, active) as read would pass and revert observed_at and needs_confirmation
case("confirm95", S.Volatility.SLOW, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 0.95,
     [lambda B: B.confirm(U, "e-1")])
case("lapse", S.Volatility.TRANSIENT, now - dt.timedelta(days=60), 0.6, [lambda B: B.confirm(U, "e-1")])
# serial controls for the two shipped behaviours: without the overlap, A finds nothing due and B's state stands
case("confirm", S.Volatility.SLOW, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 0.6,
     [lambda B: B.confirm(U, "e-1")], serial=True)
case("lapse", S.Volatility.TRANSIENT, now - dt.timedelta(days=60), 0.6, [lambda B: B.confirm(U, "e-1")], serial=True)
saved = S.DEFAULT_EXPIRY[S.Volatility.SLOW]
S.DEFAULT_EXPIRY[S.Volatility.SLOW] = S.ExpiryBehavior.DECAY
try:
    case("decay", S.Volatility.SLOW, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 0.9,
         [lambda B: expire(B.store, U, B.config), lambda B: expire(B.store, U, B.config)],
         cfg={"decay_factor": 0.5, "confidence_floor": 0.0})
    case("decay", S.Volatility.SLOW, dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc), 0.9,
         [lambda B: expire(B.store, U, B.config), lambda B: expire(B.store, U, B.config)],
         cfg={"decay_factor": 0.5, "confidence_floor": 0.0}, serial=True)
finally:
    S.DEFAULT_EXPIRY[S.Volatility.SLOW] = saved
