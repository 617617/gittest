---
name: blue-k-other-runner
description: "Execute Blue-K minimum packages under docs/mian-k/other from OTHER_MIN_PACKAGE_PROGRESS.md with a mandatory three-layer agent structure: the main runner owns the progress table, a package-runner subagent invokes stage-loop-auto for exactly one selected package, and stage-loop-auto owns its own required subagents. Use when Codex is asked to run, continue, resume, or finish the ordered other-package queue while updating the progress table, creating a full-repository clean checkpoint commit after each package result, and resuming interrupted running packages before starting new pending packages."
---

# Blue K Other Runner

## Purpose

Run the Blue-K `mian-k\other` queue from a progress table. This skill is the
outer scheduler. It must not execute package work directly and must not invoke
`stage-loop-auto` in the main agent. It hands one minimum executable package at
a time to a package-runner subagent, waits for that subagent to finish, updates
the table, then selects the next package.

## AI Chat Contract (v0.10)

This skill runs only inside a Blue-K baton chat selected by `bk sync`. Three
hard rules apply on every invocation — full text in
`blue-k-git-baton-testkit/references/ai-chat-contract.md`:

1. **First reply** begins with `I am <CC|Codex>. Lane: <lane>.` before any
   tool call or repo read. The human matches this against the `WindowMatch`
   hint printed by `bk sync`.
2. **Wrong-window input must refuse.** If this chat does not match the
   `ChatTarget` printed by the latest `bk sync`, do not acquire a lease,
   edit files, or call any Blue-K skill; reprint the correct
   `ChatTarget` / `ChatCommand` and stop.
3. **Finalize with a fixed closing line.** After one safe assignment, push
   the work branch and coordination branch atomically, write the next
   holder into `BATON.yaml`, and end the reply with exactly
   `Done. Now run: bk sync`. Do not chain into the next package, lane, or
   assignment.

For `/bk takeover`, no destructive recovery may begin before the human types
`yes, abandon` in this chat.

## Dependencies

Load these skills before execution:

- `blue-k-other-index`, for discovery and progress-table updates.
- `stage-loop-auto`, for executing the selected minimum executable package.
- Repository code graph tooling under
  `scripts/code_graph`, for mandatory commit graph gate
  preparation and package-level candidate graph review.

The progress helper script is:

```text
blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py
```

Default K root:

```text
docs/mian-k
```

Default progress table:

```text
docs/mian-k\OTHER_MIN_PACKAGE_PROGRESS.md
```

## Queue Contract

Use the progress table as the queue source of truth.

Selection rule:

1. If any item is `running`, resume the first `running` item before starting new work.
2. Otherwise start the first `pending` item in ascending index order.
3. Stop when there is no `running` or `pending` item.

Do not execute a directory that has `PACKAGE_SET_INDEX.md`; that is a package
set root, not a minimum executable package.

## Strict Serial Contract

Run strictly serial at every layer:

- The main runner may have at most one package-runner subagent open for active
  package execution.
- The package-runner subagent may invoke `stage-loop-auto` for only one package.
- `stage-loop-auto` runs one eligible stage at a time.
- `stage-loop` runs one stage through one phase at a time and may only spawn the
  subagent required for the current phase or fix attempt.

Do not start the next minimum package while the previous package-runner subagent
is still running or while its result has not been recorded in the progress
table.

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
   BLUE_K_OTHER_RUNNER_BLOCKED_NO_PACKAGE_SUBAGENT
   ```

Do not preemptively BLOCK only because the agent count may be high.

## Execution Loop

For each package:

1. Refresh the table:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" build --mian-k "docs/mian-k"
   ```

