"""Runs the 0044 stage-1 reference model: every invariant on the draft's rules, every declared mutant (each must be
killed by EXACTLY the invariant that names it), and the probes of the draft's open points and ambiguities. Writes
`arity-model-results.json`; exit 0 iff all invariants hold and every mutant is killed by its own invariant."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import arity_model as M  # noqa: E402

R = M.Rules()


def E(i, rel="measures", obj="x", user="u", source="src-a", basis=()):
    return M.Edge(id=i, user=user, relation=rel, obj=obj, source=source, basis=basis)


def base(registry=None):
    """p (weight 78) superseded by n (weight 80) under the old `single` arity, then the plan written."""
    s = M.Store()
    p, n = E("p", obj="weight 78"), E("n", obj="weight 80")
    s.edges["p"] = p
    M.supersede_single(s, p, n)
    return s


def plan(s, registry=None):
    M.write_plan(s, registry or {})
    return s


# ----------------------------------------------------------------------------------------------- invariants
def inv_revocation(rules=R):
    """INV-M1 (R1-01): a row whose source — or a contribution-basis source — is in the standing revocation set is
    WITHHELD, never active, and the receipt says so; a non-revoked control IS restored."""
    s = base()
    q, m = E("q", obj="weight 60", source="feed-A"), E("m", obj="weight 61")
    s.edges["q"] = q; M.supersede_single(s, q, m)
    c, d = E("c", obj="weight 50", basis=("feed-B",)), E("d", obj="weight 51")
    s.edges["c"] = c; M.supersede_single(s, c, d)
    s.revoked |= {"feed-A", "feed-B"}
    plan(s); M.migrate(s, rules)
    out = {r["edge"]: r["outcome"] for r in M.receipt(s, "u")}
    return (out.get("q") == "withheld_revoked" and not s.edges["q"].active
            and out.get("c") == "withheld_revoked" and not s.edges["c"].active
            and out.get("p") == "restored" and s.edges["p"].active)


def inv_once_per_plan(rules=R):
    """INV-M2 (R1-03): migrate → undo → rerun does NOT re-select the undone row; an immediate rerun changes nothing; a
    crash before a user's commit leaves that user untouched and resume completes; a crash after commit loses nothing
    (the receipt is a view, recoverable at any time)."""
    s = plan(base()); M.migrate(s, rules)
    M.undo(s, "u", "p", rules, correlation_id="c1")
    snap = copy.deepcopy(s.edges)
    M.migrate(s, rules, op_id="op-2")
    rerun_ok = not s.edges["p"].active and {k: v.active for k, v in s.edges.items()} == {k: v.active for k, v in snap.items()}
    s2 = plan(base())
    try:
        M.migrate(s2, rules, crash_user="u", crash_at="mid_user")
    except M.Crash:
        pass
    untouched = not s2.edges["p"].active and not s2.outcomes and not s2.runs
    M.migrate(s2, rules)
    resumed = s2.edges["p"].active
    s3 = plan(base())
    try:
        M.migrate(s3, rules, crash_user="u", crash_at="after_commit")
    except M.Crash:
        pass
    recovered = [r["outcome"] for r in M.receipt(s3, "u")] == ["restored"]
    # the case where the once-per-plan check (§3.4) is the ONLY guard: no run-row skip applies to import conversion.
    # The user undid the restoration, the row was later removed locally, and an old (pre-0044) export is re-imported:
    # the undone row must arrive retired, not be restored again. (A rerun alone cannot show this — the per-user run row
    # already skips the user, so the two guards are redundant there; each guard needs its own case.)
    old_export = M.export(base(), "u", fmt="pre")
    s4 = plan(base()); M.migrate(s4, rules); M.undo(s4, "u", "p", rules, correlation_id="c1")
    del s4.edges["p"]; del s4.edges["n"]
    M.import_file(s4, old_export, "default", rules)
    undo_survives_reimport = not s4.edges["p"].active
    return rerun_ok and untouched and resumed and recovered and undo_survives_reimport


def inv_successor_evidence(rules=R):
    """INV-M3 (R1-04): two restatements then one replacement: the pointer names ONE prior, so the other's successor is
    'unknown' — never guessed."""
    s = M.Store()
    p1, p2, n = E("p1", obj="weight 78"), E("p2", obj="weight 78"), E("n", obj="weight 80")
    s.edges["p1"] = p1; s.edges["p2"] = p2
    t = s.tick()
    for pr in (p1, p2):
        pr.active, pr.invalidated_at, pr.reason = False, t, "superseded"
    n.supersedes = "p2"; s.edges["n"] = n
    plan(s); M.migrate(s, rules)
    rb = {r["edge"]: r["replaced_by"] for r in M.receipt(s, "u")}
    return rb == {"p1": "unknown", "p2": ["n"]}


def inv_undo_identity(rules=R):
    """INV-M4 (R1-05, P-7): an ordinary mutation keeps undo eligibility; undo restores the retirement fields ONLY
    (later counters survive); same id + same request replays the result; a later retirement by another operation
    ends eligibility with its reason named."""
    s = plan(base()); M.migrate(s, rules)
    s.edges["p"].counters += 3; s.journal.append(("mutated", "p", s.tick()))
    r1 = M.undo(s, "u", "p", rules, correlation_id="c1")
    kept = s.edges["p"].counters == 3 and s.edges["p"].reason == "superseded" and not s.edges["p"].active
    r2 = M.undo(s, "u", "p", rules, correlation_id="c1")
    s2 = plan(base()); M.migrate(s2, rules)
    s2.edges["p"].active, s2.edges["p"].invalidated_at, s2.edges["p"].reason = False, s2.tick(), "disputed"
    try:
        M.undo(s2, "u", "p", rules); ended = False
    except M.Refused as x:
        ended = "disputed" in str(x)
    return kept and r1 == r2 and ended


def inv_custom_registry(rules=R):
    """INV-M5 (R1-06): a host that declares its own `measures` as single gets no plan row and no restoration; the
    default declaration does."""
    s = plan(base(), {"measures": "custom-single"}); M.migrate(s, rules)
    s2 = plan(base()); M.migrate(s2, rules)
    return not s.edges["p"].active and "measures" not in s.plan and s2.edges["p"].active


def inv_doctor(rules=R):
    """INV-M6 (§7): a restored pair reads `info`, not `warn`; after undo nothing reports; an unrelated active-predecessor
    pair still warns (the exemption is not a blanket)."""
    s = plan(base()); M.migrate(s, rules)
    restored = M.doctor_refs(s) == [("info", "n", "p")]
    M.undo(s, "u", "p", rules, correlation_id="c1")
    after = M.doctor_refs(s) == []
    s.edges["z"] = E("z", rel="prefers", obj="tea"); s.edges["y"] = E("y", rel="prefers", obj="coffee"); s.edges["y"].supersedes = "z"
    unrelated = ("warn", "y", "z") in M.doctor_refs(s)
    return restored and after and unrelated


def inv_portability(rules=R):
    """INV-M7 (P-4, P-5): a pre-format file's retired rows are converted on import (incoming rows only); a local undo is
    never reversed by an import; a post-format file's superseded row with no outcome is kept retired and reported
    unknown-linkage; a restored pair imported with its outcome keeps doctor's exemption (the journal is NOT carried)."""
    src = base()                                       # never migrated: a pre-0044 export
    f_pre = M.export(src, "u", fmt="pre")
    dst = M.Store(); dst.clock = 100; plan(dst)
    rec = M.import_file(dst, f_pre, "default", rules)
    converted = ("p", "restored") in rec["converted"] and dst.edges["p"].active
    loc = plan(base()); M.migrate(loc, rules); M.undo(loc, "u", "p", rules, correlation_id="c1")
    rec2 = M.import_file(loc, f_pre, "default", rules)
    undo_kept = not loc.edges["p"].active and "p" in rec2["skipped_collisions"]
    post = plan(base()); post.outcomes.clear()
    dst2 = M.Store(); dst2.clock = 100; plan(dst2)
    rec3 = M.import_file(dst2, M.export(post, "u", fmt="post"), "default", rules)
    unknown = "p" in rec3["unknown_linkage"] and not dst2.edges["p"].active
    mig = plan(base()); M.migrate(mig, rules)
    dst3 = M.Store(); dst3.clock = 100; plan(dst3)
    M.import_file(dst3, M.export(mig, "u", fmt="post"), "trusted", rules)
    exempt = M.doctor_refs(dst3) == [("info", "n", "p")] and not dst3.journal
    # §11.3 ruling: DEFAULT import's testimony earns NO exemption — the warning stays
    dst4 = M.Store(); dst4.clock = 100; plan(dst4)
    M.import_file(dst4, M.export(mig, "u", fmt="post"), "default", rules)
    default_warns = M.doctor_refs(dst4) == [("warn", "n", "p")]
    # F5: a pre-format row retired AFTER the destination's effective_at (the source upgraded later) IS converted
    src = base(); src.clock = 500
    late, ln = E("late", obj="weight 70"), E("ln", obj="weight 71"); src.edges["late"] = late; M.supersede_single(src, late, ln)
    dst5 = M.Store(); dst5.clock = 100; plan(dst5)
    rec5 = M.import_file(dst5, M.export(src, "u", fmt="pre"), "default", rules)
    late_converted = ("late", "restored") in rec5["converted"] and dst5.edges["late"].active
    return converted and undo_kept and unknown and exempt and default_warns and late_converted


