"""Run manifests, completion attestations, and the two checks that make
benchmark-policy compliance a predicate rather than a set of hopeful fields.

Implements G14–G17 of `benchmark-usage-policy.md`. The motivating failure is
concrete: a retrieval-breadth ablation was configured for 200 edges, a patch
script silently no-op'd, the run executed at 40, and the run record said

    "max_subgraph_edges": 200

for hours. The record did not merely omit the truth, it *asserted the thing
that was false*, and an experiment was drawn from it. Two independent runs were
later offered as a "matched pair" when a retrieval change had landed between
them — unprovable from the artifacts, because no record stores a commit.

So the design rules here are:

* **Record three values per material parameter, not one.** What was requested,
  what the constructed object actually holds, and what the running code
  observed. Construction being correct does not prove propagation was.
* **Two records, never one mutable one.** A manifest written once before the
  first provider call, and an attestation written at termination that
  references it *by hash*. Appending completion data to an "immutable" record
  makes it mutable.
* **Execution status and validity status are different axes.** The no-op
  ablation executed perfectly and was invalidated hours later by analysis.
  One field cannot say that.
* **Unknown means stop.** Not "permanent" — we do not know that — just that
  retrying is unsafe until a human classifies it.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA_VERSION = 1

# Execution outcome: what the run did. Set by the runner.
EXECUTION_STATUS = ("planned", "running", "completed", "failed", "partial")
# Validity: whether the result may inform a decision. Usually determined LATER,
# by analysis, which is exactly why it is not the same field as execution.
VALIDITY_STATUS = ("unreviewed", "valid", "invalidated")


class ManifestError(RuntimeError):
    """A precondition failed. Raised before any provider call, so it costs
    nothing but a stack trace — which is the entire point of checking here."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    """Streamed, because the dataset file is large and we hash it every run."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(obj) -> str:
    """Hash of a JSON structure, stable under key order."""
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                   default=str).encode())


def _git(*args, cwd=None) -> str:
    try:
        return subprocess.run(("git", *args), cwd=cwd, capture_output=True,
                              text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def git_state(repo: Path | None = None) -> dict:
    """Source identity, resolved rather than remembered (G14).

    The dirty fingerprint matters as much as the commit: most of this week's
    experiments ran from a working tree that did not match any commit, so
    "commit abc123" alone would have been a more confident lie than no commit
    at all.
    """
    repo = Path(repo or Path(__file__).resolve().parents[2])
    commit = _git("rev-parse", "HEAD", cwd=repo)
    diff = _git("diff", "HEAD", cwd=repo)
    untracked = _git("ls-files", "--others", "--exclude-standard", cwd=repo)
    return {
        "repo": str(repo),
        "commit": commit or "unknown",
        "dirty": bool(diff),
        # a fingerprint, not the diff: enough to tell two dirty trees apart
        # without writing source into an artifact we may circulate
        "dirty_fingerprint": sha256_bytes(diff.encode())[:16] if diff else None,
        "untracked_count": len([u for u in untracked.splitlines() if u]),
        "describe": _git("describe", "--tags", "--always", "--dirty", cwd=repo),
    }


def environment_state() -> dict:
    """Enough to notice that two runs used different interpreters or SDKs."""
    versions = {}
    for mod in ("openai", "veracium"):
        try:
            versions[mod] = __import__("importlib.metadata", fromlist=["version"]).version(mod)
        except Exception:
            versions[mod] = "unknown"
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "packages": versions}


@dataclass
class Parameter:
    """One material parameter, in the three forms that can disagree.

    `requested` is what the caller asked for. `resolved` is read back off the
    *constructed* runtime object. `observed` is instrumented from real
    execution. The no-op ablation had requested=200, resolved=40, observed=40 —
    a disagreement no single-value record could express.
    """
    requested: object
    resolved: object = None
    observed: object = None

    def agrees(self) -> bool:
        seen = [v for v in (self.requested, self.resolved, self.observed) if v is not None]
        return len(set(map(repr, seen))) <= 1

    def disagreement(self) -> str | None:
        if self.agrees():
            return None
        return (f"requested={self.requested!r} resolved={self.resolved!r} "
                f"observed={self.observed!r}")


class EffectiveConfig:
    """Collects parameters and refuses to let a run start while any disagree.

    Two enforcement points, deliberately: a manifest field populated from the
    constructed object, *and* a post-condition assertion before the first
    benchmark item is processed. The first catches wiring; only the second
    catches a patch that silently did nothing.
    """

    def __init__(self, **requested):
        self._p = {k: Parameter(requested=v) for k, v in requested.items()}

    def resolve(self, **values) -> None:
        """Read back from the constructed runtime object, not from the caller."""
        for k, v in values.items():
            self._p.setdefault(k, Parameter(requested=None)).resolved = v

    def observe(self, **values) -> None:
        """Instrumented from the first item actually processed."""
        for k, v in values.items():
            self._p.setdefault(k, Parameter(requested=None)).observed = v

    def as_dict(self) -> dict:
        return {k: asdict(v) for k, v in self._p.items()}

    def disagreements(self) -> dict:
        return {k: d for k, v in self._p.items() if (d := v.disagreement())}

    def assert_consistent(self, *, stage: str) -> None:
        bad = self.disagreements()
        if bad:
            lines = "\n".join(f"    {k}: {d}" for k, d in bad.items())
            raise ManifestError(
                f"effective configuration mismatch at {stage} — the run would "
                f"produce a record asserting a configuration it is not using:\n"
                f"{lines}\n"
                f"  This is the failure mode that invalidated the "
                f"retrieval-breadth ablation. Fix the wiring or the request; "
                f"do not proceed and reconcile afterwards.")


