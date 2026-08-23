# The COLLECTED.txt header as one structured artifact — the ruled construction

Spec-Status: n/a — a design note, not a spec. Nothing here is normative.

**Reviewed by the external reviewer 2026-08-20. Verdict: sound direction,
revise before implementation — three blocking findings, four moderate, and
rulings on all three open questions.** This revision folds every finding; the
construction is settled below as **C-plus** and implementation is unblocked,
pending scheduling. The review's most important sentence is recorded first,
because it is this project's recurring defect stated in its purest form yet:

> *If each field carries its own evidentiary status, a mutation could change
> `cross-checked → stated-only` and the verifier would honestly satisfy the
> altered record while silently removing a previously required check.*

My Option C handed the subject of verification the choice of its own policy.
**A record may REPORT how it is witnessed; it must never CHOOSE it.** That is
self-assertion one level up from anywhere it has appeared in twenty-one
rounds: not a claim about a value, but a claim about how much scrutiny the
value deserves.

---

## 1. History of the ask

**Round 18** — a data-only identity manifest; the lessons summary under exact
generator control. *Delivered* (`package_identity.py`; `review_lessons.py
--check` byte-verifies the whole summary).

**Round 19** — the candidate block as an exact rendered artifact; boundary
constraints on generated blocks. *Delivered* (`render_candidate_field`;
`generated_block`'s required `at_start` policy).

**Round 20** — a machine-readable schema for the complete header; generate and
verify it as one structured artifact. *This note.*

**The note's own review (2026-08-20)** — direction endorsed, design corrected
before a line of code: my proposal had the record choosing its own scrutiny
(blocking 1), left the seam between two verified artifacts unverified
(blocking 2), and never specified the order that stops the renderer and the
record agreeing because they were derived from the same wrong in-memory values
(blocking 3). Each is a found-in-fix failure caught at the design stage — the
cheapest place this review has ever caught one.

---

## 2. What the header is today

`COLLECTED.txt` = a substituted template (`specs/package/collected_header.txt`,
eleven tokens) + the generated skip-inventory block. Verification is per-fact
and detached: identity carriers, the candidate field, the inventory block, the
commit agreement, and the withdrawn-claims sweep are each checked; the prose,
layout, and — decisively — **the seams between the checked parts** are checked
by nothing.

---

## 3. Every header value, its source, and its witness

Revised per moderate findings 4 and 5: "witnessed?" was one column collapsing
several questions, and "stated-only" undersold what the sealing execution can
capture.

| header value | source | witness (package-local) | external attestation |
|---|---|---|---|
| round, version | `package_identity` | the record + basename + manifest, cross-checked | — |
| candidate revisions | `package_identity` | the record + `reviews.py` SENT rows | — |
| source commit | git | `PACKAGE_MANIFEST.txt` agreement; the commit object itself | — |
| measured line | measurement output | `COLLECTED_pytest_rs.txt` (full `-rs` output ships) | — |
| harness results | harness runs | the extraction re-runs both | — |
| evidence claim | the transcript | `evidence_run.json` ships and validates | — |
| extracted-check list | `EXTRACTION_CHECKS` | the registry ships in code | — |
| measurement context | **runtime probe** | a captured probe artifact (python/pytest/sqlite versions, command, cwd, env controls) — *currently prose; C-plus captures it* | none |
| launcher result | the launcher run | its complete stdout/stderr + exit + digest — *currently one line; C-plus captures it* | none |
| package-built timestamp | clock | structural checks only (§5.4) | **none — declared** |
| static prose | template | byte-exact render | n/a |

Moderate 5's point, folded: the measurement context and launcher result are
not condemned to "stated-only". They can carry **captured-from-the-sealing-
execution** evidence — a runtime probe artifact, a launcher transcript with
digest — which does not prove the sealing host honest but is strictly stronger
than prose. The distinction that survives is between *captured* and
*externally attested*, and only the timestamp's wall-clock truth sits in the
second gap.

---

## 4. The two consistency-not-truth traps, both now closed by construction

**At verification time** (original §4): the timestamp appears in the header
and the basename, but both come from one variable — comparing them proves
consistency, not truth.

**At construction time** (blocking 3, new): if the record and the rendered
header are produced from the same in-memory values in the same step, they
agree *perfectly and vacuously* — including when those values are wrong. The
witness must be an **immutable raw output captured before the record exists**,
and the record must be **derived from the capture**, never from the variables
that produced it.

---

## 5. The ruled construction: C-plus

### 5.1 The pieces

1. **`collected_header.json`** — generated, closed at every level (R15-1),
   never hand-maintained (R8-2). It reports values and *reports* their
   evidentiary classification.
2. **A code-owned field-policy registry**, keyed by field name, in the
   verifier's codebase — **the sole authority on how each field must be
   witnessed**. The record cannot downgrade what the registry demands; a
   record whose reported classification disagrees with the registry is
   refused, and so is a record missing a field the registry names (blocking 1).
3. **Fixed witness implementations** with closed identifiers — `pytest_rs`,
   `package_manifest`, `harness_rerun`, `runtime_probe`,
   `launcher_transcript`, `none` — not free-form strings. A witness id the
   verifier does not implement is a refusal, not a skip (moderate 4).
4. **Captured raw artifacts** shipped in the archive: the `-rs` output
   (already ships), the runtime probe, the launcher transcript with digest
   (moderate 5).
5. **Whole-file construction**, not part-wise checking (blocking 2):

       COLLECTED.txt == render_header(record) + render_skip_inventory(run)

   header anchored at byte zero; exactly one inventory block immediately
   following; EOF immediately after the permitted final newline. **No bytes
   exist that no check owns.** Verifying parts separately leaves the next
   finding living between two "verified" artifacts — R20-1's lesson at file
   scope.
6. **A dedicated renderer/template module** owning the static prose, governed
   by the record's schema — *not* `seal_package.py` (moderate 7, ruling 3).
   Editorial changes stay reviewable as data; the verifier binds exact bytes
   and positions either way, so moving prose cannot weaken anything.
7. **Mutations generated from BOTH the record schema and the policy
   registry** — every field crossed with: value mutations, status
   *downgrades*, changed witness ids, and removal of a required witness. The
   downgrade mutations are the ones blocking 1 exists for, and the transcript
   schema's derived matrix (R15-1's fix) is the working model.

