You are Agent 6A for SkillShift. Add a **second Store B procedural rule**: a campaign / promo code required before Go Live — after shipping is satisfied.

Shipping from Wave 5 stays. Skill stays frozen (four intents). Store A stays without promo or shipping.

You MAY write/edit:
- web/app/store-b/page.tsx
- web/app/globals.css (blocker / banner styles only)
- web/app/dashboard/page.tsx (adapter/status can show Campaign mapping + dual lessons)
- shared/routes.md (ADD testids only)
- agent/adapter.py
- agent/verifier.py
- agent/recovery.py (add recover_campaign / recover_workflow_promo — keep recover_workflow for shipping)
- agent/executor.py
- agent/run_transfer.py
- agent/tests/test_transfer.py
- adapters/store_b__publish_product.json (shape after recovery)
- fixtures/live dashboard writers

Do not edit: Store A, agent/models.py (prefer new StepMapping + failure_lessons), agent/learner.py, agent/run_replay_a.py, PLAN.md, ARCHITECTURE.md, WAVE*.md, modal/, modal_app/ (6B owns Modal).

Read first: WAVE6.md, WAVE5.md, agent/run_transfer.py, agent/recovery.py, agent/verifier.py, web/app/store-b Create Listing form.

SKILLSHIFT_WEB_URL=http://localhost:3010. Keep headed pacing.


On Create Listing, after shipping:

1. A visible campaign banner (not a spoiler that says “agent must…”), e.g.:
   - data-testid: `store-b-campaign-banner`
   - Text like: `New listings require a campaign code. Use LAUNCH10 for the spring launch.`
2. An input:
   - data-testid: `store-b-field-promo`
   - label: Campaign code (or Promo code)
3. Go Live enabled only when: name, price, image, shipping, **and** promo === `LAUNCH10` (case-sensitive or normalize to upper — pick one and stick to it).
4. When shipping is set but promo empty/wrong:
   - data-testid: `store-b-promo-blocker`
   - Text: `Enter a valid campaign code to go live.`
5. Optional decoy that makes hypothesis B plausible:
   - data-testid: `store-b-field-listing-type`
   - select: Public / Draft — changing it must **NOT** unlock Go Live.

Do not put promo on Store A.

## Verifier

Extend verify_step for publish intent:

| Condition | Result |
| --- | --- |
| Form visible, shipping empty, Go Live blocked | existing shipping WORKFLOW mismatch |
| Form visible, shipping set, promo empty/wrong, Go Live blocked | **new** campaign mismatch |
| hypothesis | `This environment requires a campaign / promo code that was not part of the original skill.` |
| alternative | `Enter campaign code LAUNCH10 from the listing banner` |
| observed_state | must mention campaign/promo blocked |

Do not confuse this with Collections or shipping hypotheses. Prefer checking promo blocker / empty promo field when shipping already has a value.

## Recovery (adapter grows again)

`recover_campaign(verification, adapter)`:
- Insert StepMapping before INTENT_PUBLISH (after shipping if present):
  - semantic_intent: `satisfy environment prerequisite: campaign promo code`
  - app_action: `Create Listing > Campaign code LAUNCH10`
  - learned_from: `recovery`
- failure_lessons += `Store B requires campaign code LAUNCH10 before Go Live`
- Do **not** rewrite the Publish mapping into “enter promo”
- Skill unchanged

intent_to_testids: campaign action → `["store-b-field-promo"]`  
Executor: type `LAUNCH10` into that field (and still select shipping when that mapping exists).

For 6A only: recover_campaign can be **local deterministic** (always add promo mapping). Agent 6B will replace the *choice* of which hypothesis won with Modal. Structure recover_campaign so 6B can pass in a winning candidate action string.

## run_transfer.py (first run choreography)

Use inventory adapter stripped of campaign (and of shipping if you need to re-demo shipping — prefer):

**Preferred demo path (shipping already known, promo is the new wow):**
1. Load adapter that has shipping, strip campaign mapping if present (`without_campaign`).
2. Inventory → Create Listing → fill Leather Bag → set shipping.
3. Attempt verify / Go Live with empty promo → WORKFLOW MISMATCH campaign.
4. recover_campaign → persist → log `Adapter updated: + campaign promo`.
5. Enter LAUNCH10 → Go Live → Leather Bag. Hold if headed.
6. Dashboard: highlight Campaign mapping red on mismatch; after recovery show it green; status mentions missing campaign prerequisite.
7. Second run Blue Sneaker: shipping + promo applied without hitting blockers; log  
   `Previously learned: shipping category required; campaign code LAUNCH10`  
   and `Exploration skipped`.

If you must keep shipping discovery in the same script, do shipping first then promo in the same first browser context — both must end up in the persisted adapter. Prefer the “shipping known, promo new” path so the Modal beat (6B) is about promo ambiguity.

## Dashboard

Adapter card supports Create item, Shipping, **Campaign**, Publish.  
Cached status must mention both learned lessons.

## Tests

- Go Live blocked when shipping set but promo empty.
- Listing type change does not enable Go Live.
- recover_campaign inserts campaign mapping; skill dump unchanged; shipping mapping preserved.
- Full run_transfer: logs campaign missing prerequisite; second run logs Previously learned with campaign; adapter JSON contains both shipping and campaign intents.
- Existing shipping / Collections tests still pass.

No Modal in 6A. No Store C.

Done when:
  SKILLSHIFT_WEB_URL=http://localhost:3010 python -m agent.run_transfer
shows shipping satisfied → campaign blocker → adapter +campaign → Leather Bag → second run already knows LAUNCH10.
