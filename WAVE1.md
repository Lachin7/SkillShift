# Wave 1 — two independent agents

Do not start Wave 2 until you have verified both outputs. You are the merge gate.

```text
Agent A  writes  web/                 fake stores + dashboard shell
Agent B  writes  agent/ fixtures/ adapters/*.json
shared/          is frozen            both only read it
```

## Before you launch

Each agent must read, in order:

1. [CONTRACT.md](CONTRACT.md)
2. [shared/ownership.md](shared/ownership.md)
3. [shared/routes.md](shared/routes.md)
4. [ARCHITECTURE.md](ARCHITECTURE.md)
5. The prompt in this file for that agent only

They must not edit `PLAN.md`, `ARCHITECTURE.md`, `CONTRACT.md`, `WAVE1.md`, or `shared/`.

---

## Agent A prompt

Copy everything in the block below into a new agent.

```text
You are Agent A for SkillShift Wave 1. You own ONLY web/.

Do not edit: agent/, fixtures/, adapters/, shared/, inspo/, modal/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE1.md.

This is a hackathon research demo, not a SaaS. Build a minimal Next.js app so a human can publish a product in two fake stores, and so a four-card dashboard can show Skill vs Adapter from static JSON.

Read first (do not rewrite them):
- CONTRACT.md
- shared/ownership.md
- shared/routes.md
- shared/examples/dashboard-state.json
- shared/examples/dashboard-state.mismatch.json
- PLAN.md step 1
- ARCHITECTURE.md sections "Fake stores" and "Dashboard contract"

Build:
1. Next.js app in web/ (App Router, TypeScript).
2. /store-a — multi-step seller wizard: Products → Add Product → Media → Publish. After Publish, show a visible product card. Use product fields name, price, image. In-memory / client state only.
3. /store-b — different IA: nav is Collections, Inventory, Orders. Product creation is Inventory → Create Listing (single-page form). Finish action is "Go Live". Collections is a plausible decoy (collection management, NOT product creation) and should include a Create action so an explorer can pick it first. After Go Live, show a product card.
4. Put the data-testid values from shared/routes.md on the real controls.
5. /dashboard — four cards side by side: Learned Skill, Current App, Adapter, Status. Render from static JSON copied into web/ (e.g. public/dashboard-state.json). Support phases mismatch | recovered | cached. In mismatch, the Create item mapping is red (Collections). Include a simple control to flip fixture phase so we can demo the visual without a live agent.
6. Home page with links to Store A, Store B, Dashboard.

Must not: recorder events, Playwright, Python, Modal, auth, database, extra commerce features.

Optional visual inspiration only (do not copy their stack): inspo/understudy.

Done when:
- A human can publish in Store A and see a product card.
- A human can publish in Store B via Inventory → Create Listing → Go Live and see a product card.
- Store B Collections is clearly not product creation.
- /dashboard shows the four cards from fixtures, including a red mismatch mapping.
```

---

## Agent B prompt

Copy everything in the block below into a new agent.

```text
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
```

---

## Verify (you, before Wave 2)

| Check | Agent |
| --- | --- |
| Store A publish → product card | A |
| Store B Inventory path → product card | A |
| Store B Collections is a trap | A |
| Dashboard 4 cards + red mapping | A |
| `data-testid` values match `shared/routes.md` | A |
| Skill has no click-the-button wording | B |
| Adapter is a separate object from Skill | B |
| Learner works with no API key | B |
| Dashboard fixture fields still match B's schemas | both — fix fixtures, not stores |

If dashboard JSON drifted from `shared/examples/`, fix the copy in `web/`. Do not change `shared/`.

---

## Wave 2 (do not assign yet)

After both pass: instrument Store A (recorder) and a Playwright executor against Store B. Still split by directory: recorder in `web/`, executor in `agent/executor.py`.
