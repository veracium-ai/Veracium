"""specs/0021 §6 — the W-checks for scope under derivation and consolidation.

Slice C: the WRITE and MAINTAIN halves. Each test is named for the W-check it
carries, so a reader can go from the spec's invariant table to the executable
in one hop.

COVERED HERE: W1, W2, W3, W4, W5, W7, W8, W9, W10, W11, W12, W13, W14, and the
reopen/durability cell of W15.

NOT COVERED, with the reason stated ONCE here and again at the deferral stubs
at the bottom of this file (an omission must never read as a decision):

- **W6** — the value-level cross-principal leak probe is the LIVE / D-extension
  form. It needs a real model and the benchmark harness; it cannot run offline
  and is not simulated here, because a simulated leak probe measures the
  simulation.
- **W15** — the import primitive's obligations (pre-commit refusal leaving the
  destination byte-identical, mid-plan rollback, idempotent re-import,
  concurrent linearization) are already executed in
  `tests/test_0021_import_linkage.py`; this file adds only the membership-
  after-reopen cell rather than duplicating them.
- **W16 / W18 (partly)** — both turn on `apply_retention_prune_plan`, the
  retention contract's own atomic primitive. §7a names it FUTURE and §2c-ii
  asserts executably that NO shipped path prunes an absorbed edge, so the
  reparenting half of W16 and the after-a-prune half of W18 have no writer to
  exercise. The halves that DO have a writer are covered: W14's post-drop cell
  is the born-closed half of W16, and W18's before-a-prune half is
  `test_native_chain_export_carries_absorbed_by_id_on_both_absorbed` in the
  linkage tests.
- **W17** — `test_ledger_plan_against_real_ddl` is the shipped evidence
  program `specs/evidence/0020/ledger_plan_harness.py` (it extracts the REAL
  DDL from a live store); duplicating it in pytest would give a second,
  weaker copy.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from veracium import Memory, MemoryConfig
from veracium.audit import AuditLog
from veracium.config import MemoryConfig as Config
from veracium.graph import apply_supersession
from veracium.lifecycle import (POOL_ERROR_CODES, POOL_STATUSES, consolidate,
                                partition_cold)
from veracium.schema import (DEFAULT_RELATIONS, ConsolidationOutputDraft,
                             ConsolidationState, Edge, Episode as Ep,
                             EvidenceAuthor, Provenance)
from veracium.scope import SHARED, SHARED_POOL_KEY, UNRESOLVED, Identity, digest_of
from veracium.scope_read import MembershipResolver
from veracium.store.sqlite import SqliteStore, SupersessionIntegrityError

ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 6, 1, tzinfo=timezone.utc)
CONF = Config(consolidate_after_days=30, consolidate_min_batch=8)
U = "u"


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

def _llm(n_records=2, *, raises=None, text=None, first_only=False):
    """A deterministic compactor. `raises` / `text` inject a fault at the LLM
    seam; `first_only` confines it to the FIRST pool, so the test observes a
    LATER pool continuing (which is the property W12 is about)."""
    calls = {"n": 0}

    def f(*a, **k):
        calls["n"] += 1
        firing = not first_only or calls["n"] == 1
        if raises is not None and firing:
            raise raises
        if text is not None and firing:
            return text
        return json.dumps({"records": [
            {"date": "2026-01-01", "summary": f"merged {i}"}
            for i in range(n_records)]})
    return f


def _store(tmp_path, name="s.db"):
    return SqliteStore(str(tmp_path / name))


def _cold(store, ids, *, source_id, author=EvidenceAuthor.USER,
          evidence_ref=None, origin=None, summary=None, user_id=U):
    """Persist cold episodes (older than the cutoff) in one scope."""
    out = []
    for i, eid in enumerate(ids):
        ep = Ep(id=eid, user_id=user_id, date=f"2026-01-{(i % 28) + 1:02d}",
                summary=summary or f"day {eid}",
                provenance=Provenance(
                    author_of_evidence=author,
                    evidence_ref=evidence_ref if evidence_ref is not None
                    else f"r-{eid}",
                    observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    source_id=source_id, origin=origin))
        store.add_episode(ep)
        out.append(ep)
    return out


def _edge(eid, obj, *, source_id, conf=0.9, rel="pet", user_id=U,
          author=EvidenceAuthor.USER, evidence_ref=None, subject="user"):
    return Edge(id=eid, user_id=user_id, subject=subject, relation=rel,
                object=obj, valid_from=NOW,
                provenance=Provenance(
                    author_of_evidence=author,
                    evidence_ref=evidence_ref or f"ev-{eid}",
                    observed_at=NOW, confidence=conf, source_id=source_id))


def _digests(store, *source_ids, origin=None):
    local = store.local_origin()
    return [digest_of(Identity(origin, s), local) for s in source_ids]


def _outputs(store, user_id=U):
    return [e for e in store.episodes(user_id) if e.lineage]


def _robustness_accumulators():
    """`tests/robustness/invariants.py` — the SHIPPED checker external R4-2
    named as an implementation obligation (it rejected the dict-valued
    `pools` key at review time).

    Loaded BY PATH rather than by `sys.path` insertion: it does
    `from adapter import snippet`, and in a full-suite run another module
    called `adapter` may already own that name in `sys.modules`. The binding
    is installed and restored around the load so nothing else sees it."""
    import importlib.util
    base = ROOT / "tests" / "robustness"
    saved = sys.modules.get("adapter")
    spec_a = importlib.util.spec_from_file_location("adapter",
                                                    base / "adapter.py")
    adapter = importlib.util.module_from_spec(spec_a)
    sys.modules["adapter"] = adapter
    try:
        spec_a.loader.exec_module(adapter)
        spec_i = importlib.util.spec_from_file_location(
            "_robustness_invariants", base / "invariants.py")
        inv = importlib.util.module_from_spec(spec_i)
        spec_i.loader.exec_module(inv)
    finally:
        if saved is None:
            sys.modules.pop("adapter", None)
        else:
            sys.modules["adapter"] = saved
    return inv.Accumulators


# --------------------------------------------------------------------------- #
# W1 — test_consolidation_partitions_by_scope
# --------------------------------------------------------------------------- #

def test_consolidation_partitions_by_scope(tmp_path):
    """W1: consolidation NEVER merges across scopes.

    NARROWED, per §4d: the claim holds on stores operated exclusively by
    0021-capable processes. No schema/format marker stops a PRE-0021 process
    from opening the same store during a rolling upgrade and running today's
    global consolidation — new processes partition, old ones do not, and the
    deployment requirement is to upgrade every writer before relying on this.
    Scoped READS stay fail-closed throughout the window either way (the
    pre-0021 derivative lands legacy-shaped → UNRESOLVED, W9)."""
    store = _store(tmp_path)
    _cold(store, [f"a{i}" for i in range(8)], source_id="src-A")
    _cold(store, [f"b{i}" for i in range(8)], source_id="src-B")
    da, db = _digests(store, "src-A", "src-B")

    rep = consolidate(store, _llm(), U, CONF, now=NOW)
    assert set(rep["pools"]) == {da, db}
    assert rep["pools"][da]["status"] == "ok"
    assert rep["pools"][db]["status"] == "ok"
    assert rep["consolidated"] == 16 and rep["pools_ok"] == 2

    # every output's lineage is drawn from ONE pool — no derivative carries
    # inputs from both scopes
    a_ids, b_ids = {f"a{i}" for i in range(8)}, {f"b{i}" for i in range(8)}
    for out in _outputs(store):
        base = {lid.split("hist:")[-1] if "hist:" in lid else lid
                for lid in out.lineage}
        raw = {x.rsplit(":", 1)[-1] for x in base} | base
        assert not (raw & a_ids and raw & b_ids), (
            f"output {out.id} mixes scope A and scope B inputs — W1 broken")

    # and the ledger says so: every output's contribution rows carry ONE digest
    for out in _outputs(store):
        rows = store.contributions(U, "episode", out.id)
        assert len({r.identity_digest for r in rows}) == 1
    store.close()


# --------------------------------------------------------------------------- #
# W2 — test_absorption_partitions_by_scope
# --------------------------------------------------------------------------- #

def test_absorption_partitions_by_scope(tmp_path):
    """W2: absorption never absorbs across scopes. A cross-scope prior
    ACCUMULATES as a separate edge — today's cross-CLASS behaviour, extended
    one axis (§4c)."""
    store = _store(tmp_path)
    apply_supersession(store, _edge("p-a", "Miso", source_id="src-A", conf=0.5),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("w-b", "cat Miso", source_id="src-B"),
                       DEFAULT_RELATIONS)

    live = {e.id for e in store.edges(U, active_only=True)}
    assert live == {"p-a", "w-b"}, "a cross-scope prior must NOT be absorbed"
    assert store.contributions(U, "edge", "w-b") == []
    prior = next(e for e in store.edges(U, active_only=False)
                 if e.id == "p-a")
    assert prior.invalidation_reason is None and "absorbed_by:" not in \
        (prior.note or "")

    # the SAME-scope case still absorbs — the check is not vacuous
    apply_supersession(store, _edge("w-a", "small cat Miso", source_id="src-A"),
                       DEFAULT_RELATIONS)
    after = {e.id for e in store.edges(U, active_only=True)}
    assert "p-a" not in after and "w-a" in after
    rows = store.contributions(U, "edge", "w-a")
    assert [r.site for r in rows] == ["absorption"]
    assert rows[0].contributor_ref == "p-a"

    # …and an UNIDENTIFIED pair absorbs among ITSELF (SHARED == SHARED), while
    # neither crosses into a scope
    apply_supersession(store, _edge("p-n", "Rex", source_id=None, rel="dog"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("w-n", "dog Rex", source_id=None,
                                    rel="dog"), DEFAULT_RELATIONS)
    assert {e.id for e in store.edges(U, active_only=True, relation="dog")} \
        == {"w-n"}
    store.close()


# --------------------------------------------------------------------------- #
# W3 — test_scope_operation_matrix_is_total
# --------------------------------------------------------------------------- #

def test_scope_operation_matrix_is_total():
    """W3: the §3 matrix is total via the COMBINING_SITES registry + the
    generated manifest — AND the gate actually BITES.

    The second half is the whole point. A gate that only ever runs on the
    current tree proves nothing about the tree that adds a merge path, so a
    synthetic module carrying a NEW write in an unregistered function is fed
    to the same enumerator and must be reported."""
    r = subprocess.run([sys.executable,
                        str(ROOT / "specs" / "combining_sites.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, (
        f"the combining-site manifest and the code disagree:\n{r.stdout}\n"
        f"{r.stderr}\nRegenerate with "
        f"`python3 specs/combining_sites.py --write` and give every new write "
        f"site a verdict in src/veracium/combining.py.")

    sys.path.insert(0, str(ROOT / "specs"))
    import combining_sites as cs
    from veracium.combining import COMBINING_SITES, OPERATIONS, SiteSpec

    synthetic = (
        "class S:\n"
        "    def merge_everything(self, a, b):\n"
        "        self._conn.execute('INSERT INTO edges(id) VALUES(?)', (a,))\n")
    found = cs.enumerate_write_sites(synthetic, "src/veracium/store/sqlite.py")
    assert ("src/veracium/store/sqlite.py", "merge_everything") in found
    bad = cs.problems(found, COMBINING_SITES, OPERATIONS)
    assert any("UNREGISTERED" in b and "merge_everything" in b for b in bad), bad

    # a STALE row is caught too (the other direction)
    assert any("STALE registry row" in b
               for b in cs.problems({}, COMBINING_SITES, OPERATIONS))

    # a combining site with NO scope rule cannot pass as a decision
    real = cs.sites()
    key = ("src/veracium/store/sqlite.py", "set_wiki")
    ruleless = dict(COMBINING_SITES)
    ruleless[key] = SiteSpec(True, ("wiki-compilation",), "")
    assert any("no scope rule" in b
               for b in cs.problems(real, ruleless, OPERATIONS))

    # and a matrix row NO site claims is fiction, in both directions
    assert any("non-combining" in b.lower() or "NO registered" in b
               for b in cs.problems(real, COMBINING_SITES,
                                    {**OPERATIONS, "expiry": "combining"}))


# --------------------------------------------------------------------------- #
# W4 — test_unidentified_pool_is_closed
# --------------------------------------------------------------------------- #

def test_unidentified_pool_is_closed(tmp_path):
    """W4: HOST-produced unidentified records merge only among THEMSELVES.
    Nothing crosses INTO a scope, and a writer who omits identity to make
    content mergeable everywhere achieves the opposite (§2c)."""
    store = _store(tmp_path)
    _cold(store, [f"a{i}" for i in range(8)], source_id="src-A")
    _cold(store, [f"n{i}" for i in range(8)], source_id=None)
    (da,) = _digests(store, "src-A")

    pools = dict(partition_cold(store, U, [e for e in store.episodes(U)]))
    assert set(pools) == {da, SHARED_POOL_KEY}
    assert {e.id for e in pools[SHARED_POOL_KEY]} == {f"n{i}" for i in range(8)}
    assert {e.id for e in pools[da]} == {f"a{i}" for i in range(8)}

    # the reserved key cannot collide with digest space (external R3-4): a
    # 0006 digest is 64 hex characters, and this literal carries a colon
    assert ":" in SHARED_POOL_KEY and len(SHARED_POOL_KEY) != 64

    rep = consolidate(store, _llm(), U, CONF, now=NOW)
    assert rep["pools_ok"] == 2
    # the shared pool's derivatives stay POOLED: their rows carry NULL digests
    resolver = MembershipResolver(store, U)
    shapes = {resolver.evidence(o) for o in _outputs(store)}
    assert shapes == {da, SHARED}, shapes
    store.close()


# --------------------------------------------------------------------------- #
# W5 — test_supersession_is_scope_blind
# --------------------------------------------------------------------------- #

def test_supersession_is_scope_blind(tmp_path):
    """W5: supersession is UNTOUCHED — truth is global, so a cross-scope
    differing value on a functional relation still retires the prior. Per-scope
    truths would diverge; visibility is 0020's job, not supersession's."""
    store = _store(tmp_path)
    apply_supersession(store, _edge("s-a", "tea over coffee",
                                    source_id="src-A", rel="prefers"),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("s-b", "coffee over tea",
                                    source_id="src-B", rel="prefers"),
                       DEFAULT_RELATIONS)
    hist = {e.id: e for e in store.edges(U, active_only=False)}
    assert hist["s-a"].invalidation_reason == "superseded", (
        "supersession must stay scope-BLIND (§3)")
    assert hist["s-b"].supersedes == "s-a"
    # and it is NOT an absorption: no ledger row, no absorbed_duplicate
    assert store.contributions(U, "edge", "s-b") == []
    store.close()


# --------------------------------------------------------------------------- #
# W7 — test_derivative_inherits_partition_scope
# --------------------------------------------------------------------------- #

def test_derivative_inherits_partition_scope(tmp_path):
    """W7: a derivative's membership comes from the LEDGER evidence hierarchy,
    never from a copied identity field. The output's own identity is CLEARED
    (W8) and it still resolves to its pool's scope."""
    store = _store(tmp_path)
    _cold(store, [f"a{i}" for i in range(8)], source_id="src-A")
    (da,) = _digests(store, "src-A")
    consolidate(store, _llm(), U, CONF, now=NOW)

    resolver = MembershipResolver(store, U)
    for out in _outputs(store):
        assert out.provenance.source_id is None      # nothing to copy from
        assert out.provenance.origin is None
        assert resolver.evidence(out) == da, (
            "membership must travel through the ledger")
        rows = store.contributions(U, "episode", out.id)
        assert len(rows) == len(out.lineage) and all(
            r.identity_digest == da for r in rows)
    store.close()


