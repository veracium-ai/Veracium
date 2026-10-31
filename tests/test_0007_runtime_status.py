"""0007 §4g (v17): a SQLite build is `attested`, `verified` or `refused` BY MEASUREMENT on every open (0007 I3/I4, the
production carrier; 0013 §5f.3 carrier (ii), P1–P3).

INV-SA2 (all three verification steps, any failure or exception refused), INV-SA7 (the warning once per process,
none on an attested build), INV-SA8 (the refusal names the first failing step and no file outside the wheel), INV-SA12
(the ONE canonicaliser and the full attestation key), the near-miss set's structure, P1–P3, one `refused`-build cell
per production gate call site with an AST census that fails on a new caller until it has a cell, and the read-once
rule (the status is read at the two gates only, and nothing after branches on it). §4g.3's named vectors are in
tests/test_store_versioning.py.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sqlite3
import sys
import warnings

import pytest

from veracium.store import near_misses as nm
from veracium.store import schema_version as sv

OTHER_MACHINE = "ppc64le" if sv.canonical_platform()["machine"] == "riscv64" else "riscv64"
"""A canonical machine that is NOT this build's (0007 CI run 1, 2026-10-27): "another key" made with a fixed
`aarch64` was this build's own key on arm64 runners, and `libc="musl"` was non-canonical beside Darwin, so cells meant
to hold two keys held one, or a malformed record, off x86_64 Linux."""


ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "veracium"
HEAD = sv.SCHEMA_VERSION
REFUSED = sv.RuntimeStatus("refused", "feature probe preserves_ddl_body is False", None, ())


def record_for_this_build(**over):
    """A well-formed current attestation record whose full key is this build's."""
    ident = sv.attestation_identity()
    r = {**{k: ident[k] for k in sv.KEY_FIELDS}, "manifest_algorithm": sv.MANIFEST_ALGORITHM,
         "schema_version": HEAD, "result_digest": "a" * 64,
         "confinement": {k: True for k in sv.CONFINEMENT_PROBE_KEYS},
         "provenance": [{"route": "setup-python", "runner_image": "ubuntu-24.04", "run_id": "1", "job_id": 1,
                         "commit": "0" * 40}]}
    r.update(over)
    return r


def with_records(monkeypatch, *records):
    monkeypatch.setattr(sv, "attestations", lambda: list(records))


def store_at(path, version):
    c = sqlite3.connect(path)
    sv.create(c, version)
    c.execute(f"PRAGMA user_version = {version}")
    c.commit()
    c.close()
    return str(path)


def sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---- the status: three outcomes by measurement (§4a) ---------------------------------------------------------------
def test_no_matching_record_is_verified_and_a_matching_one_is_attested(monkeypatch):
    with_records(monkeypatch)
    assert sv.runtime_status().status == "verified"
    with_records(monkeypatch, record_for_this_build())
    st = sv.runtime_status()
    assert st.status == "attested" and st.reason is None and st.key == sv.attestation_key(sv.attestation_identity())


def test_any_number_of_keys_is_valid_and_another_keys_record_attests_nothing(monkeypatch):
    other = record_for_this_build(machine=OTHER_MACHINE)
    assert sv.attestation_artifact_problems([other, record_for_this_build()]) == []
    with_records(monkeypatch, other)
    assert sv.runtime_status().status == "verified"


@pytest.mark.parametrize("step", ["probes", "reproduction", "discrimination", "an exception"])
def test_each_verification_step_refuses_and_names_itself(monkeypatch, step):
    """INV-SA2: verified requires all three steps; a failure, or any exception, is refused (a record cannot help)."""
    with_records(monkeypatch, record_for_this_build())
    if step == "probes":
        real = sv._feature_probes
        monkeypatch.setattr(sv, "_feature_probes", lambda: {**real(), "preserves_ddl_body": False})
        want = "feature probe preserves_ddl_body is False"
    elif step == "reproduction":
        _tamper_v1_constructor(monkeypatch, "table:episodes")
        want = "schema v1: table:episodes differs from the accepted manifest"
    elif step == "discrimination":
        monkeypatch.setattr(sv, "_near_miss_objects",
                            lambda m, v: sv._accepted_constructor_entry(v)["objects"])
        want = f"near-miss {nm.NEAR_MISSES[0].name} was not told apart"
    else:
        monkeypatch.setattr(sv, "version_records", lambda: 1 / 0)
        want = "verification raised ZeroDivisionError"
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason == want, st


def test_reproduction_compares_the_complete_manifestation_not_the_digest_alone(monkeypatch):
    """INV-SA3 / S69: a rebuildable index's text is outside the digest, so a digest-only comparison passes a build
    that writes it differently; the complete manifestation refuses it."""
    tampered = _tamper_v1_constructor(monkeypatch, "index:ix_episodes_user",
                                      "CREATE INDEX ix_episodes_user ON episodes(user_id)")
    assert sv._digest_of_identity(tampered, 1) in sv.accepted_digests(1)          # the digest alone passes
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason == "schema v1: index:ix_episodes_user differs from the accepted " \
                                                    "manifest", st


def _tamper_v1_constructor(monkeypatch, key, sql=None):
    """The ACCEPTED side made wrong (the build stays real): v1's constructor entry with `key`'s SQL changed. Returns
    the tampered objects."""
    import copy
    real = copy.deepcopy(sv.version_records())
    entry = next(a for a in real["1"]["accepted"] if a.get("provenance") == "constructor v1")
    entry["objects"][key] = dict(entry["objects"][key], sql=sql if sql is not None else entry["objects"][key]["sql"] + " ")
    monkeypatch.setattr(sv, "version_records", lambda: real)
    return entry["objects"]


# ---- the near-miss set (§4b step 3, INV-SA4) --------------------------------------------------------------------------
def test_the_near_miss_set_covers_every_required_kind_and_each_is_the_head_with_one_change():
    assert sorted({m.kind for m in nm.NEAR_MISSES}) == sorted(nm.REQUIRED_KINDS)
    head = [o.ddl for o in sv.SCHEMAS[HEAD]]
    for m in nm.NEAR_MISSES:
        variant = nm.head_variant(m, sv.SCHEMAS[HEAD])
        changed = [i for i, (a, b) in enumerate(zip(head, variant)) if a != b]
        if m.anchor is None:
            assert len(variant) == len(head) - 1, m
        else:
            assert len(variant) == len(head) and len(changed) == 1, (m, changed)


def test_every_near_miss_is_told_apart_on_this_build():
    head = sv._accepted_constructor_entry(HEAD)["objects"]
    for m in nm.NEAR_MISSES:
        assert sv._near_miss_objects(m, HEAD) != head, m.name


def test_a_near_miss_whose_anchor_moved_refuses_to_build():
    bad = nm.NEAR_MISSES[0]._replace(anchor="no such text")
    with pytest.raises(nm.NearMissError):
        nm.head_variant(bad, sv.SCHEMAS[HEAD])


