"""Phrases that have been withdrawn, and must not reappear in a spec.

Four external reviews in a row found withdrawn rules still stated normatively,
each time after the document claimed they had been removed. The failure was
always the same shape: I searched for *my own edits* -- annotation markers, the
sections I remembered touching -- rather than for every place the rule is
stated. A search for one's own corrections cannot find text one never annotated.

So the retraction list is now executable. Each entry is (rule_id, pattern,
reason, where-the-current-rule-lives). The rule_id is STABLE and load-bearing:
tests/test_withdrawn_gate_bites.py maps every motivating fixture to a specific
rule_id and asserts THAT entry matches it (R8-5 — proving a fixture matches
*any* entry lets a broad neighbour mask a dead one).
"""

WITHDRAWN = [
    # ---- 0039 (round-6 external finding, 2026-09-11): three post-acceptance
    # amendments each rewrote the cell they touched and left the spec's other
    # sentences asserting the superseded behaviour — the carrier sweep had been
    # run for identifiers, not for the VOCABULARY of a behaviour. THE LIMIT OF
    # THIS REGISTER, stated so a green is not read as "no stale claim survives":
    # these entries refuse the PHRASINGS we happened to write, not the CLAIMS
    # they made. "adds no field" or "the tool result is as before" escapes all
    # three; the positive control (tests/test_0039_degradation_visibility.py)
    # proves the entries FIRE on a marker-stripped copy of the spec, which is a
    # different property from the entry set being complete.
    ("0039-non-list-triples-still-raise",
     # narrow on purpose: "no longer raise TypeError" is the CURRENT claim and must not
     # match; the lint compares punctuation-insensitively, so no backticks here
     r"(null|numeric|number)\b[^|\n]{0,40}(boolean|bool)\b[^|\n]{0,80}(still raises?|TypeError PROPAGATES|is a TypeError today)|"
     r"three shapes that raise still raise|shapes that raise TypeError (today )?still raise",
     "0025 v16 (2026-09-10, owner's word): every non-list `triples` is normalized to no "
     "triples at both call sites — one `primary_failed`/`shape` record, zero facts, "
     "`extraction_unusable: True`, nothing raises",
     "specs/0039 §2a/§2b/§2c-ii rows 6–7/§8 as rewritten at v17; specs/0025 §4b(1) v16"),
    ("0039-bare-array-retry-attributeerror",
     # v2 (2026-09-11): the two "— UNDESIGNED" branches quoted wording that left the
     # spec at v17 and spelled `bare_array` with the underscore the lint then stripped,
     # so neither could ever fire (an ocr review of the v0.21.0 range); the register's
     # rule is history quoted VERBATIM, and the history that exists is §1/§2c's
     # `bare array → cause=AttributeError`.
     r"AttributeError`? inside the `?try`?|bare array → cause=`?AttributeError",
     "0025 v15 (2026-09-10, owner's word): the retry normalizes a bare JSON array exactly "
     "as the first extraction does — a recovery attempt; `cause=bare_array` is unproducible",
     "specs/0039 §2c-i row 2c and §2c-ii rows 8–9 as rewritten at v17; specs/0025 §4b(1) v15"),
    # ---- 0039 round-7 R7-1: the semantic VARIANTS the reviewer named, plus dev's
    # sweep's. These are the BACKSTOP; the primary check is the closed pointer-site
    # list in tests/test_0039_degradation_visibility.py (a negative check over an
    # open vocabulary cannot be complete — every round teaches one more word).
    ("0039-result-surface-unchanged-variants",
     # subject-scoped on purpose: this lint runs over EVERY spec, and "no new field" or
     # "adds no field" are true sentences in nine other specs about their own surfaces.
     # Generic paraphrases are the closed-site test's job (tests/test_0039_…, primary);
     # this entry is the backstop for the phrasings that name THIS subject.
     r"unchanged tool result|tool result is unchanged|(ingest |tool )?result(\'s)? key set is unchanged|"
     r"degrade paths\' return values are unchanged|does not tell the MCP host more|"
     r"diagnostics=None`? learns nothing new|does not add a principal-facing field|the default is NO new field",
     "0025 v18 / 0039 v18: what the ingest result and the MCP tool result carry is stated ONCE in "
     "0039 §2e; every other mention is a pointer that names the location and the subject and "
     "never the value",
     "specs/0039 §2e (v18) — the single carrier, and the pointer rule beside it"),
    ("0039-conditional-raise-after-record",
     r"whether or not the loop then raises|the one path where (it does|the operation raises)|then lets? the TypeError propagate",
     "0025 v16 / 0039 v16: no provider ANSWER raises after a record is written; V-RECORD-ORDER-ON-ERROR "
     "is instanced on a store failure after a record",
     "specs/0039 §2a and V-DEGRADE-RECORDED as rewritten at v18"),
    ("0039-mcp-result-gains-no-field",
     r"MCP tool result gains no field|MCP tool result is unchanged|MCP result gains no field|tool result gain(s)? no field",
     "0025 v18 / 0039 v17: the MCP `remember` tool result carries exactly ONE field this "
     "line added, `extraction_unusable`, and the operator counters remain stripped "
     "(V-MCP-RESULT-CARRIES-ONE; V-MCP-RESULT-UNCHANGED retired)",
     "specs/0039 §2e and §6 V-MCP-RESULT-CARRIES-ONE, v17"),
    # ---- 0031 (round-2 self-correction, 2026-09-01): the P3-5 overreach was
    # withdrawn in the working candidate and the correction reached the README
    # but NOT the adopted spec — two carriers of one fact updated
    # independently; the seal-check's byte-identity assertions (transport
    # fidelity) were structurally blind to it (package == repo@pin, both
    # stale together). Registered per the discipline this file's docstring
    # describes: search for every place the claim is stated, not for one's
    # own edits.
    ("0031-relay-floor-unguarded",
     r"the only thing standing between the marker-bearing note|because nothing\s+reports it|relay floor could be deleted unnoticed",
     "round-2 self-correction: P2-1/P2-2 are the relay floor's standing "
     "host-path guard; P3-5's vacuity does NOT leave the floor untested. "
     "The capability=direct variant is owed because Phase A opens a NEW "
     "path to a mentionable baseline (the MCP surface), not because the "
     "floor is unmeasured",
     "specs/0031 §6a — the corrected P3-5 disposition"),
    # ---- 0022 (external round 2, F1/F2): TWO claims narrowed in round 1 and
    # then left standing in six and three other carriers respectively. The
    # docstring above describes this failure exactly, the list was already
    # gated, and I folded both findings by hand at the site the reviewer named
    # WITHOUT registering the retraction here. Registering it is the fix; the
    # sweep below is what found the rest.
    ("0022-retirement-is-a-new-event",
     r"retirement and reinstatement are both new events|reinstatement are both new events|(retirements?|reversal) (REVERSE|reverses?) BY SUPERSESSION|by supersession, never by edit|a new event that supersedes the retirement",
     "external round 2 F1/0022: the product has NO retirement-event carrier. C3 is narrowed to retain-never-erase over reversible IN-PLACE state; only source_revocations is append-only",
     "specs/0022 §4f + C3; the successor carrier is Q9"),
    ("0022-history-only-grew",
     r"history only grew|appends? (every )?superseded value to .?history|supersede.never.erase(?!.{0,80}NARROWED)",
     "external round 2 F1/0022: there is no generic record-value history in the store; R9 asserted a carrier that does not exist",
     "specs/0022 §4f/R9 — retained-and-updated-in-place, over the append-only ledger"),
    ("0022-class-c-is-system-authored",
     # v2 of this pattern (external round 3, R3-2). The first version matched
     # the FORWARD wording ("system-authored records with no attribution") and
     # missed the REVERSED one ("...and if it is system-authored it is COUNTED
     # in class (c)"), which is what §2c actually said. The sweep reported
     # closure over a carrier it could not see.
     # THE LESSON, and it is why this comment is here: registering a retraction
     # only moves the failure from "did I remember every site" to "does my
     # pattern match every PHRASING". A pattern is a claim about language, and
     # it needs the same adversarial treatment as any other claim — which is
     # what tests/test_withdrawn_gate_bites.py is for, and what this entry now
     # has fixtures in.
     r"system.authored records with NO attribution|only system.authored"
     r"|class \(c\) (counts|is) .{0,30}system.authored"
     r"|if it is system.authored it is COUNTED"
     r"|system.authored[^.]{0,60}(COUNTED|counts) in class \(c\)"
     r"|class \(c\)[^.]{0,60}(only )?if .{0,20}system.authored",
     "external round 2 F2/0022: authorship is not a derivation discriminator — a pre-0014 absorption survivor keeps the incoming record's USER authorship. Class (c) is unattributed AND unreached, any authorship",
     "specs/0022 §4c/R7"),
    # ---- 0014 (rounds 4-8): rules retired during the external review, restated
    # affirmatively nowhere. Underscores are stripped by _normalise (emphasis
    # folding), so identifiers are written normalised. Added at R6-6, which
    # correctly found the previous 'mechanized sweep' was an uncommitted script:
    # THIS list is the mechanism — committed, in the package, run by the suite.
    ("0014-payload-empty-legal",
     r"payload MAY be \{\}|\{\} (is|remains) (the )?legal|\{\} (only|remains .{0,20}legal) at|legal (form )?(ONLY )?at absorption.{0,3}s no.transfer",
     "R4-1/v8-0014: payloads are TOTAL at every site; {} is an integrity error",
     "specs/0014 §4a"),
    ("0014-empty-consumption",
     r"empty.payload consumption|no.payload consumption|payload empty or not|payload MAY be empty",
     "v8-0014: the consult-and-discard record is TOTAL; emptiness was retired with the base+contributor shape",
     "specs/0014 §4/A1/A7"),
    ("0014-legitimately-empty",
     r"which may legitimately be empty",
     "v8-0014: the total base+contributor/input shapes retired the empty payload",
     "specs/0014 §4"),
    ("0014-no-transfer-form",
     r"no.transfer form",
     "v8-0014: the no-transfer case is visible IN the recorded values",
     "specs/0014 §4a/A1"),
    ("0014-empty-payload-evasion",
     r"evasion is the empty payload|empty.payload evasion",
     "R8-5/0014: payloads are store-derived and total, and an empty payload aborts; the cheapest evasion is the NO-TRANSFER CONSUMPTION",
     "specs/0014 §1/§8"),
    ("0014-direct-restoration",
     r"direct restoration( material)?",
     "R4-1/0014: multi-prior absorption killed direct restoration; reversal is recomputation",
     "specs/0014 §7 Reversibility"),
    # ---- 2026-09-11: five 0014 patterns below spelled identifiers WITHOUT their
    # underscores because the lint's normaliser used to strip every underscore; it
    # now keeps intra-token ones (see lint_withdrawn._normalise), so the patterns
    # spell the identifiers as the specs do. Same fixtures, same coverage.
    ("0014-no-format-bump",
     r"no FORMAT_VERSION change",
     "R5-4/0014: the exported Episode field bumps FORMAT_VERSION 4->5 (0010 refuse-dont-drop)",
     "specs/0014 §7a portability"),
    ("0014-sql-column",
     r"consolidation_output_index INTEGER|episodes\.consolidation_output_index",
     "R5-3/0014: the SQL-column form is withdrawn; the index is an Episode model field in the json blob",
     "specs/0014 §4c"),
    ("0014-preimage-into-request-digest",
     r"(pre.image|drafts?|contributions?) (ENTERS?|enters?) .{0,25}logical_request_digest",
     "R5-2/0014: the receipt split; the pre-image enters the OUTCOME digest, replay identity is the REQUEST digest",
     "specs/0014 §4b/§7b"),
    ("0014-loser-may-conflict",
     r"replays.or.conflicts per its receipt|the other replays or conflicts",
     "R8-1/0014: phase 2 is REQUEST-FIRST; a matching raw_request REPLAYS — the concurrent-preflight loser never conflicts",
     "specs/0014 §4b phase 2"),
    ("0014-no-ddl-beyond-ledger",
     r"no schema DDL beyond (the )?ledger",
     "R9-6/0014: the migration ALSO carries the receipts ALTERs; the Episode field adds no DDL of its own but the claim as stated contradicted §7a",
     "specs/0014 §4c/§7a"),
    ("0014-needs-confirmation-recomputed",
     r"needs_confirmation \(never cleared",
     "R9-4/0014: needs_confirmation is EXACT-EQUAL — the shipped absorption (graph.py:163-167) inherits only valid_from/observed_at/confidence and never touches it",
     "specs/0014 §4b partition"),
    ("0014-liveness-trust-transfers",
     r"liveness.trust transfers",
     "R9-4/0014: nothing beyond the C' three transfers at absorption; the vague transfer list misled the field partition",
     "specs/0014 §4b pre-image"),
    ("0014-replay-exact-persisted",
     r"returns EXACTLY the deserialized persisted response|replay equals O1 exactly",
     "R10-1/0014: the receipt persists the EFFECT payload (minus the runtime replayed flag); replay = effects + replayed=True — exact-copy replay contradicted the shipped runtime contract",
     "specs/0014 §4b R9-1 block"),
    ("0014-record-identical-reimport",
     r"accepted IFF it is RECORD.IDENTICAL",
     "R10-5/0014: the shipped remap mints fresh destination ids, so raw record equality never holds; re-import idempotency is SOURCE-IDENTICAL over normalized identity",
     "specs/0014 §2c output-index row"),
    ("0014-references-removed",
     r"REMAPPED fields REMOVED — exactly|every remapped REFERENCE field \(",
     "R12-3/R13-2/0014: reference fields are COMPARED (lineage/operation ids are stable historical per 0010 X18/X19 — compared verbatim, never removed, never remap-inverted)",
     "specs/0014 §2c output-index row (two-set projection)"),
    ("0014-lineage-remap-inversion",
     r"normalized BACK to the source.file id via the import.s remap table|destination lineage IDs? are inverted",
     "R13-2/0014: no such remap exists — the importer never remaps lineage (portability.py:279-291); historical ids are stable (0010 X18/X19) and compare verbatim",
     "specs/0014 §2c output-index row (two-set projection)"),
    ("0014-migrated-digest-identical",
     r"v6 store and a migrated v5 store are digest.identical|file imported twice.{0,60}(accepted as a )?no.op|whole.file.{0,30}no.op",
     "R11-1/R11-2/0014: fresh-constructor and ALTER-path DDL legitimately differ — MANIFESTS[6] is 0013 §4e's SET; and the re-import no-op is scoped to the indexed output, ordinary records keep shipped remap-copy semantics",
     "specs/0014 §4b R10-3 block / §2c output-index row"),
    ("0012-reinforcement-never-persists",
     r"reinforcement (never persists|does not persist) (the |its )?incoming",
     "0012 Design 1 LANDED: restatements persist as their own edges",
     "specs/0012 §4a; specs/0014 §1 historical note"),
    ("0014-validfrom-consolidation",
     r"valid_from\? (disclosure|derived_from)|valid_from is (in|part of) the consolidation",
     "R4-6/0014: Episodes have no valid_from; the consolidation set excludes it",
     "specs/0014 §4a"),
    # Narrowed deliberately. A first attempt matched any *description* of the
    # withdrawn rule -- "the generator added whatever a migration produced" --
    # which every review disposition and test docstring has to contain. A
    # pattern that forces a WITHDRAWN marker onto a dozen paragraphs stops being
    # a lint and becomes noise, and noisy lints get bypassed. These match an
    # affirmative restatement only. The real guard for the migration rule is
    # S50, which is executable.
    ("0007-both-runtimes-qualified",
     r"(3\.45\.1 and 3\.46\.1|3\.46\.1 and 3\.45\.1) (are|is|have been) (qualified|supported|recorded)",
     "R6/0007: the artifact records only 3.45.1; the package failed its own test on 3.46.1",
     "specs/0007 §4a-viii"),
    ("0007-txn-control-unreachable",
     r"transaction control .{0,30}(is|are) (not reachable|unreachable)|enforced by construction",
     "R5/0007: name mangling is not access control; migrations are declarative, and the claim is withdrawn",
     "specs/0007 §4d"),
    # `_normalise` strips underscores, so an identifier must be written
    # against the NORMALISED text: `LEGACY_DIGESTS` arrives as `LEGACYDIGESTS`.
    # This is the second time a pattern was written against raw markdown and
    # could never fire; a dead entry reads as coverage.
    # CASE-SENSITIVE by `(?-i:…)` (the lint searches under re.I globally): the
    # withdrawn thing is 0007's UPPER-CASE CONSTANT, and the case-insensitive
    # form also matched `legacy_digests` — an unrelated LOWER-CASE parameter in
    # 0020's absorption-closure signature (the note-derived fallback digests),
    # a different spec's namespace with nothing to do with base-version
    # resolution. A gate that fires on unrelated new code is a defect in the
    # gate: false positives are how a check gets routed around. The motivating
    # 0007 form is pinned as a fixture in tests/test_withdrawn_gate_bites.py,
    # so the tightened pattern is proven to still bite.
    ("0007-legacy-digests-map",
     r"(?-i:LEGACY_?DIGESTS)",
     "R5/0007: a digest->version map is the circular design; LEGACY_BASE_VERSIONS restricts resolution",
     "specs/0007 §4-i"),
    ("0007-tested-sqlite-tuple",
     r"TESTED_?SQLITE|the tested set is the contract",
     "R5/0007: a hand-edited tuple is not evidence; qualification is derived from sqlite_runtimes.json",
     "specs/0007 §4a-viii"),
    ("0007-declared-range",
     r"3\.35 ?<= ?sqlite|declares? (the )?(supported )?range",
     "R4/0007: a declared range with no evidence or enforcement is not a contract; gate on TESTED_SQLITE",
     "specs/0007 §4a-viii"),
    ("0007-immutable-entries",
     r"old entries .{0,20}are immutable(?!,? and now actually)|regenerates only the current constructor entry",
     "R4/0007: v5 said so and rewrote them; regenerating a historical version differently is now an error",
     "specs/0007 §4a-iv"),
    ("0007-whitespace-collapsed-ddl",
     r'" ?"\.join\(sql\.split\(\)\)|whitespace[- ]collapsed DDL|canonicalisation is deliberately minimal',
     "R3/0007: collapsing whitespace rewrites quoted literals; keep sqlite_master.sql byte-for-byte",
     "specs/0007 §4a"),
    ("0007-rebuildable-by-name",
     r"REBUILDABLE = \(|excluded from the digest by name",
     "R3/0007: identity is (type, name); a same-named trigger digested as clean",
     "specs/0007 §4a-0"),
    ("0007-one-manifest-per-version",
     r"one manifest per version|MANIFESTS: dict\[int, Manifest\]",
     "R3/0007: a version accepts a SET; a correct ALTER migration produces a different digest",
     "specs/0007 §4a-v"),
    ("0007-semantic-signature-bound",
     r"a semantic signature (bounds|is the strictest)|(indexes|indices) are (a )?performance only",
     "R2/0007: four more counterexamples passed it; the bound is known-constructor equality",
     "specs/0007 §4a"),
    ("0007-atomic-adoption-audit",
     r"adoption and (the )?audit are atomic|sink .{0,30}makes .{0,20}atomic",
     "R2/0007: a Python callback is outside the sqlite transaction; attempted/committed instead",
     "specs/0007 §4e"),
    ("0007-refuses-unknown-store",
     r"a veracium build refuses to open a store it does not understand",
     "R2/0007: false of all 23 released builds; the claim covers version-aware builds only",
     "specs/0007 §8"),
    ("0007-names-columns-strictest",
     r"names ?\+ ?columns.{0,40}strictest|names and declared types.{0,30}(strictest|sufficient)",
     "R1/0007: the reviewer built a constraint-stripped counterexample that matched",
     "specs/0007 §4a"),
    ("0007-indexes-performance-only",
     r"(indexes|indices) are a performance property",
     "R1/0007: a UNIQUE index decides which writes are accepted",
     "specs/0007 §4a-iii"),
    ("0007-create-index-restores",
     r"CREATE INDEX IF NOT EXISTS.{0,40}restores",
     "R1/0007: measured -- a wrong same-named index survives untouched",
     "specs/0007 §4a-iii"),
    # `_normalise` strips underscores and backticks before matching, so the
    # pattern must describe the NORMALISED text: `sqlite\_%` arrives as
    # `sqlite\%`. Written against the raw form first, this regex matched
    # nothing at all -- a lint entry that cannot fire is worse than none,
    # because it reads as coverage.
    ("0007-not-like-sqlite",
     r"NOT LIKE 'sqlite\\?%'(?! *(does not|ESCAPE))",
     "R1/0007: backslash is not a LIKE escape without ESCAPE; use GLOB",
     "specs/0007 §4a-i"),
    ("0008-same-author-clears",
     r"clears only on (evidence from the )?(the )?same author",
     "R3: only confirm() clears needs_confirmation; no field value does",
     "specs/0008 §3"),
    ("0008-author-class-clears",
     r"same author class.{0,40}(clear|evidence)",
     "R3: author class is not source identity",
     "specs/0008 §1"),
    ("0009-authorship-note",
     r"retain prior authorship in a note",
     "the note is rebuilt on every upgrade and survives one hop",
     "specs/0009 §4"),
    ("0002-falls-back-to-now",
     r"falls back to now|fallback to now|keep their (pre-)?existing fallback",
     "malformed dates are rejected; absence is the only thing meaning now",
     "specs/0002 §7f"),
    ("0002-validfrom-min-exception",
     r"valid_from = min.{0,30}sole exception",
     "R1: N1 is absolute; min is construction of a new edge",
     "specs/0002 §7c"),
    ("0002-audit-every-op",
     r"an audit of every maintenance-time operation",
     "withdrawn in §1; the audit is scoped to the manifest",
     "specs/0002 §8"),
    ("0002-fixes-three-defects",
     r"fixes three provenance defects",
     "0.4.5 ATTEMPTED three; M3 and M4 do not hold",
     "specs/0002 §8"),
    ("0002-manifest-cannot-drift",
     r"derived from the manifest.{0,40}cannot drift",
     "the evidence-bearing column is hand-authored",
     "specs/0002 §6a"),
    ("0002-general-form-both",
     r"the general form of both advisories",
     "N7 is an end-to-end gate; N9 is the general form",
     "specs/0002 §6"),
    ("0002-five-findings-closed",
     r"all five findings.{0,20}are closed",
     "M3, M4 and consolidation are unimplemented",
     "specs/0002 §11"),
    ("0002-m1-m5-closed",
     r"M1.M5,? all closed",
     "M3, M4, N9b-lineage, N4-decay and X-crash are unimplemented",
     "specs/0002 §11 — generated"),
    ("0002-hardcoded-counts",
     r"(three|four) (rows are red|external reviews)",
     "counts are generated from specs/findings.py",
     "specs/0002 §11, §12"),
    ("0002-046-unreleased",
     r"0\.4\.6 \(unreleased",
     "0.4.6 and 0.4.7 are both published",
     "specs/0002 §11 — generated"),
    ("0003-refuse-correct-nonassertable",
     r"refuse `?correct\(\)`? on a non-assertable edge",
     "Q5 resolved the other way: a correction inherits the corrected edge's class",
     "specs/0003 Q5, §M7"),
    ("0003-ladder-inverted",
     # v2 (2026-09-11): the ladder is written with an arrow; `assistant . third_party`
     # also matched 0011's entitlement table row `assistant | third_party | 0 | ALLOW`,
     # a different table with a different meaning, once the lint stopped stripping the
     # identifier's underscore.
     r"assistant (->|→|=>) third_party.{0,10}allow|assistant (->|→|=>) user.{0,10}block",
     "inverted: the ladder gives assistant->user ALLOW and assistant->third_party BLOCK",
     "specs/0003 §3"),
    ("0003-one-guard-one-loop",
     r"one guard in one loop",
     "the change spans write, read and storage — specs/0003 §7a",
     "specs/0003 §7a"),
    ("0003-full-400-row",
     r"the full 400.row",
     "the product follows the SHIPPED enum; 400 assumed a class that does not exist",
     "specs/ladder.py"),
    # ---- 0015 (round 3): the R2-3/R2-5 withdrawn claims survived in four
    # unswept carriers (R3-3) — exactly this registry's founding failure shape.
    ("0015-cli-gains-counters",
     r"CLI (`?remember`? )?(output|returns?) (gains?|keeps?) (the )?(two|both)|CLI (operator|caller)( sees| and .{0,30}sees)? the (counts|counters|two int)",
     "R2-3/R3-3: CLI output is UNCHANGED — cli.py prints its fixed summary; the counters reach the host-API return only",
     "specs/0015 §2/§4"),
    ("0015-lock-failure-blanket-false",
     r"acquisition failure( or timeout)? .{0,10}(the )?flush returns\s*.False.\s*and sends nothing",
     "R7-1/R8: the failure classes are SPLIT — pre-authorization returns False; a post-send failure returns True with last_sent unwritten; consolidated §4.5",
     "specs/0015 §4 rule 5 / I17"),
    ("0015-unix-only-lock",
     r"fcntl\.flock.{0,15}on\s*.telemetry\.json\.lock|the lock primitive,? pinned:?\s*.?fcntl",
     "R6-3/R8-1: the lock is the OS-exclusive adapter pair (flock/msvcrt.locking), one kernel contract — never a pinned Unix-only primitive nor a breakable lockfile",
     "specs/0015 §4 rule 2"),
    ("0015-nonnegative-epoch",
     r"consent.epoch.{0,40}non.negative|non.negative .{0,15}(int|integer).{0,40}epoch",
     "R7-4: the epoch validity predicate is POSITIVE int (bool excluded); zero is invalid; no live collector holds 0",
     "specs/0015 §4 rule 1 / I16"),
    ("0015-nothing-persisted",
     r"nothing persisted changes|(change|spec) persists nothing|nothing is persisted \(",
     "R2-5/R3-3: telemetry.json's schema_version (and consent_epoch) ARE persisted consent; claims are scoped to the MEMORY store",
     "specs/0015 §2/§4/§7"),
    ("0018-readback-never-an-error",
     r"(malformed or missing|missing or malformed) record yields the\s*audit.unknown facts,? never an error",
     "0018 internal F1: the R13-3 audit-unknown readback branch was DEAD (every "
     "call site is post-record_terminal-success) and contradicted R14-3 — the "
     "integrity check lives AT the read boundary; missing/malformed raises "
     "MigrationAuditReadError. (Pattern deliberately requires the operative "
     "'record yields' form so 0016 v18's frozen round-history narrative, which "
     "describes what R13-3 said using an arrow, is not flagged.)",
     "specs/0018 §4 readback interface / I17"),
    ("0028-state-count-in-prose",
     r"\b(six|seven|eight|nine|thirteen) states\b",
     "0028 external round 5 (corrections): README and §9 said 'nine states' while "
     "the model's EXPECTED executed eight; then 'six states' survived in two model "
     "headers and a build() docstring after the header sweep. The states are the "
     "ones EXPECTED names and the program prints their count on every run; no "
     "carrier states the number. (The version cell's own history of the error is "
     "in a WITHDRAWN-marked block.) The other 0028 withdrawals — the window-refusal "
     "trio, 'except the current-truth pointer', V-UNAVAILABLE-NEVER-HEAD — are "
     "registered with the v13 fold, whose text marks the five paragraphs that "
     "quote them as errata.",
     "specs/0028 §6a / §9; specs/evidence/0028/check_successor_lookup.py"),
    ("0028-window-refuses-writers",
     r"refused for the whole resolution|refused for the window'?s duration|refuses a concurrent writer",
     "0028 external rounds 3–4 (correction 7; R4-2..R4-5): v8 said a concurrent writer is "
     "refused for the whole resolution / the window's duration; the two-connection "
     "transcript disproved it — the writer waits behind busy_timeout and succeeds, or "
     "fails at COMMIT and loses the write. A THIRD wording survived two sweeps (R4-3).",
     "specs/0028 §4b-o / §5; specs/evidence/0028/window_transcript.py"),
    ("0028-except-current-truth-pointer",
     r"except (the )?current-truth pointer",
     "0028 external round 4 (R4-2): v10's 'no step consults wall-clock now except the "
     "current-truth pointer' named one step that does; no step reads a clock — the one "
     "injected value captured at step 0 is threaded everywhere, the pointer included. "
     "Survived as a line-wrapped sentence a flat grep missed.",
     "specs/0028 §4a"),
    ("0028-old-invariant-name",
     r"V-UNAVAILABLE-NEVER-HEAD",
     "0028 v12: renamed V-NEVER-HEAD and phrased over the STATES it must hold in — "
     "phrased over UNAVAILABLE results, a collapse-to-HEAD produces none and the "
     "invariant passes vacuously. A live use of the old name is a stale carrier.",
     "specs/0028 §6"),
    ("0028-indeterminate-always-with-cause",
     r"every instance is disclosed with its cause|never a bare indeterminate",
     "0028 external rounds 5–6 (R5-3, R6-1): SUCCESSOR_UNAVAILABLE is INDETERMINATE with "
     "NO principal-facing cause by design (a cause there is the existence signal); §4b "
     "carries two classes. R5-3 fixed the checklist; R6-1 found the definition it "
     "summarises still carried the one-rule form.",
     "specs/0028 §4b; the reviewer checklist"),
    ("0028-lock-surfaces-bare",
     r"surfaces? unwrapped|raises SQLite'?s bare|receive the bare|commit failure is bare",
     "0028 external round 6 (R6-2): 0029 v11 (9202d3d) made _write_txn own every commit "
     "it opens and refuse a commit-time 'database is locked' in the wrapped BEGIN-time form "
     "(V-LOCK-REFUSAL-FORM), SQLite's message retained as the cause; three 0028 carriers "
     "kept describing the bare form while the sealed window test asserted the wrapped one. "
     "(Pattern deliberately requires the operative claim forms so 'the bare v2 spec', "
     "'bare — cells' and 'a bare interpreter error' — different bares — are not flagged.)",
     "specs/0028 §4b-o / §5 / §7; specs/0029 §4a"),
    ("0038-gate-passed",
     r"the §8 gate PASSED|§8 gate — RUN, AND PASSED|gate PASSED on a NAMED DEVIATION",
     "0038 external round 2 (R2-1): v5.x said the §8 validation gate PASSED while its "
     "mandatory blind-human condition was unmet — 'a named deviation, not waived' documents "
     "the hole and then claims what the hole disproves; disclosure is not compliance. The "
     "owner ruled option 3: the gate is NOT SATISFIED, its human condition UNMET, nothing "
     "substitutes for it; §6b-A is an explicitly weaker rule that borrows the gate's "
     "statistic and none of its authority.",
     "specs/0038 §6b, §6b-A, §9"),
    ("0038-named-deviation-not-waived",
     r"named deviation,? (and )?not waived|deviation from the frozen gate'?s §1, named and not waived",
     "0038 external round 2 (R2-1): naming a deviation from a mandatory condition does not "
     "satisfy it; the phrase is withdrawn with the claim it qualified.",
     "specs/0038 §6b, §9"),
]
