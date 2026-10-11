"""Runs package II's reference model: invariants on the draft's rules, mutants (each must be killed by the invariant
that names it), and probes of the draft's open points and contradictions. With `--out <path>` it writes the machine-readable results there."""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grounding_model as M  # noqa: E402

R = M.Rules()


def E(i, ungrounded=False, version=M.GROUNDING_VERSION, obj=None, rel="works_as"):
    return M.Edge(id=i, user="u", relation=rel, obj=obj or f"obj-{i}", ungrounded=ungrounded, version=version)


def store(*edges):
    s = M.Store()
    for e in edges:
        s.edges[e.id] = e
    return s


# ----------------------------------------------------------------------------------------------- invariants
def inv_legacy_never_attested(rules=R):
    """INV-G1 (R1-02): a row written before the grounding version is never `attested`, flagged or not — the mutant R1-02
    names (old false/missing flag = positively attested) must fail; a post-version unflagged row IS attested."""
    s = store(E("old", False, 15), E("oldf", True, 15), E("new", False))
    return (M.grounding(s, s.edges["old"], rules) == "unknown" and M.grounding(s, s.edges["oldf"], rules) != "attested"
            and M.grounding(s, s.edges["new"], rules) == "attested")


def inv_context_never_clears(rules=R):
    """INV-G2 (R1-06): context text — even 'I withdraw my dispute' — never clears a challenge; a structured resolve
    clears exactly the one it names; with two challenges, resolving one leaves one open and still blocks confirm."""
    e = E("e"); s = store(e)
    c1 = M.add_reply(s, e, "challenge", "wrong job"); c2 = M.add_reply(s, e, "challenge", "also wrong")
    M.add_reply(s, e, "context", "I withdraw my dispute")
    still = len(M.active_challenges(s, e)) == 2
    M.add_reply(s, e, "resolve", "", target=c1.id)
    one = [r.id for r in M.active_challenges(s, e)] == [c2.id]
    try:
        M.confirm(s, e); blocked = False
    except M.Refused:
        blocked = True
    M.add_reply(s, e, "resolve", "", target=c2.id)
    M.confirm(s, e)
    return still and one and blocked


def inv_gate_is_restriction_only(rules=R):
    """INV-G3 (R1-05): no grid cell promotes an edge an existing gate refused."""
    e = E("e"); s = store(e)
    return M.gate(s, e, rules, existing_ok=False) == "not_assertable"


def inv_unit_or_withheld(rules=R):
    """INV-G4 (R1-05): a challenged fact renders WITH its unit or not at all; the open count is all challenges, not the
    budget-selected ones."""
    e = E("e"); s = store(e)
    for i in range(3):
        M.add_reply(s, e, "challenge", f"no {i}")
    full = M.render(s, e, rules, budget=10_000)
    tight = M.render(s, e, rules, budget=len(f"{e.relation}: {e.obj}") + 2)
    return full is not None and "3 open" in full and tight is None


def inv_absorption_keeps_acts(rules=R):
    """INV-G5 (R1-03): absorption never moves or discards a person's act: a prior carrying a confirmation or a reply is
    NOT absorbed, its acts stay on it, and no confirmation is copied to the more specific incoming."""
    p = E("p", True, obj="Miso"); i = E("i", False, obj="big cat Miso"); s = store(p)
    M.confirm(s, p)
    out = M.absorb(s, p, i, rules)
    return (out == "not_absorbed" and s.edges["p"].active and not any(c.edge == "i" for c in s.confirmations)
            and M.grounding(s, p, rules) == "confirmed")


def inv_no_new_inferred(rules=R):
    """INV-G6 (R1-03, A9): after the grounding version, no NEW edge is `inferred` without having gone through a
    proposal — including the survivor of an act-free absorption."""
    p = E("p", True, version=15, obj="Miso"); i = E("i", False, obj="big cat Miso"); s = store(p)
    M.absorb(s, p, i, rules)
    return M.grounding(s, s.edges["i"], rules) != "inferred"


