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
    """122 rows at v0.5.2 (§6 I1), derived from the vectors, with the groups the spec names."""
    groups = {}
    for _rid, g, _t, _e in ROWS:
        groups[g] = groups.get(g, 0) + 1
    assert len(ROWS) == 122, len(ROWS)
    assert groups == {"witness": 1, "structural": 21, "labelled": 23, "normalisation": 5, "composition": 19,
                      "near-miss": 47, "limit": 6}, groups
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
        "curly_depth3_four_pass": curly(3),
        "curly_depth4_fallback": curly(4),
    }


I9_SIZES = (256 * 1024, 1024 * 1024)
I9_RATIO = 6.0
I9_CEILING_S = 2.0


def _on_the_named_runner() -> bool:
    """The named CI runner: the tests workflow's pytest lanes (GitHub-hosted ubuntu-latest)."""
    return os.environ.get("GITHUB_ACTIONS") == "true" and bool(os.environ.get("VERACIUM_CI_SHARD"))


def test_i9_the_recogniser_is_linear_on_the_named_inputs():
    """I9 (§5): at most 6x the time for 4x the input, and 1 MiB screens in under 2 s on the named CI runner. Each
    timing is the median of three. Off the runner the ratio is asserted and the absolute time is recorded only:
    a shared host's time is not the runner's (round 3's A1). The record goes to VERACIUM_0055_I9_RECORD when set."""
    record, over_ratio, over_ceiling = [], [], []
    for name, unit in _named_inputs().items():
        meds = []
        for size in I9_SIZES:
            s = (unit * (size // len(unit) + 1))[:size]
            runs = []
            for _ in range(3):
                t0 = time.perf_counter()
                P.mask(s)
                runs.append(time.perf_counter() - t0)
            meds.append(statistics.median(runs))
        ratio = meds[1] / max(meds[0], 1e-9)
        record.append({"case": name, "sizes_bytes": list(I9_SIZES), "median_s": [round(x, 4) for x in meds],
                       "ratio": round(ratio, 2)})
        # a ratio over tiny absolute times is noise, not growth: below 50 ms at 1 MiB the case is linear enough
        if ratio > I9_RATIO and meds[1] > 0.05:
            over_ratio.append(name)
        if meds[1] >= I9_CEILING_S:
            over_ceiling.append(name)
    path = os.environ.get("VERACIUM_0055_I9_RECORD")
    if path:
        import platform
        Path(path).write_text(json.dumps({
            "about": "0055 I9: the product's mask() at 256 KiB and 1 MiB, median of three",
            "algorithm": f"veracium.credentials.mask, at most MAX_PASSES + 1 = {P.MAX_PASSES + 1} scans",
            "named_runner": _on_the_named_runner(), "python": platform.python_version(),
            "machine": platform.machine(), "cpus": os.cpu_count(), "load_at_end": [round(x, 2) for x in os.getloadavg()],
            "ratio_limit": I9_RATIO, "ceiling_s": I9_CEILING_S, "cases": record}, indent=1) + "\n")
    assert not over_ratio, (over_ratio, record)
    if _on_the_named_runner():
        assert not over_ceiling, (over_ceiling, record)
