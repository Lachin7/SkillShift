# SkillShift — Build Brief for the Hackathon

## One-line idea

**SkillShift learns a task once from a human demonstration, extracts an app-independent semantic skill, then grounds and adapts that skill to a structurally different unseen application using verification-driven repair and persistent app-specific memory.**

Tagline:

> **Teach the goal once. Let the agent learn the environment.**

---

# 1. What the project is — and is not

## The project is

A controlled research prototype showing that an agent can:

1. observe a successful human demonstration in **Store A**,
2. infer the **semantic task structure**,
3. enter an unseen **Store B**,
4. figure out how Store B implements the same semantic operations,
5. detect when its first interpretation is wrong,
6. repair only the Store B-specific grounding,
7. verify the real outcome,
8. save what it learned,
9. perform the same task again with less exploration.

The core thesis is:

> **SkillShift learns invariant task structure and separately learns how each application grounds that structure. Verification, not model confidence, determines whether adaptation succeeded.**

## The project is NOT

- a general-purpose computer-use agent,
- a raw video-understanding project,
- a hardcoded Store A → Store B script,
- a selector cache,
- a generic multi-agent swarm,
- a full e-commerce product,
- a system that claims to “learn any software.”

The hackathon claim should stay narrow and defensible:

> **Given one successful demonstration of a task in App A, SkillShift extracts a semantic workflow and creates/repairs an adapter that can execute the same task in structurally different App B.**

---

# 2. Demo domain

Use **synthetic seller portals** because they are easy to control, visually clear, and have objective success conditions.

## Store A — teaching environment

Example flow:

1. Products
2. Add Product
3. Enter title
4. Enter price
5. Upload image
6. Set inventory
7. Publish
8. Product visible on storefront

Example labels:

- `Products`
- `Add Product`
- `Publish`

## Store B — unseen environment

Make the structure genuinely different, not just renamed buttons.

Example flow:

1. Inventory
2. Create Listing
3. Multi-step form
4. Enter details
5. Upload media
6. Set inventory
7. Select shipping profile
8. `Activate Listing`
9. Product becomes live

Add one or two decoys:

- `Collections`
- `Save Draft`
- `Catalog`

The agent must not know Store B selectors or mappings in advance.

## Optional Store C — only if there is time

Use a third layout with:

- table-based editing,
- status menu,
- different ordering,
- no one-to-one screen match with Store A.

---

# 3. The key conceptual separation

SkillShift should store **three different kinds of information**.

## A. Semantic Skill = WHAT the job means

The Skill is app-independent.

It should contain things like:

- create a product entity,
- set title,
- set price,
- attach an image,
- satisfy publication prerequisites,
- transition product to published,
- verify the product is purchasable.

It must NOT contain:

- Store A page names,
- selectors,
- button labels like `Publish`,
- Store B labels like `Activate Listing`,
- coordinates,
- URLs.

Example:

```python
from pydantic import BaseModel
from typing import Literal

class SemanticStep(BaseModel):
    id: str
    intent: Literal[
        "create_entity",
        "set_attribute",
        "attach_asset",
        "transition_state",
        "verify_state",
    ]
    entity: str
    inputs: dict[str, str] = {}
    preconditions: list[str] = []
    postconditions: list[str] = []
    depends_on: list[str] = []

class Skill(BaseModel):
    name: str
    objective: str
    parameters: list[str]
    steps: list[SemanticStep]
    success_contract: list[str]
```

Example skill:

```yaml
objective: Publish a purchasable product

steps:
  - id: create_product
    intent: create_entity
    entity: product
    postconditions:
      - product_exists

  - id: set_title
    intent: set_attribute
    entity: product.title
    inputs:
      value: "{{ product_name }}"

  - id: set_price
    intent: set_attribute
    entity: product.price
    inputs:
      value: "{{ price }}"

  - id: attach_image
    intent: attach_asset
    entity: product.image

  - id: publish
    intent: transition_state
    entity: product
    inputs:
      target_state: published

  - id: verify
    intent: verify_state
    entity: product

success_contract:
  - product_exists
  - product_title_matches
  - product_price_matches
  - product_is_visible
  - product_is_purchasable
```

