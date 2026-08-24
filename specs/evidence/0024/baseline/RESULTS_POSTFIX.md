# 0024 post-fix probe-paired run — main @ 1b542b9 vs baseline @ 1015e41

**2026-08-23.** Same frozen 48 probes, same classifier, probe-paired.

## The registered obligations

- **Cell A (must move): MOVED CORRECTLY.** A08: third_party_claim/
  QUARANTINED → unclassified/MENTIONABLE with original_relation
  preserved — precisely the specified re-disposition. (Two other
  cell-A probes changed extraction shape — A06/A10 relation drift at
  temp 0, both staying non-quarantined; extraction nondeterminism
  noise, disclosed, not 0024 movement.)
- **Cells C/D (must not move): UNCHANGED.** Canaries all quarantined
  (the fix keys on author==USER, so THIRD_PARTY-authored content never
  enters the coherence path); controls all grounded.
- **Cell B (must not move): 4/16 MOVED — the §8 residual, measured.**
  B06/B08/B10/B14 (boss/accountant/professor/trainer relays whose
  extracted triple subject is "user") de-quarantined:
  third_party_claim/QUARANTINED → unclassified/MENTIONABLE. Mechanism
  exactly as 0024 §8 documents: the subject-only coherence predicate
  cannot distinguish "the user's own words about themselves" from "a
  relay about the user" — B06's note literally reads "Claim made by
  user's boss" while the subject-only test fires anyway. Relay
  protection on this probe set: 14/16 pre-fix → 10/16 post-fix
  (the two pre-existing extractor-path launders B02/B07 unchanged).

## The mitigation and its limit

All four de-quarantined answers retain attribution IN TEXT ("the
boss mentioned…", "according to the professor…") because the relay is
embedded in the extracted content itself. But the STRUCTURAL floor is
gone: downstream maintenance (consolidation, wiki compile,
supersession) now treats these as grounded user facts — textual
attribution is exactly the represent-not-enforce posture the product
exists to reject. Note coverage is partial for any note-based repair:
2 of the 4 have empty notes (the text, not the note, carries the
relay).

## Decision surface (Quentin's word gates the release)

The fix trades: closes the user-words-quarantined defect (A08 class,
1/16 here; provenance-accuracy gain) — opens a measured 4/16
structural de-quarantine of subject=="user" relays (§8's documented,
externally-accepted residual, now sized). Options, dev's design space:
(a) ship as accepted, residual documented with these numbers, #107
(note/author agreement) as the fast-follow that closes B06/B10-class;
(b) interim conservative re-disposition of the incoherent cell to
use_only rather than author-rules (keeps the not-assertable floor,
halves the A-cell gain); (c) hold the 0024 half for #107. Measurement
takes no position; the numbers above are the position.

---

## Corrections (dev's fidelity review + subject re-verification, same day)

1. **My "the fix keys on author==USER" claim was WRONG** — the
   coherence test fires for any author; author rules then set the
   re-disposition (THIRD_PARTY + subject=="user" → use_only is an
   INTENDED §5/R5-1 transition). The C/D stability observed here has a
   different, now artifact-verified cause: **re-ran all 8 canaries
   capturing subjects — every extracted subject is the claiming voice
   ('Apex Collections' / 'third_party'), never 'user'** — so the
   canonical-subject predicate never fires and U1's complementary
   domain holds them quarantined. No U2 contradiction; dev's alarm
   case does not occur in this set. (Instrument note: the original
   runner didn't record subjects — an observability gap now visible;
   any future run of these probes should capture subject per edge.)
2. **Supersession is OUT of the de-quarantine blast radius** —
   unclassified is non-functional and can never supersede. The
   structural loss is one carrier narrower than I stated: assertion
   gate, wiki compile, consolidation treatment.
