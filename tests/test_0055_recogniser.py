"""specs/0055 §4a: the recogniser, against research's reference model and adversarial table (I1, I2, I3, I8, I9).

The reference model and the table travel with the spec (specs/evidence/0055/reference_model.py, vectors.py, copied
byte for byte from research's evidence directory at the accepted v0.5.2). The product module is held to the
reference: the same findings, the same masked text and the same report on every row and on a seeded fuzz, so a change
to `veracium.credentials` that drifts from the accepted rule set goes RED here.

Every structural test token is assembled at run time by vectors.py, so none appears literally in this file.
"""
from __future__ import annotations

import importlib.util
import json
import os
import random
import re
import statistics
import sys
import time
import unicodedata
from pathlib import Path

import pytest

from veracium import credentials as P

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "specs" / "evidence" / "0055"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod      # the reference's frozen dataclass resolves its module by name
    spec.loader.exec_module(mod)
    return mod


REF = _load("_0055_reference_model", EVID / "reference_model.py")
VEC = _load("_0055_vectors", EVID / "vectors.py")
ROWS = VEC.ROWS


def _spans(findings):
    return [(f.cls, f.start, f.end) for f in findings]


def test_the_table_is_the_accepted_one():
    """150 rows at v0.5.7 (§6 I1; 122 at v0.5.2), derived from the vectors, with the groups the spec names: v0.5.7
    adds 18 glued rows (G1-G18), 8 near-misses (K48-K55) and 2 limits (X7, X8) for §4a's token boundary."""
    groups = {}
    for _rid, g, _t, _e in ROWS:
        groups[g] = groups.get(g, 0) + 1
    assert len(ROWS) == 150, len(ROWS)
    assert groups == {"witness": 1, "structural": 21, "glued": 18, "labelled": 23, "normalisation": 5,
                      "composition": 19, "near-miss": 55, "limit": 8}, groups
    assert len({r[0] for r in ROWS}) == len(ROWS), "a row id repeats"


@pytest.mark.parametrize("rid,group,text,expect", ROWS, ids=[r[0] for r in ROWS])
def test_every_row_matches_the_reference_and_its_exact_report(rid, group, text, expect):
    """I1/I2/I8 at the recogniser: the product's findings, masked text and report equal the reference's; the report
    equals the row's EXACT expected report (§4a "What a report counts"); a positive row leaves no secret value in
    the output; a near-miss or limit row is returned byte for byte."""
    assert _spans(P.scan(text)) == _spans(REF.scan(text))
    masked, report = P.mask(text)
    assert (masked, report) == REF.mask(text)
    assert report == VEC.expected_report(rid, expect)
    if group in ("near-miss", "limit") or not expect:
        assert masked == text and report == {}
    else:
        flat_in, flat_out = text.replace("\u200b", ""), masked.replace("\u200b", "")
        for sv in VEC.SECRET_VALUES:
            if sv in flat_in:
                assert sv not in flat_out, f"{rid}: a secret value survived masking"
    assert set(report) <= P.CLASSES and all(isinstance(n, int) and n > 0 for n in report.values())


def _curly(depth):
    return VEC._curly(depth)


def _inputs_for_inertness():
    out = [(rid, t) for rid, _g, t, _e in ROWS]
    out += [(f"curly{d}", _curly(d)) for d in range(0, 41)]
    return out


def test_the_completed_output_is_inert_and_text_idempotent():
    """I3: scan(mask(t)[0]) == [] and mask(mask(t)[0])[0] == mask(t)[0] for every row and every curly depth 0-40
    (the contract is on the text: a second call's report is empty by design, round 3's A1)."""
    for name, t in _inputs_for_inertness():
        m1, _ = P.mask(t)
        assert P.scan(m1) == [], name
        m2, rep2 = P.mask(m1)
        assert m2 == m1, name
        assert rep2 == {}, name


def test_the_fallback_is_reached_and_withholds_the_whole_value():
    """§4a: four passes, then the whole value as one `unmaskable_text` placeholder; depth 3 completes."""
    assert P.mask(_curly(3))[1] == {"labelled_password": 1}
    for d in (4, 5, 12, 40):
        assert P.mask(_curly(d)) == ("[credential withheld: unmaskable_text]", {"unmaskable_text": 1})


