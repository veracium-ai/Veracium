| model check | §7 row | ids asserted | the table's ids | agrees |
|---|---|---|---|---|
| oracle reach: delegated current (True, True, 'destination', 2) at 1->2 | `C1` | continue | continue | yes |
| oracle reach: delegated internal-error (True, True, 'destination', 2) at 1->2 | `C2` | stop-inspect-committed | stop-inspect-committed | yes |
| oracle reach: write error carrying current (True, True, 'destination', 2) at 1->2 | `E1>C1` | rerun-resumes-store, audit-record-not-published | rerun-resumes-store, audit-record-not-published | yes |
| oracle reach: write error carrying internal-error (True, True, 'destination', 2) at 1->2 | `E1>C2` | stop-inspect-committed, audit-record-not-published | stop-inspect-committed, audit-record-not-published | yes |
| oracle reach: write error carrying adopted (None, None, 'unknown', None) at 1->2 | `E1>K` | stop-inspect-unknown, audit-record-not-published | stop-inspect-unknown, audit-record-not-published | yes |
| oracle reach: write error carrying current (False, False, 'destination', 2) at 1->2 | `E1>U0` | rerun-resumes-store, audit-record-not-published | rerun-resumes-store, audit-record-not-published | yes |
| oracle reach: write error carrying foreign-shape (False, False, 'unaccepted', None) at 1-> | `E1>U1` | no-rerun-not-a-source, audit-record-not-published | no-rerun-not-a-source, audit-record-not-published | yes |
| oracle reach: write error carrying migration-source-missing (False, False, 'missing', None | `E1>U2` | fix-path-then-rerun, audit-record-not-published | fix-path-then-rerun, audit-record-not-published | yes |
| oracle reach: write error carrying migration-source-missing (False, False, 'unaccepted', N | `E1>U3` | conditional-other-writer-or-path, audit-record-not-published | conditional-other-writer-or-path, audit-record-not-published | yes |
| oracle reach: write error carrying newer (False, False, 'unaccepted', None) at 1->2 | `E1>U4` | conditional-other-writer-or-newer-build, audit-record-not-published | conditional-other-writer-or-newer-build, audit-record-not-published | yes |
| oracle reach: write error carrying unsupported-migration (False, False, 'unknown', None) a | `E1>U5` | no-rerun-this-build, audit-record-not-published | no-rerun-this-build, audit-record-not-published | yes |
| oracle reach: write error carrying locked (False, False, 'unknown', None) at 1->2 | `E1>U6` | fix-access-then-rerun, audit-record-not-published | fix-access-then-rerun, audit-record-not-published | yes |
| oracle reach: write error carrying adopted (False, False, 'unknown', None) at 1->2 | `E1>U7` | inspect-first-fallback, audit-record-not-published | inspect-first-fallback, audit-record-not-published | yes |
| oracle reach: a terminal read error | `E2` | inspect-audit-trail | inspect-audit-trail | yes |
| oracle reach: a pre-mint package escape | `E3` | repair-build | repair-build | yes |
| oracle reach: delegated adopted (None, None, 'unknown', None) at 1->2 | `K` | stop-inspect-unknown | stop-inspect-unknown | yes |
| oracle reach: delegated migration-audit-unavailable None at 1->2 | `N1` | rerun | rerun | yes |
| oracle reach: delegated migration-audit-state-unknown None at 1->2 | `N2` | query-id-first | query-id-first | yes |
| oracle reach: delegated migration-quiescence-required None at 1->2 | `N3` | rerun-when-quiescent | rerun-when-quiescent | yes |
| oracle reach: delegated migration-evidence-missing None at 1->2 | `N4` | no-rerun-this-build | no-rerun-this-build | yes |
| oracle reach: preflight current/destination (_preflight_classify L1033) | `P0` | done | done | yes |
| oracle reach: preflight mint-contention/unknown (run_release_migration L1360) | `P1` | rerun-after-contention | rerun-after-contention | yes |
| oracle reach: preflight invalid-request/unknown (_invalid_request L1309) | `P2` | fix-invocation | fix-invocation | yes |
| oracle reach: unexpected-base | `P3` | rerun-when-quiescent | rerun-when-quiescent | yes |
| oracle reach: preflight foreign-shape/unaccepted (_preflight_classify L1044) | `P4>U1` | no-rerun-not-a-source | no-rerun-not-a-source | yes |
| oracle reach: preflight migration-source-missing/missing (_preflight_classify L1004) | `P4>U2` | fix-path-then-rerun | fix-path-then-rerun | yes |
| oracle reach: preflight newer/unaccepted (_preflight_classify L1021) | `P4>U4` | no-rerun-this-build | no-rerun-this-build | yes |
| oracle reach: preflight unsupported-base/source (_preflight_classify L1059) | `P4>U5` | no-rerun-this-build | no-rerun-this-build | yes |
| oracle reach: preflight locked/unknown (_preflight_classify L1014 via _observe L842) | `P4>U6` | fix-access-then-rerun | fix-access-then-rerun | yes |
| oracle reach: delegated current (False, False, 'destination', 2) at 1->2 | `U0` | continue-uncounted | continue-uncounted | yes |
| oracle reach: delegated foreign-shape (False, False, 'unaccepted', None) at 1->2 | `U1` | no-rerun-not-a-source | no-rerun-not-a-source | yes |
| oracle reach: delegated migration-source-missing (False, False, 'missing', None) at 1->2 | `U2` | fix-path-then-rerun | fix-path-then-rerun | yes |
| oracle reach: delegated migration-source-missing (False, False, 'unaccepted', None) at 1-> | `U3` | conditional-other-writer-or-path | conditional-other-writer-or-path | yes |
| oracle reach: delegated newer (False, False, 'unaccepted', None) at 1->2 | `U4` | conditional-other-writer-or-newer-build | conditional-other-writer-or-newer-build | yes |
| oracle reach: delegated unsupported-migration (False, False, 'unknown', None) at 1->2 | `U5` | no-rerun-this-build | no-rerun-this-build | yes |
| oracle reach: delegated locked (False, False, 'unknown', None) at 1->2 | `U6` | fix-access-then-rerun | fix-access-then-rerun | yes |
| oracle reach: delegated adopted (False, False, 'unknown', None) at 1->2 | `U7` | inspect-first-fallback | inspect-first-fallback | yes |
| R3-01 the reviewer's carrier internal-error/False/False/source/13 at 13->14 is U7 | `U7` | inspect-first-fallback | inspect-first-fallback | yes |
| R3-01 the reviewer's carrier migration-failed/False/False/source/13 at 13->14 is U7 | `U7` | inspect-first-fallback | inspect-first-fallback | yes |
| R3-01 the reviewer's carrier migration-result-mismatch/False/False/source/13 at 13->14 is  | `U7` | inspect-first-fallback | inspect-first-fallback | yes |
| R3-01 the reviewer's carrier invalid-store/False/False/unknown/None at 13->14 is U1 | `U1` | no-rerun-not-a-source | no-rerun-not-a-source | yes |
| R3-01 an outcome a later head adds, unchanged, is the fallback U7 | `U7` | inspect-first-fallback | inspect-first-fallback | yes |
| R3-01 pair source-missing/unaccepted (an accepted v12 vs an empty replacement): one conser | `U3` | conditional-other-writer-or-path | conditional-other-writer-or-path | yes |
| R3-01 pair newer (an accepted v15 vs a v17 store): one conservative action for both, U4 | `U4` | conditional-other-writer-or-newer-build | conditional-other-writer-or-newer-build | yes |
| R3-01 walk: an honest v13 walk | `P0` | done | done | yes |
| R3-01 walk: a committed error at rung 2 stops, counted once (C2) | `C2` | stop-inspect-committed | stop-inspect-committed | yes |
| R3-01 walk: a write error with committed success facts (E1, C1: resume the store) | `E1>C1` | rerun-resumes-store, audit-record-not-published | rerun-resumes-store, audit-record-not-published | yes |
| R3-01 walk: a terminal read error (E2), uncounted although the store is at t | `E2` | inspect-audit-trail | inspect-audit-trail | yes |
| R3-01 walk: a postcondition failure (U5): not with the same build | `U5` | no-rerun-this-build | no-rerun-this-build | yes |
| R3-02 pair committed migrated (C1): the escape's store-side ids equal the ordinary record' | `E1>C1` | rerun-resumes-store, audit-record-not-published | rerun-resumes-store, audit-record-not-published | yes |
| R3-02 pair committed internal-error (C2): the escape's store-side ids equal the ordinary r | `E1>C2` | stop-inspect-committed, audit-record-not-published | stop-inspect-committed, audit-record-not-published | yes |
| R3-02 pair unchanged unsupported-migration (U5): the escape's store-side ids equal the ord | `E1>U5` | no-rerun-this-build, audit-record-not-published | no-rerun-this-build, audit-record-not-published | yes |
| R3-02 pair unknown migration-failed (K): the escape's store-side ids equal the ordinary re | `E1>K` | stop-inspect-unknown, audit-record-not-published | stop-inspect-unknown, audit-record-not-published | yes |
| R3-03 a lawful package-inconsistent record at the minted rung, committed (bound, counted) | `E4` | repair-build, stop-inspect-committed | repair-build, stop-inspect-committed | yes |
| R3-03 a record with another outcome (migrated: round 3's defective positive): unbound, not | `E4` | repair-build | repair-build, stop-inspect-committed | yes |
| R3-03 a lawful package-inconsistent record at ANOTHER rung: unbound, not counted | `E4` | repair-build | repair-build, stop-inspect-committed | yes |
| R3-03 a bound package-inconsistent record that did not commit ((False, False, 'destination | `E4` | repair-build | repair-build, stop-inspect-committed | yes |

rows asserted by no cell (0 of 24; listed, not failed): none
ROWMAP checks=57 disagree=0 rows=24 unexercised=0
