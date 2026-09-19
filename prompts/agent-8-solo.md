# Agent 8 solo — Wave 8 in one chat

Read [WAVE8.md](../docs/build/WAVE8.md), then execute in this order, committing between each:

1. [agent-8a.md](agent-8a.md) — judge-controlled perturbation of Store B.
2. [agent-8b.md](agent-8b.md) — `agent/targets.py` refactor, then Store C. **Step 1 of 8B must be green on Store B before you write any Store C UI.**
3. [agent-8c.md](agent-8c.md) — Store D (Japanese). Only after 8B.

Rules:

- Local only. Next.js on `:3010`. Real key for the final runs; `SKILLSHIFT_MOCK_LLM=1` for tests.
- Skill intents stay frozen. No hardcoded HOW HERE in the live path, in any app.
- Do not touch `web/app/dashboard/**` (Agent 7F owns it).
- After each agent: `pytest agent/tests` and `cd web && npx tsc --noEmit && npm run build` (there is no `lint` script).
- If you run out of time, ship in the order above. 8A alone is already a strong demo beat; Store C without Store D is fine; Store D without 8B's refactor is not possible.

Stop and report if Store B's cold or cached run regresses at any point — that is the spine of the demo and takes priority over every Wave 8 addition.
