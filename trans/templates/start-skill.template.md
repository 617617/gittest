---
name: <preset>-start
description: One-command orchestrator for the <preset> workflow. Use whenever the user wants to start a new unit of work, resume an in-progress one, or check "where are we" — this skill diagnoses the current baton state and emits the exact next action (including copy-paste text for the other host). Designed so the user only has to remember `/<preset>-start`.
---

# <preset>-start — One-command orchestrator

This skill is the user's single entry point into the `<preset>`
workflow. It removes the need to remember the bootstrap sequence: CC
runs it, diagnoses the current state, and tells the user exactly what
to do next.

## When to invoke

- The user wants to start the first unit of work.
- The user wants to start the next unit (after a previous one closed).
- The user wants to resume or check status of an in-progress unit.
- Any time the user types `/<preset>-start`.

If `/<preset>-watch` is not armed in this session, this skill invokes it
automatically as the first step.

## Steps

### 1. Ensure the watcher is armed

Check whether the persistent Monitor with description
`<preset>: new files in _coord/from-codex/` is running.

- If TaskList shows it: skip.
- If not: invoke `/<preset>-watch`. Fail-stop on its failure.

### 2. Run both verifiers + artifact checker

```bash
python scripts/verify_<preset>_skills.py
python scripts/check_baton_artifacts.py
# also run other presets' verifiers (e.g., testkit) as sanity check
```

Fail-stop on any FAIL.

### 3. Diagnose the current baton state

Read the latest state of both mailboxes:

```bash
git ls-tree --name-only origin/master:workflows/<preset>/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort
git ls-tree --name-only origin/master:workflows/<preset>/_coord/from-cc   2>/dev/null | grep -v '^\.gitkeep$' | sort
```

Identify the most recent artifact and its first line `BatonNext:
<STATE>`.

Also identify the open unit id, if any. A unit is "open" if it has
artifacts without a matching `<unit-id>__close.md`.

### 4. Branch on state and emit the right next action

#### Branch A — No unit open yet

Emit the **other-host bootstrap text** as a copy-paste block. (Include
the exact files the other side must read, the verifier commands they
run, and a "reply ready when done" line.)

Then prompt the user (in chat) for:
- a unit id matching the format defined in CHARTER;
- a short goal description.

When the user supplies both, emit the **kickoff text** as a
copy-paste block including the lane the other side should open and the
expected `BatonNext`.

#### Branch B — Unit open and in progress

Look up the current state in `workflows/<preset>/HANDOFF.md` §3.1
state→lane table. Emit:

```text
<preset> status:
  Open unit:        <unit-id>
  Current state:    <STATE>
  Latest artifact:  <mailbox>/<filename>
  Next driver:      <CC | other>
  Next action:      <one sentence>
  Next lane skill:  <lane name>
```

If next driver is CC: offer to proceed now or wait.
If next driver is the other side: emit a short reminder message the
user can paste to them.

#### Branch C — Unit just closed

Report the `BatonNext:` (COMPLETED or BLOCKED_*) and the close.md
completion-criteria summary. Ask whether to start the next unit (back
to Branch A).

### 5. Final summary

Always print:

```text
<preset>-start: <branch A/B/C> -- <one-line summary of what was emitted>
```

## What this skill does NOT do

- Does not write any baton artifact itself.
- Does not pick unit ids or goal text.
- Does not push or pull anything beyond what `<preset>-watch` does.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Watcher won't arm | Surface failure. Do not continue. |
| Any verifier / checker FAIL | Surface FAIL output. Do not emit kickoff text. |
| More than one open unit | Artifact checker already FAILs; surface and stop. |
| Cannot read mailboxes | Surface error. |

## Related files

- `.claude/skills/<preset>-watch/SKILL.md`
- `workflows/<preset>/HANDOFF.md`
- `workflows/<preset>/CHARTER.md`
- `scripts/verify_<preset>_skills.py`, `scripts/check_baton_artifacts.py`
