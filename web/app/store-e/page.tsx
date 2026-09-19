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
  { name: "بهاره", note: "۰ مورد" },
  { name: "پیشنهادی", note: "۰ مورد" },
  { name: "تازه", note: "۰ مورد" },
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

export default function StoreEPage() {
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
        const response = await fetch("/api/live-products?app=store-e", { cache: "no-store" });
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

  function release() {
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
    <div className="store-b store-e" lang="fa" dir="rtl">
      <aside className="b-side">
        <Link className="store-back" href="/">
          بازگشت
        </Link>
        <p className="b-brand">فروشگاه بندر</p>
        <nav className="b-nav">
          <button
            type="button"
            data-testid="store-e-nav-collections"
            className={section === "collections" ? "active" : ""}
            onClick={() => {
              setSection("collections");
              setCreatingListing(false);
            }}
          >
            مجموعه‌ها
          </button>
          <button
            type="button"
            data-testid="store-e-nav-inventory"
            className={section === "inventory" ? "active" : ""}
            onClick={() => {
              setSection("inventory");
            }}
          >
            موجودی
          </button>
          <button
            type="button"
            data-testid="store-e-nav-orders"
            className={section === "orders" ? "active" : ""}
            onClick={() => {
              setSection("orders");
              setCreatingListing(false);
            }}
          >
            سفارش‌ها
          </button>
        </nav>
      </aside>
      <main className="b-main">
        {section === "collections" && (
          <>
            <h1>مجموعه‌ها</h1>
            <p className="b-lead">برای دسته‌بندی کالاها است.</p>
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
                <h1>فهرست موجودی</h1>
              </div>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-e-create-listing"
                onClick={() => setCreatingListing(true)}
              >
                ایجاد آگهی
              </button>
            </div>
            {products.length === 0 ? (
              <section className="b-panel">
                <p className="b-lead" style={{ margin: 0 }}>
                  هنوز آگهی‌ای نیست.
                </p>
              </section>
            ) : (
              <div className="b-grid">
                {products.map((product, index) => (
                  <article
                    key={`${product.name}-${index}`}
                    className="b-card"
                    data-testid="store-e-product-card"
                  >
                    <img src={product.image} alt="" />
                    <div dir="ltr">
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
            <h1>ساخت آگهی</h1>
            <label className="field">
              نام کالا
              <input data-testid="store-e-field-name" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field">
              دستهٔ ارسال
              <select
                data-testid="store-e-field-shipping"
                value={shipping}
                onChange={(event) => setShipping(event.target.value)}
              >
                <option value="">انتخاب کنید</option>
                <option value="Standard">عادی</option>
                <option value="Express">سریع</option>
                <option value="Freight">باربری</option>
              </select>
            </label>
            <label className="field">
              قیمت
              <input
                data-testid="store-e-field-price"
                value={price}
                onChange={(event) => setPrice(event.target.value)}
              />
            </label>
            <label className="field">
              تصویر کالا
              <input
                type="file"
                accept="image/*"
                data-testid="store-e-field-image"
                onChange={(event) => onImage(event.target.files?.[0])}
              />
            </label>
            {image ? (
              <div className="b-preview">
                <img src={image} alt="" />
              </div>
            ) : null}
            <label className="field">
              وضعیت انتشار
              <select
                data-testid="store-e-field-listing-type"
                value={listingType}
                onChange={(event) => setListingType(event.target.value)}
              >
                <option value="Public">عمومی</option>
                <option value="Draft">پیش‌نویس</option>
              </select>
            </label>
            {detailsReady && !shipping ? (
              <p className="b-shipping-blocker" data-testid="store-e-shipping-blocker">
                برای انتشار باید دستهٔ ارسال را انتخاب کنید.
              </p>
            ) : null}
            <div className="b-actions">
              <button type="button" className="b-btn" onClick={() => setCreatingListing(false)}>
                انصراف
              </button>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-e-release"
                disabled={!canGoLive}
                onClick={release}
              >
                انتشار
              </button>
            </div>
          </section>
        )}

        {section === "orders" && (
          <>
            <h1>سفارش‌ها</h1>
            <p className="b-lead">سفارشی ثبت نشده است.</p>
          </>
        )}
      </main>
    </div>
  );
}
