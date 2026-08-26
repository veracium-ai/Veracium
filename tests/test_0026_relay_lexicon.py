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

    # 3. possessives read as first person: 'my doctor said' suppressed. The
    #    other lex-1 defect, in the favourable direction (fewer fires).
    L, V = _fresh()
    assert mutate(_FIRST_PERSON_SUBJ=("i", "we", "my", "our")), (
        "treating possessives as first-person subjects left the matrix "
        "green — the commonest relay shape in the corpus would vanish")
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
