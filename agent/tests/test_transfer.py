"""R1 adaptation tests: constrained explore/verify/recover + optional live transfer."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from agent.adapter import (
    INTENT_SHIPPING,
    INTENT_START,
    empty_store_b_adapter,
    load_skill,
    mapping_for_intent,
)
from agent.executor import LEATHER_BAG, WebUnavailable, open_hands, require_web
from agent.explorer import explore_step
from agent.grounding import validate_candidate
from agent.models import CandidateAction, EnvironmentAdapter, SkillStep, Verification
from agent.recovery import CACHED_ADAPTER_PATH, persist, propose_recovery
from agent.verifier import verify_step

ROOT = Path(__file__).resolve().parents[2]
SKILL_JSON = ROOT / "fixtures" / "skill.json"
ADAPTER_PATH = ROOT / "adapters" / "store_b__publish_product.json"


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_MOCK_LLM", "1")


def test_empty_adapter_cold_start():
    adapter = empty_store_b_adapter()
    assert adapter.mappings == []
    assert adapter.app_id == "store-b"


def test_validate_candidate_rejects_invented_testid():
    elements = [{"testid": "store-b-nav-inventory", "name": "Inventory", "role": "button"}]
    with pytest.raises(ValueError, match="Invented testid"):
        validate_candidate(
            CandidateAction(
                target_testid="store-b-made-up",
                action="click",
                rationale="x",
                confidence=0.5,
            ),
            elements,
        )


def test_explorer_picks_only_visible_testids():
    step = SkillStep(
        intent=INTENT_START,
        required_inputs=[],
        expected_state="a product creation form is visible",
        success_condition="form on screen",
    )
    elements = [
        {"testid": "store-b-nav-collections", "name": "Collections", "role": "button"},
        {"testid": "store-b-nav-inventory", "name": "Inventory", "role": "button"},
        {"testid": "store-b-nav-orders", "name": "Orders", "role": "button"},
    ]
    result = explore_step(step, elements, backend="mock")
    assert result.chosen.target_testid in {e["testid"] for e in elements}


def test_recovery_after_collections_prefers_inventory():
    elements = [
        {"testid": "store-b-nav-collections", "name": "Collections", "role": "button"},
        {"testid": "store-b-nav-inventory", "name": "Inventory", "role": "button"},
        {"testid": "store-b-nav-orders", "name": "Orders", "role": "button"},
    ]
    verification = Verification(
        step_intent=INTENT_START,
        expected_state="a product creation form is visible",
        observed_state="collection management interface",
        matched=False,
        confidence=0.9,
        mismatch_type="wrong_navigation",
        hypothesis="Collections is not product creation",
        alternative="Try Inventory",
    )
    action = propose_recovery(
        verification,
        elements,
        failed_testids={"store-b-nav-collections"},
        backend="mock",
    )
    assert action.target_testid == "store-b-nav-inventory"


def test_recovery_shipping_prerequisite_picks_shipping_field():
    elements = [
        {"testid": "store-b-field-shipping", "name": "Shipping", "role": "select"},
        {"testid": "store-b-go-live", "name": "Go Live", "role": "button"},
    ]
    verification = Verification(
        step_intent="make the product publicly available",
        expected_state="product is published",
        observed_state="Go Live disabled; shipping empty",
        matched=False,
        confidence=0.9,
        mismatch_type="missing_prerequisite",
        hypothesis="additional prerequisite",
        alternative="Set shipping",
    )
    action = propose_recovery(verification, elements, backend="mock")
    assert action.target_testid == "store-b-field-shipping"
    assert action.action == "select"


def test_persist_empty_then_mapping():
    adapter = empty_store_b_adapter()
    path = persist(adapter)
    assert path == ADAPTER_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mappings"] == []


def test_verifier_mismatch_on_collections_page():
    require_web()
    skill = load_skill()
    with open_hands() as hands:
        hands.goto("/store-b")
        verification = verify_step(hands, skill.steps[0], backend="mock")
    assert verification.matched is False
    assert verification.mismatch_type == "wrong_navigation"
    assert "collection" in verification.observed_state.lower()


def test_go_live_blocked_without_shipping():
    require_web()
    skill = load_skill()
    with open_hands() as hands:
        hands.goto("/store-b")
        hands.click("store-b-nav-inventory")
        hands.click("store-b-create-listing")
        hands.type("store-b-field-name", LEATHER_BAG.name)
        hands.type("store-b-field-price", LEATHER_BAG.price)
        hands.upload("store-b-field-image", LEATHER_BAG.image)
        assert not hands.page.get_by_test_id("store-b-go-live").is_enabled()
        assert hands.page.get_by_test_id("store-b-shipping-blocker").is_visible()
        verification = verify_step(hands, skill.steps[-1], backend="mock")
    assert verification.matched is False
    assert verification.mismatch_type == "missing_prerequisite"
    assert "shipping" in verification.observed_state.lower()


def test_go_live_enabled_with_shipping_only():
    """R1: promo gate deferred — shipping alone unlocks Go Live."""
    require_web()
    with open_hands() as hands:
        hands.goto("/store-b")
        hands.click("store-b-nav-inventory")
        hands.click("store-b-create-listing")
        hands.type("store-b-field-name", LEATHER_BAG.name)
        hands.type("store-b-field-price", LEATHER_BAG.price)
        hands.upload("store-b-field-image", LEATHER_BAG.image)
        hands.select("store-b-field-shipping", "Standard")
        assert hands.page.get_by_test_id("store-b-go-live").is_enabled()


def test_full_transfer_cold_and_cached(capsys):
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    os.environ["SKILLSHIFT_MOCK_LLM"] = "1"
    persist(empty_store_b_adapter())

    from agent.run_transfer import main

    assert main() == 0
    out = capsys.readouterr().out
    assert "discover HOW HERE" in out or "Adapter: empty" in out
    assert "STEP:" in out

    persisted = json.loads(ADAPTER_PATH.read_text(encoding="utf-8"))
    assert persisted["mappings"], "adapter should have discovered mappings"
    intents = [m["semantic_intent"] for m in persisted["mappings"]]
    assert INTENT_START in intents
    assert INTENT_SHIPPING in intents
    adapter = EnvironmentAdapter.model_validate(persisted)
    shipping = mapping_for_intent(adapter, INTENT_SHIPPING)
    assert shipping is not None
    assert shipping.resolved_targets
    assert len(json.loads(SKILL_JSON.read_text(encoding="utf-8"))["steps"]) == 4
    assert CACHED_ADAPTER_PATH.is_file()
