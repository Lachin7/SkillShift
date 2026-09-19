"use client";

import { CatalogPicker } from "@/components/CatalogPicker";
import { formatPrice, type Product } from "@/lib/types";
import Link from "next/link";
import { useState } from "react";

type Section = "collections" | "inventory" | "orders";

type Collection = {
  name: string;
  note: string;
};

const SEED_COLLECTIONS: Collection[] = [
  { name: "Spring Essentials", note: "0 products in this group" },
  { name: "Staff Picks", note: "0 products in this group" },
];

export default function StoreBPage() {
  const [section, setSection] = useState<Section>("collections");
  const [creatingListing, setCreatingListing] = useState(false);
  const [creatingCollection, setCreatingCollection] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [collections, setCollections] = useState<Collection[]>(SEED_COLLECTIONS);
  const [collectionName, setCollectionName] = useState("");
  const [collectionNote, setCollectionNote] = useState("");
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [image, setImage] = useState("");

  const canGoLive =
    name.trim().length > 0 && price.trim().length > 0 && image.length > 0;
  const draft = { name, image };

  function onImage(file: File | undefined) {
    if (!file) return;
    setImage(URL.createObjectURL(file));
  }

  function goLive() {
    if (!canGoLive) return;
    setProducts((current) => [
      ...current,
      { name: name.trim(), price: formatPrice(price), image },
    ]);
    setName("");
    setPrice("");
    setImage("");
    setCreatingListing(false);
    setSection("inventory");
  }

  function saveCollection() {
    if (!collectionName.trim()) return;
    setCollections((current) => [
      ...current,
      {
        name: collectionName.trim(),
        note: collectionNote.trim() || "Empty merchandising group",
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
        </nav>
      </aside>

      <main className="b-main">
        {section === "collections" && (
          <>
            <div className="b-toolbar">
              <div>
                <h1>Collections</h1>
                <p className="b-lead">
                  Groups for products already in inventory. This is not product
                  creation.
                </p>
              </div>
              <button
                type="button"
                className="b-btn warn"
                data-testid="store-b-collections-create"
                onClick={() => setCreatingCollection(true)}
              >
                Create
              </button>
            </div>
            <div className="b-note">
              Collection management only. New sellable items live under Inventory.
            </div>
            {creatingCollection && (
              <section className="b-panel" style={{ marginBottom: 20 }}>
                <h2>New collection</h2>
                <p className="b-lead">Name a group. Add inventory to it later.</p>
                <label className="field">
                  Collection name
                  <input
                    value={collectionName}
                    onChange={(event) => setCollectionName(event.target.value)}
                    placeholder="Archive"
                  />
                </label>
                <label className="field">
                  Internal note
                  <input
                    value={collectionNote}
                    onChange={(event) => setCollectionNote(event.target.value)}
                    placeholder="Seasonal merchandising group"
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
                  <h3>{collection.name}</h3>
                  <p>{collection.note}</p>
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
              One form. Name, price, and image. Finish with Go Live.
            </p>
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
            <div className="b-actions">
              <button
                type="button"
                className="b-btn"
                onClick={() => setCreatingListing(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="b-btn primary"
                data-testid="store-b-go-live"
                disabled={!canGoLive}
                onClick={goLive}
              >
                Go Live
              </button>
            </div>
          </section>
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
