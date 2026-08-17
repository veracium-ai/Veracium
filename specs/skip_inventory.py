"""The canonical environment-conditional skip inventory (0014 R13-3).

Round 13 found the COLLECTED.txt inventory hand-listed and INCOMPLETE — the
optional-MCP importorskip was missing, so the reviewer's suite delta could not
fully reconcile against names. The inventory is therefore now a committed
module with a mechanical completeness gate
(tests/test_spec_gate.py::test_conditional_skip_inventory_is_complete): every
skip/skipif/importorskip site in tests/ must match an entry here, and every
entry must match a live site — a new conditional skip breaks the gate until it
is inventoried, and a stale entry breaks it until removed.

Each entry: (file, kind, condition_token, condition_class, reason).
`condition_token` must appear verbatim within the skip site's source (the
matching window spans the call line plus the following four lines, covering
multi-line messages). `condition_class` is one of:
  git-checkout        — skips when the tree is not a git checkout (always
                        skipped in the measured line and in extracted runs)
  env-flag            — opt-in live tiers, skipped unless the flag is set
  optional-dependency — skips when an optional package is absent
  host-conditional    — depends on host state (files present, runtime
                        identity, euid); the usual source of reviewer deltas
  package-artifact    — runs only inside an extracted review package (R14-1)
COLLECTED.txt's inventory section is generated from this module — one source,
and BOUND at both ends (R14-1): packaging asserts the marked COLLECTED section
equals render() before sealing, and
tests/test_spec_gate.py::test_collected_inventory_matches_the_generator makes
the same assertion inside the extracted package, so a stale or hand-edited
shipped inventory fails in the reviewer's own run.
"""

INVENTORY = [
    ("tests/test_0015_lifecycle.py", "skip", "POSIX adapter test (specs/0015 I17)",
     "host-conditional", "the two 0015 lock-adapter tests run the POSIX kernel "
                         "contract via independent processes; they skip on "
                         "non-POSIX hosts (the Windows pair is a platform-gated "
                         "implementation obligation per 0015 R9-4/R10-3)"),
    ("tests/test_0015_lifecycle.py", "skip", "POSIX adapter test (specs/0015 I17)",
     "host-conditional", "the death-release half of the same POSIX pair"),
    ("tests/test_mcp.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK — the importorskip is INSIDE "
                            "test_mcp_server_wiring ONLY (external 0018 B3-1: "
                            "the earlier ×5 claim mistook the file's test count "
                            "for the gate's scope); the file's other 4 tests "
                            "run without the SDK. Author line: all 5 PASS (mcp "
                            "importable in the authoring venv); an mcp-absent "
                            "environment sees 4 PASS + 1 SKIP"),
    # ---- FOUR ENTRIES MISSING SINCE 0021 SHIPPED (external round 3, R3-5).
    # These skip UNCONDITIONALLY on every host and were in no category, so the
    # generated inventory decomposed a measured line it could not account for
    # and `verify_collected` passed anyway — it checks the block EQUALS the
    # generator's output, which is true of an incomplete generator. The
    # reviewer's extracted run surfaced them with `-rs`; ours never printed
    # skip reasons at all. The reconciler added alongside this list is the
    # real fix; these entries are what it needs to reconcile against.
    ("tests/test_0021_maintain_scope.py", "skip",
     "W6 is the LIVE",
     "future-obligation",
     "1 test. UNCONDITIONAL on every host: it needs a real model and the "
     "benchmark harness, and a simulated leak probe measures the simulation. "
     "0021 W6 names it as research's D-extension obligation"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W16's reparenting half",
     "future-obligation",
     "1 test. UNCONDITIONAL: 0021 §7a names the primitive FUTURE and §2c-ii "
     "asserts executably that it has no shipped writer; the born-closed half "
     "IS covered by test_transitive_absorption_chains"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W17 is the shipped evidence program",
     "future-obligation",
     "1 test. UNCONDITIONAL: the check lives in "
     "specs/evidence/0020/ledger_plan_harness.py, which extracts the REAL "
     "contribution_ledger DDL from a live store; a pytest copy would be a "
     "weaker second implementation"),
    ("tests/test_0021_maintain_scope.py", "skip",
     "W18's after-a-prune half",
     "future-obligation",
     "1 test. UNCONDITIONAL, same FUTURE primitive as W16; the before half is "
     "test_native_chain_export_carries_absorbed_by_id_on_both_absorbed"),
    ("tests/test_spec_gate.py", "skip", "COLLECTED.txt not present",
     "package-artifact", "binds COLLECTED's inventory to render(); 1 test. "
                         "SINCE THE 0020/0021 R2 SEAL REORDER the measured "
                         "line is the PACKAGED-STATE run (COLLECTED present "
                         "in the measuring tree), so this test EXECUTES AND "
                         "PASSES in the measured line — and in your "
                         "extraction, which also carries COLLECTED. A "
                         "COLLECTED-less copy (e.g. a bare git clone) sees "
                         "it SKIP; either status reconciles, and your report "
                         "should say which"),
    ("tests/test_eval.py", "skipif", "VERACIUM_EVAL",
     "env-flag", "live acceptance-eval tier"),
    # (specs/0016 D2: the VERACIUM_MIN_DEP_JOB floor regression was removed
    # with the D1 warning surface it exercised — Field(deprecated=...) is gone)
    ("tests/test_robustness.py", "skipif", "VERACIUM_ROBUSTNESS",
     "env-flag", "live robustness tier"),
    ("tests/test_spec_gate.py", "skip", "COORDINATION.md not present",
     "host-conditional", "reads a HOME-anchored local-only coordination file — "
                         "1 test, PASS in the measured line (the file exists "
                         "on the authoring HOST, outside the tree); SKIP on "
                         "any other host"),
    ("tests/test_spec_gate.py", "skip", "not a git checkout",
     "git-checkout", "STATUS.md `updated` derives from git log"),
    ("tests/test_spec_gate.py", "skip", "no archives present",
     "git-checkout", "archives are gitignored; a clone has none"),
    ("tests/longmemeval/test_run_wiring.py", "skipif", "not a git checkout",
     "git-checkout", "a run's manifest resolves git state by design"),
    ("tests/longmemeval/test_manifest.py", "skip", "not a git checkout",
     "git-checkout", "git_state() resolves rather than remembers"),
    ("tests/test_migrations_0013.py", "skip", "different runtime identity",
     "host-conditional", "artifact records a different runtime identity"),
    ("tests/test_migrations_0013.py", "skipif", "geteuid",
     "host-conditional", "root euid defeats the read-only-store fixture"),
    ("tests/test_schema_model.py", "skip", "not a qualified runtime",
     "host-conditional", "unqualified SQLite runtime (the gate working)"),
    ("tests/test_schema_model.py", "skip", "no git checkout",
     "git-checkout", "check() returns 2 before reaching the assertion"),
]


