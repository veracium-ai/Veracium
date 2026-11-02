"""specs/0007 v24.1 §4e, INV-SA13: `veracium doctor` names what it compares.

Every listed attested build carries its source id's last 12 characters; on a `verified` build the doctor names the
nearest attested record of the SAME SQLite version (fewest differing key fields among every key field but the version;
an unreadable field differs; a tie goes to the first in the listing's own order), and exactly the fields that
differ; no record is named when none has the version; `attested` and `refused` builds get no such line; `--json`'s
`nearest_attested` carries the same record and fields. Each cell below is the one a named INV-SA13 mutant fails.
"""
from __future__ import annotations

import re

import pytest

from veracium import doctor
from veracium.store import schema_version as sv

V = "3.50.0"


FEATURES = {k: True for k in sv.FEATURE_KEYS}
DIGEST = "d" * 64


def _rec(version, source, machine, system, libc, route="r", digest=DIGEST, features=None):
    return {"sqlite_version": version, "source_id": source, "machine": machine, "system": system, "libc": libc,
            "features": dict(features or FEATURES), "compile_options_digest": digest,
            "provenance": [{"route": route, "runner_image": "img"}]}


def _status(status, source="S" * 20 + "running00000", platform=("x86_64", "Linux", "glibc"), version=V,
            digest=DIGEST, features=None):
    ident = {"sqlite_version": version, "source_id": source, "features": dict(features or FEATURES),
             "compile_options_digest": digest, "machine": platform[0], "system": platform[1], "libc": platform[2]}
    return sv.RuntimeStatus(status, None, sv.attestation_key(ident),
                            tuple(k for k, v in zip(("machine", "system", "libc"), platform) if v is None),
                            version, source, platform)


def _run(monkeypatch, records, status):
    """The runtime check over `records` fed through the artifact path itself (attestations → problems → revision), so
    the listing's own order and the artifact's order can differ."""
    monkeypatch.setattr(sv, "attestations", lambda *a, **k: list(records))
    monkeypatch.setattr(sv, "attestation_artifact_problems", lambda *a, **k: [])
    monkeypatch.setattr(sv, "attestation_revision", lambda *a, **k: "current")
    monkeypatch.setattr(sv, "runtime_status", lambda: status)
    rep = doctor.Report(db="(none)", readable=False)
    doctor._check_runtime(rep)
    return rep, doctor.render(rep)


def test_every_listed_build_carries_its_source_ids_last_12():
    """The real artifact: each listed string carries `(<the record's source_id[-12:]>)` right after its version."""
    rep = doctor.Report(db="(none)", readable=False)
    doctor._check_runtime(rep)
    records = [r for r in sv.attestations() if sv.attestation_revision(r) == "current"]
    assert rep.attested_builds and len(rep.attested_builds) == len(records)
    wanted = sorted(f"SQLite {r['sqlite_version']} ({r['source_id'][-12:]}) on" for r in records)
    matches = [re.match(r"^(SQLite \S+ \([^)]{12}\) on)", b) for b in rep.attested_builds]
    assert all(matches), [b for b, m in zip(rep.attested_builds, matches) if not m]   # a row without the part fails HERE
    assert sorted(m.group(1) for m in matches) == wanted


def test_the_nearest_record_and_exactly_the_fields_that_differ(monkeypatch):
    far = _rec(V, "A" * 20 + "aaaaaaaaaaaa", "aarch64", "Darwin", "none")
    near = _rec(V, "B" * 20 + "bbbbbbbbbbbb", "x86_64", "Linux", "glibc")
    rep, out = _run(monkeypatch, [far, near], _status("verified"))
    assert rep.nearest_attested == {"build": next(b for b in rep.attested_builds if "bbbbbbbbbbbb" in b),
                                    "differs": ["source_id"]}, rep.nearest_attested
    assert "nearest attested build of SQLite 3.50.0" in out and "differs in source_id" in out
    j = doctor.to_json(rep)
    assert j["nearest_attested"] == rep.nearest_attested and "nearest_line" not in j, sorted(j)


def test_an_unreadable_field_differs_never_matches(monkeypatch):
    """A field the running build could not read counts as DIFFERING: it is named among the differences (a matching
    reading would leave it out and call the build nearer than it is)."""
    rec = _rec(V, "S" * 20 + "running00000", "x86_64", "Linux", "glibc")
    rep, out = _run(monkeypatch, [rec], _status("verified", platform=("x86_64", "Linux", None)))
    assert "libc" in rep.nearest_attested["differs"] and "machine" not in rep.nearest_attested["differs"], \
        rep.nearest_attested


