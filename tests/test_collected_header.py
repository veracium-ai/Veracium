"""C-plus — the ruled COLLECTED-header construction (COLLECTED_HEADER_DESIGN §5).

The three blocking findings, each with its adversarial regression:

  blocking 1 — the record must not choose its own scrutiny: the mutation
               matrix is GENERATED from the record schema × the code-owned
               policy registry (§5.1.7), so every field is crossed with value
               mutations, validation DOWNGRADES, changed witness ids, and
               removal of a required witness — the downgrade mutations are
               the ones blocking 1 exists for.
  blocking 2 — the seam between two verified artifacts: COLLECTED.txt is one
               whole-file equation; bytes between blocks, duplicated blocks,
               trailing prose, and a displaced header are each injected.
  blocking 3 — agreement is vacuous when both sides share a source: the
               derive_* functions read CAPTURE FILES, and changing the file
               changes the record.
"""
import copy
import hashlib
import json
import pathlib
import sys
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "specs"))

import collected_record as CR                                   # noqa: E402
import collected_render as CX                                   # noqa: E402
import package_identity as pid                                  # noqa: E402
import runtime_probe                                            # noqa: E402
import seal_package as sp                                       # noqa: E402
import skip_inventory as S                                      # noqa: E402

LINE = sorted(pid.PACKAGES)[-1]
VERSION = sorted(pid.PACKAGES[LINE], key=lambda v: int(v[1:]))[-1]
ROUND = pid.PACKAGES[LINE][VERSION][0]
COMMIT = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"

# every required header token once, plus static prose around them
TEMPLATE = (
    "PKG __VERSION__ round __ROUND__ at __TS__ commit __COMMIT__\n"
    "__CANDIDATES__\nrequires: __REQUIRES__\nmeasured: __MEASURED__\n"
    "context:\n  __CONTEXT__\nlauncher: __LAUNCHER__\n"
    "harnesses: __HARNESSES__\nevidence: __EVIDENCE__\n"
    "extracted: __EXTRACTED__\nstatic prose the template owns\n")
MANIFEST_TEMPLATE = ("PACKAGE: __PACKAGE__ — external ROUND __ROUND__\n"
                     "COMMIT: __COMMIT_FULL__\ncandidates:\n__CANDIDATES__\n"
                     "loose:\n__LOOSE__\n")
RS = ("...........\n1779 passed, 8 skipped, 25 warnings in 100.00s "
      "(0:01:40)\n")


def _captures(tmp: pathlib.Path) -> dict:
    """Synthetic captured raw outputs — the immutable files the record
    derives from (blocking 3)."""
    rs = tmp / "pytest_rs.txt"
    rs.write_text(RS)
    probe = tmp / CR.PROBE_CARRIER
    probe.write_text(json.dumps({
        k: {"captured_at": "20260801T0000Z"}.get(k, f"probe-{k}")
        for k in runtime_probe.PROBE_KEYS}))
    launcher = tmp / CR.LAUNCHER_CARRIER
    launcher.write_text("venv built\n1779 passed, 8 skipped (launcher)\n"
                        "--- LAUNCHER EXIT: 0 ---\n")
    h1 = tmp / "h1.txt"
    h1.write_text("18/18 checks passed\n")
    h2 = tmp / "h2.txt"
    h2.write_text("store: 12/12 concurrent checks passed\n")
    transcript = tmp / "evidence_run.json"
    transcript.write_text(json.dumps(
        {"commands": [{"argv": ["x"], "exit": 0}] * 3}))
    return {"rs": rs, "probe": probe, "launcher": launcher,
            "harnesses": [("specs/evidence/x/h1.py", h1),
                          ("specs/evidence/x/h2.py", h2)],
            "transcript": transcript}


