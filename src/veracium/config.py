"""Configuration for a `Memory` instance. See `docs/api.md` for the field table."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .schema import DEFAULT_RELATIONS, Relation, Volatility


def _default_lifetimes() -> dict[Volatility, Optional[int]]:
    """Expected lifetime in days per volatility class (None = never expires)."""
    return {Volatility.PERMANENT: None, Volatility.DURABLE: 730,
            Volatility.SLOW: 120, Volatility.TRANSIENT: 7, Volatility.EPHEMERAL: 1}


@dataclass
class MemoryConfig:
    db_path: str = "veracium.db"
    relations: dict[str, Relation] = field(default_factory=lambda: dict(DEFAULT_RELATIONS))
    # recall assembly (these caps bound read cost as history grows — finding 22)
    max_subgraph_edges: int = 40
    # Fraction of the subgraph budget reserved for time coverage when the store
    # is larger than the budget. Pure top-k has no coverage term, so facts that
    # share vocabulary can collapse the selection onto one period.
    # DEFAULT 0.0 (off): the mechanism is implemented and tested, but the
    # measurement that motivated it was retracted — the benchmark sample it was
    # diagnosed from turned out to be unrepresentative on exactly the dimension
    # involved, so coverage has never been tested on data that could exercise
    # it. Set >0 to enable; it will become the default if and when a balanced
    # measurement supports it.
    subgraph_coverage_share: float = 0.0
    max_recent_episodes: int = 12
    # proactive recall (recall with no query): how far ahead a dated commitment
    # counts as "coming due", and how far back "recent history" reaches.
    proactive_deadline_window_days: int = 7
    proactive_recent_days: int = 7
    # compiled-wiki cache: recompile when this many writes have landed since the
    # last compile (0 disables the wiki layer → recall renders the subgraph only).
    wiki_recompile_after_writes: int = 8
    # lifecycle (findings 9/11/19) — applied by mem.maintain()
    volatility_lifetime_days: dict[Volatility, Optional[int]] = field(default_factory=_default_lifetimes)
    decay_factor: float = 0.5          # confidence multiplier when a DECAY fact expires
    confidence_floor: float = 0.3      # below this, a decayed fact is invalidated
    consolidate_after_days: int = 30   # episodes older than this are consolidation candidates
    consolidate_min_batch: int = 8     # don't consolidate fewer than this many cold episodes
    # specs/0012 I10 — hard budgets on the RENDERED, MODEL-FACING text (estimated tokens,
    # chars/4). Floor-validated below AND at every surface build; below-floor is a loud
    # ValueError, never a silent clamp.
    query_context_budget_tokens: int = 4000    # query recall's DEFAULT context bound
    wiki_input_budget_tokens: int = 8000       # the compiler INPUT (facts + episodes)
    proactive_default_budget_tokens: int = 1200
    item_cap_tokens: int = 512                 # per rendered item, framing PLUS content
    wiki_variant_cap: int = 4                  # per-group variant lines feeding the compiler
    contested_members_per_line: int = 6        # the §4c packing K (validated >= 2)
    wiki_render_share: float = 1 / 3           # recall-time clamp of the cached wiki body
    group_heading_allowance_tokens: int = 48   # sub-cap for a heading's clamped fields
    # specs/0020 §4a-ii — THE SCOPE POLICY, host-supplied and per-process (the
    # relations-registry precedent). READ-SIDE ONLY: it governs visibility and
    # assertability at recall and NEVER governs maintenance (0021 partitions on
    # identity alone), so two hosts with different policies can differ only in
    # what they SHOW, never in what the store merges.
    #   `scope_groups is None`  → the feature is DISABLED: recall is exactly
    #     today's, and a principal-bearing call REFUSES (R2-2 — never a silent
    #     degrade to an unscoped, fully-assertable view).
    #   `scope_groups == {}`    → CONFIGURED-EMPTY, a valid state: the principal
    #     is ungrouped (own identity is OWN, the host pool is SHARED, every other
    #     identified record is CROSS).
    # Members are `veracium.scope.Identity` values; a malformed policy raises HERE,
    # at config load, never mid-recall (§7).
    scope_groups: Optional[dict] = None
    cross_scope_visible: bool = False

    def __post_init__(self):
        from .budgets import MIN_ITEM_ALLOWANCE, validate_budget
        validate_budget("recall", self.query_context_budget_tokens,
                        self.group_heading_allowance_tokens)
        validate_budget("wiki", self.wiki_input_budget_tokens,
                        self.group_heading_allowance_tokens)
        validate_budget("proactive", self.proactive_default_budget_tokens,
                        self.group_heading_allowance_tokens)
        if self.item_cap_tokens < MIN_ITEM_ALLOWANCE:
            raise ValueError(
                f"item_cap_tokens {self.item_cap_tokens} is below the minimum item "
                f"allowance {MIN_ITEM_ALLOWANCE} — one framed clamped item must fit")
        if self.contested_members_per_line < 2:
            raise ValueError(
                f"contested_members_per_line {self.contested_members_per_line} < 2: the "
                f"packing must be able to render BOTH mandatory members (the highest-"
                f"effective-authority member and the grounded prior) when they do not "
                f"alias (specs/0012 §4c)")
        if self.wiki_variant_cap < 1:
            raise ValueError("wiki_variant_cap must be >= 1")
        if not (0 < self.wiki_render_share <= 1):
            raise ValueError("wiki_render_share must be in (0, 1]")
        from .budgets import MARKER_RESERVE
        if int(self.query_context_budget_tokens * self.wiki_render_share) < \
                MIN_ITEM_ALLOWANCE + MARKER_RESERVE:
            raise ValueError(
                f"wiki_render_share {self.wiki_render_share} of the query context budget "
                f"{self.query_context_budget_tokens} leaves "
                f"{int(self.query_context_budget_tokens * self.wiki_render_share)} tokens "
                f"for the wiki slot — below one clamped item + the marker reserve "
                f"({MIN_ITEM_ALLOWANCE + MARKER_RESERVE}); the share would render the "
                f"cached-wiki framing unable to carry any content")
        if self.group_heading_allowance_tokens < 16:
            raise ValueError("group_heading_allowance_tokens must be >= 16")
        self._validate_scope_policy()

    # -- specs/0020 §4a-ii: the policy is validated AT LOAD, never at recall --
    #: the local origin the LOAD-TIME shape check resolves absent origins
    #: against. The authoritative validation happens a second time in
    #: `Memory.__init__` against the STORE's real `local_origin()` (the value
    #: 0006 I9 resolves to), which is the only place digest OVERLAP between an
    #: absent-origin rule and an explicit-origin rule can be judged. This
    #: sentinel can never collide with a real one: `origin` is store-MINTED and
    #: never host-set (0006 I2a).
    _SHAPE_CHECK_ORIGIN = "scope-policy-load-shape-check"

    def _validate_scope_policy(self) -> None:
        if not isinstance(self.cross_scope_visible, bool):
            raise ValueError(
                f"cross_scope_visible must be a real bool, got "
                f"{self.cross_scope_visible!r} (specs/0020 §4a-ii)")
        if self.scope_groups is None:
            if self.cross_scope_visible:
                raise ValueError(
                    "cross_scope_visible=True with scope_groups=None is a policy "
                    "setting with no policy — the feature is DISABLED without "
                    "scope_groups. Set scope_groups={} for the configured-empty "
                    "state (specs/0020 §4a-ii)")
            return
        from .scope import validate_policy      # the §4a-ii validator, verbatim
        validate_policy(self.scope_groups, self.cross_scope_visible,
                        local_origin=self._SHAPE_CHECK_ORIGIN)
