#!/usr/bin/env python3
"""The C-plus COLLECTED.txt renderer — COLLECTED_HEADER_DESIGN.md §5.1.5/6.

Blocking 2: verifying parts separately leaves the next finding living
BETWEEN two verified artifacts — undeclared bytes between blocks, a
duplicated block, trailing prose, a header at the wrong boundary. So the
unit here is the WHOLE FILE:

    COLLECTED.txt == render_header(record, template) + skip-inventory block

byte-for-byte: header anchored at byte zero, exactly one inventory block
immediately following it, EOF immediately after the permitted final
newline. No bytes exist that no check owns.

Ruling 3: the static prose lives in the TEMPLATE (data, reviewable),
substituted by this module under the record schema — not inside the
sealing code. The token set is CLOSED both ways: a template token the
registry does not name refuses, a registry header-field whose token the
template lacks refuses, and a field VALUE that itself carries a token
refuses (substitution injection).
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from collected_record import FIELD_POLICY  # noqa: E402

TOKEN_RE = re.compile(r"__[A-Z][A-Z_]*__")


class RenderError(ValueError):
    """A template/record pairing this module refuses to render."""


def token_of(field: str) -> str:
    return f"__{field.upper()}__"


def render_header(record: dict, template_text: str) -> str:
    """The header, entirely from the record and the template — closed."""
    fields = record["fields"]
    present = set(TOKEN_RE.findall(template_text))
    known = {token_of(f) for f in FIELD_POLICY}
    required = {token_of(f) for f, pol in FIELD_POLICY.items()
                if pol.in_header}
    unknown = sorted(present - known)
    if unknown:
        raise RenderError(f"the template carries tokens the registry does "
                          f"not name: {unknown} — the token set is closed")
    missing = sorted(required - present)
    if missing:
        raise RenderError(f"the template lacks required header tokens: "
                          f"{missing} — a field with nowhere to render is a "
                          f"claim nobody reads")
    out = template_text
    for name in FIELD_POLICY:
        tok = token_of(name)
        if tok not in out:
            continue
        value = fields[name]["value"]
        if TOKEN_RE.search(value):
            raise RenderError(f"{name}'s value itself carries a token — "
                              f"substitution injection refused")
        out = out.replace(tok, value)
    residue = sorted(set(TOKEN_RE.findall(out)))
    if residue:
        raise RenderError(f"unsubstituted tokens survive rendering: "
                          f"{residue}")
    return out


def render_manifest(record: dict, manifest_template: str) -> str:
    """PACKAGE_MANIFEST.txt from the same record — unknown tokens refused,
    no residue. The manifest is outside the whole-file equation (it is not
    COLLECTED.txt) but its values come from the one record, so the two
    carriers cannot be filled from different variables again (R16-1)."""
    fields = record["fields"]
    unknown = sorted(set(TOKEN_RE.findall(manifest_template))
                     - {token_of(f) for f in FIELD_POLICY})
    if unknown:
        raise RenderError(f"the manifest template carries unknown tokens: "
                          f"{unknown}")
    out = manifest_template
    for name in FIELD_POLICY:
        value = fields[name]["value"]
        if TOKEN_RE.search(value):
            raise RenderError(f"{name}'s value itself carries a token — "
                              f"substitution injection refused")
        out = out.replace(token_of(name), value)
    residue = sorted(set(TOKEN_RE.findall(out)))
    if residue:
        raise RenderError(f"unsubstituted manifest tokens survive: {residue}")
    return out


def manifest_problems(man_text: str, record: dict,
                      manifest_template: str) -> list:
    """The manifest's own whole-file equation (impl-review round 1, F2):
    PACKAGE_MANIFEST.txt == render_manifest(record, template), byte-for-byte.
    The partial witness parsed two lines and left every other byte unowned —
    forged trailing claims and hand-maintained dynamic prose both rode along.
    Same rule as COLLECTED.txt: no bytes exist that no check owns."""
    try:
        expected = render_manifest(record, manifest_template)
    except (RenderError, KeyError, TypeError) as e:
        return [f"the manifest construction itself refuses: {e}"]
    if man_text != expected:
        i = next((k for k, (a, b) in enumerate(zip(man_text, expected))
                  if a != b), min(len(man_text), len(expected)))
        return [f"PACKAGE_MANIFEST.txt is not the recomputed construction — "
                f"first divergence at byte {i} (have {man_text[i:i + 40]!r}, "
                f"expected {expected[i:i + 40]!r}) (F2)"]
    return []


def compose(record: dict, template_text: str, rs_text: str) -> str:
    """The whole file, built the one way it may exist."""
    import skip_inventory as S
    return (render_header(record, template_text)
            + S.BEGIN_MARKER + "\n" + S.render(rs_text) + "\n"
            + S.END_MARKER + "\n")


def whole_file_problems(col_text: str, record: dict, template_text: str,
                        rs_text: str) -> list:
    """The whole-file equation (blocking 2). Byte equality against the
    recomputed construction is the complete gate; the named checks after it
    exist to say WHERE a failing file went wrong."""
    import skip_inventory as S
    try:
        expected = compose(record, template_text, rs_text)
    except (RenderError, KeyError, TypeError) as e:
        return [f"the construction itself refuses: {e}"]
    problems = []
    if col_text != expected:
        i = next((k for k, (a, b) in enumerate(zip(col_text, expected))
                  if a != b), min(len(col_text), len(expected)))
        problems.append(
            f"COLLECTED.txt is not the recomputed construction — first "
            f"divergence at byte {i} (have {col_text[i:i + 40]!r}, expected "
            f"{expected[i:i + 40]!r})")
        # diagnosis, each a seam the review named:
        header = expected[:expected.index(S.BEGIN_MARKER)]
        if not col_text.startswith(header):
            problems.append("the header is not anchored at byte zero")
        n = col_text.count(S.BEGIN_MARKER)
        if n != 1:
            problems.append(f"{n} inventory blocks, expected exactly one")
        if col_text.count(S.END_MARKER) >= 1 \
                and not col_text.endswith(S.END_MARKER + "\n"):
            problems.append("bytes exist after the permitted final newline — "
                            "EOF must follow it immediately")
    return problems
