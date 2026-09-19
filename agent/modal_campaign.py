"""Optional Wave 6B campaign Modal scoring (R2). Not used by R1 transfer loop."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .adapter import INTENT_SHIPPING
from .models import EnvironmentAdapter, StepMapping, Verification
from .recovery import persist

REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ACTION = "Create Listing > Campaign code LAUNCH10"
INTENT_CAMPAIGN = "satisfy environment prerequisite: campaign promo code"
CAMPAIGN_LESSON = "Store B requires campaign code LAUNCH10 before Go Live"


def recover_campaign(
    verification: Verification,
    adapter: EnvironmentAdapter,
    winning_action: str | None = None,
) -> EnvironmentAdapter:
    """R2 helper: insert campaign mapping. Not used by R1 live transfer."""
    _ = verification
    action = winning_action or CAMPAIGN_ACTION
    updated = adapter.model_copy(deep=True)
    if not any(mapping.semantic_intent == INTENT_CAMPAIGN for mapping in updated.mappings):
        extra = StepMapping(
            semantic_intent=INTENT_CAMPAIGN,
            app_action=action,
            confidence=0.9,
            learned_from="recovery",
        )
        insert_at = next(
            (
                index
                for index, mapping in enumerate(updated.mappings)
                if "publicly available" in mapping.semantic_intent
            ),
            len(updated.mappings),
        )
        updated.mappings.insert(insert_at, extra)
    if CAMPAIGN_LESSON not in updated.failure_lessons:
        updated.failure_lessons.append(CAMPAIGN_LESSON)
    return updated


def apply_campaign_winner(
    verification: Verification,
    adapter: EnvironmentAdapter,
    winner_id: str,
) -> EnvironmentAdapter:
    if winner_id != "A":
        winner_id = "A"
    return recover_campaign(verification, adapter, winning_action=CAMPAIGN_ACTION)


def _import_modal_sdk():
    try:
        import modal as sdk

        if hasattr(sdk, "App"):
            return sdk
    except ImportError:
        return None
    return None


def _modal_ready() -> bool:
    if os.environ.get("SKILLSHIFT_FORCE_LOCAL_MODAL", "").lower() in {"1", "true", "yes"}:
        return False
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("SKILLSHIFT_USE_MODAL") != "1":
        return False
    if _import_modal_sdk() is None:
        return False
    if os.environ.get("MODAL_TOKEN_ID"):
        return True
    return (Path.home() / ".modal.toml").is_file()


def _score_local(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    from modal_app.scoring import CANDIDATE_A, CANDIDATE_B, score_candidate

    return [score_candidate(snapshot, CANDIDATE_A), score_candidate(snapshot, CANDIDATE_B)]


def score_campaign_hypotheses(snapshot: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    from modal_app.scoring import build_report, pick_winner

    if not _modal_ready():
        results = _score_local(snapshot)
        return pick_winner(results), build_report("local", results)
    try:
        import concurrent.futures
        from modal_app.recovery_runner import app, score_payloads

        def _run() -> list[dict[str, Any]]:
            with app.run():
                return score_payloads(snapshot)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            results = pool.submit(_run).result(timeout=180)
        return pick_winner(results), build_report("modal", results)
    except Exception:
        results = _score_local(snapshot)
        return pick_winner(results), build_report("local", results)


def ensure_shipping_for_tests(adapter: EnvironmentAdapter) -> EnvironmentAdapter:
    if any(m.semantic_intent == INTENT_SHIPPING for m in adapter.mappings):
        return adapter
    updated = adapter.model_copy(deep=True)
    updated.mappings.append(
        StepMapping(
            semantic_intent=INTENT_SHIPPING,
            app_action="Create Listing > Shipping category",
            confidence=0.9,
            learned_from="recovery",
            resolved_targets=["store-b-field-shipping"],
        )
    )
    return updated
