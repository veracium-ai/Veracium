"""0007 §4g.6 4d and v19: the attestation-record writer (specs/attestation_writer.py), I4's writer side.

The record's key is this process's own; one validator both directions and a read-back round trip; fixture marks
refused; v19's cross-run order arm by arm, each refusal asserting its MESSAGE, driven through an injectable git and
grounded by REAL temporary repositories (an ancestor, an older commit, a sibling branch, a file:// shallow clone, an
unknown commit's exit 128); the record's commit must be the checkout's HEAD; git's environment pinned; merge over the
full key; atomic publication over a closed top level.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("veracium_attestation_writer", ROOT / "specs" / "attestation_writer.py")
aw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aw)
sv = aw.sv

OTHER_MACHINE = "ppc64le" if sv.canonical_platform()["machine"] == "riscv64" else "riscv64"
"""A canonical machine that is NOT this build's (0007 CI run 1, 2026-10-27): "another key" made with a fixed
`aarch64` was this build's own key on arm64 runners, and `libc="musl"` was non-canonical beside Darwin, so cells meant
to hold two keys held one, or a malformed record, off x86_64 Linux."""


A = "a" * 40
B = "b" * 40


def evidence(digest="e" * 64):
    return digest, {k: True for k in sv.CONFINEMENT_PROBE_KEYS}


def record(commit=A, digest="e" * 64, **over):
    d, c = evidence(digest)
    r = aw.build_record(d, c, [{"route": "setup-python", "runner_image": "ubuntu-24.04", "run_id": "1",
                                 "job_id": 1, "commit": commit}])
    r.update(over)
    return r


def fake_git(head=A, shallow="false", fmt="sha1", inside="true", ancestor=None, version_rc=0):
    """An injectable git: `ancestor` maps (old, new) to --is-ancestor's exit code."""
    ancestor = ancestor or {}

    def git(args, repo):
        if args == ["--version"]:
            return version_rc, "git version 2.43.0"
        if args == ["rev-parse", "--is-inside-work-tree"]:
            return (0, inside) if inside is not None else (128, "")
        if args == ["rev-parse", "--is-shallow-repository"]:
            return 0, shallow
        if args == ["rev-parse", "--show-object-format"]:
            return 0, fmt
        if args == ["rev-parse", "HEAD"]:
            return 0, head
        if args[:2] == ["merge-base", "--is-ancestor"]:
            return ancestor.get((args[2], args[3]), 128), ""
        raise AssertionError(args)
    return git


# ---- the record and its validation (W1–W4) ---------------------------------------------------------------------------
def test_the_key_is_this_builds_own_and_the_record_validates_as_the_reader_does():
    r = record()
    assert sv.attestation_key(r) == sv.attestation_key(sv.attestation_identity())
    assert sv.attestation_record_problems(r) == []


def test_a_record_whose_provenance_names_two_commits_is_malformed():
    """W1 (a production rule): one record, one commit — v19's ancestry compares exactly that one."""
    r = record()
    r["provenance"] = sorted(r["provenance"] + [dict(r["provenance"][0], job_id=2, commit=B)],
                             key=lambda j: (j["route"], j["runner_image"], j["job_id"]))
    assert any("the same commit" in p for p in sv.attestation_record_problems(r))
    with pytest.raises(aw.AttestationRefused, match="malformed"):
        aw.merged([], r, git=fake_git())


@pytest.mark.parametrize("mark", ["commit", "run_id"])
def test_a_fixture_mark_is_refused_by_the_writer(mark):
    """W4: the writer never writes a fixture (B12's marks), so the packaged artifact holds none by construction."""
    r = record(commit=aw.FIXTURE_COMMIT if mark == "commit" else A)
    if mark == "run_id":
        r["provenance"][0]["run_id"] = "fixture-x"
    with pytest.raises(aw.AttestationRefused, match="fixture mark"):
        aw.merged([], r, git=fake_git(head=r["provenance"][0]["commit"]))


# ---- v19's order, arm by arm, through an injectable git --------------------------------------------------------------
ARMS = {
    # name: (git, existing records, the message the refusal must carry)
    "no git": (fake_git(version_rc=127), [], "unanswerable: git is not available"),
    "outside a repository": (fake_git(inside=None), [], "not inside a git repository"),
    "shallow": (fake_git(shallow="true"), [], "unanswerable: the repository is shallow"),
    "unreadable object format": (fake_git(fmt="sha0"), [], "object format is unreadable"),
    "the record's commit is not HEAD": (fake_git(head=B), [], f"the record's commit {A} is not this checkout's HEAD {B}"),
    "the same commit, different evidence": (fake_git(), "same", "the same commit"),
    "the writing commit is OLDER": (fake_git(ancestor={(B, A): 1, (A, B): 0}), "older", "the writing commit"),
    "sibling branches": (fake_git(ancestor={(B, A): 1, (A, B): 1}), "older", "sibling branches"),
    "--is-ancestor unanswerable": (fake_git(ancestor={(B, A): 128}), "older", "unanswerable: --is-ancestor exited 128"),
    "the reverse unanswerable": (fake_git(ancestor={(B, A): 1, (A, B): 129}), "older",
                                 "unanswerable: the reverse --is-ancestor exited 129"),
}


@pytest.mark.parametrize("arm", sorted(ARMS))
def test_each_cross_run_arm_refuses_with_its_message(arm):
    """v19 §4g.6 4d, each refusal by its MESSAGE. Mutants (stage 2): drop an arm; move the shallow check after
    --is-ancestor; take the same-commit step after step 4; read any nonzero exit as one class; a claimed commit."""
    git, existing, want = ARMS[arm]
    if existing == "same":
        existing = [record(digest="d" * 64)]
    elif existing == "older":
        existing = [record(commit=B)]
    with pytest.raises(aw.AttestationRefused) as e:
        aw.merged(existing, record(), git=git)
    assert want in str(e.value), str(e.value)


def test_the_same_commit_with_equal_evidence_is_idempotent(tmp_path):
    path = tmp_path / "sqlite_runtimes.json"
    path.write_text(json.dumps({"attestations": [record()]}))
    before = path.read_bytes()
    assert aw.write(record(), path=path, git=fake_git()) == "idempotent"
    assert path.read_bytes() == before


