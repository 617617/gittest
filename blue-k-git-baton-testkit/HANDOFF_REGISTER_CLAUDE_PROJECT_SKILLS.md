# Handoff: Register Blue-K Baton Entries In A Claude Project

Audience: Claude Code agent on the real DND backend project.

Source testkit: `blue-k-git-baton-testkit`

Target project: the repository root where the workflow is being registered.

Goal: register the Blue-K Git baton workflow so the human only sees the two
intended entries:

```text
bk sync   - shell-side safe Git sync, clipboard, and decision sheet
/bk work  - Claude chat-side execution entry
```

Do not ask the user to run raw `git pull` during normal baton operation.
`bk sync` owns safe fetch/fast-forward behavior.
Do not ask the user to memorize resume/takeover flags. `bk sync` must print
and, when possible, copy the exact `ChatCommand` to paste into the target chat.
Do not ask the user to run per-scenario commands during normal testing. Boundary
coverage must be exposed as `bk sync -Coverage` or an equivalent single
`bk sync` submode.

## Current Claude Registration Format

Prefer project skills:

```text
.claude/skills/<skill-name>/SKILL.md
```

Claude Code still supports `.claude/commands/*.md`, but current docs recommend
project skills because they support the same slash invocation plus richer
skill behavior.

Use these registrations:

```text
.claude/skills/bk/SKILL.md        -> supports /bk work, /bk resume, /bk takeover
.claude/skills/bk-sync/SKILL.md   -> optional Claude-side mirror of shell sync
scripts/blue_k_baton/bk.ps1       -> shell-side bk sync wrapper
blue-k-git-baton-testkit/skills/  -> portable Blue-K workflow skill closure
```

The required user path is `bk sync` in shell plus the printed chat command in
Claude chat. In normal starts that command is `/bk work`; resume and takeover
may be printed as `/bk resume` or `/bk takeover`.
`/bk-sync` is only an optional Claude-side audit convenience.

## Read First

From the testkit, read:

```text
SKILL.md
HANDOFF.md
references/protocol-v0.10.md
references/scenario-matrix.md
scripts/bk.ps1
HANDOFF_BLUE_K_WORKFLOW_SKILL_BUNDLE.md
```

From the target project, read:

```text
AGENTS.md
.claude/HANDOFF_codex_workflows_for_claude.md
docs/mian-k/MAIN_PACKAGE_PROGRESS.md
docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md
docs/mian-k/BLUE_K_PLAN_AUDIT_REPORT.md
```

If a file is missing, stop and report what is missing. Do not invent a new
Blue-K state source.

## Install Steps

1. Create the shell wrapper directory:

```powershell
New-Item -ItemType Directory -Force scripts\blue_k_baton
```

2. Copy or adapt the testkit wrapper:

```powershell
Copy-Item blue-k-git-baton-testkit\scripts\bk.ps1 scripts\blue_k_baton\bk.ps1
```

For the real project, replace simulator-only calls with real BATON inspection.
The wrapper must still keep these rules:

- fetch origin first;
- fast-forward only when local branch is clean and local HEAD is ancestor of upstream;
- stop on dirty worktree, local-ahead, diverged branches, missing upstream, or fetch failure;
- never merge, rebase, stash, clean, force-push, or execute Blue-K skills;
- print one first-line `NEXT:`;
- print `Task`, `Holder`, `Last`, `ChatTarget`, and `ChatCommand`;
- copy `ChatCommand` to the clipboard when possible, and fail soft otherwise.

3. Add a project shell alias instruction. Prefer documenting this in the
operator setup notes instead of changing global shell profile automatically:

```powershell
function bk { powershell -ExecutionPolicy Bypass -File .\scripts\blue_k_baton\bk.ps1 @args }
```

4. Create the Claude project skill directories:

```powershell
New-Item -ItemType Directory -Force .claude\skills\bk
New-Item -ItemType Directory -Force .claude\skills\bk-sync
```

5. Register or expose the portable Blue-K workflow skill closure from:

```text
blue-k-git-baton-testkit/skills/
```

The minimum closure is:

```text
blue-k-planner
blue-k-plan-audit
blue-k-main-runner
blue-k-other-runner
blue-k-other-index
traceable-plan
pre-doc-review
stage-loop-auto
stage-loop
doc-review
traceable-review
```

Use project-local relative paths. Do not point Claude at a machine-specific
global skill directory.

6. Write `.claude/skills/bk/SKILL.md`:

