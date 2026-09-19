"""Gateway prize layer: model routing + decoy-ignore demo (no network)."""

from __future__ import annotations

import agent.demo_gateway_before_after as demo
from agent.gateway import (
    DECOY_IGNORE_RULE_INSTRUCTION,
    DEFAULT_GATEWAY_MODEL,
    filter_visible_for_demo,
    gateway_enabled,
    gateway_model,
    is_decoy_testid,
)
from agent.grounding import configured_model, require_decision_backend


def test_decoy_detection():
    assert is_decoy_testid("store-b-field-listing-type")
    assert is_decoy_testid("store-b-nav-collections")
    assert not is_decoy_testid("store-b-field-shipping")


def test_filter_visible_for_demo_drops_decoys():
    elements = [
        {"testid": "store-b-field-shipping", "name": "Shipping"},
        {"testid": "store-b-field-listing-type", "name": "Listing type"},
    ]
    off = filter_visible_for_demo(elements, rule_on=False)
    on = filter_visible_for_demo(elements, rule_on=True)
    assert len(off) == 2
    assert [e["testid"] for e in on] == ["store-b-field-shipping"]


def test_rule_instruction_mentions_visible_only():
    text = DECOY_IGNORE_RULE_INSTRUCTION.lower()
    assert "visible_elements" in text
    assert "invent" in text
    assert "draft" in text or "listing type" in text


def test_configured_model_prefers_gateway(monkeypatch):
    monkeypatch.delenv("SKILLSHIFT_MOCK_LLM", raising=False)
    monkeypatch.delenv("SKILLSHIFT_MODEL", raising=False)
    monkeypatch.delenv("SKILLSHIFT_USE_GATEWAY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("PYDANTIC_AI_GATEWAY_API_KEY", "pylf_v_test")
    monkeypatch.delenv("SKILLSHIFT_GATEWAY_MODEL", raising=False)
    assert gateway_enabled() is True
    assert gateway_model() == DEFAULT_GATEWAY_MODEL
    assert configured_model() == DEFAULT_GATEWAY_MODEL
    assert require_decision_backend() == DEFAULT_GATEWAY_MODEL


def test_materialize_aistudio_model(monkeypatch):
    from agent.gateway import materialize_model
    from pydantic_ai.models.openai import OpenAIChatModel

    monkeypatch.setenv("PYDANTIC_AI_GATEWAY_API_KEY", "pylf_v2_eu_testkey")
    monkeypatch.setenv(
        "PYDANTIC_AI_GATEWAY_BASE_URL", "https://gateway-eu.pydantic.dev/proxy"
    )
    model = materialize_model("gateway/aistudio:models/gemini-3.6-flash")
    assert isinstance(model, OpenAIChatModel)
    assert materialize_model("google:gemini-3.6-flash") == "google:gemini-3.6-flash"


def test_skillshift_model_override_beats_gateway(monkeypatch):
    monkeypatch.setenv("PYDANTIC_AI_GATEWAY_API_KEY", "pylf_v_test")
    monkeypatch.setenv("SKILLSHIFT_MODEL", "gateway/groq:openai/gpt-oss-120b")
    assert configured_model() == "gateway/groq:openai/gpt-oss-120b"


def test_before_after_script_exits_zero(capsys):
    assert demo.main() == 0
    out = capsys.readouterr().out
    assert "BEFORE" in out
    assert "AFTER" in out
    assert "store-b-field-shipping" in out
    assert "listing-type" in out
