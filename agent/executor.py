"""Playwright hands for SkillShift.

Brain (explorer / verifier / recovery) chooses grounded CandidateActions.
This module only executes them and provides screenshots / visible_elements.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from playwright.sync_api import expect, sync_playwright

from .adapter import STORE_A_TESTIDS, intent_to_testids
from .models import CandidateAction, EnvironmentAdapter, Skill

DEFAULT_DEMO_PAUSE = 1.2
DEFAULT_DEMO_HOLD = 3.0
HEADED_SLOW_MO_MS = 400

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://localhost:3010"
BLUE_SNEAKER_IMAGE = REPO_ROOT / "web" / "public" / "products" / "blue-sneaker.svg"
LEATHER_BAG_IMAGE = REPO_ROOT / "web" / "public" / "products" / "leather-bag.svg"
CERAMIC_MUG_IMAGE = REPO_ROOT / "web" / "public" / "products" / "ceramic-mug.svg"
BRASS_LAMP_IMAGE = REPO_ROOT / "web" / "public" / "products" / "brass-lamp.svg"
def live_products_path() -> Path:
    from .targets import current_target

    return REPO_ROOT / current_target().live_products_file


LIVE_PRODUCTS_PATH = REPO_ROOT / "fixtures" / "live" / "store-b-products.json"

PRODUCT_NAME = "Blue Sneaker"
PRODUCT_PRICE = "120"


@dataclass(frozen=True)
class ProductSpec:
    name: str
    price: str
    image: Path


LEATHER_BAG = ProductSpec("Leather Bag", "89", LEATHER_BAG_IMAGE)
BLUE_SNEAKER = ProductSpec("Blue Sneaker", "120", BLUE_SNEAKER_IMAGE)
CERAMIC_MUG = ProductSpec("Ceramic Mug", "24", CERAMIC_MUG_IMAGE)
BRASS_LAMP = ProductSpec("Brass Lamp", "76", BRASS_LAMP_IMAGE)


class WebUnavailable(RuntimeError):
    """Next.js is not reachable. This module does not start the frontend."""


class BrowserMissing(RuntimeError):
    """Playwright Chromium is not installed."""


class MissingTargetError(RuntimeError):
    """A cached testid is no longer in the DOM — diagnosable stale mapping."""

    def __init__(self, testid: str):
        super().__init__(f"saved testid missing: {testid}")
        self.testid = testid


class BrowserHands:
    """Primitive Playwright actions. Callers pass data-testid values."""

    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")
        self.clicked: list[str] = []

    def goto(self, path: str = "/store-b") -> None:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.page.goto(url, wait_until="domcontentloaded")
        try:
            self.page.locator("[data-testid*='-nav-']").first.wait_for(
                state="visible", timeout=5000
            )
        except Exception:
            pass

    def screenshot(self, path: str | Path | None = None) -> bytes:
        data = self.page.screenshot(type="png")
        if path is not None:
            destination = Path(path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        return data

    def visible_elements(self) -> list[dict[str, str]]:
        """DOM/accessibility summary of nodes with data-testid."""
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

    def click(self, testid: str) -> None:
        self.clicked.append(testid)
        self.page.get_by_test_id(testid).click()
        from .metrics import record_action

        record_action()

    def type(self, testid: str, text: str) -> None:
        self.page.get_by_test_id(testid).fill(text)
        from .metrics import record_action

        record_action()

    def upload(self, testid: str, image_path: str | Path) -> None:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Image not found: {path}")
        self.page.get_by_test_id(testid).set_input_files(str(path))
        from .metrics import record_action

        record_action()

    def select(self, testid: str, value: str) -> None:
        locator = self.page.get_by_test_id(testid)
        option = locator.locator(f"option[value='{value}']")
        if option.count() and option.get_attribute("disabled") is not None:
            return
        locator.select_option(value)
        from .metrics import record_action

        record_action()


def observe_app(hands: BrowserHands):
    """Generic snapshot wrapper. Decision logic lives in observer + brain modules."""
    from .observer import observe_app as _observe_app

    return _observe_app(hands)


def execute_candidate(
    hands: BrowserHands,
    action: CandidateAction,
    *,
    product: ProductSpec | None = None,
) -> None:
    """Execute one grounded CandidateAction. No Store B decision logic."""
    testid = action.target_testid
    if action.action == "click":
        locator = hands.page.get_by_test_id(testid)
        if testid.endswith(("go-live", "publish", "launch-product", "save-row")):
            try:
                expect(locator).to_be_enabled(timeout=5000)
            except (PlaywrightTimeout, AssertionError):
                # Still blocked — leave page as-is for the verifier.
                return
        hands.click(testid)
    elif action.action == "fill":
        value = action.value
        if value is None and product is not None:
            if "price" in testid or "amount" in testid:
                value = product.price
            else:
                value = product.name
        if value is None:
            raise RuntimeError(f"fill action missing value for {testid}")
        hands.type(testid, value)
    elif action.action == "upload":
        path = action.value or (str(product.image) if product else None)
        if not path:
            raise RuntimeError(f"upload action missing path for {testid}")
        hands.upload(testid, path)
    elif action.action == "select":
        from .grounding import default_select_value

        value = action.value or default_select_value(testid) or "Standard"
        hands.select(testid, value)
        if any(token in testid for token in ("shipping", "tax-class", "category")):
            _wait_finish_enabled(hands)
    else:
        raise RuntimeError(f"Unknown action {action.action!r}")
    demo_pause()


def _testid_present(hands: BrowserHands, testid: str) -> bool:
    try:
        return hands.page.get_by_test_id(testid).count() > 0
    except Exception:
        return False


def _wait_finish_enabled(hands: BrowserHands) -> None:
    from .grounding import FINISH_SUFFIXES

    for suffix in FINISH_SUFFIXES:
        locator = hands.page.locator(f"[data-testid$='{suffix}']")
        if locator.count() == 0:
            continue
        try:
            expect(locator.first).to_be_enabled(timeout=5000)
            return
        except (PlaywrightTimeout, AssertionError):
            return


def execute_resolved_targets(
    hands: BrowserHands,
    targets: list[str],
    product: ProductSpec,
) -> None:
    """Replay a saved trail of testids (cached adapter fast path)."""
    for testid in targets:
        if not _testid_present(hands, testid):
            raise MissingTargetError(testid)
        form_open = False
        try:
            name_loc = hands.page.locator(
                "[data-testid$='-field-name'], [data-testid$='-field-title']"
            )
            form_open = name_loc.count() > 0 and name_loc.first.is_visible()
        except Exception:
            form_open = False
        if testid.endswith(
            ("-nav-inventory", "-nav-catalog", "-nav-listings", "-create-listing", "-new-row")
        ):
            if form_open:
                continue
        if testid.endswith(("-field-name", "-field-title")):
            hands.type(testid, product.name)
        elif testid.endswith(("-field-price", "-field-amount")):
            hands.type(testid, product.price)
        elif testid.endswith(("-field-image", "-field-photo")):
            hands.upload(testid, product.image)
        elif testid.endswith("-field-status"):
            hands.select(testid, "Live")
        elif testid.endswith(("-field-shipping", "-field-tax-class", "-field-category")):
            value = "Standard"
            if testid.endswith("-field-tax-class"):
                value = "Standard rate"
            elif testid.endswith("-field-category"):
                value = "General"
            hands.select(testid, value)
            _wait_finish_enabled(hands)
        elif testid.endswith("-field-listing-type"):
            hands.select(testid, "Public")
        elif testid.endswith("-product-card"):
            continue
        elif testid.endswith(("-go-live", "-launch-product", "-publish", "-save-row")):
            locator = hands.page.get_by_test_id(testid)
            try:
                expect(locator).to_be_enabled(timeout=2000)
            except (PlaywrightTimeout, AssertionError):
                return
            hands.click(testid)
        else:
            hands.click(testid)
        demo_pause()


def require_web(base_url: str | None = None) -> str:
    url = (base_url or os.environ.get("SKILLSHIFT_WEB_URL") or DEFAULT_BASE_URL).rstrip(
        "/"
    )
    probe = f"{url}/"
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


def _headless() -> bool:
    return os.environ.get("SKILLSHIFT_HEADED", "").lower() not in {"1", "true", "yes"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    return float(raw)


def demo_pause_seconds() -> float:
    if _headless():
        return 0.0
    return _env_float("SKILLSHIFT_DEMO_PAUSE", DEFAULT_DEMO_PAUSE)


def demo_hold_seconds() -> float:
    if _headless():
        return 0.0
    return _env_float("SKILLSHIFT_DEMO_HOLD", DEFAULT_DEMO_HOLD)


def demo_pause(seconds: float | None = None) -> None:
    delay = demo_pause_seconds() if seconds is None else seconds
    if delay > 0:
        time.sleep(delay)


def demo_hold(seconds: float | None = None) -> None:
    delay = demo_hold_seconds() if seconds is None else seconds
    if delay > 0:
        time.sleep(delay)


def public_product_image(product: ProductSpec) -> str:
    return f"/products/{product.image.name}"


def persist_live_product(product: ProductSpec) -> Path:
    destination = live_products_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, str]] = []
    if destination.is_file():
        raw = json.loads(destination.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            items = [item for item in raw if isinstance(item, dict)]
    price = product.price if product.price.startswith("£") else f"£{product.price}"
    entry = {
        "name": product.name,
        "price": price,
        "image": public_product_image(product),
    }
    items = [item for item in items if item.get("name") != product.name]
    items.append(entry)
    destination.write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
    return destination


@contextmanager
def open_hands(
    base_url: str | None = None,
    *,
    headless: bool | None = None,
) -> Iterator[BrowserHands]:
    url = require_web(base_url)
    use_headless = _headless() if headless is None else headless
    slow_mo = 0 if use_headless else HEADED_SLOW_MO_MS
    try:
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(
                    headless=use_headless,
                    slow_mo=slow_mo,
                )
            except Exception as exc:
                message = str(exc).lower()
                if "executable doesn't exist" in message or "playwright install" in message:
                    raise BrowserMissing(
                        "Playwright Chromium is missing. Run: playwright install chromium"
                    ) from exc
                raise
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            hands = BrowserHands(page, url)
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


def _wait_store_a_testid(hands: BrowserHands, testid: str) -> None:
    expect(hands.page.get_by_test_id(testid)).to_be_visible()


def _apply_store_a_testids(hands: BrowserHands, testids: list[str], product: ProductSpec) -> None:
    for testid in testids:
        if testid not in STORE_A_TESTIDS:
            raise RuntimeError(f"Store A path refused non-A testid: {testid}")
        if testid == "store-a-add-product":
            hands.click(testid)
            _wait_store_a_testid(hands, "store-a-field-name")
        elif testid == "store-a-field-name":
            hands.type(testid, product.name)
        elif testid == "store-a-field-price":
            hands.type(testid, product.price)
            demo_pause()
            continue_media = hands.page.get_by_role("button", name="Continue to Media")
            expect(continue_media).to_be_enabled()
            continue_media.click()
            _wait_store_a_testid(hands, "store-a-field-image")
        elif testid == "store-a-field-image":
            hands.upload(testid, product.image)
            demo_pause()
            continue_publish = hands.page.get_by_role("button", name="Continue to Publish")
            expect(continue_publish).to_be_enabled()
            continue_publish.click()
            _wait_store_a_testid(hands, "store-a-publish")
        elif testid == "store-a-publish":
            expect(hands.page.get_by_test_id(testid)).to_be_enabled()
            hands.click(testid)
            _wait_store_a_testid(hands, "store-a-product-card")
        else:
            hands.click(testid)
        demo_pause()


def execute_store_a(
    hands: BrowserHands,
    adapter: EnvironmentAdapter,
    skill: Skill,
    product: ProductSpec,
) -> str:
    """Replay the frozen Skill on Store A via cached adapter strings."""
    if adapter.app_id != "store-a":
        raise RuntimeError(f"execute_store_a expected store-a adapter, got {adapter.app_id!r}.")
    if product.name == "Leather Bag":
        raise RuntimeError("Same-environment replay must use a new catalog item, not Leather Bag.")
    rec = hands.page.get_by_role("button", name="Rec")
    if rec.count() > 0 and rec.get_attribute("aria-pressed") == "true":
        rec.click()
        expect(hands.page.get_by_role("button", name="Start")).to_be_visible()
    by_intent = {mapping.semantic_intent: mapping for mapping in adapter.mappings}
    for step in skill.steps:
        mapping = by_intent.get(step.intent)
        if mapping is None:
            raise RuntimeError(f"Store A adapter missing mapping for {step.intent!r}.")
        if mapping.resolved_targets:
            testids = mapping.resolved_targets
        else:
            testids = intent_to_testids(
                mapping.app_action, intent=step.intent, app_id="store-a"
            )
        _apply_store_a_testids(hands, testids, product)

    card = hands.page.get_by_test_id("store-a-product-card").filter(has_text=product.name)
    expect(card).to_be_visible()
    expected_price = f"£{product.price}" if not product.price.startswith("£") else product.price
    expect(card).to_contain_text(expected_price)
    return card.inner_text()
