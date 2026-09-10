"""specs/0039 §2c-ii: the answer matrix's "today" columns are a KEPT execution.

`specs/evidence/0039/answer_shapes.py` drives every named provider answer shape
through the real `ingest_event`; its committed transcript is the measured
"today" column of the matrix. This node asserts the script still prints that
transcript byte for byte — a change in shipped behaviour (or a new shape) moves
the transcript, and the spec's matrix is re-read against it. The negative
control plants a shape the transcript does not carry and asserts the
comparison fails, so the equality is doing work.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "specs" / "evidence" / "0039" / "answer_shapes.py"
TRANSCRIPT = ROOT / "specs" / "evidence" / "0039" / "answer_shapes_transcript.txt"


def _assert_the_interpreter_resolves_this_tree() -> None:
    """The instruments import whatever `veracium` the interpreter resolves
    (research, 2026-09-10: the subject is environment-resolved). A transcript
    describes THIS tree's product; a run against another — a stale offline
    venv's wheel, a released install — would describe a different product and
    must fail by name, not by a puzzling diff. Inside an extracted archive the
    reviewer runs with PYTHONPATH=src, which resolves the archive's own copy."""
    resolved = subprocess.run([sys.executable, "-c", "import veracium, pathlib; print(pathlib.Path(veracium.__file__).resolve())"],
                              capture_output=True, text=True, check=True).stdout.strip()
    expected = (ROOT / "src" / "veracium" / "__init__.py").resolve()
    assert pathlib.Path(resolved) == expected, (
        f"this interpreter resolves veracium from {resolved}, not this tree's {expected} — "
        "the transcript would describe a different product; run with PYTHONPATH=src or an "
        "editable install of this tree")


def _run() -> str:
    _assert_the_interpreter_resolves_this_tree()
    return subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=True).stdout


def _body(transcript: pathlib.Path) -> str:
    """The transcript minus its comment header (the header carries the pin)."""
    return "".join(l for l in transcript.read_text().splitlines(keepends=True) if not l.startswith("#")).lstrip("\n")


def _assert_transcript_pin_is_this_tree(transcript: pathlib.Path, root: pathlib.Path = ROOT) -> None:
    """The header's `against veracium @ <pin>` line is the one line that says
    which product the outcomes describe, so it is the one line that must be
    asserted rather than skipped (research, 2026-09-10): the pin must be an
    ancestor of HEAD and src/ must be unchanged since it — otherwise the
    transcript describes a different product and must be regenerated.

    THREE repository states, enumerated explicitly (research's second catch:
    two had been handled and the third — SHALLOW — turned git's exit 128 "I
    cannot see that object" into a false "regenerate the transcript"):
      no repository  → SKIP, named ("no repository here");
      shallow        → SKIP, named ("not enough history") — an environment fact,
                       never a transcript finding;
      full           → the check runs; 128 from git here means the pin is not an
                       object in this repository (a transcript from another
                       line), 1 means it exists but is not an ancestor (another
                       branch) — two different findings, both about the transcript."""
    import re
    import pytest
    m = re.search(r"against veracium @ ([0-9a-f]{7,40})", transcript.read_text())
    assert m, f"{transcript.name}: no pin line in the header"
    pin = m.group(1)
    if not (root / ".git").exists():
        pytest.skip("no repository here (a git archive or a bare tree): the transcript's pin cannot be checked against history")
    shallow = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-shallow-repository"], capture_output=True, text=True)
    if shallow.stdout.strip() == "true":
        pytest.skip("shallow repository: not enough history to check the transcript's pin (git exit 128 here is a fact about the checkout, not the transcript; CI's pytest jobs check out with fetch-depth 0)")
    present = subprocess.run(["git", "-C", str(root), "cat-file", "-e", f"{pin}^{{commit}}"], capture_output=True)
    assert present.returncode == 0, f"{transcript.name}: pin {pin[:7]} is not an object in this repository — a transcript from another line"
    anc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", pin, "HEAD"], capture_output=True, text=True)
    if anc.returncode == 128:
        raise RuntimeError(f"git could not answer for {pin[:7]} in a full repository: {anc.stderr.strip()}")
    assert anc.returncode == 0, f"{transcript.name}: pin {pin[:7]} exists but is not an ancestor of HEAD — a transcript from another branch"
    diff = subprocess.run(["git", "-C", str(root), "diff", "--stat", f"{pin}..HEAD", "--", "src/"], capture_output=True, text=True, check=True).stdout
    assert diff.strip() == "", f"{transcript.name}: src/ changed since its pin {pin[:7]} — regenerate the transcript and re-read the matrix:\n{diff}"


