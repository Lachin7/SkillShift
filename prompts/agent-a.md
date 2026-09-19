You are Agent A for SkillShift Wave 1. You own ONLY web/.

Do not edit: agent/, fixtures/, adapters/, shared/, inspo/, modal/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE1.md.

This is a hackathon research demo, not a SaaS. Build a minimal Next.js app so a human can publish a product in two fake stores, and so a four-card dashboard can show Skill vs Adapter from static JSON.

Read first (do not rewrite them):
- CONTRACT.md
- shared/ownership.md
- shared/routes.md
- shared/examples/dashboard-state.json
- shared/examples/dashboard-state.mismatch.json
- PLAN.md step 1
- ARCHITECTURE.md sections "Fake stores" and "Dashboard contract"

Build:
1. Next.js app in web/ (App Router, TypeScript).
2. /store-a — multi-step seller wizard: Products → Add Product → Media → Publish. After Publish, show a visible product card. Use product fields name, price, image. In-memory / client state only.
3. /store-b — different IA: nav is Collections, Inventory, Orders. Product creation is Inventory → Create Listing (single-page form). Finish action is "Go Live". Collections is a plausible decoy (collection management, NOT product creation) and should include a Create action so an explorer can pick it first. After Go Live, show a product card.
4. Put the data-testid values from shared/routes.md on the real controls.
5. /dashboard — four cards side by side: Learned Skill, Current App, Adapter, Status. Render from static JSON copied into web/ (e.g. public/dashboard-state.json). Support phases mismatch | recovered | cached. In mismatch, the Create item mapping is red (Collections). Include a simple control to flip fixture phase so we can demo the visual without a live agent.
6. Home page with links to Store A, Store B, Dashboard.

Must not: recorder events, Playwright, Python, Modal, auth, database, extra commerce features.

Optional visual inspiration only (do not copy their stack): inspo/understudy.

Done when:
- A human can publish in Store A and see a product card.
- A human can publish in Store B via Inventory → Create Listing → Go Live and see a product card.
- Store B Collections is clearly not product creation.
- /dashboard shows the four cards from fixtures, including a red mismatch mapping.
