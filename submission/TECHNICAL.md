# Technical appendix

Read after [SUBMISSION.md](../SUBMISSION.md). This is the architecture an automated judge can map onto files.

## Separation that must stay true

| Object | Question it answers | Mutates? | File |
| --- | --- | --- | --- |
| **Skill** | WHAT is the task? | Frozen after learn (4 intents) | `fixtures` / `agent/learner.py` |
| **Adapter** | HOW HERE does this app do it? | Yes — discovered, patched, versioned | `adapters/store_*__publish_product.json` |
| **AppTarget** | Which app, which path, which adapter file? | Config only | `agent/targets.py` |
| **AppObservation** | What is on screen *now*? | Rebuilt every step | `agent/observer.py` |
| **Verification** | Did the *goal* happen? | Independent call | `agent/verifier.py` |

`AppTarget` is allowed to know `/store-c` and `store-c-`. It is **forbidden** to know “publish means Save row.” That is Adapter memory.

Frozen Skill intents (exact strings, both agents use these):

1. `start creating a new sellable item`
2. `provide basic product information`
3. `attach the product image`
4. `make the product publicly available`

## Typed contracts (`agent/models.py`)

Pydantic AI agents are constructed with `output_type=...`. The model cannot return a paragraph and call it a decision.

```python
class CandidateAction(BaseModel):
    target_testid: str          # must exist in current observation
    action: Literal["click", "fill", "upload", "select"]
    value: str | None = None
    rationale: str
    confidence: float

class ObservationControl(BaseModel):
    ref: str
    role: str
    name: str
    enabled: bool = True
    region: str = ""
    value: str = ""             # lets the verifier see an empty required field

class VerificationResult(BaseModel):
    passed: bool
    expected_state: str
    observed_evidence: list[str]
    failure_class: Literal[
        "none", "action_not_executed", "wrong_mapping", "stale_mapping",
        "missing_prerequisite", "validation_error", "navigation_error",
        "ambiguous_state", "unexpected_app_state", "unsupported_concept",
    ]

class AdapterPatch(BaseModel):
    semantic_intent: str
    operation: Literal[
        "replace_mapping", "add_prerequisite",
        "deprecate_rule", "add_navigation_rule",
    ]
    new_targets: list[str]
    new_app_action: str
    evidence: list[str]
    applied: bool = False
```

`apply_patch` in `agent/adapter_curator.py` refuses a patch when verification failed, and refuses `new_targets` that were not in the observation. That is how we stop the Adapter becoming a fiction.

## Runtime loop (`agent/transfer_loop.py`)

Per Skill step, up to `MAX_ATTEMPTS_PER_STEP`:

1. **Cache hit** — `resolved_targets` present → `execute_resolved_targets` (suffix-based *kind*: `-field-name` types the name; it does not choose the control).
2. **Explore** — `explore_step(step, observation, screenshot)` → `ExploreResult`.
3. **Act** — `execute_candidate`.
4. **Details follow-up** — if the step is “provide basic product information” and price/amount is visible but not yet in the trail, fill it. **This is the one mechanical shortcut** in the live path. Documented so it cannot be mistaken for Explorer intelligence.
5. **Verify** — `verify_independent(..., product_name=...)`. Publish steps also hit `/api/store-b-state?app=&title=`.
6. **Diagnose** on miss — `failure_class` from the diagnoser, not from the Explorer.
7. **Recover**
   - `missing_prerequisite` → pick a visible required control, persist `add_prerequisite`, retry finish.
   - `stale_mapping` (saved testid gone) → re-explore, `replace_mapping`, bump `adapter_version`.
   - navigation miss → exclude failed testid, propose another visible one.
8. **Persist** only after `matched=True`. Loop-trace records the failure **and** the resolving row (`recovered click …`).

`--reset` / `SKILLSHIFT_RESET_ADAPTER=1` (`agent/run_transfer.py`) writes `empty_adapter()` before load so a warm file cannot silently skip discovery.

## Grounding and the event-loop split

Playwright sync and Pydantic AI `run_sync` both want an event loop. `run_agent_sync` in `agent/grounding.py` runs the agent in a worker thread. Live runs require a key **or** `SKILLSHIFT_MOCK_LLM=1` (`require_decision_backend`). There is no silent hardcoded Store B fallback.

Model resolution order:

1. `SKILLSHIFT_MODEL` override
2. Gateway **only if** `SKILLSHIFT_USE_GATEWAY=1` *or* no direct key exists
3. First present of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY`

A 403ing gateway key therefore cannot take down a Gemini demo.

## Multimodal payload

Explorer / Verifier / Recovery user parts are:

1. JSON: intent, observation (`controls` with `value`/`enabled`), visible-element summary
2. PNG screenshot via `screenshot_parts`

The mock backend ignores the image and uses DOM signals. The real Gemini path does not.

## Metrics

`agent/metrics.py` counts actions, model calls, recoveries, cache hits, latency. After a cold+cached pair, `fixtures/live/run-metrics.json` and the dashboard `metrics` field get:

```json
{ "first": { "model_calls": 13, "recoveries": 2, "cache_hits": 0 },
  "second": { "model_calls": 3, "recoveries": 0, "cache_hits": 4 },
  "reuse_gain": { "actions": 0, "model_calls": 10, "recoveries": 2 } }
```

Actions stay 7→7 because the clicks still happen. The saving is **thinking**, which is the correct reuse metric.

## Perturbations (DOM contract, not labels)

`fixtures/live/perturbations.json` + `GET/POST /api/perturbations`. Store B polls it. Flags:

| Flag | Old testid gone | New contract |
| --- | --- | --- |
| `rename_publish` | `store-b-go-live` | `store-b-launch-product` (“Launch Product”) |
| `extra_required` | — | `store-b-field-tax-class` gates Go Live |
| `reorder_nav` | `store-b-nav-inventory` | `store-b-nav-catalog` (“Catalog”) |

Cached `resolved_targets` hold testids. Changing only a label would be a no-op. We change the testid so the miss is real.

## File map

```text
agent/models.py              typed Skill / Adapter / Observation / Patch / Metrics
agent/observer.py            AppObservation from visible testids
agent/explorer.py            Pydantic Explorer
agent/verifier.py            independent Verifier + /api/store-b-state
agent/failure_diagnoser.py   FailureClass
agent/recovery.py            constrained recovery action
agent/adapter_curator.py     apply AdapterPatch after verify
agent/transfer_loop.py       explore → act → verify → recover → persist
agent/run_transfer.py        CLI, --reset, .env load, dashboard writer
agent/targets.py             AppTarget registry (B/C/D/E)
agent/grounding.py           validate_candidate, run_agent_sync, model id
agent/executor.py            Playwright hands
agent/metrics.py             reuse_gain
agent/modal_recovery.py      Modal-or-local hypothesis scoring
agent/gateway.py             optional Gateway + decoy-ignore rule
modal_app/                   Modal functions
web/app/store-{a,b,c,d,e}/   synthetic apps
web/app/dashboard/           Skill / App / Adapter / Status + loop_trace
web/app/api/perturbations/   judge flags
web/app/api/store-b-state/   verifier ground truth (?app=&title=)
adapters/                    live per-app memory (emptied by --reset)
docs/evidence/adapters/      frozen copies for judges
```
