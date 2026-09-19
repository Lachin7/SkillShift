"""Skill / Adapter loaders.

Skill = WHAT. Adapter = HOW HERE (discovered memory).
Store B live path does not use keyword → testid decision tables.
Store A replay still maps cached app_action strings for Wave 5B.
"""

from __future__ import annotations

import json
from pathlib import Path

from .learner import learn_skill, load_trace
from .models import EnvironmentAdapter, Skill
from .targets import current_target

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_PATH = REPO_ROOT / "fixtures" / "traces" / "store-a.json"
SKILL_FALLBACK = REPO_ROOT / "fixtures" / "skill.json"
WRONG_ADAPTER_PATH = REPO_ROOT / "fixtures" / "adapter.wrong.json"
STORE_A_ADAPTER_PATH = REPO_ROOT / "adapters" / "store_a__publish_product.json"


def persisted_adapter_path() -> Path:
    return REPO_ROOT / current_target().adapter_file


PERSISTED_ADAPTER_PATH = REPO_ROOT / "adapters" / "store_b__publish_product.json"

INTENT_START = "start creating a new sellable item"
INTENT_DETAILS = "provide basic product information"
INTENT_IMAGE = "attach the product image"
INTENT_PUBLISH = "make the product publicly available"
INTENT_SHIPPING = "satisfy environment prerequisite: shipping category"

# Exact strings from shared/routes.md — Store A replay only.
STORE_A_TESTIDS = frozenset(
    {
        "store-a-nav-products",
        "store-a-add-product",
        "store-a-field-name",
        "store-a-field-price",
        "store-a-field-image",
        "store-a-publish",
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


def empty_adapter(app_id: str | None = None, skill_name: str = "publish_product") -> EnvironmentAdapter:
    """Cold start: no HOW HERE known yet."""
    target_id = app_id or current_target().app_id
    return EnvironmentAdapter(
        app_id=target_id,
        skill_name=skill_name,
        mappings=[],
        failure_lessons=[],
    )


def empty_store_b_adapter(skill_name: str = "publish_product") -> EnvironmentAdapter:
    """Back-compat alias for empty_adapter('store-b')."""
    return empty_adapter("store-b", skill_name)


def load_wrong_adapter() -> EnvironmentAdapter:
    """Fixture-only (unit tests). Not used by live transfer."""
    return EnvironmentAdapter.model_validate_json(
        WRONG_ADAPTER_PATH.read_text(encoding="utf-8")
    )


def load_cached_adapter(
    path: Path | None = None,
) -> EnvironmentAdapter | None:
    """Load persisted Store B adapter if it has any learned mappings."""
    adapter_file = path or persisted_adapter_path()
    if not adapter_file.is_file():
        return None
    adapter = EnvironmentAdapter.model_validate_json(
        adapter_file.read_text(encoding="utf-8")
    )
    if adapter.app_id != "store-b":
        return None
    if not adapter.mappings:
        return None
    return adapter


def load_or_empty_store_b_adapter(skill_name: str = "publish_product") -> EnvironmentAdapter:
    cached = load_cached_adapter()
    if cached is not None:
        return cached
    return empty_store_b_adapter(skill_name)


def load_store_a_adapter(path: Path | None = None) -> EnvironmentAdapter:
    """Cached Store A HOW HERE. Same Skill, original environment, no shipping."""
    adapter_file = path or STORE_A_ADAPTER_PATH
    if not adapter_file.is_file():
        raise FileNotFoundError(f"Store A adapter missing: {adapter_file}")
    adapter = EnvironmentAdapter.model_validate_json(
        adapter_file.read_text(encoding="utf-8")
    )
    if adapter.app_id != "store-a":
        raise RuntimeError(f"Expected store-a adapter, got {adapter.app_id!r}.")
    return adapter


def persist_store_a_adapter(adapter: EnvironmentAdapter, path: Path | None = None) -> Path:
    destination = path or STORE_A_ADAPTER_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(adapter.model_dump(), indent=2) + "\n", encoding="utf-8"
    )
    return destination


def _store_a_testids(app_action: str, intent: str | None) -> list[str]:
    if intent == INTENT_START:
        return ["store-a-nav-products", "store-a-add-product"]
    if intent == INTENT_DETAILS:
        return ["store-a-field-name", "store-a-field-price"]
    if intent == INTENT_IMAGE:
        return ["store-a-field-image"]
    if intent == INTENT_PUBLISH:
        return ["store-a-publish"]
    action = app_action.lower()
    if "add product" in action and "fill" not in action and "name" not in action:
        return ["store-a-nav-products", "store-a-add-product"]
    if "image" in action or "media" in action or "upload" in action:
        return ["store-a-field-image"]
    if "fill" in action or "name" in action or "price" in action:
        return ["store-a-field-name", "store-a-field-price"]
    if "publish" in action:
        return ["store-a-publish"]
    return []


def intent_to_testids(
    app_action: str,
    intent: str | None = None,
    app_id: str | None = None,
) -> list[str]:
    """Store A replay only. Store B live path uses resolved_targets."""
    if app_id != "store-a":
        raise RuntimeError(
            "intent_to_testids is Store A replay only. "
            "Store B must use StepMapping.resolved_targets from exploration."
        )
    ids = _store_a_testids(app_action, intent)
    unknown = [testid for testid in ids if testid not in STORE_A_TESTIDS]
    if unknown:
        raise RuntimeError(f"Refusing invented testids: {unknown}")
    return ids


def mapping_for_intent(adapter: EnvironmentAdapter, intent: str):
    for mapping in adapter.mappings:
        if mapping.semantic_intent == intent:
            return mapping
    return None


def upsert_mapping(adapter: EnvironmentAdapter, mapping) -> EnvironmentAdapter:
    updated = adapter.model_copy(deep=True)
    for index, existing in enumerate(updated.mappings):
        if existing.semantic_intent == mapping.semantic_intent:
            updated.mappings[index] = mapping
            return updated
    # Prerequisites insert before publish when present.
    if mapping.semantic_intent.startswith("satisfy environment prerequisite"):
        insert_at = next(
            (
                i
                for i, item in enumerate(updated.mappings)
                if item.semantic_intent == INTENT_PUBLISH
            ),
            len(updated.mappings),
        )
        updated.mappings.insert(insert_at, mapping)
        return updated
    updated.mappings.append(mapping)
    return updated
