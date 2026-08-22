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