# --------------------------------------------------------------------------- #
# W8 — test_output_identity_cleared
# --------------------------------------------------------------------------- #

def test_output_identity_cleared(tmp_path):
    """W8 — THE REVIEWER'S MIXED-SCOPE PROBE, verbatim (external F1).

    `_derive_output_metadata` copied `inputs[0].provenance` WITHOUT clearing
    `origin`/`source_id`, so a mixed A+B consolidation output CLAIMED identity
    A. The probe drives the 0010 primitives DIRECTLY with a deliberately mixed
    claimed set — which is exactly what a pre-0021 (or an adversarially
    driven) writer does, and the partition in `consolidate` therefore cannot
    be what makes this pass. Store-authored means store-identified."""
    store = _store(tmp_path)
    _cold(store, ["mix-a"], source_id="src-A", origin="org-a")
    _cold(store, ["mix-b"], source_id="src-B", origin="org-b")

    op = store.create_or_takeover_consolidation(U, ["mix-a", "mix-b"], "w", 60)
    store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w", ConsolidationState.GENERATING)
    assert store.write_consolidation_output_if_current(
        op.operation_id, op.fence, "w",
        ConsolidationOutputDraft(summary="mixed", date_start="2026-01-01",
                                 date_end="2026-01-02"))
    # the output is provisional and hidden until the cutover (0010 X14), so
    # advance to OUTPUTS_DURABLE before reading it back
    assert store.transition_consolidation_if_current(
        op.operation_id, op.fence, "w", ConsolidationState.OUTPUTS_DURABLE)
    out = _outputs(store)[0]
    assert out.provenance.origin is None, (
        "a mixed A+B derivative must NOT claim origin A — external F1")
    assert out.provenance.source_id is None, (
        "a mixed A+B derivative must NOT claim source_id A — external F1")
    # the identity is not merely absent from the object: it resolves to the
    # LOCAL singleton at read (0006 I9) and is NOT groupable (I13)
    assert digest_of(Identity(out.provenance.origin, out.provenance.source_id),
                     store.local_origin()) is None
    # and the derived trust fields the same call computes are UNCHANGED
    assert out.provenance.author_of_evidence is EvidenceAuthor.SYSTEM
    assert out.provenance.evidence_ref == op.operation_id
    store.close()


