---
name: blue-k-main-runner
description: "Execute Blue-K serial main packages under docs/mian-k/main from MAIN_PACKAGE_PROGRESS.md with a mandatory three-layer agent structure: the main runner owns package selection and progress-table writes, a package-runner subagent invokes stage-loop-auto for exactly one selected main package, and stage-loop-auto owns its own required subagents. Use when Codex is asked to run, continue, resume, or finish the Blue-K main trunk while preserving serial dependencies, updating progress, running code graph gates, and creating a full-repository clean checkpoint commit after each reliable package result."
---

# Blue K Main Runner

## Purpose

Run the Blue-K `mian-k\main` trunk as a strict serial queue. This skill is the
outer scheduler. It must not execute package work directly and must not invoke
`stage-loop-auto` in the main agent. It hands one main package at a time to a
package-runner subagent, waits for that subagent to finish, updates the progress
table, then selects the next package.

## Dependencies

Load these skills before execution:

- `stage-loop-auto`, for executing the selected main package.
- Repository code graph tooling under
  `scripts/code_graph`, for mandatory commit graph gate
  preparation and package-level candidate graph review.

The progress helper script is:

```text
blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py
```

Default K root:

```text
docs/mian-k
```

Default progress table:

```text
docs/mian-k\MAIN_PACKAGE_PROGRESS.md
```

Main package order source:

```text
docs/mian-k\main\PACKAGE_SET_INDEX.md
```

## Queue Contract

Use the progress table as the queue source of truth after it has been built.
Refresh it from `main\PACKAGE_SET_INDEX.md` before every selection while
preserving existing item statuses and notes.

Selection rule:

1. If any item is `running`, resume the first `running` item before starting
   new work.
2. Otherwise start the first `pending` item in ascending main order.
3. Stop when there is no `running` or `pending` item.

Do not execute `docs\mian-k\main` itself. It contains `PACKAGE_SET_INDEX.md`
and is a package-set root, not a minimum executable package. Execute only child
directories that have `PACKAGE_CHARTER.md`, package `scope.md`, and at least one
`stage-*` directory with `EXECUTE.md`.

## Strict Serial Contract

Run strictly serial at every layer:

- The main runner may have at most one package-runner subagent open for active
  main-package execution.
- The package-runner subagent may invoke `stage-loop-auto` for only one package.
- `stage-loop-auto` runs one eligible stage at a time.
- `stage-loop` runs one stage through one phase at a time and may only spawn the
  subagent required for the current phase or fix attempt.

Do not start a later numbered main package until all earlier main packages are
`done` or explicitly `skipped` by user instruction or accepted plan repair.

## Main Dependency Gate

Before handing any selected package to a package-runner subagent, including a
resumed `running` package, verify that all earlier main packages are complete:

- `done` is complete.
- `skipped` is complete only when the note records explicit user instruction or
  accepted plan repair.
- `blocked`, `pending`, or `running` earlier items block the later package.

The progress helper's `next` command returns `prior_incomplete`. Treat any
non-empty `prior_incomplete` list as a hard serial-admission blocker for the
selected package, even when the selected package is already `running`. Do not
resume a later `running` package while an earlier main package is incomplete;
repair the progress table or resume the earlier package instead.

The final integration package, usually `05_k1_integration_gate`, also depends
on required other-branch evidence named by `Kx_INDEX.md` and its package-local
documents. If that evidence is incomplete, stop that package as `blocked` or
keep it `running` when a recoverable dependency run is already underway; do not
invent other-branch acceptance.

## Subagent Spawn Retry Gate

Subagents are mandatory, but a no-subagent BLOCK is valid only after an actual
spawn attempt fails.

When a package-runner subagent cannot be spawned:

1. Confirm that no package-runner subagent is already active.
2. Close completed or no-longer-needed subagents from this runner session when
   tool support is available.
3. Retry spawning the package-runner subagent once.
4. If the retry also fails, keep the selected package `running` and stop with:

   ```text
   BLUE_K_MAIN_RUNNER_BLOCKED_NO_PACKAGE_SUBAGENT
   ```

Do not preemptively BLOCK only because the agent count may be high.

## Execution Loop

For each package:

1. Refresh the table:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" build --mian-k "docs/mian-k"
   ```

2. Select the next item:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" next --mian-k "docs/mian-k"
   ```

3. If `multiple_running` is true, stop and ask the user which running item to
   resume or repair the table.

4. Run the Main Dependency Gate for the selected item. If `prior_incomplete` is
   non-empty, stop with `BLUE_K_MAIN_RUNNER_BLOCKED_PRIOR_MAIN_INCOMPLETE`.

