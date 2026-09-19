"""Transfer loop: ground frozen Skill on Store B via Explore → Verify → Recover.

Cold start: empty adapter. Shipping prerequisite is discovered from a real blocker.
Second run: cached resolved_targets, no rediscovery.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.adapter import (  # noqa: E402
    INTENT_PUBLISH,
    INTENT_SHIPPING,
    INTENT_START,
    empty_adapter,
    empty_store_b_adapter,
    load_cached_adapter,
    load_skill,
    mapping_for_intent,
)
from agent.executor import (  # noqa: E402
    BLUE_SNEAKER,
    LEATHER_BAG,
    demo_hold,
    demo_pause,
    live_products_path,
    open_hands,
)
from agent.targets import current_target  # noqa: E402
from agent.grounding import require_decision_backend  # noqa: E402
from agent.models import EnvironmentAdapter  # noqa: E402
from agent.recovery import mark_cached, persist, persist_cached  # noqa: E402
from agent.metrics import format_reuse_gain, snapshot, start_run, write_run_metrics  # noqa: E402
from agent.transfer_loop import (  # noqa: E402
    current_loop_trace,
    reset_loop_trace,
    run_store_b_transfer,
    set_dashboard_hook,
)

LIVE_DASHBOARD = ROOT / "fixtures" / "live" / "dashboard-state.json"

SKILL_CARD = {
    "name": "publish_product",
    "title": "Publish Product",
    "steps": ["Create item", "Add details", "Add image", "Publish"],
}


def _log(message: str) -> None:
    print(message, flush=True)


def _dashboard_from_adapter(
    phase: str,
    adapter: EnvironmentAdapter,
    *,
    unseen: bool,
    message: str,
    metrics: dict | None = None,
) -> dict:
    mappings = []
    for item in adapter.mappings:
        label = item.semantic_intent.split(":")[-1].strip()
        if item.semantic_intent == INTENT_START:
            label = "Create item"
        elif "shipping" in item.semantic_intent:
            label = "Shipping"
        elif item.semantic_intent == INTENT_PUBLISH:
            label = "Publish"
        mappings.append(
            {
                "label": label,
                "app_action": item.app_action,
                "semantic_intent": item.semantic_intent,
                "highlight": "error" if phase == "mismatch" and "shipping" in item.semantic_intent else None,
            }
        )
    return {
        "phase": phase,
        "skill": SKILL_CARD,
        "app": {
            "app_id": current_target().app_id,
            "label": current_target().label,
            "unseen": unseen,
        },
        "adapter": {
            "skill_name": adapter.skill_name,
            "mappings": mappings,
            "failure_lessons": adapter.failure_lessons,
        },
        "status": {
            "skill_loaded": True,
            "adapter_learned": bool(adapter.mappings),
            "product_live": phase in {"recovered", "cached"},
            "message": message,
        },
        "loop_trace": current_loop_trace(),
        "metrics": metrics or {},
    }


def write_dashboard(
    phase: str,
    adapter: EnvironmentAdapter,
    *,
    unseen: bool,
    message: str,
    metrics: dict | None = None,
) -> Path:
    LIVE_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    payload = _dashboard_from_adapter(
        phase, adapter, unseen=unseen, message=message, metrics=metrics
    )
    LIVE_DASHBOARD.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return LIVE_DASHBOARD


def main() -> int:
    require_decision_backend()
    skill = load_skill()
    if len(skill.steps) != 4:
        raise RuntimeError("Skill must stay four frozen intents.")

    target = current_target()
    cached = load_cached_adapter()
    cold = cached is None or not cached.mappings or cached.app_id != target.app_id
    adapter = empty_adapter(target.app_id, skill.name) if cold else cached

    _log("Skill loaded: publish_product")
    _log(f"Environment: {target.app_id}" + (" unseen" if cold else " (adapter cached)"))
    if cold:
        _log("Adapter: empty — grounding via Explorer / Verifier / Recovery")
    else:
        start = mapping_for_intent(adapter, INTENT_START)
        _log(f"Adapter cache: {len(adapter.mappings)} mappings")
        if start:
            _log(f"  start → {start.app_action}")

    products_file = live_products_path()
    products_file.parent.mkdir(parents=True, exist_ok=True)
    products_file.write_text("[]\n", encoding="utf-8")
    reset_loop_trace()
    set_dashboard_hook(
        lambda phase, current, msg: write_dashboard(
            phase if phase in {"mismatch", "recovered", "cached"} else "mismatch",
            current,
            unseen=True,
            message=msg,
        )
    )

    with open_hands() as hands:
        if cold:
            write_dashboard(
                "exploring",
                adapter,
                unseen=True,
                message="Grounding Skill steps on Store B from visible UI.",
            )
            _log("First run — discover HOW HERE")
            start_run(LEATHER_BAG.name)
            adapter, card = run_store_b_transfer(
                hands, skill, LEATHER_BAG, adapter, persist_adapter=True
            )
            first_metrics = snapshot()
            shipping = mapping_for_intent(adapter, INTENT_SHIPPING)
            msg = "Adapter learned from exploration/recovery."
            if shipping:
                msg = (
                    "Missing shipping prerequisite discovered and patched. "
                    f"Remembered: {shipping.app_action}"
                )
            write_dashboard("recovered", adapter, unseen=True, message=msg)
            _log("Product live (Leather Bag)")
            _log(card.replace("\n", " | "))
            persist_cached(mark_cached(adapter))
            demo_hold()

            _log("Second run — cached adapter")
            hands.goto(target.path)
            demo_pause()
            start_run(BLUE_SNEAKER.name)
            adapter2, card2 = run_store_b_transfer(
                hands, skill, BLUE_SNEAKER, adapter, persist_adapter=True
            )
            second_metrics = snapshot()
            _log(format_reuse_gain(first_metrics, second_metrics))
            write_run_metrics(first_metrics, second_metrics)
            write_dashboard(
                "cached",
                adapter2,
                unseen=False,
                message="Previously learned mappings reused. Exploration skipped where cached.",
                metrics={
                    "first": first_metrics.model_dump(),
                    "second": second_metrics.model_dump(),
                    "reuse_gain": {
                        "actions": first_metrics.actions - second_metrics.actions,
                        "model_calls": first_metrics.model_calls - second_metrics.model_calls,
                        "recoveries": first_metrics.recoveries - second_metrics.recoveries,
                    },
                },
            )
            _log("Blue Sneaker live")
            _log(card2.replace("\n", " | "))
            demo_hold()
        else:
            _log("Cached run only")
            adapter2, card2 = run_store_b_transfer(
                hands, skill, BLUE_SNEAKER, adapter, persist_adapter=True
            )
            write_dashboard(
                "cached",
                adapter2,
                unseen=False,
                message="Cached Store B adapter. Product live.",
            )
            _log(card2.replace("\n", " | "))
            demo_hold()

    return 0


if __name__ == "__main__":
    # Default offline CI to mock unless a real key is present.
    if not os.environ.get("SKILLSHIFT_MOCK_LLM") and not any(
        os.environ.get(k)
        for k in (
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GROQ_API_KEY",
        )
    ):
        # Live CLI without keys: fail clearly via require_decision_backend in main.
        pass
    raise SystemExit(main())
