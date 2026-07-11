"""Tolerant JSON extraction.

BYO `Complete` callables may return JSON wrapped in prose or code fences even when
asked for raw JSON. `raw_decode` parses a complete value from a start position and
ignores trailing text, so prose after (or around) the JSON can't corrupt the parse
— the fix the research arrived at after fenced/appended-prose broke naive parsing.
"""

from __future__ import annotations

import json


def extract_json(text: str):
    decoder = json.JSONDecoder()
    for i in sorted(j for j, ch in enumerate(text) if ch in "{["):
        try:
            obj, _ = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError(f"no parseable JSON in: {text[:200]!r}")
