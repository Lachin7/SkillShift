# Evidence — does SkillShift actually work?

This file exists to be checked, not believed. Every number below was produced by a command you can run. Transcripts in [`docs/evidence/`](evidence/) are redirected tool output, not typed up afterwards. Frozen adapters in [`evidence/adapters/`](evidence/adapters/) survive `--reset`, which empties the live files in `/adapters`.

**Judges:** start at [../SUBMISSION.md](../SUBMISSION.md). Scoring overlay: [JUDGE_SCORECARD.md](JUDGE_SCORECARD.md). This file is the raw proof.

Captured **2026-09-19**, macOS, live Next.js on `:3010`.
Model: `google:gemini-3.6-flash` via `GEMINI_API_KEY` in `.env` (autoload — no export required).
Versions: [`evidence/environment.txt`](evidence/environment.txt).

## Headline

| Check | Result | Artifact |
| --- | --- | --- |
| Python test suite (mock backend, no network) | **67 passed** in 167s | [`pytest.txt`](evidence/pytest.txt) |
| `tsc --noEmit` + `next build` | clean, 5 store routes + 7 API routes | [`environment.txt`](evidence/environment.txt) |
| Store B publish from an **empty** adapter (real model) | cold 71.6s → cached 9.2s | [`store-b-cold-and-cached.txt`](evidence/store-b-cold-and-cached.txt) |
| Reuse gain, run 1 → run 2 | model calls **13 → 3**, recoveries **2 → 0** | [`loop-trace.txt`](evidence/loop-trace.txt) |
| Store C (table + status dropdown, no publish button) | **3 / 3** cold starts passed | [`store-c-reliability.txt`](evidence/store-c-reliability.txt) |
| Store D (Japanese) and Store E (Persian, RTL) | publish from empty adapters | [`store-d-transfer.txt`](evidence/store-d-transfer.txt), [`store-e-transfer.txt`](evidence/store-e-transfer.txt) |
| Judge flips a rule mid-run, warm adapter | 3 / 3 flags detected and repaired | [`perturbations.txt`](evidence/perturbations.txt) |
| Naive replay baseline (the honest control) | **fails**, as it must | [`verification-independence.txt`](evidence/verification-independence.txt) |
| Same Skill, four HOW HEREs | four finish trails, none shared | [`cross-app-mappings.json`](evidence/cross-app-mappings.json) |

## The claim, and what would disprove it

> A Skill learned in one app can acquire, repair, and persist an adapter for an app it has never seen.

That is only interesting if the adapter is genuinely *absent* at the start and genuinely *earned* during the run. Four things would expose a fake: a pre-written mapping table, a scripted failure, a verifier that always agrees, or an app tuned so that only one obvious button exists. Each is addressed below.

### 1. The adapter starts empty, and the file proves it

`--reset` writes an empty adapter before the run, and the transcript opens with it:

```bash
python -m agent.run_transfer --reset
```

```text
Reset: emptied store_b__publish_product.json — forcing cold start
Environment: store-b unseen
Adapter: empty — grounding via Explorer / Verifier / Recovery
```

The same file at the end of the run contains five mappings with `resolved_targets`, `successes`, and `adapter_version`. A frozen copy is [`evidence/adapters/store_b.learned.json`](evidence/adapters/store_b.learned.json) — use that if someone has since reset the live file. `adapters/` holds one file *per app*, so Store B's knowledge is never available to Store C, D, or E.

### 2. The failure is real, discovered from the live DOM

Store B's Go Live button is genuinely disabled until a shipping category is set. The agent doesn't know that. It clicks publish, the verifier reports the goal unmet, the diagnoser classifies it, and recovery fixes the cause:

```text
explore[1]: click store-b-go-live
diagnose: class=missing_prerequisite (The 'Go Live' button remains disabled because the mandatory 'Shipping …')
verify: matched=False type=missing_prerequisite class=missing_prerequisite
recover prereq: select store-b-field-shipping
retry step: click store-b-go-live
patch applied: add_prerequisite satisfy environment prerequisite: shipping category
```