def render(rs_output: str = "") -> str:
    """The COLLECTED.txt inventory section, generated from INVENTORY.

    `rs_output` is the sealed `pytest -q -rs` text. Supplying it makes the
    reconciliation block OBSERVED rather than remembered (R4-4).
    """
    classes = {}
    for f, kind, token, cls, reason in INVENTORY:
        classes.setdefault(cls, []).append(f"{f} ({kind}: {reason})")
    # EXTERNAL ROUND 4, R4-4. This list was HARD-CODED and omitted
    # "future-obligation", so the four entries added at round 3 went into
    # INVENTORY and never reached the rendered block: the data was right, the
    # renderer could not see it, and `verify_collected` compared the block to
    # that same blind renderer. The order stays explicit for readability, but
    # any category present in INVENTORY and missing from it now RAISES rather
    # than being silently dropped — the renderer's domain is INVENTORY's, not
    # a list someone remembered to extend.
    order = ["git-checkout", "env-flag", "optional-dependency", "package-artifact",
             "host-conditional", "future-obligation"]
    unordered = sorted(set(classes) - set(order))
    if unordered:
        raise ValueError(
            f"INVENTORY carries categories this renderer would silently drop: "
            f"{unordered}. Add them to `order` and `blurb` — the failure this "
            f"guard exists for is external round 4's R4-4.")
    blurb = {
        "git-checkout": ("git-checkout-dependent (SKIPPED in the measured line — the "
                         "measuring copy has no .git — and in your extracted run):"),
        "env-flag": "env-flag tiers (SKIPPED unless the flag is set; part of the measured line):",
        "optional-dependency": ("optional-dependency (per-entry counts and the measured "
                                "author status are in each entry):"),
        "package-artifact": ("package-artifact (status depends on whether COLLECTED.txt is "
                             "in the tree you run — see the entry):"),
        "host-conditional": ("host-conditional (may differ between the authoring host and "
                             "yours — the usual source of reviewer deltas; each entry "
                             "carries its count and measured author status):"),
        "future-obligation": ("future-obligation (SKIPPED UNCONDITIONALLY on every host, "
                              "including yours and ours — each names a primitive or a "
                              "live-model probe a spec marks FUTURE. These four were "
                              "absent from this inventory until external round 4 because "
                              "the completeness gate's regex did not recognise "
                              "`pytest.mark.skip(`):"),
    }
    out = []
    for cls in order:
        if cls in classes:
            out.append("  " + blurb[cls])
            out += [f"    {line}" for line in classes[cls]]
    out.append(
        "  RECONCILIATION — DERIVED FROM THE MEASURED RUN, not hand-written\n"
        "  (external round 4, R4-4). The block that stood here until v5 was\n"
        "  prose: it decomposed a measured line as 'git-checkout 11 + env-flag 3\n"
        "  = 14' while the measured line said 6, cited a pydantic-floor\n"
        "  regression that no longer exists, and claimed 'the seal verifies this\n"
        "  decomposition' — which nothing did. An arithmetic claim maintained by\n"
        "  hand beside a number produced by a machine will drift, and did.\n"
        + _observed_block(rs_output))
    return "\n".join(out)


