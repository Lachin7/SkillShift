"""Independent verifier. Explorer never scores its own success.

Returns legacy Verification (dashboard) plus VerificationResult (failure_class).
"""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import urlopen

from .grounding import (
    elements_from_observation,
    heading_text,
    page_text,
    require_decision_backend,
    screenshot_parts,
    summarize_elements,
)
from .models import AppObservation, SkillStep, Verification, VerificationResult
from .observer import observe_app

_VERIFIER_INSTRUCTIONS = """\
You verify whether the CURRENT screen satisfies a Skill step's expected_state
and success_condition. You are a separate skill_verifier — do not assume the
previous action succeeded just because it was clicked.

Return matched=true only if the step goal appears satisfied now.
If not, set mismatch_type:
- wrong_navigation: landed on an unrelated area
- missing_prerequisite: form/action blocked until another field is set
- wrong_input: fields present but values wrong/incomplete
- transient_failure: loading / temporary
- unknown: unclear

Also set failure_class from: none, action_not_executed, wrong_mapping,
stale_mapping, missing_prerequisite, validation_error, navigation_error,
ambiguous_state, unexpected_app_state, unsupported_concept.

Use observed_state to describe what you see. hypothesis/alternative should help recovery.
Only reason from the provided observation, page_text, and screenshot.
Clicking a publish control is not success — a published product must be visible
or the test API must report status=published.
"""

MISMATCH_TO_FAILURE: dict[str, str] = {
    "none": "none",
    "wrong_navigation": "wrong_mapping",
    "missing_prerequisite": "missing_prerequisite",
    "wrong_input": "validation_error",
    "transient_failure": "action_not_executed",
    "unknown": "ambiguous_state",
}

FAILURE_TO_MISMATCH: dict[str, str] = {
    "none": "none",
    "action_not_executed": "transient_failure",
    "wrong_mapping": "wrong_navigation",
    "stale_mapping": "wrong_navigation",
    "missing_prerequisite": "missing_prerequisite",
    "validation_error": "wrong_input",
    "navigation_error": "wrong_navigation",
    "ambiguous_state": "unknown",
    "unexpected_app_state": "unknown",
    "unsupported_concept": "unknown",
}


def verify_step(
    hands,
    skill_step: SkillStep,
    *,
    screenshot_bytes: bytes | None = None,
    product_name: str | None = None,
    backend: str | None = None,
) -> Verification:
    verification, _ = verify_independent(
        hands,
        skill_step,
        screenshot_bytes=screenshot_bytes,
        product_name=product_name,
        backend=backend,
    )
    return verification


def verify_independent(
    hands,
    skill_step: SkillStep,
    *,
    screenshot_bytes: bytes | None = None,
    product_name: str | None = None,
    backend: str | None = None,
) -> tuple[Verification, VerificationResult]:
    """Separate verifier call. Collects observe_app + after screenshot."""
    observation = observe_app(hands)
    text = page_text(hands)
    heading = heading_text(hands)
    resolved = backend or require_decision_backend()
    api_state = None
    if _is_publish_step(skill_step):
        api_state = fetch_store_b_state(hands, product_name)
    try:
        shot = screenshot_bytes if screenshot_bytes is not None else hands.screenshot()
    except Exception:
        shot = None

    if resolved == "mock":
        verification = _verify_mock(
            skill_step,
            observation,
            text,
            heading,
            hands,
            api_state=api_state,
            product_name=product_name,
        )
    else:
        verification = _verify_llm(
            skill_step,
            observation,
            text,
            heading,
            screenshot_bytes=shot or b"",
            api_state=api_state,
            model=resolved,
        )
    if _is_publish_step(skill_step) and not verification.matched:
        enabled = _go_live_enabled(hands, observation)
        api_ok = bool(
            api_state
            and api_state.get("status") == "published"
            and product_name
            and str(api_state.get("title") or "").lower() == product_name.lower()
        )
        card_ok = _product_card_visible(hands, product_name)
        if enabled is False:
            card_ok = False
            api_ok = False
        if card_ok or api_ok:
            verification = verification.model_copy(
                update={
                    "matched": True,
                    "mismatch_type": "none",
                    "failure_class": "none",
                    "observed_state": "public product card visible",
                    "confidence": max(verification.confidence, 0.95),
                }
            )
    result = verification_to_result(verification)
    return verification, result