def _record(tmp: pathlib.Path) -> dict:
    """The record via the REAL constructor, from the synthetic captures and
    a template placed where build_record requires one: inside the tree it
    must ship from."""
    cap = _captures(tmp)
    tpl = ROOT / "specs" / "package" / ".test_cplus_template.txt"
    mtpl = ROOT / "specs" / "package" / ".test_cplus_manifest.txt"
    tpl.write_text(TEMPLATE)
    mtpl.write_text(MANIFEST_TEMPLATE)
    try:
        return CR.build_record(
            ROOT, line=LINE, version=VERSION, round_no=ROUND,
            commit_full=COMMIT, ts=time.strftime("%Y%m%dT%H%MZ",
                                                 time.gmtime()),
            rs_path=cap["rs"], probe_path=cap["probe"],
            launcher_path=cap["launcher"],
            harness_captures=cap["harnesses"],
            template_path=tpl, manifest_template_path=mtpl,
            transcript_path=cap["transcript"])
    finally:
        tpl.unlink(missing_ok=True)
        mtpl.unlink(missing_ok=True)


def test_the_clean_construction_conforms_renders_and_recomputes(tmp_path):
    r = _record(tmp_path)
    assert CR.validate_record(r) == []
    col = CX.compose(r, TEMPLATE, RS)
    assert CX.whole_file_problems(col, r, TEMPLATE, RS) == []
    # and the file is fully owned: header at byte zero, one inventory
    # block, EOF after the final newline
    assert col.startswith("PKG ") and col.endswith(S.END_MARKER + "\n")
    assert col.count(S.BEGIN_MARKER) == 1


def _mutations(record):
    """§5.1.7: the matrix is GENERATED from the schema and the registry —
    enumeration has no cell to overlook."""
    for name, pol in CR.FIELD_POLICY.items():
        m = copy.deepcopy(record)
        m["fields"][name]["value"] += " tampered"
        yield f"{name}: value mutated", name, m
        # BOTH rank directions (impl-review round 1, F1: the downgrade-only
        # generator encoded the same one-directional assumption as the
        # minimum-only rule it tested — false confidence is the same defect
        # as false modesty)
        for other_v in CR.VALIDATIONS:
            if other_v == pol.min_validation:
                continue
            m = copy.deepcopy(record)
            m["fields"][name]["validation"] = other_v
            way = ("DOWNGRADED" if CR.VALIDATIONS.index(other_v)
                   < CR.VALIDATIONS.index(pol.min_validation)
                   else "ESCALATED without proof")
            yield f"{name}: validation {way} to {other_v}", name, m
        for other_a in CR.ATTESTATIONS:
            if other_a == pol.min_attestation:
                continue
            m = copy.deepcopy(record)
            m["fields"][name]["external_attestation"] = other_a
            yield (f"{name}: attestation claimed {other_a} without a "
                   f"verifier"), name, m
        for other in CR.WITNESSES:
            if other == pol.witness:
                continue
            m = copy.deepcopy(record)
            m["fields"][name]["witness"] = other
            what = "required witness REMOVED" if other == "none" \
                else f"witness id changed to {other}"
            yield f"{name}: {what}", name, m
        m = copy.deepcopy(record)
        del m["fields"][name]
        yield f"{name}: field removed", None, m
        m = copy.deepcopy(record)
        m["fields"][name]["source"] = \
            "registry" if pol.source != "registry" else "git"
        yield f"{name}: source reassigned", name, m
        m = copy.deepcopy(record)
        m["fields"][name]["smuggled"] = "x"
        yield f"{name}: extra key inside the field", name, m
        m = copy.deepcopy(record)
        m["fields"][name]["witness"] = "notarised_blockchain"
        yield f"{name}: unknown witness id", name, m
        m = copy.deepcopy(record)
        m["fields"][name]["external_attestation"] = "vibes"
        yield f"{name}: unknown attestation", name, m
    m = copy.deepcopy(record)
    m["fields"]["bonus_claim"] = copy.deepcopy(record["fields"]["ts"])
    yield "a field the registry does not name", None, m
    m = copy.deepcopy(record)
    m["sidecar"] = {}
    yield "an extra top-level key", None, m
    m = copy.deepcopy(record)
    m["record_version"] = 99
    yield "a record_version this verifier does not implement", None, m


