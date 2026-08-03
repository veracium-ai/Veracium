#!/usr/bin/env python3
"""Generated evidence: what every released version built, and on what runtime.

Separated from the schema kernel because git probing and artifact presentation
should not sit inside the trust boundary (round 5). This module *uses*
`schema_model`; nothing in `schema_model` depends on it.

**Migrations are out of `0007`'s scope from v10** -- see `specs/0013`. What
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

MANIFEST_ALGORITHM = 13

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
    # here installs one. `specs/0013` owns migration confinement and should
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
        # Recorded as part of runtime identity, but NOT required: nothing in
        # `0007`'s schema matching uses strict tables (round 11). Being explicit
        # beats listing it among required behaviours and not enforcing it.
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


def _discard(*tmps) -> None:
    """Remove staged temporaries. v12 left `sqlite_runtimes.json.tmp` behind and
    it shipped in the review package (round 10)."""
    for t in tmps:
        try:
            t.unlink(missing_ok=True)
        except OSError:
            pass


def _structure_problems(r) -> list:
    """Type errors in a record, found before any field is USED.

    **Round 13, finding 2: the validator was not total.** `features = []` raised
    `AttributeError`, `constructor_digests = 1` raised `TypeError` — measured —
    so a malformed record beside a valid one made `runtime_supported()` escape
    with an implementation exception instead of returning False, and the caller
    never saw the closed `unsupported-sqlite` outcome.

    And the evidence-revision fields were untyped: `manifest_algorithm = 13.0`
    with `schema_version = True` passed and qualified, the same Python-equality
    class (`True == 1`, `13.0 == 13`) that round 12 fixed for features.
    **`type(v) is int`, never `isinstance`** — bool is an int subclass."""
    if not isinstance(r, dict):
        return [f"runtime record is {type(r).__name__}, not a mapping"]
    problems = []
    for field in ("sqlite_version", "source_id"):
        v = r.get(field)
        if not isinstance(v, str) or not v:
            problems.append(f"{field!r} must be a nonempty string")
    for field in ("manifest_algorithm", "schema_version"):
        if type(r.get(field)) is not int:
            problems.append(f"{field!r} must be an int, is "
                            f"{type(r.get(field)).__name__}")
    if not isinstance(r.get("features"), dict):
        problems.append(f"'features' must be a mapping, is "
                        f"{type(r.get('features')).__name__}")
    if not isinstance(r.get("constructor_digests"), dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in (r.get("constructor_digests") or {}).items()
            if isinstance(r.get("constructor_digests"), dict)):
        problems.append("'constructor_digests' must map str to str")
    m = r.get("manifestations")
    if not isinstance(m, dict) or not all(
            isinstance(k, str) and isinstance(v, dict) for k, v in (m or {}).items()
            if isinstance(m, dict)):
        problems.append("'manifestations' must map str to mappings")
    return problems


def runtime_record_problems(r) -> list:
    """Whether a recorded runtime is complete enough to qualify anything.

    **Total**: returns problems for any input, never raises (round 13). The
    empty-mapping vacuity (round 6), exact key sets (rounds 9/11/12) and typed
    features (round 12) all live behind the structural gate."""
    problems = _structure_problems(r)
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
    if set(r["features"]) != FEATURE_KEYS:
        problems.append(f"feature keys {sorted(r['features'])} are not exactly "
                        f"{sorted(FEATURE_KEYS)}")
    for k, v in r["features"].items():
        if type(v) is not bool:
            problems.append(f"feature {k!r} is {type(v).__name__}, not bool")
    for name in ("preserves_ddl_body", "xinfo_exposes_generated"):
        if r["features"].get(name) is not True:
            problems.append(f"runtime fails a required behaviour: {name}")
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


FEATURE_KEYS = frozenset({"generated_columns", "strict_tables",
                          "preserves_ddl_body", "xinfo_exposes_generated"})
"""The closed feature vocabulary. Every probe result is a real bool -- round 12
measured `strict_tables: 1` passing dict equality because Python's `1 == True`,
while the canonical JSON identity correctly distinguished them, so the
production predicate and the declared identity disagreed."""


def build_identity(r: dict) -> tuple:
    """**RuntimeBuildIdentity: which SQLite build this is.**

    Round 12, finding 1: v14 declared one canonical five-field key and then used
    `(version, source_id)` for replacement anyway — so a record with the same
    version and source id but *different feature results* was silently replaced,
    though the spec itself says a source id does not identify compile options.
    The reviewer's split is adopted: **build identity** (version, source id,
    canonical typed features) is what one-active enforcement, matching,
    replacement, attestation and reporting key on; **evidence revision**
    (manifest algorithm, schema version) is merely which revision of the record
    format described it."""
    return (r.get("sqlite_version"), r.get("source_id"),
            json.dumps(r.get("features"), sort_keys=True))


def _identity_key(r: dict) -> tuple:
    """Build identity plus the evidence revision — for exact-duplicate checks."""
    return build_identity(r) + (r.get("manifest_algorithm"), r.get("schema_version"))


def active_records(records=None) -> list:
    """Records that are current-algorithm and internally valid."""
    records = qualified_runtimes() if records is None else records
    return [r for r in records
            if r.get("manifest_algorithm") == MANIFEST_ALGORITHM
            and not runtime_record_problems(r)]


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
    if not isinstance(records, list):
        return [f"runtime artifact is {type(records).__name__}, not a list"]
    problems, seen = [], {}

    def _current(r):
        """Round 13, finding 3: every production check is scoped to
        current-algorithm records. Superseded ones contribute nothing and
        cannot disqualify; `--check` reports them for repository cleanup."""
        return isinstance(r, dict) and r.get("manifest_algorithm") == MANIFEST_ALGORITHM

    for r in records:
        if not isinstance(r, dict):
            problems.append(f"runtime artifact contains a {type(r).__name__}, "
                            f"not a record")
    records = [r for r in records if isinstance(r, dict)]
    # **Round 10, finding 2: `0007` supports exactly ONE active runtime.**
    # v12 described a cross-runtime union and could not construct it: on runtime
    # A only A contributes, on B only B, and nothing persists an attestation
    # that A was reproduced by its own job. `write_runtime()` then refused a
    # second differing runtime outright, because it required every valid
    # prospective manifestation to be in an accepted set that excluded it.
    # **A half-built union is worse than an honest single-runtime contract**, so
    # the union claim is withdrawn and S-Q7 owns widening it with durable
    # per-runtime attestation.
    # **Round 12, finding 3: a malformed CURRENT-algorithm record must poison
    # the artifact, not be skipped.** A record at an older algorithm is
    # superseded and ignored; a current-algorithm record that fails validation
    # is evidence of tampering or generator breakage, and the safe reading of
    # such an artifact is "unqualified".
    for r in records:
        if not _current(r):
            continue
        for p in runtime_record_problems(r):
            problems.append(f"current-algorithm record for "
                            f"{r.get('sqlite_version')!r}: {p}")
    identities = {build_identity(r) for r in active_records(records)}
    if len(identities) > 1:
        problems.append(
            f"{len(identities)} active runtime build identities recorded "
            f"({sorted(i[0] for i in identities)}); `0007` supports exactly one. "
            f"Durable cross-runtime attestation is S-Q7.")
    # Two current-algorithm records agreeing on version+source_id but differing
    # on probes are one build described inconsistently -- one build cannot have
    # two probe results under the same probe definitions.
    by_build = {}
    for r in records:
        if not _current(r):
            continue
        by_build.setdefault((r.get("sqlite_version"), r.get("source_id")),
                            set()).add(build_identity(r))
    for build, keys in sorted(by_build.items()):
        if len(keys) > 1:
            problems.append(
                f"runtime {build[0]!r} has {len(keys)} current-algorithm records "
                f"that disagree on probes — one build cannot have two")
    # Scoped to current-algorithm records (round 13, finding 3): a stale
    # duplicate is a cleanup item for --check, not a startup failure.
    for r in records:
        if not _current(r):
            continue
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
    """A recorded manifestation must be EXACTLY the declared object set.

    Round 9, finding 1a: a self-consistent fabrication was accepted — hashing
    proves internal consistency, not provenance, so a manifestation may contain
    only objects this build declares.

    **Round 12, finding 2: "no extras" was only half of "exact".** A record with
    a *missing* object — including a missing required table — passed the
    validator once its digest was updated to match, and only the production
    predicate's separate full-comparison recovered safety. The key set must
    equal the declaration, and every entry must have the closed field shape."""
    declared = {f"{o.kind}:{o.name}" for o in SCHEMAS[version]}
    problems = [f"manifestation for v{version} contains undeclared object {k!r}"
                for k in sorted(set(objs) - declared)]
    problems += [f"manifestation for v{version} is missing declared object {k!r}"
                 for k in sorted(declared - set(objs))]
    for k, entry in sorted(objs.items()):
        if not isinstance(entry, dict):
            problems.append(f"object {k!r} is not a mapping")
            continue
        # A genuinely closed structure: exact field set, typed fields, exact
        # column-row width. Round 13's correction — "closed" had meant only
        # "these fields are present", so arbitrary extras and mistyped values
        # passed.
        want_fields = ({"type", "table", "sql", "columns"} if k.startswith("table:")
                       else {"type", "table", "sql"})
        if set(entry) != want_fields:
            problems.append(f"object {k!r} fields {sorted(entry)} are not exactly "
                            f"{sorted(want_fields)}")
            continue
        for f in ("type", "table"):
            if not isinstance(entry[f], str):
                problems.append(f"object {k!r} field {f!r} is not a string")
        if entry["sql"] is not None and not isinstance(entry["sql"], str):
            problems.append(f"object {k!r} field 'sql' is neither string nor null")
        if k.startswith("table:"):
            cols = entry["columns"]
            if not isinstance(cols, list):
                problems.append(f"table {k!r} columns is not a list")
            else:
                for row in cols:
                    if (not isinstance(row, list) or len(row) != 6
                            or not isinstance(row[0], str)
                            or not isinstance(row[1], str)
                            or type(row[2]) is not int
                            or not (row[3] is None or isinstance(row[3], str))
                            or type(row[4]) is not int
                            or type(row[5]) is not int):
                        problems.append(f"table {k!r} has a malformed column row")
                        break
    return problems


def runtime_supported() -> bool:
    """**Derived from the evidence artifact, never from a hand-edited tuple.**

    Qualification means: a *complete* recorded runtime whose identity matches
    this process, and whose recorded **complete constructor manifestations**
    reproduce here.

    **Round 11, finding 2: comparing digests was not enough.** The acceptance
    digest deliberately excludes rebuildable indexes, so a record claiming
    `CREATE UNIQUE INDEX ix_edges_subj_rel ON edges(user_id)` reproduced its
    digest exactly while describing an index that changes which writes succeed.
    Measured: the generator caught it, this predicate did not — the same
    wrong-place class round 10's finding 1 was about."""
    # **Total, fail-closed** (round 13, finding 2). Malformed JSON, a missing
    # `runtimes` member, wrong containers, or any validator escape must yield
    # False — the caller's closed outcome is `unsupported-sqlite`, never an
    # implementation exception escaping into the open path. The release check
    # is where diagnostics belong; this predicate only answers the question.
    try:
        records = qualified_runtimes()
        # Round 10, finding 1: the production-facing predicate must see
        # artifact-level conflicts, not only the generator.
        if artifact_problems(records):
            return False
        me = runtime_identity()
        for r in records:
            # Superseded records contribute nothing and cannot disqualify
            # (round 13, finding 3); malformed CURRENT records already poisoned
            # the artifact above.
            if not isinstance(r, dict) or runtime_record_problems(r):
                continue
            # Canonical build identity, never raw dict equality: `1 == True` in
            # Python, so a mistyped probe made the two disagree (round 12).
            if build_identity(r) != build_identity({**me,
                    "manifest_algorithm": MANIFEST_ALGORITHM,
                    "schema_version": SCHEMA_VERSION}):
                continue
            if any(_constructor_digest(int(v)) != d
                   for v, d in r["constructor_digests"].items()):
                return False
            # The complete manifestation, including rebuildable objects.
            return all(r["manifestations"].get(f"constructor v{v}")
                       == _constructor_objects(v) for v in SCHEMAS)
        return False
    except Exception:
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
    # **Replacement is by build identity, with one carve-out for superseded
    # revisions** (round 12, finding 1). Same build identity -> replaced: that
    # is a new evidence revision of the same build. Same (version, source_id)
    # at an OLDER algorithm -> also replaced, because probe definitions may
    # have changed with the algorithm and the old record is superseded either
    # way; this is what clears a bump without deadlocking. Same (version,
    # source_id), CURRENT algorithm, different probes -> kept, and
    # `artifact_problems()` refuses the contradiction rather than this code
    # silently deciding which record to believe.
    # **Round 13, finding 1: the evidence revision must be MONOTONE.** v15's
    # rule was "!= current algorithm", which read as "older" in the comments and
    # meant "any other" in the code — so an old checkout silently overwrote
    # evidence generated by newer code (a record at algorithm 14 became 13, and
    # a schema-version-2 record became 1; both measured, rc 0). Downgrading
    # evidence is the reverse of superseding it. A FUTURE component refuses.
    def _newer(r):
        if not isinstance(r, dict):
            return False
        alg, sv = r.get("manifest_algorithm"), r.get("schema_version")
        return ((type(alg) is int and alg > MANIFEST_ALGORITHM)
                or (type(sv) is int and sv > SCHEMA_VERSION))
    future = [r for r in qualified_runtimes()
              if _newer(r) and isinstance(r, dict)
              and (r.get("sqlite_version"), r.get("source_id"))
              == (rec["sqlite_version"], rec["source_id"])]
    if future:
        print(f"refusing to overwrite evidence from a NEWER revision "
              f"(algorithm {future[0].get('manifest_algorithm')}, schema "
              f"{future[0].get('schema_version')}); this checkout is older than "
              f"the artifact", file=sys.stderr)
        return 1

    def _replaced(r):
        if not isinstance(r, dict):
            return True                        # malformed junk: rewrite it away
        if build_identity(r) == build_identity(rec):
            return True
        # The older-algorithm carve-out: probe definitions may have changed, so
        # the old record's features are not comparable. STRICTLY older only —
        # future revisions were refused above.
        alg = r.get("manifest_algorithm")
        return ((r.get("sqlite_version"), r.get("source_id"))
                == (rec["sqlite_version"], rec["source_id"])
                and type(alg) is int and alg < MANIFEST_ALGORITHM)
    others = [r for r in qualified_runtimes() if not _replaced(r)]
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
    except (Exception, SystemExit) as exc:      # validation OR filesystem
        # `SystemExit` is not an `Exception`, so v12's handler never caught
        # the validation failure it was written for (round 10).
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
        _discard(RUNTIMES.with_suffix(RUNTIMES.suffix + ".tmp"),
                 VERSIONS.with_suffix(VERSIONS.suffix + ".tmp"))
        print(f"staging failed, nothing published: {exc}", file=sys.stderr)
        return 1
    try:
        t_rt.replace(RUNTIMES)
        t_vs.replace(VERSIONS)
    except OSError as exc:
        _discard(t_rt, t_vs)
        if saved is None:
            RUNTIMES.unlink(missing_ok=True)
        else:
            RUNTIMES.write_text(saved)
        print(f"publish failed and was rolled back: {exc}", file=sys.stderr)
        return 1
    me_key = _identity_key(build_runtime_record())
    valid = active_records(prospective["runtimes"])
    attested = sum(1 for r in valid if _identity_key(r) == me_key)
    unattested = len(valid) - attested
    stale = len(prospective["runtimes"]) - len(valid)
    # Round 9: superseded records were counted as "qualified". They are not.
    # Round 10: an internally valid but unattested foreign record was counted
    # as "active" though it contributes nothing. Three categories, named.
    print(f"recorded {rec['sqlite_version']} ({rec['source_id'][:20]}…) — "
          f"{attested} attested and contributing, {unattested} recorded but "
          f"unattested, {stale} superseded or invalid")
    if unattested or stale:
        print(f"note: {unattested + stale} record(s) contribute no accepted "
              f"manifest")
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
        # *(Historical: round 7's union across qualified runtimes. `0007` now
        # supports exactly one active build identity; this loop survives so the
        # attestation refusal below is exercised, and `0013`/S-Q7 own any real
        # widening.)* v8 regenerated the current version solely from
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
            # claimed runtime produced them. The only record that may contribute
            # is one this process can REPRODUCE -- running the constructor here
            # and getting the same objects.
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
    if not VERSIONS.exists():
        bad.append(f"{VERSIONS.name} is missing — it is load-bearing evidence and "
                   f"its absence must fail, not pass silently (round 11)")
    elif json.loads(VERSIONS.read_text()) != generated:
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
    # The release check is where stale-record diagnostics belong (round 13,
    # finding 3): superseded or duplicate leftovers do not disqualify the
    # runtime at open time, but the repository must be cleaned before release.
    seen_stale = set()
    for rt in qualified_runtimes():
        if not isinstance(rt, dict):
            bad.append(f"runtime artifact contains a {type(rt).__name__}")
            continue
        if rt.get("manifest_algorithm") != MANIFEST_ALGORITHM:
            key = (rt.get("sqlite_version"), rt.get("source_id"),
                   rt.get("manifest_algorithm"))
            dup = " (duplicate)" if key in seen_stale else ""
            seen_stale.add(key)
            bad.append(f"runtime {rt.get('sqlite_version')!r} was recorded under "
                       f"manifest algorithm {rt.get('manifest_algorithm')}, build "
                       f"uses {MANIFEST_ALGORITHM} — re-qualify or remove it{dup}")
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
