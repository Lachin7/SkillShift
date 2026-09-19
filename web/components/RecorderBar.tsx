"use client";

type Props = {
  recording: boolean;
  count: number;
  busy: boolean;
  status: string;
  onToggle: () => void;
  onDownload: () => void;
  onSave: () => void;
};

export function RecorderBar({
  recording,
  count,
  busy,
  status,
  onToggle,
  onDownload,
  onSave,
}: Props) {
  return (
    <div className="recorder" data-html2canvas-ignore>
      <button
        type="button"
        className={`recorder-toggle${recording ? " on" : ""}`}
        onClick={onToggle}
      >
        <span className="recorder-dot" />
        {recording ? "Rec" : "Start"}
      </button>
      <span className="recorder-count">
        {count} {count === 1 ? "event" : "events"}
        {busy ? " · capturing" : ""}
      </span>
      <button type="button" onClick={onDownload} disabled={count === 0}>
        Download trace
      </button>
      <button type="button" onClick={onSave} disabled={count === 0 || busy}>
        Save trace
      </button>
      {status ? <span className="recorder-status">{status}</span> : null}
    </div>
  );
}
