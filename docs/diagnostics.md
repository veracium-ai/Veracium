# Diagnostics — opt-in error reporting

When engram hits a **genuine error**, it can send its local log to the maintainers
so the bug can be diagnosed. This is a **separate, more careful channel** than
[telemetry](telemetry.md): telemetry is content-free by construction, but a *log*
can incidentally contain fragments of memory content (e.g. inside an exception
message). So error reporting is local-first and never sends without consent.

## How it works

1. **Local first.** When a reporter is attached, genuine errors from `remember` /
   `recall` / `answer` / `maintain` are written to a local, user-owned rotating log
   file — *and the original error is re-raised unchanged.* Reporting is strictly
   additive; it never swallows or delays the real exception.
2. **Sending is consented.** A log is transmitted only with **advance permission**
   (opt-in auto-send) **or** an explicit per-incident "yes". Default: neither.
3. **Transparent + redacted.** `preview` shows exactly what would be sent. A
   redaction pass (on by default) scrubs emails, phone/account/card-like number
   runs, and grouped amounts from the tail first. Redaction is best-effort — the
   real safeguard is that *you see the payload and choose*.
4. **Anonymous + bounded.** A random install id (shared with telemetry if you have
   one), minimal environment (engram / python / os), and only the log **tail** up
   to a byte cap (default 64 KB).
5. **No endpoint shipped.** engram bundles no URL, so even "enabled" sends nothing
   until an endpoint is configured.

## What a report contains

```json
{
  "schema_version": 1,
  "install_id": "<random>",
  "reason": "manual | auto:<op>",
  "engram_version": "0.1.0",
  "python": "3.12.3",
  "os": "Linux",
  "redacted": true,
  "log_tail": "…the last N KB of the local error log, redacted…"
}
```

`log_tail` is the sensitive part. It is engram's own log lines — timestamps, the
operation that failed, a hashed user id, and the Python traceback. Tracebacks show
engram's source lines (not memory content); the residual risk is an **exception
message** that quoted a value, which is why redaction + preview + consent apply.
Raw user ids are never logged — only a truncated SHA-256 hash of the id.

## CLI

```bash
engram diagnostics status      # setting + resolved log path
engram diagnostics path        # just the log file location
engram diagnostics preview     # EXACTLY what a report would send (redacted)
engram diagnostics report      # send the current log now — asks first, shows the preview

# advance permission (auto-send on future errors):
engram diagnostics prompt      # the consent question
engram diagnostics enable --endpoint https://your-collector.example/report
engram diagnostics disable     # revoke send (local logging is unaffected)
```

The MCP server attaches a reporter automatically (local logging on). Because its
stdio transport isn't a terminal it never prompts and never auto-sends unless you
granted advance permission with `engram diagnostics enable`; otherwise the log
stays local until you run `engram diagnostics report`.

## Embedded in a host application

The host decides whether engram manages a log at all, and owns the consent UX.

```python
from engram import Memory
from engram import diagnostics

reporter = diagnostics.load_reporter()          # None if local logging is disabled
mem = Memory(llm=your_llm, diagnostics=reporter)

try:
    mem.remember(user_id, text)
except Exception:
    # engram already logged it locally and re-raised. Offer to report:
    preview = mem.diagnostics_preview()         # show the user what would be sent
    if user_agrees:
        mem.report_error(interactive=False)     # sends iff an endpoint is configured
    raise
```

- `mem.report_error(interactive=…)` — send the captured log, subject to consent
  (advance permission, or an interactive yes). No-ops if nothing was captured or no
  endpoint is set; never raises.
- `mem.diagnostics_preview()` — the exact (redacted) payload, or `None` if off.

If you granted advance permission (`diagnostics.set_report_enabled(True,
endpoint=…)`), engram auto-sends on error — throttled so an error loop can't flood
the endpoint.

## Config file

Stored at `$XDG_CONFIG_HOME/engram/diagnostics.json`; the log defaults to
`$XDG_STATE_HOME/engram/engram.log` (override with `log_path`). Fields:
`{log_enabled, report_enabled, prompt_on_error, redact, endpoint, log_path,
install_id, max_report_bytes, report_min_interval_s, last_report}`. Set
`log_enabled: false` to turn off local logging entirely.

## Guarantees, restated

1. The real error is always re-raised; reporting never hides a failure.
2. Nothing is sent without consent (advance permission or an explicit yes).
3. You can see the exact payload first (`preview`); redaction is on by default.
4. Anonymous (random install id); no raw user ids in the log.
5. A reporting failure never affects memory (the reporter never raises).
