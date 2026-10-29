#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0007_attestation_writer.py::test_the_attestation_writer_mutation_matrix
"""0007 §4g.6 4d (and v19): the attestation-record WRITER — the one way a record reaches `sqlite_runtimes.json`.

An attestation record states that the FULL attestation suite passed in this repository's CI on one build. The record's
KEY is never taken from the job's input: it is THIS process's `sv.attestation_identity()`, through production's one
canonicaliser (`sv.options_digest`, `sv.canonical_platform`). The job supplies only its evidence (the suite's result
digest and the sixteen confinement results) and its provenance (route, runner image, run, job, commit).

Writing, in order (research's stage-1 read of the writer, f5aaa289 §18, and W1–W7):
  1. the record is built and validated by PRODUCTION's own `attestation_record_problems` (one validator both
     directions, W2); a fixture mark (the all-zeros commit, a `fixture-` run id) is refused outright (W4);
  2. answerability, ALWAYS: git present, inside a repository, not shallow, the record's ONE commit (W1) full hex in the
     repository's object format, and that commit IS this checkout's HEAD (BLOCKING 1: never a claimed commit);
  3. per existing record of the SAME full key (`sv.attestation_key`, never a reconstruction, W7): a FUTURE revision
     refuses (S75); an OLDER revision is superseded (10(a)'s carve-out); a CURRENT one goes through v19's order —
     the same commit (equal evidence idempotent, else refused), then `merge-base --is-ancestor` (0 replaces; 1
     refuses "not an ancestor", the reverse call naming the direction; anything else "unanswerable");
  4. records of other keys are kept unchanged (merge, never replace, W6); the prospective artifact must pass
     `attestation_artifact_problems`, and must read back attested for the written key (W2's round trip);
  5. published atomically: a temporary in the same directory, then `os.replace`; the top level stays closed.
Git runs with its environment PINNED (BLOCKING 2; widened at stage 2): every inherited GIT_* variable is dropped,
system and global configuration are off, and replace objects are ignored.

The CLI merges records ALREADY BUILT, each in the CI job that measured its build (I5: attestation_job.py builds it,
attestation_aggregate.py groups it). It never builds one: a record built here would wrap THIS process's key around
another build's evidence (research's stage 2, BLOCKING 2).

    $PY specs/attestation_writer.py <records.json>       # a JSON list of records, or an aggregate summary
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from veracium.store import schema_version as sv  # noqa: E402

GIT_PINNED = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_NO_REPLACE_OBJECTS": "1"}
"""Git's environment is built by DROPPING every inherited GIT_* variable, then pinning these (research's stage 2 on
5c01ec7, BLOCKING 1: a named scrub list was one short. GIT_SHALLOW_FILE=/nonexistent made a shallow clone answer
--is-shallow-repository "false", and a refs/replace object dropping a parent turned a true ancestor into exit 1;
GIT_NO_REPLACE_OBJECTS=1 restores it). A missing variable is an ABSENT name, which no list can be mutation-tested
for, so the rule is by prefix."""
FIXTURE_COMMIT = "0" * 40
_HEX = {"sha1": re.compile(r"[0-9a-f]{40}"), "sha256": re.compile(r"[0-9a-f]{64}")}


class AttestationRefused(Exception):
    """The writer refuses; nothing was written. The message names why."""


def git_env(base=None) -> dict:
    """Git's environment, PINNED (BLOCKING 2): no inherited variable can answer "shallow?" or "ancestor?" for another
    repository or object store, and no developer's configuration changes an answer."""
    env = {k: v for k, v in (os.environ if base is None else base).items() if not k.startswith("GIT_")}
    env.update(GIT_PINNED)
    return env


