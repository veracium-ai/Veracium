#!/usr/bin/env python3
"""Generated evidence: what every released version built, and on what runtime.

Separated from the schema kernel because git probing and artifact presentation
should not sit inside the trust boundary (round 5). This module *uses*
`schema_model`; nothing in `schema_model` depends on it.

**Migrations are out of `0007`'s scope from v10** -- see `specs/0006`. What
remains here is constructor output per version, which is what adoption needs.

  `--releases --write`  build a store with every released tag's own code and
                        record tag, commit sha, on-disk stamp, resolved version
                        and digest.
  `--runtime --write`   record this SQLite runtime's identity and feature probes.
  `--check`             re-derive every authoritative field and compare.
                        **Needs a git checkout**; exits 2 in an extracted archive.

**Every field is classified.** v6 said the gate re-derived everything and it did
not: an artifact with `head_digest="BAD"`, `head_schema_version=999`,
`legacy_base_versions=[999]`, `sqlite_version="0.0.0"` and every release
`result="fabricated"` passed with rc 0 (round 5, finding 4, measured). A field
kept as evidence must be checked; a field that cannot be checked must not be
kept as evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from schema_model import (GENERATED, POLICY_ARTIFACT, ROOT, SCHEMA_VERSION, SCHEMAS,
                          create, declared_policies, digest, identity, manifest,
                          resolve)

RELEASES = GENERATED / "legacy_stores.json"
VERSIONS = GENERATED / "schema_versions.json"
RUNTIMES = GENERATED / "sqlite_runtimes.json"

MANIFEST_ALGORITHM = 10

# Which recorded fields are authoritative (re-derived and compared), which are
# summaries (recomputed from the authoritative ones), and which are notes.
# `result` is authoritative and was NOT compared until round 7, finding 7:
# the gate inspected the *stored* value, so a record could describe a
# freshly unbuildable release as "ok".
AUTHORITATIVE = ("tag", "commit", "on_disk_user_version", "store_schema_version",
                 "digest", "result")
SUMMARY = ("legacy_base_versions", "head_digest", "head_schema_version")


# --------------------------------------------------------------------------
# runtime identity


def _feature_probes() -> dict:
    """Behaviours the manifest actually depends on.

    A version number names a release, not a build. Two builds of `3.45.1` can
    differ in compile options, authorizer availability and DDL support — all of
    which the exact-match model leans on (round 5, finding 6)."""
    c = sqlite3.connect(":memory:")
    out = {}
    try:
        c.execute("CREATE TABLE t (a TEXT, b TEXT GENERATED ALWAYS AS (a) VIRTUAL)")
        out["generated_columns"] = True
    except sqlite3.DatabaseError:
        out["generated_columns"] = False
    # No authorizer probe: with migrations out of 0007's scope (v10) nothing
    # here installs one. `specs/0006` owns migration confinement and should
    # probe it where it is used.
    # Round 7, finding 5: this probe used `CREATE TABLE s (a) STRICT`, which is
    # invalid -- a strict table's column must declare a datatype. It therefore
    # recorded `strict_tables: False` on a runtime that fully supports them.
    # Measured on 3.46.1. A probe that fails for the wrong reason is worse than
    # no probe: it records a false property as evidence.
    try:
        c.execute("CREATE TABLE s (a TEXT) STRICT")
        out["strict_tables"] = True
    except sqlite3.DatabaseError:
        out["strict_tables"] = False
    # ...and this one only checked that a row existed, which cannot establish
    # that DDL is stored verbatim. Submit distinctive text and compare it.
    # Writing this probe found that "verbatim" was too strong a word for what
    # the manifest actually needs. SQLite normalises the whitespace *before* the
    # object name -- `CREATE TABLE  vp` is stored as `CREATE TABLE vp` -- while
    # preserving the body exactly. The property §4a depends on is body
    # preservation, which is why two-space and one-space CHECK literals produce
    # different digests. Probe the property, not the slogan.
    marker = ("CREATE TABLE verbatim_probe ( a   TEXT ,\n"
              "  b TEXT DEFAULT 'x  y' , c TEXT CHECK(c <> 'p  q') )")
    c.execute(marker)
    stored = c.execute(
        "SELECT sql FROM sqlite_master WHERE name='verbatim_probe'").fetchone()[0]
    out["preserves_ddl_body"] = stored[stored.index("("):] == marker[marker.index("("):]
    # `table_xinfo` must expose a generated column with a nonzero hidden flag --
    # the property §4a-ii depends on.
    out["xinfo_exposes_generated"] = any(
        r[1] == "b" and int(r[6]) != 0
        for r in c.execute("SELECT * FROM pragma_table_xinfo('t')"))
    c.close()
    return out


def runtime_identity() -> dict:
    return {"sqlite_version": sqlite3.sqlite_version,
            "source_id": sqlite3.connect(":memory:").execute(
                "SELECT sqlite_source_id()").fetchone()[0],
            "features": _feature_probes()}


_RUNTIME_OVERRIDE: list = []


def qualified_runtimes() -> list:
    """Recorded runtimes — or the prospective set, while `write_runtime()` is
    validating a pair it has not published yet."""
    if _RUNTIME_OVERRIDE:
        return _RUNTIME_OVERRIDE[0]
    return json.loads(RUNTIMES.read_text())["runtimes"] if RUNTIMES.exists() else []


def _stage(path: pathlib.Path, text: str) -> pathlib.Path:
    """Write the new content beside its target, without publishing it.

    **The residual limit, stated rather than claimed away:** two renames are not
    one transaction. A crash between them can still leave the pair disagreeing.
    **The honest atomic boundary is the git commit**, and `--check` fails on a
    disagreeing pair — which is the guarantee that actually holds."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    return tmp