def inv_legacy_flag_keeps_marker(rules=R):
    """INV-G7 (accepted 0019 U5): a flagged row renders its marker on every code-rendered surface — legacy (`unknown`)
    rows included."""
    e = E("oldf", True, 15); s = store(e)
    line = M.render(s, e, rules, budget=10_000)
    return line is not None and "[possible extraction error]" in line


def inv_proposal_lifetime(rules=R):
    """INV-G8 (R1-04, R1-09): a proposal dies on redaction / revocation / forget / a key change; a non-USER source or a
    missing episode mints none (counted); confirmation of a live proposal writes ONE edge + ONE row."""
    s = store()
    ok = []
    for kill in ("redact", "revoke", "forget", "rekey"):
        p = M.mint(s, "u", "works_as", f"x-{kill}", f"ep-{kill}", f"src-{kill}")
        if kill == "redact": s.redacted_episodes.add(p["episode"])
        if kill == "revoke": s.revoked_sources.add(p["source"])
        if kill == "forget": s.forgotten_users.add("u")
        if kill == "rekey": s.key = b"other"
        try:
            M.confirm_inference(s, p, actor="h", call_path="host", correlation_id=f"k-{kill}"); ok.append(False)
        except M.Refused:
            ok.append(True)
        s.forgotten_users.discard("u"); s.key = b"store-key-1"
    s2 = store()
    none_assist = M.mint(s2, "u", "works_as", "x", "ep", "src", author="assistant") is None
    none_ep = M.mint(s2, "u", "works_as", "x", None, "src") is None
    counted = s2.counts["unattested_refused"] == 1 and s2.counts["unattested_unproposable"] == 1
    p = M.mint(s2, "u", "works_as", "nurse", "ep1", "src")
    M.confirm_inference(s2, p, actor="h", call_path="host", correlation_id="c1")
    one = len(s2.edges) == 1 and len(s2.confirmations) == 1
    return all(ok) and none_assist and none_ep and counted and one


def inv_replay(rules=R):
    """INV-G9 (R1-09): same id + same request replays; same id + a different proposal is refused."""
    s = store()
    p = M.mint(s, "u", "works_as", "nurse", "ep1", "src"); q = M.mint(s, "u", "works_as", "baker", "ep2", "src")
    a = M.confirm_inference(s, p, actor="h", call_path="host", correlation_id="c1")
    b = M.confirm_inference(s, p, actor="h", call_path="host", correlation_id="c1")
    try:
        M.confirm_inference(s, q, actor="h", call_path="host", correlation_id="c1"); refused = False
    except M.Refused:
        refused = True
    return a == b and refused and len(s.confirmations) == 1


def inv_import_authority(rules=R):
    """INV-G10 (R1-07, R1-08): default import refuses an act aimed at a PRE-EXISTING local edge (the reply-only attack);
    a fresh round trip (edge + its reply into an empty store) is ADMITTED; an orphan act is refused."""
    local = E("loc"); s = store(local); M.confirm(s, local)
    forged = M.Reply(id="f1", edge="loc", kind="challenge", text="forged", t=1)
    try:
        M.import_rows(s, [], [], [forged], "default"); attack = False
    except M.Refused:
        attack = True
    s2 = store(); ex = E("x"); r = M.Reply(id="r1", edge="x", kind="challenge", text="mine", t=1)
    M.import_rows(s2, [ex], [], [r], "default")
    roundtrip = "x" in s2.edges and len(s2.replies) == 1
    try:
        M.import_rows(store(), [], [], [M.Reply(id="o", edge="nowhere", kind="context", text="", t=1)], "default"); orphan = False
    except M.Refused:
        orphan = True
    return attack and roundtrip and orphan and M.gate(s, local, rules) == "assertable"


INVARIANTS = {"INV-G1": inv_legacy_never_attested, "INV-G2": inv_context_never_clears,
              "INV-G3": inv_gate_is_restriction_only, "INV-G4": inv_unit_or_withheld,
              "INV-G5": inv_absorption_keeps_acts, "INV-G6": inv_no_new_inferred,
              "INV-G7": inv_legacy_flag_keeps_marker, "INV-G8": inv_proposal_lifetime,
              "INV-G9": inv_replay, "INV-G10": inv_import_authority}