5. If the selected item is `pending`, mark it `running` before spawning the
   package-runner subagent:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status running --note "Starting stage-loop-auto."
   ```

6. Spawn exactly one package-runner subagent for the selected item.

   The main runner must give the subagent only:

   - selected progress index;
   - selected package path;
   - selector: `all` for a new `pending` item or `continue` for a resumed
     `running` item;
   - progress table path for read-only context;
   - the main serial dependency context for this one package;
   - instruction to load and use `stage-loop-auto`;
   - instruction to return result status, commits, commands, evidence verdict,
     blockers, dirty worktree status, and whether another resume is required.

   The package-runner subagent must not edit the progress table. The main
   runner is the only progress-table writer.

7. The package-runner subagent invokes `stage-loop-auto` on the selected package
   path:

   - Use selector `all` when starting a new `pending` item.
   - Use selector `continue` when resuming an existing `running` item.

8. When the package-runner subagent returns:

   - Mark `done` if the package finishes with ACCEPT or an acceptable WARN and
     no runner-level stop condition remains.
   - Mark `blocked` if `stage-loop-auto` reports BLOCK, EARLY_EXIT, failed
     admission, failed verification, missing contract files, dirty code-layer
     worktree, missing main prerequisite, missing required other-branch evidence
     for the integration gate, or another hard blocker.
   - Keep `running` if the conversation/tool execution is interrupted before a
     reliable final result is known. The next invocation must resume it with
     `stage-loop-auto continue`.

9. If a package was previously attempted but has durable work without the
   required stage-loop records, run the Unrecorded Work Recovery Gate before
   marking it blocked.

10. After the package result is reliable and before any checkpoint commit, run
   the Code Graph Package Gate.

11. After marking `done` or `blocked`, run the Full-Repository Clean Commit Gate
    before selecting another package.

12. After the clean commit gate passes, loop to the next item unless the user
    requested only one package.

## Unrecorded Work Recovery Gate

Use this gate when a main package has evidence that work was done but the normal
`stage-loop-auto` records are incomplete, such as missing `Stage:` execution
commits, missing traceable-review verdicts, generic checkpoint commits that
captured package changes, interrupted subagents, or evidence files that contain
PASS-like text without a reliable final package result.

Recovery policy:

1. Do not mark the package `done` from memory, chat history, or old terminal
   output. Git, filesystem, and fresh command output are the only durable
   evidence.
2. Search for persistent code and document evidence:
   - commits touching the package path or its Allowed Files;
   - staged or committed diffs for source, tests, evidence, and approval files;
   - existing tests, fixtures, evidence ledgers, and review artifacts;
   - `git log --grep="Stage: <stage-id>" -- <stage-dir>` for formal execution
     commits.
3. Treat persisted code or document changes as recoverable work. The next
   package-runner should use that evidence as source material and resume the
   same package rather than reimplementing blindly.
4. Treat tests and command results as ephemeral unless their exact command is
   rerun in the current recovery attempt. If the missing record is a test pass,
   rerun the required primary and compatibility commands and capture fresh
   output before accepting the result.
5. If durable code evidence exists but the formal execution commit is missing,
   instruct the package-runner to resume `stage-loop-auto` and reconcile the
   package by reading persisted diffs, rerunning required tests, persisting fresh
   verification output, correcting unfinished evidence status, and creating the
   required `Stage:` execution commit if `stage-loop-auto` permits recovery from
   the current state.
6. If no durable code or document evidence exists, rerun the package from the
   start of its current stage.
7. If at least three package-runner attempts for the same already-approved stage
   return no durable artifact at all, the main runner may run the Limited
   Main-Runner Closure Gate instead of looping indefinitely.

The main runner may perform read-only evidence discovery for this gate and may
update the progress table. It must not create the missing execution commit or
run `stage-loop-auto` directly; that remains package-runner responsibility.

## Limited Main-Runner Closure Gate

This is an emergency recovery valve for repeated no-artifact subagent loss. It
is not the normal path and must not be used merely for convenience.

The main runner may perform a narrow closure itself only when all conditions are
true:

1. The same stage has a committed approval artifact such as
   `REVIEW_TERMINATION.md` or an approval commit.
2. At least three package-runner attempts after that approval produced no
   durable artifact and no actionable BLOCK.
3. The package has one stage, explicit Allowed Files, and the required work is
   test-only or evidence-only, or source edits are mechanically proven by
   already-present dirty files.
4. The main runner can keep all edits inside Allowed Files and can run the exact
   required fresh commands.
5. The main runner records in evidence that closure used this emergency gate,
   lists the failed runner attempts, and preserves the normal structured commit
   message with the `Stage:` field.

When this gate is used, run fresh tests and scans, run the Code Graph Package
Gate after the closure commit, and resume the normal main flow only after the
repository is clean.

## Code Graph Package Gate

Follow the repository Code Graph Contract in `AGENTS.md`. The detailed command
source of truth is `scripts/code_graph/README.md`; do not duplicate that flow in
this skill.

After each package-runner returns a reliable result and before the checkpoint
commit, the main runner must stage the intended package result, prepare the code
graph gate, review the staged code diff plus candidate graph diff against source
and boundary contracts, apply only accepted overlay changes, and verify the gate
for the exact staged diff.

If the gate cannot be prepared, review is inconclusive, high-risk edges cannot
be source-verified, or the hook check fails, stop with:

```text
BLUE_K_MAIN_RUNNER_BLOCKED_CODE_GRAPH_GATE
```

## Runtime Infrastructure Review Handoff

When the selected package, its blockers, or its verification output touches
runtime infrastructure integration (Redis/cache/throttle, Channels, Dramatiq,
Temporal, DB connection/migrations, workers, background jobs, ports, env vars,
Docker/compose, CI/service topology, or deployment settings), the main runner
must include the traceable-review Runtime Infrastructure Context Gate in the
package-runner handoff. The package-runner final result must name which
Docker/compose/env/settings files it inspected before reporting a code defect or
environment blocker, and must classify findings as code defect,
environment/service defect, test-environment configuration defect, or
product/architecture decision. DB-backed pytest commands must be run serially
unless their databases are explicitly isolated.

## Full-Repository Clean Commit Gate

The main runner must leave the repository clean after every package attempt that
returns a reliable result.

After updating the progress table:

1. Locate the git repository that contains `docs/mian-k`.
2. Run `git status --short --branch`.
3. If the worktree is clean, record `clean checkpoint not needed` in the final
   runner report and continue.
4. If the worktree is dirty, create exactly one full-repository checkpoint
   commit:

   ```powershell
   git add -A
   git commit -m "docs(blue-k): checkpoint main package progress"
   ```

5. Run `git status --short --branch` again.
6. Continue only if the worktree is clean.

The commit is intentionally full-repository, not path-selective, so evidence,
progress-table updates, package docs, accepted overlay updates, code graph gate
evidence, and any executor leftovers are captured before the next package
begins. Do not start the next package with a dirty worktree.

If the commit fails or the worktree remains dirty, stop with:

```text
BLUE_K_MAIN_RUNNER_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

