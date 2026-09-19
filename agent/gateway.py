"""Pydantic AI Gateway prize layer — same Explorer code, optional Gateway route.

SkillShift still Explore → Act → Verify on Store B.
When PYDANTIC_AI_GATEWAY_API_KEY is set, model calls go through the Gateway
so Logfire optimizations can change behaviour without editing this repo.

The decoy-ignore rule itself is created in Logfire → Gateway → Optimizations.
Paste DECOY_IGNORE_RULE_INSTRUCTION there.
"""

from __future__ import annotations

import os
from typing import Any

# Default for orgs that only enabled the AI Studio route (common EU Quick Start).
# Override with SKILLSHIFT_GATEWAY_MODEL (e.g. gateway/openai:gpt-4o when OpenAI is enabled).
DEFAULT_GATEWAY_MODEL = "gateway/aistudio:models/gemini-3.6-flash"

# Paste this into Logfire → Gateway → Optimizations → New (custom Style / Transform).
# Bind it to your Gateway endpoint (e.g. modal or openai). Toggle off/on for before/after.
DECOY_IGNORE_RULE_INSTRUCTION = """
You are choosing ONE on-screen UI control for a SkillShift agent.

Hard rules:
1. target_testid MUST be copied exactly from the provided visible_elements list.
2. Never invent a data-testid.
3. Prefer the active listing form / product creation region over decoys.
4. Ignore decoys unless no safer control exists:
   - Collections / collection management
   - Listing type / Draft / Save Draft
5. If Go Live / publish is blocked and a shipping (or similar prerequisite) control
   is visible and empty, prefer that prerequisite control.
6. Keep rationale under 25 words. Output only the structured fields requested.

Preserve technical precision. Do not change the Skill intents.
""".strip()

DECOY_TESTID_HINTS = (
    "collections",
    "listing-type",
    "draft",
)


def gateway_enabled() -> bool:
    return bool(os.environ.get("PYDANTIC_AI_GATEWAY_API_KEY", "").strip())


def gateway_model() -> str:
    """Model id when routing through the Pydantic AI Gateway."""
    return (
        os.environ.get("SKILLSHIFT_GATEWAY_MODEL", "").strip()
        or DEFAULT_GATEWAY_MODEL
    )


def materialize_model(model: str | Any) -> Any:
    """Turn SkillShift model ids into objects Agent() accepts.

    pydantic-ai 2.46 knows gateway/openai|anthropic|google|… but not
    gateway/aistudio:… — AI Studio is OpenAI-compatible behind route=aistudio.
    """
    if not isinstance(model, str):
        return model
    if model.startswith("gateway/aistudio:"):
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.gateway import gateway_provider

        model_id = model.split(":", 1)[1]
        provider = gateway_provider("openai", route="aistudio")
        return OpenAIChatModel(model_id, provider=provider)
    return model


def resolve_decision_model(
    *,
    prefer_gateway: bool | None = None,
    direct_fallback: str | None = None,
) -> str | None:
    """Pick Gateway model when keyed; else optional direct provider model."""
    use_gateway = gateway_enabled() if prefer_gateway is None else prefer_gateway
    if use_gateway:
        return gateway_model()
    return direct_fallback


def is_decoy_testid(testid: str) -> bool:
    lowered = testid.lower()
    return any(hint in lowered for hint in DECOY_TESTID_HINTS)


def filter_visible_for_demo(elements: list[dict[str, str]], *, rule_on: bool) -> list[dict[str, str]]:
    """Local before/after helper: when rule_on, drop decoy rows from the list shown to a mock picker.

    Real Gateway optimizations inject text; this only proves the *effect* offline.
    """
    if not rule_on:
        return list(elements)
    return [item for item in elements if not is_decoy_testid(item.get("testid") or "")]
