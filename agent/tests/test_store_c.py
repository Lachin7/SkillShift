"""Store C transfer. Mock LLM proves plumbing; semantics need a real-key run."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.adapter import (
    INTENT_DETAILS,
    INTENT_IMAGE,
    INTENT_PUBLISH,
    INTENT_START,
    empty_adapter,
    load_skill,
    mapping_for_intent,
    persisted_adapter_path,
)
from agent.executor import (
    BLUE_SNEAKER,
    LEATHER_BAG,
    WebUnavailable,
    execute_resolved_targets,
    live_products_path,
    open_hands,
    require_web,
)
from agent.metrics import snapshot, start_run
from agent.recovery import persist
from agent.targets import current_target
from agent.transfer_loop import run_store_b_transfer

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_C = ROOT / "adapters" / "store_c__publish_product.json"
ADAPTER_B = ROOT / "adapters" / "store_b__publish_product.json"


@pytest.fixture(autouse=True)
def _store_c_env(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_MOCK_LLM", "1")
    monkeypatch.setenv("SKILLSHIFT_TARGET_APP", "store-c")


def test_store_c_never_reads_store_b_adapter():
    target = current_target()
    assert target.app_id == "store-c"
    path = persisted_adapter_path()
    assert path == ADAPTER_C
    assert path != ADAPTER_B
    assert "store_b" not in path.name


def test_execute_resolved_targets_replays_store_c_trail():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    live_products_path().write_text("[]\n", encoding="utf-8")
    with open_hands() as hands:
        hands.goto("/store-c")
        execute_resolved_targets(
            hands,
            [
                "store-c-nav-listings",
                "store-c-new-row",
                "store-c-field-title",
                "store-c-field-amount",
                "store-c-field-photo",
                "store-c-field-category",
                "store-c-field-status",
                "store-c-save-row",
            ],
            LEATHER_BAG,
        )
        card = hands.page.get_by_test_id("store-c-product-card").filter(
            has_text=LEATHER_BAG.name
        )
        assert card.count() == 1


def test_store_c_cold_start_then_cache_hit():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    persist(empty_adapter("store-c"))
    live_products_path().write_text("[]\n", encoding="utf-8")
    skill = load_skill()
    assert len(skill.steps) == 4

    with open_hands() as hands:
        start_run(LEATHER_BAG.name)
        adapter, _ = run_store_b_transfer(
            hands, skill, LEATHER_BAG, empty_adapter("store-c"), persist_adapter=True
        )
        first = snapshot()
        start_run(BLUE_SNEAKER.name)
        adapter2, _ = run_store_b_transfer(
            hands, skill, BLUE_SNEAKER, adapter, persist_adapter=True
        )
        second = snapshot()

    intents = [item.semantic_intent for item in adapter2.mappings]
    assert INTENT_START in intents
    assert INTENT_DETAILS in intents
    assert INTENT_IMAGE in intents
    assert INTENT_PUBLISH in intents
    assert any("category" in item for item in intents)
    assert first.recoveries >= 1
    assert second.model_calls < first.model_calls
    assert second.recoveries < first.recoveries

    publish = mapping_for_intent(adapter2, INTENT_PUBLISH)
    assert publish is not None
    assert "store-c-field-status" in publish.resolved_targets
    assert "store-c-save-row" in publish.resolved_targets

    persisted = json.loads(ADAPTER_C.read_text(encoding="utf-8"))
    assert persisted["app_id"] == "store-c"
    assert persisted["mappings"]
