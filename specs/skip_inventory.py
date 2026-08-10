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
    ("tests/test_mcp.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK is absent"),
    ("tests/test_spec_gate.py", "skip", "COLLECTED.txt not present",
     "package-artifact", "binds COLLECTED's inventory to render(); runs only in "
                         "an extracted review package"),
    ("tests/test_eval.py", "skipif", "VERACIUM_EVAL",
     "env-flag", "live acceptance-eval tier"),
    ("tests/test_robustness.py", "skipif", "VERACIUM_ROBUSTNESS",
     "env-flag", "live robustness tier"),
    ("tests/test_spec_gate.py", "skip", "COORDINATION.md not present",
     "host-conditional", "local-only coordination file absent"),
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


def render() -> str:
    """The COLLECTED.txt inventory section, generated from INVENTORY."""
    classes = {}
    for f, kind, token, cls, reason in INVENTORY:
        classes.setdefault(cls, []).append(f"{f} ({kind}: {reason})")
    order = ["git-checkout", "env-flag", "optional-dependency", "package-artifact",
             "host-conditional"]
    blurb = {
        "git-checkout": ("git-checkout-dependent (SKIPPED in the measured line — the "
                         "measuring copy has no .git — and in your extracted run):"),
        "env-flag": "env-flag tiers (SKIPPED unless the flag is set; part of the measured line):",
        "optional-dependency": ("optional-dependency (PASS where the package is installed, "
                                "SKIP where absent):"),
        "package-artifact": ("package-artifact (SKIPPED in the measured line and in git "
                             "checkouts; RUNS in your extracted package, where "
                             "COLLECTED.txt exists — so your run gains one PASS here):"),
        "host-conditional": ("host-conditional (may differ between the authoring host and "
                             "yours — the usual source of reviewer deltas):"),
    }
    out = []
    for cls in order:
        if cls in classes:
            out.append("  " + blurb[cls])
            out += [f"    {line}" for line in classes[cls]]
    out.append("  Any delta NOT explained by a named test above is a finding.")
    return "\n".join(out)


if __name__ == "__main__":
    print(render())


BEGIN_MARKER = "<!-- GENERATED:skip-inventory -->"
END_MARKER = "<!-- /GENERATED:skip-inventory -->"


def verify_collected(text: str) -> None:
    """Byte-exact carrier verification (R15-1 — the first verifier split on the
    first marker pair and stripped boundary newlines, so a duplicated complete
    block and an extra blank line after the opening marker both passed).

    Rules, exactly as the reviewer required: markers count only as COMPLETE
    STANDALONE LINES; exactly one opening and one closing marker; the enclosed
    block is compared to render() with NO normalization. Raises ValueError with
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
    expected = render()
    if block != expected:
        raise ValueError(
            "the enclosed inventory block is not byte-identical to render() "
            "(stale, hand-edited, or boundary-padded)")
