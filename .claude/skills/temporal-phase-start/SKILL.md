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

4. **Check before committing.** Run `python scripts/check_baton_artifacts.py`
   against the working tree. The new kickoff is present locally;
   the checker confirms filename, BatonNext, mailbox routing, and
   single-open-Phase. **If it FAILs**: delete the local file
   (`rm workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md`),
   surface the error, and stop. Nothing has been committed or pushed.

5. **Collision check vs archive.** Even though check_baton_artifacts.py
   ensures no other Phase is open in live mailboxes, it does NOT scan
   `_coord/archive/`. Confirm `<phase-id>` is unused across the full
   history:

   ```bash
   ALL_IDS=$( {
     ls workflows/temporal-phase/_coord/from-cc/ workflows/temporal-phase/_coord/from-codex/ 2>/dev/null \
       | grep -oE '^phase-[0-9]+';
     ls workflows/temporal-phase/_coord/archive/ 2>/dev/null \
       | grep -oE '^phase-[0-9]+';
   } | sort -u )
   echo "$ALL_IDS" | grep -qx "<phase-id>" && echo "CHAIN_COLLISION: <phase-id> already in use" && exit 1
   ```
   On collision: delete the local file, report `CHAIN_COLLISION`,
   ask the user to pick a different phase-id, and stop.

6. Stage and commit:
   ```bash
   git add workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
   git commit -m "kickoff(<phase-id>): start Phase per temporal-phase workflow"
   ```

7. **Pull --rebase, then push.** Absorb any concurrent pushes before
   sending yours:
   ```bash
   git pull --rebase origin master
   git push origin master
   ```
   If the rebase has conflicts, surface them and stop — do not resolve
   silently. If the push is rejected by some other rule (hook, branch
   protection), surface and stop.

**Step A3 — tell the user what happens next.**

