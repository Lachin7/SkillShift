import { spawn } from "child_process";
import { existsSync } from "fs";
import { NextResponse } from "next/server";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 180;

function repoRoot(): string {
  const cwd = process.cwd();
  const parent = path.resolve(cwd, "..");
  if (existsSync(path.join(parent, "agent", "run_transfer.py"))) return parent;
  return cwd;
}

function pythonBin(root: string): string {
  const venv = path.join(root, ".venv", "bin", "python");
  if (existsSync(venv)) return venv;
  return process.platform === "win32" ? "python" : "python3";
}

function siteOrigin(request: Request): string {
  const origin = request.headers.get("origin");
  if (origin) return origin.replace(/\/$/, "");
  const host = request.headers.get("x-forwarded-host") || request.headers.get("host");
  const proto = request.headers.get("x-forwarded-proto") || "http";
  return host ? `${proto}://${host}` : "http://localhost:3010";
}

export async function POST(request: Request) {
  const root = repoRoot();
  const python = pythonBin(root);
  const origin = siteOrigin(request);

  const result = await new Promise<{
    ok: boolean;
    code: number;
    log: string;
    error?: string;
  }>((resolve) => {
    const child = spawn(python, ["-m", "agent.run_transfer"], {
      cwd: root,
      env: {
        ...process.env,
        SKILLSHIFT_WEB_URL: origin,
        SKILLSHIFT_HEADED: "1",
        // Prefer real keys from the environment; otherwise use constrained mock.
        ...(process.env.GEMINI_API_KEY ||
        process.env.GOOGLE_API_KEY ||
        process.env.OPENAI_API_KEY ||
        process.env.ANTHROPIC_API_KEY ||
        process.env.GROQ_API_KEY
          ? {}
          : { SKILLSHIFT_MOCK_LLM: "1" }),
      },
    });

    let log = "";
    child.stdout.on("data", (chunk: Buffer) => {
      log += chunk.toString();
    });
    child.stderr.on("data", (chunk: Buffer) => {
      log += chunk.toString();
    });
    child.on("error", (error) => {
      resolve({
        ok: false,
        code: 1,
        log,
        error: error.message,
      });
    });
    child.on("close", (code) => {
      const exit = code ?? 1;
      resolve({
        ok: exit === 0,
        code: exit,
        log,
        error: exit === 0 ? undefined : log.trim().split("\n").slice(-6).join("\n") || `exit ${exit}`,
      });
    });
  });

  return NextResponse.json(result, { status: result.ok ? 200 : 500 });
}