---

## B. App Adapter = HOW this app implements the Skill

The Adapter is application-specific knowledge discovered during execution.

It answers:

> “How does Store B realise this semantic step?”

Example:

```python
class AdapterRule(BaseModel):
    semantic_step_id: str
    locator_strategy: str
    locator: str
    preconditions: list[str] = []
    expected_effect: str
    successes: int = 0
    failures: int = 0
    confidence: float = 0.5
    provenance: list[str] = []

class AppAdapter(BaseModel):
    app_signature: str
    rules: list[AdapterRule]
    known_prerequisites: list[str] = []
    navigation_rules: list[str] = []
    version: int = 1
```

Possible learned Store B adapter:

```yaml
app_signature: store-b

rules:
  - semantic_step_id: create_product
    locator_strategy: role_name
    locator: button[name="Create Listing"]
    expected_effect: product creation flow becomes available

  - semantic_step_id: publish
    locator_strategy: role_name
    locator: button[name="Activate Listing"]
    preconditions:
      - inventory_set
      - shipping_profile_selected
    expected_effect: listing status becomes Active
```

The key rule:

> **Do not rewrite the Skill when Store B behaves differently. Update the Adapter unless the semantic Skill itself is genuinely wrong.**

---

## C. Execution Trace = WHAT actually happened

Store every meaningful observation, action, result and verification.

```python
class TraceEvent(BaseModel):
    event_id: str
    parent_id: str | None = None
    phase: Literal[
        "plan",
        "observe",
        "retrieve_adapter",
        "ground",
        "act",
        "verify",
        "diagnose",
        "repair",
        "learn",
    ]
    semantic_step_id: str | None = None
    observation: dict | None = None
    decision: dict | None = None
    tool_call: dict | None = None
    result: Literal["success", "failure", "uncertain"] | None = None
    verification_evidence: list[str] = []
    screenshot_ref: str | None = None
    cost: float = 0.0
    latency_ms: int = 0
```

This gives you a real trace viewer and makes the project measurable.

---

# 4. The actual agent architecture

Do NOT make one huge agent that does everything.

Use three conceptual loops.

## Loop A — Skill induction

Input:

- Store A demonstration,
- UI observations,
- action trace,
- before/after screenshots.

Question:

> **What app-independent procedure was demonstrated?**

Output:

- `Skill`

This loop must remove Store A-specific wording.

---

## Loop B — Target-app grounding and execution

Input:

- semantic `Skill`,
- current Store B observation,
- existing Store B adapter if available.

Question:

> **How can Store B realise the next semantic step?**

Output:

- a grounded candidate action or action sequence.

This is where transfer happens.

---

## Loop C — Verification and learning

Input:

- expected postcondition,
- pre-action state,
- post-action state,
- trace.

Question:

> **Did the intended semantic state really occur? If not, why?**

Output:

- verified/not verified,
- failure class,
- proposed adapter patch,
- confidence update.

---

# 5. Treat the applications as black boxes

The agent should NOT inspect Store B source code.

The agent may observe:

- screenshot,
- accessibility tree,
- visible labels and controls,
- page title / URL,
- field values,
- state badges,
- visible validation errors,
- DOM mutations,
- optional synthetic test API for final verification only.

The agent should interact through Playwright like a user.

This is stronger than a system that knows Store B routes or test IDs ahead of time.

---

# 6. Recorder / teaching input

For the hackathon MVP, do NOT attempt full arbitrary video understanding.

Use:

- screen recording for the judge/demo,
- instrumented browser recording for the actual system.

Capture after meaningful actions:

- screenshot,
- accessibility snapshot,
- clicked element,
- typed value,
- URL/title,
- focused element,
- visible success/error messages,
- form state.

The important learner question is:

> **What semantic state changed, and what evidence supports that interpretation?**

Not:

> “What did the user click?”

This is inspired by human-taught GUI-agent work such as ShowUI-Aloha and UI-Mate, but your contribution is downstream transfer and adapter learning.

---

# 7. Observation tools

Do not expose only raw Playwright calls to the reasoning layer.

Create a small semantic action/observation API.

## `observe_app()`

Return a compact model of the current page:

```json
{
  "screen": "listing_editor",
  "regions": ["navigation", "details", "status"],
  "controls": [
    {
      "ref": "e17",
      "role": "button",
      "name": "Activate Listing",
      "region": "status"
    }
  ],
  "state": {
    "publication_status": "draft"
  }
}
```

## `inspect_control(ref)`

Return:

- surrounding labels,
- current enabled/disabled state,
- relation to nearby form,
- any associated help text,
- previous observed effects if known.

## `find_capability(goal)`

Example:

```text
find_capability("transition product to published")
```

Search:

- current accessibility tree,
- visible navigation labels,
- adapter memory,
- previous traces,
- current page semantics.

## `act(...)`

Typed actions only:

- `Navigate`
- `EnterValue`
- `SelectOption`
- `AttachResource`
- `InvokeCapability`
- `ConfirmAction`

## `verify(...)`

Example:

```python
verify(
    expected="product.status == published",
    evidence_sources=["ui", "reload", "test_api"]
)
```

Playwright remains the physical executor, but raw Playwright should not be the reasoning vocabulary.

---

# 8. Independent verification

This is one of the most important improvements.

Do NOT let the same reasoning step:

1. choose an action,
2. execute it,
3. decide that it succeeded.

Use a separate verifier call/session.

```python
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
    ]
```

Verification hierarchy:

1. UI evidence
   - badge changed,
   - field value present,
   - row appeared,
   - confirmation state visible.

2. Behavioural evidence
   - entity can be reopened,
   - state survives navigation/reload.

3. Backend/test API evidence
   - only for synthetic demo apps.

4. Persistence check
   - reload page and verify the result is still true.

Do NOT count:

> “The agent clicked Publish”

as success.

Success means:

> **The success contract is actually satisfied.**

---

# 9. Failure taxonomy

Do not use a generic “try again” recovery prompt.

Classify failures first.

| Failure | Meaning | Recovery |
|---|---|---|
| wrong_mapping | wrong UI control selected | generate alternative grounding candidates |
| stale_mapping | saved rule no longer works | refresh observation and remap |
| missing_prerequisite | Store B requires an extra step | satisfy prerequisite and patch adapter |
| validation_error | supplied value rejected | inspect validation message and change input |
| navigation_error | control exists elsewhere | re-plan navigation only |
| action_not_executed | click/type did not take effect | retry physically |
| ambiguous_state | verifier cannot tell | collect more evidence |
| unsupported_concept | Store B cannot express task step | stop and report capability gap |
| risk_requires_approval | irreversible/high-risk action | ask for approval |

The hard part of SkillShift is not clicking.

The interesting problem is:

> **What failed, and which layer should change?**

Wrong mapping → update Adapter  
Missing prerequisite → update Store-B procedure  
Transient UI issue → retry  
Bad input → adjust/request input  
Bad semantic skill → only then consider revising Skill

---

# 10. Core adaptation logic

The Store B adapter should begin empty or incomplete.

Example:

```text
Store B Adapter = {}
```

For semantic step:

```text
start creating a sellable item
```

The grounding agent observes:

```text
Collections
Inventory
Orders
Analytics
```

It proposes candidates:

```text
Inventory      0.62
Collections    0.28
Orders         0.10
```

It chooses one and acts.

Then the verifier compares:

Expected:

> a product creation workflow or control should now be available

Observed:

> collection management screen

Result:

```text
passed = false
failure_class = wrong_mapping
```

Recovery proposes a new candidate.

If the next route reaches:

```text
Inventory → Create Listing
```

and the verifier passes, save that mapping into the Adapter.