def inv_redaction(rules=R):
    """INV-M8 (INV-A7): a redacted superseded row is never restored, by either redaction arm."""
    s = base(); M.redact(s, "p"); plan(s); M.migrate(s, rules)
    return not s.edges["p"].active


def inv_order_key(rules=R):
    """INV-M9 (the 0003 amendment v1.3 §4a: R1-07, R1-08): the key is TOTAL over the post-visibility representation —
    a renderable singleton, an equal-authority pair (gap 0), a group with nothing renderable (sorts last) — and ranks by
    the RENDERABLE top, so a hidden higher member cannot outrank a visible one (the reviewer's groups H and U); an
    UNRESOLVED member is never used; and a visible contended pair is MORE ambiguous than a visible singleton."""
    H = [(3, "U"), (2, "R")]                 # user prior hidden; system fact rendered
    U = [(3, "R"), (0, "U")]                 # user prior rendered; challenger fenced
    none = [(3, "O"), (1, "U")]
    single = [(3, "R")]
    pair = [(3, "R"), (1, "R")]
    equal = [(3, "R"), (3, "R")]
    try:
        k = {n: M.order_key(g) for n, g in (("H", H), ("U", U), ("none", none), ("single", single), ("pair", pair), ("equal", equal))}
    except Exception:
        return False
    order = sorted(k, key=k.get)
    unresolved_unused = M.order_key([(3, "R"), (2, "U")]) == M.order_key([(3, "R")])
    # two fully rendered pairs: the closer contention (3,2) ranks before (3,1) — ambiguity over V∖{t}, not O alone
    closer_first = M.order_key([(3, "R"), (2, "R")]) < M.order_key([(3, "R"), (1, "R")])
    return (order.index("U") < order.index("H") and order[-1] == "none" and order.index("equal") < order.index("pair")
            < order.index("single") and unresolved_unused and closer_first)




