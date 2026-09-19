"""Playwright hands for SkillShift.

Pydantic AI is the brain. This module executes a GIVEN adapter:
screenshot, visible_elements, click, type, upload.

Chromium: `playwright install chromium`
Web (already running): SKILLSHIFT_WEB_URL=http://localhost:3010
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from playwright.sync_api import expect, sync_playwright

from .adapter import intent_to_testids
from .models import EnvironmentAdapter, Skill

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://localhost:3010"
ADAPTER_PATH = REPO_ROOT / "adapters" / "store_b__publish_product.json"
BLUE_SNEAKER_IMAGE = REPO_ROOT / "web" / "public" / "products" / "blue-sneaker.svg"

# Recovered Store B HOW HERE. Wave 2 never uses the Collections trap.
FORBIDDEN_TESTIDS = frozenset(
    {
        "store-b-nav-collections",
        "store-b-collections-create",
    }
)

PRODUCT_NAME = "Blue Sneaker"
PRODUCT_PRICE = "120"
LEATHER_BAG_IMAGE = REPO_ROOT / "web" / "public" / "products" / "leather-bag.svg"


@dataclass(frozen=True)
class ProductSpec:
    name: str
    price: str
    image: Path


LEATHER_BAG = ProductSpec("Leather Bag", "89", LEATHER_BAG_IMAGE)
BLUE_SNEAKER = ProductSpec("Blue Sneaker", "120", BLUE_SNEAKER_IMAGE)


class WebUnavailable(RuntimeError):
    """Next.js is not reachable. This module does not start the frontend."""


class BrowserMissing(RuntimeError):
    """Playwright Chromium is not installed."""


class BrowserHands:
    """Primitive Playwright actions. Callers pass data-testid values from routes.md."""

    def __init__(self, page: Page, base_url: str, *, allow_collections: bool = False):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.clicked: list[str] = []
        self.allow_collections = allow_collections

    def goto(self, path: str = "/store-b") -> None:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.page.goto(url, wait_until="domcontentloaded")

    def screenshot(self, path: str | Path | None = None) -> bytes:
        data = self.page.screenshot(type="png")
        if path is not None:
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        return data

    def visible_elements(self) -> list[dict[str, str]]:
        """DOM/accessibility summary of nodes with data-testid. No OmniParser."""
        return self.page.evaluate(
            """() => {
              const nodes = [...document.querySelectorAll("[data-testid]")];
              return nodes.flatMap((el) => {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                const hidden =
                  style.display === "none" ||
                  style.visibility === "hidden" ||
                  style.opacity === "0" ||
                  rect.width === 0 ||
                  rect.height === 0;
                if (hidden) return [];
                const labelled = el.getAttribute("aria-labelledby");
                const labelledText = labelled
                  ? [...labelled.split(/\\s+/)]
                      .map((id) => document.getElementById(id)?.textContent?.trim() || "")
                      .filter(Boolean)
                      .join(" ")
                  : "";
                const name =
                  el.getAttribute("aria-label") ||
                  labelledText ||
                  (el.innerText || "").trim() ||
                  el.getAttribute("placeholder") ||
                  el.getAttribute("alt") ||
                  "";
                return [{
                  testid: el.getAttribute("data-testid") || "",
                  role: el.getAttribute("role") || el.tagName.toLowerCase(),
                  name,
                  text: name,
                }];
              });
            }"""
        )

    def click(self, testid: str, *, allow_collections: bool | None = None) -> None:
        allowed = self.allow_collections if allow_collections is None else allow_collections
        if not allowed:
            _forbid_collections(testid)
        self.clicked.append(testid)
        self.page.get_by_test_id(testid).click()

    def type(self, testid: str, text: str) -> None:
        if not self.allow_collections:
            _forbid_collections(testid)
        locator = self.page.get_by_test_id(testid)
        locator.fill(text)

    def upload(self, testid: str, image_path: str | Path) -> None:
        if not self.allow_collections:
            _forbid_collections(testid)
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        self.page.get_by_test_id(testid).set_input_files(str(path))


def _forbid_collections(testid: str) -> None:
    if testid in FORBIDDEN_TESTIDS:
        raise RuntimeError(
            f"Wave 2 recovered path must not click {testid}. "
            "Collections is the decoy; use Inventory → Create Listing."
        )


def require_web(base_url: str | None = None) -> str:
    """Fail clearly if Next.js is down. Does not start the frontend."""
    url = (base_url or os.environ.get("SKILLSHIFT_WEB_URL") or DEFAULT_BASE_URL).rstrip(
        "/"
    )
    probe = f"{url}/store-b"
    try:
        with urlopen(probe, timeout=3) as response:  # noqa: S310 — local demo URL
            status = getattr(response, "status", 200)
    except URLError as exc:
        raise WebUnavailable(
            f"SkillShift web is not running at {url} (tried {probe}). "
            "Start Next.js yourself, then re-run. "
            "Override with SKILLSHIFT_WEB_URL if the port is not 3010. "
            "This script will not start the frontend."
        ) from exc
    except OSError as exc:
        raise WebUnavailable(
            f"SkillShift web is not running at {url}: {exc}. "
            "Start Next.js yourself. This script will not start the frontend."
        ) from exc
    if status >= 400:
        raise WebUnavailable(
            f"SkillShift web at {probe} returned HTTP {status}. "
            "Start Next.js yourself. This script will not start the frontend."
        )
    return url


def reject_collections_mapping(adapter: dict[str, Any]) -> None:
    create = next(
        mapping
        for mapping in adapter["mappings"]
        if mapping["semantic_intent"] == "start creating a new sellable item"
    )
    action = create["app_action"].lower()
    if "collection" in action:
        raise RuntimeError(
            "Refusing to execute a Collections mapping. "
            "Wave 2 runs the recovered Inventory path only."
        )
    if "inventory" not in action:
        raise RuntimeError(
            f"Expected recovered mapping Inventory > Create Listing, got {create['app_action']!r}."
        )


def load_recovered_adapter(path: Path | None = None) -> dict[str, Any]:
    adapter_file = path or ADAPTER_PATH
    adapter = json.loads(adapter_file.read_text(encoding="utf-8"))
    reject_collections_mapping(adapter)
    return adapter


def _headless() -> bool:
    return os.environ.get("SKILLSHIFT_HEADED", "").lower() not in {"1", "true", "yes"}


@contextmanager
def open_hands(
    base_url: str | None = None,
    *,
    headless: bool | None = None,
    allow_collections: bool = False,
) -> Iterator[BrowserHands]:
    url = require_web(base_url)
    use_headless = _headless() if headless is None else headless
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=use_headless)
            except Exception as exc:
                message = str(exc).lower()
                if "executable doesn't exist" in message or "playwright install" in message:
                    raise BrowserMissing(
                        "Playwright Chromium is missing. Run: playwright install chromium"
                    ) from exc
                raise
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            hands = BrowserHands(page, url, allow_collections=allow_collections)
            try:
                yield hands
            finally:
                browser.close()
    except BrowserMissing:
        raise
    except Exception as exc:
        message = str(exc).lower()
        if "executable doesn't exist" in message or "playwright install" in message:
            raise BrowserMissing(
                "Playwright Chromium is missing. Run: playwright install chromium"
            ) from exc
        raise


def execute_recovered_adapter(
    hands: BrowserHands,
    *,
    name: str = PRODUCT_NAME,
    price: str = PRODUCT_PRICE,
    image_path: Path | None = None,
    adapter: dict[str, Any] | None = None,
) -> str:
    """Walk Store B using the recovered adapter. Returns product-card text."""
    resolved = adapter or load_recovered_adapter()
    reject_collections_mapping(resolved)

    image = image_path or BLUE_SNEAKER_IMAGE
    hands.goto("/store-b")
    hands.click("store-b-nav-inventory")
    hands.click("store-b-create-listing")
    hands.type("store-b-field-name", name)
    hands.type("store-b-field-price", price)
    hands.upload("store-b-field-image", image)
    expect(hands.page.get_by_test_id("store-b-go-live")).to_be_enabled()
    hands.click("store-b-go-live")

    card = hands.page.get_by_test_id("store-b-product-card")
    try:
        expect(card).to_be_visible()
        expect(card).to_contain_text(name)
        expect(card).to_contain_text("£120" if price == "120" else price)
    except PlaywrightTimeout as exc:
        raise AssertionError(
            "store-b-product-card was not visible with the published product after Go Live."
        ) from exc
    if "store-b-nav-collections" in hands.clicked or "store-b-collections-create" in hands.clicked:
        raise RuntimeError("Collections was clicked; recovered path was violated.")
    return card.inner_text()


def _apply_testids(hands: BrowserHands, testids: list[str], product: ProductSpec) -> None:
    for testid in testids:
        if testid == "store-b-field-name":
            hands.type(testid, product.name)
        elif testid == "store-b-field-price":
            hands.type(testid, product.price)
        elif testid == "store-b-field-image":
            hands.upload(testid, product.image)
        elif testid == "store-b-go-live":
            expect(hands.page.get_by_test_id(testid)).to_be_enabled()
            hands.click(testid)
        else:
            hands.click(testid)


def execute_until(
    hands: BrowserHands,
    adapter: EnvironmentAdapter,
    skill: Skill,
    product: ProductSpec,
    stop_after_first_step: bool = False,
) -> str | None:
    """Walk skill intents through adapter mappings → locked testids."""
    by_intent = {mapping.semantic_intent: mapping for mapping in adapter.mappings}
    for step in skill.steps:
        mapping = by_intent.get(step.intent)
        if mapping is None:
            continue
        testids = intent_to_testids(mapping.app_action, intent=step.intent)
        _apply_testids(hands, testids, product)
        if stop_after_first_step:
            return None

    card = hands.page.get_by_test_id("store-b-product-card")
    expect(card).to_be_visible()
    expect(card).to_contain_text(product.name)
    expected_price = f"£{product.price}" if not product.price.startswith("£") else product.price
    expect(card).to_contain_text(expected_price)
    return card.inner_text()
