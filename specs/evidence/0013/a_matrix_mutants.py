#!/usr/bin/env python3
# Mutation-Matrix: tests/test_0013_a_matrix_mutants.py::test_the_table_check_refuses_each_tampered_table
"""0013 §5f.3's finite acceptance matrix (A1–A16, P1–P3): every mutant the table names, demonstrated red.

§5f.3: "Each row is demonstrated red against the named mutant." The mutants are the spec's own PHRASES: the 4th column
("mutant that must fail") of each A/P row of that table, version markers stripped, split BY MUTANT at parenthesis
depth 0 on "; ", ", or " and " or " (derived from the text at run time, so a mutant the spec gains or loses fails by
NAME). Every phrase has exactly one carrier, and every carrier is a row of THIS table:
  MUTANT   a code edit run by the shared protocol (specs/evidence/mutation_protocol.py), killed by assertion in its
           named cells, which INCLUDE the cells of the phrase's own A/P case (CASE_CELLS), never only a sibling's;
  CONTROL  A2's "— (control)": no mutant; its cell must be in this table as an honest probe that passes on the clean
           tree (first and last) and beside every model mutant;
  ABSENT   no mutant is writable on today's code, with the reason and a cell that fails the day one becomes writable
           (none is used today).
A1–A15 are carrier (i) rows (the model, specs/migrations_0013.py), except A11 and A12's "as a pass", whose case is
production's attestation artifact (src/veracium/store/schema_version.py); A16 is a row for carriers (i) and (ii) both,
so its one phrase has TWO rows: the model's validator and production's evidence check (specs/schema_evidence.py's
acceptance_digest_problems). P1–P3 are carrier (ii) rows (production).

    $PY specs/evidence/0013/a_matrix_mutants.py --check     # fast: definitions, anchors, digests, phrases, every row good
    $PY specs/evidence/0013/a_matrix_mutants.py --phrases   # every phrase with its carrier
    TMPDIR=/dev/shm $PY specs/evidence/0013/a_matrix_mutants.py --write
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import mutation_protocol as _protocol  # noqa: E402

_strict_pairs = _protocol._strict_pairs

TABLE = HERE / "a_matrix" / "mutation-table.json"     # the name tests/test_closure_mutants.py finds
SELF = "specs/evidence/0013/a_matrix_mutants.py"
MODEL = "specs/migrations_0013.py"
SV = "src/veracium/store/schema_version.py"
REL = "src/veracium/store/release_migration.py"
MIG = "src/veracium/store/migration.py"
SE = "specs/schema_evidence.py"
EVIDENCE = "specs/generated/migration_0013_evidence.json"
MT = "tests/test_migrations_0013.py"
RS = "tests/test_0007_runtime_status.py"
SPEC = "specs/0013-store-migrations.md"
SUBJECT = "A1-A16-P1-P3"
DIGESTED = (MODEL, SV, REL, MIG, SE, EVIDENCE, MT, RS, SPEC, "specs/evidence/mutation_protocol.py", _protocol.KINDS,
            SELF)

M = lambda name: f"{MT}::{name}"                                                    # noqa: E731
R = lambda name: f"{RS}::{name}"                                                    # noqa: E731
A2 = M("test_a2_the_attested_build_migrates_and_its_row_says_attested")
P1 = lambda s: R(f"test_p1_a_verified_build_migrates_a_base_store_as_the_attested_build_does[{s}]")   # noqa: E731
P2 = R("test_p2_a_refused_build_refuses_migrate_store_and_the_release_before_touching_the_store")
P3 = lambda s: R(f"test_p3_a_stamp_below_head_is_refused_by_revalidation_and_rolls_back[{s}]")        # noqa: E731

CASE_CELLS = {
    # the cells of each A/P CASE: every mutant carrying a phrase of that row must name all of them
    "A1": [M("test_a1_a_verified_build_migrates_and_its_row_says_verified")],
    "A2": [A2],
    "A3": [M("test_the_migration_runtime_gate_is_independent_of_0007s")],          # its docstring: "in A3's shape"
    "A4": [M("test_an_authorizer_allowing_temp_triggers_fails_qualification"),
           M("test_an_authorizer_allowing_temp_vtables_fails_qualification")],
    "A5": [M("test_a5_a_refused_build_is_refused_after_consumption_and_the_store_is_unchanged")],
    "A6": [M("test_an_absent_path_record_refuses")],
    "A7": [M("test_a_duplicate_path_record_refuses")],
    "A8": [M("test_a8_two_current_path_records_for_one_key_with_different_outputs_refuse")],
    "A9": [M("test_a_missing_algorithm_field_is_malformed_not_superseded")],
    "A10": [M("test_a10_a_generated_on_that_resolves_to_no_attested_record_poisons_the_paths")],
    "A11": [M("test_a11_two_attested_keys_are_valid_and_each_resolves_separately")],
    "A12": [M("test_a12_an_attestation_record_with_a_false_probe_is_malformed_and_the_probes_still_run_live")],
    "A13": [M("test_a_stale_algorithm_record_is_superseded_not_consumed")],
    "A14": [M("test_a_side_effect_free_alteration_is_still_not_evidenced")],
    "A15": [M("test_a15_an_extra_current_path_record_outside_the_expected_set_is_a_cardinality_refusal")],
    "A16": [M("test_a16_two_accepted_manifestations_sharing_an_acceptance_digest_are_refused"),
            R("test_a16_production_evidence_refuses_two_accepted_manifestations_sharing_an_acceptance_digest")],
    "P1": [P1("verified")],
    "P2": [P2],
    "P3": [P3("verified")],
}
"""A16's two cells are split between its two rows (one carrier each); `carrier_problems` checks their UNION."""

