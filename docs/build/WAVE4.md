# Wave 4 — make the demo look like one product

The loop works. Judges still feel a science-fair: terminal command, a Chromium pop-up, an empty Store B tab, a dashboard with extra “fixture preview” knobs, and Collections that spoils the trap.

```text
Must ship:  cockpit (Run + products persist + trace visible)
Then:       optics (honest stores, quieter dashboard)
Then:       judge README + 2-minute talk
Last:       Modal (prompts/agent-3c.md) if sponsors matter
```

## Issues (why it’s not wow yet)

| Issue | Why it hurts |
| --- | --- |
| Transfer is a **terminal command** | Looks like a script, not a product |
| Playwright is **another window**; your Store B tab stays empty | “I ran it and nothing happened” |
| **Two Chromium windows** (run 1 close, run 2 open) | Breaks the story |
| Dashboard **Live vs mismatch/recovered/cached** | Judges don’t know what to click |
| Trace lives in a JSON file nobody shows | Teach step has no payoff on screen |
| Store B Collections says **“this is not product creation”** | Trap is spoiled |
| Rec bar sits on the fake seller chrome | Looks bolted on |
| README is still wave-docs | Judges need a north star + how to run |
| Modal missing | Fine to skip; weak if you promised the sponsor line |

## How to run agents

Do **not** start all three at once.

| Order | Prompt | Parallel with |
| --- | --- | --- |
| 1 | [prompts/agent-4-cockpit.md](../../prompts/agent-4-cockpit.md) | README only |
| 2 | [prompts/agent-4-optics.md](../../prompts/agent-4-optics.md) | After cockpit, or parallel with README |
| 3 | [prompts/agent-4-readme.md](../../prompts/agent-4-readme.md) | Anytime; safest parallel with 1 or 2 |
| Last | [prompts/agent-3c.md](../../prompts/agent-3c.md) | After cockpit works |

All **local**. Next.js on `:3010`. No new API keys.

## Done when a human can

1. Open dashboard, press **Run transfer**.
2. Watch Store B get driven (headed, one window, slow).
3. Refresh or keep Store B open and **see Leather Bag + Blue Sneaker cards**.
4. See Skill / Adapter / a short trace on the same dashboard without touching fixture buttons.
5. Read README and run the demo in under two minutes.