def run_invariants(rules=R) -> dict:
    out = {}
    for k, f in INVARIANTS.items():
        try:
            out[k] = bool(f(rules))
        except Exception as x:
            out[k] = f"ERROR {type(x).__name__}: {x}"
    return out


# ----------------------------------------------------------------------------------------------- mutants
def _set(name, fn):
    return lambda: setattr(M, name, fn)


def _grounding_old_false_attested(s, e, rules, at=None):
    return "attested" if not e.ungrounded else ("confirmed" if any(c.edge == e.id for c in s.confirmations) else "inferred")


def _challenges_context_clears(s, e, at=None):
    rs = [r for r in s.replies if r.edge == e.id]
    if any(r.kind == "context" and "withdraw" in r.text for r in rs):
        return []
    return [r for r in rs if r.kind == "challenge"]


def _gate_promotes(s, e, rules, existing_ok=True, at=None):
    return "assertable"


_orig_render = M.render


def _render_budget_selected(s, e, rules, budget, at=None):
    line = _orig_render(s, e, rules, 10_000, at)
    if line is None:
        return None
    return line if len(line) <= budget else line.split(" [challenged")[0]   # drops the unit to fit


def _absorb_copy_acts(s, prior, incoming, rules):
    s.edges[incoming.id] = incoming; prior.active = False
    for c in [c for c in s.confirmations if c.edge == prior.id]:
        s.confirmations.append(M.Confirmation(id=c.id + "'", edge=incoming.id, t=c.t, actor=c.actor,
                                              correlation_id=c.correlation_id, digest=c.digest))
    return "absorbed"


_orig_confirm_inf = M.confirm_inference


def _confirm_no_lifetime(s, p, **kw):
    s2_red, s2_rev, s2_fg, key = set(s.redacted_episodes), set(s.revoked_sources), set(s.forgotten_users), s.key
    s.redacted_episodes.clear(); s.revoked_sources.clear(); s.forgotten_users.clear()
    p = dict(p); p["token"] = M.hmac.new(s.key, M.canonical(p), M.hashlib.sha256).hexdigest()
    try:
        return _orig_confirm_inf(s, p, **kw)
    finally:
        s.redacted_episodes |= s2_red; s.revoked_sources |= s2_rev; s.forgotten_users |= s2_fg; s.key = key


def _confirm_replay_any(s, p, **kw):
    rec = s.corr.get((p["user"], kw["correlation_id"]))
    if rec is not None:
        return rec[1]                                                   # same id ALWAYS replays (no digest check)
    return _orig_confirm_inf(s, p, **kw)


_orig_import = M.import_rows


def _import_trust_acts(s, edges, confirmations, replies, mode):
    return _orig_import(s, edges, confirmations, replies, "trusted")    # edge cap kept? no: acts trusted


def _rules(**kw):
    import functools
    def install():
        for name in ("grounding", "gate", "render", "absorb"):
            f = getattr(M, name)
            def wrap(f=f):
                @functools.wraps(f)
                def g(*a, **k):
                    a = tuple(M.Rules(**{**vars(x), **kw}) if isinstance(x, M.Rules) else x for x in a)
                    return f(*a, **k)
                return g
            setattr(M, name, wrap())
    return install


