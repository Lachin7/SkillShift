You are Agent 4 — Demo optics. Make Store A / Store B / Dashboard look like a product, not a hackathon control panel.

You MAY write/edit:
- web/app/store-a/page.tsx
- web/app/store-b/page.tsx
- web/components/RecorderBar.tsx
- web/app/dashboard/page.tsx
- web/app/globals.css
- web/app/page.tsx (copy only)

Do not edit: agent/, adapters/, fixtures/, shared/, PLAN.md, ARCHITECTURE.md.
Do not remove data-testids from shared/routes.md.
Do not remove Rec/Save capability — only restyle / move it.

Read first: WAVE4.md, ARCHITECTURE.md Dashboard + Fake stores.

## Build

1. **Store B Collections is a real decoy**
   - Remove copy like "This is not product creation" and "New sellable items live under Inventory."
   - Collections should look like a plausible merchandising area (Create, groups, empty counts). A first-time agent/human can mistake it for "make a new item."
   - Keep store-b-collections-create and the create-collection form. No name/price/image fields there.

2. **Recorder is SkillShift teach mode, not Harbor/Atelier chrome**
   - Rec bar should read as SkillShift (e.g. "SkillShift · teaching") sitting as a small overlay, not a store toolbar.
   - Still default ON on /store-a. Keep Download / Save.
   - Do not add a recorder to Store B.

3. **Dashboard chrome for judges**
   - Default view: Live + four cards (+ trace panel if cockpit already added — don't delete it).
   - Hide "fixture preview" / mismatch|recovered|cached behind a small "Dev" or "Replay slides" disclosure, closed by default.
   - Home page: one line that the demo is Teach (A) → Watch (dashboard Run) → Store B product cards.

## Done when

- Collections no longer spoils the punchline in the UI text.
- A stranger can tell Rec is SkillShift teaching, not a seller feature.
- Dashboard default has one obvious mode (Live), not six competing buttons.
