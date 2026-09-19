"use client";

import type { DashboardPhase, DashboardState, LiveDashboardPayload } from "@/lib/types";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import cached from "../../public/dashboard-state.cached.json";
import mismatch from "../../public/dashboard-state.mismatch.json";
import recovered from "../../public/dashboard-state.json";

const FIXTURES: Record<DashboardPhase, DashboardState> = {
  mismatch: mismatch as DashboardState,
  recovered: recovered as DashboardState,
  cached: cached as DashboardState,
};

const PHASES: DashboardPhase[] = ["mismatch", "recovered", "cached"];
const FROZEN_SKILL = recovered.skill;
const POLL_MS = 800;

type Mode = "live" | "preview";

type TeachEvent = {
  action: string;
  target: string;
  value: string | null;
};

export default function DashboardPage() {
  const [mode, setMode] = useState<Mode>("live");
  const [previewPhase, setPreviewPhase] = useState<DashboardPhase>("mismatch");
  const [live, setLive] = useState<DashboardState | null>(null);
  const [liveAvailable, setLiveAvailable] = useState(false);
  const [running, setRunning] = useState(false);
  const [runLog, setRunLog] = useState("");
  const [runError, setRunError] = useState("");
  const [trace, setTrace] = useState<TeachEvent[] | null>(null);

  const poll = useCallback(async () => {
    try {
      const response = await fetch("/api/live-dashboard", { cache: "no-store" });
      const data = (await response.json()) as LiveDashboardPayload;
      if (data.source === "live" && data.state) {
        setLiveAvailable(true);
        setLive(data.state);
        return;
      }
    } catch {
      // 3A is optional. Fixture preview still works.
    }
    setLiveAvailable(false);
    setLive(null);
  }, []);

  const loadTrace = useCallback(async () => {
    try {
      const response = await fetch("/api/teach-trace", { cache: "no-store" });
      const data = (await response.json()) as { events: TeachEvent[] | null };
      setTrace(data.events);
    } catch {
      setTrace(null);
    }
  }, []);

  useEffect(() => {
    void poll();
    void loadTrace();
    const timer = window.setInterval(() => {
      void poll();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [loadTrace, poll]);

  async function runTransfer() {
    setRunning(true);
    setRunError("");
    setRunLog("");
    try {
      const response = await fetch("/api/run-transfer", { method: "POST" });
      const data = (await response.json()) as {
        ok?: boolean;
        log?: string;
        error?: string;
      };
      setRunLog(data.log || "");
      if (!response.ok || data.ok === false) {
        setRunError(data.error || "Transfer failed.");
      }
      void poll();
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Transfer failed.");
    } finally {
      setRunning(false);
    }
  }

  const showingLive = mode === "live" && live !== null;
  const raw = showingLive ? live : FIXTURES[previewPhase];
  const state: DashboardState = { ...raw, skill: FROZEN_SKILL };
  const sourceLabel = showingLive ? "live" : "fixture";

  return (
    <main className="dash" data-source={sourceLabel} data-phase={state.phase}>
      <div className="dash-top">
        <div>
          <Link className="store-back" href="/">
            ← SkillShift
          </Link>
          <h1>Adapter dashboard</h1>
          <p className="dash-claim">
            Skill = WHAT. Adapter = HOW HERE. The skill card never changes.
          </p>
        </div>
        <div className="dash-controls">
          <div className="live-ctrl">
            <button
              type="button"
              className="run-transfer-btn"
              disabled={running}
              onClick={() => void runTransfer()}
            >
              {running ? "Running…" : "Run transfer"}
            </button>
            <button
              type="button"
              className={`live-btn ${mode === "live" ? "on" : ""} ${liveAvailable ? "hot" : ""}`}
              onClick={() => setMode("live")}
            >
              <span className={`live-dot ${liveAvailable ? "pulse" : ""}`} />
              Live
            </button>
            <span className="live-hint">
              {running
                ? "headed Store B — one window"
                : liveAvailable
                  ? "live"
                  : "waiting for a run"}
            </span>
          </div>
          {runError ? <p className="run-error">{runError}</p> : null}
          {runLog ? <pre className="run-log">{runLog.trim().split("\n").slice(-8).join("\n")}</pre> : null}
          <details className="dash-dev">
            <summary>Replay slides</summary>
            <p className="preview-label">Dev fallback if a live run is not available.</p>
            <div className="phase-ctrl" aria-label="Replay slides">
              {PHASES.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={mode === "preview" && previewPhase === item ? "on" : ""}
                  onClick={() => {
                    setPreviewPhase(item);
                    setMode("preview");
                  }}
                >
                  {item}
                </button>
              ))}
            </div>
            <button type="button" className="refresh-btn" onClick={() => void poll()}>
              Refresh live
            </button>
          </details>
        </div>
      </div>

      <section className="cards">
        <article className="card skill-card">
          <h2>Learned Skill</h2>
          <h3>{state.skill.title}</h3>
          <p className="sub">{state.skill.name}</p>
          <ol className="steps">
            {state.skill.steps.map((step, index) => (
              <li key={step}>
                {index + 1} {step}
              </li>
            ))}
          </ol>
          <p className="frozen-note">Frozen after learning</p>
        </article>

        <article className="card">
          <h2>Current App</h2>
          <h3>{state.app.label}</h3>
          <p className="sub">{state.app.app_id}</p>
          {state.app.unseen ? (
            <span className="badge">Unseen environment</span>
          ) : (
            <span className="badge recognised">Recognised environment</span>
          )}
          {state.app.app_id === "store-a" ? (
            <p className="frozen-note">Environment Store A / Adapter cached</p>
          ) : null}
        </article>

        <article className="card adapter-card">
          <h2>Adapter</h2>
          <p className="sub">{state.adapter.skill_name}</p>
          {state.adapter.mappings.map((mapping) => (
            <div
              key={mapping.semantic_intent}
              className={`mapping${mapping.highlight === "error" ? " error" : ""}`}
            >
              <div className="label">{mapping.label}</div>
              <div className="action">→ {mapping.app_action}</div>
              <div className="intent">{mapping.semantic_intent}</div>
            </div>
          ))}
        </article>

        <article className="card">
          <h2>Status</h2>
          <div className="flags">
            <div className={`flag ${state.status.skill_loaded ? "on" : "off"}`}>
              <span>Skill loaded</span>
              <span>{state.status.skill_loaded ? "yes" : "no"}</span>
            </div>
            <div className={`flag ${state.status.adapter_learned ? "on" : "off"}`}>
              <span>Adapter learned</span>
              <span>{state.status.adapter_learned ? "yes" : "no"}</span>
            </div>
            <div className={`flag ${state.status.product_live ? "on" : "off"}`}>
              <span>Product live</span>
              <span>{state.status.product_live ? "yes" : "no"}</span>
            </div>
          </div>
          <div
            className={`status-msg ${
              state.phase === "mismatch" ? "bad" : state.phase === "cached" ? "cached" : "good"
            }`}
          >
            {state.status.message}
          </div>
          {typeof (state.status as unknown as { modal?: string }).modal === "string" ? (
            <p className="frozen-note">{(state.status as unknown as { modal: string }).modal}</p>
          ) : null}
          {state.metrics?.reuse_gain ? (
            <p className="frozen-note">
              reuse {state.metrics.first?.actions ?? "—"}→{state.metrics.second?.actions ?? "—"} actions
              {" · "}
              {state.metrics.first?.model_calls ?? "—"}→{state.metrics.second?.model_calls ?? "—"} models
              {" · "}
              recoveries {state.metrics.second?.recoveries ?? state.status.recoveries ?? 0}
            </p>
          ) : null}
        </article>
      </section>

      {state.loop_trace && state.loop_trace.length > 0 ? (
        <section className="loop-trace">
          <h2>Transfer loop</h2>
          <ol>
            {state.loop_trace.map((item, index) => (
              <li key={`${item.semantic_step}-${index}`} data-verification={item.verification}>
                <span className="loop-step">{item.semantic_step}</span>
                {item.control ? <span className="loop-control">→ {item.control}</span> : null}
                <span className={`loop-verify ${item.verification === "passed" ? "ok" : "bad"}`}>
                  {item.verification}
                  {item.failure_class && item.failure_class !== "none"
                    ? ` · ${item.failure_class}`
                    : ""}
                </span>
                {item.patch ? <span className="loop-patch">patch {item.patch}</span> : null}
                {typeof item.mapping_count === "number" ? (
                  <span className="loop-maps">maps {item.mapping_count}</span>
                ) : null}
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <section className="teach-trace">
        <h2>Store A demonstration</h2>
        {trace && trace.length > 0 ? (
          <ol>
            {trace.map((event, index) => (
              <li key={`${event.action}-${event.target}-${index}`}>
                <span className="teach-action">{event.action}</span>
                <span className="teach-target">{event.target}</span>
                {event.value ? <span className="teach-value">{event.value}</span> : null}
              </li>
            ))}
          </ol>
        ) : (
          <p>No demonstration saved — teach in Store A.</p>
        )}
      </section>
    </main>
  );
}
