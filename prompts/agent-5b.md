You are Agent 5B for SkillShift. Add **same-environment replay** on Store A after 5A’s shipping loop already works.

Do not start until `python -m agent.run_transfer` already demonstrates the Store B shipping prerequisite. If 5A is not merged, stop and say so.

You MAY write/edit:
- agent/run_replay_a.py (preferred new entrypoint) OR extend agent/run_transfer.py with a flag `--replay-a` / env SKILLSHIFT_REPLAY_A=1
- agent/adapter.py (load/save adapters/store_a__publish_product.json)
- agent/executor.py (Store A testid path only)
- web/app/dashboard/page.tsx (a line: Environment Store A / Adapter cached — do not break B shipping UI)
- fixtures/live/dashboard-state.json writer for the A-replay phase
- agent/tests/test_replay_a.py

Do not edit: Store B shipping fields, agent/models.py, agent/learner.py, shared/routes.md testids except you may USE existing Store A testids, PLAN.md, WAVE*.md.

Read first: WAVE5.md, shared/routes.md Store A testids, agent/executor.py, adapters/.

## Goal

```text
Skill publish_product (already learned)
  → Adapter store-a (HOW HERE: Products > Add Product > Publish)
  → headed Store A
  → new item from catalog (e.g. Ceramic Mug / Brass Lamp — NOT Leather Bag)
  → product card
  → log: Same environment. Exploration skipped.
```

This proves the Skill is not Store-B-only. Then the existing Store B transfer is the *other* environment.

## Build

1. adapters/store_a__publish_product.json — mappings for the four skill intents onto Store A actions/testids (Add Product, fill name/price, image, Publish). learned_from: cached or exploration. No shipping step on A.

2. execute Store A using existing data-testids only. Headed pacing same as B.

3. Dashboard: when replaying A, Current App = Store A, unseen = false, Status = Same environment. Adapter found. Exploration skipped.

4. Do not require a new teach. Use existing Skill from load_skill().

5. pytest: if server down, WebUnavailable; if up, mug/lamp card visible, no Store B shipping clicks.

Done when:
  SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 python -m agent.run_replay_a[text](vscode-file://vscode-app/Applications/Cursor.app/Contents/Resources/app/out/vs/code/electron-sandbox/workbench/prompts/agent-5-solo.md)
publishes a different product on Store A with no Collections and no shipping.
