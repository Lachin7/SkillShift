# Agent prompts

Paste one file into one agent. Do not give both prompts to the same agent.

Wave 1 (done):

- [agent-a.md](agent-a.md) — owns `web/`
- [agent-b.md](agent-b.md) — owns `agent/`, `fixtures/`, sample `adapters/`

Wave 2 (done):

- [agent-2a.md](agent-2a.md) — Store A recorder (`web/` only). No API key.
- [agent-2b.md](agent-2b.md) — Playwright hands (`agent/executor.py`). No API key. Needs Next.js at `SKILLSHIFT_WEB_URL`.

Wave 3 (now) — see [WAVE3.md](../WAVE3.md) for run order:

- [agent-3a.md](agent-3a.md) — fail / verify / rewrite adapter / second run. **Do this first.** Local. Needs `:3010`.
- [agent-3b.md](agent-3b.md) — live dashboard. After 3A, or in parallel with 3A.
- [agent-3c.md](agent-3c.md) — Modal candidate scoring. After 3A only. Needs `modal setup`.
- [agent-3-solo.md](agent-3-solo.md) — one agent does 3A then 3B.

Context: `CONTRACT.md`, `shared/`, `PLAN.md`, `ARCHITECTURE.md`, `WAVE3.md`. All Wave 3 agents should be **local**.