```markdown
---
description: Blue-K Git baton chat entry. Use when the user types /bk work, /bk resume, or /bk takeover after bk sync has selected this Claude window.
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
  - Bash(powershell -ExecutionPolicy Bypass -File scripts/blue_k_baton/bk.ps1 *)
  - Read
  - Grep
  - Glob
  - Edit
  - Write
---

# Blue-K Baton Work

This skill handles `/bk work`, `/bk resume`, and `/bk takeover`.

On the first response in each chat, self-announce:

```text
I am Claude. Lane: <current BATON lane or lanes this window owns>.
```

If the user did not pass `work`, `resume`, or `takeover` as the first argument,
stop and say:

```text
Use shell bk sync first, then paste its ChatCommand here.
```

## Non-Negotiable Rules

- Run shell `bk sync` or the equivalent safe-sync gate before any work.
- Do not start unless local HEAD, origin work branch, and BATON.WorkBranchHead match.
- Do not start unless the worktree is clean.
- Do not execute from the wrong owner role/window.
- If the current chat/window does not match BATON.OwnerRole and Lane, refuse
  and print the correct target window plus exact command.
- Acquire the coordination lease through compare-and-swap before changing business state.
- Run exactly one BATON assignment, then push a safe point and hand off.
- Do not select runner packages in this wrapper.
- Do not write progress tables in this wrapper.
- Do not run stage-loop-auto in this wrapper.
- Do not override plan-audit, traceable-review, code-graph, or package-gate BLOCK.
- `/bk resume` is same-holder recovery only.
- `/bk takeover` resumes only from the last pushed checkpoint and must ask the
  human to type `yes, abandon` after showing current remote evidence and the
  abandoned-unpushed-work basis.

## Dispatch

Dispatch by BATON lane:

- `blue-k-planner`: call the existing Blue-K planner workflow; requires durable human authorization.
- `blue-k-plan-audit`: call the existing Blue-K plan audit workflow.
- `blue-k-main-runner`: call the existing Blue-K main runner. The runner selects/resumes from `docs/mian-k/MAIN_PACKAGE_PROGRESS.md`.
- `blue-k-other-runner`: call the existing Blue-K other runner. The runner selects/resumes from `docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md`.
- `blue-k-consensus`: run the consensus lane only under `docs/mian-k/_consensus/<topic-id>/`.

## Required Consensus Gates

- Every plan output must pass plan consensus before runner execution.
- Every code/package output must pass code consensus before runner finalization.
- `review_pending + accepted consensus` means finalize the current row only, then stop.
- `fix_required` means route back to the runner-owned fix lane.
- Superseded, cancelled, subject-mismatch, hash-mismatch, docs-only-freeze violation, or lower-gate BLOCK must stop.

## Finish

After one safe assignment:

1. Update/preserve the runner-owned checkpoint artifacts.
2. Push work branch plus coordination branch atomically where supported.
3. Print exactly:

```text
Done. Now run: bk sync
```

4. Stop. Do not chain into the next package.
```

7. Write `.claude/skills/bk-sync/SKILL.md`:

```markdown
---
description: Claude-side mirror of Blue-K bk sync. Use when the user asks Claude to inspect or validate baton sync state. Normal users should run shell bk sync instead.
disable-model-invocation: true
allowed-tools:
  - Bash(powershell -ExecutionPolicy Bypass -File scripts/blue_k_baton/bk.ps1 *)
  - Bash(git *)
  - Read
---

# Blue-K Baton Sync Mirror

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\blue_k_baton\bk.ps1 sync
```

Report the exact first-line `NEXT:` and any `FailureCode`.

Do not execute planner, audit, runner, review, or consensus work from this
skill. If the output says to use `/bk work`, tell the user to run `/bk work`
in the named Claude window.
```

## Real-Project Implementation Notes

The copied testkit wrapper currently simulates BATON decisions. For production
registration, replace simulator decisions with real remote state reads:

```text
origin/blue-k/coordination:.blue-k/BATON.yaml
origin/<work-branch>
docs/mian-k/MAIN_PACKAGE_PROGRESS.md
docs/mian-k/OTHER_MIN_PACKAGE_PROGRESS.md
docs/mian-k/_consensus/<topic-id>/**
```

Coordination-branch reads/writes must use an isolated worktree or Git plumbing.
Do not checkout `blue-k/coordination` in the execution worktree.

## Acceptance Check

From the target project root, after registration:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\blue_k_baton\bk.ps1 sync
powershell -ExecutionPolicy Bypass -File scripts\blue_k_baton\bk.ps1 sync -Coverage
powershell -ExecutionPolicy Bypass -File scripts\blue_k_baton\bk.ps1 work
```

Expected:

- `sync` fetches/safely fast-forwards or blocks with a clear `FailureCode`;
- `sync` prints one first-line `NEXT:`;
- `sync` prints and, when possible, copies `ChatCommand`;
- `sync -Coverage` covers representative boundary partitions without asking
  the user to run individual scenario ids;
- shell-side `work` does not execute tasks and tells the user to use `/bk work`;
- Claude Code lists/recognizes `/bk` and `/bk-sync` after skills are created or after restarting if needed;
- `/bk work`, `/bk resume`, and `/bk takeover` refuse to proceed if sync/start
  gates or window-role gates are not satisfied.

## Stop Conditions

Stop and report instead of registering if:

- target project has no `.claude/skills` support in its Claude version;
- existing `.claude/skills/bk` or `.claude/skills/bk-sync` already exists and conflicts;
- existing Blue-K planner/audit/runner skills are unavailable;
- remote coordination branch does not exist;
- BATON schema is missing required fields;
- user expects shell `bk work` to execute tasks. Shell `bk work` must remain a guard.

## Final Report Format

```text
Verdict: PASS / WARN / BLOCK
Installed:
- <path>
Changed:
- <path>
Commands tested:
- <command>: <result>
Remaining manual setup:
- <only if needed>
```
