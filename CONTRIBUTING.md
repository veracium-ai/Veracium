# Contributing to Veracium

Thanks for your interest. Veracium is small and opinionated; contributions that
fit its discipline land quickly.

## Dev setup

```bash
git clone https://github.com/veracium-ai/Veracium.git && cd Veracium
python -m venv .venv && .venv/bin/pip install -e ".[dev,mcp]"
.venv/bin/pytest                       # fast, offline, deterministic
```

To exercise the live guarantees against a real model (optional, costs tokens):

```bash
veracium selfcheck                     # needs a provider, e.g. ANTHROPIC_API_KEY
VERACIUM_EVAL=1 pytest tests/test_eval.py            # acceptance eval
VERACIUM_ROBUSTNESS=1 pytest tests/test_robustness.py  # robustness tier
PYTHONPATH=src python bench/run_bench.py               # internal benchmark (see bench/README.md)
```

## The bar

- **Every behavioral claim maps to a test.** If your change alters what Veracium
  does, the diff includes the test that proves it.
- **PRs touching quarantine, the gate, or supersession must *extend* the eval,
  not just pass it.** These are the load-bearing guarantees; a change that
  weakens them with green tests is the failure mode we care most about. Flag
  such changes explicitly in the PR.
- **Every shipped capability gets a short example** — a recipe in
  `docs/recipes.md` (copy-pasteable, <15 lines) lands in the same PR/release
  as the feature. A feature without an example isn't done.
- CI (py3.10–3.13 + packaging check) must be green; `main` requires it.

## Wanted

- **`Store` backends** — Postgres, Neo4j, … (implement the `Store` interface;
  the sqlite backend is the reference).
- **`Complete` providers** — worked examples for other model APIs (see
  `examples/claude_cli_provider.py` for the contract: any callable works).
- **MCP client recipes** — configs for agents/IDEs speaking to the Veracium MCP
  server.
- Docs fixes, always.

## Security

A quarantine bypass, gate bypass, or cross-user leak is a **vulnerability**, not
a quality bug — see [SECURITY.md](SECURITY.md) and report privately.

## Specifications

Changes to **stored state, its semantics, its trust or disclosure classes, its
lifecycle, or how it is selected for recall** need a spec before implementation
— see `specs/PROCESS.md` and `specs/TEMPLATE.md`. Docs, tests, CI, packaging and
behaviour-preserving refactors do not.

Commits touching the trust surface carry a `Spec:` trailer, and CI checks for it
(`specs/check_spec_reference.py`). The exemption is deliberate and visible:

    Spec: specs/0007-generated-content-trust-class.md
    Spec: none (docs-only change to a guarded file)
    Spec: none (hotfix — GHSA-xxxx, retrospective review per PROCESS.md)

## Maintainer release checklist

0. **Re-read open asks addressed to you since your last entry.** A trust-boundary
   review sat unread for eight hours and the release that followed needed a
   published advisory. Two minutes.
1. `CHANGELOG.md`: retitle *Unreleased* → version; bump `pyproject.toml`.
   Run the bench (`bench/run_bench.py --live` then `--compare`): no hard
   regressions; soft flags need a written justification in the notes.
2. `pytest` green locally; commit `release X.Y.Z`; `git fetch` then push.
3. `python -m build` + `twine check dist/*` + `twine upload dist/*`.
4. Tag `vX.Y.Z` at the release commit; GitHub Release with the changelog section.
5. Confirm CI green on the release commit.
