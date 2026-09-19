# File ownership

Agents must not touch each other's trees. If you need a change outside your paths, stop and write it in the handoff — do not edit it.

| Path | Owner | Wave 1 |
| --- | --- | --- |
| `web/**` | Agent A | Yes — Next.js stores + dashboard shell |
| `agent/**` | Agent B | Yes — Pydantic models + learner + tests |
| `fixtures/**` | Agent B | Yes — runtime copies of examples, learner I/O |
| `adapters/**` | Agent B | Yes — sample `store_b__publish_product.json` only |
| `shared/**` | Setup (read-only) | Do not edit |
| `inspo/**` | Setup (read-only) | Reference clones only |
| `modal/**` | Nobody yet | Leave empty |
| `PLAN.md` | Setup | Do not edit |
| `ARCHITECTURE.md` | Setup | Do not edit |
| `CONTRACT.md` | Setup | Do not edit |
| `WAVE1.md` | Setup | Do not edit |

Neither agent implements Playwright execution, Modal recovery, or real video understanding in Wave 1.
