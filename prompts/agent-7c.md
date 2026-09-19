You are Agent 7C for SkillShift. Recovery must emit an **AdapterPatch**; the curator applies it **only after** the retry verifies. Skill never mutates.

You MAY write/edit:
- agent/adapter_curator.py (NEW)
- agent/recovery.py (propose_recovery may stay; add patch builder)
- agent/adapter.py (upsert + status/successes on StepMapping)
- agent/models.py (StepMapping optional status/successes/failures if not done)
- agent/transfer_loop.py (apply patch after verified retry)
- adapters/store_b__publish_product.json shape after a run
- fixtures/failures/ or adapters/ lessons list (failure memory: append strings, no Store B spoilers authored in advance)
- agent/tests/test_adapter_curator.py (NEW)

Do not edit: Store A/B page layouts, explorer.py, verifier.py (unless patch needs a field), modal_app/, WAVE*.md, PLAN.md.

Read first: WAVE7.md AdapterPatch, agent/recovery.py, agent/adapter.py, agent/transfer_loop.py, agent/models.py StepMapping.

## Curator rules

```text
authoritative current observation
> verified adapter rule
> provisional rule
> model guess
```

Operations:
- `replace_mapping` — wrong_mapping / stale_mapping: rewrite `resolved_targets` for that semantic_intent
- `add_prerequisite` — missing_prerequisite: insert mapping (shipping intent string already used: `satisfy environment prerequisite: shipping category`) **before** publish; do not edit Skill steps
- `deprecate_rule` — optional: mark old targets deprecated if replaced
- `add_navigation_rule` — extra click in the create-item trail (Inventory then Create Listing)

Apply patch only if `Verification.matched` (or VerificationResult.passed) after the patched actions.

On first verified save: `status=provisional`, `successes=1`.
On cached second-run success: `status=reusable` (or `trusted`), increment successes.

## Failure memory

Append diagnoser hypothesis to `failure_lessons` (already on EnvironmentAdapter). Do not pre-seed “Collections is wrong” in repo JSON for the live run.

## Tests

- Patch with `add_prerequisite` inserts shipping mapping and leaves four Skill intents untouched
- Curator refuses to apply patch when verification failed
- Invented targets in patch.new_targets raise like grounding validation

Done when: cold transfer still publishes; adapter JSON contains patched mappings with `resolved_targets` and status; Skill JSON unchanged.