If the worktree is already dirty before the first package starts and there is no
selected `running` resume item, create one full-repository checkpoint commit
before selecting new work. If that preflight checkpoint fails or leaves the
worktree dirty, stop with the same blocker.

## Package-Runner Prompt

Use a concise prompt with this shape:

```text
Use $stage-loop-auto to execute exactly one Blue-K serial main package.

Package index: <index>
Package path: <path>
Selector: <all|continue>
Progress table: <path, read-only for you>
Main serial context: earlier main packages must already be accepted; do not
execute later packages or update the progress table.

You are not alone in the codebase. Do not revert edits made by others. Do not
update the progress table. Load the local stage-loop-auto skill and follow its
subagent requirements. Treat the code graph as navigation evidence only: use it
to find relevant source quickly, but verify behavior against source and package
contracts before trusting graph edges. If runtime infrastructure integration is
in scope, apply the traceable-review Runtime Infrastructure Context Gate and
report inspected Docker/compose/env/settings files plus finding classification.
Return: final verdict, execution commit(s), approval commit(s), commands run,
evidence status, blockers, WARN items, final worktree status,
graph-consumption notes, runtime-infrastructure notes when relevant, and whether
this package needs resume.
```

## Marking Examples

Successful completion:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status done --commit "<commit>" --note "stage-loop-auto ACCEPT."
```

Blocked completion:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status blocked --note "<exact blocker>"
```

Authorized skip only:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-main-runner/scripts/main_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status skipped --note "Explicit user instruction: <reason>."
```

## Mandatory Three-Layer Agent Boundary

This skill requires a three-layer execution structure:

1. Main runner agent: owns queue selection and progress-table writes.
2. Package-runner subagent: owns exactly one selected main package and invokes
   `stage-loop-auto`.
3. `stage-loop-auto` subagents: owns its internal `stage-loop`, doc-review,
   execution, and traceable-review subagent requirements.

The main runner must not call `stage-loop-auto` directly and must not implement
package work directly. The package-runner subagent must not bypass
`stage-loop-auto`. `stage-loop-auto` must not bypass its required subagents.

Do not pass the full blueprint or unrelated packages into the package-runner
subagent unless the selected package-local documents explicitly require
escalation.

Run only one main package at a time. After one package completes and the table is
updated, select the next package from the table again instead of reusing stale
queue state.

## Stop Conditions

Stop and report the exact blocker when:

- The progress table cannot be created or parsed.
- More than one item is `running`; ask the user which one to resume or repair
  the table.
- The selected path no longer exists.
- The selected path contains `PACKAGE_SET_INDEX.md`.
- An earlier main package is not complete
  (`BLUE_K_MAIN_RUNNER_BLOCKED_PRIOR_MAIN_INCOMPLETE`).
- The final integration gate lacks required other-branch evidence and no
  recovery path has been requested.
- The package-runner subagent cannot be spawned.
- The Code Graph Package Gate fails.
- `stage-loop-auto` stops with a hard blocker.
- Updating the progress table fails.
- The Full-Repository Clean Commit Gate fails or leaves the worktree dirty.
- The next action would require destructive git or filesystem operations.

If the user interrupts execution, leave the current item as `running`. On the
next use, resume that item before any pending item.