```text
Kickoff pushed.
  File:    workflows/temporal-phase/_coord/from-cc/<phase-id>__kickoff.md
  Commit:  <short SHA>
  State:   DRAFTING_BLUEPRINT (Codex's turn)

The kickoff is now on origin/master. Codex on Host B does NOT have a
live watcher -- the next time the user opens Codex (or runs
/temporal-phase-codex-sync), Codex will pick up the kickoff and enter
the temporal-phase-blueprint lane.
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

**Helper — phase-id collision check (used multiple times below):**

```bash
ALL_IDS=$( {
  ls workflows/temporal-phase/_coord/from-cc/ workflows/temporal-phase/_coord/from-codex/ 2>/dev/null \
    | grep -oE '^phase-[0-9]+';
  ls workflows/temporal-phase/_coord/archive/ 2>/dev/null \
    | grep -oE '^phase-[0-9]+';
} | sort -u )
echo "$ALL_IDS" | grep -qx "<candidate-id>"   # exit 0 = collision
```

Note: live mailboxes still contain the closing Phase's artifacts at
this point — that is expected, and the closing phase-id will appear in
`ALL_IDS`. Exclude `<closed-id>` from collision matching when
validating `<NextPhaseId>`.

**Decision tree — apply in order, stopping at the first match:**

1. **Hard stop conditions** (regardless of `ChainMode`):
   - `BatonNext:` is `BLOCKED_*` → tell the user the chain stops here,
     surface `NextPhasePlan.StopReason:` if present, suggest manual
     triage. Skip to step 5 (archive prompt).
   - `NextPhasePlan:` block is missing or has no `NextPhaseId:` → tell
     the user the chain ended naturally (cite `StopReason:` if
     given). Skip to step 5.
   - `NextPhaseId:` matches `^phase-\d+$` fails → report
     `CHAIN_INVALID_ID`. Skip to step 5.
   - **Run the helper above** with `<NextPhaseId>` (excluding
     `<closed-id>`). If it returns collision → report
     `CHAIN_COLLISION: <NextPhaseId> already exists as
     <live|archived>`. **Do not** auto-advance. Skip to step 5.

2. **`ChainMode = off`** → report the close and the proposed
   `NextPhasePlan` for the user's information. Take no further action.
   Ask about archiving (step 5) only if the user explicitly asks.

3. **`ChainMode = confirm`** (default) → present the proposed plan and
   ask:

   > Phase `<closed-id>` is `<state>`. The close proposes
   > `<NextPhaseId>` with goal "`<NextPhaseGoal>`" (anchor:
   > `<NextSourceAnchor>`). Advance? [yes / edit / no]

   - `yes` → proceed with auto-advance (step 4).
   - `edit` → re-prompt the user for phase-id / goal / source-anchor
     (same prompts as Branch A step A1). **After collecting the
     edits, re-run the collision check on the user's new
     `<NextPhaseId>`.** If collision → report and re-prompt or stop.
     Only after the edited phase-id passes the collision check,
     proceed with auto-advance.
   - `no` → take no further action; ask about archiving (step 5).

4. **Auto-advance** (`ChainMode = auto`, or `confirm` with user `yes`,
   or `confirm` with `edit` after re-prompt + re-validation). All
   archive + kickoff changes are wrapped in **one atomic commit** so
   that origin/master never sees a half-state.

   1. **Move locally.** Run `python scripts/archive_phase.py <closed-id>`.
      This moves files from `from-cc/`+`from-codex/` to
      `_coord/archive/<closed-id>/`. It does NOT commit. Surface any
      FAIL and stop.
   2. **Write next kickoff locally.** Create
      `workflows/temporal-phase/_coord/from-cc/<NextPhaseId>__kickoff.md`
      following the same body shape as Branch A step A2, populating
      from `NextPhasePlan` (or the user-edited values) plus
      `PreviousPhaseClose: gittest:workflows/temporal-phase/_coord/archive/<closed-id>/from-codex/<closed-id>__close.md`.
      Do NOT commit yet.
   3. **Check the combined working tree.** Run
      `python scripts/check_baton_artifacts.py`. It must see exactly
      the new kickoff in live mailboxes (archive is ignored). **If it
      FAILs**: undo locally with
      ```bash
      git reset --hard HEAD
      rm -f workflows/temporal-phase/_coord/from-cc/<NextPhaseId>__kickoff.md
      ```
      (the `git reset --hard` restores the tracked files that
      archive_phase.py moved; the `rm` removes the still-untracked new
      kickoff.) Surface the error and stop.
   4. **Pull --rebase.** Absorb any concurrent pushes that landed
      during the work above:
      ```bash
      git pull --rebase origin master
      ```
      If conflicts, surface and stop.
   5. **One atomic commit.** Stage archive + kickoff together:
      ```bash
      git add -A workflows/temporal-phase/_coord/
      git commit -m "chain: archive <closed-id> + kickoff <NextPhaseId>"
      ```
   6. **Push.**
      ```bash
      git push origin master
      ```
      If the push is rejected, surface and stop — the local commit is
      still safe; the user can investigate. Do NOT auto-retry.
   7. **Report.**
      ```text
      Chain advanced (atomic): <closed-id> archived, <NextPhaseId> kicked off.
        ChainMode:        <auto | confirm-confirmed | confirm-edited>
        Commit:           <short SHA>
        NewState:         DRAFTING_BLUEPRINT (Codex's turn -- next /temporal-phase-codex-sync picks it up)
      ```

5. **Archive prompt for non-auto paths** (`off`, `no`, or hard-stop):
   Ask:

   > Phase `<closed-id>` is closed and the chain is paused. Archive
   > its artifacts to `_coord/archive/<closed-id>/`? [yes / no]

   On `yes`: run `archive_phase.py`, then check before commit, then
   pull --rebase, then commit + push:
   ```bash
   python scripts/archive_phase.py <closed-id>
   python scripts/check_baton_artifacts.py   # FAIL -> git reset --hard HEAD; stop
   git pull --rebase origin master
   git add -A workflows/temporal-phase/_coord/
   git commit -m "archive: <closed-id> (<terminal-state>)"
   git push origin master
   ```

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
