# Tests — what exists, how to run, what a pass means

Automated judges: a green suite is necessary and **not sufficient**. These tests prove the *loop* and the *constraints*. They use `SKILLSHIFT_MOCK_LLM=1` (visible-testid heuristics). Gemini grounding is in [`docs/evidence/`](../docs/evidence/), not here.

## How to run

```bash
# Next.js on :3010 (several tests open Playwright against the live stores)
cd web && npm run build && npx next start -p 3010   # terminal 1

# terminal 2
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_MOCK_LLM=1 \
  .venv/bin/python -m pytest agent/tests -q
```

Recorded result (2026-09-19): **67 passed in 166.73s** — [`docs/evidence/pytest.txt`](../docs/evidence/pytest.txt).

Typecheck / build (no `lint` script exists):

```bash
cd web && npx tsc --noEmit && npm run build
```

## Inventory (67 tests)

### Core loop — `test_transfer.py` (10)

| Test | Proves |
| --- | --- |
| `test_empty_adapter_cold_start` | Live path starts with `mappings: []` |
| `test_validate_candidate_rejects_invented_testid` | Model cannot click a fantasy id |
| `test_explorer_picks_only_visible_testids` | Grounding is observation-bounded |
| `test_recovery_after_collections_prefers_inventory` | Collections trap fails verify; recovery leaves it |
| `test_recovery_shipping_prerequisite_picks_shipping_field` | Blocked publish → shipping control |
| `test_persist_empty_then_mapping` | Adapter file grows only after success |
| `test_verifier_mismatch_on_collections_page` | Wrong page is `wrong_navigation` |
| `test_go_live_blocked_without_shipping` | DOM gate is real; verify = miss |
| `test_go_live_enabled_with_shipping_only` | Promo gate is off for R1; shipping unlocks |
| `test_full_transfer_cold_and_cached` | Two products; second is cache |

### Independent verification — `test_verifier.py` (3)

Collections heading is not “create item.” Blocked Go Live with shipping evidence is `missing_prerequisite`. Legacy `verify_step` still returns the dashboard `Verification` shape.

### Observation — `test_observer.py` (5)

Empty refs skipped. Invented candidates rejected from an `AppObservation`. Explorer grounds only from `controls`. `GET /api/store-b-state` JSON shape is stable.

### Curator — `test_adapter_curator.py` (3)

`add_prerequisite` inserts shipping **without editing Skill intents**. Failed verification → patch refused. Invented patch targets raise.

### Metrics / baseline — `test_metrics.py` (3)

Counters move on `execute_candidate`. `reuse_gain` keys exist. Baseline must not treat Collections as published.

### Perturbations — `test_perturbation.py` (6)

| Test | Proves the judge panel is not theatre |
| --- | --- |
| `test_rename_publish_swaps_testid` | `go-live` absent, `launch-product` present |
| `test_rename_publish_warm_adapter_stale_then_remap` | Warm trail misses → remap |
| `test_stale_mapping_diagnoser_on_missing_testid` | Missing saved id is `stale_mapping`, not a timeout |
| `test_extra_required_warm_adapter_adds_tax` | New gate → `add_prerequisite` |
| `test_reorder_nav_remaps_create_step` | `nav-catalog` replaces `nav-inventory` |
| `test_missing_target_error_is_clean` | Replay of a gone testid is diagnosable |

### Store C — `test_store_c.py` (3)

Never reads Store B’s adapter. Suffix replay of a C trail works. Cold start then cache hit on the table/drawer app.

### Store D / E — `test_store_d.py` (3), `test_store_e.py` (4)

B does not read D/E adapters. Visible copy has **no ASCII letters** (testids/classes excluded). E is `dir=rtl`. Cold then cache.

### Registry — `test_targets.py` (4)

Default target is `store-b`. C/D/E registered with their own adapter files.

### Modal — `test_modal_recovery.py` (3)

Shipping snapshot prefers the shipping hypothesis. Hypotheses are diagnoser-shaped dicts. Live path does **not** hardcode `LAUNCH10` as the winner.

### Gateway — `test_gateway.py` (7)

Decoy detection, filter-visible-for-demo, rule instruction mentions `visible_elements`, gateway vs direct-key precedence, `SKILLSHIFT_MODEL` override, offline before/after script exits 0.

### Hands / teach — `test_executor.py`, `test_learner.py`, `test_replay_a.py`

Playwright can click/fill/upload. Skill loads as `publish_product` and is not an Adapter. Store A replay publishes a catalog item without inventing a shipping step.

## What the mock is allowed to do

The mock Explorer / Verifier / Recovery may key off **control kind / suffix** (`-field-shipping`, `-launch-product`, `-nav-catalog`) so CI is keyless. That is **not** allowed on the live Gemini path. Live decisions come from the model over observation + screenshot.

If a test needs the web and `:3010` is down, helpers `skip` via `WebUnavailable` rather than fail closed. The recorded 67 assumed the server was up.

## Real-model checks (not in pytest)

These are the Gemini runs an automated judge should treat as the grounding proof:

| Check | File |
| --- | --- |
| B cold + cached | `docs/evidence/store-b-cold-and-cached.txt` |
| C cold + cached | `docs/evidence/store-c-cold-and-cached.txt` |
| C reliability 3/3 | `docs/evidence/store-c-reliability.txt` |
| D Japanese | `docs/evidence/store-d-transfer.txt` |
| E Persian | `docs/evidence/store-e-transfer.txt` |
| Perturbations 3/3 | `docs/evidence/perturbations.txt` |
| Baseline fail + verifier no | `docs/evidence/verification-independence.txt` |

Re-run: `python -m agent.run_transfer --reset` with `GEMINI_API_KEY` in `.env`.
