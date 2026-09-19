"""Score diagnoser hypotheses remotely (Modal) or locally. No Playwright."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .models import AppObservation, CandidateAction, VerificationResult

_MODAL_UNAVAILABLE = "Modal unavailable — local sequential candidates"


def build_snapshot(
    verification_result: VerificationResult,
    observation: AppObservation,
    failed_refs: set[str] | list[str] | None = None,
) -> dict[str, Any]:
    return {
        "expected_state": verification_result.expected_state,
        "observed_evidence": list(verification_result.observed_evidence),
        "failure_class": verification_result.failure_class,
        "controls": [control.model_dump() for control in observation.controls],
        "messages": list(observation.messages),
        "failed_refs": sorted(failed_refs or []),
        "screen": observation.screen,
    }


def hypotheses_from_observation(
    observation: AppObservation,
    *,
    failure_class: str = "",
) -> list[dict[str, Any]]:
    """Two CandidateAction-shaped hypotheses. No staged LAUNCH10 winner."""
    refs = {control.ref: control for control in observation.controls}
    primary: dict[str, Any] | None = None
    decoy: dict[str, Any] | None = None
    tax_ref = next((ref for ref in refs if "tax-class" in ref), None)
    if tax_ref:
        primary = {
            "id": "A",
            "rationale": "select the visible tax-class control then retry publish",
            "actions": [
                {
                    "target_testid": tax_ref,
                    "action": "select",
                    "value": "Standard rate",
                }
            ],
        }

    for ref, control in refs.items():
        lowered = f"{ref} {control.name}".lower()
        if primary is None and "tax-class" in lowered:
            primary = {
                "id": "A",
                "rationale": "select the visible tax-class control then retry publish",
                "actions": [
                    {
                        "target_testid": ref,
                        "action": "select",
                        "value": "Standard rate",
                    }
                ],
            }
        if primary is None and "shipping" in lowered:
            primary = {
                "id": "A",
                "rationale": "select the visible shipping control then retry publish",
                "actions": [
                    {
                        "target_testid": ref,
                        "action": "select",
                        "value": "Standard",
                    }
                ],
            }
        if decoy is None and (
            "listing-type" in lowered or "draft" in lowered or "listing type" in lowered
        ):
            decoy = {
                "id": "B",
                "rationale": "change listing type / Save Draft",
                "actions": [
                    {
                        "target_testid": ref,
                        "action": "select",
                        "value": "Draft",
                    }
                ],
            }

    if primary is None:
        enabled = next(
            (c for c in observation.controls if c.enabled and c.ref not in {"store-b-go-live"}),
            observation.controls[0] if observation.controls else None,
        )
        if enabled is not None:
            primary = {
                "id": "A",
                "rationale": f"try visible control {enabled.name or enabled.ref}",
                "actions": [{"target_testid": enabled.ref, "action": "click", "value": None}],
            }
    if decoy is None:
        decoy = {
            "id": "B",
            "rationale": "click listing-type / Save Draft (should verify false)",
            "actions": [
                {
                    "target_testid": "store-b-field-listing-type",
                    "action": "select",
                    "value": "Draft",
                }
            ],
        }
    _ = failure_class
    return [primary, decoy] if primary is not None else [decoy]


def candidate_from_hypothesis(hypothesis: dict[str, Any]) -> CandidateAction | None:
    actions = hypothesis.get("actions") or []
    if not actions:
        return None
    first = actions[0]
    return CandidateAction(
        target_testid=str(first.get("target_testid") or ""),
        action=first.get("action") or "click",  # type: ignore[arg-type]
        value=first.get("value"),
        rationale=str(hypothesis.get("rationale") or ""),
        confidence=0.8,
    )


def _modal_ready() -> bool:
    if os.environ.get("SKILLSHIFT_FORCE_LOCAL_MODAL", "").lower() in {"1", "true", "yes"}:
        return False
    if os.environ.get("PYTEST_CURRENT_TEST") and os.environ.get("SKILLSHIFT_USE_MODAL") != "1":
        return False
    try:
        import modal as sdk

        if not hasattr(sdk, "App"):
            return False
    except ImportError:
        return False
    if os.environ.get("MODAL_TOKEN_ID"):
        return True
    return (Path.home() / ".modal.toml").is_file()


def score_diagnoser_hypotheses(
    snapshot: dict[str, Any],
    hypotheses: list[dict[str, Any]] | None = None,
) -> tuple[str, dict[str, Any]]:
    from modal_app.scoring import build_report, pick_winner, score_hypothesis

    hyps = hypotheses or []
    if not hyps:
        hyps = [
            {"id": "A", "rationale": "unknown", "actions": []},
            {"id": "B", "rationale": "unknown", "actions": []},
        ]

    if not _modal_ready():
        print(_MODAL_UNAVAILABLE, flush=True)
        results = [score_hypothesis(snapshot, item) for item in hyps]
        return pick_winner(results), build_report("local", results)

    try:
        import concurrent.futures

        from modal_app.recovery_runner import app, score_payloads

        def _run() -> list[dict[str, Any]]:
            with app.run():
                return score_payloads(snapshot, hyps)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            results = pool.submit(_run).result(timeout=180)
        return pick_winner(results), build_report("modal", results)
    except Exception:
        print(_MODAL_UNAVAILABLE, flush=True)
        results = [score_hypothesis(snapshot, item) for item in hyps]
        return pick_winner(results), build_report("local", results)
