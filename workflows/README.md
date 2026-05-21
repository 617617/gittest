# workflows/ — Plug-and-play registry for multi-AI collaborative workflows

This directory is a **registry of workflow presets**. Each subdirectory is
one plug-and-play collaborative workflow that describes, for a specific
project scenario, how CC and Codex divide work, which baton states they
move through, and which handoffs drive progress.

`blue-k-git-baton-testkit/` is **not** under this directory and does **not**
read any file here. It is the first, frozen workflow instance. This
registry is an incremental mechanism for "future projects that want to opt
into a dual-AI collaboration".

## Layout

```text
workflows/
  README.md           # this file
  _active.md          # informational only: which preset has the user's primary focus (not enforced)
  <preset-name>/      # one workflow preset
    CHARTER.md        # charter: goals, scope, completion criteria
    ROLES.md          # step × AI responsibility matrix
    BATON.schema.md   # state machine: states, legal transitions, drivers
    _coord/
      from-cc/        # CC → Codex mailbox (git-tracked)
      from-codex/     # Codex → CC mailbox (git-tracked)
    skills/           # per-lane skill folders for this preset
```

## Adding a preset

1. Create `<preset-name>/` under this directory.
2. Copy the four core files (CHARTER / ROLES / BATON.schema / `_coord/`)
   from an existing preset as a skeleton.
3. Fill CHARTER and ROLES section by section from the source workflow
   document.
4. Derive the BATON state machine from the ROLES matrix.
5. Write a SKILL.md stub for every lane under `skills/` (start with the
   trigger / reads / writes / product fields; flesh out prompts later).
6. **Do not** copy anything from `blue-k-git-baton-testkit/` into a new
   preset — the two are unrelated by design.

## Enablement (per-workflow, independent)

There is **no single "active" preset.** A workflow is enabled by the
existence of its directory plus its registered skills; multiple
workflows can be enabled and running in parallel.

Each workflow ships its own watcher skill (e.g.,
`.claude/skills/temporal-phase-watch/`, `.claude/skills/bk-watch/`).
Each watcher:

- arms independently;
- only touches its own workflow's coord directory;
- does not read `_active.md`;
- is idempotent (safe to re-invoke in the same session).

The SessionStart hook in `.claude/settings.json` lists all available
watchers. CC decides which to invoke based on which workflows the
current session is participating in.

`workflows/_active.md` is **informational only** — it records which
workflow has the user's primary focus, as a hint for new conversations.
It does not gate anything.

## Currently registered presets

- `temporal-phase` — sourced from
  `E:/code/temporal/docs/skill-temporal-reorchestration/current/execution/PHASE_COLLABORATIVE_EXECUTION_WORKFLOW_ZH_2026-05-21.md`,
  the Temporal project's Phase collaborative workflow.

## Quick-start shortcuts (CC side)

Each preset exposes a one-command orchestrator so the user does not need
to memorize the bootstrap sequence:

| Preset | One-command entry |
|--------|-------------------|
| `temporal-phase` | `/temporal-phase-start` |
| `blue-k-git-baton-testkit` | `/bk-watch` (the testkit only has a watcher; the walkthrough is interactive) |

The orchestrator skill diagnoses the current baton state and emits the
exact next action (including any copy-paste text the user needs to send
to the Codex side on the other host).
