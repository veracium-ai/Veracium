# Feature spec: credential-shaped text is never stored

Spec-Status: accepted

| | |
|---|---|
| **Author / session** | research (veracium-research), candidate v0.1 → dev (veracium-61), adopted 2026-11-22 at rest and re-read from the file: v0.5.2 from research `a07a6910`'s `proposals/0055-credential-shaped-text-never-stored-CANDIDATE.md` (sha256 `48b05ffe…840f`). Dev owns this cell from adoption on |
| **Version** | **v0.5.8 — 2026-11-25: round 4's implementation corrections recorded, and the text corrections it asked for; the design is not reopened.** Round 4, the build review, RETURNED six implementation findings and the residual-report amendment A1 (banked at coordination `a421b28`). Dev fixed them with research's stage-1 sweeps S1–S3 (veracium `cb6462a4` to `6ef11e12`). What the text now records: every argument the screen takes is refused by type before any consumer, D3's screen included (§2c, §4b; R4-01); a fresh cached wiki body is masked on read (§4e; R4-02); every report that names records names a shaped id by ordinal, render receipts, import's procedural refusals and the served redaction receipt included, while the library `RedactionReceipt` keeps 0041's ids (§4g, §8; R4-03 and S2); the finder reads every per-user table from the live schema and fails closed (§4f; R4-04 and S1), and journal text a second redaction cannot reach is a residual (§4f; found by round 5's carrier-to-boundary table, with an episode's printed date and `why`'s keys and lookup fields, §4e); the CLI's defect path quotes no input, and a validation location prints only declared names (the Build section's *The scope of E1*; R4-05 and S3); the diagnostics send path screens whole lines before it cuts (§4i; R4-06); `maintain()`'s pool key is in the finder's declared list (§4f; A1). The text corrections: §10 Q8 decided; the mutant count read from the table at the pin; the I19 matrix row's 102 pairs; I9's wording names the ten-round remeasurement and the gate's limits (§6, §8). **Prior:** **v0.5.7 — 2026-11-24: an underscore no longer shields a token (§4a's token boundary), the shapes version becomes 2, and two build carriers brought to the tree; nothing else the product does changes.** The owner's ruling, first-hand to dev and relayed by dev, *"Fix the recogniser (Recommended)"*, on research's QC of the test harness (step 6 of `proposals/evidence-test-harness-qc-2026-11-23/`): `has_key_` followed by a GitHub-style token was stored with the token in it, because a structural pattern's `\b` treats `_` (and every Unicode letter) as part of a word; dev confirmed the boundary was not deliberate. From v0.5.7 a structural pattern may not start just after an ASCII letter or digit, and the five that end on a boundary may not end just before one; `_` and every other character are a boundary. The reference model changes with it (the boundary in 20 patterns, nothing else), and the table gains 18 glued rows (G1–G18, each RED on v0.5.6's patterns), 8 near-misses (K48–K55: snake_case identifiers holding a vendor prefix, Stripe's mode words; K55 RED with no boundary at all) and 2 stated limits (X7, X8: a token glued to an ASCII letter or digit): 150 rows (§6 I1, I2). Measured on the corpora (§8): no unit changes its findings, and the corpora present the condition in 6 units only. T1 re-run with two glued cases, 3.9–4.2× (§4a). `CREDENTIAL_SHAPES_VERSION` becomes 2, so an audit line names which boundary screened a write (§4a). The Build section records dev's I9 interleaving (`f86dc0ea`) in place of a row it made stale, and discloses the removal of two §4e masks no product path reaches (`credentials.masked_episode`, and `gate.partition`'s; research's QC, equivalent mutants M313 and M318). The PIN rule keeps its boundary, a separate question (§10 Q8). **Prior:** **v0.5.6 — 2026-11-23: §4b-ii D1's order stated at its true width, and I9 measured past a cache step; no change to what the product does.** I9 (the owner's ruling, first-hand to dev and relayed by dev, "Measure past the step (Recommended)", after CI run 45275466884 read 6.96× and 7.24× on two label cases at 256 KiB→1 MiB on a quiet runner): the ratio ≤ 6 is asserted on 1 MiB→4 MiB, the 256 KiB→1 MiB ratio is recorded, the two-second ceiling stays at 1 MiB on the named runner, and the record adds the CPU model (§6, §8, the Build section). The I9 row's "a quadratic mutant of `mask` reads RED" had no tracked check (a scratch copy measured once); `test_i9_a_quadratic_mask_reads_red` is now that check. D1 (research's QC of the test harness found `correct_fact` refusing an unknown edge id before the credential screen; dev confirmed it is a class, the served boundary's content-free pre-gates, and ruled to fix the wording rather than reorder). D1's first sentence read *"§4b runs first in every entry point: before any digest, length check, model call, log line or refusal that names an argument"*. It now says first before anything that reads a free-text argument's content, writes, or carries part of a value, and a new paragraph names the pre-gates that may precede §4b (capability, erasure, scope configuration, target presence by lookup id, a type or length check, a closed-vocabulary check) with their sites at `85d84928` (corrected: `remember`'s capability floor discards and never refuses). The build pins it in `tests/test_0055_d1_pregates.py`. **Prior:** **v0.5.5 — 2026-11-23: the owner's rulings on the build's I19 findings, first-hand to dev and relayed by dev: *"1. declare both destinations as a named exception / 2. declare them in the map / 3. fix it / 4. disclosure them / build review before release"*.** I19-F1: `maintain()`'s pool key, the scope's identity digest that map rows 8, 14 and 34 compute, is RETURNED and LOGGED; those rows become `declared_exception` in D3's form (§4b-ii D3). I19-F2: the three digest sites census F did not list are mapped, rows 37-39 (§4b-ii). Census F is kept as taken; research's census F addendum (evidence/census-F-addendum-2026-11-23.md) carries the new rows and the amended destinations, and evidence/digest_map.py reads both, refusing an addendum row or site that repeats census F, an amendment to a row census F does not hold, and a row amended twice. The map is 102 rows (101 components and the provider row P). I19-F3 to F5 stay disclosures, carried to the build review. I19-F6 is fixed (dev): every store refusal that quotes a stored free-text value (an invalidation reason, an episode's retired reason or kind, at the write and import sites, and the journal's reason) masks it before quoting it; the four reachable sites are RED without the fix (`test_i19_f6_a_store_refusal_masks_the_value_it_quotes`), and the three import sites sit behind §4h's screen and are masked as defence in depth; the implementation mutation table gains its mutant (the upsert's quote unmasked: exactly that cell fails, by assertion). The sweep now runs 131 entries over the 102 rows. The build review comes before release. **Prior:** **v0.5.4 — 2026-11-23: the build's three owed items closed, no design change.** I19's map-driven sweep runs every row of `evidence/digests.json` at the build (`tests/test_0055_i19_digest_sweep.py`); I9's figures ride in each CI lane's JUnit file; the implementation mutation table holds 21 product mutants RED (`specs/evidence/0055/implementation_mutants.py`). The sweep's departures from census F's map are listed in the `## Build` section as findings I19-F1 to I19-F6 for the build review: one undeclared destination (F1), three unmapped digest sites (F2), and every other departure stricter than its rule (F3-F5), with E1's scope (F6). **Prior:** **v0.5.3 — 2026-11-23: built, no design change.** The build is recorded in the new `## Build` section: the implemented invariant matrix, the scope of E1 at the library boundary, the import screen's placement at 0041 v16.5's pin, and what the build still owes before its review (I19's per-row sweep of the digest map, I9 on the named runner, RED demonstrations by mutation). **Prior:** **v0.5.2 — 2026-11-22: round 3's verdict folded (ACCEPT WITH AMENDMENTS; coordination `eec95f4`, body sha16 `4d136857a0482324`).** The design is frozen on I1–I20. **A1 (LOW):** the reference now reuses each scan's result, so it meets §4a's construction of at most five scans; v0.5.1's did two per pass, eight at the bound. scan_count.py asserts the count on four-pass completion and on the fallback, and holds v0.5.1's loop RED. Timing was re-run on the kept algorithm, and its scope is stated: T1's ratios at 32/128 KiB are not I9's 256 KiB/1 MiB, two-second gate on the named runner (§4a T1, §5, I9). Text idempotence is written `mask(mask(t)[0])[0] == mask(t)[0]` (§4a, I3). **A2 (LOW):** digest_map.py refuses a repeated row, site or component before building the map and asserts an exact bijection between census pairs and explicit rules. The whole-plan row's default `identifier_kept` (and row 17's default `screened`) are now explicit lists. digest_map_mutants.py holds the map GREEN, byte-identical, and eight mutants RED (§4b-ii D2, I19). **Fold notes:** I1's table count is 122; §4b-ii's 0039 line folds with adoption or build, with shaped controls; §4h verifies 0041 v16.5's adopted bytes at the build pin; the finder reports opaque residual digests as declared, unvouched domains (§4f); §9 lists the build review's artifacts. A new `## Review closure` section binds A1 and A2 to the banked verdict's digest, with their closure commands. `accepted` follows dev's executable closure of both, recorded there (PROCESS §4a). **Prior:** **v0.5.1 — 2026-11-22: dev's internal read of v0.5 folded (one BLOCKING item, and the placements it asked to be stated).** B1, R2-04's own class: the converting import's whole-file digest lives in the store-level `migration_op` table (no `user_id`; never erased, 0044 §4g-ii), so it survives `forget_user` inside the database. §4f's paragraph and matrix, §8 and the CHANGELOG sentence say so, and the other store-level tables are shown to hold nothing user-derived (census F D12, D13). Placements: `correct` applies the mask and the refusal before `graph.plan_correction`, so the plan, its `raw_request` and every supersession digest see the masked note (§4c-ii rule 1); §4h's screen sits after parsing and before the linkage snapshot, ahead of every digest over a file component. Carriers named: 0041 REPLACEs all three request-digest carriers, undo's registry row included; the receipt residual outlives a 0041 redaction of the prior. The diagnostics digest change is cross-spec, `0055/0039-masked-diagnostic-digests`, and 0039's transcripts stay byte-identical because their fixtures hold no shape. **Prior:** **v0.5 — 2026-11-22: round 2 (RETURN for four focused amendments) answered, finding by finding**, on research's stage-1 read (research `33a3d22d`) and dev's census F at `2040a789` (coordination `9abf5ca`). R2-02 (HIGH): §4b-ii D2 classifies every legacy-capable component of every digest, 98 in 36 sites, each with exactly one rule in `evidence/digests.json`. Request identities over a lookup id keep it as an identifier; the supersession receipt digest over a stored prior's free text is a named residual beside 0041's receipt domain; `correct` is refused or masked before its projection is hashed; §4h screens a file before any digest over it; the diagnostics digests are over masked provider text. I19 is bound to (component, destination) pairs. R2-01: `mask()` is bounded by construction (four passes, then the whole value withheld); v0.4's argument was false for every quote class, not only the curly quote. R2-03: a report counts the placeholders in the final output; every fixture has an exact expected report; the I8 oracle compares counts. R2-04: `forget_user` is scoped to the user's database rows; the host AuditLog's D3 digest is a named residual; the outward claims carry the whole snapshot set. The small corrections are folded. The owner's rulings stand; nothing in them is reopened. **Prior:** **v0.4.2 — 2026-11-22: two defects in research's own evidence, found by the round-2 package's self-scan; no design change.** (1) The reference model carried `pin` as a weak label, contrary to §4a's text, and with v0.4's JSON-key rule it withheld a commit sha (`"pin": "<sha>"`). The model now matches the text, and rows K45–K47 are added; the table is 118 rows. (2) The report checker's self-test printed a matched canary, so a committed output carried one assembled test token. The checker no longer quotes strings, and §6 says so. The corpora are unchanged (LoCoMo 0/5,882; specs and CHANGELOG 0/59,066). **Prior:** **v0.4.1 — 2026-11-22: dev's internal read of v0.4 folded (three BLOCKING items, three notes).** B1: MCP's refusal shape is unchanged (`refusal` and the existing names kept); only `detail` changes, to the formatter's text or nothing (§4g E1). B2: a backup whose identifiers carry a shape has a stated route, a plain import that refuses those records and their dependents; §8 states the limit, and §10 Q6's DECIDED text records that the flag's reach narrowed at v0.4 after the owner's ruling. B3: D3's lookup is scoped to the same `user_id` and the resolved origin, and is named as an existence oracle, acceptable because revocation is host-only (§4b-ii). N1: re-embedding cost (§5). N2: absorption's rewrite of a legacy note (§7). N3: E1 does not cover the SDK's own argument validation; E2 and I17 do (§4g). Dev's own nested-label fuzz (12,000 cases, three seeds, four layers): 0 failures, at most 3 passes. **Prior:** **v0.4 — 2026-11-22: round 1 (RETURN for amendment, 8 findings) answered, finding by finding**, on research's stage-1 read and dev's five censuses at `2040a789` (coordination `1e519b1`, `5bfc69b`, `e42b05f`, `47997b5`). R1-01: §4c-ii, the derived-write rule (composed text withheld; model sites screened; a closed snapshot-exception list; I11 names the rule; I16). R1-02: §4g's outward-error rule at every boundary (E1 one formatter, E2 no input echo in validation errors, E3 the diagnostics log) and per-report ordinal locators; rowids rejected as unstable (I17). R1-03: §4f's field-level action/residual matrix, a second scan after acting, parent mapping for replies and journal rows, `forget_user` as the total remedy, and §10 Q7 for the identity contracts (I18). R1-04: `mask()` repeats until inert, bounded at four passes, with the argument and the measurements (§4a, I3). R1-05: `record_procedure` keeps its `str`, a `record_procedure_report` twin carries the report, library refusal raises `CredentialRefused` (§4g, I20). R1-06: §6 says which evidence is executed now and which is planned; I8 by schema over the whole result; the runners exit nonzero; a machine-readable invariants file. R1-07: §4b-ii, digests and identities (D1 order, D2 a per-digest rule, D3 revoking a credential-shaped legacy source, D4 `user_id`'s scope, with import's exception; I19). R1-08: §8's release sentence scoped with its exceptions beside it; query and embedder egress named; time stated as measured. Also: the label grammar covers structured configuration (JSON and dict keys, prefixed environment variables, XML), and a quoted value is withheld quote to quote; the table is 115 rows. The owner's three rulings stand unchanged; the reviewer's verdict says so. **Prior:** **v0.3.2 — 2026-11-22: §6's literal-credential claim stated at its true width**, from dev's pre-seal scan of the round-1 package (`credential_shapes.scan` over every file: 23 spans in 5 files). v0.3.1 said no literal credential appeared in the spec, the table or a commit. True of structural tokens, which are all assembled at run time; not of the labelled rows, which use well-known dummy values literally, nor of one test-minted preview token in census 2's output. §6 now states the property that holds and points to the package's self-scan. No behaviour, invariant or ruling changes. **Prior:** **v0.3.1 — 2026-11-22: §10 Q1's scope, ruled.** The owner, first-hand in the dev session (as dev relays it): *"Include remember and record_procedure (Recommended)"*. §4g and I15 cover all nine `*_impl` that strip `provenance_raises_discarded`: the seven trust tools, plus `remember_impl` and `record_procedure_impl` (`_OPERATOR_ONLY`, `_PROCEDURE_OPERATOR_ONLY`), so 0031 §10 Q4 closes fully. v0.3 had stated this as research's reading, for dev to confirm; it is now a ruling. A respin before the package is sealed; nothing else changes. **Prior:** **v0.3 — 2026-11-22: the owner's two rulings folded, first-hand in the dev session as dev relays them.** §10 Q1, *"Yes, same build (Recommended)"*: the trust tools' `*_impl` record `provenance_raises_discarded` to the same AuditLog surface, and 0031 §10 Q4 closes in that build, with a 0031 text change riding with it (§4g, I15). §10 Q6, *"Refuse unless a flag is passed (Recommended)"*: a restore that carries credentials refuses unless `withhold_credentials=True` is passed, as v0.2 has it (§4h). Both questions move from open to decided; nothing else changes. Dev signed off v0.2 internally (no new items). **Prior:** **v0.2 — 2026-11-22: dev's internal review folded (three BLOCKING items, B1–B3, and notes N1–N2).** B1: §4e's read backstop is scoped to stored record text; a store-minted value in a result (0031's `tt1` preview token, ids, digests, receipts) is not masked, and `forget_everything_confirm`'s `preview_token` is never screened (I14, preview then confirm under every screen). B2: `record_outcome`'s `corrected_value` is free text written into an outcome episode's summary, so it is withheld (§4b). B3: a restore of a backup that carries credentials gets a named operator path, `withhold_credentials=True`, which withholds and lists the record ids in the receipt; the default still refuses (§4h, §8, §10 Q6). N1: §2c-ii A5 is now a signature census of every public `Memory` parameter that admits a string (77 rows, 23 methods), each classed; it found three more free-text fields (`dispute`'s and `correct`'s `actor`, `remember`'s `event_type`) and `undo_restoration`'s `correlation_id`, all now refused as identifiers. N2: I12's RED includes the degrade path over a provider error that echoes the prompt. §10 Q3 is closed by dev's search (the description lives only in `src/veracium/mcp_server.py`); Q1 has dev's agreement and is the owner's. **Prior:** **v0.1 — 2026-11-22: the first draft**, on the owner's ruling of 2026-10-29 (Dev-queue row 🔑, *"Spec it, after round 4 (Recommended)"*) and his go-ahead of 2026-11-22, first-hand in the dev session as dev relays it (*"I agree"*, to dev's recommendation to make this next). It answers dev's five questions: (1) every write path, by reach; (2) mixed messages, and what a report may carry; (3) the pattern set, its false-positive budget and an executed adversarial table; (4) a backstop for rows already stored; (5) one operator surface, shared with 0031 §10 Q4. Built at veracium `2040a789`. |
| **Status** | *narrative only — the canonical state is the `Spec-Status:` line at the top* |
| **Internal reviewers** | research (author) · dev (asked the five questions; internal review of v0.1, three BLOCKING and two notes, folded at v0.2; signed off v0.2 with nothing new) |
| **External review** | required: the change touches guarded files (D2: `src/veracium/ingest.py`, `src/veracium/mcp_server.py`, `src/veracium/store/sqlite.py`, `src/veracium/portability.py`, `src/veracium/__init__.py`) |
| **Decision + date** | **ACCEPTED 2026-11-22**, the owner, first-hand in the dev session: *"Adopt as accepted (Recommended)"* (design accepted with amendments at external round 3, banked coordination `eec95f4`; the amendments A1 and A2 closed with executable evidence by dev, § Review closure). The owner's rulings, 2026-11-22, first-hand in the dev session (as dev relays them): §10 Q1 *"Yes, same build (Recommended)"*, and its scope, *"Include remember and record_procedure (Recommended)"*; §10 Q6 *"Refuse unless a flag is passed (Recommended)"*. External review, round 3 (2026-11-22; banked at coordination `eec95f4`): **ACCEPT WITH AMENDMENTS**, A1 and A2 (both LOW), folded at v0.5.2. The line becomes `accepted` once dev has recorded executable closure of both (the verdict's words; PROCESS §4a) |
| **Path** | full, by D2 (the list above, derived from `specs/check_spec_reference.py`'s `GUARDED` at `2040a789`) |

**Spec-Requires:** 0006 and 0041's identity contracts (provenance identifiers are kept by redaction; §4f, §10 Q7), 0037 (the `record_procedure` `str` contract and its new twin, §4g), 0041 (targeted redaction: the remedy for rows already stored, and its marker, which this spec must
not reuse), 0029 (the edge journal: `edge_event.state` keeps every version of an edge), 0031 (the served tools and
§10 Q4's open operator surface), 0023 (the AuditLog's "audit-only facts"), 0039 (the degrade callback's `_len_sha16`).

---

## 1. Problem and motivation

**Veracium stores credentials verbatim today.** Research's adoption probe (research `57a8672f`, the adoption-probes
note of 2026-10-29, section "#2 Secrets") sent one message holding an AWS key id (AWS's documented example), a
password and a GitHub-style token, plus "I deploy every Friday". **Under `none`, all three secrets were stored
verbatim**, each as a `third_party_claim` edge (e.g. `staging database password is <the password>`), and a scan of
every text cell of every table found each in `edges` and in `edge_event`, one row each. Under `direct` nothing was
stored, **by the extractor's own judgement**: its episode summary said the credentials "should not be retained", and
it also dropped the one ordinary fact. No code in the product handles secrets (§2c-ii, A9).

Three further facts make the defect wider than "a row in `edges`":
- **The raw text reaches a model provider before any write.** `ingest.py` sends the caller's `event_text` to the
  host's `distill` model (`src/veracium/ingest.py`, the `role="distill"` call, line 360 at `2040a789`) before its first
  write at line 394. A filter at the store is too late for this egress.
- **Stored text goes out again.** The answer gate, the wiki compile and consolidation send stored facts and summaries
  to providers, and the embedder sends edge text (§2c-ii, A7). A credential stored once is re-sent on every such read.
- **History keeps it.** `edge_event.state` holds every version of an edge (0029), so an edit of the visible row does
  not remove the credential.

**If we do nothing:** every store that has ever seen a pasted key keeps it at rest, in history, in exports and in
backups, and re-sends it to model providers on later reads. The product's own position (provenance-aware memory that
an operator can trust) is contradicted by a stored AWS key. The only current defence is a model's discretion, which
the probe showed to be both unreliable as a control and lossy (it dropped "I deploy every Friday").

**Alternatives rejected:**
- **Ask the model to withhold secrets (a prompt rule).** That is today's accidental behaviour under `direct`, and the
  row's ruling excludes it: *no model judgement*. A prompt is not a control, the probe shows it over-drops, and under
  `none` it does not happen at all.
- **An unlabelled high-entropy detector** (flag any long random-looking token). Our own store is full of
  high-entropy values that must be kept: 64-hex source digests, 32-hex uuids, base64 digests, `e-`/`ep-`/`ev-` ids,
  and the commit shas users quote (§4a, near-miss rows K1–K5, K29–K32). Any entropy threshold that catches a 40-char
  random secret also catches a base64 sha256. The boundary is not deterministic in the sense the row asks for (a
  reviewer cannot predict a verdict from the rule), so it is left out, and §8 states the residual (X5).
- **Refuse the whole write when any credential shape appears.** Simple, but it repeats the model's over-drop: one
  pasted key in a long transcript loses every fact in it. Kept only where masking is unsafe (identifier fields, §4b;
  a restore import, §4h; the store guard, §4d).
- **Encrypt matched spans at rest instead of dropping them.** It keeps a credential the product has no use for and
  adds key management. Withholding is cheaper and stronger.
- **Scrub existing stores with a schema migration.** Rewriting history in a migration is irreversible, runs without
  the operator's eyes on what is removed, and would have to re-derive digests over rewritten rows. 0041 redaction
  already does the one-record version properly; §4f gives the operator a finder that feeds it.

---

## 2. Field contracts touched

| field | read / written | its **documented** contract | every other consumer | does this change preserve the contract? |
|---|---|---|---|---|
| `edges.subject`/`object`/`json.note`, `episodes.json.summary`, `replies.text` | written | the stored statement, as distilled or as supplied | recall render, find_facts, why, export, embedder, compile, gate, consolidation | **Changed, additively:** a withheld span is replaced by `[credential withheld: <class>]` (§4a). The text is no longer byte-equal to the caller's input when a span is withheld, and the result's new key says so. |
| result dicts of `remember`, `correct`, `dispute`, `reply`, `record_outcome`, `import_memory` (library); `record_procedure_report` (new library twin; `record_procedure` itself keeps returning `str`, §4g, R1-05); and their MCP / adapter results | new key | — | the 0053 conformance suite (compares served results), MCP clients | **New key `credentials_withheld`** (§4g), present only when non-empty, so every existing result without a withheld span is byte-identical. |
| `AuditLog` lines | new event `credential_withheld`, `credential_refused` | "content-free counters" (`src/veracium/audit.py`, its module docstring) | the host that attached the log | Preserved: the events carry class names and counts only (§4g). |
| `edge_event.state` | written (by the edge write) | every version of the edge (0029) | why, history readers, 0041 | Preserved. A new write's journal event records the written (withheld) text. A transition over a LEGACY record snapshots the row as stored, a legacy credential included: §4c-ii rule 3's declared exception (v0.5, round 2's R2-04; v0.4 said the journal never sees a credential, which the snapshot rule made false). 0041's tombstone of the parent removes it (§4f). |

**Consumer enumeration for the build** (commands, not recall; run at the implementation commit and recorded in the
adoption): `grep -rn '"remember"\|remember_report\|remember_impl' src tests` for the result-dict consumers;
`grep -rn 'credential withheld' src tests` must be empty before the build (the placeholder is new text);
`grep -rn 'def _record' src` and its callers for the AuditLog events.

---

## 2c. Untrusted inputs — REQUIRED, blocking

| uncontrolled input | empty | malformed | unrecognised | adversarial | **invariant that pins it** |
|---|---|---|---|---|---|
| caller free text: `remember`'s `event_text`, `record_procedure`'s `summary` and `note`, `dispute`'s `reason`, `reply`'s `text` | screened, nothing withheld, unchanged | any string is screened. **A value that is neither `None` nor a `str` is refused by type before any consumer** (`ArgumentTypeRefused`; v0.5.8, round 4's R4-01; §4b's *Type first*). To v0.5.7 this cell said non-strings were refused "by the existing type checks": true of a bytes `event_text` (a `TypeError` before the provider), never measured for identifiers, and false for a bytes `event_type` or `evidence_ref`, which skipped the screen and were stored as text | text with no credential shape: stored byte for byte (34 near-miss rows) | invisible characters inside a token (N1, N2), full-width forms (N3, L12), wrapping punctuation (N4, N5), a quoted multi-word passphrase (L16, L17), a value with a tail past the pattern (L18), a payload built to make the recogniser super-linear (§4a, T1) | **I1** (every positive row withheld, no secret byte survives), **I2** (every near-miss stored unchanged), **I3** (the output is inert), **I9** (linear time) |
| caller identifier fields: `source_id`, `evidence_ref`, `context_ref`, `correlation_id`, `reply`'s `target`, `correct`'s `corrected_value` (§4b's table) | unchanged | as above | stored unchanged | a webhook URL or a connection string with a password used as a `source_id` (S7, S19 shapes) | **I4**: refused whole with `credential_refused` naming the field and class; nothing written |
| extractor (`distill`) output, its retry, consolidation output, wiki text | nothing to screen | existing parse refusals | screened like caller text | a model that reassembles a withheld span from context, or hallucinates a credential shape | **I5**: model output is screened before it is parsed into a write; a triple carrying a shape is dropped and counted as `credential_refused` (source `model_output`); a summary is masked |
| an import file (`import_memory`, CLI `import`) | existing import refusals | existing import refusals | screened per record | a file written by an older version, carrying credentials stored before this spec | **I6**: a plain import masks per field and reports; a `restore=True` import refuses the whole import, naming the record ids (never values), because a restore promises the source's bytes |
| rows already stored (written before this spec) | — | — | — | legacy credentials in `edges`, `episodes`, `edge_event`, `replies` | **I7** (read backstop: masked on every model-bound and tool-bound read) and **I8** (the finder reports class and id, never value) |
| host configuration | **none added**: there is no switch that turns the filter off (§10 Q2) | — | — | — | I1 holds under every capability (`none`, `direct`) and every surface (library, MCP, adapters, CLI): **I10** |
| `VERACIUM_AUDIT_LOG` (new, the stock server's path for an AuditLog) | unset: no log, as today | unwritable path: the AuditLog's existing behaviour; the filter does not depend on the log | — | a path the operator does not own | the filter's withholding never depends on the log (**I1** runs with no log attached) |
| the stored text a model provider receives (egress) | — | — | — | a legacy credential re-sent on a read | **I7** |
| text composed from stored records (v0.4, R1-01) | — | — | — | a legacy credential copied into a new summary, a rewritten note or a replacement edge | **I16** (§4c-ii: composed text withheld; snapshot exceptions an exact set) |
| outward errors, reports and ids (v0.4, R1-02) | — | invalid enum, date or lookup input | — | a value echoed by a validation error, an SDK error, an adapter or a log; a credential-shaped record id printed in a report | **I17** (§4g E1–E3; ordinal locators) |
| digests over caller input (v0.4, R1-07) | — | — | — | a credential hashed before any screen and persisted, returned or logged | **I19** (§4b-ii D1–D3) |

### 2c-ii. Assertions about reach — REQUIRED

All commands run on a `git archive` export of veracium `2040a789`, from the export's root; research's census
scripts and outputs are committed beside this candidate (research evidence directory
evidence-0055-credential-shapes, `census1/` and `census2/`).

| # | assertion | command that establishes it | result |
|---|---|---|---|
| A1 | No SQL write exists outside `src/veracium/store/` | `python3 -I census1/sqlwrites.py <export>` (an AST scan of string constants for INSERT/UPDATE/DELETE/REPLACE) | 58 writing function scopes, all in `store/`, plus two prose false hits (`embed_backfill`, `procedures.py`), read and discounted |
| A2 | Every `edges` row write passes one function | `grep -n '_journal_edge_write\|def _write_edge_row\|def _upsert_edge_row' src/veracium/store/sqlite.py` | `_journal_edge_write` is "THE emission choke point (specs/0029 §4b): called by every `edges` writer"; reached from `:385` and `:574`; 7 writer call sites, import (`:2961`) and redaction (`:4045`) among them |
| A3 | Episodes and replies have no single write point | `python3 -I census1/reach_store.py <export>` | episode writers: `add_episode`, `append_outcome_if_head`, `write_consolidation_output_if_current`, `confirm_edge`'s own INSERT, `commit_outcome_import_plan`'s own INSERTs, migrations |
| A4 | The store's public writers are already inventoried in CI | `grep -n 'WRITERS = {\|def test_every_public_store_method_is_classed' tests/test_rii_r2_01_writer_inventory.py`, and the dict's size by `ast` (the assignment's `len(value.keys)`) | `WRITERS` at line 365 with 23 entries; the test at line 410 asserts every public `SqliteStore` method is a writer or a read, so a new one fails CI until classed |
| A5 | Every public `Memory` parameter that admits a string is classed (v0.2; v0.1 read entry points by name) | `python3 -I sig/memory_text_params.py <export>` (an `ast` read of every public method's parameters whose annotation admits `str`, or has none; `user_id` excluded) | 77 rows over 23 methods, each classed in §4b's second table (at the round-5 pin: 83 rows over 24 methods, I20's twin adding six; §4b's *Type first*); the screened ones are on `remember`, `record_procedure`, `correct`, `dispute`, `confirm`, `reply`, `record_outcome`, `undo_restoration`, plus `import_memory`'s file. v0.1's name-level graph (`census1/reach_api.py`) is kept as the record |
| A6 | Of the 13 MCP tools, four carry new caller text | `awk '/def build_server/{f=1} f' src/veracium/mcp_server.py \| grep -A2 '\.tool('` | remember, record_procedure, correct_fact, dispute_fact; `forget_fact` writes only 0041's marker |
| A7 | Caller text reaches a model provider before any write; stored text reaches providers on reads | `grep -rn 'role="' src/veracium` and `grep -n 'def embedded_text' src/veracium/semantic.py` | `ingest.py:360` (`distill`) and `:595` (`distill-retry`), before the first write at :394; `gate.py:228`, `compile.py:353`, `lifecycle.py:212` over stored text; the embedder's input is `embedded_text(edge)` (`semantic.py:42`) |
| A8 | The 0053 adapters reach the same writers as MCP | `grep -n '_impl(' src/veracium/adapters/_surface.py` | every served tool calls the `*_impl` the MCP tool calls |
| A9 | No secret handling exists in the product | `grep -rniIE 'secret\|credential\|password\|api[_-]?key\|AKIA\|ghp_' src/veracium --include=*.py` | 13 lines: usage text naming `ANTHROPIC_API_KEY`, the stdlib `secrets` module, "secretary" in a lexicon, and prose that Veracium owns no credentials; no detection or masking |
| A10 | No persisted operator counter exists; the stock server attaches no AuditLog | `grep -n 'AuditLog\|audit=' src/veracium/mcp_server.py src/veracium/cli.py` | none; `Memory._record` (`src/veracium/__init__.py:555`) writes to `self.audit` only when the host attached one |
| A11 | `provenance_raises_discarded` never reaches the AuditLog | `grep -n 'provenance_raises_discarded' src/veracium/mcp_server.py` | computed in `remember_report` (`:198`) after `Memory.remember` has recorded |
| A12 | The diagnostics reporter's local error log can hold caller text | `sed -n '175,186p' src/veracium/diagnostics.py` and `grep -n 'def redact' -A5 src/veracium/diagnostics.py` | `record_error` logs the context and the full traceback locally; `redact()` replaces emails and number patterns only |
| A13 | Hashes over caller text exist at rest | `grep -n 'def reply_request_digest' src/veracium/schema.py` and `grep -rn 'content_digest' src/veracium --include=*.py \| head -3` | `reply_request_digest(user_id, edge_id, kind, target, text)` (`schema.py:189`) feeds `replies.request_digest` and `request_registry`; `semantic.content_digest(edge)` feeds the embedding row (`__init__.py:765`) |

**Round 1's census, v0.4.** Five more read-only censuses by dev at `2040a789`, each row with its command and file:line, committed in the coordination repository under `dev-handoff/0055-r1-census/`:

| # | census | what it establishes | coordination |
|---|---|---|---|
| A14 | A, composition | 19 writers copy stored text into new rows (5 free text, 2 model-mediated, 12 snapshots) and 12 sites rewrite a row in place; probes probe_a, probe_b | `1e519b1` |
| A15 | B, echo | 55 outward paths carry caller input and 50 echo the raw value; b-probes with a canary | `5bfc69b` |
| A16 | C, identity hashing | the digests over caller input, where each is persisted, returned or logged, and where it runs relative to any screen; `user_id`'s whole path; probes probe_c, probe_c2 | `e42b05f` |
| A17 | D, returns | only `record_procedure` returns a non-dict, and its `str` is contract | `47997b5` |
| A18 | E, remedy domain | what 0041 treats and keeps, reply and journal parent mapping, rowid instability, what `forget_user` removes | `47997b5` |
| A19 | F, every digest by component (round 2's R2-02) | 33 primitive hash sites and a closed transitive sweep of 129 call sites; 429 component rows over 80 digest sites, each with its source class and destinations; 98 legacy-capable components in 36 sites, each given one rule in `evidence/digests.json`; witnesses W1–W6 (W3 the control) | `9abf5ca` |

**What A1–A13 do not show.** The reach census is name-level (A5 over-approximates; it cannot under-approximate a
direct call, but a call through a stored callable would be missed). The build closes that gap mechanically: I4 and I11
bind the screen to A4's inventory, so a writer added later fails CI until it is classed.

---

## 3. Trust-class matrix — REQUIRED, blocking

The operation is unary and content-level: it withholds spans before a write, or refuses the write. It reads no trust
class and sets none. The classes, from the enums at `2040a789`
(`python3 -I -c "import sys; sys.path.insert(0,'src'); from veracium.schema import EvidenceAuthor, Disclosure; print([m.value for m in EvidenceAuthor], [m.value for m in Disclosure])"`),
are each answered the same way, which is the point: **the rule holds for every author, every disclosure, every
capability.**

| state before | event | state after |
|---|---|---|
| caller text with a shape, any author (user, third party, model-derived), any disclosure, quarantined or not, `use_only` or not | ingress screen | the same write with the span withheld; author, disclosure, quarantine and `use_only` exactly as they would have been for the withheld text |
| an identifier field with a shape | ingress screen | no write at all; `credential_refused` |
| a model output with a shape | model-output screen | the triple is dropped (no edge); a summary is masked |
| a stored row with a shape (legacy) | any read toward a model or a tool result | the row is unchanged at rest; the read sees it masked |

- **Can a user-asserted fact become non-assertable?** Only its withheld span changes; the fact's class is computed as
  before on the withheld text. A fact whose whole object was a credential is stored as `… [credential withheld: …]`
  with the same class it would have had.
- **Can non-user content gain authority?** No. The screen sets no class and no confidence.
- **Can it clear `needs_confirmation`?** No.
- **Does it merge, drop or overwrite provenance?** It drops a model triple that carries a shape (I5). That triple's
  provenance is lost with it, by design; the drop is counted and audited.
- **Write-time or maintain-time?** Write-time for the screen; read-time for the backstop, which writes nothing.

---

## 3b. Authorization and scope — *full specs only*

- No user, tenant or scope boundary is crossed. The screen sees only the call's own text.
- Nothing becomes visible to anyone who could not see it before. The backstop (§4e) makes less visible.
- The `credentials_withheld` report reaches the same principal the result reaches. It carries class names and counts,
  which the caller's own text already determines, so it discloses nothing the caller did not send.
- The AuditLog events reach the host that attached the log, as every AuditLog event does today.

---

## 4. Behaviour

### 4a. The recogniser

**Deterministic:** regular expressions over a normalised view of the text, no model, no network, no state. A reference
model is committed beside this candidate (credential_shapes in research's evidence directory) and is the oracle for
the build's tests, not a module to copy blind.

**Normalisation (view only; the stored text is never normalised).** Per character: Unicode format characters
(category `Cf`, which includes U+200B–U+200D, U+2060, U+FEFF) and U+00AD are dropped; every other character is NFKC'd.
The view keeps a map back to original offsets, so a withheld span always covers the original characters, invisible
ones included.

**Two kinds of class.**

*Structural* (the token's own shape names it). The v1 set, by class name:
`aws_access_key_id`, `github_token`, `gitlab_token`, `slack_token`, `slack_webhook`, `stripe_key`, `anthropic_key`,
`openai_key`, `google_api_key`, `google_oauth_secret`, `huggingface_token`, `npm_token`, `pypi_token`, `sendgrid_key`,
`digitalocean_token`, `azure_storage_key`, `jwt` (three segments, the first two starting `eyJ`), `private_key_block`
(PEM armour naming `PRIVATE KEY`, through its END line or, if truncated, to the end of the text),
`url_userinfo_password` (`scheme://user:password@host`), `auth_header` (`Authorization: Basic|Bearer|Token …`),
`bearer_token`, and **`veracium_preview_token`** (our own: `tt1.eyJ….<mac>`, the bearer that authorises a whole-user
erase, 0031 §4f). The exact expressions are in the reference model; every unbounded repetition that could run over a
long input is bounded (T1).

**The token boundary (v0.5.7; the owner's ruling, relayed by dev, *"Fix the recogniser (Recommended)"*).** A
structural pattern may not start immediately after an ASCII letter or digit (`(?<![A-Za-z0-9])`), and the five that
end on a boundary (`aws_access_key_id`, both `github_token` forms, `npm_token`, `digitalocean_token`) may not end
immediately before one (`(?![A-Za-z0-9])`). Every other character is a boundary: `_`, punctuation, white space, and
every non-ASCII character. To v0.5.6 the boundary was a regular-expression word boundary, for which `_` and every
Unicode letter are word characters, so a token glued by `_` (a model-emitted relation `has_key_…`, an environment key
`HTTP_AUTHORIZATION: Basic …`) or written against CJK text, which has no spaces, was not recognised (rows G1–G18,
each stored with its token by v0.5.6's patterns). A token glued to an ASCII letter or digit is still part of a longer
word and is not recognised (X7, X8: a stated limit; K55 shows why the boundary stays, `sk-` inside `risk-…`). The
labelled rule's own placement (a label may follow `_` or `-`, below) and the PIN rule are unchanged (§10 Q8).

*Labelled* (a credential-naming label, a separator, a value).
- **Strong labels** (the word has no ordinary sense): password, passwd, passphrase, passcode, pwd, api key, access key
  (id), secret key, client secret, access/auth/refresh token, private key, aws secret access key, and contraseña,
  mot de passe, Passwort, senha, パスワード, 密码. The value is withheld unless it is a stop word ("expired", "in",
  "the same", …), a masked or template value (`********`, `<redacted>`, `${X}`, `$X`, `[…]`), or a code expression
  (`token = m.group(0)`).
- **Weak labels** (ordinary words with a credential sense): secret, token. *(v0.4.2: research's reference model also carried `pin` as a weak label, contrary to this text, until the round-2 package's own self-scan found `"pin": "<commit sha>"` withheld as a generated value. The model now matches the text, and K45–K47 pin commit shas as near-misses.)* The value must look generated: at least 8
  characters with three of {upper, lower, digit, symbol}, or 12+ with a digit; one token, no spaces.
- **PIN:** upper-case `PIN`, or `pin` after an owner word (my, card, bank, ATM, phone, …), followed by 4–8 digits. A
  bare lower-case "pin" is this project's own word for a commit (the corpus run found 52 hits of "capture at the pin:
  7351 passed" in `specs/` before this narrowing, K35).
- **Separators:** is, is now, was, `=`, `:`, the full-width colon, `->`, `=>`. **Values:** a double- or single-quoted
  string up to 200 characters (so a multi-word passphrase is withheld whole), or one unquoted token.

**Where a label may stand (v0.4, round 1's answer to Q2).** A label may:
- close its own quote, so JSON and dict keys are labels (`{"password": "…"}`, L19, L20, L23);
- follow `_` or `-`, so a prefixed environment variable is a label (`DB_PASSWORD=…`, L21);
- be followed directly by `>`, so an XML element is a label (`<password>…`, L22).

A label may not be followed by more of a word (`password_policy`, K40), nor stand in a path (`/etc/passwd`, K44: the
corpus run found one). Config literals (`true`, `false`, `null`, `yes`, `no`, `on`, `off`, `enabled`, `disabled`) are
stop words (K39, K43). These were limits at v0.3.2, and the grammar now covers them: a v0.3.2-grammar mutant goes RED
on these rows.

**Widening.** An unquoted span, except a PEM block, is widened to the whitespace-delimited token it sits in, so a
partial match never leaves a tail (L18: a value with a `;` inside). **A quoted value is withheld from quote to quote,
inclusive, and not widened (v0.4):** its quotes bound it, and widening took a JSON object's closing brace with it.
Token boundaries are computed once per text; widening is by bisection.

**One class per span.** Overlapping matches merge; the span takes the first structural class in list order, else
`labelled_password`, `labelled_pin`, `labelled_secret`.

**The placeholder** is `[credential withheld: <class>]`. It is **not** 0041's marker (0041 INV-11 forbids ordinary
writes from introducing that). A value beginning with `[` never satisfies a label, and no structural pattern spans the
placeholder's brackets and spaces.

**The completed output is inert (v0.4, round 1's R1-04).** At v0.3.2 one pass of masking was taken to be inert. Round 1
showed it is not. Masking a token inside a long quoted value can shorten that value back under the labelled rule's
200-character bound, so a second scan finds the enclosing label (`'password: "' + "a " * 79 + token + ' end"'`, and at
80). So `mask()` repeats until `scan()` finds nothing.

**The bound is a construction (v0.5, round 2's R2-01).** v0.4 argued that double-quoted values cannot nest, so at most
three passes were needed. That was false, and no argument about the quote grammar can replace it. A pass withholds a
quoted value quote to quote, so the value one layer out no longer contains the inner quotes. Every quote class
therefore nests to any depth by containment, one layer per pass. Round 2's reviewer showed it with the opening curly
quote; research's depth_family.py shows it for every opener/closer pairing and for alternating classes. Excluding
U+201C from the double-quoted body was tried and measured, and did not remove the nesting, so the grammar is unchanged.
So:
- **`mask()` runs at most `MAX_PASSES = 4` passes.** If the text is still not inert after them, the **whole value** is
  withheld as one placeholder of class `unmaskable_text`.
- **It always returns and never raises.** Its output is always inert: the fallback placeholder is inert, which is
  asserted. Its work is at most five scans of the value: one scan, then one after each pass. Each scan's result is
  used twice, as the check that the previous pass left the text inert and as the findings the next pass withholds.
  So a completed mask does passes + 1 scans (five at a four-pass completion), and a fallback does five. *(v0.5.2,
  round 3's A1: v0.5.1's reference scanned inside each pass and again before the next, two scans per pass and eight
  at the bound. evidence/scan_count.py counts the scans of every table row and of the curly family at depths 0–40.
  It asserts the count on four-pass completion and on the fallback, and holds v0.5.1's loop RED.)*
- **There is no refusal outcome for free text.** The fallback is a withholding, reported like any other (§4g), at
  every screen alike:
  - at ingress, the field is stored as the placeholder;
  - at the model-output screen, a triple carrying a shape is dropped as before, and a summary is withheld whole;
  - in a derived write (§4c-ii), the composed text is withheld whole;
  - at the read backstop (§4e), the field is returned withheld whole.

  An identifier is never masked (§4b), so it is unaffected.
- **Measured:**
  - on ordinary text the repetition needs at most 3 passes: rows C1–C17, and the seeded compositions, which from v0.5
    draw every accepted delimiter pairing;
  - a labelled value nested four or more deep takes the fallback: row D4, and depth_family.py at depths 4–12;
  - a placeholder can also be *longer* than its value, so a value can grow over the bound instead (C14). Then only the
    inner span is withheld, and the output is still inert.

`mask(mask(t)[0])[0] == mask(t)[0]` and `scan(mask(t)[0]) == []` hold for every row and every family depth (I3). The
contract is on the text: a second call's report is empty by design, so the pair is not idempotent and is not the
contract (v0.5.2, round 3's A1). T1 below is re-measured on v0.5.2's construction, with the four-pass and fallback
worst cases included.

**What a report counts (v0.5, round 2's R2-03).** A report counts the placeholders `mask()` wrote that are in its
FINAL output, by class:
- a span swallowed by a later pass is not counted again (row C5: one `labelled_password`, not that plus the token's
  class);
- spans merged into one are one placeholder, under the merged span's class;
- a fallback is `{"unmaskable_text": 1}`;
- a placeholder already present in the caller's text is not one `mask()` wrote, and is never counted.

So every fixture has one exact expected report, written from its text (`vectors.EXPECTED_REPORT`), and the I8 oracle
compares counts with it.

**Versioned.** The set carries `CREDENTIAL_SHAPES_VERSION = 2` (v0.5.7; 1 to v0.5.6), recorded in every audit event, so
an operator can tell which rule set screened a write. Adding a class, or changing what a class matches, is a spec change
(a new row in §4a and in the table). From 2 the token boundary above is the rule: a write screened under 1 may hold a
token glued by `_`. The read backstop (§4e) masks it on every read with the current recogniser, and the finder (§4f)
reports it.

**T1, time, as measured (not proved).** The reference model was measured on adversarial inputs at 32 KiB and 128 KiB (research's
redos probe, its committed output, which records the box's load; from v0.5 the median of three timings per size, and
the revised construction's four-pass and fallback cases): every named case takes 3.5–4.3× as long at 4× the size on
v0.5.2's run (`evidence/out/redos.json` records the sizes, the algorithm, the interpreter and the load). **Scope (v0.5.2,
round 3's A1):** these are ratios of the reference model on research's shared host, at 32 and 128 KiB. They are
**not** I9's gate, which times the build's implementation at 256 KiB, 1 MiB and 4 MiB (v0.5.6) against the named CI
runner's two-second ceiling at 1 MiB. redos.py checks only the ratio, so it exits 0 whatever the absolute times. For information
only, at I9's sizes on the same host (`evidence/out/redos_gate_sizes.json`, 256 KiB / 1 MiB): four-pass completion
0.785 s / 3.109 s (ratio 4.0), fallback 0.874 s / 3.699 s (ratio 4.2). Round 3's reviewer measured v0.5.1's
eight-scan reference on its host at 1.673 s / 8.356 s and 1.735 s / 9.277 s (ratios 5.0 and 5.3). Every one of these
is over two seconds at 1 MiB: the reference model is not the build, and neither host is the CI runner. **Two quadratic defects were found and fixed in the
reference model by this probe** and are the reason I9 exists: widening walked the token once per finding (repeated
JWT-shaped segments: 14.7× per 4×), and the URL rule's unbounded scheme rescanned long dotted runs (10.3× per 4×; the
scheme is now at most 32 characters). **Re-run at v0.5.7** (`evidence/out/v057/redos.out`, `redos.json`) with two new
named inputs for the token boundary, which lets a prefix after `_` start a match: `glued_short` (`_hf_` and 33
characters, each unit a start that fails short) and `glued_body_run` (`_sk-`, whose body class takes the rest of the
run). Every case 3.9–4.2×, the two new ones 4.0× and 3.9×.

### 4b. The ingress screen (before any model call and any write)

At the top of each library entry point that takes new caller text (A5), before anything else reads the text:

| entry point (surfaces) | field | kind | on a match |
|---|---|---|---|
| `remember` (MCP, adapters, CLI `remember`) | `event_text` | free text | **withhold**, then proceed (the extractor sees the withheld text) |
| `record_procedure` (MCP, adapters) | `summary`, `note` | free text | withhold |
| `dispute` (MCP `dispute_fact`, adapters) | `reason` | free text | withhold |
| `reply` (library) | `text` | free text | withhold (before `request_digest` is computed, A13) |
| `record_outcome` (library) | `corrected_value` | free text: it is written only into the outcome episode's summary, " (true value: …)" (`src/veracium/__init__.py:2342`), and joins nothing | withhold |
| `correct` (MCP `correct_fact`, adapters) | `corrected_value` | identifier (it becomes the edge's object verbatim) | **refuse** (`credential_refused`) |
| every entry point that takes them: `remember`, `record_procedure`, `correct`, `dispute`, `confirm`, `reply`, `record_outcome`, `undo_restoration` | `source_id`, `evidence_ref`, `context_ref`, `correlation_id`, `target` | identifier | refuse |
| `dispute`, `correct` | `actor` (a free string, written as "(actor) …" into the episode summary; the MCP tools fix it to the user, 0031 §4f) | identifier (a label, compared in audit) | refuse |
| `remember` | `event_type` (a free string passed to ingest) | identifier | refuse |
| `import_memory` (library, CLI `import`) | every text field of every record | per §4h | per §4h |

**Type first (v0.5.8, round 4's R4-01).** The screen reads `str` values, so a type check comes before it. Every argument the screen takes, identifier or free text, that is neither `None` nor a `str` is refused before any consumer, with `ArgumentTypeRefused`. That is an `ArgumentRefused` (`.field`, reason `not_a_string`, formatted without the value) and also a `TypeError`, so 0037's type contract for `record_procedure` holds. A `str` subclass is screened on its `str` data. Up to round 4 a non-`str` identifier skipped the screen and later code turned it into text: `remember`'s fallback summary interpolates `event_type`, and the provenance model converts a bytes `evidence_ref`. §4b-ii D3's screen of `revoke_source`'s and `unrevoke_source`'s `origin` and `source_id` takes the same check; before it, a bytes value skipped D3 and a later bound check quoted it in its exception's message (found by dev's A5 drive in round 5).

*Measured scope at the round-5 pin* (`specs/evidence/0055/a5-type-census.json`; the check is `tests/test_0055_r4_closure.py`, which derives A5's census from the signatures and drives every row with the same token as bytes and as a `str`): 83 rows over 24 methods. 32 are refused by type: 28 by the method's own screen and 4 by D3. On the other 51, a bytes value reaches no further than the same `str`: not the store, not a provider, and not an exception's text. 14 of them raise a library exception that quotes the caller's own argument in both forms (an unknown edge or notice id, a value outside a closed vocabulary, an unparseable date). That is E1's library scope (the Build section's *The scope of E1*), and every boundary that carries such an exception onward formats it.

**Every other string parameter (A5's census), and why it is not screened:**

| class | parameters | why not screened |
|---|---|---|
| lookup key for an existing row | every `edge_id`, `episode_id`, `notice_id`, `recall_id` | it names a row already stored and introduces no text. **v0.4:** how such a key is *reported* when it carries a shape is §4g's locator rule |
| identity that may name a legacy source | `revoke_source`'s and `unrevoke_source`'s `origin` and `source_id` | **v0.4, R1-07: not exempt.** §4b-ii D3: a shape that names no stored record is refused before any digest; one that names a legacy record proceeds under a declared digest exception |
| closed vocabulary, enforced in code | `revoke_source`/`unrevoke_source` `reason` (`SOURCE_REVOCATION_REASONS`, `SOURCE_LIFT_REASONS`, checked at `src/veracium/store/revocation.py:353`); `redact`'s `reason` (`REDACTION_REASONS`, 0041 INV-6); `reply`'s `kind` (`REPLY_KINDS`); `record_outcome`'s `actor` (`_OUTCOME_ACTORS`); `record_procedure`'s `relation` (must be registered procedural); `introspect`'s `mode` | a value outside the vocabulary is already refused |
| parsed format | every `date` (`datetime.fromisoformat`, refused on failure) | an ISO date cannot carry a §4a shape |
| query, not stored | `recall`, `answer`, `describe_procedures` `query`; `facts_valid_at`'s `subject`, `relation` | not written (`policy_receipt` holds no query text, census 1); egress to the gate's provider is §10 Q4 |
| authorisation token | `forget_everything_confirm`'s `preview_token` | verified by its HMAC and never stored; **never screened and never refused** (B1, I14) |
| paths | `import_memory`'s and `export_memory`'s `path` | a host path; the file's *content* is screened (§4h) |

Closed-vocabulary fields (enums such as `author`, `kind`, `outcome`) are not screened: they cannot carry a value.

**Why identifiers refuse.** An identifier is compared, hashed or joined on. Withholding part of it would silently
change what it names (and, for `corrected_value`, store a different fact than the caller asked for). A refusal is
visible and costs one call.

**Order matters, and is an invariant (I12).** The screen runs before: the `distill` call (A7), the degrade callback's
`_len_sha16` (a 16-hex sha256 of the text, which for a short password is a guessing oracle in a host log), any digest
over the text (A13), and any write.

### 4b-ii. Digests and identities over caller input (v0.4, round 1's R1-07)

v0.3.2 said the screen runs "before any digest", and exempted `revoke_source`'s `origin` and `source_id` as lookup keys
that "introduce no text". Round 1 showed the exemption false: `revoke_source` on an **empty** store computes the source
identity digest and persists it to `source_revocations` and the AuditLog. Dev's census C at `2040a789` (coordination
`e42b05f`, `dev-handoff/0055-r1-census/C-identity-hashing.md`, probes probe_c and probe_c2) found the class
wider than that:
- an invalid revocation reason is refused only after the digest;
- a `dry_run` returns the digest;
- `record_procedure` writes its source's digest to the AuditLog on every call with a `source_id`;
- ingest hashes `source_id` before the model call and before its length checks;
- import hashes the whole file before reading its header.

**D1, order.** §4b runs first in every entry point: before any digest, model call, log line or write, before any
check that reads a free-text argument's content, and before any refusal that carries part of an argument's value. I12
holds this for every digest in census C's rows 1–3, 8–11, 13, 15 and 18, not only for the distill call.

**Content-free pre-gates may come first (v0.5.6).** A served tool may refuse before §4b runs, on a gate that reads no
free-text content and writes nothing:
- the capability gate (§4g's `attempted_elevation`) and the erasure setting;
- the scope configuration;
- the target's presence by its lookup id (an identifier §4b does not screen, D2);
- a type or length check of a free-text argument;
- a closed-vocabulary check (`author`, `derived_from`), refused `not_accepted`: the served refusal carries the field
  and the allowed values as attributes, never the value (§4g E1).

Each such refusal names the gate, the target id, the scope, or the field and its limit; none carries any part of a
free-text value. The sites at `85d84928`:
- `correct_fact_report` and `confirm_fact_report`: capability, scope configuration, target presence;
- `dispute_fact_report`: capability, the reason's type and length (`reason_too_long`), scope configuration, target
  presence;
- `forget_fact_report`: capability and erasure, scope configuration, target presence;
- `forget_everything_preview_report` and `forget_everything_confirm_report`: capability and erasure;
- `find_facts_report`: capability, scope configuration;
- `record_procedure_report`: capability and the closed-vocabulary check;
- `remember_report`: the closed-vocabulary check only. Its capability floor discards a raise rather than refusing
  (`provenance_raises_discarded`), so it is no refusal.

**A consequence, stated:** a credential-shaped `corrected_value` on an unknown edge id is refused `not_found_in_scope`,
not `credential_refused`. Nothing is written either way, and neither refusal carries the value. The build pins the
rule in `tests/test_0055_d1_pregates.py`: each listed site and gate, with a credential shape in every free-text argument
(and in `source_id` where the site takes one, and in `forget_everything_confirm`'s preview token), returns its own
refusal's name, leaves the store unchanged, and echoes no 8-character window of the shape; `remember`'s
closed-vocabulary refusal is driven through the MCP transport with `text` shaped too; a negative control shows the
window check fires; and `correct_fact`'s target-presence case expects `not_found_in_scope`. Reordering the gates
instead would move gates in accepted surfaces (0031's tools) without changing any observable outcome.

**D2, by input component, not by digest name (v0.5, round 2's R2-02).** v0.4 classified each digest by its name,
for example "over the screened incoming edge" or "over screened identifiers". Round 2's reviewer showed two digests
whose name was classified while one of their components was not:
- **the supersession digests:** they hash whole STORED prior edges, so a clean new input over a prior carrying a
  recognised `evidence_ref` persists a receipt digest over it;
- **the confirm request digest:** it hashes the lookup argument `edge_id`, which §4b leaves unscreened because it
  names a stored record.

That repeats round 1's class one level down. Census C asked what is hashed over caller input; it never asked what
else a digest's projection holds.

**Census F** (dev, coordination `9abf5ca`, `dev-handoff/0055-r2-census/`) is a sweep, not a list of names. At
`2040a789` it covers:
- every hash call site in `src/`: 33 primitive `hashlib`/`hmac` sites, and 129 call sites through 38 wrapper functions
  in a closed transitive sweep;
- every component of every digest: 429 rows over 80 digest call sites, each with its source class and the digest's
  destinations (persisted, returned, logged, exported).

It found 98 LEGACY-CAPABLE components (stored, lookup argument, import file, digest chain) in 36 digest sites. Its
witnesses W1–W6 reproduce the reviewer's two cases and extend them; W3 is the no-token control. The figures are
census F's own, generated by its assemble.py.

**From v0.5.5, census F has an addendum** (research, evidence/census-F-addendum-2026-11-23.md, at `b256e348`),
written from the build's sweep (`## Build`, I19-F1 and I19-F2) and the owner's rulings on it. Census F itself is kept
as taken. The addendum:
- **adds three sites census F did not list** (I19-F2), each with one component:
  - row 37, `request_digest_under` in `SqliteStore.apply_supersession_plan`: the stored prior's `user_id` inside the
    plan's raw request. `identifier_kept` (D4's host-supplied `user_id`); the digest is persisted with the receipt,
    and for a shaped stored `user_id` the store guard (I13) refuses the write after the hash, so it persists nowhere;
  - rows 38 and 39, the import ledger's identity and evidence-ref digests in
    `scope_linkage.reconstruct_absorption_rows`: `screened` (§4h screens the file before any digest over it);
- **adds the pool key's two destinations to rows 8, 14 and 34** (I19-F1; D3 below).

So the map covers 39 sites and 101 components.

**Every legacy-capable component has exactly one rule.** The map is `evidence/digests.json`, generated by
evidence/digest_map.py from census F and its addendum. That script exits nonzero if a component has no rule, has two,
or names a component the census does not list; from v0.5.5 it also refuses an addendum row number or site that
repeats census F, a destination amendment to a row census F does not hold, and a row amended twice. **From v0.5.2 (round 3's A2) the check is a bijection, and no rule is a default:**
- before any map is built, the census is refused on a repeated row number, a repeated site, or a component listed
  twice in a row, and the rules on a component named twice;
- every rule names its components by the census's exact text. The census's (row, component) pairs and the rules'
  pairs must be equal sets, so a missing rule and an unknown component each refuse the map, and no map is written;
- v0.5.1 gave an unrecognised component of the whole-plan row (row 1) `identifier_kept`, and one of row 17
  `screened`, by default. Both rows are now explicit lists, so an unfamiliar component refuses the map instead of
  acquiring an identity exemption.

evidence/digest_map_mutants.py keeps the ordinary census as the GREEN control (the map byte-identical to
`digests.json`). It holds eight mutants RED for their own reasons: a duplicated row (round 3's reproduction, the
confirm row), a duplicated site, a duplicated component, a missing rule, an unknown component, an unfamiliar
whole-plan component, and a rule deleted or named twice. It also runs v0.5.1's script on two of them: the duplicated
row passes with exit 0 and a byte-identical map, and the unfamiliar component is given `identifier_kept`. From v0.5.5
it holds four addendum mutants RED too (a repeated row, a repeated site, an amendment to an unknown row, a row amended
twice), with the control still byte-identical (`out/digest_map_mutants.out`). The rules:

| rule | meaning |
|---|---|
| `screened` | the component is screened before the hash: caller input (D1), composed text (§4c-ii), an import file's fields (§4h, which runs before any digest over them), provider text (§4g E3) |
| `refused` | a shape in the component refuses the operation before the hash |
| `identifier_kept` | an id, link, provenance identifier or closed-vocabulary value that the store keeps raw (0041 keeps identities; §4f's identifier residual; §10 Q7). The digest holds nothing the stored identifier does not, and lives no longer than it |
| `content_residual` | stored free text whose digest outlives the remedy of its source record: a named residual (§4f) |
| `compare_only` | the digest is not persisted, returned, logged or exported |
| `declared_exception` | D3 (below), `maintain()`'s pool key in D3's form (rows 8, 14 and 34, v0.5.5), and the converting import's whole-file digest (`portability.py:834`): it names the artifact, not a field, and a field cannot be recovered from it without the rest of the file. It is store-level (`migration_op`) and survives `forget_user` (§4f) |

**What the map decides, for the components a reviewer would ask about first:**
- **Request identities hash a lookup id:** `identifier_kept`.
  - confirm hashes `edge_id`;
  - reply hashes `edge_id`, and on a resolve a reply id;
  - undo hashes `edge_id` and the migration `plan_id` (v0.4's D2 omitted undo).

  The id is the stored record's own. When the edge is redacted, 0041 REPLACEs all three carriers:
  `confirmations.request_digest`, `replies.request_digest`, and `request_registry.request_digest` for every row whose
  `target_edge_id` is the edge, which covers undo's registry row (dev verified the undo case). Legacy operations stay usable: confirm, reply and undo on a record with a shaped id succeed,
  as today.
- **The supersession digests hash whole stored priors.**
  - A prior's ids and provenance identifiers are `identifier_kept`.
  - A prior's free text (`subject`, `relation`, `object`, `note`, `invalidation_reason`, `original_relation`) and a
    refusal's `relation` are `content_residual`. 0041 §4f cannot locate a supersession receipt exactly, so a
    redaction of the prior reports the receipt domain (`receipts_complete=False`), and the receipt may keep this
    digest (0041 D4). `forget_user` removes it.
  - **The projection is not changed.** It is the replay identity (0041 D4), and screening it would change what a
    replay of an existing receipt compares. So a clean new input over a legacy prior is accepted as today, and §4f
    lists the receipt digest as a residual.
- **`correct()` builds its incoming edge from the prior.**
  - A shaped `subject` or `relation` refuses `correct` before the projection is hashed (§4c-ii row 8).
  - The copied `note` is masked before the write AND before the projection is hashed: D1's order holds for composed
    text as it does for caller text.
  - `supersedes`, and the lookup id inside `evidence_ref`, are `identifier_kept`.
- **Import-file components are `screened`.** These are the record ids, act and outcome uids, a notice's source
  identity, and the file provenance that `plan_row_id` binds. §4h screens the whole file before any digest over its
  components.
- **`semantic.content_digest` keeps v0.4's rule:** it is computed over the masked text the embedder receives (§4e),
  never over raw legacy text. Census F's W4 shows today's raw digest on backfill, the red baseline. The compare sites
  compute over the same masked text, so freshness compares like with like.
- **Provider text is masked before the diagnostics digest (§4g E3).** This covers `_len_sha16` over an answer, a retry
  answer or a provider error. 0039 §2a's `answer_sha16` and `msg_sha16` become digests of the masked text. They are
  identical to today on text with no shape. They are diagnostic fields with no CAS or replay role, so this is the one
  interface change R2-02 makes, and it is named here.
  - **The lengths change with them:** `answer_len` and `msg_len` are lengths of the same masked text.
  - **It is cross-spec:** 0039 §2a defines those fields. It gets an amendment line, `0055/0039-masked-diagnostic-digests`
    (`proposals/0039-masked-diagnostic-digests-AMENDMENT-DRAFT.md`).
  - **0039's transcripts stay byte-identical** only because their fixtures hold no shape. A re-pin of them is not a
    change in behaviour.
  - **It folds with this spec's adoption or build** (round 3's answer 3), not before. That build verifies that the
    no-shape transcripts are unchanged, and adds controls with a shaped provider answer and a shaped provider
    exception. A draft amendment is not evidence that the line has landed.
- **Compare-only components** (scope fingerprints, standing-revocation guards, membership evidence, freshness checks)
  stay compare-only. I19 asserts that they never reach a destination. The exception, from v0.5.5, is the scope
  identity digest that `maintain()` returns as a pool key (rows 14 and 34, with row 8's ledger copy): D3's form, below.

**What census F left open, and where it lands.**
- **Read, not run:** undo's digest over a legacy id (running it needs a restored migration outcome row) and reply's
  resolve target over a legacy reply id. I19's build witness runs both.
- **`revoke_source`'s `origin` and `source_id`:** classed as lookup arguments; D3 governs them.
- **The consolidation `op_key`:** a colon join that stores an episode id in clear, not a digest. It is an identifier
  the store keeps raw (`identifier_kept` by the same reasoning).
- **What the build's sweep found census F had not listed** (v0.5.5): three digest sites (rows 37-39, above) and two
  destinations of one digest (the pool key, D3's form below). Each is now in the map; the sweep's `UNMAPPED_SITES`
  and `UNDECLARED` entries for them become mapped rows.

**D3, revoking a credential-shaped source.** It must stay possible to revoke a legacy source whose `source_id` is
credential-shaped, and it must not become a way to introduce one. So, when `revoke_source` or `unrevoke_source` is given
an `origin` or `source_id` that carries a shape:
- **The lookup:** the library first looks for a stored record (an edge's or an episode's provenance) **of the same
  `user_id`**, carrying exactly that `source_id` under the **resolved origin**, i.e. the same pair the digest would
  frame (v0.4.1, dev's B3). Unscoped, user A's legacy record would let a revoke for user B persist a
  credential-derived digest under B. **The lookup is not a sink:** it writes nothing, logs nothing, and raises nothing
  that echoes the value. **It is an existence oracle:** refuse or proceed tells the caller whether such a record
  exists. That is acceptable only because `revoke_source` and `unrevoke_source` are host-only: no MCP tool or adapter
  reaches them (census C).
- **None found:** the call is refused with `credential_refused`, before the reason check and before any digest. An
  invalid reason is checked before the digest too, so a refused call never computes one.
- **One found:** this is legacy resolution. The call proceeds, and the identity digest of that legacy source is persisted
  to `source_revocations`, written to the AuditLog line when a log is attached, and returned by a `dry_run`. **This is
  the declared exception.** The digest is the shared source-identity primitive (`source_identity_digest`, 0006): an
  unsalted sha256, domain-separated and length-framed over the RESOLVED pair, the origin and `source_id`. The store's
  local origin is not a third component; it only resolves an absent origin. Anyone who knows the resolved origin can
  test a guess of a low-entropy `source_id` against it. It is a residual (§4f's matrix): 0041 redaction does not reach `source_revocations`, and
  `forget_user` removes it.

**D3's form, `maintain()`'s pool key (v0.5.5, the build's I19-F1; the owner: "declare both destinations as a named
exception").** `maintain()` keys each consolidation pool by the scope's identity digest (0021 §4b): the same shared
source-identity primitive over the same resolved (origin, `source_id`) pair as D3, computed at map rows 8, 14 and 34.
The key is RETURNED (the host API, the MCP `maintain` tool, an adapter's `maintain`) and LOGGED (the AuditLog's
`consolidate-pool` event, `pool_key`). Its inputs are legacy only: §4b refuses a shaped `source_id` at every entry
point, so a shaped value can reach the key only from a record stored before this spec. Those rows are
`declared_exception`. Like D3's, the AuditLog line's copy is the host's and survives `forget_user` (§4f); the ledger
copy (row 8) is CLEARed by 0041 with its input, as before. A reader who knows the resolved origin can test a guess of a
low-entropy `source_id` against the key, as against D3's digest.

**D4, `user_id` is host-supplied and outside the screen**, with one exception:
- **On every served surface it is bound by the host:** every MCP tool passes the server's `default_user`, and no tool
  schema has a `user_id` (V-NO-USER-ID-ARG, 0031). An adapter drops one passed as an argument. It is never
  model-suppliable.
- **The exception is import.** `import_memory` takes `user_id` from the file's header when the host passes none, and
  there the value is import-file input: it is an identifier under §4h, refused if it carries a shape.
- **Where it lives:** `user_id` is stored in 21 tables and on every AuditLog line in plaintext. It is folded into about
  ten digests, and it appears in readable base64 inside the `tt1` preview token returned to the model, which is a
  disclosure of the host's own id to its own model, not a supply path.
- **The limit:** a host that uses a credential as a user id is outside this spec, and §8 says so.

### 4c. The model-output screen

Model text derived from caller text is screened before it is parsed into a write: the distill output and its retry,
consolidation output (`lifecycle.py:212`), and the compiled wiki (`compile.py:353`). A triple with a shape in any
string field is **dropped**: it is the credential fact itself, and dropping it loses only that triple. An episode
summary or wiki text is **withheld** span by span. Each drop is counted with source `model_output`.

With §4b in place this screen should never fire on new text: a non-zero count means a model reassembled a withheld
span, or a path bypassed §4b. It is the canary, not the defence. **It runs at each model site, not only at the
extractor (v0.4):** the consolidation draft (`lifecycle.py:252`) and the compiled wiki (`compile.py:353`) take stored
text in their prompts and store the model's output, so a screen at the extractor alone would not reach them
(census A rows 6–7).

### 4c-ii. Derived writes: text composed from stored records (v0.4, round 1's R1-01)

§4b screens what a caller sends; §4c screens what a model returns. Neither covers a writer that **composes new text from
a record already stored**, and round 1 showed that this copies a legacy credential into a fresh row: `dispute` and
`record_outcome` build an episode summary from the old edge's `relation` and `object`. Dev's census A at `2040a789`
(coordination `1e519b1`, `dev-handoff/0055-r1-census/A-composition.md`, probes probe_a and probe_b) lists 19
writers that copy stored text into new rows, and 12 more sites that rewrite a row in place. Each writer falls under one
of three rules.

**1. Composed free text is withheld before it is written, hashed or journaled.** These five writers compose a new
string that includes stored field values. Each passes the composed string through `mask()` (§4a) at the composition
site, before the string reaches a row, a digest or the journal:

| census A row | writer | composed field |
|---|---|---|
| 1 | `Memory.dispute` (`__init__.py:2138`) | the audit episode's `summary` |
| 2 | `SqliteStore.confirm_edge` (`store/sqlite.py:1141`) | the confirmation episode's `summary` |
| 3 | `Memory.record_outcome` (`__init__.py:2346`) | the outcome episode's `summary` |
| 4 | `Memory.correct` (`__init__.py:2513`) | the audit episode's `summary` |
| 5 | absorption (`graph.py:553–556`), reached by an ordinary `remember` or `record_procedure` | the prior record's rewritten `note`: `<old note>; absorbed_by:<id> (restated as '<new object>')` |
| 8 (`note`) | `Memory.correct`'s replacement edge (`__init__.py`, the `Edge(...)` built before `graph.plan_correction`) | the copied `note` |

**Where `correct` applies the rule (v0.5, dev's internal read).** In `Memory.correct`, the mask and the subject/relation
refusal (rule 3, row 8) are applied to the new edge **before `graph.plan_correction`**. The plan, its `raw_request`
and every supersession digest are functions of the plan, so all three then see the masked note. Applied at the
store's write boundary instead, the row would be masked while the digest and `raw_request` stayed over the raw note.
That would break §4b-ii D2's claim and the store's own `verify_snapshot_against_plan` check. The agreement relay
(`relay_markers`) reads the raw note before that point. Its output is a closed vocabulary of markers, so it is not a
carrier.

Row 5 rewrites the prior's own note, so withholding there also withholds a legacy span in that note. That is
intended: the row is being rewritten anyway, and the rewrite is the moment the text passes through our code.

**This is also what keeps legacy records workable.** §4d refuses an introduced shape on a created or changed edge. Without
this rule, the guard would make it impossible to correct a legacy-secret edge, because `correct`'s replacement copies
the note. It would also make an ordinary `remember` that absorbs a legacy-secret prior fail. The derived-write screen
runs first, so the guard sees withheld text and passes (I13, I16).

**2. Model-mediated rewrites are screened at their own site** (§4c, above): census A rows 6 and 7.

**3. Unchanged snapshots are a closed, declared exception.** These copy a stored value byte for byte, or a whole row,
into a new row. They are permitted, and listed so that nothing else can claim the exception:

| census A rows | what is copied | why the exception |
|---|---|---|
| 10, 11, 12 | the edge journal's whole-row snapshot (`edge_event.state`) on every transition; the 0029 baseline; the episode redaction journal | the journal is the record's history (0029). A snapshot that differed from the row it records would make history disagree with state. 0041 redaction tombstones the journal (§4f), which is how a legacy credential leaves it |
| 8 (identity fields only) | `correct`'s replacement edge copies the prior's `subject` and `relation` | they are the fact's identity, which supersession joins on. If either carries a shape, `correct` is **refused** with `credential_refused` and names 0041 redaction as the remedy, rather than masking an identity. The copied `note` is free text and falls under rule 1 |
| 9 | an outcome link inherits the chain head's `context_ref` when the caller omits it | an opaque chain key, joined on |
| 14–19 | consolidation output provenance and dates; contribution-ledger payloads and digests; the request-registry backfill; migration copies of reasons and stamps | provenance identities, dates, digests and closed reasons, copied for continuity |

**What the exception does not permit.** It covers copying a value unchanged. It never covers composing new free text
around one: a writer that builds a string from stored fields is rule 1, whatever else it does. The reviewer's
distinction, kept: the journal snapshot is an intentional exception; a new summary is not.

**I11 names the rule, not a category.** Each public store writer is classed as one of four things:
- screened at source (§4b or §4c, naming the screen);
- derived-write rule 1 (naming the composed field);
- a snapshot exception (naming its row in the table above);
- marker only.

"Existing text only" is no longer a class. A new writer fails CI until classed.

### 4d. The store guard for edges (defence in depth)

At `_upsert_edge_row`, beside 0041's marker refusal (`_SITE_UPSERT_MARKER`), every string field a write **introduces**
is screened: all fields on a `created` edge, only the changed string fields on a `mutated` one. A match raises
`CredentialRefused` and writes nothing. Exempt: 0041's redaction path (it writes the marker over the old text) and
state transitions that change no string (invalidate, expire, reinstate, confirm), which is why the rule reads
*introduced* rather than *present*: a stored legacy credential must stay disputable, expirable and redactable (census
1 §5).

Episodes and replies have no single write point (A3). Their writers are covered at source (§4b, §4c), by the
derived-write rule (§4c-ii), and bound to the writer inventory (A4) by **I11** in §4c-ii's four classes.

### 4e. The read backstop (rows already stored)

Every text **read from a stored record** that the library sends toward a model or a tool result passes the same
recogniser and is withheld: the recall block, `find_facts`, `describe_procedures`, `why`, the answer gate's prompt, the compile and
consolidation prompts, and the embedder's input. Nothing at rest changes; this is a read-time mask, deterministic, with
no migration and no schema step. The precedent is `procedures.matches_executable_detail` with its withheld outcome
(`src/veracium/procedures.py`).

**The compiled wiki's cached body too (v0.5.8, round 4's R4-02).** `ensure_wiki` can return a fresh cached body without compiling; that body is masked on the read like every stored text. Freshness and a valid envelope do not show the body was screened (a cache written before this spec, or by another writer), and the cache identity does not bind the shapes version. The read masks and never rewrites the cache.

**Every stored field a read prints, not the summary alone (v0.5.8, found by round 5's carrier-to-boundary table).** An episode line printed `[<date>] <masked summary>`, so a legacy shaped `date` reached the answer gate's prompt, the compile prompt and the served recall results; the date is now masked where recall and the compile print it. Two other printers of an episode date (the briefing's recent lines and consolidation's listing) read only a date that `date.fromisoformat` parses, which a shaped value never is, so they take no mask and a test holds each clean. A structured report (`why`, text and JSON) is masked keys and values alike: `credentials.mask_deep` masked values only, so a legacy `outcome_counts` key was printed as stored; two keys that mask alike stay two entries. `why --find` masks its whole hit, `invalidation_reason` included. The table plants each position in two value forms, the token alone and behind an ISO-date prefix: an episode whose date is a bare token reads as a future date (`Episode.valid_now` compares dates as text), so it is not assertable and never reaches the compile, and a mutant unmasking only the compile's date line survived every bare plant. The check's domain is value forms as well as positions.

**Scope, stated (v0.2, B1).** The backstop applies to stored record text only. A **store-minted value** in a result
is not record text and is never masked: ids, digests, receipts, and above all **0031's `tt1` preview token**, which
`forget_everything_preview` returns and the model must pass back to `forget_everything_confirm`. Masking it would make
the two-step erase impossible. The pair is exempt by construction, because the token is minted at call time and never
read from a record, and the exemption is pinned by I14. A `tt1` token that a model or user pastes into `remember` is
still caller text, and §4b withholds it.

**Not masked, by design:** `export_memory` (a host backup; masking it would break the restore round trip), 0041
redaction, the finder (§4f), and the host's own direct reads of the store. §8 says so.

### 4f. The finder, the remedy, and what the remedy cannot reach (v0.4, round 1's R1-03)

**The finder.** A `doctor` check, `credentials_at_rest`, and the CLI verb `veracium credentials scan` run the recogniser
over every carrier census E lists (dev, coordination `47997b5`, `dev-handoff/0055-r1-census/E-remedy-domain.md`):
- the text fields and provenance identifiers of `edges` and `episodes`;
- `edge_event.state` and `episode_event.state`;
- `replies` (text, target, correlation id), `confirmations` and `request_registry`;
- `wiki.text`, `contribution_ledger.payload`, and `source_revocations`.

**It fails closed (v0.5.8, round 4's R4-04 and research's S1).** Up to round 4 the finder kept a string only when its top-level key was on a hand-written list, read fixed side columns, and skipped a current row whose JSON did not parse. It missed four historical text carriers (`invalidation_reason`; an episode's `kind` and `retired_reason`, in the records and in their journals), and the verifying second scan agreed with the first on the miss. From v0.5.8:
- a record's removable text is derived from 0041's own treatment tables (the fields a redaction of that record rewrites), never listed again;
- every other string leaf of a record or a journal state, mapping keys included (`outcome_counts` is `dict[str, int]`), is still read: provenance and link fields as identifiers, anything else as `<carrier>.other`, both residual, because the redaction preserves them;
- a current record that does not parse is read whole as `<kind>.unparsed`, and a journal row's own `reason` column as `<journal>.reason`, both residual; a journal's text under a parent already redacted is `<journal>.after_redaction`, residual, because a second redaction writes nothing;
- every non-BLOB column of every table with a `user_id` column is read from the live schema, so a column added later is scanned; a column no class names is `<table>.<column>`, residual;
- a table without `user_id` holds no user's record (census F, D12 and D13) and is not read; the build holds that set equal to the live schema's, so a new store-level table is a decision.

A class no remedy names is a residual by rule, so an unlisted carrier is reported, never dropped.

The report is by carrier class, with counts and class names. A record is named by a **per-report ordinal** (§4g), never
by a value, length, offset or digest.

**The remedy is field by field, and its residual is reported.** v0.3.2 said `redact` removes what the finder finds.
Round 1 showed it does not: 0041 redaction treats text fields and deliberately keeps identifiers and provenance
(`redaction.py:96–115`; replies keep `target` and correlation ids, `store/sqlite.py:4060–4071`). Census E confirmed
this at `2040a789`. The matrix:

| carrier (where the match is) | action | removed? |
|---|---|---|
| an edge's text fields (`object`, `note`, `subject`) | 0041 `redact` of that edge, reason `operator_policy` | **yes**: marker; the journal gets a `redacted` tombstone; embeddings deleted |
| an episode's text (`summary`), including legacy dispute, correct, confirm and outcome summaries | 0041 `redact` of **that episode** by its own id. The finder scans episodes, so a confirm episode quoting a redacted edge is found as itself, not through 0041's derived-record links | **yes** |
| `edge_event.state` or `episode_event.state` only (history of a record whose current row is clean) | 0041 `redact` of the **parent** record (the event row's edge or episode id) | **yes**: the tombstone covers the history |
| journal text of a record **already redacted** (`<journal>.after_redaction`; v0.5.8, found by round 5's carrier-to-boundary table): a store redacted before 0041's treatment covered the field, such as an episode's `kind` or `retired_reason` (R4-04) | none by 0041: a second redaction answers `repeated` and writes nothing | **no: residual**, reported as such; `forget_user` removes it. An episode's journal is written only by a redaction, so every text hit there is this case |
| `replies.text` only | 0041 `redact` of the reply's **parent edge** (`replies.edge_id`), even when that edge itself carries no match | **yes**, for the text |
| `wiki.text` | discard the compiled wiki (`discard_wiki`); it is rebuilt from masked reads (§4e) | **yes** |
| a provenance identifier: `source_id`, `evidence_ref`, `context_ref`; a reply's `target`; a correlation id (`replies`, `confirmations`, `request_registry`) | none by 0041, which keeps identities by design | **no: residual**, reported as such |
| `source_revocations.identity_digest` (§4b-ii D3) | none by 0041 | **no: residual**; `forget_user` removes the row |
| D3's identity digest in an AuditLog `revoke_source` / `unrevoke_source` line (v0.5, R2-04) | none: the AuditLog is the host's append-only file, outside the store | **no: host residual.** It survives `forget_user`: round 2's probe found 0 revocation rows after `forget`, and the digest still in `audit.jsonl`. Handling it (rotating or deleting the log) is the host's, outside this API |
| `maintain()`'s pool key in an AuditLog `consolidate-pool` line (v0.5.5, I19-F1; §4b-ii, D3's form) | none: the AuditLog is the host's append-only file, outside the store | **no: host residual**, as D3's digest. It survives `forget_user`; it is also returned to the caller of `maintain()`, which keeps no copy in the store |
| the converting import's whole-file digest, `migration_op.inputs_digest` (§4b-ii D2's declared exception; v0.5.1) | none: `migration_op` is store-level, and never erased (0044 §4g-ii) | **no: residual by design, and it SURVIVES `forget_user`** inside the database |
| a supersession receipt's request, logical and outcome digests over a legacy prior (§4b-ii D2, `content_residual`; v0.5, R2-02) | none exact: 0041 §4f reports the receipt domain (`receipts_complete=False`) | **no: residual, and it OUTLIVES a 0041 redaction of the prior** (0041's declared unvouched receipt domain); `forget_user` removes the row |
| `supersession_refusals.relation` (census E; v0.5.8, S1) | 0041 `redact` of the refusal's prior edge (a redaction of either edge rewrites it) | **yes** |
| `contribution_ledger.payload`, migration copies | none by 0041 | **no: residual** if found |
| any other string the finder reads (v0.5.8): `<carrier>.other`, `<kind>.unparsed`, `<journal>.reason`, `<journal>.after_redaction`, `<table>.<column>` | none by 0041, which preserves them | **no: residual**, reported as such; `forget_user` removes the row |

**`forget_user` is the total remedy for the user's logical database rows (v0.5, round 2's R2-04).** It deletes
every row of all 21 tables that hold `user_id` (census E, executed: no planted string survived in the database bytes
on this box). The finder names it whenever a residual remains in the database.

**One digest inside the database survives it (v0.5.1, dev's internal read).** It is the converting import's
whole-file digest, `migration_op.inputs_digest` in `import-convert` mode. `migration_op` is store-level: it has no
`user_id`, and 0044 §4g-ii's erasure rule names it among the tables that are never erased. When the converted file
was the user's export, a legacy credential in that file is in the digest's preimage. It is §4b-ii D2's declared
exception, and it is a residual by design. The other store-level tables hold nothing derived from a user (census F,
D12 and D13), and neither do `migration_op`'s other two modes:
- `arity_era` holds a timestamp;
- `plan_header.registry_digest` is over the constant plan relations and their closed arities;
- `reclassification_plan` holds those relation names;
- `migration_op`'s `plan_only` and `restore` modes are over that digest and the mode.

**It does not reach what lives outside the store's tables:**
- the host-managed AuditLog, which keeps `user_id` in plaintext, counts, and D3's identity digest for each revoke or
  lift of a credential-shaped legacy source, and (v0.5.5) the same digest as `maintain()`'s pool key for each
  consolidation pool;
- exports and backups;
- the diagnostics log file;
- freed database pages (§8).

The finder's report names these as outside the remedy. v0.4 called `forget_user` "the total remedy" without that
scope.

**After acting, the CLI scans again** and prints what was removed and what remains, by carrier class with ordinals. It
exits nonzero while a residual remains. **A 0041 receipt is not proof of removal; the second scan is** (I18).

**An opaque digest is declared, never inferred absent (v0.5.2, round 3's build note).** A shape scan cannot see a
credential inside a digest. So the report lists every opaque residual digest domain as declared and unvouched,
whether or not any raw token was found: the supersession receipts' digests, the host AuditLog's D3 digest and (v0.5.5)
its `consolidate-pool` pool keys (named in the finder's declared list from v0.5.8, round 4's A1), and the store-level whole-file digest of a converting import. This holds most of all after a targeted redaction or
`forget_user`. Those domains never become a clean-removal claim. This implements the frozen residual contract and
does not reopen it.

**Whether to amend the identity contracts** so that a credential in a provenance identifier can be removed without
erasing the user is an owner decision, not something this spec does incidentally: §10 Q7.

**No migration, no `SCHEMA_VERSION` change.**

### 4g. The report, outward errors, and where refusals are counted

**In the result**, only when something was withheld or refused:
`"credentials_withheld": {"<field>": {"<class>": <count>, …}, …}`, or for a refusal
`{"ok": false, "refusal": "credential_refused", "field": "<field>", "class": "<class>"}`.

**The library contract (v0.4, round 1's R1-05; dev's census D, coordination `47997b5`).** Of §4b's entry points, only
`Memory.record_procedure` returns a non-dict: a `str` edge id (`__init__.py:837`). That is contract: 0037's canonical
signature (0037 line 130), 0037 line 1052, and `docs/api.md` line 113. Every caller uses it as an id. So:
- `record_procedure` keeps returning `str`;
- a new library twin, **`Memory.record_procedure_report(...) -> dict`**, returns `{"edge_id": …}` plus
  `credentials_withheld` when anything was withheld;
- `record_procedure`'s docstring names the twin, and so do 0037's contract text and `docs/api.md` (a 0037 text change
  rides with the build);
- MCP's `record_procedure` already returns `{"ok", "edge_id"}` (`mcp_server.py:297`, `:303`). It builds that dict from
  the twin, and the adapters pass it through (`adapters/_surface.py:113`);
- every other entry point returns a dict today and gains the key additively.

**Library refusal is an exception.** `CredentialRefused(ValueError)` carries `.reason = "credential_refused"`, `.field`
and `.cls`, and its message is `credential_refused: <field> carries a <class>`, never the value. This is the 0037
pattern: a library exception and a tool refusal carry the same name. MCP and the adapters map it to the refusal dict
above.

**Locators (round 1's R1-02).** A stored or imported record id is not guaranteed to be a safe, minted value: round 1
stored an edge whose id was a credential. Every report that names records names them like this (v0.5.8, round 4's
R4-03 and S2: the finder, the CLI, an import refusal or receipt, import's procedural refusals, the served
redaction receipt, and every render receipt, whether it leaves through MCP `find_facts`, library
`recall(render_receipt=True)` or `proactive`):
- by their id when the id carries no shape;
- **by a per-report ordinal** (`record 3 of this report`, with its table and carrier class) when it does.

The action keeps the raw id privately. `veracium credentials redact --yes` scans and acts in one process, and never
looks a record up by a printed ordinal or by a withheld text. Store rowids are not used: census E showed they change
(`INSERT OR REPLACE` re-mints an edge's rowid; export has no `ORDER BY`; a user remap re-ids).

**A record named by ordinal cannot be addressed by a later served call (v0.5.8).** No tool looks a record up by a printed ordinal, so a shaped-id record that a render receipt names is acted on only through `veracium credentials redact` or `forget_user`.

**One receipt keeps ids (v0.5.8).** The library `RedactionReceipt` that `Memory.redact` returns to the host keeps 0041's ids: it is the host's handle for its next redaction (0041 §11.5(3)). A served, CLI or log projection of any receipt uses locators (MCP `forget_fact`: `target_id` and `surviving_derived` by ordinal when shaped). Import's refusal list and its `withhold_credentials` receipt stay by locator, also as library returns. §8 states the residual.

**Outward errors (round 1's R1-02; dev's census B, coordination `5bfc69b`).** Census B found 55 outward paths that
carry caller input. 50 echo the raw value:
- the MCP `detail` field (`mcp_server.py:300–302`, `str(exc)[:200]`);
- any exception a tool lets escape, which the MCP SDK hands to the model as its error text;
- the SDK's own argument validation, and every Pydantic `ValidationError` (`hide_input_in_errors` is never set);
- the adapters' `ToolException(str(exc))` and `ModelRetry(str(exc))` (`adapters/langchain.py:45`, `adapters/pydantic_ai.py:51`);
- the validators of closed vocabularies, dates and correlation ids;
- 55 import sites;
- the diagnostics log's full tracebacks.

**A per-site fix does not close this.** So the rule sits at each boundary:
- **E1, one outward formatter.** Every error that leaves the library toward a model, a tool result, a CLI stream or the
  diagnostics log names the field and the reason, and for a closed vocabulary the allowed values. It never names the
  caller's value.
  - **MCP's refusal shape does not change (v0.4.1, dev's B1).** Tools keep `{"ok": false, "refusal": <name>, …}` with
    the existing refusal names, which the trust tools and the 0053 conformance suite compare. The only change: `detail`
    is no longer built from `str(exc)`. It carries the formatter's text (field and reason, never the value), or is
    omitted.
  - Adapters raise their framework's error with the formatted text.
  - An exception escaping a tool body is caught at the tool boundary and formatted. **E1 does not cover the SDK's own
    argument validation (dev's N3):** FastMCP validates arguments before the tool body runs, so only E2, and I17's
    outcome check, cover that path.
- **E2, no input echo in validation errors.** Every Pydantic model on a served or library boundary sets
  `hide_input_in_errors=True`. For the SDK's own argument validation, the build shows the served error text carries no
  value. That means configuring the SDK, or a boundary hook, whichever the SDK allows; I17 holds the outcome, not the
  mechanism.
- **E3, the diagnostics log.** Every line, tracebacks included, passes `mask()` before it is written or sent (§4i).
  `redact()`'s email and number rules stay as well.
- **Not covered, stated:**
  - `find_facts` returns the caller's own query in a successful result (`:467`). That is the model's own argument, in
    the same call, and queries are out of v1's scope (§10 Q4).
  - argparse repeats a mistyped option to the terminal of the operator who typed it.

**Never carried, anywhere** (result, AuditLog, doctor, CLI, error text, degrade payload, exception text): the matched
text, its length, its offsets, any prefix or suffix ("last four"), or any digest of it, including `_len_sha16`, except
the digests §4b-ii D2 computes over masked text or declares. A digest of a low-entropy value is the value to anyone who
can guess. **I8 checks every one of these sinks, against a schema** (§6).

**To the model as well as the host.** The report tells the model that a span was not remembered, so it does not claim
otherwise. For a caller's own new text, the report is a function of that text. For a model's output or a legacy row,
it is not, and it still carries only class names and counts.

**Counted for the operator, on one surface (dev's question 5):**
- Each withhold and each refusal calls `Memory._record("credential_withheld" | "credential_refused", {surface, field,
  class counts, source, shapes_version})`, an AuditLog "audit-only fact" in the 0023 pattern (telemetry's whitelist
  drops it).
- **The stock MCP server attaches an AuditLog when `VERACIUM_AUDIT_LOG` names a path**, and the 0053 adapters take an
  `audit_log` argument. Today neither can attach one (A10), which is the gap 0031 §10 Q4 records.
- `doctor` reads the log, when one is attached, and prints the counts by class and source.

**0031 §10 Q4 closes on the same surface, in the same build** (the owner's ruling on §10 Q1). The trust tools'
`*_impl` call `_record("provenance_raises_discarded", {surface, tool, count})` before they strip the key from the
result, and so do `remember_impl` and `record_procedure_impl`. Their counts are the same counter (0031 §4a's discarded
raise, stripped by `_OPERATOR_ONLY` and `_PROCEDURE_OPERATOR_ONLY`); without them Q4 would close for the trust tools
and stay open for the two tools where most raises are discarded. **Scope ruled by the owner, 2026-11-22, first-hand
in the dev session (as dev relays it): *"Include remember and record_procedure (Recommended)"*.** All nine `*_impl`
record the count, and 0031 §10 Q4 closes fully. The count still never reaches a tool result (0031 §4d), and it now reaches the operator through the AuditLog,
which the stock server attaches from `VERACIUM_AUDIT_LOG`. A 0031 text change rides with the build: §10 Q4's status note
(v23.8.1) becomes closed, and §4d's and §7's pointers say where the count is visible (I15).

### 4h. Import

A plain import screens every field of every record by §4b's kinds: free text is withheld, and an identifier carrying a
shape refuses its record. **Every line kind and every identifier in it is screened (v0.5, R2-02):** edges, episodes,
replies, confirmation acts, outcome rows and notices, with their record ids, links, act and outcome uids, and a
notice's source identity. **The screen runs before any digest over a file component** (row identities, op keys,
`plan_row_id`, notice ids). Its one placement is **after parsing and the procedural pass, and before the linkage
snapshot (`import_memory`'s step 1b)**. Every later step hashes file components: the remap and its outcome and act
uids, the ledger reconstruction with its identity digests, op keys and `plan_row_id`, the identity gates, the
standing cap, the act preflight, and the notice id at commit. The 0006 identity gates (step 2b) are too late a home,
because step 2a has already hashed identities by then. 0041 v16.5's reference rewrite runs in step 2, on screened
values: a shaped edge id is refused before the rewrite sees it. The converting import's whole-file digest, taken
before parsing, is the one declared exception (§4b-ii D2). *(0041 v16.5 was adopted after this spec's pin, at
veracium `658b73d1`. The build verifies 0041's adopted bytes and this placement at the build's pin: round 3's
answer 4.)* A record that links to a refused record is refused too, since its link would dangle. Records
are reported by §4g's locators, and **nothing is written until the screen has passed over the whole file**: the refusal
of any record happens before any write.

**A `restore=True` import refuses the whole import** if any record carries a shape, and names the records by locator. A
restore promises the source's bytes and identities, and a masked restore would quietly break that promise. The operator
redacts at the source (§4f), exports again, and restores.

**When the backup is all that is left (v0.2, B3; corrected at v0.4 by round 1's answer to Q1).** The operator passes
`restore=True, withhold_credentials=True`, an explicit flag that is never a default (the owner's ruling on §10 Q6).
- **What the flag covers:** it withholds free-text fields only. A record whose identifier fields (its id, provenance
  identifiers, or links) carry a shape still refuses the whole restore, because an identity cannot be withheld without
  breaking the links that join on it.
- **The route when an identity carries a shape (v0.4.1, dev's B2).** The realistic case is a webhook URL used as a
  `source_id` in the only backup. No restore path takes that backup. The route is a **plain import**, which refuses
  only the records whose identifiers carry a shape, and the records that link to them, reports them by locator, and
  imports the rest. Restore's guarantees (the source's bytes and identities) are given up for the whole import. §8
  states this limit.
- **The receipt:** it lists the withheld records by locator, with class counts.
- **What changes, stated exactly:**
  - **record ids do not change**, because they are identifiers and are never withheld;
  - the withheld records' **text** differs from the backup;
  - so do the **contribution-row identities** derived from their payloads (`plan_row_id` over `canonical_payload`).
  v0.2 said "their row identities" differ, which was wider than true.
- Every unlisted record is byte-identical to the backup.

### 4i. The diagnostics error log

The reporter's local error log, and its send path, pass every string through the recogniser before writing or sending
(A12). It is at rest on the operator's disk and may be sent by consent; the same rule applies.

**Screen whole lines, then cut (v0.5.8, round 4's R4-06).** The send path reads a window of whole lines, masks and redacts it, and only then cuts to the payload limit, keeping complete lines only: a line the cut would split is omitted, never sent in part. Up to round 4 the last bytes were cut first, so a cut inside a credential dropped its recognition prefix or its label, and the rest was sent unmasked.

### 4j. Rendering changes (model context)

- The placeholder `[credential withheld: <class>]` appears in rendered facts where a span was withheld.
- `remember`'s tool description gains one sentence: *"Credential-shaped text (keys, tokens, passwords) is withheld
  before storage; `credentials_withheld` in the result says what was."* No test pins the description's bytes at
  `2040a789`: the 0053 suite's oracle reads descriptions from the served surface, so the adapters follow, and
  0031's `test_capability_is_host_only` only requires that no description names `capability` or
  `provenance_raises_discarded` (this sentence names neither). Commands:
  `grep -n 'description' tests/test_0053_adapter_conformance.py tests/test_0031_phase_a.py`. §10 Q3.

**Migration:** none. **Unrecoverable:** a withheld span is never stored, so a false positive loses that span. The
report names its class, so the caller can rephrase.

---

## 5. Regime analysis — where does this behave differently?

- **Text size.** The recogniser's time grows in proportion to the input on the measured adversarial inputs (T1, I9; a
  measurement, not a proof); `record_procedure` caps `summary` at 512 characters
  (`MAX_SUMMARY_CHARS`), and `remember` has no cap. So I9, a build gate, times the implementation at 256 KiB, 1 MiB
  and 4 MiB, asserts the ratio on the 1 MiB→4 MiB pair (v0.5.6), and asserts under two seconds at 1 MiB on the named
  CI runner. The evidence for this design times the reference model
  at 32 and 128 KiB, for ratios only (§4a T1), and **does not satisfy that gate** (v0.5.2, round 3's A1).
- **Re-embedding (v0.4.1, dev's N1).** `content_digest` is computed over the masked text (§4b-ii D2 row 13), so the
  embedding cache key changes for every legacy row that carries a shape, and those rows re-embed on next use. It is a
  one-time cost, bounded by the finder's count.
- **Store size.** The finder (§4f) is a full scan, O(rows), run on demand, never on a hot path. The backstop (§4e)
  costs one scan per rendered string, and v0.4's mask adds one scan per pass (§4a). v0.1 measured about 0.55 ms per
  KiB per scan on a quiet box, so a 4 KiB recall block costs a few milliseconds. v0.4's re-measure ran under load
  and states ratios only.
- **Volume of withheld spans.** A text that is mostly credentials (a pasted `.env` file) becomes mostly placeholders.
  The extractor then has little to say, which is correct.
- **Language.** The labels cover English and five others (§4a); a password labelled in any other language is stored
  (§8, X-row class).
- **Cold or warm store:** no difference; the recogniser has no state.
- **Release class:** stable, on by default, no off switch. Every regime above is reachable by the tests in §6.

---

## 6. Invariants and executable checks — REQUIRED, blocking

**What is executed now, and what the build must still show (v0.4, round 1's R1-06).** v0.3.2 said "every check
below has a RED demonstration". That was true only of the rows that exercise the recogniser. The last column now says
which is which:
- **executed (reference):** run on research's reference model in its evidence directory, with a mutant shown RED and a
  no-op control green;
- **red at the pin:** a census probe at `2040a789` demonstrates today's defect, so the build's check has a known RED
  before the fix;
- **planned (build):** an integration check the implementation round must demonstrate RED then GREEN against the actual
  build.

The same mapping is machine-readable in research's evidence directory (its invariants file), and every evidence runner
exits nonzero when its check fails.

| invariant | executable check | where it runs | RED against | evidence now |
|---|---|---|---|---|
| **I1** every positive row's class is reported and **no secret byte survives** in the stored text | the adversarial table (150 rows at v0.5.7: 1 witness, 21 structural, 18 glued, 23 labelled, 5 normalisation, 19 composition, 55 near-miss, 8 stated limits; 122 at v0.5.2; run_table.py prints the total), each row run through every free-text field of §4b (`remember`, `record_procedure`, `dispute`, `reply`, and `record_outcome`'s `corrected_value`) under `none` and `direct`, then a scan of every text cell of every table and of `edge_event.state` for each secret value | CI | report-only, no normalisation, no labelled rules, no quoted values, no widening (L18); v0.5.6's word boundary (G1–G18, v0.5.7); each RED, its failures counted in `evidence/out/mutants.out` (v0.5.7: `evidence/out/v057/mutants.out`) | executed (reference): the table, on the reference model only; planned (build): through each entry point and every table. The 122 rows have not yet run through any product entry point |
| **I2** every near-miss is stored byte for byte | the same table, near-miss rows | CI | no stop list (K6), case-insensitive PIN (K35), weak labels taking any value (K10, K35), no code-expression rule (K36, K37), no token boundary at all (K55, v0.5.7) | executed (reference) |
| **I3** the **completed** output is inert: `scan(mask(t)[0]) == []` and `mask(mask(t)[0])[0] == mask(t)[0]` for every row, under composition, and `mask()` always returns, in at most five scans (v0.5: bounded by construction, §4a; v0.5.2: the scan count) | the same table, rows C1–C17, D3 and D4 (round 1's R1-04 witnesses, the boundary around them, and round 2's curly-quote family at three and four layers); the seeded composition fuzz over every accepted delimiter pairing; depth_family.py over every pairing at depths 0–12; scan_count.py's spy over every row and the curly family at depths 0–40 | CI | placeholder not exempted; a single-pass mask (C5, C6); v0.4's raise at the bound (D4); a fallback that keeps the text (D4); v0.5.1's two scans per pass (scan_count.py) | executed (reference): the table, the fuzz (at most 3 passes on ordinary text), the depth family (fallback from depth 4), the scan count (passes + 1 on completion, five at four passes and at the fallback), each mutant RED |
| **I4** an identifier field with a shape is refused whole and nothing is written | one row per identifier field in §4b (v0.2 adds `actor`, `event_type`, `undo_restoration`'s `correlation_id`); a store byte-digest before and after | CI | a build that withholds instead of refusing | planned (build) |
| **I5** a model output carrying a shape writes no edge, and is counted with source `model_output` | a stub `distill` that returns a triple carrying S1's shape for an input with none | CI | the screen moved after the write | planned (build) |
| **I6** a plain import withholds per field; a restore import with any shape refuses whole, naming record ids and the flag; with `withhold_credentials=True` it restores, withholds free text, and lists exactly the affected record ids in the receipt, and every unlisted record is byte-identical to the backup; **an identifier carrying a shape still refuses the restore under the flag (§4h)** | three import runs over one fixture built from an export of a store holding W1's credentials, written with the guard off | CI | restore that masks without the flag; a receipt that omits an affected id | planned (build) |
| **I7** no legacy credential reaches a model or tool result | a store seeded directly through the store (the guard off) with W1's credentials; recall, find_facts, why, answer (a recording stub provider), compile, consolidation and embed are each run, and every captured provider payload and tool result is scanned | CI | one read path left unmasked | planned (build) |
| **I8** no report sink carries the value, its length, offsets, a prefix or suffix, or any digest of it, and every count is the exact count | **schema-aware (v0.4, round 1's R1-06):** each sink's whole key set is held to its endpoint's schema. A credential key carries only field names, class names and positive counts, so a correct report passes whatever its classes are called (the `github_pat_`/`github_token` collision control). Canary checks (value, first and last four, sha256, sha16) run only over strings outside the vocabulary, with canaries of 37+ characters. **v0.5 (round 2's R2-03): counts are compared with the fixture's exact expected report** under §4a's count semantics (one span, multi-span, multi-pass, fallback); no number is banned for equalling a length, since a legitimate count may. The checker names no key outside the vocabulary. Sinks: the result, AuditLog lines, doctor and CLI output, exception and error text, the degrade payload | CI | schema: value, length, offset, prefix, sha16, an echoing refusal, a non-field name; counts (each schema-valid): length-as-count, offset-as-count, span-length-as-count, v0.4's cumulative count, a dropped span, a count off by one, a misreported fallback; each RED for its intended reason | executed (reference): the schema check, the exact-count check and their fourteen mutants, and every table row's exact report; planned (build): every named sink, with the same exact expectations |
| **I9** time within a measured bound (not a proof) | the named adversarial inputs (§4a T1, the two-pass composition included) from 1 MiB to 4 MiB: at most 6× the thread CPU time for 4× the input (per size the minimum over five interleaved rounds, or over ten when a case reads over the ratio and is measured again; the record's `rounds`), and 1 MiB screens in under 2 s on the CI runner; the 256 KiB→1 MiB ratio is recorded, not asserted (v0.5.6) | CI | the two quadratic forms of §4a T1 | executed (reference, ratio evidence only): the named inputs at 32 and 128 KiB, the four-pass and fallback cases included, the median of three per size, ratios 3.5–4.3× on v0.5.2's run (`out/redos.json` records the sizes, the algorithm and the runtime). This is not the gate (§4a T1); built: the implementation at 256 KiB, 1 MiB and 4 MiB, the ceiling asserted on the named CI runner only (the Build section's I9 row) |
| **I10** the rule holds under every capability and every surface | I1's table through MCP and through each 0053 adapter, under `none` and `direct` | CI (the 0053 suite) | a surface that bypasses the library entry point | planned (build) |
| **I11** every public store writer is classed for the screen | `tests/test_rii_r2_01_writer_inventory.py` gains a column; an unclassed writer fails | CI | a new writer added unclassed | planned (build) |
| **I12** the screen runs before the distill call, the degrade hash and any digest | a recording stub provider and a recording `on_degrade`: neither ever receives a positive row's value, nor its sha16. This includes the degrade site over a provider exception (`_len_sha16(str(e))`, `src/veracium/ingest.py:634` at `2040a789`), driven by a stub provider whose exception message echoes the whole prompt | CI | the screen moved after `distill`; v0.2 adds the echoing-exception case | red at the pin (census C: digests before any screen); planned (build) |
| **I15** `provenance_raises_discarded` reaches the AuditLog and never a tool result (§10 Q1, ruled) | each trust tool and `remember`/`record_procedure` under `none` with an elevation claim, through the stock server with `VERACIUM_AUDIT_LOG` set and through each 0053 adapter with `audit_log`: the log holds the count; every tool result and every reflected schema still lacks the key (0031's `test_capability_is_host_only` unchanged) | CI | `_record` after the strip; the strip removed | planned (build) |
| **I14** the two-step erase survives every screen (B1) | `forget_everything_preview` then `forget_everything_confirm` with the returned token, through the library, MCP and each 0053 adapter, with the backstop on: the erase completes; and `remember` of a text carrying a `tt1` token withholds it | CI | §4e applied to the preview result; `preview_token` screened at ingress | planned (build) |
| **I13** the store guard refuses an introduced shape and passes state transitions over a legacy row | a legacy edge carrying S1's shape (guard off), then invalidate, expire, confirm, dispute and 0041 redaction of it with the guard on: all succeed; an `add_edge` carrying a shape: `CredentialRefused` | CI | a guard on *present* rather than *introduced* (dispute of the legacy row fails) | planned (build) |
| **I16** derived writes withhold composed text, and transitions over legacy records still succeed (§4c-ii; round 1's R1-01) | seed a legacy value in each field census A's rows copy; run dispute, confirm, record_outcome, correct and an absorbing `remember` with safe new arguments; scan every new cell and journal event. Composed fields are withheld; every state change succeeds, except the intended refusal of `correct` when the prior's `subject` or `relation`, which the replacement copies, carries a shape (§4c-ii row 8); the only secret-bearing new rows are §4c-ii rule 3's declared snapshots, asserted as an exact set | CI | the derived-write screen omitted (the copy reappears in the new summary); a guard without rule 1 (correct and absorbing remember fail) | red at the pin (census A probes); planned (build) |
| **I17** no outward path echoes caller input, and reports name a shaped id by ordinal (§4g E1–E3, locators; round 1's R1-02) | every row of census B's 55 paths with the canary in each argument, through the library, MCP, the SDK's validation and each adapter: no canary in any error text, `detail`, tool error, log line or CLI stream. A record whose id carries a shape is reported by ordinal and is still acted on by its raw id. Import refuses before any write | CI | the formatter bypassed at one boundary; `hide_input_in_errors` unset; a report printing the raw id | red at the pin (census B: 50 of 55 echo); planned (build) |
| **I18** the remedy reports its residual honestly (§4f matrix; round 1's R1-03) | fixtures with a match in a text field, a provenance identifier, a reply's text only, and a journal event only: run `veracium credentials redact --yes`; removed carriers re-scan clean; the identifier match is reported as a residual and the CLI exits nonzero; operational identities are unchanged; `forget_user` then removes the residual | CI | a remedy that trusts the 0041 receipt without the second scan; a reply match not mapped to its parent | red at the pin (round 1's probe: `source_id` survives `redact`); planned (build) |
| **I19** every digest's legacy-capable components follow their one rule (§4b-ii D2; v0.5, round 2's R2-02: bound to (component, destination) pairs in `evidence/digests.json`, not to function names) | for each row of the map, seed a recognised value in that component (a stored legacy record, a lookup id, an import-file field, provider text), run the operation with clean new arguments beside an ordinary control, capture the digest's inputs and every destination, and assert the row's rule: `screened`, the shaped value never reaches the hash; `refused`, the operation refuses before it; `identifier_kept` and `content_residual`, the digest lands only in the listed destinations, and §4f lists every `content_residual`; `compare_only`, no destination; D3 and the whole-file digest as declared. The sweep is re-run at the build's pin, and a new legacy-capable component fails until it has a rule. v0.4's cases stand: `revoke_source` with an unknown credential-shaped source refuses before any digest (audit log attached and absent, preview and commit); with a legacy one it revokes and lifts and persists only D3's digest | CI | the digest moved before §4b; a component dropped from the map; a duplicated census row that overwrites its twin; an unfamiliar component given a default rule; `correct` hashing the raw copied note; the diagnostics digest over raw provider text; the reason check after the digest; `dry_run` returning a digest for an unknown shape | executed (reference): digest_map.py's bijection check over census F, and digest_map_mutants.py (the map GREEN and byte-identical; duplicate-row, duplicate-site, duplicate-component, missing-rule, unknown-component, unfamiliar whole-plan component, deleted and duplicated rule mutants RED); red at the pin: census F's W1, W2, W4–W6 (W3 the control) and census C's probes; planned (build): every row |
| **I20** `record_procedure` keeps its `str` contract, and its twin reports (§4g; round 1's R1-05) | an ordinary and a withheld call through `record_procedure` (returns the id), `record_procedure_report` (the id and the report), MCP and each adapter (the dict with the key); a refusal raises `CredentialRefused` with `.reason == "credential_refused"` and maps to the refusal dict | CI | the str API changed; the twin omitted on a served surface | planned (build) |

**The table travels with the spec, and what in it is literal (v0.3.2).** No **structural** token appears literally
in this spec, the table or a commit: no vendor key, PEM block, JWT, URL with a password or preview token. Every
structural positive is **assembled at run time** from parts (e.g. `"gh" + "p_" + 36 base62`), and the AWS rows use
AWS's documented example key, assembled the same way. A literal of that kind would trip a push's secret scanner, and a
real-looking one in our own repository would be the defect this spec exists to prevent. **The labelled rows are literal
on purpose:** well-known dummy values such as hunter2 and made-up PINs, which the table needs as written. Running the
recogniser over research's review package (its self-scan script) finds those, rule text that describes a shape (§4a's
URL form, the timing probe's PEM armour line), the probe's quoted test password, and one preview token minted under a
fixed test key by census 2's example script (redacted in the package copy). The package's README lists each by file,
line and class. v0.3.1 claimed that no literal credential appeared at all, which was broader than the artifact;
dev's pre-seal scan found it, and research's own literal scan had covered the structural shapes only. **Bytecode undoes the
assembly:** CPython folds `"gh" + "p_" + …` into one constant, so a `__pycache__` of the vectors holds whole
tokens (research's literal scan found exactly that). The repository ignores `**/__pycache__/`; the build must keep
it so, and never ship bytecode of the table. **A checker's output can undo it too (v0.4.2):** research's report-check
self-test printed the offending string when a canary matched, so its committed output carried one whole assembled
test token (a random `github_pat_` dummy, in research commits `30e10b88` and `a0896f37`). The round-2 package's
self-scan found it. The checker now names the kind of match and never quotes the string, and the round-2 package's
README lists what its self-scan finds.

**False-positive budget (dev's question 3).**
- **Zero** on the near-miss rows, enforced by I2: commit shas (40 hex), sha256 and sha16 hex, UUIDs and their 32-hex
  form, base64 digests, our `e-`/`ep-`/`ev-` ids, source-identity digests, an AWS ARN, a public key block, an SSH
  public key, URLs without a password, `$VAR` and `<redacted>` values, and prose that mentions passwords without one.
- **Measured on ordinary text** (reference model at v0.1, re-measured at v0.4 after the label-grammar change with identical counts; recorded, not a CI gate; the corpus runner records its inputs' digests and exits nonzero over the LoCoMo budget):
  - LoCoMo (locomo10, sha256 `8e2e93e1…`): **0 hits in 5,882 dialogue turns**;
  - the veracium export's `specs/*.md` and `CHANGELOG.md`: **0 hits in 59,066 lines** after the PIN narrowing (52 before it, all one shape, K35);
  - the export's `src/` and `tests/` Python: **17 hits in 164,749 lines**, every one a test constant written
    `SECRET = "SECRET-…"`, a value labelled secret, which is what the rule withholds.
- **The budget for a change to the set:** no near-miss row may turn red, and the LoCoMo count must stay at or below
  1 per 1,000 turns. LoCoMo is not vendored (licence); the measurement is re-run and recorded with each set change.

**Standing checks that must not regress:** injection 0, cross-user leaks 0, trust canaries 0, and the 0053 suite.
**Reproducer retention:** the two quadratic forms (T1), the tail leak (L18) and the commit-pin false positive (K35)
are rows in the table.

---

## 7. Failure modes and reversibility

- **Silent failure: a credential shape the set does not know.** It is stored as today. First symptom: none, until the
  finder is updated and run. The X rows name the known classes (X1 a described password, X2 a spaced key, X3 base64 of
  a key, X5 an unlabelled, unprefixed random secret, X6 an unquoted multi-word passphrase).
- **Silent failure: a false positive.** A span the user wanted is not stored. First symptom: the result's
  `credentials_withheld` names it, at once, in the same call, on every surface that returns a report. The one
  exception is `record_procedure`, whose `str` return is unchanged (§4g): its report is carried by the
  `record_procedure_report` twin and by the served MCP mapping, and its AuditLog event is written either way. Not reversible from the store (the span was never
  written); the caller can rephrase.
- **An ordinary `remember` rewrites legacy history outside 0041 (v0.4.1, dev's N2).** §4c-ii rule 1 withholds a
  legacy span in the prior's note when absorption rewrites it. The current row then carries the placeholder, but the
  prior's earlier journal events keep the raw text until that record is redacted (0041). The change is not reversible
  from the store, by design: the raw span is exactly what the rule withholds.
- **A model reassembles a withheld span.** §4c drops the triple and counts it; §4d refuses it at the edge write if
  §4c were bypassed. Visible in the AuditLog with source `model_output`.
- **Partial failure.** The ingress screen is pure and runs before any write, so a crash inside it writes nothing.
  The derived-write screens (§4c-ii) run later, during composition, inside the composing write's own transaction:
  - `mask()` never raises (§4a's fallback), so the recogniser cannot fail part-way through a write;
  - a refusal there (`correct` over a prior whose `subject` or `relation` carries a shape, §4c-ii row 8) rolls the
    whole transaction back.
    Nothing is written, and the refusal is content-free (§4g E1).

  A provider failure after the ingress screen behaves as today, over withheld text.
- **Reversibility of the remedy.** 0041 redaction is irreversible by design; `veracium credentials redact` requires
  `--yes` and prints what it will redact (ids and classes) first.
- **New attack surface.** The report tells a caller which shapes the screen recognises in text the caller supplied.
  That reveals the rule set, which is public in this spec anyway, and nothing about any stored value.

---

## 8. Claims and limits

**What we will say (CHANGELOG), scoped (v0.4, round 1's R1-08):** *"New memory writes no longer store
credential-shaped text. Keys, tokens, private keys, connection strings with passwords and labelled passwords that the
recogniser names are withheld from what a caller writes, what a model returns, and what is composed from stored
records. This happens before that text is stored or sent to the extractor, under every capability. Text read from
stored records is masked before it goes to a model or into a tool result. The result's `credentials_withheld` lists
what was withheld, by kind, never the value. Not covered: a `recall` or `answer` query, which still reaches the answer
model and the embedder unscreened (it is not stored); `export_memory`, which copies a store as it is; and the declared
snapshots of stored values (journal history; provenance identifiers, dates and an outcome link's inherited
context_ref; contribution-ledger payloads and digests; the request-registry backfill; migration copies), which keep
legacy values until they are redacted or the user is forgotten, as do digests computed over legacy records.
Forgetting a user removes the user's rows from the store. It does not remove the host's audit log, or the
store-level digest of an import file the store converted. `veracium credentials scan` finds what earlier
versions stored, and reports what 0041 redaction can and cannot remove."*

The exceptions sit beside the claim, so a downstream copy of the sentence carries them. Every outward description is
held to §4b's and §4c-ii's screened-input inventory and to this section's exclusions.

**What this does NOT establish:**
- **Not "no secret is ever stored".** The rule is a recogniser of shapes: a described, encoded, spaced, unlabelled or
  foreign-language credential is stored (X1–X6). The claim is "credential-shaped text", and §4a defines the shape.
  A token glued to an ASCII letter or digit is part of a longer word and is stored too (X7, X8; v0.5.7, §4a's token
  boundary).
- **Not protection against a user who wants to store a secret.** Encoding it defeats the rule. The rule is for
  accidental disclosure, and for third-party text that carries credentials.
- **Not a scrub of existing stores.** Rows written before this spec stay at rest until the operator runs the finder and
  0041 redaction; the backstop only masks them on the way to a model or a tool result.
- **Not a scrub of exports or backups** made before, or of `export_memory`'s output now.
- **No restore takes a backup whose identifiers carry a shape (v0.4.1).** The route is a plain import, which refuses
  those records and their dependents and gives up restore's guarantees (§4h).
- **A restore with `withhold_credentials=True` is not byte-faithful** for the records it lists (§4h): their text and
  their row identities differ from the backup's.
- **Queries are not screened in v1.** A credential typed into a `recall` or `answer` query reaches the gate's provider
  **and the embedder** (`__init__.py:713`, `embedder([query])`), though it is not stored. §10 Q4.
- **Linear time is a measured bound, not a proof.** I9 holds on the named adversarial inputs (§4a T1), at the stated
  sizes. No claim is made over inputs not measured. **From v0.5.6 the asserted pair is 1 MiB→4 MiB**, past a
  hardware-dependent cache step between 256 KiB and 1 MiB (the Build section's I9 paragraph), so the 256 KiB→1 MiB
  ratio is a record, not a claim. **The gate's limits, kept explicit (v0.5.8, round 4's answer 6):** a superlinear term with a small constant can stay under 6× at these sizes; a case under the 0.2 s floor is recorded, not ratio-gated; only the named input families are measured; and the two-second ceiling is asserted on the named CI runner only.
- **0041's library receipt keeps ids (v0.5.8, §4g).** `Memory.redact` returns 0041's `RedactionReceipt` to the host with its ids, the host's handle for its next redaction. A legacy shaped id can reach the host through it; what the host does with it afterwards is outside this claim. Its served, CLI and log projections use locators.
- **The declared snapshots keep legacy values until acted on (v0.4; the whole set at v0.5, round 2's R2-04).**
  §4c-ii rule 3 permits each of these unchanged into new rows:
  - the journal's whole-row snapshots, removed by 0041's tombstone of the parent, except text left in the journal of a record redacted before 0041's treatment covered the field: a second redaction writes nothing, so that text stays until `forget_user` (v0.5.8, §4f);
  - an outcome link's inherited `context_ref`;
  - consolidation provenance and dates;
  - contribution-ledger payloads and digests;
  - the request-registry backfill;
  - migration copies of reasons and stamps.

  Provenance identifiers are not removable by 0041 at all (§4f), and digests over legacy records follow their
  records (§4b-ii D2). The finder reports each as a residual. **`forget_user` removes every database row of the
  user**, and nothing outside the database (below). One store-level digest inside the database also survives it: the
  converting import's whole-file digest in `migration_op` (§4f, v0.5.1).
- **Outside the database (v0.4, census E):**
  - the AuditLog file keeps `user_id` in plaintext and counts (never values), and **D3's source identity digest**
    for each revoke or lift of a credential-shaped legacy source, and the same digest as `maintain()`'s pool key in
    each `consolidate-pool` line (v0.5.5). That digest survives `forget_user` (round 2's R2-04 probe). It is the host's
    log, and its handling is outside this API;
  - exports and backups are copies;
  - `origin_user` columns on another user's imported rows are untested;
  - **freed database pages can keep deleted bytes** when SQLite is built without `SECURE_DELETE`. The store never sets
    it; the build on this machine (3.45.1) enables it by default, and other builds may not.
- **A credential used as a `user_id` is outside this spec (v0.4, §4b-ii D4):** the host chooses it, and it is stored
  everywhere `user_id` is.
- **PII is out of scope:** card numbers, national ids and similar are not credentials and are not in the set.
- **Measurements:** the false-positive counts are the reference model's at research's v0.1 evidence commit, on the
  named corpora only. **v0.5.7's token boundary** was measured against v0.5.6's patterns over 2,566,234 units
  (`evidence/boundary_corpus.py`, `out/v057/boundary_corpus.out`): LoCoMo's 5,882 turns and every line of every tracked
  text file of veracium `cee5bcb9` (1,352 files) and the agent harness `18a31344` (16,639 files). No unit changes its
  findings (1,826 are flagged the same by both). The corpora present the condition in 6 units only, all identifiers
  such as `_denied_by_authorization` (`evidence/glued_presence.py`, `out/v057/glued_presence.out`), so the zero says little
  about code that holds vendor prefixes after `_`; the near-miss rows K48–K55 are the constructed evidence for that.

---

## 9. Brief for the external reviewer

**Round 3's verdict (v0.5.1 → v0.5.2): ACCEPT WITH AMENDMENTS** (coordination `eec95f4`, body sha16
`4d136857a0482324`). The design is frozen on I1–I20, with the declared snapshot and digest exceptions, the whole-value
fallback, the identifier refusal and the restore rules. All four round-2 findings are closed, R2-01's design with A1
correcting the scan count. The supersession receipt residual, the fallback, the 0039 line and §4h's placement were
each accepted (answers 1–4).

| item | where | closure, by execution |
|---|---|---|
| A1 the scan bound (LOW) | §4a; §5; I3; I9 | python3 -I -B scan_count.py: the current reference GREEN (passes + 1 scans; five at four-pass completion and at the fallback), v0.5.1's loop RED; every other runner's output byte-identical to v0.5.1's; redos.py re-run with JSON output, its scope stated |
| A2 the map's validation (LOW) | §4b-ii D2; I19 | python3 -I -B digest_map_mutants.py (census F) (v0.5.1's digest_map.py): the map GREEN and byte-identical, eight mutants RED, v0.5.1's script shown passing round 3's reproduction |
| I1's count | §6 I1 | 122 rows, from the vectors (150 at v0.5.7); no claim that they run through product entry points |
| 0039 | §4b-ii D2 | folds with adoption or build, with shaped provider-answer and exception controls |
| 0041 v16.5 | §4h | adopted at veracium `658b73d1`, after the pin; its bytes and the placement are verified at the build pin |
| the finder | §4f | opaque residual digests are reported as declared and unvouched, never inferred absent |

**The build review needs** (round 3's standing artifact questions):
- the implemented invariant matrix;
- RED/GREEN integration evidence, including ordinal ids and SDK validation;
- component and destination digest traces;
- 0041 v16.5's adopted text and the 0039 amendment, at the same pin;
- I9 measured on the named runner.
- Keep this archive layout, the prior verdicts' receipts and the bundled reviewer guide. Record timing sizes, the
  algorithm and the runtime machine-readably; keep the manifests and the digest map's rows duplicate-free; derive
  table totals from the vectors.

**Round 3 (v0.5).** Round 2 returned four focused amendments. R1-01, R1-02 and R1-05 closed at design level, and
the architecture, the owner's rulings and §10 Q7 were not reopened. Each finding is answered:

| finding | where | evidence |
|---|---|---|
| R2-02 D2 by component (HIGH) | §4b-ii D2; §4h; §4f's matrix; I19 | census F (`9abf5ca`): every hash call site, every component, W1–W6; `evidence/digests.json`, generated by digest_map.py, one rule per legacy-capable component |
| R2-01 termination | §4a (the bound is a construction: four passes, then the whole value withheld); §7 | depth_family.py over every delimiter pairing, depths 0–12; rows D3, D4; the fuzz over every pairing; two fallback mutants; I9 re-measured |
| R2-03 counts | §4a (what a report counts); I8 | `vectors.EXPECTED_REPORT`; report_check.py's exact-count check and seven schema-valid count mutants (length-, offset- and span-length-as-count among them); every table row's exact report |
| R2-04 claims | §2's journal row; §4f (`forget_user` scoped to the database; the host AuditLog residual; the receipt residual); §8's CHANGELOG sentence and limits (the whole snapshot set); §10 Q7; `carriers.json` | round 2's probe (as the reviewer ran it); census E |

The small corrections are done as well:
- `invariants.json` writes no totals by hand;
- I6 carries §4h's identifier-under-flag refusal, and I16 keeps `correct`'s refusal;
- D3 cites the shared primitive over the resolved pair;
- §7 names the `record_procedure` twin;
- the restore fixture builds its episode;
- the package bundles `specs/REVIEWER_GUIDE.md`.

**Least sure of, round 3:**
- (1) **The supersession receipt digest is accepted as a residual, not screened.** Screening it would change a frozen
  replay identity (0041 D4). Is listing it in §4f, beside 0041's receipt domain, the right price?
- (2) **The whole-value fallback** withholds all of a field's text when labelled values nest four or more deep. It never
  fires on the corpora or the fuzz, but it is a loss of content on adversarial text.
- (3) **The diagnostics digests become digests of masked provider text.** That is a change to 0039 §2a's fields,
  identical on text with no shape.

**Round 2 (v0.4).** All eight findings of round 1 are answered:

| finding | where | evidence |
|---|---|---|
| R1-01 composed text | §4c-ii | census A; I16 |
| R1-02 echoes and ids | §4g (E1–E3, locators) | census B; I17 |
| R1-03 the remedy's domain | §4f's matrix | census E; I18 |
| R1-04 inertness | §4a (repeat until inert, bounded) | C1–C15, the seeded fuzz, a single-pass mutant |
| R1-05 `record_procedure` | §4g (the library contract) | census D; I20 |
| R1-06 evidence | §6's evidence column, the invariants file, runners that exit nonzero, I8 by schema | the mutants, the report check |
| R1-07 digests | §4b-ii | census C; I19 |
| R1-08 claims | §8 | — |

The recogniser also gained structured-config labels (§4a), answering round 1's reply to Q2.

**Least sure of, round 2:**
- (1) §4c-ii rule 3's snapshot list: is any copy there really composition in disguise?
- (2) §4g E2's reliance on configuring the MCP SDK's own validation errors: the outcome is pinned by I17, the mechanism
  is the build's;
- (3) §4b-ii D3's lookup-before-hash for a legacy source: is the declared digest exception the right price for keeping
  revocation possible?

**Prior rounds' brief:**


- **Least sure of:**
  - (1) the strong/weak label split and the stop list: the weak rule's "looks generated" test is a heuristic, deterministic but chosen;
  - (2) whether *withhold* is right for `dispute`'s `reason` and `record_procedure`'s `summary` (free text), and *refuse* for `corrected_value` (we chose by "is the field compared or joined on");
  - (3) the read backstop's coverage list (§4e): is there a read path toward a model we did not name?
- **Where we may have overstated:**
  - the reach census is name-level (§2c-ii, "What A1–A13 do not show"); I11 is the mechanical answer, but only for public store writers;
  - "linear" is a measurement on 13 adversarial shapes, not a proof over the expressions.
- **What would change our minds:**
  - a store-level single choke point for episodes and replies, which would make §4d total and §4c's canary sufficient;
  - evidence that a host relies on byte-equality between `remember`'s input and the stored episode summary.
- **Reviewer-safe copy:** no generalisation needed; the spec carries no credential and no customer data.

---

## 10. Open questions

1. **Close 0031 §10 Q4 on this surface?** The trust tools' `*_impl` would call `_record("provenance_raises_discarded",
   …)`, and the stock server's `VERACIUM_AUDIT_LOG` (§4g) would make it visible to an operator. It is a text change to
   0031 and three lines of code. **DECIDED, 2026-11-22: the owner, first-hand in the dev session (as dev relays it):
   *"Yes, same build (Recommended)"*.** Folded at v0.3 (§4g, I15). Its scope, ruled the same day: *"Include remember
   and record_procedure (Recommended)"*: all nine `*_impl` (v0.3.1).
2. **An off switch?** v1 has none: a host that wants credentials stored has a password manager. An opt-out would be a
   fail-open default waiting for a misconfiguration. **Owner decides; class: deferred** (revisit on a real host's need).
3. ~~The tool-description sentence (§4j)~~ — **closed at v0.2 by dev's search at `2040a789`:** `remember`'s
   description text is held only by `src/veracium/mcp_server.py` (README, `docs/`, `tests/`, `specs/` and the
   harness's tests have no hits; the harness's `runs/` captures are records, not pins). Re-checked at the build
   commit.
4. **Screen queries before the gate's provider call?** Not storage, but the same egress. Cheap: one call at the top of
   `answer` and `recall`. **Owner decides; class: deferred.**
5. **Telemetry:** should the consented anonymous aggregate carry a count of withheld spans by class? It would need
   `EVENT_FIELDS`, `FIELD_MIN_VERSION` and a telemetry `SCHEMA_VERSION` bump. **Owner decides; class: deferred.**
6. **The default for a restore that carries credentials (§4h, B3).** v0.2 refuses unless
   `withhold_credentials=True` is passed. The alternative is withholding by default with the receipt listing the ids.
   Refusal makes the loss of byte-faithfulness a decision the operator types; withholding by default makes it a line in
   a receipt. **DECIDED, 2026-11-22: the owner, first-hand in the dev session (as dev relays it): *"Refuse unless a
   flag is passed (Recommended)"*.** The default refuses; `withhold_credentials=True` is the operator's typed opt-in
   (§4h, as at v0.2). **Narrowed after the ruling, at v0.4 (round 1's answer to Q1):** the flag withholds free text
   only. A backup whose identifiers carry a shape is still refused under the flag; its route is a plain import (§4h,
   §8). Dev is telling the owner, who ruled on v0.2's wording.
7. **Amend the identity contracts so a credential in a provenance identifier can be removed without erasing the user?**
   (v0.4, round 1's R1-03.) 0041 keeps `source_id`, `evidence_ref`, `context_ref`, reply targets and correlation ids
   by design; they are identities other records join on. Today the finder reports such a match as a residual, and the
   store-wide remedy is `forget_user` (the user's logical database rows; the host's AuditLog is outside it, §4f). A targeted scrub would amend 0006's and 0041's identity contracts and every rule that
   joins on those fields. **Owner decides; class: deferred.** Recommended: keep v0.4's honest residual, and open the
   amendment only if a real store shows such matches.
8. **Should an underscore stop shielding a PIN too?** (v0.5.7.) The ruling on §4a's token boundary covers structural
   tokens. The PIN rule keeps its word boundary, so `CARD_PIN: 4821` and `my_card_PIN=4821` are stored, while the
   same digits after a bare `PIN` label are withheld (row L7; measured on the reference model). Treating `_` as a boundary there would also withhold
   ordinary configuration such as `LED_PIN = 1234`, a pin number on a board. **Owner decides; class: deferred.**
   Recommended: leave the PIN rule as it is; it is narrow by design (K35). **DECIDED, 2026-11-24: the owner,
   first-hand to research: *"Leave it (Recommended)"*.** The PIN rule is unchanged, and `CARD_PIN: 4821` is
   stored, as this question measured.

## Build (2026-11-22 to 2026-11-23, dev)

Built on the owner's word in the dev session (*"Build 0055"*, 2026-11-22), at the tree after `09c2598d`. The design is
unchanged (frozen on I1–I20 at round 3); this section records what the build implements, where, and what it still
owed before the build review (closed at v0.5.4, below). The build's own invariant tests are
`tests/test_0055_recogniser.py` (the recogniser: I1–I3 and I8 on the table, I9), `tests/test_0055_invariants.py` (the
product: I1, I2, I4–I8, I10, I12–I20) and `tests/test_0055_i19_digest_sweep.py` (I19 by the map); I11 is a column in
`tests/test_rii_r2_01_writer_inventory.py`. Round 4's corrections are held by `tests/test_0055_r4_closure.py` (v0.5.8).

**The recogniser** is `src/veracium/credentials.py`. Research's reference model and table are committed beside it as
the oracle (`specs/evidence/0055/reference_model.py`, `vectors.py`, byte copies of research `a07a6910`'s
evidence files) and the product is held equal to the reference on every row and on a seeded fuzz with non-ASCII
adversaries. The product differs only in speed: an ASCII text is its own normalised view; non-ASCII runs that
normalise one for one keep the offset map's segment; and each structural pattern, the labelled rule and the PIN rule
are skipped when a literal every match contains is absent (exact prefilters, checked per pattern and by an
IGNORECASE census over every code point).

**The implemented invariant matrix:**

| invariant | where it is enforced | the build's check |
|---|---|---|
| I1 | §4b's ingress screen in `Memory` (`_cred_ingress`) for every free-text field; the model-output, derived-write and store-guard screens behind it | the table's positive rows through each free-text field (six fields), every text cell of every table scanned |
| I2 | the recogniser's stop list, PIN rule and value tests | every near-miss reaches the extractor and the store byte for byte, no report |
| I3 | `credentials.mask` (four passes, then the whole value) | inertness and text idempotence on every row and the curly family 0–40; the scan count (passes + 1, five at the bound), with v0.5.1's loop held RED |
| I4 | `_cred_ingress`'s identifier refusals, before any digest, check or write | 18 identifier fields, each refused with the store's every row byte-identical before and after |
| I5 | ingest's model-output screen (`_model_triple_class`), the episode summary masked | a stub triple carrying S1's shape: no edge, `extracted_fact` reported, `credential_refused` audited from `model_output` |
| I6 | `portability._credential_screen`, after the procedural pass and before step 1b | plain, restore, restore with `withhold_credentials`, and an identifier under the flag |
| I7 | the read backstop at the renderers (`render_edges`, `clamp_edge_line`, the episode lines, proactive, as-of, contested lines, `why`, `describe_procedures`) and the embedder | a legacy-seeded store; every provider payload and tool result scanned |
| I8 | content-free reports and audit lines; `CredentialRefused`'s message | every sink held to its schema; canaries checked outside the vocabulary; every count the row's exact report |
| I9 | the recogniser | v0.5.6: the named inputs at `I9_SIZES` 256 KiB, 1 MiB and 4 MiB, measured by one routine, `_i9_measure`. **From `f86dc0ea` (v0.5.7 records it, from dev's land report and the routine's docstring):** each round times all three sizes, interleaved, so a burst of another process's load falls on every size alike; per size the thread's CPU minimum over all rounds and the wall median of the first three; five rounds, and a case that reads over `I9_RATIO` and over `I9_FLOOR_S` is measured five more, the minimum over all ten deciding (the record's `rounds`). Why: the gating suite at `c2ecbfd2` (`-n 8`, beside 15 other pytest processes) read `pem_begin_repeated` over 6×; under dev's burst load (12 processes copying 96 MiB, 2 s on and 2 s off) sizes timed one after another read over 6× in 3 of 3 runs, interleaved in 1 of 3, interleaved and re-measured in 0 of 3 (at most 5.57×). The statistic, the 6× assertion, the floor, the ceiling and the quadratic check are unchanged. *(To v0.5.6 this row said: per size the thread's CPU minimum over five runs and the wall median of the first three; wall time under the parallel suite charged other workers' load to one size and read over 6× on a case that reads 4.0–4.6× alone.)* Asserted: the 4 MiB / 1 MiB CPU ratio ≤ 6 (`I9_RATIO`), for each case over `I9_FLOOR_S`, 0.2 s of CPU at 4 MiB (a case under it is recorded, not asserted); and under 2 s of wall time at 1 MiB (`I9_CEILING_S`), on the named runner only. Recorded only: the 1 MiB / 256 KiB ratio (`ratio_256k_1m`). `test_i9_a_quadratic_mask_reads_red` holds a quadratic mutant RED: the product's `mask` plus a scan from the start every 1,024 characters (`I9_QUAD_STRIDE`), on the cases `bearer` and `pem_begin_repeated` (`I9_QUAD_CASES`), read 12.13× / 12.35× and 9.03× / 9.37× in dev's two runs. Only those two, because a fixed-constant quadratic term dominates only where the linear work is small: on the label cases this stride reads under 6× and would prove nothing either way. **Before v0.5.6 this row said "a quadratic mutant of `mask` reads RED" with no tracked check behind it**: it was a scratch copy measured once (veracium `444f82f3`'s message: 8.06–15.92×) |
| I10 | the MCP tool boundary (`_served`) and the adapters' `Binding.call`, both through the library | the positive rows through the served `remember` and an adapter binding, under `none` and `direct` |
| I11 | the writer inventory's screen column | `test_i11_every_writer_is_classed_for_the_credential_screen` |
| I12 | the ingress screen runs first; `_len_sha16` masks provider text | a recording provider (and one whose error echoes the prompt) and a recording diagnostics hook |
| I13 | `_upsert_edge_row`'s guard on INTRODUCED strings (declared site `store.upsert.credential-introduced`) | transitions over a legacy edge succeed; `add_edge` with a shape refuses |
| I14 | the backstop's scope (store-minted values never masked); `preview_token` never screened | the two-step erase through the library and an adapter; a pasted `tt1` token withheld |
| I15 | `_record_discarded` in the nine `*_impl`, before the strip; `VERACIUM_AUDIT_LOG`; the adapters' `audit_log` | the stock server's `build_memory` and an adapter binding |
| I16 | §4c-ii rule 1 at dispute, confirm, record_outcome, correct (before `plan_correction`) and absorption; rule 3's identity refusal in `correct` | legacy values seeded in every copied field; no new row carries one; `correct` refused on a shaped subject |
| I17 | E1 `credentials.outward_text` at the MCP tool boundary, MCP `detail`, the adapters and the CLI; E2 `hide_input_in_errors` on the SDK's argument models; E3 the diagnostics log; §4g's locators | the canary through every served tool, the SDK's validation, an adapter and the CLI; the log masked; a shaped id reported by ordinal and still redacted |
| I18 | `veracium credentials scan|redact` (`credential_finder.py`), the second scan | text, identifier, reply-only and journal-only matches; residual reported, exit nonzero; `forget_user` clears it |
| I19 | D1's order; D3 in `Memory._d3_legacy_source_or_refuse` and the reason check before the digest; the masked `correct` note; the reply digest over masked text; `content_digest` and `_len_sha16` over masked text | the named witnesses, and the map-driven sweep over all 102 (row, component) pairs of `evidence/digests.json` (below); D3's order under the hash tap (`test_d3_the_reason_is_checked_before_the_identity_digest`) |
| I20 | `Memory.record_procedure_report`, `record_procedure`'s `str` unchanged | the library, MCP and the refusal mapping |

**The scope of E1, stated.** E1 names four sinks: a model, a tool result, a CLI stream and the diagnostics log. A
library exception raised to the host that made the call reaches none of them, and its message is unchanged: it is
the host's own argument, returned to the host. Every boundary that carries an exception onward formats it
(`outward_text`: the field, the reason and, for a closed vocabulary, the allowed values). At the CLI the split is by
kind: a refusal (`CredentialRefused`, `ArgumentRefused`, an `OSError` on a supplied path) is that one line with exit
1; any other exception is a defect, re-raised as itself (its type, attributes and traceback) with its message
replaced and its chain suppressed, so a crash still reads as a crash. **From v0.5.8 (round 4's R4-05 and research's S3)** replacing the message is not enough: a Pydantic `ValidationError` formats its stored errors, input included, whatever its message holds, and notes survive a rewrite. So a defect is raised as itself only when its formatting shows the replaced message alone. A `ValidationError` is rebuilt over the same error types, each location reduced and the input hidden, and any other exception with its own formatter is replaced by a fresh one of its class, or by a `RuntimeError` naming it. Notes are dropped (`credentials.withheld_defect`). `outward_text` prints a validation location segment only when it is a list index or a declared field name, and any other segment as `[key]`, because a segment can be a caller's dict key (`Edge.outcome_counts`). The first build's catch-all turned every
exception into the one line, and `specs/evidence/0018/rungs/implementation_mutants.py`'s `CTRL-unrelated-TypeError`
then read KILLED; the record was re-derived after the split. E3's rule is `mask()`, so
the diagnostics log's check uses a credential-shaped canary; the served and CLI checks use census B's plain canary.

**0041 v16.5 at this pin.** The import screen sits after the procedural pass and before step 1b's linkage snapshot,
so 0041 v16.5's quoting-reference rewrite (step 2) runs on screened values, as round 3's answer 4 requires.

**v0.5.7, owed by the next build (dev's chain after `cee5bcb9`).**
- The recogniser takes §4a's token boundary, and `CREDENTIAL_SHAPES_VERSION` becomes 2. The oracle copies (`specs/evidence/0055/reference_model.py`,
  `specs/evidence/0055/vectors.py`) take research's v0.5.7 reference model and table byte for byte, and I9's named inputs gain `glued_short` and
  `glued_body_run` (§4a T1).
- **Disclosed: two §4e masks no product path reaches are removed.** At `85d84928` and `cee5bcb9`,
  `credentials.masked_episode` has no caller in `src/`, and `gate.partition` and `gate.partition_parts` are called only
  by the product's own tests, so their masks guarded nothing a served surface reads. Research's QC of the test harness
  found both as equivalent mutants (M313, M318). §4e's stored episode summaries stay masked where they are read: recall's
  context (`__init__.py`, assertable and fenced) and its no-query briefing (`proactive.py`).

**Owed before the build review: closed 2026-11-23 (v0.5.4).** None changed the design.

*I19's per-row sweep.* `tests/test_0055_i19_digest_sweep.py`, over the instrument and scenarios in
`tests/support_0055_i19.py`, runs every row of the map. The map is `specs/evidence/0055/digests.json`, a byte copy of
research's (v0.5.5's map, research `9f3b9180`; v0.5.4's was tracked at `a07a6910`). The instrument replaces `hashlib.sha256` while an
operation runs and records each digest's input bytes and the veracium frames that computed it. Each map row's census F
site is re-anchored to the function that hashes at this build (a renamed one fails a test). After the operation it reads
every sink: every column of every table, the result, the AuditLog, an export and any diagnostics hook. Each of 131
entries over the map's 102 (row, component) pairs runs twice: a CONTROL with a plain marker, which must reach the site
carrying it (so a clean shaped run is never vacuous), and the SHAPED run with a credential-shaped value planted as legacy
state. The map's rule is judged independently of the entry's pinned observation; a digest carrying the shaped value at
a site the map does not list fails until it is declared. 64 pairs have an entry that behaves exactly as mapped. Every
other observation is stricter than its rule and carries a `MAP:` note in the test naming its mechanism. The findings, for
the build review (the owner's rulings, 2026-11-23, v0.5.5: F1 and F2 declared, F6 fixed, F3-F5 disclosures):
- **I19-F1, a destination the map does not list.** `maintain()` keys each consolidation pool by the scope's identity
  digest (0021 §4b), sha256 over the pool records' (origin, source_id): the value map rows 8 (persisted,
  identifier_kept) and 14 and 34 (compare_only) compute. The key is RETURNED (the host API, the MCP `maintain` tool, an
  adapter's `maintain`) and LOGGED (the AuditLog's `consolidate-pool` event, `pool_key`), neither in census F. For a
  legacy record whose source_id carries a shape, a digest over it reaches a tool result. **Ruled and closed (v0.5.5):**
  declared as a named exception in D3's form (§4b-ii); rows 8, 14 and 34 list both destinations, and the sweep also
  runs row 34 through `maintain()`, where its site computes the same key. The test's `UNDECLARED` is empty.
- **I19-F2, three legacy-capable digest sites census F does not list.** The raw-request digest
  (`contribution.request_digest_under` in `apply_supersession_plan`) hashes a shaped stored user_id before the store
  guard rolls the write back, so it persists nowhere. The import ledger's identity and evidence-ref digests
  (`scope_linkage.reconstruct_absorption_rows`) persist in `contribution_ledger` and see only screened values. **Ruled and
  closed (v0.5.5):** declared in the map as rows 37-39; the sweep runs each, and `UNMAPPED_SITES` is empty.
- **I19-F3, refused after the digest (7 pairs).** `incoming_edge.supersedes` [remember, procedure, correct],
  `incoming_edge.provenance.evidence_ref` [correct], `prior_invalidations[].edge_id` [correct], `prior_upserts[].user_id`
  and `prior_upserts[].invalidation_reason`. The map has identifier_kept or content_residual. At this build the stored
  shaped value is copied into the new row, hashed, then refused by the store guard (I13) or by the closed reasons, and
  the transaction rolls back: the digest exists in memory only.
- **I19-F4, stricter than mapped.** The absorption's rewritten note is screened, not a residual. `refusals[].relation`
  [correct] is refused before planning. `content_digest` masks before hashing at the compare-only sites (rows 29-31).
  The import screen refuses a record before row 17's `target_id`, and before rows 18 and 25 on the import route, and a restore refuses
  whole (I6).
- **I19-F5, unreachable at this build (8 pairs).** `incoming_edge.agreement.markers` [correct] (a closed lexicon);
  `prior_upserts[].subject`, `.relation` and `.object` (the model-output screen drops the incoming triple first);
  `prior_upserts[].provenance.source_id`, row 6's source_id and row 11 (same-scope absorption needs the incoming
  source_id to equal the prior's, and ingress refuses it); row 6's origin (even a plain value: out of scope, or no
  source_id to hash).
- **I19-F6, E1's scope.** The store's refusal of an unregistered invalidation reason (0041 §11.2) quotes the reason, so
  absorbing a legacy prior whose stored prose reason carries a shape raises to the library caller with the shape in the
  message. E1's scope paragraph above assumes a library message carries only the host's own argument; this one carries
  stored text. The MCP boundary (`outward_text`) and the CLI (a defect, its message withheld) do not echo it. **Fixed
  (v0.5.5):** the message masks the reason before quoting it, and so does every store refusal that quotes a stored
  free-text value (seven sites); `tests/test_0055_invariants.py::test_i19_f6_a_store_refusal_masks_the_value_it_quotes`
  is RED without the fix at the four reachable ones.

*I9 on the named runner.* The I9 test records its figures (per case: sizes, wall-clock medians, CPU minima, the
ratio, and from v0.5.6 `ratio_256k_1m` and `floor_s`; the runner, Python, CPU count, `cpu_model` and load) into the
JUnit file as the testsuite property `veracium_0055_i9`.
Each CI lane uploads its `junit.xml` in its `ci-evidence-*` artifact, bound by sha256 in that artifact's
`manifest.json` (`.github/ci_run.py`), so the runner's figures come from CI's own record with no workflow change. The
test asserts the two-second ceiling only there.

*Why the asserted pair moved (v0.5.6; the owner's ruling, first-hand to dev and relayed by dev: "Measure past the step
(Recommended)").* CI run 45275466884, job "pytest (py3.14, 2/5)", went red on v0.5.5's I9 at `85d84928`: on the
256 KiB→1 MiB pair, `label_repeated` read 6.96× (CPU 0.0771 → 0.5364 s) and `label_no_value` 7.24× (0.0708 →
0.5128 s), against 6×, while the other 14 cases read 3.77–4.15× and the runner's load was 0.93. Earlier runs of the same
cases read 4.03–5.38×. Dev's diagnosis on an AMD EPYC 7R13: the recogniser is linear (`label_repeated` about 490 ns a
byte at 128–256 KiB, then 560–650 ns flat from 512 KiB to 8 MiB; 1 MiB→4 MiB grows 4.22× and 4.16×), and the step
stays with garbage collection off, so it is the memory hierarchy, not the code. On that runner the 256 KiB point ran
fast while 1 MiB did not, and the label cases, which allocate the most (every repeat is a finding), straddle the step.
So the ratio is asserted on 1 MiB→4 MiB, past the step; the 256 KiB→1 MiB ratio is recorded; the record adds the
CPU model. With the change, dev's local run (box load about 9) read 3.26–4.95× on the asserted pair, `label_repeated`
4.19× and `label_no_value` 4.20×.

*RED by mutation.* `specs/evidence/0055/implementation_mutants.py` (table `implementation/mutation-table.json`,
checked by `tests/test_0055_implementation_mutants.py`) holds 42 product mutants at the round-5 pin (21 at v0.5.4; v0.5.5 adds I19-F6's; v0.5.7 adds `I1-v056-word-boundary`, the superseded word boundary; round 4's corrections and round 5's own findings add 19: `R4-01-no-type-gate`, `R4-02-cache-unmasked`, `R4-03-receipt-raw-id`, `R4-03-import-refusal-raw-id`, `R4-03-served-receipt-raw-id`, `R4-04-old-text-lists`, `R4-04-unclassified-dropped`, `S1-unparsed-record-skipped`, `S1-named-side-tables-only`, `R4-05-args-rewrite-only`, `S3-dict-key-echoed`, `R4-06-cut-before-screen`, `A1-pool-key-undeclared`, `R5-D3-str-only-gate`, `R5-recall-episode-date-unmasked`, `R5-compile-episode-date-unmasked`, `R5-mask-deep-keys-kept`, `R5-why-find-two-fields` and `R5-journal-after-redaction-removable`), each the RED its invariant's row
names, on the shared protocol: killed by assertion in every named cell, the named cells measured (the cells of the
three 0055 test files that fail under the edit by a qualifying kind), an honest probe passing, a no-op control per
mutated file and a classifier negative control. Two mutants survived the first measurement. Each exposed a gap, closed
in the same change: I7's no-query briefing never rendered its legacy record (the seed was a durable fact and the
briefing renders transient ones), so removing proactive's read mask went unseen; and nothing held D3's reason check
before the identity digest. I20's one failing cell failed by a `KeyError` and now compares by value.

## Review closure

**Round 3 (design), 2026-11-22: ACCEPT WITH AMENDMENTS.** Banked verbatim at coordination `eec95f4`
(`outbox/archive/0055-round3-verdict-verbatim.md`, file sha16 `37c6722505eec65b`, body sha16 `4d136857a0482324`). The design
is frozen on I1–I20. Two LOW amendments remain before `Spec-Status: accepted`. They need no further architectural
review. In the verdict's words, dev records executable closure for them and sets `accepted` only after they are
satisfied (PROCESS §4a). Each closure command runs from `proposals/evidence-0055-credential-shapes/` in research's
repository. v0.5.1's script is `git show 4be8371a:proposals/evidence-0055-credential-shapes/digest_map.py`.

| amendment | folded at | closure command, and what it must print | state |
|---|---|---|---|
| A1 (round 3, accepted with amendments, file sha16 `37c6722505eec65b`): the scan bound (LOW) | v0.5.2: §4a, §5, I3, I9 | python3 -I -B scan_count.py: `current reference: GREEN`, `control (v0.5.1's loop): RED`, `SCAN-COUNT OK`, exit 0; then python3 -I -B redos.py, exit 0, its scope as §4a T1 states | closed internally 2026-11-22 (dev): run on a `git archive` export of research `a07a6910` — scan_count.py exit 0, `current reference: GREEN (0 defects over 163 inputs)`, `control (v0.5.1's loop): RED (98 defects)`, `SCAN-COUNT OK`; redos.py exit 0, `ALL-WITHIN 6.0x` (32/128 KiB ratio evidence only); and the reviewer's own independent_probes.py over v0.5.2's evidence reads at most 5 scans at every depth 0–40 |
| A2 (round 3, accepted with amendments, file sha16 `37c6722505eec65b`): the map's validation (LOW) | v0.5.2: §4b-ii D2, I19 | python3 -I -B digest_map_mutants.py (census F's F-digests.md) (v0.5.1's digest_map.py): the control green and byte-identical, every mutant `RED ok`, both v0.5.1 rows reproduced, `ALL-AS-EXPECTED True`, exit 0 | closed internally 2026-11-22 (dev): run on the same export with v0.5.1's script from `4be8371a` — digest_map_mutants.py exit 0, the control green with the map byte-identical, all eight mutants `RED ok` (exit 1, no map written), both v0.5.1 rows reproduced, `ALL-AS-EXPECTED True`; the reviewer's probe's duplicated census row now exits 1 |
