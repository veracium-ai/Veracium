"""0026 §3a — the relay lexicon's mutation matrix.

P1's pointer target for `specs/evidence/0026/validate_lexicon.py`. The
matrix script is the ORACLE; this test runs it and then plants the mutants a
reviewer would reach for, requiring the oracle to catch each. A matrix that
cannot fail is a matrix that establishes nothing.

0026 is a DRAFT and this touches no guarded module: the lexicon lives under
`specs/evidence/` until acceptance, and this test exercises it there.
"""
from __future__ import annotations

import importlib
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVID = ROOT / "specs" / "evidence" / "0026"
ARTIFACT = EVID / "validate_lexicon.py"

# module-level, not inside _fresh: the round-1-fold tests import the
# evidence modules directly, and under pytest-randomly they can run
# before any test that called _fresh() — a lazily inserted path made the
# whole grammar family order-dependent (37 failures on some seeds)
sys.path.insert(0, str(EVID))


def _fresh():
    sys.path.insert(0, str(EVID))
    import relay_lexicon
    importlib.reload(relay_lexicon)
    import validate_lexicon
    importlib.reload(validate_lexicon)
    return relay_lexicon, validate_lexicon


def test_the_matrix_script_runs_clean_on_the_shipped_lexicon():
    r = subprocess.run([sys.executable, str(ARTIFACT)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, (
        f"specs/evidence/0026/validate_lexicon.py fails on the shipped "
        f"lexicon:\n{r.stdout}{r.stderr}")


def test_relay_lexicon_mutation_matrix(monkeypatch):
    """Each mutant is a way the lexicon could be wrong while looking fine.

    Two of them are not hypothetical — `possessive_third_party` and
    `user_third_person` both shipped in lex-1 and were caught by measuring,
    each in the direction that makes the checker look better than it is.
    """
    # the artifact this matrix binds, named IN THE BODY: P1 refuses a
    # pointer whose test only mentions it in a docstring or a module-level
    # constant, because that is satisfied by an unrelated test in the same
    # file (PROCESS-R23-1).
    artifact = ROOT / "specs" / "evidence" / "0026" / "validate_lexicon.py"
    assert artifact.exists(), "specs/evidence/0026/validate_lexicon.py is gone"

    L, V = _fresh()
    assert V.problems() == [], "the matrix must start clean"

    def mutate(**attrs):
        for k, v in attrs.items():
            monkeypatch.setattr(L, k, v)
        return V.problems()

    # 1. the reviewer's first move: empty the table. A lexicon that matches
    #    nothing reports a clean sheet forever.
    assert mutate(_VERBS=(), _PHRASES=()), (
        "an EMPTY lexicon passed the matrix — a vacuous checker is the "
        "presumed-faking rule's own target")
    monkeypatch.undo()

    # 2. direction inverted: the user's own word treated as a relay. This is
    #    lex-1's defect, and it is the one the 2% bar is decided by.
    L, V = _fresh()
    assert mutate(_USER_SUBJ=()), (
        "dropping the third-person-user subjects left the matrix green — "
        "'user confirmed X' would be floored as somebody else's claim")
    monkeypatch.undo()

    # 3. RETIRED under lex-3, with the reason stated rather than deleted:
    #    the my/our-as-subject mutation is now HARMLESS BY CONSTRUCTION —
    #    the backward scan resolves the noun HEAD ("doctor" in "my doctor
    #    said"), so a possessive in the subject table changes nothing. A
    #    mutant that cannot alter behaviour cannot be killed and does not
    #    belong in the matrix. Its lex-3 successors, each of a load-bearing
    #    grammar rule (0026-R1-1):
    # 3a. agent rule neutered: "price stated by user" reads inbound — the
    #     reduced-passive counterexample returns
    L, V = _fresh()
    monkeypatch.setattr(L, "_agent_after", lambda toks, idx: None)
    assert V.problems(), (
        "neutering the post-verbal agent rule left the matrix green — "
        "'stated by user' would be somebody else's claim again")
    monkeypatch.undo()
    # 3b. adverb skipping dropped: "user also said…" reads the adverb as
    #     a third-party subject head, the user's own word restricted.
    #     (The _BE_FORMS mutant was considered and REJECTED as unkillable:
    #     the unknown-token fallback yields the same direction on every
    #     cell, so the passive rule is explicitness, not mechanism — a
    #     mutant that cannot alter behaviour does not belong here.)
    L, V = _fresh()
    assert mutate(_SKIP_TOKENS=frozenset()), (
        "dropping the skip tokens left the matrix green — an adverb "
        "between subject and verb would restrict the user's own word")
    monkeypatch.undo()
    # 3c. ambiguity dropped: "she said…" resolves to a third party — the
    #     silent-assumption defect in the other direction
    L, V = _fresh()
    assert mutate(_AMBIG_PRON=()), (
        "dropping the ambiguous-pronoun class left the matrix green — "
        "she/he/they would silently classify instead of restricting "
        "with a counted outcome")
    monkeypatch.undo()
    # 3e. a single verb dropped (lex-5, research's FN finding): removing
    #     `claimed` alone must fail — the recall cells make verb-list
    #     completeness MEASURED, so the next silently omitted verb is a
    #     red matrix, not a silent laundering path
    L, V = _fresh()
    assert mutate(_VERBS=tuple(v for v in L._VERBS
                               if v not in ("claimed", "claims"))), (
        "removing `claimed` left the matrix green — verb-list recall is "
        "enumerated again, not measured")
    monkeypatch.undo()
    # 3h. comitative phrases dropped (lex-8): "the user, along with her
    #     vet, said…" loses its co-speaker — the round-1 co-source class
    #     one syntactic layer up, in the unsafe direction
    L, V = _fresh()
    assert mutate(_COMITATIVE=()), (
        "dropping the comitative set left the matrix green — a "
        "quasi-coordinated co-speaker would go unrestricted")
    monkeypatch.undo()
    # 3i. the OWNERSHIP CARVE-OUT reintroduced (lex-10, R4-1): a rewrite
    #     that reads "my own record/account" as user-authored again must
    #     be caught by the ownership-vs-authorship cells — ownership is
    #     not authorship, and the relapse is the laundering direction
    L, V = _fresh()
    assert not hasattr(L, "_SELF_ARTIFACTS"), (
        "the artifact carve-out is back as a constant — R4-1 removed it; "
        "any reintroduction needs its own reviewed amendment")
    _orig_classify = L._classify_source

    def _relapse(head_tokens):
        toks = [t for t in head_tokens if t not in L._DETERMINERS
                and t not in L._SKIP_TOKENS]
        if (toks and toks[0] in ("my", "our", "user's", "users'")
                and len(toks) > 2 and toks[1] in L._FIRST_PERSON_SELF):
            return "user"                # lex-9's mistake, replayed
        return _orig_classify(head_tokens)

    monkeypatch.setattr(L, "_classify_source", _relapse)
    assert V.problems(), (
        "reintroducing the owned-artifact-is-user inference left the "
        "matrix green — the ownership-vs-authorship cells are not biting")
    monkeypatch.undo()
    # 3f. Unicode normalization dropped (lex-7): the curly-apostrophe
    #     possessive tokenizes as fragments and "the user's doctor"
    #     classifies as the user again
    L, V = _fresh()
    monkeypatch.setattr(L, "_APOSTROPHES", str.maketrans({}))
    assert V.problems(), (
        "dropping apostrophe normalization left the matrix green — a "
        "curly possessive defeats every possessive rule")
    monkeypatch.undo()
    # 3g. possessive attachment dropped (lex-7): "the user's doctor"
    #     reads its possessor as the source
    L, V = _fresh()
    monkeypatch.setattr(L, "_is_possessive", lambda tok: False)
    assert V.problems(), (
        "dropping possessive attachment left the matrix green — a "
        "possessed head would classify by its possessor")
    monkeypatch.undo()
    # 3d. coordinator transparency dropped (lex-4): "the vet examined the
    #     cat and said…" attributes nothing again — the elided
    #     third-party subject vanishes across the VP coordination
    L, V = _fresh()
    assert mutate(_COORD=frozenset()), (
        "dropping coordinator transparency left the matrix green — the "
        "coordinated co-source and the elided shared subject both "
        "vanish, the unsafe direction")
    monkeypatch.undo()

    # 4. the agentless participle treated as attribution: 'recommended brand'
    L, V = _fresh()
    monkeypatch.setattr(L, "_direction",
                        lambda toks, idx, lookback=4: "inbound")
    assert V.problems(), (
        "a participle with NO subject was accepted as attribution — that "
        "single error class was 79% of lex-1's fires")
    monkeypatch.undo()

    # 5. `per` without the unit exclusion: every rate becomes a source
    L, V = _fresh()
    assert mutate(_PER_UNITS=frozenset()), (
        "dropping the unit exclusion left the matrix green — '3 sessions "
        "per week' would name a source")
    monkeypatch.undo()

    # 6. case sensitivity: the scan lowercases, so an uppercased table can
    #    never match anything it claims to
    L, V = _fresh()
    assert V.problems() == [], "restore failed"
    r = subprocess.run([sys.executable, str(artifact)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, "the shipped lexicon must end clean"


def test_the_lexicon_refuses_a_vacuous_table_at_load():
    """V4: refusal is at LOAD, so a hollow lexicon can never be used."""
    sys.path.insert(0, str(EVID))
    import relay_lexicon as L
    importlib.reload(L)
    with pytest.raises(L.LexiconError):
        original = L._VERBS
        try:
            L._VERBS = ()
            L._validate_lexicon()
        finally:
            L._VERBS = original


# ---- 0026-R1-1: the directional GRAMMAR, exhaustively -----------------------
#
# The lex-2 rule was a 4-token proximity scan, and proximity is not
# authorship: the reviewer's five executed counterexamples (passive
# recipient, passive with named agent, reduced-passive user agent, embedded
# clause, ambiguous pronoun) all classified wrongly. lex-3 is a grammar;
# this matrix enumerates its domain rather than its motivating cases.

def _cls(text):
    """Every attribution verb in `text` with its lex-3 direction."""
    RL = importlib.import_module("relay_lexicon")
    toks = RL._tokens(text)
    return {t: RL._direction(toks, i)
            for i, t in enumerate(toks) if t in RL._VERBS}


def test_the_reviewers_five_counterexamples_verbatim():
    assert _cls("I was told by my doctor to rest")["told"] == "inbound"
    assert _cls("user was told by the vet to fast the cat")["told"] \
        == "inbound"
    assert _cls("price stated by user")["stated"] == "outbound"
    got = _cls("user said their doctor confirmed the dosage")
    assert got["said"] == "outbound" and got["confirmed"] == "inbound"
    assert _cls("she said the user needs medication")["said"] == "ambiguous"


# The grammar's domain, as a generated cross-product: for each VOICE the
# relevant identity axis (active: the subject; passive/reduced: the agent)
# crossed with every identity class, expected direction derived from the
# design rule, not hand-picked examples.
_IDENTITY = {
    # class -> (subject-position surface, agent-position surface, direction
    #           when that identity is the SOURCE of the attribution)
    "first_person":  ("i",           "me",          "outbound"),
    "user_3rd":      ("user",        "user",        "outbound"),
    # R4-1: a self-POSSESSED artifact restricts — ownership is not
    # authorship (the account's producer may be a bank or a doctor)
    "self_poss":     ("my own account", "my own account", "inbound"),
    "third_noun":    ("doctor",      "the doctor",  "inbound"),
    "third_poss":    ("my doctor",   "my doctor",   "inbound"),
    "their_poss":    ("their vet",   "their vet",   "inbound"),
    "ambig_pron":    ("she",         "her",         "ambiguous"),
}


@pytest.mark.parametrize("ident", sorted(_IDENTITY))
@pytest.mark.parametrize("verb", ["said", "told", "stated", "confirmed"])
def test_active_voice_subject_governs(ident, verb):
    subj, _agent, want = _IDENTITY[ident]
    got = _cls(f"{subj} {verb} the medication schedule")
    assert got.get(verb) == want, (ident, verb, got)


@pytest.mark.parametrize("ident", sorted(_IDENTITY))
@pytest.mark.parametrize("recipient", ["i", "user", "the client"])
def test_passive_voice_agent_governs(ident, recipient):
    """Whatever precedes the verb (the RECIPIENT), the post-verbal agent
    decides — the recipient axis must be inert."""
    _subj, agent, want = _IDENTITY[ident]
    got = _cls(f"{recipient} was told by {agent} to rest")
    assert got.get("told") == want, (ident, recipient, got)


@pytest.mark.parametrize("ident", sorted(_IDENTITY))
def test_reduced_passive_agent_governs(ident):
    """`<noun> stated by <agent>` — no auxiliary, agent still governs."""
    _subj, agent, want = _IDENTITY[ident]
    got = _cls(f"price stated by {agent}")
    assert got.get("stated") == want, (ident, got)


def test_passive_with_unnamed_source_is_conservatively_inbound():
    assert _cls("i was told to rest")["told"] == "inbound"
    assert _cls("user was informed about the change")["informed"] \
        == "inbound"


@pytest.mark.parametrize("outer,inner,want_outer,want_inner", [
    ("user", "their doctor", "outbound", "inbound"),
    ("i", "my doctor", "outbound", "inbound"),
    ("my doctor", "user", "inbound", "outbound"),
    ("she", "user", "ambiguous", "outbound"),
])
def test_embedded_clauses_classify_independently(outer, inner,
                                                 want_outer, want_inner):
    got = _cls(f"{outer} said {inner} confirmed the dosage")
    assert got.get("said") == want_outer, got
    assert got.get("confirmed") == want_inner, got


def test_no_subject_attributes_nothing():
    assert _cls("recommended brand") == {}
    assert _cls("confirmed no allergies")["confirmed"] == "none" or \
        "confirmed" not in {k: v for k, v in
                            _cls("confirmed no allergies").items()
                            if v != "none"}


def test_ambiguity_restricts_and_is_counted_separately():
    """The explicit conservative outcome: relay_markers includes the
    ambiguous set (over-restriction is the safe failure in a
    restrict-only design), and scan exposes the split so §6a can COUNT
    ambiguity instead of hiding it in either bucket."""
    RL = importlib.import_module("relay_lexicon")
    r = RL.scan("she said the user needs medication", None)
    assert r["ambiguous"] and not r["inbound"]
    assert RL.relay_markers("she said the user needs medication", None)
    r2 = RL.scan("user confirmed no dietary restrictions", None)
    assert not r2["ambiguous"] and not r2["inbound"] and r2["outbound"]


# ---- 0026-EVIDENCE-R1-1: the aggregate is bound, not asserted ---------------

def _agg_and_mod():
    import json
    MF = importlib.import_module("measure_false_positives")
    agg = json.loads((ROOT / "specs" / "evidence" / "0026"
                      / "fp_aggregate.json").read_text())
    return MF, agg


def test_the_shipped_fp_aggregate_validates():
    """The reviewer's finding verbatim: nothing read fp_aggregate.json —
    fires 415→0, coverage→0 and lexicon 0026-lex-999 all passed the
    whole gate. This test IS the reader, through the closed validator
    with its cross-artifact manifest anchor."""
    MF, agg = _agg_and_mod()
    assert MF.validate_aggregate(agg) == []


def test_fp_aggregate_validator_matrix():
    """Each mutant is one of the reviewer's executed tamperings, plus the
    internal-consistency and cross-artifact classes they generalize to.
    The artifact this matrix binds, named in the body: P1's rule."""
    import copy
    import json
    artifact = ROOT / "specs" / "evidence" / "0026" / \
        "measure_false_positives.py"
    assert artifact.exists()
    MF, agg = _agg_and_mod()

    def refused(mutate, needle):
        m = copy.deepcopy(agg)
        mutate(m)
        bad = MF.validate_aggregate(m)
        assert bad, f"the {needle} tampering validated clean"
        assert any(needle in b for b in bad), (needle, bad[:3])

    # the reviewer's three, verbatim
    refused(lambda m: m["grounded_first_person"].__setitem__("fires", 0),
            "exceeds fires")            # markers now exceed zero fires
    refused(lambda m: m["coverage"].__setitem__("matched_by_lexicon",
                                                10**6),
            "numerators exceed")
    refused(lambda m: m.__setitem__("lexicon_version", "0026-lex-999"),
            "some other detector")
    # the classes they generalize to
    refused(lambda m: m.__setitem__("schema", 1), "not 3")
    refused(lambda m: m.__setitem__("banana", 1), "CLOSED")
    refused(lambda m: m["manifest"].__setitem__("entries", 1),
            "disagrees with the 0011/0025")
    refused(lambda m: m["manifest"].__setitem__(
        "sha256", "0" * 64), "disagrees with the 0011/0025")
    refused(lambda m: m["grounded_first_person"].__setitem__(
        "fires", m["grounded_first_person"]["total"] + 1),
        "outside")
    refused(lambda m: m["grounded_first_person"].__setitem__(
        "fires_ambiguous_only",
        m["grounded_first_person"]["fires"] + 1),
        "exceeds fires")
    refused(lambda m: m["grounded_first_person"]["markers"].__setitem__(
        "said", True), "positive count")
    # privacy: a foreign key in a marker table could carry corpus content
    # into the shipped record (the census C3 class) — and a marker outside
    # the closed lexicon cannot have fired
    refused(lambda m: m["grounded_first_person"]["markers"].__setitem__(
        "the user's actual sentence here", 1), "member of the shipped")


def test_the_real_entry_point_verifies_and_refuses(tmp_path):
    """Both boundaries driven as commands: --aggregate on the shipped
    record passes; on a tampered copy it refuses with exit 1; --cache
    together with --aggregate refuses at the CLI (exactly one mode)."""
    import json
    script = ROOT / "specs" / "evidence" / "0026" / \
        "measure_false_positives.py"
    shipped = ROOT / "specs" / "evidence" / "0026" / "fp_aggregate.json"
    r = subprocess.run([sys.executable, str(script),
                        "--aggregate", str(shipped)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-300:]
    assert "RECORDED ONLY" in r.stdout
    d = json.loads(shipped.read_text())
    d["grounded_first_person"]["fires"] = 0
    bad = tmp_path / "tampered.json"
    bad.write_text(json.dumps(d, sort_keys=True, indent=1))
    r = subprocess.run([sys.executable, str(script),
                        "--aggregate", str(bad)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1 and "REFUSED" in r.stderr
    r = subprocess.run([sys.executable, str(script), "--cache", "x",
                        "--aggregate", str(shipped)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0


def test_structured_candidate_field_binds_to_the_package_record(monkeypatch):
    """0026-PACKAGE-R1-1: the round-1 SENT row called the candidate v3 in
    one sentence and v4 in another, and identity verified VALID —
    candidate revision was prose. It is a structured `candidate=` field
    now, and a row whose field disagrees with package_identity's record
    refuses."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "pi_test", ROOT / "specs" / "package_identity.py")
    PI = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(PI)
    assert PI.validate() == [], "pristine control"
    real = PI._reviews()
    swapped = []
    for r in real:
        if (r["spec"] == "0026" and r.get("kind") == "external"
                and r.get("round") == 1
                and r["verdict"].startswith("SENT")):
            r = dict(r, candidate={"0026": "v999"})
        swapped.append(r)
    monkeypatch.setattr(PI, "_reviews", lambda: swapped)
    bad = PI.validate()
    assert any("0026-PACKAGE-R1-1" in b and "v999" in b for b in bad), bad


@pytest.mark.parametrize("text,verb,want", [
    ("the vet and I said the diet works", "said", "inbound"),
    ("my wife and I said it was fine", "said", "inbound"),
    ("the vet and she said to fast", "said", "inbound"),
    ("the vet examined the cat and said no allergies", "said", "inbound"),
    ("user visited the clinic and said no allergies", "said", "outbound"),
    ("my sister said the vet said it is fine", "said", "inbound"),
])
def test_coordination_and_nesting_shapes(text, verb, want):
    """lex-4 (pre-emptive, the shapes research named for their red-team
    pass): a coordinated user subject restricts via its co-source; an
    elided third-party subject survives VP coordination; a user-subject
    shared across a VP coordination stays outbound; nesting keeps the
    inner relay. Both new rules err toward over-restriction — the safe
    direction — and the §6a re-measurement prices them (lex-4: 418 =
    0.61%, still under the bar)."""
    assert _cls(text).get(verb) == want


def _spec_section(heading):
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    i = spec.index(heading)
    j = spec.find("\n## ", i)
    j2 = spec.find("\n### ", i + len(heading))
    end = min(x for x in (j, j2, len(spec)) if x > i)
    return spec[i:end]


def test_import_matrix_is_total_in_the_spec():
    """0026-R1-2's closure, bound to §3d's own region (not a file-wide
    phrase): the import matrix carries all five input rows, the
    recomputation rule, and the never-consumed contract. Implementation
    lands at acceptance like the rest of §3; until then the spec text IS
    the artifact and this is its structural check."""
    sec = _spec_section("### 3d. The carrier (V6)")
    rows = [l for l in sec.splitlines()
            if l.startswith("|") and "|" in l[1:]]
    body = "\n".join(rows)
    for needle in ("absent, text carries markers",
                   "forged", "malformed", "foreign `lexicon` version",
                   "direction disagrees"):
        assert needle in body, f"import-matrix row {needle!r} missing"
    assert "RECOMPUTES" in sec
    assert "never consumed" in sec
    assert "agreement_import_mismatches" in sec
    # 0026-R2-2: the mode split and the format bump are bound too
    assert "TRUST-FIELD-FAITHFUL, per accepted `0005` P2" in sec
    assert "FORMAT_VERSION bump" in sec
    assert "the reader REFUSES the bumped format" in sec
    assert "restored VERBATIM, disclosure included" in sec


def test_telemetry_deferral_is_bound():
    """0026-R1-3's closure, bound structurally: the deferral statement
    lives in §3d, forbids whitelisting, names the 0015-amendment
    condition — and Spec-Requires consistently does NOT list 0015,
    because a deferred consumer has no prerequisite."""
    sec = _spec_section("### 3d. The carrier (V6)")
    assert "DEFERRED" in sec and "MUST NOT whitelist" in sec
    assert "adds `0015` to `Spec-Requires`" in sec
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    req = next(l for l in spec.splitlines()
               if l.startswith("Spec-Requires:"))
    assert "0015" not in req, (
        "Spec-Requires lists 0015 while telemetry is deferred — the "
        "deferral and the dependency list disagree")
    # 0026-R2-3: the deferral must hold in EVERY carrier — §3c still said
    # "consumed by telemetry from day one" and §9 still named telemetry a
    # consumer while this test inspected §3d alone. Whole-file scan for
    # any surviving affirmative-consumption claim, with the swept
    # carriers' bracketed corrections tolerated by construction (they
    # QUOTE the withdrawn phrasing inside a sweep note).
    low = spec.lower()
    i = 0
    while True:
        i = low.find("consumed by telemetry from day one", i)
        if i < 0:
            break
        context = low[max(0, i - 200):i]
        assert "swept" in context or "previously" in context, (
            "a carrier still AFFIRMS day-one telemetry consumption "
            "outside a sweep note (0026-R2-3): "
            + spec[max(0, i - 80):i + 60])
        i += 1
    sec3c = _spec_section("### 3c. The demotion-direction RECORD")
    assert "DEFERRED per §3d" in sec3c, (
        "§3c does not defer to §3d's telemetry ruling")


def test_the_gate_and_the_doc_are_bound(tmp_path):
    """0026-EVIDENCE-R2-1: fires=2,000 (2.92%, over the 2% gate) verified
    as 'aggregate VALID' — the validator checked shape while the gate
    lived elsewhere; and FP-MEASUREMENT.md carried stale figures beside
    the current ones because nothing compared prose to artifact. Both
    bound now, at the real entry point."""
    import json
    MF, agg = _agg_and_mod()
    # the reviewer's exact tampering: over-gate fires
    import copy
    m = copy.deepcopy(agg)
    m["grounded_first_person"]["fires"] = 2000
    m["grounded_first_person"]["fires_ambiguous_only"] = 0
    m["grounded_first_person"]["markers"] = {"said": 1}
    bad = MF.validate_aggregate(m)
    assert any("OVER the" in b and "2% gate" in b for b in bad), bad
    assert any("adjudication" in b for b in bad), bad
    # doc binding: a drifted shipped figure refuses at the entry point
    script = ROOT / "specs" / "evidence" / "0026" / \
        "measure_false_positives.py"
    doc = (ROOT / "specs" / "evidence" / "0026"
           / "FP-MEASUREMENT.md").read_text()
    g = agg["grounded_first_person"]
    tampered = doc.replace(f"{g['fires']:,} of", f"{g['fires'] + 1:,} of")
    assert tampered != doc
    bad = MF.doc_problems(agg, tampered)
    assert bad, "a drifted headline figure validated clean"
    # and the pristine control through the real command
    r = subprocess.run([sys.executable, str(script), "--aggregate",
                        str(ROOT / "specs" / "evidence" / "0026"
                            / "fp_aggregate.json")],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-300:]
    # 0026-EVIDENCE-R2-1, research's re-verify counterexample: the gate
    # CLAIMED "separately validated" and CHECKED is_file — an EMPTY {}
    # beside a 5%-fires aggregate produced "aggregate VALID". The
    # adjudication is read, closed-schema-validated, and BOUND to this
    # exact aggregate (lexicon version AND fire count):
    over = copy.deepcopy(agg)
    total = over["grounded_first_person"]["total"]
    over["grounded_first_person"]["fires"] = int(total * 0.05)
    over["grounded_first_person"]["fires_ambiguous_only"] = 0
    over["grounded_first_person"]["markers"] = {"said": 1}
    # schema 3: the digest population must agree with the fire count —
    # the test's own synthetic population
    import hashlib
    over["fire_digests"] = sorted(
        hashlib.sha256(f"pop{i}".encode()).hexdigest()
        for i in range(over["grounded_first_person"]["fires"]))
    empty_adj = tmp_path / "e" / "fp_adjudication.json"
    empty_adj.parent.mkdir()
    empty_adj.write_text("{}")
    bad = MF.validate_aggregate(over, adj_path=empty_adj)
    assert any("stub file" in b for b in bad), (
        "an EMPTY adjudication carried an over-gate record", bad)

    import hashlib as _hl

    def _agg_digest(a):
        return _hl.sha256(
            (json.dumps(a, sort_keys=True, indent=1) + "\n").encode()
        ).hexdigest()

    # 0026-EVIDENCE-R6-1: no seed exists — every adjudication is a
    # census (the round-5 projection seed and every sampling successor
    # were retired at face eight of the selection class)

    def _adj_on_disk(name, adj, manifest_lines, raw_bytes=None,
                     co_lines=None, no_co=False):
        """One adjudication record + its sibling manifests in a private
        dir — the validator derives both paths from the record's. The
        co-verification census defaults to CONCURRING labels
        (0026-EVIDENCE-R7-2); no_co=True omits it (the host-only cell),
        co_lines overrides it."""
        d = tmp_path / name
        d.mkdir()
        sp = d / "fp_adjudication_sample.jsonl"
        raw = (raw_bytes if raw_bytes is not None else
               "".join(json.dumps(r) + "\n"
                       for r in manifest_lines).encode())
        sp.write_bytes(raw)
        co_raw = (raw if co_lines is None else
                  "".join(json.dumps(r) + "\n" for r in co_lines).encode())
        if not no_co:
            (d / "fp_coverification_sample.jsonl").write_bytes(co_raw)
        adj = dict(adj, sample_sha256=_hl.sha256(raw).hexdigest(),
                   coverification_sha256=_hl.sha256(co_raw).hexdigest())
        ap = d / "fp_adjudication.json"
        ap.write_text(json.dumps(adj))
        return ap

    def _validate(over_, ap):
        return MF.validate_aggregate(over_, adj_path=ap)

    pop = over["fire_digests"]
    # 0026-EVIDENCE-R6-1 (face EIGHT, terminal): every adjudication is
    # a CENSUS — the manifest labels every fire, exactly; no draw, seed
    # or size choice exists to shop
    SZ = over["grounded_first_person"]["fires"]
    assert SZ == len(pop)
    n_fp = 60
    good_labels = ([{"fire": f, "label": "tp"} for f in pop[n_fp:]]
                   + [{"fire": f, "label": "fp"} for f in pop[:n_fp]])
    good_adj = dict(schema=MF.ADJUDICATION_SCHEMA,
                    lexicon_version=over["lexicon_version"],
                    fires=over["grounded_first_person"]["fires"],
                    sample=dict(size=SZ),
                    verdict="accept",
                    aggregate_sha256=_agg_digest(over))
    # 0026-EVIDENCE-R4-1, the round-4 reviewer's EXACT bypass: schema-2
    # carried counts (tp=100/fp=-50 summed to size and passed). Counts
    # are gone from the record; an old schema refuses on sight:
    bypass = dict(good_adj, schema=2,
                  sample=dict(size=SZ, seed=1, true_positive=100,
                              false_positive=-50))
    bad = _validate(over, _adj_on_disk("bypass", bypass, good_labels))
    assert any(f"not {MF.ADJUDICATION_SCHEMA}" in b for b in bad), bad
    # counts OR a seed smuggled into a current record refuse as unknown
    # keys — no seed exists in a census (0026-EVIDENCE-R6-1)
    smuggle = dict(good_adj)
    smuggle["sample"] = dict(size=SZ, seed=1, true_positive=100,
                             false_positive=-50)
    bad = _validate(over, _adj_on_disk("smuggle", smuggle, good_labels))
    assert any("no seed exists" in b for b in bad), bad
    # a digest that points at NOTHING is not a binding
    d = tmp_path / "dangling"
    d.mkdir()
    ap = d / "fp_adjudication.json"
    ap.write_text(json.dumps(dict(good_adj, sample_sha256="ab" * 32,
                                  coverification_sha256="ab" * 32)))
    bad = _validate(over, ap)
    assert any("points at nothing" in b for b in bad), bad
    # a manifest whose bytes do not hash to sample_sha256 refuses
    d = tmp_path / "wronghash"
    d.mkdir()
    (d / "fp_adjudication_sample.jsonl").write_text("")
    ap = d / "fp_adjudication.json"
    ap.write_text(json.dumps(dict(good_adj, sample_sha256="ab" * 32,
                                  coverification_sha256="ab" * 32)))
    bad = _validate(over, ap)
    assert any("some other census" in b for b in bad), bad
    # a census over the WRONG fires: one population digest substituted
    # for a foreign one refuses (the round-6 single-digest attack has
    # nothing left to shop — but a fabricated member still refuses)
    swapped = ([{"fire": _hl.sha256(b"foreign").hexdigest(),
                 "label": "tp"}] + good_labels[1:])
    bad = _validate(over, _adj_on_disk("swapped", good_adj, swapped))
    assert any("thin air" in b for b in bad), bad
    # a partial census refuses: size must BE the population size...
    part = dict(good_adj, sample=dict(size=500))
    bad = _validate(over, _adj_on_disk("partial", part,
                                       good_labels[:500]))
    assert any("CENSUS" in b for b in bad), bad
    # ...and a manifest that under-labels refuses on census
    # completeness (the reader checks population equality per manifest)
    bad = _validate(over, _adj_on_disk("short", good_adj,
                                       good_labels[:-1]))
    assert any("no more, no fewer" in b for b in bad), bad
    # the same fire labelled twice refuses
    dbl = good_labels[:-1] + [good_labels[0]]
    bad = _validate(over, _adj_on_disk("double", good_adj, dbl))
    assert any("twice" in b for b in bad), bad
    # 0026-EVIDENCE-R3-1, the round-3 case: a REJECT verdict in free
    # text passed. The enum + the computed decision refuse it:
    bad = _validate(over, _adj_on_disk(
        "rej", dict(good_adj, verdict="reject"), good_labels))
    assert any("REJECT" in b for b in bad), bad
    bad = _validate(over, _adj_on_disk(
        "freetext",
        dict(good_adj,
             verdict="REJECT: the rate remains over the 2% gate"),
        good_labels))
    assert any("closed enum" in b for b in bad), bad
    # the EXACT-share boundary, both sides of the bar: at 5.00% of the
    # population, fp=1370 of 3423 puts pct x share at 2.0014% (refuses)
    # and fp=1369 at 1.9999% (accepts) — the census decides exactly
    hot = ([{"fire": f, "label": "fp"} for f in pop[:1370]]
           + [{"fire": f, "label": "tp"} for f in pop[1370:]])
    bad = _validate(over, _adj_on_disk("hot", good_adj, hot))
    assert any("exact census share" in b for b in bad), bad
    cool = ([{"fire": f, "label": "fp"} for f in pop[:1369]]
            + [{"fire": f, "label": "tp"} for f in pop[1369:]])
    bad = _validate(over, _adj_on_disk("cool", good_adj, cool))
    assert bad == [], ("the just-under-the-bar census was refused", bad)
    # 0026-EVIDENCE-R7-2: a HOST-ONLY census is not an adjudication —
    # without the independent co-verification manifest the record
    # refuses, whatever the labels say
    bad = _validate(over, _adj_on_disk("hostonly", good_adj,
                                       good_labels, no_co=True))
    assert any("host-only labels are not an adjudication" in b
               for b in bad), bad
    # the FAIL-CLOSED union: host says all-tp, the co-verifier flags
    # enough fp that the union crosses the bar — the accept refuses
    # (the host's under-labelling incentive cannot win)
    all_tp = [{"fire": f, "label": "tp"} for f in pop]
    co_hot = ([{"fire": f, "label": "fp"} for f in pop[:1370]]
              + [{"fire": f, "label": "tp"} for f in pop[1370:]])
    bad = _validate(over, _adj_on_disk("union", good_adj, all_tp,
                                       co_lines=co_hot))
    assert any("fp-union" in b and "disagreement" in b
               for b in bad), bad
    # a digest for some other aggregate cannot carry this one
    bad = _validate(over, _adj_on_disk(
        "wrongd", dict(good_adj, aggregate_sha256="0" * 64),
        good_labels))
    assert any("some other record" in b for b in bad), bad
    bad = _validate(over, _adj_on_disk(
        "stalelex", dict(good_adj, lexicon_version="0026-lex-999"),
        good_labels))
    assert any("stale verdict" in b for b in bad), bad
    bad = _validate(over, _adj_on_disk(
        "stalefires", dict(good_adj, fires=good_adj["fires"] - 1),
        good_labels))
    assert any("different fires" in b for b in bad), bad
    # 0026-EVIDENCE-R5-3: undecodable bytes are a STRUCTURED refusal,
    # never a crash — for the manifest (hash-bound, invalid UTF-8)...
    bad = _validate(over, _adj_on_disk(
        "badutf8", good_adj, None, raw_bytes=b"\xff\xfe garbage"))
    assert any("not valid UTF-8" in b for b in bad), bad
    # ...and for the adjudication record itself
    d = tmp_path / "badutf8adj"
    d.mkdir()
    (d / "fp_adjudication.json").write_bytes(b"\xff\xfe{}")
    bad = _validate(over, d / "fp_adjudication.json")
    assert any("unreadable or" in b for b in bad), bad
    # 0026-EVIDENCE-R5-2 + R6-2: the doc coverage needle is DERIVED and
    # zero-guarded — a mutated denominator bites, a zero one refuses
    # structurally instead of crashing
    den = copy.deepcopy(agg)
    den["coverage"]["with_nonempty_note"] = 9999
    den["coverage"]["third_party_claim_triples"] = 10000
    doc_now = (ROOT / "specs" / "evidence" / "0026"
               / "FP-MEASUREMENT.md").read_text()
    assert MF.doc_problems(den, doc_now), (
        "a mutated coverage denominator validated clean")
    zero = copy.deepcopy(agg)
    zero["coverage"] = dict(third_party_claim_triples=0,
                            with_nonempty_note=0, matched_by_lexicon=0)
    assert MF.doc_problems(zero, doc_now), (
        "the zero-denominator cell must refuse, and structurally")
    # and a REAL census carries the over-bar record: 80 fp of 3423
    ok_labels = ([{"fire": f, "label": "fp"} for f in pop[:80]]
                 + [{"fire": f, "label": "tp"} for f in pop[80:]])
    bad = _validate(over, _adj_on_disk("good", good_adj, ok_labels))
    assert bad == [], ("a valid census adjudication was refused", bad)


def test_spec_binder_and_round_count_are_bound():
    """0026-EVIDENCE-R3-2 + 0026-PACKAGE-R3-1: the candidate spec is a
    live quantitative carrier — its §6a figures bind to the aggregate
    (a 217-vs-220 drift shipped while the binder covered only the
    measurement doc), and §9's internal-round count binds to the
    structured ledger (the brief said "two rounds" beside a six-round
    ledger)."""
    import importlib.util
    import json as _json
    MF = importlib.import_module("measure_false_positives")
    agg = _json.loads((ROOT / "specs" / "evidence" / "0026"
                       / "fp_aggregate.json").read_text())
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    assert MF.spec_problems(agg, spec) == []
    # 0026-EVIDENCE-R4-2, the reviewer's exact mutations: a 9,999
    # coverage denominator and a lex-999 headline both survived the
    # substring binder — the byte-bound generated block refuses them
    for needle, repl in ((f"of {agg['coverage']['with_nonempty_note']:,} =",
                          "of 9,999 ="),
                         (agg["lexicon_version"], "0026-lex-999")):
        tampered = spec.replace(needle, repl)
        assert tampered != spec, needle
        assert MF.spec_problems(agg, tampered), (
            f"mutating {needle!r} validated clean — the claim block is "
            f"not byte-bound")
    # a hand-edit INSIDE the generated block refuses too
    assert MF.spec_problems(agg, spec.replace(
        "439 fires", "440 fires")), "an in-block figure edit passed"
    # 0026-R4-2: both import-matrix carriers come from the ONE table
    IM = importlib.import_module("import_matrix")
    assert IM.spec_matrix_problems(spec) == []
    assert IM.spec_matrix_problems(spec.replace(
        "RAISES, nothing written", "treated as absent")), (
        "a §3d cell edit validated clean — the matrix is not byte-bound")
    assert IM.spec_matrix_problems(spec.replace(
        "the two modes DIFFER by design", "either mode RAISES")), (
        "a §2c cell edit validated clean")
    # §9's round count AND the front-matter Internal-reviewers row both
    # derive from the ledger (0026-PACKAGE-R3-1 + 0026-PACKAGE-R4-1:
    # round 3 named the header and §9; the fold swept only §9)
    rspec = importlib.util.spec_from_file_location(
        "rv0026", ROOT / "specs" / "reviews.py")
    RV = importlib.util.module_from_spec(rspec)
    rspec.loader.exec_module(RV)
    internal = len([r for r in RV.REVIEWS
                    if r["spec"] == "0026" and r["kind"] == "internal"])
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    assert words.get(internal, str(internal)) + " internal rounds" in spec, (
        f"§9 does not state the ledger's count of {internal} internal "
        f"rounds — the prose has drifted from the structured record")
    assert RV.internal_reviewers_row("0026") in spec, (
        "the Internal-reviewers front-matter row does not byte-match "
        "the ledger's rendering (0026-PACKAGE-R4-1)")
    front = spec.split("\n## ", 1)[0]     # front matter only: history
    assert "READY FOR EXTERNAL" not in front, (   # sections may QUOTE it
        "a static readiness claim survives in the front matter — "
        "readiness is the ledger's state to derive (0026-PACKAGE-R4-1)")


def test_renderers_agree_with_independent_oracles():
    """0026-I7-2 (research's round-4 pre-seal MODERATE find): byte-
    equality binders verify DRIFT (shipped == render), not renderer
    CORRECTNESS — an off-by-one renderer produces wrong-but-self-
    consistent bytes and a re-render passes. Each renderer therefore
    gets an INDEPENDENT oracle: this test computes the figures straight
    from the artifact — never by re-invoking the renderer — and requires
    the rendering to carry them."""
    import copy
    import importlib.util
    import json as _json
    MF = importlib.import_module("measure_false_positives")
    IM = importlib.import_module("import_matrix")
    agg = _json.loads((ROOT / "specs" / "evidence" / "0026"
                       / "fp_aggregate.json").read_text())
    g, c = agg["grounded_first_person"], agg["coverage"]
    r = MF.render_spec_claim(agg)
    # figures computed HERE, from the aggregate
    pct = 100.0 * g["fires"] / g["total"]
    cov = 100.0 * c["matched_by_lexicon"] / c["with_nonempty_note"]
    assert f"`{agg['lexicon_version']}`" in r
    assert f"{g['fires']:,} fires of {g['total']:,} grounded" in r
    assert f"= {pct:.2f}% at the bound" in r
    assert (f"{c['matched_by_lexicon']:,} of "
            f"{c['with_nonempty_note']:,} = {cov:.1f}%") in r
    assert f"{g['suppressed_by_direction_only']:,} suppressed" in r
    assert ("CLEARED (UNDER)" in r) == (pct <= 2.0)
    # both gate branches, driven with a synthetic over-bar aggregate
    hi = copy.deepcopy(agg)
    hi["grounded_first_person"]["fires"] = int(g["total"] * 0.05)
    assert "NOT CLEARED (OVER)" in MF.render_spec_claim(hi)
    # the renderer-mutation cell: an off-by-one renderer is exactly a
    # correct renderer over an off-by-one aggregate — the oracle's
    # needles distinguish it
    off = copy.deepcopy(agg)
    off["grounded_first_person"]["fires"] += 1
    assert f"{g['fires']:,} fires of" not in MF.render_spec_claim(off)
    # import matrix: every cell of the ONE table appears in the §3d
    # rendering, and the cross-carrier facts hold in BOTH renderings
    table = IM.render_3d_table()
    for fmt, mode, state, outcome in IM.MATRIX:
        assert f"| {fmt} | {mode} | {state} | {outcome} |" in table
    restore_malformed = [out for f, m, st, out in IM.MATRIX
                         if m == "restore" and "MALFORMED" in st]
    default_malformed = [out for f, m, st, out in IM.MATRIX
                         if m == "default" and "MALFORMED" in st]
    assert len(restore_malformed) == 1 and "RAISES" in restore_malformed[0]
    assert (len(default_malformed) == 1
            and "treated as absent" in default_malformed[0])
    row2c = IM.render_2c_row()
    assert "restore: **RAISES" in row2c and "treated as absent" in row2c, (
        "§2c must state BOTH modes' malformed outcomes — the round-4 "
        "contradiction cell")
    # internal_reviewers_row: the count computed HERE from the ledger
    rspec = importlib.util.spec_from_file_location(
        "rv0026b", ROOT / "specs" / "reviews.py")
    RV = importlib.util.module_from_spec(rspec)
    rspec.loader.exec_module(RV)
    n = len([x for x in RV.REVIEWS
             if x["spec"] == "0026" and x["kind"] == "internal"])
    words = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten"}
    row = RV.internal_reviewers_row("0026")
    assert f"**{words.get(n, str(n))} internal rounds**" in row
    assert "READY FOR EXTERNAL" not in row


def test_import_matrix_carriers_move_together(monkeypatch):
    """0026-R5-1: round 4's render_2c_row hard-coded its text BESIDE the
    matrix — a mutated matrix regenerated §3d while §2c stayed
    contradictory and the binder returned clean. Both renderers PROJECT
    the table now; this is the source-level mutation test: change a
    MATRIX outcome and BOTH renderings must carry the change."""
    import importlib
    IM = importlib.import_module("import_matrix")
    base_3d, base_2c = IM.render_3d_table(), IM.render_2c_row()
    mutated = tuple(
        (f, m, st,
         "QUIETLY FLOORED INSTEAD" if (m == "restore" and "MALFORMED" in st)
         else out)
        for f, m, st, out in IM.MATRIX)
    monkeypatch.setattr(IM, "MATRIX", mutated)
    new_3d, new_2c = IM.render_3d_table(), IM.render_2c_row()
    assert new_3d != base_3d and "QUIETLY FLOORED INSTEAD" in new_3d
    assert new_2c != base_2c and "QUIETLY FLOORED INSTEAD" in new_2c, (
        "the §2c rendering did not move with the mutated matrix — it is "
        "not a projection (0026-R5-1)")
    # and the shipped spec (rendered from the UNMUTATED table) now fails
    # BOTH binder halves under the mutated module
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    probs = IM.spec_matrix_problems(spec)
    assert any("§3d" in p or "import-matrix" in p for p in probs)
    assert any("§2c" in p for p in probs)
    monkeypatch.undo()
    # research's round-5 pre-seal ask 2: the head-projection is faithful
    # only while heads are pairwise DISTINCT — collide two decisions
    # that differ only in rationale and the projection must REFUSE, not
    # silently under-distinguish
    collided = tuple(
        (f, m, st,
         ("SAME HEAD — first rationale" if (m == "restore"
                                            and "MALFORMED" in st)
          else "SAME HEAD — second rationale" if (m == "default"
                                                  and "MALFORMED" in st)
          else out))
        for f, m, st, out in IM.MATRIX)
    monkeypatch.setattr(IM, "MATRIX", collided)
    with pytest.raises(LookupError, match="heads collide"):
        IM.render_2c_row()


def test_the_worked_adjudication_example_validates_from_disk():
    """0026-PACKAGE-R5-1: the spec claimed the adjudication manifest was
    a SHIPPED artifact while the archive contained none — the live path
    is dormant (under-gate), so no live artifacts can exist. What SHIPS
    is the construction plus this WORKED, clearly-synthetic example —
    validated here from disk, end to end, through the real entry."""
    import importlib
    import json as _json
    MF = importlib.import_module("measure_false_positives")
    D = ROOT / "specs" / "evidence" / "0026" / "adjudication_example"
    agg = _json.loads((D / "demo_aggregate.json").read_text())
    assert MF.validate_aggregate(
        agg, adj_path=D / "fp_adjudication.json") == []
    # 0026-PACKAGE-R6-1: the README once claimed a generator the
    # package did not ship. It ships now — run it into scratch and
    # require BYTE-IDENTICAL output to the shipped artifacts, so the
    # example can never drift from the code defining the schema
    import shutil
    import subprocess
    import sys as _sys
    scratch = D.parent / "_example_regen_scratch"
    try:
        r = subprocess.run(
            [_sys.executable, str(D / "generate_example.py"),
             str(scratch)], capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout + r.stderr
        for name in ("demo_aggregate.json",
                     "fp_adjudication_sample.jsonl",
                     "fp_adjudication.json"):
            assert ((scratch / name).read_bytes()
                    == (D / name).read_bytes()), (
                f"{name}: the shipped example is not what the shipped "
                f"generator generates (0026-PACKAGE-R6-1)")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    # the example is honest about being synthetic: over-gate (the path
    # exercised) and labelled as a census by both parties (R7-2)
    g = agg["grounded_first_person"]
    assert 100.0 * g["fires"] / g["total"] > 2.0
    adj = _json.loads((D / "fp_adjudication.json").read_text())
    assert adj["schema"] == MF.ADJUDICATION_SCHEMA, (
        "the example must carry the CURRENT schema — the constant is "
        "the one carrier of the revision (0026-PACKAGE-R6-1)")
    assert adj["sample"] == {"size": agg["grounded_first_person"]
                             ["fires"]}, "a census record: size only"
    assert "SYNTHETIC" in (D / "README.md").read_text()
    # and the SHIPPED live aggregate needs no adjudication: under-gate
    live = _json.loads((ROOT / "specs" / "evidence" / "0026"
                        / "fp_aggregate.json").read_text())
    lg = live["grounded_first_person"]
    assert 100.0 * lg["fires"] / lg["total"] <= 2.0


def test_live_prose_names_carriers_not_mechanisms():
    """0026-I8-1: prose that RESTATES a mechanism is the one carrier
    the generated-schema pattern cannot bind — the adjudication
    docstring said 'Schema 3' and 'Wilson' two revisions after both
    were deleted. The live docstring must reference the mechanism's
    carriers, and the deleted machinery's names may appear only as
    named history of the drift itself."""
    import importlib
    MF = importlib.import_module("measure_false_positives")
    doc = MF._validate_adjudication.__doc__
    assert "ADJUDICATION_SCHEMA" in doc, (
        "the docstring must point at the one generated revision carrier")
    assert "census" in doc.lower()
    # the stale terms appear ONLY inside the drift's own history note
    for stale in ("Schema 3", "Wilson"):
        for i, line in enumerate(doc.splitlines()):
            if stale in line:
                ctx = " ".join(doc.splitlines()[max(0, i - 2):i + 2])
                assert ("drifted" in ctx or "0026-I8-1" in ctx), (
                    f"{stale!r} appears in live prose outside the "
                    f"drift-history note: {line!r}")
    # and no deleted sampling machinery survives in the module
    for gone in ("_wilson_upper", "canonical_seed", "canonical_draw",
                 "CENSUS_LIMIT", "seed_from_archive"):
        assert not hasattr(MF, gone), (
            f"{gone} is back — sampling ended at EVIDENCE-R6-1")


def test_the_over_gate_pipeline_end_to_end(tmp_path):
    """0026-EVIDENCE-R7-1 + R7-2: the live over-gate census must be
    CREATABLE — round 7 executed a fresh over-gate measurement and got
    exit 1 with nothing emitted, because validation demanded the
    adjudication the emission exists to enable. The whole pipeline,
    through the real main(): measurement reaches the distinct
    OVER-NEEDS-ADJUDICATION state (exit 3, aggregate + FULL-CONTENT
    worklist emitted, acceptance not claimed) → census labelled from
    the worklist → independent co-verification census → final
    --aggregate verification accepts only with BOTH manifests bound."""
    import hashlib as _hl
    import importlib
    import json as _json
    import subprocess
    import sys as _sys
    MF = importlib.import_module("measure_false_positives")
    FIX = ROOT / "specs" / "evidence" / "0026" / "e2e_fixture"
    script = ROOT / "specs" / "evidence" / "0026" / \
        "measure_false_positives.py"
    aggp = tmp_path / "agg.json"
    workp = tmp_path / "worklist.jsonl"

    # stage 1: measurement — the bootstrap state, not a failure
    r = subprocess.run(
        [_sys.executable, str(script),
         "--cache", str(FIX / "fixture_cache.jsonl"),
         "--emit-aggregate", str(aggp), "--worklist", str(workp),
         "--peer-anchor", str(FIX / "fixture_peer.json")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 3, (r.returncode, r.stdout[-400:], r.stderr[-400:])
    assert "NEEDS ADJUDICATION" in r.stdout
    assert "NOT claimed" in r.stdout
    assert aggp.is_file(), "the over-gate aggregate must be emittable"
    agg = _json.loads(aggp.read_text())
    pop = agg["fire_digests"]
    assert len(pop) == 3
    # the worklist is FULL-CONTENT and keyed by digest (R7-2: truncated
    # previews made fires unjudgeable)
    work = [_json.loads(l) for l in workp.read_text().splitlines()]
    assert {w["fire"] for w in work} == set(pop)
    assert all("my doctor said synthetic thing" in w["note"]
               for w in work), "the worklist must carry FULL content"

    # stage 2: the host census + the independent co-verification census
    lines = "".join(_json.dumps({"fire": f, "label": "tp"}) + "\n"
                    for f in sorted(pop))
    (tmp_path / "fp_adjudication_sample.jsonl").write_text(lines)
    co = "".join(_json.dumps({"fire": f, "label": "tp"}) + "\n"
                 for f in sorted(pop))
    (tmp_path / "fp_coverification_sample.jsonl").write_text(co)
    adj = dict(schema=MF.ADJUDICATION_SCHEMA,
               lexicon_version=agg["lexicon_version"],
               fires=3, sample=dict(size=3), verdict="accept",
               aggregate_sha256=_hl.sha256(
                   aggp.read_bytes()).hexdigest(),
               sample_sha256=_hl.sha256(lines.encode()).hexdigest(),
               coverification_sha256=_hl.sha256(co.encode()).hexdigest())
    (tmp_path / "fp_adjudication.json").write_text(_json.dumps(adj))

    # a substituted peer WITHOUT the fixture declaration refuses —
    # the cross-anchor is not silently substitutable (round-7 pre-seal)
    r = subprocess.run(
        [_sys.executable, str(script), "--aggregate", str(aggp),
         "--peer-anchor", str(FIX / "fixture_peer.json")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 2
    assert "not silently substitutable" in r.stderr
    # stage 3: final verification through the real entry — accepts,
    # BRANDED as fixture (all-tp censuses: exact share 0 <= 2%)
    r = subprocess.run(
        [_sys.executable, str(script), "--aggregate", str(aggp),
         "--fixture", "--peer-anchor", str(FIX / "fixture_peer.json")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-500:]
    assert "NOT acceptance evidence" in r.stdout

    # and WITHOUT the co-verification manifest the same record refuses:
    # host-only labels are not an adjudication (R7-2)
    (tmp_path / "fp_coverification_sample.jsonl").unlink()
    r = subprocess.run(
        [_sys.executable, str(script), "--aggregate", str(aggp),
         "--fixture", "--peer-anchor", str(FIX / "fixture_peer.json")],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 1
    assert "host-only labels are not an adjudication" in r.stderr


def test_agreement_shape_bounds_at_the_limit_and_beyond():
    """0026-R8-2: every AGREEMENT_SHAPE bound driven at the limit (must
    pass) and one beyond (must refuse), plus duplicates, closed
    direction, unknown/missing keys, and the pattern edge — the
    executable definition a conforming implementation must match."""
    import importlib
    IM = importlib.import_module("import_matrix")
    S = IM.AGREEMENT_SHAPE
    ok = lambda **kw: IM.agreement_shape_problems(dict(
        {"markers": ["said"], "direction": "inbound",
         "lexicon": "0026-lex-999"}, **kw))
    assert ok() == []
    # marker count: at the limit / one beyond
    at = [f"m{i}" for i in range(S["markers_max_count"])]
    assert ok(markers=at) == []
    assert ok(markers=at + ["extra"]), (
        f"{S['markers_max_count'] + 1} markers must refuse — the "
        f"diagnostic derives from the shape, never restates it "
        f"(0026-PACKAGE-R10-1)")
    # marker length: at the limit / one beyond / below the minimum
    assert ok(markers=["x" * S["marker_max_chars"]]) == []
    assert ok(markers=["x" * (S["marker_max_chars"] + 1)])
    assert ok(markers=[""])
    # duplicates refuse; non-strings refuse; wrong collection refuses
    assert ok(markers=["said", "said"])
    assert ok(markers=["said", 3])
    assert ok(markers="said")
    # direction is a closed enum — §3d's STORED vocabulary exactly
    # (0026-R9-1: user_source is legal, the lexicon-internal 'outbound'
    # reading is not a stored value, and an empty markers array is not
    # a record)
    for d in S["direction_values"]:
        assert ok(direction=d) == []
    assert "user_source" in S["direction_values"]
    assert ok(direction="outbound"), (
        "'outbound' is the lexicon's internal reading, not a stored "
        "direction — it must refuse")
    assert ok(direction="sideways")
    assert ok(markers=[]), "V2: no markers means NO record"
    # lexicon version: limits and pattern
    assert ok(lexicon="x" * S["lexicon_max_chars"]) == []
    assert ok(lexicon="x" * (S["lexicon_max_chars"] + 1))
    assert ok(lexicon="")
    assert ok(lexicon="UPPER-case")
    assert ok(lexicon="-starts-wrong")
    # closed record: unknown and missing keys refuse
    r = {"markers": ["said"], "direction": "inbound",
         "lexicon": "0026-lex-999", "extra": 1}
    assert IM.agreement_shape_problems(r)
    assert IM.agreement_shape_problems({"markers": ["said"]})
    # and the spec carries the generated shape block byte-exactly
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    assert IM.render_shape_block() in spec


def test_census_manifests_refuse_ambiguous_records(tmp_path):
    """0026-EVIDENCE-R8-1: json.loads keeps the LAST duplicate member,
    so '"label":"fp","label":"tp"' passed as tp and could reduce the
    fp-union. Duplicate members refuse AT PARSE in both manifests and
    in the adjudication record."""
    import importlib
    MF = importlib.import_module("measure_false_positives")
    pop = {"a" * 64}
    dup_label = ('{"fire":"' + "a" * 64
                 + '","label":"fp","label":"tp"}\n')
    # drive through the real reader via a file
    p = tmp_path / "m.jsonl"
    p.write_text(dup_label)
    import hashlib as _hl
    lab, prob = MF._read_census_manifest(
        p, _hl.sha256(dup_label.encode()).hexdigest(), pop, "manifest")
    assert lab is None and "duplicate JSON member" in prob, prob
    dup_fire = ('{"fire":"' + "a" * 64 + '","fire":"' + "b" * 64
                + '","label":"tp"}\n')
    p.write_text(dup_fire)
    lab, prob = MF._read_census_manifest(
        p, _hl.sha256(dup_fire.encode()).hexdigest(), pop, "manifest")
    assert lab is None and "duplicate JSON member" in prob, prob
    # the adjudication record boundary refuses too
    assert "duplicate JSON member" in str(
        __import__("pytest").raises(ValueError, MF._strict_json,
                                    '{"a":1,"a":2}').value)


def test_bootstrap_paths_cannot_alias_and_worklists_stay_local(tmp_path):
    """0026-EVIDENCE-R8-3 + 0026-PRIVACY-R8-4: output paths are resolved
    and validated BEFORE any write — aliases among cache/aggregate/
    worklist refuse (including relative-vs-absolute aliases), a worklist
    inside the package tree refuses, and a written worklist is 0600."""
    import os
    import subprocess
    import sys as _sys
    FIX = ROOT / "specs" / "evidence" / "0026" / "e2e_fixture"
    script = ROOT / "specs" / "evidence" / "0026" / \
        "measure_false_positives.py"
    cache = FIX / "fixture_cache.jsonl"
    peer = FIX / "fixture_peer.json"

    def run(*args):
        return subprocess.run(
            [_sys.executable, str(script), "--cache", str(cache),
             "--peer-anchor", str(peer)] + list(args),
            capture_output=True, text=True, cwd=ROOT)

    # aggregate and worklist naming the SAME file refuse before writing
    x = tmp_path / "x.json"
    r = run("--emit-aggregate", str(x), "--worklist", str(x))
    assert r.returncode == 1 and "SAME" in r.stderr
    assert not x.exists(), "refusal must precede any write"
    # ...including via a relative alias of the same path
    rel = os.path.relpath(x, ROOT)
    r = run("--emit-aggregate", str(x), "--worklist", rel)
    assert r.returncode == 1 and "SAME" in r.stderr
    # an output naming the INPUT cache refuses (source preserved)
    before = cache.read_bytes()
    r = run("--emit-aggregate", str(cache))
    assert r.returncode == 1 and "SAME" in r.stderr
    assert cache.read_bytes() == before
    # ...and a HARDLINK to the cache — distinct path, same inode —
    # refuses too (research, round-8 pre-seal: path-string resolution
    # alone missed it)
    link = tmp_path / "cache_link.jsonl"
    os.link(cache, link)
    r = run("--emit-aggregate", str(link))
    assert r.returncode == 1 and "SAME" in r.stderr
    assert cache.read_bytes() == before
    # a worklist inside the package tree refuses — LOCAL-ONLY enforced
    r = run("--worklist", str(ROOT / "specs" / "wl.jsonl"))
    assert r.returncode == 1 and "INSIDE the package tree" in r.stderr
    assert not (ROOT / "specs" / "wl.jsonl").exists()
    # the good path: distinct external paths, worklist mode 0600, and
    # the bootstrap state still reached with BOTH artifacts retained
    aggp, wp = tmp_path / "agg.json", tmp_path / "wl.jsonl"
    # PRIVACY-R9-2: a PRE-EXISTING permissive worklist must end 0600 —
    # O_TRUNC applies the mode only on create, so chmod is explicit
    wp.write_text("stale")
    os.chmod(wp, 0o644)
    r = run("--emit-aggregate", str(aggp), "--worklist", str(wp))
    assert r.returncode == 3, (r.stdout[-300:], r.stderr[-300:])
    assert aggp.is_file() and wp.is_file()
    assert (wp.stat().st_mode & 0o777) == 0o600, (
        "a pre-existing 0644 worklist kept its mode (0026-PRIVACY-R9-2)")


def test_no_full_content_worklist_ships_in_the_package():
    """0026-PRIVACY-R8-4 + R9-2's package check: no structured-text
    file under specs/ carries the worklist line shape
    (fire+rel+note+obj) on ANY line, WHATEVER its suffix — the round-8
    check read only the first line of *.jsonl, so a renamed file or a
    later-line payload evaded the 'rename-proof' claim, and round 10
    found the 8MB size skip was a further undocumented evasion. Scope
    is TOTAL now: every file under specs/ at any size — text streamed
    line by line; undecodable files byte-scanned in bounded chunks for
    the four-key worklist basis."""
    import json as _json
    hits = []
    for f in (ROOT / "specs").rglob("*"):
        if not f.is_file():
            continue
        # NO size exclusion (0026-PRIVACY-R10-2: the 8MB skip was an
        # undocumented evasion) — text files stream line by line, and
        # a decode failure falls back to a CHUNKED byte scan with an
        # overlap window, so memory stays bounded at any size
        try:
            with f.open("r", errors="strict") as fh:
                for line in fh:
                    line = line.strip()
                    if not (line.startswith("{") and '"fire"' in line):
                        continue
                    try:
                        row = _json.loads(line)
                    except Exception:
                        continue
                    if (type(row) is dict
                            and {"fire", "rel", "note",
                                 "obj"} <= set(row)):
                        hits.append(str(f.relative_to(ROOT)))
                        break
        except OSError:
            continue
        except UnicodeDecodeError:
            KEYS = (b'"fire"', b'"rel"', b'"note"', b'"obj"')
            found = set()
            tail = b""
            with f.open("rb") as fh:
                while True:
                    chunk = fh.read(1 << 20)
                    if not chunk:
                        break
                    window = tail + chunk
                    for k in KEYS:
                        if k in window:
                            found.add(k)
                    tail = window[-16:]
                    if len(found) == len(KEYS):
                        break
            if len(found) == len(KEYS):
                hits.append(str(f.relative_to(ROOT)) + " (undecodable)")
    assert hits == [], (
        f"full-content worklist artifact(s) inside the package: {hits}")
def test_duplicate_key_cache_rows_count_unparseable(tmp_path):
    """0026-I10-1's exploitable form, made PROBATIVE at round 9
    (0026-EVIDENCE-R9-3: the first version passed on returncode != 0,
    which the peer mismatch it introduced already guaranteed — proving
    nothing about the count). The peer here MATCHES the modified cache
    exactly, so the run succeeds to its bootstrap state and the report
    must show the duplicate-key row COUNTED unparseable — never
    resolved last-wins."""
    import hashlib as _hl
    import json as _json
    import subprocess
    import sys as _sys
    FIX = ROOT / "specs" / "evidence" / "0026" / "e2e_fixture"
    script = (ROOT / "specs" / "evidence" / "0026"
              / "measure_false_positives.py")
    dup = tmp_path / "dup_cache.jsonl"
    raw = ((FIX / "fixture_cache.jsonl").read_text()
           + '{"value":"{}","value":"{}"}\n')
    dup.write_text(raw)
    peer = {"manifest": {
        "entries": len(raw.splitlines()),
        "sha256": _hl.sha256(raw.encode()).hexdigest(),
        "unparseable": 1}}
    pp = tmp_path / "peer.json"
    pp.write_text(_json.dumps(peer))
    r = subprocess.run(
        [_sys.executable, str(script), "--cache", str(dup),
         "--peer-anchor", str(pp)],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 3, (r.stdout[-300:], r.stderr[-300:])
    assert "1 unparseable" in r.stdout, (
        "the duplicate-key row was not COUNTED unparseable", r.stdout)


def test_no_plain_json_load_at_evidence_boundaries():
    """0026-I10-1 + I11-1, research's structural gate — PROVEN necessary
    by its own history: the duplicate-key class was closed in 0011
    round 9, recurred in fresh 0026 code eleven days later (R8-1), the
    closing fold missed THREE sites, and the gate's own first allowlist
    then carried three slots of HEADROOM in the very file it protected
    (a regex miscount: the impl line was skipped, the docstrings never
    matched). The gate is AST-BASED and EXACT-MATCH now: calls are
    resolved through import aliases (json.loads, j.loads, bare loads
    from `from json import loads`), a call is safe only if its
    object_pairs_hook is a KNOWN-STRICT callable by name (hook PRESENCE
    was the tenth face: object_pairs_hook=dict keeps the last duplicate
    and passed the gate while staying vulnerable — research demonstrated
    it), and every file's plain-call count must EQUAL its
    allowlisted count — headroom is impossible, and a stale allowlist
    trips on itself in either direction."""
    import ast

    def plain_calls(text):
        tree = ast.parse(text)
        mods, fns = set(), {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name == "json":
                        mods.add(a.asname or "json")
            elif isinstance(node, ast.ImportFrom) and node.module == "json":
                for a in node.names:
                    if a.name in ("load", "loads"):
                        fns[a.asname or a.name] = a.name
        n = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            hit = ((isinstance(f, ast.Attribute)
                    and isinstance(f.value, ast.Name)
                    and f.value.id in mods
                    and f.attr in ("load", "loads"))
                   or (isinstance(f, ast.Name) and f.id in fns))
            if not hit:
                continue
            # STRICT hooks only, by name: the duplicate-refusing
            # callables the evidence tree actually defines. A call with
            # any OTHER hook (object_pairs_hook=dict keeps last-wins)
            # counts as plain — presence is a proxy, strictness is the
            # guarantee (research's tenth-face demonstration).
            STRICT = ("_strict_pairs", "_no_dup_pairs")
            strict = any(kw.arg == "object_pairs_hook"
                         and isinstance(kw.value, ast.Name)
                         and kw.value.id in STRICT
                         for kw in node.keywords)
            if not strict:
                n += 1
        return n

    LEGACY = ("predates the strict-decoder rule; the artifact is "
              "sealed under its own line's review and hardening it is "
              "that line's amendment, not 0026's — NEW files get 0")
    allow = {
        # file -> (EXACT plain-call count, why). No headroom exists:
        # a count above OR below the pin trips (0026-I11-1).
        "0011/check_round1_fold.py": (1, LEGACY),
        "0011/subject_census.py": (4, LEGACY),
        "0019/phase1f_reference.py": (3, LEGACY),
        "0019/phase1g_u3b.py": (3, LEGACY),
        "0020/ledger_plan_harness.py": (3, LEGACY),  # AST found 2
                                                     # the regex missed
        "0020/store_adapter_harness.py": (2, LEGACY),
        "0020/vector_harness.py": (1, LEGACY),
        "0020/verify_package.py": (1, LEGACY),
        "0022/vector_harness.py": (1, LEGACY),
        "0024/baseline/run_baseline.py": (3, LEGACY),
        "0024/baseline/run_postfix.py": (3, LEGACY),
        "0024/baseline/validate_baseline.py": (2, LEGACY),
        "0025/corpus_counts.py": (3, LEGACY),
    }
    bad = []
    for f in sorted((ROOT / "specs" / "evidence").rglob("*.py")):
        rel = str(f.relative_to(ROOT / "specs" / "evidence"))
        plain = plain_calls(f.read_text())
        pinned = allow.get(rel, (0, ""))[0]
        if plain != pinned:
            bad.append(f"{rel}: {plain} plain json.load(s) call(s), "
                       f"pinned {pinned} — EXACT match required")
    assert bad == [], (
        "evidence-boundary json parsing drifted from the pinned "
        "allowlist — route through the strict duplicate-refusing "
        "decoder, or re-pin with a stated reason:\n  "
        + "\n  ".join(bad))


def test_lexicon_and_stored_direction_domains_are_bound():
    """0026-I12 (research's round-9 pre-seal, the R9-1 CLASS closure):
    the lexicon's reading domain and the stored direction enum were two
    independent definitions bridged by prose — mutant (a): add a
    lexicon reading value and nothing trips. Now the mapping is
    executable and TOTAL: LEXICON_TO_STORED's keys must equal
    LEXICON_DIRECTIONS exactly (a new reading value with no mapping row
    fails HERE instead of re-splitting the carriers), the shape's
    direction_values must equal the mapping's non-None image, and
    _direction's observed returns stay inside the declared domain."""
    import importlib
    IM = importlib.import_module("import_matrix")
    L = importlib.import_module("relay_lexicon")
    assert set(IM.LEXICON_TO_STORED) == set(L.LEXICON_DIRECTIONS), (
        "a lexicon reading value has no lexicon->stored mapping row — "
        "decide its stored form explicitly (0026-I12)")
    want = tuple(dict.fromkeys(
        v for v in IM.LEXICON_TO_STORED.values() if v is not None))
    assert IM.AGREEMENT_SHAPE["direction_values"] == want, (
        "the shape's direction enum is not the mapping's image")
    # observed returns of the real _direction stay inside the domain
    seen = set()
    for text in ("my doctor said to rest",
                 "i said it myself",
                 "she said to rest",
                 "recommended brand"):
        toks = L._tokens(text)
        for i, tok in enumerate(toks):
            if tok in L._VERBS:
                seen.add(L._direction(toks, i))
    assert seen and seen <= set(L.LEXICON_DIRECTIONS), seen


def test_generated_carrier_registry_is_complete():
    """0026-I12 ask 2, built as consolidation + registry discipline: a
    canonical registry of (generated-block marker -> binder) so an
    UNBOUND generated carrier is conspicuous by absence — R9-1's root
    was an unregistered multi-carrier fact. Every GENERATED marker in
    the spec must have a registry row, and every registry binder must
    run clean against the shipped spec. ('No fact unregistered' is a
    stated discipline, not a mechanical proof — the mechanical half is
    that no generated BLOCK escapes a binder.)"""
    import importlib
    import json as _json
    import re
    IM = importlib.import_module("import_matrix")
    MF = importlib.import_module("measure_false_positives")
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    agg = _json.loads((ROOT / "specs" / "evidence" / "0026"
                       / "fp_aggregate.json").read_text())
    REGISTRY = {
        # marker name -> callable returning problems against the spec
        "import-matrix": lambda: IM.spec_matrix_problems(spec),
        "agreement-shape": lambda: IM.spec_matrix_problems(spec),
        "fp-claim": lambda: MF.spec_problems(agg, spec),
        "review-closure": lambda: [],   # bound by render_closure --check
                                        # via the standing spec gate
    }
    markers = set(re.findall(r"<!-- GENERATED:([a-z-]+)", spec))
    unregistered = markers - set(REGISTRY)
    assert unregistered == set(), (
        f"generated carrier(s) with no registered binder: "
        f"{sorted(unregistered)} — an unbound generated block is the "
        f"R9-1 class (0026-I12)")
    for name, binder in REGISTRY.items():
        assert binder() == [], f"registered binder {name} is not clean"


def test_undecodable_worklist_bytes_still_flagged(tmp_path):
    """0026-I12 mutant (c): the every-line package sweep skips files
    that fail UTF-8 decode — so a full-content worklist with one stray
    invalid byte would evade it. The sweep's byte-level fallback flags
    undecodable files whose RAW bytes carry all four worklist keys;
    this test drives that basis directly."""
    probe = (b'{"fire":"' + b"a" * 64
             + b'","rel":"r","note":"\xff corpus","obj":"o"}\n')
    assert _worklist_bytes_suspect(probe)
    assert not _worklist_bytes_suspect(b"\xff plain binary, no keys")


def _worklist_bytes_suspect(raw: bytes) -> bool:
    """The byte-level detection basis shared by the package sweep."""
    return all(k in raw for k in (b'"fire"', b'"rel"',
                                  b'"note"', b'"obj"'))


def test_current_v_table_tests_resolve_and_no_live_restatement():
    """0026-I13 (research's round-10 pre-seal — the one thing that
    would stop an ACCEPT): the §6 check column presented six unwritten
    tests as standing (one drifted name, five implementation-time
    obligations unmarked). Two guards, both standing:

    (1) every test name cited in the spec's LIVE zone (outside
    generated blocks and the per-round Changes sections) must resolve
    to a real function under tests/ or specs/evidence/ — UNLESS its
    §6 row is explicitly marked IMPLEMENTATION-TIME, in which case it
    is an obligation, not a claim;

    (2) the restatement guard: the AGREEMENT_SHAPE bound digits may
    appear in marker/character context in the LIVE zone only inside
    generated blocks — five carriers in three rounds restated a bound
    (§18, the SENT row, a closure row, a test diagnostic, the V-table
    names)."""
    import importlib
    import re
    IM = importlib.import_module("import_matrix")
    spec = (ROOT / "specs" / "0026-label-value-agreement.md").read_text()
    # the LIVE zone: strip generated blocks and per-round history
    live = re.sub(r"<!-- GENERATED:.*?/GENERATED:[a-z-]+ -->", "",
                  spec, flags=re.S)
    live = re.split(r"^## 1[1-9]\. Changes in ", live, maxsplit=1,
                    flags=re.M)[0]
    # (1) cited test names resolve, or their row is marked
    corpus = ""
    for tf in list((ROOT / "tests").glob("*.py")) + list(
            (ROOT / "specs" / "evidence").rglob("*.py")):
        corpus += tf.read_text()
    for line in live.splitlines():
        for name in re.findall(r"`(test_[a-z0-9_]+)`", line):
            # NO exemption (0026-R11-1: the IMPLEMENTATION-TIME carve-
            # out let six named checks not exist; every cited name
            # resolves now — the implementation-time ones are
            # absence-aware and activate at graduation)
            assert f"def {name}(" in corpus, (
                f"the spec's live zone cites {name} but no such test "
                f"exists (0026-I13/R11-1)")
    # (2) bound digits out of live prose
    S = IM.AGREEMENT_SHAPE
    for n, ctx in ((S["markers_max_count"], "marker"),
                   (S["marker_max_chars"], "charact|chars"),):
        pat = (rf"\b{n}\b[^\n]{{0,40}}(?:{ctx})"
               rf"|(?:{ctx})[a-z ]{{0,40}}\b{n}\b")
        hits = [m.group(0) for m in re.finditer(pat, live, re.I)]
        assert hits == [], (
            f"live prose restates the shape bound {n}: {hits[:3]} — "
            f"numbers live only in generated blocks (0026-I13)")


# ---- §6 V2/V3/V5/V6/V6a/V7: absence-aware standing checks ------------------
# 0026-R11-1, the stated acceptance condition: each IMPLEMENTATION-TIME
# invariant's named test EXISTS NOW and activates automatically when the
# mechanism graduates into src/. In the draft state each proves its
# invariant holds VACUOUSLY — and proves the vacuity, never assumes it:
# the moment agreement machinery appears in src/, _prove_vacuity fails,
# which forces the behavioral cells below it to run instead.

def _agreement_implemented() -> bool:
    """The activation condition every absence-aware V-test keys on.
    A missing veracium package entirely (the reviewer's offline
    interpreter carries the evidence tree, not the product) is the
    not-implemented case a fortiori."""
    try:
        from veracium.schema import Edge
    except ModuleNotFoundError:
        return False
    return "agreement" in getattr(Edge, "model_fields", {})


def _prove_vacuity():
    """The draft-state proof: NO agreement/relay mechanism exists
    anywhere in src/veracium, so the invariant under test holds
    vacuously. This assertion flips when implementation begins."""
    import pathlib
    try:
        import veracium
    except ModuleNotFoundError:
        return      # no product package at all — vacuous a fortiori
                    # (the reviewer's offline interpreter)
    src = pathlib.Path(veracium.__file__).resolve().parent
    hits = sorted(f.name for f in src.rglob("*.py")
                  if any(tok in f.read_text()
                         for tok in ("AgreementRecord", "relay_lexicon",
                                     "relay_markers")))
    assert hits == [], (
        f"agreement machinery is appearing in src/ ({hits}) — the "
        f"absence-aware V-tests must run their behavioral cells now "
        f"(0026-R11-1)")
    assert not _agreement_implemented()


def _mem_for_v(tmp, payload_triples):
    import json as _json
    from veracium import EvidenceContext, Memory, MemoryConfig

    def llm(prompt, *, system=None, role="distill", json_schema=None):
        if role == "distill-retry":
            return _json.dumps({"triples": []})
        return _json.dumps({"triples": payload_triples, "episode": "ep"})

    mem = Memory(llm=llm, config=MemoryConfig(
        db_path=f"{tmp}/v.db", wiki_recompile_after_writes=0))
    return mem, EvidenceContext


def test_absence_is_no_evidence(tmp_path):
    """V2: marker ABSENCE never changes anything — empty/absent
    note+object mean no floor, no record, byte-identical edge."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    mem, EC = _mem_for_v(tmp_path, [
        {"subject": "user", "relation": "works_as", "object": "welder"}])
    mem.remember("u", "markerless", context=EC.direct())
    (e,) = mem.store.edges("u")
    assert e.agreement is None
    assert "agreement" not in e.model_dump(mode="json"), (
        "None must be OMITTED from serialization (the 0025 F6 pattern)")
    assert e.assertable
    mem.close()


def test_laundered_relay_floors_use_only(tmp_path):
    """V3: the B02/B07 class floors at USE_ONLY, and the floor NEVER
    raises — a quarantined edge stays quarantined."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    from veracium.schema import Disclosure
    mem, EC = _mem_for_v(tmp_path, [
        {"subject": "user", "relation": "health_state",
         "object": "needs rest", "note": "my doctor said to rest"}])
    mem.remember("u", "relay", context=EC.direct())
    (e,) = mem.store.edges("u", active_only=False)
    assert e.provenance.disclosure is Disclosure.USE_ONLY, (
        "a marked relay on a concrete relation floors at USE_ONLY (B07)")
    assert e.agreement is not None and e.agreement.direction == "inbound"
    mem.close()
    # research's graduation refinement (b): the SECOND clause — the
    # floor NEVER raises. A quarantined claim carrying a marker stays
    # QUARANTINED (restrict-only: the floor moves disclosure down or
    # nowhere, never up to USE_ONLY)
    from veracium.schema import QUARANTINE_RELATION
    memq, ECq = _mem_for_v(tmp_path / "q", [
        {"subject": "the vet", "relation": QUARANTINE_RELATION,
         "object": "the dog needs rest",
         "note": "my doctor said the dog needs rest"}])
    memq.remember("u", "quarantined relay", context=ECq.direct())
    (eq,) = memq.store.edges("u", active_only=False,
                             include_quarantined=True)
    assert eq.provenance.disclosure is Disclosure.QUARANTINED, (
        "the floor must never RAISE a quarantined claim to USE_ONLY — "
        "restrict-only means down or nowhere (V3 second clause)")
    memq.close()


def test_demotion_direction_records_only(tmp_path):
    """V5: a demotion-direction disagreement is RECORDED and counted
    with NO disposition change."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    from veracium.schema import QUARANTINE_RELATION
    mem, EC = _mem_for_v(tmp_path, [
        {"subject": "the vet", "relation": QUARANTINE_RELATION,
         "object": "user told the vet the dog is fine",
         "note": "as I told the vet"}])
    before = mem.store.edges("u", active_only=False,
                             include_quarantined=True)
    mem.remember("u", "demotion-direction", context=EC.direct())
    (e,) = mem.store.edges("u", active_only=False,
                           include_quarantined=True)
    assert e.quarantined, "the disposition must NOT change (record-only)"
    assert e.agreement is not None
    assert e.agreement.direction == "user_source"
    mem.close()


def test_agreement_carriers_complete(tmp_path):
    """V6: the record is structured (markers+direction+lexicon),
    None-omitted; both counters present on every remember path; the
    MCP surface strips them."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    import importlib
    IM = importlib.import_module("import_matrix")
    mem, EC = _mem_for_v(tmp_path, [
        {"subject": "user", "relation": "health_state",
         "object": "needs rest", "note": "my doctor said to rest"}])
    r = mem.remember("u", "x", context=EC.direct())
    assert "agreement_floored" in r and "agreement_recorded" in r, (
        "both counters present on EVERY path — an absent key is not 0")
    (e,) = mem.store.edges("u", active_only=False)
    rec = e.agreement.model_dump(mode="json")
    assert IM.agreement_shape_problems(rec) == [], (
        "the stored record must satisfy the executable shape")
    # research's graduation refinement (a): the MARKERLESS path carries
    # both counters too, at zero — an absent key is not a zero there
    # either (a partial implementation could pass the floored path
    # alone)
    mem2, EC2 = _mem_for_v(str(mem.config.db_path) + ".2", [
        {"subject": "user", "relation": "works_as", "object": "welder"}])
    r2 = mem2.remember("u", "markerless", context=EC2.direct())
    assert r2.get("agreement_floored") == 0
    assert r2.get("agreement_recorded") == 0
    mem2.close()
    mem.close()


def test_agreement_import_recomputes(tmp_path):
    """V6a: the import boundary is MODE-SPLIT per the ONE matrix —
    default recomputes (forged/malformed/foreign resolve to the
    recomputation, counted); restore is trust-field-faithful for VALID
    fields and RAISES on malformed with nothing written."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    import importlib
    IM = importlib.import_module("import_matrix")
    # every MATRIX row must be exercised at graduation; the rows are
    # the contract — drive default-recompute, restore-verbatim,
    # restore-malformed-raises, restore-foreign-verbatim
    raise AssertionError(
        "graduation reached: implement the V6a matrix drive over "
        f"{len(IM.MATRIX)} rows before accepting the implementation")


def test_no_markers_is_byte_identical(tmp_path):
    """V7: a marker-free store is byte-identical before and after —
    the whole mechanism is invisible where no marker ever fired."""
    if not _agreement_implemented():
        _prove_vacuity()
        return
    mem, EC = _mem_for_v(tmp_path, [
        {"subject": "user", "relation": "works_as", "object": "welder"}])
    mem.remember("u", "markerless", context=EC.direct())
    out1 = tmp_path / "a.jsonl"
    out2 = tmp_path / "b.jsonl"
    mem.export_memory("u", out1)
    mem.export_memory("u", out2)
    assert out1.read_bytes() == out2.read_bytes()
    assert b"agreement" not in out1.read_bytes(), (
        "a marker-free export must carry no agreement keys at all")
    mem.close()
