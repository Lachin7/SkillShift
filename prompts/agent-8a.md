# Agent 8A — Judge-controlled perturbation of Store B

You are Agent 8A on SkillShift. Read [WAVE8.md](../WAVE8.md) first, then [shared/routes.md](../shared/routes.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).

## Goal

A judge changes Store B **from the browser, mid-demo**, and the agent repairs its own adapter with no code change and no restart. This kills the "it's just a recorded selector cache" objection.

Run entirely locally. Next.js on `:3010`. Real key or `SKILLSHIFT_MOCK_LLM=1`.

## Why the naive version fails (read this before coding)

Renaming a button's **label** only is a no-op: cached `resolved_targets` hold `data-testid` values, so replay still clicks the same node and nothing adapts.

Every perturbation must therefore change the **DOM contract**:

- rename → old `data-testid` is gone, a new one appears
- extra required field → a new control gates the finish action
- reorder → old nav `data-testid` is gone, replaced by a differently-named one

## Perturbation state must survive navigation

The agent calls `page.goto("/store-b")`, so URL query params and React state are lost. Persist flags in a file, same pattern as `fixtures/live/store-b-products.json`:

`fixtures/live/perturbations.json`

```json
{ "rename_publish": false, "extra_required": false, "reorder_nav": false }
```

Add `web/app/api/perturbations/route.ts`:

- `GET` → current flags (defaults all `false` if the file is missing). `Cache-Control: no-store`.
- `POST` → merge partial flags, write the file, return the new state.
- Use the existing `repoFile()` helper from `@/lib/repo-paths`. `runtime = "nodejs"`, `dynamic = "force-dynamic"`.

Store B polls `GET /api/perturbations` on the same 1s interval it already uses for live products (reuse that `useEffect` shape; do not add a second timer if you can fold it in).

## Judge controls (UI)

Put them on `/store-b` itself, in the sidebar under the nav, as a small block:

```text
Judge controls          data-testid="store-b-judge-panel"
[ ] Rename publish      data-testid="store-b-perturb-rename"
[ ] Extra required field data-testid="store-b-perturb-required"
[ ] Reorder navigation  data-testid="store-b-perturb-reorder"
```

Muted, small, clearly out-of-app chrome (reuse existing muted classes in `globals.css`; add at most one new class). Toggling POSTs and optimistically updates. The agent must never click these: they are the judge's, and the Explorer is allowed to ignore them because they are not part of the seller app.

## The three perturbations (Store B only)

**1. `rename_publish`**

- `store-b-go-live` must **not render**.
- Instead render a button labelled **"Launch Product"** with `data-testid="store-b-launch-product"`, same `canGoLive` disabled logic, same `goLive()` handler.

**2. `extra_required`**

- New required select above Listing type: label **"Tax class"**, `data-testid="store-b-field-tax-class"`, options `""` (Select tax class) / `Standard rate` / `Reduced rate` / `Zero rated`.
- `canGoLive` also requires a non-empty tax class.
- When details are ready and tax class is empty, show `data-testid="store-b-tax-blocker"`: "Choose a tax class to go live."
- Wording must not name the finish button, so the agent has to reason from the blocker plus the disabled control.

**3. `reorder_nav`**

- Nav order becomes `Orders`, `Analytics` (inert, `store-b-nav-analytics`), `Collections`, `Catalog`.
- The inventory entry renders as **"Catalog"** with `data-testid="store-b-nav-catalog"`; `store-b-nav-inventory` must not render. Same section behaviour.

Flags compose. All three off ⇒ today's Store B, byte-identical behaviour.

## Agent side

Do **not** add perturbation-specific branches to `explorer.py` / `verifier.py` / `recovery.py` / `transfer_loop.py`. The point is that the Wave 7 loop already handles this. Your job is to make sure it does:

1. Observation must pick up the new controls automatically (it reads the live DOM — confirm, don't special-case).
2. Cached replay must fail **cleanly** when a saved testid is absent: if `page.get_by_test_id(t).count() == 0`, do not throw a raw Playwright timeout — surface it as a diagnosable failure so the diagnoser can classify `stale_mapping` and the loop re-grounds via the Explorer. Fix that in the replay path (`execute_resolved_targets` / `transfer_loop`) generically, keyed on "saved testid missing", never on which testid.
3. After a successful re-ground, the curator (7C) must persist a `replace_mapping` patch and bump `adapter_version`, so the third run is a cache hit on the new control.
4. Extend mock-LLM heuristics by **control kind/suffix** (`-launch-product`, `-field-tax-class`, `-nav-catalog`) so CI passes without a key. Suffix heuristics in the mock are fine; in the live path they are not.

## Tests

`agent/tests/test_perturbation.py`:

- `rename_publish` + warm adapter ⇒ diagnoser returns `stale_mapping`, explorer re-grounds, adapter ends with the new target and a higher `adapter_version`, old rule marked deprecated/replaced.
- `extra_required` + warm adapter ⇒ `missing_prerequisite`, `add_prerequisite` patch, run completes.
- `reorder_nav` + warm adapter ⇒ create step remaps to `store-b-nav-catalog`.
- All flags off ⇒ existing Wave 7 tests unchanged (run them).

Web: assert `store-b-go-live` absent and `store-b-launch-product` present when the flag is on (component/route test, matching how `web/` is already tested).

## Guardrails

- Never edit the Skill or its four intents.
- Never edit `web/app/dashboard/**` — Agent 7F owns it. If the dashboard should show perturbations, leave a one-line note at the end of [WAVE8.md](../WAVE8.md) instead.
- Perturbation flags must not leak into the adapter schema. The adapter records what was learned, not why the environment changed.
- Reset must be trivial: POST all-false, or delete `fixtures/live/perturbations.json`. Add it to `.gitignore` if the other `fixtures/live/*` runtime files are ignored.

## Done when

1. `curl -s localhost:3010/api/perturbations` returns the flags; POSTing `{"rename_publish":true}` persists them.
2. With a warm adapter and the flag flipped in the browser, `python -m agent.run_transfer` detects the stale rule, re-grounds, verifies, patches, and the next run is a cache hit on `store-b-launch-product`.
3. Same for `extra_required` and `reorder_nav`.
4. `pytest agent/tests` green, `npm run lint && npm run build` green in `web/`.
5. Append a "Perturbations" section to [shared/routes.md](../shared/routes.md) documenting the flags, the swapped testids, and the judge-panel testids.

Report at the end: for each flag, the observed `failure_class`, the chosen new target, the patch kind, and the `adapter_version` before/after.
