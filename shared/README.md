# Shared contract

Frozen by Wave 1 setup. **Neither agent edits this folder.**

Read these files before writing code:

| File | What it locks |
| --- | --- |
| [routes.md](routes.md) | URLs, nav, product fields |
| [ownership.md](ownership.md) | Who may write which paths |
| [examples/skill.json](examples/skill.json) | `publish_product` Skill shape |
| [examples/adapter.wrong.json](examples/adapter.wrong.json) | First-guess Store B adapter (`Collections`) |
| [examples/adapter.recovered.json](examples/adapter.recovered.json) | After recovery (`Inventory`) |
| [examples/adapter.cached.json](examples/adapter.cached.json) | Second-run adapter |
| [examples/verification.mismatch.json](examples/verification.mismatch.json) | Expected vs observed miss |
| [examples/trace.store-a.json](examples/trace.store-a.json) | Instrumented demo trace |
| [examples/dashboard-state.json](examples/dashboard-state.json) | Four-card dashboard payload |

Canonical type definitions: [ARCHITECTURE.md](../ARCHITECTURE.md).
Canonical build order: [PLAN.md](../PLAN.md).
Wave 1 prompts: [WAVE1.md](../WAVE1.md).