_GATES = ('''                status = sv.runtime_status()
                if status.status == "refused":
''')
_PROBES = ('''                if migrating:
                    failing = probes_problems(authorizer_probes())
''')
_TRIGGER = ('''    out["denies_temp_trigger"] = _denied_by_authorizer(
        ("BEGIN IMMEDIATE", "CREATE TABLE mainprobe (a)"),
        "CREATE TEMP TRIGGER trprobe AFTER INSERT ON mainprobe "
        "BEGIN DELETE FROM mainprobe; END")
''')
_VTABLE = ('''    out["denies_temp_virtual_table"] = _denied_by_authorizer(
        ("BEGIN IMMEDIATE",), "CREATE VIRTUAL TABLE temp.vtprobe USING dbstat")
''')
_MALFORMED = ('''        if cls == "malformed":
            problems.append("path record with a missing or mistyped algorithm "
                            "field — malformed, not superseded")
            continue
        problems += path_record_problems(rec, art)
''')
_CONTRADICTORY = ('''            if seen[key] != rec.get("output_full_manifest_hash"):
                problems.append("two path records share a selection key but "
                                "declare different outputs — the artifact is "
                                "self-contradictory and neither can be trusted")
''')
_DUPLICATE = ('''            else:
                problems.append("duplicate path record for one selection key")
''')
_OLDER = ("                    older(conn, spath, found, objs, found, runtime=status)\n"
          "                    _validated_current(conn, spath, found, require_stamp=True, target=target)\n")
_HONEST_P = [P1("attested"), P3("attested")]          # the attested build's own cells: the clean path a P mutant keeps