def run_git(args, repo) -> tuple:
    """(exit code, stripped stdout) of `git <args>` in `repo`; 127 when git itself cannot run."""
    try:
        p = subprocess.run(["git", *args], cwd=str(repo), env=git_env(), capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return p.returncode, p.stdout.strip()


def build_record(result_digest, confinement, provenance) -> dict:
    """The record for THIS build: its key from `sv.attestation_identity()` (W3), the job's evidence and provenance."""
    ident = sv.attestation_identity()
    if sv.attestation_key(ident) is None:
        raise AttestationRefused(f"this build's attestation key has an unreadable field "
                                 f"({[k for k in sv.KEY_FIELDS if ident[k] is None]}); it can never be attested")
    return {**{k: ident[k] for k in sv.KEY_FIELDS}, "manifest_algorithm": sv.MANIFEST_ALGORITHM,
            "schema_version": sv.SCHEMA_VERSION, "result_digest": result_digest, "confinement": confinement,
            "provenance": sorted(provenance, key=lambda j: (j.get("route"), j.get("runner_image"), j.get("job_id")))
            if isinstance(provenance, list) else provenance}


def _check_record(rec) -> str:
    problems = sv.attestation_record_problems(rec)
    if problems:
        raise AttestationRefused(f"the record is malformed: {problems[0]}")
    for j in rec["provenance"]:
        if j["commit"] == FIXTURE_COMMIT or j["run_id"].startswith("fixture-"):
            raise AttestationRefused("the record carries a fixture mark (the all-zeros commit or a fixture- run id): "
                                     "fixture records are tests-only and never written")
    return sv.record_commit(rec)


def _answerable(commit, repo, git) -> None:
    """v19 step 2, plus BLOCKING 1: the record's commit must be this checkout's HEAD."""
    rc, _ = git(["--version"], repo)
    if rc != 0:
        raise AttestationRefused("unanswerable: git is not available")
    rc, out = git(["rev-parse", "--is-inside-work-tree"], repo)
    if rc != 0 or out != "true":
        raise AttestationRefused("unanswerable: the writer is not inside a git repository")
    rc, out = git(["rev-parse", "--is-shallow-repository"], repo)
    if rc != 0 or out != "false":
        raise AttestationRefused("unanswerable: the repository is shallow (or its shallowness cannot be read), so "
                                 "--is-ancestor's exit 1 would be ambiguous")
    rc, fmt = git(["rev-parse", "--show-object-format"], repo)
    if rc != 0 or fmt not in _HEX:
        raise AttestationRefused(f"unanswerable: the repository's object format is unreadable ({fmt!r})")
    if not _HEX[fmt].fullmatch(commit):
        raise AttestationRefused(f"unanswerable: the record's commit {commit!r} is not a full {fmt} id")
    rc, head = git(["rev-parse", "HEAD"], repo)
    if rc != 0 or head != commit:
        raise AttestationRefused(f"the record's commit {commit} is not this checkout's HEAD {head or '(unreadable)'}: "
                                 f"a record attests the commit its suite ran at, never a claimed one")
    return fmt


def _ordered(existing, new, new_commit, repo, git, fmt) -> str:
    """v19's order for an existing CURRENT record of the same full key: "idempotent", "replace", or a refusal."""
    old_commit = sv.record_commit(existing)
    if old_commit is None or not _HEX[fmt].fullmatch(old_commit):
        raise AttestationRefused(f"unanswerable: the existing record's commit {old_commit!r} is not a full {fmt} id")
    evidence = lambda r: (r["result_digest"], json.dumps(r["confinement"], sort_keys=True))   # noqa: E731
    if old_commit == new_commit:                   # before --is-ancestor: a commit is its own ancestor
        if evidence(existing) == evidence(new):
            return "idempotent"
        raise AttestationRefused(f"the same commit {new_commit} recorded different evidence for one key: the key "
                                 f"does not identify the build")
    rc, _ = git(["merge-base", "--is-ancestor", old_commit, new_commit], repo)
    if rc == 0:
        return "replace"
    if rc == 1:
        rrc, _ = git(["merge-base", "--is-ancestor", new_commit, old_commit], repo)
        if rrc == 0:
            raise AttestationRefused(f"not an ancestor: the writing commit {new_commit} is OLDER than the recorded "
                                     f"{old_commit}")
        if rrc == 1:
            raise AttestationRefused(f"not an ancestor: {old_commit} and {new_commit} are on sibling branches or the "
                                     f"history was rewritten")
        raise AttestationRefused(f"unanswerable: the reverse --is-ancestor exited {rrc}")
    raise AttestationRefused(f"unanswerable: --is-ancestor exited {rc}")


def merged(records, new, *, repo=ROOT, git=run_git) -> tuple:
    """(the prospective record list, "written" | "replaced" | "idempotent"). Raises AttestationRefused."""
    commit = _check_record(new)
    fmt = _answerable(commit, repo, git)
    key = sv.attestation_key(new)
    out, outcome = [], "written"
    for r in records:
        if not isinstance(r, dict) or sv.attestation_key(r) != key:
            out.append(r)                             # another key: kept, byte for byte (W6)
            continue
        rev = sv.attestation_revision(r)
        if rev == "future":
            raise AttestationRefused("refusing to overwrite a NEWER revision's record of this key: this checkout is "
                                     "older than the artifact (S75)")
        if rev == "superseded":
            continue                                  # 10(a)'s carve-out, on the FULL key only (W7)
        if rev == "malformed":
            out.append(r)                             # left for the artifact check below to refuse
            continue
        decision = _ordered(r, new, commit, repo, git, fmt)
        if decision == "idempotent":
            out, outcome = list(records), "idempotent"
            break
        outcome = "replaced"                          # this current record is replaced by the new one
    else:
        out.append(new)
    # Both checks run on the idempotent list too (stage 2, should-fix): a re-record into an artifact ALREADY poisoned
    # by another key must not report idempotent, rc 0, while the reader attests nothing from it.
    problems = sv.attestation_artifact_problems(out)
    if problems:
        raise AttestationRefused(f"the prospective artifact would be poisoned: {problems[0]}")
    if not sv.attested_key(key, out):
        raise AttestationRefused("the written record would not read back attested (round trip)")
    return out, outcome


def write(new, *, path=None, repo=ROOT, git=run_git) -> str:
    """Merge `new` into the artifact at `path` (default: the package's) and publish it atomically."""
    return next(iter(write_records([new], path=path, repo=repo, git=git).values()))


ARTIFACT_REL = "src/veracium/store/evidence/sqlite_runtimes.json"


def zero_current(records) -> bool:
    """0007 v22 (N1): THE zero-current test, ONE function for the job's exemption and for the bootstrap derivation:
    every record superseded (none counts). A current, malformed or future record makes it False."""
    return isinstance(records, list) and all(sv.attestation_revision(r) == "superseded" for r in records)


def is_bootstrap_record(r, *, repo=ROOT, git=run_git) -> bool:
    """v21 (3), v22 (N1): the bootstrap mark is DERIVED, never stored. A record is a bootstrap record iff the
    committed artifact AT ITS OWN COMMIT was at a zero-current state, by the exemption's own test (zero_current): any
    run at a zero-current state is a bootstrap run. Needs full
    history: a shallow repository, an unknown commit or an unreadable artifact at that commit is "unanswerable"
    (AttestationRefused), never "not bootstrap"."""
    commit = sv.record_commit(r)
    if commit is None:
        raise AttestationRefused("unanswerable: the record has no single commit")
    if git(["rev-parse", "--is-shallow-repository"], repo) != (0, "false"):
        raise AttestationRefused("unanswerable: the repository is shallow, so a record's commit may be absent")
    rc, _ = git(["cat-file", "-e", f"{commit}^{{commit}}"], repo)
    if rc != 0:
        raise AttestationRefused(f"unanswerable: the record's commit {commit} is not in this repository")
    rc, listed = git(["ls-tree", "--name-only", commit, "--", ARTIFACT_REL], repo)
    if rc != 0:
        raise AttestationRefused(f"unanswerable: git ls-tree at {commit} exited {rc}")
    if not listed:
        return True                                    # no artifact at that commit: it held no current record
    rc, text = git(["show", f"{commit}:{ARTIFACT_REL}"], repo)
    try:
        if rc != 0:
            raise ValueError(f"git show exited {rc}")
        then = json.loads(text, object_pairs_hook=_strict_pairs)["attestations"]
        if not isinstance(then, list):
            raise ValueError("'attestations' is not a list")
    except (ValueError, KeyError, TypeError) as exc:
        raise AttestationRefused(f"unanswerable: the artifact at {commit} cannot be read ({exc})")
    return zero_current(then)


def _strict_pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


def write_records(news, *, path=None, repo=ROOT, git=run_git, fresh=False) -> dict:
    """I5 (research's stage-1 Q4): records ALREADY BUILT, each in its own job's process. The aggregator cannot
    recompute another runner's key, so the key is taken ONLY from each record, never from this process. Each record
    still passes everything `merged` asks (production's validator, fixture marks, the HEAD binding, v19's order), and
    they publish together, atomically: {key-tuple-as-list-string: outcome}."""
    path = pathlib.Path(sv.RUNTIMES if path is None else path)
    data = json.loads(path.read_text()) if path.exists() else {"attestations": []}
    if not isinstance(data, dict) or set(data) - sv.ARTIFACT_KEYS or not isinstance(data.get("attestations"), list):
        raise AttestationRefused(f"the existing artifact's top level is not within {sorted(sv.ARTIFACT_KEYS)}")
    records, outcomes = data["attestations"], {}
    if fresh:
        # 0007 round 3, SA-R3-04: every ordinary check runs against the ORIGINAL artifact before fresh mode discards
        # anything. A future or malformed record of ANY key is newer or unreadable evidence, never a licence to erase
        # it (the ordinary write keeps another key's, W6, or refuses the artifact); then a dry run of the ordinary merge
        # over the original applies S75 to the same key, v19's order and the poison check, all with bytes unchanged.
        for r in records:
            rev = sv.attestation_revision(r)
            if rev in ("future", "malformed"):
                what = (f"({r.get('sqlite_version')!r}, {r.get('machine')!r})" if isinstance(r, dict) else repr(r)[:60])
                raise AttestationRefused(
                    f"a fresh write would erase a {'NEWER revision' if rev == 'future' else 'malformed'} record "
                    f"{what}: fresh mode replaces only a bootstrap run's records"
                    + (" (S75)" if rev == "future" else ""))
        # 0007 round 4, SA-R4-02: "malformed" is what THIS revision's ARTIFACT VALIDATOR rejects, not only a malformed
        # revision field. It runs over the ORIGINAL records, before the dry run can replace one, so a same-key current
        # record with a bad digest, a missing or false confinement probe, or an unexpected field (and a conflicting
        # duplicate) refuses, bytes unchanged. Validation of the prospective output is not validation of the original it
        # removes. A superseded record is outside this validator by S74 and is dropped by design (a later format's
        # validator cannot judge it); a future one was refused above.
        bad = sv.attestation_artifact_problems(records)
        if bad:
            raise AttestationRefused(f"a fresh write would erase a malformed record: {bad[0]} (fresh mode replaces only a "
                                     f"bootstrap run's records, and only records this revision's validator accepts)")
        probe = list(records)
        for new in news:
            probe, _ = merged(probe, new, repo=repo, git=git)
        # v21 (3): fresh mode is NOT a W6 bypass. It drops prior records only when every CURRENT one is a bootstrap
        # record by derivation, so an attested key whose route was unavailable on the day is never silently lost.
        for r in records:
            if sv.attestation_revision(r) == "current" and not is_bootstrap_record(r, repo=repo, git=git):
                raise AttestationRefused(f"a fresh write would drop a non-bootstrap current record "
                                         f"({r.get('sqlite_version')!r}, {r.get('machine')!r}): fresh mode replaces "
                                         f"only a bootstrap run's records")
        for new in news:            # v22 (N2): the shipped set is never a bootstrap run's, whatever the input form
            if is_bootstrap_record(new, repo=repo, git=git):
                raise AttestationRefused("a fresh write was given a record that is itself a bootstrap record (its "
                                         "commit's artifact was at a zero-current state): it never ships")
        records = []
    for new in news:
        records, outcome = merged(records, new, repo=repo, git=git)
        outcomes[repr(sv.attestation_key(new))] = outcome
    if set(outcomes.values()) <= {"idempotent"}:
        return outcomes
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps({"attestations": records}, indent=2) + "\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return outcomes


def main(argv) -> int:
    """`attestation_writer.py [--fresh] <records.json | aggregate.json>`.

    `--fresh` (v21) writes the given records ALONE, dropping the existing artifact's, and only over bootstrap records
    (derived; see is_bootstrap_record): it is how run 2's records replace run 1's. Every ordinary check runs against
    the existing artifact first, and a future or malformed record of ANY key refuses it (SA-R3-04). It refuses an aggregate that has any
    bootstrap-pending job, since a bootstrap run's records are never the shipped set."""
    flags = {a for a in argv[1:] if a.startswith("--")}
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1 or flags - {"--fresh"}:
        print(main.__doc__.strip().splitlines()[0], file=sys.stderr)
        return 2
    data = json.loads(pathlib.Path(args[0]).read_text(), object_pairs_hook=_strict_pairs)
    fresh = "--fresh" in flags
    if fresh and isinstance(data, dict) and data.get("bootstrap_jobs"):
        print("refused: a fresh write takes run 2's records, and this aggregate has bootstrap-pending jobs "
              f"({len(data['bootstrap_jobs'])}): a bootstrap run's records are never the shipped set", file=sys.stderr)
        return 1
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list) or not all(isinstance(r, dict) and "provenance" in r for r in records):
        print("refused: the input is not a list of built records (the writer never builds one: a job input belongs to "
              "attestation_job.py, in the job that measured the build)", file=sys.stderr)
        return 1
    try:
        print(write_records(records, fresh=fresh))
    except AttestationRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
