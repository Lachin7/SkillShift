# Wave 6 — campaign promo + Modal hypotheses

Shipping (Wave 5) proved **one** missing prerequisite. Wave 6 adds a **second** environment rule and uses **Modal** to choose between two recovery stories.

```text
Skill (frozen — still four steps from Store A)
  create → details → image → publish

Store B world rules (not in the Skill)
  1. shipping category   (already learned in Wave 5)
  2. campaign promo code ← NEW

First B run
  fill listing + shipping
  → Go Live still blocked
  → WORKFLOW MISMATCH #2
  → Modal (or local fallback) tests two hypotheses in parallel:

       A: enter campaign promo from the banner   ✅
       B: change listing type / skip campaign    ❌

  → Adapter grows: apply campaign promo
  → Go Live → Leather Bag live

Second B run
  Previously learned: shipping + campaign promo
  → Exploration skipped
```

Tagline for judges: **Skills that learn the software they run on.**

## Why promo + Modal together

| Piece | Job |
| --- | --- |
| Shipping | Deterministic “missing field” (already shipped) |
| Promo | Ambiguous failure — banner says `LAUNCH10`, wrong guess is “listing type” |
| Modal | Parallel scratch scoring of A vs B **without** hosting Next.js |

Modal must **not** open `localhost`. It scores a **snapshot** (blocker text, visible testids, expected state). Playwright on your machine applies the winning Adapter patch.

## How to run agents

**Sequential. Local. Next.js on :3010.**

1. [prompts/agent-6a.md](../../prompts/agent-6a.md) — Store B campaign gate + adapter growth + transfer loop  
2. You verify `python -m agent.run_transfer` discovers promo after shipping  
3. [prompts/agent-6b.md](../../prompts/agent-6b.md) — Modal parallel candidates for the **promo** mismatch  
4. Optional: [prompts/agent-6-solo.md](../../prompts/agent-6-solo.md)

Do **not** parallelize 6A and 6B (both touch `recovery.py`).

Secrets: none for 6A. For 6B: `modal setup` once; if missing, local sequential fallback must still pass.

## Done when

- Skill still four intents; Store A unchanged (no promo).
- First transfer: shipping patch (if needed) then promo mismatch → Modal/local picks promo over listing-type → product live.
- Dashboard shows Modal A ✅ / B ❌ (or “local sequential”) and Adapter line for campaign code.
- Second transfer: no blocker path; lessons include both shipping and campaign.
- `modal_app/` exists; `import modal` is never from the repo’s `modal/` folder.