# (id, kind, file, [(anchor, replacement)], named cells (EVERY one must fail), honest probes, reason or None, what)
MUTANTS = [
    # ---- carrier (i), the model ----------------------------------------------------------------------------------
    ("a1-require-a-record", "model", MODEL,
     [(_PROBES, '                if migrating and status.status != "attested":\n'
                '                    return Outcome("unsupported-sqlite", "no migration-runtime record for this build")\n'
       + _PROBES)],
     CASE_CELLS["A1"], [A2], None,
     "the model at 58dd7f6: migration requires a record for the running build (attested), so a verified one refuses"),
    ("a3-runtime-status-alone", "model", MODEL,
     [(_PROBES, _PROBES.replace("probes_problems(authorizer_probes())", "[]"))],
     CASE_CELLS["A3"], [A2], None,
     "migration gated on runtime_status() alone: the sixteen live probes are never consulted"),
    ("a4-collapse-the-temp-probes", "model", MODEL,
     [(_TRIGGER, '    out["denies_temp_trigger"] = out["denies_temp_table"]\n'),
      (_VTABLE, '    out["denies_temp_virtual_table"] = out["denies_temp_table"]\n')],
     CASE_CELLS["A4"], [A2, M("test_the_authorizer_probes_all_hold_on_this_runner")], None,
     "the TEMP trigger and TEMP virtual-table probes report the TEMP table probe's answer (one probe for three classes)"),
    ("a5-confinement-first", "model", MODEL,
     [(_GATES, _GATES.replace('if status.status == "refused":',
                              'if status.status == "refused" and not (migrating and not '
                              'probes_problems(authorizer_probes())):'))],
     CASE_CELLS["A5"], [A2], None,
     "confinement runs first and, when its probes pass, a refused build migrates"),
    ("a6-rederive-the-record-live", "model", MODEL,
     [("        snapshot = _artifact_snapshot()\n",
       "        snapshot = _artifact_snapshot()\n"
       "        if isinstance(snapshot[0], dict) and expected_path_problems(snapshot[0]):\n"
       "            snapshot = (dict(snapshot[0], paths=_generate_artifact()[0][\"paths\"]), snapshot[1])\n")],
     CASE_CELLS["A6"], [A2], None,
     "0013 round 3's hole: when no recorded path record covers the source x declaration, derive it from live code"),
    ("a7-deduplicate-silently", "model", MODEL,
     [(_DUPLICATE, "            else:\n                pass                       # deduplicated silently\n")],
     CASE_CELLS["A7"], [A2], None,
     "two identical current records for one key: the artifact validator says nothing"),
    ("a8-take-the-first", "model", MODEL,
     [(_CONTRADICTORY, '            if seen[key] != rec.get("output_full_manifest_hash"):\n'
                       "                continue                   # the first record is taken\n")],
     CASE_CELLS["A8"], [A2], None,
     "two current records for one key with different outputs: the first is kept, the contradiction unreported"),
    ("a9-filter-the-malformed-record", "model", MODEL,
     [(_MALFORMED, '        if cls == "malformed":\n            continue                       # filtered\n'
                   "        if path_record_problems(rec, art):\n"
                   "            continue                       # filtered: the valid one is selected\n")],
     CASE_CELLS["A9"] + [M("test_a_coerced_path_algorithm_poisons_the_paths")], [A2], None,
     "0013 round 4's hole: a malformed current-algorithm record (a missing algorithm field, or a record failing its "
     "own rules) is filtered out, poisoning nothing, and the valid record is selected"),
    ("a10-ignore-generated-on", "model", MODEL,
     [('        if not sv.attested_key(sv.attestation_key(rec["generated_on"]), revision=PRODUCTION_REVISION):\n',
       "        if False:\n")],
     CASE_CELLS["A10"], [A2], None,
     "a path record's generated_on is never resolved: provenance poisons nothing"),
    ("a12-recorded-false-is-authority", "model", MODEL,
     [(_PROBES, '                if migrating and any(isinstance(r, dict) and False in dict(r.get("confinement") or {})'
                '.values()\n                                     for r in sv.attestations()):\n'
                '                    return Outcome("unsupported-sqlite", "an attestation record carries a False probe")\n'
       + _PROBES)],
     CASE_CELLS["A12"], [A2], None,
     "a recorded False probe is AUTHORITY: the migration refuses on the record, without running the probes live"),
    ("a13-consume-the-stale-record", "model", MODEL,
     [('    return "current" if alg == MIGRATION_EVIDENCE_ALGORITHM else "superseded"\n',
       '    return "current"\n')],
     CASE_CELLS["A13"], [A2], None,
     "a stale-algorithm record is current: validated, counted and selectable"),
    ("a14-drop-the-declaration-digest", "model", MODEL,
     [("    return (from_version, source_acceptance_digest, source_full_manifest_hash, to_version,\n"
       "            migration_declaration_digest)\n",
       "    return (from_version, source_acceptance_digest, source_full_manifest_hash, to_version)\n")],
     CASE_CELLS["A14"] + [M("test_a_data_destructive_alteration_cannot_authorize_itself")], [A2], None,
     "the path key without the migration declaration digest: an altered declaration selects the recorded evidence"),
    ("a15-count-only-expected-keys", "model", MODEL,
     [("    for key in sorted(set(have) - expected, key=repr):\n", "    for key in []:\n")],
     CASE_CELLS["A15"], [A2], None,
     "cardinality counts only expected keys: a current record outside the expected set is not refused"),
    ("a16-model-admit-it", "model", MODEL,
     [('                    if seen_dig.setdefault(a["digest"], fmh) != fmh:\n', "                    if False:\n")],
     [CASE_CELLS["A16"][0]], [A2], None,
     "the model's evidence validator admits two accepted manifestations sharing one acceptance digest"),
    # ---- A11, A12 and A16 in production's attestation and evidence checks ------------------------------------------
    ("a11-single-active-runtime", "product", SV,
     [("        else:\n            seen[key] = (i, evidence)\n    return problems\n",
       "        else:\n            seen[key] = (i, evidence)\n    if len(seen) > 1:\n"
       "        problems.append(\"more than one active runtime\")\n    return problems\n")],
     CASE_CELLS["A11"] + [R("test_any_number_of_keys_is_valid_and_another_keys_record_attests_nothing")], [A2], None,
     "S66's single-active-runtime count kept: a second attested key poisons the attestation artifact"),
    ("a12-recorded-false-is-a-pass", "product", SV,
     [("or any(v is not True for v in c.values()):", "or any(type(v) is not bool for v in c.values()):")],
     CASE_CELLS["A12"], [A2], None,
     "an attestation record carrying a probe result False is well-formed: the recorded False passes"),
    ("a16-production-admit-it", "product", SE,
     [('            if seen.setdefault(a["digest"], body) != body:\n', "            if False:\n")],
     [CASE_CELLS["A16"][1]], [A2], None,
     "production's evidence check admits two accepted manifestations sharing one acceptance digest"),
    # ---- carrier (ii), production: P1–P3 ---------------------------------------------------------------------------
    ("p1-runtime-supported-as-the-gate", "product", SV,
     [("        if runtime_refused(status):\n            raise _SITE_OPEN_RUNTIME_UNSUPPORTED",
       "        if status.status != \"attested\":\n            raise _SITE_OPEN_RUNTIME_UNSUPPORTED")],
     CASE_CELLS["P1"], _HONEST_P, None,
     "the withdrawn runtime_supported() kept as the open gate: only an attested build opens, so a verified one "
     "cannot migrate"),
    ("p1-skip-validated-current-verified", "product", SV,
     [(_OLDER, _OLDER.replace("                    _validated_current(",
                              "                    if status.status != \"verified\":\n"
                              "                        _validated_current("))],
     CASE_CELLS["P1"], _HONEST_P, None, "a verified build's migration skips _validated_current"),
    ("p2-gate-only-open-versioned", "product", REL,
     [("    if sv.runtime_refused(status):\n        return _intercept(\"unsupported-sqlite\"",
       "    if False:\n        return _intercept(\"unsupported-sqlite\"")],
     CASE_CELLS["P2"] + [R("test_a_refused_build_is_refused_before_any_version_decision"
                           "[store/release_migration.py:_classify_or_intercept]")], _HONEST_P, None,
     "only open_versioned gates: the release preflight never reads the measured status, so a refused build reaches it"),
    ("p3-commit-before-revalidating-verified", "product", SV,
     [(_OLDER, _OLDER.replace("                    _validated_current(",
                              "                    if status.status == \"verified\":\n"
                              "                        conn.execute(\"COMMIT\")\n"
                              "                        conn.execute(\"BEGIN IMMEDIATE\")\n"
                              "                    _validated_current("))],
     CASE_CELLS["P3"], _HONEST_P, None, "a verified build's migration commits before _validated_current runs"),
    ("p3-require-stamp-false-verified", "product", SV,
     [(_OLDER, _OLDER.replace("require_stamp=True,", "require_stamp=status.status != \"verified\","))],
     CASE_CELLS["P3"], _HONEST_P, None, "a verified build's revalidation passes require_stamp=False"),
]

