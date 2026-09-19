# Judge scorecard — what to rate, and what proves it

Use this when writing the official judge-facing write-up. Every row is a **claim we want scored**, paired with an artifact a skeptical reader can open without trusting us.

Full transcripts and numbers: [EVIDENCE.md](EVIDENCE.md). Raw files: [`evidence/`](evidence/).

Captured 2026-09-19 against a live Next.js server on `:3010`, model `google:gemini-3.6-flash`.

---

## Rate these five things (in this order)

The wow is not “an agent clicked Publish.” The wow is **the Skill never changed, the Adapter did, and a judge can watch that happen.**

| # | Score this | Do not score this | Open this |
| --- | --- | --- | --- |
| 1 | Same frozen Skill, four different HOW HEREs, each *earned* from an empty adapter | Pretty store UIs | [`evidence/cross-app-mappings.json`](evidence/cross-app-mappings.json) + the four [`adapters/*.learned.json`](evidence/adapters/) |
| 2 | A real miss, then a *new* mapping the demonstration never contained (shipping / category) | A scripted happy path | [`evidence/store-b-cold-and-cached.txt`](evidence/store-b-cold-and-cached.txt) lines 23–32 |
| 3 | Second product is cheaper because memory, not because we cheated | “It ran twice” | `reuse_gain`: model calls **13 → 3**, recoveries **2 → 0** in the same file |
| 4 | A judge can break a warm adapter *from the browser* and watch it repair | A second hardcoded selector | [`evidence/perturbations.txt`](evidence/perturbations.txt) — `stale mapping: saved testid missing store-b-go-live` |
| 5 | Verification can say **no** | A loop that always reports success | [`evidence/verification-independence.txt`](evidence/verification-independence.txt) — `BASELINE_REPLAY_FAILED` and `matched=False` |

If a later write-up has room for only one figure, use the table in §Hero below.

---

## Hero figure — same WHAT, four HOW HEREs

Skill intents are frozen (`start creating a new sellable item` · `provide basic product information` · `attach the product image` · `make the product publicly available`). Nothing below was hand-authored as the live decision source.

| App | Start trail | Finish trail | Prerequisite the Skill never mentioned |
| --- | --- | --- | --- |
| **B** Harbor Ledger | `nav-inventory` → `create-listing` | `go-live` | shipping category |
| **C** Northwind Market | `new-row` | `field-status` → `save-row` | **category** (different gate) |
| **D** みなと商店 | `nav-inventory` → `create-listing` | `publish` (`公開する`) | 配送カテゴリ |
| **E** فروشگاه بندر | `nav-inventory` → `create-listing` | `release` (`انتشار`) | Persian shipping field |

Store C is the sharpest cell: there is **no publish button**. Publishing is “set status to Live, then save.” That trail is two actions and it is what the adapter stored.

Store D and E kill English keyword matching. The model’s own rationales quote the native labels (`出品を作成`, `公開する`, `انتشار`).

---

## Suggested rubric (hackathon-shaped)

Write the official doc so a judge can tick these without a demo if they have to.

### A. It actually works (reproducible)

- [ ] `67 passed` in [`evidence/pytest.txt`](evidence/pytest.txt) — no API key
- [ ] Real-model cold start prints `Adapter: empty` then `Product live (Leather Bag)` then `Blue Sneaker live`
- [ ] Store C 3/3 in [`evidence/store-c-reliability.txt`](evidence/store-c-reliability.txt)
- [ ] Reproduce: `python -m agent.run_transfer --reset` with Next.js on `:3010`

### B. The claim is not a script

- [ ] Adapter file starts `mappings: []` (`--reset` writes this; transcript line 1)
- [ ] Explorer picks from *visible* controls; invented testids are rejected (unit tests + live traces)
- [ ] Verifier is a **separate** call and reports `matched=False` on an unmet goal
- [ ] Naive baseline (Store A labels on Store B) **fails**
- [ ] Each app has its **own** adapter file — B’s knowledge is never handed to C

### C. Adaptation, not replay

- [ ] First run discovers a prerequisite the Skill does not contain
- [ ] That prerequisite is persisted (`learned_from: "recovery"`)
- [ ] Second run is cache hits only (`cache_hits: 4`, `recoveries: 0`)
- [ ] Mid-demo perturbation changes the **testid**, not just the label, and the agent remaps

### D. Generality signal (wow)

- [ ] Four IAs: form / table+drawer / Japanese / Persian RTL
- [ ] Finish controls do not share a suffix (`go-live` / `status+save` / `publish` / `release`)
- [ ] Live judge panel: rename / extra required field / reorder nav

