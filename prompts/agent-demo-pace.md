You are fixing the SkillShift demo visibility. Wave 3 already works; judges cannot see it because Playwright is too fast and the window closes immediately.

Own ONLY:
- agent/executor.py
- agent/run_transfer.py
- optionally agent/run_store_b.py if it shares the same open_hands helpers

Do not edit: web/, shared/, PLAN.md, ARCHITECTURE.md, WAVE*.md, agent/models.py, agent/learner.py, agent/verifier.py, agent/recovery.py (unless a tiny import is required).

## Goal

When the user runs:

```bash
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 .venv/bin/python -m agent.run_transfer
```

they must clearly see Store B:

1. Window opens and stays readable (not a flash).
2. Collections is clicked (wrong path) — pause so humans can see the collections UI.
3. Mismatch happens (can stay in terminal + dashboard; browser still showing collections).
4. Inventory → Create Listing → fill Leather Bag → Go Live — each step with a short pause.
5. Product card visible — pause.
6. Second run (Blue Sneaker) — also headed, slow enough to see, then pause on the product card.
7. Only then close the browser.

## Requirements

1. Default `SKILLSHIFT_HEADED=1` behavior for demo OR keep env flag but document that demo MUST use headed.
2. Add a demo pace helper, e.g. `demo_pause(seconds)` controlled by env:
   - `SKILLSHIFT_DEMO_PAUSE` default **1.2** seconds between major actions when headed
   - `SKILLSHIFT_DEMO_HOLD` default **3** seconds to hold on product card / collections screen before continuing or closing
3. When headed, set Playwright slow_mo (e.g. 300–500ms) on `chromium.launch(slow_mo=...)`.
4. After first wrong step lands on Collections, pause HOLD seconds before recovery continues.
5. After Leather Bag product card appears, pause HOLD seconds before starting second run.
6. After Blue Sneaker product card appears, pause HOLD seconds before closing.
7. Print clear terminal lines like:
   - "WATCH: Collections (wrong)"
   - "WATCH: Inventory → Create Listing"
   - "WATCH: product card — holding"
   so the presenter knows what to look at.
8. Do not break headless CI/tests: when headed is false, pauses can be 0 / tiny and browsers close immediately as now. Existing `pytest agent/tests/test_transfer.py` must still pass headless.

## Done when

```bash
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 SKILLSHIFT_DEMO_PAUSE=1.5 SKILLSHIFT_DEMO_HOLD=4 .venv/bin/python -m agent.run_transfer
```

lets a human comfortably watch wrong Collections → fix → Leather Bag card → second run Blue Sneaker card, without the window vanishing instantly.

Also update agent/README.md (or a short comment at top of run_transfer.py) with that exact demo command.
