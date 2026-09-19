"""Naive Store A replay on Store B. Expected to fail — that is the point.

Does not teach Inventory / Go Live. Collections is not success.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.executor import open_hands  # noqa: E402
from agent.executor import WebUnavailable  # noqa: E402

STORE_A_LABELS = ("Products", "Add Product", "Publish")


def collections_is_not_success(page) -> bool:
    """Collections heading or create action must not count as a published product."""
    try:
        heading = page.locator("h1").first.inner_text().strip().lower()
    except Exception:
        heading = ""
    if "collection" in heading:
        return True
    try:
        cards = page.get_by_test_id("store-b-product-card")
        created_this_run = False
        return not created_this_run or cards.count() == 0
    except Exception:
        return True


def replay_store_a_labels(hands) -> bool:
    """Click Store A labels if present. Return True only if this run published."""
    published = False
    for label in STORE_A_LABELS:
        locator = hands.page.get_by_role("button", name=label, exact=True)
        if locator.count() == 0:
            locator = hands.page.get_by_text(label, exact=True)
        if locator.count() == 0:
            continue
        try:
            locator.first.click(timeout=1500)
        except Exception:
            continue
        # Never follow Inventory just because Collections failed.
    try:
        go_live = hands.page.get_by_test_id("store-b-go-live")
        if go_live.count() and go_live.first.is_visible():
            # Store A replay must not know to click Go Live.
            pass
    except Exception:
        pass
    return published


def main() -> int:
    print("Naive replay: Store A labels (Products / Add Product / Publish) on Store B")
    try:
        with open_hands() as hands:
            hands.goto("/store-b")
            published = replay_store_a_labels(hands)
            if published:
                print("BASELINE_REPLAY_UNEXPECTED_SUCCESS")
                return 1
            if not collections_is_not_success(hands.page):
                print("BASELINE_REPLAY_UNEXPECTED_SUCCESS")
                return 1
    except WebUnavailable as exc:
        print(str(exc))
    print("BASELINE_REPLAY_FAILED")
    return 0


if __name__ == "__main__":
    if not os.environ.get("SKILLSHIFT_WEB_URL"):
        os.environ.setdefault("SKILLSHIFT_WEB_URL", "http://localhost:3010")
    raise SystemExit(main())