### 5.2 Evidentiary axes (moderate 4)

One enum collapsed origin, validation, comparison, independence, and
attestation. Four closed axes instead:

    source:               measurement_output | runtime_probe | clock | package_identity | registry
    validation:           syntax | internal_consistency | independent_cross_check
    witness:              pytest_rs | package_manifest | harness_rerun | runtime_probe | launcher_transcript | none
    external_attestation: none | signed_ci

The registry declares the *required minimum* per field on every axis; the
record reports what was done; the verifier refuses any field below its
registry minimum.

### 5.3 Construction order (blocking 3) — normative for the implementation

    1. run the measurement and harness commands
    2. capture immutable raw outputs (files, digested)
    3. derive the structured record FROM THOSE OUTPUTS — never from the
       in-memory values that produced them
    4. cross-check every independently-sourced field against its witness
    5. render COLLECTED.txt from the record
    6. reparse and verify the FINAL ARCHIVE (the whole-file equation, from
       the extraction)
    7. refuse any later mutation

Steps 2→3 are the load-bearing pair: they are what makes agreement between
record and render mean something.

### 5.4 The timestamp (moderate 6, ruling 2)

Wall-clock truth: **externally unattested, and the record says so.** Still
enforced, labelled as consistency-and-plausibility rather than truth:

- strict UTC format;
- one canonical value across basename and header (consistency between copies
  of one variable — labelled as exactly that);
- ordered after measurement completion;
- not in the verifier's future beyond a declared tolerance;
- archive-member mtimes not later than the declared seal time.

Signed CI provenance only if authenticated creation time ever becomes a real
requirement. It is not one today.

---

## 6. The three questions — RULED (2026-08-20)

1. **Is the honesty acceptable in a reviewer-facing carrier?** **Yes.**
   *"Explicitly disclosing internally unverifiable claims is preferable to
   implying they were verified."*
2. **Witness the timestamp?** **Not for this package generation.** Structural
   and consistency checks per §5.4; wall-clock truth declared unattested.
3. **Prose under generator control?** **Yes — in a dedicated renderer/template
   module governed by a closed schema**, not inside the sealing code. Coupling
   editorial edits to security-critical packaging was the cost I had accepted
   and should not have.

---

## 7. Failure modes to design against

The original five stand (hand-maintained record · schema closed at every
level · bound to position and label · nothing verifies what its own run
produces · every field gets a mutation). The review added three, each a class
instance caught before it shipped:

