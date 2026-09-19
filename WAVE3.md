# Wave 3 — fail, adapt, remember

This is the project. Wave 2 built the two ends (recorder + hands). Wave 3 is the middle:

```text
wrong Adapter (Collections)
        ↓
   execute first step
        ↓
   verifier: expected form vs collections UI
        ↓
   rewrite Adapter only  (Skill stays frozen)
        ↓
   retry Inventory → Go Live
        ↓
   persist adapters/store_b__publish_product.json
        ↓
   second product: exploration skipped
```

Do **not** start all three prompts at once unless you want 3A and 3B in parallel. **3C waits for 3A.**

## How to run (pick one)

### Recommended — one after the other

1. Paste [prompts/agent-3a.md](prompts/agent-3a.md) into a **local** agent. Next.js must be on `http://localhost:3010`.
2. You verify 3A (script shows mismatch → recovery → second run).
3. Then paste [prompts/agent-3b.md](prompts/agent-3b.md) into a new local agent.
4. If time left: [prompts/agent-3c.md](prompts/agent-3c.md) (needs `modal setup`).

### Parallel — two at once

Launch **3A** and **3B** together. They share one file, they do not edit each other's trees.

| | Writes | Must not write |
| --- | --- | --- |
| 3A | `agent/verifier.py`, `agent/recovery.py`, `agent/adapter.py`, `agent/run_transfer.py`, `agent/tests/test_transfer.py`, may edit `agent/executor.py` + `agent/requirements.txt`, writes `adapters/*.json` and `fixtures/live/dashboard-state.json` | `web/**` |
| 3B | `web/app/dashboard/**`, `web/app/api/live-dashboard/**` | `agent/**`, `adapters/**` |

Contract they both already know: [shared/examples/dashboard-state.json](shared/examples/dashboard-state.json) plus `mismatch` / `recovered` / `cached`.

### Solo — one agent does 3A then 3B

Paste [prompts/agent-3-solo.md](prompts/agent-3-solo.md). Slower but no merge. Skip 3C unless that agent finishes early.

## Secrets

| Need | When |
| --- | --- |
| Next.js at `SKILLSHIFT_WEB_URL=http://localhost:3010` | 3A (and 3B to look at it) |
| Playwright Chromium (already installed) | 3A |
| LLM key | Optional. Verifier can be deterministic from `visible_elements` / URL / testids. |
| Modal token (`modal setup`) | **3C only**. Not 3A/3B. |

## Cut-line

If time slips: **ship 3A**. Then 3B. Drop 3C. Never drop mismatch → adapter rewrite → second run.

Modal cannot see `localhost`. 3C must not try to drive Store B from a Modal Sandbox. See the 3C prompt.
