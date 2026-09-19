"""Adapter-only mutation after a verifier mismatch.

The Skill is never edited. Only the matching StepMapping is rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path

from .adapter import PERSISTED_ADAPTER_PATH, REPO_ROOT
from .models import EnvironmentAdapter, Verification

RECOVERED_ACTION = "Inventory > Create Listing"
FAILURE_LESSON = "Collections is collection management, not product creation"
CACHED_ADAPTER_PATH = REPO_ROOT / "fixtures" / "adapter.cached.json"


def recover_adapter(
    verification: Verification, adapter: EnvironmentAdapter
) -> EnvironmentAdapter:
    """Rewrite only the mapping whose semantic_intent == verification.step_intent."""
    updated = adapter.model_copy(deep=True)
    for mapping in updated.mappings:
        if mapping.semantic_intent == verification.step_intent:
            mapping.app_action = RECOVERED_ACTION
            mapping.learned_from = "recovery"
            mapping.confidence = 0.9
            break
    if FAILURE_LESSON not in updated.failure_lessons:
        updated.failure_lessons.append(FAILURE_LESSON)
    return updated


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
