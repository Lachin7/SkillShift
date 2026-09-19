You are Agent 7E for SkillShift. Wire **Modal** to score **diagnoser hypotheses**, not hardcoded LAUNCH10 vs Draft.

You MAY write/edit:
- modal_app/scoring.py
- modal_app/recovery_runner.py
- agent/recovery.py or agent/modal_recovery.py (NEW) — snapshot + score + pick winner
- agent/transfer_loop.py (on missing_prerequisite or wrong_mapping, optional parallel score)
- agent/tests/test_modal_recovery.py (rewrite: hypotheses come from diagnoser-shaped dicts)
- agent/modal_campaign.py only to stop live path from importing staged campaign winners

Do not edit: Store B promo gate (stay deferred), Store A, Skill intents, explorer.py, WAVE*.md, PLAN.md.

Read first: WAVE7.md Priority 6, WAVE6.md (what **not** to copy), agent/failure_diagnoser.py, agent/recovery.py, modal_app/, ARCHITECTURE.md Modal note: no localhost inside Modal.

## Behaviour

On verifier failure, build a snapshot JSON only:

- expected_state, observed_evidence, failure_class
- visible control refs + names
- blocker/banner text
- failed_refs

Generate **two** hypotheses as `CandidateAction` lists (from diagnoser / recovery propose, not constants `CAMPAIGN_ACTION`).

Example shape for shipping:

- A: select shipping control then retry publish
- B: click listing-type / Save Draft (should verify false)

Modal (or local fallback) scores each against the snapshot. Winner is the hypothesis `verified_success` true with lower cost. Coordinator applies **AdapterPatch** from 7C for the winner.

If Modal unavailable: print `Modal unavailable — local sequential candidates` and score locally. Tests must pass without `modal setup`.

Never open Playwright inside Modal. Never mutate the live headed page from two branches at once — live Playwright applies the winning patch only.

Done when: unit test with a shipping-blocker snapshot picks the shipping hypothesis; live transfer still works if Modal is down; grep live path shows no `LAUNCH10` as the recovery decision.
