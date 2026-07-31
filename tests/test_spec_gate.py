"""The spec-reference gate is itself a postcondition check, so it needs one.

PROCESS.md §6 says an invariant with no executable check does not count. That
applies to the checker: a guard that silently passes everything looks identical
to a clean repository.
"""

import subprocess
import sys
from pathlib import Path

CHECK = Path(__file__).resolve().parents[1] / "specs" / "check_spec_reference.py"


def _repo(tmp_path, files, message):
    """A throwaway git repo with one commit touching `files`."""
    run = lambda *a: subprocess.run(a, cwd=tmp_path, check=True,
                                    capture_output=True, text=True)
    run("git", "init", "-q")
    run("git", "config", "user.email", "t@example.com")
    run("git", "config", "user.name", "t")
    (tmp_path / "seed").write_text("x")
    run("git", "add", "seed"); run("git", "commit", "-qm", "seed")
    base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path,
                          capture_output=True, text=True).stdout.strip()
    for f in files:
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("changed")
    run("git", "add", "-A"); run("git", "commit", "-qm", message)
    return subprocess.run([sys.executable, str(CHECK), f"{base}..HEAD"],
                          cwd=tmp_path, capture_output=True, text=True)


def test_trust_surface_change_without_a_spec_fails(tmp_path):
    r = _repo(tmp_path, ["src/veracium/graph.py"], "change supersession")
    assert r.returncode == 1
    assert "graph.py" in r.stderr


def test_spec_trailer_satisfies_the_gate(tmp_path):
    r = _repo(tmp_path, ["src/veracium/graph.py"],
              "change supersession\n\nSpec: specs/0007-thing.md")
    assert r.returncode == 0


def test_exemption_is_allowed_and_recorded(tmp_path):
    """The hotfix carve-out must work — a process that cannot ship a security
    fix first is one people route around — and must land in the history."""
    r = _repo(tmp_path, ["src/veracium/gate.py"],
              "urgent fix\n\nSpec: none (hotfix — GHSA-x, retrospective review)")
    assert r.returncode == 0
    assert "hotfix" in r.stdout


def test_unguarded_files_do_not_trip_the_gate(tmp_path):
    """A noisy gate gets bypassed; docs and the wiki compiler are excluded on
    purpose."""
    r = _repo(tmp_path, ["README.md", "src/veracium/compile.py"], "docs + wiki view")
    assert r.returncode == 0


def test_the_surfaces_review_added_are_actually_guarded(tmp_path):
    """These three were missed by the first list: the trust verbs, the
    active_only default every caller depends on, and the briefing that reaches
    model context with no user turn."""
    for f in ("src/veracium/__init__.py", "src/veracium/store/sqlite.py",
              "src/veracium/proactive.py", "src/veracium/introspect.py"):
        d = tmp_path / f.replace("/", "_")
        d.mkdir()
        r = _repo(d, [f], "change trust behaviour")
        assert r.returncode == 1, f"{f} is not guarded"
