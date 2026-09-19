"""Modal app: score campaign recovery hypotheses in parallel.

Does NOT host Next.js. Does NOT Playwright against localhost.
Scores a JSON snapshot only.

Run (from repo root, after `modal setup`):

    modal run modal_app/recovery_runner.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import modal

_APP_DIR = Path(__file__).resolve().parent
_REPO = _APP_DIR.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from modal_app.scoring import (  # noqa: E402
    HYPOTHESIS_DECOY,
    HYPOTHESIS_SHIPPING,
    SHIPPING_SNAPSHOT,
    build_report,
    pick_winner,
    status_line,
)

image = modal.Image.debian_slim(python_version="3.12").add_local_python_source("modal_app")

app = modal.App("skillshift-campaign-recovery", image=image)


@app.function()
def score_candidate_remote(payload: dict) -> dict:
    """Remote scorer. Snapshot in, verdict out. No browser."""
    from modal_app.scoring import score_candidate as _score

    return _score(payload["snapshot"], payload["candidate"])


def score_payloads(snapshot: dict, hypotheses: list[dict] | None = None) -> list[dict]:
    items = hypotheses or [HYPOTHESIS_SHIPPING, HYPOTHESIS_DECOY]
    payloads = [{"snapshot": snapshot, "candidate": item} for item in items]
    return list(score_candidate_remote.map(payloads))


@app.local_entrypoint()
def main() -> None:
    print("SkillShift Modal recovery — snapshot scoring only (no localhost).")
    results = score_payloads(SHIPPING_SNAPSHOT, [HYPOTHESIS_SHIPPING, HYPOTHESIS_DECOY])
    winner = pick_winner(results)
    report = build_report("modal", results)
    print(json.dumps(report, indent=2))
    print(f"winner={winner}")
    print(status_line(report))
    for item in results:
        mark = "✅" if item["ok"] else "❌"
        print(f"  {item['id']} {item['action']}  {mark}")
