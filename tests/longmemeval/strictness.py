"""Extraction-strictness experiment (over-extraction hypothesis).

The pilot writes **3.50 facts per turn** — 1,747 facts from 500 turns of
largely conversational material — and characterising the cached extractions
showed why that number is suspicious:

  * **35.6% of triples use a relation outside the registry**, across **7,210
    invented relation names**;
  * one relation, `prefers`, accounts for **33.5%** of everything;
  * **96.8%** of triples are marked `durable`, so volatility discriminates
    nothing.

That is the shape of an extractor promoting conversational detail to durable
facts. If so, the density problem is write-side: we manufacture the haystack we
then fail to search.

This wraps the provider and filters its *already-cached* output before veracium
parses it, so a strictness setting can be tested end to end with **no new LLM
calls** — the experiment is a replay, not a re-extraction. Deliberately not a
core change: we measure first, and only then decide what (if anything) belongs
in `ingest`.

Bars:
  none              baseline
  registry          drop triples whose relation is not in the configured registry
  registry+len      also drop essay-length objects (a fact should not be a paragraph)
"""

from __future__ import annotations

import json

from veracium.schema import DEFAULT_RELATIONS

MAX_OBJECT_CHARS = 120          # p90 of observed objects is 81; 989 is the max


class StrictExtraction:
    """Provider wrapper that applies an extraction bar to distill output."""

    def __init__(self, inner, *, bar: str = "none", relations=None):
        self.inner = inner
        self.bar = bar
        self.relations = set(relations or DEFAULT_RELATIONS)
        self.stats = {"triples_in": 0, "triples_out": 0,
                      "dropped_off_registry": 0, "dropped_long_object": 0,
                      "responses_filtered": 0}

    # provider identity passthrough, so the run record still describes the model
    @property
    def model(self):
        return getattr(self.inner, "model", type(self.inner).__name__)

    @property
    def decoding(self):
        return getattr(self.inner, "decoding", {})

    @property
    def throughput(self):
        return getattr(self.inner, "throughput", {})

    def cost_usd(self):
        return getattr(self.inner, "cost_usd", lambda: {})()

    def bind(self, *a, **kw):        # CachedComplete passthrough
        return self.inner.bind(*a, **kw)

    def key_for(self, *a, **kw):
        return self.inner.key_for(*a, **kw)

    def parts_for(self, *a, **kw):
        return self.inner.parts_for(*a, **kw)

    @property
    def unique_keys(self):
        return getattr(self.inner, "unique_keys", 0)

    def _keep(self, t: dict) -> bool:
        if not isinstance(t, dict):
            return False
        rel = str(t.get("relation", "")).strip()
        if self.bar in ("registry", "registry+len") and rel not in self.relations:
            self.stats["dropped_off_registry"] += 1
            return False
        if self.bar == "registry+len" and len(str(t.get("object", ""))) > MAX_OBJECT_CHARS:
            self.stats["dropped_long_object"] += 1
            return False
        return True

    def __call__(self, prompt, *, system=None, role="compile", json_schema=None):
        out = self.inner(prompt, system=system, role=role, json_schema=json_schema)
        if self.bar == "none" or role != "distill":
            return out
        try:
            data = json.loads(out)
            tri = data.get("triples")
            if not isinstance(tri, list):
                return out
        except Exception:
            return out          # unparseable output is veracium's problem, not ours
        self.stats["triples_in"] += len(tri)
        kept = [t for t in tri if self._keep(t)]
        self.stats["triples_out"] += len(kept)
        if len(kept) != len(tri):
            self.stats["responses_filtered"] += 1
        data["triples"] = kept
        return json.dumps(data)
