# Modal (SkillShift)

This folder is for **our** recovery runner later (`recovery_runner.py`). It is **not** the Modal Python SDK.

## Critical: rename before Wave 3

Right now `import modal` from the repo root resolves to this directory (namespace package), not the SDK:

```text
SkillShift/modal/   ← shadows the real `modal` package
```

Before any Modal code lands, rename this folder, e.g.:

```text
modal_app/recovery_runner.py
```

or keep recovery under `agent/recovery_modal.py` and delete this directory.

Do **not** put `from modal import App, Sandbox` code in a package named `modal`.

## Modal agent skill (installed)

Official Modal skill is installed for Cursor at:

- [`.agents/skills/modal/SKILL.md`](../.agents/skills/modal/SKILL.md) (project)
- [`.cursor/skills/modal/SKILL.md`](../.cursor/skills/modal/SKILL.md) (project)
- `~/.agents/skills/modal/` and `~/.claude/skills/modal/` (global)

`modal skills` is in Modal's CLI docs / main branch, but **PyPI `modal==1.2.6` does not ship the `skills` command yet**. We installed `SKILL.md` + `references/llms.txt` manually from Modal's repo.

When your CLI gains the command:

```bash
pip install -U modal
modal skills install -y --global          # → ~/.agents/skills/modal
# optional also:
modal skills install -y --global --claude # → ~/.claude/skills/modal
```

In this repo, prefer the **project** copies under `.agents/skills/modal` so local Wave 3 agents see them without relying on global paths.

## Do not edit the Modal skill

Leave Modal's `SKILL.md` as upstream wrote it. Do **not** patch it for SkillShift. When Wave 3 starts, put SkillShift-specific Modal instructions in our own prompt / `WAVE3.md`, not inside Modal's skill.

## Auth (only when you implement recovery)

```bash
# add modal to the project venv (uv/poetry/pip — not from repo root until rename)
pip install -U modal
modal setup    # interactive login / token — you must do this once
```

Wave 2 (recorder + Playwright) does **not** need Modal auth or API keys.

## SkillShift use of Modal

Sponsor story: parallel Sandboxes to try competing adapter candidates after a mismatch — not “host our Next.js app on Modal.”

See [PLAN.md](../PLAN.md) step 7 and [ARCHITECTURE.md](../ARCHITECTURE.md) Modal recovery.
