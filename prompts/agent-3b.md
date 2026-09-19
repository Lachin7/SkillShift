You are Agent 3B for SkillShift Wave 3. You own ONLY the dashboard live view.

You MAY write/edit:
- web/app/dashboard/**
- web/app/api/live-dashboard/** (or similar)
- web/lib/types.ts only if you add a field without breaking existing fixture phases
- web/app/globals.css for dashboard polish

Do not edit: agent/, adapters/, fixtures/ except you MAY read fixtures/live/, shared/, inspo/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE*.md.

This is the presentation surface. The Skill card never changes. The Adapter card is the wow.

Read first:
- WAVE3.md
- ARCHITECTURE.md "Dashboard contract"
- shared/examples/dashboard-state.json
- shared/examples/dashboard-state.mismatch.json
- web/app/dashboard/page.tsx
- web/lib/types.ts

Build:

1. A small Next.js route (e.g. GET /api/live-dashboard) that reads
   `../fixtures/live/dashboard-state.json` from the repo root.
   If the file is missing, fall back to the existing static fixtures (mismatch / recovered / cached).

2. Dashboard polls that route every ~800ms (or uses a refresh button + auto poll).
   When Agent 3A writes a new phase, the four cards update without a full rewrite of Store A/B.

3. Keep the manual phase flipper as a fallback labelled "fixture preview" so the demo still works if 3A is not running.

4. Visual contract (do not invent a fifth card):
   - Learned Skill | Current App | Adapter | Status
   - phase=mismatch → Create item mapping is red (Collections > Create), status shows ADAPTER MISMATCH + hypothesis
   - phase=recovered → mapping rewrites in place to Inventory > Create Listing, status adapter learned / product live
   - phase=cached → App is recognised (unseen=false), status "Exploration skipped"
   - Skill steps never change

5. Do not add a Rec bar to Store B. Do not change Store A/B IA or data-testids.

Must not: Playwright, Python agent modules, Modal, auth, database.

No API keys.

Done when:
- /dashboard shows live state if fixtures/live/dashboard-state.json exists
- fixture preview still works if that file is absent
- mismatch is visually red, recovered updates the same mapping, cached says exploration skipped
