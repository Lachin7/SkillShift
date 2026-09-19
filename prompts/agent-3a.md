You are Agent 3A for SkillShift Wave 3. You own the Python transfer loop.

You MAY write/edit:
- agent/verifier.py
- agent/recovery.py
- agent/adapter.py
- agent/run_transfer.py
- agent/tests/test_transfer.py
- agent/executor.py (you MUST relax the Wave 2 Collections ban for the *first* attempt only)
- agent/requirements.txt
- adapters/*.json
- fixtures/live/dashboard-state.json (create fixtures/live/)

Do not edit: web/, shared/, inspo/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE*.md, agent/models.py, agent/learner.py.

This is a hackathon research demo. Everything exists to prove: a Skill learned in Store A can acquire, repair, and persist an Adapter for unseen Store B.

Read first:
- WAVE3.md
- ARCHITECTURE.md (Runtime loop, Adapter-only mutation, Verification)
- shared/routes.md
- fixtures/adapter.wrong.json
- adapters/store_b__publish_product.json
- agent/executor.py
- agent/models.py (Verification, EnvironmentAdapter — read only)

Assume Next.js is already running:

    SKILLSHIFT_WEB_URL=http://localhost:3010

Build this loop. No Modal. No dashboard UI.

1. agent/adapter.py
   - load_skill(): learn_skill(load_trace("fixtures/traces/store-a.json")) — fallback to fixtures/skill.json if the real trace is missing.
   - load_wrong_adapter() from fixtures/adapter.wrong.json (Collections > Create).
   - load_cached_adapter() from adapters/store_b__publish_product.json if learned_from is cached/recovery.
   - intent_to_testids(app_action) → list of testids. Locked table:
     - "Collections" in action → ["store-b-nav-collections", "store-b-collections-create"]
     - "Inventory" in action → ["store-b-nav-inventory", "store-b-create-listing"]
     - details → type store-b-field-name, store-b-field-price
     - image → upload store-b-field-image
     - "Go Live" → ["store-b-go-live"]
   - NEVER invent new testids.

2. agent/verifier.py
   - verify_step(hands, skill_step) → Verification (the Pydantic model in models.py).
   - Deterministic first: if store-b-field-name is visible → matched. If store-b-collections-create or "Collections" heading / collection form is visible and the name field is not → mismatch with hypothesis "Collections was incorrectly mapped to product creation" and alternative "Inventory".
   - Optional LLM only if an API key exists; must fall back to the rule above.
   - Skill is never edited.

3. agent/recovery.py
   - given a mismatch Verification + current EnvironmentAdapter, mutate ONLY the mapping whose semantic_intent == step_intent.
   - Set app_action to "Inventory > Create Listing", learned_from="recovery", append failure_lesson.
   - persist() writes adapters/store_b__publish_product.json.
   - After a successful full run, set all mappings learned_from="cached" on the copy used for run 2 (or write fixtures/adapter.cached.json + the persisted file).

4. agent/executor.py
   - Keep BrowserHands primitives.
   - REMOVE the global "never click Collections" ban from click() OR gate it behind a flag (allow_collections=True for attempt 1).
   - Add execute_until(hands, adapter, skill, product, stop_after_first_step=False) that walks intents via intent_to_testids.
   - Attempt 1: execute only "start creating a new sellable item" with the WRONG adapter, then verify.
   - After recovery: continue/fill/upload/Go Live with Leather Bag / 89 / web/public/products/leather-bag.svg.
   - Attempt 2 (new browser context): load persisted adapter, skip exploration, publish Blue Sneaker / 120 / blue-sneaker.svg. Print "Exploration skipped".

5. agent/run_transfer.py
   Orchestrate and print a human-readable demo log:
   - Skill loaded: publish_product
   - Environment: store-b unseen
   - Adapter guess: Collections > Create
   - ADAPTER MISMATCH DETECTED + hypothesis
   - Adapter updated: Inventory > Create Listing
   - Product live (Leather Bag)
   - Second run: Adapter found / Exploration skipped / Blue Sneaker live
   Also write fixtures/live/dashboard-state.json after each phase (mismatch, recovered, cached) matching shared/examples/dashboard-state*.json so Agent 3B can read it. If 3B has not started, still write the file.

6. Tests in agent/tests/test_transfer.py
   - verifier returns matched=False on a collections page (can use a short Playwright snippet or execute first wrong step).
   - recovery rewrites only that mapping; skill JSON unchanged.
   - persist file exists.
   - optional full run if server is up; if server down, fail with WebUnavailable — do not start Next.js.

Must not: Modal, Next.js edits, video, OmniParser, Browser Use as brain, changing Skill intents.

No new API keys required.

Done when:
  SKILLSHIFT_WEB_URL=http://localhost:3010 python -m agent.run_transfer
shows mismatch → adapter rewrite → Leather Bag live → second run Blue Sneaker with exploration skipped.