# --------------------------------------------------------------------------- #
# W9 — test_unresolved_populations_fail_closed
# --------------------------------------------------------------------------- #

def test_unresolved_populations_fail_closed(tmp_path):
    """W9: an UNRESOLVED record is in NO pool — not its claimed one, not the
    shared one. The reachable population here is the LEGACY derivative: a
    system-authored record with a consolidation-shaped `op-<12hex>`
    evidence_ref that STILL CARRIES a groupable identity (a pre-0021 output,
    or one an 0010 recovery finalized after the upgrade — recovery only
    finalizes, it cannot clear an already-durable output, §2c)."""
    store = _store(tmp_path)
    _cold(store, [f"a{i}" for i in range(8)], source_id="src-A")
    _cold(store, ["legacy-1", "legacy-2"], source_id="src-A",
          author=EvidenceAuthor.SYSTEM, evidence_ref="op-0123456789ab")
    (da,) = _digests(store, "src-A")

    resolver = MembershipResolver(store, U)
    legacy = [e for e in store.episodes(U) if e.id.startswith("legacy")]
    assert all(resolver.evidence(e) is UNRESOLVED for e in legacy)

    pools = dict(partition_cold(store, U, list(store.episodes(U))))
    assert set(pools) == {da}
    pooled = {e.id for e in pools[da]}
    assert pooled == {f"a{i}" for i in range(8)}
    assert not any(x.startswith("legacy") for x in pooled), (
        "an UNRESOLVED derivative must be in NO pool (W9)")

    # …and it is untouched by the run that consolidates its claimed scope
    consolidate(store, _llm(), U, CONF, now=NOW)
    assert {e.id for e in store.episodes(U) if not e.lineage} == \
        {"legacy-1", "legacy-2"}
    store.close()


