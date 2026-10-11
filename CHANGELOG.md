# Changelog

## Unreleased

- **Fixed: historical recall now shows the possible-extraction-error marker (specs/0019, U5).** Since 0019 landed,
  `recall(as_of=...)` and `facts_valid_at` rendered a fact the extraction check had flagged WITHOUT
  `[possible extraction error]`, although every current-recall surface shows it. A model reading a historical answer
  could therefore present an extractor's guess with no warning attached. `asof.resolve.render_line` now places the
  marker exactly where `graph.render_edges` does (after the object, before the note) on all three of its branches:
  grounded as of the time asked, fenced ("what was believed"), and indeterminate. Found by the external reviewer of
  the 0045-0047 round-1 package (2026-10-10), as a witness inside finding R1-05. Three tests, one per branch, each
  checked to fail when that branch's marker is removed. **Who should upgrade:** hosts that call `recall(as_of=...)`
  or `facts_valid_at` and pass the result to a model.

- **Accepted: the implementation of specs/0043, the refusal harness, at external round 9 — "ACCEPT —
  IMPLEMENTATION at the reviewed pin. R8-01 is closed. No new blocking finding."** The implementation review ran
  rounds 5 to 9 on round 4's design acceptance. The accepted code is pin `f7a1a42`, reviewed as the round-9 package;
  the reviewer's own offline run read 5,458 passed and 48 skips, each explained, with no failures. The design
  accepted at round 4 is unchanged (INV-3–6: the ledger, blindness, adjudication and arm contracts). Rounds 5 to 8
  raised 10 findings; each is a row in the spec's generated Review closure ledger, closed by a test a reader can run,
  and each round's package and verdict are rows in `specs/reviews.py`. The spec moves to v6.10, which records what
  was accepted and the limits the acceptance keeps: the published refusal rates (veracium 12/24, baseline 1/24) are
  results on a five-fact fixture, not production estimates; the arm comparison waives whitespace-only lines before
  the question as formatting, which is not proof that formatting cannot affect a model; and the marker set the arm
  check removes is derived from the renderer, so an error in that derivation would affect both sides. The
  corrections are in the harness (`specs/evidence/0043/`) and its tests; **no 0043 correction touched `src/`**:
  0043's one product surface, `gate.render_gate_input` with the harness-only `render=` parameter (recorded under
  tranche 1 below), is byte-identical since the round-5 pin. Nobody needs to upgrade for this entry.

- **Accepted: the implementation of specs/0041, targeted redaction, at external round 14 — "Verdict: ACCEPTED. The
  implementation at this pin closes both round-13 findings and the shared-carrier observation. No new blocking or
  nonblocking finding is raised."** The implementation review ran rounds 9 to 14 on round 8's design acceptance.
  The accepted code is pin `8a54a87`, reviewed as the round-14 package; the reviewer's own offline run read 5,139
  passed and 48 skips, each explained, with no failures. The design accepted at round 8 is unchanged: the reviewer
  checked INV-1–INV-12, the 64-carrier treatment map and §4h's transition rules byte-identical to round 13's. The
  same verdict accepts the IMPLEMENTATION of specs/0014 §2c's rider (accepted as a contract at round 13) on its three
  conditions. Rounds 9 to 13 raised 22 findings and observations; each is a row in the spec's generated Review
  closure ledger, closed by a test a reader can run, and each round's package and verdict are rows in
  `specs/reviews.py`. The spec moves to v15.5, which records what was accepted and the limits the acceptance keeps:
  other records holding the same content need their own redaction; earlier backups and host-held copies are outside
  the guarantee; contention cost is not quantified. **WHO SHOULD TAKE THIS: anyone who redacts records, or moves
  stores carrying redactions between instances (export/import or restore).** This entry also stands for the round-12
  to round-14 corrections, which this file did not record one by one:

  - **A store's own export of a redacted quarantined edge imports again.** Redacting an edge already quarantined
    listed a bookkeeping field the importer did not accept, so the store exported a notice its own importer
    refused. A notice's field set is now one closed, named domain, read by both the writer and the importer.
  - **"Nothing to redact" is decided over everything a redaction reaches**, not the live record alone. An edge
    emptied by an ordinary write still carries content in its history, its confirmation digest and its ledger
    digests; `Memory.redact` used to refuse it and leave all three. It now treats them. A record with no covered
    content or marker anywhere is still refused, and the refusal writes nothing.
  - **One redaction event has one body.** A contradictory notice of a store's OWN redaction event was accepted on
    import, and a store's own event relayed back wrote a second record of it. Both now resolve to one source
    identity and one body: a contradiction refuses the whole import, and a faithful relay is recognised as
    existing.
  - **A redaction now reaches a consolidation output the destination already holds.** The importer refused any
    difference on such an output before a notice could apply, so the held summary kept its content. Under the
    specs/0014 §2c rider it admits exactly one difference: that output's own redaction — its own notice, every
    differing field named by it, and each one's value exactly the marker. Any other difference refuses the whole
    import, as before. A repeated import under another user id binds the notice to the copy that exists.
  - **Rows shared between records are accounted for.** A source-revocation reason, or a supersession refusal that
    links two edges, already marked by another record's redaction is now attested in the second record's receipt
    instead of being omitted. The contribution ledger is the named exception: its digests are cleared, not marked,
    and an empty digest cannot show that it was ever written.

- **specs/0041 targeted redaction — the round-10 implementation corrections (round 11).** The round-10 review
  RETURNED the implementation with four findings, each in the import, attestation or provenance contracts. Each
  was swept as a sample of its class, and one more instance was found by our own testing. **WHO SHOULD TAKE THIS:
  anyone who imports redaction notices from another store, or restores a store that has deleted a redacted
  episode.**

  - **BREAKING — `Memory.redact` refuses the reason `imported_notice`.** It is the label a store writes when it
    applies ANOTHER store's redaction notice. A caller using it claimed a provenance that didn't happen, its
    receipt lost its known facts, and its export could not be imported. The owner's ruling: only the import path
    writes it. **WHO MUST ACT:** callers passing `imported_notice` to `redact`; pass the reason that applies
    (`subject_request`, `operator_policy`, `erroneous_capture` or `legal_obligation`). A notice whose own reason is
    `imported_notice` is refused on import too.
  - **BREAKING — `Memory.redact` refuses a record with nothing to redact** (no content and no redaction marker in
    any field, e.g. an episode whose summary is empty). It used to succeed, attest nothing, and export a notice the
    importer refused. The owner's ruling. **WHO MUST ACT:** callers that redact records which may be empty should
    expect the refusal.
  - **A redaction now attests every field holding its redacted value**, including fields that already held the
    marker. Redacting a row that arrived carrying the marker without its notice now protects it from ordinary
    writes, and its export round-trips.
  - **Restoring after deleting a redacted episode works.** After `delete_episode` on a redacted episode, importing a
    file that carries that episode and its notice — the store's own backup, before or after the redaction —
    writes the episode back in its redacted form, under the original redaction record. Before, the content came
    back while the record still said "redacted". A file carrying the episode WITHOUT its notice is still refused.
    `veracium doctor` now reports such a deleted, redacted episode as information, not an error.
  - **A full export carrying a newly redacted outcome now applies to a store holding the earlier outcome.** It was
    refused, and the held outcome kept its content. Outcome records follow the same rule as other records; a
    change to an outcome chain's structure is still refused.
  - **Redaction notices from other stores are identified exactly.** A notice's source (origin, user, event) is now
    stored in its own columns and compared exactly. Identifiers containing control characters (U+001F, NUL) could
    make two notices collide, make a relayed notice lose its source, or bypass the check that refuses a
    contradictory notice. The `redactions` table gains three columns; it is new in the unreleased store version 15,
    so there is no further version bump. A store created from an unreleased main checkout at the earlier v15
    shape is not supported across this change.
  - **Provenance is read from the redaction record, not from its reason**: a redaction counts as received from
    another store only when the record holds that store's identity, which only an import writes.

- **Evidence tooling: the offline test kit now matches the qualified runtime.** `specs/evidence/offline/` held a
  cp312 `pydantic_core`, which cannot install on the CPython 3.14 floor, and seven of its eleven wheels trailed the
  measured runtime. It now holds that runtime's exact versions (cp314 `pydantic_core` 2.46.5, pydantic 2.13.5,
  pytest-randomly 5.0.0 and the rest), hash-locked; `run_offline.sh` with a 3.14.7 interpreter ran the suite with no
  network: 4854 passed, 46 skipped. `JOINT-TEST-GROUPS.md` beside it names the two groups of tests that must share one
  pytest process when the suite is split. No product change.
