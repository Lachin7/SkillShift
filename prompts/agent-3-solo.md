You are the solo Wave 3 agent for SkillShift. Do 3A first, then 3B in the same session. Skip Modal (3C) unless 3A+3B already work and time remains.

This is a hackathon research demo. Prove: a Skill from Store A can acquire, repair, and persist an Adapter for Store B.

## Part 1 — Python loop (do this first, fully)

Follow [prompts/agent-3a.md](agent-3a.md) exactly. Same file ownership, same run_transfer demo log, same fixtures/live/dashboard-state.json writes.

Stop and self-check before touching web/:

    SKILLSHIFT_WEB_URL=http://localhost:3010 python -m agent.run_transfer

must show Collections mismatch → Inventory rewrite → Leather Bag live → Blue Sneaker second run, exploration skipped.

## Part 2 — Live dashboard

Then follow [prompts/agent-3b.md](agent-3b.md). Do not break Store A/B or data-testids.

## Part 3 — only if early

Do not start Modal unless Part 1+2 work. If you do, follow [prompts/agent-3c.md](agent-3c.md) including the `modal/` shadow warning.

No new API keys for Parts 1–2. Next.js must already be on http://localhost:3010.