def test_a_record_of_another_version_is_never_named(monkeypatch):
    """A record of another SQLite version that matches every compared field is NOT a candidate; the record of the
    running version is, though it differs in all four."""
    other = _rec("3.51.0", "S" * 20 + "running00000", "x86_64", "Linux", "glibc")
    same = _rec(V, "Z" * 20 + "zzzzzzzzzzzz", "aarch64", "Darwin", "none")
    rep, out = _run(monkeypatch, [other, same], _status("verified"))
    assert rep.nearest_attested["build"].startswith(f"SQLite {V} ")
    assert rep.nearest_attested["differs"] == ["source_id", "machine", "system", "libc"]


def test_every_key_field_is_compared_and_none_rendered(monkeypatch):
    """The comparison covers EVERY key field but the version (research b38909be, after dev's finding: Marketing's
    `verified` uv build shares version, source id, machine, system and libc with an attested record, so a four-field
    comparison said "differs in no compared field"). A record equal in those and differing only in the compile-options
    digest is named with exactly that field; one differing only in a feature, with `features`. Neither value renders."""
    rec = _rec(V, "S" * 20 + "running00000", "x86_64", "Linux", "glibc", digest="e" * 64)
    rep, out = _run(monkeypatch, [rec], _status("verified"))
    assert rep.nearest_attested["differs"] == ["compile_options_digest"], rep.nearest_attested
    assert "e" * 64 not in out and "d" * 64 not in out
    flipped = dict(FEATURES); flipped[sorted(sv.FEATURE_KEYS)[0]] = False
    rep, out = _run(monkeypatch, [_rec(V, "S" * 20 + "running00000", "x86_64", "Linux", "glibc", features=flipped)],
                    _status("verified"))
    assert rep.nearest_attested["differs"] == ["features"], rep.nearest_attested


def test_a_tie_goes_to_the_first_in_the_listings_own_order(monkeypatch):
    """Two records of the version, each differing in one field. The ARTIFACT lists `second` first; the LISTING (sorted
    by version, then text) lists `first` first, and the tie goes to it."""
    first = _rec(V, "S" * 20 + "running00000", "aarch64", "Linux", "glibc", route="a-route")
    second = _rec(V, "S" * 20 + "running00000", "x86_64", "Linux", "musl", route="b-route")
    rep, out = _run(monkeypatch, [second, first], _status("verified"))
    assert rep.attested_builds.index(rep.nearest_attested["build"]) == 0, rep.attested_builds
    assert "aarch64" in rep.nearest_attested["build"] and rep.nearest_attested["differs"] == ["machine"]


def test_no_record_is_named_when_none_has_the_version(monkeypatch):
    rep, out = _run(monkeypatch, [_rec("3.51.0", "X" * 32, "x86_64", "Linux", "glibc")], _status("verified"))
    assert rep.nearest_attested is None
    assert f"no attested build has SQLite {V}" in out and "nearest attested build" not in out


@pytest.mark.parametrize("status", ["attested", "refused"])
def test_an_attested_or_refused_build_gets_no_such_line(monkeypatch, status):
    rec = _rec(V, "B" * 32, "x86_64", "Linux", "glibc")
    rep, out = _run(monkeypatch, [rec], _status(status))
    assert rep.nearest_attested is None
    assert "nearest attested build" not in out and "no attested build has" not in out


def test_nothing_listed_means_no_line(monkeypatch):
    """An unusable artifact (nothing listed) gets no nearest line: the listing rule is unchanged."""
    rep, out = _run(monkeypatch, [], _status("verified"))
    assert rep.nearest_attested is None and "nearest attested build" not in out and "no attested build has" not in out


def test_the_status_level_and_exit_code_are_unchanged(monkeypatch):
    """v24.1 is rendering only: a verified build is still ONE `info` runtime finding, and the report's exit code is
    what it was."""
    rep, _ = _run(monkeypatch, [_rec(V, "B" * 32, "x86_64", "Linux", "glibc")], _status("verified"))
    runtime = [f for f in rep.findings if f.check == "runtime"]
    assert len(runtime) == 1 and runtime[0].level == "info"