# ---- INV-SA12: one canonicaliser, the full key -----------------------------------------------------------------------
@pytest.mark.parametrize("raw,want", [("x86_64", "x86_64"), ("AMD64", "x86_64"), ("amd64", "x86_64"),
                                      ("arm64", "aarch64"), ("ARM64", "aarch64"), ("aarch64", "aarch64"),
                                      ("i686", "i686"), ("ppc64le", "ppc64le"), ("x86-64", None), ("", None),
                                      (None, None)])
def test_the_machine_canonicaliser_is_a_closed_two_entry_alias_map(raw, want):
    assert sv.canonical_machine(raw) == want


def test_libc_comes_from_pt_interp_never_from_libc_ver(monkeypatch):
    import platform
    assert sv.canonical_libc("Linux", "/lib64/ld-linux-x86-64.so.2") == "glibc"
    assert sv.canonical_libc("Linux", "/lib/ld-musl-aarch64.so.1") == "musl"
    assert sv.canonical_libc("Linux", None) is None and sv.canonical_libc("Linux", "/lib/ld.so") is None
    assert sv.canonical_libc("Darwin", None) == "none" and sv.canonical_libc("Windows", "/x") == "none"
    before = sv.canonical_platform()["libc"]
    monkeypatch.setattr(platform, "libc_ver", lambda *a, **k: ("musl", "9"))
    assert sv.canonical_platform()["libc"] == before
    if sys.platform.startswith("linux"):
        assert before in ("glibc", "musl")


def test_each_key_field_separates_two_records_that_agree_on_every_other(monkeypatch):
    """INV-SA12's mutants: drop machine, system, libc or the options digest, and two builds collapse into one key."""
    base = record_for_this_build()
    me = sv.canonical_platform()             # each "other" differs from THIS build (0007 CI run 1: arm64 and macOS)
    other_system = "Windows" if me["system"] == "Darwin" else "Darwin"
    other_libc = "glibc" if me["libc"] == "musl" else "musl"
    for field, other in (("machine", OTHER_MACHINE), ("system", other_system), ("libc", other_libc),
                         ("compile_options_digest", "b" * 64), ("source_id", "x"), ("sqlite_version", "3.0.0")):
        r = record_for_this_build(**{field: other})
        if field == "system":
            r["libc"] = "none"
        assert sv.attestation_key(r) != sv.attestation_key(base), field
        with_records(monkeypatch, r)
        assert sv.runtime_status().status == "verified", field
    # `system` ALONE (I6's campaign: the pair above also changes libc, which separates it by itself): two non-Linux
    # builds on one machine share libc `none` and differ only in system (§4g.8: a record of one attests the other).
    darwin, windows = (record_for_this_build(system=s_, libc="none", machine="aarch64") for s_ in ("Darwin", "Windows"))
    assert sv.attestation_key(darwin) != sv.attestation_key(windows)


def test_a_record_canonicalised_on_one_side_only_matches_nothing(monkeypatch):
    """A record written with the raw `AMD64` is malformed (the record side canonicalises too), never a match."""
    r = record_for_this_build(machine="AMD64")
    assert any("'machine'" in p for p in sv.attestation_record_problems(r))
    # ...and the BUILD side canonicalises too (I6's campaign: on an x86_64 box the raw name is already canonical, so
    # the build side was unexercised): a Windows build reporting `AMD64` keys as `x86_64`, as its record does.
    monkeypatch.setattr(sv.platform, "machine", lambda: "AMD64")
    assert sv.canonical_platform()["machine"] == "x86_64"


def test_the_compile_options_digest_ignores_the_order_the_build_returns_them_in():
    """INV-SA12 (v0.7): one build is one key whatever order it lists its options in; the bytes are pinned."""
    _src, opts = sv._probe_build()
    assert sv.compile_options_digest() == sv.options_digest(opts) == sv.options_digest(list(reversed(opts)))
    assert sv.options_digest(["B", "A"]) == hashlib.sha256(b"A\nB").hexdigest()
    assert sv.options_digest(["A"]) != sv.options_digest(["A", "B"])


# ---- INV-SA7 / INV-SA8: what the user sees ----------------------------------------------------------------------
def test_a_verified_open_warns_once_per_process_and_an_attested_open_never(monkeypatch, tmp_path):
    from veracium.store.sqlite import SqliteStore
    monkeypatch.setattr(sv, "_WARNED", [])
    with_records(monkeypatch)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        for i in range(3):
            SqliteStore(str(tmp_path / f"v{i}.db")).close()
    mine = [x for x in w if issubclass(x.category, sv.UnattestedBuildWarning)]
    assert len(mine) == 1 and "is not one of Veracium's attested builds" in str(mine[0].message)
    monkeypatch.setattr(sv, "_WARNED", [])
    with_records(monkeypatch, record_for_this_build())
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        SqliteStore(str(tmp_path / "a.db")).close()
    assert not [x for x in w if issubclass(x.category, sv.UnattestedBuildWarning)]


def test_the_refusal_names_the_first_failing_step_and_no_file_outside_the_wheel(monkeypatch, tmp_path):
    from veracium.store.sqlite import SqliteStore
    monkeypatch.setattr(sv, "runtime_status", lambda: REFUSED)
    with pytest.raises(sv.StoreVersionError) as e:
        SqliteStore(str(tmp_path / "r.db"))
    text = str(e.value)
    assert e.value.reason == "unsupported-sqlite" and REFUSED.reason in text
    assert "schema_evidence" not in text and "specs/" not in text and ".py" not in text


# ---- P1–P3 (0013 §5f.3 carrier (ii)) -----------------------------------------------------------------------------
@pytest.mark.parametrize("status", ["verified", "attested"])
def test_p1_a_verified_build_migrates_a_base_store_as_the_attested_build_does(monkeypatch, tmp_path, status):
    """P1. The `attempted` event's `runtime.status` (INV-SA11) is I6's audit change and is not asserted here."""
    import veracium.store.migration as mig
    with_records(monkeypatch, *([record_for_this_build()] if status == "attested" else []))
    assert sv.runtime_status().status == status
    seen = []
    real = sv._validated_current
    monkeypatch.setattr(sv, "_validated_current", lambda *a, **k: (seen.append(k.get("require_stamp")),
                                                                    real(*a, **k))[1])
    p = store_at(tmp_path / "s.db", HEAD - 1)
    try:                    # a gate that refuses this build is the row's failure, asserted, never an escaping raise
        out = str(mig.migrate_store(p))
    except sv.StoreVersionError as e:
        out = f"refused {e.reason}"
    assert out == "migrated", out
    assert seen == [True]


