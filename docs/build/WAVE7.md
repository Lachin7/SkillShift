# Wave 7 — Real agent pipeline (from the build brief)

R1 already did brief **Priority 0–1**: empty Store B adapter, Explorer → Act → Verify → Recover, shipping as a real prerequisite, second-run cache.

Wave 7 implements the **remaining technical agent** from [prompts/skillshift_build_brief.md](../../prompts/skillshift_build_brief.md) without rewriting the demo stores.

```text
Skill  = WHAT (frozen four intents — do not rename)
Adapter = HOW HERE (discovered, patched, versioned)
Trace  = WHAT happened (phase events, not just recorder clicks)
```

## Already true (do not undo)

- Live path must not use `adapter.wrong.json`, `RECOVERED_ACTION`, or Store B `if "go live"` decision tables.
- Explorer / Recovery pick **only** from currently visible elements.
- Skill stays four intents from [shared/routes.md](../shared/routes.md).
- Playwright is hands. Pydantic AI is brain.
- Promo / LAUNCH10 is **not** the hero; shipping is. Campaign + Modal come back as **real hypotheses**, not hardcoded A=`LAUNCH10`.

## What Wave 7 adds

| Loop (brief §4) | Current gap | Wave 7 |
| --- | --- | --- |
| A Skill induction | Still locked mapping; optional multimodal | 7A may attach screenshots; Skill schema stays frozen |
| B Grounding | Real, but reasoning vocab is raw testids | Compact `observe_app()` snapshot + `GroundingCandidate` |
| C Verify + learn | One verifier; thin failure types; no patch object | Independent verifier + diagnoser + `AdapterPatch` |
| Memory | One JSON adapter file | Rule lifecycle + failure memory + metrics |
| Modal | Staged campaign A/B | Isolated scoring of **diagnoser** hypotheses |
| Proof | Second run works | Counted reuse_gain + optional naive-replay baseline |

## Locked contracts (all Wave 7 agents)

Add to [agent/models.py](../../agent/models.py). Keep existing `Skill`, `CandidateAction`, `StepMapping`, `EnvironmentAdapter`, `Verification` working. **Extend**; do not break R1 tests.

```python
class ObservationControl(BaseModel):
    ref: str                 # stable id for this observation only (testid if present)
    role: str
    name: str
    enabled: bool = True
    region: str = ""

class AppObservation(BaseModel):
    screen: str              # short heading / URL path, not a Store B enum invented by Python
    url: str = ""
    controls: list[ObservationControl]
    messages: list[str] = []  # visible blockers, banners, errors
    state: dict[str, str] = {}

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
```

Map old `Verification.mismatch_type` → `failure_class` so the dashboard can still read `matched` / `mismatch_type`:

| mismatch_type (keep writing) | failure_class |
| --- | --- |
| none | none |
| wrong_navigation | wrong_mapping or navigation_error |
| missing_prerequisite | missing_prerequisite |
| wrong_input | validation_error |
| transient_failure | action_not_executed |
| unknown | ambiguous_state |

`StepMapping` may gain optional:

- `status`: `candidate | provisional | reusable | trusted | deprecated` (default `provisional` after first verified success, `reusable` after second-run cache hit)
- `successes` / `failures` ints

Do **not** change Skill step intent strings.

## Test-only Store B state API

Verifier ground truth, **not** for Explorer/Planner.

`GET /api/store-b-state` → JSON like:

```json
{
  "product_exists": true,
  "title": "Leather Bag",
  "price": "89",
  "status": "published",
  "purchasable": true
}
```

Must not be imported by `explorer.py` or `recovery.py`.

## Agent order

| Agent | Owns | Depends on |
| --- | --- | --- |
| [7A](../../prompts/agent-7a.md) | Models + `observe_app` + test API | R1 |
| [7B](../../prompts/agent-7b.md) | Independent verifier + diagnoser | 7A |
| [7C](../../prompts/agent-7c.md) | AdapterPatch curator + apply-after-verify | 7B |
| [7D](../../prompts/agent-7d.md) | Metrics, reuse_gain, naive-replay baseline | 7C |
| [7E](../../prompts/agent-7e.md) | Modal scores diagnoser hypotheses | 7C |
| [7F](../../prompts/agent-7f.md) | Dashboard trace of the real loop | 7B (payload), 7D (metrics) |

Do **7A → 7B → 7C** strictly. Then **7D and 7E** may run in parallel. **7F last** (or after 7B if metrics stubbed).

Solo: [agent-7-solo.md](../../prompts/agent-7-solo.md) = 7A–7D, then 7E if time, then 7F.

## Done-when (Wave 7 cut line)

Must:

1. `observe_app()` is what Explorer/Verifier/Recovery read (not ad-hoc `visible_elements` dicts only).
2. After each important step, a **separate** verifier call produces `VerificationResult` with a real `failure_class`.
3. Recovery emits `AdapterPatch`; curator applies it **only after** the retry verifies.
4. Second run prints `RunMetrics` showing fewer actions and model calls (`reuse_gain`).
5. Live path still has no hardcoded Store B HOW HERE.

Nice: Modal two-branch recovery; dashboard shows step → verify → patch; naive replay baseline fails on Store B.

Defer (brief §25): Store C, OmniParser, Skill schema rewrite, desktop agents.

## Pitch line (after Wave 7)

> SkillShift converts a demonstration into an application-independent Skill, grounds it through a verified Adapter, and reuses that Adapter — updating only the HOW HERE when Store B diverges.
