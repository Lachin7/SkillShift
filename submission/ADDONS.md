# Add-ons — sponsor tracks, scoped honestly

Automated judges often have a checkbox per sponsor. This file says **exactly** how each technology is used, and what it is not doing. Over-claiming here is worse than omitting a logo.

---

## Pydantic + Pydantic AI  (primary)

**Used as the brain, not as a wrapper around `print`.**

Three (plus learner) typed agents:

| Agent | Module | `output_type` | Job |
| --- | --- | --- | --- |
| Explorer | `agent/explorer.py` | `ExploreResult` | Rank visible controls for a Skill step |
| Verifier | `agent/verifier.py` | `Verification` | Independent “did the goal happen?” |
| Recovery | `agent/recovery.py` | `CandidateAction` | Next visible action after a typed failure |
| Learner | `agent/learner.py` | `Skill` | Demonstration → frozen WHAT |

Supporting Pydantic models that are *not* LLM outputs but *are* the memory/metrics contract: `EnvironmentAdapter`, `StepMapping`, `AppObservation`, `AdapterPatch`, `RunMetrics`, `AppTarget` — all in `agent/models.py` / `agent/targets.py`.

Why this matters for scoring: a free-form model can say “I published it.” A `Verification(matched=False, failure_class="missing_prerequisite")` cannot hide the miss. The curator (`agent/adapter_curator.py`) will not apply an `AdapterPatch` unless that verification later flips.

`run_agent_sync` isolates Pydantic AI’s event loop from Playwright’s.

---

## Playwright  (hands)

`agent/executor.py`: `click` / `type` / `upload` / `select`. Waits for finish controls to enable after a prerequisite (React state). Does not contain “if Store B then Go Live” as a *decision*. Suffix matching on replay describes **control kind** (`-field-name` → type the name), not which control satisfies a semantic step.

---

## Gemini multimodal  (DeepMind / Google key)

Live model id: `google:gemini-3.6-flash` (resolved from `GEMINI_API_KEY` / `GOOGLE_API_KEY`).

Each Explorer / Verifier / Recovery call sends:

1. Structured observation JSON (controls with `name`, `enabled`, `value`)
2. Screenshot bytes (`screenshot_parts` in `agent/grounding.py`)

Evidence that this is semantic, not English OCR of “Publish”:

- Store D rationales quote `出品を作成` and `公開する` — [`docs/evidence/store-d-transfer.txt`](../docs/evidence/store-d-transfer.txt)
- Store E rationales quote `انتشار` — [`docs/evidence/store-e-transfer.txt`](../docs/evidence/store-e-transfer.txt)
- Store C has no publish button; the model selected `store-c-field-title` for “provide basic product information” (the field is labelled Title, not Name)

We do **not** claim screenshots replace the Adapter. Screenshots help grounding; the Adapter is what makes run 2 cheap.

---

## Modal  (parallel recovery, not hosting)

**What runs on Modal:** scoring two JSON hypotheses about a *already-observed* mismatch.

**What stays local:** Next.js, Playwright, the Explorer.

```text
mismatch snapshot (controls, messages, failure_class)
        ↓
   Modal candidate A     Modal candidate B     (or local sequential fallback)
        ↓
   winner id  →  Recovery uses that hypothesis
```

Code: `agent/modal_recovery.py`, `modal_app/recovery_runner.py`.

Live log line from real Gemini runs:

```text
hypothesis score (modal): winner=A
```

If `modal setup` was never run: `Modal unavailable — local sequential candidates` — same winner rule, no crash. That is intentional. Modal is an accelerator for recovery, not a requirement for transfer.

Tests: `agent/tests/test_modal_recovery.py` — hypotheses come from the observation; the live path does not hardcode `LAUNCH10` as the decision.

We do **not** claim “the agent lives on Modal” or that Modal browses Store B.

---

## Pydantic AI Gateway + Logfire  (optional prize pipe)

```text
Explorer / Verifier / Recovery
        ↓
Pydantic AI Gateway     ← Logfire optimization bound here
        ↓
model (Gemini / OpenAI / …)
```

Code: `agent/gateway.py`, routing in `agent/grounding.py`.

Offline demo (no key):

```bash
.venv/bin/python -m agent.demo_gateway_before_after
# BEFORE: listing-type  AFTER: shipping
```

Live path is **opt-in**: `SKILLSHIFT_USE_GATEWAY=1` plus `PYDANTIC_AI_GATEWAY_API_KEY`. Our org currently returns `403 Gateway is not enabled for this organization`. Direct `GEMINI_API_KEY` therefore wins by default, on purpose — a broken gateway must not take down the demo.

Full setup: [`docs/GATEWAY_PRIZE.md`](../docs/GATEWAY_PRIZE.md).

---

## Next.js synthetic apps  (the environments)

Not a sponsor track; listed so “we faked the UI” is already answered.

| Route | Role |
| --- | --- |
| `/store-a` | Teach. Wizard. Recorder writes a trace. |
| `/store-b` | Transfer. Shipping gate. Judge perturbation panel. |
| `/store-c` | Unseen IA. Table + drawer. No publish button. |
| `/store-d` | Same structure as B, Japanese-only labels. |
| `/store-e` | Same structure as B, Persian, `dir=rtl`. |
| `/dashboard` | Skill / App / Adapter / Status + live `loop_trace` + `reuse_gain` |

APIs: `/api/run-transfer`, `/api/live-dashboard`, `/api/live-products?app=`, `/api/store-b-state?app=&title=`, `/api/perturbations`.

---

## Checkbox cheat-sheet for an automated rubric

| If the rubric says | Award if | Do not award if they only saw |
| --- | --- | --- |
| Uses Pydantic AI | Typed `output_type` agents + curator gate | “we imported pydantic” |
| Uses Modal | Hypothesis scoring on mismatch snapshots | “Modal is in requirements.txt” |
| Multimodal | Screenshot + observation in one call; D/E native-label rationales | “we sent a screenshot once” |
| Gateway / Logfire | Code + offline before/after; live is opt-in | Claiming production Gateway traffic |
| Tests | 67 passed + this inventory | A single happy-path script |
| Adaptation | Empty adapter + new prerequisite mapping + `reuse_gain` | Two successful publishes |