2. Select the next item:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" next --mian-k "docs/mian-k"
   ```

3. If the selected item is `pending`, mark it `running` before spawning the
   package-runner subagent:

   ```powershell
   python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status running --note "Starting stage-loop-auto."
   ```

4. Spawn exactly one package-runner subagent for the selected item.

   The main runner must give the subagent only:

   - selected progress index;
   - selected package path;
   - selector: `all` for a new `pending` item or `continue` for a resumed
     `running` item;
   - progress table path for read-only context;
   - instruction to load and use `stage-loop-auto`;
   - instruction to return result status, commits, commands, evidence verdict,
     blockers, dirty worktree status, and whether another resume is required.

   The package-runner subagent must not edit the progress table. The main
   runner is the only progress-table writer.

   If the package-runner subagent cannot be spawned after the Subagent Spawn
   Retry Gate, stop with:

   ```text
   BLUE_K_OTHER_RUNNER_BLOCKED_NO_PACKAGE_SUBAGENT
   ```

5. The package-runner subagent invokes `stage-loop-auto` on the selected package
   path:

   - Use selector `all` when starting a new `pending` item.
   - Use selector `continue` when resuming an existing `running` item.

6. When the package-runner subagent returns:

   - Mark `done` if the package finishes with ACCEPT or an acceptable WARN and
     no runner-level stop condition remains.
   - Mark `blocked` if `stage-loop-auto` reports BLOCK, EARLY_EXIT, failed
     admission, failed verification, missing contract files, dirty code-layer
     worktree, or another hard blocker.
   - Keep `running` if the conversation/tool execution is interrupted before a
     reliable final result is known. The next invocation must resume it with
     `stage-loop-auto continue`.

7. If a package was previously attempted but has durable work without the
   required stage-loop records, run the Unrecorded Work Recovery Gate before
   marking it blocked.

8. If a package blocks only because a declared prerequisite package is missing,
   incomplete, or lacks explicit acceptance, run the Dependency Recovery Gate
   before marking the selected package blocked.

9. After the package result is reliable and before any checkpoint commit, run
   the Code Graph Package Gate.

10. After marking `done` or `blocked`, run the Full-Repository Clean Commit Gate
   before selecting another package.

11. After the clean commit gate passes, loop to the next item unless the user requested only
   one package.

## Unrecorded Work Recovery Gate

Use this gate when a package has evidence that work was done but the normal
stage-loop-auto records are incomplete, such as missing `Stage:` execution
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
   package by:
   - reading the persisted diff and package evidence;
   - rerunning required tests;
   - persisting fresh verification output and correcting unfinished evidence
     status when those facts are not already durably recorded;
   - producing the required `Stage:` execution commit if stage-loop-auto permits
     recovery from the current state, including an evidence-only recovery commit
     when the implementation/test files were already captured by earlier
     checkpoint commits and the only remaining valid work is final evidence
     reconciliation;
   - running traceable-review and returning a reliable final verdict.
6. Do not block solely because the worktree is clean. A clean tree means there
   are no uncommitted changes, not that formal recovery is impossible. First
   inspect whether required final evidence, fresh command output, or status
   corrections are missing from durable artifacts. If they are missing, the
   package-runner may create that narrow evidence update through the
   stage-loop-auto execution path.
7. If no durable code or document evidence exists, rerun the package from the
   start of its current stage. Do not rely on prior claimed tests.
8. If repeated package-runner attempts become unresponsive, close the stale
   runner, keep or restore the same package to `running`, and retry with a
   narrower recovery prompt that names the missing durable record and the fresh
   commands to rerun. Only mark `blocked` after recovery has no safe next action
   or would require bypassing the three-layer boundary.
9. If at least three package-runner attempts for the same already-approved
   stage return no durable artifact at all (no dirty files, no commits, no
   running process, no concrete BLOCK), the main runner may run the Limited
   Main-Runner Closure Gate instead of looping indefinitely.

The main runner may perform read-only evidence discovery for this gate and may
update the progress table. It must not create the missing execution commit or
run `stage-loop-auto` directly; that remains package-runner responsibility.

## Limited Main-Runner Closure Gate

This is an emergency recovery valve for repeated no-artifact subagent loss. It
is not the normal path and must not be used merely for convenience.

The main runner may perform a narrow closure itself only when all conditions
are true:

1. The same stage has a committed approval artifact such as
   `REVIEW_TERMINATION.md` or an approval commit.
2. At least three package-runner attempts after that approval produced no
   durable artifact and no actionable BLOCK.
3. The package has one stage, explicit Allowed Files, and the required work is
   test-only or evidence-only, or source edits are mechanically proven by
   already-present dirty files.
4. The main runner can keep all edits inside Allowed Files and can run the
   exact required fresh commands.
5. The main runner records in evidence that closure used this emergency gate,
   lists the failed runner attempts, and preserves the normal structured commit
   message with the `Stage:` field.

When this gate is used:

- Prefer test-only/evidence-only closure. Do not invent broad source behavior.
- Run fresh tests and scans; old terminal output is not sufficient.
- Run the Code Graph Package Gate after the closure commit.
- Resume the normal dependency/package flow immediately after the repository is
  clean.

Do not use this gate if a subagent left dirty implementation work that needs
design judgment beyond the approved package docs; in that case continue with a
recovery package-runner or mark blocked.

## Dependency Recovery Gate

Use this gate when the selected `other` package returns BLOCK only because a
declared prerequisite package is incomplete or lacks explicit acceptance.

Recovery policy:

1. First search for durable prerequisite evidence using the same evidence rules
   as the Unrecorded Work Recovery Gate: git commits, package evidence files,
   target tests/fixtures, and fresh command output when tests must be proven.
2. If durable evidence supports the prerequisite but records are incomplete,
   spawn a package-runner for the prerequisite with `stage-loop-auto continue`
   and instruct it to reconcile evidence, rerun required tests, create the
   missing execution/evidence commit when allowed, and return a final verdict.
3. If no durable prerequisite work exists, spawn a package-runner for the
   prerequisite with `stage-loop-auto all` rather than marking the selected
   `other` package blocked. Keep the selected `other` package `running` while
   the prerequisite is being repaired.
4. A prerequisite package under `docs\mian-k\main` is allowed as a temporary
   dependency-runner target for this gate only. The main runner still must not
   execute the prerequisite directly, and the dependency-runner must use
   `stage-loop-auto` and its required subagents.
5. After the prerequisite returns ACCEPT or acceptable WARN, run the Code Graph
   Package Gate and Full-Repository Clean Commit Gate for the prerequisite
   result, then resume the originally selected `other` package with selector
   `continue`.
6. Mark the selected `other` package `blocked` only when dependency recovery has
   no safe next action, the prerequisite package itself returns a hard BLOCK, or
   continuing would require bypassing the three-layer boundary.

## Code Graph Package Gate

Follow the repository Code Graph Contract in `AGENTS.md`. The detailed command
source of truth is `scripts/code_graph/README.md`; do not duplicate that flow in
this skill.

After each package-runner returns a reliable result and before the checkpoint
commit, the main runner must stage the intended package result, prepare the
code graph gate, review the staged code diff plus candidate graph diff against
source and boundary contracts, apply only accepted overlay changes, and verify
the gate for the exact staged diff.

If the gate cannot be prepared, review is inconclusive, high-risk edges cannot
be source-verified, or the hook check fails, stop with:

```text
BLUE_K_OTHER_RUNNER_BLOCKED_CODE_GRAPH_GATE
```

## Runtime Infrastructure Review Handoff

When the selected package, its blockers, or its verification output touches
runtime infrastructure integration (Redis/cache/throttle, Channels, Dramatiq,
Temporal, DB connection/migrations, workers, background jobs, ports, env vars,
Docker/compose, CI/service topology, or deployment settings), the main runner
must include the traceable-review Runtime Infrastructure Context Gate in the
package-runner handoff. The package-runner final result must name which
Docker/compose/env/settings files it inspected before reporting a code defect
or environment blocker, and must classify findings as code defect,
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
   git commit -m "docs(blue-k): checkpoint other package progress"
   ```