def test_p2_a_refused_build_refuses_migrate_store_and_the_release_before_touching_the_store(monkeypatch, tmp_path):
    import veracium.store.migration as mig
    import veracium.store.release_migration as rm
    monkeypatch.setattr(sv, "runtime_status", lambda: REFUSED)
    p = store_at(tmp_path / "s.db", HEAD - 1)
    before = sha(p)
    with pytest.raises(sv.StoreVersionError) as e:
        mig.migrate_store(p)
    assert e.value.reason == "unsupported-sqlite" and sha(p) == before
    # "before touching the store", for the release path: its preflight refuses before ANY connection to the store
    # opens (the open gate further down refuses too, with the same tuple and bytes, so only this tells the two apart)
    opened, real_connect = [], sqlite3.connect
    monkeypatch.setattr(sqlite3, "connect", lambda db, *a, **k: (opened.append(str(db)), real_connect(db, *a, **k))[1])
    r = rm.run_release_migration(p, host_attestation=rm.MigrationAttestation(quiesced=True, backup_ref="t"))
    monkeypatch.setattr(sqlite3, "connect", real_connect)
    assert tuple(r)[:5] == ("unsupported-sqlite", False, False, "unknown", None) and sha(p) == before
    assert not [d for d in opened if pathlib.Path(p).name in d], opened


@pytest.mark.parametrize("status", ["verified", "attested"])
def test_p3_a_stamp_below_head_is_refused_by_revalidation_and_rolls_back(monkeypatch, tmp_path, status):
    """P3, research's v0.8 stamp mutant: the stamp written as HEAD - 1 with the step's own postcondition bypassed, so
    `_validated_current(require_stamp=True)` is what refuses; the transaction rolls back on either build."""
    import veracium.store.migration as mig
    with_records(monkeypatch, *([record_for_this_build()] if status == "attested" else []))
    real = mig._refuse_unless

    def stamp_low(base, step, problems):
        if step == mig.STEP_STAMP:
            sys._getframe(1).f_locals["conn"].execute(f"PRAGMA user_version = {HEAD - 1}")
            return
        real(base, step, problems)
    monkeypatch.setattr(mig, "_refuse_unless", stamp_low)
    p = store_at(tmp_path / "s.db", HEAD - 1)
    before = sha(p)
    with pytest.raises(Exception):
        mig.migrate_store(p)
    assert sha(p) == before


# ---- one refused-build cell per production gate call site, and the census that keeps the set closed -----------------
def _gate_call_sites():
    """(file relative to src/veracium, enclosing function) of every call to `_preflight_classify` or `open_versioned`
    in src/, by AST — the enumeration the cells below must cover exactly."""
    out = set()
    for f in sorted(SRC.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for n in ast.walk(fn):
                if isinstance(n, ast.Call):
                    name = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", None)
                    if name in ("_preflight_classify", "open_versioned") and fn.name != name:
                        out.add((str(f.relative_to(SRC)), fn.name))
    return out


def _cell_sqlite(p):
    from veracium.store.sqlite import SqliteStore
    with pytest.raises(sv.StoreVersionError) as e:
        SqliteStore(p)
    return e.value.reason


def _cell_migrate(p):
    import veracium.store.migration as mig
    with pytest.raises(sv.StoreVersionError) as e:
        mig.migrate_store(p)
    return e.value.reason


def _cell_repair(p):
    import veracium.store.release_migration as rm
    return rm._repair_current(p).outcome


def _cell_release(p):
    import veracium.store.release_migration as rm
    return rm.run_release_migration(p, host_attestation=rm.MigrationAttestation(quiesced=True, backup_ref="t")).outcome


def _cell_dm_preflight(p):
    import veracium.store.data_migration as dm
    canonical, res = dm._preflight(p, "op-1")
    assert canonical is None
    return res.diagnostic.split(":")[0]


def _cell_dm_read(p):
    import veracium.store.data_migration as dm
    with pytest.raises(ValueError) as e:
        dm._read_only(p)
    return "unsupported-sqlite" if "(unsupported-sqlite)" in str(e.value) else str(e.value)


GATE_CELLS = {
    ("store/sqlite.py", "__init__"): _cell_sqlite,
    ("store/migration.py", "migrate_store"): _cell_migrate,
    ("store/release_migration.py", "_repair_current"): _cell_repair,
    ("store/release_migration.py", "_classify_or_intercept"): _cell_release,
    ("store/data_migration.py", "_preflight"): _cell_dm_preflight,
    ("store/data_migration.py", "_read_only"): _cell_dm_read,
}


def test_every_production_gate_call_site_has_a_refused_build_cell():
    assert _gate_call_sites() == set(GATE_CELLS)


@pytest.mark.parametrize("site", sorted(GATE_CELLS), ids=lambda s: f"{s[0]}:{s[1]}")
def test_a_refused_build_is_refused_at_each_gate_call_site_and_the_store_is_unchanged(monkeypatch, tmp_path, site):
    monkeypatch.setattr(sv, "runtime_status", lambda: REFUSED)
    p = store_at(tmp_path / "s.db", HEAD)
    before = sha(p)
    assert GATE_CELLS[site](p) == "unsupported-sqlite"
    assert sha(p) == before


# ---- the read-once rule (research's item 6(c)) ------------------------------------------------------------------------
def _calls_in(fn_node, name):
    return [n for n in ast.walk(fn_node) if isinstance(n, ast.Call)
            and (getattr(n.func, "attr", None) == name or getattr(n.func, "id", None) == name)]


def _function(rel, name):
    tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
    hits = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(hits) == 1, (rel, name)
    return hits[0]


def test_the_status_is_read_once_at_each_gate_and_nothing_after_branches_on_it():
    """`runtime_status()` is called exactly once in each gate function and never in `_apply_forward`; no
    production module calls the withdrawn `runtime_supported()`."""
    assert len(_calls_in(_function("store/schema_version.py", "open_versioned"), "runtime_status")) == 1
    assert len(_calls_in(_function("store/release_migration.py", "_preflight_classify"), "runtime_status")) == 1
    assert _calls_in(_function("store/migration.py", "_apply_forward"), "runtime_status") == []
    for f in sorted(SRC.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        own = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and (getattr(n.func, "attr", None) == "runtime_supported"
                      or getattr(n.func, "id", None) == "runtime_supported")]
        if f.name == "schema_version.py":
            assert "_runtime_supported_interim" not in own and "runtime_supported" not in own   # retired (I4 (A))
        assert calls == [], f"{f.relative_to(SRC)} calls runtime_supported()"
        interim = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                   and (getattr(n.func, "attr", None) == "_runtime_supported_interim"
                        or getattr(n.func, "id", None) == "_runtime_supported_interim")]
        assert interim == [], f"{f.relative_to(SRC)} calls the interim predicate; production reads runtime_status()"