The prerequisite becomes a **new mapping the demonstration never contained**, and the second product reuses it without rediscovery. Store C's gate is *category* rather than shipping, so nothing transfers for free between apps.

### 3. Verification is a separate call with its own evidence

The verifier never trusts that a click worked. It re-observes the page, reads control values, and consults a test-only ground-truth API. From [`verification-independence.txt`](evidence/verification-independence.txt):

```text
--- state after typing ONLY the name ---
  store-b-field-name             value='Leather Bag'
  store-b-field-price            value=''

--- test-only ground-truth API, asked about a product that is NOT live ---
   {"product_exists": false, "title": "Leather Bag", "status": "none", "purchasable": false}

--- verifier on the publish step while Go Live is disabled ---
   matched=False mismatch=missing_prerequisite failure_class=missing_prerequisite
```

It answers `matched=False` on an unmet goal, and the API is keyed to the exact product title, so a leftover product from an earlier run cannot be mistaken for success. The naive baseline — replaying Store A's own labels on Store B — fails (`BASELINE_REPLAY_FAILED`), which is the control that shows the task is not trivially replayable.

### 4. Four target apps, deliberately dissimilar

| App | Shape | Finish control | Prerequisite | Vocabulary |
| --- | --- | --- | --- | --- |
| Store B | single-page form | `Go Live` button | shipping category | English |
| Store C | listings **table** + editing drawer | **no button** — status dropdown → `Live`, then `Save row` | category | Title / Amount, not Name / Price |
| Store D | form | `公開する` | 配送カテゴリ | Japanese only |
| Store E | form, right-to-left | `انتشار` | Persian shipping field | Persian only |

Screens: [`screens/store-c.png`](evidence/screens/store-c.png) · [`store-d.png`](evidence/screens/store-d.png) · [`store-e.png`](evidence/screens/store-e.png) (headless font fallback can look odd; the live pages on `:3010` are authoritative).

Store C is the sharpest test, because "find the button whose label means publish" cannot work — publishing is a **two-action** state change the adapter remembers as an ordered trail (`store-c-field-status` → `store-c-save-row`). Store D and E remove English keyword matching; the model's own rationales quote the native labels:

```text
explore[1]: click store-e-release (Clicking 'انتشار' (Publish) publishes the product and makes …)
```

Both finish with `Product live (Leather Bag)` and a cached second product, on the same `13 → 3` model-call profile as Store B.

The same frozen four intents drive all of them. Switching app is `SKILLSHIFT_TARGET_APP=store-c|store-d|store-e`, which changes *where the agent is*, never *what a control means*. Machine-readable comparison: [`evidence/cross-app-mappings.json`](evidence/cross-app-mappings.json).

### 5. A judge can break it live, and watch the repair

Three perturbations are flipped over HTTP against a **warm** adapter, mid-demo, with no code change and no restart. Each removes a `data-testid`, so a cached trail cannot simply replay. From [`perturbations.txt`](evidence/perturbations.txt):

| Flag | What the agent did | Adapter |
| --- | --- | --- |
| `rename_publish` | `stale mapping: saved testid missing store-b-go-live` → re-grounded to `store-b-launch-product` → verified | v2 → v3, `replace_mapping` |
| `extra_required` | healed the stale publish rule **and** discovered a new tax-class gate | v3 → v5, sixth mapping added |
| `reorder_nav` | start step remapped to `store-b-nav-catalog` | publish path still cached |

```bash
curl -X POST localhost:3010/api/perturbations -H 'Content-Type: application/json' \
  -d '{"rename_publish":true}'
python -m agent.run_transfer      # warm adapter: watch it notice and repair
```

## Reproduce it yourself

