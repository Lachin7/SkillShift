"""Publish Blue Sneaker £120 on Store B via the recovered adapter.

Hands only — no LLM, no Collections, no verifier.

Prerequisites:
  - Next.js already running (this script will not start it)
  - SKILLSHIFT_WEB_URL=http://localhost:3010  (override if needed)
  - playwright install chromium

Usage (from repo root):
  python -m agent.run_store_b
  python agent/run_store_b.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.executor import (  # noqa: E402
    execute_recovered_adapter,
    open_hands,
)


def main() -> int:
    with open_hands() as hands:
        card = execute_recovered_adapter(hands)
        print("Published Blue Sneaker £120 on Store B via Inventory → Create Listing → Go Live.")
        print("store-b-product-card:")
        print(card)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
