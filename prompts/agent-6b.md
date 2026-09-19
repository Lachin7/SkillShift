You are Agent 6B for SkillShift. Wire **Modal** so the **campaign / promo** workflow mismatch is resolved by testing two hypotheses in parallel.

Only start after 6A works: `run_transfer` already discovers campaign promo with local recover_campaign.

You MAY write/edit:
- modal_app/**   (CREATE — never put SDK imports under repo `modal/`)
- agent/recovery.py (call Modal to pick winning hypothesis, then apply recover_campaign)
- agent/run_transfer.py (log Modal A ✅ / B ❌)
- agent/requirements.txt (add `modal`)
- agent/tests/test_modal_recovery.py
- web/app/dashboard/page.tsx only if needed to show “Modal candidates” status line from live JSON
- fixtures/live dashboard payload fields for modal_result (optional)

Do not edit: Store A/B form fields (6A owns UI), agent/models.py, agent/learner.py, PLAN.md, ARCHITECTURE.md, WAVE*.md, the shadowing `modal/` README folder’s purpose (do not add `from modal import` there).

Read first: WAVE6.md, prompts/agent-3c.md (constraints), .agents/skills/modal/SKILL.md, agent/recovery.py, agent/verifier.py.

## Critical constraints

1. **Package name:** all Modal app code lives in `modal_app/`. The directory `modal/` shadows the PyPI package if you `import modal` from repo root incorrectly — run Modal entrypoints as `modal run modal_app/recovery_runner.py` and import the SDK only inside `modal_app` / recovery helpers that don’t treat `modal/` as a package.
2. **No localhost in Modal.** Modal functions must NOT Playwright against `http://localhost:3010`. They score a **JSON snapshot** only.
3. **Fallback:** if `modal` is not installed or `modal setup` was never run, score the two candidates **sequentially in-process** and print `Modal unavailable — local sequential candidates`. Same winner. Tests must pass without Modal auth.

## Snapshot contract

```python
snapshot = {
  "expected_state": str,          # from Skill publish step
  "observed_state": str,          # from Verification
  "visible_testids": list[str],
  "blocker_text": str,            # store-b-promo-blocker + banner text
  "banner_text": str,             # must include LAUNCH10 for the honest demo
  "shipping_set": bool,
  "promo_empty": bool,
}
```

## Two hypotheses (workflow, not UI rename)

| ID | Candidate action | Should win? |
| --- | --- | --- |
| A | `Enter campaign code LAUNCH10 from the listing banner` | **Yes** |
| B | `Change listing type to Draft to bypass campaign` | **No** |

Scoring (deterministic is required; LLM optional extra):
- A wins if banner/blocker mentions campaign/promo and LAUNCH10 appears in banner_text and promo_empty.
- B loses because listing-type bypass is inconsistent with “campaign code required” blocker.

Use Modal `.map` / two parallel `.remote` calls when authenticated so the sponsor story is real parallelism.

## recovery.py integration

When verifier returns the **campaign** workflow mismatch:
1. Build snapshot from hands + verification (helper in recovery or executor).
2. `winner, report = score_campaign_hypotheses(snapshot)`  
   report = `{ "mode": "modal"|"local", "candidates": [ {"id","action","ok","reason"}, ... ] }`
3. Only if winner is A: `recover_campaign(...)` as 6A defined.
4. If somehow B wins, refuse to apply B (safety) and fall back to A — never teach “Draft bypass”.
5. Persist adapter; attach `report` into dashboard live JSON under `status.modal` or `status.message` suffix like:  
   `Modal candidates: A ✅ campaign LAUNCH10 · B ❌ listing type`

## run_transfer logging

```text
WORKFLOW MISMATCH — campaign prerequisite
Modal parallel recovery
  A Enter campaign code LAUNCH10 …  ✅
  B Change listing type to Draft …  ❌
Adapter updated: + campaign promo
```

## modal_app/README.md

Document:
```bash
uv pip install modal   # or pip
modal setup            # once, human
modal run modal_app/recovery_runner.py   # smoke score_candidates
```
Explicit: Modal is **not** hosting Next.js; it scores recovery hypotheses.

## Tests

- `test_modal_recovery.py`: with Modal mocked or forced local mode, A wins, B loses, recover_campaign still inserts mapping.
- Full `test_transfer.py` still passes **without** Modal credentials.
- Never require network for CI default.

Done when:
- `modal_app/recovery_runner.py` exists and can score A/B
- `run_transfer` prints Modal (or local sequential) A ✅ B ❌ then applies campaign mapping
- Skill unchanged; shipping mapping preserved
- No Playwright inside Modal against localhost
