"""Recovery proposes the next grounded action after a verifier mismatch.

Does not hardcode Inventory / Go Live / shipping answers as Python constants.
Persists adapter memory after successful grounding elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .adapter import INTENT_SHIPPING, PERSISTED_ADAPTER_PATH, REPO_ROOT
from .grounding import (
    elements_from_observation,
    memory_string,
    require_decision_backend,
    screenshot_parts,
    summarize_elements,
    validate_candidate,
)
from .models import (
    AdapterPatch,
    AppObservation,
    CandidateAction,
    EnvironmentAdapter,
    Verification,
)

CACHED_ADAPTER_PATH = REPO_ROOT / "fixtures" / "adapter.cached.json"

_RECOVERY_INSTRUCTIONS = """\
A Skill step failed verification on an unfamiliar UI.

Propose the NEXT action to try. You may ONLY pick target_testid from
visible_elements. Never invent testids.

If mismatch_type is missing_prerequisite, prefer filling/selecting the
blocking control (e.g. a required dropdown mentioned in observed_state).
If wrong_navigation, pick a different nav/control not in failed_testids.
Return one CandidateAction.
"""


def propose_recovery(
    verification: Verification,
    elements: list[dict[str, str]],
    *,
    failed_testids: set[str] | None = None,
    screenshot_bytes: bytes | None = None,
    backend: str | None = None,
) -> CandidateAction:
    resolved = backend or require_decision_backend()
    failed = failed_testids or set()
    if resolved == "mock":
        action = _recover_mock(verification, elements, failed)
    else:
        action = _recover_llm(
            verification,
            elements,
            failed,
            screenshot_bytes=screenshot_bytes,
            model=resolved,
        )
    return validate_candidate(action, elements)


def _recover_llm(
    verification: Verification,
    elements: list[dict[str, str]],
    failed: set[str],
    *,
    screenshot_bytes: bytes | None,
    model: str,
) -> CandidateAction:
    from pydantic_ai import Agent

    payload: dict[str, Any] = {
        "verification": verification.model_dump(),
        "failed_testids": sorted(failed),
        "visible_elements": json.loads(summarize_elements(elements)),
    }
    user_parts: list[object] = [
        "Propose the next grounded recovery action.\n",
        json.dumps(payload, indent=2),
        *screenshot_parts(screenshot_bytes),
    ]
    agent = Agent(
        model,
        name="skill_recovery",
        output_type=CandidateAction,
        instructions=_RECOVERY_INSTRUCTIONS,
    )
    from .grounding import run_agent_sync

    return run_agent_sync(agent, user_parts)


def _recover_mock(
    verification: Verification,
    elements: list[dict[str, str]],
    failed: set[str],
) -> CandidateAction:
    from .metrics import record_model_call

    record_model_call()
    from .grounding import (
        CREATE_SUFFIXES,
        FINISH_SUFFIXES,
        NAME_SUFFIXES,
        NAV_PRODUCT_SUFFIXES,
        PREREQ_SUFFIXES,
        default_select_value,
        first_suffix,
    )

    ids = {item.get("testid") for item in elements if item.get("testid")}

    if verification.mismatch_type == "missing_prerequisite" or verification.failure_class == "missing_prerequisite":
        blob = f"{verification.observed_state} {verification.hypothesis} {verification.alternative}".lower()
        order = PREREQ_SUFFIXES
        if "tax" in blob:
            order = ("-field-tax-class", "-field-category", "-field-shipping")
        elif "categor" in blob:
            order = ("-field-category", "-field-tax-class", "-field-shipping")
        prereq = first_suffix(ids - failed, order)
        if prereq:
            return CandidateAction(
                target_testid=prereq,
                action="select",
                value=default_select_value(prereq),
                rationale="visible prerequisite control while publish blocked",
                confidence=0.9,
            )

    # Prefer unused nav / create / finish controls by kind suffix
    for suffix, rationale in (
        *[(s, "try product-area nav") for s in NAV_PRODUCT_SUFFIXES],
        *[(s, "open create listing") for s in CREATE_SUFFIXES],
        *[(s, "retry publish") for s in FINISH_SUFFIXES],
        *[(s, "return to form") for s in NAME_SUFFIXES],
    ):
        testid = first_suffix(ids - failed, (suffix,))
        if testid:
            return CandidateAction(
                target_testid=testid,
                action="click",
                rationale=rationale,
                confidence=0.75,
            )

    for item in elements:
        testid = item.get("testid") or ""
        if testid and testid not in failed:
            return CandidateAction(
                target_testid=testid,
                action="click",
                rationale="first unused visible control",
                confidence=0.4,
            )
    raise RuntimeError("Mock recovery: no remaining visible targets")


def build_recovery_patch(
    verification: Verification,
    action: CandidateAction,
    observation: AppObservation,
) -> AdapterPatch:
    """Build an AdapterPatch. Curator applies it only after the retry verifies."""
    evidence = [verification.observed_state] if verification.observed_state else []
    if verification.hypothesis:
        evidence.append(verification.hypothesis)
    elements = elements_from_observation(observation)
    app_action = memory_string([action.target_testid], elements)
    missing = (
        verification.mismatch_type == "missing_prerequisite"
        or verification.failure_class == "missing_prerequisite"
    )
    if missing:
        target = action.target_testid
        if "tax" in target:
            intent = "satisfy environment prerequisite: tax class"
        elif "category" in target:
            intent = "satisfy environment prerequisite: category"
        elif "shipping" in target:
            intent = INTENT_SHIPPING
        else:
            intent = f"satisfy environment prerequisite: {target.split('-')[-1]}"
        return AdapterPatch(
            semantic_intent=intent,
            operation="add_prerequisite",
            new_targets=[action.target_testid],
            new_app_action=app_action,
            evidence=evidence,
        )
    stale = verification.failure_class == "stale_mapping"
    if stale:
        return AdapterPatch(
            semantic_intent=verification.step_intent,
            operation="replace_mapping",
            new_targets=[action.target_testid],
            new_app_action=app_action,
            evidence=evidence,
        )
    nav_like = any(
        token in action.target_testid
        for token in ("nav", "create", "add")
    )
    return AdapterPatch(
        semantic_intent=verification.step_intent,
        operation="add_navigation_rule" if nav_like else "replace_mapping",
        new_targets=[action.target_testid],
        new_app_action=app_action,
        evidence=evidence,
    )


def append_lesson(adapter: EnvironmentAdapter, lesson: str) -> EnvironmentAdapter:
    updated = adapter.model_copy(deep=True)
    if lesson and lesson not in updated.failure_lessons:
        updated.failure_lessons.append(lesson)
    return updated


def lesson_from_verification(verification: Verification) -> str | None:
    if verification.matched:
        return None
    if verification.hypothesis:
        return verification.hypothesis
    if verification.observed_state:
        return verification.observed_state
    return None


def persist(adapter: EnvironmentAdapter, path: Path | None = None) -> Path:
    destination = path or PERSISTED_ADAPTER_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(adapter.model_dump(), indent=2) + "\n", encoding="utf-8"
    )
    return destination


def mark_cached(adapter: EnvironmentAdapter) -> EnvironmentAdapter:
    updated = adapter.model_copy(deep=True)
    for mapping in updated.mappings:
        mapping.learned_from = "cached"
        mapping.confidence = 0.95
    return updated


def persist_cached(adapter: EnvironmentAdapter) -> Path:
    cached = mark_cached(adapter)
    persist(cached, CACHED_ADAPTER_PATH)
    return CACHED_ADAPTER_PATH
