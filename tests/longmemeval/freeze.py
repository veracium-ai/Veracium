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
    # Added 2026-08-01. Absent from the freeze spec's required-content list and
    # from all four freezes in the first real experiment, so nobody wrote down
    # WHAT THE TREATMENT IS. `coverage-selection-balanced` froze the hypothesis,
    # metric, thresholds, analysis plan, item set and stop rules — and never the
    # value of `subgraph_coverage_share`, which is the entire intervention.
    #
    # G15 made us able to prove what a run DID (the manifest's
    # requested/resolved/observed triple). Nothing made us declare in advance
    # what it SHOULD do. An unfrozen treatment strength is a free parameter: a
    # null result invites "you should have used a larger reserve", and choosing
    # the value after any outcome is exactly what G3 exists to prevent.
    "arm_config",
    # Added 2026-08-01 after R2, adopted into the spec's required table by
    # research. Each one exists because R2 failed in a way the previous list
    # could not see:
    #
    #   max_achievable — R2 froze "≥10/12 items improve" against a sample where
    #     7 of 12 were already at a perfect score. Maximum achievable was 5/12,
    #     so P(confirm) = 0 before a single paid call. Six freezes enforced
    #     "fix every degree of freedom" and none asked whether the experiment
    #     could ever say yes. Checkable on paper, at approval time, for free.
    #
    #   tail_guardrail — one item went 1.000 -> 0.000 and the aggregate
    #     criterion could not see it at all. A mean-improvement threshold is
    #     blind to a single query losing everything.
    #
    #   replicate_rationale — R2 froze 3 replicates against a pipeline that is
    #     deterministic by construction (cached extraction, temp 0.0). 0 of 24
    #     cells varied; averaging three identical numbers spent ~1/3 of the
    #     arm-run budget on an experiment whose real problem was too few items.
    #     Replicates must name the variance they absorb.
    "max_achievable",
    "tail_guardrail",
    "replicate_rationale",
)

# Proposed by dev, NOT yet adopted into `freeze-artifact-spec.md`'s required
# table. The verifier enforces the agreed spec; a rule one session invented an
# hour ago must not silently veto the other session's artifact. Reported as an
# advisory so the finding stays visible without blocking:
#
#   a protocol frozen against unspecified code and models is not frozen. The
#   "matched pair" that straddled ce66282 was two runs compared across a
#   retrieval change — this is that defect declared in advance rather than
#   discovered after. Zero of the five real freezes pin a model.
ADVISORY_FIELDS = ("environment",)

# "default" is not a value. Defaults change between versions, so a freeze saying
# "0.4.2 behaviour" silently means something else after 0.5.0 — the frozen
# prediction then describes a configuration nobody can reconstruct.
_PLACEHOLDERS = {"default", "defaults", "as shipped", "current", "tbd", "?"}


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
    arm_config: dict = field(default_factory=dict)
    advisories: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"confirmatory": self.confirmatory, "freeze_id": self.freeze_id,
                "path": self.path, "problems": self.problems,
                "approved_at": self.approved_at,
                "arm_config": self.arm_config, "advisories": self.advisories,
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
_ARM_BLOCK = re.compile(r"^arm_config:\s*$(.*?)(?=^\S|\Z)", re.M | re.S)
_KV = re.compile(r"([a-z_]+)\s*:\s*([^,\s}]+)")
# Arms may be written inline (`arm: {k: v, k: v}`) or nested over following
# indented lines. v1 handled only the inline form and silently returned
# `{"treatment_primary": {"name": ...}}` for the real artifact — it read the
# first sub-key and reported success. A parser that half-succeeds is worse than
# one that fails, so both forms are handled and anything else is a problem.
_ARM_HEAD = re.compile(r"^(\s+)([a-z_0-9]+)\s*:\s*(.*)$")
_NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")
_ISO = re.compile(r"^\s*approved_at:\s*(\S+)", re.M)
_ITEMSET_HASH = re.compile(r"item_set_hash:\s*([0-9a-f]{16,64})", re.I)


def _parse_fields(text: str) -> set[str]:
    return set(_FIELD.findall(text))