# --------------------------------------------------------------------------- #
# W10 — test_per_scope_thresholds
# --------------------------------------------------------------------------- #

def test_per_scope_thresholds(tmp_path):
    """W10: `consolidate_min_batch` applies PER POOL. Four A records plus four
    B records with min_batch=8 is a NO-OP — the reviewer's cell. No global
    trigger exists to fall back to."""
    store = _store(tmp_path)
    _cold(store, [f"a{i}" for i in range(4)], source_id="src-A")
    _cold(store, [f"b{i}" for i in range(4)], source_id="src-B")
    da, db = _digests(store, "src-A", "src-B")

    rep = consolidate(store, _llm(), U, CONF, now=NOW)
    assert rep["consolidated"] == 0 and rep["into"] == 0
    assert rep["pools"][da]["status"] == "below-threshold"
    assert rep["pools"][db]["status"] == "below-threshold"
    assert rep["pools_ok"] == 0 and rep["pools_failed"] == 0
    assert _outputs(store) == [], "the 4A+4B/min-8 cell must mutate nothing"

    # per-pool trigger INDEPENDENCE: bring A over the line, B stays below
    _cold(store, [f"a{i}" for i in range(4, 8)], source_id="src-A")
    rep = consolidate(store, _llm(), U, CONF, now=NOW)
    assert rep["pools"][da]["status"] == "ok"
    assert rep["pools"][da]["consolidated"] == 8
    assert rep["pools"][db]["status"] == "below-threshold"
    assert rep["consolidated"] == 8
    assert {e.id for e in store.episodes(U) if not e.lineage} == \
        {f"b{i}" for i in range(4)}
    store.close()