---

# 11. Workflow adaptation, not only label adaptation

This makes the project much more interesting.

Store B should have a requirement Store A did not have.

Example:

Store A:

```text
create
→ details
→ image
→ price
→ publish
```

Store B:

```text
create
→ details
→ image
→ price
→ inventory
→ SHIPPING PROFILE
→ activate
```

The agent reaches `Activate Listing`.

The app rejects:

> Shipping profile required.

The verifier should classify:

```text
failure_class = missing_prerequisite
```

Then recovery should infer:

> Store B has an environment-specific prerequisite not represented in the original ordering.

The Skill can stay:

```text
transition product to published
```

The Store B adapter grows:

```text
Before publish in Store B:
- ensure inventory exists
- ensure shipping profile selected
- invoke Activate Listing
```

This is procedural adaptation, not synonym matching.

---

# 12. Adapter learning as evidence accumulation

Do NOT permanently trust a mapping because it worked once.

Use a lifecycle:

```text
proposed
→ sandbox_verified
→ provisional
→ reused
→ trusted

or

→ invalidated
```

Suggested rule structure:

```python
class AdapterRule(BaseModel):
    concept: str
    locator: str
    preconditions: list[str]
    verification_rule: str
    successes: int
    failures: int
    confidence: float
    provenance: list[str]
    status: Literal[
        "candidate",
        "sandbox_verified",
        "provisional",
        "reusable",
        "trusted",
        "deprecated",
    ]
```

Confidence can consider:

- verified successful executions,
- different product inputs,
- different app states,
- recovery count,
- selector stability,
- contradictory evidence.

The live app state always outranks stored adapter memory.

---

# 13. Memory model

Persist four kinds of memory.

## Semantic memory

General task structure:

> Publishing requires an entity to exist and reach an externally visible state.

## Procedural memory

App-specific procedure:

> In Store B, inventory and shipping profile must precede activation.

## Episodic memory

A concrete attempt:

> Run 17: `Save Draft` left status as Draft; `Activate Listing` changed it to Active.

## Failure memory

Known-bad assumptions:

> `Save Draft` does not implement publication.

Priority:

```text
authoritative current observation
> repeatedly verified adapter rule
> provisional adapter rule
> similar-app prior
> model guess
```

---

# 14. Pydantic AI's role

Pydantic AI should be the structured reasoning/orchestration layer, not merely JSON validation.

Use typed agents/contracts for:

- Skill Inducer
- Planner
- Grounder / Explorer
- Verifier
- Failure Diagnoser
- Recovery proposer
- Adapter Curator

Examples of typed outputs:

```text
Demonstration
→ Agent[Skill]

Skill + Store B observation
→ Agent[GroundingCandidate]

Post-action state
→ Agent[VerificationResult]

Failure
→ Agent[AdapterPatch]
```

This gives you a strong partner story:

> **Pydantic AI defines the contracts between every stage of learning, grounding, verification and recovery.**

---

# 15. Modal's role

Modal should not merely host the backend.

Use Modal for **bounded parallel recovery experiments**.

Example failure:

```text
Goal: publish product

Hypothesis A:
"Activate Listing" is the publish action

Hypothesis B:
"Set Status → Active" is the publish action

Hypothesis C:
publishing requires inventory first
```

Clone/reset Store B state and test candidates separately.

Each branch returns:

```python
class RecoveryHypothesisResult(BaseModel):
    hypothesis: str
    proposed_actions: list[dict]
    verified_success: bool
    evidence: list[str]
    action_cost: float
    destructive_risk: float
```

Rank roughly by:

```text
verified_success
- action_cost
- destructive_risk
- assumptions
- divergence_from_semantic_skill
```

One coordinator chooses the winning branch.

Important:

> Branches should not independently mutate the same live browser.

For the hackathon, two recovery branches are enough.

Sponsor story:

> **Modal gives SkillShift isolated scratch environments where it can test competing interpretations of unfamiliar software before committing a learned adapter rule.**

