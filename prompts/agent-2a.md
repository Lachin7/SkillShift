You are Agent 2A for SkillShift Wave 2. You own ONLY web/.

Do not edit: agent/, adapters/, shared/, inspo/, modal/, PLAN.md, ARCHITECTURE.md, CONTRACT.md, WAVE1.md, WAVE2.md.

You MAY write a recorded trace out to fixtures/traces/ (create that folder if needed). Do not change agent/*.py or the existing fixture JSON that Agent B already tests.

This is a hackathon research demo. Instrument Store A so a human demonstration becomes a semantic trace, not a video pipeline.

Read first (do not rewrite them):
- WAVE2.md
- CONTRACT.md
- shared/routes.md
- shared/examples/trace.store-a.json
- agent/models.py (TraceEvent — read only)
- PLAN.md step 2
- ARCHITECTURE.md "Demonstration trace"

Build:
1. An instrumented recorder that is ON for /store-a (a small Rec/Stop control is fine; default ON is also fine).
2. On every meaningful user action (click on a real control, fill/type in a field, file upload), capture:
   - screenshot BEFORE the action
   - { action, target, value }
   - screenshot AFTER the action
3. Action vocabulary is locked: "click" | "fill" | "upload" only.
4. `target` is the visible label or the data-testid, e.g. "Add Product", "Product name", "Publish". `value` is the typed/uploaded value or null.
5. Persist the trace as a JSON list matching shared/examples/trace.store-a.json / TraceEvent. Screenshot fields may be relative file paths (preferred) or data URLs. If files, write PNGs under fixtures/traces/frames/ and point the JSON at those paths.
6. Add a "Download trace" / "Save trace" control on Store A so a Leather Bag walkthrough can be exported in one click.
7. Keep every existing data-testid from shared/routes.md. Do not break the wizard: Products → Add Product → Media → Publish → product card.
8. Do not record every mouse move. Only the actions that change the task.

Must not: Playwright, Python learner changes, Modal, real video → keyframes, OmniParser, auth, database. Do not implement Store B recording.

No API keys. This is browser-side capture only (html2canvas or equivalent is fine).

Done when:
- A human can still publish Leather Bag in Store A and see a product card.
- That walkthrough produces a real trace (not the hand-written Wave 1 fixture) with at least: click Add Product, fill name, fill price, attach image, click Publish — each with before and after images.
- The JSON loads as list[TraceEvent] conceptually (same keys as the example).