def inv_undo_id_scope(rules=R):
    """INV-M10 (F2): a correlation id is USER-scoped: reused on a different edge it is REFUSED, not taken as fresh."""
    s = M.Store(); a, b, n1, n2 = E("a", obj="weight 1"), E("b", obj="weight 2"), E("n1", obj="weight 3"), E("n2", obj="weight 4")
    s.edges["a"] = a; M.supersede_single(s, a, n1); s.edges["b"] = b; M.supersede_single(s, b, n2)
    plan(s); M.migrate(s, rules)
    M.undo(s, "u", "a", rules, correlation_id="same")
    try:
        M.undo(s, "u", "b", rules, correlation_id="same")
        return False
    except M.Refused as x:
        return "different request" in str(x) and s.edges["b"].active


def inv_idless_duplicate(rules=R):
    """INV-M11 (F3): a duplicate undo WITHOUT an id returns the recorded "already undone at T" — not a refusal, and
    no second write."""
    s = plan(base()); M.migrate(s, rules)
    first = M.undo(s, "u", "p", rules)
    t = s.outcomes[next(k for k in s.outcomes if k[1] == "p")]["undone_at"]
    clock = s.clock
    second = M.undo(s, "u", "p", rules)
    return first["already_undone_at"] is None and second["already_undone_at"] == t and s.clock == clock


