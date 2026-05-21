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

Fresh-start path. CC writes the kickoff as a git artifact and pushes
it; the other side's watcher (or its next sync skill) picks it up
from origin. **There is no copy-paste chat relay for the kickoff.**

> Do NOT emit kickoff text for chat relay — the kickoff is a git
> artifact. See PATTERNS P17 and ANTI-PATTERNS A13.

**Step A1 — prompt the user (in chat, not in a tool):**

> Please provide:
>   1. A unit-id matching the format defined in CHARTER.
>   2. A short goal description (1-3 sentences).
>   3. (Optional) A source-anchor for what this unit implements.
>   4. (Optional) The previous unit's close.md path (if any).

Wait for the user's reply.

**Step A2 — write the kickoff baton artifact locally.**

Create `workflows/<preset>/_coord/from-cc/<unit-id>__kickoff.md` with
first line `BatonNext: <initial-driver-state>` followed by the body
shape defined in `BATON.schema.md` for kickoff artifacts. Substitute
the user's `<unit-id>`, `<goal>`, `<source-anchor>`, and
`<previous-close>` verbatim.

**Step A3 — check before pushing.**

Run `python scripts/check_baton_artifacts.py` against the working
tree. **If it FAILs:**
```bash
rm workflows/<preset>/_coord/from-cc/<unit-id>__kickoff.md
```
Surface the error and stop. Nothing has been committed or pushed.

**Step A4 — collision check vs live + archive.**

check_baton_artifacts.py does not scan `_coord/archive/`. Confirm
`<unit-id>` is unused across the full history:

```bash
ALL_IDS=$( {
  ls workflows/<preset>/_coord/from-cc/ workflows/<preset>/_coord/from-codex/ 2>/dev/null \
    | grep -oE '^<unit-id-regex>';
  ls workflows/<preset>/_coord/archive/ 2>/dev/null \
    | grep -oE '^<unit-id-regex>';
} | sort -u )
echo "$ALL_IDS" | grep -qx "<unit-id>" && echo "CHAIN_COLLISION: <unit-id> already in use" && exit 1
```

On collision: delete the local file, report `CHAIN_COLLISION`, and
ask the user for a different `<unit-id>`.

**Step A5 — commit, then rebase, then push.**

The commit must exist BEFORE pulling — `git pull --rebase` refuses to
run on a dirty working tree, so the order is mandatory:

```bash
git add workflows/<preset>/_coord/from-cc/<unit-id>__kickoff.md
git commit -m "kickoff(<unit-id>): start unit"
git pull --rebase origin master
git push origin master
```

If rebase has conflicts, surface and stop — do not resolve silently.
If push is rejected (hook, branch protection), surface and stop; the
local commit is intact.

**Step A6 — report result. NO copy-paste text emission.**

```text
Kickoff pushed.
  File:    workflows/<preset>/_coord/from-cc/<unit-id>__kickoff.md
  Commit:  <short SHA>
  State:   <initial-driver-state> (<other-side>'s turn)
```

**First-time onboarding (only if the OTHER side has never participated
in `<preset>` before, on its host).** Emit ONCE for the user to paste:

```text
You are the <other side> of the <preset> workflow on <host>.
Read workflows/<preset>/HANDOFF.md, then run /<preset>-<other-side>-sync.
```

After that one-time onboarding, future units never need a chat relay —
the kickoff file is the only signal.

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

#### Branch C — Unit just closed (last artifact is `close.md`)

Read close.md to extract `BatonNext:` (terminal state), the
completion-criteria summary, and the `NextPhasePlan:` block (may be
missing / empty). Then read `workflows/_active.md` to find the
`ChainMode:` line (default `confirm` if absent / malformed).

**Helper — unit-id collision check (used below):**

```bash
ALL_IDS=$( {
  ls workflows/<preset>/_coord/from-cc/ workflows/<preset>/_coord/from-codex/ 2>/dev/null \
    | grep -oE '^<unit-id-regex>';
  ls workflows/<preset>/_coord/archive/ 2>/dev/null \
    | grep -oE '^<unit-id-regex>';
} | sort -u )
echo "$ALL_IDS" | grep -qx "<candidate-id>"   # exit 0 = collision
```