def test_a_same_commit_re_record_from_another_job_is_idempotent():
    """INV-SA6 (v19): ordering writes must not make provenance a conflict field. The same commit and equal evidence,
    measured by ANOTHER job of the same run, is idempotent, not "different evidence"."""
    other_job = record()
    other_job["provenance"] = [dict(other_job["provenance"][0], route="deadsnakes", job_id=2)]
    try:
        out, outcome = aw.merged([record()], other_job, git=fake_git())
    except aw.AttestationRefused as exc:                      # the defect itself: provenance read as evidence
        pytest.fail(f"another job's provenance was read as different evidence: {exc}")
    assert outcome == "idempotent"


def test_an_ancestor_replaces_and_every_other_key_is_kept():
    """10(d)'s replacement-by-key, inverted from the legacy writer: an ancestor's record of THIS key is replaced; a
    record of another key (here another machine) is kept byte for byte."""
    other = record(commit=B, machine=OTHER_MACHINE)
    out, outcome = aw.merged([record(commit=B), other], record(), git=fake_git(ancestor={(B, A): 0}))
    assert outcome == "replaced" and out[0] == other and len(out) == 2
    assert sv.record_commit(out[1]) == A


def test_a_later_suite_revision_with_a_changed_result_digest_replaces_and_keeps_every_other_key():
    """I4 (round 2's frozen obligations): "Test a later suite revision with changed result digest: do not append two
    current records for one key or silently lose other keys." An ancestor's record of this key (commit B, digest e…)
    beside another key's; the later run's record of this key (commit A, digest f…) REPLACES the ancestor's: exactly one
    record for the key, carrying the new digest, and the other key's record kept byte for byte. Every other replacement
    cell uses the fixture's one digest, so none of them could see a changed result."""
    old, other, new = record(commit=B), record(commit=B, machine=OTHER_MACHINE), record(digest="f" * 64)
    assert old["result_digest"] != new["result_digest"] and sv.attestation_key(old) == sv.attestation_key(new)
    try:
        out, outcome = aw.merged([old, other], new, git=fake_git(ancestor={(B, A): 0}))
    except aw.AttestationRefused as exc:                # the later revision must be RECORDED, never refused
        raise AssertionError(f"a later suite revision with a changed result digest was refused: {exc}") from None
    assert outcome == "replaced"
    mine = [r for r in out if sv.attestation_key(r) == sv.attestation_key(new)]
    assert len(mine) == 1 and mine[0]["result_digest"] == "f" * 64 and sv.record_commit(mine[0]) == A, mine
    assert [r for r in out if sv.attestation_key(r) != sv.attestation_key(new)] == [other]


def test_a_superseded_revision_is_replaced_only_on_the_full_key():
    """W7 / 10(a): an OLDER-revision record of the same full key is superseded; one sharing (version, source_id) on
    ANOTHER key is kept."""
    old_mine = record(manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)
    old_other = record(manifest_algorithm=sv.MANIFEST_ALGORITHM - 1, machine=OTHER_MACHINE)
    assert (old_other["sqlite_version"], old_other["source_id"]) == (old_mine["sqlite_version"], old_mine["source_id"])
    out, _ = aw.merged([old_mine, old_other], record(), git=fake_git())
    assert old_mine not in out and old_other in out


def test_a_future_revision_of_this_key_is_never_overwritten_and_another_keys_does_not_block():
    """S75 / 10(d): a NEWER revision of this key refuses; a newer revision of ANOTHER key blocks nothing."""
    with pytest.raises(aw.AttestationRefused, match="NEWER revision"):
        aw.merged([record(commit=B, schema_version=sv.SCHEMA_VERSION + 1)], record(), git=fake_git())
    out, outcome = aw.merged([record(commit=B, schema_version=sv.SCHEMA_VERSION + 1, machine=OTHER_MACHINE)], record(),
                             git=fake_git())
    assert outcome == "written" and len(out) == 2


def test_a_record_with_a_failed_confinement_probe_is_refused_as_malformed():
    """W2: the NEW record is validated by production's record validator before anything else runs."""
    d, c = evidence()
    r = record()
    r["confinement"] = dict(c, **{sorted(c)[0]: False})
    with pytest.raises(aw.AttestationRefused, match="the record is malformed"):
        aw.merged([], r, git=fake_git())


def test_a_record_that_would_not_read_back_attested_is_refused(monkeypatch):
    """W2's round trip is a refusal of its own, not only a property of valid input: a reader that would not answer
    attested for the written key stops the write (forged reader; nothing valid reaches this arm otherwise)."""
    monkeypatch.setattr(sv, "attested_key", lambda key, records, *a, **k: False)
    with pytest.raises(aw.AttestationRefused, match="would not read back attested"):
        aw.merged([], record(), git=fake_git())


