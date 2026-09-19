"use client";

import type { TraceAction, TraceEvent } from "@/lib/trace";
import { downloadTrace } from "@/lib/trace";
import { type RefObject, useCallback, useRef, useState } from "react";
import { flushSync } from "react-dom";

async function afterPaint() {
  await new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  });
  await new Promise((resolve) => window.setTimeout(resolve, 60));
}

async function captureNode(node: HTMLElement | null): Promise<string> {
  if (!node) return "";
  const html2canvas = (await import("html2canvas")).default;
  const canvas = await html2canvas(node, {
    backgroundColor: "#f4ebe0",
    scale: 0.55,
    logging: false,
    useCORS: true,
    ignoreElements: (element) => element.hasAttribute("data-html2canvas-ignore"),
  });
  return canvas.toDataURL("image/png");
}

export function useStoreARecorder(rootRef: RefObject<HTMLElement | null>) {
  const [recording, setRecording] = useState(true);
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("");
  const chain = useRef(Promise.resolve());
  const committed = useRef<Record<string, string>>({});
  const focusBefore = useRef<Record<string, string>>({});
  const focusValue = useRef<Record<string, string>>({});
  const recordingRef = useRef(recording);
  recordingRef.current = recording;

  const push = useCallback((event: TraceEvent) => {
    setEvents((current) => [...current, event]);
  }, []);

  const record = useCallback(
    (action: TraceAction, target: string, value: string | null, perform: () => void) => {
      const run = async () => {
        if (!recordingRef.current) {
          perform();
          return;
        }
        setBusy(true);
        setStatus("");
        try {
          const before = await captureNode(rootRef.current);
          flushSync(perform);
          await afterPaint();
          const after = await captureNode(rootRef.current);
          push({ before, action, target, value, after });
        } catch (error) {
          perform();
          console.warn("Store A recorder missed an event", error);
        } finally {
          setBusy(false);
        }
      };
      const next = chain.current.then(run, run);
      chain.current = next;
      return next;
    },
    [push, rootRef],
  );

  const onFieldFocus = useCallback(
    async (target: string, value: string) => {
      if (!recordingRef.current) return;
      focusValue.current[target] = value;
      focusBefore.current[target] = await captureNode(rootRef.current);
    },
    [rootRef],
  );

  const onFieldBlur = useCallback(
    async (target: string, value: string) => {
      if (!recordingRef.current) return;
      const trimmed = value.trim();
      if (!trimmed || trimmed === (committed.current[target] ?? focusValue.current[target] ?? "")) {
        return;
      }
      setBusy(true);
      try {
        const before = focusBefore.current[target] || (await captureNode(rootRef.current));
        await afterPaint();
        const after = await captureNode(rootRef.current);
        committed.current[target] = trimmed;
        push({ before, action: "fill", target, value: trimmed, after });
      } finally {
        setBusy(false);
      }
    },
    [push, rootRef],
  );

  const markCommitted = useCallback((target: string, value: string) => {
    committed.current[target] = value;
  }, []);

  const download = useCallback(() => {
    if (events.length === 0) {
      setStatus("Nothing recorded yet.");
      return;
    }
    downloadTrace(events, "trace.store-a.json");
    setStatus("Downloaded trace JSON.");
  }, [events]);

  const save = useCallback(async () => {
    if (events.length === 0) {
      setStatus("Nothing recorded yet.");
      return;
    }
    setBusy(true);
    setStatus("Saving…");
    try {
      const written: TraceEvent[] = [];
      let frame = 1;
      let lastAfter: string | null = null;

      async function uploadFrame(dataUrl: string): Promise<string> {
        const index = frame;
        frame += 1;
        const response = await fetch("/api/trace", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kind: "frame", index, dataUrl }),
        });
        if (!response.ok) {
          throw new Error(await response.text());
        }
        const payload = (await response.json()) as { path: string };
        return payload.path;
      }

      for (const event of events) {
        const before = lastAfter ?? (await uploadFrame(event.before));
        const after = await uploadFrame(event.after);
        written.push({
          before,
          action: event.action,
          target: event.target,
          value: event.value,
          after,
        });
        lastAfter = after;
      }

      const response = await fetch("/api/trace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "commit", events: written }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as { events: TraceEvent[]; path: string };
      downloadTrace(payload.events, "trace.store-a.json");
      setStatus(`Saved ${payload.path}`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }, [events]);

  return {
    recording,
    setRecording,
    events,
    busy,
    status,
    record,
    onFieldFocus,
    onFieldBlur,
    markCommitted,
    download,
    save,
  };
}
