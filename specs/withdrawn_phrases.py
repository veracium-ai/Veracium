"""Phrases that have been withdrawn, and must not reappear in a spec.

Four external reviews in a row found withdrawn rules still stated normatively,
each time after the document claimed they had been removed. The failure was
always the same shape: I searched for *my own edits* -- annotation markers, the
sections I remembered touching -- rather than for every place the rule is
stated. A search for one's own corrections cannot find text one never annotated.

So the retraction list is now executable. Each entry is a phrase that was
retracted, the reason, and where the current rule lives.
"""

WITHDRAWN = [
    (r"clears only on (evidence from the )?(the )?same author",
     "R3: only confirm() clears needs_confirmation; no field value does",
     "specs/0008 §3"),
    (r"same author class.{0,40}(clear|evidence)",
     "R3: author class is not source identity",
     "specs/0008 §1"),
    (r"retain prior authorship in a note",
     "the note is rebuilt on every upgrade and survives one hop",
     "specs/0009 §4"),
    (r"falls back to now|fallback to now|keep their (pre-)?existing fallback",
     "malformed dates are rejected; absence is the only thing meaning now",
     "specs/0002 §7f"),
    (r"valid_from = min.{0,30}sole exception",
     "R1: N1 is absolute; min is construction of a new edge",
     "specs/0002 §7c"),
    (r"an audit of every maintenance-time operation",
     "withdrawn in §1; the audit is scoped to the manifest",
     "specs/0002 §8"),
    (r"fixes three provenance defects",
     "0.4.5 ATTEMPTED three; M3 and M4 do not hold",
     "specs/0002 §8"),
    (r"derived from the manifest.{0,40}cannot drift",
     "the evidence-bearing column is hand-authored",
     "specs/0002 §6a"),
    (r"the general form of both advisories",
     "N7 is an end-to-end gate; N9 is the general form",
     "specs/0002 §6"),
    (r"all five findings.{0,20}are closed",
     "M3, M4 and consolidation are unimplemented",
     "specs/0002 §11"),
]