# --------------------------------------------------------------------------- #
# W11 — test_partition_is_policy_independent
# --------------------------------------------------------------------------- #

def test_partition_is_policy_independent(tmp_path):
    """W11 (external F5): identity partitioning is POLICY-INDEPENDENT. The
    same store partitions identically with and without a policy — because
    policy is a read-side concept and no process's configuration may change
    what the store MERGES. An honest unscoped host can no longer
    co-consolidate A and B while a scoped host assumes isolation."""
    def _run(db, groups):
        mem = Memory(llm=_llm(), config=MemoryConfig(
            db_path=str(db), consolidate_after_days=30,
            consolidate_min_batch=8, wiki_recompile_after_writes=0,
            **({"scope_groups": groups} if groups is not None else {})))
        # an EXPLICIT origin, so the two stores (which mint DIFFERENT local
        # singletons) produce the SAME digests — the comparison is then over
        # the partition itself rather than over two id spaces
        _cold(mem.store, [f"a{i}" for i in range(8)], source_id="src-A",
              origin="org-x")
        _cold(mem.store, [f"b{i}" for i in range(8)], source_id="src-B",
              origin="org-x")
        rep = mem.maintain(U)["consolidation"]
        outs = sorted((tuple(sorted(o.lineage)),) for o in _outputs(mem.store))
        mem.close()
        return rep, outs

    unscoped, outs_u = _run(tmp_path / "none.db", None)
    scoped, outs_s = _run(tmp_path / "pol.db",
                          {"team-a": [Identity(None, "src-A")]})

    assert set(unscoped["pools"]) == set(scoped["pools"])
    assert unscoped["pools"] == scoped["pools"]
    assert outs_u == outs_s, (
        "the partition must not depend on any host's policy (§2)")
    # and the partitioner takes no policy argument at all — the structural
    # form of the same claim
    import inspect
    assert "policy" not in inspect.signature(partition_cold).parameters
    assert "policy" not in inspect.signature(consolidate).parameters


# --------------------------------------------------------------------------- #
# W12 — test_per_pool_fault_matrix
# --------------------------------------------------------------------------- #

SECRET = "Mo flies a Beechcraft Baron out of Aerodyne"

_FAULTS = {
    # (name) -> (llm factory, store-method to break, expected code)
    "llm-error": (lambda: _llm(raises=RuntimeError("provider exploded"),
                               first_only=True), None, "llm-error"),
    "llm-secret": (lambda: _llm(raises=RuntimeError(
        f"model refused on input: {SECRET}"), first_only=True),
        None, "llm-error"),
    "timeout": (lambda: _llm(raises=TimeoutError("gateway timeout"),
                             first_only=True), None, "timeout"),
    "validation-error": (lambda: _llm(text="not json at all",
                                      first_only=True),
                         None, "validation-error"),
    "store-claim": (_llm, "create_or_takeover_consolidation", "store-error"),
    "store-generate": (_llm, "write_consolidation_output_if_current",
                       "store-error"),
    "store-cutover": (_llm, "transition_consolidation_if_current",
                      "store-error"),
    "store-delete": (_llm, "delete_claimed_inputs_if_current", "store-error"),
}


class _BreakForPool:
    """Breaks `method` only while the FIRST pool is running, so the later
    pool's continuation is what the test observes."""

    def __init__(self, real, method, victim_ids):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_method", method)
        object.__setattr__(self, "_victims", set(victim_ids))
        object.__setattr__(self, "_armed", True)
        object.__setattr__(self, "_ops", set())

    def __getattr__(self, name):
        attr = getattr(self._real, name)
        if name != self._method:
            return attr

        def wrapped(*a, **k):
            if name == "create_or_takeover_consolidation":
                if self._armed and set(a[1]) & self._victims:
                    raise RuntimeError("store exploded")
                return attr(*a, **k)
            if self._armed and a and a[0] in self._ops:
                raise RuntimeError("store exploded")
            return attr(*a, **k)
        return wrapped

    def create_or_takeover_consolidation(self, user_id, ids, owner, lease):
        if self._method == "create_or_takeover_consolidation" \
                and self._armed and set(ids) & self._victims:
            raise RuntimeError("store exploded")
        op = self._real.create_or_takeover_consolidation(
            user_id, ids, owner, lease)
        if op is not None and set(ids) & self._victims:
            self._ops.add(op.operation_id)
        return op


