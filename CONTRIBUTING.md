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
```

## The bar

- **Every behavioral claim maps to a test.** If your change alters what Veracium
  does, the diff includes the test that proves it.
- **PRs touching quarantine, the gate, or supersession must *extend* the eval,
  not just pass it.** These are the load-bearing guarantees; a change that
  weakens them with green tests is the failure mode we care most about. Flag
  such changes explicitly in the PR.
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

## Maintainer release checklist

1. `CHANGELOG.md`: retitle *Unreleased* → version; bump `pyproject.toml`.
2. `pytest` green locally; commit `release X.Y.Z`; `git fetch` then push.
3. `python -m build` + `twine check dist/*` + `twine upload dist/*`.
4. Tag `vX.Y.Z` at the release commit; GitHub Release with the changelog section.
5. Confirm CI green on the release commit.
