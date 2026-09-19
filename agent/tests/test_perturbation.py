"""Wave 8A: judge-controlled Store B perturbations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.adapter import INTENT_START, empty_store_b_adapter, load_skill, mapping_for_intent
from agent.executor import (
    LEATHER_BAG,
    LIVE_PRODUCTS_PATH,
    MissingTargetError,
    WebUnavailable,
    execute_resolved_targets,
    open_hands,
    require_web,
)
from agent.explorer import explore_step
from agent.failure_diagnoser import diagnose_failure
from agent.models import AppObservation, ObservationControl, SkillStep, StepMapping, VerificationResult
from agent.observer import observe_app
from agent.recovery import persist
from agent.transfer_loop import run_store_b_transfer
from agent.verifier import verify_independent

ROOT = Path(__file__).resolve().parents[2]
PERTURB = ROOT / "fixtures" / "live" / "perturbations.json"
ADAPTER = ROOT / "adapters" / "store_b__publish_product.json"


def _write_flags(**flags: bool) -> None:
    payload = {
        "rename_publish": False,
        "extra_required": False,
        "reorder_nav": False,
        **flags,
    }
    PERTURB.parent.mkdir(parents=True, exist_ok=True)
    PERTURB.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _warm_adapter():
    return persist(
        empty_store_b_adapter().model_copy(
            update={
                "adapter_version": 1,
                "mappings": [
                    StepMapping(
                        semantic_intent="start creating a new sellable item",
                        app_action="Inventory > Create Listing",
                        confidence=0.9,
                        learned_from="cached",
                        resolved_targets=["store-b-nav-inventory", "store-b-create-listing"],
                        status="reusable",
                        successes=2,
                    ),
                    StepMapping(
                        semantic_intent="provide basic product information",
                        app_action="name / price",
                        confidence=0.9,
                        learned_from="cached",
                        resolved_targets=["store-b-field-name", "store-b-field-price"],
                        status="reusable",
                        successes=2,
                    ),
                    StepMapping(
                        semantic_intent="attach the product image",
                        app_action="image",
                        confidence=0.9,
                        learned_from="cached",
                        resolved_targets=["store-b-field-image"],
                        status="reusable",
                        successes=2,
                    ),
                    StepMapping(
                        semantic_intent="satisfy environment prerequisite: shipping category",
                        app_action="shipping",
                        confidence=0.9,
                        learned_from="cached",
                        resolved_targets=["store-b-field-shipping"],
                        status="reusable",
                        successes=2,
                    ),
                    StepMapping(
                        semantic_intent="make the product publicly available",
                        app_action="Go Live",
                        confidence=0.9,
                        learned_from="cached",
                        resolved_targets=["store-b-go-live"],
                        status="reusable",
                        successes=2,
                    ),
                ],
            }
        )
    )


@pytest.fixture(autouse=True)
def _reset_flags():
    _write_flags()
    yield
    _write_flags()


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.setenv("SKILLSHIFT_MOCK_LLM", "1")


def test_rename_publish_swaps_testid():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")
    _write_flags(rename_publish=True)
    with open_hands() as hands:
        hands.goto("/store-b")
        hands.page.wait_for_timeout(1200)
        hands.click("store-b-nav-inventory")
        hands.click("store-b-create-listing")
        assert hands.page.get_by_test_id("store-b-go-live").count() == 0
        assert hands.page.get_by_test_id("store-b-launch-product").count() == 1


def test_rename_publish_warm_adapter_stale_then_remap():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")
    _write_flags(rename_publish=True)
    LIVE_PRODUCTS_PATH.write_text("[]\n", encoding="utf-8")
    _warm_adapter()
    before = json.loads(ADAPTER.read_text(encoding="utf-8"))
    version_before = before.get("adapter_version", 1)
    skill = load_skill()
    warm = empty_store_b_adapter()
    warm = type(warm).model_validate_json(ADAPTER.read_text(encoding="utf-8"))
    with open_hands() as hands:
        adapter, _ = run_store_b_transfer(
            hands, skill, LEATHER_BAG, warm, persist_adapter=True
        )
    publish = mapping_for_intent(adapter, "make the product publicly available")
    assert publish is not None
    assert "store-b-launch-product" in publish.resolved_targets
    assert adapter.adapter_version > version_before
    deprecated = [m for m in adapter.mappings if m.status == "deprecated"]
    assert deprecated or publish.resolved_targets == ["store-b-launch-product"]


def test_stale_mapping_diagnoser_on_missing_testid():
    result = VerificationResult(
        passed=False,
        confidence=0.9,
        expected_state="product is published",
        observed_evidence=["saved testid missing: store-b-go-live"],
        failure_class="stale_mapping",
    )
    observation = AppObservation(
        screen="Create Listing",
        controls=[
            ObservationControl(ref="store-b-launch-product", role="button", name="Launch Product"),
        ],
    )
    diagnosis = diagnose_failure(result, observation, ["store-b-go-live"], backend="mock")
    assert diagnosis.failure_class == "stale_mapping"
    step = SkillStep(
        intent="make the product publicly available",
        required_inputs=[],
        expected_state="product is published",
        success_condition="card",
    )
    explored = explore_step(
        step,
        observation=observation,
        backend="mock",
    )
    assert explored.chosen.target_testid == "store-b-launch-product"


def test_extra_required_warm_adapter_adds_tax():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")
    _write_flags(extra_required=True)
    LIVE_PRODUCTS_PATH.write_text("[]\n", encoding="utf-8")
    _warm_adapter()
    skill = load_skill()
    warm = type(empty_store_b_adapter()).model_validate_json(ADAPTER.read_text(encoding="utf-8"))
    with open_hands() as hands:
        adapter, _ = run_store_b_transfer(
            hands, skill, LEATHER_BAG, warm, persist_adapter=True
        )
    intents = [item.semantic_intent for item in adapter.mappings]
    assert any("tax" in item for item in intents)
    tax = next(item for item in adapter.mappings if "tax" in item.semantic_intent)
    assert tax.resolved_targets == ["store-b-field-tax-class"]


def test_reorder_nav_remaps_create_step():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")
    _write_flags(reorder_nav=True)
    LIVE_PRODUCTS_PATH.write_text("[]\n", encoding="utf-8")
    _warm_adapter()
    skill = load_skill()
    warm = type(empty_store_b_adapter()).model_validate_json(ADAPTER.read_text(encoding="utf-8"))
    with open_hands() as hands:
        adapter, _ = run_store_b_transfer(
            hands, skill, LEATHER_BAG, warm, persist_adapter=True
        )
    start = mapping_for_intent(adapter, INTENT_START)
    assert start is not None
    assert "store-b-nav-catalog" in start.resolved_targets


def test_missing_target_error_is_clean():
    class FakeLocator:
        def count(self) -> int:
            return 0

    class FakePage:
        def get_by_test_id(self, testid: str) -> FakeLocator:
            return FakeLocator()

        def locator(self, _sel: str) -> FakeLocator:
            return FakeLocator()

    from agent.executor import BrowserHands

    hands = BrowserHands(FakePage(), "http://localhost:3010")  # type: ignore[arg-type]
    with pytest.raises(MissingTargetError, match="saved testid missing"):
        execute_resolved_targets(hands, ["store-b-go-live"], LEATHER_BAG)
