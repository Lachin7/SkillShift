"""Wave 7C: AdapterPatch curator applies only after verified retry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent.adapter import INTENT_PUBLISH, INTENT_SHIPPING, empty_store_b_adapter, load_skill
from agent.adapter_curator import apply_patch
from agent.models import (
    AdapterPatch,
    AppObservation,
    ObservationControl,
    StepMapping,
    Verification,
)

SKILL_JSON = Path(__file__).resolve().parents[2] / "fixtures" / "skill.json"


def _shipping_observation() -> AppObservation:
    return AppObservation(
        screen="Create Listing",
        url="http://localhost:3010/store-b",
        controls=[
            ObservationControl(ref="store-b-field-shipping", role="select", name="Shipping"),
            ObservationControl(ref="store-b-go-live", role="button", name="Go Live", enabled=True),
        ],
        messages=["Select a shipping category to go live."],
    )


def _passed() -> Verification:
    return Verification(
        step_intent=INTENT_PUBLISH,
        expected_state="product is published",
        observed_state="public product card visible",
        matched=True,
        mismatch_type="none",
        failure_class="none",
    )


def _failed() -> Verification:
    return Verification(
        step_intent=INTENT_PUBLISH,
        expected_state="product is published",
        observed_state="Go Live disabled; shipping empty",
        matched=False,
        mismatch_type="missing_prerequisite",
        failure_class="missing_prerequisite",
    )


def test_add_prerequisite_inserts_shipping_leaves_skill_intents():
    skill_before = json.loads(SKILL_JSON.read_text(encoding="utf-8"))
    skill = load_skill()
    frozen = [step.intent for step in skill.steps]
    assert len(frozen) == 4

    adapter = empty_store_b_adapter()
    adapter.mappings.append(
        StepMapping(
            semantic_intent=INTENT_PUBLISH,
            app_action="Go Live",
            confidence=0.8,
            learned_from="exploration",
            resolved_targets=["store-b-go-live"],
        )
    )
    patch = AdapterPatch(
        semantic_intent=INTENT_SHIPPING,
        operation="add_prerequisite",
        new_targets=["store-b-field-shipping"],
        new_app_action="Shipping category",
        evidence=["Go Live disabled", "shipping blocker"],
    )
    updated = apply_patch(adapter, patch, _passed(), _shipping_observation())
    intents = [item.semantic_intent for item in updated.mappings]
    assert INTENT_SHIPPING in intents
    assert intents.index(INTENT_SHIPPING) < intents.index(INTENT_PUBLISH)
    shipping = next(item for item in updated.mappings if item.semantic_intent == INTENT_SHIPPING)
    assert shipping.resolved_targets == ["store-b-field-shipping"]
    assert shipping.status == "provisional"
    assert shipping.successes == 1
    assert [step.intent for step in skill.steps] == frozen
    assert json.loads(SKILL_JSON.read_text(encoding="utf-8")) == skill_before
    assert patch.applied is True


def test_curator_refuses_failed_verification():
    adapter = empty_store_b_adapter()
    patch = AdapterPatch(
        semantic_intent=INTENT_SHIPPING,
        operation="add_prerequisite",
        new_targets=["store-b-field-shipping"],
        new_app_action="Shipping category",
        evidence=["blocked"],
    )
    with pytest.raises(ValueError, match="refuses"):
        apply_patch(adapter, patch, _failed(), _shipping_observation())
    assert adapter.mappings == []
    assert patch.applied is False


def test_invented_patch_targets_raise():
    adapter = empty_store_b_adapter()
    patch = AdapterPatch(
        semantic_intent=INTENT_SHIPPING,
        operation="add_prerequisite",
        new_targets=["store-b-made-up"],
        new_app_action="ghost",
        evidence=["no"],
    )
    with pytest.raises(ValueError, match="Invented testid"):
        apply_patch(adapter, patch, _passed(), _shipping_observation())
