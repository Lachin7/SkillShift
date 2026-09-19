You are the solo Wave 7 agent. Improve the **technical agent pipeline** from WAVE7.md and prompts/skillshift_build_brief.md. Do not rebuild Store A/B.

Order (same chat):

1. prompts/agent-7a.md — observe_app + test API  
2. prompts/agent-7b.md — independent verifier + diagnoser  
3. prompts/agent-7c.md — AdapterPatch curator  
4. prompts/agent-7d.md — metrics + naive replay baseline  

Then if time:

5. prompts/agent-7e.md — Modal scores real hypotheses  
6. prompts/agent-7f.md — dashboard trace  

After 7C, confirm:

```bash
SKILLSHIFT_MOCK_LLM=1 SKILLSHIFT_WEB_URL=http://localhost:3010 \
  .venv/bin/python -m agent.run_transfer
```

Cold adapter still publishes; shipping still discovered; second run cache hits.

Do not restore `adapter.wrong.json` on the live path. Do not rename Skill intents. Next.js on :3010. Local agent.