def runtime_record_problems(r: dict) -> list:
    """Whether a recorded runtime is complete enough to qualify anything.

    **Round 6, finding 4: an empty `constructor_digests` qualified vacuously**,
    because `all(...)` over an empty mapping is `True`. Measured. Completeness
    is now a precondition, and the key set must *equal* the declared schema
    versions rather than being whatever happened to be recorded."""
    problems = []
    for field in ("sqlite_version", "source_id", "features", "constructor_digests",
                  "manifestations", "manifest_algorithm", "schema_version"):
        if field not in r:
            problems.append(f"runtime record is missing {field!r}")
    if problems:
        return problems
    if r["manifest_algorithm"] != MANIFEST_ALGORITHM:
        problems.append(f"runtime record uses manifest algorithm "
                        f"{r['manifest_algorithm']}, build uses {MANIFEST_ALGORITHM}")
    if r["schema_version"] != SCHEMA_VERSION:
        problems.append(f"runtime record is for schema version {r['schema_version']}, "
                        f"build declares {SCHEMA_VERSION}")
    want = {str(v) for v in SCHEMAS}
    if set(r["constructor_digests"]) != want:
        problems.append(f"runtime record covers versions "
                        f"{sorted(r['constructor_digests'])}, build declares "
                        f"{sorted(want)}")
    if not r["constructor_digests"]:
        problems.append("runtime record has no constructor digests")
    if not r["features"]:
        problems.append("runtime record has no feature probes")
    for name, must in (("preserves_ddl_body", True),
                       ("xinfo_exposes_generated", True)):
        if r["features"].get(name) is not must:
            problems.append(f"runtime fails a required behaviour: {name}")
    # **Round 8, finding 2: `manifestations` was load-bearing and unvalidated.**
    # `build_version_artifact()` imports object records from every runtime
    # record, so an added `CREATE TRIGGER evil ... DELETE FROM edges` became an
    # accepted version-1 shape while `runtime_record_problems()` returned `[]`
    # and `runtime_supported()` returned True. Measured. That falsifies the
    # headline guarantee -- an unrecognised store was recognised.
    want_prov = {f"constructor v{v}" for v in SCHEMAS}
    if set(r["manifestations"]) != want_prov:
        problems.append(f"runtime manifestations {sorted(r['manifestations'])} "
                        f"are not exactly {sorted(want_prov)}")
    else:
        for v in SCHEMAS:
            objs = r["manifestations"][f"constructor v{v}"]
            recorded = r["constructor_digests"].get(str(v))
            if _digest_of_identity(objs, v) != recorded:
                problems.append(f"manifestation 'constructor v{v}' does not hash "
                                f"to its recorded digest — the object records and "
                                f"the digest disagree")
            problems.extend(manifestation_problems(objs, v))
    return problems


def _identity_key(r: dict) -> tuple:
    return (r.get("sqlite_version"), r.get("source_id"),
            json.dumps(r.get("features"), sort_keys=True),
            r.get("manifest_algorithm"), r.get("schema_version"))


