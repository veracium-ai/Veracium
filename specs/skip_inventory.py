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
COLLECTED.txt's inventory section is generated from this module — one source.
"""

INVENTORY = [
    ("tests/test_mcp.py", "importorskip", "mcp",
     "optional-dependency", "the optional MCP SDK is absent"),
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
    order = ["git-checkout", "env-flag", "optional-dependency", "host-conditional"]
    blurb = {
        "git-checkout": ("git-checkout-dependent (SKIPPED in the measured line — the "
                         "measuring copy has no .git — and in your extracted run):"),
        "env-flag": "env-flag tiers (SKIPPED unless the flag is set; part of the measured line):",
        "optional-dependency": ("optional-dependency (PASS where the package is installed, "
                                "SKIP where absent):"),
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
