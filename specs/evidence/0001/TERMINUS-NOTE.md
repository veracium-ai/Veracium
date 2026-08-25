# 0001 evidence machinery — a terminus question (dev, 2026-08-25)

This note asks a scheduling question, not a technical one. **We are not
contesting any finding.** Rounds 11–17 each identified a real bypass in
our evidence machinery, each was reproduced here before fixing, and
each fix is in the package you are reading. The question is what should
happen next, and we would rather ask than discover an eighth seam.

## The arc, stated plainly

Since round 10 the specification has not changed. Every return since
has been in the machinery that evidences the candidate measurement:

| round | finding | what was bound |
|---|---|---|
| 11 | a carried count incremented by inference | the numbers got one producer |
| 12 | the checker bound a projection, not the record | a closed, exactly typed schema |
| 13 | the replay was sound but unprotected | the guard became regression-bound |
| 14 | reachability proved syntactically | the test executes `main()` |
| 15 | the chain was bound link by link, not at the join | the exact argv and cwd |
| 16 | the producer could collapse into a copy of its input | the producer's behaviour |
| 17 | the injected path was bound; production's was not | one path, required runner |

Read together, these have a shape: **bind a thing, and the join to that
thing becomes the next finding.** R15-1 was enforcement→verify; R17-1
was production→implementation. That is not a criticism of the reviews —
each join genuinely was unbound, and two of them (16, 17) would have let
the record vouch for itself. It is an observation about the generator:
every abstraction boundary is a candidate join, and closing one creates
the next.

## What makes this scheduling rather than engineering

Two facts we think bear on the disposition:

**1. The artifact under review is scheduled for deletion.** All of it —
`candidate.patch`, `candidate_results.json`, `measure_candidate.py`,
`check_candidate_results.py`, and the sealer's replay precondition —
exists to evidence the blast radius of a specification that is *not yet
implemented*. On acceptance, 0001 is implemented, the candidate patch
becomes the product change, its sixteen carrier failures become the
implementation work, and this machinery retires. That is not a promise;
the retirement is already built into the SEALING PATH: with the
candidate gone, the sealer's replay precondition returns early, the
extraction checker reports "absent, not broken", and the replay
comparison short-circuits — no gate fails and no package is blocked.
(The producer itself still refuses if invoked by hand with no patch to
measure, which is the right answer to that request; it is simply not on
the sealing path once the candidate is gone. We state this precisely
because our own member test caught the first draft claiming more.)

**2. The implementation is what the acceptance is for.** The sixteen
failing carriers in the candidate measurement are real work on the
product, spread across ten test families — the FORMAT-9 pins, the MCP
author surfaces, the `0018` preflight matrix and the generated
authority tables among them. None of it can start until the status
flips. Each additional hardening round defers that
work to strengthen a scaffold with a scheduled end date.

## What we propose — any of these closes it

**(a) Accept with evidence-maintenance status.** This is your own
disposition for the 0024 A1 amendment at its round 24, and it worked:
the design was approved, and further checker defects became maintenance
rather than acceptance-blocking. The repo now carries the standing
**P1** gate — every evidence artifact must declare and bind an
adversarial mutation matrix, refused otherwise — and **P4**, which
requires closure evidence to run behaviour rather than match text.
Under those gates, a later finding in this machinery is a maintenance
commit, not a review round.

**(b) State the remaining threat model.** If there is a specific class
of bypass still open — one we have not closed and you can name — we
will close it in a single round rather than discovering its members one
seam at a time. We would genuinely rather have the list than the
sequence.

**(c) Rule the machinery out of scope for acceptance.** The candidate
measurement is *supporting evidence* for a blast-radius claim, not part
of the trust model. If its remaining defects cannot change the design
verdict — and since round 10 none has — it may be reasonable to accept
0001 on the specification and treat the scaffold as ours to maintain.

## What we are not asking for

We are not asking you to lower the bar, and we are not asking you to
stop looking. Every finding in this series was legitimate and we would
make each fix again. If you judge that the evidence must be sound
before the status flips regardless of how many seams that takes, say
so plainly and we will keep folding — with the same discipline, and
without asking again.
