# The COLLECTED.txt header as one structured artifact — the ask, and the design question

Spec-Status: n/a — a design note, not a spec. Nothing here is normative.

The external reviewer has asked three times, in escalating scope, for package
carriers to be generated and verified as whole artifacts rather than validated
as detached substrings. Twice the ask was narrow enough to implement directly,
and both are done. The third covers the entire `COLLECTED.txt` header, and it
is not blocked on effort — it is blocked on a question about what the
verification would be checking *against*. This note states the ask, the current
machinery, the question, and the options, so the question can be ruled rather
than quietly answered by whoever writes the code.

---

## 1. What was asked, and what has been delivered

**Round 18** — *"For the archive, I would ship one data-only identity manifest
and generate every identity carrier from it, while placing the entire lessons
summary under exact generator control."*

Delivered. `specs/package_identity.py` is the data-only record (version, round,
per-spec candidate revision); every identity carrier is filled from it; the
whole lessons summary — title, prologue, table, derived paragraphs — is
generated and byte-verified by `review_lessons.py --check`, which the archive
verifier runs.

**Round 19** — *"I would make the candidate block an exact rendered artifact
rather than parsing selected fields from it, and give generated blocks optional
boundary constraints such as 'must begin at byte zero.'"*

Delivered. The candidate field is compared byte-for-byte against
`render_candidate_field(version)`; `generated_block` takes a required
keyword-only `at_start` policy.

**Round 20** — *"For future robustness, a machine-readable schema for the
complete `COLLECTED.txt` header would help. I would change the archive by
generating and verifying that header as one structured artifact rather than
validating detached substrings."*

**Open.** This note is about that one.

The escalation is not the reviewer repeating themselves. Each ask was answered
at exactly the scope it named, and the next finding arrived one level up:
R19-1 was fields-instead-of-artifact, R20-1 was artifact-without-position. The
whole-header ask is the same lesson at the scope where it stops recursing.

---

## 2. What the header is today

`COLLECTED.txt` = a substituted template (`specs/package/collected_header.txt`)
followed by the generated skip-inventory block. The template carries eleven
tokens; the sealer substitutes them and refuses any that survive
(`refuse_placeholders`), which is what stops an unsubstituted token shipping.

Verification today is **per-fact and detached**: `identity_problems()` checks
the identity carriers, `verify_collected` checks the inventory block byte-for-
byte, the commit is cross-checked against `PACKAGE_MANIFEST.txt`,
`refuse_withdrawn_claims` greps the built artifact. Everything between those
checks — the explanatory prose, the field labels, the layout — is verified by
nothing.

That is the reviewer's point. The parts we learned to check are checked; the
rest of the file is unexamined, and "unexamined" is where every finding in this
review has lived.

---

## 3. Every header value, and what independently carries it

This table is the actual content of the design question. The column that
matters is the last one.

| header value | filled from | independent carrier inside the archive | witnessed? |
|---|---|---|---|
| round, version (line 1) | `package_identity` | the record + the archive basename + the manifest | **yes** |
| candidate revisions | `package_identity` | the record, cross-checked against `reviews.py` SENT rows | **yes** |
| source commit | `git rev-parse` | `PACKAGE_MANIFEST.txt` names it; agreement enforced | **partly** — see §4 |
| measured line | the `-rs` run | `COLLECTED_pytest_rs.txt` ships the full output | **yes** |
| harness results | running them | the extraction **re-runs both harnesses** | **yes** |
| evidence claim | the transcript | `specs/generated/evidence_run.json` ships and validates | **yes** |
| extracted-check list | `EXTRACTION_CHECKS` | the registry ships in `seal_package.py` | **yes** |
| package-built timestamp | `time.gmtime()` at seal | the archive **basename**, from the same variable | **no** — see §4 |
| measurement context | the sealing host | nothing | **no** |
| launcher result | the launcher run | nothing | **no** |
| explanatory prose | the template | nothing | n/a — not a claim about the run |

---

## 4. The design question

> Verify the header against **what**?

For most rows above the answer exists: the archive already carries an
independent witness, and the check can be a comparison against it. For three it
does not.