def test_the_answer_shape_transcript_is_the_scripts_output():
    assert SCRIPT.name == "answer_shapes.py"          # the artifact this matrix binds (PROCESS-R23-1)
    # round-3 R3-2: reproduction runs EVERYWHERE, an archive included; the
    # git-history binding is its own test below and skips only itself
    out = _run()
    assert out == _body(TRANSCRIPT), "the shipped outcomes moved: re-read specs/0039 §2c-ii against the new transcript"
    # the rows the spec's matrix leans on hardest, asserted by name so a
    # transcript regenerated by mistake cannot silently carry the old claim
    # `null` stopped raising with the WIDER normalization rule (specs/0025 §4b(1),
    # amended 2026-09-10): every non-list `triples` is one recorded `shape` and zero
    # facts. The row is still asserted by name -- and its OLD text is asserted absent,
    # so a transcript restored from before the amendment fails instead of reading true.
    assert "  null                             -> RESULT facts=0 unparseable=False" in out
    assert "RAISES TypeError" not in out
    assert "  number                           -> RESULT facts=0 unparseable=False" in out
    assert "  boolean                          -> RESULT facts=0 unparseable=False" in out
    assert "  string                           -> RESULT facts=0 unparseable=False" in out
    assert "  missing key                      -> RESULT facts=0 unparseable=False" in out
    assert "  bare array of dicts              -> RESULT facts=1" in out
    assert "  triples null                     -> RESULT facts=1 unparseable=False retried=1 recovered=0" in out
    assert "  primary call raises              -> RAISES RuntimeError" in out


def test_a_planted_shape_changes_the_transcript(tmp_path, monkeypatch):
    """RULE ZERO: the equality above must be able to fail."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("answer_shapes", SCRIPT)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.PRIMARY.append(("planted shape", '{"triples": "planted"}'))
    assert mod.transcript() != _body(TRANSCRIPT)
    assert "planted shape" in mod.transcript()


RESEARCH_SCRIPT = ROOT / "specs" / "evidence" / "0039" / "answer_shapes_research_instrument.py"
RESEARCH_TRANSCRIPT = ROOT / "specs" / "evidence" / "0039" / "answer_shapes_research_transcript.txt"


def test_researchs_independent_instrument_still_prints_its_transcript():
    """The second instrument (research's, written without reading dev's — the
    only reason agreement between them counts as evidence). Its committed
    transcript carries a header naming the pin it was generated against;
    the script's output is the body below that header, byte for byte."""
    assert RESEARCH_SCRIPT.name == "answer_shapes_research_instrument.py"
    _assert_the_interpreter_resolves_this_tree()
    out = subprocess.run([sys.executable, str(RESEARCH_SCRIPT)], capture_output=True, text=True, check=True).stdout
    body = _body(RESEARCH_TRANSCRIPT)
    assert out == body, "research's instrument no longer prints its transcript: the shipped outcomes moved"


def test_the_pin_binding_refuses_stale_foreign_and_unreachable_pins_and_names_the_two_skip_states(tmp_path):
    """RULE ZERO for the pin binding, over every state it enumerates: a stale pin
    (src/ changed since it) and a foreign pin (not an object here) are refused
    as TRANSCRIPT findings with distinct messages; a valid-but-unreachable pin
    (a commit on another branch, when one is present) is refused as a third
    distinct finding; a shallow clone and a tree with no repository are SKIPPED
    with their own named reasons, never reported as findings — planted headers
    and throwaway checkouts, so the binding is doing work rather than decoration."""
    import pytest
    if not (ROOT / ".git").exists():
        pytest.skip("no repository here (a git archive or a bare tree): the transcript's pin cannot be checked against history")
    if subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-shallow-repository"], capture_output=True, text=True).stdout.strip() == "true":
        pytest.skip("shallow repository: not enough history to check the transcript's pin (this control needs the full history to plant its cases)")
    def header(pin): return f"# generated against veracium @ {pin}\nbody\n"
    first = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--max-parents=0", "HEAD"], capture_output=True, text=True, check=True).stdout.split()[0]
    stale = tmp_path / "stale.txt"; stale.write_text(header(first))
    with pytest.raises(AssertionError, match="src/ changed since its pin"):
        _assert_transcript_pin_is_this_tree(stale)
    foreign = tmp_path / "foreign.txt"; foreign.write_text(header("0" * 40))
    with pytest.raises(AssertionError, match="not an object in this repository"):
        _assert_transcript_pin_is_this_tree(foreign)
    # a commit that exists here but is on another branch: any ref not merged into HEAD
    others = subprocess.run(["git", "-C", str(ROOT), "rev-list", "--all", "--not", "HEAD", "--max-count=1"], capture_output=True, text=True, check=True).stdout.split()
    if others:
        unreachable = tmp_path / "unreachable.txt"; unreachable.write_text(header(others[0]))
        with pytest.raises(AssertionError, match="not an ancestor of HEAD"):
            _assert_transcript_pin_is_this_tree(unreachable)
    # the two skip states, each on a throwaway checkout: shallow, and no repository
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{ROOT}", str(shallow)], check=True, capture_output=True)
    good = tmp_path / "good.txt"; good.write_text(header(head))
    with pytest.raises(pytest.skip.Exception, match="shallow repository"):
        _assert_transcript_pin_is_this_tree(good, root=shallow)
    bare = tmp_path / "bare"; bare.mkdir()
    with pytest.raises(pytest.skip.Exception, match="no repository here"):
        _assert_transcript_pin_is_this_tree(good, root=bare)


def test_devs_transcript_pin_describes_this_tree():
    """The history-dependent half, separated from reproduction (round-3 R3-2):
    skips only itself where there is no or not enough history."""
    _assert_transcript_pin_is_this_tree(TRANSCRIPT)


def test_researchs_transcript_pin_describes_this_tree():
    _assert_transcript_pin_is_this_tree(RESEARCH_TRANSCRIPT)