@dataclass
class RunManifest:
    """Written ONCE, before the first provider call, and never edited.

    Four levels of identity, because one experiment has matched repeats,
    diagnostic reruns, resumes, judge-only reruns and arms. Collapsing those
    into a single id is how a retry starts masquerading as a new experiment.
    """
    experiment_name: str                 # the frozen hypothesis + design
    arm_name: str                        # baseline | treatment | ...
    trust_arm: str                       # veracium-specific: T | C
    experiment_id: str = ""
    run_id: str = ""                     # one semantic execution
    attempt_id: str = ""                 # operational retry, NOT a new experiment
    parent_run_id: str | None = None     # resume lineage
    freeze_artifact_id: str | None = None
    created_at: str = ""
    schema_version: int = SCHEMA_VERSION
    source: dict = field(default_factory=dict)
    environment: dict = field(default_factory=dict)
    dataset: dict = field(default_factory=dict)
    adapter: dict = field(default_factory=dict)
    extraction_identity: dict = field(default_factory=dict)
    effective_config: dict = field(default_factory=dict)
    expected_item_ids: list = field(default_factory=list)
    expected_output_count: int = 0
    note: str = ""

    def __post_init__(self):
        self.experiment_id = self.experiment_id or f"exp_{uuid.uuid4().hex[:12]}"
        self.run_id = self.run_id or f"run_{uuid.uuid4().hex[:12]}"
        self.attempt_id = self.attempt_id or f"attempt_{uuid.uuid4().hex[:12]}"
        self.created_at = self.created_at or time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def hash(self) -> str:
        return canonical_hash(asdict(self))

    def path(self, out_dir: Path) -> Path:
        return Path(out_dir) / f"manifest_{self.run_id}.json"

    def write(self, out_dir: Path) -> str:
        """Write-once. Refuses to overwrite: a manifest that can be rewritten
        is not a manifest, and a colliding run_id means two runs are about to
        share an identity."""
        p = self.path(out_dir)
        if p.exists():
            raise ManifestError(
                f"{p} already exists — a run manifest is written once. "
                f"Two runs sharing {self.run_id} would be indistinguishable "
                f"in the record.")
        p.parent.mkdir(parents=True, exist_ok=True)
        body = asdict(self)
        h = canonical_hash(body)
        p.write_text(json.dumps({"manifest_hash": h, **body}, indent=2))
        return h


@dataclass
class CompletionAttestation:
    """Written at termination, referencing the manifest by hash.

    Separate from the manifest so the immutable record stays immutable, and so
    a run that dies without writing this one is *visibly* incomplete rather
    than looking like a clean run with fewer rows.
    """
    run_id: str
    manifest_hash: str
    execution_status: str
    validity_status: str = "unreviewed"
    invalidation_reason: str | None = None
    finished_at: str = ""
    items_expected: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    per_item_status: dict = field(default_factory=dict)
    # The FINAL configuration triple, including the `observed` values that only
    # exist once items have run. The manifest is written before any of them are
    # known, so it necessarily carries requested + resolved only; without this
    # field the runtime post-condition would be checked and then thrown away.
    effective_config: dict = field(default_factory=dict)
    output_hashes: dict = field(default_factory=dict)
    cost_ledger_hash: str | None = None
    retries: int = 0
    failures: int = 0
    validation: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.execution_status not in EXECUTION_STATUS:
            raise ValueError(f"execution_status must be one of {EXECUTION_STATUS}")
        if self.validity_status not in VALIDITY_STATUS:
            raise ValueError(f"validity_status must be one of {VALIDITY_STATUS}")
        self.finished_at = self.finished_at or time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def write(self, out_dir: Path) -> Path:
        p = Path(out_dir) / f"attestation_{self.run_id}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(self), indent=2))
        return p


