---
name: temporal-phase-start
description: One-command orchestrator for the temporal-phase workflow. Use whenever the user wants to start a new Phase, resume an in-progress Phase, or check "where are we" — this skill diagnoses the current baton state and emits the exact next action (including copy-paste-able messages for the Codex side on Host B). Designed so the user only has to remember `/temporal-phase-start`.
---

# temporal-phase-start — One-command orchestrator

This skill is the user's single entry point into the `temporal-phase`
workflow. It removes the need to remember the bootstrap sequence: CC
runs it, diagnoses the current state, and tells the user exactly what
to do next.

## When to invoke

- The user wants to start the first Phase.
- The user wants to start the next Phase (after a previous Phase
  closed).
- The user wants to resume / check status of an in-progress Phase.
- Any time the user types `/temporal-phase-start`.

If the user has not yet invoked `/temporal-phase-watch` in this session,
this skill invokes it automatically as the first step.

## Steps

### 1. Ensure the watcher is armed

Check whether the persistent Monitor with description
`temporal-phase: new files in _coord/from-codex/` is running.

- If TaskList shows it: skip.
- If not: invoke `/temporal-phase-watch` first. If that skill fails any
  precondition, stop and surface the failure.

### 2. Run both verifiers + the artifact checker

```bash
python scripts/verify_temporal_phase_skills.py
python scripts/check_baton_artifacts.py
python blue-k-git-baton-testkit/scripts/verify_project_scoped_skills.py
```

If any FAIL: surface the FAIL output and stop. Fixes typically need
human triage.

### 3. Diagnose the current baton state

Read the latest state of both mailboxes:

```bash
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-codex 2>/dev/null | grep -v '^\.gitkeep$' | sort
git ls-tree --name-only origin/master:workflows/temporal-phase/_coord/from-cc   2>/dev/null | grep -v '^\.gitkeep$' | sort
```

Identify the most recent artifact (by filename ordering / mtime) and
read its first line to extract `BatonNext: <STATE>`. That `<STATE>` is
the current baton state.

Also identify the open Phase ID (if any). A Phase is "open" if it has
artifacts in either mailbox without a matching `<phase-id>__close.md`.

### 4. Branch on state and emit the right next action

#### Branch A — No Phase open yet (both mailboxes empty of phase artifacts)

This is the fresh-start path. The user supplies a phase-id + goal in
chat; CC then writes a kickoff baton artifact and pushes it. Codex's
watcher on the other host picks up the kickoff and enters
`DRAFTING_BLUEPRINT` automatically. There is **no copy-paste relay**.

**Step A1 — prompt the user (in chat, not in a tool):**

> Please provide:
>   1. A phase-id matching `phase-\d+` (e.g., `phase-01`, `phase-11`).
>   2. A short Phase goal description (1-3 sentences).
>   3. (Optional) A source-document anchor: a short string identifying
>      the section of the Temporal workflow doc this Phase implements.
>   4. (Optional) The previous Phase's close.md path (if any).

Wait for the user's reply.

**Step A2 — write the kickoff baton artifact.**

When the user supplies `<phase-id>`, `<goal>`, and (optionally)
`<source-anchor>` / `<previous-close>`:

1. Confirm `<phase-id>` matches `^phase-\d+$`. If not, ask again.
2. Verify no other Phase is open (the artifact checker already gates
   this; if a different open phase-id exists, surface the conflict and
   stop).