# ---- research's stage-1 read of the design (item 14): the cells it named ----------------------------------------------
def test_a_poisoned_artifact_blocks_attestation_never_verification(monkeypatch):
    """D1(a): poison blocks ATTESTATION, never verification (§4g.3: a record can only remove the warning): a malformed
    record beside a matching valid one, and a conflicting pair, each leave the build `verified`, the reason naming it."""
    good = record_for_this_build()
    for records, says in (([good, record_for_this_build(machine="AMD64")], "'machine'"),
                          ([good, record_for_this_build(result_digest="b" * 64)], "different evidence")):
        with_records(monkeypatch, *records)
        st = sv.runtime_status()
        assert st.status == "verified" and st.reason.startswith("attestation artifact: ") and says in st.reason, st


@pytest.mark.parametrize("count", [0, 2])
def test_reproduction_needs_exactly_one_accepted_constructor_entry_per_version(monkeypatch, count):
    """D3: zero or two `constructor v{v}` entries refuse, naming the count (never the first of two, never vacuous)."""
    real = sv.version_records()

    def records():
        out = {k: dict(v) for k, v in real.items()}
        ctor = [a for a in out["3"]["accepted"] if a.get("provenance") == "constructor v3"]
        rest = [a for a in out["3"]["accepted"] if a.get("provenance") != "constructor v3"]
        out["3"]["accepted"] = rest + ctor * count
        return out
    monkeypatch.setattr(sv, "version_records", records)
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason == f"schema v3: {count} accepted constructor manifestations, not one", st


def test_every_near_miss_is_outside_every_accepted_head_shape_and_the_dropped_index_is_rebuildable():
    """D4: not only different from the constructor — outside EVERY accepted head shape (11 at schema 16, most of them
    migrated), or a near-miss that coincides with an accepted migrated shape would test nothing."""
    accepted = [a["objects"] for a in sv.version_records()[str(HEAD)]["accepted"]]
    assert len(accepted) > 1
    for m in nm.NEAR_MISSES:
        assert sv._near_miss_objects(m, HEAD) not in accepted, m.name
    dropped = [m for m in nm.NEAR_MISSES if m.kind == "dropped-rebuildable-index"]
    assert dropped and all(next(o for o in sv.SCHEMAS[HEAD] if o.key == m.target).policy == sv.REBUILDABLE
                           for m in dropped)


def test_a_near_miss_that_coincides_with_an_accepted_head_shape_refuses_the_build(monkeypatch):
    other = next(a["objects"] for a in sv.version_records()[str(HEAD)]["accepted"]
                 if a.get("provenance") != f"constructor v{HEAD}")
    monkeypatch.setattr(sv, "_near_miss_objects", lambda m, v: other)
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason == f"near-miss {nm.NEAR_MISSES[0].name} was not told apart", st


def test_libc_is_read_from_the_process_image_so_a_loader_launch_is_unreadable():
    """D5 / item 10(c): started through the loader, `sys.executable` still names a glibc interpreter, but the process
    image is the loader itself, with no PT_INTERP: libc is unreadable, never guessed."""
    import subprocess
    assert sv.PROCESS_IMAGE == "/proc/self/exe"
    interp = sv._pt_interp(sv.PROCESS_IMAGE)
    if sv.canonical_platform()["system"] != "Linux":
        assert interp is None and sv.canonical_platform()["libc"] == "none"
        return
    assert interp and sv.canonical_platform()["libc"] in ("glibc", "musl")
    import os
    import site
    code = "from veracium.store import schema_version as sv; print(sv.canonical_platform()['libc'])"
    path = os.pathsep.join([str(SRC.parent)] + site.getsitepackages())    # the venv's packages, by the real binary
    r = subprocess.run([interp, os.path.realpath(sys.executable), "-c", code], capture_output=True, text=True,
                       timeout=120, env={**os.environ, "PYTHONPATH": path})
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "None"


@pytest.mark.parametrize("value", ["x86_64\n", "Linux\n"])
def test_a_trailing_newline_is_never_canonical(value):
    assert sv.canonical_machine(value) is None and sv.canonical_system(value) is None
    field = "machine" if value.startswith("x86") else "system"
    assert any(f"'{field}'" in p for p in sv.attestation_record_problems(record_for_this_build(**{field: value})))


def test_the_record_and_artifact_key_sets_are_closed(monkeypatch, tmp_path):
    """D7 / item 10(b): an extra or missing field is malformed; a record with no `libc` key never matches a build
    whose libc is unreadable; an unknown top-level artifact key poisons."""
    extra = record_for_this_build()
    extra["note"] = "x"
    missing = record_for_this_build()
    del missing["libc"]
    for r in (extra, missing):
        assert any(p.startswith("fields ") for p in sv.attestation_record_problems(r))
    assert sv.attestation_key(missing) is None
    art = tmp_path / "sqlite_runtimes.json"
    art.write_text('{"attestations": [], "runtimes": [], "extra": 1}')
    monkeypatch.setattr(sv, "RUNTIMES", art)
    st = sv.runtime_status()
    assert st.status == "verified" and "top level" in st.reason, st


@pytest.mark.parametrize("revision,kind", [((sv.MANIFEST_ALGORITHM - 1, HEAD), "superseded"),
                                           ((sv.MANIFEST_ALGORITHM, HEAD - 1), "superseded"),
                                           ((sv.MANIFEST_ALGORITHM + 1, HEAD), "future"),
                                           ((sv.MANIFEST_ALGORITHM, HEAD + 1), "future")])
def test_a_superseded_or_future_record_contributes_nothing_and_poisons_nothing(monkeypatch, revision, kind):
    r = record_for_this_build(manifest_algorithm=revision[0], schema_version=revision[1], machine="AMD64")
    assert sv.attestation_revision(r) == kind
    assert sv.attestation_artifact_problems([r]) == []                 # malformed, but not current: not validated
    with_records(monkeypatch, record_for_this_build(manifest_algorithm=revision[0], schema_version=revision[1]))
    assert sv.runtime_status().status == "verified"                    # and it cannot attest


@pytest.mark.parametrize("bad", [True, "16", 16.0])
def test_a_revision_field_that_is_not_an_exact_int_is_malformed_and_poisons(bad):
    """Research's 69bba264: `True`, `"2"` and `2.0` are garbage, never a high revision (round 5's `True == 1`)."""
    for field in ("manifest_algorithm", "schema_version"):
        r = record_for_this_build(**{field: bad})
        assert sv.attestation_revision(r) == "malformed"
        assert sv.attestation_artifact_problems([r]) != []


@pytest.mark.parametrize("change,says", [
    (lambda j: j.update(commit="abc1234"), "full hex commit"),
    (lambda j: j.update(job_id="1"), "job_id must be a non-negative int"),
    (lambda j: j.update(job_id=True), "job_id must be a non-negative int"),
    (lambda j: j.update(route=""), "nonempty strings"),
])
def test_provenance_is_typed(change, says):
    r = record_for_this_build()
    change(r["provenance"][0])
    assert any(says in p for p in sv.attestation_record_problems(r)), sv.attestation_record_problems(r)


