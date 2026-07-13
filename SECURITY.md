# Security Policy

Veracium's core premise is that a memory system is a **security boundary**: content
the agent merely *read* (a received email, a fetched document, tool output) must never
become a fact the agent asserts, and one user's memory must never reach another's. So
we treat failures of that boundary as vulnerabilities, not quality bugs.

## What counts as a vulnerability

Report these privately (below), not as public issues:

- **Quarantine bypass** — third-party-authored content becoming an assertable user
  fact (e.g. a claim in a received email surfacing as grounded memory rather than a
  quarantined `third_party_claim`).
- **Abstention-gate bypass** — the answer path asserting an unverified / third-party
  claim as fact instead of abstaining.
- **Cross-`user_id` leakage** — any path by which one user's memory is retrieved,
  compiled, or answered into another user's context.
- **Provenance forgery** — causing content to be stored with a higher trust
  authorship (`USER`/`SYSTEM`) than its true source.
- **Trust-cap bypass ("laundering")** — third-party-influenced content reaching an
  assertable surface despite a correct `derived_from` declaration (the cap is
  structural; it must not depend on the extractor's judgment). Note the converse is
  a *host* responsibility: an event that embeds third-party text but is ingested
  without `derived_from` is a misdeclaration by the caller — see
  `docs/concepts.md` → "Mixed provenance".
- **Unintended data egress** — telemetry or diagnostics transmitting memory content,
  or sending anything without the documented consent gate.

Ordinary bugs, feature requests, and "the LLM gave a weird answer" cases are **not**
security reports — open a regular issue for those.

## Reporting a vulnerability

Please use **GitHub Private Vulnerability Reporting**:
**https://github.com/veracium-ai/Veracium/security/advisories/new**

This keeps the report confidential until a fix is available. Do not open a public
issue or PR for a suspected vulnerability, and please do not disclose it elsewhere
until it is resolved.

A useful report includes: affected version (`veracium --version` / the installed
release), the provider and store in use, a minimal reproduction, and the observed vs.
expected behavior at the boundary above. A failing test against the acceptance eval
(`tests/eval/`) is the ideal artifact — it is exactly how we regression-guard these
guarantees.

## What to expect

- **Acknowledgement:** within 7 days (Veracium is maintained by a small team; we aim
  to be honest about timelines rather than optimistic).
- **Handling:** we confirm, fix on a private branch, add a regression test to the
  eval, then release and publish an advisory.
- **Credit:** reporters are credited in the advisory and CHANGELOG unless you prefer
  otherwise.

## Supported versions

Veracium is pre-1.0. Only the **latest 0.1.x** release receives security fixes; please
reproduce on the latest release before reporting.

| Version | Supported |
|---|---|
| latest 0.1.x | ✅ |
| older | ❌ |

## Scope notes

- **Bring-your-own-LLM / store:** Veracium calls a `Complete` callable and a `Store`
  you supply. Vulnerabilities in *your* model, keys, or database are out of scope;
  vulnerabilities in how Veracium *routes trust* across that boundary are in scope.
- **Redaction is best-effort.** The diagnostics redaction pass reduces, but cannot
  guarantee removal of, sensitive fragments in a log — the real control is the consent
  gate and preview. A redaction miss alone is a hardening issue; an *unconsented send*
  is a vulnerability.
