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
    "__CANDIDATES__\n__HISTORY__\n__CHANGES__\n"
    "requires: __REQUIRES__\nmeasured: __MEASURED__\n"
    "context:\n  __CONTEXT__\nlauncher: __LAUNCHER__\n"
    "harnesses: __HARNESSES__\nevidence: __EVIDENCE__\n"
    "extracted: __EXTRACTED__\nstatic prose the template owns\n")
MANIFEST_TEMPLATE = ("PACKAGE: __PACKAGE__ — external ROUND __ROUND__\n"
                     "COMMIT: __COMMIT_FULL__\nBUILT: __TS__\n"
                     "measured: __MEASURED__\ncandidates:\n__CANDIDATES__\n"
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

    # F3 via the PURE helpers (R2-2: the first regression called
    # build_archive → `git archive`, so it could not run from a reviewer's
    # extraction — the named check never executed on their artifact. The
    # helpers ARE the builder's and verifier's code paths, git-free.)
    import calendar, tarfile, time as _t
    epoch = calendar.timegm(_t.strptime(r["fields"]["ts"]["value"],
                                        "%Y%m%dT%H%MZ"))
    info = tarfile.TarInfo("./LOOSE_A.txt")
    info.mtime = epoch + 999                     # write-time drift, as live
    stamped = sp.stamp_loose_member(info, epoch)
    assert stamped.mtime == epoch and stamped.uid == 0 \
        and stamped.mode == 0o644, (
        "the stamp must land EXACTLY on the declared seal epoch")
    assert sp.member_mtime_problems([("./a", epoch), ("./b", epoch - 5)],
                                    epoch) == []
    # the reviewer's injection: one second late must REFUSE, no tolerance
    assert sp.member_mtime_problems([("./late", epoch + 1)], epoch), (
        "seal_epoch + 1 must refuse — F3 is exact, not tolerance-bounded")


def test_impl_review_round2_regression_template_is_not_a_policy_source(
        tmp_path):
    """R2-1, the reviewer's exact full-repack attack: keep the legitimate
    __CANDIDATES__ token, plant a static `draft v999` candidate claim in the
    TEMPLATE, update the record's template digest, re-render the manifest —
    every prior check recomputes perfectly. The registry's manifest token
    policy plus the shared candidate-field sweep must refuse it anyway."""
    import hashlib
    r = _record(tmp_path)
    evil_tpl = MANIFEST_TEMPLATE + (
        "also shipping: specs/0001-generated-content-trust-class.md — "
        "draft v999 (external candidate)\n")
    m = copy.deepcopy(r)
    m["templates"]["manifest"]["sha256"] = hashlib.sha256(
        evil_tpl.encode()).hexdigest()          # step 4 of the attack
    evil_man = CX.render_manifest(m, evil_tpl)  # renders fine — tokens legal
    problems = CX.manifest_problems(evil_man, m, evil_tpl)
    assert any("OUTSIDE its verified field" in p for p in problems), (
        "a digest-bound template smuggling a static candidate claim must "
        "refuse (R2-1)")
    # the registry's token policy refuses the omission direction too: a
    # template that drops a required dynamic fact cannot render at all
    for f, pol in CR.FIELD_POLICY.items():
        if not pol.in_manifest:
            continue
        broken = MANIFEST_TEMPLATE.replace(CX.token_of(f), "static-claim")
        with pytest.raises(CX.RenderError):
            CX.render_manifest(r, broken)
    # ...and the duplication direction: the same token twice
    with pytest.raises(CX.RenderError):
        CX.render_manifest(r, MANIFEST_TEMPLATE + "BUILT again: __TS__\n")


def test_impl_review_round3_regression_field_is_position_and_label_bound(
        tmp_path):
    """C3-1, the reviewer's exact relocation attack: a static `specs: none`
    line on the real label, the correct rendered field behind a `backup:`
    prefix, template digest updated, manifest re-rendered — presence-bound
    checking accepted it whole. The shared position-and-label helper must
    refuse it on BOTH carriers."""
    import hashlib
    import package_identity as pid
    r = _record(tmp_path)
    evil_tpl = MANIFEST_TEMPLATE.replace(
        "candidates:\n__CANDIDATES__",
        "specs: none — no external candidates\nbackup: __CANDIDATES__")
    m = copy.deepcopy(r)
    m["templates"]["manifest"]["sha256"] = hashlib.sha256(
        evil_tpl.encode()).hexdigest()
    evil_man = CX.render_manifest(m, evil_tpl)
    problems = CX.manifest_problems(evil_man, m, evil_tpl)
    assert any("BEGIN at the label's offset" in p or "specs:" in p
               for p in problems), (
        "the relocated field must refuse — presence is not position (C3-1)")
    # the same helper serves COLLECTED — one implementation, not a copy
    field = m["fields"]["candidates"]["value"]
    assert pid.candidate_field_problems(
        f"specs: none — nothing\nbackup: {field}\n", field, "X")
    # C4-1: END-bound. The prior form of this assertion was neutralized by
    # an `or True` tautology — the reviewer found the missing regression BY
    # the tautology. Their exact contradiction, refused:
    assert any("END at a line boundary" in p for p in
               pid.candidate_field_problems(
                   field + " — withdrawn; no external candidate is under "
                   "review\n", field, "X"))
    assert pid.candidate_field_problems(field + "\n", field, "X") == []
    assert pid.candidate_field_problems(field, field, "X") == []   # EOF form
    # ...and through the manifest carrier in full-repack shape: template
    # digest updated, manifest re-rendered with the trailing contradiction
    evil_tpl2 = MANIFEST_TEMPLATE.replace(
        "__CANDIDATES__",
        "__CANDIDATES__ — withdrawn; no external candidate is under review")
    m2 = copy.deepcopy(r)
    m2["templates"]["manifest"]["sha256"] = hashlib.sha256(
        evil_tpl2.encode()).hexdigest()
    evil_man2 = CX.render_manifest(m2, evil_tpl2)
    assert any("END at a line boundary" in p
               for p in CX.manifest_problems(evil_man2, m2, evil_tpl2))


def test_impl_review_round4_regression_wheelset_is_exact(tmp_path):
    """C4-2, the reviewer's exact mutation: remove a locked wheel, stand in
    a renamed duplicate of another locked wheel — count parity held and
    every digest appeared 'somewhere in the lock', so the first bootstrap
    ACCEPTED it. The verifier now binds each requirement to its own digest
    set via wheel METADATA and requires exact set equality."""
    import importlib.util
    import zipfile
    spec = importlib.util.spec_from_file_location(
        "verify_wheelset",
        ROOT / "specs" / "evidence" / "offline" / "verify_wheelset.py")
    vw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vw)

    def wheel(dirp, name, version, fname=None):
        p = dirp / (fname or f"{name}-{version}-py3-none-any.whl")
        with zipfile.ZipFile(p, "w") as z:
            z.writestr(f"{name}-{version}.dist-info/METADATA",
                       f"Name: {name}\nVersion: {version}\n")
        return p

    wa = wheel(tmp_path, "pkg-a", "1.0")
    wb = wheel(tmp_path, "pkg-b", "2.0")
    import hashlib as _h
    lock = tmp_path / "req.lock"
    lock.write_text(
        f"pkg-a==1.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n"
        f"pkg-b==2.0 --hash=sha256:{_h.sha256(wb.read_bytes()).hexdigest()}\n")
    assert vw.verify(tmp_path, lock) == []          # the clean control

    # THE MUTATION: pkg-b's wheel removed, a renamed copy of pkg-a's stands
    # in — count parity holds, every digest is 'in the lock'
    wb.unlink()
    (tmp_path / "pkg-b-2.0-py3-none-any.whl").write_bytes(wa.read_bytes())
    problems = vw.verify(tmp_path, lock)
    assert any("duplicate" in p for p in problems), problems
    assert any("NO wheel on disk" in p for p in problems), problems

    # digest bound to the RIGHT requirement: pkg-b restored with pkg-a's
    # hash listed under pkg-b refuses too
    (tmp_path / "pkg-b-2.0-py3-none-any.whl").unlink()
    wb2 = wheel(tmp_path, "pkg-b", "2.0")
    lock.write_text(
        f"pkg-a==1.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n"
        f"pkg-b==2.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n")
    assert any("permitted hashes" in p for p in vw.verify(tmp_path, lock))

    # C5-2: the lock GRAMMAR fails closed — an appended direct-reference
    # requirement sat outside the computed set and the first parser
    # silently ignored it
    lock.write_text(
        f"pkg-a==1.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n"
        f"pkg-b==2.0 --hash=sha256:{_h.sha256(wb2.read_bytes()).hexdigest()}\n"
        "extra-package @ file:///tmp/extra.whl --hash=sha256:" + "0" * 64
        + "\n")
    assert any("unsupported lock grammar" in p
               for p in vw.verify(tmp_path, lock))
    # duplicates and orphan continuations refuse too
    lock.write_text(
        f"pkg-a==1.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n"
        f"pkg-a==1.0 --hash=sha256:{_h.sha256(wa.read_bytes()).hexdigest()}\n")
    assert any("duplicate declaration" in p
               for p in vw.verify(tmp_path, lock))