def test_git_env_scrubs_inherited_repository_variables_and_pins_config():
    """BLOCKING 2 (widened at stage 2), on the environment itself: EVERY inherited GIT_* variable is gone, including
    ones no list named, and exactly the pins are set, whatever the caller inherited."""
    base = {k: "/elsewhere" for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_SHALLOW_FILE", "GIT_REPLACE_REF_BASE",
                                      "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_A_NAME_NO_LIST_HAS")}
    base.update(PATH="/usr/bin", GIT_CONFIG_GLOBAL="/home/dev/.gitconfig", GIT_CONFIG_NOSYSTEM="0",
                GIT_NO_REPLACE_OBJECTS="0")
    env = aw.git_env(base)
    assert {k: v for k, v in env.items() if k.startswith("GIT_")} == {
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1"}
    assert env["PATH"] == "/usr/bin"


def test_an_idempotent_re_record_into_a_poisoned_artifact_is_refused():
    """Stage 2's should-fix: the artifact checks run on the unchanged list too. Another key's conflicting pair already
    poisons the artifact; re-recording this key's equal evidence must not answer idempotent, rc 0."""
    other = record(machine=OTHER_MACHINE)
    poisoned = [record(), other, dict(other, result_digest="b" * 64)]
    with pytest.raises(aw.AttestationRefused, match="would be poisoned"):
        aw.merged(poisoned, record(), git=fake_git())


def test_the_cli_never_builds_a_record(tmp_path, monkeypatch):
    """Stage 2, BLOCKING 2: a job input (evidence plus provenance, no key) is refused. A record built here would wrap
    THIS process's key around another build's evidence. Already-built records are what the CLI merges. (The artifact
    path is redirected, so no mutant of this arm can reach package data.)"""
    import contextlib
    import io
    monkeypatch.setattr(sv, "RUNTIMES", tmp_path / "sqlite_runtimes.json")
    d, c = evidence()
    job_input = tmp_path / "job.json"
    job_input.write_text(json.dumps({"result_digest": d, "confinement": c, "provenance": record()["provenance"]}))
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = aw.main(["attestation_writer.py", str(job_input)])
    assert rc == 1 and "never builds one" in err.getvalue(), err.getvalue()
    assert not (tmp_path / "sqlite_runtimes.json").exists()


def test_a_fresh_write_refuses_an_aggregate_with_a_bootstrap_job(tmp_path, monkeypatch):
    """v21 (3): --fresh takes run 2's records; an aggregate with any bootstrap-pending job is refused, writing nothing."""
    import contextlib
    import io
    path = tmp_path / "sqlite_runtimes.json"
    monkeypatch.setattr(sv, "RUNTIMES", path)
    agg_in = tmp_path / "agg.json"
    agg_in.write_text(json.dumps({"records": [record()], "bootstrap_jobs": ["setup-python on ubuntu-24.04 (job 1)"]}))
    err = io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
        rc = aw.main(["w", "--fresh", str(agg_in)])
    assert rc == 1 and "bootstrap-pending jobs" in err.getvalue() and not path.exists(), err.getvalue()


def test_a_record_the_reader_would_poison_is_never_written():
    """W2: one validator both directions — the prospective artifact must pass the reader's checks."""
    with pytest.raises(aw.AttestationRefused, match="would be poisoned"):
        aw.merged([{"manifest_algorithm": True, "schema_version": 16}], record(), git=fake_git())


# ---- publication (W6) and the round trip (W2) ------------------------------------------------------------------------
def test_a_written_record_reads_back_attested(tmp_path, monkeypatch):
    path = tmp_path / "sqlite_runtimes.json"
    assert aw.write(record(), path=path, git=fake_git()) == "written"
    monkeypatch.setattr(sv, "RUNTIMES", path)
    assert set(json.loads(path.read_text())) == {"attestations"}
    assert sv.runtime_status().status == "attested"


def test_a_failed_publish_leaves_the_artifact_unchanged_and_no_temporary(tmp_path, monkeypatch):
    path = tmp_path / "sqlite_runtimes.json"
    path.write_text(json.dumps({"attestations": []}))
    before = path.read_bytes()

    def boom(*a):
        raise OSError("disk full")
    monkeypatch.setattr(aw.os, "replace", boom)
    with pytest.raises(OSError):
        aw.write(record(), path=path, git=fake_git())
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["sqlite_runtimes.json"]


def test_an_artifact_with_a_foreign_top_level_key_is_refused(tmp_path):
    path = tmp_path / "sqlite_runtimes.json"
    path.write_text(json.dumps({"attestations": [], "runtimes": []}))
    with pytest.raises(aw.AttestationRefused, match="top level"):
        aw.write(record(), path=path, git=fake_git())


def test_the_release_check_reports_every_stale_attestation_record():
    """S77 (round 13, finding 3) on the attestation class: superseded and future-revision records never disqualify a
    build at open time (the reader reads current records), and the release check reports EACH for cleanup; a current
    record and a malformed one are not its to report. A FUTURE record's remedy never says remove (S75: that is the
    downgrade it forbids) nor re-attest (the writer refuses to). Mutants: drop either revision from the report; give
    the future record superseded's remedy."""
    sys.path.insert(0, str(ROOT / "specs"))
    import schema_evidence as ev
    current = record()
    superseded = record(manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)
    future = record(commit=B, schema_version=sv.SCHEMA_VERSION + 1, machine=OTHER_MACHINE)
    malformed = {"manifest_algorithm": True}
    found = ev.stale_attestation_problems([current, superseded, future, malformed, 42])          # total
    assert len(found) == 2 and "superseded revision" in found[0] and "re-attest or remove" in found[0], found
    assert "future revision" in found[1] and "cannot read" in found[1] and "remove" not in found[1], found   # S75
    assert sv.attested_key(sv.attestation_key(current), [current, superseded, future])   # never disqualifying
    assert ev.stale_attestation_problems([current]) == []


def test_the_release_check_itself_carries_the_stale_record_report(monkeypatch, capsys):
    """S77's report is the RELEASE CHECK's, not only a helper's: a superseded record planted in the artifact reaches
    `check()`'s problems, and without it the report is absent (the control). Release probing is stubbed as in
    test_schema_model's missing-versions precedent; skips outside a git checkout, where check() returns 2 first."""
    sys.path.insert(0, str(ROOT / "specs"))
    import schema_evidence as ev
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("no git checkout: check() returns 2 before reaching this")
    monkeypatch.setattr(ev, "_tags", lambda: [])
    monkeypatch.setattr(ev, "_probe_at", lambda ref, work: {"tag": ref, "commit": "x", "on_disk_user_version": 0,
                                                            "store_schema_version": 1, "digest": None, "result": "ok",
                                                            "_objects": {}})
    superseded = record(manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)
    for planted, present in (([], False), ([superseded], True)):
        monkeypatch.setattr(sv, "attestations", lambda planted=planted: list(planted))
        ev.check()
        err = capsys.readouterr().err
        assert ("superseded revision" in err and "re-attest or remove it before release" in err) is present, err[-800:]


# ---- REAL repositories: they ground the injectable git's exit semantics (research's W10(c)) --------------------------
@pytest.fixture
def repo(tmp_path, monkeypatch):
    return _make_repo(tmp_path, monkeypatch)


def _make_repo(tmp_path, monkeypatch):
    """A real repository: commits A0 -> A1 on main, and a sibling S off A0. HOME is the test's own, so no developer
    configuration reaches git (BLOCKING 2's pins are the writer's own)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    r = tmp_path / "repo"
    r.mkdir()

    def g(*args, cwd=r):
        return subprocess.run(["git", *args], cwd=str(cwd), env=aw.git_env(), capture_output=True, text=True,
                              check=True).stdout.strip()
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@example.com")
    g("config", "user.name", "t")
    (r / "f").write_text("0")
    g("add", "f"); g("commit", "-q", "-m", "A0")
    a0 = g("rev-parse", "HEAD")
    g("checkout", "-q", "-b", "side")
    (r / "f").write_text("s")
    g("commit", "-q", "-am", "S")
    s = g("rev-parse", "HEAD")
    g("checkout", "-q", "main")
    (r / "f").write_text("1")
    g("commit", "-q", "-am", "A1")
    a1 = g("rev-parse", "HEAD")
    return {"path": r, "A0": a0, "A1": a1, "S": s, "git": g}


def test_real_an_ancestor_replaces(repo):
    assert aw.run_git(["merge-base", "--is-ancestor", repo["A0"], repo["A1"]], repo["path"])[0] == 0    # precondition
    out, outcome = aw.merged([record(commit=repo["A0"])], record(commit=repo["A1"]), repo=repo["path"])
    assert outcome == "replaced"


def test_real_the_same_commit_is_idempotent_not_a_replacement(repo):
    """v19 step 3 before step 4: a commit IS its own ancestor (real exit 0), so the same-commit step must come first."""
    assert aw.run_git(["merge-base", "--is-ancestor", repo["A1"], repo["A1"]], repo["path"])[0] == 0   # precondition
    out, outcome = aw.merged([record(commit=repo["A1"])], record(commit=repo["A1"]), repo=repo["path"])
    assert outcome == "idempotent"


def test_real_an_older_writing_commit_refuses(repo):
    repo["git"]("checkout", "-q", repo["A0"])                       # the writer stands at the OLDER commit
    assert aw.run_git(["rev-parse", "HEAD"], repo["path"])[1] == repo["A0"]                                # precondition
    with pytest.raises(aw.AttestationRefused, match="the writing commit .* is OLDER"):
        aw.merged([record(commit=repo["A1"])], record(commit=repo["A0"]), repo=repo["path"])


def test_real_a_sibling_branch_refuses(repo):
    assert aw.run_git(["merge-base", "--is-ancestor", repo["S"], repo["A1"]], repo["path"])[0] == 1        # precondition
    assert aw.run_git(["merge-base", "--is-ancestor", repo["A1"], repo["S"]], repo["path"])[0] == 1
    with pytest.raises(aw.AttestationRefused, match="sibling branches"):
        aw.merged([record(commit=repo["S"])], record(commit=repo["A1"]), repo=repo["path"])


def test_real_an_unknown_commit_is_unanswerable_not_older(repo):
    unknown = "c" * 40
    assert aw.run_git(["merge-base", "--is-ancestor", unknown, repo["A1"]], repo["path"])[0] == 128       # precondition
    with pytest.raises(aw.AttestationRefused, match="unanswerable: --is-ancestor exited 128"):
        aw.merged([record(commit=unknown)], record(commit=repo["A1"]), repo=repo["path"])


def test_real_a_shallow_clone_is_unanswerable_before_any_ancestry(repo, tmp_path):
    """Research's W10(c): the clone MUST be file:// — a plain local path ignores --depth and makes a FULL clone."""
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo['path']}", str(shallow)], env=aw.git_env(),
                   check=True, capture_output=True)
    assert aw.run_git(["rev-parse", "--is-shallow-repository"], shallow) == (0, "true")                  # precondition
    with pytest.raises(aw.AttestationRefused, match="unanswerable: the repository is shallow"):
        aw.merged([record(commit=repo["A0"])], record(commit=repo["A1"]), repo=shallow)


