# Locked routes and IA

Do not invent extra seller features, auth, or a database.

## Apps

| Route | App id | Mental model | Create path | Finish | Success |
| --- | --- | --- | --- | --- | --- |
| `/store-a` | `store-a` | Multi-step wizard | `Products → Add Product → Media → Publish` | Publish | Product card |
| `/store-b` | `store-b` | Single-page form | `Inventory → Create Listing` | Go Live | Product card |
| `/store-c` | `store-c` | Table + drawer | `Listings → Add row` | Status Live + Save row | Product card |
| `/store-d` | `store-d` | Store B twin, Japanese labels | `在庫 → 出品を作成` | 公開する | Product card |
| `/dashboard` | — | Four cards | — | — | Skill / App / Adapter / Status |

Store B nav **must** include a plausible decoy:

```text
Collections    ← trap (not product creation)
Inventory      ← correct
Orders
```

## Product fields

`name`, `price`, `image`

Demo products:

| Run | name | price | image |
| --- | --- | --- | --- |
| Teach / first transfer | Leather Bag | £89 | any bag-like image or placeholder |
| Second run | Blue Sneaker | £120 | any sneaker-like image or placeholder |

## Skill / adapter identity

- Skill name: `publish_product`
- Adapter file: `adapters/store_b__publish_product.json`
- Intents (exact strings — both agents use these):

1. `start creating a new sellable item`
2. `provide basic product information`
3. `attach the product image`
4. `make the product publicly available`

## Stable selectors (for a later executor)

Agent A should put these `data-testid` values on the real controls so Wave 2 Playwright does not guess.

### Store A

- `store-a-nav-products`
- `store-a-add-product`
- `store-a-field-name`
- `store-a-field-price`
- `store-a-field-image`
- `store-a-publish`
- `store-a-product-card`

### Store B

- `store-b-nav-collections`
- `store-b-nav-inventory`
- `store-b-nav-orders`
- `store-b-create-listing`
- `store-b-field-name`
- `store-b-field-price`
- `store-b-field-image`
- `store-b-field-shipping`
- `store-b-shipping-blocker`
- `store-b-campaign-banner`
- `store-b-field-promo`
- `store-b-promo-blocker`
- `store-b-field-listing-type`
- `store-b-go-live`
- `store-b-product-card`
- `store-b-collections-create`

### Store C

Northwind Market. Prerequisite is **category**, not shipping. Finish is two actions: `store-c-field-status` → Live, then `store-c-save-row`.

- `store-c-nav-overview`, `store-c-nav-listings`, `store-c-nav-payouts`
- `store-c-new-row`, `store-c-row-edit`, `store-c-drawer`, `store-c-drawer-close`
- `store-c-field-title`, `store-c-field-amount`, `store-c-field-photo`, `store-c-field-category`
- `store-c-field-status`, `store-c-save-row`, `store-c-category-blocker`
- `store-c-row-status`, `store-c-product-card`

### Store D

みなと商店. Structurally a twin of Store B; every visible string is Japanese. `data-testid` values stay ASCII (hands infrastructure, not brain semantics). Finish is `store-d-publish`, not `*-go-live`. Field order: price, name, shipping, image, listing type.

| Element | Copy |
| --- | --- |
| Brand | みなと商店 |
| Nav | コレクション / 在庫 / 注文 |
| Inventory heading | 在庫一覧 |
| Create | 出品を作成 |
| Form heading | 出品の作成 |
| Fields | 価格 / 商品名 / 配送カテゴリ / 商品画像 / 公開設定 |
| Shipping options | 選択してください / 通常配送 / 速達 / 大型便 |
| Listing type | 公開 / 下書き |
| Finish | 公開する |
| Cancel | キャンセル |
| Blocker | 公開するには配送カテゴリを選択してください。 |
| Empty inventory | 出品はまだありません。 |

- `store-d-nav-collections`, `store-d-nav-inventory`, `store-d-nav-orders`
- `store-d-create-listing`
- `store-d-field-price`, `store-d-field-name`, `store-d-field-shipping`, `store-d-field-image`, `store-d-field-listing-type`
- `store-d-shipping-blocker`, `store-d-publish`, `store-d-product-card`

## Perturbations (Store B judge controls)

Flags live in `fixtures/live/perturbations.json` and `GET`/`POST` `/api/perturbations`. They survive `page.goto`. All false ⇒ today’s Store B.

| Flag | DOM change | Expected failure |
| --- | --- | --- |
| `rename_publish` | remove `store-b-go-live`; add `store-b-launch-product` (“Launch Product”) | `stale_mapping` → `replace_mapping` |
| `extra_required` | add `store-b-field-tax-class` + `store-b-tax-blocker` | `missing_prerequisite` → `add_prerequisite` |
| `reorder_nav` | remove `store-b-nav-inventory`; add `store-b-nav-catalog` (“Catalog”); nav becomes Orders / Analytics / Collections / Catalog | `wrong_mapping` / `navigation_error` |

Judge chrome (never part of the seller app):

- `store-b-judge-panel`
- `store-b-perturb-rename`
- `store-b-perturb-required`
- `store-b-perturb-reorder`

## Dashboard cards

Left to right: **Learned Skill** · **Current App** · **Adapter** · **Status**

Payload shape: [examples/dashboard-state.json](examples/dashboard-state.json).
Support a `phase` of `mismatch` | `recovered` | `cached` so the Adapter card can turn a mapping red, then rewrite it.

## Test-only Store B state API

Verifier ground truth. **Not** for Explorer or Recovery.

`GET /api/store-b-state?title=Leather%20Bag`

```json
{
  "product_exists": true,
  "title": "Leather Bag",
  "price": "89",
  "status": "published",
  "purchasable": true
}
```

`status` is `published` when a matching live product exists, otherwise `none`. `purchasable` is true only when published. Reads `fixtures/live/store-b-products.json`.
