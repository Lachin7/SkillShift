import type { Product } from "@/lib/types";
import { repoFile } from "@/lib/repo-paths";
import { readFile } from "fs/promises";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

const APP_FILES: Record<string, string> = {
  "store-a": "store-a-products.json",
  "store-b": "store-b-products.json",
  "store-c": "store-c-products.json",
  "store-d": "store-d-products.json",
};

function isProduct(value: unknown): value is Product {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.price === "string" &&
    typeof record.image === "string"
  );
}

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

export async function GET(request: Request) {
  const app = new URL(request.url).searchParams.get("app") || "store-b";
  const products = await readProducts(app);
  return NextResponse.json(
    { products },
    { headers: { "Cache-Control": "no-store, max-age=0" } },
  );
}
