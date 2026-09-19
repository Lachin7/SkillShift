# Agent 8C — Store D: same structure, Japanese labels

You are Agent 8C on SkillShift. Read [WAVE8.md](../docs/build/WAVE8.md) first, then [prompts/agent-8b.md](agent-8b.md) (you depend on its `AppTarget` registry), [shared/routes.md](../shared/routes.md), and `agent/transfer_loop.py`.

**Do not start until 8B has landed.** You need `agent/targets.py` and the de-`store-b-`-ified live path.

## Goal

Add **Store D**: structurally a twin of Store B, but every visible string is Japanese. Then publish with the same frozen Skill. This isolates one variable — language — and makes "it's just string matching on *publish*" impossible to argue.

Run locally. Next.js on `:3010`.

## Design rules

- **Every** visible string in Japanese: nav, headings, field labels, placeholders, button text, blocker text, empty states. No English fallback text, no bilingual labels, no English `title`/`aria-label` cheats. Set `lang="ja"` on the Store D root.
- `data-testid` values stay ASCII. They are infrastructure for the hands, not semantics for the brain — say so in a comment.
- Structure matches Store B (nav with a decoy, create form, shipping-category gate, finish control) so the only changed variable is language.
- Two deliberate anti-cheat details:
  1. The finish control is `data-testid="store-d-publish"`, **not** `store-d-go-live` — so no suffix table can carry the finish action over from B.
  2. Field order differs from B: price, then name, then shipping category, then image, then listing type.
- Product data stays English (`Leather Bag`, `£89`) so verification and `formatPrice` are unchanged. Currency stays `£`; ¥ is deferred.

## Copy (use exactly this — do not invent Japanese)

| Element | Japanese |
| --- | --- |
| Brand | みなと商店 |
| Nav: Collections (decoy) | コレクション |
| Nav: Inventory (correct) | 在庫 |
| Nav: Orders | 注文 |
| Inventory heading | 在庫一覧 |
| Create listing button | 出品を作成 |
| Form heading | 出品の作成 |
| Price | 価格 |
| Name | 商品名 |
| Shipping category | 配送カテゴリ |
| Shipping options | 選択してください / 通常配送 / 速達 / 大型便 |
| Image | 商品画像 |
| Listing type | 公開設定 |
| Listing type options | 公開 / 下書き |
| Finish button | 公開する |
| Cancel | キャンセル |
| Shipping blocker | 公開するには配送カテゴリを選択してください。 |
| Empty inventory | 出品はまだありません。 |

## Testids

`store-d-nav-collections`, `store-d-nav-inventory`, `store-d-nav-orders`, `store-d-create-listing`, `store-d-field-price`, `store-d-field-name`, `store-d-field-shipping`, `store-d-field-image`, `store-d-field-listing-type`, `store-d-shipping-blocker`, `store-d-publish`, `store-d-product-card`.

Gate: the finish control stays disabled until name, price, image, and shipping category are set — identical logic to Store B's `canGoLive`.

## Wiring

- `web/app/store-d/page.tsx`; add a CJK-safe font fallback (`"Hiragino Sans", "Noto Sans JP", sans-serif`) scoped to `.store-d`.
- Register `store-d` in `agent/targets.py`: path `/store-d`, prefix `store-d-`, card `store-d-product-card`, live file `fixtures/live/store-d-products.json`, adapter `adapters/store_d__publish_product.json` (starts empty).
- Extend `GET /api/live-products?app=store-d` and the test-only state API's `app` param (both already parameterised by 8B).
- Add a `/store-d` card to `web/app/page.tsx` (its label may be Japanese with a small English gloss — the home page is SkillShift chrome, not the app).

## Agent side

Nothing app-specific. If you find yourself adding a Japanese keyword list anywhere in `agent/`, stop — that is exactly the cheat this store exists to disprove. The Explorer reads labels plus the screenshot and reasons.

Mock-LLM heuristics may match on testid suffix so CI runs keyless, **but** be explicit in the test docstring that mock tests prove plumbing only. The semantic claim is proven by a real-key run, which is part of Done when.

## Tests

`agent/tests/test_store_d.py`, mock LLM:

- cold start on `store-d` from empty adapter → four mappings, ≥1 recovery for the shipping gate, product live
- second run is a cache hit with lower model calls
- assert no Store D adapter path is read when `SKILLSHIFT_TARGET_APP` is `store-b`
- a lint-style test (or a simple regex scan over `web/app/store-d/page.tsx`) asserting no ASCII letters appear in user-visible label/button/option text — testids, class names, and imports excluded

## Done when

1. `SKILLSHIFT_TARGET_APP=store-d python -m agent.run_transfer` with a **real key** publishes from an empty adapter, discovering 配送カテゴリ as the prerequisite. Save the terminal transcript and a screenshot of the finished store into `docs/` (or wherever prior runs are kept) — that is the demo evidence.
2. `pytest agent/tests` green with the mock. `npx tsc --noEmit && npm run build` green.
3. Stores A/B/C unchanged.
4. [shared/routes.md](../shared/routes.md) gains a Store D section with the copy table and testids.

Report at the end: the four learned mappings with the Japanese label the Explorer picked for each, the recovery it ran for the shipping gate, and run 1 vs run 2 metrics.