def test_every_generated_mutation_is_refused(tmp_path):
    """Three refusal tiers, in the construction's own order: the registry
    check, then the whole-file equation, then the field's witness. Fields
    that render only in the manifest (in_header=False) have no bytes in
    COLLECTED.txt — their value mutations MUST fall to the witness tier,
    which is exactly what the registry's required witness is for."""
    r = _record(tmp_path)
    col = CX.compose(r, TEMPLATE, RS)
    man = CX.render_manifest(r, MANIFEST_TEMPLATE)
    cap_over = {"COLLECTED_pytest_rs.txt": tmp_path / "pytest_rs.txt",
                CR.PROBE_CARRIER: tmp_path / CR.PROBE_CARRIER,
                CR.LAUNCHER_CARRIER: tmp_path / CR.LAUNCHER_CARRIER}
    count = 0
    for label, field, mutant in _mutations(r):
        count += 1
        refused = (CR.validate_record(mutant)
                   or CX.whole_file_problems(col, mutant, TEMPLATE, RS)
                   or (field is not None and CR.witness_problems(
                       mutant, ROOT, manifest_text=man, overrides=cap_over,
                       only={field}, run_harnesses=False)))
        assert refused, f"NOT refused: {label}"
    # the matrix really enumerated: every field crossed with every kind
    assert count > len(CR.FIELD_POLICY) * 5


def test_the_seams_are_owned(tmp_path):
    """blocking 2: each injection lives BETWEEN parts the old per-fact
    checks each individually accepted."""
    r = _record(tmp_path)
    col = CX.compose(r, TEMPLATE, RS)
    block = col[col.index(S.BEGIN_MARKER):]
    seams = {
        "header displaced off byte zero": "\n" + col,
        "undeclared bytes between header and inventory":
            col.replace(S.BEGIN_MARKER, "smuggled prose\n" + S.BEGIN_MARKER,
                        1),
        "duplicated inventory block": col + block,
        "trailing prose after the permitted final newline":
            col + "P.S. all fine\n",
        "inventory block deleted": col.replace(block, ""),
    }
    for label, bad in seams.items():
        assert CX.whole_file_problems(bad, r, TEMPLATE, RS), \
            f"NOT refused: {label}"


