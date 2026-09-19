# Wave 5 — procedural adaptation

Ranks 1–3 are **one loop**. Rank 4 is the next agent. Do not start Modal, Store C, photo-input, or a refund skill in this wave.

```text
Skill (frozen, from Store A)
  create item → details → image → publish

Store B world
  same, PLUS: cannot Go Live until shipping category is set

First B run
  Go Live blocked
  → not "wrong button"
  → "this environment has an extra prerequisite"
  → adapter gains: choose shipping category
  → Go Live succeeds

Second B run
  Previously learned: shipping category required
  → no surprise, product live
```

## How to run

1. Local agent: paste [prompts/agent-5a.md](../../prompts/agent-5a.md)  
   Next.js at `http://localhost:3010`.
2. You verify `python -m agent.run_transfer` (headed if you want to watch).
3. Then local agent: [prompts/agent-5b.md](../../prompts/agent-5b.md) (same-env replay on Store A).
4. Optional one chat: [prompts/agent-5-solo.md](../../prompts/agent-5-solo.md).

Do **not** run 5A and 5B in parallel — both touch `run_transfer.py` / dashboard live JSON.

No new API keys. Modal is still [prompts/agent-3c.md](../../prompts/agent-3c.md) **after** 5A.

## Done when

- Store B Go Live stays disabled until a shipping category is chosen.
- Skill JSON / four intents are unchanged.
- Adapter for Store B includes an extra mapping learned from recovery.
- Dashboard status talks about a **missing prerequisite**, not only Collections.
- Second Store B product does not re-discover shipping.
- After 5B: teach-once Skill replays on Store A with a new catalog item (no exploration).