- **The record must not choose its own scrutiny** (blocking 1). Policy lives
  in the verifier's code; the record reports it; disagreement refuses.
  Self-assertion, one level up: a claim about how much checking a claim
  deserves.
- **The seam between two verified artifacts is unverified** (blocking 2). Own
  every byte of the file or name the finding now: undeclared bytes between
  blocks, duplicated blocks, trailing prose, a header at the wrong boundary.
- **Agreement is vacuous when both sides share a source** (blocking 3). The
  record derives from captured immutable outputs, never from the variables
  that produced them — consistency-not-truth, at construction time.

---

## 8. Status

Design **ruled and closed**; **IMPLEMENTED 2026-08-22** — every §5 piece:

- `specs/collected_record.py` — the code-owned FIELD_POLICY registry (the
  sole authority; blocking 1), the four closed axes, the derive-from-capture
  functions (blocking 3), and the fixed witness implementations (moderate 4;
  an unimplemented witness id refuses).
- `specs/collected_render.py` — the whole-file equation (blocking 2): header
  at byte zero, one inventory block, EOF after the final newline, byte
  equality against the recomputed construction; static prose stays in the
  template as data (ruling 3), token set closed both ways.
- `specs/runtime_probe.py` — the captured measurement-context artifact
  (moderate 5); also the one authority for the measurement argv/env.
- `specs/seal_package.py` — main() restructured into the §5.3 order:
  measure → capture (probe, launcher transcript with exit trailer, harness
  stdouts) → derive `collected_header.json` from the captures → validate +
  witness cross-check → render → whole-file equation → archive (three new
  loose carriers) → §5.4 timestamp structure in verify_archive (basename/
  record one canonical value; member mtimes ≤ declared seal time).
- `specs/verify_extracted.py header` — the extraction re-runs all of it:
  record conformance, template digest, whole-file recompute, witnesses.
- `tests/test_collected_header.py` — the §5.1.7 mutation matrix GENERATED
  from schema × registry (value mutations, validation downgrades, changed/
  removed witness ids, redirected artifacts, extra/missing fields), the
  seam injections, the derive-from-capture property, and the labelled
  timestamp checks.

It ships in `specs/`, so the next sealed package (whichever line it is)
carries its own packaging contract and verifies it from the extraction.

---

## 9. Implementation review — round 1 (2026-08-22): RETURNED, folded same-day

The reviewer attacked the implementation using the live 0001-v3 specimen
(two live seals had run clean by dispatch). Verdict: return for revision —
two blocking, one moderate. Every finding was verified against the code and
folded; each is the review's own recurring class, caught one level deeper:

1. **F1 (blocking) — the record could claim MORE scrutiny than occurred.**
   `validate_record` enforced a minimum where the ruled principle ("the
   record may report the policy, it must never choose it") demands
   exactness: `independent_cross_check` without an independent witness and
   `signed_ci` without any signature both passed. **Folded: classifications
   must EQUAL the registry's** — a stronger claim becomes admissible only
   when a code-owned proof requirement for it exists (none does; `signed_ci`
   needs its signature carrier, signer identity rules and verifier first).
   The mutation generator had encoded the same one-directional assumption
   (downgrades only) — it now generates BOTH rank directions and every
   attestation value, and the two named escalations are pinned by name.
2. **F2 (blocking) — the manifest was a partially-verified carrier.** A
   forged 40-char commit sharing the 7-char prefix, appended contradictory
   identity lines, and stale hand-maintained version prose all passed. This
   is blocking 2's class on the OTHER carrier: the whole-file equation
   existed for COLLECTED.txt while `render_manifest` output went unbound.
   **Folded: `PACKAGE_MANIFEST.txt == render_manifest(record, template)`,
   byte-for-byte, template digest-bound in the record (RECORD_VERSION 2:
   `templates.{header,manifest}`), verified from the extraction; commits
   compared on all 40 characters; identity lines required unique; dynamic
   prose tokenised out of the manifest templates.**
3. **F3 (moderate) — the mtime ordering was tolerance-weakened.** §5.4
   promises member mtimes ≤ the declared seal time; the loose carriers
   landed ~13s after it and passed under the 900s tolerance — one constant
   serving two contracts. **Folded: `build_archive` stamps appended members
   with the declared seal epoch; `verify_archive` enforces `mtime ≤
   seal_epoch` exactly. The tolerance remains only where it belongs — the
   verifier's-own-clock future check.**

Survived the reviewer's attacks: the whole-file COLLECTED construction, the
capture-before-record ordering, the clean-path verifications, and the
launcher's runtime qualification (it refused their SQLite 3.53.1, which
they correctly treated as the guard working). Queued from the round: a
portable qualified runtime for independent full-suite reproduction (rides
with the hashed no-ensurepip launcher bootstrap item).

