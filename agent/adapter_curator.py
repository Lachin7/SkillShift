"""Apply AdapterPatch only after a retry verifies. Skill never mutates."""

from __future__ import annotations

from .adapter import INTENT_PUBLISH, INTENT_SHIPPING, mapping_for_intent, upsert_mapping
from .grounding import validate_candidate
from .models import (
    AdapterPatch,
    AppObservation,
    CandidateAction,
    EnvironmentAdapter,
    StepMapping,
    Verification,
    VerificationResult,
)


def validate_patch_targets(
    patch: AdapterPatch, observation: AppObservation | None
) -> None:
    if observation is None:
        return
    for target in patch.new_targets:
        validate_candidate(
            CandidateAction(target_testid=target, action="click"),
            observation,
        )


def verification_passed(verification: Verification | VerificationResult) -> bool:
    if isinstance(verification, VerificationResult):
        return verification.passed
    return verification.matched


def apply_patch(
    adapter: EnvironmentAdapter,
    patch: AdapterPatch,
    verification: Verification | VerificationResult,
    observation: AppObservation | None = None,
) -> EnvironmentAdapter:
    """Authoritative observation > verified rule > provisional > model guess."""
    if not verification_passed(verification):
        raise ValueError("Curator refuses to apply patch when verification failed")
    validate_patch_targets(patch, observation)

    mapping = StepMapping(
        semantic_intent=patch.semantic_intent,
        app_action=patch.new_app_action,
        confidence=0.9,
        learned_from="recovery",
        resolved_targets=list(patch.new_targets),
        status="provisional",
        successes=1,
        failures=0,
    )

    if patch.operation == "deprecate_rule":
        updated = adapter.model_copy(deep=True)
        for item in updated.mappings:
            if item.semantic_intent == patch.semantic_intent:
                item.status = "deprecated"
                item.failures += 1
        patch.applied = True
        return updated

    if patch.operation == "add_navigation_rule":
        existing = mapping_for_intent(adapter, patch.semantic_intent)
        if existing is not None:
            targets = list(
                dict.fromkeys([*existing.resolved_targets, *patch.new_targets])
            )
            mapping = existing.model_copy(
                update={
                    "resolved_targets": targets,
                    "app_action": patch.new_app_action or existing.app_action,
                    "learned_from": "recovery",
                    "status": "provisional",
                    "successes": max(existing.successes, 1),
                }
            )

    if patch.operation == "replace_mapping":
        existing = mapping_for_intent(adapter, patch.semantic_intent)
        if existing is not None:
            mapping = mapping.model_copy(
                update={
                    "status": "provisional",
                    "successes": 1,
                }
            )
        updated = upsert_mapping(adapter, mapping)
        updated = updated.model_copy(deep=True)
        updated.adapter_version = int(getattr(adapter, "adapter_version", 1) or 1) + 1
        patch.applied = True
        return updated

    updated = upsert_mapping(adapter, mapping)
    if patch.operation == "add_prerequisite":
        updated = updated.model_copy(deep=True)
        updated.adapter_version = int(getattr(adapter, "adapter_version", 1) or 1) + 1
    patch.applied = True
    return updated


def mark_mapping_success(
    adapter: EnvironmentAdapter,
    intent: str,
    *,
    reusable: bool = False,
) -> EnvironmentAdapter:
    updated = adapter.model_copy(deep=True)
    for item in updated.mappings:
        if item.semantic_intent != intent:
            continue
        item.successes += 1
        if reusable or item.successes >= 2:
            item.status = "reusable"
        elif item.status == "candidate":
            item.status = "provisional"
    return updated


def shipping_intent() -> str:
    return INTENT_SHIPPING


def publish_intent() -> str:
    return INTENT_PUBLISH
