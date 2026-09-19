import { padFrame, type TraceAction, type TraceEvent } from "@/lib/trace";
import { mkdir, writeFile } from "fs/promises";
import { NextResponse } from "next/server";
import path from "path";

export const runtime = "nodejs";

const ACTIONS = new Set<TraceAction>(["click", "fill", "upload"]);

function repoRoot(): string {
  return path.resolve(process.cwd(), "..");
}

function decodePng(dataUrl: string): Buffer {
  const marker = "base64,";
  const index = dataUrl.indexOf(marker);
  if (index === -1) {
    throw new Error("Screenshot must be a PNG data URL.");
  }
  return Buffer.from(dataUrl.slice(index + marker.length), "base64");
}

type FrameBody = {
  kind: "frame";
  index: number;
  dataUrl: string;
};

type CommitBody = {
  kind: "commit";
  events: TraceEvent[];
};

export async function POST(request: Request) {
  const body = (await request.json()) as FrameBody | CommitBody;
  const root = repoRoot();
  const framesDir = path.join(root, "fixtures", "traces", "frames");
  await mkdir(framesDir, { recursive: true });

  if (body.kind === "frame") {
    const rel = `fixtures/traces/frames/frame_${padFrame(body.index)}.png`;
    await writeFile(path.join(root, rel), decodePng(body.dataUrl));
    return NextResponse.json({ path: rel });
  }

  if (body.kind !== "commit" || !Array.isArray(body.events) || body.events.length === 0) {
    return NextResponse.json({ error: "Expected a list of TraceEvent." }, { status: 400 });
  }

  for (const event of body.events) {
    if (!ACTIONS.has(event.action) || !event.target) {
      return NextResponse.json({ error: "Invalid TraceEvent." }, { status: 400 });
    }
  }

  const jsonPath = "fixtures/traces/store-a.json";
  await writeFile(
    path.join(root, jsonPath),
    `${JSON.stringify(body.events, null, 2)}\n`,
    "utf8",
  );

  return NextResponse.json({ path: jsonPath, events: body.events });
}
