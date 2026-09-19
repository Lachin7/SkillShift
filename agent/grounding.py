"""Shared grounding helpers: visible elements, screenshot parts, validation.

Decision logic lives in explorer / verifier / recovery.
This module never picks Store B HOW HERE answers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import (
    AppObservation,
    CandidateAction,
    ExploreResult,
    GroundingCandidate,
    SkillStep,
    StepMapping,
)

_API_KEY_MODELS: tuple[tuple[str, str], ...] = (
    ("OPENAI_API_KEY", "openai:gpt-4o"),
    ("ANTHROPIC_API_KEY", "anthropic:claude-sonnet-4-5"),
    ("GOOGLE_API_KEY", "google:gemini-3.6-flash"),
    ("GEMINI_API_KEY", "google:gemini-3.6-flash"),
    ("GROQ_API_KEY", "groq:meta-llama/llama-4-scout-17b-16e-instruct"),
)

INTENT_SHIPPING = "satisfy environment prerequisite: shipping category"

# Control *kind* suffixes — not app-specific HOW HERE.
FINISH_SUFFIXES = ("-go-live", "-launch-product", "-publish", "-save-row", "-release")
NAME_SUFFIXES = ("-field-name", "-field-title")
PRICE_SUFFIXES = ("-field-price", "-field-amount")
IMAGE_SUFFIXES = ("-field-image", "-field-photo")
PREREQ_SUFFIXES = ("-field-shipping", "-field-tax-class", "-field-category")
CREATE_SUFFIXES = ("-create-listing", "-new-row")
NAV_PRODUCT_SUFFIXES = ("-nav-inventory", "-nav-catalog", "-nav-listings")
JUDGE_MARKERS = ("-perturb-", "-judge-panel")


def first_suffix(ids: set[str] | list[str], suffixes: tuple[str, ...]) -> str | None:
    present = set(ids)
    for suffix in suffixes:
        for testid in present:
            if testid.endswith(suffix):
                return testid
    return None


def is_judge_chrome(ref: str) -> bool:
    return any(marker in ref for marker in JUDGE_MARKERS)


def is_finish_control(ref: str) -> bool:
    return any(ref.endswith(suffix) for suffix in FINISH_SUFFIXES)


def gateway_requested() -> bool:
    """Gateway must be asked for while a working direct key exists.

    A merely present PYDANTIC_AI_GATEWAY_API_KEY used to outrank GEMINI_API_KEY, so a
    gateway not enabled for the org (403) took the whole demo down.
    """
    return os.environ.get("SKILLSHIFT_USE_GATEWAY", "").lower() in {"1", "true", "yes"}


def configured_model() -> str | None:
    """Resolve model for Explorer / Verifier / Recovery.

    Priority:
    1. SKILLSHIFT_MODEL (explicit override, may be gateway/…)
    2. Gateway, when SKILLSHIFT_USE_GATEWAY=1 or no direct provider key exists
    3. Direct provider keys (OpenAI / Anthropic / Gemini / Groq)
    """
    override = os.environ.get("SKILLSHIFT_MODEL")
    if override:
        return override
    from .gateway import gateway_enabled, gateway_model

    direct = next(
        (model for env_name, model in _API_KEY_MODELS if os.environ.get(env_name)),
        None,
    )
    if gateway_enabled() and (gateway_requested() or direct is None):
        return gateway_model()
    return direct


def use_mock_llm() -> bool:
    return os.environ.get("SKILLSHIFT_MOCK_LLM", "").lower() in {"1", "true", "yes"}


def require_decision_backend() -> str:
    """Return 'mock' or a model id. Live runs must not silently hardcode Store B."""
    if use_mock_llm():
        return "mock"
    model = configured_model()
    if model:
        return model
    raise RuntimeError(
        "Store B grounding requires PYDANTIC_AI_GATEWAY_API_KEY (prize path), "
        "a direct LLM key (e.g. GEMINI_API_KEY), "
        "or SKILLSHIFT_MOCK_LLM=1 for offline/CI mocks. "
        "Hardcoded Store B decisions were removed."
    )


def visible_testid_set(elements: list[dict[str, str]] | AppObservation) -> set[str]:
    if isinstance(elements, AppObservation):
        return {item.ref for item in elements.controls if item.ref}
    return {item["testid"] for item in elements if item.get("testid")}


def elements_from_observation(observation: AppObservation) -> list[dict[str, str]]:
    """Project observation.controls into the list shape explorer already consumes."""
    rows: list[dict[str, str]] = []
    for control in observation.controls:
        if not control.ref:
            continue
        rows.append(
            {
                "testid": control.ref,
                "role": control.role,
                "name": control.name,
                "text": control.name,
                "value": control.value,
            }
        )
    return rows


def as_grounding_candidate(step: SkillStep, result: ExploreResult) -> GroundingCandidate:
    return GroundingCandidate(
        semantic_step_intent=step.intent,
        candidates=result.candidates,
        chosen=result.chosen,
    )


def summarize_elements(elements: list[dict[str, str]]) -> str:
    rows = []
    for item in elements:
        testid = item.get("testid") or ""
        if not testid:
            continue
        name = (item.get("name") or item.get("text") or "").strip().replace("\n", " ")
        role = item.get("role") or ""
        row = {"testid": testid, "role": role, "name": name[:120]}
        value = (item.get("value") or "").strip()
        if value:
            row["value"] = value[:120]
        rows.append(row)
    return json.dumps(rows, indent=2)


def validate_candidate(
    candidate: CandidateAction,
    elements: list[dict[str, str]] | AppObservation,
) -> CandidateAction:
    allowed = visible_testid_set(elements)
    if candidate.target_testid not in allowed:
        raise ValueError(
            f"Invented testid refused: {candidate.target_testid!r}. "
            f"Visible: {sorted(allowed)}"
        )
    return candidate


def validate_explore_result(
    result: ExploreResult,
    elements: list[dict[str, str]] | AppObservation,
) -> ExploreResult:
    validate_candidate(result.chosen, elements)
    valid_candidates: list[CandidateAction] = []
    for candidate in result.candidates:
        try:
            valid_candidates.append(validate_candidate(candidate, elements))
        except ValueError:
            continue
    if result.chosen not in valid_candidates:
        valid_candidates.insert(0, result.chosen)
    return ExploreResult(candidates=valid_candidates, chosen=result.chosen)


def pick_first_valid(
    candidates: list[CandidateAction],
    elements: list[dict[str, str]] | AppObservation,
    *,
    exclude: set[str] | None = None,
) -> CandidateAction | None:
    blocked = exclude or set()
    for candidate in candidates:
        if candidate.target_testid in blocked:
            continue
        try:
            return validate_candidate(candidate, elements)
        except ValueError:
            continue
    return None


def screenshot_parts(screenshot_bytes: bytes | None) -> list[Any]:
    if not screenshot_bytes:
        return []
    from pydantic_ai import BinaryContent

    return [BinaryContent(data=screenshot_bytes, media_type="image/png")]


def memory_string(trail: list[str], elements: list[dict[str, str]] | None = None) -> str:
    """Human-readable HOW HERE from a successful click/fill trail."""
    labels: list[str] = []
    by_id = {
        item.get("testid", ""): (item.get("name") or item.get("text") or item.get("testid") or "")
        for item in (elements or [])
    }
    for testid in trail:
        label = (by_id.get(testid) or testid).strip()
        if not label:
            label = testid
        # Prefer short visible names over raw testids when available.
        if label == testid:
            short = testid.replace("store-b-", "").replace("-", " ")
            labels.append(short.title())
        else:
            first_line = label.split("\n")[0].strip()
            labels.append(first_line[:48] if first_line else testid)
    return " > ".join(labels) if labels else "unknown"


def make_step_mapping(
    intent: str,
    trail: list[str],
    *,
    confidence: float,
    learned_from: str,
    elements: list[dict[str, str]] | None = None,
) -> StepMapping:
    return StepMapping(
        semantic_intent=intent,
        app_action=memory_string(trail, elements),
        confidence=confidence,
        learned_from=learned_from,  # type: ignore[arg-type]
        resolved_targets=list(trail),
        status="provisional",
        successes=1,
        failures=0,
    )


def page_text(hands) -> str:
    try:
        return hands.page.locator("body").inner_text()
    except Exception:
        return ""


def heading_text(hands) -> str:
    try:
        return hands.page.locator("h1").first.inner_text().strip()
    except Exception:
        return ""


def product_inputs_for_step(step: SkillStep, product) -> dict[str, str]:
    """Map skill required_inputs onto demo product values (values are demo constants)."""
    mapping: dict[str, str] = {}
    for key in step.required_inputs:
        lowered = key.lower()
        if lowered in {"name", "title"}:
            mapping[key] = product.name
        elif lowered == "price":
            mapping[key] = product.price
        elif lowered in {"image", "photo", "media"}:
            mapping[key] = str(product.image)
    return mapping


def default_select_value(testid: str) -> str:
    if "tax-class" in testid:
        return "Standard rate"
    if "category" in testid:
        return "General"
    if "shipping" in testid:
        return "Standard"
    return ""


def run_agent_sync(agent, user_parts):
    """Run a Pydantic AI agent from Playwright's sync context.

    Playwright owns an event loop; Agent.run_sync() cannot nest on it.
    Always execute in a dedicated thread with its own loop.
    """
    import concurrent.futures

    def _run():
        return agent.run_sync(user_parts).output

    from .metrics import record_model_call

    record_model_call()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_run).result()
