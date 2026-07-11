"""Example BYO provider: wrap the `claude` CLI as an engram `Complete` callable.

Shows the bring-your-own-model contract with zero SDK dependency — any callable
with this shape works, including your agent's existing client. This one ignores
`json_schema` (the CLI has no structured-output flag); engram's tolerant JSON
parser handles that, which is exactly why the interface allows it.
"""

from __future__ import annotations

import subprocess
from typing import Optional

# Aligned with the AnthropicComplete reference defaults; override as you like.
ROLE_MODEL = {
    "distill": "claude-haiku-4-5",
    "compile": "claude-sonnet-5",
    "gate": "claude-sonnet-5",
}


class ClaudeCLIComplete:
    def __call__(self, prompt: str, *, system: Optional[str] = None,
                 role: str = "compile", json_schema: Optional[dict] = None) -> str:
        cmd = ["claude", "-p", "--model", ROLE_MODEL.get(role, "claude-sonnet-4-5")]
        if system:
            cmd += ["--append-system-prompt", system]
        p = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=180)
        if p.returncode != 0:
            raise RuntimeError(f"claude CLI failed: {p.stderr[:300]}")
        return p.stdout.strip()
