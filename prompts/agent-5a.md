You are Agent 5A for SkillShift. Implement **workflow adaptation**: Store B requires a shipping category the original Skill never mentioned.

This is ranks 1–3 in one agent. Keep the existing Collections recovery working as code, but the **default transfer demo must highlight shipping**, not the Collections rename.

You MAY write/edit:
- web/app/store-b/page.tsx
- web/app/globals.css (store-b form only)
- web/app/dashboard/page.tsx (status / adapter card copy for the new lesson — keep four cards)
- shared/routes.md (ADD testids only, do not rename existing ones)
- agent/executor.py
- agent/adapter.py
- agent/verifier.py
- agent/recovery.py
- agent/run_transfer.py
- agent/tests/test_transfer.py (extend, don't delete old tests)
- adapters/store_b__publish_product.json
- fixtures/live/dashboard-state.json shape writers in run_transfer
- fixtures/adapter.wrong.json only if needed for shipping-less first adapter

Do not edit: Store A wizard IA, agent/models.py (unless you must add an optional field on EnvironmentAdapter — prefer failure_lessons + extra StepMapping), agent/learner.py, PLAN.md, ARCHITECTURE.md, WAVE*.md, modal/.

Read first: WAVE5.md, agent/run_transfer.py, agent/verifier.py, agent/recovery.py, web/app/store-b/page.tsx (Create Listing form), ARCHITECTURE.md Adapter-only mutation.

Assume SKILLSHIFT_WEB_URL=http://localhost:3010. Keep headed pacing helpers.

## Store B (the new world rule)

On Create Listing, add a required **Shipping category** control:
- data-testid: `store-b-field-shipping`
- Options e.g. Standard / Express / Freight (simple select).
- `store-b-go-live` stays **disabled** (or click shows a visible error) until shipping is set AND name/price/image are set.
- Optional testid `store-b-shipping-blocker` with text like "Select a shipping category to go live."
- Do **not** add shipping to Store A. Skill stays four steps.

## Verifier (new class of mismatch)

When the listing form is visible, Go Live is disabled/blocked, and shipping is empty:

Verification:
- matched = False
- observed_state mentions shipping / publish blocked
- hypothesis: **This environment requires an additional prerequisite that was not part of the original skill.**
- alternative: **Choose a shipping category before Go Live**

This is NOT the Collections hypothesis. Keep Collections verification for the collections screen.

When shipping is set and Go Live enabled / product card visible for the publish step: matched = True.

## Recovery (adapter grows; Skill frozen)

On this workflow mismatch:
- Do **not** rewrite "make the product publicly available" into something else as the only change.
- **Insert** (or append) a StepMapping:
  - semantic_intent: `satisfy environment prerequisite: shipping category`
    (or a short frozen string you reuse everywhere)
  - app_action: `Create Listing > Shipping category`
  - learned_from: `recovery`
- failure_lessons += `Store B requires a shipping category before Go Live`
- Persist adapters/store_b__publish_product.json

intent_to_testids must map that action to `["store-b-field-shipping"]`.
Executor must select a default category (e.g. Standard) then click Go Live.

## run_transfer.py (default story)

1. Skill loaded (unchanged four intents).
2. Navigate Store B via **Inventory → Create Listing** (use recovered UI mapping; skip Collections as the main beat so shipping is visible). You may keep a one-line log that UI mapping was already learned.
3. Fill Leather Bag name/price/image. Attempt Go Live while shipping empty (or verify before selecting).
4. Log:
   - WORKFLOW MISMATCH / missing prerequisite
   - Adapter updated: + shipping category
5. Select shipping, Go Live, Leather Bag card. Hold if headed.
6. write_dashboard_state so Adapter card shows the extra shipping line; Status message includes **Previously learned** only on the second run.
7. Second run (same or new context): Blue Sneaker, **select shipping without failing first**. Log `Previously learned: shipping category required` and `Exploration skipped`.
8. Skill file / skill.steps must still be the original four. Assert that in tests.

## Dashboard

Adapter card must be able to show 3+ mappings (Create item, Shipping, Go Live). Status on recovered: missing prerequisite patched. Status on cached: Previously learned: shipping category required.

## Tests

- Go Live blocked without shipping (Playwright or unit if you expose a helper).
- recover_adapter / workflow recover inserts extra mapping; skill dump unchanged.
- Full run_transfer: first run logs missing prerequisite; persisted adapter has shipping mapping; second run does not need the blocker path.
- Existing Collections unit tests still pass.

No Modal. No Store C. No new LLM keys required.

Done when:
  SKILLSHIFT_WEB_URL=http://localhost:3010 python -m agent.run_transfer
shows Inventory form → Go Live blocked → missing prerequisite → adapter +shipping → Leather Bag live → second run Blue Sneaker with shipping already known.