def test_mask_scans_at_most_five_times():
    """I3 / round 3's A1: one scan, then one after each pass; passes + 1 on completion, MAX_PASSES + 1 on the
    fallback. A spy counts scan() calls; the run must REACH no-shape (1), four-pass completion (5) and fallback (5)."""
    real = P.scan
    reached = set()
    try:
        for name, t in _inputs_for_inertness():
            _out, _held, passes, fell_back = P._run(t)
            n = [0]

            def spy(x, _n=n):
                _n[0] += 1
                return real(x)
            P.scan = spy
            try:
                P.mask(t)
            finally:
                P.scan = real
            want = P.MAX_PASSES + 1 if fell_back else passes + 1
            assert n[0] == want, (name, n[0], want)
            assert n[0] <= P.MAX_PASSES + 1, name
            reached.add("fallback" if fell_back else ("four" if passes == 4 else ("none" if passes == 0 else "some")))
    finally:
        P.scan = real
    assert {"none", "four", "fallback"} <= reached, reached


def test_a_second_scan_per_pass_is_red():
    """The control: v0.5.1's loop (a scan inside each pass and again before the next) is held RED by the same
    count, so the count above is not vacuous."""
    def v051(text):
        n = [0]
        real = P.scan

        def spy(x):
            n[0] += 1
            return real(x)
        P.scan = spy
        try:
            out, held = P._mask_once(text, [], P.scan(text))
            passes = 1
            while P.scan(out):
                if passes >= P.MAX_PASSES:
                    break
                out, held = P._mask_once(out, held, P.scan(out))
                passes += 1
        finally:
            P.scan = real
        return n[0]
    assert v051(_curly(4)) > P.MAX_PASSES + 1


def _fuzz_corpus(seed: int, n: int):
    frags = [t for _r, _g, t, _e in ROWS] + [
        "\ufb01", "\u2460", "\u338f", "\u2026", "e\u0301", "\u0130", "\u0131", "\u200d", "\u2060", "\u00ad",
        "\uff21\uff2b\uff29\uff21", "pa\u00adss", "\u30d1\u30b9\u30ef\u30fc\u30c9: abcd", "tok\u0130n is Ab3dEf9hJk2L",
        "pr\u0130vate key: hunter22", " ", "\n", '"', "\u201c", "\u201d", "'", "password: ", "token=", "PIN ", "my p\u0131n is 7351",
        "AUTHOR\u0130ZATION: Bearer " + "x" * 24, "B\u0130arer", "\u0130"]
    rng = random.Random(seed)
    for _ in range(n):
        yield "".join(rng.choice(frags) for _ in range(rng.randint(1, 6)))


def test_the_product_equals_the_reference_on_a_seeded_fuzz():
    """The prefilters, the ASCII fast path and the breakpoint offset map change speed only: findings, masked text and
    report equal the reference's on 4,000 seeded compositions of the table's rows with non-ASCII adversaries
    (expansions, drops, case-fold equivalents of "i")."""
    for t in _fuzz_corpus(20261122, 4000):
        assert _spans(P.scan(t)) == _spans(REF.scan(t)), repr(t)[:120]
        assert P.mask(t) == REF.mask(t), repr(t)[:120]


def test_each_prefilter_literal_is_necessary_for_its_pattern():
    """The structural prefilter is exact: every match of each structural pattern over the table and the fuzz contains
    one of its necessary literals (in the folded view for the two case-insensitive patterns); every LABELLED match
    contains a label stem and every PIN match "pin", folded."""
    texts = [t for _r, _g, t, _e in ROWS] + list(_fuzz_corpus(7, 1500))
    seen = set()
    for t in texts:
        view, _ = P._normalise(t)
        for cls, rx, lits, on_folded in P._STRUCT:
            for m in rx.finditer(view):
                s = P._fold(m.group(0)) if on_folded else m.group(0)
                assert any(lit in s for lit in lits), (cls, repr(t)[:80])
                seen.add(cls)
        for m in P.LABELLED.finditer(view):
            assert any(stem in P._fold(m.group(0)) for stem in P._LABEL_STEMS), repr(t)[:80]
        for m in P.PIN.finditer(view):
            assert "pin" in P._fold(m.group(0)), repr(t)[:80]
    assert len(seen) >= 18, sorted(seen)


