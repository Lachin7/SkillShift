# Wave 2 — recorder + executor hands

Wave 1 is the merge gate. These two agents stay independent.

```text
Agent 2A  writes  web/          instrumented recorder on Store A
Agent 2B  writes  agent/        Playwright hands against Store B
```

They share only the existing contract: `TraceEvent` JSON and `data-testid` values. They do not implement verifier, recovery, Modal, or a live dashboard.

## Secrets

**Neither agent needs an API key.**

| Need | Who | Notes |
| --- | --- | --- |
| LLM / OpenAI / Anthropic / Gemini | Nobody | Learner already works offline. Do not paste keys into the agent chat. |
| Next.js running | You, before 2B | `http://localhost:3010` (or 3000). Tell 2B the URL. |
| Playwright Chromium | Agent 2B installs locally | `playwright install chromium` — not a key |
| Modal token | Nobody | Wave 3+ |

Optional, later, **you** (not the agents): if you want the real VLM learner on a recorded trace, put a key in `.env` (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`). Wave 2 does not depend on that.

Run both as **local** agents. 2B must hit localhost and install a browser.

---

## Agent 2A prompt

Copy [prompts/agent-2a.md](prompts/agent-2a.md) into a new local agent.

---

## Agent 2B prompt

Copy [prompts/agent-2b.md](prompts/agent-2b.md) into a new local agent.

Tell it the store URL if it is not 3010:

```text
SKILLSHIFT_WEB_URL=http://localhost:3010
```

---

## Verify (you, before Wave 3)

| Check | Agent |
| --- | --- |
| Walk Store A (Leather Bag). Download / save a real trace with before/after images | 2A |
| Trace validates as `list[TraceEvent]` | 2A → existing `agent.models.TraceEvent` |
| `learn_skill(real_trace)` still returns `publish_product` with the four locked intents and no `"click"` in intents | 2A + existing B |
| Script publishes Blue Sneaker £120 on Store B via Inventory, no LLM | 2B |
| Product card visible (`store-b-product-card`) | 2B |
| 2B never clicks Collections | 2B |

---

## Do not assign yet (Wave 3)

Deliberate Collections miss → verifier → adapter-only mutation → persist → second run → live dashboard. Modal last.