def test_the_record_derives_from_the_capture_not_the_variables(tmp_path):
    """blocking 3: the value comes FROM the file; change the file, the
    record changes. None of the derive functions accepts the value it
    returns."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("x\n10 passed in 1.00s\n")
    b.write_text("x\n11 passed in 1.00s\n")
    assert CR.derive_measured(a) != CR.derive_measured(b)

    p = tmp_path / "p.json"
    payload = {k: {"captured_at": "20260801T0000Z"}.get(k, f"v-{k}")
               for k in runtime_probe.PROBE_KEYS}
    p.write_text(json.dumps(payload))
    before = CR.derive_context(p)
    payload["sqlite"] = "3.99.0-injected"
    p.write_text(json.dumps(payload))
    assert CR.derive_context(p) != before

    # a probe artifact with an extra key (or a missing one) is refused —
    # the capture format is closed too
    payload["bonus"] = "x"
    p.write_text(json.dumps(payload))
    with pytest.raises(CR.RecordError):
        CR.derive_context(p)


def test_capture_witnesses_bind_digests_and_content(tmp_path):
    r = _record(tmp_path)
    cap_over = {"COLLECTED_pytest_rs.txt": tmp_path / "pytest_rs.txt",
                CR.PROBE_CARRIER: tmp_path / CR.PROBE_CARRIER,
                CR.LAUNCHER_CARRIER: tmp_path / CR.LAUNCHER_CARRIER}
    ok = CR.witness_problems(r, ROOT, overrides=cap_over,
                             only={"measured", "context", "launcher", "ts"})
    assert ok == []
    # the capture moved after the record was derived → digest refusal
    (tmp_path / CR.PROBE_CARRIER).write_text(
        (tmp_path / CR.PROBE_CARRIER).read_text().replace(
            "probe-sqlite", "3.99.0"))
    assert any("digest" in p for p in CR.witness_problems(
        r, ROOT, overrides=cap_over, only={"context"}))
    # a launcher transcript whose recorded exit is not the artifact's
    m = copy.deepcopy(r)
    m["fields"]["launcher"]["witness_data"]["exit"] = 2
    lt = tmp_path / CR.LAUNCHER_CARRIER
    lt.write_text(lt.read_text().replace("EXIT: 0", "EXIT: 2"))
    m["fields"]["launcher"]["witness_data"]["sha256"] = \
        hashlib.sha256(lt.read_bytes()).hexdigest()
    assert CR.validate_record(m), "a non-zero launcher exit must refuse"
    # the measured line disagreeing with the shipped -rs capture
    m = copy.deepcopy(r)
    m["fields"]["measured"]["value"] = "9999 passed in 1.00s"
    assert any("measured" in p for p in CR.witness_problems(
        m, ROOT, overrides=cap_over, only={"measured"}))
    # a REDIRECTED artifact — the right witness id reading the wrong file
    # (including a traversal out of the extraction) — refuses at validation
    for fname in ("context", "launcher"):
        m = copy.deepcopy(r)
        m["fields"][fname]["witness_data"]["artifact"] = "../outside.json"
        assert any("artifact" in p for p in CR.validate_record(m)), fname


def test_impl_review_round1_regressions(tmp_path):
    """The reviewer's four recommended regressions, each their exact attack
    against the live specimen, done first:

    F1: rank escalation and unearned attestation (in the generated matrix
    now — asserted here by name so the cells cannot silently vanish).
    F2: a forged full commit sharing the 7-char prefix; duplicate/trailing
    identity claims; stale hand-maintained dynamic prose — all three fell
    to the partial witness; the whole-manifest equation owns every byte.
    F3: member mtimes exactly at the declared seal epoch."""
    r = _record(tmp_path)
    man = CX.render_manifest(r, MANIFEST_TEMPLATE)

    # F1, by name: both escalations refuse at validation
    m = copy.deepcopy(r)
    m["fields"]["context"]["validation"] = "independent_cross_check"
    assert any("ABOVE" in p for p in CR.validate_record(m))
    m = copy.deepcopy(r)
    m["fields"]["ts"]["external_attestation"] = "signed_ci"
    assert any("signed_ci" in p for p in CR.validate_record(m))

    # F2a: a forged 40-char commit sharing only the short prefix
    m = copy.deepcopy(r)
    forged = COMMIT[:7] + "f" * 33
    m["fields"]["commit_full"]["value"] = forged
    assert any("all 40" in p for p in CR.witness_problems(
        m, ROOT, manifest_text=man, only={"commit_full"}))
    # ...and the whole-manifest equation catches it from the other side
    assert CX.manifest_problems(man, m, MANIFEST_TEMPLATE)

    # F2b: duplicate/trailing identity claims — the first-match read is gone
    forged_man = man + "PACKAGE: forged-v999 — external ROUND 999\n" \
                 + "COMMIT: " + "0" * 40 + "\n"
    assert any("expected exactly one" in p for p in CR.witness_problems(
        r, ROOT, manifest_text=forged_man,
        only={"package", "round", "commit_full"}))
    assert CX.manifest_problems(forged_man, r, MANIFEST_TEMPLATE)

    # F2c: stale dynamic prose — ANY byte the render does not produce refuses
    assert CX.manifest_problems(
        man.replace("candidates:", "candidates (draft v999):"), r,
        MANIFEST_TEMPLATE)

    # F3: appended members are STAMPED with the seal epoch and verified
    # exactly — no tolerance
    import calendar, tarfile, time as _t
    epoch = calendar.timegm(_t.strptime(r["fields"]["ts"]["value"],
                                        "%Y%m%dT%H%MZ"))
    old_archives = sp.ARCHIVES
    try:
        sp.ARCHIVES = tmp_path
        arc = sp.build_archive(".test-mtime", {"LOOSE_A.txt": "a\n"},
                               seal_epoch=epoch)
        with tarfile.open(arc) as tf:
            loose = [m2 for m2 in tf.getmembers()
                     if m2.name.endswith("LOOSE_A.txt")]
        assert loose and all(m2.mtime == epoch for m2 in loose), (
            "appended members must carry the DECLARED seal time exactly")
    finally:
        sp.ARCHIVES = old_archives


def test_manifest_witness_catches_cross_carrier_disagreement(tmp_path):
    r = _record(tmp_path)
    man = CX.render_manifest(r, MANIFEST_TEMPLATE)
    assert CR.witness_problems(
        r, ROOT, manifest_text=man,
        only={"package", "version", "round", "commit", "commit_full"}) == []
    m = copy.deepcopy(r)
    m["fields"]["round"]["value"] = str(ROUND + 1)
    assert any("round" in p for p in CR.witness_problems(
        m, ROOT, manifest_text=man, only={"round"}))
    m = copy.deepcopy(r)
    m["fields"]["commit"]["value"] = "beef000"
    m["fields"]["commit_full"]["value"] = "beef000" + "0" * 33
    assert any("commit" in p for p in CR.witness_problems(
        m, ROOT, manifest_text=man, only={"commit", "commit_full"}))


def test_timestamp_structure_without_pretending_truth(tmp_path):
    """§5.4: strict format, ordered after the capture, not in the
    verifier's future — consistency and plausibility, labelled; wall-clock
    truth stays declared unattested (witness `none`, attestation `none`)."""
    r = _record(tmp_path)
    assert r["fields"]["ts"]["witness"] == "none"
    assert r["fields"]["ts"]["external_attestation"] == "none"
    m = copy.deepcopy(r)
    m["fields"]["ts"]["value"] = "2026-08-22 01:00 UTC"
    assert any("ts" in p for p in CR.validate_record(m))
    m = copy.deepcopy(r)
    m["fields"]["ts"]["value"] = "21000101T0000Z"
    assert any("future" in p for p in CR.witness_problems(
        m, ROOT, only={"ts"}))
    m = copy.deepcopy(r)
    m["fields"]["ts"]["value"] = "20200101T0000Z"   # before the capture
    assert any("precedes" in p for p in CR.witness_problems(
        m, ROOT,
        overrides={CR.PROBE_CARRIER: tmp_path / CR.PROBE_CARRIER},
        only={"context", "ts"}))


def test_the_template_token_set_is_closed_both_ways(tmp_path):
    r = _record(tmp_path)
    with pytest.raises(CX.RenderError):
        CX.render_header(r, TEMPLATE + "and __SURPRISE__\n")
    with pytest.raises(CX.RenderError):
        CX.render_header(r, TEMPLATE.replace("__MEASURED__", "measured"))
    m = copy.deepcopy(r)
    m["fields"]["measured"]["value"] = "__COMMIT__ passed"
    with pytest.raises(CX.RenderError):
        CX.render_header(m, TEMPLATE)     # substitution injection


def test_the_registry_itself_is_closed_and_ranked():
    """The policy registry is the sole authority (blocking 1) — so its own
    shape is pinned: every axis value closed, every witness id implemented
    as a witness_data schema, the ranking axes ordered weakest-first."""
    assert CR.VALIDATIONS == ("syntax", "internal_consistency",
                              "independent_cross_check")
    assert CR.ATTESTATIONS == ("none", "signed_ci")
    assert sorted(CR.WITNESS_DATA_KEYS) == sorted(CR.WITNESSES)
    for name, pol in CR.FIELD_POLICY.items():
        assert pol.source in CR.SOURCES, name
        assert pol.min_validation in CR.VALIDATIONS, name
        assert pol.witness in CR.WITNESSES, name
        assert pol.min_attestation in CR.ATTESTATIONS, name
    # the loose-carrier names the sealer ships are the ones this module
    # derives digests for — one authority, asserted here AND at seal time
    for carrier in (CR.RECORD_CARRIER, CR.PROBE_CARRIER,
                    CR.LAUNCHER_CARRIER):
        assert carrier in sp.LOOSE_CARRIERS, carrier
    # the extraction registry runs the header verifier
    assert any(n == "verify_extracted.py header"
               for n, _ in sp.EXTRACTION_CHECKS)
    # measurement command: ONE authority — the sealer's measure() imports
    # the argv the probe records
    assert "pytest" in " ".join(runtime_probe.MEASUREMENT_ARGV)
    assert runtime_probe.MEASUREMENT_ENV["PYTHONPATH"] == "src"
