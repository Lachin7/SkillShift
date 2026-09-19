# Wave 8 — Wow factor: live perturbation, Store C, localized Store D

Wave 7 made the agent pipeline real (observe → ground → verify independently → diagnose → patch → persist → metrics). Wave 8 makes it **undeniable to a judge**.

```text
Skill   = WHAT      (frozen four intents — never renamed here)
Adapter = HOW HERE  (per app, discovered, patched, versioned)
Wave 8  = more environments + a judge who can break one on stage
```

Three beats, in order:

| Agent | Beat | Why it wows |
| --- | --- | --- |
| [8A](prompts/agent-8a.md) | Judge renames/adds a rule on Store B mid-demo | Proves it is not a selector cache. Live `stale_mapping` → remap → deprecate old rule |
| [8B](prompts/agent-8b.md) | **Store C**: table + drawer + status dropdown (no publish button) | Proves transfer is not "find the button that means publish" |
| [8C](prompts/agent-8c.md) | **Store D**: same structure as B, Japanese labels | Proves semantic grounding, not string matching |

## Non-negotiables (all Wave 8 agents)

- Skill stays the four intents in [shared/routes.md](shared/routes.md). Adding an app never edits the Skill.
- Live path keeps **no** hardcoded HOW HERE: no `adapter.wrong.json`, no `RECOVERED_ACTION`, no `if "go live"` decision branches.
- Explorer / Recovery still choose only from controls present in the current `AppObservation`.
- Each app gets its **own** adapter file. Store B's learned adapter must never be handed to Store C or D.
- Playwright stays hands. Pydantic AI stays brain.

## The one refactor Wave 8 needs (owned by 8B)

`store-b-` strings are currently baked into `transfer_loop.py`, `explorer.py`, `verifier.py`, `executor.py`, `run_transfer.py`. A third and fourth app cannot exist until that is plumbing instead of copy-paste.

Add `agent/targets.py`:

```python
class AppTarget(BaseModel):
    app_id: str                 # "store-c"
    label: str                  # "Store C"
    path: str                   # "/store-c"
    testid_prefix: str          # "store-c-"
    product_card_testid: str    # "store-c-product-card"
    live_products_file: str     # "fixtures/live/store-c-products.json"
    adapter_file: str           # "adapters/store_c__publish_product.json"
```

Registry for `store-a` / `store-b` / `store-c` / `store-d`; selected by `SKILLSHIFT_TARGET_APP` (default `store-b`).

**Critical distinction — state this in code comments:**

- Allowed: "which app am I in, where does it live, where do I persist its adapter" (environment plumbing).
- Forbidden: "in this app, intent X means control Y" (that is the Adapter, and it must be discovered).

Suffix-based replay is fine (`endswith("-field-name")` → type the product name) because it describes **control kind**, not which control satisfies a semantic step. Choosing the control is still the Explorer's job.

## Perturbation contract (owned by 8A)

State lives in `fixtures/live/perturbations.json` and is read through an API, so toggles **survive the agent's navigation**:

```json
{ "rename_publish": false, "extra_required": false, "reorder_nav": false }
```

| Flag | Store B change | Expected agent behaviour |
| --- | --- | --- |
| `rename_publish` | `store-b-go-live` is **removed**; `store-b-launch-product` appears labelled "Launch Product" | Cached run: `stale_mapping` → re-ground → verify → patch `replace_mapping`, deprecate old rule |
| `extra_required` | New required select `store-b-field-tax-class` + `store-b-tax-blocker`; Go Live stays disabled until set | Cached run: `missing_prerequisite` → `add_prerequisite` patch |
| `reorder_nav` | Nav order shuffled and `store-b-nav-inventory` replaced by `store-b-nav-catalog` ("Catalog") | `wrong_mapping` / `navigation_error` on the create step → remap |

**Must change the `data-testid`, not only the visible label.** If the testid stays the same, cached `resolved_targets` still work and nothing adapts — the beat becomes a no-op.

## Risk to manage: candidate-list growth

More apps and more controls mean bigger observation lists, more tokens, more chances of a wrong pick (this already bit us once with `store-b-field-listing-type`). Mitigation, already available from 7A: `ObservationControl.region`. Prefer candidates in the active region plus navigation, so a dense screen still offers ~8 plausible targets.

## Done-when (Wave 8 cut line)

Must:

1. With `rename_publish` on and a **warm** Store B adapter, a run detects the stale rule, remaps, verifies, and persists a patch — no code change, no restart.
2. `SKILLSHIFT_TARGET_APP=store-c` completes publish on Store C from an **empty** `adapters/store_c__publish_product.json`, including Store C's own prerequisite.
3. `SKILLSHIFT_TARGET_APP=store-d` completes publish with Japanese-only labels.
4. Store B behaviour and all Wave 7 tests still pass unchanged.

Nice: dashboard shows app + adapter version per app; a Skills × Apps matrix; learning-curve numbers (C cold vs B cold vs cached).

Defer: Store C invalidation, ¥ currency formatting, a fifth app, OmniParser, raw video.

Note for 7F: dashboard does not render perturbation flags; they live on `/store-b` judge controls.

## Demo beats after Wave 8

```text
1. Teach in Store A
2. Transfer to Store B — shipping prerequisite discovered, adapter saved
3. Judge flips "rename publish" — agent detects stale rule and repairs live
4. Store C (table, status dropdown, never run before) — publishes from empty adapter
5. Store D (Japanese) — same Skill, no English anywhere
```