def test_real_the_records_commit_must_be_head(repo):
    """BLOCKING 1: an input commit that IS an ancestor of HEAD but not HEAD refuses, naming both."""
    with pytest.raises(aw.AttestationRefused) as e:
        aw.merged([], record(commit=repo["A0"]), repo=repo["path"])
    assert repo["A0"] in str(e.value) and repo["A1"] in str(e.value) and "not this checkout's HEAD" in str(e.value)


def test_real_a_planted_shallow_file_cannot_make_a_shallow_clone_answerable(repo, tmp_path, monkeypatch):
    """Stage 2, BLOCKING 1, measured by research: GIT_SHALLOW_FILE=/nonexistent made a shallow clone answer
    --is-shallow-repository "false". The writer's git never inherits it."""
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo['path']}", str(shallow)], env=aw.git_env(),
                   check=True, capture_output=True)
    monkeypatch.setenv("GIT_SHALLOW_FILE", str(tmp_path / "nonexistent"))
    leak = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=str(shallow), capture_output=True,
                          text=True, env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}).stdout.strip()
    assert leak == "false"                                    # precondition: the variable DOES defeat the question
    with pytest.raises(aw.AttestationRefused, match="unanswerable: the repository is shallow"):
        aw.merged([record(commit=repo["A0"])], record(commit=repo["A1"]), repo=shallow)


def test_real_a_replace_ref_cannot_turn_a_true_ancestor_into_not_an_ancestor(repo):
    """Stage 2, BLOCKING 1: a refs/replace object that drops A1's parent made `--is-ancestor A0 A1` exit 1. The writer
    pins GIT_NO_REPLACE_OBJECTS=1, so the true ancestor still replaces."""
    g = repo["git"]
    tree = g("rev-parse", f"{repo['A1']}^{{tree}}")
    orphan = subprocess.run(["git", "commit-tree", tree, "-m", "no parent"], cwd=str(repo["path"]), env=aw.git_env(),
                            capture_output=True, text=True, check=True).stdout.strip()
    g("replace", repo["A1"], orphan)
    honoured = subprocess.run(["git", "merge-base", "--is-ancestor", repo["A0"], repo["A1"]], cwd=str(repo["path"]),
                              env={k: v for k, v in aw.git_env().items() if k != "GIT_NO_REPLACE_OBJECTS"}).returncode
    assert honoured == 1                                      # precondition: the replace ref DOES move the answer
    try:
        out, outcome = aw.merged([record(commit=repo["A0"])], record(commit=repo["A1"]), repo=repo["path"])
    except aw.AttestationRefused as exc:                      # the defect itself: a TRUE ancestor refused
        pytest.fail(f"a replace ref moved the writer's ancestry answer: {exc}")
    assert outcome == "replaced"


def _commit_artifact(repo, records):
    """Commit `records` as the repo's attestation artifact; returns the new HEAD."""
    p = repo["path"] / aw.ARTIFACT_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"attestations": records}))
    repo["git"]("add", aw.ARTIFACT_REL)
    repo["git"]("commit", "-q", "-m", "artifact")
    return repo["git"]("rev-parse", "HEAD")


