# `web/` — Agent A

Next.js fake stores and the four-card dashboard.

**You own this directory. Do not edit `agent/`, `fixtures/`, `adapters/`, `shared/`, or the root markdown plans.**

Read first:

1. [../CONTRACT.md](../CONTRACT.md)
2. [../shared/routes.md](../shared/routes.md)
3. [../shared/ownership.md](../shared/ownership.md)
4. [../shared/examples/dashboard-state.json](../shared/examples/dashboard-state.json)
5. [../PLAN.md](../PLAN.md) step 1
6. [../ARCHITECTURE.md](../ARCHITECTURE.md) Fake stores + Dashboard contract

Inspiration (read-only, do not copy their stacks): `inspo/understudy` for teach/replay UX feel.

Full prompt: [../WAVE1.md](../WAVE1.md) § Agent A.

## Run

```bash
cd web
npm install
npm run dev
```

- [http://localhost:3000](http://localhost:3000) — Store A, Store B, Dashboard
- `/store-a` — Products → Add Product → Media → Publish. Recorder is on by default; Download / Save writes `fixtures/traces/store-a.json`.
- `/store-b` — Inventory → Create Listing → Go Live (Collections is a decoy)
- `/dashboard` — Skill / App / Adapter / Status, with a fixture phase switcher

Dashboard JSON lives in `public/dashboard-state*.json` (copied from `shared/examples/`, plus a `cached` phase).
