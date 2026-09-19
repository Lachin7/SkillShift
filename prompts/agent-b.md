You are Agent B for SkillShift Wave 1. You own ONLY agent/, fixtures/, and sample JSON under adapters/.

Do not edit: web/, shared/, inspo/, modal/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE1.md.

This is a hackathon research demo, not a SaaS. Implement the typed Skill / Adapter layer so a demonstration trace becomes an app-agnostic Skill. No browser.

Read first (do not rewrite them):
- CONTRACT.md
- ARCHITECTURE.md "Typed models"
- shared/examples/*.json
- PLAN.md steps 3–4

Inspiration (read structure only, do not port their runtime or download checkpoints):
- inspo/ShowUI-Aloha — recorder → semantic trace
- inspo/UI-Mate — demo is advice, not a script
- inspo/EvoSkill-GUI — plan / recovery / failure as separate objects
- inspo/pydantic-ai — typed agent outputs

Build:
1. agent/models.py — Skill, SkillStep, EnvironmentAdapter, StepMapping, Verification, TraceEvent exactly as in ARCHITECTURE.md. learned_from is Literal["exploration", "recovery", "cached"].
2. agent/learner.py — function that takes a list of TraceEvent (screenshot paths may be placeholders) and returns a Skill. Prefer a multimodal Pydantic AI agent if an API key exists in the environment. MUST fall back to a deterministic mapping from the Store A trace → publish_product with the exact intents in shared/routes.md when no key is present. The Skill must contain ZERO app-specific clicks ("click Products", "click Publish" are failures).
3. Copy shared examples into fixtures/ as needed. Screenshot paths may stay as placeholders.
4. Write adapters/store_b__publish_product.json from shared/examples/adapter.recovered.json.
5. Also keep fixtures for: wrong adapter (Collections), recovered adapter, cached adapter, mismatch Verification.
6. A tiny pytest (or a script) that: loads models; runs the learner on the Store A fixture trace; asserts skill.name == "publish_product"; asserts no step.intent contains "click".

Must not: Next.js, Playwright, Modal, live websites, OmniParser.

Done when those tests pass without an API key, and the Skill intents match shared/routes.md.
