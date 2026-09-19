"""Typed Skill / Adapter / Verification / TraceEvent models.

Source of truth: ARCHITECTURE.md § Typed models.
Skill = WHAT (app-agnostic). Adapter = HOW HERE (app-specific).
"""

from typing import Literal

from pydantic import BaseModel, Field


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


class CandidateAction(BaseModel):
    """One grounded action chosen from currently visible elements."""

    target_testid: str
    action: Literal["click", "fill", "upload", "select"]
    value: str | None = None
    rationale: str = ""
    confidence: float = 0.5


class ExploreResult(BaseModel):
    candidates: list[CandidateAction] = Field(default_factory=list)
    chosen: CandidateAction


class StepMapping(BaseModel):
    semantic_intent: str
    app_action: str
    confidence: float
    learned_from: Literal["exploration", "recovery", "cached"]
    resolved_targets: list[str] = Field(default_factory=list)
    status: Literal[
        "candidate", "provisional", "reusable", "trusted", "deprecated"
    ] = "provisional"
    successes: int = 0
    failures: int = 0


class EnvironmentAdapter(BaseModel):
    app_id: str
    skill_name: str
    mappings: list[StepMapping]
    failure_lessons: list[str] = []
    adapter_version: int = 1


class ObservationControl(BaseModel):
    ref: str
    role: str
    name: str
    enabled: bool = True
    region: str = ""
    # Current value for inputs/selects. Lets the verifier see an empty required
    # field instead of assuming a fill succeeded. "" means empty or not an input.
    value: str = ""


class AppObservation(BaseModel):
    screen: str
    url: str = ""
    controls: list[ObservationControl]
    messages: list[str] = []
    state: dict[str, str] = Field(default_factory=dict)


class GroundingCandidate(BaseModel):
    semantic_step_intent: str
    candidates: list[CandidateAction]
    chosen: CandidateAction


class VerificationResult(BaseModel):
    passed: bool
    confidence: float
    expected_state: str
    observed_evidence: list[str]
    failure_class: Literal[
        "none",
        "action_not_executed",
        "wrong_mapping",
        "stale_mapping",
        "missing_prerequisite",
        "validation_error",
        "navigation_error",
        "ambiguous_state",
        "unexpected_app_state",
        "unsupported_concept",
    ] = "none"


class AdapterPatch(BaseModel):
    semantic_intent: str
    operation: Literal[
        "replace_mapping",
        "add_prerequisite",
        "deprecate_rule",
        "add_navigation_rule",
    ]
    new_targets: list[str]
    new_app_action: str
    evidence: list[str]
    applied: bool = False


class RunMetrics(BaseModel):
    product: str
    actions: int
    model_calls: int
    recoveries: int
    cache_hits: int
    latency_ms: int = 0


class Verification(BaseModel):
    step_intent: str
    expected_state: str
    observed_state: str
    matched: bool
    confidence: float = 1.0
    mismatch_type: Literal[
        "wrong_navigation",
        "missing_prerequisite",
        "wrong_input",
        "transient_failure",
        "unknown",
        "none",
    ] = "none"
    hypothesis: str | None = None
    alternative: str | None = None
    failure_class: Literal[
        "none",
        "action_not_executed",
        "wrong_mapping",
        "stale_mapping",
        "missing_prerequisite",
        "validation_error",
        "navigation_error",
        "ambiguous_state",
        "unexpected_app_state",
        "unsupported_concept",
    ] = "none"


class TraceEvent(BaseModel):
    before: str  # screenshot path
    action: Literal["click", "fill", "upload"]
    target: str
    value: str | None = None
    after: str  # screenshot path
