import { repoFile } from "@/lib/repo-paths";
import { mkdir, readFile, writeFile } from "fs/promises";
import path from "path";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export type PerturbationFlags = {
  rename_publish: boolean;
  extra_required: boolean;
  reorder_nav: boolean;
};

const DEFAULTS: PerturbationFlags = {
  rename_publish: false,
  extra_required: false,
  reorder_nav: false,
};

const HEADERS = { "Cache-Control": "no-store, max-age=0" };

function asBool(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function normalize(value: unknown): PerturbationFlags {
  const record = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return {
    rename_publish: asBool(record.rename_publish, DEFAULTS.rename_publish),
    extra_required: asBool(record.extra_required, DEFAULTS.extra_required),
    reorder_nav: asBool(record.reorder_nav, DEFAULTS.reorder_nav),
  };
}

async function readFlags(): Promise<PerturbationFlags> {
  for (const file of repoFile("fixtures", "live", "perturbations.json")) {
    try {
      return normalize(JSON.parse(await readFile(file, "utf8")));
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") continue;
    }
  }
  return { ...DEFAULTS };
}

async function writeFlags(next: PerturbationFlags): Promise<PerturbationFlags> {
  for (const file of repoFile("fixtures", "live", "perturbations.json")) {
    try {
      await mkdir(path.dirname(file), { recursive: true });
      await writeFile(file, `${JSON.stringify(next, null, 2)}\n`, "utf8");
      return next;
    } catch {
      continue;
    }
  }
  throw new Error("Could not persist perturbations.json");
}

export async function GET() {
  return NextResponse.json(await readFlags(), { headers: HEADERS });
}

export async function POST(request: Request) {
  const incoming = normalize(await request.json().catch(() => ({})));
  const current = await readFlags();
  const merged = { ...current, ...incoming };
  const saved = await writeFlags(merged);
  return NextResponse.json(saved, { headers: HEADERS });
}