### E. Honesty (score this *up* if we name the limits)

Limits we want the write-up to keep, not bury:

1. The stores are ours. Counter: Store C + live perturbations + empty-adapter rule.
2. The model is nondeterministic. Counter: Store C 3/3 sample, not a single lucky log.
3. `_details_followups` fills the remaining price/amount field by control kind after the Explorer has already begun the details step. It does not choose which control satisfies an intent.
4. CI is a mock backend (visible-testid constrained). Grounding numbers in the headline table are real-model.
5. Modal only scores recovery hypotheses. Gateway is wired but 403 on our org.

---

## What a fake would look like (use this as a self-check before submitting)

| Fake | What we have instead |
| --- | --- |
| `if app == "store-b": click("go-live")` | Explorer output is a `CandidateAction` chosen from the current observation |
| Adapter JSON committed already filled, “run” just replays | `--reset` empties it; transcript starts `Adapter: empty` |
| Rename the button label, keep the testid, call it adaptation | Perturbations **remove** the old testid (`store-b-go-live` gone) |
| Verifier always returns matched | Independent call + title-keyed `/api/store-b-state` + baseline that fails |
| One store, one button, English only | Four apps, two languages, one app with no publish button |
| Metrics invented in a README | [`fixtures/live/run-metrics.json`](../fixtures/live/run-metrics.json) written by the run |

---

## 90-second inspection (no demo)

1. Open [`evidence/cross-app-mappings.json`](evidence/cross-app-mappings.json) — four finish trails, none shared.
2. Open [`evidence/store-b-cold-and-cached.txt`](evidence/store-b-cold-and-cached.txt) — empty → miss → patch → cache.
3. Open [`evidence/perturbations.txt`](evidence/perturbations.txt) — `stale mapping` on a warm adapter.
4. Open [`evidence/verification-independence.txt`](evidence/verification-independence.txt) — `BASELINE_REPLAY_FAILED`.
5. Glance at [`evidence/screens/store-c.png`](evidence/screens/store-c.png) (table, no publish button) and [`store-d.png`](evidence/screens/store-d.png) (Japanese chrome).

## 2-minute live demo (if they have a laptop)

`--reset` first. Dashboard Live + headed Chromium. Talk track in [PITCH.md](../PITCH.md). If they ask “is it hardcoded?”, flip **Rename publish** on Store B and rerun without resetting — the stale-mapping line is the answer.

---

## Numbers to copy into the write-up (do not round)

| Metric | Value | Source |
| --- | --- | --- |
| Mock suite | 67 passed / 166.73s | [`evidence/pytest.txt`](evidence/pytest.txt) |
| Store B cold | 71.6s, 13 model calls, 2 recoveries, 0 cache hits | [`evidence/store-b-cold-and-cached.txt`](evidence/store-b-cold-and-cached.txt) |
| Store B cached | 9.2s, 3 model calls, 0 recoveries, 4 cache hits | same |
| reuse_gain | actions 0 · model_calls 10 · recoveries 2 | same |
| Store C cold | 11 → 3 model calls, 1 recovery (category) | [`evidence/store-c-cold-and-cached.txt`](evidence/store-c-cold-and-cached.txt) |
| Store C reliability | 3 / 3 | [`evidence/store-c-reliability.txt`](evidence/store-c-reliability.txt) |
| Store D / E | same 13 → 3 profile as B | [`store-d-transfer.txt`](evidence/store-d-transfer.txt), [`store-e-transfer.txt`](evidence/store-e-transfer.txt) |
| Perturbations | 3 / 3 flags repaired; adapter v2 → v3 → v5 | [`evidence/perturbations.txt`](evidence/perturbations.txt) |

Actions stay 7→7 because the cached run still performs the same clicks — the saving is **model calls and recoveries**, which is the right metric for “we stopped thinking.”

---

## Phrases to use / avoid in the official doc

**Use**

- “Skill is frozen; the Adapter is discovered, patched, and versioned.”
- “The shipping / category gate is a mapping the demonstration never contained.”
- “A judge can change the DOM contract mid-demo.”
- “The naive baseline fails; that is the control.”

**Avoid**

- “It works on any website.” (We have four stores we built.)
- “Fully autonomous, no heuristics.” (`_details_followups` exists; say so.)
- “67 tests prove the LLM.” (They prove the loop and the mock; Gemini proves grounding.)
- “Modal does the transfer.” (It scores hypotheses.)