def test_provenance_sorts_job_ids_as_ints():
    """Item 10(f): job 9 sorts before job 10 (as strings it would not)."""
    base = {"route": "setup-python", "runner_image": "ubuntu-24.04", "run_id": "1", "commit": "0" * 40}
    good = [dict(base, job_id=9), dict(base, job_id=10)]
    assert sv.attestation_record_problems(record_for_this_build(provenance=good)) == []
    assert any("not sorted" in p for p in sv.attestation_record_problems(record_for_this_build(
        provenance=list(reversed(good)))))


# ---- INV-SA11: the migrating build rides both kernel events and the sidecar ------------------------------------------
UPSTREAM_ID = "2024-01-30 16:01:20 e876e51a0ed5c5b3126f52e532044363a014bc594cfefa87ffb5b82257cc8b2a"
DISTRO_ID = "2024-01-30 16:01:20 e876e51a0ed5c5b3126f52e532044363a014bc594cfefa87ffb5b82257ccalt1"


@pytest.mark.parametrize("source_id,ok", [
    (UPSTREAM_ID, True), (DISTRO_ID, True), (DISTRO_ID + "\0", False), (DISTRO_ID + " ", False),
    (DISTRO_ID[:-4] + "alt1x", False), (DISTRO_ID[:-4] + "ALT1", False), (DISTRO_ID[:-1] + "\ud800", False),
    ("", False)])
def test_the_audit_source_id_has_its_own_closed_grammar(source_id, ok):
    import veracium.store.migration as mig
    attested = sv.RuntimeStatus("attested", None, None, (), "3.45.1", source_id)
    if ok:
        assert mig.migration_runtime(attested) == mig.MigrationRuntime("3.45.1", source_id, "attested")
    else:
        with pytest.raises(ValueError, match="runtime.source_id"):
            mig.migration_runtime(attested)


@pytest.mark.parametrize("version,status,field", [("3.45", "verified", "sqlite_version"),
                                                  ("3.45.1 ", "verified", "sqlite_version"),
                                                  (None, "verified", "sqlite_version"),
                                                  ("3.45.1", "refused", "status"), ("3.45.1", None, "status")])
def test_the_audit_version_and_status_have_closed_grammars(version, status, field):
    import veracium.store.migration as mig
    with pytest.raises(ValueError, match=f"runtime.{field}"):
        mig.migration_runtime(sv.RuntimeStatus(status, None, None, (), version, DISTRO_ID) if status else None)


@pytest.mark.parametrize("status", ["verified", "attested"])
def test_both_kernel_events_carry_the_gates_measurement_as_their_last_field(monkeypatch, tmp_path, status):
    import veracium.store.migration as mig
    with_records(monkeypatch, *([record_for_this_build()] if status == "attested" else []))
    assert mig.MigrationAuditEvent._fields[-1] == "runtime"
    events = []
    p = store_at(tmp_path / "s.db", HEAD - 1)
    assert str(mig.migrate_store(p, audit_sink=events.append)) == "migrated"
    me = sv.runtime_identity()
    assert [e.event for e in events] == ["migration_attempted", "migration_committed"]
    assert {e.runtime for e in events} == {mig.MigrationRuntime(me["sqlite_version"], me["source_id"], status)}


def test_the_release_sidecar_copies_the_runtime(monkeypatch, tmp_path):
    import json
    import os
    import veracium.store.release_migration as rm
    with_records(monkeypatch)
    p = store_at(tmp_path / "s.db", HEAD - 1)
    r = rm.run_release_migration(p, host_attestation=rm.MigrationAttestation(quiesced=True, backup_ref="t"))
    assert r.outcome == "migrated", r
    trail = json.loads(pathlib.Path(rm.audit_trail_path(os.path.realpath(p))).read_text())
    attempted = [e["attempted"] for e in trail.values() if isinstance(e, dict) and "attempted" in e]
    me = sv.runtime_identity()
    assert attempted and all(a["runtime"] == {"sqlite_version": me["sqlite_version"], "source_id": me["source_id"],
                                              "status": "verified"} for a in attempted)


# ---- the interim predicate's readers: a committed list (research's item 14 D9) ---------------------------------------
INTERIM_READERS = set()
"""Empty since I4 (A): the legacy runtime record class and its interim predicate are retired (0007 §4g.6 4f), so no
live file may read `_runtime_supported_interim` at all."""
FROZEN_EVIDENCE = {
    # round-2 accepted evidence, run only at its recorded pin (research 69bba264): excluded BY EXACT PATH, never by a
    # pattern a live reader could hide under
    "specs/evidence/0007-sqlite-attestation/steptable.py",
    "specs/evidence/0007-sqlite-attestation/probe_build_reproduces.py",
    "specs/evidence/0007-sqlite-attestation/r1-repro-at-58dd7f6/runtime_contract_probe.py",
}


def _names_in(f):
    if f.suffix == ".sh":                      # code lines only: a `#` comment line is history, not a reader
        import re
        code = "\n".join(ln for ln in f.read_text(encoding="utf-8").splitlines() if not ln.lstrip().startswith("#"))
        return ({"_runtime_supported_interim"} if "_runtime_supported_interim" in code else set()) | (
            {"runtime_supported"} if re.search(r"(?<![A-Za-z0-9_])runtime_supported\b", code) else set())
    out = set()
    for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
        name = (n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute)
                else n.name if isinstance(n, ast.alias)
                else n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None)
        if name in ("_runtime_supported_interim", "runtime_supported"):
            out.add(name)
    return out


def test_the_interim_predicate_is_read_only_by_a_committed_list_and_the_old_name_by_nothing_live():
    """Every reader of `_runtime_supported_interim` is on the committed list, so a new reader fails until it is
    classified, and the list is deleted with the predicate in the commit that retires `runtimes`. No live file
    refers to `runtime_supported` by code (the rename touched every call and every patch, so a stale patch cannot
    silently stop reaching a gate)."""
    found_interim, found_old = set(), set()
    for base in ("src", "specs", "tests"):
        for f in sorted((ROOT / base).rglob("*")):
            if f.suffix not in (".py", ".sh") or not f.is_file():
                continue
            rel = str(f.relative_to(ROOT))
            if rel in FROZEN_EVIDENCE or rel == "tests/test_0007_runtime_status.py":
                continue
            names = _names_in(f)
            if "_runtime_supported_interim" in names:
                found_interim.add(rel)
            if "runtime_supported" in names:
                found_old.add(rel)
    assert found_interim == INTERIM_READERS, (sorted(found_interim - INTERIM_READERS),
                                              sorted(INTERIM_READERS - found_interim))
    assert found_old == set(), sorted(found_old)
    for rel in FROZEN_EVIDENCE:
        assert (ROOT / rel).is_file(), rel