## 10. Implementation review — round 2 (2026-08-23): F1/F3 CLOSED; F2 one layer deeper

**R2-1 (blocking) — the digest-bound manifest template was itself an
unchecked policy source.** The reviewer's full-repack attack: keep the
legitimate `__CANDIDATES__` token, plant a static `draft v999` candidate
claim IN THE TEMPLATE, update `templates.manifest.sha256`, re-render —
every check recomputed perfectly, because the equation proves the output
came from the bound template and nothing proved the template's dynamic
claims came from the record. Recursive carrier completeness, one layer
below round 1's fix. **Folded:** the registry now carries `in_manifest` —
seven required dynamic facts (package, round, commit_full, ts, candidates,
measured, loose) whose tokens the manifest template must carry EXACTLY
once (`render_manifest` refuses omission and duplication), and the
candidate-field discipline COLLECTED.txt has is SHARED with the manifest
via `package_identity.CANDIDATE_LINE_RE` (one authority): the record's
rendered field exactly once, candidate-shaped claims outside it refused.
The regression is the reviewer's own attack — template + digest + rendered
manifest mutated together.

**R2-2 (moderate/package-blocking) — the F3 regression could not run from
an extraction.** It called `build_archive` → `git archive`, and review
packages carry no `.git`; the reviewer's advertised-command run failed,
meaning the named check never executed on their artifact and a qualified
launcher would fail rather than reconcile. **Folded:** the mtime transform
and the §5.4 predicate are pure helpers (`stamp_loose_member`,
`member_mtime_problems`) — the builder and verifier call them, the
regression tests them git-free, and the `seal_epoch + 1` injection the
reviewer asked for is asserted to refuse.

Confirmed closed by the round: both F1 escalation directions, false
`signed_ci`, forged 40-char commits, output-only manifest edits, duplicate
identity lines, zero post-seal members with exact epoch stamps, and the
`seal_epoch + 1` repack refusal.

## 11. Implementation review — round 3 (2026-08-23): F1/F3 hold; C3-1 folded

**C3-1 (blocking) — the manifest candidate field was PRESENCE-bound, not
position-and-label-bound.** The reviewer's relocation attack: a static
`specs: none` line on the real label with the correct rendered field behind
a `backup:` prefix — template digest updated, manifest re-rendered, all 422
members exact — passed the whole extraction workflow. R20-1's lesson,
verbatim, on the second carrier. **Folded:** the position-and-label binding
is ONE shared implementation, `package_identity.candidate_field_problems`
(exactly one `specs:` label; the record-rendered field begins at its
offset; nothing candidate-shaped outside), consumed by BOTH
`seal_package.identity_problems` (COLLECTED) and
`collected_render.manifest_problems` (manifest). The regression is the
reviewer's exact relocation, full-repack shape.

Also confirmed by the round: the round-2 timestamp helpers and the
required-token omission/duplication checks hold. The no-`ensurepip`
launcher bootstrap requested at rounds 1 and 3 is DELIVERED (hash-locked
no-pip venv: `--without-pip`, every wheel sha256-verified against the lock,
stdlib unzip — the refusal path is gone for qualified interpreters).

## 12. Implementation review — round 4 (2026-08-23): C4-1 + C4-2 folded

