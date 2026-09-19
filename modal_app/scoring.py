"""Score diagnoser hypotheses against a JSON snapshot. No Playwright. No localhost."""

from __future__ import annotations

from typing import Any

SHIPPING_SNAPSHOT = {
    "expected_state": "product is published",
    "observed_evidence": [
        "Go Live disabled; shipping empty",
        "Select a shipping category to go live.",
    ],
    "failure_class": "missing_prerequisite",
    "controls": [
        {"ref": "store-b-field-shipping", "name": "Shipping category", "role": "select", "enabled": True},
        {"ref": "store-b-field-listing-type", "name": "Listing type", "role": "select", "enabled": True},
        {"ref": "store-b-go-live", "name": "Go Live", "role": "button", "enabled": False},
    ],
    "messages": ["Select a shipping category to go live."],
    "failed_refs": ["store-b-go-live"],
}

HYPOTHESIS_SHIPPING = {
    "id": "A",
    "rationale": "select shipping control then retry publish",
    "actions": [
        {"target_testid": "store-b-field-shipping", "action": "select", "value": "Standard"}
    ],
}

HYPOTHESIS_DECOY = {
    "id": "B",
    "rationale": "click listing-type / Save Draft",
    "actions": [
        {"target_testid": "store-b-field-listing-type", "action": "select", "value": "Draft"}
    ],
}


def _blob(snapshot: dict[str, Any]) -> str:
    evidence = " ".join(str(item) for item in snapshot.get("observed_evidence") or [])
    messages = " ".join(str(item) for item in snapshot.get("messages") or [])
    observed = str(snapshot.get("observed_state") or "")
    return f"{evidence} {messages} {observed} {snapshot.get('failure_class', '')}".lower()


def _action_blob(hypothesis: dict[str, Any]) -> str:
    parts = [
        str(hypothesis.get("id") or ""),
        str(hypothesis.get("rationale") or ""),
        str(hypothesis.get("action") or ""),
    ]
    for action in hypothesis.get("actions") or []:
        parts.append(str(action.get("target_testid") or ""))
        parts.append(str(action.get("value") or ""))
        parts.append(str(action.get("action") or ""))
    return " ".join(parts).lower()


def score_hypothesis(snapshot: dict[str, Any], hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Score one diagnoser hypothesis. Never opens a browser."""
    hyp_id = str(hypothesis.get("id") or "")
    rationale = str(hypothesis.get("rationale") or hypothesis.get("action") or "")
    snap = _blob(snapshot)
    acts = _action_blob(hypothesis)
    failure = str(snapshot.get("failure_class") or "")
    cost = max(1, len(hypothesis.get("actions") or []) or 1)

    tax_needed = failure == "missing_prerequisite" and "tax" in snap
    shipping_needed = failure == "missing_prerequisite" and "shipping" in snap and not tax_needed
    tax_plan = "tax" in acts
    shipping_plan = "shipping" in acts
    decoy_plan = any(token in acts for token in ("listing-type", "draft", "listing type"))

    verified = False
    reason = "Hypothesis does not match snapshot evidence."
    if tax_needed and tax_plan and not decoy_plan:
        verified = True
        reason = "Tax blocker evidence matches the tax-class hypothesis."
        cost = 1
    elif shipping_needed and shipping_plan and not decoy_plan:
        verified = True
        reason = "Shipping blocker evidence matches the shipping-control hypothesis."
        cost = 1
    elif decoy_plan:
        verified = False
        cost = 99
        reason = "Listing-type / Draft does not satisfy a shipping prerequisite."

    return {
        "id": hyp_id or ("A" if shipping_plan else "B"),
        "action": rationale,
        "ok": verified,
        "verified_success": verified,
        "cost": cost,
        "reason": reason,
    }


def score_candidate(snapshot: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Back-compat wrapper: treat {id, action} as a single-action hypothesis."""
    hypothesis = {
        "id": candidate.get("id"),
        "rationale": candidate.get("action") or candidate.get("rationale") or "",
        "actions": candidate.get("actions")
        or (
            [
                {
                    "target_testid": candidate.get("target_testid") or "",
                    "action": candidate.get("kind") or "click",
                    "value": candidate.get("value"),
                }
            ]
            if candidate.get("target_testid")
            else []
        ),
        "action": candidate.get("action") or "",
    }
    return score_hypothesis(snapshot, hypothesis)


def pick_winner(results: list[dict[str, Any]]) -> str:
    successful = [
        item
        for item in results
        if item.get("verified_success") or item.get("ok")
    ]
    if successful:
        return min(successful, key=lambda item: item.get("cost", 99)).get("id", "A")
    return (results[0].get("id") if results else "A") or "A"


def build_report(mode: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(results, key=lambda item: item.get("id", ""))
    return {"mode": mode, "candidates": ordered}


def status_line(report: dict[str, Any]) -> str:
    prefix = "local sequential. " if report.get("mode") == "local" else ""
    bits = []
    for item in report.get("candidates") or []:
        mark = "✅" if item.get("verified_success") or item.get("ok") else "❌"
        bits.append(f"{item.get('id')} {mark} {item.get('action', '')[:40]}")
    return prefix + " · ".join(bits)
