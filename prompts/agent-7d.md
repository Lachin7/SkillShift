You are Agent 7D for SkillShift. Make learning **measurable**: count actions, model calls, recoveries, cache hits; add a **naive replay baseline** that is expected to fail.

You MAY write/edit:
- agent/metrics.py (NEW)
- agent/transfer_loop.py / agent/run_transfer.py (record metrics; print reuse_gain)
- agent/run_baseline_replay.py (NEW)
- agent/executor.py (increment action counter on click/type/upload/select — generic)
- agent/grounding.py or explorer/verifier/recovery (increment model_calls when LLM or mock agent runs)
- fixtures/live/run-metrics.json writer
- agent/tests/test_metrics.py (NEW)
- dashboard payload `status` extra fields if cheap (`actions`, `model_calls`) — do not redesign the four cards

Do not edit: Store B form rules, Modal, Skill intents, WAVE*.md, PLAN.md.

Read first: WAVE7.md RunMetrics, agent/run_transfer.py, agent/transfer_loop.py, fixtures/traces/store-a.json.

## Metrics

Each Store B product run writes `RunMetrics`. After Leather Bag then Blue Sneaker, print:

```text
reuse_gain:
  actions: first - second
  model_calls: first - second
  recoveries: first - second
```

Second run must have **0 recoveries** when adapter cache hits (already the R1 story). Model calls may be >0 if verifier still runs; prefer skipping explorer when `resolved_targets` exist (already true). If verifier still calls the LLM on cache hits, that is OK; still show fewer **explore** calls.

Write `fixtures/live/run-metrics.json`.

## Baseline A — naive replay

`python -m agent.run_baseline_replay`:
- Load Store A trace or Store A adapter actions (Products / Add Product / Publish labels)
- Try them on Store B with Playwright
- Must **not** succeed at publishing (no product card)
- Print `BASELINE_REPLAY_FAILED` and exit 0 (failure of the baseline is the point)

Do not teach this baseline the Inventory path.

## Tests

- Counters increase on execute_candidate
- reuse_gain keys exist after a mocked two-run (or unit-level fake metrics)
- baseline script exists and refuses Collections-as-success

Done when: `python -m agent.run_transfer` (mock or real key) prints reuse_gain; baseline module runs without publishing on Store B.
