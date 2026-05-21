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

This is the fresh-start path. Emit two blocks in the chat:

**Block A1 — Codex Host B bootstrap (copy-paste to Codex)**

````text
You are the Codex side of the temporal-phase workflow on Host B.

Bootstrap:

1) Sync repo:
   cd D:\code\gittest
   git pull origin master

2) Confirm registration (you should now see all 15 /temporal-phase-*
   lanes in your skill list):
   python scripts/verify_temporal_phase_skills.py
   python scripts/check_baton_artifacts.py

3) Read these files in order:
   workflows/temporal-phase/HANDOFF.md             (your entry point)
   workflows/temporal-phase/PATHS.md               (your row = Host B)
   workflows/temporal-phase/CHARTER.md
   workflows/temporal-phase/ROLES.md
   workflows/temporal-phase/BATON.schema.md
   workflows/temporal-phase/skills/temporal-phase-blueprint/SKILL.md
     (in particular its ## Tools section — it delegates to the work-repo
      skill temporal-stage-package-generator)

4) Arm a monitor on workflows/temporal-phase/_coord/from-cc/ so you see
   CC's audits / synthesis / repairs as they land.

5) Reply with exactly one line:
   "Codex ready on Host B for temporal-phase, waiting for Phase goal."

Then wait. Do NOT draft a blueprint until I give you a specific Phase
goal in the next message.
````

**Then prompt the user (in chat, not in a tool):**

> Please provide:
>   1. A phase-id matching `phase-\d+` (e.g., `phase-01`, `phase-11`).
>   2. A short Phase goal description (1-3 sentences).
>
> Once you paste those back, I'll generate the Phase-kickoff message
> for you to send to Codex.

**Block A2 — emit AFTER the user replies with phase-id + goal**

When the user supplies `<phase-id>` and `<goal>`, emit:

````text
<phase-id> goal:
<goal>

Open the temporal-phase-blueprint lane:
  - Follow its ## Tools section: switch focus to the Temporal work repo
    (PATHS.md → Host B → temporal: → D:\code\temporal\), follow
    temporal-stage-package-generator's procedure, produce the package
    directory under
      temporal:docs/skill-temporal-reorchestration/stage-loop-auto-packages/pending/<package-id>/
    with the full Generator output (PACKAGE_CHARTER, scope,
    HANDOFF_execute, HANDOFF_plan_review, GENERATION_REVIEW_REPORT,
    stage-NN/{EXECUTE,scope,evidence}.md).
  - Run the Generator's mandatory post-generation multi-agent review.
  - Then write the coord-side pointer file
    gittest:workflows/temporal-phase/_coord/from-codex/<phase-id>__blueprint.md
    with first line "BatonNext: PRE_AUDIT_R1" and the fields per the
    blueprint SKILL §3 "coord-side product".
  - Commit + push to origin/master.

Use phase-id `<phase-id>`. Do not start more than one Phase at a time.
````

substituting `<phase-id>` and `<goal>` verbatim.

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

Report COMPLETED vs BLOCKED_POSTEXEC from the close.md's `BatonNext:`
line. Show its CompletionCriteria summary. Then ask the user whether
they want to start the next Phase (re-enter Branch A) or stop.

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
