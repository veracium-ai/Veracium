"""The structured record of every specs/0002 finding. THE source of truth.

Five external reviews deferred this spec, and every one found a status claim
contradicting another status claim in the same document: a header saying five
findings were closed beside a ledger showing four unimplemented; "three rows are
red" over a four-row table; "three external reviews" in a document containing
four; a release marked unreleased that had shipped twice over.

Each was corrected by hand and the next one appeared, because every summary was
maintained independently of the thing it summarised. Adding a phrase lint made
that a better hand-check, not a different mechanism -- it passed while
"M1-M5, all closed" sat in the header.

So the prose is now DERIVED. `render_status.py --write` regenerates every
summary from this file; `--check` fails when they drift. Nothing below is
restated anywhere by hand.

  disposition     what the review process decided
  implementation  whether the CODE is fixed -- deliberately separate, because
                  "closed" silently meant both and that was finding #1 of the
                  second review
  owner           the spec that owns the fix; `0002` means this one
"""

# disposition: resolved | open
# implementation: shipped | committed | none | n/a
#
#   shipped    in a released version -- users have it
#   committed  on main and unreleased -- users DO NOT have it. Added after the
#              v7 package shipped a ledger saying `none` for two fixes made in
#              the same session: there was no state between "not done" and "in
#              a release", so a real fix had to be recorded as neither.
FINDINGS = [
    dict(id="M1", title="consolidation derived provenance from `cold[0]`",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.4", advisory="GHSA-hcj3-8jqc-wqrp",
         test="test_consolidation_preserves_and_compresses",
         released_defect="provenance inherited from the first cold episode",
         current_defect=None),
    dict(id="M2", title="`confirm()` mutated `valid_from`",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.5", advisory=None,
         test="test_confirm_advances_liveness_not_first_known",
         released_defect="confirmation moved a fact's first-known date",
         current_defect=None),
    dict(id="M2′", title="`confirm()` returned a `valid_from` it never set; future dates accepted",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.6", advisory=None,
         test="test_confirm_returns_the_real_valid_from_not_the_confirmation_date",
         released_defect="the return contract carried the caller's date; a future date was unrecoverable",
         current_defect=None),
    dict(id="M2″", title="offset-bearing dates relabelled UTC instead of converted",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.7", advisory=None,
         test="test_an_offset_bearing_timestamp_is_converted_not_relabelled",
         released_defect="`.replace(tzinfo=utc)` discarded the offset — 12h of skew bypass measured",
         current_defect=None),
    dict(id="M2‴", title="malformed dates silently became *now*",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.7", advisory=None,
         test="test_a_malformed_event_date_is_rejected_not_silently_now",
         released_defect="an invented observation time the caller never supplied",
         current_defect=None),
    dict(id="M3", title="staleness cleared on same-author-class evidence",
         owner="0008", disposition="resolved", implementation="shipped",
         release="0.5.0", advisory=None,
         test="test_no_provenance_value_clears_staleness · test_same_author_restatement_does_not_clear_staleness",
         released_defect="0.4.5 closed cross-class clearing and left same-class open",
         current_defect=None),
    dict(id="M4", title="`record_outcome` overwrites authorship",
         owner="0009", disposition="resolved", implementation="shipped",
         release="0.5.0", advisory=None, test="0009 H1 test_outcome_authorship_is_never_overwritten",
         released_defect="0.4.5 appends a note to a summary rebuilt on every upgrade",
         current_defect=None),
    dict(id="M5", title="merge-time `confidence = max(...)`",
         owner="0002", disposition="resolved", implementation="n/a",
         release=None, advisory=None, test="constrains the unwritten T2 design",
         released_defect="T1 retains `max`, which is earned",
         current_defect=None),
    dict(id="M9", title="reinforcement transfers `observed_at`/`confidence` unattributed",
         owner="0012", disposition="resolved", implementation="shipped",
         release="0.7.0", advisory=None,
         test="test_reinforcement_attributes_the_contributing_source",
         released_defect="the reinforcement branch (`graph.py`) never persists the incoming edge; the prior absorbs `max(observed_at)`/`max(confidence)` and returns, leaving no record the contributing source existed",
         current_defect=None),
         # M9 history: REPOINTED 0002→0012 (2026-08-08) — research ruled 0012
         # Design 1 (reinforcement PERSISTS the incoming edge with its own
         # provenance, transfers nothing); the persisted edge IS the attribution,
         # closing M9 and 0014 §3.1. 0012 implemented 2026-08-10 (Slice A flipped
         # the two M9 xfails to passing), impl-review accepted, RELEASED in
         # v0.7.0 (2026-08-11). Ledger row updated 2026-08-13 with the named
         # test re-run green.
    dict(id="N9b-floor", title="consolidation manufactured confidence, disclosure and currency",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.7", advisory=None,
         test="test_consolidation_output_is_no_stronger_than_its_weakest_input",
         released_defect="`confidence = 0.9` flat; disclosure inherited from `cold[0]`",
         current_defect=None),
    dict(id="N9b-lineage", title="consolidation retains no record of the absorbed set",
         owner="0010", disposition="resolved", implementation="shipped",
         release="0.5.0", advisory=None, test="0010 X6, X8 test_lineage_is_the_whole_batch",
         released_defect="inputs deleted, no lineage",
         current_defect=None),
    dict(id="N4-decay", title="`MemoryConfig` bounds are unvalidated, and declared field bounds are not enforced on assignment",
         owner="0002", disposition="open", implementation="none",
         release=None, advisory=None, test="0002 N4b–N4d",
         released_defect="`decay_factor=2.0`, `NaN`, `-1.0` all accepted; `validate_assignment` is False",
         current_defect="`expire()` can RAISE confidence, which makes N4 false as written"),
    dict(id="N9t-transfer", title="`transfer` may raise trust and claim new currency",
         owner="0005", disposition="resolved", implementation="committed",
         release=None, advisory=None, test="test_default_import_caps_every_record + test_import_never_mutates_existing_rows",
         released_defect="`import_memory` persists every claimed trust field verbatim",
         current_defect="closed by the 0005 implementation: the three-lever cap floors trust (P1/P4/P6) and import mutates no existing row, so no currency can be renewed (P8/§4e)"),
    dict(id="N9b-provenance", title="consolidation inherits `source_type` and `evidence_ref` from `cold[0]`",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.8", advisory=None, test="test_consolidated_provenance_is_internally_consistent",
         released_defect="a SYSTEM summary reports `source_type=stated` and the first input's `evidence_ref`",
         current_defect="internally false provenance — M1's `cold[0]` inheritance surviving on two unexamined fields"),
    dict(id="M2⁗", title="offset timestamps fail through `remember()`",
         owner="0002", disposition="resolved", implementation="shipped",
         release="0.4.8", advisory=None, test="test_an_offset_timestamp_survives_every_public_entry_point",
         released_defect="`prompts.date_context` parses the raw string and rejects offsets",
         current_defect="one input, two parsers — `_event_dt` is not the single contract §7f claims"),
    dict(id="M7-correct", title="`correct()` bypasses the supersession ladder",
         owner="0011", disposition="open", implementation="none",
         release=None, advisory=None, test="0011 E5",
         released_defect="`correct()` writes a replacement with hardcoded `author=USER`",
         current_defect="it is the only `supersedes=` writer and never calls `apply_supersession`"),
         # M7-correct re-owned 0003→0011 (2026-08-13): accepted 0003 §1b rules
         # correct() OUT of scope and names the fix — one authorised replacement
         # operation — as 0011 E5; the 0.6.0 CHANGELOG says the same. The old
         # test pointer "0003 I9, I10" was pre-split numbering (accepted 0003's
         # I9 is PlanStale). Verified still open in code: __init__.correct()
         # calls store.invalidate_edge + writes supersedes= directly.
    dict(id="M8-wiki", title="the wiki serves a revoked trust decision",
         owner="0004", disposition="open", implementation="none",
         release=None, advisory=None, test="0004 W1–W4",
         released_defect="a cached wiki outlives the revocation of its inputs",
         current_defect="no wiki drop on a trust-reducing invalidation"),
    dict(id="M6-import", title="`import_memory` has no trust boundary",
         owner="0005", disposition="resolved", implementation="committed",
         release=None, advisory=None, test="tests/test_0005_import_boundary.py (P1–P16)",
         released_defect="`--user` remap re-homes another principal's records verbatim",
         current_defect="closed by the 0005 implementation: the unconditional three-lever cap (nothing keys on the header — I-Q1); restore is the operator's explicit opt-out"),
    dict(id="X-crash", title="consolidation deletes every input before writing any output",
         owner="0010", disposition="resolved", implementation="shipped",
         release="0.5.0", advisory=None, test="0010 X1–X9 test_no_crash_point_loses_data",
         released_defect="delete-all-then-write; a crash loses the batch",
         current_defect=None),
]

# Review rounds live in specs/reviews.py -- ONE source across all specs. They
# were here (0002 only) and in a hand-written table in 0003, and this copy
# stopped at v5 while a sixth disposition sat in the document.