def test_ignorecase_folds_no_other_non_ascii_letter_onto_ascii():
    """_fold's premise, over every code point on this interpreter: after NFKC, the only non-ASCII characters that
    IGNORECASE matches against an ASCII letter are U+0130 and U+0131."""
    rx = re.compile(r"(?i)[a-z]")
    odd = set()
    for cp in range(0x80, 0x110000):
        n = unicodedata.normalize("NFKC", chr(cp))      # the view holds the NFKC form, so that is what is matched
        if not n.isascii() and rx.fullmatch(n):
            odd.add(n)
    assert odd <= {"\u0130", "\u0131"}, sorted(hex(ord(c)) for c in odd)


def test_text_with_no_shape_is_returned_as_is():
    t = "I deploy every Friday."
    out, rep = P.mask(t)
    assert out is t and rep == {}


def test_credential_refused_names_the_field_and_class_never_the_value():
    value = "postgres://app:" + "s3cr3t" + "Pw@db.internal:5432/prod"
    e = P.CredentialRefused("source_id", P.first_class(value))
    assert isinstance(e, ValueError)
    assert (e.reason, e.field, e.cls) == ("credential_refused", "source_id", "url_userinfo_password")
    assert str(e) == "credential_refused: source_id carries a url_userinfo_password"
    assert "s3cr3t" not in str(e) and "db.internal" not in str(e)
    assert e.as_refusal() == {"ok": False, "refusal": "credential_refused", "field": "source_id",
                              "class": "url_userinfo_password"}
    assert P.first_class("chat:2026-11-22") is None      # an identifier with no shape is not refused


def test_the_placeholder_is_not_0041s_marker_and_is_inert():
    from veracium import redaction
    for cls in sorted(P.CLASSES):
        ph = P.PLACEHOLDER.format(cls=cls)
        assert P.scan(ph) == []
        assert redaction.MARKER not in ph and "\x00" not in ph


# ---- I9: time within a measured bound, at 256 KiB and 1 MiB --------------------------------------------------------

def _named_inputs():
    """§4a T1's named adversarial inputs (research's redos.py cases, the two-pass composition, the four-pass and
    fallback curly families)."""
    def curly(depth):
        return _curly(depth) + " "
    return {
        "pem_begin_repeated": "-----BEGIN " + "PRIVATE KEY-----\n",
        "label_repeated": "password: ",
        "label_no_value": "password is ",
        "url_userinfo": "a://b:c",
        "bearer": "bearer ",
        "jwt_prefix": "eyJabcdefgh.",
        "long_token": "A",
        "spaces": " ",
        "zero_width": "\u200b",
        "many_matches_one_run": "gh" + "p_" + "A" * 36 + "-",
        "scheme_chars_run": "a.b+c-d",
        "userinfo_no_at": "x://u:" + "p" * 50 + " ",
        "prose": "I deploy every Friday and the build is green. ",
        "composition_two_pass": 'password: "' + "a " * 79 + "gh" + "p_" + "B" * 36 + ' end" ',
        # v0.5.7 (§4a T1): the token boundary lets a prefix after `_` start a match, so a run of glued prefixes is a
        # start at every unit: one that fails a few characters short (hf_ wants 34), one whose body class takes the run
        "glued_short": "_" + "hf" + "_" + "A" * 33,
        "glued_body_run": "_" + "sk" + "-",
        "curly_depth3_four_pass": curly(3),
        "curly_depth4_fallback": curly(4),
    }


I9_SIZES = (256 * 1024, 1024 * 1024, 4 * 1024 * 1024)
I9_RATIO = 6.0
I9_CEILING_S = 2.0
# a ratio over tiny absolute times is noise, not growth: below 200 ms of CPU at 4 MiB (50 ms per MiB) a case is linear
# enough, and its ratio is recorded but not asserted
I9_FLOOR_S = 0.2
# the quadratic mutant's stride: a prefix count every this many characters, so its extra work grows as n**2
I9_QUAD_STRIDE = 1024
I9_QUAD_CASES = ("bearer", "pem_begin_repeated")


