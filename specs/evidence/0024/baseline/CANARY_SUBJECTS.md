# Canary-subject verification records (EVIDENCE-R15-1)

`canary_subject_records.jsonl` — the 8 cell-C canaries re-run WITH
per-edge subject capture (the field both baseline harnesses omitted —
the disclosed instrument gap).

Honest chain, in order:
1. The original baseline/postfix records carry NO subject field. The
   canary-floor claim in RESULTS_POSTFIX.md's corrections note rested
   on a 2026-08-23 ~22:40Z re-run that PRINTED subjects and persisted
   nothing — the gap-closure had its own instrument gap, caught by the
   external round's EVIDENCE-R15-1.
2. THIS file is a fresh, persisted measurement (2026-08-24, commit in
   each record): all 8 canary subjects are the CLAIMING VOICE ('Apex
   Collections' / literal 'third_party'), never 'user'; all
   third_party_claim/QUARANTINED. It AGREES with the unpersisted run
   on every subject; one benign extraction drift (C07 yielded an edge
   this run, none before — temp-0 nondeterminism, subject still
   claiming-voice, disclosure unchanged).
3. The supported claim: canary subjects are artifact-verified BY THIS
   FILE; the 2026-08-23 stdout run is corroborating history recorded
   in the session transcript, not shipped evidence.
