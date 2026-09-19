"use client";

import { formatPrice, type Product } from "@/lib/types";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Section = "collections" | "inventory" | "orders";

type Collection = {
  name: string;
  note: string;
};

const SEED_COLLECTIONS: Collection[] = [
  { name: "春の定番", note: "0 件" },
  { name: "おすすめ", note: "0 件" },
  { name: "新着", note: "0 件" },
];

function mergeProducts(persisted: Product[], local: Product[]): Product[] {
  const seen = new Set<string>();
  const merged: Product[] = [];
  for (const product of [...persisted, ...local]) {
    const key = `${product.name}|${product.price}`;
    if (seen.has(key)) continue;
    seen.add(key);
    merged.push(product);
  }
  return merged;
}

export default function StoreDPage() {
  // data-testid values are ASCII infrastructure for the hands, not semantics for the brain.
  const [section, setSection] = useState<Section>("collections");
  const [creatingListing, setCreatingListing] = useState(false);
  const [persisted, setPersisted] = useState<Product[]>([]);
  const [localProducts, setLocalProducts] = useState<Product[]>([]);
  const products = useMemo(
    () => mergeProducts(persisted, localProducts),
    [persisted, localProducts],
  );
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [image, setImage] = useState("");
  const [shipping, setShipping] = useState("");
  const [listingType, setListingType] = useState("Public");

  const detailsReady =
    name.trim().length > 0 && price.trim().length > 0 && image.length > 0;
  const canGoLive = detailsReady && shipping.length > 0;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("/api/live-products?app=store-d", { cache: "no-store" });
        const data = (await response.json()) as { products?: Product[] };
        if (!cancelled && Array.isArray(data.products)) setPersisted(data.products);
      } catch {
        /* human create still works */
      }
    }
    void load();
    const timer = window.setInterval(() => void load(), 1000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  function onImage(file: File | undefined) {
    if (!file) return;
    setImage(URL.createObjectURL(file));
  }

  function publish() {
    if (!canGoLive) return;
    setLocalProducts((current) => [
      ...current,
      { name: name.trim(), price: formatPrice(price), image },
    ]);
    setName("");
    setPrice("");
    setImage("");
    setShipping("");
    setListingType("Public");
    setCreatingListing(false);
    setSection("inventory");
  }

  return (
    <div className="store-b store-d" lang="ja">
      <aside className="b-side">
        <Link className="store-back" href="/">
          戻る
        </Link>
        <p className="b-brand">みなと商店</p>
        <nav className="b-nav">
          <button
            type="button"
            data-testid="store-d-nav-collections"
            className={section === "collections" ? "active" : ""}
            onClick={() => {
              setSection("collections");
              setCreatingListing(false);
            }}
          >
            コレクション
          </button>
          <button
            type="button"
            data-testid="store-d-nav-inventory"
            className={section === "inventory" ? "active" : ""}
            onClick={() => {
              setSection("inventory");
            }}
          >
            在庫
          </button>
          <button
            type="button"
            data-testid="store-d-nav-orders"
            className={section === "orders" ? "active" : ""}
            onClick={() => {
              setSection("orders");
              setCreatingListing(false);
            }}
          >
            注文
          </button>
        </nav>
      </aside>
      <main className="b-main">
        {section === "collections" && (
          <>
            <h1>コレクション</h1>
            <p className="b-lead">商品をまとめるための画面です。</p>
            <div className="b-grid">
              {SEED_COLLECTIONS.map((collection) => (
                <article key={collection.name} className="b-collection">
                  <div className="b-collection-mosaic" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="b-collection-body">
                    <h3>{collection.name}</h3>
                    <p>{collection.note}</p>
                  </div>
                </article>
              ))}
            </div>
          </>
        )}

        {section === "inventory" && !creatingListing && (
          <>
            <div className="b-toolbar">
              <div>
                <h1>在庫一覧</h1>
              </div>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-d-create-listing"
                onClick={() => setCreatingListing(true)}
              >
                出品を作成
              </button>
            </div>
            {products.length === 0 ? (
              <section className="b-panel">
                <p className="b-lead" style={{ margin: 0 }}>
                  出品はまだありません。
                </p>
              </section>
            ) : (
              <div className="b-grid">
                {products.map((product, index) => (
                  <article
                    key={`${product.name}-${index}`}
                    className="b-card"
                    data-testid="store-d-product-card"
                  >
                    <img src={product.image} alt="" />
                    <div>
                      <h3>{product.name}</h3>
                      <p>{formatPrice(product.price)}</p>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </>
        )}

        {section === "inventory" && creatingListing && (
          <section className="b-panel">
            <h1>出品の作成</h1>
            <label className="field">
              価格
              <input
                data-testid="store-d-field-price"
                value={price}
                onChange={(event) => setPrice(event.target.value)}
              />
            </label>
            <label className="field">
              商品名
              <input data-testid="store-d-field-name" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field">
              配送カテゴリ
              <select
                data-testid="store-d-field-shipping"
                value={shipping}
                onChange={(event) => setShipping(event.target.value)}
              >
                <option value="">選択してください</option>
                <option value="Standard">通常配送</option>
                <option value="Express">速達</option>
                <option value="Freight">大型便</option>
              </select>
            </label>
            <label className="field">
              商品画像
              <input
                type="file"
                accept="image/*"
                data-testid="store-d-field-image"
                onChange={(event) => onImage(event.target.files?.[0])}
              />
            </label>
            {image ? (
              <div className="b-preview">
                <img src={image} alt="" />
              </div>
            ) : null}
            <label className="field">
              公開設定
              <select
                data-testid="store-d-field-listing-type"
                value={listingType}
                onChange={(event) => setListingType(event.target.value)}
              >
                <option value="Public">公開</option>
                <option value="Draft">下書き</option>
              </select>
            </label>
            {detailsReady && !shipping ? (
              <p className="b-shipping-blocker" data-testid="store-d-shipping-blocker">
                公開するには配送カテゴリを選択してください。
              </p>
            ) : null}
            <div className="b-actions">
              <button type="button" className="b-btn" onClick={() => setCreatingListing(false)}>
                キャンセル
              </button>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-d-publish"
                disabled={!canGoLive}
                onClick={publish}
              >
                公開する
              </button>
            </div>
          </section>
        )}

        {section === "orders" && (
          <>
            <h1>注文</h1>
            <p className="b-lead">注文はまだありません。</p>
          </>
        )}
      </main>
    </div>
  );
}
