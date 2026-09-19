"""Wave 7A: observation contract + test-only Store B state API."""

from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

import pytest

from agent.executor import WebUnavailable, observe_app, open_hands, require_web
from agent.explorer import explore_step
from agent.grounding import elements_from_observation, validate_candidate
from agent.models import AppObservation, CandidateAction, ObservationControl, SkillStep
from agent.observer import observe_app as observe_from_module


def _observation(*refs: str) -> AppObservation:
    return AppObservation(
        screen="Inventory",
        url="http://localhost:3010/store-b",
        controls=[
            ObservationControl(ref=ref, role="button", name=ref.split("-")[-1].title())
            for ref in refs
        ],
    )


def test_observation_controls_skip_empty_refs():
    observation = AppObservation(
        screen="/store-b",
        url="http://localhost:3010/store-b",
        controls=[
            ObservationControl(ref="store-b-nav-inventory", role="button", name="Inventory"),
            ObservationControl(ref="", role="generic", name="skip me"),
        ],
    )
    elements = elements_from_observation(observation)
    assert [item["testid"] for item in elements] == ["store-b-nav-inventory"]


def test_validate_candidate_rejects_invented_from_observation():
    observation = _observation("store-b-nav-inventory")
    with pytest.raises(ValueError, match="Invented testid"):
        validate_candidate(
            CandidateAction(
                target_testid="store-b-made-up",
                action="click",
                rationale="invented",
                confidence=0.4,
            ),
            observation,
        )


def test_explorer_grounds_from_observation_controls():
    observation = _observation(
        "store-b-nav-collections",
        "store-b-nav-inventory",
        "store-b-nav-orders",
    )
    step = SkillStep(
        intent="start creating a new sellable item",
        required_inputs=[],
        expected_state="a product creation form is visible",
        success_condition="form on screen",
    )
    result = explore_step(step, observation=observation, backend="mock")
    allowed = {control.ref for control in observation.controls}
    assert result.chosen.target_testid in allowed


def test_observe_app_visible_refs_only():
    try:
        require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    with open_hands() as hands:
        hands.goto("/store-b")
        observation = observe_app(hands)
        same = observe_from_module(hands)
    refs = {control.ref for control in observation.controls}
    assert refs
    assert all(control.ref for control in observation.controls)
    assert "store-b-nav-collections" in refs
    assert "store-b-nav-inventory" in refs
    # Landing screen is Collections — listing form is not visible yet.
    assert "store-b-field-name" not in refs
    assert observation.screen
    assert "/store-b" in observation.url
    assert {c.ref for c in same.controls} == refs
    # No HOW HERE advice in state.
    blob = " ".join(observation.state.values()).lower()
    assert "click inventory" not in blob


def test_store_b_state_api_json():
    try:
        base = require_web()
    except WebUnavailable:
        pytest.skip("web not running")

    url = f"{base}/api/store-b-state?title={quote('Leather Bag')}"
    try:
        with urlopen(url, timeout=4) as response:  # noqa: S310 — local demo URL
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError):
        pytest.skip("store-b-state API not reachable")

    assert set(payload) >= {"product_exists", "title", "price", "status", "purchasable"}
    assert payload["status"] in {"published", "none"}
    if payload["product_exists"]:
        assert payload["status"] == "published"
        assert payload["purchasable"] is True
    else:
        assert payload["status"] == "none"
        assert payload["purchasable"] is False
