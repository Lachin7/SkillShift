# Raw evidence artifacts

Redirected command output and frozen files. Do not edit by hand — recapture if you rerun.

| File | What it is |
| --- | --- |
| [`environment.txt`](environment.txt) | Python / Node / Next.js versions and the production route table |
| [`pytest.txt`](pytest.txt) | `67 passed` on `SKILLSHIFT_MOCK_LLM=1` |
| [`store-b-cold-and-cached.txt`](store-b-cold-and-cached.txt) | Real Gemini cold start + cache hit + learned adapter JSON + metrics |
| [`store-c-cold-and-cached.txt`](store-c-cold-and-cached.txt) | Table app, no publish button |
| [`store-c-reliability.txt`](store-c-reliability.txt) | Three consecutive Store C cold starts, all passed |
| [`store-d-transfer.txt`](store-d-transfer.txt) | Japanese labels; rationales quote `出品を作成` / `公開する` |
| [`store-e-transfer.txt`](store-e-transfer.txt) | Persian RTL; rationale quotes `انتشار` |
| [`perturbations.txt`](perturbations.txt) | Warm adapter + three live DOM-contract changes |
| [`verification-independence.txt`](verification-independence.txt) | Naive baseline fails; verifier sees empty fields and says no |
| [`loop-trace.txt`](loop-trace.txt) | Dashboard trace: every failure followed by its resolution |
| [`cross-app-mappings.json`](cross-app-mappings.json) | Same four Skill intents → four different `resolved_targets` trails |
| [`adapters/*.learned.json`](adapters/) | Frozen adapters. Live files in `/adapters` get emptied by `--reset` |
| [`screens/`](screens/) | Headless captures of B / C / D / E / dashboard (CJK/RTL fonts may fallback) |

Narrative and scoring overlay: [../EVIDENCE.md](../EVIDENCE.md) and [../JUDGE_SCORECARD.md](../JUDGE_SCORECARD.md).
