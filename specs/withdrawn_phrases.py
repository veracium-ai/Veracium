"""Phrases that have been withdrawn, and must not reappear in a spec.

Four external reviews in a row found withdrawn rules still stated normatively,
each time after the document claimed they had been removed. The failure was
always the same shape: I searched for *my own edits* -- annotation markers, the
sections I remembered touching -- rather than for every place the rule is
stated. A search for one's own corrections cannot find text one never annotated.

So the retraction list is now executable. Each entry is a phrase that was
retracted, the reason, and where the current rule lives.
"""

WITHDRAWN = [
    # ---- 0014 (rounds 4-6): rules retired during the external review, restated
    # affirmatively nowhere. Underscores are stripped by _normalise (emphasis
    # folding), so identifiers are written normalised. Added at R6-6, which
    # correctly found the previous 'mechanized sweep' was an uncommitted script:
    # THIS list is the mechanism — committed, in the package, run by the suite.
    (r"payload MAY be \{\}|\{\} (is|remains) (the )?legal",
     "R4-1/v8-0014: payloads are TOTAL at every site; {} is an integrity error",
     "specs/0014 §4a"),
    (r"which may legitimately be empty",
     "v8-0014: the total base+contributor/input shapes retired the empty payload",
     "specs/0014 §4"),
    (r"no.transfer form",
     "v8-0014: the no-transfer case is visible IN the recorded values",
     "specs/0014 §4a/A1"),
    (r"direct restoration( material)?",
     "R4-1/0014: multi-prior absorption killed direct restoration; reversal is recomputation",
     "specs/0014 §7 Reversibility"),
    (r"no FORMATVERSION change",
     "R5-4/0014: the exported Episode field bumps FORMAT_VERSION 4->5 (0010 refuse-dont-drop)",
     "specs/0014 §7a portability"),
    (r"consolidationoutputindex INTEGER|episodes\.consolidationoutputindex",
     "R5-3/0014: the SQL-column form is withdrawn; the index is an Episode model field in the json blob",
     "specs/0014 §4c"),
    (r"pre.image (ENTERS|enters) (the )?(receipt digest|logicalrequestdigest)",
     "R5-2/0014: the receipt split; the pre-image enters the OUTCOME digest, replay identity is the REQUEST digest",
     "specs/0014 §4b/§7b"),
    (r"reinforcement (never persists|does not persist) (the |its )?incoming",
     "0012 Design 1 LANDED: restatements persist as their own edges",
     "specs/0012 §4a; specs/0014 §1 historical note"),
    (r"validfrom\? (disclosure|derivedfrom)|validfrom is (in|part of) the consolidation",
     "R4-6/0014: Episodes have no valid_from; the consolidation set excludes it",
     "specs/0014 §4a"),
    # Narrowed deliberately. A first attempt matched any *description* of the
    # withdrawn rule -- "the generator added whatever a migration produced" --
    # which every review disposition and test docstring has to contain. A
    # pattern that forces a WITHDRAWN marker onto a dozen paragraphs stops being
    # a lint and becomes noise, and noisy lints get bypassed. These match an
    # affirmative restatement only. The real guard for the migration rule is
    # S50, which is executable.
    (r"(3\.45\.1 and 3\.46\.1|3\.46\.1 and 3\.45\.1) (are|is|have been) (qualified|supported|recorded)",
     "R6/0007: the artifact records only 3.45.1; the package failed its own test on 3.46.1",
     "specs/0007 §4a-viii"),
    (r"transaction control .{0,30}(is|are) (not reachable|unreachable)|enforced by construction",
     "R5/0007: name mangling is not access control; migrations are declarative, and the claim is withdrawn",
     "specs/0007 §4d"),
    # `_normalise` strips underscores, so an identifier must be written
    # against the NORMALISED text: `LEGACY_DIGESTS` arrives as `LEGACYDIGESTS`.
    # This is the second time a pattern was written against raw markdown and
    # could never fire; a dead entry reads as coverage.
    (r"LEGACY_?DIGESTS",
     "R5/0007: a digest->version map is the circular design; LEGACY_BASE_VERSIONS restricts resolution",
     "specs/0007 §4-i"),
    (r"TESTED_?SQLITE|the tested set is the contract",
     "R5/0007: a hand-edited tuple is not evidence; qualification is derived from sqlite_runtimes.json",
     "specs/0007 §4a-viii"),
    (r"3\.35 ?<= ?sqlite|declares? (the )?(supported )?range",
     "R4/0007: a declared range with no evidence or enforcement is not a contract; gate on TESTED_SQLITE",
     "specs/0007 §4a-viii"),
    (r"old entries .{0,20}are immutable(?!,? and now actually)|regenerates only the current constructor entry",
     "R4/0007: v5 said so and rewrote them; regenerating a historical version differently is now an error",
     "specs/0007 §4a-iv"),
    (r'" ?"\.join\(sql\.split\(\)\)|whitespace[- ]collapsed DDL|canonicalisation is deliberately minimal',
     "R3/0007: collapsing whitespace rewrites quoted literals; keep sqlite_master.sql byte-for-byte",
     "specs/0007 §4a"),
    (r"REBUILDABLE = \(|excluded from the digest by name",
     "R3/0007: identity is (type, name); a same-named trigger digested as clean",
     "specs/0007 §4a-0"),
    (r"one manifest per version|MANIFESTS: dict\[int, Manifest\]",
     "R3/0007: a version accepts a SET; a correct ALTER migration produces a different digest",
     "specs/0007 §4a-v"),
    (r"a semantic signature (bounds|is the strictest)|(indexes|indices) are (a )?performance only",
     "R2/0007: four more counterexamples passed it; the bound is known-constructor equality",
     "specs/0007 §4a"),
    (r"adoption and (the )?audit are atomic|sink .{0,30}makes .{0,20}atomic",
     "R2/0007: a Python callback is outside the sqlite transaction; attempted/committed instead",
     "specs/0007 §4e"),
    (r"a veracium build refuses to open a store it does not understand",
     "R2/0007: false of all 23 released builds; the claim covers version-aware builds only",
     "specs/0007 §8"),
    (r"names ?\+ ?columns.{0,40}strictest|names and declared types.{0,30}(strictest|sufficient)",
     "R1/0007: the reviewer built a constraint-stripped counterexample that matched",
     "specs/0007 §4a"),
    (r"(indexes|indices) are a performance property",
     "R1/0007: a UNIQUE index decides which writes are accepted",
     "specs/0007 §4a-iii"),
    (r"CREATE INDEX IF NOT EXISTS.{0,40}restores",
     "R1/0007: measured -- a wrong same-named index survives untouched",
     "specs/0007 §4a-iii"),
    # `_normalise` strips underscores and backticks before matching, so the
    # pattern must describe the NORMALISED text: `sqlite\_%` arrives as
    # `sqlite\%`. Written against the raw form first, this regex matched
    # nothing at all -- a lint entry that cannot fire is worse than none,
    # because it reads as coverage.
    (r"NOT LIKE 'sqlite\\?%'(?! *(does not|ESCAPE))",
     "R1/0007: backslash is not a LIKE escape without ESCAPE; use GLOB",
     "specs/0007 §4a-i"),
    (r"clears only on (evidence from the )?(the )?same author",
     "R3: only confirm() clears needs_confirmation; no field value does",
     "specs/0008 §3"),
    (r"same author class.{0,40}(clear|evidence)",
     "R3: author class is not source identity",
     "specs/0008 §1"),
    (r"retain prior authorship in a note",
     "the note is rebuilt on every upgrade and survives one hop",
     "specs/0009 §4"),
    (r"falls back to now|fallback to now|keep their (pre-)?existing fallback",
     "malformed dates are rejected; absence is the only thing meaning now",
     "specs/0002 §7f"),
    (r"valid_from = min.{0,30}sole exception",
     "R1: N1 is absolute; min is construction of a new edge",
     "specs/0002 §7c"),
    (r"an audit of every maintenance-time operation",
     "withdrawn in §1; the audit is scoped to the manifest",
     "specs/0002 §8"),
    (r"fixes three provenance defects",
     "0.4.5 ATTEMPTED three; M3 and M4 do not hold",
     "specs/0002 §8"),
    (r"derived from the manifest.{0,40}cannot drift",
     "the evidence-bearing column is hand-authored",
     "specs/0002 §6a"),
    (r"the general form of both advisories",
     "N7 is an end-to-end gate; N9 is the general form",
     "specs/0002 §6"),
    (r"all five findings.{0,20}are closed",
     "M3, M4 and consolidation are unimplemented",
     "specs/0002 §11"),
    (r"M1.M5,? all closed",
     "M3, M4, N9b-lineage, N4-decay and X-crash are unimplemented",
     "specs/0002 §11 — generated"),
    (r"(three|four) (rows are red|external reviews)",
     "counts are generated from specs/findings.py",
     "specs/0002 §11, §12"),
    (r"0\.4\.6 \(unreleased",
     "0.4.6 and 0.4.7 are both published",
     "specs/0002 §11 — generated"),
    (r"refuse `?correct\(\)`? on a non-assertable edge",
     "Q5 resolved the other way: a correction inherits the corrected edge's class",
     "specs/0003 Q5, §M7"),
    (r"assistant . third_party.{0,10}allow|assistant . user.{0,10}block",
     "inverted: the ladder gives assistant->user ALLOW and assistant->third_party BLOCK",
     "specs/0003 §3"),
    (r"one guard in one loop",
     "the change spans write, read and storage — specs/0003 §7a",
     "specs/0003 §7a"),
    (r"the full 400.row",
     "the product follows the SHIPPED enum; 400 assumed a class that does not exist",
     "specs/ladder.py"),
]
