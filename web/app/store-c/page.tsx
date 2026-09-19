"use client";

import { CatalogPicker } from "@/components/CatalogPicker";
import { formatPrice, type Product } from "@/lib/types";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Section = "overview" | "listings" | "payouts";
type Status = "Draft" | "Scheduled" | "Live";

type Row = Product & { status: Status; category: string };

const SEED: Row = {
  name: "Canvas Tote",
  price: "£18",
  image: "/products/leather-bag.svg",
  status: "Draft",
  category: "",
};

function mergeLive(persisted: Product[], local: Row[]): Row[] {
  const extras: Row[] = persisted
    .filter((item) => !local.some((row) => row.name === item.name))
    .map((item) => ({ ...item, status: "Live" as const, category: "General" }));
  return [...local, ...extras];
}

export default function StoreCPage() {
  const [section, setSection] = useState<Section>("listings");
  const [persisted, setPersisted] = useState<Product[]>([]);
  const [rows, setRows] = useState<Row[]>([SEED]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingSeed, setEditingSeed] = useState(false);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [photo, setPhoto] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState<Status>("Draft");

  const listing = useMemo(() => mergeLive(persisted, rows), [persisted, rows]);
  const detailsReady = title.trim().length > 0 && amount.trim().length > 0 && photo.length > 0;
  const canLive = detailsReady && category.length > 0;

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const response = await fetch("/api/live-products?app=store-c", { cache: "no-store" });
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

  function openNew() {
    setEditingSeed(false);
    setTitle("");
    setAmount("");
    setPhoto("");
    setCategory("");
    setStatus("Draft");
    setDrawerOpen(true);
  }

  function saveRow() {
    if (!title.trim()) return;
    const next: Row = {
      name: title.trim(),
      price: formatPrice(amount),
      image: photo || "/products/leather-bag.svg",
      status,
      category,
    };
    if (editingSeed) {
      setRows((current) => current.map((row) => (row.name === SEED.name ? next : row)));
    } else {
      setRows((current) => [...current.filter((row) => row.name !== next.name), next]);
    }
    setDrawerOpen(false);
  }

  return (
    <div className="store-c">
      <aside className="c-side">
        <Link className="store-back" href="/">
          SkillShift
        </Link>
        <p className="c-brand">Northwind Market</p>
        <nav className="c-nav">
          <button
            type="button"
            data-testid="store-c-nav-overview"
            className={section === "overview" ? "active" : ""}
            onClick={() => setSection("overview")}
          >
            Overview
          </button>
          <button
            type="button"
            data-testid="store-c-nav-listings"
            className={section === "listings" ? "active" : ""}
            onClick={() => setSection("listings")}
          >
            Listings
          </button>
          <button
            type="button"
            data-testid="store-c-nav-payouts"
            className={section === "payouts" ? "active" : ""}
            onClick={() => setSection("payouts")}
          >
            Payouts
          </button>
        </nav>
      </aside>
      <main className="c-main">
        {section === "overview" && (
          <>
            <h1>Overview</h1>
            <p className="c-lead">Northwind is a market ops desk, not a wizard.</p>
          </>
        )}
        {section === "payouts" && (
          <>
            <h1>Payouts</h1>
            <p className="c-lead">Settlements appear after a listing is Live.</p>
          </>
        )}
        {section === "listings" && (
          <>
            <div className="c-toolbar">
              <div>
                <h1>Listings</h1>
                <p className="c-lead">Rows in a table. Publish by setting status Live, then saving.</p>
              </div>
              <button type="button" className="c-btn" data-testid="store-c-new-row" onClick={openNew}>
                Add row
              </button>
            </div>
            <table className="c-table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Amount</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {listing.map((row) => (
                  <tr key={row.name}>
                    <td>{row.name}</td>
                    <td>{row.price}</td>
                    <td>{row.category || "—"}</td>
                    <td data-testid={row.name === SEED.name ? "store-c-row-status" : undefined}>
                      {row.status}
                    </td>
                    <td>
                      {row.name === SEED.name ? (
                        <button
                          type="button"
                          data-testid="store-c-row-edit"
                          onClick={() => {
                            setEditingSeed(true);
                            setTitle(row.name);
                            setAmount(row.price.replace("£", ""));
                            setPhoto(row.image);
                            setCategory(row.category);
                            setStatus(row.status);
                            setDrawerOpen(true);
                          }}
                        >
                          Edit
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <section className="c-storefront">
              <h2>Storefront</h2>
              <div className="c-cards">
                {listing
                  .filter((row) => row.status === "Live")
                  .map((row) => (
                    <article key={row.name} className="c-card" data-testid="store-c-product-card">
                      <img src={row.image} alt={row.name} />
                      <div>
                        <h3>{row.name}</h3>
                        <p>{row.price}</p>
                      </div>
                    </article>
                  ))}
              </div>
            </section>
          </>
        )}
      </main>
      {drawerOpen ? (
        <aside className="c-drawer" data-testid="store-c-drawer">
          <button type="button" data-testid="store-c-drawer-close" onClick={() => setDrawerOpen(false)}>
            Close
          </button>
          <h2>Edit row</h2>
          <CatalogPicker
            tone="b"
            selected={{ name: title, image: photo }}
            onPick={(item) => {
              setTitle(item.name);
              setAmount(item.price);
              setPhoto(item.image);
            }}
          />
          <label className="field">
            Title
            <input data-testid="store-c-field-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
          <label className="field">
            Amount
            <input data-testid="store-c-field-amount" value={amount} onChange={(e) => setAmount(e.target.value)} />
          </label>
          {photo ? <img className="media-preview" src={photo} alt="" /> : null}
          <label className="field">
            Photo
            <input
              type="file"
              accept="image/*"
              data-testid="store-c-field-photo"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setPhoto(URL.createObjectURL(file));
              }}
            />
          </label>
          <label className="field">
            Category
            <select data-testid="store-c-field-category" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Select category</option>
              <option value="General">General</option>
              <option value="Apparel">Apparel</option>
              <option value="Home">Home</option>
            </select>
          </label>
          <label className="field">
            Status
            <select
              data-testid="store-c-field-status"
              value={status}
              onChange={(e) => setStatus(e.target.value as Status)}
            >
              <option value="Draft">Draft</option>
              <option value="Scheduled">Scheduled</option>
              <option value="Live" disabled={!canLive}>
                Live
              </option>
            </select>
          </label>
          {detailsReady && !category ? (
            <p className="c-blocker" data-testid="store-c-category-blocker">
              Set a category before a listing can go Live.
            </p>
          ) : null}
          <button type="button" className="c-btn" data-testid="store-c-save-row" onClick={saveRow}>
            Save row
          </button>
        </aside>
      ) : null}
    </div>
  );
}