# ---- research's stage 2 on ce6117f (§15): each finding's cell, and the five surviving mutants' ----------------------
@pytest.mark.parametrize("field", sorted(sv._RECORD_FIELDS))
@pytest.mark.parametrize("bad", [[], {}])
def test_every_record_field_as_a_container_leaves_the_build_verified_naming_it(monkeypatch, field, bad):
    """F1: a current record whose field is `[]` or `{}` poisons THAT record; it never escapes the validator, so the
    build is `verified` (it was `refused`, "verification raised TypeError", for `libc` at ce6117f)."""
    with_records(monkeypatch, record_for_this_build(), record_for_this_build(**{field: bad}))
    st = sv.runtime_status()
    assert st.status == "verified" and st.reason and st.reason.startswith("attestation artifact: "), st
    assert f"'{field}'" in st.reason or "fields " in st.reason, st      # it NAMES the field (research's M24)


def test_a_validator_escape_poisons_that_record_and_the_build_stays_verified(monkeypatch):
    """Research's M23: with the per-record try/except removed, an escaping validator would refuse every build."""
    with_records(monkeypatch, record_for_this_build())
    monkeypatch.setattr(sv, "attestation_record_problems", lambda r: (_ for _ in ()).throw(TypeError("boom")))
    st = sv.runtime_status()
    assert st.status == "verified" and "its validation raised TypeError" in st.reason, st


def test_a_failing_identity_read_refuses_at_the_gate_and_never_raises_through_it(monkeypatch, tmp_path):
    """F2: the refusal text, the warning and the audit value come from the status's ONE read. With the build's own
    identity read failing, the open refuses `unsupported-sqlite`; it does not re-raise the read's error."""
    from veracium.store.sqlite import SqliteStore
    monkeypatch.setattr(sv, "_probe_build", lambda: (_ for _ in ()).throw(sqlite3.OperationalError("probe")))
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason == "verification raised OperationalError", st
    with pytest.raises(sv.StoreVersionError) as e:
        SqliteStore(str(tmp_path / "s.db"))
    assert e.value.reason == "unsupported-sqlite"
    assert "verification raised OperationalError" in str(e.value) and "source id unreadable" in str(e.value)


def test_the_status_carries_the_build_it_measured(monkeypatch):
    st = sv.runtime_status()
    me = sv.runtime_identity()
    assert (st.sqlite_version, st.source_id) == (me["sqlite_version"], me["source_id"])
    assert st.platform == tuple(sv.canonical_platform()[k] for k in ("machine", "system", "libc"))


def test_doctor_names_a_poisoned_artifact(monkeypatch):
    """F3: the poison reason reaches a reader: doctor's verified line carries it."""
    from veracium import doctor
    with_records(monkeypatch, record_for_this_build(), record_for_this_build(machine="AMD64"))
    rep = doctor.Report(db="x", readable=False)
    doctor._check_runtime(rep)
    msgs = [f.message for f in rep.findings if f.check == "runtime"]
    assert msgs and "attestation artifact" in msgs[0] and "'machine'" in msgs[0], msgs


def test_a_probe_that_is_not_exactly_true_refuses(monkeypatch):
    """M1: `None` (or `1`) is not True; a required probe must be exactly True."""
    real = sv._feature_probes
    for bad in (None, 1):
        monkeypatch.setattr(sv, "_feature_probes", lambda bad=bad: {**real(), "preserves_ddl_body": bad})
        st = sv.runtime_status()
        assert st.status == "refused" and st.reason == f"feature probe preserves_ddl_body is {bad!r}", st


def test_a_build_whose_probe_reads_as_an_int_matches_no_record(monkeypatch):
    """M15: the key's features must be EXACT bools. A build whose non-required probes return 1 (not True) has no key,
    so even a record with True there does not attest it (`isinstance(v, int)` would)."""
    with_records(monkeypatch, record_for_this_build())
    real = sv._feature_probes
    monkeypatch.setattr(sv, "_feature_probes", lambda: {**real(), "generated_columns": 1, "strict_tables": 1})
    st = sv.runtime_status()
    assert st.status == "verified" and st.key is None, st


def test_a_near_miss_set_missing_a_required_kind_refuses(monkeypatch):
    """M16: the kinds arm, isolated: the set without its reordered-column member."""
    monkeypatch.setattr(nm, "NEAR_MISSES", tuple(m for m in nm.NEAR_MISSES if m.kind != "reordered-column"))
    st = sv.runtime_status()
    assert st.status == "refused" and st.reason.startswith("the near-miss set covers "), st


def test_equal_evidence_with_different_provenance_is_a_duplicate_not_a_conflict():
    """M17: provenance is never compared as evidence."""
    a = record_for_this_build()
    b = record_for_this_build(provenance=[{"route": "deadsnakes", "runner_image": "ubuntu-24.04", "run_id": "2",
                                           "job_id": 7, "commit": "1" * 40}])
    probs = sv.attestation_artifact_problems([a, b])
    assert len(probs) == 1 and probs[0].endswith("with equal evidence: a duplicate"), probs


def test_the_release_preflight_warns_on_a_verified_build(monkeypatch, tmp_path):
    """M18: `_preflight_classify` is a gate too; a verified build reading a store there warns (once per process)."""
    import veracium.store.release_migration as rm
    with_records(monkeypatch)
    p = store_at(tmp_path / "s.db", HEAD)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        rm._preflight_classify(p)
    assert [x for x in w if issubclass(x.category, sv.UnattestedBuildWarning)]


# ---- A16 (0013 v35): production's evidence check -------------------------------------------------------------------
def test_a16_production_evidence_refuses_two_accepted_manifestations_sharing_an_acceptance_digest():
    import copy
    import importlib.util
    spec = importlib.util.spec_from_file_location("veracium_schema_evidence", ROOT / "specs" / "schema_evidence.py")
    se = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(se)
    versions = copy.deepcopy(sv.version_records())
    assert se.acceptance_digest_problems(versions) == []                    # the shipped sets hold the rule
    entry = versions["1"]["accepted"][0]
    twin = copy.deepcopy(entry)
    idx = next(k for k in twin["objects"] if k.startswith("index:"))
    twin["objects"][idx] = dict(twin["objects"][idx], sql=twin["objects"][idx]["sql"] + " ")
    assert sv._digest_of_identity(twin["objects"], 1) == entry["digest"]   # a rebuildable-only difference
    versions["1"]["accepted"].append(twin)
    probs = se.acceptance_digest_problems(versions)
    assert len(probs) == 1 and probs[0].startswith("v1: two accepted manifestations share"), probs


