import type { Product } from "@/lib/types";
import { repoFile } from "@/lib/repo-paths";
import { readFile } from "fs/promises";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

function isProduct(value: unknown): value is Product {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.price === "string" &&
    typeof record.image === "string"
  );
}

const APP_FILES: Record<string, string> = {
  "store-b": "store-b-products.json",
  "store-c": "store-c-products.json",
  "store-d": "store-d-products.json",
};

async function readProducts(app: string): Promise<Product[]> {
  const fileName = APP_FILES[app] || APP_FILES["store-b"];
  for (const file of repoFile("fixtures", "live", fileName)) {
    try {
      const parsed: unknown = JSON.parse(await readFile(file, "utf8"));
      if (Array.isArray(parsed)) return parsed.filter(isProduct);
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") continue;
    }
  }
  return [];
}

function barePrice(price: string): string {
  return price.trim().replace(/^£/, "");
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const wanted = (url.searchParams.get("title") || url.searchParams.get("name") || "").trim();
  const app = url.searchParams.get("app") || "store-b";
  const products = await readProducts(app);
  const match = wanted
    ? products.find((item) => item.name.toLowerCase() === wanted.toLowerCase())
    : products[products.length - 1];

  if (!match) {
    return NextResponse.json(
      {
        product_exists: false,
        title: wanted,
        price: "",
        status: "none",
        purchasable: false,
      },
      { headers: { "Cache-Control": "no-store, max-age=0" } },
    );
  }

  return NextResponse.json(
    {
      product_exists: true,
      title: match.name,
      price: barePrice(match.price),
      status: "published",
      purchasable: true,
    },
    { headers: { "Cache-Control": "no-store, max-age=0" } },
  );
}