def _observed_block(rs_output) -> str:
    """The decomposition, computed from `pytest -q -rs` output.

    No argument means no measured run was supplied, and the block SAYS SO
    rather than reciting a remembered decomposition — the failure R4-4 found.
    """
    if not rs_output:
        return ("  NO MEASURED RUN WAS SUPPLIED to the renderer, so no\n"
                "  decomposition is claimed here. The seal supplies one; a\n"
                "  block without these numbers was not sealed.\n")
    import re as _re
    from collections import Counter
    cat_of = {}
    for f, _kind, token, cls, _reason in INVENTORY:
        cat_of.setdefault(f, []).append((token, cls))
    counts, unmatched, total = Counter(), [], 0
    for m in _re.finditer(r"^SKIPPED \[(\d+)\] ([^:]+):\d+: (.*)$", rs_output, _re.M):
        n, path, reason = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        total += n
        hit = None
        for f, pairs in cat_of.items():
            tail = f.split("tests/")[-1]
            if path.endswith(tail):
                for token, cls in pairs:
                    if token.lower() in reason.lower():
                        hit = cls
                        break
            if hit:
                break
        if hit:
            counts[hit] += n
        else:
            unmatched.append(f"{path}: {reason[:60]}")
    lines = ["  OBSERVED in the sealed run, by category:"]
    for cls, n in sorted(counts.items()):
        lines.append(f"    {cls}: {n}")
    lines.append(f"    TOTAL: {total}")
    # The PASS count is deliberately NOT echoed here. It belongs in COLLECTED's
    # header, which is not byte-compared. Putting it in the generated block made
    # the block depend on the pass count, which depends on whether the block is
    # correct (the packaged-state test verifies it) — a fixed point that cannot
    # converge: build the block, the pass count changes, the block no longer
    # matches. Caught while sealing round 5, by running the suite twice and
    # diffing the two renderings. Only the SKIP arithmetic belongs to this
    # block, and it is stable across that feedback.
    summary = _re.search(r"(\d+) passed, (\d+) skipped", rs_output)
    if summary:
        lines.append(f"    summary line skips: {summary.group(2)}")
        if int(summary.group(2)) != total:
            lines.append("    *** MISMATCH: the -rs section and the summary "
                         "disagree ***")
    if unmatched:
        lines.append("    *** OBSERVED SKIPS MATCHING NO ENTRY ***")
        lines += [f"      {u}" for u in unmatched]
    lines.append("  Your environment will differ where the categories above say "
                 "it will;")
    lines.append("  reconcile() computes this same table from YOUR run.")
    return "\n".join(lines) + "\n"



if __name__ == "__main__":
    print(render())


BEGIN_MARKER = "<!-- GENERATED:skip-inventory -->"
END_MARKER = "<!-- /GENERATED:skip-inventory -->"


