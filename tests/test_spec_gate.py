"""The spec-reference gate is itself a postcondition check, so it needs one.

PROCESS.md §6 says an invariant with no executable check does not count. That
applies to the checker: a guard that silently passes everything looks identical
to a clean repository — which is exactly what an external reviewer demonstrated
by running the previous version. `Spec: banana`, a nonexistent spec file, a
rename out of a guarded path, a new trust module, and an unresolvable commit
range all passed with exit 0.

Every bypass they found has a named test below. Tests are written against the
FAILURE, not the feature, so a regression reads as "the banana case passes
again" rather than "test_17 broke".
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

CHECK = Path(__file__).resolve().parents[1] / "specs" / "check_spec_reference.py"

OK, POLICY_FAIL, CANNOT_RUN = 0, 1, 2


class Repo:
    """A scratch git repo. Commits take a real trailer block, because Git's
    trailer parser — unlike a regex — cares where the lines are."""

    def __init__(self, path: Path):
        self.path = path
        path.mkdir(parents=True, exist_ok=True)
        self._run("git", "init", "-q")
        self._run("git", "config", "user.email", "t@example.com")
        self._run("git", "config", "user.name", "t")
        for f in ("src/veracium/graph.py", "src/veracium/gate.py", "README.md"):
            p = path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("original\n")
        # a spec must now declare a machine-readable state; only `accepted`
        # authorises implementation
        self.write_spec("specs/0007-thing.md", "accepted")
        self._run("git", "add", "-A")
        self._run("git", "commit", "-qm", "seed")
        self.base = self._out("git", "rev-parse", "HEAD").strip()

    def write_spec(self, path, status, closure=True):
        p = self.path / path
        p.parent.mkdir(parents=True, exist_ok=True)
        tail = ("\n## Review closure\n\n| finding | evidence |\n|---|---|\n"
                "| item 1 | `pytest tests/test_thing.py` |\n" if closure else "")
        p.write_text(f"# Spec: thing\n\nSpec-Status: {status}\n\nbody\n{tail}")
        return p

    # A scratch repo must not inherit the developer's git configuration.
    # `commit.gpgsign = true` globally makes every `git commit` here wait on a
    # GPG agent that a sandbox or CI container does not have, and the wait has
    # no timeout -- the run hangs rather than fails. An external reviewer hit
    # exactly that on 0007 v3 and could not finish the suite. Templates, hooks
    # and aliases are the same class of problem. `GIT_CONFIG_GLOBAL` and
    # `GIT_CONFIG_SYSTEM` pointing at /dev/null make the fixture hermetic, and
    # every git call below inherits it.
    _ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull, "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0"}

    def _run(self, *a):
        return subprocess.run(a, cwd=self.path, check=True, capture_output=True,
                              text=True, env=self._ENV, timeout=60)

    def _out(self, *a):
        return subprocess.run(a, cwd=self.path, capture_output=True,
                              text=True, env=self._ENV, timeout=60).stdout

    def commit(self, subject, trailers=(), touch=(), delete=(), rename=None):
        for f in touch:
            p = self.path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("changed\n")
        for f in delete:
            self._run("git", "rm", "-q", f)
        if rename:
            self._run("git", "mv", rename[0], rename[1])
        self._run("git", "add", "-A")
        args = ["git", "commit", "-q", "-m", subject]
        if trailers:
            args += ["-m", "\n".join(trailers)]
        self._run(*args)
        return self

    def check(self, rng=None, *extra):
        # the checker shells out to git inside this scratch repo, so it needs
        # the same hermetic environment the fixture's own git calls use
        r = subprocess.run([sys.executable, str(CHECK), rng or f"{self.base}..HEAD",
                            *extra], cwd=self.path, capture_output=True, text=True,
                           env=self._ENV, timeout=120)
        return r.returncode, r.stdout + r.stderr


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path / "r")


# --- the bypasses the external reviewer demonstrated ------------------------

def test_arbitrary_trailer_value_is_rejected(repo):
    """`Spec: banana` passed the old regex."""
    code, out = repo.commit("change", ["Spec: banana"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "must be a path under `specs/`" in out


def test_bare_none_is_rejected(repo):
    """`Spec: none` carried no category and any invented reason passed."""
    code, out = repo.commit("change", ["Spec: none"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "no longer accepted" in out


def test_nonexistent_spec_file_is_rejected(repo):
    code, out = repo.commit("change", ["Spec: specs/does-not-exist.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "does not exist in this commit's tree" in out


def test_pointing_at_the_template_is_rejected(repo):
    """Found while reproducing: the gate could be satisfied by referencing the
    blank template."""
    code, out = repo.commit("change", ["Spec: specs/TEMPLATE.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "template/process itself" in out


def test_prose_line_is_not_a_trailer(repo):
    """The old regex matched any line starting with `Spec:` anywhere in the
    message, so a sentence in a discussion paragraph satisfied the gate."""
    r = repo.commit("Discussion of the process", touch=["src/veracium/graph.py"])
    r._run("git", "commit", "-q", "--amend", "-m",
           "Discussion\n\nSpec: not decided yet\n\nMore prose follows.\n")
    code, out = r.check()
    assert code == POLICY_FAIL
    assert "no `Spec:` or `Spec-Exception:` trailer" in out


def test_rename_out_of_a_guarded_path_is_caught(repo):
    """`git show --name-only` reports only a rename's destination, so moving
    graph.py to an unguarded name escaped the gate entirely."""
    code, out = repo.commit("move it", rename=("src/veracium/graph.py",
                                               "src/veracium/graph_new.py")).check()
    assert code == POLICY_FAIL
    assert "src/veracium/graph.py" in out


def test_deleting_a_guarded_file_is_caught(repo):
    code, _ = repo.commit("remove", delete=["src/veracium/gate.py"]).check()
    assert code == POLICY_FAIL


def test_unresolvable_range_fails_closed(repo):
    """The worst defect: a shallow clone or missing origin printed 'skipping'
    and exited 0 — a green build that checked nothing."""
    code, out = repo.check("origin/main..HEAD")
    assert code == CANNOT_RUN
    assert "nothing was checked" in out
    assert "Refusing to report success" in out


def test_missing_base_can_be_waived_explicitly_and_only_explicitly(repo):
    code, _ = repo.check("origin/main..HEAD", "--allow-missing-base")
    assert code == OK


def test_the_checker_cannot_silently_modify_itself(repo):
    """A commit could weaken the checker and have the weakened checker approve
    its own change."""
    code, out = repo.commit("tweak the gate",
                            touch=["specs/check_spec_reference.py"]).check()
    assert code == POLICY_FAIL
    assert "Process-Change" in out


@pytest.mark.parametrize("control", [
    "specs/check_spec_reference.py", "specs/PROCESS.md", "specs/TEMPLATE.md",
    ".github/workflows/test.yml",
])
def test_every_process_control_is_protected(repo, control):
    code, _ = repo.commit("touch a control", touch=[control]).check()
    assert code == POLICY_FAIL


def test_process_change_trailer_permits_it_and_says_it_needs_approval(repo):
    code, out = repo.commit("tweak the gate", ["Process-Change: widen GUARDED"],
                            touch=["specs/check_spec_reference.py"]).check()
    assert code == OK
    assert "requires independent approval" in out


# --- the accepting paths, which must still work ----------------------------

def test_a_real_spec_reference_passes(repo):
    code, out = repo.commit("implement it", ["Spec: specs/0007-thing.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == OK
    assert "0007-thing.md" in out


def test_multiple_spec_refs_all_validate(repo):
    """A commit may legitimately implement two accepted specs. The old code
    silently used the first match."""
    code, out = repo.commit(
        "two specs", ["Spec: specs/0007-thing.md", "Spec: specs/nope.md"],
        touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL, "the second, invalid reference must not be ignored"
    assert "nope.md" in out


def test_structured_exception_passes(repo):
    code, out = repo.commit(
        "fix a comment",
        ["Spec-Exception: docs-only",
         "Spec-Exception-Reason: corrected a stale comment about absorption"],
        touch=["src/veracium/graph.py"]).check()
    assert code == OK
    assert "EXCEPTION docs-only" in out


def test_unrecognised_exception_category_is_rejected(repo):
    code, out = repo.commit(
        "whatever", ["Spec-Exception: because-i-said-so",
                     "Spec-Exception-Reason: it seemed fine at the time"],
        touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "unrecognised" in out


def test_exception_without_a_reason_is_rejected(repo):
    code, out = repo.commit("skip it", ["Spec-Exception: docs-only"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "Spec-Exception-Reason" in out


def test_trivial_reason_is_rejected(repo):
    code, _ = repo.commit("skip it", ["Spec-Exception: docs-only",
                                      "Spec-Exception-Reason: fix"],
                          touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL


def test_security_hotfix_requires_a_retrospective_deadline(repo):
    """The carve-out is correct — holding the 0.4.1 advisory fix would have been
    wrong. The deadline is what keeps it a carve-out rather than a door."""
    code, out = repo.commit(
        "contain it",
        ["Spec-Exception: security-hotfix",
         "Spec-Exception-Reason: GHSA-r7j7-5jq9-3f5q cross-trust identity merges"],
        touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "Spec-Retrospective-Due" in out


def test_security_hotfix_with_a_deadline_passes(repo):
    code, _ = repo.commit(
        "contain it",
        ["Spec-Exception: security-hotfix",
         "Spec-Exception-Reason: GHSA-r7j7-5jq9-3f5q cross-trust identity merges",
         "Spec-Retrospective-Due: 2026-08-04"],
        touch=["src/veracium/graph.py"]).check()
    assert code == OK


def test_malformed_deadline_is_rejected(repo):
    code, _ = repo.commit(
        "contain it",
        ["Spec-Exception: security-hotfix",
         "Spec-Exception-Reason: GHSA-r7j7-5jq9-3f5q cross-trust identity merges",
         "Spec-Retrospective-Due: next week"],
        touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL


def test_both_a_spec_and_an_exception_is_rejected(repo):
    code, out = repo.commit(
        "hedging", ["Spec: specs/0007-thing.md", "Spec-Exception: docs-only",
                    "Spec-Exception-Reason: covering both bases just in case"],
        touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "pick one" in out


def test_unguarded_files_do_not_trip_the_gate(repo):
    """A noisy gate gets bypassed, so the exclusions must stay real.

    This used `compile.py` until M8 showed the wiki caches a trust decision and
    serves it after revocation — so it is guarded now, and the test moved to
    files that genuinely decide nothing about trust."""
    code, _ = repo.commit("docs", touch=["README.md",
                                         "src/veracium/selfcheck.py"]).check()
    assert code == OK


def test_every_guarded_surface_actually_trips_the_gate(tmp_path):
    for i, f in enumerate(("src/veracium/schema.py", "src/veracium/__init__.py",
                           "src/veracium/store/sqlite.py",
                           "src/veracium/proactive.py",
                           "src/veracium/introspect.py",
                           "src/veracium/portability.py")):
        r = Repo(tmp_path / f"guard{i}")
        code, _ = r.commit("change trust behaviour", touch=[f]).check()
        assert code == POLICY_FAIL, f"{f} is not guarded"


def test_a_merge_commit_does_not_fail_on_its_own(repo):
    """A merge introduces no changes of its own; its branch commits are in the
    same range and are checked individually."""
    repo._run("git", "checkout", "-q", "-b", "side")
    repo.commit("side change", ["Spec: specs/0007-thing.md"],
                touch=["src/veracium/graph.py"])
    repo._run("git", "checkout", "-q", "-")
    repo.commit("main change", touch=["README.md"])
    repo._run("git", "merge", "-q", "--no-ff", "side", "-m", "merge side")
    code, _ = repo.check()
    assert code == OK


def test_multiple_commits_in_one_range_are_all_checked(repo):
    repo.commit("good", ["Spec: specs/0007-thing.md"],
                touch=["src/veracium/graph.py"])
    repo.commit("bad", touch=["src/veracium/gate.py"])
    code, out = repo.check()
    assert code == POLICY_FAIL
    assert "gate.py" in out



# --- status gating: `Spec:` must name a spec that authorises implementation ---

@pytest.mark.parametrize("status", ["draft", "in review", "deferred", "rejected",
                                    "accepted-with-amendments"])
def test_a_non_accepted_spec_does_not_authorise_implementation(repo, status):
    """The gate could not previously tell an accepted spec from a blank draft:
    `Spec:` proved a file existed and nothing more. 0.4.5 shipped citing a spec
    whose status line read "draft"."""
    repo.write_spec("specs/0008-pending.md", status)
    code, out = repo.commit("implement it", ["Spec: specs/0008-pending.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "does not authorise implementation" in out


def test_accepted_with_amendments_is_explicitly_not_enough(repo):
    """PROCESS.md says so in prose; this makes it true."""
    repo.write_spec("specs/0009-amend.md", "accepted-with-amendments")
    code, out = repo.commit("implement", ["Spec: specs/0009-amend.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "amendments must be resolved" in out


def test_an_accepted_spec_authorises_implementation(repo):
    code, _ = repo.commit("implement it", ["Spec: specs/0007-thing.md"],
                          touch=["src/veracium/graph.py"]).check()
    assert code == OK


def test_a_spec_with_no_status_line_fails_closed(repo):
    """A spec that declares nothing must not be treated as permissive."""
    p = repo.path / "specs/0010-nostatus.md"
    p.write_text("# Spec\n\nbody with no status\n")
    code, out = repo.commit("implement", ["Spec: specs/0010-nostatus.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "no `Spec-Status:` line" in out


def test_an_unrecognised_status_is_rejected(repo):
    repo.write_spec("specs/0011-weird.md", "probably fine")
    code, out = repo.commit("implement", ["Spec: specs/0011-weird.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "not one of" in out


def test_docs_and_tests_on_a_draft_spec_still_pass_via_exception(repo):
    """The gate must not block writing the spec itself, or its tests."""
    repo.write_spec("specs/0012-draft.md", "draft")
    code, _ = repo.commit(
        "add tests while the spec is drafted",
        ["Spec-Exception: test-only",
         "Spec-Exception-Reason: coverage for a spec still in draft"],
        touch=["src/veracium/graph.py"]).check()
    assert code == OK


# --- the 0002 audit manifest must stay in sync with the code ----------------

def test_every_store_mutation_site_carries_a_verdict():
    """External review item 5: the spec claimed 28 enumerated sites were listed
    alongside the findings and presented an 11-row operation summary instead.

    The manifest is now generated from the mutator interface and this check
    fails when the code and the verdicts disagree — so the coverage claim is an
    artifact rather than an assertion. Two earlier enumerations (from memory,
    then from a grep keyed on assignment) were both incomplete, which is why
    prose is not an acceptable form for this."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "audit_manifest.py"), "--check"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, (
        f"the audit manifest and the code disagree:\n{r.stdout}\n{r.stderr}\n"
        f"Regenerate with `python3 specs/audit_manifest.py --write` and give "
        f"every new site a verdict in specs/audit_dispositions.py.")


def test_every_numbered_spec_file_is_actually_a_spec():
    """`specs/NNNN-*.md` is the citable namespace: the leading number IS the
    identity. A generated artifact was once named `0002-audit-manifest.md` and
    sat next to `0002-maintenance-provenance-invariant.md`, reading as a second
    spec 0002. It could never have been cited — the gate fails closed without a
    `Spec-Status:` line — but "unciteable" is not the same as "unconfusing".
    Generated artifacts live in `specs/generated/`."""
    import pathlib, re, collections
    specs = pathlib.Path(__file__).resolve().parent.parent / "specs"
    numbered = sorted(p for p in specs.glob("[0-9][0-9][0-9][0-9]-*.md"))
    assert numbered, "no numbered specs found — has the layout changed?"

    missing = [p.name for p in numbered if not re.search(r"^Spec-Status:", p.read_text(), re.M)]
    assert not missing, (
        f"{missing} sit in the numbered spec namespace without a `Spec-Status:` "
        f"line. Either it is a spec and needs one, or it is not and belongs in "
        f"specs/generated/.")

    by_number = collections.defaultdict(list)
    for p in numbered:
        by_number[p.name[:4]].append(p.name)
    dupes = {n: v for n, v in by_number.items() if len(v) > 1}
    assert not dupes, f"spec numbers must be unique: {dupes}"



