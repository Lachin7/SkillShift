"""Wave 7B: independent verifier + diagnoser."""

from __future__ import annotations

from agent.adapter import load_skill
from agent.executor import LEATHER_BAG, WebUnavailable, open_hands, require_web
from agent.failure_diagnoser import diagnose_failure
from agent.observer import observe_app
from agent.verifier import verify_independent, verify_step
import pytest


def test_collections_page_is_wrong_mapping_or_navigation():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    skill = load_skill()
    with open_hands() as hands:
        hands.goto("/store-b")
        verification, result = verify_independent(hands, skill.steps[0], backend="mock")
        observation = observe_app(hands)
        diagnosis = diagnose_failure(
            result,
            observation,
            [],
            backend="mock",
            expected_state=skill.steps[0].expected_state,
        )
    assert verification.matched is False
    assert verification.mismatch_type == "wrong_navigation"
    assert result.failure_class in {"wrong_mapping", "navigation_error"}
    assert diagnosis.failure_class in {"wrong_mapping", "navigation_error"}
    assert "collection" in verification.observed_state.lower()
    assert "RECOVERED_ACTION" not in (diagnosis.hypothesis or "")
    assert "RECOVERED_ACTION" not in (diagnosis.alternative or "")


def test_blocked_go_live_is_missing_prerequisite_with_shipping_evidence():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    skill = load_skill()
    with open_hands() as hands:
        hands.goto("/store-b")
        hands.click("store-b-nav-inventory")
        hands.click("store-b-create-listing")
        hands.type("store-b-field-name", LEATHER_BAG.name)
        hands.type("store-b-field-price", LEATHER_BAG.price)
        hands.upload("store-b-field-image", LEATHER_BAG.image)
        verification, result = verify_independent(
            hands, skill.steps[-1], product_name=LEATHER_BAG.name, backend="mock"
        )
        diagnosis = diagnose_failure(
            result,
            observe_app(hands),
            ["store-b-go-live"],
            backend="mock",
            expected_state=skill.steps[-1].expected_state,
        )
    assert verification.matched is False
    assert verification.mismatch_type == "missing_prerequisite"
    assert result.failure_class == "missing_prerequisite"
    blob = " ".join(result.observed_evidence).lower()
    assert "shipping" in blob or "blocker" in blob
    assert diagnosis.failure_class == "missing_prerequisite"
    assert "shipping" in " ".join(diagnosis.observed_evidence).lower() or "shipping" in (
        diagnosis.hypothesis + diagnosis.alternative
    ).lower()


def test_verify_step_still_returns_legacy_verification():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    skill = load_skill()
    with open_hands() as hands:
        hands.goto("/store-b")
        verification = verify_step(hands, skill.steps[0], backend="mock")
    assert verification.matched is False
    assert verification.mismatch_type == "wrong_navigation"