def test_impl_review_round6_regressions(tmp_path):
    """C6-1: history claims ONLY the governed domain — for every line,
    including 0022-0023 whose pre-record rounds are sealed (sidecars
    v3-v16), no 'document-only' inference survives. C6-2: the predecessor
    must be the IMMEDIATE one, sidecar-hash-verified — older-only,
    wrong-version, and wrong-hash all refuse."""
    for line, versions in pid.PACKAGES.items():
        for v in versions:
            h = CR.derive_line_history(line, v, pid.PACKAGES)
            assert "document-only" not in h, (line, v)
            assert "OUTSIDE this record's domain" in h, (line, v)
            assert "makes no claim" in h, (line, v)

    # C6-2 with a synthetic line: ledger v3/v4/v5, sealing round 6
    fake = {"9999": {"v3": (3, {}), "v4": (4, {}), "v5": (5, {})}}
    real = pid.PACKAGES
    old_archives = sp.ARCHIVES
    try:
        pid.PACKAGES = {**real, **fake}
        sp.ARCHIVES = tmp_path / "archives"
        sp.ARCHIVES.mkdir()
        outbox = tmp_path / "outbox"
        outbox.mkdir()
        # older-only: v3 present, v5 (the immediate predecessor) absent
        (outbox / "9999-v3-20260801T0000Z.tar.gz").write_bytes(b"x")
        r = sp.required_predecessor("9999", 6, outbox)
        assert isinstance(r, str) and "immediate predecessor" in r, r
        # wrong-hash: v5 present but sidecar disagrees
        p5 = outbox / "9999-v5-20260823T0000Z.tar.gz"
        p5.write_bytes(b"the archive")
        (sp.ARCHIVES / f"{p5.name}.sha256").write_text("0" * 64 + f"  {p5.name}\n")
        r = sp.required_predecessor("9999", 6, outbox)
        assert isinstance(r, str) and "sidecar" in r, r
        # clean: sidecar matches → the Path comes back
        import hashlib as _h
        (sp.ARCHIVES / f"{p5.name}.sha256").write_text(
            _h.sha256(b"the archive").hexdigest() + f"  {p5.name}\n")
        r = sp.required_predecessor("9999", 6, outbox)
        assert r == p5, r
        # no prior declared (round 3 is the line's first): the EXPLICIT
        # sentinel, never None (C8-2 — None reactivated the diff's
        # internal fallback selector)
        assert sp.required_predecessor("9999", 3, outbox) is sp.NO_PRIOR
        # ...and the diff, given the sentinel, emits the named skip and
        # SELECTS NOTHING even with an undeclared archive present
        (outbox / "9999-v2-20260823T0000Z.tar.gz").write_bytes(b"undeclared")
        txt = sp._changed_from_previous("9999", "v3", prior=sp.NO_PRIOR)
        assert "SKIPPED" in txt or "no prior" in txt.lower()
        assert "9999-v2" not in txt, (
            "the diff consumed an undeclared archive (C8-2)")
    finally:
        pid.PACKAGES = real
        sp.ARCHIVES = old_archives


