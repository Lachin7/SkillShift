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

export default function DashboardPage() {
  const [mode, setMode] = useState<Mode>("live");
  const [previewPhase, setPreviewPhase] = useState<DashboardPhase>("mismatch");
  const [live, setLive] = useState<DashboardState | null>(null);
  const [liveAvailable, setLiveAvailable] = useState(false);

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

  useEffect(() => {
    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [poll]);

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
              className={`live-btn ${mode === "live" ? "on" : ""} ${liveAvailable ? "hot" : ""}`}
              onClick={() => setMode("live")}
            >
              <span className={`live-dot ${liveAvailable ? "pulse" : ""}`} />
              Live
            </button>
            <button type="button" className="refresh-btn" onClick={() => void poll()}>
              Refresh
            </button>
            <span className="live-hint">
              {liveAvailable
                ? "fixtures/live/dashboard-state.json"
                : "waiting for 3A — using fixture preview"}
            </span>
          </div>
          <div className="preview-block">
            <span className="preview-label">fixture preview</span>
            <div className="phase-ctrl" aria-label="Fixture preview">
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
          </div>
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
        </article>
      </section>
    </main>
  );
}
