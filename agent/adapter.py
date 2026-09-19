"""Skill / Adapter loaders and the locked Store B testid table.

Skill = WHAT. Adapter = HOW HERE. This module never invents selectors.
"""

from __future__ import annotations

import json
from pathlib import Path

from .learner import learn_skill, load_trace
from .models import EnvironmentAdapter, Skill

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = REPO_ROOT / "fixtures" / "traces" / "store-a.json"
SKILL_FALLBACK = REPO_ROOT / "fixtures" / "skill.json"
WRONG_ADAPTER_PATH = REPO_ROOT / "fixtures" / "adapter.wrong.json"
PERSISTED_ADAPTER_PATH = REPO_ROOT / "adapters" / "store_b__publish_product.json"

INTENT_START = "start creating a new sellable item"
INTENT_DETAILS = "provide basic product information"
INTENT_IMAGE = "attach the product image"
INTENT_PUBLISH = "make the product publicly available"

# Exact strings from shared/routes.md. Never invent new ones.
LOCKED_TESTIDS = frozenset(
    {
        "store-b-nav-collections",
        "store-b-collections-create",
        "store-b-nav-inventory",
        "store-b-create-listing",
        "store-b-field-name",
        "store-b-field-price",
        "store-b-field-image",
        "store-b-go-live",
    }
)


def load_skill() -> Skill:
    """Learn from the recorded Store A trace, or fall back to fixtures/skill.json."""
    if TRACE_PATH.is_file():
        try:
            return learn_skill(load_trace(TRACE_PATH))
        except (OSError, ValueError, KeyError):
            pass
    return Skill.model_validate_json(SKILL_FALLBACK.read_text(encoding="utf-8"))


def load_wrong_adapter() -> EnvironmentAdapter:
    return EnvironmentAdapter.model_validate_json(
        WRONG_ADAPTER_PATH.read_text(encoding="utf-8")
    )


def load_cached_adapter(
    path: Path | None = None,
) -> EnvironmentAdapter | None:
    """Load the persisted Store B adapter if it was recovered or cached."""
    adapter_file = path or PERSISTED_ADAPTER_PATH
    if not adapter_file.is_file():
        return None
    adapter = EnvironmentAdapter.model_validate_json(
        adapter_file.read_text(encoding="utf-8")
    )
    if any(mapping.learned_from in {"cached", "recovery"} for mapping in adapter.mappings):
        return adapter
    return None


def intent_to_testids(app_action: str, intent: str | None = None) -> list[str]:
    """Map an adapter HOW HERE string onto locked Store B testids."""
    action = app_action.lower()
    if "collections" in action:
        ids = ["store-b-nav-collections", "store-b-collections-create"]
    elif "inventory" in action:
        ids = ["store-b-nav-inventory", "store-b-create-listing"]
    elif "go live" in action:
        ids = ["store-b-go-live"]
    elif intent == INTENT_IMAGE or "image" in action or "upload" in action:
        ids = ["store-b-field-image"]
    elif (
        intent == INTENT_DETAILS
        or "fill" in action
        or "title" in action
        or "name" in action
        or "price" in action
    ):
        ids = ["store-b-field-name", "store-b-field-price"]
    else:
        ids = []

    unknown = [testid for testid in ids if testid not in LOCKED_TESTIDS]
    if unknown:
        raise RuntimeError(f"Refusing invented testids: {unknown}")
    return ids


def mapping_for_intent(adapter: EnvironmentAdapter, intent: str):
    for mapping in adapter.mappings:
        if mapping.semantic_intent == intent:
            return mapping
    return None
