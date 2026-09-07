# 0037 — post-acceptance evidence note (2026-09-07): the package protocol, and what its one omission did not touch

**What this notes.** Every one of 0037's five external-review packages
(rounds 1–5, the accepted package `78a20446b085d7999c14957d373d9793817c0743ffa362665defa043b1094527`
among them) carried in its `tree/` the repository's `specs/REVIEWER_GUIDE.md`,
whose "What green means" section said the archive carries
`collected_header.json`, a machine-verified record checked by
`python specs/verify_extracted.py header`. None of the five archives carried
that file. It is produced by the C-plus protocol of `specs/seal_package.py`
(the 0022/0023, 0024, 0025 and 0026 lines); 0037's packages were built by the
two-seat hand-assembled protocol — `PIN.txt`, `collected/COLLECTED.txt` with
the fresh-clone result line, the named skip delta and the disclosure lineage
beside the raw `-rs` transcript, the spec copy, the tracked-only `tree/`,
`prior-rounds/` and `SHA256SUMS`, verified by the assembly's receipts and by
research's fifteen-assertion `seal_check` — which never produces it. The guide
described the protocol these packages were not built by. Found 2026-09-07 by
the 0038 round-1 external reviewer, who ran the header check because the
guide told them to; corrected in the guide the same day (both protocols named,
which lines use each, the header check marked not applicable to this one).

**What it did not touch — stated so the omission is not read as larger than it
is.** Nothing the 0037 reviewer verified routed through `collected_header.json`.
Across the five rounds their verdicts record checking the outer checksum, every
internal `SHA256SUMS` entry, the byte-identity of the packaged spec copy against
`tree/specs/`, the corpus digest and its bidirectional binding to the spec, and
the pinned revision; at round 5 they ran the test suite independently
("Independent offline run on the recorded Python 3.12.3 / SQLite 3.45.1
runtime: 2,714 passed, 33 skipped"). Each of those checks reads artifacts this
protocol does carry. The acceptance rests on exactly what the verdicts say was
verified; the header would have added a machine-readable record of
`COLLECTED.txt`'s own derivation, which was instead verified by the two seats'
legs and, at round 5, by the reviewer's independent run.

**Whose omission.** Dev's, as the packaging seat: the assembly followed the
runbook's hand-assembled chain without checking the tree's guide against the
archive it described. Recorded here because a reader auditing 0037's acceptance
comes to 0037's record; the 0028 round-3 and 0038 round-2 bundle READMEs carry
the same note because they are the next archives out.