# (id, file, [(anchor, replacement)], named cells, what, the outcome the classifier must give)
CONTROLS = [
    ("CTRL-unrelated-TypeError", MODEL,
     [("def path_provenance_problems(art) -> list:\n",
       "def path_provenance_problems(art) -> list:\n"
       '    raise TypeError("an unrelated execution failure (classifier negative control)")\n')],
     [CASE_CELLS["A10"][0]],
     "an UNRELATED TypeError in the provenance validator: a cell fails for no reason the row names", "UNCLASSIFIED"),
]

CARRIERS = {
    # (row, phrase index) -> ("mutant", id, ...) | ("control", cell) | ("absent", reason, cell)
    ("A1", 0): ("mutant", "a1-require-a-record"),
    ("A2", 0): ("control", A2),
    ("A3", 0): ("mutant", "a3-runtime-status-alone"),
    ("A4", 0): ("mutant", "a4-collapse-the-temp-probes"),
    ("A5", 0): ("mutant", "a5-confinement-first"),
    ("A6", 0): ("mutant", "a6-rederive-the-record-live"),
    ("A7", 0): ("mutant", "a7-deduplicate-silently"),
    ("A8", 0): ("mutant", "a8-take-the-first"),
    ("A9", 0): ("mutant", "a9-filter-the-malformed-record"),
    ("A10", 0): ("mutant", "a10-ignore-generated-on"),
    ("A11", 0): ("mutant", "a11-single-active-runtime"),
    ("A12", 0): ("mutant", "a12-recorded-false-is-authority"),
    ("A12", 1): ("mutant", "a12-recorded-false-is-a-pass"),
    ("A13", 0): ("mutant", "a13-consume-the-stale-record"),
    ("A14", 0): ("mutant", "a14-drop-the-declaration-digest"),
    ("A15", 0): ("mutant", "a15-count-only-expected-keys"),
    ("A16", 0): ("mutant", "a16-model-admit-it", "a16-production-admit-it"),
    ("P1", 0): ("mutant", "p1-runtime-supported-as-the-gate"),
    ("P1", 1): ("mutant", "p1-skip-validated-current-verified"),
    ("P2", 0): ("mutant", "p2-gate-only-open-versioned"),
    ("P3", 0): ("mutant", "p3-commit-before-revalidating-verified"),
    ("P3", 1): ("mutant", "p3-require-stamp-false-verified"),
}
"""Every phrase's ONE carrier (A16's one phrase is a row for two carriers, so it names two mutants)."""


