"""Same-environment replay: frozen Skill + cached Store A adapter.

Usage (from repo root, Next.js already running):
  SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 python -m agent.run_replay_a
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.adapter import (  # noqa: E402
    INTENT_DETAILS,
    INTENT_IMAGE,
    INTENT_PUBLISH,
    INTENT_START,
    load_skill,
    load_store_a_adapter,
    mapping_for_intent,
)
from agent.executor import CERAMIC_MUG, demo_hold, demo_pause, execute_store_a, open_hands  # noqa: E402

LIVE_DASHBOARD = ROOT / "fixtures" / "live" / "dashboard-state.json"

SKILL_CARD = {
    "name": "publish_product",
    "title": "Publish Product",
    "steps": ["Create item", "Add details", "Add image", "Publish"],
}


def _dashboard_payload(adapter) -> dict:
    start = mapping_for_intent(adapter, INTENT_START)
    details = mapping_for_intent(adapter, INTENT_DETAILS)
    image = mapping_for_intent(adapter, INTENT_IMAGE)
    publish = mapping_for_intent(adapter, INTENT_PUBLISH)
    return {
        "phase": "cached",
        "skill": SKILL_CARD,
        "app": {
            "app_id": "store-a",
            "label": "Store A",
            "unseen": False,
        },
        "adapter": {
            "skill_name": "publish_product",
            "mappings": [
                {
                    "label": "Create item",
                    "app_action": start.app_action if start else "Products > Add Product",
                    "semantic_intent": INTENT_START,
                    "highlight": None,
                },
                {
                    "label": "Add details",
                    "app_action": details.app_action if details else "Fill name and price",
                    "semantic_intent": INTENT_DETAILS,
                    "highlight": None,
                },
                {
                    "label": "Add image",
                    "app_action": image.app_action if image else "Media > Upload image",
                    "semantic_intent": INTENT_IMAGE,
                    "highlight": None,
                },
                {
                    "label": "Publish",
                    "app_action": publish.app_action if publish else "Publish",
                    "semantic_intent": INTENT_PUBLISH,
                    "highlight": None,
                },
            ],
        },
        "status": {
            "skill_loaded": True,
            "adapter_learned": True,
            "product_live": True,
            "message": "Same environment. Adapter found. Exploration skipped.",
        },
    }


def write_dashboard_state(adapter) -> Path:
    LIVE_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    LIVE_DASHBOARD.write_text(
        json.dumps(_dashboard_payload(adapter), indent=2) + "\n", encoding="utf-8"
    )
    return LIVE_DASHBOARD


def _log(message: str) -> None:
    print(message, flush=True)


def main() -> int:
    skill = load_skill()
    if len(skill.steps) != 4:
        raise RuntimeError("Skill must stay four frozen intents.")
    adapter = load_store_a_adapter()

    _log("Skill loaded: publish_product")
    _log("Environment: store-a (same)")
    _log("Adapter found")
    _log("Same environment. Exploration skipped.")
    write_dashboard_state(adapter)

    with open_hands() as hands:
        hands.goto("/store-a")
        demo_pause()
        _log("WATCH: Products → Add Product → Publish")
        card = execute_store_a(hands, adapter, skill, CERAMIC_MUG)
        _log("Product live (Ceramic Mug)")
        if card:
            _log(card.replace("\n", " | "))
        write_dashboard_state(adapter)
        _log("WATCH: product card — holding")
        demo_hold()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
