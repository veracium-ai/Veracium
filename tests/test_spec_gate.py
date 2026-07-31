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
        for f in ("src/veracium/graph.py", "src/veracium/gate.py",
                  "specs/0007-thing.md", "README.md"):
            p = path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("original\n")
        self._run("git", "add", "-A")
        self._run("git", "commit", "-qm", "seed")
        self.base = self._out("git", "rev-parse", "HEAD").strip()

    def _run(self, *a):
        return subprocess.run(a, cwd=self.path, check=True, capture_output=True,
                              text=True)

    def _out(self, *a):
        return subprocess.run(a, cwd=self.path, capture_output=True,
                              text=True).stdout

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
        r = subprocess.run([sys.executable, str(CHECK), rng or f"{self.base}..HEAD",
                            *extra], cwd=self.path, capture_output=True, text=True)
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
    """A noisy gate gets bypassed; docs and the wiki compiler are excluded on
    purpose."""
    code, _ = repo.commit("docs",
                          touch=["README.md", "src/veracium/compile.py"]).check()
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