---

# 16. Baselines

Judges may otherwise think the demo is scripted.

Implement at least 2–3 lightweight baselines.

## Baseline A — Naive replay

Replay Store A actions on Store B.

Expected: fail.

## Baseline B — Fresh agent

Ask an agent to solve Store B from scratch without Store A demonstration or learned Skill.

Measure:

- actions,
- model calls,
- latency,
- success.

## Baseline C — SkillShift without persistent adapter

Give semantic Skill but do not reuse Store B memory.

## Full SkillShift

Skill + adaptation + verification + persistent adapter.

---

# 17. Metrics

Useful metrics:

- Store B first-attempt success,
- final success after adaptation,
- second-run success,
- actions to completion,
- model calls,
- recovery branches,
- false-success rate,
- adapter reuse rate,
- verification precision,
- repeated-action rate,
- latency,
- cost.

Most important demo metric:

```text
reuse_gain =
cost(second Store B run without learned adapter)
-
cost(second Store B run with learned adapter)
```

Visually show:

```text
First Store B run:
- exploration required
- 1 recovery
- 12 actions
- 4 model decisions

Second Store B run:
- adapter reused
- 0 recovery
- 7 actions
- 1 model decision
```

---

# 18. Useful ablations if time allows

Remove one component:

- no semantic abstraction,
- no verifier,
- no persistent adapter,
- no recovery,
- no Modal parallel hypothesis testing,
- screenshot-only observation,
- accessibility-only observation.

The goal is not a full paper. One small chart or table is enough to prove the architecture matters.

---

# 19. Synthetic test apps

Build local stores rather than real Shopify-like systems.

Reasons:

- deterministic,
- no authentication,
- no anti-bot issues,
- resettable state,
- objective backend labels,
- easy to perturb.

Expose a test-only state endpoint:

```json
{
  "product_exists": true,
  "title": "Blue Lamp",
  "price": 29.99,
  "inventory": 8,
  "status": "published",
  "purchasable": true
}
```

This endpoint is for verifier ground truth, not for planning.

Inject controlled changes:

- renamed controls,
- reordered screens,
- extra prerequisite,
- delayed state transition,
- duplicate/ambiguous buttons,
- stale adapter mapping,
- transient error.

---

# 20. Demo sequence

## Scene 1 — Teach

Human demonstrates in Store A:

> “Create and publish this lamp.”

Recorder captures actions + state changes.

Show:

```text
LEARNED SKILL

1. Create product
2. Set title
3. Set price
4. Attach image
5. Set inventory
6. Transition to published
7. Verify purchasable state
```

Emphasize:

> No Store A labels/selectors remain in the Skill.

---

## Scene 2 — Transfer

Open unseen Store B.

Agent loads:

```text
Skill: Publish Product
Store B adapter: empty / incomplete
```

It observes the UI.

Example:

```text
Collections
Inventory
Orders
```

It grounds the next semantic step and starts execution.

---

## Scene 3 — Real failure

Do not script the recovery constant.

Use a real difference.

Best failure:

> Store B requires inventory/shipping before activation.

The agent attempts publication.

Store B rejects it.

Verifier outputs:

```text
FAILED

failure_class:
missing_prerequisite

evidence:
"Shipping profile required"
```

---

## Scene 4 — Recovery

Generate two bounded hypotheses.

Example:

```text
A: choose shipping profile then activate
B: use Save Draft and reopen
```

Modal branches test both.

Show:

```text
Hypothesis A  ✅ verified
Hypothesis B  ❌ still draft
```

Commit A.

Adapter v1 updated.

---

## Scene 5 — Verify

Verifier checks:

```text
Status = Active
Product visible in storefront
Reload still Active
Backend test state = published
```

Show:

```text
SUCCESS CONTRACT VERIFIED ✓
```

---

## Scene 6 — Prove learning

Give a second product.

Now:

```text
Store B adapter found
Known prerequisite: shipping profile
Exploration skipped
Recovery skipped
```