def test_real_a_fresh_write_drops_bootstrap_records_and_refuses_a_non_bootstrap_one(repo, tmp_path):
    """v21 (3), the derived mark on a REAL history. A record whose commit's artifact held no current record (A1: no
    artifact at all) is a bootstrap record, and a fresh write drops it. A record whose commit's artifact held a current
    one is not, and a fresh write over it refuses (no W6 bypass)."""
    boot = record(commit=repo["A1"], machine=OTHER_MACHINE)
    assert aw.is_bootstrap_record(boot, repo=repo["path"]) is True
    held = _commit_artifact(repo, [boot])                    # an artifact holding a current record, committed
    attested = record(commit=held, machine=OTHER_MACHINE)
    assert aw.is_bootstrap_record(attested, repo=repo["path"]) is False
    head = _commit_artifact(repo, [boot, attested])
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"attestations": [boot]}))
    aw.write_records([record(commit=head)], path=path, repo=repo["path"], fresh=True)
    assert [sv.record_commit(r) for r in json.loads(path.read_text())["attestations"]] == [head]   # boot dropped
    path.write_text(json.dumps({"attestations": [attested]}))
    with pytest.raises(aw.AttestationRefused, match="non-bootstrap current record"):
        aw.write_records([record(commit=head)], path=path, repo=repo["path"], fresh=True)


_FRESH_EXTRA = {   # SA-R3-04 and research's stage-1 siblings: the record beside K's bootstrap record, and what the
    # ORDINARY write does with it ("refuse:<text>" or "keep"); a fresh write must refuse wherever that one keeps or refuses
    "same-key-future": (lambda a1: record(commit=a1, schema_version=sv.SCHEMA_VERSION + 1), "refuse:(S75)"),
    "other-key-future": (lambda a1: record(commit=a1, machine=OTHER_MACHINE, schema_version=sv.SCHEMA_VERSION + 1),
                         "keep"),
    "other-key-malformed": (lambda a1: record(commit=a1, machine=OTHER_MACHINE, schema_version=str(sv.SCHEMA_VERSION)),
                            "refuse:would be poisoned"),
}


@pytest.mark.parametrize("case", sorted(_FRESH_EXTRA))
def test_real_a_fresh_write_erases_no_future_or_malformed_record_of_any_key(repo, tmp_path, case):
    """0007 round 3, SA-R3-04 (the reviewer's witness is same-key-future; research's stage-1 read found the other two).
    Fresh mode checked only CURRENT records and then cleared the list, so `merged` never saw a future or malformed
    record of any key: it returned `written` and erased it. Now every such record refuses the fresh write, with the
    artifact's bytes unchanged, and the ordinary write's own answer on the same input is unchanged too."""
    make, ordinary = _FRESH_EXTRA[case]
    boot = record(commit=repo["A1"])                          # A1 held no artifact: a bootstrap record of key K
    extra = make(repo["A1"])
    head = _commit_artifact(repo, [boot, extra])
    assert aw.is_bootstrap_record(boot, repo=repo["path"]) is True
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"attestations": [boot, extra]}, indent=2))
    before = path.read_bytes()
    with pytest.raises(aw.AttestationRefused, match="a fresh write would erase a (NEWER revision|malformed) record"):
        aw.write_records([record(commit=head)], path=path, repo=repo["path"], fresh=True)
    assert path.read_bytes() == before
    if ordinary == "keep":
        aw.write_records([record(commit=head)], path=path, repo=repo["path"])
        assert extra in json.loads(path.read_text())["attestations"]           # W6: kept, byte for byte
    else:
        with pytest.raises(aw.AttestationRefused, match=re.escape(ordinary.split(":", 1)[1])):
            aw.write_records([record(commit=head)], path=path, repo=repo["path"])
        assert path.read_bytes() == before


def test_real_a_fresh_write_drops_a_superseded_record_of_another_key(repo, tmp_path):
    """SA-R3-04's clean control: a SUPERSEDED record (an older revision) contributes nothing and is not evidence a
    fresh write could erase; it is dropped with the bootstrap record, as fresh mode intends."""
    boot = record(commit=repo["A1"])
    old = record(commit=repo["A1"], machine=OTHER_MACHINE, manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)
    head = _commit_artifact(repo, [boot, old])
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"attestations": [boot, old]}))
    assert aw.write_records([record(commit=head)], path=path, repo=repo["path"], fresh=True) == {
        repr(sv.attestation_key(record(commit=head))): "written"}
    assert [sv.record_commit(r) for r in json.loads(path.read_text())["attestations"]] == [head]


def test_real_a_fresh_write_keeps_v19s_order(repo, tmp_path):
    """SA-R3-04, the order (dev's reproduction): K's bootstrap record is at a commit NEWER than the writing HEAD. The
    ordinary write refuses "OLDER"; a fresh write cleared the list first and wrote. Its dry run over the original
    artifact now refuses the same way, with the bytes unchanged."""
    h1 = _commit_artifact(repo, [record(commit=repo["A1"], machine=OTHER_MACHINE)])   # h1's artifact holds a current record
    h2 = _commit_artifact(repo, [])                                                   # a zero-current state
    boot = record(commit=h2)
    assert aw.is_bootstrap_record(boot, repo=repo["path"]) is True
    _commit_artifact(repo, [boot])
    repo["git"]("checkout", "-q", h1)                                                  # the writing checkout is OLDER
    new = record(commit=h1)
    assert aw.is_bootstrap_record(new, repo=repo["path"]) is False
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"attestations": [boot]}))
    before = path.read_bytes()
    for fresh in (False, True):
        with pytest.raises(aw.AttestationRefused, match="is OLDER than the recorded"):
            aw.write_records([new], path=path, repo=repo["path"], fresh=fresh)
        assert path.read_bytes() == before


def test_real_the_bootstrap_derivation_and_the_exemption_are_one_predicate(repo):
    """0007 v22 (N1): over every artifact state, the derivation's answer at a commit EQUALS the job's exemption test on
    that artifact (one function). The two v21 readings disagreed on a future-only and a malformed-only artifact."""
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("veracium_attestation_job_n1", ROOT / "specs" / "attestation_job.py")
    jobmod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(jobmod)
    base = record(commit=repo["A1"], machine=OTHER_MACHINE)
    states = {"empty": [], "superseded": [dict(base, manifest_algorithm=sv.MANIFEST_ALGORITHM - 1)], "current": [base],
              "future": [dict(base, schema_version=sv.SCHEMA_VERSION + 1)], "malformed": [{"manifest_algorithm": True}]}
    for name, artifact in states.items():
        at = _commit_artifact(repo, artifact)
        derived = aw.is_bootstrap_record(record(commit=at), repo=repo["path"])
        assert derived is jobmod.bootstrap_open(artifact) is aw.zero_current(artifact), name
    assert [n for n, a in states.items() if aw.zero_current(a)] == ["empty", "superseded"]


