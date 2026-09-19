You are Agent 7B for SkillShift. Make verification **independent** and add a **failure diagnoser**. Explorer must not score its own success.

You MAY write/edit:
- agent/verifier.py
- agent/failure_diagnoser.py (NEW)
- agent/models.py (only if 7A types need a small field)
- agent/transfer_loop.py (call diagnose after failed verify; do not hardcode shipping/Inventory)
- agent/grounding.py (run_agent_sync reuse)
- agent/tests/test_verifier.py or extend test_transfer.py
- fixtures/live writers only for evidence lists on dashboard payload if already written from run_transfer

Do not edit: web/ Store B IA, explorer.py candidate policy (except pass observation in), modal_app/, learner.py intents, WAVE*.md, PLAN.md.

Read first: WAVE7.md § locked contracts, agent/verifier.py, agent/explorer.py, agent/transfer_loop.py, agent/observer.py (7A).

Requires GEMINI_API_KEY or SKILLSHIFT_MOCK_LLM=1. Next.js on :3010.

## Independent verifier

After every important act (and after recovery retries):

1. Collect `observe_app(hands)` + screenshot **after** the action.
2. Call verifier in a **separate** Agent (`skill_verifier`) — never reuse the explorer agent instance/prompt.
3. Return both legacy `Verification` (for dashboard) and `VerificationResult`.
4. Evidence hierarchy (use what is available, in order):
   - UI: heading, messages, enabled/disabled Go Live, product card text
   - Behaviour: still on expected screen
   - Test API: GET `/api/store-b-state` **only** for the **final publish** step, never for navigation
5. Success for publish = product card **or** test API `status=published` for that product. Clicking Go Live is not success.

Mock backend (`SKILLSHIFT_MOCK_LLM=1`) may use DOM signals but must still fill `failure_class` and `observed_evidence`.

## Diagnoser

`diagnose_failure(verification_result, observation, failed_refs) ->` structured output that includes `failure_class` (may refine verifier) and a short `hypothesis` / `alternative` for recovery.

Do **not** encode “Collections → Inventory” as the only branch. Instruct the model with the observation. Mock: if heading looks like collections and goal is create item → `wrong_mapping`; if shipping blocker visible and publish blocked → `missing_prerequisite`.

## Transfer loop

On mismatch: `verify` then `diagnose` then existing `propose_recovery`. Persist `failure_class` into dashboard status message when easy.

Done when: a blocked Go Live yields `missing_prerequisite` with evidence mentioning shipping/blocker; Collections page yields `wrong_mapping` or `navigation_error` without reading `RECOVERED_ACTION`.
