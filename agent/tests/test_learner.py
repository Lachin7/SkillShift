"""Wave 1: demonstration trace → app-agnostic Skill. No API key required."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.learner import (  # noqa: E402
    PUBLISH_PRODUCT_INTENTS,
    learn_skill,
    load_trace,
)
from agent.models import (  # noqa: E402
    EnvironmentAdapter,
    Skill,
    SkillStep,
    StepMapping,
    TraceEvent,
    Verification,
)

FIXTURES = ROOT / "fixtures"
ADAPTERS = ROOT / "adapters"
LOCKED_INTENTS = [
    "start creating a new sellable item",
    "provide basic product information",
    "attach the product image",
    "make the product publicly available",
]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_models_load():
    Skill.model_validate(_load(FIXTURES / "skill.json"))
    TraceEvent.model_validate(_load(FIXTURES / "trace.store-a.json")[0])
    EnvironmentAdapter.model_validate(_load(FIXTURES / "adapter.wrong.json"))
    EnvironmentAdapter.model_validate(_load(FIXTURES / "adapter.recovered.json"))
    EnvironmentAdapter.model_validate(_load(FIXTURES / "adapter.cached.json"))
    Verification.model_validate(_load(FIXTURES / "verification.mismatch.json"))
    StepMapping.model_validate(
        {
            "semantic_intent": LOCKED_INTENTS[0],
            "app_action": "Inventory > Create Listing",
            "confidence": 0.9,
            "learned_from": "recovery",
        }
    )
    SkillStep.model_validate(_load(FIXTURES / "skill.json")["steps"][0])


def test_learner_store_a_trace_is_publish_product():
    events = load_trace(FIXTURES / "trace.store-a.json")
    skill = learn_skill(events)
    assert skill.name == "publish_product"
    for step in skill.steps:
        assert "click" not in step.intent.lower()
    assert [step.intent for step in skill.steps] == LOCKED_INTENTS
    assert tuple(step.intent for step in skill.steps) == PUBLISH_PRODUCT_INTENTS
    assert skill.inputs == ["name", "price", "image"]


def test_skill_is_separate_from_adapter():
    skill = Skill.model_validate(_load(FIXTURES / "skill.json"))
    adapter = EnvironmentAdapter.model_validate(
        _load(ADAPTERS / "store_b__publish_product.json")
    )
    assert adapter.skill_name == skill.name
    assert "steps" in Skill.model_fields
    assert "mappings" in EnvironmentAdapter.model_fields
    skill_keys = set(skill.model_dump())
    assert skill_keys.isdisjoint({"app_id", "mappings", "failure_lessons"})
    # Cold-start adapter may be empty; fixture wrong/cached still carry learned_from.
    if adapter.mappings:
        assert adapter.mappings[0].learned_from in {"exploration", "recovery", "cached"}


def test_wrong_adapter_is_collections_trap():
    adapter = EnvironmentAdapter.model_validate(_load(FIXTURES / "adapter.wrong.json"))
    create = adapter.mappings[0]
    assert create.semantic_intent == LOCKED_INTENTS[0]
    assert "Collections" in create.app_action
    assert create.learned_from == "exploration"


def test_cached_adapter_skips_exploration():
    adapter = EnvironmentAdapter.model_validate(_load(FIXTURES / "adapter.cached.json"))
    assert all(mapping.learned_from == "cached" for mapping in adapter.mappings)


def test_mismatch_verification():
    verification = Verification.model_validate(
        _load(FIXTURES / "verification.mismatch.json")
    )
    assert verification.matched is False
    assert verification.alternative == "Inventory"
    assert "collection" in verification.observed_state.lower()


def test_persisted_store_b_adapter_cold_or_learned():
    adapter = EnvironmentAdapter.model_validate(
        _load(ADAPTERS / "store_b__publish_product.json")
    )
    assert adapter.app_id == "store-b"
    assert adapter.skill_name == "publish_product"
    # R1: file starts empty; after a transfer run it holds discovered mappings.
    assert isinstance(adapter.mappings, list)
