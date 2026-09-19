"""Independent failure diagnosis after a verifier miss.

Reads the observation. Does not encode a single Collections → Inventory branch.
"""

from __future__ import annotations

import json
from typing import Any

from .grounding import require_decision_backend, run_agent_sync
from .models import AppObservation, VerificationResult

_DIAGNOSER_INSTRUCTIONS = """\
A Skill step failed verification. Classify the failure and propose a short
hypothesis plus an alternative next try.

Use ONLY the observation (screen, controls, messages) and the verifier result.
Do not assume a single named navigation is always the fix.
Prefer:
- wrong_mapping / navigation_error when the screen is unrelated to the goal
- missing_prerequisite when a blocker/disabled finish control is visible
- validation_error when fields exist but values look wrong
Return failure_class, hypothesis, alternative.
"""


class Diagnosis(VerificationResult):
    hypothesis: str = ""
    alternative: str = ""


def diagnose_failure(
    verification_result: VerificationResult,
    observation: AppObservation,
    failed_refs: set[str] | list[str] | None = None,
    *,
    backend: str | None = None,
    expected_state: str = "",
) -> Diagnosis:
    resolved = backend or require_decision_backend()
    failed = set(failed_refs or [])
    if resolved == "mock":
        return _diagnose_mock(verification_result, observation, failed, expected_state)
    return _diagnose_llm(
        verification_result,
        observation,
        failed,
        expected_state=expected_state,
        model=resolved,
    )


def _diagnose_llm(
    verification_result: VerificationResult,
    observation: AppObservation,
    failed: set[str],
    *,
    expected_state: str,
    model: str,
) -> Diagnosis:
    from pydantic_ai import Agent

    payload: dict[str, Any] = {
        "verification": verification_result.model_dump(),
        "expected_state": expected_state or verification_result.expected_state,
        "failed_refs": sorted(failed),
        "observation": {
            "screen": observation.screen,
            "url": observation.url,
            "messages": observation.messages,
            "state": observation.state,
            "controls": [c.model_dump() for c in observation.controls],
        },
    }
    agent = Agent(
        model,
        name="skill_diagnoser",
        output_type=Diagnosis,
        instructions=_DIAGNOSER_INSTRUCTIONS,
    )
    return run_agent_sync(
        agent,
        ["Diagnose this failed Skill step.\n", json.dumps(payload, indent=2)],
    )


def _diagnose_mock(
    verification_result: VerificationResult,
    observation: AppObservation,
    failed: set[str],
    expected_state: str,
) -> Diagnosis:
    from .metrics import record_model_call

    record_model_call()
    heading = (
        observation.state.get("heading") or observation.screen or ""
    ).lower()
    messages = " ".join(observation.messages).lower()
    refs = {control.ref for control in observation.controls}
    names = " ".join(control.name.lower() for control in observation.controls)
    blob = f"{heading} {messages} {names}"
    goal = (expected_state or verification_result.expected_state or "").lower()
    create_goal = any(
        token in goal
        for token in ("creat", "form", "sellable", "listing", "product")
    )
    publish_goal = any(
        token in goal for token in ("publish", "public", "live", "available")
    )

    evidence = list(verification_result.observed_evidence)
    evidence.extend(observation.messages)
    if failed:
        evidence.append(f"failed_refs={sorted(failed)}")

    evidence_blob = " ".join(evidence).lower()
    if "saved testid missing" in evidence_blob or verification_result.failure_class == "stale_mapping":
        return Diagnosis(
            passed=False,
            confidence=0.95,
            expected_state=verification_result.expected_state,
            observed_evidence=evidence or ["saved testid missing"],
            failure_class="stale_mapping",
            hypothesis="A saved control is no longer on the page.",
            alternative="Re-ground from currently visible controls.",
        )

    shipping_blocker = any(
        "shipping" in msg.lower() for msg in observation.messages
    ) or any("shipping" in ref and "blocker" in ref for ref in refs)
    tax_blocker = any("tax" in msg.lower() for msg in observation.messages) or any(
        "tax" in ref and "blocker" in ref for ref in refs
    )
    finish_disabled = any(
        (not control.enabled)
        and any(token in control.ref.lower() for token in ("go-live", "publish", "activate"))
        for control in observation.controls
    )
    category_gate = any(
        ref.endswith(("-field-category", "-category-blocker")) for ref in refs
    )
    if category_gate and (
        publish_goal or verification_result.failure_class == "missing_prerequisite"
    ):
        return Diagnosis(
            passed=False,
            confidence=0.92,
            expected_state=verification_result.expected_state,
            observed_evidence=evidence or ["publish blocked; category message visible"],
            failure_class="missing_prerequisite",
            hypothesis="This environment requires a category before a listing can go Live.",
            alternative="Satisfy the visible required control, then retry publish.",
        )

    if (
        tax_blocker or ("tax" in blob and finish_disabled)
    ) and (
        publish_goal or verification_result.failure_class == "missing_prerequisite"
    ):
        return Diagnosis(
            passed=False,
            confidence=0.92,
            expected_state=verification_result.expected_state,
            observed_evidence=evidence or ["publish blocked; tax message visible"],
            failure_class="missing_prerequisite",
            hypothesis="This environment requires an extra tax-class prerequisite.",
            alternative="Satisfy the visible required control, then retry publish.",
        )

    if (shipping_blocker or ("shipping" in blob and finish_disabled)) and (
        publish_goal or verification_result.failure_class == "missing_prerequisite"
    ):
        return Diagnosis(
            passed=False,
            confidence=0.92,
            expected_state=verification_result.expected_state,
            observed_evidence=evidence or ["publish blocked; shipping message visible"],
            failure_class="missing_prerequisite",
            hypothesis=(
                "This environment requires an extra prerequisite before publish."
            ),
            alternative="Satisfy the visible required control, then retry publish.",
        )

    if "collection" in heading:
        if create_goal or publish_goal:
            return Diagnosis(
                passed=False,
                confidence=0.9,
                expected_state=verification_result.expected_state,
                observed_evidence=evidence or ["collections-like heading"],
                failure_class="wrong_mapping",
                hypothesis="This screen manages collections, not a new sellable item.",
                alternative="Try a different visible nav or create control.",
            )

    refined = verification_result.failure_class
    if refined == "none":
        refined = "ambiguous_state"
    return Diagnosis(
        passed=False,
        confidence=verification_result.confidence,
        expected_state=verification_result.expected_state,
        observed_evidence=evidence or [observation.screen],
        failure_class=refined,
        hypothesis=verification_result.observed_evidence[0]
        if verification_result.observed_evidence
        else "Verifier did not accept the current screen.",
        alternative="Pick another visible control that was not just tried.",
    )
