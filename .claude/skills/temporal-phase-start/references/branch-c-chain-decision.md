# Branch C — Phase just closed (chaining decision)

Reached when the latest artifact across both mailboxes is
`<phase-id>__close.md`. This branch reads the close + ChainMode and
decides whether to auto-advance, prompt for confirmation, or stop.

## Step C1 — read inputs

From close.md, extract:
- `BatonNext:` — terminal state (`COMPLETED` or `BLOCKED_POSTEXEC`).
- `CompletionCriteria:` summary (already produced by the close lane).
- `NextPhasePlan:` block (may be missing / empty).

From `workflows/_active.md`, find the `ChainMode:` line. Default to
`confirm` if absent or malformed.

Report the close to the user: terminal state + a brief
CompletionCriteria summary.

## Helper — phase-id collision check

Used multiple times below. Takes `<candidate-id>` (the id we are about
to use) and `<closed-id>` (the just-closed Phase, excluded from the
live-set since it is about to be archived):

```bash
ALL_IDS=$( {
  ls workflows/temporal-phase/_coord/from-cc/ workflows/temporal-phase/_coord/from-codex/ 2>/dev/null \
    | grep -oE '^phase-[a-zA-Z0-9][a-zA-Z0-9-]*';
  ls workflows/temporal-phase/_coord/archive/ 2>/dev/null \
    | grep -oE '^phase-[a-zA-Z0-9][a-zA-Z0-9-]*';
} | sort -u | grep -vx "<closed-id>" )
echo "$ALL_IDS" | grep -qx "<candidate-id>"

# Also catch reuse of the just-closed id (treated as collision):
[ "<candidate-id>" = "<closed-id>" ] && echo "CHAIN_COLLISION: <candidate-id> equals just-closed phase-id (reuse not allowed)"
```

If `grep -qx` returns 0 OR the reuse echo fires, treat as
`CHAIN_COLLISION`.

## Step C2 — decision tree (apply in order, stop at first match)

### 1. Hard-stop conditions (regardless of ChainMode)

- `BatonNext:` is `BLOCKED_*` → chain stops here. Surface
  `NextPhasePlan.StopReason:` if present, suggest manual triage. Skip
  to step C3 (archive prompt).
- `NextPhasePlan:` block missing or no `NextPhaseId:` → chain ended
  naturally. Cite `StopReason:` if given. Skip to C3.
- `NextPhaseId:` fails `^phase-[a-zA-Z0-9][a-zA-Z0-9\-]*$` regex →
  report `CHAIN_INVALID_ID`. Skip to C3.
- Helper returns collision → report
  `CHAIN_COLLISION: <NextPhaseId> already exists as <live|archived>`
  (or `reuse of just-closed`). Do NOT auto-advance. Skip to C3.

### 2. ChainMode = off

Report the close + the proposed `NextPhasePlan` for the user's
information. Take no further action. Ask about archiving (step C3)
only if the user explicitly asks.

### 3. ChainMode = confirm (default)

Present the proposed plan and ask:

> Phase `<closed-id>` is `<state>`. The close proposes `<NextPhaseId>`
> with goal "`<NextPhaseGoal>`" (anchor: `<NextSourceAnchor>`).
> Advance? [yes / edit / no]

- `yes` → proceed to auto-advance (step C4).
- `edit` → re-prompt the user for phase-id / goal / source-anchor
  (same prompts as Branch A step A1). **After collecting the
  edits, re-run the collision check on the user's new
  `<NextPhaseId>` against the same archive set.** If collision →
  report and re-prompt or stop. Only after the edited phase-id
  passes do we proceed to auto-advance.
- `no` → take no further action; ask about archiving (step C3).

### 4. ChainMode = auto

Proceed directly to auto-advance (step C4) without prompting.

## Step C3 — archive prompt (for non-auto paths)

Reached when `ChainMode = off`, the user said `no`, or a hard-stop
fired. Ask:

> Phase `<closed-id>` is closed and the chain is paused. Archive
> its artifacts to `_coord/archive/<closed-id>/`? [yes / no]

On `yes`:

```bash
python scripts/archive_phase.py <closed-id>
python scripts/check_baton_artifacts.py   # FAIL -> see step C4.3 cleanup; stop
git add -A workflows/temporal-phase/_coord/
git commit -m "archive: <closed-id> (<terminal-state>)"
git pull --rebase origin master            # tree clean now; rebase if needed
git push origin master
```

On `no`: take no further action.

## Step C4 — auto-advance (atomic chain commit)

Reached when `ChainMode = auto`, or `confirm` with user `yes`, or
`confirm` with `edit` after re-prompt + re-validation.

All archive + kickoff changes are wrapped in **one atomic commit** so
origin/master never sees a half-state.

The order — **commit first, rebase second** — is mandatory:
`git pull --rebase` refuses to run on a dirty working tree.

### C4.1 — move locally

```bash
python scripts/archive_phase.py <closed-id>
```

Moves files from `from-cc/`+`from-codex/` to
`_coord/archive/<closed-id>/`. Does NOT commit. Surface any FAIL and
stop.

### C4.2 — write next kickoff locally

Create
`workflows/temporal-phase/_coord/from-cc/<NextPhaseId>__kickoff.md`
following the same body shape as Branch A step A2 (see
`branch-a-fresh-start.md`), populating from `NextPhasePlan` (or the
user-edited values) plus:

```text
PreviousPhaseClose: gittest:workflows/temporal-phase/_coord/archive/<closed-id>/from-codex/<closed-id>__close.md
```

Do NOT commit yet.

### C4.3 — check the combined working tree

Run `python scripts/check_baton_artifacts.py`. It must see exactly
the new kickoff in live mailboxes (archive is ignored by the
checker).

**If it FAILs**: undo locally. `archive_phase.py` uses `shutil.move`,
so `git reset --hard HEAD` restores the *source* files but leaves
the untracked archive copies and untracked kickoff in place. All
three layers needed:

```bash
git reset --hard HEAD
rm -rf workflows/temporal-phase/_coord/archive/<closed-id>/
rm -f  workflows/temporal-phase/_coord/from-cc/<NextPhaseId>__kickoff.md
```

Surface the error and stop.

### C4.4 — one atomic commit

```bash
git add -A workflows/temporal-phase/_coord/
git commit -m "chain: archive <closed-id> + kickoff <NextPhaseId>"
```

### C4.5 — pull --rebase

Tree is clean now (everything is in the commit from C4.4); rebase
replays your commit on top of any concurrent pushes:

```bash
git pull --rebase origin master
```

If conflicts, surface and stop — do not resolve silently.

### C4.6 — push

```bash
git push origin master
```

If the push is rejected, surface and stop — the local commit is
still safe; the user can investigate. Do NOT auto-retry.

### C4.7 — report

```text
Chain advanced (atomic): <closed-id> archived, <NextPhaseId> kicked off.
  ChainMode:        <auto | confirm-confirmed | confirm-edited>
  Commit:           <short SHA>
  NewState:         DRAFTING_BLUEPRINT (Codex's turn -- next /temporal-phase-codex-sync picks it up)
```

## Final note

In all paths, after the work above completes (or after declining), end
with the SKILL.md §5 final summary line, e.g.:

```text
temporal-phase-start: Branch C -- chain advanced (phase-01 -> phase-02)
```

If the user wants to resume an interrupted chain after this branch
returns, the two normal recovery levers are: edit
`workflows/_active.md` `ChainMode:` to the desired value (auto /
confirm / off) and commit, or start a manual next Phase via Branch A.