def inv_retained_refusals(rules=R):
    """INV-M12 (§1, §11.4): a refusal recorded while `single` stays contested after reclassification, with no expiry,
    until a verb retires a member; a refusal stamped after effective_at is not retained."""
    s = M.Store()
    p, i = E("rp", obj="weight 78"), E("ri", obj="weight 80")
    s.edges["rp"] = p; s.edges["ri"] = i; s.refusals.append(("rp", "ri", "measures", s.tick()))
    plan(s); M.migrate(s, rules)
    for _ in range(50):
        s.tick()                                                         # time passes: no expiry
    kept = M.contested_pairs(s) == [("rp", "ri")]
    s.edges["ri"].active, s.edges["ri"].invalidated_at, s.edges["ri"].reason = False, s.tick(), "corrected"
    ended = M.contested_pairs(s) == []
    s2 = M.Store(); s2.edges["a"] = E("a", obj="w 1"); s2.edges["b"] = E("b", obj="w 2"); plan(s2)
    s2.refusals.append(("a", "b", "measures", s2.tick()))                 # stamped AFTER effective_at
    return kept and ended and M.contested_pairs(s2) == []


INVARIANTS = {"INV-M1": inv_revocation, "INV-M2": inv_once_per_plan, "INV-M3": inv_successor_evidence,
              "INV-M4": inv_undo_identity, "INV-M5": inv_custom_registry, "INV-M6": inv_doctor,
              "INV-M7": inv_portability, "INV-M8": inv_redaction, "INV-M9": inv_order_key,
              "INV-M10": inv_undo_id_scope, "INV-M11": inv_idless_duplicate, "INV-M12": inv_retained_refusals}


# ----------------------------------------------------------------------------------------------- mutants
def _consider_without(check):
    orig = M.consider

    def mutant(s, e, rules):
        if check == "once":
            saved = dict(s.outcomes); s.outcomes.clear()
            try:
                return orig(s, e, rules)
            finally:
                s.outcomes.update(saved)
        return orig(s, e, rules)
    return mutant


MUTANTS = {
    # name: (the invariant that must kill it, how to install it)
    "omit standing-revocation check (R1-01)": ("INV-M1", lambda: setattr(M, "would_be_revoked", lambda s, e: False)),
    "selector-only completion: no outcome-row check (R1-03)": ("INV-M2", lambda: setattr(M, "consider", _consider_without("once"))),
    "guess the successor from the latest same-relation row (R1-04)": ("INV-M3", None),
    "undo eligibility = latest journal event is 'reinstated' (R1-05)": ("INV-M4", None),
    "undo restores the whole pre-snapshot, counters included (R1-05)": ("INV-M4", None),
    "name-only selector: plan ignores the registry (R1-06)": ("INV-M5", lambda: setattr(M, "write_plan", _plan_name_only)),
    "doctor exemption keyed on the journal (R1-05, P-5)": ("INV-M7", None),
    "import conversion rescans local rows (P-4)": ("INV-M7", None),
    "order key over ALL members, not renderable ones (R1-08)": ("INV-M9", lambda: setattr(M, "order_key", _key_global)),
    "ambiguity over O = visible-but-not-emitted only (the amendment's first wording)": ("INV-M9", lambda: setattr(M, "order_key", _key_o_only)),
    "doctor exemption as a blanket: every active-predecessor pair reads info (§7)": ("INV-M6", None),
    "redaction keeps the relation (a future 0041 change) AND eligibility drops arm (2) (INV-A7)": ("INV-M8", None),
    "draft 1's id lookup per (plan, edge) (F2)": ("INV-M10", None),
    "draft 1's refusal of an id-less duplicate undo (F3)": ("INV-M11", None),
    "the effective_at time test applied to imported rows (F5)": ("INV-M7", None),
    "default import's testimony earns the doctor exemption (§11.3)": ("INV-M7", None),
    "retained refusals expire after a time (§11.4)": ("INV-M12", None),
}