def test_real_a_fresh_write_refuses_a_new_record_that_is_itself_a_bootstrap_record(repo, tmp_path):
    """0007 v22 (N2): whatever the input form (here a bare list, no aggregate), a fresh write refuses a NEW record whose
    commit's artifact was at a zero-current state: the shipped set is never a bootstrap run's."""
    path = tmp_path / "out.json"
    path.write_text(json.dumps({"attestations": []}))
    with pytest.raises(aw.AttestationRefused, match="itself a bootstrap record"):
        aw.write_records([record(commit=repo["A1"])], path=path, repo=repo["path"], fresh=True)


def test_real_an_unanswerable_bootstrap_derivation_refuses(repo, tmp_path):
    """v21 (3): an unknown commit, or a shallow clone, is "unanswerable", never "not a bootstrap record"."""
    with pytest.raises(aw.AttestationRefused, match="unanswerable: the record's commit"):
        aw.is_bootstrap_record(record(commit="c" * 40), repo=repo["path"])
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo['path']}", str(shallow)], env=aw.git_env(),
                   check=True, capture_output=True)
    with pytest.raises(aw.AttestationRefused, match="unanswerable: the repository is shallow"):
        aw.is_bootstrap_record(record(commit=repo["A1"]), repo=shallow)


def test_the_release_check_refuses_a_bootstrap_record_and_passes_a_non_bootstrap_one(monkeypatch, capsys):
    """v21 (4), driven through check() itself: a current record whose commit is a REAL commit of this repository at
    which no current record existed (its root commit) is a bootstrap record, refused at release, naming it. The control, the same
    record judged non-bootstrap, carries no refusal. Release probing is stubbed as in S77's cell; skips outside a git
    checkout, where check() returns 2 first."""
    sys.path.insert(0, str(ROOT / "specs"))
    import schema_evidence as ev
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT, capture_output=True).returncode:
        pytest.skip("no git checkout: check() returns 2 before reaching this")
    monkeypatch.setattr(ev, "_tags", lambda: [])
    monkeypatch.setattr(ev, "_probe_at", lambda ref, work: {"tag": ref, "commit": "x", "on_disk_user_version": 0,
                                                            "store_schema_version": 1, "digest": None, "result": "ok",
                                                            "_objects": {}})
    import attestation_writer as used                         # the module schema_evidence itself imports
    # the repository's ROOT commit predates the artifact, so on any full history it is a real bootstrap commit, whatever
    # records later commits carry (no skip: at C1 and after, HEAD's artifact holds records)
    root_commit = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=ROOT, capture_output=True,
                                 text=True).stdout.split()[0]
    boot = record(commit=root_commit)
    monkeypatch.setattr(sv, "attestations", lambda: [boot])
    assert ev.check() == 1                                    # the REAL derivation, on this repository's history
    assert "BOOTSTRAP record" in capsys.readouterr().err
    monkeypatch.setattr(used, "is_bootstrap_record", lambda r, **k: False)          # control: judged non-bootstrap
    ev.check()
    assert "BOOTSTRAP record" not in capsys.readouterr().err


def test_real_the_release_check_refuses_a_bootstrap_record_by_derivation(repo):
    """v21 (4), on a REAL history and with no git checkout of this tree needed: the release check's own function
    names a record whose commit's artifact held no current record, and passes one whose commit's artifact held one."""
    sys.path.insert(0, str(ROOT / "specs"))
    import schema_evidence as ev
    boot = record(commit=repo["A1"], machine=OTHER_MACHINE)
    held = _commit_artifact(repo, [boot])
    found = ev.bootstrap_release_problems([boot], repo=repo["path"])
    assert len(found) == 1 and "BOOTSTRAP record" in found[0], found
    assert ev.bootstrap_release_problems([record(commit=held, machine=OTHER_MACHINE)], repo=repo["path"]) == []


def test_real_an_inherited_git_dir_cannot_answer_for_another_repository(repo, tmp_path, monkeypatch):
    """BLOCKING 2: GIT_DIR pointing at ANOTHER repository is scrubbed, so HEAD is read from the repository the writer
    stands in."""
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(other), env=aw.git_env(), check=True)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "nope"))
    assert aw.run_git(["rev-parse", "HEAD"], repo["path"]) == (0, repo["A1"])
    out, outcome = aw.merged([], record(commit=repo["A1"]), repo=repo["path"])
    assert outcome == "written"


