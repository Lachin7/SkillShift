"""Wave 3 transfer loop: fail on Collections, rewrite Adapter, persist, second run.

Usage (from repo root, Next.js already running):
  SKILLSHIFT_WEB_URL=http://localhost:3010 python -m agent.run_transfer
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.adapter import (  # noqa: E402
    INTENT_START,
    load_cached_adapter,
    load_skill,
    load_wrong_adapter,
    mapping_for_intent,
)
from agent.executor import (  # noqa: E402
    BLUE_SNEAKER,
    LEATHER_BAG,
    execute_until,
    open_hands,
)
from agent.recovery import persist, persist_cached, recover_adapter  # noqa: E402
from agent.verifier import verify_step  # noqa: E402

LIVE_DASHBOARD = ROOT / "fixtures" / "live" / "dashboard-state.json"

SKILL_CARD = {
    "name": "publish_product",
    "title": "Publish Product",
    "steps": ["Create item", "Add details", "Add image", "Publish"],
}


def _dashboard_payload(phase: str, create_action: str, *, unseen: bool) -> dict:
    mismatch = phase == "mismatch"
    recovered = phase == "recovered"
    cached = phase == "cached"
    if mismatch:
        message = (
            "ADAPTER MISMATCH DETECTED — Collections is not product creation. "
            "Alternative: Inventory"
        )
    elif recovered:
        message = "Adapter recovered. Product live."
    else:
        message = "Adapter found. Exploration skipped. Product live."
    return {
        "phase": phase,
        "skill": SKILL_CARD,
        "app": {
            "app_id": "store-b",
            "label": "Store B",
            "unseen": unseen,
        },
        "adapter": {
            "skill_name": "publish_product",
            "mappings": [
                {
                    "label": "Create item",
                    "app_action": create_action,
                    "semantic_intent": INTENT_START,
                    "highlight": "error" if mismatch else None,
                },
                {
                    "label": "Publish",
                    "app_action": "Go Live",
                    "semantic_intent": "make the product publicly available",
                    "highlight": None,
                },
            ],
        },
        "status": {
            "skill_loaded": True,
            "adapter_learned": recovered or cached,
            "product_live": recovered or cached,
            "message": message,
        },
    }


def write_dashboard_state(phase: str, create_action: str, *, unseen: bool) -> Path:
    LIVE_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    payload = _dashboard_payload(phase, create_action, unseen=unseen)
    LIVE_DASHBOARD.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return LIVE_DASHBOARD


def _log(message: str) -> None:
    print(message, flush=True)


def main() -> int:
    skill = load_skill()
    wrong = load_wrong_adapter()
    guess = mapping_for_intent(wrong, INTENT_START)
    guess_action = guess.app_action if guess else "Collections > Create"

    _log("Skill loaded: publish_product")
    _log("Environment: store-b unseen")
    _log(f"Adapter guess: {guess_action}")

    with open_hands(allow_collections=True) as hands:
        hands.goto("/store-b")
        execute_until(
            hands,
            wrong,
            skill,
            LEATHER_BAG,
            stop_after_first_step=True,
        )
        verification = verify_step(hands, skill.steps[0])
        if verification.matched:
            raise RuntimeError("Expected a Collections mismatch on the first attempt.")

        _log("ADAPTER MISMATCH DETECTED")
        _log(f"  Hypothesis: {verification.hypothesis}")
        _log(f"  Alternative: {verification.alternative}")
        write_dashboard_state("mismatch", guess_action, unseen=True)

        recovered = recover_adapter(verification, wrong)
        persist(recovered)
        updated = mapping_for_intent(recovered, INTENT_START)
        _log(f"Adapter updated: {updated.app_action if updated else 'Inventory > Create Listing'}")

        hands.allow_collections = False
        card = execute_until(hands, recovered, skill, LEATHER_BAG)
        _log("Product live (Leather Bag)")
        if card:
            _log(card.replace("\n", " | "))
        write_dashboard_state(
            "recovered",
            updated.app_action if updated else "Inventory > Create Listing",
            unseen=True,
        )

    cached = load_cached_adapter()
    if cached is None:
        raise RuntimeError("Persisted adapter missing after recovery.")
    persist_cached(cached)

    _log("Second run")
    _log("  Adapter found")
    _log("Exploration skipped")
    with open_hands(allow_collections=False) as hands:
        hands.goto("/store-b")
        card = execute_until(hands, cached, skill, BLUE_SNEAKER)
        _log("Blue Sneaker live")
        if card:
            _log(card.replace("\n", " | "))
    write_dashboard_state("cached", "Inventory > Create Listing", unseen=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
