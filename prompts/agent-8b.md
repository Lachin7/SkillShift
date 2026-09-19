# Agent 8B — Store C: a third app the agent has never run before

You are Agent 8B on SkillShift. Read [WAVE8.md](../docs/build/WAVE8.md) first, then [shared/routes.md](../shared/routes.md), [ARCHITECTURE.md](../ARCHITECTURE.md), and `agent/transfer_loop.py`.

## Goal

Add **Store C**, whose IA has no publish button at all: a listings **table**, an editing **drawer**, and publishing by setting a **status dropdown to Live and saving**. Then run the same frozen Skill against it from an **empty** adapter, on stage, for the first time.

Store B can always be accused of being tuned. Store C answers that: no adapter, no fixture, no button.

Run locally. Next.js on `:3010`. Real key or `SKILLSHIFT_MOCK_LLM=1`. Do not run this in parallel with any Wave 7 agent — you touch the same `agent/` files.

## Step 1 — App targets (do this first, it is the blocker)

`store-b-` is baked into `transfer_loop.py`, `explorer.py`, `verifier.py`, `executor.py`, `run_transfer.py`. Replace it with one registry.

Create `agent/targets.py`:

```python
class AppTarget(BaseModel):
    app_id: str                 # "store-c"
    label: str                  # "Store C"
    path: str                   # "/store-c"
    testid_prefix: str          # "store-c-"
    product_card_testid: str    # "store-c-product-card"
    live_products_file: str     # "fixtures/live/store-c-products.json"
    adapter_file: str           # "adapters/store_c__publish_product.json"

TARGETS: dict[str, AppTarget]   # store-a, store-b, store-c
def current_target() -> AppTarget  # SKILLSHIFT_TARGET_APP, default "store-b"
```

Then:

- `adapter.py`: `empty_store_b_adapter` → `empty_adapter(app_id, skill_name)`. Keep a thin back-compat alias if other callers use it.
- `run_transfer.py` / `transfer_loop.py` / `observer.py`: take path, card testid, adapter file, live file from the target. No literal `"/store-b"` or `"store-b-product-card"` left in the live path.
- `executor.py` `execute_resolved_targets`: match by **suffix** (`-field-name`, `-field-price`, `-field-image`, `-field-shipping`, `-field-status`, `-product-card`, …), not by full `store-b-*` ids. The "wait until the finish control is enabled" logic becomes "wait until the target's finish control is enabled", resolved from the observation, not a constant.
- Mock-LLM heuristics in `explorer.py` / `verifier.py` / `recovery.py`: key off suffix + prefix so mock CI works for any app.

Write this comment where the registry lives, and honour it:

```python
# AppTarget is environment plumbing: which app, where it lives, where its adapter is
# persisted. It must never say "in this app, intent X means control Y" — that is the
# Adapter, and it is discovered by the Explorer at run time.
```

Verify Store B is untouched behaviourally: full `pytest agent/tests` plus one real cold+cached Store B run before you move on. **Commit here.**

## Step 2 — Store C (`web/app/store-c/page.tsx`)

Brand it differently (e.g. "Northwind Market"). Reuse `globals.css` patterns; add a `store-c` scope with at most a handful of new classes. No auth, no DB, no extra seller features.

IA — deliberately unlike A and B:

```text
left nav: Overview · Listings · Payouts        (Listings is correct; others inert)
Listings = a TABLE: Title | Amount | Category | Status | (row action)
toolbar:  "Add row"        store-c-new-row
row:      "Edit"           store-c-row-edit
editor:   a right-side DRAWER, not a page section
finish:   NO button. Status select → "Live", then "Save row".
```

Testids (append to [shared/routes.md](../shared/routes.md)):

- `store-c-nav-overview`, `store-c-nav-listings`, `store-c-nav-payouts`
- `store-c-new-row`, `store-c-row-edit`, `store-c-drawer`, `store-c-drawer-close`
- `store-c-field-title` (product name — note the different word), `store-c-field-amount` (price), `store-c-field-photo` (image), `store-c-field-category`
- `store-c-field-status` (`Draft` / `Scheduled` / `Live`), `store-c-save-row`
- `store-c-category-blocker`, `store-c-row-status`, `store-c-product-card`

Rules:

- `Live` must be **disabled** in the status select until title, amount, photo, and **category** are all set; show `store-c-category-blocker` ("Set a category before a listing can go Live.") when the rest is ready but category is empty. Category is Store C's own prerequisite — a different gate from Store B's shipping, so nothing transfers for free.
- Choosing `Live` alone does nothing until `store-c-save-row` is clicked. Publishing is therefore a **two-action** finish, which the adapter must remember as an ordered trail.
- On save with status `Live`: append to the table with status Live **and** render a `store-c-product-card` in a small "Storefront" strip, so verification stays uniform across apps.
- Persist to `fixtures/live/store-c-products.json` through the same mechanism Store B uses; poll `GET /api/live-products?app=store-c`. Extend the existing route with an `app` param, defaulting to `store-b` so nothing breaks.
- Add one plausible decoy: a `Scheduled` status option and an inert `Payouts` section. No decoy may be a trap the Skill cannot recover from.
- Seed the table with one pre-existing Draft row ("Canvas Tote") so the table is not empty — but the agent must create its own row, not edit that one.

## Step 3 — Verifier ground truth for C

Extend the test-only state API from 7A to accept `?app=store-c` (keep `/api/store-b-state` behaviour intact), reading that app's live products file and returning the same shape. Verifier only. Explorer and Recovery must never read it.

## Step 4 — Run it

```bash
SKILLSHIFT_TARGET_APP=store-c python -m agent.run_transfer
```

`adapters/store_c__publish_product.json` must start as an empty-mappings adapter (or be absent and created empty). The run must discover: Listings → Add row → fill title/amount/photo → hit the category gate → set category → set status Live → Save row → verified live.

## Tests

`agent/tests/test_store_c.py`, mock LLM:

- empty adapter cold start on `store-c` produces four mappings, ≥1 recovery for the category gate
- second run is a cache hit with fewer model calls (reuse `metrics.py` / `reuse_gain` from 7D)
- Store B's learned adapter is never read while `SKILLSHIFT_TARGET_APP=store-c` (assert on the resolved adapter path)
- `execute_resolved_targets` replays a Store C trail (suffix matching works)

Plus a regression test that `current_target()` defaults to `store-b`.

## Guardrails

- Skill intents frozen. Store C must be reachable with the **same four intents**; if you feel the urge to add a fifth, the Skill is wrong or Store C is over-designed.
- No `if app_id == "store-c"` in the live decision path.
- Do not edit `web/app/dashboard/**` (7F) or `web/app/store-b/**` (8A) beyond what Step 1 forces. If Store C should appear on the dashboard app card, note it in [WAVE8.md](../docs/build/WAVE8.md).
- Add a `/store-c` card to `web/app/page.tsx` — that file is yours.

## Done when

1. `SKILLSHIFT_TARGET_APP=store-c python -m agent.run_transfer` publishes on Store C from an empty adapter, with the category prerequisite discovered, not scripted.
2. A second Store C run is a cache hit; `reuse_gain` is reported.
3. Store B cold + cached runs still behave exactly as before. `pytest agent/tests` green. `npx tsc --noEmit && npm run build` green.
4. [shared/routes.md](../shared/routes.md) documents Store C's route, IA, prerequisite, and testids.

Report at the end: the four learned mappings for Store C, the `resolved_targets` trail saved for the publish step, actions/model-calls/recoveries for run 1 vs run 2, and the diff of every file you touched in `agent/` during Step 1.