@pytest.mark.parametrize("fault", sorted(_FAULTS))
def test_per_pool_fault_matrix(tmp_path, fault):
    """W12 (R2-5 / R3-5 / R4-3): every pool phase × later-pool continuation,
    through ALL the carriers.

    "A committed, B failed, C/D ran anyway" must be REPRESENTABLE, and it must
    be representable in each carrier separately: the additive-superset return,
    the amended audit contract (aggregate + per-pool events, closed error
    codes), telemetry's preserved-key mapping, and the robustness checker.

    THE ADVERSARIAL CELL: the `llm-secret` case plants an episode string
    inside the exception the provider raises. The audit sink's invariant is
    NO MEMORY TEXT EVER, and `str(exc)` on an LLM exception is precisely how
    that invariant dies — so the secret must be provably absent from the log
    AND from the returned result."""
    make_llm, break_method, expected = _FAULTS[fault]
    log_path = tmp_path / "audit.jsonl"
    log = AuditLog(str(log_path))
    mem = Memory(llm=make_llm(), audit=log, config=MemoryConfig(
        db_path=str(tmp_path / "s.db"), consolidate_after_days=30,
        consolidate_min_batch=8, wiki_recompile_after_writes=0))
    _cold(mem.store, [f"a{i}" for i in range(8)], source_id="src-A",
          summary=SECRET)
    _cold(mem.store, [f"b{i}" for i in range(8)], source_id="src-B",
          summary=SECRET)
    da, db = _digests(mem.store, "src-A", "src-B")
    # pools run in sorted digest order, so the FIRST is the victim and the
    # SECOND is the continuation the matrix is about
    victim, survivor = sorted([da, db])[0], sorted([da, db])[1]
    victim_ids = [e.id for e in mem.store.episodes(U)
                  if MembershipResolver(mem.store, U).evidence(e) == victim]

    real_store = mem.store
    if break_method is not None:
        mem.store = _BreakForPool(real_store, break_method, victim_ids)

    report = mem.maintain(U)
    co = report["consolidation"]
    mem.store = real_store

    # -- carrier 1: the ADDITIVE-SUPERSET return ---------------------------
    assert set(co) == {"consolidated", "into", "recovered", "pools",
                       "pools_ok", "pools_failed"}
    assert co["pools"][victim]["status"] in ("failed", "contended")
    assert co["pools"][victim]["error"] == expected
    assert co["pools"][victim]["error"] in POOL_ERROR_CODES
    assert all(p["status"] in POOL_STATUSES for p in co["pools"].values())
    # THE CONTINUATION: the later pool ran anyway, and its commit stands
    assert co["pools"][survivor]["status"] == "ok"
    assert co["pools"][survivor]["consolidated"] == 8
    assert co["consolidated"] == 8 and co["pools_ok"] == 1
    # the preserved totals ROLL UP the pools — not a separate accounting
    assert co["consolidated"] == sum(p["consolidated"]
                                     for p in co["pools"].values())

    # the victim pool mutated nothing durable: its inputs are all still there
    remaining = {e.id for e in real_store.episodes(U) if not e.lineage}
    if break_method != "delete_claimed_inputs_if_current":
        assert set(victim_ids) <= remaining

    # -- carrier 2: the AMENDED AUDIT CONTRACT -----------------------------
    entries = log.entries(user_id=U)
    pool_events = [e for e in entries if e["op"] == "consolidate-pool"]
    aggregate = [e for e in entries if e["op"] == "maintain"]
    assert len(aggregate) == 1, "the aggregate maintain event is PRESERVED"
    assert len(pool_events) == 2, "one additive event per ATTEMPTED pool"
    assert {e["pool_key"] for e in pool_events} == {victim, survivor}
    for e in pool_events:
        assert e["status"] in POOL_STATUSES
        assert e.get("error_code") in (None, *POOL_ERROR_CODES)
    assert aggregate[0]["consolidated_in"] == 8      # the preserved counters
    assert aggregate[0]["consolidated_out"] == co["into"]

    # -- the ADVERSARIAL cell: no memory text, ever ------------------------
    raw = log_path.read_text()
    assert SECRET not in raw, (
        "an exception carrying episode text reached the audit sink — the "
        "error code must be a CLOSED CONTENT-FREE enum, never str(exc)")
    assert "Beechcraft" not in raw and "exploded" not in raw
    assert SECRET not in json.dumps(co), (
        "…and not into the returned result either — one value, both carriers")

    # -- carrier 3: telemetry's PRESERVED KEYS -----------------------------
    from veracium.telemetry import EVENT_FIELDS
    assert "consolidate-pool" not in EVENT_FIELDS, (
        "the per-pool event is audit-only; adding it to telemetry would "
        "change the shipped mapping this test exists to protect")
    assert EVENT_FIELDS["maintain"] >= {"consolidated_in", "consolidated_out"}

    # -- carrier 4: the ROBUSTNESS CHECKER ---------------------------------
    acc = _robustness_accumulators()()
    acc.check_maintain(report, n_edges=0,
                       n_episodes=len(real_store.episodes(U)) + 16)
    assert acc.s5["violations"] == [], acc.s5["violations"]
    mem.close()


# --------------------------------------------------------------------------- #
# W13 — test_absorption_survivor_membership
# --------------------------------------------------------------------------- #

