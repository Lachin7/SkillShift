"""Which app the hands are in — not how that app grounds a Skill step.

AppTarget is environment plumbing: which app, where it lives, where its adapter is
persisted. It must never say "in this app, intent X means control Y" — that is the
Adapter, and it is discovered by the Explorer at run time.
"""

from __future__ import annotations

import os

from pydantic import BaseModel


class AppTarget(BaseModel):
    app_id: str
    label: str
    path: str
    testid_prefix: str
    product_card_testid: str
    live_products_file: str
    adapter_file: str


TARGETS: dict[str, AppTarget] = {
    "store-a": AppTarget(
        app_id="store-a",
        label="Store A",
        path="/store-a",
        testid_prefix="store-a-",
        product_card_testid="store-a-product-card",
        live_products_file="fixtures/live/store-a-products.json",
        adapter_file="adapters/store_a__publish_product.json",
    ),
    "store-b": AppTarget(
        app_id="store-b",
        label="Store B",
        path="/store-b",
        testid_prefix="store-b-",
        product_card_testid="store-b-product-card",
        live_products_file="fixtures/live/store-b-products.json",
        adapter_file="adapters/store_b__publish_product.json",
    ),
    "store-c": AppTarget(
        app_id="store-c",
        label="Store C",
        path="/store-c",
        testid_prefix="store-c-",
        product_card_testid="store-c-product-card",
        live_products_file="fixtures/live/store-c-products.json",
        adapter_file="adapters/store_c__publish_product.json",
    ),
}


def current_target() -> AppTarget:
    app_id = os.environ.get("SKILLSHIFT_TARGET_APP", "store-b").strip() or "store-b"
    if app_id not in TARGETS:
        raise RuntimeError(
            f"Unknown SKILLSHIFT_TARGET_APP={app_id!r}. Known: {sorted(TARGETS)}"
        )
    return TARGETS[app_id]