def test_verify_build_reproduces_through_the_generators_constructor(monkeypatch):
    """Research's Y5 / F1: production's reproduction calls `_constructor_objects` (create()) once per declared
    version, the constructor the evidence generator records, never a second DDL-only builder."""
    calls = []
    real = sv._constructor_objects
    monkeypatch.setattr(sv, "_constructor_objects", lambda v: calls.append(v) or real(v))
    sv.verify_build()
    assert sorted(calls) == sorted(sv.SCHEMAS), calls


def test_the_packaged_attestation_artifact_is_valid(tmp_path, monkeypatch):
    """S56 / S65 (0007 v20, research): a claim about the SHIPPED artifact, not a fabricated one. From the first CI
    attestation on, package data carries real records, and a poisoned artifact silently downgrades every build to
    `verified`; so the packaged file, read where production reads it, has no problem at all (malformed, conflicting
    or duplicate). Control: the same reader over a copy of it carrying a planted conflicting pair (one key, two
    result digests) reports the conflict."""
    packaged = pathlib.Path(sv.__file__).resolve().parent / "evidence" / "sqlite_runtimes.json"
    assert pathlib.Path(sv.RUNTIMES).resolve() == packaged and packaged.exists()
    assert sv.attestation_artifact_problems() == []

    ident = sv.attestation_identity()
    planted_record = {**{k: ident[k] for k in sv.KEY_FIELDS}, "manifest_algorithm": sv.MANIFEST_ALGORITHM,
                      "schema_version": sv.SCHEMA_VERSION, "result_digest": "a" * 64,
                      "confinement": {k: True for k in sv.CONFINEMENT_PROBE_KEYS},
                      "provenance": [{"route": "setup-python", "runner_image": "ubuntu-24.04", "run_id": "1",
                                      "job_id": 1, "commit": "a" * 40}]}
    assert sv.attestation_record_problems(planted_record) == []            # the pair is valid record by record
    planted = tmp_path / "sqlite_runtimes.json"
    planted.write_text(json.dumps({"attestations": sv.attestations()
                                   + [planted_record, dict(planted_record, result_digest="b" * 64)]}))
    monkeypatch.setattr(sv, "RUNTIMES", planted)
    problems = sv.attestation_artifact_problems()
    assert any("with different evidence" in p for p in problems), problems



# ---- I6: the cells INV-SA1–SA12's mutation table needed and the suite lacked (specs/evidence/0007/sa_mutants.py) ----
@pytest.mark.parametrize("site", sorted(GATE_CELLS), ids=lambda s: f"{s[0]}:{s[1]}")
def test_a_refused_build_is_refused_before_any_version_decision(monkeypatch, tmp_path, site):
    """INV-SA1 "decide shape first": a store stamped NEWER than this build would be refused as `newer` by a version
    decision. On a refused build it must be refused as `unsupported-sqlite`, so the gate ran first, at every gate
    call site."""
    import sqlite3 as _sqlite3
    monkeypatch.setattr(sv, "runtime_status", lambda: REFUSED)
    p = store_at(tmp_path / "s.db", HEAD)
    with _sqlite3.connect(p) as c:
        c.execute(f"PRAGMA user_version = {HEAD + 1}")
    assert GATE_CELLS[site](p) == "unsupported-sqlite"


def test_doctor_checks_the_sqlite_build_before_opening_any_store(monkeypatch, tmp_path):
    """INV-SA9 "report after opening": the runtime check runs BEFORE doctor opens any store (it is exactly what a
    refused build's user needs, and a refused build cannot open one)."""
    from veracium import doctor
    order = []
    real_check = doctor._check_runtime
    monkeypatch.setattr(doctor, "_check_runtime", lambda rep: (order.append("runtime"), real_check(rep))[1])
    monkeypatch.setattr(doctor, "_open_snapshot", lambda rep, path, tmpdir: order.append("open"))
    monkeypatch.setattr(sv, "runtime_status", lambda: REFUSED)
    rep = doctor.diagnose(str(tmp_path / "absent.db"))
    assert order[:2] == ["runtime", "open"], order
    assert [f.level for f in rep.findings if f.check == "runtime"] == ["error"]


@pytest.mark.parametrize("status, level", [("verified", "info"), ("refused", "error")])
def test_doctor_reports_verified_at_info_and_refused_at_error(monkeypatch, status, level):
    """INV-SA9 "report `verified` at `warn`": doctor exits 1 on any warning, so a verified build (every uv user's)
    must be `info`; a refused build is `error`."""
    from veracium import doctor
    st = sv.runtime_status()._replace(status=status, reason="probe x is False" if status == "refused" else None)
    monkeypatch.setattr(sv, "runtime_status", lambda: st)
    rep = doctor.Report(db="x", readable=False)
    doctor._check_runtime(rep)
    assert [f.level for f in rep.findings if f.check == "runtime"] == [level]


def test_doctor_lists_every_current_record_of_an_unpoisoned_artifact(monkeypatch):
    """0007 §4g.6 (v0.12) "lists each attested build with its machine, system and libc": every CURRENT record, in the
    report and its JSON and on the text form, untruncated; a superseded record attests nothing, so it is not listed
    (0.28.0's release read, research B1: doctor listed nothing while the refusal and warning said it lists them)."""
    from veracium import doctor
    me = record_for_this_build()
    other = record_for_this_build(machine="riscv64")
    old = record_for_this_build(machine="ppc64le", schema_version=HEAD - 1)
    with_records(monkeypatch, me, other, old)
    rep = doctor.Report(db="x", readable=False)
    doctor._check_runtime(rep)
    assert len(rep.attested_builds) == 2, rep.attested_builds
    assert any(f" on {me['machine']} {me['system']} {me['libc']} (setup-python ubuntu-24.04)" in b
               for b in rep.attested_builds), rep.attested_builds
    assert any(" on riscv64 " in b for b in rep.attested_builds) and not any("ppc64le" in b for b in rep.attested_builds)
    assert doctor.to_json(rep)["attested_builds"] == rep.attested_builds
    text = doctor.render(rep)
    assert "attested builds (2):" in text and all(b in text for b in rep.attested_builds), text


def test_a_poisoned_artifact_lists_no_build(monkeypatch):
    """attested_key's rule: a record in a poisoned artifact attests nothing, so doctor lists none of them (listing them
    would name builds the package does not attest), and says so."""
    from veracium import doctor
    with_records(monkeypatch, record_for_this_build(), record_for_this_build(machine="AMD64"))
    rep = doctor.Report(db="x", readable=False)
    doctor._check_runtime(rep)
    assert rep.attested_builds == []
    assert "no build is attested by this package" in doctor.render(rep)


@pytest.mark.parametrize("status, level, mark", [("attested", "info", "·"), ("verified", "info", "·"),
                                                 ("refused", "error", "✘")])