def _key_o_only(group, o_reading="other_than_top", negative="as_is", slot="s"):
    return _PRISTINE_KEY(group, o_reading="non_emitted", negative=negative, slot=slot)


_PRISTINE_KEY = M.order_key


def _plan_name_only(s, registry):
    t = s.tick()
    for rel in M.PLAN_RELATIONS:
        s.plan[rel] = {"plan_id": f"plan-{rel}", "effective_at": t}
    return s.plan


def _key_global(group, o_reading="other_than_top", negative="as_is", slot="s"):
    allm = sorted((a for a, _k in group), reverse=True)              # every member, hidden and UNRESOLVED included
    if not any(k == "R" for _a, k in group):
        return (1, 0, 0, 0, slot)
    return (0, -allm[0], (allm[0] - allm[1]) if len(allm) > 1 else float("inf"), -len(allm), slot)


def _install_successor_guess():
    orig = M.receipt

    def receipt(s, user):
        rows = orig(s, user)
        for r in rows:
            if r["replaced_by"] == "unknown":
                cands = sorted((x for x in s.edges.values() if x.active and x.relation == s.edges[r["edge"]].relation),
                               key=lambda x: x.id)
                r["replaced_by"] = [cands[-1].id] if cands else "unknown"
        return rows
    M.receipt = receipt


def _install_latest_event():
    orig = M.undo

    def undo(s, user, edge_id, rules, correlation_id=None):
        last = [j for j in s.journal if j[1] == edge_id]
        if not last or last[-1][0] != "reinstated":
            raise M.Refused("latest event is not reinstated")
        return orig(s, user, edge_id, rules, correlation_id)
    M.undo = undo


def _install_whole_snapshot():
    orig = M.undo

    def undo(s, user, edge_id, rules, correlation_id=None):
        r = orig(s, user, edge_id, rules, correlation_id)
        s.edges[edge_id].counters = 0                                   # the stale snapshot's counter value
        return r
    M.undo = undo


def _install_journal_exemption():
    def doctor_refs(s):
        out = []
        for e in s.edges.values():
            pred = s.edges.get(e.supersedes) if e.supersedes else None
            if e.active and pred is not None and pred.active:
                last = [j for j in s.journal if j[1] == pred.id]
                ex = bool(last) and last[-1][0] == "reinstated"
                out.append(("info" if ex else "warn", e.id, pred.id))
        return out
    M.doctor_refs = doctor_refs


def _install_rescan():
    orig = M.import_file

    def import_file(s, f, mode, rules, op_id="op-import"):
        rec = orig(s, f, mode, rules, op_id)
        if f["format"] == "pre":
            for e in s.edges.values():
                if e.reason == "superseded" and e.relation in s.plan:
                    e.active, e.invalidated_at, e.reason = True, None, None
        return rec
    M.import_file = import_file


def _install_blanket_exemption():
    orig = M.doctor_refs
    M.doctor_refs = lambda st: [("info", e, pr) for _lvl, e, pr in orig(st)]


def _install_redaction_two_fault():
    def redact(st, edge_id):
        st.edges[edge_id].obj = M.MARKER                               # relation kept: arm (1) no longer protects
    orig = M.consider

    def consider(st, e, rules):
        saved = set(st.attested_redactions); st.attested_redactions.clear()
        obj = e.obj; e.obj = obj if obj != M.MARKER else "x"           # arm (2) dropped: the marker is not looked at
        try:
            return orig(st, e, rules)
        finally:
            e.obj = obj; st.attested_redactions |= saved
    M.redact, M.consider = redact, consider


def _rules_swap(**kw):
    """Install a mutant that changes one RULE: wrap every module entry point so it runs under the altered Rules."""
    import functools
    for name in ("migrate", "migrate_user", "undo", "import_file", "consider"):
        f = getattr(M, name)

        def wrap(f=f):
            @functools.wraps(f)
            def g(*a, **k):
                a = tuple(M.Rules(**{**vars(x), **kw}) if isinstance(x, M.Rules) else x for x in a)
                if "rules" in k:
                    k["rules"] = M.Rules(**{**vars(k["rules"]), **kw})
                return f(*a, **k)
            return g
        setattr(M, name, wrap())


