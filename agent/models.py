"""Typed Skill / Adapter / Verification / TraceEvent models.

Source of truth: ARCHITECTURE.md § Typed models.
Skill = WHAT (app-agnostic). Adapter = HOW HERE (app-specific).
"""

from typing import Literal

from pydantic import BaseModel


class SkillStep(BaseModel):
    intent: str
    required_inputs: list[str]
    expected_state: str
    success_condition: str


class Skill(BaseModel):
    name: str
    goal: str
    inputs: list[str]
    steps: list[SkillStep]
    final_success_condition: str


class StepMapping(BaseModel):
    semantic_intent: str
    app_action: str
    confidence: float
    learned_from: Literal["exploration", "recovery", "cached"]


class EnvironmentAdapter(BaseModel):
    app_id: str
    skill_name: str
    mappings: list[StepMapping]
    failure_lessons: list[str] = []


class Verification(BaseModel):
    step_intent: str
    expected_state: str
    observed_state: str
    matched: bool
    hypothesis: str | None = None
    alternative: str | None = None


class TraceEvent(BaseModel):
    before: str  # screenshot path
    action: Literal["click", "fill", "upload"]
    target: str
    value: str | None = None
    after: str  # screenshot path
