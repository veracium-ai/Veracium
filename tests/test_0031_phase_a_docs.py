"""specs/0031 Phase A, punch-list F1: the §8 boundary and the configuration
facts are carried by EVERY documentation surface, bound mechanically so the
default and the warning cannot diverge across them.

The facts are canonical strings; each surface must contain each. A surface
that paraphrases the boundary into "verified" or drops the default fails
here, not in a reader's deployment.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# the enumerated surfaces (F1)
SURFACES = {
    "docs/mcp.md": ROOT / "docs/mcp.md",                 # MCP deployment docs + env reference
    "server.json": ROOT / "server.json",                 # the registry manifest (example config)
    "mcp_server.py": ROOT / "src/veracium/mcp_server.py",  # build_server API docs + --help text
    "CHANGELOG.md": ROOT / "CHANGELOG.md",
}

# the facts, as canonical fragments every surface must carry
# `\s+` between words: a line-wrap in a docstring or a Markdown cell is not a
# divergence; a changed WORD is.
FACTS = {
    "the variable":        "VERACIUM_MCP_CAPABILITY",
    "the default":         re.compile(r"[Uu]nset[^.|]{0,40}(=|means|is)[^.|]{0,10}`?none`?"),
    "attested-not-verified": re.compile(r"[Aa]ttested\s+by\s+the\s+host,?\s+(and\s+)?(NOT|not)\s+verified"),
    "the public-agent rule": re.compile(r"public\s+or\s+untrusted\s+agent\s+must\s+leave\s+it\s+unset"),
    "direct's definition": re.compile(r"stands?\s+behind\s+the\s+model'?s\s+authorship\s+labell?ing\s+as\s+its\s+own"),
}


def test_every_surface_carries_every_fact():
    missing = []
    for name, path in SURFACES.items():
        text = path.read_text()
        for fact, pat in FACTS.items():
            ok = (pat in text) if isinstance(pat, str) else bool(pat.search(text))
            if not ok:
                missing.append(f"{name}: {fact}")
    assert not missing, "documentation surfaces missing a Phase A fact:\n  " + "\n  ".join(missing)


def test_the_manifest_declares_the_variable_with_the_boundary():
    m = json.loads((ROOT / "server.json").read_text())
    envs = {e["name"]: e for s in m["packages"] for e in s.get("environmentVariables", [])} \
        if "packages" in m else {}
    if not envs:  # tolerate a different top-level shape: find the list anywhere
        flat = json.dumps(m)
        assert "VERACIUM_MCP_CAPABILITY" in flat
        return
    v = envs["VERACIUM_MCP_CAPABILITY"]
    assert v["isRequired"] is False and v["isSecret"] is False
    assert "not verified" in v["description"]


def test_the_pinned_remember_signature_is_documented_without_user_id():
    """§4b-iii: the docs show the Phase A signature, and no surface still
    documents `user_id` as a `remember` argument."""
    doc = (ROOT / "docs/mcp.md").read_text()
    assert "`remember(text, author?, event_type?, date?, derived_from?)`" in doc
    for tool in ("remember", "recall", "answer", "maintain"):
        assert not re.search(tool + r"\([^)]*user_id", doc), tool


def test_the_fact_patterns_match_their_own_canonical_forms():
    """The checker's mutants: each pattern accepts the canonical sentence and
    refuses the paraphrase that would silently invert the boundary."""
    assert FACTS["attested-not-verified"].search("Attested by the host, not verified by veracium")
    assert not FACTS["attested-not-verified"].search("verified by the host")
    assert FACTS["the default"].search("Unset = `none`: events default")
    assert FACTS["the default"].search("unset means `none`")
    assert not FACTS["the default"].search("unset means `direct`")
    assert FACTS["direct's definition"].search("stands behind the model's authorship labelling as its own")
