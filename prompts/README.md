# Agent prompts

Internal build prompts — **not for judges**. Waves live in [docs/build/](../docs/build/).

Paste one file into one agent. Do not give both prompts to the same agent.

Wave 1 (done):

- [agent-a.md](agent-a.md) — owns `web/`
- [agent-b.md](agent-b.md) — owns `agent/`, `fixtures/`, sample `adapters/`

Wave 2 (done):

- [agent-2a.md](agent-2a.md) — Store A recorder (`web/` only). No API key.
- [agent-2b.md](agent-2b.md) — Playwright hands (`agent/executor.py`). No API key. Needs Next.js at `SKILLSHIFT_WEB_URL`.

Wave 4 (demo polish) — see [WAVE4.md](../docs/build/WAVE4.md):

- [agent-4-cockpit.md](agent-4-cockpit.md) — Run button, persist Store B products, show trace. **Do first.**
- [agent-4-optics.md](agent-4-optics.md) — Decoy copy, Rec as SkillShift, quieter dashboard.
- [agent-4-readme.md](agent-4-readme.md) — Judge README + DEMO.md talk track.
- [agent-demo-pace.md](agent-demo-pace.md) — Already done (headed pauses).

Wave 3 — see [WAVE3.md](../docs/build/WAVE3.md) for run order:

- [agent-3a.md](agent-3a.md) — fail / verify / rewrite adapter / second run. **Do this first.** Local. Needs `:3010`.
- [agent-3b.md](agent-3b.md) — live dashboard. After 3A, or in parallel with 3A.
- [agent-3c.md](agent-3c.md) — Modal candidate scoring. After 3A only. Needs `modal setup`.
- [agent-3-solo.md](agent-3-solo.md) — one agent does 3A then 3B.

Wave 5 (procedural adaptation) — see [WAVE5.md](../docs/build/WAVE5.md):

- [agent-5a.md](agent-5a.md) — Store B shipping prerequisite + heal + remember. **Do first.**
- [agent-5b.md](agent-5b.md) — Same-env replay on Store A. After 5A.
- [agent-5-solo.md](agent-5-solo.md) — 5A then 5B in one chat.

All Wave 5 agents should be **local**. Next.js on `:3010`. Do not run 5A and 5B in parallel.

Wave 6 (campaign promo + Modal) — see [WAVE6.md](../docs/build/WAVE6.md):

- [agent-6a.md](agent-6a.md) — Campaign / promo gate on Store B. **Do first.**
- [agent-6b.md](agent-6b.md) — Modal parallel hypotheses for promo. After 6A.
- [agent-6-solo.md](agent-6-solo.md) — 6A then 6B in one chat.

Wave 7 (real agent pipeline — after R1 grounding) — see [WAVE7.md](../docs/build/WAVE7.md) and [skillshift_build_brief.md](skillshift_build_brief.md):

- [agent-7a.md](agent-7a.md) — `observe_app` + test-only Store B state API. **Do first.**
- [agent-7b.md](agent-7b.md) — Independent verifier + failure diagnoser. After 7A.
- [agent-7c.md](agent-7c.md) — `AdapterPatch` curator. After 7B.
- [agent-7d.md](agent-7d.md) — Metrics / reuse_gain + naive replay baseline. After 7C.
- [agent-7e.md](agent-7e.md) — Modal scores diagnoser hypotheses (not hardcoded LAUNCH10). After 7C; parallel with 7D.
- [agent-7f.md](agent-7f.md) — Dashboard trace of the real loop. Last.
- [agent-7-solo.md](agent-7-solo.md) — 7A–7D in one chat; 7E/7F if time.

Do not run 7B before 7A. Keep Skill intents frozen. Live path stays empty-adapter + Explorer (R1).

Wave 8 (wow factor: more environments, live perturbation) — see [WAVE8.md](../docs/build/WAVE8.md):

- [agent-8a.md](agent-8a.md) — Judge perturbs Store B from the browser (rename / extra required field / reorder). **Do first.**
- [agent-8b.md](agent-8b.md) — `agent/targets.py` app registry, then Store C (table + status dropdown, no publish button). Refactor step must be green on Store B first.
- [agent-8c.md](agent-8c.md) — Store D, Japanese labels, same structure as B. After 8B.
- [agent-8-solo.md](agent-8-solo.md) — 8A → 8B → 8C in one chat.

All Wave 8 agents local, Next.js on `:3010`. Do not run 8B alongside a Wave 7 agent (same `agent/` files). Nobody but 7F edits `web/app/dashboard/**`.
