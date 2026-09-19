"""Compact page snapshot for Explorer / Verifier / Recovery.

Playwright stays the hands. This module never chooses Inventory / Go Live.
"""

from __future__ import annotations

from urllib.parse import urlparse

from .grounding import heading_text, is_judge_chrome
from .models import AppObservation, ObservationControl

_MESSAGE_HINTS = ("blocker", "banner", "error", "alert", "warning")


def observe_app(hands) -> AppObservation:
    """Build an AppObservation from currently visible testid nodes."""
    url = ""
    try:
        url = str(hands.page.url or "")
    except Exception:
        url = getattr(hands, "base_url", "") or ""

    heading = heading_text(hands)
    path = urlparse(url).path if url else ""
    screen = heading or path or "unknown"

    raw = []
    try:
        raw = hands.visible_elements()
    except Exception:
        raw = []

    controls: list[ObservationControl] = []
    for item in raw:
        ref = (item.get("testid") or "").strip()
        if not ref or is_judge_chrome(ref):
            continue
        name = (item.get("name") or item.get("text") or "").strip()
        role = (item.get("role") or "").strip() or "generic"
        controls.append(
            ObservationControl(
                ref=ref,
                role=role,
                name=name,
                enabled=_control_enabled(hands, ref),
                value=_control_value(hands, ref),
            )
        )

    messages = _visible_messages(hands, controls)
    state: dict[str, str] = {}
    if heading:
        state["heading"] = heading
    if path:
        state["path"] = path

    return AppObservation(
        screen=screen,
        url=url,
        controls=controls,
        messages=messages,
        state=state,
    )


def _control_value(hands, ref: str) -> str:
    """What the field currently holds. Empty string for non-inputs."""
    try:
        locator = hands.page.get_by_test_id(ref)
        if locator.count() == 0:
            return ""
        node = locator.first
        tag = str(node.evaluate("el => el.tagName") or "").lower()
        if tag not in {"input", "select", "textarea"}:
            return ""
        if str(node.get_attribute("type") or "").lower() == "file":
            chosen = bool(node.evaluate("el => (el.files || []).length > 0"))
            return "file selected" if chosen else ""
        return (node.input_value() or "").strip()[:120]
    except Exception:
        return ""


def _control_enabled(hands, ref: str) -> bool:
    try:
        locator = hands.page.get_by_test_id(ref)
        if locator.count() == 0:
            return True
        return bool(locator.first.is_enabled())
    except Exception:
        return True


def _visible_messages(hands, controls: list[ObservationControl]) -> list[str]:
    messages: list[str] = []
    for control in controls:
        ref = control.ref.lower()
        if any(hint in ref for hint in _MESSAGE_HINTS) and control.name:
            messages.append(control.name[:240])
    try:
        alerts = hands.page.locator("[role=alert]")
        count = min(alerts.count(), 6)
        for index in range(count):
            text = alerts.nth(index).inner_text().strip()
            if text and text not in messages:
                messages.append(text[:240])
    except Exception:
        pass
    return messages
