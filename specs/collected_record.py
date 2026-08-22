#!/usr/bin/env python3
"""The C-plus COLLECTED-header record — COLLECTED_HEADER_DESIGN.md §5, ruled
2026-08-20 and implemented here.

Three parts, mapping onto the review's three blocking findings:

1.  FIELD_POLICY — a code-owned registry, the SOLE authority on how each
    header field must be witnessed (blocking 1). The record REPORTS values
    and classifications; it cannot choose them. A record whose reported
    classification sits below the registry minimum, whose witness id
    differs from the registry's, or which is missing a field the registry
    names, is refused. So is a record carrying anything the schema does
    not name: closed at every level (R15-1).

2.  derive_* functions — each derives a field's value FROM a captured
    immutable raw output (a file), never from the in-memory variables
    that produced it (blocking 3). Agreement between the record and the
    rendered header means something only because both descend from the
    captures.

3.  witness_problems() — the fixed witness implementations, one per
    closed witness id (moderate 4). A witness id this module does not
    implement is a refusal, not a skip. Run from the EXTRACTION by
    `verify_extracted.py header`, and at seal time by the sealer's
    cross-check step (§5.3 step 4).

The whole-file equation (blocking 2) lives in `collected_render`.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent

RECORD_VERSION = 1

# ---------------------------------------------------------------------------
# The four closed evidentiary axes (§5.2). VALIDATIONS and ATTESTATIONS are
# RANKED weakest-first: the registry names a required minimum, the record may
# report that or stronger, never weaker.
# ---------------------------------------------------------------------------
VALIDATIONS = ("syntax", "internal_consistency", "independent_cross_check")
ATTESTATIONS = ("none", "signed_ci")
SOURCES = ("measurement_output", "runtime_probe", "clock", "package_identity",
           "registry", "git", "spec_header", "harness_run", "launcher_run",
           "evidence_transcript")
WITNESSES = ("pytest_rs", "package_manifest", "harness_rerun", "runtime_probe",
             "launcher_transcript", "reviews_sent", "evidence_transcript",
             "extraction_registry", "spec_header", "none")

# Each witness's closed witness_data key set. A field whose witness_data
# carries different keys is refused — an extra key is a place a claim can
# hide, a missing one is a check silently disarmed.
WITNESS_DATA_KEYS = {
    "pytest_rs": (),
    "package_manifest": (),
    "reviews_sent": (),
    "spec_header": (),
    "extraction_registry": (),
    "none": (),
    "harness_rerun": ("results",),
    "runtime_probe": ("artifact", "sha256"),
    "launcher_transcript": ("artifact", "sha256", "exit"),
    "evidence_transcript": ("observed",),
}


def _rank(axis, value):
    return axis.index(value)


class _P:
    __slots__ = ("source", "min_validation", "witness", "min_attestation",
                 "in_header")

    def __init__(self, source, min_validation, witness, in_header,
                 min_attestation="none"):
        self.source = source
        self.min_validation = min_validation
        self.witness = witness
        self.min_attestation = min_attestation
        self.in_header = in_header


# ---------------------------------------------------------------------------
# THE REGISTRY (blocking 1). Keyed by field name; each field's token in the
# header/manifest templates is `__<NAME-uppercased>__`. `in_header` names the
# fields whose token the header template must carry (the rest render only in
# PACKAGE_MANIFEST.txt, outside the whole-file equation, and lean on their
# witnesses instead).
#
# HONESTY NOTE on `package_manifest` as a witness: the manifest is rendered
# from this same record, so at EXTRACTION time that witness proves carrier
# consistency, not truth (design §4). The `independent_cross_check` minimum
# is discharged at SEAL time, where the sealer checks commit against
# `git rev-parse`, identity against package_identity + reviews.py — sources
# the record did not produce. The extraction re-verifies what an extraction
# can: consistency, digests, re-derivation, re-execution.
# ---------------------------------------------------------------------------
FIELD_POLICY = {
    "package":     _P("package_identity", "independent_cross_check",
                      "package_manifest", in_header=False),
    "version":     _P("package_identity", "independent_cross_check",
                      "package_manifest", in_header=True),
    "round":       _P("package_identity", "independent_cross_check",
                      "package_manifest", in_header=True),
    "candidates":  _P("package_identity", "independent_cross_check",
                      "reviews_sent", in_header=True),
    "commit":      _P("git", "independent_cross_check",
                      "package_manifest", in_header=True),
    "commit_full": _P("git", "independent_cross_check",
                      "package_manifest", in_header=False),
    "requires":    _P("spec_header", "independent_cross_check",
                      "spec_header", in_header=True),
    "measured":    _P("measurement_output", "independent_cross_check",
                      "pytest_rs", in_header=True),
    "harnesses":   _P("harness_run", "independent_cross_check",
                      "harness_rerun", in_header=True),
    "evidence":    _P("evidence_transcript", "independent_cross_check",
                      "evidence_transcript", in_header=True),
    "extracted":   _P("registry", "independent_cross_check",
                      "extraction_registry", in_header=True),
    "loose":       _P("registry", "independent_cross_check",
                      "extraction_registry", in_header=False),
    # context and launcher are CAPTURED from the sealing execution (moderate
    # 5): stronger than prose, weaker than independent — the capture and the
    # value share the sealing host. internal_consistency is the honest floor.
    "context":     _P("runtime_probe", "internal_consistency",
                      "runtime_probe", in_header=True),
    "launcher":    _P("launcher_run", "internal_consistency",
                      "launcher_transcript", in_header=True),
    # The timestamp's wall-clock truth is externally unattested AND THE
    # RECORD SAYS SO (§5.4, ruling 2): witness `none`, attestation `none`,
    # structural checks in witness_problems().
    "ts":          _P("clock", "syntax", "none", in_header=True),
}

FIELD_KEYS = ("value", "source", "validation", "witness",
              "external_attestation", "witness_data")
TOP_KEYS = ("record_version", "template", "fields")
TEMPLATE_KEYS = ("path", "sha256")

TS_FORMAT = "%Y%m%dT%H%MZ"
TS_RE = re.compile(r"^\d{8}T\d{4}Z$")
# §5.4: "not in the verifier's future beyond a declared tolerance". Declared:
TS_FUTURE_TOLERANCE_S = 900

# The loose carriers C-plus adds to the archive (captures + the record).
RECORD_CARRIER = "collected_header.json"
PROBE_CARRIER = "RUNTIME_PROBE.json"
LAUNCHER_CARRIER = "LAUNCHER_TRANSCRIPT.txt"
_LAUNCHER_EXIT_RE = re.compile(r"^--- LAUNCHER EXIT: (\d+) ---$", re.M)


class RecordError(ValueError):
    """A record, capture, or witness this module refuses."""


# ---------------------------------------------------------------------------
# Derivations (blocking 3): every function takes the PATH of a captured raw
# output and reads it. None accepts the value it returns as an argument.
# ---------------------------------------------------------------------------

def derive_measured(rs_path: pathlib.Path) -> str:
    m = re.search(r"\d+ passed[^\n]*", rs_path.read_text())
    if not m:
        raise RecordError(f"{rs_path.name} carries no `N passed` summary line")
    return m.group(0)


def load_probe(probe_path: pathlib.Path) -> dict:
    try:
        p = json.loads(probe_path.read_text())
    except (OSError, ValueError) as e:
        raise RecordError(f"the probe artifact does not parse: {e}")
    if not isinstance(p, dict) or sorted(p) != sorted(_probe_keys()):
        raise RecordError(
            f"the probe artifact's keys are {sorted(p) if isinstance(p, dict) else type(p).__name__}, "
            f"expected exactly {sorted(_probe_keys())}")
    bad = [k for k, v in p.items() if not isinstance(v, str)]
    if bad:
        raise RecordError(f"probe values must be strings; {bad} are not")
    return p


def _probe_keys():
    sys.path.insert(0, str(HERE))
    import runtime_probe
    return runtime_probe.PROBE_KEYS


def derive_context(probe_path: pathlib.Path) -> str:
    p = load_probe(probe_path)
    pad = "                 "
    return (f"command        {p['command']}\n"
            f"{pad}cwd            {p['cwd']}  (the author's committed git "
            f"checkout — R10-1: the ONE canonical measurement site)\n"
            f"{pad}interpreter    {p['interpreter']}\n"
            f"{pad}python         {p['python']} ({p['machine']}, "
            f"{p['system']} {p['release']})\n"
            f"{pad}pytest         {p['pytest']}\n"
            f"{pad}sqlite         {p['sqlite']}\n"
            f"{pad}collection     {p['collection']}")


def derive_launcher(transcript_path: pathlib.Path) -> tuple[str, int, str]:
    """(result line, exit status, sha256) from the captured transcript.

    The transcript is the launcher's complete stdout+stderr with one
    `--- LAUNCHER EXIT: N ---` trailer appended by the capture step, so the
    exit status lives IN the digested artifact, not beside it.
    """
    raw = transcript_path.read_bytes()
    text = raw.decode(errors="replace")
    exits = _LAUNCHER_EXIT_RE.findall(text)
    if len(exits) != 1:
        raise RecordError(
            f"{transcript_path.name} carries {len(exits)} exit trailers, "
            f"expected exactly one")
    body = text[:_LAUNCHER_EXIT_RE.search(text).start()]
    line = next((l for l in reversed(body.strip().splitlines())
                 if "passed" in l or "REFUS" in l), "")
    if not line:
        raise RecordError(f"{transcript_path.name} has no result line "
                          f"(`passed` or a refusal)")
    return line.strip(), int(exits[0]), hashlib.sha256(raw).hexdigest()


def derive_harnesses(captures: list[tuple[str, pathlib.Path]]) \
        -> tuple[str, list]:
    """(rendered block, results) from per-harness captured stdout files.

    `captures` is [(script-rel-path, capture-path), ...]; the result line is
    each capture's last non-empty line, exactly what the old in-memory path
    used — now read back from the file.
    """
    results = []
    for script, path in captures:
        lines = [l for l in path.read_text().strip().splitlines() if l.strip()]
        if not lines:
            raise RecordError(f"the harness capture for {script} is empty")
        results.append([script, lines[-1].strip()])
    return render_harness_block(results), results


def render_harness_block(results: list) -> str:
    return "\n                 ".join(
        f"{pathlib.PurePosixPath(s).name:<32} — {line}" for s, line in results)


def derive_evidence(transcript_path: pathlib.Path, total: int,
                    launcher_ev: int) -> tuple[str, int]:
    try:
        observed = len(json.loads(transcript_path.read_text())["commands"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise RecordError(f"the evidence transcript does not parse: {e}")
    return render_evidence_claim(total, observed, launcher_ev), observed


def render_evidence_claim(total: int, observed: int, launcher_ev: int) -> str:
    return (f"{total} closure-evidence commands: {observed} OBSERVED "
            f"executing during this seal's measured run, each with its argv, "
            f"cwd, exit status and output digest recorded in "
            f"specs/generated/evidence_run.json (shipped), and {launcher_ev} "
            f"(the launcher) run separately — the runner skips that one "
            f"because it builds a venv and runs the whole suite")


def derive_requires(specs: list[str], specs_dir: pathlib.Path) -> str:
    """The Spec-Requires block, from each spec file's own header line —
    the one canonical carrier (round 2, L-pair)."""
    lines = []
    for spec in specs:
        matches = sorted(specs_dir.glob(f"{spec}-*.md"))
        if not matches:
            raise RecordError(f"no spec file matches {spec}-*.md")
        for ln in matches[0].read_text().splitlines():
            if ln.startswith("Spec-Requires:"):
                lines.append(f"{spec} Spec-Requires: "
                             f"{ln.split(':', 1)[1].strip()}")
                break
        else:
            raise RecordError(f"{spec} has no Spec-Requires: header line "
                              f"to derive from")
    return "\n                 ".join(lines)


# ---------------------------------------------------------------------------
# Record construction (§5.3 step 3) and validation (blocking 1).
# ---------------------------------------------------------------------------

def _field(policy: _P, value: str, witness_data: dict | None = None,
           validation: str | None = None) -> dict:
    return {"value": value,
            "source": policy.source,
            "validation": validation or policy.min_validation,
            "witness": policy.witness,
            "external_attestation": policy.min_attestation,
            "witness_data": dict(witness_data or {})}


def build_record(root: pathlib.Path, *, line: str, version: str,
                 round_no: int, commit_full: str, ts: str,
                 rs_path: pathlib.Path, probe_path: pathlib.Path,
                 launcher_path: pathlib.Path,
                 harness_captures: list[tuple[str, pathlib.Path]],
                 template_path: pathlib.Path,
                 transcript_path: pathlib.Path | None = None) -> dict:
    """Derive the record. Capture-backed fields come FROM the capture files;
    identity fields come from their own canonical carriers (package_identity,
    git, the spec headers) and are cross-checked by witness_problems()."""
    specs_dir = root / "specs"
    sys.path.insert(0, str(specs_dir))
    import closure_findings
    import package_identity as pid
    import seal_package as sp

    if transcript_path is None:
        import evidence_transcript
        transcript_path = root / evidence_transcript.REL_PATH

    launcher_line, launcher_exit, launcher_sha = derive_launcher(launcher_path)
    harness_block, harness_results = derive_harnesses(harness_captures)
    total_ev = len(closure_findings.CLOSURES)
    launcher_ev = sum(1 for c in closure_findings.CLOSURES
                      if "run_offline.sh" in c[6])
    evidence_text, observed = derive_evidence(transcript_path, total_ev,
                                              launcher_ev)
    specs = line.split("-")
    template_bytes = template_path.read_bytes()
    rel_template = template_path.resolve().relative_to(root.resolve())

    f = FIELD_POLICY
    fields = {
        "package": _field(f["package"], f"{line}-{version}"),
        "version": _field(f["version"], version),
        "round": _field(f["round"], str(round_no)),
        "candidates": _field(f["candidates"],
                             pid.render_candidate_field(line, version)),
        "commit": _field(f["commit"], commit_full[:7]),
        "commit_full": _field(f["commit_full"], commit_full),
        "requires": _field(f["requires"], derive_requires(specs, specs_dir)),
        "measured": _field(f["measured"], derive_measured(rs_path)),
        "harnesses": _field(f["harnesses"], harness_block,
                            {"results": harness_results}),
        "evidence": _field(f["evidence"], evidence_text,
                           {"observed": observed}),
        "extracted": _field(f["extracted"], render_extracted_list(sp)),
        "loose": _field(f["loose"], render_loose_lines(sp)),
        "context": _field(f["context"], derive_context(probe_path),
                          {"artifact": PROBE_CARRIER,
                           "sha256": hashlib.sha256(
                               probe_path.read_bytes()).hexdigest()}),
        "launcher": _field(f["launcher"], launcher_line,
                           {"artifact": LAUNCHER_CARRIER,
                            "sha256": launcher_sha,
                            "exit": launcher_exit}),
        "ts": _field(f["ts"], ts),
    }
    return {"record_version": RECORD_VERSION,
            "template": {"path": str(rel_template),
                         "sha256": hashlib.sha256(template_bytes).hexdigest()},
            "fields": fields}


def render_extracted_list(sp) -> str:
    return "\n                 ".join(
        f"{i + 1}. {n}" for i, (n, _) in enumerate(sp.EXTRACTION_CHECKS))


def render_loose_lines(sp) -> str:
    return "\n".join(f"  - {k}" for k in sorted(sp.LOOSE_CARRIERS))


def validate_record(record) -> list:
    """Every way a record can disagree with the registry or its own schema.

    Returns problems; empty means the record CONFORMS — it says nothing about
    whether its values are true (witness_problems answers that)."""
    p = []
    if not isinstance(record, dict):
        return [f"the record is {type(record).__name__}, not an object"]
    if sorted(record) != sorted(TOP_KEYS):
        return [f"top-level keys are {sorted(record)}, expected exactly "
                f"{sorted(TOP_KEYS)}"]
    if record["record_version"] != RECORD_VERSION:
        p.append(f"record_version is {record['record_version']!r}, this "
                 f"verifier implements {RECORD_VERSION}")
    t = record["template"]
    if not isinstance(t, dict) or sorted(t) != sorted(TEMPLATE_KEYS):
        p.append(f"template keys are "
                 f"{sorted(t) if isinstance(t, dict) else type(t).__name__}, "
                 f"expected exactly {sorted(TEMPLATE_KEYS)}")
    elif not (isinstance(t["sha256"], str)
              and re.fullmatch(r"[0-9a-f]{64}", t["sha256"])):
        p.append("template.sha256 is not a lowercase sha256 hex digest")

    fields = record["fields"]
    if not isinstance(fields, dict):
        return p + [f"fields is {type(fields).__name__}, not an object"]
    missing = sorted(set(FIELD_POLICY) - set(fields))
    extra = sorted(set(fields) - set(FIELD_POLICY))
    if missing:
        p.append(f"the registry names fields the record is missing: {missing}"
                 f" — absence is not exemption (blocking 1)")
    if extra:
        p.append(f"the record carries fields the registry does not name: "
                 f"{extra} — the schema is closed")

    for name in sorted(set(fields) & set(FIELD_POLICY)):
        f, pol = fields[name], FIELD_POLICY[name]
        if not isinstance(f, dict) or sorted(f) != sorted(FIELD_KEYS):
            p.append(f"{name}: keys are "
                     f"{sorted(f) if isinstance(f, dict) else type(f).__name__},"
                     f" expected exactly {sorted(FIELD_KEYS)}")
            continue
        if not isinstance(f["value"], str) or not f["value"]:
            p.append(f"{name}: value must be a non-empty string")
            continue
        # the four axes, each against the registry (blocking 1)
        if f["source"] not in SOURCES:
            p.append(f"{name}: unknown source {f['source']!r}")
        elif f["source"] != pol.source:
            p.append(f"{name}: source {f['source']!r} disagrees with the "
                     f"registry's {pol.source!r}")
        if f["validation"] not in VALIDATIONS:
            p.append(f"{name}: unknown validation {f['validation']!r}")
        elif _rank(VALIDATIONS, f["validation"]) < _rank(VALIDATIONS,
                                                         pol.min_validation):
            p.append(f"{name}: validation {f['validation']!r} is BELOW the "
                     f"registry minimum {pol.min_validation!r} — the record "
                     f"cannot downgrade its own scrutiny (blocking 1)")
        if f["witness"] not in WITNESSES:
            p.append(f"{name}: witness id {f['witness']!r} is not implemented "
                     f"— a refusal, not a skip (moderate 4)")
        elif f["witness"] != pol.witness:
            what = ("required witness removed" if f["witness"] == "none"
                    else "witness id changed")
            p.append(f"{name}: {what} — the registry requires "
                     f"{pol.witness!r}, the record says {f['witness']!r}")
        if f["external_attestation"] not in ATTESTATIONS:
            p.append(f"{name}: unknown external_attestation "
                     f"{f['external_attestation']!r}")
        elif _rank(ATTESTATIONS, f["external_attestation"]) < \
                _rank(ATTESTATIONS, pol.min_attestation):
            p.append(f"{name}: external_attestation below the registry "
                     f"minimum {pol.min_attestation!r}")
        wd = f["witness_data"]
        want = WITNESS_DATA_KEYS.get(f["witness"], None)
        if want is not None:
            if not isinstance(wd, dict) or sorted(wd) != sorted(want):
                p.append(f"{name}: witness_data keys are "
                         f"{sorted(wd) if isinstance(wd, dict) else type(wd).__name__},"
                         f" the {f['witness']!r} witness requires exactly "
                         f"{sorted(want)}")

    # internal consistencies the schema alone can see
    fv = {k: v.get("value") for k, v in fields.items()
          if isinstance(v, dict)}
    if {"commit", "commit_full"} <= set(fv):
        if not (isinstance(fv["commit_full"], str)
                and re.fullmatch(r"[0-9a-f]{40}", fv["commit_full"] or "")):
            p.append("commit_full is not a 40-hex commit id")
        elif fv["commit"] != fv["commit_full"][:7]:
            p.append(f"commit {fv['commit']!r} is not commit_full's 7-char "
                     f"prefix — two carriers of one value disagree")
    if {"package", "version"} <= set(fv) and isinstance(fv["package"], str) \
            and isinstance(fv["version"], str):
        if not fv["package"].endswith(f"-{fv['version']}"):
            p.append(f"package {fv['package']!r} does not end with the "
                     f"version {fv['version']!r}")
    if "ts" in fv and isinstance(fv["ts"], str) \
            and not TS_RE.fullmatch(fv["ts"]):
        p.append(f"ts {fv['ts']!r} is not strict `YYYYMMDDTHHMMZ` UTC (§5.4)")
    h = fields.get("harnesses")
    if isinstance(h, dict) and sorted(h.get("witness_data", {})) == ["results"]:
        res = h["witness_data"]["results"]
        ok_shape = (isinstance(res, list) and res and all(
            isinstance(r, list) and len(r) == 2
            and all(isinstance(x, str) and x for x in r) for r in res))
        if not ok_shape:
            p.append("harnesses.witness_data.results must be a non-empty "
                     "list of [script, result-line] string pairs")
        elif h.get("value") != render_harness_block(res):
            p.append("harnesses.value does not render from its own "
                     "witness_data.results — the two carriers disagree")
    l = fields.get("launcher")
    if isinstance(l, dict) and "exit" in l.get("witness_data", {}):
        if l["witness_data"]["exit"] != 0:
            p.append(f"launcher exit is {l['witness_data']['exit']!r} — a "
                     f"failed launcher cannot seal")
    e = fields.get("evidence")
    if isinstance(e, dict) and "observed" in e.get("witness_data", {}):
        if not isinstance(e["witness_data"]["observed"], int) \
                or e["witness_data"]["observed"] < 0:
            p.append("evidence.witness_data.observed must be a non-negative "
                     "integer")
    # the artifact names are PINNED to the canonical carriers: a redirected
    # artifact is a different witness wearing the right id, and a relative
    # path would let a witness read outside the extraction
    for fname, carrier in (("context", PROBE_CARRIER),
                           ("launcher", LAUNCHER_CARRIER)):
        fld = fields.get(fname)
        if isinstance(fld, dict) \
                and "artifact" in fld.get("witness_data", {}) \
                and fld["witness_data"]["artifact"] != carrier:
            p.append(f"{fname}: witness_data.artifact is "
                     f"{fld['witness_data']['artifact']!r}, the witness "
                     f"reads only {carrier!r}")
    return p


# ---------------------------------------------------------------------------
# The witness implementations (moderate 4): one per closed id.
# ---------------------------------------------------------------------------

def _ts_epoch(ts: str) -> int:
    return calendar.timegm(time.strptime(ts, TS_FORMAT))


def witness_problems(record: dict, root: pathlib.Path,
                     manifest_text: str | None = None,
                     overrides: dict | None = None,
                     only: set | None = None,
                     run_harnesses: bool = True) -> list:
    """Run each field's required witness against the carriers under `root`.

    `root` is an extraction root (or the repo at seal time). `overrides`
    maps a loose-carrier filename to an out-of-tree path — the sealer uses
    it before the archive exists; the extraction passes nothing. `only`
    restricts to named fields (unit tests isolate witnesses with it; the
    extraction verifier passes None and runs everything)."""
    problems = []
    fields = record.get("fields", {})
    ov = overrides or {}

    def path_of(name):
        return pathlib.Path(ov.get(name, root / name))

    def value(name):
        return fields[name]["value"]

    def active(name):
        return name in fields and (only is None or name in only)

    # -- pytest_rs: the measured line, re-derived from the shipped capture
    if active("measured"):
        try:
            got = derive_measured(path_of("COLLECTED_pytest_rs.txt"))
            if got != value("measured"):
                problems.append(f"measured: the record says "
                                f"{value('measured')!r}, the shipped -rs "
                                f"capture says {got!r}")
        except (OSError, RecordError) as e:
            problems.append(f"measured: {e}")

    # -- package_manifest: identity + commit agreement across the carrier
    man_fields = [n for n in ("package", "version", "round", "commit",
                              "commit_full") if active(n)]
    if man_fields:
        try:
            man = (manifest_text if manifest_text is not None
                   else path_of("PACKAGE_MANIFEST.txt").read_text())
        except OSError as e:
            problems.append(f"package_manifest witness: {e}")
            man = None
        if man is not None:
            mp = re.search(r"^PACKAGE:\s*(\S+)\s+—\s+external ROUND\s+(\d+)",
                           man, re.M)
            mc = re.search(r"^COMMIT:\s*([0-9a-f]{7,40})", man, re.M)
            if not mp:
                problems.append("package_manifest witness: the manifest has "
                                "no PACKAGE identity line")
            else:
                if active("package") and mp.group(1) != value("package"):
                    problems.append(f"package: record {value('package')!r} vs "
                                    f"manifest {mp.group(1)!r}")
                if active("version") and not mp.group(1).endswith(
                        f"-{value('version')}"):
                    problems.append(f"version: {value('version')!r} is not "
                                    f"the manifest package's version")
                if active("round") and mp.group(2) != value("round"):
                    problems.append(f"round: record {value('round')!r} vs "
                                    f"manifest {mp.group(2)!r}")
            if not mc:
                problems.append("package_manifest witness: the manifest has "
                                "no COMMIT line")
            else:
                for n in ("commit", "commit_full"):
                    if active(n) and not (
                            value(n).startswith(mc.group(1)[:7])
                            or mc.group(1).startswith(value(n)[:7])):
                        problems.append(f"{n}: record {value(n)!r} vs "
                                        f"manifest {mc.group(1)!r} — round "
                                        f"4's two-commit defect")

    # -- reviews_sent: the candidate field re-rendered from the identity
    #    record, which package_identity itself validates against reviews.py
    if active("candidates"):
        sys.path.insert(0, str(root / "specs"))
        try:
            import package_identity as pid
            for prob in pid.validate():
                problems.append(f"candidates: the identity record is "
                                f"invalid: {prob}")
            line = value("package")[: -len(value("version")) - 1] \
                if active("version") else None
            if line is not None:
                want = pid.render_candidate_field(line, value("version"))
                if want != value("candidates"):
                    problems.append(
                        f"candidates: the record's field does not re-render "
                        f"from package_identity for {line} "
                        f"{value('version')} (R17-1)")
        except Exception as e:            # noqa: BLE001 — the reason matters
            problems.append(f"candidates: reviews_sent witness failed: {e}")

    # -- spec_header: the requires block re-derived from the spec files
    if active("requires"):
        try:
            line = value("package")[: -len(value("version")) - 1]
            want = derive_requires(line.split("-"), root / "specs")
            if want != value("requires"):
                problems.append("requires: the record's block does not "
                                "re-derive from the spec files' own "
                                "Spec-Requires lines")
        except (RecordError, KeyError) as e:
            problems.append(f"requires: {e}")

    # -- harness_rerun: re-execute each recorded script, compare tails
    if active("harnesses"):
        res = fields["harnesses"]["witness_data"].get("results", [])
        if run_harnesses:
            for script, recorded in res:
                sp_path = root / script
                if not sp_path.exists():
                    problems.append(f"harnesses: {script} is not present to "
                                    f"re-run")
                    continue
                r = subprocess.run([sys.executable, script], cwd=root,
                                   capture_output=True, text=True)
                tail = (r.stdout.strip().splitlines() or [""])[-1].strip()
                if r.returncode != 0 or tail != recorded:
                    problems.append(
                        f"harnesses: re-running {script} gave exit "
                        f"{r.returncode}, tail {tail!r}; the record says "
                        f"{recorded!r}")

    # -- runtime_probe: the shipped artifact, digest-bound and re-derived
    if active("context"):
        wd = fields["context"]["witness_data"]
        ap = path_of(wd.get("artifact", PROBE_CARRIER))
        try:
            raw = ap.read_bytes()
            if hashlib.sha256(raw).hexdigest() != wd.get("sha256"):
                problems.append(f"context: {ap.name} does not match the "
                                f"record's digest — the capture moved after "
                                f"the record was derived")
            elif derive_context(ap) != value("context"):
                problems.append("context: the record's block does not "
                                "re-derive from the shipped probe artifact")
            elif active("ts"):
                # §5.4: the declared seal time is ordered AFTER measurement
                cap = load_probe(ap)["captured_at"]
                if _ts_epoch(value("ts")) < _ts_epoch(cap):
                    problems.append(f"ts: the declared seal time "
                                    f"{value('ts')} precedes the probe's "
                                    f"capture {cap} (§5.4 ordering)")
        except (OSError, RecordError, ValueError) as e:
            problems.append(f"context: {e}")

    # -- launcher_transcript: digest, exit, and result line from the artifact
    if active("launcher"):
        wd = fields["launcher"]["witness_data"]
        ap = path_of(wd.get("artifact", LAUNCHER_CARRIER))
        try:
            raw = ap.read_bytes()
            if hashlib.sha256(raw).hexdigest() != wd.get("sha256"):
                problems.append(f"launcher: {ap.name} does not match the "
                                f"record's digest")
            else:
                line, code, _sha = derive_launcher(ap)
                if code != wd.get("exit"):
                    problems.append(f"launcher: transcript exit {code} vs "
                                    f"recorded {wd.get('exit')!r}")
                if line != value("launcher"):
                    problems.append(f"launcher: the record's line "
                                    f"{value('launcher')!r} is not the "
                                    f"transcript's {line!r}")
        except (OSError, RecordError) as e:
            problems.append(f"launcher: {e}")

    # -- evidence_transcript: validate the shipped transcript, re-render
    if active("evidence"):
        sys.path.insert(0, str(root / "specs"))
        try:
            import closure_findings
            import evidence_transcript
            tpath = pathlib.Path(ov.get(evidence_transcript.REL_PATH,
                                        root / evidence_transcript.REL_PATH))
            tprob = evidence_transcript.validate(tpath, root / "specs")
            problems.extend(f"evidence: {x}" for x in tprob)
            total = len(closure_findings.CLOSURES)
            launcher_ev = sum(1 for c in closure_findings.CLOSURES
                              if "run_offline.sh" in c[6])
            want, observed = derive_evidence(tpath, total, launcher_ev)
            if want != value("evidence"):
                problems.append("evidence: the record's claim does not "
                                "re-derive from the shipped transcript and "
                                "the closure registry")
            if observed != fields["evidence"]["witness_data"].get("observed"):
                problems.append(f"evidence: witness_data.observed disagrees "
                                f"with the transcript ({observed} commands)")
        except Exception as e:            # noqa: BLE001 — the reason matters
            problems.append(f"evidence: {e}")

    # -- extraction_registry: both lists re-rendered from the code registry
    if active("extracted") or active("loose"):
        sys.path.insert(0, str(root / "specs"))
        try:
            import seal_package as sp
            if active("extracted") \
                    and render_extracted_list(sp) != value("extracted"):
                problems.append("extracted: the rendered check list is not "
                                "the code registry's (R8-2: one list, "
                                "generated once)")
            if active("loose") and render_loose_lines(sp) != value("loose"):
                problems.append("loose: the rendered carrier list is not "
                                "LOOSE_CARRIERS")
        except Exception as e:            # noqa: BLE001 — the reason matters
            problems.append(f"extracted/loose: {e}")

    # -- none (ts): structural checks only; wall-clock truth stays declared
    #    unattested (§5.4, ruling 2)
    if active("ts") and TS_RE.fullmatch(value("ts") or ""):
        now = int(time.time())
        if _ts_epoch(value("ts")) > now + TS_FUTURE_TOLERANCE_S:
            problems.append(
                f"ts: {value('ts')} is in the verifier's future beyond the "
                f"declared {TS_FUTURE_TOLERANCE_S}s tolerance (§5.4)")
    return problems