def _install_expiring_refusals():
    orig = M.contested_pairs
    M.contested_pairs = lambda st: [pr for pr in orig(st) if st.clock - next(t for a, b, _r, t in st.refusals if (a, b) == pr) < 20]


INSTALL = {"draft 1's id lookup per (plan, edge) (F2)": lambda: _rules_swap(undo_id_scope="plan_edge"),
           "draft 1's refusal of an id-less duplicate undo (F3)": lambda: _rules_swap(undo_without_id_duplicate="refuse"),
           "the effective_at time test applied to imported rows (F5)": lambda: _rules_swap(time_test_on_import=True),
           "default import's testimony earns the doctor exemption (§11.3)": lambda: _rules_swap(default_import_earns_exemption=True),
           "retained refusals expire after a time (§11.4)": _install_expiring_refusals,
           "doctor exemption as a blanket: every active-predecessor pair reads info (§7)": _install_blanket_exemption,
           "redaction keeps the relation (a future 0041 change) AND eligibility drops arm (2) (INV-A7)": _install_redaction_two_fault,
           "guess the successor from the latest same-relation row (R1-04)": _install_successor_guess,
           "undo eligibility = latest journal event is 'reinstated' (R1-05)": _install_latest_event,
           "undo restores the whole pre-snapshot, counters included (R1-05)": _install_whole_snapshot,
           "doctor exemption keyed on the journal (R1-05, P-5)": _install_journal_exemption,
           "import conversion rescans local rows (P-4)": _install_rescan}


def run_invariants(rules=R) -> dict:
    res = {}
    for name, f in INVARIANTS.items():
        try:
            res[name] = bool(f(rules))
        except Exception as x:                                          # an exception is a failure, named
            res[name] = f"ERROR {type(x).__name__}: {x}"
    return res


def run_mutants() -> dict:
    out = {}
    pristine = {k: getattr(M, k) for k in ("would_be_revoked", "consider", "write_plan", "order_key", "receipt",
                                           "undo", "doctor_refs", "import_file", "redact", "migrate",
                                           "migrate_user", "contested_pairs")}
    for name, (owner, install) in MUTANTS.items():
        (install or INSTALL[name])()
        try:
            res = run_invariants()
        finally:
            for k, v in pristine.items():
                setattr(M, k, v)
        killed_by = sorted(k for k, v in res.items() if v is not True)
        out[name] = {"owner": owner, "killed_by": killed_by, "killed_by_owner": owner in killed_by}
    return out


