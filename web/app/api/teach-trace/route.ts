import { repoFile } from "@/lib/repo-paths";
import { readFile } from "fs/promises";
import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

export type TeachEvent = {
  action: string;
  target: string;
  value: string | null;
};

async function readTrace(): Promise<TeachEvent[] | null> {
  for (const file of repoFile("fixtures", "traces", "store-a.json")) {
    try {
      const parsed: unknown = JSON.parse(await readFile(file, "utf8"));
      if (!Array.isArray(parsed)) continue;
      return parsed.flatMap((item) => {
        if (!item || typeof item !== "object") return [];
        const record = item as Record<string, unknown>;
        if (typeof record.action !== "string" || typeof record.target !== "string") {
          return [];
        }
        return [
          {
            action: record.action,
            target: record.target,
            value: typeof record.value === "string" ? record.value : null,
          },
        ];
      });
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") continue;
    }
  }
  return null;
}

export async function GET() {
  const events = await readTrace();
  return NextResponse.json(
    { events },
    { headers: { "Cache-Control": "no-store, max-age=0" } },
  );
}