def verification_to_result(verification: Verification) -> VerificationResult:
    failure = verification.failure_class
    if failure == "none" and not verification.matched:
        failure = MISMATCH_TO_FAILURE.get(verification.mismatch_type, "ambiguous_state")
    if verification.matched:
        failure = "none"
    evidence = [verification.observed_state] if verification.observed_state else []
    if verification.hypothesis:
        evidence.append(verification.hypothesis)
    return VerificationResult(
        passed=verification.matched,
        confidence=verification.confidence,
        expected_state=verification.expected_state,
        observed_evidence=evidence,
        failure_class=failure,  # type: ignore[arg-type]
    )


def failure_class_to_mismatch(failure_class: str) -> str:
    return FAILURE_TO_MISMATCH.get(failure_class, "unknown")


def _is_publish_step(skill_step: SkillStep) -> bool:
    intent = skill_step.intent.lower()
    expected = skill_step.expected_state.lower()
    return any(
        token in intent or token in expected
        for token in ("publicly available", "publish", "published")
    )


def fetch_store_b_state(hands, product_name: str | None) -> dict[str, Any] | None:
    """Test API only. Never used for navigation steps."""
    base = getattr(hands, "base_url", "") or ""
    if not base:
        return None
    from .targets import current_target

    url = f"{base.rstrip('/')}/api/store-b-state?app={quote(current_target().app_id)}"
    if product_name:
        url = f"{url}&title={quote(product_name)}"
    try:
        with urlopen(url, timeout=2) as response:  # noqa: S310 — local demo URL
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _verify_llm(
    skill_step: SkillStep,
    observation: AppObservation,
    text: str,
    heading: str,
    *,
    screenshot_bytes: bytes,
    api_state: dict[str, Any] | None,
    model: str,
) -> Verification:
    from pydantic_ai import Agent

    payload: dict[str, Any] = {
        "intent": skill_step.intent,
        "expected_state": skill_step.expected_state,
        "success_condition": skill_step.success_condition,
        "heading": heading,
        "page_text_excerpt": text[:4000],
        "observation": observation.model_dump(),
        "visible_elements": json.loads(
            summarize_elements(elements_from_observation(observation))
        ),
        "test_api": api_state,
    }
    user_parts: list[object] = [
        "Verify this Skill step against the current UI.\n",
        json.dumps(payload, indent=2),
        *screenshot_parts(screenshot_bytes or None),
    ]
    agent = Agent(
        model,
        name="skill_verifier",
        output_type=Verification,
        instructions=_VERIFIER_INSTRUCTIONS,
    )
    from .grounding import run_agent_sync

    result = run_agent_sync(agent, user_parts)
    failure = result.failure_class
    if result.matched:
        failure = "none"
    elif failure == "none":
        failure = MISMATCH_TO_FAILURE.get(result.mismatch_type, "ambiguous_state")
    return result.model_copy(
        update={
            "step_intent": skill_step.intent,
            "expected_state": skill_step.expected_state,
            "failure_class": failure,
        }
    )


def _go_live_enabled(hands, observation: AppObservation | None = None) -> bool | None:
    from .grounding import FINISH_SUFFIXES, first_suffix, is_finish_control

    refs: list[str] = []
    if observation is not None:
        refs = [control.ref for control in observation.controls if is_finish_control(control.ref)]
    if not refs:
        found = first_suffix(
            {item.get("testid", "") for item in getattr(hands, "visible_elements", lambda: [])()}
            if observation is None
            else set(),
            FINISH_SUFFIXES,
        )
        refs = [found] if found else ["store-b-go-live"]
    for ref in refs:
        try:
            button = hands.page.get_by_test_id(ref)
            if button.count() == 0 or not button.is_visible():
                continue
            return button.is_enabled()
        except Exception:
            continue
    return None