**The timestamp looks witnessed and is not.** It appears in the header and in
the archive filename, so a naive check would compare them and pass. But both
are filled from the same `ts` variable in the same function. Two carriers
written from one source prove **consistency, not truth** — the distinction this
review has spent twenty rounds on, in the one place it is easiest to miss,
because agreement between two copies *feels* like verification. A second copy
is not a witness.

**The measurement context and the launcher result describe the sealing host**,
which the extraction is not running on and cannot re-derive. A reviewer can
confirm the shape of those lines. Nothing in the package can confirm their
content.

So a structured header record shipped beside `COLLECTED.txt`, with the
extraction asserting `render(record) == header`, would prove:

- the header is exactly what the generator produces from the record — real, and
  it closes the unexamined-prose gap;
- every declared field is present, in order, with nothing undeclared — real,
  and it is the closed-schema property that R15-1 taught us to make recursive.

and would **not** prove that the record's own run-specific values are true. For
those fields it relocates the self-assertion from the prose into the record. A
smaller surface, better shaped — but the same class this review keeps finding,
and worth naming before we build it rather than after someone attacks it.

---

## 5. Options

**A. Structured record + byte-exact render.** Ship `collected_header.json`;
extraction asserts the header renders from it. *Closes:* unverified prose,
field order, undeclared/missing fields. *Leaves:* three self-asserted values,
now in a tidier place.

**B. Per-field witness binding, no record.** Bind each field to its independent
carrier (measured ↔ `-rs` tail, harnesses ↔ re-run, evidence ↔ transcript,
identity ↔ record) and leave the rest alone. *Closes:* the fields that can be
witnessed, properly. *Leaves:* the prose and the layout unverified — i.e. the
reviewer's actual complaint.

**C. Both, with the evidentiary status declared per field.** The record carries,
for every field, its value **and how it is witnessed** — `derived`,
`cross-checked-against-<carrier>`, or `stated-only`. Extraction asserts the
render is byte-exact, runs each declared cross-check, and refuses any field
whose declared status it cannot satisfy. `stated-only` fields are printed as
such in the header.

C is the only one that does not create a new place for an unbacked claim to
hide, because it makes the archive **say which of its own claims are
unverifiable from inside it**. That is a stronger position than either proving
nothing about them or implying they were checked.

**Recommendation: C.** The prose moves into the generator, exactly as the
lessons prologue did under R18-2 — precedent exists and it worked.

---

## 6. What to settle before code is written

1. **Is C's honesty acceptable in a reviewer-facing carrier?** The header would
   gain a short line saying, in effect, *these three values are stated by the
   sealer and nothing in this package can confirm them.* I think that is
   strictly better than the status quo, where the same is true and unsaid. It
   is a presentation decision, not a technical one.
2. **Is the timestamp worth witnessing at all?** It could be bound to something
   external (a signature, a CI attestation, the commit date as a lower bound).
   Each adds machinery. My read: record it `stated-only` and stop pretending
   otherwise. But it is the reviewer's instrument, so their view should decide.
3. **Prose in the generator — accepted cost?** Editing the header would then
   mean editing `seal_package.py` and regenerating. That is the cost of
   byte-exactness and I think it is worth paying; it is also irreversible in
   practice once the template is gone.

---

## 7. Failure modes to design against

Written down first because five of the last six findings were defects *in the
previous round's fix*, and this change touches the machinery that has produced
most of them.

- **The record must not be hand-maintained.** A `collected_header.json` typed
  by a human is R8-2 with a schema — four hand-maintained package claims that
  had gone false.
- **The schema must be closed at every level.** R15-1: commands rejected
  undeclared fields while the object holding them did not.
- **The record must be bound to its position and label**, not merely present
  somewhere in the archive. R20-1: a block that occurs anywhere is not a field
  that states it.
- **Nothing may verify an artifact its own run produces.** R21-1, R15-3: the
  header check must not read a record written by the same step that renders it
  without an independent path.
- **Every new field needs a mutation.** The transcript's derived mutation
  matrix is the working model: adding a field automatically demands coverage,
  so the "which fields did we test" question cannot be answered wrongly.

---

## 8. Status

Not started. Not blocked on effort — blocked on §6.1 and §6.2, which are
judgement calls about what a review package should claim about itself, and
those belong to Quentin and to the reviewer rather than to whoever writes the
patch.

This note ships in the archive so the reviewer can rule on it directly.
