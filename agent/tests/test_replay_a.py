"""Wave 5B: same-environment Skill replay on Store A. No shipping, no Collections."""

from __future__ import annotations

import json
from pathlib import Path

from agent.adapter import STORE_A_ADAPTER_PATH, load_skill, load_store_a_adapter
from agent.executor import (
    CERAMIC_MUG,
    WebUnavailable,
    execute_store_a,
    open_hands,
    require_web,
)

ROOT = Path(__file__).resolve().parents[2]
SKILL_JSON = ROOT / "fixtures" / "skill.json"
LIVE_DASHBOARD = ROOT / "fixtures" / "live" / "dashboard-state.json"


def test_store_a_adapter_is_cached_no_shipping():
    adapter = load_store_a_adapter()
    assert adapter.app_id == "store-a"
    assert STORE_A_ADAPTER_PATH.is_file()
    intents = [mapping.semantic_intent for mapping in adapter.mappings]
    assert "satisfy environment prerequisite: shipping category" not in intents
    assert all(mapping.learned_from in {"cached", "exploration"} for mapping in adapter.mappings)
    assert len(json.loads(SKILL_JSON.read_text(encoding="utf-8"))["steps"]) == 4


def test_replay_a_publishes_catalog_item_not_leather_bag():
    try:
        require_web()
    except WebUnavailable:
        raise
    skill = load_skill()
    adapter = load_store_a_adapter()
    with open_hands() as hands:
        hands.goto("/store-a")
        card = execute_store_a(hands, adapter, skill, CERAMIC_MUG)
        assert "Ceramic Mug" in card
        assert "£24" in card
        assert hands.page.get_by_test_id("store-a-product-card").filter(
            has_text="Ceramic Mug"
        ).is_visible()
        assert "store-a-add-product" in hands.clicked
        assert "store-a-publish" in hands.clicked
        assert "store-b-field-shipping" not in hands.clicked
        assert "store-b-go-live" not in hands.clicked


def test_full_replay_a_if_server_up(capsys):
    try:
        require_web()
    except WebUnavailable:
        raise
    from agent.run_replay_a import main

    assert main() == 0
    out = capsys.readouterr().out
    assert "Same environment. Exploration skipped." in out
    assert "Ceramic Mug" in out
    assert "Leather Bag" not in out
    live = json.loads(LIVE_DASHBOARD.read_text(encoding="utf-8"))
    assert live["app"]["app_id"] == "store-a"
    assert live["app"]["unseen"] is False
    assert "Same environment" in live["status"]["message"]
    assert "Exploration skipped" in live["status"]["message"]
    assert len(json.loads(SKILL_JSON.read_text(encoding="utf-8"))["steps"]) == 4
    assert not any(
        mapping["semantic_intent"] == "satisfy environment prerequisite: shipping category"
        for mapping in live["adapter"]["mappings"]
    )
