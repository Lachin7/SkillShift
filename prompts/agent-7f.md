You are Agent 7F for SkillShift. Dashboard must show the **real loop**, not a scripted Collections story.

You MAY write/edit:
- web/app/dashboard/page.tsx
- web/lib/types.ts
- web/public/dashboard-state*.json (preview fixtures — update copy; Skill steps stay four)
- agent/run_transfer.py dashboard writer
- fixtures/live/dashboard-state.json shape
- shared/examples/dashboard-state.json
- web/app/globals.css (trace list only)

Do not edit: agent explorer/verifier/recovery logic, Store A/B IA, modal_app/, Skill intents, WAVE*.md, PLAN.md.

Read first: WAVE7.md Priority 7, WAVE7 done-when, web/app/dashboard/page.tsx, fixtures/live/dashboard-state.json, shared/examples/dashboard-state.json.

## Show (live)

A compact trace list (newest last), each item:

```text
semantic step
→ chosen control (name/ref)
→ verification passed/failed + failure_class
→ patch operation if any
→ adapter version / mapping count
```

Keep the four cards. Status message must come from the live run (discovered mappings, shipping lesson from verifier), not “designed to click Collections.”

Optional metrics line from 7D: `actions` / `model_calls` / `recoveries` on first vs second product.

Preview fixtures: mismatch = missing_prerequisite + shipping evidence; recovered = adapter has shipping + go live; cached = reuse, 0 recovery.

Done when: headed or mock transfer updates live dashboard through the loop; README/demo copy is not required unless you already touch dashboard strings.