def test_impl_review_round8_regressions(tmp_path):
    """C8-1: the lineage validates RECORDS — malformed content and a
    deleted non-in-flight witness both refuse. The in-flight exemption is
    the explicit declaration only."""
    real = pid.PACKAGES
    real_flight = pid.IN_FLIGHT
    try:
        pid.PACKAGES = {"9997": {"v1": (1, {}), "v2": (2, {})}}
        pid.IN_FLIGHT = ()
        d = tmp_path
        (d / "9997-v1-20260823T0000Z.tar.gz.sha256").write_text(
            "0" * 64 + "  9997-v1-20260823T0000Z.tar.gz\n")
        (d / "9997-v2-20260823T0100Z.tar.gz.sha256").write_text(
            "1" * 64 + "  9997-v2-20260823T0100Z.tar.gz\n")
        assert pid.lineage_problems(d) == []          # clean control
        # the reviewer's malformed-record mutation
        (d / "9997-v1-20260823T0000Z.tar.gz.sha256").write_text(
            "not-a-digest  wrong-target.tar.gz\n")
        assert any("C8-1" in x for x in pid.lineage_problems(d))
        # self-inconsistent target
        (d / "9997-v1-20260823T0000Z.tar.gz.sha256").write_text(
            "0" * 64 + "  some-other.tar.gz\n")
        assert any("its\n" not in x and "own name" in x
                   for x in pid.lineage_problems(d))
        # the reviewer's frontier-deletion mutation: v2's witness gone and
        # NOT declared in flight -> refuse
        (d / "9997-v1-20260823T0000Z.tar.gz.sha256").write_text(
            "0" * 64 + "  9997-v1-20260823T0000Z.tar.gz\n")
        (d / "9997-v2-20260823T0100Z.tar.gz.sha256").unlink()
        assert any("expected exactly one" in x
                   for x in pid.lineage_problems(d))
        # ...and permitted ONLY via the explicit declaration
        pid.IN_FLIGHT = ("9997-v2",)
        assert pid.lineage_problems(d) == []
    finally:
        pid.PACKAGES = real
        pid.IN_FLIGHT = real_flight