def artifact_problems(records=None) -> list:
    """Problems visible only across the whole runtime artifact.

    **Round 9, finding 1b: two individually valid records with the SAME runtime
    identity and DIFFERENT constructor output both passed.** Measured. One
    SQLite build cannot legitimately produce two different constructor outputs,
    so the artifact is self-contradictory — and a per-record validator cannot
    see it, because each record is internally consistent.

    Duplicate identity is rejected outright rather than resolved: picking one
    would be guessing which record is the forgery."""
    records = qualified_runtimes() if records is None else records
    problems, seen = [], {}
    for r in records:
        key = _identity_key(r)
        if key in seen:
            if seen[key] != r.get("constructor_digests"):
                problems.append(
                    f"two runtime records share identity {key[0]!r}/{key[1][:20]!r} "
                    f"but declare different constructor output — the artifact is "
                    f"self-contradictory and neither can be trusted")
            else:
                problems.append(f"duplicate runtime record for {key[0]!r}")
        seen[key] = r.get("constructor_digests")
    return problems


def manifestation_problems(objs: dict, version: int) -> list:
    """Undeclared persistent objects in a recorded manifestation.

    **Round 9, finding 1a: a *self-consistent* fabrication was accepted.** v11
    only checked that a manifestation hashed to its recorded digest — so adding
    a trigger AND updating the digest passed, and the trigger became an accepted
    version-1 shape. Measured.

    Hashing proves internal consistency, **not provenance**. This is the
    independent check the reviewer asked for: a manifestation may contain only
    objects this build declares, whatever runtime claims to have produced it."""
    declared = {f"{o.kind}:{o.name}" for o in SCHEMAS[version]}
    return [f"manifestation for v{version} contains undeclared object {k!r}"
            for k in sorted(set(objs) - declared)]


def runtime_supported() -> bool:
    """**Derived from the evidence artifact, never from a hand-edited tuple.**

    Qualification means: a *complete* recorded runtime whose version, source id
    and feature probes match this process, and whose recorded constructor
    digests all reproduce here. **`specs/0013` adds per-path migration digests**
    when migrations exist -- DDL rewriting is why a version can have several
    accepted manifests -- but at `SCHEMA_VERSION = 1` there are no paths."""
    me = runtime_identity()
    for r in qualified_runtimes():
        if runtime_record_problems(r):
            continue
        if not (r["sqlite_version"] == me["sqlite_version"]
                and r["source_id"] == me["source_id"]
                and r["features"] == me["features"]):
            continue
        return all(_constructor_digest(int(v)) == d
                   for v, d in r["constructor_digests"].items())
    return False


def build_runtime_record() -> dict:
    me = runtime_identity()
    me["manifest_algorithm"] = MANIFEST_ALGORITHM
    me["schema_version"] = SCHEMA_VERSION
    me["constructor_digests"] = {str(v): _constructor_digest(v) for v in sorted(SCHEMAS)}
    # Full object records, not only digests: a second qualified runtime's
    # manifestations must be reconstructible, and an object-level `diff` cannot
    # be built from a digest (round 7, finding 4).
    me["manifestations"] = {f"constructor v{v}": _constructor_objects(v)
                            for v in sorted(SCHEMAS)}
    return me