def _field_value(hands, testid: str) -> str:
    try:
        locator = hands.page.get_by_test_id(testid)
        if locator.count() == 0:
            return ""
        return locator.input_value().strip()
    except Exception:
        return ""


def _product_card_visible(hands, product_name: str | None = None) -> bool:
    try:
        cards = hands.page.locator("[data-testid$='-product-card']")
        if product_name:
            cards = cards.filter(has_text=product_name)
        return cards.count() > 0 and cards.first.is_visible()
    except Exception:
        return False


def _verify_mock(
    skill_step: SkillStep,
    observation: AppObservation,
    text: str,
    heading: str,
    hands,
    *,
    api_state: dict[str, Any] | None = None,
    product_name: str | None = None,
) -> Verification:
    """CI mock: judge from observation + DOM signals. Fills failure_class."""
    from .metrics import record_model_call

    record_model_call()
    ids = {control.ref for control in observation.controls}
    intent = skill_step.intent.lower()
    heading_l = (heading or observation.screen or "").lower()

    def pack(
        *,
        matched: bool,
        observed: str,
        mismatch: str,
        failure: str,
        confidence: float,
        hypothesis: str | None = None,
        alternative: str | None = None,
    ) -> Verification:
        return Verification(
            step_intent=skill_step.intent,
            expected_state=skill_step.expected_state,
            observed_state=observed,
            matched=matched,
            confidence=confidence,
            mismatch_type=mismatch,  # type: ignore[arg-type]
            hypothesis=hypothesis,
            alternative=alternative,
            failure_class=failure,  # type: ignore[arg-type]
        )

    if "sellable" in intent or "creating" in intent or "start" in intent:
        name_id = next((ref for ref in ids if ref.endswith(("-field-name", "-field-title"))), None)
        create_id = next((ref for ref in ids if ref.endswith(("-create-listing", "-new-row"))), None)
        if name_id:
            return pack(
                matched=True,
                observed="product creation form visible with name/price/image fields",
                mismatch="none",
                failure="none",
                confidence=0.95,
            )
        if create_id:
            return pack(
                matched=False,
                observed="create control visible; form not open",
                mismatch="wrong_navigation",
                failure="navigation_error",
                confidence=0.7,
                hypothesis="Need to open Create Listing",
                alternative="Click Create Listing",
            )
        if "collections" in heading_l or any("collections-create" in ref for ref in ids):
            return pack(
                matched=False,
                observed="collection management interface",
                mismatch="wrong_navigation",
                failure="wrong_mapping",
                confidence=0.9,
                hypothesis="Collections is not product creation",
                alternative="Try another visible nav item",
            )
        return pack(
            matched=False,
            observed=f"heading={heading!r}; form not open",
            mismatch="wrong_navigation",
            failure="navigation_error",
            confidence=0.6,
            hypothesis="Not yet on a product creation form",
            alternative="Navigate toward a create-listing control",
        )

    if "basic product information" in intent:
        name_id = next((ref for ref in ids if ref.endswith(("-field-name", "-field-title"))), None)
        price_id = next((ref for ref in ids if ref.endswith(("-field-price", "-field-amount"))), None)
        name_ok = bool(name_id and _field_value(hands, name_id))
        price_ok = bool(price_id and _field_value(hands, price_id))
        matched = name_ok and price_ok
        return pack(
            matched=matched,
            observed=f"name_filled={name_ok} price_filled={price_ok}",
            mismatch="none" if matched else "wrong_input",
            failure="none" if matched else "validation_error",
            confidence=0.9,
        )

    if "image" in intent or "attach" in intent:
        matched = False
        try:
            matched = hands.page.locator(".b-preview img, .media-preview").count() > 0
        except Exception:
            matched = False
        if not matched:
            try:
                matched = bool(
                    hands.page.evaluate(
                        """() => {
                          const el = document.querySelector(
                            "[data-testid$='-field-image'], [data-testid$='-field-photo']"
                          );
                          return !!(el && el.files && el.files.length);
                        }"""
                    )
                )
            except Exception:
                matched = False
        return pack(
            matched=matched,
            observed="image preview visible" if matched else "no image preview",
            mismatch="none" if matched else "wrong_input",
            failure="none" if matched else "validation_error",
            confidence=0.85,
        )

    if "publicly available" in intent or "publish" in intent:
        api_title = str((api_state or {}).get("title") or "")
        published_api = bool(
            api_state
            and api_state.get("status") == "published"
            and product_name
            and api_title.lower() == product_name.lower()
        )
        enabled = _go_live_enabled(hands, observation)
        card_ok = _product_card_visible(hands, product_name)
        # A leftover catalog item is not success while the current finish control is blocked.
        if enabled is False:
            card_ok = False
            published_api = False
        if card_ok or published_api:
            evidence = "public product card visible"
            if published_api:
                evidence = f"{evidence}; test API status=published"
            return pack(
                matched=True,
                observed=evidence,
                mismatch="none",
                failure="none",
                confidence=0.95,
            )

        shipping = _field_value(hands, "store-b-field-shipping") or _field_value(
            hands,
            next((ref for ref in ids if ref.endswith("-field-shipping")), "store-b-field-shipping"),
        )
        tax = _field_value(
            hands,
            next((ref for ref in ids if ref.endswith("-field-tax-class")), "store-b-field-tax-class"),
        )
        blocker_msgs = [msg for msg in observation.messages if msg]
        shipping_blocker = any("shipping" in msg.lower() for msg in blocker_msgs)
        tax_blocker = any("tax" in msg.lower() for msg in blocker_msgs)
        if any(ref.endswith("-shipping-blocker") for ref in ids):
            shipping_blocker = True
        if any(ref.endswith("-tax-blocker") for ref in ids):
            tax_blocker = True
        if enabled is False and not shipping:
            observed = f"finish disabled; shipping empty; {'shipping blocker visible' if shipping_blocker else ''}.".strip()
            return pack(
                matched=False,
                observed=observed,
                mismatch="missing_prerequisite",
                failure="missing_prerequisite",
                confidence=0.9,
                hypothesis=(
                    "This environment requires an additional prerequisite "
                    "that was not part of the original skill."
                ),
                alternative="Set the shipping category control, then retry publish",
            )
        category = _field_value(
            hands,
            next((ref for ref in ids if ref.endswith("-field-category")), "store-c-field-category"),
        )
        category_blocker = any("category" in msg.lower() for msg in blocker_msgs) or any(
            ref.endswith("-category-blocker") for ref in ids
        )
        if category_blocker or (
            not category
            and any(ref.endswith("-field-category") for ref in ids)
            and any(ref.endswith("-field-status") for ref in ids)
        ):
            return pack(
                matched=False,
                observed="status Live blocked; category empty; category blocker visible.",
                mismatch="missing_prerequisite",
                failure="missing_prerequisite",
                confidence=0.9,
                hypothesis="This environment requires a category before a listing can go Live.",
                alternative="Set the category control, then set status Live and save.",
            )
        if enabled is False and (tax_blocker or (not tax and any(ref.endswith("-field-tax-class") for ref in ids))):
            return pack(
                matched=False,
                observed="finish disabled; tax class empty; tax blocker visible.",
                mismatch="missing_prerequisite",
                failure="missing_prerequisite",
                confidence=0.9,
                hypothesis="This environment requires an extra tax-class prerequisite.",
                alternative="Set the tax class control, then retry publish",
            )
        if enabled is True:
            return pack(
                matched=False,
                observed="Go Live enabled; product not yet published",
                mismatch="wrong_input",
                failure="action_not_executed",
                confidence=0.7,
                hypothesis="Publish control ready but not completed",
                alternative="Click Go Live",
            )
        return pack(
            matched=False,
            observed="publish not complete",
            mismatch="unknown",
            failure="ambiguous_state",
            confidence=0.5,
        )

    return pack(
        matched=False,
        observed=heading or text[:200],
        mismatch="unknown",
        failure="ambiguous_state",
        confidence=0.4,
    )
