"""Pydantic Explorer: Skill step + visible UI → constrained CandidateAction."""

from __future__ import annotations

import json
from typing import Any

from .grounding import (
    CREATE_SUFFIXES,
    FINISH_SUFFIXES,
    IMAGE_SUFFIXES,
    NAME_SUFFIXES,
    NAV_PRODUCT_SUFFIXES,
    PREREQ_SUFFIXES,
    PRICE_SUFFIXES,
    default_select_value,
    elements_from_observation,
    first_suffix,
    pick_first_valid,
    product_inputs_for_step,
    require_decision_backend,
    screenshot_parts,
    summarize_elements,
    validate_explore_result,
)
from .models import AppObservation, CandidateAction, ExploreResult, SkillStep

_EXPLORER_INSTRUCTIONS = """\
You ground an app-agnostic Skill step onto the CURRENT screen.

Rules:
- You may ONLY choose target_testid values from the provided visible_elements list.
- Never invent CSS selectors or testids.
- Prefer the action that best satisfies the step intent and expected_state.
- For fill/upload/select, set action accordingly and put the value in `value` when given.
- Rank a few candidates; set `chosen` to your top pick.
- Do not use app-specific knowledge from training data that contradicts the visible list.
- If the intent is to make something publicly available / publish, prefer a control named
  like "Go Live" or "Publish" over "Listing type", "Draft", or product cards.
"""


def explore_step(
    step: SkillStep,
    elements: list[dict[str, str]] | None = None,
    *,
    observation: AppObservation | None = None,
    screenshot_bytes: bytes | None = None,
    product_values: dict[str, str] | None = None,
    exclude_testids: set[str] | None = None,
    backend: str | None = None,
) -> ExploreResult:
    """Return a constrained ExploreResult. Raises if backend missing.

    Allowed targets come from AppObservation.controls when provided.
    """
    if observation is not None:
        elements = elements_from_observation(observation)
    if elements is None:
        raise ValueError("explore_step requires visible elements or an AppObservation")
    allowed = observation if observation is not None else elements
    resolved_backend = backend or require_decision_backend()
    if resolved_backend == "mock":
        result = _explore_mock(step, elements, product_values=product_values)
    else:
        result = _explore_llm(
            step,
            elements,
            screenshot_bytes=screenshot_bytes,
            product_values=product_values,
            model=resolved_backend,
        )
    result = validate_explore_result(result, allowed)
    if exclude_testids:
        alt = pick_first_valid(
            [result.chosen, *result.candidates],
            allowed,
            exclude=exclude_testids,
        )
        if alt is None:
            raise RuntimeError(
                f"No valid explore candidate left after excluding {sorted(exclude_testids)}"
            )
        result = ExploreResult(candidates=result.candidates, chosen=alt)
    return result


def _explore_llm(
    step: SkillStep,
    elements: list[dict[str, str]],
    *,
    screenshot_bytes: bytes | None,
    product_values: dict[str, str] | None,
    model: str,
) -> ExploreResult:
    from pydantic_ai import Agent

    payload: dict[str, Any] = {
        "intent": step.intent,
        "expected_state": step.expected_state,
        "success_condition": step.success_condition,
        "required_inputs": step.required_inputs,
        "product_values": product_values or {},
        "visible_elements": json.loads(summarize_elements(elements)),
    }
    user_parts: list[object] = [
        "Ground this Skill step. Pick ONLY from visible_elements.\n",
        json.dumps(payload, indent=2),
        *screenshot_parts(screenshot_bytes),
    ]
    agent = Agent(
        model,
        name="skill_explorer",
        output_type=ExploreResult,
        instructions=_EXPLORER_INSTRUCTIONS,
    )
    from .grounding import run_agent_sync

    return run_agent_sync(agent, user_parts)


