"""Wave 2: recovered Store B adapter via Playwright hands. No LLM."""

from __future__ import annotations

from agent.executor import (
    FORBIDDEN_TESTIDS,
    PRODUCT_NAME,
    BrowserHands,
    execute_recovered_adapter,
    load_recovered_adapter,
    open_hands,
    reject_collections_mapping,
    require_web,
)

COLLECTIONS = "store-b-nav-collections"


def test_require_web_is_reachable():
    url = require_web()
    assert url.startswith("http")


def test_recovered_adapter_is_inventory_not_collections():
    adapter = load_recovered_adapter()
    reject_collections_mapping(adapter)
    create = adapter["mappings"][0]
    assert "Inventory" in create["app_action"]
    assert "Collections" not in create["app_action"]


def test_click_guard_blocks_collections():
    class FakeLocator:
        def click(self) -> None:
            raise AssertionError("Playwright click must not run for Collections")

    class FakePage:
        def get_by_test_id(self, testid: str) -> FakeLocator:
            return FakeLocator()

    hands = BrowserHands(FakePage(), "http://localhost:3010")  # type: ignore[arg-type]
    try:
        hands.click(COLLECTIONS)
        raise AssertionError("Collections click should have been refused")
    except RuntimeError as exc:
        assert "must not click" in str(exc)
    assert COLLECTIONS not in hands.clicked


def test_publish_blue_sneaker_on_store_b():
    with open_hands() as hands:
        card = execute_recovered_adapter(hands)
        assert PRODUCT_NAME in card
        assert "£120" in card
        assert hands.page.get_by_test_id("store-b-product-card").is_visible()
        assert COLLECTIONS not in hands.clicked
        assert "store-b-collections-create" not in hands.clicked
        assert FORBIDDEN_TESTIDS.isdisjoint(hands.clicked)
        assert "store-b-nav-inventory" in hands.clicked
        assert "store-b-create-listing" in hands.clicked
        assert "store-b-go-live" in hands.clicked
        visible = {item["testid"] for item in hands.visible_elements()}
        assert "store-b-product-card" in visible
        shot = hands.screenshot()
        assert shot[:8] == b"\x89PNG\r\n\x1a\n"