```bash
cd web && npm install && npm run build && npx next start -p 3010   # terminal 1
# terminal 2, from the repo root:
python3 -m venv .venv && .venv/bin/pip install -r agent/requirements.txt
.venv/bin/playwright install chromium
# GEMINI_API_KEY in .env is enough — the CLI loads it

.venv/bin/python -m pytest agent/tests -q                                   # 67 passed, no key needed
.venv/bin/python -m agent.run_transfer --reset                              # Store B, empty adapter
SKILLSHIFT_TARGET_APP=store-c .venv/bin/python -m agent.run_transfer --reset # unseen app
SKILLSHIFT_TARGET_APP=store-d .venv/bin/python -m agent.run_transfer --reset # Japanese
```

`--reset` matters: with a warm adapter the run is a cache hit by design and the discovery never happens.

## Limitations we are not hiding

- **The five stores are ours.** They are honest React apps with real disabled states and real blockers, not mocks, but we built them. The strongest counter is Store C and the perturbations: the agent had no run history on either, and a judge can change the rules at the table.
- **The model is nondeterministic.** Wording differs run to run, and the loop budgets retries per step. Store C is 3/3 after we fixed a genuinely misleading drawer heading (it said "Edit row" while creating a new one, and the verifier was right to reject it). We publish the reliability sample rather than a single lucky log.
- **One mechanical shortcut in the live path.** `_details_followups` fills the remaining product field of the details step by control kind (`-field-price` / `-field-amount`). It completes data entry the Explorer already began; it never chooses which control satisfies an intent.
- **Superseded rules are not invalidated yet.** Turn `extra_required` off after a run and the learned tax-class prerequisite stays in the adapter. It is harmless — the control is simply absent — but it is not yet pruned.
- **CI runs on a mock backend.** `SKILLSHIFT_MOCK_LLM=1` keeps the 67 tests keyless and offline, and the mock is constrained to visible testids, but it is not a substitute for the real-model runs above. Every number in the Headline table that involves grounding came from a real model call.
- **Modal's role is narrow.** It scores competing recovery hypotheses in parallel (`hypothesis score (modal): winner=A`). It is not doing the grounding.
- **The Pydantic Gateway path is wired but unverified on our org.** The gateway key we hold answers `403 Gateway is not enabled for this organization`, so gateway routing is opt-in behind `SKILLSHIFT_USE_GATEWAY=1` and direct keys win by default. See [GATEWAY_PRIZE.md](GATEWAY_PRIZE.md).

## Artifact index

| File | Contents |
| --- | --- |
| [`JUDGE_SCORECARD.md`](JUDGE_SCORECARD.md) | Scoring overlay for the official write-up |
| [`evidence/README.md`](evidence/README.md) | Index of every raw file |
| [`evidence/environment.txt`](evidence/environment.txt) | Versions and the `next build` route table |
| [`evidence/pytest.txt`](evidence/pytest.txt) | Full suite result |
| [`evidence/store-b-cold-and-cached.txt`](evidence/store-b-cold-and-cached.txt) | Cold + cached run, learned adapter JSON, run metrics |
| [`evidence/store-c-cold-and-cached.txt`](evidence/store-c-cold-and-cached.txt) | Unseen table-based app |
| [`evidence/store-c-reliability.txt`](evidence/store-c-reliability.txt) | Three consecutive cold starts |
| [`evidence/store-d-transfer.txt`](evidence/store-d-transfer.txt) | Japanese app transcript |
| [`evidence/store-e-transfer.txt`](evidence/store-e-transfer.txt) | Persian (RTL) app transcript |
| [`evidence/perturbations.txt`](evidence/perturbations.txt) | All three live perturbations, adapter before/after |
| [`evidence/verification-independence.txt`](evidence/verification-independence.txt) | Baseline failure, observed field values, ground-truth API |
| [`evidence/loop-trace.txt`](evidence/loop-trace.txt) | What the dashboard renders, plus `reuse_gain` |
| [`evidence/cross-app-mappings.json`](evidence/cross-app-mappings.json) | Same four intents, four different trails |
| [`evidence/adapters/`](evidence/adapters/) | Frozen learned adapters (B/C/D/E) |
| [`evidence/screens/`](evidence/screens/) | Headless captures of the four stores and the dashboard |
