"""Freeze-artifact verification — `proposals/freeze-artifact-spec.md`.

A freeze fixes hypothesis, metric, thresholds and item set **before outcomes
exist**. Without one a run is exploratory by construction; the runner records
that rather than pretending otherwise.

Two rules from the spec drive every design choice here:

* **"Verifiable locally, or it will not be verified."** The freeze id is the
  sha256 of a committed file. Verification is: recompute, compare. No registry,
  no service, no network call — a scheme needing a lookup gets skipped the first
  time someone is in a hurry.
* **The runner never blocks a run for lacking a freeze.** It refuses to call a
  run *confirmatory*; it does not refuse to *run* it. A verification step that
  can stop a run gets disabled the first time it misfires at 2am. One that can
  only downgrade a label survives — the same reasoning that made the manifest's
  eligibility check a predicate rather than a gate.

The exception is check 1: a `--freeze-id` that does not match its file means the
operator believes something false about what is being run, so that aborts
**before the first paid call**, per G15's precedent.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# Every field the spec marks required. A missing one is a verification failure,
# not a warning — an unstated threshold is what post-hoc reasoning fills in.
REQUIRED_FIELDS = (
    "experiment_name", "arm_name", "hypothesis", "primary_metric",
    "thresholds", "analysis_plan", "mapping_procedure", "item_set",
    "stop_rules", "approved_by", "approved_at",
)


class FreezeError(RuntimeError):
    """The operator asserted something false about the freeze. Abort."""


@dataclass
class FreezeVerdict:
    """Why a run is or is not confirmatory. Never a bare bool: the reason is
    what a reader needs six weeks later."""
    confirmatory: bool
    freeze_id: str | None = None
    path: str | None = None
    problems: list[str] = field(default_factory=list)
    fields_present: list[str] = field(default_factory=list)
    approved_at: str | None = None

    def as_dict(self) -> dict:
        return {"confirmatory": self.confirmatory, "freeze_id": self.freeze_id,
                "path": self.path, "problems": self.problems,
                "approved_at": self.approved_at,
                "fields_present": self.fields_present}

    def explain(self) -> str:
        if self.confirmatory:
            return f"confirmatory — freeze {(self.freeze_id or '')[:12]} verified"
        if not self.freeze_id:
            return ("exploratory — no freeze artifact given (this is normal for "
                    "most runs; it only bars use as an acceptance criterion)")
        return "exploratory — " + "; ".join(self.problems)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_items(item_ids) -> str:
    """Hash of the item set, order-independent — the denominator must not be
    able to move without changing the hash."""
    joined = "\n".join(sorted(item_ids)).encode()
    return hashlib.sha256(joined).hexdigest()


_FIELD = re.compile(r"^([a-z_]+):", re.M)
_ISO = re.compile(r"^\s*approved_at:\s*(\S+)", re.M)
_ITEMSET_HASH = re.compile(r"item_set_hash:\s*([0-9a-f]{16,64})", re.I)


def _parse_fields(text: str) -> set[str]:
    return set(_FIELD.findall(text))


def _approved_at(text: str) -> datetime | None:
    m = _ISO.search(text)
    if not m:
        return None
    raw = m.group(1).strip().strip('"\'')
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def verify(freeze_path, *, freeze_id: str | None, run_started_at: datetime,
           item_ids=None) -> FreezeVerdict:
    """The four checks from the spec. Returns a verdict; raises only on check 1.

    `freeze_id` is what the operator passed on the command line; `freeze_path`
    is the file it should name.
    """
    if not freeze_path:
        return FreezeVerdict(confirmatory=False,
                             problems=["no freeze artifact given"])

    path = Path(freeze_path)
    if not path.exists():
        raise FreezeError(
            f"freeze artifact {path} does not exist. The id names a committed "
            f"file; a missing file means the run is not what the operator "
            f"thinks it is.")

    actual = sha256_file(path)

    # --- check 1: the id matches the bytes. Abort, do not downgrade. ---------
    if freeze_id and freeze_id != actual:
        raise FreezeError(
            f"--freeze-id does not match {path}.\n"
            f"  given:  {freeze_id}\n"
            f"  actual: {actual}\n"
            f"  The operator believes something false about what is being run. "
            f"Aborting before the first paid call (G15 precedent). If the "
            f"freeze was amended, that is a NEW file with a new hash and a "
            f"`supersedes:` line — a freeze is never edited.")

    text = path.read_text()
    problems: list[str] = []

    # --- check 2: required fields present -----------------------------------
    present = _parse_fields(text)
    missing = [f for f in REQUIRED_FIELDS if f not in present]
    if missing:
        problems.append(f"missing required field(s): {', '.join(missing)}")

    # --- check 3: approved BEFORE the run started ---------------------------
    approved = _approved_at(text)
    if approved is None:
        problems.append("approved_at missing or unparseable (need ISO-8601)")
    elif approved >= run_started_at:
        problems.append(
            f"approved_at ({approved.isoformat()}) is not strictly before run "
            f"start ({run_started_at.isoformat()}) — a freeze committed after "
            f"the run began is not a freeze")

    # --- check 4: the item set is the one being executed --------------------
    declared = _ITEMSET_HASH.search(text)
    if item_ids is not None:
        if not declared:
            problems.append("no item_set_hash declared, so the denominator "
                            "cannot be pinned")
        else:
            actual_items = sha256_items(item_ids)
            claimed = declared.group(1).lower()
            if not actual_items.startswith(claimed):
                problems.append(
                    f"item_set_hash mismatch: freeze declares {claimed[:16]}, "
                    f"runner is about to execute {actual_items[:16]} "
                    f"({len(list(item_ids))} items)")

    return FreezeVerdict(
        confirmatory=not problems, freeze_id=actual, path=str(path),
        problems=problems, fields_present=sorted(present),
        approved_at=approved.isoformat() if approved else None)
