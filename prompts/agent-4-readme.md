You are Agent 4 — Judge-facing docs. Do not change app behavior except README/docs.

You MAY write/edit:
- README.md (replace the wave-index with a demo README)
- DEMO.md (create — 2-minute talk track)
- agent/README.md (keep the headed command; don't delete it)

Do not edit: web/app, agent/*.py, shared/, PLAN.md, ARCHITECTURE.md, WAVE*.md.

Read first: PLAN.md north star, WAVE4.md, agent/README.md, README.md.

## Build

1. **README.md** for judges / sponsors (short):
   - One-paragraph claim: Skill = WHAT, Adapter = HOW HERE.
   - How to run locally: Next.js in web/ on 3010, then dashboard Run transfer OR the headed python command.
   - What they will see: teach optional on Store A, mismatch on Collections, rewrite to Inventory, second run skips exploration.
   - Stack: Next.js, Pydantic models, Playwright hands, optional Modal later.
   - Link PLAN.md / ARCHITECTURE.md as "more".
   - Do not list every wave prompt.

2. **DEMO.md** — 2-minute script, timed:
   - 0:00 claim
   - 0:20 Store A (or "we already taught") + mention Rec/Save
   - 0:40 dashboard four cards, Skill frozen
   - 0:50 Run transfer / headed Store B — narrate Collections miss
   - 1:20 Adapter rewrite
   - 1:35 second product, exploration skipped
   - 1:50 one sentence on Modal-if-present or "parallel scratch envs" as future
   - What to have on screen (dashboard Live + headed Chromium)

## Done when

Someone who never saw WAVE*.md can run the demo and give the talk from DEMO.md alone.
