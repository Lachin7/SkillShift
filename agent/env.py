"""Load the repo-root .env for CLI runs.

Next.js loads .env itself, so the dashboard Run button always had the key.
A bare `python -m agent.run_transfer` did not — this closes that gap.
Exported variables always win, so `GEMINI_API_KEY=... python -m agent.run_transfer`
still overrides the file.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_env_file(path: Path | None = None) -> list[str]:
    """Set vars from .env without overriding anything already in the environment."""
    target = path or ENV_FILE
    loaded: list[str] = []
    if not target.is_file():
        return loaded
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if not key or key in os.environ:
            continue
        os.environ[key] = value
        loaded.append(key)
    return loaded