def parse_arm_config(text: str) -> dict[str, dict[str, str]]:
    """`arm_config:` → {arm: {param: value}}.

    Deliberately tolerant of layout and strict about content: a block we cannot
    parse is reported as a problem rather than skipped, because a silently
    ignored declaration is worse than an absent one — it reads as frozen.
    """
    m = _ARM_BLOCK.search(text)
    if not m:
        return {}
    out: dict[str, dict[str, str]] = {}
    current, base_indent = None, None
    for raw in m.group(1).splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        h = _ARM_HEAD.match(line)
        if not h:
            continue
        indent, key, rest = len(h.group(1)), h.group(2), h.group(3).strip()
        if base_indent is None:
            base_indent = indent
        if indent <= base_indent:
            # an arm heading: inline params, or a nested block follows
            inline = {k: v for k, v in _KV.findall(rest)} if rest else {}
            # prose keys (rationale_for_0_25: >) are not arms
            if rest.startswith(">") or rest.startswith("|"):
                current = None
                continue
            current = key
            out[key] = inline
        elif current is not None and rest and not rest.startswith((">", "|")):
            # a parameter line under the current arm; keep numerics and pins
            out[current][key] = rest.rstrip(",")
    # drop anything that captured no usable parameter
    return {a: p for a, p in out.items() if p}


_MAX_ACH = re.compile(r"max_achievable\s*:\s*([0-9]+)\s*/\s*([0-9]+)", re.I)
_THRESH = re.compile(r"(?:minimum_improvement|threshold)\D{0,40}?([0-9]+)\s*/\s*([0-9]+)", re.I)


def reachability_problem(text: str) -> str | None:
    """Can the frozen sample actually produce the frozen threshold?

    R2's answer was no, and nobody asked. `P(confirm) = 0` was determinable on
    paper at approval time — this makes it determinable automatically.
    """
    a, t = _MAX_ACH.search(text), _THRESH.search(text)
    if not a or not t:
        return None            # not both stated numerically; nothing to compare
    ach, ach_n = int(a.group(1)), int(a.group(2))
    thr, thr_n = int(t.group(1)), int(t.group(2))
    if ach_n != thr_n:
        return (f"max_achievable is out of {ach_n} but the threshold is out of "
                f"{thr_n} — cannot be compared")
    if thr > ach:
        return (f"UNREACHABLE THRESHOLD: needs {thr}/{thr_n} but the frozen "
                f"sample can produce at most {ach}/{ach_n}. P(confirm) = 0 at "
                f"any effectiveness. This is R2's failure exactly; the freeze "
                f"cannot be approved.")
    return None


def config_conflicts(declared: dict[str, str], observed: dict[str, object],
                     *, arm: str) -> list[str]:
    """Frozen intent vs what the run actually did.

    The freeze declares INTENDED values; `manifest.EffectiveConfig` records
    requested/resolved/OBSERVED. Until now those two records never met — the
    manifest could prove precisely what we ran, and the freeze could not say
    what we meant to run.
    """
    problems = []
    for param, want in declared.items():
        if want.lower() in _PLACEHOLDERS:
            problems.append(f"arm_config[{arm}].{param} = {want!r} is not a "
                            f"value — write the number; defaults move between "
                            f"versions")
            continue
        if param not in observed:
            continue
        got = observed[param]
        try:
            same = abs(float(want) - float(got)) < 1e-9
        except (TypeError, ValueError):
            same = str(want).strip() == str(got).strip()
        if not same:
            problems.append(f"arm_config[{arm}].{param}: freeze declares "
                            f"{want!r}, run observed {got!r}")
    return problems


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

    advisories = [f"{f} not declared (dev proposal, not yet in the spec's "
                  f"required table)" for f in ADVISORY_FIELDS if f not in present]
    unreachable = reachability_problem(text)
    if unreachable:
        problems.append(unreachable)

    arms = parse_arm_config(text)
    if "arm_config" in present and not arms:
        problems.append("arm_config present but unparseable — a declaration "
                        "that cannot be read is worse than an absent one, "
                        "because it reads as frozen")

    return FreezeVerdict(
        confirmatory=not problems, freeze_id=actual, path=str(path),
        problems=problems, fields_present=sorted(present),
        approved_at=approved.isoformat() if approved else None,
        arm_config=arms, advisories=advisories)
