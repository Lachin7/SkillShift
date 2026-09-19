# `agent/` — Agent B

Pydantic models, Explorer / Verifier / Recovery (Pydantic AI), Playwright hands, tests.

**You own this directory plus `fixtures/` and sample files in `adapters/`.**

## Real Store B transfer (R1)

Cold start uses an **empty** adapter. The loop is:

```text
Skill step → screenshot + visible elements → Explorer → act → Verifier
  → match? save mapping : Recovery → retry
```

Requires either a real API key or the CI mock. The key is read from the repo-root
`.env` automatically; exported variables still win.

```bash
# Offline / CI mock (constrained heuristics, still picks from visible testids)
SKILLSHIFT_MOCK_LLM=1 SKILLSHIFT_WEB_URL=http://localhost:3010 \
  .venv/bin/python -m agent.run_transfer

# Real multimodal grounding
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 \
  SKILLSHIFT_DEMO_PAUSE=0.25 SKILLSHIFT_DEMO_HOLD=1.2 \
  .venv/bin/python -m agent.run_transfer --reset
```

**Run `--reset` before any demo.** A warm adapter makes the run print
"Cached run only" and skip the entire cold-start beat — no exploration, no
shipping discovery. `--reset` (or `SKILLSHIFT_RESET_ADAPTER=1`) empties the
current target's adapter file first. Pick the app with
`SKILLSHIFT_TARGET_APP=store-c|store-d|store-e`.

Shipping is the hero adaptation: Go Live blocks until a shipping category is set; recovery discovers that prerequisite and persists it. Campaign / Modal are deferred (R2).

`SKILLSHIFT_HEADED=1` for a visible browser. Headless skips pauses.

## Pydantic Gateway (optional prize path)

With `PYDANTIC_AI_GATEWAY_API_KEY` set **and** `SKILLSHIFT_USE_GATEWAY=1`, Explorer/Verifier/Recovery use a `gateway/…` model so Logfire optimizations can change picks **without editing code**. See [docs/GATEWAY_PRIZE.md](../docs/GATEWAY_PRIZE.md).

The opt-in matters: a gateway key that the org has not enabled answers `403`, and while the gateway merely being present outranked `GEMINI_API_KEY` that failure took down every run. Direct keys now win unless the gateway is explicitly requested (or is the only key available).

```bash
.venv/bin/python -m agent.demo_gateway_before_after
```

## Modules

| File | Role |
| --- | --- |
| `explorer.py` | Skill step → `CandidateAction` from visible elements |
| `verifier.py` | Structured `Verification` (incl. `mismatch_type`) |
| `recovery.py` | Next action after mismatch; adapter persist |
| `transfer_loop.py` | Explore → Act → Verify → Recover → Persist |
| `executor.py` | Playwright hands only |
| `grounding.py` | Shared validation / screenshot parts |

Read: [../ARCHITECTURE.md](../ARCHITECTURE.md), [../docs/build/CONTRACT.md](../docs/build/CONTRACT.md).
