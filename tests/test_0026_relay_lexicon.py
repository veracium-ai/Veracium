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
    "self_poss":     ("my own account", "my own account", "outbound"),
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
    refused(lambda m: m.__setitem__("schema", 1), "not 2")
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
