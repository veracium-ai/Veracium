"""The curated view (finding 20): an LLM cartographer compiles a budgeted "wiki"
from the store, cached and recompiled after N writes.

Security-critical design (finding 23-C — the injection surface is the episode,
not the wiki): the compiler is fed ONLY grounded, user/system-authored material.
Third-party claims and third-party-authored episodes are never compiled into the
assertable body; they surface only through recall's unverified channel, where the
abstention gate governs them. This is why excluding claims from the wiki *text*
alone was insufficient in the research — the claim re-entered via its episode. Here
the episode itself is withheld from the grounded compile.
"""

from __future__ import annotations

from typing import Optional

from .graph import render_edges
from .llm.base import Complete
from .schema import EvidenceAuthor

COMPILE_SYSTEM = (
    "You are the memory curator for an AI assistant. You compile a compact, "
    "accurate memory document from a user's known facts and interaction history. "
    "You never invent; you keep names, dates, and numbers exact; you merge "
    "duplicates and keep one current value per changing fact with brief inline "
    "history."
)

COMPILE_PROMPT = """Compile the material below into ONE curated memory document,
<= {budget} tokens, with these sections (omit a section if empty):

## USER MODEL
## CURRENT STATE
## WORK & PROJECT KNOWLEDGE
## NOTABLE EVENTS

GROUNDED FACTS (verified — user-stated or system-observed):
{facts}

INTERACTION HISTORY (user's own interactions):
{episodes}

Rules:
- Merge duplicates; one line per fact. Keep names/dates/numbers EXACT.
- For a changed fact, give the current value with brief inline history:
  "X (since <date>; previously Y)".
- NOTABLE EVENTS: keep recent events as dated one-liners; compress older periods,
  but ALWAYS keep first occurrences of failures, their fixes, and dated commitments.
- Output only the document. No preamble, no commentary."""


def _grounded_inputs(store, user_id: str):
    """Claims never feed the compile: active non-quarantined edges and episodes
    NOT authored by a third party. Third-party *inferences* (use_only) do pass —
    they legitimately shape behavior — but render_edges tags them
    '[third-party-reported; unconfirmed]', so the wiki carries the caveat."""
    edges = store.edges(user_id, active_only=True, include_quarantined=False)
    episodes = [e for e in store.episodes(user_id)
                if e.provenance.author_of_evidence != EvidenceAuthor.THIRD_PARTY]
    return edges, episodes


def needs_recompile(store, user_id: str, recompile_after: int) -> bool:
    cached = store.get_wiki(user_id)
    if cached is None:
        return True
    _, version_at_compile = cached
    return store.store_version(user_id) - version_at_compile >= recompile_after


def compile_wiki(store, llm: Complete, user_id: str, *, budget_tokens: int = 900) -> str:
    edges, episodes = _grounded_inputs(store, user_id)
    facts = render_edges(edges) or "(none)"
    hist = "\n".join(f"[{e.date}] {e.summary}" for e in episodes) or "(none)"
    wiki = llm(COMPILE_PROMPT.format(budget=budget_tokens, facts=facts, episodes=hist),
               system=COMPILE_SYSTEM, role="compile").strip()
    store.set_wiki(user_id, wiki, store.store_version(user_id))
    return wiki


def ensure_wiki(store, llm: Complete, user_id: str, recompile_after: int) -> Optional[str]:
    """Return the current wiki, recompiling if stale. None disables the wiki layer."""
    if recompile_after <= 0:
        return None
    if needs_recompile(store, user_id, recompile_after):
        return compile_wiki(store, llm, user_id)
    return store.get_wiki(user_id)[0]
