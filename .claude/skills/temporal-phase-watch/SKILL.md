---
name: temporal-phase-watch
description: Boot CC's temporal-phase coord watchers. Use at the start of any Claude Code session that participates in the temporal-phase workflow. Pulls origin, verifies registrations, validates baton artifacts, arms a persistent Monitor for new Codex artifacts in workflows/temporal-phase/_coord/from-codex/. Idempotent within a session, and independent from other workflow watchers (multiple workflows can run their watchers in parallel).
---

# temporal-phase-watch — Boot CC's temporal-phase coord watchers

Set up CC's side of the **temporal-phase** workflow preset. Each step
is idempotent; safe to run alongside other workflow watchers (e.g.,
`bk-watch`) since each only touches its own workflow's coord directory.

## When to invoke

- Start of any CC session participating in the temporal-phase workflow.
- After anything that may have killed background tasks.
- Any time you want to confirm watchers are armed and the registry is consistent.

This skill does **not** check `workflows/_active.md` (informational
only). Multiple workflows can be enabled simultaneously, each with its
own watcher.

## Steps

Follow in order. On failure, stop and surface — never arm watchers against a broken baseline.

### 1. Inspect already-running tasks

Load `TaskList` via `ToolSearch` if needed, list running tasks, and
check whether a Monitor with description
`temporal-phase: new files in _coord/from-codex/` is already armed.
Record the result; do not restart an already-running Monitor.

### 2. Pull origin

Run `git pull origin master`. Report any new commits. If pull fails
(conflict / diverged), stop and surface — do not start watchers.

### 3. Verify temporal-phase skill registrations

Run `python scripts/verify_temporal_phase_skills.py` (expect
`PASS: temporal-phase skills verified`) and the testkit verifier
`python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py`
(both presets share `.codex/skills.json`). Stop on any FAIL.

### 3.5. Validate runtime baton artifacts

Run `python scripts/check_baton_artifacts.py` — catches malformed
filenames, missing/illegal `BatonNext:` lines, authority violations,
and more-than-one open Phase. Stop on FAIL (fixes need human triage).

### 4. Check baton state (informational, non-blocking)

List the most recent files under origin/master in both mailboxes
(`workflows/temporal-phase/_coord/from-codex` and `from-cc`) via
`git ls-tree --name-only`. If either is empty, note "no Phase started
yet" but continue — the monitor will catch new files when they land.

### 5. Arm Monitor — new files in from-codex/ (if not running)

Skip if step 1 found the Monitor already armed. Otherwise start it.
See `references/monitor-command.md` for the exact command + shell
requirement (bash-only).

### 6. Report status

Print exactly this block, populated from the steps above:

```text
temporal-phase-watch status:
  OriginHead:                <short SHA from step 2>
  TemporalPhaseVerifier:     <PASS or FAIL summary from step 3>
  TestkitVerifier:           <PASS or FAIL summary from step 3>
  BatonArtifacts:            <PASS / FAIL summary from step 3.5>
  FromCodex mailbox:         <count> files
  FromCC mailbox:            <count> files
  Monitor (from-codex):      <already-running / newly-started / failed>
```

## Event handling

When the Monitor fires (`NEW_FROM_CODEX: <filename>`), look up the
step-tag in `references/event-handling.md` and follow the reaction
described there. The `close` step-tag has special chaining semantics —
see that file for details.

## Failure modes

See `references/failure-modes.md` for the symptom → required-behavior
table. General principle: never arm watchers against a broken baseline.

## What this skill does NOT do

- Does not write or review baton artifacts — those are lane-driven, reactive choices.
- Does not start Codex's side — Codex on Host B sets up via `workflows/temporal-phase/HANDOFF.md`.
- Does not modify `.claude/settings.json`. The SessionStart hook already
  reminds CC to run this skill when `_active.md` is temporal-phase.

## Related files

- `references/event-handling.md` — step-tag → reaction table for Monitor events.
- `references/monitor-command.md` — exact Monitor command + bash shell requirement.
- `references/failure-modes.md` — symptom → required-behavior table.
- `workflows/_active.md` — active preset pointer (must be `temporal-phase`).
- `workflows/temporal-phase/HANDOFF.md` — Codex-side entry; read once for context.
- `workflows/temporal-phase/_coord/from-codex/` — Codex artifacts watched by the Monitor.
- `workflows/temporal-phase/_coord/from-cc/` — CC artifacts written per lane.
- `scripts/verify_temporal_phase_skills.py` — registration verifier.
- `scripts/check_baton_artifacts.py` — runtime artifact validator.
- `workflows/temporal-phase/ROLES.md` Step Matrix — lane to invoke per artifact.
- `workflows/temporal-phase/BATON.schema.md` — state machine.
