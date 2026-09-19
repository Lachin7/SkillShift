"use client";

import { CatalogPicker } from "@/components/CatalogPicker";
import { RecorderBar } from "@/components/RecorderBar";
import { useStoreARecorder } from "@/hooks/use-store-a-recorder";
import type { CatalogItem } from "@/lib/catalog";
import { formatPrice, type Product } from "@/lib/types";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";

type Step = "products" | "details" | "media" | "publish";

export default function StoreAPage() {
  const rootRef = useRef<HTMLDivElement>(null);
  const recorder = useStoreARecorder(rootRef);
  const [step, setStep] = useState<Step>("products");
  const [products, setProducts] = useState<Product[]>([]);
  const [name, setName] = useState("");
  const [price, setPrice] = useState("");
  const [image, setImage] = useState("");

  const canContinueDetails = name.trim().length > 0 && price.trim().length > 0;
  const canContinueMedia = image.length > 0;
  const canPublish = canContinueDetails && canContinueMedia;
  const draft = { name, image };

  function resetDraft() {
    setName("");
    setPrice("");
    setImage("");
  }

  function publish() {
    if (!canPublish) return;
    setProducts((current) => [
      ...current,
      { name: name.trim(), price: formatPrice(price), image },
    ]);
    resetDraft();
    setStep("products");
  }

  async function pickCatalog(item: CatalogItem, imageOnly = false) {
    if (!imageOnly) {
      await recorder.record("fill", "Product name", item.name, () => setName(item.name));
      recorder.markCommitted("Product name", item.name);
      await recorder.record("fill", "Price", item.price, () => setPrice(item.price));
      recorder.markCommitted("Price", item.price);
    }
    await recorder.record("upload", "Product image", item.image, () => setImage(item.image));
    recorder.markCommitted("Product image", item.image);
  }

  function onImageFile(file: File | undefined) {
    if (!file) return;
    const url = URL.createObjectURL(file);
    void recorder.record("upload", "Product image", file.name, () => setImage(url));
    recorder.markCommitted("Product image", file.name);
  }

  const heading = useMemo(() => {
    if (step === "details") return "Add Product";
    if (step === "media") return "Media";
    if (step === "publish") return "Publish";
    return "Products";
  }, [step]);

  return (
    <div className="store-a" ref={rootRef}>
      <header className="a-top">
        <div>
          <Link className="store-back" href="/">
            SkillShift
          </Link>
          <div className="a-brand">Atelier A</div>
        </div>
        <nav className="a-nav">
          <button
            type="button"
            data-testid="store-a-nav-products"
            className={step === "products" ? "active" : ""}
            onClick={() => setStep("products")}
          >
            Products
          </button>
        </nav>
      </header>

      <main className="a-main" aria-busy={recorder.busy}>
        {step !== "products" && (
          <div className="a-steps">
            <span>Products</span>
            <span>→</span>
            <span className={step === "details" ? "on" : ""}>Add Product</span>
            <span>→</span>
            <span className={step === "media" ? "on" : ""}>Media</span>
            <span>→</span>
            <span className={step === "publish" ? "on" : ""}>Publish</span>
          </div>
        )}

        {step === "products" && (
          <section className="a-panel">
            <div className="a-panel-head">
              <div>
                <h1>{heading}</h1>
                <p className="lead">Live pieces from the atelier.</p>
              </div>
              <button
                type="button"
                className="a-btn primary"
                data-testid="store-a-add-product"
                onClick={() =>
                  void recorder.record("click", "Add Product", null, () => setStep("details"))
                }
              >
                Add Product
              </button>
            </div>
            {products.length === 0 ? (
              <div className="a-empty">Nothing published yet.</div>
            ) : (
              <div className="a-grid">
                {products.map((product, index) => (
                  <article
                    key={`${product.name}-${index}`}
                    className="a-card"
                    data-testid="store-a-product-card"
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
          </section>
        )}

        {step === "details" && (
          <section className="a-panel">
            <h2>{heading}</h2>
            <p className="lead">Name and price, or pick from the catalog.</p>
            <CatalogPicker tone="a" selected={draft} onPick={(item) => void pickCatalog(item)} />
            <label className="field">
              Product name
              <input
                data-testid="store-a-field-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                onFocus={() => void recorder.onFieldFocus("Product name", name)}
                onBlur={() => void recorder.onFieldBlur("Product name", name)}
                placeholder="Leather Bag"
              />
            </label>
            <label className="field">
              Price
              <input
                data-testid="store-a-field-price"
                value={price}
                onChange={(event) => setPrice(event.target.value)}
                onFocus={() => void recorder.onFieldFocus("Price", price)}
                onBlur={() => void recorder.onFieldBlur("Price", price)}
                placeholder="89"
              />
            </label>
            <div className="a-actions">
              <button type="button" className="a-btn" onClick={() => setStep("products")}>
                Back
              </button>
              <button
                type="button"
                className="a-btn primary"
                disabled={!canContinueDetails}
                onClick={() =>
                  void recorder.record("click", "Continue to Media", null, () => setStep("media"))
                }
              >
                Continue to Media
              </button>
            </div>
          </section>
        )}

        {step === "media" && (
          <section className="a-panel">
            <h2>{heading}</h2>
            <p className="lead">Attach a photo, or reuse one from the catalog.</p>
            <CatalogPicker
              tone="a"
              selected={draft}
              onPick={(item) => void pickCatalog(item, true)}
            />
            <label className="field">
              Product image
              <input
                type="file"
                accept="image/*"
                data-testid="store-a-field-image"
                onChange={(event) => onImageFile(event.target.files?.[0])}
              />
            </label>
            {image && (
              <div className="a-preview">
                <img src={image} alt="Product preview" />
              </div>
            )}
            <div className="a-actions">
              <button type="button" className="a-btn" onClick={() => setStep("details")}>
                Back
              </button>
              <button
                type="button"
                className="a-btn primary"
                disabled={!canContinueMedia}
                onClick={() =>
                  void recorder.record("click", "Continue to Publish", null, () =>
                    setStep("publish"),
                  )
                }
              >
                Continue to Publish
              </button>
            </div>
          </section>
        )}

        {step === "publish" && (
          <section className="a-panel">
            <h2>{heading}</h2>
            <p className="lead">A last look before it goes live.</p>
            <div className="a-preview">
              {image && <img src={image} alt={name} />}
              <div>
                <h3>{name}</h3>
                <p>{formatPrice(price)}</p>
              </div>
            </div>
            <div className="a-actions">
              <button type="button" className="a-btn" onClick={() => setStep("media")}>
                Back
              </button>
              <button
                type="button"
                className="a-btn primary"
                data-testid="store-a-publish"
                disabled={!canPublish}
                onClick={() => void recorder.record("click", "Publish", null, publish)}
              >
                Publish
              </button>
            </div>
          </section>
        )}
      </main>

      <RecorderBar
        recording={recorder.recording}
        count={recorder.events.length}
        busy={recorder.busy}
        status={recorder.status}
        onToggle={() => recorder.setRecording((on) => !on)}
        onDownload={recorder.download}
        onSave={() => void recorder.save()}
      />
    </div>
  );
}
