# `adapters/`

Persisted HOW HERE memory for each app × skill.

- `store_a__publish_product.json` — Store A replay cache (teaching environment)
- `store_b__publish_product.json` … `store_e__publish_product.json` — one file per target app

`--reset` empties the *current* target's live file so the next run is a genuine cold start. Frozen copies of learned adapters (for judges) live in [`docs/evidence/adapters/`](../docs/evidence/adapters/) and are not touched by reset.

Do not hand-author HOW HERE as the live decision source. The transfer loop writes mappings after Explorer / Verifier / Recovery succeed.
