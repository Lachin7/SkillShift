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
      <div className="recorder-brand">SkillShift · teaching</div>
      <div className="recorder-row">
        <button
          type="button"
          className={`recorder-toggle${recording ? " on" : ""}`}
          onClick={onToggle}
          aria-pressed={recording}
        >
          <span className="recorder-dot" />
          {recording ? "Rec" : "Start"}
        </button>
        <span className="recorder-count">
          {count} {count === 1 ? "event" : "events"}
          {busy ? " · capturing" : ""}
        </span>
        <button type="button" onClick={onDownload} disabled={count === 0}>
          Download
        </button>
        <button type="button" onClick={onSave} disabled={count === 0 || busy}>
          Save
        </button>
      </div>
      {status ? <span className="recorder-status">{status}</span> : null}
    </div>
  );
}