The second execution completes directly.

This is the key moment:

> **The system learned something reusable about Store B.**

---

## Optional Scene 7 — Invalidation

Rename `Activate Listing` → `Launch Product`.

Stored mapping fails.

SkillShift:

```text
stale mapping detected
→ remap control
→ verify
→ old rule deprecated
→ new rule saved
```

This proves the project is more than selector caching.

---

# 21. What should be real vs mocked

## Must be real

- demo → semantic Skill generation,
- live Store B observation,
- model-selected grounding,
- Playwright execution,
- independent verification,
- failure classification,
- adapter patch generation,
- adapter persistence,
- faster second run.

## Can be controlled/synthetic

- Store A and Store B,
- product data,
- product images,
- test API,
- specific failure scenario,
- app resets.

## Should NOT drive the live run

Remove live dependency on:

- hardcoded `adapter.wrong.json`,
- `RECOVERED_ACTION = ...`,
- `if "go live" then click store-b-go-live`,
- pre-known shipping lessons,
- forced first wrong guess.

Fixtures are okay for tests, but the live agent should discover these mappings.

---

# 22. Recommended repo inspirations

Use these as architecture/inspiration, not as complete dependencies unless needed.

## ShowUI-Aloha

GitHub:

https://github.com/showlab/ShowUI-Aloha

Use for:

- demonstration recording ideas,
- semantic trace format,
- recorder → learner → planner → actor structure.

Do NOT copy their entire OS-level agent.

---

## UI-Mate

GitHub:

https://github.com/Tencent/UI-Mate

Use for:

- “demonstration as advice, not script,”
- replanning against live UI state,
- demonstration-guided computer use.

Do NOT run their large model unless absolutely necessary.

---

## EvoSkill-GUI

GitHub:

https://github.com/ZJU-REAL/EvoSkill-GUI

Use for:

- structured skill packages,
- reflect → revise → reuse,
- keeping recovery/failure knowledge separate,
- versioned procedural memory.

This is the most relevant conceptual inspiration for the adapter evolution loop.

---

## Understudy

GitHub:

https://github.com/understudy-ai/understudy

Use for:

- teach-once UX,
- persistent learned skills,
- how to present generalisation.

Your differentiation should be stronger emphasis on:

- explicit semantic Skill vs environment Adapter,
- independently verified adaptation,
- procedural differences between apps,
- evidence-backed adapter memory.

---

## Browser Use

GitHub:

https://github.com/browser-use/browser-use

Use for:

- browser-agent patterns,
- screenshots,
- browser execution ideas.

For this MVP, plain Playwright may be simpler.

---

## Stagehand

GitHub:

https://github.com/browserbase/stagehand

Alternative browser execution framework if useful.

Do not use Stagehand and Browser Use together unless there is a clear reason.

---

## OmniParser

GitHub:

https://github.com/microsoft/OmniParser

Potential future inspiration for pure-vision GUI grounding.

Do NOT make this part of MVP unless everything else is working.

---

# 23. Recommended file structure

```text
skillshift/

├── apps/
│   ├── store-a/
│   ├── store-b/
│   └── dashboard/
│
├── agent/
│   ├── models.py
│   ├── skill_inducer.py
│   ├── planner.py
│   ├── observer.py
│   ├── grounder.py
│   ├── executor.py
│   ├── verifier.py
│   ├── failure_diagnoser.py
│   ├── recovery.py
│   └── adapter_curator.py
│
├── recorder/
│   ├── capture.py
│   └── trace_parser.py
│
├── memory/
│   ├── skills/
│   ├── adapters/
│   ├── traces/
│   └── failures/
│
├── modal/
│   └── recovery_runner.py
│
├── tests/
│   ├── baseline_replay.py
│   ├── baseline_fresh_agent.py
│   └── transfer_eval.py
│
└── README.md
```

---

# 24. Build order from current state

## Priority 0 — remove fake adaptation from the live path

Audit the code for:

- hardcoded Store B test IDs in reasoning logic,
- fixed wrong adapter fixtures,
- hardcoded recovery constants,
- predefined Store B lessons.

Keep only generic browser actions and test fixtures.

---

## Priority 1 — real Store B grounding

Given:

- semantic step,
- screenshot,
- accessibility/visible controls,

have a Pydantic AI agent return a structured candidate.

Then Playwright executes the model-selected target.

No Store B-specific decision should live in executor code.

---

## Priority 2 — independent verifier

After every important step:

- collect post-action state,
- compare against semantic postcondition,
- produce `VerificationResult`.

Do not continue blindly.

---

## Priority 3 — real failure diagnosis

Implement at least:

- `wrong_mapping`,
- `missing_prerequisite`,
- `validation_error`,
- `stale_mapping`.

---

## Priority 4 — adapter patch

Recovery should propose a structured patch:

```python
class AdapterPatch(BaseModel):
    semantic_step_id: str
    operation: Literal[
        "replace_mapping",
        "add_prerequisite",
        "deprecate_rule",
        "add_navigation_rule",
    ]
    old_rule: dict | None
    new_rule: dict
    evidence: list[str]
```

Apply only after verification.

---

## Priority 5 — persistence + second-run proof

Save Store B adapter.

Second run must:

- retrieve adapter,
- skip known exploration,
- use learned prerequisite,
- require fewer actions/model calls.

---

## Priority 6 — Modal recovery branch

After a failure:

- generate 2 candidate hypotheses,
- execute each in isolated/reset Store B state,
- verify each,
- choose winning patch.

This is enough for the Modal prize story.

---

## Priority 7 — trace UI / polish

Only after the actual adaptation loop works.

Show:

```text
Semantic step
→ candidate mapping
→ action
→ verification
→ failure class
→ recovery hypotheses
→ winning patch
→ adapter version
```

---

# 25. Hackathon MVP cut line

## Must have

- Store A and Store B,
- one human demonstration,
- semantic Skill generation,
- Store B observation/grounding,
- one real mismatch,
- correct failure classification,
- adapter repair,
- independent verification,
- persisted adapter,
- faster/recovery-free second run,
- real Pydantic AI reasoning,
- real Modal recovery experiment,
- public GitHub repo,
- good README,
- 2-minute demo.

## Nice to have

- Store C,
- adapter confidence lifecycle,
- trace visualisation,
- ablation table,
- controlled invalidation,
- app-family priors.

## Defer

- arbitrary desktop software,
- production authentication,
- full raw video understanding,
- general-purpose software discovery,
- irreversible real-world transactions,
- long-term user-specific memory.

---

# 26. Strongest technical framing

Use this in the README and pitch:

> **SkillShift converts human demonstrations into application-independent semantic skills, grounds those skills through application-specific adapters, and improves those adapters from independently verified execution trajectories.**

Simpler version:

> **Most automation learns the interface. SkillShift learns the task, then learns each interface separately.**

Even simpler:

> **Teach the goal once. Let the agent learn the environment.**

---

# 27. Why this is technically interesting

The underlying concepts are:

- learning from demonstration,
- semantic skill abstraction,
- task transfer,
- cross-environment generalisation,
- GUI grounding,
- closed-loop agent execution,
- independent verification,
- failure attribution,
- procedural adaptation,
- self-repair,
- persistent procedural memory,
- bounded parallel search,
- evidence-backed learning,
- adapter versioning.

The hard problem is not clicking buttons.

The hard problem is:

> **When execution diverges from expectation, identify whether the problem is grounding, prerequisites, data, navigation, transient execution, or the semantic Skill itself — and update only the correct layer.**

That is the real research/agentic substance.

---

# 28. One-line mental model for the coding agent

When implementing any feature, ask:

> **Does this help prove that SkillShift learned task semantics once, learned Store B-specific procedure separately, verified the outcome independently, and reused that knowledge later?**

If not, it is probably not necessary for the hackathon MVP.