def test_absorption_survivor_membership(tmp_path):
    """W13: an absorption survivor resolves through its ledger rows over the
    TRANSITIVELY CLOSED set, and the cross-digest cell FAILS CLOSED.

    The cross-digest state is PRE-0021 by construction — §4c's partition means
    the native writer can no longer create it — so it is installed directly,
    which is exactly the shape a rolling upgrade or an import leaves."""
    store = _store(tmp_path)
    apply_supersession(store, _edge("p1", "Miso", source_id="src-A", conf=0.5),
                       DEFAULT_RELATIONS)
    apply_supersession(store, _edge("s1", "cat Miso", source_id="src-A"),
                       DEFAULT_RELATIONS)
    (da,) = _digests(store, "src-A")
    resolver = MembershipResolver(store, U)
    survivor = next(e for e in store.edges(U, active_only=True))
    assert resolver.evidence(survivor) == da

    # now forge the pre-0021 cell: the survivor's row names ANOTHER scope
    (db,) = _digests(store, "src-B")
    store._conn.execute(
        "UPDATE contribution_ledger SET identity_digest=? WHERE survivor_id=?",
        (db, "s1"))
    store._conn.commit()
    assert MembershipResolver(store, U).evidence(survivor) is UNRESOLVED, (
        "a survivor whose ledger says another scope contributed must fail "
        "closed (R3-3)")
    store.close()


# --------------------------------------------------------------------------- #
# W14 — test_transitive_absorption_chains
# --------------------------------------------------------------------------- #

def test_transitive_absorption_chains(tmp_path):
    """W14 (external R7-1): every POST-0021 absorption leaves the survivor's
    row set TRANSITIVELY CLOSED — born closed, by construction, in the same
    atomic operation. The A→B→C chain that defeated the single-level read
    cannot recur on rows this spec writes."""
    store = _store(tmp_path)
    for eid, obj, conf in (("A", "Miso", 0.2), ("B", "cat Miso", 0.5),
                           ("C", "small cat Miso", 0.9)):
        apply_supersession(store, _edge(eid, obj, source_id="src-A",
                                        conf=conf), DEFAULT_RELATIONS)
    (da,) = _digests(store, "src-A")

    rows = {(r.site, r.contributor_ref): r
            for r in store.contributions(U, "edge", "C")}
    assert set(rows) == {("absorption", "B"), ("scope-attribution", "A")}, (
        "C's row set must carry its WHOLE ancestry, not just its direct "
        "contributor")
    flat = rows[("scope-attribution", "A")]
    assert flat.payload == {"flattened": True}      # the closed §7b class
    assert flat.contributor_type == "edge"
    assert flat.identity_digest == da
    assert flat.op_key and flat.op_key.startswith("scope-attribution:"), (
        "the NATIVE per-row key form: the shipped `sup-{edge.id}` op id "
        "embeds unrestricted text, so it is FRAMED INTO the digest")
    # the DIRECT contributor keeps the accepted native payload, UNAMENDED
    assert set(rows[("absorption", "B")].payload) == {"base", "contributor"}

    survivor = next(e for e in store.edges(U, active_only=True))
    assert MembershipResolver(store, U).evidence(survivor) == da

    # BORN CLOSED: drop the intermediate's own rows (accepted 0014 A10 — a
    # ledger row lives exactly as long as its survivor) and C still resolves,
    # because its ancestry lives on C's OWN rows
    store._drop_contributions_for_survivor(U, "edge", "B")
    store._conn.commit()
    assert MembershipResolver(store, U).evidence(survivor) == da

    # …and after a close/reopen (durability, not a cache)
    path = store.path if hasattr(store, "path") else None
    store.close()
    reopened = SqliteStore(str(tmp_path / "s.db"))
    again = next(e for e in reopened.edges(U, active_only=True))
    assert MembershipResolver(reopened, U).evidence(again) == da
    assert {(r.site, r.contributor_ref)
            for r in reopened.contributions(U, "edge", "C")} == \
        {("absorption", "B"), ("scope-attribution", "A")}
    reopened.close()
    assert path is None or True


def test_a_pre_0021_chain_still_fails_closed(tmp_path):
    """W14's other half / §4d: a chain that PREDATES the flattening is read
    with the closure and lands UNRESOLVED — the direct row alone reads
    own-scope, so the single-level read is what the closure replaces."""
    store = _store(tmp_path)
    for eid, obj, conf in (("A", "Miso", 0.2), ("B", "cat Miso", 0.5),
                           ("C", "small cat Miso", 0.9)):
        apply_supersession(store, _edge(eid, obj, source_id="src-A",
                                        conf=conf), DEFAULT_RELATIONS)
    (db,) = _digests(store, "src-B")
    # rewrite history into the pre-0021 shape: no flattened copies, and A's
    # row carries a FOREIGN digest one hop down
    store._conn.execute(
        "DELETE FROM contribution_ledger WHERE site='scope-attribution'")
    store._conn.execute(
        "UPDATE contribution_ledger SET identity_digest=? "
        "WHERE survivor_id='B'", (db,))
    store._conn.commit()
    survivor = next(e for e in store.edges(U, active_only=True))
    assert MembershipResolver(store, U).evidence(survivor) is UNRESOLVED
    store.close()


