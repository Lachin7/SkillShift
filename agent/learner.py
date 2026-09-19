"""Demonstration trace → app-agnostic Skill.

A recorded Store A walkthrough is advice, not a replay script (UI-Mate).
The learner throws away app-specific clicks and emits the frozen Skill WHAT.

If an LLM API key is present, a multimodal Pydantic AI agent infers the Skill
(screenshots are attached when the placeholder paths exist on disk). Otherwise
a deterministic mapping from the Store A trace produces `publish_product` with
the exact intents in shared/routes.md.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Skill, SkillStep, TraceEvent

# Exact strings from shared/routes.md — both agents use these.
INTENT_START = "start creating a new sellable item"
INTENT_DETAILS = "provide basic product information"
INTENT_IMAGE = "attach the product image"
INTENT_PUBLISH = "make the product publicly available"

PUBLISH_PRODUCT_INTENTS = (
    INTENT_START,
    INTENT_DETAILS,
    INTENT_IMAGE,
    INTENT_PUBLISH,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

_API_KEY_MODELS: tuple[tuple[str, str], ...] = (
    ("OPENAI_API_KEY", "openai:gpt-4o"),
    ("ANTHROPIC_API_KEY", "anthropic:claude-sonnet-4-5"),
    ("GOOGLE_API_KEY", "google-gla:gemini-2.0-flash"),
    ("GEMINI_API_KEY", "google-gla:gemini-2.0-flash"),
    ("GROQ_API_KEY", "groq:meta-llama/llama-4-scout-17b-16e-instruct"),
)

_LEARNER_INSTRUCTIONS = """\
You convert a human demonstration trace into an app-agnostic Skill.

The demonstration is ADVICE, not a script to replay. Drop every app-specific
click, button label, and nav item. Intents must never contain the word "click"
and must never name UI chrome such as "Products" or "Publish".

This locked demo skill is publish_product. Use these exact step intents, in order:
1. start creating a new sellable item
2. provide basic product information
3. attach the product image
4. make the product publicly available

Inputs are always name, price, image.
"""


def _publish_product_steps() -> dict[str, SkillStep]:
    return {
        INTENT_START: SkillStep(
            intent=INTENT_START,
            required_inputs=[],
            expected_state="a product creation form is visible",
            success_condition="a form with name, price, and image fields is on screen",
        ),
        INTENT_DETAILS: SkillStep(
            intent=INTENT_DETAILS,
            required_inputs=["name", "price"],
            expected_state="name and price are populated",
            success_condition="the form shows the provided name and price",
        ),
        INTENT_IMAGE: SkillStep(
            intent=INTENT_IMAGE,
            required_inputs=["image"],
            expected_state="product image preview is visible",
            success_condition="an image preview appears on the listing",
        ),
        INTENT_PUBLISH: SkillStep(
            intent=INTENT_PUBLISH,
            required_inputs=[],
            expected_state="product is published",
            success_condition="a public product card is visible",
        ),
    }


def publish_product_skill() -> Skill:
    """Frozen Wave 1 Skill: WHAT, never HOW HERE."""
    templates = _publish_product_steps()
    return Skill(
        name="publish_product",
        goal="Create and publish a sellable product listing",
        inputs=["name", "price", "image"],
        steps=[templates[intent] for intent in PUBLISH_PRODUCT_INTENTS],
        final_success_condition=(
            "a sellable product card exists with the given name, price, and image"
        ),
    )


def load_trace(path: str | Path) -> list[TraceEvent]:
    """Load a recorder JSON list of before/action/after events."""
    raw = Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    return [TraceEvent.model_validate(item) for item in payload]


def _resolve_media(path_str: str) -> Path | None:
    candidate = Path(path_str)
    if candidate.is_file():
        return candidate
    rooted = _REPO_ROOT / path_str
    if rooted.is_file():
        return rooted
    return None


def _intent_for_event(event: TraceEvent) -> str:
    """Map a Store A (or similar) recorder event onto a semantic intent."""
    target = event.target.lower()
    if event.action == "upload":
        return INTENT_IMAGE
    if event.action == "fill":
        if "image" in target or "media" in target or "photo" in target:
            return INTENT_IMAGE
        return INTENT_DETAILS
    # click
    if any(token in target for token in ("publish", "go live", "make live")):
        return INTENT_PUBLISH
    return INTENT_START


def _learn_deterministically(events: list[TraceEvent]) -> Skill:
    """Store A trace → publish_product with the exact routes.md intents.

    Walks the recorder events so app-specific clicks (Add Product, Publish)
    become semantic intents. The Skill itself is frozen: four locked steps,
    zero click-the-button wording.
    """
    templates = _publish_product_steps()
    mapped: list[str] = []
    for event in events:
        intent = _intent_for_event(event)
        if intent not in mapped:
            mapped.append(intent)

    # Store A maps onto the four locked intents; always emit them in routes.md order.
    if tuple(mapped) != PUBLISH_PRODUCT_INTENTS:
        mapped = list(PUBLISH_PRODUCT_INTENTS)
    steps = [templates[intent] for intent in mapped]
    return Skill(
        name="publish_product",
        goal="Create and publish a sellable product listing",
        inputs=["name", "price", "image"],
        steps=steps,
        final_success_condition=(
            "a sellable product card exists with the given name, price, and image"
        ),
    )


def _configured_model() -> str | None:
    override = os.environ.get("SKILLSHIFT_MODEL")
    if override:
        return override
    for env_name, model in _API_KEY_MODELS:
        if os.environ.get(env_name):
            return model
    return None


def _has_click_wording(skill: Skill) -> bool:
    return any("click" in step.intent.lower() for step in skill.steps)


def _matches_locked_intents(skill: Skill) -> bool:
    return tuple(step.intent for step in skill.steps) == PUBLISH_PRODUCT_INTENTS


def _learn_with_pydantic_ai(events: list[TraceEvent], model: str) -> Skill:
    from pydantic_ai import Agent, BinaryContent

    user_parts: list[object] = [
        "Demonstration trace (JSON). Infer the Skill; do not copy button labels.\n",
        json.dumps([event.model_dump() for event in events], indent=2),
    ]
    attached: set[Path] = set()
    for event in events:
        for path_str in (event.before, event.after):
            media = _resolve_media(path_str)
            if media is None or media in attached:
                continue
            attached.add(media)
            user_parts.append(BinaryContent.from_path(media))

    agent = Agent(
        model,
        name="skill_learner",
        output_type=Skill,
        instructions=_LEARNER_INSTRUCTIONS,
    )
    result = agent.run_sync(user_parts)
    return result.output


def learn_skill(events: list[TraceEvent]) -> Skill:
    """Turn a demonstration trace into an app-agnostic Skill.

    Prefers a multimodal Pydantic AI agent when an API key is in the
    environment. Always falls back to the deterministic Store A mapping
    so Wave 1 works offline.
    """
    model = _configured_model()
    if model:
        try:
            skill = _learn_with_pydantic_ai(events, model)
            if not _has_click_wording(skill) and _matches_locked_intents(skill):
                return skill
        except Exception:
            pass
    return _learn_deterministically(events)
