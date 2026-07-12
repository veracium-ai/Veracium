"""Tolerant JSON extraction.

BYO `Complete` callables may return JSON wrapped in prose or code fences even when
asked for raw JSON. `raw_decode` parses a complete value from a start position and
ignores trailing text, so prose after (or around) the JSON can't corrupt the parse
— the fix the research arrived at after fenced/appended-prose broke naive parsing.
"""

from __future__ import annotations

import json


def extract_json(text: str):
    """Return the first JSON object in `text`, preferring dicts: every veracium
    prompt asks for an object, so a list that parses first is either prose debris
    (`[]` in a code sample before the real object — keep scanning past it) or the
    payload with its wrapper omitted (a bare triples array — returned as a
    fallback for the caller to normalize). Scanning never descends into a parsed
    list, so a dict *inside* the fallback list is not mistaken for the payload."""
    decoder = json.JSONDecoder()
    fallback = None
    skip_until = -1
    for i in sorted(j for j, ch in enumerate(text) if ch in "{["):
        if i < skip_until:
            continue
        try:
            obj, end = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
        if fallback is None:
            fallback = obj
        skip_until = i + end
    if fallback is not None:
        return fallback
    raise ValueError(f"no parseable JSON in: {text[:200]!r}")
