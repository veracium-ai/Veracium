#!/usr/bin/env python3
"""0011 — the mutant campaign as an executable, RUNNER-OBSERVED ledger.

PROCESS-R11-1 ended the reporter protocol. Through rounds 7-10 a kill was
a CLAIM: a standing test, having exercised its scenario, reported the id it
believed it had killed, and successive rounds hardened who was allowed to
say so (per-node isolation, runner-owned node labels, reporters moved out
of the artifact). Round 11 showed the id half was still self-reported — a
registry with swapped ids plus reporters rewritten to look ids up FROM the
registry passed --write, --check and the focused suite — and that the
round-10 regression never executed anything (its copied module derived
ROOT from /tmp, pytest exited 4, and the empty kill list produced the
expected mismatch).

So no claim survives anywhere in the protocol. Each entry now carries the
MUTATION ITSELF as text hunks, and a kill is a fact the runner observes:

  * CLEAN     — every distinct node passes (exit 0, tests collected) on
                the unmutated tree;
  * KILL      — with the entry's hunks applied to the real artifacts (each
                old text required EXACTLY ONCE, restored byte-identically
                after), the entry's node FAILS with real test failures
                (exit 1, failed >= 1) — a collection error, usage error or
                empty run is a campaign ERROR, never a kill;
  * MINIMAL   — for a multi-hunk entry, each leave-one-out subset leaves
                the node PASSING, so every hunk is individually
                load-bearing. The hunk count is therefore a MEASURED
                witness of defense depth (M3's narrowed-SUBJECTS attack
                takes FOUR simultaneous neuters to get through).

A swapped registry now applies one artifact's mutation and runs the other
entry's node, which passes — a SURVIVAL, refused loudly. There is no
reporter to conspire with and no id to misreport: the record is built from
what the runner did and saw, and --check recompares it byte-for-byte.

    $PY specs/evidence/0011/mutant_registry.py            # CHECK (default):
        re-runs the campaign, rebuilds the record, and REQUIRES it to equal
        the shipped mutant_results.json byte-for-byte. The LIVE TREE is
        never mutated — the campaign runs in a private snapshot.
    $PY specs/evidence/0011/mutant_registry.py --write    # seal-time only:
        writes the record.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent
RECORD = HERE / "mutant_results.json"
T1 = "tests/test_0011_policy_matrix.py"
T2 = "tests/test_0011_mutant_registry.py"

PM = "specs/evidence/0011/policy_matrix.py"
CF = "specs/evidence/0011/check_round1_fold.py"
SC = "specs/evidence/0011/subject_census.py"
CK = "specs/evidence/0011/check_contention_rule.py"

# Research F-B residual (round-11 pre-seal pass): the mutable-artifact set
# is defined by INCLUSION. A deny-list ("not tests/, not this registry")
# is the polarity this whole arc exists to refuse — it silently admitted a
# future conftest.py (judge-side infrastructure) and any off-path src
# function (defense-depth inflation: a genuine kill of a function that has
# nothing to do with the 0011 checker). The campaign is ENTITLED to mutate
# exactly these artifacts, and nothing else, ever, until a reviewed edit
# widens this set.
MUTABLE_ARTIFACTS = frozenset({PM, CF, SC, CK})


def artifact_problems(art) -> list:
    """THE shared path guard, for BOTH carriers (PROCESS-R14-1: entry
    validation computed identity before enforcing the allowlist, and
    record validation never enforced paths at all — a record hunk naming
    /etc/passwd validated clean, and /bin/sh crashed the checker with an
    uncaught decode error because identity READ it). Membership comes
    first and is a pure string check, so an out-of-set path is refused
    with NO filesystem access; the R8-1(3) containment and regular-file
    checks are depth behind it."""
    if art not in MUTABLE_ARTIFACTS:
        return [f"artifact {art!r} is OUTSIDE the closed mutable set "
                f"{sorted(MUTABLE_ARTIFACTS)} — mutating the judge or "
                f"off-path code manufactures or inflates the verdict; "
                f"widening this set is a reviewed edit"]
    ap = pathlib.PurePosixPath(art)
    if ap.is_absolute() or ".." in ap.parts:
        return [f"artifact {art!r} is not a plain relative path inside "
                f"the package"]
    full = ROOT / art
    try:
        full.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return [f"artifact {art!r} escapes the package root"]
    if not full.is_file():
        return [f"artifact {art!r} is not a regular file in the package"]
    return []


def mutation_identity(hunks) -> tuple:
    """PROCESS-R12-1/R13-1: the canonical identity of a MUTATION is the
    RESULTING ARTIFACT TRANSFORMATION — per artifact, the sha256 of the
    bytes produced by applying the entry's complete bundle to the
    pristine file — never any description of how to produce it.

    This is the terminal rung of a four-face ladder, each face a
    representation the previous fix still depended on: (1) the id string
    (a fresh id relabeled R5A); (2) the full old/new text (the context
    window slides); (3) the minimal diff plus position (round 13: the
    hunk PARTITIONING slides — C2's two edits merged into one wider hunk
    yield byte-identical mutated artifacts under a distinct identity,
    and dropping C1 beside the merged duplicate held the totals constant
    while one mutant vanished and another counted twice). Hashing the
    OUTCOME has no representation left to vary: any decomposition that
    produces the same mutated bytes is the same mutation.

    The named boundary moves with it, honestly: whitespace variants of
    the INSERTED text produce distinct resulting bytes, so they sit with
    the semantically-equivalent-program class — undecidable in general,
    visible as data (hunks ship in the record). The whitespace-folded
    digest screen in validate_entries refuses the cheapest of those too.
    Entries whose bundle cannot apply cleanly identify by their raw
    hunks and are refused by the application checks elsewhere."""
    return _identity(hunks, fold_ws=False)


def _apply_hunks_to_text(text, pairs):
    """THE apply path — the identity and the campaign share this one
    function BY CONSTRUCTION (research, round-13 pre-seal): "the bytes
    the bundle produces" is only well-defined if identity and execution
    apply the same way in the same order. Today's bundles are pairwise
    disjoint, so order happens not to matter; the day an entry carries
    ORDER-DEPENDENT hunks (one hunk's new text creating or destroying
    another's old text), a digest computed by any OTHER path could
    disagree with what actually ran — the same mutation under two
    identities, face four one level down. Sharing the function makes
    same-executed-bytes imply same-digest definitionally, so
    order-dependence is well-defined rather than forbidden.

    Returns (text_or_None, problems); refuses at the first hunk whose
    old text is not exactly-once in the CURRENT text."""
    problems = []
    for o, n in pairs:
        if text is None or text.count(o) != 1:
            problems.append(f"hunk old text occurs "
                            f"{0 if text is None else text.count(o)} "
                            f"times at application — refused")
            return None, problems
        text = text.replace(o, n, 1)
    return text, problems


def _identity(hunks, fold_ws) -> tuple:
    per_art = {}
    for a, o, n in hunks:
        per_art.setdefault(a, []).append((o, n))
    out = []
    for art in sorted(per_art):
        # defensive against unvalidated paths (PROCESS-R14-1): identity
        # itself refuses to read outside the tree or crash on a binary —
        # validation refuses such entries loudly; this just guarantees no
        # read happens on the way there
        pristine = None
        ap = pathlib.PurePosixPath(art)
        full = ROOT / art
        if not ap.is_absolute() and ".." not in ap.parts:
            try:
                full.resolve().relative_to(ROOT.resolve())
                pristine = full.read_text()
            except (ValueError, OSError, UnicodeDecodeError):
                pristine = None
        applied, _probs = _apply_hunks_to_text(pristine, per_art[art])
        if applied is None:
            out.append((art, None, tuple(sorted(per_art[art]))))
        else:
            text = " ".join(applied.split()) if fold_ws else applied
            out.append((art,
                        hashlib.sha256(text.encode()).hexdigest()))
    return tuple(out)


ENTRIES = (
    ("R4A", "reviewer",
     "the oracle judges its own recomputation instead of the injected "
     "stream — the round-4 certifying-its-inputs defect",
     f"{T1}::test_a_variance_planted_in_the_emission_is_caught",
     "problems",
     ((PM, "seen = list(cells() if stream is None else stream)",
       "seen = list(cells())"),)),
    ("R4B", "reviewer",
     "dependency closure regresses to last-definition-wins — a dangerous "
     "helper shadowed by a benign redefinition disappears",
     f"{T1}::test_the_fold_checker_refuses_a_shadowed_helper",
     "_dependency_closure",
     ((CF, 'defs[name] = (defs[name] + "\\n" + body) if name in defs '
           'else body',
       "defs[name] = body"),)),
    ("R5A", "reviewer",
     "duplicate-key detection neutered — a cardinality-preserving "
     "replacement is invisible on the duplicate side",
     f"{T1}::test_a_duplicate_hiding_a_missing_cell_is_caught",
     "problems",
     ((PM, "emitted_keys.count(k) > 1", "emitted_keys.count(k) > 2"),)),
    ("R5B", "reviewer",
     "the row-bound rider contradiction blunted — §3c may re-promise the "
     "withdrawn measurement rider",
     f"{T2}::test_rider_promise_in_the_row_is_refused",
     "ROW_CONTRADICTIONS",
     ((CF, '("| USER (sole authority: self-assertion) |", '
           '"with the measurement rider",',
       '("| USER (sole authority: self-assertion) |", '
       '"with the measurement rider NEVER SAID",'),)),
    ("R6A", "reviewer",
     "the DERIVED enum-identity pin neutered — the derivation axis can "
     "self-narrow (its NAMED complaint dies; coverage complaints do not "
     "carry the axis name the standing test requires)",
     f"{T2}::test_narrowed_enum_dimension_is_refused",
     "problems",
     ((PM, "if tuple(DERIVED) != (None, *tuple(A)):",
       "if tuple(DERIVED) != tuple(DERIVED):"),)),
    ("R6B", "reviewer",
     "check_census_figures dropped from main()'s aggregation — a whole "
     "check family unreachable",
     f"{T2}::test_every_fold_check_is_reached",
     "main",
     ((CF, "+ check_decision_table(t) + check_census_figures(t))",
       "+ check_decision_table(t))"),)),
    ("M1", "dev",
     "the SOURCES literal pin neutered — the hand-picked source axis can "
     "narrow while emitter and expectation shrink together",
     f"{T1}::test_narrowed_dimensions_are_refused",
     "problems",
     ((PM, 'if len(SOURCES) != 3 or None not in SOURCES or not any(\n'
           '            s and "caller" in s for s in SOURCES if s):',
       "if False:"),)),
    ("M2", "dev",
     "the ORIGINS literal pin neutered — the origin axis can narrow",
     f"{T1}::test_narrowed_dimensions_are_refused",
     "problems",
     ((PM, "if len(ORIGINS) != 2 or None not in ORIGINS:",
       "if False:"),)),
    ("M3", "dev",
     "the OTHER subject dropped — takes FOUR simultaneous neuters (the "
     "subject-class pin, both named REFUSE cells, and the low-authority "
     "derived check's empty-set tolerance): measured defense depth 4",
     f"{T1}::test_narrowed_dimensions_are_refused",
     "problems",
     ((PM, 'if subj_classes != {"SELF", "OTHER"}:',
       "if subj_classes != subj_classes:"),
      (PM, 'if emitted(A.USER, None, "OTHER") != {"REFUSE"}:',
       'if emitted(A.USER, None, "OTHER") - {"REFUSE", "ALLOW"}:'),
      (PM, 'if emitted(A.USER, A.USER, "OTHER") != {"REFUSE"}:',
       'if emitted(A.USER, A.USER, "OTHER") - {"REFUSE", "ALLOW"}:'),
      (PM, 'if emitted(low, A.USER, "OTHER") != {"ALLOW"}:',
       'if emitted(low, A.USER, "OTHER") - {"ALLOW"}:'))),
    ("M4", "dev",
     "the NEVER-EMITTED (missing-key) defense neutered — the displaced "
     "half of a duplicate swap, and any truncation the named cells miss, "
     "pass the coverage layer",
     f"{T1}::test_a_duplicate_hiding_a_missing_cell_is_caught",
     "problems",
     ((PM, "missing = expected_keys - set(emitted_keys)",
       "missing = expected_keys - expected_keys"),)),
    ("M5", "dev",
     "import cells fabricated in problems() — the production adapter is "
     "never reached and the value checks are satisfied by fiction",
     f"{T1}::test_problems_actually_reaches_the_import_adapter",
     "problems",
     ((PM, "imp = import_flattened_cells()",
       'imp = [("default", A.THIRD_PARTY, "ALLOW"), '
       '("restore", A.USER, "REFUSE")]'),)),
    ("F1", "dev",
     "definition anchor loses its indent tolerance — an indented helper "
     "definition is invisible to the closure",
     f"{T2}::test_indented_helper_definition_is_followed",
     "_dependency_closure",
     ((CF, 'r"^\\s*(\\w+)\\s*(?:\\([^)]*\\))?\\s*:?=", f, re.M):',
       'r"^(\\w+)\\s*(?:\\([^)]*\\))?\\s*:?=", f, re.M):'),)),
    ("F2", "dev",
     "definition parens made mandatory — a parenless binding is never a "
     "definition, so a read hidden in one is never followed",
     f"{T2}::test_parenless_binding_is_followed",
     "_dependency_closure",
     ((CF, 'r"^\\s*(\\w+)\\s*(?:\\([^)]*\\))?\\s*:?=", f, re.M):',
       'r"^\\s*(\\w+)\\s*(?:\\([^)]*\\))\\s*:?=", f, re.M):'),)),
    ("F3", "dev",
     "fence grammar regresses to bare fences — an info-string fence "
     "(```text) hides its contents entirely",
     f"{T2}::test_info_string_fence_is_scanned",
     "_dependency_closure",
     ((CF, 'fences = re.findall(r"```[\\w-]*[ \\t]*\\n(.*?)```", spec, '
           're.S)',
       'fences = re.findall(r"```\\n(.*?)```", spec, re.S)'),)),
    ("F4", "dev",
     "multiset equality over the spec's table block neutered — an extra "
     "contradicting hand-written row sits beside the generated rows",
     f"{T2}::test_extra_table_row_is_refused",
     "check_decision_table",
     ((CF, "if sorted(spec_rows) != sorted(rows):",
       "if sorted(spec_rows) != sorted(spec_rows):"),)),
    ("C1", "dev",
     "the recorded-only census figure read from a CONSTANT instead of the "
     "aggregate — an inflated aggregate agrees with everything",
     f"{T2}::test_inflated_aggregate_figure_is_refused",
     "check_census_figures",
     ((CF, '"predicate passes": (agg["predicate_passes"],',
       '"predicate passes": (72253,'),)),
    ("C2", "dev",
     "both candidate-table bindings hardcoded — a gutted table keeps its "
     "published totals: measured defense depth 2",
     f"{T2}::test_gutted_candidate_table_is_refused",
     "check_census_figures",
     ((CF, '"candidate rows": (sum(table.values()),',
       '"candidate rows": (337,'),
      (CF, '"distinct strings": (len(table), r"over \\*\\*([\\d,]+) '
           'distinct"),',
       '"distinct strings": (94, r"over \\*\\*([\\d,]+) distinct"),'))),
    ("C3", "dev",
     "the aggregate-side name-mask refusal neutered — an unmasked "
     "name-shaped key validates",
     f"{T2}::test_unmasked_name_in_aggregate_is_refused",
     "validate_aggregate",
     ((SC, "if _NAME_AFTER.search(s):",
       "if False and _NAME_AFTER.search(s):"),)),
    ("C4", "dev",
     "the spec-side figure never parsed — stated is defined as actual, so "
     "§3b prose can drift freely from its artifact",
     f"{T2}::test_spec_figure_drift_is_refused",
     "check_census_figures",
     ((CF, 'stated = int(m.group(1).replace(",", ""))',
       "stated = actual"),)),
    ("K1", "dev",
     "a deleted cell silently counted as ran — the registry mismatch and "
     "the no-such-cell complaint both vanish",
     f"{T1}::test_contention_checker_cells_cannot_vanish",
     "run_cells",
     ((CK, 'if fn is None:\n                bad.append(f"registry names '
           '{name} and no such cell exists")\n                continue',
       "if fn is None:\n                ran.append(name)\n"
       "                continue"),)),
    ("K2", "dev",
     "the direct-pair cell's assertion made unfireable while the cell "
     "still runs — reachability without failability",
     f"{T1}::test_contention_checker_cells_cannot_vanish",
     "cell_direct_pair_not_contested",
     ((CK, "if direct:", "if direct is None:"),)),
)


FOUND_BY = ("reviewer", "dev")           # closed: EVIDENCE-R9-1 planted
                                          # "banana" and the totals grew a
                                          # partition the round never governed

_NODE_RE = re.compile(r"^tests/[\w./-]+\.py::\w+$")


def _no_dup_pairs(pairs):
    """EVIDENCE-R9-1(1): `json.loads` keeps the LAST of duplicate keys, so a
    prepended `"schema": false` vanished in parsing and canonicalisation
    then blessed the file. Duplicates refuse at PARSE."""
    seen = set()
    for k, _v in pairs:
        if k in seen:
            raise ValueError(f"duplicate JSON key {k!r}")
        seen.add(k)
    return dict(pairs)


def strict_parse(raw: str) -> dict:
    return json.loads(raw, object_pairs_hook=_no_dup_pairs)


def canonical_bytes(record: dict) -> str:
    """THE writer. Check mode compares the shipped file's RAW BYTES to this
    exact serialisation, so nothing survives a parse-normalise round trip."""
    return json.dumps(record, indent=1, sort_keys=True) + "\n"


def _is_int(x):
    return type(x) is int


def validate_record(rec) -> list:
    """Recursive, exactly typed, CLOSED — unknown and missing keys refuse at
    every level, bool never passes as int (bool is an int subclass), and
    found_by is the governed two-value partition."""
    if type(rec) is not dict:
        return ["record is not an object"]
    if sorted(rec) != ["entries", "schema", "totals", "verified"]:
        return [f"top-level keys {sorted(rec)} != the closed set"]
    bad = []
    if rec["schema"] != 4 or not _is_int(rec["schema"]):
        bad.append(f"schema {rec['schema']!r} is not 4 (kills became "
                   f"runner-observed with in-record hunks — that shape "
                   f"change is a version, PROCESS-R11-1)")
    if type(rec["entries"]) is not list or not rec["entries"]:
        bad.append("entries is not a non-empty list")
    else:
        for e in rec["entries"]:
            if type(e) is not dict or sorted(e) != [
                    "defends", "found_by", "hunks", "id", "mutation",
                    "node"]:
                bad.append(f"entry keys {sorted(e) if type(e) is dict else e}"
                           f" != the closed set")
                break
            if any(type(e[k]) is not str
                   for k in ("defends", "found_by", "id", "mutation",
                             "node")):
                bad.append(f"entry {e.get('id')!r} carries a non-string")
                break
            if e["found_by"] not in FOUND_BY:
                bad.append(f"entry {e['id']!r} found_by {e['found_by']!r} is "
                           f"outside the governed partition {FOUND_BY}")
                break
            hs = e["hunks"]
            if type(hs) is not list or not hs or any(
                    type(h) is not dict or sorted(h) != ["artifact", "new",
                                                         "old"]
                    or any(type(h[k]) is not str for k in h)
                    for h in hs):
                bad.append(f"entry {e['id']!r} hunks are not a non-empty "
                           f"list of {{artifact, new, old}} strings")
                break
    if type(rec["entries"]) is list:
        keys = {}
        for e in rec["entries"]:
            if type(e) is not dict or type(e.get("hunks")) is not list:
                break
            try:
                hs = [(h["artifact"], h["old"], h["new"])
                      for h in e["hunks"]]
            except (TypeError, KeyError):
                break
            # PROCESS-R14-1: the record carrier gets the SAME guard, and
            # it runs BEFORE identity touches the filesystem — a record
            # hunk naming /etc/passwd validated clean here, and /bin/sh
            # was READ and crashed the checker
            guarded = False
            for a, _o, _n in hs:
                for g in artifact_problems(a):
                    bad.append(f"record entry {e.get('id')!r}: {g}")
                    guarded = True
            if guarded:
                continue
            key = mutation_identity(hs)
            if key in keys:
                bad.append(f"record entries {keys[key]!r} and "
                           f"{e.get('id')!r} carry the same normalized "
                           f"hunk bundle (PROCESS-R12-1)")
                break
            keys[key] = e.get("id")
    v = rec["verified"]
    if type(v) is not dict or sorted(v) != ["clean", "kills",
                                            "leave_one_out"]:
        bad.append("verified is not {clean, kills, leave_one_out}")
    else:
        cl = v["clean"]
        if type(cl) is not dict or not cl or any(
                type(k) is not str or not _is_int(n) or n < 1
                for k, n in cl.items()):
            bad.append("verified.clean is not {node: positive int passed}")
        ks = v["kills"]
        if type(ks) is not list or not ks or any(
                type(k) is not dict or sorted(k) != ["exit", "failed", "id"]
                or type(k["id"]) is not str or k["exit"] != 1
                or not _is_int(k["exit"]) or not _is_int(k["failed"])
                or k["failed"] < 1
                for k in ks):
            bad.append("verified.kills is not a non-empty list of "
                       "{id, exit: 1, failed >= 1} — a kill is a REAL "
                       "test failure, observed")
        lo = v["leave_one_out"]
        if type(lo) is not list or any(
                type(k) is not dict or sorted(k) != ["dropped", "exit", "id"]
                or type(k["id"]) is not str or k["exit"] != 0
                or not _is_int(k["exit"]) or not _is_int(k["dropped"])
                for k in lo):
            bad.append("verified.leave_one_out is not a list of "
                       "{id, dropped, exit: 0} — each dropped hunk must "
                       "leave the node PASSING (the layer is alive)")
    t_ = rec["totals"]
    if type(t_) is not dict or sorted(t_) != ["all", "dev", "distinct_nodes",
                                              "hunks", "reviewer"]:
        bad.append(f"totals keys != the closed set (got "
                   f"{sorted(t_) if type(t_) is dict else t_})")
    elif not all(_is_int(x) for x in t_.values()):
        bad.append("a totals value is not an exact int")
    return bad


def _defense_span(src: str, name: str):
    """The source segment of the TOP-LEVEL function or constant `name` —
    the span a defense's hunks must fall inside (research F-B)."""
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef,
                             ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(src, node)
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name
                for t in node.targets):
            return ast.get_source_segment(src, node)
    return None