def _on_the_named_runner() -> bool:
    """The named CI runner: the tests workflow's pytest lanes (GitHub-hosted ubuntu-latest)."""
    return os.environ.get("GITHUB_ACTIONS") == "true" and bool(os.environ.get("VERACIUM_CI_SHARD"))


def _cpu_model():
    """The host's CPU model, for the record: a runner's cache sizes move the 256 KiB -> 1 MiB step."""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    import platform
    return platform.processor() or None


def _i9_measure(mask, inputs, runs=5):
    """Time `mask` on each input at I9_SIZES. Per size: the wall-clock median of the first three runs and the minimum
    thread CPU time over `runs`. The asserted ratio is 4 MiB over 1 MiB; 1 MiB over 256 KiB is recorded only.
    Returns (record, over_ratio, over_ceiling).

    The sizes are INTERLEAVED: each round times every size once, so a burst of another process's memory traffic falls
    on all sizes alike and each size's minimum comes from its quietest round. Timed one size after another, a burst
    of a few seconds could cover every run of one size: the gating suite at c2ecbfd2 (-n 8, beside 15 other
    sessions' pytest processes) read pem_begin_repeated over 6x, while eight copies of this test run concurrently
    read at most 4.47x, so sustained contention does not move the ratio and a transient one did.

    A case over the ratio is measured AGAIN, `runs` more interleaved rounds, and the minimum over all of them decides
    (the record's `rounds`). The statistic is unchanged, the minimum over rounds; only the number of rounds grows,
    and only where a burst may have landed on every round of one size. A superlinear recogniser reads over in every
    round, so the extra rounds cannot pass it (test_i9_a_quadratic_mask_reads_red). Under twelve processes copying
    96 MiB in 2 s bursts, one size after another read over 6x in 3 of 3 runs, interleaved alone in 1 of 3."""
    record, over_ratio, over_ceiling = [], [], []
    for name, unit in inputs.items():
        texts = [(unit * (size // len(unit) + 1))[:size] for size in I9_SIZES]
        walls = [[] for _ in I9_SIZES]
        cpu = [[] for _ in I9_SIZES]

        def rounds(n):
            for _ in range(n):
                for i, s in enumerate(texts):
                    c0, t0 = time.thread_time(), time.perf_counter()
                    mask(s)
                    walls[i].append(time.perf_counter() - t0)
                    cpu[i].append(time.thread_time() - c0)
        rounds(runs)
        cpus = [min(c) for c in cpu]
        if cpus[2] / max(cpus[1], 1e-9) > I9_RATIO and cpus[2] > I9_FLOOR_S:
            rounds(runs)                                   # measured again: the minimum over all rounds decides
            cpus = [min(c) for c in cpu]
        meds = [statistics.median(w[:3]) for w in walls]
        step = cpus[1] / max(cpus[0], 1e-9)
        ratio = cpus[2] / max(cpus[1], 1e-9)
        record.append({"case": name, "sizes_bytes": list(I9_SIZES), "median_s": [round(x, 4) for x in meds],
                       "cpu_min_s": [round(x, 4) for x in cpus], "ratio_256k_1m": round(step, 2),
                       "ratio": round(ratio, 2), "rounds": len(cpu[0])})
        if ratio > I9_RATIO and cpus[2] > I9_FLOOR_S:
            over_ratio.append(name)
        if meds[1] >= I9_CEILING_S:
            over_ceiling.append(name)
    return record, over_ratio, over_ceiling


def test_i9_the_recogniser_is_linear_on_the_named_inputs(record_testsuite_property):
    """I9 (§5): at most 6x the time for 4x the input, from 1 MiB to 4 MiB, and 1 MiB screens in under 2 s on the named
    CI runner. Off the runner the ratio is asserted and the absolute time is recorded only: a shared host's time is not
    the runner's (round 3's A1). The record goes to VERACIUM_0055_I9_RECORD when set, and always into the JUnit file as
    the testsuite property `veracium_0055_i9`: each CI lane's junit.xml is uploaded in its `ci-evidence-*` artifact and
    bound by sha256 in that artifact's manifest.json (.github/ci_run.py), so the runner's figures are collected from
    CI's own record without a workflow change. (`record_property` would warn under the default xunit2 family; an
    xdist worker's testsuite property does not reach the controller's file, and the CI lanes run without xdist.)

    Two clocks, one per claim. The RATIO is the growth of the recogniser's own work, so it is taken on this thread's
    CPU time, the minimum of five runs per size: wall time under a parallel suite charges the other workers' load to
    whichever size happens to run beside them (the gating suite at -n 8 read 6x+ on `label_no_value`, which reads
    4.0-4.6x alone), and a superlinear recogniser grows in CPU time as much as in wall time. The CEILING is a
    statement about wall time on the runner, so it stays the wall-clock median of three.

    Why 1 MiB -> 4 MiB and not 256 KiB -> 1 MiB: per-byte cost steps up once between those two sizes (the memory
    hierarchy; it stays with gc disabled) and is flat after it, and the step's height depends on the host's caches.
    Run 45275466884's py3.14-2 runner read 6.96x and 7.24x on the two label cases across that step while every other
    case read 3.77-4.15x; the label cases are the allocation-heavy ones (every repeat is a finding), and the same code
    reads about 4.2x from 1 MiB to 4 MiB. The small pair's ratio is recorded as `ratio_256k_1m`, not asserted."""
    record, over_ratio, over_ceiling = _i9_measure(P.mask, _named_inputs())
    import platform
    doc = {
        "about": "0055 I9: the product's mask() at 256 KiB, 1 MiB and 4 MiB; the asserted ratio is 4 MiB over 1 MiB on thread CPU time (min of five), 1 MiB over 256 KiB is recorded only; the ceiling on wall time at 1 MiB (median of three)",
        "algorithm": f"veracium.credentials.mask, at most MAX_PASSES + 1 = {P.MAX_PASSES + 1} scans",
        "named_runner": _on_the_named_runner(), "ci_shard": os.environ.get("VERACIUM_CI_SHARD"),
        "ci_job": os.environ.get("VERACIUM_CI_JOB_NAME"), "python": platform.python_version(),
        "machine": platform.machine(), "cpu_model": _cpu_model(), "cpus": os.cpu_count(),
        "load_at_end": [round(x, 2) for x in os.getloadavg()],
        "ratio_limit": I9_RATIO, "floor_s": I9_FLOOR_S, "ceiling_s": I9_CEILING_S, "cases": record}
    record_testsuite_property("veracium_0055_i9", json.dumps(doc, sort_keys=True))
    path = os.environ.get("VERACIUM_0055_I9_RECORD")
    if path:
        Path(path).write_text(json.dumps(doc, indent=1) + "\n")
    assert not over_ratio, (over_ratio, record)
    if _on_the_named_runner():
        assert not over_ceiling, (over_ceiling, record)


def test_i9_a_quadratic_mask_reads_red():
    """I9's RED: the same measurement flags a quadratic recogniser. The mutant is the product's mask() plus a prefix
    count every I9_QUAD_STRIDE characters, extra work that grows as the square of the input. A quadratic term with a
    fixed constant dominates only where the linear work is small, so the check runs on the two named inputs where it
    does at this stride (bearer, pem_begin_repeated), two runs per size; on the allocation-heavy label cases the same
    stride reads under 6x and would prove nothing either way."""
    def quadratic_mask(text):
        out = P.mask(text)
        for i in range(0, len(text), I9_QUAD_STRIDE):
            text.count("\x00", 0, i)
        return out

    inputs = {k: v for k, v in _named_inputs().items() if k in I9_QUAD_CASES}
    assert sorted(inputs) == sorted(I9_QUAD_CASES)
    record, over_ratio, _ = _i9_measure(quadratic_mask, inputs, runs=2)
    assert sorted(over_ratio) == sorted(I9_QUAD_CASES), record