def check_manifest_self_consistency(manifest: RunManifest, out_dir: Path, *,
                                    referenced_files=()) -> dict:
    """Runs BEFORE the first provider call (G14/G16).

    Cheap to run and it fails free, which is the argument for putting it here
    rather than in review: every check below corresponds to something we got
    wrong once with real money attached.
    """
    written = manifest.path(out_dir)
    problems = []

    stored = json.loads(written.read_text()) if written.exists() else None
    if stored is None:
        problems.append(f"manifest not written at {written}")
    else:
        claimed = stored.pop("manifest_hash", None)
        if canonical_hash(stored) != claimed:
            problems.append("manifest hash does not recompute — the file was "
                            "edited after it was written")

    if len(manifest.expected_item_ids) != manifest.expected_output_count:
        problems.append(
            f"expected_output_count={manifest.expected_output_count} but the "
            f"item set has {len(manifest.expected_item_ids)} ids")
    if len(set(manifest.expected_item_ids)) != len(manifest.expected_item_ids):
        problems.append("expected_item_ids contains duplicates — per-item "
                        "status would silently collapse")
    if manifest.source.get("commit") == "unknown":
        problems.append("source commit unresolved — two runs could not be "
                        "shown to share a code state (this is exactly what "
                        "made the '3.3pp matched pair' unprovable)")

    for f in referenced_files:
        if not Path(f).exists():
            problems.append(f"referenced file missing: {f}")

    if problems:
        raise ManifestError("manifest self-consistency check failed:\n  - "
                            + "\n  - ".join(problems))
    return {"checked": True, "referenced_files": [str(f) for f in referenced_files]}


DECISION_REQUIREMENTS = (
    "execution_complete", "validity_valid", "effective_config_verified",
    "manifest_hash_matches", "outputs_present", "outputs_hash_match",
    "freeze_artifact_referenced",
)


def decision_eligibility(manifest: RunManifest, attestation: CompletionAttestation,
                         *, out_dir: Path) -> tuple[bool, dict]:
    """Would this run be allowed to inform a decision? (G16/G19)

    Returns (eligible, per-requirement detail). Deliberately a *predicate the
    report generator calls*, not a paragraph in a policy document: the point of
    the whole exercise is that "we should have checked" becomes "the tool
    refused". Exploratory use of an ineligible run is fine and expected — what
    is not fine is an ineligible run reaching an acceptance threshold.
    """
    r = {k: False for k in DECISION_REQUIREMENTS}
    why = {}

    r["execution_complete"] = attestation.execution_status == "completed"
    if not r["execution_complete"]:
        why["execution_complete"] = f"status={attestation.execution_status}"

    r["validity_valid"] = attestation.validity_status == "valid"
    if not r["validity_valid"]:
        why["validity_valid"] = (attestation.invalidation_reason
                                 or f"status={attestation.validity_status}")

    # prefer the attestation's copy: it is the only one that can contain the
    # observed values
    config = attestation.effective_config or manifest.effective_config
    disagree = {k: v for k, v in config.items() if not Parameter(**v).agrees()}
    r["effective_config_verified"] = not disagree
    if disagree:
        why["effective_config_verified"] = ", ".join(disagree)

    r["manifest_hash_matches"] = attestation.manifest_hash == manifest.hash()
    if not r["manifest_hash_matches"]:
        why["manifest_hash_matches"] = "attestation references a different manifest"

    outs = list(attestation.output_hashes)
    r["outputs_present"] = bool(outs)
    if not outs:
        why["outputs_present"] = "no output hashes recorded"
    mismatched = [p for p, h in attestation.output_hashes.items()
                  if not Path(p).exists() or sha256_file(p) != h]
    r["outputs_hash_match"] = bool(outs) and not mismatched
    if mismatched:
        why["outputs_hash_match"] = f"changed or missing since the run: {mismatched}"

    r["freeze_artifact_referenced"] = bool(manifest.freeze_artifact_id)
    if not manifest.freeze_artifact_id:
        why["freeze_artifact_referenced"] = (
            "no frozen protocol — the hypothesis, metric and threshold were "
            "not fixed before the run, so this is exploratory by construction")

    eligible = all(r.values())
    return eligible, {"requirements": r, "why_not": why,
                      "run_id": manifest.run_id,
                      "experiment": manifest.experiment_name}


def explain_ineligibility(detail: dict) -> str:
    """A sentence a human can act on, for the report header."""
    if not detail["why_not"]:
        return "decision-eligible"
    return ("NOT decision-eligible (exploratory only): "
            + "; ".join(f"{k} — {v}" for k, v in detail["why_not"].items()))


def load_manifest(path) -> RunManifest:
    body = json.loads(Path(path).read_text())
    body.pop("manifest_hash", None)
    body.pop("schema_version", None)
    return RunManifest(schema_version=SCHEMA_VERSION, **body)


def load_attestation(path) -> CompletionAttestation:
    return CompletionAttestation(**json.loads(Path(path).read_text()))


def eligibility_for_output(hypothesis_path, out_dir: Path):
    """Find the run that produced `hypothesis_path` and judge its eligibility.

    Links by output hash rather than by filename convention: a file renamed or
    copied between directories should not inherit another run's attestation.
    Returns None for runs that predate the manifest (they are not *ineligible*,
    they are unattested — a distinction the report must state rather than
    quietly resolve either way).
    """
    out_dir = Path(out_dir)
    target = str(hypothesis_path)
    for att_file in sorted(out_dir.glob("attestation_*.json")):
        try:
            att = load_attestation(att_file)
        except Exception:
            continue
        if target not in att.output_hashes:
            continue
        man_file = out_dir / f"manifest_{att.run_id}.json"
        if not man_file.exists():
            return None
        return decision_eligibility(load_manifest(man_file), att, out_dir=out_dir)
    return None