def test_an_accepted_spec_must_carry_a_review_closure(repo):
    """PROCESS.md §4a: dev sets `accepted` once external-review comments are
    satisfied. Dev's judgement of "satisfied" was wrong three times this week —
    v3 asserted stale rules were replaced when they were annotated, the manifest
    certified 17 sites clean while 11 cited tests that do not exist, and §6a
    called a hand-authored column mechanically derived. The closure record turns
    "I fixed it" into something openable."""
    repo.write_spec("specs/0013-nocls.md", "accepted", closure=False)
    code, out = repo.commit("implement", ["Spec: specs/0013-nocls.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "Review closure" in out


def test_an_accepted_spec_with_a_closure_passes(repo):
    repo.write_spec("specs/0014-cls.md", "accepted")
    code, _ = repo.commit("implement", ["Spec: specs/0014-cls.md"],
                          touch=["src/veracium/graph.py"]).check()
    assert code == OK


def test_no_withdrawn_rule_is_stated_as_live_spec_text():
    """Four external reviews (WITHDRAWN wording) in a row found withdrawn rules still normative,
    each time after the document claimed they were removed. Every pass searched
    for my own annotations rather than for the rule, and a search for one's own
    corrections cannot find text one never annotated.

    History may quote a withdrawn phrase; the block must be marked WITHDRAWN or
    OBSOLETE, which is explicit and cannot be applied by accident."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "lint_withdrawn.py")],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_status_prose_is_generated_from_the_structured_records():
    """Five external reviews were deferred for a status claim contradicting
    another status claim in the same document — most recently a header saying
    "M1–M5, all closed" (WITHDRAWN wording) beside a ledger showing five unimplemented. Every fix
    was a better hand-check; the phrase lint passed straight through that one.

    Summaries are now derived from specs/findings.py."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "render_status.py"), "--check"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_authority_tables_are_generated_from_the_ladder():
    """specs/0003 v1 stated the ladder as arithmetic and wrote its consequences
    out in prose, inverting two of four ASSISTANT cases — including
    `assistant -> third_party`, the unsafe direction. The document it was
    transcribed from had all four right."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "render_ladder.py"), "--check"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_generated_authority_heading_is_authority_sorted():
    """Round-6 contract B: render_ladder generated the ladder heading in
    `EvidenceAuthor` DECLARATION order — `USER 3 > THIRD_PARTY 0 > SYSTEM 2`, a false
    inequality — while `--check` stayed green because the generator never sorted by
    authority. The heading must be strictly descending; the matrix rows below it were
    always right, so a green generator check was not enough."""
    import re, sys, pathlib, importlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import render_ladder
    importlib.reload(render_ladder)
    heading = re.search(r"`((?:[A-Z_]+ \d+ > )+[A-Z_]+ \d+)`",
                        render_ladder._regions()["matrix"])
    assert heading, "no authority heading in the generated matrix region"
    nums = [int(n) for n in re.findall(r"\d+", heading.group(1))]
    assert nums == sorted(nums, reverse=True) and len(set(nums)) == len(nums), \
        f"authority heading is not strictly descending: {heading.group(1)}"


def test_the_withdrawn_lint_is_punctuation_insensitive():
    """Round-6 contract A: §4a stated the WITHDRAWN `one guard in one loop` as
    `One guard, in one loop`, and the lint's normaliser folded emphasis but not the
    comma, so the exact spec it protects sailed through green. Clause punctuation must
    fold to a space. (This block quotes the WITHDRAWN phrase as test data, so it is
    marked WITHDRAWN to exempt itself from the very lint it exercises.)"""
    import re, sys, pathlib, importlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import lint_withdrawn
    importlib.reload(lint_withdrawn)
    normed = lint_withdrawn._normalise("One guard, in one loop")
    assert re.search(r"one guard in one loop", normed, re.I), \
        f"clause punctuation not folded: {normed!r}"
    # hyphens/periods are intra-token and must be LEFT intact, or `0.4.5` and
    # `same-author-class` would manufacture spurious matches (0002 regressed on this)
    assert lint_withdrawn._normalise("0.4.5") == "0.4.5"
    assert lint_withdrawn._normalise("same-author-class") == "same-author-class"


def test_watch_rows_are_not_counted_as_open_questions():
    """Round-6 contract D: 0003 Q2a is a `watch` — a recorded trigger for a future
    condition, which the spec calls 'not an open question' — yet the status generator
    counted it as the sole open Q. A `watch` row is not open."""
    import sys, pathlib, importlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import render_index
    importlib.reload(render_index)
    body = ("## 10. Open questions\n\n"
            "| # | question | class | who | by when |\n"
            "|---|---|---|---|---|\n"
            "| **Q9** | a genuinely open question | design | dev | soon |\n"
            "| **Q2a** | a recorded trigger | `watch` | dev | on some condition |\n")
    open_q, blocking = render_index._questions(body)
    assert open_q == 1, f"a watch row was counted as open: open_q={open_q}"


def test_the_rule_gives_the_right_assistant_answers_when_assistant_exists():
    """The four cases v1 inverted, asserted against the RULE rather than the
    shipped enum — `ASSISTANT` arrives with specs/0001, which is deferred.

    Written against `_RUNGS` because the property must hold the day the enum
    gains the member, not only afterwards."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from ladder import _RUNGS
    ok = lambda prior, inc: _RUNGS[inc] >= _RUNGS[prior]
    assert ok("assistant", "user"), "a user may retire assistant content"
    assert not ok("user", "assistant"), "assistant must not retire user"
    assert ok("third_party", "assistant")
    assert not ok("assistant", "third_party"), \
        "assistant content must not retire a third-party record"


def test_capping_changes_the_answer_on_a_real_subset():
    """The rule is min(author, derived_from); a matrix over authors alone cannot
    see the rows an attacker reaches by omitting derived_from."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from ladder import CLASSES, divergent, effective_matrix
    from veracium.schema import EvidenceAuthor
    # The product follows the SHIPPED enum. v5 hard-coded 400, which described
    # four classes including one that does not exist — so the generated tables
    # modelled a rule the runtime cannot execute.
    assert set(CLASSES) == {e.value for e in EvidenceAuthor}
    n = len(CLASSES) * (len(CLASSES) + 1)          # (author, derived_from|None)
    assert len(effective_matrix()) == n * n
    assert divergent(), "capping must change the answer somewhere"


def test_rulings_and_spec_question_tables_agree():
    """A ruling lands in COORDINATION, the spec's question table is updated
    separately, and the two drift: 0001 Q5 read "blocking / research" for 16
    hours after it was answered, 0006 Q1 for 12. Anyone auditing what is blocked
    reads the stale copy, and for a spec in external review that reader is the
    reviewer.

    Skips when COORDINATION.md is absent — it is local-only coordination state,
    not repo content, so a clone must not fail on it."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    if not (pathlib.Path.home() / "Documents" / "veracium" / "COORDINATION.md").exists():
        import pytest
        pytest.skip("COORDINATION.md not present (local-only coordination state)")
    r = subprocess.run([sys.executable, str(root / "specs" / "lint_rulings.py")],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_spec_status_index_is_current():
    """specs/STATUS.md is the at-a-glance view for Quentin and the coordination
    session. It is generated: every column comes from the spec files, git,
    findings.py or reviews.py. A hand-maintained status table is what got 0002
    deferred seven times."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    # The index derives `updated` from `git log`, so it cannot be reproduced
    # outside a checkout — an extracted review archive has no .git. Skip there
    # rather than fail, and say why.
    if subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True,
                      cwd=root).returncode != 0:
        import pytest
        pytest.skip("not a git checkout; STATUS.md derives `updated` from git log")
    r = subprocess.run([sys.executable, str(root / "specs" / "render_index.py"), "--check"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_review_archives_are_named_and_indexed():
    """specs/archives/ holds the exact package sent for each external review
    round. Names must match `NNNN-v<version>-<YYYYMMDDTHHMMZ>.tar.gz`, and
    INDEX.md — which is committed while the tarballs are not — must carry a
    current sha256 for each."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    if not list((root / "specs" / "archives").glob("*.tar.gz")):
        import pytest
        pytest.skip("no archives present (they are gitignored; a clone has none)")
    r = subprocess.run([sys.executable, str(root / "specs" / "render_archives.py"), "--check"],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_spec_cites_an_invariant_it_does_not_define():
    """Four review rounds of 0003 found prose referring to invariants the table
    no longer contained — I9 after it was replaced, I5 with its old meaning,
    I11/I12/I13 after they moved to 0011. A contributor implementing from that
    prose builds a different feature from the one named in the table."""
    import re, pathlib
    specs = pathlib.Path(__file__).resolve().parent.parent / "specs"
    problems = []
    for f in sorted(specs.glob("[0-9][0-9][0-9][0-9]-*.md")):
        # Stop at a review disposition, the same boundary `lint_withdrawn` and
        # `render_index` use. A disposition is history: it legitimately names
        # invariants that existed when that round ran. 0007 v10 cut the
        # migration scope and retired 16 ids that its round 1-7 dispositions
        # still cite -- correctly, because those rounds did address them.
        raw = f.read_text()
        # EXTERNAL ROUND 5: the generated per-finding closure ledger (R5-3)
        # names FINDINGS — F1, R3-3, R4-2 — in the same `| **X** |` shape as an
        # invariant row. They are not invariants and are not defined in the
        # invariant table, so this gate read them as dangling citations. Strip
        # the generated block for the same reason review dispositions are
        # stripped: it legitimately names ids from another vocabulary.
        raw = re.sub(r"<!-- GENERATED:review-closure -->.*?"
                     r"<!-- /GENERATED:review-closure -->", "", raw, flags=re.S)
        body = re.split(
            r"^##+ \d+\w*\.\s*(?:Review history\b|[^\n]*review[^\n]*disposition\b)",
            raw, flags=re.M | re.I)[0]
        # struck rows still DEFINE an id — `~~**Q5**~~` is a resolved question,
        # not an undefined one.
        defined = set(re.findall(r"^\| ~{0,2}\*\*([A-Z]\d+[a-z]?)\*\*", body, re.M))
        if not defined:
            continue          # spec has no table yet
        # Compare within each prefix letter separately. The first version picked
        # one prefix with `next(iter(defined))`, whose order depends on hash
        # randomisation — so it passed or failed run to run.
        by_prefix = {}
        for d in defined:
            by_prefix.setdefault(d[0], set()).add(d)
        for prefix, ids in sorted(by_prefix.items()):
            cited = {c for c in re.findall(r"\b([A-Z]\d+[a-z]?)\b", body)
                     if c[0] == prefix}
            missing = cited - ids
            if missing:
                problems.append(f"{f.name}: cites {sorted(missing)}, "
                                f"defines {sorted(ids)}")
    assert not problems, "\n".join(problems)


def test_no_spec_has_a_duplicated_section_heading():
    """The v5 package shipped 0003 with two §2, two §2c, two §2c-ii, two §3 and
    two §1b — the second copies stale and contradicting the first.

    Every check passed on that file. lint_withdrawn scans for withdrawn phrases,
    and both copies contained the same ones. render_ladder writes into every
    matching region, so it kept BOTH generated tables in sync and --check was
    green. A structural duplicate is invisible to a phrase lint by construction.
    """
    import re, pathlib, collections
    specs = pathlib.Path(__file__).resolve().parent.parent / "specs"
    problems = []
    for f in sorted(specs.glob("[0-9][0-9][0-9][0-9]-*.md")):
        # capture the whole number token: `### 3.1` and `### 3.2` are
        # distinct, and truncating at the first dot made them collide.
        heads = re.findall(r"^(##+ [0-9][0-9a-z.\-]*)", f.read_text(), re.M)
        dupes = [h for h, n in collections.Counter(heads).items() if n > 1]
        if dupes:
            problems.append(f"{f.name}: duplicated {sorted(dupes)}")
    assert not problems, "\n".join(problems)


def test_a_spec_cannot_be_accepted_while_its_prerequisite_is_unresolved(repo):
    """0008 adds a `confirmations` table. An older build opens the newer store,
    ignores the table, and clears the flag unaudited through the old path — so
    accepting 0008 without 0007 authorises an unsafe partial cut.

    Four specs now declare `Spec-Requires: 0007`, and 0007 has never been
    reviewed."""
    p = repo.path / "specs/0020-dep.md"
    p.write_text("# Spec\n\nSpec-Status: draft\n\nbody\n")
    q = repo.path / "specs/0021-needs.md"
    q.write_text("# Spec\n\nSpec-Status: accepted\nSpec-Requires: 0020\n\nbody\n"
                 "\n## Review closure\n\n| f | evidence |\n|---|---|\n| 1 | `x` |\n")
    code, out = repo.commit("implement", ["Spec: specs/0021-needs.md"],
                            touch=["src/veracium/graph.py"]).check()
    assert code == POLICY_FAIL
    assert "requires `0020`" in out


def test_a_spec_claiming_a_test_is_measured_today_must_have_it():
    """A row that says "measured today" must cite a test that exists.

    0007's invariant table mixes checks that run now with a contract for checks
    still to be written. That is fine -- but an earlier manifest in this project
    listed 17 rows of which 11 cited tests that did not exist, and after the
    round-5 module split several 0007 rows still cited pre-split names. A claim
    of present-tense evidence is exactly the claim worth gating."""
    import re
    root = Path(__file__).resolve().parent.parent
    have = set()
    for f in (root / "tests").rglob("test_*.py"):
        have |= set(re.findall(r"def (test_\w+)", f.read_text()))
    bad = []
    for spec in (root / "specs").glob("[0-9][0-9][0-9][0-9]-*.md"):
        for line in spec.read_text().splitlines():
            if "measured today" not in line.lower():
                continue
            for name in re.findall(r"`(test_\w+)`", line):
                if name not in have:
                    bad.append(f"{spec.name}: claims `{name}` is measured today, "
                               f"but no such test exists")
    assert not bad, "\n".join(bad)


def test_the_sdist_excludes_every_locally_excluded_file():
    """A file kept out of the REPO must also be kept out of the RELEASE.

    hatchling builds the sdist from the working tree and honours
    `.gitignore`, but NOT `.git/info/exclude`. So a file that is
    deliberately untracked via the local exclude list is invisible to
    `git status`, absent from GitHub, and STILL SHIPPED to PyPI — where a
    version cannot be withdrawn and re-cut.

    Caught during the 0.16.0 release: `CLAUDE.md` (internal multi-session
    workflow, explicitly local-only) was in a built, twine-checked sdist,
    one command short of being published.

    The two lists are therefore bound: anything `.git/info/exclude` keeps
    out of the repo must appear in the sdist's exclude list.
    """
    import re
    root = Path(__file__).resolve().parent.parent
    exclude_file = root / ".git" / "info" / "exclude"
    if not exclude_file.exists():          # a plain export, not a checkout
        pytest.skip("no .git/info/exclude — not a git checkout")
    local = [l.strip() for l in exclude_file.read_text().splitlines()
             if l.strip() and not l.strip().startswith("#")]
    if not local:
        return
    pyproject = (root / "pyproject.toml").read_text()
    m = re.search(r"\[tool\.hatch\.build\.targets\.sdist\](.*?)(?=\n\[|\Z)",
                  pyproject, re.S)
    assert m, ("pyproject declares no [tool.hatch.build.targets.sdist] "
               "section, so nothing constrains what the release tarball "
               "carries — and `.git/info/exclude` lists " + str(local))
    declared = set(re.findall(r'"([^"]+)"', m.group(1)))
    missing = [pat for pat in local if pat not in declared]
    assert not missing, (
        f"these are excluded from the REPO but not from the SDIST, so they "
        f"would be published to PyPI: {missing}. Add them to "
        f"[tool.hatch.build.targets.sdist] exclude in pyproject.toml.")


def test_no_spec_names_a_module_or_script_that_does_not_exist():
    """A spec that cites `specs/<name>.py` must cite one that is there.

    Round 6: after the module split, normative text in 0007 still pointed at
    `specs/schema_manifest.py` -- a file the same document said was gone -- in
    three places, including an invariant's executable check. The "measured
    today" gate catches a stale *test* name and could not catch a stale
    *module* name. Same class of drift, so the same kind of gate."""
    import re
    root = Path(__file__).resolve().parent.parent
    bad = []
    for spec in (root / "specs").glob("[0-9][0-9][0-9][0-9]-*.md"):
        body = spec.read_text()
        # historical dispositions legitimately name retired modules
        body = re.split(r"^##+ \d+\w*\.\s*(?:Review history\b|[^\n]*review[^\n]*disposition\b)",
                        body, flags=re.M | re.I)[0]
        for ref in set(re.findall(r"`(specs/[\w./-]+\.py)`", body)):
            if not (root / ref).exists():
                bad.append(f"{spec.name}: names `{ref}`, which does not exist")
        # Round 8, finding 4: the gate matched only `specs/<name>.py` and missed
        # a bare `schema_migrations.py` in the normative instrument row, so the
        # scope cut left a live reference to a deleted module.
        # A bare module name may live anywhere in the tree -- `base.py` is
        # `src/veracium/store/base.py`. Match on basename, not on a guessed
        # directory, or the gate invents violations.
        for ref in set(re.findall(r"`(\w+\.py)`", body)):
            if not any(p.name == ref for p in root.rglob("*.py")
                       if ".git" not in p.parts):
                bad.append(f"{spec.name}: names `{ref}`, which does not exist "
                           f"anywhere in the tree")
    assert not bad, "\n".join(bad)


# R11-4/R12-4 (0014 rounds 11-12): the guide's hardcoded counts drifted three
# releases behind the suite; the FIRST gate written against that regression was
# itself vacuous — its regex matched neither the original stale form nor the
# natural comma form (class E: a check proving the adjacent property). So the
# pattern is now proven against the motivating forms, the same mechanism as
# tests/test_withdrawn_gate_bites.py.
_FROZEN_COUNT_PATTERNS = [
    # "975 passed / 5 skipped / 4 xfailed" and "1121 passed, 13 skipped, 2 xfailed"
    r"\d+\s*passed\s*[,/]\s*\d+\s*skipped",
    # bare triples: "975/5/4" (with or without an xfail suffix)
    r"\b\d{2,4}/\d{1,3}/\d{1,3}",
    # frozen deltas: "+3 skips", "+3 git-only skips" — the count is mutable too
    r"\+\d+\s*(?:git[- ]only\s*)?skips",
]

# The verbatim forms this gate exists to catch — each must be caught by a pattern,
# or the gate is dead coverage (the R12-4 failure mode, mechanically prevented).
_FROZEN_COUNT_MOTIVATING_FORMS = [
    "975 passed / 5 skipped / 4 xfailed",
    "1121 passed, 13 skipped, 2 xfailed",
    "expect 975/5/4xfail",
    "the reconciliation RULE (+3 git-only skips in an extracted tree)",
]


def test_frozen_count_patterns_catch_their_motivating_forms():
    """The gate proves itself against the original stale form and representative
    variants — a pattern set that misses its own motivating text fails loudly."""
    import re

    missed = [f for f in _FROZEN_COUNT_MOTIVATING_FORMS
              if not any(re.search(p, f) for p in _FROZEN_COUNT_PATTERNS)]
    assert not missed, f"vacuous gate — forms not caught: {missed}"


def test_reviewer_guide_carries_no_frozen_suite_counts():
    """Counts and deltas live in COLLECTED.txt where they are measured (both the
    checkout and extracted-shape lines, plus the environment-conditional skip
    inventory); the guide must carry the rule, never a number."""
    import pathlib
    import re

    guide = (pathlib.Path(__file__).resolve().parent.parent
             / "specs" / "REVIEWER_GUIDE.md").read_text()
    hits = [m.group(0) for p in _FROZEN_COUNT_PATTERNS
            for m in re.finditer(p, guide)]
    assert not hits, (
        "REVIEWER_GUIDE.md carries frozen suite counts/deltas (they belong in "
        f"COLLECTED.txt): {hits}")


def test_conditional_skip_inventory_is_complete():
    """R13-3 (0014 round 13): the hand-listed COLLECTED inventory missed the
    optional-MCP importorskip, so the reviewer's delta could not fully reconcile
    against names. Both directions are now mechanical: every conditional-skip
    site in tests/ must match an inventory entry (file + condition token within
    the site's five-line window), and every entry must match a live site."""
    import pathlib
    import re
    import sys

    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from skip_inventory import INVENTORY

    # EXTERNAL ROUND 3, R3-5 — THE ROOT CAUSE OF THE MISSING FOUR. This regex
    # matched `pytest.mark.skipif` and NOT `pytest.mark.skip(`, so four
    # UNCONDITIONAL skips in test_0021_maintain_scope.py were structurally
    # invisible to a gate named "..._is_complete". It reported completeness
    # over a domain it could not see, COLLECTED decomposed a measured line it
    # could not account for, and verify_collected passed because it compares
    # the block to the same incomplete generator.
    # The bug is the checker's DEFINITION of the thing it checks — the third
    # instance of that shape in one review round (0023's N15 swept for the old
    # condition; the withdrawn-phrase pattern matched one phrasing).
    TQ = chr(34) * 3
    SQ = chr(39) * 3
    site_re = re.compile(
        r"pytest\.importorskip\(|pytest\.skip\(|pytest\.mark\.skipif"
        r"|pytest\.mark\.skip\(")
    sites = []  # (relpath, line_no, five-line window text)
    for f in sorted((root / "tests").rglob("*.py")):
        lines = f.read_text().splitlines()
        rel = str(f.relative_to(root))
        in_doc = False
        for i, line in enumerate(lines):
            # A triple-quoted block is PROSE. `pytest.skip(...)` inside one
            # documents the vocabulary; it is not a use of it. This gate fired
            # on its own new test's docstring (external round 5) — a checker
            # counting a MENTION as a SITE, which is the same shape as every
            # finding this round.
            ticks = line.count(TQ) + line.count(SQ)
            was_in_doc = in_doc
            if ticks % 2 == 1:
                in_doc = not in_doc
            if was_in_doc:
                continue
            if line.lstrip().startswith("#"):
                continue
            # A MENTION IS NOT A SITE (external round 5, found by this gate
            # firing on its own new test's docstring). `pytest.skip(...)` inside
            # a docstring explaining the skip vocabulary is prose; only a call
            # in code is a site. Detected by the quote that opens the line's
            # enclosing string — cheap and sufficient here, since every real
            # site is a bare statement or a decorator.
            stripped = line.lstrip()
            if stripped.startswith(('"', "'", "*", ">")):
                continue
            if in_doc:
                continue
            if site_re.search(line):
                window = "\n".join(lines[i:i + 5])
                sites.append((rel, i + 1, window))

    uninventoried = []
    for rel, ln, window in sites:
        if not any(f == rel and token in window
                   for f, _, token, _, _ in INVENTORY):
            uninventoried.append(f"{rel}:{ln}")
    assert not uninventoried, (
        "conditional-skip sites missing from specs/skip_inventory.py "
        f"(the R13-3 gap, mechanically): {uninventoried}")

    dead = []
    for f, kind, token, _, _ in INVENTORY:
        if not any(rel == f and token in window for rel, _, window in sites):
            dead.append(f"{f} [{kind}: {token!r}]")
    assert not dead, (
        f"inventory entries matching no live skip site (stale — remove): {dead}")


def test_collected_inventory_matches_the_generator():
    """R14-1/R15-1 (0014 rounds 14-15): binds the reviewer-facing carrier. In an
    extracted review package (COLLECTED.txt at the tree root) the marked
    inventory section must satisfy skip_inventory.verify_collected — the STRICT
    verifier (standalone-line markers, exactly one pair, byte-exact block, no
    normalization) shared with the packaging step. The first verifier split on
    the first marker pair and stripped boundary newlines; the reviewer
    reproduced a duplicated block and a padded boundary passing — hence the
    shared callable and the adversarial test below."""
    import pathlib
    import sys

    root = pathlib.Path(__file__).resolve().parent.parent
    collected = root / "COLLECTED.txt"
    if not collected.exists():
        import pytest
        pytest.skip("COLLECTED.txt not present (exists only in a sealed review package)")

    sys.path.insert(0, str(root / "specs"))
    from skip_inventory import verify_collected

    # R4-4: the block is now COMPUTED from the sealed -rs output, so the
    # verifier must be handed the same input the block was built with. The
    # sealed run ships beside COLLECTED for exactly this reason; without it
    # we would be comparing two different renderings and calling the
    # difference a defect.
    rs = root / "COLLECTED_pytest_rs.txt"
    verify_collected(collected.read_text(), rs.read_text() if rs.exists() else "")

    # and the sealed run must RECONCILE against the inventory, not merely
    # match the generator — the check whose absence was R3-5
    if rs.exists():
        from skip_inventory import reconcile
        problems = reconcile(rs.read_text())
        assert not problems, problems


def test_collected_verifier_rejects_the_adversarial_cases():
    """R15-1: the verifier is proven against the reviewer's reproduced bypasses
    and the required case list — valid, missing marker, stale content,
    duplicated complete block, extra boundary newline, edited content, and a
    mid-line (non-standalone) marker. Runs everywhere (pure function, no
    COLLECTED.txt needed), so the carrier gate itself can never regress to a
    happy-path check unnoticed."""
    import pathlib
    import sys

    import pytest

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from skip_inventory import BEGIN_MARKER, END_MARKER, render, verify_collected

    body = render()
    valid = f"head\n{BEGIN_MARKER}\n{body}\n{END_MARKER}\ntail"
    verify_collected(valid)  # must not raise

    bad = {
        "missing end marker": f"head\n{BEGIN_MARKER}\n{body}\ntail",
        "stale content": f"head\n{BEGIN_MARKER}\nwrong\n{END_MARKER}\ntail",
        "duplicated complete block":
            valid + f"\n{BEGIN_MARKER}\n{body}\n{END_MARKER}",
        "extra boundary newline":
            f"head\n{BEGIN_MARKER}\n\n{body}\n{END_MARKER}\ntail",
        "edited content":
            f"head\n{BEGIN_MARKER}\n{body.replace('mcp', 'mpc', 1)}\n{END_MARKER}\ntail",
        "mid-line marker": f"head\nx {BEGIN_MARKER}\n{body}\n{END_MARKER}\ntail",
    }
    for name, text in bad.items():
        with pytest.raises(ValueError):
            verify_collected(text)


def test_reconcile_bites_on_an_unlisted_skip():
    """External round 4, R4-4: COLLECTED claimed reconcile()'s adversarial
    cases were "proven to bite" and NO SHIPPED TEST exercised them. A claim
    about a check, with no check on the claim, is the shape this whole review
    has been about — so the two cases are here, in the suite, where the seal
    runs them."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from skip_inventory import reconcile

    unlisted = ("SKIPPED [1] tests/test_invented.py:1: a reason no entry carries\n"
                "1 passed, 1 skipped in 0.1s")
    problems = reconcile(unlisted)
    assert problems, "an unlisted skip must be reported"
    assert any("NOT IN THE INVENTORY" in p for p in problems), problems


def test_reconcile_bites_on_a_truncated_report():
    """The other half: a `-rs` section that lists fewer skips than the summary
    counts. Without this, a truncated report reconciles by omission — which is
    how an incomplete inventory looks identical to a complete one."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from skip_inventory import reconcile

    truncated = ("SKIPPED [1] tests/test_spec_gate.py:900: COLLECTED.txt not present\n"
                 "1 passed, 5 skipped in 0.1s")
    problems = reconcile(truncated)
    assert problems, "a truncated -rs section must be reported"
    assert any("truncated" in p for p in problems), problems


def test_the_renderer_cannot_silently_drop_a_category():
    """R4-4's root cause: `render()`'s category list was HARD-CODED and omitted
    "future-obligation", so four inventory entries never reached the generated
    block — and `verify_collected` passed because it compares the block to the
    same blind renderer. The renderer now raises on any category it would drop;
    this proves the guard fires."""
    import sys, pathlib, pytest
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    import skip_inventory as S

    original = list(S.INVENTORY)
    try:
        S.INVENTORY.append(("tests/test_invented.py", "skip", "a token",
                            "a-category-the-renderer-does-not-know", "reason"))
        with pytest.raises(ValueError, match="silently drop"):
            S.render()
    finally:
        S.INVENTORY[:] = original


def test_review_closure_blocks_are_generated_and_current():
    """External round 4, R4-3. The closure ledgers were hand-maintained beside
    reviews.py and drifted three rounds running — a round count disagreeing
    with its own rows, a placeholder claiming it had been removed sitting under
    the rows it denied, two tables with different column counts in one file.

    This is the defect findings.py's own docstring opens with: "every summary
    was maintained independently of the thing it summarised". The fix is the
    one this repo already made for STATUS.md — derive it — and this test is the
    `--check` half, so drift fails the build instead of a reviewer."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "render_closure.py"),
                        "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout


def test_reconcile_handles_an_emitted_reason_that_differs_from_its_source_token():
    """External round 5, R5-4 — the ROOT-HOST regression.

    An inventory `token` is a SOURCE-SITE token: it must appear near the
    `pytest.skip(...)` call so the completeness gate can locate the site.
    pytest emits the RESOLVED reason, which is frequently different text. The
    euid entry's token is `geteuid`; on a root host pytest prints "root
    traverses any directory...". reconcile() matched emitted reasons against
    source tokens and therefore called a LISTED skip unlisted — but only when
    running as root, which is why no run of ours ever saw it and a reviewer's
    did.

    This pins both vocabularies, and it is the regression that would have
    failed on their host and passed on ours."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "specs"))
    from skip_inventory import reconcile

    root_host = ("SKIPPED [1] tests/test_migrations_0013.py:1: root traverses any "
                 "directory, so the read-only-store fixture cannot bite\n"
                 "1 passed, 1 skipped in 0.1s")
    assert not reconcile(root_host), reconcile(root_host)

    non_root = ("SKIPPED [1] tests/test_migrations_0013.py:1: geteuid() == 0 defeats "
                "the read-only-store fixture\n"
                "1 passed, 1 skipped in 0.1s")
    assert not reconcile(non_root), reconcile(non_root)


def test_r19_binds_the_product_store_the_moment_a_revocation_writer_appears():
    """0022 R19's PRODUCT-STORE binding test.

    THE HONEST STATUS FIRST: `source_revocations` DOES NOT EXIST in
    `src/veracium/` today. 0022 and 0023 were ACCEPTED at external round 21
    (2026-08-20) and are not yet implemented — the state this repo's process
    deliberately passes through, since only an accepted spec AUTHORISES
    implementation (0006 sat in it for days). A test binding the shipped
    construction to shipped store code cannot test behaviour that has not been
    written.

    What it CAN do, and this is not a stub, is PRE-EXIST the code and bite the
    moment it lands. Every structural invariant in this pair works that way —
    0004 W7's sole-writer sweep, 0023 N2's single-disclosure-writer sweep,
    0025 X7. Writing the check after the implementation is how
    `_invalidate_edge_row` acquired two call sites that each had to remember
    the wiki drop.

    SCOPED TO THE ENCLOSING FUNCTION, not the module. A module-level substring
    check passes any non-conforming writer that happens to live beside an
    unrelated BEGIN IMMEDIATE, and `sqlite.py` already contains two. That
    weakness was found by exercising the NEGATIVE case on a scratch copy: the
    module-level form accepted a writer with the BEGIN removed."""
    import ast, re, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    store = root / "src" / "veracium" / "store"
    pattern = re.compile(r"(INSERT|UPDATE|DELETE)[^\n]*source_revocations", re.I)

    writers = []
    for f in sorted(store.rglob("*.py")):
        text = f.read_text()
        if "source_revocations" not in text:
            continue
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.get_source_segment(text, node) or ""
            if pattern.search(body):
                writers.append((f.relative_to(root), node.name, node.lineno, body))

    if not writers:
        # This branch used to assert the specs were NOT accepted, on the
        # premise that acceptance and implementation arrive together. The
        # premise was wrong the day it was tested: acceptance AUTHORISES
        # implementation here, it does not imply it — 0006 sat
        # accepted-unimplemented, and 0022/0023 entered the same state at
        # round 21. The dormancy that assertion guarded against cannot occur:
        # any implementation must write `source_revocations` inside
        # `src/veracium/store/`, which is exactly where this sweep reads, so
        # the moment a writer lands the real assertions below run on it.
        # Accepted-with-no-writer is the authorised-pending state, not a
        # defect.
        return

    for path, fname, line, body in writers:
        assert "BEGIN IMMEDIATE" in body, (
            f"{path}:{line} `{fname}` writes source_revocations without "
            f"BEGIN IMMEDIATE in the SAME function. R19: allocate, re-read, "
            f"plan, append and apply must be ONE serialised write — and "
            f"`with conn:` begins nothing (external round 2, R3-1)")
        # `.upper()` on both sides: comparing an uppercased haystack against a
        # mixed-case needle could ONLY fail, which is a check that cannot pass.
        assert "MAX(SEQ)" in body.upper(), (
            f"{path}:{line} `{fname}` writes source_revocations without "
            f"allocating the ordinal from MAX(seq) in the same function — "
            f"R19 requires the allocation INSIDE the transaction")


def test_the_r19_operation_block_matches_its_executable():
    """External round 5, R5-2 said the spec's construction was "quoted
    verbatim" when it differed from the executable. I withdrew the claim; this
    makes it TRUE instead. specs/render_operation.py emits §4e-i's block from
    `revocation_operation`'s own source, byte for byte, and this is the
    --check half."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    r = subprocess.run([sys.executable, str(root / "specs" / "render_operation.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr or r.stdout


def test_the_closure_ledger_is_complete_against_the_reviews():
    """External round 6, R6-3. `render_closure --check` proved the rendered
    block matched `closure_findings.py` — it could not prove that file matched
    REALITY, so the ledger sat 12-of-15 and 3-of-5 complete while the gate
    stayed green.

    That is the third time in this review that a check compared an artifact to
    the same incomplete source it was generated from: `verify_collected`
    against a blind renderer (R4-4), one hand-maintained twin replaced by
    another (R5-3), and this. The finding ids are now EXTRACTED from
    `reviews.py`'s verdict text — written first, independently — and every one
    must have a ledger row."""
    import subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from render_closure import completeness_problems
    problems = completeness_problems()
    assert not problems, "\n".join(problems)


def test_the_round5_verbatim_withdrawal_is_absent_from_0022():
    """External round 7, R7-1's tail. R6-2's closure evidence was a
    `grep -q` for the withdrawn assertion's ABSENCE — and that command is
    rendered into the generated ledger inside 0022 itself, so the file
    contained its own needle and the evidence failed on a clean tree.

    A grep-for-absence cannot live in the document it searches. The assertion
    lives here instead, where the ledger can point at it without becoming it."""
    import pathlib
    spec = (pathlib.Path(__file__).resolve().parent.parent / "specs"
            / "0022-source-revocation.md").read_text()
    # split off the GENERATED ledger, which legitimately DESCRIBES the finding
    body = spec.split("<!-- GENERATED:review-closure -->")[0]
    assert '"QUOTED VERBATIM" IS WITHDRAWN' not in body, (
        "0022 §4e-i has regained round 5's withdrawal assertion, which "
        "contradicts the block generated from the executable on the same page "
        "(external round 6, R6-2)")


def test_every_closure_evidence_command_actually_runs():
    """External round 7, R7-1. Four of the ledger's evidence commands could not
    run as written — three said `python3 -m pytest` and a bare python3 has no
    pytest; one was a grep-for-absence rendered INTO the document it searched,
    so the file supplied its own needle.

    PROCESS §4a asks for openable evidence. A command that does not execute is
    a description of evidence, which is the exact substitution this field
    exists to refuse — so the commands are RUN here rather than eyeballed.

    `$PY` is the reviewer's interpreter (the offline launcher's venv). Commands
    that need the whole suite are skipped when it is absent, and named, so a
    thin environment cannot silently reduce coverage."""
    import os, subprocess, sys, pathlib, pytest
    # RECURSION BOUND. Several evidence commands legitimately invoke
    # `pytest tests/test_spec_gate.py`, which runs THIS test, which runs them
    # again — nesting until the timeout. Measured: the suite went from 27s to
    # 10m44s and this test failed inside itself. The runner marks its children,
    # and a marked child does not re-enter. Depth 1, and the check is still the
    # one that matters: every command runs, once, from the top.
    if os.environ.get("VERACIUM_EVIDENCE_CHILD"):
        pytest.skip("nested evidence run — the parent already executes every "
                    "command exactly once")
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from closure_findings import CLOSURES

    py = root / ".venv-offline" / "bin" / "python"
    if not py.exists():
        py = pathlib.Path(sys.executable)
    # `-p no:cacheprovider` because concurrency introduces one hazard the
    # reviewer never has: they run these commands ONE AT A TIME, so their
    # children never contend for `.pytest_cache`. Ours now do. Disabling the
    # cache in our runner restores the reviewer's conditions rather than
    # departing from them, and it changes nothing a command asserts.
    #
    # Recorded because it is unresolved: one run failed here with a child
    # reporting a test failure that five subsequent runs — three normal, two
    # under deliberate extra load — did not reproduce, and I no longer have its
    # output. This is the most plausible mechanism I can name, not a diagnosis.
    # CI runs the suite on every push and the transcript now records per-command
    # durations, so a load-induced failure has somewhere to show up.
    env = dict(os.environ, PY=str(py), VERACIUM_EVIDENCE_CHILD="1",
               PYTEST_ADDOPTS="-p no:cacheprovider")

    import hashlib, json, time
    from concurrent.futures import ThreadPoolExecutor

    # WHY THIS RUNS CONCURRENTLY, measured rather than assumed.
    #
    # The ledger holds 59 runnable commands and each pays ~6.5s that is almost
    # entirely interpreter start plus importing the project — 1.1s of it is
    # `import pytest` alone. Serially that is ~6.4 minutes, and it was the bulk
    # of an 8-minute suite and of every seal.
    #
    # The obvious fix was the wrong one. Selecting by NODE ID instead of `-k`
    # saves nothing, because `-k` is not what costs: measured on this tree, the
    # node-id form ran 7.58s against 6.48s for `-k`. The cost is the import,
    # and the only way to stop paying it 59 times in a row is to stop being in
    # a row.
    #
    # Each command keeps running EXACTLY as written, in its own process, with
    # its own exit code and output digest — the reviewer runs these one at a
    # time and must get what we got. Only the scheduling changes. Results are
    # reassembled in LEDGER ORDER, so the transcript is byte-identical to what
    # a serial run would have produced apart from the durations.
    workers = min(4, (os.cpu_count() or 2))

    # SOME EVIDENCE MEASURES CONTENTION, so it cannot be measured under
    # contention. The store-concurrency harness times SQLite BUSY behaviour and
    # a deadline; run beside three other interpreters on a four-core box it
    # reported 17/18 and failed the seal. That is not flakiness to be retried
    # away — the command's SUBJECT is timing, so unrelated load changes what it
    # observes, and a green result obtained that way would be worth less than
    # the slow one.
    #
    # These run alone, after the concurrent batch has drained. The property is
    # a fact about what the command measures, not a workaround, so it is named
    # by what it runs rather than by which finding cites it — five closure rows
    # cite this harness today and a sixth must not silently miss the lane.
    NEEDS_QUIET = ("store_concurrency_harness",)

    runnable, quiet, skipped = [], [], []
    for row in CLOSURES:
        spec, _kind, _rno, fid, _summary, _closed, evidence = row
        # the launcher builds a venv and runs the entire suite: running it from
        # inside the suite would recurse
        if "run_offline.sh" in evidence:
            skipped.append(f"{spec} {fid} (launcher — run separately at seal)")
        elif any(n in evidence for n in NEEDS_QUIET):
            quiet.append((spec, fid, evidence))
        else:
            runnable.append((spec, fid, evidence))
    assert quiet, ("no command claims the quiet lane — the harness that "
                   "measures contention was renamed, and it is now being "
                   "measured under load")

    def _execute(item):
        spec, fid, evidence = item
        t0 = time.monotonic()
        r = subprocess.run(evidence, shell=True, capture_output=True,
                           cwd=root, env=env, timeout=600)
        ms = int((time.monotonic() - t0) * 1000)
        out = (r.stdout or b"") + (r.stderr or b"")
        return {
            "spec": spec, "finding": fid, "argv": evidence, "cwd": str(root),
            "exit": r.returncode, "duration_ms": ms,
            "output_sha256": hashlib.sha256(out).hexdigest(),
        }, (None if r.returncode == 0 else
            f"{spec} {fid}: exit {r.returncode}\n    {evidence}\n"
            f"    {out.decode(errors='replace')[-200:]}")

    wall0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(_execute, runnable))
    results += [_execute(item) for item in quiet]      # alone, machine idle
    wall_ms = int((time.monotonic() - wall0) * 1000)

    # LEDGER ORDER, whatever order they finished in: the transcript must be
    # what a serial run would have produced.
    order = {(spec, fid): i for i, (spec, _k, _r, fid, _s, _c, _e)
             in enumerate(CLOSURES)}
    results.sort(key=lambda r: order[(r[0]["spec"], r[0]["finding"])])
    transcript = [rec for rec, _ in results]
    failures = [f for _, f in results if f]

    # THE TRANSCRIPT IS THE ARTIFACT (external round 11): argv, cwd, exit and an
    # output digest per command. The sealer READS this instead of spawning
    # another pytest to watch this test print a number — that duplication took
    # the suite from 39s to 23 MINUTES and is the reason this file exists.
    # It also answers the reviewer's standing request for an execution record.
    gen = root / "specs" / "generated"
    gen.mkdir(exist_ok=True)
    # `wall_ms` and the per-command `duration_ms` exist so the NEXT round can
    # see what the checks cost without rediscovering it. Every round added a
    # check and no round measured one; a number nobody records is a number
    # nobody defends.
    (gen / "evidence_run.json").write_text(json.dumps(
        {"ran": len(transcript), "wall_ms": wall_ms, "workers": workers,
         "skipped": skipped, "commands": transcript},
        indent=1) + "\n")

    assert not failures, "closure evidence that does not run:\n  " + "\n  ".join(failures)

    # R12-2's validation happens HERE, against the transcript this test just
    # wrote, and not in a test of its own.
    #
    # It USED to be a separate test that read the live file — and `pytest-
    # randomly` (a dev dependency, shuffling order every run) put the reader
    # before the writer on some seeds, so CI went red intermittently from the
    # round-12 seal onward while every local run happened to order them the
    # other way. Five red runs before I looked, which is the actual lesson: the
    # ledger already recorded that this artifact must not be read by anything
    # taking part in its production, and that rule was applied to the EVIDENCE
    # COMMANDS while a test was left depending on another test to run first.
    #
    # A test that needs a different test to have run is the same defect as an
    # evidence command that reads what the runner writes. The dependency is
    # removed rather than ordered: one test writes the transcript and validates
    # it in the same breath. Presence is still MANDATORY where it matters — the
    # sealer calls validate() directly and the extraction runs
    # specs/evidence_transcript.py inside the archive — so nothing is weakened
    # by this test not existing separately.
    sys.path.insert(0, str(root / "specs"))
    from evidence_transcript import validate as _validate
    problems = _validate(gen / "evidence_run.json", root / "specs")
    assert not problems, ("the transcript this run just produced does not "
                          "validate:\n  " + "\n  ".join(problems))

    slowest = sorted(transcript, key=lambda c: -c["duration_ms"])[:3]
    print(f"\n{len(transcript)} evidence commands ran clean in "
          f"{wall_ms / 1000:.1f}s across {workers} workers "
          f"(serial cost would be {sum(c['duration_ms'] for c in transcript) / 1000:.1f}s); "
          f"slowest: " + ", ".join(f"{c['finding']} {c['duration_ms']}ms"
                                   for c in slowest)
          + f"; skipped: {skipped}")


def test_a_returned_verdict_must_declare_what_it_raised():
    """External round 8, R8-1. `raised` was read with `.get(..., [])`, so
    FORGETTING the field was indistinguishable from declaring no findings —
    the reviewer injected a verdict naming R99-1 with no `raised` and the gate
    reported zero problems. Omission is not a declaration."""
    import sys, pathlib, pytest
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import render_closure

    real = render_closure.review_findings()          # the clean tree must pass
    assert real

    import reviews
    victim = next(r for r in reviews.REVIEWS
                  if r["spec"] in render_closure.TRACKED
                  and not render_closure._is_sent(r))
    saved = victim.pop("raised")
    try:
        with pytest.raises(ValueError, match="NO `raised` field"):
            render_closure.review_findings()
    finally:
        victim["raised"] = saved


def test_the_rendered_finding_count_comes_from_raised_not_the_legacy_field():
    """R8-1's other half: the column is labelled "findings raised" and was fed
    by the legacy `findings=`, which disagrees with `raised` in four rows. The
    displayed number now comes from the structure it claims to show."""
    import sys, pathlib, re
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import reviews, render_closure

    disagree = [r for r in reviews.REVIEWS
                if "raised" in r and r.get("findings") != len(r["raised"])]
    assert disagree, ("this regression is pointless if no row disagrees — if "
                      "the legacy field has been reconciled, delete this test")
    block = render_closure.render(disagree[0]["spec"])
    row = [l for l in block.splitlines()
           if l.startswith(f"| {disagree[0]['kind']} {disagree[0]['round']} (verdict)")]
    assert row, f"no rendered row for {disagree[0]['spec']} {disagree[0]['round']}"
    shown = row[0].split("|")[3].strip()
    assert shown == str(len(disagree[0]["raised"])), (
        f"the rendered count is {shown}, the legacy field is "
        f"{disagree[0]['findings']}, and `raised` has "
        f"{len(disagree[0]['raised'])} — the column must show the structure")


def test_the_extraction_check_list_matches_the_sealer_registry():
    """External round 9, R9-1. Both package carriers claimed the sealer reran
    "both harnesses and both verifiers from the EXTRACTED archive". It ran the
    two harnesses; the verifiers ran before the archive existed, against the
    build tree — the reviewer traced the subprocesses.

    The claim was the better one, so the code moved to meet it. This binds the
    carrier's list to the sealer's registry: the header carries a token the
    sealer fills FROM `EXTRACTION_CHECKS`, and the sealer aborts if it runs
    anything else. A description of what a tool does, maintained separately
    from the tool, is the defect this whole review has been about."""
    import sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import seal_package

    # R11-1: the FULL normalised argv, pinned. The previous version accepted
    # any command whose text contained the right words, and
    # `python -c "pass # verify_collected COLLECTED"` passed it. Every entry
    # now ends in a FILE whose behaviour is fixed by its own source.
    def norm(cmd):
        # the interpreter is part of what the label promises: an entry run
        # by the shell is a different thing from one run by python, and
        # collapsing both to "python" would let a registry entry advertise
        # a command it does not run. (PACKAGE-M18-1 added the first
        # non-python entry — the launcher, which is a bash script.)
        head = "python" if cmd[0] == sys.executable else cmd[0]
        return (head,) + tuple(cmd[1:])

    names = [n for n, _ in seal_package.EXTRACTION_CHECKS]
    assert len(names) == len(set(names)), f"duplicate check names: {names}"

    required = {
        "vector_harness.py":
            ("python", "specs/evidence/0022/vector_harness.py"),
        "store_concurrency_harness.py":
            ("python", "specs/evidence/0022/store_concurrency_harness.py"),
        "verify_extracted.py collected":
            ("python", "specs/verify_extracted.py", "collected"),
        "verify_extracted.py reconcile":
            ("python", "specs/verify_extracted.py", "reconcile"),
        "evidence_transcript.py (validate the shipped transcript)":
            ("python", "specs/evidence_transcript.py"),
        # Round-14 standing feedback (A1): the candidate patch verified by
        # applying to a temp copy and running the patched file's OWN
        # runner — the wrapper-vs-runner mismatch, mechanically closed.
        "verify_a1_patch.py (apply + own-runner the A1 candidate)":
            ("python", "specs/verify_a1_patch.py"),
        "validate_baseline.py (recompute the 4:1 result offline)":
            ("python",
             "specs/evidence/0024/baseline/validate_baseline.py"),
        "render_closure.py --check":
            ("python", "specs/render_closure.py", "--check"),
        "render_operation.py --check":
            ("python", "specs/render_operation.py", "--check"),
        # R16-2: the lessons carrier was verified in the build tree and NOWHERE
        # in the archive, so a block appended after the build was invisible to
        # the only verification the reviewer receives.
        "review_lessons.py --check":
            ("python", "specs/review_lessons.py", "--check"),
        # R17-1: identity is structured data now, and the record is verified
        # from the extraction like every other generated carrier.
        "package_identity.py (the record agrees with reviews.py)":
            ("python", "specs/package_identity.py"),
        # C-plus (COLLECTED_HEADER_DESIGN §5): the header record, the
        # whole-file equation, and the witnesses — from the extraction.
        "verify_extracted.py header":
            ("python", "specs/verify_extracted.py", "header"),
        # PACKAGE-M18-1: the qualified suite runs where the REVIEWER runs
        # it — inside the extracted archive — and a red run refuses the
        # seal. This is 0022 R9-1 (the finding this very test was written
        # for) recurring in the one carrier that fix did not reach: the
        # launcher ran at cwd=ROOT, measuring the build tree, while the
        # header presented the number as the package's.
        "the qualified suite, from the EXTRACTED archive (PACKAGE-M18-1)":
            ("bash", "specs/evidence/offline/run_offline.sh"),
    }
    got = {n: norm(c) for n, c in seal_package.EXTRACTION_CHECKS}
    assert set(got) == set(required), (
        f"the extraction registry is {sorted(got)}, expected {sorted(required)}")
    for label, argv in required.items():
        assert got[label] == argv, (
            f"{label} runs {got[label]}, not {argv} — the carrier advertises "
            f"the LABEL, so the label must name the command that runs")
    for label, argv in got.items():
        assert "-c" not in argv, (
            f"{label} uses an inline -c program; R11-1 showed those can only "
            f"be checked by inspecting their source text, which a comment "
            f"defeats. Use a named script.")

    header = (root / "specs" / "package" / "collected_header.txt").read_text()
    assert "__EXTRACTED__" in header, (
        "the header must carry the token the sealer fills from the registry — "
        "a hand-written list is what R9-1 found overstating the checks")


def test_corrupting_the_packaged_collected_makes_the_extraction_refuse():
    """External round 11, R11-1's behavioural mutation, run rather than
    described.

    The previous version of this test substituted a no-op COMMAND and checked
    that a SOURCE-INSPECTING assertion caught it — which the reviewer defeated
    with `python -c "pass # verify_collected COLLECTED"`. Inspecting a string
    proves nothing about what runs.

    So this corrupts the packaged carrier and requires the extraction verifier
    to REFUSE. It exercises the real script, on real files, exactly as the
    sealer runs it from an extracted archive."""
    import subprocess, sys, pathlib, shutil, tempfile
    root = pathlib.Path(__file__).resolve().parent.parent
    live_rs = root / "COLLECTED_pytest_rs.txt"
    live_col = root / "COLLECTED.txt"

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        shutil.copytree(root / "specs", d / "specs",
                        ignore=shutil.ignore_patterns("archives", "__pycache__"))
        # a MINIMAL sealed pair: whatever the tree currently has, or a stub
        if live_col.exists() and live_rs.exists():
            shutil.copy2(live_col, d / "COLLECTED.txt")
            shutil.copy2(live_rs, d / "COLLECTED_pytest_rs.txt")
        else:
            sys.path.insert(0, str(root / "specs"))
            import skip_inventory as S
            rs = "1 passed, 0 skipped in 0.1s\n"
            (d / "COLLECTED_pytest_rs.txt").write_text(rs)
            (d / "COLLECTED.txt").write_text(
                "head\n" + S.BEGIN_MARKER + "\n" + S.render(rs) + "\n"
                + S.END_MARKER + "\n")

        script = d / "specs" / "verify_extracted.py"
        clean = subprocess.run([sys.executable, str(script), "collected"],
                               cwd=d, capture_output=True, text=True)
        assert clean.returncode == 0, (
            f"the verifier must PASS on the intact carriers first, else the "
            f"mutation proves nothing: {clean.stderr}")

        # CORRUPT the packaged carrier — one byte inside the generated block
        col = d / "COLLECTED.txt"
        text = col.read_text()
        marker = text.index("<!-- GENERATED:skip-inventory -->")
        col.write_text(text[:marker + 40] + "CORRUPTED" + text[marker + 40:])

        dirty = subprocess.run([sys.executable, str(script), "collected"],
                               cwd=d, capture_output=True, text=True)
        assert dirty.returncode != 0, (
            "the extraction verifier ACCEPTED a corrupted COLLECTED.txt — "
            "R11-1's point: the check must bind behaviour, not spelling")
        assert "verify_collected FAILED" in dirty.stderr, dirty.stderr


def test_the_sealed_environment_drops_the_recursion_marker():
    """External round 11, R11-2. `measure()` copied all of os.environ and
    overrode two keys. With VERACIUM_EVIDENCE_CHILD=1 in the shell, the
    evidence runner SKIPS — and the sealer still generated "all N evidence
    commands ran", because that number came from the closure ledger's length
    rather than from execution. The skip is inventoried, so reconciliation
    would not have rejected it either: a sealed package could assert an
    execution that had been silently switched off.

    The sealing environment is an allowlist now. This pins the two properties
    that matter: the recursion marker cannot survive it, and no VERACIUM_*
    flag can."""
    import os, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import seal_package

    saved = dict(os.environ)
    try:
        os.environ["VERACIUM_EVIDENCE_CHILD"] = "1"
        os.environ["VERACIUM_ROBUSTNESS"] = "1"
        os.environ["VERACIUM_SOMETHING_NEW"] = "1"
        env = seal_package.sealed_env(PYTHONPATH="src")
        assert "VERACIUM_EVIDENCE_CHILD" not in env, (
            "the recursion marker survived the sealing environment — it turns "
            "the evidence runner into a skip while the claim stands")
        leaked = [k for k in env if k.startswith("VERACIUM_")
                  and k != "VERACIUM_FORBID_NETWORK"]
        assert not leaked, f"VERACIUM_* flags leaked into sealing: {leaked}"
        assert "PATH" in env and env["PYTHONPATH"] == "src"
    finally:
        os.environ.clear()
        os.environ.update(saved)


def test_a_counterfeit_or_missing_transcript_is_rejected():
    """R12-1 and R12-2's adversarial cases, run rather than described: the
    reviewer DELETED the transcript from an archive and it still passed, and
    fabricated a zero-record one that satisfied every count check."""
    import json, pathlib, shutil, sys, tempfile
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from evidence_transcript import (validate, REL_PATH, TOP_SCHEMA,
                                     COMMAND_SCHEMA)

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        (d / "specs").mkdir()
        shutil.copy2(root / "specs" / "closure_findings.py", d / "specs")

        # (a) DELETED — the R12-1 archive mutation
        assert validate(d / REL_PATH, d / "specs"), (
            "a missing transcript must be rejected")

        # (b) COUNTERFEIT — the R12-2 fabrication
        t = d / "evidence_run.json"
        t.write_text(json.dumps({"ran": 40, "skipped": [], "commands": []}))
        assert validate(t, d / "specs"), (
            "the reviewer's literal counterfeit must be rejected")
        # ...and the PROPERTY it was written to prove, kept alive as the schema
        # grows: a schema-complete transcript with zero records still cannot
        # claim a count. Without this, extending the schema would silently
        # retire R12-2's finding — the counterfeit would be refused for a
        # missing field and the "a number is not evidence" check would never
        # run again.
        t.write_text(json.dumps({"ran": 40, "wall_ms": 1, "workers": 1,
                                 "skipped": [], "commands": []}))
        problems = validate(t, d / "specs")
        assert problems, "the counterfeit transcript must be rejected"
        assert any("command records" in p for p in problems), problems

        # (c) R13-1: FIELD VALUES, not just presence. `exit: false` passed
        # because in Python False == 0; a 64-character non-hex string passed a
        # length check; and `cwd: null` passed a presence check. A full-length
        # transcript of every ledger row, entirely fabricated, was accepted.
        from closure_findings import CLOSURES
        rows = [{"spec": c[0], "finding": c[3], "argv": c[6],
                 "cwd": None, "exit": False, "output_sha256": "x" * 64,
                 "duration_ms": 1}
                for c in CLOSURES if "run_offline.sh" not in c[6]]
        skipped = [f"{c[0]} {c[3]} (launcher — run separately at seal)"
                   for c in CLOSURES if "run_offline.sh" in c[6]]
        t.write_text(json.dumps({"ran": len(rows), "wall_ms": 1,
                                 "workers": 1, "skipped": skipped,
                                 "commands": rows}))
        problems = validate(t, d / "specs")
        assert problems, ("a transcript with null cwds, boolean exits and "
                          "non-hex digests must be rejected")
        # assert on the FIELD reported, not on prose: the round-14 schema
        # rewrite changed every message, and a regression pinned to wording
        # fails for the right fix as loudly as for a regression
        assert any("`exit`" in p for p in problems), problems
        assert any("`output_sha256`" in p for p in problems), problems
        assert any("`cwd`" in p for p in problems), problems

        # (d) R14-1: THE COERCIONS THE LANGUAGE PERFORMS SILENTLY. Round 13
        # typed three fields; three MORE cells were still coercible —
        # `ran: 45.0` (45.0 == 45), a 64-digit JSON INTEGER digest surviving
        # `str()` before the hex regex, and a duplicated `skipped` entry
        # vanishing into a set. The reviewer applied all three at once and
        # repacked an archive the verifier accepted.
        clean_rows = [{"spec": c[0], "finding": c[3], "argv": c[6],
                       "cwd": "/x", "exit": 0, "output_sha256": "a" * 64,
                       "duration_ms": 1}
                      for c in CLOSURES if "run_offline.sh" not in c[6]]
        combined = {"ran": float(len(clean_rows)), "wall_ms": 1,
                    "workers": 1, "skipped": skipped * 2,
                    "commands": [dict(r, output_sha256=int("1" * 64))
                                 for r in clean_rows]}
        t.write_text(json.dumps(combined))
        problems = validate(t, d / "specs")
        assert problems, "the combined R14-1 mutation must be rejected"
        assert any("`ran`" in p for p in problems), problems

        # each coercion alone, so a partial fix cannot hide behind the others.
        #
        # EXTERNAL ROUND 15 (R15-1) CHANGED THE SHAPE OF THIS TEST. The list
        # below was hand-enumerated, so it covered exactly the attacks that had
        # already been made: every entry mutated a COMMAND field, and none
        # added an undeclared key to the object HOLDING the commands. The
        # closedness the schema advertised was therefore untested one level up,
        # and `{"undeclared_top_level": "accepted"}` rode through validate(),
        # the archive verifier, and a repacked archive.
        #
        # A hand list can only replay the attacks already suffered. So the
        # matrix below is DERIVED FROM THE SCHEMA: every declared field of
        # every level gets a cross-type mutation, and every level with keys
        # gets an undeclared-key mutation. The coverage assertion at the end
        # closes the loop — add a field or a level to the schema without a
        # mutation and this test fails, which is the check that did not exist
        # when R15-1 was written.
        clean = {"ran": len(clean_rows), "wall_ms": 1, "workers": 1,
                 "skipped": skipped, "commands": clean_rows}

        def _cross_type(v):
            """Values of every JSON type the clean value is NOT. Every schema
            check pins an exact type, so all of these must be rejected —
            including `True` for an int field, which is R13-1's attack
            regenerated rather than remembered."""
            bank = [None, True, 7, 4.5, "x", ["x"], {"k": "v"}]
            return [b for b in bank if type(b) is not type(v)]

        def _at_top(doc, field, value):
            return {**doc, field: value}

        def _at_command(doc, field, value):
            head = dict(doc["commands"][0], **{field: value})
            return {**doc, "commands": [head] + doc["commands"][1:]}

        LEVELS = (("top", TOP_SCHEMA, _at_top, "`%s`"),
                  ("command", COMMAND_SCHEMA, _at_command, "`%s`"))
        covered = set()
        for level, schema, place, needle_fmt in LEVELS:
            for field in schema:
                for bad in _cross_type(clean[field] if level == "top"
                                       else clean["commands"][0][field]):
                    doc = place(clean, field, bad)
                    t.write_text(json.dumps(doc))
                    ps = validate(t, d / "specs")
                    assert ps, (f"{level} `{field}` = {bad!r} "
                                f"({type(bad).__name__}) was ACCEPTED")
                    assert any((needle_fmt % field) in x or "missing" in x
                               or "not a JSON object" in x for x in ps), \
                        f"{level} `{field}` = {bad!r}: wrong complaint {ps}"
                covered.add((level, field))

                # and the key REMOVED — a schema that only type-checks present
                # keys is satisfied by an empty object
                doc = place(clean, field, None)
                doc = ({k: v for k, v in doc.items() if k != field}
                       if level == "top" else
                       {**clean, "commands": [
                           {k: v for k, v in clean["commands"][0].items()
                            if k != field}] + clean["commands"][1:]})
                t.write_text(json.dumps(doc))
                assert validate(t, d / "specs"), (
                    f"{level} with `{field}` REMOVED was accepted")

            # R15-1 ITSELF, at every level that has keys: an undeclared key
            doc = place(clean, "undeclared_%s_level" % level, "accepted")
            t.write_text(json.dumps(doc))
            ps = validate(t, d / "specs")
            assert ps, (f"an undeclared {level}-level key was ACCEPTED — "
                        f"R15-1 exactly")
            assert any("undeclared" in x for x in ps), ps
            covered.add((level, "<undeclared key>"))

        # THE COVERAGE CLOSURE: the mutation domain is the schema's domain.
        # This is the assertion whose absence let R15-1 exist — the old list
        # tested what had been attacked, not what was declared.
        expected = {(lvl, f) for lvl, schema, _, _ in LEVELS for f in schema}
        expected |= {(lvl, "<undeclared key>") for lvl, _, _, _ in LEVELS}
        assert covered == expected, (
            f"the mutation matrix does not cover the schema: "
            f"missing {sorted(expected - covered)}")

        # THE REVIEWER'S EXACT ATTACKS, replayed. The matrix above generates
        # cross-type mutations; these are SAME-TYPE near misses no generator
        # would invent, each one an attack that was actually made.
        for name, doc, needle in (
            ("R14-1 float ran", {**clean, "ran": float(len(clean_rows))},
             "`ran`"),
            ("R14-1 int digest", {**clean, "commands": [
                dict(r, output_sha256=int("1" * 64)) for r in clean_rows]},
             "`output_sha256`"),
            ("R14-1 duplicated skipped", {**clean, "skipped": skipped * 2},
             "duplicates"),
            ("R13-1 non-hex 64-char digest", {**clean, "commands": [
                dict(r, output_sha256="x" * 64) for r in clean_rows]},
             "`output_sha256`"),
            ("R13-1 relative cwd", {**clean, "commands": [
                dict(r, cwd="relative/path") for r in clean_rows]}, "`cwd`"),
            ("R14-1 undeclared command field", {**clean, "commands": [
                dict(r, sneaky="x") for r in clean_rows]}, "undeclared field"),
            ("R15-1 undeclared top-level field",
             {**clean, "undeclared_top_level": "accepted"},
             "undeclared top-level"),
        ):
            t.write_text(json.dumps(doc))
            ps = validate(t, d / "specs")
            assert ps and any(needle in x for x in ps), f"{name}: {ps}"

        # and the CLEAN transcript must still pass, or the schema is just a
        # wall — a check that rejects everything passes all its rejection tests
        t.write_text(json.dumps(clean))
        assert not validate(t, d / "specs"), (
            "the schema rejects a well-formed transcript")

        # (e) RECORDS THAT DO NOT MATCH THE LEDGER
        t.write_text(json.dumps({
            "ran": 1, "wall_ms": 1, "workers": 1, "skipped": [],
            "commands": [{"spec": "0022", "finding": "INVENTED",
                          "argv": "echo hi", "cwd": "/tmp", "exit": 0,
                          "output_sha256": "0" * 64, "duration_ms": 1}]}))
        problems = validate(t, d / "specs")
        assert any("matches no closure row" in p for p in problems), problems


def test_every_k_atom_in_the_closure_ledger_selects_a_test():
    """External round 13, R13-3. R11-2's evidence selected
    `sealed_environment or reports_a_count`, but `reports_a_count` had been
    replaced — so the command reported "1 passed, 80 deselected" and exercised
    only half of what its label claimed. It EXITED 0, so the
    every-command-runs gate was satisfied by a check that had quietly stopped
    covering its own finding.

    A `-k` expression that matches nothing is the sharpest form of this
    review's recurring defect: it passes, it looks like evidence, and it tests
    nothing. Every atom must select at least one test."""
    import re, subprocess, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from closure_findings import CLOSURES

    atoms = set()
    for c in CLOSURES:
        for m in re.finditer(r"-k\s+'([^']+)'|-k\s+(\S+)", c[6]):
            expr = m.group(1) or m.group(2)
            for a in re.split(r"\s+(?:or|and)\s+", expr):
                a = a.strip().strip("()")
                if a:
                    atoms.add(a)
    assert atoms, "no -k atoms found — has the evidence format changed?"

    # ONE COLLECTION, not one per atom. This spawned `pytest --collect-only -k
    # <atom>` for each of the 19 atoms, and collection costs ~6.5s on this tree
    # — almost all of it interpreter start and importing the project — so the
    # gate paid two minutes to ask a question about strings. Collect once, then
    # answer every atom against the same list.
    #
    # THE PROPERTY IS UNCHANGED: `-k <atom>` for a bare atom selects the tests
    # whose node id contains it as a substring, which is exactly the test
    # below. The controls guard the equivalence rather than assuming it — a
    # known-present atom must be found and a deliberately absent one must not,
    # so a collection that returned nothing (or everything) cannot pass this.
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only",
         "tests/test_spec_gate.py"],
        cwd=root, capture_output=True, text=True)
    node_ids = [l.strip() for l in r.stdout.splitlines() if "::" in l]
    assert len(node_ids) > 50, (
        f"the single collection returned {len(node_ids)} node ids — too few "
        f"for this file, so every atom below would pass or fail for the wrong "
        f"reason:\n{r.stdout[-400:]}")

    def selects(atom):
        return any(atom in nid for nid in node_ids)

    assert selects("k_atom_in_the_closure"), (
        "the collection does not contain THIS test — the matcher is broken")
    assert not selects("definitely_not_a_test_name_9f3a"), (
        "the matcher claims an absent atom selects something")

    empty = sorted(a for a in atoms if not selects(a))
    assert not empty, (
        f"these -k atoms select NO test, so the evidence citing them exercises "
        f"nothing while exiting 0: {empty}")


def test_no_closure_evidence_reads_an_artifact_the_runner_produces():
    """CLASS 5 of specs/REVIEW_LESSONS.md — self-reference — and the only class
    that had no mechanical gate.

    Evidence commands validated the transcript the evidence runner was WRITING
    as it executed them (external R12-1/R12-2), and I REINTRODUCED it at R13-3
    while repointing a stale selector — the same defect, in the fix for a
    different one. Re-finding a class after fixing its first instance is the
    pattern this gate exists to break.

    An evidence command must not read an artifact whose production it is part
    of. Two forms are forbidden: naming the transcript path directly, and
    selecting a test that reads it."""
    import re, sys, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from closure_findings import CLOSURES
    from evidence_transcript import REL_PATH

    # tests that READ the live transcript — found by source, not by memory
    def _readers(source_text):
        found = set()
        for m in re.finditer(r"^def (test_\w+)\(", source_text, re.M):
            nxt = source_text.find("\ndef ", m.end())
            body = source_text[m.end():nxt if nxt > 0 else len(source_text)]
            # READS THE LIVE FILE, not merely mentions the constant. The
            # counterfeit test imports REL_PATH and writes its own fixtures
            # into a temp dir; flagging it would be this gate committing class
            # 4's mirror — a domain too WIDE — in the fix for class 5.
            if re.search(r"root\s*/\s*REL_PATH|root\s*/\s*[\"']specs[\"']\s*/\s*"
                         r"[\"']generated[\"']", body):
                found.add(m.group(1))
        return found

    # THE DETECTOR'S POSITIVE AND NEGATIVE CONTROLS, on synthetic source.
    # This assertion used to be `len(readers) >= 2` against the real file —
    # "the producer plus at least one genuine reader must be found, or the
    # regex matches nothing". That tied the gate's own validity to the codebase
    # CONTAINING a hazard, so removing the last live reader (the order-dependent
    # transcript test, deleted when pytest-randomly exposed it) broke the gate
    # rather than satisfying it. A control belongs on a fixture, never on the
    # continued existence of the thing being guarded against.
    #
    # The hazard fixture is COMPOSED from fragments instead of written as a
    # literal: spelled out in full, it would make this gate detect ITSELF as a
    # reader, and the ledger row that points at this test would then be flagged
    # for selecting it. Mention-versus-use, which this review has now produced
    # seven times — a docstring counted as a skip site, a finding id read as a
    # citation, a placeholder guard firing on prose about placeholders, a
    # grep-for-absence rendered into the document it searched. The rule that
    # keeps coming back: a checker's own text is inside its domain.
    hazard = "def test_hazard():\n    p = root /" + " REL_PATH\n"
    mention = "def test_safe():\n    x = REL" + "_PATH\n    d / \"f.json\"\n"
    assert _readers(hazard) == {"test_hazard"}, (
        "the reader detector matches nothing — it is vacuous")
    assert _readers(mention) == set(), (
        "the reader detector flags a mere mention — its domain is too wide")

    source = pathlib.Path(__file__).read_text()
    readers = _readers(source)
    producer = "test_every_closure_evidence_command_actually_runs"
    assert producer in source, "the evidence runner was renamed"
    assert producer in readers, (
        "the producer no longer reads the transcript it writes — if the "
        "validation moved out of it, this gate is guarding the wrong function")
    readers.add(producer)          # it WRITES the transcript

    problems = []
    for spec, kind, rno, fid, _s, _c, ev in CLOSURES:
        if "run_offline.sh" in ev:
            continue
        if REL_PATH in ev or "evidence_run.json" in ev:
            problems.append(f"{spec} {fid}: names the transcript path")
        for m in re.finditer(r"-k\s+'([^']+)'|-k\s+(\S+)", ev):
            expr = m.group(1) or m.group(2)
            for atom in re.split(r"\s+(?:or|and)\s+", expr):
                atom = atom.strip().strip("()")
                for reader in readers:
                    if atom and atom in reader:
                        problems.append(
                            f"{spec} {fid}: selects `{atom}` -> {reader}, which "
                            f"reads the transcript the runner is writing")
    assert not problems, (
        "closure evidence that reads an artifact the runner produces:\n  "
        + "\n  ".join(problems))


def _p1_binding_problems(root, artifact, test_file, test_name):
    """P1's binding, PROCESS-R23-1 form: the artifact must be referenced
    INSIDE the named test's own body (AST source segment) — a mention
    anywhere else in the file is the proxy the gate exists to refuse."""
    import ast
    problems = []
    tpath = root / test_file
    if not tpath.exists():
        return [f"matrix file {test_file} does not exist"]
    ttext = tpath.read_text()
    try:
        tree = ast.parse(ttext)
    except SyntaxError as e:
        return [f"matrix file {test_file} does not parse: {e}"]
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == test_name), None)
    if fn is None:
        return [f"matrix test {test_name} not found in {test_file}"]
    body = ast.get_source_segment(ttext, fn) or ""
    if artifact.name not in body and artifact.stem not in body:
        problems.append(
            f"{test_name}'s BODY never references the artifact by "
            f"filename or module name — the pointer binds an unrelated "
            f"test (PROCESS-R23-1: a mention elsewhere in the file is "
            f"the proxy this binding refuses)")
    return problems


def test_every_evidence_artifact_declares_a_mutation_matrix():
    """P1 (adopted 2026-08-24; claim narrowed at PROCESS-M24-1): every
    checker declares and BINDS its mutation matrix — this gate enforces
    the pointer convention (the matrix test exists and references the
    artifact in its body); the kill evidence is the matrix tests
    themselves, which CI runs. Seven consecutive external rounds were the
    reviewer mutation-testing ONE evidence script at one mutant per
    round — the most expensive way to test a parser. Every evidence
    artifact (specs/check_*.py, specs/verify_*.py, validate_*.py under
    specs/) must carry a `# Mutation-Matrix:` pointer at a NAMED pytest
    test that (a) exists and (b) references the artifact by filename —
    so an artifact cannot ship before its adversarial matrix, and a
    stale pointer at an unrelated test refuses."""
    import pathlib, re
    root = pathlib.Path(__file__).resolve().parent.parent
    # pre-rule artifacts, each covered by an ACCEPTED review surface
    # with its own regressions; enumerated so a NEW file is never
    # silently grandfathered
    GRANDFATHERED = {
        "check_spec_reference.py",   # the CI citation gate; its own
                                     # tests in this file predate P1
        "verify_extracted.py",       # the accepted C-plus extraction
                                     # surface (COLLECTED_HEADER_DESIGN)
        # pre-rule artifacts of ACCEPTED lines, pulled in when the glob
        # widened (0011 own campaign, 2026-08-28): 0020's package verifier
        # ships its own selftest (verify_package_selftest.py IS its
        # matrix), and the wheelset check is the offline launcher's
        # bootstrap guard with the launcher's own transcript as evidence
        "verify_package.py",
        "verify_package_selftest.py",
        "verify_wheelset.py",
    }
    # RECURSIVE on purpose (0011 own campaign): check_* under specs/evidence/
    # was OUTSIDE this domain, so two evidence checkers on a line the
    # reviewer was actively mutation-testing carried no matrix pointer and
    # nothing demanded one — the gate covered the artifacts nobody was
    # attacking and missed the ones under attack.
    # PROCESS-R6-1: the filename convention is a PROXY for "is a checker",
    # and subject_census.py — a validator that had already produced findings
    # in three consecutive rounds — sat outside it because of its name. The
    # convention stays for discovery, and this EXPLICIT registry carries the
    # checkers the convention cannot see; a checker added under any name
    # belongs here or under a matching name, and the reviewer's alternative
    # (a full registry replacing the convention) is the escalation path if
    # this list grows.
    EXPLICIT_ARTIFACTS = [
        root / "specs" / "evidence" / "0011" / "subject_census.py",
    ]
    for f in EXPLICIT_ARTIFACTS:
        assert f.exists(), f"EXPLICIT_ARTIFACTS names a missing file: {f}"
    candidates = sorted(
        list((root / "specs").rglob("check_*.py"))
        + list((root / "specs").rglob("verify_*.py"))
        + list((root / "specs").rglob("validate_*.py"))
        + EXPLICIT_ARTIFACTS)
    assert candidates, "the artifact domain is unexpectedly empty"
    for f in candidates:
        if f.name in GRANDFATHERED:
            continue
        text = f.read_text()
        m = re.search(r"^# Mutation-Matrix:\s*(tests/\S+?\.py)::(\w+)\s*$",
                      text, re.M)
        assert m, (
            f"{f.name} declares no `# Mutation-Matrix: tests/<file>.py::"
            f"<test>` pointer — no unmutated checker ships (P1)")
        tf, tname = m.group(1), m.group(2)
        problems = _p1_binding_problems(root, f, tf, tname)
        assert not problems, f"{f.name}: " + "; ".join(problems)

    # PROCESS-R23-1's planted mutant, as a self-test: a checker whose
    # pointer names an unrelated test, with the filename mentioned
    # ELSEWHERE in the test file, must refuse — the first gate searched
    # the whole file and passed it
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        troot = pathlib.Path(td)
        (troot / "specs").mkdir()
        (troot / "tests").mkdir()
        art = troot / "specs" / "check_planted.py"
        art.write_text("# Mutation-Matrix: tests/test_x.py::test_unrelated\n")
        (troot / "tests" / "test_x.py").write_text(
            "# check_planted.py is mentioned here, outside any test\n"
            "def test_unrelated():\n    assert True\n")
        probs = _p1_binding_problems(troot, art, "tests/test_x.py",
                                     "test_unrelated")
        assert probs, (
            "the planted unrelated-matrix mutant passed — the binding "
            "reads the file, not the test body (PROCESS-R23-1)")


def _p4_evidence_problem(evidence: str):
    """P4's grammar, PROCESS-R23-1 form: the evidence must INVOKE a
    named pytest test or a named specs/ script — `startswith("$PY")`
    blessed `$PY -c "pass"`, an inline no-op wearing the prefix."""
    import re
    e = evidence.strip()
    if re.match(r"\$PY\s+-m\s+pytest\s+tests/\S+::\w+", e):
        return None
    if re.match(r"\$PY\s+specs/[\w/.-]+\.py(\s|$)", e):
        return None
    return ("must invoke `$PY -m pytest tests/<file>::<test>` or "
            "`$PY specs/<script>.py`")


def test_new_closure_evidence_is_behavioral():
    """P4 (adopted 2026-08-24): closure evidence for NEW findings runs a
    named script or pytest test, never an inline lexical command — a
    grep for a diagnostic string is satisfied by a no-op artifact
    containing the string (EVIDENCE-R17-1, verbatim). DECLARED DOMAIN:
    rows BEYOND the per-line round cutoffs frozen at adoption; the
    historical rows keep their evidence as dispatched. Growing a cutoff
    is a visible diff, never silent."""
    import pathlib, sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import importlib
    import closure_findings
    importlib.reload(closure_findings)
    CUTOFFS = {
        ("0001", "external"): 10, ("0001", "internal"): 1,
        ("0022", "external"): 20, ("0022", "internal"): 21,
        ("0023", "external"): 6, ("0023", "internal"): 2,
        ("0024", "external"): 22,   # A1-R22-1 is the last pre-P4 row
        ("0025", "external"): 11,
        # 0011 and 0026 are DRAFTS — accepted-but-unimplemented is not their
        # state; they are not implemented at all. P4 exists because a grep
        # for a diagnostic string can be satisfied by a no-op artifact
        # CONTAINING that string, which is a real substitution when there is
        # behaviour the evidence could have run instead. For a spec whose
        # folds live only in its own text, the document IS the artifact and
        # reading it is the evidence, not a proxy for it.
        #
        # Bounded deliberately at the rounds that exist: internal 1-2 on each
        # line (0011's round 1 predates P4's 2026-08-24 adoption outright).
        # Round 3 onward is governed, and so is every external round — which
        # is where these specs are going next, and where behaviour will exist
        # to point at. Growing a cutoff is meant to be a visible diff.
        ("0011", "internal"): 2,
        ("0026", "internal"): 2,
        # 0031 (2026-09-04, the ledger written at acceptance after sixteen
        # rounds): rounds 1-4 folded SPEC TEXT — the lattice, the direct
        # bridge, the identity boundary, the digest minting, the retired
        # umbrella — before behaviour existed to point at; their text-only
        # closures cite the fold commit (`git show`), and their mechanism
        # closures already cite pytest nodes. Every round from 5 on is
        # governed and behavioral (the connection-acquisition ladder's
        # permanent batteries). Growing this is a visible diff.
        ("0031", "external"): 4,
    }
    # 0030 (2026-09-04, the joint arc's ledger written after acceptance):
    # its text-only closures are NOT prefix-shaped — design/prose findings
    # interleave with mechanism findings (round 1 entirely text: the
    # spec-designated tests do not exist because implementation is coupled
    # to acceptance; then R2 F1/F3/F7/F8 and R3 F5 beside mechanism rows in
    # the same rounds). A round cutoff would silently exempt every
    # mechanism finding in those rounds too. So: a PER-FINDING table,
    # finding id → reason, which keeps exactly the property the cutoff
    # bought (growing it is a visible diff) at finding grain. Every exempt
    # row must STILL cite an openable fold (`git show`), never prose —
    # tests/test_0030_closure_ledger.py holds that and the table's totality.
    TEXT_ONLY = {
        '0030-R1-1': 'both: [F1] The pair cannot reconstruct `EdgeStateAt(known_as_of)` — same-ID ',
        '0030-R1-2': 'both: [F2] Current trust and historical knowledge require two separate state',
        '0030-R1-3': '0029: [F3] 0029\'s event cuts can split an atomic mutation — a cutoff between',
        '0030-R1-4': '0029: [F4] V-TOTAL misses a shipped classification-relevant mutation — four ',
        '0030-R1-5': '0029: [F5] 0029\'s event schema remains unresolved — one `content_digest` col',
        '0030-R1-6': '0030: [F6] 0030\'s exact classifier still does not implement its input contra',
        '0030-R1-7': '0030: [F7] 0030 evaluates hidden records before applying visibility — a hidd',
        '0030-R1-8': '0030: [F8] 0030\'s prior fixes were not swept through every carrier — six rem',
        '0030-R2-1': '0029: [F1] migrated edges still lack reconstructable epoch state (no baselin',
        '0030-R2-3': '0030: [F3] current valid-time and semantic changes do not subtract (snapshot',
        '0030-R2-7': '0030: [F7] datetime normalization is not total (`as_utc(None) -> None` lets ',
        '0030-R2-8': 'both: [F8] 0029 \'digest-only\'/\'one digest\'/data-handling residue; 0030 unkno',
        '0030-R3-5': '0030: [F5] 0030 — the reason×cutoff matrix contradicts rule 8 and V-SUBTRACT',
    }
    offenders = []
    for row in closure_findings.CLOSURES:
        spec, kind, rnd, fid = row[0], row[1], row[2], row[3]
        evidence = row[6]
        if rnd <= CUTOFFS.get((spec, kind), 0):
            continue
        if fid in TEXT_ONLY and evidence.startswith("git show "):
            continue
        if _p4_evidence_problem(evidence):
            offenders.append(f"{spec} {kind} {rnd} {fid}: "
                             f"{_p4_evidence_problem(evidence)} — "
                             f"{evidence[:60]!r}")
    assert not offenders, (
        "closure evidence past the P4 cutoff must run a named script or "
        "pytest test, never an inline command:\n  "
        + "\n  ".join(offenders))

    # PROCESS-R23-1's planted mutant, as a self-test: `$PY -c "pass"`
    # starts with $PY and does nothing — the first gate's startswith
    # accepted it
    assert _p4_evidence_problem('$PY -c "pass"'), (
        "the planted $PY -c mutant passed (PROCESS-R23-1)")
    assert _p4_evidence_problem("$PY -m timeit 1+1"), (
        "a non-pytest -m module passed")
    assert not _p4_evidence_problem(
        "$PY -m pytest tests/test_x.py::test_y -q -p no:randomly"), (
        "a legitimate pytest invocation was refused")
    assert not _p4_evidence_problem("$PY specs/check_a1_carriers.py"), (
        "a legitimate named script was refused")


def test_the_lessons_taxonomy_is_total_and_its_counts_are_generated():
    """External round 15, R15-2. `specs/REVIEW_LESSONS.md` was hand-written: it
    said 39 external findings collapsed into six classes while the six headings
    summed to THIRTY — nine findings had no class and the prose could not show
    it — and it restated a suite duration three carriers in the same package
    measured at 16:45, 15:06 and 1:33.

    A count is a second copy of a list, and this was a count of a list nobody
    had written down. The list exists now (`MECHANISM`), the counts are
    rendered from it, and the drift gate below is what makes that true rather
    than intended. Every mutation the classification could suffer is injected:
    a finding with no class, a class naming a finding that does not exist, a
    class with nothing in it, and a document that has drifted from the source.
    The clean control runs last, because a validator that rejects everything
    passes all its rejection tests."""
    import pathlib, sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import review_lessons as rl

    real_mech, real_classes = rl.MECHANISM, rl.CLASSES
    try:
        # (a) A FINDING WITH NO CLASS — R15-2 itself. Nine of these were live
        # in the shipped document and the prose read as if they were covered.
        victim = sorted(real_mech)[0]
        rl.MECHANISM = {k: v for k, v in real_mech.items() if k != victim}
        problems = rl.validate()
        assert any("NOT classified" in p for p in problems), problems
        assert any(victim[2] in p for p in problems), (
            f"the unclassified finding {victim} must be NAMED, not counted: "
            f"{problems}")

        # (b) A CLASS NAMING A FINDING THAT DOES NOT EXIST — the same defect
        # mirrored: a renamed or deleted closure row leaves a classification
        # behind, and the count stays plausible.
        rl.MECHANISM = {**real_mech, ("0022", 99, "R99-1"): ("proxy", "packaging", "x")}
        assert any("matches no closure row" in p for p in rl.validate()), \
            rl.validate()

        # (c) A CLASS WITH NOTHING IN IT — a taxonomy grows classes to look
        # complete; an empty one is a claim about the world, not an
        # observation of it.
        rl.MECHANISM = real_mech
        rl.CLASSES = real_classes + (("phantom", "t", "r", "m"),)
        rl.CLASS_KEYS = tuple(k for k, *_ in rl.CLASSES)
        assert any("NO finding" in p for p in rl.validate()), rl.validate()
        rl.CLASSES, rl.CLASS_KEYS = real_classes, tuple(
            k for k, *_ in real_classes)

        # (d) AN UNDECLARED CLASS on an otherwise valid entry
        rl.MECHANISM = {**real_mech, victim: ("not-a-class", "packaging", "x")}
        assert any("undeclared class" in p for p in rl.validate()), rl.validate()

        # (e) A CLASSIFICATION WITH NO REASON — the reason is the part that
        # can be argued with; without it the table is an assertion again.
        rl.MECHANISM = {**real_mech, victim: (real_mech[victim][0], "packaging", "   ")}
        assert any("no reason" in p for p in rl.validate()), rl.validate()

        # (f) MALFORMED ENTRIES — R15-1's lesson applied to this module:
        # totality over the KEY SET is not totality. A key set that matches the
        # ledger exactly still admits a value of the wrong shape, and the
        # unpacking loop would then raise instead of reporting — a `--check`
        # gate that crashes has returned no verdict at all.
        for label, mutant in (
            ("a 4-tuple value",
             {**real_mech, victim: (real_mech[victim][0], "packaging", "why", "x")}),
            ("a bare string value", {**real_mech, victim: "domain"}),
            ("a stringified round in the key",
             {**real_mech, (victim[0], str(victim[1]), victim[2]):
              real_mech[victim]}),
        ):
            rl.MECHANISM = mutant
            ps = rl.validate()
            assert ps and any("not (" in p for p in ps), f"{label}: {ps}"

        # and the class rows themselves, at their own level
        rl.MECHANISM = real_mech
        rl.CLASSES = real_classes[:-1] + (("key", "title", "rule"),)
        rl.CLASS_KEYS = tuple(k for k, *_ in rl.CLASSES)
        assert any("class row" in p for p in rl.validate()), rl.validate()
        rl.CLASSES, rl.CLASS_KEYS = real_classes, tuple(
            k for k, *_ in real_classes)
    finally:
        rl.MECHANISM, rl.CLASSES = real_mech, real_classes
        rl.CLASS_KEYS = tuple(k for k, *_ in real_classes)

    # (f) THE DOCUMENT ITSELF — total classification is worth nothing if the
    # shipped block is a stale copy of it. This is the assertion that makes
    # the counts generated rather than merely generatable.
    assert not rl.validate(), rl.validate()
    text = rl.DOC.read_text()
    assert rl.BEGIN in text and rl.END in text, "the generated block is gone"
    shipped = text.split(rl.BEGIN, 1)[1].split(rl.END, 1)[0]
    assert shipped.strip() == rl.render().strip(), (
        "specs/REVIEW_LESSONS.md has drifted from specs/review_lessons.py — "
        "regenerate with `python3 specs/review_lessons.py --write`")

    # and the CLEAN control: the real classification passes, so the gate is
    # not passing by rejecting everything
    assert rl.main(["review_lessons.py", "--check"]) == 0


def test_one_generated_block_verifier_refuses_every_marker_mutation():
    """External round 16, R16-2. `review_lessons.py` located its block with
    `split(BEGIN, 1)` — the FIRST marker pair, with nothing requiring there be
    only one — so an appended second block claiming "999 external findings"
    passed `--check`, the dedicated gate, and full archive verification after
    repacking.

    The defect is not that the parsing was weak. THE STRICT RULE ALREADY
    EXISTED IN THIS REPO: `skip_inventory.verify_collected`, written for 0014's
    round-15 finding, where `split(begin, 1)` accepted exactly this mutation.
    I wrote a second, weaker copy of a verifier that already existed, and the
    copy carried the bug the original was written to fix. An implementation is
    a second copy of a rule and it goes stale the same way a count does.

    So this exercises the ONE implementation both carriers now call, over the
    full mutation domain rather than the mutation that was reported."""
    import pathlib, sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import generated_block as gb

    B, E = "<!-- B -->", "<!-- /B -->"
    body = "one\ntwo"
    good = f"prose\n{B}\n{body}\n{E}\ntail\n"
    gb.verify(good, B, E, body, at_start=False)                    # the CLEAN control, first

    for label, text in (
        ("a duplicated complete block — the reviewer's mutation",
         good + f"{B}\n999 findings\n{E}\n"),
        ("a second OPENING marker only", good + f"{B}\n"),
        ("a second CLOSING marker only", good + f"{E}\n"),
        ("no markers at all", "prose\n"),
        ("the opening marker missing", f"prose\n{body}\n{E}\n"),
        ("the closing marker missing", f"prose\n{B}\n{body}\n"),
        ("end before begin", f"{E}\n{body}\n{B}\n"),
    ):
        with pytest.raises(gb.BlockError):
            gb.verify(text, B, E, body, at_start=False)
        # and the WRITE path must refuse too — regenerating the first block of
        # a duplicated carrier leaves the second one lying, which is how the
        # reviewer's mutation would have survived a `--write`
        with pytest.raises(gb.BlockError):
            gb.replace(text, B, E, body, at_start=False)

    # R19-2: THE ANCHOR, both directions. A carrier that must start at the
    # marker refuses anything above it; one that legitimately carries a header
    # (COLLECTED) must still pass. Neither is a default — both call sites state
    # their policy, because the unstated one is what shipped.
    anchored = f"{B}\n{body}\n{E}\ntail\n"
    gb.verify(anchored, B, E, body, at_start=True)
    for label, text in (("a prepended title", "# What 9999 rounds\n" + anchored),
                        ("a prepended blank line", "\n" + anchored)):
        with pytest.raises(gb.BlockError):
            gb.verify(text, B, E, body, at_start=True)
        # the SAME text is fine for an unanchored carrier — the anchor is the
        # only thing being tested here, not the marker rules
        gb.verify(text, B, E, body, at_start=False)

    # and indenting the marker breaks it for BOTH policies, because it is no
    # longer a standalone line — a different rule, asserted as a different case
    for policy in (True, False):
        with pytest.raises(gb.BlockError):
            gb.verify(" " + anchored, B, E, body, at_start=policy)

    # MARKERS COUNT ONLY AS STANDALONE LINES: prose that mentions one is prose.
    # (Mention-versus-use, which this review has produced seven times.)
    mentioned = f"prose about {B} inline\n{B}\n{body}\n{E}\n"
    gb.verify(mentioned, B, E, body, at_start=False)

    # CONTENT, with no normalization: a boundary newline is a difference
    for label, text in (
        ("stale content", f"{B}\nSTALE\n{E}\n"),
        ("a boundary newline after the opening marker",
         f"{B}\n\n{body}\n{E}\n"),
        ("a boundary newline before the closing marker",
         f"{B}\n{body}\n\n{E}\n"),
    ):
        with pytest.raises(gb.BlockError):
            gb.verify(text, B, E, body, at_start=False)

    # BOTH CARRIERS CALL IT — the point of the fix is that there is no second
    # copy left to drift. Checked by behaviour: each refuses the duplicate.
    import review_lessons as rl
    from skip_inventory import BEGIN_MARKER, END_MARKER, verify_collected
    dup = rl.DOC.read_text() + f"\n{rl.BEGIN}\n\n**999 external findings.**\n\n{rl.END}\n"
    with pytest.raises(gb.BlockError):
        gb.verify(dup, rl.BEGIN, rl.END, "\n" + rl.render() + "\n",
                  at_start=True)
    with pytest.raises(ValueError):     # BlockError subclasses ValueError
        verify_collected(f"{BEGIN_MARKER}\nx\n{END_MARKER}\n{BEGIN_MARKER}\ny\n{END_MARKER}\n")


def test_the_packages_three_identity_carriers_must_agree():
    """External round 16, R16-1. The archive was named v16 while both shipped
    carriers said v15 / ROUND 15: `build_collected(..., version, ...)` received
    the requested version and never used it, so `--version` controlled the
    FILENAME alone and the identity line a reviewer reads first came from a
    hand-edited template.

    Round 4 made the two carriers agree about the COMMIT. Nothing made them
    agree about WHICH PACKAGE THEY ARE. Identity has three carriers here, so
    every one-carrier disagreement is injected below, plus the agreeing
    control — and the templates are asserted to be tokenized, because a
    template that carries a literal version is the defect itself."""
    import pathlib, re, sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    from seal_package import identity_problems

    # R17-1 made the identity record the source of the packaged revisions, so
    # the fixtures are built from the GOVERNED package rather than pinned to
    # the round this test was written in — a fixture that names a version the
    # record no longer governs tests nothing about today's seal.
    import package_identity as pid
    LINE = "0022-0023"           # the fixtures below are written in this
    #                              line's names; the record went per-line when
    #                              the 0024-0025 send opened a second line
    V = max(pid.PACKAGES[LINE], key=lambda v: int(v[1:]))
    MEMBERS = {"./" + m for m in re.findall(
        r"(specs/\S+\.md) — [a-z][a-z -]* v", pid.render_candidate_lines(LINE, V))}
    RND = pid.PACKAGES[LINE][V][0]
    STALE = f"v{RND - 1}"
    NAME = f"0022-0023-{V}-20260819T0136Z.tar.gz"
    COL = (f"0022 source revocation (A3a) + 0023 non-revival (A3b) — COUPLED "
           f"round-{RND} external-review package ({V})\nsource commit: abc1234\n"
           f"{pid.render_candidate_field(LINE, V)}\n")
    MAN = f"PACKAGE: 0022-0023-{V} — external ROUND {RND}\nCOMMIT:  abc1234\n"
    assert identity_problems(NAME, COL, MAN, MEMBERS) == [], (
        f"the agreeing case must pass: {identity_problems(NAME, COL, MAN, MEMBERS)}")

    # ONE CARRIER WRONG AT A TIME — including the exact shipped defect
    for label, name, col, man in (
        ("the archive shipped with the PREVIOUS round's carriers (R16-1)",
         NAME, COL.replace(f"round-{RND}", f"round-{RND - 1}").replace(f"({V})", f"({STALE})"),
         MAN.replace(V, STALE).replace(f"ROUND {RND}", f"ROUND {RND - 1}")),
        ("the manifest alone is stale", NAME, COL,
         MAN.replace(V, STALE).replace(f"ROUND {RND}", f"ROUND {RND - 1}")),
        ("the COLLECTED header alone is stale", NAME,
         COL.replace(f"round-{RND}", f"round-{RND - 1}").replace(f"({V})", f"({STALE})"), MAN),
        ("the archive alone is renamed",
         f"0022-0023-v{RND + 1}-20260819T0136Z.tar.gz", COL, MAN),
        ("the round disagrees with the version", NAME,
         COL.replace(f"round-{RND}", f"round-{RND - 1}"), MAN),
        ("the manifest names a different SPEC SET", NAME, COL,
         MAN.replace(f"0022-0023-{V}", f"0022-0099-{V}")),
        ("the manifest has no identity line", NAME, COL, "COMMIT: abc1234\n"),
        ("COLLECTED has no identity line", NAME, "source commit: abc1234\n", MAN),
        ("the archive name carries no version",
         "0022-0023-20260819T0136Z.tar.gz", COL, MAN),
    ):
        assert identity_problems(name, col, man, MEMBERS), f"ACCEPTED: {label}"

    # THE TEMPLATES MUST BE TOKENIZED. Substitution is what makes the identity
    # produced rather than typed, and `refuse_placeholders` already fails the
    # seal on any token that survives — so the only way back to R16-1 is a
    # template with a literal version in it again.
    for rel in ("specs/package/collected_header.txt", "specs/package/manifest.txt"):
        head = (root / rel).read_text().split("\n")[0]
        assert not re.search(r"\bv\d+\b|ROUND\s+\d+|round-\d+", head), (
            f"{rel} carries a LITERAL version/round in its identity line "
            f"({head!r}) — it must be __VERSION__/__ROUND__/__PACKAGE__ and "
            f"substituted at seal (R16-1)")
        assert re.search(r"__(VERSION|ROUND|PACKAGE)__", head), (
            f"{rel} names no identity token")


def test_the_whole_lessons_summary_is_byte_verified_by_check():
    """External round 18, R18-2. The summary above the table was hand-written
    prose guarded by a pytest heuristic that hunted for cardinal words and
    digits. Two things were wrong with that.

    It lived only in this file, so `review_lessons.py --check` — the command
    the ARCHIVE VERIFIER runs, and the only check a reviewer's extraction
    exercises — never saw it. And detecting quantities in natural language is a
    PROXY for the property that matters: the scrubber dropped every four-digit
    number as though all of them were spec ids, so "has not moved in 9999
    rounds" read as clean and both checks passed.

    A proxy for "this prose is what the generator says" is unnecessary when the
    generator can just say it. The whole summary — title, prologue, table,
    derived paragraphs — is generated and byte-verified now, so ANY edit fails,
    quantitative or not, in the tree and in the extraction alike."""
    import pathlib, sys, tempfile
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import review_lessons as rl

    rendered = rl.render()
    assert rendered.lstrip().startswith("# "), (
        "the TITLE is outside the generated region — it carried a stale count "
        "once already")
    assert "Spec-Status:" in rendered and "## The classes" in rendered, (
        "the prologue is outside the generated region")

    original = rl.DOC.read_text()
    assert rl.main(["review_lessons.py", "--check"]) == 0, "the clean control"

    # EVERY MUTATION BELOW RUNS ON A COPY, never on the shipped document.
    #
    # It used to edit specs/REVIEW_LESSONS.md in place and restore it in a
    # `finally`, which was safe only because nothing else ran at the same time.
    # When the evidence runner became concurrent, this test and the evidence
    # command `$PY specs/review_lessons.py --check` began racing over the same
    # file — one mutating it, the other reading it — and CI failed on exactly
    # that pair (R15-2 and R19-2) in two of five jobs. Class 5 again: a check
    # reading an artifact another check is producing. The fix is not to
    # serialize them; it is to stop sharing the file.
    #
    # It also removes a worse failure mode: a process killed mid-test used to
    # leave a tracked file mutated on disk.

    # THE REVIEWER'S MUTATION, and it must be `--check` that refuses it — not a
    # test, because a test does not ship inside the archive.
    for label, mutant in (
        ("a quantitative sentence inserted mid-prologue",
         original.replace("The findings are not a pile",
                          "The design has not moved in 9999 rounds.\n\nThe "
                          "findings are not a pile", 1)),
        ("a word-form quantity, R17-2's original defect",
         original.replace("The findings are not a pile",
                          "The design has not moved in eight rounds.\n\nThe "
                          "findings are not a pile", 1)),
        ("the title edited", original.replace(
            "# What the external review", "# What fifteen rounds", 1)),
        # R19-2: everything BETWEEN the markers was verified and the text
        # BEFORE the opening marker was not, so a prepended markdown title
        # became the document's title while every check passed. Verifying the
        # block is not verifying the document.
        ("a title PREPENDED above the opening marker",
         "# What 9999 rounds actually found\n\n" + original),
        ("a single blank line prepended", "\n" + original),
        ("a table row edited", original.replace("| 1 | **self-assertion**",
                                                "| 1 | **self-assertions**", 1)),
        ("a derived paragraph edited",
         original.replace("The last finding that required a change",
                          "The last finding that required no change", 1)),
    ):
        assert mutant != original, f"{label}: the mutation did not apply"
        real_doc = rl.DOC
        with tempfile.TemporaryDirectory() as td:
            copy = pathlib.Path(td) / "REVIEW_LESSONS.md"
            copy.write_text(mutant)
            rl.DOC = copy
            try:
                assert rl.main(["review_lessons.py", "--check"]) == 1, (
                    f"--check ACCEPTED {label} — the summary is not "
                    f"byte-verified, which is R18-2")
            finally:
                rl.DOC = real_doc

    assert rl.DOC.read_text() == original, (
        "the shipped document was modified by this test")
    assert rl.main(["review_lessons.py", "--check"]) == 0


def test_the_package_identity_record_governs_every_candidate_carrier():
    """External round 17, R17-1. Round 16 made the package version PRODUCED and
    enumerated three carriers of it. There were five: COLLECTED lines 6-7 name
    each specification's own candidate revision, and those were still template
    literals — so the v17 package shipped saying `draft v16` for both specs
    while its SENT rows described them as v18, and identity verification found
    nothing wrong because it read only the carriers the previous finding had
    named.

    Enumerating the carriers a reviewer NAMED is not enumerating the carrier
    domain. Identity is structured data now, and every carrier is filled from
    it and checked against it."""
    import pathlib, re, sys
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import package_identity as pid
    from seal_package import identity_problems

    assert pid.validate() == [], pid.validate()

    # R19-1: the member set is REQUIRED, and derived from the record's own
    # rendered paths so the fixture cannot drift from what the generator emits.
    def _members(v):
        return {"./" + m for m in re.findall(
            r"(specs/\S+\.md) — [a-z][a-z -]* v",
            pid.render_candidate_lines("0022-0023", v))}

    LINE = "0022-0023"
    version = max(pid.PACKAGES[LINE], key=lambda v: int(v[1:]))
    MEMBERS = _members(version)
    rnd, cands = pid.PACKAGES[LINE][version]
    specs = "-".join(sorted(cands))
    name = f"{specs}-{version}-20260819T0000Z.tar.gz"
    col = (f"0022 source revocation (A3a) + 0023 non-revival (A3b) — COUPLED "
           f"round-{rnd} external-review package ({version})\n"
           f"source commit: abc1234\n"
           f"{pid.render_candidate_field(LINE, version)}\n")
    man = f"PACKAGE: {specs}-{version} — external ROUND {rnd}\nCOMMIT: abc1234\n"
    assert identity_problems(name, col, man, MEMBERS) == [], (
        f"the agreeing package is refused: {identity_problems(name, col, man, MEMBERS)}")

    # ONE DRAFT LINE AT A TIME — the reviewer's required regression. Each spec's
    # own revision is an identity carrier, so each must be able to fail alone.
    for spec, rev in sorted(cands.items()):
        stale = col.replace(f"{spec}-", f"{spec}-", 1)
        # PACKAGE-R13-1: the status word is DERIVED from Spec-Status now,
        # so the mutation matches any status, not the old draft literal
        stale = re.sub(rf"(specs/{spec}-\S+\.md — [a-z][a-z -]* )v\d+",
                       r"\g<1>v1", col)
        assert stale != col, f"could not mutate {spec}'s candidate line"
        assert identity_problems(name, stale, man, MEMBERS), (
            f"a stale `draft vN` on {spec} ALONE was accepted — R17-1 exactly")

    # and the whole block missing, and a package with no identity row
    assert identity_problems(name, col.split("specs:")[0], man, MEMBERS)

    # EXTERNAL ROUND 20, R20-1: THE FIELD IS THE CARRIER, AND WHERE IT SITS
    # IS PART OF IT. The check asked whether the rendered block occurred
    # ANYWHERE in COLLECTED, so a package could answer `specs: none — this
    # package has no external candidates` on the line a reviewer reads and
    # carry the correct block further down; the contradiction passed every
    # check and the repacked archive verified clean. Presence somewhere
    # stood in for the field's value — the proxy class one level up from
    # where R19-1 closed it.
    import skip_inventory as _si
    field = pid.render_candidate_field(LINE, version)
    lines = pid.render_candidate_lines(LINE, version)
    lie = "specs: none — this package has no external candidates"
    body = f"{_si.BEGIN_MARKER}\ninventory\n{_si.END_MARKER}\n"
    anchored = col + body
    assert identity_problems(name, anchored, man, MEMBERS) == [], (
        "the anchored control must pass: "
        f"{identity_problems(name, anchored, man, MEMBERS)}")
    for label, mutant in (
        ("the reviewer's reproducer: a LIE in the field, the correct "
         "lines appended after the inventory block",
         anchored.replace(field, lie) + lines + "\n"),
        ("a lie in the field, a whole second FIELD appended below",
         anchored.replace(field, lie) + field + "\n"),
        ("the field relocated below the inventory block",
         anchored.replace(field + "\n", "") + field + "\n"),
        ("two specs: fields", anchored + field + "\n"),
        ("the field replaced by a plausible lie", anchored.replace(field, lie)),
    ):
        assert mutant != anchored, f"{label}: the mutation did not apply"
        assert identity_problems(name, mutant, man, MEMBERS), (
            f"ACCEPTED {label} — R20-1")

    assert identity_problems(name.replace(version, "v999"),
                             col.replace(version, "v999"),
                             man.replace(version, "v999"), MEMBERS)

    # EXTERNAL ROUND 18, R18-1: three mutations the record accepted, kept here
    # because each one is a different way for a "structured" record to be
    # untotal over the domain it claims.
    #
    # (b) A DUPLICATE CARRIER. The candidate lines were read with
    # `dict(re.findall(...))`, so a PREPENDED conflicting line collapsed and the
    # later correct value won — R14-1's mechanism (a duplicate vanishing into a
    # set) inside a check written after R14-1.
    dup = col.replace(
        pid.LABEL,
        pid.LABEL + "specs/0022-source-revocation.md — draft v999 "
        "(external candidate)\n" + pid.INDENT, 1)
    assert dup != col
    assert identity_problems(name, dup, man, MEMBERS), (
        "a carrier stating one spec's revision TWICE, with different values, "
        "was accepted — R18-1")

    # (c) CONTINUITY FROM THE BOUND. `FIRST_GOVERNED` was enforced and the run
    # from it was not, so deleting the oldest governed row left the record
    # valid while a governed package went undeclared. A bound is not a domain.
    saved = {k: dict(v) for k, v in pid.PACKAGES.items()}
    try:
        if len(pid.PACKAGES[LINE]) > 1:
            pid.PACKAGES[LINE].pop(f"v{pid.FIRST_GOVERNED[LINE]}")
            assert any("contiguous" in x for x in pid.validate()), (
                f"a gap at the bottom of the governed run was accepted: "
                f"{pid.validate()}")
        pid.PACKAGES.clear()
        pid.PACKAGES.update({k: dict(v) for k, v in saved.items()})
        _top = max(int(v[1:]) for v in saved[LINE])
        pid.PACKAGES[LINE][f"v{_top + 2}"] = (
            _top + 2, {"0022": "v1", "0023": "v1"})
        assert any("contiguous" in x for x in pid.validate()), (
            "a HOLE in the governed run was accepted")
    finally:
        pid.PACKAGES.clear()
        pid.PACKAGES.update({k: dict(v) for k, v in saved.items()})
    assert pid.validate() == [], pid.validate()

    # (a) THE SENT PROSE IS A SECOND COPY of the candidate revisions, and it was
    # unchecked: a row could say `0022 at v999` beside a record saying v19 and
    # validate() returned clean, because it only asked whether the row NAMED
    # the package and the round.
    import reviews
    real = [dict(r) for r in reviews.REVIEWS]
    real_reviews = pid._reviews
    try:
        pid._reviews = lambda: reviews.REVIEWS
        hit = 0
        for r in reviews.REVIEWS:
            if (r["kind"] == "external" and r["verdict"].startswith("SENT")
                    and f"0022-0023-{version}" in r["verdict"]
                    and re.search(r"\b0022 at v\d+", r["verdict"])):
                r["verdict"] = re.sub(r"\b0022 at v\d+", "0022 at v999",
                                      r["verdict"])
                hit += 1
        assert hit, "no SENT row carries a candidate claim to mutate"
        assert any("second copy" in x for x in pid.validate()), (
            f"a SENT row contradicting the identity record was accepted: "
            f"{pid.validate()}")
    finally:
        reviews.REVIEWS[:] = real
        pid._reviews = real_reviews
    assert pid.validate() == [], pid.validate()

    # EXTERNAL ROUND 19, R19-1: THE PATH IS PART OF THE IDENTITY. The check
    # extracted the four-digit spec id and the revision from each candidate
    # line and compared only those, so renaming the PATH kept both correct and
    # every identity check passed — COLLECTED could point the reviewer at a
    # file that does not exist. The fields I chose to extract stood in for the
    # artifact; the block is compared byte for byte against the generator now.
    renamed = col.replace("specs/0022-source-revocation.md",
                          "specs/0022-not-the-shipped-spec.md")
    assert renamed != col
    assert identity_problems(name, renamed, man, MEMBERS), (
        "a renamed candidate PATH with the right id and revision was accepted "
        "— R19-1 exactly")

    # and a path the archive does not carry, which a byte-perfect block cannot
    # rule out on its own
    assert identity_problems(name, col, man, set()), (
        "a candidate path that is not an archive member was accepted (R19-1)")
    for drop in sorted(MEMBERS):
        assert identity_problems(name, col, man, MEMBERS - {drop}), (
            f"a package missing {drop} was accepted (R19-1)")

    # a candidate line OUTSIDE the verified block: the block matching exactly
    # says nothing about what else the carrier says
    stray = col + ("\n" + pid.INDENT + "specs/0022-source-revocation.md — "
                   "draft v99 (external candidate)\n")
    assert identity_problems(name, stray, man, MEMBERS), (
        "a second candidate line outside the block was accepted")

    # THE TEMPLATE MUST NOT CARRY THE LITERALS AGAIN
    header = (root / "specs" / "package" / "collected_header.txt").read_text()
    assert "__CANDIDATES__" in header, (
        "collected_header.txt must fill its candidate field from the identity "
        "record, not carry `draft vN` literals (R17-1)")
    assert "specs:" not in header, (
        "collected_header.txt still carries the `specs:` LABEL — the label and "
        "the lines must be ONE rendered field, or verification can only ask "
        "whether the lines appear somewhere (R20-1)")
    assert not re.search(r"draft v\d+", header), (
        "collected_header.txt carries a literal `draft vN` — that is the "
        "defect, restored")


def test_a_repacked_archive_with_a_relocated_candidate_field_is_refused(capsys):
    """External round 20, R20-1, at the ARCHIVE level — the reviewer asked for
    both a pure-function and a full-repack regression, because the pure
    function is not what shipped: `verify_archive` is.

    The reviewer built a contradictory package — `specs: none ...` on the
    reviewer-facing line, the correct candidate lines appended lower down — and
    the complete extracted-archive verifier accepted it. This repacks the most
    recent sealed archive with that same mutation and requires the verifier to
    REFUSE.

    It skips when no archive is present (they are gitignored, so a clone has
    none), which is the inventoried `no archives present` condition."""
    import pathlib, re, sys, tarfile, tempfile
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import package_identity as pid
    import seal_package as sp

    archives = sorted((root / "specs" / "archives").glob("*.tar.gz"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    if not archives:
        pytest.skip("no archives present (they are gitignored; a clone has none)")
    src = archives[0]
    m = re.match(r".+-(v\d+)-\d{8}T\d{4}Z\.tar\.gz$", src.name)
    if not m or m.group(1) not in pid.PACKAGES:
        pytest.skip("the newest archive predates the identity record's domain")
    version = m.group(1)

    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td)
        with tarfile.open(src) as tf:
            tf.extractall(d / "x")
        col_path = d / "x" / "COLLECTED.txt"
        col = col_path.read_text()
        field = pid.render_candidate_field(LINE, version)
        assert field in col, (
            "the sealed archive does not carry the rendered candidate field — "
            "this test would otherwise pass by mutating nothing")

        # THE REVIEWER'S EXACT MUTATION
        lie = "specs: none — this package has no external candidates"
        col_path.write_text(col.replace(field, lie)
                            + pid.render_candidate_lines(version) + "\n")

        repacked = d / src.name
        with tarfile.open(repacked, "w:gz") as tf:
            # FILES ONLY, and non-recursive. Adding directories as well made
            # every child appear twice, so verify_archive refused for
            # `duplicate members` and this test passed WITHOUT the identity
            # check ever running — which is precisely why the refusal reason is
            # asserted below rather than just the refusal.
            for f in sorted((d / "x").rglob("*")):
                if f.is_file():
                    tf.add(f, arcname="./" + str(f.relative_to(d / "x")),
                           recursive=False)

        # the UNMUTATED carriers must pass the same check, or this test could
        # be satisfied by an archive that was already broken. (The control is
        # the pure function, not a second verify_archive: a clean run executes
        # nine extraction subprocesses, and the identity refusal below happens
        # before any of them.)
        man = (d / "x" / "PACKAGE_MANIFEST.txt").read_text()
        with tarfile.open(src) as tf:
            members = set(tf.getnames())
        assert sp.identity_problems(src.name, col, man, members) == [], (
            "the sealed archive's own carriers do not verify — this test would "
            "then prove nothing about the mutation")

        with pytest.raises(SystemExit):
            sp.verify_archive(repacked, ["0022", "0023"])
        # AND FOR THE RIGHT REASON: a seal can abort for many reasons, and a
        # test that accepts any of them would pass while the identity check
        # slept.
        refusal = capsys.readouterr().err
        assert "R20-1" in refusal or "specs:" in refusal, (
            f"the archive was refused, but not by the identity check: "
            f"{refusal[-400:]}")


def test_changed_from_previous_orders_numerically_and_skips_same_version():
    """0025 round 10, R10-2; reshaped round 11, PACKAGE-R11-1. The
    lexicographic selector would diff v11 against v9 and could pick a
    same-version predecessor. Round 11: the SELECTION is a pure helper
    with no git call, so this regression runs in an EXTRACTED review
    package too — the v11 form invoked `git archive` and crashed with
    tarfile.ReadError exactly there, taking the closure-evidence gate
    with it."""
    import sys, tempfile, pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "specs"))
    import seal_package

    with tempfile.TemporaryDirectory() as td:
        outbox = pathlib.Path(td)
        for n in ("0024-0025-v9-20260821T2210Z.tar.gz",
                  "0024-0025-v10-20260821T2249Z.tar.gz",
                  "0024-0025-v11-20260821T2300Z.tar.gz"):
            (outbox / n).write_bytes(b"placeholder")   # selection reads NAMES
        pick = seal_package._select_prior_archive
        # a v11 seal must pick v10 numerically — not v9 lexicographically —
        # and must EXCLUDE the existing v11 (the same-version reseal case)
        assert pick("0024-0025", "v11", outbox).name.startswith(
            "0024-0025-v10-")
        assert pick("0024-0025", "v12", outbox).name.startswith(
            "0024-0025-v11-")
        # no prior below the current version: None, which the caller turns
        # into the NAMED skip
        assert pick("0024-0025", "v9", outbox) is None
        # a malformed name never matches
        (outbox / "0024-0025-vX-garbage.tar.gz").write_bytes(b"x")
        assert pick("0024-0025", "v12", outbox).name.startswith(
            "0024-0025-v11-")


def test_citation_version_matches_the_released_version():
    """CITATION.cff sat at 0.2.4 through eleven releases — GitHub renders
    it, so every citation carried the wrong version, and the Aug-1 TASKS
    reconciliation had marked it done on PRESENCE alone. A rendered second
    copy of the version needs a gate: this binds it to pyproject's, so a
    release bump that forgets the citation fails the suite instead of
    shipping."""
    import pathlib, re
    root = pathlib.Path(__file__).resolve().parent.parent
    pyproject = (root / "pyproject.toml").read_text()
    released = re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1)
    citation = (root / "CITATION.cff").read_text()
    cited = re.search(r"^version: (\S+)$", citation, re.M).group(1)
    assert cited == released, (
        f"CITATION.cff says {cited}, pyproject says {released} — the "
        f"citation is rendered by GitHub and must move with the release")