def verify_collected(text: str, rs_output: str = "") -> None:
    """Byte-exact carrier verification.

    `rs_output` MUST be the same sealed `pytest -rs` text the block was
    rendered with (external round 4, R4-4 made the decomposition observed
    rather than recited). Verifying with a different argument than the block
    was built with compares two different renderings and fails loudly, which
    is the correct direction: the alternative is a check that passes because
    both sides forgot the same thing.

    Original docstring follows.

    Byte-exact carrier verification (R15-1 — the first verifier split on the
    first marker pair and stripped boundary newlines, so a duplicated complete
    block and an extra blank line after the opening marker both passed).

    Rules, exactly as the reviewer required: markers count only as COMPLETE
    STANDALONE LINES; exactly one opening and one closing marker; the enclosed
    block is compared to render(rs_output) with NO normalization OF THE DECODED TEXT.
    Narrowed claim (0014 round-16 bin-(b) obligation): callers typically read
    the carrier via Path.read_text(), which normalizes CRLF — so the guarantee
    is TEXT-EXACT across line-ending conversion; the implementation may upgrade
    to raw-bytes verification per the acceptance ledger. Raises ValueError with
    a specific reason; returns None on success. Shared by the packaging step
    and tests/test_spec_gate.py — one verifier, no drift."""
    lines = text.split("\n")
    begins = [i for i, l in enumerate(lines) if l == BEGIN_MARKER]
    ends = [i for i, l in enumerate(lines) if l == END_MARKER]
    if len(begins) != 1 or len(ends) != 1:
        raise ValueError(
            f"expected exactly one standalone begin and end marker, found "
            f"{len(begins)} begin / {len(ends)} end (a duplicated block or a "
            f"missing/edited marker)")
    b, e = begins[0], ends[0]
    if e <= b:
        raise ValueError("end marker precedes begin marker")
    block = "\n".join(lines[b + 1:e])
    expected = render(rs_output)
    if block != expected:
        raise ValueError(
            "the enclosed inventory block is not byte-identical to render(rs_output) "
            "(stale, hand-edited, or boundary-padded)")


# ---------------------------------------------------------------------------
# RECONCILIATION — external round 3, R3-5.
#
# `verify_collected` proves the shipped block EQUALS this generator's output.
# That is a real check and it is not the one that was needed: an INCOMPLETE
# generator satisfies it perfectly, which is exactly what happened — four
# unconditional skips were invisible to the completeness gate's regex, absent
# from this list, and `verify_collected` passed while COLLECTED's own
# decomposition could not account for its own measured line.
#
# So this reconciles against REALITY rather than against ourselves: it parses
# `pytest -q -rs` output and requires every OBSERVED skip reason to match an
# inventory entry, and the totals to agree. A skip nobody listed is a failure,
# not a rounding difference.
def reconcile(pytest_rs_output: str) -> list:
    """Return a list of problems; empty means the run reconciles.

    Feed it the FULL `pytest -q -rs` output. Two independent checks:
      1. every `SKIPPED [n] path:line: reason` line matches an entry (by file
         and by a token of the reason);
      2. the count of observed skips equals the summary line's skip count, so
         a truncated `-rs` section cannot pass by omission.
    """
    import re as _re
    problems = []
    observed = []
    for m in _re.finditer(r"^SKIPPED \[(\d+)\] ([^:]+):\d+: (.*)$",
                          pytest_rs_output, _re.M):
        n, path, reason = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        observed.append((n, path, reason))
    for n, path, reason in observed:
        # the harness may report a path relative to a different root
        tail = path.split("tests/")[-1]
        hit = any(entry_file.endswith(tail) or tail.endswith(entry_file.split("tests/")[-1])
                  for entry_file, _, _, _, _ in INVENTORY
                  if _token_matches(reason, entry_file))
        if not hit:
            problems.append(f"OBSERVED SKIP NOT IN THE INVENTORY: {path}: {reason[:90]}")
    summary = _re.search(r"(\d+) passed, (\d+) skipped", pytest_rs_output)
    if summary:
        claimed = int(summary.group(2))
        total = sum(n for n, _, _ in observed)
        if total != claimed:
            problems.append(
                f"the -rs section lists {total} skips but the summary says "
                f"{claimed} — the report is truncated or the parse is wrong")
    elif observed:
        problems.append("no summary line found; cannot reconcile totals")
    return problems


# EXTERNAL ROUND 5, R5-4. An entry's `token` is a SOURCE-SITE token — it must
# appear near the `pytest.skip(...)` call so the completeness gate can find the
# site. pytest emits the RESOLVED reason, which is often different text: the
# euid entry's token is `geteuid` (what the source says) while pytest prints
# "root traverses any directory...". Matching emitted reasons against
# source tokens therefore reported a listed skip as unlisted on any root host —
# and only on a root host, which is why our own runs never saw it.
#
# The two vocabularies are now separate. EMITTED holds the reason text pytest
# prints, keyed by (file, source-token); reconcile matches against either.
EMITTED = {
    ("tests/test_migrations_0013.py", "geteuid"):
        ("root traverses any directory", "running as root"),
}


def _token_matches(reason: str, entry_file: str) -> bool:
    r = reason.lower()
    for f, _kind, token, _cat, _note in INVENTORY:
        if f != entry_file:
            continue
        if token.lower() in r:
            return True
        for emitted in EMITTED.get((f, token), ()):
            if emitted.lower() in r:
                return True
    return False
