# Fallback modes for temporal-phase-codex-sync

The sync protocol assumes Codex CLI on Host B can (a) load this skill
from `.codex/skills.json`, (b) run `python` subprocesses, and (c) `git
push` without per-action confirmation. None of these are guaranteed
universally. If any fails, the chain must not silently corrupt — fall
back as follows.

## 1. Slash command `/temporal-phase-codex-sync` not recognised

Codex CLI may not auto-register every entry from `.codex/skills.json`
as a slash command. Fallback: open this skill file
(`workflows/temporal-phase/skills/temporal-phase-codex-sync/SKILL.md`)
by path and follow steps 1–5 manually. Same effect.

## 2. `python` subprocess blocked

Your CLI may refuse to spawn python. Surface the verifier output to
the user:

> "subprocess blocked; please run
> `python scripts/verify_temporal_phase_skills.py` and
> `python scripts/check_baton_artifacts.py` manually and paste the
> output back".

Do NOT proceed with `git push` until the user confirms both PASS.

## 3. `git push` requires per-action confirmation

If your CLI prompts for confirmation on every push, surface that to
the user rather than guessing. State the exact `git push` command
being proposed, wait for user approval, then proceed.

## 4. Cannot read `.codex/skills.json` to enumerate skills

Surface this to the user as "skill registry not visible from this
session". Recovery: open this SKILL file directly by path
(`workflows/temporal-phase/skills/temporal-phase-codex-sync/SKILL.md`)
and follow steps 1–5 manually. The slash form will start working once
the registry can be loaded (likely after Codex restart in the correct
CWD = the coord-repo root).