def test_impl_review_round9_regressions(tmp_path):
    """C9-1: the IN_FLIGHT exemption is CONSTRAINED — singleton, known
    row, genuinely absent sidecar. C9-2: ONE archive-name grammar for
    lineage witnesses, and unclaimed sidecars are flagged. C9-3: the
    NO_PRIOR skip speaks about the governed record, not the host."""
    real = pid.PACKAGES
    real_flight = pid.IN_FLIGHT
    real_first = pid.FIRST_GOVERNED
    try:
        pid.PACKAGES = {"9997": {"v1": (1, {}), "v2": (2, {})},
                        "9998": {"v1": (1, {})}}
        pid.FIRST_GOVERNED = {"9997": 1, "9998": 1}
        pid.IN_FLIGHT = ()
        d = tmp_path
        for name, fill in (("9997-v1-20260823T0000Z", "0"),
                           ("9997-v2-20260823T0100Z", "1"),
                           ("9998-v1-20260823T0200Z", "2")):
            (d / f"{name}.tar.gz.sha256").write_text(
                fill * 64 + f"  {name}.tar.gz\n")
        assert pid.lineage_problems(d) == []          # clean control
        # --- C9-1, the reviewer's exact attack: delete a committed
        # witness and WIDEN the declaration to cover it beside the real
        # seal — the widened declaration itself must refuse
        (d / "9997-v2-20260823T0100Z.tar.gz.sha256").unlink()
        pid.IN_FLIGHT = ("9998-v1", "9997-v2")
        assert any("singleton" in x for x in pid.lineage_problems(d)), (
            "a widened IN_FLIGHT let one seal ride another's exemption")
        # entry validity: unknown line, dead exemption, stale declaration
        pid.IN_FLIGHT = ("bogus",)
        assert any("known governed line" in x
                   for x in pid.lineage_problems(d))
        pid.IN_FLIGHT = ("9997-v9",)
        assert any("dead exemption" in x for x in pid.lineage_problems(d))
        pid.IN_FLIGHT = ("9997-v1",)      # v1's sidecar EXISTS -> stale
        assert any("stale declaration" in x
                   for x in pid.lineage_problems(d))
        # the honest declaration is still honored
        pid.IN_FLIGHT = ("9997-v2",)
        assert pid.lineage_problems(d) == []
        # --- C9-2: a SELF-CONSISTENT sidecar with a name the predecessor
        # selector cannot parse must not stand as a lineage witness
        pid.IN_FLIGHT = ()
        (d / "9997-v2-z.tar.gz.sha256").write_text(
            "1" * 64 + "  9997-v2-z.tar.gz\n")
        probs = pid.lineage_problems(d)
        assert any("C9-2" in x and "strict grammar" in x for x in probs), (
            "the malformed-name witness passed lineage while selection "
            "would ignore it — two grammars again")
        (d / "9997-v2-z.tar.gz.sha256").unlink()
        (d / "9997-v2-20260823T0100Z.tar.gz.sha256").write_text(
            "1" * 64 + "  9997-v2-20260823T0100Z.tar.gz\n")
        # ...and a sidecar naming a round INSIDE the governed domain
        # that no PACKAGES row claims is flagged, never silently ignored
        # — while a PRE-governed or foreign-line sidecar draws no claim
        # (C6-1: the sweep's own domain is the governed record)
        (d / "9997-v3-20260823T0300Z.tar.gz.sha256").write_text(
            "3" * 64 + "  9997-v3-20260823T0300Z.tar.gz\n")
        assert any("NO PACKAGES row claims" in x
                   for x in pid.lineage_problems(d))
        (d / "9997-v3-20260823T0300Z.tar.gz.sha256").unlink()
        (d / "9996-v1-20260823T0000Z.tar.gz.sha256").write_text(
            "3" * 64 + "  9996-v1-20260823T0000Z.tar.gz\n")
        assert pid.lineage_problems(d) == [], (
            "an unknown line is OUTSIDE the governed domain — no claim")
        (d / "9996-v1-20260823T0000Z.tar.gz.sha256").unlink()
        assert pid.lineage_problems(d) == []
        # --- C9-3: the skip message claims the governed record, not the
        # host's directory contents
        txt = sp._changed_from_previous("9997", "v1", prior=sp.NO_PRIOR)
        assert "SKIPPED" in txt and "governed record" in txt
        assert "was present" not in txt, (
            "the skip still speaks about host contents it never examined")
        # --- C9-2 also holds at the selector: both consumers share the
        # ONE grammar object
        assert pid.strict_archive_re("9997", "v2").fullmatch(
            "9997-v2-20260823T0100Z.tar.gz")
        assert not pid.strict_archive_re("9997", "v2").fullmatch(
            "9997-v2-z.tar.gz")
    finally:
        pid.PACKAGES = real
        pid.IN_FLIGHT = real_flight
        pid.FIRST_GOVERNED = real_first