def test_doctor_reports_the_build_with_no_store_for_every_status(monkeypatch, tmp_path, status, level, mark):
    """INV-SA9 "before any store is opened", for a user with NO store yet (research B2: an attested build printed only
    the missing file, and a verified build's info rendered as an error). One runtime finding for every status, at its
    level and with its own mark, the attested list beneath it; the missing file is still exit 2."""
    from veracium import doctor
    st = sv.runtime_status()._replace(status=status, reason="probe x is False" if status == "refused" else None)
    monkeypatch.setattr(sv, "runtime_status", lambda: st)
    rep = doctor.diagnose(str(tmp_path / "absent.db"))
    assert [f.level for f in rep.findings if f.check == "runtime"] == [level]
    assert not rep.readable and rep.exit_code == 2
    lines = doctor.render(rep).splitlines()
    rt = [i for i, ln in enumerate(lines) if ln.strip().startswith(f"{mark} runtime")]
    assert len(rt) == 1, lines
    assert lines[rt[0] + 1].strip().startswith(("attested builds (", "no build is attested")), lines


def test_doctor_names_an_unreadable_key_field(monkeypatch):
    """0007 §4g.6 (v0.12) "names any field of the running build's key that was unreadable": such a build matches no
    record, and the report says which field and why."""
    from veracium import doctor
    st = sv.runtime_status()
    st = st._replace(status="verified", reason=None, key=None, unreadable=("libc",),
                     platform=(st.platform[0], st.platform[1], None))
    monkeypatch.setattr(sv, "runtime_status", lambda: st)
    rep = doctor.Report(db="x", readable=False)
    doctor._check_runtime(rep)
    (msg,) = [f.message for f in rep.findings if f.check == "runtime"]
    assert "unreadable key field(s): libc" in msg and "(unreadable)" in msg, msg


def test_the_compile_options_come_from_the_probe_connection(monkeypatch):
    """INV-SA12 "read them from a SQLite library other than the one the store's connections use": the digest is of
    `_probe_build()`'s options, the one scratch connection of this module's own `sqlite3`. A digest read anywhere
    else does not follow a changed probe."""
    real = sv._probe_build()
    monkeypatch.setattr(sv, "_probe_build", lambda: (real[0], ["PLANTED_OPTION_A", "PLANTED_OPTION_B"]))
    assert sv.compile_options_digest() == sv.options_digest(["PLANTED_OPTION_A", "PLANTED_OPTION_B"])


def test_machine_is_read_from_the_process_never_a_runner_label(monkeypatch):
    """INV-SA12 "take `machine` from the runner's label": a CI runner's architecture label is not the build's machine.
    With every label a runner sets planted, the key's machine is still the process's."""
    import platform as _platform
    for var, val in (("RUNNER_ARCH", "ARM64"), ("PROCESSOR_ARCHITECTURE", "ARM64"), ("HOSTTYPE", "aarch64")):
        monkeypatch.setenv(var, val)
    assert sv.canonical_platform()["machine"] == sv.canonical_machine(_platform.machine())
    assert sv.attestation_identity()["machine"] == sv.canonical_machine(_platform.machine())


def test_the_store_records_no_sqlite_build_so_the_audit_can_only_measure():
    """INV-SA11 "record the build that created the store": no schema version stores a SQLite build identity, so the
    audit has no store-side value to read in place of its measurement. This mutant has no carrier on today's code,
    and this cell fails the day one appears, which is when the mutant becomes writable."""
    names = ("sqlite_version", "sqlite_source", "compile_options", "sqlite_build")
    hits = [(v, o.ddl[:60]) for v, objs in sv.SCHEMAS.items() for o in objs if any(n in o.ddl.lower() for n in names)]
    assert hits == [], hits


def test_every_migration_step_has_a_campaign_matcher_or_a_named_reason():
    """INV-SA10 "add a `STEP_*` name with no matcher": every STEP_* the migration declares is either a step 0013-PA1's
    campaign can attribute a write to (a matcher in pa1_campaign._steps()) or a WRITELESS step named with its reason,
    so a new step can never ship with no write the campaign checks."""
    import importlib.util as _ilu
    import veracium.store.migration as mig
    spec = _ilu.spec_from_file_location("veracium_pa1_campaign_for_i6", ROOT / "specs" / "evidence" / "0013" /
                                        "pa1_campaign.py")
    camp = _ilu.module_from_spec(spec)
    spec.loader.exec_module(camp)
    declared = {v for k, v in vars(mig).items() if k.startswith("STEP_") and isinstance(v, str)}
    covered = set(camp._steps()) | set(camp.WRITELESS_STEPS)
    assert declared and declared <= covered, sorted(declared - covered)


def _synthetic_elf(path, interp: bytes, interp_off: int, size: int | None = None):
    """A minimal ELF64 little-endian image: one program header, PT_INTERP at `interp_off` (the file is sparse)."""
    import struct
    size = len(interp) if size is None else size
    hdr = bytearray(64)
    hdr[:4], hdr[4], hdr[5], hdr[6] = b"\x7fELF", 2, 1, 1
    struct.pack_into("<Q", hdr, 0x20, 64)                      # e_phoff: the table right after the header
    struct.pack_into("<HH", hdr, 0x36, 56, 1)                  # e_phentsize, e_phnum
    ph = bytearray(56)
    struct.pack_into("<I", ph, 0, 3)                           # PT_INTERP
    struct.pack_into("<Q", ph, 8, interp_off)                  # p_offset
    struct.pack_into("<Q", ph, 32, size)                       # p_filesz
    with open(path, "wb") as f:
        f.write(bytes(hdr) + bytes(ph))
        f.seek(interp_off)
        f.write(interp)


def test_pt_interp_is_read_wherever_the_segment_lies(tmp_path):
    """0007 CI run 1 (2026-10-27; research measured uv's aarch64 CPython: PT_INTERP at ~19.7 MiB in a 23 MB image).
    The reader seeks: an interpreter 20 MiB into the file reads, and canonicalises to glibc."""
    p = tmp_path / "far"
    _synthetic_elf(p, b"/lib/ld-linux-aarch64.so.1\0", 20 << 20)
    assert sv._pt_interp(str(p)) == "/lib/ld-linux-aarch64.so.1"
    assert sv.canonical_libc("Linux", sv._pt_interp(str(p))) == "glibc"


@pytest.mark.parametrize("interp, size", [(b"/lib/ld-linux-aarch64.so", 40), (b"\0", 1), (b"", 0),
                                          (b"/lib/ld-linux-aarch64.so.1", None)],
                         ids=["truncated", "empty-path", "zero-size", "unterminated"])
def test_a_short_empty_or_unterminated_pt_interp_is_none_never_empty(tmp_path, interp, size):
    """A short read, an empty path or a missing NUL is None (unreadable), never '' or a partial path."""
    p = tmp_path / "bad"
    _synthetic_elf(p, interp, 4096, size)
    assert sv._pt_interp(str(p)) is None
