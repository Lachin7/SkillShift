"use client";

import { CatalogPicker } from "@/components/CatalogPicker";
import { formatPrice, type Product } from "@/lib/types";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Section = "collections" | "inventory" | "orders" | "analytics";

type PerturbationFlags = {
  rename_publish: boolean;
  extra_required: boolean;
  reorder_nav: boolean;
};

const DEFAULT_PERTURBATIONS: PerturbationFlags = {
  rename_publish: false,
  extra_required: false,
  reorder_nav: false,
};

type Collection = {
  name: string;
  note: string;
};

const SEED_COLLECTIONS: Collection[] = [
  { name: "Spring Essentials", note: "0 items" },
  { name: "Staff Picks", note: "0 items" },
  { name: "New arrivals", note: "0 items" },
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

export default function StoreBPage() {
  const [section, setSection] = useState<Section>("collections");
  const [creatingListing, setCreatingListing] = useState(false);
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [persisted, setPersisted] = useState<Product[]>([]);
  const [localProducts, setLocalProducts] = useState<Product[]>([]);
  const [perturb, setPerturb] = useState<PerturbationFlags>(DEFAULT_PERTURBATIONS);
  const [flagsReady, setFlagsReady] = useState(false);
  const products = useMemo(
    () => mergeProducts(persisted, localProducts),
    [persisted, localProducts],
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [productsResponse, flagsResponse] = await Promise.all([
          fetch("/api/live-products", { cache: "no-store" }),
          fetch("/api/perturbations", { cache: "no-store" }),
        ]);
        const data = (await productsResponse.json()) as { products?: Product[] };
        if (!cancelled && Array.isArray(data.products)) {
          setPersisted(data.products);
        }
        const flags = (await flagsResponse.json()) as Partial<PerturbationFlags>;
        if (!cancelled) {
          setPerturb({
            rename_publish: Boolean(flags.rename_publish),
            extra_required: Boolean(flags.extra_required),
            reorder_nav: Boolean(flags.reorder_nav),
          });
          setFlagsReady(true);
        }
      } catch {
        if (!cancelled) setFlagsReady(true);
      }
    }

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, 1000);
    const onFocus = () => {
      void load();
    };
    window.addEventListener("focus", onFocus);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
    };
  }, []);
  const [collections, setCollections] = useState<Collection[]>(SEED_COLLECTIONS);
  const [collectionName, setCollectionName] = useState("");
  const [collectionNote, setCollectionNote] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [image, setImage] = useState("");
  const [shipping, setShipping] = useState("");
  const [promo, setPromo] = useState("");
  const [listingType, setListingType] = useState("Public");
  const [taxClass, setTaxClass] = useState("");

  const detailsReady =
    name.trim().length > 0 && price.trim().length > 0 && image.length > 0;
  // R1: shipping is the real procedural gate. Campaign/LAUNCH10 deferred to R2.
  const canGoLive =
    detailsReady && shipping.length > 0 && (!perturb.extra_required || taxClass.length > 0);
  const draft = { name, image };

  function onImage(file: File | undefined) {
    if (!file) return;
    setImage(URL.createObjectURL(file));
  }

  function goLive() {
    if (!canGoLive) return;
    setLocalProducts((current) => [
      ...current,
      { name: name.trim(), price: formatPrice(price), image },
    ]);
    setName("");
    setPrice("");
    setImage("");
    setShipping("");
    setPromo("");
    setListingType("Public");
    setTaxClass("");
    setCreatingListing(false);
    setSection("inventory");
  }

  async function togglePerturb(key: keyof PerturbationFlags) {
    const next = { ...perturb, [key]: !perturb[key] };
    setPerturb(next);
    try {
      const response = await fetch("/api/perturbations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      });
      const saved = (await response.json()) as Partial<PerturbationFlags>;
      setPerturb({
        rename_publish: Boolean(saved.rename_publish),
        extra_required: Boolean(saved.extra_required),
        reorder_nav: Boolean(saved.reorder_nav),
      });
    } catch {
      setPerturb(perturb);
    }
  }

  function saveCollection() {
    if (!collectionName.trim()) return;
    setCollections((current) => [
      ...current,
      {
        name: collectionName.trim(),
        note: collectionNote.trim() || "0 items",
      },
    ]);
    setCollectionName("");
    setCollectionNote("");
    setCreatingCollection(false);
  }

  return (
    <div className="store-b">
      <aside className="b-side">
        <Link className="store-back" href="/">
          SkillShift
        </Link>
        <p className="b-brand">Harbor Ledger</p>
        <nav className="b-nav">
          {!flagsReady ? null : perturb.reorder_nav ? (
            <>
              <button
                type="button"
                data-testid="store-b-nav-orders"
                className={section === "orders" ? "active" : ""}
                onClick={() => {
                  setSection("orders");
                  setCreatingListing(false);
                  setCreatingCollection(false);
                }}
              >
                Orders
              </button>
              <button
                type="button"
                data-testid="store-b-nav-analytics"
                className={section === "analytics" ? "active" : ""}
                onClick={() => {
                  setSection("analytics");
                  setCreatingListing(false);
                  setCreatingCollection(false);
                }}
              >
                Analytics
              </button>
              <button
                type="button"
                data-testid="store-b-nav-collections"
                className={section === "collections" ? "active" : ""}
                onClick={() => {
                  setSection("collections");
                  setCreatingListing(false);
                }}
              >
                Collections
              </button>
              <button
                type="button"
                data-testid="store-b-nav-catalog"
                className={section === "inventory" ? "active" : ""}
                onClick={() => {
                  setSection("inventory");
                  setCreatingCollection(false);
                }}
              >
                Catalog
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                data-testid="store-b-nav-collections"
                className={section === "collections" ? "active" : ""}
                onClick={() => {
                  setSection("collections");
                  setCreatingListing(false);
                }}
              >
                Collections
              </button>
              <button
                type="button"
                data-testid="store-b-nav-inventory"
                className={section === "inventory" ? "active" : ""}
                onClick={() => {
                  setSection("inventory");
                  setCreatingCollection(false);
                }}
              >
                Inventory
              </button>
              <button
                type="button"
                data-testid="store-b-nav-orders"
                className={section === "orders" ? "active" : ""}
                onClick={() => {
                  setSection("orders");
                  setCreatingListing(false);
                  setCreatingCollection(false);
                }}
              >
                Orders
              </button>
            </>
          )}
        </nav>
        <section className="b-judge" data-testid="store-b-judge-panel">
          <p>Judge controls</p>
          <label>
            <input
              type="checkbox"
              data-testid="store-b-perturb-rename"
              checked={perturb.rename_publish}
              onChange={() => void togglePerturb("rename_publish")}
            />
            Rename publish
          </label>
          <label>
            <input
              type="checkbox"
              data-testid="store-b-perturb-required"
              checked={perturb.extra_required}
              onChange={() => void togglePerturb("extra_required")}
            />
            Extra required field
          </label>
          <label>
            <input
              type="checkbox"
              data-testid="store-b-perturb-reorder"
              checked={perturb.reorder_nav}
              onChange={() => void togglePerturb("reorder_nav")}
            />
            Reorder navigation
          </label>
        </section>
      </aside>

      <main className="b-main">
        {section === "collections" && (
          <>
            <div className="b-toolbar">
              <div>
                <h1>Collections</h1>
                <p className="b-lead">
                  Build merchandising groups for your catalog. Create a collection,
                  then add items to it.
                </p>
                <p className="b-meta">
                  {collections.length} collections · 0 items
                </p>
              </div>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-b-collections-create"
                onClick={() => setCreatingCollection(true)}
              >
                Create
              </button>
            </div>
            {creatingCollection && (
              <section className="b-panel" style={{ marginBottom: 20 }}>
                <h2>New collection</h2>
                <p className="b-lead">Name the group and how it should appear.</p>
                <label className="field">
                  Collection name
                  <input
                    value={collectionName}
                    onChange={(event) => setCollectionName(event.target.value)}
                    placeholder="Holiday edit"
                  />
                </label>
                <label className="field">
                  Display note
                  <input
                    value={collectionNote}
                    onChange={(event) => setCollectionNote(event.target.value)}
                    placeholder="Homepage row · seasonal"
                  />
                </label>
                <div className="b-actions">
                  <button
                    type="button"
                    className="b-btn"
                    onClick={() => setCreatingCollection(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="b-btn primary"
                    disabled={!collectionName.trim()}
                    onClick={saveCollection}
                  >
                    Save collection
                  </button>
                </div>
              </section>
            )}
            <div className="b-grid">
              {collections.map((collection) => (
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
                <h1>Inventory</h1>
                <p className="b-lead">Live listings. Create one, then go live.</p>
              </div>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-b-create-listing"
                onClick={() => setCreatingListing(true)}
              >
                Create Listing
              </button>
            </div>
            {products.length === 0 ? (
              <section className="b-panel">
                <p className="b-lead" style={{ margin: 0 }}>
                  No live listings yet.
                </p>
              </section>
            ) : (
              <div className="b-grid">
                {products.map((product, index) => (
                  <article
                    key={`${product.name}-${index}`}
                    className="b-card"
                    data-testid="store-b-product-card"
                  >
                    <img src={product.image} alt={product.name} />
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
            <h1>Create Listing</h1>
            <p className="b-lead">
              Name, price, image, and shipping category. Finish with Go Live.
            </p>
            <div className="b-campaign-banner" data-testid="store-b-campaign-banner" hidden>
              Campaign codes return in a later wave.
            </div>
            <CatalogPicker
              tone="b"
              selected={draft}
              onPick={(item) => {
                setName(item.name);
                setPrice(item.price);
                setImage(item.image);
              }}
            />
            <label className="field">
              Name
              <input
                data-testid="store-b-field-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Leather Bag"
              />
            </label>
            <label className="field">
              Price
              <input
                data-testid="store-b-field-price"
                value={price}
                onChange={(event) => setPrice(event.target.value)}
                placeholder="89"
              />
            </label>
            <label className="field">
              Image
              <input
                type="file"
                accept="image/*"
                data-testid="store-b-field-image"
                onChange={(event) => onImage(event.target.files?.[0])}
              />
            </label>
            {image && (
              <div className="b-preview">
                <img src={image} alt="Listing preview" />
              </div>
            )}
            <label className="field">
              Shipping category
              <select
                data-testid="store-b-field-shipping"
                value={shipping}
                onChange={(event) => setShipping(event.target.value)}
              >
                <option value="">Select category</option>
                <option value="Standard">Standard</option>
                <option value="Express">Express</option>
                <option value="Freight">Freight</option>
              </select>
            </label>
            {perturb.extra_required ? (
              <label className="field">
                Tax class
                <select
                  data-testid="store-b-field-tax-class"
                  value={taxClass}
                  onChange={(event) => setTaxClass(event.target.value)}
                >
                  <option value="">Select tax class</option>
                  <option value="Standard rate">Standard rate</option>
                  <option value="Reduced rate">Reduced rate</option>
                  <option value="Zero rated">Zero rated</option>
                </select>
              </label>
            ) : null}
            <label className="field">
              Listing type
              <select
                data-testid="store-b-field-listing-type"
                value={listingType}
                onChange={(event) => setListingType(event.target.value)}
              >
                <option value="Public">Public</option>
                <option value="Draft">Draft</option>
              </select>
            </label>
            <label className="field" hidden>
              Campaign code
              <input
                data-testid="store-b-field-promo"
                value={promo}
                onChange={(event) => setPromo(event.target.value)}
                placeholder="Campaign code"
                autoComplete="off"
              />
            </label>
            {detailsReady && !shipping ? (
              <p className="b-shipping-blocker" data-testid="store-b-shipping-blocker">
                Select a shipping category to go live.
              </p>
            ) : null}
            {perturb.extra_required && detailsReady && shipping && !taxClass ? (
              <p className="b-shipping-blocker" data-testid="store-b-tax-blocker">
                Choose a tax class to go live.
              </p>
            ) : null}
            <div className="b-actions">
              <button
                type="button"
                className="b-btn"
                onClick={() => setCreatingListing(false)}
              >
                Cancel
              </button>
              {perturb.rename_publish ? (
                <button
                  type="button"
                  className="b-btn primary"
                  data-testid="store-b-launch-product"
                  disabled={!canGoLive}
                  onClick={goLive}
                >
                  Launch Product
                </button>
              ) : (
                <button
                  type="button"
                  className="b-btn primary"
                  data-testid="store-b-go-live"
                  disabled={!canGoLive}
                  onClick={goLive}
                >
                  Go Live
                </button>
              )}
            </div>
          </section>
        )}

        {section === "analytics" && (
          <>
            <h1>Analytics</h1>
            <p className="b-lead">Traffic arrives after listings go live.</p>
          </>
        )}

        {section === "orders" && (
          <>
            <h1>Orders</h1>
            <p className="b-lead">Incoming purchases. Nothing to fulfill yet.</p>
            <section className="b-panel">
              <table className="b-table">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Buyer</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan={3}>No orders.</td>
                  </tr>
                </tbody>
              </table>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