# ---- the writer's mutation matrix (P1; CLAUDE.md item 9) ------------------------------------------------------------
WRITER = ROOT / "specs" / "attestation_writer.py"
SHALLOW = ('''    rc, out = git(["rev-parse", "--is-shallow-repository"], repo)
    if rc != 0 or out != "false":
        raise AttestationRefused("unanswerable: the repository is shallow (or its shallowness cannot be read), so "
                                 "--is-ancestor's exit 1 would be ambiguous")
''')
ARM = "test_each_cross_run_arm_refuses_with_its_message"
FRESH_ANY = "test_real_a_fresh_write_erases_no_future_or_malformed_record_of_any_key"
MUTANTS = {
    # name: ([(anchor, replacement), ...], [(killing cell, its parameters), ...])
    # ---- I4: a later suite revision with a changed result digest (round 2's obligation; the three failure words) -----
    "keep the replaced record beside the new one (two current records for one key)": (
        [('        outcome = "replaced"                          # this current record is replaced by the new one\n',
          '        out.append(r)\n        outcome = "replaced"\n')],
        [("test_a_later_suite_revision_with_a_changed_result_digest_replaces_and_keeps_every_other_key", {})]),
    "drop every other key's record on a replacement (silently lose other keys)": (
        [("    # Both checks run on the idempotent list too", '    if outcome == "replaced":\n'
          "        out = [x for x in out if not isinstance(x, dict) or sv.attestation_key(x) == key]\n"
          "    # Both checks run on the idempotent list too")],
        [("test_a_later_suite_revision_with_a_changed_result_digest_replaces_and_keeps_every_other_key", {})]),
    "refuse a changed result digest as a conflict (a later revision cannot be recorded)": (
        [("        decision = _ordered(r, new, commit, repo, git, fmt)\n",
          '        if r.get("result_digest") != new.get("result_digest"):\n'
          '            raise AttestationRefused("a different result digest for this key")\n'
          "        decision = _ordered(r, new, commit, repo, git, fmt)\n")],
        [("test_a_later_suite_revision_with_a_changed_result_digest_replaces_and_keeps_every_other_key", {})]),
    # ---- SA-R3-04 (round 3): a fresh write runs every ordinary check against the ORIGINAL artifact ----------------
    "fresh refuses no future or malformed record (another key's is erased; the same key's reads as S75)": (
        [('            if rev in ("future", "malformed"):\n', "            if False:\n")],
        [(FRESH_ANY, {"case": "other-key-future"}), (FRESH_ANY, {"case": "other-key-malformed"}),
         (FRESH_ANY, {"case": "same-key-future"})]),
    "fresh skips the dry run over the original artifact (v19's order is not applied)": (
        [("        probe = list(records)\n        for new in news:\n            probe, _ = merged(probe, new, repo=repo, git=git)\n", "")],
        [("test_real_a_fresh_write_keeps_v19s_order", {})]),
    "the superseded implementation: fresh checks only current records, then clears the list": (
        [('            if rev in ("future", "malformed"):\n', "            if False:\n"),
         ("        probe = list(records)\n        for new in news:\n            probe, _ = merged(probe, new, repo=repo, git=git)\n", "")],
        [(FRESH_ANY, {"case": "same-key-future"}), ("test_real_a_fresh_write_keeps_v19s_order", {})]),
    "shallow check dropped": ([('    if rc != 0 or out != "false":\n', "    if False:\n")],
                              [(ARM, {"arm": "shallow"}), ("test_real_a_shallow_clone_is_unanswerable_before_any_ancestry", {})]),
    "shallow check after the ancestry": (
        [(SHALLOW, ""), ("        out.append(new)\n    # Both checks", "        out.append(new)\n"
                         + SHALLOW.replace("rc, out", "s_rc, s_out").replace("rc != 0 or out", "s_rc != 0 or s_out")
                         + "    # Both checks")],
        [("test_real_a_shallow_clone_is_unanswerable_before_any_ancestry", {})]),
    "same-commit step dropped": ([("    if old_commit == new_commit:", "    if False:")],
                                 [(ARM, {"arm": "the same commit, different evidence"}),
                                  ("test_the_same_commit_with_equal_evidence_is_idempotent", {})]),
    "same-commit step after --is-ancestor": (
        [("    if old_commit == new_commit:", '    if git(["merge-base", "--is-ancestor", old_commit, new_commit], repo)[0] == 0:\n'
          '        return "replace"\n    if old_commit == new_commit:')],
        [("test_real_the_same_commit_is_idempotent_not_a_replacement", {})]),
    "any nonzero --is-ancestor read as 'not an ancestor'": ([("    if rc == 1:\n        rrc", "    if rc != 0:\n        rrc")],
        [(ARM, {"arm": "--is-ancestor unanswerable"}), ("test_real_an_unknown_commit_is_unanswerable_not_older", {})]),
    "any nonzero reverse read as 'sibling'": ([("        if rrc == 1:\n", "        if rrc != 0:\n")],
                                              [(ARM, {"arm": "the reverse unanswerable"})]),
    "replace whatever the commit order (v18's behaviour, INV-SA6)": (
        [('    rc, _ = git(["merge-base", "--is-ancestor", old_commit, new_commit], repo)\n    if rc == 0:',
          '    rc = 0\n    if rc == 0:')],
        [("test_real_an_older_writing_commit_refuses", {}), ("test_real_a_sibling_branch_refuses", {})]),
    "compare provenance as evidence when ordering writes (INV-SA6)": (
        [('    evidence = lambda r: (r["result_digest"], json.dumps(r["confinement"], sort_keys=True))   # noqa: E731',
          '    evidence = lambda r: (r["result_digest"], json.dumps(r["confinement"], sort_keys=True), json.dumps(r["provenance"]))   # noqa: E731')],
        [("test_a_same_commit_re_record_from_another_job_is_idempotent", {})]),
    "a fresh write drops a non-bootstrap record (v21)": (
        [("            if sv.attestation_revision(r) == \"current\" and not is_bootstrap_record(r, repo=repo, git=git):",
          "            if False:")],
        [("test_real_a_fresh_write_drops_bootstrap_records_and_refuses_a_non_bootstrap_one", {})]),
    "a fresh write accepts a bootstrap-pending job (v21)": (
        [('    if fresh and isinstance(data, dict) and data.get("bootstrap_jobs"):', "    if False:")],
        [("test_a_fresh_write_refuses_an_aggregate_with_a_bootstrap_job", {})]),
    "an unanswerable bootstrap derivation read as not bootstrap (v21)": (
        [('        raise AttestationRefused(f"unanswerable: the record\'s commit {commit} is not in this repository")',
          "        return False")],
        [("test_real_an_unanswerable_bootstrap_derivation_refuses", {})]),
    "the bootstrap mark derived by a test other than the exemption's (v22)": (
        [("    return zero_current(then)", '    return not any(sv.attestation_revision(x) == "current" for x in then)')],
        [("test_real_the_bootstrap_derivation_and_the_exemption_are_one_predicate", {})]),
    "a fresh write accepts a new bootstrap record (v22)": (
        [("        for new in news:            # v22 (N2)", "        for new in []:            # v22 (N2)")],
        [("test_real_a_fresh_write_refuses_a_new_record_that_is_itself_a_bootstrap_record", {})]),
    "a claimed commit accepted": ([("    if rc != 0 or head != commit:\n", "    if rc != 0:\n")],
                                  [(ARM, {"arm": "the record's commit is not HEAD"}), ("test_real_the_records_commit_must_be_head", {})]),
    "fixture commit mark dropped": ([('j["commit"] == FIXTURE_COMMIT or ', "")],
                                    [("test_a_fixture_mark_is_refused_by_the_writer", {"mark": "commit"})]),
    "fixture run-id mark dropped": ([(' or j["run_id"].startswith("fixture-")', "")],
                                    [("test_a_fixture_mark_is_refused_by_the_writer", {"mark": "run_id"})]),
    "a future revision overwritten (S75)": ([('        if rev == "future":\n', "        if False:\n")],
        [("test_a_future_revision_of_this_key_is_never_overwritten_and_another_keys_does_not_block", {})]),
    "the key reduced to (version, source_id) (W7)": (
        [("sv.attestation_key(r) != key:", '(r.get("sqlite_version"), r.get("source_id")) != (new["sqlite_version"], new["source_id"]):')],
        [("test_a_superseded_revision_is_replaced_only_on_the_full_key", {}),
         ("test_a_future_revision_of_this_key_is_never_overwritten_and_another_keys_does_not_block", {})]),
    "a superseded record kept": ([("            continue                                  # 10(a)", "            out.append(r); continue  # 10(a)")],
                                 [("test_a_superseded_revision_is_replaced_only_on_the_full_key", {})]),
    "another key's record dropped (W6)": ([("            out.append(r)                             # another key", "            pass  # another key")],
                                          [("test_an_ancestor_replaces_and_every_other_key_is_kept", {})]),
    "the new record unvalidated": ([('    if problems:\n        raise AttestationRefused(f"the record is malformed', '    if False:\n        raise AttestationRefused(f"the record is malformed')],
                                   [("test_a_record_with_a_failed_confinement_probe_is_refused_as_malformed", {})]),
    "the prospective artifact unvalidated": ([('    if problems:\n        raise AttestationRefused(f"the prospective', '    if False:\n        raise AttestationRefused(f"the prospective')],
                                             [("test_a_record_the_reader_would_poison_is_never_written", {})]),
    "the round trip dropped": ([("    if not sv.attested_key(key, out):\n", "    if False:\n")],
                               [("test_a_record_that_would_not_read_back_attested_is_refused", {})]),
    "git's environment unscrubbed": ([('if not k.startswith("GIT_")}', "if True}")],
        [("test_real_an_inherited_git_dir_cannot_answer_for_another_repository", {}),
         ("test_git_env_scrubs_inherited_repository_variables_and_pins_config", {})]),
    "global config not pinned": ([('"GIT_CONFIG_GLOBAL": os.devnull, ', "")],
                                 [("test_git_env_scrubs_inherited_repository_variables_and_pins_config", {})]),
    "a named scrub list (stage 2)": ([('if not k.startswith("GIT_")}', 'if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_INDEX_FILE", "GIT_CEILING_DIRECTORIES")}')],
                                     [("test_real_a_planted_shallow_file_cannot_make_a_shallow_clone_answerable", {}),
                                      ("test_git_env_scrubs_inherited_repository_variables_and_pins_config", {})]),
    "replace objects honoured (stage 2)": ([(', "GIT_NO_REPLACE_OBJECTS": "1"}', "}")],
                                           [("test_real_a_replace_ref_cannot_turn_a_true_ancestor_into_not_an_ancestor", {})]),
    "idempotent skips the artifact checks (stage 2)": ([('            out, outcome = list(records), "idempotent"\n            break', '            return list(records), "idempotent"')],
                                                       [("test_an_idempotent_re_record_into_a_poisoned_artifact_is_refused", {})]),
    "the CLI builds from a job input (stage 2)": ([('    records = data.get("records") if isinstance(data, dict) else data\n', '    records = ([build_record(data["result_digest"], data["confinement"], data["provenance"])]\n               if isinstance(data, dict) and "result_digest" in data else data)\n')],
                                                  [("test_the_cli_never_builds_a_record", {})]),
    "publication not atomic": ([("        os.replace(tmp, path)\n", "        path.write_text(pathlib.Path(tmp).read_text())\n")],
                               [("test_a_failed_publish_leaves_the_artifact_unchanged_and_no_temporary", {})]),
    "an idempotent write rewrites the file": ([('    if set(outcomes.values()) <= {"idempotent"}:\n        return outcomes\n', "")],
                                              [("test_the_same_commit_with_equal_evidence_is_idempotent", {})]),
    "the top level left open": ([("    if not isinstance(data, dict) or set(data) - sv.ARTIFACT_KEYS or ", "    if not isinstance(data, dict) or ")],
                                [("test_an_artifact_with_a_foreign_top_level_key_is_refused", {})]),
}