- **specs/0041 targeted redaction — the round-9 implementation corrections (round 10).** The round-9 review
  RETURNED the implementation with eight findings. Each was treated as a sample of its class and swept; the sweeps
  found more instances, which are corrected here too. **WHO SHOULD TAKE THIS: anyone who redacts.** Before it, a
  redaction could be undone or bypassed by a concurrent write on a second connection, by a consolidation running at
  the same time, or by a later import, and the receipt did not name records that still held the content.

  - **BREAKING — reason fields are closed vocabularies for new writes.** A revoke's reason must be one of
    `subject_request`, `legal_obligation`, `erroneous_capture`, `policy`. A lift's must be one of
    `revoked_in_error`, `subject_request`, `legal_obligation`, `policy` (the owner's ruling). `Episode.retired_reason`
    and `Edge.invalidation_reason`, when present, must be registered reasons. Each is checked when a record is
    written and when it is imported, and anything else is refused. Records already stored with free text still load.
    **WHO MUST ACT:** callers passing free-text reasons to `revoke_source`. Also: **a store holding legacy free-text
    reasons (or a free-text episode kind) cannot restore its own export until those records are redacted**, because
    redaction replaces the prose. Admitting legacy prose on restore would be a change to D1.
  - **BREAKING (receipt shape) — a redaction receipt now reports two kinds of fact.** For a redaction received from
    another store (an imported notice), `reason`, `recorded_at`, `store_version_before`, `store_version_after`,
    `marker_version` and `event_ref` are the SOURCE's, and are `None` where the notice does not carry them. This
    store's own application of the notice is reported under `applied_at`, `applied_store_version_before`,
    `applied_store_version_after` and `applied_event_ref`. The four version and time fields are therefore Optional.
    **WHO MUST ACT:** consumers that read those fields as always-integers.
  - **The receipt names more of what may still hold the content** (§11.5(3), widened by the owner). It names
    records linked to the redacted one by an identifier, in either direction:
    - redacting a fact names the conversation episode it was extracted from and its outcome episodes;
    - redacting an episode names the facts extracted from it and any consolidation output built from it.
    Records already redacted are left out. Disputed or corrected facts add a named category, because the episode
    recording the dispute or correction quotes them.
  - **Concurrency.** These decisions are now made inside the write's own transaction, so a second connection's
    redaction cannot land between the check and the write and be overwritten or consumed:
    - an ordinary episode write's redaction check, and its in-flight-consolidation reservation check;
    - consolidation's claim of its inputs. An input redacted after the listing makes the pool report the existing
      `contended`, and a redacted episode is never consolidated;
    - dispute, record_outcome and correct, which also no longer leave a partial write on a redacted record;
    - the outcome chain's compare-and-set, which now holds across two connections.

    The store's instance lock is now re-entrant, which changes nothing across threads.
  - **Readers and derivations skip redacted records.** Semantic backfill no longer re-embeds them. Proactive recall
    no longer returns them. Expiry skips them, so one redacted aged edge no longer makes every `maintain()` fail. A
    wiki compile that raced a redaction recompiles once, and otherwise returns a fixed notice; it never returns a
    body built from redacted content.
  - **Import and export of redaction notices.** A notice is bound to the user and record it was imported for, so
    the same file imported for two users protects both. A later notice that contradicts one already held refuses
    the whole import. A re-export passes the original notice on unchanged, so an honest relay is not mistaken for
    corruption. Notice field names must be the redacted record's real fields. An episode whose kind field holds
    the redaction marker can now be imported when the same import attests that the kind was redacted.
  - **Only a redaction writes the reason `redacted`.** Every other writer refuses it, and an import admits it only
    when a notice in the same import, or one already held, covers that record. Before, an ordinary write could
    make a record no redaction had touched show as redacted.
  - **Free text already stored in a revocation's reason** is replaced at redaction. This goes through the one
    function specs/0022's append-only rule now admits; it changes only that column, so which sources are revoked
    cannot change.
  - The redaction-record table (`redactions`) gains a column. It is new in this unreleased store version 15, so
    there is no further version bump.

- **Fixed: opening a store no longer leaves an SQLite connection open.** `runtime_identity()` opened an in-memory
  connection to read `sqlite_source_id()` and never closed it, so every store open left one behind, reported on
  Python 3.13 and newer as `ResourceWarning: unclosed database` once the store was closed and collected (found by
  the workflow platform, 2026-09-29). The three other in-memory probe connections in `store/schema_version.py`
  closed only on success; all four are now closed on every path. Nothing a store records or refuses changes. Because
  this is the first change to `src/` since specs/0042's round-8 pin, the INV-7 four-arm run was re-made on the new
  tree (`specs/evidence/0042/inv7_transcript.txt`): the four arms read identical over 860 tests with every gate
  true, and the twin's digest moved with the one file of its sixty that changed.

- **BREAKING: Veracium requires Python 3.14 or newer, and pydantic 2.12 or newer.** `requires-python` moves from
  `>=3.10` to `>=3.14` (the owner's decision, 2026-09-27), and CI tests 3.14 alone. pydantic's floor moves from 2.7 to
  2.12 because no `pydantic-core` wheel exists for CPython 3.14 below 2.12; the 2.7 floor's original reason, specs/0016
  D1's `Field(deprecated=...)`, had already lapsed when D2 removed it. The minimum-dependency CI job now pins 2.12.0
  and, again, asserts the installed version equals the declared floor (`tests/test_dependency_floor.py`; the
  assertion had gone with D2 while the job's comment still claimed it). **WHO MUST ACT:** anyone on Python 3.13 or
  older stays on the last 3.10-floor release. **AND ON 3.14, THE STORE STILL QUALIFIES ONE SQLITE BUILD, 3.45.1**
  (specs/0007; widening it is 0007's open question S-Q7, a spec change not yet made): a 3.14 whose `sqlite3` links
  another build — uv's, python.org's and Homebrew's standalone builds bundle newer ones, measured at 3.53.1 for uv's
  3.14.7 — refuses to open a store with `unsupported-sqlite`. A 3.14 linked against the system SQLite on Ubuntu 24.04,
  as GitHub's setup-python builds are, runs. Evidence for 3.14 also changed: specs/0042's evidence layer reads
  interpreter internals, and three 3.14 changes needed answers — lazy annotations (PEP 649: the INV-7 describer no
  longer reads an annotation, which on 3.14 ran compiler-generated code in census.py's name), a tokenizer that refuses
  an invalid byte even in a comment (the source reader now decodes strictly), and annotation and type-parameter scopes
  in the symbol table (the scope resolver models them, refuses a block kind it does not know, and refuses a census use
  inside one). Those are changes to accepted evidence and go to external review as 0042 round 24. Two evidence
  outputs changed with the interpreter, not the code: 0041's carrier enumeration prints `X | None` where it printed
  `Optional[X]` (34 lines; the counts do not move), and the 0029/0030 seam model reads both spellings and derives its
  deep-nesting probe's depth from the running `json`.

- **Accepted: the implementation of specs/0042, exercised guarantees, at external round 23 — "ACCEPTED. The
  round-22 regression is fixed; no new findings."** The implementation review ran rounds 6 to 23 on round 5's
  design acceptance, as amended by acceptance at round 16 (the meaning of UNINSTRUMENTED: INV-7's reference arm
  carries the census of an accepted commit, pinned by digest) and at round 19 (INV-7's scope: census code that
  changes behaviour, not census code written to attack the measurement). The accepted code is pin `d00cd86`,
  reviewed as the round-23 package; the reviewer's own run read 4,136 passed and 35 skips, each explained, with no
  failures. Every finding was in the ACCEPTANCE CHECKS — the evidence layer under `specs/evidence/0042/` and its
  tests — and `src/` is byte-identical to the round-8 package's pin. Rounds 6 to 22 raised 34 findings against the
  implementation; each is a row in the spec's generated Review closure ledger, closed by a test a reader can run
  (`specs/closure_findings.py`), and each round's package and verdict are rows in `specs/reviews.py`. The spec moves
  to v12.4, which records what was accepted and what the acceptance does not cover: the limits it names stay named,
  and an interpreter the package did not run — CPython 3.14 — is new ground for this evidence, to be reviewed as a
  change to it. This entry also stands for rounds 11 to 23, which this file did not record one by one; their
  mechanisms are in the spec's implementation notes and in each round's closure rows.

- **Fixed: the census's round-9 implementation finding — the twin transform establishes that a census alias
  is bound once by a sibling census import, and stops claiming the one thing a static reading cannot reach
  (specs/0042, round 10; one finding, in the ACCEPTANCE CHECKS).** Round 8's F1 and F2 are closed; no product
  code changed and `src/` is byte-identical to the round-9 pin. *The finding:* round 8 made the census-alias
  question a SCOPE question, and scope is not identity. A genuine `from . import census as _census` followed
  by `_census = On()` still resolves to module scope while no longer denoting the census, and the
  `aliases or {"_census", "census"}` fallback treated those two spellings as the census in a module importing
  no census at all. In both cases an ordinary function returned 101 in the source and 1 in the twin while
  `verify()` reported no problems. *Three things changed.* `declared_names` now examines the import's `module`
  and `level` and not only the imported NAME — it tested `any(a.name == "census")` alone, so six of seven
  spellings were collected, including `from totally_unrelated import census`, `from conftest import census`
  and `from .. import census`; only the sibling form `from . import census` is the census now. The guessed-alias
  fallback is REMOVED, which preserves ordinary behaviour in a module that imports no census (the verdict
  allows "preserve or refuse", and preserving is the half that cannot over-refuse). And an established alias
  must be bound EXACTLY ONCE at module level, read from the compiled code object by rule A's own mechanism,
  now public as `module_binding_count` — a name bound twice had its import replaced, and the transform refuses
  rather than rewriting a condition whose subject it cannot establish. **THE RUNG THE FIX DOES NOT CLAIM.**
  Three rounds climbed membership → spelling → scope, one rung per round, and the fourth — does the alias
  DENOTE this project's census module? — is not statically reachable: two BYTE-IDENTICAL files under different
  packages bind different objects, because `.census` resolves against whichever package the file sits in, and
  a static reading cannot separate them since they ARE the same file. So the refusal now states exactly what
  it establishes and no more, and identity is asserted at RUNTIME instead, in a regression that already
  executes both modules and can compare `veracium.schema._census is veracium.census` with a negative control.
  Measured before shipping: the twin derives byte-identically (162 sites, 302 fires, 152 consults, 4 bypasses,
  digest unchanged), and zero modules use the import spelling the removed fallback would newly refuse.

- **Fixed: the census's round-8 implementation findings — the nested-scope rule reads the interpreter instead
  of a hand-picked predicate pair, the comparison derives its control set once, and the twin transform asks a
  scope question where it had been matching a spelling (specs/0042, round 9; three findings, plus two found by
  exhausting their classes).** All five are in the ACCEPTANCE CHECKS; no product code changed, and `src/` is
  byte-identical to the round-8 pin. *F1, the nested-scope rule:* a nested `import os as S` or
  `from os import path as S` under `global S` replaced a declared site while the scan reported it bound and the
  site's counters stayed at zero — `symtable` reports such a symbol `is_imported` and NOT `is_assigned`, so the
  rule's `is_global() and is_assigned()` never fired. The fix is not a third predicate: the rule now reads what
  the compiler emits in a NESTED code object, `STORE_GLOBAL` or `DELETE_GLOBAL`, which is the same kind of
  reading the module-level rule already was and is total over syntax for the same reason. The superseded pair
  is kept as the negative control its replacement must beat, and the two are measured to differ on exactly the
  two nested imports and agree on every other row of a 46-case matrix, on 3.10, 3.11, 3.12 and 3.13. The nested
  opcode set is asserted to be a STRICT SUBSET of the module-level one, because a class body's ordinary
  attribute assignment emits `STORE_NAME` in its own code object and reading the wider tuple there refuses
  `class K: S = 1` — correct code, and every class whose attribute collides with a site name. One row changes
  hands between the two rules at 3.12, where PEP 709 inlines a list comprehension's walrus into the module,
  while the generator-expression spelling stays with the nested rule on every version; the matrix therefore
  pins WHICH rule caught each refused row, since a matrix asserting only "refused" is green for a different
  reason on each side of that boundary. *F2, the comparison:* the set of control runs had TWO derivations —
  the comparison chose controls by DIRECTORY and substituted the main arm's summary for an absent one, while
  the exit gate iterated the SUMMARY KEYS — so deleting one key made them disagree: the control was still
  compared, decoded through the wrong arm's dictionaries, and its exit check vanished, which meant a control
  run that FAILED gave exit 0. That is the defect round 8 closed, restored by another route, because that fix
  moved the gate's source from one set of what happens to be available to another. There is now one derivation:
  a control whose directory exists without its own summary is named and fails the exit, never substituted. The
  fix is measured to change nothing for a COMPLETE capture — the harness at the round-8 pin and the current one
  agree on verdict, per-test comparison, exit and every pre-existing gate — so the shipped four-arm transcript
  needs no re-run. *F3, the twin transform:* round 8 made "is this name the declared SITE?" a scope question and
  routed it to the resolver; the CENSUS-ALIAS question four methods away was still answered by spelling, and
  unlike the membership tests that REFUSE, that one REWRITES. An ordinary function whose parameter is named
  `_census` and which branches on that object's `enabled()` had its branch turned into `if False:`, so the twin
  returned 1 where the source returned 101 while `verify()` reported no problems. It now asks the same resolver.
  Because `verify()`'s structure check re-derives the twin with the SAME transform — so a transform defect
  reproduces identically and reads clean — the regression EXECUTES both modules rather than comparing trees.
  **Two further defects were found by exhausting those classes rather than fixing the cells the reviewer named:**
  the import-restoration test read a hand-written `("_census", "census")` sitting two lines below the DERIVED
  alias set, so a module importing the census under any other name lost its import and produced a twin that
  died with `NameError`; and a packaging gate written in round 8 to catch dead `collected/` citations matched
  only the prefixed spelling, so it saw NOTHING on the README line that names eleven such files — three of them
  stale. **The round's own class:** every one of the five is a literal sitting next to the derivation that
  should have produced it, or a property established at one of a question's two sites.
  **The gate that enforces the scope rule was itself rewritten three times in this round, each time because a
  mutant walked through it.** It began as a blanket text ban on the name question's spelling anywhere in the
  transform, which refused the legitimate census-alias lookup. Replaced by an AST property, it enforced "if you
  ask a resolver question, ask the right one" — a property satisfied by NEVER ASKING, so a function reading
  `self.declared` and calling no resolver at all passed, which is round 7's original defect verbatim. Inverted
  to "consulting `declared` obliges the site question", it then had to exempt the two visitors that consult it
  only to REFUSE; the first exemption ("every read sits in an `if` whose body is a raise") was defeated by
  inverting the guard clause, which refuses on absence and then acts on presence by fall-through. The exemption
  is now the invariant it was always standing for — consulting `declared` may REFUSE but never AFFIRM, so every
  statement outside the refusal guard must be a bare passthrough return — and a refusal guard's test may not
  call a method, which closed a survivor that acted through a side effect in the test. Eight attack shapes are
  driven against it, with the legitimate visitors as the acceptance control.

- **Fixed: the census's round-7 implementation findings — a validation reports its own incompleteness, names
  resolve through the language's scope analysis, the comparison gates every run it rests on, and the twin
  verifier establishes preservation (specs/0042, round 8; four findings, all in the ACCEPTANCE CHECKS).** The
  round-7 reviewer stated it explicitly: the reproductions demonstrate weaknesses in the checks and do NOT show
  that any shipped trace or the regenerated copy is wrong. No product code changed. *F1, validation:*
  `census_table.validate_report`'s registry reconciliation ran only when the caller supplied the scan's map, so
  the ordinary two-argument call returned NO refusals for a declared, already-loaded site whose registration had
  been deleted. The reconciliation stays optional — the map is an observation of a running interpreter, and a
  reviewer validating the shipped report in a throwaway cannot supply one — but its absence is now a refusal in
  the list every caller already reads, naming which argument was missing, so `[]` keeps meaning "validated,
  completely" and no caller had to change. What a report CANNOT SPEAK FOR moved to its companion
  `insufficiency`, one entry per id: an unmeasured row and an out-of-reach site say the same thing about the
  claim "every declared site was exercised", and an evidence run asserts both functions empty. *F2 and F4a,
  name resolution:* the binding scan and the twin transform each decided "is this NAME the declared site?" by
  enumerating the forms that bind a name, and the reviewer found the rungs the enumeration had not reached — an
  assignment expression and a `match` capture both read as bound while the site's counters never moved, and a
  function PARAMETER shadowing a site name had its own ordinary method call rewritten. Both now ask one shared
  resolver built on `symtable`, CPython's own scope analysis, which covers the binding grammar by construction;
  the set of nodes that even get a scope is derived from the interpreter, since PEP 709 inlines comprehensions
  from 3.12 and CI runs 3.10 through 3.13. `nonlocal` on a site now RESOLVES as a shadow instead of being
  refused. The refusal that a site is not REBOUND at module level — the guarantee that makes "this name is the
  module binding" evidence about the site OBJECT — kept an enumeration of its own one layer down, and six
  spellings defeated it because none is an `ast.Name` in a `Store` context: `import os as S`,
  `from os import path as S`, `except Exception as S`, `del S`, `def S()`, `class S`. It now reads the module's
  COMPILED code object, which binds a name by exactly four opcodes and is therefore total over syntax, plus
  the NESTED code objects for the bindings they perform against module scope. *(Round 8 read that second half
  through a `symtable` predicate pair; round 9 replaced it — see the entry above. This text describes what
  ships.)* There is now no hand-enumerated walk anywhere in
  that refusal: a third reading written in the same fix, comparing the two, was deleted once it was shown to
  refuse correct code (a dead `if False` branch the compiler folds away, and a bare annotation), and the AST
  walk it cross-checked went with it. Checked against a 46-case matrix — 29 refusals, 17 acceptances, since an
  over-strict refusal refuses correct code and three drafts of this fix did — on all four interpreters. A
  site bound in two mutually exclusive branches is refused rather than analysed, including the
  `if TYPE_CHECKING` import idiom, because a static reading cannot tell a dead branch from a live one unless
  the compiler folds it. **Also in this round, and it is about the specification rather than
  the code: 0042 is bumped v9.2 → v9.3 because THREE DIFFERENT DOCUMENTS had shipped or would ship under one
  version name.** The round-6 and round-7 packages each carry a file called
  `0042-exercised-guarantees-SPEC-v9.2.md` and they differ from each other and from this tree — each round
  added an implementation note under the accepted version and nothing moved the identity, so a reviewer
  holding two copies had two files with one name. No frozen invariant's text changed and the bump does not
  re-open the design: what carries acceptance is `Spec-Status: accepted` and round 5's verdict, and the
  accepted text remains v7. The precedent was already in the cell — v9, v9.1 and v9.2 were all
  post-acceptance corrections. *F3, comparison:* a control run's pytest exit is gated like
  any other run's (a failed control still gave exit 0); the exits-per-function guard is replaced by the
  site-to-exit ASSOCIATION, since two sites sharing one return satisfy a count of two exits for two sites; and
  the gates are computed BEFORE `verdict.json` is written, which is why every shipped verdict lacked the gates
  both READMEs said it carried. *F4, the twin:* `verify` requires its source (the harness had been calling it
  without one, so the preservation half was dead code in every run), compares the file set both ways, compares
  program structure by re-deriving the transform and diffing the AST, and checks the manifest's before and after
  hashes — it had verified clean after a `return False` became `return True` and after a module was deleted
  outright. The derivation itself is unchanged: 162 sites, 302 fires, 152 consults, 4 bypasses across 31
  modules, byte-identical to the round-7 seal. **The round's own class, swept rather than patched:** three of
  the four findings are a check whose scope depends on an argument and reads clean when the argument is absent,
  and the same shape had migrated into the function written to fix the first one. Every public function in the
  0042 evidence layer with an optional argument was read against two rules — an optional argument is safe when
  its default is the COMPLETE behaviour, and a default that supplies an INPUT is safe when that input is BOUND
  to the run rather than merely located — leaving five safe, two reporting their own incompleteness, and a test
  pinning both.
- **Fixed: the census's round-6 implementation findings — a measurement that fails is counted as a failure,
  a consultation means the site's own condition ran, a declared id that never registered is refused, the
  INV-7 comparison decodes what it compares, and the twin transform refuses what it has not established is
  instrumentation (specs/0042, round 7; seven findings R6-1..R6-7).** *Counting (R6-1):* a trace recorder or
  decline classifier that raises is CONTAINED — the decision is returned as made, `errors` counts it, the
  exception's type name is recorded per id (`Site.failure_kinds`, the snapshot's `measurement_failures`), the row
  reads UNMEASURED, and a report carrying such a row is structurally valid but evidentially INSUFFICIENT
  (`census_table.insufficiency` names the ids and kinds). *Consultation (R6-2):* each sequential site is
  consulted immediately before its own condition (the gate's three scoped-assertability checks, the MCP author/
  trust split, the as-of resolver, the graph's absorption gate, the scope policy's per-member checks,
  portability's seven refusals — a consult statement before the check where a bracket would span other sites),
  and the four hot `Edge` predicates consult BEFORE evaluating when the census is on, through ONE `return`
  statement for both paths. *Registration (R6-3):* the snapshot carries what REGISTERED; given the scan's
  id → module map and the loaded product modules, a declared id whose module is loaded but never registered is
  REFUSED as a missing registration, one whose module was never imported is NAMED as out of reach, and a
  registered id the scan maps to an unloaded module refuses the scan. The loaded-module observation is the
  EVIDENCE layer's (`census_table.loaded_product_modules`): specs/0031 refuses `sys.modules` and `vars()` inside
  src, so the product does not pretend to make it. *The scan (R6-4):* a site name resolves through enclosing
  FUNCTION scopes (a closure sees its enclosing function's binding; a class body is not a scope; `nonlocal`/
  `global` on a site name is refused as unresolvable), and the live registry reconciles against the scan with
  nothing out of reach after every product module is imported by file — `pkgutil.walk_packages` had skipped
  `store/`, a namespace package. *INV-7 (R6-5):* the observer records (symbol, EXIT STATEMENT ordinal, label)
  — three bytes, the exit statement read from the frame's line events, because CPython 3.12 attributes the
  return after a `with` block to the `with` line and every census-enabled hot predicate had read as an implicit
  exit; the harness decodes every arm through its own dictionaries, compares canonical records, prints a
  canonical digest per arm, and its exit status requires every arm's pytest exit and every cross-check
  (`final_status`, gates named); the test-boundary side file is written at the record width (it was still at the
  two-byte width, so every per-test segment was cut at 1.5× its index); and the control pair is run for EVERY
  arm, a test excluded by name when two runs of any one arm disagree on it — the first round-7 run found
  wall-clock noise in one 0029 acceptance-corpus test that only the healthy arm's slower timing sampled and
  a reference-only pair could not. Research's pre-dispatch pass on the fix (two mutants, both taken): the exception path records a
  raise that came from a callee as PROPAGATED even when a return statement was walked first (`try: return` /
  `finally: boom()` had read as an exit at return #0 — the statement-line witness is the return path's only); and
  the loaded-module observation decides by file alone, since a key test could only turn a refusal into a benign
  out-of-reach listing. Its second pass (a mutation campaign over the twin transform's refusals, and the control
  pairs as a sample): four refusals no test drove are now each pinned to their own message (`global` naming a
  site, the consult statement on an undeclared name, a bypass whose else branch does work, a fire with no
  decision); and the INV-7 exclusion list is STANDING and NAMED (`specs/evidence/0042/inv7_exclusions.py`, each
  entry with its cause — the 0029 acceptance corpus's wall-clock step is its one entry), the transcript reporting
  standing exclusions and newly non-reproducible tests apart, a new one failing the harness's exit as a finding. *The twin (R6-6):* the transform rewrites only NAMES bound by `declare_site` in
  the same module and only the recognised shapes (`return/raise X.fire(v)`, `name = X.fire(name)`, `with
  X.consult():`, the statement `X.consult()`, the `if enabled:` bypass whose body is assignments/a return and
  whose else is assignments), refuses anything else by line, keeps the bypass DEAD rather than deleting it so
  exit ordinals survive, and writes `twin_manifest.json` (source hashes before and after, every count) that
  `verify()` re-derives. *Exact deltas (R6-7):* the surface-driven sites assert deltas EQUAL to counts derived
  from the product's own control flow (grounded (4, 4, 0): the claim plus `_fit_to_budget`'s two sums; variant
  (2, 1, 0); eligible, claim, digest-overlap (1, 1, 0) / (2, 1, 0)); the reviewer's doubled-increment control
  now fails every one, and the superseded `fired >= 1 and consulted >= fired` form is kept inside the test as
  the mutant it could not kill. Every regression was run RED on the round-6 pin with only tests/ replaced,
  then GREEN on this tree (twelve of fifteen red on the pin; the three that pass there are the R6-7 mutant
  campaign and an exits-per-function guard, whose defect was in the old assertion, not the tree). **Cost at
  the shipped default, re-measured** (census OFF; the round-6 pin against this tree on the ten-conversation
  store migrated v14 → v15, 180 timed recalls per run, alternated twice): medians 144.2 / 144.3 ms against
  146.0 / 144.4 ms — inside run-to-run noise; the one-return form costs nothing measurable. Regenerated: the
  0042 inventory (787 → 783 candidates: the four bypass returns folded into one return each), the review keys
  (300 entries over 162 ids), reviewed points and declaration; the 0031 LIVE attribute partition; the INV-7
  four-arm transcript (IDENTICAL across four arms over 860 tests, 75,569 records per arm, one canonical digest, 1 excluded as non-reproducible between two runs of one arm). No decision's behaviour changes.
- **Fixed: the 0043 canned-pipeline test assumed a git checkout (specs/0043; found by research's offline leg on the
  0042 round-6 review package).** The harness recorded `git rev-parse HEAD` verbatim, so a report generated in an
  extracted archive carried an EMPTY pin and the test asserting a 40-hex there was green in every checkout and red
  for the reviewer. The harness now declares `unpinned (not a git checkout)` when git cannot answer, the test
  accepts exactly the two honest values (a commit in a checkout, the declared marker elsewhere) and refuses an empty
  pin, and the committed run's own pin test still requires the commit. Evidence and tests only; no product change.
- **Fixed: the 0042 runtime leg ran 143 of its 157 declining executions, and one census id consulted twice per
  decline (specs/0042, round-6 pre-seal).** The leg's parametrised id list was evaluated above its last three
  entry blocks, so the fourteen entries below it (0041's tranches 3–5) never ran under the exactly-one delta
  assertion while the completeness test, which compared dict keys rather than the parametrised set, stayed
  green at every pin since 0041's tranche 3. The ids are now frozen after the last block, asserted equal to
  the dicts, and a static guard refuses an entry block below the freeze. One of the fourteen,
  `store.redact.target`, bracketed two decision points under one id — 0041 §4a's exactly-one-target and INV-5's
  unknown-or-cross-user — and consulted twice per decline; they are two ids now (`store.redact.both-or-neither`
  beside `store.redact.target`; 162 declared, reviewed, reconciled, exercised). Found by generating the per-site
  decision trace the round-5 verdict asked for at implementation review. No behaviour changes.
- **Changed: the two delayed writers make their read and their publish one transaction (specs/0041
  §4e, tranche 5).** The embedding upsert takes the database write lock (`BEGIN IMMEDIATE`) before it
  reads the edge it checks its digest against, so a second connection's redaction cannot land between
  the read and the insert; a writer that cannot take the lock within the busy timeout is refused loudly
  (the 0007 lock-refusal form, a declared site), never skipped. The wiki compile reads the store version
  BEFORE its inputs and publishes through one conditional statement, written only if the counter is
  unchanged — a store that moved during the slow compile (a redaction, any write) is never published
  over; the compile returns its text for that call and the next read recompiles. `Store.set_wiki` now
  returns whether the row was written. **Who must act:** hosts that IMPLEMENT `Store` and cache a wiki
  must return False rather than publish over a moved store; everyone else changes nothing. The
  round-2 two-connection regression (a stale vector stored under the original digest while the live
  edge was the tombstone) now refuses inside the window and stores nothing; the round-1 wiki race
  (cleared content republished as current) is refused by the statement.
- **Changed: export format 12 → 13 — the redaction record travels, and import applies it under the
  §4g contract (specs/0041, tranche 4b).** An export from a store holding any redaction record carries one
  `{"record": "redaction", ...}` line per record (the attestation: target, the carriers treated, the marker
  version, the vocabulary reason, the SOURCE identity — origin, source user, source event — never a content
  digest) and is stamped 13; a store without one still exports 12, byte-identical to before. **Who must act:**
  operators whose exports may reach an older Veracium — a 0.26.x reader REFUSES a 13 file outright (the
  refuse-don't-drop rule: a reader that dropped the notice would import the record un-redacted, the exact
  harm the contract exists to prevent); upgrade the reader, or redact after import. On import: a notice
  whose record is in the file or already held is applied IN THE SAME TRANSACTION as the record (the
  destination attests it; its own journal closes the record with a `redacted` event; an ordinary write may
  not repopulate it); a notice whose record the destination does not hold is a STANDING notice (a
  redaction record with no event), and the record is redacted on arrival — so the two import orders
  reach the same state; a held DIFFERENT version is redacted anyway and the result flags it
  (`inconsistent_notices`); an invalid notice refuses the whole import with nothing written; two notices
  under one source identity with different bodies are an integrity refusal; repeat imports are idempotent
  by source identity; a `user_id=` remap moves the notice's target with the record's minted id; a marker-
  carrying record arriving with NO notice is admitted as an UNATTESTED marker and listed in
  `unattested_markers` (no reader treats it as redacted, and it stays writable). A file declaring a
  version below 13 that carries notices is refused. The doctor reports a standing notice as information,
  never as a missing-target error. The receipt of a witnessed redaction is `reconstructed=True` with
  reason `imported_notice` (this store was told the source redacted it). The result dict gains
  `notices_applied`, `notices_standing`, `notices_existing`, `inconsistent_notices`, `unattested_markers`.
- **Changed: redacted records leave every read surface (specs/0041, tranche 4a).** By the attestation
  record, never by marker bytes: an attested-redacted edge or episode is absent from `recall`'s subgraph,
  episode list and contested groups, from the compiled wiki's input, and `describe_procedures` reports a
  redacted procedure as withheld with outcome `redacted` (a hidden one stays hidden — the existing
  visibility restrictions are unchanged). An as-of read of an attested-redacted record reports the new
  status `REDACTED` for any T — never `MALFORMED`, which would claim damage — and
  resolves `NOT_RETURNABLE` with the tag `redacted-excluded`. Accepted 0030's status set gains the eighth
  status (0041 §11.4). `Store.redacted_targets(user_id, kind)` is the read the surfaces share; a host store
  without redaction returns the empty set. A row that merely holds the marker bytes (an unattested
  marker) is treated by every reader exactly as before. **Who must act:** nobody has to; hosts that
  consume the as-of status set or the describe outcome set see one new member in each.
- **Added: targeted redaction — `Memory.redact(user_id, *, edge_id | episode_id, reason) -> RedactionReceipt`
  (specs/0041, tranche 3).** Removes one record's CONTENT and keeps its structure, in ONE store transaction
  over the accepted treatment map: the content carriers become the marker byte string, `outcome_counts` is
  cleared, a prose reason becomes the registry value `redacted` (an absent or registered one is untouched),
  a prose episode kind becomes the marker (a recognised kind is kept), the duplicated edge columns follow the
  json, the confirmation's request digest and the refusal rows' copied relation become the marker, the
  ledger's identity and evidence-ref digests are cleared, the embedding rows are deleted, every prior journal
  event's state is tombstoned and a `redacted` event is appended with the reason, an episode gets its
  `episode_event` row, and the wiki cache is dropped. A `redactions` row ATTESTS the treated fields: a repeat
  call writes nothing and returns the original receipt with `repeated=True`, and an ordinary write to an
  attested record is refused (INV-11) while a row merely holding the marker bytes stays writable. A
  redaction never changes a derived disposition (a quarantine relation's edge stays quarantined through its
  disclosure; any other change refuses with nothing written), never deletes a row, and is not an
  entitlement operation (`forget` erases). `reason` is a closed vocabulary (`subject_request`,
  `operator_policy`, `erroneous_capture`, `legal_obligation`, `imported_notice`), refused at the operation
  and at the journal. The receipt never carries a content digest, reports `receipts_complete=False` with the
  receipt domains it cannot vouch for, and NAMES the derived records that may still carry the content
  (ledger survivors, consolidation outputs) so the caller can act on them. `why` renders a redacted edge as
  "redacted" and never fails; `veracium.store.base.Store.redact` refuses by default, so a host store that
  has not implemented it cannot pretend content was removed. **Who must act:** hosts that IMPLEMENT
  `Store` and want the operation add `redact`; everyone else changes nothing. Two accepted-0029 amendments
  ride with it (0041 §11.4): the journal kind vocabulary gains `redacted`, and `redact` is the one path
  that updates a journal row (`state` only, the tombstone). Measured on the frozen pre-restriction store
  (specs/0041 §4h(iii)): every transition claim of the treatment map, the seven §6 invariants with their
  planted mutants, and the mutant campaign at 18 of 18.
- **BREAKING for existing stores — schema 14 → 15: the episode journal and the redaction
  attestation record (specs/0041, tranche 2).** Two additive tables and their indexes:
  `episode_event` (the episode-side transaction-time journal, `edge_event`'s shape — an episode
  redaction will be durable in the record AND visible in the journal) and `redactions` (THE
  attestation record: a field is redacted iff a row names that record and that field; the marker
  bytes alone confer nothing). No data step — no redaction and no episode event exists before the
  tables do, so every row crosses byte-identical. A store created by ≤ 0.26.1 must be migrated
  offline before this build opens it — `veracium migrate --db X --i-have-quiesced --backup REF`
  (the orchestrator now migrates v14 → v15; a store further behind takes the one-call library
  path `veracium.store.migration.migrate_store`). **Who must act:** every operator with an
  on-disk store. Hosts that implement `veracium.store.base.Store` need nothing yet: no operation
  writes either table until `redact()` lands (tranche 3). Also: `migration.unattested_marker_report(store)`
  enumerates every stored row holding the marker byte string in a field with no attesting record —
  admitted, neither refused nor quarantined (§4b, ruled v7) — named per row AND per field; on the
  frozen pre-restriction store it names the two planted rows and nothing else. `forget_user` erases
  both tables for the user; the doctor reports a redaction record naming a target that does not exist
  and an episode event naming an episode that does not exist as `refs` errors. The shipped release
  record (`store/evidence/legacy_stores.json`) re-derived at the commit; the migrated-shape record
  carries v15 like the additive bumps before it.
- **Changed: three write-path refusals ahead of targeted redaction, and `redacted` as a registered
  invalidation reason (specs/0041, tranche 1).** A non-redaction write may no longer introduce the redaction
  marker byte string (`\x00veracium:redacted\x00`) into an edge or an episode, on any persistence path
  (INV-11's mirror); an edge carrying the quarantine relation must carry the QUARANTINED disclosure (§4h(i));
  `Episode.kind` is closed to the recognised operational kinds (`interaction`, `outcome`) at the write path
  and at import — never at read, so stored prose kinds still load. BREAKING for a host that wrote those
  shapes through the store or an import: the write now raises `ValueError` naming the rule; ingest is
  unaffected (it never produced them). `redacted` enters every reason registry (dispositioned `drop`;
  as-of `excluded`; names no successor; resolves NOT_RETURNABLE) ahead of the operation that will produce
  it. Each refusal is a declared 0042 census site. Consumers whose stores are written only through
  `remember`, `correct`, `confirm` and import of their own exports see no change.
- **Added: the refusal harness RUN — both arms against a model, every rate with its denominator
  (specs/0043, tranche 2).** `specs/evidence/0043/run_harness.py` executes the accepted harness end to
  end: a blind examiner (a model seeing only the examiner view) authors the questions; the trust class
  attaches afterwards from provenance; non-blind or rowless questions are excluded and counted; the
  interpreter is calibrated on the reference cases first; each question runs the shipped answer path
  and the captured baseline arm against the real model through the capturing boundary; the ledger's
  six checks pass with both sources captured; the report states refusal rates with their denominators
  per arm and per class, `UNRESOLVED` by cause, `absent` as NOT PRESENTED, and every answer verbatim,
  pinned to the commit it ran against. `run_report.txt` and `run_ledger.json` are the committed run;
  `tests/test_0043_run.py` drives the pipeline on a canned model without spend and re-derives the
  committed rates from the ledger and refuses a report whose interpreter has moved. Measured on the first
  run (24 blind questions, `claude-sonnet-5` at the gate; re-scored after the run's own answer shapes were
  added to the reference cases): shipped arm refusal rate 10/24 — quarantined 7/7, untrusted 3/3,
  answered-on-trusted 14/14; baseline arm 0/24 with four anomalies where it asserted the untrusted fact.
  The interpreter is the deterministic fact-string matcher at clause level; its limit is stated in the spec
  and every answer is in the report. No product behaviour changes.
- **Changed: the refusal-harness report names its calibration gate and its independence, and the committed
  run is a fresh question set scored with the frozen interpreter (specs/0043, tranche 2b).** The calibration
  line splits `UNRESOLVED` on the reference cases into the ambiguity control (expected) and known answers the
  judge could not resolve (an unexpected one refuses the run); the report states that the reference cases
  include shapes learned from the first two runs; run 3 — questions authored after the interpreter was
  frozen — is the committed run: shipped arm 11/24 refusals (quarantined 8/8, untrusted 3/3, trusted answered
  13/13) against a baseline of 2/24. Runs 1 and 2 are kept beside it. The spec's limits gain the absent
  class, unreachable by a blind examiner, and the small-class caveat. No product behaviour changes.
- **Added: the gate's rendering seam, and the refusal harness's baseline arm captured at its own
  model invocation (specs/0043, tranche 1).** `gate.render_gate_input` now composes the exact (system,
  prompt) the assertion gate sends to the model, and `gate.answer` takes a harness-only `render=` that
  replaces it for one invocation — a seam, not a mode: the shipped path always renders through the
  default and no product module passes the parameter. The 0043 harness's baseline arm is no longer a
  construction: it is a second invocation of the gate over the same selection through the same injected
  boundary with the stated transform at the seam, asserted equal to the oracle; a departing invocation
  or an untransformed one refuses, and the harness ledger refuses any rate while the comparison arm is
  constructed or its capture source undeclared (check 6). Closes the one item the 0043 acceptance left
  owed. Product behaviour unchanged.
- **Added: INV-7, the census's observation-only guarantee, as a FOUR-ARM decision-trace diff
  (specs/0042, tranche 6b).** An independent observer (`specs/evidence/0042/inv7_observer.py`, a pytest
  plugin) wraps every enforcement function the declaration names — 95 of 102; the 7 nested inside another
  function are excluded by name — and records one content-free (symbol, decision) per exit. The harness
  (`inv7_harness.py`) runs the suites that reach the sites — 29 files, derived: the spec-named 0027, gate,
  ingest and schema files plus a greedy cover of every id the whole suite reaches (145 of 147; the two
  others only the 0042 runtime leg exercises) — under counters healthy, forced to error, disabled (the
  shipped default, the bypass path) and an UNINSTRUMENTED twin exported from the commit the tranches began
  from, and compares the traces PER TEST after a control pair (the reference arm run twice) has named any
  test whose own trace is not reproducible. The committed transcript reads IDENTICAL over 859 tests in all
  four arms, one digest, none excluded; the census's fired sequence is a subsequence of the observer's in
  both census arms; the failing arm is UNMEASURED on all 145 ids it reached; the twin registers no site.
  The control pair found a test whose store file was named after an object address (a reused address
  reopened an earlier build's store); it is fixed. An in-process miniature replays the runtime leg's 147
  declining executions under three arms in the suite. No behaviour changes.
- **Changed: every predicate-helper decision in the census review names its consumer (specs/0042,
  tranche 6a-bis).** Research's second read of the review's NOT half found that all 43 `predicate-helper`
  rows shared one reason — "the consumer's site is the enforcement point where one exists" — a sentence
  true whether or not a consuming site exists, so a helper consumed by a declared site and one consumed by
  nothing read identically. The generator now derives each helper's consumers from the source and writes
  them into the reason: the consuming functions that carry a declared site, with the site ids; the
  consumers that carry none, named; or, for a helper no product function references, a reading the review
  states by hand (the `==` operator; a public meter read; a harness-only export). A helper with none of the
  three refuses generation, and the test runs that refusal. Decisions unchanged; the escape clause is gone
  from the class text. No behaviour changes.
- **Added: the census's REVIEWED set and DECLARATION exist, and the four sets reconcile on the real
  tree (specs/0042, tranche 6a).** Every one of the 752 discovered decision candidates carries a
  decision — 276 enforcement candidates bound to 147 site ids, 476 not (argument-check 97,
  internal-invariant 239, control-flow 88, predicate-helper 43, cli-usage 9) — in a review file
  GENERATED from the authored semantic review with, per decision, the candidate's stable key, its
  line and the statement text it decided about; the spec-side declaration (id, governing spec,
  invariant, file:symbol) is generated from the same review. DISCOVERED, REVIEWED, DECLARED and
  INSTALLED reconcile with zero refusals, and every refusal is shown live against an emptied or
  altered input. No behaviour changes.
- **Added: the census binds the store's forty-six sites (specs/0042, tranche 5) — every enforcement
  point the semantic review named is now a declared site (147 ids).** Migration's unsupported-base and
  duplicate-chain refusals; revocation's unknown-state, ordinal-collision and integrity refusals and the
  sweep's two row validators; the store-open refusals (shape, runtime, lock, version, legacy) and the
  runtime gate; and sqlite's journal, read-visibility, immutable-field, flattening, contribution,
  transaction-lock, consolidation, outcome-chain, supersession, correction-authorisation, import-plan,
  confirmation, deletion, read-fence and embedding refusals. The runtime leg executes one declining
  decision at every id. No behaviour changes.
- **Added: the census binds thirty-three more sites (specs/0042, tranche 4)** — the scope policy's
  validator and revalidation, the absorption closure walk, the prune's cycle refusal, membership's
  and classification's refusals, the filter grammar and its application, the import linkage
  reconstruction and export linkage refusals, the scope view's construction refusals and its two
  lenses, and portability's export and import refusals (the outcome chain, the file envelope, the
  agreement record, the origin requirement, the record shape, the retry bound and the preflight).
  101 sites are bound in all. No behaviour changes.
- **Added: the census binds forty more sites (specs/0042, tranche 3)** — the supersession
  receipt boundary and replay mismatch, the absorption gate's three scope refusals, the
  correction planner's two refusals, the source-revocation verdict, the semantic-duplicate keep
  rule, strict redundancy, the render collapse, the proactive variant and eligibility verdicts,
  ingest's three refusals, the procedure's source-id requirement, the procedural gate's two
  predicates, the registry's two refusals, the MCP closed set, eleven `Memory` refusals, the
  diagnostics send consent and telemetry's five consent gates. 68 sites are bound in all; the
  runtime leg executes one declining decision at every one. No behaviour changes.
- **Added: the exercised-guarantees census binds its first 28 product sites (specs/0042,
  tranche 2)** — gate (the procedural exclusion, the three scoped-assertability restrictions, the
  partition), schema (`Edge`/`Episode` `quarantined`, `use_only`, `valid_now`, `assertable`,
  `Episode.active`), the compiler's grounded-input filter, the grounding downgrade, authority's
  `permitted`/`self_assertion`, and the as-of adapter, classifier, recall and resolver refusals.
  Each decision is returned through its declared site; a predicate site declares its declining
  value so `fired` counts only declines. **Cost at the shipped default (census off), measured on
  the rebuilt ten-conversation store, 180 timed recalls per tree, the two trees run adjacently and
  alternated:** with the plain idiom at every site, the pre-tranche tree against this one read
  145.3 → 154.2 ms and 143.7 → 146.0 ms — two alternations, +1.6 % and +6.1 %: the cost is real
  (both positive) and its magnitude is not established at two alternations; an earlier single
  adjacent pair had read +4.5 %. A recall executes 12,527 census decisions and 12,385 of them are
  the four `Edge` predicates, so those four skip the census machinery when it is off — the
  structural reason: a disabled feature should not execute its machinery on the hottest path — the
  decision computed once and the count taken after it (a predicate that raises is therefore
  uncounted at those four, and both paths are asserted to raise and return identically). With the
  bypass, alternated twice: 149.9 / 151.1 ms against 150.5 / 147.6 ms — inside run-to-run noise.
  No behaviour changes; every site's tests still pass unchanged except one 0037 text pin re-pinned
  to the predicate's conjuncts.
- **Fixed: the reference Anthropic provider refuses an empty completion instead of returning
  `""`.** With the default `max_tokens` (4096) a hard prompt can spend the whole budget inside a
  `thinking` block; the API call succeeds with `stop_reason == "max_tokens"` and no text block, and
  `AnthropicComplete` returned an empty string with no signal (found by research, reproduced against
  the SDK: block types `['thinking']`, 4096 output tokens, returns `''`). Every role reads emptiness
  as a finding — an empty distill is "no triples", an empty compile is an empty wiki, and an empty
  gate answer is what an abstention looks like, on the one surface where a negative result is a
  product claim. Now the provider raises `veracium.llm.anthropic.EmptyCompletion` (a `RuntimeError`
  carrying `stop_reason`, `output_tokens`, `block_types`, `max_tokens`, `model`) whenever no text
  block came back, whatever the stop reason; a cut-off answer that has text is still returned. The
  assembly is one pure function (`text_of`) the provider renders through, tested without the SDK.
  **Who should take this:** anyone using `AnthropicComplete` on prompts long enough to think about —
  raise `max_tokens` where the error names it. **Consumers, swept:** `Memory.answer` records the
  error and re-raises; lifecycle pools classify it `llm-error`; the selfcheck reports it per check;
  ingest and compile propagate it like any provider failure (the extraction retry path records it
  as a retry with its cause, never a second call). No consumer turns it back into silence.
- **Fixed: the recall budget report now states the contested block's losses, and appears
  whenever the block truncated.** The `[budget: …]` line was built from the detail fitter's own
  counts and emitted only when the fitter itself dropped something, while the `CONTESTED
  FUNCTIONAL FACTS` block is charged upstream and its losses reached only the `truncated` flag.
  **Measured, on the rebuilt ten-conversation store at share `0.5` (60 questions):** before the
  fix 54 of 60 truncated contexts carried no budget line at all and the 6 that did read
  `0 SAFETY` while 71 contested groups were withheld on every question — a wrong number in the
  report 0012 I10b writes so that overflow is never silent; after the fix 60 of 60 contexts
  carry the line, each stating `71 contested groups / 54 contested values`. The line gains those
  two figures as their own class (`SAFETY` keeps its meaning) and is emitted on the block's own
  flag, so the flag and the visible report cannot disagree. **Who should take this:** anyone
  whose model reasons over contested facts — the model now sees how much of the contested
  surface it was not shown. **What moved with it:** the recall report reserve is 40 tokens (was
  32) to carry the longer line, so the recall floor is 280 tokens (was 272); a host `token_budget`
  or `query_context_tokens` between 272 and 279 is now rejected at the floor with the derivation
  printed. Beside it, the fitter's four within-class admission orders (warnings most-overdue
  first, related and unrelated; commitments nearest-first; episodes newest-first) were found
  reversible with no 0012 test failing; they are pinned now, one mutant per sort. Both report
  lines now come from one named builder each, and a test builds them with every count at its
  bounded maximum and asserts each fits its reserve, so the next class added without the
  reserve raised fails loudly. 0012 carries the amendment.
- **Changed: the contested-fact renderer is capped at a share of the recall budget
  (`MemoryConfig.contested_render_share`, default `0.5`).** The `CONTESTED FUNCTIONAL
  FACTS` block had first claim on the whole token budget, so on a store with many
  contended functional facts it starved `RELEVANT DETAIL` of the lines recall had ranked
  first: measured on a ten-conversation store, 99.4% of the rendered context was the
  contested block and the answer-carrying record reached the model in 8 of 19 answerable
  questions while ranking 4th of 834. The block now takes at most the configured share; its
  first line stays unconditional (the higher-authority prior is never dropped, I6a); the
  remainder goes to detail; `1.0` reproduces the previous behaviour. **Who should take
  this:** anyone whose recall context is dominated by contested blocks. **What it cannot
  fix:** a carrier inside a contested group is removed from detail by construction — that is
  the functional-relation vocabulary question, which goes to its own spec round. The
  acceptance measurement (answers reaching the rendered context at share 1.0 vs 0.5 on one
  rebuilt store, in one run) is stated in the ledger with its own figures; the store the 8/19
  was measured on no longer exists and is not reproducible. **Measured on the rebuilt store**
  (ten LoCoMo conversations through the shipped extractor; 60 questions; one run per share;
  the store carries 103 live contested groups and recall delivers all of them on every
  question): answers reaching the rendered context 7 → 11 → 12 of 19 at shares 1.0 / 0.5 /
  0.25, every gain a previously starved detail line. **The cost, stated:** contested group
  lines rendered per question 64 → 32 → 16 of the 103 delivered (highest-priority first; the
  rest dropped), the block's share of rendered characters 99% → 52% → 36%; every context
  was truncated at every share, so the cap trades the tail of an already-cut contested list
  for detail. **What the cut takes, stated:** the block renders its groups in `(subject,
  relation)` order and the budget cut takes that order's tail — at every share, `1.0`
  included, so this release changes how far down that order the block reaches, not what
  decides it (on the rebuilt store the tail was every subject from `person:Gina` on, on every
  question). The block is query-independent by design (0003 §4c-ii: it replaces the broad
  channel the wiki used to provide), so relevance-ordering it is NOT the fix; what order a
  static-plus-truncated block should take is open under 0003. **A drop the report does not
  state, measured:** the `[budget: …]` line counts detail, SAFETY claim lines, clamps, wiki and
  episodes, and the contested groups the block drops are in none of its figures; on the same
  store at share `0.5`, 54 of 60 truncated contexts carried no budget line at all and the 6
  that did reported `0 SAFETY`. That is a pre-existing gap against 0012 I10b (39 groups were
  dropped silently at `1.0`), widened by this default; the count goes into the report as its
  own change. Until both land the `0.5` default is a bound the owner set, not a tuned figure.
- **Added: the exercised-guarantees census module (`veracium.census`, specs/0042 — accepted at the
  design level, external round 5; implementation begins here).** An enforcement point declares a
  site at module level and expresses its decision through it (`with SITE.consult(): … raise
  SITE.fire(...)`), so the count and the decision are one call. Counters are process-local and
  atomic per id; `fire()` returns the decision unchanged (observation only, INV-7); the report
  carries ids and integers only (INV-8) and assigns one of six statuses per declared id from the
  spec's state table, carried verbatim and asserted equal to the spec's own parsed table.
  **Opt-in, default off** (`MemoryConfig(census_enabled=True)`): off, every site is a no-op and the
  report reads `DISABLED` per id. No enforcement point is bound in this change — the sites land
  module by module under the same trailer, with the review of every discovered candidate, the
  declaration and the four-set reconciliation closing the tranche.
- **Fixed: the release-migration orchestrator's `unsupported-base` diagnostic is
  derived from the store, not recited.** `veracium migrate` on a store more than one
  schema version behind refused correctly but said "store resolves to base v6" for
  every base 7–12 and sent the operator to releases for a v8 head (the 0019 rider's
  literal sentences, unchanged while `SCHEMA_VERSION` moved 8 → 14; found by the
  workflow platform's 0.13.0 → 0.26.1 upgrade, store 9 → 14). The diagnostic now
  names the resolved base, the mint base, the number of one-version rungs a CLI
  ladder would need and — from the shipped release record — which rungs the record
  names no release for (v2, v5, v6, v7, v10, v11 today: stamp-only bumps and releases
  probed without a schema version, so the CLI ladder cannot be planned from the record
  alone), and the
  offline library route that applies every step in one call
  (`veracium.store.migration.migrate_store`). Outcome, facts and exit code are
  unchanged; only the sentence. Tested exhaustively over every base 1..HEAD-2, with
  the superseded literal text kept in the suite as the mutant the property must fail
  on. Accepted spec 0018 amended in place (the diagnostic is derived; the rider's
  ladder sentences are historical).

## 0.26.1 — 2026-09-18

**Documentation, evidence and process only — no behaviour change.** Nothing under
`src/veracium` changed between the `v0.26.0` tag and this one except
`store/evidence/legacy_stores.json`, the record that names the commit v0.26.0 was cut
from. The wheel's code is the wheel you have. **Who should take this release: nobody
has to.** A 0.26.0 deployment runs the same product and needs no migration (schema
stays 14). Take it if you read release notes from the installed package or from PyPI:
**0.26.0's notes shipped with three wrong sentences, one in the direction that would
let an operator skip a trust-surface release** — it said the two import-boundary fixes
were *"not reachable by a deployment that only ingests its own writes"*, and restoring
your own export crosses that same boundary (`veracium import --restore` is a mode of
`import_memory`). The corrected guidance stands above the 0.26.0 erratum below, and this
cut publishes it in the sdist's frozen copy of this file and in the GitHub Release.

- **0.26.0 erratum (2026-09-17/18).** The three sentences and their corrections are kept
  verbatim under the 0.26.0 heading: the reachability sentence above; *"32 findings"* →
  34 (the ledger it cites); *"three comments renumbered"* → seven lines across three
  files. The receipt figure it quoted as ≈2.3 KB was an estimate; it has since been
  measured (next item).
- **specs/0027 v15.1 — the policy receipt's cost measured, not estimated.** At the
  default budget (`max_subgraph_edges = 40`) a receipt is 1,280 B of JSON, a 1,384 B row,
  and 2,171 B per firing on disk (106 SQLite pages amortised over 200 firings). It scales
  with the BUDGET, not the store: payload ≈ 580 B + 17.5 B per unit of budget while the
  budget truncates (`budget_state.truncated` true); the `tags_matched` bound adds exactly
  one 4,096 B page flat. *"Linear in the budget"* is withdrawn as a general law — it
  describes the default-shaped receipt only. Measured on this repository's fixtures;
  the measurement scripts are in the sdist.
- **specs/0022 — the two evidence records regenerated and bound to their generators.**
  `vector_harness_result.txt` (78/78 against `reference_revocation.py`) and
  `store_concurrency_result.txt` (18/18 against the §4e-i construction), previously
  stale since the finding that named them was closed a month ago; a test now fails if
  either drifts from its generator.
- **The evidence fan-out stays at four workers.** Six was measured against a prediction
  filed first and the prediction was falsified: the evidence phase fell from 149.2 s to
  132.3 s (predicted 85–100 s), the suite total was unchanged within noise, and every
  command got slower — serial-equivalent CPU 580 s → 764 s, the median command 1.33×
  slower. The commands contend with each other; the box was not the limiter. The
  comment beside the constant now says so instead of the reason that was wrong.
- **`specs/check_spec_reference.py` refuses an empty commit range** the way it already
  refused a missing base: a bare invocation after a push was reporting green having
  examined nothing.
- **Two draft specs, not implemented: specs/0042 (exercised guarantees — the firing
  census, v4) and specs/0043 (the refusal harness, v1).** 0042's round-1 external verdict
  returned it for amendment and it was split on the owner's ruling; both are in external
  review and authorise no implementation. Their evidence directories ship runnable
  reproductions of the reviewer's findings: an AST inventory of decision sites over all
  of `src/veracium` (55 modules, 636 candidate sites by syntactic kind — an inventory,
  not a census); a neutral examiner projection whose forbidden-label set is derived from
  the render code (the product's `introspect(mode="categories")` prints the trust
  labels; the projection carries none); and five disclaimer-then-assertion answers that
  the shipped abstention heuristic counts as abstention — **which is a measurement
  defect in the product's own `abstained` telemetry (`Memory.answer`, the selfcheck),
  filed, not yet fixed, and not a behaviour change here.**

## 0.26.0 — 2026-09-17

**BREAKING for existing stores — schema 13 → 14 (specs/0027 v14, the durable policy
receipt).** One additive table (`policy_receipt`) and its time index; no data step — a
receipt is written only by a recall on an open v14 store, so there is nothing to carry.
A store created by ≤ 0.25.0 must be migrated offline before this build opens it —
`veracium migrate --db X --i-have-quiesced --backup REF` (specs/0013's operation; a
below-head store refuses to open otherwise). **Who must act:** every operator with an
on-disk store; and every host that IMPLEMENTS `veracium.store.base.Store` and uses a
policy lane — the store must add `write_policy_receipt`, `policy_receipts` and
`policy_receipt`, because the base class refuses rather than drops and the first
recall on which a lane fires raises `NotImplementedError` against a store without
them. Library and MCP callers that pass no `policy` change nothing.

> **Erratum, 2026-09-17, after publication.** Three sentences in this section shipped wrong in
> the sdist's frozen copy of this file and are corrected above; the shipped wording is kept
> here so the two copies can be reconciled. (1) The upgrade guidance read *"Neither is
> reachable by a deployment that only ingests its own writes"* — false, and in the direction
> that would let an operator skip a trust-surface release: restoring your own export crosses
> the same import boundary. (2) The 0041 entry said *"32 findings"*; the ledger it cites
> sums to 34. (3) It said *"three comments renumbered"*; the commit changed seven lines
> across three files, six comments and one docstring line — three was the file count. Also
> labelled: the ≈2.3 KB receipt figure is an estimate, not a measurement. Found by the second
> seat's post-land re-derivation, the first run of that standing step; every correction
> re-derived from the artifact before it was written. **Addendum, 2026-09-18:** the shipped
> notes say *"≈2.3 KB per row, linear in the budget"*; the figure was then measured (specs/0027
> v15.1) — ≈2.2 KB per firing at the default budget, scaling with the budget and not the store,
> with the `tags_matched` bound adding one 4,096 B page flat, so "linear in the budget" holds
> for the default-shaped receipt only. The section's retention entry (below, under the durable
> receipt) now carries the measured statement.

**Who should take this release, beyond the store migration above.** Any deployment that
IMPORTS procedural records from a source it does not itself control should take it: two
import-boundary defects are fixed here, and both let a claim in an incoming copy decide
something the stored record should have decided. A copy claiming a different predecessor
had its claim replace the stored producer in the inheritance lookup; and conflicting
record ids were resolved after inheritance was derived rather than before. Both live in
`import_memory`, and RESTORE is a mode of that same function (`veracium import --restore`,
the path the product's own backup guidance directs operators to), so **any deployment that
imports — including one restoring its own export — reaches them; only a deployment that
never imports at all is unaffected.** Stated per the standing rule that a release carrying a
trust-surface fix says who should act, not only what changed.

- **Import boundary: a persisted producer is the constraint** (specs/0037 v24.5; the amendments
  review package, round 9, returned 2026-09-14 with the design acceptances in force). A copy of a
  stored procedural record that claimed a different predecessor was refused, but the claim had
  replaced the stored producer in the inheritance lookup, so a successor with the claimed
  producer restored under a predecessor that carries another. Now a stored producer is never
  replaced by claimed ancestry, admitted or refused; a stored record without a producer takes
  the claimed chain's (a claim adds a constraint, never removes one).
- **Fixed: an omitted event date defaults to the UTC calendar date** (the round-9 reviewer's
  F2, a pre-existing defect). `remember`, `dispute`, `confirm`, `record_outcome` and `correct` — the
  five paths that default a missing date (the round-10 reviewer corrected an earlier wording here
  that named `record_procedure`, whose default was already UTC, and omitted three of the five) — used the host's LOCAL calendar date, while ingestion reads a bare date
  as UTC midnight; on a runtime whose local date runs ahead of UTC (the reviewer's, at 22:01
  UTC), a new record was stored with tomorrow's `valid_from` and withheld as `not_yet_valid`
  until UTC midnight. One clock now: the default is the UTC date the reading uses. **Who
  should act:** hosts on runtimes east of UTC that saw new records unavailable late in the
  local day; nothing changes for a host that passes dates explicitly.
- **Import boundary: conflicting record ids are resolved before inheritance is derived**
  (specs/0037 v24.4; the amendments review package, round 8, returned 2026-09-14 with the
  design accepted and frozen). A refused incomplete copy of a stored procedural predecessor
  could hide the stored producer and let a successor with another producer restore, and a
  file naming one id twice gave a file-order-dependent result. Now every copy of an id the
  file names more than once is refused (`duplicate_id`), the lineage lookup reads the stored
  record first and every incoming copy together (a rejected copy never erases a persisted
  constraint), and copies that disagree about a constraint leave it unresolved, which no
  successor satisfies. Both file orders give one disposition. A file that repeats an id was
  previously imported last-copy-wins, silently; it is now refused per copy and counted.
  Also closed before the seal (research's red team of the fix): a stored predecessor that is
  procedural only by the receiving registry's kind now constrains its successors on the
  default path exactly as an incoming one does, and a stored record with no predecessor no
  longer shadows an incoming copy's claim to one.
- **Added: the policy receipt is durable.** When a policy lane fires, `Memory.recall`
  writes the receipt to the store as one row keyed by its minted `recall_id` — the
  receipt's JSON verbatim beside the identity columns a reader lists by — BEFORE it
  returns, and `Memory.policy_receipts(user_id, limit=None)` (newest first) and
  `Memory.policy_receipt(user_id, recall_id)` read it back field-equal to what `recall`
  returned (0027 §4g, V-RECEIPT-DURABLE). A receipt write that fails raises out of
  `recall` (V-RECEIPT-DURABLE-OR-LOUD): the answer is not returned as if its trace
  existed, which is the defect the receipt was built to close (correction C1). A
  receipt is written once — a second row for a `recall_id` is refused by the key.
  Receipts are ids only, as before; they are not part of `export_memory` (deployment
  audit, not memory) and `forget_user` erases them with the user's rows in the same
  transaction (V-RECEIPT-ERASE). Retention is not in this release: the table grows by
  one row per firing recall — MEASURED after this release shipped (2026-09-18, specs/0027
  v15.1): ≈2.2 KB per firing at the default budget (`max_subgraph_edges = 40`; 2,171 B on
  disk, row 1,384 B), scaling with the BUDGET — receipt payload ≈ 580 B + 17.5 B per unit while the budget
  truncates (`budget_state.truncated` is true; once the budget exceeds the candidates the receipt
  is sized by the candidates), independently derived blind by the second seat; the disk figure is page-quantised, 106 pages
  amortised over 200 firings — and not with the store; a host using the full `tags_matched` bound adds exactly one 4,096 B page
  per firing, flat, which dominates — budget-linearity describes the default-shaped receipt
  only. T10's ≈2.3 KB estimate was 5.9% high on the default cell. Erasure is per user.
- **Docs: the migration section re-derived.** `docs/api.md`'s "Migrating a store" had said "this
  release migrates v7 stores only" with a two-release ladder for older bases — true of an earlier
  release and stale since schema 8. Measured 2026-09-15: every stamped base from v1 through v13,
  and an unstamped legacy v1, migrates to the current schema in one operation; the section now
  says so. Two of the four evidence scripts that carried an absolute local path (0019
  phase1f/phase1g) now resolve the repository root from their own location; the other two
  (0024 baseline run_baseline/run_postfix) are digest-bound inside a sealed evidence bundle
  (`DIGESTS.sha256`, closure row EVIDENCE-R15-1) and stay byte-identical — their repair is
  that line's amendment, not a cleanup. None of the four is run by a shipped check.

  > **Erratum, 2026-09-18, after publication.** The sentence above and the docs
  > paragraph it describes attributed to `veracium migrate` what only the LIBRARY
  > path does. Re-executed on a store stamped at each base 1–13 (the probe ran both
  > paths on copies of the same store): `veracium migrate` — the specs/0018
  > orchestrator, `run_release_migration` — migrates base **13 only** (`HEAD-1`, the
  > accepted 0018 contract) and returns `unsupported-base` for bases 1–12;
  > `veracium.store.migration.migrate_store` migrates every base 1–13 and an
  > unstamped v1 to 14 in one call. The 2026-09-15 measurement ran `migrate_store`
  > (its commit says so) and the sentence went under the CLI's heading. Found
  > the same day by the workflow platform's 0.13.0 → 0.26.1 upgrade (store
  > 9 → 14): the CLI refused, correctly; the library chained. `docs/api.md`'s
  > "Migrating a store" now states both paths and the far-behind consumer's route.
  > A second defect, not fixed here: the orchestrator's `unsupported-base`
  > diagnostic reports bases 7–12 as "resolves to base v6" and gives ladder advice
  > written when the head was v8 (the outcome is right, the sentence is not).
- **Added: the displacement budget** (specs/0027 v15 §4h; research's candidate, the owner's word).
  `PolicyLane.max_displaced` declares the most records a policy lane may displace from the returned
  selection (an int ≥ 0; `None` for no cap; `0` means reorder but never change membership). It is
  enforced inside the fused construction, where both orders exist, so every caller is bounded; on a
  breach the recall returns the already-computed no-policy selection and the receipt records
  `budget_breached=True` with `displaced` still naming what the lane would have displaced. Every
  receipt now carries `max_displaced_declared` (`None` recorded when no cap was declared). The
  bound is enforced; its value is the host's — a generous cap changes nothing but the receipt.
- **Changed (before release, v14.1): the policy's identity strings are bounded.** `PolicyLane.policy_id`,
  `policy_version` and every `tags_matched` entry must be identifiers (letters, digits and `._:-`,
  1–64 characters, no whitespace; at most 64 tags) and are refused at construction otherwise —
  the receipt persists them verbatim, and v14 had accepted a sentence or a 400-character tag into
  the `policy_receipt` row while its schema comment claimed the row carried no content. Bounded,
  not content-free: an identifier can still name a person, which specs/0041 records as the same
  class as `evidence_ref` and `source_id` — and the identifier alphabet is the alphabet of
  structured personal data (`ssn:123-45-6789`, `dob:1974-03-02`, `dx:C50.9` all pass). **Who must
  act:** a host whose policy ids, versions or tags carry spaces or punctuation beyond `._:-`, or
  exceed 64 characters, must rename them; and every host must apply the rule no validator can:
  a policy tag names a policy, not a subject.
- **Regenerated: the schema evidence** (`src/veracium/store/evidence/*.json`,
  `specs/generated/schema_policy.json`) at the new head — it had been stale since
  schema 13 (recorded head 12; the 0.20.0–0.25.0 tags absent), which no shipped
  check enforced; the regeneration records all 46 released tags and the qualified
  runtime.

- **Procedural capture: the enclosure structure is typed, quote-aware and established or the
  passage is declined; import inheritance reads every signal and validates the inherited
  producer** (specs/0037 v24.3, specs/0038 v6.8; the amendments review package, round 7,
  returned 2026-09-14). A quoted closing character — `(press "]" when ready?)` — had ended a
  parenthetical early and let the sentence after it through with its framing stripped, and
  mismatched enclosure types were accepted; now parentheses, brackets and braces must nest and
  match by type, characters inside a quoted literal are inert, and a passage whose structure
  cannot be established (a mismatch, a stray closer, an unclosed opener, an unbalanced double
  quote) is declined. On import, a predecessor that was procedural only by the receiving
  registry's kind, or only by its producer stamp, no longer lets its marker-free descendants
  through, and a rejected intermediate's producer no longer stands in for the lineage's
  validated one — the constraint carries through it to every successor, on both paths and in
  either file order. The cost figures' histogram ships as an emitted file beside the counting
  script, and a test recomputes both figures from it without the dataset.
- **Stated limit, published: Veracium does not witness its own history** (specs/0036; the
  owner's ruling of 2026-09-12 took journal witnessing off the critical path on condition that
  the limit be published, and the owner's word of 2026-09-14 puts it in the docs). The
  `edge_event` journal lives in the same SQLite file as the rows it describes, with no hash
  chain, no `prev_digest` and no signature, and `forget_user` erases it with the user's rows —
  a history, not a tamper-evident record. Veracium detects inconsistency, faults and changes
  made outside its own interfaces, but not changes made by the party who operates the store.
  The sentence has stood under `veracium why` in the API reference and in the release notes
  that introduced it (2026-09-12); it is now also in the concepts page's "What Veracium does
  not do" and in "Providing a store" beside the store-boundary statement, where a host reads
  limits, and a test reads all three. No behaviour change.
- **Procedural capture: a parenthetical's punctuation ends nothing, a `?` establishes the next
  start only with a separator, and the import boundary's inheritance check sees refused
  predecessors; the capture-cost figures relabelled** (specs/0037 v24.2, specs/0038 v6.7; the
  amendments review package, round 6, returned 2026-09-14). "For illustration only (ready?) I
  review invoices daily." stored the last sentence with its framing stripped — a terminator
  inside an enclosing parenthetical or bracket is now inside its sentence; "Any tips?I review
  invoices daily." admitted while the `!` form refused — a run now establishes the next start
  only by what follows it, whatever marks it carries. On the default import path a procedural
  predecessor refused as procedural no longer erases its marker-stripped successor's
  requirement: the inheritance lookup is built from the raw records before any refusal,
  procedural-ness is read by lineage, and a chain that drops the markers one hop later is
  refused one hop later too, in either file order. The 0.25.0 notes said the fail-closed
  contract costs "about half of sentence positions"; that was the fraction of chunks holding
  more than one sentence (53.6%, 1,809 of 3,372) — those chunks contain 76.3% of sentence
  positions (5,045 of 6,608), and neither is a capture-loss figure; the measured capture
  result is the held-out draw's 0 of 6 positive rows. The counting script ships in the
  evidence tree. Two fixture and wording cleanups the reviewer named.

- **Design accepted, NOT implemented: targeted redaction** (specs/0041, external round 8,
  2026-09-17; eight rounds, 34 findings, the ledger in the spec's `## Review closure`).
  Acceptance freezes INV-1–INV-12, the 64-carrier treatment map and §4h's transition rules,
  and authorises implementation — **it ships no behaviour.** Nothing in this release removes
  stored content, and no redaction API exists; the only source change the line made is seven
  lines renumbered `0040` → `0041` across three files — six comments and one docstring line. Stated here because an accepted design is a commitment
  a consumer can read, and because "redaction accepted" is easy to misread as "redaction
  available". Carried into implementation by the reviewer: reconstructed receipts where no
  original exists, positive controls for the eight strict expected-failure tests that still
  lack one, and the `"redacted"` disposition.

## 0.25.0 — 2026-09-14

**Upgrade recommendation — BREAKING on three narrow surfaces; every other host upgrades
without acting. Hosts on 0.24.0 that capture procedures should take this release.** Who
must act, per surface: (1) a host that MUTATED a record's provenance in place
(`edge.provenance.confidence = …`, `setattr(edge.provenance, …)`) builds a copy instead
(`edge.provenance = edge.provenance.model_copy(update={...})`) — `Provenance` is a frozen
model now, and assignment raises a `ValidationError`; (2) an MCP deployment whose model
passed `source_id` on the served `record_procedure` tool sets `VERACIUM_MCP_SOURCE_ID`
instead (none known; the tool shipped 2026-09-08), and a host calling
`Memory.record_procedure` with a third-party author and no `source_id` now gets
`SourceIdRequired` with `require_source_id` on; (3) a host that pinned the export format
at 11 reads 12 — stamped only when a producer-bearing procedural record exists, refused by
older readers rather than shed. Why 0.24.0 hosts capturing procedures should upgrade: on
0.24.0 a captured procedure could be corrected and its successor rendered the verbatim
quote into recall context after one host action (closed at 0037 v19 — `correct()` refuses a
procedural record, the store refuses a successor that drops the markers, and a captured
procedure keeps no separate copy of the span); the erratum under 0.24.0 below records it.
What else changed, all additive for a host writing through `Memory`: the extractor's
capture gate is stricter and stated — one whole sentence of the event whose boundaries are
ESTABLISHED (the start or end of the user's turn, or a `?`/`!` before a sentence start; a
mid-text period establishes nothing, so a routine sentence beside a period-terminated
neighbour is declined — about half of sentence positions in real turns, the stated cost of
the assertion-preservation contract the external review holds this line to), positive
present form, no transformation: EXPECT VERY FEW CAPTURES, and `record_procedure` remains
the explicit path; `describe_procedures` attributes with
"recorded from something you said"; `recall(policy=)` returns a receipt; every new
procedural record says which path wrote it and `veracium doctor` reports the split. No
schema change (`SCHEMA_VERSION` stays 13); no stored byte changes for existing records;
rollback to 0.24.0 is safe for a store holding no producer-stamped record; a store holding
one still opens on 0.24.0 (its `Provenance` ignores the unknown key, so the stamp is read
past and shed on any rewrite of that record — verified against the v0.24.0 tag), and its
export is stamped format 12, which 0.24.0 refuses to import.

**Erratum (2026-09-14, the round-6 review).** These notes say the fail-closed capture contract
costs "about half of sentence positions in real turns", and the entry below repeats it. The
53.6% was the fraction of `?`/`!`-delimited chunks holding more than one sentence (1,809 of
3,372); those chunks contain 76.3% of sentence positions (5,045 of 6,608). Neither figure
measures routine capture; the measured result is the held-out draw's 0 of 6 positive rows.
The direction of the trade is unchanged — the corrected figure makes the contract more costly,
not less — and the release's behaviour is exactly as described.

- **Procedural capture: a boundary is established or the passage is declined — no abbreviation
  list; restore enforces the inheritance rules; the doctor claims nothing about why a producer
  is unknown** (specs/0037 v24.1, specs/0038 v6.6; the amendments review package, round 5,
  returned 2026-09-14; the owner's word "Fail closed"). v24's list-based rule let a passage start
  after an ambiguous separator ("For illustration only, e.g. I review invoices daily." stored the
  last sentence with its framing stripped) and let an abbreviation outside the list end one early
  ("I review invoices in env. Prod only after approval." stored "I review invoices in env"); the
  reviewer ruled that no list can establish the guarantee. Now a boundary is established only at
  the start or end of the user's turn or at a `?`/`!` followed by a sentence start; a mid-text
  period establishes nothing in either direction, and the abbreviation list is gone. THE COST,
  stated: a routine sentence before or after a period-terminated neighbour is no longer
  captured — about half of sentence positions in real turns (research: 1,809 of 3,372 chunks in
  500 sessions carry two or more sentences); the held-out draw's two admissions fall to 0 of 4;
  `record_procedure` remains the explicit path. Restore (and the default import) now apply the
  store's inheritance rules before committing — a successor that drops the procedural markers or
  names a different producer than its predecessor, in the file or already in the store, is
  refused per record as `inheritance_violation` in either file order. `veracium doctor`'s
  `procedural_unstamped` names every cause of an unknown producer (written before the stamp;
  restored from an older export or a sub-12 envelope; written outside `Memory`) and no longer
  claims a write past `Memory` on a new store. The event-aware labelling rubric v2 ships beside
  v1 in the evidence tree with its digest.
- **Procedural capture: sentence boundaries are read from the complete event as kinds, total
  and fail-closed; the claimed refusal of "I doubt I…" is real** (specs/0037 v24, specs/0038
  v6.5; the amendments review package, round 4, returned 2026-09-14). The v22 rule tested
  characters, not boundaries: a span could stop one character short of its own `?` ("I review
  invoices daily?" stored as a statement), the `.` in `$100.50` counted as sentence-final (the
  stored text lost part of the amount and the condition after it), and two sentences with no
  space between them passed as one carrier. Now a terminator's kind is read from the event —
  a boundary (end of text, or whitespace then an uppercase letter, digit or opening quote), a
  decimal point (inside), a question (`?` in the run — refused, per sentence: a routine before a
  question to the assistant still admits), or an ambiguous join (an ellipsis, an abbreviation
  before the period, a letter right after it, a lowercase continuation — refused, never
  guessed). `doubt`, `deny`, `suspect` and `presume` join the cognitive class; `question` and
  `bet` deliberately do not. Re-measured with thresholds fixed first: every pinned figure
  unchanged. Two stated costs: a lowercase continuation ("daily. archive"; "commit. npm test
  follows") now refuses the first sentence too, and an abbreviation outside the gate's list that
  carries a vowel ("per sched. Every week…") still reads as a boundary — the open residual,
  named in the spec and pinned by a test. The draw-5 labelled pairs run through the full path
  in the packaged test.
- **The store boundary stated; `Provenance` frozen; every new procedural record says which
  path wrote it** (specs/0006 v10, specs/0037 v23; the owner's word, 2026-09-14). `Store` and
  `Store.add_edge` are an interface a host IMPLEMENTS, not a write API a host CALLS: every
  guarantee in this documentation is about records written through `Memory`, and a record a
  host writes by calling `add_edge` directly carries exactly what that host minted — a stated
  limit, not a gate (`docs/api.md`, "Providing a store"). `Provenance` is now a frozen model:
  a stamp cannot be flipped on a built record, only minted at construction; hosts that mutated
  `edge.provenance.<field>` must build a copy (`edge.provenance =
  edge.provenance.model_copy(update={...})`) — the eight places the library itself did so now
  do. New `Provenance.producer` (`"host"` from `record_procedure`, `"extractor"` from the
  quote-gated capture) on every procedural record written from this release; absent on every
  declarative record (bytes unchanged) and on procedural records written earlier or written
  through a path other than `Memory` — or restored from an older export or a sub-12 envelope,
  where the field is stripped — which `veracium doctor` reports as `procedural_unstamped`
  (the producer is unknown; the count does not say why) beside the split it can now make —
  `procedural_declared` and `procedural_captured` were one merged number before, and the
  check's own docstring called them declared. The stamp is immutable on a same-id replace and
  inherited across a supersession. Export format 11 → 12, stamped only when a producer-bearing
  record exists; an older reader refuses such a file rather than shedding the field; a
  producer-free store exports as before. BREAKING for a host that assigned to provenance
  attributes or pinned the export version; nothing changes for a host that writes through
  `Memory` and reads exports with the current release.
- **Procedural capture: the quoted span must be one whole sentence of the event, and the stored
  text is that sentence with no transformation** (specs/0037 v22, specs/0038 v6.4; the amendments
  review package, round 3, returned 2026-09-13). The relative-clause cut added at v21 removed a
  mid-sentence clause and the condition after it ("I review invoices, which arrive daily, only after
  approval" stored as "I review invoices"); it is withdrawn — the user's sentence is stored as
  written. A quote that is a fragment of a sentence ("I always review invoices" lifted from
  "Imagine I always review invoices.") or that spans two sentences (v24 reads the join as a kind: a
  lowercase continuation is ambiguous and refuses the first sentence too)
  is refused: the span's boundaries are validated against the event. A conditional whose lead
  clause carries the routine ("If I review invoices daily, the queue stays short.") is refused.
  Re-measured on all four labelled draws with thresholds fixed first: admissions unchanged. Packages
  now carry a machine-readable test-results file.
- **Recall accepts a host policy and returns its receipt** (specs/0027 v13; the owner's word,
  2026-09-13, "Do the A1 receipt"). `recall(..., policy=PolicyLane(policy_id, policy_version, ranks,
  tags_matched))` feeds the policy lane landed at v11, whose use had been forbidden until a receipt
  existed. When the lane fires, `Recall.policy_receipt` records the counterfactual: the order this
  call would have returned with no policy, the order it returned, the records displaced and
  admitted within the returned length, the per-edge score delta, whether the budget could truncate
  at all and at what coverage share, the protected reserve's ids under both orders, and a minted
  `recall_id` to join to the host's own logs. Written on the
  non-semantic path too; ids only; an inert policy leaves no receipt; not combinable with
  `as_of`. The receipt is not yet stored durably — hosts persist it themselves until the store
  table lands with its migration. No shipped code passes a policy, so nothing changes for a host
  that does not.
- **Procedural capture: the stored summary is now DERIVED from the user's quoted span; requests,
  second-person and multi-sentence spans are refused** (specs/0037 v21, specs/0038 v6.3; the
  amendments review package, round 2, returned 2026-09-13; the owner's word on derivation the same
  day). Until now the extractor supplied a summary and ingest checked it against the quote by word
  order — a curly apostrophe lost a negation ("I don’t review invoices" stored as "Reviews
  invoices") and a coordination lent its object ("I review invoices and archive receipts" stored as
  "Reviews receipts"). The model's summary is no longer used for a procedural triple at all: the
  stored `object` is the quoted span itself, whitespace-normalised ("I've been misting my fern every
  other day"; "I go to the gym on Tuesdays, Thursdays, and Saturdays."; the relative-clause cut this
  entry first carried was withdrawn the same day, see the entry above); `describe_procedures` renders it after "recorded
  from something you said:". A first-person request ("I request that you review
  invoices today"), any span addressed in the second person, and a span crossing a sentence
  boundary are refused. The record guarantee is now exact: `object` is the derived span, `note` is
  empty, no digest is stored, and the render exclusion is the whole protection — the grammar is
  the only filter between a user's sentence and stored text. Measured with thresholds fixed first:
  the grammar's admissions on the three prior draws unchanged; on a fourth held-out draw of 120
  (sessions 301–400), 0 of 115 must-refuse spans admitted and 2 of 3 routines (a stative "I've
  got … down to a science" refused, a stated cost). 16 clean routines in 400 sessions.
- **Procedural capture: the actor-present gate is now POSITIVE-FORM** (specs/0037 v20; the owner's
  word, 2026-09-13, on research's reading of the held-out failure recorded under v19). A capture is
  admitted only when the quoted span opens with an explicit assertion of the user's current,
  repeated performance: present simple ("I use it to…", "I don't eat meat", "I always run…"),
  present perfect continuous ("I've been using…"), or present progressive with a frequency
  marker ("I'm walking the dog every morning"), with an action verb at the head — not a modal or
  auxiliary, not a cognitive or volitional verb (think, mean, hope, plan, consider, want, try, …).
  Every form not enumerated is refused; the v19 markers stay as a second gate. Re-measured with
  the thresholds fixed first: on the labelled 31, 8 of 9 routines admitted and 0 of 20 must-refuse
  spans; on the 51, 0 of 45 (the three "thinking of" intentions v19 admitted now refuse by
  class) and both positives kept; on a third, HELD-OUT draw of 39 (sessions 201–300) with the
  threshold stated before the run, 0 of 34 must-refuse spans admitted and 1 of 2 positives (the
  miss predicted before the run: "I've been trying to…" is refused by class). Stated cost:
  "I do the dishes every night" and "I've always run the linter" are refused (a lexical "do", a
  present perfect without "been") — zero occurrences in 121 labelled spans, so unmeasured here.
  Caveat on every recall figure: 11 of the 13 clean positives across three draws are
  present-perfect-continuous, and that may be the probe's distribution rather than users';
  recall on present-simple habituals is essentially unmeasured. EXPECT FEW CAPTURES, as before
  (~13 clean routines in 300 sessions); `record_procedure` remains the explicit path.
- **Procedural capture: the gates the external return and research's red team demanded; a
  render defeat on 0.24.0 closed** (specs/0037 v19, specs/0038 v6.2; the amendments review
  package, round 1, returned 2026-09-13). On 0.24.0 a captured procedure could be CORRECTED
  (`correct()`), and the successor lost the procedural stamp while keeping the note that held
  the verbatim quote — so the quote rendered into recall context after one host action. Now
  `correct()` on a procedural record refuses with the named reason `correction_of_procedure`
  (retire it and restate the procedure), the store refuses any successor that would drop the
  markers, and a captured procedure keeps no separate copy of the quoted span (its note is
  empty; no digest is stored; the span is verified and discarded — `object` holds the gloss). Capture itself is gated in order: the event's
  author is the user; the quote is a verbatim span; the summary meets the same contract as
  `record_procedure` (normalised, at most 512 characters); the span opens with the user as the
  actor in the present or habitual and carries no report, rejection, aspect, norm, request,
  aspiration, one-time or past marker, with no quotation frame to its left; and the summary
  describes the span (contained, in order, negation and conditions kept). Any failure is
  refused and counted in `procedural_refused`. The residual is MEASURED in the spec with the
  thresholds fixed before the runs, and one threshold FAILED: on research's labelled 31
  (designed-from), recall 8/9 and the two borderlines admitted — a span grammar cannot tell a
  single ongoing project from a repeating practice; on a held-out draw of 51 with the rubric
  frozen before labelling, 3 of 45 must-refuse spans admitted, all intentions phrased "I'm
  thinking of", a form the aspiration lexicon does not carry — left as measured, not patched
  after the score. Whether to extend the lexicon or require a positive assertion of current
  performance was the owner's decision (v20, above). EXPECT FEW CAPTURES: the corpus shows ~13
  clean user-stated routines per 300 sessions, before a gate that must refuse aspirations. Also: the `mcp` extra
  is bounded to `<2` (2.x broke the server import in the reviewer's environment). **Hosts on
  0.24.0 that capture procedures should upgrade**; an erratum on 0.24.0's notes is the owner's
  call.
- **`describe_procedures` no longer says "you said you follow"** (specs/0037 v18; the owner's word,
  2026-09-13, on research's pre-dispatch read of the amendments review package). The 0.24.0
  quote gate proves that a routine's words appeared in the user's own message — not who the
  routine belongs to, nor that the user endorses it now: "Marcus told me to always run the
  linter", "I refuse to always run the linter" and "I used to always run the linter" all
  store a procedural record with basis `stated`, and describe rendered each as a routine the
  user follows. Render stays closed, so nothing could instruct the model; the misattribution
  reached the host. The `stated` attribution now reads "recorded from something you said:
  <summary>", which is true of a host-declared procedure and of every captured one; the
  host-declared path gives up its stronger wording. The gate itself is unchanged and its
  residual is stated in the spec; an acceptance grammar over the quoted span is the named
  next refinement, not in this entry.
- **BREAKING for one MCP surface — the served `record_procedure` tool no longer takes
  `source_id`; `require_source_id` now reaches `record_procedure`** (specs/0006 v9, specs/0037
  v17; the owner's word, 2026-09-12). The tool took `source_id` as a model-supplied argument
  and stored it unchanged — a model could mint or impersonate a source identity, which 0006 I1
  forbids and its test never reached. The tool now carries the deployment's
  `VERACIUM_MCP_SOURCE_ID` binding exactly as `remember` does. **Who must act:** an MCP host
  whose model passed `source_id` on `record_procedure` sets the binding instead (none known;
  the tool shipped 2026-09-08). Second: `Memory.record_procedure` with a third-party author, or
  a context derived from a third party, and no `source_id` was written even with
  `require_source_id` on — the 0.23.0 rule reached the extractor path only. It now raises
  `SourceIdRequired` before any write; the MCP tool returns `{"ok": false, "refusal":
  "source_id_required"}`. Hosts that opted out are unaffected. No stored byte moves.

## 0.24.0 — 2026-09-12

**Upgrade recommendation:** no host must act. This release changes what the extractor may
STORE — a routine the user stated in an event can now be recorded as a procedural record,
behind a verbatim-quote gate — and changes nothing about what is RENDERED: a captured
procedure is excluded from recall, the briefing and the wiki exactly as a host-declared one
is. Hosts that read raw edges (`store.edges`, exports) should know that procedural records
can now arrive from ordinary `remember` calls on user-authored events, marked by the same
stamp `record_procedure` writes (`is_procedural`). Two additive result keys, `procedures`
and `procedural_refused`; the served MCP `remember` tool strips them with the other
extractor counters. `veracium doctor` gains an informational check that cannot fail a run.
No schema, export-format or stored-byte change for existing records; `require_source_id`
stays on (0.23.0); rollback to 0.23.0 is safe.

**Erratum (2026-09-14, the owner's call).** These notes said a captured procedure "changes
nothing about what is RENDERED". On 0.24.0 that held for the record as written and not
after one host action: `correct()` on a captured procedure produced a successor without the
procedural stamp that kept the note holding the verbatim quote, and that note rendered into
recall context (found by the external amendments review, round 1, 2026-09-13). Closed in
0.25.0 (0037 v19: `correct()` refuses a procedural record; the store refuses a successor
that drops the markers; a captured procedure keeps no separate copy of the span). Hosts on
0.24.0 that capture procedures should upgrade.

- **`veracium doctor` gains a `procedural` tripwire** (research's census as a standing check;
  the owner's word, 2026-09-12). Two numbers, never merged: `procedural_declared`, records
  stamped procedural (exact, the record's own stamp), and `procedural_shaped`, declarative
  records whose `note` matches the census marker screen — a screen result, never a count of
  procedures (specs/0037 §4a: kind is the stamp, never the text). Notes only: `summary` is
  never read (specs/0022 §7a, amended to disposition the doctor's one read of `note`).
  Informational on every outcome; it cannot fail the build. Baseline recorded with the
  screen: 13 of 312 notes on the LongMemEval-derived corpus, none genuine. It exists to
  notice an extractor that starts producing procedure-shaped notes, or hosts feeding
  procedures down the declarative path — neither would announce itself.
- **Procedural capture reopened, render still closed** (specs/0037 v16, specs/0038 v6.1,
  specs/0025 amended; the owner's word, 2026-09-12). The extractor may now RECORD a
  routine the user stated — it may not conclude one. A procedural relation
  (`follows_procedure`) is in the extraction vocabulary again; a triple under it must
  carry `quote`, the verbatim span of the event text in which the user states the
  routine, and ingest verifies that span against the event text it already holds: a
  verified quote on a user-authored event is stored as a procedural record with basis
  DERIVED `stated` (the quote kept in the never-rendered `note`); a missing, empty,
  paraphrased or unverifiable quote, or an event the user did not author, is refused
  and counted. Two new result keys on every path, `procedures` and `procedural_refused`
  (stripped from the MCP tool result with the other extractor counters). Nothing
  rendered changes: a captured procedure is excluded from recall, the briefing and
  the wiki exactly as a host-declared one is, and `describe_procedures` shows it with
  the `stated` attribution. `record_procedure` is unchanged; `observed` stays host-only;
  no `inferred` basis exists. No stored byte moves for existing records. Motivation:
  research's ablation showed the extractor flattening stated routines into completed
  one-off events, a fidelity loss at capture.

## 0.23.0 — 2026-09-12

**Upgrade recommendation — BREAKING; every host that ingests third-party content must
act before upgrading.** `MemoryConfig.require_source_id` now defaults on: a
third-party-authored event, or one declared third-party-derived, is refused before any
write unless it carries a `source_id`. Who must act, per surface: a library host adds
`source_id=` to those `remember` calls; a CLI host adds `--source-id`; an MCP deployment
sets `VERACIUM_MCP_SOURCE_ID` — and a deployment with `VERACIUM_MCP_CAPABILITY` unset has
the third-party baseline, so without the binding **every** `remember` there is refused. A
host that cannot supply ids yet sets `MemoryConfig(require_source_id=False)` and keeps
0.22.0's behaviour exactly. Stored bytes do not move, no schema or export-format change,
existing unsourced rows are untouched and `veracium doctor` names them; rollback to 0.22.0
is safe. The other entries need no action: the `doctor` `sources` check, the confirmation-
episode id fix (0.22.0's disclosed finding), an inert third recall lane, and two doc sentences.

- **BREAKING — `source_id` is now required for third-party content: `MemoryConfig.require_source_id`
  defaults on** (specs/0006 v7 + v8, §4 rule 9 / I15; option C stages 2 and 3, on the owner's word).
  `remember` refuses, before any write, a third-party-authored event or a declared
  third-party-derived one that carries no `source_id` — no source identity means no revocation
  can ever reach the record (0022 R12). The 0011 floor (no declared context) is never refused.
  **Who must act:** a library host passing `author=THIRD_PARTY` or `derived_from=THIRD_PARTY`
  adds `source_id=` (an opaque, stable id for the mailbox / connector / device — never a
  person); a CLI host adds `--source-id`; an MCP deployment sets `VERACIUM_MCP_SOURCE_ID` —
  and a deployment with `VERACIUM_MCP_CAPABILITY` unset has the third-party baseline (0031),
  so without the binding **every** `remember` there is now refused with
  `{"ok": false, "refusal": "source_id_required"}`. To keep the previous behaviour set
  `MemoryConfig(require_source_id=False)`. Existing rows are untouched (no ids are invented,
  0006 I1); `veracium doctor`'s `sources` check names the unsourced ones. The library
  refusal is `veracium.ingest.SourceIdRequired`; the served MCP tool exposes no `source_id`
  argument (0006 I1). The selfcheck's third-party cell and every docs example now carry an id.
- **`veracium doctor` gains a `sources` check** (the owner's staged ruling on requiring
  `source_id` for third-party content, option C, stage 1): every third-party-authored fact
  or episode with no `source_id` is named — it has no source identity and no revocation
  can reach it (specs/0006 I13, specs/0022 R12); only per-user erasure does. Keyed on the
  evidence author only: content merely derived from a third party is not checked, because
  the stored payload cannot tell a declared derivation from the default every undeclared
  ingest receives. The ingest-time refusal is the BREAKING entry above; this check
  reads the store and changes nothing.
- **Recall fusion gains an inert third lane** (specs/0027 v11, the owner's design ruling):
  `fused_subgraph(..., policy_rank=None)` accepts a `{edge_id: rank}` map whose term
  `1/(K + rank)` feeds `fused_score` only, for ids the lexical or semantic lane already
  holds — never the protected reserve (`rel_ext`) and never Stage 3 membership, so a
  learned ranking adjustment can never decide what counts as protected evidence. No
  shipped caller passes one; with it absent every recall path is byte-identical to 0.22.0.
  The receipt and any automatic acceptance are later steps, not in this release.
- **Docs: the history's limit, stated.** The transaction-time journal (specs/0029) lives
  in the same file as the rows it describes, with no hash chain or signature; veracium
  detects inconsistency, faults and changes made outside its own interfaces, not changes
  made by the party who operates the store. Independent witnessing is not part of v1.
  Two sentences in the API reference (the owner's ruling, 2026-09-12); no behaviour change.
- **Fix: a confirmation episode now has one id, and a host can delete or retire it.**
  `confirm()` (specs/0008) wrote the confirmation episode's row under one minted id
  and its stored payload under another; every read surface returned the payload's id
  and every lookup used the row's, so `delete_episode`, retirement and reinstatement
  by the id a consumer held found no row, changed nothing and returned without error
  (found by `veracium doctor` on its first run; 0.22.0's release note carries the
  erratum). The row id is now derived from the confirmation id and equals the
  payload's. Forward-only: episodes written by earlier versions keep their two ids,
  `doctor` keeps naming them, and per-user `forget` was and is unaffected. No
  accepted spec names the episode id; 0008's summary and transaction obligations
  stand unchanged.

## 0.22.0 — 2026-09-12

**Upgrade recommendation:** no host must act. This release adds three operator verbs
to the CLI — `veracium why`, `veracium doctor` and `veracium remember --dry-run` —
and changes nothing else: no schema, export-format, library-API or MCP change, no
stored byte moves, and rollback to 0.21.0 is safe. Hosts that operate a store
should take it for `doctor`, which lints a store without a provider and without
touching it. **Known and disclosed:** on any store carrying a confirmation, `doctor`
reports one finding it did not cause — `SqliteStore.confirm_edge` writes the
confirmation episode's row under one id and its payload under another (found by
this release's own linter; not fixed in this release). It names the episode row.
*Erratum, 2026-09-12, after the other seat read the specs against it:* no accepted
spec governs the episode's id (specs/0008 pins the summary and the transaction,
not the id), so this is an internal inconsistency awaiting an owner ruling on
which id is canonical — and it is NOT harmless. Every read surface returns the
payload id and every lookup is by the row id, so `store.delete_episode(...)`,
retirement and reinstatement of a CONFIRMATION episode by the id a consumer holds
find no row, change nothing, and return without error. Per-user erasure
(`forget`) is unaffected and still removes the row. Measured by both seats.

- **`veracium remember --dry-run` — what an ingest would write, without writing it**
  (the developer-tools backlog's fourth item, started 2026-09-12 on the owner's word).
  The shipped ingest runs for real against a snapshot copy of the store, and the report
  is the delta: each fact that would be written with its author, disclosure tier,
  quarantine / grounding / confirmation flags, agreement record and supersession
  target; each existing fact that would move, with what moved; the ingest's counters
  verbatim (including `subject_refused`, `quarantined_at_birth`, `agreement_floored`
  — the 0026 relay floor — and `extraction_unusable`); the episode; every specs/0039
  degrade record. The original is never opened and is byte-identical afterwards. The
  provider is called once, as the real ingest calls it. `--json`; exit 0 usable, 1 not.
- **`veracium doctor --db X` — a read-only store linter, no provider needed** (the
  developer-tools backlog's fifth item, started 2026-09-12 on the owner's word). It
  copies the file and opens the copy through the store constructor — the original is
  never opened, and specs/0031 §4b-ii's connection inventory gains no site — so the
  constructor's refusals (below head, above head, unstamped/foreign, not a database)
  are the first findings; then `quick_check`, the identity singleton and epoch, every
  payload's consistency with its row (`id`, `user_id`, `active`, `quarantined`, a
  dispositioned reason on retired edges), dangling and cyclic `supersedes` links, an
  unretired predecessor, orphaned outcome episodes / confirmations / ledger rows /
  embeddings / journal events, edges with no journal event, and for every standing
  revocation the reference sweep's pending effects (specs/0022 §4e). Exit 0/1/2. It
  repairs nothing. Found on its first run: `SqliteStore.confirm_edge` writes the
  confirmation episode's row under one id and its payload under another (see
  tests/test_doctor_cli.py and the erratum in this release's upgrade note); not fixed
  in this entry.
- **`veracium why --user X <edge-id>` — a fact's biography** (the developer-tools
  backlog's third item, started 2026-09-11 on the owner's word). Read-only,
  store-only, no provider: the fact with its provenance and source standing, its
  lineage both ways with the reasons the retired side carries, the contribution
  ledger both ways, refusals it was party to, and a timeline of every journal event
  (specs/0029), confirmation (specs/0008) and outcome judgment (specs/0009) — a
  mutation names the fields that moved. `--json` for the same as one document;
  `--find TEXT` lists edge ids by subject, relation or object text, since no other
  verb prints ids. Composed from existing public store accessors; no stored byte,
  no schema and no guarded module changes. Three of the reads run after the
  snapshot window closes (the accessors take the store's non-reentrant lock) and
  may be one write newer than the rest; the module documents it.

## 0.21.0 — 2026-09-11

**Upgrade recommendation: every host should read this section; hosts that catch
`TypeError` around `remember` must act, and every host gains one result key.** No
schema, export-format or migration change; rollback to 0.20.1 is safe (a host loses
the `extraction_unusable` key and the three non-list `triples` answers raise again). The
extraction path stopped raising on three malformed provider answers, every `remember`
result now carries a boolean that tells a malformed answer from an empty one, and a
provider that degrades leaves a record in the diagnostics log when a reporter is
attached. This is one account of the final behaviour; the last paragraph says how it
was reached between 0.20.1 and this release, because the intermediate states were
published on `main` and a host tracking `main` may have seen them.

**What a host sees now, in one place.**

- **`extraction_unusable`, a boolean on every `remember` result and on the MCP `remember`
  tool result** (specs/0025 §4c, amended). True when the provider's first answer produced
  no shape-valid triple — rejected before any triple was read (no JSON object; an
  `instructions` value of the wrong type), a missing or non-list `triples`, or a non-empty
  list none of whose members is a well-formed triple. False otherwise, including for a
  legitimately empty extraction and for a list whose members were well-formed but all
  refused for another reason, which the existing counters carry. It says an answer was
  unusable, never which way. The older `unparseable` flag keeps its narrow meaning and is
  present only on the rejected-before-any-triple path. The opt-in telemetry event does
  NOT carry the new field.
- **`remember` no longer raises `TypeError` when a provider answers with a `null`, numeric
  or boolean `triples`** (specs/0025 §4b(1), amended). Those answers returned an
  exception while a string or a dict in the same position returned zero facts silently;
  the difference was iterability, not a property anyone chose. Every non-list `triples` is
  now one recorded shape failure, zero facts, `extraction_unusable: True`. A provider
  EXCEPTION still propagates as before. Hosts that caught `TypeError` to detect a broken
  provider must read `extraction_unusable` or the diagnostics log instead.
- **A re-extraction retry answered with a bare JSON array now repairs** (specs/0025
  §4b(1), amended): the triples without the `{"triples": ...}` wrapper used to be treated
  as malformed and every repair in them discarded. On this path `recovered` rises and the
  stored relation is the registry member the retry named instead of `unclassified`.
  Measured on the standard fixture by two independent instruments: `recovered` 0 → 1.
- **Every stored byte is otherwise unchanged; no schema, export or migration changes.**

**Degradation visibility (specs/0039, ACCEPTED at external round 4, 2026-09-10; its
implementation reviewed at external rounds 5 through 9 and accepted 2026-09-11).** Veracium degrades in five places instead
of failing, by design, and until now none of them left a record an operator could see:
the ONE re-extraction retry that a provider fails, an extraction answered in prose, a
volatility class outside the enum (silently DURABLE), a first answer with no usable
`triples`, and a list member that is not a well-formed triple. Each now writes ONE
content-free `WARNING` line to the local diagnostics log when a reporter is attached —
`op`, `degrade`, a hashed user id, a closed-vocabulary `cause`, and only the byte length
and a sixteen-hex SHA-256 of the provider's message or raw answer (never text; never the
exception's class name), or a per-call `count`. A record never changes an outcome and is
never sent inline — it waits for the next consented send. **Every degrade record is
written before the first store write**, so an error that follows always finds its record
already in the log (a round-5 review finding: the two per-call records used to be written
after the storage loop, and a store failure inside it lost them). Every provider answer
shape was RUN through the real ingest path on two independent instruments and the
transcripts are committed (`specs/evidence/0039/`), asserted byte for byte by the suite.

- **The CLI attaches a diagnostics reporter by default** (as the MCP entry point always
  did): `veracium remember` writes to `$XDG_STATE_HOME/veracium/veracium.log` when local
  logging is enabled (the default). `veracium diagnostics disable` and the config file's
  `log_enabled` turn it off; `veracium diagnostics path` prints the location.
- **Log retention, measured (specs/0039 §7):** a degrade record is 98–155 bytes,
  measured at this commit over ten records spanning all five degrade kinds — the
  shortest is `member_skipped` (a count), the longest `primary_failed`/`no_triples_key`.
  The rotation window is 3,000,000 bytes (1 MB × 3 files), so it holds 19,354 records
  at the largest size and 30,612 at the smallest. An error record is a multi-line
  traceback, measured across our CI matrix (Python 3.10 to 3.13) at 2.8 to 4.6 times
  the largest degrade record, so a traceback written now rotates out of the window after roughly 19,300
  further degraded events at the largest degrade size. No single byte figure is quoted
  for the error record on purpose: a traceback's length is the interpreter's format and
  the absolute source paths of the installation. Because the volatility path writes one
  record per CALL, not per triple, a drifted provider with ten triples per event still
  costs one record.
- **Manual exercise (specs/0039 §6a):** `specs/evidence/0039/manual-cli-transcript.txt`
  — the shipped CLI against a provider that fails the retry and one whose vocabulary
  drifted, then the log; the provider was scripted at the CLI's own seam.
- **Not covered, deliberately:** a failed RETRY is visible as `retried > 0, recovered =
  0` rather than through `extraction_unusable`; and the field says an answer was
  unusable, never which way — that distinction is in the diagnostics log and needs a
  reporter.

**How this release got here, for a host that tracked `main` between 0.20.1 and 0.21.0.** The 0039 implementation
landed first with the accepted scope: records only, no result change, the three
non-list shapes still raising. The retry's bare-array normalization followed, then the
wider normalization that stopped the raise. That last change removed the only signal a
host with no reporter had, so an intermediate commit widened the existing `unparseable`
flag onto the failure paths; the external reviewer showed that flag then meant neither
thing it could mean (silent on an all-invalid list, set on a parsed answer whose triples
were fine), and it was replaced by `extraction_unusable` with `unparseable` restored to
its narrow meaning. Only the final state above ships in this release; the external
review of the implementation closed at round 9 with no product-code finding after the
replacement.

## 0.20.1 — 2026-09-08

**Upgrade recommendation:** every host wiring a non-Anthropic provider should take this release; a host on the reference provider sees no behaviour change. No schema, export-format or API change; rollback to 0.20.0 is safe (a store written by 0.20.1 differs only in the facts it refused to write).

**Fix: the extraction prompt's subject grammar is enforced, and the
selfcheck's supersession pair is mandatory (specs/0025 as amended
2026-09-08; found by the 0.20.0 release's provider-backed selfcheck).** Under
an OpenAI-compatible provider (the shipped `examples/openai_provider.py`,
gpt-4o-mini) the prompt's placeholder `user|person:<name>|org:<name>` was read
as a literal separator, so "I work at Acme" and "I switched to Globex" were
stored under two different subjects, supersession was never invoked, and the
store accumulated never-superseded facts — while the selfcheck scored 12/13
and reported PASS under its 90% tolerance. Claude reads the pipes as
alternation, which is why five releases never showed it. **Who should take
this release:** every host wiring a non-Anthropic provider; a host on the
reference provider sees no behaviour change.

- **Changed: the prompt's subject placeholder** is spelled out
  (`user, or person:<name>, or org:<name>`) — no `|` a provider can
  concatenate.
- **Added: the subject refusal at ingest — exactly the defect and no wider.**
  A fact whose returned subject carries `|` (the alternation separator taken
  literally) is DROPPED, never written under any subject, and counted in the
  new operator counter **`subject_refused`** (present on every ingest return
  path; stripped from the MCP result like the others): there is no truthful
  placeholder for WHO a fact is about, so it cannot be re-filed the way an
  off-vocabulary relation is re-dispositioned, and the retry re-emits the same
  subject. Everything the suite already stores keeps storing — `user` in any
  case, `person:`/`org:`, a host's `task:` forms, and bare entity names such
  as `Rex` (the relay shape 0026 governs). `third_party_claim`'s claimant slot
  is exempt: free text by the prompt's own rule, and a receipt supersedes
  nothing.
- **Changed: `selfcheck` requires `supersession` 2/2** beside
  `injection_asserts == 0`; the 90% tolerance keeps the remaining checks. The
  scores 0.20.0 produced under that provider (12/13, history not retained)
  now FAIL, and the scorecard line reads `supersession 1/2 (must be 2/2)`.

## 0.20.0 — 2026-09-08

**Upgrade recommendation.** This release lands four accepted specs — the
transaction-time journal (0029) with the time-relative classifier (0030), as-of
queries (0028), procedural records with the `basis` axis (0037) — and one
trust-surface fix (0038). Three groups must act, each named at its entry
below: **every operator with an on-disk store** must migrate it offline before
this build opens it (`veracium migrate --db X --i-have-quiesced --backup REF`;
schema 12 → 13, the migration journals every existing edge once as a
`baseline` event and a below-head store refuses to open otherwise); **every
consumer running the reference extraction prompt on user-authored text**
should take the 0038 fix (a declared instruction is filed, never stored as a
disposition or a performed act); and **every host that moves export files
between installations of different versions** should note that a file holding
any procedural record is stamped format 11 and refused whole by an older
reader (a procedural-free export keeps its previous stamp, byte-identical).
**Rollback rule:** a store migrated to schema 13 cannot be opened by ≤ 0.19 —
roll back only by restoring the pre-migration backup the migration command
takes, never by downgrading the package over a migrated file; records written
by 0.20.0 do not exist in that backup. Library and MCP callers of the existing
surfaces change nothing: with no as-of or procedural caller every existing
surface reproduces the pre-feature oracle byte-identically (0029 V-COMPAT,
captured at the pre-feature tree; re-verified on this build for 0037's
declarative population). Minor bump per the 0.16.0 precedent: breaking
changes carried as minor with BREAKING notes.

*Acceptance evidence (research's oracles, each frozen before the code it
scores):* 0028's successor-lookup model, pinned at `1f1cf53` (file sha16
`aa3c5c33af0a1ad9`, `EXPECTED` block `7c49dfe9a9504ec4`), run against the
shipped accessor on all thirteen states for both principals; 0037's 972-cell
corpus at manifest amendment 7 (sha256 `4f80addce40f4357…`) consumed whole
through the shipped surface, 972/972, and its frozen procedure texts (sha256
`cddd9078a1fbaadb…`) driving the recognition rule's derived sets (22/22,
0/32, 0/5). Five external-review rounds did not find the nine spec and corpus
defects that implementation did (each recorded at its entry); the process rule
that follows — a spec is not verified until something has been built from it
— is research's to write.

**Procedural records and the `basis` axis (specs/0037, accepted 2026-09-07 at
external round 5; implemented 2026-09-08): a host-declared content kind that
is never asserted as fact, never enters recall's context, and is described
through one dedicated surface that names its basis.** Additive and inert
until a host records a procedure: every existing record is declarative and
its bytes are unchanged (the pre-feature oracle replays byte-identically).
⚠ **Export format 10 → 11, conditionally:** an export from a store holding
any procedural record is stamped 11 and an older Veracium refuses it whole
("newer than this Veracium understands"); a procedural-free export keeps
its previous stamp and is byte-identical to before. **Who should act:** a
host that records procedures and moves files between installations of
different versions.

- **Added: `Relation.relation_kind`** (`"declarative"` default,
  `"procedural"`) and **`follows_procedure`** in `DEFAULT_RELATIONS` — the
  one default procedural relation. The extractor's vocabulary is filtered by
  kind (a registry with a procedural relation renders a prompt byte-identical
  to one without it); an emitted procedural name is off-vocabulary and follows
  0025's residual path — never an edge under a procedural relation, never a
  stamp.
- **Added: `Provenance.record_kind`** (`None` | `"procedural"`, the registry's
  declaration stamped AT WRITE and read from the stamp ever after — a registry
  change moves no stored record) and **`Provenance.basis`** (`None` |
  `"stated"` | `"observed"`); both keys are ABSENT when `None`, so a
  declarative record serializes to exactly its previous 8 keys. A stored basis
  or stamp never changes on same-id replace; absorption carries the whole-set
  minimum basis (`observed` ≤ `stated`).
- **Added: `EvidenceContext.direct(basis=)` / `derived(X, basis=)`** — the
  closed basis domain refuses at construction. `remember` / `ingest_event`
  REFUSE a context carrying a basis (the extractor path cannot produce a
  procedural record).
- **Added: `Memory.record_procedure(user_id, summary, *, author, context,
  relation="follows_procedure", note=None, when=None, evidence_ref=None,
  source_id=None) -> str`** — the ONLY producer of a procedural record;
  every argument refuses its empty or malformed form before any write; the
  relation must be registered procedural; disclosure is derived, with
  quarantine-at-birth for a standing-revoked source; no episode is written.
- **Added: `Memory.describe_procedures(user_id, *, query=None,
  principal=None, limit=None) -> DescribeResult`** — one result per visible
  procedural record, described or withheld under the first failing conjunct
  of the ordered predicate (`kind_conflict`, `relation_unregistered`,
  `inactive`, `not_yet_valid`, `quarantined`, `use_only`, `basis_unknown`,
  `executable_detail`); the note is rendered in no field; a hidden record is
  in neither list; `withheld` is query-blind; the population is ordered
  before the cut and `total_describable` keeps it accountable after it.
- **Changed: the model-context choke point** — `gate.partition` /
  `partition_parts`, recall's selection, the proactive briefing and the wiki
  compiler exclude procedural records by the STORED stamp/basis rule with the
  named outcome `procedural_out_of_scope`, in NEITHER block; `Edge.assertable`
  is untouched.
- **Added: MCP `record_procedure` and `describe_procedures` tools.** The write
  tool is honoured under `VERACIUM_MCP_CAPABILITY=direct` only and refuses
  under `none` as an attempted elevation (counted like one); both return
  serialized refusals `{"ok": false, "refusal": <name>}` — a result shape NEW
  with these two tools; `remember` gains nothing and refuses a basis-shaped
  input.
- **Import (specs/0037 §4e):** the default path refuses a record as
  procedural on ANY of three raw signals — stamp, basis, or the RECEIVING
  registry's kind for its relation — per record, naming the signal
  (`procedural_refused`, `procedural_refusals` in the report); declarative
  records in the same file import as before; `restore=True` round-trips a
  store's own procedural records with their basis and refuses inconsistent
  markers as malformed.
- **Evidence:** the frozen 972-cell corpus
  (`tests/eval/procedural_describe/MANIFEST.json`) consumed whole through the
  shipped surface under both principals, 972/972; research's frozen
  procedure texts (`FROZEN_TEXTS.json`, authored 2026-09-08 — the accepted
  spec cited texts that had never existed) drive the recognition rule's
  derived opener and step-marker sets: 22/22 must-match, 0/32 paraphrased and
  plain, 0/5 must-not-match by name. One corpus column found wrong at
  implementation — the hand-filled boolean "absent from both recall blocks"
  was uniformly true, while §4a's unstamped rule renders the 108
  visible declarative-kind control cells exactly as today — and replaced in
  manifest amendment 7 by a three-valued `recall_expectation` DERIVED from
  kind_state × visibility (810 absent by kind, 54 absent by visibility, 108
  render as today); the expectation moved because the corpus disagreed with
  the spec, never because the code did something.
- **Found at implementation, recorded for the spec:** §4 called the
  `{ok, refusal}` tool-result shape "existing" (it is new); §2c attributed
  a str `when` refusal to `as_utc_required` (the surface's own gate); the
  extractor rows said an emitted procedural name is "dropped as invalid,
  nothing written" (0025 files it as `unclassified`; the guarantee is about
  the stamp and the prompt, not storage); §6a cited frozen texts that did
  not exist. Research's amendments fold at v15.

**As-of queries (specs/0028, accepted 2026-09-07 at external round 7;
implemented 2026-09-08): *what did we hold to be true at T*.** A
read-only, additive surface; `as_of=None` is today's recall, byte-identical
(the resolution is never invoked), and no stored byte differs.

- **Added: `Memory.recall(…, as_of=T)`.** The §4a resolution runs as a
  PRE-FILTER — one read of the store's injected clock, one read window,
  scope applied before historical eligibility — and normal ranking and
  budgeting run over the candidates it yields with the branch's own
  T-predicate; `Recall.as_of` carries a `Resolution` per returned edge
  (interval, reason, tag, 0030 status, a disclosed cause, the pointer).
  Under `as_of` the wiki, the episodes and the contested block are
  omitted: each is a statement about now. `T` in the future raises the
  typed `FutureAsOfRefused` (carrying `T` and the `now` compared against);
  a naive or non-datetime `T` raises `ValueError` before any comparison;
  `T == now` is permitted; the proactive path (`query=None`) refuses the
  axis. MCP is UNCHANGED (0028 §10 Q5: a library surface in v2).
- **Added: `Memory.facts_valid_at(user_id, subject, relation, T, *,
  principal=None, policy=None) -> list[AsOfFact]`** — the direct lookup,
  carrying the scope inputs recall carries: two principals against one
  store get their own answers, and no choice of `T` grants a principal a
  record its scope excludes (V-SCOPE-DIFFERENTIAL, research's round-4
  design executed as written).
- **Added: `SqliteStore.read_window(user_id)`** — the public read-only
  window (BEGIN under the instance lock or JOIN on the owning thread;
  ROLLBACK on error, COMMIT on exit), extracted from `current_state`,
  which now joins it. A resolution's every read joins ONE window: a
  correction committed by another connection during a resolution is
  invisible to its later reads (V-ONE-SNAPSHOT). **Measured cost, stated:**
  under the default rollback journal a resolution longer than a writer's
  `busy_timeout` makes that writer's commit fail with the store's wrapped
  refusal and lose its write (0028 §5, §7); under WAL the writer commits
  and the reader keeps its snapshot. Hosts running long resolutions
  against a write-heavy store raise `busy_timeout`, enable WAL, or accept
  the bound.
- **Added: `SqliteStore.edges_superseding(user_id, edge_id, *, principal,
  policy) -> SuccessorLookup`** — the direct-successor accessor, scan-backed
  and stated as such; the closed three-value `SuccessorDisposition`
  (`head` / `superseded` / `successor_unavailable`) with successors ordered
  `valid_from` asc then `id` asc. NOT an existence oracle: the queried
  edge is read through the caller's view like its successors, so a hidden
  queried id and a nonexistent one give equal whole objects, and a
  hidden successor and a missing one are one outcome with no cause. Run
  against the accepted model's frozen `EXPECTED` table on all thirteen
  states for both principals (file sha16 `aa3c5c33af0a1ad9`, block sha16
  `7c49dfe9a9504ec4`, pinned by research at `1f1cf53` before the code).
- **Added: `schema.NAMES_A_SUCCESSOR`** — the third registry total over
  `DISPOSITIONED_REASONS`, refusing at import in both directions; an
  eighth reason must now be dispositioned THREE times (`AS_OF_DISPOSITION`,
  `NAMES_A_SUCCESSOR`, and the resolution's own `RESOLUTION` table).
- **Behaviour, per 0028 §4b:** `superseded` returns the value held;
  `lapsed`/`decayed` return it flagged; `corrected` and `disputed` return
  a FENCED claim about what was believed, `corrected` with a pointer to
  where truth became (the chain head classified at T=now; at most 3 hops;
  a longer chain or a cycle is INDETERMINATE with its cause);
  `revoked_source`, an unregistered reason and a `None` reason on a
  retired row are NOT_RETURNABLE (fail closed); `absorbed_duplicate` is
  INDETERMINATE (the store cannot name a reachable absorber). No row
  upgrades 0030's verdict; INDETERMINATE is never silent about itself.
- **Internal, no behaviour change with `as_of=None`:** `ScopeView.shape`,
  `graph.fused_subgraph` and `Memory._fit_to_budget` gain keyword-only
  predicate/renderer hooks defaulting to today's `Edge.assertable` and
  `render_edges`, so the as-of branch never consults the wall-clock
  predicates (V-ONE-CLOCK; the absence proof's roots now include the
  resolution: static hits 0, behavioural violations 0).
- **Found at implementation, recorded for the spec:** 0028 §2c-i
  attributes the naive-datetime and non-datetime `ValueError` to
  `as_utc_required`, which takes a naive value as UTC and parses ISO text;
  the resolution enforces the table itself. Four post-acceptance
  amendments, written by research and folded into the spec at v15 (that
  row and V-NORM-FIRST's check; the contested omission; the "no reachable
  absorber" condition with its cause string deliberately unchanged; and
  V-HEAD's example state — a disputed head is retired, so 0030 classifies
  it `NOT_VALID_AT_T` at now, not fenced), each stating why the old text
  passed seven external rounds.

**Trust-surface fix (specs/0038, landed under a security-hotfix exception
with a retrospective due 2026-09-14): the reference extraction no longer
turns a user's DECLARED instruction into a stored disposition — and reports
the rate at which an undeclared one still slips through.** Measured over the
412-text ingestion capture through the shipped prompt (gpt-4.1, temperature
0): 31/66 bare procedural inputs ("Reuse the same password across service
accounts") were stored as `prefers` / `works_on` / `uses_tool` facts asserting
the user holds the practice, and 19/66 as episodes asserting the user
performed it — fabricated speech acts under intact provenance, rendered into
model context exactly as any true record would be. **Who should take this
build:** every consumer running the reference prompt on user-authored
text; a host running its own prompt inherits nothing but the schema change.
The fix is prospective — records already stored are untouched (a migration
would have to classify stored text, the inference that produced the defect);
a host that wants them out re-ingests or revokes the source.

- **Changed: `EXTRACT_SCHEMA.required` is `[triples, episode, instructions]`**
  — the extraction JSON gains an `instructions` array (may be empty, never
  absent) and the reference prompt directs each instruction, directive or
  stated practice the user states there, verbatim, and never into `triples`.
  The schema is a hint handed to the provider; it binds a compliant provider
  and nothing else.
- **Changed: ingest REFUSES a triple whose object equals a declared
  instruction** (casefolded, whitespace-collapsed, surrounding punctuation
  stripped — equality, never containment: no triple is decided to be an
  instruction without the model saying so), at the pass-1 filter before any
  edge exists. A `third_party_claim` is exempt: it is the receipt record of a
  notice, not a speech act of the user, and refusing it would erase
  received-claim history. Mixed events keep their declarative facts.
- **Added: `instructions_dropped` in the ingest report** — the count of
  REFUSALS (never of declarations, never of malformed members: a non-string
  or blank member is dropped uncounted; duplicates de-duplicate), present
  on every return path including the unparseable early return, at zero when
  nothing was refused. An `instructions` value of the wrong type (a string,
  an object, null) makes the response unparseable. The counter is an
  operator counter: the library report carries it; the MCP tool result
  strips it with the other extractor counters (a model that learns how often
  its coercions are refused learns to shape them); telemetry is untouched.
- **Not closed by this build, and measured rather than claimed:** a provider
  that coerces an instruction into a triple WITHOUT declaring it is not
  reached — that is the shipped behaviour, and the rate is reported by the
  0038 harness as a figure with no pass condition.

**BREAKING for existing stores — schema 12 → 13 (specs/0029, the
transaction-time carrier).** Two additive tables (`edge_event`, `store_epoch`)
and ONE data step: the migration journals every existing edge exactly once as
a `baseline` event holding the row's json as found, in one transaction with
the stamp. A store created by ≤ 0.19 must be migrated offline before this
build opens it — `veracium migrate --db X --i-have-quiesced --backup REF`
(specs/0013's operation; a below-head store refuses to open otherwise).
**Who must act:** every operator with an on-disk store. Library and MCP
callers change nothing: no public surface reads or accepts the new carrier
(V-INERT, V-MINT), and with no consumer every existing surface — recall, the
context block, export, the MCP tools — reproduces the pre-feature oracle
byte-identically (V-COMPAT, captured at the pre-feature tree before any
journaling code existed; `specs/evidence/0029/pre_feature_oracle/`).

- **Added: the append-only edge-event journal** (`edge_event`). Every write to
  the `edges` table — creation, same-id replacement, confirmation, invalidation,
  reinstatement, recompute, import — emits ONE event in the same transaction
  carrying the edge's FULL post-write serialization; an unchanged serialization
  emits nothing (the full-state trigger basis, 0030 R1-4's fourth site
  included). Kinds are closed: `created`, `mutated`, `invalidated`,
  `reinstated`, and the migration-only `baseline`. Events share a per-user
  transaction id (`txn`) per event-emitting write transaction, so a
  supersession's invalidate-A + create-B is one batch that any cutoff includes
  or excludes whole; `seq` is the ordering authority and `recorded_at`
  (store-minted, once per batch, never backwards) is telemetry.
- **Added: the read surface** `Store.edge_events(user_id, *, edge_id=None,
  until_txn=None)`, `Store.edge_state_at(user_id, edge_id, until_txn)` — the
  RAW carrier (`RawEdgeState`: payload VERBATIM text, identity from the row
  columns, no parse) — and `Store.epoch_txn(user_id)`. A cutoff below a
  migrated user's epoch raises `PreEpochQuery` (the store fabricates no
  pre-epoch knowledge); a fully-journaled user has epoch 0 and never refuses.
- **Changed: every edge-writing entry point takes `BEGIN IMMEDIATE` before any
  allocation read** (specs/0029 §4a; two `SqliteStore` instances on one file
  allocate disjointly; the DEFERRED schedule is kept as an executable negative
  control). The 0007 busy-timeout discipline applies: waits, then refuses loudly.
- **Changed (fail-closed, one layer earlier): an invalidation reason outside
  `DISPOSITIONED_REASONS` now REFUSES the write** (V-KIND) instead of retiring
  the edge with an unregistered reason. Before, such a reason reached the wiki
  drop's retain-set check; now it never reaches the writer. The refusal is
  TOTAL across producers because it sits in the emission choke point
  (`_journal_edge_write`), which every `edges` writer calls, and
  `_invalidate_edge_row` is the sole `active=0` writer (0004 W7's structural
  test) — not in `invalidate_edge`, where a reader checking one entry point
  would find no guard. 0004's retain-set polarity is unchanged over the
  registered domain (test updated to say so).
- **Changed: `forget_user` erases the user's events in the same transaction**
  (V-ERASE).
- Write-path cost: one extra row per edge write plus two `MAX()` reads inside
  the already-held write lock. No figure is stated until it is measured under
  the harness's conditions (the 0027 ~6% note is the precedent for how).

- **Fixed: the two retire writers normalize the instant they are handed.**
  The revocation path (`revoke_source`, since 0.17.0) hands the operation
  time as ISO text, and `_invalidate_edge_row` / `_retire_episode_row`
  assigned it raw into datetime fields (`Edge`/`Episode` have no
  validate_assignment). The PERSISTED bytes were never wrong — the text
  serialized identically — but the live object carried a `str` where its
  journal-reconstructed twin carries a `datetime`, and every
  revocation-retired record emitted a Pydantic serializer warning (reproduced
  in shipped 0.19.0 by research's Tier 8 run). Both writers now route through
  `as_utc_required`: a datetime or ISO text becomes a UTC-aware instant, and
  anything else REFUSES the write. **Who is affected (these two writers):**
  operators running revocations see the warning disappear; no stored data
  changes and no migration is needed. Regression: the real revoke path runs
  with serializer warnings promoted to errors, and live == reconstructed by
  attribute.
- **Changed (write path; dispositioned separately from the fix above): the
  recompute writer normalizes its instants too.** The class was swept from
  the models' datetime-typed fields (research): the only other assignment
  site, `_recompute_edge_row`'s parse, persisted a NAIVE instant for text
  without a zone, safe only because every comparison takes naive as UTC. It
  now parses through `as_utc_required`, so a zoneless input would persist an
  AWARE instant — different bytes (`…T00:00:00` → `…T00:00:00Z`) from the
  same input before this release. **A checked no-op for every caller in the
  tree today, not an inherited claim:** the recompute writer's only caller is
  the revocation sweep's effect applier, and the sweep REFUSES any recompute
  value that is not the canonical Z-suffixed UTC form
  (`revocation_sweep.py`, "not the writer's canonical Z-suffixed UTC
  json_datetime"), so zoneless text cannot reach the writer through any
  shipped path. A future caller supplying it will persist an aware instant
  rather than a naive one; journal payloads written after this release by
  such a caller would differ byte-wise from before, which is the journal
  recording what was actually written.

**Added (additive, not wired into recall) — specs/0030, time-relative
classification.** The primitive 0028 v2's `as_of=` recall will call:
`veracium.asof.classify_as_of(envelope, snapshot_raw, current_state, T, now,
view=None) -> Result{status, held_at_K, flags}` and its boolean
`assertable_as_of`, transcribed rule-by-rule from the accepted spec's
pseudocode. Two verdicts, not one: `held_at_K` ("the store held this belief at
K", from the snapshot alone) and `status` ("may this be asserted as fact now",
the current caps applied, which only ever subtract). Seven closed statuses
(`GROUNDED_AS_OF`, `FENCED_AS_OF`, `EXCLUDED`, `NOT_VALID_AT_T`, `MALFORMED`,
`SCOPE_HIDDEN`, `IDENTITY_UNBOUND`); one flag, `stale-at-recall`. Nothing on
the current recall path calls it; `Edge.assertable` is unchanged (caller-grep
and the post-0027 oracle replay in `tests/test_0030_asof.py`).
- `veracium.schema.AS_OF_DISPOSITION` — the TOTAL as-of disposition beside
  `DISPOSITIONED_REASONS` (key-equal or the import fails; unknown key → fenced
  at lookup). Deliberately not `WIKI_RETAINING_REASONS`: `superseded` drops
  from the wiki yet was validly true inside its interval.
- `veracium.schema.as_utc_required` / `as_utc_optional` — the two normalizers
  (a datetime or a raw payload's ISO text → UTC-aware; `None` refused by the
  required form, kept by the optional one).
- `Store.current_state(user_id, edge_id, *, principal=None, policy=None) ->
  CurrentState` — the current row VERBATIM, the three-valued source-restriction
  verdict from the STANDING source state (clear / restricted / undeterminable,
  returned never raised), the read token and, with a principal, the scope
  decision computed IN the read window — all from ONE window the store owns
  (one world under both journal modes).
- `veracium.asof.adapt` — the raw adapter: journal or row TEXT → a validated
  record with `quarantined`/`use_only` DERIVED (they are never serialized), or
  `None`; duplicate JSON keys refused at the boundary. Parsing is the
  consumer's (0029 promises bytes); a payload the current model rejects is
  CLASSIFIED (`MALFORMED`, or `SCOPE_HIDDEN` under a view), never raised.

## 0.19.0 — 2026-09-04

**Upgrade recommendation:** every host running `veracium-mcp` should take
this release — the MCP surface's provenance is now attested by the HOST, not
declared by the model (specs/0031 Phase A). A deployment that declares nothing
runs as before EXCEPT that new MCP writes carry the `third_party` baseline and
a model-supplied `derived_from="user"` no longer elevates a write to
mentionable; a first-party embedded host sets `VERACIUM_MCP_CAPABILITY=direct`
(or `build_server(capability="direct")`) and recovers the mentionable class by
attestation. Every MCP tool loses its `user_id` argument (the host process is
the identity boundary). **Rollback rule:** roll back only to **0.18.1**, the
designated compat release — never to 0.18.0, which would silently ignore the
capability variable and restore the pre-attestation default. Records written
under `direct` keep their meaning after a rollback. The on-disk store schema
and the export format are unchanged from 0.18.0; no migration.

*Acceptance evidence (research):* the Phase A capability floor was verified
against a pre-committed instrument frozen BEFORE the implementation existed
(veracium-harness `23c3ba5a`, tier-8 manifest digest `662ac798…`, 21/21 on
first contact) and receipted after merge (harness `5c778f6`: the P3-3
elevation retired on purpose with its structured re-pin receipt; before-state
preserved at digest `ebfabbfd…`).

- **Fixed: the offline launcher's suite passes from a source export.** The
  review-closure ledgers landed this week cite text-only closures with
  `git show <fold-sha> -- <spec>`; those rows are openable in a git checkout
  and unrunnable in an sdist export, which is where
  `specs/evidence/offline/run_offline.sh` runs the suite — found red by this
  release's own battery. The evidence runner now declares those rows skipped
  with the cause named in its transcript when the tree has no `.git`, as a
  whole set only (a partial skip is refused by the transcript validator), and
  refuses any such skip inside a checkout, so CI still executes every row.

*Note on this file:* the 2026-09-02 fold `efab441` overwrote the `## 0.18.0`
heading with `## Unreleased`; it is restored below exactly as tagged.

- **⚠ BREAKING (MCP surface): the host attests provenance; the model can only
  restrict it — specs/0031 Phase A.** Three changes to `veracium-mcp`, all
  from the accepted spec's own text:
  1. **`author` has no default.** An MCP `remember` with no `author` now
     stores the DEPLOYMENT's baseline class instead of `"user"`: `third_party`
     unless the host attests otherwise. A supplied `author` or `derived_from`
     can only restrict trust below that baseline; an attempted raise is
     discarded (and counted for the operator in the library-level report as
     `provenance_raises_discarded`, which never reaches the tool result).
     Under the default, a model-supplied `derived_from="user"` therefore no
     longer elevates a write to mentionable, and `author="assistant"` stores
     the baseline rather than the assistant class (specs/0031 §2c-i, V-INERT-
     UNDER-NONE). Malformed values still raise, regardless of capability.
  2. **`VERACIUM_MCP_CAPABILITY`** (or `build_server(..., capability=...)`,
     keyword-only): the host's attestation about every call on this server.
     Unset means `none`. `direct` means every call originates in a turn with
     the authenticated principal AND the deployment stands behind the model's
     authorship labelling as its own; events then default to the user's class
     and are mentionable. Read once at startup; the empty string or any other
     value refuses to start. **Attested by the host, not verified by
     veracium** — a server reachable by a public or untrusted agent must
     leave it unset.
  3. **Every tool loses `user_id`** (specs/0031 §4b-iii): `remember`,
     `recall`, `answer` and `maintain` act on the deployment's user
     (`VERACIUM_USER` / `default_user`). The host process is the identity
     boundary; over stdio a model-supplied id bound nothing — and on `recall`
     it was a cross-principal read. Multi-user hosts run one process per
     principal.
  Regimes (specs/0031 §5): a host that declares nothing runs identically to
  before EXCEPT that MCP writes now carry the third-party baseline and a
  model's `derived_from="user"` no longer raises trust; an embedded
  first-party host declares `direct` and recovers the mentionable class by
  attestation. **Who should take this release:** every host running
  `veracium-mcp` whose memory is populated through the `remember` tool —
  writes made before this release keep their stored provenance (a record is
  a fact about its write, not a view over current configuration); writes
  after it are held at the baseline until the deployment attests. Hosts
  embedding the `*_impl` functions get the same behaviour through
  `remember_impl(..., capability=...)` and the new `remember_report` (the
  full report with operator counters). Phase B (proposals) is not in this
  release.
- **⚠ BREAKING (behaviour): a fact is not assertable before it is true.**
  `Edge.assertable` and `Episode.assertable` now consult a valid-time
  predicate at the present — `valid_now`: an edge whose `valid_from` has not
  yet arrived, or an episode whose `date` is after today (UTC), is no longer
  asserted as fact by recall's GROUNDED channel, the wiki compile, or any
  other consumer of `assertable`; it stays stored and becomes assertable by
  itself when its time arrives (nothing is rewritten). Routing of the
  withheld records follows the accepted 0023 §4a-iv contract unchanged: a
  not-yet-valid edge is withheld from recall exactly as an inactive edge
  is, and a future-dated episode is fenced into the unverified section
  (visible as a claim, never asserted) rather than suppressed. This is the S2
  ruling (owner, 2026-08-31; specs/0031 §5's ordering precondition; the
  measured divergence cell in specs/0030 §4e): ingest already refuses dates
  beyond `MAX_FUTURE_SKEW` (1 day), but inside that window an MCP
  `remember` could write a fact that was assertable a day before it became
  true. **Who should take this release:** hosts whose agents can write
  future-dated facts through the MCP `remember` tool — under 0031 Phase A's
  `capability=direct` (not yet shipped) that window becomes agent-reachable,
  and this release closes it first, as ruled. Hosts that never write
  future dates see byte-identical behaviour. Comparisons are UTC-aware via
  the new `schema.as_utc` (a naive `valid_from` is taken as UTC).
- **Fixed: the revocation sweep's recompute path now refuses malformed
  persisted absorption payloads with its declared `RevocationError`
  instead of crashing.** A `contribution_ledger` absorption row whose
  `base`/`contributor` sides lack (or mistype) the fields the recompute
  fold consumes (`valid_from`, `observed_at`, `confidence`) previously
  escaped as `KeyError` — and, when the corrupt row predated the
  revocation, crashed `revoke_source` itself mid-transaction. The sweep's
  reader now validates exactly what it consumes before folding (fields
  present; datetime fields strings, confidence numeric and not bool),
  raising `RevocationError` so the R19 transaction rolls back cleanly on
  the write path and consumers can classify the store as unreadable on
  the read path. The shipped writer already refuses these shapes at write
  time; this closes the reader's half against at-rest corruption and
  ledgers outliving their writer. Found by the 0029/0030 external review
  (round 9); regression coverage: the reviewer's exact payload plus a
  12-cell field×type×side matrix, both operation orders.

## 0.18.0 — 2026-08-31

**Upgrade recommendation:** hosts that want paraphrase/synonym recall
("my vacation" finding "trip to Tokyo") should take this release and
supply an embedder — any `Embed` implementing `__call__`, `id()`, and
`dim()` activates the semantic lane; without one, recall behaves exactly
as 0.17.0 (`semantic="auto"` reports `no_embedder` and stays lexical), so
no consumer must act to stay correct. ⚠ **BREAKING for existing stores:**
the on-disk store schema moves **11→12** (one additive table); a store
created by ≤0.17 must be migrated offline (`veracium.store.migration.
migrate_store`) before this build opens it — the migration is additive,
reversible (`DROP TABLE edge_embedding`), and requires no backfill.

- **0027 — semantic hybrid recall (EXTERNALLY ACCEPTED 2026-08-31, nine
  review rounds closing at "ACCEPT — 0027 is closed"; implemented, and the
  acceptance measurement passed all three pre-committed criteria — the
  recorded verdict lives in the spec's Review closure, figures held
  internal by the §6a rider).** An
  ADDITIVE, RRF-fused (K=60), lexically-anchored semantic lane: recall
  gains `semantic="auto"` (attempted iff a host `Embed` with `id()`/`dim()`
  is configured; every failure degrades to lexical with a closed
  `Recall.semantic_status`, never an exception) and a parallel id-keyed
  `Recall.recalled_edges` provenance carrier (`Recall.edges` unchanged).
  Semantic changes WHICH edges are candidates and their ORDER — never a
  record's trust classification (poison surfaces fenced; classification
  stays at render). Collapse decides membership from the lexical lane
  alone while the output keeps the fused order; scope's lens is applied to
  BOTH lanes before ranking (a deliberate order amendment for
  principal-bearing recall; `principal=None` semantic-off recall is
  byte-identical to 0.17.0, pinned by a frozen pre-feature oracle). Store
  schema 11→12: the additive `edge_embedding` derived-index table —
  vectors keyed (edge_id, embedder_id, content_digest), stale-excluded on
  text change, deleted inside `forget_user`'s transaction, never exported.

## 0.17.0 — 2026-08-30

**Upgrade recommendation — consumers whose hosts ingest user-relayed
third-party content ("my doctor said…", "the landlord told me…")
should take this release**: before it, such a relay filed by the
extractor under a concrete relation was asserted as the user's own
fact (the B02/B07 laundering class, open since the 0024 baseline
measurements). It is closed here. Hosts upgrading from ≤0.16 must
also act on the 0011 entries below: first-party ingest call sites
need an explicit `context=EvidenceContext.direct()` (absence now
floors conservatively), and `correct()` callers must handle
`CorrectionRefused` on other-entity facts.

- **0026 — label/value agreement check (accepted 2026-08-30, external
  round 12; twelve external + fourteen internal review rounds) —
  IMPLEMENTED. ⚠ BEHAVIOR CHANGE.** A relayed claim whose note or
  object matches the versioned marker lexicon is never asserted as
  the user's fact, whatever relation the extractor filed it under —
  closing the B02/B07 relay-laundering class ("my doctor said…"
  filed under a concrete relation used to land assertable). The
  detector (`veracium.agreement`, lexicon `0026-lex-10`) is pure,
  closed, and directional by grammar: the agent governs, outbound
  (user-as-source) never matches, ambiguous restricts conservatively.
  RESTRICT-ONLY: a marked relay FLOORS disclosure
  MENTIONABLE→USE_ONLY and never raises (quarantined stays
  quarantined); marker absence changes nothing (marker-free stores
  are byte-identical, proven against a frozen pre-feature export).
  Each affected edge carries a structured `agreement` record
  (markers + direction + lexicon version, None-omitted); §3c
  demotion-direction disagreements are recorded without disposition
  change. `remember` results carry `agreement_floored` /
  `agreement_recorded` on every path (the MCP surface strips them).
  Export rides a CONDITIONAL format bump (10 for agreement-bearing
  stores; marker-free exports stay at 9): old readers refuse rather
  than silently drop. Import is mode-split per the accepted decision
  table: default RECOMPUTES under the current lexicon (incoming
  values diagnostic-only, mismatches counted); `restore=True` is
  trust-faithful for well-typed records (foreign lexicon versions
  verbatim with opaque markers) and RAISES on malformed with nothing
  written. Measured acceptance gate: 0.64% false-positive rate
  (439 of 68,479 grounded first-person triples) against the
  pre-committed 2% bar. The floor covers all three establishment
  boundaries — ingest, default-mode import recomputation, and
  `correct()` (a corrected fact's preserved note passes through the
  same floor and derivation site; found by research's implementation
  red-team, closed same-day) — and §3c's `user_source` record is
  scoped to the extractor-demotion case.

- **0011 (accepted 2026-08-29, external round 19) — implementation in
  progress.** Landed so far:

  **E4 — trusted ingress is a capability. ⚠ BREAKING for every
  context-less ingest caller.** `derived_from=None` stops being
  trusted-by-omission: `ingest_event` and `Memory.remember` gain
  `context` — the host's POSITIVE declaration, minted as
  `EvidenceContext.direct()` (first-party capture attested) or
  `EvidenceContext.derived(X)`. **A call that declares nothing — no
  `context`, no legacy `derived_from` — now floors the content class to
  `derived(THIRD_PARTY)`: the event is kept but nothing extracted from
  it is assertable.** The legacy `derived_from=X` keyword remains
  honoured as a positive `derived(X)` declaration; a malformed or
  forged context RAISES with nothing written (closed domain, no
  coercion, subclasses refused at the persistence site); passing both
  carriers raises. `remember` deliberately does not mint `direct()` on
  the caller's behalf — that would recreate trusted-by-omission one
  layer up. The MCP `remember` tool and the CLI stay context-less on
  purpose and therefore now floor: content relayed by a model caller
  or typed at an operator prompt gets the conservative class until a
  host-attested capability exists for those surfaces. **Upgrade path:
  add `context=EvidenceContext.direct()` at call sites that genuinely
  capture first-party events; leave relay/unknown-origin sites alone
  and they inherit the safe floor.**

  **E3 — `CONTESTED` at every reader.** Contention stays `0003`'s
  refusal-scoped notion with NO stored carrier — derived per read from
  the live refusal set. The per-reader obligations are now PINNED by
  standing tests against the shipped surfaces: recall asserts the
  CONTENTION (never one side as a plain current fact), maintain
  resolves nothing across a contested pair while `0012` per-edge
  expiry still fires, an exported/imported pair arrives uncontested
  (refusal records are store-local), and a directly-inserted
  distinct-value pair is not contested.

  **E6 — the history partition.** `graph.history_label` +
  `HISTORY_LABELS`: THE one five-label vocabulary
  (`RETIRED_HISTORY` / `QUARANTINED_CLAIM` / `CONTESTED_CURRENT` /
  `UNVERIFIED_CURRENT` / `GROUNDED_CURRENT`), first-match over the
  §4f precedence table — total by the catch-all, exclusive by
  first-match, verified cell-by-cell against an independent oracle
  over the full cross-product. `introspect` gains a `history_labels`
  count block derived from it (additive key; the labelling reads
  disclosure, never writes it — the 0023 N2 sweep extends over the
  new surfaces).

  **E5 — `correct()` through the ladder, authorised (closes
  `M7-correct`). ⚠ BEHAVIOR CHANGE.** `Memory.correct()` no longer
  writes storage directly: the correction goes through the same atomic
  CAS plan machinery as extractor supersession, carrying a
  `CorrectionAuthorisation` bound to *(store origin, prior edge id,
  replacement value digest, kind, acting principal)* and verified
  element-by-element INSIDE the transaction — a forged, rebound,
  replayed-against-a-different-prior, foreign-origin, or
  cross-principal authorisation aborts with nothing written. This is
  an INTEGRITY BINDING, not authentication (`correct()` mints it from
  caller values): `correct()` is a protected host API — the host
  authenticates the principal and establishes intent. §4b now applies
  to corrections too: correcting a prior about an OTHER-class subject
  on bare self-assertion raises `graph.CorrectionRefused` after a
  durable refusal row commits, where it previously silently retired
  the prior — that silent path was the defect.

  **E1+E2 — the subject axis.** `graph.subject_class(user_id, subject)`
  — total, `OTHER` by default, the 0024 canonical-subject predicate —
  and the §4b refusal cell: a bare self-assertion (author `USER`, no
  derivation) can no longer retire a prior fact about an OTHER-class
  subject; the refusal is recorded like every other refused
  supersession. Rule version: `supersession-authority-v2`.

## 0.16.0 — 2026-08-26

- **0001 — THE GENERATED-CONTENT TRUST CLASS IS LIVE** (accepted at
  external round 18, 2026-08-25, after eighteen rounds; implemented
  2026-08-26). Assistant-authored material is now a first-class
  evidence class rather than something a host must remember not to
  mislabel: `EvidenceAuthor.ASSISTANT` sits at **rung 1** on the
  supersession ladder — below `USER` (3) and `SYSTEM` (2), above
  `THIRD_PARTY` (0) — and everything it authors is held at
  **`USE_ONLY`: it may inform an answer and is never asserted as
  fact.**

  **Upgrade recommendation — consumers ingesting third-party content
  should take this release.** Before it, a record authored by the user
  or the system but derived from a third party was rendered to the model
  as `third-party-reported`, which names the RELAY as the reporter. That
  is an inaccurate provenance claim about unverified material, on the
  surface the model actually reads. It is corrected here, and the
  fail-safe added alongside means an unlabelled author can no longer
  inherit another class's origin string at all.

  **BREAKING — rendered provenance labels.** Origin labels are now
  keyed on the PAIR `(author, derived_from)` with the capping axis read
  first, so a record DERIVED FROM a third party is described as a
  relayed claim whoever carried it. Two label strings change for
  material that already exists:

  | author | `derived_from` | before | now |
  |---|---|---|---|
  | `user` | `third_party` | `third-party-reported` | `third-party-derived` |
  | `system` | `third_party` | `third-party-reported` | `third-party-derived` |
  | `assistant` | — | *(unreachable)* | `assistant-generated` |
  | `user` / `system` | — | `third-party-reported` | `unverified-origin` |

  Rendered text IS model context, so this is a behaviour change and not
  a cosmetic one: the old string named the RELAY as the reporter. An
  author with no deliberate label now fails safe to `unverified-origin`
  rather than inheriting another class's string — **a confidently wrong
  provenance is worse than a missing one**, because nothing downstream
  can discount it.

  **Store schema 10 → 11, stamp-only.** `SCHEMA_V11` is byte-identical
  to `SCHEMA_V10`; the bump exists so a pre-`ASSISTANT` reader REFUSES a
  v11 store at open with a typed `StoreVersionError(reason="newer")`
  instead of failing mid-read on a value its enum does not know. v11
  inherits all five accepted v10 manifestations by digest. Migration is
  a stamp across the constructor, v6 and v9 routes; no data moves.

  **Export FORMAT_VERSION 8 → 9.** A v9 export round-trips; an importer
  at FORMAT ≤ 8 refuses it as newer with our message rather than a
  validation traceback. On the DEFAULT import path an `ASSISTANT`
  record arrives capped to `THIRD_PARTY` (the ratified 0005 boundary —
  an imported file cannot carry its own trust); `restore=True`
  preserves the author exactly.

  **Measured** (`bench/run_bench.py --live`, then `--compare`: no
  regressions). Eval 5/5 with **injection asserts 0**; robustness over
  the 20k sample — 0 internal crashes, 0 cross-user leaks, 0 injection
  leaks, 0 malformed edges. The engine tier carries a **real ~6% cost
  on the write paths** and it is stated rather than absorbed into the
  1.5× flag it comfortably clears: `remember` 12.732 → 13.576 ms p50
  (×1.066) and `record_outcome` 12.869 → 13.648 ms (×1.061) against
  0.15.0's quiet baseline. Read paths are flat (`recall` ×1.019,
  `recall_budgeted` ×0.955). The write cost is where the work landed —
  pair-keyed label derivation, the widened author enum on the
  supersession ladder, and v11 stamp handling.

  Both engine records ship. 0.15.0's release bench was contaminated by a
  concurrent test run and read 46% high, so this release re-measured the
  engine tier a second time with the load sampled either side; the two
  runs agree within 1.3%, which is what establishes the 6% as product
  cost and not contention. Trust canary failures: 0.

  **MCP/CLI author surfaces.** `remember(author="assistant")` is
  accepted — a self-DEMOTION to rung 1, which is the honest declaration
  for model-authored text. `"system"` remains deliberately unavailable
  through those surfaces: it denotes veracium's own maintenance output,
  and a trust-bearing field must not be settable by the party whose
  trust it describes. An unrecognised author still fails CLOSED rather
  than resolving to the highest-authority class.

## 0.15.0 — 2026-08-24

- **0024 as amended by A1 — AUTHORSHIP BEFORE STRUCTURAL QUARANTINE,
  live at last** (A1 accepted at external round 24, 2026-08-24, on the
  frozen U1–U7 surface with revised U2 — twelve amendment rounds after
  the paired measurement held the v7 mechanism out of 0.14.0). An
  extractor-emitted `third_party_claim` whose canonical subject is
  exactly the user is re-dispositioned: relation → the reserved
  non-functional `unclassified`, the original preserved in
  `Edge.original_relation`, and disclosure set to **uniform USE_ONLY —
  may inform answers, never asserted as fact** (the A1 change: the
  measured population behind the self-contradictory label is 4 genuine
  relays per 1 genuine self-statement, so the label's collapse licenses
  use, not assertion; v7's author-rules disposition made those relays
  assertable and was reverted before 0.14.0 shipped). Every accepted
  floor still applies after — a standing-revoked source's records land
  QUARANTINED regardless. The `redispositioned` counter goes live on
  its pre-wired carriers. U2's executable oracle is the two-branch
  constant (revoked → QUARANTINED, else USE_ONLY); assertion for this
  cell awaits content evidence (0024 Q5 → the 0026 agreement check).
  Stores that never see `third_party_claim` are byte-identical (U4).

  **Measured on the frozen 48-probe paired instrument** (research, main
  @ `984dee8`, scored against pre-registered expectations; dev
  independently recomputed the figures below from the shipped records):
  the over-quarantine defect stays fixed (A08 leaves quarantine) while
  **no probe anywhere moves from quarantined to assertable** — the
  amendment's whole point. The relay floor in the bait cell returns to
  its pre-fix level, **14 of 16 non-assertable** (the v7 mechanism had
  degraded it to 10/16; A1 restores it). It is NOT 16/16: the two
  remaining are the pre-existing B02/B07 shape where the extractor
  files a relay under a CONCRETE relation and never reaches the
  quarantine branch at all — untouched by this fix by construction, and
  the subject of the queued label/value agreement check (`0026`).
  *Instrument note, standing across three runs:* this probe set's
  extraction is not bit-stable at temperature 0, so per-probe RELATION
  identity is advisory; DISCLOSURE and the assert/hedge outcome are the
  load-bearing comparisons. Two canary probes drifted at extraction in
  this run (one to a concrete relation floored USE_ONLY by the ordinary
  author rules with no re-disposition, one producing a conservative
  edge where earlier runs produced none); neither is a floor
  regression, and both answers still decline to assert.

## 0.14.0 — 2026-08-23

- **0024 (authorship before structural quarantine): accepted, implemented,
  measured — and HELD from this release.** The coherence mechanism landed
  on main (`1b542b9`, all U1–U7 checks green) and Research's probe-paired
  measurement then sized the spec's §8 residual at 4/16: four genuine
  relays whose extracted triple subject was `"user"` lost their structural
  quarantine and became assertable, against 1/16 correctly restored
  (relay floor 14/16 → 10/16 on the probe set). The disclosed,
  externally-accepted residual measured four times the gain, so the
  implementation is reverted from this release rather than shipped; the
  `redispositioned` counter remains present-at-zero on every carrier. The
  destination is a narrow amendment (re-disposition to `use_only` — keep
  the never-assert floor on the ambiguous population) through external
  review, with the note/label agreement check as its companion. Records:
  the paired run is banked in the research workspace; the implementation
  and its 16 tests live in git history at `1b542b9` for the amended
  return.

- **selfcheck: the revocation guarantee is now user-runnable.** `veracium
  selfcheck` (and `Memory.self_check()`) gains a fourth check walking the
  0022/0023 seam end to end on a throwaway store: revoke a source → its
  standing records leave the read seam → re-entry attempts (a restatement
  and a changed value) land **quarantined at birth** with
  `birth_revocation_digest` binding them to the standing revocation → no
  standing record moves (byte-checked) → an unrevoked source is untouched →
  consolidation pools exclude the source → the floor survives
  export/import → a lift restores exactly what the revocation took, never
  the birth floor. Eight cells fold into the existing content-free
  `total_ok`/`total_n`; the per-check counters are not telemetered
  (whitelisting is a consent-schema decision).

- **0025 — THE RELATION VOCABULARY IS CLOSED** (accepted with 0024 at
  external round 12 after twelve rounds; implemented 2026-08-22; 0024's
  own mechanism was implemented, measured, and HELD — see its entry
  above).
  Extracted relations are now constrained to the registry: the host's
  `relations` dict is validated at the `ingest_event` boundary (empty and
  conflicting-reserved-shadow registries refuse with `RegistryError`), the
  reserved members `unclassified` and `third_party_claim` are always
  resident, and every stored relation is registry-resident. Off-vocabulary
  relations take ONE re-extraction retry per event (its own `distill-retry`
  usage role); the residual lands on `unclassified` with the original
  relation in the new typed `Edge.original_relation` field — omitted from
  every serialization when None, so unaffected edges stay byte-identical.
  The ingest result gains five counters (`invalid`/`retried`/`recovered`/
  `residual`/`redispositioned`, zeros present on every path); the MCP tool
  result strips them; telemetry carries them at consent schema v4. SQLite
  SCHEMA v10 adds `supersession_operations.request_digest_domain`: new
  digest-bearing receipts stamp the v2 request-digest domain, migrated
  receipts compare dual-domain — lost-response retries now replay across
  the era boundary (the confirmed `0014` interface amendment) — and
  uninterpretable domains refuse with `ReceiptDomainError`. Export
  `FORMAT_VERSION` 8 (a v7 file imports absent→None; old readers refuse
  v8).

## 0.13.0 — 2026-08-21

- **0004 + 0022 + 0023 — SOURCE REVOCATION, THE COMPLETE SEAM** (accepted
  atomically at external round 21 after twenty-one rounds; implemented
  2026-08-20/21). A revoked trust decision now reaches everything derived
  from it, and nothing revoked can re-enter:

  - **0004**: a derived view must not outlive a revoked trust decision. The
    wiki drop generalises into the sole `active=0` writer, keyed on a
    RETAIN-set registry (an unrecognised reason drops, fail-closed); W1–W8.
  - **0022**: `source_revocations` (SCHEMA v9) — an append-only ledger whose
    standing state derives by append ordinal alone (a hostile clock orders
    nothing). The R19 operation: allocate, re-read, plan, append, apply,
    commit-or-rollback in ONE serialised write, failure outcomes total. The
    sweep is the normative reference ported verbatim, transitively closed,
    proven by a 20-vector differential corpus against the product store;
    episodes gain retirement (JSON field + the sole read seam, no DDL) and
    `revoked_source` retirements drop the wiki through 0004's registry.
    Completeness statements are audit-event-only (Q6, approved).
  - **0023**: non-revival. `Episode.assertable` — one derived predicate,
    six consumers routed through it (the render fences rather than
    suppresses); quarantine-at-birth for a standing-revoked source's writes
    (no host refusal mode — Q1, both names; a lift never revisits the birth
    floor — Q2); non-revival guards at reinforcement, absorption,
    supersession (refusal recorded; the reverse still works), consolidation
    (`partition_cold`), and import (the destination-standing cap applies in
    BOTH modes — no flag on a file overrides this store's standing state);
    N1–N15 with the spec's canonical test names, including the adversarial
    inventory bite-test.
  - ⚠️ Behaviour notes: episode disclosure is now SET AT INGEST (third-party
    influence caps at USE_ONLY; legacy rows stay fenced via the subsuming
    derived property); stores migrate v8→v9 additively.

## 0.12.0 — 2026-08-20

**The principal boundary: scoped recall (0020) and scope under maintenance (0021).** A scope that recall enforces but derivation ignores is a boundary with an unlocked back door, so both halves land together — the read surfaces and the write/maintain surfaces.

- **0021 scope under maintenance, slice C — THE WRITE AND MAINTAIN HALVES**
  (spec `specs/0021-scope-under-maintenance.md` §3/§4a–§4d; implemented,
  unreleased). 0020 without this was a boundary with an unlocked back door:
  a scope that recall enforces but derivation ignores leaks across principals
  through synthesis.

  - **Consolidation outputs CLEAR their inherited identity** (§4a / W8).
    `_derive_output_metadata` copied `inputs[0].provenance` wholesale, so a
    mixed A+B consolidation output CLAIMED identity A. Outputs now carry
    `origin=None`, `source_id=None`: store-authored means store-identified,
    the origin resolves to the local singleton at read (0006 I9), and
    membership can only travel through the 0014 ledger. Every other derived
    field (SYSTEM author, whole-set-minimum trust, date range) is unchanged.
  - **Absorption partitions by resolved identity** (§4c / W2). A cross-scope
    or UNRESOLVED prior is no longer an absorption candidate — it accumulates
    as a separate edge, exactly as a cross-CLASS prior always has. The atomic
    primitive refuses such a plan independently of the planner.
  - **Write-time FLATTENING** (§4c / W14): when an absorption commits, the
    survivor's rows gain copies of the absorbed prior's *transitively closed*
    row set — same operation, `scope-attribution` site, payload
    `{"flattened": true}`, native per-row keys. Every post-0021 survivor's
    row set is its whole ancestry by construction, so the A→B→C chain that
    defeats a single-level read cannot recur on rows we write, and a later
    prune of an intermediate is harmless.
  - **Consolidation runs PER SCOPE** (§4b / W1, W10). Cold candidates are
    partitioned by resolved identity, one 0010 operation per pool (own claim,
    lease, crash-safety), pools ordered by digest with the unidentified pool
    last. **Thresholds are per pool: four A records + four B records with
    `consolidate_min_batch=8` is a NO-OP.** Pools fail INDEPENDENTLY — a
    pool's model error leaves the pools that already committed standing and
    later pools still run.
  - ⚠️ **BEHAVIOUR CHANGE, disclosed (§2): partitioning is
    POLICY-INDEPENDENT.** An identity-bearing store gets partitioned
    consolidation even if no host ever configures `scope_groups` — policy is
    a read-side concept, and no process's configuration may change what the
    store MERGES. A store with **no** identities keeps identical stored state
    and identical top-level counter values.
  - ⚠️ **RESULT SHAPE (additive superset, not byte-identical).**
    `maintain()["consolidation"]` preserves `consolidated` / `into` /
    `recovered` verbatim as roll-up totals — the shipped telemetry mapping
    reads exactly those and is untouched — and adds `pools`, `pools_ok`,
    `pools_failed`. Hosts that compare the dict for equality (rather than
    reading keys) will see the new keys.
  - ⚠️ **AUDIT CARDINALITY (amended contract).** `maintain()` now appends one
    additional `consolidate-pool` line per ATTEMPTED pool before its
    aggregate `maintain` line. `error_code` is a CLOSED CONTENT-FREE enum —
    `llm-error`, `store-error`, `claim-contention`, `validation-error`,
    `timeout` — never `str(exc)`, because a model's exception routinely
    quotes the prompt back and the prompt carries memory text.
  - **A pool's failure no longer propagates.** `consolidate()` catches and
    reports; callers that relied on an exception escaping `maintain()` should
    read `pools_failed` / `pools[...]["error"]` instead.
  - **W3 mechanical totality:** a `COMBINING_SITES` registry
    (`veracium.combining`) plus the generated manifest
    `specs/generated/0021-combining-sites.md`, enumerated by parsing the
    store's SQL. A new record-writing path that is not dispositioned fails
    `test_scope_operation_matrix_is_total`.
  - **UNRESOLVED derivatives** (legacy, imported, recovered) join no pool and
    stay invisible to principal-bearing reads. The operator remedy is
    re-derivation; see `docs/api.md`.

- **0020 scoped recall, slice B — THE READ SURFACES: the principal
  boundary is live** (spec `specs/0020-scoped-recall.md` §4b–§4f;
  implemented, unreleased). `recall()` and `answer()` gain
  `principal: Optional[veracium.scope.Identity] = None` plus the closed
  §4e filter parameters, and `MemoryConfig` gains the host-supplied scope
  policy (`scope_groups`, `cross_scope_visible`), VALIDATED AT LOAD — a
  malformed policy raises when the config (and then the `Memory`) is
  built, never mid-recall.

  - **`principal=None` is byte-identical to today** over a fixed store
    state — the migration invariant, and the unscoped path runs no scope
    code at all (V1, checked on the FULL `Recall` value and by a
    detonator substituted for the view).
  - **The boundary is enforced on the STRUCTURED CARRIERS**, not on
    rendered bytes: `Recall.edges`, `.episodes`, `.contested` and each
    `ContestedGroup.exposed` carry only records the visibility relation
    admits. Membership evidence comes from the 0014 ledger; absorption
    survivors resolve over the TRANSITIVELY CLOSED row set, and missing
    or partial evidence is UNRESOLVED — invisible to every scoped
    principal, visible unscoped, never silently "shared" (V13).
  - **Restrict-only (§4b):** same-scope status never raises trust, never
    clears `ungrounded`/`needs_confirmation`, never lifts disclosure.
    Cross-scope material that policy admits is visible but pinned to the
    third-party-testimony shape — fenced, never assertable, never
    volunteered proactively. `gate.scoped_assertable` is the predicate
    and carries the NAMED, INERT seam 0011's subject dimension will use.
  - **The compiled wiki is EXCLUDED from principal-bearing responses**
    (§4d): a store-wide LLM re-rendering is a synthesis path the scope
    machinery does not control. Not filtered — not compiled.
  - **`answer()` threads the principal** into its internal recall (an
    answer path that dropped it would be a public bypass), and the
    queryless proactive briefing applies the same relation to the edge
    and episode sets BEFORE assembly.
  - **Operator surfaces stay UNSCOPED by decision, not by omission**:
    `introspect`, `export_memory`, `forget` (and `edges_since`) take no
    principal — right-to-know, portability and erasure must be total.
    Per-principal introspection is a recorded widening.
  - **The §4f inventory is now GENERATED**:
    `specs/generated/0020-read-surfaces.md` is produced by
    `specs/read_surfaces.py` from the AST of the public surface, with
    verdicts in `specs/read_surface_dispositions.py`; a new public read
    path that returns records and carries no disposition fails the gate
    (V12).
  - **Honest limits, unchanged:** `(origin, source_id)` is namespacing,
    NOT authentication (0006 R7) — this is honest-host ISOLATION
    (context bleed, confused deputy, cross-agent leakage), never a
    boundary against a caller who forges an identity. The default MCP
    stream supplies no identities, so no isolation exists on it.

- **0020 scoped recall, slice A — the normative scope core lands in
  production** (spec `specs/0020-scoped-recall.md` §4a-ii/§4a-iii/§4e;
  implemented, no behaviour change yet): a new module `veracium.scope`
  provides `Identity`/`resolve`/`same_identity`, the
  REGISTRY-AUTHORITATIVE `ScopePolicy` + `validate_policy`, the
  transitive absorption closure `close_absorption_rows` (None means
  UNRESOLVED) and the retention contract's `prune_absorbed_record`
  model, the total `membership` resolver, the visibility decision
  (`classify`/`decide`/`DECISION_TABLE`), and the closed §4e filter
  grammar. Digests are the SHIPPED 0006 primitive reached through
  `veracium.scope_linkage` — one implementation, never a copy. **No
  read surface consumes this yet**: `recall`/`answer`/proactive/the gate
  and `MemoryConfig` are unchanged, so shipped behaviour is byte-identical
  (slice B threads the principal). 0020 V10 is bound mechanically —
  the 128 pinned vectors in `specs/evidence/0020/vectors.json` now
  execute against the SHIPPED surface as well as against the normative
  reference. Scope errors are ONE class, `veracium.scope_linkage.ScopeError`
  (re-exported as `veracium.scope.PolicyError`), a `ValueError` subclass
  that the linkage errors now derive from — existing `except ValueError`
  callers are unaffected.

## 0.11.0 — 2026-08-16

- **THE API-BREAKING RELEASE (stage D2)** — the one break every deferred
  removal and schema change was staged for. Four coordinated changes, all
  under accepted specs (0016 D2; 0018; and the 0020/0021 acceptance
  riders to 0009/0014/0016/0018/0019):

  - **`source_type` is removed** (spec 0016, stage D2 — the deletion D1
    warned about since 0.9.0). The `Provenance.source_type` field, the
    public `SourceType` enum, and the entire deprecation surface are
    gone; the star-import inventory is 41 names. The field never
    influenced any decision; `evidence_basis` remains the frozen
    standing contract (spec 0016 §1b), deliberately NOT shipped as a
    field. Request/outcome digests no longer include the field.
    **Supersession receipts stamp `outcome_digest_version 4`**; the
    validated set becomes {1,2,3,4}, and — the era boundary — a
    persisted receipt with version < 4 now refuses UNCONDITIONALLY on
    sight at both phases (`ReceiptSchemaBoundaryError`, a named
    integrity refusal; no digest is computed, no comparison runs).
    Re-run the superseding write to mint a v4 receipt.
  - **Export FORMAT 6→7**: files no longer carry `source_type` (older
    importers refuse a 7-file; importing a ≤6 file drops the key), and
    exported absorbed records now carry **`absorbed_by_id`** — the
    structured absorption linkage, derived from the store's typed
    contribution ledger (never from free-text notes). Imports
    reconstruct absorption attribution PRE-COMMIT: structured-first,
    with a decidable legacy note rule for old files (ambiguous or
    unresolvable linkage refuses the WHOLE import before any write),
    and the reconstructed rows commit atomically with the records
    through the extended whole-import primitive
    (`commit_outcome_import_plan` gains `plan["contributions"]` +
    `contribution_state`; its return gains `contributions` /
    `contributions_existing`; idempotent re-imports skip rows, and a
    conflicting recorded history refuses).
  - **Store SCHEMA v7→v8 — WITH DDL** (the first since v6): the
    contribution ledger gains `contributor_type`/`contributor_ref`,
    populated on every new absorption row (legacy rows stay NULL). Both
    schema manifestations (constructor and ALTER-path) are generated,
    measured, and sha-pinned in the accepted evidence. **Older builds
    refuse a v8 store — back up before upgrading.** Migration to v8
    runs ONLY under the new release-migration orchestrator (below);
    ordinary open of a v7 store on this build refuses with guidance.
  - **The release-migration orchestrator** (accepted spec 0018):
    `veracium migrate --db X --i-have-quiesced --backup REF` — explicit
    operator attestation (flags, never prompts), a total read-only
    preflight (older bases get the exact two-release upgrade ladder;
    nothing is touched without an authority), a bounded mint/retry
    against concurrent access, structured results whose facts are never
    inferred from labels, a durable per-store migration audit trail,
    and loud audit failures (exit 3 — never a silent success). Library
    surface: `veracium.store.migration.run_release_migration`.
  - Also in this release: `veracium selfcheck` exits **2** when the
    provider environment prevents any check from running (previously 0
    with the DID-NOT-RUN banner) — CI consumers can now distinguish
    "environment problem" from "checks passed".

  **Upgrade path:** quiesce, back up, then `veracium migrate --db X
  --i-have-quiesced --backup <ref>`. Stores at v6 or below need the
  ladder: v7 on a 0.9–0.10 release first. Files exported by ≤0.10
  import fine (the dropped key is the only difference); files exported
  by this release refuse on ≤0.10 importers.

## 0.10.0 — 2026-08-15

- **The `ungrounded` flag — extraction-fidelity marking at ingest**
  (accepted spec 0019). Every extracted fact's specifics (digits,
  identifiers, proper nouns, ISO dates) are checked against the event text
  they came from; a fact carrying specifics the source never contained
  stores with `Edge.ungrounded=True` — never refused, never demoted, and
  fully recallable, but marked `[possible extraction error]` wherever it
  renders, never volunteered proactively, and excluded from the compiled
  wiki (the flag's only two behavioural reductions; both withhold, never
  grant). The flag is immutable for the record's life — `confirm()` cannot
  clear it (the remedy is restatement); absorption merges strengthen it by
  an N-ary OR and never launder it. Deterministic, zero LLM calls; dates
  ground through a pinned resolution-set rule ("next Friday" grounds its
  arithmetic resolution, proximity grounds nothing). **Export format 5→6**
  (older importers refuse rather than silently dropping the flag) and
  **store SCHEMA v6→v7** (no DDL — the ordinary `veracium migrate` /
  open-time migration applies; older builds refuse a v7 store, so back up
  before upgrading). Supersession receipts stamp `outcome_digest_version 3`
  (spec 0014 as amended). `introspect()` gains an `ungrounded` count. No
  telemetry change (deferred to a future consent version, recorded in the
  spec).

- *Correction to the 0.9.0 `SourceType`-deprecation entry (released text is
  immutable):* that entry said stage D2 ships "export format 6, store schema
  v7". Accepted spec 0019 takes format 6 and schema v7 first; **D2's numbers
  are now format 7 and schema v8** (spec 0016, as amended by 0019 — sign-off
  granted at 0019's round 4).

## 0.9.0 — 2026-08-14

- **`SourceType` is deprecated and will be removed in the next API-breaking
  release** (accepted spec 0016, stage D1 — warning-only, no behaviour
  change). It has never influenced any decision. On ingest-derived records it
  restates `author_of_evidence`; directly-constructed records may carry any
  value, which nothing reads. Accessing the enum through the package or
  `veracium.schema` (including `import *` and pickling) warns, and reading
  `provenance.source_type` on an edge warns once per access. NOT warned, by
  design: model metadata only (`model_fields`, `get_type_hints`) — those and
  only those. Hosts reading the field from exports should stop. Dependency
  note: the minimum supported pydantic rises to **2.7** (the
  `Field(deprecated=...)` floor), enforced by a dedicated CI job at the exact
  floor. Stage D2 (the removal, export format 6, store schema v7) executes
  only through the accepted 0018 release-migration orchestrator in the next
  API-breaking release.

- **Token-usage telemetry over the `Metered` wrapper** (accepted spec 0017 —
  15 external review rounds). Wrap your `Complete` in
  `veracium.llm.metered.Metered(fn, counter=your_tokenizer)` and Veracium now
  attributes per-operation token usage: the wrapper carries an affirmative
  capability (`veracium-metered-v1`) and a listener protocol; `Memory`
  registers a fail-closed listener that attributes each provider call's
  counts to exactly the operation (and user) that made it — exact under
  concurrency, shared wrappers, nested operations, and copied contexts.
  Where the numbers go: the local audit sink and `introspect(user)["llm_usage"]`
  (instance-lifetime, consent-independent, erased by `forget()`); the
  telemetry payload gains eight per-operation token fields ONLY under the new
  consent text (version 3 — existing installs keep sending exactly their old
  field set until telemetry is re-enabled against the updated text, per the
  0015 machinery). No counter → no token fields anywhere (character counts
  stay host-side and are never sent). A failed operation records nothing;
  `self_check` is excluded; MCP surfaces carry no usage. No schema change,
  no migration.

- **BEHAVIOUR CHANGE: default imports now cap trust** (accepted spec 0005 —
  "import has no trust boundary"). Every `import_memory()` / `veracium import`
  without `--restore` sets `author_of_evidence` and `derived_from` to
  `third_party` and floors `disclosure` to `use_only` on every imported record
  (`quarantined` is never weakened), so imported content is never assertable
  or rendered as the target user's own testimony. The return dict and the CLI
  line gain a `capped` count. `--restore` (new, mutually exclusive with
  `--user`; API `restore=True`, strict bool) preserves trust fields exactly —
  for restoring **your own** exports only; the refusal message on an own-store
  default re-import explains the distinction. **Upgrade note for hosts that
  script imports:** a same-store re-import of a pre-0005 export now refuses on
  the default path — pass `restore=True` for backup-restore flows; seeding a
  project from another principal's export keeps working and now lands capped
  (confirm a fact to assert it). One narrow amendment to the 0014
  source-identity projection rides along: on the default path the comparison
  runs over capped records, so identity claims differing only within a cap
  equivalence class skip (inserting nothing) instead of refusing; any content
  difference still refuses. No schema change, no format change, no migration.

## 0.8.0 — 2026-08-13

- **Opt-in telemetry can now report how often values are superseded and
  reinforced** (accepted spec 0015) — the counters the consent dialog's
  "aggregate counters" always intended. Counted at the planner from committed
  results only; consent-gated at record time; stripped from the MCP tool
  result (a per-write count is a supersession oracle). Installs that
  consented before this version keep sending exactly the old field set until
  telemetry is re-enabled against the updated consent text. A process that
  started with telemetry disabled begins collecting at its next process start
  after consent, not mid-run. Consent transitions are serialized under an
  OS-exclusive lock with a persisted transition epoch; deleting
  `telemetry.json` is the consent-erasure mechanism and is never undone by
  telemetry code.
  (`specs/0015`, accepted after 11 external review rounds + implemented.)
- **`veracium migrate` — an operator-facing CLI verb** wrapping the store's offline
  `migrate_store(path)`: migrates a below-head store to the current schema, reports the
  structured result (resulting version, whether anything changed), and refuses
  future-version stores with the store's own reason. Exit 0 migrated/current, 1 refusal,
  2 no file.
- **The `measures` relation** joins the default registry — a functional relation for
  changing quantities (weight, reading progress, balance, score): one current value,
  history kept. `docs/recipes.md` now shows how hosts extend `MemoryConfig.relations`.
- **`veracium.llm.metered.Metered`** — an opt-in wrapper for any `Complete` callable:
  per-role call counts, token counts when the host supplies a counter, honestly-labelled
  character counts when it does not. Totals stay host-side; `docs/telemetry.md`'s stale
  token-totals claim is corrected to what the code actually sends.

## 0.7.0 — 2026-08-11

> **Upgrade recommended for consumers ingesting third-party content**: this release
> ships `specs/0006` source identity and `specs/0014` maintenance attribution —
> trust-surface improvements that make third-party contributions durably attributable
> and revocation-joinable. One offline `migrate_store()` call advances a v3/v4/v5
> store to schema v6; an older build refuses a v6 store rather than misreading it.

- **Maintenance attribution — a consumed contributor now leaves a recoverable record**
  (`specs/0014`, accepted after 16 external review rounds + implemented). When maintenance
  consumes a contributor — absorption folding a duplicate into a more specific restatement, or
  consolidation compacting cold episodes into a summary — the store now writes a durable,
  content-free `contribution_ledger` row in the SAME transaction: who was consumed (as
  domain-separated digests of the resolved source identity and evidence reference — never raw
  refs), into which survivor, at which site, with a store-derived payload recording the exact
  values consulted (total at every site — a stale-but-corroborating input that moves nothing is
  still recorded, closing the invisible-contribution path). Reversal is RE-COMPUTATION over the
  recorded values; `revoke_source` gains its blast-radius join (`contributors_of_source`).
  - **The supersession receipt splits into request and outcome identity**: public
    `apply_supersession` now performs a pre-plan receipt lookup and a lost-response retry
    REPLAYS the persisted effects instead of raising (a live defect executed during review);
    the request digest is STORE-derived from a complete raw-request snapshot under a frozen
    byte-exact construction with pinned test vectors, verified against the plan by an
    exhaustive field partition with store-level per-field abort oracles; the
    concurrent-preflight loser replays, never conflicts.
  - **Consolidation outputs gain durable identity**: `Episode.consolidation_output_index`,
    store-assigned only (caller-supplied values refused); exported per the exclude-none rule.
  - ⚠️ **`SCHEMA_VERSION` v5→v6** — the ledger table + three indexes AND the repo's first
    ALTER of an existing table (`supersession_operations` gains `request_digest`, `response`,
    `outcome_digest_version NOT NULL DEFAULT 1`); `MANIFESTS[6]` accepts BOTH the constructor
    and the reviewed ALTER-path manifest per `0013` §4e (the ALTER-path DDL is an
    independently authored reviewed constant the migration must byte-match). Migrated
    receipts read version 1 (legacy semantics preserved honestly); new receipts stamp 2.
  - ⚠️ **`FORMAT_VERSION` 4→5** — exports carry the output index; older importers refuse a
    v5 file rather than dropping the field; v4 files stay accepted (a pre-v5 index field is
    stripped, never trusted, per `0006` I10). Import enforces indexed-output identity against
    destination state (tenant-scoped, origin-namespaced); a source-identical re-import
    resolves idempotently.
  - `specs/0003` §4f is amended in the same commit (the verbatim `0014` §7b text + eleven new
    I9 checks). The round-16 bin-(b) obligation (carrier-verifier byte-vs-text exactness) is
    dispositioned as the narrowed text-exact claim, recorded in the §12 acceptance ledger.

- **Fact-currency renewal — a restatement can no longer silently renew a fact's currency**
  (`specs/0012`, accepted after 14 external review rounds + implemented; the implementation
  itself independently reviewed and ACCEPTED after 8 further rounds). Reinforcement now
  transfers NOTHING: a re-stated fact is persisted as its own edge with its own provenance, and
  the prior is left byte-untouched — closing a measured bypass where same-class restatements
  (e.g. a system feed re-asserting a user fact) kept a stale fact perpetually fresh and silently
  raised its confidence, and closing finding M9 (the contributing source now leaves a recoverable
  record: the edge itself). Each edge ages against its own `observed_at`; only `confirm()` clears
  the possibly-stale flag.
  - **Read-path collapse**: every model-facing surface (query recall, the wiki compiler input,
    proactive assembly) suppresses only *strictly redundant* active duplicates — full
    authority-envelope grouping, deterministic survivors, one confirmable stale-warning owner at
    a time ("×N restatements need confirmation"), never a synthesized value, and the store keeps
    every edge.
  - **Hard token budgets** on all rendered surfaces: envelope-derived floors (a below-floor
    `token_budget` now raises `ValueError` instead of best-effort rendering), per-item clamps
    that shrink content but never sever safety labels, deterministic precedence under overflow
    (safety and warnings before breadth), a truncation report line with per-class counts, and
    budget-aware packing of contested groups.
  - **The wiki compile-drop marker**: every compiled wiki ends with an authoritative, forge-proof
    `[[veracium-wiki-compile:v1]] +N facts / +M episodes not compiled` line; `introspect()`
    exposes it as `wiki_compile_record` (status ok/absent/legacy/malformed), and the CLI prints
    a one-line summary.
  - ⚠️ **The wiki cache identity now binds the compiler policy** (version `0012-v1` + budgets +
    the marker grammar): an existing cache recompiles once on first use after upgrade. The
    store-only CLI (`veracium recall`) never recompiles — with a stale cache it serves recall
    without the wiki plus an explicit notice, instead of failing.
  - ⚠️ `MemoryConfig` gains seven budget fields (all validated); `0003`'s reinforcement plan
    action and `0008`'s C3 liveness-refresh are amended accordingly (marked in both specs).

- **Source identity — record *which source* a fact came from** (`specs/0006`, accepted +
  implemented). Provenance gains an optional `(origin, source_id)` pair: `source_id` is an opaque,
  host-supplied identifier for the source that produced an event (a mailbox, a connector instance, a
  device), passed via `Memory.remember(..., source_id="…")`; `origin` is a store-minted collision
  namespace so two stores' identical `source_id`s never merge on import. It is **diagnostic only —
  it groups records for dedup/inspection/attribution but grants no trust and changes no answer**, and
  it is host-supplied only, never model-derived. Under the hood: a canonical, shared
  `source_identity_digest` primitive (so future consumers re-derive one key), a durable per-store
  `store_identity` singleton, and resolve-at-read so a local record and its own export round-trip
  count as one source.
  - ⚠️ **On-disk store schema advances to v5** (one new `store_identity` singleton; no per-record
    change). A v1–v4 store migrates forward in one `migrate_store()` call; an older build refuses a
    v5 store rather than misreading it.
  - ⚠️ **Export/import `FORMAT_VERSION` advances to 4** — a v4 export is self-describing (each record
    carries its resolved origin); a v4 import rejects a record with no origin and ignores
    source-identity fields smuggled into an older-format file. Older builds refuse a v4 export.

## 0.6.0 — 2026-08-08

- **Supersession authority — third-party content can no longer retire your facts**
  (`specs/0003`, implemented). Until now the functional-supersession loop retired *any*
  differing value for a fact regardless of who reported it, so an incoming email extracted
  as `works_as: unemployed` could silently retire your own `works_as: CFO` and erase it from
  recall. Retirement is now governed by an **authority ladder** capped by provenance (who the
  evidence is from, and what it was derived from): `USER > SYSTEM > ASSISTANT > THIRD_PARTY`,
  with `effective = min(author, derived_from)` — so a `SYSTEM` summary of an attacker's email
  scores as third-party and retires nothing. A differing value supersedes the prior **only**
  when its effective authority is greater than or equal to the prior's; otherwise the
  retirement is **refused**: both values stay active and visible, and a durable, **content-free**
  refusal record (opaque edge ids, the relation, two authority levels — never your memory
  content) is kept so the guard's behaviour is observable and later policy can re-evaluate it.
  `Memory.supersessions_refused(user_id)` and `Memory` recall now expose this.

- **A refused update no longer disappears from recall.** Keeping both edges in the store is
  not enough if retrieval then drops the older one, so recall was hardened to match: within a
  contested functional group, recorded authority is ordered ahead of relevance and recency
  (a permutation — unrelated facts keep their place); the contested pair is kept **out of the
  one-value curated wiki** so it can't be collapsed there; and the higher-authority value is
  surfaced in a deterministic **CONTESTED FUNCTIONAL FACTS** block that gets first claim on the
  recall token budget. `Recall` gains a structured `contested` field; a lower-trust challenger
  that ordinary retrieval didn't surface appears only as content-free linkage, never as
  assertable content. The abstention gate still asserts only grounded memory.

- **On-disk store schema is now v4.** Two new content-free, per-user tables (the refusal
  inventory and a crash-safe operation receipt) are added additively. v1/v2/v3 stores migrate
  via one `migrate_store()` call, which also drops any wiki cache compiled under the old
  "one current value" semantics. ⚠️ **Consumers:** as with the v3 bump, a bare dependency-pin
  bump will not open an un-migrated older store — run the deployment-authority migration first;
  an older build opening a v4 store refuses rather than losing the refusal inventory.
  `apply_supersession` is applied as one atomic, compare-and-set-linearized plan, so concurrent
  updates to the same fact cannot branch it into two current values.

- **`correct()` is unchanged and remains out of scope** (tracked in `specs/0011`): it is a
  separate replacement path and is not governed by the authority ladder in this release.

## 0.5.0 — 2026-08-07

- **Outcome-authorship history is append-only** (`specs/0009`, implemented).
  `record_outcome` no longer overwrites a prior judgment: every use-and-judgment of a
  fact — keyed by `(edge_id, evidence_ref)` — becomes a new link in an append-only
  chain, so **who judged what, and when, is never destroyed** (the previous behaviour
  kept only the latest judgment, silently losing the earlier author). The edge's
  `times_used`/`outcome_counts` are now **derived from the chain heads**, not mutated
  in place. `Store` gains an atomic compare-and-set writer `append_outcome_if_head`
  (the only sanctioned way to extend a chain) and a whole-file
  `commit_outcome_import_plan`; the generic `add_episode`/`delete_episode` refuse
  outcome-chain rows. Portable import validates-or-refuses an incoming chain (never
  repairs), remaps cross-user references, and is idempotent on record equality; the
  offline migration converts each legacy outcome episode into an honest chain root,
  marked **`judgment_time_known = False`** (its stored date is the original use date,
  not a fabricated judgment time), and refuses rather than branching on a duplicate
  identity. `Episode` gains `seq` / `supersedes_episode` / `judgment_time_known`.

- **Crash-safe consolidation** (`specs/0010`, implemented). Memory consolidation is now
  a **fenced, leased, crash-recoverable** operation. Inputs are claimed atomically over
  the whole batch; the consolidated summary is written and made durable **before any
  input is deleted**; and a crash at *any* point is recovered on the next
  `consolidate()` — rolled forward (idempotent re-delete + finalize) or cleanly
  abandoned — so **no episode is ever lost without a replacement** (the previous path
  deleted every input before writing any summary, a total-loss window on a mid-operation
  crash). Every ordinary read sees **exactly one** complete representation — all inputs
  or all outputs, never both and never neither. A consolidated output carries its
  **whole** input set as lineage and the **minimum trust across that set** (a summary of
  third-party-influenced material stays third-party-influenced), and renders a date
  **range** rather than a single misleading date. `Store` gains the consolidation
  operation record and its fenced primitives; a claimed input is **reserved** (the
  generic mutators refuse it) until the operation finalizes. `export_memory` is now a
  **read-only quiescent snapshot** that refuses to export mid-consolidation (mutating
  nothing) rather than emitting a claimed input whose operation cannot travel with it.
  `Episode` gains `claimed_by` / `operation_id` / `lineage` / `date_start` / `date_end`.

- **The on-disk store schema advances to v3.** The new `Episode` fields (`0009` + `0010`)
  ride the existing episode JSON blob and `0010`'s operation record lands as a new
  `consolidation_ops` table — a purely additive change. A store below the head (an
  unstamped v1 store from any released veracium, **or** a v2 store) is brought forward in
  **one** offline `veracium.store.migration.migrate_store(path)` call (`specs/0013`); an
  older build opening a v3 store refuses loudly rather than silently misreading it.

- **`confirm()` is the only thing that clears the "possibly stale" flag**
  (`specs/0008`, implemented). Reinforcement — a re-statement of a fact already
  known — no longer clears `needs_confirmation`; it refreshes liveness only. The
  0.4.5 behaviour cleared the flag whenever a re-statement's author *class* matched
  (USER and SYSTEM share a disclosure class), so a system-authored restatement
  silently answered a "confirm before relying on this" question meant for the user.
  Now only an explicit `Memory.confirm()` clears it, atomically: the flag, liveness,
  confidence, the confirmation episode, and a **mandatory confirmation record** all
  commit together — if the record cannot be written the confirmation fails and the
  flag stays set. `confirm()` gains closed-enum `actor`/`call_path` (audit metadata,
  granting nothing) and an optional `correlation_id` for replay-safe retries; it
  returns `{confirmed, valid_from, confirmed_at, correlation_id, replayed}`.
  `Store` gains an atomic `confirm_edge` mutator and a `confirmations_for()` audit
  read; `add_edge` now refuses to clear the flag or change an edge's owner through
  the upsert path. A cross-user `import(..., user_id=…)` now mints fresh ids (a copy,
  never an ownership transfer). **The store schema advances to v2** (the
  `confirmations` table) via the offline `specs/0013` migration:
  `veracium.store.migration.migrate_store(path)` — a store below the head version
  refuses ordinary open (`migration-required`) and is brought forward by this
  explicit, deployment-authority-owned operation, per `0013` §5b.

- **On-disk store migrations** (`specs/0013`, accepted 2026-08-07 after 12 external
  review rounds post-M-Q4-ruling) — the abstract migration design and audit
  *protocol* for evolving a stamped store across schema versions, reviewed against
  the concrete v1→v2 `confirmations`-table migration. Accepted on the finite M-Q4
  acceptance boundary (spec §8a): the six gated properties are frozen and
  mechanically demonstrated (concrete migration correctness; planner/evidence
  architecture; closed public semantics; the abstract atomic audit protocol;
  the adapter-conformance surface; independent mechanical gates). The design is a
  prerequisite of `0006`/`0008`/`0009`/`0010`. **No production behaviour ships
  yet**: `Spec-Requires: 0007` (still `draft`) is gate-enforced, and the
  production audit sink — with its explicit blocking obligations (real two-table
  DDL, multiprocess consumption, invocation-provenance reconciliation, the
  `current`-with-repair `committed=True` contract, crash injection) — lands with
  `0008`. The in-process reference instrument (`specs/migrations_0013.py`) is a
  draft measuring model, not shipped code.
- **On-disk store schema versioning** (`specs/0007`, accepted after 14 external
  review rounds). A store now carries `PRAGMA user_version`; on open the store
  is recognised exactly or refused loudly, replacing the previous unconditional
  `CREATE TABLE IF NOT EXISTS` that opened any file and silently added missing
  tables to foreign ones. Concretely:
  - a **new** store is created and stamped in one `BEGIN IMMEDIATE` transaction;
  - every store written by any released veracium (all are unstamped) is
    **adopted losslessly** on first open — data unchanged, drifted acceleration
    indexes repaired, stamp written — with optional typed audit events
    (`audit_sink=`) and an `allow_adopt=False` opt-out;
  - anything else — newer stamps, foreign schemas, stamped-but-wrong shapes,
    negative versions — raises `StoreVersionError` with a closed `reason` and a
    diff naming the nearest accepted shape;
  - the running SQLite must match the packaged runtime evidence
    (`unsupported-sqlite` otherwise; 3.45.1 is the qualified build identity).
  `SqliteStore` gains keyword-only `allow_adopt`, `audit_sink`,
  `busy_timeout_ms`. The schema is now derived from a single registry shared
  with the spec tooling, and the evidence artifacts ship as package data.
  `open_versioned()` now returns which branch ran (`"current"` / `"created"` /
  `"adopted"` / `"migrated"`) and exposes two delegation seams for
  `specs/0013` as keyword-only hooks — `older=` (the §4 older row) and `new=`
  (creation, so a dedicated migration mode can refuse to create); with no
  hooks (the production default while `SCHEMA_VERSION == 1`) behaviour is
  unchanged. Package-consistency impossibilities now raise the named
  `PackageConsistencyError` (a `RuntimeError` subclass), and path/audit
  string caps measure filesystem bytes, so stores at non-UTF-8 POSIX
  filenames work.


## 0.4.8 — 2026-08-02

- **Consolidation wrote internally false provenance.** A summary reported
  `author_of_evidence=SYSTEM` while carrying `source_type=STATED` and the
  **first input's** `evidence_ref`, because both were inherited from `cold[0]`.
  A system-authored summary is not a stated fact and its evidence is not one
  arbitrary member. Now `INFERRED`, with an `evidence_ref` naming the
  consolidation.

  This is the 0.4.4 `cold[0]` defect surviving on two fields the 0.4.7 test
  never inspected.

- **An offset-bearing `date=` failed through `remember()`.** 0.4.7 taught
  `_event_dt` to convert offsets, then handed the **raw string** to the prompt
  builder, which parses with `date.fromisoformat` and rejects them — so
  `remember(date="2026-01-01T12:00:00+05:30")` raised `Invalid isoformat
  string`. Every public entry point now normalises once and passes the
  normalised value on.

- **The unparseable-extraction path recorded the wrong instant.** When
  extraction returned no parseable JSON, `observed_at` was re-derived from the
  already-reduced date, so `12:30+05:30` was stored as **midnight** rather than
  07:00 UTC. Both branches now reuse the accepted instant.

- **`veracium-mcp --version` no longer fails outside an installed package.** It
  reported `PackageNotFoundError` from a bare source tree; it now says so and
  continues. Deliberately without a `__version__` constant — `pyproject.toml`
  stays the single source of the version.

## 0.4.7 — 2026-08-02

- **An offset-bearing event date was relabelled UTC instead of converted.**
  `_event_dt` did `datetime.fromisoformat(x).replace(tzinfo=utc)`, which
  **discards** an existing offset rather than converting the instant. A
  timestamp written `...T20:00:00-12:00` was checked as if it were 20:00 UTC
  when the instant it names is 08:00 the following day — **measured at 12 hours
  of future-skew bypass, and up to 26 across the legal offset range.** It
  partially defeated the future-date rejection shipped in 0.4.6.

  Offset-bearing values are now converted with `astimezone(utc)`; a naive value
  still means UTC, which is the documented contract for a bare date.

- **Consolidation manufactured confidence, disclosure and currency.**
  `consolidate()` set `confidence = 0.9` unconditionally and inherited the first
  input's disclosure, so **a batch containing a 0.2 episode produced a summary at
  0.9**, and a batch containing one `use_only` episode could produce a
  `mentionable` summary. A summary is now **no stronger than its weakest input**
  across every trust-bearing field: `confidence = min`, `disclosure = weakest`,
  `observed_at = max(inputs)` and never *now*.

  This is the same rule that governs T2 deduplication — **recognition is not
  observation, and a summary of old material is not new evidence.**

  Found by external review of `specs/0002`, against an invariant that spec had
  itself added while the code violated it.

- **A malformed `date=` is now rejected instead of silently becoming *now*.**
  `_event_dt` fell back to the current time on any unparseable date. That is the
  same manufacture 0.4.6 removed for *future* dates, in a quieter form: **a
  malformed statement about when an event happened is not evidence that it
  happened now.** The fallback could refresh a stale fact, relieve lifecycle
  pressure through a later `observed_at`, and write an audit record attributing
  an invented time to a caller that believed it had supplied one.

  **Absence is now the only thing that means now** — omit `date=` and you get
  the current time, as before.

  Ingest validates through the same function before building its prompt, so a
  bad date fails with the reason rather than with `date_context`'s raw
  `Invalid isoformat string`. **One input had two parsers and two error
  contracts.**

  Found by external review of `specs/0002`; the reviewer noted §7f rejected
  future dates while retaining the malformed fallback, which violates the
  principle that section exists to enforce.

## 0.4.6 — 2026-08-01

- **Two defects found while verifying an external review of `specs/0002` — both
  live in released 0.4.5, both fixed.** Neither was reported by the review; both
  turned up in the process of checking its claims against running code.

  **`confirm()` returned a `valid_from` it never set.** 0.4.5's M2 fix stopped
  `confirm()` moving a fact's first-known date, because `render_edges` emits
  `(since <valid_from>)` into answer context and a January preference confirmed
  in March read *"(since March)"*. The fix corrected the model's context and
  **left the same false date in the return value a host UI reads** —
  `confirm()` returned `{"valid_from": <confirmation date>}` while the edge kept
  its real one. The return now carries both `valid_from` (the real, unchanged
  first-known date) and `confirmed_at`. **A fix that missed one of its own
  surfaces; the sibling it missed is the one an integrator sees.**

  **A future-dated event was accepted, and was unrecoverable.** `date=` had no
  upper bound, so `remember(date="2099-01-01")` set both `valid_from` and
  `observed_at` to 2099. `observed_at` is only ever advanced with `max(...)` —
  which is what correctly defeats *back*-dating, and is therefore exactly what
  made *forward*-dating permanent: no later confirmation could bring it down.
  **One host-supplied date removed a fact from lapse, decay and staleness
  flagging for 73 years, with no API to undo it.** Event dates more than a day
  in the future are now rejected at `_event_dt`, the single point every event
  date passes through, so `remember()`, `confirm()`, `correct()` and
  `record_outcome()` are all covered.

  **Behaviour change:** a future `date=` now raises `ValueError` instead of
  being stored. It has no legitimate meaning — the event date records when a
  statement was made, not what it is about, so *"the contract expires in 2027"*
  is a value and never an event date. Malformed dates keep their existing
  fallback to now.

- **retrieval: coverage-aware subgraph selection was measured and stays OFF.**
  0.4.2 shipped it disabled and said *"the default will change only if a
  balanced measurement supports it."* **That measurement has now run, under a
  pre-registered protocol, and it does not support it.**

  30 items drawn stratified on distinct `valid_from` days — the variable the
  code actually branches on — with the hypothesis, primary metric, thresholds,
  analysis plan and stop rule fixed in advance and approved before any run.
  Three replicates across four arms.

  **Coverage rose on 12/12 items (+5.25 distinct sessions at the tested
  setting). The primary metric — the fraction of answer-bearing turns actually
  retrieved — improved on 2 of 12, against a pre-declared threshold of 10.**
  The mechanism does exactly what it was built to do and does not buy the thing
  it was built for. Read cost was flat, so it is not expensive — it is
  ineffective on this measure. Exploratory arms at half and double the reserve
  moved coverage monotonically (+2.75 / +7.67 sessions) and the primary metric
  not at all, so this is not a mistuned parameter.

  **`subgraph_coverage_share` keeps its default of `0.0`, and the code stays**
  — off by default, tested, and re-runnable if the storage granularity that
  bounds this result ever changes.

  **What the result does not establish.** It is evidence about day-clustered
  coverage selection **under day-granular storage**, on one benchmark and one
  metric, n=12. Seven of the twelve items were already at a perfect hit rate in
  the baseline, so more than half the sample had no room to improve and the
  pre-declared threshold was, in hindsight, unreachable from the moment the
  sample was fixed. That does not rescue the hypothesis — coverage rose
  everywhere and the metric moved almost nowhere — but "ineffective in general"
  is **not** what was shown.

  One item regressed from a perfect hit rate to zero when coverage was enabled;
  that is being investigated separately as a defect rather than folded into this
  result.

## 0.4.5

Three provenance defects, found by an audit of the maintenance-time operations
(`specs/0002-maintenance-provenance-invariant.md`).

> **Correction (2026-08-01):** this entry originally said the audit covered
> **every** maintenance-time operation. It did not. Review found
> `portability.import_memory` absent from the enumeration — a surface that
> reconstructs *every* trust-bearing field from a file and writes it straight to
> the store, bypassing the ingest path's trust machinery entirely. The word is
> withdrawn until the enumeration is mechanical rather than recalled. See
> `specs/0002` §M6. The audit was
prompted by two advisories in four days — GHSA-r7j7-5jq9-3f5q and
GHSA-hcj3-8jqc-wqrp — which are the same shape: a maintenance operation crossing
a trust boundary the write path guards correctly. **None of the three below is a
trust-boundary bypass**, so no advisory accompanies this release.

- **`confirm()` no longer moves a fact's first-known date.** It used to set
  `valid_from` to the confirmation date — **the exact defect 0.4.3 shipped C′ to
  eliminate**, in a sibling path the fix never touched. Because `render_edges`
  emits `(since <valid_from>)` into answer context, a preference stated in
  January and confirmed in March was rendered to the model as *"(since
  2026-03-01)"* — a false statement in front of the model, not merely lost
  history. **0.4.3's changelog asserted "valid_from is set at creation and never
  mutated"; that was not true of `confirm()`, and now is.** A confirmation is
  new evidence about *liveness*, so it advances `provenance.observed_at`.
  **Not repairable:** dates already moved by a prior `confirm()` are
  unrecoverable — the original is not recorded anywhere.
  *A test asserted the old behaviour, which is why C′ did not catch it.*

- **A staleness flag can no longer be cleared by a different author.**
  `needs_confirmation` renders as *"confirm before relying on it"* — a question
  addressed to the party who stated the fact. Reinforcement cleared it
  unconditionally, and the 0.4.1 same-class guard compares **disclosure** class,
  where `USER` and `SYSTEM` both sit in `MENTIONABLE`. So a system-authored
  restatement answered a question meant for the user. Now only same-author
  evidence clears it; `confirm()` remains the explicit path, and third-party
  content was already correctly blocked.

- **Outcome authorship is no longer overwritten.** `record_outcome()`'s
  upgrade-in-place path replaced the episode's `author_of_evidence` with the new
  actor's, discarding who made the earlier judgment — in a system whose stated
  principle is supersession-never-erasure. The prior author is now retained in
  the episode summary. Outcome episodes are excluded from recall, so nothing
  reached the model either way.

**Also added:** `tests/test_maintenance_invariant.py`, which states the class
rather than the instances. The load-bearing one is **N7** — *a full `maintain()`
cycle never moves an edge from the UNVERIFIED block to the GROUNDED one* —
expressed over the observable boundary rather than any field, so it catches the
next instance even when the mechanism is one nobody anticipated. **Both
advisories would have failed N7.**

## 0.4.4 — security

- **SECURITY: episode consolidation laundered third-party content into the
  grounded block.** `maintain()`'s consolidation step built the consolidated
  episode's provenance from a **single member** of the cold batch
  (`cold[0].provenance`), so a mixed batch whose first episode happened to be
  user- or system-authored collapsed to `author_of_evidence=USER` with
  `derived_from=None`. `Provenance.third_party_influenced` then reported
  `False`, and `gate.partition_parts` — which routes episodes on exactly that
  property — moved the summarised third-party text out of the UNVERIFIED block
  and into the **GROUNDED** one, where it may be asserted.

  This is the attack `gate.partition_parts` names in its own docstring (*"a
  system-authored summary quoting a received email launders attacker text into
  its episode — route by influence, never by authorship alone"*): consolidation
  was defeating the defence its own module documents. It required no
  hallucination and no prompt injection — a faithful summariser compacting a
  mixed batch was sufficient. Same class as GHSA-r7j7-5jq9-3f5q (0.4.1): a
  **maintenance-time** operation crossing a trust boundary that the write path
  guards correctly.

  **Fixed:** consolidated provenance is now computed across the **whole set** —
  `author_of_evidence=SYSTEM` (which is what the code's own comment always
  claimed it was) and `derived_from=THIRD_PARTY` if **any** member was
  third-party-influenced. The result stays in the UNVERIFIED block, matching
  pre-consolidation behaviour.

  **Affected:** every version with consolidation, through 0.4.3. **Exposure
  requires** `maintain()` to run consolidation over **≥8 cold episodes**
  (default `consolidate_min_batch`) older than **30 days** (default
  `consolidate_after_days`) with **mixed authorship** and a trusted episode
  first in store order. Deployments that never call `maintain()`, or whose
  episodes are single-author, are unaffected. **Upgrade if you ingest
  third-party content (received mail, documents, tool output) and run
  maintenance.** No store migration is required; existing consolidated
  episodes are **not** retroactively re-labelled — see the advisory for how to
  identify them.

  Found while writing the first specification under `specs/PROCESS.md`: the
  template's rule to enumerate a changed field's consumers *mechanically rather
  than from memory* surfaced `lifecycle.py` as a writer of
  `author_of_evidence`, which the memory-written list had missed.

## 0.4.3

- **telemetry: the abstention heuristic under-counted abstentions.** It existed
  twice — a narrow copy behind `answer`'s content-free `abstained` counter and a
  broader one in `selfcheck` — and the narrow copy missed the most common
  refusal phrasing the gate actually emits (*"I don't have any confirmed
  information about X"*). Abstention is the metric that most directly tracks the
  product's core guarantee, so under-reporting it was the worst place for a
  duplicated regex to drift. Now defined once as `gate.ABSTAINED` and imported
  by both; regression test uses verbatim openings from real judged answers.
  Found while hand-classifying benchmark misses, not by any test.

- **BREAKING (semantics): `valid_from` is now first-known and immutable.**
  Reinforcement used to overwrite it with the latest restatement date, so a
  fact stated in January and restated in March reported `valid_from` = March
  and the January date was unrecoverable. Because `render_edges` emits
  `(since <valid_from>)` into recall context, that was **a false statement in
  the answer context**, not merely lost history — and it violated the field's
  own documented contract (`edges_since` already distinguishes "when it became
  true" from "when veracium recorded it"). Now: `valid_from` is set at creation
  and never mutated; `provenance.observed_at` carries the latest recording (it
  already did); **`maintain()` ages liveness against `observed_at`** instead, so
  a restatement still keeps a fact alive — it refreshes the field that means
  liveness. T1 absorption's winner inherits the **earliest** `valid_from`
  (`min`, was `max`) and the latest `observed_at`; recall's recency tiebreak
  and proactive recall's "unrefreshed since" read `observed_at`.
  **`introspect()` renames `first_observed`/`last_observed` →
  `first_known`/`last_recorded`** — the old `first_observed` was computed from
  the `max()`ed field and so reported *last* observed under a "first" name.
  **Forward-fixing only:** already-collapsed `valid_from` values in existing
  stores cannot be recovered. Invariant now asserted on every write path:
  `valid_from <= observed_at`.
  Found by a LongMemEval experiment; the write-path defect, not the benchmark,
  is the reason it ships.

- **retrieval: time coverage in subgraph selection — implemented but OFF by
  default (`subgraph_coverage_share = 0.0`).** When enabled, most of the budget
  is still filled by relevance alone and a reserved tail goes to periods not
  already represented. **It ships disabled because it is unvalidated**: the
  measurement that motivated it was retracted — the benchmark sample it was
  diagnosed from proved unrepresentative on exactly the dimension involved, so
  the mechanism has never been tested on data that could exercise it. The code
  and tests are here so the experiment can run; the default will change only if
  a balanced measurement supports it. Pure top-k has no coverage
  term, so a cluster of facts sharing the question's vocabulary takes the
  whole budget and a question spanning months gets answered from a single
  day — measured on LongMemEval, where an interval question recalled 37 date
  mentions of which **one** was distinct, making the interval uncomputable
  and the abstention correct. Clusters on `valid_from`, the only temporal key
  always available (session identity is a host concept most callers never
  supply). Conservative by construction: the head is pure relevance so the
  strongest matches are never displaced, coverage only spends the reserved
  tail on candidates that already passed relevance, the tail backfills by
  relevance when there is no other period to reach, and stores below the
  budget are bit-identical to before. Set `subgraph_coverage_share=0.0` to
  restore pure relevance ranking.

  > **Outcome (2026-08-01):** the balanced measurement promised above has run.
  > **It does not support enabling this, and the default stays `0.0`** — see the
  > Unreleased entry at the top of this file. Recorded here rather than by
  > editing the text above, so the original commitment and its answer both stay
  > readable.

## 0.4.2

- **retrieval (graph): recall was query-blind on large stores.** Every
  user-subject edge carried a *constant* score, so once a store outgrew
  `max_subgraph_edges` the truncation kept whichever edges the store listed
  first and the query stopped mattering for the subject that owns most facts.
  Small stores were unaffected (everything fits), which is why fixtures never
  showed it; on a ~1,700-fact store recall returned effectively the same facts
  whatever you asked, and raising the cap only returned more of the same
  (measured: 40 → 200 edges gave **no accuracy gain at 3.8× the read cost**).
  Now: user-subject edges stay always-eligible — the "everything off the user
  node" contract is unchanged — but relevance decides which survive
  truncation, with recency as a deterministic tiebreak. Also: `relation` is
  matchable text (so "pet" reaches `has_pet`), the non-discriminating owner
  token `user` is excluded from matching, and query wording is folded to a
  fixed point over ordinary plurals ("deadlines" reaches `deadline`).
  Found by the LongMemEval pilot, whose failure taxonomy put **0 misses in
  extraction** and the rest in ranking and synthesis.

## 0.4.1

- **security (graph)**: identity merges (reinforcement + T1 absorption) are
  now confined to edges of the **same disclosure class** — previously both
  were trust-blind, so a third-party `use_only` restatement of a user fact
  could (a) retire the user's assertable edge (reason `absorbed_duplicate`),
  leaving no assertable version of a true, user-evidenced fact — a
  third-party event could silently demote user facts out of assertable
  recall (subset form new in 0.4.0's T1); and (b) refresh a USER edge's
  liveness, clear its `needs_confirmation` flag, and raise its confidence
  (exact-match form present since 0.3.0 and earlier; widened by T1).
  Cross-class restatements now accumulate as separate edges, each carrying
  its own trust — the explicit upgrade path for corroborated third-party
  material remains `confirm()`/a user restatement. Dedup never makes trust
  decisions. Found by the research session's post-merge T1 review
  (`proposals/t1-review.md`); locked by cross-trust regression tests and a
  new hard **trust-canary gate in the bench engine tier**
  (`engine.trust_canary_failures == 0`).

## 0.4.0

- **proactive recall**: `recall(user_id)` with no query returns a session-start
  briefing — dated commitments due/overdue, possibly-stale facts to confirm,
  current transient state, recent history. Volunteering is disclosure-gated:
  only `MENTIONABLE` facts surface; `use_only` and quarantined material never
  appear unprompted (the Disclosure tier doing the job it names). LLM-free,
  deterministic, budget-aware (commitments outrank history when trimming);
  MCP `recall` exposes it by omitting `query`. New config:
  `proactive_deadline_window_days` / `proactive_recent_days`.

- **introspect** (the "inspectable memory" half of a recurring demand signal;
  `dispute`/`confirm`/`correct` are the editable half): `introspect(user_id,
  mode="summary"|"categories")` — the formatted transparency view over what
  was always exposed raw. Counts by relation / evidence author / disclosure
  tier, lifecycle state, retired history by reason, episode counts;
  `categories` adds the facts grouped by relation with the same provenance
  markers recall renders. LLM-free, store-only; content-free `introspect`
  telemetry event.

- **CLI memory verbs**: `veracium recall` (no query → the proactive briefing;
  with a query → subgraph + *cached* wiki — store-only either way, never
  compiles, needs no provider), `veracium remember` (ingest one event;
  `-` reads stdin; `--author`/`--derived-from` route trust exactly like the
  API), `veracium introspect` (`--categories`, `--json`). Memory becomes
  scriptable without touching Python.

- **Claude Code hooks recipe** (`examples/claude_code_hooks/`): ambient
  memory via lifecycle hooks instead of (or alongside) MCP — a `SessionStart`
  hook injects the proactive briefing at zero schema-token cost (and again
  after context compaction), a `UserPromptSubmit` hook writes the user's
  words back through a detached `veracium remember` so extraction never
  blocks a turn. Provenance discipline documented: captured content the user
  did not author must be routed `third_party`/`derived_from`.
- **value-equivalence T1 — subset absorption** (`graph.apply_supersession`,
  per `proposals/value-equivalence.md`): a *more specific* restatement of a
  held value ("cat Miso" after "Miso") now absorbs the shorter form instead
  of accumulating a duplicate — the prior retires non-destructively (reason
  `absorbed_duplicate`, note carries `absorbed_by:<winner-id>`), the winner
  takes `max(valid_from)`/`max(confidence)` and keeps its own provenance,
  and no `supersedes` pointer is set (absorption is identity, not change —
  `render_edges` never shows an absorbed value as history, and on functional
  relations a subset-shaped restatement no longer churns a false
  supersession). A *less specific* restatement ("Miso" after "cat Miso")
  reinforces the fuller edge: validity refreshed, `needs_confirmation`
  cleared — allowed because write-time evidence just arrived. Guardrails:
  ordered-subsequence match only (the 'tea over coffee' ≠ 'coffee over tea'
  contract survives), at most 2 extra tokens, same (subject, relation) only;
  `his X`/`her X` still never merge. Exact-match reinforcement now takes
  `max(valid_from)` too, so a back-dated restatement can no longer rewind a
  fact's freshness. The S4 robustness checker and bench record classify
  absorptions in their own bucket (`absorbed`), never as `duplicated`.

## 0.3.0

- **bench**: internal benchmark suite (`bench/run_bench.py`) — engine-overhead
  medians against a zero-latency scripted model, the acceptance eval, and the
  robustness tier at `--s4-samples 50` with duplicate-shape classification
  (the value-equivalence T0 measurement), recorded per-release to
  `bench/results.jsonl` with a `--compare` regression gate. Now part of the
  maintainer release checklist. See `bench/README.md`.

- **mcp 2.0 compat**: the MCP SDK 2.0.0 renamed `FastMCP` to `MCPServer`
  (same decorator API) — `veracium-mcp` now imports whichever the installed
  SDK provides, so `mcp>=1.0` stays the supported range on both majors.

- **outcome tracking (V4)**: co-designed with the first production consumer —
  `record_outcome()` records uses and judgments of facts as `kind="outcome"`
  episodes (the source of truth) with derived edge counters
  (`times_used`/`outcome_counts`/`last_outcome`); judgments upgrade the
  matching use in place via (`edge_id`, `evidence_ref`). Vocabulary:
  `unreviewed`/`confirmed`/`corrected` (human) /`challenged`/`concurred`
  (LLM judge), actor rules enforced. Edge-blind by design: `record_outcome`
  never supersedes facts; the explicit fact-level `correct()` verb supersedes
  with reason `"corrected"`. `challenged` reuses the possibly-stale flag;
  counters render into recall as information, never gating; outcome episodes
  are excluded from the narrative recall window and from LLM consolidation.
  Portability format v2 (`"record"` marker; v1 imports unchanged). Neither
  verb is an MCP tool.

## 0.2.4

- **selfcheck UX**: `veracium selfcheck` now preflights the provider — a
  missing SDK or missing `ANTHROPIC_API_KEY` exits with one clear install
  hint instead of a traceback or, worse, a garbage `FAIL … injection
  asserts=1` scorecard (an erroring check was conservatively scored as an
  assert, which read exactly like the injection guarantee failing). If the
  provider fails every check mid-run (e.g. bad credentials), the result is
  now reported as **DID NOT RUN** (exit code 2) — an environment problem is
  never rendered as a memory-safety result.

## 0.2.3

- **MCP Registry**: README carries the `mcp-name` validation marker and
  `server.json` (current registry schema) sits at the repo root — Veracium is
  publishable to registry.modelcontextprotocol.io, which the MCP directories
  crawl. `docs/mcp.md` refreshed: PyPI install flow (the page still described
  a pre-PyPI clone install), the `remember` tool row now documents
  `derived_from`, `recall` documents `token_budget`, and the deliberately
  non-MCP verbs are listed with their rationale.

## 0.2.2

- **veracium-mcp CLI**: `--help` and `--version` now work (previously any
  argument was ignored and the stdio server booted silently — confusing on a
  first install); unknown arguments fail with a pointer to `--help`; a boot
  failure (e.g. missing `ANTHROPIC_API_KEY`) exits with a clear one-line
  message instead of a traceback.

## 0.2.1

- **host queries** (requested by the first production consumer for its
  intelligence layer): `Memory.list_entities()` — distinct ids with
  edge/episode counts, for proactive-recall planning and coverage audits — and
  `Memory.edges_since(user_id, since)` — edges learned after a date, filtered
  on `provenance.observed_at`, including superseded/quarantined material so
  change-detection sees everything. Host/admin surface; neither is an MCP tool
  (cross-user enumeration is not an agent capability). `Store` gains
  `list_users()` (non-abstract, like `forget_user`).

## 0.2.0

The launch release: the five capability gaps identified by an independent
landscape analysis, plus the display-brand and one-liner refresh.

- **branding**: display brand is capitalized **Veracium** in all prose (code
  identifiers stay lowercase); canonical one-liner applied to the PyPI summary,
  README lead, and MCP server description.
- **audit**: opt-in operation audit log — `Memory(audit=AuditLog(path))`
  appends one content-free JSONL line per operation (UTC timestamp, op,
  `user_id`, the op's counters; never memory text) covering
  remember/recall/answer/maintain/dispute/confirm/forget/export/import.
  Append-only, host-owned; sink failures never break memory.
- **feedback verbs**: `dispute(user_id, edge_id, reason=, actor=)` — the edge
  leaves every assertable surface immediately (non-destructive invalidation,
  reason `"disputed"`), and the dispute itself is remembered as an episode with
  actor and reason; `confirm(user_id, edge_id)` — refreshes validity, clears
  the possibly-stale flag, records the confirmation. `confirm` refuses
  non-assertable edges (elevating a claim by confirmation would be a laundering
  vector — affirmation is new evidence, use `remember()`). Neither is an MCP
  tool by design. Content-free `feedback` telemetry event.
- **forget** (compliance erasure): `Memory.forget(user_id)` irreversibly erases
  everything stored for a user — edges incl. superseded history and quarantined
  claims, episodes, wiki cache, counters. Distinct from lifecycle by design
  (`maintain()` never deletes; `forget()` never preserves). CLI:
  `veracium forget --user X` (confirmation prompt; `--yes` to skip).
  Deliberately not exposed over MCP — an agent-callable wipe verb is a standing
  prompt-injection target. `Store` gains `forget_user()` (non-abstract;
  custom stores keep working until they implement it).
- **portability**: JSONL export/import — `Memory.export_memory(user_id, path)`
  writes the complete store of record (all edges incl. superseded history and
  quarantined claims, all episodes, full provenance/disclosure);
  `import_memory(path, user_id=...)` is idempotent (existing ids skipped, never
  overwritten) and can remap users. CLI: `veracium export` / `veracium import`
  (store-only, no LLM needed). The wiki cache is not exported — it recompiles.
- **recall**: token-budget-aware context assembly — `recall(user_id, query,
  token_budget=N)` caps the rendered context (chars/4 heuristic; Veracium is
  tokenizer-agnostic). Trimming follows a documented priority: query-matched
  facts, then unverified-claim flags (never silently dropped below the facts
  they annotate), then the curated wiki (all-or-nothing), then recent episodes
  newest-first; best-effort minimum of one item. `Recall` gains
  `tokens_estimated`/`truncated`; the MCP `recall` tool exposes the parameter;
  the content-free telemetry `recall` event gains a `trimmed` counter.

## 0.1.7

- **security (ingest/gate/compile)**: closed the **system-event laundering**
  bypass — third-party text embedded inside a `SYSTEM`/`USER`-authored event (a
  triage verdict quoting a received email's subject, a summary of a message
  body) previously acquired the event's full trust and could surface as
  assertable user facts. `remember()` gains `derived_from`: declare
  `author=SYSTEM, derived_from=THIRD_PARTY` and trust is capped at the minimum
  of the two — edges cap at `use_only` (claims still quarantine), and the
  episode routes to the unverified channel at the gate *and* is excluded from
  the compiled wiki (episodes now route by third-party *influence*, not
  authorship alone). `Provenance` records both fields; MCP `remember` exposes
  the parameter; documented in `docs/concepts.md` ("Mixed provenance") and
  `SECURITY.md`. Found by the first production consumer on a real-mailbox
  backfill (130 laundered assertable edges); reported in
  `proposals/system-event-laundering.md` with the attack fixture now locked as
  a regression test.

- **ingest**: an `unparseable` extraction no longer leaves a history gap — the
  turn records a content-free placeholder episode ("(unprocessed <type> event —
  extraction returned no parseable JSON; content not retained)") with full
  provenance/`evidence_ref`. Deliberately not the raw event text: that would
  feed unmediated, possibly adversarial input straight into recall prompts.
- **_json**: among list fallbacks, `extract_json` now prefers a non-empty
  list of dicts (the shape of a bare triples array) over junk like `[]` or
  `[1, 2]` that happened to parse earlier in the prose.
- **graph**: `his`/`her` removed from the value-equivalence filler list — they
  can point at a third party ("his assistant" vs "her assistant") and so carry
  meaning; user-referential possessives (`my`/`our`/`their`) remain filler.
- **examples**: `openai_provider.py` — `OpenAIComplete` wraps any
  OpenAI-compatible chat-completions API (OpenAI, vLLM, Ollama's `/v1`), with
  per-role model mapping, honest structured-output fallback, and a memoized
  capability check. First outside contribution — thanks @vreddy-commits (#8).

## 0.1.6

- **security (compile)**: a third-party *inference* (`use_only`) is no longer fed
  into the compiled wiki. `recall()` places the wiki in the gate's assertable
  GROUNDED block, so a `use_only` fact reaching the wiki could be asserted through
  the wiki path — even though `gate.partition` (0.1.3) already routed such inferences
  to UNVERIFIED. `compile._grounded_inputs` now excludes `use_only` edges, mirroring
  the gate; the inference still shapes behavior via recall's unverified channel, only
  kept out of the assertable body. Completes the 0.1.3 fix (which covered only the
  subgraph path). Adds a unit lock (`test_grounded_inputs_excludes_use_only`).

## 0.1.5

- **ingest/_json**: a distill response whose first parseable JSON value is a
  *list* no longer crashes `remember()` (`'list' object has no attribute
  'get'`). `extract_json` now prefers the first JSON *object* — skipping prose
  debris like a stray `[]` before the real payload — and returns a bare array
  only as a fallback, which ingest normalizes as the triples payload with its
  wrapper omitted. Found by the robustness tier's first lmsys-chat-1m run
  (3/368 real turns crashed, all code-shaped inputs).
- **tests**: robustness tier Phase 2 — S4 (reinforcement ≠ duplication: a seeded
  sample of fact-yielding turns is re-ingested; new-edge growth is reported as a
  distribution) and S5 (every `maintain()` report must carry non-negative counts
  bounded by the store it ran over). Both soft signals; hard gates unchanged.

## 0.1.4

- **ingest**: an unparseable distill response (the extractor answering in prose —
  typically a refusal on jailbreak-shaped or degenerate input) no longer raises
  out of `remember()`; it records nothing and returns
  `{"episode": "", "facts": 0, "quarantined": 0, "unparseable": True}`, with a
  content-free `unparseable` counter in the telemetry `ingest` event. Found by
  the new robustness tier on its first run (7/19 fixture turns crashed).
- **tests**: new opt-in robustness tier (`tests/robustness/`,
  `VERACIUM_ROBUSTNESS=1`) — streams real, messy conversations through the write
  path and holds veracium's guarantees as hard invariants (no internal crashes,
  no cross-user leakage, no assertable third-party user-facts, well-formed
  persistence), plus soft distributions (yield, relation drift, latency,
  provider crash-rate). Ships a committed adversarial fixture corpus
  (`fixtures/messy.jsonl`); points at a locally exported lmsys-chat-1m for the
  full run. Reports are redacted — raw corpus text never appears.

## 0.1.3

- **gate/graph** (security): third-party *inferences* — real-looking user facts
  whose only support is third-party evidence (marked `use_only` at ingest) — were
  treated as grounded by the abstention gate and rendered as bare facts, so
  `answer()` would assert e.g. an employer learned solely from a received email.
  The `use_only` disclosure is now enforced everywhere it's read: the gate
  partitions these under UNVERIFIED (never asserted), and `render_edges` tags
  them `[third-party-reported; unconfirmed]` in recall context and the compiled
  wiki. New `Edge.assertable` / `Edge.use_only` properties expose the discipline.

## 0.1.2

- **graph**: reinforcement now matches paraphrased values ("dog named Ollie" /
  "dog Ollie" / "dog: Ollie") via order-preserving normalized-token comparison,
  instead of exact string equality — a re-stated fact whose extraction phrasing
  drifted between runs used to accumulate as a near-duplicate edge. Order still
  matters ("tea over coffee" ≠ "coffee over tea"), so functional supersession of
  genuinely new values is unaffected.

## 0.1.1

Reliability fixes surfaced by building the runnable demo notebook
(`examples/demo.ipynb`, new in this release):

- **selfcheck**: the abstention detector now recognizes natural abstention
  phrasings ("I don't have any confirmed record of ..."); previously a correct
  abstention could flakily score the check FAIL.
- **distill**: the extraction prompt now carries a one-clause gloss per relation
  (`Relation.desc`), disambiguating confusable pairs — employment occasionally
  landed under `works_on` instead of `works_as`, silently defeating supersession.
- **examples**: end-to-end scam-email demo notebook with real captured outputs
  and a Colab badge, linked from the README.

## 0.1.0

First working release — the validated layered memory design as a plug-in.

- **Store of record**: typed graph edges + dated episodes with provenance;
  embedded `SqliteStore` behind a `Store` interface; per-user isolation.
- **Write path**: LLM extraction → edges + episode, functional
  supersession-with-history, reinforcement on re-statement, structural
  third-party quarantine (claims never become user facts).
- **Curated view**: LLM-compiled wiki cached and recompiled after N writes;
  third-party claims/episodes are never fed to the compiler.
- **Recall + abstention gate**: grounded/unverified partition; `answer()` answers
  only from grounded memory, never asserts unverified claims, abstains rather than
  confabulating.
- **Lifecycle**: volatility-driven expiry (transient lapse, durable stale-flag),
  consolidation with a compaction-loss guard; `maintain()` runs both.
- **Bring-your-own LLM**: `Complete`/`Embed` callables; Anthropic reference
  provider (`veracium[anthropic]`).
- **MCP server** (`veracium[mcp]`): `remember` / `recall` / `answer` / `maintain`
  tools for any MCP-compatible agent.
- **Telemetry** (opt-in, off by default): anonymous, content-free usage
  statistics with explicit consent (`veracium telemetry`), a weekly in-process
  flush (`mem.flush_telemetry()`), and a whitelist-enforced content-free
  payload. See `docs/telemetry.md`.
- **Self-check** (`veracium selfcheck` / `mem.self_check()`): runs the load-bearing
  guarantees (supersession, injection defense, abstention) against a throwaway
  synthetic memory and self-scores them structurally (no LLM judge); the counters
  feed telemetry's content-free `selfcheck` event.
- **Diagnostics** (opt-in error reporting; `veracium diagnostics`): genuine errors are
  logged to a local, user-owned rotating file and re-raised unchanged; the log is
  sent for diagnosis only with consent (advance permission or a per-incident yes),
  redacted, previewable, anonymous, and bounded. No endpoint shipped. See
  `docs/diagnostics.md`.
- **Docs**: `docs/concepts.md`, `docs/api.md`, `docs/mcp.md`; acceptance eval
  (`tests/eval/`) holding the library to the research claims (5/5, 0 injection
  asserts on the live run).