def validate_entries(entries=None) -> list:
    """Structural validity, independent of any run: unique ids, governed
    found_by, well-formed nodes, and hunks that name real, contained,
    NON-TEST artifacts whose old text occurs exactly once. A hunk aimed at
    a test file (or at this registry) would let an entry manufacture its
    own kill by breaking the very test that judges it — the artifact under
    mutation and the test that detects the mutation must be different
    files on opposite sides of the contract."""
    entries = ENTRIES if entries is None else entries
    bad = []
    ids = [e[0] for e in entries]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        bad.append(f"duplicate registry id(s): {sorted(dupes)}")
    seen_mut, seen_ws = {}, {}
    for e in entries:
        # PROCESS-R14-1: the guard runs BEFORE identity touches the
        # filesystem — an entry with any out-of-set, escaping or missing
        # artifact is excluded here and refused in the per-hunk loop below
        if any(artifact_problems(a) for a, _o, _n in e[5]):
            continue
        key = mutation_identity(e[5])
        wskey = _identity(e[5], fold_ws=True)
        if key in seen_mut:
            bad.append(f"duplicate mutation: {e[0]} produces the same "
                       f"resulting artifact bytes as {seen_mut[key]} — a "
                       f"second label for one transformation inflates the "
                       f"ledger whatever its id, finder, node, hunk "
                       f"partitioning or window (PROCESS-R12-1/R13-1)")
        elif wskey in seen_ws:
            bad.append(f"duplicate mutation: {e[0]} and {seen_ws[wskey]} "
                       f"differ only in whitespace of the mutated result "
                       f"— the cheapest semantically-equivalent variant, "
                       f"refused for human review (PROCESS-R12-1)")
        else:
            seen_mut[key] = e[0]
            seen_ws[wskey] = e[0]
    for i, by, mut, node, defends, hunks in entries:
        if by not in FOUND_BY:
            bad.append(f"{i}: found_by {by!r} outside the governed "
                       f"partition {FOUND_BY}")
        if not mut.strip():
            bad.append(f"{i}: empty mutation description")
        if not _NODE_RE.match(node):
            bad.append(f"{i}: {node!r} is not a plain pytest node id under "
                       f"tests/ — options or spaces could smuggle pytest "
                       f"arguments into the runner")
        if not hunks:
            bad.append(f"{i}: no hunks — an entry that mutates nothing can "
                       f"only 'survive' or fake a kill")
            continue
        for n, (art, old, new) in enumerate(hunks):
            # ONE shared guard for both carriers (PROCESS-R14-1):
            # inclusion-first, no filesystem access for an out-of-set path
            guard = artifact_problems(art)
            if guard:
                bad.extend(f"{i}.h{n}: {g}" for g in guard)
                continue
            full = ROOT / art
            if old == new:
                bad.append(f"{i}.h{n}: old and new text are identical")
                continue
            src = full.read_text()
            hits = src.count(old)
            if hits != 1:
                bad.append(f"{i}.h{n}: old text occurs {hits} times in "
                           f"{art} — exactly once is required for an "
                           f"unambiguous, verified application")
                continue
            # research F-B (proxy-kill): the hunk must mutate the DEFENSE
            # the entry names, not merely something the node's execution
            # touches — an observed failure otherwise proves noise, not
            # a live defense. The span is located by ast at check time,
            # so a refactor that moves the old text into a comment,
            # docstring or dead copy outside the defense refuses here.
            span = _defense_span(src, defends)
            if span is None:
                bad.append(f"{i}.h{n}: defends {defends!r} names no "
                           f"top-level function or constant in {art}")
            elif old not in span:
                bad.append(f"{i}.h{n}: old text lies OUTSIDE the source "
                           f"span of {defends!r} — a hunk off the defense "
                           f"can only buy a proxy-kill")
    return bad