def test_candidate_results_record_binds_the_measurement(tmp_path):
    """P1's matrix for measure_candidate.py + check_candidate_results.py
    (0001 R11-1: a carried focused count of 20 shipped while the branch
    ran 21). Every property the binding claims is exercised by a mutant
    violating exactly that property: a drifted focused count, a drifted
    full-suite triple, a record bound to a DIFFERENT patch, and a
    failure set whose size contradicts its own count. The pristine tree
    passes."""
    import json, shutil, subprocess, sys as _sys
    checker = ROOT / "specs" / "check_candidate_results.py"
    rec_path = ROOT / "specs" / "evidence" / "0001" / "candidate_results.json"
    patch_path = ROOT / "specs" / "evidence" / "0001" / "candidate.patch"
    if not (rec_path.exists() and patch_path.exists()):
        import pytest as _pytest
        _pytest.skip("candidate folded or absent — binding not applicable")

    def run(tree):
        return subprocess.run([_sys.executable, str(tree / "specs"
                                                    / checker.name)],
                              capture_output=True, text=True).returncode

    def tree_with(mutate_record=None, mutate_patch=None):
        w = tmp_path / f"t{len(list(tmp_path.iterdir()))}"
        (w / "specs" / "evidence" / "0001").mkdir(parents=True)
        shutil.copy2(checker, w / "specs" / checker.name)
        rec = json.loads(rec_path.read_text())
        if mutate_record:
            mutate_record(rec)
        (w / "specs" / "evidence" / "0001"
         / "candidate_results.json").write_text(json.dumps(rec, indent=1))
        text = patch_path.read_text()
        if mutate_patch:
            text = mutate_patch(text)
        (w / "specs" / "evidence" / "0001"
         / "candidate.patch").write_text(text)
        return w

    assert run(tree_with()) == 0, "the pristine binding must pass"
    # the round-11 defect itself: the README's focused count drifts
    assert run(tree_with(mutate_patch=lambda s: s.replace(
        "**21 passed**", "**20 passed**", 1))) != 0, (
        "a drifted README focused count passed — the R11-1 defect")
    # the full-suite triple drifts
    assert run(tree_with(mutate_record=lambda r: r["full_suite"].update(
        {"passed": r["full_suite"]["passed"] + 1}))) != 0, (
        "a drifted full-suite triple passed")
    # the record binds a DIFFERENT patch (bytes changed after measuring)
    assert run(tree_with(mutate_patch=lambda s: s + "\n# drift\n")) != 0, (
        "a record bound to different patch bytes passed")
    # the failure set contradicts its own count
    assert run(tree_with(mutate_record=lambda r: r["failure_set"].pop())) != 0, (
        "a failure set smaller than its count passed — the SET is the claim")


def test_terminus_proposal_is_an_archive_member():
    """PACKAGE-R23-1: a promised companion is a carrier. The terminus
    proposal must exist IN the tree (hence in every archive built from
    it), the spec must reference the in-archive path, and no
    side-channel accompanies-claim may survive outside the corrected
    historical notes."""
    proposal = ROOT / "specs" / "evidence" / "0024" / \
        "A1-CHECKER-TERMINUS-PROPOSAL.md"
    assert proposal.exists(), "the terminus proposal left the tree"
    spec = (ROOT / "specs"
            / "0024-authorship-before-structural-quarantine.md").read_text()
    assert "specs/evidence/0024/A1-CHECKER-TERMINUS-PROPOSAL.md" in spec
    assert "accompanies this package" not in spec, (
        "a live side-channel accompanies-claim survives (PACKAGE-R23-1)")


