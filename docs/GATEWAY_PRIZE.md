# Pydantic Gateway + Modal prize layer

Branch: `feat/gateway-prize-layer`

This does **not** change Skill / Adapter / Store B. It adds an optional pipe:

```text
Explorer / Verifier / Recovery
        ↓
Pydantic AI Gateway   ← Logfire optimization toggled here
        ↓
Model (your key or Modal BYOK)
```

## What we added in code

| File | Job |
| --- | --- |
| `agent/gateway.py` | Gateway model id + **decoy-ignore rule text** to paste in Logfire |
| `agent/grounding.py` | If `PYDANTIC_AI_GATEWAY_API_KEY` is set → use `gateway/…` model |
| `agent/demo_gateway_before_after.py` | Offline before/after (no key needed) |
| `agent/tests/test_gateway.py` | Unit tests |

Existing Modal parallel recovery (`modal_app/`) stays as-is for the Modal checkbox.

## Offline verify (always works)

```bash
.venv/bin/python -m agent.demo_gateway_before_after
.venv/bin/python -m pytest agent/tests/test_gateway.py -q
```

You should see BEFORE picking `listing-type` and AFTER picking `shipping`.

## Live prize path (needs your Logfire account)

1. Sign up / open Gateway: [logfire.pydantic.dev](https://logfire.pydantic.dev)  
   Docs: [Pydantic AI Gateway](https://pydantic.dev/docs/ai/overview/gateway/)
2. Create a Gateway API key.
3. Put in `.env` (never commit):

```bash
PYDANTIC_AI_GATEWAY_API_KEY=pylf_v_...
# optional override:
# SKILLSHIFT_GATEWAY_MODEL=gateway/openai:gpt-4o
# or Modal/Groq BYOK route, e.g.:
# SKILLSHIFT_GATEWAY_MODEL=gateway/groq:openai/gpt-oss-120b
```

4. In Logfire → Gateway → Optimizations → New, paste the instruction from:

```bash
.venv/bin/python -c "from agent.gateway import DECOY_IGNORE_RULE_INSTRUCTION; print(DECOY_IGNORE_RULE_INSTRUCTION)"
```

5. **Bind the rule to your endpoint** (easy to miss).
6. Run the same Explorer prompt twice (rule off, then on). Save both Logfire traces.

## Transfer still works without Gateway

```bash
SKILLSHIFT_MOCK_LLM=1 SKILLSHIFT_WEB_URL=http://localhost:3010 \
  .venv/bin/python -m agent.run_transfer
```

Direct `GEMINI_API_KEY` / etc. still work when no Gateway key is set.

## Merge to main when

- [ ] `pytest agent/tests/test_gateway.py` green  
- [ ] `python -m agent.demo_gateway_before_after` exits 0  
- [ ] (Prize) Two Logfire traces with rule off/on  
- [ ] (Prize) Modal endpoint listed if you used Modal BYOK  