5. Run `git status --short --branch` again.
6. Continue only if the worktree is clean.

The commit is intentionally full-repository, not path-selective, so evidence,
progress-table updates, package docs, accepted overlay updates, code graph gate
evidence, and any executor leftovers are captured before the next package
begins. Do not start the next package with a dirty worktree.

If the commit fails or the worktree remains dirty, stop with:

```text
BLUE_K_OTHER_RUNNER_BLOCKED_DIRTY_AFTER_CHECKPOINT
```

If the worktree is already dirty before the first package starts and there is no
selected `running` resume item, create one full-repository checkpoint commit
before selecting new work. If that preflight checkpoint fails or leaves the
worktree dirty, stop with the same blocker.

## Package-Runner Prompt

Use a concise prompt with this shape:

```text
Use $stage-loop-auto to execute exactly one Blue-K minimum executable package.

Package index: <index>
Package path: <path>
Selector: <all|continue>
Progress table: <path, read-only for you>

You are not alone in the codebase. Do not revert edits made by others. Do not
update the progress table. Load the local stage-loop-auto skill and follow its
subagent requirements. Treat the code graph as navigation evidence only: use it
to find relevant source quickly, but verify behavior against source and package
contracts before trusting graph edges. If runtime infrastructure integration is
in scope, apply the traceable-review Runtime Infrastructure Context Gate and
report inspected Docker/compose/env/settings files plus finding classification.
Return: final verdict, execution commit(s), approval commit(s), commands run,
evidence status, blockers, WARN items, final worktree status,
graph-consumption notes, runtime-infrastructure notes when relevant, and
whether this package needs resume.
```

## Marking Examples

Successful completion:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status done --commit "<commit>" --note "stage-loop-auto ACCEPT."
```

Blocked completion:

```powershell
python "blue-k-git-baton-testkit/skills/blue-k-other-index/scripts/other_progress.py" mark --mian-k "docs/mian-k" --index "<index>" --status blocked --note "<exact blocker>"
```

## Mandatory Three-Layer Agent Boundary

This skill requires a three-layer execution structure:

1. Main runner agent: owns queue selection and progress-table writes.
2. Package-runner subagent: owns exactly one selected package and invokes
   `stage-loop-auto`.
3. `stage-loop-auto` subagents: owns its internal `stage-loop`, doc-review,
   execution, and traceable-review subagent requirements.

The main runner must not call `stage-loop-auto` directly and must not implement
package work directly. The package-runner subagent must not bypass
`stage-loop-auto`. `stage-loop-auto` must not bypass its required subagents.

Do not pass the full blueprint or unrelated packages into the package-runner
subagent unless the selected package-local documents explicitly require
escalation.

Run only one minimum executable package at a time. After one package completes
and the table is updated, select the next package from the table again instead
of reusing stale queue state.

## Stop Conditions

Stop and report the exact blocker when:

- The progress table cannot be created or parsed.
- More than one item is `running`; ask the user which one to resume or repair the table.
- The selected path no longer exists.
- The selected path contains `PACKAGE_SET_INDEX.md`.
- The package-runner subagent cannot be spawned.
- The Code Graph Package Gate fails.
- `stage-loop-auto` stops with a hard blocker.
- Updating the progress table fails.
- The Full-Repository Clean Commit Gate fails or leaves the worktree dirty.
- The next action would require destructive git or filesystem operations.

If the user interrupts execution, leave the current item as `running`. On the
next use, resume that item before any pending item.