def _load_writer(text, name):
    import types
    mod = types.ModuleType(name)
    mod.__file__ = str(WRITER)
    exec(compile(text, str(WRITER), "exec"), mod.__dict__)
    return mod


def _run_cell(mod, cell, params, tmp_path_factory):
    """'pass', 'kill' (an assertion or DID NOT RAISE: the classifier's two kill kinds) or 'crash: <type>'."""
    import inspect
    this = sys.modules[__name__]
    fn = getattr(this, cell)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(this, "aw", mod)
        tmp = tmp_path_factory.mktemp("cell")
        args = {}
        for name in inspect.signature(fn).parameters:
            if name in params:
                args[name] = params[name]
            elif name == "tmp_path":
                args[name] = tmp
            elif name == "monkeypatch":
                args[name] = mp
            elif name == "repo":
                args[name] = _make_repo(tmp, mp)
            else:
                raise AssertionError(f"{cell}: no argument for {name}")
        try:
            fn(**args)
        except (AssertionError, pytest.fail.Exception):
            return "kill"
        except Exception as exc:  # noqa: BLE001 - a crash is reported, never counted as a kill
            return f"crash: {type(exc).__name__}: {exc}"
    return "pass"


def test_the_attestation_writer_mutation_matrix(tmp_path_factory):
    """P1's matrix for specs/attestation_writer.py: every mutant is killed BY ASSERTION in at least one of its named
    cells, each cell passing on the unmutated source loaded the same way (the control, run first and last). Each
    anchor must occur exactly once and the mutant must change the bytes (mutate.py's rule)."""
    text = WRITER.read_text()
    cells = sorted({(c, tuple(sorted(p.items()))) for _, kills in MUTANTS.values() for c, p in kills})

    def control(label):
        mod = _load_writer(text, "aw_control")
        bad = {c: r for c, p in cells if (r := _run_cell(mod, c, dict(p), tmp_path_factory)) != "pass"}
        assert not bad, (label, bad)
    control("control, first")
    survivors = {}
    for name, (edits, kills) in MUTANTS.items():
        mutated = text
        for anchor, replacement in edits:
            assert mutated.count(anchor) == 1, (name, anchor)
            mutated = mutated.replace(anchor, replacement)
        assert mutated != text, name
        mod = _load_writer(mutated, "aw_mutant")
        results = {c: _run_cell(mod, c, p, tmp_path_factory) for c, p in kills}
        if "kill" not in results.values():
            survivors[name] = results
    control("control, last")
    assert not survivors, survivors
