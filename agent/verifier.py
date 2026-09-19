"""Expected vs observed. Mutates nothing. Skill stays frozen."""

from __future__ import annotations

import os

from .models import SkillStep, Verification

HYPOTHESIS = "Collections was incorrectly mapped to product creation"
ALTERNATIVE = "Inventory"
OBSERVED_FORM = "product creation form containing image, title and price inputs"
OBSERVED_COLLECTIONS = "collection management interface"

_API_KEY_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
)


def _visible_testids(hands) -> set[str]:
    return {item["testid"] for item in hands.visible_elements() if item.get("testid")}


def _heading_text(hands) -> str:
    try:
        return hands.page.locator("h1").first.inner_text().strip()
    except Exception:
        return ""


def _body_text(hands) -> str:
    try:
        return hands.page.locator("body").inner_text()
    except Exception:
        return ""


def _looks_like_collections(hands) -> bool:
    testids = _visible_testids(hands)
    heading = _heading_text(hands)
    body = _body_text(hands)
    return (
        "store-b-collections-create" in testids
        or heading == "Collections"
        or "New collection" in body
        or "This is not product creation" in body
        or "Collection management only" in body
    )


def _verify_deterministic(hands, skill_step: SkillStep) -> Verification:
    testids = _visible_testids(hands)
    name_visible = "store-b-field-name" in testids

    if name_visible:
        return Verification(
            step_intent=skill_step.intent,
            expected_state=skill_step.expected_state,
            observed_state=OBSERVED_FORM,
            matched=True,
            hypothesis=None,
            alternative=None,
        )

    if _looks_like_collections(hands):
        return Verification(
            step_intent=skill_step.intent,
            expected_state=skill_step.expected_state,
            observed_state=OBSERVED_COLLECTIONS,
            matched=False,
            hypothesis=HYPOTHESIS,
            alternative=ALTERNATIVE,
        )

    return Verification(
        step_intent=skill_step.intent,
        expected_state=skill_step.expected_state,
        observed_state="unfamiliar screen; product form not visible",
        matched=False,
        hypothesis=HYPOTHESIS,
        alternative=ALTERNATIVE,
    )


def verify_step(hands, skill_step: SkillStep) -> Verification:
    """Return a Verification. Deterministic first; LLM only if a key exists."""
    rule = _verify_deterministic(hands, skill_step)
    if not any(os.environ.get(name) for name in _API_KEY_ENV):
        return rule
    try:
        llm = _verify_with_llm(hands, skill_step)
    except Exception:
        return rule
    return llm if llm is not None else rule


def _verify_with_llm(hands, skill_step: SkillStep) -> Verification | None:
    """Optional. Always allowed to return None so the rule is the source of truth."""
    return None
