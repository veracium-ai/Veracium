"""Every review round, across every spec. One source.

Review counts were previously stated in three places -- `findings.py REVIEWS`
(0002 only, and it stopped at v5 while a sixth disposition sat in the document),
a hand-written table in 0003, and prose in both. The seventh review of 0002
caught the first; the second review of 0003 caught the others.

`kind` distinguishes who reviewed:
  internal  another session (research / workflow-platform) -- never the author
  external  the trusted third-party reviewer

`findings` is the count RAISED by that round, not the count outstanding.
"""

REVIEWS = [
    # --- 0001 -------------------------------------------------------------
    dict(spec="0001", round=1, kind="internal", date="2026-07-31", verdict="revise", findings=None),
    dict(spec="0001", round=1, kind="external", date="2026-07-31", verdict="deferred", findings=None),
    dict(spec="0001", round=2, kind="external", date="2026-08-01", verdict="deferred", findings=None),

    # --- 0002 -------------------------------------------------------------
    dict(spec="0002", round=1, kind="internal", date="2026-07-31", verdict="revise", findings=None),
    dict(spec="0002", round=2, kind="internal", date="2026-08-01", verdict="revise", findings=None),
    dict(spec="0002", round=1, kind="external", date="2026-08-01", verdict="deferred", findings=9),
    dict(spec="0002", round=2, kind="external", date="2026-08-01", verdict="deferred", findings=10),
    dict(spec="0002", round=3, kind="external", date="2026-08-01", verdict="deferred", findings=7),
    dict(spec="0002", round=4, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0002", round=5, kind="external", date="2026-08-02", verdict="deferred", findings=11),
    dict(spec="0002", round=6, kind="external", date="2026-08-02", verdict="deferred", findings=10),
    dict(spec="0002", round=7, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0002", round=8, kind="external", date="2026-08-02", verdict="deferred", findings=11),

    # --- 0008 -------------------------------------------------------------
    dict(spec="0008", round=1, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred", findings=7),
    dict(spec="0008", round=2, kind="external", date="2026-08-02", verdict="clearing rule approved; liveness rule rejected", findings=11),
    dict(spec="0008", round=3, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred on the storage and API contract", findings=8),
    dict(spec="0008", round=4, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred on episode inputs, idempotency and 0007", findings=9),

    # --- 0009 (5 external rounds; per-round dispositions in the spec's Review-closure
    #          ledger §11–§15; accepted 2026-08-07 on a finite boundary. These entries
    #          restore the count STATUS.md was undercounting — findings=None because the
    #          per-round counts were recorded in the closure ledger, not here) ------------
    dict(spec="0009", round=1, kind="external", date="2026-08-07", verdict="append-only design approved; deferred (Review closure §11)", findings=None),
    dict(spec="0009", round=2, kind="external", date="2026-08-07", verdict="deferred (Review closure §12)", findings=None),
    dict(spec="0009", round=3, kind="external", date="2026-08-07", verdict="deferred (Review closure §13)", findings=None),
    dict(spec="0009", round=4, kind="external", date="2026-08-07", verdict="deferred (Review closure §14)", findings=None),
    dict(spec="0009", round=5, kind="external", date="2026-08-07", verdict="ACCEPTED on a finite boundary (Review closure §15)", findings=None),

    # --- 0010 (7 external rounds; per-round dispositions in the spec's Review-closure
    #          ledger §11–§17; accepted 2026-08-07 on a finite boundary) -----------------
    dict(spec="0010", round=1, kind="external", date="2026-08-07", verdict="crash-safe design approved; deferred (Review closure §11)", findings=None),
    dict(spec="0010", round=2, kind="external", date="2026-08-07", verdict="deferred (Review closure §12)", findings=None),
    dict(spec="0010", round=3, kind="external", date="2026-08-07", verdict="deferred (Review closure §13)", findings=None),
    dict(spec="0010", round=4, kind="external", date="2026-08-07", verdict="deferred (Review closure §14)", findings=None),
    dict(spec="0010", round=5, kind="external", date="2026-08-07", verdict="deferred (Review closure §15)", findings=None),
    dict(spec="0010", round=6, kind="external", date="2026-08-07", verdict="deferred (Review closure §16)", findings=None),
    dict(spec="0010", round=7, kind="external", date="2026-08-07", verdict="ACCEPTED on a finite boundary (Review closure §17)", findings=None),

    # --- 0012 -------------------------------------------------------------
    dict(spec="0012", round=1, kind="internal", date="2026-08-08", verdict="O-Q1/O-Q2/O-Q3 RULED (research) — Design 1: reinforcement transfers NOTHING (incl. confidence); expire() stays per-edge (invariant); render both. Design 3 rejected, Design 2 successor. Design 1 closes 0014 §3.1 + M9. No open question blocks the spec", findings=3),

    # --- 0007 -------------------------------------------------------------
    dict(spec="0007", round=1, kind="external", date="2026-08-02",
         verdict="design direction approved; deferred on the shape comparison", findings=12),
    dict(spec="0007", round=2, kind="external", date="2026-08-02",
         verdict="direction approved; deferred; S-Q4 answered — known-constructor equality", findings=10),
    dict(spec="0007", round=3, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred on the manifest mechanics; S-Q5 resolved", findings=9),
    dict(spec="0007", round=4, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred for a truthful generator; S-Q6 resolved", findings=8),
    dict(spec="0007", round=5, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred; instrument split adopted", findings=8),
    dict(spec="0007", round=6, kind="external", date="2026-08-03",
         verdict="architecture approved; deferred; migration self-authorisation found", findings=8),
    dict(spec="0007", round=7, kind="external", date="2026-08-03",
         verdict="architecture approved; deferred; destination contract contradicted itself", findings=8),
    dict(spec="0007", round=8, kind="external", date="2026-08-03",
         verdict="scope cut approved; deferred; the cut broke 0008's prerequisite", findings=5),
    dict(spec="0007", round=9, kind="external", date="2026-08-03",
         verdict="narrowed design approved; deferred; fabrication and atomicity", findings=3),
    dict(spec="0007", round=10, kind="external", date="2026-08-03",
         verdict="core design approved; deferred; artifact conflicts and the unbuildable union", findings=3),
    dict(spec="0007", round=11, kind="external", date="2026-08-03",
         verdict="core spec approved; deferred; identity, attestation and a regressed guard", findings=3),
    dict(spec="0007", round=12, kind="external", date="2026-08-03",
         verdict="architecture approved outright; S-Q7 ruled; deferred on runtime-evidence validation", findings=3),
    dict(spec="0007", round=13, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred on monotonicity, totality and stale-record scoping", findings=3),
    dict(spec="0007", round=14, kind="external", date="2026-08-03",
         verdict="ACCEPTED — v16 approved for acceptance; three non-blocking corrections", findings=0),

    # --- 0013 -------------------------------------------------------------
    dict(spec="0013", round=1, kind="external", date="2026-08-03",
         verdict="architecture approved directionally; deferred; M-Q2 ruled adopt-with-conditions", findings=7),
    dict(spec="0013", round=2, kind="external", date="2026-08-03",
         verdict="concrete migration approved; deferred; integration, evidence, offline boundary", findings=4),
    dict(spec="0013", round=3, kind="external", date="2026-08-03",
         verdict="concrete v1→v2 approved directionally; deferred; one planner, prior evidence, qualified confinement, total outcomes; M-Q2 ruled at the library boundary", findings=4),
    dict(spec="0013", round=4, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred; evidence totality, artifact-wide cardinality, probe soundness, authority lifecycle", findings=5),
    dict(spec="0013", round=5, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred; monotone evidence writes, operation-level consumption, exact scalar typing, outermost boundary", findings=4),
    dict(spec="0013", round=6, kind="external", date="2026-08-03",
         verdict="approved architecture restated; deferred; migrate-only planner mode, serialized publication, Unicode-safe boundary, audit state machine, immutable release identity", findings=5),
    dict(spec="0013", round=7, kind="external", date="2026-08-03",
         verdict="mode, publication and boundary held; deferred; evidence snapshot binding, framed full-length identity, two-table audit machine, static source resolution, truthful internal-error", findings=5),
    dict(spec="0013", round=8, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; per-class TEMP qualification, enforced audit schema/atomicity, kernel terminal facts, fail-closed release identity, canonical timestamps; resolution/refusal split approved", findings=5),
    dict(spec="0013", round=9, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; atomic audit activation, complete+semantic audit schema, post-commit truth, TEMP vtable qualification, canonical generated_at, rolled-back cell", findings=5),
    dict(spec="0013", round=10, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; single-value audit state, exact per-cell terminal contract, post-commit representability, defect-vs-outage, total evidence validators", findings=5),
    dict(spec="0013", round=11, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; honest resulting_state, committed facts survive cleanup, named-escape terminalization, deeply-immutable audit state + event_id PK, validators total over nested malformed JSON; commit-ambiguity mapping", findings=5),
    dict(spec="0013", round=12, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; confirmed-rollback for source, absent-vs-unaccepted classification, distinct audit-state-unknown outcome, MigrationAuditWriteError carries resulting_state, validators total under recursive nested mutation; operation-row type validation + deep freeze, event_id grammar", findings=5),
    dict(spec="0013", round=13, kind="external", date="2026-08-04",
         verdict="architecture standing; deferred; tri-state commit/change facts, phase-classified post-commit cleanup, lstat-proven absence, per-outcome allowed-state map, one shared validated TerminalFacts; NUL-path rejection, stale-wording reconcile, narrowed rollback claim", findings=5),
    dict(spec="0013", round=14, kind="external", date="2026-08-05",
         verdict="architecture standing; deferred; complete-tuple TerminalFacts shared verbatim, committed-activation-loss terminalization, audit_committed on write error, read-site SQLite classification, package-inconsistent at every phase + re-raise; total problems(), write-error context validation, root-safe permission test", findings=5),
    dict(spec="0013", round=15, kind="external", date="2026-08-05",
         verdict="architecture standing; deferred; closed activation-result vocab, kernel-result validation + total terminal wrapper, hook SQLite -> migration-failed, read-rejected -> unaccepted, connection cleanup scope; preserve supplied commit status, adjacency + exact audit_committed typing, total payload validation, real after-rollback regression", findings=5),
    dict(spec="0013", round=16, kind="external", date="2026-08-05",
         verdict="architecture standing; deferred; verified ActivationReceipt/TerminalReceipt, mode-aware OpenResult validation, guarded sink metadata, check-to-open race classification; duplicate reconciliation, independent gate oracle + record-completeness sweep, UUID4 bit enforcement, MigrationRefused raise", findings=5),
    dict(spec="0013", round=17, kind="external", date="2026-08-05",
         verdict="architecture standing; deferred; verify content not existence — activation receipt binds authority row, terminal receipt binds requested payload, returned branch equals committed branch, validating on_committed, total terminal-derivation boundary; duplicate durable verification, total receipt validators, request-to-record gate invariants", findings=5),
    dict(spec="0013", round=18, kind="external", date="2026-08-05",
         verdict="architecture standing; deferred; verify the complete record — activation binds the complete attempted event, terminal write verifies the attempted->terminal transition + event_id integrity, on_committed distinguishes a proven commit from a no-commit position, total post-consumption boundary, derivation fallback changes the public outcome; recorded receipt must be audit_committed, duplicate binds the authority, complete-durable-state gate, operation-id UUID4 wording reconciled", findings=5),
    dict(spec="0013", round=19, kind="external", date="2026-08-05",
         verdict="M-Q4 RULED — finite acceptance boundary frozen (§8a: six gated properties; ten 0008 production obligations); architecture standing; v22 deferred on two semantic gaps + four reference-scope corrections — audit_committed follows durable proof not a contradictory receipt, a validated no-op-current destination position survives a later defect; terminalization verifies row+attempted-event preserved, malformed duplicate lifecycle is audit-integrity error, activation readback checks the event_ids index + exact row field set, receipt validators total over str subclasses", findings=2),
    dict(spec="0013", round=20, kind="external", date="2026-08-05",
         verdict="M-Q4 boundary respected; architecture standing; v23 deferred on three semantic gaps + two corrections — all closed. Strongest durable evidence on every path: consumption follows the durable row not the carrier (an invalid receipt or contradictory committed=False after a durable activation is internal-error WITH a terminal event, never a false safe-retry); a terminal-sink exception cannot override a durably-observed commit; the terminal fallback preserves every established physical state (proven no-op destination / missing source), not only committed. TerminalFacts.problems() total over hostile str subclasses; duplicate receipt must be audit_committed=True", findings=3),
    dict(spec="0013", round=21, kind="external", date="2026-08-05",
         verdict="M-Q4 boundary respected; architecture standing; v24 deferred on three semantic gaps + two corrections — all closed. Strongest durable evidence + validator totality on EVERY carrier: durable readback precedes classifying every activation carrier (a wrong-type return or unrecognized exception after a durable activation is internal-error WITH a terminal event, never attempted-only); an adapter-supplied MigrationAuditWriteError is untrusted (wrapper re-derives audit_committed + owns the identity, adapter's exc only the cause); a typed committed=True with no transition degrades to None. Timestamp/token/digest/path validators total over hostile str subclasses; seam gate covers the new carrier combinations", findings=3),
    dict(spec="0013", round=22, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v25 deferred on three semantic gaps + two corrections — all closed. Exact-typing/completeness where a carrier or value had been trusted by shape: the complete durable lifecycle is classified before every activation carrier (an already-terminal op + committed=False is a consumed replay, not a false safe-retry); on_committed freezes a wrapper-owned immutable copy exact-typed (no live-object mutation, no OpenResult-subclass branch spoof); MigrationAuditWriteError requires an exact TerminalFacts + base validator + exact operation_id. Top-level authority validator exact-types before .strip()/regex; independent gate covers all five new cases", findings=3),
    dict(spec="0013", round=23, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v26 deferred on three semantic gaps + two corrections — all closed. on_committed protocol contract + exact authority carrier: a successful migrate result requires its mandatory on_committed publication (a kernel returning migrated without it is internal-error, store untouched); on_committed validates the mode-aware semantic cell before freezing via one shared validator (a migrated/(F,F) publication is a defect, not a destination position); the authority must be the EXACT MigrationAuthority type before any field access (a subclass could intercept access, pass validation, then raise after commit and strand the op attempted-only) and the initial terminal fallback moved inside the total boundary; independent gate covers the three new cases", findings=3),
    dict(spec="0013", round=24, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v27 deferred on three semantic gaps + two corrections — all closed. Callback cardinality + single freeze + total rescue: on_committed fires exactly once so any second publication (even value-identical) is a defect, not idempotent; the returned result is frozen exactly once and that immutable value drives validation/equality/state/branch/terminal-derivation (no re-read of the live label reopening a mutation window); the terminal rescue never re-runs a failed helper (_safe_fallback_facts degrades a fallback defect to a minimal valid value, so a fallback-helper failure after commit is a wrapper-owned write error, not a raw escape). _static_resolution_problems exact-types its carrier; independent gate covers the three new cases", findings=3),
    dict(spec="0013", round=25, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v28 deferred on three semantic gaps + two corrections — all closed. Already-proven facts survive a defect in the wrapper's OWN verification helpers (resting on M-Q4's allowance to trust a valid success receipt): a post-publication verifier defect preserves the durable terminal result (exact requested facts + audit_committed=True, not internal-error/None); the safe fallback reconstructs the strongest proven store state inline, independent of the derivation-helper family, so a proven commit is never erased to unknown; a valid activated receipt establishes provisional consumption so an activation-readback verifier defect still terminalizes (a clean rejection with no row stays not-consumed). _static_resolution_problems exact-types its digest fields; independent gate covers the three new verifier-defect seams", findings=3),
    dict(spec="0013", round=26, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v29 deferred on three semantic gaps + three corrections — all closed over the full matrix. The symmetry of a verifier defect: round 25 hardened the verifier-RAISES case, round 26 found the sibling cells where it returns a clean FALSE-negative. An activation-binding false-negative over an existing durable row after a valid activated receipt still consumes and terminalizes (not only when it raises); a terminal-transition false-negative on a valid receipt still reports audit_committed=True; a committed=True response-loss under a raising verifier is trusted while a cleanly-observed missing transition stays contradictory (None). _safe_fallback_facts computes its full truth table inline (adds False/False/unaccepted for read-then-rejected and False/False/unknown for known-unchanged). Corrections: §5d prose aligned to M106 (any second publication, even value-identical, is a defect); internal-error state set adds missing/unaccepted; independent gate covers the three new verifier-false-negative seams, each proven non-vacuous", findings=3),
    dict(spec="0013", round=27, kind="external", date="2026-08-06",
         verdict="M-Q4 boundary respected; architecture standing; v30 deferred on three semantic gaps + two corrections — all closed. Extends the verifier-defect symmetry to the committed=True response-loss carrier when the verifier cannot confirm, and hardens carrier trust to the exact protocol type. An exact AuditStorageUnavailable(committed=True) activation carrier is itself proof of the durable write (§5b): consumed → migration-quiescence-required + terminal event, whether the readback verifier raises OR false-negatives (v29 stranded it attempted-only or reported migration-audit-state-unknown); a subclass does not consume. The AUDIT-write commit fact checks the independent durable presence of a well-formed terminal event FIRST, so a verifier false-negative over a real lifecycle preserves audit_committed=True; a genuinely-absent transition stays contradictory (None). Only type(exc) is AuditStorageUnavailable contributes trusted commit metadata — a subclass cannot fabricate audit_committed=True with no durable write. Corrections: the round-26 'full matrix' claim narrowed to the carrier matrix actually gated; the independent gate adds the four missing carrier combinations, each proven non-vacuous. M112-M113", findings=3),
    dict(spec="0013", round=28, kind="external", date="2026-08-07",
         verdict="M-Q4 boundary respected; architecture standing; v31 deferred on three semantic gaps + two corrections — all closed at the ROOT. This round showed v30's own fixes were incomplete/unsound against FROZEN invariants, so v31 makes the rules total rather than special-casing a third time. Finding 1: a complete durable activation was left attempted-only for every nontrusted carrier (committed-false/none, raw exception, wrong-return, invalid-receipt) when _durable_row_binds_authority raised or false-negatived — reopening M90/M95. Consumption is now decided by the INDEPENDENT request-bound _durable_lifecycle classifier: a non-duplicate authority-bound attempted lifecycle is this call's fresh publication → consumed → internal-error WITH a terminal event, whatever the carrier or verifier health; genuine duplicate/absent lifecycles keep their distinctions. Finding 2: the outer post-consumption catch now consults request-bound durable evidence, so an exact transition + invalid return + raising verifier preserves migrated facts + audit_committed=True (M86/M108 not limited to a valid receipt). Finding 3: M113's proof was request-UNbound (used _terminal_event_wellformed, no payload compare) so a durable `current` event proved a `migrated` commit — now the request-bound primitive _requested_transition_durable (exact payload match, below the monkeypatchable verifier). Corrections: carrier-matrix claim narrowed until M90/M95/M86/M108/M112-M115 coexist; independent gate adds the missing carrier x verifier-mode cells, each proven non-vacuous; the committed=True failure carrier grounded in the §5e typed-failure contract. M114-M115; M113 corrected", findings=3),

    dict(spec="0013", round=29, kind="external", date="2026-08-07",
         verdict="M-Q4 boundary approved and applied as ruled; architecture standing. Findings 2 & 3 closed in v32; finding 1 deferred to 0008; 0013 set ACCEPTED on the finite §8a boundary. Round 29 confirmed the reviewer's next-adjacent-cell method has no natural terminal on an executable model (finding 1 was a sibling of v31's own root fix); per M-Q4 the acceptance criterion is the six §8a gated properties (all met), not the absence of further draft edge cells. F2 (closed): the complete durable lifecycle is classified before EVERY carrier including the committed=True fast path, so an existing terminal lifecycle is a consumed replay (migration-quiescence-required, no second terminal write), not a MigrationAuditWriteError (M116/M99). F3 (closed): the audit-commit fact is a truthful tri-state — a durable-but-request-mismatched terminal write that landed is audit_committed=None, never False; False is reserved for a total absence of any terminal write (M113 corrected). F1 (deferred to 0008): a prior attempted-only lifecycle needs invocation-provenance (an activation-attempt token bound into the row before the sink call) to distinguish this call's fresh publication from a prior/concurrent one — the multiprocess/reconciliation machinery M-Q4 assigned to the production sink; the in-process draft cannot bind the current invocation without racing another process, so it conservatively terminalizes. Corrections: narrowed the total/root wording (finding 1's provenance gap remains a 0008 obligation); gate adds the durable-mismatched-write + raw-exception cell. M116; M113 corrected. ACCEPTED (dev, PROCESS.md §4a) — authorises implementation of the design; code still blocked by Spec-Requires: 0007 (draft)", findings=3),

    # --- 0003 -------------------------------------------------------------
    dict(spec="0003", round=1, kind="internal", date="2026-08-01", verdict="adopted", findings=None),
    dict(spec="0003", round=1, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0003", round=2, kind="external", date="2026-08-02", verdict="deferred", findings=12),
    dict(spec="0003", round=3, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for cleanup", findings=5),
    dict(spec="0003", round=4, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for retrieval fix", findings=5),
    dict(spec="0003", round=5, kind="external", date="2026-08-02", verdict="narrow design approved; deferred — duplicated sections, ladder not runtime-grounded", findings=7),
    dict(spec="0003", round=6, kind="external", date="2026-08-08", verdict="direction re-approved; deferred — 3 design blockers (default-wiki path, schema-versioned refusal table, atomic supersession plan) + 4 corrections", findings=7),
    dict(spec="0003", round=7, kind="external", date="2026-08-08", verdict="direction re-approved; deferred — 3 found-in-fix gaps (wiki exclusion violates I6a, cache/migration/registry, reinforcement plan variant) + 3 corrections", findings=6),
    dict(spec="0003", round=8, kind="external", date="2026-08-08", verdict="direction re-approved; deferred — 3 found-in-fix gaps (contention surface vs grounded/unverified partition, budget/proactive contract, plan not CAS-linearized) + 3 corrections", findings=6),
    dict(spec="0003", round=9, kind="external", date="2026-08-08", verdict="finite-boundary concept approved in principle; deferred — 3 architectural seams (challenger reach, refusal-scoped derived-view invalidation, durable operation receipt) + 3 corrections (acceptance-artifact order, structured Recall carrier, expected_state completeness)", findings=6),
    dict(spec="0003", round=10, kind="external", date="2026-08-08", verdict="finite boundary approved; set accepted after this revision — deferred on 2 derived-view/cache gaps (resolution invalidation, cache binds relation registry) + 2 public-contract corrections (Recall.contested reach, §7a Recall API) + acceptance-ledger PROCESS §4a compliance", findings=5),
    dict(spec="0003", round=11, kind="external", date="2026-08-08", verdict="architecture APPROVED (end broad review here); set accepted after this revision — deferred on 2 contract/process-only corrections (same-partition grounded member must be a full exposed member in Recall.contested/edges; §11a made literally one-row-per-finding with an evidence-loss ruling for verdict-only rounds 3/4)", findings=2),
    dict(spec="0003", round=12, kind="external", date="2026-08-08", verdict="APPROVED FOR ACCEPTANCE; broad external architecture review closed — one same-commit deletion-pass correction (remove the stale round-9 'correct()/lifecycle need not invalidate' sentence, which contradicted the round-10 symmetric resolution rule) then set Spec-Status: accepted", findings=1),

    # --- 0006 -------------------------------------------------------------
    dict(spec="0006", round=1, kind="internal", date="2026-08-08", verdict="review-ready held for 3 dev fixes — F1 (§1 motivates a payoff §3 no longer delivers; name 0014 as the v1 consumer, mark the original three deferred), F2 (FORMAT_VERSION stale by one: 3→4, not 2→3), F3 (source_id opacity is a convention not a mechanism; add a §8 limit). Reviewer-safety CLEAN", findings=3),
    dict(spec="0006", round=1, kind="external", date="2026-08-08", verdict="RETURN FOR AMENDMENT (not rejection); 6 findings all verified, none rejected — R1 (pre-R3 negative-framing remnants in §3/I5), R2 (evidence_basis has 3 values not 2 and no v1 consumer → SPLIT OUT of v1), R3 (no-DDL SCHEMA_VERSION bump; 0006/0014 disagreed on next version), R4 (Q3 confirmed only in coordination not the spec), R5 (source_id has no namespace scope across import → identity is (origin, source_id)), R6 (Path: full but §3b/§5/§7 absent). v2 amends all six", findings=6),
    dict(spec="0006", round=2, kind="external", date="2026-08-08", verdict="RETURN FOR AMENDMENT; v2's (origin, source_id) design raised 5 — R7 (origin is collision-resistant namespacing NOT authenticated provenance: materialised into exports + 0005 imports untrusted → adversarial forgery possible; 'structurally impossible' claims too strong), R8 (no durable place for the local origin → add a persistent store_identity singleton; minimal DDL not no-DDL; no backfill), R9 (I2 and foreign-origin preservation contradict → split I2a local/I2b import), R10 (pre-v4-envelope carrying source_id must be stripped), R11 (package overstates 0014 maturity — it is a v2 stub; acceptance gated on 0014 mechanical completeness). v3 amends all five", findings=5),
    dict(spec="0006", round=3, kind="external", date="2026-08-09", verdict="INTERFACE-FREEZE reviewer half WITHHELD (5 of 7 frozen points + point-2 design confirmed); 4 raised — F1 (point 4 undefined when source_id absent: identity_digest must be NULLABLE, populated iff source_id present, never a (origin, NULL) pseudo-source), F2 (digest(pair) not mechanically frozen: freeze ONE canonical length-framed domain-separated construction as a single shared primitive), plus two cleanups (0006 §3b stale 'structurally incapable'/'cannot name another store' prose; 0014's three stale §4.5 refs → §4.6). Carry-forward (NOT a freeze blocker): A→B→C transitive attribution under A10 retention. v4 (0006) + 0014 amendment fold all four; interface point 4 changed → research RE-RATIFIED (2026-08-09); reviewer sign-off pending (delivered in round 4)", findings=4),
    dict(spec="0006", round=4, kind="external", date="2026-08-09", verdict="INTERFACE FREEZE reviewer half CONFIRMED (seven-point 0006<->0014 freeze signed from the reviewer side; F1/F2 satisfactorily folded — the folding was NOT itself the sign-off, this disposition is). 0006 ACCEPTANCE HELD for F3 — a valid FORMAT_VERSION>=4 import with origin ABSENT hits contradictory rules (global absent->local-singleton vs current-format preserve-foreign); rule: a v4 import MUST carry origin, missing=malformed->REJECT, never localise (new I14, does NOT alter the frozen seven points — constrains ingress). Plus a minor origin-generation tightening (CSPRNG-128/UUIDv4) + the store-lineage-identity limit. No further architectural blocker to 0006 acceptance seen after F3. v5 folds F3+tightening", findings=2),
    dict(spec="0006", round=5, kind="external", date="2026-08-09", verdict="ACCEPTANCE PASS — no further architectural blocker; design accepted from the reviewer side, no further external design round. Archive v5 byte-identical to the standalone file. Two mechanical closure edits required before the status flip (NOT a design amendment, no re-review): C1 remove superseded 'no-DDL' wording (§0b/§1/Q3) + refresh the stale External-review header row; C2 state origin entropy exactly (canonical UUIDv4 from a CSPRNG, 122 random bits not 128). Plus the PROCESS.md Review closure section. Dev folded all three in v6 and set Spec-Status: accepted", findings=2),
]
