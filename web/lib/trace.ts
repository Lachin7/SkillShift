export type TraceAction = "click" | "fill" | "upload";

export type TraceEvent = {
  before: string;
  action: TraceAction;
  target: string;
  value: string | null;
  after: string;
};

export function downloadTrace(events: TraceEvent[], filename: string) {
  const blob = new Blob([JSON.stringify(events, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function padFrame(index: number): string {
  return String(index).padStart(2, "0");
}