Exclude `<closed-id>` when validating `<NextUnitId>` (the closing
unit's artifacts are still live).

**Decision tree — apply in order, stopping at the first match:**

1. **Hard-stop conditions** (regardless of `ChainMode`):
   - `BatonNext:` is `BLOCKED_*` → chain stops here; surface
     `NextPhasePlan.StopReason:` if present.
   - `NextPhasePlan:` block missing or no `NextUnitId:` → chain ended
     naturally; cite `StopReason:` if given.
   - `<NextUnitId>` fails id regex → report `CHAIN_INVALID_ID`.
   - Helper above returns collision (excluding `<closed-id>`) →
     report `CHAIN_COLLISION: <NextUnitId> already exists as
     <live|archived>`. Do NOT auto-advance.

2. **`ChainMode = off`** → report close + proposed `NextPhasePlan`
   for information only. Offer archive (step 5) only on user request.

3. **`ChainMode = confirm`** (default) → present the proposed plan
   and ask `[yes / edit / no]`. On `edit`, re-prompt for
   id / goal / source-anchor and **re-run the collision check** on
   the new id. Only after the edited id passes do we proceed.

4. **Auto-advance** (`ChainMode = auto`, or `confirm`+`yes`, or
   `confirm`+`edit` after re-validation). All archive + kickoff
   changes are wrapped in **one atomic commit** so origin/master
   never sees a half-state. The order — **commit first, rebase
   second** — is mandatory:

   1. **Archive locally.** `python scripts/archive_phase.py <closed-id>`
      (or the preset's equivalent). Moves files from `from-cc/`+
      `from-codex/` into `_coord/archive/<closed-id>/`. Does NOT
      commit. Surface any FAIL and stop.
   2. **Write next kickoff locally.** Create
      `workflows/<preset>/_coord/from-cc/<NextUnitId>__kickoff.md`
      from `NextPhasePlan` (or user-edited values), with
      `PreviousPhaseClose:` pointing at
      `_coord/archive/<closed-id>/from-<other>/<closed-id>__close.md`.
   3. **Check the combined working tree.**
      `python scripts/check_baton_artifacts.py` — must PASS. **If
      FAILs**, undo all three layers:
      ```bash
      git reset --hard HEAD
      rm -rf workflows/<preset>/_coord/archive/<closed-id>/
      rm -f  workflows/<preset>/_coord/from-cc/<NextUnitId>__kickoff.md
      ```
      Surface error; do not push.
   4. **Atomic commit.**
      ```bash
      git add -A workflows/<preset>/_coord/
      git commit -m "chain: archive <closed-id> + kickoff <NextUnitId>"
      ```
   5. **Pull --rebase** (tree clean now):
      ```bash
      git pull --rebase origin master
      ```
      Conflicts → surface and stop.
   6. **Push.**
      ```bash
      git push origin master
      ```
   7. **Report** the chain advance with `ChainMode`, commit SHA, and
      the new baton state.

5. **Archive prompt for non-auto paths** (`off`, `no`, hard-stop) —
   if the user opts to archive, use the same
   commit-before-rebase order (archive → check → add → commit →
   pull --rebase → push).

See PATTERNS P20 (chain-mode) and AUDIT-LESSONS Lessons 6+7
(check-before-push, atomicity).

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
| Artifact checker FAILs after archive + write | `git reset --hard HEAD; rm -rf _coord/archive/<closed-id>/; rm -f _coord/from-cc/<NextUnitId>__kickoff.md`; surface error; do not push. |

## Related files

- `.claude/skills/<preset>-watch/SKILL.md`
- `workflows/<preset>/HANDOFF.md`
- `workflows/<preset>/CHARTER.md`
- `scripts/verify_<preset>_skills.py`, `scripts/check_baton_artifacts.py`
