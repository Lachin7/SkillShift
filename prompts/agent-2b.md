You are Agent 2B for SkillShift Wave 2. You own ONLY agent/executor.py, a small run script under agent/, tests under agent/tests/ that you add, and agent/requirements.txt (you may add playwright).

Do not edit: web/, shared/, inspo/, modal/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE1.md, WAVE2.md, agent/models.py, agent/learner.py.

You MAY read adapters/store_b__publish_product.json and shared/routes.md. Do not invent new testids.

This is a hackathon research demo. Pydantic AI is the brain later. You are only the hands: Playwright primitives that execute a GIVEN adapter. No exploration. No LLM.

Read first (do not rewrite them):
- WAVE2.md
- shared/routes.md (Store B testids)
- adapters/store_b__publish_product.json
- ARCHITECTURE.md "Brain and hands"
- PLAN.md step 5

Assume the Next.js app is already running. Default base URL:

    SKILLSHIFT_WEB_URL=http://localhost:3010

(override via env if needed).

Build:
1. agent/executor.py with a small BrowserHands (or similar) class:
   - screenshot() → bytes or path
   - visible_elements() → list of {testid, role, name/text} from the page (use data-testid + accessible names; do not add OmniParser)
   - click(testid)
   - type(testid, text)
   - upload(testid, image_path)
2. A runner that opens /store-b and executes the RECOVERED adapter happy path only:
   - click store-b-nav-inventory
   - click store-b-create-listing
   - type store-b-field-name "Blue Sneaker"
   - type store-b-field-price "120"
   - upload store-b-field-image (use web/public/products/blue-sneaker.svg or any existing catalog image)
   - click store-b-go-live
   - assert store-b-product-card is visible and shows Blue Sneaker
3. Add playwright to agent/requirements.txt. Document `playwright install chromium`.
4. A pytest or script that performs the run against SKILLSHIFT_WEB_URL. If the server is down, fail with a clear message — do not start Next.js yourself and do not edit web/.
5. Never click store-b-nav-collections or store-b-collections-create in this wave.

Must not: verifier, recovery, Modal, learner changes, dashboard wiring, Browser Use as the brain, Stagehand, OmniParser, any API/LLM calls.

No API keys. Do not ask for OpenAI/Anthropic/Gemini. Install Playwright Chromium locally.

Done when:
- `SKILLSHIFT_WEB_URL=http://localhost:3010` plus your script publishes Blue Sneaker £120 on Store B.
- store-b-product-card is present afterwards.
- The script does not call an LLM and does not touch Collections.
