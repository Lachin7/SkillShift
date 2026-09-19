"""Playwright hands: execute CandidateAction, no Collections hard-block."""

from __future__ import annotations

from agent.executor import (
    PRODUCT_NAME,
    BrowserHands,
    execute_candidate,
    open_hands,
    require_web,
)
from agent.models import CandidateAction as CA


def test_require_web_is_reachable():
    url = require_web()
    assert url.startswith("http")


def test_collections_click_allowed_during_explore():
    """Decoy clicks are allowed; verifier catches wrong navigation."""
    class FakeLocator:
        def click(self) -> None:
            return None

        def is_enabled(self) -> bool:
            return True

        def fill(self, text: str) -> None:
            return None

    class FakePage:
        def get_by_test_id(self, testid: str) -> FakeLocator:
            return FakeLocator()

    hands = BrowserHands(FakePage(), "http://localhost:3010")  # type: ignore[arg-type]
    hands.click("store-b-nav-collections")
    assert "store-b-nav-collections" in hands.clicked


def test_execute_candidate_click():
    class FakeLocator:
        def click(self) -> None:
            self.clicked = True

        def is_enabled(self) -> bool:
            return True

    class FakePage:
        def __init__(self) -> None:
            self.loc = FakeLocator()

        def get_by_test_id(self, testid: str) -> FakeLocator:
            return self.loc

    hands = BrowserHands(FakePage(), "http://localhost:3010")  # type: ignore[arg-type]
    execute_candidate(
        hands,
        CA(
            target_testid="store-b-nav-inventory",
            action="click",
            rationale="test",
            confidence=0.8,
        ),
    )
    assert "store-b-nav-inventory" in hands.clicked


def test_publish_blue_sneaker_hands_path():
    """Smoke: direct Inventory path (hands only, no explorer)."""
    require_web()
    from agent.executor import BLUE_SNEAKER, LIVE_PRODUCTS_PATH, persist_live_product

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
            has_text=PRODUCT_NAME
        )
        assert card.is_visible()
        persist_live_product(BLUE_SNEAKER)
        assert "store-b-nav-inventory" in hands.clicked
        assert "store-b-go-live" in hands.clicked
        shot = hands.screenshot()
        assert shot[:8] == b"\x89PNG\r\n\x1a\n"