def test_a1_carrier_checker_mutation_matrix(tmp_path):
    """A1-R17-1's requested artifact, grown at A1-R18-1: the adversarial
    mutation matrix for check_a1_carriers — every property it claims is
    exercised by a mutant violating exactly that property. The cells are
    ENUMERATED here, never counted (round 18's editorial: a typed count
    of the cells drifted the day it was written): three §9 target
    removals, the restored singular form, the ledger-shadow (round 17),
    the plain obsolete-header restore, the same-section comment-shadow
    (round 18 — the live fragment inside an HTML comment while the
    obsolete row stands), round 19's pair (the outside-the-table stray
    line; the contradictory second row), round 20's pair (the malformed
    delimiter; the triple-backtick fenced table), round 21's
    fence-grammar pair (the tilde fence; the four-backtick fence), and
    round 22's context cells (multi-word info string; four-space
    indented code; the self-added shallow-fence and dead-fence indent
    boundary, one failing and one passing control), and round 23's
    closer-whitespace oracle (U+00A0/U+2000/U+3000/VT/FF suffixes leave
    the fence open; a tab-suffixed closer closes)."""
    import re, subprocess, sys as _sys
    import check_a1_carriers as cac
    spec_text = cac.SPEC.read_text()

    def run(mutated: str) -> int:
        f = tmp_path / "spec.md"
        f.write_text(mutated)
        return subprocess.run(
            [_sys.executable, str(ROOT / "specs" / "check_a1_carriers.py"),
             str(f)], capture_output=True, text=True).returncode

    assert run(spec_text) == 0, "the pristine spec must pass"
    live_row = "| **is a re-dispositioned record then able to SUPERSEDE?**"
    assert live_row in spec_text

    sec9 = re.search(r"^## 9\..*?(?=^## 10\.)", spec_text, re.M | re.S)
    assert sec9
    for target in ("§4b-iii step 1", "§4b-iii step 2", "§7b's"):
        mutated = spec_text.replace(
            sec9.group(0), sec9.group(0).replace(target, "REDACTED"))
        assert run(mutated) != 0, f"removing {target!r} from §9 passed"
    mutated = spec_text.replace(
        sec9.group(0),
        sec9.group(0) + "\n(the one-sentence step-2 replacement)\n")
    assert run(mutated) != 0, "restoring the singular form in §9 passed"

    # the ledger-shadow mutant, verbatim: the §4b-i row goes obsolete
    # while a ledger-like block elsewhere still QUOTES the live phrase
    shadow = spec_text.replace(
        live_row,
        "| **is a corrected user statement then able to SUPERSEDE?**", 1)
    shadow += ("\n| ledger row | the §4b-i header now reads 'is a "
               "re-dispositioned record then able to SUPERSEDE?' |\n")
    assert run(shadow) != 0, (
        "the ledger-shadow mutant passed — presence-somewhere stood in "
        "for presence-at-the-site again (A1-R17-1)")
    # and the plain restore, no shadow
    plain = spec_text.replace(
        live_row,
        "| **is a corrected user statement then able to SUPERSEDE?**", 1)
    assert run(plain) != 0, "the plain obsolete-header restore passed"

    # A1-R18-1's comment-shadow mutant, verbatim: the obsolete row stands
    # while the live fragment survives only inside an HTML comment IN the
    # same §4b-i section — mention is not use
    comment_shadow = spec_text.replace(
        live_row,
        "| **is a corrected user statement then able to SUPERSEDE?**"
        "\n<!-- is a re-dispositioned record then able to SUPERSEDE? "
        "| **is a re-dispositioned record then able to SUPERSEDE?** -->",
        1)
    assert run(comment_shadow) != 0, (
        "the same-section comment-shadow mutant passed — substring "
        "matching survived inside the right section (A1-R18-1)")
    # ...and the LINE-ANCHORED variant of the same shadow: a multi-line
    # comment can put the row fragment at a line start, so the checker
    # strips comments before matching (the property, recursed rather
    # than awaited)
    anchored_shadow = spec_text.replace(
        live_row,
        "| **is a corrected user statement then able to SUPERSEDE?**"
        "\n<!--\n| **is a re-dispositioned record then able to "
        "SUPERSEDE?**\n-->",
        1)
    assert run(anchored_shadow) != 0, (
        "the line-anchored comment-shadow passed — the anchor alone was "
        "not the property")

    # A1-R19-1's two mutants, verbatim. (1) outside-the-table: the
    # obsolete row stands IN the table; the live phrase sits on an
    # isolated pipe-prefixed line separated from it by prose
    live_line = None
    for line in spec_text.splitlines():
        if line.startswith(live_row):
            live_line = line
            break
    assert live_line is not None
    obsolete_line = live_line.replace(
        "is a re-dispositioned record then able to SUPERSEDE?",
        "is a corrected user statement then able to SUPERSEDE?", 1)
    outside = spec_text.replace(live_line, obsolete_line, 1).replace(
        "### 4c.",
        live_line + "\n\nprose separating the stray row\n\n### 4c.", 1)
    assert run(outside) != 0, (
        "an isolated pipe-prefixed live line outside the table passed as "
        "table membership (A1-R19-1 mutant 1)")
    # (2) contradictory carriers: the obsolete row ADDED above the live
    # one — two supersession-question rows in one table
    contradictory = spec_text.replace(
        live_line, obsolete_line + "\n" + live_line, 1)
    assert run(contradictory) != 0, (
        "two contradictory supersession rows passed as a live header "
        "(A1-R19-1 mutant 2)")

    # A1-R20-1's two mutants, verbatim. (1) the delimiter row replaced
    # by an ordinary two-cell row — consecutive pipe lines, but not a
    # Markdown table
    table_head = "| question | answer |\n|---|---|"
    assert table_head in spec_text
    no_delim = spec_text.replace(
        table_head, "| question | answer |\n| not | a delimiter |", 1)
    assert run(no_delim) != 0, (
        "a pipe block without a valid delimiter row passed as a table "
        "(A1-R20-1 mutant 1)")
    # (2) the whole table wrapped in a fenced code block — rendered as
    # code, not a table
    sec_b = re.search(r"^#### 4b-i\..*?(?=^#{2,4} )", spec_text,
                      re.M | re.S).group(0)
    tbl = re.search(r"^\| question \| answer \|\n(?:^\|.*\n)+",
                    sec_b, re.M).group(0)
    fenced = spec_text.replace(tbl, "```\n" + tbl + "```\n", 1)
    assert run(fenced) != 0, (
        "a fenced (code-rendered) table passed as a table "
        "(A1-R20-1 mutant 2)")
    # A1-R21-1's fence-grammar pair: tilde and four-backtick fences are
    # fences too — the regex for one literal form was a proxy for the
    # grammar
    tilde_fenced = spec_text.replace(tbl, "~~~\n" + tbl + "~~~\n", 1)
    assert run(tilde_fenced) != 0, (
        "a tilde-fenced table passed as a table (A1-R21-1 mutant 1)")
    four_fenced = spec_text.replace(tbl, "````\n" + tbl + "````\n", 1)
    assert run(four_fenced) != 0, (
        "a four-backtick-fenced table passed as a table "
        "(A1-R21-1 mutant 2)")

    # A1-R22-1's context pair. (1) a multi-word info string is a valid
    # fence opener
    info_fenced = spec_text.replace(
        tbl, "```text example\n" + tbl + "```\n", 1)
    assert run(info_fenced) != 0, (
        "a fence with a multi-word info string passed as a table "
        "(A1-R22-1 mutant 1)")
    # (2) a four-space-indented table renders as an indented CODE block
    indented = spec_text.replace(
        tbl, "".join("    " + ln + "\n" for ln in tbl.splitlines()), 1)
    assert run(indented) != 0, (
        "a four-space-indented (code-rendered) table passed as a table "
        "(A1-R22-1 mutant 2)")
    # self-exhausted same-class cells (P5, item 9 — the next mutants,
    # written now): a fence opener up to three spaces deep is STILL a
    # fence and must hide the table...
    shallow_fence = spec_text.replace(
        tbl, "  ```\n" + tbl + "  ```\n", 1)
    assert run(shallow_fence) != 0, (
        "a 2-space-indented fence was not honored as a fence")
    # ...while a FOUR-space-indented marker is code, not a fence — the
    # unindented table between such markers is real, and the checker
    # must still PASS (the positive control for the indent boundary)
    dead_fence = spec_text.replace(
        tbl, "    ```\n" + tbl + "    ```\n", 1)
    assert run(dead_fence) == 0, (
        "a 4-space-indented marker was honored as a fence — the indent "
        "boundary is wrong in the strict direction")

    # A1-R23-1's whitespace oracle: only SPACE and TAB may follow a
    # closing fence. The reviewer's U+00A0 repro plus the compact
    # domain: each non-space/tab whitespace suffix leaves the fence
    # OPEN (the table stays code-rendered -> checker must fail), while
    # a space/tab suffix CLOSES it (the table after the true closer is
    # real -> the mutant construction differs, so we assert via the
    # reviewer's exact shape: fake closer, table, genuine closer)
    for ws, label in ((chr(0x00A0), "U+00A0"), (chr(0x2000), "U+2000"),
                      (chr(0x3000), "U+3000"), ("\v", "vertical tab"),
                      ("\f", "form feed")):
        hidden = spec_text.replace(
            tbl, "```\n```" + ws + "\n" + tbl + "```\n", 1)
        assert run(hidden) != 0, (
            f"a {label}-suffixed line closed the fence — the closer "
            f"whitespace class is wider than CommonMark (A1-R23-1)")
    # EVIDENCE-M24-1: the space/tab positive controls are EXPLICIT
    # `== 0` assertions (the first form was `!= 0 or True` — a tautology
    # the reviewer proved could not fail by breaking the grammar under
    # it): fenced junk, a space- or tab-suffixed closer, then the
    # untouched table — the closer must close, the table must be real
    for ws, label in ((" ", "space"), ("\t", "tab")):
        positive = spec_text.replace(
            tbl, "```\njunk\n```" + ws + "\n" + tbl, 1)
        assert run(positive) == 0, (
            f"a {label}-suffixed closer was not honored — the strict "
            f"direction of the whitespace boundary is wrong")
    # ...and the reviewer's exact grammar mutant is PLANTED: a checker
    # whose closer class drops the space ([\t]* for [ \t]*) must FAIL
    # the space-positive control — proving the control can fail
    checker_src = (ROOT / "specs" / "check_a1_carriers.py").read_text()
    assert 'r"[ \\t]*"' in checker_src
    mutated = checker_src.replace('r"[ \\t]*"', 'r"[\\t]*"', 1)
    mchk = tmp_path / "mutated_checker.py"
    mchk.write_text(mutated)
    space_positive = spec_text.replace(
        tbl, "```\njunk\n``` \n" + tbl, 1)
    sf = tmp_path / "space_spec.md"
    sf.write_text(space_positive)
    r = subprocess.run([_sys.executable, str(mchk), str(sf)],
                       capture_output=True, text=True)
    assert r.returncode != 0, (
        "the [\\t]* grammar mutant passed the space-positive control — "
        "the control is still tautological (EVIDENCE-M24-1)")