def _explore_mock(
    step: SkillStep,
    elements: list[dict[str, str]],
    *,
    product_values: dict[str, str] | None = None,
) -> ExploreResult:
    """Deterministic mock for CI — still constrained to visible testids."""
    from .metrics import record_model_call

    record_model_call()
    ids = {item.get("testid") for item in elements}
    intent = step.intent.lower()
    values = product_values or {}

    def click(testid: str, rationale: str, confidence: float = 0.7) -> CandidateAction:
        return CandidateAction(
            target_testid=testid,
            action="click",
            rationale=rationale,
            confidence=confidence,
        )

    candidates: list[CandidateAction] = []

    name_id = first_suffix(ids, NAME_SUFFIXES)
    price_id = first_suffix(ids, PRICE_SUFFIXES)
    image_id = first_suffix(ids, IMAGE_SUFFIXES)
    create_id = first_suffix(ids, CREATE_SUFFIXES)
    nav_id = first_suffix(ids, NAV_PRODUCT_SUFFIXES)
    finish_id = first_suffix(ids, FINISH_SUFFIXES)
    prereq_id = first_suffix(ids, PREREQ_SUFFIXES)
    decoy_nav = next((item for item in ids if item and "collections" in item), None)

    if "sellable" in intent or "creating" in intent or "start" in intent:
        if name_id:
            chosen = click(name_id, "form already open", 0.9)
        elif create_id:
            chosen = click(create_id, "begin listing", 0.85)
            if nav_id:
                candidates.append(click(nav_id, "product-area nav", 0.8))
        elif nav_id:
            chosen = click(nav_id, "product-area nav", 0.75)
            if decoy_nav:
                candidates.append(click(decoy_nav, "decoy collections", 0.2))
        elif decoy_nav:
            chosen = click(decoy_nav, "only nav available", 0.4)
        else:
            raise RuntimeError("Mock explorer: no nav/form targets visible")
        candidates.insert(0, chosen)
        return ExploreResult(candidates=candidates, chosen=chosen)

    if "basic product information" in intent or "details" in intent:
        name_val = values.get("name") or next(
            (v for k, v in values.items() if "name" in k.lower() or "title" in k.lower()),
            "Leather Bag",
        )
        price_val = values.get("price") or next(
            (v for k, v in values.items() if "price" in k.lower()),
            "89",
        )
        if not name_id:
            raise RuntimeError("Mock explorer: name field not visible")
        chosen = CandidateAction(
            target_testid=name_id,
            action="fill",
            value=name_val,
            rationale="fill product name",
            confidence=0.9,
        )
        candidates = [chosen]
        if price_id:
            candidates.append(
                CandidateAction(
                    target_testid=price_id,
                    action="fill",
                    value=price_val,
                    rationale="fill price",
                    confidence=0.9,
                )
            )
        return ExploreResult(candidates=candidates, chosen=chosen)

    if "image" in intent or "attach" in intent:
        if not image_id:
            raise RuntimeError("Mock explorer: image field not visible")
        image_val = values.get("image") or next(
            (v for k, v in values.items() if "image" in k.lower()),
            "",
        )
        chosen = CandidateAction(
            target_testid=image_id,
            action="upload",
            value=image_val,
            rationale="upload product image",
            confidence=0.9,
        )
        return ExploreResult(candidates=[chosen], chosen=chosen)

    if "publicly available" in intent or "publish" in intent:
        status_id = first_suffix(ids, ("-field-status",))
        if status_id:
            chosen = CandidateAction(
                target_testid=status_id,
                action="select",
                value="Live",
                rationale="set listing status to Live",
                confidence=0.85,
            )
            if finish_id:
                candidates.append(click(finish_id, "save after status", 0.8))
            return ExploreResult(candidates=[chosen, *candidates], chosen=chosen)
        if finish_id:
            chosen = click(finish_id, "make listing public", 0.85)
            return ExploreResult(candidates=[chosen], chosen=chosen)
        raise RuntimeError("Mock explorer: no publish control visible")

    if "shipping" in intent or "tax" in intent or "category" in intent or "prerequisite" in intent:
        if prereq_id:
            chosen = CandidateAction(
                target_testid=prereq_id,
                action="select",
                value=default_select_value(prereq_id),
                rationale="set visible prerequisite",
                confidence=0.9,
            )
            return ExploreResult(candidates=[chosen], chosen=chosen)
        raise RuntimeError("Mock explorer: prerequisite field not visible")

    # Generic: prefer first interactive-looking control
    for item in elements:
        testid = item.get("testid") or ""
        if "-nav-" in testid or testid.endswith(CREATE_SUFFIXES):
            chosen = click(testid, "generic navigation", 0.5)
            return ExploreResult(candidates=[chosen], chosen=chosen)
    raise RuntimeError(f"Mock explorer: cannot ground intent {step.intent!r}")
