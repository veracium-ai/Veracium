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

    # --- 0003 -------------------------------------------------------------
    dict(spec="0003", round=1, kind="internal", date="2026-08-01", verdict="adopted", findings=None),
    dict(spec="0003", round=1, kind="external", date="2026-08-02", verdict="deferred", findings=8),
    dict(spec="0003", round=2, kind="external", date="2026-08-02", verdict="deferred", findings=12),
    dict(spec="0003", round=3, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for cleanup", findings=5),
    dict(spec="0003", round=4, kind="external", date="2026-08-02", verdict="narrow design approved; deferred for retrieval fix", findings=5),
]