**C4-1 (blocking) — start-bound but not end-bound**: the canonical field
with a same-line contradiction appended ("… — withdrawn; no external
candidate is under review") passed. The reviewer found the missing
regression BY ITS TAUTOLOGY — the test's end-bound assertion was
neutralized with `or True`. **Folded:** the byte after the rendered field
must be newline or EOF (`candidate_field_problems`, both carriers); the
tautology is replaced by the reviewer's exact contradiction, exercised
through the manifest in full-repack shape.

**C4-2 (moderate) — the no-pip bootstrap verified membership, not the
SET**: a locked wheel removed and a renamed duplicate of another locked
wheel standing in passed (digest-in-lock + count parity). **Folded:**
`verify_wheelset.py` — each requirement bound to ITS OWN digest set, wheel
identity read from METADATA, exact bijection required (duplicates,
absences, and wrong-requirement digests all refuse); the launcher runs it
before anything unpacks; the reviewer's exact mutation is the regression.

## 13. Implementation review — round 5 (2026-08-23): C5-1 + C5-2 folded

**C5-1 (blocking) — authenticated-but-false history.** The line templates
said "first sealed package / first live seal" on the line's THIRD sealed
round, and CHANGED_FROM_PREVIOUS skipped because the sealing host had
deleted the prior archives — the disclosed template limitation, landed.
**Folded:** `history` and `changes` are DERIVED record fields
(`derive_line_history` / `derive_changes_pointer`, from the
review/package ledger), rendered via tokens, re-derived by the witness at
extraction; the stale static prose is deleted from both templates; and
the sealer now REFUSES to seal when the ledger records a prior sealed
round whose archive is absent from the outbox — the named skip is
reserved for genuine first packages. Workflow change: prior archives are
KEPT in the outbox as the diff base.

**C5-2 (moderate) — the lock parser failed open.** An appended
direct-reference requirement sat outside the computed set. **Folded:**
strict logical-line grammar (name==version + hash options ONLY; direct
references, markers, options, duplicates, orphan continuations all
refuse), parse problems surfaced through `verify()`, the reviewer's
appended line as the regression.

## 14. Implementation review — round 6 (2026-08-23): C6-1 + C6-2 folded

**C6-1 (blocking) — the generated history inferred beyond its domain.**
`derive_line_history` claimed "document-only" for every round before the
registry's first entry — FALSE for 0022-0023, whose v3-v16 sidecars sit
committed in specs/archives. The registry defines the generator's governed
DOMAIN; absence from it is not evidence about the world. **Folded:** the
history states governed rounds only and points earlier rounds at the
committed sidecar index without characterising them; the regression sweeps
EVERY line in the registry, 0022-0023 included.

**C6-2 (blocking) — "some lower version" is not the predecessor.** With
v3/v4/v5 in the ledger, a directory holding only v3 satisfied the prior
check for v6 and seeded the diff. **Folded:** `required_predecessor`
computes the maximum declared lower version, requires an archive of
EXACTLY that version, selects the newest timestamp deterministically, and
verifies its sha256 against the COMMITTED sidecar; older-only,
wrong-version and wrong-hash all refuse (tested). The committed
specs/archives INDEX + sidecars serve as the hash-witnessed lineage index
the round asked for; both ship in every git archive.

## 15. Implementation review — round 7 (2026-08-23): C7-1 + C7-2 folded

**C7-1 (blocking) — the hash-witnessed lineage was incomplete, and the
wound was self-inflicted**: the v3/v4 sidecars of DISPATCHED packages had
been deleted by the reseal workflow's own discard step, so C6-1's
governed-domain history pointed at witnesses that did not exist — one
false carrier claim replaced by another. **Folded:** the dispatched
sidecars RESTORED from git history (their digests match the shas the
round-3/4 verdicts quote); a generated LINEAGE table in the archives
INDEX with EXACT PACKAGES↔sidecar correspondence, enforced by
`lineage_problems` at every render, every suite `--check`, and every
seal; discarded/superseded seals disclosed BY NAME
(`DISCARDED_PRE_ROUND`); and the workflow rule inverted — dispatched
sidecars are never deleted.

**C7-2 (blocking) — two predecessor selectors could diverge**: the
verification glob was looser than the diff's parser, so a witnessed
malformed-name decoy could satisfy the gate while the diff consumed an
unwitnessed canonical. **Folded:** ONE strict selector
(`required_predecessor`, exact-grammar filename match), and the verified
Path it returns is passed INTO `_changed_from_previous` — reselection
prohibited.

## 16. Implementation review — round 8 (2026-08-23): C8-1 + C8-2 folded

**C8-1 (blocking)** — the lineage check counted FILENAMES: malformed
sidecar content and a deleted frontier witness both passed. **Folded:**
the sidecar RECORD is validated (`<64-hex>  <name>.tar.gz`, target equal
to the sidecar's own stem); the in-flight exemption is an EXPLICIT
declaration (`IN_FLIGHT` in package_identity — diffable, cleared by the
sidecar commit) and the sealer refuses to seal any version not named
there; render/suite checks are strict over everything else.

**C8-2 (blocking)** — `None` from a line's first governed round
reactivated the diff's internal fallback selector, which could consume an
undeclared archive. **Folded:** the `NO_PRIOR` sentinel distinguishes
"explicitly no predecessor" from an omitted argument; the diff function
takes `prior` as a required keyword and performs NO selection, ever.