# ---- the phrases, from the spec text ----------------------------------------------------------------------------------
_HEADER = "| # | case | expected | mutant that must fail |"
_MARKER = re.compile(r"\*\*\((?:v[0-9.]+)\)\*\*\s*")
_ROW = re.compile(r"\| ((?:A|P)\d+) \|")
SEPARATORS = ("; ", ", or ", " or ")


def _split_depth0(text, seps=SEPARATORS):
    """`text` cut at every separator that sits at parenthesis depth 0 (longest separator first at each position)."""
    out, depth, cur, i = [], 0, [], 0
    while i < len(text):
        ch = text[i]
        if depth == 0:
            sep = next((s for s in sorted(seps, key=len, reverse=True) if text.startswith(s, i)), None)
            if sep is not None:
                out.append("".join(cur))
                cur, i = [], i + len(sep)
                continue
        depth += ch == "("
        depth -= ch == ")"
        cur.append(ch)
        i += 1
    out.append("".join(cur))
    return out


def phrases(root: pathlib.Path = ROOT) -> dict:
    """{(row, index): phrase}: §5f.3's "mutant that must fail" column, the table that follows its header line."""
    lines = (root / SPEC).read_text(encoding="utf-8").splitlines()
    starts = [i for i, ln in enumerate(lines) if ln.strip() == _HEADER]
    if len(starts) != 1:
        raise ValueError(f"{SPEC}: the §5f.3 table header occurs {len(starts)} times, not once")
    out = {}
    for line in lines[starts[0] + 2:]:
        if not line.startswith("|"):
            break
        m = _ROW.match(line)
        if not m:
            raise ValueError(f"{SPEC}: a §5f.3 table row is not an A/P row: {line[:60]!r}")
        cells = [c.strip() for c in line.split("|")]
        if len(cells) != 6:
            raise ValueError(f"{SPEC}: row {m.group(1)} has {len(cells) - 2} columns, not 4")
        if (m.group(1), 0) in out:
            raise ValueError(f"{SPEC}: row {m.group(1)} occurs twice")
        for i, p in enumerate(q.strip() for q in _split_depth0(_MARKER.sub("", cells[4]))):
            out[(m.group(1), i)] = p
    return out


