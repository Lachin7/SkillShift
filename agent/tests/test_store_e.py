"""Store E transfer. Mock LLM proves plumbing only — labels are Farsi."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agent.adapter import (
    INTENT_DETAILS,
    INTENT_IMAGE,
    INTENT_PUBLISH,
    INTENT_SHIPPING,
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
    live_products_path,
    open_hands,
    require_web,
)
from agent.metrics import snapshot, start_run
from agent.recovery import persist
from agent.targets import current_target
from agent.transfer_loop import run_store_b_transfer

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "web" / "app" / "store-e" / "page.tsx"
ADAPTER_E = ROOT / "adapters" / "store_e__publish_product.json"
ADAPTER_B = ROOT / "adapters" / "store_b__publish_product.json"


@pytest.fixture(autouse=True)
def _store_e_env(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_MOCK_LLM", "1")
    monkeypatch.setenv("SKILLSHIFT_TARGET_APP", "store-e")


def test_store_b_does_not_read_store_e_adapter(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_TARGET_APP", "store-b")
    assert current_target().app_id == "store-b"
    path = persisted_adapter_path()
    assert path == ADAPTER_B
    assert path != ADAPTER_E


def test_store_e_visible_copy_has_no_ascii_letters():
    """Source lint only. Mock transfer below does not prove Farsi grounding."""
    source = PAGE.read_text(encoding="utf-8")
    texts = [item.strip() for item in re.findall(r">([^<>{}\n]+)<", source)]
    leaked = [item for item in texts if item and re.search(r"[A-Za-z]", item)]
    assert leaked == []


def test_store_e_is_rtl():
    source = PAGE.read_text(encoding="utf-8")
    assert 'lang="fa"' in source
    assert 'dir="rtl"' in source


def test_store_e_cold_start_then_cache_hit():
    """Plumbing: suffix heuristics + own adapter file. Semantics need a real key."""
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    persist(empty_adapter("store-e"))
    live_products_path().write_text("[]\n", encoding="utf-8")
    skill = load_skill()
    assert len(skill.steps) == 4

    with open_hands() as hands:
        start_run(LEATHER_BAG.name)
        adapter, _ = run_store_b_transfer(
            hands, skill, LEATHER_BAG, empty_adapter("store-e"), persist_adapter=True
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
    assert INTENT_SHIPPING in intents
    assert first.recoveries >= 1
    assert second.model_calls < first.model_calls

    publish = mapping_for_intent(adapter2, INTENT_PUBLISH)
    assert publish is not None
    assert publish.resolved_targets == ["store-e-release"]

    persisted = json.loads(ADAPTER_E.read_text(encoding="utf-8"))
    assert persisted["app_id"] == "store-e"
