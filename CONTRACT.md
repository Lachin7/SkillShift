# SkillShift contract (Wave 1)

Read this, then [ARCHITECTURE.md](ARCHITECTURE.md), then [shared/](shared/). Do not invent types, routes, or extra product.

```text
Skill   = WHAT
Adapter = HOW HERE
```

North star: a semantic skill learned in Store A can acquire, repair, and persist an adapter for unseen Store B.

## Locked identity

- Skill: `publish_product`
- App ids: `store-a`, `store-b`
- Inputs: `name`, `price`, `image`
- Intents: exactly the four strings in [shared/routes.md](shared/routes.md)
- Adapter path: `adapters/store_b__publish_product.json`

## Ownership

| Agent | Writes | Must not write |
| --- | --- | --- |
| **A** (frontend) | `web/**` | `agent/`, `fixtures/`, `adapters/`, `shared/`, `inspo/`, `modal/` |
| **B** (python core) | `agent/**`, `fixtures/**`, `adapters/*.json` | `web/`, `shared/`, `inspo/`, `modal/` |

## Wave 1 out of scope for both

Playwright execution, Modal sandboxes, real video → keyframes, OmniParser, auth, database.

## Verify before Wave 2

See [WAVE1.md](WAVE1.md). You are the merge gate. Do not start the recorder or executor until both trees pass the checklist.
