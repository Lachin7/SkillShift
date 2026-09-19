You are Agent 4 — Demo cockpit. Make the transfer feel like one product, not a terminal script.

You MAY write/edit:
- web/app/dashboard/**
- web/app/api/run-transfer/** (or similar)
- web/app/api/live-products/** (or similar)
- web/app/store-b/page.tsx (read persisted products only — keep all data-testids and IA)
- agent/run_transfer.py
- agent/executor.py (only if needed to persist products + keep ONE headed window for both runs)
- fixtures/live/**

Do not edit: shared/, PLAN.md, ARCHITECTURE.md, WAVE*.md, agent/models.py, agent/learner.py, agent/verifier.py, agent/recovery.py, Store A wizard IA.

Read first: WAVE4.md, agent/run_transfer.py, web/app/dashboard/page.tsx, web/app/store-b/page.tsx.

## Build

1. **One headed browser for the whole transfer**
   - Do not close Chromium between Leather Bag and Blue Sneaker.
   - Second run: same page/context, go Inventory → Create Listing again (or reset listing form), publish Blue Sneaker.
   - Keep SKILLSHIFT_HEADED / DEMO_PAUSE / DEMO_HOLD. Default headed when launched from the dashboard.

2. **Persist products so Store B is not empty**
   - After each successful Go Live, append {name, price, image} to fixtures/live/store-b-products.json.
   - Store B loads that list on mount (and polls every ~1s or on focus) and renders product cards with store-b-product-card.
   - In-memory create still works for a human clicking by hand.
   - Image can be a public path (/products/leather-bag.svg).

3. **Dashboard: Run transfer**
   - A primary button "Run transfer" on /dashboard.
   - POST /api/run-transfer starts (from repo root):
     SKILLSHIFT_WEB_URL=<the site origin> SKILLSHIFT_HEADED=1 python -m agent.run_transfer
     using the project .venv if present.
   - Do not start Next.js from Python. If the spawn fails, show the error on the dashboard.
   - Disable the button while running; show "Running…" + last log lines if you stream them (optional; exit status is enough).
   - After it finishes, live dashboard-state.json should already be cached — cards update via existing poll.

4. **Show the teach trace on the dashboard**
   - A compact fifth strip OR a panel under the four cards: last saved fixtures/traces/store-a.json events (action + target + value only — not giant data-URLs).
   - If the file is missing, say "No demonstration saved — teach in Store A."
   - Skill card still never changes.

5. **Keep the four cards.** Do not remove Live poll.

## Done when

- Clicking Run transfer on /dashboard opens ONE headed Store B, mismatch → recover → two product cards, window holds.
- Refreshing /store-b in the user's normal browser shows Leather Bag and Blue Sneaker.
- Dashboard shows a short Store A trace.
- Headless `pytest agent/tests/test_transfer.py` still passes (no headed, no long holds).
