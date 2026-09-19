# `agent/` — Agent B

Pydantic models, Explorer / Verifier / Recovery (Pydantic AI), Playwright hands, tests.

**You own this directory plus `fixtures/` and sample files in `adapters/`.**

## Real Store B transfer (R1)

Cold start uses an **empty** adapter. The loop is:

```text
Skill step → screenshot + visible elements → Explorer → act → Verifier
  → match? save mapping : Recovery → retry
```

Requires either a real API key or the CI mock:

```bash
# Offline / CI mock (constrained heuristics, still picks from visible testids)
SKILLSHIFT_MOCK_LLM=1 SKILLSHIFT_WEB_URL=http://localhost:3010 \
  .venv/bin/python -m agent.run_transfer

# Real multimodal grounding
export GEMINI_API_KEY=...
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 \
  SKILLSHIFT_DEMO_PAUSE=1.5 SKILLSHIFT_DEMO_HOLD=4 \
  .venv/bin/python -m agent.run_transfer
```

Shipping is the hero adaptation: Go Live blocks until a shipping category is set; recovery discovers that prerequisite and persists it. Campaign / Modal are deferred (R2).

`SKILLSHIFT_HEADED=1` for a visible browser. Headless skips pauses.

## Pydantic Gateway (optional prize path)

If `PYDANTIC_AI_GATEWAY_API_KEY` is set, Explorer/Verifier/Recovery use a `gateway/…` model so Logfire optimizations can change picks **without editing code**. See [docs/GATEWAY_PRIZE.md](../docs/GATEWAY_PRIZE.md).

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

Read: [../ARCHITECTURE.md](../ARCHITECTURE.md), [../CONTRACT.md](../CONTRACT.md).
