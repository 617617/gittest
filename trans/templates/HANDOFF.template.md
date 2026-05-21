# HANDOFF — <PRESET> workflow · for `<the other AI>`

Read this file first. It is the entry point into the `<preset>`
preset for the AI on the other host.

> **CC-side shortcut for the user:** `/<preset>-start` is a CC
> orchestrator skill that diagnoses the current baton state and emits
> the right next action automatically (including the bootstrap text
> for this side). The user does not need to remember any other command
> on the CC side. This HANDOFF is what *you* read; the user's path
> through CC is `/<preset>-start`.

## 1. Where you are

- Coord repo (this directory's repo): your machine's `gittest` repo
  root (see `PATHS.md`).
- Work repo (where this preset's actual work happens): your machine's
  `<project>` root (see `PATHS.md`).
- Collaboration mode: `<path X (coord-vs-work separate) | path Y
  (same repo)>`.

Machine paths are maintained **only** in `PATHS.md`. Everywhere else,
documents use prefix references (`gittest:...`, `<project>:...`,
`<project>@<sha>`).

## 2. Required reading (in order)

1. `PATHS.md`
2. `CHARTER.md`
3. `ROLES.md`
4. `BATON.schema.md`
5. The lane skill matching the current baton state:
   `skills/<preset>-<lane>/SKILL.md`.

The authoritative source document: `<path>`.

## 2.1 Registered skill list

All `<N>` lanes are registered in `.codex/skills.json` and loaded by
the Codex CLI at startup. Registration is validated by
`scripts/verify_<preset>_skills.py`.

Codex sees `<M>` Codex lanes (each invocable via `/<lane-name>`):
`<list>`.

The `<K>` CC-only lanes are also registered but their `default_prompt`
declares "Codex must refuse". If asked to take one of them, Codex
declines and indicates that it is a CC lane.

## 3. Your role in this preset

`<description of the AI's responsibilities>`.

## 3.1 State → lane lookup

| Baton state | Lane to use |
|-------------|-------------|
| `<STATE>` | `<preset>-<lane>` |
| ... | ... |

## 4. Where your products go

Write path: `workflows/<preset>/_coord/from-<your-side>/`

Filename pattern: `<unit-id>__<step-tag>.md`.

**The first line of every product must be:**
```text
BatonNext: <STATE>
```

## 5. Cross-repo linking

`<rules for referring to the work repo via prefixes and SHA>`

## 6. Getting started

`<the very first action you take when the preset starts>`.

## 7. Hard rules

`<list the structural locks: scope, iteration caps, one-shot branches,
completion gates, isolation>`.

## 8. Relationship to other presets

Unrelated. `<other presets>` is separate; this preset borrows ideas but
not files.
