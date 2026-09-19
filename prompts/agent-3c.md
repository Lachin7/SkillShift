You are Agent 3C for SkillShift Wave 3. Optional Modal recovery. Only start after 3A works.

You MAY write/edit:
- modal_app/**  (CREATE this folder — do NOT put Python in the existing `modal/` directory)
- agent/recovery.py (call out to Modal if configured, else keep local fallback)
- agent/requirements.txt (add modal)

Do not edit: web/, shared/, PLAN.md, ARCHITECTURE.md, WAVE*.md, agent/models.py, agent/learner.py, agent/executor.py.

CRITICAL:
The folder `modal/` already exists in this repo and SHADOWS the Modal SDK (`import modal` resolves to our folder). Do not add `from modal import App` under `modal/`. Put the Modal app in `modal_app/recovery_runner.py`.

CRITICAL:
Modal cannot reach http://localhost:3010. Do NOT open Store B from a Modal Sandbox. Do NOT ngrok unless the user explicitly asks.

Read first:
- WAVE3.md
- ARCHITECTURE.md "Modal recovery"
- .agents/skills/modal/SKILL.md
- agent/recovery.py (from 3A)
- agent/models.py Verification / StepMapping

Build a *real* Modal use that matches the sponsor line:

  "Modal gives the agent parallel scratch environments in which it can
   safely test competing interpretations of unfamiliar software before
   updating its learned adapter."

Honest implementation that works without exposing localhost:

1. modal_app/recovery_runner.py
   - A Modal App with a function `score_candidate(snapshot, candidate_action) -> Verification`
   - snapshot = { expected_state, visible_elements, screenshot_note or small text description }
   - Two candidates in parallel via .map or two .spawn/.remote calls:
     A: "Inventory > Create Listing"
     B: "Catalog > New Item"
   - Return which candidate is consistent with "product creation form" vs "collection management".
   - Deterministic scoring is fine (string/testid rules). LLM optional.

2. agent/recovery.py
   - If MODAL_TOKEN_ID / modal is authenticated, call the two candidates in parallel, keep the winner, write StepMapping.learned_from="recovery".
   - If Modal is not authenticated, run the same two candidates sequentially in-process and print "Modal unavailable — local sequential candidates". Same Adapter result.

3. Document in modal_app/README.md:
   pip/uv install modal
   modal setup    # human must do this once
   modal run modal_app/recovery_runner.py
   How this is NOT "we hosted Next.js on Modal".

Must not: deploy the Next.js app to Modal, drive Playwright inside Modal against localhost, edit Store pages, change Skill.

Done when:
- Two candidates are scored (Modal if logged in, local fallback otherwise)
- Winner is Inventory
- Catalog candidate is discarded
- Adapter update path from 3A still works