def _digest_of_identity(objs: dict, version: int) -> str:
    """Digest a recorded identity mapping without rebuilding the database."""
    from schema_model import rebuildable_keys
    import hashlib as _h
    skip = rebuildable_keys(version)
    scoped = {k: v for k, v in objs.items() if tuple(k.split(":", 1)) not in skip}
    return _h.sha256(
        json.dumps(scoped, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _constructor_objects(version: int) -> dict:
    c = sqlite3.connect(":memory:")
    create(c, version)
    o = identity(manifest(c))
    c.close()
    return o


def write_runtime(force: bool = False) -> int:
    """Record **this** runtime as qualified. Round 6, finding 5: `--runtime
    --write` was documented and did nothing — the flag was ignored on that path,
    so the stated workflow for qualifying a second runtime did not exist."""
    rec = build_runtime_record()
    problems = runtime_record_problems(rec)
    if problems and not force:
        for p in problems:
            print(p, file=sys.stderr)
        print("refusing to write incomplete runtime evidence", file=sys.stderr)
        return 1
    others = [r for r in qualified_runtimes()
              if (r.get("source_id"), r.get("sqlite_version")) !=
                 (rec["source_id"], rec["sqlite_version"])]
    GENERATED.mkdir(parents=True, exist_ok=True)

    # **Round 8, finding 3: qualification must be atomic at the artifact level.**
    # v10 wrote only `sqlite_runtimes.json` and reported success, leaving
    # `schema_versions.json` byte-for-byte unchanged. Measured by adding 3.46.1:
    # rc 0, two runtime records, accepted provenance still "constructor v1"
    # only. On those two runtimes the digests agree so nothing broke -- but when
    # a runtime produces different stored DDL, which is the entire reason the
    # union model exists, it would be marked qualified while the stores it
    # creates were NOT in MANIFESTS.
    # **Round 9, finding 2: the "both or neither" claim was false.** v11 wrote
    # the runtime file first and restored it only on `SystemExit`; an ordinary
    # `OSError` from the second write left a qualified-but-stale artifact.
    # Measured against a simulated disk failure.
    #
    # The order is now: build and validate the complete prospective pair in
    # memory, then publish both by atomic rename. A crash between the two
    # renames is still possible -- **os.replace is per-file, not a two-file
    # transaction** -- so the honest boundary is the git commit, and `--check`
    # fails on a disagreeing pair. That limit is stated rather than claimed
    # away.
    prospective = {"runtimes": others + [rec]}
    saved_runtimes = qualified_runtimes()
    try:
        _RUNTIME_OVERRIDE.append(prospective["runtimes"])
        versions = build_version_artifact()
        accepted = {a["digest"] for recs in versions["versions"].values()
                    for a in recs["accepted"]}
        for rt in prospective["runtimes"]:
            if runtime_record_problems(rt) or rt.get("manifest_algorithm") != MANIFEST_ALGORITHM:
                continue
            for prov, objs in rt["manifestations"].items():
                v = int(prov.rsplit("v", 1)[1])
                if _digest_of_identity(objs, v) not in accepted:
                    raise SystemExit(f"runtime output {prov} @ "
                                     f"{rt['sqlite_version']} is not in the "
                                     f"accepted set")
    except Exception as exc:                     # validation OR filesystem
        print(f"qualification refused, artifacts unchanged: {exc}", file=sys.stderr)
        return 1
    finally:
        _RUNTIME_OVERRIDE.clear()

    # Stage BOTH temporaries before renaming either, so a filesystem failure
    # happens while nothing is published. The two renames are then back to back,
    # and the first is rolled back if the second fails.
    saved = RUNTIMES.read_text() if RUNTIMES.exists() else None
    try:
        t_rt = _stage(RUNTIMES, json.dumps(prospective, indent=2) + "\n")
        t_vs = _stage(VERSIONS, json.dumps(versions, indent=2) + "\n")
    except OSError as exc:
        print(f"staging failed, nothing published: {exc}", file=sys.stderr)
        return 1
    try:
        t_rt.replace(RUNTIMES)
        t_vs.replace(VERSIONS)
    except OSError as exc:
        if saved is None:
            RUNTIMES.unlink(missing_ok=True)
        else:
            RUNTIMES.write_text(saved)
        print(f"publish failed and was rolled back: {exc}", file=sys.stderr)
        return 1
    active = sum(1 for r in prospective["runtimes"]
                 if r.get("manifest_algorithm") == MANIFEST_ALGORITHM
                 and not runtime_record_problems(r))
    stale = len(prospective["runtimes"]) - active
    # Round 9: superseded records were counted as "qualified". They are not.
    print(f"recorded {rec['sqlite_version']} ({rec['source_id'][:20]}…) — "
          f"{active} active, {stale} superseded or invalid; accepted manifests "
          f"updated")
    if stale:
        print(f"note: {stale} record(s) contribute nothing and --check will fail "
              f"until they are regenerated or removed")
    return 0


def _constructor_digest(version: int) -> str:
    c = sqlite3.connect(":memory:")
    create(c, version)
    d = digest(manifest(c), version)
    c.close()
    return d


# --------------------------------------------------------------------------
# accepted manifests per version


def build_version_artifact(strict: bool = True) -> dict:
    """Regenerate accepted manifests. Historical versions are immutable.

    Two guards, both from round 5's finding 5:

      * a historical version that regenerates *differently* is an error (v6 had
        this);
      * a historical version that is **missing** is also an error (v6 did not —
        running the generator with version 1 dropped from `SCHEMAS` silently
        emitted an artifact without it).

    Generation is bound to the declared `SCHEMA_VERSION`, not `max(SCHEMAS)`."""
    existing = (json.loads(VERSIONS.read_text()).get("versions", {})
                if VERSIONS.exists() else {})
    from schema_model import validate_schema_registry
    out, problems = {}, validate_schema_registry()

    for version in sorted(SCHEMAS):
        accepted = []
        c = sqlite3.connect(":memory:")
        create(c, version)
        accepted.append({"provenance": f"constructor v{version}",
                         "digest": digest(manifest(c), version),
                         "objects": identity(manifest(c))})
        c.close()
        # **Round 7, finding 4: accepted manifests are the union across every
        # qualified runtime.** v8 regenerated the current version solely from
        # the runtime running the command, so qualifying a second runtime whose
        # DDL differs would mark it qualified while stores it creates were not
        # in MANIFESTS -- and regenerating there would delete the first
        # runtime's manifestation. Measured: an inserted foreign manifestation
        # was silently dropped.
        have = {a["digest"] for a in accepted}
        problems.extend(artifact_problems())
        for rt in qualified_runtimes():
            # A record written under an older manifest algorithm describes a
            # different computation. It is **superseded, not fraudulent**: it
            # contributes nothing and is reported, but it does not block
            # regeneration -- otherwise bumping the algorithm deadlocks, since
            # the artifact can only be rewritten by a run that first refuses to
            # read it. Skipping is fail-closed: nothing it holds is accepted.
            if rt.get("manifest_algorithm") != MANIFEST_ALGORITHM:
                print(f"note: runtime {rt.get('sqlite_version')!r} was recorded "
                      f"under manifest algorithm {rt.get('manifest_algorithm')}; "
                      f"re-run --runtime --write there to qualify it again")
                continue
            if runtime_record_problems(rt):
                problems.append(f"runtime record for sqlite "
                                f"{rt.get('sqlite_version')!r} is invalid and "
                                f"contributes no accepted manifest: "
                                f"{runtime_record_problems(rt)[0]}")
                continue
            # **Attestation, round 9 finding 1.** A record's objects agreeing
            # with its own digest proves internal consistency, not that the
            # claimed runtime produced them. Until a CI job attests a foreign
            # runtime, the only record that may contribute is one this process
            # can REPRODUCE -- and reproducing means running the constructor
            # here and getting the same objects.
            if _identity_key(rt) != _identity_key(build_runtime_record()):
                print(f"note: runtime {rt.get('sqlite_version')!r} is recorded but "
                      f"not attested by this process; it contributes no accepted "
                      f"manifest until a job on that runtime regenerates it")
                continue
            for v in SCHEMAS:
                if rt["manifestations"][f"constructor v{v}"] != _constructor_objects(v):
                    problems.append(
                        f"runtime {rt.get('sqlite_version')!r} claims a v{v} "
                        f"manifestation this process does not reproduce")
            for prov, objs in (rt.get("manifestations") or {}).items():
                if not prov.endswith(f"v{version}") and prov != f"constructor v{version}":
                    continue
                d = _digest_of_identity(objs, version)
                if d in have:
                    continue
                have.add(d)
                accepted.append({
                    "provenance": f"{prov} @ sqlite {rt['sqlite_version']}",
                    "digest": d, "objects": objs})
        record = {"accepted": accepted}
        if version < SCHEMA_VERSION and str(version) in existing:
            if existing[str(version)] != record:
                problems.append(
                    f"version {version} is historical and regenerates differently. "
                    f"Historical manifests are immutable; a manifest-algorithm "
                    f"change needs a separately reviewed artifact migration.")
            out[str(version)] = existing[str(version)]
        else:
            out[str(version)] = record

    for key in existing:
        if key not in out:
            problems.append(
                f"version {key} is recorded but this build no longer declares it. "
                f"Deleting or renumbering a historical version is an error.")
            out[key] = existing[key]

    if problems and strict:
        raise SystemExit("\n".join(problems))
    return {"manifest_algorithm": MANIFEST_ALGORITHM, "schema_version": SCHEMA_VERSION,
            "versions": out}


def legacy_base_versions() -> frozenset:
    """Versions whose release evidence shows a genuinely **unstamped** store.

    The only candidates version-zero resolution may try (round 5, finding 3)."""
    if not RELEASES.exists():
        # **Fails closed** (round 6, finding 7). v7 returned {SCHEMA_VERSION},
        # which silently authorised adoption using the very evidence that was
        # missing. No verified legacy artifact means no adoption candidates.
        return frozenset()
    return frozenset(
        r["store_schema_version"] for r in json.loads(RELEASES.read_text())["releases"]
        if r.get("on_disk_user_version") == 0 and r.get("store_schema_version"))


# --------------------------------------------------------------------------
# release probing


def _git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def _tags() -> list:
    return sorted((t for t in _git("tag").split() if t.startswith("v")),
                  key=lambda t: [int(x) for x in t.lstrip("v").split(".")])


def _probe_at(ref: str, work: pathlib.Path) -> dict:
    """Build a store with the code at `ref`. The creating code is that release's."""
    row = {"tag": ref, "commit": _git("rev-list", "-n1", ref),
           "on_disk_user_version": None, "store_schema_version": None,
           "digest": None, "result": None}
    wt = work / ref.replace("/", "_")
    if subprocess.run(["git", "worktree", "add", "-q", "--detach", str(wt), ref],
                      cwd=ROOT, capture_output=True).returncode:
        row["result"] = "worktree failed"
        return row
    try:
        db = str(wt / "probe.db")
        r = subprocess.run(
            [sys.executable, "-c",
             f"from veracium.store.sqlite import SqliteStore; SqliteStore({db!r})"],
            cwd=wt, env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True)
        if r.returncode:
            row["result"] = f"unbuildable: {r.stderr.strip().splitlines()[-1][:80]}"
            return row
        c = sqlite3.connect(db)
        row["on_disk_user_version"] = c.execute("PRAGMA user_version").fetchone()[0]
        row["_objects"] = {tuple(k.split(":", 1)): v
                           for k, v in identity(manifest(c)).items()}
        c.close()
        row["result"] = "ok"
        return row
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=ROOT, capture_output=True)


def _resolved(row: dict, records: dict, candidates=None) -> dict:
    objs = row.pop("_objects", {})
    v = resolve(objs, records, candidates)
    row["store_schema_version"] = v
    row["digest"] = None if v is None else digest(objs, v)
    return row


def releases(write: bool) -> int:
    records = build_version_artifact()["versions"]
    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _resolved(_probe_at("HEAD", work), records)
        rows = [_resolved(_probe_at(t, work), records) for t in _tags()]

    unknown = [r for r in rows if r["result"] == "ok" and r["store_schema_version"] is None]
    broken = [r for r in rows if r["result"] != "ok"]
    bad_stamp = [r for r in rows if r["result"] == "ok"
                 and r["on_disk_user_version"] not in (0, r["store_schema_version"])]
    for r in rows:
        v, st = r["store_schema_version"], r["on_disk_user_version"]
        mark = (r["result"] if r["result"] != "ok"
                else f"schema v{v}, " + ("unstamped (legacy)" if st == 0 else f"stamped {st}")
                if v is not None else "** UNKNOWN MANIFEST **")
        print(f"  {r['tag']:<10} {r['commit'][:12]}  {mark}")
    legacy = sorted({r["store_schema_version"] for r in rows
                     if r["on_disk_user_version"] == 0 and r["store_schema_version"]})
    print(f"\n{len(rows) - len(unknown) - len(broken)}/{len(rows)} resolve to a known "
          f"version · {len(broken)} unbuildable · legacy bases {legacy} · "
          f"sqlite {sqlite3.sqlite_version}")

    if write:
        GENERATED.mkdir(parents=True, exist_ok=True)
        RELEASES.write_text(json.dumps({
            "manifest_algorithm": MANIFEST_ALGORITHM,
            "head_digest": head["digest"],
            "head_schema_version": head["store_schema_version"],
            "legacy_base_versions": legacy,
            "releases": rows,
        }, indent=2) + "\n")
        VERSIONS.write_text(json.dumps(build_version_artifact(), indent=2) + "\n")
        POLICY_ARTIFACT.write_text(json.dumps(
            {str(v): declared_policies(v) for v in sorted(SCHEMAS)}, indent=2) + "\n")
        if write_runtime() != 0:
            print("runtime evidence was not written", file=sys.stderr)
            return 1
        print(f"wrote {RELEASES.name}, {VERSIONS.name}, {POLICY_ARTIFACT.name}")
    return 1 if (unknown or broken or bad_stamp) else 0


def check() -> int:
    if subprocess.run(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                      capture_output=True).returncode:
        print("--check needs a git checkout: it rebuilds a store from every "
              "released tag. An extracted archive has no git metadata.",
              file=sys.stderr)
        return 2
    if not RELEASES.exists():
        print(f"{RELEASES.name} missing — run --releases --write", file=sys.stderr)
        return 1
    stored = json.loads(RELEASES.read_text())
    generated = build_version_artifact()
    records = generated["versions"]
    bad = []

    if stored.get("manifest_algorithm") != MANIFEST_ALGORITHM:
        bad.append(f"manifest algorithm: artifact {stored.get('manifest_algorithm')} "
                   f"vs build {MANIFEST_ALGORITHM}")
    if VERSIONS.exists() and json.loads(VERSIONS.read_text()) != generated:
        bad.append("schema_versions.json does not match what this build generates")
    if POLICY_ARTIFACT.exists():
        want = {str(v): declared_policies(v) for v in sorted(SCHEMAS)}
        if json.loads(POLICY_ARTIFACT.read_text()) != want:
            bad.append("schema_policy.json disagrees with the registry's policies")
    else:
        bad.append(f"{POLICY_ARTIFACT.name} missing")
    if not runtime_supported():
        bad.append(f"sqlite {sqlite3.sqlite_version} is not a qualified runtime "
                   f"(see {RUNTIMES.name}); 0007 §4a-viii refuses it")
    # Every stored record, not merely the one this process matches: an invalid
    # record beside a valid one still feeds the accepted set.
    for rt in qualified_runtimes():
        if rt.get("manifest_algorithm") != MANIFEST_ALGORITHM:
            bad.append(f"runtime {rt.get('sqlite_version')!r} was recorded under "
                       f"manifest algorithm {rt.get('manifest_algorithm')}, build "
                       f"uses {MANIFEST_ALGORITHM} — re-qualify it")
            continue
        for p in runtime_record_problems(rt):
            bad.append(f"runtime {rt.get('sqlite_version')!r}: {p}")

    with tempfile.TemporaryDirectory() as tmp:
        work = pathlib.Path(tmp)
        head = _resolved(_probe_at("HEAD", work), records)
        fresh = {r["tag"]: _resolved(r, records)
                 for r in (_probe_at(t, work) for t in _tags())}

    # every AUTHORITATIVE field re-derived, not just the version
    for row in stored["releases"]:
        now = fresh.get(row["tag"])
        if now is None:
            bad.append(f"{row['tag']}: recorded but no longer a tag")
            continue
        for field in AUTHORITATIVE:
            if now.get(field) != row.get(field):
                bad.append(f"{row['tag']}: {field} recorded {row.get(field)!r}, "
                           f"re-derived {now.get(field)!r}")
        if now.get("result") != "ok":
            bad.append(f"{row['tag']}: freshly probed result "
                       f"{now.get('result')!r}")
    for t in _tags():
        if t not in {r["tag"] for r in stored["releases"]}:
            bad.append(f"{t}: released since the artifact was generated")

    # SUMMARY fields recomputed from the authoritative ones
    want_legacy = sorted({r["store_schema_version"] for r in fresh.values()
                          if r["on_disk_user_version"] == 0 and r["store_schema_version"]})
    if stored.get("legacy_base_versions") != want_legacy:
        bad.append(f"legacy_base_versions recorded {stored.get('legacy_base_versions')}, "
                   f"recomputed {want_legacy}")
    if stored.get("head_digest") != head["digest"]:
        bad.append("head_digest does not match a freshly built HEAD")
    if stored.get("head_schema_version") != head["store_schema_version"]:
        bad.append(f"head_schema_version recorded {stored.get('head_schema_version')}, "
                   f"re-derived {head['store_schema_version']}")

    for b in bad:
        print(b, file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} problem(s) — run --releases --write", file=sys.stderr)
        return 1
    print(f"evidence current — {len(stored['releases'])} releases, legacy bases "
          f"{want_legacy}, HEAD at v{head['store_schema_version']}, "
          f"sqlite {sqlite3.sqlite_version} qualified")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--releases", action="store_true")
    ap.add_argument("--runtime", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.releases:
        return releases(a.write)
    if a.runtime:
        if a.write:
            return write_runtime()
        print(json.dumps(build_runtime_record(), indent=2))
        print("qualified:", runtime_supported())
        return 0
    if a.check:
        return check()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
