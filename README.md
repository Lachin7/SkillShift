# SkillShift

```text
Skill   = WHAT     (app-agnostic — frozen)
Adapter = HOW HERE (app-specific — discovered, patched, remembered)
```

Teach once. Transfer to an unseen store with an **empty** adapter. The agent grounds from live UI + screenshot, verifies the real outcome, repairs on failure (e.g. a shipping rule the skill never mentioned), and reuses that memory on the next product.

**Repo:** [github.com/Lachin7/SkillShift](https://github.com/Lachin7/SkillShift)

---

## For judges — read in this order

| # | Open this | What it is |
| --- | --- | --- |
| 1 | **[SUBMISSION.md](SUBMISSION.md)** | Full write-up: claim, evidence, tests, add-ons, scorecard |
| 2 | **[submission/TECHNICAL.md](submission/TECHNICAL.md)** | Schemas, explore→verify→recover loop, file map |
| 3 | **[submission/TESTS.md](submission/TESTS.md)** | 67 tests and what each family proves |
| 4 | **[submission/ADDONS.md](submission/ADDONS.md)** | Pydantic AI · Gemini · Playwright · Modal · Gateway |
| 5 | **[docs/EVIDENCE.md](docs/EVIDENCE.md)** | Raw transcripts (redirected, not typed) |

Quick checks: [docs/JUDGE_SCORECARD.md](docs/JUDGE_SCORECARD.md) · spoken demo: [PITCH.md](PITCH.md)

Do **not** use `docs/build/` or `prompts/` for judging — those are internal build notes.

---

## Run locally

```bash
# terminal 1
cd web && npm install && npm run build && npx next start -p 3010

# terminal 2 (once)
python3 -m venv .venv && .venv/bin/pip install -r agent/requirements.txt
.venv/bin/playwright install chromium
# GEMINI_API_KEY=... in .env

# cold start — --reset matters
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 \
  .venv/bin/python -m agent.run_transfer --reset

# tests (no key)
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_MOCK_LLM=1 \
  .venv/bin/python -m pytest agent/tests -q
```

Dashboard: [http://localhost:3010/dashboard](http://localhost:3010/dashboard) (Live). Teach: `/store-a` Rec / Save.

---

## Stack

Next.js stores + dashboard · Pydantic AI (Explorer / Verifier / Recovery) · Playwright hands · Gemini multimodal · JSON adapters · Modal hypothesis scoring

Architecture reference: [ARCHITECTURE.md](ARCHITECTURE.md)
