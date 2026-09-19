"""Publish Blue Sneaker £120 on Store B via direct hands (smoke / no LLM).

For the real Explore→Verify→Recover demo, use:
  SKILLSHIFT_MOCK_LLM=1 python -m agent.run_transfer
  # or with GEMINI_API_KEY set (no mock)

Prerequisites:
  - Next.js already running
  - playwright install chromium
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.executor import (  # noqa: E402
    BLUE_SNEAKER,
    LIVE_PRODUCTS_PATH,
    open_hands,
    persist_live_product,
)


def main() -> int:
    LIVE_PRODUCTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LIVE_PRODUCTS_PATH.write_text("[]\n", encoding="utf-8")
    with open_hands() as hands:
        hands.goto("/store-b")
        hands.click("store-b-nav-inventory")
        hands.click("store-b-create-listing")
        hands.type("store-b-field-name", BLUE_SNEAKER.name)
        hands.type("store-b-field-price", BLUE_SNEAKER.price)
        hands.upload("store-b-field-image", BLUE_SNEAKER.image)
        hands.select("store-b-field-shipping", "Standard")
        hands.click("store-b-go-live")
        card = hands.page.get_by_test_id("store-b-product-card").filter(
            has_text=BLUE_SNEAKER.name
        )
        text = card.inner_text()
        persist_live_product(BLUE_SNEAKER)
        print("Published Blue Sneaker £120 on Store B (hands smoke path).")
        print("store-b-product-card:")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