# ----------------------------------------------------------------------------------------------- probes of the draft
def probes() -> dict:
    p = {}
    # (A) is `withheld_redacted` reachable under the draft's order of checks?
    s = base(); M.redact(s, "p"); plan(s); M.migrate(s, R)
    p["redacted_row_considered_at_all"] = any(k[1] == "p" for k in s.outcomes)
    s = base(); M.redact(s, "p"); plan(s)
    try:
        M.migrate(s, M.Rules(redaction_check_before_relation=True))
        p["withheld_redacted_if_redaction_checked_first"] = any(o["outcome"] == "withheld_redacted" for o in s.outcomes.values())
    except KeyError as x:      # the outcome row is keyed by plan_id, found from `relation` — which redaction REPLACED
        p["withheld_redacted_if_redaction_checked_first"] = f"UNRECORDABLE: no plan for relation {x} (redaction replaced it)"
    # (B) undo correlation id reused on a DIFFERENT edge
    for scope in ("plan_edge", "user"):
        s = M.Store(); a, b, n1, n2 = E("a", obj="weight 1"), E("b", obj="weight 2"), E("n1", obj="weight 3"), E("n2", obj="weight 4")
        s.edges["a"] = a; M.supersede_single(s, a, n1); s.edges["b"] = b; M.supersede_single(s, b, n2)
        rules = M.Rules(undo_id_scope=scope); plan(s); M.migrate(s, rules)
        M.undo(s, "u", "a", rules, correlation_id="same")
        try:
            M.undo(s, "u", "b", rules, correlation_id="same"); r = "ACCEPTED as a fresh request (one id, two requests)"
        except M.Refused as x:
            r = f"refused: {x}"
        p[f"undo_id_reused_on_another_edge[{scope}]"] = r
    # (C) a duplicate undo with NO correlation id
    for mode in ("refuse", "replay_state"):
        s = plan(base()); rules = M.Rules(undo_without_id_duplicate=mode); M.migrate(s, rules); M.undo(s, "u", "p", rules)
        try:
            p[f"undo_duplicate_without_id[{mode}]"] = f"returned {M.undo(s, 'u', 'p', rules)}"
        except M.Refused as x:
            p[f"undo_duplicate_without_id[{mode}]"] = f"refused: {x}"
    # (D) the 0003 amendment v1.3 §4a: the two readings of "O", on a fully rendered contended pair vs a singleton
    for o in ("other_than_top", "non_emitted"):
        ks = {n: M.order_key(g, o_reading=o) for n, g in (("singleton(3)", [(3, "R")]), ("pair(3,1) both rendered", [(3, "R"), (1, "R")]))}
        p[f"O_reading[{o}]"] = {"order": sorted(ks, key=ks.get), "pair_ambiguity": ks["pair(3,1) both rendered"][2]}
        # the decisive case: two fully rendered pairs, gap 1 vs gap 2 — the closer contention should rank first
        k2 = {n: M.order_key(g, o_reading=o) for n, g in (("pair(3,1)", [(3, "R"), (1, "R")]), ("pair(3,2)", [(3, "R"), (2, "R")]))}
        p[f"O_reading[{o}] two rendered pairs"] = {"order": sorted(k2, key=k2.get),
                                                    "ambiguities": {n: v[2] for n, v in k2.items()}}
    # QO4: a visible-but-not-emitted member ABOVE the rendered top (negative ambiguity)
    for neg in ("as_is", "last"):
        ks = {n: M.order_key(g, negative=neg) for n, g in (("negative(2R,3O)", [(2, "R"), (3, "O")]), ("pair(2,1)", [(2, "R"), (1, "R")]))}
        p[f"QO4_negative[{neg}]"] = sorted(ks, key=ks.get)
    # (E) §11.2 later-created user, both settings
    for v in (True, False):
        s = plan(base()); s.edges["w"] = E("w", user="later", obj="weight 9"); M.migrate(s, M.Rules(empty_run_row_for_new_user=v))
        p[f"later_user_run_row[{v}]"] = any(k[1] == "later" for k in s.runs)
    # (F) §8: whose effective_at governs an imported row? the destination's plan, by construction of the model —
    # a pre-format row superseded AFTER the destination's effective_at is NOT converted
    src = base(); src.clock = 500
    late, ln = E("late", obj="weight 70"), E("ln", obj="weight 71"); src.edges["late"] = late; M.supersede_single(src, late, ln)
    dst = M.Store(); dst.clock = 100; plan(dst)
    rec = M.import_file(dst, M.export(src, "u", fmt="pre"), "default", R)
    p["pre_format_row_retired_after_destination_effective_at_converted"] = any(e == "late" for e, _ in rec["converted"])
    return p


def main() -> int:
    inv = run_invariants()
    mut = run_mutants()
    pr = probes()
    ok = all(v is True for v in inv.values()) and all(m["killed_by_owner"] for m in mut.values())
    res = {"model": "0044 stage 1 reference model", "rules_draft_sha256_prefix": "ff39bb49aa151b1e", "rules_draft_commit": "74c51aaf",
           "invariants": inv, "mutants": mut, "probes": pr, "verdict": "PASS" if ok else "FAIL"}
    if "--out" in sys.argv:                 # results go to a path the CALLER names; never beside this file, so a
        out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])   # test run leaves the tracked tree untouched
        out.write_text(json.dumps(res, indent=2, default=str) + "\n")
    for k, v in inv.items():
        print(f"{'ok  ' if v is True else 'FAIL'} {k}: {v if v is not True else ''}")
    for k, v in mut.items():
        print(f"{'KILLED  ' if v['killed_by_owner'] else 'SURVIVED'} {k} -> by {v['killed_by']} (owner {v['owner']})")
    for k, v in pr.items():
        print(f"probe {k}: {v}")
    print("VERDICT:", res["verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
