# Inspiration clones

Shallow local copies for reading. **Gitignored. Do not vendor their code into SkillShift.**

| Directory | Steal | Do not do |
| --- | --- | --- |
| `ShowUI-Aloha` | Recorder → semantic trace | Their OS-level actor / model |
| `UI-Mate` | Demo = advice, not a script | Run their 27B checkpoint |
| `EvoSkill-GUI` | Plan / recovery / failure as separate knowledge | Reproduce the full research framework |
| `understudy` | Teach / replay UX | Recreate a desktop agent |
| `browser-use` | Browser action primitives | Let it own reasoning |
| `stagehand` | Alternative executor ideas | Use it *and* Browser Use |
| `OmniParser` | Future vision grounding | Install for MVP |
| `pydantic-ai` | Typed outputs, harness / TrajectoryJudge later | Use Pydantic only as validation |

Clone command (already run during setup):

```bash
cd inspo
git clone --depth 1 https://github.com/showlab/ShowUI-Aloha.git
git clone --depth 1 https://github.com/Tencent/UI-Mate.git
git clone --depth 1 https://github.com/ZJU-REAL/EvoSkill-GUI.git
git clone --depth 1 https://github.com/understudy-ai/understudy.git
git clone --depth 1 https://github.com/browser-use/browser-use.git
git clone --depth 1 https://github.com/browserbase/stagehand.git
git clone --depth 1 https://github.com/microsoft/OmniParser.git
git clone --depth 1 https://github.com/pydantic/pydantic-ai.git
```
