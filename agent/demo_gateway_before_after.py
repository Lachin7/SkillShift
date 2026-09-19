"""Offline before/after for the decoy-ignore prize rule (no Gateway key required).

Simulates what a Logfire optimization does to the *input* the picker sees:
  rule OFF → decoys remain (listing-type looks tempting)
  rule ON  → decoys filtered; shipping is the safe pick

Real prize entry still needs Logfire Gateway with DECOY_IGNORE_RULE_INSTRUCTION
bound to your route — see docs/GATEWAY_PRIZE.md.

Usage (from repo root):
  .venv/bin/python -m agent.demo_gateway_before_after
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.gateway import (  # noqa: E402
    DECOY_IGNORE_RULE_INSTRUCTION,
    filter_visible_for_demo,
    gateway_enabled,
    gateway_model,
)
from agent.grounding import first_suffix  # noqa: E402

# Snapshot shaped like a shipping-blocker screen (Store B).
SHIPPING_BLOCKER_ELEMENTS = [
    {
        "testid": "store-b-field-shipping",
        "role": "select",
        "name": "Shipping category",
        "text": "Shipping category",
    },
    {
        "testid": "store-b-field-listing-type",
        "role": "select",
        "name": "Listing type",
        "text": "Listing type",
    },
    {
        "testid": "store-b-go-live",
        "role": "button",
        "name": "Go Live",
        "text": "Go Live",
    },
]


def naive_pick(elements: list[dict[str, str]]) -> str | None:
    """Naive picker that prefers listing-type if present (the decoy failure mode)."""
    ids = [item["testid"] for item in elements]
    for testid in ids:
        if "listing-type" in testid:
            return testid
    return first_suffix(ids, ("-field-shipping", "-go-live"))


def main() -> int:
    off = filter_visible_for_demo(SHIPPING_BLOCKER_ELEMENTS, rule_on=False)
    on = filter_visible_for_demo(SHIPPING_BLOCKER_ELEMENTS, rule_on=True)
    pick_off = naive_pick(off)
    pick_on = naive_pick(on)

    print("SkillShift — Gateway prize before/after (local simulation)")
    print("=" * 60)
    print("Intent: satisfy shipping / publish (Go Live blocked)")
    print()
    print("BEFORE (rule OFF) — visible controls:")
    print(json.dumps([e["testid"] for e in off], indent=2))
    print(f"  naive pick → {pick_off}")
    print()
    print("AFTER (rule ON) — decoys dropped from consideration:")
    print(json.dumps([e["testid"] for e in on], indent=2))
    print(f"  naive pick → {pick_on}")
    print()
    ok = pick_off == "store-b-field-listing-type" and pick_on == "store-b-field-shipping"
    print(f"visible change: {ok}")
    print()
    print("Paste this instruction into Logfire → Gateway → Optimizations:")
    print("-" * 60)
    print(DECOY_IGNORE_RULE_INSTRUCTION)
    print("-" * 60)
    print()
    if gateway_enabled():
        print(f"Gateway key detected → live model would be: {gateway_model()}")
    else:
        print(
            "No PYDANTIC_AI_GATEWAY_API_KEY yet — code path is ready; "
            "set the key to send Explorer through Gateway."
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
