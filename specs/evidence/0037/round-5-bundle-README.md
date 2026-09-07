<!-- TERMINAL RECORD of spec 0037's external review. The bytes below the
     marker line are the round-5 bundle README exactly as sealed in the
     ACCEPTED package 0037-round5-review-package.tar.gz (sha256
     78a20446b085d7999c14957d373d9793817c0743ffa362665defa043b1094527,
     pin ae6be7687ac77a73da7d232722a7bfb629434447, CI 34067972232),
     copied UNMODIFIED at acceptance (2026-09-07) and cmp-proven against
     the packaged member at that moment. It carries every disposition
     map and errors ledger of the arc's five rounds by reference to
     prior-rounds/. Do not edit below the marker. -->
<!-- BEGIN PACKAGED BYTES -->
# 0037 procedural records and the `basis` axis (stages 1–3) — round-5 external review bundle

Assembled 2026-09-06 by dev. Fifth external round for spec 0037. Round 4
(package `35f2f7826a7b4f849a2314620fd055542401b1c55b82396e06c9f56fb80c9f25`
@ `07d28a58a1276af96a4f5705e341499975a5831d`, CI 34061355491) returned the
same day: **RETURN for revision** — all ten round-3 findings named closed,
ONE blocking inconsistency at the intersection of the declared format
version and the three-signal import rule, five non-blocking corrections.
All four verdicts are in `prior-rounds/` verbatim as banked. This package
carries **v13**, the fold of the round-4 verdict, with the acceptance
corpus amended once against it and rebound in both directions. Nothing is implemented; prose,
one corpus artifact and the tests that bind and validate it.

**Canonical artifact:** `specs/0037-procedural-basis.md` at the pinned
commit (see `PIN.txt` — commit, CI run id, and the suite line as printed;
repo `github.com/veracium-ai/Veracium`, public). The copy here
(`0037-procedural-basis-SPEC-v13.md`) is byte-identical to `tree/specs/`
at seal; on any doubt the repo wins.

## A disclosure before the disposition map

**The reviewer has not been able to run the suite in any round, and this
round's package says so in the same words as the last.** Round 3's verdict,
verbatim: "The package reports `2737 passed, 9 skipped`; the
complete suite could not be independently run because the available
Python runtime lacks `pytest`." In detail: the outer checksum, all 567 manifest entries, the
spec-copy comparison and the corpus digest were checked by hand and
passed; "2737 passed, 9 skipped" is OUR fresh-clone capture reported back
to us, not an independent reproduction, because the reviewer's Python
runtime lacks `pytest`. Round 4's verdict repeats it: "the complete suite
remains independently unexecuted because the available runtime lacks
`pytest`." The same was true in rounds 1 and 2. We say it
here so four rounds of "capture verified" do not accumulate into an
assumption nobody re-checks: the suite line in `PIN.txt` is dev's capture
at the pin, research's leg re-ran the pin tests and the offline matrix
from the archive's bytes, and nobody outside the two seats has executed
the suite. If your runtime can, `python -m pip install -e "tree[dev,mcp]"`
then `python -m pytest -q tree/tests` is the reproduction.

## Disposition map — every round-4 item, answered in the spec

| # | the finding (reviewer's words, abridged) | disposition | where in v13 |
|---|---|---|---|
| B1 | the version-key stripping rule disables two of the three import signals: a format-10 file carrying a procedural marker under an unknown or declarative relation imports as declarative | the reviewer's second option: the three signals are evaluated on the RAW record BEFORE any version normalization; a raw `record_kind == "procedural"` or raw non-null `basis` refuses THAT RECORD with its signal named and `raw: true` (the presence of a newer key in a format-10 envelope is the evidence); the registry signal is read on the same raw record; only admissible records are then normalized. Refusal is RECORD-level, never file-level — a mixed file keeps its declarative records. The 8-cell raw-marker × receiving-relation matrix is in the spec and, verbatim, in the corpus as named cells; V-IMPORT's mutant is "normalize before inspecting", and the two cells that catch it are the ones the single v12 cell could not express (`procedural stamp × unknown`, `basis × declarative`). Read the matrix as DISCRIMINATION, not coverage: six of its eight rows pass under the broken implementation too, and the two that do not are flagged in the corpus with the reason — the registry signal does not fire in those states, so the raw marker is the only thing between the record and ordinary recall | §2c (import row), §4e Export, V-IMPORT-REFUSES-PROCEDURAL-UNLESS-RESTORE, §6a |
| C1 | replace the single format-10 corpus cell with the full matrix | done in research's amendment 4, verbatim, with the two mutant-catching cells annotated and a note that the superseded cell was a tautology (it fixed the relation in the one state where the registry refuses regardless) | corpus `named_cells`, §6a |
| C2 | record or file refusal on a version/key disagreement | RECORD — stated in §2c, §4e and V-IMPORT | §2c, §4e |
| C3 | V-IMPORT to say raw record or after normalization | "evaluated ON THE RAW RECORD, BEFORE version normalization", in those words | V-IMPORT |
| C4 | the §4a heading names only the registry | renamed: the registry at write, the record's own stamp at read, three raw signals at import; never the text | §4a heading |
| C5 | "validates through the declared field types" overstates what the test does | the narrower form used everywhere, in the spec and the manifest: domain validation now, real `Provenance` construction after implementation | V-CORPUS-ROWS-IN-DOMAIN, §6a, the manifest |

