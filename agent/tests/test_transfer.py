"""Wave 3: mismatch → adapter-only rewrite → persist. Full run if the web is up."""

from __future__ import annotations

import json
from pathlib import Path

from agent.adapter import INTENT_START, load_skill, load_wrong_adapter
from agent.executor import LEATHER_BAG, WebUnavailable, execute_until, open_hands, require_web
from agent.models import Verification
from agent.recovery import CACHED_ADAPTER_PATH, persist, recover_adapter
from agent.verifier import ALTERNATIVE, HYPOTHESIS, verify_step

ROOT = Path(__file__).resolve().parents[2]
SKILL_JSON = ROOT / "fixtures" / "skill.json"
ADAPTER_PATH = ROOT / "adapters" / "store_b__publish_product.json"


def test_recovery_rewrites_only_that_mapping():
    skill_before = json.loads(SKILL_JSON.read_text(encoding="utf-8"))
    skill = load_skill()
    frozen = skill.model_dump()
    adapter = load_wrong_adapter()
    other_actions = [mapping.app_action for mapping in adapter.mappings[1:]]

    verification = Verification(
        step_intent=INTENT_START,
        expected_state=skill.steps[0].expected_state,
        observed_state="collection management interface",
        matched=False,
        hypothesis=HYPOTHESIS,
        alternative=ALTERNATIVE,
    )
    recovered = recover_adapter(verification, adapter)

    assert recovered.mappings[0].semantic_intent == INTENT_START
    assert recovered.mappings[0].app_action == "Inventory > Create Listing"
    assert recovered.mappings[0].learned_from == "recovery"
    assert [mapping.app_action for mapping in recovered.mappings[1:]] == other_actions
    assert skill.model_dump() == frozen
    assert json.loads(SKILL_JSON.read_text(encoding="utf-8")) == skill_before
    assert "Collections is collection management" in recovered.failure_lessons[0]


def test_persist_file_exists():
    adapter = load_wrong_adapter()
    verification = Verification(
        step_intent=INTENT_START,
        expected_state="a product creation form is visible",
        observed_state="collection management interface",
        matched=False,
        hypothesis=HYPOTHESIS,
        alternative=ALTERNATIVE,
    )
    path = persist(recover_adapter(verification, adapter))
    assert path.is_file()
    assert path == ADAPTER_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mappings"][0]["app_action"] == "Inventory > Create Listing"
    assert payload["mappings"][0]["learned_from"] == "recovery"


def test_verifier_mismatch_on_collections_page():
    require_web()
    skill = load_skill()
    adapter = load_wrong_adapter()
    with open_hands(allow_collections=True) as hands:
        hands.goto("/store-b")
        execute_until(hands, adapter, skill, LEATHER_BAG, stop_after_first_step=True)
        verification = verify_step(hands, skill.steps[0])
    assert verification.matched is False
    assert verification.hypothesis == HYPOTHESIS
    assert verification.alternative == ALTERNATIVE
    assert "collection" in verification.observed_state.lower()


def test_full_run_if_server_up():
    try:
        require_web()
    except WebUnavailable:
        raise
    from agent.run_transfer import main

    assert main() == 0
    live = json.loads((ROOT / "fixtures" / "live" / "dashboard-state.json").read_text())
    assert live["phase"] == "cached"
    assert CACHED_ADAPTER_PATH.is_file()
    assert all(
        mapping["learned_from"] == "cached"
        for mapping in json.loads(CACHED_ADAPTER_PATH.read_text())["mappings"]
    )
