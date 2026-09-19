# Modal notes (SkillShift)

This folder used to be named `modal/`, which **shadowed** the PyPI Modal SDK
(`import modal` resolved here). It was renamed to `modal_notes/` for Wave 6.

**Live Modal app code:** [`modal_app/`](../modal_app/) — run with:

```bash
modal run modal_app/recovery_runner.py
```

## Modal agent skill

Official Modal skill (project): [`.agents/skills/modal/SKILL.md`](../.agents/skills/modal/SKILL.md)

```bash
.venv/bin/modal skills install -y
# or update:
.venv/bin/modal skills update -y
```

See also: [modal skills CLI](https://modal.com/docs/cli/latest/skills).

## Auth

```bash
.venv/bin/pip install -U modal
.venv/bin/modal setup    # once, interactive
```

## SkillShift use of Modal

Parallel snapshot scoring of campaign recovery hypotheses — not hosting Next.js.
See [PLAN.md](../docs/build/PLAN.md) and [ARCHITECTURE.md](../ARCHITECTURE.md) Modal recovery.
