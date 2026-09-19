# `modal_app/` — parallel recovery hypotheses

Modal scores **JSON snapshots** of a Store B mismatch. It does **not** host Next.js and it does **not** open `http://localhost:3010`.

Playwright stays on your machine. Modal only answers: campaign promo (A) vs listing-type bypass (B).

## Setup

```bash
uv pip install modal   # or: .venv/bin/pip install modal
modal setup            # once, human — opens a browser / token
```

## Smoke

From the repo root:

```bash
modal run modal_app/recovery_runner.py
```

You should see candidate **A ✅** (enter `LAUNCH10`) and **B ❌** (Draft listing type).

If `modal` is missing or `modal setup` was never run, `python -m agent.run_transfer` still works: it prints `Modal unavailable — local sequential candidates` and applies the same winner.

## Package name

SDK imports live in `modal_app/`. The old repo folder `modal/` shadowed PyPI `modal` and was renamed to `modal_notes/`.