def test_a1_patch_verifier_refuses_an_incomplete_tree():
    """PACKAGE-R15-1: the verifier accepted `1 named skip(s)` because it
    copied only the reference file and dev's installed veracium masked
    the hole (env-leak). Both cells are pinned: without the product tree
    the import-provenance witness refuses; with it the exact zero-skip
    result passes with veracium resolved from INSIDE the constructed
    tree."""
    import verify_a1_patch as vap
    if vap.PATCH.exists():
        assert vap.run_verification(copy_src=False) != 0, (
            "an incomplete tree must REFUSE — a skipped or masked vector "
            "is an unverified vector")
        assert vap.run_verification(copy_src=True) == 0
    else:
        # A1 accepted (round 24): the patch is FOLDED into the reference
        # and removed; the verifier's contract is the VISIBLE skip —
        # exit 0 either way, with the absence named
        assert vap.run_verification(copy_src=False) == 0
        assert vap.run_verification(copy_src=True) == 0


def test_baseline_validator_bites_on_a_planted_mutation(tmp_path):
    """Research's §VII condition on trusting the validator's green: a
    component that has not refused data it should refuse is presumed to
    be faking. A copy of the shipped bundle with ONE movement record's
    disclosure flipped must fail; the pristine copy must pass."""
    import json, shutil, subprocess, sys as _sys
    src = ROOT / "specs" / "evidence" / "0024" / "baseline"
    work = tmp_path / "baseline"
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("__pycache__"))
    r = subprocess.run([_sys.executable, str(work / "validate_baseline.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"pristine copy must pass: {r.stderr}"
    rec_path = work / "postfix_records.jsonl"
    rows = [json.loads(l) for l in rec_path.read_text().splitlines()]
    for row in rows:
        if row["probe_id"] == "b24-A08":
            for e in row["edges"]:
                if e.get("original_relation") == "third_party_claim":
                    e["disclosure"] = "quarantined"     # un-move A08
    rec_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    r = subprocess.run([_sys.executable, str(work / "validate_baseline.py")],
                       capture_output=True, text=True)
    assert r.returncode != 0, (
        "the planted mutation survived — the validator is faking (§VII)")

    # research's co-check cells (2026-08-24), plant-verified before riding:
    # (b) a canary-only mutation must bite — the first validator predated
    # the canary file and this exact mutation passed silently
    work2 = tmp_path / "baseline2"
    shutil.copytree(src, work2, ignore=shutil.ignore_patterns("__pycache__"))
    cpath = work2 / "canary_subject_records.jsonl"
    rows = [json.loads(l) for l in cpath.read_text().splitlines()]
    for row in rows:
        if row["probe_id"] == "b24-C04":
            for e in row["edges"]:
                e["subject"] = "user"
    cpath.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    r = subprocess.run([_sys.executable, str(work2 / "validate_baseline.py")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "canonicalizes" in r.stderr, (
        "the C04 user-subject mutation survived (research's co-check cell)")
    # EVIDENCE-R16-1 (the reviewer's deleted-subject mutant): an absent
    # or None subject must REFUSE — e.get("subject", "") silently
    # coerced absence into passing evidence
    for mutate in ("delete", "none"):
        workx = tmp_path / f"baseline_{mutate}"
        shutil.copytree(src, workx,
                        ignore=shutil.ignore_patterns("__pycache__"))
        cpx = workx / "canary_subject_records.jsonl"
        rowsx = [json.loads(l) for l in cpx.read_text().splitlines()]
        for row in rowsx:
            if row["probe_id"] == "b24-C04":
                for e in row["edges"]:
                    if mutate == "delete":
                        e.pop("subject", None)
                    else:
                        e["subject"] = None
        cpx.write_text("\n".join(json.dumps(r) for r in rowsx) + "\n")
        r = subprocess.run(
            [_sys.executable, str(workx / "validate_baseline.py")],
            capture_output=True, text=True)
        assert r.returncode != 0 and "ABSENCE IS NOT EVIDENCE" in r.stderr, (
            f"an {mutate}d canary subject passed as evidence "
            f"(EVIDENCE-R16-1)")
    # (a) an unknown digest-bound data file must refuse, not ride
    work3 = tmp_path / "baseline3"
    shutil.copytree(src, work3, ignore=shutil.ignore_patterns("__pycache__"))
    (work3 / "extra_measurements.jsonl").write_text('{"x": 1}\n')
    dig = work3 / "DIGESTS.sha256"
    dig.write_text(dig.read_text()
                   + "0" * 64 + "  extra_measurements.jsonl\n")
    r = subprocess.run([_sys.executable, str(work3 / "validate_baseline.py")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "NO validator check" in r.stderr, (
        "an unchecked bundle addition rode silently (closure over the "
        "unknown)")


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