MUTANTS = {
    "draft 1: unknown suppresses a legacy flag's marker (G3)": ("INV-G7", _rules(unknown_renders_marker_if_flagged=False, legacy_flag_precedence="unknown")),
    "draft 1: the OR rule flags a post-version survivor (G2)": ("INV-G6", _rules(absorption_or_post_version=True)),
    "old false/missing flag treated as attested (R1-02)": ("INV-G1", _set("grounding", _grounding_old_false_attested)),
    "a context reply mentioning withdrawal clears all challenges (R1-06)": ("INV-G2", _set("active_challenges", _challenges_context_clears)),
    "a grid cell promotes an otherwise ineligible edge (R1-05)": ("INV-G3", _set("gate", _gate_promotes)),
    "budget selection drops the challenge unit to fit (R1-05)": ("INV-G4", _set("render", _render_budget_selected)),
    "absorption copies every confirmation to the more specific survivor (R1-03)": ("INV-G5", _set("absorb", _absorb_copy_acts)),
    "proposal lifetime not re-checked at confirmation (R1-04)": ("INV-G8", _set("confirm_inference", _confirm_no_lifetime)),
    "same correlation id always replays, whatever the request (R1-09)": ("INV-G9", _set("confirm_inference", _confirm_replay_any)),
    "default import trusts every incoming act (R1-08)": ("INV-G10", _set("import_rows", _import_trust_acts)),
}


def run_mutants() -> dict:
    names = ("grounding", "active_challenges", "gate", "render", "absorb", "confirm_inference", "import_rows")
    pristine = {k: getattr(M, k) for k in names}
    out = {}
    for name, (owner, install) in MUTANTS.items():
        install()
        try:
            res = run_invariants()
        finally:
            for k, v in pristine.items():
                setattr(M, k, v)
        killed = sorted(k for k, v in res.items() if v is not True)
        out[name] = {"owner": owner, "killed_by": killed, "killed_by_owner": owner in killed}
    return out


# ----------------------------------------------------------------------------------------------- probes
def probes() -> dict:
    p = {}
    for v in ("assertable_with_unit", "not_assertable"):
        e = E("oldc", False, 15); s = store(e); M.add_reply(s, e, "challenge", "no")
        p[f"§10.2 unknown+challenge[{v}]"] = M.gate(s, e, M.Rules(unknown_with_challenge=v))
    for v in ("flag_first", "unknown", "confirmed"):
        e = E("lfc", True, 15); s = store(e); M.confirm(s, e)
        p[f"G1 legacy flagged+confirmed precedence[{v}]"] = M.grounding(s, e, M.Rules(legacy_flag_precedence=v))
    for v in (False, True):
        e = E("lf", True, 15); s = store(e)
        p[f"G3 legacy flagged row's marker, unknown_renders_marker={v}"] = M.render(s, e, M.Rules(unknown_renders_marker_if_flagged=v), 10_000)
    for v in (True, False):
        pr = E("p", True, version=15, obj="Miso"); i = E("i", False, obj="big cat Miso"); s = store(pr)
        M.absorb(s, pr, i, M.Rules(absorption_or_post_version=v))
        p[f"G2 act-free absorption survivor grounding, OR rule={v}"] = M.grounding(s, s.edges["i"], M.Rules())
    for n in (1, 2, 5):
        e = E("e"); s = store(e)
        for k in range(n):
            M.add_reply(s, e, "challenge", f"c{k}")
        p[f"§10.4 render with {n} open"] = M.render(s, e, R, 10_000)
    return p


def main() -> int:
    inv = run_invariants(); mut = run_mutants(); pr = probes()
    ok = all(v is True for v in inv.values()) and all(m["killed_by_owner"] for m in mut.values())
    res = {"model": "package II reference model", "rules_draft_sha256_prefix": "d9ec36f4",
           "rules_draft_commit": "93b0d285", "invariants": inv, "mutants": mut, "probes": pr,
           "verdict": "PASS" if ok else "FAIL"}
    if "--out" in sys.argv:                 # results go to a path the CALLER names; never beside this file, so a
        out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])   # test run leaves the tracked tree untouched
        out.write_text(json.dumps(res, indent=2, default=str) + "\n")
    for k, v in inv.items():
        print(f"{'ok  ' if v is True else 'FAIL'} {k}: {'' if v is True else v}")
    for k, v in mut.items():
        print(f"{'KILLED  ' if v['killed_by_owner'] else 'SURVIVED'} {k} -> by {v['killed_by']} (owner {v['owner']})")
    for k, v in pr.items():
        print(f"probe {k}: {v!r}")
    print("VERDICT:", res["verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