class _Restorer:
    """Apply hunks inside the campaign SNAPSHOT; restore BYTE-IDENTICALLY
    between entries, verified. The live tree is never touched."""

    def __init__(self, root):
        self.root, self.originals = root, {}

    def apply(self, hunks) -> list:
        """Grouped per artifact IN ENTRY ORDER and routed through
        _apply_hunks_to_text — the same function, in the same order, the
        identity digests. Executed bytes and digested bytes cannot
        disagree, because they are the same computation."""
        bad = []
        per_art = {}
        for art, old, new in hunks:
            per_art.setdefault(art, []).append((old, new))
        for art, pairs in per_art.items():
            p = self.root / art
            src = p.read_text()
            if art not in self.originals:
                self.originals[art] = src
            applied, probs = _apply_hunks_to_text(src, pairs)
            bad.extend(f"{art}: {b}" for b in probs)
            if applied is not None:
                p.write_text(applied)
        return bad

    def restore(self) -> list:
        bad = []
        for art, original in self.originals.items():
            p = self.root / art
            p.write_text(original)
            if p.read_text() != original:
                bad.append(f"{art} did NOT restore byte-identically")
        self.originals = {}
        return bad


def _run_node(node, root) -> tuple:
    """One isolated pytest run. Returns (exit, passed, failed, skipped) —
    counts parsed from the summary line, -1 when absent (skipped 0).
    PROCESS-R11-1: the caller must judge ALL of these; an exit code alone
    said nothing when the tests never ran (exit 4, zero collected, empty
    kills looked exactly like the defense working).

    Research F-D: the environment is SCRUBBED — PYTEST_ADDOPTS or
    PYTEST_PLUGINS in the invoking environment could deselect, soften or
    substitute what this run observes, and plugin autoload is disabled so
    nothing outside the tree joins the verdict."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")}
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    # STALE-BYTECODE HAZARD (found live, 2026-08-28): pyc invalidation is
    # mtime+size, the hunks are often length-preserving, and the campaign's
    # patch->run->restore cycles fit inside one mtime second — so a run can
    # execute ANOTHER run's cached semantics and report a false survival
    # (or a false kill). Every subprocess gets a FRESH, private bytecode
    # namespace; adjacent __pycache__ dirs are bypassed entirely.
    import shutil
    import tempfile
    cache = tempfile.mkdtemp(prefix="veracium-mutant-pyc-")
    env["PYTHONPYCACHEPREFIX"] = cache
    try:
        # research (round-15 pass): pytest's default rootdir/confcutdir
        # resolution DOES land at the snapshot and bounds conftest
        # discovery there — verified empirically with a planted parent
        # conftest — but that closure is by-configuration. Pinning both
        # makes it by-construction, the arc's own standard against
        # agreement by coincidence (a parent-dir conftest would be code
        # execution, not just a read).
        r = subprocess.run(
            [sys.executable, "-m", "pytest", node, "-q", "-p",
             "no:randomly", f"--rootdir={root}", f"--confcutdir={root}"],
            cwd=root, capture_output=True, text=True, env=env)
    finally:
        shutil.rmtree(cache, ignore_errors=True)
    passed = failed = -1
    skipped = 0
    tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    for count, word in re.findall(r"(\d+) (passed|failed|skipped|xfailed|"
                                  r"xpassed|deselected)", tail):
        if word == "passed":
            passed = int(count)
        elif word == "failed":
            failed = int(count)
        else:
            skipped += int(count)
    return r.returncode, passed, failed, skipped


def _snapshot(root) -> str:
    """A private copy of everything a campaign run touches — src, tests,
    specs (minus the archive tarballs) and the pytest entry files.

    THE CAMPAIGN NEVER MUTATES THE LIVE TREE. The first design patched in
    place with verified restores, and reality supplied three failure modes
    in one afternoon: a concurrent campaign interleaved apply/restore and
    froze a mutation into the fold checker; a killed campaign left a
    frozen hunk behind (validate_entries refused loudly, as designed, but
    the tree still needed hand repair); and the closure-evidence gate runs
    ledger commands CONCURRENTLY, so sibling commands read artifacts
    mid-mutation. A snapshot makes every reader of the real tree safe by
    construction, a crash costs a temp dir, and concurrent campaigns
    cannot see each other at all. Symlinks are DEREFERENCED by the
    copy (research, round-11 pass): a link's target content lands in the
    snapshot as a regular file, so a hunk writes to the snapshot copy,
    never through a link to the live tree — the dereference is the
    protection."""
    import os as _os
    import shutil
    import tempfile
    rp = pathlib.Path(root)
    # PROCESS-R14-1, snapshot half (research): copytree with
    # symlinks=False DEREFERENCES — a committed symlink anywhere under
    # the copied dirs would make the snapshot READ its target, inside
    # the tree or out (an escaping link is an out-of-tree read the
    # artifact guard never sees, because the snapshot copies the WHOLE
    # tree, not the four guarded artifacts). A symlink in this tree is
    # anomalous, so the posture is refusal, not skipping: pre-scan
    # without following links, and ERROR naming the first one found —
    # before any copy, so nothing is read through it.
    for d in ("src", "tests", "specs"):
        base = rp / d
        # PROCESS-R15-1: the ROOT of each copied dir is a node of the
        # scanned tree too — is_dir() follows symlinks, os.walk() walks a
        # symlinked top even with followlinks=False, and copytree then
        # dereferences it, so a symlinked src/tests/specs was an
        # unguarded read of an entire external tree. The recursion-base
        # case of the round-14 property, checked BEFORE is_dir/walk.
        if base.is_symlink():
            raise RuntimeError(
                f"symlink in the campaign tree: {base} — a symlinked "
                f"copy root would be dereferenced wholesale (reading an "
                f"external tree); a symlink here is anomalous and "
                f"refuses")
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in _os.walk(base,
                                                     followlinks=False):
            # CHECK, then prune (research): a symlinked dir named like a
            # pruned one would otherwise slip the scan — it is also
            # copy-ignored, so no read would occur, but the scan and the
            # copy sharing an exclusion list by coincidence is the
            # agreement-by-coincidence shape this round retired
            for name in dirnames + filenames:
                p_ = pathlib.Path(dirpath) / name
                if p_.is_symlink():
                    raise RuntimeError(
                        f"symlink in the campaign tree: {p_} — the "
                        f"snapshot copy would dereference it (reading "
                        f"its target, possibly outside the tree); a "
                        f"symlink here is anomalous and refuses")
            dirnames[:] = [x for x in dirnames
                           if x not in ("__pycache__", "archives",
                                        ".pytest_cache")]
    snap = tempfile.mkdtemp(prefix="veracium-mutant-tree-")
    for name in ("conftest.py", "pyproject.toml", "pytest.ini",
                 "setup.cfg", "setup.py"):
        f = rp / name
        # PROCESS-R15-1: a symlinked (or broken-symlink) config carrier
        # REFUSES rather than being silently omitted — silent omission
        # would quietly change what the campaign's pytest runs under
        if f.is_symlink():
            raise RuntimeError(
                f"symlink in the campaign tree: {f} — a symlinked "
                f"configuration carrier refuses rather than being "
                f"silently dropped from the snapshot")
        if f.is_file():
            shutil.copy2(f, snap)
    for d in ("src", "tests", "specs"):
        f = rp / d
        if f.is_dir():
            shutil.copytree(
                f, pathlib.Path(snap) / d,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "archives", "*.tar.gz",
                    ".pytest_cache"))
    return snap


def execute(entries=None, root=None) -> tuple:
    """The campaign, runner-observed end to end, in a PRIVATE SNAPSHOT of
    `root`. Returns (verified, problems): `verified` is the record's
    verified block, `problems` is every deviation, each named. Nothing
    here trusts a test's account of what it did — only exit codes,
    summary counts, and the runner's own knowledge of which hunks it
    applied. The live tree is read-only to the whole campaign."""
    import shutil
    entries = ENTRIES if entries is None else entries
    root = ROOT if root is None else pathlib.Path(root)
    try:
        snap = _snapshot(root)
    except RuntimeError as exc:
        return (dict(clean={}, kills=[], leave_one_out=[]),
                [f"campaign REFUSED before any copy: {exc}"])
    try:
        return _execute_in(entries, pathlib.Path(snap))
    finally:
        shutil.rmtree(snap, ignore_errors=True)


def _execute_in(entries, root) -> tuple:
    problems = []
    clean = {}
    for node in sorted({e[3] for e in entries}):
        code, passed, _failed, skipped = _run_node(node, root)
        if code != 0 or passed < 1 or skipped != 0:
            problems.append(f"CLEAN {node}: exit {code}, {passed} passed, "
                            f"{skipped} skipped/xfailed/deselected — the "
                            f"campaign has no baseline (research F-C: a "
                            f"skip-laundered node exits 0 having proven "
                            f"nothing)")
            continue
        clean[node] = passed
    kills, loo = [], []
    for i, _by, _mut, node, _defends, hunks in entries:
        if node not in clean:
            problems.append(f"{i}: no clean baseline for {node}; skipped")
            continue
        rest = _Restorer(root)
        try:
            bad = rest.apply(hunks)
            if bad:
                problems.extend(f"{i}: {b}" for b in bad)
                continue
            code, _passed, failed, _skipped = _run_node(node, root)
        finally:
            problems.extend(f"{i}: {b}" for b in rest.restore())
        if code == 0:
            problems.append(f"{i}: SURVIVED — {node} passed with all "
                            f"{len(hunks)} hunk(s) applied; the mutation "
                            f"is not killed by its declared node")
            continue
        if code != 1 or failed < 1:
            problems.append(f"{i}: campaign ERROR — {node} exited {code} "
                            f"with {failed} failed under mutation; only a "
                            f"real test failure is a kill (PROCESS-R11-1: "
                            f"a run that never happened is not a defense)")
            continue
        kills.append(dict(id=i, exit=code, failed=failed))
        for n in range(len(hunks)):
            if len(hunks) == 1:
                break
            subset = tuple(h for j, h in enumerate(hunks) if j != n)
            rest = _Restorer(root)
            try:
                bad = rest.apply(subset)
                if bad:
                    problems.extend(f"{i}.drop{n}: {b}" for b in bad)
                    continue
                code, passed, _failed, skipped = _run_node(node, root)
            finally:
                problems.extend(f"{i}.drop{n}: {b}" for b in rest.restore())
            if code != 0 or passed < 1 or skipped != 0:
                problems.append(f"{i}: hunk {n} is NOT individually "
                                f"load-bearing — dropping it still fails "
                                f"{node} (exit {code}); the entry "
                                f"overstates the defense depth")
                continue
            loo.append(dict(id=i, dropped=n, exit=code))
    verified = dict(clean=clean, kills=sorted(kills, key=lambda k: k["id"]),
                    leave_one_out=sorted(loo, key=lambda k: (k["id"],
                                                             k["dropped"])))
    return verified, problems


def coverage_problems(entries, verified) -> list:
    """Every entry killed, every multi-hunk entry minimality-witnessed —
    computed from the verified block, so a record missing an observation
    cannot claim the campaign was complete."""
    bad = []
    killed_ids = {k["id"] for k in verified["kills"]}
    for i, _by, _mut, node, _defends, hunks in entries:
        if i not in killed_ids:
            bad.append(f"{i}: no observed kill")
        if node not in verified["clean"]:
            bad.append(f"{i}: node {node} has no clean baseline")
        expect = len(hunks) if len(hunks) > 1 else 0
        got = len([l for l in verified["leave_one_out"] if l["id"] == i])
        if got != expect:
            bad.append(f"{i}: {got} leave-one-out witnesses, expected "
                       f"{expect}")
    return bad


def build_record(entries, verified) -> dict:
    by_finder: dict = {}
    for e in entries:
        by_finder[e[1]] = by_finder.get(e[1], 0) + 1
    return dict(
        schema=4,
        entries=[dict(id=i, found_by=f, mutation=m, node=n,
                      defends=d,
                      hunks=[dict(artifact=a, old=o, new=w)
                             for a, o, w in hs])
                 for i, f, m, n, d, hs in entries],
        verified=verified,
        totals=dict(**by_finder, all=len(entries),
                    distinct_nodes=len({e[3] for e in entries}),
                    hunks=sum(len(e[5]) for e in entries)),
    )


def main() -> int:
    write = "--write" in sys.argv
    if write:
        bad = validate_entries()
        if bad:
            print("mutant registry INVALID:\n  " + "\n  ".join(bad),
                  file=sys.stderr)
            return 1
        verified, problems = execute()
        problems += coverage_problems(ENTRIES, verified)
        if problems:
            print("mutant registry FAILED:\n  " + "\n  ".join(problems),
                  file=sys.stderr)
            return 1
        record = build_record(ENTRIES, verified)
        RECORD.write_text(canonical_bytes(record))
        print(f"mutant registry: {record['totals']['all']} entries, every "
              f"kill OBSERVED by the runner (exit 1, real failures), "
              f"{len(verified['leave_one_out'])} leave-one-out minimality "
              f"witnesses; record WRITTEN")
        return 0
    return run_check(RECORD)


def run_check(record_path: pathlib.Path) -> int:
    """The whole check, over an explicit operand. `main()` pins it to
    RECORD — EVIDENCE-M10-1: an environment selector introduced for
    testing let the reviewer point the 'shipped record' at a pristine
    alternate file; tests exercise corrupt operands through THIS helper
    on copies, and the command entry point takes no selector at all.

    Order (grammar FIRST): parse strictly, validate the closed schema,
    require the raw bytes to BE the canonical serialisation of what they
    parse to — all before the campaign runs — and only then recompute
    and require equality with reality."""
    if not record_path.exists():
        print("mutant_results.json is MISSING — nothing to check",
              file=sys.stderr)
        return 1
    raw = record_path.read_text()
    try:
        shipped = strict_parse(raw)
    except ValueError as exc:
        print(f"shipped record REFUSED at parse: {exc}", file=sys.stderr)
        return 1
    gram = validate_record(shipped)
    if gram:
        print("shipped record REFUSED by the grammar:\n  "
              + "\n  ".join(gram), file=sys.stderr)
        return 1
    if raw != canonical_bytes(shipped):
        print("shipped bytes are not the canonical serialisation of their "
              "own content — refused before any recomputation",
              file=sys.stderr)
        return 1
    # only a well-formed, canonically-serialised record earns a campaign
    # run — and only a VALID registry does (PROCESS-R12-1: the duplicate
    # refusal must land at this boundary, cheaply, before ~45 subprocess
    # runs are spent on a ledger already known to lie)
    problems = validate_entries()
    if problems:
        print("mutant registry FAILED:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    verified, run_problems = execute()
    problems = run_problems + coverage_problems(ENTRIES, verified)
    if problems:
        print("mutant registry FAILED:\n  " + "\n  ".join(problems),
              file=sys.stderr)
        return 1
    record = build_record(ENTRIES, verified)
    # PROCESS-R8-1(2): dict equality COERCES — False == 0, True == 1 — so a
    # boolean smuggled into an int field claimed an exact match. Canonical
    # SERIALIZED BYTES are compared instead ("false" is not "0"), after a
    # typed sanity pass on the fields coercion can reach.
    if raw != canonical_bytes(record):
        for k in sorted(set(shipped) | set(record)):
            if (json.dumps(shipped.get(k), sort_keys=True)
                    != json.dumps(record.get(k), sort_keys=True)):
                print(f"shipped record DIVERGES at {k!r}", file=sys.stderr)
        print("shipped record does not match the RECOMPUTED campaign",
              file=sys.stderr)
        return 1
    t_ = record["totals"]
    print(f"mutant registry: {t_['all']} entries ({t_.get('reviewer', 0)} "
          f"reviewer + {t_.get('dev', 0)} dev), {t_['hunks']} hunks, every "
          f"kill runner-observed, shipped record matches the recomputation "
          f"exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
