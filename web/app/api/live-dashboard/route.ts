import type { DashboardState, LiveDashboardPayload } from "@/lib/types";
import { readFile } from "fs/promises";
import { NextResponse } from "next/server";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const revalidate = 0;

function liveFileCandidates(): string[] {
  const cwd = process.cwd();
  return [
    path.resolve(cwd, "..", "fixtures", "live", "dashboard-state.json"),
    path.resolve(cwd, "fixtures", "live", "dashboard-state.json"),
  ];
}

function isDashboardState(value: unknown): value is DashboardState {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  const skill = record.skill as Record<string, unknown> | undefined;
  const app = record.app as Record<string, unknown> | undefined;
  const adapter = record.adapter as Record<string, unknown> | undefined;
  const status = record.status as Record<string, unknown> | undefined;
  return (
    typeof record.phase === "string" &&
    Array.isArray(skill?.steps) &&
    typeof app?.app_id === "string" &&
    Array.isArray(adapter?.mappings) &&
    typeof status?.message === "string"
  );
}

function payload(body: LiveDashboardPayload, status = 200) {
  return NextResponse.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store, max-age=0",
    },
  });
}

async function readLiveState(): Promise<DashboardState | null> {
  for (const file of liveFileCandidates()) {
    try {
      const raw = await readFile(file, "utf8");
      const parsed: unknown = JSON.parse(raw);
      if (isDashboardState(parsed)) return parsed;
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") continue;
      return null;
    }
  }
  return null;
}

export async function GET() {
  const state = await readLiveState();
  if (!state) {
    return payload({ source: "fixture", state: null });
  }
  return payload({ source: "live", state });
}
