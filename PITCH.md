# SkillShift — 3-minute pitch

Say this out loud. Do not open WAVE notes, SUBMISSION, or the evidence pack unless someone asks “is it fake?”

You need **two windows** the whole time:

1. Your browser on [http://localhost:3010/dashboard](http://localhost:3010/dashboard) — **Live** is on
2. The headed Chromium that pops up — leave it in front so people watch the clicks

---

## 60 seconds before you start (do this off-mic)

```bash
# terminal 1 — already running
cd web && npx next start -p 3010

# terminal 2 — THIS LINE IS THE DEMO
cd /path/to/SkillShift
.venv/bin/python -m agent.run_transfer --reset
```

Wait until it prints `Reset: emptied …` and `Adapter: empty`, then **Ctrl+C** if you only wanted the reset — **or** just run `--reset` as the actual demo from the terminal (headed Chromium opens itself).

Easier path for a live pitch:

```bash
SKILLSHIFT_WEB_URL=http://localhost:3010 SKILLSHIFT_HEADED=1 \
  SKILLSHIFT_DEMO_PAUSE=1.5 SKILLSHIFT_DEMO_HOLD=3 \
  .venv/bin/python -m agent.run_transfer --reset
```

Then you narrate while it runs. The dashboard **Run transfer** button does **not** reset. If you already have a learned adapter, that button will only replay. Reset first, every time.

On Store B, confirm the three **Judge controls** are **off**.

---

## The one idea (say this, ~20s)

Stand on the home page (`/`) or the dashboard. Point at the two words.

> Most agents remember **clicks**. We remember the **job**.
>
> **Skill** is *what* — publish a product. That never changes.
>
> **Adapter** is *how here* — this store’s buttons, this store’s extra rules. That we discover.

Pause. Then:

> We taught it once in Store A. Store B has never seen a mapping. Watch it fail for a real reason, fix itself, and remember.

---

## Beat 1 — the kitchen we already know (~20s, optional)

Only if you have time. Open `/store-a` for one breath.

> This is the teaching store. Products, Add, picture, **Publish**. Same job you’ll see everywhere else. The skill we saved is four steps: start, details, image, make it public. No button names in it.

Back to `/dashboard`. Point left to right: **Learned Skill · Current App · Adapter · Status**.

> Skill card stays frozen. Adapter card is empty or stale — that’s the point. Status will move while it runs.

---

## Beat 2 — first product, empty memory (~90s)

Chromium is on Store B. Talk about what you *see*, not a script. Typical path:

**It opens Inventory, then Create Listing.**  
If it taps Collections first, that’s fine — say:

> That’s a decoy. Looks like “create,” it’s merchandising. The checker says this is the wrong place.

**It fills name, price, image, then clicks Go Live. The button stays grey.**

This is the line. Slow down.

> The skill says “make it public.” It does **not** say “pick a shipping category.” This store refuses to go live without one. That’s a rule it has never seen.

Wait for the blocker text / the dashboard to show a failed publish.

> Separate checker: did a product actually appear? No. So this is not “the click failed.” This is “the environment wants something extra.”

It selects shipping, clicks Go Live again. **Leather Bag** lands on the page.

> We did not edit the skill. We wrote a new line in the adapter: *this kitchen needs shipping first.*

On the dashboard, point at the new Shipping row and the Status message.

---

## Beat 3 — second product, it already knows (~30s)

Same Chromium window. **Blue Sneaker**. Almost no thinking.

> Same skill. Known how-here. It does not re-discover shipping. That’s the number we care about — model calls drop from about thirteen to three. The clicks are the same. The *guessing* stopped.

Hold on the two product cards. Stop talking for a second so it lands.

---

## Close (~15s)

> Teach the goal once. Let the agent learn the room. If the room changes, we patch the adapter — not the skill.

That’s the demo. Sit down.

---

## If they still look unconvinced (+60s, pick ONE)

### “Isn’t that just recorded selectors?”

On `/store-b`, sidebar, tick **Rename publish**. Do **not** reset. Run again (dashboard button is fine now — you *want* the warm adapter).

> I just deleted the old Go Live control. New button, new id: Launch Product. A cache would die here.

Watch for `stale mapping` then a remap. Adapter version ticks up.

### “What if there’s no publish button?”

Open `/store-c` (don’t need a full run).

> Table. Drawer. You publish by setting status to Live and saving. There is no button that means publish. Same four-step skill. Different adapter file. We have never handed it Store B’s memory.

### “What about other languages?”

Flash `/store-d`. No English on the chrome.

> Same layout as B. Every label is Japanese. The model has to read the screen, not the word “Publish.”

---

## What you should *not* say

| Don’t | Say instead |
| --- | --- |
| “It works on any website.” | “Four stores we built, on purpose different.” |
| “Collections is always the first miss.” | Narrate whatever Chromium actually does. |
| “Modal does the browsing.” | Skip Modal unless asked. (It only scores a guess.) |
| “67 tests.” | Save it for “is it real?” — then hand [docs/EVIDENCE.md](docs/EVIDENCE.md). |

---

## Panic card

| Symptom | Fix |
| --- | --- |
| Chromium just publishes, no shipping drama | You forgot `--reset`. Stop. Reset. Restart. |
| Button says Running… forever | Terminal 2 already has a transfer, or no API key and mock is slow. Check `.env`. |
| Dashboard looks static / “fixture” | Click **Live**. |
| Go Live already says Launch Product | Judge toggle is still on. Turn all three off. |
| Second product doesn’t appear | Wait — `DEMO_HOLD` keeps the window. Don’t close Chromium. |

---

## Timing

| Clock | You’re on |
| --- | --- |
| 0:00 | One idea: skill vs adapter |
| 0:20 | Dashboard cards (Store A only if early) |
| 0:40–2:10 | Empty adapter, grey Go Live, shipping, Leather Bag |
| 2:10–2:40 | Blue Sneaker, no rediscovery |
| 2:40–3:00 | Close line |
| +1:00 | One encore: rename, or Store C, or Japanese — not all three |