**Preserved as you named them closed:** `None` for the declarative stamp;
972 valid cells; the four coherent states; the corpus rebound both ways;
format 11 for procedural exports and an old reader's refusal; format 10
for procedural-free exports; the registry consulted when both markers are
genuinely absent; restore's rejection of inconsistent pairs; exclusion
language on the stored rule. None moved in v13 except where B1 required.

## Where the authors ask you to attack (spec §9, updated for round 5)

1. **Raw-record evaluation reads keys the format did not declare.** We
   now inspect `record_kind` and `basis` on a format-10 record before
   normalization. If there is a THIRD way a procedural record can be
   represented in a serialized form the raw inspection does not read —
   a key under another name, a nested carrier — that is the cell we have
   not written, and the fourth signal we did not name.
2. **The conditional version stamp is per-export, not per-record.** A
   procedural-free export stays at 10 for byte compatibility. If a
   procedural record can be present without either marker being present
   in the SERIALIZED form the stamp inspects, the file is stamped 10 and
   an old reader accepts it.
3. **`kind_conflict` is a tamper state that no shipped writer produces.**
   If one can, the floor is right in the safe direction and the name is
   wrong in the expensive one.

## The internal passes and the corpus amendment (research, 2026-09-06; amendment 4 for this round)

Research banked round 3's verdict (it arrived in their session), checked
finding 1 against the generator before writing to dev, and held the
corpus amendment until dev's import decision and the corrected text
existed, so that the amendment and the rebind happened ONCE. The
amendment encodes the declarative stamp as `null`, documents the axis as
a representation, adds the six import/restore cells as named cells, and
states row-schema validation as a corpus requirement. Dev refused to fold
from research's summary of the verdict and folded from the banked file;
research's reading turned out accurate, and both seats recorded that this
was luck, not method, and that the method is what stops the third time.

## Errors ledger

Rounds 1–4's ledgers are in `prior-rounds/`. This round:

- **The strip-before-inspect rule (B1), dev's in the text and research's
  in the corpus cell.** Dev wrote the format-10 special case so that the
  existing newer-field strip ran before the three-signal classification,
  erasing two signals; research's single corpus cell for it fixed the
  receiving relation as procedural — the one state where the registry
  refuses regardless — so the cell could not fail under either
  implementation and its justification described the reasoning that made
  it useless. The reviewer found it by varying the axis the cell held
  fixed. Fixed on both sides: the rule reads the raw record first, and the
  8-cell matrix carries the two cells that discriminate.
- **No seal was discarded in this round's chain as of assembly**; if one
  is, `PIN.txt` and `collected/COLLECTED.txt` disclose it and the assembly
  asserts the two agree on every digest and refuse any fill-me-in form.

**What the lineage means.** This package's predecessors now run: four
discarded seals, one held stage, one superseded-never-dispatched seal,
and four dispatched-and-returned rounds. Every entry that was never
dispatched was caught by one of the two seats before anything was sent;
every dispatched round was folded in full the same day. A reviewer
meeting that many predecessors could read instability; it is the
opposite, and this ledger says which.

## Contents

- `0037-procedural-basis-SPEC-v13.md` — the spec, byte-identical to `tree/specs/`
- `PIN.txt` — commit, CI run id, suite line, corpus digest, and every disclosed identifier
- `collected/COLLECTED.txt`, `collected/suite-run-raw.txt` — the fresh-clone capture at the pin, profile `[dev,mcp]`, raw transcript from the same run
- `prior-rounds/` — the round-1 through round-4 READMEs and verdicts, verbatim
- `tree/` — `git archive` at the pin (tracked files only, asserted both directions), including `tests/eval/procedural_describe/MANIFEST.json` and `tests/test_0037_corpus_pin.py`
- `SHA256SUMS` — every file above, excluding itself