3. Write `workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md`
   with the following body (substitute the user's values verbatim):

   ````text
   BatonNext: DRAFTING_BLUEPRINT

   # Phase <phase-id> — Kickoff

   PhaseId: <phase-id>
   StartedBy: CC (Host A)
   StartedAt: <current ISO-8601 UTC timestamp>

   Goal:
   <goal>

   SourceAnchor:
   <source-anchor or "N/A">

   PreviousPhaseClose:
   <previous-close path resolved via PATHS.md, or "N/A (first Phase)">

   Notes for Codex (blueprint lane):
   - Follow `workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md`.
   - Its `## Tools` section delegates to the work-repo skill
     `temporal-stage-package-generator`. Generator SKILL.md resolves
     via `PATHS.md` to
     `temporal:.codex/skills/temporal-stage-package-generator/SKILL.md`.
   - Use phase-id `<phase-id>` consistently in package-id selection
     and product filenames.
   ````

4. Stage, commit, and push:

   ```bash
   git add workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
   git commit -m "kickoff(<phase-id>): start Phase per temporal-phase workflow"
   git push origin master
   ```

5. Run `python scripts/check_baton_artifacts.py` to confirm the kickoff
   is well-formed (filename, BatonNext, mailbox routing, single open
   Phase). If it FAILs, undo the commit and surface the error.

**Step A3 — tell the user what happens next.**

```text
Kickoff pushed.
  File:    workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
  Commit:  <short SHA>
  State:   DRAFTING_BLUEPRINT (Codex's turn)

Codex on Host B will detect the kickoff via its watcher and enter the
temporal-phase-blueprint lane. No further action needed from you
until Codex pushes the blueprint pointer to from-codex/. You will be
notified when that arrives.
```

**First-time Codex bootstrap (only if Codex has never been told about
this workflow on Host B).** If the user mentions that Codex on Host B
has never participated in temporal-phase before, also emit one short
line for them to paste once:

```text
You are the Codex side of the temporal-phase workflow on Host B.
Read workflows/temporal-phase/HANDOFF.md, then run /temporal-phase-codex-sync.
From now on, run /temporal-phase-codex-sync at every session start.
```

After that one-time onboarding, future Phases never need a chat
relay — the kickoff file is the only signal. Codex does not need to
stay online between Phases; `/temporal-phase-codex-sync` catches up on
anything pending whenever Codex boots.

#### Branch B — Phase open and in progress

Find the latest artifact and its `BatonNext: <STATE>`. Then look up the
state in `workflows/temporal-phase/HANDOFF.md` §3.1 to see which lane
runs next.

Emit a short status block:

```text
temporal-phase status:
  Open Phase:       <phase-id>
  Current state:    <STATE>
  Latest artifact:  <mailbox>/<filename>
  Next driver:      <CC | Codex>
  Next action:      <one sentence describing what should happen next>
  Next lane skill:  <lane name, e.g. temporal-phase-pre-audit-cc>
```

If next driver is **CC**, also tell the user CC is ready to run that
lane and ask if they want to proceed now or wait.

If next driver is **Codex**, output a short message the user can paste
to Codex on Host B reminding them which lane to open:

```text
The baton is at <STATE>. Please open the <lane> lane:
  workflows/temporal-phase/skills/<lane>/SKILL.md
Read it and produce the corresponding artifact in
workflows/temporal-phase/_coord/from-codex/. Commit + push.
```

#### Branch C — Phase just closed (last artifact is `close.md`)

Read the close.md to extract:

- `BatonNext:` — terminal state (`COMPLETED` or `BLOCKED_POSTEXEC`).
- `CompletionCriteria:` — summary (already done by the close lane).
- `NextPhasePlan:` block (may be missing / empty).

Report the close to the user (terminal state + a brief
CompletionCriteria summary).

Then read `workflows/_active.md` to find the `ChainMode:` line (default
to `confirm` if absent or malformed).

**Decision tree — apply in order, stopping at the first match:**

1. **Hard stop conditions** (regardless of `ChainMode`):
   - `BatonNext:` is `BLOCKED_*` → tell the user the chain stops here,
     surface `NextPhasePlan.StopReason:` if present, suggest manual
     triage. Skip to step 5 (archive).
   - `NextPhasePlan:` block is missing or has no `NextPhaseId:` → tell
     the user the chain ended naturally (cite `StopReason:` if
     given). Skip to step 5.
   - `NextPhaseId:` collides with any live mailbox phase-id or any
     archived phase-id → report a `CHAIN_COLLISION` error with the
     conflicting ids. **Do not** auto-advance. Skip to step 5.

2. **`ChainMode = off`** → report the close and the proposed
   `NextPhasePlan` for the user's information. Take no further action.
   Skip to step 5 only if the user explicitly asks to archive.

3. **`ChainMode = confirm`** (default) → present the proposed plan and
   ask:

   > Phase `<closed-id>` is `<state>`. The close proposes
   > `<NextPhaseId>` with goal "`<NextPhaseGoal>`" (anchor:
   > `<NextSourceAnchor>`). Advance? [yes / edit / no]

   - `yes` → proceed with auto-advance (step 4).
   - `edit` → re-prompt the user for phase-id / goal / source-anchor
     (same prompts as Branch A step A1), then proceed with
     auto-advance using the edited values.
   - `no` → take no further action; ask about archiving (step 5).

4. **Auto-advance** (`ChainMode = auto`, or `confirm` with user `yes`,
   or `confirm` with `edit` after re-prompt):
   1. Run `python scripts/archive_phase.py <closed-id>`; surface any
      FAIL.
   2. Stage + commit + push the archive:
      ```bash
      git add -A workflows/temporal-phase/_coord/
      git commit -m "archive: <closed-id> (<terminal-state>)"
      git push origin master
      ```
   3. Re-run `python scripts/check_baton_artifacts.py` to confirm
      clean mailboxes.
   4. Write the next kickoff `from-cc/<NextPhaseId>__kickoff.md`
      following the same format as Branch A step A2, populating from
      `NextPhasePlan` (or the user-edited values) and adding
      `PreviousPhaseClose: gittest:workflows/temporal-phase/_coord/archive/<closed-id>/from-codex/<closed-id>__close.md`.
   5. Stage + commit + push the kickoff:
      ```bash
      git add workflows/temporal-phase/_coord/from-cc/<NextPhaseId>__kickoff.md
      git commit -m "kickoff(<NextPhaseId>): chained from <closed-id>"
      git push origin master
      ```
   6. Run `check_baton_artifacts.py` once more to confirm the new
      open Phase is well-formed.
   7. Report:
      ```text
      Chain advanced: <closed-id> archived, <NextPhaseId> kicked off.
        ChainMode:        <auto | confirm-confirmed | confirm-edited>
        NewState:         DRAFTING_BLUEPRINT (Codex's turn)
      ```

5. **Archive prompt for non-auto paths** (`off`, `no`, or hard-stop):
   Ask:

   > Phase `<closed-id>` is closed and the chain is paused. Archive
   > its artifacts to `_coord/archive/<closed-id>/`? [yes / no]

   On `yes`: run archive_phase.py + commit + push (same steps as 4.1
   through 4.3), then stop.

In all branches, end with a clear summary of what happened and what
the user can do next (resume the chain by editing `ChainMode`, or
start a manual Phase via Branch A).

### 5. Final summary

Always print a one-line summary at the end:

```text
temporal-phase-start: <branch A/B/C> -- <one-line summary of what was emitted>
```

## What this skill does NOT do

- It does NOT write any baton artifact itself (no blueprints, no
  audits). Those are still produced by the matching lane skills.
- It does NOT decide phase-ids or Phase goals — those come from the
  user.
- It does NOT push or pull anything; it only reads (via git ls-tree)
  and emits text. Only the user's explicit next actions (or other
  skills) push.

## Failure modes

| Symptom | Required behavior |
|---|---|
| Watcher won't arm (`/temporal-phase-watch` fails) | Surface the failure. Do not continue. |
| Any verifier or checker FAIL | Surface the FAIL output. Do not emit the bootstrap or kickoff messages. |
| More than one open Phase | The artifact checker will already FAIL; surface that and stop. |
| Cannot read `_coord/` mailboxes | Surface the error. |

## Related files

- `.claude/skills/temporal-phase-watch/SKILL.md` — watcher.
- `workflows/temporal-phase/HANDOFF.md` — Codex entry; this skill emits
  text that references it.
- `workflows/temporal-phase/CHARTER.md` — phase-id rules.
- `scripts/verify_temporal_phase_skills.py`, `scripts/check_baton_artifacts.py` —
  validation gates.