def carrier_problems(root: pathlib.Path = ROOT) -> list:
    """The complement check, both directions: the spec's phrase set EQUALS the carriers' key set; each carrier
    resolves (a mutant of THIS table, the control cell among the honest probes, or an ABSENT cell that exists); each
    mutant carrying a row's phrase names that row's own case cells (the union over its mutants, for A16); and every
    mutant of this table carries a phrase."""
    ph, out = phrases(root), []
    ids = {m[0]: m for m in MUTANTS}
    out += [f"{k[0]} phrase {k[1]} has no carrier: {ph[k]!r}" for k in sorted(set(ph) - set(CARRIERS))]
    out += [f"{k[0]} carrier {k[1]} has no phrase in the spec" for k in sorted(set(CARRIERS) - set(ph))]
    out += [f"{r} has no case cells" for r in sorted({k[0] for k in ph} - set(CASE_CELLS))]
    used = set()
    for k, c in sorted(CARRIERS.items()):
        if c[0] == "mutant":
            named = set()
            for mid in c[1:]:
                used.add(mid)
                if mid not in ids:
                    out.append(f"{k[0]} phrase {k[1]}: no mutant {mid!r} in this table")
                else:
                    named |= set(ids[mid][4])
            missing = [n for n in CASE_CELLS.get(k[0], []) if n not in named]
            if missing:
                out.append(f"{k[0]} phrase {k[1]}: its mutants do not name the row's own case cells {missing}")
        elif c[0] == "control":
            if c[1] not in SUBJECT_P.honest_nodes():
                out.append(f"{k[0]} phrase {k[1]}: the control cell {c[1]} is not an honest probe of this table")
            if c[1] not in CASE_CELLS.get(k[0], []):
                out.append(f"{k[0]} phrase {k[1]}: the control cell {c[1]} is not the row's own case cell")
        elif c[0] == "absent":
            f, name = c[2].split("::")[0], c[2].split("::")[-1].split("[")[0]
            if f"{f}::{name}" not in SUBJECT_P.defined_tests(root):
                out.append(f"{k[0]} phrase {k[1]}: the ABSENT cell {c[2]} does not exist")
        else:
            out.append(f"{k[0]} phrase {k[1]}: carrier kind {c[0]!r} is not mutant/control/absent")
    out += [f"mutant {m} carries no phrase" for m in sorted(set(ids) - used)]
    return out


SUBJECT_P = _protocol.Subject(
    spec="0013", finding=SUBJECT, table=TABLE, digested=DIGESTED, mutants=MUTANTS, controls=CONTROLS,
    import_modules=("veracium.store.schema_version", "veracium.store.migration", "veracium.store.release_migration"),
    import_specs=(MODEL, SE), cells_files=(MT, RS), kinds=("model", "product"))


def problems(path: pathlib.Path = TABLE, root: pathlib.Path = ROOT) -> list:
    return carrier_problems(root) + SUBJECT_P.problems(path, root)


definition_sha = _protocol.definition_sha
canonical = _protocol.canonical
render = _protocol.render
_digests = SUBJECT_P.digests


def main() -> int:
    if "--phrases" in sys.argv:
        ph = phrases()
        for k, p in sorted(ph.items(), key=lambda kv: (kv[0][0][0], int(kv[0][0][1:]), kv[0][1])):
            c = CARRIERS.get(k, ("MISSING",))
            print(f"{k[0]:4s} {k[1]}  {c[0]:8s} {' + '.join(c[1:]) if c[0] == 'mutant' else ''}  {p}")
        bad = carrier_problems()
        for b in bad:
            print(f"CARRIER: {b}")
        return 1 if bad else 0
    bad = carrier_problems()
    if bad and "--write" in sys.argv:
        for b in bad:
            print(f"CARRIER: {b}")
        return 1
    if "--check" in sys.argv or len(sys.argv) == 1:
        probs = problems()
        for b in probs:
            print(f"STALE: {b}")
        return 1 if probs else 0
    return SUBJECT_P.main(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