def test_the_store_refuses_a_cross_scope_absorption_plan(tmp_path):
    """§4c, at the ATOMIC PRIMITIVE: the same-scope requirement is not only a
    planner decision. A plan carrying a cross-scope absorption draft — the
    shape a store-level caller can submit directly — is REFUSED whole, with
    nothing durable."""
    from veracium.graph import _build_supersession_plan
    from veracium.schema import ContributionDraft
    store = _store(tmp_path)
    apply_supersession(store, _edge("p-a", "Miso", source_id="src-A",
                                    conf=0.5), DEFAULT_RELATIONS)
    incoming = _edge("w-b", "cat Miso", source_id="src-B")
    plan, _ = _build_supersession_plan(store, incoming, DEFAULT_RELATIONS,
                                       "sup-w-b")
    assert plan.contribution_drafts == []       # the planner already refused
    # force the draft on anyway, as a store-level caller could
    plan.contribution_drafts = [ContributionDraft(
        site="absorption", survivor_type="edge", survivor_id="w-b",
        contributor_type="edge", contributor_id="p-a")]
    plan.prior_invalidations = [("p-a", incoming.valid_from,
                                 "absorbed_duplicate")]
    plan.absorption_pre_image = {"observed_at": "2026-06-01T00:00:00Z",
                                 "confidence": 0.9, "disclosure": "mentionable",
                                 "valid_from": "2026-06-01T00:00:00Z"}
    with pytest.raises(SupersessionIntegrityError, match="scope"):
        store.apply_supersession_plan(plan)
    assert {e.id for e in store.edges(U, active_only=True)} == {"p-a"}
    assert store.contributions(U, "edge", "w-b") == []
    store.close()


# --------------------------------------------------------------------------- #
# W15 — the reopen cell (the rest lives in tests/test_0021_import_linkage.py)
# --------------------------------------------------------------------------- #

def test_import_contribution_primitive_membership_after_reopen(tmp_path):
    """W15's durability cell: membership is IDENTICAL after close/reopen.

    The other W15 obligations — pre-commit refusal leaving the destination
    byte-identical, mid-plan rollback, idempotent re-import, concurrent
    linearization — are executed in `tests/test_0021_import_linkage.py`
    (`test_refusal_cell_leaves_destination_unchanged`,
    `test_midplan_failure_rolls_back_the_whole_commit`,
    `test_reimport_is_idempotent_rows_skip_counted_existing`,
    `test_concurrent_same_plan_commits_linearize_no_duplicates`) and are not
    duplicated here."""
    from veracium import portability
    src = _store(tmp_path, "src.db")
    for eid, obj, conf in (("A", "Miso", 0.2), ("B", "cat Miso", 0.5),
                           ("C", "small cat Miso", 0.9)):
        apply_supersession(src, _edge(eid, obj, source_id="src-A", conf=conf),
                           DEFAULT_RELATIONS)
    exp = tmp_path / "u.jsonl"
    portability.export_memory(src, U, str(exp))
    src.close()

    dest = SqliteStore(str(tmp_path / "dest.db"))
    portability.import_memory(dest, str(exp), restore=True)
    before = MembershipResolver(dest, U).evidence(
        next(e for e in dest.edges(U, active_only=True)))
    dest.close()

    again = SqliteStore(str(tmp_path / "dest.db"))
    after = MembershipResolver(again, U).evidence(
        next(e for e in again.edges(U, active_only=True)))
    assert before == after
    # an imported CONSOLIDATION derivative would arrive without membership
    # evidence — the ledger is LOCAL and does not travel (§2c); absorption
    # survivors are the case the reconstruction restores
    again.close()


# --------------------------------------------------------------------------- #
# DEFERRED — stated, never silent
# --------------------------------------------------------------------------- #

@pytest.mark.skip(reason="W6 is the LIVE / D-extension cross-principal value "
                         "probe: it needs a real model and the benchmark "
                         "harness, and a simulated leak probe measures the "
                         "simulation")
def test_no_cross_principal_leak_through_maintenance():
    """W6 — deferred, offline-unreachable. See the module docstring."""


@pytest.mark.skip(reason="W16's reparenting half needs apply_retention_prune_"
                         "plan, which §7a names FUTURE and §2c-ii asserts "
                         "executably has no shipped writer; the born-closed "
                         "half is covered by test_transitive_absorption_chains")
def test_closure_survives_pruning():
    """W16 — half-deferred. See the module docstring."""


@pytest.mark.skip(reason="W17 is the shipped evidence program "
                         "specs/evidence/0020/ledger_plan_harness.py, which "
                         "extracts the REAL contribution_ledger DDL from a "
                         "live store; a pytest copy would be a weaker second "
                         "implementation")
def test_ledger_plan_against_real_ddl():
    """W17 — carried by the evidence harness. See the module docstring."""


@pytest.mark.skip(reason="W18's after-a-prune half needs apply_retention_"
                         "prune_plan (FUTURE); the before half is "
                         "test_native_chain_export_carries_absorbed_by_id_on_"
                         "both_absorbed in tests/test_0021_import_linkage.py")
def test_export_reverse_link_unique():
    """W18 — half-deferred. See the module docstring."""
