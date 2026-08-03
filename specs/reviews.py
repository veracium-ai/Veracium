"""Every review round, across every spec. One source.

Review counts were previously stated in three places -- `findings.py REVIEWS`
(0002 only, and it stopped at v5 while a sixth disposition sat in the document),
a hand-written table in 0003, and prose in both. The seventh review of 0002
caught the first; the second review of 0003 caught the others.

`kind` distinguishes who reviewed:
  internal  another session (research / workflow-platform) -- never the author
  external  the trusted third-party reviewer

`findings` is the count RAISED by that round, not the count outstanding.
"""

REVIEWS = [
    # --- 0001 -------------------------------------------------------------
    dict(spec="0001", round=1, kind="internal", date="2026-07-31", verdict="revise", findings=None),
    dict(spec="0001", round=1, kind="external", date="2026-07-31", verdict="deferred", findings=None),
    dict(spec="0001", round=2, kind="external", date="2026-08-01", verdict="deferred", findings=None),

    # --- 0002 -------------------------------------------------------------
    dict(spec="0002", round=1, kind="internal", date="2026-07-31", verdict="revise", findings=None),
    dict(spec="0002", round=2, kind="internal", date="2026-08-01", verdict="revise", findings=None),
    dict(spec="0002", round=1, kind="external", date="2026-08-01", verdict="deferred", findings=9),
    dict(spec="0002", round=2, kind="external", date="2026-08-01", verdict="deferred", findings=10),
    dict(spec="0002", round=3, kind="external", date="2026-08-01", verdict="deferred", findings=7),
    dict(spec="0002", round=4, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0002", round=5, kind="external", date="2026-08-02", verdict="deferred", findings=11),
    dict(spec="0002", round=6, kind="external", date="2026-08-02", verdict="deferred", findings=10),
    dict(spec="0002", round=7, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0002", round=8, kind="external", date="2026-08-02", verdict="deferred", findings=11),

    # --- 0008 -------------------------------------------------------------
    dict(spec="0008", round=1, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred", findings=7),
    dict(spec="0008", round=2, kind="external", date="2026-08-02", verdict="clearing rule approved; liveness rule rejected", findings=11),
    dict(spec="0008", round=3, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred on the storage and API contract", findings=8),
    dict(spec="0008", round=4, kind="external", date="2026-08-02", verdict="clearing rule approved; deferred on episode inputs, idempotency and 0007", findings=9),

    # --- 0007 -------------------------------------------------------------
    dict(spec="0007", round=1, kind="external", date="2026-08-02",
         verdict="design direction approved; deferred on the shape comparison", findings=12),
    dict(spec="0007", round=2, kind="external", date="2026-08-02",
         verdict="direction approved; deferred; S-Q4 answered — known-constructor equality", findings=10),
    dict(spec="0007", round=3, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred on the manifest mechanics; S-Q5 resolved", findings=9),
    dict(spec="0007", round=4, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred for a truthful generator; S-Q6 resolved", findings=8),
    dict(spec="0007", round=5, kind="external", date="2026-08-02",
         verdict="architecture approved; deferred; instrument split adopted", findings=8),
    dict(spec="0007", round=6, kind="external", date="2026-08-03",
         verdict="architecture approved; deferred; migration self-authorisation found", findings=8),
    dict(spec="0007", round=7, kind="external", date="2026-08-03",
         verdict="architecture approved; deferred; destination contract contradicted itself", findings=8),
    dict(spec="0007", round=8, kind="external", date="2026-08-03",
         verdict="scope cut approved; deferred; the cut broke 0008's prerequisite", findings=5),
    dict(spec="0007", round=9, kind="external", date="2026-08-03",
         verdict="narrowed design approved; deferred; fabrication and atomicity", findings=3),
    dict(spec="0007", round=10, kind="external", date="2026-08-03",
         verdict="core design approved; deferred; artifact conflicts and the unbuildable union", findings=3),
    dict(spec="0007", round=11, kind="external", date="2026-08-03",
         verdict="core spec approved; deferred; identity, attestation and a regressed guard", findings=3),
    dict(spec="0007", round=12, kind="external", date="2026-08-03",
         verdict="architecture approved outright; S-Q7 ruled; deferred on runtime-evidence validation", findings=3),
    dict(spec="0007", round=13, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred on monotonicity, totality and stale-record scoping", findings=3),
    dict(spec="0007", round=14, kind="external", date="2026-08-03",
         verdict="ACCEPTED — v16 approved for acceptance; three non-blocking corrections", findings=0),

    # --- 0013 -------------------------------------------------------------
    dict(spec="0013", round=1, kind="external", date="2026-08-03",
         verdict="architecture approved directionally; deferred; M-Q2 ruled adopt-with-conditions", findings=7),
    dict(spec="0013", round=2, kind="external", date="2026-08-03",
         verdict="concrete migration approved; deferred; integration, evidence, offline boundary", findings=4),
    dict(spec="0013", round=3, kind="external", date="2026-08-03",
         verdict="concrete v1→v2 approved directionally; deferred; one planner, prior evidence, qualified confinement, total outcomes; M-Q2 ruled at the library boundary", findings=4),
    dict(spec="0013", round=4, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred; evidence totality, artifact-wide cardinality, probe soundness, authority lifecycle", findings=5),
    dict(spec="0013", round=5, kind="external", date="2026-08-03",
         verdict="architecture standing; deferred; monotone evidence writes, operation-level consumption, exact scalar typing, outermost boundary", findings=4),
    dict(spec="0013", round=6, kind="external", date="2026-08-03",
         verdict="approved architecture restated; deferred; migrate-only planner mode, serialized publication, Unicode-safe boundary, audit state machine, immutable release identity", findings=5),
    dict(spec="0013", round=7, kind="external", date="2026-08-03",
         verdict="mode, publication and boundary held; deferred; evidence snapshot binding, framed full-length identity, two-table audit machine, static source resolution, truthful internal-error", findings=5),

    # --- 0003 -------------------------------------------------------------
    dict(spec="0003", round=1, kind="internal", date="2026-08-01", verdict="adopted", findings=None),
    dict(spec="0003", round=1, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0003", round=2, kind="external", date="2026-08-02", verdict="deferred", findings=12),
    dict(spec="0003", round=3, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for cleanup", findings=5),
    dict(spec="0003", round=4, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for retrieval fix", findings=5),
    dict(spec="0003", round=5, kind="external", date="2026-08-02", verdict="narrow design approved; deferred — duplicated sections, ladder not runtime-grounded", findings=7),
]
