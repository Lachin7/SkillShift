You are Agent 7A for SkillShift. Add the **observation contract** and **test-only state API**. Do not change Store B HOW HERE decisions.

You MAY write/edit:
- agent/models.py (ADD the locked Wave 7 types; keep Skill / CandidateAction / StepMapping / EnvironmentAdapter / Verification)
- agent/observer.py (NEW)
- agent/grounding.py (wire observation helpers; do not pick Inventory/Go Live)
- agent/explorer.py (consume AppObservation.controls as the allowed set)
- agent/executor.py (`observe_app(hands)` only — still generic Playwright)
- web/app/api/store-b-state/route.ts (NEW)
- web/app/store-b/page.tsx only if needed so live products are readable by the API (prefer reading `fixtures/live/store-b-products.json` like live-products)
- shared/routes.md (document the API; do not rename testids)
- agent/tests/test_observer.py (NEW)
- agent/__init__.py exports if needed

Do not edit: agent/learner.py Skill intents, agent/run_transfer.py loop logic, agent/recovery.py decision constants, PLAN.md, ARCHITECTURE.md, WAVE*.md except you may read WAVE7.md, modal_app/, Store A wizard IA.

Read first: WAVE7.md (locked contracts), agent/models.py, agent/executor.py visible_elements, agent/explorer.py, web/app/api/live-products/route.ts.

SKILLSHIFT_WEB_URL=http://localhost:3010.

## observe_app

`observe_app(hands) -> AppObservation`:
- `url` from the page
- `screen` from visible `h1` or path (`/store-b` etc.) — do not hardcode a Store B screen enum in Python
- `controls` from currently visible nodes: `ref` = data-testid if present else skip (hands still need a target). Include role, name, enabled
- `messages` = inner text of visible blockers/banners/errors if those testids exist; also short page snippets of `[role=alert]` if any
- `state` may include heading text; do not put “click Inventory” advice

Explorer and Recovery must validate `target_testid` against `observation.controls[].ref`. Invented refs still raise.

## Test API

`GET /api/store-b-state` returns JSON from live products file + whether a matching card exists. Fields: `product_exists`, `title`, `price`, `status` (`published` if a product exists else `none`), `purchasable` (true if published).

This module must not be imported by explorer.py or recovery.py.

## Tests

- Observation controls only include visible refs
- `validate_candidate` still rejects invented testids
- API route returns JSON (unit or skip if no web)

Done when: Explorer still grounds from visible controls via AppObservation; no new Store B keyword → testid table.
