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
    `src/veracium/` today. 0022 and 0023 are drafts, and this repo's own gate
    refuses any `src/` commit citing a non-accepted spec, so a test that binds
    the shipped construction to shipped store code cannot test behaviour that
    has not been written.

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
        specs = root / "specs"
        for name in ("0022-source-revocation.md",
                     "0023-non-revival-under-maintenance.md"):
            status = re.search(r"^Spec-Status:\s*(\S+)",
                               (specs / name).read_text(), re.M).group(1)
            assert status != "accepted", (
                name + " is ACCEPTED but no source_revocations writer exists in "
                "the store — either the implementation is missing or this "
                "binding test needs its real assertions turned on")
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
